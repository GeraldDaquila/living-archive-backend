# USE PRODUCTION VERSION: v487.37 — subject-frame ranking and distinct adjacent navigation
import hashlib
import importlib
import re
from pathlib import Path

_BASE_MODULE_NAME="main_v487_28_runtime"
_base=importlib.import_module(_BASE_MODULE_NAME)
use_core=_base.use_core

APP_VERSION="v487.37"
DEPLOYMENT_FINGERPRINT="USE-v487.37-subject-frame-ranking"
CANONICAL_BUILD_ID="USE-BUILD-v487.37-subject-frame-ranking"
EXPECTED_CORE_BLOB_SHA="fb3208a8d287f16562ffd640d89f65d5e8d18607"

_MAIN_PATH=Path(__file__).resolve()
RUNTIME_SOURCE_SHA256=hashlib.sha256(_MAIN_PATH.read_bytes()).hexdigest()
if getattr(_base,"_core_runtime_sha","")!=EXPECTED_CORE_BLOB_SHA:
    raise RuntimeError("USE v487.37 package integrity failure: protected core mismatch.")

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
def _has(q,patterns):
    return bool(re.search(r"(?:^|\b)(?:"+"|".join(patterns)+r")(?:\b|$)",q))
def _has_experiential_stance(q):
    return any(re.search(p,q,re.I) for p in _EXPERIENTIAL_STANCE_PATTERNS)
def _has_experiential_state(q):
    return any(re.search(rf"\b{p}\b",q,re.I) for p in _EXPERIENTIAL_STATE_TERMS)
def _has_archive_help_request(q):
    return bool(re.search(r"\b(?:anything|something|something here)\b.{0,100}\b(?:living archive|archive|site|guide)\b.{0,100}\b(?:help|think|start|read|explore|reflect)\b",q,re.I))

_original_weighted_inquiry_profile=_base._weighted_inquiry_profile
def _weighted_inquiry_profile(query):
    q=_normalize_query(query)
    p=_original_weighted_inquiry_profile(q)
    if _has_experiential_stance(q) or _has_experiential_state(q):
        p["lived"]=max(float(p.get("lived",0.0)),0.86)
    if _has_archive_help_request(q):
        p["recommendation"]=max(float(p.get("recommendation",0.0)),0.82)
    return p
_base._normalize_query=_normalize_query
_base._weighted_inquiry_profile=_weighted_inquiry_profile

_GENERIC_TERMS=frozenset({
    "anything","something","might","may","could","would","should","help","think","thought","thinking","about","question","questions",
    "living","archive","site","website","guide","place","begin","start","first","read","reading","explore","exploring","reflect",
    "reflection","recommend","recommendation","suggest","suggestion","advice","advise","essay","essays","article","articles",
    "resource","resources","piece","pieces","material","where","what","which","how","why","can","please","find","give","offer",
    "tell","one","best","good","for","from","with","into","through","there","here","someone","person","people","need","want",
    "looking","thing","things","finding","know","knows","do","does","care"
})
_GENERIC_STANCE_TERMS=frozenset({
    "i","im","am","struggling","struggle","dealing","having","hard","time","going","experiencing","feeling","feel","worried",
    "worry","afraid","confused","unsure","sure","keep","still","my","me","mine","it","its","this","that","don't","dont","not"
})
def _subject_terms(query):
    tokens=re.findall(r"[a-z0-9]+(?:[-'][a-z0-9]+)?",_normalize_query(query))
    return tuple(dict.fromkeys(t.strip("-'") for t in tokens if len(t.strip("-'"))>=3 and t.strip("-'") not in _GENERIC_TERMS and t.strip("-'") not in _GENERIC_STANCE_TERMS))
def _term_variants(term):
    v=str(term or "").casefold().strip("-'")
    out={v} if v else set()
    if v.endswith("ies") and len(v)>4: out.add(v[:-3]+"y")
    if v.endswith("iness") and len(v)>6: out.add(v[:-5]+"y")
    if v.endswith("ness") and len(v)>5: out.add(v[:-4])
    if v.endswith("ing") and len(v)>5: out.add(v[:-3])
    if v.endswith("ed") and len(v)>5: out.add(v[:-2])
    if v.endswith("es") and len(v)>4: out.add(v[:-2])
    if v.endswith("s") and len(v)>4: out.add(v[:-1])
    return {x for x in out if len(x)>=3}

_SUBJECT_FAMILIES={
    "anger":("anger","angry","resentment","resentful","irritation","irritated","frustration","frustrated","rage","conflict"),
    "loneliness":("loneliness","lonely","isolation","isolated","disconnection","disconnected"),
    "grief":("grief","grieving","bereavement","mourning","loss","lost","death"),
    "fear":("fear","afraid","anxiety","anxious","worry","worried"),
    "shame":("shame","ashamed","guilt","guilty"),
    "relationship":("relationship","relationships","partner","partners","interpersonal","marriage","married","friendship","friends","conflict","communication","boundaries"),
}
_RELATIONAL_PATTERNS=(
    r"\bsomeone i care about\b",r"\bpeople i care about\b",r"\bperson i care about\b",r"\brelationship\b",r"\bpartner\b",
    r"\bloved one\b",r"\bfamily\b",r"\bfriend\b",r"\binterpersonal\b",r"\bbetween us\b",r"\bwith someone\b",r"\bcare about\b"
)
_ACTION_PATTERNS=(r"\bwhat do i do\b",r"\bwhat to do\b",r"\bhow do i\b",r"\bhow to\b",r"\bhandle\b",r"\brespond\b",r"\bwork with\b",r"\bdeal with\b",r"\bmanage\b")

def _query_frame(query):
    q=_normalize_query(query)
    families=[]
    for family,terms in _SUBJECT_FAMILIES.items():
        if any(re.search(rf"\b{re.escape(t)}\b",q) for t in terms):
            families.append(family)
    relational=any(re.search(p,q,re.I) for p in _RELATIONAL_PATTERNS)
    action=any(re.search(p,q,re.I) for p in _ACTION_PATTERNS)
    return {"families":tuple(families),"relational":relational,"action":action,"terms":_subject_terms(q)}

def _role_evidence(doc):
    text=re.sub(r"\s+"," ",str(doc.get("text") or doc.get("content") or "").strip().casefold())
    title=str(doc.get("title") or "").casefold()
    corpus=title+" "+text
    return {
        "worldview":bool(re.search(r"\b(?:spiritual|spirituality|religious|religion|mystical|mysticism|afterlife|reincarnation|soul|sacred|transcenden\w*|metaphysics|cosmic|oversoul|ascension)\b",corpus)),
        "risk":bool(re.search(r"\b(?:suicid\w*|self-harm|self harm|overdose|acute crisis|crisis intervention|immediate danger)\b",corpus)),
    }
_base._role_evidence=_role_evidence

def _eligible_docs(query,docs,profile):
    allow_worldview=bool(profile.get("specialized") or profile.get("grief") or profile.get("ai_truth"))
    out=[]
    for doc in docs or []:
        if not isinstance(doc,dict): continue
        title=str(doc.get("title") or "").strip()
        url=str(doc.get("url") or doc.get("canonical_url") or "").strip()
        if not title or not re.match(r"^https://\S+$",url,re.I): continue
        role=_role_evidence(doc)
        if role["risk"] and not profile.get("risk"): continue
        if role["worldview"] and not allow_worldview: continue
        out.append(doc)
    return out

def _doc_tokens(text):
    return set(re.findall(r"[a-z0-9]+(?:[-'][a-z0-9]+)?",str(text or "").casefold()))

def _family_hits(text,families):
    tokens=_doc_tokens(text)
    return {family:sum(bool(_term_variants(term)&tokens) for term in _SUBJECT_FAMILIES.get(family,())) for family in families}

def _subject_fit(query,doc):
    frame=_query_frame(query)
    title=str(doc.get("title") or "").casefold()
    text=str(doc.get("text") or doc.get("content") or doc.get("excerpt") or "").casefold()
    early=text[:3000]
    title_tokens=_doc_tokens(title); early_tokens=_doc_tokens(early); full_tokens=_doc_tokens(text)
    family_title=sum(1 for family in frame["families"] if _family_hits(title,(family,))[family]>0)
    family_early=sum(1 for family in frame["families"] if _family_hits(early,(family,))[family]>0)
    family_full=sum(1 for family in frame["families"] if _family_hits(text,(family,))[family]>0)
    exact_title=sum(bool(_term_variants(t)&title_tokens) for t in frame["terms"])
    exact_early=sum(bool(_term_variants(t)&early_tokens) for t in frame["terms"])
    exact_full=sum(bool(_term_variants(t)&full_tokens) for t in frame["terms"])
    relational_title=sum(1 for t in _SUBJECT_FAMILIES["relationship"] if _term_variants(t)&title_tokens)
    relational_early=sum(1 for t in _SUBJECT_FAMILIES["relationship"] if _term_variants(t)&early_tokens)
    relational_full=sum(1 for t in _SUBJECT_FAMILIES["relationship"] if _term_variants(t)&full_tokens)
    combined=0
    if frame["relational"]:
        combined=int((family_title>0 and relational_title>0)*6+(family_early>0 and relational_early>0)*5+(family_full>0 and relational_full>0)*3)
    tier=0
    if exact_title or family_title: tier=4
    elif combined>=5: tier=3
    elif exact_early or family_early: tier=2
    elif exact_full or family_full: tier=1
    score=(tier,exact_title*14+family_title*18+combined,exact_early*5+family_early*7,exact_full*2+family_full*3,relational_title*2+relational_early,int(frame["action"] and (exact_early>0 or family_early>0)))
    return score

def _rank_recommendation_docs(query,docs,profile):
    eligible=_eligible_docs(query,docs,profile)
    ranked=[]
    for i,doc in enumerate(eligible):
        fit=_subject_fit(query,doc)
        if fit[0]<=0: continue
        base_score=float(doc.get("score",doc.get("_score",0)) or 0)
        ranked.append((fit,base_score,-i,doc))
    ranked.sort(key=lambda x:(x[0],x[1],x[2]),reverse=True)
    return [x[3] for x in ranked]

def _claims_for_recommendation(query,docs,profile):
    ranked=_rank_recommendation_docs(query,docs,profile)
    claims=[]
    for doc in ranked[:8]:
        title=str(doc.get("title") or "").strip()
        url=str(doc.get("url") or doc.get("canonical_url") or "").strip()
        if not title or not url: continue
        claims.append({"text":"","title":title,"url":url,"score":float(doc.get("score",0) or 0),"epistemic":"interpretive" if _role_evidence(doc)["worldview"] else "supported","_fit":_subject_fit(query,doc)})
    return claims

def _recommendation_answer(query,docs,profile):
    if profile.get("ai_truth") or profile.get("grief"):
        return _base._recommendation_answer(query,docs,profile)
    claims=_claims_for_recommendation(query,docs,profile)
    if not claims: return ""
    primary=claims[0]
    if primary["_fit"][0]<2: return ""
    secondary=None
    primary_key=(primary["url"].casefold(),primary["title"].casefold())
    for c in claims[1:]:
        key=(c["url"].casefold(),c["title"].casefold())
        if key==primary_key: continue
        if c["_fit"][0]>=2:
            secondary=c
            break
    parts=[
        f"A useful place to begin with this question is [{primary['title']}]({primary['url']})",
        "Before trying to solve the question, it can help to notice what is most present in the experience—what hurts, what feels uncertain, what you may be longing for, or what you are not yet ready to name.",
        _base._recommendation_foothold(profile),
        "I’m recommending this first because it offers a direct place to reflect on the question you brought here, without asking you to treat it as the whole answer.",
        "This doorway is offered as a reflection gateway, not as a complete explanation or prescription. It is one place to begin noticing what this question opens for you."
    ]
    if secondary:
        parts.append(f"A nearby path is [{secondary['title']}]({secondary['url']}), which opens another aspect of the question without asking you to treat either doorway as the whole answer.")
    parts.append("You can stay with this lens, follow the connected material, or return with another part of the question that feels more relevant.")
    return "\n\n".join(parts)

def _unified_visitor_construction(query,retrieved_docs,canonical_docs):
    profile=_base._inquiry_profile(query)
    docs=[]; seen=set()
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
if _probe_profile["action"]!="recommendation": raise RuntimeError(f"USE v487.37 invariant failed: anger action={_probe_profile['action']}")
_probe_docs=[
    {"title":"Suicide and the Journey of the Soul: A Unified Exploration of Mind, Spirit, and Society","url":"https://geralddaquila.com/example-suicide","text":"A spiritual exploration of suicide, the soul, and despair."},
    {"title":"The Divine Feminine: Reawakening Sacred Balance in the Ascension Process and Its Intersections with Feminism","url":"https://geralddaquila.com/example-divine","text":"A spiritual exploration of sacred balance."},
    {"title":"Understanding Anger in Human Relationships","url":"https://geralddaquila.com/example-anger","text":"Anger in relationships can signal hurt, unmet needs, boundaries, and unresolved conflict."},
    {"title":"Healthy Communication Between People Who Care About Each Other","url":"https://geralddaquila.com/example-communication","text":"Relationships and communication can help people work with conflict, anger, and unmet needs."},
]
_probe_answer,_probe_mode=_unified_visitor_construction(_probe_query,_probe_docs,[])
if _probe_mode!="recommendation" or "Understanding Anger in Human Relationships" not in _probe_answer: raise RuntimeError("USE v487.37 invariant failed: subject-family primary")
if "Healthy Communication Between People Who Care About Each Other" not in _probe_answer: raise RuntimeError("USE v487.37 invariant failed: distinct adjacent path")
if _probe_answer.count("Understanding Anger in Human Relationships")!=1: raise RuntimeError("USE v487.37 invariant failed: duplicate primary doorway")
_probe_lonely="I’m struggling with loneliness. Is there anything in the Living Archive that might help me think about it?"
_probe_lonely_docs=[
    {"title":"Why Social Media Makes Us Anxious: FOMO, Comparison, and Mental Health Explained","url":"https://geralddaquila.com/example-social","text":"Social comparison can contribute to feelings of disconnection."},
    {"title":"The Silent Epidemic: Exploring Loneliness, Despair, Emptiness, and the Redemptive Power of the Eternal Now","url":"https://geralddaquila.com/example-loneliness","text":"Loneliness and emptiness are examined directly."}
]
_probe_lonely_answer,_probe_lonely_mode=_unified_visitor_construction(_probe_lonely,_probe_lonely_docs,[])
if _probe_lonely_mode!="recommendation" or "The Silent Epidemic" not in _probe_lonely_answer: raise RuntimeError("USE v487.37 invariant failed: loneliness subject family")
_ai="I keep wondering whether AI is making it harder to know what is actually true. Where should I begin in the Living Archive?"
_grief="I’m struggling with grief after losing someone I love, and I keep wondering whether I should let go or hold on. Where should I begin in the Living Archive?"
if _base._inquiry_profile(_ai)["action"]!="recommendation": raise RuntimeError("USE v487.37 invariant failed: AI movement task")
if _base._inquiry_profile(_grief)["action"]!="recommendation": raise RuntimeError("USE v487.37 invariant failed: grief movement task")

app=_base.app
app.title=f"Find Your Way (The Guide) {APP_VERSION}"
use_core.APP_VERSION=APP_VERSION
use_core.DEPLOYMENT_FINGERPRINT=DEPLOYMENT_FINGERPRINT
use_core.CANONICAL_BUILD_ID=CANONICAL_BUILD_ID
use_core.generate_llm_response=_base._v487_generate_boundary
use_core._evidence_sufficiency_unavailable_response=_base._v487_evidence_gap_boundary
use_core.handle_query=_base._v487_query_wrapper
