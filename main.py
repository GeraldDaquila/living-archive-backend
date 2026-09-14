# USE PRODUCTION VERSION: v413 — structural role-plan adjudication and role-specific recovery
import hashlib
import importlib
import re
from pathlib import Path

APP_VERSION = "v413"
DEPLOYMENT_FINGERPRINT = "USE-v413-structural-role-plan-adjudication"
CANONICAL_BUILD_ID = "USE-BUILD-v413-structural-role-plan-adjudication"
EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"

_MAIN_PATH = Path(__file__).resolve()
_CORE_PATH = _MAIN_PATH.with_name("use_core.py")
RUNTIME_SOURCE_SHA256 = hashlib.sha256(_MAIN_PATH.read_bytes()).hexdigest()
if not _CORE_PATH.exists():
    raise RuntimeError("USE v413 package integrity failure: use_core.py is missing.")
_core_bytes = _CORE_PATH.read_bytes()
_core_runtime_sha = hashlib.sha1(f"blob {len(_core_bytes)}\0".encode() + _core_bytes).hexdigest()
if _core_runtime_sha != EXPECTED_CORE_BLOB_SHA:
    raise RuntimeError(f"USE v413 package integrity failure: expected protected core blob sha={EXPECTED_CORE_BLOB_SHA}, actual={_core_runtime_sha}")

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
    """Choose complementary dimensions first, before choosing a resource."""
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


def _secondary_role_candidates(doc: dict, target_roles=None):
    e = _role_evidence(doc)
    if e["acute_risk"] or e["title_risk"]:
        return []
    if e["title_loneliness"] and e["direct_loneliness"]:
        return []
    allowed = set(target_roles or ())
    candidates = []
    if (not allowed or "grounded" in allowed) and e["grounded"] and _role_content_hits(doc, "grounded") >= 2:
        candidates.append(("grounded", "a grounded or research-oriented route into the experience", 30))
    if (not allowed or "meaning" in allowed) and e["meaning"] and _role_content_hits(doc, "meaning") >= 2:
        candidates.append(("meaning", "a route into meaning, perspective, and ways of understanding the experience", 28))
    if (not allowed or "reflection" in allowed) and e["practical_reflection"] and _role_content_hits(doc, "reflection") >= 2:
        candidates.append(("reflection", "a reflective route into staying with the experience", 24))
    if (not allowed or "belonging" in allowed) and e["belonging_connection"] and _role_content_hits(doc, "belonging") >= 2:
        candidates.append(("belonging", "a route into connection and belonging", 22))
    if (not allowed or "transition" in allowed) and e["transition"] and _role_content_hits(doc, "transition") >= 2:
        candidates.append(("transition", "a route into change, uncertainty, and reorientation", 22))
    if (not allowed or "continuity" in allowed) and _role_content_hits(doc, "continuity") >= 2:
        candidates.append(("continuity", "a route into continuity, remembrance, and what may endure", 22))
    if (not allowed or "lived" in allowed) and e["title_life"] and e["lived_experience"] and _role_content_hits(doc, "lived") >= 2:
        candidates.append(("lived", "a broader route into the lived human dimensions around the question", 20))
    return candidates


def _secondary_role_quality(doc: dict, role_key: str) -> int:
    e = _role_evidence(doc)
    score = 0
    score += 18 * int(e["grounded"])
    score += 18 * int(e["meaning"])
    score += 12 * int(e["lived_experience"])
    score += 10 * int(e["belonging_connection"])
    score += 8 * int(e["title_meaning"])
    score += 6 * int(e["title_life"])
    score += min(16, _role_content_hits(doc, role_key) * 5)
    if _is_risk_related(doc):
        return -1000
    score -= 18 * int(e["worldview"])
    text = re.sub(r"\s+", " ", str(doc.get("text") or "").strip().casefold())
    if re.search(r"\b(?:recommend|should|must|need to|therapy|treatment|diagnos)\b", text):
        score -= 20
    role_bonus = {"grounded": 22, "meaning": 20, "reflection": 18, "belonging": 16, "transition": 14, "continuity": 16, "lived": 14}
    return score + role_bonus.get(role_key, 0)


def _planned_secondary(doc: dict, target_roles):
    roles = _secondary_role_candidates(doc, target_roles=target_roles)
    ranked = []
    for role_key, role_text, _bonus in roles:
        ranked.append((_secondary_role_quality(doc, role_key), role_key, role_text))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return ranked[0] if ranked and ranked[0][0] >= 60 else None


def _select_structural_secondary(docs, primary_title, profile):
    seen = {_normalize_title(primary_title).casefold()}
    role_plan = _complementary_role_plan(profile)
    role_keys = [role_key for role_key, _query in role_plan]
    candidates = []
    for index, doc in enumerate(docs):
        title = _normalize_title(doc.get("title") or "")
        url = str(doc.get("url") or doc.get("canonical_url") or "").strip()
        if not title or not re.match(r"^https?://\S+$", url, re.I) or title.casefold() in seen:
            continue
        combined = title + " " + str(doc.get("text") or "")
        if not profile.get("explicit_framework") and re.search(r"\b(?:starseed|afterlife|reincarnation|higher-order intelligence)\b", combined, re.I):
            continue
        planned = _planned_secondary(doc, role_keys)
        if planned:
            score, role_key, role_text = planned
            role_position = role_keys.index(role_key)
            candidates.append((role_position, score, index, role_key, role_text, doc))
    candidates.sort(key=lambda item: (item[0], -item[1], item[2]))
    if not candidates:
        return None
    role_position, score, index, role_key, role_text, doc = candidates[0]
    return {"doc": doc, "role_key": role_key, "role_text": role_text, "score": score, "role_position": role_position}


def _recover_structural_complementary_candidates(user_query, profile, existing_docs):
    """Recover evidence for the highest-priority unmet role using core retrieval primitives."""
    if not user_query or profile.get("risk") or not getattr(use_core, "index", None):
        return []
    role_plan = _complementary_role_plan(profile)
    existing_keys = {_resource_key(doc) for doc in existing_docs}
    recovered = []
    recovered_keys = set(existing_keys)
    try:
        for role_key, role_terms in role_plan:
            role_query = f"{user_query} {role_terms}"
            vector = use_core.generate_embedding(role_query)
            if not vector:
                continue
            matches = use_core._query_index(vector, max(getattr(use_core, "RETRIEVAL_TOP_K", 12), 80))
            role_candidates = []
            local_seen = set(existing_keys)
            for semantic_score, match_id_value, metadata in matches:
                if not isinstance(metadata, dict):
                    continue
                key = _resource_key(metadata)
                if not key or key in recovered_keys or key in local_seen:
                    continue
                working = []
                local_append_seen = set()
                use_core._append_unique_resource(working, local_append_seen, metadata)
                if not working:
                    continue
                candidate = working[0]
                planned = _planned_secondary(candidate, [role_key])
                if not planned:
                    continue
                role_candidates.append((planned[0], -float(semantic_score or 0.0), candidate))
                local_seen.add(key)
                if len(role_candidates) >= 6:
                    break
            role_candidates.sort(key=lambda item: (-item[0], item[1], _normalize_title(item[2].get("title") or "").casefold()))
            for _quality, _semantic_rank, candidate in role_candidates[:2]:
                key = _resource_key(candidate)
                if key in recovered_keys:
                    continue
                recovered_keys.add(key)
                recovered.append(candidate)
            print(f"USE v413 complementary-role retrieval: role={role_key!r}, candidates={len(role_candidates)}, admitted={min(2, len(role_candidates))}")
            trial = existing_docs + recovered
            primary = _select_loneliness_primary(trial, profile)
            if primary and _select_structural_secondary(trial, _normalize_title(primary.get("title") or ""), profile):
                break
    except Exception as exc:
        print(f"USE v413 complementary-role retrieval error: {type(exc).__name__}: {exc}")
    return recovered


def _evidence_boundary_note(docs, has_secondary=False):
    has_science = any(re.search(r"\b(?:scientific|science|psychological|neuroscientific|clinical|research)\b", str(doc.get("text") or ""), re.I) for doc in docs)
    has_spiritual = any(re.search(r"\b(?:spiritual|soul|afterlife|religious|mystical|sacred|transcenden)\b", str(doc.get("text") or ""), re.I) for doc in docs)
    if has_secondary:
        if has_science and has_spiritual:
            return "The Archive opens different ways of understanding the question without requiring them to become one certainty."
        return "The Archive offers more than one way into the question, and the routes do different work rather than resolving it into one certainty."
    if has_spiritual:
        return "Where the material turns toward spiritual or afterlife possibilities, those are perspectives offered by the work rather than established facts you need to accept."
    return "This piece offers one way into the question without deciding in advance what the experience must mean."


def _build_structural_companion_answer(user_query, primary, docs, profile):
    title = _normalize_title(primary.get("title") or "")
    url = str(primary.get("url") or primary.get("canonical_url") or "").strip()
    if not title or not re.match(r"^https?://\S+$", url, re.I):
        return ""
    secondary = _select_structural_secondary(docs, title, profile)
    sections = []
    if profile.get("loneliness"):
        sections.append("Loneliness can be difficult to name because it is not always only about being physically alone. It can touch belonging, connection, meaning, and the sense of being seen or understood.")
        sections.append(f"A gentle place to begin is [{title}]({url}).")
    elif profile.get("grief"):
        sections.append("Grief can hold loss, love, meaning, and uncertainty at the same time; it does not need to be reduced to one explanation before you can begin.")
        sections.append(f"A place to begin is [{title}]({url}).")
    elif profile.get("transition"):
        sections.append("A major transition can leave several questions open at once: what is ending, what still matters, and what might come next.")
        sections.append(f"A useful place to begin is [{title}]({url}).")
    elif profile.get("meaning"):
        sections.append("Questions about meaning rarely arrive with a single settled answer. They can open into several different ways of understanding a life and what matters within it.")
        sections.append(f"A useful place to begin is [{title}]({url}).")
    else:
        sections.append(f"A useful place to begin is [{title}]({url}).")
    sections.append(_evidence_boundary_note(docs, has_secondary=bool(secondary)))
    if secondary:
        item = secondary["doc"]
        item_title = _normalize_title(item.get("title") or "")
        item_url = str(item.get("url") or item.get("canonical_url") or "").strip()
        sections.append(f"From a different angle, [{item_title}]({item_url}) offers {secondary['role_text']}." )
    sections.append("You do not have to settle the question all at once. One piece that feels right for today can be enough of a place to begin.")
    return "\n\n".join(sections)


def _v413_finalize(*args, **kwargs):
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
    print(f"USE v413 runtime hook: query_present={bool(user_query)}, intent={intent!r}, docs={len(docs)}, recommendation={recommendation_question}, profile={profile}, args={len(args)}, kwargs={sorted(kwargs.keys())}")
    if user_query and not profile.get("risk"):
        primary = _select_loneliness_primary(docs, profile) if profile.get("loneliness") else None
        if profile.get("loneliness") and primary:
            secondary = _select_structural_secondary(docs, _normalize_title(primary.get("title") or ""), profile)
            if not secondary:
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
            answer = _build_structural_companion_answer(user_query, primary, docs, profile) if primary else ""
            if answer:
                print(f"USE v413 runtime hook: structural navigation=ACTIVE family='loneliness' primary='{_normalize_title(primary.get('title') or '')}' secondary={bool(_select_structural_secondary(docs, _normalize_title(primary.get('title') or ''), profile))}")
                return answer
    return _original_generate_llm_response(*args, **kwargs)


app = use_core.app
app.title = f"Find Your Way (USE) Navigation Engine {APP_VERSION}"
print(f"USE v413 GUIDE BUILD IDENTITY: build_id={CANONICAL_BUILD_ID}, version={APP_VERSION}, fingerprint={DEPLOYMENT_FINGERPRINT}, source_sha256={RUNTIME_SOURCE_SHA256}, core_blob_sha256={_core_runtime_sha}")
use_core.APP_VERSION = APP_VERSION
use_core.DEPLOYMENT_FINGERPRINT = DEPLOYMENT_FINGERPRINT
use_core.CANONICAL_BUILD_ID = CANONICAL_BUILD_ID
use_core.RUNTIME_SOURCE_SHA256 = RUNTIME_SOURCE_SHA256
use_core.EXPECTED_CORE_BLOB_SHA = EXPECTED_CORE_BLOB_SHA
use_core.generate_llm_response = _v413_finalize
