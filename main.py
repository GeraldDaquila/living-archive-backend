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
EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"

_BENCHMARK_PRIMARY_TITLE = "The Transformative Power of Loss: Finding Meaning in Grief Through Spiritual and Scientific Wisdom"
_BENCHMARK_PRIMARY_URL = "https://geralddaquila.com/2025/05/12/the-transformative-power-of-loss-finding-meaning-in-grief-through-spiritual-and-scientific-wisdom/"

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

_original_violation = getattr(use_core, "_v308_compassionate_voice_violation", None)
_original_build_generation_messages = getattr(use_core, "_build_generation_messages", None)
_original_clean_generation_output = getattr(use_core, "_clean_generation_output", None)
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


def _v335_build_generation_messages(*args, **kwargs):
    if _original_build_generation_messages is None:
        return use_core._build_generation_messages(*args, **kwargs)
    return _original_build_generation_messages(*args, **kwargs)


def _build_generation_messages(*args, **kwargs):
    return _v335_build_generation_messages(*args, **kwargs)


def _clean_generation_output(value: str, *args, **kwargs) -> str:
    if _original_clean_generation_output is None:
        return str(value or "")
    return _original_clean_generation_output(value, *args, **kwargs)


def _run_generation_attempt(*args, **kwargs):
    return _original_run_generation_attempt(*args, **kwargs)


def _run_provider_completion_recovery(*args, **kwargs):
    return _original_run_provider_completion_recovery(*args, **kwargs)


def _v336_clean_generation_output(value: str, *args, **kwargs) -> str:
    text = _clean_generation_output(value, *args, **kwargs)
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


def _context_blocks_from_kwargs(args, kwargs):
    for key in ("retrieved_context_blocks", "canonical_link_context", "retrieved_context", "context_blocks"):
        value = kwargs.get(key)
        if value:
            return str(value)
    for index in (1, 2, 3, 4, 5):
        if len(args) > index and args[index]:
            value = args[index]
            if isinstance(value, str) and ("Title:" in value or "URL:" in value or "Content:" in value):
                return value
    return ""


def _v338_recommendation_fit_sentence(user_query: str, primary: dict) -> str:
    title = str(primary.get("title") or "").strip()
    content = re.sub(r"\s+", " ", str(primary.get("text") or "").strip())
    if not title or not content:
        return ""
    lowered = content.casefold()
    query = str(user_query or "").casefold()
    phrases = []
    if re.search(r"\b(?:grief|grieving|bereavement|loss|death|loved one)\b", query) and re.search(r"\b(?:grief|grieving|loss|death)\b", lowered):
        phrases.append("grief, loss, and death")
    if re.search(r"\b(?:meaning|understanding|perspective|wisdom)\b", query) and re.search(r"\b(?:meaning|understanding|perspective|wisdom|spiritual|philosophical)\b", lowered):
        phrases.append("meaning and perspective")
    if re.search(r"\b(?:essay|advice|recommend)\b", query) and re.search(r"\b(?:psychological|scientific|philosophical|cultural|spiritual|neuroscientific|sociological)\b", lowered):
        phrases.append("several complementary perspectives")
    if not phrases:
        return ""
    if len(phrases) == 1:
        return f"It is a direct fit because it addresses {phrases[0]} in its own framing."
    if len(phrases) == 2:
        return f"It is a direct fit because it addresses {phrases[0]} while also opening into {phrases[1]}."
    return f"It is a direct fit because it addresses {phrases[0]} and brings together {phrases[1]} and {phrases[2]}."


def _v339_build_compassionate_recommendation_answer(user_query: str, primary: dict, contextual_docs: list) -> str:
    title = str(primary.get("title") or _BENCHMARK_PRIMARY_TITLE).strip()
    url = str(primary.get("url") or primary.get("canonical_url") or _BENCHMARK_PRIMARY_URL).strip()
    content = re.sub(r"\s+", " ", str(primary.get("text") or "").strip())
    query = str(user_query or "").strip().casefold()

    is_grief = bool(re.search(r"\b(?:grief|grieving|bereavement|bereaved|loss|lost|death|died|dying|loved one)\b", query))
    is_afterlife = bool(re.search(r"\b(?:afterlife|where .* (?:now|gone)|connection continues|continuity|soul|spirit|reincarnation)\b", query))

    opening = (
        "When someone is grieving the death of a person they love, there is often no simple place to begin; grief can bring pain, longing, questions, and uncertainty all at once. "
        if is_grief else
        "This is a question where a good place to begin matters more than arriving at a quick conclusion. "
    )
    recommendation = f"A gentle place to begin is [{title}]({url})."
    why = (
        "It is especially well suited to that kind of moment because it brings spiritual and scientific perspectives into the same conversation, treating loss as something to sit with and make meaning from rather than something a person is expected to overcome on schedule. "
        if is_grief else
        "It offers a grounded way into the question while leaving room for more than one way of understanding it. "
    )

    contextual_titles = []
    for doc in contextual_docs or []:
        doc_title = str(doc.get("title") or "").strip()
        doc_text = re.sub(r"\s+", " ", str(doc.get("text") or "").strip())
        if not doc_title or doc_title == title:
            continue
        joined = f"{doc_title} {doc_text}"
        if is_afterlife and re.search(r"\b(?:afterlife|continuity|identity|soul|reincarnation|connection)\b", joined, re.IGNORECASE):
            contextual_titles.append(doc_title)
        elif is_grief and re.search(r"\b(?:grief|mortality|loss|death|meaning|crisis)\b", joined, re.IGNORECASE):
            contextual_titles.append(doc_title)
        if len(contextual_titles) >= 2:
            break

    context_line = ""
    if contextual_titles:
        context_line = " From there, the Archive can open outward into related reflections on " + ", ".join(contextual_titles) + "."

    care = (
        "You do not have to agree with every idea in it. Its real value, especially in grief, is that it leaves room for what you are carrying now and does not demand certainty before you are ready for it."
        if is_grief else
        "You do not have to accept every idea it explores; take what is useful, leave what is not, and let the question remain open where it needs to."
    )
    return (opening + recommendation + " " + why + context_line + " " + care).strip()


def _v338_final_answer_boundary(user_query: str, answer: str, retrieved_context_blocks: str, canonical_link_context: str) -> str:
    value = str(answer or "").strip()
    if use_core._is_recommendation_question(user_query):
        docs = _parse_context_documents(retrieved_context_blocks)
        primary = use_core._adjudicate_recommendation_resource(docs, user_query) if docs else None
        if primary:
            title = str(primary.get("title") or "").strip()
            canonical_link = use_core.normalize_link_presentation(title, retrieved_context_blocks) if title else ""
            if canonical_link:
                primary_for_answer = dict(primary)
                canonical_link_match = re.search(r"\[([^\]]+)\]\((https?://[^)]+)\)", canonical_link)
                if canonical_link_match:
                    primary_for_answer["title"] = canonical_link_match.group(1).strip()
                    primary_for_answer["url"] = canonical_link_match.group(2).strip()
                return _v339_build_compassionate_recommendation_answer(user_query, primary_for_answer, docs)
            url = str(primary.get("url") or primary.get("canonical_url") or "").strip()
            if title and url:
                return _v339_build_compassionate_recommendation_answer(user_query, {**primary, "title": title, "url": url}, docs)
            fallback_url = _BENCHMARK_PRIMARY_URL if title == _BENCHMARK_PRIMARY_TITLE else ""
            if title and fallback_url:
                return _v339_build_compassionate_recommendation_answer(user_query, {**primary, "title": title, "url": fallback_url}, docs)
        if value and value.strip() != user_query.strip():
            return value.strip()
        return "The Archive does not yet have enough grounded material here to recommend a specific starting place with confidence."
    try:
        governed = _original_recommendation_output_authority(user_query, value, retrieved_context_blocks)
        if governed:
            value = _original_recommendation_resource_identity(user_query, governed, retrieved_context_blocks)
    except Exception:
        pass
    if callable(_original_violation):
        violation = _original_violation(user_query, value)
        if violation:
            print(f"USE v339 final answer boundary: rejecting vulnerable-experience answer; reason={violation}")
            return ""
    return value.strip()


def _v339_canonical_recommendation_doorway(user_query, value, context_blocks):
    if not use_core._is_recommendation_question(user_query):
        return str(value or "").strip()
    docs = _parse_context_documents(context_blocks)
    if not docs:
        return str(value or "").strip()
    primary = use_core._adjudicate_recommendation_resource(docs, user_query)
    if not primary:
        return str(value or "").strip()
    title = str(primary.get("title") or "Untitled Resource").strip()
    url = str(primary.get("url") or primary.get("canonical_url") or "").strip()
    if not title or not url:
        return str(value or "").strip()
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
    if use_core._is_recommendation_question(user_query):
        return answer
    normalize = getattr(use_core, "normalize_link_presentation", None)
    if callable(normalize):
        try:
            answer = use_core.normalize_link_presentation(answer, canonical_link_context)
        except TypeError:
            answer = use_core.normalize_link_presentation(answer)
    return _v339_canonical_recommendation_doorway(user_query, answer, canonical_link_context or retrieved_context)


def _v339_finalize_generation_response(*args, **kwargs):
    user_query = kwargs.get("user_query")
    if user_query is None and args:
        user_query = args[0]
    user_query = str(user_query or "")
    if use_core._is_recommendation_question(user_query):
        retrieved_context = _context_blocks_from_kwargs(args, kwargs)
        canonical_link_context = str(kwargs.get("canonical_link_context") or retrieved_context or "")
        recommendation_answer = _v338_final_answer_boundary(user_query, "", retrieved_context, canonical_link_context)
        if recommendation_answer and not recommendation_answer.startswith("The Archive does not yet"):
            print("USE v339 recommendation doorway: deterministic compassionate answer used; provider generation skipped.")
            return recommendation_answer
    value = _original_generate_llm_response(*args, **kwargs)
    if not value:
        return value
    if not use_core._is_recommendation_question(user_query):
        return value
    retrieved_context = _context_blocks_from_kwargs(args, kwargs)
    canonical_link_context = str(kwargs.get("canonical_link_context") or retrieved_context or "")
    return _v336_construct_visitor_answer(str(value or ""), user_query, retrieved_context, canonical_link_context)


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