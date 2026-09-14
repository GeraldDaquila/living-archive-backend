# USE PRODUCTION VERSION: v409 — complementary pathway query expansion
# v391 remains the protected production baseline; this wrapper changes only visitor-facing
# recommendation role selection/construction. Protected use_core.py is unchanged.
import hashlib
import importlib
import re
from pathlib import Path

APP_VERSION = "v409"
DEPLOYMENT_FINGERPRINT = "USE-v409-complementary-pathway-query-expansion"
CANONICAL_BUILD_ID = "USE-BUILD-v409-complementary-pathway-query-expansion"
EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"

_MAIN_PATH = Path(__file__).resolve()
_CORE_PATH = _MAIN_PATH.with_name("use_core.py")
RUNTIME_SOURCE_SHA256 = hashlib.sha256(_MAIN_PATH.read_bytes()).hexdigest()
if not _CORE_PATH.exists():
    raise RuntimeError("USE v409 package integrity failure: use_core.py is missing.")
_core_bytes = _CORE_PATH.read_bytes()
_core_runtime_sha = hashlib.sha1(f"blob {len(_core_bytes)}\0".encode() + _core_bytes).hexdigest()
if _core_runtime_sha != EXPECTED_CORE_BLOB_SHA:
    raise RuntimeError(f"USE v409 package integrity failure: expected protected core blob sha={EXPECTED_CORE_BLOB_SHA}, actual={_core_runtime_sha}")

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


def _extract_intent(args, kwargs):
    for key in ("intent", "query_intent", "classification"):
        value = kwargs.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return args[2].strip() if len(args) >= 3 and isinstance(args[2], str) and args[2].strip() else ""


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
        "sensitive": bool(re.search(r"\b(?:grief|grieving|bereavement|bereaved|loss|lost|death|died|dying|loved one|trauma|abuse|coercion|suicid|self-harm|overdose|loneliness|lonely|despair|emptiness|depressed|depression)\b", q)),
        "loneliness": bool(re.search(r"\b(?:loneliness|lonely|alone|isolat|disconnected|belonging|connection)\b", q)),
        "grief": bool(re.search(r"\b(?:grief|grieving|bereavement|bereaved|loss|death|died|dying|loved one)\b", q)),
        "risk": bool(re.search(r"\b(?:suicid|self-harm|overdose|abuse|coercion|immediate danger|unsafe|threatened)\b", q)),
        "meaning": bool(re.search(r"\b(?:meaning|understanding|perspective|wisdom|why|purpose|identity|continuity|spiritual|afterlife|belief|loneliness|lonely|despair|emptiness)\b", q)),
        "transition": bool(re.search(r"\b(?:crossroads|major change|change in my life|life transition|transition|new chapter|what comes next|what happens next|starting over|beginning again|moving forward|identity shift|uncertain what comes next)\b", q)),
        "explicit_framework": bool(re.search(r"\b(?:spiritual|spirituality|religious|religion|mystical|mysticism|afterlife|reincarnation|soul|astrology|tarot|starseed)\b", q)),
    }


def _role_evidence(doc: dict) -> dict:
    text = re.sub(r"\s+", " ", str(doc.get("text") or "").strip().casefold())
    title = _normalize_title(doc.get("title") or "").casefold()
    return {
        "direct_loneliness": bool(re.search(r"\b(?:loneliness|lonely|social isolation|socially isolated|feeling alone|sense of aloneness|disconnected|disconnection|belonging|lack of connection|need for connection|being seen|being understood)\b", text)),
        "belonging_connection": bool(re.search(r"\b(?:belonging|connection|connected|relationship|relationships|community|companionship|being seen|being understood|social connection)\b", text)),
        "lived_experience": bool(re.search(r"\b(?:experience|lived|personal|human|everyday|relationships|routine|role|journey|navigate|navigating|felt|feeling|living with)\b", text)),
        "meaning": bool(re.search(r"\b(?:meaning|purpose|wisdom|perspective|understanding|sense-making|make sense|interpretation)\b", text)),
        "grounded": bool(re.search(r"\b(?:science|scientific|research|psychological|clinical|neuroscientific|evidence|empirical)\b", text)),
        "worldview": bool(re.search(r"\b(?:spiritual|spirituality|religious|religion|mystical|mysticism|afterlife|reincarnation|soul|sacred|transcenden|starseed)\b", text)),
        "transition": bool(re.search(r"\b(?:transition|crossroads|change|new chapter|starting over|moving forward|turning point|reorientation|uncertainty|in-between|before and after|rebuild|reorient|adapt)\b", text)),
        "practical_reflection": bool(re.search(r"\b(?:reflect|reflection|notice|naming|journal|practice|grounding|orientation|practical|everyday|attention)\b", text)),
        "acute_risk": bool(re.search(r"\b(?:suicid(?:e|al|ality)|suicidal ideation|self-harm|overdose|acute crisis|crisis intervention|immediate danger)\b", text)),
        "title_risk": bool(re.search(r"\b(?:suicide|suicidal|self-harm|overdose|crisis intervention|acute crisis)\b", title)),
        "title_loneliness": bool(re.search(r"\b(?:loneliness|lonely|alone|belonging|connection|connected|isolation|isolated)\b", title)),
        "title_meaning": bool(re.search(r"\b(?:meaning|purpose|perspective|wisdom|understanding|journey|soul|life)\b", title)),
    }


def _is_risk_related(doc: dict) -> bool:
    evidence = _role_evidence(doc)
    return evidence["acute_risk"] or evidence["title_risk"]


def _loneliness_primary_score(doc: dict, profile: dict) -> int:
    evidence = _role_evidence(doc)
    if _is_risk_related(doc) and not profile.get("risk"):
        return -10_000
    score = 95 * int(evidence["title_loneliness"])
    score += 70 * int(evidence["direct_loneliness"])
    score += 22 * int(evidence["belonging_connection"])
    score += 18 * int(evidence["lived_experience"])
    score += 8 * int(evidence["meaning"])
    score += 5 * int(evidence["practical_reflection"])
    score += 3 * int(evidence["grounded"])
    if evidence["worldview"] and not profile.get("explicit_framework"):
        score -= 40
    if not profile.get("explicit_framework") and re.search(r"\b(?:starseed|afterlife|reincarnation|higher-order intelligence)\b", _normalize_title(doc.get("title") or "") + " " + str(doc.get("text") or ""), re.I):
        score -= 45
    if evidence["title_loneliness"] and evidence["direct_loneliness"]:
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


def _secondary_roles(doc: dict):
    evidence = _role_evidence(doc)
    if evidence["acute_risk"] or evidence["title_risk"] or evidence["direct_loneliness"]:
        return []
    roles = []
    if evidence["grounded"]:
        roles.append(("grounded", "a grounded or research-oriented route into the experience", 26))
    if evidence["meaning"]:
        roles.append(("meaning", "a route into meaning, perspective, and ways of understanding loneliness", 25))
    if evidence["transition"]:
        roles.append(("transition", "a route into change, uncertainty, and reorientation", 23))
    if evidence["practical_reflection"]:
        roles.append(("reflection", "a reflective route into staying with the experience", 20))
    if evidence["belonging_connection"]:
        roles.append(("belonging", "a route into connection and belonging", 18))
    if evidence["title_meaning"]:
        roles.append(("meaning_title", "a broader route into meaning and perspective", 15))
    return roles


def _secondary_quality(doc: dict) -> int:
    evidence = _role_evidence(doc)
    quality = 0
    quality += 20 * int(evidence["grounded"])
    quality += 20 * int(evidence["meaning"])
    quality += 12 * int(evidence["lived_experience"])
    quality += 10 * int(evidence["practical_reflection"])
    quality += 10 * int(evidence["transition"])
    quality += 8 * int(evidence["title_meaning"])
    quality -= 12 * int(evidence["worldview"])
    if _is_risk_related(doc):
        quality -= 100
    return quality


def _secondary_role_quality(doc: dict, role_key: str) -> int:
    evidence = _role_evidence(doc)
    text = re.sub(r"\s+", " ", str(doc.get("text") or "").strip().casefold())
    score = _secondary_quality(doc)
    if role_key in {"meaning", "meaning_title"}:
        score += 12 * int(evidence["meaning"])
        score += 8 * int(evidence["lived_experience"])
    elif role_key == "grounded":
        score += 12 * int(evidence["grounded"])
        score += 8 * int(evidence["lived_experience"])
    elif role_key == "transition":
        score += 12 * int(evidence["transition"])
    elif role_key == "reflection":
        score += 12 * int(evidence["practical_reflection"])
    elif role_key == "belonging":
        score += 12 * int(evidence["belonging_connection"])
    if re.search(r"\b(?:recommend|should|must|need to|therapy|treatment|diagnos)\b", text):
        score -= 15
    return score


def _select_loneliness_secondaries(docs, primary_title, profile, limit=2):
    seen = {_normalize_title(primary_title).casefold()}
    candidates = []
    for index, doc in enumerate(docs):
        title = _normalize_title(doc.get("title") or "")
        if not title or title.casefold() in seen:
            continue
        if not profile.get("explicit_framework") and re.search(r"\b(?:starseed|afterlife|reincarnation|higher-order intelligence)\b", title + " " + str(doc.get("text") or ""), re.I):
            continue
        quality = _secondary_quality(doc)
        if quality < 18:
            continue
        for role_key, role_text, role_score in _secondary_roles(doc):
            role_quality = _secondary_role_quality(doc, role_key)
            if role_quality < 28:
                continue
            candidates.append((role_quality + role_score, index, role_key, role_text, doc))
    candidates.sort(key=lambda item: (-item[0], item[1]))
    selected, role_keys, title_keys = [], set(), set()
    for score, index, role_key, role_text, doc in candidates:
        title_key = _normalize_title(doc.get("title") or "").casefold()
        if role_key in role_keys or title_key in title_keys:
            continue
        role_keys.add(role_key)
        title_keys.add(title_key)
        selected.append({"doc": doc, "role_key": role_key, "role_text": role_text, "score": score})
        if len(selected) >= limit:
            break
    return selected


def _evidence_boundary_note(docs):
    has_science = any(re.search(r"\b(?:scientific|science|psychological|neuroscientific|clinical|research)\b", str(doc.get("text") or ""), re.I) for doc in docs)
    has_spiritual = any(re.search(r"\b(?:spiritual|soul|afterlife|religious|mystical|sacred|transcenden)\b", str(doc.get("text") or ""), re.I) for doc in docs)
    if has_science and has_spiritual:
        return "The Archive holds different ways of understanding loneliness without requiring them to become one certainty."
    if has_spiritual:
        return "Where the material turns toward spiritual or afterlife possibilities, those are perspectives offered by the work rather than established facts you need to accept."
    return "The material can open a way into the question without deciding in advance what loneliness must mean."


def _build_loneliness_answer(user_query, primary, docs):
    title = _normalize_title(primary.get("title") or "")
    url = str(primary.get("url") or primary.get("canonical_url") or "").strip()
    if not title or not re.match(r"^https?://\S+$", url, re.I):
        return ""
    profile = _query_profile(user_query)
    secondaries = _select_loneliness_secondaries(docs, title, profile)
    sections = [
        "Loneliness can be difficult to name because it is not always only about being physically alone. It can touch belonging, connection, meaning, and the sense of being seen or understood.",
        f"A gentle place to begin is [{title}]({url}).",
        _evidence_boundary_note(docs),
    ]
    if secondaries:
        role_sentences = [
            f"[{_normalize_title(item['doc'].get('title') or '')}]({str(item['doc'].get('url') or item['doc'].get('canonical_url') or '').strip()}) — {item['role_text']}."
            for item in secondaries
        ]
        sections.append("From there, the Archive opens a few different ways into the question:\n\n" + "\n\n".join(role_sentences))
    sections.append("You do not have to turn loneliness into a diagnosis or a final explanation. A useful piece can simply give you another language for noticing what the experience is asking you to consider.")
    return "\n\n".join(sections)


def _v408_finalize(*args, **kwargs):
    user_query = _extract_user_query(args, kwargs)
    intent = _extract_intent(args, kwargs)
    raw_context = _context_blocks_from_kwargs(args, kwargs)
    docs = _parse_context_documents(raw_context)
    profile = _query_profile(user_query)
    recommendation_question = False
    try:
        recommendation_question = bool(use_core._is_recommendation_question(user_query)) if user_query else False
    except Exception:
        recommendation_question = False
    print(f"USE v408 runtime hook: query_present={bool(user_query)}, intent={intent!r}, docs={len(docs)}, recommendation={recommendation_question}, profile={profile}, args={len(args)}, kwargs={sorted(kwargs.keys())}")
    if user_query and profile.get("loneliness") and not profile.get("risk"):
        primary = _select_loneliness_primary(docs, profile)
        if primary:
            answer = _build_loneliness_answer(user_query, primary, docs)
            if answer:
                secondaries = _select_loneliness_secondaries(docs, _normalize_title(primary.get('title') or ''), profile)
                print(f"USE v408 runtime hook: loneliness interception=ACTIVE primary='{_normalize_title(primary.get('title') or '')}' secondary_count={len(secondaries)} recommendation_classifier={recommendation_question}")
                return answer
    return _original_generate_llm_response(*args, **kwargs)


app = use_core.app
app.title = f"Find Your Way (USE) Navigation Engine {APP_VERSION}"
print(f"USE v408 GUIDE BUILD IDENTITY: build_id={CANONICAL_BUILD_ID}, version={APP_VERSION}, fingerprint={DEPLOYMENT_FINGERPRINT}, source_sha256={RUNTIME_SOURCE_SHA256}, core_blob_sha256={_core_runtime_sha}")
use_core.APP_VERSION = APP_VERSION
use_core.DEPLOYMENT_FINGERPRINT = DEPLOYMENT_FINGERPRINT
use_core.CANONICAL_BUILD_ID = CANONICAL_BUILD_ID
use_core.RUNTIME_SOURCE_SHA256 = RUNTIME_SOURCE_SHA256
use_core.EXPECTED_CORE_BLOB_SHA = EXPECTED_CORE_BLOB_SHA
use_core.generate_llm_response = _v408_finalize
