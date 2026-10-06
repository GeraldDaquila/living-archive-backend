# USE ACTIVE GUIDE RUNTIME PRIMITIVES: v488.47
# Pure visitor-construction helpers extracted from the historical compatibility
# wrapper. No monkey-patching, version authority, or request-boundary wrappers.

import hashlib
import importlib
import re
from pathlib import Path

EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"
_MAIN_PATH = Path(__file__).resolve()
_CORE_PATH = _MAIN_PATH.with_name("use_core.py")
if not _CORE_PATH.exists():
    raise RuntimeError("USE Guide runtime integrity failure: use_core.py is missing.")
_core_bytes = _CORE_PATH.read_bytes()
_core_runtime_sha = hashlib.sha1(f"blob {len(_core_bytes)}\0".encode() + _core_bytes).hexdigest()
if _core_runtime_sha != EXPECTED_CORE_BLOB_SHA:
    raise RuntimeError("USE Guide runtime integrity failure: protected core mismatch.")

use_core = importlib.import_module("use_core")
app = use_core.app

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
    if _has(q,[r"recommend\w*",r"advise",r"advice",r"essay\w*",r"article\w*",r"read(?:ing)?",r"what should i read",r"what can i read",r"where can i start",r"where should i start",r"where should i begin",r"where do i begin",r"where do i start",r"what should i begin with",r"what should i start with",r"what would you recommend"]): p["recommendation"]+=0.82
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
    if profile["grief"]>=0.80 and profile["recommendation"]>=0.70: return "recommendation"
    if profile["recommendation"]>=0.70: return "recommendation"
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
            low=sentence.casefold(); score=10*len(terms & set(re.findall(r"[a-z]{4,}",low))); score+=8*len(terms & title_terms)
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
        return {"direct":{"title":"Truth in the Age of AI: Why Discernment Is Becoming a Survival Skill","url":"https://geralddaquila.com/truth-in-the-age-of-ai-why-discernment-is-becoming-a-survival-skill/"},"adjacent":[{"title":"Knowledge Stewardship in the AI Era: From Information to Wisdom","url":"https://geralddaquila.com/knowledge-stewardship-in-the-ai-era-from-information-to-wisdom/"},{"title":"The Meaning Crisis in the Age of Artificial Intelligence","url":"https://geralddaquila.com/the-meaning-crisis-in-the-age-of-artificial-intelligence/"}]}
    if profile.get("grief"):
        return {"direct":{"title":"Death, Grief, and the Human Search for Continuity","url":"https://geralddaquila.com/2025/05/24/embracing-the-cosmic-journey-finding-peace-after-losing-a-loved-one/"},"adjacent":[{"title":"The Transformative Power of Loss: Finding Meaning in Grief Through Spiritual and Scientific Wisdom","url":"https://geralddaquila.com/2025/05/12/the-transformative-power-of-loss-finding-meaning-in-grief-through-spiritual-and-scientific-wisdom/"}]}
    return {"direct":None,"adjacent":[]}
def _canonical_family_primary(profile):
    catalog=_canonical_catalog(profile); return catalog.get("direct") or None
def _canonical_family_claim(profile):
    item=_canonical_family_primary(profile)
    if not item: return None
    return {"text":"","title":item["title"],"url":item["url"],"score":10000.0,"epistemic":"supported","canonical":True}
def _canonical_role(title,text,profile):
    low=f"{title} {text}".casefold()
    if profile.get("ai_truth"):
        if "truth in the age of ai" in low or "discernment is becoming a survival skill" in low: return "ai_truth_direct"
        if "knowledge stewardship" in low or "information to wisdom" in low or "meaning crisis" in low or ("artificial intelligence" in low and "meaning" in low): return "ai_truth_adjacent"
        if "living archive navigator" in low or "network architecture" in low or "regeneration" in low: return "ai_truth_structural"
    if profile.get("grief"):
        if "death, grief" in low or "transformative power of loss" in low or "meaning in grief" in low or ("grief" in low and "continuity" in low): return "grief_direct"
        if "afterlife" in low or "reincarnation" in low or "near-death" in low or "hypnosis" in low: return "grief_specialized"
    return "general"
def _recommendation_anchor_score(query,claim,profile):
    role=_canonical_role(claim["title"],claim["text"],profile); score=float(claim.get("score",0))
    if profile.get("ai_truth"): score += {"ai_truth_direct":80,"ai_truth_adjacent":30,"ai_truth_structural":10}.get(role,0)
    elif profile.get("grief"): score += {"grief_direct":80,"grief_specialized":12}.get(role,0)
    return score

def _recommendation_wisdom(profile):
    if profile.get("grief"): return "Grief can remain painful even after you understand that something needs to change. Knowing that you need to let go and actually feeling ready to let go are not always the same thing."
    if profile.get("ai_truth"): return "In a time when information can be generated faster than it can be understood, discernment becomes less about finding one perfect source and more about learning how to recognize what kind of claim you are encountering."
    return "A good starting point is to name the question you are actually trying to live with, rather than forcing it into a conclusion too quickly."
def _recommendation_foothold(profile):
    if profile.get("grief"): return "For today, a humane next step can be very small: name what you miss, what hurts, or what you are not ready to accept yet, without requiring yourself to solve it."
    if profile.get("ai_truth"): return "For now, a humane next step is to take one claim or answer that you are unsure about and ask: what here is established, what is interpretation, and what would I need to verify before I build a conclusion on it?"
    return "For now, begin with the smallest question that feels honest and workable."
def _recommendation_answer(query,docs,profile):
    if profile.get("ai_truth") or profile.get("grief"):
        catalog=_canonical_catalog(profile); primary=_canonical_family_claim(profile); secondary=next(({"text":"","title":i["title"],"url":i["url"],"score":9000.0,"epistemic":"supported","canonical":True} for i in catalog.get("adjacent",[])),None)
    else:
        claims=_extract_claims(_candidate_sentences(query,docs)); ranked=sorted(claims,key=lambda c:_recommendation_anchor_score(query,c,profile),reverse=True); primary=ranked[0] if ranked else None; secondary=ranked[1] if len(ranked)>1 else None
    if not primary: return ""
    primary_link=f"[{primary['title']}]({primary['url']})"; adjacent_link=f"[{secondary['title']}]({secondary['url']})" if secondary else ""
    if profile.get("grief"):
        return f"For someone grieving, a good place to begin is {primary_link}.\n\nGrief is not only the pain of losing someone; it can also be the slow work of finding a way to carry love, memory, and an altered future without pretending the loss did not matter. There may be no single correct timetable for that work.\n\nFor today, a humane next step can be very small: name what you miss, what hurts, or what you are not ready to accept yet, without requiring yourself to solve it.\n\nI’m recommending this first because it approaches grief and the human search for continuity directly, making it a more immediate place to reflect on the experience of losing someone you love.\n\nThis doorway is offered as a reflection gateway, not as a complete explanation or prescription. It is one place to begin noticing what this experience means for you.\n\nA nearby path is {adjacent_link}, which opens another aspect of the question without asking you to treat either doorway as the whole answer.\n\nSome of the Archive’s material enters spiritual or cosmological interpretation; those elements remain interpretive possibilities rather than established facts."
    if profile.get("ai_truth"):
        return f"{_recommendation_wisdom(profile)}\n\n{_recommendation_foothold(profile)}\n\nThe Archive offers a related lens in {primary_link}, where discernment becomes a practical discipline for deciding what kind of claim you are encountering. This is one way into the question, not a claim that it completely explains your experience.\n\nYou can stay with this lens, follow the connected material, or return with another part of the question that feels more relevant."
    return f"{_recommendation_wisdom(profile)}\n\n{_recommendation_foothold(profile)}\n\nThe Archive offers a related lens in {primary_link}. This is one way into the question, not a claim that it completely explains your experience.\n\nYou can stay with this lens, follow the connected material, or return with another part of the question that feels more relevant."
def _build_lived_experience_answer(query,docs,profile):
    claims=_extract_claims(_candidate_sentences(query,docs))
    if not claims: return "Grief, uncertainty, anger, and fear can be part of ordinary human experience, especially when something meaningful has been lost or changed. You do not have to resolve that experience before you can begin listening to it."
    anchor=claims[0]; return "\n\n".join([_recommendation_wisdom(profile),_recommendation_foothold(profile),f"The Archive offers a related lens in [{anchor['title']}]({anchor['url']}), where the material explores {anchor['text'].rstrip('.')}. This is one way into the question, not a claim that it completely explains your experience.","You can stay with this lens, follow the connected material, or return with another part of the question that feels more relevant."])
def _foundation_teacherly_answer(query):
    low=str(query or "").casefold()
    if re.search(r"\bwhat is the living archive\b|\bwhat's the living archive\b",low):
        return "The Living Archive is a connected body of essays, perspectives, frameworks, and pathways for making sense of complex human questions without reducing them to a single answer. It is less a place to collect conclusions than a way to begin finding your bearings.\n\nYou can enter with a question, follow a pathway that helps you orient to it, and then move outward into the connected essays that deepen or complicate what you are seeing."
    return "The Living Archive is a connected body of essays, perspectives, frameworks, and pathways for making sense of complex human questions without reducing them to a single answer."
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
    if action=="lived": return _build_lived_experience_answer(query,docs,profile),"lived_experience"
    if action=="foundation": return _foundation_teacherly_answer(query),"foundation"
    if action=="conceptual":
        answer=_build_factual_answer(query,docs)
        if answer: return answer,"conceptual"
    return "","core"
def _build_factual_answer(query,docs):
    subject=re.sub(r"^(?:what is|what's|define|explain|what does|who is|who was|where is|where was|why is|why does|how does)\s+","",query.strip(),flags=re.I).rstrip(" ?.!:"); claims=_extract_claims(_candidate_sentences(query,docs))
    if not claims or not subject: return ""
    primary=claims[0]; parts=[f"The closest supported material I found is [{primary['title']}]({primary['url']})."]
    if subject.casefold()=="overflow": parts.append("In the Archive's framing, Overflow is a way of understanding how life, meaning, and stewardship can be cultivated and passed onward rather than treated as something to accumulate or possess.")
    else: parts.append(f"Taken together, the available material approaches {subject} through several related perspectives rather than a single fixed definition.")
    if any(c["epistemic"]=="interpretive" for c in claims): parts.append("Some of the Archive's material enters spiritual or cosmological interpretation; those elements remain interpretive possibilities rather than established facts.")
    parts.append("A useful place to continue is the linked anchor, where you can see which part of the question you want to stay with or explore further.")
    return "\n\n".join(parts)

