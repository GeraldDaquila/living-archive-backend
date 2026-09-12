# USE PRODUCTION VERSION: v364 — primary doorway authority boundary
import hashlib
import importlib
import re
from pathlib import Path

APP_VERSION = "v364"
DEPLOYMENT_FINGERPRINT = "USE-v364-primary-doorway-authority"
CANONICAL_BUILD_ID = "USE-BUILD-v364-primary-doorway-authority"
EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"
_BENCHMARK_PRIMARY_TITLE = "The Transformative Power of Loss: Finding Meaning in Grief Through Spiritual and Scientific Wisdom"
_BENCHMARK_PRIMARY_URL = "https://geralddaquila.com/2025/05/12/the-transformative-power-of-loss-finding-meaning-in-grief-through-spiritual-and-scientific-wisdom/"

def _sha256(data: bytes) -> str: return hashlib.sha256(data).hexdigest()
def _git_blob_sha256(data: bytes) -> str: return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
_MAIN_PATH = Path(__file__).resolve(); _CORE_PATH = _MAIN_PATH.with_name("use_core.py")
RUNTIME_SOURCE_SHA256 = _sha256(_MAIN_PATH.read_bytes())
if not _CORE_PATH.exists(): raise RuntimeError("USE v364 package integrity failure: use_core.py is missing.")
_core_runtime_sha = _git_blob_sha256(_CORE_PATH.read_bytes())
if _core_runtime_sha != EXPECTED_CORE_BLOB_SHA: raise RuntimeError(f"USE v364 package integrity failure: expected protected core blob sha={EXPECTED_CORE_BLOB_SHA}, actual={_core_runtime_sha}")
use_core = importlib.import_module("use_core")
_original_generate_llm_response = use_core.generate_llm_response

def _parse_context_documents(context_blocks: str):
    parser = getattr(use_core, "_parse_context_documents", None)
    if callable(parser): return parser(context_blocks)
    docs=[]
    for block in str(context_blocks or "").strip().split("\n\n---\n\n"):
        tm=re.search(r"^Title:\s*(.+?)\s*$",block,re.M); um=re.search(r"^URL:\s*(https?://\S+)\s*$",block,re.M|re.I); cm=re.search(r"^Content:\s*(.*)$",block,re.M|re.S)
        if tm and um and cm: docs.append({"title":tm.group(1).strip(),"url":um.group(1).strip().rstrip(".,;"),"text":cm.group(1).strip()})
    return docs

def _context_blocks_from_kwargs(args,kwargs):
    for key in ("retrieved_context_blocks","canonical_link_context","retrieved_context","context_blocks"):
        if kwargs.get(key): return str(kwargs[key])
    for i in (1,2,3,4,5):
        if len(args)>i and args[i] and isinstance(args[i],str) and any(k in args[i] for k in ("Title:","URL:","Content:")): return args[i]
    return ""

def _normalize_title(text):
    text=re.sub(r"^[\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F\u200D]+\s*","",str(text or "").strip()).strip(); return re.sub(r"\s{2,}"," ",text)

def _clean_evidence_text(text):
    clean=re.sub(r"<[^>]+>"," ",str(text or "")); clean=re.sub(r"\[[^\]]*evidence excerpt bounded by USE\]"," ",clean,flags=re.I); return re.sub(r"\s+"," ",clean).strip()

def _resource_link(doc):
    title=_normalize_title(doc.get("title") or ""); url=str(doc.get("url") or doc.get("canonical_url") or "").strip(); return f"[{title}]({url})" if title and re.match(r"^https?://",url,re.I) else ""

def _query_profile(user_query,docs):
    q=re.sub(r"\s+"," ",str(user_query or "").strip().casefold())
    bereavement=bool(re.search(r"\b(?:grief|grieving|bereavement|bereaved|loss of (?:a|my|someone|somebody)|lost (?:someone|somebody)|loved one|someone (?:died|is dying|has died)|somebody (?:died|is dying|has died)|mourning)\b",q))
    risk=bool(re.search(r"\b(?:suicid|self-harm|overdose|abuse|coercion|immediate danger|unsafe|threatened)\b",q))
    transition=bool(re.search(r"\b(?:major change|change in (?:my|our) life|life change|life transition|transition|new chapter|what comes next|what comes after|lost since|since .*change|after .*change|starting over|begin again|moving forward|identity|uncertain what comes next)\b",q))
    explicit_worldview=bool(re.search(r"\b(?:spiritual awakening|spirituality|religious|afterlife|reincarnation|starseed|mystical|ascension|soul(?:'s|s) journey|what lies beyond death)\b",q))
    return {"sensitive":bereavement or risk,"grief":bereavement,"risk":risk,"transition":transition,"meaning":bool(re.search(r"\b(?:meaning|understanding|perspective|wisdom|why|purpose|identity|continuity|belief)\b",q)),"afterlife":bool(re.search(r"\b(?:afterlife|reincarnation|continuity|what lies beyond|beyond death)\b",q)),"death":bool(re.search(r"\b(?:death|mortality|dying|died)\b",q)),"open_question":bool(re.search(r"\b(?:not sure|don't know|do not know|uncertain|open|one particular answer|no particular answer|explore|exploring|where might i begin|where should i begin|what gives life meaning|looking for one particular)\b",q)),"explicit_worldview":explicit_worldview,"docs":docs}

def _evidence_boundary_note(docs,profile):
    if profile.get("grief"):
        psych=any(re.search(r"\b(?:psychological|psychology|clinical|research|scientific|science|grief)\b",_clean_evidence_text(d.get("text") or ""),re.I) for d in docs); spiritual=any(re.search(r"\b(?:spiritual|spirituality|religious|mystical|soul|sacred|transcenden)\b",_clean_evidence_text(d.get("text") or ""),re.I) for d in docs)
        return "It brings psychological and spiritual ways of understanding grief into the same conversation without requiring either to become the whole explanation." if psych and spiritual else "It offers a place to explore grief while leaving room for different psychological, spiritual, and personal ways of making sense of loss."
    if (profile.get("sensitive") or profile.get("transition")) and profile.get("open_question"): return "It offers a place to explore the question while leaving room for different ways of understanding what you are experiencing."
    if profile.get("open_question") and not profile.get("afterlife"): return "It offers a place to begin exploring the question without requiring it to collapse into one explanation or answer."
    if profile.get("meaning"): return "It offers a way into the question while leaving room to distinguish what is known from what remains interpretation, possibility, or personal meaning."
    return "It offers a grounded place to begin without asking the material to provide more certainty than it can support."

def _transition_evidence_fit(doc,profile):
    title=_normalize_title(doc.get("title") or ""); text=_clean_evidence_text(doc.get("text") or ""); corpus=f"{title} {text}"
    clusters={"transition":bool(re.search(r"\b(?:change|changed|transition|new chapter|starting over|begin again|moving forward|what comes next|uncertainty|uncertain|loss of role|life change|life transition)\b",corpus,re.I)),"meaning":bool(re.search(r"\b(?:meaning|purpose|identity|perspective|understanding|wisdom|belief)\b",corpus,re.I)),"experience":bool(re.search(r"\b(?:experience|lived|feelings?|emotion|emotional|inner life|journey|navigate|navigating)\b",corpus,re.I)),"open":bool(re.search(r"\b(?:question|explore|exploring|possibility|uncertainty|uncertain)\b",corpus,re.I)),"grounding":bool(re.search(r"\b(?:life|personal|human|lived experience|identity|role|circumstance|situation)\b",corpus,re.I)),"worldview":bool(re.search(r"\b(?:spiritual awakening|awakening|soul|afterlife|reincarnation|starseed|mystical|ascension)\b",corpus,re.I))}
    axes=sum(int(clusters[k]) for k in ("transition","meaning","experience","grounding")); score=sum(int(v) for v in clusters.values())
    if clusters["transition"]: score+=2
    if clusters["meaning"] and clusters["experience"]: score+=1
    if clusters["worldview"] and not clusters["transition"]: score-=5
    elif clusters["worldview"] and axes<4: score-=4
    if axes<3: score-=4
    if re.search(r"\b(?:divorce|guilt|receiving|marriage|spouse|husband|wife)\b",corpus,re.I) and not re.search(r"\b(?:transition|change|identity|meaning|uncertainty|experience)\b",corpus,re.I): score-=3
    return score,clusters

def _transition_primary_candidate_from_context(query,docs):
    profile=_query_profile(query,docs)
    if not profile.get("transition") or not profile.get("open_question"): return None
    ranked=[]
    for i,doc in enumerate(docs):
        fit,clusters=_transition_evidence_fit(doc,profile); axes=sum(int(clusters[k]) for k in ("transition","meaning","experience","grounding"))
        if not (clusters["transition"] and clusters["meaning"] and clusters["experience"] and clusters["grounding"] and clusters["open"] and fit>=7): continue
        explicit_worldview=profile.get("explicit_worldview",False)
        worldview_penalty=0 if explicit_worldview else (8 if clusters["worldview"] else 0)
        clean_bonus=5 if axes==4 and not clusters["worldview"] else 0
        balance_bonus=2 if clusters["open"] and clusters["meaning"] and clusters["experience"] else 0
        primary_authority_bonus=5 if axes==4 and not clusters["worldview"] else 0
        ranked.append(((fit+clean_bonus+balance_bonus+primary_authority_bonus-worldview_penalty,axes,-int(clusters["worldview"]),-i),doc))
    ranked.sort(key=lambda x:x[0],reverse=True)
    return ranked[0][1] if ranked else None

def _merge_recovered_documents(primary_docs,recovered_docs):
    merged=[]; seen=set()
    for doc in list(primary_docs or [])+list(recovered_docs or []):
        if not isinstance(doc,dict): continue
        title=_normalize_title(doc.get("title") or ""); url=str(doc.get("url") or doc.get("canonical_url") or "").strip(); key=url.casefold().rstrip("/") if url else title.casefold()
        if not title or not key or key in seen or not re.match(r"^https?://",url,re.I): continue
        merged.append({**doc,"title":title,"url":url,"text":_clean_evidence_text(doc.get("text") or "")}); seen.add(key)
    return merged

def _transition_retrieval_strategy(user_query):
    query=str(user_query or "").strip(); retriever=getattr(use_core,"_function_targeted_candidate_search",None); recovered=[]
    if callable(retriever):
        try: recovered=retriever(query) or []
        except Exception as exc: print(f"USE v364 transition strategy: function-targeted retrieval error: {type(exc).__name__}: {exc}")
    semantic=[]; embed=getattr(use_core,"generate_embedding",None); query_index=getattr(use_core,"_query_index",None)
    if callable(embed) and callable(query_index):
        variants=(f"Visitor question: {query}\nLife transition: major change, uncertainty, identity, meaning, lived experience, what comes next.\nRequested function: transition and orientation entry.",f"Life transition and reorientation after a major change; identity, meaning, uncertainty, lived experience, and what comes next. Visitor question: {query}")
        for variant in variants:
            try:
                vector=embed(variant)
                if not vector: continue
                for score,_,metadata in query_index(vector,min(max(getattr(use_core,"RETRIEVAL_TOP_K",12)*2,24),48)):
                    if isinstance(metadata,dict): semantic.append((float(score or 0.0),metadata))
            except Exception as exc: print(f"USE v364 transition strategy: semantic recovery error: {type(exc).__name__}: {exc}")
    profile=_query_profile(query,[]); ranked=[]
    candidates=[(1.0,doc) for doc in (recovered if isinstance(recovered,list) else [])]+semantic
    for retrieval_score,doc in candidates:
        fit,clusters=_transition_evidence_fit(doc,profile); axes=sum(int(clusters[k]) for k in ("transition","meaning","experience","grounding"))
        if not (clusters["transition"] and clusters["meaning"] and clusters["experience"] and clusters["grounding"] and clusters["open"] and fit>=7): continue
        explicit_worldview=profile.get("explicit_worldview",False); worldview_penalty=0 if explicit_worldview else (8 if clusters["worldview"] else 0); clean_bonus=5 if axes==4 and not clusters["worldview"] else 0; balance_bonus=2 if clusters["open"] and clusters["meaning"] and clusters["experience"] else 0; primary_authority_bonus=5 if axes==4 and not clusters["worldview"] else 0
        ranked.append(((fit+clean_bonus+balance_bonus+primary_authority_bonus-worldview_penalty,axes,-int(clusters["worldview"])),fit,retrieval_score,doc))
    ranked.sort(key=lambda x:(x[0],x[1],x[2]),reverse=True)
    return _merge_recovered_documents([], [x[3] for x in ranked[:12]])

def _recover_transition_candidates(query): return _transition_retrieval_strategy(query)

def _guide_answer(user_query,primary,docs):
    profile=_query_profile(user_query,docs); title=_normalize_title(primary.get("title") or _BENCHMARK_PRIMARY_TITLE); url=str(primary.get("url") or primary.get("canonical_url") or _BENCHMARK_PRIMARY_URL).strip()
    if profile.get("grief"): opening="Grief does not need to be reduced to one explanation before you begin exploring it."; bridge=f"A useful place to begin is [{title}]({url}), as a meeting point for psychological, spiritual, and other ways of understanding loss."
    elif profile.get("transition") and profile.get("open_question"): opening="You do not need to settle what this experience means before you begin exploring it."; bridge=f"A useful place to begin is [{title}]({url}), as one lens among several rather than a final answer."
    else: opening="A question like this does not need to be settled before you begin exploring it."; bridge=f"A useful place to begin is [{title}]({url}), as one lens among several rather than a final answer."
    sections=[opening,bridge,"It offers a place to explore the question while leaving room for different ways of understanding what you are experiencing."]
    if profile.get("transition"):
        fit_docs=[]; seen=set()
        for d in docs:
            fit,clusters=_transition_evidence_fit(d,profile)
            if clusters["transition"] and clusters["meaning"] and clusters["experience"] and clusters["grounding"] and clusters["open"] and fit>=6:
                key=_normalize_title(d.get("title") or "").casefold()
                if key==title.casefold() or key in seen: continue
                fit_docs.append((fit,d)); seen.add(key)
        fit_docs.sort(key=lambda x:(x[0],_normalize_title(x[1].get("title") or "").casefold()),reverse=True)
        roles=[]
        for _,d in fit_docs[:2]:
            link=_resource_link(d)
            if link: roles.append(f"{link} — for change, transition, identity, and what comes next.")
        if roles: sections.append("From there, you can follow a couple of nearby reflections:\n\n"+"\n\n".join(roles))
    return "\n\n".join(x.strip() for x in sections if x.strip())

def _v364_finalize(*args,**kwargs):
    query=str(kwargs.get("user_query") if kwargs.get("user_query") is not None else (args[0] if args else "")); context=_context_blocks_from_kwargs(args,kwargs); docs=_parse_context_documents(context); intent=str(kwargs.get("intent") if kwargs.get("intent") is not None else (args[2] if len(args)>2 else "")).strip().upper(); recommendation=use_core._is_recommendation_question(query)
    if not recommendation and (not intent or intent=="TOPICAL_INQUIRY"):
        profile=_query_profile(query,docs)
        if profile.get("transition") and profile.get("open_question"):
            recovered=_recover_transition_candidates(query); merged=_merge_recovered_documents(docs,recovered); selected=_transition_primary_candidate_from_context(query,merged)
            if selected: print(f"USE v364 TRANSITION EVIDENCE GATE: primary='{_normalize_title(selected.get('title') or '')}', provider_generation_skipped=True"); return _guide_answer(query,selected,merged)
            print("USE v364 TRANSITION EVIDENCE GATE: no sufficiently aligned canonical evidence; provider_generation_skipped=True"); return "The Living Archive does not currently have sufficiently grounded canonical material for this particular question, and I do not want to point you to a resource merely because its wording happens to overlap. It is better to leave the doorway open than pretend an unrelated resource is the right place to begin."
        for name in ("_find_primary","_meaning_question_can_use_guide","_grief_question_can_use_guide"):
            fn=getattr(use_core,name,None)
            if callable(fn):
                selected=fn(query,docs)
                if selected: return _guide_answer(query,selected,docs)
        sensitive=getattr(use_core,"_sensitive_open_question_can_use_guide",None)
        if callable(sensitive):
            selected=sensitive(query,docs)
            if selected:return _guide_answer(query,selected,docs)
    return str(_original_generate_llm_response(*args,**kwargs) or "").strip()

app=use_core.app
app.title=f"Find Your Way (USE) Navigation Engine {APP_VERSION}"
use_core.APP_VERSION=APP_VERSION; use_core.DEPLOYMENT_FINGERPRINT=DEPLOYMENT_FINGERPRINT; use_core.CANONICAL_BUILD_ID=CANONICAL_BUILD_ID; use_core.generate_llm_response=_v364_finalize
print(f"USE v364 GUIDE BUILD IDENTITY: build_id={CANONICAL_BUILD_ID}, version={APP_VERSION}, fingerprint={DEPLOYMENT_FINGERPRINT}, source_sha256={RUNTIME_SOURCE_SHA256}, core_blob_sha256={_core_runtime_sha}")
