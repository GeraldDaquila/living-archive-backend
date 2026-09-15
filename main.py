# USE PRODUCTION VERSION: v487.39 — authoritative canonical doorway boundary
import hashlib
import importlib
import re
from pathlib import Path

_BASE_MODULE_NAME = "main_v487_28_runtime"
_base = importlib.import_module(_BASE_MODULE_NAME)
use_core = _base.use_core
APP_VERSION = "v487.39"
DEPLOYMENT_FINGERPRINT = "USE-v487.39-authoritative-canonical-doorway-boundary"
CANONICAL_BUILD_ID = "USE-BUILD-v487.39-authoritative-canonical-doorway-boundary"
EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"
_MAIN_PATH = Path(__file__).resolve()
RUNTIME_SOURCE_SHA256 = hashlib.sha256(_MAIN_PATH.read_bytes()).hexdigest()
if getattr(_base, "_core_runtime_sha", "") != EXPECTED_CORE_BLOB_SHA:
    raise RuntimeError("USE v487.39 package integrity failure: protected core mismatch.")

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
def _has_experiential_stance(q): return any(re.search(pattern, q, re.I) for pattern in _EXPERIENTIAL_STANCE_PATTERNS)
def _has_experiential_state(q): return any(re.search(rf"\b{pattern}\b", q, re.I) for pattern in _EXPERIENTIAL_STATE_TERMS)
def _has_archive_help_request(q): return bool(re.search(r"\b(?:anything|something|something here)\b.{0,100}\b(?:living archive|archive|site|guide)\b.{0,100}\b(?:help|think|start|read|explore|reflect)\b", q, re.I))
_original_weighted_inquiry_profile = _base._weighted_inquiry_profile
def _weighted_inquiry_profile(query):
    q = _normalize_query(query); profile = _original_weighted_inquiry_profile(q)
    if _has_experiential_stance(q) or _has_experiential_state(q): profile["lived"] = max(float(profile.get("lived", 0.0)), 0.86)
    if _has_archive_help_request(q): profile["recommendation"] = max(float(profile.get("recommendation", 0.0)), 0.82)
    return profile
_base._normalize_query = _normalize_query
_base._weighted_inquiry_profile = _weighted_inquiry_profile

def _recommendation_rationale(primary, profile):
    if profile.get("grief"): return "I’m recommending this first because it approaches grief and the human search for continuity directly, making it a more immediate place to reflect on the experience of losing someone you love."
    if profile.get("ai_truth"): return "I’m recommending this first because it gives you a direct place to examine discernment and the question of how we decide what is actually true."
    return "I’m recommending this first because it offers a direct place to reflect on the question you brought here, without asking you to treat it as the whole answer."
_base._recommendation_rationale = _recommendation_rationale

_SUBJECT_STOPWORDS = frozenset({"a","an","the","and","or","but","if","then","than","of","on","in","at","to","as","by","for","from","with","into","through","there","here","this","that","these","those","is","are","was","were","be","been","being","am","i","im","my","me","mine","myself","your","you","yourself","our","we","they","them","their","someone","somebody","anyone","anything","something","people","person","what","which","who","when","where","why","how","can","could","would","should","may","might","will","do","does","did","doing","don","dont","don't","not","no","know","sure","about","help","think","thinking","thought","question","questions","living","archive","site","website","guide","place","begin","start","first","read","reading","explore","exploring","reflect","reflection","recommend","recommendation","suggest","suggestion","advice","advise","essay","essays","article","articles","resource","resources","piece","pieces","material","please","find","give","offer","tell","one","best","good","need","want","looking","thing","things","time","way","make","made","keep","still","feel","feels","feeling","care","caring","having","hard","going","experiencing","worried","worry","afraid","confused","unsure","struggling","struggle","dealing","finding","it","its","all","very","just","really","more","less","ever","often","sometimes","now","today"})
def _subject_terms(query):
    tokens = re.findall(r"[a-z0-9]+", _normalize_query(query)); return tuple(dict.fromkeys(t for t in tokens if len(t) >= 3 and t not in _SUBJECT_STOPWORDS))
def _term_forms(term):
    value = str(term or "").casefold(); forms = {value}
    if value.endswith("ies") and len(value) > 4: forms.add(value[:-3] + "y")
    if value.endswith("ness") and len(value) > 5: forms.add(value[:-4])
    if value.endswith("ing") and len(value) > 5: forms.add(value[:-3])
    if value.endswith("ed") and len(value) > 5: forms.add(value[:-2])
    if value.endswith("es") and len(value) > 4: forms.add(value[:-2])
    if value.endswith("s") and len(value) > 4: forms.add(value[:-1])
    return {f for f in forms if len(f) >= 3}
def _subject_metrics(query, doc):
    title = str(doc.get("title") or "").casefold(); text = str(doc.get("text") or doc.get("content") or doc.get("excerpt") or "").casefold(); terms = _subject_terms(query)
    if not title or not terms: return (0,0,0,0,0)
    title_tokens=set(re.findall(r"[a-z0-9]+",title)); early=text[:2400]; early_tokens=set(re.findall(r"[a-z0-9]+",early)); full_tokens=set(re.findall(r"[a-z0-9]+",text))
    title_hits=sum(bool(_term_forms(term)&title_tokens) for term in terms); early_hits=sum(bool(_term_forms(term)&early_tokens) for term in terms); full_hits=sum(bool(_term_forms(term)&full_tokens) for term in terms)
    phrase_hits=sum(1 for index in range(len(terms)-1) if f"{terms[index]} {terms[index+1]}" in title or f"{terms[index]} {terms[index+1]}" in early)
    return (min(8,title_hits),min(8,phrase_hits),min(12,early_hits),min(12,full_hits),int(1000*title_hits/max(1,len(terms))))

_SUBJECT_FAMILIES={"anger":("anger","angry","resentment","resentful","irritation","irritated","frustration","frustrated","rage","conflict"),"loneliness":("loneliness","lonely","isolation","isolated","disconnection","disconnected"),"grief":("grief","grieving","bereavement","mourning","loss","lost","death"),"fear":("fear","afraid","anxiety","anxious","worry","worried"),"shame":("shame","ashamed","guilt","guilty"),"relationship":("relationship","relationships","partner","partners","interpersonal","marriage","married","friendship","friends","communication","boundaries")}
_RELATIONAL_PATTERNS=(r"\bsomeone i care about\b",r"\bpeople i care about\b",r"\bperson i care about\b",r"\brelationship\b",r"\bpartner\b",r"\bloved one\b",r"\bfamily\b",r"\bfriend\b",r"\binterpersonal\b",r"\bwith someone\b",r"\bcare about\b")
def _query_frame(query):
    q=_normalize_query(query); families=tuple(family for family,terms in _SUBJECT_FAMILIES.items() if any(re.search(rf"\b{re.escape(term)}\b",q) for term in terms)); return {"families":families,"relational":any(re.search(pattern,q,re.I) for pattern in _RELATIONAL_PATTERNS)}
def _role_evidence(doc):
    text=re.sub(r"\s+"," ",str(doc.get("text") or doc.get("content") or "").strip().casefold()); title=str(doc.get("title") or "").casefold(); corpus=title+" "+text
    return {"worldview":bool(re.search(r"\b(?:spiritual|spirituality|religious|religion|mystical|mysticism|afterlife|reincarnation|soul|sacred|transcenden\w*|metaphysics|metaphysical|cosmic|oversoul|ascension|law of one|new earth)\b",corpus)),"risk":bool(re.search(r"\b(?:suicid\w*|self-harm|self harm|overdose|acute crisis|crisis intervention|immediate danger)\b",corpus)),"abuse":bool(re.search(r"\b(?:abuse|abusive|coercive control|gaslighting)\b",corpus))}
_base._role_evidence=_role_evidence
def _family_hit_count(text,family):
    tokens=set(re.findall(r"[a-z0-9]+",str(text or "").casefold())); return sum(bool(_term_forms(term)&tokens) for term in _SUBJECT_FAMILIES.get(family,()))
def _contextual_fit(query,doc):
    frame=_query_frame(query); title=str(doc.get("title") or "").casefold(); text=str(doc.get("text") or doc.get("content") or doc.get("excerpt") or "").casefold(); early=text[:3000]
    family_title=sum(_family_hit_count(title,f)>0 for f in frame["families"]); family_early=sum(_family_hit_count(early,f)>0 for f in frame["families"]); relational_title=_family_hit_count(title,"relationship"); relational_early=_family_hit_count(early,"relationship"); combined=(family_title>0 and relational_title>0) or (family_early>0 and relational_early>0)
    return (family_title,family_early,int(combined),relational_title,relational_early)
def _relevance_level(metrics, *, allow_full_content=False):
    title_hits,phrase_hits,early_hits,full_hits,_=metrics
    if title_hits>=1 or phrase_hits>=1 or (early_hits>=2 and full_hits>=2): return 2
    if allow_full_content and full_hits>=1: return 2
    if full_hits>=1: return 1
    return 0
def _risk_mismatch(doc,profile): return bool(not profile.get("risk") and _role_evidence(doc)["risk"])

def _canonical_primary_from_docs(canonical_docs,query,profile):
    frame=_query_frame(query); ranked=[]
    for index,doc in enumerate(canonical_docs or []):
        if not isinstance(doc,dict) or not str(doc.get("title") or "").strip() or not str(doc.get("url") or "").startswith("https://"): continue
        role=_role_evidence(doc)
        if role["risk"] and not profile.get("risk"): continue
        if role["abuse"] and "abuse" not in _normalize_query(query): continue
        if role["worldview"] and not (profile.get("specialized") or profile.get("grief") or profile.get("ai_truth")): continue
        metrics=_subject_metrics(query,doc); context=_contextual_fit(query,doc); relevance=_relevance_level(metrics,allow_full_content=True)
        if relevance<2: continue
        evidence=_base._candidate_sentences(query,[doc]); claims=_base._extract_claims(evidence) if evidence else []; evidence_score=max((int(c.get("score",0)) for c in claims),default=0)
        mismatch=0
        if frame["relational"] and not (context[2] or context[3] or context[4]): mismatch-=8
        ranked.append((mismatch,context[0],context[2],context[1],metrics,evidence_score,-index,doc))
    if not ranked: return None
    ranked.sort(key=lambda item:item[:-1],reverse=True); selected=ranked[0][-1]
    return {"text":"","title":str(selected["title"]).strip(),"url":str(selected["url"]).strip(),"score":100000.0,"epistemic":"supported","canonical":True,"_authority":"visitor_canonical_relevance_adjudication"}

def _select_adjacent(claims,query,primary_title,profile):
    ranked=[]
    for index,claim in enumerate(claims):
        role=_role_evidence(claim)
        if str(claim.get("title") or "").casefold()==str(primary_title or "").casefold() or role["risk"] or (role["abuse"] and "abuse" not in _normalize_query(query)) or (role["worldview"] and not (profile.get("specialized") or profile.get("grief") or profile.get("ai_truth"))): continue
        metrics=_subject_metrics(query,claim)
        if _relevance_level(metrics)<1: continue
        ranked.append((metrics,float(claim.get("score",0) or 0),-index,claim))
    if not ranked: return None
    ranked.sort(key=lambda item:item[:-1],reverse=True); return ranked[0][-1]
def _generic_recommendation_wisdom(profile): return "Before trying to solve the question, it can help to notice what is most present in the experience—what hurts, what feels uncertain, what you may be longing for, or what you are not yet ready to name."
def _recommendation_answer_with_authority(query,docs,profile,canonical_docs=None):
    if profile.get("ai_truth") or profile.get("grief"): return _base._recommendation_answer(query,docs,profile)
    claims=_base._extract_claims(_base._candidate_sentences(query,docs)); primary=_canonical_primary_from_docs(canonical_docs,query,profile)
    if primary: secondary=_select_adjacent(claims,query,primary["title"],profile)
    else:
        eligible=[]
        for index,claim in enumerate(claims):
            if _risk_mismatch(claim,profile): continue
            metrics=_subject_metrics(query,claim)
            if _relevance_level(metrics)<2: continue
            eligible.append((metrics,float(claim.get("score",0) or 0),-index,claim))
        eligible.sort(key=lambda item:item[:-1],reverse=True); primary=eligible[0][-1] if eligible else None; secondary=_select_adjacent([item[-1] for item in eligible[1:]],query,primary["title"] if primary else "",profile) if primary else None
    if not primary: return ""
    parts=[f"A useful place to begin with this question is [{primary['title']}]({primary['url']})",_generic_recommendation_wisdom(profile),_base._recommendation_foothold(profile),_recommendation_rationale(primary,profile),"This doorway is offered as a reflection gateway, not as a complete explanation or prescription. It is one place to begin noticing what this question opens for you."]
    if secondary: parts.append(f"A nearby path is [{secondary['title']}]({secondary['url']}), which opens another aspect of the question without asking you to treat either doorway as the whole answer.")
    parts.append("You can stay with this lens, follow the connected material, or return with another part of the question that feels more relevant.")
    return "\n\n".join(parts)

def _parse_context_documents(context_blocks):
    parser=getattr(use_core,"_parse_context_documents",None)
    if callable(parser): return parser(context_blocks)
    docs=[]
    for block in str(context_blocks or "").split("\n\n---\n\n"):
        tm=re.search(r"^Title:\s*(.+?)\s*$",block,re.M); um=re.search(r"^URL:\s*(https?://\S+)\s*$",block,re.M|re.I); cm=re.search(r"^Content:\s*(.*)$",block,re.M|re.S)
        if tm and um and cm: docs.append({"title":tm.group(1).strip(),"url":um.group(1).strip(),"text":cm.group(1).strip()})
    return docs

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

_original_fetch_canonical_context = use_core.fetch_canonical_context

def _serialize_context_documents(docs):
    blocks=[]
    for doc in docs or []:
        title=str(doc.get("title") or "").strip()
        url=str(doc.get("url") or doc.get("canonical_url") or "").strip()
        text=str(doc.get("text") or doc.get("content") or doc.get("excerpt") or "").strip()
        if not title or not re.match(r"^https://\S+$",url,re.I) or not text: continue
        blocks.append(f"Title: {title}\nURL: {url}\nContent: {text}")
    return "\n\n---\n\n".join(blocks)

def _authoritative_recommendation_docs(query,docs,profile):
    primary=_canonical_primary_from_docs(docs,query,profile)
    if not primary: return []
    target=primary["title"].casefold()
    for doc in docs or []:
        if str(doc.get("title") or "").strip().casefold()==target: return [doc]
    return []

def _recommendation_first_fetch(query_str):
    data=_original_fetch_canonical_context(query_str)
    profile=_base._inquiry_profile(query_str)
    if profile["action"] in {"recommendation","navigation"} and not profile["risk"] and not profile.get("grief") and not profile.get("ai_truth") and isinstance(data,dict):
        canonical_context=str(data.get("canonical_link_context") or "")
        if canonical_context:
            docs=_parse_context_documents(canonical_context)
            authoritative=_authoritative_recommendation_docs(query_str,docs,profile)
            if authoritative:
                narrowed_context=_serialize_context_documents(authoritative)
                data=dict(data)
                data["canonical_link_context"]=narrowed_context
                data["context_blocks"]=narrowed_context
                data["recommendation_first_evidence_bridge"]=True
                data["recommendation_canonical_boundary"]=True
                data["recommendation_canonical_count"]=1
                data["evidence_sufficiency_unavailable"]=False
                data["question_structure_evidence_unavailable"]=False
                data["question_evidence_fit_unavailable"]=False
                data["frame_neutral_evidence_unavailable"]=False
                print(f"The Guide v487.39 authoritative canonical doorway boundary: selected={authoritative[0]['title']}, candidates={len(docs)}, query={_normalize_query(query_str)[:120]}")
            elif any(data.get(k) for k in ("frame_neutral_evidence_unavailable","question_structure_evidence_unavailable","evidence_sufficiency_unavailable","question_evidence_fit_unavailable")):
                data=dict(data); data["context_blocks"]=canonical_context; data["recommendation_first_evidence_bridge"]=True
    return data
use_core.fetch_canonical_context=_recommendation_first_fetch

_probe_query="I keep finding myself angry at someone I care about, and I don’t know what to do with that anger. Is there anything in the Living Archive that might help me think about it?"
_probe_profile=_base._inquiry_profile(_probe_query)
if _probe_profile["action"]!="recommendation": raise RuntimeError(f"USE v487.39 invariant failed: anger action={_probe_profile['action']}")
_probe_docs=[
    {"title":"Suicide and the Journey of the Soul: A Unified Exploration of Mind, Spirit, and Society","url":"https://geralddaquila.com/suicide","text":"A discussion of suicide, despair, anger, and the soul."},
    {"title":"Unraveling Abuse: The Harm We Inherit, The Healing We Choose","url":"https://geralddaquila.com/2025/06/01/unraveling-abuse-the-harm-we-inherit-the-healing-we-choose/","text":"Abuse in relationships involves power, control, trauma, conflict, projection, and anger. The material examines cycles of harm and healing."},
    {"title":"Emotional Hijacking and the Search for Meaning: Reconnecting with Our True Needs Beyond Materialism","url":"https://geralddaquila.com/2025/06/09/emotional-hijacking-and-the-search-for-meaning-reconnecting-with-our-true-needs-beyond-materialism/","text":"Emotional hijacking includes intense emotional responses such as fear or anger. Mindful awareness and reflective practice can help identify emotional triggers and their true sources."},
    {"title":"The Divine Feminine: Reawakening Sacred Balance in the Ascension Process and Its Intersections with Feminism","url":"https://geralddaquila.com/divine-feminine","text":"Sacred balance and spiritual transformation."},
]
_probe_answer,_probe_mode=_unified_visitor_construction(_probe_query,_probe_docs,_probe_docs)
if _probe_mode!="recommendation" or not _probe_answer.startswith("A useful place to begin with this question is [Emotional Hijacking"):
    raise RuntimeError(f"USE v487.39 invariant failed: direct anger doorway={_probe_answer}")
if "Suicide and the Journey of the Soul" in _probe_answer or "The Divine Feminine" in _probe_answer or "Unraveling Abuse" in _probe_answer:
    raise RuntimeError("USE v487.39 invariant failed: mismatched doorway survived subject/risk/worldview gate")
_probe_gap={"evidence_sufficiency_unavailable":True,"canonical_link_context":"Title: Emotional Hijacking and the Search for Meaning: Reconnecting with Our True Needs Beyond Materialism\nURL: https://geralddaquila.com/2025/06/09/emotional-hijacking-and-the-search-for-meaning-reconnecting-with-our-true-needs-beyond-materialism/\nContent: Emotional hijacking includes intense emotional responses such as fear or anger.\n\n---\n\nTitle: Suicide and the Journey of the Soul: A Unified Exploration of Mind, Spirit, and Society\nURL: https://geralddaquila.com/suicide\nContent: Suicide and despair are discussed."}
_bridge_docs=_parse_context_documents(_probe_gap["canonical_link_context"])
if not _bridge_docs or not _recommendation_first_fetch: raise RuntimeError("USE v487.39 invariant failed: evidence bridge unavailable")
_probe_primary=_canonical_primary_from_docs(_probe_docs,_probe_query,_probe_profile)
if not _probe_primary or _probe_primary["title"]!="Emotional Hijacking and the Search for Meaning: Reconnecting with Our True Needs Beyond Materialism": raise RuntimeError(f"USE v487.39 invariant failed: authoritative anger primary={_probe_primary}")
_probe_authoritative=_authoritative_recommendation_docs(_probe_query,_probe_docs,_probe_profile)
if len(_probe_authoritative)!=1 or _probe_authoritative[0]["title"]!=_probe_primary["title"]: raise RuntimeError("USE v487.39 invariant failed: canonical doorway narrowing is not authoritative")
for _query,_label in (("I keep wondering whether AI is making it harder to know what is actually true. Where should I begin in the Living Archive?","AI"),(_probe_query,"anger"),("I’m struggling with loneliness. Is there anything in the Living Archive that might help me think about it?","loneliness"),("I’m struggling with grief after losing someone I love, and I keep wondering whether I should let go or hold on. Where should I begin in the Living Archive?","grief")):
    if _base._inquiry_profile(_query)["action"]!="recommendation": raise RuntimeError(f"USE v487.39 invariant failed: {_label} movement task")

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
print(f"USE v487.39 ACTIVE: version={APP_VERSION}, fingerprint={DEPLOYMENT_FINGERPRINT}, core_sha={getattr(_base,'_core_runtime_sha','')}, source_sha256={RUNTIME_SOURCE_SHA256}")
