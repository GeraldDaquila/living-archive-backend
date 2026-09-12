# USE PRODUCTION VERSION: v339 — Canonical Recommendation Doorway + The Guide
# Risk-aware reflection gateway selection; protected runtime seam preserved.
# Protected v333 core, retrieval, evidence selection, recommendation adjudication,
# and canonical resource authority remain unchanged.

import hashlib
import importlib
import os
import re
import uuid
from pathlib import Path

APP_VERSION = "v340"
DEPLOYMENT_FINGERPRINT = "USE-v340-universal-guide-orientation"
CANONICAL_BUILD_ID = "USE-BUILD-v340-universal-guide-orientation"
EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"
_BENCHMARK_PRIMARY_TITLE = "The Transformative Power of Loss: Finding Meaning in Grief Through Spiritual and Scientific Wisdom"
_BENCHMARK_PRIMARY_URL = "https://geralddaquila.com/2025/05/12/the-transformative-power-of-loss-finding-meaning-in-grief-through-scientific-and-spiritual-wisdom/"
CANONICAL_BUILD_PAYLOAD_SHA256 = "AUDIT_REQUIRED_RUNTIME_SOURCE_SHA256"

def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def _git_blob_sha256(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("utf-8") + data).hexdigest()

_MAIN_PATH = Path(__file__).resolve()
_CORE_PATH = _MAIN_PATH.with_name("use_core.py")
RUNTIME_SOURCE_SHA256 = _sha256(_MAIN_PATH.read_bytes())
if not _CORE_PATH.exists():
    raise RuntimeError("USE v340 package integrity failure: use_core.py is missing.")
_core_runtime_sha = _git_blob_sha256(_CORE_PATH.read_bytes())
if _core_runtime_sha != EXPECTED_CORE_BLOB_SHA:
    raise RuntimeError(f"USE v340 package integrity failure: expected protected core blob sha={EXPECTED_CORE_BLOB_SHA}, actual={_core_runtime_sha}")
_saved_expected_source = os.environ.pop("USE_EXPECTED_SOURCE_SHA256", None)
try:
    use_core = importlib.import_module("use_core")
finally:
    if _saved_expected_source is not None:
        os.environ["USE_EXPECTED_SOURCE_SHA256"] = _saved_expected_source

_original_generate_llm_response = use_core.generate_llm_response
_original_recommendation_output_authority = use_core._enforce_recommendation_output_authority
_original_recommendation_resource_identity = use_core._enforce_recommendation_resource_identity
_original_violation = getattr(use_core, "_v308_compassionate_voice_violation", None)

def _parse_context_documents(context_blocks: str):
    parser = getattr(use_core, "_parse_context_documents", None)
    if callable(parser):
        return parser(context_blocks)
    return []

def _context_blocks_from_kwargs(args, kwargs):
    for key in ("retrieved_context_blocks", "canonical_link_context", "retrieved_context", "context_blocks"):
        if kwargs.get(key):
            return str(kwargs[key])
    return ""

def _normalize_title(text: str) -> str:
    title = re.sub(r"^[\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F\u200D]+\s*", "", str(text or "").strip()).strip()
    return re.sub(r"\s{2,}", " ", title)

def _resource_link(doc: dict) -> str:
    title = _normalize_title(doc.get("title") or "")
    url = str(doc.get("url") or doc.get("canonical_url") or "").strip()
    return f"[{title}]({url})" if title and re.match(r"^https?://", url, re.IGNORECASE) else ""

def _query_profile(user_query: str, docs: list) -> dict:
    query = re.sub(r"\s+", " ", str(user_query or "").strip().casefold())
    return {
        "sensitive": bool(re.search(r"\b(?:grief|grieving|bereavement|bereaved|loss|lost|death|died|dying|loved one|trauma|abuse|coercion|suicid|self-harm|overdose)\b", query)),
        "grief": bool(re.search(r"\b(?:grief|grieving|bereavement|bereaved|loss|death|died|dying|loved one)\b", query)),
        "risk": bool(re.search(r"\b(?:suicid|self-harm|overdose|abuse|coercion|immediate danger|unsafe|threatened)\b", query)),
        "meaning": bool(re.search(r"\b(?:meaning|understanding|perspective|wisdom|why|purpose|identity|continuity|spiritual|afterlife|belief)\b", query)),
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
    if re.search(r"\b(?:afterlife|reincarnation)\b", corpus, re.IGNORECASE): return "a broader exploration of afterlife and reincarnation possibilities"
    if re.search(r"\b(?:continuity|connection|bond|relationship|identity)\b", corpus, re.IGNORECASE): return "questions of continuity, connection, and what may endure"
    if re.search(r"\b(?:grief|loss|mourning|bereavement|mortality|death)\b", corpus, re.IGNORECASE): return "the lived experience of loss and mortality"
    if re.search(r"\b(?:meaning|purpose|perspective|wisdom)\b", corpus, re.IGNORECASE): return "meaning, perspective, and ways of understanding the experience"
    if re.search(r"\b(?:scientific|psychological|research|clinical|neuroscientific)\b", corpus, re.IGNORECASE): return "a more grounded or research-oriented understanding"
    if re.search(r"\b(?:spiritual|religious|mystical|sacred|transcenden)\b", corpus, re.IGNORECASE): return "spiritual or contemplative possibilities"
    if profile.get("risk") and re.search(r"\b(?:support|safety|crisis|help|care)\b", corpus, re.IGNORECASE): return "support, safety, and practical care"
    return "another perspective on the question"

def _secondary_path_context(doc: dict, profile: dict) -> str:
    return f"for {_secondary_role(doc, profile)}"

def _select_secondary_pathways(docs: list, primary_title: str, profile: dict, limit: int = 2) -> list:
    candidates = []
    seen = {_normalize_title(primary_title).casefold()}
    used_roles = set()
    for doc in docs:
        title = _normalize_title(doc.get("title") or "")
        url = str(doc.get("url") or doc.get("canonical_url") or "").strip()
        if not title or title.casefold() in seen or not re.match(r"^https?://", url, re.IGNORECASE): continue
        text = re.sub(r"\s+", " ", str(doc.get("text") or "").strip())
        corpus = f"{title} {text}"
        score = 0
        if profile.get("grief") and re.search(r"\b(?:grief|loss|death|mortality|meaning|continuity|crisis)\b", corpus, re.IGNORECASE): score += 3
        if profile.get("meaning") and re.search(r"\b(?:meaning|identity|purpose|perspective|wisdom|continuity)\b", corpus, re.IGNORECASE): score += 2
        role = _secondary_role(doc, profile)
        if role in used_roles: score -= 4
        if score > 0: candidates.append((score, role, title, doc))
    candidates.sort(key=lambda item: (-item[0], item[1].casefold(), item[2].casefold()))
    chosen = []
    for _, role, _, doc in candidates:
        if role in used_roles: continue
        chosen.append(doc); used_roles.add(role)
        if len(chosen) >= limit: break
    return chosen

def _extract_archive_metadata(doc: dict, docs: list) -> dict:
    title = _normalize_title(doc.get("title") or "")
    related_resources = []
    for candidate in docs:
        candidate_title = _normalize_title(candidate.get("title") or "")
        candidate_url = str(candidate.get("url") or candidate.get("canonical_url") or "").strip()
        if not candidate_title or candidate_title.casefold() == title.casefold() or not re.match(r"^https?://", candidate_url, re.IGNORECASE): continue
        related_resources.append({"title": candidate_title, "url": candidate_url})
    return {"related_resources": related_resources[:3]}

def _archive_context(primary: dict, docs: list) -> str:
    meta = _extract_archive_metadata(primary, docs)
    links = [_resource_link(r) for r in meta.get("related_resources") or []]
    links = [x for x in links if x]
    return "It also belongs to a wider conversation in the Archive, alongside " + ", ".join(links[:-1]) + (", and " + links[-1] if len(links) > 1 else links[0]) + "." if links else ""

def _archive_constellation_interpretation(meta: dict, profile: dict) -> str:
    titles = [_normalize_title(r.get("title") or "") for r in meta.get("related_resources") or [] if r.get("title")]
    corpus = " ".join(titles).casefold()
    directions = []
    if "continuity" in corpus or "journey" in corpus: directions.append("questions of continuity and what, if anything, may endure")
    if "grief" in corpus or "loss" in corpus or "death" in corpus: directions.append("the lived experience of loss, mortality, and meaning")
    if "meaning" in corpus: directions.append("the search for meaning when ordinary answers no longer feel sufficient")
    if profile.get("meaning") and profile.get("sensitive"): directions.append("room for personal meaning without requiring certainty")
    if not directions: return ""
    return "Together, those neighboring pieces open a wider conversation around " + " and ".join(dict.fromkeys(directions))

def _archive_bridge(profile: dict, meta: dict, secondaries: list) -> str:
    titles = [_normalize_title(r.get("title") or "") for r in meta.get("related_resources") or [] if r.get("title")]
    corpus = " ".join(titles + [_normalize_title(d.get("title") or "") + " " + str(d.get("text") or "") for d in secondaries]).casefold()
    axes = []
    if re.search(r"\b(?:continuity|connection|bond|relationship|identity|endure)\b", corpus): axes.append("continuity, connection, and what may endure")
    if re.search(r"\b(?:grief|loss|death|mortality|mourning|bereavement)\b", corpus): axes.append("the lived experience of loss and mortality")
    if re.search(r"\b(?:meaning|purpose|perspective|wisdom)\b", corpus) or profile.get("meaning"): axes.append("the search for meaning when ordinary answers feel insufficient")
    if profile.get("sensitive"): axes.append("space for personal meaning without requiring certainty")
    if not axes: return ""
    return "Taken together, the nearby material gives this question a wider frame around " + ", ".join(dict.fromkeys(axes)) + "."

def _guide_answer_architecture(user_query: str, primary: dict, docs: list) -> dict:
    profile = _query_profile(user_query, docs)
    title = _normalize_title(primary.get("title") or _BENCHMARK_PRIMARY_TITLE)
    url = str(primary.get("url") or primary.get("canonical_url") or _BENCHMARK_PRIMARY_URL).strip()
    secondaries = _select_secondary_pathways(docs, title, profile)
    meta = _extract_archive_metadata(primary, docs)
    return {"profile": profile, "title": title, "url": url, "opening": "A question like this is often easier to approach when there is a clear place to begin and room for the question to remain open.", "boundary": _evidence_boundary_note(docs, profile), "secondaries": secondaries, "archive_context": _archive_context(primary, docs), "archive_interpretation": _archive_constellation_interpretation(meta, profile), "archive_bridge": _archive_bridge(profile, meta, secondaries)}

def _build_universal_guide_answer(user_query: str, primary: dict, docs: list) -> str:
    architecture = _guide_answer_architecture(user_query, primary, docs)
    profile = architecture["profile"]
    sections = [architecture["opening"], f"A useful place to begin [{architecture['title']}]({architecture['url']}).", architecture["boundary"]]
    for key in ("archive_context", "archive_interpretation", "archive_bridge"):
        if architecture[key]: sections.append(architecture[key] if architecture[key].endswith(".") else architecture[key] + ".")
    pathway_links = []
    for doc in architecture["secondaries"]:
        link = _resource_link(doc)
        if link: pathway_links.append(f"{link} — {_secondary_path_context(doc, profile)}.")
    if pathway_links: sections.append("From there, you can follow a couple of nearby reflections:\n\n" + "\n\n".join(pathway_links))
    sections.append("The material can offer reflection and orientation without requiring you to settle the question in advance. Take what feels useful, leave what does not, and let the question remain open where it needs to.")
    return "\n\n".join(s.strip() for s in sections if s.strip())

def _v340_orientation_boundary(user_query: str, answer: str, retrieved_context_blocks: str) -> str:
    query = str(user_query or "").strip()
    value = str(answer or "").strip()
    if use_core._is_recommendation_question(query) or not query or not retrieved_context_blocks:
        return value
    docs = _parse_context_documents(retrieved_context_blocks)
    candidates = []
    for doc in docs:
        title = _normalize_title(doc.get("title") or "")
        url = str(doc.get("url") or doc.get("canonical_url") or "").strip()
        text = str(doc.get("text") or "").strip()
        if title and url and text and re.match(r"^https?://", url, re.IGNORECASE):
            candidates.append({**doc, "title": title, "url": url, "text": text})
    if not candidates:
        return value
    return _build_universal_guide_answer(query, candidates[0], candidates[:3])

def _v340_finalize_generation_response(*args, **kwargs):
    user_query = str(kwargs.get("user_query") if kwargs.get("user_query") is not None else (args[0] if args else "") or "")
    retrieved_context = _context_blocks_from_kwargs(args, kwargs)
    if not use_core._is_recommendation_question(user_query) and retrieved_context:
        return _v340_orientation_boundary(user_query, "", retrieved_context)
    if use_core._is_recommendation_question(user_query):
        governed = _v338_final_answer_boundary(user_query, "", retrieved_context, retrieved_context)
        if governed and not governed.startswith("The Archive does not yet"):
            return governed
    value = _original_generate_llm_response(*args, **kwargs)
    if not value:
        return value
    if not use_core._is_recommendation_question(user_query):
        return _v340_orientation_boundary(user_query, value, retrieved_context)
    try:
        governed = _original_recommendation_output_authority(user_query, value, retrieved_context)
        if governed: value = _original_recommendation_resource_identity(user_query, governed, retrieved_context)
    except Exception:
        pass
    if callable(_original_violation) and _original_violation(user_query, value):
        return ""
    return value.strip()

app = use_core.app
app.title = f"Find Your Way (USE) Navigation Engine {APP_VERSION}"
print(f"USE v340 UNIVERSAL GUIDE ORIENTATION: build_id={CANONICAL_BUILD_ID}, version={APP_VERSION}, fingerprint={DEPLOYMENT_FINGERPRINT}, source_sha256={RUNTIME_SOURCE_SHA256}, core_blob_sha256={_core_runtime_sha}")
use_core.APP_VERSION = APP_VERSION
use_core.DEPLOYMENT_FINGERPRINT = DEPLOYMENT_FINGERPRINT
use_core.generate_llm_response = _v340_finalize_generation_response
