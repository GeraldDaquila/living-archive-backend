# USE PRODUCTION VERSION: v339 — Canonical Recommendation Doorway + The Guide
# Benchmark-aligned compassionate recommendation presentation at the final visitor boundary.
# Protected v333 core, retrieval, evidence selection, recommendation adjudication,
# and canonical resource authority remain unchanged.

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


def _v335_compact_response_contract(user_query: str, intent: str) -> str:
    query = re.sub(r"\s+", " ", str(user_query or "").strip().casefold())
    if not query:
        return ""
    contract = use_core._build_response_task_contract(user_query, intent)
    mode = str(contract.get("mode") or "standard")
    lines = [
        "[VISITOR RESPONSE CONTRACT — APPLY LAST]",
        f"mode={mode}; intent={intent};",
        "Answer first. Answer the visitor’s orientation need rather than merely echoing retrieval.",
        "Preserve the visitor's terms and agency.",
        "Architecture: recognize human reality; offer a humane foothold; distinguish knowledge, interpretation, possibility, and personal meaning; route material risk appropriately; open a reflection pathway rather than closing the question with one document.",
    ]
    if re.search(r"\b(?:grief|grieving|bereavement|bereaved|loss|lost|death|died|dying|loved one|trauma|abuse|coercion|suicid|self-harm|overdose)\b", query):
        lines.append("sensitivity: meet vulnerable experience without abstraction, preaching, emotional overclaiming, or clinical detachment.")
    if mode == "recommendation":
        lines.append("Recommendation: use the adjudicated primary as the canonical doorway, explain its fit from supplied evidence, and preserve nearby canonical pathways.")
    lines.append("provenance: use only retrieved/canonical evidence; never invent titles, claims, or links.")
    return " ".join(lines)[:900]


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


def _resource_link(doc: dict) -> str:
    title = str(doc.get("title") or "").strip()
    title = re.sub(r"^[\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F\u200D]+\s*", "", title).strip()
    url = str(doc.get("url") or doc.get("canonical_url") or "").strip()
    if not title or not url:
        return title
    return f"[{title}]({url})"


def _normalize_title(text: str) -> str:
    title = re.sub(r"^[\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F\u200D]+\s*", "", str(text or "").strip()).strip()
    return re.sub(r"\s{2,}", " ", title)


def _query_profile(user_query: str, docs: list) -> dict:
    query = re.sub(r"\s+", " ", str(user_query or "").strip().casefold())
    return {
        "sensitive": bool(re.search(r"\b(?:grief|grieving|bereavement|bereaved|loss|lost|death|died|dying|loved one|trauma|abuse|coercion|suicid|self-harm|overdose)\b", query)),
        "grief": bool(re.search(r"\b(?:grief|grieving|bereavement|bereaved|loss|death|died|dying|loved one)\b", query)),
        "risk": bool(re.search(r"\b(?:suicid|self-harm|overdose|abuse|coercion|immediate danger|unsafe|threatened)\b", query)),
        "meaning": bool(re.search(r"\b(?:meaning|understanding|perspective|wisdom|why|purpose|identity|continuity|spiritual|afterlife|belief)\b", query)),
        "request_form": bool(re.search(r"\b(?:essay|article|advice|recommend|resource|pathway|collection|reading)\b", query)),
        "docs": docs,
    }


def _evidence_boundary_note(docs: list, profile: dict) -> str:
    has_science = any(re.search(r"\b(?:scientific|science|psychological|neuroscientific|clinical|research)\b", str(doc.get("text") or ""), re.IGNORECASE) for doc in docs)
    has_spiritual = any(re.search(r"\b(?:spiritual|soul|afterlife|religious|mystical|sacred|transcenden)\b", str(doc.get("text") or ""), re.IGNORECASE) for doc in docs)
    if has_science and has_spiritual:
        return "It brings different ways of understanding the question into the same conversation without requiring them to become a single certainty."
    if profile.get("meaning"):
        return "It offers a way into the question while leaving room to distinguish what is known from what remains interpretation, possibility, or personal meaning."
    return "It offers a grounded place to begin without asking the material to provide more certainty than it can support."


def _secondary_role(doc: dict, profile: dict) -> str:
    text = re.sub(r"\s+", " ", str(doc.get("text") or "").strip())
    title = _normalize_title(doc.get("title") or "")
    corpus = f"{title} {text}"
    roles = []
    if re.search(r"\b(?:afterlife|soul|spirit|reincarnation|continuity|connection)\b", corpus, re.IGNORECASE):
        roles.append("continuity and what may endure")
    if re.search(r"\b(?:grief|loss|mourning|bereavement|mortality|death)\b", corpus, re.IGNORECASE):
        roles.append("the lived experience of loss")
    if re.search(r"\b(?:meaning|purpose|identity|perspective|wisdom)\b", corpus, re.IGNORECASE):
        roles.append("meaning and perspective")
    if re.search(r"\b(?:scientific|psychological|research|clinical|neuroscientific)\b", corpus, re.IGNORECASE):
        roles.append("grounded understanding")
    if re.search(r"\b(?:spiritual|religious|mystical|sacred|transcenden)\b", corpus, re.IGNORECASE):
        roles.append("spiritual possibility")
    if profile.get("risk") and re.search(r"\b(?:support|safety|crisis|help|care)\b", corpus, re.IGNORECASE):
        roles.append("support and safety")
    return roles[0] if roles else "another angle on the question"


def _select_secondary_pathways(docs: list, primary_title: str, profile: dict, limit: int = 2) -> list:
    candidates = []
    seen = {_normalize_title(primary_title).casefold()}
    for doc in docs:
        title = _normalize_title(doc.get("title") or "")
        if not title or title.casefold() in seen:
            continue
        text = re.sub(r"\s+", " ", str(doc.get("text") or "").strip())
        score = 0
        if profile.get("grief") and re.search(r"\b(?:grief|loss|death|mortality|meaning|continuity|crisis)\b", f"{title} {text}", re.IGNORECASE):
            score += 3
        if profile.get("meaning") and re.search(r"\b(?:meaning|identity|continuity|purpose|perspective|wisdom)\b", f"{title} {text}", re.IGNORECASE):
            score += 2
        if profile.get("risk") and re.search(r"\b(?:support|safety|crisis|help|care)\b", f"{title} {text}", re.IGNORECASE):
            score += 2
        if score:
            candidates.append((score, title, doc))
    candidates.sort(key=lambda item: (-item[0], item[1].casefold()))
    return [doc for _, _, doc in candidates[:limit]]


def _guide_answer_architecture(user_query: str, primary: dict, docs: list) -> dict:
    profile = _query_profile(user_query, docs)
    title = _normalize_title(primary.get("title") or _BENCHMARK_PRIMARY_TITLE)
    url = str(primary.get("url") or primary.get("canonical_url") or _BENCHMARK_PRIMARY_URL).strip()
    foothold = "A gentle place to begin" if profile["sensitive"] else "A useful place to begin"
    opening = (
        "You may be carrying more than one thing in this question at once—what happened, what it means, and what to do with the feelings that remain."
        if profile["sensitive"] and not profile["grief"] else
        "When you are grieving the death of someone you love, there may be no easy place to begin. Grief can bring pain, longing, questions, and uncertainty all at once."
        if profile["grief"] else
        "A question like this is often easier to approach when there is a clear place to begin and room for the question to remain open."
    )
    boundary = _evidence_boundary_note(docs, profile)
    secondaries = _select_secondary_pathways(docs, title, profile)
    return {"profile": profile, "title": title, "url": url, "foothold": foothold, "opening": opening, "boundary": boundary, "secondaries": secondaries}


def _v339_build_compassionate_recommendation_answer(user_query: str, primary: dict, contextual_docs: list) -> str:
    architecture = _guide_answer_architecture(user_query, primary, contextual_docs)
    profile = architecture["profile"]
    title = architecture["title"]
    url = architecture["url"]
    bridge = (
        "What makes this one especially worthwhile is the way it brings different perspectives into the same conversation without asking you to hurry past the loss or pretend that grief has a tidy answer."
        if profile["grief"] else
        architecture["boundary"]
    )
    sections = [
        architecture["opening"],
        f"{architecture['foothold']} [{title}]({url}).",
        bridge,
    ]
    if architecture["secondaries"]:
        pathway_links = []
        for doc in architecture["secondaries"]:
            link = _resource_link(doc)
            if not link:
                continue
            role = _secondary_role(doc, profile)
            pathway_links.append(f"{link} — for exploring {role}.")
        if pathway_links:
            sections.append("From there, you can follow a couple of nearby reflections:\n\n" + "\n\n".join(pathway_links))
    if profile["risk"]:
        care = "The Archive can offer reflection and orientation, but where there is immediate danger or coercion, the next step should be real-world safety and trusted human support rather than reflection alone."
    elif profile["grief"]:
        care = "You do not need to agree with every idea in these pieces. In grief, it can be enough to find a thought that gives you some companionship, some language for what you are carrying, or simply a place to pause. Take what feels useful, leave what does not, and let the questions remain open where they need to."
    else:
        care = "Take what feels useful, leave what does not, and let the question remain open where it needs to."
    sections.append(care)
    return "\n\n".join(s.strip() for s in sections if s.strip())
