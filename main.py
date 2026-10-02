# USE PRODUCTION VERSION: v487.68 — ASGI recursion repair
import hashlib
import importlib
import re
import json
from pathlib import Path
from fastapi import Request
from fastapi.responses import JSONResponse

from specialist_registry import (
    SPECIALIST_PIPE_CONTRACT_VERSION,
    registry_snapshot,
    validate_registry,
)
from relationship_contribution import (
    RELATIONSHIP_CONTRIBUTION_CONTRACT_VERSION,
    RELATIONSHIP_VOICE_POLICY,
    relationship_contract_snapshot,
    validate_relationship_contribution,
)
from relationship_adapter import RelationshipAdapter
from specialist_adapters import (
    SPECIALIST_ADAPTER_CONTRACT_VERSION,
    SpecialistAdapterRegistry,
    adapter_contract_snapshot,
    invoke_specialist,
)

_BASE_MODULE_NAME = "main_v487_28_runtime"
_base = importlib.import_module(_BASE_MODULE_NAME)
use_core = _base.use_core
_ORIGINAL_APP = _base.app
_original_guide_handle_query = use_core.handle_query
APP_VERSION = "v487.68"
DEPLOYMENT_FINGERPRINT = "USE-v487.68-asgi-recursion-repair"
CANONICAL_BUILD_ID = "USE-BUILD-v487.68-asgi-recursion-repair"
EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"
_MAIN_PATH = Path(__file__).resolve()
RUNTIME_SOURCE_SHA256 = hashlib.sha256(_MAIN_PATH.read_bytes()).hexdigest()
use_core.APP_VERSION = APP_VERSION
use_core.DEPLOYMENT_FINGERPRINT = DEPLOYMENT_FINGERPRINT
use_core.CANONICAL_BUILD_ID = CANONICAL_BUILD_ID
use_core.RUNTIME_SOURCE_SHA256 = RUNTIME_SOURCE_SHA256
use_core.EXPECTED_CORE_BLOB_SHA = EXPECTED_CORE_BLOB_SHA
if getattr(_base, "_core_runtime_sha", "") != EXPECTED_CORE_BLOB_SHA:
    raise RuntimeError("USE protected core integrity failure: protected core mismatch.")

validate_registry()
SPECIALIST_CAPABILITY_REGISTRY = registry_snapshot()
SPECIALIST_ADAPTER_REGISTRY = SpecialistAdapterRegistry()
SPECIALIST_ADAPTER_REGISTRY.register(RelationshipAdapter())
SPECIALIST_ADAPTER_DIAGNOSTICS = adapter_contract_snapshot(SPECIALIST_ADAPTER_REGISTRY)
RELATIONSHIP_CONTRIBUTION_DIAGNOSTICS = relationship_contract_snapshot()

_probe = validate_relationship_contribution({"status":"CONTRIBUTION","voice_policy":RELATIONSHIP_VOICE_POLICY,"human_response":"Sometimes the first thing worth noticing is not whether the relationship is right or wrong, but what happens between you when this particular tension appears.","interpretation":{"focus":"relational pattern"},"perspectives":[{"view":"visitor"}],"movement":{"direction":"perspective"},"canonical_candidates":[]})
if _probe["voice_policy"] != "preserve_specialist_voice":
    raise RuntimeError("USE relational voice-preservation invariant failed")

def _normalize_query(text):
    return re.sub(r"\s+", " ", str(text or "").strip().casefold().replace("’", "'").replace("‘", "'").replace("–", "-").replace("—", "-"))

def _history_text(history):
    if not history: return ""
    if isinstance(history, str): return history.strip()
    parts=[]
    for item in list(history)[-8:]:
        if isinstance(item,dict):
            role=str(item.get("role") or item.get("speaker") or "").strip(); content=str(item.get("content") or item.get("message") or item.get("text") or item.get("response") or item.get("question") or "").strip()
            if content: parts.append(f"{role}: {content}" if role else content)
        elif item is not None:
            value=str(item).strip()
            if value: parts.append(value)
    return "\n".join(parts)

_GUIDE_ROUTE_IDS=frozenset({"guide","relationship","formation","catalogue","systems_ph","safety","glossary","glyph"})
_GUIDE_ROUTE_PROMPT="""You are the private routing layer behind The Guide. Interpret the visitor's inquiry before selecting a specialist route. Distinguish presenting situation, underlying question, uncertainty, desired movement, and processing need. For lived relational exploration, route=relationship and mode=delegated_journey. Never answer the visitor and never choose a canonical resource. Return ONLY JSON with route, mode, confidence, reason, alternatives, and round1_interpretation."""
_RELATIONAL_FALLBACK=re.compile(r"\b(?:someone i care about|relationship|partner|family|friend|friendship|loved one|between us|care about)\b",re.I)
_EXP_FALLBACK=re.compile(r"\b(?:afraid|fear|worried|avoid|avoiding|hesitat|putting off|confused|unsure|feel|feeling|struggl|lonely|grief|loss|shame|guilt|uncertain)\b",re.I)

def _route_model():
    get_models=getattr(use_core,"get_live_groq_models",None); budget=getattr(use_core,"_generation_budget_profile",None)
    if not callable(get_models): return None
    try: live=list(get_models() or [])
    except Exception: return None
    pref=[]
    if callable(budget):
        for complexity in (2,3,1,4):
            try:
                m=str(budget({"complexity":complexity}).get("model") or "").strip()
                if m and m not in pref: pref.append(m)
            except Exception: pass
    for m in pref:
        if m in live: return m
    return next((m for m in live if m),None)

def _guide_capability_route(query,history=None):
    fallback={"route":"guide","mode":"direct","confidence":0.50,"reason":"no bounded specialist route established","alternatives":["guide"],"source":"deterministic-fallback","round1_interpretation":{}}
    client=getattr(use_core,"groq_client",None); model=_route_model()
    if client is None or not model:
        if _RELATIONAL_FALLBACK.search(query) and _EXP_FALLBACK.search(query): fallback.update({"route":"relationship","mode":"delegated_journey","confidence":0.70,"reason":"bounded relational fallback","source":"deterministic-relational-fallback","round1_interpretation":{"processing_need":"exploration"}})
        return fallback
    content="Visitor question:\n"+str(query).strip()+("\n\nRecent conversation context:\n"+_history_text(history) if history else "")
    try:
        kwargs={"model":model,"messages":[{"role":"system","content":_GUIDE_ROUTE_PROMPT},{"role":"user","content":content[:9000]}],"temperature":0.0,"max_completion_tokens":650,"response_format":{"type":"json_object"}}
        if model.startswith("openai/gpt-oss-"): kwargs.update({"reasoning_effort":"medium","include_reasoning":False})
        parsed=json.loads(str(client.chat.completions.create(**kwargs).choices[0].message.content or "").strip())
        if not isinstance(parsed,dict): raise ValueError("routing response was not an object")
        route=str(parsed.get("route") or "guide").strip().casefold(); mode=str(parsed.get("mode") or "direct").strip().casefold(); conf=max(0.0,min(1.0,float(parsed.get("confidence",0.0) or 0.0)))
        if route not in _GUIDE_ROUTE_IDS: route="guide"
        if mode not in {"direct","delegated_journey","lookup","clarify","safety"}: mode="direct"
        interp=parsed.get("round1_interpretation") if isinstance(parsed.get("round1_interpretation"),dict) else {}
        if route=="relationship" and mode=="direct" and str(interp.get("processing_need") or "").casefold()=="exploration": mode="delegated_journey"
        return {"route":route,"mode":mode,"confidence":conf,"reason":str(parsed.get("reason") or "")[:500],"alternatives":[str(x).strip().casefold() for x in (parsed.get("alternatives") or []) if str(x).strip().casefold() in _GUIDE_ROUTE_IDS][:3] or ["guide"],"source":"groq","model":model,"round1_interpretation":interp}
    except Exception:
        if _RELATIONAL_FALLBACK.search(query) and _EXP_FALLBACK.search(query): return {"route":"relationship","mode":"delegated_journey","confidence":0.70,"reason":"bounded relational fallback after routing-model failure","alternatives":["guide"],"source":"deterministic-relational-fallback","round1_interpretation":{"processing_need":"exploration"}}
        return fallback

def _registered_available_specialist(specialist_id):
    for capability in SPECIALIST_CAPABILITY_REGISTRY:
        if capability.specialist_id==specialist_id and capability.status=="available": return capability
    return None

def _canonical_return(body):
    session_id=str(body.get("session_id") or "").strip(); original=str(body.get("original_question") or body.get("query") or "").strip(); conversation=str(body.get("conversation") or "").strip(); action=str(body.get("journey_action") or "").strip().casefold()
    if action!="end": return {"ok":False,"version":APP_VERSION,"error_type":"relational_return_requires_closure","response":"The relational journey is still open."}
    if not original or not conversation: return {"ok":False,"version":APP_VERSION,"error_type":"relational_return_incomplete","response":"The completed relational conversation was not supplied in full."}
    vals={k:str(body.get(k) or "").strip() for k in ("thread_summary","completed_insight","perspective_delta","body_of_thought","underlying_need","desired_condition","next_horizon","journey_synthesis")}; ledger=body.get("journey_ledger") if isinstance(body.get("journey_ledger"),dict) else {}; records=body.get("fractal_records") if isinstance(body.get("fractal_records"),list) else []; rounds=body.get("round_synthesis_history") if isinstance(body.get("round_synthesis_history"),list) else []
    query="\n".join(x for x in [original,"Conversation thread: "+vals["thread_summary"],"What became clearer: "+vals["perspective_delta"],"Completed insight: "+vals["completed_insight"],"Underlying need: "+vals["underlying_need"],"Desired condition: "+vals["desired_condition"],"Living body of thought: "+vals["body_of_thought"],"Previous topic-fractal syntheses: "+json.dumps(records,ensure_ascii=False),"Round-by-round synthesis history: "+json.dumps(rounds,ensure_ascii=False),"Journey ledger: "+json.dumps(ledger,ensure_ascii=False),"Whole-journey synthesis from Seeing the Relationship: "+vals["journey_synthesis"],"Next horizon: "+vals["next_horizon"]] if x.split(": ",1)[-1].strip())[:18000]
    fetcher=getattr(use_core,"_fetch_canonical_context",None) or getattr(use_core,"fetch_canonical_context",None) or getattr(use_core,"_original_fetch_canonical_context",None); sanitizer=getattr(use_core,"_sanitize_outward_context",None)
    if not callable(fetcher): return {"ok":False,"version":APP_VERSION,"request_id":session_id,"intent":"RELATIONAL_CANONICAL_RETURN","response":"The Archive doorway could not be prepared right now.","canonical_doorway":None,"error_type":"relational_return_fetch_unavailable"}
    try:
        data=fetcher(query); ctx=str(data.get("canonical_link_context") or data.get("context_blocks") or "") if isinstance(data,dict) else ""; parser=getattr(use_core,"_parse_context_documents",None); docs=parser(ctx) if callable(parser) else []; profile=_base._inquiry_profile(query); profile["action"]="recommendation"; profile["recommendation"]=max(float(profile.get("recommendation",0.0)),0.95); outward=sanitizer(query,docs,profile) if callable(sanitizer) else docs
        primary=None; terms=[t for t in re.findall(r"[a-z0-9]+",_normalize_query(query)) if len(t)>=3 and t not in {"the","and","for","with","that","this","from","into","your","you","what","when","where","why","how","about","living","archive","guide","question"}]
        for i,doc in enumerate(outward or []):
            title=str(doc.get("title") or "").casefold(); text=str(doc.get("text") or doc.get("content") or doc.get("excerpt") or "").casefold(); url=str(doc.get("url") or doc.get("canonical_url") or "")
            if not title or not re.match(r"^https://\S+$",url,re.I): continue
            tt=set(re.findall(r"[a-z0-9]+",title)); early=set(re.findall(r"[a-z0-9]+",text[:2400])); full=set(re.findall(r"[a-z0-9]+",text)); th=sum(bool(_term_forms(t)&tt) for t in terms); eh=sum(bool(_term_forms(t)&early) for t in terms); fh=sum(bool(_term_forms(t)&full) for t in terms)
            if th>=1 or (eh>=2 and fh>=2):
                candidate=(th,eh,fh,-i,doc)
                if primary is None or candidate[:4]>primary[:4]: primary=candidate
        doc=primary[4] if primary else None; payload={"state":"complete","session_id":session_id,"perspective_delta":vals["perspective_delta"],"completed_insight":vals["completed_insight"],"next_horizon":vals["next_horizon"],"journey_synthesis":vals["journey_synthesis"],"fractal_records":records,"round_synthesis_history":rounds}
        return {"ok":True,"version":APP_VERSION,"request_id":session_id,"intent":"RELATIONAL_CANONICAL_RETURN","response":"There is a place in the Archive that may carry this new perspective further." if doc else "You have brought the conversation to a meaningful place. No doorway was close enough to offer honestly from what emerged.","display_mode":"hrn","canonical_doorway":{"title":doc["title"],"url":doc["url"]} if doc else None,"relational_journey":payload,"visitor_boundary_version":APP_VERSION}
    except Exception as exc:
        print(f"The Guide {APP_VERSION} relational closure failed safely: {exc}")
        return {"ok":False,"version":APP_VERSION,"request_id":session_id,"intent":"RELATIONAL_CANONICAL_RETURN","response":"The conversation is complete, but the Archive doorway could not be prepared right now.","canonical_doorway":None,"error_type":"relational_return_retrieval_failure"}

def _term_forms(term):
    v=str(term).casefold(); forms={v}
    if v.endswith("ies") and len(v)>4: forms.add(v[:-3]+"y")
    if v.endswith("ness") and len(v)>5: forms.add(v[:-4])
    if v.endswith("ing") and len(v)>5: forms.add(v[:-3])
    if v.endswith("ed") and len(v)>5: forms.add(v[:-2])
    if v.endswith("es") and len(v)>4: forms.add(v[:-2])
    if v.endswith("s") and len(v)>4: forms.add(v[:-1])
    return forms

async def _query_asgi(scope,receive,send):
    if scope.get("type")!="http": return await _ORIGINAL_APP(scope,receive,send)
    method=str(scope.get("method") or "").upper(); path=str(scope.get("path") or "")
    if method!="POST" or path not in {"/api/query","/"}: return await _ORIGINAL_APP(scope,receive,send)
    chunks=[]
    while True:
        msg=await receive()
        if msg.get("type")=="http.disconnect": return
        if msg.get("type")!="http.request": continue
        chunks.append(msg.get("body") or b"")
        if not msg.get("more_body",False): break
    raw_body=b"".join(chunks)
    try: body=json.loads(raw_body.decode("utf-8")) if raw_body else {}
    except Exception: body={}
    if not isinstance(body,dict): body={}
    query=str(body.get("query") or body.get("user_query") or body.get("question") or body.get("text") or body.get("input") or "").strip(); history=body.get("history") or body.get("conversation_history")
    if not query:
        sent=False
        async def replay():
            nonlocal sent
            if not sent: sent=True; return {"type":"http.request","body":raw_body,"more_body":False}
            return {"type":"http.request","body":b"","more_body":False}
        return await _ORIGINAL_APP(scope,replay,send)
    route=_guide_capability_route(query,history); rid=str(route.get("route") or "guide").casefold(); mode=str(route.get("mode") or "direct").casefold(); conf=float(route.get("confidence") or 0); cap=_registered_available_specialist(rid)
    if cap and rid=="relationship" and mode=="delegated_journey" and conf>=0.60:
        req_id="relationship-"+hashlib.sha1((query+"|"+_history_text(history)).encode("utf-8")).hexdigest()[:16]
        response={"ok":True,"version":APP_VERSION,"query":query,"intent":"RELATIONAL_HANDOFF","response":"","relational_delegation":{"state":"open","specialist":cap.public_name,"specialist_id":cap.specialist_id,"session_id":req_id,"seed_message":query,"conversation":_history_text(history),"handoff_reason":"The Guide recognized that this question may be better explored as a relationship before choosing a doorway into the Archive.","hrn_endpoint":"https://geralddaquila.com/wp-json/living-archive/v1/relational-navigator","guide_return_endpoint":"https://living-archive-backend.onrender.com/api/relational-return","return_mode":"background_gift"},"visitor_boundary_version":APP_VERSION,"request_id":req_id}
        data=json.dumps(response,ensure_ascii=False,separators=(",",":")).encode("utf-8"); headers=[(b"content-type",b"application/json; charset=utf-8"),(b"content-length",str(len(data)).encode("ascii")),(b"access-control-allow-origin",b"*")]
        await send({"type":"http.response.start","status":200,"headers":headers}); await send({"type":"http.response.body","body":data}); return
    sent=False
    async def replay2():
        nonlocal sent
        if not sent: sent=True; return {"type":"http.request","body":raw_body,"more_body":False}
        return {"type":"http.request","body":b"","more_body":False}
    return await _ORIGINAL_APP(scope,replay2,send)

async def _relational_return_route(request:Request):
    try: body=await request.json()
    except Exception: body={}
    return JSONResponse(status_code=200 if str(body.get("journey_action") or "").casefold()=="end" else 409,content=_canonical_return(body))

# The closure endpoint must be registered on the original FastAPI application.
if not any(getattr(route,"path","")=="/api/relational-return" for route in _ORIGINAL_APP.routes):
    _ORIGINAL_APP.add_api_route("/api/relational-return",_relational_return_route,methods=["POST"])

app=_query_asgi
print(f"USE {APP_VERSION} ACTIVE: fingerprint={DEPLOYMENT_FINGERPRINT}, core_sha={EXPECTED_CORE_BLOB_SHA}, relationship_contract={RELATIONSHIP_CONTRIBUTION_CONTRACT_VERSION}, voice={RELATIONSHIP_VOICE_POLICY}")
