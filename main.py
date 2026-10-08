# USE PRODUCTION VERSION: v488.72 — systemic relational boundary calibration
import asyncio
import hashlib
import ipaddress
import re
import json
import time
from urllib.request import Request as UrlRequest, urlopen
from shared_evidence import normalize_documents_for_use, CONTRACT_VERSION as SHARED_EVIDENCE_CONTRACT_VERSION
from shared_intelligence_primitives import normalize_claims as _shared_normalize_claims, build_synthesis_material as _shared_build_synthesis_material
from pathlib import Path
from urllib.parse import quote
from fastapi import Request
from fastapi.responses import JSONResponse

from hub_contracts import (
    build_hub_request,
    hub_contract_snapshot,
    route_spoke,
)

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
from formation_adapter import FormationAdapter
from formation_contribution import (
    FORMATION_CONTRIBUTION_CONTRACT_VERSION,
    FORMATION_VOICE_POLICY,
    formation_contract_snapshot,
)
from specialist_adapters import (
    SPECIALIST_ADAPTER_CONTRACT_VERSION,
    SpecialistAdapterRegistry,
    adapter_contract_snapshot,
    invoke_specialist,
)
from guide_node_registry import (
    GUIDE_NODE_REGISTRY_VERSION,
    active_nodes,
    node_handoff_payload,
)
from provider_bank import (
    CONTRACT_VERSION as PROVIDER_BANK_CONTRACT_VERSION,
    route as route_with_model_bank,
    snapshot as provider_bank_snapshot,
)
from safety_utility import classify_safety, safety_utility_snapshot
from safety_adapter import SafetyUtilityAdapter
from safety_intelligence import SAFETY_INTELLIGENCE_CONTRACT_VERSION, repair_safety_question, safety_intelligence_snapshot

_BASE_MODULE_NAME = "guide_runtime"
_base = __import__(_BASE_MODULE_NAME)
use_core = _base.use_core
app = _base.app
_original_guide_handle_query = use_core.handle_query
APP_VERSION = "v488.72"
DEPLOYMENT_FINGERPRINT = "USE-v488.72-systemic-relational-boundary"
CANONICAL_BUILD_ID = "USE-BUILD-v488.72-systemic-relational-boundary"

# v488.64 systemwide safety continuity contract marker.
# This marker is intentionally adjacent to the production identity so CI can
# detect drift between the live Guide boundary and its regression tests.
SAFETY_BOUNDARY_CONTRACT_VERSION = "v488.68"

GUIDE_NODE_REGISTRY_URL = "https://geralddaquila.com/wp-json/guide/v1/nodes"
_GUIDE_NODE_REGISTRY_CACHE = {"nodes": [], "fetched_at": 0.0, "failed_at": 0.0}
_GUIDE_NODE_REGISTRY_CACHE_TTL = 300.0
_GUIDE_NODE_REGISTRY_FAILURE_TTL = 30.0


def _guide_node_registry_snapshot():
    """Read the authoritative WordPress Guide Node Registry with bounded caching."""
    now = time.time()
    if _GUIDE_NODE_REGISTRY_CACHE["nodes"] and (
        now - float(_GUIDE_NODE_REGISTRY_CACHE["fetched_at"]) < _GUIDE_NODE_REGISTRY_CACHE_TTL
    ):
        return list(_GUIDE_NODE_REGISTRY_CACHE["nodes"])
    if float(_GUIDE_NODE_REGISTRY_CACHE["failed_at"]) and (
        now - float(_GUIDE_NODE_REGISTRY_CACHE["failed_at"]) < _GUIDE_NODE_REGISTRY_FAILURE_TTL
    ):
        return []
    try:
        request = UrlRequest(
            GUIDE_NODE_REGISTRY_URL,
            headers={"Accept": "application/json", "User-Agent": "Living-Archive-The-Guide/1.0"},
            method="GET",
        )
        with urlopen(request, timeout=4) as response:
            payload = json.loads(response.read().decode("utf-8"))
        records = payload.get("nodes") if isinstance(payload, dict) else []
        nodes = active_nodes(records if isinstance(records, list) else [])
        _GUIDE_NODE_REGISTRY_CACHE["nodes"] = nodes
        _GUIDE_NODE_REGISTRY_CACHE["fetched_at"] = now
        _GUIDE_NODE_REGISTRY_CACHE["failed_at"] = 0.0
        print(
            "The Guide Node Registry: "
            f"source=wordpress, nodes={len(nodes)}, registry_version="
            f"{payload.get('registry_version') if isinstance(payload, dict) else 'unknown'}"
        )
        return list(nodes)
    except Exception as exc:
        _GUIDE_NODE_REGISTRY_CACHE["failed_at"] = now
        print(f"The Guide Node Registry unavailable; continuing without node routing: {exc}")
        return []


def _guide_node_prompt_context():
    nodes = _guide_node_registry_snapshot()
    if not nodes:
        return "No approved Guide Nodes are currently available to the routing layer."
    return json.dumps([
        {
            "node_id": node.get("node_id"),
            "title": node.get("title"),
            "purpose": node.get("purpose"),
            "asset_type": node.get("asset_type"),
            "access_class": node.get("access_class"),
            "discovery_level": int(node.get("discovery_level", 1) or 1),
            "semantic_hints": node.get("semantic_hints") or [],
        }
        for node in nodes
    ], ensure_ascii=False, separators=(",", ":"))


def _guide_node_by_id(node_id):
    target = str(node_id or "").strip()
    if not target:
        return None
    for node in _guide_node_registry_snapshot():
        if str(node.get("node_id") or "").strip() == target:
            return node
    return None


EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"
_MAIN_PATH = Path(__file__).resolve()
RUNTIME_SOURCE_SHA256 = hashlib.sha256(_MAIN_PATH.read_bytes()).hexdigest()

# Runtime/version integrity is a startup invariant, not external bookkeeping.
if str(APP_VERSION) != "v488.71":
    raise RuntimeError("USE version integrity failure: APP_VERSION drift.")
if not str(DEPLOYMENT_FINGERPRINT).startswith(f"USE-{APP_VERSION}-"):
    raise RuntimeError("USE version integrity failure: deployment fingerprint/version mismatch.")
if not str(CANONICAL_BUILD_ID).startswith(f"USE-BUILD-{APP_VERSION}-"):
    raise RuntimeError("USE version integrity failure: canonical build/version mismatch.")

use_core.APP_VERSION = APP_VERSION
use_core.DEPLOYMENT_FINGERPRINT = DEPLOYMENT_FINGERPRINT
use_core.CANONICAL_BUILD_ID = CANONICAL_BUILD_ID
use_core.RUNTIME_SOURCE_SHA256 = RUNTIME_SOURCE_SHA256
use_core.EXPECTED_CORE_BLOB_SHA = EXPECTED_CORE_BLOB_SHA
if getattr(_base, "_core_runtime_sha", "") != EXPECTED_CORE_BLOB_SHA:
    raise RuntimeError("USE protected core integrity failure: protected core mismatch.")

if PROVIDER_BANK_CONTRACT_VERSION != "v2":
    raise RuntimeError("USE provider bank contract integrity failure: unsupported provider bank contract.")
if GUIDE_NODE_REGISTRY_VERSION != "v2":
    raise RuntimeError("USE Guide Node Registry contract integrity failure: unsupported registry version.")

validate_registry()
SPECIALIST_CAPABILITY_REGISTRY = registry_snapshot()
SPECIALIST_ADAPTER_REGISTRY = SpecialistAdapterRegistry()
SPECIALIST_ADAPTER_REGISTRY.register(RelationshipAdapter())
SPECIALIST_ADAPTER_REGISTRY.register(FormationAdapter())
SPECIALIST_ADAPTER_REGISTRY.register(SafetyUtilityAdapter())
SPECIALIST_ADAPTER_DIAGNOSTICS = adapter_contract_snapshot(SPECIALIST_ADAPTER_REGISTRY)
RELATIONSHIP_CONTRIBUTION_DIAGNOSTICS = relationship_contract_snapshot()
FORMATION_CONTRIBUTION_DIAGNOSTICS = formation_contract_snapshot()
HUB_CONTRACT_DIAGNOSTICS = hub_contract_snapshot()
SAFETY_UTILITY_DIAGNOSTICS = safety_utility_snapshot()
SAFETY_INTELLIGENCE_DIAGNOSTICS = safety_intelligence_snapshot()
if SAFETY_INTELLIGENCE_DIAGNOSTICS.get("contract_version") != SAFETY_INTELLIGENCE_CONTRACT_VERSION:
    raise RuntimeError("USE safety intelligence contract integrity failure.")
if SAFETY_UTILITY_DIAGNOSTICS.get("hrn_dependency") is not True:
    raise RuntimeError("USE safety utility integrity failure: HRN safety linkage missing.")


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
    r"\bsomeone i care about\b", r"\bpeople i care about\b", r"\bperson i care about\b",
    r"\brelationship\b", r"\bpartner\b", r"\bloved one\b", r"\bfamily\b", r"\bfriend\b",
    r"\binterpersonal\b", r"\bwith someone\b", r"\bcare about\b",
    r"\bmy father\b", r"\bmy mother\b", r"\bmy parent\b", r"\bmy parents\b",
    r"\bmy son\b", r"\bmy daughter\b", r"\bmy child\b", r"\bmy brother\b",
    r"\bmy sister\b", r"\bmy husband\b", r"\bmy wife\b", r"\bmy family\b",
    r"\bmy friend\b", r"\bmy colleague\b", r"\bmy boss\b", r"\bmy coworker\b",
    r"\bmy client\b", r"\bmy team\b", r"\bbetween us\b", r"\bwith my\b"
)

_RELATIONAL_ACTION_PATTERNS = (
    # Commitments, conflict, responsibility, and explicit relational work.
    r"\bpromised\b", r"\bpromise\b", r"\bgave (?:him|her|them) my word\b",
    r"\bgave my word\b", r"\bcommitted\b", r"\bcommitment\b", r"\bagreed\b",
    r"\bowe\b", r"\bowed\b", r"\btake care of\b", r"\blet .* down\b",
    r"\bdisappoint(?:ed|ing)?\b", r"\bconflict(?:s)?\b", r"\bargument(?:s)?\b", r"\bargu(?:e|ed|ing)\b", r"\bfight(?:s|ing)?\b",
    r"\bdisagree(?:d|ment|ing)?\b", r"\bneed to tell\b", r"\bneed to say\b",
    r"\bhave to tell\b", r"\bhave to say\b", r"\bset a boundary\b",
    r"\bboundaries\b", r"\btrust\b", r"\bforgive\b", r"\bforgiveness\b",
    r"\bresponsibilit(?:y|ies)\b", r"\bresponsible for\b", r"\bobligation\b",
    r"\bobligated\b", r"\bexpectation\b", r"\bexpected\b", r"\bduty\b",
    r"\bdecision\b", r"\bdecide\b", r"\bchoose\b", r"\bchoice\b",
    r"\bburden\b", r"\btension\b", r"\bcommunication\b", r"\bcommunicat(?:e|ing)\b",
    r"\bdistance\b", r"\bdisconnect(?:ed|ion)?\b", r"\brelationship\b",

    # Recurring interaction cycles are relational structure even when the
    # visitor does not use words such as conflict, boundary, or relationship.
    r"\bdefensive\b", r"\bgets? angry\b", r"\bget angry\b",
    r"\bwithdraw(?:s|al|n|ing)?\b", r"\bstops? talking\b",
    r"\bgoes? quiet\b", r"\bshuts? down\b", r"\bshut down\b",
    r"\bcycle\b", r"\bloop\b", r"\brepeat(?:s|ed|ing)?\b",
    r"\bsame thing happens\b", r"\bkeeps? happening\b",
    r"\bcomes? up again\b",

    # Reciprocity and availability are relational dynamics even when there is
    # no conflict, promise, boundary, or named relationship problem.
    r"\basks? me\b", r"\bask(?:s|ed)? for (?:my )?(?:support|help|time|attention)\b",
    r"\bneeds? me\b", r"\bneed(?:s|ed)? (?:my )?(?:support|help|time|attention)\b",
    r"\bsupport(?:s|ed|ing)?\b", r"\bshow(?:s|ed)? up\b", r"\bbeing there\b",
    r"\bbe there for\b", r"\bavailable\b", r"\bavailability\b",
    r"\bdisappear(?:s|ed|ing)?\b", r"\bvanish(?:es|ed|ing)?\b",
    r"\bone[- ]sided\b", r"\bone[- ]way\b", r"\brecipro(?:cal|city)\b",
    r"\bmutual\b", r"\bgive[- ]and[- ]take\b", r"\bgive\b.*\btake\b",
    r"\bkeeps? asking\b", r"\bkeep asking\b", r"\brely(?:ing|ies|ied)? on me\b",
    r"\bdepend(?:s|ed|ing)? on me\b", r"\bonly when\b", r"\bwhenever\b",
    r"\balways\b.*\b(?:asks?|needs?|expects?|takes?)\b",
    r"\b(?:asks?|needs?|expects?|takes?)\b.*\balways\b"
)


def _query_frame(query):
    q = _normalize_query(query)
    families = tuple(family for family, terms in _SUBJECT_FAMILIES.items() if any(re.search(rf"\b{re.escape(term)}\b", q) for term in terms))
    return {"families": families, "relational": any(re.search(pattern, q, re.I) for pattern in _RELATIONAL_PATTERNS)}


# Relational role/context signals are deliberately broader than named family or
# partnership terms. A lived relationship can be shaped by authority, work,
# learning, care, service, or community roles. These signals are only useful
# when paired with first-person experience and unresolved relational tension;
# they are not standalone routing keywords.
_RELATIONAL_ROLE_PATTERNS = (
    r"\bmy\s+(?:manager|supervisor|boss|employer|employee|colleague|coworker|co-worker|teammate|team|client|customer|teacher|student|professor|doctor|therapist|counselor|coach|mentor|neighbor|landlord|tenant|caregiver|carer|parent|child|brother|sister|friend|partner|spouse|husband|wife)\b",
    r"\b(?:manager|supervisor|boss|employer|colleague|coworker|co-worker|teammate)\s+(?:at|from|in)\b",
)

_RELATIONAL_INTERACTION_PATTERNS = (
    r"\b(?:trust|trusted|trusts|distrust|check(?:s|ed|ing)?|monitor(?:s|ed|ing)?|control(?:s|led|ling)?|micromanag(?:e|es|ed|ing)|report(?:s|ed|ing)?|update(?:s|d|ing)?|approve(?:s|d|ing)?|question(?:s|ed|ing)?|watch(?:es|ed|ing)?|expect(?:s|ed|ation|ations)?|ask(?:s|ed|ing)?|tell(?:s|ing)?|listen(?:s|ed|ing)?|ignore(?:s|d|ing)?|respect(?:s|ed|ing)?|dismiss(?:es|ed|ing)?)\b",
)

def _lived_relational_structure(query):
    """Recognize relational structure from lived-situation form, not topic alone."""
    q = _normalize_query(query)
    first_person = bool(re.search(r"\b(?:i|i'm|im|my|me|we|our)\b", q, re.I))
    relational_other = any(re.search(pattern, q, re.I) for pattern in _RELATIONAL_PATTERNS)
    role_context = any(re.search(pattern, q, re.I) for pattern in _RELATIONAL_ROLE_PATTERNS)
    relational_action = any(re.search(pattern, q, re.I) for pattern in _RELATIONAL_ACTION_PATTERNS) or any(re.search(pattern, q, re.I) for pattern in _RELATIONAL_INTERACTION_PATTERNS)
    tension = bool(re.search(
        r"\b(?:but|however|although|yet|now|instead|then|eventually|until|again|"
        r"same thing|can't|cannot|don't|doesn't|not sure|unsure|hard|difficult|"
        r"overwhelmed|want to|need to|have to|part of me|i wish|i don't know)\b",
        q,
        re.I,
    ))
    bounded_lookup = bool(re.search(
        r"\b(?:define|definition|what is|what does .* mean|meaning of|"
        r"look up|lookup|find (?:the|a) (?:resource|article|essay|page)|"
        r"where is|url|link)\b",
        q,
        re.I,
    ))
    return {
        "first_person": first_person,
        "relational_other": relational_other,
        "role_context": role_context,
        "relational_action": relational_action,
        "tension": tension,
        "bounded_lookup": bounded_lookup,
        "lived_relational": (
            first_person
            and (relational_other or role_context)
            and tension
            and (relational_action or role_context)
            and not bounded_lookup
        ),
    }


def _explicit_bounded_archive_request(query):
    """Detect an explicit request for a bounded Archive/resource operation.
    
    A model-generated processing label is not sufficient to suppress relational
    exploration. The visitor's own wording must establish that retrieval,
    definition, or lookup is actually what they are asking for.
    """
    q = _normalize_query(query)
    return bool(re.search(
        r"\b(?:"
        r"find|show|lookup|look up|link to|url for|where is|where can i find|"
        r"recommend (?:a|an|the)?\s*(?:resource|article|essay|page)|"
        r"suggest (?:a|an|the)?\s*(?:resource|article|essay|page)|"
        r"which (?:resource|article|essay|page)|"
        r"what (?:resource|article|essay|page)|"
        r"is there (?:a|an|anything|something)\s+(?:in|on)\s+(?:the )?"
        r"(?:living archive|archive|site|website)|"
        r"anything in (?:the )?(?:living archive|archive|site|website)|"
        r"resource about|article about|essay about|page about|"
        r"definition of|meaning of|what does .* mean|what is"
        r")\b",
        q,
        re.I,
    ))

# v488.72 — SYSTEMIC RELATIONAL BOUNDARY CONTRACT
#
# This boundary is intentionally owned by the request seam, not by the
# provider/model router and not by Basic Inquiry. It answers one structural
# question only: does the visitor's lived situation centrally involve a
# relationship that they are trying to understand or navigate?
#
# It is not a topic keyword gate. It requires converging evidence from the
# visitor's form: a lived relational counterpart/context, an interactional
# dynamic, and an inquiry/uncertainty signal. Explicit bounded retrieval and
# definition requests remain outside the relational lane. Safety is handled
# earlier and always retains precedence.
RELATIONAL_BOUNDARY_CONTRACT_VERSION = "v1"

_RELATIONAL_COUNTERPART_PATTERNS = (
    r"\\bmy\\s+(?:husband|wife|spouse|partner|boyfriend|girlfriend|father|mother|parent|parents|son|daughter|child|brother|sister|friend|friends|colleague|coworker|co-worker|manager|supervisor|boss|employee|employer|client|customer|teacher|student|mentor|neighbor|landlord|tenant)\\b",
    r"\\b(?:someone|somebody|a person|another person|people|person)\\s+(?:i|we)\\s+(?:care about|love|trust|work with)\\b",
    r"\\b(?:someone|somebody|a person)\\s+(?:close to|important to)\\s+me\\b",
    r"\\b(?:between us|between me and|between you and)\\b",
    r"\\b(?:our|this|the)\\s+relationship\\b",
    r"\\b(?:with|from)\\s+(?:someone|somebody|my)\\b",
)

_RELATIONAL_DYNAMIC_PATTERNS = (
    r"\\b(?:argument|arguments|fight|fights|fighting|conflict|tension|disagreement|disagree|misunderstanding|misunderstand|distance|disconnect(?:ed|ion)?|withdraw(?:al|ing)?|defensive|shut(?:s|ting)?\\s+down|stop(?:s|ped|ping)?\\s+talking|go(?:es|ing)?\\s+quiet|resent(?:ment|ful)?|trust|distrust|boundary|boundaries|communication|communicate|expectation|expectations|control(?:led|ling)?|critic(?:ize|ized|ism)|blame|blaming|forgive(?:ness)?|support|one[- ]sided|recipro(?:cal|city)|rely|depend|keeps?\\s+asking|keeps?\\s+doing|same\\s+thing|same\\s+argument|same\\s+fight|same\\s+pattern|cycle|loop)\\b",
    r"\\b(?:gets?|becomes?|become)\\s+(?:angry|defensive|quiet|distant)\\b",
    r"\\b(?:i|we)\\s+(?:keep|keeps|kept)\\b",
)

_RELATIONAL_INQUIRY_PATTERNS = (
    r"\\b(?:i|we)\\s+(?:want|need|wonder|hope|wish)\\s+to\\s+(?:understand|figure out|make sense|see|know)\\b",
    r"\\b(?:i|we)\\s+(?:don't|do not|can't|cannot|am not|are not)\\s+(?:understand|know|tell|see)\\b",
    r"\\b(?:what(?:'s| is)|why|how)\\b.{0,120}\\b(?:happening|between us|relating|relationship|treat|respond|react|communicat|understand|make sense)\\b",
    r"\\b(?:understand|make sense of|figure out|explore|see)\\b.{0,100}\\b(?:between us|with (?:my|someone)|relationship|pattern|dynamic|cycle|interaction)\\b",
    r"\\b(?:i|we)\\s+(?:feel|feels|felt|struggle|struggling|uncertain|unsure|confused|stuck|hurt|worried)\\b",
)


def _relational_boundary_decision(query):
    """Return the authoritative request-boundary decision for lived relationships.

    The decision is deliberately evidence-based rather than a single-word
    trigger. A relationship lane opens when at least two independent structural
    dimensions converge, including a lived relational counterpart/context and
    an interactional or inquiry signal. This prevents ordinary topical mentions
    of relationships from becoming specialist handoffs while ensuring natural
    descriptions of recurring relational dynamics do not fall into Basic Inquiry.
    """
    q = _normalize_query(query)
    if not q:
        return {"open": False, "contract_version": RELATIONAL_BOUNDARY_CONTRACT_VERSION, "reason": "empty"}

    bounded = bool(_explicit_bounded_archive_request(q))
    definition = bool(re.search(
        r"\\b(?:define|definition|meaning of|what does .* mean|what is)\\b",
        q,
        re.I,
    ))
    if bounded or definition:
        return {
            "open": False,
            "contract_version": RELATIONAL_BOUNDARY_CONTRACT_VERSION,
            "reason": "bounded_archive_or_definition_request",
        }

    first_person = bool(re.search(r"\\b(?:i|i'm|im|me|my|we|our|us)\\b", q, re.I))
    counterpart = any(re.search(pattern, q, re.I) for pattern in _RELATIONAL_COUNTERPART_PATTERNS)
    dynamic = any(re.search(pattern, q, re.I) for pattern in _RELATIONAL_DYNAMIC_PATTERNS)
    inquiry = any(re.search(pattern, q, re.I) for pattern in _RELATIONAL_INQUIRY_PATTERNS)
    relational_term = bool(re.search(r"\\b(?:relationship|relationships|interpersonal|relational)\\b", q, re.I))
    explicit_between = bool(re.search(r"\\b(?:between us|between me and|between you and)\\b", q, re.I))

    score = 0
    if counterpart or relational_term or explicit_between:
        score += 2
    if dynamic:
        score += 2
    if inquiry:
        score += 1
    if first_person:
        score += 1

    # Strong lived relational structure: counterpart + dynamic + inquiry/first
    # person. This is the normal path for natural visitor language.
    open_boundary = bool(
        first_person
        and (counterpart or relational_term or explicit_between)
        and dynamic
        and (inquiry or first_person)
    )

    # A compact relational sentence may omit an explicit counterpart while
    # still clearly describing a mutual interaction (e.g. "we keep arguing").
    # Require both first-person plural framing and an interactional dynamic.
    if not open_boundary and first_person and bool(re.search(r"\\bwe\\b", q)) and dynamic and inquiry:
        open_boundary = True

    return {
        "open": open_boundary,
        "contract_version": RELATIONAL_BOUNDARY_CONTRACT_VERSION,
        "reason": "lived_relational_structure" if open_boundary else "insufficient_converging_relational_evidence",
        "score": score,
        "signals": {
            "first_person": first_person,
            "counterpart": counterpart,
            "dynamic": dynamic,
            "inquiry": inquiry,
            "relational_term": relational_term,
            "explicit_between": explicit_between,
            "bounded": bounded,
            "definition": definition,
        },
    }


def _should_open_relationship_specialist(query, interpretation=None):
    """Compatibility wrapper around the single authoritative boundary contract."""
    decision = _relational_boundary_decision(query)
    return bool(decision.get("open"))


# v488.72 regression probes: these represent the actual visitor language that
# previously escaped into Basic Inquiry. They are intentionally phrased without
# requiring the visitor to know the words "relationship" or "relational".
_RELATIONAL_BOUNDARY_PROBES = (
    "My husband and I keep having the same argument about money. We both care about each other, but somehow we end up defensive and stop talking. I want to understand what is happening between us.",
    "I keep getting angry with someone I care about, and I don't know what to do with that anger. Is there anything in the Living Archive that might help me think about it?",
    "My colleague and I keep misunderstanding each other. I want to understand why our conversations become tense and then go nowhere.",
    "Whenever I bring something up, my partner becomes defensive, I get angry, they withdraw, and a few days later the same thing happens again.",
)
for _relational_probe in _RELATIONAL_BOUNDARY_PROBES:
    if not _relational_boundary_decision(_relational_probe).get("open"):
        raise RuntimeError("USE v488.72 invariant failed: natural relational boundary probe not recognized")

_RELATIONAL_BOUNDARY_NEGATIVE_PROBES = (
    "What is the meaning of relationship in the Living Archive?",
    "Find an article about setting boundaries in relationships.",
    "What is a healthy relationship?",
)
for _relational_probe in _RELATIONAL_BOUNDARY_NEGATIVE_PROBES:
    if _relational_boundary_decision(_relational_probe).get("open"):
        raise RuntimeError("USE v488.72 invariant failed: bounded/topical relationship request was misrouted")


def _should_open_relationship_specialist(query, interpretation=None):
    """Systemic Guide-side arbitration for lived relational inquiries.
    
    The visitor's processing need is determined from the form of the request,
    not from a potentially over-broad model label. A lived relational inquiry
    remains relational unless the visitor explicitly asks the Guide to perform
    a bounded retrieval/definition/lookup operation.
    """
    structure = _lived_relational_structure(query)
    if not structure["lived_relational"]:
        return False
    if structure["bounded_lookup"] or _explicit_bounded_archive_request(query):
        return False
    return True


_route_probe_lived_relational = "I promised my father I'd take care of something for him. At the time it felt natural. Now the responsibility has become much bigger than I expected, and part of me wants to back out. But I gave him my word."
if not _lived_relational_structure(_route_probe_lived_relational)["lived_relational"]:
    raise RuntimeError("USE v487.88 routing invariant failed: lived relational structure not recognized")
if not _should_open_relationship_specialist(_route_probe_lived_relational, {"processing_need": "retrieval"}):
    raise RuntimeError("USE v487.88 routing invariant failed: model retrieval label suppressed lived relational routing")
if _should_open_relationship_specialist(
    "Is there an article in the Living Archive about setting boundaries with a parent?",
    {"processing_need": "retrieval"},
):
    raise RuntimeError("USE v487.88 routing invariant failed: explicit Archive retrieval delegated to relationship")

# v488.71 regression guard: natural-language conflict nouns must count as
# lived relational action. "Argument" is relational structure even when the
# visitor does not use the verb "argue".
_route_probe_argument_noun = (
    "I keep having the same argument with someone I care about, but I'm not "
    "sure whether the problem is really between us or something I'm bringing into it."
)
if not _lived_relational_structure(_route_probe_argument_noun)["lived_relational"]:
    raise RuntimeError("USE v488.71 routing invariant failed: argument-noun relational inquiry not recognized")
if not _should_open_relationship_specialist(_route_probe_argument_noun, {"processing_need": "orientation"}):
    raise RuntimeError("USE v488.69 routing invariant failed: argument-noun inquiry did not open relationship specialist")

# v488.69 regression guard: natural-language fight nouns must remain inside
# the same relational boundary.
_route_probe_fight_noun = (
    "I keep having the same fight with my partner, and I can't tell whether "
    "we're actually disagreeing about the issue or reacting to each other."
)
if not _should_open_relationship_specialist(_route_probe_fight_noun, {"processing_need": "orientation"}):
    raise RuntimeError("USE v488.69 routing invariant failed: fight-noun inquiry did not open relationship specialist")

# v487.92 regression guard: relational reciprocity must route to Seeing the
# Relationship even when the visitor does not use conflict/boundary language.
_route_probe_reciprocity = (
    "My friend always asks me for support when they need something, but "
    "whenever I need them, they disappear. I'm starting to wonder whether "
    "this friendship is one-sided."
)
if not _lived_relational_structure(_route_probe_reciprocity)["lived_relational"]:
    raise RuntimeError("USE v487.92 routing invariant failed: reciprocity pattern not recognized")
if not _should_open_relationship_specialist(_route_probe_reciprocity, {"processing_need": "orientation"}):
    raise RuntimeError("USE v487.92 routing invariant failed: reciprocity inquiry did not open relationship specialist")

# v487.95 regression guard: the observed defensive/anger/withdrawal cycle must
# bypass the Guide routing-model call and open HRN immediately.
_route_probe_defensive_cycle = (
    "Whenever I bring up something that bothers me, my partner becomes defensive. "
    "Then I get angry, they withdraw, and eventually we stop talking. "
    "A few days later everything seems fine until the same thing happens again."
)
if not _lived_relational_structure(_route_probe_defensive_cycle)["lived_relational"]:
    raise RuntimeError("USE v487.97 routing invariant failed: defensive cycle not recognized")
if not _should_open_relationship_specialist(
    _route_probe_defensive_cycle, {"processing_need": "orientation"}
):
    raise RuntimeError("USE v487.95 routing invariant failed: defensive cycle did not open relationship specialist")

# v487.97 regression guard: workplace/authority relationships must use the
# same immediate HRN boundary as family/partnership relationships. This avoids
# sending an unresolved lived relationship through the expensive legacy Guide
# retrieval path, which can surface as a visitor-facing connection failure when
# the request exceeds the browser's patience window.
_route_probe_authority_relationship = (
    "My manager says they trust me, but they check everything I do and "
    "constantly ask for updates. I feel like I'm being controlled even "
    "though they keep saying they trust me."
)
if not _lived_relational_structure(_route_probe_authority_relationship)["lived_relational"]:
    raise RuntimeError("USE v487.97 invariant failed: authority/workplace relational structure not recognized")
if not _should_open_relationship_specialist(_route_probe_authority_relationship, {"processing_need": "orientation"}):
    raise RuntimeError("USE v487.97 invariant failed: authority/workplace inquiry did not open relationship specialist")



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


def _build_doorway_candidates_for_use(docs):
    """Normalize pre-selected doorway mappings without changing selection authority."""
    from shared_intelligence_primitives import normalize_doorway_candidates as _normalize_shared_doorways
    return _normalize_shared_doorways(docs or [])

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
    claims = _normalize_shared_claims_for_use(docs or [])
    synthesis = _build_shared_synthesis_material_for_use(claims)
    claims_for_composition = _legacy_claims_from_synthesis(synthesis, claims)
    primary = _canonical_primary_from_docs(canonical_docs, query, profile)
    if primary:
        secondary = _select_adjacent(claims_for_composition, query, primary["title"], profile)
    else:
        eligible = []
        for index, claim in enumerate(claims_for_composition):
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
        "Before trying to solve the question, it can help to notice what is most present in the experience—what hurts, what feels uncertain, what you may be longing for, or what you are not yet ready to name.",
        _base._recommendation_foothold(profile),
        _recommendation_rationale(primary, profile),
        "This doorway is offered as a reflection gateway, not as a complete explanation or prescription. It is one place to begin noticing what this question opens for you.",
    ]
    if secondary:
        parts.append(f"A nearby path is [{secondary['title']}]({secondary['url']}), which opens another aspect of the question without asking you to treat either doorway as the whole answer.")
    parts.append("You can stay with this lens, follow the connected material, or return with another part of the question that feels more relevant.")
    return "\n\n".join(parts)


def _normalize_shared_evidence_for_use(documents, *, provenance="supplied"):
    """Apply the shared evidence transformation and return the legacy USE shape."""
    return normalize_documents_for_use(documents, provenance=provenance)


def _normalize_shared_claims_for_use(candidates):
    """Normalize legacy USE claim dictionaries through the shared claim primitive."""
    raw = []
    evidence_ids = []
    for index, candidate in enumerate(candidates or []):
        if not isinstance(candidate, dict):
            continue
        text = str(candidate.get("text") or "").strip()
        if not text:
            continue
        evidence_id = str(candidate.get("id") or f"claim:{index + 1}")
        evidence_ids.append(evidence_id)
        raw.append({
            "text": text,
            "evidence_ids": [evidence_id],
            "claim_type": "interpretation" if candidate.get("epistemic") == "interpretive" else "observation",
            "epistemic": str(candidate.get("epistemic") or "uncertain"),
        })
    normalized = _shared_normalize_claims(raw, evidence_ids=evidence_ids)
    source_by_text = {
        str(candidate.get("text") or "").strip(): candidate
        for candidate in (candidates or [])
        if isinstance(candidate, dict)
    }
    return [
        {
            **source_by_text.get(item.text, {}),
            "text": item.text,
            "epistemic": item.epistemic,
        }
        for item in normalized
    ]


def _build_shared_synthesis_material_for_use(claims):
    """Package already-normalized USE claims through the shared synthesis primitive."""
    shared_claims = [_shared_claim_object(item) for item in (claims or []) if isinstance(item, dict)]
    return _shared_build_synthesis_material([item for item in shared_claims if item is not None])


def _shared_claim_object(item):
    """Convert one legacy claim mapping to the shared Claim object."""
    evidence_id = str(item.get("id") or "claim:1")
    normalized = _shared_normalize_claims(
        [{
            "text": str(item.get("text") or "").strip(),
            "evidence_ids": [evidence_id],
            "claim_type": "interpretation" if item.get("epistemic") == "interpretive" else "observation",
            "epistemic": str(item.get("epistemic") or "uncertain"),
        }],
        evidence_ids=[evidence_id],
    )
    return normalized[0] if normalized else None


def _legacy_claims_from_synthesis(synthesis, fallback_claims):
    """Return the legacy claim mappings represented by SynthesisMaterial."""
    fallback_by_text = {str(item.get("text") or "").strip(): item for item in (fallback_claims or []) if isinstance(item, dict)}
    return [{
        **fallback_by_text.get(item.text, {}),
        "text": item.text,
        "epistemic": item.epistemic,
    } for item in (getattr(synthesis, "claims", ()) or ())]


def _parse_context_documents(context_blocks):
    parser = getattr(use_core, "_parse_context_documents", None)
    if callable(parser):
        parsed = parser(context_blocks)
        return _normalize_shared_evidence_for_use(parsed, provenance="retrieved-context")
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
    """Serialize conversation history without losing safety-loop questions.

    The Guide receives structured turns from specialist frontends. A safety
    assistant turn can contain both a human-facing message and the active
    safety question. The previous serializer silently discarded the question
    whenever content was present, collapsing the safety state machine on short
    answers such as "yes" or "no".

    This is a shared conversation-boundary contract, not a UI patch: every
    downstream specialist receives the same lossless recent conversation.
    """
    if not history:
        return ""
    if isinstance(history, str):
        return history.strip()

    parts = []
    for item in list(history)[-8:]:
        if isinstance(item, dict):
            role = str(item.get("role") or item.get("speaker") or "").strip()
            content = str(
                item.get("content")
                or item.get("message")
                or item.get("text")
                or item.get("response")
                or ""
            ).strip()
            question = str(item.get("question") or "").strip()
            if content:
                parts.append(f"{role}: {content}" if role else content)
            if question and question != content:
                question_role = f"{role} question" if role else "question"
                parts.append(f"{question_role}: {question}")
        elif item is not None:
            value = str(item).strip()
            if value:
                parts.append(value)
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

RELATIONSHIP_JOURNEY_CONTRACT_VERSION = "v2"
_RELATIONSHIP_JOURNEY_ACTIONS = frozenset({"continue", "end"})
_RELATIONSHIP_LOCAL_STATES = frozenset({"in_progress", "spiral_complete", "journey_complete"})

def _relationship_integrated_response(contribution):
    """Preserve HRN's human response and its steering question; doorway selection stays with USE at closure."""
    human = str(contribution.get("human_response") or "").strip()
    if not human:
        return ""
    movement = contribution.get("movement") or {}
    parts = [human]
    question = str(movement.get("question") or "").strip()
    if question and not bool(movement.get("rest")):
        parts.append(question)
    return "\n\n".join(parts)


def _relationship_journey_state(contribution):
    movement = contribution.get("movement") or {}
    state = str(
        movement.get("journey_state")
        or contribution.get("journey_state")
        or ""
    ).strip().casefold()
    if state not in _RELATIONSHIP_LOCAL_STATES:
        state = "spiral_complete" if bool(
            movement.get("spiral_complete")
            or movement.get("topic_complete")
            or movement.get("unit_complete")
        ) else "in_progress"
        if str(movement.get("movement_state") or "").strip().casefold() in {"journey_complete", "complete"}:
            state = "journey_complete"
    action = str(
        movement.get("journey_action")
        or contribution.get("journey_action")
        or ""
    ).strip().casefold()
    if action not in _RELATIONSHIP_JOURNEY_ACTIONS:
        action = "continue" if state != "journey_complete" else "end"
    return {
        "state": state,
        "action": action,
        "spiral_complete": state == "spiral_complete",
        "journey_complete": state == "journey_complete",
    }


def _build_journey_contribution_for_use(body):
    """Package HRN closure material without selecting, retrieving, or generating."""
    from shared_intelligence_primitives import normalize_journey_contribution as _normalize_shared_journey
    payload = {
        "original_question": body.get("original_question") or body.get("query"),
        "conversation": body.get("conversation"),
        "thread_summary": body.get("thread_summary"),
        "working_hypothesis": body.get("working_hypothesis"),
        "completed_insight": body.get("completed_insight"),
        "perspective_delta": body.get("perspective_delta"),
        "body_of_thought": body.get("body_of_thought"),
        "underlying_need": body.get("underlying_need"),
        "desired_condition": body.get("desired_condition"),
        "next_horizon": body.get("next_horizon"),
        "resource_fit": body.get("resource_fit"),
        "journey_synthesis": body.get("journey_synthesis"),
        "journey_action": body.get("journey_action"),
        "journey_ledger": body.get("journey_ledger"),
        "fractal_records": body.get("fractal_records"),
        "round_synthesis_history": body.get("round_synthesis_history"),
    }
    return _normalize_shared_journey(payload)


async def _v48755_relational_return(request: Request):
    try:
        body = await request.json()
    except Exception:
        body = {}
    if not isinstance(body, dict):
        body = {}

    session_id = str(body.get("session_id") or "").strip()
    journey_contribution = _build_journey_contribution_for_use(body)
    original_question = journey_contribution.original_question
    conversation = journey_contribution.conversation
    thread_summary = journey_contribution.thread_summary
    working_hypothesis = journey_contribution.working_hypothesis
    completed_insight = journey_contribution.completed_insight
    perspective_delta = journey_contribution.perspective_delta
    body_of_thought = journey_contribution.body_of_thought
    underlying_need = journey_contribution.underlying_need
    desired_condition = journey_contribution.desired_condition
    next_horizon = journey_contribution.next_horizon
    resource_fit = journey_contribution.resource_fit
    journey_action = journey_contribution.journey_action
    journey_synthesis = journey_contribution.journey_synthesis
    journey_ledger = dict(journey_contribution.journey_ledger)
    fractal_records = list(journey_contribution.fractal_records)
    round_synthesis_history = list(journey_contribution.round_synthesis_history)

    if journey_action != "end":
        return JSONResponse(
            status_code=409,
            content={
                "ok": False,
                "version": APP_VERSION,
                "error_type": "relational_return_requires_closure",
                "response": "The relational journey is still open.",
            },
        )

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

    # The Guide receives the whole journey only after the visitor has explicitly
    # chosen to close it. Mid-journey topic-fractal junctions never trigger this path.
    synthesis_parts = [
        original_question,
        "Conversation thread: " + thread_summary,
        "What became clearer: " + perspective_delta,
        "Completed insight: " + completed_insight,
        "Underlying need: " + underlying_need,
        "Desired condition: " + desired_condition,
        "Living body of thought: " + body_of_thought,
        "Previous topic-fractal syntheses: " + json.dumps(fractal_records, ensure_ascii=False),
        "Round-by-round synthesis history: " + json.dumps(round_synthesis_history, ensure_ascii=False),
        "Journey ledger: " + json.dumps(journey_ledger, ensure_ascii=False),
        "Whole-journey synthesis from Seeing the Relationship: " + journey_synthesis,
        "Next horizon: " + next_horizon,
        "Canonical doorway fit noted by Seeing the Relationship: " + resource_fit,
    ]
    synthesis_query = "\n".join(part for part in synthesis_parts if part.split(": ", 1)[-1].strip())
    synthesis_query = synthesis_query[:18000]

    try:
        context_data = _original_fetch_canonical_context(synthesis_query)
        canonical_context = str(
            context_data.get("canonical_link_context")
            or context_data.get("context_blocks")
            or ""
        ) if isinstance(context_data, dict) else ""
        docs = _parse_context_documents(canonical_context)

        # The final doorway is still a Guide responsibility. The completed
        # perspective, not the visitor's opening wording alone, governs the gift.
        profile = _base._inquiry_profile(synthesis_query)
        profile["action"] = "recommendation"
        profile["recommendation"] = max(float(profile.get("recommendation", 0.0)), 0.95)
        outward = _sanitize_outward_context(synthesis_query, docs, profile)
        primary = _canonical_primary_from_docs(outward, synthesis_query, profile)

        if not primary:
            # One bounded retry against the strongest earned perspective.
            fallback_query = " ".join(
                value for value in (
                    journey_synthesis,
                    completed_insight,
                    perspective_delta,
                    underlying_need,
                    next_horizon,
                    original_question,
                ) if value
            )[:10000]
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
            "The Guide v487.66 seamless HRN gift return: "
            f"session={session_id or 'none'}, "
            f"selected={primary['title'] if primary else 'none'}, "
            f"conversation_chars={len(conversation)}, "
            f"ledger_fractals={len(fractal_records)}, "
            f"round_syntheses={len(round_synthesis_history)}, "
            f"query={_normalize_query(original_question)[:120]}"
        )

        journey_payload = {
            "state": "complete",
            "session_id": session_id,
            "perspective_delta": perspective_delta,
            "completed_insight": completed_insight,
            "next_horizon": next_horizon,
            "journey_synthesis": journey_synthesis,
            "fractal_records": fractal_records,
            "round_synthesis_history": round_synthesis_history,
        }

        if primary:
            return JSONResponse(
                status_code=200,
                content={
                    "ok": True,
                    "version": APP_VERSION,
                    "request_id": session_id,
                    "intent": "RELATIONAL_CANONICAL_RETURN",
                    "response": "There is a place in the Archive that may carry this new perspective further.",
                    "display_mode": "hrn",
                    "canonical_doorway": {
                        "title": primary["title"],
                        "url": primary["url"],
                    },
                    "relational_journey": journey_payload,
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
                "response": "You have brought the conversation to a meaningful place. No doorway was close enough to offer honestly from what emerged.",
                "canonical_doorway": None,
                "display_mode": "hrn",
                "relational_journey": journey_payload,
                "visitor_boundary_version": APP_VERSION,
            },
        )
    except Exception as exc:
        print(f"The Guide v487.63 relational closure failed safely: {exc}")
        return JSONResponse(
            status_code=200,
            content={
                "ok": False,
                "version": APP_VERSION,
                "request_id": session_id,
                "intent": "RELATIONAL_CANONICAL_RETURN",
                "response": "The conversation is complete, but the Archive doorway could not be prepared right now.",
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
    "atlas",
    "navigator",
    "systems_ph",
    "safety",
    "glossary",
    "glyph",
    "case",
    "fsd",
    "guide_node",
})

_GUIDE_ROUTE_PROMPT = """You are the private Round 1 interpretation layer behind The Guide,
the macro orientation layer of the Living Archive.

The visitor's first question is an open human inquiry. Do not treat it as a
keyword-classification exercise. Before choosing a route, reason about what
the visitor may actually be trying to understand, resolve, explore, find,
change, or move toward.

Use the same disciplined first-move reasoning used by Seeing the Relationship,
but at the macro level of the Archive.

First distinguish:
- what the visitor literally says;
- the presenting situation or proposition;
- the experience or human reality being brought;
- the assumption, explanation, or proposed solution the visitor is already
  carrying;
- the underlying question or tension that may be more important than the
  literal wording;
- what remains genuinely uncertain;
- what kind of movement would actually help the visitor now.

Do not assume the visitor's explanation is correct. Do not manufacture hidden
motives, diagnoses, mental states, or facts about other people. Preserve
uncertainty. A tentative interpretation is not a fact.

Then determine what kind of processing would best serve the visitor at this
moment.

Possible routes:
- guide: The Guide remains with broad Archive orientation/navigation
- relationship: Seeing the Relationship; open relational exploration across
  self, person-to-person, family, group, community, organization,
  institution, and intergroup situations
- formation: Stewardship Formation Navigator; formation-oriented inquiry about
  what a situation may be asking someone to learn, practice, examine, or carry
- catalogue: Stewardship Catalogue; bounded stewardship-resource navigation
- atlas: Living Archive Atlas Finder; bounded visual Reference Map navigation
- navigator: Living Archive Navigator; the universal entry/orientation surface when the visitor is trying to find where to begin, how to enter the Living Archive, or how to discover a useful path through it rather than retrieve one particular resource
- systems_ph: Philippine Systems Lens; bounded inquiry into interacting
  Philippine systems and conditions
- safety: Safety / Crisis
- glossary: vocabulary/definition lookup
- glyph: glyph/symbol lookup
- case: Case Study search; bounded structural case matching based on the visitor situation
- fsd: Fractal Systems Diagnostic; native systems-pattern orientation and diagnostic navigation
- guide_node: a specific approved Guide Node; use only when the visitor's need clearly points to one of the approved destinations supplied below

Important routing principles:
- The initial question may be about anything. Do not require a domain keyword.
- Do not route by topic alone. Route by the kind of movement or processing the
  visitor appears to need.
- A relational topic does not automatically mean Seeing the Relationship.
- Seeing the Relationship is appropriate when the lived human situation itself
  is central and exploratory, and relational inquiry is likely to create more
  perspective than immediately selecting a resource.
- A question can begin in one terrain and reveal another. On later turns,
  reconsider the accumulated conversation rather than protecting the initial
  route.
- If the visitor explicitly seeks a definition, glyph, catalogue item, or
  bounded systems/formation task, honor that clear intent.
- When the visitor is asking where to begin, how to enter, or how to find a
  useful way into the Living Archive or site as a whole, prefer navigator when
  that orientation need is central. Do not require the visitor to name the
  Navigator.
- If the visitor is presenting a lived situation whose useful next step is
  discovery rather than retrieval, prefer the processing mode that can create
  that discovery.
- Do not select a specialist merely because its subject appears somewhere in
  the question.
- Preserve ambiguity when no specialized processing is clearly warranted.
- Safety concerns remain the highest boundary.
- The Guide remains the steward of the whole journey even when processing is
  delegated.
- The specialist is an internal capability, not a visitor-facing explanation
  of the machinery.

Return ONLY valid JSON with exactly these keys:
{
  "human_reality": "what human reality is being brought, if discernible",
  "presenting_situation": "what is happening on the surface",
  "visitor_proposition": "the explanation, assumption, or proposed solution the visitor is carrying",
  "underlying_question": "what the visitor may actually be trying to understand or resolve",
  "uncertainty": "the uncertainty whose clarification would most change direction",
  "desired_movement": "the kind of movement that would help now",
  "processing_need": "exploration|orientation|retrieval|definition|lookup|formation|systems_inquiry|safety|clarification",
  "route": "guide|relationship|formation|catalogue|atlas|navigator|systems_ph|safety|glossary|glyph|case|fsd|guide_node",
  "mode": "direct|delegated_journey|lookup|clarify|safety",
  "confidence": 0.0,
  "reason": "short internal explanation of why this processing mode and route fit",
  "alternatives": ["guide"],
  "glossary_term": "canonical term only when route=glossary",
  "guide_node_id": "canonical Guide Node ID only when route=guide_node"
}

The interpretation fields are internal reasoning instruments. They are not
visitor-facing labels.

A critical distinction:
- route answers WHERE the visitor should be processed;
- mode answers HOW the question should be processed there.
Do not return relationship + direct when the visitor's lived relational
situation itself calls for exploratory relational processing. Likewise, do not
force delegated processing when the visitor is simply asking for a resource
or definition.

Think strategically: the first move sets the tone for the journey. The goal
is not to solve the visitor's question in Round 1. The goal is to choose the
most intelligent next mode of engagement.
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


def _normalize_glossary_term(query, interpretation=None):
    """Extract the bounded canonical term for the native Glossary lookup.

    The Glossary owns term resolution. USE only converts a definition/meaning
    question into the term that the existing Glossary search contract expects.
    It never performs glossary retrieval or duplicates the Glossary registry.
    """
    interpretation = interpretation or {}
    candidate = str(interpretation.get("glossary_term") or "").strip()
    if candidate:
        candidate = re.sub(r"^[\s\"']+|[\s\"'?.!]+$", "", candidate)
        candidate = re.sub(r"^(?:the\s+term\s+|the\s+word\s+|word\s+)", "", candidate, flags=re.I)
        if 1 <= len(candidate) <= 120 and not re.search(r"[?\n]", candidate):
            return candidate

    normalized = re.sub(r"\s+", " ", str(query or "").strip()).strip()
    patterns = (
        r"^(?:what does|what is|what's)\s+(?:the\s+)?(?:meaning\s+of\s+)?(.+?)(?:\s+mean)?[?!.]?$",
        r"^(?:what is the meaning of|meaning of|define|definition of)\s+(.+?)[?!.]?$",
    )
    for pattern in patterns:
        match = re.match(pattern, normalized, re.I)
        if match:
            term = re.sub(r"^[\s\"']+|[\s\"'?.!]+$", "", match.group(1))
            term = re.sub(r"^(?:the\s+term\s+|the\s+word\s+|word\s+)", "", term, flags=re.I)
            if 1 <= len(term) <= 120:
                return term
    embedded = _extract_embedded_glossary_term(query)
    if embedded:
        return embedded
    return ""


def _extract_embedded_glossary_term(query):
    """Extract a bounded glossary term when definition intent is embedded in a longer question.

    This is a visitor-boundary guard, not a second glossary search engine.
    It exists so genuine meaning/definition requests remain Glossary-owned even
    when an orientation phrase such as "where should I begin?" appears later
    in the same sentence.
    """
    normalized = re.sub(r"\s+", " ", str(query or "").strip()).strip()
    if not normalized:
        return ""

    patterns = (
        r"\b(?:the\s+)?(?:word|term)\s+([A-Za-z][A-Za-z0-9-]*(?:\s+[A-Za-z][A-Za-z0-9-]*){0,5}?)\b.{0,120}?\b(?:actually\s+)?means?\b",
        r"\b(?:not\s+sure|unsure|unclear)\s+what\s+(?:the\s+)?([A-Za-z][A-Za-z0-9-]*(?:\s+[A-Za-z][A-Za-z0-9-]*){0,5}?)\s+(?:actually\s+)?means?\b",
        r"\bwhat\s+(?:the\s+)?([A-Za-z][A-Za-z0-9-]*(?:\s+[A-Za-z][A-Za-z0-9-]*){0,5}?)\s+is\s+all\s+about\b",
    )

    for pattern in patterns:
        match = re.search(pattern, normalized, re.I)
        if not match:
            continue

        term = re.sub(
            r"^[\s\"']+|[\s\"'?.!]+$",
            "",
            match.group(1),
        )
        term = re.sub(
            r"\s+(?:here|there)$",
            "",
            term,
            flags=re.I,
        )
        term = re.sub(
            r"^(?:the\s+term\s+|the\s+word\s+|word\s+)",
            "",
            term,
            flags=re.I,
        )

        if 1 <= len(term) <= 120 and not re.search(r"[?\n]", term):
            return term

    return ""


# v488.00 regression guards.
if _normalize_glossary_term("What does forgiveness mean?") != "forgiveness":
    raise RuntimeError("USE v488.00 invariant failed: glossary term extraction")
if _normalize_glossary_term("What does the word stewardship mean?") != "stewardship":
    raise RuntimeError("USE v488.04 invariant failed: glossary word-prefix extraction")
if _normalize_glossary_term("What is the meaning of stewardship?") != "stewardship":
    raise RuntimeError("USE v488.00 invariant failed: glossary meaning extraction")
if _normalize_glossary_term("How do I forgive someone who hurt me?"):
    raise RuntimeError("USE v487.98 invariant failed: open inquiry became glossary lookup")
if _normalize_glossary_term(
    "I keep seeing the word stewardship here, but I'm not sure what it actually means. Where should I begin?"
) != "stewardship":
    raise RuntimeError("USE v488.68 invariant failed: embedded word-meaning extraction")
if _normalize_glossary_term(
    "I want to know what stewardship is all about? How is it different from leadership, or management for that matter?"
) != "stewardship":
    raise RuntimeError("USE v488.68 invariant failed: embedded 'all about' extraction")
if _normalize_glossary_term("Where should I begin exploring the Archive?"):
    raise RuntimeError("USE v488.68 invariant failed: orientation request became glossary lookup")


def _catalogue_handoff_url(query):
    """Build the native Stewardship Catalogue destination for a bounded handoff.

    The Catalogue owns its own search and presentation. USE only carries the
    visitor's original request across the specialist boundary; it does not
    duplicate Catalogue retrieval or ranking.
    """
    return (
        "https://geralddaquila.com/explore-the-stewardship-catalogue/"
        + "?catalogue_query="
        + quote(str(query or "").strip(), safe="")
    )


def _atlas_handoff_url(query):
    """Build the native Living Archive Atlas Finder destination for a bounded handoff.

    The Atlas Finder owns its own candidate retrieval, Groq semantic selection,
    visual-asset resolution, and presentation. USE only carries the visitor's
    original inquiry across the specialist boundary.
    """
    return (
        "https://geralddaquila.com/the-living-archive-atlas/"
        + "?atlas_query="
        + quote(str(query or "").strip(), safe="")
    )


def _fsd_handoff_url(query):
    """Build the native Fractal Systems Diagnostic landing page destination.

    FSD owns its complete diagnostic experience after arrival. USE only
    identifies the native doorway and sends the visitor directly to it.
    """
    return "https://geralddaquila.com/fractal-systems-diagnostic-2/"


def _philippine_systems_handoff_url(query):
    """Build the native Philippine Systems landing page destination."""
    return "https://geralddaquila.com/understanding-the-philippines-culture-society-history-and-systemic-transformation/"


def _is_fsd_request(query):
    """Recognize explicit or high-confidence natural-language FSD doorway requests.

    FSD is a native diagnostic surface. The visitor should not have to know the
    name of the tool before The Guide can recognize a clear systems-level
    diagnostic need. The natural-language branch is deliberately bounded:
    systems context must co-occur with genuinely diagnostic/problem language.

    Important boundary:
    A visitor can legitimately want to explore recurring patterns in people
    and systems without asking for diagnosis. Broad pattern/series language
    therefore remains Guide-owned and must not be promoted to FSD merely
    because words such as "system", "pattern", or "recurring" appear.
    """
    q = _normalize_query(query)
    if not q:
        return False

    # Explicit FSD naming remains the strongest doorway.
    if re.search(r"\bfractal\s+systems?\s+diagnostic\b", q, re.I):
        return True
    if re.search(r"\bfsd\b", q, re.I):
        return True

    # A systems/organizational context is necessary for the natural-language
    # diagnostic boundary.
    systems_context = bool(re.search(
        r"\b(?:organization|organizational|institution|institutional|community|"
        r"system|systems|governance|structure|team|company|group)\b",
        q,
        re.I,
    ))
    if not systems_context:
        return False

    # Require an actual diagnostic/problematization signal. Do NOT treat
    # generic "pattern", "recurring", "underlying", or "deeper" language as
    # diagnostic by itself; those are legitimate Series & Analysis / Archive
    # territory signals.
    diagnostic_language = bool(re.search(
        r"\b(?:wrong|problem|problems|issue|issues|broken|failing|fails|failure|"
        r"not\s+working|isn't\s+working|aren't\s+working|stuck|"
        r"dysfunction(?:al)?|diagnos(?:e|is|tic)|assess|assessment|"
        r"what(?:\s+is|'s)\s+happening|"
        r"help\s+me\s+figure\s+(?:out\s+)?(?:what|how)|"
        r"underneath|maintaining|causing|driving|"
        r"where\s+(?:do\s+i|to)\s+start)\b",
        q,
        re.I,
    ))
    if diagnostic_language:
        return True

    # Preserve explicit systems/organizational diagnostic wording.
    return bool(re.search(
        r"\b(?:systems?|organizational|organization(?:al)?|institutional|community)\s+"
        r"(?:diagnostic|diagnosis|assessment)\b",
        q,
        re.I,
    ))


def _case_handoff_url(query):
    """Build the native Case Navigator destination.

    The Case Navigator owns structural inference, canonical stage/case
    resolution, explanation, and visitor-facing presentation. USE only
    carries the visitor's original inquiry across the native boundary.
    """
    return (
        "https://geralddaquila.com/how-to-access-the-case-studies/"
        + "?case_navigator_query="
        + quote(str(query or "").strip(), safe="")
    )


def _is_case_navigator_request(query):
    """Recognize a high-confidence request for the native Case Navigator."""
    q = _normalize_query(query)
    if not q:
        return False

    if re.search(r"\bcase\s+stud(?:y|ies)\b", q, re.I):
        return True

    if re.search(r"\b(?:relevant|matching|useful|best)\s+case\b", q, re.I):
        return True

    return bool(re.search(
        r"\b(?:find|show|search|which|what|relevant|matching)\b.{0,50}"
        r"\bcase(?:s)?\b",
        q,
        re.I,
    ))

def _glyph_handoff_url(query):
    """Build the native Guardian Glyph Finder destination.

    The Glyph Finder owns canonical Glyph identity resolution, semantic
    evidence matching, and visitor-facing presentation. USE only carries the
    visitor's original inquiry across the native search boundary.
    """
    return (
        "https://geralddaquila.com/guardian-glyph-archives/"
        + "?glyph_finder_query="
        + quote(str(query or "").strip(), safe="")
    )


def _is_glyph_finder_request(query):
    """Recognize a high-confidence request for the native Glyph Finder.

    This is a visitor-boundary rule, not a duplicate Glyph retrieval engine.
    Explicit Glyph/Guardian Glyph requests are handed to the native Finder
    before provider routing can turn them into an ordinary Guide answer.

    Natural-language symbol/icon/mark requests are also bounded here when the
    visitor is clearly asking to identify, find, or understand the symbol.
    This preserves the native Glyph Finder handoff without requiring the
    visitor
    to know the Archive's internal term "Glyph" first.
    """
    q = _normalize_query(query)
    if not q:
        return False

    if re.search(r"\bguardian\s+glyphs?\b", q, re.I):
        return True

    if re.search(r"\bglyphs?\b", q, re.I):
        return bool(re.search(
            r"\b(?:find|show|lookup|look\s+up|meaning|mean|which|what|"
            r"where|related\s+to|for|about|tell\s+me\s+about|"
            r"search|identify)\b",
            q,
            re.I,
        ))

    symbol_term = bool(re.search(r"\b(?:symbol|icon|mark)\b", q, re.I))
    if not symbol_term:
        return False

    lookup_language = bool(re.search(
        r"\b(?:find|show|lookup|look\s+up|meaning|mean|which|what|"
        r"where|identify|search|tell\s+me\s+about|"
        r"what(?:\s+is|'s)\s+this|what\s+does\s+this)\b",
        q,
        re.I,
    ))
    return lookup_language


# v488.22 Glyph Finder natural-language boundary guards.
if not _is_glyph_finder_request("What is this symbol?"):
    raise RuntimeError("USE v488.22 invariant failed: natural symbol lookup not recognized")
if not _is_glyph_finder_request("What does this icon mean?"):
    raise RuntimeError("USE v488.22 invariant failed: natural icon meaning lookup not recognized")
if not _is_glyph_finder_request("Find the mark for sovereignty"):
    raise RuntimeError("USE v488.22 invariant failed: natural mark lookup not recognized")
if _is_glyph_finder_request("The symbol in my report is too large"):
    raise RuntimeError("USE v488.22 invariant failed: non-lookup symbol context was misrouted")


def _navigator_handoff_url(query):
    """Build the native Living Archive Navigator entrance destination.

    The Navigator's first screen is a welcome/orientation entrance, not a
    question intake. The visitor's original USE question therefore does not
    travel into the landing URL. The Navigator owns the subsequent inquiry
    flow after the visitor chooses to begin.
    """
    return "https://geralddaquila.com/start-here-2/"

def _is_navigator_orientation_request(query):
    """Recognize high-confidence Archive/site orientation intent before retrieval.

    This is a governance boundary, not a topic classifier. Clear orientation
    requests are routed to the native Navigator before the Guide can answer
    them as ordinary retrieval. Ambiguous questions still go through the
    provider/model bank, preserving LLM judgment for cases that need it.
    The rule intentionally combines an orientation action with an Archive/site
    context, while also allowing strong first-entry language such as "I am new
    here" or "where do I begin". It does not inspect the subject matter of the
    requested resources.
    """
    q = _normalize_query(query)
    if not q:
        return False

    orientation_action = re.search(
        r"\b(?:where|how)\b.{0,80}\b(?:start|begin|get\s+started|"
        r"enter|find\s+my\s+way|explore|navigate)\b"
        r"|\b(?:best|good|right|useful)\s+(?:place|way)\s+to\s+"
        r"(?:start|begin)\b"
        r"|\b(?:new\s+to|new\s+here|new\s+around)\b"
        r"|\b(?:how\s+do\s+i|where\s+do\s+i)\s+(?:start|begin|"
        r"get\s+started|go\s+from\s+here)\b",
        q,
        re.I,
    )
    if not orientation_action:
        return False

    archive_context = re.search(
        r"\b(?:living\s+archive|archive|this\s+site|this\s+website|"
        r"this\s+site|site|website|here)\b",
        q,
        re.I,
    )
    first_entry = re.search(
        r"\b(?:i(?:\s+am|'m)\s+new\s+(?:to\s+)?(?:this\s+site|"
        r"this\s+website|the\s+archive|living\s+archive|here)|"
        r"i(?:\s+am|'m)\s+new\s+here|"
        r"where(?:'s|\s+is)\s+(?:the\s+)?(?:best|right|good)\s+place\s+"
        r"to\s+(?:start|begin)|"
        r"where\s+should\s+i\s+(?:start|begin))\b",
        q,
        re.I,
    )
    return bool(archive_context or first_entry)





def _is_explicit_atlas_request(query):
    """Recognize a bounded request for the native Atlas / Reference Map surface.

    Atlas routing must not turn ordinary uses of the word 'map' into a
    specialist handoff. Explicit Atlas/Reference Map language is authoritative;
    generic visual-map language is accepted only when paired with a clear
    map-finding verb and a Living Archive subject context.
    """
    q = _normalize_query(query)
    if re.search(r"\batlas\b", q, re.I):
        return True
    if re.search(r"\breference\s+maps?\b", q, re.I):
        return True

    map_request = bool(re.search(
        r"\b(?:find|show|explore|looking\s+for|look\s+for|search\s+for|browse)\b"
        r".{0,90}\b(?:visual\s+)?maps?\b",
        q,
        re.I,
    ))
    if not map_request:
        return False

    atlas_context = (
        r"\b(?:stewardship|governance|leadership|relationships?|systems?|"
        r"community|knowledge|discernment|transition|reciprocity|resilience|"
        r"sovereignty|human\s+development)\b"
    )
    return bool(re.search(atlas_context, q, re.I))


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

    if _is_fsd_request(query):
        return {
            "route": "fsd",
            "mode": "direct",
            "confidence": 0.98,
            "reason": "explicit Fractal Systems Diagnostic request",
            "alternatives": ["guide"],
            "source": "deterministic-fallback",
        }

    # If the reasoning model is unavailable, remain conservative at the
    # macro Guide layer. Do not substitute a deterministic topic classifier
    # for the open-ended Round 1 reasoning. Safety remains authoritative.
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


    if _is_explicit_atlas_request(query):
        return {
            "route": "atlas",
            "mode": "lookup",
            "confidence": 0.90,
            "reason": "explicit Atlas / Reference Map request",
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


def _guide_route_models():
    """Return the currently viable provider/model bank for diagnostics."""
    try:
        return provider_bank_snapshot(use_core).get("candidates", [])
    except Exception as exc:
        print(f"USE provider bank snapshot failed: {exc}")
        return []


def _guide_node_semantic_activation(query, interpretation, route):
    """Activate an approved Guide Node with explicit Level I/II precedence.

    Level I nodes are concrete destinations: tools, navigators, diagnostics,
    archives, and other specific experiences. Level II nodes are territories:
    broader bodies of knowledge or pathways.

    The registry remains structural. USE supplies the routing intelligence and
    this guard only arbitrates approved destinations after macro routing.
    """
    route_id = str(route or "guide").strip().casefold()
    if route_id in {"safety", "relationship", "glossary", "glyph", "fsd", "systems_ph", "atlas", "catalogue", "navigator"}:
        return None

    # Case Navigator is a bounded retrieval specialist, but the model can
    # occasionally choose it for broad pattern/series language because its
    # territory includes recurring stewardship patterns. Do not let that
    # mistaken macro route suppress an approved Guide Node. Preserve the Case
    # Navigator boundary when the visitor actually asks for cases.
    if route_id == "case" and _is_case_navigator_request(query):
        return None

    interpretation = interpretation if isinstance(interpretation, dict) else {}
    # Destination arbitration must remain anchored to the visitor's actual
    # words. The provider interpretation is useful for route selection, but it
    # must not be allowed to manufacture destination evidence and then use that
    # manufactured evidence to override the visitor's question. Otherwise a
    # mistaken macro interpretation such as "leadership/system challenge" can
    # make Leadership Challenge Navigator win a broad territory query that
    # actually belongs to Series & Analysis.
    raw_query = _normalize_query(query)
    query_terms = set(_subject_terms(raw_query))
    if not query_terms:
        return None

    territory_markers = (
        "explore", "overview", "broader", "broad", "territory", "area",
        "domain", "field", "pathway", "body of work", "body of knowledge",
        "where can i learn", "where can i explore", "what part of the archive",
        "which area", "which part", "understand the broader", "learn more about",
    )
    broad_request = any(marker in raw_query for marker in territory_markers)

    candidates = []
    for node in _guide_node_registry_snapshot():
        title = str(node.get("title") or "").strip()
        purpose = str(node.get("purpose") or "").strip()
        hints = [str(item).strip() for item in (node.get("semantic_hints") or []) if str(item).strip()]
        if not title:
            continue

        try:
            level = int(node.get("discovery_level", 1) or 1)
        except (TypeError, ValueError):
            level = 1
        if level not in {1, 2}:
            level = 1

        score = 0
        signals = 0
        distinctive = 0

        title_norm = _normalize_query(title)
        if title_norm and title_norm in raw_query:
            score += 12
            signals += 2
            distinctive += 12

        title_terms = set(_subject_terms(title_norm))
        title_overlap = query_terms & title_terms
        if title_overlap:
            score += min(8, 4 * len(title_overlap))
            signals += 1
            distinctive += min(8, 4 * len(title_overlap))

        # Multi-word semantic phrases carry more destination information than
        # isolated generic words. This prevents a Level-I specialist such as
        # Leadership Challenge Navigator from winning merely because a broad
        # territory query happens to contain "systems" and "pattern".
        query_tokens = tuple(_subject_terms(raw_query))
        query_bigrams = {
            " ".join(query_tokens[index:index + 2])
            for index in range(max(0, len(query_tokens) - 1))
        }
        for phrase_source, weight in (
            (hints, 5),
            ([purpose], 4),
        ):
            for phrase in phrase_source:
                phrase_norm = _normalize_query(phrase)
                phrase_tokens = tuple(_subject_terms(phrase_norm))
                phrase_bigrams = {
                    " ".join(phrase_tokens[index:index + 2])
                    for index in range(max(0, len(phrase_tokens) - 1))
                }
                phrase_overlap = query_bigrams & phrase_bigrams
                if phrase_overlap:
                    hits = min(3, len(phrase_overlap))
                    score += weight * hits
                    signals += 1
                    distinctive += weight * hits

        for hint in hints:
            hint_norm = _normalize_query(hint)
            if hint_norm and hint_norm in raw_query:
                score += 8
                signals += 1
                distinctive += 8
                continue
            hint_terms = set(_subject_terms(hint_norm))
            overlap = query_terms & hint_terms
            if overlap:
                score += min(6, 2 * len(overlap))
                signals += 1

        purpose_terms = set(_subject_terms(_normalize_query(purpose)))
        purpose_overlap = query_terms & purpose_terms
        if len(purpose_overlap) >= 2:
            score += min(6, 2 * len(purpose_overlap))
            signals += 1
        elif len(purpose_overlap) == 1:
            score += 2

        if score >= 8 and signals >= 2:
            candidates.append((score, signals, level, distinctive, node))

    if not candidates:
        return None

    candidates.sort(key=lambda item: (item[0], item[1], item[3], -item[2]), reverse=True)

    # Level I is not an automatic override. A concrete specialist must
    # demonstrate destination-strength evidence; generic vocabulary must not
    # suppress a materially better Level-II territory.
    level_one = [item for item in candidates if item[2] == 1]
    level_two = [item for item in candidates if item[2] == 2]

    if level_one:
        best_one = level_one[0]
        best_two_for_comparison = level_two[0] if level_two else None
        level_one_is_specific = best_one[3] >= 8
        level_one_is_clear_winner = (
            best_two_for_comparison is None
            or best_one[0] >= best_two_for_comparison[0] + 4
        )
        if best_one[0] >= 8 and level_one_is_specific and level_one_is_clear_winner:
            if len(level_one) > 1 and best_one[0] < level_one[1][0] + 3:
                return None
            node = best_one[4]
            print(
                "The Guide registry Level I activation: "
                f"route_before={route_id}, node={node.get('node_id')}, "
                f"score={best_one[0]}, signals={best_one[1]}"
            )
            return node

    # Level II is intentionally conservative. It is a territory destination
    # for broad exploration, not a substitute for a specific native experience.
    if not broad_request:
        # An exact territory title/hint can still activate directly when the
        # visitor clearly names the territory itself.
        explicit_level_two = [
            item for item in level_two
            if _normalize_query(str(item[3].get("title") or "")) in raw_query
        ]
        if explicit_level_two:
            explicit_level_two.sort(key=lambda item: (item[0], item[1]), reverse=True)
            return explicit_level_two[0][3]
        return None

    if not level_two:
        return None

    best_two = level_two[0]
    if len(level_two) > 1 and best_two[0] < level_two[1][0] + 3:
        return None

    node = best_two[4]
    print(
        "The Guide registry Level II activation: "
        f"route_before={route_id}, node={node.get('node_id')}, "
        f"score={best_two[0]}, signals={best_two[1]}"
    )
    return node

def _guide_capability_route(query, history=None):
    """Interpret the opening inquiry through the provider-neutral intelligence bank."""
    fallback = _guide_route_fallback(query, history)
    history_text = _guide_route_history_text(history)
    user_content = (
        "Visitor question:\n"
        + str(query).strip()
        + ("\n\nRecent conversation context:\n" + history_text if history_text else "")
        + "\n\nApproved Guide Nodes currently available (JSON):\n"
        + _guide_node_prompt_context()
    )
    messages = [
        {"role": "system", "content": _GUIDE_ROUTE_PROMPT},
        {"role": "user", "content": user_content[:9000]},
    ]

    def _parse(raw):
        parsed = json.loads(str(raw or "").strip())
        if not isinstance(parsed, dict):
            raise ValueError("route response was not an object")
        return parsed

    bank_result = route_with_model_bank(
        use_core=use_core,
        messages=messages,
        max_tokens=320,
        parse=_parse,
    )
    if not bank_result:
        print("USE provider bank: no viable intelligence candidate; using deterministic fallback")
        return fallback

    parsed = bank_result["parsed"]
    provider = str(bank_result["provider"]).strip().casefold()
    model_id = str(bank_result["model"]).strip()
    preference_order = list(bank_result.get("preference_order") or [])

    route = str(parsed.get("route") or "guide").strip().casefold()
    mode = str(parsed.get("mode") or "direct").strip().casefold()
    confidence = float(parsed.get("confidence", 0.0) or 0.0)
    reason = str(parsed.get("reason") or "").strip()
    alternatives = parsed.get("alternatives") or []
    interpretation = {
        "human_reality": str(parsed.get("human_reality") or "").strip(),
        "presenting_situation": str(parsed.get("presenting_situation") or "").strip(),
        "visitor_proposition": str(parsed.get("visitor_proposition") or "").strip(),
        "underlying_question": str(parsed.get("underlying_question") or "").strip(),
        "uncertainty": str(parsed.get("uncertainty") or "").strip(),
        "desired_movement": str(parsed.get("desired_movement") or "").strip(),
        "processing_need": str(parsed.get("processing_need") or "").strip().casefold(),
        "glossary_term": str(parsed.get("glossary_term") or "").strip(),
        "guide_node_id": str(parsed.get("guide_node_id") or "").strip(),
    }

    if route == "guide" and _relational_boundary_decision(query).get("open"):
        route = "relationship"
        mode = "delegated_journey"
        reason = (
            "Guide-side structural arbitration recognized a lived relational "
            "situation; Seeing the Relationship owns the next exploratory move."
        )

    activated_node = _guide_node_semantic_activation(query, interpretation, route)
    if activated_node is not None:
        route = "guide_node"
        mode = "direct"
        interpretation["guide_node_id"] = str(activated_node.get("node_id") or "").strip()
        confidence = max(confidence, 0.90)
        reason = (
            "The approved Guide Node is a stronger destination match than the "
            "broader macro route, based on multiple registry-defined semantic signals."
        )

    if route not in _GUIDE_ROUTE_IDS:
        print(f"USE provider bank rejected unsupported route {route!r}; using fallback")
        return fallback

    if route == "guide_node":
        selected_node = _guide_node_by_id(interpretation.get("guide_node_id"))
        if selected_node is None:
            print("USE provider bank proposed an unavailable Guide Node; continuing as ordinary Guide.")
            route = "guide"
            mode = "direct"
            reason = "proposed Guide Node was not present in the authoritative active registry"
    if mode not in {"direct", "delegated_journey", "lookup", "clarify", "safety"}:
        mode = "direct"

    if route == "relationship" and mode == "direct":
        processing_need = str(interpretation.get("processing_need") or "").casefold().strip()
        bounded_needs = {"retrieval", "definition", "lookup"}
        if processing_need not in bounded_needs:
            mode = "delegated_journey"
            reason = (
                "Round 1 identified a lived relational inquiry. Unless the visitor "
                "is explicitly seeking a bounded lookup, definition, or retrieval task, "
                "the relationship specialist owns the next exploratory move."
            )

    confidence = max(0.0, min(1.0, confidence))
    alternatives = [
        str(item).strip().casefold()
        for item in alternatives
        if str(item).strip().casefold() in _GUIDE_ROUTE_IDS
    ][:3]

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
        "source": "model_bank",
        "provider": provider,
        "model": model_id,
        "preference_order": preference_order,
        "round1_interpretation": interpretation,
    }
    print(
        "USE capability route: "
        f"source=model_bank, provider={provider}, model={model_id}, route={route}, "
        f"mode={mode}, confidence={confidence:.3f}, reason={reason[:180]!r}"
    )
    return result


def _relationship_specialist_response(query, history, route, request_id, raw_body=None):
    """Run Seeing the Relationship through the common specialist pipe."""
    context = _relationship_guide_context(history, raw_body or {})
    context["route_interpretation"] = route.get("round1_interpretation") or {}
    hub_request = build_hub_request(
        request_id=request_id,
        guide_version=APP_VERSION,
        original_question=query,
        recognized_territory="human relationships",
        processing_purpose="open relational exploration from The Guide",
        guide_context=context,
        safety_state="green",
    )
    hub_contribution = route_spoke(
        request=hub_request,
        specialist_id="relationship",
        invoke=lambda **kwargs: invoke_specialist(
            SPECIALIST_ADAPTER_REGISTRY,
            **kwargs,
        ),
    )
    contribution = {
        "status": hub_contribution.status,
        "voice_policy": hub_contribution.voice_policy,
        "human_response": str(
            (hub_contribution.payload or {}).get("human_response") or ""
        ),
        "interpretation": dict(
            (hub_contribution.payload or {}).get("interpretation")
            or hub_contribution.payload
            or {}
        ),
        "perspectives": list(
            (hub_contribution.payload or {}).get("perspectives") or []
        ),
        "movement": dict(
            (hub_contribution.payload or {}).get("movement") or {}
        ),
        "canonical_candidates": list(hub_contribution.canonical_candidates),
        "journey": dict(
            (hub_contribution.payload or {}).get("journey") or {}
        ),
    }
    response = _relationship_integrated_response(contribution)
    if not response:
        raise RuntimeError("Seeing the Relationship returned no human response.")

    journey = contribution.get("journey") or {}
    movement = contribution.get("movement") or {}
    interpretation = contribution.get("interpretation") or {}

    return {
        "response": response,
        "relational_delegation": {
            "state": "open",
            "specialist": "Seeing the Relationship",
            "specialist_id": "relationship",
            "contract_version": RELATIONSHIP_CONTRIBUTION_CONTRACT_VERSION,
            "voice_policy": RELATIONSHIP_VOICE_POLICY,
            "session_id": request_id,
            "seed_message": query,
            "conversation": context.get("conversation") or "",
            "handoff_reason": "The Guide recognized that this lived situation is best explored as a relationship before choosing a doorway into the Archive.",
            "hrn_endpoint": "https://geralddaquila.com/wp-json/living-archive/v1/relational-navigator",
            "guide_return_endpoint": "/api/relational-return",
            "return_mode": "guide_integrated",
            "movement": movement,
            "interpretation": interpretation,
            "journey": journey,
        },
    }


def _formation_specialist_response(query, history, route, request_id):
    """Run Formation through the common specialist pipe and integrate it into Guide output."""
    interpretation = route.get("round1_interpretation") or {}
    context = {
        "conversation": _history_text(history),
        "situation": str(interpretation.get("presenting_situation") or query),
        "possibility": str(interpretation.get("desired_movement") or ""),
        "desired_movement": str(interpretation.get("desired_movement") or ""),
    }
    hub_request = build_hub_request(
        request_id=request_id,
        guide_version=APP_VERSION,
        original_question=query,
        recognized_territory="stewardship formation",
        processing_purpose="bounded formation navigation",
        guide_context=context,
        safety_state="green",
    )
    hub_contribution = route_spoke(
        request=hub_request,
        specialist_id="formation",
        invoke=lambda **kwargs: invoke_specialist(
            SPECIALIST_ADAPTER_REGISTRY,
            **kwargs,
        ),
    )
    # invoke_specialist() preserves the complete domain contribution in
    # payload when the specialist owns a domain-specific contract. The common
    # pipe metadata is not the domain interpretation itself.
    domain_payload = dict(hub_contribution.payload or {})
    interpretation_data = dict(domain_payload.get("interpretation") or {})
    movement_data = dict(domain_payload.get("movement") or {})
    pathway = str(interpretation_data.get("pathway") or "").strip()
    doors = list(hub_contribution.canonical_candidates)
    response = pathway or "There is something here worth staying with before deciding what it means."
    return {
        "response": response,
        "formation_delegation": {
            "state": "open",
            "specialist": "Stewardship Formation Navigator",
            "specialist_id": "formation",
            "contract_version": FORMATION_CONTRIBUTION_CONTRACT_VERSION,
            "voice_policy": FORMATION_VOICE_POLICY,
            "doors": doors,
            "movement": movement_data,
            "interpretation": interpretation_data,
            "return_mode": "guide_integrated",
        },
    }


def _registered_available_specialist(specialist_id):
    for capability in SPECIALIST_CAPABILITY_REGISTRY:
        if (
            capability.specialist_id == specialist_id
            and capability.status == "available"
        ):
            return capability
    return None


# ---------------------------------------------------------------------
# v488.31 — BASIC INQUIRY
# ---------------------------------------------------------------------
_BASIC_INQUIRY_ENABLED = str(__import__("os").getenv("USE_BASIC_INQUIRY_ENABLED", "1")).strip().casefold() not in {"0", "false", "no", "off"}

_BASIC_INQUIRY_MACRO_PATTERNS = (
    re.compile(r"\b(?:stewardship\s+formation|formation\s+navigator|formation\s+pathway)\b", re.I),
    re.compile(r"\b(?:philippine\s+systems|philippines?\s+(?:systems?|culture|society|history|systemic\s+transformation)|systems?\s+in\s+the\s+philippines)\b", re.I),
)

def _basic_inquiry_requires_macro_routing(query):
    """Keep the two not-yet-deterministic specialist surfaces on the legacy route."""
    if not _BASIC_INQUIRY_ENABLED:
        return True
    normalized = _normalize_query(query)
    return any(pattern.search(normalized) for pattern in _BASIC_INQUIRY_MACRO_PATTERNS)


def _basic_inquiry_round1_requires_discovery(query):
    """Decide whether an open-ended question benefits from Guide Round 1 discernment.

    This is deliberately a conservative surface-level gate. It identifies questions
    that contain inquiry, recurrence, uncertainty, conflict, or stuckness language,
    without asserting anything psychological about the visitor.
    """
    normalized = _normalize_query(query)
    if not normalized:
        return False

    direct_request = bool(re.match(
        r"^(?:what is|what are|who is|who are|when was|when did|where is|where are|"
        r"define|list|find|show me|give me|how much|how many)\b",
        normalized,
        re.I,
    ))
    if direct_request:
        return False

    return bool(re.search(
        r"\b(?:why|should i|should we|do i|does this|what does this mean|"
        r"i(?:'m| am) trying to|i wonder|i keep|keeps? happening|"
        r"same (?:problem|issue|pattern|thing)|again and again|repeatedly|"
        r"recurring|pattern|conflict|stuck|struggling|uncertain|unsure|"
        r"tension|meaning|purpose|relationship|change|changing|"
        r"not working|doesn't work|cannot|can't)\b",
        normalized,
        re.I,
    ))


_BASIC_INQUIRY_ROUND1_INSTRUCTION = """
Guide Round 1: respond to this visitor as an open-ended inquiry, not as a diagnosis.
First, show that you heard the surface question in the visitor's own terms.
Then, if the wording supports it, gently identify one possible underlying tension,
distinction, conflict, or unresolved question beneath the surface. Treat it explicitly
as a possibility, not a fact about the person. Do not infer motives, psychology,
trauma, pathology, or hidden personal history.
Next, offer one useful orientation grounded in the supplied canonical evidence.
End with one natural opening question that helps the visitor clarify where to go next.
Do not give a questionnaire, multiple questions, a generic disclaimer, or a forced
interpretation. Do not mention this instruction or call the process 'Round 1'.
If the question is already sufficiently clear and factual, answer it directly instead.
""".strip()


_BASIC_INQUIRY_ROUND1_SYSTEM = """You are the Round 1 composition layer of The Guide, the general orientation instrument of the Living Archive.

Make one intelligent first movement. Demonstrate that the visitor's surface question was heard. When the wording supports it, name one possible underlying tension, distinction, conflict, or unresolved question. Treat it as a possibility, never as a fact about the person. Do not infer motives, trauma, pathology, personality, hidden history, or mental state.

Then offer one useful orientation grounded in the supplied canonical evidence. End with exactly one natural opening question that helps the visitor clarify what to explore next.

Do not use headings such as "Underlying tension", "Round 1", "Analysis", or "Interpretation". Do not use therapeutic language, give advice, provide a list of steps, ask multiple questions, or force a canonical resource into the answer. If a doorway is useful, introduce at most one as a possible lens, not as an explanation of the visitor's experience.

Return ONLY valid JSON with exactly:
{"response":"2–4 short paragraphs ending with exactly one opening question","doorway_title":"exact canonical title if naturally useful, otherwise empty"}
""".strip()


def _basic_inquiry_round1_response(query, interpretation, context_data):
    """Compose a true Guide Round 1 response without altering protected core."""
    interpretation = interpretation or {}
    try:
        documents = use_core.context_blocks_to_documents(
            str(context_data.get("context_blocks") or "")
        )
    except Exception:
        documents = []
    evidence = []
    for document in documents[:3]:
        title = str(document.get("title") or "").strip()
        content = str(document.get("content") or "").strip()
        if title:
            evidence.append({"title": title, "content": content[:2200]})

    internal = {
        "human_reality": str(interpretation.get("human_reality") or "").strip(),
        "presenting_situation": str(interpretation.get("presenting_situation") or "").strip(),
        "visitor_proposition": str(interpretation.get("visitor_proposition") or "").strip(),
        "underlying_question": str(interpretation.get("underlying_question") or "").strip(),
        "uncertainty": str(interpretation.get("uncertainty") or "").strip(),
        "desired_movement": str(interpretation.get("desired_movement") or "").strip(),
    }
    user_content = (
        "Surface question:\n" + str(query).strip()
        + "\n\nTentative internal interpretation:\n"
        + json.dumps(internal, ensure_ascii=False)
        + "\n\nCanonical evidence:\n"
        + json.dumps(evidence, ensure_ascii=False)
    )

    def _parse(raw):
        parsed = json.loads(str(raw or "").strip())
        if not isinstance(parsed, dict):
            raise ValueError("Round 1 response was not an object.")
        response = str(parsed.get("response") or "").strip()
        title = str(parsed.get("doorway_title") or "").strip()
        if not response:
            raise ValueError("Round 1 response was empty.")
        if response.count("?") != 1:
            raise ValueError("Round 1 response must contain exactly one opening question.")
        return {"response": response, "doorway_title": title}

    bank_result = route_with_model_bank(
        use_core=use_core,
        messages=[
            {"role": "system", "content": _BASIC_INQUIRY_ROUND1_SYSTEM},
            {"role": "user", "content": user_content[:12000]},
        ],
        max_tokens=500,
        parse=_parse,
    )
    if not bank_result:
        return None

    parsed = bank_result["parsed"]
    canonical_titles = {str(item.get("title") or "").strip() for item in evidence if str(item.get("title") or "").strip()}
    selected = str(parsed.get("doorway_title") or "").strip()
    if selected and selected not in canonical_titles:
        selected = ""
    return {
        "response": str(parsed["response"]).strip(),
        "doorway_title": selected,
        "provider": str(bank_result.get("provider") or ""),
        "model": str(bank_result.get("model") or ""),
    }


def _basic_inquiry_round1_deterministic_response(query, interpretation, context_data):
    """Safe fallback that preserves the Round 1 movement without provider prose."""
    interpretation = interpretation or {}
    underlying = str(interpretation.get("underlying_question") or "").strip()
    uncertainty = str(interpretation.get("uncertainty") or "").strip()
    movement = str(interpretation.get("desired_movement") or "").strip()

    if underlying and uncertainty:
        opening = f"The question seems to sit between {underlying.rstrip('.')} and not yet knowing {uncertainty.rstrip('.')}."
    elif underlying:
        opening = f"The question may be pointing to something slightly deeper than its surface wording: {underlying.rstrip('.')}."
    else:
        opening = "There may be a useful distinction beneath the question that is easier to see once the surface question is separated from the explanation we might give it."

    orientation = (
        f"A useful next movement may be {movement.rstrip('.')}."
        if movement
        else "A useful next movement may be to stay with the part of the question that is still genuinely open, rather than deciding too quickly what explains it."
    )

    try:
        documents = use_core.context_blocks_to_documents(str(context_data.get("context_blocks") or ""))
    except Exception:
        documents = []
    title = str(documents[0].get("title") or "").strip() if documents else ""
    url = str(documents[0].get("url") or documents[0].get("canonical_url") or "").strip() if documents else ""
    doorway = (
        f"One related Archive lens is [{title}]({url}). It is a possible place to look, not an explanation of your experience."
        if title and url else ""
    )
    final_question = "What part of the question feels most important to understand first?"
    return {
        "response": "\n\n".join(part for part in (opening, orientation, doorway, final_question) if part),
        "doorway_title": title,
        "provider": "deterministic_round1",
        "model": "",
    }


def _basic_inquiry_response(query, history=None, raw_body=None):
    """Answer an ordinary Guide question through the protected USE core."""
    started = time.perf_counter()
    query = str(query or "").strip()
    context_data = use_core.fetch_canonical_context(query)
    if not isinstance(context_data, dict):
        raise RuntimeError("Basic Inquiry retrieval returned an invalid context object.")

    if context_data.get("frame_neutral_evidence_unavailable"):
        llm_output = use_core._frame_neutral_evidence_unavailable_response(query)
    elif context_data.get("question_structure_evidence_unavailable"):
        llm_output = use_core._evidence_sufficiency_unavailable_response(query, context_data.get("canonical_link_context", ""))
    elif context_data.get("evidence_sufficiency_unavailable"):
        llm_output = use_core._evidence_sufficiency_unavailable_response(query, context_data.get("canonical_link_context", ""))
    else:
        round1_result = None
        round1_gate = _basic_inquiry_round1_requires_discovery(query)
        print(
            "The Guide Round 1 gate: "
            f"activated={round1_gate}, query={_normalize_query(query)[:120]}"
        )
        if round1_gate:
            try:
                # Basic Inquiry owns this operation once native boundaries have
                # been cleared. It must not call the capability router as a second,
                # hidden specialist-classification layer. Round 1 composition receives
                # the visitor's original question and canonical evidence directly.
                # Any specialist handoff decision has already been made at the request
                # boundary above; ordinary inquiry must remain ordinary inquiry.
                interpretation = {}
                round1_result = _basic_inquiry_round1_response(query, interpretation, context_data)
                print("The Guide Basic Inquiry Round 1: discernment_source=direct_composition, capability_router=not_called")
                if not round1_result:
                    round1_result = _basic_inquiry_round1_deterministic_response(query, interpretation or {}, context_data)
            except Exception as exc:
                print(f"The Guide Round 1 discernment failed safely; using deterministic recovery: {exc}")
                try:
                    round1_result = _basic_inquiry_round1_deterministic_response(query, {}, context_data)
                except Exception:
                    round1_result = None

        if round1_result:
            llm_output = round1_result.get("response", "")
            print(
                "The Guide Round 1: "
                f"provider={round1_result.get('provider') or 'unknown'}, "
                f"model={round1_result.get('model') or 'none'}, "
                f"doorway={round1_result.get('doorway_title') or 'none'}"
            )
        else:
            llm_output = use_core.generate_llm_response(
                query,
                context_data.get("context_blocks", ""),
                context_data.get("intent", "TOPICAL_INQUIRY"),
                orientational_frame=context_data.get("orientational_frame", {"primary": "general", "scores": {}}),
                canonical_link_context=context_data.get("canonical_link_context", context_data.get("context_blocks", "")),
                protected_documents=context_data.get("generation_authority_protected_docs", context_data.get("question_authority_protected_docs")),
            )

    response = str(llm_output or "").strip()
    if not response:
        raise RuntimeError("Basic Inquiry generation returned an empty visitor response.")

    request_id = "basic-" + hashlib.sha1((query + "|" + _history_text(history)).encode("utf-8")).hexdigest()[:16]
    payload = {
        "ok": True,
        "version": APP_VERSION,
        "fingerprint": DEPLOYMENT_FINGERPRINT,
        "source_sha256": RUNTIME_SOURCE_SHA256,
        "request_id": request_id,
        "query": query,
        "intent": context_data.get("intent", "TOPICAL_INQUIRY"),
        "response": response,
        "processing": "basic_inquiry",
        "route_source": "guide_basic_inquiry",
        "visitor_boundary_version": APP_VERSION,
    }
    print("The Guide Basic Inquiry: " + f"request_id={request_id}, intent={payload['intent']}, response_chars={len(response)}, elapsed={time.perf_counter() - started:.3f}s, query={_normalize_query(query)[:120]}")
    return payload


def _v48831_basic_inquiry_seam_self_audit():
    """Static contract audit for the Basic Inquiry seam."""
    if not _BASIC_INQUIRY_ENABLED:
        raise RuntimeError("Basic Inquiry is disabled by USE_BASIC_INQUIRY_ENABLED.")
    if not callable(getattr(use_core, "fetch_canonical_context", None)):
        raise RuntimeError("Basic Inquiry retrieval boundary is missing.")
    if not callable(getattr(use_core, "generate_llm_response", None)):
        raise RuntimeError("Basic Inquiry generation boundary is missing.")
    import inspect as _inspect
    fetch_signature = str(_inspect.signature(use_core.fetch_canonical_context))
    generate_signature = str(_inspect.signature(use_core.generate_llm_response))
    fetch_parameters = list(_inspect.signature(use_core.fetch_canonical_context).parameters)
    generate_parameters = list(_inspect.signature(use_core.generate_llm_response).parameters)
    if len(fetch_parameters) != 1:
        raise RuntimeError(f"Basic Inquiry retrieval contract drift: {fetch_signature}")
    # The protected generation callable may be decorator-wrapped at runtime;
    # its inspect.signature can therefore legitimately expose (*args, **kwargs)
    # even though its protected source contract remains stable. The actual seam
    # already calls it positionally for the first three arguments and by name
    # for the optional arguments. Audit callability here, not wrapper metadata.
    if not callable(getattr(use_core, "generate_llm_response", None)):
        raise RuntimeError("Basic Inquiry generation boundary is not callable.")
    probe = "I am trying to understand why I keep seeing the same problem in my life."
    if _basic_inquiry_requires_macro_routing(probe):
        raise RuntimeError("Basic Inquiry probe was incorrectly deferred to macro routing.")
    if not _basic_inquiry_round1_requires_discovery(probe):
        raise RuntimeError("Basic Inquiry Round 1 discovery gate failed for the canonical probe.")
    source_text = _MAIN_PATH.read_text(encoding="utf-8")
    basic_start = source_text.find("def _basic_inquiry_response(")
    basic_end = source_text.find("def _v48831_basic_inquiry_seam_self_audit(", basic_start)
    basic_block = source_text[basic_start:basic_end] if basic_start >= 0 and basic_end > basic_start else ""
    if "_guide_capability_route(" in basic_block:
        raise RuntimeError("Basic Inquiry structural isolation failure: capability router remains inside ordinary inquiry.")
    if not _basic_inquiry_requires_macro_routing("I want stewardship formation."):
        raise RuntimeError("Formation macro-routing boundary was lost.")
    if not _basic_inquiry_requires_macro_routing("I want to understand Philippine systems."):
        raise RuntimeError("Philippine Systems macro-routing boundary was lost.")
    source = _inspect.getsource(_use_request_boundary)
    basic_position = source.find("if not _basic_inquiry_requires_macro_routing(query):")
    macro_position = source.find("route = _guide_capability_route(query, history)")
    if basic_position < 0 or macro_position < 0 or not basic_position < macro_position:
        raise RuntimeError("Basic Inquiry seam ordering regression.")
    print("USE v488.32 BASIC INQUIRY SEAM AUDIT: PASS; ordinary=direct; native_boundaries=precedence; formation_and_philippine_systems=legacy_macro")

# Canonical request boundary: one route decision, one specialist handoff seam,
# one explicit fallback into the protected FastAPI/core application.
async def _use_request_body(receive):
    chunks = []
    while True:
        message = await receive()
        if message.get("type") == "http.disconnect":
            break
        if message.get("type") != "http.request":
            continue
        body = message.get("body") or b""
        if body:
            chunks.append(body)
        if not message.get("more_body", False):
            break
    return b"".join(chunks)


def _use_replay_receive(body):
    sent = False
    async def _receive():
        nonlocal sent
        if not sent:
            sent = True
            return {"type": "http.request", "body": body, "more_body": False}
        return {"type": "http.request", "body": b"", "more_body": False}
    return _receive


async def _use_send_json(send, payload, status_code=200):
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    await send({"type": "http.response.start", "status": status_code,
                "headers": [(b"content-type", b"application/json; charset=utf-8"),
                            (b"content-length", str(len(body)).encode("ascii")),
                            (b"access-control-allow-origin", b"*")]})
    await send({"type": "http.response.body", "body": body})


# v488.32 startup audit: verify the Basic Inquiry seam against the protected core.

_FASTAPI_APP = app



def _guide_node_specific_match(query):
    """Resolve a clearly named registered destination before generic Navigator routing.

    This is structural arbitration, not a specialist keyword gate: only the
    WordPress registry's declared title/semantic-hint phrases can produce a
    match, and generic one-word hints are intentionally ignored.
    """
    normalized = _normalize_query(query)
    if not normalized:
        return None

    best = None
    best_score = 0

    for node in _guide_node_registry_snapshot():
        labels = [str(node.get("title") or "").strip()]
        labels.extend(
            str(hint).strip()
            for hint in (node.get("semantic_hints") or [])
            if str(hint).strip()
        )

        for label in labels:
            phrase = _normalize_query(label)
            phrase_tokens = tuple(
                token for token in re.findall(r"[a-z0-9]+", phrase)
                if len(token) >= 3
            )
            # A registered two-word-or-longer phrase is an explicit discovery
            # signal, but it must match complete tokens. Plain substring
            # matching is unsafe here: "recurring pattern" must NOT match
            # "recurring patterns". The former is a Leadership Challenge
            # Navigator hint; the latter belongs to the broader Series &
            # Analysis territory.
            normalized_tokens = tuple(re.findall(r"[a-z0-9]+", normalized))
            if len(phrase_tokens) >= 2:
                phrase_tuple = tuple(phrase_tokens)
                exact_phrase_match = any(
                    normalized_tokens[index:index + len(phrase_tuple)] == phrase_tuple
                    for index in range(
                        max(0, len(normalized_tokens) - len(phrase_tuple) + 1)
                    )
                )
                if exact_phrase_match:
                    score = 100 + len(phrase_tokens)
                    if score > best_score:
                        best_score = score
                        best = node
                    continue

            query_tokens = set(re.findall(r"[a-z0-9]+", normalized))
            meaningful = {
                token for token in phrase_tokens
                if token not in {"the", "and", "for", "with", "archive", "living"}
            }
            overlap = len(query_tokens & meaningful)
            if len(meaningful) >= 3 and overlap >= 2:
                score = 10 + overlap
                if score > best_score:
                    best_score = score
                    best = node

    # Exact registered phrases remain strongest (100+). When a visitor uses
    # natural language that expresses the same destination without repeating
    # the registry phrase verbatim, the registry's own semantic hints may
    # authorize the destination when at least two meaningful hint terms align.
    # This is still registry-driven: USE is not maintaining a second keyword
    # map, and no question-specific rule is added here.
    return best if best_score >= 10 else None


# v488.24 Guide Node semantic-overlap boundary guard.
# The registered Steward Readiness destination must be reachable from natural
# language that expresses the destination without reproducing its exact title.
_steward_readiness_probe = _guide_node_specific_match(
    "How can I assess my readiness for stewardship?"
)
if not _steward_readiness_probe or _steward_readiness_probe.get("node_id") != "steward-readiness-instruments":
    raise RuntimeError(
        "USE v488.24 invariant failed: natural Steward Readiness destination was not resolved."
    )

# v488.30 phrase-boundary invariant: a singular registered hint must not
# match a plural visitor phrase merely because the singular is a substring.
_series_analysis_boundary_probe = _guide_node_specific_match(
    "I want to explore recurring patterns in people and systems over time."
)
if _series_analysis_boundary_probe and _series_analysis_boundary_probe.get("node_id") == "leadership-challenge-navigator":
    raise RuntimeError(
        "USE v488.30 invariant failed: singular Leadership hint matched plural pattern query."
    )


def _request_header(scope, name):
    target = str(name or "").strip().lower().encode("latin-1")
    for key, value in scope.get("headers") or []:
        if bytes(key).lower() == target:
            try:
                return bytes(value).decode("latin-1").strip()
            except Exception:
                return ""
    return ""


def _first_forwarded_ip(value):
    first = str(value or "").split(",", 1)[0].strip()
    try:
        ipaddress.ip_address(first)
        return first
    except ValueError:
        return ""


def _request_location_context(scope, parsed_body):
    """Build the Guide's normalized location context without requiring a prompt.

    Precedence is explicit visitor context, browser/device context, trusted edge
    country metadata, then bounded IP geolocation. The resolver never invents
    a country and returns an empty context when no reliable signal is available.
    """
    headers = {
        "cf_connecting_ip": _request_header(scope, "cf-connecting-ip"),
        "true_client_ip": _request_header(scope, "true-client-ip"),
        "x_forwarded_for": _request_header(scope, "x-forwarded-for"),
        "cf_ipcountry": _request_header(scope, "cf-ipcountry"),
        "cf_region": _request_header(scope, "cf-region"),
        "cf_ipcity": _request_header(scope, "cf-ipcity"),
        "cf_iplatitude": _request_header(scope, "cf-iplatitude"),
        "cf_iplongitude": _request_header(scope, "cf-iplongitude"),
        "cf_timezone": _request_header(scope, "cf-timezone"),
    }
    client_ip = ""
    for candidate in (
        headers["cf_connecting_ip"],
        headers["true_client_ip"],
        _first_forwarded_ip(headers["x_forwarded_for"]),
    ):
        try:
            ipaddress.ip_address(candidate)
            client_ip = candidate
            break
        except ValueError:
            continue

    context = {}
    for key in (
        "explicit_country", "browser_country", "ip_country",
        "timezone_country", "locale_country", "region", "province",
        "locality", "address", "refused", "user_confirmation",
        "latitude", "longitude", "accuracy",
    ):
        value = parsed_body.get(key)
        if value not in ("", None):
            context[key] = value

    if parsed_body.get("country") not in ("", None) and "explicit_country" not in context:
        context["explicit_country"] = str(parsed_body.get("country")).strip()

    if headers["cf_ipcountry"] and "browser_country" not in context and "explicit_country" not in context:
        context["ip_country"] = headers["cf_ipcountry"].strip().upper()
        context["location_source"] = "cloudflare_edge"

    if headers["cf_region"] and "region" not in context:
        context["region"] = headers["cf_region"]
    if headers["cf_ipcity"] and "locality" not in context:
        context["locality"] = headers["cf_ipcity"]
    if headers["cf_iplatitude"] and "latitude" not in context:
        context["latitude"] = headers["cf_iplatitude"]
    if headers["cf_iplongitude"] and "longitude" not in context:
        context["longitude"] = headers["cf_iplongitude"]
    if headers["cf_timezone"] and "timezone" not in context:
        context["timezone"] = headers["cf_timezone"]
    if client_ip:
        context["client_ip"] = client_ip

    return context, client_ip


def _ip_geolocation(client_ip, timeout=0.65):
    if not client_ip:
        return {}
    try:
        ipaddress.ip_address(client_ip)
    except ValueError:
        return {}
    endpoint = "https://get.geojs.io/v1/ip/geo/" + quote(client_ip, safe="")
    try:
        request = UrlRequest(
            endpoint,
            headers={
                "Accept": "application/json",
                "User-Agent": "Living-Archive-The-Guide/1.0",
            },
            method="GET",
        )
        with urlopen(request, timeout=float(timeout)) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if not isinstance(payload, dict):
            return {}
        result = {}
        country_code = str(payload.get("country_code") or "").strip().upper()
        if country_code:
            result["ip_country"] = country_code
        if payload.get("region"):
            result["region"] = str(payload.get("region")).strip()
            result["province"] = str(payload.get("region")).strip()
        if payload.get("city"):
            result["locality"] = str(payload.get("city")).strip()
        for source_key, target_key in (
            ("latitude", "latitude"),
            ("longitude", "longitude"),
            ("accuracy", "accuracy"),
            ("timezone", "timezone"),
        ):
            if payload.get(source_key) not in ("", None):
                result[target_key] = payload.get(source_key)
        if result:
            result["location_source"] = "ip_geolocation"
        return result
    except Exception as exc:
        print(f"The Guide IP location fallback unavailable: {exc}")
        return {}


async def _resolve_request_location(scope, parsed_body):
    context, client_ip = _request_location_context(scope, parsed_body)
    # First-party/context supplied by the visitor or edge wins. Only use the
    # external IP resolver when no country signal exists yet.
    if any(context.get(key) for key in (
        "explicit_country", "browser_country", "ip_country",
        "timezone_country", "locale_country",
    )):
        return context
    if client_ip:
        fallback = await asyncio.to_thread(_ip_geolocation, client_ip, 0.65)
        for key, value in fallback.items():
            if value not in ("", None) and not context.get(key):
                context[key] = value
    return context


async def _use_request_boundary(scope, receive, send):
    if scope.get("type") != "http":
        await _FASTAPI_APP(scope, receive, send)
        return
    method = str(scope.get("method") or "").upper()
    path = str(scope.get("path") or "")
    if method != "POST" or path not in {"/api/query", "/"}:
        await _FASTAPI_APP(scope, receive, send)
        return

    raw_body = await _use_request_body(receive)
    try:
        parsed_body = json.loads(raw_body.decode("utf-8")) if raw_body else {}
    except Exception:
        parsed_body = {}
    if not isinstance(parsed_body, dict):
        parsed_body = {}

    query = str(parsed_body.get("query") or parsed_body.get("user_query") or
                parsed_body.get("question") or parsed_body.get("text") or
                parsed_body.get("input") or "").strip()
    history = parsed_body.get("history") or parsed_body.get("conversation_history")
    if not query:
        await _FASTAPI_APP(scope, _use_replay_receive(raw_body), send)
        return

    # Highest-priority sitewide Safety / Crisis boundary. The Guide owns
    # the interruption boundary, but the existing HRN Safety Fractal +
    # Emergency Intelligence system remains the semantic/resource authority.
    # This is deliberately a sibling linkage, not a replacement safety routine.
    history_text = _history_text(history)
    safety_question_hint = str(parsed_body.get("safety_question") or "").strip()
    safety_state_hint = str(parsed_body.get("safety_state") or "").strip().casefold()
    safety_active_hint = bool(parsed_body.get("safety_active"))
    safety_state = classify_safety(query, history=history_text)

    # Conversation continuity contract: a specialist safety turn may carry an
    # explicit active-state/question alongside its structured history. This is
    # a server-side continuity aid, not a client-authorized escalation; it can
    # only keep an already-active safety conversation inside the safety lane.
    if (
        not safety_state
        and safety_active_hint
        and safety_question_hint
    ):
        safety_state = "acute_followthrough"
    elif (
        not safety_state
        and safety_active_hint
        and safety_state_hint in {"acute", "plan", "immediacy", "current", "acute_followthrough"}
    ):
        safety_state = safety_state_hint

    # Boundary recovery: the protected core remains the authoritative
    # deterministic fallback if the auxiliary safety classifier misses a
    # risk signal. This executes before normal Guide routing or retrieval.
    if not safety_state:
        try:
            risk_profile = _base._inquiry_profile(query)
            if isinstance(risk_profile, dict) and bool(risk_profile.get("risk")):
                safety_state = "current"
                print("The Guide safety boundary recovered from protected-core risk profile.")
        except Exception as exc:
            print(f"The Guide protected-core safety recovery was unavailable: {exc}")

    if safety_state:
        request_id = "safety-" + hashlib.sha1(
            (query + "|" + _history_text(history)).encode("utf-8")
        ).hexdigest()[:16]
        safety_country = str(parsed_body.get("country") or parsed_body.get("visitor_country") or "").strip()
        safety_location = await _resolve_request_location(scope, parsed_body)
        if safety_country and "explicit_country" not in safety_location:
            safety_location["explicit_country"] = safety_country
        if safety_location.get("ip_country") and not safety_country:
            safety_country = str(safety_location.get("ip_country") or "").strip()
        try:
            safety_contribution = await asyncio.wait_for(
                asyncio.to_thread(
                    invoke_specialist,
                    SPECIALIST_ADAPTER_REGISTRY,
                    request_id=request_id,
                    guide_version=APP_VERSION,
                    specialist_id="safety",
                    original_question=query,
                    recognized_territory="immediate safety",
                    processing_purpose="sitewide safety interruption and emergency-resource movement",
                    guide_context={
                        "country": safety_country,
                        "location": safety_location,
                        "conversation": history_text,
                        "visitor_history": history_text,
                        "safety_question": safety_question_hint,
                        "unit_turns": len(history) if isinstance(history, list) else 0,
                    },
                    safety_state=safety_state,
                ),
                timeout=5.5,
            )
            safety_payload = dict(safety_contribution.get("payload") or {})
            safety_response = str(safety_payload.get("human_response") or "").strip()
            if not safety_response:
                raise RuntimeError("Safety utility returned no visitor response.")

            # Fail-closed continuity contract: an active safety interruption
            # may never silently release because HRN returned a response without
            # its next question. HRN remains the semantic authority. The shared
            # safety-intelligence layer supplies a state-aware native next
            # movement only when HRN omitted one; this boundary repeats that
            # contract defensively for any malformed specialist payload.
            safety_release_ready = bool(safety_payload.get("safety_release_ready"))
            safety_question = str(safety_payload.get("safety_question") or "").strip()
            if not safety_release_ready and not safety_question:
                safety_question = repair_safety_question(
                    safety_state=safety_state,
                    previous_question=safety_question_hint,
                    query=query,
                    history=history_text,
                )
                safety_payload["safety_question"] = safety_question
                safety_payload["safety_continuity_guard"] = (
                    "native_next_movement_repaired"
                )
            print(
                "The Guide sitewide Safety utility: "
                f"request_id={request_id}, state={safety_state}, "
                "hrn_safety_lane=called, ordinary_hrn=not_called, llm=not_called, retrieval=not_called"
            )
            return await _use_send_json(send, {
                "ok": True,
                "version": APP_VERSION,
                "fingerprint": DEPLOYMENT_FINGERPRINT,
                "source_sha256": RUNTIME_SOURCE_SHA256,
                "request_id": request_id,
                "query": query,
                "intent": "SAFETY_INTERRUPT",
                "response": safety_response,
                "processing": "sitewide_safety_utility",
                "route_source": "guide_sitewide_safety_boundary",
                "handoff": "safety",
                "handoff_mode": "interrupt",
                "handoff_pending": False,
                # Preserve the existing flat HRN safety response contract so
                # the established safety UI can render without redesign.
                "safety_message": safety_payload.get("safety_message") or safety_response,
                "safety_question": safety_payload.get("safety_question") or "",
                "safety_note": safety_payload.get("safety_note") or "",
                "safety_resources": safety_payload.get("safety_resources") or [],
                "safety_location_required": bool(safety_payload.get("safety_location_required")),
                "country": safety_payload.get("country") or safety_country,
                "safety_release_ready": bool(safety_payload.get("safety_release_ready")),
                "safety_continuity_guard": safety_payload.get("safety_continuity_guard") or "",
                "safety": {
                    "state": safety_payload.get("safety_state") or safety_state,
                    "interrupt": True,
                    "display_mode": safety_payload.get("display_mode") or "hrn_safety",
                    "resources": safety_payload.get("safety_resources") or safety_payload.get("resources") or [],
                    "next_movement": safety_payload.get("next_movement") or safety_payload.get("safety_question") or "",
                    "safety_message": safety_payload.get("safety_message") or safety_response,
                    "safety_question": safety_payload.get("safety_question") or "",
                    "safety_note": safety_payload.get("safety_note") or "",
                    "safety_location_required": bool(safety_payload.get("safety_location_required")),
                    "country": safety_payload.get("country") or safety_country,
                    "safety_release_ready": bool(safety_payload.get("safety_release_ready")),
                    "safety_continuity_guard": safety_payload.get("safety_continuity_guard") or "",
                    "bypasses_ordinary_hrn": True,
                    "bypasses_llm": True,
                    "bypasses_retrieval": True,
                    "safety_intelligence_contract_version": SAFETY_INTELLIGENCE_CONTRACT_VERSION,
                },
                "visitor_boundary_version": APP_VERSION,
            })
        except Exception as exc:
            print(f"The Guide sitewide Safety utility failed closed: {exc}")
            return await _use_send_json(send, {
                "ok": True,
                "version": APP_VERSION,
                "query": query,
                "intent": "SAFETY_INTERRUPT",
                "response": (
                    "If you may be in immediate danger or may act on thoughts "
                    "of self-harm, please contact your local emergency services "
                    "or go to the nearest emergency department now. If possible, "
                    "stay with another person while you get help."
                ),
                "processing": "sitewide_safety_utility_fallback",
                "route_source": "guide_sitewide_safety_boundary",
                "handoff": "safety",
                "handoff_mode": "interrupt",
                "handoff_pending": False,
                "safety_message": (
                    "If you may be in immediate danger, contact the emergency "
                    "service where you are or go to the nearest emergency "
                    "department, and stay with another person."
                ),
                "safety_question": "",
                "safety_note": "",
                "safety_resources": [],
                "safety_location_required": True,
                "country": safety_country,
                "safety_release_ready": False,
                "safety": {
                    "state": safety_state,
                    "interrupt": True,
                    "display_mode": "hrn_safety",
                    "resources": [],
                    "bypasses_ordinary_hrn": True,
                    "bypasses_llm": True,
                    "bypasses_retrieval": True,
                    "safety_intelligence_contract_version": SAFETY_INTELLIGENCE_CONTRACT_VERSION,
                },
                "visitor_boundary_version": APP_VERSION,
            })

    # Immediate FSD handoff: FSD is a native standalone diagnostic
    # surface. Do not spend a routing-model call; send the visitor directly
    # to the canonical landing page and let FSD own the complete experience.
    if _is_fsd_request(query):
        fsd_url = _fsd_handoff_url(query)
        request_id = "fsd-" + hashlib.sha1(
            (query + "|" + _history_text(history)).encode("utf-8")
        ).hexdigest()[:16]
        print(
            "The Guide immediate FSD handoff: "
            f"request_id={request_id}, url={fsd_url}"
        )
        return await _use_send_json(send, {
            "ok": True,
            "version": APP_VERSION,
            "query": query,
            "intent": "FSD_HANDOFF",
            "response": "",
            "handoff": "fsd",
            "handoff_mode": "immediate",
            "handoff_pending": True,
            "fsd_url": fsd_url,
            "return_mode": "native_fsd_landing",
            "visitor_boundary_version": APP_VERSION,
            "request_id": request_id,
        })

    # Immediate Catalogue handoff: an explicit request to explore or use
    # the Stewardship Catalogue is already a bounded specialist request.
    # Do not spend a routing-model call or let Guide retrieval answer it first.
    if re.search(
        r"\b(?:catalogue|catalog)\b",
        _normalize_query(query),
        re.I,
    ):
        catalogue_url = _catalogue_handoff_url(query)
        request_id = "catalogue-" + hashlib.sha1(
            (query + "|" + _history_text(history)).encode("utf-8")
        ).hexdigest()[:16]
        print(
            "The Guide immediate Catalogue handoff: "
            f"request_id={request_id}, url={catalogue_url}"
        )
        return await _use_send_json(send, {
            "ok": True,
            "version": APP_VERSION,
            "query": query,
            "intent": "CATALOGUE_HANDOFF",
            "response": "",
            "handoff": "catalogue",
            "handoff_mode": "immediate",
            "handoff_pending": True,
            "catalogue_query": query,
            "catalogue_url": catalogue_url,
            "return_mode": "native_catalogue_search",
            "visitor_boundary_version": APP_VERSION,
            "request_id": request_id,
        })

# Immediate Atlas handoff: an explicit Atlas / Reference Map request is
    # already a bounded specialist request. Do not spend a routing-model call
    # or let ordinary Guide retrieval answer it first. The native Atlas page
    # then invokes its existing Finder/AJAX contract with the original query.
    if _is_explicit_atlas_request(query):
        atlas_url = _atlas_handoff_url(query)
        request_id = "atlas-" + hashlib.sha1(
            (query + "|" + _history_text(history)).encode("utf-8")
        ).hexdigest()[:16]
        print(
            "The Guide immediate Atlas handoff: "
            f"request_id={request_id}, url={atlas_url}"
        )
        return await _use_send_json(send, {
            "ok": True,
            "version": APP_VERSION,
            "query": query,
            "intent": "ATLAS_HANDOFF",
            "response": "",
            "handoff": "atlas",
            "handoff_mode": "immediate",
            "handoff_pending": True,
            "atlas_query": query,
            "atlas_url": atlas_url,
            "return_mode": "native_atlas_finder",
            "visitor_boundary_version": APP_VERSION,
            "request_id": request_id,
        })

    # High-confidence Glyph Finder boundary: explicit Glyph requests belong
    # to the native Finder. Do not let provider/model routing or deterministic
    # Guide fallback convert a bounded native search into an ordinary answer.
    if _is_glyph_finder_request(query):
        glyph_url = _glyph_handoff_url(query)
        request_id = "glyph-" + hashlib.sha1(
            (query + "|" + _history_text(history)).encode("utf-8")
        ).hexdigest()[:16]
        print(
            "The Guide direct Glyph Finder handoff: "
            f"request_id={request_id}, url={glyph_url}"
        )
        return await _use_send_json(send, {
            "ok": True,
            "version": APP_VERSION,
            "query": query,
            "intent": "GLYPH_HANDOFF",
            "response": "",
            "handoff": "glyph",
            "handoff_mode": "direct",
            "handoff_pending": True,
            "glyph_query": query,
            "glyph_url": glyph_url,
            "return_mode": "native_guardian_glyph_finder",
            "visitor_boundary_version": APP_VERSION,
            "request_id": request_id,
        })


    # Immediate Glossary handoff: an explicit definition/meaning question is
    # already a bounded lookup request. Do not spend a routing-model call or
    # allow ordinary Guide retrieval to answer it first.
    glossary_term = _normalize_glossary_term(query)
    embedded_glossary_term = _extract_embedded_glossary_term(query)
    if glossary_term and (
        re.match(
            r"^(?:what does|what is|what's|what is the meaning of|meaning of|define|definition of)\b",
            _normalize_query(query),
            re.I,
        )
        or embedded_glossary_term
    ):
        glossary_url = (
            "https://geralddaquila.com/glossary/?glossary_term="
            + quote(glossary_term, safe="")
        )
        request_id = "glossary-" + hashlib.sha1(
            (query + "|" + _history_text(history)).encode("utf-8")
        ).hexdigest()[:16]
        print(
            "The Guide immediate Glossary handoff: "
            f"request_id={request_id}, term={glossary_term!r}, url={glossary_url}"
        )
        return await _use_send_json(send, {
            "ok": True,
            "version": APP_VERSION,
            "query": query,
            "intent": "GLOSSARY_HANDOFF",
            "response": "",
            "handoff": "glossary",
            "handoff_mode": "immediate",
            "handoff_pending": True,
            "glossary_term": glossary_term,
            "glossary_url": glossary_url,
            "return_mode": "native_glossary_search",
            "visitor_boundary_version": APP_VERSION,
            "request_id": request_id,
        })

    # Immediate lived-relational handoff: do not spend a Guide routing-model call
    # or invoke the HRN specialist before the HRN surface is opened. The visitor's
    # question is already sufficient to establish this bounded structural route.
    # The Guide remains authoritative for the handoff; HRN owns the actual
    # interpretation/composition journey after the browser arrives there.
    # v488.72 authoritative relational boundary. This executes before Basic Inquiry
    # and before provider/model routing, so a natural lived relationship inquiry
    # cannot be consumed by the generic Guide path simply because the model later
    # labels it TOPICAL_INQUIRY.
    relational_boundary = _relational_boundary_decision(query)
    if relational_boundary.get("open"):
        request_id = "relationship-" + hashlib.sha1(
            (query + "|" + _history_text(history)).encode("utf-8")
        ).hexdigest()[:16]
        print(
            "The Guide immediate HRN handoff: "
            f"request_id={request_id}, query={_normalize_query(query)[:120]}"
        )
        return await _use_send_json(send, {
            "ok": True,
            "version": APP_VERSION,
            "query": query,
            "intent": "RELATIONAL_HANDOFF",
            "response": "",
            "handoff": "relationship",
            "handoff_mode": "immediate",
            "handoff_pending": True,
            "relational_delegation": {
                "state": "pending",
                "specialist": "Seeing the Relationship",
                "specialist_id": "relationship",
                "contract_version": RELATIONSHIP_CONTRIBUTION_CONTRACT_VERSION,
                "voice_policy": RELATIONSHIP_VOICE_POLICY,
                "session_id": request_id,
                "seed_message": query,
                "conversation": _history_text(history),
                "handoff_reason": "The Guide recognized a lived relational inquiry and is opening Seeing the Relationship directly.",
                "hrn_endpoint": "https://geralddaquila.com/wp-json/living-archive/v1/relational-navigator",
                "return_mode": "guide_integrated",
            },
            "visitor_boundary_version": APP_VERSION,
            "request_id": request_id,
            "relational_boundary_contract": RELATIONAL_BOUNDARY_CONTRACT_VERSION,
            "relational_boundary_reason": relational_boundary.get("reason"),
        })

    # High-confidence Case Navigator boundary: explicit Case Study requests
    # belong to the native structural case search. Do not let provider routing
    # or deterministic Guide fallback turn a bounded case request into an
    # ordinary answer.
    if _is_case_navigator_request(query):
        case_url = _case_handoff_url(query)
        request_id = "case-" + hashlib.sha1(
            (query + "|" + _history_text(history)).encode("utf-8")
        ).hexdigest()[:16]
        print(
            "The Guide direct Case Navigator handoff: "
            f"request_id={request_id}, url={case_url}"
        )
        return await _use_send_json(send, {
            "ok": True,
            "version": APP_VERSION,
            "query": query,
            "intent": "CASE_HANDOFF",
            "response": "",
            "handoff": "case",
            "handoff_mode": "direct",
            "handoff_pending": True,
            "case_query": query,
            "case_url": case_url,
            "return_mode": "native_case_navigator",
            "visitor_boundary_version": APP_VERSION,
            "request_id": request_id,
        })
    # Registered destination precedence is evaluated BEFORE generic
    # orientation and before provider/model routing. A visitor who names a
    # specific Guide Node has already supplied enough destination intent;
    # sending that question to Start Here would discard useful specificity.
    # This is registry-driven, not a question-specific keyword redirect.
    specific_node = _guide_node_specific_match(query)
    if specific_node is not None:
        request_id = "guide-node-" + hashlib.sha1(
            (query + "|" + str(specific_node.get("node_id"))).encode("utf-8")
        ).hexdigest()[:16]
        payload = node_handoff_payload(
            specific_node,
            query=query,
            request_id=request_id,
            visitor_boundary_version=APP_VERSION,
        )
        payload.update({
            "version": APP_VERSION,
            "route_source": "registry_specific_destination",
            "route_confidence": 1.0,
        })
        print(
            "The Guide registry destination precedence: "
            f"request_id={request_id}, node={specific_node.get('node_id')}, "
            f"url={specific_node.get('canonical_url')}"
        )
        return await _use_send_json(send, payload)

    # High-confidence orientation boundary: a visitor asking how to enter,
    # Generic orientation normally belongs to the native Navigator. However,
    # when the visitor names a specific registered destination, that specific
    # doorway takes precedence over the generic Start Here experience. This
    # prevents questions such as "Where can I explore Philippine renewal?"
    # from losing their destination merely because they are phrased as
    # navigation questions.
    if _is_navigator_orientation_request(query):
        specific_node = _guide_node_specific_match(query)
        if specific_node is not None:
            request_id = "guide-node-" + hashlib.sha1(
                (query + "|" + str(specific_node.get("node_id"))).encode("utf-8")
            ).hexdigest()[:16]
            payload = node_handoff_payload(
                specific_node,
                query=query,
                request_id=request_id,
                visitor_boundary_version=APP_VERSION,
            )
            payload.update({
                "version": APP_VERSION,
                "route_source": "registry_specific_destination",
                "route_confidence": 1.0,
            })
            print(
                "The Guide specific destination precedence: "
                f"request_id={request_id}, node={specific_node.get('node_id')}, "
                f"url={specific_node.get('canonical_url')}"
            )
            return await _use_send_json(send, payload)

        navigator_url = _navigator_handoff_url(query)
        request_id = "navigator-" + hashlib.sha1(
            (query + "|" + _history_text(history)).encode("utf-8")
        ).hexdigest()[:16]
        print(
            "The Guide systemic Navigator orientation handoff: "
            f"request_id={request_id}, url={navigator_url}, "
            f"query={_normalize_query(query)[:120]}"
        )
        return await _use_send_json(send, {
            "ok": True,
            "version": APP_VERSION,
            "query": query,
            "intent": "NAVIGATOR_HANDOFF",
            "response": "",
            "handoff": "navigator",
            "handoff_mode": "entrance",
            "handoff_pending": True,
            "navigator_url": navigator_url,
            "return_mode": "native_archive_navigator_welcome",
            "visitor_boundary_version": APP_VERSION,
            "request_id": request_id,
        })

    # v488.45: ordinary questions get exactly one routing decision.
    # Native boundaries above remain authoritative. Once those boundaries have
    # been cleared, Basic Inquiry owns the ordinary path. A Basic Inquiry
    # failure must NOT re-enter the legacy capability router: doing so creates
    # a second classification decision and can turn a transient generation
    # failure into a false specialist handoff.
    if not _basic_inquiry_requires_macro_routing(query):
        try:
            basic_result = _basic_inquiry_response(
                query=query,
                history=history,
                raw_body=parsed_body,
            )
            return await _use_send_json(send, basic_result)
        except Exception as exc:
            print(
                "The Guide Basic Inquiry seam failed; "
                f"ordinary route remains ordinary and will not be reclassified: {exc}"
            )
            try:
                context_data = use_core.fetch_canonical_context(query)
                recovery = _basic_inquiry_round1_deterministic_response(
                    query,
                    {},
                    context_data if isinstance(context_data, dict) else {},
                )
                recovery_text = str(recovery.get("response") or "").strip()
                if recovery_text:
                    request_id = "basic-recovery-" + hashlib.sha1(
                        (query + "|" + _history_text(history)).encode("utf-8")
                    ).hexdigest()[:16]
                    return await _use_send_json(send, {
                        "ok": True,
                        "version": APP_VERSION,
                        "fingerprint": DEPLOYMENT_FINGERPRINT,
                        "source_sha256": RUNTIME_SOURCE_SHA256,
                        "request_id": request_id,
                        "query": query,
                        "intent": (
                            context_data.get("intent", "TOPICAL_INQUIRY")
                            if isinstance(context_data, dict)
                            else "TOPICAL_INQUIRY"
                        ),
                        "response": recovery_text,
                        "processing": "basic_inquiry_recovery",
                        "route_source": "guide_basic_inquiry_recovery",
                        "recovery": "deterministic_round1",
                        "visitor_boundary_version": APP_VERSION,
                    })
            except Exception as recovery_exc:
                print(
                    "The Guide Basic Inquiry deterministic recovery also failed: "
                    f"{recovery_exc}"
                )
            return await _use_send_json(send, {
                "ok": False,
                "version": APP_VERSION,
                "query": query,
                "intent": "TOPICAL_INQUIRY",
                "response": "The Guide could not complete this question right now.",
                "error_type": "basic_inquiry_failure",
                "route_source": "guide_basic_inquiry",
                "visitor_boundary_version": APP_VERSION,
            }, 503)

    route = _guide_capability_route(query, history)
    route_id = str(route.get("route") or "guide").strip().casefold()
    mode = str(route.get("mode") or "direct").strip().casefold()
    confidence = float(route.get("confidence", 0.0) or 0.0)
    capability = _registered_available_specialist(route_id)
    should_delegate = capability is not None and route_id in {"relationship", "formation"}

    print(f"The Guide canonical request boundary: route={route_id}, mode={mode}, confidence={confidence:.3f}, delegate={should_delegate}, query={_normalize_query(query)[:120]}")

    # Guide Nodes are visitor-facing native Archive destinations. USE only
    # selects an approved WordPress node and carries the original question
    # across the native boundary. The node itself owns its experience.
    if route_id == "guide_node":
        node = _guide_node_by_id((route.get("round1_interpretation") or {}).get("guide_node_id"))
        if node is not None:
            request_id = "guide-node-" + hashlib.sha1(
                (query + "|" + str(node.get("node_id"))).encode("utf-8")
            ).hexdigest()[:16]
            payload = node_handoff_payload(
                node,
                query=query,
                request_id=request_id,
                visitor_boundary_version=APP_VERSION,
            )
            payload.update({
                "version": APP_VERSION,
                "route_source": route.get("source"),
                "route_confidence": confidence,
            })
            print(
                "The Guide direct Guide Node handoff: "
                f"request_id={request_id}, node={node.get('node_id')}, url={node.get('canonical_url')}"
            )
            return await _use_send_json(send, payload)

    # FSD is a visitor-facing native diagnostic surface. Once the
    # Guide route identifies it, hand off directly to its landing page.
    # Philippine Systems is a visitor-facing native knowledge surface.
    # The LLM has already made the macro routing decision above; hand the
    # visitor directly to its native landing page.
    if route_id == "systems_ph":
        philippine_systems_url = _philippine_systems_handoff_url(query)
        request_id = "systems-ph-" + hashlib.sha1(
            (query + "|" + _history_text(history)).encode("utf-8")
        ).hexdigest()[:16]
        print(
            "The Guide direct Philippine Systems handoff: "
            f"request_id={request_id}, url={philippine_systems_url}"
        )
        return await _use_send_json(send, {
            "ok": True,
            "version": APP_VERSION,
            "query": query,
            "intent": "SYSTEMS_PH_HANDOFF",
            "response": "",
            "handoff": "systems_ph",
            "handoff_mode": "direct",
            "handoff_pending": True,
            "philippine_systems_url": philippine_systems_url,
            "return_mode": "native_philippine_systems_landing",
            "visitor_boundary_version": APP_VERSION,
            "request_id": request_id,
        })

    if route_id == "fsd":
        fsd_url = _fsd_handoff_url(query)
        request_id = "fsd-" + hashlib.sha1(
            (query + "|" + _history_text(history)).encode("utf-8")
        ).hexdigest()[:16]
        print(
            "The Guide direct FSD handoff: "
            f"request_id={request_id}, url={fsd_url}"
        )
        return await _use_send_json(send, {
            "ok": True,
            "version": APP_VERSION,
            "query": query,
            "intent": "FSD_HANDOFF",
            "response": "",
            "handoff": "fsd",
            "handoff_mode": "direct",
            "handoff_pending": True,
            "fsd_url": fsd_url,
            "return_mode": "native_fsd_landing",
            "visitor_boundary_version": APP_VERSION,
            "request_id": request_id,
        })

    # Catalogue is a visitor-facing specialist surface, not a Guide retrieval
    # spoke. Preserve the visitor's request and let the native Catalogue own
    # the actual resource search and presentation.
    if route_id == "catalogue":
        catalogue_url = _catalogue_handoff_url(query)
        request_id = "catalogue-" + hashlib.sha1(
            (query + "|" + _history_text(history)).encode("utf-8")
        ).hexdigest()[:16]
        print(
            "The Guide direct Catalogue handoff: "
            f"request_id={request_id}, url={catalogue_url}"
        )
        return await _use_send_json(send, {
            "ok": True,
            "version": APP_VERSION,
            "query": query,
            "intent": "CATALOGUE_HANDOFF",
            "response": "",
            "handoff": "catalogue",
            "handoff_mode": "direct",
            "handoff_pending": True,
            "catalogue_query": query,
            "catalogue_url": catalogue_url,
            "return_mode": "native_catalogue_search",
            "visitor_boundary_version": APP_VERSION,
            "request_id": request_id,
        })

        # Navigator is a visitor-facing specialist surface. Hand the original
    # inquiry to its native Start Here/Navigator experience rather than
    # duplicating its multi-step retrieval and path-planning logic.
    if route_id == "navigator":
        navigator_url = _navigator_handoff_url(query)
        request_id = "navigator-" + hashlib.sha1(
            (query + "|" + _history_text(history)).encode("utf-8")
        ).hexdigest()[:16]
        print(
            "The Guide direct Navigator handoff: "
            f"request_id={request_id}, url={navigator_url}"
        )
        return await _use_send_json(send, {
            "ok": True,
            "version": APP_VERSION,
            "query": query,
            "intent": "NAVIGATOR_HANDOFF",
            "response": "",
            "handoff": "navigator",
            "handoff_mode": "entrance",
            "handoff_pending": True,
            "navigator_url": navigator_url,
            "return_mode": "native_archive_navigator_welcome",
            "visitor_boundary_version": APP_VERSION,
            "request_id": request_id,
        })

# Atlas is a visitor-facing specialist surface, not a Guide retrieval
    # spoke. Hand the original inquiry to the native Atlas Finder surface.
    if route_id == "atlas":
        atlas_url = _atlas_handoff_url(query)
        request_id = "atlas-" + hashlib.sha1(
            (query + "|" + _history_text(history)).encode("utf-8")
        ).hexdigest()[:16]
        print(
            "The Guide direct Atlas handoff: "
            f"request_id={request_id}, url={atlas_url}"
        )
        return await _use_send_json(send, {
            "ok": True,
            "version": APP_VERSION,
            "query": query,
            "intent": "ATLAS_HANDOFF",
            "response": "",
            "handoff": "atlas",
            "handoff_mode": "direct",
            "handoff_pending": True,
            "atlas_query": query,
            "atlas_url": atlas_url,
            "return_mode": "native_atlas_finder",
            "visitor_boundary_version": APP_VERSION,
            "request_id": request_id,
        })

    # Case Navigator is a visitor-facing native structural search surface.
    # The native Navigator owns terrain/stage/case inference and presentation.
    if route_id == "case":
        case_url = _case_handoff_url(query)
        request_id = "case-" + hashlib.sha1(
            (query + "|" + _history_text(history)).encode("utf-8")
        ).hexdigest()[:16]
        print(
            "The Guide direct Case Navigator handoff: "
            f"request_id={request_id}, url={case_url}"
        )
        return await _use_send_json(send, {
            "ok": True,
            "version": APP_VERSION,
            "query": query,
            "intent": "CASE_HANDOFF",
            "response": "",
            "handoff": "case",
            "handoff_mode": "direct",
            "handoff_pending": True,
            "case_query": query,
            "case_url": case_url,
            "return_mode": "native_case_navigator",
            "visitor_boundary_version": APP_VERSION,
            "request_id": request_id,
        })
    # Glyph Finder is a visitor-facing native search surface. The native
    # Finder owns identity resolution, semantic evidence weighting, and
    # presentation; USE only carries the original inquiry across the boundary.
    if route_id == "glyph":
        glyph_url = _glyph_handoff_url(query)
        request_id = "glyph-" + hashlib.sha1(
            (query + "|" + _history_text(history)).encode("utf-8")
        ).hexdigest()[:16]
        print(
            "The Guide direct Glyph Finder handoff: "
            f"request_id={request_id}, url={glyph_url}"
        )
        return await _use_send_json(send, {
            "ok": True,
            "version": APP_VERSION,
            "query": query,
            "intent": "GLYPH_HANDOFF",
            "response": "",
            "handoff": "glyph",
            "handoff_mode": "direct",
            "handoff_pending": True,
            "glyph_query": query,
            "glyph_url": glyph_url,
            "return_mode": "native_guardian_glyph_finder",
            "visitor_boundary_version": APP_VERSION,
            "request_id": request_id,
        })

    # Glossary is a visitor-facing specialist surface, not a Guide retrieval
    # spoke. Hand the canonical term to the Glossary's existing native search
    # contract and let WordPress perform the authoritative lookup/rendering.
    if route_id == "glossary" and mode in {"lookup", "definition"}:
        interpretation = route.get("round1_interpretation") or {}
        glossary_term = _normalize_glossary_term(query, interpretation)
        if glossary_term:
            glossary_url = (
                "https://geralddaquila.com/glossary/?glossary_term="
                + quote(glossary_term, safe="")
            )
            print(
                "The Guide direct Glossary handoff: "
                f"term={glossary_term!r}, url={glossary_url}"
            )
            return await _use_send_json(send, {
                "ok": True,
                "version": APP_VERSION,
                "query": query,
                "intent": "GLOSSARY_HANDOFF",
                "response": "",
                "handoff": "glossary",
                "handoff_mode": "direct",
                "handoff_pending": True,
                "glossary_term": glossary_term,
                "glossary_url": glossary_url,
                "return_mode": "native_glossary_search",
                "visitor_boundary_version": APP_VERSION,
            })

    if should_delegate:
        request_id = route_id + "-" + hashlib.sha1((query + "|" + _history_text(history)).encode("utf-8")).hexdigest()[:16]
        if route_id == "formation":
            try:
                result = _formation_specialist_response(query, history, route, request_id)
                return await _use_send_json(send, {
                    "ok": True, "version": APP_VERSION, "query": query,
                    "intent": "FORMATION_HANDOFF", "response": result["response"],
                    "formation_delegation": result["formation_delegation"],
                    "visitor_boundary_version": APP_VERSION, "request_id": request_id,
                })
            except Exception as exc:
                print(f"USE Formation specialist failed safely: {exc}")
                return await _use_send_json(send, {
                    "ok": False, "version": APP_VERSION, "query": query,
                    "intent": "FORMATION_HANDOFF",
                    "response": "The Formation pathway could not be opened right now.",
                    "error_type": "formation_specialist_failure", "request_id": request_id,
                }, 503)
        try:
            result = _relationship_specialist_response(query, history, route, request_id, parsed_body)
            return await _use_send_json(send, {
                "ok": True, "version": APP_VERSION, "query": query,
                "intent": "RELATIONAL_HANDOFF", "response": result["response"],
                "handoff": "relationship", "handoff_mode": "specialist",
                "relational_delegation": result["relational_delegation"],
                "visitor_boundary_version": APP_VERSION, "request_id": request_id,
            })
        except Exception as exc:
            print(f"USE Relationship specialist failed safely: {exc}")
            return await _use_send_json(send, {
                "ok": False, "version": APP_VERSION, "query": query,
                "intent": "RELATIONAL_HANDOFF",
                "response": "The Seeing the Relationship pathway could not be opened right now.",
                "error_type": "relationship_specialist_failure",
                "relational_delegation": {"state": "unavailable", "specialist": "Seeing the Relationship",
                                          "specialist_id": "relationship", "session_id": request_id},
                "visitor_boundary_version": APP_VERSION, "request_id": request_id,
            }, 503)

    # Exactly one fallback into the original protected application.
    await _FASTAPI_APP(scope, _use_replay_receive(raw_body), send)


FORMATION_ENTRANCE_CONTRACT_VERSION = "v1"
FORMATION_ENTRANCE_SOURCE = "steward-entrance"


def _formation_entrance_error(message, error_type, status_code=400):
    return JSONResponse(
        status_code=status_code,
        content={
            "ok": False,
            "version": APP_VERSION,
            "intent": "FORMATION_HANDOFF",
            "response": "",
            "error_type": error_type,
            "contract_version": FORMATION_ENTRANCE_CONTRACT_VERSION,
            "source": FORMATION_ENTRANCE_SOURCE,
            "message": message,
        },
    )


# v488.36 startup audit: verify the Basic Inquiry seam against the protected core.
_v48831_basic_inquiry_seam_self_audit()

@app.post("/api/formation-entrance")
async def _formation_entrance_route(request: Request):
    try:
        body = await request.json()
    except Exception:
        return _formation_entrance_error(
            "The Formation entrance payload must be valid JSON.",
            "formation_entrance_invalid_json",
        )

    if not isinstance(body, dict):
        return _formation_entrance_error(
            "The Formation entrance payload must be a JSON object.",
            "formation_entrance_invalid_payload",
        )

    choice = str(body.get("choice") or "").strip()
    situation = str(body.get("situation") or "").strip()
    possibility = str(body.get("possibility") or "").strip()

    missing = [
        name for name, value in (
            ("choice", choice),
            ("situation", situation),
            ("possibility", possibility),
        ) if not value
    ]
    if missing:
        return _formation_entrance_error(
            "The Formation entrance requires choice, situation, and possibility.",
            "formation_entrance_missing_fields",
        )

    contract_version = str(
        body.get("contract_version") or FORMATION_ENTRANCE_CONTRACT_VERSION
    ).strip()
    source = str(body.get("source") or FORMATION_ENTRANCE_SOURCE).strip()

    if contract_version != FORMATION_ENTRANCE_CONTRACT_VERSION:
        return _formation_entrance_error(
            "Unsupported Formation entrance contract version.",
            "formation_entrance_contract_version",
        )
    if source != FORMATION_ENTRANCE_SOURCE:
        return _formation_entrance_error(
            "Unsupported Formation entrance source.",
            "formation_entrance_source",
        )

    # Steward Entrance is itself a Guide-owned request boundary.
    # Propagate one bounded request identity through the common specialist pipe.
    request_id = (
        "guide-formation-"
        + hashlib.sha1(
            (
                FORMATION_ENTRANCE_SOURCE
                + "|"
                + choice
                + "|"
                + situation
                + "|"
                + possibility
            ).encode("utf-8")
        ).hexdigest()[:16]
    )

    try:
        contribution = invoke_specialist(
            SPECIALIST_ADAPTER_REGISTRY,
            request_id=request_id,
            guide_version=APP_VERSION,
            specialist_id="formation",
            original_question=situation,
            recognized_territory="stewardship formation",
            processing_purpose="bounded formation navigation from Steward Entrance",
            guide_context={
                "choice": choice,
                "situation": situation,
                "possibility": possibility,
            },
            safety_state="green",
        )
    except Exception as exc:
        print(f"USE v487.92 Formation entrance failed safely: {exc}")
        return _formation_entrance_error(
            "The Formation pathway could not be opened right now.",
            "formation_entrance_specialist_failure",
            status_code=503,
        )

    # The adapter bridges Formation's domain contract into the common
    # specialist pipe. Read the preserved domain payload, not the common
    # envelope's optional interpretation field.
    domain_payload = dict(contribution.get("payload") or {})
    interpretation = dict(domain_payload.get("interpretation") or {})
    movement = dict(domain_payload.get("movement") or {})
    doors = list(contribution.get("canonical_candidates") or [])

    bounded_doors = []
    seen_ids = set()
    for door in doors:
        if not isinstance(door, dict):
            continue
        door_id = str(door.get("id") or "").strip()
        title = str(door.get("title") or "").strip()
        url = str(door.get("url") or "").strip()
        if not door_id or door_id in seen_ids:
            continue
        if not title or not re.match(r"^https://geralddaquila\.com/\S+$", url, re.I):
            continue
        seen_ids.add(door_id)
        bounded_doors.append(
            {
                "id": door_id,
                "title": title,
                "url": url,
            }
        )
        if len(bounded_doors) >= 3:
            break

    return JSONResponse(
        status_code=200,
        content={
            "ok": True,
            "version": APP_VERSION,
            "intent": "FORMATION_HANDOFF",
            "contract_version": FORMATION_ENTRANCE_CONTRACT_VERSION,
            "source": FORMATION_ENTRANCE_SOURCE,
            "request_id": request_id,
            "choice": choice,
            "situation": situation,
            "possibility": possibility,
            "response": str(interpretation.get("pathway") or "").strip(),
            "formation_contribution": {
                "status": str(contribution.get("status") or ""),
                "contract_version": FORMATION_CONTRIBUTION_CONTRACT_VERSION,
                "voice_policy": FORMATION_VOICE_POLICY,
                "interpretation": interpretation,
                "movement": movement,
                "canonical_candidates": bounded_doors,
                "boundary_notes": contribution.get("boundary_notes"),
                "safety_flags": contribution.get("safety_flags"),
            },
            "visitor_boundary_version": APP_VERSION,
        },
    )




if not any(getattr(route, "path", "") == "/api/formation-entrance" for route in app.routes):
    raise RuntimeError("USE formation entrance route registration invariant failed")

@app.post("/api/relational-return")
async def _v48755_relational_return_route(request: Request):
    return await _v48755_relational_return(request)


# v488.17 Philippine Systems native doorway invariant.
if _philippine_systems_handoff_url("test") != "https://geralddaquila.com/understanding-the-philippines-culture-society-history-and-systemic-transformation/":
    raise RuntimeError("USE v488.17 invariant failed: Philippine Systems landing URL drift.")
if "systems_ph" not in _GUIDE_ROUTE_IDS:
    raise RuntimeError("USE v488.17 invariant failed: Philippine Systems route missing.")

# v488.17 FSD native doorway invariants.
if _fsd_handoff_url("test") != "https://geralddaquila.com/fractal-systems-diagnostic-2/":
    raise RuntimeError("USE v488.17 invariant failed: FSD landing URL drift.")
if "fsd" not in _GUIDE_ROUTE_IDS:
    raise RuntimeError("USE v488.17 invariant failed: FSD route missing.")
_fsd_route_probes = (
    "What's wrong with my organization? Can you help me where to start.",
    "Something is wrong with my organization. Where do I start?",
    "Can you help me understand what is happening in my organization?",
    "Why does our community keep getting stuck in the same pattern?",
)
if not all(_is_fsd_request(item) for item in _fsd_route_probes):
    raise RuntimeError("USE v488.17 invariant failed: natural systems diagnostic doorway not recognized.")
_fsd_nonroute_probes = (
    "What does stewardship mean?",
    "Can you define continuity?",
)
if any(_is_fsd_request(item) for item in _fsd_nonroute_probes):
    raise RuntimeError("USE v488.17 invariant failed: glossary definitions were captured by FSD.")

# The middleware, not mutation of FastAPI's stored endpoint objects, owns
# relational interception. This preserves the base route's validated request
# contract for every non-relational query.
if not any(getattr(route, "path", "") == "/api/relational-return" for route in app.routes):
    raise RuntimeError("USE v487.57 invariant failed: relational return route not registered")

# Single authoritative request boundary; all non-specialist requests fall through once.
app = _use_request_boundary



print(f"USE ACTIVE + FORMATION SPECIALIST v1: version={APP_VERSION}, fingerprint={DEPLOYMENT_FINGERPRINT}, core_sha={EXPECTED_CORE_BLOB_SHA}, source_sha256={RUNTIME_SOURCE_SHA256}, specialist_contract={SPECIALIST_PIPE_CONTRACT_VERSION}, adapter_contract={SPECIALIST_ADAPTER_CONTRACT_VERSION}, relationship_contract={RELATIONSHIP_CONTRIBUTION_CONTRACT_VERSION}, relationship_voice_policy={RELATIONSHIP_VOICE_POLICY}, formation_contract={FORMATION_CONTRIBUTION_CONTRACT_VERSION}, formation_voice_policy={FORMATION_VOICE_POLICY}, registered_specialists={len(SPECIALIST_CAPABILITY_REGISTRY)}, active_adapters={len(SPECIALIST_ADAPTER_REGISTRY.ids())}, provider_bank_contract={PROVIDER_BANK_CONTRACT_VERSION}, capability_routing=provider_model_bank")
print(f"USE SAFETY INTELLIGENCE: contract={SAFETY_INTELLIGENCE_CONTRACT_VERSION}, authority=HRN_Safety_Fractal_and_Emergency_Intelligence, resource_owner=Emergency Intelligence, resource_contract=living-archive/emergency/v1/resolve, sibling_link=relationship")

# v487.88 synthesis hardening invariant: shared synthesis packaging is bounded and consumed downstream.
if SHARED_EVIDENCE_CONTRACT_VERSION != "v1":
    raise RuntimeError("USE v487.88 invariant failed: shared evidence contract drift.")

# v487.88 synthesis hardening invariant: USE answer composition consumes the shared claim transformer and synthesis packager exactly once.
if "claims = _normalize_shared_claims_for_use(docs or [])" not in open(_MAIN_PATH, encoding="utf-8").read():
    raise RuntimeError("USE v487.87 invariant failed: shared claim seam wiring missing.")
if "synthesis = _build_shared_synthesis_material_for_use(claims)" not in open(_MAIN_PATH, encoding="utf-8").read():
    raise RuntimeError("USE v487.87 invariant failed: shared synthesis seam wiring missing.")
if "build_synthesis_material as _shared_build_synthesis_material" not in open(_MAIN_PATH, encoding="utf-8").read():
    raise RuntimeError("USE v487.87 invariant failed: shared synthesis primitive import missing.")
if "normalize_journey_contribution as _normalize_shared_journey" not in open(_MAIN_PATH, encoding="utf-8").read():
    raise RuntimeError("USE v487.92 invariant failed: journey contribution seam wiring missing.")
if "_build_journey_contribution_for_use(body)" not in open(_MAIN_PATH, encoding="utf-8").read():
    raise RuntimeError("USE v487.92 invariant failed: journey contribution adapter consumption missing.")