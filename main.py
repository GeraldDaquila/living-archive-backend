# USE PRODUCTION VERSION: v487.57 — LLM capability routing
import hashlib
import importlib
import re
import json
from pathlib import Path
from fastapi import Request
from fastapi.responses import JSONResponse

from specialist_registry import (
    SPECIALIST_PIPE_CONTRACT_VERSION,
    registry_snapshot,
    validate_registry,
)
from relationship_contribution import (
    RELATIONSHIP_CONTRIBUTION_CONTRACT_VERSION,
    RELATIONSHIP_VOICE_POLICY,
    relationship_contract_snapshot,
    validate_relationship_contribution,
)
from relationship_adapter import RelationshipAdapter
from specialist_adapters import (
    SPECIALIST_ADAPTER_CONTRACT_VERSION,
    SpecialistAdapterRegistry,
    adapter_contract_snapshot,
    invoke_specialist,
)

_BASE_MODULE_NAME = "main_v487_28_runtime"
_base = importlib.import_module(_BASE_MODULE_NAME)
use_core = _base.use_core
app = _base.app
_original_guide_handle_query = use_core.handle_query
APP_VERSION = "v487.57"
DEPLOYMENT_FINGERPRINT = "USE-v487.57-asgi-capability-routing"
CANONICAL_BUILD_ID = "USE-BUILD-v487.57-asgi-capability-routing"
EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"
_MAIN_PATH = Path(__file__).resolve()
RUNTIME_SOURCE_SHA256 = hashlib.sha256(_MAIN_PATH.read_bytes()).hexdigest()
use_core.APP_VERSION = APP_VERSION
use_core.DEPLOYMENT_FINGERPRINT = DEPLOYMENT_FINGERPRINT
use_core.CANONICAL_BUILD_ID = CANONICAL_BUILD_ID
use_core.RUNTIME_SOURCE_SHA256 = RUNTIME_SOURCE_SHA256
use_core.EXPECTED_CORE_BLOB_SHA = EXPECTED_CORE_BLOB_SHA
if getattr(_base, "_core_runtime_sha", "") != EXPECTED_CORE_BLOB_SHA:
    raise RuntimeError("USE protected core integrity failure: protected core mismatch.")

validate_registry()
SPECIALIST_CAPABILITY_REGISTRY = registry_snapshot()
SPECIALIST_ADAPTER_REGISTRY = SpecialistAdapterRegistry()
SPECIALIST_ADAPTER_REGISTRY.register(RelationshipAdapter())
SPECIALIST_ADAPTER_DIAGNOSTICS = adapter_contract_snapshot(SPECIALIST_ADAPTER_REGISTRY)
RELATIONSHIP_CONTRIBUTION_DIAGNOSTICS = relationship_contract_snapshot()


# Seeing the Relationship contribution invariant: HRN's human voice is
# preserved by contract. The Guide may integrate it, but does not rewrite it
# merely to impose Guide phrasing.
_relationship_contract_probe = validate_relationship_contribution({
    "status": "CONTRIBUTION",
    "voice_policy": RELATIONSHIP_VOICE_POLICY,
    "human_response": "Sometimes the first thing worth noticing is not whether the relationship is right or wrong, but what happens between you when this particular tension appears.",
    "interpretation": {"focus": "relational pattern"},
    "perspectives": [{"view": "visitor"}, {"view": "relationship"}],
    "movement": {"direction": "perspective"},
    "canonical_candidates": [],
})
if _relationship_contract_probe["voice_policy"] != "preserve_specialist_voice":
    raise RuntimeError("USE v487.52 invariant failed: relational voice-preservation policy lost")
if _relationship_contract_probe["human_response"].startswith("A useful place to begin"):
    raise RuntimeError("USE v487.52 invariant failed: relational contribution was rewritten into Guide voice")

def _normalize_query(text):
    return re.sub(r"\s+", " ", str(text or "").strip().casefold().replace("’", "'").replace("‘", "'").replace("`", "'").replace("–", "-").replace("—", "-"))


_EXPERIENTIAL_STANCE_PATTERNS = (
    r"i(?:\s+am|'m)\s+struggl(?:e|ing)\s+with", r"i\s+struggle\s+with", r"i(?:\s+am|'m)\s+dealing\s+with",
    r"i(?:\s+am|'m)\s+having\s+a\s+hard\s+time\s+with", r"i(?:\s+am|'m)\s+going\s+through",
    r"i(?:\s+am|'m)\s+experiencing", r"i(?:\s+am|'m)\s+feeling", r"i\s+feel",
    r"i(?:\s+am|'m)\s+worried\s+about", r"i(?:\s+am|'m)\s+afraid\s+of",
    r"i(?:\s+am|'m)\s+confused\s+about", r"i(?:\s+am|'m)\s+unsure\s+about",
    r"i(?:\s+am|'m)\s+not\s+sure\s+about", r"i\s+(?:need|want)\s+help\s+with",
)
_EXPERIENTIAL_STATE_TERMS = (
    r"lonelin(?:ess|e)", r"empt(?:iness|y)", r"sad(?:ness|ly)", r"sorrow", r"despair", r"hopeless(?:ness)?",
    r"anxiety", r"anxious", r"fear", r"afraid", r"anger", r"angry", r"resentment", r"shame", r"guilt",
    r"confusion", r"uncertain(?:ty)?", r"isolation", r"isolated", r"disconnection", r"disconnected",
    r"heartbreak", r"breakup", r"betrayal", r"burnout", r"stress", r"overwhelmed", r"grief", r"grieving",
    r"bereavement", r"mourning", r"loss", r"relationship", r"abuse", r"trauma", r"forgiveness", r"letting\s+go",
)


def _has_experiential_stance(q):
    return any(re.search(pattern, q, re.I) for pattern in _EXPERIENTIAL_STANCE_PATTERNS)


def _has_experiential_state(q):
    return any(re.search(rf"\b{pattern}\b", q, re.I) for pattern in _EXPERIENTIAL_STATE_TERMS)


def _has_archive_help_request(q):
    return bool(re.search(r"\b(?:anything|something|something here)\b.{0,100}\b(?:living archive|archive|site|guide)\b.{0,100}\b(?:help|think|start|read|explore|reflect)\b", q, re.I))


_original_weighted_inquiry_profile = _base._weighted_inquiry_profile


def _weighted_inquiry_profile(query):
    q = _normalize_query(query)
    profile = _original_weighted_inquiry_profile(q)
    if _has_experiential_stance(q) or _has_experiential_state(q):
        profile["lived"] = max(float(profile.get("lived", 0.0)), 0.86)
    if _has_archive_help_request(q):
        profile["recommendation"] = max(float(profile.get("recommendation", 0.0)), 0.82)
    return profile


_base._normalize_query = _normalize_query
_base._weighted_inquiry_profile = _weighted_inquiry_profile


def _recommendation_rationale(primary, profile):
    if profile.get("grief"):
        return "I’m recommending this first because it approaches grief and the human search for continuity directly, making it a more immediate place to reflect on the experience of losing someone you love."
    if profile.get("ai_truth"):
        return "I’m recommending this first because it gives you a direct place to examine discernment and the question of how we decide what is actually true."
    return "I’m recommending this first because it offers a direct place to reflect on the question you brought here, without asking you to treat it as the whole answer."


_SUBJECT_STOPWORDS = frozenset({
    "a", "an", "the", "and", "or", "but", "if", "then", "than", "of", "on", "in", "at", "to", "as", "by",
    "for", "from", "with", "into", "through", "there", "here", "this", "that", "these", "those", "is", "are",
    "was", "were", "be", "been", "being", "am", "i", "im", "my", "me", "mine", "myself", "your", "you",
    "yourself", "our", "we", "they", "them", "their", "someone", "somebody", "anyone", "anything", "something",
    "people", "person", "what", "which", "who", "when", "where", "why", "how", "can", "could", "would", "should",
    "may", "might", "will", "do", "does", "did", "doing", "don", "dont", "don't", "not", "no", "know", "sure", "about",
    "help", "think", "thinking", "thought", "question", "questions", "living", "archive", "site", "website", "guide",
    "place", "begin", "start", "first", "read", "reading", "explore", "exploring", "reflect", "reflection", "recommend",
    "recommendation", "suggest", "suggestion", "advice", "advise", "essay", "essays", "article", "articles", "resource",
    "resources", "piece", "pieces", "material", "please", "find", "give", "offer", "tell", "one", "best", "good", "need",
    "want", "looking", "thing", "things", "time", "way", "make", "made", "keep", "still", "feel", "feels", "feeling",
    "care", "caring", "having", "hard", "going", "experiencing", "worried", "worry", "afraid", "confused", "unsure",
    "struggling", "struggle", "dealing", "finding", "it", "its", "all", "very", "just", "really", "more",
    "less", "ever", "often", "sometimes", "now", "today", "something", "anything",
})


def _subject_terms(query):
    q = _normalize_query(query)
    tokens = re.findall(r"[a-z0-9]+", q)
    return tuple(dict.fromkeys(t for t in tokens if len(t) >= 3 and t not in _SUBJECT_STOPWORDS))


def _term_forms(term):
    value = str(term or "").casefold()
    forms = {value}
    if value.endswith("ies") and len(value) > 4:
        forms.add(value[:-3] + "y")
    if value.endswith("ness") and len(value) > 5:
        forms.add(value[:-4])
    if value.endswith("ing") and len(value) > 5:
        forms.add(value[:-3])
    if value.endswith("ed") and len(value) > 5:
        forms.add(value[:-2])
    if value.endswith("es") and len(value) > 4:
        forms.add(value[:-2])
    if value.endswith("s") and len(value) > 4:
        forms.add(value[:-1])
    return {f for f in forms if len(f) >= 3}


def _subject_metrics(query, doc):
    title = str(doc.get("title") or "").casefold()
    text = str(doc.get("text") or doc.get("content") or doc.get("excerpt") or "").casefold()
    terms = _subject_terms(query)
    if not title or not terms:
        return (0, 0, 0, 0, 0)
    title_tokens = set(re.findall(r"[a-z0-9]+", title))
    early = text[:2400]
    early_tokens = set(re.findall(r"[a-z0-9]+", early))
    full_tokens = set(re.findall(r"[a-z0-9]+", text))
    title_hits = sum(bool(_term_forms(term) & title_tokens) for term in terms)
    early_hits = sum(bool(_term_forms(term) & early_tokens) for term in terms)
    full_hits = sum(bool(_term_forms(term) & full_tokens) for term in terms)
    phrase_hits = sum(1 for index in range(len(terms) - 1) if f"{terms[index]} {terms[index + 1]}" in title or f"{terms[index]} {terms[index + 1]}" in early)
    return (min(8, title_hits), min(8, phrase_hits), min(12, early_hits), min(12, full_hits), int(1000 * title_hits / max(1, len(terms))))


_SUBJECT_FAMILIES = {
    "anger": ("anger", "angry", "resentment", "resentful", "irritation", "irritated", "frustration", "frustrated", "rage", "conflict"),
    "loneliness": ("loneliness", "lonely", "isolation", "isolated", "disconnection", "disconnected"),
    "grief": ("grief", "grieving", "bereavement", "mourning", "loss", "lost", "death"),
    "fear": ("fear", "afraid", "anxiety", "anxious", "worry", "worried"),
    "shame": ("shame", "ashamed", "guilt", "guilty"),
    "relationship": ("relationship", "relationships", "partner", "partners", "interpersonal", "marriage", "married", "friendship", "friends", "communication", "boundaries"),
}
_RELATIONAL_PATTERNS = (
    r"\bsomeone i care about\b", r"\bpeople i care about\b", r"\bperson i care about\b", r"\brelationship\b",
    r"\bpartner\b", r"\bloved one\b", r"\bfamily\b", r"\bfriend\b", r"\binterpersonal\b", r"\bwith someone\b", r"\bcare about\b"
)


def _query_frame(query):
    q = _normalize_query(query)
    families = tuple(family for family, terms in _SUBJECT_FAMILIES.items() if any(re.search(rf"\b{re.escape(term)}\b", q) for term in terms))
    return {"families": families, "relational": any(re.search(pattern, q, re.I) for pattern in _RELATIONAL_PATTERNS)}


def _role_evidence(doc):
    title = re.sub(r"\s+", " ", str(doc.get("title") or "").strip().casefold())
    text = re.sub(r"\s+", " ", str(doc.get("text") or doc.get("content") or "").strip().casefold())
    early = text[:1800]
    worldview_pattern = r"\b(?:spiritual|spirituality|religious|religion|mystical|mysticism|afterlife|reincarnation|soul|sacred|transcenden\w*|metaphysics|metaphysical|cosmic|oversoul|ascension|law of one|new earth)\b"
    risk_pattern = r"\b(?:suicid\w*|self-harm|self harm|overdose|acute crisis|crisis intervention|immediate danger)\b"
    abuse_pattern = r"\b(?:abuse|abusive|coercive control|gaslighting)\b"
    worldview_in_title = bool(re.search(worldview_pattern, title))
    worldview_early_hits = len(re.findall(worldview_pattern, early))
    risk_in_title = bool(re.search(risk_pattern, title))
    risk_early_hits = len(re.findall(risk_pattern, early))
    abuse_in_title = bool(re.search(abuse_pattern, title))
    abuse_early_hits = len(re.findall(abuse_pattern, early))
    return {
        "worldview": bool(worldview_in_title or worldview_early_hits >= 2),
        "risk": bool(risk_in_title or risk_early_hits >= 1),
        "abuse": bool(abuse_in_title or abuse_early_hits >= 2),
    }


_base._role_evidence = _role_evidence


def _family_hit_count(text, family):
    tokens = set(re.findall(r"[a-z0-9]+", str(text or "").casefold()))
    return sum(bool(_term_forms(term) & tokens) for term in _SUBJECT_FAMILIES.get(family, ()))


def _contextual_fit(query, doc):
    frame = _query_frame(query)
    title = str(doc.get("title") or "").casefold()
    text = str(doc.get("text") or doc.get("content") or doc.get("excerpt") or "").casefold()
    early = text[:3000]
    family_title = sum(_family_hit_count(title, f) > 0 for f in frame["families"])
    family_early = sum(_family_hit_count(early, f) > 0 for f in frame["families"])
    relational_title = _family_hit_count(title, "relationship")
    relational_early = _family_hit_count(early, "relationship")
    relational = frame["relational"]
    combined = relational and ((family_title > 0 and relational_title > 0) or (family_early > 0 and relational_early > 0))
    return (family_title, family_early, int(combined), relational_title, relational_early)


def _relevance_level(metrics, *, allow_full_content=False):
    title_hits, phrase_hits, early_hits, full_hits, _ = metrics
    if title_hits >= 1 or phrase_hits >= 1 or (early_hits >= 2 and full_hits >= 2):
        return 2
    if allow_full_content and full_hits >= 1:
        return 2
    if full_hits >= 1:
        return 1
    return 0


def _eligible_outward_doc(query, doc, profile, *, min_relevance=2):
    if not isinstance(doc, dict):
        return False
    title = str(doc.get("title") or "").strip()
    url = str(doc.get("url") or doc.get("canonical_url") or "").strip()
    if not title or not re.match(r"^https://\S+$", url, re.I):
        return False
    role = _role_evidence(doc)
    q = _normalize_query(query)
    if role["risk"] and not profile.get("risk"):
        return False
    if role["abuse"] and not re.search(r"\b(?:abuse|abusive|coercive\s+control|gaslighting)\b", q):
        return False
    if role["worldview"] and not (profile.get("specialized") or profile.get("grief") or profile.get("ai_truth")):
        return False
    metrics = _subject_metrics(query, doc)
    if min_relevance is not None and _relevance_level(metrics) < min_relevance:
        # A canonical doorway can be semantically central even when the query's
        # exact wording appears only once in the opening. Preserve that case
        # when the relevant subject family is established early and reinforced
        # across the document, rather than requiring literal title overlap.
        frame = _query_frame(query)
        contextual_family_support = bool(frame["families"]) and _contextual_fit(query, doc)[1] >= 1 and metrics[2] >= 1
        if not contextual_family_support:
            return False
    return True


def _canonical_primary_from_docs(docs, query, profile):
    eligible = []
    for index, doc in enumerate(docs or []):
        if not _eligible_outward_doc(query, doc, profile, min_relevance=2):
            continue
        metrics = _subject_metrics(query, doc)
        context = _contextual_fit(query, doc)
        score = (metrics[0], metrics[1], metrics[2], context[2], context[1], metrics[3], -index)
        eligible.append((score, doc))
    eligible.sort(key=lambda item: item[0], reverse=True)
    return eligible[0][1] if eligible else None


def _select_adjacent(claims, query, primary_title, profile):
    eligible = []
    for index, claim in enumerate(claims or []):
        if str(claim.get("title") or "").strip().casefold() == str(primary_title or "").strip().casefold():
            continue
        if not _eligible_outward_doc(query, claim, profile, min_relevance=2):
            continue
        metrics = _subject_metrics(query, claim)
        eligible.append((metrics, float(claim.get("score", 0) or 0), -index, claim))
    eligible.sort(key=lambda item: item[:-1], reverse=True)
    return eligible[0][-1] if eligible else None


def _recommendation_answer_with_authority(query, docs, profile, canonical_docs):
    canonical_docs = canonical_docs or []
    claims = docs or []
    primary = _canonical_primary_from_docs(canonical_docs, query, profile)
    if primary:
        secondary = _select_adjacent(claims, query, primary["title"], profile)
    else:
        eligible = []
        for index, claim in enumerate(claims):
            if not _eligible_outward_doc(query, claim, profile, min_relevance=2):
                continue
            metrics = _subject_metrics(query, claim)
            eligible.append((metrics, float(claim.get("score", 0) or 0), -index, claim))
        eligible.sort(key=lambda item: item[:-1], reverse=True)
        primary = eligible[0][-1] if eligible else None
        secondary = _select_adjacent([item[-1] for item in eligible[1:]], query, primary["title"] if primary else "", profile) if primary else None
    if not primary:
        return ""
    parts = [
        f"A useful place to begin with this question is [{primary['title']}]({primary['url']})",
        _base._generic_recommendation_wisdom(profile) if hasattr(_base, "_generic_recommendation_wisdom") else "Before trying to solve the question, it can help to notice what is most present in the experience—what hurts, what feels uncertain, what you may be longing for, or what you are not yet ready to name.",
        _base._recommendation_foothold(profile),
        _recommendation_rationale(primary, profile),
        "This doorway is offered as a reflection gateway, not as a complete explanation or prescription. It is one place to begin noticing what this question opens for you.",
    ]
    if secondary:
        parts.append(f"A nearby path is [{secondary['title']}]({secondary['url']}), which opens another aspect of the question without asking you to treat either doorway as the whole answer.")
    parts.append("You can stay with this lens, follow the connected material, or return with another part of the question that feels more relevant.")
    return "\n\n".join(parts)


def _parse_context_documents(context_blocks):
    parser = getattr(use_core, "_parse_context_documents", None)
    if callable(parser):
        return parser(context_blocks)
    docs = []
    for block in str(context_blocks or "").split("\n\n---\n\n"):
        tm = re.search(r"^Title:\s*(.+?)\s*$", block, re.M)
        um = re.search(r"^URL:\s*(https?://\S+)\s*$", block, re.M | re.I)
        cm = re.search(r"^Content:\s*(.*)$", block, re.M | re.S)
        if tm and um and cm:
            docs.append({"title": tm.group(1).strip(), "url": um.group(1).strip(), "text": cm.group(1).strip()})
    return docs


def _unified_visitor_construction(query, retrieved_docs, canonical_docs):
    profile = _base._inquiry_profile(query)
    docs = []
    seen = set()
    for doc in list(canonical_docs or []) + list(retrieved_docs or []):
        key = (str(doc.get("url") or ""), str(doc.get("title") or ""))
        if key in seen:
            continue
        seen.add(key)
        docs.append(doc)
    action = profile["action"]
    if action == "risk":
        return _base._build_risk_answer(query), "risk"
    if action in {"recommendation", "navigation"}:
        answer = _recommendation_answer_with_authority(query, docs, profile, canonical_docs)
        if answer:
            return answer, "recommendation"
    if action == "lived":
        return _base._build_lived_experience_answer(query, docs, profile), "lived_experience"
    if action == "foundation":
        return _base._foundation_teacherly_answer(query), "foundation"
    if action == "conceptual":
        answer = _base._build_factual_answer(query, docs)
        if answer:
            return answer, "conceptual"
    return "", "core"


_base._unified_visitor_construction = _unified_visitor_construction

_original_fetch_canonical_context = use_core.fetch_canonical_context


def _serialize_context_documents(docs):
    blocks = []
    for doc in docs or []:
        title = str(doc.get("title") or "").strip()
        url = str(doc.get("url") or doc.get("canonical_url") or "").strip()
        text = str(doc.get("text") or doc.get("content") or doc.get("excerpt") or "").strip()
        if not title or not re.match(r"^https://\S+$", url, re.I) or not text:
            continue
        blocks.append(f"Title: {title}\nURL: {url}\nContent: {text}")
    return "\n\n---\n\n".join(blocks)


def _authoritative_recommendation_docs(query, docs, profile):
    primary = _canonical_primary_from_docs(docs, query, profile)
    if not primary:
        return []
    target = primary["title"].casefold()
    for doc in docs or []:
        if str(doc.get("title") or "").strip().casefold() == target:
            return [doc]
    return []


def _sanitize_outward_context(query, docs, profile):
    eligible = []
    for doc in docs or []:
        if _eligible_outward_doc(query, doc, profile, min_relevance=2):
            eligible.append(doc)
    return eligible


def _recommendation_first_fetch(query_str):
    data = _original_fetch_canonical_context(query_str)
    profile = _base._inquiry_profile(query_str)
    if profile["action"] not in {"recommendation", "navigation"} or profile.get("risk") or not isinstance(data, dict):
        return data
    canonical_context = str(data.get("canonical_link_context") or "")
    if not canonical_context:
        return data
    docs = _parse_context_documents(canonical_context)
    if not docs:
        return data
    authoritative = [] if (profile.get("grief") or profile.get("ai_truth")) else _authoritative_recommendation_docs(query_str, docs, profile)
    if authoritative:
        outward = authoritative
        boundary_mode = "primary"
    else:
        outward = _sanitize_outward_context(query_str, docs, profile)
        boundary_mode = "sanitized-context"
    narrowed_context = _serialize_context_documents(outward)
    data = dict(data)
    data["canonical_link_context"] = narrowed_context
    data["context_blocks"] = narrowed_context
    data["recommendation_first_evidence_bridge"] = True
    data["recommendation_canonical_boundary"] = True
    data["recommendation_canonical_count"] = len(outward)
    data["recommendation_canonical_boundary_mode"] = boundary_mode
    if authoritative:
        data["evidence_sufficiency_unavailable"] = False
        data["question_structure_evidence_unavailable"] = False
        data["question_evidence_fit_unavailable"] = False
        data["frame_neutral_evidence_unavailable"] = False
    print(f"The Guide v487.49 unified outward navigation boundary: mode={boundary_mode}, selected={authoritative[0]['title'] if authoritative else 'none'}, eligible={len(outward)}, candidates={len(docs)}, query={_normalize_query(query_str)[:120]}")
    return data


use_core.fetch_canonical_context = _recommendation_first_fetch


_probe_query = "I keep finding myself angry at someone I care about, and I don’t know what to do with that anger. Is there anything in the Living Archive that might help me think about it?"
_probe_profile = _base._inquiry_profile(_probe_query)
if _probe_profile["action"] != "recommendation":
    raise RuntimeError(f"USE v487.45 invariant failed: anger action={_probe_profile['action']}")
_probe_docs = [
    {"title": "Suicide and the Journey of the Soul: A Unified Exploration of Mind, Spirit, and Society", "url": "https://geralddaquila.com/suicide", "text": "A discussion of suicide, despair, anger, and the soul."},
    {"title": "Unraveling Abuse: The Harm We Inherit, The Healing We Choose", "url": "https://geralddaquila.com/2025/06/01/unraveling-abuse-the-harm-we-inherit-the-healing-we-choose/", "text": "Abuse in relationships involves power, control, trauma, conflict, projection, and anger. The material examines cycles of harm and healing."},
    {"title": "Emotional Hijacking and the Search for Meaning: Reconnecting with Our True Needs Beyond Materialism", "url": "https://geralddaquila.com/2025/06/09/emotional-hijacking-and-the-search-for-meaning-reconnecting-with-our-true-needs-beyond-materialism/", "text": "Emotional hijacking includes intense emotional responses such as fear or anger. Mindful awareness and reflective practice can help identify emotional triggers and their true sources. The article examines emotional needs, neuroscience, self-reflection, and internal validation. " + ("The discussion remains focused on emotional awareness, triggers, needs, reflection, and practical sensemaking. " * 24) + "Later sections also discuss spiritual and metaphysical perspectives on inner fulfillment, including Buddhism, Advaita Vedanta, self-transcendence, meditation, and prayer."},
    {"title": "The Divine Feminine: Reawakening Sacred Balance in the Ascension Process and Its Intersections with Feminism", "url": "https://geralddaquila.com/divine-feminine", "text": "Sacred balance and spiritual transformation."},
]

_probe_answer, _probe_mode = _unified_visitor_construction(_probe_query, _probe_docs, [_probe_docs[2], _probe_docs[0], _probe_docs[1], _probe_docs[3]])
if _probe_mode != "recommendation" or not _probe_answer.startswith("A useful place to begin with this question is [Emotional Hijacking"):
    raise RuntimeError(f"USE v487.49 invariant failed: direct anger doorway={_probe_answer}")
if "Suicide and the Journey of the Soul" in _probe_answer or "The Divine Feminine" in _probe_answer:
    raise RuntimeError("USE v487.49 invariant failed: mismatched doorway survived risk/worldview gate")
if _role_evidence(_probe_docs[2])["worldview"]:
    raise RuntimeError("USE v487.49 invariant failed: broad multidisciplinary article misclassified as worldview-specialized")
if _role_evidence(_probe_docs[0])["risk"] is not True:
    raise RuntimeError("USE v487.49 invariant failed: explicit risk doorway lost its risk role")
if _role_evidence(_probe_docs[1])["abuse"] is not True:
    raise RuntimeError("USE v487.49 invariant failed: explicit abuse doorway lost its abuse role")
if _role_evidence(_probe_docs[3])["worldview"] is not True:
    raise RuntimeError("USE v487.49 invariant failed: explicit worldview doorway lost its worldview role")

_probe_decoys = [_probe_docs[0], _probe_docs[1], _probe_docs[3]]
if _sanitize_outward_context(_probe_query, _probe_decoys, _probe_profile):
    raise RuntimeError("USE v487.49 invariant failed: decoy-only context leaked through navigation boundary")
_probe_fallback_answer = _recommendation_answer_with_authority(_probe_query, _probe_decoys, _probe_profile, _probe_decoys)
if _probe_fallback_answer:
    raise RuntimeError("USE v487.49 invariant failed: fallback recommendation leaked decoy-only context")

_probe_gap = {"evidence_sufficiency_unavailable": True, "canonical_link_context": "Title: Unraveling Abuse: The Harm We Inherit, The Healing We Choose\nURL: https://geralddaquila.com/2025/06/01/unraveling-abuse-the-harm-we-inherit-the-healing-we-choose/\nContent: Abuse in relationships involves conflict, projection, and anger.\n\n---\n\nTitle: Suicide and the Journey of the Soul: A Unified Exploration of Mind, Spirit, and Society\nURL: https://geralddaquila.com/suicide\nContent: Suicide and despair are discussed."}
_bridge_docs = _parse_context_documents(_probe_gap["canonical_link_context"])
if not _bridge_docs or not _recommendation_first_fetch:
    raise RuntimeError("USE v487.49 invariant failed: evidence bridge unavailable")
if _sanitize_outward_context(_probe_query, _bridge_docs, _probe_profile):
    raise RuntimeError("USE v487.49 invariant failed: rejected evidence-gap context survived outward boundary")

for _query, _label in (
    ("I feel lonely and disconnected from everyone lately. Is there anything in the Living Archive that might help me think about it?", "loneliness"),
    ("I’m struggling with grief after losing someone I love. Is there anything in the Living Archive that might help?", "grief"),
    ("I’m afraid of what AI is doing to our ability to know what is true. Is there anything in the Living Archive that might help me think about discernment?", "ai_truth"),
):
    _profile = _base._inquiry_profile(_query)
    if _profile["action"] != "recommendation":
        raise RuntimeError(f"USE v487.49 invariant failed: {_label} movement classification")

def _history_text(history):
    if not history: return ""
    if isinstance(history, str): return history.strip()
    parts=[]
    for item in list(history)[-8:]:
        if isinstance(item, dict):
            role=str(item.get("role") or item.get("speaker") or "").strip()
            content=str(item.get("content") or item.get("message") or item.get("text") or item.get("response") or item.get("question") or "").strip()
            if content: parts.append(f"{role}: {content}" if role else content)
        elif item is not None:
            value=str(item).strip()
            if value: parts.append(value)
    return "\n".join(parts)

_RELATIONSHIP_INTERACTION_PATTERNS=(
    r"\bbetween us\b",r"\bbetween me and\b",r"\bbetween you and\b",r"\bwe keep\b",
    r"\bwe(?:'re| are)\b",r"\bwe can(?:'t|not)\b",r"\bwe don't\b",r"\bwe disagree\b",
    r"\bwe argue\b",r"\bargu(?:e|ing|ed)\b",r"\bconflict\b",r"\btension\b",
    r"\bcommunication\b",r"\bcommunicat(?:e|ing|ion)\b",r"\bunderstand(?:ing)?\b",
    r"\bmisunderstand(?:ing)?\b",r"\bdistance\b",r"\bdisconnect(?:ed|ion)?\b",
    r"\breconnect\b",r"\btrust\b",r"\bforgive(?:ness)?\b",r"\bresent(?:ment|ful)?\b",
    r"\bboundar(?:y|ies)\b",r"\bhurt\b",r"\bheal(?:ing)?\b",r"\bcare about\b",
    r"\bclose to\b",r"\bdrift(?:ed|ing)?\b",r"\bfeel(?:ing)? unheard\b",r"\bfeel(?:ing)? unseen\b",
)
_RELATIONSHIP_PERSON_PATTERNS=(
    r"\bsomeone i care about\b",r"\bperson i care about\b",r"\bpeople i care about\b",
    r"\bsomeone i love\b",r"\bmy partner\b",r"\bmy spouse\b",r"\bmy husband\b",
    r"\bmy wife\b",r"\bmy family\b",r"\bmy friend\b",r"\bmy friends\b",
    r"\ba friend\b",r"\ba loved one\b",r"\bmy relationship\b",r"\bour relationship\b",
    r"\bthis relationship\b",r"\bwith someone\b",r"\bwith my\b",
)

def _relationship_territory_assessment(query, history=None):
    current=_normalize_query(query); prior=_normalize_query(_history_text(history))
    combined=" ".join(part for part in (current,prior) if part).strip()
    if not combined: return {"invoke":False,"score":0.0,"reason":"empty"}
    person_signal=any(re.search(pattern,combined,re.I) for pattern in _RELATIONSHIP_PERSON_PATTERNS)
    interaction_signal=any(re.search(pattern,combined,re.I) for pattern in _RELATIONSHIP_INTERACTION_PATTERNS)
    family_signal=bool(_query_frame(combined)["relational"])
    experiential_signal=_has_experiential_stance(current) or _has_experiential_state(current)
    current_relational=family_signal or person_signal
    history_relational=bool(prior) and any(re.search(pattern,prior,re.I) for pattern in (*_RELATIONSHIP_PERSON_PATTERNS,*_RELATIONSHIP_INTERACTION_PATTERNS))
    followup_signal=bool(history_relational and re.search(r"\b(?:what do i do now|what do we do now|what now|where do we go from here|how do i respond|how do i handle this|how do i move forward|what happens next)\b",current,re.I))
    profile=_base._inquiry_profile(query)
    if profile.get("risk"): return {"invoke":False,"score":0.0,"reason":"safety-boundary"}
    if profile.get("conceptual") and not experiential_signal and not interaction_signal and not history_relational:
        return {"invoke":False,"score":0.0,"reason":"conceptual-only"}
    score=0.0
    if person_signal: score+=0.34
    if family_signal: score+=0.22
    if interaction_signal: score+=0.24
    if experiential_signal: score+=0.12
    if history_relational: score+=0.18
    if followup_signal: score+=0.30
    if current_relational and (interaction_signal or experiential_signal): score+=0.10
    if profile.get("navigation") and not experiential_signal and not interaction_signal: score-=0.20
    invoke=score>=0.50 and (current_relational or history_relational)
    return {"invoke":bool(invoke),"score":round(score,3),"reason":"relational-territory" if invoke else "insufficient-relational-signal","current_relational":current_relational,"history_relational":history_relational,"person_signal":person_signal,"interaction_signal":interaction_signal,"experiential_signal":experiential_signal}

def _relationship_guide_context(history, raw_body):
    history_text=_history_text(history)
    return {"conversation":history_text,"visitor_history":history_text,"unit_turns":len(history) if isinstance(history,list) else 0,"safety_question":str((raw_body or {}).get("safety_question") or ""),"country":str((raw_body or {}).get("country") or "")}

def _relationship_primary_doorway(contribution):
    for index,item in enumerate(contribution.get("canonical_candidates") or []):
        if not isinstance(item,dict): continue
        title=str(item.get("title") or "").strip(); url=str(item.get("url") or item.get("canonical_url") or "").strip()
        access_class=str(item.get("access_class") or "public").strip().casefold()
        if title and re.match(r"^https://geralddaquila\.com/\S+$",url,re.I) and access_class in {"public",""}: return index,title,url
    return None

def _relationship_integrated_response(contribution):
    human=str(contribution.get("human_response") or "").strip()
    if not human: return ""
    parts=[human]; doorway=_relationship_primary_doorway(contribution); movement=contribution.get("movement") or {}
    if doorway:
        _,title,url=doorway
        parts.append(f"If you want to continue from here, one doorway into the Archive is [{title}]({url}).")
    question=str(movement.get("question") or "").strip()
    if question and not bool(movement.get("rest")): parts.append(question)
    return "\n\n".join(parts)

async def _v48755_relational_return(request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    if not isinstance(body, dict):
        body = {}

    session_id = str(body.get("session_id") or "").strip()
    original_question = str(body.get("original_question") or body.get("query") or "").strip()
    conversation = str(body.get("conversation") or "").strip()
    thread_summary = str(body.get("thread_summary") or "").strip()
    working_hypothesis = str(body.get("working_hypothesis") or "").strip()
    completed_insight = str(body.get("completed_insight") or "").strip()
    perspective_delta = str(body.get("perspective_delta") or "").strip()
    body_of_thought = str(body.get("body_of_thought") or "").strip()
    underlying_need = str(body.get("underlying_need") or "").strip()
    desired_condition = str(body.get("desired_condition") or "").strip()
    next_horizon = str(body.get("next_horizon") or "").strip()
    resource_fit = str(body.get("resource_fit") or "").strip()
    fractal_maturity = str(body.get("fractal_maturity") or "").strip().casefold()

    if not original_question or not conversation:
        return JSONResponse(
            status_code=400,
            content={
                "ok": False,
                "version": APP_VERSION,
                "error_type": "relational_return_incomplete",
                "response": "The completed relational conversation was not supplied in full.",
            },
        )

    if fractal_maturity not in {"complete", "mature", "consolidating", ""}:
        return JSONResponse(
            status_code=409,
            content={
                "ok": False,
                "version": APP_VERSION,
                "error_type": "relational_return_not_ready",
                "response": "The relational inquiry has not reached a return point yet.",
                "fractal_maturity": fractal_maturity,
            },
        )

    # The Guide receives the whole journey, not merely HRN's final sentence.
    # The synthesis query is deliberately constructed from HRN's own evolving
    # state; no deterministic classifier is asked to reconstruct the meaning.
    synthesis_parts = [
        original_question,
        "Conversation thread: " + thread_summary,
        "What became clearer: " + perspective_delta,
        "Completed insight: " + completed_insight,
        "Underlying need: " + underlying_need,
        "Desired condition: " + desired_condition,
        "Living body of thought: " + body_of_thought,
        "Next horizon: " + next_horizon,
        "Canonical doorway fit noted by Seeing the Relationship: " + resource_fit,
    ]
    synthesis_query = "\n".join(part for part in synthesis_parts if part.split(": ", 1)[-1].strip())
    synthesis_query = synthesis_query[:12000]

    try:
        context_data = _original_fetch_canonical_context(synthesis_query)
        canonical_context = str(
            context_data.get("canonical_link_context")
            or context_data.get("context_blocks")
            or ""
        ) if isinstance(context_data, dict) else ""
        docs = _parse_context_documents(canonical_context)

        # Final doorway selection remains a Guide responsibility. HRN's own
        # candidates are evidence, not authority, and are not blindly accepted.
        profile = _base._inquiry_profile(original_question)
        profile["action"] = "recommendation"
        profile["recommendation"] = max(float(profile.get("recommendation", 0.0)), 0.90)
        outward = _sanitize_outward_context(synthesis_query, docs, profile)
        primary = _canonical_primary_from_docs(outward, synthesis_query, profile)

        if not primary:
            # One bounded retry against the strongest completed insight when
            # the composite journey query is too diffuse for canonical retrieval.
            fallback_query = " ".join(
                value for value in (
                    completed_insight,
                    perspective_delta,
                    underlying_need,
                    original_question,
                ) if value
            )[:8000]
            fallback_data = _original_fetch_canonical_context(fallback_query)
            fallback_context = str(
                fallback_data.get("canonical_link_context")
                or fallback_data.get("context_blocks")
                or ""
            ) if isinstance(fallback_data, dict) else ""
            fallback_docs = _parse_context_documents(fallback_context)
            fallback_outward = _sanitize_outward_context(fallback_query, fallback_docs, profile)
            primary = _canonical_primary_from_docs(fallback_outward, fallback_query, profile)
            if primary:
                outward = fallback_outward

        print(
            "The Guide v487.55 relational return: "
            f"session={session_id or 'none'}, "
            f"complete={fractal_maturity or 'unspecified'}, "
            f"selected={primary['title'] if primary else 'none'}, "
            f"conversation_chars={len(conversation)}, "
            f"query={_normalize_query(original_question)[:120]}"
        )

        if primary:
            return JSONResponse(
                status_code=200,
                content={
                    "ok": True,
                    "version": APP_VERSION,
                    "request_id": session_id,
                    "intent": "RELATIONAL_CANONICAL_RETURN",
                    "response": "You have brought this question to a meaningful place. If you want to carry it further, this is one place in the Archive you can now enter.",
                    "canonical_doorway": {
                        "title": primary["title"],
                        "url": primary["url"],
                    },
                    "relational_journey": {
                        "state": "complete",
                        "session_id": session_id,
                        "perspective_delta": perspective_delta,
                        "completed_insight": completed_insight,
                        "next_horizon": next_horizon,
                    },
                    "visitor_boundary_version": APP_VERSION,
                },
            )

        return JSONResponse(
            status_code=200,
            content={
                "ok": True,
                "version": APP_VERSION,
                "request_id": session_id,
                "intent": "RELATIONAL_CANONICAL_RETURN",
                "response": "You have brought this question to a meaningful place. You do not need to force a next step if no doorway feels right yet.",
                "canonical_doorway": None,
                "relational_journey": {
                    "state": "complete",
                    "session_id": session_id,
                    "perspective_delta": perspective_delta,
                    "completed_insight": completed_insight,
                    "next_horizon": next_horizon,
                },
                "visitor_boundary_version": APP_VERSION,
            },
        )
    except Exception as exc:
        print(f"The Guide v487.55 relational return failed safely: {exc}")
        return JSONResponse(
            status_code=200,
            content={
                "ok": False,
                "version": APP_VERSION,
                "request_id": session_id,
                "intent": "RELATIONAL_CANONICAL_RETURN",
                "response": "The relational conversation is complete. The Archive doorway could not be prepared right now.",
                "canonical_doorway": None,
                "error_type": "relational_return_retrieval_failure",
            },
        )


# ---------------------------------------------------------------------
# v487.57 — EARLY GUIDE CAPABILITY ROUTING
# ---------------------------------------------------------------------
#
# The first Guide decision is now an LLM interpretation task, not a
# deterministic specialist keyword gate. The purpose of this pass is only
# to understand what kind of doorway the question may need. It does not
# answer the visitor, select canonical resources, or release Guide ownership.
#
# Existing USE/Groq model discovery and capability management are reused from
# use_core.py. Deterministic governance remains authoritative after the model
# proposes a route. A specialist is invoked only when it is registered and
# explicitly available.
#
_GUIDE_ROUTE_IDS = frozenset({
    "guide",
    "relationship",
    "formation",
    "catalogue",
    "systems_ph",
    "safety",
    "glossary",
    "glyph",
})

_GUIDE_ROUTE_PROMPT = """You are the internal routing interpreter for The Guide,
the orientation layer of the Living Archive.

Your task is NOT to answer the visitor and NOT to recommend an Archive resource.
Interpret the visitor's question only to determine what kind of doorway or
processing would best serve the question.

Possible routes:
- guide: remain with The Guide's broad Archive orientation/navigation
- relationship: Seeing the Relationship; bounded exploration of relationships
  across self, person-to-person, family, group, community, organization,
  institution, and intergroup situations
- formation: Stewardship Formation Navigator; questions about what a situation
  may be asking a person to learn, practice, examine, or carry
- catalogue: Stewardship Catalogue; bounded navigation of stewardship resources
- systems_ph: Philippine Systems Lens; interacting Philippine systems and
  conditions
- safety: Safety / Crisis; acute or potentially acute safety concerns
- glossary: a vocabulary/definition lookup is the apparent need
- glyph: a glyph/symbol lookup is the apparent need

Important:
- A relationship can exist in work, leadership, family, friendship, community,
  institutional, or group settings. Do not require the word "relationship".
- A question can contain relational material without needing a relational
  specialist. Prefer relationship only when the human situation itself is
  central and exploratory.
- Definitions should not be routed to a conversational specialist merely
  because the defined concept happens to concern relationships.
- Preserve ambiguity. When no specialized door is clearly warranted, choose
  guide.
- Safety concerns are never downgraded because another route seems relevant.
- Do not infer diagnosis, motives, mental state, or hidden conditions.

Return ONLY valid JSON in this shape:
{
  "route": "guide|relationship|formation|catalogue|systems_ph|safety|glossary|glyph",
  "mode": "direct|delegated_journey|lookup|clarify|safety",
  "confidence": 0.0,
  "reason": "short internal explanation",
  "alternatives": ["guide"]
}
"""

def _guide_route_history_text(history):
    if not isinstance(history, list):
        return ""
    parts = []
    for item in history[-6:]:
        if isinstance(item, dict):
            role = str(item.get("role") or item.get("speaker") or "").strip()
            value = str(
                item.get("content")
                or item.get("message")
                or item.get("text")
                or item.get("response")
                or item.get("question")
                or ""
            ).strip()
            if value:
                parts.append(f"{role}: {value}" if role else value)
        elif item is not None:
            value = str(item).strip()
            if value:
                parts.append(value)
    return "\n".join(parts)[-6000:]


def _guide_route_fallback(query, history=None):
    """Conservative fallback when the early LLM route cannot execute."""
    q = _normalize_query(query)
    combined = " ".join(part for part in (q, _guide_route_history_text(history)) if part)

    # Safety remains the highest deterministic boundary.
    try:
        profile = _base._inquiry_profile(query)
        if profile.get("risk"):
            return {
                "route": "safety",
                "mode": "safety",
                "confidence": 1.0,
                "reason": "deterministic safety boundary",
                "alternatives": ["guide"],
                "source": "deterministic-safety-fallback",
            }
    except Exception:
        pass

    workplace_relational = bool(re.search(
        r"\b(?:manager|supervisor|boss|employee|colleague|coworker|co-worker|team|"
        r"direct report|department|workplace|office|leader|leadership)\b",
        combined,
        re.I,
    )) and bool(re.search(
        r"\b(?:trust|trusted|trusts|micromanag|control|controlled|controll|"
        r"communication|conflict|tension|relationship|misunderstand|"
        r"respect|respectful|feedback|check-ins?|boundar|disagree|"
        r"feel|feeling|concern|worried|unsure)\b",
        combined,
        re.I,
    ))

    current_relationship = _relationship_territory_assessment(query, history)
    if current_relationship.get("invoke") or workplace_relational:
        return {
            "route": "relationship",
            "mode": "delegated_journey",
            "confidence": 0.70 if workplace_relational else float(current_relationship.get("score", 0.0)),
            "reason": "conservative relational fallback",
            "alternatives": ["guide"],
            "source": "deterministic-relational-fallback",
        }

    if re.search(r"\b(?:glyph|symbol|icon|mark)\b", q) and re.search(
        r"\b(?:find|show|lookup|look up|meaning|what does)\b", q, re.I
    ):
        return {
            "route": "glyph",
            "mode": "lookup",
            "confidence": 0.65,
            "reason": "explicit glyph lookup language",
            "alternatives": ["guide"],
            "source": "deterministic-fallback",
        }

    if re.search(r"\b(?:define|definition|what is|what does .* mean|meaning of)\b", q, re.I):
        return {
            "route": "glossary",
            "mode": "lookup",
            "confidence": 0.65,
            "reason": "explicit definition language",
            "alternatives": ["guide"],
            "source": "deterministic-fallback",
        }

    return {
        "route": "guide",
        "mode": "direct",
        "confidence": 0.50,
        "reason": "no sufficiently bounded specialist route established",
        "alternatives": ["guide"],
        "source": "deterministic-fallback",
    }


def _guide_route_model():
    """Select the early routing model from the existing USE model pool."""
    get_models = getattr(use_core, "get_live_groq_models", None)
    budget_profile = getattr(use_core, "_generation_budget_profile", None)

    if not callable(get_models):
        return None, None

    try:
        live_models = list(get_models() or [])
    except Exception as exc:
        print(f"USE v487.57 route model discovery failed: {exc}")
        return None, None

    # Capability-aware preference: routing is short but interpretively important.
    # Prefer the existing class-2 reasoning model, then class-3, then class-1.
    preferred = []
    if callable(budget_profile):
        for complexity in (2, 3, 1, 4):
            try:
                model = str(
                    budget_profile({"complexity": complexity}).get("model") or ""
                ).strip()
                if model and model not in preferred:
                    preferred.append(model)
            except Exception:
                continue

    for model in preferred:
        if model in live_models:
            return model, preferred

    for model in live_models:
        if model:
            return model, preferred

    return None, preferred


def _guide_capability_route(query, history=None):
    """Interpret the first question through the existing Groq model architecture."""
    fallback = _guide_route_fallback(query, history)

    groq_client = getattr(use_core, "groq_client", None)
    if groq_client is None:
        return fallback

    model_id, preference_order = _guide_route_model()
    if not model_id:
        return fallback

    history_text = _guide_route_history_text(history)
    user_content = (
        "Visitor question:\n"
        + str(query).strip()
        + (
            "\n\nRecent conversation context:\n" + history_text
            if history_text else ""
        )
    )

    try:
        provider_kwargs = {
            "model": model_id,
            "messages": [
                {"role": "system", "content": _GUIDE_ROUTE_PROMPT},
                {"role": "user", "content": user_content[:9000]},
            ],
            "temperature": 0.0,
            "max_completion_tokens": 300,
            "response_format": {"type": "json_object"},
        }

        if model_id.startswith("openai/gpt-oss-"):
            provider_kwargs["reasoning_effort"] = "low"
            provider_kwargs["include_reasoning"] = False

        preflight = getattr(use_core, "_known_daily_tpd_preflight", None)
        estimate = getattr(use_core, "_estimate_quota_tokens", None)
        if callable(preflight) and callable(estimate):
            try:
                estimated = int(
                    estimate(provider_kwargs["messages"], 300)
                )
                preflight(model_id, estimated)
            except Exception as exc:
                print(f"USE v487.57 route preflight skipped: {exc}")

        response = groq_client.chat.completions.create(**provider_kwargs)
        raw = str(response.choices[0].message.content or "").strip()
        parsed = json.loads(raw)

        if not isinstance(parsed, dict):
            raise ValueError("route response was not an object")

        route = str(parsed.get("route") or "guide").strip().casefold()
        mode = str(parsed.get("mode") or "direct").strip().casefold()
        confidence = float(parsed.get("confidence", 0.0) or 0.0)
        reason = str(parsed.get("reason") or "").strip()
        alternatives = parsed.get("alternatives") or []

        # The early LLM identifies the capability; the bounded deterministic
        # territory assessment governs whether a genuine relational experience
        # enters the delegated journey. The model must not be allowed to turn
        # a clearly relational lived question into a direct Guide answer merely
        # by returning mode=direct.
        if route == "relationship":
            relational_assessment = _relationship_territory_assessment(query, history)
            if relational_assessment.get("invoke"):
                mode = "delegated_journey"
                confidence = max(
                    confidence,
                    float(relational_assessment.get("score", 0.0) or 0.0),
                    0.70,
                )
                reason = (
                    "bounded relational territory confirmed; "
                    "delegated relational journey required"
                )

        if route not in _GUIDE_ROUTE_IDS:
            raise ValueError(f"unsupported route {route!r}")
        if mode not in {"direct", "delegated_journey", "lookup", "clarify", "safety"}:
            mode = "direct"
        confidence = max(0.0, min(1.0, confidence))
        alternatives = [
            str(item).strip().casefold()
            for item in alternatives
            if str(item).strip().casefold() in _GUIDE_ROUTE_IDS
        ][:3]

        # Deterministic safety remains authoritative.
        try:
            profile = _base._inquiry_profile(query)
            if profile.get("risk"):
                route = "safety"
                mode = "safety"
                confidence = 1.0
                reason = "deterministic safety boundary"
        except Exception:
            pass

        result = {
            "route": route,
            "mode": mode,
            "confidence": confidence,
            "reason": reason[:500],
            "alternatives": alternatives or ["guide"],
            "source": "groq",
            "model": model_id,
            "preference_order": preference_order,
        }

        print(
            "USE v487.57 capability route: "
            f"source=groq, model={model_id}, route={route}, mode={mode}, "
            f"confidence={confidence:.3f}, reason={reason[:180]!r}"
        )
        return result

    except Exception as exc:
        print(
            "USE v487.57 capability route failed safely: "
            f"model={model_id}, error={exc}"
        )
        return fallback


def _registered_available_specialist(specialist_id):
    for capability in SPECIALIST_CAPABILITY_REGISTRY:
        if (
            capability.specialist_id == specialist_id
            and capability.status == "available"
        ):
            return capability
    return None


async def _v48756_query_middleware(request: Request, call_next):
    if request.method.upper() != "POST" or request.url.path not in {"/api/query", "/"}:
        return await call_next(request)

    try:
        raw_body = await request.json()
    except Exception:
        raw_body = {}
    if not isinstance(raw_body, dict):
        raw_body = {}

    query = str(
        raw_body.get("query")
        or raw_body.get("user_query")
        or raw_body.get("question")
        or raw_body.get("text")
        or raw_body.get("input")
        or ""
    ).strip()
    history = raw_body.get("history") or raw_body.get("conversation_history")

    if not query:
        return await call_next(request)

    route = _guide_capability_route(query, history)
    route_id = str(route.get("route") or "guide").strip().casefold()
    mode = str(route.get("mode") or "direct").strip().casefold()
    confidence = float(route.get("confidence", 0.0) or 0.0)

    # Only an actually available specialist can receive a delegated journey.
    # The LLM proposes; registry governance authorizes.
    capability = _registered_available_specialist(route_id)
    should_delegate = (
        capability is not None
        and route_id == "relationship"
        and mode == "delegated_journey"
        and confidence >= 0.60
    )

    print(
        "The Guide v487.57 capability gate: "
        f"route={route_id}, mode={mode}, confidence={confidence:.3f}, "
        f"delegate={should_delegate}, query={_normalize_query(query)[:120]}"
    )

    if should_delegate:
        request_id = str(getattr(request.state, "use_request_id", "") or "")
        if not request_id:
            request_id = "relationship-" + hashlib.sha1(
                (query + "|" + _history_text(history)).encode("utf-8")
            ).hexdigest()[:16]

        return JSONResponse(
            status_code=200,
            content={
                "ok": True,
                "version": APP_VERSION,
                "query": query,
                "intent": "RELATIONAL_HANDOFF",
                "response": "",
                "relational_delegation": {
                    "state": "open",
                    "specialist": capability.public_name,
                    "specialist_id": capability.specialist_id,
                    "session_id": request_id,
                    "seed_message": query,
                    "conversation": _history_text(history),
                    "handoff_reason": "The Guide recognized that this question may be better explored as a relationship before choosing a doorway into the Archive.",
                    "hrn_endpoint": "https://geralddaquila.com/wp-json/living-archive/v1/relational-navigator",
                    "guide_return_endpoint": "/api/relational-return",
                },
                "visitor_boundary_version": APP_VERSION,
                "request_id": request_id,
            },
        )

    return await call_next(request)

# v487.57 request-boundary interception.
#
# The v487.56 HTTP middleware did not reliably reach /api/query in the live
# FastAPI application. The inherited core request path could execute first,
# which is why the benchmark still produced the v487.28 visitor boundary
# instead of RELATIONAL_HANDOFF.
#
# Keep the FastAPI application intact and wrap it at the ASGI boundary.
# Non-relational traffic is replayed unchanged into the original FastAPI
# application, preserving its CORS, request-id, retrieval, generation,
# safety, and visitor-boundary middleware.

async def _v48757_read_body(receive):
    chunks = []
    while True:
        message = await receive()
        message_type = message.get("type")
        if message_type == "http.disconnect":
            break
        if message_type != "http.request":
            continue
        body = message.get("body") or b""
        if body:
            chunks.append(body)
        if not message.get("more_body", False):
            break
    return b"".join(chunks)


def _v48757_replay_receive(body):
    sent = False

    async def _receive():
        nonlocal sent
        if not sent:
            sent = True
            return {"type": "http.request", "body": body, "more_body": False}
        return {"type": "http.request", "body": b"", "more_body": False}

    return _receive


async def _v48757_send_json(send, payload, status_code=200):
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    await send({
        "type": "http.response.start",
        "status": status_code,
        "headers": [
            (b"content-type", b"application/json; charset=utf-8"),
            (b"content-length", str(len(body)).encode("ascii")),
            (b"access-control-allow-origin", b"*"),
        ],
    })
    await send({"type": "http.response.body", "body": body})


_FASTAPI_APP = app


async def _v48757_query_asgi(scope, receive, send):
    if scope.get("type") != "http":
        await _FASTAPI_APP(scope, receive, send)
        return

    method = str(scope.get("method") or "").upper()
    path = str(scope.get("path") or "")
    if method != "POST" or path not in {"/api/query", "/"}:
        await _FASTAPI_APP(scope, receive, send)
        return

    raw_body = await _v48757_read_body(receive)
    try:
        raw_body_text = raw_body.decode("utf-8")
        parsed_body = json.loads(raw_body_text) if raw_body_text else {}
    except Exception:
        parsed_body = {}

    if not isinstance(parsed_body, dict):
        parsed_body = {}

    query = str(
        parsed_body.get("query")
        or parsed_body.get("user_query")
        or parsed_body.get("question")
        or parsed_body.get("text")
        or parsed_body.get("input")
        or ""
    ).strip()
    history = parsed_body.get("history") or parsed_body.get("conversation_history")

    if not query:
        await _FASTAPI_APP(scope, _v48757_replay_receive(raw_body), send)
        return

    route = _guide_capability_route(query, history)
    route_id = str(route.get("route") or "guide").strip().casefold()
    mode = str(route.get("mode") or "direct").strip().casefold()
    confidence = float(route.get("confidence", 0.0) or 0.0)

    capability = _registered_available_specialist(route_id)
    should_delegate = (
        capability is not None
        and route_id == "relationship"
        and mode == "delegated_journey"
        and confidence >= 0.60
    )

    print(
        "The Guide v487.57 capability boundary: "
        f"route={route_id}, mode={mode}, confidence={confidence:.3f}, "
        f"delegate={should_delegate}, query={_normalize_query(query)[:120]}"
    )

    if should_delegate:
        request_id = "relationship-" + hashlib.sha1(
            (query + "|" + _history_text(history)).encode("utf-8")
        ).hexdigest()[:16]

        return await _v48757_send_json(
            send,
            {
                "ok": True,
                "version": APP_VERSION,
                "query": query,
                "intent": "RELATIONAL_HANDOFF",
                "response": "",
                "relational_delegation": {
                    "state": "open",
                    "specialist": capability.public_name,
                    "specialist_id": capability.specialist_id,
                    "session_id": request_id,
                    "seed_message": query,
                    "conversation": _history_text(history),
                    "handoff_reason": "The Guide recognized that this question may be better explored as a relationship before choosing a doorway into the Archive.",
                    "hrn_endpoint": "https://geralddaquila.com/wp-json/living-archive/v1/relational-navigator",
                    "guide_return_endpoint": "/api/relational-return",
                },
                "visitor_boundary_version": APP_VERSION,
                "request_id": request_id,
            },
        )

    await _FASTAPI_APP(scope, _v48757_replay_receive(raw_body), send)


@app.post("/api/relational-return")
async def _v48755_relational_return_route(request: Request):
    return await _v48755_relational_return(request)


# v487.57 capability-routing invariants.
_RELATIONSHIP_TESTS=(
    ("I keep getting angry with someone I care about and I don't know what to do with it.",True),
    ("My partner and I keep misunderstanding each other and I want to see what is happening between us.",True),
    ("What should I read about relationships in the Living Archive?",False),
    ("What is a relationship?",False),
    ("I keep wondering whether AI is making it harder to know what is true. Where should I begin?",False),
    ("What do I do now?",True),
)
for _relationship_test_query,_relationship_expected in _RELATIONSHIP_TESTS:
    _relationship_test_history=([{"role":"user","content":"My partner and I keep misunderstanding each other."}] if _relationship_test_query=="What do I do now?" else [])
    _relationship_test=_relationship_territory_assessment(_relationship_test_query,_relationship_test_history)
    if _relationship_test["invoke"]!=_relationship_expected:
        raise RuntimeError("USE v487.55 relational territory invariant failed: " f"expected={_relationship_expected}, result={_relationship_test}")

# The middleware, not mutation of FastAPI's stored endpoint objects, owns
# relational interception. This preserves the base route's validated request
# contract for every non-relational query.
if not any(getattr(route, "path", "") == "/api/relational-return" for route in app.routes):
    raise RuntimeError("USE v487.57 invariant failed: relational return route not registered")

# Only expose the ASGI wrapper after every FastAPI route and startup invariant
# has been registered against the original application object.
app = _v48757_query_asgi


# Legacy relational territory invariants retained as fallback safeguards.
_RELATIONSHIP_TESTS=(
    ("I keep getting angry with someone I care about and I don't know what to do with it.",True),
    ("My partner and I keep misunderstanding each other and I want to see what is happening between us.",True),
    ("What should I read about relationships in the Living Archive?",False),
    ("What is a relationship?",False),
    ("I keep wondering whether AI is making it harder to know what is true. Where should I begin?",False),
    ("What do I do now?",True),
)
for _relationship_test_query,_relationship_expected in _RELATIONSHIP_TESTS:
    _relationship_test_history=([{"role":"user","content":"My partner and I keep misunderstanding each other."}] if _relationship_test_query=="What do I do now?" else [])
    _relationship_test=_relationship_territory_assessment(_relationship_test_query,_relationship_test_history)
    if _relationship_test["invoke"]!=_relationship_expected:
        raise RuntimeError("USE v487.54 relational territory invariant failed: " f"expected={_relationship_expected}, result={_relationship_test}")


print(f"USE v487.57 ACTIVE: version={APP_VERSION}, fingerprint={DEPLOYMENT_FINGERPRINT}, core_sha={EXPECTED_CORE_BLOB_SHA}, source_sha256={RUNTIME_SOURCE_SHA256}, specialist_contract={SPECIALIST_PIPE_CONTRACT_VERSION}, adapter_contract={SPECIALIST_ADAPTER_CONTRACT_VERSION}, relationship_contract={RELATIONSHIP_CONTRIBUTION_CONTRACT_VERSION}, relationship_voice_policy={RELATIONSHIP_VOICE_POLICY}, registered_specialists={len(SPECIALIST_CAPABILITY_REGISTRY)}, active_adapters={len(SPECIALIST_ADAPTER_REGISTRY.ids())}, capability_routing=groq_first_governed")