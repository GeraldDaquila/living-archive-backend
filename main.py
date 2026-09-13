# USE PRODUCTION VERSION: v391 — canonical identity recovery
import hashlib
import importlib
import re
from pathlib import Path

APP_VERSION = "v391"
DEPLOYMENT_FINGERPRINT = "USE-v391-canonical-identity-recovery"
CANONICAL_BUILD_ID = "USE-BUILD-v391-canonical-identity-recovery"
EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"

def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def _git_blob_sha256(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()

_MAIN_PATH = Path(__file__).resolve()
_CORE_PATH = _MAIN_PATH.with_name("use_core.py")
RUNTIME_SOURCE_SHA256 = _sha256(_MAIN_PATH.read_bytes())
if not _CORE_PATH.exists():
    raise RuntimeError("USE v391 package integrity failure: use_core.py is missing.")
_core_runtime_sha = _git_blob_sha256(_CORE_PATH.read_bytes())
if _core_runtime_sha != EXPECTED_CORE_BLOB_SHA:
    raise RuntimeError(
        f"USE v391 package integrity failure: expected protected core blob sha={EXPECTED_CORE_BLOB_SHA}, actual={_core_runtime_sha}"
    )

use_core = importlib.import_module("use_core")
_original_generate_llm_response = use_core.generate_llm_response

def _parse_context_documents(context_blocks: str):
    parser = getattr(use_core, "context_blocks_to_documents", None)
    if callable(parser):
        try:
            return parser(str(context_blocks or ""))
        except Exception:
            pass
    docs = []
    for block in str(context_blocks or "").strip().split("\n\n---\n\n"):
        tm = re.search(r"^Title:\s*(.+?)\s*$", block, re.M)
        um = re.search(r"^URL:\s*(https?://\S+)\s*$", block, re.M | re.I)
        cm = re.search(r"^Content:\s*(.*)$", block, re.M | re.S)
        if tm and um and cm:
            docs.append({"title": tm.group(1).strip(), "url": um.group(1).strip().rstrip(".,;"), "text": cm.group(1).strip()})
    return docs

def _context_layers(args, kwargs):
    generation = ""
    source = "none"
    for key in ("retrieved_context_blocks", "retrieved_context", "context_blocks"):
        if kwargs.get(key):
            generation = str(kwargs[key])
            source = key
            break
    if not generation:
        for index in (1, 4, 5):
            if len(args) > index and isinstance(args[index], str) and any(k in args[index] for k in ("Title:", "URL:", "Content:")):
                generation = args[index]
                source = f"args[{index}]"
                break
    canonical = str(kwargs.get("canonical_link_context") or "")
    return source, generation, canonical

def _normalize_title(text: str) -> str:
    return re.sub(r"\s{2,}", " ", str(text or "").strip())

def _clean_evidence_text(text: str) -> str:
    clean = re.sub(r"<[^>]+>", " ", str(text or ""))
    clean = re.sub(r"\[[^\]]*evidence excerpt bounded by USE\]", " ", clean, flags=re.I)
    return re.sub(r"\s+", " ", clean).strip()

def _query_profile(user_query: str) -> dict:
    q = re.sub(r"\s+", " ", str(user_query or "").strip().casefold())
    return {
        "transition": bool(re.search(r"\b(?:major change|change in (?:my|our) life|life change|life transition|transition|new chapter|what comes next|what comes after|lost since|since .*change|after .*change|starting over|beginning again|begin again|moving forward|identity|uncertain what comes next)\b", q)),
        "meaning": bool(re.search(r"\b(?:meaning|purpose|why am i here|what is the point|what does it all mean|make sense|understand the experience)\b", q)),
        "open_question": bool(re.search(r"\b(?:how do i make sense|what do people believe|what are the possibilities|is there more|what happens after|what if there is no|i don't know what to believe|not sure what to believe|does anyone know|can anyone know|different perspectives|many perspectives|open question|no single answer|not sure|uncertain)\b", q)),
        "explicit_framework": bool(re.search(r"\b(?:spiritual|spirituality|religious|religion|mystical|mysticism|afterlife|reincarnation|starseed|ascension|awakening|kundalini|soul|indigenous|traditional wisdom|ai|artificial intelligence|astrology|tarot|political|capitalism|socialism)\b", q)),
    }

def _resource_frame_groups(doc: dict) -> set:
    hay = f"{_normalize_title(doc.get('title') or '').casefold()} {_clean_evidence_text(doc.get('text') or doc.get('content') or '').casefold()}"
    groups = set()
    if re.search(r"\b(?:spiritual|spirituality|religious|religion|mystical|mysticism|afterlife|reincarnation|starseed|ascension|awakening|kundalini|soul|indigenous|traditional wisdom|astrology|tarot)\b", hay):
        groups.add("worldview")
    if re.search(r"\b(?:political|capitalism|socialism)\b", hay):
        groups.add("political")
    return groups

def _is_specialized_framework_resource(doc: dict) -> bool:
    return bool(_resource_frame_groups(doc))

def _transition_evidence_fit(doc: dict, query: str):
    hay = f"{_normalize_title(doc.get('title') or '').casefold()} {_clean_evidence_text(doc.get('text') or doc.get('content') or '').casefold()}"
    q = str(query or '').casefold()
    c = {
        "transition": bool(re.search(r"\b(?:transition|change|chapter|starting over|moving forward|uncertain|flux|reorientation|turning point|new beginning|life change|before and after|crossroads|in-between|rebuild|reorient|adjust|adapt)\b", hay)),
        "meaning": bool(re.search(r"\b(?:meaning|purpose|identity|sensemaking|sense-making|making sense|what it means)\b", hay)),
        "experience": bool(re.search(r"\b(?:experience|lived|personal|human|everyday|relationships|routine|role|journey|navigate|navigating|felt|feeling)\b", hay)),
        "grounding": bool(re.search(r"\b(?:ground|grounding|practical|reflect|reflection|notice|naming|journal|practice|orientation)\b", hay)),
        "open": bool(re.search(r"\b(?:perspective|perspectives|possibilit|different views|different approaches|uncertainty|no single answer|question|open|ambiguous|ambiguity)\b", hay)),
        "worldview": _is_specialized_framework_resource(doc),
        "support": bool(re.search(r"\b(?:support|receive|receiving|care|cared|guilt|need|needing|help|helping)\b", hay)),
        "belief": bool(re.search(r"\b(?:belief|believe|faith|spiritual|religious|worldview)\b", hay)),
    }
    score = sum(int(c[k]) for k in ("transition", "meaning", "experience", "grounding", "open"))
    if re.search(r"\b(?:what comes next|major change|change in my life|life transition|new chapter|lost since|understand the experience|not sure what i believe|without being told what i should feel|without being told what i should believe)\b", q) and (c["transition"] or c["meaning"] or c["experience"]):
        score += 2
    return score, c

def _is_query_aligned_transition_doorway(doc: dict, query: str) -> bool:
    qfit = _query_profile(query)
    if not qfit["transition"] or qfit["explicit_framework"]:
        return False
    score, clusters = _transition_evidence_fit(doc, query)
    if clusters["worldview"]:
        return False
    substantive = int(clusters["transition"]) + int(clusters["meaning"]) + int(clusters["experience"])
    contextual = int(clusters["open"]) + int(clusters["grounding"])
    return substantive >= 2 or (substantive >= 1 and contextual >= 1 and score >= 4)

def _transition_doorway_score(doc: dict, query: str) -> int:
    score, clusters = _transition_evidence_fit(doc, query)
    qfit = _query_profile(query)
    score *= 5
    if clusters["transition"] and qfit["transition"]: score += 8
    if clusters["meaning"] and qfit["meaning"]: score += 5
    if clusters["open"] and qfit["open_question"]: score += 5
    if clusters["experience"]: score += 3
    if clusters["grounding"]: score += 3
    if clusters["support"] and not clusters["transition"]: score -= 8
    if clusters["belief"] and qfit["open_question"] and not qfit["explicit_framework"]: score -= 6
    if clusters["worldview"]: score -= 30
    return score

def _resource_identity(doc: dict) -> str:
    return str(doc.get("url") or doc.get("canonical_url") or doc.get("title") or "").strip().rstrip("/").casefold()

def _identity_index(docs: list) -> dict:
    index = {}
    for doc in docs:
        if not isinstance(doc, dict):
            continue
        title_key = _normalize_title(doc.get("title") or "").casefold()
        url_key = str(doc.get("url") or doc.get("canonical_url") or "").strip().rstrip("/").casefold()
        if title_key:
            index.setdefault(("title", title_key), doc)
        if url_key:
            index.setdefault(("url", url_key), doc)
    return index

def _recover_canonical_candidates(generation_docs: list, canonical_docs: list, query: str) -> list:
    """Recover canonical identity using URL-first, title-second matching.

    Selection authority remains bounded by the supplied generation layer. The
    broader canonical layer only restores authoritative identity/content for a
    selected resource; it cannot introduce a resource absent from generation.
    """
    canonical_index = _identity_index(canonical_docs)
    candidates = []
    seen = set()
    for doc in generation_docs:
        if not isinstance(doc, dict):
            continue
        title_key = _normalize_title(doc.get("title") or "").casefold()
        url_key = str(doc.get("url") or doc.get("canonical_url") or "").strip().rstrip("/").casefold()
        canonical = None
        if url_key:
            canonical = canonical_index.get(("url", url_key))
        if canonical is None and title_key:
            canonical = canonical_index.get(("title", title_key))
        if canonical is None:
            continue
        merged = dict(canonical)
        merged.update({k: v for k, v in doc.items() if v not in (None, "")})
        merged["url"] = str(canonical.get("url") or canonical.get("canonical_url") or merged.get("url") or "").strip()
        if not re.match(r"^https?://\S+$", merged["url"], re.I):
            continue
        if _is_specialized_framework_resource(merged):
            continue
        if not _is_query_aligned_transition_doorway(merged, query):
            continue
        key = _resource_identity(merged)
        if key and key not in seen:
            candidates.append(merged)
            seen.add(key)
    return sorted(candidates, key=lambda d: _transition_doorway_score(d, query), reverse=True)[:4]

def _direct_open_transition_response(docs: list) -> str:
    if not docs:
        return "<visitor_answer>A possible place to begin is with the transition itself: what changed, what feels uncertain now, and what remains open rather than already decided. The material available here does not establish one particular belief about what your experience means, so the question can remain open while you explore it.</visitor_answer>"
    primary = docs[0]
    title = _normalize_title(primary.get("title") or "")
    url = str(primary.get("url") or primary.get("canonical_url") or "").strip()
    if not title or not re.match(r"^https?://\S+$", url, re.I):
        return "<visitor_answer>A possible place to begin is with the transition itself: what changed, what feels uncertain now, and what remains open.</visitor_answer>"
    return f"<visitor_answer>A possible place to begin is with the transition itself: a major change can leave what comes next genuinely open, especially while you are still finding your own language for what the experience means. The material surfaced here can offer a lens for that inquiry without requiring you to adopt a particular belief.\n\nOne useful doorway is [{title}]({url}).</visitor_answer>"

def _v391_finalize(*args, **kwargs):
    user_query = str(kwargs.get("user_query") or (args[0] if args else "") or "")
    intent = str(kwargs.get("intent") or (args[2] if len(args) > 2 else "") or "")
    source, generation_context, canonical_context = _context_layers(args, kwargs)
    if not user_query or intent != "TOPICAL_INQUIRY":
        return _original_generate_llm_response(*args, **kwargs)
    profile = _query_profile(user_query)
    if not (profile["transition"] and profile["open_question"] and not profile["explicit_framework"]):
        return _original_generate_llm_response(*args, **kwargs)
    generation_docs = _parse_context_documents(generation_context)
    canonical_docs = _parse_context_documents(canonical_context)
    recovered = _recover_canonical_candidates(generation_docs, canonical_docs, user_query)
    if not recovered:
        print(f"USE v391 transition doorway: source={source}, generation_docs={len(generation_docs)}, canonical_docs={len(canonical_docs)}, selected=NONE")
        return _direct_open_transition_response([])
    selected = recovered[:1]
    print(f"USE v391 transition doorway: source={source}, generation_docs={len(generation_docs)}, canonical_docs={len(canonical_docs)}, selected={_normalize_title(selected[0].get('title') or '')}")
    return _direct_open_transition_response(selected)

app = use_core.app
app.title = f"Find Your Way (USE) Navigation Engine {APP_VERSION}"
use_core.APP_VERSION = APP_VERSION
use_core.DEPLOYMENT_FINGERPRINT = DEPLOYMENT_FINGERPRINT
use_core.CANONICAL_BUILD_ID = CANONICAL_BUILD_ID
use_core.RUNTIME_SOURCE_SHA256 = RUNTIME_SOURCE_SHA256
use_core.EXPECTED_CORE_BLOB_SHA = EXPECTED_CORE_BLOB_SHA
use_core.generate_llm_response = _v391_finalize
print(f"USE v391 GUIDE BUILD IDENTITY: build_id={CANONICAL_BUILD_ID}, version={APP_VERSION}, fingerprint={DEPLOYMENT_FINGERPRINT}, source_sha256={RUNTIME_SOURCE_SHA256}, core_blob_sha256={_core_runtime_sha}")