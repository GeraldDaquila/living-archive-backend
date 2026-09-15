# USE PRODUCTION VERSION: v487.34 — generic directness adjudication
import hashlib
import importlib
import re
from pathlib import Path

_BASE_MODULE_NAME="main_v487_28_runtime"
_base=importlib.import_module(_BASE_MODULE_NAME)
use_core=_base.use_core
APP_VERSION="v487.34"
DEPLOYMENT_FINGERPRINT="USE-v487.34-generic-directness-adjudication"
CANONICAL_BUILD_ID="USE-BUILD-v487.34-generic-directness-adjudication"
EXPECTED_CORE_BLOB_SHA="fb3208a8d287f16562ffd640d89f65d5e8d18607"
_MAIN_PATH=Path(__file__).resolve()
RUNTIME_SOURCE_SHA256=hashlib.sha256(_MAIN_PATH.read_bytes()).hexdigest()
if getattr(_base,"_core_runtime_sha","")!=EXPECTED_CORE_BLOB_SHA: raise RuntimeError("USE v487.34 package integrity failure: protected core mismatch.")

def _normalize_query(text):
    return re.sub(r"\s+"," ",str(text or "").strip().casefold().replace("’","'").replace("‘","'").replace("`","'").replace("–","-").replace("—","-"))
_EXPERIENTIAL_STANCE_PATTERNS=(r"i(?:\s+am|'m)\s+struggl(?:e|ing)\s+with",r"i\s+struggle\s+with",r"i(?:\s+am|'m)\s+dealing\s+with",r"i(?:\s+am|'m)\s+having\s+a\s+hard\s+time\s+with",r"i(?:\s+am|'m)\s+going\s+through",r"i(?:\s+am|'m)\s+experiencing",r"i(?:\s+am|'m)\s+feeling",r"i\s+feel",r"i(?:\s+am|'m)\s+worried\s+about",r"i(?:\s+am|'m)\s+afraid\s+of",r"i(?:\s+am|'m)\s+confused\s+about",r"i(?:\s+am|'m)\s+unsure\s+about",r"i(?:\s+am|'m)\s+not\s+sure\s+about",r"i\s+(?:need|want)\s+help\s+with")
_EXPERIENTIAL_STATE_TERMS=(r"lonelin(?:ess|e)",r"empt(?:iness|y)",r"sad(?:ness|ly)",r"sorrow",r"despair",r"hopeless(?:ness)?",r"anxiety",r"anxious",r"fear",r"afraid",r"anger",r"angry",r"resentment",r"shame",r"guilt",r"confusion",r"uncertain(?:ty)?",r"isolation",r"isolated",r"disconnection",r"disconnected",r"heartbreak",r"breakup",r"betrayal",r"burnout",r"stress",r"overwhelmed",r"grief",r"grieving",r"bereavement",r"mourning",r"loss",r"relationship",r"abuse",r"trauma",r"forgiveness",r"letting\s+go")
def _has(q,patterns): return bool(re.search(r"(?:^|\b)(?:"+"|".join(patterns)+r")(?:\b|$)",q))
def _has_experiential_stance(q): return any(re.search(p,q,re.I) for p in _EXPERIENTIAL_STANCE_PATTERNS)
def _has_experiential_state(q): return any(re.search(rf"\b{p}\b",q,re.I) for p in _EXPERIENTIAL_STATE_TERMS)
def _has_archive_help_request(q): return bool(re.search(r"\b(?:anything|something|something here)\b.{0,100}\b(?:living archive|archive|site|guide)\b.{0,100}\b(?:help|think|start|read|explore|reflect)\b",q,re.I))
_original_weighted_inquiry_profile=_base._weighted_inquiry_profile
def _weighted_inquiry_profile(query):
    q=_normalize_query(query); p=_original_weighted_inquiry_profile(q)
    if _has_experiential_stance(q) or _has_experiential_state(q): p["lived"]=max(float(p.get("lived",0.0)),0.86)
    if _has_archive_help_request(q): p["recommendation"]=max(float(p.get("recommendation",0.0)),0.82)
    return p
_base._normalize_query=_normalize_query
_base._weighted_inquiry_profile=_weighted_inquiry_profile

def _recommendation_rationale(primary,profile):
    if profile.get("grief"): return "I’m recommending this first because it approaches grief and the human search for continuity directly, making it a more immediate place to reflect on the experience of losing someone you love."
    if profile.get("ai_truth"): return "I’m recommending this first because it gives you a direct place to examine discernment and the question of how we decide what is actually true."
    return "I’m recommending this first because it offers a direct place to reflect on the question you brought here, without asking you to treat it as the whole answer."
_base._recommendation_rationale=_recommendation_rationale

_RECOMMENDATION_GENERIC_TERMS=frozenset({"anything","something","might","may","could","would","should","help","think","thought","thinking","about","question","questions","living","archive","site","website","guide","place","begin","start","first","read","reading","explore","exploring","reflect","reflection","recommend","recommendation","suggest","suggestion","advice","advise","essay","essays","article","articles","resource","resources","piece","pieces","material","where","what","which","how","why","can","please","find","give","offer","tell","one","best","good","for","from","with","into","through","there","here","someone","something","need","want","looking","anything","thing","things"})
_RECOMMENDATION_GENERIC_STANCE_TERMS=frozenset({"i","im","am","struggling","struggle","dealing","having","hard","time","going","experiencing","feeling","feel","worried","worry","afraid","confused","unsure","sure","keep","still","know","don't","dont","not","my","me","mine","it","its","this","that"})

def _recommendation_term_variants(term):
    value=str(term or "").casefold().strip("-'")
    if not value: return set()
    variants={value}
    if value.endswith("ies") and len(value)>4: variants.add(value[:-3]+"y")
    if value.endswith("iness") and len(value)>6: variants.add(value[:-5]+"y")
    if value.endswith("ness") and len(value)>5: variants.add(value[:-4])
    if value.endswith("ing") and len(value)>5: variants.add(value[:-3])
    if value.endswith("ed") and len(value)>5: variants.add(value[:-2])
    if value.endswith("es") and len(value)>4: variants.add(value[:-2])
    if value.endswith("s") and len(value)>4: variants.add(value[:-1])
    return {v for v in variants if len(v)>=3}

def _generic_recommendation_subject_terms(query):
    q=_normalize_query(query)
    tokens=re.findall(r"[a-z0-9]+(?:[-'][a-z0-9]+)?",q)
    terms=[]
    for token in tokens:
        clean=token.strip("-'")
        if len(clean)<3 or clean in _RECOMMENDATION_GENERIC_TERMS or clean in _RECOMMENDATION_GENERIC_STANCE_TERMS: continue
        if clean not in terms: terms.append(clean)
    return tuple(terms)

def _generic_recommendation_directness(query,doc):
    """Rank an already-retrieved canonical resource by direct subject fit.

    This is intentionally topic-agnostic. It gives strongest weight to the
    visitor's substantive subject appearing in the canonical title, then to
    explicit subject phrases/content, and only then to broader body-text fit.
    It never uses transport order as semantic authority.
    """
    title=str(doc.get("title") or "").casefold().strip()
    text=str(doc.get("text") or doc.get("content") or doc.get("excerpt") or "").casefold()
    subject_terms=_generic_recommendation_subject_terms(query)
    if not title or not subject_terms: return (0,0,0,0,0)
    title_tokens=set(re.findall(r"[a-z0-9]+(?:[-'][a-z0-9]+)?",title))
    content_tokens=set(re.findall(r"[a-z0-9]+(?:[-'][a-z0-9]+)?",text[:2400]))
    full_tokens=set(re.findall(r"[a-z0-9]+(?:[-'][a-z0-9]+)?",text))
    title_hits=sum(1 for term in subject_terms if _recommendation_term_variants(term) & title_tokens)
    early_hits=sum(1 for term in subject_terms if _recommendation_term_variants(term) & content_tokens)
    full_hits=sum(1 for term in subject_terms if _recommendation_term_variants(term) & full_tokens)
    phrase_hits=sum(1 for i in range(len(subject_terms)-1) if f"{subject_terms[i]} {subject_terms[i+1]}" in title or f"{subject_terms[i]} {subject_terms[i+1]}" in text[:2400])
    title_density=round(title_hits/max(1,len(subject_terms)),3)
    return (min(8,title_hits),min(8,phrase_hits),min(12,early_hits),min(12,full_hits),int(title_density*1000))

def _canonical_primary_from_docs(canonical_docs,query,profile):
    """Adjudicate the primary doorway from supplied canonical evidence using generic directness."""
    docs=[d for d in (canonical_docs or []) if isinstance(d,dict) and str(d.get("title") or "").strip() and str(d.get("url") or "").startswith("https://")]
    if not docs: return None
    scored=[]
    for index,d in enumerate(docs):
        directness=_generic_recommendation_directness(query,d)
        candidates=_base._candidate_sentences(query,[d])
        claims=_base._extract_claims(candidates) if candidates else []
        evidence_score=max((int(c.get("score",0)) for c in claims),default=0)
        scored.append((directness,evidence_score,-index,d))
    scored.sort(key=lambda item:item[:-1],reverse=True)
    d=scored[0][-1]
    return {"text":"","title":str(d["title"]).strip(),"url":str(d["url"]).strip(),"score":100000.0,"epistemic":"supported","canonical":True,"_authority":"visitor_canonical_generic_directness_adjudication"}

def _recommendation_answer_with_authority(query,docs,profile,canonical_docs=None):
    if profile.get("ai_truth") or profile.get("grief"): return _base._recommendation_answer(query,docs,profile)
    claims=_base._extract_claims(_base._candidate_sentences(query,docs))
    authoritative=_canonical_primary_from_docs(canonical_docs,query,profile)
    if authoritative:
        primary=authoritative
        ranked=[c for c in claims if str(c.get("title") or "").casefold()!=primary["title"].casefold()]
        secondary=ranked[0] if ranked else None
    else:
        ranked=sorted(claims,key=lambda c:_base._recommendation_anchor_score(query,c,profile),reverse=True)
        primary=ranked[0] if ranked else None
        secondary=ranked[1] if len(ranked)>1 else None
    if not primary: return ""
    primary_link=f"[{primary['title']}]({primary['url']})"
    parts=[f"A useful place to begin with this question is {primary_link}",_base._recommendation_wisdom(profile),_base._recommendation_foothold(profile),_recommendation_rationale(primary,profile),"This doorway is offered as a reflection gateway, not as a complete explanation or prescription. It is one place to begin noticing what this question opens for you."]
    if secondary: parts.append(f"A nearby path is [{secondary['title']}]({secondary['url']}), which opens another aspect of the question without asking you to treat either doorway as the whole answer.")
    parts.append("You can stay with this lens, follow the connected material, or return with another part of the question that feels more relevant.")
    return "\n\n".join(parts)

def _unified_visitor_construction(query,retrieved_docs,canonical_docs):
    profile=_base._inquiry_profile(query); docs=[]; seen=set()
    for doc in list(canonical_docs or [])+list(retrieved_docs or []):
        key=(str(doc.get("url") or ""),str(doc.get("title") or ""))
        if key in seen: continue
        seen.add(key); docs.append(doc)
    action=profile["action"]
    if action=="risk": return _base._build_risk_answer(query),"risk"
    if action in {"recommendation","navigation"}:
        answer=_recommendation_answer_with_authority(query,docs,profile,canonical_docs)
        if answer: return answer,"recommendation"
    if action=="lived": return _base._build_lived_experience_answer(query,docs,profile),"lived_experience"
    if action=="foundation": return _base._foundation_teacherly_answer(query),"foundation"
    if action=="conceptual":
        answer=_base._build_factual_answer(query,docs)
        if answer: return answer,"conceptual"
    return "","core"
_base._unified_visitor_construction=_unified_visitor_construction

# Four-pass startup audit. The canonical decoy is deliberately first, so passing requires
authority through generic directness rather than transport order.
_probe_query="I’m struggling with loneliness. Is there anything in the Living Archive that might help me think about it?"
_probe_profile=_base._inquiry_profile(_probe_query)
if _probe_profile["action"]!="recommendation": raise RuntimeError(f"USE v487.34 invariant failed: loneliness action={_probe_profile['action']}")
_probe_canonical=[{"title":"Why Social Media Makes Us Anxious: FOMO, Comparison, and Mental Health Explained","url":"https://geralddaquila.com/2025/06/02/why-social-media-makes-us-anxious-fomo-comparison-and-mental-health-explained/","text":"Social comparison can contribute to feelings of disconnection."},{"title":"The Silent Epidemic: Exploring Loneliness, Despair, Emptiness, and the Redemptive Power of the Eternal Now","url":"https://geralddaquila.com/2025/06/03/the-silent-epidemic-exploring-loneliness-despair-emptiness-and-the-redemptive-power-of-the-eternal-now/","text":"Loneliness and emptiness are examined directly."}]
_probe_retrieved=[{"title":"You Are Enough: Freeing Inner Beauty from the Clutches of Expectations","url":"https://geralddaquila.com/2025/06/01/you-are-enough-freeing-inner-beauty-from-the-clutches-of-expectations/","text":"Expectations can shape how people understand themselves."}]
_probe_answer,_probe_mode=_unified_visitor_construction(_probe_query,_probe_retrieved,_probe_canonical)
if _probe_mode!="recommendation" or not _probe_answer.startswith("A useful place to begin with this question is [The Silent Epidemic:"): raise RuntimeError(f"USE v487.34 invariant failed: canonical directness adjudication: {_probe_answer}")
_ai="I keep wondering whether AI is making it harder to know what is actually true. Where should I begin in the Living Archive?"
_grief="I’m struggling with grief after losing someone I love, and I keep wondering whether I should let go or hold on. Where should I begin in the Living Archive?"
if _base._inquiry_profile(_ai)["action"]!="recommendation": raise RuntimeError("USE v487.34 invariant failed: AI movement task")
if _base._inquiry_profile(_grief)["action"]!="recommendation": raise RuntimeError("USE v487.34 invariant failed: grief movement task")

app=_base.app
app.title=f"Find Your Way (The Guide) {APP_VERSION}"
use_core.APP_VERSION=APP_VERSION
use_core.DEPLOYMENT_FINGERPRINT=DEPLOYMENT_FINGERPRINT
use_core.CANONICAL_BUILD_ID=CANONICAL_BUILD_ID
use_core.RUNTIME_SOURCE_SHA256=RUNTIME_SOURCE_SHA256
use_core.EXPECTED_CORE_BLOB_SHA=EXPECTED_CORE_BLOB_SHA
use_core.generate_llm_response=_base._v487_generate_boundary
use_core._evidence_sufficiency_unavailable_response=_base._v487_evidence_gap_boundary
use_core.handle_query=_base._v487_query_wrapper
print(f"USE v487.34 ACTIVE: version={APP_VERSION}, fingerprint={DEPLOYMENT_FINGERPRINT}, core_sha={getattr(_base,'_core_runtime_sha','')}, source_sha256={RUNTIME_SOURCE_SHA256}")
