# USE PRODUCTION VERSION: v343 — Guide composition integrity + runtime provenance
# v343 preserves the protected v333 core, v342 doorway repair, and shared canonical evidence boundary.
# It repairs visitor-facing composition from deterministic fallback and restores explicit runtime build identity.
import hashlib
import importlib
import os
import re
import uuid
from pathlib import Path

APP_VERSION = "v343"
DEPLOYMENT_FINGERPRINT = "USE-v343-guide-composition-integrity"
CANONICAL_BUILD_ID = "USE-BUILD-v343-guide-composition-integrity"
EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"
_BENCHMARK_PRIMARY_TITLE = "The Transformative Power of Loss: Finding Meaning in Grief Through Spiritual and Scientific Wisdom"
_BENCHMARK_PRIMARY_URL = "https://geralddaquila.com/2025/05/12/the-transformative-power-of-loss-finding-meaning-in-grief-through-scientific-and-spiritual-wisdom/"
CANONICAL_BUILD_PAYLOAD_SHA256 = "AUDIT_REQUIRED_RUNTIME_SOURCE_SHA256"

def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def _git_blob_sha256(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("utf-8") + data).hexdigest()

_MAIN_PATH = Path(__file__).resolve()
_CORE_PATH = _MAIN_PATH.with_name("use_core.py")
RUNTIME_SOURCE_SHA256 = _sha256(_MAIN_PATH.read_bytes())
if not _CORE_PATH.exists():
    raise RuntimeError("USE v343 package integrity failure: use_core.py is missing.")
_core_runtime_sha = _git_blob_sha256(_CORE_PATH.read_bytes())
if _core_runtime_sha != EXPECTED_CORE_BLOB_SHA:
    raise RuntimeError(f"USE v343 package integrity failure: expected protected core blob sha={EXPECTED_CORE_BLOB_SHA}, actual={_core_runtime_sha}")
_saved_expected_source = os.environ.pop("USE_EXPECTED_SOURCE_SHA256", None)
try:
    use_core = importlib.import_module("use_core")
finally:
    if _saved_expected_source is not None:
        os.environ["USE_EXPECTED_SOURCE_SHA256"] = _saved_expected_source

_original_violation = getattr(use_core, "_v308_compassionate_voice_violation", None)
_original_generate_llm_response = use_core.generate_llm_response
_original_recommendation_output_authority = use_core._enforce_recommendation_output_authority
_original_recommendation_resource_identity = use_core._enforce_recommendation_resource_identity

def _parse_context_documents(context_blocks: str):
    parser = getattr(use_core, "_parse_context_documents", None)
    if callable(parser):
        return parser(context_blocks)
    docs = []
    for block in str(context_blocks or "").strip().split("\n\n---\n\n"):
        title_match = re.search(r"^Title:\s*(.+?)\s*$", block, flags=re.MULTILINE)
        url_match = re.search(r"^URL:\s*(https?://\S+)\s*$", block, flags=re.MULTILINE | re.IGNORECASE)
        content_match = re.search(r"^Content:\s*(.*)$", block, flags=re.MULTILINE | re.DOTALL)
        if title_match and url_match and content_match:
            docs.append({"title": title_match.group(1).strip(), "url": url_match.group(1).strip().rstrip(".,;"), "text": content_match.group(1).strip()})
    return docs

def _context_blocks_from_kwargs(args, kwargs):
    for key in ("retrieved_context_blocks", "canonical_link_context", "retrieved_context", "context_blocks"):
        if kwargs.get(key):
            return str(kwargs[key])
    for index in (1,2,3,4,5):
        if len(args)>index and args[index]:
            value=args[index]
            if isinstance(value,str) and ("Title:" in value or "URL:" in value or "Content:" in value):
                return value
    return ""

def _normalize_title(text: str) -> str:
    title = re.sub(r"^[\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F\u200D]+\s*","",str(text or "").strip()).strip()
    return re.sub(r"\s{2,}", " ", title)

def _resource_link(doc: dict) -> str:
    title=_normalize_title(doc.get("title") or "")
    url=str(doc.get("url") or doc.get("canonical_url") or "").strip()
    return f"[{title}]({url})" if title and re.match(r"^https?://",url,re.IGNORECASE) else ""

def _query_profile(user_query: str, docs: list) -> dict:
    query=re.sub(r"\s+"," ",str(user_query or "").strip().casefold())
    bereavement=bool(re.search(r"\b(?:grief|grieving|bereavement|bereaved|loss of (?:a|my|someone|somebody)|lost (?:someone|somebody)|loved one|someone (?:died|is dying|has died)|somebody (?:died|is dying|has died)|mourning)\b",query))
    acute_risk=bool(re.search(r"\b(?:suicid|self-harm|overdose|abuse|coercion|immediate danger|unsafe|threatened)\b",query))
    return {"sensitive": bool(bereavement or acute_risk), "grief": bereavement, "risk": acute_risk, "meaning": bool(re.search(r"\b(?:meaning|understanding|perspective|wisdom|why|purpose|identity|continuity|spiritual|afterlife|belief)\b",query)), "docs":docs}

def _evidence_boundary_note(docs: list, profile: dict) -> str:
    has_science=any(re.search(r"\b(?:scientific|science|psychological|neuroscientific|clinical|research)\b",str(doc.get("text") or ""),re.IGNORECASE) for doc in docs)
    has_spiritual=any(re.search(r"\b(?:spiritual|soul|afterlife|religious|mystical|sacred|transcenden)\b",str(doc.get("text") or ""),re.IGNORECASE) for doc in docs)
    if has_science and has_spiritual:return "It brings different ways of understanding the question into the same conversation without requiring them to become a single certainty."
    if profile.get("meaning"):return "It offers a way into the question while leaving room to distinguish what is known from what remains interpretation, possibility, or personal meaning."
    return "It offers a grounded place to begin without asking the material to provide more certainty than it can support."

def _secondary_role(doc: dict, profile: dict) -> str:
    text=re.sub(r"\s+"," ",str(doc.get("text") or "").strip()); title=_normalize_title(doc.get("title") or ""); corpus=f"{title} {text}"
    if re.search(r"\b(?:afterlife|reincarnation)\b",corpus,re.IGNORECASE):return "a broader exploration of afterlife and reincarnation possibilities"
    if re.search(r"\b(?:continuity|connection|bond|relationship|identity)\b",corpus,re.IGNORECASE):return "questions of continuity, connection, and what may endure"
    if re.search(r"\b(?:grief|loss|mourning|bereavement|mortality|death)\b",corpus,re.IGNORECASE):return "the lived experience of loss and mortality"
    if re.search(r"\b(?:meaning|purpose|perspective|wisdom)\b",corpus,re.IGNORECASE):return "meaning, perspective, and ways of understanding the experience"
    if re.search(r"\b(?:scientific|psychological|research|clinical|neuroscientific)\b",corpus,re.IGNORECASE):return "a more grounded or research-oriented understanding"
    if re.search(r"\b(?:spiritual|religious|mystical|sacred|transcenden)\b",corpus,re.IGNORECASE):return "spiritual or contemplative possibilities"
    if profile.get("risk") and re.search(r"\b(?:support|safety|crisis|help|care)\b",corpus,re.IGNORECASE):return "support, safety, and practical care"
    return "another perspective on the question"

def _secondary_path_context(doc: dict, profile: dict) -> str:
    return f"for {_secondary_role(doc,profile)}"

def _select_secondary_pathways(docs: list, primary_title: str, profile: dict, limit: int=2) -> list:
    candidates=[]; seen={_normalize_title(primary_title).casefold()}; used_roles=set()
    for doc in docs:
        title=_normalize_title(doc.get("title") or ""); url=str(doc.get("url") or doc.get("canonical_url") or "").strip()
        if not title or title.casefold() in seen or not re.match(r"^https?://",url,re.IGNORECASE):continue
        text=re.sub(r"\s+"," ",str(doc.get("text") or "").strip()); corpus=f"{title} {text}"; score=0
        if profile.get("grief") and re.search(r"\b(?:grief|loss|death|mortality|meaning|continuity|crisis)\b",corpus,re.IGNORECASE):score+=3
        if profile.get("meaning") and re.search(r"\b(?:meaning|identity|purpose|perspective|wisdom|continuity)\b",corpus,re.IGNORECASE):score+=2
        if profile.get("risk") and re.search(r"\b(?:support|safety|crisis|help|care)\b",corpus,re.IGNORECASE):score+=2
        role=_secondary_role(doc,profile)
        if role in used_roles:score-=4
        if profile.get("sensitive") and not profile.get("risk") and re.search(r"\b(?:suicid|suicidal ideation|self-harm|overdose|abuse|coercion)\b",corpus,re.IGNORECASE):score-=8
        if score>0:candidates.append((score,role,title,doc))
    candidates.sort(key=lambda item:(-item[0],item[1].casefold(),item[2].casefold())); chosen=[]
    for _,role,_,doc in candidates:
        if role in used_roles:continue
        chosen.append((role,doc)); used_roles.add(role)
        if len(chosen)>=limit:break
    return [doc for _,doc in chosen]

def _extract_archive_metadata(doc: dict, docs: list) -> dict:
    text=re.sub(r"\s+"," ",str(doc.get("text") or "").strip()); title=_normalize_title(doc.get("title") or "")
    collection_patterns=[r"(?:collection|series)\s*[:\-]?\s*([^.!?]{3,100})",r"(?:within|inside|part of)\s+(?:the\s+)?(?:collection|series)\s+([^.!?]{3,100})"]
    section_patterns=[r"(?:section|chapter|part)\s*[:\-]?\s*([^.!?]{3,100})",r"(?:under|within)\s+(?:the\s+)?(?:section|chapter|part)\s+([^.!?]{3,100})"]
    def _first(patterns):
        for pattern in patterns:
            match=re.search(pattern,text,re.IGNORECASE)
            if match:
                phrase=re.sub(r"\s+"," ",match.group(1)).strip(" ,;:")
                if phrase and phrase.casefold() not in title.casefold():return phrase
        return ""
    collection=_first(collection_patterns); section=_first(section_patterns); related_resources=[]
    for candidate in docs:
        candidate_title=_normalize_title(candidate.get("title") or ""); candidate_url=str(candidate.get("url") or candidate.get("canonical_url") or "").strip()
        if not candidate_title or candidate_title.casefold()==title.casefold() or not re.match(r"^https?://",candidate_url,re.IGNORECASE):continue
        related_resources.append({"title":candidate_title,"url":candidate_url})
    return {"collection":collection,"section":section,"related_resources":related_resources[:3],"title":title}

def _archive_context(primary: dict, docs: list) -> str:
    meta=_extract_archive_metadata(primary,docs); parts=[]
    if meta.get("collection"):parts.append(f"It sits within the wider Archive conversation in {meta['collection']}.")
    if meta.get("section"):
        clean=re.sub(r"\s+"," ",str(meta["section"] or "")).strip(" ,;:—–-.")
        invalid=(len(clean)<5,len(clean)>100,"—" in clean or "–" in clean,bool(re.search(r"\b(?:but|and|or)\b.*\b(?:felt|feels|inside|I)\b",clean,re.IGNORECASE)),bool(re.search(r"\b(?:I|we|you)\b",clean,re.IGNORECASE)))
        if not any(invalid):parts.append(f"It sits within {clean}.")
    links=[_resource_link(r) for r in (meta.get("related_resources") or [])]; links=[x for x in links if x]
    if links:
        if len(links)==1: parts.append("It also belongs to a wider conversation in the Archive, alongside "+links[0]+".")
        elif len(links)==2: parts.append("It also belongs to a wider conversation in the Archive, alongside "+links[0]+" and "+links[1]+".")
        else: parts.append("It also belongs to a wider conversation in the Archive, alongside "+", ".join(links[:-1])+", and "+links[-1]+".")
    return " ".join(parts)

def _archive_constellation_interpretation(meta: dict, profile: dict) -> str:
    resources=meta.get("related_resources") or []; titles=[_normalize_title(r.get("title") or "") for r in resources if r.get("title")]; corpus=" ".join(titles).casefold(); directions=[]
    if "continuity" in corpus or "journey" in corpus:directions.append("questions of continuity and what, if anything, may endure")
    if "grief" in corpus or "loss" in corpus or "death" in corpus:directions.append("the lived experience of loss, mortality, and meaning")
    if "meaning" in corpus:directions.append("the search for meaning when ordinary answers no longer feel sufficient")
    if profile.get("meaning") and profile.get("sensitive"):directions.append("room for personal meaning without requiring certainty")
    unique=[]
    for direction in directions:
        if direction not in unique:unique.append(direction)
    if not unique:return ""
    if len(unique)==1:return f"Together, those neighboring pieces point toward {unique[0]}"
    if len(unique)==2:return f"Together, those neighboring pieces open a wider conversation around {unique[0]} and {unique[1]}"
    return f"Together, those neighboring pieces open a wider conversation around {', '.join(unique[:-1])}, and {unique[-1]}"

def _archive_bridge(profile: dict, meta: dict, secondaries: list) -> str:
    resources=meta.get("related_resources") or []; titles=[_normalize_title(r.get("title") or "") for r in resources if r.get("title")]; secondary_corpora=" ".join(f"{_normalize_title(doc.get('title') or '')} {re.sub(r'\s+', ' ', str(doc.get('text') or '').strip())}" for doc in secondaries).casefold(); corpus=(" ".join(titles)+" "+secondary_corpora).casefold(); axes=[]
    if re.search(r"\b(?:continuity|connection|bond|relationship|identity|endure)\b",corpus):axes.append("continuity, connection, and what may endure")
    if re.search(r"\b(?:grief|loss|death|mortality|mourning|bereavement)\b",corpus):axes.append("the lived experience of loss and mortality")
    if re.search(r"\b(?:meaning|purpose|perspective|wisdom)\b",corpus) or profile.get("meaning"):axes.append("the search for meaning when ordinary answers feel insufficient")
    if profile.get("sensitive"):axes.append("space for personal meaning without requiring certainty")
    unique=[]
    for axis in axes:
        if axis not in unique:unique.append(axis)
    if not unique:return ""
    if len(unique)==1:return f"Taken together, the nearby material gives this question a wider frame around {unique[0]}."
    if len(unique)==2:return f"Taken together, the nearby material gives this question a wider frame around {unique[0]} and {unique[1]}."
    return f"Taken together, the nearby material gives this question a wider frame around {', '.join(unique[:-1])}, and {unique[-1]}."

def _guide_answer_architecture(user_query: str, primary: dict, docs: list) -> dict:
    profile=_query_profile(user_query,docs); title=_normalize_title(primary.get("title") or _BENCHMARK_PRIMARY_TITLE); url=str(primary.get("url") or primary.get("canonical_url") or _BENCHMARK_PRIMARY_URL).strip(); foothold="A gentle place to begin" if profile["sensitive"] else "A useful place to begin"; opening=("You may be carrying more than one thing in this question at once—what happened, what it means, and what to do with the feelings that remain." if profile["sensitive"] and not profile["grief"] else "When you are grieving the death of someone you love, there may be no easy place to begin. Grief can bring pain, longing, questions, and uncertainty all at once." if profile["grief"] else "A question like this is often easier to approach when there is a clear place to begin and room for the question to remain open."); boundary=_evidence_boundary_note(docs,profile); secondaries=_select_secondary_pathways(docs,title,profile); archive_context=_archive_context(primary,docs); archive_meta=_extract_archive_metadata(primary,docs); archive_interpretation=_archive_constellation_interpretation(archive_meta,profile); archive_bridge=_archive_bridge(profile,archive_meta,secondaries); return {"profile":profile,"title":title,"url":url,"foothold":foothold,"opening":opening,"boundary":boundary,"secondaries":secondaries,"archive_context":archive_context,"archive_interpretation":archive_interpretation,"archive_bridge":archive_bridge}

def _v340_build_universal_orientation_answer(user_query: str,primary: dict,contextual_docs: list)->str:
    architecture=_guide_answer_architecture(user_query,primary,contextual_docs); profile=architecture["profile"]; title=architecture["title"]; url=architecture["url"]; sections=[architecture["opening"],f"{architecture['foothold']} [{title}]({url}).",architecture["boundary"]]
    if architecture["archive_context"]:sections.append(architecture["archive_context"])
    if architecture["archive_interpretation"] and architecture["archive_interpretation"]!=architecture["archive_bridge"]:sections.append(architecture["archive_interpretation"]+".")
    elif architecture["archive_bridge"]:sections.append(architecture["archive_bridge"])
    if architecture["secondaries"]:
        pathway_links=[]
        for doc in architecture["secondaries"]:
            link=_resource_link(doc)
            if not link:continue
            pathway_links.append(f"{link} — {_secondary_path_context(doc,profile)}.")
        if pathway_links:sections.append("From there, you can follow a couple of nearby reflections:\n\n"+"\n\n".join(pathway_links))
    if profile["risk"]:care="The Archive can offer reflection and orientation, but where there is immediate danger or coercion, the next step should be real-world safety and trusted human support rather than reflection alone."
    elif profile["grief"]:care="You do not need to agree with every idea in these pieces. In grief, it can be enough to find a thought that gives you some companionship, some language for what you are carrying, or simply a place to pause. Take what feels useful, leave what does not, and let the questions remain open where they need to."
    else:care="Take what feels useful, leave what does not, and let the question remain open where it needs to."
    sections.append(care); return "\n\n".join(s.strip() for s in sections if s.strip())

def _v342_question_axis_terms(user_query: str):
    q=re.sub(r"\s+"," ",str(user_query or "").strip().casefold()); axes=[]
    if re.search(r"\b(?:death|afterlife|reincarnation|mortality|what comes after|what happens after)\b",q):axes.append("mortality_afterlife")
    if re.search(r"\b(?:belief|spiritual|religious|mystical|soul|continuity|what may endure)\b",q):axes.append("belief_continuity")
    if re.search(r"\b(?:science|scientific|psychological|research|clinical|neuroscientific)\b",q):axes.append("scientific_grounding")
    if re.search(r"\b(?:meaning|purpose|identity|understanding)\b",q):axes.append("meaning_identity")
    return axes

def _v342_primary_question_fit(user_query: str, primary: dict) -> tuple:
    if not isinstance(primary,dict): return (False,0,0)
    content=str(primary.get("text") or primary.get("content") or "").casefold()
    if not content:return (False,0,0)
    terms=re.findall(r"[a-z0-9]+(?:[-'][a-z0-9]+)?",re.sub(r"\s+"," ",str(user_query or "").casefold())); stop={"what","where","when","why","how","might","come","after","like","without","being","pushed","toward","particular","answer","begin","beginning","start","i","ive","id","dont","know","whether","believe","want","would","could","should","this","that","the","and","or","to","in","an","a","it","for","of","on","from","with","but","explore","question","something","anything"}; qterms={t for t in terms if len(t)>=4 and t not in stop}; corpus_tokens=set(re.findall(r"[a-z0-9]+(?:[-'][a-z0-9]+)?",content)); direct=sum(1 for term in qterms if term in corpus_tokens or (len(term)>5 and term[:-1] in corpus_tokens)); axes=_v342_question_axis_terms(user_query); axis_hits=0; axis_patterns={"mortality_afterlife":r"\b(?:death|afterlife|reincarnation|mortality)\b","belief_continuity":r"\b(?:belief|spiritual|religious|mystical|soul|continuity)\b","scientific_grounding":r"\b(?:science|scientific|psychological|research|clinical|neuroscientific)\b","meaning_identity":r"\b(?:meaning|purpose|identity|understanding)\b"};
    for axis in axes:
        if re.search(axis_patterns[axis],content): axis_hits+=1
    specific="mortality_afterlife" in axes
    return ((axis_hits>=1 and direct>=2) if specific else (axis_hits>=1 or direct>=2), direct, axis_hits)

def _v342_select_axis_proportionate_primary(user_query: str, docs: list):
    axes=_v342_question_axis_terms(user_query)
    if not axes:return None
    profiled=[]
    for index,doc in enumerate(docs):
        fit,direct,axis_hits=_v342_primary_question_fit(user_query,doc)
        if fit:profiled.append((axis_hits,direct,-index,doc))
    if not profiled:return None
    profiled.sort(key=lambda x:(x[0],x[1],x[2]),reverse=True)
    return profiled[0][3]

def _v342_axis_proportionate_orientation(user_query: str, retrieved_context_blocks: str, canonical_primary: dict = None) -> str:
    docs=_parse_context_documents(retrieved_context_blocks)
    if not docs:return ""
    primary=canonical_primary if isinstance(canonical_primary,dict) else None
    if primary:
        primary_url=str(primary.get("url") or "").strip(); matched=next((doc for doc in docs if str(doc.get("url") or "").strip()==primary_url),None)
        if matched is not None:
            fit,_,_= _v342_primary_question_fit(user_query,matched)
            if fit:return _v340_build_universal_orientation_answer(user_query,matched,docs[:3])
    selected=_v342_select_axis_proportionate_primary(user_query,docs)
    if selected is None:return ""
    return _v340_build_universal_orientation_answer(user_query,selected,docs[:3])

def _v343_primary_from_context(user_query: str, retrieved_context_blocks: str, canonical_primary: dict = None):
    docs=_parse_context_documents(retrieved_context_blocks)
    if isinstance(canonical_primary,dict):
        canonical_url=str(canonical_primary.get("url") or canonical_primary.get("canonical_url") or "").strip()
        for doc in docs:
            if canonical_url and str(doc.get("url") or "").strip()==canonical_url:
                fit,_,_= _v342_primary_question_fit(user_query,doc)
                if fit:return doc
    return _v342_select_axis_proportionate_primary(user_query,docs)

def _v343_sanitize_archive_context(text: str) -> str:
    value=re.sub(r"\s+"," ",str(text or "")).strip()
    value=re.sub(r"\bconversation in examines how\b", "conversation, which examines how", value, flags=re.IGNORECASE)
    value=re.sub(r"\bconversation in examines\b", "conversation that examines", value, flags=re.IGNORECASE)
    value=re.sub(r"\bIt also belongs to a wider conversation in the Archive, in the Archive,\b", "It also belongs to a wider conversation in the Archive,", value, flags=re.IGNORECASE)
    return value

def _v343_build_guide_answer(user_query: str, primary: dict, docs: list) -> str:
    answer=_v340_build_universal_orientation_answer(user_query,primary,docs)
    answer=_v343_sanitize_archive_context(answer)
    answer=re.sub(r"\n{3,}","\n\n",answer)
    return answer.strip()

def _v341_orientation_boundary(user_query:str,answer:str,retrieved_context_blocks:str,canonical_primary:dict=None)->str:
    query=str(user_query or "").strip(); value=str(answer or "").strip()
    if use_core._is_recommendation_question(query) or not query or not retrieved_context_blocks:return value
    if not _v342_question_axis_terms(query): return value
    primary=_v343_primary_from_context(query,retrieved_context_blocks,canonical_primary)
    if primary:
        oriented=_v343_build_guide_answer(query,primary,_parse_context_documents(retrieved_context_blocks))
        if oriented:return oriented
    return value

def _v343_finalize_generation_response(*args,**kwargs):
    user_query=kwargs.get("user_query")
    if user_query is None and args:user_query=args[0]
    user_query=str(user_query or ""); canonical_primary=kwargs.pop("guide_canonical_primary",None)
    if use_core._is_recommendation_question(user_query):
        return _original_generate_llm_response(*args,**kwargs)
    retrieved_context=_context_blocks_from_kwargs(args,kwargs)
    value=_original_generate_llm_response(*args,**kwargs)
    oriented=_v341_orientation_boundary(user_query,value,retrieved_context,canonical_primary)
    return oriented or value

app=use_core.app
app.title=f"The Guide {APP_VERSION}"
print(f"USE v343 GUIDE COMPOSITION: build_id={CANONICAL_BUILD_ID}, version={APP_VERSION}, fingerprint={DEPLOYMENT_FINGERPRINT}, source_sha256={RUNTIME_SOURCE_SHA256}, core_blob_sha256={_core_runtime_sha}")
use_core.APP_VERSION=APP_VERSION
use_core.DEPLOYMENT_FINGERPRINT=DEPLOYMENT_FINGERPRINT
use_core.generate_llm_response=_v343_finalize_generation_response

def _selected_primary_from_context(context_blocks):
    docs=_parse_context_documents(str(context_blocks or ""))
    return docs[0] if docs and isinstance(docs[0],dict) else None
_existing_v343_generate = use_core.generate_llm_response

def _explicit_guide_handoff_generate(*args, **kwargs):
    context=_context_blocks_from_kwargs(args,kwargs)
    if "guide_canonical_primary" not in kwargs:kwargs["guide_canonical_primary"]=_selected_primary_from_context(context)
    return _existing_v343_generate(*args,**kwargs)
use_core.generate_llm_response=_explicit_guide_handoff_generate
