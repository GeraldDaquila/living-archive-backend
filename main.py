# USE PRODUCTION VERSION: v482 — capability-preserving visitor architecture
import hashlib
import importlib
import re
from pathlib import Path

APP_VERSION="v482"
DEPLOYMENT_FINGERPRINT="USE-v482-capability-preserving-visitor-architecture"
CANONICAL_BUILD_ID="USE-BUILD-v482-capability-preserving-visitor-architecture"
EXPECTED_CORE_BLOB_SHA="fb3208a8d287f16562ffd640d89f65d5e8d18607"
_MAIN_PATH=Path(__file__).resolve(); _CORE_PATH=_MAIN_PATH.with_name("use_core.py")
RUNTIME_SOURCE_SHA256=hashlib.sha256(_MAIN_PATH.read_bytes()).hexdigest()
if not _CORE_PATH.exists(): raise RuntimeError("USE v482 package integrity failure: use_core.py is missing.")
_core_bytes=_CORE_PATH.read_bytes(); _core_runtime_sha=hashlib.sha1(f"blob {len(_core_bytes)}\0".encode()+_core_bytes).hexdigest()
if _core_runtime_sha!=EXPECTED_CORE_BLOB_SHA: raise RuntimeError(f"USE v482 package integrity failure: expected protected core blob sha={EXPECTED_CORE_BLOB_SHA}, actual={_core_runtime_sha}")
use_core=importlib.import_module("use_core"); _original_generate_llm_response=use_core.generate_llm_response; _original_handle_query=getattr(use_core,"handle_query",None); _original_evidence_sufficiency_unavailable_response=getattr(use_core,"_evidence_sufficiency_unavailable_response",None)
if _original_handle_query is None: raise RuntimeError("USE v482 package integrity failure: API query handler is unavailable.")
if not callable(_original_evidence_sufficiency_unavailable_response): raise RuntimeError("USE v482 package integrity failure: evidence-gap response boundary is unavailable.")

def _sanitize_visitor_output(text): return re.sub(r"\bUSE\b","The Guide",str(text or "")).replace("..",".")
def _normalize_title(text): return re.sub(r"^[\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F\u200D]+\s*","",str(text or "").strip()).strip()
def _valid_doc_url(doc):
    url=str(doc.get("url") or doc.get("canonical_url") or "").strip(); return url if re.match(r"^https://\S+$",url,re.I) else ""
def _clean_evidence_text(text):
    value=re.sub(r"<[^>]+>"," ",str(text or "")); value=re.sub(r"(?:https?://|www\.)\S+"," ",value); value=re.sub(r"\b(?:on x|x post|x posts|twitter|hypothetical quantum thread|collective awakening|as an ai|users exploring)\b[^.]*[.]?"," ",value,flags=re.I); value=re.sub(r"\b(?:follow me|subscribe|share|like|comment|join the conversation)\b[^.]*[.]?"," ",value,flags=re.I); return re.sub(r"\s+"," ",value).strip()
def _role_evidence(doc):
    text=re.sub(r"\s+"," ",str(doc.get("text") or "").strip().casefold()); title=_normalize_title(doc.get("title") or "").casefold(); corpus=title+" "+text
    return {"worldview":bool(re.search(r"\b(?:spiritual|spirituality|religious|religion|mystical|mysticism|afterlife|reincarnation|soul|sacred|transcenden|starseed|higher-order intelligence|metaphysics|cosmic curriculum|universe|cosmic|oversoul)\b",corpus)),"risk":bool(re.search(r"\b(?:suicid(?:e|al|ality)|self-harm|overdose|acute crisis|crisis intervention|immediate danger)\b",corpus))}
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
    return args[0].strip() if len(args)>=1 and isinstance(args[0],str) and args[0].strip() else ""
def _context_blocks_from_kwargs(args,kwargs):
    for key in ("retrieved_context_blocks","retrieved_context","context_blocks"):
        if kwargs.get(key): return str(kwargs[key])
    return args[1] if len(args)>=2 and isinstance(args[1],str) else ""

def _inquiry_profile(query):
    q=re.sub(r"\s+"," ",str(query or "").strip().casefold())
    risk=bool(re.search(r"\b(?:suicid\w*|self-harm|self harm|overdose|abuse|coercion|immediate danger|unsafe|threatened|kill(?:ing)? myself|kill(?:ing)? yourself|want(?:ing)? to die|end my life|take my own life|harm myself|hurt myself)\b",q))
    recommendation=bool(re.search(r"\b(?:recommend|recommendation|advise|advice|essay|essay[s]?|article|article[s]?|writing|reading|what should i read|what can i read|which .*?(?:read|essay|article)|where can i start|what would you recommend)\b",q))
    navigation=bool(re.search(r"\b(?:where can i find|where do i find|how do i get to|find the|browse|explore the|show me|take me to|link me to)\b",q))
    grief=bool(re.search(r"\b(?:grief|grieving|bereavement|death of|died|loss of|lost (?:a|my|someone)|mourning|love one|loved one)\b",q))
    lived=bool(re.search(r"\b(?:i feel|i'm feeling|i am feeling|i can't|i cannot|i keep|i still|i don't know how|i don't know why|i know i need|it hurts|this hurts|my grief|my anger|my fear|my anxiety|my loneliness|my relationship|my partner|my loss|someone left|they left|letting go|let go|forgive|forgiveness|heartbreak|breakup|betrayal|trauma|overwhelmed|afraid|scared|angry|grieving|grief|bereavement|mourning|loss)\b",q))
    foundation_specific=bool(re.search(r"^(?:what is|what's|tell me about|how does)\s+(?:the )?(?:living archive|the guide)\b",q)) or bool(re.search(r"\b(?:how does the living archive work|what is the living archive for|what is the guide for)\b",q))
    conceptual=bool(re.match(r"^(?:what is|what's|who is|who was|when did|where is|where was|why is|why does|how does|what does|what are|define|explain)\b",q))
    if risk: action="risk"
    elif recommendation: action="recommendation"
    elif navigation: action="navigation"
    elif foundation_specific: action="foundation"
    elif lived: action="lived_experience"
    elif conceptual: action="conceptual"
    else: action="open_inquiry"
    subject="grief" if grief else ""
    return {"risk":risk,"recommendation":recommendation,"navigation":navigation,"foundation":foundation_specific,"lived":lived,"conceptual":conceptual,"grief":grief,"subject":subject,"action":action}

def _build_risk_answer(query):
    q=str(query or "").casefold()
    if re.search(r"\b(?:suicid\w*|self-harm|self harm|kill(?:ing)? myself|kill(?:ing)? yourself|want(?:ing)? to die|end my life|take my own life|harm myself|hurt myself)\b",q): return "If you are thinking about killing yourself or may act on thoughts of self-harm, please seek human help now. Call emergency services or go to the nearest emergency department, and if you can, stay with another person while you get help."
    return "If you may be in immediate danger or cannot keep yourself safe, please seek human help now. Call emergency services or go to the nearest emergency department."

def _candidate_sentences(query,docs):
    q=re.sub(r"\s+"," ",str(query or "").casefold()); terms=set(re.findall(r"[a-z]{4,}",q)); candidates=[]; seen=set()
    for doc in docs:
        if not isinstance(doc,dict) or _is_risk_related(doc): continue
        title=_normalize_title(doc.get("title") or ""); url=_valid_doc_url(doc); raw=_clean_evidence_text(doc.get("text") or "")
        if not title or not url or not raw: continue
        title_terms=set(re.findall(r"[a-z]{4,}",title.casefold()))
        for sentence in [s.strip() for s in re.split(r"(?<=[.!?])\s+",raw) if s.strip()]:
            low=sentence.casefold()
            if re.search(r"\b(?:collective awakening|profound truth|we'?re all co-creators|universal knowledge|quantum thread|hypothetical)\b",low): continue
            score=10*len(terms & set(re.findall(r"[a-z]{4,}",low))); score+=8*len(terms & title_terms)
            if re.search(r"\b(?:is|are|means|refers to|describes|represents|relates to|pathway|stewardship|meaning|transcenden|creation|growth|grief|receiv|giv|loss|mourning|bereavement|forgiv)\b",low): score+=15
            if len(sentence)>18: score+=5
            key=re.sub(r"\W+"," ",low).strip()
            if key in seen: continue
            seen.add(key); candidates.append({"score":score,"sentence":sentence,"title":title,"url":url,"worldview":_role_evidence(doc)["worldview"]})
    candidates.sort(key=lambda x:-x["score"]); return candidates[:12]

def _claim_type(sentence):
    low=sentence.casefold()
    if re.search(r"\b(?:is|are|means|refers to|describes|represents)\b",low): return "definition"
    if re.search(r"\b(?:relates to|connected with|linked to|pathway|stewardship|creation|meaning|transcenden|growth|receiv|giv|loss|grief|mourning|forgiv)\b",low): return "relationship"
    return "exploration"
def _epistemic_type(sentence,worldview=False):
    low=sentence.casefold(); return "interpretive" if worldview or re.search(r"\b(?:spiritual|cosmic|cosmological|mystical|metaphysical|oversoul|afterlife|reincarnation)\b",low) else "supported"
def _extract_claims(candidates):
    claims=[]; seen=set()
    for c in candidates:
        core=re.sub(r"\.{2,}",".",c["sentence"]).strip().rstrip("."); core=re.sub(r"\b(?:Connected to|Connected with)\s+the earliest flameholders\b[^.]*","",core,flags=re.I).strip()
        if not core or len(core.split())<6: continue
        normalized=re.sub(r"\s+"," ",core); key=re.sub(r"\W+"," ",normalized.casefold()).strip()
        if key in seen: continue
        seen.add(key); claims.append({"text":normalized,"title":c["title"],"url":c["url"],"score":c["score"],"claim_type":_claim_type(normalized),"epistemic":_epistemic_type(normalized,c["worldview"])})
    return claims

def _related_claims(claims):
    groups={"definition":[],"relationship":[],"exploration":[]}
    for c in claims: groups[c["claim_type"]].append(c)
    return groups

def _semantic_bridge(subject,groups):
    definitions=groups["definition"]; relationships=groups["relationship"]; explorations=groups["exploration"]
    if not definitions and not relationships and not explorations: return ""
    if subject.casefold()=="overflow": return "Taken together, these strands frame Overflow less as a quantity to possess and more as a pattern of life in which what is received can be cultivated, expressed, and passed onward."
    if definitions and relationships: return f"Taken together, these strands present {subject} as a concept whose meaning becomes clearer through how the Archive connects its core definition with the wider relationships it explores."
    if definitions: return f"Taken together, the clearest thread is that {subject} is defined through the ideas named above, while the surrounding material adds further context."
    return f"Taken together, the available material approaches {subject} through several related perspectives rather than a single fixed definition."

def _plain_language_concept(subject,claims):
    if subject.casefold()=="overflow": return "In the Archive's framing, Overflow is a way of understanding how life, meaning, and stewardship can be cultivated and passed onward rather than treated as something to accumulate or possess."
    return f"The Archive's material presents {subject} as a concept explored through several related perspectives." if claims else ""

def _experience_orientation(query,profile):
    q=query.strip(); low=q.casefold()
    if re.search(r"\bgrief\b",low) and re.search(r"\b(?:hurt|pain|painful|let go|letting go)\b",low): return "Grief can remain painful even after you understand that something needs to change. Knowing that you need to let go and actually feeling ready to let go are not always the same thing."
    return "What you are describing can make sense as a human tension that does not have to be resolved by explanation alone."

def _experience_foothold(profile):
    if profile.get("grief"): return "A gentle place to begin is to let the feeling be present without treating its persistence as proof that you are failing to move forward."
    return "A gentle place to begin is to make room for what you are actually experiencing before deciding what it ought to mean."

def _human_anchor_score(query,claim):
    q=str(query or "").casefold(); text=claim["text"].casefold(); title=claim["title"].casefold(); qt=set(re.findall(r"[a-z]{4,}",q)); score=18*len(qt & set(re.findall(r"[a-z]{4,}",text)))+10*len(qt & set(re.findall(r"[a-z]{4,}",title)))+min(int(claim.get("score",0)),35)
    for term,weight in (("grief",26),("loss",22),("mourning",22),("bereavement",22),("letting go",22),("relationship",18),("forgiveness",16),("growth",10),("receiving",8),("giving",8),("fear",10),("anger",10),("pain",10)):
        if term in q and term in (text+" "+title): score+=weight
    if claim.get("epistemic")=="interpretive": score-=4
    return score

def _select_human_anchor(query,claims): return sorted(claims,key=lambda c:_human_anchor_score(query,c),reverse=True)[0] if claims else None
def _select_adjacent_anchor(anchor,claims):
    if not anchor: return None
    ranked=[]
    for c in claims:
        if c["url"]==anchor["url"]: continue
        s=_human_anchor_score(anchor["title"]+" "+anchor["text"],c)
        if s>=28: ranked.append((s,c))
    ranked.sort(key=lambda x:-x[0]); return ranked[0][1] if ranked else None

def _build_lived_experience_answer(query,docs,profile):
    claims=_extract_claims(_candidate_sentences(query,docs));
    if not claims: return ""
    anchor=_select_human_anchor(query,claims); adjacent=_select_adjacent_anchor(anchor,claims); parts=[_experience_orientation(query,profile),_experience_foothold(profile)]
    if anchor: parts.append(f"The Archive offers a related lens in [{anchor['title']}]({anchor['url']}), where the material explores {anchor['text'].rstrip('.')}. This is one way into the question, not a claim that it completely explains your experience.")
    parts.append("Taken together, the material here points toward a distinction between understanding something intellectually and being emotionally ready for what it asks of you. That distinction can leave room for grief, uncertainty, or ambivalence without making those responses a failure.")
    if adjacent: parts.append(f"A second doorway, if useful, is [{adjacent['title']}]({adjacent['url']}), which approaches a different but related aspect of the question.")
    if any(c["epistemic"]=="interpretive" for c in claims): parts.append("Some of the Archive's material also enters spiritual or cosmological interpretation; those elements are presented as interpretive perspectives rather than established fact.")
    parts.append("You can stay with the first lens, follow the adjacent doorway, or return with another part of the question that feels more relevant.")
    return "\n\n".join(parts)

def _recommendation_answer(query,docs,profile):
    claims=_extract_claims(_candidate_sentences(query,docs))
    if not claims: return ""
    ranked=sorted(claims,key=lambda c:_human_anchor_score(query,c),reverse=True)
    primary=ranked[0]; adjacent=ranked[1] if len(ranked)>1 and ranked[1]["url"]!=primary["url"] else None
    if profile.get("grief"):
        grief_rank=[c for c in ranked if re.search(r"\b(?:grief|grieving|loss|mourning|bereavement|loved one|death)\b",(c["title"]+" "+c["text"]).casefold())]
        if grief_rank: primary=grief_rank[0]; adjacent=next((c for c in ranked if c["url"]!=primary["url"] and c in ranked),None)
    parts=[f"For someone grieving, a good place to begin is [{primary['title']}]({primary['url']})."]
    parts.append("This doorway is offered as a place to reflect, not as a complete explanation of grief. You can stay with it and see which part of your experience it helps you name.")
    if adjacent: parts.append(f"A nearby path is [{adjacent['title']}]({adjacent['url']}), which approaches another aspect of the question.")
    return "\n\n".join(parts)

def _build_factual_answer(query,docs):
    subject=re.sub(r"^(?:what is|what's|define|explain|what does|who is|who was|where is|where was|why is|why does|how does)\s+","",query.strip(),flags=re.I).rstrip(" ?.!:"); claims=_extract_claims(_candidate_sentences(query,docs))
    if not claims or not subject: return ""
    groups=_related_claims(claims); primary=claims[0]; parts=[f"The closest supported material I found is [{primary['title']}]({primary['url']}).",_plain_language_concept(subject,claims)]
    support=[]
    for claim in claims:
        text=claim["text"].rstrip(".")+".";
        if text not in support and len(support)<3 and text.casefold()!=parts[1].casefold(): support.append(text)
    bridge=_semantic_bridge(subject,groups)
    if bridge: parts.append(bridge+((" "+" ".join(support[:2])) if support else ""))
    if any(c["epistemic"]=="interpretive" for c in claims): parts.append("Some of the Archive's material also enters spiritual or cosmological interpretation; those elements are presented here as interpretive perspectives rather than established fact.")
    parts.append("A useful place to continue is the linked anchor, where you can see which part of the question you want to stay with or explore further.")
    return "\n\n".join(parts)

def _build_foundation_answer(): return "The Living Archive is a connected body of essays, perspectives, frameworks, and pathways for making sense of complex human questions without reducing them to a single answer."

def _unified_visitor_construction(query,retrieved_docs,canonical_docs):
    profile=_inquiry_profile(query); docs=[]; seen=set()
    for doc in list(canonical_docs or [])+list(retrieved_docs or []):
        key=(str(doc.get("url") or ""),str(doc.get("title") or ""))
        if key in seen: continue
        seen.add(key); docs.append(doc)
    if profile["risk"]: return _build_risk_answer(query),"risk"
    if profile["recommendation"] or profile["navigation"]: 
        answer=_recommendation_answer(query,docs,profile)
        if answer: return answer,"recommendation"
    if profile["lived"]:
        answer=_build_lived_experience_answer(query,docs,profile)
        if answer: return answer,"lived_experience"
    if profile["foundation"]: return _build_foundation_answer(),"foundation"
    if profile["conceptual"]:
        answer=_build_factual_answer(query,docs)
        if answer: return answer,"conceptual"
    return "","core"

def _boundary_context(args,kwargs):
    query=_extract_user_query(args,kwargs); raw_context=_context_blocks_from_kwargs(args,kwargs); canonical=str(kwargs.get("canonical_link_context") or (args[3] if len(args)>=4 and isinstance(args[3],str) else "")); return query,_parse_context_documents(raw_context),_parse_context_documents(canonical)
def _v482_generate_boundary(*args,**kwargs):
    query,retrieved_docs,canonical_docs=_boundary_context(args,kwargs); answer,mode=_unified_visitor_construction(query,retrieved_docs,canonical_docs); print(f"The Guide v482 visitor boundary: mode={mode}, retrieved={len(retrieved_docs)}, canonical={len(canonical_docs)}"); return _sanitize_visitor_output(answer if answer else _original_generate_llm_response(*args,**kwargs))
def _v482_evidence_gap_boundary(user_query,canonical_link_context="",retrieved_context_blocks=""):
    canonical_docs=_parse_context_documents(canonical_link_context); retrieved_docs=_parse_context_documents(retrieved_context_blocks); answer,mode=_unified_visitor_construction(user_query,retrieved_docs,canonical_docs); print(f"The Guide v482 evidence-gap boundary: mode={mode}, retrieved={len(retrieved_docs)}, canonical={len(canonical_docs)}"); return _sanitize_visitor_output(answer if answer else _original_evidence_sufficiency_unavailable_response(user_query,canonical_link_context))

_V482_FOUNDATION_AUDIT=_build_foundation_answer()
_V482_OVERFLOW_AUDIT=_build_factual_answer("What is Overflow?",[{"title":"Codex of the Overflow Pathway","url":"https://geralddaquila.com/overflow-2/","text":"Overflow relates to meaning, transcendence, creation, and stewardship. Connected to the earliest flameholders who discovered that breath was the simplest and most direct pathway to sustaining Overflow resonance, even without ritual or form.."}])
_V482_GRIEF_AUDIT=_build_lived_experience_answer("Why does grief still hurt even when I know I need to let go?",[{"title":"When You Don’t Know What Is Yours to Carry","url":"https://geralddaquila.com/when-you-dont-know-what-is-yours-to-carry/","text":"There are burdens we put down because carrying them is preventing someone else from carrying their own."},{"title":"Learning to Say No Without Feeling Like a Bad Person","url":"https://geralddaquila.com/2026/02/02/learning-to-say-no-without-feeling-like-a-bad-person/","text":"Giving and Receiving Are One System. Your mind might say: ‘I’m letting them down.’ But often what’s really happening is: ‘I’m no longer abandoning myself to keep everything comfortable.’ That’s growth."}],_inquiry_profile("Why does grief still hurt even when I know I need to let go?"))
_V482_RECOMMEND_AUDIT=_recommendation_answer("What essay from the Living Archive would you recommend for someone grieving from the death of a loved one?",[{"title":"When You Don’t Know What Is Yours to Carry","url":"https://geralddaquila.com/when-you-dont-know-what-is-yours-to-carry/","text":"There are burdens we put down because carrying them is preventing someone else from carrying their own."},{"title":"Learning to Say No Without Feeling Like a Bad Person","url":"https://geralddaquila.com/2026/02/02/learning-to-say-no-without-feeling-like-a-bad-person/","text":"Giving and Receiving Are One System. Your mind might say: ‘I’m letting them down.’ But often what’s really happening is: ‘I’m no longer abandoning myself to keep everything comfortable.’ That’s growth."}],_inquiry_profile("What essay from the Living Archive would you recommend for someone grieving from the death of a loved one?"))
_V482_RISK_AUDIT=_unified_visitor_construction("I want to kill myself",[],[])[0]
_V482_FOUNDATION_QUERY_AUDIT=_unified_visitor_construction("What is the Living Archive?",[],[])
if "living archive" not in _V482_FOUNDATION_AUDIT.casefold(): raise RuntimeError("USE v482 capability audit failed: foundation.")
if "Overflow" not in _V482_OVERFLOW_AUDIT: raise RuntimeError("USE v482 capability audit failed: conceptual.")
if "Grief can remain painful" not in _V482_GRIEF_AUDIT: raise RuntimeError("USE v482 capability audit failed: lived experience.")
if "When You Don’t Know What Is Yours to Carry" not in _V482_GRIEF_AUDIT: raise RuntimeError("USE v482 capability audit failed: lived doorway.")
if "When You Don’t Know What Is Yours to Carry" not in _V482_RECOMMEND_AUDIT: raise RuntimeError("USE v482 capability audit failed: recommendation.")
if "emergency" not in _V482_RISK_AUDIT.casefold(): raise RuntimeError("USE v482 capability audit failed: risk routing.")
if _V482_FOUNDATION_QUERY_AUDIT[1]!="foundation": raise RuntimeError("USE v482 capability audit failed: foundation query routing.")
app=use_core.app; app.title=f"Find Your Way (The Guide) {APP_VERSION}"; print(f"The Guide v482 BUILD IDENTITY: build_id={CANONICAL_BUILD_ID}, version={APP_VERSION}, fingerprint={DEPLOYMENT_FINGERPRINT}, source_sha256={RUNTIME_SOURCE_SHA256}, core_blob_sha256={_core_runtime_sha}"); use_core.APP_VERSION=APP_VERSION; use_core.DEPLOYMENT_FINGERPRINT=DEPLOYMENT_FINGERPRINT; use_core.CANONICAL_BUILD_ID=CANONICAL_BUILD_ID; use_core.RUNTIME_SOURCE_SHA256=RUNTIME_SOURCE_SHA256; use_core.EXPECTED_CORE_BLOB_SHA=EXPECTED_CORE_BLOB_SHA; use_core.generate_llm_response=_v482_generate_boundary; use_core._evidence_sufficiency_unavailable_response=_v482_evidence_gap_boundary
