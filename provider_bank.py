"""Provider-neutral model bank for USE."""
import base64, json, mimetypes, os, urllib.error, urllib.parse, urllib.request
from collections import OrderedDict

from provider_resilience import (
    CONTRACT_VERSION as RESILIENCE_CONTRACT_VERSION,
    acquire_probe,
    aggregate_provider_health,
    blocked,
    new_state,
    record_failure,
    record_success,
    state_summary,
)

CONTRACT_VERSION = "v2"

# Only production models with the structured-output capability required by the
# current Provider Bank contract may enter the JSON operation pool. Live model
# discovery remains diagnostic; it never grants runtime eligibility by itself.
PRODUCTION_GROQ_MODELS = ("openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b")

# Capability policy is owned here, at the Provider Bank boundary. A model may
# only enter an operation pool when the bank knows that it can satisfy that
# operation's contract. Health/cooldown state remains separate and dynamic.
# Unknown models are intentionally conservative: discovery never grants
# specialist eligibility by itself.
MODEL_CAPABILITIES = {
    ("groq", "openai/gpt-oss-120b"): frozenset({"json_object", "json_schema_strict", "reasoning", "long_context", "composition", "relational_analysis", "low_latency"}),
    ("groq", "openai/gpt-oss-20b"): frozenset({"json_object", "json_schema_strict", "reasoning", "long_context", "composition", "relational_analysis", "low_latency"}),
    # Qwen has structured-output support, but the live bank has observed
    # completion-bound JSON failures on the long HRN composition workload.
    # Keep it eligible for structured/short reasoning work, not composition.
    ("groq", "qwen/qwen3.8-27b"): frozenset({"json_object", "json_schema_strict", "reasoning", "long_context", "relational_analysis", "low_latency"}),
    ("gemini", "gemini-3.8-flash"): frozenset({"json_object", "json_schema_strict", "reasoning", "long_context", "composition", "relational_analysis", "vision", "low_latency"}),
    ("mistral", "mistral-small-latest"): frozenset({"json_object", "json_schema_strict", "long_context", "composition", "relational_analysis", "low_latency"}),
    ("workers_ai", "@cf/google/gemma-4-26b-a4b-it"): frozenset({"json_object", "json_schema_strict", "reasoning", "long_context", "composition", "relational_analysis", "vision"}),
    ("workers_ai", "@cf/zai-org/glm-4.7-flash"): frozenset({"json_object", "json_schema_strict", "reasoning", "long_context", "composition", "relational_analysis", "low_latency"}),
}

OPERATION_REQUIREMENTS = {
    "hrn_relational": frozenset({"json_object", "long_context", "composition", "relational_analysis"}),
    "hrn_perception": frozenset({"json_object", "relational_analysis"}),
    "atlas_finder": frozenset({"json_object"}),
    "atlas_vision": frozenset({"json_object", "vision"}),
    "mini_use": frozenset({"json_object"}),
    "stewardship_pathway": frozenset({"json_object", "long_context", "reasoning"}),
}

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
    return _STATE["models"].setdefault(key, new_state(provider, model))

def _blocked(state):
    return blocked(state)

def _failure(exc, provider, model):
    state = _state(provider, model)
    text = str(exc)
    low = text.casefold()
    status = getattr(exc, "status_code", None)
    retry_after = getattr(exc, "retry_after", None)
    category = getattr(exc, "category", "provider_failure")

    if "terms_required" in low or "requires terms acceptance" in low:
        category = "terms_required"
    elif status in {401, 403} or "unauthorized" in low or "forbidden" in low:
        category = "authentication"
    elif status == 429 or "rate limit" in low or "too many requests" in low:
        category = "rate_limited"
    elif status == 402:
        category = "quota_or_billing"
    elif status == 404:
        category = "model_unavailable"
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
        category = "structured_output_contract"
    elif "request too large" in low or ("context" in low and "length" in low):
        category = "request_too_large"

    delay = record_failure(
        state,
        category,
        text,
        retry_after=retry_after,
    )
    print(
        "USE provider resilience: "
        f"provider={provider}, model={model}, state=open, category={category}, "
        f"cooldown_seconds={int(delay)}"
    )

def _success(provider, model):
    state = _state(provider, model)
    was_recovery = str(state.get("state") or "") == "half_open"
    record_success(state)
    if was_recovery:
        print(
            "USE provider resilience: "
            f"provider={provider}, model={model}, recovery_probe=success, state=healthy"
        )

def _http_json(url, headers, payload, provider, model):
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={**headers, "Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=6) as response:
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

def _groq(use_core, model, messages, max_tokens, schema=None):
    client = getattr(use_core, "groq_client", None)
    if client is None: raise ProviderCallError("Groq client unavailable", "groq", model, category="unavailable")
    kwargs = {"model": model, "messages": messages, "temperature": 0.0,
              "max_completion_tokens": max_tokens, "response_format": ({"type": "json_schema", "json_schema": schema} if isinstance(schema, dict) else {"type": "json_object"})}
    if model.startswith("openai/gpt-oss-"):
        kwargs["reasoning_effort"] = "low"; kwargs["include_reasoning"] = False
    response = client.chat.completions.create(**kwargs)
    return str(response.choices[0].message.content or "").strip()

def _gemini(key, model, messages, max_tokens, schema=None):
    system = "\n".join(str(x.get("content") or "") for x in messages if x.get("role") == "system" and isinstance(x.get("content"), str)).strip()
    contents = []
    for message in messages:
        if message.get("role") == "system":
            continue
        content = message.get("content")
        parts = []
        if isinstance(content, list):
            for item in content:
                if not isinstance(item, dict):
                    continue
                if item.get("type") == "text":
                    parts.append({"text": str(item.get("text") or "")})
                elif item.get("type") == "image_url":
                    image_url = item.get("image_url") or {}
                    url = str(image_url.get("url") or "") if isinstance(image_url, dict) else str(image_url or "")
                    parsed = urllib.parse.urlparse(url)
                    if parsed.scheme != "https" or not parsed.hostname or not parsed.hostname.casefold().endswith("geralddaquila.com"):
                        raise ProviderCallError("Gemini vision URL is not an approved Living Archive asset.", "gemini", model, category="invalid_request")
                    request = urllib.request.Request(url, headers={"User-Agent": "Living-Archive-Provider-Bank/1.0"})
                    with urllib.request.urlopen(request, timeout=8) as response:
                        raw = response.read(8 * 1024 * 1024 + 1)
                        mime = str(response.headers.get_content_type() or mimetypes.guess_type(url)[0] or "image/jpeg")
                    if len(raw) > 8 * 1024 * 1024:
                        raise ProviderCallError("Vision asset exceeds Provider Bank size limit.", "gemini", model, category="request_too_large")
                    parts.append({"inlineData": {"mimeType": mime, "data": base64.b64encode(raw).decode("ascii")}})
        else:
            parts.append({"text": str(content or "")})
        if parts:
            contents.append({"role": "user" if message.get("role") != "assistant" else "model", "parts": parts})
    payload = {"contents": contents, "generationConfig": {
        "maxOutputTokens": max_tokens,
        "responseMimeType": "application/json",
        "thinkingConfig": {"thinkingLevel": "low"},
    }}
    if isinstance(schema, dict) and isinstance(schema.get("schema"), dict):
        payload["generationConfig"]["responseSchema"] = schema["schema"]
    if system: payload["systemInstruction"] = {"parts": [{"text": system}]}
    url = "https://generativelanguage.googleapis.com/v1beta/models/" + urllib.parse.quote(model, safe="") + ":generateContent?key=" + urllib.parse.quote(key, safe="")
    data = _http_json(url, {}, payload, "gemini", model)
    try: return str(data["candidates"][0]["content"]["parts"][0]["text"]).strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise ProviderCallError("Gemini returned no text", "gemini", model, category="invalid_provider_response") from exc

def _openai_compatible(base_url, key, provider, model, messages, max_tokens, schema=None):
    payload = {"model": model, "messages": messages, "temperature": 0.0,
               "max_tokens": max_tokens, "response_format": ({"type": "json_schema", "json_schema": schema} if isinstance(schema, dict) else {"type": "json_object"})}
    data = _http_json(base_url.rstrip("/") + "/chat/completions",
                      {"Authorization": "Bearer " + key}, payload, provider, model)
    try: return str(data["choices"][0]["message"]["content"] or "").strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise ProviderCallError(provider + " returned no text", provider, model, category="invalid_provider_response") from exc

def _workers(key, account, model, messages, max_tokens, schema=None):
    payload = {"messages": messages, "max_tokens": max_tokens, "temperature": 0.0,
               "options": {"rejectIfBusy": True}}
    if isinstance(schema, dict) and isinstance(schema.get("schema"), dict):
        payload["response_format"] = {"type": "json_schema", "json_schema": schema["schema"]}
    else:
        payload["response_format"] = {"type": "json_object"}
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
    live_set = {str(x).strip() for x in (live_groq or []) if str(x).strip()}
    out["groq"] = [model for model in PRODUCTION_GROQ_MODELS if model in live_set]
    if os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_GEMINI_API_KEY"):
        out["gemini"] = _csv("USE_GEMINI_MODELS") or ["gemini-3.8-flash"]
    if os.getenv("MISTRAL_API_KEY"):
        out["mistral"] = _csv("USE_MISTRAL_MODELS") or ["mistral-small-latest"]
    if os.getenv("CLOUDFLARE_API_TOKEN") and os.getenv("CLOUDFLARE_ACCOUNT_ID"):
        gateway = _csv("USE_CLOUDFLARE_GATEWAY_MODELS")
        workers = _csv("USE_WORKERS_AI_MODELS")
        if gateway: out["cloudflare_gateway"] = gateway
        if workers: out["workers_ai"] = workers
        elif not gateway: out["workers_ai"] = ["@cf/google/gemma-4-26b-a4b-it", "@cf/zai-org/glm-4.7-flash"]
    return out

def _capabilities(provider, model):
    return MODEL_CAPABILITIES.get((provider, model), frozenset())

def _operation_requirements(operation, schema):
    required = set(OPERATION_REQUIREMENTS.get(operation, frozenset()))
    if isinstance(schema, dict):
        required.add("json_schema_strict")
    return required

def _eligible(provider, model, operation, schema=None):
    required = _operation_requirements(operation, schema)
    capabilities = _capabilities(provider, model)
    missing = required.difference(capabilities)
    if missing:
        return False, sorted(missing)
    return True, []

def candidates(use_core, operation="generic", schema=None):
    out = []
    for provider, models in _configured(use_core).items():
        for index, model in enumerate(models):
            if _blocked(_state(provider, model)):
                continue
            eligible, missing = _eligible(provider, model, operation, schema=schema)
            if not eligible:
                print(
                    "USE provider capability exclusion: "
                    f"operation={operation}, provider={provider}, model={model}, "
                    f"missing={','.join(missing)}"
                )
                continue
            out.append({
                "provider": provider,
                "model": model,
                "index": index,
                "capabilities": sorted(_capabilities(provider, model)),
            })
    return out

def _rotate(values, cursor):
    if not values: return []
    n = cursor % len(values)
    return values[n:] + values[:n]

def select(use_core, operation="generic", schema=None):
    items = candidates(use_core, operation=operation, schema=schema)
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

def _call(use_core, item, messages, max_tokens, schema=None):
    provider, model = item["provider"], item["model"]
    if provider == "groq": return _groq(use_core, model, messages, max_tokens, schema)
    if provider == "gemini":
        key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_GEMINI_API_KEY")
        if not key: raise ProviderCallError("Gemini API key unavailable", provider, model, category="unavailable")
        return _gemini(key, model, messages, max_tokens, schema)
    if provider == "mistral":
        key = os.getenv("MISTRAL_API_KEY")
        if not key: raise ProviderCallError("Mistral API key unavailable", provider, model, category="unavailable")
        return _openai_compatible("https://api.mistral.ai/v1", key, provider, model, messages, max_tokens, schema)
    if provider == "cloudflare_gateway":
        token = os.getenv("CLOUDFLARE_API_TOKEN")
        account = os.getenv("CLOUDFLARE_ACCOUNT_ID")
        if not token or not account: raise ProviderCallError("Cloudflare credentials unavailable", provider, model, category="unavailable")
        base = "https://api.cloudflare.com/client/v4/accounts/" + urllib.parse.quote(account, safe="") + "/ai/v1"
        return _openai_compatible(base, token, provider, model, messages, max_tokens, schema)
    if provider == "workers_ai":
        token = os.getenv("CLOUDFLARE_API_TOKEN")
        account = os.getenv("CLOUDFLARE_ACCOUNT_ID")
        if not token or not account: raise ProviderCallError("Workers AI credentials unavailable", provider, model, category="unavailable")
        return _workers(token, account, model, messages, max_tokens, schema)
    raise ProviderCallError("unknown provider", provider, model, category="unavailable")

def route(*, use_core, messages, max_tokens, parse, operation="generic", schema=None):
    pool = select(use_core, operation=operation)
    if not pool: return None
    order = [x["provider"] + ":" + x["model"] for x in pool]
    last_error = ""
    max_attempts = min(len(pool), max(3, min(5, int(os.getenv("USE_PROVIDER_BANK_MAX_ATTEMPTS", "5") or 5))))
    for attempt_index, item in enumerate(pool[:max_attempts], start=1):
        provider, model = item["provider"], item["model"]
        state = _state(provider, model)
        if not acquire_probe(state):
            continue
        try:
            print("USE model bank attempt: provider=" + provider + ", model=" + model +
                  ", state=" + str(state.get("state") or "healthy"))
            parsed = parse(_call(use_core, item, messages, max_tokens, schema))
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
    provider_states = {}
    for item in all_items:
        provider_states.setdefault(item["provider"], []).append(_state(item["provider"], item["model"]))
    return {
        "contract_version": CONTRACT_VERSION,
        "resilience_contract_version": RESILIENCE_CONTRACT_VERSION,
        "selection_policy": "capability_and_provider_health_aware_self_healing",
        "capability_policy_version": "1.0",
        "operation_requirements": {
            operation: sorted(requirements)
            for operation, requirements in OPERATION_REQUIREMENTS.items()
        },
        "providers": sorted({x["provider"] for x in all_items}),
        "provider_health": {
            provider: aggregate_provider_health(states)
            for provider, states in provider_states.items()
        },
        "candidates": [
            {
                "provider": x["provider"],
                "model": x["model"],
                "blocked": _blocked(_state(x["provider"], x["model"])),
                "state": state_summary(_state(x["provider"], x["model"])),
                "capabilities": sorted(_capabilities(x["provider"], x["model"])),
            }
            for x in all_items
        ],
    }
