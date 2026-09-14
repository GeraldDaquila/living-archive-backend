# USE PRODUCTION VERSION: v430 — risk query-handler boundary
import hashlib
import importlib
import re
from pathlib import Path

APP_VERSION = "v430"
DEPLOYMENT_FINGERPRINT = "USE-v430-risk-query-handler-boundary"
CANONICAL_BUILD_ID = "USE-BUILD-v430-risk-query-handler-boundary"
EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"

_MAIN_PATH = Path(__file__).resolve()
_CORE_PATH = _MAIN_PATH.with_name("use_core.py")
RUNTIME_SOURCE_SHA256 = hashlib.sha256(_MAIN_PATH.read_bytes()).hexdigest()
if not _CORE_PATH.exists():
    raise RuntimeError("USE v430 package integrity failure: use_core.py is missing.")
_core_bytes = _CORE_PATH.read_bytes()
_core_runtime_sha = hashlib.sha1(f"blob {len(_core_bytes)}\0".encode() + _core_bytes).hexdigest()
if _core_runtime_sha != EXPECTED_CORE_BLOB_SHA:
    raise RuntimeError(f"USE v430 package integrity failure: expected protected core blob sha={EXPECTED_CORE_BLOB_SHA}, actual={_core_runtime_sha}")

use_core = importlib.import_module("use_core")
_original_generate_llm_response = use_core.generate_llm_response
_original_fetch_canonical_context = use_core.fetch_canonical_context


def _extract_user_query(args, kwargs):
    for key in ("user_query", "query", "question"):
        value = kwargs.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return args[0].strip() if len(args) >= 1 and isinstance(args[0], str) and args[0].strip() else ""


def _query_profile(user_query: str) -> dict:
    q = re.sub(r"\s+", " ", str(user_query or "").strip().casefold())
    return {
        "loneliness": bool(re.search(r"\b(?:loneliness|lonely|alone|isolat|disconnected|belonging|connection)\b", q)),
        "meaning": bool(re.search(r"\b(?:meaning|purpose|point of life|what gives life meaning|why am i here|lost about what gives life meaning|sense of purpose)\b", q)),
        "grief": bool(re.search(r"\b(?:grief|grieving|grieve|mourning|bereaved|bereavement|death of (?:a|my|their|the) (?:loved one|partner|spouse|friend|parent|child)|lost (?:a|my|their|the) (?:loved one|partner|spouse|friend|parent|child))\b", q)),
        "risk": bool(re.search(r"\b(?:suicid|self-harm|overdose|abuse|coercion|immediate danger|unsafe|threatened)\b", q)),
        "explicit_framework": bool(re.search(r"\b(?:spiritual|spirituality|religious|religion|mystical|mysticism|afterlife|reincarnation|soul|astrology|tarot|starseed)\b", q)),
    }


def _build_risk_answer():
    return (
        "If you are thinking about killing yourself or may be in immediate danger, please treat this as something that needs human help now. "
        "Call emergency services or go to the nearest emergency department, and if you can, stay with another person while you get help. "
        "You do not need to work out the larger meaning of what you are going through before taking that next step."
    )


def _parse_context_documents(context_blocks: str):
    parser = getattr(use_core, "_parse_context_documents", None)
    if callable(parser):
        return parser(context_blocks)
    return []


def _context_blocks_from_kwargs(args, kwargs):
    for key in ("retrieved_context_blocks", "retrieved_context", "context_blocks"):
        if kwargs.get(key):
            return str(kwargs[key])
    return args[1] if len(args) >= 2 and isinstance(args[1], str) else ""


def _normalize_title(text: str) -> str:
    return re.sub(r"^[\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F\u200D]+\s*", "", str(text or "").strip()).strip()


def _role_evidence(doc: dict) -> dict:
    text = re.sub(r"\s+", " ", str(doc.get("text") or "").strip().casefold())
    title = _normalize_title(doc.get("title") or "").casefold()
    corpus = title + " " + text
    return {
        "direct_loneliness": bool(re.search(r"\b(?:loneliness|lonely|social isolation|socially isolated|feeling alone|sense of aloneness|disconnected|disconnection|lack of connection|need for connection)\b", text)),
        "belonging_connection": bool(re.search(r"\b(?:belonging|connection|connected|relationship|relationships|community|companionship|being seen|being understood|social connection)\b", corpus)),
        "lived_experience": bool(re.search(r"\b(?:experience|lived|personal|human|everyday|relationships|routine|role|journey|navigate|navigating|felt|feeling|living with)\b", text)),
        "meaning": bool(re.search(r"\b(?:meaning|purpose|wisdom|perspective|understanding|sense-making|make sense|interpretation)\b", corpus)),
        "grounded": bool(re.search(r"\b(?:science|scientific|research|psychological|clinical|neuroscientific|evidence|empirical)\b", corpus)),
        "worldview": bool(re.search(r"\b(?:spiritual|spirituality|religious|religion|mystical|mysticism|afterlife|reincarnation|soul|sacred|transcenden|starseed)\b", corpus)),
        "practical_reflection": bool(re.search(r"\b(?:reflect|reflection|notice|naming|journal|practice|grounding|orientation|practical|everyday|attention)\b", text)),
        "acute_risk": bool(re.search(r"\b(?:suicid(?:e|al|ality)|suicidal ideation|self-harm|overdose|acute crisis|crisis intervention|immediate danger)\b", corpus)),
        "title_risk": bool(re.search(r"\b(?:suicide|suicidal|self-harm|overdose|crisis intervention|acute crisis)\b", title)),
        "title_loneliness": bool(re.search(r"\b(?:loneliness|lonely|alone|belonging|connection|connected|isolation|isolated)\b", title)),
        "title_meaning": bool(re.search(r"\b(?:meaning|purpose|life|consciousness|journey|understanding|perspective|wisdom)\b", title)),
        "title_grief": bool(re.search(r"\b(?:grief|grieving|mourning|bereavement|loss|death|dying|dying well)\b", title)),
        "continuity": bool(re.search(r"\b(?:continuity|connection beyond death|afterlife|legacy|what may endure|endure|transcenden)\b", corpus)),
        "grief_lived": bool(re.search(r"\b(?:grief|grieving|mourning|loss|bereavement|bereaved|companion|comfort|sorrow|lament|heart|heartbreak)\b", corpus)),
    }


def _is_risk_related(doc: dict) -> bool:
    e = _role_evidence(doc)
    return e["acute_risk"] or e["title_risk"]

# Preserve all ordinary v429 behavior below by loading the existing implementation
# from the committed module. Only the public request boundary is wrapped here.
# v430 is intentionally narrow: explicit risk is handled before fetch/generation;
# every other query uses the exact v429 functions and behavior.

def _risk_guarded_fetch_canonical_context(user_query: str):
    if _query_profile(user_query).get("risk"):
        return {
            "intent": "RISK_ROUTING",
            "orientational_frame": {},
            "context_blocks": "",
            "canonical_link_context": "",
            "risk_route_required": True,
        }
    return _original_fetch_canonical_context(user_query)


def _v430_finalize(*args, **kwargs):
    user_query = _extract_user_query(args, kwargs)
    if _query_profile(user_query).get("risk"):
        return _build_risk_answer()
    return _original_generate_llm_response(*args, **kwargs)


app = use_core.app
app.title = f"Find Your Way (USE) Navigation Engine {APP_VERSION}"
print(f"USE v430 GUIDE BUILD IDENTITY: build_id={CANONICAL_BUILD_ID}, version={APP_VERSION}, fingerprint={DEPLOYMENT_FINGERPRINT}, source_sha256={RUNTIME_SOURCE_SHA256}, core_blob_sha256={_core_runtime_sha}")
use_core.APP_VERSION = APP_VERSION
use_core.DEPLOYMENT_FINGERPRINT = DEPLOYMENT_FINGERPRINT
use_core.CANONICAL_BUILD_ID = CANONICAL_BUILD_ID
use_core.RUNTIME_SOURCE_SHA256 = RUNTIME_SOURCE_SHA256
use_core.EXPECTED_CORE_BLOB_SHA = EXPECTED_CORE_BLOB_SHA
use_core.fetch_canonical_context = _risk_guarded_fetch_canonical_context
use_core.generate_llm_response = _v430_finalize
