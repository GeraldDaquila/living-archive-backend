# USE PRODUCTION VERSION: v487.29 — structural experiential/recommendation routing repair
import hashlib
import importlib
import re
from pathlib import Path

_BASE_MODULE_NAME="main_v487_28_runtime"
_base=importlib.import_module(_BASE_MODULE_NAME)
use_core=_base.use_core

APP_VERSION="v487.29"
DEPLOYMENT_FINGERPRINT="USE-v487.29-structural-experiential-routing-repair"
CANONICAL_BUILD_ID="USE-BUILD-v487.29-structural-experiential-routing-repair"
EXPECTED_CORE_BLOB_SHA="fb3208a8d287f16562ffd640d89f65d5e8d18607"
_MAIN_PATH=Path(__file__).resolve()
RUNTIME_SOURCE_SHA256=hashlib.sha256(_MAIN_PATH.read_bytes()).hexdigest()
if getattr(_base,"_core_runtime_sha","")!=EXPECTED_CORE_BLOB_SHA:
    raise RuntimeError("USE v487.29 package integrity failure: protected core mismatch.")

# Structural normalization: visitor punctuation and common typographic variants
# are normalized before inquiry scoring, so linguistic form cannot change the
# architectural route.
def _normalize_query(text):
    return re.sub(r"\s+"," ",str(text or "").strip().casefold().replace("’","'").replace("‘","'").replace("`","'").replace("–","-").replace("—","-"))

def _has(q,patterns): return bool(re.search(r"(?:^|\b)(?:"+"|".join(patterns)+r")(?:\b|$)",q))

_EXPERIENTIAL_STANCE_PATTERNS=(
    r"i(?:\s+am|'m)\s+struggl(?:e|ing)\s+with",
    r"i\s+struggle\s+with",
    r"i(?:\s+am|'m)\s+dealing\s+with",
    r"i(?:\s+am|'m)\s+having\s+a\s+hard\s+time\s+with",
    r"i(?:\s+am|'m)\s+going\s+through",
    r"i(?:\s+am|'m)\s+experiencing",
    r"i(?:\s+am|'m)\s+feeling",
    r"i\s+feel",
    r"i(?:\s+am|'m)\s+worried\s+about",
    r"i(?:\s+am|'m)\s+afraid\s+of",
    r"i(?:\s+am|'m)\s+confused\s+about",
    r"i(?:\s+am|'m)\s+unsure\s+about",
    r"i(?:\s+am|'m)\s+not\s+sure\s+about",
    r"i\s+(?:need|want)\s+help\s+with",
)
_EXPERIENTIAL_STATE_TERMS=(
    r"lonelin(?:ess|e)",r"empt(?:iness|y)",r"sad(?:ness|ly)",r"sorrow",r"despair",r"hopeless(?:ness)?",
    r"anxiety",r"anxious",r"fear",r"afraid",r"anger",r"angry",r"resentment",r"shame",r"guilt",
    r"confusion",r"uncertain(?:ty)?",r"isolation",r"isolated",r"disconnection",r"disconnected",
    r"heartbreak",r"breakup",r"betrayal",r"burnout",r"stress",r"overwhelmed",r"grief",r"grieving",
    r"bereavement",r"mourning",r"loss",r"relationship",r"abuse",r"trauma",r"forgiveness",r"letting\s+go",
)
def _has_experiential_stance(q): return any(re.search(p,q,re.I) for p in _EXPERIENTIAL_STANCE_PATTERNS)
def _has_experiential_state(q): return any(re.search(rf"\b{p}\b",q,re.I) for p in _EXPERIENTIAL_STATE_TERMS)
def _has_archive_help_request(q):
    return bool(re.search(r"\b(?:anything|something|something here)\b.{0,100}\b(?:living archive|archive|site|guide)\b.{0,100}\b(?:help|think|start|read|explore|reflect)\b",q,re.I))

_original_weighted_inquiry_profile=_base._weighted_inquiry_profile
def _weighted_inquiry_profile(query):
    q=_normalize_query(query)
    p=_original_weighted_inquiry_profile(q)
    if _has_experiential_stance(q) or _has_experiential_state(q): p["lived"]=max(float(p.get("lived",0.0)),0.86)
    if _has_archive_help_request(q): p["recommendation"]=max(float(p.get("recommendation",0.0)),0.82)
    return p

# Patch the base module's classifier dependency rather than creating a second
# response engine. All existing visitor construction, retrieval, canonical
# catalogs, risk handling, and application wiring remain in the preserved v487.28
# runtime module.
_base._normalize_query=_normalize_query
_base._weighted_inquiry_profile=_weighted_inquiry_profile

def _recommendation_answer(query,docs,profile):
    if profile.get("ai_truth") or profile.get("grief"):
        return _base._recommendation_answer(query,docs,profile)
    claims=_base._extract_claims(_base._candidate_sentences(query,docs))
    ranked=sorted(claims,key=lambda c:_base._recommendation_anchor_score(query,c,profile),reverse=True)
    primary=ranked[0] if ranked else None
    secondary=ranked[1] if len(ranked)>1 else None
    if not primary: return ""
    primary_link=f"[{primary['title']}]({primary['url']})"
    parts=[f"A useful place to begin with this question is {primary_link}.",_base._recommendation_wisdom(profile),_base._recommendation_foothold(profile),_base._recommendation_rationale(primary,profile),"This doorway is offered as a reflection gateway, not as a complete explanation or prescription. It is one place to begin noticing what this question opens for you."]
    if secondary: parts.append(f"A nearby path is [{secondary['title']}]({secondary['url']}), which opens another aspect of the question without asking you to treat either doorway as the whole answer.")
    parts.append("You can stay with this lens, follow the connected material, or return with another part of the question that feels more relevant.")
    return "\n\n".join(parts)
_base._recommendation_answer=_recommendation_answer

# Re-run the unified visitor construction against the patched classifier and
# require the previously failing benchmark to resolve as recommendation.
_profile=_base._inquiry_profile("I’m struggling with loneliness. Is there anything in the Living Archive that might help me think about it?")
if _profile["action"]!="recommendation":
    raise RuntimeError(f"USE v487.29 invariant failed: loneliness action={_profile['action']}")
_probe_doc={"title":"The Silent Epidemic: Exploring Loneliness, Despair, Emptiness, and the Redemptive Power of the Eternal Now","url":"https://geralddaquila.com/example-loneliness","text":"Loneliness and emptiness can be approached as questions of human experience."}
_probe_answer,_probe_mode=_base._unified_visitor_construction("I’m struggling with loneliness. Is there anything in the Living Archive that might help me think about it?",[_probe_doc],[])
if _probe_mode!="recommendation" or "The Silent Epidemic" not in _probe_answer or "reflection gateway" not in _probe_answer:
    raise RuntimeError(f"USE v487.29 invariant failed: loneliness visitor contract mode={_probe_mode}, answer={_probe_answer}")

# Preserve the three launch benchmarks as startup guards against regression.
_ai="I keep wondering whether AI is making it harder to know what is actually true. Where should I begin in the Living Archive?"
_grief="I’m struggling with grief after losing someone I love, and I keep wondering whether I should let go or hold on. Where should I begin in the Living Archive?"
if _base._inquiry_profile(_ai)["action"]!="recommendation": raise RuntimeError("USE v487.29 invariant failed: AI movement task")
if _base._inquiry_profile(_grief)["action"]!="recommendation": raise RuntimeError("USE v487.29 invariant failed: grief movement task")

app=_base.app
app.title=f"Find Your Way (The Guide) {APP_VERSION}"
use_core.APP_VERSION=APP_VERSION
use_core.DEPLOYMENT_FINGERPRINT=DEPLOYMENT_FINGERPRINT
use_core.CANONICAL_BUILD_ID=CANONICAL_BUILD_ID
use_core.RUNTIME_SOURCE_SHA256=RUNTIME_SOURCE_SHA256
use_core.EXPECTED_CORE_BLOB_SHA=EXPECTED_CORE_BLOB_SHA
# The preserved v487.28 module already installed the generation/evidence-gap
# boundaries; reinstall them from the patched base so they use the structural
# classifier above.
use_core.generate_llm_response=_base._v487_generate_boundary
use_core._evidence_sufficiency_unavailable_response=_base._v487_evidence_gap_boundary
use_core.handle_query=_base._v487_query_wrapper
print(f"USE v487.29 ACTIVE: version={APP_VERSION}, fingerprint={DEPLOYMENT_FINGERPRINT}, core_sha={getattr(_base,'_core_runtime_sha','')}, source_sha256={RUNTIME_SOURCE_SHA256}")
