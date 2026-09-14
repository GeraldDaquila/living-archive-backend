# USE PRODUCTION VERSION: v452 — verified evidence-gap visitor-construction boundary
import hashlib
import importlib
import re
from pathlib import Path

APP_VERSION = "v452"
DEPLOYMENT_FINGERPRINT = "USE-v452-verified-evidence-gap-visitor-construction-boundary"
CANONICAL_BUILD_ID = "USE-BUILD-v452-verified-evidence-gap-visitor-construction-boundary"
EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"

_MAIN_PATH = Path(__file__).resolve()
_CORE_PATH = _MAIN_PATH.with_name("use_core.py")
RUNTIME_SOURCE_SHA256 = hashlib.sha256(_MAIN_PATH.read_bytes()).hexdigest()
if not _CORE_PATH.exists():
    raise RuntimeError("USE v452 package integrity failure: use_core.py is missing.")
_core_bytes = _CORE_PATH.read_bytes()
_core_runtime_sha = hashlib.sha1(f"blob {len(_core_bytes)}\0".encode() + _core_bytes).hexdigest()
if _core_runtime_sha != EXPECTED_CORE_BLOB_SHA:
    raise RuntimeError(f"USE v452 package integrity failure: expected protected core blob sha={EXPECTED_CORE_BLOB_SHA}, actual={_core_runtime_sha}")

use_core = importlib.import_module("use_core")
_original_generate_llm_response = use_core.generate_llm_response
_original_evidence_sufficiency_unavailable_response = getattr(use_core, "_evidence_sufficiency_unavailable_response", None)
if not callable(_original_evidence_sufficiency_unavailable_response):
    raise RuntimeError("USE v452 package integrity failure: evidence-gap response boundary is unavailable.")


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


def _role_evidence(doc: dict) -> dict:
    text = re.sub(r"\s+", " ", str(doc.get("text") or "").strip().casefold())
    title = str(doc.get("title") or "").strip().casefold()
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
        title = str(doc.get("title") or "").strip()
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


def _select_meaning_primary(docs):
    candidates = []
    for index, doc in enumerate(docs):
        title = str(doc.get("title") or "").strip()
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
        title = str(doc.get("title") or "").strip()
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
        title = str(doc.get("title") or "").strip()
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


def _build_transition_answer(user_query, primary=None, docs=None):
    docs = docs or []
    if primary:
        title = str(primary.get("title") or "").strip()
        url = _valid_doc_url(primary)
        if title and url:
            parts = [
                "When an old way of living no longer fits, the uncertainty can be real even when part of you already knows that something has changed.",
                f"A possible place to begin is [{title}]({url}).",
                "For now, you might simply name what no longer fits and give yourself one small space today in which nothing has to be decided. A walk, a page of writing, or a conversation with someone you trust can be enough.",
            ]
            parts.append("You can see whether this lens speaks to the tension you’re carrying, without needing to decide whether to stay or leave, keep or let go, all at once.")
            return "\n\n".join(parts)
    return ("It is possible to sense that a life you have built no longer fits without knowing yet what needs to change. "
            "That uncertainty does not have to be resolved before it can be listened to. "
            "For now, notice what feels most outgrown, what still feels alive, and what you are reluctant to lose. "
            "A small piece of observation can be more useful than forcing yourself to decide what the next chapter should be.")


def _persistent_visitor_construction(query: str, docs: list, profile: dict):
    if profile.get("risk"):
        return f"<visitor_answer>{_build_risk_answer(query)}</visitor_answer>"
    if profile.get("transition_open"):
        return _build_transition_answer(query, _select_transition_primary(docs), docs)
    if profile.get("emptiness_open"):
        primary = _select_emptiness_primary(docs)
        if primary:
            return _build_transition_answer(query, primary, docs) if profile.get("transition_open") else ""
    return None


def _v452_generate_boundary(*args, **kwargs):
    user_query = str(kwargs.get("user_query") or kwargs.get("query") or (args[0] if args else "")).strip()
    raw_context = str(kwargs.get("canonical_link_context") or kwargs.get("retrieved_context") or (args[1] if len(args) > 1 else ""))
    docs = _parse_context_documents(raw_context)
    persistent = _persistent_visitor_construction(user_query, docs, _query_profile(user_query))
    if persistent:
        return persistent
    return _original_generate_llm_response(*args, **kwargs)


def _v452_evidence_gap_boundary(user_query: str, canonical_link_context: str = "") -> str:
    docs = _parse_context_documents(canonical_link_context)
    persistent = _persistent_visitor_construction(user_query, docs, _query_profile(user_query))
    if persistent:
        return persistent
    return _original_evidence_sufficiency_unavailable_response(user_query, canonical_link_context)


_V452_BOUNDARY_QUERY = "Everything looks fine from the outside, but my life feels strangely empty. I keep wondering whether I’ve outgrown the life I built."
_V452_BOUNDARY_AUDIT = _v452_evidence_gap_boundary(_V452_BOUNDARY_QUERY, "")
assert "outgrown" in _V452_BOUNDARY_AUDIT.casefold()
assert "uncertainty" in _V452_BOUNDARY_AUDIT.casefold()

app = use_core.app
app.title = f"Find Your Way (USE) Navigation Engine {APP_VERSION}"
print(f"USE v452 GUIDE BUILD IDENTITY: build_id={CANONICAL_BUILD_ID}, version={APP_VERSION}, fingerprint={DEPLOYMENT_FINGERPRINT}, source_sha256={RUNTIME_SOURCE_SHA256}, core_blob_sha256={_core_runtime_sha}")
use_core.APP_VERSION = APP_VERSION
use_core.DEPLOYMENT_FINGERPRINT = DEPLOYMENT_FINGERPRINT
use_core.CANONICAL_BUILD_ID = CANONICAL_BUILD_ID
use_core.RUNTIME_SOURCE_SHA256 = RUNTIME_SOURCE_SHA256
use_core.EXPECTED_CORE_BLOB_SHA = EXPECTED_CORE_BLOB_SHA
use_core.generate_llm_response = _v452_generate_boundary
use_core._evidence_sufficiency_unavailable_response = _v452_evidence_gap_boundary
