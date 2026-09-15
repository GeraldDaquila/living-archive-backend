# USE PRODUCTION VERSION: v487.36 — subject-fit and boundary gating
import hashlib
import importlib
import re
from pathlib import Path

_BASE_MODULE_NAME="main_v487_28_runtime"
_base=importlib.import_module(_BASE_MODULE_NAME)
use_core=_base.use_core

APP_VERSION="v487.36"
DEPLOYMENT_FINGERPRINT="USE-v487.36-subject-fit-boundary-gating"
CANONICAL_BUILD_ID="USE-BUILD-v487.36-subject-fit-boundary-gating"
EXPECTED_CORE_BLOB_SHA="fb3208a8d287f16562ffd640d89f65d5e8d18607"

_MAIN_PATH=Path(__file__).resolve()
RUNTIME_SOURCE_SHA256=hashlib.sha256(_MAIN_PATH.read_bytes()).hexdigest()
if getattr(_base,"_core_runtime_sha","")!=EXPECTED_CORE_BLOB_SHA:
    raise RuntimeError("USE v487.36 package integrity failure: protected core mismatch.")

def _normalize_query(text):
    return re.sub(r"\s+"," ",str(text or "").strip().casefold().replace("’","'").replace("‘","'").replace("`","'").replace("–","-").replace("—","-"))

_EXPERIENTIAL_STANCE_PATTERNS=(
    r"i(?:\s+am|'m)\s+struggl(?:e|ing)\s+with",r"i\s+struggle\s+with",r"i(?:\s+am|'m)\s+dealing\s+with",
    r"i(?:\s+am|'m)\s+having\s+a\s+hard\s+time\s+with",r"i(?:\s+am|'m)\s+going\s+through",r"i(?:\s+am|'m)\s+experiencing",
    r"i(?:\s+am|'m)\s+feeling",r"i\s+feel",r"i(?:\s+am|'m)\s+worried\s+about",r"i(?:\s+am|'m)\s+afraid\s+of",
    r"i(?:\s+am|'m)\s+confused\s+about",r"i(?:\s+am|'m)\s+unsure\s+about",r"i(?:\s+am|'m)\s+not\s+sure\s+about",
    r"i\s+(?:need|want)\s+help\s+with"
)
_EXPERIENTIAL_STATE_TERMS=(
    r"lonelin(?:ess|e)",r"empt(?:iness|y)",r"sad(?:ness|ly)",r"sorrow",r"despair",r"hopeless(?:ness)?",r"anxiety",r"anxious",
    r"fear",r"afraid",r"anger",r"angry",r"resentment",r"shame",r"guilt",r"confusion",r"uncertain(?:ty)?",r"isolation",
    r"isolated",r"disconnection",r"disconnected",r"heartbreak",r"breakup",r"betrayal",r"burnout",r"stress",r"overwhelmed",
    r"grief",r"grieving",r"bereavement",r"mourning",r"loss",r"relationship",r"abuse",r"trauma",r"forgiveness",r"letting\s+go"
)
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

_GENERIC_TERMS=frozenset({
    "anything","something","might","may","could","would","should","help","think","thought","thinking","about",
    "question","questions","living","archive","site","website","guide","place","begin","start","first","read","reading",
    "explore","exploring","reflect","reflection","recommend","recommendation","suggest","suggestion","advice","advise",
    "essay","essays","article","articles","resource","resources","piece","pieces","material","where","what","which",
    "how","why","can","please","find","give","offer","tell","one","best","good","for","from","with","into",
    "through","there","here","someone","person","people","need","want","looking","thing","things","finding","know",
    "knows","do","does","care"
})
_GENERIC_STANCE_TERMS=frozenset({
    "i","im","am","struggling","struggle","dealing","having","hard","time","going","experiencing","feeling","feel",
    "worried","worry","afraid","confused","unsure","sure","keep","still","my","me","mine","it","its","this","that",
    "don't","dont","not"
})
def _subject_terms(query):
    tokens=re.findall(r"[a-z0-9]+(?:[-'][a-z0-9]+)?",_normalize_query(query)); out=[]
    for token in tokens:
        t=token.strip("-'")
        if len(t)>=3 and t not in _GENERIC_TERMS and t not in _GENERIC_STANCE_TERMS and t not in out: out.append(t)
    return tuple(out)
def _term_variants(term):
    v=str(term or "").casefold().strip("-'"); out={v} if v else set()
    if v.endswith("ies") and len(v)>4: out.add(v[:-3]+"y")
    if v.endswith("iness") and len(v)>6: out.add(v[:-5]+"y")
    if v.endswith("ness") and len(v)>5: out.add(v[:-4])
    if v.endswith("ing") and len(v)>5: out.add(v[:-3])
    if v.endswith("ed") and len(v)>5: out.add(v[:-2])
    if v.endswith("es") and len(v)>4: out.add(v[:-2])
    if v.endswith("s") and len(v)>4: out.add(v[:-1])
    return {x for x in out if len(x)>=3}
def _directness(query,doc):
    title=str(doc.get("title") or "").casefold(); text=str(doc.get("text") or doc.get("content") or doc.get("excerpt") or "").casefold(); terms=_subject_terms(query)
    if not title or not terms: return (0,0,0,0,0)
    title_tokens=set(re.findall(r"[a-z0-9]+(?:[-'][a-z0-9]+)?",title)); early_tokens=set(re.findall(r"[a-z0-9]+(?:[-'][a-z0-9]+)?",text[:2400])); full_tokens=set(re.findall(r"[a-z0-9]+(?:[-'][a-z0-9]+)?",text))
    title_hits=sum(bool(_term_variants(t)&title_tokens) for t in terms); early_hits=sum(bool(_term_variants(t)&early_tokens) for t in terms); full_hits=sum(bool(_term_variants(t)&full_tokens) for t in terms)
    phrase_hits=sum(1 for i in range(len(terms)-1) if f"{terms[i]} {terms[i+1]}" in title or f"{terms[i]} {terms[i+1]}" in text[:2400])
    return (min(8,title_hits),min(8,phrase_hits),min(12,early_hits),min(12,full_hits),int(1000*title_hits/max(1,len(terms))))

def _role_evidence(doc):
    text=re.sub(r"\s+"," ",str(doc.get("text") or "").strip().casefold()); title=str(doc.get("title") or "").casefold(); corpus=title+" "+text
    return {"worldview":bool(re.search(r"\b(?:spiritual|spirituality|religious|religion|mystical|mysticism|afterlife|reincarnation|soul|sacred|transcenden\w*|metaphysics|cosmic|oversoul|ascension)\b",corpus)),"risk":bool(re.search(r"\b(?:suicid\w*|self-harm|self harm|overdose|acute crisis|crisis intervention|immediate danger)\b",corpus))}
_base._role_evidence=_role_evidence

def _eligible_docs(query,docs,profile):
    allow_worldview=bool(profile.get("specialized") or profile.get("grief") or profile.get("ai_truth")); out=[]
    for doc in docs or []:
        if not isinstance(doc,dict): continue
        title=str(doc.get("title") or "").strip(); url=str(doc.get("url") or doc.get("canonical_url") or "").strip()
        if not title or not re.match(r"^https://\S+$",url,re.I): continue
        role=_role_evidence(doc)
        if role["risk"] and not profile.get("risk"): continue
        if role["worldview"] and not allow_worldview: continue
        out.append(doc)
    return out

def _claims_for_recommendation(query,docs,profile):
    eligible=_eligible_docs(query,docs,profile); candidates=_base._candidate_sentences(query,eligible); claims=_base._extract_claims(candidates); scored=[]
    for i,c in enumerate(claims): scored.append((_directness(query,c),float(c.get("score",0) or 0),-i,c))
    scored.sort(key=lambda x:x[:-1],reverse=True); return [x[-1] for x in scored]

def _recommendation_answer(query,docs,profile):
    if profile.get("ai_truth") or profile.get("grief"): return _base._recommendation_answer(query,docs,profile)
    claims=_claims_for_recommendation(query,docs,profile)
    if not claims: return ""
    primary=claims[0]; d=_directness(query,primary)
    if d[0]==0 and d[2]==0: return ""
    secondary=next((c for c in claims[1:] if (_directness(query,c)[0]>0 or _directness(query,c)[2]>0)),None)
    parts=[
        f"A useful place to begin with this question is [{primary['title']}]({primary['url']})",
        "Before trying to solve the question, it can help to notice what is most present in the experience—what hurts, what feels uncertain, what you may be longing for, or what you are not yet ready to name.",
        _base._recommendation_foothold(profile),
        "I’m recommending this first because it offers a direct place to reflect on the question you brought here, without asking you to treat it as the whole answer.",
        "This doorway is offered as a reflection gateway, not as a complete explanation or prescription. It is one place to begin noticing what this question opens for you."
    ]
    if secondary: parts.append(f"A nearby path is [{secondary['title']}]({secondary['url']}), which opens another aspect of the question without asking you to treat either doorway as the whole answer.")
    parts.append("You can stay with this lens, follow the connected material, or return with another part of the question that feels more relevant.")
    return "\n\n".join(parts)

def _unified_visitor_construction(query,retrieved_docs,canonical_docs):
    profile=_base._inquiry_profile(query); docs=[]; seen=set()
    for doc in list(canonical_docs or [])+list(retrieved_docs or []):
        key=(str(doc.get("url") or ""),str(doc.get("title") or "").casefold())
        if key in seen: continue
        seen.add(key); docs.append(doc)
    if profile["action"]=="risk": return _base._build_risk_answer(query),"risk"
    if profile["action"] in {"recommendation","navigation"}:
        answer=_recommendation_answer(query,docs,profile)
        if answer: return answer,"recommendation"
    eligible=_eligible_docs(query,docs,profile)
    if profile["action"]=="lived": return _base._build_lived_experience_answer(query,eligible,profile),"lived_experience"
    if profile["action"]=="foundation": return _base._foundation_teacherly_answer(query),"foundation"
    if profile["action"]=="conceptual":
        answer=_base._build_factual_answer(query,eligible)
        if answer: return answer,"conceptual"
    return "","core"
_base._unified_visitor_construction=_unified_visitor_construction
_base._recommendation_answer=_recommendation_answer

_probe_query="I keep finding myself angry at someone I care about, and I don’t know what to do with that anger. Is there anything in the Living Archive that might help me think about it?"
_probe_profile=_base._inquiry_profile(_probe_query)
if _probe_profile["action"]!="recommendation": raise RuntimeError(f"USE v487.36 invariant failed: anger action={_probe_profile['action']}")
_probe_docs=[
    {"title":"Suicide and the Journey of the Soul: A Unified Exploration of Mind, Spirit, and Society","url":"https://geralddaquila.com/example-suicide","text":"A spiritual exploration of suicide, the soul, and despair."},
    {"title":"The Divine Feminine: Reawakening Sacred Balance in the Ascension Process and Its Intersections with Feminism","url":"https://geralddaquila.com/example-divine","text":"A spiritual exploration of sacred balance."},
    {"title":"Understanding Anger in Human Relationships","url":"https://geralddaquila.com/example-anger","text":"Anger in relationships can signal hurt, unmet needs, boundaries, and unresolved conflict."}
]
_probe_answer,_probe_mode=_unified_visitor_construction(_probe_query,_probe_docs,[])
if _probe_mode!="recommendation" or "Understanding Anger in Human Relationships" not in _probe_answer: raise RuntimeError("USE v487.36 invariant failed: specialized decoys defeated by subject-fit gate")
_probe_canonical=[
    {"title":"Why Social Media Makes Us Anxious: FOMO, Comparison, and Mental Health Explained","url":"https://geralddaquila.com/example-social","text":"Social comparison can contribute to feelings of disconnection."},
    {"title":"The Silent Epidemic: Exploring Loneliness, Despair, Emptiness, and the Redemptive Power of the Eternal Now","url":"https://geralddaquila.com/example-loneliness","text":"Loneliness and emptiness are examined directly."}
]
_probe_lonely="I’m struggling with loneliness. Is there anything in the Living Archive that might help me think about it?"
_probe_lonely_answer,_probe_lonely_mode=_unified_visitor_construction(_probe_lonely,[],_probe_canonical)
if _probe_lonely_mode!="recommendation" or "The Silent Epidemic" not in _probe_lonely_answer: raise RuntimeError("USE v487.36 invariant failed: loneliness directness")
_ai="I keep wondering whether AI is making it harder to know what is actually true. Where should I begin in the Living Archive?"
_grief="I’m struggling with grief after losing someone I love, and I keep wondering whether I should let go or hold on. Where should I begin in the Living Archive?"
if _base._inquiry_profile(_ai)["action"]!="recommendation": raise RuntimeError("USE v487.36 invariant failed: AI movement task")
if _base._inquiry_profile(_grief)["action"]!="recommendation": raise RuntimeError("USE v487.36 invariant failed: grief movement task")

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
print(f"USE v487.36 ACTIVE: version={APP_VERSION}, fingerprint={DEPLOYMENT_FINGERPRINT}, core_sha={getattr(_base,'_core_runtime_sha','')}, source_sha256={RUNTIME_SOURCE_SHA256}")