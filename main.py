# USE PRODUCTION VERSION: v429 — risk path routing
import hashlib
import importlib
import re
from pathlib import Path

APP_VERSION = "v429"
DEPLOYMENT_FINGERPRINT = "USE-v429-risk-path-routing"
CANONICAL_BUILD_ID = "USE-BUILD-v429-risk-path-routing"
EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"

_MAIN_PATH = Path(__file__).resolve()
_CORE_PATH = _MAIN_PATH.with_name("use_core.py")
RUNTIME_SOURCE_SHA256 = hashlib.sha256(_MAIN_PATH.read_bytes()).hexdigest()
if not _CORE_PATH.exists():
    raise RuntimeError("USE v429 package integrity failure: use_core.py is missing.")
_core_bytes = _CORE_PATH.read_bytes()
_core_runtime_sha = hashlib.sha1(f"blob {len(_core_bytes)}\0".encode() + _core_bytes).hexdigest()
if _core_runtime_sha != EXPECTED_CORE_BLOB_SHA:
    raise RuntimeError(f"USE v429 package integrity failure: expected protected core blob sha={EXPECTED_CORE_BLOB_SHA}, actual={_core_runtime_sha}")

use_core = importlib.import_module("use_core")
_original_generate_llm_response = use_core.generate_llm_response
_original_fetch_canonical_context = use_core.fetch_canonical_context


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
        "meaning": bool(re.search(r"\b(?:meaning|purpose|point of life|what gives life meaning|why am i here|lost about what gives life meaning|sense of purpose)\b", q)),
        "grief": bool(re.search(r"\b(?:grief|grieving|grieve|mourning|bereaved|bereavement|death of (?:a|my|their|the) (?:loved one|partner|spouse|friend|parent|child)|lost (?:a|my|their|the) (?:loved one|partner|spouse|friend|parent|child))\b", q)),
        "risk": bool(re.search(r"\b(?:suicid|self-harm|overdose|abuse|coercion|immediate danger|unsafe|threatened)\b", q)),
        "explicit_framework": bool(re.search(r"\b(?:spiritual|spirituality|religious|religion|mystical|mysticism|afterlife|reincarnation|soul|astrology|tarot|starseed)\b", q)),
    }


def _build_risk_answer():
    return (
        "If you are thinking about killing yourself or may be in immediate danger, please treat this as something that needs human help now. "
        "Call emergency services or go to the nearest emergency department, and if you can, stay with another person while you get help. "
        "You do not need to work out the larger meaning of what you are going through before taking that next step."
    )


def _risk_guarded_fetch_canonical_context(user_query: str):
    """Terminate the canonical evidence path for explicit acute-risk queries."""
    if _query_profile(user_query).get("risk"):
        return {
            "intent": "RISK_ROUTING",
            "orientational_frame": {},
            "context_blocks": "",
            "canonical_link_context": "",
            "risk_route_required": True,
        }
    return _original_fetch_canonical_context(user_query)


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
        "title_meaning": bool(re.search(r"\b(?:meaning|purpose|life|consciousness|journey|understanding|perspective|wisdom)\b", title)),
        "title_grief": bool(re.search(r"\b(?:grief|grieving|mourning|bereavement|loss|death|dying|dying well)\b", title)),
        "continuity": bool(re.search(r"\b(?:continuity|connection beyond death|afterlife|legacy|what may endure|endure|transcenden)\b", corpus)),
        "grief_lived": bool(re.search(r"\b(?:grief|grieving|mourning|loss|bereavement|bereaved|companion|comfort|sorrow|lament|heart|heartbreak)\b", corpus)),
    }


def _is_risk_related(doc: dict) -> bool:
    e = _role_evidence(doc)
    return e["acute_risk"] or e["title_risk"]


def _select_loneliness_primary(docs, profile):
    ranked = []
    for index, doc in enumerate(docs):
        title = _normalize_title(doc.get("title") or "")
        url = str(doc.get("url") or doc.get("canonical_url") or "").strip()
        if not title or not re.match(r"^https?://\S+$", url, re.I):
            continue
        e = _role_evidence(doc)
        if _is_risk_related(doc) and not profile.get("risk"):
            continue
        score = 100 * int(e["title_loneliness"])
        score += 75 * int(e["direct_loneliness"])
        score += 22 * int(e["belonging_connection"])
        score += 18 * int(e["lived_experience"])
        score += 8 * int(e["meaning"])
        score += 5 * int(e["grounded"])
        if e["worldview"] and not profile.get("explicit_framework"):
            score -= 40
        ranked.append((score, index, doc))
    ranked = [item for item in ranked if item[0] > 0]
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return ranked[0][2] if ranked else None


def _select_meaning_primary(docs, profile):
    ranked = []
    for index, doc in enumerate(docs):
        title = _normalize_title(doc.get("title") or "")
        url = str(doc.get("url") or doc.get("canonical_url") or "").strip()
        if not title or not re.match(r"^https?://\S+$", url, re.I):
            continue
        e = _role_evidence(doc)
        if _is_risk_related(doc):
            continue
        score = 100 * int(e["title_meaning"])
        score += 25 * int(e["meaning"])
        score += 18 * int(e["lived_experience"])
        score += 12 * int(e["grounded"])
        score += 10 * int(e["practical_reflection"])
        if e["worldview"] and not profile.get("explicit_framework"):
            score -= 90
        if e["title_meaning"] and e["worldview"] and not profile.get("explicit_framework"):
            score -= 60
        ranked.append((score, index, doc))
    ranked = [item for item in ranked if item[0] > 0]
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return ranked[0][2] if ranked else None


def _select_grief_primary(docs, profile):
    ranked = []
    for index, doc in enumerate(docs):
        title = _normalize_title(doc.get("title") or "")
        url = str(doc.get("url") or doc.get("canonical_url") or "").strip()
        if not title or not re.match(r"^https?://\S+$", url, re.I):
            continue
        e = _role_evidence(doc)
        if _is_risk_related(doc) and not profile.get("risk"):
            continue
        score = 100 * int(e["title_grief"])
        score += 55 * int(e["grief_lived"])
        score += 18 * int(e["meaning"])
        score += 12 * int(e["lived_experience"])
        score += 10 * int(e["practical_reflection"])
        if e["worldview"] and not profile.get("explicit_framework"):
            score -= 65
        ranked.append((score, index, doc))
    ranked = [item for item in ranked if item[0] > 0]
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return ranked[0][2] if ranked else None


def _select_grief_secondaries(user_query: str, docs, primary):
    if not docs or not primary:
        return []
    primary_key = str(primary.get("url") or primary.get("canonical_url") or _normalize_title(primary.get("title") or "")).strip().casefold()
    selector = getattr(use_core, "_select_complementary_generation_evidence", None)
    if not callable(selector):
        return []
    try:
        candidate = selector(docs, user_query)
    except Exception:
        return []
    if isinstance(candidate, dict):
        candidate = list(candidate.values()) if all(isinstance(v, dict) for v in candidate.values()) else []
    if not isinstance(candidate, list):
        return []
    scored = []
    for index, doc in enumerate(candidate):
        if not isinstance(doc, dict):
            continue
        key = str(doc.get("url") or doc.get("canonical_url") or _normalize_title(doc.get("title") or "")).strip().casefold()
        if not key or key == primary_key or _is_risk_related(doc):
            continue
        e = _role_evidence(doc)
        score = 25 * int(e["continuity"])
        score += 20 * int(e["meaning"])
        score += 14 * int(e["lived_experience"])
        score += 10 * int(e["practical_reflection"])
        score -= 20 * int(e["worldview"])
        scored.append((score, index, doc))
    scored.sort(key=lambda item: (-item[0], item[1]))
    if not scored:
        return []
    return [scored[0][2]]


def _grief_secondary_role_text(doc: dict) -> str:
    e = _role_evidence(doc)
    if e["continuity"]:
        return "a route into continuity, connection, and questions about what may endure"
    if e["meaning"] and e["practical_reflection"]:
        return "a reflective route into meaning and the experience of living with loss"
    if e["meaning"]:
        return "a route into meaning and ways of understanding loss"
    if e["lived_experience"]:
        return "a route into the lived human experience of grief and loss"
    return "a complementary route into the experience"


def _build_grief_answer(user_query, primary, docs):
    title = _normalize_title(primary.get("title") or "")
    url = str(primary.get("url") or primary.get("canonical_url") or "").strip()
    if not title or not re.match(r"^https?://\S+$", url, re.I):
        return ""
    secondaries = _select_grief_secondaries(user_query, docs, primary)
    sections = [
        "When you are grieving, it can be hard to know what to reach for first, especially when the loss is still close. You do not have to make sense of it all at once.",
        f"A gentle place to begin is [{title}]({url}). This piece can give you some room to stay with the experience before asking what it might mean.",
    ]
    if secondaries:
        item = secondaries[0]
        item_title = _normalize_title(item.get("title") or "")
        item_url = str(item.get("url") or item.get("canonical_url") or "").strip()
        sections.append("The Archive holds different ways of approaching grief, and they do not all ask you to understand the loss in the same way.")
        sections.append(f"Another route into the question is [{item_title}]({item_url}): {_grief_secondary_role_text(item)}.")
    else:
        sections.append("The material can offer a place to begin without requiring one final explanation of what the loss means.")
    sections.append("You can stay with whichever piece feels most useful for where you are today. There is no need to settle the grief all at once.")
    return "\n\n".join(sections)


def _secondary_role_text(doc: dict) -> str:
    e = _role_evidence(doc)
    if e["grounded"] and e["meaning"]:
        return "a grounded route into meaning and perspective, without requiring a single explanation"
    if e["grounded"]:
        return "a grounded or research-oriented route into the experience"
    if e["meaning"] and e["belonging_connection"]:
        return "a route into meaning, connection, and ways of understanding the experience"
    if e["meaning"]:
        return "a route into meaning, purpose, and ways of understanding the experience"
    if e["lived_experience"]:
        return "a route into the lived human dimensions surrounding the question"
    return "a complementary perspective on the question"


def _canonical_complementary_roles(user_query: str, docs, primary):
    if not docs or not primary:
        return []
    primary_key = str(primary.get("url") or primary.get("canonical_url") or _normalize_title(primary.get("title") or "")).strip().casefold()
    selector = getattr(use_core, "_select_complementary_generation_evidence", None)
    if not callable(selector):
        return []
    try:
        candidate = selector(docs, user_query)
    except Exception:
        return []
    if isinstance(candidate, dict):
        candidate = list(candidate.values()) if all(isinstance(v, dict) for v in candidate.values()) else []
    if not isinstance(candidate, list):
        return []
    result = []
    for doc in candidate:
        if not isinstance(doc, dict):
            continue
        key = str(doc.get("url") or doc.get("canonical_url") or _normalize_title(doc.get("title") or "")).strip().casefold()
        if not key or key == primary_key or _is_risk_related(doc):
            continue
        result.append({"doc": doc, "role_text": _secondary_role_text(doc)})
        break
    return result


def _build_loneliness_answer(user_query, primary, docs):
    title = _normalize_title(primary.get("title") or "")
    url = str(primary.get("url") or primary.get("canonical_url") or "").strip()
    if not title or not re.match(r"^https?://\S+$", url, re.I):
        return ""
    secondaries = _canonical_complementary_roles(user_query, docs, primary)
    sections = [
        "Loneliness can be difficult to name because it is not always only about being physically alone. It can touch belonging, connection, meaning, and the sense of being seen or understood.",
        f"A gentle place to begin is [{title}]({url}).",
    ]
    if secondaries:
        item = secondaries[0]
        doc = item["doc"]
        item_title = _normalize_title(doc.get("title") or "")
        item_url = str(doc.get("url") or doc.get("canonical_url") or "").strip()
        sections.append("The Archive offers more than one way into the question, and the routes do different work rather than resolving it into one certainty.")
        sections.append(f"Another route into the question is [{item_title}]({item_url}): {item['role_text']}.")
    else:
        sections.append("The material can open a way into the question without deciding in advance what loneliness must mean.")
    sections.append("You do not have to turn loneliness into a diagnosis or a final explanation. A useful piece can simply give you another language for noticing what the experience is asking you to consider.")
    return "\n\n".join(sections)


def _build_meaning_answer(user_query, primary, docs):
    title = _normalize_title(primary.get("title") or "")
    url = str(primary.get("url") or primary.get("canonical_url") or "").strip()
    if not title or not re.match(r"^https?://\S+$", url, re.I):
        return ""
    secondaries = _canonical_complementary_roles(user_query, docs, primary)
    sections = [
        "Sometimes it is hard to know what gives life meaning, especially when an answer that once felt clear no longer does. You do not have to solve that question all at once.",
        f"A useful place to begin is [{title}]({url}). It can give you a way into the question without asking you to settle it before you have had time to explore it.",
    ]
    if secondaries:
        item = secondaries[0]
        doc = item["doc"]
        item_title = _normalize_title(doc.get("title") or "")
        item_url = str(doc.get("url") or doc.get("canonical_url") or "").strip()
        sections.append("The Archive contains different ways of approaching meaning; they do not all make the same claim about what a meaningful life is.")
        sections.append(f"Another route into the question is [{item_title}]({item_url}): {item['role_text']}.")
    else:
        sections.append("The material can offer a way into the question without requiring you to adopt one worldview as the answer.")
    sections.append("You can take the first piece as a place to reflect and see what resonates, rather than as a final explanation of what gives life meaning.")
    return "\n\n".join(sections)


def _v429_finalize(*args, **kwargs):
    user_query = _extract_user_query(args, kwargs)
    profile = _query_profile(user_query)
    if profile.get("risk"):
        return _build_risk_answer()
    raw_context = _context_blocks_from_kwargs(args, kwargs)
    docs = _parse_context_documents(raw_context)
    if user_query and profile.get("loneliness"):
        primary = _select_loneliness_primary(docs, profile)
        if primary:
            answer = _build_loneliness_answer(user_query, primary, docs)
            if answer:
                return answer
    if user_query and profile.get("meaning") and not profile.get("explicit_framework"):
        primary = _select_meaning_primary(docs, profile)
        if primary:
            answer = _build_meaning_answer(user_query, primary, docs)
            if answer:
                return answer
    if user_query and profile.get("grief"):
        primary = _select_grief_primary(docs, profile)
        if primary:
            answer = _build_grief_answer(user_query, primary, docs)
            if answer:
                return answer
    return _original_generate_llm_response(*args, **kwargs)


app = use_core.app
app.title = f"Find Your Way (USE) Navigation Engine {APP_VERSION}"
print(f"USE v429 GUIDE BUILD IDENTITY: build_id={CANONICAL_BUILD_ID}, version={APP_VERSION}, fingerprint={DEPLOYMENT_FINGERPRINT}, source_sha256={RUNTIME_SOURCE_SHA256}, core_blob_sha256={_core_runtime_sha}")
use_core.APP_VERSION = APP_VERSION
use_core.DEPLOYMENT_FINGERPRINT = DEPLOYMENT_FINGERPRINT
use_core.CANONICAL_BUILD_ID = CANONICAL_BUILD_ID
use_core.RUNTIME_SOURCE_SHA256 = RUNTIME_SOURCE_SHA256
use_core.EXPECTED_CORE_BLOB_SHA = EXPECTED_CORE_BLOB_SHA
use_core.fetch_canonical_context = _risk_guarded_fetch_canonical_context
use_core.generate_llm_response = _v429_finalize
