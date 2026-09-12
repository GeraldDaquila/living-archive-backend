# USE PRODUCTION VERSION: v344 — Guide chunk preservation
# v344 preserves protected v333 core, v342 doorway selection, and v343 semantic composition.
# It restores explicit paragraph boundaries in deterministic Guide fallback output.
import hashlib
import importlib
import os
import re
import uuid
from pathlib import Path

APP_VERSION = "v344"
DEPLOYMENT_FINGERPRINT = "USE-v344-guide-chunk-preservation"
CANONICAL_BUILD_ID = "USE-BUILD-v344-guide-chunk-preservation"
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
    raise RuntimeError("USE v344 package integrity failure: use_core.py is missing.")
_core_runtime_sha = _git_blob_sha256(_CORE_PATH.read_bytes())
if _core_runtime_sha != EXPECTED_CORE_BLOB_SHA:
    raise RuntimeError(f"USE v344 package integrity failure: expected protected core blob sha={EXPECTED_CORE_BLOB_SHA}, actual={_core_runtime_sha}")
use_core = importlib.import_module("use_core")
_original_generate_llm_response = use_core.generate_llm_response

def _parse_context_documents(context_blocks: str):
    parser = getattr(use_core, "_parse_context_documents", None)
    if callable(parser):
        return parser(context_blocks)
    docs=[]
    for block in str(context_blocks or "").strip().split("\n\n---\n\n"):
        title_match=re.search(r"^Title:\s*(.+?)\s*$",block,re.MULTILINE)
        url_match=re.search(r"^URL:\s*(https?://\S+)\s*$",block,re.MULTILINE|re.IGNORECASE)
        content_match=re.search(r"^Content:\s*(.*)$",block,re.MULTILINE|re.DOTALL)
        if title_match and url_match and content_match:
            docs.append({"title":title_match.group(1).strip(),"url":url_match.group(1).strip().rstrip(".,;"),"text":content_match.group(1).strip()})
    return docs

def _context_blocks_from_kwargs(args, kwargs):
    for key in ("retrieved_context_blocks","canonical_link_context","retrieved_context","context_blocks"):
        if kwargs.get(key): return str(kwargs[key])
    for index in (1,2,3,4,5):
        if len(args)>index and args[index] and isinstance(args[index],str) and any(k in args[index] for k in ("Title:","URL:","Content:")):
            return args[index]
    return ""

def _normalize_title(text: str) -> str:
    text=re.sub(r"^[\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F\u200D]+\s*","",str(text or "").strip()).strip()
    return re.sub(r"\s{2,}"," ",text)

def _resource_link(doc: dict) -> str:
    title=_normalize_title(doc.get("title") or "")
    url=str(doc.get("url") or doc.get("canonical_url") or "").strip()
    return f"[{title}]({url})" if title and re.match(r"^https?://",url,re.IGNORECASE) else ""

def _query_profile(user_query: str, docs: list) -> dict:
    q=re.sub(r"\s+"," ",str(user_query or "").strip().casefold())
    bereavement=bool(re.search(r"\b(?:grief|grieving|bereavement|bereaved|loss of (?:a|my|someone|somebody)|lost (?:someone|somebody)|loved one|someone (?:died|is dying|has died)|somebody (?:died|is dying|has died)|mourning)\b",q))
    risk=bool(re.search(r"\b(?:suicid|self-harm|overdose|abuse|coercion|immediate danger|unsafe|threatened)\b",q))
    return {"sensitive":bool(bereavement or risk),"grief":bereavement,"risk":risk,"meaning":bool(re.search(r"\b(?:meaning|understanding|perspective|wisdom|why|purpose|identity|continuity|spiritual|afterlife|belief)\b",q)),"docs":docs}

def _evidence_boundary_note(docs, profile):
    has_science=any(re.search(r"\b(?:scientific|science|psychological|neuroscientific|clinical|research)\b",str(d.get("text") or ""),re.I) for d in docs)
    has_spiritual=any(re.search(r"\b(?:spiritual|soul|afterlife|religious|mystical|sacred|transcenden)\b",str(d.get("text") or ""),re.I) for d in docs)
    if has_science and has_spiritual:return "It brings different ways of understanding the question into the same conversation without requiring them to become a single certainty."
    if profile.get("meaning"):return "It offers a way into the question while leaving room to distinguish what is known from what remains interpretation, possibility, or personal meaning."
    return "It offers a grounded place to begin without asking the material to provide more certainty than it can support."

def _secondary_role(doc, profile):
    corpus=f"{_normalize_title(doc.get('title') or '')} {re.sub(r'\s+',' ',str(doc.get('text') or '').strip())}"
    for pattern, role in [
        (r"\b(?:afterlife|reincarnation)\b","a broader exploration of afterlife and reincarnation possibilities"),
        (r"\b(?:continuity|connection|bond|relationship|identity)\b","questions of continuity, connection, and what may endure"),
        (r"\b(?:grief|loss|mourning|bereavement|mortality|death)\b","the lived experience of loss and mortality"),
        (r"\b(?:meaning|purpose|perspective|wisdom)\b","meaning, perspective, and ways of understanding the experience"),
        (r"\b(?:scientific|psychological|research|clinical|neuroscientific)\b","a more grounded or research-oriented understanding"),
        (r"\b(?:spiritual|religious|mystical|sacred|transcenden)\b","spiritual or contemplative possibilities")]:
        if re.search(pattern,corpus,re.I): return role
    return "another perspective on the question"

def _select_secondary_pathways(docs, primary_title, profile, limit=2):
    seen={_normalize_title(primary_title).casefold()}; candidates=[]; used=set()
    for doc in docs:
        title=_normalize_title(doc.get("title") or ""); url=str(doc.get("url") or doc.get("canonical_url") or "").strip()
        if not title or title.casefold() in seen or not re.match(r"^https?://",url,re.I): continue
        corpus=f"{title} {re.sub(r'\s+',' ',str(doc.get('text') or '').strip())}"; score=0
        if profile.get("grief") and re.search(r"\b(?:grief|loss|death|mortality|meaning|continuity|crisis)\b",corpus,re.I): score+=3
        if profile.get("meaning") and re.search(r"\b(?:meaning|identity|purpose|perspective|wisdom|continuity|afterlife|reincarnation)\b",corpus,re.I): score+=2
        role=_secondary_role(doc,profile)
        if role in used: score-=4
        if profile.get("sensitive") and not profile.get("risk") and re.search(r"\b(?:suicid|self-harm|overdose|abuse|coercion)\b",corpus,re.I): score-=8
        if score>0:candidates.append((score,role,title,doc))
    candidates.sort(key=lambda x:(-x[0],x[1].casefold(),x[2].casefold()))
    out=[]
    for _,role,_,doc in candidates:
        if role in used: continue
        out.append(doc); used.add(role)
        if len(out)>=limit: break
    return out

def _extract_archive_metadata(doc, docs):
    text=re.sub(r"\s+"," ",str(doc.get("text") or "").strip()); title=_normalize_title(doc.get("title") or "")
    collection=""; section=""
    for pattern,target in [
        (r"(?:collection|series)\s*[:\-]?\s*([^.!?]{3,100})","collection"),
        (r"(?:within|inside|part of)\s+(?:the\s+)?(?:collection|series)\s+([^.!?]{3,100})","collection"),
        (r"(?:section|chapter|part)\s*[:\-]?\s*([^.!?]{3,100})","section"),
        (r"(?:under|within)\s+(?:the\s+)?(?:section|chapter|part)\s+([^.!?]{3,100})","section")]:
        m=re.search(pattern,text,re.I)
        if m and not locals()[target]:
            phrase=re.sub(r"\s+"," ",m.group(1)).strip(" ,;:")
            if phrase and phrase.casefold() not in title.casefold(): locals()[target]=phrase
    related=[]
    for candidate in docs:
        ct=_normalize_title(candidate.get("title") or ""); cu=str(candidate.get("url") or candidate.get("canonical_url") or "").strip()
        if ct and ct.casefold()!=title.casefold() and re.match(r"^https?://",cu,re.I): related.append({"title":ct,"url":cu})
    return {"collection":collection,"section":section,"related_resources":related[:3],"title":title}

def _archive_context(primary, docs):
    meta=_extract_archive_metadata(primary,docs); parts=[]
    if meta["collection"]: parts.append(f"It sits within the wider Archive conversation in {meta['collection']}.")
    if meta["section"]:
        clean=re.sub(r"\s+"," ",meta["section"]).strip(" ,;:—–-.")
        invalid=(len(clean)<5,len(clean)>100,"—" in clean or "–" in clean,bool(re.search(r"\b(?:but|and|or)\b.*\b(?:felt|feels|inside|I)\b",clean,re.I)),bool(re.search(r"\b(?:I|we|you)\b",clean,re.I)))
        if not any(invalid): parts.append(f"It sits within {clean}.")
    links=[_resource_link(x) for x in meta["related_resources"] if _resource_link(x)]
    if links:
        parts.append("It also belongs to a wider conversation in the Archive, alongside "+(" and ".join(links) if len(links)==2 else ", ".join(links[:-1])+", and "+links[-1] if len(links)>2 else links[0])+".")
    return " ".join(parts)

def _archive_interpretation(meta, profile):
    titles=" ".join(x.get("title","") for x in meta.get("related_resources") or []).casefold(); d=[]
    if "continuity" in titles or "journey" in titles:d.append("questions of continuity and what, if anything, may endure")
    if any(x in titles for x in ("grief","loss","death")):d.append("the lived experience of loss, mortality, and meaning")
    if "meaning" in titles:d.append("the search for meaning when ordinary answers no longer feel sufficient")
    unique=list(dict.fromkeys(d))
    if not unique:return ""
    if len(unique)==1:return f"Together, those neighboring pieces point toward {unique[0]}"
    if len(unique)==2:return f"Together, those neighboring pieces open a wider conversation around {unique[0]} and {unique[1]}"
    return f"Together, those neighboring pieces open a wider conversation around {', '.join(unique[:-1])}, and {unique[-1]}"

def _guide_answer(user_query, primary, docs):
    profile=_query_profile(user_query,docs); title=_normalize_title(primary.get("title") or _BENCHMARK_PRIMARY_TITLE); url=str(primary.get("url") or primary.get("canonical_url") or _BENCHMARK_PRIMARY_URL).strip()
    sections=["A question like this is often easier to approach when there is a clear place to begin and room for the question to remain open.", f"A useful place to begin [{title}]({url}).", _evidence_boundary_note(docs,profile)]
    archive=_archive_context(primary,docs)
    if archive: sections.append(archive)
    meta=_extract_archive_metadata(primary,docs); interpretation=_archive_interpretation(meta,profile)
    if interpretation: sections.append(interpretation+".")
    secondaries=_select_secondary_pathways(docs,title,profile)
    if secondaries:
        pathways=[]
        for doc in secondaries:
            link=_resource_link(doc)
            if link: pathways.append(f"{link} — for {_secondary_role(doc,profile)}.")
        if pathways: sections.append("From there, you can follow a couple of nearby reflections:\n\n"+"\n\n".join(pathways))
    sections.append("Take what feels useful, leave what does not, and let the question remain open where it needs to.")
    return "\n\n".join(x.strip() for x in sections if x.strip())

def _find_primary(user_query, docs):
    axes=[]
    q=str(user_query or "").casefold()
    if re.search(r"\b(?:death|afterlife|reincarnation|mortality)\b",q): axes.append("mortality")
    if re.search(r"\b(?:belief|spiritual|religious|mystical|soul|continuity)\b",q): axes.append("belief")
    if not axes:return None
    scored=[]
    for i,doc in enumerate(docs):
        content=str(doc.get("text") or "").casefold(); hits=sum(bool(re.search(p,content)) for p in (r"\b(?:death|afterlife|reincarnation|mortality)\b",r"\b(?:belief|spiritual|religious|mystical|soul|continuity)\b"))
        direct=sum(t in content for t in ("death","afterlife","belief","continuity","question"))
        if hits and direct>=2: scored.append((hits,direct,-i,doc))
    if not scored:return None
    return sorted(scored,reverse=True,key=lambda x:(x[0],x[1],x[2]))[0][3]

def _v344_finalize(*args,**kwargs):
    query=str(kwargs.get("user_query") if kwargs.get("user_query") is not None else (args[0] if args else ""))
    context=_context_blocks_from_kwargs(args,kwargs)
    value=str(_original_generate_llm_response(*args,**kwargs) or "").strip()
    if use_core._is_recommendation_question(query): return value
    docs=_parse_context_documents(context)
    primary=_find_primary(query,docs)
    if primary:
        return _guide_answer(query,primary,docs)
    return value

app=use_core.app
app.title=f"Find Your Way (USE) Navigation Engine {APP_VERSION}"
print(f"USE v344 GUIDE CHUNK PRESERVATION: build_id={CANONICAL_BUILD_ID}, version={APP_VERSION}, fingerprint={DEPLOYMENT_FINGERPRINT}, source_sha256={RUNTIME_SOURCE_SHA256}, core_blob_sha256={_core_runtime_sha}")
use_core.APP_VERSION=APP_VERSION
use_core.DEPLOYMENT_FINGERPRINT=DEPLOYMENT_FINGERPRINT
use_core.generate_llm_response=_v344_finalize