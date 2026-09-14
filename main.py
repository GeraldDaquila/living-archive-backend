# USE PRODUCTION VERSION: v412 — structural complementary role recovery
import hashlib
import importlib
import re
from pathlib import Path

APP_VERSION = "v412"
DEPLOYMENT_FINGERPRINT = "USE-v412-structural-complementary-role-recovery"
CANONICAL_BUILD_ID = "USE-BUILD-v412-structural-complementary-role-recovery"
EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"

_MAIN_PATH = Path(__file__).resolve()
_CORE_PATH = _MAIN_PATH.with_name("use_core.py")
RUNTIME_SOURCE_SHA256 = hashlib.sha256(_MAIN_PATH.read_bytes()).hexdigest()
if not _CORE_PATH.exists():
    raise RuntimeError("USE v412 package integrity failure: use_core.py is missing.")
_core_bytes = _CORE_PATH.read_bytes()
_core_runtime_sha = hashlib.sha1(f"blob {len(_core_bytes)}\0".encode() + _core_bytes).hexdigest()
if _core_runtime_sha != EXPECTED_CORE_BLOB_SHA:
    raise RuntimeError(f"USE v412 package integrity failure: expected protected core blob sha={EXPECTED_CORE_BLOB_SHA}, actual={_core_runtime_sha}")

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
        "loneliness": bool(re.search(r"\b(?:loneliness|lonely|alone|isolat|disconnected|belonging|connection)\b", q)),
        "grief": bool(re.search(r"\b(?:grief|grieving|bereavement|loss|mourning|death of a loved one)\b", q)),
        "transition": bool(re.search(r"\b(?:crossroads|transition|turning point|new chapter|starting over|uncertain what comes next|major change)\b", q)),
        "meaning": bool(re.search(r"\b(?:meaning|purpose|what gives life meaning|sense of purpose)\b", q)),
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
        "transition": bool(re.search(r"\b(?:transition|crossroads|change|new chapter|starting over|moving forward|turning point|reorientation|uncertainty|in-between|before and after|rebuild|reorient|adapt)\b", corpus)),
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


def _complementary_role_plan(profile: dict):
    """Choose generic complementary dimensions before choosing a resource.

    This is the structural seam absent from v411: a visitor need establishes
    role slots first; retrieval then supplies canonical evidence for those
    slots. No resource title or URL is hard-coded here.
    """
    if profile.get("loneliness"):
        return [
            ("belonging", "belonging connection relationships community companionship being seen understood social connection"),
            ("meaning", "meaning purpose perspective wisdom understanding sense-making interpretation"),
            ("grounded", "research science psychological social evidence empirical"),
        ]
    if profile.get("grief"):
        return [
            ("meaning", "meaning purpose perspective reflection wisdom"),
            ("continuity", "continuity connection remembrance relationship what endures"),
            ("grounded", "research psychological social scientific evidence"),
        ]
    if profile.get("transition"):
        return [
            ("transition", "change crossroads uncertainty reorientation new chapter starting over"),
            ("meaning", "meaning purpose perspective identity understanding"),
            ("grounded", "research psychological evidence adaptation"),
        ]
    if profile.get("meaning"):
        return [
            ("meaning", "meaning purpose perspective wisdom sense-making interpretation"),
            ("grounded", "research evidence psychological scientific understanding"),
            ("lived", "human experience reflection everyday life"),
        ]
    return [
        ("grounded", "research evidence psychological social understanding"),
        ("meaning", "meaning purpose perspective interpretation wisdom"),
        ("reflection", "reflection noticing practice attention lived experience"),
    ]


def _role_content_hits(doc: dict, role_key: str) -> int:
    role_terms = {
        "belonging": ("belonging", "connection", "relationship", "community", "companionship", "being seen", "being understood", "social connection"),
        "meaning": ("meaning", "purpose", "perspective", "wisdom", "understanding", "sense-making", "interpretation"),
        "grounded": ("research", "science", "scientific", "psychological", "clinical", "evidence", "empirical"),
        "continuity": ("continuity", "remembrance", "connection", "endure", "relationship"),
        "transition": ("transition", "crossroads", "change", "reorientation", "new chapter", "uncertainty", "rebuild"),
        "lived": ("experience", "personal", "human", "everyday", "journey", "felt", "living with"),
        "reflection": ("reflect", "reflection", "notice", "naming", "journal", "practice", "attention"),
    }
    text = re.sub(r"\s+", " ", str(doc.get("text") or "").strip().casefold())
    return sum(1 for term in role_terms.get(role_key, ()) if re.search(rf"\b{re.escape(term)}\b", text))


def _secondary_role_candidates(doc: dict):
    e = _role_evidence(doc)
    # A second resource may mention the same experience; what matters is that
    # its primary role is different. Exclude a true primary-topic duplicate,
    # not every resource that happens to mention the word loneliness.
    if e["acute_risk"] or e["title_risk"]:
        return []
    if e["title_loneliness"] and e["direct_loneliness"]:
        return []
    candidates = []
    if e["grounded"] and _role_content_hits(doc, "grounded") >= 1:
        candidates.append(("grounded", "a grounded or research-oriented route into the experience", 30))
    if e["meaning"] and _role_content_hits(doc, "meaning") >= 1:
        candidates.append(("meaning", "a route into meaning, perspective, and ways of understanding the experience", 28))
    if e["practical_reflection"] and _role_content_hits(doc, "reflection") >= 1:
        candidates.append(("reflection", "a reflective route into staying with the experience", 24))
    if e["belonging_connection"] and _role_content_hits(doc, "belonging") >= 1:
        candidates.append(("belonging", "a route into connection and belonging", 22))
    if e["transition"] and _role_content_hits(doc, "transition") >= 1:
        candidates.append(("transition", "a route into change, uncertainty, and reorientation", 22))
    if e["title_meaning"] and _role_content_hits(doc, "meaning") >= 1:
        candidates.append(("meaning_title", "a broader route into meaning and perspective", 18))
    if e["title_life"] and e["lived_experience"] and _role_content_hits(doc, "lived") >= 1:
        candidates.append(("human", "a broader route into the lived human dimensions around the question", 20))
    return candidates


def _secondary_role_quality(doc: dict, role_key: str) -> int:
    e = _role_evidence(doc)
    text = re.sub(r"\s+", " ", str(doc.get("text") or "").strip().casefold())
    score = 0
    score += 18 * int(e["grounded"])
    score += 18 * int(e["meaning"])
    score += 12 * int(e["lived_experience"])
    score += 10 * int(e["belonging_connection"])
    score += 8 * int(e["title_meaning"])
    score += 6 * int(e["title_life"])
    score += min(12, _role_content_hits(doc, role_key) * 4)
    if _is_risk_related(doc):
        return -1000
    score -= 18 * int(e["worldview"])
    if re.search(r"\b(?:recommend|should|must|need to|therapy|treatment|diagnos)\b", text):
        score -= 20
    if role_key == "grounded" and e["grounded"]: score += 20
    if role_key == "meaning" and e["meaning"]: score += 18
    if role_key == "reflection" and e["practical_reflection"]: score += 16
    if role_key == "belonging" and e["belonging_connection"]: score += 12
    if role_key == "transition" and e["transition"]: score += 12
    if role_key == "meaning_title" and e["title_meaning"]: score += 12
    if role_key == "human" and e["lived_experience"] and e["title_life"]: score += 16
    return score


def _select_loneliness_secondaries(docs, primary_title, profile, limit=1):
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
            if role_quality < 36:
                continue
            candidates.append((role_quality + role_bonus, index, role_key, role_text, doc))
    candidates.sort(key=lambda item: (-item[0], item[1]))
    selected = []
    roles = set()
    for score, index, role_key, role_text, doc in candidates:
        if role_key in roles:
            continue
        roles.add(role_key)
        selected.append({"doc": doc, "role_key": role_key, "role_text": role_text, "score": score})
        if len(selected) >= limit:
            break
    return selected


def _recover_structural_complementary_candidates(user_query, profile, existing_docs):
    """Recover evidence for an unfilled role using the protected core retrieval primitives.

    This is the structural repair: complementary role planning happens before
    visitor-facing construction, and retrieval is expanded only for an unmet
    role. The same canonical index, embedding model, and canonical-resource
    admission helper used by use_core remain authoritative.
    """
    if not user_query or profile.get("risk") or not getattr(use_core, "index", None):
        return []

    role_plan = _complementary_role_plan(profile)
    existing_keys = {_resource_key(doc) for doc in existing_docs}
    recovered = []
    recovered_keys = set(existing_keys)

    try:
        for role_key, role_terms in role_plan[:2]:
            role_query = f"{user_query} {role_terms}"
            vector = use_core.generate_embedding(role_query)
            if not vector:
                continue
            matches = use_core._query_index(vector, max(getattr(use_core, "RETRIEVAL_TOP_K", 12), 80))
            role_seen = 0
            for semantic_score, match_id_value, metadata in matches:
                if not isinstance(metadata, dict):
                    continue
                key = _resource_key(metadata)
                if not key or key in recovered_keys:
                    continue
                working = []
                local_seen = set()
                use_core._append_unique_resource(working, local_seen, metadata)
                if not working:
                    continue
                candidate = working[0]
                recovered_keys.add(key)
                recovered.append(candidate)
                role_seen += 1
                if role_seen >= 4:
                    break
            print(f"USE v412 complementary-role retrieval: role={role_key!r}, recovered={role_seen}")
            if recovered:
                # One bounded recovery role is normally enough; the selector
                # can call the next role only if the first did not yield a usable
                # differentiated resource.
                trial = existing_docs + recovered
                primary = _select_loneliness_primary(trial, profile)
                if primary and _select_loneliness_secondaries(trial, _normalize_title(primary.get("title") or ""), profile, limit=1):
                    break
    except Exception as exc:
        print(f"USE v412 complementary-role retrieval error: {type(exc).__name__}: {exc}")

    return recovered


def _evidence_boundary_note(docs, has_secondary=False):
    has_science = any(re.search(r"\b(?:scientific|science|psychological|neuroscientific|clinical|research)\b", str(doc.get("text") or ""), re.I) for doc in docs)
    has_spiritual = any(re.search(r"\b(?:spiritual|soul|afterlife|religious|mystical|sacred|transcenden)\b", str(doc.get("text") or ""), re.I) for doc in docs)
    if has_secondary:
        if has_science and has_spiritual:
            return "The Archive opens different ways of understanding loneliness without requiring them to become one certainty."
        return "The Archive offers more than one way into the question, and the routes do different work rather than resolving it into one certainty."
    if has_spiritual:
        return "Where the material turns toward spiritual or afterlife possibilities, those are perspectives offered by the work rather than established facts you need to accept."
    return "This piece offers one way into the question without deciding in advance what loneliness must mean."


def _build_loneliness_answer(user_query, primary, docs):
    title = _normalize_title(primary.get("title") or "")
    url = str(primary.get("url") or primary.get("canonical_url") or "").strip()
    if not title or not re.match(r"^https?://\S+$", url, re.I):
        return ""
    profile = _query_profile(user_query)
    secondaries = _select_loneliness_secondaries(docs, title, profile, limit=1)
    sections = [
        "Loneliness can be difficult to name because it is not always only about being physically alone. It can touch belonging, connection, meaning, and the sense of being seen or understood.",
        f"A gentle place to begin is [{title}]({url}).",
        _evidence_boundary_note(docs, has_secondary=bool(secondaries)),
    ]
    if secondaries:
        item = secondaries[0]
        item_title = _normalize_title(item["doc"].get("title") or "")
        item_url = str(item["doc"].get("url") or item["doc"].get("canonical_url") or "").strip()
        sections.append(f"Another route into the question is [{item_title}]({item_url}) — {item['role_text']}.")
    sections.append("You do not have to turn loneliness into a diagnosis or a final explanation. A useful piece can simply give you another language for noticing what the experience is asking you to consider.")
    return "\n\n".join(sections)


def _v412_finalize(*args, **kwargs):
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
    print(f"USE v412 runtime hook: query_present={bool(user_query)}, intent={intent!r}, docs={len(docs)}, recommendation={recommendation_question}, profile={profile}, args={len(args)}, kwargs={sorted(kwargs.keys())}")
    if user_query and profile.get("loneliness") and not profile.get("risk"):
        primary = _select_loneliness_primary(docs, profile)
        if primary:
            secondaries = _select_loneliness_secondaries(docs, _normalize_title(primary.get("title") or ""), profile, limit=1)
            if not secondaries:
                recovered = _recover_structural_complementary_candidates(user_query, profile, docs)
                if recovered:
                    merged = list(docs)
                    merged_keys = {_resource_key(doc) for doc in merged}
                    for document in recovered:
                        if _resource_key(document) not in merged_keys:
                            merged.append(document)
                            merged_keys.add(_resource_key(document))
                    docs = merged
            primary = _select_loneliness_primary(docs, profile)
            answer = _build_loneliness_answer(user_query, primary, docs) if primary else ""
            if answer:
                secondaries = _select_loneliness_secondaries(docs, _normalize_title(primary.get("title") or ""), profile, limit=1)
                print(f"USE v412 runtime hook: loneliness interception=ACTIVE primary='{_normalize_title(primary.get('title') or '')}' secondary_count={len(secondaries)} recommendation_classifier={recommendation_question}")
                return answer
    return _original_generate_llm_response(*args, **kwargs)


app = use_core.app
app.title = f"Find Your Way (USE) Navigation Engine {APP_VERSION}"
print(f"USE v412 GUIDE BUILD IDENTITY: build_id={CANONICAL_BUILD_ID}, version={APP_VERSION}, fingerprint={DEPLOYMENT_FINGERPRINT}, source_sha256={RUNTIME_SOURCE_SHA256}, core_blob_sha256={_core_runtime_sha}")
use_core.APP_VERSION = APP_VERSION
use_core.DEPLOYMENT_FINGERPRINT = DEPLOYMENT_FINGERPRINT
use_core.CANONICAL_BUILD_ID = CANONICAL_BUILD_ID
use_core.RUNTIME_SOURCE_SHA256 = RUNTIME_SOURCE_SHA256
use_core.EXPECTED_CORE_BLOB_SHA = EXPECTED_CORE_BLOB_SHA
use_core.generate_llm_response = _v412_finalize
