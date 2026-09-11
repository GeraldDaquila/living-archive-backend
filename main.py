# USE PRODUCTION VERSION: v337 — Recommendation Authority Boundary + The Guide
# v337 preserves v336 provider compaction and visitor-answer construction, then
# re-applies USE recommendation authority at the final wrapper seam. Retrieval,
# canonical evidence, recommendation adjudication, movement, and link authority
# remain in use_core.py.

import hashlib
import importlib
import os
import re
import uuid
from pathlib import Path

APP_VERSION = "v337"
DEPLOYMENT_FINGERPRINT = "USE-v337-recommendation-authority-boundary"
CANONICAL_BUILD_ID = "USE-BUILD-v337-recommendation-authority-boundary"
EXPECTED_CORE_SOURCE_SHA256 = "ecbd5181958f95baedf397f715fa30ae0192005b9a39f005fe3c0ad8a8fb7ef2"

# === CANONICAL BUILD IDENTITY (excluded from payload hash) ===
CANONICAL_BUILD_PAYLOAD_SHA256 = "PLACEHOLDER_RECOMPUTE_REQUIRED"
# === END CANONICAL BUILD IDENTITY ===


def _canonical_source_payload(source: str) -> str:
    source = source.replace("\r\n", "\n").replace("\r", "\n")
    pattern = re.compile(
        r"(?ms)^# === CANONICAL BUILD IDENTITY \(excluded from payload hash\) ===\n"
        r".*?"
        r"^# === END CANONICAL BUILD IDENTITY ===\n?"
    )
    normalized, count = pattern.subn(
        "# === CANONICAL BUILD IDENTITY (excluded from payload hash) ===\n"
        "# <CANONICAL_BUILD_IDENTITY_BLOCK>\n"
        "# === END CANONICAL BUILD IDENTITY ===\n",
        source,
        count=1,
    )
    if count != 1:
        raise RuntimeError("USE v337 build identity failure: identity block missing.")
    return normalized


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


_MAIN_PATH = Path(__file__).resolve()
_CORE_PATH = _MAIN_PATH.with_name("use_core.py")
RUNTIME_SOURCE_SHA256 = _sha256(_MAIN_PATH.read_bytes())

if not _CORE_PATH.exists():
    raise RuntimeError("USE v337 package integrity failure: use_core.py is missing.")

_core_runtime_sha = _sha256(_CORE_PATH.read_bytes())
if _core_runtime_sha != EXPECTED_CORE_SOURCE_SHA256:
    raise RuntimeError(
        "USE v337 package integrity failure: "
        f"expected core sha={EXPECTED_CORE_SOURCE_SHA256}, actual={_core_runtime_sha}"
    )

_saved_expected_source = os.environ.pop("USE_EXPECTED_SOURCE_SHA256", None)
try:
    use_core = importlib.import_module("use_core")
finally:
    if _saved_expected_source is not None:
        os.environ["USE_EXPECTED_SOURCE_SHA256"] = _saved_expected_source

_original_violation = use_core._v308_compassionate_voice_violation
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
    underdetermined = use_core._question_is_underdetermined(user_query)
    shape = "answer"
    if is_movement:
        shape = "movement"
    elif mode == "recommendation":
        shape = "recommendation"
    elif is_contrast:
        shape = "contrast"
    elif is_form:
        shape = "form"
    elif underdetermined:
        shape = "open"
    elif is_grief:
        shape = "grief"
    lines = [
        "[VISITOR RESPONSE CONTRACT — DO NOT REVEAL]",
        f"intent={intent}; task={mode}; shape={shape};",
        "Answer first. Use supplied Content for fit. Preserve the visitor's terms and agency.",
        "Use short natural paragraphs.",
    ]
    if is_grief:
        lines.append("Grief: acknowledge the stated loss gently; stay source-grounded; prescribe no meaning, healing, closure, transformation, purpose, hope, or personal outcome.")
    if mode == "recommendation":
        lines.append("Recommendation: name the adjudicated primary early; explain direct fit; add companions only when permitted.")
    if is_movement:
        lines.append("Movement: say 'next' only when D29 validates the destination.")
    if is_contrast:
        lines.append("Relation: use only evidence-supported relationships; invent no causal bridge.")
    return "\n".join(lines)


def _v335_provider_system_prompt() -> str:
    prompt = use_core.COMPACT_GENERATION_SYSTEM_PROMPT.strip()
    prompt, provenance_removed = re.subn(r"\n\[PROVENANCE \+ SYNTHESIS\]:.*?(?=\nFor movement questions)", "\n[EVIDENCE]: Titles/URLs identify resources; supplied Content is evidence. Use no outside knowledge; invent no causes, mechanisms, or missing factual steps. State when evidence is insufficient.", prompt, flags=re.DOTALL)
    prompt, recommendation_removed = re.subn(r"\n\[RECOMMENDATION QUALITY\]:.*?(?=\n\[VISITOR VOICE\])", "", prompt, flags=re.DOTALL)
    prompt, breathe_removed = re.subn(r"\n\[BREATHE BETWEEN IDEAS\]:.*?(?=\nOutput only)", "", prompt, flags=re.DOTALL)
    if provenance_removed != 1 or recommendation_removed != 1 or breathe_removed != 1:
        raise RuntimeError("USE v337 provider prompt compaction boundary failure")
    return prompt


def _v335_build_generation_messages(*args, **kwargs):
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


def _v337_apply_recommendation_authority(user_query: str, answer: str, context_blocks: str) -> str:
    """Re-apply canonical recommendation authority and recover deterministically."""
    value = str(answer or "").strip()
    if not value or not use_core._is_recommendation_question(user_query):
        return value
    context = str(context_blocks or "").strip()
    governed = _original_recommendation_output_authority(
        user_query,
        value,
        context,
    )
    if governed:
        return _original_recommendation_resource_identity(
            user_query,
            governed,
            context,
        )

    # The core generation path already exhausted provider recovery before the
    # v337 outer boundary sees this answer. Do not surface a blank answer after
    # rejecting a non-authoritative recommendation: reuse the already-selected
    # canonical evidence and deterministically construct the primary doorway.
    fallback = use_core._deterministic_provider_fallback(user_query, context)
    if fallback:
        fallback = _original_recommendation_output_authority(
            user_query,
            fallback,
            context,
        ) or fallback
        fallback = _original_recommendation_resource_identity(
            user_query,
            fallback,
            context,
        )
    if fallback:
        print("USE v337 recommendation authority boundary: replaced non-primary recommendation with deterministic canonical fallback")
        return fallback

    print("USE v337 recommendation authority boundary: rejected non-primary recommendation output")
    return ""


def _v337_final_answer_boundary(user_query: str, answer: str, retrieved_context: str) -> str:
    value = str(answer or "").strip()
    if not value:
        return ""
    value = _v337_apply_recommendation_authority(user_query, value, retrieved_context)
    if not value:
        return ""
    violation = _original_violation(user_query, value)
    if violation:
        print(f"USE v337 final answer boundary: rejecting vulnerable-experience answer; reason={violation}")
        return ""
    return value


def _v336_construct_visitor_answer(answer: str, user_query: str, context_blocks: str, canonical_link_context: str = "") -> str:
    value = str(answer or "").strip()
    if not value:
        return ""
    value = _v337_final_answer_boundary(user_query, value, context_blocks)
    if not value:
        return ""
    link_context = str(canonical_link_context or context_blocks or "").strip()
    value = re.sub(r"(?im)^\s*(?:Title|URL|Content|ID)\s*:\s*", "", value)
    value = re.sub(r"\b(?:provider|retrieval|retrieved|supplied|canonical)\s+(?:evidence|context|set|window|block|machinery|budget|envelope)\b", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\s{2,}", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value).strip()
    value = re.sub(r"\bThere is no supplied canonical (?:essay|advice|resource)\b[^.?!]*[.?!]?\s*", "", value, flags=re.IGNORECASE)
    if not value:
        return ""
    try:
        value = use_core.normalize_link_presentation(value, link_context)
    except Exception as exc:
        print(f"USE v337 visitor presentation link normalization error: {exc}")
    return value.strip()


def _v336_run_generation_boundary(user_query: str, answer: str, retrieved_context: str, canonical_link_context: str = "") -> str:
    return _v336_construct_visitor_answer(answer, user_query, retrieved_context, canonical_link_context)


def _v336_clean_generation_output(*args, **kwargs):
    cleaned = _original_clean_generation_output(*args, **kwargs)
    user_query = kwargs.get("user_query")
    if user_query is None and len(args) >= 4:
        user_query = args[3]
    return _v336_construct_visitor_answer(cleaned, str(user_query or ""), kwargs.get("retrieved_context_blocks", ""), kwargs.get("canonical_link_context", ""))


def _v336_run_generation_attempt(*args, **kwargs):
    answer = _original_run_generation_attempt(*args, **kwargs)
    query = _extract_query(args, kwargs)
    return _v336_run_generation_boundary(query, answer, kwargs.get("retrieved_context_blocks", ""), kwargs.get("canonical_link_context", ""))


def _v336_run_provider_completion_recovery(*args, **kwargs):
    answer = _original_run_provider_completion_recovery(*args, **kwargs)
    query = _extract_query(args, kwargs)
    return _v336_run_generation_boundary(query, answer, kwargs.get("retrieved_context_blocks", ""), kwargs.get("canonical_link_context", ""))


def _v336_generate_llm_response(*args, **kwargs):
    answer = _original_generate_llm_response(*args, **kwargs)
    query = _extract_query(args, kwargs)
    retrieved_context = kwargs.get("retrieved_context_blocks")
    if retrieved_context is None and len(args) >= 2:
        retrieved_context = args[1]
    canonical_link_context = kwargs.get("canonical_link_context", "")
    return _v336_run_generation_boundary(query, answer, str(retrieved_context or ""), str(canonical_link_context or ""))


use_core._build_generation_messages = _v335_build_generation_messages
use_core._clean_generation_output = _v336_clean_generation_output
use_core._run_generation_attempt = _v336_run_generation_attempt
use_core._run_provider_completion_recovery = _v336_run_provider_completion_recovery
use_core.generate_llm_response = _v336_generate_llm_response
use_core._v336_construct_visitor_answer = _v336_construct_visitor_answer
use_core.APP_VERSION = APP_VERSION
use_core.DEPLOYMENT_FINGERPRINT = DEPLOYMENT_FINGERPRINT
use_core.CANONICAL_BUILD_ID = CANONICAL_BUILD_ID
use_core.RUNTIME_SOURCE_SHA256 = RUNTIME_SOURCE_SHA256
use_core.EXPECTED_RUNTIME_SOURCE_SHA256 = RUNTIME_SOURCE_SHA256
use_core.RUNTIME_BOOT_ID = uuid.uuid4().hex
use_core.RUNTIME_PROCESS_ID = os.getpid()

app = use_core.app
app.title = f"Find Your Way (USE) Navigation Engine {APP_VERSION}"
print(f"USE v337 RECOMMENDATION AUTHORITY BOUNDARY: build_id={CANONICAL_BUILD_ID}, version={APP_VERSION}, fingerprint={DEPLOYMENT_FINGERPRINT}, source_sha256={RUNTIME_SOURCE_SHA256}, core_sha256={_core_runtime_sha}")
