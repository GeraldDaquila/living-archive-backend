# USE PRODUCTION VERSION: v487.44 — structural role-centrality abuse-boundary repair
import hashlib
import importlib
import re
from pathlib import Path

_BASE_MODULE_NAME = "main_v487_28_runtime"
_base = importlib.import_module(_BASE_MODULE_NAME)
use_core = _base.use_core
APP_VERSION = "v487.44"
DEPLOYMENT_FINGERPRINT = "USE-v487.44-structural-role-centrality-abuse-boundary-repair"
CANONICAL_BUILD_ID = "USE-BUILD-v487.44-structural-role-centrality-abuse-boundary-repair"
EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"
_MAIN_PATH = Path(__file__).resolve()
RUNTIME_SOURCE_SHA256 = hashlib.sha256(_MAIN_PATH.read_bytes()).hexdigest()
if getattr(_base, "_core_runtime_sha", "") != EXPECTED_CORE_BLOB_SHA:
    raise RuntimeError("USE protected core integrity failure: protected core mismatch.")


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
    if min_relevance is not None and _relevance_level(_subject_metrics(query, doc)) < min_relevance:
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
    print(f"The Guide v487.44 unified outward navigation boundary: mode={boundary_mode}, selected={authoritative[0]['title'] if authoritative else 'none'}, eligible={len(outward)}, candidates={len(docs)}, query={_normalize_query(query_str)[:120]}")
    return data


use_core.fetch_canonical_context = _recommendation_first_fetch


_probe_query = "I keep finding myself angry at someone I care about, and I don’t know what to do with that anger. Is there anything in the Living Archive that might help me think about it?"
_probe_profile = _base._inquiry_profile(_probe_query)
if _probe_profile["action"] != "recommendation":
    raise RuntimeError(f"USE v487.44 invariant failed: anger action={_probe_profile['action']}")
_probe_docs = [
    {"title": "Suicide and the Journey of the Soul: A Unified Exploration of Mind, Spirit, and Society", "url": "https://geralddaquila.com/suicide", "text": "A discussion of suicide, despair, anger, and the soul."},
    {"title": "Unraveling Abuse: The Harm We Inherit, The Healing We Choose", "url": "https://geralddaquila.com/2025/06/01/unraveling-abuse-the-harm-we-inherit-the-healing-we-choose/", "text": "Abuse in relationships involves power, control, trauma, conflict, projection, and anger. The material examines cycles of harm and healing."},
    {"title": "Emotional Hijacking and the Search for Meaning: Reconnecting with Our True Needs Beyond Materialism", "url": "https://geralddaquila.com/2025/06/09/emotional-hijacking-and-the-search-for-meaning-reconnecting-with-our-true-needs-beyond-materialism/", "text": "Emotional hijacking includes intense emotional responses such as fear or anger. Mindful awareness and reflective practice can help identify emotional triggers and their true sources. The article examines emotional needs, neuroscience, self-reflection, and internal validation. " + ("The discussion remains focused on emotional awareness, triggers, needs, reflection, and practical sensemaking. " * 24) + "Later sections also discuss spiritual and metaphysical perspectives on inner fulfillment, including Buddhism, Advaita Vedanta, self-transcendence, meditation, and prayer."},
    {"title": "The Divine Feminine: Reawakening Sacred Balance in the Ascension Process and Its Intersections with Feminism", "url": "https://geralddaquila.com/divine-feminine", "text": "Sacred balance and spiritual transformation."},
]

_probe_answer, _probe_mode = _unified_visitor_construction(_probe_query, _probe_docs, [_probe_docs[2], _probe_docs[0], _probe_docs[1], _probe_docs[3]])
if _probe_mode != "recommendation" or not _probe_answer.startswith("A useful place to begin with this question is [Emotional Hijacking"):
    raise RuntimeError(f"USE v487.44 invariant failed: direct anger doorway={_probe_answer}")
if "Suicide and the Journey of the Soul" in _probe_answer or "The Divine Feminine" in _probe_answer:
    raise RuntimeError("USE v487.44 invariant failed: mismatched doorway survived risk/worldview gate")
if _role_evidence(_probe_docs[2])["worldview"]:
    raise RuntimeError("USE v487.44 invariant failed: broad multidisciplinary article misclassified as worldview-specialized")
if _role_evidence(_probe_docs[0])["risk"] is not True:
    raise RuntimeError("USE v487.44 invariant failed: explicit risk doorway lost its risk role")
if _role_evidence(_probe_docs[1])["abuse"] is not True:
    raise RuntimeError("USE v487.44 invariant failed: explicit abuse doorway lost its abuse role")
if _role_evidence(_probe_docs[3])["worldview"] is not True:
    raise RuntimeError("USE v487.44 invariant failed: explicit worldview doorway lost its worldview role")

_probe_decoys = [_probe_docs[0], _probe_docs[1], _probe_docs[3]]
if _sanitize_outward_context(_probe_query, _probe_decoys, _probe_profile):
    raise RuntimeError("USE v487.44 invariant failed: decoy-only context leaked through navigation boundary")
_probe_fallback_answer = _recommendation_answer_with_authority(_probe_query, _probe_decoys, _probe_profile, _probe_decoys)
if _probe_fallback_answer:
    raise RuntimeError("USE v487.44 invariant failed: fallback recommendation leaked decoy-only context")

_probe_gap = {"evidence_sufficiency_unavailable": True, "canonical_link_context": "Title: Unraveling Abuse: The Harm We Inherit, The Healing We Choose\nURL: https://geralddaquila.com/2025/06/01/unraveling-abuse-the-harm-we-inherit-the-healing-we-choose/\nContent: Abuse in relationships involves conflict, projection, and anger.\n\n---\n\nTitle: Suicide and the Journey of the Soul: A Unified Exploration of Mind, Spirit, and Society\nURL: https://geralddaquila.com/suicide\nContent: Suicide and despair are discussed."}
_bridge_docs = _parse_context_documents(_probe_gap["canonical_link_context"])
if not _bridge_docs or not _recommendation_first_fetch:
    raise RuntimeError("USE v487.44 invariant failed: evidence bridge unavailable")
if _sanitize_outward_context(_probe_query, _bridge_docs, _probe_profile):
    raise RuntimeError("USE v487.44 invariant failed: rejected evidence-gap context survived outward boundary")

for _query, _label in (
    ("I feel lonely and disconnected from everyone lately. Is there anything in the Living Archive that might help me think about it?", "loneliness"),
    ("I’m struggling with grief after losing someone I love. Is there anything in the Living Archive that might help?", "grief"),
    ("I’m afraid of what AI is doing to our ability to know what is true. Is there anything in the Living Archive that might help me think about discernment?", "ai_truth"),
):
    _profile = _base._inquiry_profile(_query)
    if _profile["action"] != "recommendation":
        raise RuntimeError(f"USE v487.44 invariant failed: {_label} movement classification")

print(f"USE v487.44 ACTIVE: version={APP_VERSION}, fingerprint={DEPLOYMENT_FINGERPRINT}, core_sha={EXPECTED_CORE_BLOB_SHA}, source_sha256={RUNTIME_SOURCE_SHA256}")
