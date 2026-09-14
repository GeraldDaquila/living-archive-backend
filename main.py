# USE PRODUCTION VERSION: v451 — evidence-gap visitor-construction boundary
import hashlib
import importlib
import re
from pathlib import Path

APP_VERSION = "v451"
DEPLOYMENT_FINGERPRINT = "USE-v451-evidence-gap-visitor-construction-boundary"
CANONICAL_BUILD_ID = "USE-BUILD-v451-evidence-gap-visitor-construction-boundary"
EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"

_MAIN_PATH = Path(__file__).resolve()
_CORE_PATH = _MAIN_PATH.with_name("use_core.py")
RUNTIME_SOURCE_SHA256 = hashlib.sha256(_MAIN_PATH.read_bytes()).hexdigest()
if not _CORE_PATH.exists():
    raise RuntimeError("USE v451 package integrity failure: use_core.py is missing.")
_core_bytes = _CORE_PATH.read_bytes()
_core_runtime_sha = hashlib.sha1(f"blob {len(_core_bytes)}\0".encode() + _core_bytes).hexdigest()
if _core_runtime_sha != EXPECTED_CORE_BLOB_SHA:
    raise RuntimeError(f"USE v451 package integrity failure: expected protected core blob sha={EXPECTED_CORE_BLOB_SHA}, actual={_core_runtime_sha}")

use_core = importlib.import_module("use_core")
_original_generate_llm_response = use_core.generate_llm_response
_original_handle_query = getattr(use_core, "handle_query", None)
_original_evidence_sufficiency_unavailable_response = getattr(
    use_core, "_evidence_sufficiency_unavailable_response", None
)
if _original_handle_query is None:
    raise RuntimeError("USE v451 package integrity failure: API query handler is unavailable.")
if not callable(_original_evidence_sufficiency_unavailable_response):
    raise RuntimeError("USE v451 package integrity failure: evidence-gap response boundary is unavailable.")


def _query_profile(user_query: str) -> dict:
    q = re.sub(r"\s+", " ", str(user_query or "").strip().casefold())
    transition_marker = bool(re.search(r"\b(?:old way|no longer works|what comes next|next chapter|different way of seeing|way of seeing.*no longer|transition|turning point|threshold|outgrown|outgrew|no longer feels like me|changed so much|life has changed|change it|changing|what no longer fits|what no longer feels right|built.*afraid.*lose|afraid.*lose.*change|move on|moving on|new chapter|leave.*behind|letting go|rebuild|starting over|reinvent)\b", q))
    transition_context = bool(re.search(r"\b(?:life|my life|what comes next|think|explore|help|built|change|changed|fits|right|lose|leaving|starting|begin|next)\b", q))
    emptiness_marker = bool(re.search(r"\b(?:empty|emptiness|numb|numbness|disconnected from my life|disconnected from life|feel disconnected|disconnected|going through the motions|nothing is obviously wrong|nothing is wrong|all right on paper|everything is fine|feel absent from my life)\b", q))
    emptiness_context = bool(re.search(r"\b(?:life|my life|unhappy|happiness|numb|empty|disconnected|understand|happening|help|supposed to|supposed)\b", q))
    return {
        "loneliness": bool(re.search(r"\b(?:loneliness|lonely|alone|isolat|disconnected|belonging|connection)\b", q)),
        "risk": bool(re.search(r"\b(?:suicid\w*|self-harm|self harm|overdose|abuse|coercion|immediate danger|unsafe|threatened|kill(?:ing)? myself|kill(?:ing)? yourself|want(?:ing)? to die|don't want to (?:live|be here)|do not want to (?:live|be here)|end my life|take my own life|harm myself|hurt myself|better off dead|wish I were dead)\b", q)),
        "coercion_open": bool(re.search(r"\b(?:controlling|control(?:led|s)?|coercion|coercive|making me feel|can't trust my own judgment|cannot trust my own judgment|undermine(?:s|d)? my judgment|question my own judgment|isolat(?:es|ed)? me|controls what i do|controls what i wear|controls who i see|controls who i talk to|power over me|makes decisions for me)\b", q)) and bool(re.search(r"\b(?:someone in my life|partner|spouse|relationship|person|trust my own judgment|judgment|control|controlling|coercion|worry|worried|concerned|understand|happening|help|power|choice|freedom|safety)\b", q)),
        "emptiness_open": emptiness_marker and emptiness_context,
        "meaning_open": bool(re.search(r"\b(?:what gives life meaning|meaning in life|what makes life meaningful|what matters|purpose|larger meaning|meaning behind)\b", q)) and bool(re.search(r"\b(?:lost|not sure|don't know|do not know|uncertain|explore|exploring|where might i begin|where should i begin|going through|believe|belief|what to believe)\b", q)),
        "transition_open": transition_marker and transition_context,
        "grief": bool(re.search(r"\b(?:griev\w*|grief|mourning|death of (?:a|my|their) (?:love|loved) one|loss of (?:a|my|their) (?:love|loved) one|someone (?:i|we|they) love(?:d)? died)\b", q)),
        "fear_open": bool(re.search(r"\b(?:scared|afraid|fear|fearful|frightened|terrified|anxious|anxiety|uneasy|uncertain|uncertainty)\b", q)) and bool(re.search(r"\b(?:what(?:'s| is) happening|happening|make sense|understand|explore|help|don't know|do not know|not sure|life|going on)\b", q)),
        "anger_open": bool(re.search(r"\b(?:angr\w*|furious|resent\w*|resentment|frustrat\w*|frustration|bitter\w*|bitterness)\b", q)) and bool(re.search(r"\b(?:life|carrying|long time|understand|understanding|help|doing to me|happened|turned out|going on|explore)\b", q)),
        "ambiguous_loss_open": bool(re.search(r"\b(?:lost something important|lost something|can't quite put my finger|not sure whether i'm grieving|not sure whether i am grieving|grieving, changing|changing, or just stuck|grieving|stuck)\b", q)) and bool(re.search(r"\b(?:lost|loss|grieving|changing|stuck|what's happening|what is happening|understand|help|explore)\b", q)),
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


def _valid_doc_url(doc: dict) -> str:
    url = str(doc.get("url") or doc.get("canonical_url") or "").strip()
    return url if re.match(r"^https://\S+$", url, re.I) else ""


def _doc_identity(doc: dict) -> str:
    return str(doc.get("url") or doc.get("canonical_url") or "").strip()


def _select_grief_primary(docs):
    ranked = []
    for index, doc in enumerate(docs):
        title = _normalize_title(doc.get("title") or "")
        url = _valid_doc_url(doc)
        if not title or not url:
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
        url = _valid_doc_url(doc)
        if not title or not url:
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
        url = _valid_doc_url(doc)
        text = re.sub(r"\s+", " ", str(doc.get("text") or "").strip()).casefold()
        if not title or not url:
            continue
        e = _role_evidence(doc)
        score = 12 * int(e["meaning"]) + 10 * int(e["grounded"]) + 8 * int(e["lived_experience"]) + 5 * int(bool(re.search(r"\b(?:purpose|meaningful|existential|existence|identity)\b", text)))
        if e["worldview"]:
            score -= 10
        candidates.append((score, index, doc))
    candidates = [item for item in candidates if item[0] > 0]
    candidates.sort(key=lambda item: (-item[0], item[1]))
    return candidates[0][2] if candidates else None


def _select_emptiness_primary(docs):
    candidates = []
    for index, doc in enumerate(docs):
        title = _normalize_title(doc.get("title") or "")
        url = _valid_doc_url(doc)
        text = re.sub(r"\s+", " ", str(doc.get("text") or "").strip()).casefold()
        if not title or not url or _is_risk_related(doc):
            continue
        corpus = f"{title.casefold()} {text}"
        e = _role_evidence(doc)
        explicit = int(bool(re.search(r"\b(?:emptiness|empty|numb|numbness|disconnected|disconnection|going through the motions|absent from (?:my )?life|nothing is wrong|all right on paper|everything is fine|unhappy|fulfillment|fulfilled)\b", corpus)))
        life_context = int(bool(re.search(r"\b(?:life|living|meaningful|purpose|identity|belonging|connection|what matters|how to live|change|season|chapter|routine|daily life)\b", corpus)))
        reflective = int(e["meaning"] or e["practical_reflection"])
        grounded = int(e["grounded"])
        lived = int(e["lived_experience"])
        score = 45 * explicit + 18 * life_context + 12 * reflective + 8 * grounded + 8 * lived
        if e["worldview"]:
            score -= 12
        if score > 0:
            candidates.append((score, index, doc))
    candidates.sort(key=lambda item: (-item[0], item[1]))
    return candidates[0][2] if candidates else None


def _select_transition_primary(docs):
    candidates = []
    for index, doc in enumerate(docs):
        title = _normalize_title(doc.get("title") or "")
        url = _valid_doc_url(doc)
        if not title or not url:
            continue
        e = _role_evidence(doc)
        score = 18 * int(e["threshold"]) + 8 * int(e["lived_experience"]) + 6 * int(e["meaning"]) + 4 * int(bool(re.search(r"\b(?:transition|threshold|liminal|crossroads|turning point|change|outgrown|letting go|starting over|reinvent)\b", f"{title} {doc.get('text') or ''}", re.I)))
        if e["worldview"]:
            score -= 8
        if score > 0:
            candidates.append((score, index, doc))
    candidates.sort(key=lambda item: (-item[0], item[1]))
    return candidates[0][2] if candidates else None


def _select_secondary_pathways(user_query, primary, docs, primary_role, limit=1):
    primary_key = _doc_identity(primary).casefold()
    selector = getattr(use_core, "_select_complementary_generation_evidence", None)
    candidates = []
    if callable(selector):
        try:
            candidate = selector(docs, user_query, protected_documents=[])
            if isinstance(candidate, dict):
                candidate = list(candidate.values()) if all(isinstance(v, dict) for v in candidate.values()) else []
            if isinstance(candidate, list):
                candidates = [doc for doc in candidate if isinstance(doc, dict)]
        except Exception:
            candidates = []
    ranked = []
    for index, doc in enumerate(candidates):
        if _is_risk_related(doc) or not _valid_doc_url(doc) or _doc_identity(doc).casefold() == primary_key:
            continue
        e = _role_evidence(doc)
        if e["meaning"] and not e["worldview"]:
            role_text, score = "meaning, perspective, and ways of understanding the experience", 12
        elif e["grounded"]:
            role_text, score = "a grounded or research-oriented route into the question", 11
        elif e["practical_reflection"]:
            role_text, score = "staying with the question through reflection and practice", 10
        else:
            continue
        ranked.append((score, index, role_text, doc))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return [{"doc": item[3], "role_text": item[2], "score": item[0]} for item in ranked[:limit]]


def _foothold_text(primary_role: str) -> str:
    footholds = {
        "grief": "For now, it may be enough to stay close to what you are actually feeling and choose one small act of care today—rest, a quiet walk, a conversation with someone you trust, or simply giving yourself permission not to make sense of everything yet.",
        "transition": "For now, you might simply name what no longer fits and give yourself one small space today in which nothing has to be decided. A walk, a page of writing, or a conversation with someone you trust can be enough.",
        "meaning": "For now, you might choose one thing that still feels quietly worth caring about and give it your attention today. You do not need a complete philosophy of life before taking one meaningful step.",
        "loneliness": "For now, a gentle foothold might be one small movement toward connection—a message to someone you trust, sitting with someone, or simply naming what you wish another person could understand.",
        "fear": "For now, you might not need to figure out exactly what you are afraid of. Notice one thing in the situation that feels most immediate, and give yourself permission to take it one small piece at a time.",
        "anger": "For now, you might let yourself name what the anger is protecting or pointing toward—hurt, disappointment, violated expectations, or a sense that something important has been lost—without needing to act on it or resolve it today.",
        "liminality": "For now, you might allow the uncertainty itself to be information. You do not have to decide yet whether this is grief, change, or being stuck; simply notice what feels most absent, most different, or most unfinished.",
        "emptiness": "For now, you might notice one moment in the day when you feel most present and one when you feel most absent, without judging either one. You do not have to decide yet whether this is unhappiness, numbness, exhaustion, or something else.",
    }
    return footholds.get(primary_role, "For now, one small, humane step is enough. You do not need to settle the larger question before taking it.")


def _build_risk_answer_from_query(user_query: str = ""):
    return _build_risk_answer(user_query)


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
    secondaries = _select_secondary_pathways(user_query, primary, docs, "loneliness", limit=1)
    parts = [
        "Loneliness can be difficult to name because it is not always only about being physically alone. It can touch belonging, connection, meaning, and the sense of being seen or understood.",
        f"A gentle place to begin is [{title}]({url}).",
        _foothold_text("loneliness"),
    ]
    if secondaries:
        item = secondaries[0]
        item_title = _normalize_title(item["doc"].get("title") or "")
        item_url = _valid_doc_url(item["doc"])
        if item_title and item_url:
            parts.append("The Archive offers more than one way into the question, and the routes do different work rather than resolving it into one certainty.")
            parts.append(f"Another route into the question is [{item_title}]({item_url}).")
    return "\n\n".join(parts)


def _build_meaning_answer(user_query, primary, docs):
    title = _normalize_title(primary.get("title") or "")
    url = _valid_doc_url(primary)
    if not title or not url:
        return ""
    e = _role_evidence(primary)
    secondaries = _select_secondary_pathways(user_query, primary, docs, "meaning", limit=1)
    parts = [f"A possible place to begin is [{title}]({url}). The essay offers a perspective rather than a final answer, so you can see what is useful without needing to adopt its worldview."]
    if e["worldview"]:
        parts.append("The essay also works with spiritual or cosmological possibilities. Those belong to a worldview or interpretation presented in the Archive, rather than established fact, so you can explore them without having to adopt them.")
    if secondaries:
        item = secondaries[0]
        item_title = _normalize_title(item["doc"].get("title") or "")
        item_url = _valid_doc_url(item["doc"])
        if item_title and item_url:
            parts.append(f"Another route into the question is [{item_title}]({item_url}), offering {item['role_text']}.")
    parts.append("You can stay with the question and decide for yourself which parts feel grounded, which feel interpretive, and which may simply hold personal meaning for you.")
    return "\n\n".join(parts)


def _build_transition_answer(user_query, primary=None, docs=None):
    docs = docs or []
    if primary:
        title = _normalize_title(primary.get("title") or "")
        url = _valid_doc_url(primary)
        if title and url:
            parts = [
                "When an old way of living no longer fits, the uncertainty can be real even when part of you already knows that something has changed.",
                f"A possible place to begin is [{title}]({url}).",
                _foothold_text("transition"),
            ]
            secondaries = _select_secondary_pathways(user_query, primary, docs, "transition", limit=1)
            if secondaries:
                item = secondaries[0]
                doc = item["doc"]
                sec_title = _normalize_title(doc.get("title") or "")
                sec_url = _valid_doc_url(doc)
                if sec_title and sec_url:
                    parts.append(f"Another route into the question is [{sec_title}]({sec_url}), offering {item['role_text']}.")
            parts.append("You can see whether this lens speaks to the tension you’re carrying, without needing to decide whether to stay or leave, keep or let go, all at once.")
            return "\n\n".join(parts)
    return ("It is possible to sense that a life you have built no longer fits without knowing yet what needs to change. "
            "That uncertainty does not have to be resolved before it can be listened to. "
            "For now, notice what feels most outgrown, what still feels alive, and what you are reluctant to lose. "
            "A small piece of observation can be more useful than forcing yourself to decide what the next chapter should be.")


def _build_emptiness_answer(user_query, primary, docs):
    title = _normalize_title(primary.get("title") or "")
    url = _valid_doc_url(primary)
    if not title or not url:
        return ""
    primary_evidence = _role_evidence(primary)
    parts = [
        "You can be doing what you are supposed to do and still feel strangely absent from your own life. Nothing being obviously wrong does not make the feeling less real, and you do not have to decide yet whether it is unhappiness, numbness, exhaustion, or a sign that something in your life has changed.",
        "What you may be noticing is a gap between functioning and feeling engaged with your life. That can be worth exploring without turning it immediately into a diagnosis or a problem you must fix.",
        f"A possible place to begin is [{title}]({url}). Its perspective may help you put language around that sense of emptiness and ask what, beneath the surface, feels missing, muted, or unfinished. Treat it as a reflection doorway rather than an explanation you have to accept.",
        _foothold_text("emptiness"),
    ]
    if primary_evidence["worldview"]:
        parts.append("If the essay moves into spiritual or cosmological interpretation, that belongs to the perspective presented in the Archive rather than established fact, so you can consider it without having to adopt it.")
    parts.append("You can also notice the contrast between moments when you feel most present and most absent: what are you doing, who are you with, and what seems to come alive or go quiet? You do not need to solve the larger question before that pattern begins to tell you something.")
    parts.append("Whether this turns out to be a season, a signal that something needs to change, or simply something you want to understand more clearly, the next step can be observation rather than judgment.")
    return "\n\n".join(parts)


def _build_coercion_answer(user_query, docs):
    parts = [
        "When someone repeatedly controls what you do or leaves you doubting your own judgment, it is reasonable to take that pattern seriously. You do not need to decide today whether it has a particular label before you can notice what it is doing to your sense of safety and autonomy.",
    ]
    candidates = []
    for index, doc in enumerate(docs):
        title = _normalize_title(doc.get("title") or "")
        url = _valid_doc_url(doc)
        text = f"{title} {doc.get('text') or ''}"
        if title and url and not _is_risk_related(doc) and re.search(r"\b(?:autonomy|boundaries|control|coercion|power|judgment|self-trust|freedom)\b", text, re.I):
            candidates.append((index, title, url))
    candidates.sort(key=lambda item: item[0])
    if candidates:
        _, title, url = candidates[0]
        parts.append(f"A possible place to begin in the Living Archive is [{title}]({url}). Treat it as a reflection doorway rather than a verdict about your situation; the point is to see whether its language helps you recognize what is happening without overriding your own judgment.")
    else:
        parts.append("The Living Archive does not need to supply a label before your experience can be taken seriously. A useful next step is to look for material about autonomy, power, boundaries, control, or self-trust rather than forcing the experience into a more generic psychological frame.")
    parts.append("For now, consider writing down a few specific things that have happened, especially moments when you felt pressured, isolated, or unable to make an ordinary choice freely. If it feels safe, sharing those observations with someone you trust can give you another perspective.")
    parts.append("Support from a trusted person or appropriate local support service may be more useful than trying to interpret the experience alone. You are allowed to take your own unease seriously without having to prove a case first.")
    return "\n\n".join(parts)


def _build_liminality_answer(user_query, primary, docs):
    title = _normalize_title(primary.get("title") or "")
    url = _valid_doc_url(primary)
    if not title or not url:
        return ""
    return "\n\n".join([
        "Sometimes something important has been lost, but the experience does not yet feel like straightforward grief. It can also be a period in which your life is changing and you cannot tell what the feeling means yet.",
        f"A possible place to begin is [{title}]({url}).",
        _foothold_text("liminality"),
    ])


def _build_fear_answer(user_query, primary, docs):
    title = _normalize_title(primary.get("title") or "")
    url = _valid_doc_url(primary)
    if not title or not url:
        return ""
    secondaries = _select_secondary_pathways(user_query, primary, docs, "fear", limit=1)
    primary_evidence = _role_evidence(primary)
    parts = [
        "Feeling scared about what is happening in your life without being able to name the fear clearly can be disorienting. You do not have to explain it perfectly before you can begin to look at it.",
        f"A possible place to begin is [{title}]({url}). It offers one way of reflecting on what can lie beneath an unsettled or uncertain experience, rather than telling you what your fear must mean.",
        _foothold_text("fear"),
    ]
    if primary_evidence["worldview"]:
        parts.append("If the essay moves into spiritual or cosmological interpretation, that belongs to the perspective presented in the Archive rather than established fact, so you can consider it without having to adopt it.")
    if secondaries:
        item = secondaries[0]
        doc = item["doc"]
        sec_title = _normalize_title(doc.get("title") or "")
        sec_url = _valid_doc_url(doc)
        if sec_title and sec_url:
            parts.append(f"Another route into the question is [{sec_title}]({sec_url}), offering {item['role_text']}.")
    parts.append("You can stay with the uncertainty and notice what feels most immediate, without needing to solve the whole situation at once.")
    return "\n\n".join(parts)


def _build_anger_answer(user_query, primary, docs):
    title = _normalize_title(primary.get("title") or "")
    url = _valid_doc_url(primary)
    if not title or not url:
        return ""
    secondaries = _select_secondary_pathways(user_query, primary, docs, "anger", limit=1)
    parts = [
        "Anger about how your life has turned out can carry more than anger itself—it can hold hurt, disappointment, grief, or the feeling that something important did not go as it should have. You do not have to dismiss the anger or act on it before you can understand it.",
        f"A possible place to begin is [{title}]({url}). It offers one perspective for reflecting on what is happening beneath the surface of a difficult experience, rather than telling you what your anger must mean.",
        _foothold_text("anger"),
    ]
    primary_evidence = _role_evidence(primary)
    if primary_evidence["worldview"]:
        parts.append("If the essay moves into spiritual or cosmological interpretation, that belongs to the perspective presented in the Archive rather than established fact, so you can consider it without having to adopt it.")
    if secondaries:
        item = secondaries[0]
        doc = item["doc"]
        sec_title = _normalize_title(doc.get("title") or "")
        sec_url = _valid_doc_url(doc)
        if sec_title and sec_url:
            parts.append(f"Another route into the question is [{sec_title}]({sec_url}), offering {item['role_text']}.")
    parts.append("You can stay with the anger long enough to notice what it may be asking you to see, without needing to turn that understanding into a final judgment about yourself or your life.")
    return "\n\n".join(parts)


def _persistent_visitor_construction(query: str, docs: list, profile: dict):
    if profile.get("risk"):
        return f"<visitor_answer>{_build_risk_answer(query)}</visitor_answer>"
    if profile.get("coercion_open"):
        answer = _build_coercion_answer(query, docs=docs)
        if answer:
            return answer
    if profile.get("ambiguous_loss_open"):
        primary = _select_transition_primary(docs)
        if primary:
            answer = _build_liminality_answer(query, primary, docs)
            if answer:
                return answer
    if profile.get("grief"):
        primary = _select_grief_primary(docs)
        if primary:
            answer = _build_grief_answer(query, primary, docs)
            if answer:
                return answer
    if profile.get("transition_open"):
        primary = _select_transition_primary(docs)
        answer = _build_transition_answer(query, primary, docs)
        if answer:
            return answer
    if profile.get("emptiness_open"):
        primary = _select_emptiness_primary(docs)
        if primary:
            answer = _build_emptiness_answer(query, primary, docs)
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
    if profile.get("fear_open"):
        primary = _select_meaning_primary(docs)
        if primary:
            answer = _build_fear_answer(query, primary, docs)
            if answer:
                return answer
    if profile.get("anger_open"):
        primary = _select_transition_primary(docs)
        if primary:
            answer = _build_anger_answer(query, primary, docs)
            if answer:
                return answer
    return None


def _v450_generate_boundary(*args, **kwargs):
    user_query = _extract_user_query(args, kwargs)
    raw_context = _context_blocks_from_kwargs(args, kwargs)
    docs = _parse_context_documents(raw_context)
    profile = _query_profile(user_query)
    persistent = _persistent_visitor_construction(user_query, docs, profile)
    if persistent:
        return persistent
    return _original_generate_llm_response(*args, **kwargs)


def _v451_evidence_gap_boundary(user_query: str, canonical_link_context: str = "") -> str:
    """Preserve v450 visitor construction when the core bypasses generation."""
    docs = _parse_context_documents(canonical_link_context)
    profile = _query_profile(user_query)
    persistent = _persistent_visitor_construction(user_query, docs, profile)
    if persistent:
        return persistent
    return _original_evidence_sufficiency_unavailable_response(user_query, canonical_link_context)


_V451_BOUNDARY_QUERY = "Everything looks fine from the outside, but my life feels strangely empty. I keep wondering whether I’ve outgrown the life I built."
_V451_BOUNDARY_AUDIT = _v451_evidence_gap_boundary(_V451_BOUNDARY_QUERY, "")
if "outgrown" not in _V451_BOUNDARY_AUDIT.casefold() or "uncertainty" not in _V451_BOUNDARY_AUDIT.casefold():
    raise RuntimeError("USE v451 evidence-gap boundary audit failed: transition construction did not survive the core bypass.")

app = use_core.app
app.title = f"Find Your Way (USE) Navigation Engine {APP_VERSION}"
print(f"USE v451 GUIDE BUILD IDENTITY: build_id={CANONICAL_BUILD_ID}, version={APP_VERSION}, fingerprint={DEPLOYMENT_FINGERPRINT}, source_sha256={RUNTIME_SOURCE_SHA256}, core_blob_sha256={_core_runtime_sha}")
use_core.APP_VERSION = APP_VERSION
use_core.DEPLOYMENT_FINGERPRINT = DEPLOYMENT_FINGERPRINT
use_core.CANONICAL_BUILD_ID = CANONICAL_BUILD_ID
use_core.RUNTIME_SOURCE_SHA256 = RUNTIME_SOURCE_SHA256
use_core.EXPECTED_CORE_BLOB_SHA = EXPECTED_CORE_BLOB_SHA
use_core.generate_llm_response = _v450_generate_boundary
use_core._evidence_sufficiency_unavailable_response = _v451_evidence_gap_boundary
