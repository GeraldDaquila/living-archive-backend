# USE PRODUCTION VERSION: v487 — constitutional calibration layer
import hashlib
import importlib
import re
from pathlib import Path

APP_VERSION="v487"
DEPLOYMENT_FINGERPRINT="USE-v487-constitutional-calibration"
CANONICAL_BUILD_ID="USE-BUILD-v487-constitutional-calibration"
EXPECTED_CORE_BLOB_SHA="fb3208a8d287f16562ffd640d89f65d5e8d18607"
_MAIN_PATH=Path(__file__).resolve(); _CORE_PATH=_MAIN_PATH.with_name("use_core.py")
RUNTIME_SOURCE_SHA256=hashlib.sha256(_MAIN_PATH.read_bytes()).hexdigest()
if not _CORE_PATH.exists(): raise RuntimeError("USE v487 package integrity failure: use_core.py is missing.")
_core_bytes=_CORE_PATH.read_bytes(); _core_runtime_sha=hashlib.sha1(f"blob {len(_core_bytes)}\0".encode()+_core_bytes).hexdigest()
if _core_runtime_sha!=EXPECTED_CORE_BLOB_SHA: raise RuntimeError(f"USE v487 package integrity failure: expected protected core blob sha={EXPECTED_CORE_BLOB_SHA}, actual={_core_runtime_sha}")
use_core=importlib.import_module("use_core"); _original_generate_llm_response=use_core.generate_llm_response; _original_handle_query=getattr(use_core,"handle_query",None); _original_evidence_sufficiency_unavailable_response=getattr(use_core,"_evidence_sufficiency_unavailable_response",None)
if _original_handle_query is None: raise RuntimeError("USE v487 package integrity failure: API query handler is unavailable.")
if not callable(_original_evidence_sufficiency_unavailable_response): raise RuntimeError("USE v487 package integrity failure: evidence-gap response boundary is unavailable.")

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
def _has(q,patterns): return bool(re.search(r"(?:^|\b)(?:"+"|".join(patterns)+r")(?:\b|$)",q))
def _weighted_inquiry_profile(query):
    q=re.sub(r"\s+"," ",str(query or "").strip().casefold()); p={"risk":0.0,"recommendation":0.0,"navigation":0.0,"foundation":0.0,"lived":0.0,"conceptual":0.0,"grief":0.0,"specialized":0.0}
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
    if p["grief"]: p["lived"]=max(p["lived"],0.90)
    if p["recommendation"] and p["grief"]: p["recommendation"]=min(1.0,p["recommendation"]+0.10)
    return p
def _weighted_action(profile):
    if profile["risk"]>=0.80: return "risk"
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
    low=query.casefold()
    if re.search(r"\bgrief\b",low) and re.search(r"\b(?:hurt|pain|painful|let go|letting go)\b",low): return "Grief can remain painful even after you understand that something needs to change. Knowing that you need to let go and actually feeling ready to let go are not always the same thing."
    return "What you are describing can make sense as a human tension that does not have to be resolved by explanation alone."
def _experience_foothold(profile):
    if profile.get("grief"): return "A gentle place to begin is to let the feeling be present without treating its persistence as proof that you are failing to move forward."
    return "A gentle place to begin is to make room for what you are actually experiencing before deciding what it ought to mean."
def _human_anchor_score(query,claim):
    q=str(query or "").casefold(); text=claim["text"].casefold(); title=claim["title"].casefold(); qt=set(re.findall(r"[a-z]{4,}",q)); score=18*len(qt & set(re.findall(r"[a-z]{4,}",text)))+10*len(qt & set(re.findall(r"[a-z]{4,}",title)))+min(int(claim.get("score",0)),35)
    for term,weight in (("grief",26),("loss",22),("mourning",22),("bereavement",22),("letting go",22),("relationship",18),("forgiveness",16),("growth",10),("receiving",8),("giving",8),("fear",10),("anger",10),("pain",10)):
        if term in q and term in (text+" "+title): score+=weight
    if claim.get("epistemic")=="interpretive" and "grief" in q and not re.search(r"\b(?:afterlife|reincarnation|spiritual|spirituality|cosmic|mystical|metaphysical|transcendence)\b",q): score-=10
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
def _explicit_specialized(query): return bool(re.search(r"\b(?:afterlife|reincarnation|spiritual|spirituality|cosmic|mystical|metaphysical|transcendence|near-death|nde)\b",str(query or "").casefold()))
def _recommendation_anchor_score(query,claim,profile):
    score=_human_anchor_score(query,claim); low=(claim["title"]+" "+claim["text"]).casefold(); specialized=bool(re.search(r"\b(?:afterlife|reincarnation|hypnosis|near-death|nde|cosmic|mystical|metaphysical)\b",low)); explicit_specialized=_explicit_specialized(query)
    if profile.get("grief"):
        if re.search(r"\b(?:death|grief|grieving|mourning|loss|bereavement|loved one|continuity|meaning in grief)\b",low): score+=35
        if specialized and not explicit_specialized: score-=25
        if re.search(r"\b(?:death, grief|grief.*continuity|meaning in grief|loss.*grief)\b",low): score+=20
    if explicit_specialized and specialized: score+=25
    return score
def _recommendation_rationale(query,primary,profile):
    low=(primary["title"]+" "+primary["text"]).casefold()
    if profile.get("grief"):
        if re.search(r"\bcontinuity\b",low): return "I’m recommending this first because it approaches grief and the human search for continuity directly, making it a more immediate place to reflect on the experience of losing someone you love."
        if re.search(r"\b(?:grief|loss|mourning|bereavement)\b",low): return "I’m recommending this first because it speaks directly to grief and loss, rather than asking you to begin with a more specialized interpretation of what happens after death."
        return "I’m recommending this first because it offers a direct doorway into the human experience at the center of your question."
    return "This is a useful place to begin because it speaks directly to the part of the question you asked about."
def _recommendation_wisdom(query,primary,profile):
    if profile.get("grief"): return "Grief is not only the pain of losing someone; it can also be the slow work of finding a way to carry love, memory, and an altered future without pretending the loss did not matter. There may be no single correct timetable for that work."
    return "A useful way to approach a question like this is to let the first insight open the inquiry rather than treating it as the final word."
def _recommendation_foothold(profile):
    if profile.get("grief"): return "For today, a humane next step can be very small: name what you miss, what hurts, or what you are not ready to accept yet, without requiring yourself to solve it."
    return "A humane next step is to notice which part of the question matters most to you now and stay with that part before moving on."
def _adjacent_anchor_score(query,primary,claim,profile):
    if not claim or claim.get("url")==primary.get("url"): return -10**9
    score=_human_anchor_score(query,claim); low=(claim.get("title","")+" "+claim.get("text","")).casefold(); primary_low=(primary.get("title","")+" "+primary.get("text","")).casefold(); score+=min(int(_human_anchor_score(primary_low,claim)*0.55),45)
    if profile.get("grief"):
        if re.search(r"\b(?:grief|loss|mourning|bereavement|loved one|meaning in grief|healing|heals|loss and meaning)\b",low): score+=38
        if re.search(r"\b(?:death|grief|loss|mourning|bereavement|loved one)\b",low): score+=18
    if re.search(r"\b(?:meaning|continuity|transformation|growth|healing|surrender|acceptance|forgiv)\b",low): score+=10
    if bool(re.search(r"\b(?:afterlife|reincarnation|hypnosis|near-death|nde|cosmic|mystical|metaphysical|ego death|spiritual|spirituality)\b",low)) and not _explicit_specialized(query): score-=18
    return score
def _select_adjacent_anchor(query,primary,claims,profile):
    ranked=[(_adjacent_anchor_score(query,primary,c,profile),c) for c in claims if c.get("url")!=primary.get("url")]; ranked.sort(key=lambda x:x[0],reverse=True); return ranked[0][1] if ranked and ranked[0][0]>18 else None
def _recommendation_answer(query,docs,profile):
    claims=_extract_claims(_candidate_sentences(query,docs))
    if not claims: return ""
    ranked=sorted(claims,key=lambda c:_recommendation_anchor_score(query,c,profile),reverse=True); primary=ranked[0]; adjacent=_select_adjacent_anchor(query,primary,ranked[1:],profile); label="For someone grieving, a good place to begin is" if profile.get("grief") else "A good place to begin is"
    parts=[f"{label} [{primary['title']}]({primary['url']}).",_recommendation_wisdom(query,primary,profile),_recommendation_foothold(profile),_recommendation_rationale(query,primary,profile)]
    parts.append("This doorway is offered as a reflection gateway, not as a complete explanation or prescription. It is one place to begin noticing what this experience means for you.")
    if adjacent: parts.append(f"A nearby path is [{adjacent['title']}]({adjacent['url']}), which opens another aspect of the question without asking you to treat either doorway as the whole answer.")
    if any(c["epistemic"]=="interpretive" for c in claims): parts.append("Some of the Archive's material enters spiritual or cosmological interpretation; those elements remain interpretive possibilities rather than established facts.")
    return "\n\n".join(parts)
def _build_factual_answer(query,docs):
    subject=re.sub(r"^(?:what is|what's|define|explain|what does|who is|who was|where is|where was|why is|why does|how does)\s+","",query.strip(),flags=re.I).rstrip(" ?.!:"); claims=_extract_claims(_candidate_sentences(query,docs))
    if not claims or not subject: return ""
    groups=_related_claims(claims); primary=claims[0]; parts=[f"The closest supported material I found is [{primary['title']}]({primary['url']}).",_plain_language_concept(subject,claims)]; support=[]
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
    action=profile["action"]
    if action=="risk": return _build_risk_answer(query),"risk"
    if action in {"recommendation","navigation"}:
        answer=_recommendation_answer(query,docs,profile)
        if answer: return answer,"recommendation"
    if action=="lived_experience" or (action=="core" and profile.get("lived")):
        answer=_build_lived_experience_answer(query,docs,profile)
        if answer: return answer,"lived_experience"
    if action=="foundation": return _build_foundation_answer(),"foundation"
    if action=="conceptual":
        answer=_build_factual_answer(query,docs)
        if answer: return answer,"conceptual"
    return "","core"
def _boundary_context(args,kwargs):
    query=_extract_user_query(args,kwargs); raw_context=_context_blocks_from_kwargs(args,kwargs); canonical=str(kwargs.get("canonical_link_context") or (args[3] if len(args)>=4 and isinstance(args[3],str) else "")); return query,_parse_context_documents(raw_context),_parse_context_documents(canonical)
def _v487_generate_boundary(*args,**kwargs):
    query,retrieved_docs,canonical_docs=_boundary_context(args,kwargs); answer,mode=_unified_visitor_construction(query,retrieved_docs,canonical_docs); print(f"The Guide v487 visitor boundary: mode={mode}, retrieved={len(retrieved_docs)}, canonical={len(canonical_docs)}"); return _sanitize_visitor_output(answer if answer else _original_generate_llm_response(*args,**kwargs)
def _v487_evidence_gap_boundary(user_query,canonical_link_context="",retrieved_context_blocks=""):
    canonical_docs=_parse_context_documents(canonical_link_context); retrieved_docs=_parse_context_documents(retrieved_context_blocks); answer,mode=_unified_visitor_construction(user_query,retrieved_docs,canonical_docs); print(f"The Guide v487 evidence-gap boundary: mode={mode}, retrieved={len(retrieved_docs)}, canonical={len(canonical_docs)}"); return _sanitize_visitor_output(answer if answer else _original_evidence_sufficiency_unavailable_response(user_query,canonical_link_context))
def _calibration_contract_audit(answer,mode,risk=False):
    text=str(answer or ""); low=text.casefold(); checks={
        "human_reality": bool(re.search(r"\b(?:grief|grieving|loss|mourning|bereavement|love|experience|what you are describing|what you are experiencing)\b",low)),
        "humane_foothold": bool(re.search(r"\b(?:for today|next step|gentle|name what|notice|stay with|place to begin|without requiring yourself to solve it)\b",low)),
        "epistemic_boundary": bool(re.search(r"\b(?:interpretive|possibilit(?:y|ies)|established fact|established knowledge|personal meaning|reflection gateway|not a complete explanation|not the whole answer|rather than established facts?)\b",low)),
        "risk_routing": ("emergency" in low) if risk else True,
        "outward_gateway": bool(re.search(r"\[[^\]]+\]\(https://geralddaquila\.com/[^)]+\)",text)) and bool(re.search(r"\b(?:nearby path|second doorway|reflection gateway|another aspect|another doorway)\b",low)),
        "teacherly_sovereignty_voice": bool(re.search(r"\b(?:wisdom|slow work|no single correct timetable|you can|for today|stay with|without requiring yourself to solve it|what this experience means for you|rather than treating it as the final word)\b",low)),
    }; return checks
_V487_FOUNDATION_AUDIT=_build_foundation_answer()
_V487_OVERFLOW_AUDIT=_build_factual_answer("What is Overflow?",[{"title":"Codex of the Overflow Pathway","url":"https://geralddaquila.com/overflow-2/","text":"Overflow relates to meaning, transcendence, creation, and stewardship."}])
_V487_GRIEF_AUDIT=_build_lived_experience_answer("Why does grief still hurt even when I know I need to let go?",[{"title":"When You Don’t Know What Is Yours to Carry","url":"https://geralddaquila.com/when-you-dont-know-what-is-yours-to-carry/","text":"There are burdens we put down because carrying them is preventing someone else from carrying their own."},{"title":"Learning to Say No Without Feeling Like a Bad Person","url":"https://geralddaquila.com/2026/02/02/learning-to-say-no-without-feeling-like-a-bad-person/","text":"Giving and Receiving Are One System. Your mind might say: ‘I’m letting them down.’"}],_inquiry_profile("Why does grief still hurt even when I know I need to let go?"))
_V487_RECOMMEND_AUDIT=_recommendation_answer("What essay from the Living Archive would you recommend for someone grieving from the death of a loved one?",[{"title":"Death, Grief, and the Human Search for Continuity","url":"https://geralddaquila.com/2025/05/24/embracing-the-cosmic-journey-finding-peace-after-losing-a-loved-one/","text":"The writing addresses death, grief, and the human search for continuity after losing a loved one."},{"title":"The Transformative Power of Loss: Finding Meaning in Grief Through Spiritual and Scientific Wisdom","url":"https://geralddaquila.com/2025/05/29/transformative-power-of-loss-finding-meaning-in-grief-through-spiritual-and-scientific-wisdom/","text":"The writing approaches grief, loss, meaning, healing, and wisdom."},{"title":"The Surrender Process: Ego Death as a Catalyst for Transformation","url":"https://geralddaquila.com/2025/06/22/the-surrender-process-ego-death-as-a-catalyst-for-transformation/","text":"The writing approaches surrender, ego death, and transformation."}],_inquiry_profile("What essay from the Living Archive would you recommend for someone grieving from the death of a loved one?"))
_V487_RISK_AUDIT=_unified_visitor_construction("I want to kill myself",[],[])[0]
_V487_CONTRACT_AUDIT=_calibration_contract_audit(_V487_RECOMMEND_AUDIT,"recommendation")
_V487_RISK_CONTRACT_AUDIT=_calibration_contract_audit(_V487_RISK_AUDIT,"risk",risk=True)
if "living archive" not in _V487_FOUNDATION_AUDIT.casefold(): raise RuntimeError("USE v487 invariant audit failed: foundation.")
if "Overflow" not in _V487_OVERFLOW_AUDIT: raise RuntimeError("USE v487 invariant audit failed: conceptual.")
if "Grief" not in _V487_GRIEF_AUDIT: raise RuntimeError("USE v487 invariant audit failed: human reality.")
if "Death, Grief, and the Human Search for Continuity" not in _V487_RECOMMEND_AUDIT: raise RuntimeError("USE v487 invariant audit failed: anchor doorway.")
if "The Transformative Power of Loss" not in _V487_RECOMMEND_AUDIT: raise RuntimeError("USE v487 invariant audit failed: adjacent doorway.")
if "I’m recommending this first because" not in _V487_RECOMMEND_AUDIT: raise RuntimeError("USE v487 invariant audit failed: doorway rationale.")
if not all(_V487_CONTRACT_AUDIT.values()): raise RuntimeError(f"USE v487 constitutional calibration contract failed: {_V487_CONTRACT_AUDIT}")
if "emergency" not in _V487_RISK_AUDIT.casefold(): raise RuntimeError("USE v487 invariant audit failed: risk routing.")
if not all(_V487_RISK_CONTRACT_AUDIT.values()): raise RuntimeError(f"USE v487 risk calibration contract failed: {_V487_RISK_CONTRACT_AUDIT}")
app=use_core.app; app.title=f"Find Your Way (The Guide) {APP_VERSION}"; print(f"The Guide v487 BUILD IDENTITY: build_id={CANONICAL_BUILD_ID}, version={APP_VERSION}, fingerprint={DEPLOYMENT_FINGERPRINT}, source_sha256={RUNTIME_SOURCE_SHA256}, core_blob_sha={_core_runtime_sha}"); use_core.APP_VERSION=APP_VERSION; use_core.DEPLOYMENT_FINGERPRINT=DEPLOYMENT_FINGERPRINT; use_core.CANONICAL_BUILD_ID=CANONICAL_BUILD_ID; use_core.RUNTIME_SOURCE_SHA256=RUNTIME_SOURCE_SHA256; use_core.EXPECTED_CORE_BLOB_SHA=EXPECTED_CORE_BLOB_SHA; use_core.generate_llm_response=_v487_generate_boundary; use_core._evidence_sufficiency_unavailable_response=_v487_evidence_gap_boundary