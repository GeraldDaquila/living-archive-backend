# USE PRODUCTION VERSION: v393 — generalized complementary visitor navigation
# v391 remains the protected production baseline; this wrapper changes only visitor-facing
# recommendation role selection/construction. Protected use_core.py is unchanged.
import hashlib
import importlib
import re
from pathlib import Path

APP_VERSION = "v393"
DEPLOYMENT_FINGERPRINT = "USE-v393-generalized-complementary-navigation"
CANONICAL_BUILD_ID = "USE-BUILD-v393-generalized-complementary-navigation"
EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"

_MAIN_PATH = Path(__file__).resolve()
_CORE_PATH = _MAIN_PATH.with_name("use_core.py")
RUNTIME_SOURCE_SHA256 = hashlib.sha256(_MAIN_PATH.read_bytes()).hexdigest()
if not _CORE_PATH.exists():
    raise RuntimeError("USE v393 package integrity failure: use_core.py is missing.")
_core_bytes = _CORE_PATH.read_bytes()
_core_runtime_sha = hashlib.sha1(f"blob {len(_core_bytes)}\0".encode() + _core_bytes).hexdigest()
if _core_runtime_sha != EXPECTED_CORE_BLOB_SHA:
    raise RuntimeError(f"USE v393 package integrity failure: expected protected core blob sha={EXPECTED_CORE_BLOB_SHA}, actual={_core_runtime_sha}")

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

def _context_blocks_from_kwargs(args, kwargs):
    for key in ("retrieved_context_blocks", "canonical_link_context", "retrieved_context", "context_blocks"):
        if kwargs.get(key):
            return str(kwargs[key])
    for index in (1, 2, 3, 4, 5):
        if len(args) > index and isinstance(args[index], str) and any(k in args[index] for k in ("Title:", "URL:", "Content:")):
            return args[index]
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

def _candidate_role(doc: dict, profile: dict) -> tuple[str, str, int]:
    evidence = _role_evidence(doc)
    score = 0
    role_key = "other"
    role_text = "another perspective on the question"
    if evidence["existential_loneliness"]:
        role_key = "existential_loneliness"
        role_text = "loneliness, emptiness, and existential dimensions of the question"
        score += 14
    if evidence["continuity"] and role_key == "other":
        role_key = "continuity"
        role_text = "continuity, connection, and what may endure"
    if evidence["continuity"]:
        score += 12
    if evidence["lived_loss"] and role_key == "other":
        role_key = "lived_loss"
        role_text = "the lived experience of grief, loss, and mortality"
    if evidence["lived_loss"]:
        score += 10
    if evidence["meaning"] and role_key == "other":
        role_key = "meaning"
        role_text = "meaning, perspective, and ways of understanding the experience"
    if evidence["meaning"]:
        score += 7
    if evidence["grounded"] and role_key == "other":
        role_key = "grounded"
        role_text = "a grounded or research-oriented way of looking at the question"
    if evidence["grounded"]:
        score += 5
    if evidence["lived_experience"] and role_key == "other":
        role_key = "lived_experience"
        role_text = "the lived, human experience of the question"
    if evidence["lived_experience"]:
        score += 4
    if evidence["practical_reflection"] and role_key == "other":
        role_key = "practical_reflection"
        role_text = "a reflective or practical way of staying with the question"
    if evidence["practical_reflection"]:
        score += 3
    if evidence["worldview"] and not profile.get("explicit_framework"):
        score -= 4
    return role_key, role_text, score

def _select_secondary_pathways(docs: list, primary_title: str, profile: dict, limit: int = 2) -> list:
    seen = {_normalize_title(primary_title).casefold()}
    ranked = []
    for index, doc in enumerate(docs):
        title = _normalize_title(doc.get("title") or "")
        if not title or title.casefold() in seen:
            continue
        if profile.get("sensitive") and not profile.get("explicit_framework") and not profile.get("risk") and _is_acute_risk_resource(doc):
            continue
        role_key, role_text, score = _candidate_role(doc, profile)
        if profile.get("grief") and role_key == "lived_loss" and score < 10:
            continue
        if profile.get("grief") and role_key == "continuity":
            score += 4
        if profile.get("grief") and role_key == "existential_loneliness":
            score += 5
        if profile.get("meaning") and role_key == "meaning":
            score += 3
        if profile.get("sensitive") and not profile.get("explicit_framework") and not profile.get("risk"):
            if re.search(r"\b(?:afterlife|reincarnation)\b", str(doc.get("text") or ""), re.I):
                score -= 4
        if score > 0:
            ranked.append((score, index, role_key, role_text, doc))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    selected = []
    role_keys = set()
    for item in ranked:
        if item[2] in role_keys:
            continue
        role_keys.add(item[2])
        selected.append({"doc": item[4], "role_key": item[2], "role_text": item[3], "score": item[0]})
        if len(selected) >= limit:
            break
    return selected

def _evidence_boundary_note(docs: list, profile: dict) -> str:
    has_science = any(re.search(r"\b(?:scientific|science|psychological|neuroscientific|clinical|research)\b", str(doc.get("text") or ""), re.I) for doc in docs)
    has_spiritual = any(re.search(r"\b(?:spiritual|soul|afterlife|religious|mystical|sacred|transcenden)\b", str(doc.get("text") or ""), re.I) for doc in docs)
    if has_science and has_spiritual:
        return "It brings different ways of understanding the question into the same conversation without requiring them to become a single certainty."
    if has_spiritual:
        return "Where the material turns toward spiritual or afterlife possibilities, those are perspectives offered by the work rather than established facts you need to accept."
    if profile.get("meaning"):
        return "It offers a way into the question while leaving room to distinguish what is known from what remains interpretation, possibility, or personal meaning."
    return "It offers a place to begin without asking the material to provide more certainty than it can support."

def _article_role_phrase(role_text: str) -> str:
    mapping = {
        "continuity, connection, and what may endure": "a route into continuity, connection, and what may endure",
        "loneliness, emptiness, and existential dimensions of the question": "a route into loneliness, emptiness, and the existential dimensions of the question",
        "the lived experience of grief, loss, and mortality": "a route into the lived experience of grief, loss, and mortality",
        "meaning, perspective, and ways of understanding the experience": "a route into meaning, perspective, and ways of understanding the experience",
        "a grounded or research-oriented way of looking at the question": "a grounded or research-oriented route into the question",
        "the lived, human experience of the question": "a route into the lived, human experience of the question",
        "a reflective or practical way of staying with the question": "a route into reflective or practical ways of staying with the question",
        "another perspective on the question": "another perspective on the question",
    }
    return mapping.get(role_text, role_text)

def _build_sensitive_recommendation_answer(user_query: str, primary: dict, docs: list) -> str:
    profile = _query_profile(user_query)
    title = _normalize_title(primary.get("title") or "")
    url = str(primary.get("url") or primary.get("canonical_url") or "").strip()
    if not title or not re.match(r"^https?://\S+$", url, re.I):
        return ""
    secondaries = _select_secondary_pathways(docs, title, profile)
    if profile.get("grief"):
        opening = "When you are grieving the death of someone you love, there may be no easy place to begin. Grief can bring pain, longing, questions, and uncertainty all at once."
    elif profile.get("sensitive"):
        opening = "A question like this can be difficult to hold in one frame, so it can help to have a clear place to begin while leaving room for the question to remain open."
    else:
        opening = "A question like this can benefit from a clear place to begin and room for the question to remain open."
    sections = [opening, f"A useful doorway is [{title}]({url}).", _evidence_boundary_note(docs, profile)]
    if secondaries:
        role_sentences = [f"[{_normalize_title(item['doc'].get('title') or '')}]({str(item['doc'].get('url') or item['doc'].get('canonical_url') or '').strip()}) — {_article_role_phrase(item['role_text'])}." for item in secondaries if item.get("doc")]
        if role_sentences:
            sections.append("From there, the Archive opens a few distinct paths:" + "\n\n" + "\n\n".join(role_sentences))
    if profile.get("risk"):
        sections.append("The Archive can offer reflection and orientation, but where there is immediate danger or coercion, real-world safety and trusted human support matter more than reflection alone.")
    elif profile.get("grief"):
        sections.append("There is no need to settle the grief all at once. One piece that feels right for today can be enough of a place to begin.")
    elif profile.get("sensitive"):
        sections.append("You do not need to turn the question into an answer all at once. A piece that opens a useful perspective can be enough of a place to begin.")
    else:
        sections.append("Take what is useful, leave what is not, and let the question remain open where it needs to.")
    return "\n\n".join(section for section in sections if section)

def _transition_profile(user_query: str) -> dict:
    q = re.sub(r"\s+", " ", str(user_query or "").strip().casefold())
    return {"transition": bool(re.search(r"\b(?:major change|change in (?:my|our) life|life change|life transition|transition|new chapter|what comes next|what comes after|lost since|since .*change|after .*change|starting over|beginning again|begin again|moving forward|identity|uncertain what comes next)\b", q)), "meaning": bool(re.search(r"\b(?:meaning|purpose|why am i here|what is the point|what does it all mean|make sense|understand the experience)\b", q)), "open_question": bool(re.search(r"\b(?:how do i make sense|what do people believe|what are the possibilities|is there more|what happens after|what if there is no|i don't know what to believe|not sure what to believe|does anyone know|can anyone know|different perspectives|many perspectives|open question|no single answer|not sure|uncertain)\b", q)), "explicit_framework": bool(re.search(r"\b(?:spiritual|spirituality|religious|religion|mystical|mysticism|afterlife|reincarnation|starseed|ascension|awakening|kundalini|soul|indigenous|traditional wisdom|ai|artificial intelligence|astrology|tarot|political|capitalism|socialism)\b", q))}

def _transition_evidence_fit(doc: dict, query: str):
    title = _normalize_title(doc.get("title") or "").casefold(); text = re.sub(r"\s+", " ", str(doc.get("text") or "").strip()).casefold(); hay = f"{title} {text}"
    clusters = {"transition": bool(re.search(r"\b(?:transition|change|chapter|starting over|moving forward|uncertain|flux|reorientation|turning point|new beginning|life change|before and after|crossroads|in-between|rebuild|reorient|adjust|adapt)\b", hay)), "meaning": bool(re.search(r"\b(?:meaning|purpose|identity|sensemaking|sense-making|making sense|what it means)\b", hay)), "experience": bool(re.search(r"\b(?:experience|lived|personal|human|everyday|relationships|routine|role|journey|navigate|navigating|felt|feeling)\b", hay)), "grounding": bool(re.search(r"\b(?:ground|grounding|practical|reflect|reflection|notice|naming|journal|practice|orientation)\b", hay)), "open": bool(re.search(r"\b(?:perspective|perspectives|possibilit|different views|different approaches|uncertainty|no single answer|question|open|ambiguous|ambiguity)\b", hay)), "worldview": bool(re.search(r"\b(?:spiritual|spirituality|religious|religion|mystical|mysticism|afterlife|reincarnation|soul|astrology|tarot|political|capitalism|socialism)\b", hay)), "belief": bool(re.search(r"\b(?:belief|believe|faith|spiritual|religious|worldview)\b", hay))}
    score = sum(int(clusters[k]) for k in ("transition", "meaning", "experience", "grounding", "open")); q = str(query or "").casefold()
    if re.search(r"\b(?:what comes next|major change|change in my life|life transition|new chapter|lost since|understand the experience|not sure what i believe|without being told what i should feel|without being told what i should believe)\b", q) and (clusters["transition"] or clusters["meaning"] or clusters["experience"]): score += 2
    return score, clusters

def _is_query_aligned_transition_doorway(doc: dict, query: str) -> bool:
    profile = _transition_profile(query)
    if not profile["transition"] or profile["explicit_framework"]: return False
    score, clusters = _transition_evidence_fit(doc, query)
    if clusters["worldview"]: return False
    substantive = int(clusters["transition"]) + int(clusters["meaning"]) + int(clusters["experience"]); contextual = int(clusters["open"]) + int(clusters["grounding"])
    return substantive >= 2 or (substantive >= 1 and contextual >= 1 and score >= 4)

def _transition_doorway_score(doc: dict, query: str) -> int:
    score, clusters = _transition_evidence_fit(doc, query); profile = _transition_profile(query); score *= 5
    if clusters["transition"] and profile["transition"]: score += 8
    if clusters["meaning"] and profile["meaning"]: score += 5
    if clusters["open"] and profile["open_question"]: score += 5
    if clusters["experience"]: score += 3
    if clusters["grounding"]: score += 3
    if clusters["belief"] and profile["open_question"] and not profile["explicit_framework"]: score -= 6
    if clusters["worldview"]: score -= 30
    return score

def _transition_retrieval_strategy(query: str):
    source = getattr(use_core, "_transition_retrieval_strategy", None)
    if callable(source):
        try: retrieved = source(query)
        except Exception: retrieved = []
    else: retrieved = []
    ranked = []; seen = set()
    for doc in list(retrieved or []):
        if not isinstance(doc, dict): continue
        key = str(doc.get("url") or doc.get("canonical_url") or doc.get("title") or "").casefold().rstrip("/")
        if not key or key in seen or not _is_query_aligned_transition_doorway(doc, query): continue
        seen.add(key); ranked.append((_transition_doorway_score(doc, query), doc))
    ranked.sort(key=lambda x: x[0], reverse=True)
    return [doc for _, doc in ranked[:4]]

def _direct_open_transition_response(query: str, docs: list) -> dict:
    if not docs: return {"response": "A possible place to begin is with the transition itself: what changed, what feels uncertain now, and what remains open rather than already decided. The material available here does not establish one particular belief about what your experience means, so the question can remain open while you explore it.", "resources": []}
    primary = docs[0]; title = _normalize_title(primary.get("title") or ""); url = str(primary.get("url") or primary.get("canonical_url") or "").strip()
    if not title or not re.match(r"^https?://\S+$", url, re.I): return {"response": "A possible place to begin is with the transition itself: what changed, what feels uncertain now, and what remains open.", "resources": []}
    return {"response": "A possible place to begin is with the transition itself: a major change can leave what comes next genuinely open, especially while you are still finding your own language for what the experience means. The material surfaced here can offer a lens for that inquiry without requiring you to adopt a particular belief.\n\nOne useful doorway is [" + title + "](" + url + ").", "resources": [{"title": title, "url": url}]}

def _v393_finalize(*args, **kwargs):
    user_query = str(kwargs.get("user_query") or (args[0] if args else "") or "")
    intent = str(kwargs.get("intent") or (args[2] if len(args) > 2 else "") or "")
    raw_context = _context_blocks_from_kwargs(args, kwargs)
    docs = _parse_context_documents(raw_context)
    if not user_query or intent != "TOPICAL_INQUIRY": return _original_generate_llm_response(*args, **kwargs)
    tprofile = _transition_profile(user_query)
    if tprofile["transition"] and tprofile["open_question"] and not tprofile["explicit_framework"]:
        recovered = _transition_retrieval_strategy(user_query)
        aligned = [doc for doc in docs if _is_query_aligned_transition_doorway(doc, user_query)]
        merged = []; seen = set()
        for doc in aligned + recovered:
            key = str(doc.get("url") or doc.get("canonical_url") or doc.get("title") or "").casefold().rstrip("/")
            if key and key not in seen: seen.add(key); merged.append(doc)
        return _direct_open_transition_response(user_query, sorted(merged, key=lambda d: _transition_doorway_score(d, user_query), reverse=True)[:1])
    profile = _query_profile(user_query)
    if (profile.get("sensitive") or profile.get("meaning")) and use_core._is_recommendation_question(user_query):
        primary = use_core._adjudicate_recommendation_resource(docs, user_query) if docs else None
        if primary:
            answer = _build_sensitive_recommendation_answer(user_query, primary, docs)
            if answer: return answer
    return _original_generate_llm_response(*args, **kwargs)

app = use_core.app
app.title = f"Find Your Way (USE) Navigation Engine {APP_VERSION}"
print(f"USE v393 GUIDE BUILD IDENTITY: build_id={CANONICAL_BUILD_ID}, version={APP_VERSION}, fingerprint={DEPLOYMENT_FINGERPRINT}, source_sha256={RUNTIME_SOURCE_SHA256}, core_blob_sha256={_core_runtime_sha}")
use_core.APP_VERSION = APP_VERSION
use_core.DEPLOYMENT_FINGERPRINT = DEPLOYMENT_FINGERPRINT
use_core.CANONICAL_BUILD_ID = CANONICAL_BUILD_ID
use_core.RUNTIME_SOURCE_SHA256 = RUNTIME_SOURCE_SHA256
use_core.EXPECTED_CORE_BLOB_SHA = EXPECTED_CORE_BLOB_SHA
use_core.generate_llm_response = _v393_finalize
