"""Provider-neutral model bank for USE."""
import json, os, time, urllib.error, urllib.parse, urllib.request
from collections import OrderedDict

CONTRACT_VERSION = "v2"
_STATE = {"models": {}, "provider_cursor": 0, "model_cursors": {}}

class ProviderCallError(RuntimeError):
    def __init__(self, message, provider, model, status_code=None, retry_after=None, category="provider_failure"):
        super().__init__(message)
        self.provider = provider
        self.model = model
        self.status_code = status_code
        self.retry_after = retry_after
        self.category = category

def _csv(name):
    return [x.strip() for x in os.getenv(name, "").split(",") if x.strip()]

def _state(provider, model):
    key = provider + ":" + model
    return _STATE["models"].setdefault(key, {
        "provider": provider, "model": model, "failures": 0,
        "cooldown_until": 0.0, "quarantine_until": 0.0,
        "last_error": "", "last_success": 0.0, "category": ""
    })

def _blocked(state):
    return max(float(state.get("cooldown_until", 0)), float(state.get("quarantine_until", 0))) > time.time()

def _failure(exc, provider, model):
    s = _state(provider, model)
    now = time.time()
    text = str(exc)
    low = text.casefold()
    s["failures"] = int(s.get("failures", 0)) + 1
    s["last_error"] = text[:500]
    status = getattr(exc, "status_code", None)
    retry_after = getattr(exc, "retry_after", None)
    category = getattr(exc, "category", "provider_failure")
    if "terms_required" in low or "requires terms acceptance" in low:
        category, s["quarantine_until"] = "terms_required", now + 3600
    elif status in {401, 403} or "unauthorized" in low or "forbidden" in low:
        category, s["quarantine_until"] = "authentication", now + 900
    elif status == 429 or "rate limit" in low or "too many requests" in low:
        category, s["cooldown_until"] = "rate_limited", now + max(30.0, float(retry_after or 60))
    elif status == 402:
        category, s["quarantine_until"] = "quota_or_billing", now + 1800
    elif status == 404:
        category, s["quarantine_until"] = "model_unavailable", now + 3600
    elif (
        status == 400
        and (
            "json_validate_failed" in low
            or "failed to validate json" in low
            or "invalid_request_error" in low
        )
    ) or (
        status is None
        and (
            "response was not an object" in low
            or "response was empty" in low
            or "response must contain exactly" in low
            or "invalid response" in low
            or "invalid json" in low
            or "jsondecodeerror" in low
        )
    ):
        # A model that cannot satisfy USE's structured-output contract has
        # failed the operation contract, even when the provider returned HTTP
        # 200 and the local parser rejected the payload. Treat that as a model
        # health failure, not a transient visitor failure, and quarantine the
        # candidate so repeated turns do not pay the same latency penalty.
        category, s["quarantine_until"] = "structured_output_contract", now + 3600
    elif "request too large" in low or ("context" in low and "length" in low):
        category, s["quarantine_until"] = "request_too_large", now + 1800
    else:
        category = category or "provider_failure"
        s["cooldown_until"] = now + min(300.0, 15.0 * (2 ** min(s["failures"] - 1, 4)))
    s["category"] = category

def _success(provider, model):
    s = _state(provider, model)
    s.update({"failures": 0, "cooldown_until": 0.0, "quarantine_until": 0.0,
              "last_error": "", "last_success": time.time(), "category": ""})

def _http_json(url, headers, payload, provider, model):
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={**headers, "Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            return json.loads(response.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try: retry_after = float(exc.headers.get("Retry-After", ""))
        except (TypeError, ValueError): retry_after = None
        raise ProviderCallError(
            provider + "/" + model + " HTTP " + str(exc.code) + ": " + body[:400],
            provider, model, exc.code, retry_after, "http_error"
        ) from exc
    except urllib.error.URLError as exc:
        raise ProviderCallError(str(exc), provider, model, category="network_failure") from exc

def _json_object(raw):
    text = str(raw or "").strip()
    if not text: raise ValueError("empty model response")
    try: value = json.loads(text)
    except json.JSONDecodeError:
        cleaned = text.strip(chr(96))
        if cleaned.casefold().startswith("json"): cleaned = cleaned[4:].strip()
        value = json.loads(cleaned)
    if not isinstance(value, dict): raise ValueError("model response was not an object")
    return value

def _groq(use_core, model, messages, max_tokens):
    client = getattr(use_core, "groq_client", None)
    if client is None: raise ProviderCallError("Groq client unavailable", "groq", model, category="unavailable")
    kwargs = {"model": model, "messages": messages, "temperature": 0.0,
              "max_completion_tokens": max_tokens, "response_format": {"type": "json_object"}}
    if model.startswith("openai/gpt-oss-"):
        kwargs["reasoning_effort"] = "low"; kwargs["include_reasoning"] = False
    response = client.chat.completions.create(**kwargs)
    return str(response.choices[0].message.content or "").strip()

def _gemini(key, model, messages, max_tokens):
    system = "\n".join(str(x.get("content") or "") for x in messages if x.get("role") == "system").strip()
    contents = [{"role": "user", "parts": [{"text": str(x.get("content") or "")}]}
                for x in messages if x.get("role") != "system"]
    payload = {"contents": contents, "generationConfig": {
        "maxOutputTokens": max_tokens,
        "responseMimeType": "application/json",
        "thinkingConfig": {"thinkingLevel": "low"},
    }}
    if system: payload["systemInstruction"] = {"parts": [{"text": system}]}
    url = "https://generativelanguage.googleapis.com/v1beta/models/" + urllib.parse.quote(model, safe="") + ":generateContent?key=" + urllib.parse.quote(key, safe="")
    data = _http_json(url, {}, payload, "gemini", model)
    try: return str(data["candidates"][0]["content"]["parts"][0]["text"]).strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise ProviderCallError("Gemini returned no text", "gemini", model, category="invalid_provider_response") from exc

def _openai_compatible(base_url, key, provider, model, messages, max_tokens):
    payload = {"model": model, "messages": messages, "temperature": 0.0,
               "max_tokens": max_tokens, "response_format": {"type": "json_object"}}
    data = _http_json(base_url.rstrip("/") + "/chat/completions",
                      {"Authorization": "Bearer " + key}, payload, provider, model)
    try: return str(data["choices"][0]["message"]["content"] or "").strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise ProviderCallError(provider + " returned no text", provider, model, category="invalid_provider_response") from exc

def _workers(key, account, model, messages, max_tokens):
    prompt = "\n\n".join(str(x.get("role") or "user").upper() + ": " + str(x.get("content") or "") for x in messages)
    payload = {"prompt": prompt + "\n\nReturn only one valid JSON object.", "max_tokens": max_tokens, "temperature": 0.0}
    url = "https://api.cloudflare.com/client/v4/accounts/" + urllib.parse.quote(account, safe="") + "/ai/run/" + urllib.parse.quote(model, safe="")
    data = _http_json(url, {"Authorization": "Bearer " + key}, payload, "workers_ai", model)
    result = data.get("result") if isinstance(data, dict) else None
    text = (result.get("response") or result.get("text") or result.get("output")) if isinstance(result, dict) else result
    if not text: raise ProviderCallError("Workers AI returned no text", "workers_ai", model, category="invalid_provider_response")
    return str(text).strip()

def _configured(use_core):
    out = OrderedDict()
    get_models = getattr(use_core, "get_live_groq_models", None)
    try:
        live_groq = get_models() if callable(get_models) else []
    except Exception as exc:
        print("USE provider bank: Groq inventory discovery failed: " + str(exc)[:300])
        live_groq = []
    out["groq"] = [str(x).strip() for x in (live_groq or []) if str(x).strip()]
    if os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_GEMINI_API_KEY"):
        out["gemini"] = _csv("USE_GEMINI_MODELS") or ["gemini-3.8-flash"]
    if os.getenv("MISTRAL_API_KEY"):
        out["mistral"] = _csv("USE_MISTRAL_MODELS") or ["mistral-small-latest"]
    if os.getenv("CLOUDFLARE_API_TOKEN") and os.getenv("CLOUDFLARE_ACCOUNT_ID"):
        gateway = _csv("USE_CLOUDFLARE_GATEWAY_MODELS")
        workers = _csv("USE_WORKERS_AI_MODELS")
        if gateway: out["cloudflare_gateway"] = gateway
        if workers: out["workers_ai"] = workers
    return out

def candidates(use_core):
    out = []
    for provider, models in _configured(use_core).items():
        for index, model in enumerate(models):
            if not _blocked(_state(provider, model)):
                out.append({"provider": provider, "model": model, "index": index})
    return out

def _rotate(values, cursor):
    if not values: return []
    n = cursor % len(values)
    return values[n:] + values[:n]

def select(use_core):
    items = candidates(use_core)
    if not items: return []
    grouped = OrderedDict()
    for item in items: grouped.setdefault(item["provider"], []).append(item)
    configured = _csv("USE_LLM_PROVIDER_ORDER")
    providers = [x for x in configured if x in grouped] + [x for x in grouped if x not in configured]
    providers = _rotate(providers, int(_STATE["provider_cursor"]))
    _STATE["provider_cursor"] += 1
    selected = []
    for provider in providers:
        models = grouped[provider]
        cursor = int(_STATE["model_cursors"].get(provider, 0))
        models = _rotate(models, cursor)
        _STATE["model_cursors"][provider] = cursor + 1
        selected.extend(models)
    return selected

def _call(use_core, item, messages, max_tokens):
    provider, model = item["provider"], item["model"]
    if provider == "groq": return _groq(use_core, model, messages, max_tokens)
    if provider == "gemini":
        key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_GEMINI_API_KEY")
        if not key: raise ProviderCallError("Gemini API key unavailable", provider, model, category="unavailable")
        return _gemini(key, model, messages, max_tokens)
    if provider == "mistral":
        key = os.getenv("MISTRAL_API_KEY")
        if not key: raise ProviderCallError("Mistral API key unavailable", provider, model, category="unavailable")
        return _openai_compatible("https://api.mistral.ai/v1", key, provider, model, messages, max_tokens)
    if provider == "cloudflare_gateway":
        token = os.getenv("CLOUDFLARE_API_TOKEN")
        account = os.getenv("CLOUDFLARE_ACCOUNT_ID")
        if not token or not account: raise ProviderCallError("Cloudflare credentials unavailable", provider, model, category="unavailable")
        base = "https://api.cloudflare.com/client/v4/accounts/" + urllib.parse.quote(account, safe="") + "/ai/v1"
        return _openai_compatible(base, token, provider, model, messages, max_tokens)
    if provider == "workers_ai":
        token = os.getenv("CLOUDFLARE_API_TOKEN")
        account = os.getenv("CLOUDFLARE_ACCOUNT_ID")
        if not token or not account: raise ProviderCallError("Workers AI credentials unavailable", provider, model, category="unavailable")
        return _workers(token, account, model, messages, max_tokens)
    raise ProviderCallError("unknown provider", provider, model, category="unavailable")

def route(*, use_core, messages, max_tokens, parse):
    pool = select(use_core)
    if not pool: return None
    order = [x["provider"] + ":" + x["model"] for x in pool]
    last_error = ""
    for item in pool:
        provider, model = item["provider"], item["model"]
        try:
            print("USE model bank attempt: provider=" + provider + ", model=" + model)
            parsed = parse(_call(use_core, item, messages, max_tokens))
            if not isinstance(parsed, dict): raise ValueError("route response was not an object")
            _success(provider, model)
            return {"parsed": parsed, "provider": provider, "model": model, "preference_order": order}
        except Exception as exc:
            last_error = str(exc)
            _failure(exc, provider, model)
            print("USE model bank candidate failed: provider=" + provider + ", model=" + model + ", error=" + last_error[:300])
    print("USE model bank exhausted viable candidates: last_error=" + last_error[:400])
    return None

def snapshot(use_core):
    configured = _configured(use_core)
    all_items = [
        {"provider": provider, "model": model}
        for provider, models in configured.items()
        for model in models
    ]
    return {
        "contract_version": CONTRACT_VERSION,
        "selection_policy": "provider_health_aware",
        "providers": sorted({x["provider"] for x in all_items}),
        "candidates": [
            {
                "provider": x["provider"],
                "model": x["model"],
                "blocked": _blocked(_state(x["provider"], x["model"])),
                "state": dict(_state(x["provider"], x["model"])),
            }
            for x in all_items
        ],
    }
