"""Provider-neutral model bank for USE."""
import base64, json, mimetypes, os, re, urllib.error, urllib.parse, urllib.request
from collections import OrderedDict
import time

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
from provider_health_store import (
    export_health_states,
    load_remote_states,
    merge_health_state,
    save_remote_states,
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
    ("groq", "openai/gpt-oss-120b"): frozenset({"json_object", "json_schema_strict", "json_schema_best_effort", "text_generation", "reasoning", "long_context", "composition", "relational_analysis", "low_latency"}),
    ("groq", "openai/gpt-oss-20b"): frozenset({"json_object", "json_schema_strict", "json_schema_best_effort", "text_generation", "reasoning", "long_context", "composition", "relational_analysis", "low_latency"}),
    # Qwen 3.8 is composition-capable. Its prior failure was completion
    # exhaustion, so the bank controls its reasoning mode and budget rather
    # than excluding the model from the composition capability class.
    ("groq", "qwen/qwen3.8-27b"): frozenset({"json_object", "json_schema_strict", "json_schema_best_effort", "text_generation", "reasoning", "long_context", "composition", "relational_analysis", "vision", "low_latency"}),
    # OpenRouter free router dynamically selects a currently available free model;
    # eligibility is based on router-level capabilities, not a fixed underlying model.
    # Named free-model candidates give the bank independent fallback lanes when the router returns an empty upstream response. JSON is enforced by the bank contract validator, not provider-specific response_format hints.
    ("openrouter", "openrouter/free"): frozenset({"json_object", "json_schema_best_effort", "text_generation", "long_context", "composition", "relational_analysis", "vision", "low_latency"}),
    ("openrouter", "nvidia/nemotron-3-ultra-550b-a55b:free"): frozenset({"json_object", "json_schema_best_effort", "text_generation", "long_context", "composition", "relational_analysis"}),
    ("openrouter", "google/gemma-4-31b-it:free"): frozenset({"json_object", "json_schema_best_effort", "text_generation", "long_context", "composition", "relational_analysis"}),
    ("gemini", "gemini-3.8-flash"): frozenset({"json_object", "json_schema_strict", "json_schema_best_effort", "text_generation", "reasoning", "long_context", "composition", "relational_analysis", "vision", "low_latency"}),
    ("mistral", "mistral-small-latest"): frozenset({"json_object", "json_schema_strict", "json_schema_best_effort", "text_generation", "long_context", "composition", "relational_analysis", "low_latency"}),
    # NVIDIA-hosted endpoints are admitted only for the three reviewed model IDs.
    # Capability claims are conservative and every result still passes the same
    # provider-neutral JSON and visitor-facing contract validators.
    ("nvidia", "nvidia/nemotron-3.5-lightning-30b-a3b"): frozenset({"json_object", "json_schema_best_effort", "text_generation", "reasoning", "long_context", "composition", "relational_analysis", "low_latency"}),
    ("nvidia", "nvidia/nemotron-3-super-120b-a12b"): frozenset({"json_object", "json_schema_best_effort", "text_generation", "reasoning", "long_context", "composition", "relational_analysis"}),
    ("nvidia", "google/gemma-4-31b-it"): frozenset({"json_object", "json_schema_best_effort", "text_generation", "reasoning", "long_context", "composition", "relational_analysis"}),
    ("workers_ai", "@cf/google/gemma-4-26b-a4b-it"): frozenset({"json_object", "json_schema_strict", "json_schema_best_effort", "text_generation", "reasoning", "long_context", "composition", "relational_analysis", "vision"}),
    ("workers_ai", "@cf/zai-org/glm-4.7-flash"): frozenset({"json_object", "json_schema_strict", "json_schema_best_effort", "text_generation", "reasoning", "long_context", "composition", "relational_analysis", "low_latency"}),
    # Canary fallback: Cloudflare documents this variant as optimized for faster inference.
    # It remains behind the same runtime contract and health/quality arbitration as all lanes.
    ("workers_ai", "@cf/meta/llama-3.3-70b-instruct-fp8-fast"): frozenset({"json_object", "json_schema_best_effort", "text_generation", "long_context", "composition", "relational_analysis", "low_latency"}),
}

# Verified provider-published model lifecycle aliases. An LLM may suggest a
# candidate migration, but runtime promotion is restricted to this reviewed,
# deterministic registry and still passes normal capability/health/contract gates.
MODEL_DEPRECATION_ALIASES = {
    ("gemini", "gemini-3.7-flash"): "gemini-3.8-flash",
    # Gemini 3.5 is intentionally not aliased until its successor is
    # registered in MODEL_CAPABILITIES and validated against the bank contract.
}


def resolve_model_alias(provider, model):
    """Resolve only explicitly verified provider/model deprecations."""
    provider = str(provider or "").strip().lower()
    model = str(model or "").strip()
    replacement = MODEL_DEPRECATION_ALIASES.get((provider, model))
    if not replacement:
        return model
    print(
        "USE model lifecycle: "
        f"provider={provider}, obsolete_model={model}, replacement={replacement}, "
        "source=verified_registry"
    )
    return replacement


def resolve_model_list(provider, models):
    """Resolve known aliases and preserve first-seen order without duplicates."""
    resolved = []
    for model in models:
        candidate = resolve_model_alias(provider, model)
        if candidate and candidate not in resolved:
            resolved.append(candidate)
    return resolved

# NVIDIA catalog display names are accepted for operator convenience, but are
# deterministically normalized to the exact model IDs published in NVIDIA's
# hosted API examples. Unknown IDs remain unchanged and fail closed at capability
# eligibility rather than being sent to a provider by guesswork.
NVIDIA_MODEL_ALIASES = {
    "nemotron 3.5 lightning 30b a3b": "nvidia/nemotron-3.5-lightning-30b-a3b",
    "nvidia/nemotron-3.5-lightning-30b-a3b": "nvidia/nemotron-3.5-lightning-30b-a3b",
    "nemotron 3 super 120b a12b": "nvidia/nemotron-3-super-120b-a12b",
    "nvidia/nemotron-3-super-120b-a12b": "nvidia/nemotron-3-super-120b-a12b",
    "gemma 4 31b it": "google/gemma-4-31b-it",
    "google/gemma-4-31b-it": "google/gemma-4-31b-it",
}

def resolve_nvidia_model_id(model):
    """Map a known NVIDIA catalog display name to its verified hosted model ID."""
    raw = str(model or "").strip()
    normalized = " ".join(raw.casefold().replace("_", " ").split())
    return NVIDIA_MODEL_ALIASES.get(normalized, raw)


MODEL_LIMITS = {
    # Provider/model limits are part of capability, not specialist policy.
    # Qwen's current Groq lane enforces a 1,000-token output-per-minute ceiling.
    ("groq", "qwen/qwen3.8-27b"): {"max_completion_tokens": 1000},
    ("groq", "openai/gpt-oss-20b"): {"max_completion_tokens": 3000},
    ("groq", "openai/gpt-oss-120b"): {"max_completion_tokens": 3000},
}

OPERATION_TOKEN_FLOORS = {
    # The bank owns minimum completion budgets for semantic operations. This
    # prevents a specialist's transport envelope from starving a capable model
    # before it can finish its contractual JSON object.
    "hrn_relational": 600,
    "hrn_perception": 1600,
    "atlas_finder": 500,
    "atlas_vision": 700,
    "mini_use": 500,
    "stewardship_pathway": 900,
    "general_guide_composition": 900,
}

# Strict JSON schemas are opt-in. HRN composition deliberately uses the
# provider-neutral JSON-object contract because its own protected validator
# owns the semantic envelope. This prevents constrained decoding from starving
# a long conversational composition before a valid object is emitted.
OPERATION_SCHEMAS = {"hrn_relational_recovery":{"name":"hrn_relational_recovery","strict":False,"schema":{"type":"object","properties":{"response":{"type":"string"},"question":{"type":"string"},"rest":{"type":"boolean"},"use_resource":{"type":"boolean"},"resource_intro":{"type":"string"}},"required":["response","question","rest","use_resource","resource_intro"],"additionalProperties":True}}}

OPERATION_REQUIREMENTS = {
    "hrn_relational": frozenset({"json_object", "long_context", "composition", "relational_analysis"}),
    "hrn_voice_repair": frozenset({"text_generation", "relational_analysis"}),
    "hrn_perception": frozenset({"json_object", "relational_analysis"}),
    "atlas_finder": frozenset({"json_object"}),
    "atlas_vision": frozenset({"json_object", "vision"}),
    "mini_use": frozenset({"json_object"}),
    "stewardship_pathway": frozenset({"json_object", "long_context", "reasoning"}),
    # The all-purpose Guide requires composition and enough context to answer
    # the visitor directly, but does not depend on any provider-specific
    # reasoning feature. Provider selection remains entirely bank-owned.
    "general_guide_composition": frozenset({"json_object", "long_context", "composition"}),
}

_STATE = {"models": {}, "quality": {}, "provider_cursor": 0, "model_cursors": {}}
_LAST_PROVIDER_INVENTORY_DIAGNOSTIC = None
_SHARED_STATE_DIAGNOSTICS = {
    "mode": "shared_wordpress_database",
    "available": None,
    "last_sync": 0.0,
    "last_persist": 0.0,
    "last_error": "",
}
_LAST_SHARED_STATE_WARNING = 0.0


def _sync_shared_state():
    """Merge durable cross-service health state before choosing provider lanes."""
    global _LAST_SHARED_STATE_WARNING
    remote = load_remote_states()
    if remote is None:
        _SHARED_STATE_DIAGNOSTICS["available"] = False
        _SHARED_STATE_DIAGNOSTICS["mode"] = "local_fallback"
        _SHARED_STATE_DIAGNOSTICS["last_error"] = "shared health store unavailable or not configured"
        return
    now = time.time()
    for key, incoming in remote.items():
        if not isinstance(incoming, dict):
            continue
        if key.startswith("quality:"):
            provider = str(incoming.get("provider") or "")
            model = str(incoming.get("model") or "")
            operation = str(incoming.get("operation") or "")
            quality_states = _STATE.setdefault("quality", {})
            local = quality_states.get(key)
            if local is None:
                local = {
                    "provider": provider,
                    "model": model,
                    "operation": operation,
                    "quality_failures": 0,
                    "last_quality_failure": 0.0,
                    "last_quality_success": 0.0,
                    "quality_cooldown_until": 0.0,
                    "quality_error": "",
                }
                quality_states[key] = local
            merge_health_state(local, incoming, now=now)
            continue
        provider = str(incoming.get("provider") or key.split(":", 1)[0])
        model = str(incoming.get("model") or key.split(":", 1)[-1])
        local = _STATE["models"].get(key)
        if local is None:
            local = new_state(provider, model)
            _STATE["models"][key] = local
        merge_health_state(local, incoming, now=now)
    _SHARED_STATE_DIAGNOSTICS.update({
        "mode": "shared_wordpress_database",
        "available": True,
        "last_sync": now,
        "last_error": "",
    })


def _persist_shared_state():
    """Persist the bounded health snapshot; failure never fabricates a provider answer."""
    global _LAST_SHARED_STATE_WARNING
    combined_state = dict(_STATE["models"])
    combined_state.update(_STATE.setdefault("quality", {}))
    ok = save_remote_states(export_health_states(combined_state))
    if ok:
        _SHARED_STATE_DIAGNOSTICS.update({
            "mode": "shared_wordpress_database",
            "available": True,
            "last_persist": time.time(),
            "last_error": "",
        })
        return True
    _SHARED_STATE_DIAGNOSTICS["available"] = False
    _SHARED_STATE_DIAGNOSTICS["mode"] = "local_fallback"
    _SHARED_STATE_DIAGNOSTICS["last_error"] = "shared health write failed"
    now = time.time()
    if now - _LAST_SHARED_STATE_WARNING >= 60:
        print("USE provider resilience: shared health persistence unavailable; using bounded process-local fallback")
        _LAST_SHARED_STATE_WARNING = now
    return False

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


def _quality_key(operation, provider, model):
    return "quality:" + str(operation) + ":" + provider + ":" + model


def _quality_state(operation, provider, model, create=False):
    key = _quality_key(operation, provider, model)
    quality_states = _STATE.setdefault("quality", {})
    if key in quality_states:
        return quality_states[key]
    if not create:
        return {}
    return quality_states.setdefault(key, {
        "provider": provider,
        "model": model,
        "operation": str(operation),
        "quality_failures": 0,
        "last_quality_failure": 0.0,
        "last_quality_success": 0.0,
        "quality_cooldown_until": 0.0,
        "quality_error": "",
    })

def _blocked(state):
    return blocked(state)

def _failure(exc, provider, model):
    state = _state(provider, model)
    text = str(exc)
    low = text.casefold()
    status = getattr(exc, "status_code", None)
    retry_after = getattr(exc, "retry_after", None)
    category = getattr(exc, "category", "provider_failure")

    # A daily token limit explicitly scoped to a named model is not an
    # account-wide billing failure. Keep that model on cooldown while allowing
    # healthy siblings (which can have independent token budgets) to be tried.
    # Truly account-wide quota/billing messages still quarantine the provider.
    model_scoped_daily_limit = (
        ("tokens per day" in low or re.search(r"\btpd\b", low))
        and re.search(r"\bfor model\b", low)
    )
    free_tier_daily_limit = (
        "free-models-per-day" in low
        or "free model requests per day" in low
    )
    if free_tier_daily_limit:
        # OpenRouter's free request allowance is account-wide across its free
        # model IDs. Quarantine the whole OpenRouter lane until the published
        # reset instead of spending the remaining attempt window on siblings.
        category = "free_tier_daily_quota"
        reset_match = re.search(r"x-ratelimit-reset[^0-9]{0,16}(\d{10,13})", low)
        if reset_match:
            reset_at = float(reset_match.group(1))
            if reset_at > 1_000_000_000_000:
                reset_at /= 1000.0
            retry_after = max(60.0, reset_at - time.time())
    elif "terms_required" in low or "requires terms acceptance" in low:
        category = "terms_required"
    elif status in {401, 403} or "unauthorized" in low or "forbidden" in low or "authentication error" in low:
        category = "authentication"
    elif model_scoped_daily_limit:
        category = "rate_limited"
    elif (
        status == 402
        or "tokens per day" in low
        or re.search(r"\btpd\b", low)
        or "daily quota" in low
        or "daily limit" in low
        or "billing hard limit" in low
        or "exceeded your current quota" in low
        or "quota exceeded" in low
        or "insufficient quota" in low
        or "billing details" in low
    ):
        category = "quota_or_billing"
    elif status == 404:
        category = "model_unavailable"
    elif status == 429 or "rate limit" in low or "too many requests" in low:
        category = "rate_limited"

    # Provider retry prose is useful for both ordinary 429s and model-scoped
    # daily token limits. Never let that prose override account-wide billing
    # classification above.
    if category == "rate_limited" and not retry_after:
        wait = re.search(
            r"try again in\s+(?:(\d+(?:\.\d+)?)h)?\s*(?:(\d+(?:\.\d+)?)m)?\s*(?:(\d+(?:\.\d+)?)s)?",
            low,
        )
        if wait:
            hours, minutes, seconds = (float(x or 0) for x in wait.groups())
            retry_after = hours * 3600 + minutes * 60 + seconds
    elif category != "invalid_provider_response" and (
        (
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
        )
    ):
        # An explicit provider-bank invalid-response classification is
        # authoritative. Do not upgrade it into a permanent structured-output
        # contract quarantine merely because the diagnostic mentions JSON.
        category = "structured_output_contract"
    elif "request too large" in low or ("context" in low and "length" in low):
        category = "request_too_large"

    delay = record_failure(
        state,
        category,
        text,
        retry_after=retry_after,
    )

    # Credential/quota failures belong to the provider account, not only the
    # model that happened to be attempted. Quarantine sibling models so the
    # bank does not retry the same broken credential against every model.
    # Model-specific rate limits remain isolated to preserve independent lanes.
    provider_wide = category in {"authentication", "quota_or_billing", "terms_required", "free_tier_daily_quota"}
    if provider_wide:
        until = time.time() + delay
        for key, sibling in _STATE["models"].items():
            if key == provider + ":" + model or not key.startswith(provider + ":"):
                continue
            sibling["state"] = "open"
            sibling["category"] = category
            sibling["last_error"] = text[:500]
            sibling["last_failure"] = time.time()
            sibling["probe_in_flight"] = False
            sibling["cooldown_until"] = 0.0
            sibling["quarantine_until"] = max(
                float(sibling.get("quarantine_until", 0) or 0),
                until,
            )

    print(
        "USE provider resilience: "
        f"provider={provider}, model={model}, state=open, category={category}, "
        f"cooldown_seconds={int(delay)}, provider_wide={str(provider_wide).lower()}"
    )
    _persist_shared_state()

def _record_quality_rejection(provider, model, operation, reason):
    """Penalize repeated contract failures for this operation/model pair."""
    state = _quality_state(operation, provider, model, create=True)
    now = time.time()
    last_quality_failure = float(state.get("last_quality_failure", 0) or 0)
    last_quality_success = float(state.get("last_quality_success", 0) or 0)
    if last_quality_success >= last_quality_failure:
        state["quality_failures"] = 0
    state["quality_failures"] = int(state.get("quality_failures", 0) or 0) + 1
    state["last_quality_failure"] = now
    state["quality_error"] = str(reason or "contract_rejection")[:300]
    # A visitor-facing contract rejection is already decisive evidence that this
    # operation/model pairing is unsuitable. Cool it down on the first rejection
    # so each new visitor turn does not repeatedly spend its bounded fallback slot
    # on the same known-bad voice. A later successful, validated result clears it.
    if state["quality_failures"] >= 1:
        state["quality_cooldown_until"] = max(
            float(state.get("quality_cooldown_until", 0) or 0),
            now + 300.0,
        )
    print(
        "USE provider quality resilience: "
        f"operation={operation}, provider={provider}, model={model}, "
        f"quality_failures={state['quality_failures']}, "
        f"quality_cooldown_seconds={max(0, int(float(state.get('quality_cooldown_until', 0) or 0) - now))}, "
        "reason=" + str(reason or "contract_rejection")[:180]
    )
    _persist_shared_state()


def _success(provider, model, operation):
    state = _state(provider, model)
    was_recovery = str(state.get("state") or "") == "half_open"
    record_success(state)
    quality = _quality_state(operation, provider, model, create=False)
    if quality:
        quality["last_quality_success"] = time.time()
        quality["quality_failures"] = 0
        quality["quality_cooldown_until"] = 0.0
        quality["quality_error"] = ""
    if was_recovery:
        print(
            "USE provider resilience: "
            f"provider={provider}, model={model}, recovery_probe=success, state=healthy"
        )
    _persist_shared_state()

def _http_json(url, headers, payload, provider, model, timeout=6):
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode("utf-8"),
        headers={**headers, "Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
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

def _text_mode(schema):
    return isinstance(schema, dict) and schema.get("mode") == "text"


def _ensure_json_object_instruction(messages, schema=None):
    """Make the JSON-object transport requirement explicit for every JSON-mode provider."""
    if _text_mode(schema):
        return messages
    for message in messages:
        content = message.get("content") if isinstance(message, dict) else None
        if "json" in str(content or "").casefold():
            return messages

    instruction = (
        "Return exactly one valid JSON object. Do not use Markdown fences or "
        "surrounding prose. Follow the requested output fields and types."
    )
    normalized = [dict(message) for message in messages]
    for index, message in enumerate(normalized):
        if message.get("role") == "system" and isinstance(message.get("content"), str):
            message["content"] = message["content"].rstrip() + "\n\n" + instruction
            return normalized
    normalized.insert(0, {"role": "system", "content": instruction})
    return normalized

def _groq(use_core, model, messages, max_tokens, schema=None):
    client = getattr(use_core, "groq_client", None)
    if client is None: raise ProviderCallError("Groq client unavailable", "groq", model, category="unavailable")
    kwargs = {"model": model, "messages": messages, "temperature": 0.0,
              "max_completion_tokens": max_tokens}
    if not _text_mode(schema):
        kwargs["response_format"] = ({"type": "json_schema", "json_schema": schema} if isinstance(schema, dict) else {"type": "json_object"})
    if model.startswith("openai/gpt-oss-"):
        kwargs["reasoning_effort"] = "low"; kwargs["include_reasoning"] = False
    elif model == "qwen/qwen3.8-27b":
        kwargs["reasoning_effort"] = "none"; kwargs["reasoning_format"] = "hidden"
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
        "thinkingConfig": {"thinkingLevel": "low"},
    }}
    if not _text_mode(schema):
        payload["generationConfig"]["responseMimeType"] = "application/json"
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
               "max_tokens": max_tokens}
    # NVIDIA Nemotron 3-series models can emit reasoning separately from the
    # visitor-facing content field. Disable thinking for the reviewed 3.5
    # Lightning and 3 Super models so the bounded contract receives actual text.
    # The normal schema and visitor-surface validators remain authoritative.
    if provider == "nvidia" and model in {
        "nvidia/nemotron-3.5-lightning-30b-a3b",
        "nvidia/nemotron-3-super-120b-a12b",
    }:
        payload["chat_template_kwargs"] = {"enable_thinking": False}
    json_mode = not _text_mode(schema)
    # OpenRouter may dynamically route to free models that reject the OpenAI
    # response_format extension or return an empty transport envelope. Keep the
    # JSON-object instruction in the messages and let the Provider Bank contract
    # validator enforce the actual visitor-facing schema.
    if json_mode and provider != "openrouter":
        payload["response_format"] = ({"type": "json_schema", "json_schema": schema} if isinstance(schema, dict) else {"type": "json_object"})
    url = base_url.rstrip("/") + "/chat/completions"
    headers = {"Authorization": "Bearer " + key}

    def request(current_payload):
        try:
            # NVIDIA hosted inference has previously exceeded the generic 6s
            # transport budget. Give the bounded NVIDIA attempt 12s while keeping
            # every other provider at the existing default timeout.
            if provider == "nvidia":
                data = _http_json(url, headers, current_payload, provider, model, timeout=12)
            else:
                data = _http_json(url, headers, current_payload, provider, model)
        except json.JSONDecodeError as exc:
            raise ProviderCallError(
                provider + " returned an empty or non-JSON HTTP response",
                provider, model, category="invalid_provider_response"
            ) from exc
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderCallError(
                provider + " returned no text", provider, model,
                category="invalid_provider_response"
            ) from exc
        content = str(content or "").strip()
        if not content:
            raise ProviderCallError(
                provider + " returned empty message content", provider, model,
                category="invalid_provider_response"
            )
        return content

    try:
        return request(payload)
    except ProviderCallError as exc:
        # The OpenRouter free router can select different upstream models, and
        # not every free endpoint honors OpenAI's response_format extension.
        # Retry once without that transport hint; the prompt still explicitly
        # requires one JSON object and the HRN contract validator remains final.
        if (
            provider != "openrouter"
            or not json_mode
            or "response_format" not in payload
            or exc.category != "invalid_provider_response"
        ):
            raise
        retry_payload = dict(payload)
        retry_payload.pop("response_format", None)
        print(
            "USE OpenRouter transport recovery: retrying once without "
            "response_format after empty/non-JSON response"
        )
        return request(retry_payload)

def _workers_extract_text(result):
    """Extract text from supported Workers AI response shapes."""
    if isinstance(result, str):
        return result.strip()
    if not isinstance(result, dict):
        return ""
    for key in ("response", "text", "output", "generated_text", "content"):
        value = result.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, dict):
            for nested_key in ("text", "content", "response"):
                nested = value.get(nested_key)
                if isinstance(nested, str) and nested.strip():
                    return nested.strip()
        if isinstance(value, list):
            chunks = []
            for item in value:
                if isinstance(item, str) and item.strip():
                    chunks.append(item.strip())
                elif isinstance(item, dict):
                    chunk = item.get("text") or item.get("content")
                    if isinstance(chunk, str) and chunk.strip():
                        chunks.append(chunk.strip())
            if chunks:
                return "\\n".join(chunks).strip()
    choices = result.get("choices")
    if isinstance(choices, list):
        for choice in choices:
            if not isinstance(choice, dict):
                continue
            message = choice.get("message")
            if isinstance(message, dict):
                content = message.get("content")
                if isinstance(content, str) and content.strip():
                    return content.strip()
                if isinstance(content, list):
                    chunks = [
                        item.get("text", "").strip()
                        for item in content
                        if isinstance(item, dict) and isinstance(item.get("text"), str) and item.get("text").strip()
                    ]
                    if chunks:
                        return "\\n".join(chunks).strip()
            choice_text = choice.get("text")
            if isinstance(choice_text, str) and choice_text.strip():
                return choice_text.strip()
    return ""


def _workers_response_diagnostic(data):
    """Return response-shape metadata without logging generated content or credentials."""
    result = data.get("result") if isinstance(data, dict) else None
    diagnostic = {
        "result_type": type(result).__name__,
        "result_keys": sorted(result.keys()) if isinstance(result, dict) else [],
        "response_type": type(result.get("response")).__name__ if isinstance(result, dict) and "response" in result else "missing",
        "response_chars": len(result.get("response")) if isinstance(result, dict) and isinstance(result.get("response"), str) else None,
    }
    errors = data.get("errors") if isinstance(data, dict) else None
    if isinstance(errors, list):
        diagnostic["errors"] = [
            {"code": item.get("code"), "message": str(item.get("message", ""))[:180]}
            for item in errors[:3] if isinstance(item, dict)
        ]
    return diagnostic


def _workers_url(account, model):
    """Build a Workers AI route while preserving model path separators."""
    account_path = urllib.parse.quote(str(account), safe="")
    model_path = urllib.parse.quote(str(model), safe="/@")
    return "https://api.cloudflare.com/client/v4/accounts/" + account_path + "/ai/run/" + model_path


def _workers(key, account, model, messages, max_tokens, schema=None, timeout=12):
    payload = {"messages": messages, "max_tokens": max_tokens, "temperature": 0.0,
               "options": {"rejectIfBusy": True}}
    if _text_mode(schema):
        payload["response_format"] = {"type": "text"}
    else:
        payload["response_format"] = {"type": "json_schema", "json_schema": schema["schema"]} if isinstance(schema, dict) and isinstance(schema.get("schema"), dict) else {"type": "json_object"}
    if model == "@cf/google/gemma-4-26b-a4b-it":
        payload["chat_template_kwargs"] = {"enable_thinking": False}
    url = _workers_url(account, model)
    data = _http_json(url, {"Authorization": "Bearer " + key}, payload, "workers_ai", model, timeout=timeout)
    result = data.get("result") if isinstance(data, dict) else None
    text = _workers_extract_text(result)
    if not text:
        diagnostic = _workers_response_diagnostic(data)
        raise ProviderCallError(
            "Workers AI returned no text; " + json.dumps(diagnostic, sort_keys=True),
            "workers_ai",
            model,
            category="invalid_provider_response",
        )
    return text

def _cloudflare_credentials():
    """Read canonical Cloudflare credentials without pasted whitespace."""
    token = str(os.getenv("CLOUDFLARE_API_TOKEN") or "").strip()
    account = str(os.getenv("CLOUDFLARE_ACCOUNT_ID") or "").strip()
    return token, account


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
    # Optional zero-cost fallback lane. It is dormant unless a key is configured;
    # OpenRouter routes openrouter/free across currently available free models.
    if os.getenv("OPENROUTER_API_KEY"):
        out["openrouter"] = _csv("USE_OPENROUTER_MODELS") or [
            "openrouter/free",
            "nvidia/nemotron-3-ultra-550b-a55b:free",
            "google/gemma-4-31b-it:free",
        ]
    if os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_GEMINI_API_KEY"):
        out["gemini"] = resolve_model_list("gemini", _csv("USE_GEMINI_MODELS") or ["gemini-3.8-flash"])
    if os.getenv("MISTRAL_API_KEY"):
        out["mistral"] = _csv("USE_MISTRAL_MODELS") or ["mistral-small-latest"]
    nvidia_key = str(os.getenv("NVIDIA_API_KEY") or "").strip()
    # A deployment placeholder is deliberately not treated as a usable secret.
    if nvidia_key and not nvidia_key.casefold().startswith(("replace_with_", "your_", "placeholder")):
        nvidia_models = _csv("USE_NVIDIA_MODELS")
        if nvidia_models:
            out["nvidia"] = list(dict.fromkeys(resolve_nvidia_model_id(model) for model in nvidia_models))
    cloudflare_token, cloudflare_account = _cloudflare_credentials()
    if cloudflare_token and cloudflare_account:
        gateway = _csv("USE_CLOUDFLARE_GATEWAY_MODELS")
        workers = _csv("USE_WORKERS_AI_MODELS")
        if gateway: out["cloudflare_gateway"] = gateway
        # Keep operator-selected Workers AI models first, but retain one documented
        # fast fallback lane so an unavailable/slow model does not exhaust the bank.
        fast_fallback = "@cf/meta/llama-3.3-70b-instruct-fp8-fast"
        if workers: out["workers_ai"] = list(dict.fromkeys(workers + [fast_fallback]))
        elif not gateway: out["workers_ai"] = ["@cf/google/gemma-4-26b-a4b-it", "@cf/zai-org/glm-4.7-flash", fast_fallback]
    return out

def _capabilities(provider, model):
    return MODEL_CAPABILITIES.get((provider, model), frozenset())

def _operation_requirements(operation, schema):
    required = set(OPERATION_REQUIREMENTS.get(operation, frozenset()))
    if isinstance(schema, dict) and schema.get("mode") == "text":
        return required
    if isinstance(schema, dict):
        required.add("json_schema_strict" if bool(schema.get("strict")) else "json_schema_best_effort")
    return required

def _eligible(provider, model, operation, schema=None):
    required = _operation_requirements(operation, schema)
    capabilities = _capabilities(provider, model)
    missing = required.difference(capabilities)
    if missing:
        return False, sorted(missing)
    return True, []

def candidates(use_core, operation="generic", schema=None):
    global _LAST_PROVIDER_INVENTORY_DIAGNOSTIC
    out = []
    now = time.time()
    configured_models = _configured(use_core)
    inventory_signature = (
        bool(str(os.getenv("OPENROUTER_API_KEY") or "").strip()),
        tuple(sorted((provider, tuple(models)) for provider, models in configured_models.items())),
    )
    if inventory_signature != _LAST_PROVIDER_INVENTORY_DIAGNOSTIC:
        providers = ",".join(
            provider + ":" + str(len(models))
            for provider, models in configured_models.items()
        ) or "none"
        print(
            "USE provider bank inventory: "
            f"openrouter_key_configured={str(inventory_signature[0]).lower()}, "
            f"configured_lanes={providers}"
        )
        _LAST_PROVIDER_INVENTORY_DIAGNOSTIC = inventory_signature
    for provider, models in configured_models.items():
        for index, model in enumerate(models):
            health = _state(provider, model)
            if _blocked(health):
                blocked_until = max(
                    float(health.get("cooldown_until", 0) or 0),
                    float(health.get("quarantine_until", 0) or 0),
                )
                print(
                    "USE provider bank exclusion: "
                    f"operation={operation}, provider={provider}, model={model}, "
                    f"state={health.get('state') or 'unknown'}, "
                    f"category={health.get('category') or 'unknown'}, "
                    f"retry_in_seconds={max(0, int(blocked_until - now))}"
                )
                continue
            quality = _quality_state(operation, provider, model, create=False)
            quality_until = float(quality.get("quality_cooldown_until", 0) or 0)
            if quality_until > now:
                print(
                    "USE provider quality exclusion: "
                    f"operation={operation}, provider={provider}, model={model}, "
                    f"reason=contract_rejection, retry_in_seconds={int(quality_until - now)}"
                )
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
                "quality_failures": int(quality.get("quality_failures", 0) or 0),
                "health_state": str(health.get("state") or "unknown"),
                "transport_failures": int(health.get("failures", 0) or 0),
                "consecutive_failures": int(health.get("consecutive_failures", 0) or 0),
                # Recent success is cross-operation evidence that a model is
                # currently usable. HRN perception and composition share one
                # visitor turn, so a model that just succeeded in perception
                # should outrank a sibling model with stale quota health.
                "last_success": float(health.get("last_success", 0) or 0),
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
    # OpenRouter is the preferred free lane whenever its credential enables it.
    # Preserve an explicit provider order if it names OpenRouter; otherwise
    # prepend OpenRouter even when an older environment order lists only the
    # legacy providers. This prevents the bounded attempt window from starving
    # the configured lane before it can be reached.
    if "openrouter" in grouped and "openrouter" not in configured:
        configured = ["openrouter"] + configured
    providers = [x for x in configured if x in grouped] + [x for x in grouped if x not in configured]
    # HRN invokes several semantic operations within one visitor turn. Rotating
    # the provider lane on every stage makes a healthy primary disappear behind
    # transient providers before the bounded two-candidate window can reach it.
    # Keep the configured provider priority stable for HRN; health/capability
    # filtering still removes unusable candidates, and the normal fallback lane
    # remains available. Other USE operations retain round-robin arbitration.
    if operation not in {"hrn_perception", "hrn_relational", "hrn_voice_repair"}:
        providers = _rotate(providers, int(_STATE["provider_cursor"]))
        _STATE["provider_cursor"] += 1
    lanes = []
    for provider in providers:
        models = grouped[provider]
        cursor = int(_STATE["model_cursors"].get(provider, 0))
        models = _rotate(models, cursor)
        # Keep configured provider priority, but prefer models with better
        # visitor-contract history within each provider lane.
        if operation in {"hrn_perception", "hrn_relational", "hrn_voice_repair"}:
            # Keep HRN's most recently proven model first within each provider
            # lane. A model can succeed at perception, then the next stage must
            # not rotate to a sibling that has exhausted its model-scoped quota.
            # A transport-unhealthy model must not outrank a currently
            # healthy model merely because it has fewer recorded visitor-contract
            # rejections. Half-open candidates are probes, not proven fallbacks.
            # Within the same health tier, preserve quality history and recent success.
            models.sort(key=lambda item: (
                0 if item.get("health_state") == "healthy" else 1,
                int(item.get("quality_failures", 0) or 0),
                int(item.get("consecutive_failures", 0) or 0),
                int(item.get("transport_failures", 0) or 0),
                -float(item.get("last_success", 0) or 0),
            ))
        else:
            models.sort(key=lambda item: int(item.get("quality_failures", 0) or 0))
        _STATE["model_cursors"][provider] = cursor + 1
        lanes.append(models)

    # HRN's two-attempt ceiling makes provider-lane order operationally
    # significant. Rank eligible lanes by observed health and operation-specific
    # contract history before using operator order as a tie-breaker. This keeps
    # a stale configured priority from starving a healthier, better-performing
    # independent provider while preserving deterministic arbitration.
    if operation in {"hrn_perception", "hrn_relational", "hrn_voice_repair"}:
        configured_priority = {name: index for index, name in enumerate(providers)}
        def _hrn_lane_priority(lane):
            best = lane[0] if lane else {}
            health_rank = 0 if any(item.get("health_state") == "healthy" for item in lane) else 1
            quality_rank = min((int(item.get("quality_failures", 0) or 0) for item in lane), default=10**9)
            consecutive_rank = min((int(item.get("consecutive_failures", 0) or 0) for item in lane), default=10**9)
            transport_rank = min((int(item.get("transport_failures", 0) or 0) for item in lane), default=10**9)
            recent_success_rank = -max((float(item.get("last_success", 0) or 0) for item in lane), default=0.0)
            provider = str(best.get("provider") or "")
            return (health_rank, quality_rank, consecutive_rank, transport_rank,
                    recent_success_rank, configured_priority.get(provider, len(configured_priority)))
        lanes.sort(key=_hrn_lane_priority)

    # A bounded HRN stage must have a genuinely independent fallback. Flattening
    # provider lanes lets two models from one provider consume both attempts,
    # defeating cross-provider recovery. Interleave HRN candidates by lane:
    # first choice from each eligible provider, then second choices, preserving
    # stable provider priority and existing health/capability/quality filters.
    selected = []
    if operation in {"hrn_perception", "hrn_relational", "hrn_voice_repair"}:
        for depth in range(max((len(lane) for lane in lanes), default=0)):
            for lane in lanes:
                if depth < len(lane):
                    selected.append(lane[depth])
    else:
        for lane in lanes:
            selected.extend(lane)
    return selected

def _complete_response_prefix(response):
    """Keep complete prose and trim only an unfinished trailing sentence."""
    text = str(response or "").rstrip()

    def ends_sentence(value):
        candidate = value.rstrip()
        while candidate and candidate[-1] in ('"', "'", "”", "’", ")", "]", "}"):
            candidate = candidate[:-1].rstrip()
        return bool(candidate and candidate[-1] in ".!?…")

    if ends_sentence(text):
        return text
    boundaries = list(re.finditer(r"[.!?…][\"'”’\)\]\}]*\s+", text))
    if not boundaries:
        return ""
    candidate = text[:boundaries[-1].end()].rstrip()
    return candidate if ends_sentence(candidate) else ""


def _hrn_surface_language_violation(response):
    """Reject known internal-process phrases from visitor-facing HRN composition."""
    text = str(response or "").casefold()
    if text.startswith("what becomes visible when"):
        return "formulaic-abstract-question"
    if text.startswith("what does that reveal about the relationship that was harder to see before"):
        return "formulaic-abstract-question"
    if re.search(r"\bwhat feels different when you hold (?:those(?:\s+two)?|both|the two) sides together\b", text):
        return "formulaic-abstract-question"
    forbidden = (
        "the brief identifies",
        "the movement brief",
        "the visitor contribution",
        "the current understanding",
        "specific facts of the relationship",
        "grounded in your actual experience",
        "the current state of the interaction",
        "to move from a general desire",
        "the observer indicates",
        "the interpretation indicates",
        "you can frame each interaction",
        "setting clear, flexible boundaries",
        "this opens the possibility of",
        "this small change in framing can help",
        "it makes sense that you are looking for a way to bridge the gap",
        "if we look at reaching out not as",
        "you are offering a choice rather than",
        "can help you feel less like",
        "the dynamic shifts",
        "open door",
        "in many relational dynamics",
        "necessary condition for it to re-emerge",
        "when you view distance as a pause rather than a rejection",
        "the act of reaching out shifts from",
        "invitation to re-engage",
        "had time to process",
        "the friction you are feeling often stems from",
        "a concrete shift in the relationship is the move from",
        "rather than a binary win or loss",
        "there is a distinct difference between defining a boundary and enforcing it",
        "defining it is an internal act",
        "external interaction with the other person",
        "the immediate dynamics of the conversation",
        "opens the possibility of",
        "pause before reacting",
        "choosing a stance",
        "physical or emotional gap",
        "what once felt like",
        "the way you interpret each other's actions",
        "more grounded",
        "it sounds like",
        "it seems like",
        "it sounds as though",
        "it seems as though",
        "you have noticed",
        "you are dealing with",
        "what you are experiencing",
        "your instinct",
        "it is important for you",
        "this is a protective stance",
        "a protective stance you have learned",
        "can keep the surface calm",
        "keeps the deeper feelings",
        "keeps the deeper needs",
        "may feel more distant over time",
        "can feel more distant over time",
        "hidden defense",
        "defensive pattern",
        "coping strategy",
        "coping mechanism",
        "protecting the relationship",
        "protecting your relationship",
        "blocks genuine intimacy",
        "blocks intimacy",
        "self-imposed safety",
        "you are operating from a place of guilt",
        "you are operating from a place of agency",
        "managing your own anxiety about being unwanted",
        "extending a hand without demands",
        "this distinction matters because",
        "it shifts the focus from",
        "an offer of connection that they are free to accept or decline",
        "the pull toward intimacy",
        "threat to your autonomy",
        "the same emotional energy",
        "bridge and a boundary",
        "the effort beneath the thing",
        "structural capacity of the relationship",
        "current level of intimacy or demand",
        "when a relationship hits a limit",
        "distance often appears as a sudden withdrawal",
        "gradual accumulation of unmet needs",
        "mismatched expectations that the system can no longer sustain",
        "the system can no longer sustain",
        "a change in the structural capacity",
        "confirm your worth",
        "need for reassurance",
        "the other person's autonomy can feel like a rejection rather than a boundary",
        "seeing this distinction allows you to",
        "act from genuine care rather than anxiety",
        "separate your internal need from their external choice",
    )
    matched = next((phrase for phrase in forbidden if phrase in text), "")
    if matched:
        return matched
    patterns = (
        ("action-guidance", r"\b(?:it|this|that)\s+(?:allows|enables|helps|means)\s+you\s+to\b"),
        ("action-guidance", r"\b(?:you can|you could|you might want to)\s+(?:set|establish|stabilize|enforce|frame|approach|try|consider|focus|decide|reach out|give them space)\b"),
        ("action-guidance", r"\b(?:before|when) engaging with the other (?:person|party)\b"),
        ("action-guidance", r"\b(?:preventing|ensuring|allowing) the (?:decision|choice|response)\b"),
        ("action-guidance", r"\b(?:stabilize|enforce|set) your (?:own )?(?:position|boundary|boundaries)\b"),
        ("abstract-generalization", r"\b(?:in many|often stems from|a common pattern is|relationships often)\b"),
        ("action-guidance", r"\b(?:lets|allows|helps) you (?:pause|choose|decide|frame|act|respond|engage|set|stabilize)\b"),
        ("abstract-generalization", r"\bopens the possibility of\b"),
        ("abstract-generalization", r"\b(?:physical or emotional gap|choosing a stance|more grounded)\b"),
        ("metaphorical-framing", r"\bwhat once felt like\b"),
        ("action-guidance", r"\bseeing (?:that|this) shift as .{0,100} lets you\b"),
        ("action-guidance", r"\byou\s+(?:should|must|need to|have to|ought to)\b"),
        ("action-guidance", r"\byou\s+(?:might|could|can|may)\s+try\b"),
        ("action-guidance", r"\b(?:the|your)\s+(?:best|right|next)\s+(?:thing|step|move|choice|decision)\s+(?:is|would be)\b"),
        ("action-guidance", r"\b(?:a|an)\s+(?:good|helpful|healthy|wise)\s+(?:next|first)\s+(?:step|thing|move|choice)\s+(?:is|would be)\b"),
        ("therapeutic-or-inferred", r"\b(?:they are|he is|she is)\s+(?:toxic|abusive|a narcissist|manipulating you)\b"),
        ("formulaic-connective", r"\bif you (?:view|see|frame|treat) .{0,160}\b(?:you are|you're|this means)\b"),
        ("unsupported-internal-state", r"\b(?:you are|you're) operating from a place of\b"),
        ("unsupported-relationship-causal-theory", r"\b(?:likely|frequently|often) (?:the result of|caused by|due to)\b"),
        ("unsupported-relationship-causal-theory", r"\b(?:unmet needs|mismatched expectations|structural capacity)\b"),
        ("unsupported-relationship-causal-theory", r"\b(?:the relationship|a relationship) (?:hits|has reached|reaches) a limit\b"),
        ("unsupported-relationship-causal-theory", r"\bthe distance often appears as\b"),
        ("prescriptive-language", r"\byou\s+(?:should|must|need to|have to|ought to|are supposed to)\b"),
        ("prescriptive-language", r"\byou\s+(?:might|could|can|may)\s+try\b"),
        ("prescriptive-language", r"\byou\s+(?:need|have)\s+to\s+(?:talk|ask|tell|leave|stay|set|change|stop|start|contact|call|reach|write|say|do|make|avoid|create|invite|confront|forgive|accept|let)\b"),
        ("prescriptive-language", r"\byou\s+(?:might|could|can|may)\s+consider\b"),
        ("prescriptive-language", r"\byou\s+(?:try|choose|decide|start|stop|avoid|leave|stay|contact|call|reach out|talk to|tell|ask|say|write|set|change|make|invite|confront)\b"),
        ("prescriptive-language", r"\b(?:i|we)\s+(?:recommend|advise|suggest)\s+(?:you|that you)\b"),
        ("prescriptive-language", r"(?:^|[.!?]\s+)\s*(?:try|consider|avoid|stop|start|tell|ask|call|contact|leave|stay|go|write|say|set|change|make|invite|forgive)\s+(?:to|doing|the|a|an|your|them|him|her|it|someone|anyone|people|this|that|with)\b"),
        ("prescriptive-language", r"\b(?:what you should do|what you need to do|what you must do|what you ought to do)\b"),
        ("prescriptive-language", r"\bdo not\s+(?:stay|leave|contact|call|talk|ask|tell|try|forgive|change|ignore|respond|engage|return|go|make)\b"),
    )
    return next((label for label, pattern in patterns if re.search(pattern, text)), "")


def _apply_hrn_visitor_contract(messages):
    """Apply the same visitor-facing language contract to every eligible provider."""
    contract = (
        "HRN VISITOR-FACING LANGUAGE CONTRACT: Speak directly to this visitor in "
        "plain, concrete, natural language. Use the visitor's actual material, not "
        "generic claims about relationships. Be perceptive without pretending to "
        "know another person's motives. Do not advise, prescribe, coach, or tell "
        "the visitor to take an action or change their framing. Do not assign feelings, "
        "motives, guilt, anxiety, or agency that the visitor has not stated. Do not "
        "use formulaic connective sentences such as 'This distinction matters because' "
        "or 'It shifts the focus from'. Avoid metaphors, literary phrasing, and "
        "impressive-sounding generalizations unless the "
        "visitor introduced that exact language. If the evidence is limited, offer "
        "one modest observation grounded in what was said and one relevant question. "
        "Never refer to a brief, prompt, interpretation, internal state, or the "
        "visitor contribution as an object being processed."
    )
    result = [dict(item) if isinstance(item, dict) else item for item in messages]
    for item in result:
        if isinstance(item, dict) and item.get("role") == "system":
            item["content"] = str(item.get("content") or "") + "\n\n" + contract
            return result
    result.insert(0, {"role": "system", "content": contract})
    return result


def _apply_hrn_voice_repair_contract(messages):
    """Keep the existing repair operation plain, grounded, and non-prescriptive."""
    contract = (
        "HRN VOICE-REPAIR CONTRACT: Rewrite only the response prose already supplied. "
        "Use ordinary, concrete language and stay close to what the visitor actually said. "
        "Remove unsupported explanations of why the relationship changed, hidden needs, "
        "anxiety, worth, autonomy, unmet needs, mismatched expectations, structural capacity, "
        "or claims about what either person is feeling unless the visitor explicitly stated it. "
        "Avoid metaphors and abstract relationship theory. Do not advise, prescribe, diagnose, "
        "promise an outcome, or tell the visitor what to do. Do not add a question, labels, "
        "or internal process language. Prefer one modest observation that can be traced to "
        "the visitor's words over a more impressive explanation. Return only the repair format "
        "required by the current operation."
    )
    result = [dict(item) if isinstance(item, dict) else item for item in messages]
    for item in result:
        if isinstance(item, dict) and item.get("role") == "system":
            item["content"] = str(item.get("content") or "") + "\n\n" + contract
            return result
    result.insert(0, {"role": "system", "content": contract})
    return result


def _repair_leading_hrn_hedge(response):
    """Replace only a leading hedge with a grounded, still-qualified reflection."""
    text = str(response or "").strip()
    patterns = (
        r"^it sounds like\s+you\s+",
        r"^it seems like\s+you\s+",
        r"^it sounds as though\s+you\s+",
        r"^it seems as though\s+you\s+",
    )
    for pattern in patterns:
        repaired, count = re.subn(pattern, "From what you describe, you ", text, count=1, flags=re.IGNORECASE)
        if count:
            return repaired
    return text


def _normalize_operation_result(operation, parsed):
    if operation == "hrn_relational":
        response = parsed.get("response")
        question = parsed.get("question")
        if not isinstance(response, str) or not response.strip():
            raise ValueError("hrn_relational composition contract requires response")
        if not isinstance(question, str) or not question.strip():
            raise ValueError("hrn_relational composition contract requires question")
        question_violation = _hrn_surface_language_violation(question)
        if question_violation:
            raise ValueError(
                "hrn_relational question-surface contract violation: "
                + question_violation
            )
        repaired_response = _repair_leading_hrn_hedge(response)
        if repaired_response != response.strip():
            print("USE provider response hedge normalized: operation=hrn_relational")
        response = repaired_response
        parsed["response"] = response
        surface_violation = _hrn_surface_language_violation(response)
        if surface_violation:
            raise ValueError(
                "hrn_relational visitor-surface contract violation: "
                + surface_violation
            )
        # Do not let a syntactically valid JSON object conceal a cut-off
        # visitor-facing sentence. Preserve complete sentences and discard only
        # the unfinished trailing sentence; never invent replacement prose.
        completed = _complete_response_prefix(response)
        if not completed:
            raise ValueError("hrn_relational composition contract requires a complete response")
        # Match HRN's downstream ordinary_response_shape_valid contract here,
        # so a short provider draft is repaired/fails over inside the bank rather
        # than reaching HRN as a transport-successful bad shape.
        sentence_parts = [part for part in re.split(r"(?<=[.!?])\s+", completed) if part.strip()]
        if len(completed) < 180 or len(sentence_parts) < 2:
            raise ValueError(
                "hrn_relational response shape requires at least two complete sentences and 180 characters"
            )
        if completed != response.strip():
            print(
                "USE provider response tail trimmed: operation=hrn_relational, "
                f"original_chars={len(response)}, retained_chars={len(completed)}"
            )
        parsed["response"] = completed
        # These are transport/envelope controls, not semantic content. Supplying
        # their neutral values keeps provider variation from leaking into HRN's
        # frozen composition validator.
        if "rest" not in parsed:
            parsed["rest"] = False
        if "use_resource" not in parsed:
            parsed["use_resource"] = False
        if "resource_intro" not in parsed:
            parsed["resource_intro"] = ""
    return parsed

def _call(use_core, item, messages, max_tokens, schema=None, timeout_override=None):
    provider, model = item["provider"], item["model"]
    if provider == "openrouter":
        key = os.getenv("OPENROUTER_API_KEY")
        if not key:
            raise ProviderCallError("OpenRouter API key unavailable", provider, model, category="unavailable")
        return _openai_compatible("https://openrouter.ai/api/v1", key, provider, model, messages, max_tokens, schema)
    if provider == "groq": return _groq(use_core, model, messages, max_tokens, schema)
    if provider == "gemini":
        key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_GEMINI_API_KEY")
        if not key: raise ProviderCallError("Gemini API key unavailable", provider, model, category="unavailable")
        return _gemini(key, model, messages, max_tokens, schema)
    if provider == "mistral":
        key = os.getenv("MISTRAL_API_KEY")
        if not key: raise ProviderCallError("Mistral API key unavailable", provider, model, category="unavailable")
        return _openai_compatible("https://api.mistral.ai/v1", key, provider, model, messages, max_tokens, schema)
    if provider == "nvidia":
        key = str(os.getenv("NVIDIA_API_KEY") or "").strip()
        if not key or key.casefold().startswith(("replace_with_", "your_", "placeholder")):
            raise ProviderCallError("NVIDIA API key unavailable", provider, model, category="unavailable")
        return _openai_compatible("https://integrate.api.nvidia.com/v1", key, provider, model, messages, max_tokens, schema)
    if provider == "cloudflare_gateway":
        token, account = _cloudflare_credentials()
        if not token or not account: raise ProviderCallError("Cloudflare credentials unavailable", provider, model, category="unavailable")
        base = "https://api.cloudflare.com/client/v4/accounts/" + urllib.parse.quote(account, safe="") + "/ai/v1"
        return _openai_compatible(base, token, provider, model, messages, max_tokens, schema)
    if provider == "workers_ai":
        token, account = _cloudflare_credentials()
        if not token or not account: raise ProviderCallError("Workers AI credentials unavailable", provider, model, category="unavailable")
        return _workers(token, account, model, messages, max_tokens, schema, timeout=timeout_override or 12)
    raise ProviderCallError("unknown provider", provider, model, category="unavailable")

def route(*, use_core, messages, max_tokens, parse, operation="generic", schema=None):
    _sync_shared_state()
    # Do not infer strict schemas from the operation. A specialist must
    # explicitly request one; otherwise the bank uses JSON-object mode.
    effective_schema = schema if isinstance(schema, dict) else None
    effective_messages = _ensure_json_object_instruction(messages, effective_schema)
    if operation == "hrn_relational":
        effective_messages = _apply_hrn_visitor_contract(effective_messages)
    elif operation == "hrn_voice_repair":
        effective_messages = _apply_hrn_voice_repair_contract(effective_messages)
    pool = select(use_core, operation=operation, schema=effective_schema)
    if not pool: return None
    order = [x["provider"] + ":" + x["model"] for x in pool]
    last_error = ""
    configured_attempts = max(1, min(5, int(os.getenv("USE_PROVIDER_BANK_MAX_ATTEMPTS", "5") or 5)))
    # HRN runs several semantic stages inside one WordPress turn. Allowing every
    # stage to fan out across five providers multiplies the outer turn budget and
    # leaves the visitor staring at the first page. Keep each HRN operation to
    # two candidates: one primary and one independent fallback. The existing
    # same-candidate contract correction remains bounded to one additional call.
    hrn_operations = {"hrn_perception", "hrn_relational", "hrn_voice_repair"}
    operation_attempt_cap = 2 if operation in hrn_operations else configured_attempts
    max_attempts = min(len(pool), operation_attempt_cap)
    requested_max_tokens = max(int(max_tokens), int(OPERATION_TOKEN_FLOORS.get(operation, 0)))
    # HRN relational prose needs a complete answer and a distinct question, not a
    # thousand-token draft. Bound these visitor-facing stages so multiple semantic
    # stages can finish inside one WordPress turn; keep perception's richer schema uncapped.
    if operation in {"hrn_relational", "hrn_voice_repair"}:
        requested_max_tokens = min(requested_max_tokens, 600)
    for attempt_index, item in enumerate(pool[:max_attempts], start=1):
        model_limit = int(MODEL_LIMITS.get((item["provider"], item["model"]), {}).get("max_completion_tokens", 0) or 0)
        effective_max_tokens = min(requested_max_tokens, model_limit) if model_limit > 0 else requested_max_tokens
        if effective_max_tokens < requested_max_tokens:
            print(
                "USE provider capability ceiling: "
                f"operation={operation}, provider={item['provider']}, model={item['model']}, "
                f"requested={requested_max_tokens}, ceiling={model_limit}, effective={effective_max_tokens}"
            )
        provider, model = item["provider"], item["model"]
        state = _state(provider, model)
        # The candidate pool is a snapshot created before this attempt loop.
        # A preceding candidate can open a provider-wide circuit after the pool
        # was built (for example, daily quota exhaustion). Re-check current state
        # immediately before every call so stale sibling candidates are not sent
        # to an account that has just been quarantined.
        if _blocked(state):
            print(
                "USE model bank skip newly blocked candidate: "
                f"provider={provider}, model={model}, "
                f"category={state.get('category') or 'unknown'}"
            )
            continue
        if not acquire_probe(state):
            continue
        try:
            print("USE model bank attempt: provider=" + provider + ", model=" + model +
                  ", state=" + str(state.get("state") or "healthy"))
            raw_output = _call(use_core, item, effective_messages, effective_max_tokens, effective_schema, timeout_override=8 if operation in hrn_operations else None)
            try:
                parsed = parse(raw_output)
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                # Transport-successful but unparsable output is a provider
                # response failure, not an application-owned composition
                # rejection. Record health and move to the next eligible lane.
                raise ProviderCallError(
                    provider + "/" + model + " returned invalid JSON",
                    provider, model, category="invalid_provider_response"
                ) from exc
            if not isinstance(parsed, dict):
                raise ProviderCallError(
                    provider + "/" + model + " returned a non-object response",
                    provider, model, category="invalid_provider_response"
                )
            try:
                parsed = _normalize_operation_result(operation, parsed)
            except ValueError as contract_error:
                recovery_schema = OPERATION_SCHEMAS.get(operation + "_recovery")
                if not recovery_schema:
                    raise
                schema_capable = bool(_capabilities(provider, model).intersection({"json_schema_strict", "json_schema_best_effort"}))
                recovery_mode_schema = recovery_schema if schema_capable else effective_schema
                recovery_mode = "strict_schema" if schema_capable else "provider_neutral_json_object"
                print("USE provider contract recovery: operation=" + operation + ", provider=" + provider + ", model=" + model + ", mode=" + recovery_mode)
                # A schema-only retry repeats the same prompt and gives the model no
                # information about why its previous object was rejected. Carry the
                # rejected output forward and ask for a bounded contract correction.
                # This stays at the Provider Bank boundary; specialist voice methods
                # and provider selection remain untouched.
                recovery_messages = list(effective_messages)
                recovery_messages.append({
                    "role": "assistant",
                    "content": str(raw_output or "")[:12000],
                })
                recovery_messages.append({
                    "role": "user",
                    "content": (
                        "Your preceding output failed the HRN relational response contract: "
                        + str(contract_error)[:240]
                        + ". Correct the output now. Return only one valid JSON object with "
                        + "a non-empty visitor-facing response string and a non-empty next question string. "
                        + "The response must contain at least two complete sentences and 180 characters. "
                        + "Include rest as a boolean, use_resource as a boolean, and resource_intro as a string. "
                        + "The response must be complete, end with sentence-final punctuation, and never stop mid-sentence. "
                        + "Speak directly to the visitor. Never refer to a brief, prompt, interpretation, internal state, or the visitor contribution as an object being processed. "
                        + "Do not explain the contract or omit response/question. Preserve the visitor's context. "
                        "Do not repeat the rejected wording or any canned explanatory transition, including "
                        "phrases such as 'this distinction matters because' or 'it shifts the focus from'. "
                        "Avoid generic relationship theory, abstract labels, and prescriptive advice. "
                        "Use one concrete observation grounded in the visitor's actual words, then ask a "
                        "genuinely different, open question. Do not restate the same insight in new words."
                    ),
                })
                recovered = parse(_call(use_core, item, recovery_messages, effective_max_tokens, recovery_mode_schema, timeout_override=8 if operation in hrn_operations else None))
                if not isinstance(recovered, dict):
                    raise ValueError("provider contract recovery returned a non-object")
                parsed = _normalize_operation_result(operation, recovered)
            print(
                "USE provider contract result: "
                f"operation={operation}, provider={provider}, model={model}, "
                f"keys={sorted(str(k) for k in parsed.keys())}, "
                f"types={{" + ",".join(f"{k}:{type(v).__name__}" for k, v in parsed.items()) + "}}"
            )
            _success(provider, model, operation)
            return {"parsed": parsed, "provider": provider, "model": model, "preference_order": order}
        except ValueError as exc:
            # Preserve transport health, but learn from repeated visitor-contract
            # failures so poor outputs lose priority and can be cooled down.
            last_error = str(exc)
            _record_quality_rejection(provider, model, operation, last_error)
            print(
                "USE provider composition contract rejection: "
                + "operation=" + operation
                + ", provider=" + provider
                + ", model=" + model
                + ", error=" + last_error[:300]
            )
            continue
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
        "selection_policy": "capability_health_and_contract_quality_adaptive",
        "shared_health_state": dict(_SHARED_STATE_DIAGNOSTICS),
        "capability_policy_version": "1.6",
        "strict_schema_policy": "explicit_request_only_with_operation_contract_recovery",
        "operation_token_floors": dict(OPERATION_TOKEN_FLOORS),
        "model_limits": {provider + ":" + model: dict(limits) for (provider, model), limits in MODEL_LIMITS.items()},
        "operation_requirements": {
            operation: sorted(requirements)
            for operation, requirements in OPERATION_REQUIREMENTS.items()
        },
        "providers": sorted({x["provider"] for x in all_items}),
        "provider_health": {
            provider: aggregate_provider_health(states)
            for provider, states in provider_states.items()
        },
        "provider_quality": {
            key: {
                "operation": value.get("operation", ""),
                "provider": value.get("provider", ""),
                "model": value.get("model", ""),
                "failures": int(value.get("quality_failures", 0) or 0),
                "cooldown_until": float(value.get("quality_cooldown_until", 0) or 0),
                "last_error": str(value.get("quality_error", "") or ""),
            }
            for key, value in _STATE.setdefault("quality", {}).items()
        },
        "candidates": [
            {
                "provider": x["provider"],
                "model": x["model"],
                "blocked": _blocked(_state(x["provider"], x["model"])),
                "state": state_summary(_state(x["provider"], x["model"])),
                "quality": {
                    "by_operation": {
                        key: int(value.get("quality_failures", 0) or 0)
                        for key, value in _STATE["quality"].items()
                        if value.get("provider") == x["provider"] and value.get("model") == x["model"]
                    },
                },
                "capabilities": sorted(_capabilities(x["provider"], x["model"])),
            }
            for x in all_items
        ],
    }
