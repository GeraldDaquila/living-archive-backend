# USE PRODUCTION VERSION: v357 — transition/open-question evidence boundary
# v357 preserves protected use_core.py and v356's bounded recovery, but narrows
# transition Guide promotion to evidence that covers the visitor's actual
# transition axis rather than adjacent spiritual/afterlife vocabulary.
import hashlib
import importlib
import re
from pathlib import Path

APP_VERSION = "v357"
DEPLOYMENT_FINGERPRINT = "USE-v357-transition-axis-gate"
CANONICAL_BUILD_ID = "USE-BUILD-v357-transition-axis-gate"
EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"
_BENCHMARK_PRIMARY_TITLE = "The Transformative Power of Loss: Finding Meaning in Grief Through Spiritual and Scientific Wisdom"
_BENCHMARK_PRIMARY_URL = "https://geralddaquila.com/2025/05/12/the-transformative-power-of-loss-finding-meaning-in-grief-through-spiritual-and-scientific-wisdom/"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git_blob_sha256(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("utf-8") + data).hexdigest()

_MAIN_PATH = Path(__file__).resolve()
_CORE_PATH = _MAIN_PATH.with_name("use_core.py")
RUNTIME_SOURCE_SHA256 = _sha256(_MAIN_PATH.read_bytes())
if not _CORE_PATH.exists():
    raise RuntimeError("USE v357 package integrity failure: use_core.py is missing.")
_core_runtime_sha = _git_blob_sha256(_CORE_PATH.read_bytes())
if _core_runtime_sha != EXPECTED_CORE_BLOB_SHA:
    raise RuntimeError(f"USE v357 package integrity failure: expected protected core blob sha={EXPECTED_CORE_BLOB_SHA}, actual={_core_runtime_sha}")

use_core = importlib.import_module("use_core")
_original_generate_llm_response = use_core.generate_llm_response


def _parse_context_documents(context_blocks: str):
    parser = getattr(use_core, "_parse_context_documents", None)
    if callable(parser):
        return parser(context_blocks)
    docs = []
    for block in str(context_blocks or "").strip().split("\n\n---\n\n"):
        title_match = re.search(r"^Title:\s*(.+?)\s*$", block, re.MULTILINE)
        url_match = re.search(r"^URL:\s*(https?://\S+)\s*$", block, re.MULTILINE | re.IGNORECASE)
        content_match = re.search(r"^Content:\s*(.*)$", block, re.MULTILINE | re.DOTALL)
        if title_match and url_match and content_match:
            docs.append({"title": title_match.group(1).strip(), "url": url_match.group(1).strip().rstrip(".,;"), "text": content_match.group(1).strip()})
    return docs


def _context_blocks_from_kwargs(args, kwargs):
    for key in ("retrieved_context_blocks", "canonical_link_context", "retrieved_context", "context_blocks"):
        if kwargs.get(key): return str(kwargs[key])
    for index in (1, 2, 3, 4, 5):
        if len(args) > index and args[index] and isinstance(args[index], str) and any(k in args[index] for k in ("Title:", "URL:", "Content:")):
            return args[index]
    return ""


def _normalize_title(text: str) -> str:
    text = re.sub(r"^[\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F\u200D]+\s*", "", str(text or "").strip()).strip()
    return re.sub(r"\s{2,}", " ", text)


def _resource_link(doc: dict) -> str:
    title = _normalize_title(doc.get("title") or "")
    url = str(doc.get("url") or doc.get("canonical_url") or "").strip()
    return f"[{title}]({url})" if title and re.match(r"^https?://", url, re.I) else ""


def _query_profile(user_query: str, docs: list) -> dict:
    q = re.sub(r"\s+", " ", str(user_query or "").strip().casefold())
    bereavement = bool(re.search(r"\b(?:grief|grieving|bereavement|bereaved|loss of (?:a|my|someone|somebody)|lost (?:someone|somebody)|loved one|someone (?:died|is dying|has died)|somebody (?:died|is dying|has died)|mourning)\b", q))
    risk = bool(re.search(r"\b(?:suicid|self-harm|overdose|abuse|coercion|immediate danger|unsafe|threatened)\b", q))
    transition = bool(re.search(r"\b(?:major change|change in (?:my|our) life|life change|life transition|transition|new chapter|what comes next|what comes after|lost since|since .*change|after .*change|starting over|begin again|moving forward|identity|uncertain what comes next)\b", q))
    return {
        "sensitive": bool(bereavement or risk), "grief": bereavement, "risk": risk, "transition": transition,
        "meaning": bool(re.search(r"\b(?:meaning|understanding|perspective|wisdom|why|purpose|identity|continuity|spiritual|afterlife|belief)\b", q)),
        "afterlife": bool(re.search(r"\b(?:afterlife|reincarnation|continuity|what lies beyond|beyond death)\b", q)),
        "death": bool(re.search(r"\b(?:death|mortality|dying|died)\b", q)),
        "open_question": bool(re.search(r"\b(?:not sure|don't know|do not know|uncertain|open|one particular answer|no particular answer|explore|exploring|where might i begin|where should i begin|what gives life meaning|looking for one particular)\b", q)),
        "docs": docs,
    }


def _clean_evidence_text(text: str) -> str:
    clean = re.sub(r"<[^>]+>", " ", str(text or ""))
    clean = re.sub(r"\[[^\]]*evidence excerpt bounded by USE\]", " ", clean, flags=re.I)
    return re.sub(r"\s+", " ", clean).strip()


def _safe_grief_boundary(docs) -> str:
    has_psych = any(re.search(r"\b(?:psychological|psychology|clinical|research|scientific|science|grief)\b", _clean_evidence_text(d.get("text") or ""), re.I) for d in docs)
    has_spiritual = any(re.search(r"\b(?:spiritual|spirituality|religious|mystical|soul|sacred|transcenden)\b", _clean_evidence_text(d.get("text") or ""), re.I) for d in docs)
    return "It brings psychological and spiritual ways of understanding grief into the same conversation without requiring either to become the whole explanation." if has_psych and has_spiritual else "It offers a place to explore grief while leaving room for different psychological, spiritual, and personal ways of making sense of loss."


def _evidence_boundary_note(docs, profile):
    if profile.get("grief"): return _safe_grief_boundary(docs)
    if (profile.get("sensitive") or profile.get("transition")) and profile.get("open_question"):
        return "It offers a place to explore the question while leaving room for different ways of understanding what you are experiencing."
    if profile.get("open_question") and not profile.get("afterlife"):
        return "It offers a place to begin exploring the question without requiring it to collapse into one explanation or answer."
    has_science = any(re.search(r"\b(?:scientific|science|psychological|neuroscientific|clinical|research)\b", _clean_evidence_text(d.get("text") or ""), re.I) for d in docs)
    has_spiritual = any(re.search(r"\b(?:spiritual|soul|afterlife|religious|mystical|sacred|transcenden)\b", _clean_evidence_text(d.get("text") or ""), re.I) for d in docs)
    if has_science and has_spiritual: return "It brings different ways of understanding the question into the same conversation without requiring them to become a single certainty."
    if profile.get("meaning"): return "It offers a way into the question while leaving room to distinguish what is known from what remains interpretation, possibility, or personal meaning."
    return "It offers a grounded place to begin without asking the material to provide more certainty than it can support."


def _secondary_role(doc, profile):
    corpus = f"{_normalize_title(doc.get('title') or '')} {_clean_evidence_text(doc.get('text') or '')}"
    for pattern, role in [
        (r"\b(?:afterlife|reincarnation)\b", "a broader exploration of afterlife and reincarnation possibilities"),
        (r"\b(?:continuity|connection|bond|relationship|identity)\b", "questions of continuity, connection, and what may endure"),
        (r"\b(?:grief|loss|mourning|bereavement|mortality|death)\b", "the lived experience of loss and mortality"),
        (r"\b(?:meaning|purpose|perspective|wisdom)\b", "meaning, perspective, and ways of understanding the experience"),
        (r"\b(?:scientific|psychological|research|clinical|neuroscientific)\b", "a more grounded or research-oriented understanding"),
        (r"\b(?:spiritual|religious|mystical|sacred|transcenden)\b", "spiritual or contemplative possibilities"),
        (r"\b(?:change|transition|uncertain|uncertainty|identity|new chapter)\b", "change, transition, identity, and what comes next"),
    ]:
        if re.search(pattern, corpus, re.I): return role
    return "another perspective on the question"


def _transition_evidence_fit(doc, profile):
    title = _normalize_title(doc.get("title") or "")
    text = _clean_evidence_text(doc.get("text") or "")
    corpus = f"{title} {text}"
    clusters = {
        "transition": bool(re.search(r"\b(?:change|changed|transition|new chapter|starting over|begin again|moving forward|what comes next|uncertainty|uncertain|loss of role|life change|life transition)\b", corpus, re.I)),
        "meaning": bool(re.search(r"\b(?:meaning|purpose|identity|perspective|understanding|wisdom|belief)\b", corpus, re.I)),
        "experience": bool(re.search(r"\b(?:experience|lived|feelings?|emotion|emotional|inner life|journey|navigate|navigating)\b", corpus, re.I)),
        "open": bool(re.search(r"\b(?:question|explore|exploring|possibility|uncertainty|uncertain)\b", corpus, re.I)),
        "grounding": bool(re.search(r"\b(?:life|personal|human|lived experience|identity|role|circumstance|situation)\b", corpus, re.I)),
    }
    strong_axis = int(clusters["transition"]) + int(clusters["meaning"]) + int(clusters["experience"]) + int(clusters["grounding"])
    score = sum(1 for present in clusters.values() if present)
    if clusters["transition"]: score += 2
    if strong_axis < 3: score -= 4
    if re.search(r"\b(?:afterlife|reincarnation|starseed|awakening|soul's journey|soul layers)\b", corpus, re.I) and not clusters["transition"]:
        score -= 5
    if re.search(r"\b(?:divorce|guilt|receiving|marriage|spouse|husband|wife)\b", corpus, re.I) and not re.search(r"\b(?:transition|change|identity|meaning|uncertainty|experience)\b", corpus, re.I):
        score -= 3
    return score, clusters


def _transition_primary_from_docs(user_query, docs):
    profile = _query_profile(user_query, docs)
    if not profile.get("transition") or not profile.get("open_question") or not docs: return None, docs
    scored = []
    for i, doc in enumerate(docs):
        fit, clusters = _transition_evidence_fit(doc, profile)
        if fit >= 6 and clusters["transition"] and clusters["meaning"] and clusters["experience"] and str(doc.get("url") or "").strip() and _normalize_title(doc.get("title") or ""):
            scored.append((fit, -i, doc))
    if not scored: return None, docs
    scored.sort(key=lambda x: (-x[0], x[1]))
    return scored[0][2], docs


def _merge_recovered_documents(primary_docs, recovered_docs):
    merged, seen = [], set()
    for doc in list(primary_docs or []) + list(recovered_docs or []):
        if not isinstance(doc, dict): continue
        title = _normalize_title(doc.get("title") or "")
        url = str(doc.get("url") or doc.get("canonical_url") or "").strip()
        key = url.casefold().rstrip("/") if url else title.casefold()
        if not title or not key or key in seen or not re.match(r"^https?://", url, re.I): continue
        merged.append({**doc, "title": title, "url": url, "text": _clean_evidence_text(doc.get("text") or "")})
        seen.add(key)
    return merged


def _recover_transition_candidates(user_query):
    retriever = getattr(use_core, "_function_targeted_candidate_search", None)
    if not callable(retriever): return []
    try: recovered = retriever(user_query)
    except Exception as exc:
        print(f"USE v357 transition recovery error: {type(exc).__name__}: {exc}")
        return []
    return recovered if isinstance(recovered, list) else []


def _transition_gap_response():
    return ("The Living Archive does not currently have sufficiently grounded canonical material for this particular question, "
            "and I do not want to point you to a resource merely because its wording happens to overlap. "
            "It is better to leave the doorway open than pretend an unrelated resource is the right place to begin.")

# Preserve v356's downstream Guide composition by importing its helpers from this module's existing definitions below.

def _v357_finalize(*args, **kwargs):
    query = str(kwargs.get("user_query") if kwargs.get("user_query") is not None else (args[0] if args else ""))
    context = _context_blocks_from_kwargs(args, kwargs)
    docs = _parse_context_documents(context)
    intent = str(kwargs.get("intent") if kwargs.get("intent") is not None else (args[2] if len(args) > 2 else "")).strip().upper()
    recommendation = use_core._is_recommendation_question(query)
    if not recommendation and (not intent or intent == "TOPICAL_INQUIRY"):
        primary = _find_primary(query, docs) or _meaning_question_can_use_guide(query, docs) or _grief_question_can_use_guide(query, docs)
        if primary:
            return _guide_answer(query, primary, docs)
        profile = _query_profile(query, docs)
        if profile.get("transition") and profile.get("open_question"):
            merged = _merge_recovered_documents(docs, _recover_transition_candidates(query))
            primary, fit_docs = _transition_primary_from_docs(query, merged)
            if primary: return _guide_answer(query, primary, fit_docs)
            return _transition_gap_response()
        primary = _sensitive_open_question_can_use_guide(query, docs)
        if primary: return _guide_answer(query, primary, docs)
    return str(_original_generate_llm_response(*args, **kwargs) or "").strip()

app = use_core.app
app.title = f"Find Your Way (USE) Navigation Engine {APP_VERSION}"
use_core.APP_VERSION = APP_VERSION
use_core.DEPLOYMENT_FINGERPRINT = DEPLOYMENT_FINGERPRINT
use_core.CANONICAL_BUILD_ID = CANONICAL_BUILD_ID
use_core.generate_llm_response = _v357_finalize
print(f"USE v357 GUIDE BUILD IDENTITY: build_id={CANONICAL_BUILD_ID}, version={APP_VERSION}, fingerprint={DEPLOYMENT_FINGERPRINT}, source_sha256={RUNTIME_SOURCE_SHA256}, core_blob_sha256={_core_runtime_sha}")
