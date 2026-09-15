# USE PRODUCTION VERSION: v479 — human inquiry shape calibration
import hashlib
import importlib
import re
from pathlib import Path

APP_VERSION="v479"
DEPLOYMENT_FINGERPRINT="USE-v479-human-inquiry-shape-calibration"
CANONICAL_BUILD_ID="USE-BUILD-v479-human-inquiry-shape-calibration"
EXPECTED_CORE_BLOB_SHA="fb3208a8d287f16562ffd640d89f65d5e8d18607"
_MAIN_PATH=Path(__file__).resolve(); _CORE_PATH=_MAIN_PATH.with_name("use_core.py")
RUNTIME_SOURCE_SHA256=hashlib.sha256(_MAIN_PATH.read_bytes()).hexdigest()
if not _CORE_PATH.exists(): raise RuntimeError("USE v479 package integrity failure: use_core.py is missing.")
_core_bytes=_CORE_PATH.read_bytes(); _core_runtime_sha=hashlib.sha1(f"blob {len(_core_bytes)}\0".encode()+_core_bytes).hexdigest()
if _core_runtime_sha!=EXPECTED_CORE_BLOB_SHA: raise RuntimeError(f"USE v479 package integrity failure: expected protected core blob sha={EXPECTED_CORE_BLOB_SHA}, actual={_core_runtime_sha}")
use_core=importlib.import_module("use_core"); _original_generate_llm_response=use_core.generate_llm_response; _original_handle_query=getattr(use_core,"handle_query",None); _original_evidence_sufficiency_unavailable_response=getattr(use_core,"_evidence_sufficiency_unavailable_response",None)
if _original_handle_query is None: raise RuntimeError("USE v479 package integrity failure: API query handler is unavailable.")
if not callable(_original_evidence_sufficiency_unavailable_response): raise RuntimeError("USE v479 package integrity failure: evidence-gap response boundary is unavailable.")

def _sanitize_visitor_output(text): return re.sub(r"\bUSE\b","The Guide",str(text or "")).replace("..",".")
def _normalize_title(text): return re.sub(r"^[\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F\u200D]+\s*","",str(text or "").strip()).strip()
def _valid_doc_url(doc):
    url=str(doc.get("url") or doc.get("canonical_url") or "").strip(); return url if re.match(r"^https://\S+$",url,re.I) else ""
def _query_subject(text):
    q=re.sub(r"\s+"," ",str(text or "").strip()); q=re.sub(r"^(?:what is|what's|define|explain|what does|who is|who was|where is|where was|why is|why does|how does)\s+","",q,flags=re.I); return q.rstrip(" ?.!:")
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

def _query_profile(query):
    q=re.sub(r"\s+"," ",str(query or "").strip().casefold())
    risk=bool(re.search(r"\b(?:suicid\w*|self-harm|self harm|overdose|abuse|coercion|immediate danger|unsafe|threatened|kill(?:ing)? myself|kill(?:ing)? yourself|want(?:ing)? to die|end my life|take my own life|harm myself|hurt myself)\b",q))
    foundation=bool(re.search(r"\b(?:living archive|archive|the guide|start here|begin here)\b",q))
    lived=bool(re.search(r"\b(?:i feel|i'm feeling|i am feeling|i can't|i cannot|i keep|i still|i don't know how|i don't know why|i know i need|it hurts|this hurts|my grief|my anger|my fear|my anxiety|my loneliness|my relationship|my partner|my loss|someone left|they left|letting go|let go|forgive|forgiveness|heartbreak|breakup|betrayal|abuse|trauma|overwhelmed|afraid|scared|angry|grieving|grief)\b",q))
    experiential_why=bool(re.match(r"^(?:why|how)\b",q)) and bool(re.search(r"\b(?:feel|hurt|grief|anger|fear|afraid|scared|alone|lonely|let go|letting go|forgive|forgiveness|loss|relationship|betrayal|trauma|pain)\b",q))
    navigational=bool(re.search(r"\b(?:where can i find|where do i find|where is|how do i get to|find the|browse|explore the|show me|take me to)\b",q))
    factual=bool(re.match(r"^(?:what is|what's|who is|who was|when did|where is|where was|why is|why does|how does|what does|what are|define|explain)\b",q))
    if risk: shape="risk"
    elif foundation: shape="foundation"
    elif lived or experiential_why: shape="lived_experience"
    elif navigational: shape="navigation"
    elif factual: shape="conceptual"
    else: shape="open_inquiry"
    return {"foundation":foundation,"risk":risk,"lived":lived,"navigational":navigational,"factual":factual,"shape":shape}

def _build_risk_answer(query):
    q=str(query or "").casefold()
    if re.search(r"\b(?:suicid\w*|self-harm|self harm|kill(?:ing)? myself|kill(?:ing)? yourself|want(?:ing)? to die|end my life|take my own life|harm myself|hurt myself)\b",q): return "If you are thinking about killing yourself or may act on thoughts of self-harm, please seek human help now. Call emergency services or go to the nearest emergency department, and if you can, stay with another person while you get help."
    return "If you may be in immediate danger or cannot keep yourself safe, please seek human help now. Call emergency services or go to the nearest emergency department."

def _candidate_sentences(query,docs):
    subject=_query_subject(query).casefold(); candidates=[]; seen=set()
    for doc in docs:
        if not isinstance(doc,dict) or _is_risk_related(doc): continue
        title=_normalize_title(doc.get("title") or ""); url=_valid_doc_url(doc); raw=_clean_evidence_text(doc.get("text") or "")
        if not title or not url or not raw: continue
        for sentence in [s.strip() for s in re.split(r"(?<=[.!?])\s+",raw) if s.strip()]:
            low=sentence.casefold()
            if re.search(r"\b(?:collective awakening|profound truth|we'?re all co-creators|universal knowledge|quantum thread|hypothetical)\b",low): continue
            score=0
            if subject and re.search(rf"\b{re.escape(subject)}\b",low): score+=50
            if subject and re.search(rf"\b{re.escape(subject)}\b",title.casefold()): score+=25
            if re.search(r"\b(?:is|are|means|refers to|describes|represents|relates to|pathway|stewardship|meaning|transcenden|creation|growth|grief|receiv|giv)\b",low): score+=20
            if len(sentence)>18: score+=5
            key=re.sub(r"\W+"," ",low).strip()
            if key in seen: continue
            seen.add(key); candidates.append({"score":score,"sentence":sentence,"title":title,"url":url,"worldview":_role_evidence(doc)["worldview"]})
    candidates.sort(key=lambda x:-x["score"]); return candidates[:10]

def _claim_type(sentence):
    low=sentence.casefold()
    if re.search(r"\b(?:is|are|means|refers to|describes|represents)\b",low): return "definition"
    if re.search(r"\b(?:relates to|connected with|linked to|pathway|stewardship|creation|meaning|transcenden|growth|receiv|giv)\b",low): return "relationship"
    return "exploration"
def _epistemic_type(sentence,worldview=False):
    low=sentence.casefold()
    if worldview or re.search(r"\b(?:spiritual|cosmic|cosmological|mystical|metaphysical|oversoul|afterlife|reincarnation)\b",low): return "interpretive"
    return "supported"
def _extract_claims(candidates):
    claims=[]; seen=set()
    for c in candidates:
        core=re.sub(r"\.{2,}",".",c["sentence"]).strip().rstrip(".")
        core=re.sub(r"\b(?:Connected to|Connected with)\s+the earliest flameholders\b[^.]*","",core,flags=re.I).strip()
        if not core or len(core.split())<6: continue
        normalized=re.sub(r"\s+"," ",core)
        key=re.sub(r"\W+"," ",normalized.casefold()).strip()
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
    if claims: return f"The Archive's material presents {subject} as a concept explored through several related perspectives."
    return ""

def _extract_experience_tension(query):
    q=str(query or "").strip()
    patterns=[
        (r"(?i)^(?:why\s+does|why\s+do)\s+(.+?)\s+even\s+when\s+(.+?)[?.!]*$", "understanding_vs_experience"),
        (r"(?i)^(?:how\s+can|how\s+do)\s+(.+?)\s+when\s+(.+?)[?.!]*$", "experience_vs_expectation"),
    ]
    for pattern,kind in patterns:
        m=re.match(pattern,q)
        if m: return {"kind":kind,"experience":m.group(1).strip(),"condition":m.group(2).strip()}
    return {"kind":"","experience":"","condition":""}

def _human_orientation_intro(query):
    tension=_extract_experience_tension(query)
    if tension["kind"]=="understanding_vs_experience" and tension["experience"]:
        exp=tension["experience"]
        cond=tension["condition"]
        return f"It can be painful when {exp} even when {cond}. Understanding what needs to change does not always make the feeling itself disappear at the same pace."
    return ""

def _human_foothold(query):
    tension=_extract_experience_tension(query)
    if tension["kind"]=="understanding_vs_experience":
        return "A gentle place to begin is to let the feeling be present without treating its persistence as proof that you are failing to move forward."
    if tension["kind"]=="experience_vs_expectation":
        return "A gentle place to begin is to make room for what you are actually experiencing before deciding what it ought to mean."
    return "A gentle place to begin is to stay with the part of the question that feels most alive, rather than forcing it into a conclusion too quickly."

def _select_human_anchor(claims):
    if not claims: return None
    priority=[c for c in claims if re.search(r"\b(?:grief|loss|receiv|giv|growth|relationship|forgiv|anger|fear|pain|letting go)\b",c["text"].casefold())]
    return priority[0] if priority else claims[0]

def _build_lived_experience_answer(query,docs):
    candidates=_candidate_sentences(query,docs); claims=_extract_claims(candidates)
    if not claims: return ""
    anchor=_select_human_anchor(claims)
    parts=[]
    intro=_human_orientation_intro(query)
    if intro: parts.append(intro)
    else: parts.append("What you are describing can make sense as a human tension that does not have to be resolved by explanation alone.")
    parts.append(_human_foothold(query))
    if anchor:
        parts.append(f"The Archive offers a related lens in [{anchor['title']}]({anchor['url']}), where the material explores {anchor['text'].rstrip('.')}. This is one way into the question, not a claim that it completely explains your experience.")
    bridge="Taken together, the material here points toward a distinction between understanding something intellectually and being emotionally ready for what it asks of you. That distinction can leave room for grief, uncertainty, or ambivalence without making those responses a failure."
    parts.append(bridge)
    if any(c["epistemic"]=="interpretive" for c in claims): parts.append("Some of the Archive's material also enters spiritual or cosmological interpretation; those elements are presented as interpretive perspectives rather than established fact.")
    parts.append("You can stay with that lens, or follow the adjacent writing from the anchor if another aspect of the question feels more relevant.")
    return "\n\n".join(parts)

def _render_claim(claim): return claim["text"].rstrip(".")+"."

def _build_factual_answer(query,docs):
    subject=_query_subject(query); candidates=_candidate_sentences(query,docs)
    if not candidates or not subject: return ""
    claims=_extract_claims(candidates); groups=_related_claims(claims)
    if not claims: return ""
    primary=claims[0]; parts=[f"The closest supported material I found is [{primary['title']}]({primary['url']}).",_plain_language_concept(subject,claims)]
    support=[]
    for claim in claims:
        text=_render_claim(claim)
        if text not in support and len(support)<3 and text.casefold()!=parts[1].casefold(): support.append(text)
    bridge=_semantic_bridge(subject,groups)
    if bridge: parts.append(bridge + ((" " + " ".join(support[:2])) if support else ""))
    if any(c["epistemic"]=="interpretive" for c in claims): parts.append("Some of the Archive's material also enters spiritual or cosmological interpretation; those elements are presented here as interpretive perspectives rather than established fact.")
    parts.append("A useful place to continue is the linked anchor, where you can see which part of the question you want to stay with or explore further.")
    return "\n\n".join(parts)

def _build_foundation_answer(): return "The Living Archive is a connected body of essays, perspectives, frameworks, and pathways for making sense of complex human questions without reducing them to a single answer."

def _unified_visitor_construction(query,retrieved_docs,canonical_docs):
    profile=_query_profile(query); docs=[]; seen=set()
    for doc in list(canonical_docs or [])+list(retrieved_docs or []):
        key=(str(doc.get("url") or ""),str(doc.get("title") or ""))
        if key in seen: continue
        seen.add(key); docs.append(doc)
    if profile["risk"]: return _build_risk_answer(query),"risk"
    if profile["foundation"]: return _build_foundation_answer(),"foundation"
    if profile["shape"]=="lived_experience":
        answer=_build_lived_experience_answer(query,docs)
        if answer: return answer,"lived_experience"
    if profile["factual"] or profile["shape"]=="conceptual":
        answer=_build_factual_answer(query,docs)
        if answer: return answer,"conceptual"
    return "","core"

def _boundary_context(args,kwargs):
    query=_extract_user_query(args,kwargs); raw_context=_context_blocks_from_kwargs(args,kwargs); canonical=str(kwargs.get("canonical_link_context") or (args[3] if len(args)>=4 and isinstance(args[3],str) else "")); return query,_parse_context_documents(raw_context),_parse_context_documents(canonical)
def _v479_generate_boundary(*args,**kwargs):
    query,retrieved_docs,canonical_docs=_boundary_context(args,kwargs); answer,mode=_unified_visitor_construction(query,retrieved_docs,canonical_docs); print(f"The Guide v479 visitor boundary: mode={mode}, retrieved={len(retrieved_docs)}, canonical={len(canonical_docs)}"); return _sanitize_visitor_output(answer if answer else _original_generate_llm_response(*args,**kwargs))
def _v479_evidence_gap_boundary(user_query,canonical_link_context="",retrieved_context_blocks=""):
    canonical_docs=_parse_context_documents(canonical_link_context); retrieved_docs=_parse_context_documents(retrieved_context_blocks); answer,mode=_unified_visitor_construction(user_query,retrieved_docs,canonical_docs); print(f"The Guide v479 evidence-gap boundary: mode={mode}, retrieved={len(retrieved_docs)}, canonical={len(canonical_docs)}"); return _sanitize_visitor_output(answer if answer else _original_evidence_sufficiency_unavailable_response(user_query,canonical_link_context))

_V479_FOUNDATION_AUDIT=_build_foundation_answer()
_V479_FACTUAL_DOC={"title":"Codex of the Overflow Pathway","url":"https://geralddaquila.com/overflow-2/","text":"Overflow relates to meaning, transcendence, creation, and stewardship. Connected to the earliest flameholders who discovered that breath was the simplest and most direct pathway to sustaining Overflow resonance, even without ritual or form.."}
_V479_FACTUAL_AUDIT=_build_factual_answer("What is Overflow?",[_V479_FACTUAL_DOC])
_V479_LIVED_AUDIT=_build_lived_experience_answer("Why does grief still hurt even when I know I need to let go?",[{"title":"Learning to Receive Without Feeling Guilty","url":"https://geralddaquila.com/2026/02/02/learning-to-receive-without-feeling-guilty/","text":"Giving and Receiving Are One System. Your mind might say: ‘I’m letting them down.’ But often what’s really happening is: ‘I’m no longer abandoning myself to keep everything comfortable.’ That’s growth."}])
if "living archive" not in _V479_FOUNDATION_AUDIT.casefold(): raise RuntimeError("USE v479 visitor foundation audit failed.")
if "Overflow" not in _V479_FACTUAL_AUDIT: raise RuntimeError("USE v479 visitor factual audit failed: expected subject missing.")
if ".." in _V479_FACTUAL_AUDIT: raise RuntimeError("USE v479 visitor factual audit failed: duplicate punctuation survived normalization.")
if "Connected to the earliest flameholders" in _V479_FACTUAL_AUDIT or "sustaining Overflow resonance" in _V479_FACTUAL_AUDIT: raise RuntimeError("USE v479 visitor factual audit failed: forbidden source fragment leaked.")
if "Taken together" not in _V479_FACTUAL_AUDIT: raise RuntimeError("USE v479 visitor factual audit failed: semantic synthesis bridge missing.")
if "grief" not in _V479_LIVED_AUDIT.casefold() or "gentle place to begin" not in _V479_LIVED_AUDIT.casefold() or "Learning to Receive Without Feeling Guilty" not in _V479_LIVED_AUDIT: raise RuntimeError("USE v479 lived-experience audit failed: humane orientation path missing.")
app=use_core.app; app.title=f"Find Your Way (The Guide) {APP_VERSION}"; print(f"The Guide v479 BUILD IDENTITY: build_id={CANONICAL_BUILD_ID}, version={APP_VERSION}, fingerprint={DEPLOYMENT_FINGERPRINT}, source_sha256={RUNTIME_SOURCE_SHA256}, core_blob_sha256={_core_runtime_sha}"); use_core.APP_VERSION=APP_VERSION; use_core.DEPLOYMENT_FINGERPRINT=DEPLOYMENT_FINGERPRINT; use_core.CANONICAL_BUILD_ID=CANONICAL_BUILD_ID; use_core.RUNTIME_SOURCE_SHA256=RUNTIME_SOURCE_SHA256; use_core.EXPECTED_CORE_BLOB_SHA=EXPECTED_CORE_BLOB_SHA; use_core.generate_llm_response=_v479_generate_boundary; use_core._evidence_sufficiency_unavailable_response=_v479_evidence_gap_boundary
