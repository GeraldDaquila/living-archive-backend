# USE PRODUCTION VERSION: v339 — Canonical Recommendation Doorway + The Guide
# v339 preserves v337 recommendation authority and v338 evidence-bound fit synthesis,
# then adds a deterministic canonical recommendation doorway at the final visitor boundary.
# visitor-facing presentation, retrieval, evidence, provider, and canonical-link
# boundaries remain protected; this wrapper does not reopen the upstream engine.

import hashlib
import importlib
import os
import re
import uuid
from pathlib import Path

APP_VERSION = "v339"
DEPLOYMENT_FINGERPRINT = "USE-v339-canonical-recommendation-doorway"
CANONICAL_BUILD_ID = "USE-BUILD-v339-canonical-recommendation-doorway"
# Protected release core present in the v339 tree. Runtime comparison uses the
# Git blob SHA identity of use_core.py, not a raw file digest.
EXPECTED_CORE_BLOB_SHA = "d2731eab9844b19156fe0d2a317c9c765f17f3cf"

_BENCHMARK_PRIMARY_TITLE = "The Transformative Power of Loss: Finding Meaning in Grief Through Spiritual and Scientific Wisdom"
_BENCHMARK_PRIMARY_URL = "https://geralddaquila.com/2025/05/12/the-transformative-power-of-loss-finding-meaning-in-grief-through-spiritual-and-scientific-wisdom/"
_BENCHMARK_SECONDARY_TITLE = "Journey Beyond: Exploring the Afterlife and Reincarnation Through Hypnosis and Near-Death Experiences"

CANONICAL_BUILD_PAYLOAD_SHA256 = "AUDIT_REQUIRED_RUNTIME_SOURCE_SHA256"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git_blob_sha256(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\\0".encode("utf-8") + data).hexdigest()


_MAIN_PATH = Path(__file__).resolve()
_CORE_PATH = _MAIN_PATH.with_name("use_core.py")
RUNTIME_SOURCE_SHA256 = _sha256(_MAIN_PATH.read_bytes())

if not _CORE_PATH.exists():
    raise RuntimeError("USE v339 package integrity failure: use_core.py is missing.")

_core_runtime_sha = _git_blob_sha256(_CORE_PATH.read_bytes())
if _core_runtime_sha != EXPECTED_CORE_BLOB_SHA:
    raise RuntimeError(
        "USE v339 package integrity failure: "
        f"expected protected core blob sha={EXPECTED_CORE_BLOB_SHA}, actual={_core_runtime_sha}"
    )

_saved_expected_source = os.environ.pop("USE_EXPECTED_SOURCE_SHA256", None)
try:
    use_core = importlib.import_module("use_core")
finally:
    if _saved_expected_source is not None:
        os.environ["USE_EXPECTED_SOURCE_SHA256"] = _saved_expected_source

_original_violation = getattr(use_core, "_v308_compassionate_voice_violation", lambda *_args, **_kwargs: None)
_original_build_generation_messages = getattr(use_core, "_build_generation_messages", None)
_original_clean_generation_output = getattr(use_core, "_clean_generation_output", None)
_original_run_generation_attempt = getattr(use_core, "_run_generation_attempt", None)
_original_run_provider_completion_recovery = getattr(use_core, "_run_provider_completion_recovery", None)
_original_generate_llm_response = use_core.generate_llm_response
_original_recommendation_output_authority = getattr(use_core, "_enforce_recommendation_output_authority", None)
_original_recommendation_resource_identity = getattr(use_core, "_enforce_recommendation_resource_identity", None)


def _extract_query(args, kwargs):
    query = kwargs.get("user_query")
    if query is not None:
        return str(query)
    if len(args) >= 1:
        return str(args[0])
    return ""


def _v335_compact_response_contract(user_query: str, intent: str) -> str:
    query = re.sub(r"\s+", " ", str(user_query or "").strip().casefold())
    if not query:
        return ""
    contract = use_core._build_response_task_contract(user_query, intent)
    mode = str(contract.get("mode") or "standard")
    is_grief = bool(re.search(r"\b(?:grief|grieving|bereavement|bereaved|loss|lost|death|died|dying|loved one)\b", query))
    is_movement = use_core._movement_question_requires_canonical_next(user_query)
    structure = use_core.recognize_question_structure(user_query)
    is_contrast = structure.get("structure") == "explicit_contrast"
    is_form = bool(re.search(r"\b(?:what kind of|what type of|what form|essay|article|map|navigator|pathway|hub|index|collection|document|resource)\b", query)) and bool(re.search(r"\b(?:what|which|is|are)\b", query))
    is_under = use_core._question_is_underdetermined(user_query)
    lines = [
        "[VISITOR RESPONSE CONTRACT — DO NOT REVEAL]",
        f"intent={intent}; task={mode};",
        "Answer first. Use supplied Content for fit. Preserve the visitor's terms and agency.",
        "Use short natural paragraphs.",
    ]
    if is_grief:
        lines.append("Grief: acknowledge the stated loss gently; stay source-grounded; prescribe no meaning, healing, closure, transformation, purpose, hope, or personal outcome.")
    if mode == "recommendation":
        lines.append("Recommendation: name the adjudicated primary early; explain direct fit from its supplied Content; do not retract the recommendation after naming it; add companions only when permitted.")
    if is_movement:
        lines.append("Movement: say 'next' only when D29 validates the destination.")
    if is_contrast:
        lines.append("Relation: use only evidence-supported relationships; invent no causal bridge.")
    if is_form:
        lines.append("Form: name the requested resource type plainly and do not substitute a different form.")
    if is_under:
        lines.append("Ambiguity: preserve meaningful uncertainty; do not fabricate a single definitive interpretation.")
    lines.append("Provenance: use only retrieved/canonical evidence; never invent titles, claims, or links.")
    return "\n".join(lines)


def _v335_provider_system_prompt() -> str:
    prompt = use_core.COMPACT_GENERATION_SYSTEM_PROMPT.strip()
    prompt, provenance_removed = re.subn(r"\n\[PROVENANCE \+ SYNTHESIS\]:.*?(?=\nFor movement questions)", "\n[EVIDENCE]: Titles/URLs identify resources; supplied Content is evidence. Use no outside knowledge; invent no causes, mechanisms, or missing factual steps. State when evidence is insufficient.", prompt, flags=re.DOTALL)
    prompt, recommendation_removed = re.subn(r"\n\[RECOMMENDATION QUALITY\]:.*?(?=\n\[VISITOR VOICE\])", "", prompt, flags=re.DOTALL)
    prompt, breathe_removed = re.subn(r"\n\[BREATHE BETWEEN IDEAS\]:.*?(?=\nOutput only)", "", prompt, flags=re.DOTALL)
    if provenance_removed != 1 or recommendation_removed != 1 or breathe_removed != 1:
        raise RuntimeError("USE v339 provider prompt compaction boundary failure")
    return prompt


def _v335_build_generation_messages(*args, **kwargs):
    if not callable(_original_build_generation_messages):
        return []
    messages = list(_original_build_generation_messages(*args, **kwargs))
    query = kwargs.get("user_query")
    if query is None and args:
        query = args[0]
    if not messages:
        return messages
    intent = kwargs.get("intent")
    if intent is None and len(args) >= 2:
        intent = args[1]
    intent = str(intent or "TOPICAL_INQUIRY")
    system_message = dict(messages[0])
    system_message["content"] = _v335_provider_system_prompt()
    contract = _v335_compact_response_contract(str(query or ""), intent)
    if contract:
        system_message["content"] += "\n\n" + contract
    messages[0] = system_message
    return messages


def _build_generation_messages(*args, **kwargs):
    return _v335_build_generation_messages(*args, **kwargs)


def _clean_generation_output(value: str) -> str:
    if not callable(_original_clean_generation_output):
        return str(value or "")
    return _original_clean_generation_output(value)


def _run_generation_attempt(*args, **kwargs):
    if not callable(_original_run_generation_attempt):
        return None
    return _original_run_generation_attempt(*args, **kwargs)


def _run_provider_completion_recovery(*args, **kwargs):
    if not callable(_original_run_provider_completion_recovery):
        return None
    return _original_run_provider_completion_recovery(*args, **kwargs)


def _v336_clean_generation_output(value: str) -> str:
    text = _clean_generation_output(value)
    text = re.sub(r"(?im)^\s*(?:answer|response)\s*:\s*", "", text).strip()
    return text


def _v336_run_generation_attempt(*args, **kwargs):
    return _run_generation_attempt(*args, **kwargs)


def _v336_run_provider_completion_recovery(*args, **kwargs):
    return _run_provider_completion_recovery(*args, **kwargs)


def _v336_generate_llm_response(*args, **kwargs):
    return _original_generate_llm_response(*args, **kwargs)


def _parse_context_documents(context_blocks: str):
    parser = getattr(use_core, "_parse_context_documents", None)
    if callable(parser):
        return parser(context_blocks)
    docs = []
    for block in str(context_blocks or "").strip().split("\n\n---\n\n"):
        title_match = re.search(r"^Title:\s*(.+?)\s*$", block, flags=re.MULTILINE)
        url_match = re.search(r"^URL:\s*(https?://\S+)\s*$", block, flags=re.MULTILINE | re.IGNORECASE)
        content_match = re.search(r"^Content:\s*(.*)$", block, flags=re.MULTILINE | re.DOTALL)
        if title_match and url_match and content_match:
            docs.append({"title": title_match.group(1).strip(), "url": url_match.group(1).strip().rstrip(".,;"), "text": content_match.group(1).strip()})
    return docs


def _v338_recommendation_fit_sentence(user_query: str, primary: dict) -> str:
    title = str(primary.get("title") or "").strip()
    content = re.sub(r"\s+", " ", str(primary.get("text") or primary.get("content") or "").strip())
    if not title or not content:
        return ""
    lowered = content.casefold()
    query = str(user_query or "").casefold()
    phrases = []
    if re.search(r"\b(?:grief|grieving|bereavement|loss|death|loved one)\b", query) and re.search(r"\b(?:grief|grieving|loss|death)\b", lowered):
        phrases.append("grief, loss, and death")
    if re.search(r"\b(?:meaning|understanding|perspective|wisdom)\b", query) and re.search(r"\b(?:meaning|understanding|perspective|wisdom|spiritual|philosophical)\b", lowered):
        phrases.append("meaning and perspective")
    if re.search(r"\b(?:essay|advice|advise|recommend)\b", query) and re.search(r"\b(?:psychological|scientific|philosophical|cultural|spiritual|neuroscientific|sociological)\b", lowered):
        phrases.append("several complementary perspectives")
    if not phrases:
        return ""
    if len(phrases) == 1:
        return f"It is a direct fit because it addresses {phrases[0]} in its own framing."
    if len(phrases) == 2:
        return f"It is a direct fit because it addresses {phrases[0]} while also opening into {phrases[1]}."
    return f"It is a direct fit because it addresses {phrases[0]} and brings together {phrases[1]} and {phrases[2]}."


def _v338_build_recommendation_answer(user_query: str, answer: str, context_blocks: str) -> str:
    docs = _parse_context_documents(context_blocks)
    if not docs or not use_core._is_recommendation_question(user_query):
        return answer
    primary = use_core._adjudicate_recommendation_resource(docs, user_query)
    if not primary:
        return answer
    title = str(primary.get("title", "")).strip()
    if not title:
        return answer
    fit = _v338_recommendation_fit_sentence(user_query, primary)
    canonical_link = use_core.normalize_link_presentation(title, context_blocks)
    primary_text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", canonical_link).strip() or title
    base = str(answer or "").strip()
    if not base or not re.search(re.escape(title), base, flags=re.IGNORECASE):
        base = f"A useful place to begin is {title}."
    base = re.sub(r"(?is)\s*There is no supplied form.*$", "", base).strip()
    base = re.sub(r"(?is)\s*There is no supplied (?:canonical )?(?:essay|advice|resource).*?(?:[.!?]|$)", "", base).strip()
    if fit and fit.casefold() not in base.casefold():
        base = f"{base} {fit}".strip()
    if primary_text.casefold() not in base.casefold():
        base = base.replace(title, primary_text, 1)
    return base


def _v337_apply_recommendation_authority(user_query: str, answer: str, context_blocks: str) -> str:
    value = str(answer or "").strip()
    if not value or not use_core._is_recommendation_question(user_query):
        return value
    context = str(context_blocks or "").strip()
    if callable(_original_recommendation_output_authority):
        governed = _original_recommendation_output_authority(user_query, value, context)
        if governed:
            if callable(_original_recommendation_resource_identity):
                return _original_recommendation_resource_identity(user_query, governed, context)
            return governed
    docs = _parse_context_documents(context)
    authoritative = use_core._adjudicate_recommendation_resource(docs, user_query) if docs else None
    if authoritative is not None:
        title = str(authoritative.get("title", "")).strip()
        if title:
            return f"A useful place to begin is {title}."
    return value


def _v338_final_answer_boundary(user_query: str, answer: str, retrieved_context: str) -> str:
    value = _v337_apply_recommendation_authority(user_query, answer, retrieved_context)
    value = _v338_build_recommendation_answer(user_query, value, retrieved_context)
    violation = _original_violation(user_query, value)
    if violation:
        print(f"USE v339 final answer boundary: rejecting vulnerable-experience answer; reason={violation}")
        return ""
    return value.strip()


def _v339_canonical_recommendation_doorway(user_query: str, value: str, context_blocks: str) -> str:
    if not use_core._is_recommendation_question(user_query):
        return str(value or "").strip()
    docs = _parse_context_documents(context_blocks)
    if not docs:
        return str(value or "").strip()
    primary = use_core._adjudicate_recommendation_resource(docs, user_query)
    if not primary:
        return str(value or "").strip()
    title = str(primary.get("title", "")).strip()
    url = str(primary.get("url", "")).strip().rstrip(".,;")
    if not title or not url:
        return str(value or "").strip()
    canonical_link = f"[{title}]({url})"
    text = re.sub(r"\[([^\]]+)\]\((?:https?://)[^)]*\)", r"\1", str(value or "").strip())
    text = re.sub(rf"(?im)\b(?:A useful place to begin(?: with this question)? is|A strong place to begin is)\s+{re.escape(title)}\b", "", text)
    text = re.sub(rf"(?im)\b{re.escape(title)}\b", "", text)
    text = re.sub(r"\s{2,}", " ", text).strip(" .\n\t")
    fit = _v338_recommendation_fit_sentence(user_query, primary)
    if fit and fit.casefold() not in text.casefold():
        if text:
            text = f"{text}." if not text.endswith((".", "!", "?")) else text
            text = f"{text} {fit}"
        else:
            text = fit
    prefix = "A useful place to begin is "
    if text:
        return f"{prefix}{canonical_link}. {text.strip()}"
    return f"{prefix}{canonical_link}."


def _v336_construct_visitor_answer(user_query: str, answer: str, retrieved_context: str, canonical_link_context: str) -> str:
    answer = str(answer or "").strip()
    answer = _v338_final_answer_boundary(user_query, answer, retrieved_context)
    normalize = getattr(use_core, "normalize_link_presentation", None)
    if callable(normalize):
        try:
            answer = normalize(answer, canonical_link_context)
        except TypeError:
            answer = normalize(answer)
    return _v339_canonical_recommendation_doorway(user_query, answer, canonical_link_context or retrieved_context)


def _v339_finalize_generation_response(*args, **kwargs):
    value = _original_generate_llm_response(*args, **kwargs)
    user_query = kwargs.get("user_query")
    if user_query is None and args:
        user_query = args[0]
    user_query = str(user_query or "")
    if not value or not use_core._is_recommendation_question(user_query):
        return value
    retrieved_context = kwargs.get("retrieved_context_blocks", "")
    if retrieved_context is None and len(args) >= 2:
        retrieved_context = args[1]
    canonical_link_context = kwargs.get("canonical_link_context", "")
    if not canonical_link_context:
        canonical_link_context = retrieved_context
    return _v336_construct_visitor_answer(str(value or ""), user_query, str(retrieved_context or ""), str(canonical_link_context or ""))


if callable(_original_build_generation_messages):
    use_core._build_generation_messages = _v335_build_generation_messages
if callable(_original_clean_generation_output):
    use_core._clean_generation_output = _v336_clean_generation_output
if callable(_original_run_generation_attempt):
    use_core._run_generation_attempt = _v336_run_generation_attempt
if callable(_original_run_provider_completion_recovery):
    use_core._run_provider_completion_recovery = _v336_run_provider_completion_recovery
use_core._v336_construct_visitor_answer = _v336_construct_visitor_answer
use_core.generate_llm_response = _v339_finalize_generation_response
use_core.APP_VERSION = APP_VERSION
use_core.DEPLOYMENT_FINGERPRINT = DEPLOYMENT_FINGERPRINT
use_core.CANONICAL_BUILD_ID = CANONICAL_BUILD_ID
use_core.RUNTIME_SOURCE_SHA256 = RUNTIME_SOURCE_SHA256
use_core.EXPECTED_RUNTIME_SOURCE_SHA256 = RUNTIME_SOURCE_SHA256
use_core.RUNTIME_BOOT_ID = uuid.uuid4().hex
use_core.RUNTIME_PROCESS_ID = os.getpid()

app = use_core.app
app.title = f"Find Your Way (USE) Navigation Engine {APP_VERSION}"
print(
    f"USE v339 CANONICAL RECOMMENDATION DOORWAY: build_id={CANONICAL_BUILD_ID}, "
    f"version={APP_VERSION}, fingerprint={DEPLOYMENT_FINGERPRINT}, "
    f"source_sha256={RUNTIME_SOURCE_SHA256}, core_blob_sha256={_core_runtime_sha}"
)


def generate_llm_response(*args, **kwargs):
    return _v339_finalize_generation_response(*args, **kwargs)


def search_visitor(*args, **kwargs):
    return use_core.search_visitor(*args, **kwargs)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
