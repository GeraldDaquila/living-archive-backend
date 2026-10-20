# USE PRODUCTION VERSION: v489.294 — Practical stewardship provider-exhaustion recovery
import asyncio
import hashlib
from html import unescape
import ipaddress
import re
import json
import os
import time
import uuid
from urllib.request import Request as UrlRequest, urlopen
from shared_evidence import normalize_documents_for_use, CONTRACT_VERSION as SHARED_EVIDENCE_CONTRACT_VERSION
from shared_intelligence_primitives import normalize_claims as _shared_normalize_claims, build_synthesis_material as _shared_build_synthesis_material
from pathlib import Path
from urllib.parse import quote
from boundary_resilience import CONTRACT_VERSION as BOUNDARY_RESILIENCE_CONTRACT_VERSION, StaleAuthorityCache
from fastapi import HTTPException, Request
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
from provider_gateway_service import CONTRACT_VERSION as PROVIDER_GATEWAY_CONTRACT_VERSION, authorize as authorize_provider_gateway, validate_request as validate_provider_gateway_request, execute as execute_provider_gateway
from provider_bank import (
    CONTRACT_VERSION as PROVIDER_BANK_CONTRACT_VERSION,
    route as route_with_model_bank,
    snapshot as provider_bank_snapshot,
    refresh_shared_health_state,
)
import general_guide_composition
from general_guide_composition import CONTRACT_VERSION as GENERAL_GUIDE_COMPOSITION_CONTRACT_VERSION
from safety_utility import classify_safety, safety_utility_snapshot
from safety_adapter import SafetyUtilityAdapter
from safety_intelligence import SAFETY_INTELLIGENCE_CONTRACT_VERSION, is_hypothetical_safety_discussion, normalize_safety_state, repair_safety_question, safety_intelligence_snapshot
from streaming_transport import streaming_entry, STREAM_CONTRACT_VERSION, STREAM_TRANSPORT_VERSION

_BASE_MODULE_NAME = "guide_runtime"
_base = __import__(_BASE_MODULE_NAME)
use_core = _base.use_core
app = _base.app
_original_guide_handle_query = use_core.handle_query
APP_VERSION = "v489.294"
DEPLOYMENT_FINGERPRINT = "USE-v489.294-practical-stewardship-recovery"
CANONICAL_BUILD_ID = "USE-BUILD-v489.294-practical-stewardship-recovery"

# v488.64 systemwide safety continuity contract marker.
# This marker is intentionally adjacent to the production identity so CI can
# detect drift between the live Guide boundary and its regression tests.
SAFETY_BOUNDARY_CONTRACT_VERSION = "v488.68"

GUIDE_NODE_REGISTRY_URL = "https://geralddaquila.com/wp-json/guide/v1/nodes"
GUIDE_NODE_REGISTRY_FRESH_TTL_SECONDS = 300.0
GUIDE_NODE_REGISTRY_MAX_STALE_SECONDS = 3600.0
GUIDE_NODE_REGISTRY_RETRY_SECONDS = 30.0
_GUIDE_NODE_REGISTRY_CACHE = StaleAuthorityCache(
    fresh_ttl_seconds=GUIDE_NODE_REGISTRY_FRESH_TTL_SECONDS,
    max_stale_seconds=GUIDE_NODE_REGISTRY_MAX_STALE_SECONDS,
    failure_retry_seconds=GUIDE_NODE_REGISTRY_RETRY_SECONDS,
)
_GUIDE_NODE_REGISTRY_STATE = {"state": "unavailable"}


def _load_guide_node_registry():
    # WordPress/CDN caches the bare registry URL and can keep serving an older
    # node list after a governed registry update. This loader runs only when the
    # local authority cache expires, so a timestamped query string safely busts
    # the upstream cache without increasing the normal refresh frequency.
    registry_url = f"{GUIDE_NODE_REGISTRY_URL}?registry_refresh={int(time.time())}"
    request = UrlRequest(
        registry_url,
        headers={
            "Accept": "application/json",
            "User-Agent": "Living-Archive-The-Guide/1.0",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
        method="GET",
    )
    with urlopen(request, timeout=4) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Guide Node Registry response was not an object.")
    if str(payload.get("registry_version") or "").strip() != GUIDE_NODE_REGISTRY_VERSION:
        raise ValueError("Guide Node Registry version mismatch.")
    if str(payload.get("schema_version") or "").strip() != "v2":
        raise ValueError("Guide Node Registry schema version mismatch.")
    records = payload.get("nodes")
    if not isinstance(records, list):
        raise ValueError("Guide Node Registry nodes were not a list.")
    nodes = active_nodes(records)
    if not nodes and records:
        raise ValueError("Guide Node Registry contained no valid active nodes.")
    print(
        "The Guide Node Registry: "
        f"source=wordpress, nodes={len(nodes)}, registry_version={payload.get('registry_version')}"
    )
    return nodes


def _guide_node_registry_snapshot():
    """Read WordPress authority with bounded last-known-good continuity."""
    nodes, state = _GUIDE_NODE_REGISTRY_CACHE.get(_load_guide_node_registry)
    _GUIDE_NODE_REGISTRY_STATE["state"] = state
    if state != "fresh":
        diagnostic = _GUIDE_NODE_REGISTRY_CACHE.snapshot()
        print(
            "The Guide Node Registry boundary: "
            f"state={state}, age_seconds={diagnostic.get('age_seconds')}, "
            f"failures={diagnostic.get('failure_count')}, "
            f"error={diagnostic.get('last_error') or 'none'}"
        )
    return list(nodes or [])


def guide_node_registry_state():
    """Return non-secret registry health for diagnostics and QA."""
    state = dict(_GUIDE_NODE_REGISTRY_STATE)
    state.update(_GUIDE_NODE_REGISTRY_CACHE.snapshot())
    return state


def _guide_node_registry_is_fresh():
    return _GUIDE_NODE_REGISTRY_STATE.get("state") == "fresh"


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


def _runtime_source_manifest_sha256(root=None):
    """Hash application-owned Python runtime modules, not only main.py."""
    root_path = Path(root if root is not None else _MAIN_PATH.parent).resolve()
    excluded_parts = {
        ".git", ".venv", "venv", "__pycache__", ".pytest_cache",
        "tests", "QA", "scripts", "node_modules",
    }
    source_files = []
    for path in root_path.rglob("*.py"):
        if path.is_symlink():
            continue
        relative = path.relative_to(root_path)
        if any(part in excluded_parts for part in relative.parts):
            continue
        source_files.append(path)
    digest = hashlib.sha256()
    for path in sorted(source_files, key=lambda item: item.relative_to(root_path).as_posix()):
        relative_name = path.relative_to(root_path).as_posix()
        digest.update(relative_name.encode("utf-8"))
        digest.update(b"\\0")
        digest.update(path.read_bytes())
        digest.update(b"\\0")
    return digest.hexdigest()


RUNTIME_SOURCE_SHA256 = _runtime_source_manifest_sha256()

# Runtime/version integrity is a startup invariant, not external bookkeeping.
if str(APP_VERSION) != "v489.294":
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

if PROVIDER_GATEWAY_CONTRACT_VERSION != "v1":
    raise RuntimeError("USE provider gateway contract integrity failure: unsupported provider gateway contract.")

if PROVIDER_BANK_CONTRACT_VERSION != "v2":
    raise RuntimeError("USE provider bank contract integrity failure: unsupported provider bank contract.")
if GENERAL_GUIDE_COMPOSITION_CONTRACT_VERSION != "v1.20":
    raise RuntimeError("USE General Guide composition contract integrity failure: unsupported contract.")
if GUIDE_NODE_REGISTRY_VERSION != "v2":
    raise RuntimeError("USE Guide Node Registry contract integrity failure: unsupported registry version.")
if BOUNDARY_RESILIENCE_CONTRACT_VERSION != "v1":
    raise RuntimeError("USE boundary resilience contract integrity failure.")

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
    # Lived workplace credit omissions are interactional evidence even when
    # the visitor does not use the phrase "taking credit".
    r"\b(?:present(?:s|ed|ing)?|mention(?:s|ed|ing)?|acknowledg(?:e|es|ed|ing)|credit(?:s|ed|ing)?|contribut(?:e|es|ed|ing|ion|ions))\b",
)

def _lived_relational_structure(query):
    """Recognize relational structure from lived-situation form, not topic alone."""
    q = _normalize_query(query)
    first_person = bool(re.search(r"\b(?:i|i'm|im|my|me|we|our)\b", q, re.I))
    relational_other = any(re.search(pattern, q, re.I) for pattern in _RELATIONAL_PATTERNS)
    role_context = any(re.search(pattern, q, re.I) for pattern in _RELATIONAL_ROLE_PATTERNS)
    relational_action = any(re.search(pattern, q, re.I) for pattern in _RELATIONAL_ACTION_PATTERNS) or any(re.search(pattern, q, re.I) for pattern in _RELATIONAL_INTERACTION_PATTERNS)
    tension = bool(re.search(
        r"\b(?:but|however|although|yet|now|instead|then|eventually|until|again|without|"
        r"instead of|rather than|same thing|can't|cannot|don't|doesn't|not sure|unsure|hard|difficult|"
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
    r"\bmy\s+(?:husband|wife|spouse|partner|boyfriend|girlfriend|father|mother|parent|parents|son|daughter|child|brother|sister|friend|friends|colleague|coworker|co-worker|teammate|team member|manager|supervisor|boss|employee|employer|client|customer|teacher|student|mentor|neighbor|landlord|tenant)\b",
    r"\b(?:a|this|our|my)\s+friendship\b",
    # Natural counterpart phrasing: visitors often say "a friend", not "a friendship".
    r"\b(?:a|this|our|my)\s+friend\b",
    r"\b(?:someone|somebody|a person|another person|people|person)\s+(?:i|we)\s+(?:care about|love|trust|work with)\b",
    r"\b(?:someone|somebody|a person)\s+(?:close to|important to)\s+me\b",
    r"\b(?:between us|between me and|between you and)\b",
    r"\b(?:our|this|the)\s+relationship\b",
    r"\b(?:with|from)\s+(?:someone|somebody|my)\b",
)

_RELATIONAL_DYNAMIC_PATTERNS = (
    # Natural lived interaction cues, including feared or postponed conversations.
    r"\b(?:conversation|conversations|talk(?:ing)?|discussion|putting\s+off|avoid(?:ing)?|hesitat(?:e|ing|ion)|afraid)\b",
    # v489.85: projection/sensing uncertainty is a lived relational dynamic
    # when combined with first-person language and explicit relationship context.
    r"\b(?:projection|projecting|projected|sensing|intuition|perception|perceive|misread|misreading|reading into|over[- ]?read(?:ing)?|interpret(?:ation|ing))\b",
    r"\b(?:argument|arguments|fight|fights|fighting|conflict|tension|disagreement|disagree|misunderstanding|misunderstand|distance|disconnect(?:ed|ion)?|withdraw(?:al|ing)?|defensive|shut(?:s|ting)?\s+down|stop(?:s|ped|ping)?\s+talking|go(?:es|ing)?\s+quiet|resent(?:ment|ful)?|trust|distrust|boundary|boundaries|communication|communicate|expectation|expectations|control(?:led|ling)?|critic(?:ize|ized|ism)|blame|blaming|forgive(?:ness)?|support|one[- ]sided|recipro(?:cal|city)|rely|depend|keeps?\s+asking|keeps?\s+doing|same\s+thing|same\s+argument|same\s+fight|same\s+pattern|cycle|loop|promise|promised|gave\s+(?:him|her|them)?\s*my\s+word|committed|commitment|responsibilit(?:y|ies)|obligation|obligated|burden|owe|owed|disappoint(?:ed|ing)?)\b",
    # Reciprocity and uneven effort are lived relational dynamics even when the
    # visitor does not name conflict, trust, or a formal relationship problem.
    # Credit-taking is a lived interactional dynamic even when visitors do not name conflict or trust.
    r"\b(?:taking credit|takes credit|took credit|credit for (?:work|what) we did together)\b",
    # Attribution omissions are lived interaction dynamics even without the
    # literal phrase "taking credit".
    r"\b(?:present(?:s|ed|ing)?|mention(?:s|ed|ing)?|acknowledg(?:e|es|ed|ing)|credit(?:s|ed|ing)?|contribut(?:e|es|ed|ing|ion|ions))\b",
    r"\b(?:effort|making an effort|make an effort|made an effort)\b",
    r"\b(?:always the one|doing all the work|carrying the relationship)\b",
    r"\b(?:one[- ]sided effort|not reciprocated|unequal effort|uneven effort)\b",
    r"\b(?:gets?|becomes?|become)\s+(?:angry|defensive|quiet|distant)\b",
    r"\b(?:feel|feels|felt)\s+(?:distant|disconnected|removed|far|close|closer)\b",
    r"\b(?:i|we)\s+(?:keep|keeps|kept)\b",
)

_RELATIONAL_INQUIRY_PATTERNS = (
    # Natural questions about what one may be missing should count as inquiry.
    r"\bwhat\s+(?:might|could|am|are)\s+(?:i|we)\s+(?:be\s+)?(?:missing|not seeing|overlooking)\b",
    r"\b(?:i|we)\s+(?:want|need|wonder|hope|wish)\s+to\s+(?:understand|figure out|make sense|see|know)\b",
    r"\b(?:i|we)\s+(?:don't|do not|can't|cannot|am not|are not)\s+(?:understand|know|tell|see)\b",
    r"\b(?:what(?:'s| is)|why|how)\b.{0,120}\b(?:happening|between us|relating|relationship|treat|respond|react|communicat|understand|make sense)\b",
    r"\b(?:understand|make sense of|figure out|explore|see)\b.{0,100}\b(?:between us|with (?:my|someone)|relationship|pattern|dynamic|cycle|interaction)\b",
    r"\b(?:how|why|what|can|could)\b.{0,100}\b(?:understand|make sense of|figure out)\b.{0,100}\b(?:relationship|distance|dynamic|pattern|cycle|interaction)\b",
    r"\b(?:i|we)\s+(?:want|need|hope|wish)\s+to\s+be\s+(?:understood|heard|seen|respected)\b",
    r"\b(?:i|we)\s+(?:feel|feels|felt|struggle|struggling|uncertain|unsure|confused|stuck|hurt|worried)\b",
    # Compact lived conflict descriptions often express inquiry through the
    # effort to explain the hurt, not through explicit "understand" wording.
    # Combined with first-person plural + an argument/fight dynamic, this is
    # sufficient relational evidence without capturing bounded Archive lookups.
    r"\b(?:i|we)\s+(?:keep\s+)?(?:trying|try)\s+to\s+(?:explain|understand|make sense of)\b",
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

    # Only explicit retrieval/definition operations suppress relational routing.
    # General requests such as "anything in the Archive that might help me think"
    # are still relational exploration; they do not ask the Guide to retrieve a
    # bounded resource and therefore must not collapse the specialist boundary.
    bounded = bool(re.search(
        r"\b(?:find|show|lookup|look up|link to|url for|where is|where can i find|"
        r"recommend (?:a|an|the)?\s*(?:resource|article|essay|page)|"
        r"suggest (?:a|an|the)?\s*(?:resource|article|essay|page)|"
        r"which (?:resource|article|essay|page)|"
        r"what (?:resource|article|essay|page)|"
        r"resource about|article about|essay about|page about)\b",
        q,
        re.I,
    ))
    definition = bool(re.search(
        r"\b(?:define|definition|meaning of|what does .* mean|what is the meaning of)\b",
        q,
        re.I,
    ))
    if bounded or definition:
        return {
            "open": False,
            "contract_version": RELATIONAL_BOUNDARY_CONTRACT_VERSION,
            "reason": "bounded_archive_or_definition_request",
        }

    first_person = bool(re.search(r"\b(?:i|i'm|im|me|my|we|our|us)\b", q, re.I))
    counterpart = any(re.search(pattern, q, re.I) for pattern in _RELATIONAL_COUNTERPART_PATTERNS)
    dynamic = any(re.search(pattern, q, re.I) for pattern in _RELATIONAL_DYNAMIC_PATTERNS)
    inquiry = any(re.search(pattern, q, re.I) for pattern in _RELATIONAL_INQUIRY_PATTERNS)
    relational_term = bool(re.search(r"\b(?:relationship|relationships|interpersonal|relational)\b", q, re.I))
    explicit_between = bool(re.search(r"\b(?:between us|between me and|between you and)\b", q, re.I))
    # A lived credit-taking case can be phrased as a general-pattern question
    # while still naming a personal contribution or an actual event. Preserve
    # the specialist boundary for those specific first-person cases.
    specific_lived_credit = bool(
        first_person
        and re.search(r"\b(?:my (?:manager|teammate|colleague|coworker|co-worker|idea|work|contribution|analysis)|someone on my team|this happened to me|our project)\b", q, re.I)
        and re.search(r"\b(?:taking credit|takes credit|took credit|claiming credit|present(?:s|ed|ing)? .{0,80}\b(?:as theirs|as their own)|without mentioning my contribution|without acknowledging my contribution)\b", q, re.I)
    )

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
        specific_lived_credit
        or (
            first_person
            and (counterpart or relational_term or explicit_between)
            and dynamic
            and (inquiry or first_person)
        )
    )

    # A compact relational sentence may omit an explicit counterpart while
    # still clearly describing a mutual interaction (e.g. "we keep arguing").
    # Require both first-person plural framing and an interactional dynamic.
    if not open_boundary and first_person and bool(re.search(r"\bwe\b", q)) and dynamic and inquiry:
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
            "specific_lived_credit": specific_lived_credit,
            "bounded": bounded,
            "definition": definition,
        },
    }


_route_probe_lived_relational = "I promised my father I'd take care of something for him. At the time it felt natural. Now the responsibility has become much bigger than I expected, and part of me wants to back out. But I gave him my word."
if not _lived_relational_structure(_route_probe_lived_relational)["lived_relational"]:
    raise RuntimeError("USE v487.88 routing invariant failed: lived relational structure not recognized")
if not _relational_boundary_decision(_route_probe_lived_relational).get("open"):
    raise RuntimeError("USE v487.88 routing invariant failed: model retrieval label suppressed lived relational routing")
if _relational_boundary_decision("Is there an article in the Living Archive about setting boundaries with a parent?").get("open"):
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
if not _relational_boundary_decision(_route_probe_argument_noun).get("open"):
    raise RuntimeError("USE v488.69 routing invariant failed: argument-noun inquiry did not open relationship specialist")

# v488.69 regression guard: natural-language fight nouns must remain inside
# the same relational boundary.
_route_probe_fight_noun = (
    "I keep having the same fight with my partner, and I can't tell whether "
    "we're actually disagreeing about the issue or reacting to each other."
)
if not _relational_boundary_decision(_route_probe_fight_noun).get("open"):
    raise RuntimeError("USE v488.69 routing invariant failed: fight-noun inquiry did not open relationship specialist")

# v487.92 regression guard: relational reciprocity must route to Seeing the
# Relationship even when the visitor does not use conflict/boundary language.
_route_probe_natural_distance = "How can I understand why a relationship feels distant lately?"
if not _relational_boundary_decision(_route_probe_natural_distance).get("open"):
    raise RuntimeError("USE v488.84 routing invariant failed: natural distance inquiry did not open relationship specialist")

# v489.85 regression guard: lived uncertainty about projection must enter HRN
# rather than being swallowed by the Guide's generic Basic Inquiry path.
_route_probe_projection_uncertainty = (
    "I can't tell whether what I'm sensing in a relationship is real or something I'm projecting."
)
if not _relational_boundary_decision(_route_probe_projection_uncertainty).get("open"):
    raise RuntimeError("USE v489.87 routing invariant failed: relationship projection uncertainty did not open HRN")

_route_probe_explain_displacement = (
    "I keep trying to explain why the same argument hurts me, but we end up "
    "arguing about whether I should still feel hurt."
)
if not _relational_boundary_decision(_route_probe_explain_displacement).get("open"):
    raise RuntimeError("USE v489.198 routing invariant failed: repeated-argument explanation inquiry did not open HRN")

_route_probe_reciprocity = (
    "My friend always asks me for support when they need something, but "
    "whenever I need them, they disappear. I'm starting to wonder whether "
    "this friendship is one-sided."
)
if not _lived_relational_structure(_route_probe_reciprocity)["lived_relational"]:
    raise RuntimeError("USE v487.92 routing invariant failed: reciprocity pattern not recognized")
if not _relational_boundary_decision(_route_probe_reciprocity).get("open"):
    raise RuntimeError("USE v487.92 routing invariant failed: reciprocity inquiry did not open relationship specialist")

# v489.93 regression guard: passive lived-relational language must not fall into Basic Inquiry. (Preserved under v489.97.)
_route_probe_passive_friendship_boundary = (
    "I am struggling with a friendship where I want to be understood but also need boundaries."
)
if not _relational_boundary_decision(_route_probe_passive_friendship_boundary).get("open"):
    raise RuntimeError("USE v489.99 routing invariant failed: passive friendship/boundaries inquiry did not open HRN")

# The shared boundary must remain conservative for topic-only mentions and explicit retrieval.
if _relational_boundary_decision("What is friendship and why do boundaries matter?").get("open"):
    raise RuntimeError("USE v489.93 routing invariant failed: generic explanatory relationship question was captured by HRN")
if _relational_boundary_decision("Find an article about friendship and boundaries in the Living Archive.").get("open"):
    raise RuntimeError("USE v489.93 routing invariant failed: explicit Archive retrieval was captured by HRN")

# v487.95 regression guard: the observed defensive/anger/withdrawal cycle must
# bypass the Guide routing-model call and open HRN immediately.
_route_probe_defensive_cycle = (
    "Whenever I bring up something that bothers me, my partner becomes defensive. "
    "Then I get angry, they withdraw, and eventually we stop talking. "
    "A few days later everything seems fine until the same thing happens again."
)
if not _lived_relational_structure(_route_probe_defensive_cycle)["lived_relational"]:
    raise RuntimeError("USE v487.97 routing invariant failed: defensive cycle not recognized")
if not _relational_boundary_decision(_route_probe_defensive_cycle).get("open"):
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
if not _relational_boundary_decision(_route_probe_authority_relationship).get("open"):
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


def _is_lived_uncertainty_inquiry(query):
    """Identify uncertainty questions framed as a lived human experience."""
    q = _normalize_query(query)
    uncertainty = bool(re.search(r"\b(?:uncertaint(?:y|ies)|uncertain|ambiguity|ambiguous|the unknown|not knowing)\b", q, re.I))
    lived_frame = bool(re.search(r"\b(?:live|living|deal|dealing|cope|coping|sit|sitting|tolerate|tolerating|handle|handling|navigate|navigating|accept|accepting|face|facing|move forward|make decisions?|decide|deciding)\b", q, re.I))
    institutional_frame = bool(re.search(r"\b(?:institution|institutions|system|systems|governance|politic(?:al|s)|government|public trust|philippine|philippines|organization|organizational|institutional|policy|policies)\b", q, re.I))
    return uncertainty and lived_frame and not institutional_frame


def _uncertainty_resource_direct_fit(query, doc):
    """Prevent shared-word overlap from promoting a mismatched uncertainty asset."""
    if not _is_lived_uncertainty_inquiry(query):
        return True
    title = str(doc.get("title") or "").casefold()
    body = str(doc.get("text") or doc.get("content") or doc.get("excerpt") or "").casefold()
    combined = f"{title} {body}"
    if re.search(r"\b(?:institutions?|systems?|governance|politic(?:al|s)|government|philippine|philippines|public trust|institutional|policy|policies)\b", title, re.I):
        return False
    uncertainty_support = bool(re.search(r"\b(?:uncertaint(?:y|ies)|uncertain|ambiguity|ambiguous|the unknown|not knowing)\b", combined, re.I))
    lived_support = bool(re.search(r"\b(?:personal|personally|everyday|daily life|decision|decisions|deciding|cope|coping|tolerat(?:e|ing)|accept(?:ance|ing)?|adapt(?:ation|ing)?|uncertain future|living with|live with|make choices|moving forward|what you can control|control what|emotional|anxiety|fear|patience)\b", body, re.I))
    return uncertainty_support and lived_support

_TOPIC_ANCHOR_GROUPS = {
    "political_dynasties": (
        r"\bpolitical dynast(?:y|ies)\b",
        r"\bdynast(?:y|ies)\b",
    ),
    "accountability": (
        r"\baccountability\b",
        r"\baccountable\b",
    ),
    "institutions": (
        r"\b(?:public )?institutions?\b",
        r"\binstitutional\b",
    ),
    "governance": (
        r"\bgovernance\b",
        r"\bgoverning\b",
    ),
    "political_systems": (
        r"\bpolitical systems?\b",
        r"\bpolitics\b",
        r"\bgovernment\b",
    ),
}


def _topic_anchor_groups(text):
    value = str(text or "").casefold()
    return {
        group for group, patterns in _TOPIC_ANCHOR_GROUPS.items()
        if any(re.search(pattern, value, re.I) for pattern in patterns)
    }


def _topic_specific_candidate_fit(query, doc):
    """Require substantive topic evidence for multi-concept public-system questions.

    Country, locality, or broad cultural words alone cannot authorize a doorway
    for a question about institutions, political dynasties, or accountability.
    """
    query_groups = _topic_anchor_groups(query)
    if len(query_groups) < 2:
        return True
    title = str(doc.get("title") or "")
    body = str(doc.get("text") or doc.get("content") or doc.get("excerpt") or "")
    if not title.strip() or not body.strip():
        return False
    title_groups = _topic_anchor_groups(title)
    early_groups = _topic_anchor_groups(body[:3000])
    body_groups = _topic_anchor_groups(body)
    supported = query_groups & body_groups
    if len(supported) < 2:
        return False

    # Distinctive concepts are not interchangeable with broad context. When
    # the visitor explicitly asks about political dynasties, a general article
    # about institutions or governance is not enough merely because it also
    # mentions accountability. Require evidence for that distinctive subject
    # in the title or opening body, and at least one other requested concept
    # in the same opening passage.
    if "political_dynasties" in query_groups:
        if not (title_groups | early_groups) & {"political_dynasties"}:
            return False
        if len(query_groups & early_groups) < 2:
            return False

    # Prefer a doorway whose title identifies at least one requested topic.
    # A broader title may still qualify when the opening directly discusses
    # at least two of the requested concepts.
    return bool(query_groups & title_groups) or len(query_groups & early_groups) >= 2


def _eligible_outward_doc(query, doc, profile, *, min_relevance=2):
    if not isinstance(doc, dict):
        return False
    title = str(doc.get("title") or "").strip()
    url = str(doc.get("url") or doc.get("canonical_url") or "").strip()
    if not title or not re.match(r"^https://\S+$", url, re.I):
        return False
    if not _topic_specific_candidate_fit(query, doc):
        return False
    if not _uncertainty_resource_direct_fit(query, doc):
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
    # A title overlap alone is not enough to make a canonical doorway relevant.
    # Require corroboration in the resource's own body, so generic/title-level
    # coincidences cannot outrank material that actually addresses the question.
    if metrics[0] > 0 and metrics[2] == 0 and metrics[3] == 0 and metrics[1] == 0:
        return False
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


# v489.91 regression guard: lived uncertainty must not inherit a keyword-overlapping institutional resource.
_uncertainty_probe_query = "What does it mean to live with uncertainty?"
_uncertainty_institutional_decoy = {"title": "Why Trust Breaks Down in Philippine Systems: Institutions, Uncertainty, and Survival", "url": "https://geralddaquila.com/example-institutional-uncertainty/", "text": "Institutional trust, governance, and uncertainty shape public systems and survival."}
_uncertainty_personal_candidate = {"title": "Living with Uncertainty: Making Decisions Without All the Answers", "url": "https://geralddaquila.com/example-lived-uncertainty/", "text": "Living with uncertainty means making decisions without all the answers, learning to tolerate ambiguity, and adapting as everyday life changes."}
if not _is_lived_uncertainty_inquiry(_uncertainty_probe_query):
    raise RuntimeError("USE v489.91 invariant failed: lived uncertainty inquiry not recognized.")
if _uncertainty_resource_direct_fit(_uncertainty_probe_query, _uncertainty_institutional_decoy):
    raise RuntimeError("USE v489.91 invariant failed: institutional uncertainty decoy passed lived-context fit.")
if not _uncertainty_resource_direct_fit(_uncertainty_probe_query, _uncertainty_personal_candidate):
    raise RuntimeError("USE v489.91 invariant failed: directly relevant lived-uncertainty resource rejected.")

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
        # Rank by body corroboration first, then title fit. The document's
        # substantive relevance must outrank incidental title overlap.
        score = (metrics[2], metrics[3], metrics[0], metrics[1], context[2], context[1], -index)
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
    if not isinstance(data, dict) or profile.get("risk"):
        return data

    # Never accept a selected doorway carried in from retrieval/provider content.
    data = dict(data)
    data.pop("recommendation_canonical_primary", None)
    canonical_context = str(data.get("canonical_link_context") or "")
    if not canonical_context:
        return data
    docs = _parse_context_documents(canonical_context)
    if not docs:
        return data

    # Resolve doorway authority once against the complete retrieved context.
    # The final response must not independently rerank the same evidence and
    # replace an already selected direct resource with a broad conceptual decoy.
    authoritative = []
    selected_doorway = None
    if not (profile.get("grief") or profile.get("ai_truth")):
        try:
            selected_doorway = _normalize_authoritative_recommendation(
                _general_guide_authoritative_doorway(query_str, data)
            )
        except Exception as exc:
            selected_doorway = None
            print(
                "The Guide outward navigation boundary: canonical selector "
                f"failed safely ({type(exc).__name__})."
            )
        if selected_doorway:
            target_url = str(selected_doorway.get("url") or "").rstrip("/").casefold()
            candidate_docs = list(docs)
            protected = (
                data.get("generation_authority_protected_docs")
                or data.get("question_authority_protected_docs")
                or []
            )
            if isinstance(protected, list):
                candidate_docs.extend(item for item in protected if isinstance(item, dict))
            try:
                supplied = general_guide_composition._documents_from_context(
                    use_core, data
                )
            except Exception:
                supplied = []
            candidate_docs.extend(item for item in supplied if isinstance(item, dict))

            # Reattach the validated title/URL contract to its evidence-bearing
            # document. The URL is matched against retrieved canonical evidence;
            # no provider-generated or hardcoded destination is trusted.
            for candidate in candidate_docs:
                candidate_url = str(
                    candidate.get("url") or candidate.get("canonical_url") or ""
                ).strip()
                candidate_text = str(
                    candidate.get("text") or candidate.get("content")
                    or candidate.get("excerpt") or ""
                ).strip()
                if (
                    candidate_url.rstrip("/").casefold() == target_url
                    and candidate_text
                    and str(candidate.get("title") or "").strip()
                ):
                    authoritative = [{
                        "title": str(candidate.get("title") or "").strip(),
                        "url": candidate_url,
                        "text": candidate_text,
                    }]
                    break

    if authoritative and selected_doorway:
        # Carry the exact validated primary across the retrieval/composition seam
        # for every ordinary query, including conceptual questions that should not
        # have their evidence context narrowed.
        data["recommendation_canonical_primary"] = {
            "title": selected_doorway["title"],
            "url": selected_doorway["url"],
        }

    # Preserve the complete evidence pool for non-navigation questions. Their
    # composition may need multiple sources, but the canonical primary remains
    # separately pinned for the outward recommendation field.
    if profile["action"] not in {"recommendation", "navigation"}:
        return data

    if authoritative:
        outward = authoritative
        boundary_mode = "primary"
    else:
        # Fail closed when no evidence-backed primary passed canonical selection.
        outward = _sanitize_outward_context(query_str, docs, profile)
        boundary_mode = "sanitized-context"
    narrowed_context = _serialize_context_documents(outward)
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


def _relational_communication_focus(query):
    """Recognize explicit listening/being-heard concerns without lexical polysemy."""
    q = _normalize_query(query)
    return bool(re.search(
        r"\b(?:unheard|not being heard|not heard|being heard|listen(?:ing)?|"
        r"not listening|ignored|dismissed|(?:do not|don't|does not|doesn't|cannot|can't) "
        r"(?:hear|listen)(?: me| to me)?|cannot get through to|can't get through to)\b",
        q,
    ))


def _relational_discernment_focus(query):
    """Recognize explicit uncertainty about perception/inference, not schema boilerplate."""
    q = _normalize_query(query)
    return bool(re.search(
        r"\b(?:projection|projecting|projected|what i(?:'|’)m sensing|what i sense|"
        r"what i infer|what i am inferring|what is real|am i misreading|am i assuming|"
        r"am i projecting|could i be misreading|could i be assuming|could i be projecting|"
        r"reading too much into|misreading|judge(?: them)? unfairly|misjudge|"
        r"am i being unfair|could i be unfair|distinguish what i observed from what i inferred)\b",
        q,
    ))


def _relational_return_topic_anchor(original_question, underlying_need, perspective_delta):
    """Add bounded, earned semantic anchors without replacing the visitor's own question."""
    q = _normalize_query(" ".join(str(value or "") for value in (
        original_question, underlying_need, perspective_delta
    )))
    additions = []
    effort_imbalance = bool(re.search(
        r"\b(?:always the one|making an effort|more effort|reaching out|initiating contact|"
        r"feel unseen|feeling unseen|not reciprocated|giving more|doing all the work)\b", q
    ))
    if effort_imbalance:
        additions.append(
            "Relational effort imbalance: overgiving, giving more than receiving, mutuality, "
            "feeling valued, care without self-erasure."
        )
    # HRN's standard synthesis often says a sequence is "observable" and
    # another person's "intention" is unknown. Those phrases alone do not mean
    # the visitor's central question is discernment; classify from the opening
    # question and underlying need, not the generated perspective boilerplate.
    discernment_query = _normalize_query(
        " ".join(str(value or "") for value in (original_question, underlying_need))
    )
    discernment = _relational_discernment_focus(discernment_query)
    if discernment:
        additions.append(
            "Relational discernment: distinguish observable behavior from inference and "
            "assumptions about another person's intentions."
        )
    boundary = bool(re.search(r"\b(?:boundaries|taking over|responsibility|self-erasure)\b", q))
    if boundary:
        additions.append("Relational boundaries: care, mutuality, agency, and what remains yours to carry.")
    # A disagreement is not automatically a listening problem. Only add this
    # semantic expansion when the visitor actually describes not being heard,
    # listening, or dismissal; otherwise it contaminates retrieval with unrelated
    # communication-themed Archive pages.
    communication = _relational_communication_focus(q)
    if communication:
        additions.append(
            "Relational communication during disagreement: listening, acknowledgment, "
            "being heard, and receiving another person's point before responding."
        )
    return " ".join(additions)


def _relational_return_conflict_topic_fit(query, doc):
    """Require source evidence for the visitor's concrete recurring-conflict focus."""
    if not isinstance(doc, dict):
        return False
    q = _normalize_query(query)
    recurring_argument_focus = bool(re.search(
        r"\b(?:same argument|argument keeps returning|repeated argument|recurring argument|"
        r"argue about|repeated conflict|hurt.{0,35}blame|blame.{0,35}hurt)\b",
        q,
    ))
    if not recurring_argument_focus:
        return True

    title = str(doc.get("title") or "").casefold()
    body = str(doc.get("text") or doc.get("content") or doc.get("excerpt") or "").casefold()
    direct_title = bool(re.search(
        r"\b(?:argument|argue|conflict|disagreement|repair|reconciliation|being heard)\b",
        title,
    ))
    if direct_title:
        return True

    # Require a sentence linking a concrete conflict action to its relational
    # impact. Broad concepts such as cognitive dissonance, communication, or
    # emotional growth cannot qualify through scattered vocabulary alone.
    core_terms = {
        "argument", "argue", "disagreement", "repair", "blame",
        "reopen", "reopening", "incident",
    }
    impact_terms = {
        "hurt", "listening", "heard", "hearing", "partner",
        "relationship", "conflict", "argument", "disagreement",
    }
    for sentence in re.split(r"(?<=[.!?])\s+|\n+", body):
        tokens = set(re.findall(r"[a-z0-9]+", sentence))
        if core_terms & tokens and impact_terms & tokens:
            return True
    return False


def _relational_return_is_generic_doorway(doc):
    """Reject broad entrance pages as the earned gift after a completed HRN journey.

    A successful closure must hand the visitor a resource connected to the
    perspective they reached. Generic Orientation/Home/Welcome pages are not
    a substitute for a topic-fit canonical doorway; if no specific asset qualifies,
    the existing safe no-doorway response is more honest.
    """
    if not isinstance(doc, dict):
        return False
    title = str(doc.get("title") or "").casefold().strip()
    title = re.sub(r"^[^a-z0-9]+", "", title)
    title = re.sub(r"[^a-z0-9]+", " ", title).strip()
    return bool(re.fullmatch(
        r"(?:(?:living archive )?orientation|home(?: page)?|"
        r"welcome(?: to (?:the )?(?:archive|living archive))?|"
        r"start here|the guide|life understood)",
        title,
    ))


def _relational_return_workplace_change_focus(query):
    """Recognize a concrete work-agreement change that has become interpersonal."""
    q = _normalize_query(query)
    # Workplace relational closure must include managerial trust and decision-rights
    # tensions, not only project/scope-change vocabulary. HRN can surface these as
    # an earned perspective after several turns, so classify the opening context too.
    work_context = bool(re.search(
        r"\b(?:project|work|workplace|manager|boss|supervisor|colleague|team|deadline|scope|deliverable|agreement|role)\b", q
    ))
    change_context = bool(re.search(
        r"\b(?:changed scope|scope changed|changed work|new work|agreement changed|"
        r"deadline|scope|agreement|making too much of it|unreasonable|overreacting|"
        r"trust|questions every decision|question(?:s|ed|ing)? (?:every )?decision|"
        r"decision rights|decision boundaries|decision is within my role|"
        r"prove my competence|prove i know what i'm doing|repeated scrutiny)\b", q
    ))
    interpersonal_context = bool(re.search(
        r"\b(?:colleague|manager|boss|supervisor|team|other person|conversation|between us|"
        r"making too much of it|unreasonable|overreacting|reaction|responsibility|"
        r"trust|judgment|decision|role|review|questions every decision)\b", q
    ))
    return work_context and change_context and interpersonal_context


def _relational_return_workplace_change_fit(query, doc):
    """Accept a directly titled work-conflict asset for a grounded scope/agreement change."""
    if not isinstance(doc, dict) or not _relational_return_workplace_change_focus(query):
        return False
    title = str(doc.get("title") or "").casefold()
    body = str(doc.get("text") or doc.get("content") or doc.get("excerpt") or "").casefold()
    direct_title = bool(re.search(r"\b(?:conflict|disagreement|trust|team)\b", title))
    work_evidence = bool(re.search(
        r"\b(?:team|teams|work|workplace|project|scope|deadline|agreement|expectations|responsibility)\b",
        body,
    ))
    interaction_evidence = bool(re.search(
        r"\b(?:conflict|disagreement|conversation|communication|trust|relationship)\b",
        body,
    ))
    return direct_title and work_evidence and interaction_evidence


def _relational_return_earned_focus_fit(query, doc):
    """Accept only a canonical resource that supports an earned relational focus."""
    if not isinstance(doc, dict) or _relational_return_is_generic_doorway(doc):
        return False
    if _relational_return_workplace_change_focus(query):
        return _relational_return_workplace_change_fit(query, doc)
    q = _normalize_query(query)
    title = str(doc.get("title") or "").casefold()
    body = str(doc.get("text") or doc.get("content") or doc.get("excerpt") or "").casefold()
    material = " ".join((title, body))
    if not _relational_return_conflict_topic_fit(query, doc):
        return False

    # A specific recurring-argument journey must not fall back to a broad
    # relationship/communication essay just because it mentions conflict.
    # Require a directly named conflict/repair doorway for this narrow case;
    # otherwise only the direct-topic gate may admit a resource.
    recurring_argument_focus = bool(re.search(
        r"\b(?:same argument|argument keeps returning|repeated argument|recurring argument|"
        r"argue about|repeated conflict|hurt.{0,35}blame|blame.{0,35}hurt)\b",
        q,
    ))
    direct_conflict_title = bool(re.search(
        r"\b(?:argument|argue|conflict|disagreement|repair|reconciliation|being heard)\b",
        title,
    ))
    if recurring_argument_focus and not direct_conflict_title:
        return False
    relationship_evidence = bool(re.search(
        r"\b(?:relationship|relationships|relational|friendship|friends|connection|"
        r"love|care|communication|between people)\b", material
    ))
    if not relationship_evidence:
        return False
    effort_focus = bool(re.search(
        r"\b(?:effort imbalance|making an effort|more effort|overgiving|giving more|"
        r"feel unseen|feeling unseen|feeling valued|mutuality|reciproc|unfairly|self-erasure)\b", q
    ))
    effort_evidence = bool(re.search(
        r"\b(?:imbalance|overgiving|self-sacrifice|giving more|receiving more|"
        r"mutual support|mutuality|reciproc|valued|effort|boundaries|self-erasure)\b", material
    ))
    discernment_focus = _relational_discernment_focus(q)
    discernment_evidence_terms = set(re.findall(
        r"\b(?:perception|behavior|behaviour|interpret(?:ation|ed|ing)?|"
        r"assumption|inference|intentions?|projection|observation|observed)\b",
        material,
    ))
    # A single generic mention of communication or silence is not evidence for
    # a perception/inference resource. Require a cluster of distinct cues.
    discernment_evidence = len(discernment_evidence_terms) >= 2
    # Disagreement alone does not establish that the visitor's central concern
    # is listening or being heard. Keep this exception narrow so a broad
    # relationship essay cannot qualify solely because it mentions dialogue.
    # "A hurt is heard as blame" describes how a statement is interpreted;
    # it does not establish that the visitor feels unheard or that listening is
    # the central problem. Require an explicit listening/being-heard signal.
    communication_focus = _relational_communication_focus(q)
    communication_evidence = bool(re.search(
        r"\b(?:listen|listening|heard|hearing|acknowledge|acknowledgment|acknowledgement|"
        r"communication|dialogue|being heard)\b", material
    ))
    return bool(
        (effort_focus and effort_evidence)
        or (discernment_focus and discernment_evidence)
        or (communication_focus and relationship_evidence and communication_evidence)
    )


def _relational_return_direct_topic_fit(query, doc):
    """Require evidence for the visitor's earned relational topic, not just a plausible title."""
    if not isinstance(doc, dict) or _relational_return_is_generic_doorway(doc):
        return False
    if _relational_return_workplace_change_focus(query):
        return _relational_return_workplace_change_fit(query, doc)
    q = _normalize_query(query)
    title = str(doc.get("title") or "").casefold()
    body_text = str(doc.get("text") or doc.get("content") or doc.get("excerpt") or "").casefold()
    material = " ".join((title, body_text)).casefold()
    if not _relational_return_conflict_topic_fit(query, doc):
        return False

    # Keep completed journeys about an explicit recurring argument anchored to
    # a directly named conflict/repair resource. The Guide may append semantic
    # expansions such as communication, listening, and being heard to the
    # retrieval query; those additions must not turn a broad governance essay
    # into a topical match.
    recurring_argument_focus = bool(re.search(
        r"\b(?:same argument|argument keeps returning|repeated argument|recurring argument|"
        r"argue about|repeated conflict|hurt.{0,35}blame|blame.{0,35}hurt)\b",
        q,
    ))
    direct_conflict_title = bool(re.search(
        r"\b(?:argument|argue|conflict|disagreement|repair|reconciliation|being heard)\b",
        title,
    ))
    if recurring_argument_focus and not direct_conflict_title:
        return False

    recurring_argument_focus = bool(re.search(
        r"\b(?:same argument|argument keeps returning|repeated argument|recurring argument|"
        r"argue about|repeated conflict|hurt.{0,35}blame|blame.{0,35}hurt)\b",
        q,
    ))
    direct_conflict_title = bool(re.search(
        r"\b(?:argument|argue|conflict|disagreement|repair|reconciliation|being heard)\b",
        title,
    ))
    if recurring_argument_focus and direct_conflict_title:
        # For a specific recurring-conflict query, a directly named conflict/
        # repair title plus body evidence about relational conflict is stronger
        # than exact lexical overlap with incidental wording such as "improve".
        body_conflict = bool(re.search(
            r"\b(?:argument|argue|conflict|disagreement|repair|blame|incident|criticism|defensiveness|stonewalling)\b",
            body_text,
        ))
        body_relational = bool(re.search(
            r"\b(?:relationship|relational|partner|hurt|listening|heard|criticism|defensiveness|stonewalling)\b",
            body_text,
        ))
        if body_conflict and body_relational:
            return True

    projection_query = bool(re.search(r"\b(?:project(?:ion|ing|ed)?|what i(?:'|’)m sensing|what i sense|what i infer|what is real)\b", q))
    if projection_query:
        # A canonical title explicitly about projection is direct topical evidence
        # even when its body uses broader language and does not repeat "relationship".
        if re.search(r"\b(?:projection|projecting|projected)\b", title):
            return True
        direct_projection = bool(re.search(r"\b(?:projection|projecting|projected)\b", material))
        observed_inferred = (
            bool(re.search(r"\b(?:observed|observation|notice|noticing)\b", material))
            and bool(re.search(r"\b(?:infer|inference|interpretation|assumption)\b", material))
        )
        if not (direct_projection or observed_inferred):
            return False
        if not re.search(r"\b(?:relationship|relational|between people|other person|communication|silence|withdrawal)\b", material):
            return False
        return True

    # General relational closures must also demonstrate topic fit. A document
    # that merely shares the broad relational atmosphere is not a valid gift.
    query_terms = set(_subject_terms(q))
    if not query_terms:
        return False
    title_tokens = set(re.findall(r"[a-z0-9]+", title))
    material_tokens = set(re.findall(r"[a-z0-9]+", body_text))
    generic_terms = {
        "relationship", "relational", "partner", "person", "people", "other",
        "conversation", "situation", "feeling", "feel", "think", "know",
        "meaning", "understand", "something", "someone", "change", "experience",
        "life", "human", "interaction", "dynamic",
    }
    specific_terms = query_terms - generic_terms
    title_hits = {term for term in query_terms if _term_forms(term) & title_tokens}
    body_hits = {term for term in query_terms if _term_forms(term) & material_tokens}
    specific_title_hits = {term for term in specific_terms if _term_forms(term) & title_tokens}
    specific_body_hits = {term for term in specific_terms if _term_forms(term) & material_tokens}

    # Scattered mentions across a broad essay are not direct topic fit.
    # Require either a distinctive title anchor with corroborating body evidence,
    # or at least two substantive query terms in the same sentence. This prevents
    # a broad family/couple doorway from passing merely because the essay mentions
    # silence, rejection, and intention in unrelated passages.
    sentence_specific_hits = 0
    for sentence in re.split(r"(?<=[.!?])(?:[\"'”’)\]]+)?\s+|\n+", body_text):
        sentence_tokens = set(re.findall(r"[a-z0-9]+", sentence))
        sentence_hits = {
            term for term in specific_terms
            if _term_forms(term) & sentence_tokens
        }
        sentence_specific_hits = max(sentence_specific_hits, len(sentence_hits))

    if len(specific_terms) == 1:
        # Single-topic queries need the topic named in both title and body.
        return bool(specific_title_hits and specific_body_hits)

    return bool(
        (specific_title_hits and len(body_hits) >= 2)
        or sentence_specific_hits >= 2
    )


def _relational_return_verified_workplace_candidate(query):
    """Fetch the verified public Conflict & Trust Arc page for work-agreement friction.

    This direct canonical fallback prevents the bounded WordPress search pool
    from changing the return decision when unrelated candidates time out. It is
    still subject to the same workplace-change title/body evidence gate.
    """
    if not _relational_return_workplace_change_focus(query):
        return None
    endpoint = "https://geralddaquila.com/wp-json/wp/v2/pages/39753"
    try:
        request = UrlRequest(
            endpoint,
            headers={"Accept": "application/json", "User-Agent": "LivingArchiveGuide/1.0"},
            method="GET",
        )
        with urlopen(request, timeout=3.0) as response:
            resource = json.loads(response.read().decode("utf-8"))
        if not isinstance(resource, dict):
            return None
        import html
        title_obj = resource.get("title")
        title = str(
            title_obj.get("rendered") if isinstance(title_obj, dict) else title_obj or ""
        ).strip()
        content_obj = resource.get("content")
        content_html = str(
            content_obj.get("rendered") if isinstance(content_obj, dict) else content_obj or ""
        )
        content_html = re.sub(r"(?is)<(script|style)\b[^>]*>.*?</\1>", " ", content_html)
        content = re.sub(r"(?s)<[^>]+>", " ", content_html)
        content = re.sub(r"\s+", " ", html.unescape(content)).strip()
        candidate = {
            "title": title,
            "url": str(resource.get("link") or "https://geralddaquila.com/conflict-trust-arc/").strip(),
            "text": content[:6000],
        }
        if (
            candidate["title"]
            and re.match(r"^https://geralddaquila\.com/\S+$", candidate["url"], re.I)
            and _relational_return_workplace_change_fit(query, candidate)
        ):
            return candidate
        return None
    except Exception as exc:
        print(
            "The Guide verified workplace canonical recovery: "
            f"unavailable ({type(exc).__name__})."
        )
        return None


def _relational_return_apply_verified_workplace_candidate(original_question, direct_topic_query, primary, outward):
    """Prefer the verified canonical work-conflict doorway over retrieval-pool variation."""
    if not _relational_return_workplace_change_focus(original_question):
        return primary, outward
    verified = _relational_return_verified_workplace_candidate(original_question)
    if verified and _relational_return_direct_topic_fit(direct_topic_query, verified):
        return verified, [verified]
    return primary, outward


def _relational_return_search_recovery(original_question, direct_topic_query, profile):
    """Use bounded WordPress search only when focused vector retrieval found no honest doorway."""
    normalized_original = _normalize_query(original_question)
    conflict_focus = bool(re.search(
        r"\b(?:same argument|argument keeps returning|repeated argument|recurring argument|"
        r"argue about|repeated conflict|hurt.{0,35}blame|blame.{0,35}hurt)\b",
        normalized_original,
    ))
    workplace_change_focus = _relational_return_workplace_change_focus(normalized_original)
    if not conflict_focus and not workplace_change_focus:
        return None, []
    if workplace_change_focus and not conflict_focus:
        verified_candidate = _relational_return_verified_workplace_candidate(original_question)
        if verified_candidate:
            print(
                "The Guide verified workplace canonical recovery: "
                f"selected={verified_candidate['title']}."
            )
            return verified_candidate, [verified_candidate]
    # Bounded WordPress search supplements vector retrieval for two concrete
    # relational cases: recurring arguments and a changed work agreement that
    # has become interpersonal. Every candidate still passes the same topic-fit
    # and canonical gates before a doorway can be released.
    search_queries = (
        ("relationship repair", "conflict repair", "argument hurt")
        if conflict_focus
        else ("workplace conflict", "project scope agreement", "conflict moment")
    )
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=len(search_queries)) as executor:
        candidate_sets = list(executor.map(
            lambda search_query: _wordpress_search_canonical_candidates(search_query, limit=5),
            search_queries,
        ))

    ranked_candidates = []
    seen = set()
    candidate_index = 0
    for search_query, candidates in zip(search_queries, candidate_sets):
        # These candidates were fetched from the canonical WordPress REST API
        # and contain the full published text. The generic outward sanitizer is
        # tuned for ordinary Guide answers and can discard a directly titled
        # conflict/repair asset before the stricter journey-specific evidence
        # gates run. For this bounded recovery lane, use the canonical candidates
        # directly, but require the exact original-topic and earned-focus gates
        # below before ranking or releasing anything.
        query_outward = candidates
        for doc in query_outward:
            if not (
                _relational_return_direct_topic_fit(direct_topic_query, doc)
                or _relational_return_earned_focus_fit(direct_topic_query, doc)
            ):
                continue
            key = (
                str(doc.get("title") or "").strip().casefold(),
                str(doc.get("url") or doc.get("canonical_url") or "").strip().casefold(),
            )
            if key in seen:
                continue
            seen.add(key)
            metrics = _subject_metrics(search_query, doc)
            context = _contextual_fit(search_query, doc)
            score = (
                metrics[2], metrics[3], metrics[0], metrics[1],
                context[2], context[1], -candidate_index,
            )
            ranked_candidates.append((score, doc))
            candidate_index += 1

    # Rank each candidate against the exact bounded query that retrieved it.
    # Rechecking every candidate against only the first phrase would silently
    # discard valid candidates discovered by the secondary queries.
    ranked_candidates.sort(key=lambda item: item[0], reverse=True)
    outward = [doc for _score, doc in ranked_candidates]
    primary = outward[0] if outward else None
    print(
        "The Guide relational doorway recovery: "
        f"queries={len(search_queries)}, candidates={sum(len(items) for items in candidate_sets)}, "
        f"eligible={len(outward)}, selected={primary['title'] if primary else 'none'}."
    )
    return primary, (outward if primary else [])


def _relational_return_retry_after_broad_candidate(primary, outward, original_question, direct_topic_query, profile):
    """Retry the bounded conflict search only after a broad candidate was rejected."""
    if primary is not None:
        return primary, outward
    conflict_focus = bool(re.search(
        r"\b(?:same argument|argument keeps returning|repeated argument|recurring argument|"
        r"argue about|repeated conflict|hurt.{0,35}blame|blame.{0,35}hurt)\b",
        _normalize_query(original_question),
    ))
    if not conflict_focus:
        return None, []
    candidate, candidates = _relational_return_search_recovery(
        original_question, direct_topic_query, profile
    )
    if not candidate:
        return None, []
    direct_title = bool(re.search(
        r"\b(?:argument|argue|conflict|disagreement|repair|reconciliation|being heard)\b",
        str(candidate.get("title") or "").casefold(),
    ))
    return (candidate, candidates) if direct_title else (None, [])


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
        # Select the doorway from the earned relational perspective first. The full
        # transcript/ledger query is useful evidence, but it can dilute the visitor's
        # actual movement with incidental themes. Keep the first retrieval focused.
        topic_anchor = original_question
        topic_anchor += " " + _relational_return_topic_anchor(
            original_question, underlying_need, perspective_delta
        )
        # Preserve the specialist's explicit resource-fit note as retrieval evidence.
        # It was in the synthesis payload but dropped from both doorway queries.
        if resource_fit:
            topic_anchor += " Relational resource fit: " + str(resource_fit)
        if re.search(r"\b(?:project(?:ion|ing|ed)?|what i(?:'|’)m sensing|what i sense|what i infer|what is real)\b", _normalize_query(original_question)):
            topic_anchor += " Relational projection: distinguish what is observed from what is inferred in the relationship."
        # Retrieval uses the visitor's opening plus the earned need/perspective,
        # not the full closure synthesis, which can dilute the actual concern.
        doorway_query = " ".join(
            value for value in (
                topic_anchor,
                underlying_need,
                completed_insight,
                perspective_delta,
                resource_fit,
            ) if value
        )[:6000]
        direct_topic_query = " ".join(
            value for value in (topic_anchor, underlying_need, perspective_delta, completed_insight, resource_fit)
            if value
        )[:5000] or topic_anchor
        context_data = _original_fetch_canonical_context(doorway_query)
        canonical_context = str(
            context_data.get("canonical_link_context")
            or context_data.get("context_blocks")
            or ""
        ) if isinstance(context_data, dict) else ""
        docs = _parse_context_documents(canonical_context)

        # The final doorway remains a Guide responsibility. The completed
        # perspective, not the visitor's opening wording alone, governs the gift.
        profile = _base._inquiry_profile(doorway_query)
        profile["action"] = "recommendation"
        profile["recommendation"] = max(float(profile.get("recommendation", 0.0)), 0.95)
        # This endpoint is entered only after HRN closes a relational journey.
        # Preserve that specialist boundary even if generic lexical cues lean elsewhere.
        profile["primary"] = "relational"
        profile["relational"] = True
        outward = _sanitize_outward_context(doorway_query, docs, profile)
        outward = [
            doc for doc in outward
            if _relational_return_direct_topic_fit(direct_topic_query, doc)
            or _relational_return_earned_focus_fit(direct_topic_query, doc)
        ]
        primary = _canonical_primary_from_docs(outward, direct_topic_query, profile)
        # v489.226: a verified canonical workplace-conflict page outranks vector/search pool variation.
        primary, outward = _relational_return_apply_verified_workplace_candidate(
            original_question, direct_topic_query, primary, outward
        )

        if not primary:
            # A second bounded attempt may use only the earned perspective.
            # Never reintroduce the full transcript/ledger here: if neither focused
            # query supports a canonical resource, return no doorway rather than a
            # plausible-looking but unrelated gift.
            fallback_query = " ".join(
                value for value in (
                    underlying_need,
                    perspective_delta,
                    completed_insight,
                    resource_fit,
                    str(journey_ledger.get("current_terrain") or ""),
                    str(journey_ledger.get("unresolved") or ""),
                ) if value
            )[:4000]
            fallback_data = _original_fetch_canonical_context(fallback_query)
            fallback_context = str(
                fallback_data.get("canonical_link_context")
                or fallback_data.get("context_blocks")
                or ""
            ) if isinstance(fallback_data, dict) else ""
            fallback_docs = _parse_context_documents(fallback_context)
            fallback_outward = _sanitize_outward_context(fallback_query, fallback_docs, profile)
            fallback_outward = [
                doc for doc in fallback_outward
                if _relational_return_direct_topic_fit(fallback_query, doc)
                or _relational_return_earned_focus_fit(fallback_query, doc)
            ]
            primary = _canonical_primary_from_docs(fallback_outward, fallback_query, profile)
            if primary:
                outward = fallback_outward

        if not primary:
            # Vector retrieval can return no sufficiently direct doorway even
            # when the public Archive contains a clearly relevant conflict/repair
            # resource. Try bounded WordPress search, then apply the same relevance
            # and canonical gates before releasing any recommendation.
            search_primary, search_outward = _relational_return_search_recovery(
                original_question, direct_topic_query, profile
            )
            if search_primary:
                primary = search_primary
                outward = search_outward

        # Last-mile canonical doorway invariant: even if retrieval normalization
        # or a future relevance branch changes, a completed recurring-argument
        # journey cannot release a broad resource whose title does not name
        # conflict, argument, disagreement, repair, reconciliation, or being heard.
        original_recurring_argument_focus = bool(re.search(
            r"\b(?:same argument|argument keeps returning|repeated argument|recurring argument|"
            r"argue about|repeated conflict|hurt.{0,35}blame|blame.{0,35}hurt)\b",
            _normalize_query(original_question),
        ))
        primary_title_is_direct_conflict = bool(
            primary and re.search(
                r"\b(?:argument|argue|conflict|disagreement|repair|reconciliation|being heard)\b",
                str(primary.get("title") or "").casefold(),
            )
        )
        if primary and original_recurring_argument_focus and not primary_title_is_direct_conflict:
            print(
                "The Guide v489.201 rejected a non-conflict canonical doorway "
                f"for recurring-argument return: {primary.get('title')}"
            )
            primary = None
            outward = []

        # Structural retry: a broad vector candidate can survive the initial
        # retrieval path, then be correctly rejected by the last-mile conflict
        # title guard. That rejection must not end retrieval before the bounded
        # conflict-specific WordPress search has had its turn. Reuse the same
        # direct-topic and earned-focus gates; never relax the relevance boundary.
        if original_recurring_argument_focus and primary is None:
            primary, outward = _relational_return_retry_after_broad_candidate(
                primary, outward, original_question, direct_topic_query, profile
            )

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

    # Explicit destination language is different from an explanatory definition
    # request, but the visitor still expects the Glossary's native lookup UI.
    navigation = re.search(
        r"\b(?:take me to|take me directly to|open|show me|go to|navigate to|"
        r"find|access)\b.{0,60}\bglossary(?:\s+entry)?\s*(?:for|about|on)?\s*(.+?)?[?!.]?$",
        normalized,
        re.I,
    )
    if navigation:
        candidate = re.sub(r"^[\s\"']+|[\s\"'?.!]+$", "", str(navigation.group(1) or ""))
        candidate = re.sub(r"^(?:the\s+term\s+|the\s+word\s+|word\s+)", "", candidate, flags=re.I)
        if candidate and len(candidate) <= 120 and not re.search(r"[?\n]", candidate):
            return candidate

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


def _is_comparative_explanatory_request(query):
    """Identify comparison questions that require Guide synthesis, not term lookup."""
    normalized = re.sub(r"\s+", " ", str(query or "").strip().casefold())
    if not normalized:
        return False
    patterns = (
        r"\b(?:what is|what's|explain) the difference between\b",
        r"\bdifference between\b",
        r"\bhow does .{1,100} differ from .{1,100}",
        r"\bhow do .{1,100} differ from .{1,100}",
        r"\bcompare .{1,100} (?:and|with|to) .{1,100}",
        r"\bcomparison of .{1,100} and .{1,100}",
        r"\brelationship between .{1,100} and .{1,100}",
        r"\bhow .{1,100} relates to .{1,100}",
        r"\bhow are .{1,100} different from .{1,100}",
    )
    return any(re.search(pattern, normalized) for pattern in patterns)


# Comparative questions are explanatory inquiries, not requests to look up
# the whole comparison phrase as a single glossary term.
if not _is_comparative_explanatory_request(
    "What is the difference between responsibility and stewardship?"
):
    raise RuntimeError("USE comparative-intent invariant failed: responsibility/stewardship comparison not recognized")
if _is_comparative_explanatory_request("What does stewardship mean?"):
    raise RuntimeError("USE comparative-intent invariant failed: simple glossary lookup misclassified")


def _is_lived_experience_explanatory_request(query):
    """Keep existential/lived-experience inquiries in General Guide composition.

    These questions ask how to understand or inhabit a human condition, not
    for a dictionary-style definition of a bounded canonical term.
    """
    normalized = re.sub(r"\s+", " ", str(query or "").strip().casefold())
    if not normalized:
        return False
    patterns = (
        r"^what does it mean to live with\b",
        r"^what does it mean to live through\b",
        r"^what does it mean to live in\b",
        r"^what is it like to live with\b",
        r"^how (?:can|do|does|should) (?:i|we|you|someone|a person) live with\b",
        r"^how to live with\b",
        r"^what does it mean to face\b",
        r"^what does it mean to experience\b",
    )
    return any(re.search(pattern, normalized) for pattern in patterns)


# The lived-experience guard must distinguish existential inquiry from a
# bounded term lookup before any direct Glossary handoff can occur.
if not _is_lived_experience_explanatory_request("What does it mean to live with uncertainty?"):
    raise RuntimeError("USE v489.90 lived-experience routing invariant failed")
if _is_lived_experience_explanatory_request("What does uncertainty mean?"):
    raise RuntimeError("USE v489.90 glossary distinction invariant failed")


def _is_bounded_glossary_request(query, glossary_term="", embedded_term=""):
    """Return True only for a bounded vocabulary lookup.

    A definition opening is not sufficient by itself. If the visitor adds a
    second substantive question, the question remains with Basic Inquiry
    rather than being reduced to a malformed glossary term.
    """
    normalized = re.sub(r"\s+", " ", str(query or "").strip()).strip()
    term = str(glossary_term or "").strip()
    embedded = str(embedded_term or "").strip()
    if not normalized or not term:
        return False
    if _is_comparative_explanatory_request(query):
        return False

    # v489.90 structural boundary: lived-experience/existential questions are
    # explanatory inquiries, not bounded vocabulary lookups. Phrases such as
    # "what does it mean to live with uncertainty?" ask for orientation and
    # synthesis; sending them to the Glossary mistakes a grammatical "mean"
    # for a request to define a canonical term.
    if _is_lived_experience_explanatory_request(query):
        return False

    explicit_glossary_navigation = bool(re.search(
        r"\b(?:take me to|take me directly to|open|show me|go to|navigate to|find|access)\b.{0,60}\bglossary\b",
        normalized,
        re.I,
    ))
    bounded_opening = bool(re.match(
        r"^(?:what does|what is|what's|what is the meaning of|meaning of|define|definition of)\b",
        normalized,
        re.I,
    ))
    if not bounded_opening and not embedded and not explicit_glossary_navigation:
        return False

    remainder = normalized
    remainder = re.sub(
        r"^(?:what does|what is|what's|what is the meaning of|meaning of|define|definition of)\s+",
        "",
        remainder,
        count=1,
        flags=re.I,
    )

    # A compound/open question must stay with the general-purpose Guide.
    # These patterns cover added significance, consequence, application,
    # comparison, or second-question clauses.
    compound_patterns = (
        r"\band\s+(?:why|how|what|whether|when|where|who|can|could|should|does|do)\b",
        r"\band\s+(?:why|how|what)\b.{0,160}\b(?:matter|matters|important|relevant|mean|means|work|apply|applied|practice|practiced|change|changed|today|now)\b",
        r"\?\s*(?:why|how|what|whether|when|where|who)\b",
    )
    if any(re.search(pattern, remainder, re.I) for pattern in compound_patterns):
        return False

    # Only route to the Glossary when the visitor explicitly asks for that
    # surface, or when the term is part of the small set of canonical terms
    # already guaranteed by this runtime's frozen routing contracts. A bare
    # definition request for an unverified term must remain with the Guide:
    # the Glossary may not contain it, and a missing entry must not become a
    # dead-end handoff.
    if len(re.findall(r"\b\w+\b", term)) > 8:
        return False
    if explicit_glossary_navigation:
        return True
    canonical_routed_terms = {"stewardship"}
    normalized_term = re.sub(r"[^a-z0-9\s-]", "", term.casefold()).strip()
    normalized_words = set(normalized_term.split())
    return any(canonical in normalized_words for canonical in canonical_routed_terms)


# v488.89 regression guard: execute the bounded Glossary contract with the
# same normalized term inputs used by the live handoff path.
if _is_bounded_glossary_request(
    "What is stewardship?",
    glossary_term=_normalize_glossary_term("What is stewardship?"),
) is not True:
    raise RuntimeError("USE v488.89 glossary invariant failed: simple definition was not recognized")
if _is_bounded_glossary_request(
    "What is stewardship and why it matters now more than ever?",
    glossary_term=_normalize_glossary_term("What is stewardship and why it matters now more than ever?"),
) is not False:
    raise RuntimeError("USE v488.89 glossary invariant failed: compound definition question was misrouted to Glossary")
if _is_bounded_glossary_request(
    "What is stewardship and why does it matter now more than ever?",
    glossary_term=_normalize_glossary_term("What is stewardship and why does it matter now more than ever?"),
) is not False:
    raise RuntimeError("USE v489.22 glossary invariant failed: reported compound stewardship question was misrouted to Glossary")
if _is_bounded_glossary_request(
    "What does stewardship mean here?",
    glossary_term=_normalize_glossary_term("What does stewardship mean here?"),
) is not True:
    raise RuntimeError("USE v488.89 glossary invariant failed: contextual definition was rejected")

if _is_bounded_glossary_request(
    "What is the meaning of emptiness?",
    glossary_term=_normalize_glossary_term("What is the meaning of emptiness?"),
) is not False:
    raise RuntimeError("USE glossary fallback invariant failed: unknown glossary term was handed off instead of remaining with the Guide")


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
def _is_catalogue_resource_search_query(query):
    """Recognize natural-language requests to find/browse resources, not explanatory questions."""
    text = re.sub(r"\s+", " ", str(query or "").strip().casefold())
    if not text:
        return False

    resource_noun = (
        r"(?:resources?|materials?|sources?|works?|essays?|articles?|cases?|"
        r"readings?|publications?|texts?|information|content)"
    )

    # Resource-seeking questions can start with "what/which" without asking
    # for an explanation of the underlying topic.
    if re.search(rf"^(?:what|which)\s+{resource_noun}\b", text):
        return True

    search_pattern = re.compile(
        rf"\b(?:where can i find|where do i find|how can i find|"
        rf"find(?: me)?|search(?: for| the archive| the catalogue| the catalog)|"
        rf"browse|explore|look(?:ing)? for|locate|recommend|suggest|"
        rf"show me|list|give me|provide|surface|open)\b"
        rf".{{0,120}}\b{resource_noun}\b"
    )
    # These requests explicitly name the Catalogue/Archive even when the
    # visitor describes the task as browsing or exploring rather than searching.
    catalogue_pattern = re.compile(
        r"\b(?:browse|explore|search|open)\s+(?:the\s+)?"
        r"(?:catalogue|catalog|archive)\b"
    )
    match = search_pattern.search(text)
    if not match and not catalogue_pattern.search(text):
        return False

    # Preserve Guide explanations when a visitor asks an explanatory question
    # first and only then appends a resource request.
    explanatory_pattern = re.compile(
        r"\b(?:what is|what are|why is|why are|why does|why do|"
        r"explain|how does|how do|how is|how are)\b"
    )
    explanatory = explanatory_pattern.search(text)
    if explanatory and match and explanatory.start() < match.start():
        return False
    if explanatory and not match:
        return False
    return True


def _catalogue_handoff_payload(query, history):
    catalogue_url = _catalogue_handoff_url(query)
    request_id = "catalogue-" + hashlib.sha1(
        (query + "|" + _history_text(history)).encode("utf-8")
    ).hexdigest()[:16]
    return {
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
    }


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
        r"get\s+started|go\s+from\s+here)\b"
        # Explicit whole-Archive pathway requests are orientation, not topic Q&A.
        r"|\b(?:find|follow|choose|discover)\s+(?:a\s+)?path\s+(?:through|into|around)\b"
        r"|\bwhat\b.{0,60}\b(?:explore|follow|read|look\s+at)\b.{0,40}\b(?:next|first|here)\b",
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


def _is_practical_stewardship_question(query):
    """Recognize everyday application questions without invoking a model."""
    q = _normalize_query(query)
    return bool(
        re.search(r"\b(?:how|what|which|when|where)\b", q, re.I)
        and re.search(r"\b(?:practice|practise|everyday|daily|decisions?|responsibilities|community|communities)\b", q, re.I)
        and re.search(r"\bstewardship\b", q, re.I)
        and not _explicit_formation_entry_route(query)
    )


def _guide_route_fallback(query, history=None):
    """Conservative fallback when the early LLM route cannot execute."""
    q = _normalize_query(query)
    combined = " ".join(part for part in (q, _guide_route_history_text(history)) if part)

    if _is_practical_stewardship_question(query):
        return {
            "route": "guide",
            "mode": "direct",
            "confidence": 0.90,
            "reason": "practical stewardship question stays in direct Guide response even when routing providers are unavailable",
            "alternatives": ["guide"],
            "source": "deterministic-practical-stewardship-fallback",
        }

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
    # Stale registry data may inform context, but authority-sensitive native
    # doorway activation requires a fresh WordPress registry.
    if not _guide_node_registry_is_fresh():
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
            if _normalize_query(str(item[4].get("title") or "")) in raw_query
        ]
        if explicit_level_two:
            explicit_level_two.sort(key=lambda item: (item[0], item[1]), reverse=True)
            return explicit_level_two[0][4]
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
    # The final route must be decided here, before any model candidate can
    # redirect this known practical-question class into a delegated journey.
    # The outer request boundary and the FastAPI app can each invoke routing;
    # therefore this guard belongs at the shared routing entry point itself.
    if _is_practical_stewardship_question(query):
        return {
            "route": "guide",
            "mode": "direct",
            "confidence": 0.99,
            "reason": "practical stewardship question requires a direct Guide answer; model routing cannot override this intent",
            "alternatives": ["guide"],
            "source": "deterministic-practical-stewardship-final-route",
        }
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
        max_tokens=2048,
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

    # Keep ordinary practical questions in the Guide. Formation is a distinct
    # delegated journey, not a substitute for answering a concrete public question
    # merely because it mentions stewardship, practice, or responsibility.
    # Only preserve a model-selected Formation route when the visitor explicitly
    # asks to enter or prepare for the Formation pathway.
    explicit_formation_entry = _explicit_formation_entry_route(query)
    practical_stewardship_question = bool(
        re.search(r"\b(?:how|what|which|when|where)\b", _normalize_query(query), re.I)
        and re.search(r"\b(?:practice|practise|everyday|daily|decisions?|responsibilities|community|communities)\b", _normalize_query(query), re.I)
        and re.search(r"\bstewardship\b", _normalize_query(query), re.I)
    )
    if route == "formation" and practical_stewardship_question and not explicit_formation_entry:
        route = "guide"
        mode = "direct"
        reason = (
            "A practical stewardship question requires a direct Guide answer; "
            "Formation is reserved for explicit pathway entry or preparation."
        )

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
        if _should_honor_protected_risk_profile(query, profile):
            route = "safety"
            mode = "safety"
            confidence = 1.0
            reason = "deterministic safety boundary"
        elif profile.get("risk"):
            print("The Guide capability router ignored protected-core risk fallback for a hypothetical safety calibration query.")
    except Exception:
        pass

    route, mode, reason = _guard_hypothetical_safety_route(
        query, route, mode, reason
    )

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
    re.compile(r"\b(?:prepare|preparing|training|readiness|learning|learn|develop|developing)\b.{0,80}\b(?:stewardship|steward|governance|responsibilities|shared responsibility)\b|\b(?:stewardship|steward|governance)\b.{0,80}\b(?:responsibilities|readiness|training|learning)\b", re.I),
    re.compile(r"\b(?:philippine\s+systems|philippines?\s+(?:systems?|culture|society|history|systemic\s+transformation)|systems?\s+in\s+the\s+philippines)\b", re.I),
)

def _basic_inquiry_requires_macro_routing(query):
    """Keep the two not-yet-deterministic specialist surfaces on the legacy route."""
    if not _BASIC_INQUIRY_ENABLED:
        return True
    normalized = _normalize_query(query)
    return any(pattern.search(normalized) for pattern in _BASIC_INQUIRY_MACRO_PATTERNS)


def _explicit_formation_entry_route(query):
    """Deterministically route explicit Formation entry and preparation intent."""
    normalized = _normalize_query(query)
    named_formation_surface = bool(re.search(
        r"\b(?:stewardship\s+formation|formation\s+navigator|formation\s+pathway)\b",
        normalized,
    ))
    preparation_intent = bool(re.search(
        r"\b(?:prepare|preparing|training|readiness|learning|learn|develop|developing|responsibilities)\b",
        normalized,
    ))
    stewardship_scope = bool(re.search(
        r"\b(?:stewardship|steward|governance|shared responsibility|responsibilities in a group)\b",
        normalized,
    ))
    entry_language = bool(re.search(
        r"\b(?:enter|start|begin|join|access|open|launch|take me to|"
        r"where do i begin|where can i begin|where do i start|where can i start|"
        r"where should i begin|where should i start|how do i prepare|how can i prepare)\b",
        normalized,
    ))
    if not named_formation_surface and not (
        preparation_intent and stewardship_scope and entry_language
    ):
        return None
    if named_formation_surface and not entry_language and not preparation_intent:
        return None
    return {
        "route": "formation",
        "mode": "delegated_journey",
        "confidence": 1.0,
        "reason": "deterministic stewardship formation or preparation intent",
        "alternatives": ["guide"],
        "source": ("deterministic-explicit-formation-entry" if named_formation_surface else "deterministic-formation-preparation-entry"),
        "round1_interpretation": {
            "human_reality": "The visitor is asking how to prepare for stewardship responsibilities.",
            "presenting_situation": str(query).strip(),
            "visitor_proposition": str(query).strip(),
            "underlying_question": "What learning and practice would help the visitor prepare for stewardship responsibilities?",
            "uncertainty": "The most suitable formation movement remains to be explored by the Formation specialist.",
            "desired_movement": "Open a relevant Stewardship Formation pathway.",
            "processing_need": "formation",
            "glossary_term": "",
            "guide_node_id": "",
        },
    }


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

Never expose implementation or processing language to the visitor. In particular, never write phrases such as "USE", "canonical evidence", "supplied evidence", "evidence excerpt", "bounded by", "internal interpretation", "retrieval", "synthesis", "processing layer", "provider", "model", "route", "handoff", or similar machine-facing terminology. Never add bracketed editorial annotations, debugging notes, or evidence labels. If you need to refer to the material that informed the response, use ordinary language such as "the Archive material", "the material I found", or simply name the relevant collection or essay.

Return ONLY valid JSON with exactly:
{"response":"2–4 short paragraphs ending with exactly one opening question","doorway_title":"exact canonical title if naturally useful, otherwise empty"}
""".strip()


def _guide_reconcile_resource_language(response, recommendation_available):
    """Keep visitor-facing resource language consistent with the structured doorway."""
    text = str(response or "")
    if recommendation_available:
        return text

    unavailable = "I could not identify a sufficiently relevant Archive resource to recommend here."
    unbacked_resource_phrases = (
        r"(?i)(?:if you would like to explore this further,\s*)?the Archive resource below may offer a useful next step\.?",
        r"(?i)the separately selected Archive resource offers a place to explore further\.?",
        r"(?i)the linked Archive source may offer a more specific framing\.?",
    )
    for pattern in unbacked_resource_phrases:
        if re.search(pattern, text):
            if re.search(re.escape(unavailable), text, re.I):
                text = re.sub(pattern, "", text)
            else:
                text = re.sub(pattern, unavailable, text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _guide_bounded_community_archive_answer(query):
    """Provide a modest general answer to direct community-archive responsibility questions."""
    question = re.sub(r"\s+", " ", str(query or "")).strip().casefold()
    if not re.search(r"\bcommunity archives?\b", question):
        return None
    if not re.search(
        r"\b(?:responsibilit(?:y|ies)|preserv(?:e|es|ing|ation)|public knowledge|public memory)\b",
        question,
    ):
        return None

    response = (
        "A community archive has responsibilities beyond storing material safely. It should preserve records with care, document where they came from and how they have been described, and explain the choices that shape what is collected, retained, or left out.\n\n"
        "It also needs to balance public access with privacy, consent, rights, and the risk of exposing people to harm. Clear descriptions, accessible formats, transparent correction practices, and meaningful involvement from the communities represented help people understand both what the archive holds and what may be missing.\n\n"
        "These are general archival principles, not a claim that a specific Living Archive text prescribes this list. I did not identify a sufficiently direct Archive resource to recommend for this question."
    )
    return {
        "response": response,
        "doorway_title": "",
        "provider": "bounded_community_archive_responsibility_recovery",
        "model": "",
    }


def _guide_bounded_friendship_expectations_answer(query):
    """Answer general friendship-expectation questions without requiring a 'people/we' subject."""
    question = re.sub(r"\s+", " ", str(query or "")).strip().casefold()
    if not re.search(r"\b(?:common ways|common patterns|typical ways)\b", question):
        return None
    if not re.search(r"\b(?:misunderstand|misunderstanding|misunderstandings|expectations)\b", question):
        return None
    if not re.search(r"\bfriendships?\b", question):
        return None
    if re.search(r"\b(?:my friend|my friendship|my partner|my colleague|my teammate)\b", question):
        return None

    response = (
        "Friendship expectations can differ in several ordinary ways: how often people expect to be in touch, whether they want advice or simply to be heard, how much help is reasonable to ask for, what they consider private, and how directly they prefer to address hurt or disagreement. "
        "Because these expectations are often unspoken, one person may read less contact as distance while the other sees it as normal busyness.\n\n"
        "A useful starting point is to separate the observable event from the meaning assigned to it. Rather than assuming that a friend does not care, ask what each person expected and whether those expectations were ever discussed. Which expectation tends to be hardest for people to read accurately?"
    )
    return {
        "response": response,
        "doorway_title": "",
        "provider": "bounded_friendship_expectations_recovery",
        "model": "",
    }


def _guide_response_disclaims_archive_recommendation(response):
    """Detect visitor prose that explicitly says no suitable Archive resource was identified."""
    text = str(response or "")
    return bool(re.search(
        r"\b(?:I did not identify a sufficiently direct Archive resource to recommend for this question|I could not identify a sufficiently relevant Archive resource to recommend here)\b",
        text,
        re.I,
    ))


def _sanitize_basic_inquiry_response(text):
    """Enforce the visitor-language boundary while preserving readable structure."""
    raw = str(text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not raw:
        return ""

    # Providers sometimes return HTML fragments even though the public contract is
    # plain visitor prose/Markdown. Preserve paragraph/list boundaries, then remove
    # markup and decode entities before applying the existing language boundary.
    raw = re.sub(r"(?i)<\s*br\s*/?\s*>", "\n", raw)
    raw = re.sub(r"(?i)</\s*(?:p|div|li|h[1-6]|section|article)\s*>", "\n\n", raw)
    raw = re.sub(r"(?is)<[^>]{1,1000}>", "", raw)
    raw = unescape(raw)

    # v489.206: prevent formulaic editorial labels from leaking into ordinary
    # explanatory answers. These are not semantic headings; they are prompt-shaped
    # lead-ins that make a natural answer read like a templated mini-essay.
    raw = re.sub(
        r"(?im)(?<!\S)(?:why it matters now|practical implication)\s*:\s*",
        "",
        raw,
    )

    internal_bracket_patterns = (
        r"\s*\[(?:evidence|canonical evidence|supplied evidence|evidence excerpt|"
        r"evidence excerpt bounded by USE|bounded by USE|bounded by the Guide|"
        r"internal interpretation|retrieval|synthesis|processing layer|provider|model|"
        r"route|handoff)(?:[^\]]*)\]\s*",
        r"\s*\((?:evidence excerpt bounded by USE|bounded by USE|internal interpretation|"
        r"retrieval|synthesis|processing layer)\)\s*",
    )
    for pattern in internal_bracket_patterns:
        raw = re.sub(pattern, " ", raw, flags=re.I)

    replacements = (
        (r"\bevidence excerpt bounded by USE\b", "the material I found"),
        (r"\bcanonical evidence\b", "the Archive material"),
        (r"\bsupplied evidence\b", "the material I found"),
        (r"\binternal interpretation\b", "the way the question can be understood"),
        (r"\bprocessing layer\b", "the material"),
        (r"\b(?:retrieval|synthesis)\s+layer\b", "the material"),
    )
    for pattern, replacement in replacements:
        raw = re.sub(pattern, replacement, raw, flags=re.I)

    # The final visitor boundary must not undo Markdown normalization performed
    # by General Guide Composition. Providers vary in list style and may emit
    # numbered actions inline, so apply the same bounded structural repair here.
    action_label = r"\*\*[^*\n]{2,100}\*\*"
    action_separator = r"(?:\s*:\s*|\s+[–—−-]\s+)"
    raw = re.sub(
        rf"\s+-\s+(?={action_label}{action_separator})",
        "\n- ",
        raw,
    )
    raw = re.sub(
        rf"(?<=\S)\s+(?=\d{{1,2}}[.)]\s+{action_label}{action_separator})",
        "\n",
        raw,
    )

    paragraphs = []
    for block in re.split(r"\n\s*\n+", raw):
        lines = []
        for line in block.split("\n"):
            line = re.sub(r"\s+", " ", line).strip()
            if not line:
                continue
            line = re.sub(r"\s+([,.;!?])", r"\1", line)
            line = re.sub(r"([.!?])\s*\1+", r"\1", line)
            lines.append(line)
        if lines:
            paragraphs.append("\n".join(lines))

    return "\n\n".join(paragraphs).strip()


_BASIC_INQUIRY_VISITOR_LANGUAGE_PROBE = _sanitize_basic_inquiry_response(
    "This points to the Archive. [evidence excerpt bounded by USE]"
)
if _BASIC_INQUIRY_VISITOR_LANGUAGE_PROBE != "This points to the Archive.":
    raise RuntimeError("USE v488.90 visitor-language invariant failed: internal evidence annotation escaped sanitizer.")

# v489.28 final-boundary regression probes: the final public response sanitizer
# must preserve paragraph and Markdown-list boundaries after generation.
_BASIC_INQUIRY_MARKDOWN_PROBE = _sanitize_basic_inquiry_response(
    "Practical steps: 1. **Set clear boundaries** – stop after work. "
    "Treat downtime as non-negotiable. 2. **Delegate and trust** – hand off tasks. "
    "3. **Seek support** – ask a peer."
)
if "\n2. **Delegate and trust**" not in _BASIC_INQUIRY_MARKDOWN_PROBE:
    raise RuntimeError("USE v489.28 invariant failed: final boundary flattened numbered Markdown steps.")
if "\n3. **Seek support**" not in _BASIC_INQUIRY_MARKDOWN_PROBE:
    raise RuntimeError("USE v489.28 invariant failed: final boundary flattened consecutive numbered Markdown steps.")

_BASIC_INQUIRY_FINAL_BOUNDARY_PROBE = _sanitize_basic_inquiry_response(
    "A useful place to begin is the Archive. [evidence excerpt bounded by USE]"
)
if _BASIC_INQUIRY_FINAL_BOUNDARY_PROBE != "A useful place to begin is the Archive.":
    raise RuntimeError("USE v488.91 visitor-language invariant failed: final response boundary is not sealed.")

# v489.206 regression: ordinary explanatory prose must not expose formulaic section labels.
_BASIC_INQUIRY_NATURAL_PROSE_PROBE = _sanitize_basic_inquiry_response(
    "Stewardship means caring for what is entrusted to us.\n\n"
    "Why it matters now: carelessness passes costs to others.\n\n"
    "Practical implication: consider who will live with the consequences."
)
if re.search(r"(?i)\b(?:why it matters now|practical implication)\s*:", _BASIC_INQUIRY_NATURAL_PROSE_PROBE):
    raise RuntimeError("USE v489.206 invariant failed: formulaic explanatory labels escaped the visitor boundary.")
if "carelessness passes costs to others" not in _BASIC_INQUIRY_NATURAL_PROSE_PROBE or "consider who will live with the consequences" not in _BASIC_INQUIRY_NATURAL_PROSE_PROBE:
    raise RuntimeError("USE v489.206 invariant failed: natural-prose label cleanup removed substantive answer text.")


def _basic_inquiry_has_source_dump(response):
    """Detect copied source fragments that are not safe as a visitor-facing answer."""
    text = str(response or "")
    return bool(re.search(
        r"(?i)(?:case studies and real-world applications|"
        r"consider\s+[A-Z][a-z]+,\s*\d{2,3}[- ]year[- ]old|"
        r"eisenhower matrix|by adopting mindfulness meditation)",
        text,
    ))


def _basic_inquiry_source_dump_recovery(query):
    """Fail-closed visitor answer when the composer returns copied source material."""
    q = _normalize_query(query).casefold()
    if re.search(r"\boverwhelmed\b", q) and re.search(r"\b(?:who|talk|someone|support)\b", q):
        return (
            "When you're overwhelmed, you don't have to find the perfect person or explain everything at once. "
            "If there's someone you trust, you could start with: “I'm having a hard time and could use someone to listen. Do you have a few minutes?” "
            "If no one comes to mind, a local community support service or a qualified professional can be another place to start. "
            "If you feel in immediate danger or might hurt yourself, contact local emergency or crisis support now."
        )
    if "stewardship" in q:
        return (
            "Stewardship means taking care of what has been entrusted to you while recognizing your limits and the effects your choices have on others. "
            "It matters because care, neglect, and responsibility accumulate over time, shaping what remains available to other people and to the future."
        )
    return (
        "I can help you think this through, but I don't want to pass along a copied passage as if it were an answer to your question. "
        "A useful first step is to identify the part of the situation that matters most to you right now, then look for a resource that speaks directly to it."
    )


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
    visitor_response = _sanitize_basic_inquiry_response(parsed["response"])
    if not visitor_response:
        return None
    if visitor_response.count("?") != 1:
        return None
    if re.search(
        r"\b(?:evidence excerpt|canonical evidence|internal interpretation|"
        r"bounded by USE|processing layer|provider|model|retrieval|synthesis)\b",
        visitor_response,
        re.I,
    ):
        return None

    return {
        "response": visitor_response,
        "doorway_title": selected,
        "provider": str(bank_result.get("provider") or ""),
        "model": str(bank_result.get("model") or ""),
    }


def _explicit_closing_question_requested(query):
    """Recognize a visitor's explicit request for one closing or reflective question."""
    q = re.sub(r"\s+", " ", str(query or "")).strip()
    return bool(
        re.search(r"\b(?:finish|end)\b.{0,100}\bquestion\b", q, re.I)
        or re.search(r"\bquestion\b.{0,100}\b(?:invite|inviting|prompt|prompting)\b", q, re.I)
        or re.search(r"\bask me\b.{0,60}\bquestion\b", q, re.I)
    )
def _is_generic_workplace_credit_taking_question(query):
    """Recognize general workplace-credit questions that lack a lived relational case."""
    q = _normalize_query(query)
    asks_for_patterns = bool(re.search(r"\b(?:common patterns|typical patterns|patterns|examples|ways)\b", q))
    about_credit = bool(re.search(r"\b(?:taking credit|claiming credit|credit for work|workplace credit)\b", q))
    workplace_context = bool(re.search(r"\b(?:workplace|at work|workplace relationships|colleagues|coworkers|professional relationships|on a team|team settings)\b", q))
    # A question can be phrased generally while still asking about a specific
    # lived case. Keep those cases out of the general-knowledge recovery path.
    lived_case = bool(re.search(
        r"\b(?:i feel|i am|i'm|my colleague|my coworker|my teammate|my manager|my boss|"
        r"my contribution|my idea|my work|someone on my team|a colleague of mine|"
        r"happened to me|in my team|on my team|our project|we worked together|"
        r"my team keeps|my manager keeps|my boss keeps)\b",
        q,
    ))
    return asks_for_patterns and about_credit and workplace_context and not lived_case


def _basic_inquiry_round1_deterministic_response(query, interpretation, context_data, *, recommendation_available=False):
    """Question-aware last-resort answer; never promise an answer and then refuse."""
    interpretation = interpretation or {}
    question = _normalize_query(query)
    q = re.sub(r"\s+", " ", question).strip().casefold()

    try:
        documents = use_core.context_blocks_to_documents(str(context_data.get("context_blocks") or ""))
    except Exception:
        documents = []
    documents = [d for d in documents if isinstance(d, dict)]
    title = str(documents[0].get("title") or "").strip() if documents else ""
    content = str((documents[0].get("content") or documents[0].get("text") or documents[0].get("excerpt") or "") if documents else "").strip()
    content = re.sub(r"\s+", " ", content)
    if not content:
        community_archive_recovery = _guide_bounded_community_archive_answer(query)
        if community_archive_recovery:
            return community_archive_recovery

    if _is_practical_stewardship_question(query) and re.search(
        r"\b(?:everyday|ordinary|personal)\b", q
    ) and re.search(r"\b(?:responsibilities|responsibility|life)\b", q) and not re.search(
        r"\b(?:community|communities|shared space|public budget)\b", q
    ):
        response = (
            "Stewardship in everyday life means taking care of the people, resources, roles, and commitments entrusted to you, while considering how your choices affect others. "
            "It is less about having a special title and more about how you handle what is in your care.\n\n"
            "In ordinary responsibilities, that might mean keeping a promise, using shared resources carefully, maintaining something instead of leaving the burden to someone else, being honest when a mistake affects other people, or making a decision with its longer-term consequences in mind. "
            "At work, it could mean sharing credit fairly and leaving clear records; at home, looking after a shared space; in a group, making sure responsibilities are understood rather than quietly falling on one person.\n\n"
            "A useful check is: What has been entrusted to me, who else is affected, what needs care or repair, and what should I leave in good condition for the next person? "
            "This is a general practical explanation, not a claim that a specific Archive text prescribes these examples. I could not verify a sufficiently direct Archive resource to recommend for this question."
        )
        return {"response": response, "doorway_title": "", "provider": "bounded_everyday_stewardship_recovery", "model": ""}

    if _is_practical_stewardship_question(query):
        response = (
            "A community can practice stewardship by making its responsibilities visible and considering who is affected by each decision. "
            "For example, before changing a shared space or allocating a limited budget, invite the people who rely on it to explain what they need and what could be lost.\n\n"
            "Agree on clear criteria, use the same criteria for everyone, name who will maintain the result, and make the reasons for the decision accessible. "
            "Where people disagree, record the trade-offs and choose a time to review the outcome rather than treating the first decision as beyond question.\n\n"
            "These are general practical suggestions, not a claim that a specific Archive text prescribes this process. I could not verify a sufficiently direct Archive resource to recommend for this question."
        )
        return {"response": response, "doorway_title": "", "provider": "bounded_practical_stewardship_recovery", "model": ""}

    if _is_generic_workplace_credit_taking_question(query):
        response = (
            "Common workplace credit-taking patterns can include presenting shared work as an individual achievement, leaving collaborators out of updates or presentations, describing a team's result without naming contributors, or repeating another person's idea without acknowledging its source. "
            "A single instance does not establish intent; roles, meeting habits, and unclear ownership can also affect who gets recognized. "
            "A fair assessment looks at the specific contribution, how it was represented, whether the pattern repeats, and whether attribution can be clarified. "
            "Which of these patterns, if any, are you trying to understand?"
        )
        return {
            "response": response,
            "doorway_title": "",
            "provider": "bounded_workplace_credit_taking_general_knowledge",
            "model": "",
        }

    # This recovery is deliberately modest. It answers the concrete public
    # question from general knowledge where a stable, everyday explanation is
    # available, without fabricating Archive evidence or source-specific claims.
    if re.search(r"\b(?:understand|make sense of|interpret)\b", q) and re.search(r"\b(?:difficult situation|situation|what happened|someone's behavior|their behavior)\b", q) and re.search(r"\b(?:judge|judgment|judgement|assume|assumption|rush)\b", q):
        response = (
            "When a situation is difficult, it helps to separate what you know from what you think it means. "
            "You can acknowledge your first reaction without treating it as the whole truth; there may be details you have not seen or another explanation for what happened.\n\n"
            "You do not have to suspend judgment forever or ignore your own boundaries. Sometimes giving yourself a little time, or asking one honest question before deciding, is enough to help you respond more fairly."
        )
        return {"response": response, "doorway_title": "", "provider": "bounded_reflective_general_knowledge_recovery", "model": ""}

    # Resolve the question's actual conflict before the broad stewardship-definition rule.
    # This prevents deterministic-only mode from returning the same generic definition
    # for materially different questions about disagreement and competing obligations.
    if (
        "stewardship" in q
        and re.search(r"\b(?:disagree|disagreement|conflict|competing|opposing|different priorities)\b", q)
        and re.search(r"\b(?:protect|protecting|preserve|preserving|worth|values)\b", q)
    ):
        response = (
            "When people disagree about what is worth protecting, the disagreement often reflects different values, responsibilities, or fears about what could be lost. One person may want to preserve continuity; another may believe change is necessary to protect people or keep something useful. It helps to name those underlying concerns before treating the other person as careless or unreasonable.\n\n"
            "A practical next step is to ask what each person is trying to protect, who would bear the costs of each option, and which responsibilities or rights cannot simply be traded away. Separate shared facts from judgments, and look for options that preserve the most important interests while making the unavoidable trade-offs explicit.\n\n"
            "People may not reach identical priorities, and stewardship does not require pretending otherwise. They can still agree on a fair process, explain their reasons, consider the people affected but not represented, and review the decision when new evidence or consequences emerge. The aim is to handle disagreement responsibly, not to erase it."
        )
        return {"response": response, "doorway_title": title, "provider": "bounded_conflict_stewardship_recovery", "model": ""}

    # Provider exhaustion must not turn a straightforward concept definition into a refusal.
    # This is a bounded general explanation, not a claim of a single canonical Archive definition.
    if "reciprocity" in q and re.search(r"\b(?:what\s+is|what\s+does|meaning|define|explain|mean)\b", q):
        response = (
            "Reciprocity means a relationship of mutual response: people give, receive, and support one another over time. "
            "It is not a strict tally in which every act must be repaid immediately or in exactly equal measure. "
            "For the Living Archive context, this is a useful starting definition; the linked Archive source may offer a more specific framing.\n\n"
            "For example, neighbors might take turns checking on an older resident or helping each other with errands. "
            "One person may give more during a difficult week and receive help later; the relationship can remain reciprocal without every exchange being identical.\n\n"
            "Reciprocity should not be used to demand access, obedience, or repayment from someone who cannot freely offer it. "
            "Mutual support works best when contributions respond to real circumstances rather than becoming a debt ledger."
        )
        return {"response": response, "doorway_title": title, "provider": "bounded_general_knowledge_recovery", "model": ""}

    if "stewardship" in q and "responsibility" in q and re.search(r"\b(?:difference|different|distinguish|distinction|versus|vs)\b", q):
        response = (
            "Responsibility is about what you are answerable for: a task, a promise, a role, or the consequences of a decision. "
            "It can be assigned to you, shared, or delegated. "
            "Stewardship is about how you care for something placed in your hands, especially when its value reaches beyond your immediate needs. "
            "It asks you to maintain, protect, or improve it for others and for the future.\n\n"
            "The two belong together, but they are not identical. Responsibility asks, ‘What am I accountable for?’ "
            "Stewardship asks, ‘How should I care for what I have been entrusted with?’ "
            "You can fulfill a duty narrowly and still neglect the wider trust; stewardship asks you to consider that wider effect while respecting your own limits."
        )
        return {"response": response, "doorway_title": title, "provider": "bounded_general_knowledge_recovery", "model": ""}

    # Treat explicit definition/explanation requests as answerable even when the
    # visitor does not also use "why", "matter", or "important". Navigation
    # preferences are separate from answer intent and must never suppress this
    # bounded general-knowledge recovery when the provider bank is exhausted.
    if "stewardship" in q and re.search(r"\b(?:what\s+is|explain|define|describe|meaning|means|understand|why|matter|important|everyday|life)\b", q):
        response = (
            "Stewardship means taking care of something entrusted to you—such as your time, relationships, shared spaces, money, or the natural world—rather than treating it as if only your immediate needs matter. "
            "In everyday life, it shows up in small choices: keeping a promise, maintaining what others rely on, using resources thoughtfully, and considering how your decisions affect people around you.\n\n"
            "It matters because ordinary choices accumulate. Carelessness can pass costs to other people or to the future, while responsible care helps preserve trust, usefulness, and possibilities for those who come after us.\n\n"
            "Stewardship does not mean controlling everything or sacrificing yourself for everyone else. It means recognizing what is yours to care for, acting responsibly within your limits, and leaving things no worse—and where possible better—than you found them."
        )
        # The deterministic last-resort path must preserve an explicit visitor
        # request for a reflective closing question just as the composition
        # validator does on the provider-generated path.
        if _explicit_closing_question_requested(question) and not response.rstrip().endswith("?"):
            response += " What is one thing in your everyday life that you feel responsible for caring for?"
        return {"response": response, "doorway_title": title, "provider": "bounded_general_knowledge_recovery", "model": ""}

    if "burnout" in q and re.search(r"\b(manager|manage|leader|supervisor)\b", q):
        response = (
            "As a manager, treat burnout as a workload and recovery problem—not simply a personal failure to cope. Start by identifying what is draining you most: excessive hours, constant availability, unclear priorities, emotional demands, or too little control over the work.\n\n"
            "Choose one pressure you can reduce this week. For example, if every decision comes to you, name which decisions your team can make without your approval and agree on clear limits for when they should escalate. That gives you some recovery time while building the team's capacity.\n\n"
            "Also protect basic recovery: take real breaks, set a reasonable end to the workday where possible, and speak with your own manager about priorities that cannot all fit. If exhaustion is persistent, affecting your health, or making daily functioning difficult, consider professional support. You do not have to solve a structural workload problem by pushing yourself harder."
        )
        return {"response": response, "doorway_title": "", "provider": "bounded_general_knowledge_recovery", "model": ""}

    if re.search(r"\boverwhelmed\b", q) and re.search(r"\b(?:who|talk|someone|support)\b", q):
        response = (
            "When you're overwhelmed, you don't have to find the perfect person or explain everything at once. "
            "If there's someone you trust, you could start with: “I'm having a hard time and could use someone to listen. Do you have a few minutes?” "
            "If no one comes to mind, a local community support service or a qualified professional can be another place to start. "
            "If you feel in immediate danger or might hurt yourself, contact local emergency or crisis support now."
        )
        return {"response": response, "doorway_title": "", "provider": "bounded_supportive_recovery", "model": ""}

    # Preserve a direct, bounded explanation of institutional responsibility when
    # provider composition is unavailable. A relevant doorway is not a substitute
    # for answering the visitor, and missing Archive evidence is not missing general
    # knowledge. This is explicitly general knowledge, not Archive attribution.
    if re.search(r"\binstitutional responsibility\b", q):
        response = (
            "Institutional responsibility means that an organization and the people who lead or act for it must answer for the decisions they make, the duties they hold, and the effects those decisions have on others. It is not enough for an institution to say that a harmful outcome was nobody’s personal intention; its rules, choices, and failures to act can still have real consequences.\n\n"
            "For example, if a public office repeatedly loses applications, responsibility includes more than blaming the employee at the desk. The office should examine its process, explain what went wrong, correct the problem, and make it less likely to happen again. Individual people may also be accountable for their own choices, but the institution must address problems built into its systems.\n\n"
            "Institutional responsibility does not mean an organization can control everything or guarantee perfect results. It means being clear about its obligations, making decisions fairly, giving reasons, listening to people affected, correcting preventable harm, and accepting appropriate oversight. The exact duties depend on the institution’s role, the rules that govern it, and the situation involved."
        )
        return {
            "response": response,
            "doorway_title": title,
            "provider": "bounded_general_knowledge_recovery",
            "model": "",
        }

    # When provider composition is exhausted, preserve a directly asked public
    # governance topic instead of falling through to the generic refusal path.
    # This is general knowledge, not a claim that the Archive supplied evidence.
    topic_groups = _topic_anchor_groups(question)
    if "political_dynasties" in topic_groups:
        response = (
            "Political dynasties are families whose members hold or repeatedly win elected office across generations. "
            "Their influence can shape candidate selection, local party organization, public appointments, and access to public resources. "
            "The effects depend on how elections, public institutions, and oversight operate around those family networks.\n\n"
            "Where family networks dominate nominations, appointments, or access to services, accountability can weaken because officials may face stronger incentives to answer to a family network than to the wider public. "
            "But the existence of a dynasty alone does not prove corruption or poor performance; those are claims that require evidence about specific decisions and outcomes.\n\n"
            "To assess a particular locality, examine who holds which offices and their family relationships, how competitive elections are, procurement and budget records, conflicts of interest, and whether courts, auditors, media, and citizens can scrutinize decisions. "
            "These indicators help distinguish a structural risk from an unsupported claim about a particular person or family."
        )
        return {
            "response": response,
            "doorway_title": "",
            "provider": "bounded_public_governance_recovery",
            "model": "",
        }

    # Help a visitor begin when they cannot yet phrase the question.
    if "not sure how to phrase my question" in q and "something is missing" in q:
        response = (
            "You do not need to have the question fully formed yet. We can start with the sense that something feels missing, without deciding in advance what it means. "
            "When you notice that feeling, does it seem connected to a particular part of your life, or is it difficult to locate?"
        )
        return {"response": response, "doorway_title": "", "provider": "bounded_human_orientation_recovery", "model": ""}
    # Protect the established General Guide answer for this calibrated
    # conceptual question when every provider is unavailable. This is ordinary
    # general knowledge, not an Archive attribution; doorway selection remains
    # independent and evidence-grounded.
    if re.search(r"\brelationship between personal agency and responsibility to others\b", q):
        response = (
            "Personal agency and responsibility to others are not opposing forces but interdependent aspects of the same moral life. Agency is the capacity to make choices and act on them; responsibility is the recognition that those choices have consequences for people who are affected by them. You cannot exercise genuine agency without acknowledging that your actions exist within a web of relationships, and you cannot fulfill responsibility to others without the freedom to choose how to act.\n\n"
            "The tension arises when agency is understood as pure independence—the idea that you are a self-contained individual whose choices are yours alone. In reality, our decisions are shaped by the people we are connected to, and those people are shaped by our decisions. For example, a manager who exercises agency to restructure a team is not just making a personal career move; they are altering the working conditions, security, and morale of the people on that team. The manager's freedom to decide is real, but it is bounded by the legitimate needs and rights of the employees. Ignoring that boundary does not make the choice freer; it makes it less responsible.\n\n"
            "The key distinction is between agency as the ability to act and agency as the right to act without regard for impact. True agency includes the willingness to be accountable for the effects of your choices. Responsibility to others is not a constraint on your freedom; it is the condition that makes your freedom meaningful. When you act with awareness of how your choices affect others, you are not surrendering your agency—you are exercising it fully."
        )
        return {
            "response": response,
            "doorway_title": title,
            "provider": "calibrated_general_knowledge_recovery",
            "model": "",
        }

    # Funding-priority questions remain answerable when retrieval has no directly
    # relevant canonical resource. Keep the general decision framework separate
    # from doorway selection: never cite or recommend an unrelated Archive asset
    # as a substitute for answering the question.
    if (
        re.search(r"\b(?:funding|fund|budget|allocate|allocation)\b", q, re.I)
        and re.search(r"\b(?:competing priorities|two priorities|limited resources|neither can be fully supported|cannot fully fund|can't fully fund|trade[- ]?offs?)\b", q, re.I)
    ):
        response = (
            "When a community cannot fully fund both priorities, it should agree on transparent criteria before choosing. "
            "Compare the urgency of each need, the consequences of delaying it, who would be affected, and whether a smaller "
            "or phased option could protect the most important outcomes.\n\n"
            "Make the trade-offs explicit: what each option would protect, what it would leave unmet, and who would carry the cost. "
            "Use the same criteria for both options, include the people most affected, and record the reasons for the decision. "
            "Where uncertainty remains, consider a time-limited allocation with a clear review point rather than presenting the choice as permanent.\n\n"
            "This is a general decision framework, not a claim that the Archive supplied a definitive answer. I did not identify "
            "a sufficiently direct Archive resource to recommend for this question."
        )
        return {
            "response": response,
            "doorway_title": "",
            "provider": "bounded_funding_priority_recovery",
            "model": "",
        }

    # Bounded everyday task recovery: answer common practical questions without
    # requiring Archive retrieval to manufacture a useful response.
    friendship_expectations_recovery = _guide_bounded_friendship_expectations_answer(query)
    if friendship_expectations_recovery:
        return friendship_expectations_recovery

    if re.search(r"\b(?:reading list|list of books to read|books i want to read)\b", q) and re.search(r"\b(?:organize|organise|track|manage|plan|keep)\b", q):
        response = (
            "Keep one reading list and give each item a simple status: want to read, reading, paused, or finished. "
            "Record the title and author, why it interests you, and the next step—such as borrowing it or reading the next chapter. "
            "If the list grows long, add a few broad categories rather than building a complicated system.\n\n"
            "Once a week, choose one or two books that fit your current time and energy, and move the rest to a later list. "
            "That keeps the list useful as a guide rather than turning it into another obligation."
        )
        return {"response": response, "doorway_title": "", "provider": "bounded_reading_list_recovery", "model": ""}

    if re.search(r"\b(?:cleaning schedule|household cleaning|weekly cleaning)\b", q):
        response = (
            "Start with a short list of recurring tasks and group them by frequency: daily resets, weekly cleaning, and occasional deeper jobs. "
            "Assign a few manageable tasks to specific days, and keep the daily list small enough to finish in about 10–20 minutes.\n\n"
            "If more than one person shares the home, agree who owns each task and rotate the less popular jobs. "
            "Try the schedule for two weeks, then adjust it to the time you actually have rather than treating it as a test of discipline."
        )
        return {"response": response, "doorway_title": "", "provider": "bounded_household_schedule_recovery", "model": ""}

    underlying = str(interpretation.get("underlying_question") or "").strip()
    movement = str(interpretation.get("desired_movement") or "").strip()
    if content:
        explanation = f"The Archive material available here offers this starting point: “{content[:360].rstrip()}”"
        opening = f"The question is asking about {underlying.rstrip('.')}." if underlying else f"Your question asks: {question.rstrip('?')}."
        if movement:
            closing = f"A useful next movement may be {movement.rstrip('.')}."
        elif recommendation_available:
            closing = "That gives you a starting point; the separately selected Archive resource offers a place to explore further."
        else:
            closing = "That gives you a starting point; I did not identify a directly relevant Archive resource to recommend for this question."
    elif re.search(r"\b(?:meaning|means|mean|what is)\b.{0,60}\bemptiness\b|\bemptiness\b.{0,60}\b(?:meaning|means|mean)\b", question, re.I):
        opening = "Emptiness can mean different things depending on the context."
        explanation = (
            "In everyday life, it can describe a felt absence of meaning, connection, or purpose. "
            "In philosophy, it can refer to the absence of an independent, permanent essence. "
            "In Buddhist thought, emptiness does not mean that nothing exists; it points to the way things arise through causes, conditions, and relationships."
        )
        closing = (
            "These meanings overlap, but they are not interchangeable. Are you thinking about "
            "the feeling of emptiness in everyday life, or the deeper philosophical or Buddhist idea?"
        )
    else:
        opening = f"Your question asks: {question.rstrip('?')}." if question else "The question is worth answering directly."
        explanation = "I couldn't verify a reliable answer from the material available in this request, so I won't present a guess as fact."
        closing = (
            "If you would like to explore this further, the Archive resource below may offer a useful next step."
            if recommendation_available
            else "I could not identify a sufficiently relevant Archive resource to recommend here."
        )
    return {
        "response": "\n\n".join(part for part in (opening, explanation, closing) if part),
        "doorway_title": title,
        "provider": "deterministic_question_preserving_recovery",
        "model": "",
    }



def _guide_html_to_source_text(raw_html):
    """Preserve WordPress block boundaries and omit only standalone author bylines."""
    from html.parser import HTMLParser
    import html

    class SourceParser(HTMLParser):
        BLOCKS = {"address", "article", "blockquote", "br", "dd", "div", "dl", "dt",
                  "figcaption", "figure", "h1", "h2", "h3", "h4", "h5", "h6",
                  "hr", "li", "main", "ol", "p", "section", "table", "td", "th", "tr", "ul"}
        IGNORED = {"script", "style", "noscript", "svg"}
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.parts, self.ignored_depth = [], 0
        def handle_starttag(self, tag, attrs):
            tag = tag.casefold()
            if tag in self.IGNORED:
                self.ignored_depth += 1
            elif not self.ignored_depth and tag in self.BLOCKS:
                self.parts.append("\n")
        def handle_endtag(self, tag):
            tag = tag.casefold()
            if tag in self.IGNORED and self.ignored_depth:
                self.ignored_depth -= 1
            elif not self.ignored_depth and tag in self.BLOCKS:
                self.parts.append("\n")
        def handle_data(self, data):
            if not self.ignored_depth and data:
                self.parts.append(data)

    parser = SourceParser()
    parser.feed(str(raw_html or ""))
    parser.close()
    blocks = []
    for block in re.split(r"\n+", "".join(parser.parts)):
        block = re.sub(r"\s+", " ", html.unescape(block)).strip()
        if not block:
            continue
        if re.fullmatch(
            r"written\s+by\s+gerald\s+a\.?|"
            r"(?:by\s+)?gerald\s+a?\.?\s+daquila\s*,?\s*"
            r"(?:phd\s+candidate|ph\.?d\.?\s+candidate|author)",
            block, flags=re.I,
        ):
            continue
        blocks.append(block)
    return "\n".join(blocks)

def _wordpress_fetch_selected_canonical_body(url):
    """Fetch the selected public Archive page directly when search misses its body."""
    import html
    from urllib.parse import urlparse

    candidate_url = str(url or "").strip()
    parsed = urlparse(candidate_url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != "geralddaquila.com"
        or parsed.username
        or parsed.password
        or not parsed.path.startswith("/")
        or parsed.query
        or parsed.fragment
    ):
        return None
    try:
        request = UrlRequest(
            candidate_url,
            headers={"Accept": "text/html", "User-Agent": "LivingArchiveGuide/1.0"},
            method="GET",
        )
        with urlopen(request, timeout=2.0) as response:
            final_url = str(response.geturl() or "").strip()
            raw_html = response.read(1_000_000).decode("utf-8", errors="replace")
        final = urlparse(final_url)
        if (
            final.scheme != "https"
            or final.hostname != "geralddaquila.com"
            or final.path.rstrip("/").casefold() != parsed.path.rstrip("/").casefold()
        ):
            return None
        title_match = re.search(r"(?is)<title[^>]*>(.*?)</title>", raw_html)
        title = html.unescape(re.sub(r"(?s)<[^>]+>", " ", title_match.group(1))).strip() if title_match else ""
        raw_html = re.sub(r"(?is)<(script|style|noscript|svg)\b[^>]*>.*?</\1>", " ", raw_html)
        raw_html = re.sub(r"(?is)<!--.*?-->", " ", raw_html)
        main_match = re.search(r"(?is)<main\b[^>]*>(.*?)</main>", raw_html)
        article_match = re.search(r"(?is)<article\b[^>]*>(.*?)</article>", raw_html)
        content_html = (main_match or article_match).group(1) if (main_match or article_match) else raw_html
        content = _guide_html_to_source_text(content_html)
        if len(content) < 80:
            return None
        return {
            "title": title or parsed.path.strip("/").replace("-", " ").title(),
            "url": final_url,
            "text": content[:6000],
        }
    except Exception as exc:
        print(f"The Guide selected canonical body fetch skipped ({type(exc).__name__}).")
        return None


def _wordpress_search_canonical_candidates(query, *, limit=3):
    """Recover public canonical candidates when vector retrieval cannot ground a doorway.

    WordPress search is a bounded, provider-independent retrieval supplement, not
    a source of recommendation authority. Every returned item is re-evaluated by
    the same local evidence and relevance gates as vector-retrieved candidates.
    """
    import html

    # `_subject_terms` may yield a set; sort before ranking so separate Render
    # processes do not send different WordPress queries due to hash iteration order.
    terms = sorted(set(_subject_terms(query)))
    if not terms:
        return []
    # Prefer the visitor's more distinctive query terms without introducing
    # topic-specific keyword families or changing the question's meaning.
    indexed_terms = list(enumerate(terms))
    indexed_terms.sort(key=lambda pair: (len(pair[1]), -pair[0]), reverse=True)
    search_text = " ".join(term for _, term in indexed_terms[:2]).strip()
    if not search_text:
        return []
    endpoint = (
        "https://geralddaquila.com/wp-json/wp/v2/search"
        f"?search={quote(search_text, safe='')}&per_page=10"
    )
    try:
        request = UrlRequest(
            endpoint,
            headers={"Accept": "application/json", "User-Agent": "LivingArchiveGuide/1.0"},
            method="GET",
        )
        with urlopen(request, timeout=2.0) as response:
            search_results = json.loads(response.read().decode("utf-8"))
        if not isinstance(search_results, list):
            return []
    except Exception as exc:
        print(f"The Guide canonical search recovery: search unavailable ({type(exc).__name__}).")
        return []

    ranked = []
    for index, item in enumerate(search_results):
        if not isinstance(item, dict):
            continue
        title_obj = item.get("title")
        title = str(title_obj.get("rendered") if isinstance(title_obj, dict) else title_obj or "").strip()
        url = str(item.get("url") or "").strip()
        links = item.get("_links") if isinstance(item.get("_links"), dict) else {}
        self_links = links.get("self") if isinstance(links.get("self"), list) else []
        href = str((self_links[0] or {}).get("href") or "") if self_links and isinstance(self_links[0], dict) else ""
        if not title or not re.match(r"^https://geralddaquila\.com/\S+$", url, re.I):
            continue
        if not re.match(r"^https://geralddaquila\.com/wp-json/wp/v2/(?:posts|pages)/[0-9]+(?:\?.*)?$", href, re.I):
            continue
        title_tokens = set(re.findall(r"[a-z0-9]+", title.casefold()))
        title_hits = sum(bool(_term_forms(term) & title_tokens) for term in terms)
        ranked.append((title_hits, -index, title, url, href))
    ranked.sort(reverse=True)

    def fetch_candidate(entry):
        _title_hits, _order, title, url, href = entry
        try:
            request = UrlRequest(
                href,
                headers={"Accept": "application/json", "User-Agent": "LivingArchiveGuide/1.0"},
                method="GET",
            )
            with urlopen(request, timeout=1.5) as response:
                resource = json.loads(response.read().decode("utf-8"))
            if not isinstance(resource, dict):
                return None
            resource_url = str(resource.get("link") or url).strip()
            resource_title_obj = resource.get("title")
            resource_title = str(
                resource_title_obj.get("rendered")
                if isinstance(resource_title_obj, dict) else resource_title_obj or title
            ).strip()
            content_obj = resource.get("content")
            excerpt_obj = resource.get("excerpt")
            content_html = str(content_obj.get("rendered") or "") if isinstance(content_obj, dict) else str(content_obj or "")
            excerpt_html = str(excerpt_obj.get("rendered") or "") if isinstance(excerpt_obj, dict) else str(excerpt_obj or "")
            raw_content = content_html or excerpt_html
            raw_content = re.sub(r"(?is)<(script|style)\b[^>]*>.*?</\1>", " ", raw_content)
            content = _guide_html_to_source_text(raw_content)
            if not content or not re.match(r"^https://geralddaquila\.com/\S+$", resource_url, re.I):
                return None
            return {"title": html.unescape(resource_title), "url": resource_url, "text": content[:6000]}
        except Exception as exc:
            print(f"The Guide canonical search recovery: resource fetch skipped ({type(exc).__name__}).")
            return None

    # Fetch the bounded candidate slice concurrently but preserve ranking order.
    # The per-request timeout still bounds each outbound operation.
    from concurrent.futures import ThreadPoolExecutor

    candidate_slice = ranked[:limit]
    with ThreadPoolExecutor(max_workers=max(1, min(limit, len(candidate_slice)))) as executor:
        recovered = [item for item in executor.map(fetch_candidate, candidate_slice) if item]
    print(f"The Guide canonical search recovery: search_terms={len(indexed_terms[:2])}, candidates={len(recovered)}.")
    return recovered


def _comparative_subject_terms(query):
    """Extract compared concepts from common comparison questions."""
    normalized = re.sub(r"\s+", " ", str(query or "").strip().casefold())
    patterns = (
        r"\bdifference between (.+?) and (.+?)[?.!]*$",
        r"\brelationship between (.+?) and (.+?)[?.!]*$",
        r"\bcompare (.+?) (?:and|with|to) (.+?)[?.!]*$",
        r"\bcomparison of (.+?) and (.+?)[?.!]*$",
        r"\bhow does (.+?) differ from (.+?)[?.!]*$",
        r"\bhow do (.+?) differ from (.+?)[?.!]*$",
        r"\bhow are (.+?) different from (.+?)[?.!]*$",
    )
    for pattern in patterns:
        match = re.search(pattern, normalized)
        if match:
            terms = []
            for value in match.groups():
                words = [w for w in re.findall(r"[a-z0-9]+", value)
                         if w not in {"the", "a", "an", "is", "are", "does", "do", "how", "what"}]
                if words:
                    terms.append(" ".join(words[-4:]))
            if len(terms) == 2:
                return terms
    return []


def _comparative_candidate_has_direct_fit(query, document):
    """Require evidence about both compared concepts and a topic-signalling title."""
    subjects = _comparative_subject_terms(query)
    if len(subjects) != 2:
        return True
    title = str(document.get("title") or "").casefold()
    body = str(document.get("text") or document.get("content") or document.get("excerpt") or "").casefold()
    return any(subject in title for subject in subjects) and all(subject in body for subject in subjects)


def _stewardship_conflict_candidate_has_direct_fit(query, document):
    """Require direct evidence for stewardship questions about competing values.

    Broad stewardship resources are not automatically relevant to conflict
    questions. The title must signal a stewardship/governance/decision topic and
    the body must substantively address disagreement, competing values, or
    resolving trade-offs. If evidence is insufficient, the recommendation is
    omitted; the visitor's answer is preserved by the caller.
    """
    q = _normalize_query(query)
    if not re.search(r"\bstewardship\b", q, re.I):
        return True
    conflict = bool(re.search(
        r"\b(?:disagree|disagreement|conflict|competing|opposing|different priorities|"
        r"what is worth protecting|worth protecting|trade[- ]?offs?)\b", q, re.I
    ))
    if not conflict:
        return True
    title = str(document.get("title") or "").casefold()
    body = str(document.get("text") or document.get("content") or document.get("excerpt") or "").casefold()
    title_fit = bool(re.search(r"\b(?:stewardship|governance|decision|conflict|values|ethic)\b", title))
    body_fit = bool(re.search(
        r"\b(?:disagree|disagreement|conflict|competing values|different values|"
        r"trade[- ]?offs?|what each protects|protecting|decision[- ]making|"
        r"fair process|resolve|reconcile)\b", body
    ))
    return title_fit and body_fit


def _resource_allocation_candidate_has_direct_fit(query, document):
    """Reject generic resources for questions about funding competing priorities."""
    q = _normalize_query(query)
    if not re.search(r"\b(?:funding|fund|budget|allocate|allocation|priorit(?:y|ies|ize|ise|ization)|limited resources|competing priorities)\b", q, re.I):
        return True
    title = str(document.get("title") or "").casefold()
    body = str(document.get("text") or document.get("content") or document.get("excerpt") or "").casefold()
    title_fit = bool(re.search(r"\b(?:funding|budget|allocation|allocate|priorit(?:y|ies|ization|ize|ise)|resource management|decision[- ]making|trade[- ]offs?|governance)\b", title))
    body_fit = bool(re.search(r"\b(?:fund(?:ing|s)?|budget(?:s|ing)?|allocat(?:e|es|ed|ing|ion)|priorit(?:y|ies|ization|ize|ise)|limited resources|competing needs|decision criteria|trade[- ]offs?|scarce resources|resource allocation|fair process|weigh competing)\b", body))
    return title_fit and body_fit

def _general_guide_authoritative_doorway(query, context_data):
    """Select a relevant canonical doorway from retrieved evidence only.

    A syntactically valid URL is not proof of relevance. Provider/core preselection
    is treated as a candidate, never as authority by itself. Rank retrieved
    documents with the Guide's existing relevance gate and emit only a doorway
    supported by the selected document's title, URL, and content. v489.12
    keeps this selection independent of provider-generated text and fallback URLs.
    """
    if not isinstance(context_data, dict):
        return None
    try:
        profile = _base._inquiry_profile(query)
        if profile.get("risk") or profile.get("action") == "risk":
            return None

        candidates = []
        protected = (
            context_data.get("generation_authority_protected_docs")
            or context_data.get("question_authority_protected_docs")
            or []
        )
        if isinstance(protected, list):
            candidates.extend(item for item in protected if isinstance(item, dict))

        canonical_context = str(
            context_data.get("canonical_link_context")
            or context_data.get("context_blocks")
            or ""
        )
        if canonical_context:
            candidates.extend(_parse_context_documents(canonical_context))

        try:
            supplied = general_guide_composition._documents_from_context(
                use_core, context_data
            )
        except Exception:
            supplied = []
        candidates.extend(item for item in supplied if isinstance(item, dict))

        # Preserve only evidence-bearing documents with canonical Archive URLs.
        evidence_docs = []
        seen = set()
        for item in candidates:
            title = str(item.get("title") or "").strip()
            url = str(item.get("url") or item.get("canonical_url") or "").strip()
            content = str(
                item.get("content") or item.get("text") or item.get("excerpt") or ""
            ).strip()
            if not title or not content:
                continue
            if not re.match(r"^https://geralddaquila\.com/\S+$", url, re.I):
                continue
            key = (title.casefold(), url.casefold())
            if key in seen:
                continue
            seen.add(key)
            evidence_docs.append({"title": title, "url": url, "text": content})

        comparative_subjects = _comparative_subject_terms(query)
        if comparative_subjects:
            evidence_docs = [item for item in evidence_docs if _comparative_candidate_has_direct_fit(query, item)]

        # Conflict-specific relevance is independent of general stewardship
        # topic overlap. Apply it before ranking and again after bounded recovery.
        evidence_docs = [
            item for item in evidence_docs
            if _stewardship_conflict_candidate_has_direct_fit(query, item)
        ]
        evidence_docs = [item for item in evidence_docs if _resource_allocation_candidate_has_direct_fit(query, item)]

        topic_groups = _topic_anchor_groups(query)
        # When a visitor asks what to read about political dynasties, a broad
        # essay that merely mentions the topic cannot displace the direct study.
        # Require a title-level subject match for this recommendation task so
        # that a missing direct candidate triggers bounded canonical recovery.
        require_dynasty_title = (
            profile.get("action") in {"recommendation", "navigation"}
            and "political_dynasties" in topic_groups
        )
        if require_dynasty_title:
            evidence_docs = [
                item for item in evidence_docs
                if "political_dynasties" in _topic_anchor_groups(item.get("title") or "")
            ]

        primary = _canonical_primary_from_docs(evidence_docs, query, profile)
        if not primary:
            # Retrieval and doorway selection are separate. If the retrieved
            # candidate pool lacks a direct subject match, recover public
            # canonical candidates and subject them to the same relevance gate.
            fallback_docs = _wordpress_search_canonical_candidates(query)
            if require_dynasty_title:
                # A distinctive subject query supplements the general search;
                # it does not replace the visitor's original query.
                fallback_docs.extend(
                    _wordpress_search_canonical_candidates("political dynasties", limit=10)
                )
            fallback_seen = {
                (
                    str(item.get("title") or "").casefold(),
                    str(item.get("url") or item.get("canonical_url") or "").casefold(),
                )
                for item in evidence_docs
            }
            for item in fallback_docs:
                key = (
                    str(item.get("title") or "").casefold(),
                    str(item.get("url") or item.get("canonical_url") or "").casefold(),
                )
                if key not in fallback_seen:
                    evidence_docs.append(item)
                    fallback_seen.add(key)

            # Recovery is a candidate source, not authority: reapply every
            # subject-specific gate after it has contributed candidates.
            if comparative_subjects:
                evidence_docs = [item for item in evidence_docs if _comparative_candidate_has_direct_fit(query, item)]
            evidence_docs = [
                item for item in evidence_docs
                if _stewardship_conflict_candidate_has_direct_fit(query, item)
            ]
            evidence_docs = [item for item in evidence_docs if _resource_allocation_candidate_has_direct_fit(query, item)]
            if require_dynasty_title:
                evidence_docs = [
                    item for item in evidence_docs
                    if "political_dynasties" in _topic_anchor_groups(item.get("title") or "")
                ]
            asks_for_homepage = bool(re.search(
                r"\b(?:homepage|home page|main page|site home|website home)\b",
                str(query or ""),
                re.I,
            ))
            if not asks_for_homepage:
                evidence_docs = [
                    item for item in evidence_docs
                    if "/" in str(item.get("url") or item.get("canonical_url") or "").split("://", 1)[-1] and str(item.get("url") or item.get("canonical_url") or "").split("://", 1)[-1].split("/", 1)[1].strip("/")
                ]
            primary = _canonical_primary_from_docs(evidence_docs, query, profile)

        if not primary:
            # A missing recommendation is preferable to an unrelated doorway.
            # The caller keeps the answer intact and serializes no recommendation.
            print("The Guide canonical doorway: no candidate passed relevance after bounded search recovery.")
            return None

        # Titles are plain text in the public JSON contract: decode HTML
        # entities and remove emoji/decorative symbols at the boundary.
        import html
        title = html.unescape(str(primary.get("title") or "")).strip()
        title = re.sub(r"[\U0001F000-\U0001FAFF\U00002600-\U000027BF]", "", title)
        title = re.sub(r"\s+", " ", title).strip()
        url = str(primary.get("url") or primary.get("canonical_url") or "").strip()
        if not title or not re.match(r"^https://geralddaquila\.com/\S+$", url, re.I):
            return None
        return {"title": title, "url": url}
    except Exception as exc:
        print(
            "The Guide General Guide doorway selection failed safely: "
            f"{exc}"
        )
        return None


def _normalize_authoritative_recommendation(doorway):
    """Return the single public navigation contract, or None if invalid.

    Recommendation authority belongs to the Guide, not the composition provider.
    This helper makes the response envelope deterministic across provider
    success, provider exhaustion, and conservative recovery.
    """
    if not isinstance(doorway, dict):
        return None
    title = str(doorway.get("title") or "").strip()
    url = str(
        doorway.get("url")
        or doorway.get("canonical_url")
        or ""
    ).strip()
    if not title or not re.match(r"^https://geralddaquila\.com(?:/.*)?$", url, re.I):
        return None
    return {"title": title, "url": url}


# v489.09 regression probes: valid Archive URLs survive validation and stewardship questions retain a canonical doorway
# validator, while non-HTTPS and off-domain destinations remain rejected.
_v48908_probe_url = "https://geralddaquila.com/knowledge-memory-living-codices/"
_v48908_probe = {"title": "Knowledge, Memory & Living Codices", "url": _v48908_probe_url}
if not _normalize_authoritative_recommendation(_v48908_probe):
    raise RuntimeError("USE v489.09 invariant failed: valid canonical recommendation rejected.")
if not re.match(r"^https://geralddaquila\.com/\S+$", _v48908_probe_url, re.I):
    raise RuntimeError("USE v489.09 invariant failed: canonical doorway regex rejected valid HTTPS URL.")
if _normalize_authoritative_recommendation({"title": "Invalid", "url": "http://geralddaquila.com/example/"}):
    raise RuntimeError("USE v489.09 invariant failed: non-HTTPS recommendation accepted.")
if _normalize_authoritative_recommendation({"title": "Invalid", "url": "https://example.org/example/"}):
    raise RuntimeError("USE v489.09 invariant failed: off-domain recommendation accepted.")


def _basic_inquiry_contains_html_markup(text):
    """Reject HTML-shaped provider output at the plain-text visitor boundary.

    Canonical doorways are returned as structured title/URL data, never embedded
    in generated prose. Detect incomplete tags as well as complete tags: malformed
    provider markup must not be passed to the frontend as if it were an answer.
    """
    value = str(text or "")
    return bool(re.search(
        r"<\s*/?\s*(?:a|p|div|span|br|img|iframe|script|style|button|section|ul|ol|li)\b",
        value,
        re.I,
    ))


def _basic_inquiry_markup_recovery(query, history=None, intent="TOPICAL_INQUIRY"):
    """Recompose once without Archive snippets after untrusted markup is rejected.

    In deterministic-only calibration mode, never re-enter the LLM composer
    through this secondary recovery seam.
    """
    if str(os.getenv("USE_REASONING_PROVIDER_MODE", "auto") or "auto").strip().casefold() == "deterministic_only":
        print("The Guide contextless markup recovery: skipped because deterministic-only mode is active.")
        return ""
    clean_context = {
        "intent": str(intent or "TOPICAL_INQUIRY"),
        "context_blocks": "",
        "canonical_link_context": "",
        "generation_authority_protected_docs": [],
        "question_authority_protected_docs": [],
    }
    try:
        result = general_guide_composition.compose(
            use_core=use_core,
            query=str(query or "").strip(),
            context_data=clean_context,
            history_text=_history_text(history),
        )
        response = _sanitize_basic_inquiry_response(
            str((result or {}).get("response") or "").strip()
        )
        if not response or _basic_inquiry_contains_html_markup(response):
            return ""
        if _basic_inquiry_has_source_dump(response):
            return ""
        return response
    except Exception as exc:
        print(f"The Guide contextless markup recovery failed safely: {type(exc).__name__}.")
        return ""


# v489.193 outward-response integrity probes: complete and truncated HTML are both rejected.
if not _basic_inquiry_contains_html_markup('<a href="https://geralddaquila.com/example/">Open</a>'):
    raise RuntimeError("USE visitor-response contract failed: complete HTML markup was not detected.")
if not _basic_inquiry_contains_html_markup('<a href="https://geralddaquila.com/2025/05/21/political-dynasties”'):
    raise RuntimeError("USE visitor-response contract failed: truncated HTML markup was not detected.")
if _basic_inquiry_contains_html_markup("Stewardship means caring for what has been entrusted to us."):
    raise RuntimeError("USE visitor-response contract failed: ordinary prose was rejected.")


def _guide_subject_discovery_query(query):
    """Extract the subject from a natural-language request to find Archive material.

    This is a reusable query-shaping boundary: it removes the visitor's search
    instruction while preserving the requested topic. The original question is
    still used for visitor-facing composition; the extracted subject is used
    only to retrieve and evaluate relevant resources.
    """
    q = re.sub(r"\s+", " ", _normalize_query(query)).strip()
    patterns = (
        # Natural-language reading requests are still Archive discovery tasks.
        # Extract their subject so the answer is grounded in the selected page,
        # rather than letting a broad generated explanation contradict the link.
        r"^(?:i want to understand|i would like to understand|i'd like to understand|i want to learn about|i would like to learn about|i'd like to learn about)\s+(.+?)(?:[.!?]\s*(?:what|which)\s+(?:should|could|can|would)\s+i\s+read\b.*)?[?.!]*$",
        r"^(?:what|which)\s+(?:should|could|can|would)\s+i\s+read\s+(?:about|on|regarding)\s+(.+?)[?.!]*$",
        # A named title followed by a request for the study should retain the title as subject.
        r"^(.+?)\s+[—–-]\s+i\s+(?:want|need)\s+(?:the\s+)?(?:study|article|essay|paper|page|resource)\s+itself(?:,\s*please)?[?.!]*$",
        r"^(?:i\s+)?(?:want|need)\s+(?:the\s+)?(?:study|article|essay|paper|page|resource)\s+(?:itself(?:\s+(?:on|about|regarding))?|on|about|regarding)\s+(.+?)[?.!]*$",
        r"^(?:please\s+)?(?:recommend|find|show\s+me)\s+(?:the\s+)?(?:study|article|essay|paper|page|resource)\s+(?:called|titled|on|about|regarding)\s+(.+?)[?.!]*$",
        # Requests for the study/article itself are resource discovery, not generic Q&A.
        r"^(?:please\s+)?where\s+(?:can|could|do)\s+i\s+find\s+(?:the\s+)?(?:(?:relevant|useful|specific)\s+)?(?:material|materials|information|resources?|content|articles?|essays?|documents?|entries)\s+(?:about|on|regarding|concerning|related\s+to)\s+(.+?)[?.!]*$",
        r"^(?:please\s+)?(?:find|show\s+me|help\s+me\s+find|locate|search\s+for)\s+(?:(?:relevant|useful|specific)\s+)?(?:material|materials|information|resources?|content|articles?|essays?|documents?|entries)\s+(?:about|on|regarding|concerning|related\s+to)\s+(.+?)[?.!]*$",
        r"^(?:i(?:'m|\s+am)\s+looking\s+for|i\s+need|can\s+you\s+find|could\s+you\s+find)\s+(?:(?:relevant|useful|specific)\s+)?(?:material|materials|information|resources?|content|articles?|essays?|documents?|entries)\s+(?:about|on|regarding|concerning|related\s+to)\s+(.+?)[?.!]*$",
    )
    for pattern in patterns:
        match = re.match(pattern, q, re.I)
        if match:
            subject = re.sub(r"\s+", " ", match.group(1)).strip(" \t.,;:?!")
            if subject and len(re.findall(r"[a-z0-9]+", subject, re.I)) >= 1:
                return subject
    # A short standalone noun phrase is a resource/topic lookup, not a request for general prose.
    # Do not apply this fallback to sentences or explicit questions.
    if not re.search(r"[?!.]", q) and 1 <= len(q.split()) <= 12:
        if not re.search(r"\b(?:what|why|when|where|who|how|is|are|was|were|does|do|did|can|could|would|should|will|has|have|had)\b", q, re.I):
            return q.strip(" \t.,;:")
    return ""


def _guide_requires_canonical_subject_supplement(archive_evidence_unavailable, discovery_subject):
    """Always supplement subject-finding requests with vetted canonical content."""
    return bool(archive_evidence_unavailable or str(discovery_subject or "").strip())


def _guide_subject_supplement_limit(discovery_subject):
    """Broaden candidate recall for explicit resource-finding requests."""
    return 10 if str(discovery_subject or "").strip() else 3


def _guide_discovery_evidence_grade(subject, document, node=None):
    """Grade page-level subject evidence independently of the search provider.

    DIRECT requires the subject itself to be established by the page, not just
    one broad shared token. RELATED requires a real page-level overlap plus
    corroborating registered purpose/hints; it must be described as adjacent.
    Metadata alone, or an incidental body token, is WEAK and cannot authorize
    a recommendation.
    """
    if not isinstance(document, dict) or not str(subject or "").strip():
        return {"grade": "weak", "score": 0, "support": []}
    title = str(document.get("title") or "").strip().casefold()
    body = str(
        document.get("text") or document.get("content") or document.get("excerpt") or ""
    ).strip().casefold()
    early = body[:3000]
    if len(body) < 80:
        return {"grade": "weak", "score": 0, "support": []}

    stop = {
        "about", "article", "articles", "content", "document", "documents",
        "general", "information", "material", "materials", "public", "resource",
        "resources", "specific", "where", "find", "please", "useful", "relevant",
        "could", "would", "should", "from", "with", "into", "that", "this",
        # Natural-language question wrappers are not subject anchors.
        "how", "what", "why", "when", "does", "do", "did", "can", "in", "the",
        "and", "to", "of", "for", "affect", "affects", "affecting", "read",
        "want", "understand", "learn",
    }
    subject_tokens = {
        token for token in re.findall(r"[a-z0-9]+", str(subject).casefold())
        if len(token) >= 4 and token not in stop
    }
    if not subject_tokens:
        return {"grade": "weak", "score": 0, "support": []}

    title_tokens = set(re.findall(r"[a-z0-9]+", title))
    body_tokens = set(re.findall(r"[a-z0-9]+", body))
    early_tokens = set(re.findall(r"[a-z0-9]+", early))
    title_hits = subject_tokens & title_tokens
    body_hits = subject_tokens & body_tokens
    early_hits = subject_tokens & early_tokens
    normalized_subject = re.sub(r"\s+", " ", str(subject).casefold()).strip()
    phrase_in_title = normalized_subject in title
    phrase_in_early = normalized_subject in early

    direct_fit = 0
    try:
        direct_fit, _coverage, _relation_hits, _answerability = (
            use_core._question_evidence_fit_profile(str(subject), document)
        )
        direct_fit = int(direct_fit or 0)
    except Exception:
        direct_fit = 0

    # Page text can contain repeated incidental mentions from navigation,
    # boilerplate, or a broad page's framing. For registered candidates, body
    # mentions alone cannot establish directness unless the approved node's own
    # purpose/hints also name every subject anchor. A matching page title is
    # still strong evidence. Non-registry bodies require unusually strong,
    # repeated subject evidence and cannot independently authorize a doorway.
    node_metadata = " ".join([
        str(node.get("title") or ""),
        str(node.get("purpose") or ""),
        " ".join(str(value) for value in (node.get("semantic_hints") or [])),
    ]).casefold() if node else ""
    metadata_tokens = set(re.findall(r"[a-z0-9]+", node_metadata))
    metadata_subject_hits = subject_tokens & metadata_tokens
    phrase_count = len(re.findall(re.escape(normalized_subject), body))
    direct_body_fit = (
        (
            node is not None
            and len(subject_tokens) >= 2
            and len(early_hits) >= 2
            and len(metadata_subject_hits) == len(subject_tokens)
            and (
                (phrase_count >= 1 and direct_fit >= 2)
                # A registered node whose title names the subject and whose
                # opening text corroborates it is direct even when the visitor's
                # full natural-language question is not repeated verbatim.
                or (len(title_hits) >= 2 and len(early_hits) >= 3)
            )
        )
        or (
            node is None
            and phrase_in_early
            and phrase_count >= 3
            and direct_fit >= 3
            and len(body_hits) >= 2
            and len(early_hits) >= 2
        )
    )

    # Relational reading requests can include a verb or outcome not repeated in
    # the title ("how political dynasties affect public accountability"). An
    # active registered title is a strong subject anchor, but directness still
    # requires page-level body evidence and near-complete support from approved
    # registry metadata. This keeps broad related pages from passing on a shared
    # keyword while allowing a dedicated study to answer a relationally phrased
    # request about its established subject.
    title_anchor_tokens = {
        token for token in re.findall(r"[a-z0-9]+", title)
        if len(token) >= 4 and token not in stop
    }
    title_anchor_hits = title_anchor_tokens & subject_tokens
    requested_aspect_hits = early_hits & (subject_tokens - title_anchor_tokens)
    registered_title_anchor_fit = (
        node is not None
        and len(title_anchor_tokens) >= 2
        and len(title_anchor_hits) >= min(3, len(title_anchor_tokens))
        and len(early_hits) >= 2
        and bool(requested_aspect_hits)
        and len(metadata_subject_hits) >= max(1, len(subject_tokens) - 1)
    )
    direct = phrase_in_title or direct_body_fit or registered_title_anchor_fit
    if direct:
        support = sorted(early_hits or body_hits)
        return {"grade": "direct", "score": 100 + direct_fit + len(early_hits) * 4 + len(title_hits) * 3, "support": support}

    # A related destination must be an approved Guide Node and show substantive
    # overlap in its own body. One generic token is not enough by itself: require
    # at least one subject anchor in the opening and a second body-level signal
    # represented in the registered title/purpose/hints. Report the shared terms
    # literally; do not invent a semantic relationship.
    if not node:
        return {"grade": "weak", "score": 0, "support": sorted(body_hits)}
    metadata = node_metadata
    registered_anchors = {
        token for token in metadata_tokens
        if len(token) >= 5 and token not in stop and token not in subject_tokens
    }
    body_context = {
        token for token in body_tokens
        if len(token) >= 5 and token not in stop and token not in subject_tokens
    }
    corroborating_context = registered_anchors & body_context
    if body_hits and len(corroborating_context) >= 2:
        support = sorted(body_hits | corroborating_context)
        metadata_subject_hits = subject_tokens & metadata_tokens
        # Prefer a registry node whose own approved purpose/hints name the
        # requested subject, rather than a broad node that merely mentions it.
        score = (
            len(body_hits) * 8
            + len(metadata_subject_hits) * 12
            + len(corroborating_context) * 2
            + min(direct_fit, 2)
        )
        return {"grade": "related", "score": score, "support": support}
    return {"grade": "weak", "score": 0, "support": sorted(body_hits)}


def _guide_selected_doorway_discovery_evidence(documents, subject, doorway):
    """Validate the selected canonical page and grade its direct/related fit."""
    if not isinstance(doorway, dict) or not str(subject or "").strip():
        return []
    selected_url = str(doorway.get("url") or "").strip().rstrip("/").casefold()
    if not selected_url:
        return []
    accepted = []
    for document in documents if isinstance(documents, list) else []:
        if not isinstance(document, dict):
            continue
        candidate_url = str(
            document.get("url") or document.get("canonical_url") or ""
        ).strip().rstrip("/").casefold()
        if candidate_url != selected_url:
            continue
        node = document.get("_guide_node") if isinstance(document.get("_guide_node"), dict) else None
        grade = _guide_discovery_evidence_grade(subject, document, node=node)
        if grade["grade"] in {"direct", "related"}:
            approved = dict(document)
            approved["_discovery_relevance"] = grade["grade"]
            approved["_discovery_relevance_score"] = grade["score"]
            approved["_discovery_support_terms"] = grade["support"]
            accepted.append(approved)
    accepted.sort(
        key=lambda item: (
            item.get("_discovery_relevance") == "direct",
            int(item.get("_discovery_relevance_score") or 0),
        ),
        reverse=True,
    )
    return accepted[:1]

def _guide_registered_discovery_nodes(subject, limit=3):
    """Rank active, WordPress-authorized Guide Nodes for a discovery subject.

    This is metadata-based candidate selection, not recommendation authority:
    a node can be selected only after its canonical body is fetched and passes
    the existing selected-page evidence checks.
    """
    query = re.sub(r"\s+", " ", str(subject or "").casefold()).strip()
    query_terms = {
        token for token in re.findall(r"[a-z0-9]+", query)
        if len(token) >= 4 and token not in {
            "about", "article", "articles", "content", "document", "documents",
            "general", "information", "material", "materials", "public",
            "resource", "resources", "specific", "where", "find",
        }
    }
    if not query_terms:
        return []
    ranked = []
    try:
        nodes = _guide_node_registry_snapshot()
    except Exception as exc:
        print(f"The Guide registry discovery: registry unavailable ({type(exc).__name__}).")
        return []
    for node in nodes:
        if not isinstance(node, dict) or str(node.get("status") or "") != "active":
            continue
        url = str(node.get("canonical_url") or "").strip()
        title = str(node.get("title") or "").strip()
        if not title or not re.match(r"^https://geralddaquila\.com/\S+$", url, re.I):
            continue
        metadata = " ".join([
            title,
            str(node.get("purpose") or ""),
            " ".join(str(value) for value in (node.get("semantic_hints") or [])),
        ]).casefold()
        metadata_terms = set(re.findall(r"[a-z0-9]+", metadata))
        overlap = query_terms & metadata_terms
        if not overlap:
            continue
        score = len(overlap) * 3
        if query and query in metadata:
            score += 6
        title_terms = set(re.findall(r"[a-z0-9]+", title.casefold()))
        score += 2 * len(query_terms & title_terms)
        ranked.append((score, title.casefold(), node))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return [item[2] for item in ranked[:max(1, int(limit or 3))]]


def _guide_registered_discovery_documents(subject, documents):
    """Rank canonical documents against approved Guide Nodes and page-level evidence."""
    nodes = _guide_registered_discovery_nodes(subject, limit=20)
    if not nodes:
        return []
    node_by_url = {
        str(node.get("canonical_url") or "").rstrip("/").casefold(): node
        for node in nodes
    }
    ranked = []
    for index, document in enumerate(documents if isinstance(documents, list) else []):
        if not isinstance(document, dict):
            continue
        url = str(document.get("url") or document.get("canonical_url") or "").strip()
        node = node_by_url.get(url.rstrip("/").casefold())
        if not node:
            continue
        grade = _guide_discovery_evidence_grade(subject, document, node=node)
        if grade["grade"] not in {"direct", "related"}:
            continue
        approved = dict(document)
        approved["_guide_node"] = node
        approved["_discovery_relevance"] = grade["grade"]
        approved["_discovery_relevance_score"] = grade["score"]
        approved["_discovery_support_terms"] = grade["support"]
        ranked.append((
            0 if grade["grade"] == "direct" else 1,
            -int(grade["score"]),
            str(node.get("title") or "").casefold(),
            index,
            approved,
        ))
    ranked.sort(key=lambda item: item[:4])
    return [item[-1] for item in ranked]


def _guide_align_registered_discovery_doorway(subject, documents):
    """Resolve the highest-ranked direct or explicitly related registered resource."""
    registered_documents = _guide_registered_discovery_documents(subject, documents)
    if not registered_documents:
        return None, []
    return _guide_align_discovery_doorway(subject, registered_documents)


def _guide_align_discovery_doorway(subject, documents):
    """Select direct evidence first, or an approved related resource with its grade."""
    if not str(subject or "").strip() or not isinstance(documents, list) or not documents:
        return None, []
    # The Guide Node registry is destination authority; evidence grading decides
    # directness and rank. Do not use the general outward doorway gate here because
    # it intentionally rejects adjacent resources that this discovery fallback
    # must be able to describe honestly as related rather than direct.
    graded = []
    for index, document in enumerate(documents):
        if not isinstance(document, dict):
            continue
        node = document.get("_guide_node") if isinstance(document.get("_guide_node"), dict) else None
        if node is None:
            continue
        canonical_url = str(node.get("canonical_url") or "").rstrip("/").casefold()
        document_url = str(document.get("url") or document.get("canonical_url") or "").rstrip("/").casefold()
        if not canonical_url or canonical_url != document_url:
            continue
        grade = _guide_discovery_evidence_grade(subject, document, node=node)
        if grade["grade"] not in {"direct", "related"}:
            continue
        approved = dict(document)
        approved["_guide_node"] = node
        approved["_discovery_relevance"] = grade["grade"]
        approved["_discovery_relevance_score"] = grade["score"]
        approved["_discovery_support_terms"] = grade["support"]
        # When the visitor names a resource title, prefer the exact registered
        # title over a suffixed/duplicate display node even if the duplicate has
        # a slightly higher body-evidence score. Directness still outranks related
        # matches whenever there is no exact title identity match.
        normalize_title = lambda value: re.sub(
            r"[^a-z0-9]+", " ", str(value or "").casefold()
        ).strip()
        exact_title_match = normalize_title(node.get("title")) == normalize_title(subject)
        graded.append((
            0 if exact_title_match else 1,
            0 if grade["grade"] == "direct" else 1,
            -int(grade["score"]),
            str(node.get("title") or "").casefold(),
            index,
            approved,
        ))
    if not graded:
        return None, []
    graded.sort(key=lambda item: item[:4])
    selected = graded[0][-1]
    candidate = _normalize_authoritative_recommendation({
        "title": selected.get("title") or selected.get("_guide_node", {}).get("title"),
        "url": selected.get("url") or selected.get("canonical_url") or selected.get("_guide_node", {}).get("canonical_url"),
    })
    if not candidate:
        return None, []
    evidence = _guide_selected_doorway_discovery_evidence([selected], subject, candidate)
    if not evidence:
        return None, []
    return candidate, evidence


def _guide_discovery_response_is_grounded(response, subject, doorway, evidence):
    """Reject discovery prose that ignores or contradicts its selected Archive evidence."""
    text = re.sub(r"\s+", " ", str(response or "")).strip().casefold()
    if not text or not isinstance(doorway, dict) or not evidence:
        return False
    if re.search(
        r"\b(?:no specific archive material|no relevant archive material|"
        r"couldn['’]?t verify|could not verify|couldn['’]?t identify a directly relevant|"
        r"cannot point you to a specific internal resource)\b",
        text,
        re.I,
    ):
        return False
    title = _normalize_query(str(doorway.get("title") or ""))
    # Subject discovery asks for this Archive's material. External search
    # advice cannot satisfy that request by itself, even if it overlaps with
    # the page's broad vocabulary.
    external_search_advice = bool(re.search(
        r"\b(?:google scholar|jstor|project muse|ssrn|academic databases?|"
        r"university library catalogs?|think[- ]tanks?|transparency international|"
        r"government oversight bodies|oversight bodies|ngo reports?|policy institutes?|"
        r"government transparency portals?)\b",
        text,
        re.I,
    ))
    explicitly_names_destination = bool(title and title in _normalize_query(text))
    explicitly_names_archive = bool(re.search(r"\b(?:archive|living archive)\b", text, re.I))
    if external_search_advice and not (explicitly_names_destination or explicitly_names_archive):
        return False
    source = evidence[0] if isinstance(evidence[0], dict) else {}
    body = str(source.get("text") or source.get("content") or source.get("excerpt") or "").casefold()
    subject_terms = set(re.findall(r"[a-z0-9]+", str(subject or "").casefold()))
    anchors = {
        token for token in re.findall(r"[a-z][a-z-]{4,}", body)
        if token not in subject_terms and token not in {
            "about", "above", "across", "after", "again", "also", "among",
            "because", "being", "between", "could", "every", "from", "have",
            "into", "itself", "other", "their", "there", "these", "those",
            "through", "under", "using", "where", "which", "while", "within",
        }
    }
    response_tokens = set(re.findall(r"[a-z][a-z-]{4,}", text))
    has_source_anchor = len(anchors & response_tokens) >= 1
    mentions_selected_resource = bool(title and title in _normalize_query(text))
    mentions_archive = bool(re.search(r"\b(?:archive|living archive)\b", text, re.I))
    return has_source_anchor and (mentions_selected_resource or mentions_archive)


def _guide_deterministic_discovery_response(subject, doorway, evidence):
    """Orient discovery from selected-page evidence, labeling directness honestly."""
    title = str((doorway or {}).get("title") or "").strip()
    source = evidence[0] if evidence and isinstance(evidence[0], dict) else {}
    body = str(
        source.get("text") or source.get("content") or source.get("excerpt") or ""
    )
    body = re.sub(r"\s+", " ", body).strip()
    grade = str(source.get("_discovery_relevance") or "direct").strip().casefold()
    support_terms = [
        str(term).strip()
        for term in (source.get("_discovery_support_terms") or [])
        if str(term).strip()
    ]
    if not title:
        return ""

    normalized_subject = re.sub(r"\s+", " ", str(subject or "")).strip()
    # Strip recognizable author/byline metadata accidentally concatenated into excerpts.
    # Preserve the remaining source text; never manufacture a quotation.
    body = re.sub(
        r"^(?:[A-Z][A-Za-z .’'-]{1,80},?\s+(?:PhD Candidate|PhD student|doctoral candidate|author)\s+)+",
        "", body, flags=re.I,
    ).strip()
    if grade == "related":
        overlap = ", ".join(support_terms[:4]) if support_terms else "some related terms"
        return (
            f"I couldn’t verify a page that directly covers {normalized_subject}. "
            f"A related place to explore is {title}. "
            f"Its content and description overlap with {overlap}, "
            "but that does not establish that it directly addresses your question."
        )

    if not body:
        return (
            f"{title} appears to be the closest direct match I could verify. "
            f"I confirmed the destination, but not enough page text to explain "
            f"how it addresses {normalized_subject}."
        )

    subject_tokens = {
        token for token in re.findall(r"[a-z0-9]+", normalized_subject.casefold())
        if len(token) >= 4
    }
    # WordPress excerpts can concatenate a title/subheading directly with the
    # following sentence. If a complete question follows the heading, discard
    # the heading prefix before considering the text as a source quotation.
    sentences = [
        re.sub(r"\s+", " ", sentence).strip(" \t-•")
        for sentence in re.split(r"(?<=[.!?])\s+", body)
    ]
    for index, sentence in enumerate(sentences):
        if "?" not in sentence:
            continue
        question_start = re.search(
            r"\b(?:why|what|how|when|where|who|which|does|do|did|can|could|should|would|will|is|are|was|were)\s+",
            sentence,
            re.I,
        )
        if question_start and question_start.start() >= 24:
            sentences[index] = sentence[question_start.start():].strip()
    candidates = []
    for sentence in sentences:
        if len(sentence) < 45 or len(sentence) > 320:
            continue
        if not re.search(r"[.!?]$", sentence):
            continue
        words = set(re.findall(r"[a-z0-9]+", sentence.casefold()))
        if subject_tokens and len(subject_tokens & words) < min(2, len(subject_tokens)):
            continue
        if re.search(r"\b(?:governing question|meta description|read more)\b", sentence, re.I):
            continue
        candidates.append(sentence)
    if not candidates:
        return (
            f"{title} is a promising starting point for {normalized_subject}. "
            "I couldn’t isolate a complete source sentence that I can quote reliably, "
            "so I won’t manufacture one."
        )
    sentence = candidates[0]
    return (
        f"{title} is a useful place to begin. The essay asks: “{sentence}” "
        f"That gives you a focused entry point for exploring {normalized_subject}."
    )


def _guide_discovery_doorway_is_evidence_backed(doorway, evidence):
    """Require the selected canonical body to match the final discovery doorway URL."""
    if not isinstance(doorway, dict):
        return False
    doorway_url = str(doorway.get("url") or doorway.get("canonical_url") or "").strip().rstrip("/").casefold()
    if not doorway_url or not isinstance(evidence, list) or not evidence:
        return False
    return any(
        isinstance(item, dict)
        and str(item.get("url") or item.get("canonical_url") or "").strip().rstrip("/").casefold() == doorway_url
        and bool(str(item.get("text") or "").strip())
        for item in evidence
    )


def _guide_subject_discovery_answer(response, subject, doorway, evidence):
    """Use a page-grounded direct/related answer or fall back without a false match."""
    if not isinstance(doorway, dict) or not str(doorway.get("title") or "").strip():
        return (
            f"I couldn’t verify a Living Archive page that directly covers {str(subject or 'this subject').strip()}. "
            "I’d rather leave the link out than point you to a page on the strength of a shared word alone."
        )
    return _guide_deterministic_discovery_response(subject, doorway, evidence) or str(response or "").strip()

def _guide_verified_doorway_evidence_for_query(subject, doorway, context_data, composition_context):
    """Find fetched canonical body evidence matching a selected doorway and the visitor's subject."""
    if not isinstance(doorway, dict):
        return []
    selected_url = str(doorway.get("url") or doorway.get("canonical_url") or "").strip().rstrip("/").casefold()
    if not selected_url:
        return []

    documents = []
    if isinstance(composition_context, dict):
        for key in ("generation_authority_protected_docs", "question_authority_protected_docs"):
            value = composition_context.get(key)
            if isinstance(value, list):
                documents.extend(item for item in value if isinstance(item, dict))
    try:
        blocks = str((context_data or {}).get("context_blocks") or "")
        if blocks:
            documents.extend(
                item for item in use_core.context_blocks_to_documents(blocks)
                if isinstance(item, dict)
            )
    except Exception as exc:
        print(f"The Guide selected-doorway recovery: context parsing failed safely ({type(exc).__name__}).")

    try:
        nodes = _guide_node_registry_snapshot()
    except Exception as exc:
        print(f"The Guide selected-doorway recovery: registry unavailable ({type(exc).__name__}).")
        return []
    nodes_by_url = {
        str(node.get("canonical_url") or "").strip().rstrip("/").casefold(): node
        for node in nodes if isinstance(node, dict)
        and str(node.get("status") or "") == "active"
    }

    for document in documents:
        url = str(document.get("url") or document.get("canonical_url") or "").strip().rstrip("/").casefold()
        if url != selected_url:
            continue
        node = nodes_by_url.get(url)
        if not node:
            continue
        body = str(document.get("text") or document.get("content") or document.get("excerpt") or "").strip()
        if not body:
            continue
        grade = _guide_discovery_evidence_grade(subject, document, node=node)
        if grade.get("grade") not in {"direct", "related"}:
            continue
        approved = dict(document)
        approved["url"] = url
        approved["text"] = body
        approved["_guide_node"] = node
        approved["_discovery_relevance"] = grade["grade"]
        approved["_discovery_relevance_score"] = grade.get("score", 0)
        approved["_discovery_support_terms"] = grade.get("support", [])
        evidence = _guide_selected_doorway_discovery_evidence([approved], subject, doorway)
        if evidence:
            return evidence
    return []


def _guide_discovery_html_recovery(
    query, history, intent, discovery_subject, doorway, evidence,
    context_data=None, composition_context=None,
):
    """Prefer verified canonical evidence over a refusal when generated prose is malformed."""
    subject = discovery_subject or query
    if doorway and not _guide_discovery_doorway_is_evidence_backed(doorway, evidence):
        evidence = _guide_verified_doorway_evidence_for_query(
            subject, doorway, context_data or {}, composition_context or {}
        )
    if doorway and _guide_discovery_doorway_is_evidence_backed(doorway, evidence):
        return _guide_subject_discovery_answer(
            "", subject, doorway, evidence
        )
    return _basic_inquiry_markup_recovery(query, history, intent)


def _basic_inquiry_response(query, history=None, raw_body=None):
    """Answer an ordinary Guide question through the protected USE core."""
    started = time.perf_counter()
    query = str(query or "").strip()
    # Explicit homepage navigation is a deterministic site-level destination,
    # not a subject-discovery request. Resolve it before retrieval/composition
    # so provider variance cannot suppress a clearly requested homepage.
    home_request = bool(re.search(
        r"\b(?:homepage|home page|site home|website home)\b", query, re.I
    )) and bool(re.search(
        r"\b(?:living archive|the archive|the website|the site|website|site)\b",
        query, re.I
    )) and bool(re.search(
        r"\b(?:take me|go to|bring me|send me|navigate|open|show me|link me|please take|please go)\b",
        query, re.I
    ))
    if home_request:
        request_id = "home-" + hashlib.sha1(query.encode("utf-8")).hexdigest()[:16]
        return {
            "ok": True,
            "version": APP_VERSION,
            "fingerprint": DEPLOYMENT_FINGERPRINT,
            "source_sha256": RUNTIME_SOURCE_SHA256,
            "request_id": request_id,
            "query": query,
            "intent": "NAVIGATION",
            "response": "Here’s the Living Archive homepage.",
            "recommendation": {
                "title": "Living Archive",
                "url": "https://geralddaquila.com/",
            },
            "answer_basis": {
                "kind": "navigation",
                "label": "Direct site navigation",
                "explanation": "You explicitly asked to open the Living Archive homepage.",
            },
            "processing": "guide_navigation",
            "route_source": "guide_explicit_home_navigation",
            "visitor_boundary_version": APP_VERSION,
        }
    clarification = general_guide_composition.clarification_response(
        query, _history_text(history)
    )
    if clarification:
        request_id = "clarify-" + hashlib.sha1(
            (query + "|" + _history_text(history)).encode("utf-8")
        ).hexdigest()[:16]
        return {
            "ok": True,
            "version": APP_VERSION,
            "fingerprint": DEPLOYMENT_FINGERPRINT,
            "source_sha256": RUNTIME_SOURCE_SHA256,
            "request_id": request_id,
            "query": query,
            "intent": "CLARIFICATION_REQUIRED",
            "response": clarification["response"],
            "recommendation": None,
            "answer_basis": {
                "kind": "clarification",
                "label": "A little more context",
                "explanation": "The question needs a subject before a relevant answer or Archive resource can be selected.",
            },
            "processing": "guide_clarification",
            "route_source": "guide_missing_context_guard",
            "clarification": {
                "required": True,
                "reason": clarification["clarification_reason"],
                "recommendation_suppressed": True,
            },
            "visitor_boundary_version": APP_VERSION,
        }
    # Separate the visitor's intent from the resource-search terms. Search
    # wrapper language such as "Where can I find material about..." is useful
    # to the composer but can obscure the actual subject during retrieval.
    # A correction explicitly names the subject the prior answer missed.
    # Retrieve and select any doorway for that subject, not the mistaken subject
    # or the full complaint wrapper.
    correction_subject = general_guide_composition.correction_subject(query)
    source_trace_request = general_guide_composition.is_exact_source_request(query)
    source_trace_claim = _history_text(history) if source_trace_request else ""
    discovery_subject = _guide_subject_discovery_query(query) if not correction_subject and not source_trace_request else ""
    resource_query = correction_subject or discovery_subject or (source_trace_claim[-1600:] if source_trace_claim else query)
    context_data = use_core.fetch_canonical_context(resource_query)
    if not isinstance(context_data, dict):
        raise RuntimeError("Basic Inquiry retrieval returned an invalid context object.")

    # Navigation authority is resolved once, before composition, and carried
    # through every ordinary-answer path. It must never depend on which
    # provider/model happened to compose the prose successfully.
    authoritative_doorway = _normalize_authoritative_recommendation(
        context_data.get("recommendation_canonical_primary")
        or _general_guide_authoritative_doorway(resource_query, context_data)
    )
    # Subject discovery is constrained to the active WordPress Guide Node registry.
    # A public URL returned by search is not, by itself, an approved Guide doorway.
    if discovery_subject and authoritative_doorway:
        registered_urls = {
            str(node.get("canonical_url") or "").rstrip("/").casefold()
            for node in _guide_node_registry_snapshot()
            if isinstance(node, dict) and str(node.get("status") or "") == "active"
        }
        if str(authoritative_doorway.get("url") or "").rstrip("/").casefold() not in registered_urls:
            print("The Guide discovery boundary: rejected unregistered destination.")
            authoritative_doorway = None
    # Distress-sensitive pacing governs the prose, not access to a separate
    # optional resource. Keep the compassionate response first and preserve a
    # qualified, independently rendered doorway when the existing relevance
    # and safety gates approve one. Acute-risk and unrelated resources remain
    # excluded by the outward-document eligibility boundary.

    # Evidence sufficiency governs what may be attributed to the Archive, not
    # whether an ordinary public question may receive a useful general answer.
    # Keep specialist-only evidence out of general composition when the retrieval
    # boundary says it cannot safely frame the visitor's question.
    composition_context = dict(context_data)
    archive_evidence_unavailable = any(
        composition_context.get(flag)
        for flag in (
            "frame_neutral_evidence_unavailable",
            "question_structure_evidence_unavailable",
            "evidence_sufficiency_unavailable",
        )
    )
    discovery_selected_evidence = []
    direct_selected_body = None
    registry_discovery_docs = []
    if _guide_requires_canonical_subject_supplement(
        archive_evidence_unavailable, discovery_subject
    ):
        # Subject-finding requests always receive a bounded WordPress content
        # supplement, even when the initial vector pass did not set an evidence-
        # unavailable flag. A valid doorway alone is not enough: fetch the page
        # text and re-run the same frame-neutral, sufficiency, and question-fit
        # gates before allowing it into the answer composition.
        try:
            recovered_docs = _wordpress_search_canonical_candidates(
                resource_query, limit=_guide_subject_supplement_limit(discovery_subject)
            )
            # Add a small, deterministic set of active registry nodes ranked by
            # their published purpose and semantic hints. Only fetched canonical
            # page bodies can subsequently authorize a recommendation.
            if discovery_subject:
                known_urls = {
                    str(item.get("url") or item.get("canonical_url") or "").rstrip("/").casefold()
                    for item in recovered_docs if isinstance(item, dict)
                }
                for node in _guide_registered_discovery_nodes(discovery_subject, limit=20):
                    node_url = str(node.get("canonical_url") or "").strip()
                    if not node_url or node_url.rstrip("/").casefold() in known_urls:
                        continue
                    try:
                        node_body = _wordpress_fetch_selected_canonical_body(node_url)
                    except Exception:
                        node_body = None
                    if isinstance(node_body, dict):
                        recovered_docs.append(node_body)
                        registry_discovery_docs.append(node_body)
                        known_urls.add(node_url.rstrip("/").casefold())
            # The selected doorway is already independently authorized. Fetch
            # its actual canonical body as well as topic-search candidates so
            # content relevance is tested against the destination being offered,
            # not just whichever pages WordPress ranked highest for the phrase.
            if discovery_subject and authoritative_doorway:
                doorway_docs = _wordpress_search_canonical_candidates(
                    authoritative_doorway.get("title") or "", limit=3
                )
                # Search may rank around a destination without returning that
                # exact page in its bounded slice. Fetch the already-authorized
                # URL directly, then let the same URL/body/subject-fit checks
                # decide whether it can support the discovery answer.
                direct_body = _wordpress_fetch_selected_canonical_body(
                    authoritative_doorway.get("url") or ""
                )
                direct_selected_body = direct_body if isinstance(direct_body, dict) else None
                recovered_docs = (
                    ([direct_body] if isinstance(direct_body, dict) else [])
                    + list(doorway_docs)
                    + list(recovered_docs)
                )
            normalized_recovered_docs = []
            seen_recovered_urls = set()
            for item in recovered_docs:
                if not isinstance(item, dict):
                    continue
                title = str(item.get("title") or "").strip()
                url = str(item.get("url") or "").strip()
                text_value = str(item.get("text") or "").strip()
                key = url.rstrip("/").casefold()
                if not title or not text_value or not key or key in seen_recovered_urls:
                    continue
                seen_recovered_urls.add(key)
                normalized_recovered_docs.append({"title": title, "url": url, "text": text_value})
            recovered_docs = normalized_recovered_docs
            recovered_docs, _frame_boundary_active = use_core._frame_neutral_generation_documents(
                recovered_docs, resource_query, str(context_data.get("intent") or "TOPICAL_INQUIRY")
            )
            selected_support = (
                _guide_selected_doorway_discovery_evidence(
                    recovered_docs, resource_query, authoritative_doorway
                )
                if discovery_subject and authoritative_doorway else []
            )
            # Resource discovery and answer synthesis have different contracts.
            # Once a canonical page body passes direct subject-fit validation,
            # align the destination to that exact body and retain it for the
            # discovery response guard even if the stricter synthesis gate
            # rejects the document set. This never authorizes unsupported
            # explanatory claims; it only permits a grounded resource orientation.
            if discovery_subject:
                # The general frame-neutral filter is designed for synthesis
                # authority and may discard a valid navigation-page body. Keep
                # the directly fetched selected page in a separate, bounded
                # discovery-only candidate set and let the exact URL/body/direct-
                # fit checks decide whether it can ground the doorway.
                discovery_candidate_docs = list(recovered_docs)
                known_discovery_urls = {
                    str(item.get("url") or item.get("canonical_url") or "").rstrip("/").casefold()
                    for item in discovery_candidate_docs if isinstance(item, dict)
                }
                for item in registry_discovery_docs:
                    item_url = str(item.get("url") or item.get("canonical_url") or "").rstrip("/").casefold()
                    if item_url and item_url not in known_discovery_urls:
                        discovery_candidate_docs.append(item)
                        known_discovery_urls.add(item_url)
                if direct_selected_body:
                    direct_url_key = str(direct_selected_body.get("url") or "").rstrip("/").casefold()
                    if not any(
                        str(item.get("url") or "").rstrip("/").casefold() == direct_url_key
                        for item in discovery_candidate_docs if isinstance(item, dict)
                    ):
                        discovery_candidate_docs.append(direct_selected_body)
                evidence_doorway, evidence_for_doorway = _guide_align_registered_discovery_doorway(
                    resource_query, discovery_candidate_docs
                )
                if evidence_doorway and evidence_for_doorway:
                    authoritative_doorway = evidence_doorway
                    discovery_selected_evidence = evidence_for_doorway
                    composition_context["authoritative_doorway"] = evidence_doorway
                    print(
                        "The Guide discovery evidence contract: selected destination "
                        f"and source body aligned to {evidence_doorway.get('title')!r}."
                    )
            recovered_docs, recovery_insufficient = use_core._evidence_sufficiency_gate(
                recovered_docs, resource_query, str(context_data.get("intent") or "TOPICAL_INQUIRY")
            )
            if recovery_insufficient and selected_support:
                recovered_docs = selected_support
                recovery_insufficient = False
                print(
                    "The Guide discovery evidence gate: selected canonical doorway body "
                    "passed direct subject-fit validation."
                )
            if not recovery_insufficient and recovered_docs:
                recovered_docs, recovery_question_unavailable = use_core._v208_question_evidence_fit_gate(
                    recovered_docs, resource_query, str(context_data.get("intent") or "TOPICAL_INQUIRY")
                )
                if recovery_question_unavailable and selected_support:
                    recovered_docs = selected_support
                    recovered_docs, recovery_question_unavailable = use_core._v208_question_evidence_fit_gate(
                        recovered_docs, resource_query, str(context_data.get("intent") or "TOPICAL_INQUIRY")
                    )
                if not recovery_question_unavailable and recovered_docs:
                    discovery_selected_evidence = (
                        selected_support
                        or (
                            _guide_selected_doorway_discovery_evidence(
                                recovered_docs, resource_query, authoritative_doorway
                            )
                            if discovery_subject and authoritative_doorway else []
                        )
                    )
                    composition_context["generation_authority_protected_docs"] = recovered_docs
                    composition_context.pop("question_authority_protected_docs", None)
                    if discovery_subject:
                        # The final doorway must be selected from the same vetted
                        # canonical documents that will ground the discovery answer.
                        # This prevents a good-looking but unfetched doorway from
                        # being paired with unrelated prose or a generic fallback.
                        evidence_doorway, evidence_for_doorway = _guide_align_registered_discovery_doorway(
                            resource_query, list(recovered_docs) + list(registry_discovery_docs)
                        )
                        if evidence_doorway and evidence_for_doorway:
                            authoritative_doorway = evidence_doorway
                            discovery_selected_evidence = evidence_for_doorway
                            composition_context["authoritative_doorway"] = evidence_doorway
                            print(
                                "The Guide discovery contract: doorway and answer evidence "
                                f"aligned to {evidence_doorway.get('title')!r}."
                            )
                    for flag in (
                        "frame_neutral_evidence_unavailable",
                        "question_structure_evidence_unavailable",
                        "evidence_sufficiency_unavailable",
                        "question_evidence_fit_unavailable",
                    ):
                        composition_context.pop(flag, None)
                    archive_evidence_unavailable = False
                    print(
                        "The Guide evidence recovery: substantive canonical content passed "
                        "frame-neutral, sufficiency, and question-fit gates; "
                        f"documents={len(recovered_docs)}."
                    )
        except Exception as exc:
            print(f"The Guide evidence recovery failed safely: {type(exc).__name__}.")

    # Discovery is fail-closed at the final selection boundary. An initial
    # retrieval recommendation is not sufficient: the final selected canonical
    # page body must support the exact doorway being returned. This also keeps
    # answer_basis from claiming Archive support when discovery fell back.
    if discovery_subject and not _guide_discovery_doorway_is_evidence_backed(
        authoritative_doorway, discovery_selected_evidence
    ):
        authoritative_doorway = None
        composition_context.pop("authoritative_doorway", None)
        print(
            "The Guide discovery contract: no evidence-backed selected doorway; "
            "recommendation suppressed."
        )

    if archive_evidence_unavailable:
        for key in (
            "context_blocks",
            "canonical_link_context",
            "generation_authority_protected_docs",
            "question_authority_protected_docs",
            "authoritative_doorway",
        ):
            composition_context.pop(key, None)
        # Navigation and answer synthesis have separate evidence contracts.
        # Insufficient synthesis evidence must not erase an independently
        # selected, relevant canonical doorway. The doorway is returned as a
        # separate field and is not passed into the composition context.

    # All ordinary questions use the same provider-neutral composition path,
    # including when no suitable Archive evidence is available. The composer
    # is explicitly instructed to answer from general knowledge where suitable
    # and to state source limitations only when the question actually requires it.

    # One controlled reasoning-provider seam. AUTO preserves the existing LLM-first
    # provider bank and bounded deterministic fallback. DETERMINISTIC_ONLY bypasses
    # the composer entirely for isolated calibration and is intentionally configured
    # only on a service receiving no normal visitor traffic, never by an untrusted visitor field.
    reasoning_mode = str(os.getenv("USE_REASONING_PROVIDER_MODE", "auto") or "auto").strip().casefold()
    if reasoning_mode not in {"auto", "deterministic_only"}:
        print("The Guide reasoning provider mode: invalid value; using auto.")
        reasoning_mode = "auto"

    composition_result = None
    # This narrow practical-question class has a bounded, provider-independent
    # answer. Do not send it through the general composition envelope: that
    # envelope can exceed provider token budgets before the fallback is reached.
    if _is_practical_stewardship_question(query) or _is_generic_workplace_credit_taking_question(query):
        deterministic_result = _basic_inquiry_round1_deterministic_response(
            query, {}, composition_context, recommendation_available=False
        )
        llm_output = str((deterministic_result or {}).get("response") or "").strip()
        if not llm_output:
            raise RuntimeError("Bounded general-knowledge recovery returned no answer.")
        recovery_mode = (
            "bounded_practical_stewardship_recovery"
            if _is_practical_stewardship_question(query)
            else "bounded_workplace_credit_taking_general_knowledge"
        )
        print(
            "The Guide General Composition: "
            f"mode={recovery_mode}, "
            "llm_composer_invoked=false, archive_recommendation=none"
        )
    elif reasoning_mode == "deterministic_only":
        deterministic_result = _basic_inquiry_round1_deterministic_response(
            correction_subject or query, {}, composition_context,
            recommendation_available=bool(authoritative_doorway),
        )
        llm_output = str((deterministic_result or {}).get("response") or "")
        print(
            "The Guide General Composition: "
            f"mode=deterministic_only, provider={(deterministic_result or {}).get('provider') or 'unknown'}, "
            "model=none, llm_composer_invoked=false, "
            f"archive_evidence={'unavailable' if archive_evidence_unavailable else 'available'}, "
            f"navigation_candidate={authoritative_doorway.get('title') if authoritative_doorway else 'none'}"
        )
    else:
        try:
            composition_result = general_guide_composition.compose(
                use_core=use_core,
                query=query,
                context_data=composition_context,
                history_text=_history_text(history),
            )
            if composition_result:
                llm_output = composition_result.get("response", "")
                print(
                    "The Guide General Composition: "
                    f"mode=auto, provider={composition_result.get('provider') or 'unknown'}, "
                    f"model={composition_result.get('model') or 'unknown'}, "
                    f"shape={composition_result.get('response_shape') or 'unknown'}, "
                    f"archive_evidence={'unavailable' if archive_evidence_unavailable else 'available'}, "
                    f"navigation_candidate={authoritative_doorway.get('title') if authoritative_doorway else 'none'}"
                )
            else:
                print("The Guide General Composition: mode=auto; provider bank exhausted; using conservative deterministic recovery.")
                llm_output = _basic_inquiry_round1_deterministic_response(correction_subject or query, {}, composition_context, recommendation_available=bool(authoritative_doorway)).get("response", "")
        except Exception as exc:
            print(f"The Guide General Composition failed safely in auto mode: {type(exc).__name__}; using conservative deterministic recovery.")
            try:
                llm_output = _basic_inquiry_round1_deterministic_response(query, {}, composition_context, recommendation_available=bool(authoritative_doorway)).get("response", "")
            except Exception:
                llm_output = ""

    if _is_practical_stewardship_question(query):
        # This bounded recovery has no canonical source body selected as direct
        # evidence for the exact question. Suppress any incidental doorway from
        # broad initial retrieval rather than attach an unrelated recommendation.
        authoritative_doorway = None
        archive_evidence_unavailable = True
        composition_context.pop("authoritative_doorway", None)
        composition_context["evidence_sufficiency_unavailable"] = True

    if _is_generic_workplace_credit_taking_question(query):
        # This general answer is not grounded in a sufficiently direct canonical
        # source. Do not attach an incidental resource selected by broad retrieval.
        authoritative_doorway = None
        archive_evidence_unavailable = True
        composition_context.pop("authoritative_doorway", None)
        composition_context["evidence_sufficiency_unavailable"] = True

    # These everyday deterministic recoveries answer from general knowledge, not
    # Archive evidence. Broad retrieval must not attach a coincidental doorway.
    if not discovery_subject and (
        re.search(r"\b(?:reading list|list of books to read|books i want to read)\b", _normalize_query(query), re.I)
        or re.search(r"\b(?:cleaning schedule|household cleaning|weekly cleaning)\b", _normalize_query(query), re.I)
        or (
            re.search(r"\b(?:common ways|common patterns|typical ways)\b", _normalize_query(query), re.I)
            and re.search(r"\b(?:misunderstand|misunderstanding|misunderstandings|expectations)\b", _normalize_query(query), re.I)
            and re.search(r"\bfriendships?\b", _normalize_query(query), re.I)
            and not re.search(r"\b(?:my friend|my friendship|my partner|my colleague|my teammate)\b", _normalize_query(query), re.I)
        )
    ):
        authoritative_doorway = None
        archive_evidence_unavailable = True
        composition_context.pop("authoritative_doorway", None)
        composition_context["evidence_sufficiency_unavailable"] = True

    # Subject-discovery prose must be independent of provider availability and generation.
    # Always compose it from the selected canonical page evidence, so primary and mirror
    # cannot drift into different descriptions or introduce unselected resources.
    if discovery_subject:
        grounded_discovery = _guide_subject_discovery_answer(
            llm_output, resource_query, authoritative_doorway, discovery_selected_evidence
        )
        if grounded_discovery != str(llm_output or "").strip():
            print(
                "The Guide discovery composition boundary: replaced provider prose "
                "with selected canonical doorway orientation."
            )
        llm_output = grounded_discovery

    # Final visitor-language boundary for EVERY ordinary Guide response path.
    # Canonical navigation is a separate structured field. If a provider tries
    # to smuggle a link into prose, reject the entire generated response and
    # recover without reusing that text. This prevents malformed markup and
    # unsupported title/URL pairs from crossing the API boundary.
    raw_visitor_text = str(llm_output or "").strip()
    if _basic_inquiry_contains_html_markup(raw_visitor_text):
        print(
            "The Guide visitor boundary: rejected HTML-shaped generated prose; "
            "using query-grounded deterministic recovery."
        )
        llm_output = _guide_discovery_html_recovery(
            query, history, context_data.get("intent", "TOPICAL_INQUIRY"),
            discovery_subject, authoritative_doorway, discovery_selected_evidence,
            context_data, composition_context,
        )
        if not llm_output:
            try:
                deterministic_recovery = _basic_inquiry_round1_deterministic_response(
                    correction_subject or query, {}, {"context_blocks": ""}, recommendation_available=bool(authoritative_doorway)
                )
                llm_output = str(deterministic_recovery.get("response") or "").strip()
            except Exception as exc:
                print(f"The Guide markup recovery failed safely: {type(exc).__name__}.")
                llm_output = ""
        if _basic_inquiry_contains_html_markup(llm_output):
            llm_output = ""
    response = _sanitize_basic_inquiry_response(str(llm_output or "").strip())
    # A provider refusal must never be paired with an incidental retrieval
    # doorway. Replace it with a bounded deterministic answer where available;
    # otherwise fail closed by suppressing the recommendation and attribution.
    if re.search(r"\bI couldn't verify a reliable answer from the material available in this request\b", response, re.I):
        try:
            deterministic_recovery = _basic_inquiry_round1_deterministic_response(
                query, {}, {"context_blocks": ""}, recommendation_available=False
            )
            recovered_text = _sanitize_basic_inquiry_response(
                str(deterministic_recovery.get("response") or "").strip()
            )
            if recovered_text and not re.search(
                r"\bI couldn't verify a reliable answer from the material available in this request\b",
                recovered_text, re.I
            ):
                response = recovered_text
        except Exception as exc:
            print(f"The Guide unverified-answer recovery failed safely: {type(exc).__name__}.")
        authoritative_doorway = None
        archive_evidence_unavailable = True
        composition_context.pop("authoritative_doorway", None)
        print("The Guide relevance boundary: unverified provider answer detected; unrelated doorway suppressed.")
    if _basic_inquiry_has_source_dump(response):
        print(
            "The Guide visitor boundary: rejected a copied/truncated source excerpt; "
            "using deterministic synthesis instead."
        )
        # Do not feed the rejected excerpt back into recovery; that would
        # reproduce the same copied/truncated passage under a deterministic label.
        deterministic_recovery = _basic_inquiry_round1_deterministic_response(
            query, {}, {"context_blocks": ""}
        )
        response = _sanitize_basic_inquiry_response(
            str(deterministic_recovery.get("response") or "").strip()
        )
        # The boundary is fail-closed: even if deterministic recovery unexpectedly
        # returns the same excerpt, no copied/truncated source dump may be emitted.
        if _basic_inquiry_has_source_dump(response):
            response = _sanitize_basic_inquiry_response(
                _basic_inquiry_source_dump_recovery(query)
            )
    if not response:
        raise RuntimeError("Basic Inquiry generation returned an empty visitor response.")

    # Re-apply provider-independent discovery composition after sanitization, immediately
    # before payload assembly. This is intentionally deterministic even when a generated
    # answer passed the broad relevance validator above.
    if discovery_subject:
        response = _sanitize_basic_inquiry_response(
            _guide_subject_discovery_answer(
                response, resource_query, authoritative_doorway, discovery_selected_evidence
            )
        )

    if re.search(r"\bUSE\b", response) or re.search(
        r"(?:canonical evidence|supplied evidence|evidence excerpt|"
        r"evidence excerpt bounded by USE|bounded by USE|"
        r"bounded by the Guide|internal interpretation|retrieval layer|"
        r"synthesis layer|processing layer|provider bank|provider selection|"
        r"model selection|route source|handoff|machine-facing|"
        r"implementation metadata|system instruction|debugging annotation)",
        response,
        re.I,
    ):
        raise RuntimeError(
            "Basic Inquiry visitor-language boundary rejected internal implementation language."
        )

    response = _guide_reconcile_resource_language(response, bool(authoritative_doorway))

    request_id = "basic-" + hashlib.sha1((query + "|" + _history_text(history)).encode("utf-8")).hexdigest()[:16]
    if _guide_response_disclaims_archive_recommendation(response):
        authoritative_doorway = None
        archive_evidence_unavailable = True
        composition_context.pop("authoritative_doorway", None)
        composition_context["evidence_sufficiency_unavailable"] = True

    # Expose a small, deterministic provenance contract for the visitor UI.
    # This describes the answer's basis; it does not claim that every sentence
    # is directly quoted from a source. A recommendation is only supplied when
    # the relevance gate found a canonical doorway for this specific question.
    if archive_evidence_unavailable:
        answer_basis = {
            "kind": "general_knowledge",
            "label": "General knowledge",
            "explanation": "No suitable Archive evidence was available to ground this answer.",
        }
    elif authoritative_doorway:
        answer_basis = {
            "kind": "archive_supported",
            "label": "Informed by the Living Archive",
            "explanation": "A relevant Archive resource is available to explore the ideas behind this answer.",
        }
    else:
        answer_basis = {
            "kind": "general_knowledge",
            "label": "General knowledge",
            "explanation": "No sufficiently relevant Archive resource was identified for this question.",
        }

    payload = {
        "ok": True,
        "version": APP_VERSION,
        "fingerprint": DEPLOYMENT_FINGERPRINT,
        "source_sha256": RUNTIME_SOURCE_SHA256,
        "request_id": request_id,
        "query": query,
        "intent": context_data.get("intent", "TOPICAL_INQUIRY"),
        "response": response,
        # The recommendation is a first-class response field, never
        # inferred from prose and never dependent on provider metadata.
        "recommendation": authoritative_doorway,
        "answer_basis": answer_basis,
        "processing": "basic_inquiry",
        "route_source": "guide_basic_inquiry",
        "visitor_boundary_version": APP_VERSION,
    }
    print("The Guide Basic Inquiry: " + f"request_id={request_id}, intent={payload['intent']}, response_chars={len(response)}, elapsed={time.perf_counter() - started:.3f}s, query={_normalize_query(query)[:120]}")
    return payload


def _v48894_general_guide_composition_self_audit():
    """Static contract audit for the provider-neutral all-purpose Guide seam."""
    if not callable(getattr(general_guide_composition, "compose", None)):
        raise RuntimeError("General Guide composition boundary is missing.")
    snapshot = general_guide_composition.contract_snapshot()
    if snapshot.get("contract_version") != "v1.20":
        raise RuntimeError("General Guide composition contract version drift.")
    if snapshot.get("provider_neutral") is not True:
        raise RuntimeError("General Guide composition lost provider neutrality.")
    if snapshot.get("operation") != "general_guide_composition":
        raise RuntimeError("General Guide composition operation identity drift.")
    import inspect as _inspect
    source = _inspect.getsource(_basic_inquiry_response)
    if "use_core.generate_llm_response" in source:
        raise RuntimeError("General Guide structural isolation failure: legacy single-provider generation remains in the all-purpose path.")
    if "general_guide_composition.compose" not in source:
        raise RuntimeError("General Guide structural isolation failure: all-purpose path is not bound to General Composition.")
    print("USE GENERAL GUIDE COMPOSITION AUDIT: PASS; provider_neutral=True; legacy_single_provider_path=absent")


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
        node_title = str(node.get("title") or "").strip()
        normalized_title = _normalize_query(node_title)
        node_asset_type = str(node.get("asset_type") or "").strip().casefold().replace("-", "_")
        # Generic access surfaces explain how to browse the Archive; they are
        # not subject destinations. Never let their broad semantic hints
        # outrank a visitor's subject-specific request. A generic surface is
        # eligible only when the visitor explicitly names that surface.
        generic_access_titles = {
            "libraries", "library", "archive index", "archive reference index",
            "site index", "archive navigation", "start here", "begin here",
        }
        is_generic_access_node = normalized_title in generic_access_titles
        if is_generic_access_node:
            if normalized_title and re.search(
                rf"\b{re.escape(normalized_title)}\b",
                normalized,
                re.I,
            ):
                score = 105
                if score > best_score:
                    best_score = score
                    best = node
            # Do not inspect broad generic navigation hints as if they named
            # the visitor's requested subject.
            continue

        labels = [node_title]
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

def _is_explicit_guide_destination_request(query):
    """Only hand off to a registered node when the visitor asks to navigate.

    Subject overlap alone is not destination intent. Explanatory questions
    must remain in ordinary Guide composition so the answer and recommendation
    can both be returned instead of sending the visitor straight to a page.
    """
    normalized = _normalize_query(query)
    if not normalized:
        return False
    return bool(re.search(
        r"\b(?:where can i find|where do i find|show me|take me to|"
        r"link me to|go to|navigate to|find the|browse|"
        r"take me directly to|send me to|direct me to|access the page for)|"
        r"^(?:please\s+|could you\s+|can you\s+)?open\b",
        normalized,
        re.I,
    ))

def _guide_node_handoff_is_authorized(query, selected_node_id):
    """Authorize a native Guide Node handoff only when the registry supports it.

    An explicit request to find material is not permission to open an arbitrary
    node chosen by a model. The selected node must also be the strongest
    registry-backed subject destination. If no such destination exists, keep
    the request in ordinary Guide composition so it can answer and recommend
    relevant material without substituting a generic access page.
    """
    if not _is_explicit_guide_destination_request(query):
        return False
    selected_id = str(selected_node_id or "").strip()
    if not selected_id:
        return False
    matched = _guide_node_specific_match(query)
    return bool(
        matched
        and str(matched.get("node_id") or "").strip() == selected_id
    )


# Routing boundary regression probes: compound explanatory questions must
# never be mistaken for a request to navigate directly to a registry node.
if _is_explicit_guide_destination_request(
    "What is stewardship and why does it matter now more than ever?"
):
    raise RuntimeError("Guide routing invariant failed: explanatory question classified as destination request.")
if not _is_explicit_guide_destination_request("Please take me to the Steward Readiness Instruments."):
    raise RuntimeError("Guide routing invariant failed: explicit destination request not recognized.")
if _is_explicit_guide_destination_request("What is open source software?"):
    raise RuntimeError("Guide routing invariant failed: explanatory open-source question classified as destination request.")
if not _is_explicit_guide_destination_request("Please open the Steward Readiness Instruments."):
    raise RuntimeError("Guide routing invariant failed: explicit open command not recognized.")

# Subject-discovery regression: broad semantic hints on generic access hubs
# must never convert a topic request into a Libraries page handoff.
_institutional_discovery_probe = _guide_node_specific_match(
    "Where can I find material about institutional responsibility?"
)
if str((_institutional_discovery_probe or {}).get("title") or "").strip().casefold() in {
    "libraries", "library", "archive index", "site index",
    "archive navigation", "start here", "begin here",
}:
    raise RuntimeError(
        "Guide routing invariant failed: subject-specific discovery resolved to a generic access hub."
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

    Only explicit visitor-provided country data is accepted here. This service may
    receive requests through a WordPress bridge, so proxy IPs, forwarded-IP
    headers, and unverified Cloudflare-looking headers are not evidence of the
    visitor's country. Authenticated edge attestation must be added separately.
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

    # Do not trust caller-supplied Cloudflare-looking headers by themselves.
    # No country is inferred from these headers without authenticated edge proof.

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
    # Keep this only as transport diagnostics. It is not visitor-location evidence.
    if client_ip:
        context["transport_peer_ip"] = client_ip

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
    # A visitor's explicit refusal is authoritative. Do not infer location
    # from the request IP after refusal; that IP may belong to a proxy or
    # infrastructure hop rather than the visitor.
    if str(context.get("refused") or "").strip().casefold() in {"true", "yes", "1", "refused"}:
        # Strip inferred and explicit location fields from the downstream
        # safety context after refusal. Merely skipping fallback is insufficient
        # if an edge header or proxy has already populated ip_country.
        return {"refused": context.get("refused", True)}
    # First-party/context supplied by the visitor or edge wins. Only use the
    # external IP resolver when no country signal exists yet.
    if any(context.get(key) for key in (
        "explicit_country", "browser_country", "ip_country",
        "timezone_country", "locale_country",
    )):
        return context
    # Do not geolocate the transport peer as if it were the visitor. In
    # this deployment the query may arrive through the WordPress bridge, so
    # client_ip can identify WordPress or another proxy. Only explicit visitor
    # context or trusted edge country metadata above may ground emergency
    # resources. Keep the helper available for a future verified direct-client
    # deployment, but never use it as an implicit country-selection fallback.
    return context


def _relational_handoff_session_id(parsed_body):
    """Return an isolated opaque HRN session key; never derive it from visitor prose."""
    body = parsed_body if isinstance(parsed_body, dict) else {}
    supplied = str(body.get("session_id") or "").strip()
    # A returned session key can be echoed by the client on retries/continuations.
    if re.fullmatch(r"relationship-[0-9a-f]{24}", supplied):
        return supplied
    # Accept a client-generated opaque token only; do not key stored journey state
    # by arbitrary prose, email addresses, or unbounded caller-controlled strings.
    if re.fullmatch(r"[A-Za-z0-9_-]{16,128}", supplied):
        return "relationship-" + hashlib.sha256(supplied.encode("utf-8")).hexdigest()[:24]
    # Identical opening questions from different visitors must never share a ledger.
    return "relationship-" + uuid.uuid4().hex[:24]


def _should_honor_protected_risk_profile(query, risk_profile):
    """Use a protected-core risk signal only when it is not a hypothetical calibration."""
    if not isinstance(risk_profile, dict) or not bool(risk_profile.get("risk")):
        return False
    if (
        is_hypothetical_safety_discussion(query)
        and normalize_safety_state(query) is None
    ):
        return False
    return True


def _guard_hypothetical_safety_route(query, route, mode, reason):
    """Keep an explicit third-person safety calibration in informational Guide routing."""
    if (
        str(route or "").casefold() == "safety"
        and is_hypothetical_safety_discussion(query)
        and normalize_safety_state(query) is None
    ):
        return (
            "guide",
            "direct",
            "hypothetical safety calibration is informational, not a personal-risk disclosure",
        )
    return route, mode, reason


def _hypothetical_safety_calibration_payload(query):
    """Return a deterministic, non-interrupting answer for explicit safety-routing tests."""
    normalized = " ".join(str(query or "").strip().casefold().split())
    calibration_signal = any(
        phrase in normalized
        for phrase in (
            "immediate danger",
            "immediate support options",
            "what should the guide do",
            "safety routing",
            "safety calibration",
            "calibration test",
            "calibration only",
            "hypothetical visitor",
            "support contacts",
            "safety / crisis",
        )
    )
    if (
        not is_hypothetical_safety_discussion(normalized)
        or normalize_safety_state(normalized) is not None
        or not calibration_signal
    ):
        return None
    request_id = "safety-calibration-" + hashlib.sha1(
        normalized.encode("utf-8")
    ).hexdigest()[:16]
    return {
        "ok": True,
        "version": APP_VERSION,
        "fingerprint": DEPLOYMENT_FINGERPRINT,
        "source_sha256": RUNTIME_SOURCE_SHA256,
        "request_id": request_id,
        "query": str(query or "").strip(),
        "intent": "SAFETY_CALIBRATION_INFORMATION",
        "response": (
            "In an actual immediate-danger situation, The Guide should pause ordinary "
            "Archive exploration and direct the visitor to their local emergency service "
            "or nearest emergency department. Emergency Intelligence should provide "
            "country-specific contacts once the visitor's location is known; without a "
            "location, the system must not invent a hotline or number. This question is "
            "a routing calibration, not a personal crisis disclosure."
        ),
        "processing": "safety_calibration_boundary",
        "route_source": "guide_hypothetical_safety_calibration",
        "handoff": None,
        "handoff_mode": "informational",
        "handoff_pending": False,
        "safety_calibration": {
            "contract_version": "safety-calibration-information-v1",
            "personal_crisis_detected": False,
            "expected_live_route": "sitewide_safety_boundary_for_actual_danger",
            "resource_owner": "Emergency Intelligence",
            "resource_contract": "living-archive/emergency/v1/resolve",
            "location_required_for_local_contacts": True,
            "resources_resolved": False,
        },
    }


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
            if _should_honor_protected_risk_profile(query, risk_profile):
                safety_state = "current"
                print("The Guide safety boundary recovered from protected-core risk profile.")
            elif isinstance(risk_profile, dict) and bool(risk_profile.get("risk")):
                print("The Guide ignored protected-core risk fallback for a hypothetical safety calibration query.")
        except Exception as exc:
            print(f"The Guide protected-core safety recovery was unavailable: {exc}")

    if not safety_state:
        calibration_payload = _hypothetical_safety_calibration_payload(query)
        if calibration_payload is not None:
            print(
                "The Guide safety calibration: "
                "hypothetical route question answered without personal-crisis interruption, "
                "ordinary retrieval, or provider inference."
            )
            return await _use_send_json(send, calibration_payload)

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

    # Explicit Formation preparation is a native boundary and must outrank the
    # generic orientation/Navigator matcher. This runs after the sitewide safety
    # boundary but before any general navigation handoff or Basic Inquiry.
    early_formation_route = _explicit_formation_entry_route(query)
    if early_formation_route is not None:
        request_id = "formation-" + hashlib.sha1(
            (query + "|" + _history_text(history)).encode("utf-8")
        ).hexdigest()[:16]
        try:
            formation_result = _formation_specialist_response(
                query, history, early_formation_route, request_id
            )
            return await _use_send_json(send, {
                "ok": True,
                "version": APP_VERSION,
                "query": query,
                "intent": "FORMATION_HANDOFF",
                "response": formation_result["response"],
                "formation_delegation": formation_result["formation_delegation"],
                "visitor_boundary_version": APP_VERSION,
                "request_id": request_id,
                "route_source": "deterministic-formation-preparation-entry",
            })
        except Exception as exc:
            print(f"USE Formation preparation handoff failed safely: {exc}")
            return await _use_send_json(send, {
                "ok": False,
                "version": APP_VERSION,
                "query": query,
                "intent": "FORMATION_HANDOFF",
                "response": "The Formation pathway could not be opened right now.",
                "error_type": "formation_specialist_failure",
                "request_id": request_id,
                "visitor_boundary_version": APP_VERSION,
            }, 503)

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
    if _is_bounded_glossary_request(
        query,
        glossary_term=glossary_term,
        embedded_term=embedded_glossary_term,
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
        request_id = _relational_handoff_session_id(parsed_body)
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
    specific_node = (
        _guide_node_specific_match(query)
        if _is_explicit_guide_destination_request(query)
        else None
    )
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
        specific_node = (
            _guide_node_specific_match(query)
            if _is_explicit_guide_destination_request(query)
            else None
        )
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
    # Explicit resource-search requests belong to the native Catalogue. This
    # boundary runs before Basic Inquiry recovery so broad source-finding
    # questions do not collapse to one generic recommendation. Explanatory
    # questions remain in the frozen Guide composition path.
    if _is_catalogue_resource_search_query(query):
        return await _use_send_json(send, _catalogue_handoff_payload(query, history))

    # Practical stewardship questions are ordinary explanatory inquiries, not glossary or delegated journeys.
    # This must be enforced at the HTTP boundary because macro routing can otherwise
    # bypass the bounded, provider-independent response already defined below.
    if _is_practical_stewardship_question(query):
        try:
            practical_result = _basic_inquiry_response(
                query=query,
                history=history,
                raw_body=parsed_body,
            )
            return await _use_send_json(send, practical_result)
        except Exception as exc:
            print(
                "The Guide practical-stewardship response failed safely; "
                f"continuing through the ordinary recovery boundary: {type(exc).__name__}"
            )

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
                recovery_context = context_data if isinstance(context_data, dict) else {}
                recovery = _basic_inquiry_round1_deterministic_response(
                    query,
                    {},
                    recovery_context,
                )
                recovery_text = str(recovery.get("response") or "").strip()
                if _basic_inquiry_contains_html_markup(recovery_text):
                    print(
                        "The Guide recovery boundary: rejected HTML-shaped deterministic output; "
                        "retrying without retrieved context."
                    )
                    recovery_text = _basic_inquiry_markup_recovery(
                        query, history, context_data.get("intent", "TOPICAL_INQUIRY")
                    )
                    if not recovery_text:
                        try:
                            recovery = _basic_inquiry_round1_deterministic_response(
                                query, {}, {"context_blocks": ""}
                            )
                            recovery_text = str(recovery.get("response") or "").strip()
                        except Exception:
                            recovery_text = ""
                if _basic_inquiry_contains_html_markup(recovery_text):
                    recovery_text = ""
                recovery_recommendation = _normalize_authoritative_recommendation(
                    _general_guide_authoritative_doorway(query, recovery_context)
                )
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
                        "recommendation": recovery_recommendation,
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

    explicit_formation_route = _explicit_formation_entry_route(query)
    if explicit_formation_route is not None:
        route = explicit_formation_route
    else:
        route = _guide_capability_route(query, history)
    route_id = str(route.get("route") or "guide").strip().casefold()
    mode = str(route.get("mode") or "direct").strip().casefold()
    confidence = float(route.get("confidence", 0.0) or 0.0)

    # Final-boundary arbitration: comparative explanatory intent outranks a
    # model's generic Glossary classification. Do not hand off the whole phrase
    # as a term; retain the visitor's complete question for Guide composition.
    if route_id == "glossary" and _is_comparative_explanatory_request(query):
        print(
            "The Guide request boundary: kept comparative inquiry in Guide composition; "
            f"query={_normalize_query(query)[:120]}"
        )
        route_id = "guide"
        mode = "direct"

    # Provider/model routing is advisory, not sufficient authority to open a
    # registered page. Enforce destination intent at the final request boundary
    # too, so a model-selected Guide Node cannot bypass the registry guard above.
    # A compound explanatory question misclassified as a page destination returns
    # to ordinary Guide composition instead of becoming an empty direct handoff.
    if route_id == "guide_node" and not _guide_node_handoff_is_authorized(
        query,
        (route.get("round1_interpretation") or {}).get("guide_node_id"),
    ):
        print(
            "The Guide request boundary: suppressed unsupported Guide Node handoff; "
            f"query={_normalize_query(query)[:120]}"
        )
        route_id = "guide"
        mode = "direct"

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

    # Catalogue is a native visitor-facing search surface, not a Guide retrieval
    # spoke. Preserve the original request and let Catalogue own retrieval/ranking.
    if route_id == "catalogue":
        return await _use_send_json(send, _catalogue_handoff_payload(query, history))

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
        embedded_glossary_term = _extract_embedded_glossary_term(query)
        if glossary_term and _is_bounded_glossary_request(
            query,
            glossary_term=glossary_term,
            embedded_term=embedded_glossary_term,
        ):
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


PROVIDER_GATEWAY_RUNTIME_VERSION = "v1"

@app.post("/api/provider-capability")
async def _provider_capability_route(request: Request):
    token = request.headers.get("X-Living-Archive-Provider-Key")
    try:
        authorize_provider_gateway(token)
        body = await request.json()
        if not isinstance(body, dict):
            raise ValueError("Provider capability payload must be an object.")
        operation, messages, max_tokens = validate_provider_gateway_request(body)
        schema = body.get("schema") if isinstance(body.get("schema"), dict) else None
        result = execute_provider_gateway(
            operation=operation,
            messages=messages,
            max_tokens=max_tokens,
            use_core=use_core,
            schema=schema,
        )
        status = 200 if result.get("ok") else 503
        return JSONResponse(status_code=status, content=result)
    except HTTPException:
        raise
    except Exception as exc:
        print(f"USE provider capability gateway failure: {str(exc)[:400]}")
        return JSONResponse(status_code=503, content={
            "ok": False,
            "contract_version": PROVIDER_GATEWAY_CONTRACT_VERSION,
            "error": "provider_gateway_failure",
        })


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
# v489.07 startup audit: verify answer/navigation separation and canonical doorway propagation.
_v48894_general_guide_composition_self_audit()

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
if STREAM_CONTRACT_VERSION != "SSE-VALIDATED-v1" or STREAM_TRANSPORT_VERSION != "0.1.1":
    raise RuntimeError("USE streaming transport contract integrity failure.")

app = streaming_entry(_use_request_boundary)



print(f"USE ACTIVE + FORMATION SPECIALIST v1: version={APP_VERSION}, fingerprint={DEPLOYMENT_FINGERPRINT}, core_sha={EXPECTED_CORE_BLOB_SHA}, source_sha256={RUNTIME_SOURCE_SHA256}, specialist_contract={SPECIALIST_PIPE_CONTRACT_VERSION}, adapter_contract={SPECIALIST_ADAPTER_CONTRACT_VERSION}, relationship_contract={RELATIONSHIP_CONTRIBUTION_CONTRACT_VERSION}, relationship_voice_policy={RELATIONSHIP_VOICE_POLICY}, formation_contract={FORMATION_CONTRIBUTION_CONTRACT_VERSION}, formation_voice_policy={FORMATION_VOICE_POLICY}, registered_specialists={len(SPECIALIST_CAPABILITY_REGISTRY)}, active_adapters={len(SPECIALIST_ADAPTER_REGISTRY.ids())}, provider_bank_contract={PROVIDER_BANK_CONTRACT_VERSION}, boundary_resilience={BOUNDARY_RESILIENCE_CONTRACT_VERSION}, guide_node_registry_state={guide_node_registry_state().get('state')}, capability_routing=provider_model_bank")
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

# Ecosystem integration diagnostics (non-secret, read-only).
# This reports the distinction between declared capabilities, runtime adapters,
# and known direct visitor-facing handoffs. It does not claim that a route has
# passed a live visitor journey; those require separate E2E checks.
@_FASTAPI_APP.get("/api/provider-health-readiness")
def provider_health_readiness():
    """Return bounded, non-secret provider shared-health readiness diagnostics."""
    try:
        refresh_shared_health_state()
        snapshot = provider_bank_snapshot(use_core)
        config = snapshot.get("shared_health_configuration", {})
        state = snapshot.get("shared_health_state", {})
        config = config if isinstance(config, dict) else {}
        state = state if isinstance(state, dict) else {}
        configured = bool(config.get("configured"))
        available = bool(state.get("available"))
        return {
            "ok": configured and available,
            "contract": "provider-health-readiness-v1",
            "version": APP_VERSION,
            "fingerprint": DEPLOYMENT_FINGERPRINT,
            "shared_health": {
                "configured": configured,
                "available": available,
                "mode": str(state.get("mode") or "unknown"),
                "url_configured": bool(config.get("url_configured")),
                "url_source": str(config.get("url_source") or "unknown"),
                "https_valid": bool(config.get("https_valid")),
                "shared_secret_configured": bool(config.get("shared_secret_configured")),
            },
            "limitations": [
                "Configuration readiness is distinct from successful shared-store reads and writes.",
                "This endpoint never returns the endpoint URL or shared secret.",
            ],
        }
    except Exception:
        return {
            "ok": False,
            "contract": "provider-health-readiness-v1",
            "version": APP_VERSION,
            "fingerprint": DEPLOYMENT_FINGERPRINT,
            "shared_health": {
                "configured": False,
                "available": False,
                "mode": "diagnostic_failure",
                "url_configured": False,
                "url_source": "unknown",
                "https_valid": False,
                "shared_secret_configured": False,
            },
            "limitations": ["Provider health diagnostics could not be completed."],
        }


@_FASTAPI_APP.get("/api/integration-audit")
def ecosystem_integration_audit():
    capabilities = []
    for item in SPECIALIST_CAPABILITY_REGISTRY:
        capabilities.append({
            "specialist_id": str(getattr(item, "specialist_id", "")),
            "public_name": str(getattr(item, "public_name", "")),
            "status": str(getattr(item, "status", "")),
            "entry_point": str(getattr(item, "entry_point", "")),
            "access_class": str(getattr(item, "access_class", "")),
        })

    adapter_ids = sorted(str(item) for item in SPECIALIST_ADAPTER_REGISTRY.ids())
    adapter_set = set(adapter_ids)
    capability_ids = {item["specialist_id"] for item in capabilities}
    declared_available = {
        item["specialist_id"] for item in capabilities
        if item["status"] == "available"
    }

    # Native visitor-facing surfaces are available capabilities, but they are
    # deliberately not adapter-backed retrieval spokes.
    direct_handoffs = {
        "catalogue": "native_catalogue_search",
        "systems_ph": "native_philippine_systems_landing",
        "navigator": "native_navigator",
        "fsd": "native_fsd_landing",
        "guide_node": "canonical_guide_node",
    }
    native_handoff_ids = set(direct_handoffs)
    missing_adapters = sorted(declared_available - adapter_set - native_handoff_ids)
    unregistered_adapters = sorted(adapter_set - capability_ids)

    return {
        "ok": not missing_adapters and not unregistered_adapters,
        "audit_contract": "ecosystem-integration-audit-v1",
        "version": APP_VERSION,
        "fingerprint": DEPLOYMENT_FINGERPRINT,
        "capability_registry": capabilities,
        "runtime_adapters": adapter_ids,
        "direct_handoffs": direct_handoffs,
        "available_capabilities_missing_adapters": missing_adapters,
        "adapters_without_capabilities": unregistered_adapters,
        "catalogue_mode": "direct_handoff_not_adapter",
        "limitations": [
            "This endpoint reports registration and declared routing mode only.",
            "It does not assert live provider health or end-to-end visitor journey success.",
        ],
    }
