# USE PRODUCTION VERSION: v418 — complementary doorway title fallback
import hashlib
import importlib
import re
from pathlib import Path

APP_VERSION = "v418"
DEPLOYMENT_FINGERPRINT = "USE-v418-complementary-doorway-title-fallback"
CANONICAL_BUILD_ID = "USE-BUILD-v418-complementary-doorway-title-fallback"
EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"

_MAIN_PATH = Path(__file__).resolve()
_CORE_PATH = _MAIN_PATH.with_name("use_core.py")
RUNTIME_SOURCE_SHA256 = hashlib.sha256(_MAIN_PATH.read_bytes()).hexdigest()
if not _CORE_PATH.exists():
    raise RuntimeError("USE v418 package integrity failure: use_core.py is missing.")
_core_bytes = _CORE_PATH.read_bytes()
_core_runtime_sha = hashlib.sha1(f"blob {len(_core_bytes)}\0".encode() + _core_bytes).hexdigest()
if _core_runtime_sha != EXPECTED_CORE_BLOB_SHA:
    raise RuntimeError(f"USE v418 package integrity failure: expected protected core blob sha={EXPECTED_CORE_BLOB_SHA}, actual={_core_runtime_sha}")

use_core = importlib.import_module("use_core")
_original_generate_llm_response = use_core.generate_llm_response


def _parse_context_documents(context_blocks: str):
    parser = getattr(use_core, "_parse_context_documents", None)
    if callable(parser):
        return parser(context_blocks)
    docs = []
    for block in str(context_blocks or "").strip().split("\n\n---\n\n"):
        tm = re.search(r"^Title:\s*(.+?)\s*$", block, re.M)
        um = re.search(r"^URL:\s*(https?://\S+)\s*$", block, re.M | re.I)
        cm = re.search(r"^Content:\s*(.*)$", block, re.M | re.S)
        if tm and um and cm:
            docs.append({"title": tm.group(1).strip(), "url": um.group(1).strip().rstrip(".,;"), "text": cm.group(1).strip()})
    return docs


def _extract_user_query(args, kwargs):
    for key in ("user_query", "query", "question"):
        value = kwargs.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return args[0].strip() if len(args) >= 1 and isinstance(args[0], str) and args[0].strip() else ""


def _context_blocks_from_kwargs(args, kwargs):
    for key in ("retrieved_context_blocks", "retrieved_context", "context_blocks"):
        if kwargs.get(key):
            return str(kwargs[key])
    return args[1] if len(args) >= 2 and isinstance(args[1], str) else ""


def _normalize_title(text: str) -> str:
    return re.sub(r"^[\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F\u200D]+\s*", "", str(text or "").strip()).strip()


def _query_profile(user_query: str) -> dict:
    q = re.sub(r"\s+", " ", str(user_query or "").strip().casefold())
    return {
        "loneliness": bool(re.search(r"\b(?:loneliness|lonely|alone|isolat|disconnected|belonging|connection)\b", q)),
        "risk": bool(re.search(r"\b(?:suicid|self-harm|overdose|abuse|coercion|immediate danger|unsafe|threatened)\b", q)),
        "explicit_framework": bool(re.search(r"\b(?:spiritual|spirituality|religious|religion|mystical|mysticism|afterlife|reincarnation|soul|astrology|tarot|starseed)\b", q)),
    }


def _role_evidence(doc: dict) -> dict:
    text = re.sub(r"\s+", " ", str(doc.get("text") or "").strip().casefold())
    title = _normalize_title(doc.get("title") or "").casefold()
    corpus = title + " " + text
    return {
        "direct_loneliness": bool(re.search(r"\b(?:loneliness|lonely|social isolation|socially isolated|feeling alone|sense of aloneness|disconnected|disconnection|lack of connection|need for connection)\b", text)),
        "belonging_connection": bool(re.search(r"\b(?:belonging|connection|connected|relationship|relationships|community|companionship|being seen|being understood|social connection)\b", corpus)),
        "lived_experience": bool(re.search(r"\b(?:experience|lived|personal|human|everyday|relationships|routine|role|journey|navigate|navigating|felt|feeling|living with)\b", text)),
        "meaning": bool(re.search(r"\b(?:meaning|purpose|wisdom|perspective|understanding|sense-making|make sense|interpretation)\b", corpus)),
        "grounded": bool(re.search(r"\b(?:science|scientific|research|psychological|clinical|neuroscientific|evidence|empirical)\b", corpus)),
        "worldview": bool(re.search(r"\b(?:spiritual|spirituality|religious|religion|mystical|mysticism|afterlife|reincarnation|soul|sacred|transcenden|starseed)\b", corpus)),
        "practical_reflection": bool(re.search(r"\b(?:reflect|reflection|notice|naming|journal|practice|grounding|orientation|practical|everyday|attention)\b", text)),
        "acute_risk": bool(re.search(r"\b(?:suicid(?:e|al|ality)|suicidal ideation|self-harm|overdose|acute crisis|crisis intervention|immediate danger)\b", corpus)),
        "title_risk": bool(re.search(r"\b(?:suicide|suicidal|self-harm|overdose|crisis intervention|acute crisis)\b", title)),
        "title_loneliness": bool(re.search(r"\b(?:loneliness|lonely|alone|belonging|connection|connected|isolation|isolated)\b", title)),
        "title_meaning": bool(re.search(r"\b(?:meaning|purpose|perspective|wisdom|understanding|journey|soul|life)\b", title)),
        "title_life": bool(re.search(r"\b(?:life|human|person|people|living|death|grief|existential)\b", title)),
    }


def _is_risk_related(doc: dict) -> bool:
    e = _role_evidence(doc)
    return e["acute_risk"] or e["title_risk"]


def _loneliness_primary_score(doc: dict, profile: dict) -> int:
    e = _role_evidence(doc)
    if _is_risk_related(doc) and not profile.get("risk"):
        return -10_000
    score = 100 * int(e["title_loneliness"])
    score += 75 * int(e["direct_loneliness"])
    score += 22 * int(e["belonging_connection"])
    score += 18 * int(e["lived_experience"])
    score += 8 * int(e["meaning"])
    score += 5 * int(e["grounded"])
    if e["worldview"] and not profile.get("explicit_framework"):
        score -= 40
    if not profile.get("explicit_framework") and re.search(r"\b(?:starseed|afterlife|reincarnation|higher-order intelligence)\b", _normalize_title(doc.get("title") or "") + " " + str(doc.get("text") or ""), re.I):
        score -= 45
    if e["title_loneliness"] and e["direct_loneliness"]:
        score += 25
    return score


def _select_loneliness_primary(docs, profile):
    ranked = []
    for index, doc in enumerate(docs):
        title = _normalize_title(doc.get("title") or "")
        url = str(doc.get("url") or doc.get("canonical_url") or "").strip()
        if not title or not re.match(r"^https?://\S+$", url, re.I):
            continue
        score = _loneliness_primary_score(doc, profile)
        if score > 0:
            ranked.append((score, index, doc))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return ranked[0][2] if ranked else None


def _secondary_role_candidates(doc: dict):
    e = _role_evidence(doc)
    if e["acute_risk"] or e["title_risk"] or e["direct_loneliness"]:
        return []
    candidates = []
    if e["grounded"]:
        candidates.append(("grounded", "a grounded or research-oriented route into the experience", 30))
    if e["meaning"]:
        candidates.append(("meaning", "a route into meaning, perspective, and ways of understanding loneliness", 28))
    if e["practical_reflection"]:
        candidates.append(("reflection", "a reflective route into staying with the experience", 24))
    if e["belonging_connection"]:
        candidates.append(("belonging", "a route into connection and belonging", 22))
    if e["title_meaning"]:
        candidates.append(("meaning_title", "a broader route into meaning and perspective", 18))
    if e["title_life"] and e["lived_experience"]:
        candidates.append(("human", "a broader route into the lived human dimensions around loneliness", 20))
    return candidates


def _secondary_role_quality(doc: dict, role_key: str) -> int:
    e = _role_evidence(doc)
    text = re.sub(r"\s+", " ", str(doc.get("text") or "").strip().casefold())
    if e["acute_risk"] or e["title_risk"]:
        return -1000
    score = 0
    score += 18 * int(e["grounded"])
    score += 18 * int(e["meaning"])
    score += 12 * int(e["lived_experience"])
    score += 10 * int(e["belonging_connection"])
    score += 8 * int(e["title_meaning"])
    score += 6 * int(e["title_life"])
    score += 10 * int(e["practical_reflection"])
    score -= 18 * int(e["worldview"])
    if re.search(r"\b(?:recommend|should|must|need to|therapy|treatment|diagnos)\b", text):
        score -= 20
    role_bonus = {"grounded": 22, "meaning": 20, "reflection": 18, "belonging": 16, "meaning_title": 12, "human": 14}
    return score + role_bonus.get(role_key, 0)


def _select_loneliness_secondary(docs, primary_title, profile):
    seen = {_normalize_title(primary_title).casefold()}
    candidates = []
    for index, doc in enumerate(docs):
        title = _normalize_title(doc.get("title") or "")
        url = str(doc.get("url") or doc.get("canonical_url") or "").strip()
        if not title or not re.match(r"^https?://\S+$", url, re.I) or title.casefold() in seen:
            continue
        combined = title + " " + str(doc.get("text") or "")
        if not profile.get("explicit_framework") and re.search(r"\b(?:starseed|afterlife|reincarnation|higher-order intelligence)\b", combined, re.I):
            continue
        for role_key, role_text, role_bonus in _secondary_role_candidates(doc):
            role_quality = _secondary_role_quality(doc, role_key)
            if role_quality < 42:
                continue
            candidates.append((role_quality + role_bonus, index, role_key, role_text, doc))
    candidates.sort(key=lambda item: (-item[0], item[1]))
    if not candidates:
        return None, None, None
    return candidates[0][4], candidates[0][3], candidates[0][2]


def _evidence_boundary_note(docs, has_secondary=False):
    has_science = any(re.search(r"\b(?:scientific|science|psychological|neuroscientific|clinical|research)\b", str(doc.get("text") or ""), re.I) for doc in docs)
    has_spiritual = any(re.search(r"\b(?:spiritual|soul|afterlife|religious|mystical|sacred|transcenden)\b", str(doc.get("text") or ""), re.I) for doc in docs)
    if has_secondary and has_science and has_spiritual:
        return "The Archive opens different ways of understanding loneliness without requiring them to become one certainty."
    if has_secondary:
        return "The Archive offers more than one way into the question, and the routes do different work rather than resolving it into one certainty."
    if has_spiritual:
        return "Where the material turns toward spiritual or afterlife possibilities, those are perspectives offered by the work rather than established facts you need to accept."
    return "The material can open a way into the question without deciding in advance what loneliness must mean."


def _build_loneliness_answer(user_query, primary, docs):
    title = _normalize_title(primary.get("title") or "")
    url = str(primary.get("url") or primary.get("canonical_url") or "").strip()
    if not title or not re.match(r"^https?://\S+$", url, re.I):
        return ""
    profile = _query_profile(user_query)
    secondary, role_text, _role_key = _select_loneliness_secondary(docs, title, profile)
    sections = [
        "Loneliness can be difficult to name because it is not always only about being physically alone. It can touch belonging, connection, meaning, and the sense of being seen or understood.",
        f"A gentle place to begin is [{title}]({url}).",
    ]
    if secondary:
        item_title = _normalize_title(secondary.get("title") or "")
        item_url = str(secondary.get("url") or secondary.get("canonical_url") or "").strip()
        sections.append(_evidence_boundary_note(docs, has_secondary=True))
        sections.append(f"From a different angle, [{item_title}]({item_url}) offers {role_text}.")
    else:
        sections.append(_evidence_boundary_note(docs, has_secondary=False))
    sections.append("You do not have to turn loneliness into a diagnosis or a final explanation. A useful piece can simply give you another language for noticing what the experience is asking you to consider.")
    return "\n\n".join(sections)


def _v418_finalize(*args, **kwargs):
    user_query = _extract_user_query(args, kwargs)
    raw_context = _context_blocks_from_kwargs(args, kwargs)
    docs = _parse_context_documents(raw_context)
    profile = _query_profile(user_query)
    if user_query and profile.get("loneliness") and not profile.get("risk"):
        primary = _select_loneliness_primary(docs, profile)
        if primary:
            answer = _build_loneliness_answer(user_query, primary, docs)
            if answer:
                return answer
    return _original_generate_llm_response(*args, **kwargs)


app = use_core.app
app.title = f"Find Your Way (USE) Navigation Engine {APP_VERSION}"
print(f"USE v418 GUIDE BUILD IDENTITY: build_id={CANONICAL_BUILD_ID}, version={APP_VERSION}, fingerprint={DEPLOYMENT_FINGERPRINT}, source_sha256={RUNTIME_SOURCE_SHA256}, core_blob_sha256={_core_runtime_sha}")
use_core.APP_VERSION = APP_VERSION
use_core.DEPLOYMENT_FINGERPRINT = DEPLOYMENT_FINGERPRINT
use_core.CANONICAL_BUILD_ID = CANONICAL_BUILD_ID
use_core.RUNTIME_SOURCE_SHA256 = RUNTIME_SOURCE_SHA256
use_core.EXPECTED_CORE_BLOB_SHA = EXPECTED_CORE_BLOB_SHA
use_core.generate_llm_response = _v418_finalize
