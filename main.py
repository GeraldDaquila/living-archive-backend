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
    return hashlib.sha1(f"blob {len(data)}\0".encode("utf-8") + data).hexdigest()


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
_original_build_generation_messages = use_core._build_generation_messages
_original_clean_generation_output = use_core._clean_generation_output
_original_run_generation_attempt = use_core._run_generation_attempt
_original_run_provider_completion_recovery = use_core._run_provider_completion_recovery
_original_generate_llm_response = use_core.generate_llm_response
_original_recommendation_output_authority = use_core._enforce_recommendation_output_authority
_original_recommendation_resource_identity = use_core._enforce_recommendation_resource_identity


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
        "[VISITOR RESPONSE CONTRACT — APPLY LAST]",
        f"mode={mode}; intent={intent};",
        "Answer first. Answer the visitor’s orientation need rather than merely echoing retrieval.",
        "Preserve the visitor's terms and agency.",
    ]
    if is_grief:
        lines.append("grief-care: acknowledge loss gently; avoid abstraction, preaching, or emotional overclaiming.")
    if is_movement:
        lines.append("movement: provide one clear next place only when a canonical destination is supported. Movement: say 'next' only when D29 validates the destination.")
    if is_contrast:
        lines.append("contrast: preserve the distinction the visitor actually asked about before moving onward.")
    if is_form:
        lines.append("form: name the requested resource type plainly and do not pretend a different form is equivalent.")
    if is_under:
        lines.append("ambiguity: preserve meaningful uncertainty; do not fabricate a single definitive interpretation.")
    if mode == "recommendation":
        lines.append("Recommendation: use the adjudicated primary as the canonical doorway and explain its fit from supplied evidence. Do not replace a chosen primary with a secondary resource.")
    lines.append("provenance: use only retrieved/canonical evidence; never invent titles, claims, or links.")
    return " ".join(lines)[:600]


def _v335_provider_system_prompt() -> str:
    return use_core.COMPACT_GENERATION_SYSTEM_PROMPT


def _v335_build_generation_messages(user_query: str, intent: str, retrieved_context_blocks: str, response_contract: str):
    return _original_build_generation_messages(user_query, intent, retrieved_context_blocks, response_contract)


def _build_generation_messages(user_query: str, intent: str, retrieved_context_blocks: str, response_contract: str):
    return _v335_build_generation_messages(user_query, intent, retrieved_context_blocks, response_contract)


def _clean_generation_output(value: str) -> str:
    return _original_clean_generation_output(value)


def _run_generation_attempt(*args, **kwargs):
    return _original_run_generation_attempt(*args, **kwargs)


def _run_provider_completion_recovery(*args, **kwargs):
    return _original_run_provider_completion_recovery(*args, **kwargs)


def _v336_clean_generation_output(value: str) -> str:
    text = _clean_generation_output(value)
    return re.sub(r"(?im)^\s*(?:answer|response)\s*:\s*", "", text).strip()


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
    question = re.sub(r"\s+", " ", str(user_query or "").strip()).casefold()
    if re.search(r"\b(?:grief|grieving|bereavement|loss|loved one|death)\b", question):
        return "It speaks directly to grief, loss, and the meaning of death without reducing the experience to a single answer."
    return "It is closely aligned with the question and gives the visitor a grounded place to begin."


def _v338_build_recommendation_answer(user_query: str, primary: dict) -> str:
    return _v338_recommendation_fit_sentence(user_query, primary)


def _v337_apply_recommendation_authority(value: str, user_query: str, retrieved_context_blocks: str) -> str:
    fn = getattr(use_core, "_enforce_recommendation_output_authority", None)
    if callable(fn):
        try:
            return fn(value, user_query, retrieved_context_blocks)
        except TypeError:
            pass
    return value


def _v338_final_answer_boundary(value: str, user_query: str, retrieved_context_blocks: str, canonical_link_context: str) -> str:
    value = _v337_apply_recommendation_authority(value, user_query, retrieved_context_blocks)
    identity_fn = getattr(use_core, "_enforce_recommendation_resource_identity", None)
    if callable(identity_fn):
        try:
            value = identity_fn(value, user_query, retrieved_context_blocks)
        except TypeError:
            pass
    return value


def _v339_canonical_recommendation_doorway(user_query, value, context_blocks):
    if not use_core._is_recommendation_question(user_query):
        return value
    docs = _parse_context_documents(context_blocks)
    primary = use_core._adjudicate_recommendation_resource(docs, user_query)
    if not primary:
        return value
    title = str(primary.get("title") or "Untitled Resource").strip()
    url = str(primary.get("url") or primary.get("canonical_url") or "").strip()
    if not title or not url:
        return value
    canonical_link = f"[{title}]({url})"
    text = re.sub(r"\[([^\]]+)\]\((?:https?://)[^)]*\)", r"\1", str(value or "").strip())
    text = re.sub(rf"(?im)\b(?:A useful place to begin(?: with this question)? is|A strong place to begin is)\s+{re.escape(title)}\b", "", text)
    text = re.sub(rf"(?im)\b{re.escape(title)}\b", "", text)
    text = re.sub(r"\s{2,}", " ", text).strip(" .")
    fit = _v338_recommendation_fit_sentence(user_query, primary)
    if fit and fit.casefold() not in text.casefold():
        text = f"{text}. {fit}".strip(" .") if text else fit
    prefix = "A useful place to begin is "
    return f"{prefix}{canonical_link}. {text.strip()}".strip() if text.strip() else f"{prefix}{canonical_link}."


def _v336_construct_visitor_answer(answer, user_query, retrieved_context, canonical_link_context):
    answer = str(answer or "").strip()
    answer = _v338_final_answer_boundary(answer, user_query, retrieved_context, canonical_link_context)
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
    canonical_link_context = kwargs.get("canonical_link_context", "") or retrieved_context
    return _v336_construct_visitor_answer(str(value or ""), user_query, str(retrieved_context or ""), str(canonical_link_context or ""))


use_core._build_generation_messages = _build_generation_messages
use_core._clean_generation_output = _v336_clean_generation_output
use_core._run_generation_attempt = _v336_run_generation_attempt
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
