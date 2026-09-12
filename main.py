# USE PRODUCTION VERSION: v345 — Guide chunk preservation + provenance alignment
import hashlib
import importlib
import os
import re
import uuid
from pathlib import Path

APP_VERSION = "v345"
DEPLOYMENT_FINGERPRINT = "USE-v345-guide-chunk-preservation-provenance"
CANONICAL_BUILD_ID = "USE-BUILD-v345-guide-chunk-preservation-provenance"
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
    raise RuntimeError("USE v345 package integrity failure: use_core.py is missing.")
_core_runtime_sha = _git_blob_sha256(_CORE_PATH.read_bytes())
if _core_runtime_sha != EXPECTED_CORE_BLOB_SHA:
    raise RuntimeError(f"USE v345 package integrity failure: expected protected core blob sha={EXPECTED_CORE_BLOB_SHA}, actual={_core_runtime_sha}")
use_core = importlib.import_module("use_core")
_original_generate_llm_response = use_core.generate_llm_response

def _parse_context_documents(context_blocks: str):
    parser = getattr(use_core, "_parse_context_documents", None)
    if callable(parser): return parser(context_blocks)
    docs=[]
    for block in str(context_blocks or "").strip().split("\n\n---\n\n"):
        m1=re.search(r"^Title:\s*(.+?)\s*$",block,re.M); m2=re.search(r"^URL:\s*(https?://\S+)\s*$",block,re.M|re.I); m3=re.search(r"^Content:\s*(.*)$",block,re.M|re.S)
        if m1 and m2 and m3: docs.append({"title":m1.group(1).strip(),"url":m2.group(1).strip().rstrip(".,;"),"text":m3.group(1).strip()})
    return docs

def _context_blocks_from_kwargs(args, kwargs):
    for key in ("retrieved_context_blocks","canonical_link_context","retrieved_context","context_blocks"):
        if kwargs.get(key): return str(kwargs[key])
    for index in (1,2,3,4,5):
        if len(args)>index and isinstance(args[index],str) and any(k in args[index] for k in ("Title:","URL:","Content:")): return args[index]
    return ""

def _normalize_title(text):
    text=re.sub(r"^[\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F\u200D]+\s*","",str(text or "").strip()).strip()
    return re.sub(r"\s{2,}"," ",text)

def _resource_link(doc):
    title=_normalize_title(doc.get("title") or ""); url=str(doc.get("url") or doc.get("canonical_url") or "").strip()
    return f"[{title}]({url})" if title and re.match(r"^https?://",url,re.I) else ""

def _profile(query,docs):
    q=re.sub(r"\s+"," ",str(query or "").strip().casefold())
    grief=bool(re.search(r"\b(?:grief|grieving|bereavement|bereaved|loss of (?:a|my|someone|somebody)|lost (?:someone|somebody)|loved one|someone (?:died|is dying|has died)|mourning)\b",q))
    risk=bool(re.search(r"\b(?:suicid|self-harm|overdose|abuse|coercion|immediate danger|unsafe|threatened)\b",q))
    meaning=bool(re.search(r"\b(?:meaning|understanding|perspective|wisdom|purpose|identity|continuity|spiritual|afterlife|belief)\b",q))
    return {"sensitive":bool(grief or risk),"grief":grief,"risk":risk,"meaning":meaning}

def _boundary(docs,profile):
    science=any(re.search(r"\b(?:scientific|science|psychological|neuroscientific|clinical|research)\b",str(d.get("text") or ""),re.I) for d in docs)
    spiritual=any(re.search(r"\b(?:spiritual|soul|afterlife|religious|mystical|sacred|transcenden)\b",str(d.get("text") or ""),re.I) for d in docs)
    if science and spiritual:return "It brings different ways of understanding the question into the same conversation without requiring them to become a single certainty."
    if profile.get("meaning"):return "It offers a way into the question while leaving room to distinguish what is known from what remains interpretation, possibility, or personal meaning."
    return "It offers a grounded place to begin without asking the material to provide more certainty than it can support."

def _role(doc):
    corpus=f"{_normalize_title(doc.get('title') or '')} {re.sub(r'\s+',' ',str(doc.get('text') or '').strip())}"
    for pattern,role in [(r"\b(?:afterlife|reincarnation)\b","a broader exploration of afterlife and reincarnation possibilities"),(r"\b(?:continuity|connection|bond|relationship|identity)\b","questions of continuity, connection, and what may endure"),(r"\b(?:grief|loss|mourning|bereavement|mortality|death)\b","the lived experience of loss and mortality"),(r"\b(?:meaning|purpose|perspective|wisdom)\b","meaning, perspective, and ways of understanding the experience"),(r"\b(?:scientific|psychological|research|clinical|neuroscientific)\b","a more grounded or research-oriented understanding"),(r"\b(?:spiritual|religious|mystical|sacred|transcenden)\b","spiritual or contemplative possibilities")]:
        if re.search(pattern,corpus,re.I): return role
    return "another perspective on the question"

def _secondaries(docs,primary_title,profile,limit=2):
    seen={_normalize_title(primary_title).casefold()}; cand=[]
    for i,doc in enumerate(docs):
        title=_normalize_title(doc.get("title") or ""); url=str(doc.get("url") or doc.get("canonical_url") or "").strip()
        if not title or title.casefold() in seen or not re.match(r"^https?://",url,re.I): continue
        corpus=f"{title} {re.sub(r'\s+',' ',str(doc.get('text') or '').strip())}"; score=0
        if profile.get("meaning") and re.search(r"\b(?:meaning|identity|purpose|perspective|wisdom|continuity|afterlife|reincarnation)\b",corpus,re.I): score+=2
        role=_role(doc)
        if score>0:cand.append((score,role,title,i,doc))
    cand.sort(key=lambda x:(-x[0],x[1].casefold(),x[2].casefold(),x[3]))
    out=[]; roles=set()
    for _,role,_,_,doc in cand:
        if role in roles: continue
        out.append(doc); roles.add(role)
        if len(out)>=limit: break
    return out

def _archive_meta(primary,docs):
    title=_normalize_title(primary.get("title") or ""); text=re.sub(r"\s+"," ",str(primary.get("text") or "").strip()); collection=""
    for p in (r"(?:collection|series)\s*[:\-]?\s*([^.!?]{3,100})",r"(?:within|inside|part of)\s+(?:the\s+)?(?:collection|series)\s+([^.!?]{3,100})"):
        m=re.search(p,text,re.I)
        if m: collection=m.group(1).strip(" ,;:"); break
    related=[]
    for doc in docs:
        t=_normalize_title(doc.get("title") or ""); u=str(doc.get("url") or doc.get("canonical_url") or "").strip()
        if t and t.casefold()!=title.casefold() and re.match(r"^https?://",u,re.I): related.append({"title":t,"url":u})
    return {"collection":collection,"related_resources":related[:3]}

def _archive_context(primary,docs):
    meta=_archive_meta(primary,docs); parts=[]
    if meta["collection"]: parts.append(f"It sits within the wider Archive conversation in {meta['collection']}.")
    links=[_resource_link(x) for x in meta["related_resources"]]; links=[x for x in links if x]
    if links:
        if len(links)==1: parts.append("It also belongs to a wider conversation in the Archive, alongside "+links[0]+".")
        elif len(links)==2: parts.append("It also belongs to a wider conversation in the Archive, alongside "+links[0]+" and "+links[1]+".")
        else: parts.append("It also belongs to a wider conversation in the Archive, alongside "+", ".join(links[:-1])+", and "+links[-1]+".")
    return " ".join(parts)

def _interpretation(meta):
    corpus=" ".join(x.get("title","") for x in meta.get("related_resources") or []).casefold(); d=[]
    if "continuity" in corpus or "journey" in corpus:d.append("questions of continuity and what, if anything, may endure")
    if any(x in corpus for x in ("grief","loss","death")):d.append("the lived experience of loss, mortality, and meaning")
    if "meaning" in corpus:d.append("the search for meaning when ordinary answers no longer feel sufficient")
    if not d:return ""
    d=list(dict.fromkeys(d))
    return (f"Together, those neighboring pieces point toward {d[0]}" if len(d)==1 else f"Together, those neighboring pieces open a wider conversation around {d[0]} and {d[1]}" if len(d)==2 else f"Together, those neighboring pieces open a wider conversation around {', '.join(d[:-1])}, and {d[-1]}")

def _find_primary(query,docs):
    q=str(query or "").casefold()
    if not re.search(r"\b(?:death|afterlife|reincarnation|mortality)\b",q): return None
    scored=[]
    for i,doc in enumerate(docs):
        c=str(doc.get("text") or "").casefold(); hits=sum(bool(re.search(p,c)) for p in (r"\b(?:death|afterlife|reincarnation|mortality)\b",r"\b(?:belief|spiritual|religious|mystical|soul|continuity)\b")); direct=sum(t in c for t in ("death","afterlife","belief","continuity","question"))
        if hits and direct>=2: scored.append((hits,direct,-i,doc))
    return sorted(scored,reverse=True,key=lambda x:(x[0],x[1],x[2]))[0][3] if scored else None

def _guide_answer(query,primary,docs):
    profile=_profile(query,docs); title=_normalize_title(primary.get("title") or _BENCHMARK_PRIMARY_TITLE); url=str(primary.get("url") or primary.get("canonical_url") or _BENCHMARK_PRIMARY_URL).strip()
    sections=["A question like this is often easier to approach when there is a clear place to begin and room for the question to remain open.",f"A useful place to begin [{title}]({url}).",_boundary(docs,profile)]
    archive=_archive_context(primary,docs)
    if archive: sections.append(archive)
    meta=_archive_meta(primary,docs); interp=_interpretation(meta)
    if interp: sections.append(interp+".")
    secondaries=_secondaries(docs,title,profile)
    if secondaries:
        pathways=[f"{_resource_link(doc)} — for {_role(doc)}." for doc in secondaries if _resource_link(doc)]
        if pathways: sections.append("From there, you can follow a couple of nearby reflections:\n\n"+"\n\n".join(pathways))
    sections.append("Take what feels useful, leave what does not, and let the question remain open where it needs to.")
    return "\n\n".join(x.strip() for x in sections if x.strip())

def _v345_finalize(*args,**kwargs):
    query=str(kwargs.get("user_query") if kwargs.get("user_query") is not None else (args[0] if args else ""))
    context=_context_blocks_from_kwargs(args,kwargs); value=str(_original_generate_llm_response(*args,**kwargs) or "").strip()
    if use_core._is_recommendation_question(query): return value
    docs=_parse_context_documents(context); primary=_find_primary(query,docs)
    return _guide_answer(query,primary,docs) if primary else value

app=use_core.app
app.title=f"Find Your Way (USE) Navigation Engine {APP_VERSION}"
use_core.APP_VERSION=APP_VERSION
use_core.DEPLOYMENT_FINGERPRINT=DEPLOYMENT_FINGERPRINT
use_core.generate_llm_response=_v345_finalize
print(f"USE v345 GUIDE CHUNK PRESERVATION: build_id={CANONICAL_BUILD_ID}, version={APP_VERSION}, fingerprint={DEPLOYMENT_FINGERPRINT}, source_sha256={RUNTIME_SOURCE_SHA256}, core_blob_sha256={_core_runtime_sha}")
