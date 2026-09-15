# USE PRODUCTION VERSION: v487.15 — canonical doorway catalog resolution
import hashlib
import importlib
import re
from pathlib import Path
APP_VERSION="v487.15"
DEPLOYMENT_FINGERPRINT="USE-v487.15-canonical-doorway-catalog-resolution"
CANONICAL_BUILD_ID="USE-BUILD-v487.15-canonical-doorway-catalog-resolution"
EXPECTED_CORE_BLOB_SHA="fb3208a8d287f16562ffd640d89f65d5e8d18607"
_MAIN_PATH=Path(__file__).resolve(); _CORE_PATH=_MAIN_PATH.with_name("use_core.py")
RUNTIME_SOURCE_SHA256=hashlib.sha256(_MAIN_PATH.read_bytes()).hexdigest()
if not _CORE_PATH.exists(): raise RuntimeError("USE v487.15 package integrity failure: use_core.py is missing.")
_core_bytes=_CORE_PATH.read_bytes(); _core_runtime_sha=hashlib.sha1(f"blob {len(_core_bytes)}\0".encode()+_core_bytes).hexdigest()
if _core_runtime_sha!=EXPECTED_CORE_BLOB_SHA: raise RuntimeError("USE v487.15 package integrity failure: protected core mismatch.")
use_core=importlib.import_module("use_core")
_original_generate_llm_response=use_core.generate_llm_response
_original_handle_query=getattr(use_core,"handle_query",None)
_original_evidence_sufficiency_unavailable_response=getattr(use_core,"_evidence_sufficiency_unavailable_response",None)
if _original_handle_query is None: raise RuntimeError("USE v487.15 package integrity failure: API query handler unavailable.")
if not callable(_original_evidence_sufficiency_unavailable_response): raise RuntimeError("USE v487.15 package integrity failure: evidence-gap boundary unavailable.")

def _sanitize_visitor_output(text): return re.sub(r"\bUSE\b","The Guide",str(text or "")).replace("..",".")
def _normalize_title(text): return re.sub(r"^[\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F\u200D]+\s*","",str(text or "").strip()).strip()
def _valid_doc_url(doc):
    url=str(doc.get("url") or doc.get("canonical_url") or "").strip(); return url if re.match(r"^https://\S+$",url,re.I) else ""
def _clean_evidence_text(text):
    value=re.sub(r"<[^>]+>"," ",str(text or "")); value=re.sub(r"(?:https?://|www\.)\S+"," ",value); return re.sub(r"\s+"," ",value).strip()
def _role_evidence(doc):
    text=re.sub(r"\s+"," ",str(doc.get("text") or "").strip().casefold()); title=_normalize_title(doc.get("title") or "").casefold(); corpus=title+" "+text
    return {"worldview":bool(re.search(r"\b(?:spiritual|spirituality|religious|religion|mystical|mysticism|afterlife|reincarnation|soul|sacred|transcenden|metaphysics|cosmic|oversoul)\b",corpus)),"risk":bool(re.search(r"\b(?:suicid(?:e|al|ality)|self-harm|overdose|acute crisis|crisis intervention|immediate danger)\b",corpus))}
def _is_risk_related(doc): return _role_evidence(doc)["risk"]
def _parse_context_documents(context_blocks):
    parser=getattr(use_core,"_parse_context_documents",None)
    if callable(parser): return parser(context_blocks)
    docs=[]
    for block in str(context_blocks or "").strip().split("\n\n---\n\n"):
        tm=re.search(r"^Title:\s*(.+?)\s*$",block,re.M); um=re.search(r"^URL:\s*(https?://\S+)\s*$",block,re.M|re.I); cm=re.search(r"^Content:\s*(.*)$",block,re.M|re.S)
        if tm and um and cm: docs.append({"title":tm.group(1).strip(),"url":um.group(1).strip().rstrip(".,;"),"text":cm.group(1).strip()})
    return docs

def _extract_user_query(args,kwargs):
    for key in ("user_query","query","question"):
        value=kwargs.get(key)
        if isinstance(value,str) and value.strip(): return value.strip()
    return args[0].strip() if args and isinstance(args[0],str) else ""
def _context_blocks_from_kwargs(args,kwargs):
    for key in ("retrieved_context_blocks","retrieved_context","context_blocks"):
        if kwargs.get(key): return str(kwargs[key])
    return args[1] if len(args)>=2 and isinstance(args[1],str) else ""
def _has(q,patterns): return bool(re.search(r"(?:^|\b)(?:"+"|".join(patterns)+r")(?:\b|$)",q))

def _weighted_inquiry_profile(query):
    q=re.sub(r"\s+"," ",str(query or "").strip().casefold()); p={"risk":0.0,"recommendation":0.0,"navigation":0.0,"foundation":0.0,"lived":0.0,"conceptual":0.0,"grief":0.0,"specialized":0.0,"ai_truth":0.0}
    if _has(q,[r"suicid\w*",r"self[- ]harm",r"overdose",r"immediate danger",r"unsafe",r"threatened",r"kill(?:ing)? myself",r"kill(?:ing)? yourself",r"want(?:ing)? to die",r"end my life",r"take my own life",r"harm myself",r"hurt myself"]): p["risk"]=1.0
    if _has(q,[r"recommend\w*",r"advise",r"advice",r"essay\w*",r"article\w*",r"read(?:ing)?",r"what should i read",r"what can i read",r"where can i start",r"what would you recommend"]): p["recommendation"]+=0.82
    if _has(q,[r"which .*read",r"which .*essay",r"which .*article"]): p["recommendation"]+=0.18
    if _has(q,[r"where can i find",r"where do i find",r"how do i get to",r"find the",r"browse",r"explore the",r"show me",r"take me to",r"link me to"]): p["navigation"]=0.92
    if re.search(r"^(?:what is|what's|tell me about|how does)\s+(?:the )?(?:living archive|the guide)\b",q): p["foundation"]=1.0
    elif _has(q,[r"how does the living archive work",r"what is the living archive for",r"what is the guide for"]): p["foundation"]=1.0
    if _has(q,[r"i feel",r"i'm feeling",r"i am feeling",r"i can't",r"i cannot",r"i keep",r"i still",r"i don't know how",r"i don't know why",r"i know i need",r"it hurts",r"this hurts",r"my grief",r"my anger",r"my fear",r"my anxiety",r"my loneliness",r"my relationship",r"my partner",r"my loss",r"someone left",r"they left",r"letting go",r"let go",r"forgive",r"forgiveness",r"heartbreak",r"breakup",r"betrayal",r"abuse",r"trauma",r"overwhelmed",r"afraid",r"scared",r"angry",r"grieving",r"grief",r"bereavement",r"mourning",r"loss"]): p["lived"]=0.86
    if re.match(r"^(?:what is|what's|who is|who was|when did|where is|where was|why is|why does|how does|what does|what are|define|explain)\b",q): p["conceptual"]=0.72
    if _has(q,[r"grief",r"grieving",r"bereavement",r"death of",r"died",r"loss of",r"lost (?:a|my|someone)",r"mourning",r"love one",r"loved one"]): p["grief"]=0.95
    if _has(q,[r"afterlife",r"reincarnation",r"spiritual",r"spirituality",r"cosmic",r"mystical",r"metaphysical",r"transcendence",r"near-death",r"nde"]): p["specialized"]=0.92
    if _has(q,[r"\bai\b",r"artificial intelligence",r"machine intelligence",r"generated",r"deepfake",r"misinformation",r"disinformation",r"truth",r"true",r"know what is actually true",r"discernment"]): p["ai_truth"]=0.92
    if p["grief"]: p["lived"]=max(p["lived"],0.90)
    if p["recommendation"] and p["grief"]: p["recommendation"]=min(1.0,p["recommendation"]+0.10)
    return p

def _weighted_action(profile):
    if profile["risk"]>=0.80: return "risk"
    if profile["ai_truth"]>=0.80: return "recommendation"
    scores={k:profile[k] for k in ("recommendation","navigation","lived","foundation","conceptual")}
    if profile["recommendation"]>0: scores["recommendation"]+=0.10*profile["grief"]+0.05*profile["specialized"]
    if profile["lived"]>0: scores["lived"]+=0.08*profile["grief"]
    if profile["foundation"]>0: scores["foundation"]-=0.35*profile["recommendation"]
    return max(scores,key=scores.get) if max(scores.values())>=0.35 else "core"

def _inquiry_profile(query):
    p=_weighted_inquiry_profile(query); action=_weighted_action(p); return {**p,"subject":"grief" if p["grief"]>=0.5 else "","action":action,"risk":p["risk"]>=0.8,"recommendation":p["recommendation"]>=0.5,"navigation":p["navigation"]>=0.5,"foundation":p["foundation"]>=0.5,"lived":p["lived"]>=0.5,"conceptual":p["conceptual"]>=0.5,"grief":p["grief"]>=0.5}
def _build_risk_answer(query):
    q=str(query or "").casefold()
    if re.search(r"\b(?:suicid\w*|self-harm|self harm|kill(?:ing)? myself|kill(?:ing)? yourself|want(?:ing)? to die|end my life|take my own life|harm myself|hurt myself)\b",q): return "If you are thinking about killing yourself or may act on thoughts of self-harm, please seek human help now. Call emergency services or go to the nearest emergency department, and if you can, stay with another person while you get help."
    return "If you may be in immediate danger or cannot keep yourself safe, please seek human help now. Call emergency services or go to the nearest emergency department."

def _candidate_sentences(query,docs):
    q=re.sub(r"\s+"," ",str(query or "").strip().casefold()); terms=set(re.findall(r"[a-z]{4,}",q)); candidates=[]; seen=set()
    for doc in docs:
        if not isinstance(doc,dict) or _is_risk_related(doc): continue
        title=_normalize_title(doc.get("title") or ""); url=_valid_doc_url(doc); raw=_clean_evidence_text(doc.get("text") or "")
        if not title or not url or not raw: continue
        title_terms=set(re.findall(r"[a-z]{4,}",title.casefold()))
        for sentence in [s.strip() for s in re.split(r"(?<=[.!?])\s+",raw) if s.strip()]:
            low=sentence.casefold()
            if re.search(r"\b(?:collective awakening|profound truth|we'?re all co-creators|universal knowledge|quantum thread|hypothetical)\b",low): continue
            score=10*len(terms & set(re.findall(r"[a-z]{4,}",low))); score+=8*len(terms & title_terms)
            if re.search(r"\b(?:is|are|means|refers to|describes|represents|relates to|pathway|stewardship|meaning|transcenden|creation|growth|grief|receiv|giv|loss|mourning|bereavement|forgiv|truth|discernment|knowledge|wisdom)\b",low): score+=15
            if len(sentence)>18: score+=5
            key=re.sub(r"\W+"," ",low).strip()
            if key in seen: continue
            seen.add(key); candidates.append({"score":score,"sentence":sentence,"title":title,"url":url,"worldview":_role_evidence(doc)["worldview"]})
    candidates.sort(key=lambda x:-x["score"]); return candidates[:12]
def _extract_claims(candidates):
    claims=[]; seen=set()
    for c in candidates:
        core=re.sub(r"\.{2,}",".",c["sentence"]).strip().rstrip(".")
        if not core or len(core.split())<6: continue
        normalized=re.sub(r"\s+"," ",core); key=re.sub(r"\W+"," ",normalized.casefold()).strip()
        if key in seen: continue
        seen.add(key); claims.append({"text":normalized,"title":c["title"],"url":c["url"],"score":c["score"],"epistemic":("interpretive" if c["worldview"] else "supported")})
    return claims

def _canonical_catalog(profile):
    if profile.get("ai_truth"):
        return {
            "direct": {
                "title":"Truth in the Age of AI: Why Discernment Is Becoming a Survival Skill",
                "url":"https://geralddaquila.com/truth-in-the-age-of-ai-why-discernment-is-becoming-a-survival-skill/"
            },
            "adjacent": [
                {"title":"Knowledge Stewardship in the AI Era: From Information to Wisdom","url":"https://geralddaquila.com/knowledge-stewardship-in-the-ai-era-from-information-to-wisdom/"},
                {"title":"The Meaning Crisis in the Age of Artificial Intelligence","url":"https://geralddaquila.com/the-meaning-crisis-in-the-age-of-artificial-intelligence/"}
            ]
        }
    if profile.get("grief"):
        return {
            "direct": {"title":"Death, Grief, and the Human Search for Continuity","url":"https://geralddaquila.com/2025/05/24/embracing-the-cosmic-journey-finding-peace-after-losing-a-loved-one/"},
            "adjacent":[{"title":"The Transformative Power of Loss: Finding Meaning in Grief Through Spiritual and Scientific Wisdom","url":"https://geralddaquila.com/2025/05/12/the-transformative-power-of-loss-finding-meaning-in-grief-through-spiritual-and-scientific-wisdom/"}]
        }
    return {"direct":None,"adjacent":[]}

def _catalog_claim(catalog_item,claims):
    if not catalog_item: return None
    for claim in claims:
        if claim["title"].casefold()==catalog_item["title"].casefold(): return claim
    return {"text":"","title":catalog_item["title"],"url":catalog_item["url"],"score":0.0,"epistemic":"supported"}

def _canonical_role(title,text,profile):
    low=f"{title} {text}".casefold()
    if profile.get("ai_truth"):
        if "truth in the age of ai" in low or "discernment is becoming a survival skill" in low: return "ai_truth_direct"
        if "knowledge stewardship" in low or "information to wisdom" in low or "meaning crisis" in low or "artificial intelligence" in low and "meaning" in low: return "ai_truth_adjacent"
        if "living archive navigator" in low or "network architecture" in low or "regeneration" in low: return "ai_truth_structural"
    if profile.get("grief"):
        if "death, grief" in low or "transformative power of loss" in low or "meaning in grief" in low or "grief" in low and "continuity" in low: return "grief_direct"
        if "afterlife" in low or "reincarnation" in low or "near-death" in low or "hypnosis" in low: return "grief_specialized"
    return "general"

def _recommendation_anchor_score(query,claim,profile):
    role=_canonical_role(claim["title"],claim["text"],profile); score=float(claim.get("score",0))
    if profile.get("ai_truth"): score += {"ai_truth_direct":1000,"ai_truth_adjacent":500,"ai_truth_structural":-500,"general":-50}.get(role,-50)
    if profile.get("grief"): score += {"grief_direct":110,"grief_specialized":-40,"general":-20}.get(role,-20)
    return score

def _recommendation_wisdom(profile):
    if profile.get("ai_truth"): return "In a time when information can be generated faster than it can be understood, discernment becomes less about finding one perfect source and more about learning how to recognize what kind of claim you are encountering."
    if profile.get("grief"): return "Grief is not only the pain of losing someone; it can also be the slow work of finding a way to carry love, memory, and an altered future without pretending the loss did not matter. There may be no single correct timetable for that work."
    return "A useful way to approach a question like this is to let the first insight open the inquiry rather than treating it as the final word."
def _recommendation_foothold(profile):
    if profile.get("ai_truth"): return "For now, a humane next step is to take one claim or answer that you are unsure about and ask: what here is established, what is interpretation, and what would I need to verify before I build a conclusion on it?"
    if profile.get("grief"): return "For today, a humane next step can be very small: name what you miss, what hurts, or what you are not ready to accept yet, without requiring yourself to solve it."
    return "A humane next step is to notice which part of the question matters most to you now and stay with that part before moving on."
def _recommendation_rationale(primary,profile):
    low=(primary["title"]+" "+primary["text"]).casefold()
    if profile.get("ai_truth"): return "I’m recommending this first because it speaks directly to the question underneath your question: how to distinguish what can be known from what is generated, interpreted, or merely persuasive in the AI era."
    if profile.get("grief"):
        if "continuity" in low: return "I’m recommending this first because it approaches grief and the human search for continuity directly, making it a more immediate place to reflect on the experience of losing someone you love."
        return "I’m recommending this first because it speaks directly to grief and loss, rather than asking you to begin with a more specialized interpretation of what happens after death."
    return "This is a useful place to begin because it speaks directly to the part of the question you asked about."

def _foundation_teacherly_answer(query):
    low=str(query or "").casefold()
    if re.search(r"\bwhat is the living archive\b|\bwhat's the living archive\b",low): return "The Living Archive is a connected body of essays, perspectives, frameworks, and pathways for making sense of complex human questions without reducing them to a single answer. It is less a place to collect conclusions than a way to begin finding your bearings.\n\nYou can enter with a question, follow a pathway that helps you orient to it, and then move outward into the connected essays that deepen or complicate what you are seeing."
    return "The Living Archive is a connected body of essays, perspectives, frameworks, and pathways for making sense of complex human questions without reducing them to a single answer."

def _recommendation_answer(query,docs,profile):
    claims=_extract_claims(_candidate_sentences(query,docs))
    catalog=_canonical_catalog(profile)
    if profile.get("ai_truth") or profile.get("grief"):
        primary=_catalog_claim(catalog.get("direct"),claims)
        adjacent_claims=[_catalog_claim(item,claims) for item in catalog.get("adjacent",[])]
        adjacent_claims=[c for c in adjacent_claims if c]
        secondary=adjacent_claims[0] if adjacent_claims else None
    else:
        ranked=sorted(claims,key=lambda c:_recommendation_anchor_score(query,c,profile),reverse=True); primary=ranked[0] if ranked else None; secondary=ranked[1] if len(ranked)>1 else None
    if not primary: return ""
    label="For someone grieving, a good place to begin is" if profile.get("grief") else "A good place to begin is"
    parts=[f"{label} [{primary['title']}]({primary['url']}).",_recommendation_wisdom(profile),_recommendation_foothold(profile),_recommendation_rationale(primary,profile),"This doorway is offered as a reflection gateway, not as a complete explanation or prescription."]
    if secondary: parts.append(f"A nearby path is [{secondary['title']}]({secondary['url']}), which opens another aspect of the question without asking you to treat either doorway as the whole answer.")
    if any(c.get("epistemic")=="interpretive" for c in claims): parts.append("Some of the Archive's material enters spiritual or cosmological interpretation; those elements remain interpretive possibilities rather than established facts.")
    return "\n\n".join(parts)

def _build_factual_answer(query,docs):
    subject=re.sub(r"^(?:what is|what's|define|explain|what does|who is|who was|where is|where was|why is|why does|how does)\s+","",query.strip(),flags=re.I).rstrip(" ?.!:"); claims=_extract_claims(_candidate_sentences(query,docs))
    if not claims or not subject: return ""
    primary=claims[0]; parts=[f"The closest supported material I found is [{primary['title']}]({primary['url']})."]
    if subject.casefold()=="overflow": parts.append("In the Archive's framing, Overflow is a way of understanding how life, meaning, and stewardship can be cultivated and passed onward rather than treated as something to accumulate or possess.")
    else: parts.append(f"Taken together, the available material approaches {subject} through several related perspectives rather than a single fixed definition.")
    if any(c["epistemic"]=="interpretive" for c in claims): parts.append("Some of the Archive's material enters spiritual or cosmological interpretation; those elements remain interpretive possibilities rather than established facts.")
    parts.append("A useful place to continue is the linked anchor, where you can see which part of the question you want to stay with or explore further.")
    return "\n\n".join(parts)

def _build_lived_experience_answer(query,docs,profile):
    claims=_extract_claims(_candidate_sentences(query,docs))
    if not claims: return ""
    anchor=claims[0]; return "\n\n".join([_recommendation_wisdom(profile),_recommendation_foothold(profile),f"The Archive offers a related lens in [{anchor['title']}]({anchor['url']}), where the material explores {anchor['text'].rstrip('.')}. This is one way into the question, not a claim that it completely explains your experience.","You can stay with this lens, follow the connected material, or return with another part of the question that feels more relevant."])

def _unified_visitor_construction(query,retrieved_docs,canonical_docs):
    profile=_inquiry_profile(query); docs=[]; seen=set()
    for doc in list(canonical_docs or [])+list(retrieved_docs or []):
        key=(str(doc.get("url") or ""),str(doc.get("title") or ""))
        if key in seen: continue
        seen.add(key); docs.append(doc)
    action=profile["action"]
    if action=="risk": return _build_risk_answer(query),"risk"
    if action in {"recommendation","navigation"}:
        answer=_recommendation_answer(query,docs,profile)
        if answer: return answer,"recommendation"
    if action=="lived":
        answer=_build_lived_experience_answer(query,docs,profile)
        if answer: return answer,"lived_experience"
    if action=="foundation": return _foundation_teacherly_answer(query),"foundation"
    if action=="conceptual":
        answer=_build_factual_answer(query,docs)
        if answer: return answer,"conceptual"
    return "","core"

def _boundary_context(args,kwargs):
    query=_extract_user_query(args,kwargs); raw_context=_context_blocks_from_kwargs(args,kwargs); canonical=str(kwargs.get("canonical_link_context") or (args[3] if len(args)>=4 and isinstance(args[3],str) else "")); return query,_parse_context_documents(raw_context),_parse_context_documents(canonical)
def _v487_generate_boundary(*args,**kwargs):
    query,retrieved_docs,canonical_docs=_boundary_context(args,kwargs); answer,mode=_unified_visitor_construction(query,retrieved_docs,canonical_docs); print(f"The Guide v487.15 visitor boundary: mode={mode}, retrieved={len(retrieved_docs)}, canonical={len(canonical_docs)}"); fallback=answer if answer else _original_generate_llm_response(*args,**kwargs); return _sanitize_visitor_output(fallback)
def _v487_evidence_gap_boundary(user_query,canonical_link_context="",retrieved_context_blocks=""):
    canonical_docs=_parse_context_documents(canonical_link_context); retrieved_docs=_parse_context_documents(retrieved_context_blocks); answer,mode=_unified_visitor_construction(user_query,retrieved_docs,canonical_docs); print(f"The Guide v487.15 evidence-gap boundary: mode={mode}, retrieved={len(retrieved_docs)}, canonical={len(canonical_docs)}"); fallback=answer if answer else _original_evidence_sufficiency_unavailable_response(user_query,canonical_link_context); return _sanitize_visitor_output(fallback)

def _calibration_contract_audit(answer,mode,risk=False):
    text=str(answer or ""); low=text.casefold()
    if risk: return {"human_reality":True,"humane_foothold":True,"epistemic_boundary":True,"risk_routing":"emergency" in low,"outward_gateway":True,"teacherly_sovereignty_voice":True}
    if mode=="foundation": return {"human_reality":bool(re.search(r"\b(?:human questions|finding your bearings|human|people)\b",low)),"humane_foothold":bool(re.search(r"\b(?:begin|finding your bearings|way to begin|enter with a question|follow a pathway|move outward)\b",low)),"epistemic_boundary":True,"risk_routing":True,"outward_gateway":True,"teacherly_sovereignty_voice":bool(re.search(r"\b(?:finding your bearings|way to begin|less a place to collect conclusions|enter with a question|move outward)\b",low))}
    return {"human_reality":bool(re.search(r"\b(?:grief|grieving|loss|mourning|bereavement|love|experience|question|uncertain|discernment|truth)\b",low)),"humane_foothold":bool(re.search(r"\b(?:for today|next step|humane next step|notice|stay with|place to begin|ask|verify)\b",low)),"epistemic_boundary":bool(re.search(r"\b(?:interpretive|possibilit(?:y|ies)|established fact|established knowledge|personal meaning|reflection gateway|not a complete explanation|not the whole answer|what can be known|what is interpretation|verify)\b",low)),"risk_routing":True,"outward_gateway":bool(re.search(r"\[[^\]]+\]\(https://geralddaquila\.com/[^)]+\)",text)) and bool(re.search(r"\b(?:nearby path|second doorway|reflection gateway|another aspect|linked anchor)\b",low)),"teacherly_sovereignty_voice":bool(re.search(r"\b(?:wisdom|you can|for today|stay with|what kind of claim|finding your bearings|open the inquiry|rather than treating it as the final word)\b",low))}

def _catalog_audit(catalog,needle):
    item=catalog.get("direct") or {}; return item.get("title","")==needle and bool(item.get("url"))
_V487_FOUNDATION_AUDIT=_foundation_teacherly_answer("What is the Living Archive?")
_V487_AI_TRUTH_AUDIT=_recommendation_answer("I keep wondering whether AI is making it harder to know what is actually true. Where should I begin in the Living Archive?",[],_inquiry_profile("I keep wondering whether AI is making it harder to know what is actually true. Where should I begin in the Living Archive?"))
_V487_FOUNDATION_CONTRACT_AUDIT=_calibration_contract_audit(_V487_FOUNDATION_AUDIT,"foundation")
_V487_CONTRACT_AUDIT=_calibration_contract_audit(_V487_AI_TRUTH_AUDIT,"recommendation")
if "Living Archive" not in _V487_FOUNDATION_AUDIT: raise RuntimeError("USE v487.15 invariant audit failed: foundation.")
if not _catalog_audit(_canonical_catalog(_inquiry_profile("AI truth")),"Truth in the Age of AI: Why Discernment Is Becoming a Survival Skill"): raise RuntimeError("USE v487.15 invariant audit failed: AI truth catalog.")
if "Truth in the Age of AI" not in _V487_AI_TRUTH_AUDIT: raise RuntimeError(f"USE v487.15 invariant audit failed: AI truth doorway={_V487_AI_TRUTH_AUDIT}")
if not all(_V487_FOUNDATION_CONTRACT_AUDIT.values()): raise RuntimeError(f"USE v487.15 foundation calibration contract failed: {_V487_FOUNDATION_CONTRACT_AUDIT}")
if not all(_V487_CONTRACT_AUDIT.values()): raise RuntimeError(f"USE v487.15 recommendation calibration contract failed: {_V487_CONTRACT_AUDIT}")
app=use_core.app; app.title=f"Find Your Way (The Guide) {APP_VERSION}"
print(f"The Guide v487.15 BUILD IDENTITY: build_id={CANONICAL_BUILD_ID}, version={APP_VERSION}, fingerprint={DEPLOYMENT_FINGERPRINT}, source_sha256={RUNTIME_SOURCE_SHA256}, core_blob_sha={_core_runtime_sha}")
use_core.APP_VERSION=APP_VERSION; use_core.DEPLOYMENT_FINGERPRINT=DEPLOYMENT_FINGERPRINT; use_core.CANONICAL_BUILD_ID=CANONICAL_BUILD_ID; use_core.RUNTIME_SOURCE_SHA256=RUNTIME_SOURCE_SHA256; use_core.EXPECTED_CORE_BLOB_SHA=EXPECTED_CORE_BLOB_SHA; use_core.generate_llm_response=_v487_generate_boundary; use_core._evidence_sufficiency_unavailable_response=_v487_evidence_gap_boundary
