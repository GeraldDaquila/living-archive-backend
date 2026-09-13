# USE PRODUCTION VERSION: v395 — runtime hook positional contract repair
# v391 remains the protected production baseline; this wrapper changes only visitor-facing
# recommendation role selection/construction. Protected use_core.py is unchanged.
import hashlib
import importlib
import re
from pathlib import Path

APP_VERSION = "v395"
DEPLOYMENT_FINGERPRINT = "USE-v395-positional-contract-repair"
CANONICAL_BUILD_ID = "USE-BUILD-v395-positional-contract-repair"
EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"

_MAIN_PATH = Path(__file__).resolve()
_CORE_PATH = _MAIN_PATH.with_name("use_core.py")
RUNTIME_SOURCE_SHA256 = hashlib.sha256(_MAIN_PATH.read_bytes()).hexdigest()
if not _CORE_PATH.exists():
    raise RuntimeError("USE v395 package integrity failure: use_core.py is missing.")
_core_bytes = _CORE_PATH.read_bytes()
_core_runtime_sha = hashlib.sha1(f"blob {len(_core_bytes)}\0".encode() + _core_bytes).hexdigest()
if _core_runtime_sha != EXPECTED_CORE_BLOB_SHA:
    raise RuntimeError(f"USE v395 package integrity failure: expected protected core blob sha={EXPECTED_CORE_BLOB_SHA}, actual={_core_runtime_sha}")

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
    # Actual production signature is generate_llm_response(query, context, intent, ...).
    # Prefer that explicit positional contract over heuristic string scanning.
    if len(args) >= 1 and isinstance(args[0], str) and args[0].strip():
        return args[0].strip()
    return ""


def _extract_intent(args, kwargs):
    for key in ("intent", "query_intent", "classification"):
        value = kwargs.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    if len(args) >= 3 and isinstance(args[2], str) and args[2].strip():
        return args[2].strip()
    return ""


def _context_blocks_from_kwargs(args, kwargs):
    for key in ("retrieved_context_blocks", "canonical_link_context", "retrieved_context", "context_blocks"):
        if kwargs.get(key):
            return str(kwargs[key])
    if len(args) >= 2 and isinstance(args[1], str) and args[1].strip():
        return args[1]
    return ""


def _normalize_title(text: str) -> str:
    return re.sub(r"^[\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F\u200D]+\s*", "", str(text or "").strip()).strip()


def _query_profile(user_query: str) -> dict:
    q = re.sub(r"\s+", " ", str(user_query or "").strip().casefold())
    return {
        "sensitive": bool(re.search(r"\b(?:grief|grieving|bereavement|bereaved|loss|lost|death|died|dying|loved one|trauma|abuse|coercion|suicid|self-harm|overdose|loneliness|lonely|despair|emptiness|depressed|depression)\b", q)),
        "grief": bool(re.search(r"\b(?:grief|grieving|bereavement|bereaved|loss|death|died|dying|loved one)\b", q)),
        "risk": bool(re.search(r"\b(?:suicid|self-harm|overdose|abuse|coercion|immediate danger|unsafe|threatened)\b", q)),
        "meaning": bool(re.search(r"\b(?:meaning|understanding|perspective|wisdom|why|purpose|identity|continuity|spiritual|afterlife|belief|loneliness|lonely|despair|emptiness)\b", q)),
        "explicit_framework": bool(re.search(r"\b(?:spiritual|spirituality|religious|religion|mystical|mysticism|afterlife|reincarnation|soul|astrology|tarot)\b", q)),
    }


def _is_acute_risk_resource(doc: dict) -> bool:
    corpus = re.sub(r"\s+", " ", str(doc.get("text") or "").strip())
    return bool(re.search(r"\b(?:suicid(?:e|al|ality)|suicidal ideation|self-harm|overdose|acute crisis|crisis intervention|immediate danger)\b", corpus, re.I))


def _role_evidence(doc: dict) -> dict:
    text = re.sub(r"\s+", " ", str(doc.get("text") or "").strip().casefold())
    return {
        "continuity": bool(re.search(r"\b(?:continuity|connection|bond|relationship|belonging|identity|endure|what may remain|what may endure|presence)\b", text)),
        "lived_loss": bool(re.search(r"\b(?:grief|grieving|bereavement|mourning|loss|death|dying|mortality|sorrow|pain of loss|living with loss)\b", text)),
        "existential_loneliness": bool(re.search(r"\b(?:loneliness|lonely|despair|emptiness|isolation|existential|meaninglessness|alone|redemptive power|eternal now)\b", text)),
        "meaning": bool(re.search(r"\b(?:meaning|purpose|wisdom|perspective|understanding|sense-making|make sense|interpretation)\b", text)),
        "grounded": bool(re.search(r"\b(?:science|scientific|research|psychological|clinical|neuroscientific|evidence|empirical)\b", text)),
        "worldview": bool(re.search(r"\b(?:spiritual|spirituality|religious|religion|mystical|mysticism|afterlife|reincarnation|soul|sacred|transcenden)\b", text)),
        "lived_experience": bool(re.search(r"\b(?:experience|lived|personal|human|everyday|relationships|routine|role|journey|navigate|navigating|felt|feeling|living with)\b", text)),
        "practical_reflection": bool(re.search(r"\b(?:reflect|reflection|notice|naming|journal|practice|grounding|orientation|practical|everyday|attention)\b", text)),
    }


def _candidate_role(doc: dict, profile: dict):
    evidence = _role_evidence(doc)
    score = 0
    role_key = "other"
    role_text = "another perspective on the question"
    if evidence["existential_loneliness"]:
        role_key = "existential_loneliness"; role_text = "loneliness, emptiness, and existential dimensions of the question"; score += 14
    if evidence["continuity"] and role_key == "other":
        role_key = "continuity"; role_text = "continuity, connection, and what may endure"
    if evidence["continuity"]: score += 12
    if evidence["lived_loss"] and role_key == "other":
        role_key = "lived_loss"; role_text = "the lived experience of grief, loss, and mortality"
    if evidence["lived_loss"]: score += 10
    if evidence["meaning"] and role_key == "other":
        role_key = "meaning"; role_text = "meaning, perspective, and ways of understanding the experience"
    if evidence["meaning"]: score += 7
    if evidence["grounded"] and role_key == "other":
        role_key = "grounded"; role_text = "a grounded or research-oriented way of looking at the question"
    if evidence["grounded"]: score += 5
    if evidence["lived_experience"] and role_key == "other":
        role_key = "lived_experience"; role_text = "the lived, human experience of the question"
    if evidence["lived_experience"]: score += 4
    if evidence["practical_reflection"] and role_key == "other":
        role_key = "practical_reflection"; role_text = "a reflective or practical way of staying with the question"
    if evidence["practical_reflection"]: score += 3
    if evidence["worldview"] and not profile.get("explicit_framework"): score -= 4
    return role_key, role_text, score


def _select_secondary_pathways(docs, primary_title, profile, limit=2):
    seen = {_normalize_title(primary_title).casefold()}
    ranked = []
    for index, doc in enumerate(docs):
        title = _normalize_title(doc.get("title") or "")
        if not title or title.casefold() in seen: continue
        if profile.get("sensitive") and not profile.get("explicit_framework") and not profile.get("risk") and _is_acute_risk_resource(doc): continue
        role_key, role_text, score = _candidate_role(doc, profile)
        if profile.get("grief") and role_key == "continuity": score += 4
        if profile.get("grief") and role_key == "existential_loneliness": score += 5
        if profile.get("meaning") and role_key == "meaning": score += 3
        if profile.get("sensitive") and not profile.get("explicit_framework") and not profile.get("risk") and re.search(r"\b(?:afterlife|reincarnation)\b", str(doc.get("text") or ""), re.I): score -= 4
        if score > 0: ranked.append((score, index, role_key, role_text, doc))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    selected = []; role_keys = set()
    for score, index, role_key, role_text, doc in ranked:
        if role_key in role_keys: continue
        role_keys.add(role_key); selected.append({"doc": doc, "role_key": role_key, "role_text": role_text, "score": score})
        if len(selected) >= limit: break
    return selected


def _evidence_boundary_note(docs, profile):
    has_science = any(re.search(r"\b(?:scientific|science|psychological|neuroscientific|clinical|research)\b", str(doc.get("text") or ""), re.I) for doc in docs)
    has_spiritual = any(re.search(r"\b(?:spiritual|soul|afterlife|religious|mystical|sacred|transcenden)\b", str(doc.get("text") or ""), re.I) for doc in docs)
    if has_science and has_spiritual: return "It brings different ways of understanding the question into the same conversation without requiring them to become a single certainty."
    if has_spiritual: return "Where the material turns toward spiritual or afterlife possibilities, those are perspectives offered by the work rather than established facts you need to accept."
    if profile.get("meaning"): return "It offers a way into the question while leaving room to distinguish what is known from what remains interpretation, possibility, or personal meaning."
    return "It offers a place to begin without asking the material to provide more certainty than it can support."


def _article_role_phrase(role_text):
    return {
        "continuity, connection, and what may endure": "a route into continuity, connection, and what may endure",
        "loneliness, emptiness, and existential dimensions of the question": "a route into loneliness, emptiness, and the existential dimensions of the question",
        "the lived experience of grief, loss, and mortality": "a route into the lived experience of grief, loss, and mortality",
        "meaning, perspective, and ways of understanding the experience": "a route into meaning, perspective, and ways of understanding the experience",
        "a grounded or research-oriented way of looking at the question": "a grounded or research-oriented route into the question",
        "the lived, human experience of the question": "a route into the lived, human experience of the question",
        "a reflective or practical way of staying with the question": "a route into reflective or practical ways of staying with the question",
        "another perspective on the question": "another perspective on the question",
    }.get(role_text, role_text)


def _build_sensitive_recommendation_answer(user_query, primary, docs):
    profile = _query_profile(user_query)
    title = _normalize_title(primary.get("title") or "")
    url = str(primary.get("url") or primary.get("canonical_url") or "").strip()
    if not title or not re.match(r"^https?://\S+$", url, re.I): return ""
    secondaries = _select_secondary_pathways(docs, title, profile)
    if profile.get("grief"): opening = "When you are grieving the death of someone you love, there may be no easy place to begin. Grief can bring pain, longing, questions, and uncertainty all at once."
    elif profile.get("sensitive"): opening = "A question like this can be difficult to hold in one frame, so it can help to have a clear place to begin while leaving room for the question to remain open."
    else: opening = "A question like this can benefit from a clear place to begin and room for the question to remain open."
    sections = [opening, f"A useful doorway is [{title}]({url}).", _evidence_boundary_note(docs, profile)]
    if secondaries:
        role_sentences = [f"[{_normalize_title(item['doc'].get('title') or '')}]({str(item['doc'].get('url') or item['doc'].get('canonical_url') or '').strip()}) — {_article_role_phrase(item['role_text'])}." for item in secondaries if item.get("doc")]
        if role_sentences: sections.append("From there, the Archive opens a few distinct paths:\n\n" + "\n\n".join(role_sentences))
    if profile.get("risk"): sections.append("The Archive can offer reflection and orientation, but where there is immediate danger or coercion, real-world safety and trusted human support matter more than reflection alone.")
    elif profile.get("grief"): sections.append("There is no need to settle the grief all at once. One piece that feels right for today can be enough of a place to begin.")
    elif profile.get("sensitive"): sections.append("You do not need to turn the question into an answer all at once. A piece that opens a useful perspective can be enough of a place to begin.")
    else: sections.append("Take what is useful, leave what is not, and let the question remain open where it needs to.")
    return "\n\n".join(section for section in sections if section)


def _v395_finalize(*args, **kwargs):
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
    print(
        "USE v395 runtime hook: "
        f"query_present={bool(user_query)}, intent={intent!r}, docs={len(docs)}, "
        f"recommendation={recommendation_question}, args={len(args)}, kwargs={sorted(kwargs.keys())}"
    )
    if user_query and recommendation_question and (profile.get("sensitive") or profile.get("meaning")):
        primary = use_core._adjudicate_recommendation_resource(docs, user_query) if docs else None
        if primary:
            answer = _build_sensitive_recommendation_answer(user_query, primary, docs)
            if answer:
                print(
                    "USE v395 runtime hook: recommendation interception=ACTIVE "
                    f"primary='{_normalize_title(primary.get('title') or '')}'"
                )
                return answer
    return _original_generate_llm_response(*args, **kwargs)


app = use_core.app
app.title = f"Find Your Way (USE) Navigation Engine {APP_VERSION}"
print(f"USE v395 GUIDE BUILD IDENTITY: build_id={CANONICAL_BUILD_ID}, version={APP_VERSION}, fingerprint={DEPLOYMENT_FINGERPRINT}, source_sha256={RUNTIME_SOURCE_SHA256}, core_blob_sha256={_core_runtime_sha}")
use_core.APP_VERSION = APP_VERSION
use_core.DEPLOYMENT_FINGERPRINT = DEPLOYMENT_FINGERPRINT
use_core.CANONICAL_BUILD_ID = CANONICAL_BUILD_ID
use_core.RUNTIME_SOURCE_SHA256 = RUNTIME_SOURCE_SHA256
use_core.EXPECTED_CORE_BLOB_SHA = EXPECTED_CORE_BLOB_SHA
use_core.generate_llm_response = _v395_finalize
