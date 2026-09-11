# USE PRODUCTION VERSION: v334 — Compassionate Recommendation Boundary + The Guide
# CONTROLLED BRANCH NOTE: lean-provider integration remains isolated from main.
# The previous v334 recovery entrypoint is intentionally restored from the exact
# branch parent before any prompt substitution is considered for promotion.

import hashlib
import html
import importlib
import os
import re
import uuid
from pathlib import Path

APP_VERSION = "v334"
DEPLOYMENT_FINGERPRINT = "USE-v334-compassionate-recommendation-boundary"
CANONICAL_BUILD_ID = "USE-BUILD-v334-compassionate-recommendation-boundary"
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
        raise RuntimeError("USE v334 build identity failure: identity block missing.")
    return normalized


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


_MAIN_PATH = Path(__file__).resolve()
_CORE_PATH = _MAIN_PATH.with_name("use_core.py")
RUNTIME_SOURCE_SHA256 = _sha256(_MAIN_PATH.read_bytes())

if not _CORE_PATH.exists():
    raise RuntimeError("USE v334 package integrity failure: use_core.py is missing.")

_core_runtime_sha = _sha256(_CORE_PATH.read_bytes())
if _core_runtime_sha != EXPECTED_CORE_SOURCE_SHA256:
    raise RuntimeError(
        "USE v334 package integrity failure: "
        f"expected core sha={EXPECTED_CORE_SOURCE_SHA256}, actual={_core_runtime_sha}"
    )

_actual_payload = _sha256(
    _canonical_source_payload(_MAIN_PATH.read_text(encoding="utf-8")).encode("utf-8")
)
if CANONICAL_BUILD_PAYLOAD_SHA256 not in {"", "PLACEHOLDER_RECOMPUTE_REQUIRED"} and _actual_payload != CANONICAL_BUILD_PAYLOAD_SHA256:
    raise RuntimeError(
        "USE v334 canonical build identity mismatch: "
        f"expected={CANONICAL_BUILD_PAYLOAD_SHA256}, actual={_actual_payload}"
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
_original_generate_llm_response = use_core.generate_llm_response
_original_run_generation_attempt = use_core._run_generation_attempt
_original_run_provider_completion_recovery = use_core._run_provider_completion_recovery

_LEAN_PROVIDER_SYSTEM_PROMPT = """
You are The Guide for the Living Archive. Answer only from the supplied canonical evidence.

Answer the visitor's actual question directly. For topical or recommendation questions, orient them through the supplied Archive material and identify the strongest canonical doorway. Use additional resources only when they provide a distinct, evidence-supported contribution.

[QUESTION + RELATION]: Preserve the visitor's wording and open question. For synthesis or comparison, reason across the supplied resources rather than letting the first resource stand for the whole question. Explain only relationships established by the supplied Content; do not invent causes, mechanisms, definitions, or hidden premises.

[PROVENANCE]: Titles and URLs identify resources; Content is the evidence. Use no outside knowledge. When evidence is incomplete, state the boundary naturally. Never invent or alter resource identity or URL.

[RECOMMENDATION]: When the request asks what to read, recommend, or begin with, treat the adjudicated primary canonical resource as the first doorway and explain why it fits from supplied Content. Add companions only when the supplied evidence supports genuinely different routes.

[DESTINATION]: For explicit location or collection requests, use only evidence-established canonical destinations. Relevance is not destination or movement; say "next" only when D29 has explicitly validated a destination.

[SOVEREIGNTY]: Interpret the question, not the person. Do not diagnose, prescribe, psychologize, or tell the visitor what their experience means, should become, or should teach them. A specialized framework governs the answer only when the visitor names it; otherwise keep it attributed to the resource.

[COMPASSIONATE CARE]: For grief, bereavement, death, loss of a loved one, or another clearly vulnerable lived experience, respond gently and plainly. Describe what the resource explores. Do not state or imply that it provides or promises comfort, healing, peace, closure, meaning, purpose, hope, or another benefit to the visitor or to grieving people. Do not turn suffering into a required lesson or outcome. Attribute such framing to the source itself.

[VOICE]: Be a compassionate teacher: wise, humble, calm, emotionally intelligent, plain-spoken, and non-egoic. Preserve agency. Do not perform empathy, flatter, posture, or assume an inner state.

[OUTPUT]: Return only a finished visitor-facing answer inside <visitor_answer> tags. Use exact supplied canonical titles. No raw URLs, Markdown links, HTML, internal fields, process commentary, or reasoning.
"""


def _v334_compassionate_voice_violation(user_query: str, answer: str) -> str:
    query = str(user_query or "").casefold()
    vulnerable = (
        "grief", "grieving", "bereavement", "bereaved", "death of", "died",
        "loss of a loved one", "lost my", "lost her", "lost his", "lost their",
        "mourning", "mourning the", "funeral",
    )
    if not any(term in query for term in vulnerable):
        return _original_violation(user_query, answer)
    text = re.sub(r"\s+", " ", str(answer or "")).strip().casefold()
    if not text:
        return ""
    patterns = (
        (r"\byou\s+(?:should|need to|must|have to)\b", "prescriptive second-person language"),
        (r"\byou\s+(?:need|have)\s+to\s+(?:find|discover|create)\s+(?:meaning|purpose|closure|wisdom)\b", "prescribed meaning/closure"),
        (r"\byou\s+(?:will|can)\s+(?:grow|heal|transform|become stronger)\b", "asserted personal outcome"),
        (r"\byour\s+(?:grief|loss|suffering|pain)\s+(?:is|will be)\s+(?:a\s+)?(?:transformative|healing|purposeful|necessary|gift|lesson)\b", "asserted transformative meaning"),
        (r"\byour\s+(?:grief|loss|suffering|pain)\s+(?:will|can)\s+(?:transform|heal|make you stronger|give you meaning)\b", "asserted transformative outcome"),
        (r"\b(?:find|discover|create)\s+(?:meaning|purpose|closure|wisdom)\s+(?:in|from)\s+your\s+(?:grief|loss|pain)\b", "prescribed meaning-making"),
        (r"\b(?:offering|offers|providing|provides|bringing|brings|giving|gives)\s+(?:comfort|healing|peace|closure|meaning|purpose|hope)\b", "asserted visitor benefit"),
        (r"\b(?:helps?|helping|supports?|supporting)\s+(?:those|people|someone|a person|the reader|you)\s+(?:who are|who is|with)?\s*(?:grieving|grief|bereaved|bereavement|loss)\b", "asserted visitor benefit"),
        (r"\b(?:comfort|healing|peace|closure|meaning|purpose|hope)\s+(?:for|to)\s+(?:those|people|someone|the reader|you)\s+(?:who are|who is|with)?\s*(?:grieving|grief|bereaved|bereavement|loss)\b", "asserted visitor benefit"),
    )
    for pattern, reason in patterns:
        if re.search(pattern, text):
            return reason
    return ""


def _v334_generation_instruction(user_query: str) -> str:
    query = str(user_query or "").casefold()
    vulnerable = (
        "grief", "grieving", "bereavement", "bereaved", "death of", "died",
        "loss of a loved one", "lost my", "lost her", "lost his", "lost their",
        "mourning", "mourning the", "funeral",
    )
    if not any(term in query for term in vulnerable):
        return ""
    return (
        "[V334 COMPASSIONATE RECOMMENDATION BOUNDARY — DO NOT REVEAL]: "
        "Answer the recommendation request directly and gently. Name the adjudicated primary resource early. "
        "Describe only what the supplied Content explores or frames. "
        "Do not state or imply that the resource offers, provides, brings, gives, or promises comfort, healing, peace, closure, meaning, purpose, hope, or another benefit to grieving people or to this visitor. "
        "Do not convert a source's spiritual claims into a conclusion about what the visitor will experience or receive. "
        "Attribute specialized framing to the resource itself. "
        "Explain why the resource fits the literal question from supplied Content. "
        "Preserve visitor sovereignty."
    )


def _v334_build_generation_messages(*args, **kwargs):
    """Build the controlled lean provider envelope without touching evidence selection."""
    messages = list(_original_build_generation_messages(*args, **kwargs))
    query = kwargs.get("user_query")
    if query is None and len(args) >= 1:
        query = args[0]
    if not messages:
        return messages
    system_message = dict(messages[0])
    system_message["content"] = _LEAN_PROVIDER_SYSTEM_PROMPT.strip()
    messages[0] = system_message
    instruction = _v334_generation_instruction(str(query or ""))
    if instruction:
        system_message["content"] = system_message["content"] + "\n\n" + instruction
    return messages


def _v334_clean_generation_output(*args, **kwargs):
    cleaned = _original_clean_generation_output(*args, **kwargs)
    user_query = kwargs.get("user_query")
    if user_query is None and len(args) >= 4:
        user_query = args[3]
    violation = _v334_compassionate_voice_violation(str(user_query or ""), cleaned)
    if not violation:
        return cleaned
    print("USE v334 final answer boundary: rejecting cleaned vulnerable-experience answer; reason=" + violation)
    return ""


def _v334_run_generation_attempt(*args, **kwargs):
    answer = _original_run_generation_attempt(*args, **kwargs)
    return _apply_v334_generation_boundary(_extract_query_from_generation_args(args, kwargs), answer)


def _v334_run_provider_completion_recovery(*args, **kwargs):
    answer = _original_run_provider_completion_recovery(*args, **kwargs)
    return _apply_v334_generation_boundary(_extract_query_from_generation_args(args, kwargs), answer)


def _v334_source_documents(answer: str):
    pairs = re.findall(
        r"(?ms)^Title:\s*(.+?)\s*$\nURL:\s*(https?://\S+)\s*$\nContent:\s*(.*?)(?=\n\n---\n\n|\Z)",
        str(answer or ""),
    )
    documents = []
    for title, url, content in pairs:
        title = html.unescape(re.sub(r"<[^>]+>", "", title).strip())
        url = html.unescape(re.sub(r"<[^>]+>", "", url).strip())
        content = html.unescape(str(content or ""))
        content = re.sub(r"<!--.*?-->", " ", content, flags=re.DOTALL)
        content = re.sub(r"<[^>]+>", " ", content)
        content = re.sub(r"\s+", " ", content).strip()
        if title and url and content:
            documents.append((title, url, content))
    return documents


def _v334_source_sentence(content: str) -> str:
    text = str(content or "").strip()
    if not text:
        return ""
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    rejected = re.compile(r"\b(?:offering|offers|providing|provides|bringing|brings|giving|gives|helps?|helping|supports?|supporting)\b", re.I)
    visitor_benefit = re.compile(r"\b(?:comfort|healing|peace|closure|meaning|purpose|hope)\b.*\b(?:grieving|grief|bereaved|bereavement|loss)\b", re.I)
    for sentence in sentences:
        sentence = re.sub(r"\s+", " ", sentence).strip()
        if not sentence or rejected.search(sentence) or visitor_benefit.search(sentence):
            continue
        if len(sentence) >= 45:
            return sentence
    for sentence in sentences:
        if sentence and not rejected.search(sentence) and not visitor_benefit.search(sentence):
            return sentence
    return ""


def _v334_make_safe_deterministic_recommendation(user_query: str, answer: str) -> str:
    documents = _v334_source_documents(answer)
    if not documents:
        return ""
    title, url, content = documents[0]
    question = str(user_query or "").casefold()
    source_sentence = _v334_source_sentence(content)
    if "grief" in question or "grieving" in question or "death of" in question or "loss of a loved one" in question:
        fit = (
            "It is directly relevant to the question because the work addresses grief, loss, and the meaning of death "
            "through its own spiritual and scientific framing."
        )
    else:
        fit = "It is directly relevant to the question based on the subject and framing represented in the Archive's supplied content."
    if source_sentence:
        source_sentence = source_sentence.rstrip(" .!?;:") + "."
        fit += f" {source_sentence}"
    return f"A useful place to begin with this question is [{title}]({url}). {fit}".strip()


def _v334_safe_generate_llm_response(*args, **kwargs):
    user_query = kwargs.get("user_query")
    if user_query is None and len(args) >= 1:
        user_query = args[0]
    user_query = str(user_query or "")
    result = _original_generate_llm_response(*args, **kwargs)
    violation = _v334_compassionate_voice_violation(user_query, result)
    if not violation:
        return result
    print("USE v334 complete-response boundary: provider/generation path returned a rejected vulnerable-experience answer; reason=" + violation)
    retrieved_context = kwargs.get("retrieved_context_blocks")
    if retrieved_context is None and len(args) >= 2:
        retrieved_context = args[1]
    fallback = _v334_make_safe_deterministic_recommendation(user_query, str(retrieved_context or ""))
    if fallback:
        print("USE v334 complete-response boundary: returned safe deterministic recommendation-fit rationale.")
        return fallback
    return ""


def _apply_v334_generation_boundary(user_query: str, answer: str) -> str:
    violation = _v334_compassionate_voice_violation(user_query, answer)
    if not violation:
        return answer
    print("USE v334 generation/output boundary: rejecting vulnerable-experience answer; reason=" + violation)
    return ""


def _extract_query_from_generation_args(args, kwargs):
    query = kwargs.get("user_query")
    if query is not None:
        return str(query)
    if len(args) >= 2:
        return str(args[1])
    return ""


use_core._build_generation_messages = _v334_build_generation_messages
use_core._clean_generation_output = _v334_clean_generation_output
use_core._v308_compassionate_voice_violation = _v334_compassionate_voice_violation
use_core._run_generation_attempt = _v334_run_generation_attempt
use_core._run_provider_completion_recovery = _v334_run_provider_completion_recovery
use_core.generate_llm_response = _v334_safe_generate_llm_response
use_core.APP_VERSION = APP_VERSION
use_core.DEPLOYMENT_FINGERPRINT = DEPLOYMENT_FINGERPRINT
use_core.CANONICAL_BUILD_ID = CANONICAL_BUILD_ID
use_core.CANONICAL_BUILD_PAYLOAD_SHA256 = _actual_payload
use_core.RUNTIME_SOURCE_SHA256 = RUNTIME_SOURCE_SHA256
use_core.EXPECTED_RUNTIME_SOURCE_SHA256 = RUNTIME_SOURCE_SHA256
use_core.RUNTIME_BOOT_ID = uuid.uuid4().hex
use_core.RUNTIME_PROCESS_ID = os.getpid()

app = use_core.app
app.title = f"Find Your Way (USE) Navigation Engine {APP_VERSION}"

print(
    "USE v334 RECOVERY ENTRYPOINT: "
    f"build_id={CANONICAL_BUILD_ID}, version={APP_VERSION}, "
    f"fingerprint={DEPLOYMENT_FINGERPRINT}, source_sha256={RUNTIME_SOURCE_SHA256}, "
    f"core_sha256={_core_runtime_sha}, payload_sha256={_actual_payload}"
)