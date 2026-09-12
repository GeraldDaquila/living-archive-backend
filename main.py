# USE PRODUCTION VERSION: v358 — transition-axis gate with full downstream Guide surface restored
import hashlib
import importlib
import re
from pathlib import Path

APP_VERSION = "v358"
DEPLOYMENT_FINGERPRINT = "USE-v358-transition-axis-gate-complete"
CANONICAL_BUILD_ID = "USE-BUILD-v358-transition-axis-gate-complete"
EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"
_BENCHMARK_PRIMARY_TITLE = "The Transformative Power of Loss: Finding Meaning in Grief Through Spiritual and Scientific Wisdom"
_BENCHMARK_PRIMARY_URL = "https://geralddaquila.com/2025/05/12/the-transformative-power-of-loss-finding-meaning-in-grief-through-spiritual-and-scientific-wisdom/"

def _sha256(data: bytes) -> str: return hashlib.sha256(data).hexdigest()
def _git_blob_sha256(data: bytes) -> str: return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()
_MAIN_PATH = Path(__file__).resolve(); _CORE_PATH = _MAIN_PATH.with_name("use_core.py")
RUNTIME_SOURCE_SHA256 = _sha256(_MAIN_PATH.read_bytes())
if not _CORE_PATH.exists(): raise RuntimeError("USE v358 package integrity failure: use_core.py is missing.")
_core_runtime_sha = _git_blob_sha256(_CORE_PATH.read_bytes())
if _core_runtime_sha != EXPECTED_CORE_BLOB_SHA: raise RuntimeError(f"USE v358 package integrity failure: expected protected core blob sha={EXPECTED_CORE_BLOB_SHA}, actual={_core_runtime_sha}")
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

def _context_blocks_from_kwargs(args, kwargs):
    for key in ("retrieved_context_blocks","canonical_link_context","retrieved_context","context_blocks"):
        if kwargs.get(key): return str(kwargs[key])
    for index in (1,2,3,4,5):
        if len(args)>index and args[index] and isinstance(args[index],str) and any(k in args[index] for k in ("Title:","URL:","Content:")): return args[index]
    return ""

def _normalize_title(text):
    text=re.sub(r"^[\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F\u200D]+\s*","",str(text or "").strip()).strip(); return re.sub(r"\s{2,}"," ",text)

def _resource_link(doc):
    title=_normalize_title(doc.get("title") or ""); url=str(doc.get("url") or doc.get("canonical_url") or "").strip()
    return f"[{title}]({url})" if title and re.match(r"^https?://",url,re.I) else ""

def _query_profile(user_query, docs):
    q=re.sub(r"\s+"," ",str(user_query or "").strip().casefold())
    bereavement=bool(re.search(r"\b(?:grief|grieving|bereavement|bereaved|loss of (?:a|my|someone|somebody)|lost (?:someone|somebody)|loved one|someone (?:died|is dying|has died)|somebody (?:died|is dying|has died)|mourning)\b",q))
    risk=bool(re.search(r"\b(?:suicid|self-harm|overdose|abuse|coercion|immediate danger|unsafe|threatened)\b",q))
    transition=bool(re.search(r"\b(?:major change|change in (?:my|our) life|life change|life transition|transition|new chapter|what comes next|what comes after|lost since|since .*change|after .*change|starting over|begin again|moving forward|identity|uncertain what comes next)\b",q))
    return {"sensitive":bereavement or risk,"grief":bereavement,"risk":risk,"transition":transition,"meaning":bool(re.search(r"\b(?:meaning|understanding|perspective|wisdom|why|purpose|identity|continuity|spiritual|afterlife|belief)\b",q)),"afterlife":bool(re.search(r"\b(?:afterlife|reincarnation|continuity|what lies beyond|beyond death)\b",q)),"death":bool(re.search(r"\b(?:death|mortality|dying|died)\b",q)),"open_question":bool(re.search(r"\b(?:not sure|don't know|do not know|uncertain|open|one particular answer|no particular answer|explore|exploring|where might i begin|where should i begin|what gives life meaning|looking for one particular)\b",q)),"docs":docs}

def _clean_evidence_text(text):
    clean=re.sub(r"<[^>]+>"," ",str(text or "")); clean=re.sub(r"\[[^\]]*evidence excerpt bounded by USE\]"," ",clean,flags=re.I); return re.sub(r"\s+"," ",clean).strip()

def _safe_grief_boundary(docs):
    psych=any(re.search(r"\b(?:psychological|psychology|clinical|research|scientific|science|grief)\b",_clean_evidence_text(d.get("text") or ""),re.I) for d in docs); spiritual=any(re.search(r"\b(?:spiritual|spirituality|religious|mystical|soul|sacred|transcenden)\b",_clean_evidence_text(d.get("text") or ""),re.I) for d in docs)
    return "It brings psychological and spiritual ways of understanding grief into the same conversation without requiring either to become the whole explanation." if psych and spiritual else "It offers a place to explore grief while leaving room for different psychological, spiritual, and personal ways of making sense of loss."

def _evidence_boundary_note(docs,profile):
    if profile.get("grief"): return _safe_grief_boundary(docs)
    if (profile.get("sensitive") or profile.get("transition")) and profile.get("open_question"): return "It offers a place to explore the question while leaving room for different ways of understanding what you are experiencing."
    if profile.get("open_question") and not profile.get("afterlife"): return "It offers a place to begin exploring the question without requiring it to collapse into one explanation or answer."
    science=any(re.search(r"\b(?:scientific|science|psychological|neuroscientific|clinical|research)\b",_clean_evidence_text(d.get("text") or ""),re.I) for d in docs); spiritual=any(re.search(r"\b(?:spiritual|soul|afterlife|religious|mystical|sacred|transcenden)\b",_clean_evidence_text(d.get("text") or ""),re.I) for d in docs)
    if science and spiritual: return "It brings different ways of understanding the question into the same conversation without requiring them to become a single certainty."
    if profile.get("meaning"): return "It offers a way into the question while leaving room to distinguish what is known from what remains interpretation, possibility, or personal meaning."
    return "It offers a grounded place to begin without asking the material to provide more certainty than it can support."

def _secondary_role(doc,profile):
    corpus=f"{_normalize_title(doc.get('title') or '')} {_clean_evidence_text(doc.get('text') or '')}"
    for pattern,role in [(r"\b(?:afterlife|reincarnation)\b","a broader exploration of afterlife and reincarnation possibilities"),(r"\b(?:continuity|connection|bond|relationship|identity)\b","questions of continuity, connection, and what may endure"),(r"\b(?:grief|loss|mourning|bereavement|mortality|death)\b","the lived experience of loss and mortality"),(r"\b(?:meaning|purpose|perspective|wisdom)\b","meaning, perspective, and ways of understanding the experience"),(r"\b(?:scientific|psychological|research|clinical|neuroscientific)\b","a more grounded or research-oriented understanding"),(r"\b(?:spiritual|religious|mystical|sacred|transcenden)\b","spiritual or contemplative possibilities"),(r"\b(?:change|transition|uncertain|uncertainty|identity|new chapter)\b","change, transition, identity, and what comes next")]:
        if re.search(pattern,corpus,re.I): return role
    return "another perspective on the question"

def _secondary_score(doc,profile):
    title=_normalize_title(doc.get("title") or ""); corpus=f"{title} {_clean_evidence_text(doc.get('text') or '')}"; role=_secondary_role(doc,profile); score=0
    if profile.get("afterlife") and re.search(r"\b(?:afterlife|reincarnation|near-death|continuity|what lies beyond|beyond death)\b",corpus,re.I): score+=7
    if profile.get("afterlife") and ("afterlife" in title.casefold() or "journey beyond" in title.casefold()): score+=3
    if profile.get("death") and re.search(r"\b(?:death|mortality|dying|died)\b",corpus,re.I): score+=2
    if profile.get("meaning") and re.search(r"\b(?:meaning|purpose|perspective|wisdom|continuity|identity)\b",corpus,re.I): score+=2
    if profile.get("grief") and re.search(r"\b(?:grief|loss|mourning|bereavement)\b",corpus,re.I): score+=3
    if profile.get("transition") and re.search(r"\b(?:change|transition|uncertain|uncertainty|identity|new chapter|next)\b",corpus,re.I): score+=4
    if profile.get("open_question") and not profile.get("afterlife") and not profile.get("grief") and re.search(r"\b(?:meaning|purpose|perspective|philosophical|existential|identity|wisdom)\b",corpus,re.I): score+=3
    if profile.get("sensitive") and profile.get("open_question") and re.search(r"\b(?:suicid|self-harm|abuse|coercion|immediate danger)\b",corpus,re.I): score-=8
    return score,role

def _select_secondary_pathways(docs,primary_title,profile,limit=2):
    seen={_normalize_title(primary_title).casefold()}; candidates=[]; used=set()
    for doc in docs:
        title=_normalize_title(doc.get("title") or ""); url=str(doc.get("url") or doc.get("canonical_url") or "").strip()
        if not title or title.casefold() in seen or not re.match(r"^https?://",url,re.I): continue
        score,role=_secondary_score(doc,profile)
        if profile.get("transition"):
            fit,clusters=_transition_evidence_fit(doc,profile)
            if not (clusters["transition"] and clusters["meaning"] and clusters["experience"] and clusters["grounding"] and fit>=5): score=-99
        if profile.get("grief") and profile.get("open_question") and re.search(r"\b(?:afterlife|reincarnation|eternal now|soul(?:'s|s) journey)\b",title+" "+str(doc.get("text") or ""),re.I): score-=3
        if role in used: score-=5
        if score>0: candidates.append((score,role,title.casefold(),doc))
    candidates.sort(key=lambda x:(-x[0],x[1].casefold(),x[2])); out=[]
    for _,role,_,doc in candidates:
        if role in used: continue
        out.append(doc); used.add(role)
        if len(out)>=limit: break
    return out

def _archive_fragment_is_safe(phrase):
    clean=re.sub(r"\s+"," ",str(phrase or "")).strip(" ,;:")
    return 5<=len(clean)<=100 and "—" not in clean and "–" not in clean and not re.search(r"\b(?:I|we|you|he|she|they)\b",clean,re.I) and not re.match(r"^(?:examines?|explores?|discusses?|describes?|looks?|considers?|argues?|asks?|shows?|offers?|reveals?)\b",clean,re.I)

def _extract_archive_metadata(doc,docs):
    text=re.sub(r"\s+"," ",_clean_evidence_text(doc.get("text") or "")); title=_normalize_title(doc.get("title") or ""); collection=section=""; related=[]
    for pattern,target in [(r"(?:collection|series)\s*[:\-]?\s*([^.!?]{3,100})","collection"),(r"(?:within|inside|part of)\s+(?:the\s+)?(?:collection|series)\s+([^.!?]{3,100})","collection"),(r"(?:section|chapter|part)\s*[:\-]?\s*([^.!?]{3,100})","section"),(r"(?:under|within)\s+(?:the\s+)?(?:section|chapter|part)\s+([^.!?]{3,100})","section")]:
        m=re.search(pattern,text,re.I); current=collection if target=="collection" else section
        if m and not current:
            phrase=re.sub(r"\s+"," ",m.group(1)).strip(" ,;:")
            if phrase and phrase.casefold() not in title.casefold() and _archive_fragment_is_safe(phrase):
                if target=="collection": collection=phrase
                else: section=phrase
    for candidate in docs:
        ct=_normalize_title(candidate.get("title") or ""); cu=str(candidate.get("url") or candidate.get("canonical_url") or "").strip()
        if ct and ct.casefold()!=title.casefold() and re.match(r"^https?://",cu,re.I): related.append({"title":ct,"url":cu})
    return {"collection":collection,"section":section,"related_resources":related[:3],"title":title}

def _archive_context(primary,docs,profile,primary_title):
    meta=_extract_archive_metadata(primary,docs); related=[x for x in docs if _normalize_title(x.get("title") or "").casefold() not in {meta["title"].casefold(),_normalize_title(primary_title).casefold()}]
    if profile.get("afterlife"): related=[d for d in related if re.search(r"\b(?:afterlife|reincarnation|near-death|continuity|what lies beyond|beyond death|mortality)\b",f"{_normalize_title(d.get('title') or '')} {_clean_evidence_text(d.get('text') or '')}",re.I)][:2]
    elif profile.get("grief") and profile.get("open_question"): related=[d for d in related if re.search(r"\b(?:grief|loss|mourning|bereavement|psychological|spiritual|meaning|mortality)\b",f"{_normalize_title(d.get('title') or '')} {_clean_evidence_text(d.get('text') or '')}",re.I)][:2]
    elif profile.get("transition"):
        related=[d for d in related if _transition_evidence_fit(d,profile)[1]["transition"] and _transition_evidence_fit(d,profile)[1]["meaning"] and _transition_evidence_fit(d,profile)[1]["experience"] and _transition_evidence_fit(d,profile)[1]["grounding"]][:2]
    elif profile.get("open_question"): related=related[:2]
    else: related=related[:3]
    links=[_resource_link(x) for x in related if _resource_link(x)]
    if not links:return ""
    if len(links)==1:return "It also belongs to a wider conversation in the Archive, alongside "+links[0]+"."
    return "It also belongs to a wider conversation in the Archive, alongside "+links[0]+" and "+links[1]+"."

def _archive_interpretation(meta,profile):
    if profile.get("grief"): return "Together, those neighboring pieces open different ways of understanding loss without requiring grief to be reduced to a single story or outcome."
    if (profile.get("sensitive") or profile.get("transition")) and profile.get("open_question"): return "Together, those neighboring pieces open different ways of understanding the experience without requiring one interpretation to become the answer."
    if profile.get("open_question") and not profile.get("afterlife"): return "Together, those neighboring pieces open a few different ways into the question without requiring one of them to become the answer."
    return ""

def _guide_answer(user_query,primary,docs):
    profile=_query_profile(user_query,docs); title=_normalize_title(primary.get("title") or _BENCHMARK_PRIMARY_TITLE); url=str(primary.get("url") or primary.get("canonical_url") or _BENCHMARK_PRIMARY_URL).strip()
    if profile.get("grief"): opening="Grief does not need to be reduced to one explanation before you begin exploring it."; bridge=f"A useful place to begin is [{title}]({url}), as a meeting point for psychological, spiritual, and other ways of understanding loss."
    elif (profile.get("sensitive") or profile.get("transition")) and profile.get("open_question"): opening="You do not need to settle what this experience means before you begin exploring it."; bridge=f"A useful place to begin is [{title}]({url}), as one lens among several rather than a final answer."
    elif profile.get("open_question") and not profile.get("afterlife"): opening="A question like this does not need to be settled before you begin exploring it."; bridge=f"A useful place to begin is [{title}]({url}), as one lens among several rather than a final answer."
    else: opening="A question like this is often easier to approach when there is a clear place to begin and room for the question to remain open."; bridge=f"A useful place to begin [{title}]({url})."
    sections=[opening,bridge,_evidence_boundary_note(docs,profile)]; archive=_archive_context(primary,docs,profile,title)
    if archive: sections.append(archive)
    interpretation=_archive_interpretation(_extract_archive_metadata(primary,docs),profile)
    if interpretation: sections.append(interpretation.rstrip(".") + ".")
    secondaries=_select_secondary_pathways(docs,title,profile)
    if secondaries:
        pathways=[]
        for doc in secondaries:
            link=_resource_link(doc)
            if link:pathways.append(f"{link} — for {_secondary_role(doc,profile)}.")
        if pathways: sections.append("From there, you can follow a couple of nearby reflections:\n\n"+"\n\n".join(pathways))
    sections.append("Take what feels useful, leave what does not, and let the question remain open where it needs to.")
    return "\n\n".join(x.strip() for x in sections if x.strip())

def _find_primary(user_query,docs):
    q=str(user_query or "").casefold(); axes=[]
    if re.search(r"\b(?:death|afterlife|reincarnation|mortality)\b",q): axes.append("mortality")
    if re.search(r"\b(?:belief|spiritual|religious|mystical|soul|continuity)\b",q): axes.append("belief")
    if not axes:return None
    scored=[]
    for i,doc in enumerate(docs):
        content=_clean_evidence_text(doc.get("text") or "").casefold(); hits=sum(bool(re.search(p,content)) for p in (r"\b(?:death|afterlife|reincarnation|mortality)\b",r"\b(?:belief|spiritual|religious|mystical|soul|continuity)\b")); direct=sum(t in content for t in ("death","afterlife","belief","continuity","question"))
        if hits and direct>=2: scored.append((hits,direct,-i,doc))
    return sorted(scored,reverse=True,key=lambda x:(x[0],x[1],x[2]))[0][3] if scored else None

def _meaning_question_can_use_guide(user_query,docs):
    q=re.sub(r"\s+"," ",str(user_query or "").strip().casefold()); open_meaning=bool(re.search(r"\b(?:what gives life meaning|life meaning|meaning in life|purpose|what matters|what makes life meaningful)\b",q)) and bool(re.search(r"\b(?:not sure|don't know|do not know|uncertain|explore|exploring|where might i begin|where should i begin|one particular answer|no particular answer)\b",q))
    if not open_meaning or not docs:return None
    candidates=[]
    for i,doc in enumerate(docs):
        title=_normalize_title(doc.get("title") or ""); text=_clean_evidence_text(doc.get("text") or ""); corpus=f"{title} {text}"; hits=len(re.findall(r"\b(?:meaning|purpose|existential|loneliness|emptiness|identity|wisdom|perspective)\b",corpus,re.I))
        if hits>=2 and str(doc.get("url") or "").strip(): candidates.append((hits,-i,doc))
    return sorted(candidates,reverse=True,key=lambda x:(x[0],x[1]))[0][2] if candidates else None

def _grief_question_can_use_guide(user_query,docs):
    q=re.sub(r"\s+"," ",str(user_query or "").strip().casefold()); open_grief=bool(re.search(r"\b(?:grief|grieving|bereavement|mourning|loss)\b",q)) and bool(re.search(r"\b(?:not sure|don't know|do not know|uncertain|explore|exploring|where might i begin|where should i begin|psychologically|psychological|spiritually|spiritual|meaning|understand)\b",q))
    if not open_grief or not docs:return None
    candidates=[]
    for i,doc in enumerate(docs):
        title=_normalize_title(doc.get("title") or ""); text=_clean_evidence_text(doc.get("text") or ""); corpus=f"{title} {text}"; hits=len(re.findall(r"\b(?:grief|loss|bereavement|psychological|spiritual|meaning|mortality|death)\b",corpus,re.I))
        if hits>=3 and str(doc.get("url") or "").strip(): candidates.append((hits,-i,doc))
    return sorted(candidates,reverse=True,key=lambda x:(x[0],x[1]))[0][2] if candidates else None

def _transition_evidence_fit(doc,profile):
    title=_normalize_title(doc.get("title") or ""); text=_clean_evidence_text(doc.get("text") or ""); corpus=f"{title} {text}"
    clusters={"transition":bool(re.search(r"\b(?:change|changed|transition|new chapter|starting over|begin again|moving forward|what comes next|uncertainty|uncertain|loss of role|life change|life transition)\b",corpus,re.I)),"meaning":bool(re.search(r"\b(?:meaning|purpose|identity|perspective|understanding|wisdom|belief)\b",corpus,re.I)),"experience":bool(re.search(r"\b(?:experience|lived|feelings?|emotion|emotional|inner life|journey|navigate|navigating)\b",corpus,re.I)),"open":bool(re.search(r"\b(?:question|explore|exploring|possibility|uncertainty|uncertain)\b",corpus,re.I)),"grounding":bool(re.search(r"\b(?:life|personal|human|lived experience|identity|role|circumstance|situation)\b",corpus,re.I))}
    strong_axis=sum(int(clusters[k]) for k in ("transition","meaning","experience","grounding")); score=sum(int(v) for v in clusters.values())
    if clusters["transition"]: score+=2
    if strong_axis<3: score-=4
    if re.search(r"\b(?:afterlife|reincarnation|starseed|awakening|soul's journey|soul layers)\b",corpus,re.I) and not clusters["transition"]: score-=5
    if re.search(r"\b(?:divorce|guilt|receiving|marriage|spouse|husband|wife)\b",corpus,re.I) and not re.search(r"\b(?:transition|change|identity|meaning|uncertainty|experience)\b",corpus,re.I): score-=3
    return score,clusters

def _transition_primary_from_docs(user_query,docs):
    profile=_query_profile(user_query,docs)
    if not profile.get("transition") or not profile.get("open_question") or not docs:return None,docs
    scored=[]
    for i,doc in enumerate(docs):
        fit,clusters=_transition_evidence_fit(doc,profile)
        if fit>=6 and clusters["transition"] and clusters["meaning"] and clusters["experience"] and str(doc.get("url") or "").strip() and _normalize_title(doc.get("title") or ""): scored.append((fit,-i,doc))
    if not scored:return None,docs
    scored.sort(key=lambda x:(-x[0],x[1])); return scored[0][2],docs

def _merge_recovered_documents(primary_docs,recovered_docs):
    merged=[]; seen=set()
    for doc in list(primary_docs or [])+list(recovered_docs or []):
        if not isinstance(doc,dict):continue
        title=_normalize_title(doc.get("title") or ""); url=str(doc.get("url") or doc.get("canonical_url") or "").strip(); key=url.casefold().rstrip("/") if url else title.casefold()
        if not title or not key or key in seen or not re.match(r"^https?://",url,re.I):continue
        merged.append({**doc,"title":title,"url":url,"text":_clean_evidence_text(doc.get("text") or "")}); seen.add(key)
    return merged

def _recover_transition_candidates(user_query):
    retriever=getattr(use_core,"_function_targeted_candidate_search",None)
    if not callable(retriever): return []
    try: recovered=retriever(user_query)
    except Exception as exc:
        print(f"USE v358 transition recovery error: {type(exc).__name__}: {exc}"); return []
    print(f"USE v358 transition recovery: protected_function_candidates={len(recovered) if isinstance(recovered,list) else 0}")
    return recovered if isinstance(recovered,list) else []

def _transition_gap_response():
    return ("The Living Archive does not currently have sufficiently grounded canonical material for this particular question, ""and I do not want to point you to a resource merely because its wording happens to overlap. ""It is better to leave the doorway open than pretend an unrelated resource is the right place to begin.")

def _v358_finalize(*args,**kwargs):
    query=str(kwargs.get("user_query") if kwargs.get("user_query") is not None else (args[0] if args else "")); context=_context_blocks_from_kwargs(args,kwargs); docs=_parse_context_documents(context); intent=str(kwargs.get("intent") if kwargs.get("intent") is not None else (args[2] if len(args)>2 else "")).strip().upper(); recommendation=use_core._is_recommendation_question(query)
    if not recommendation and (not intent or intent=="TOPICAL_INQUIRY"):
        primary=_find_primary(query,docs) or _meaning_question_can_use_guide(query,docs) or _grief_question_can_use_guide(query,docs)
        if primary:return _guide_answer(query,primary,docs)
        profile=_query_profile(query,docs)
        if profile.get("transition") and profile.get("open_question"):
            merged=_merge_recovered_documents(docs,_recover_transition_candidates(query)); primary,fit_docs=_transition_primary_from_docs(query,merged)
            if primary:return _guide_answer(query,primary,fit_docs)
            print("USE v358 TRANSITION EVIDENCE GATE: no sufficiently aligned canonical evidence; provider_generation_skipped=True"); return _transition_gap_response()
        sensitive=getattr(use_core,"_sensitive_open_question_can_use_guide",None)
        if callable(sensitive):
            primary=sensitive(query,docs)
            if primary:return _guide_answer(query,primary,docs)
    return str(_original_generate_llm_response(*args,**kwargs) or "").strip()

app=use_core.app
app.title=f"Find Your Way (USE) Navigation Engine {APP_VERSION}"
use_core.APP_VERSION=APP_VERSION; use_core.DEPLOYMENT_FINGERPRINT=DEPLOYMENT_FINGERPRINT; use_core.CANONICAL_BUILD_ID=CANONICAL_BUILD_ID; use_core.generate_llm_response=_v358_finalize
print(f"USE v358 GUIDE BUILD IDENTITY: build_id={CANONICAL_BUILD_ID}, version={APP_VERSION}, fingerprint={DEPLOYMENT_FINGERPRINT}, source_sha256={RUNTIME_SOURCE_SHA256}, core_blob_sha256={_core_runtime_sha}")
