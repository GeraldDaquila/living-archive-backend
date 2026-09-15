# USE PRODUCTION VERSION: v464 — distributed concept synthesis
import hashlib
import importlib
import re
from pathlib import Path

APP_VERSION = "v464"
DEPLOYMENT_FINGERPRINT = "USE-v464-distributed-concept-synthesis"
CANONICAL_BUILD_ID = "USE-BUILD-v464-distributed-concept-synthesis"
EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"

_MAIN_PATH = Path(__file__).resolve()
_CORE_PATH = _MAIN_PATH.with_name("use_core.py")
RUNTIME_SOURCE_SHA256 = hashlib.sha256(_MAIN_PATH.read_bytes()).hexdigest()
if not _CORE_PATH.exists(): raise RuntimeError("USE v464 package integrity failure: use_core.py is missing.")
_core_bytes = _CORE_PATH.read_bytes()
_core_runtime_sha = hashlib.sha1(f"blob {len(_core_bytes)}\0".encode() + _core_bytes).hexdigest()
if _core_runtime_sha != EXPECTED_CORE_BLOB_SHA: raise RuntimeError(f"USE v464 package integrity failure: expected protected core blob sha={EXPECTED_CORE_BLOB_SHA}, actual={_core_runtime_sha}")
use_core = importlib.import_module("use_core")
_original_generate_llm_response = use_core.generate_llm_response
_original_handle_query = getattr(use_core, "handle_query", None)
_original_evidence_sufficiency_unavailable_response = getattr(use_core, "_evidence_sufficiency_unavailable_response", None)
if _original_handle_query is None: raise RuntimeError("USE v464 package integrity failure: API query handler is unavailable.")
if not callable(_original_evidence_sufficiency_unavailable_response): raise RuntimeError("USE v464 package integrity failure: evidence-gap response boundary is unavailable.")

def _query_profile(user_query: str) -> dict:
    q=re.sub(r"\s+"," ",str(user_query or "").strip().casefold())
    return {"foundation_open":bool(re.search(r"\b(?:what is|what's|how does|how do|where do i|where should i|where can i|what can i|tell me about)\b",q)) and bool(re.search(r"\b(?:living archive|archive|guide|start|begin|work|purpose|find here|about this)\b",q)),"loneliness":bool(re.search(r"\b(?:loneliness|lonely|alone|isolat|disconnected|belonging|connection)\b",q)),"risk":bool(re.search(r"\b(?:suicid\w*|self-harm|self harm|overdose|abuse|coercion|immediate danger|unsafe|threatened|kill(?:ing)? myself|kill(?:ing)? yourself|want(?:ing)? to die|don't want to (?:live|be here)|do not want to (?:live|be here)|end my life|take my own life|harm myself|hurt myself|better off dead|wish I were dead)\b",q)),"coercion_open":bool(re.search(r"\b(?:controlling|control(?:led|s)?|coercion|coercive|making me feel|can't trust my own judgment|cannot trust my own judgment|undermine(?:s|d)? my judgment|question my own judgment|isolat(?:es|ed)? me|controls what i do|controls what i wear|controls who i see|controls who i talk to|power over me|makes decisions for me)\b",q)) and bool(re.search(r"\b(?:someone in my life|partner|spouse|relationship|person|trust my own judgment|judgment|control|controlling|coercion|worry|worried|concerned|understand|happening|help|power|choice|freedom|safety)\b",q)),"emptiness_open":bool(re.search(r"\b(?:empty|emptiness|numb|numbness|disconnected from my life|disconnected from life|feel disconnected|disconnected|going through the motions|nothing is obviously wrong|nothing is wrong|all right on paper|everything is fine|feel absent from my life)\b",q)) and bool(re.search(r"\b(?:life|my life|unhappy|happiness|numb|empty|disconnected|understand|happening|help|supposed to|supposed)\b",q)),"meaning_open":bool(re.search(r"\b(?:what gives life meaning|meaning in life|what makes life meaningful|what matters|purpose|larger meaning|meaning behind)\b",q)) and bool(re.search(r"\b(?:lost|not sure|don't know|do not know|uncertain|explore|exploring|where might i begin|where should i begin|going through|believe|belief|what to believe)\b",q)),"transition_open":bool(re.search(r"\b(?:old way|no longer works|what comes next|next chapter|different way of seeing|way of seeing.*no longer|transition|turning point|threshold|outgrown|outgrew|no longer feels like me|changed so much|life has changed|change it|changing|what no longer fits|what no longer feels right|built.*afraid.*lose|afraid.*lose.*change|move on|moving on|new chapter|leave.*behind|letting go|rebuild|starting over|reinvent)\b",q)) and bool(re.search(r"\b(?:life|my life|what comes next|think|explore|help|built|change|changed|fits|right|lose|leaving|starting|begin|next)\b",q)),"grief":bool(re.search(r"\b(?:griev\w*|grief|mourning|death of (?:a|my|their) (?:love|loved) one|loss of (?:a|my|their) (?:love|loved) one|someone (?:i|we|they) love(?:d)? died)\b",q)),"fear_open":bool(re.search(r"\b(?:scared|afraid|fear|fearful|frightened|terrified|anxious|anxiety|uneasy|uncertain|uncertainty)\b",q)) and bool(re.search(r"\b(?:what(?:'s| is) happening|happening|make sense|understand|explore|help|don't know|do not know|not sure|life|going on)\b",q)),"anger_open":bool(re.search(r"\b(?:angr\w*|furious|resent\w*|resentment|frustrat\w*|frustration|bitter\w*|bitterness)\b",q)) and bool(re.search(r"\b(?:life|carrying|long time|understand|understanding|help|doing to me|happened|turned out|going on|explore)\b",q)),"ambiguous_loss_open":bool(re.search(r"\b(?:lost something important|lost something|can't quite put my finger|not sure whether i'm grieving|not sure whether i am grieving|grieving, changing|changing, or just stuck|grieving|stuck)\b",q)) and bool(re.search(r"\b(?:lost|loss|grieving|changing|stuck|what's happening|what is happening|understand|help|explore)\b",q))}

def _build_risk_answer(user_query=""):
    q=str(user_query or "").casefold()
    if re.search(r"\b(?:suicid\w*|self-harm|self harm|kill(?:ing)? myself|kill(?:ing)? yourself|want(?:ing)? to die|don't want to (?:live|be here)|do not want to (?:live|be here)|end my life|take my own life|harm myself|hurt myself|better off dead|wish I were dead)\b",q): return "If you are thinking about killing yourself or may act on thoughts of self-harm, please treat this as something that needs human help now. Call emergency services or go to the nearest emergency department, and if you can, stay with another person while you get help. You do not need to work out the larger meaning of what you are going through before taking that next step."
    if re.search(r"\b(?:abuse|coercion|threatened|unsafe)\b",q): return "If someone is threatening, abusing, or coercing you, or you are not safe where you are, prioritize getting to a safer place and contacting a trusted person or local emergency service now. You do not need to settle the larger meaning of the situation before taking a step toward safety."
    return "If you may be in immediate danger or cannot keep yourself safe, please seek human help now. Call emergency services or go to the nearest emergency department, and if you can, stay with another person while you get help."

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

def _normalize_title(text): return re.sub(r"^[\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F\u200D]+\s*","",str(text or "").strip()).strip()

def _role_evidence(doc):
    text=re.sub(r"\s+"," ",str(doc.get("text") or "").strip().casefold()); title=_normalize_title(doc.get("title") or "").casefold(); corpus=title+" "+text
    return {"grounded":bool(re.search(r"\b(?:science|scientific|research|psychological|clinical|neuroscientific|evidence|empirical)\b",corpus)),"meaning":bool(re.search(r"\b(?:meaning|purpose|wisdom|perspective|understanding|sense-making|make sense|interpretation)\b",corpus)),"worldview":bool(re.search(r"\b(?:spiritual|spirituality|religious|religion|mystical|mysticism|afterlife|reincarnation|soul|sacred|transcenden|starseed|higher-order intelligence|metaphysics|cosmic curriculum|universe|cosmic)\b",corpus)),"acute_risk":bool(re.search(r"\b(?:suicid(?:e|al|ality)|suicidal ideation|self-harm|overdose|acute crisis|crisis intervention|immediate danger)\b",corpus)),"title_risk":bool(re.search(r"\b(?:suicide|suicidal|self-harm|overdose|crisis intervention|acute crisis)\b",title))}

def _is_risk_related(doc):
    e=_role_evidence(doc); return e["acute_risk"] or e["title_risk"]

def _valid_doc_url(doc):
    url=str(doc.get("url") or doc.get("canonical_url") or "").strip(); return url if re.match(r"^https://\S+$",url,re.I) else ""

def _query_subject(query):
    q=re.sub(r"\s+"," ",str(query or "").strip()); q=re.sub(r"^(?:what is|what's|define|explain|what does)\s+","",q,flags=re.I); return q.rstrip(" ?.!:")

def _clean_evidence_text(text):
    value=re.sub(r"<[^>]+>"," ",str(text or "")); value=re.sub(r"(?:https?://|www\.)\S+"," ",value)
    value=re.sub(r"\b(?:on x|x post|x posts|twitter|hypothetical quantum thread|collective awakening|as an ai|users exploring)\b[^.]*[.]?"," ",value,flags=re.I)
    value=re.sub(r"\b(?:follow me|subscribe|share|like|comment|join the conversation)\b[^.]*[.]?"," ",value,flags=re.I)
    return re.sub(r"\s+"," ",value).strip()

def _definition_strength(query,sentence,title):
    subject=_query_subject(query).casefold(); low=sentence.casefold(); score=0
    if subject and re.search(rf"\b{re.escape(subject)}\b",title.casefold()): score+=30
    if subject and re.search(rf"\b{re.escape(subject)}\b",low): score+=35
    if re.search(r"\b(?:is|are|means|refers to|describes|defines|understood as|can be understood as|represents)\b",low): score+=25
    if re.search(r"\b(?:framework|concept|practice|idea|approach|pathway|collection|body of work|relates to|concerns|explores)\b",low): score+=12
    if re.search(r"\b(?:spiritual|cosmic|awakening|metaphysical|universal|interconnected reality|co-creator|transcenden)\b",low) and not re.search(r"\b(?:perspective|interpretation|worldview|framing|in the archive|the essay)\b",low): score-=18
    return score

def _select_factual_primary(query,docs):
    subject=_query_subject(query).casefold(); ranked=[]
    for index,doc in enumerate(docs):
        title=_normalize_title(doc.get("title") or ""); url=_valid_doc_url(doc)
        if not title or not url or _is_risk_related(doc): continue
        raw=_clean_evidence_text(doc.get("text") or ""); low=raw.casefold(); title_hit=int(bool(subject and re.search(rf"\b{re.escape(subject)}\b",title.casefold()))); exact_text=int(bool(subject and re.search(rf"\b{re.escape(subject)}\b",low))); definition_hits=sum(1 for s in re.split(r"(?<=[.!?])\s+",raw) if _definition_strength(query,s,title)>=40); e=_role_evidence(doc)
        score=100*title_hit+55*exact_text+30*min(definition_hits,3)+6*int(e["grounded"] or e["meaning"])
        if e["worldview"] and not title_hit: score-=18
        if score>0: ranked.append((score,index,doc))
    ranked.sort(key=lambda x:(-x[0],x[1])); return ranked[0][2] if ranked else None

def _definition_candidates(query,primary):
    raw=_clean_evidence_text(primary.get("text") or ""); title=_normalize_title(primary.get("title") or ""); sentences=[s.strip() for s in re.split(r"(?<=[.!?])\s+",raw) if s.strip()]; definition=[]; supporting=[]
    for idx,sentence in enumerate(sentences):
        score=_definition_strength(query,sentence,title)
        if score>=45: definition.append((score,idx,sentence))
        elif score>=15: supporting.append((score,idx,sentence))
    definition.sort(key=lambda x:(-x[0],x[1])); supporting.sort(key=lambda x:(-x[0],x[1])); return definition[:3],supporting[:4]

def _concept_synthesis(query,primary):
    subject=_query_subject(query); definition,supporting=_definition_candidates(query,primary); usable=[]
    for item in definition+supporting:
        low=item[2].casefold()
        if re.search(r"\b(?:collective awakening|profound truth|we'?re all co-creators|universal knowledge|quantum thread|hypothetical|we are all co-creators)\b",low): continue
        usable.append(item[2])
    if not usable: return ""
    exact=[s for s in usable if subject and re.search(rf"\b{re.escape(subject)}\b",s,re.I)]; chosen=(exact[:2] or usable[:2])
    if definition:
        if len(chosen)==1 and supporting: chosen.append(supporting[0][2])
        return " ".join(chosen).strip()
    if len(chosen)>=2: return f"Taken together, the retrieved material presents {subject} as " + re.sub(r"^[Tt]his collection explores|^[Tt]hese writings consider","a concept explored through"," ".join(chosen),count=1)
    return chosen[0]

def _factual_open(query,profile):
    q=str(query or "").strip().casefold(); return bool(q) and not any(profile.get(k) for k in ("risk","foundation_open","coercion_open","ambiguous_loss_open","grief","transition_open","emptiness_open","meaning_open","loneliness","fear_open","anger_open")) and bool(re.match(r"^(?:what is|what's|who is|who was|when did|where is|where was|why is|why does|how does|what does|what are|define|explain)\b",q))

def _build_factual_answer(query,primary,docs):
    title=_normalize_title(primary.get("title") or ""); url=_valid_doc_url(primary); subject=_query_subject(query)
    if not title or not url or not subject: return ""
    synthesis=_concept_synthesis(query,primary)
    if synthesis:
        parts=[f"The closest supported material I found is [{title}]({url}).",synthesis]; e=_role_evidence(primary)
        if e["worldview"]: parts.append("The Archive also moves into spiritual, cosmological, or metaphysical interpretation here; those elements are presented as an interpretive perspective rather than established fact.")
        return "\n\n".join(parts)
    return f"The Archive has material related to {subject} in [{title}]({url}), but the retrieved evidence does not establish a clear definition. It is better to leave that boundary explicit than infer one from adjacent material."

def _build_foundation_answer(query,primary=None,docs=None):
    if primary and _valid_doc_url(primary):
        title=_normalize_title(primary.get("title") or ""); url=_valid_doc_url(primary); return "\n\n".join(["The Living Archive is a connected body of essays, perspectives, frameworks, and pathways for making sense of complex human questions without reducing them to a single answer.",f"A useful place to begin is [{title}]({url}). It offers a way into the Archive while preserving the distinction between what is established, what is interpretive, and what may hold personal meaning.","Begin with the question that brought you here and follow the route that feels most relevant."])
    return "The Living Archive is a connected body of essays, perspectives, frameworks, and pathways for making sense of complex human questions without reducing them to a single answer."

def _persistent_visitor_construction(query,docs,profile,canonical_link_context=""):
    if profile.get("risk"): return _build_risk_answer(query)
    if profile.get("foundation_open"):
        foundation_docs=_parse_context_documents(canonical_link_context) or docs; primary=foundation_docs[0] if foundation_docs else None; answer=_build_foundation_answer(query,primary,foundation_docs)
        if answer: return answer
    if _factual_open(query,profile):
        primary=_select_factual_primary(query,docs)
        if primary:
            answer=_build_factual_answer(query,primary,docs)
            if answer: return answer
    return None

def _sanitize_visitor_output(text): return re.sub(r"\bUSE\b","The Guide",str(text or ""))

def _v464_generate_boundary(*args,**kwargs):
    user_query=_extract_user_query(args,kwargs); raw_context=_context_blocks_from_kwargs(args,kwargs); docs=_parse_context_documents(raw_context); canonical_link_context=str(kwargs.get("canonical_link_context") or "")
    if not canonical_link_context and len(args)>=4 and isinstance(args[3],str): canonical_link_context=args[3]
    profile=_query_profile(user_query); persistent=_persistent_visitor_construction(user_query,docs,profile,canonical_link_context)
    if persistent: return _sanitize_visitor_output(persistent)
    return _sanitize_visitor_output(_original_generate_llm_response(*args,**kwargs))

def _v464_evidence_gap_boundary(user_query,canonical_link_context=""):
    docs=_parse_context_documents(canonical_link_context); profile=_query_profile(user_query); persistent=_persistent_visitor_construction(user_query,docs,profile,canonical_link_context)
    if persistent: return _sanitize_visitor_output(persistent)
    return _sanitize_visitor_output(_original_evidence_sufficiency_unavailable_response(user_query,canonical_link_context))

_V464_BOUNDARY_QUERY="What is the Living Archive?"; _V464_BOUNDARY_AUDIT=_v464_evidence_gap_boundary(_V464_BOUNDARY_QUERY,"")
if "living archive" not in _V464_BOUNDARY_AUDIT.casefold() or "USE" in _V464_BOUNDARY_AUDIT: raise RuntimeError("USE v464 visitor boundary audit failed.")
app=use_core.app; app.title=f"Find Your Way (The Guide) {APP_VERSION}"
print(f"The Guide v464 BUILD IDENTITY: build_id={CANONICAL_BUILD_ID}, version={APP_VERSION}, fingerprint={DEPLOYMENT_FINGERPRINT}, source_sha256={RUNTIME_SOURCE_SHA256}, core_blob_sha256={_core_runtime_sha}")
use_core.APP_VERSION=APP_VERSION; use_core.DEPLOYMENT_FINGERPRINT=DEPLOYMENT_FINGERPRINT; use_core.CANONICAL_BUILD_ID=CANONICAL_BUILD_ID; use_core.RUNTIME_SOURCE_SHA256=RUNTIME_SOURCE_SHA256; use_core.EXPECTED_CORE_BLOB_SHA=EXPECTED_CORE_BLOB_SHA
use_core.generate_llm_response=_v464_generate_boundary; use_core._evidence_sufficiency_unavailable_response=_v464_evidence_gap_boundary