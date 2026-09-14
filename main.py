# USE PRODUCTION VERSION: v439 — secondary pathway URL integrity
import hashlib
import importlib
import re
from pathlib import Path

APP_VERSION = "v439"
DEPLOYMENT_FINGERPRINT = "USE-v439-secondary-pathway-url-integrity"
CANONICAL_BUILD_ID = "USE-BUILD-v439-secondary-pathway-url-integrity"
EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"

_MAIN_PATH = Path(__file__).resolve()
_CORE_PATH = _MAIN_PATH.with_name("use_core.py")
RUNTIME_SOURCE_SHA256 = hashlib.sha256(_MAIN_PATH.read_bytes()).hexdigest()
if not _CORE_PATH.exists():
    raise RuntimeError("USE v439 package integrity failure: use_core.py is missing.")
_core_bytes = _CORE_PATH.read_bytes()
_core_runtime_sha = hashlib.sha1(f"blob {len(_core_bytes)}\0".encode() + _core_bytes).hexdigest()
if _core_runtime_sha != EXPECTED_CORE_BLOB_SHA:
    raise RuntimeError(f"USE v439 package integrity failure: expected protected core blob sha={EXPECTED_CORE_BLOB_SHA}, actual={_core_runtime_sha}")

use_core = importlib.import_module("use_core")
_original_generate_llm_response = use_core.generate_llm_response
_original_handle_query = getattr(use_core, "handle_query", None)
if _original_handle_query is None:
    raise RuntimeError("USE v439 package integrity failure: API query handler is unavailable.")


def _query_profile(user_query: str) -> dict:
    q = re.sub(r"\s+", " ", str(user_query or "").strip().casefold())
    return {
        "loneliness": bool(re.search(r"\b(?:loneliness|lonely|alone|isolat|disconnected|belonging|connection)\b", q)),
        "risk": bool(re.search(r"\b(?:suicid\w*|self-harm|self harm|overdose|abuse|coercion|immediate danger|unsafe|threatened|kill(?:ing)? myself|kill(?:ing)? yourself|want(?:ing)? to die|don't want to (?:live|be here)|do not want to (?:live|be here)|end my life|take my own life|harm myself|hurt myself|better off dead|wish I were dead)\b", q)),
        "meaning_open": bool(re.search(r"\b(?:what gives life meaning|meaning in life|what makes life meaningful|what matters|purpose|larger meaning|meaning behind)\b", q)) and bool(re.search(r"\b(?:lost|not sure|don't know|do not know|uncertain|explore|exploring|where might i begin|where should i begin|going through|believe|belief|what to believe)\b", q)),
        "transition_open": bool(re.search(r"\b(?:old way|no longer works|what comes next|next chapter|different way of seeing|way of seeing.*no longer|transition|turning point|threshold|outgrown|outgrew|no longer feels like me|changed so much|life has changed|change it|changing|what no longer fits|what no longer feels right|built.*afraid.*lose|afraid.*lose.*change|move on|moving on|new chapter|leave.*behind|letting go|rebuild|starting over|reinvent)\b", q)) and bool(re.search(r"\b(?:life|my life|what comes next|think|explore|help|built|change|changed|fits|right|lose|leaving|starting|begin|next)\b", q)),
        "grief": bool(re.search(r"\b(?:griev\w*|grief|mourning|death of (?:a|my|their) (?:love|loved) one|loss of (?:a|my|their) (?:love|loved) one|someone (?:i|we|they) love(?:d)? died)\b", q)),
    }


def _build_risk_answer(user_query: str = "") -> str:
    q = str(user_query or "").casefold()
    if re.search(r"\b(?:suicid\w*|self-harm|self harm|kill(?:ing)? myself|kill(?:ing)? yourself|want(?:ing)? to die|don't want to (?:live|be here)|do not want to (?:live|be here)|end my life|take my own life|harm myself|hurt myself|better off dead|wish I were dead)\b", q):
        return ("If you are thinking about killing yourself or may act on thoughts of self-harm, please treat this as something that needs human help now. "
                "Call emergency services or go to the nearest emergency department, and if you can, stay with another person while you get help. "
                "You do not need to work out the larger meaning of what you are going through before taking that next step.")
    if re.search(r"\b(?:abuse|coercion|threatened|unsafe)\b", q):
        return ("If someone is threatening, abusing, or coercing you, or you are not safe where you are, prioritize getting to a safer place and contacting a trusted person or local emergency service now. "
                "You do not need to settle the larger meaning of the situation before taking a step toward safety.")
    return ("If you may be in immediate danger or cannot keep yourself safe, please seek human help now. "
            "Call emergency services or go to the nearest emergency department, and if you can, stay with another person while you get help.")


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
        "worldview": bool(re.search(r"\b(?:spiritual|spirituality|religious|religion|mystical|mysticism|afterlife|reincarnation|soul|sacred|transcenden|starseed|higher-order intelligence|metaphysics|cosmic curriculum|universe|cosmic)\b", corpus)),
        "threshold": bool(re.search(r"\b(?:threshold|transition|turning point|old way|new way|change|chapter|uncertain|beginning|ending|liminal|crossroads|outgrown|outgrew|letting go|starting over|reinvent)\b", corpus)),
        "acute_risk": bool(re.search(r"\b(?:suicid(?:e|al|ality)|suicidal ideation|self-harm|overdose|acute crisis|crisis intervention|immediate danger)\b", corpus)),
        "title_risk": bool(re.search(r"\b(?:suicide|suicidal|self-harm|overdose|crisis intervention|acute crisis)\b", title)),
        "title_loneliness": bool(re.search(r"\b(?:loneliness|lonely|alone|belonging|connection|connected|isolation|isolated)\b", title)),
        "grief": bool(re.search(r"\b(?:grief|grieving|loss|mourning|death|bereavement|dying|meaning after loss)\b", corpus)),
        "continuity": bool(re.search(r"\b(?:continuity|connection|endure|afterlife|what may endure|what remains)\b", corpus)),
        "existential_loneliness": bool(re.search(r"\b(?:loneliness|lonely|emptiness|isolation|isolated|alone|existential)\b", corpus)),
        "practical_reflection": bool(re.search(r"\b(?:reflection|reflective|journal|journaling|practice|practical|questions to consider|what matters|how to live|daily life|everyday)\b", corpus)),
    }


def _is_risk_related(doc: dict) -> bool:
    e = _role_evidence(doc)
    return e["acute_risk"] or e["title_risk"]


def _select_grief_primary(docs):
    ranked = []
    for index, doc in enumerate(docs):
        title = _normalize_title(doc.get("title") or "")
        url = str(doc.get("url") or doc.get("canonical_url") or "").strip()
        if not title or not re.match(r"^https?://\S+$", url, re.I):
            continue
        e = _role_evidence(doc)
        if _is_risk_related(doc):
            continue
        score = 120 * int(bool(re.search(r"\b(?:grief|loss|mourning|bereavement)\b", title.casefold()))) + 35 * int(e["grief"]) + 18 * int(e["meaning"]) + 12 * int(e["lived_experience"]) + 8 * int(e["grounded"])
        if e["worldview"]:
            score -= 4
        ranked.append((score, index, doc))
    ranked = [item for item in ranked if item[0] > 0]
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return ranked[0][2] if ranked else None


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
        score = 100 * int(e["title_loneliness"]) + 75 * int(e["direct_loneliness"]) + 22 * int(e["belonging_connection"]) + 18 * int(e["lived_experience"]) + 8 * int(e["meaning"]) + 5 * int(e["grounded"])
        if e["worldview"]:
            score -= 40
        ranked.append((score, index, doc))
    ranked = [item for item in ranked if item[0] > 0]
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return ranked[0][2] if ranked else None


def _select_meaning_primary(docs):
    candidates = []
    for index, doc in enumerate(docs):
        title = _normalize_title(doc.get("title") or "")
        url = str(doc.get("url") or doc.get("canonical_url") or "").strip()
        text = re.sub(r"\s+", " ", str(doc.get("text") or "").strip()).casefold()
        if not title or not re.match(r"^https?://\S+$", url, re.I):
            continue
        e = _role_evidence(doc)
        score = 12 * int(e["meaning"]) + 10 * int(e["grounded"]) + 8 * int(e["lived_experience"]) + 5 * int(bool(re.search(r"\b(?:purpose|meaningful|existential|existence|identity)\b", text)))
        if e["worldview"]:
            score -= 10
        candidates.append((score, index, doc))
    candidates = [item for item in candidates if item[0] > 0]
    candidates.sort(key=lambda item: (-item[0], item[1]))
    return candidates[0][2] if candidates else None


def _select_transition_primary(docs):
    candidates = []
    for index, doc in enumerate(docs):
        title = _normalize_title(doc.get("title") or "")
        url = str(doc.get("url") or doc.get("canonical_url") or "").strip()
        if not title or not re.match(r"^https?://\S+$", url, re.I):
            continue
        e = _role_evidence(doc)
        score = 18 * int(e["threshold"]) + 8 * int(e["lived_experience"]) + 6 * int(e["meaning"]) + 4 * int(bool(re.search(r"\b(?:transition|threshold|liminal|crossroads|turning point|change|outgrown|letting go|starting over|reinvent)\b", f"{title} {doc.get('text') or ''}", re.I)))
        if e["worldview"]:
            score -= 8
        if score > 0:
            candidates.append((score, index, doc))
    candidates.sort(key=lambda item: (-item[0], item[1]))
    return candidates[0][2] if candidates else None


def _doc_identity(doc: dict) -> str:
    return str(doc.get("url") or doc.get("canonical_url") or "").strip()


def _valid_doc_url(doc: dict) -> str:
    url = _doc_identity(doc)
    return url if re.match(r"^https://\S+$", url, re.I) else ""


def _canonical_complementary_roles(user_query: str, docs, primary):
    if not docs or not primary:
        return []
    primary_key = _doc_identity(primary).casefold()
    selector = getattr(use_core, "_select_complementary_generation_evidence", None)
    if not callable(selector):
        return []
    try:
        candidate = selector(docs, user_query, protected_documents=[])
    except Exception:
        return []
    if isinstance(candidate, dict):
        candidate = list(candidate.values()) if all(isinstance(v, dict) for v in candidate.values()) else []
    if not isinstance(candidate, list):
        return []
    valid = []
    for doc in candidate:
        if not isinstance(doc, dict) or _is_risk_related(doc):
            continue
        if not _valid_doc_url(doc):
            continue
        if _doc_identity(doc).casefold() == primary_key:
            continue
        valid.append(doc)
    return valid


def _complementary_role(doc: dict, primary_role: str):
    e = _role_evidence(doc)
    title_text = f"{doc.get('title') or ''} {doc.get('text') or ''}"
    if re.search(r"\b(?:starseed|higher-order intelligence|metaphysics|afterlife|reincarnation)\b", title_text, re.I) and primary_role != "explicit_framework":
        return None, None, -999
    if primary_role == "transition":
        if e["meaning"] and not e["worldview"]:
            return "meaning", "meaning, perspective, and ways of understanding what the transition may open", 18 + 3 * int(e["practical_reflection"])
        if e["grounded"]:
            return "grounded", "a grounded or research-oriented route into change", 16
        if e["continuity"]:
            return "continuity", "continuity, identity, and what remains connected through change", 15
        if e["practical_reflection"]:
            return "reflection", "staying with uncertainty and noticing what matters", 13
        return None, None, -999
    if primary_role == "grief":
        if e["continuity"]:
            return "continuity", "continuity, connection, and what may endure", 18
        if e["existential_loneliness"]:
            return "existential_loneliness", "loneliness, emptiness, and existential dimensions of loss", 15
        if e["meaning"]:
            return "meaning", "meaning, perspective, and ways of understanding loss", 13
        return None, None, -999
    if e["meaning"] and not e["worldview"]:
        return "meaning", "meaning, perspective, and ways of understanding the experience", 12
    if e["grounded"]:
        return "grounded", "a grounded or research-oriented route into the question", 11
    if e["practical_reflection"]:
        return "reflection", "staying with the question through reflection and practice", 10
    return None, None, -999


def _select_secondary_pathways(user_query, primary, docs, primary_role, limit=1):
    primary_key = _doc_identity(primary).casefold()
    candidates = _canonical_complementary_roles(user_query, docs, primary)
    ranked = []
    for index, doc in enumerate(candidates):
        key = _doc_identity(doc).casefold()
        if not key or key == primary_key:
            continue
        sec_url = _valid_doc_url(doc)
        if not sec_url:
            continue
        role_key, role_text, score = _complementary_role(doc, primary_role)
        if role_key is not None and score > 0:
            ranked.append((score, index, role_key, role_text, doc))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    selected = []
    role_keys = set()
    for score, index, role_key, role_text, doc in ranked:
        if role_key in role_keys:
            continue
        role_keys.add(role_key)
        selected.append({"doc": doc, "role_key": role_key, "role_text": role_text, "score": score})
        if len(selected) >= limit:
            break
    return selected


def _foothold_text(primary_role: str) -> str:
    footholds = {
        "grief": "For now, it may be enough to stay close to what you are actually feeling and choose one small act of care today—rest, a quiet walk, a conversation with someone you trust, or simply giving yourself permission not to make sense of everything yet.",
        "transition": "For now, you might simply name what no longer fits and give yourself one small space today in which nothing has to be decided. A walk, a page of writing, or a conversation with someone you trust can be enough.",
        "meaning": "For now, you might choose one thing that still feels quietly worth caring about and give it your attention today. You do not need a complete philosophy of life before taking one meaningful step.",
        "loneliness": "For now, a gentle foothold might be one small movement toward connection—a message to someone you trust, sitting with someone, or simply naming what you wish another person could understand.",
    }
    return footholds.get(primary_role, "For now, one small, humane step is enough. You do not need to settle the larger question before taking it.")


def _build_grief_answer(user_query, primary, docs):
    title = _normalize_title(primary.get("title") or "")
    url = _valid_doc_url(primary)
    if not title or not url:
        return ""
    secondaries = _select_secondary_pathways(user_query, primary, docs, "grief", limit=1)
    parts = [
        "Grief after the death of someone you love can leave many questions open at once, and there is no need to force the experience into one meaning.",
        f"A possible place to begin is [{title}]({url}). It approaches loss through spiritual and scientific perspectives, including questions of meaning that can arise after someone dies. You can see whether that lens speaks to the grief you’re carrying.",
        _foothold_text("grief"),
    ]
    if secondaries:
        item = secondaries[0]
        doc = item["doc"]
        sec_title = _normalize_title(doc.get("title") or "")
        sec_url = _valid_doc_url(doc)
        if sec_title and sec_url:
            parts.append(f"Another route into the question is [{sec_title}]({sec_url}), offering {item['role_text']}.")
    parts.append("There is no need to settle what the loss means all at once. One piece that feels right for today can be enough of a place to begin.")
    return "\n\n".join(parts)


def _build_loneliness_answer(user_query, primary, docs):
    title = _normalize_title(primary.get("title") or "")
    url = _valid_doc_url(primary)
    if not title or not url:
        return ""
    secondaries = _canonical_complementary_roles(user_query, docs, primary)
    sections = [
        "Loneliness can be difficult to name because it is not always only about being physically alone. It can touch belonging, connection, meaning, and the sense of being seen or understood.",
        f"A gentle place to begin is [{title}]({url}).",
        _foothold_text("loneliness"),
    ]
    if secondaries:
        item = secondaries[0]
        item_title = _normalize_title(item.get("title") or "")
        item_url = _valid_doc_url(item)
        if item_title and item_url:
            sections.append("The Archive offers more than one way into the question, and the routes do different work rather than resolving it into one certainty.")
            sections.append(f"Another route into the question is [{item_title}]({item_url}).")
    else:
        sections.append("The material can open a way into the question without deciding in advance what loneliness must mean.")
    sections.append("You do not have to turn loneliness into a diagnosis or a final explanation. A useful piece can simply give you another language for noticing what the experience is asking you to consider.")
    return "\n\n".join(sections)


def _build_meaning_answer(user_query, primary, docs):
    title = _normalize_title(primary.get("title") or "")
    url = _valid_doc_url(primary)
    if not title or not url:
        return ""
    secondaries = _select_secondary_pathways(user_query, primary, docs, "meaning", limit=1)
    primary_evidence = _role_evidence(primary)
    parts = [
        "Questions about larger meaning can be deeply personal, and it is reasonable to explore them without being told what you must believe.",
        f"A possible place to begin is [{title}]({url}). This is one perspective from the Archive to consider, not a conclusion you are required to accept.",
        _foothold_text("meaning"),
    ]
    if primary_evidence["grounded"] and not primary_evidence["worldview"]:
        parts.append("Where an essay draws on established research or other evidence, you can treat those parts differently from interpretation or personal meaning.")
    elif primary_evidence["worldview"]:
        parts.append("The essay also works with spiritual or cosmological possibilities. Those belong to a worldview or interpretation presented in the Archive, rather than established fact, so you can explore them without having to adopt them.")
    if secondaries:
        item = secondaries[0]
        item_title = _normalize_title(item.get("doc", {}).get("title") or "")
        item_url = _valid_doc_url(item.get("doc", {}))
        if item_title and item_url:
            parts.append(f"Another route into the question is [{item_title}]({item_url}), offering {item['role_text']}.")
    parts.append("You can stay with the question and decide for yourself which parts feel grounded, which feel interpretive, and which may simply hold personal meaning for you.")
    return "\n\n".join(parts)


def _build_transition_answer(user_query, primary, docs):
    title = _normalize_title(primary.get("title") or "")
    url = _valid_doc_url(primary)
    if not title or not url:
        return ""
    secondaries = _select_secondary_pathways(user_query, primary, docs, "transition", limit=1)
    parts = [
        "When a life you have built no longer feels like it fits, and part of you is afraid of what change might cost, the tension itself can be worth listening to before you decide what to do.",
        f"A possible place to begin is [{title}]({url}), which offers one way of exploring transition without telling you what your experience must mean.",
        _foothold_text("transition"),
    ]
    if secondaries:
        item = secondaries[0]
        doc = item["doc"]
        sec_title = _normalize_title(doc.get("title") or "")
        sec_url = _valid_doc_url(doc)
        if sec_title and sec_url:
            parts.append(f"Another route into the question is [{sec_title}]({sec_url}), offering {item['role_text']}.")
            parts.append("You can see whether either lens speaks to the tension you’re carrying, without needing to decide whether to stay or leave, keep or let go, all at once.")
        else:
            parts.append("You can see whether this lens speaks to the tension you’re carrying, without needing to decide whether to stay or leave, keep or let go, all at once.")
    else:
        parts.append("You can see whether this lens speaks to the tension you’re carrying, without needing to decide whether to stay or leave, keep or let go, all at once.")
    return "\n\n".join(parts)


def _persistent_visitor_construction(query: str, docs: list, profile: dict):
    if profile.get("risk"):
        return f"<visitor_answer>{_build_risk_answer(query)}</visitor_answer>"
    if profile.get("grief"):
        primary = _select_grief_primary(docs)
        if primary:
            answer = _build_grief_answer(query, primary, docs)
            if answer:
                return answer
    if profile.get("transition_open"):
        primary = _select_transition_primary(docs)
        if primary:
            answer = _build_transition_answer(query, primary, docs)
            if answer:
                return answer
    if profile.get("meaning_open"):
        primary = _select_meaning_primary(docs)
        if primary:
            answer = _build_meaning_answer(query, primary, docs)
            if answer:
                return answer
    if profile.get("loneliness"):
        primary = _select_loneliness_primary(docs, profile)
        if primary:
            answer = _build_loneliness_answer(query, primary, docs)
            if answer:
                return answer
    return None


def _v439_finalize(*args, **kwargs):
    user_query = _extract_user_query(args, kwargs)
    raw_context = _context_blocks_from_kwargs(args, kwargs)
    docs = _parse_context_documents(raw_context)
    profile = _query_profile(user_query)
    persistent = _persistent_visitor_construction(user_query, docs, profile)
    if persistent:
        return persistent
    return _original_generate_llm_response(*args, **kwargs)


app = use_core.app
app.title = f"Find Your Way (USE) Navigation Engine {APP_VERSION}"
print(f"USE v439 GUIDE BUILD IDENTITY: build_id={CANONICAL_BUILD_ID}, version={APP_VERSION}, fingerprint={DEPLOYMENT_FINGERPRINT}, source_sha256={RUNTIME_SOURCE_SHA256}, core_blob_sha256={_core_runtime_sha}")
use_core.APP_VERSION = APP_VERSION
use_core.DEPLOYMENT_FINGERPRINT = DEPLOYMENT_FINGERPRINT
use_core.CANONICAL_BUILD_ID = CANONICAL_BUILD_ID
use_core.RUNTIME_SOURCE_SHA256 = RUNTIME_SOURCE_SHA256
use_core.EXPECTED_CORE_BLOB_SHA = EXPECTED_CORE_BLOB_SHA
use_core.generate_llm_response = _v439_finalize
