# USE PRODUCTION VERSION: v399 — compassionate loneliness navigation
# v391 remains the protected production baseline; this wrapper changes only visitor-facing
# recommendation role selection/construction. Protected use_core.py is unchanged.
import hashlib
import importlib
import re
from pathlib import Path

APP_VERSION = "v399"
DEPLOYMENT_FINGERPRINT = "USE-v399-compassionate-loneliness-navigation"
CANONICAL_BUILD_ID = "USE-BUILD-v399-compassionate-loneliness-navigation"
EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"

_MAIN_PATH = Path(__file__).resolve()
_CORE_PATH = _MAIN_PATH.with_name("use_core.py")
RUNTIME_SOURCE_SHA256 = hashlib.sha256(_MAIN_PATH.read_bytes()).hexdigest()
if not _CORE_PATH.exists():
    raise RuntimeError("USE v399 package integrity failure: use_core.py is missing.")
_core_bytes = _CORE_PATH.read_bytes()
_core_runtime_sha = hashlib.sha1(f"blob {len(_core_bytes)}\0".encode() + _core_bytes).hexdigest()
if _core_runtime_sha != EXPECTED_CORE_BLOB_SHA:
    raise RuntimeError(f"USE v399 package integrity failure: expected protected core blob sha={EXPECTED_CORE_BLOB_SHA}, actual={_core_runtime_sha}")

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
        "loneliness": bool(re.search(r"\b(?:loneliness|lonely|alone|isolat|disconnected|belonging|connection)\b", q)),
        "grief": bool(re.search(r"\b(?:grief|grieving|bereavement|bereaved|loss|death|died|dying|loved one)\b", q)),
        "risk": bool(re.search(r"\b(?:suicid|self-harm|overdose|abuse|coercion|immediate danger|unsafe|threatened)\b", q)),
        "meaning": bool(re.search(r"\b(?:meaning|understanding|perspective|wisdom|why|purpose|identity|continuity|spiritual|afterlife|belief|loneliness|lonely|despair|emptiness)\b", q)),
        "transition": bool(re.search(r"\b(?:crossroads|major change|change in my life|life transition|transition|new chapter|what comes next|what happens next|starting over|beginning again|moving forward|identity shift|uncertain what comes next)\b", q)),
        "explicit_framework": bool(re.search(r"\b(?:spiritual|spirituality|religious|religion|mystical|mysticism|afterlife|reincarnation|soul|astrology|tarot|starseed)\b", q)),
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
        "worldview": bool(re.search(r"\b(?:spiritual|spirituality|religious|religion|mystical|mysticism|afterlife|reincarnation|soul|sacred|transcenden|starseed)\b", text)),
        "lived_experience": bool(re.search(r"\b(?:experience|lived|personal|human|everyday|relationships|routine|role|journey|navigate|navigating|felt|feeling|living with)\b", text)),
        "practical_reflection": bool(re.search(r"\b(?:reflect|reflection|notice|naming|journal|practice|grounding|orientation|practical|everyday|attention)\b", text)),
        "transition": bool(re.search(r"\b(?:transition|crossroads|change|new chapter|starting over|moving forward|turning point|reorientation|uncertainty|in-between|before and after|rebuild|reorient|adapt)\b", text)),
    }


def _select_loneliness_primary(docs, profile):
    ranked = []
    for index, doc in enumerate(docs):
        title = _normalize_title(doc.get("title") or "")
        url = str(doc.get("url") or doc.get("canonical_url") or "").strip()
        if not title or not re.match(r"^https?://\S+$", url, re.I):
            continue
        evidence = _role_evidence(doc)
        score = 0
        score += 35 if evidence["existential_loneliness"] else 0
        score += 10 if evidence["lived_experience"] else 0
        score += 8 if evidence["meaning"] else 0
        score += 4 if evidence["practical_reflection"] else 0
        if evidence["worldview"] and not profile.get("explicit_framework"):
            score -= 25
        if not profile.get("explicit_framework") and re.search(r"\b(?:starseed|afterlife|reincarnation|higher-order intelligence)\b", title + " " + str(doc.get("text") or ""), re.I):
            score -= 30
        if score > 0:
            ranked.append((score, index, doc))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return ranked[0][2] if ranked else None


def _candidate_loneliness_role(doc: dict, profile: dict):
    evidence = _role_evidence(doc)
    if evidence["transition"] and not evidence["existential_loneliness"]:
        return "transition", "a route into change, uncertainty, and reorientation", 18
    if evidence["grounded"] and not evidence["existential_loneliness"]:
        return "grounded", "a grounded or research-oriented route into the experience", 15
    if evidence["meaning"] and not evidence["existential_loneliness"]:
        return "meaning", "a route into meaning, perspective, and ways of understanding loneliness", 14
    if evidence["continuity"] and not evidence["existential_loneliness"]:
        return "continuity", "a route into connection, belonging, and what may endure", 12
    if evidence["practical_reflection"] and not evidence["existential_loneliness"]:
        return "reflection", "a reflective route into staying with the experience", 10
    return "other", "another perspective on loneliness", 2


def _select_loneliness_secondaries(docs, primary_title, profile, limit=2):
    seen = {_normalize_title(primary_title).casefold()}
    ranked = []
    for index, doc in enumerate(docs):
        title = _normalize_title(doc.get("title") or "")
        if not title or title.casefold() in seen:
            continue
        role_key, role_text, score = _candidate_loneliness_role(doc, profile)
        if role_key == "other":
            continue
        if not profile.get("explicit_framework") and re.search(r"\b(?:starseed|afterlife|reincarnation|higher-order intelligence)\b", title + " " + str(doc.get("text") or ""), re.I):
            continue
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


def _evidence_boundary_note(docs, profile):
    has_science = any(re.search(r"\b(?:scientific|science|psychological|neuroscientific|clinical|research)\b", str(doc.get("text") or ""), re.I) for doc in docs)
    has_spiritual = any(re.search(r"\b(?:spiritual|soul|afterlife|religious|mystical|sacred|transcenden)\b", str(doc.get("text") or ""), re.I) for doc in docs)
    if has_science and has_spiritual:
        return "The Archive holds different ways of understanding loneliness without requiring them to become one certainty."
    if has_spiritual:
        return "Where the material turns toward spiritual or afterlife possibilities, those are perspectives offered by the work rather than established facts you need to accept."
    return "The material can open a way into the question without deciding in advance what loneliness must mean."


def _build_loneliness_answer(user_query, primary, docs):
    profile = _query_profile(user_query)
    title = _normalize_title(primary.get("title") or "")
    url = str(primary.get("url") or primary.get("canonical_url") or "").strip()
    if not title or not re.match(r"^https?://\S+$", url, re.I):
        return ""
    secondaries = _select_loneliness_secondaries(docs, title, profile)
    sections = [
        "Loneliness can be difficult to name because it is not always only about being physically alone. It can touch belonging, connection, meaning, and the sense of being seen or understood.",
        f"A gentle place to begin is [{title}]({url}).",
        _evidence_boundary_note(docs, profile),
    ]
    if secondaries:
        role_sentences = [
            f"[{_normalize_title(item['doc'].get('title') or '')}]({str(item['doc'].get('url') or item['doc'].get('canonical_url') or '').strip()}) — {item['role_text']}."
            for item in secondaries
        ]
        sections.append("From there, the Archive opens a few different ways into the question:\n\n" + "\n\n".join(role_sentences))
    sections.append("You do not have to turn loneliness into a diagnosis or a final explanation. A useful piece can simply give you another language for noticing what the experience is asking you to consider.")
    return "\n\n".join(sections)


def _v399_finalize(*args, **kwargs):
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
    print(f"USE v399 runtime hook: query_present={bool(user_query)}, intent={intent!r}, docs={len(docs)}, recommendation={recommendation_question}, profile={profile}")
    if user_query and recommendation_question:
        if profile.get("grief"):
            primary = use_core._adjudicate_recommendation_resource(docs, user_query) if docs else None
            if primary:
                return _original_generate_llm_response(*args, **kwargs)
        if profile.get("loneliness"):
            primary = _select_loneliness_primary(docs, profile)
            if primary:
                answer = _build_loneliness_answer(user_query, primary, docs)
                if answer:
                    print(f"USE v399 runtime hook: loneliness interception=ACTIVE primary='{_normalize_title(primary.get('title') or '')}'")
                    return answer
        return _original_generate_llm_response(*args, **kwargs)
    return _original_generate_llm_response(*args, **kwargs)


app = use_core.app
app.title = f"Find Your Way (USE) Navigation Engine {APP_VERSION}"
print(f"USE v399 GUIDE BUILD IDENTITY: build_id={CANONICAL_BUILD_ID}, version={APP_VERSION}, fingerprint={DEPLOYMENT_FINGERPRINT}, source_sha256={RUNTIME_SOURCE_SHA256}, core_blob_sha256={_core_runtime_sha}")
use_core.APP_VERSION = APP_VERSION
use_core.DEPLOYMENT_FINGERPRINT = DEPLOYMENT_FINGERPRINT
use_core.CANONICAL_BUILD_ID = CANONICAL_BUILD_ID
use_core.RUNTIME_SOURCE_SHA256 = RUNTIME_SOURCE_SHA256
use_core.EXPECTED_CORE_BLOB_SHA = EXPECTED_CORE_BLOB_SHA
use_core.generate_llm_response = _v399_finalize
