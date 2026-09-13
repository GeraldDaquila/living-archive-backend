# USE PRODUCTION VERSION: v383 — direct open-transition bridge
# Structural intervention: for open transition inquiries, bypass legacy canonical
# doorway/generation selection when it would reintroduce semantically unrelated
# resources. The protected core remains unchanged.
import hashlib
import importlib
import re
from pathlib import Path

APP_VERSION = "v383"
DEPLOYMENT_FINGERPRINT = "USE-v383-direct-open-transition-bridge"
CANONICAL_BUILD_ID = "USE-BUILD-v383-direct-open-transition-bridge"
EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git_blob_sha256(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()

_MAIN_PATH = Path(__file__).resolve()
_CORE_PATH = _MAIN_PATH.with_name("use_core.py")
RUNTIME_SOURCE_SHA256 = _sha256(_MAIN_PATH.read_bytes())
if not _CORE_PATH.exists():
    raise RuntimeError("USE v383 package integrity failure: use_core.py is missing.")
_core_runtime_sha = _git_blob_sha256(_CORE_PATH.read_bytes())
if _core_runtime_sha != EXPECTED_CORE_BLOB_SHA:
    raise RuntimeError(
        f"USE v383 package integrity failure: expected protected core blob sha={EXPECTED_CORE_BLOB_SHA}, actual={_core_runtime_sha}"
    )

use_core = importlib.import_module("use_core")
_original_generate_llm_response = use_core.generate_llm_response


def _parse_context_documents(context_blocks: str):
    parser = getattr(use_core, "_parse_context_documents", None)
    if callable(parser):
        return parser(context_blocks)
    docs = []
    for block in str(context_blocks or "").strip().split("\n\n---\n\n"):
        tm = re.search(r"^Title:\s*(.+?)\s*$", block, re.M)
        um = re.search(r"^URL:\s*(https?://\S+)\s*$", block, re.M | re.I)
        cm = re.search(r"^Content:\s*(.*)$", block, re.M | re.S)
        if tm and um and cm:
            docs.append({"title": tm.group(1).strip(), "url": um.group(1).strip().rstrip(".,;"), "text": cm.group(1).strip()})
    return docs


def _context_blocks_from_kwargs(args, kwargs):
    for key in ("retrieved_context_blocks", "canonical_link_context", "retrieved_context", "context_blocks"):
        if kwargs.get(key):
            return str(kwargs[key])
    for index in (1, 2, 3, 4, 5):
        if len(args) > index and isinstance(args[index], str) and any(k in args[index] for k in ("Title:", "URL:", "Content:")):
            return args[index]
    return ""


def _normalize_title(text: str) -> str:
    return re.sub(r"\s{2,}", " ", str(text or "").strip())


def _clean_evidence_text(text: str) -> str:
    clean = re.sub(r"<[^>]+>", " ", str(text or ""))
    clean = re.sub(r"\[[^\]]*evidence excerpt bounded by USE\]", " ", clean, flags=re.I)
    return re.sub(r"\s+", " ", clean).strip()


def _query_profile(user_query: str, docs: list) -> dict:
    q = re.sub(r"\s+", " ", str(user_query or "").strip().casefold())
    explicit_framework = bool(re.search(
        r"\b(?:spiritual|spirituality|religious|religion|mystical|mysticism|afterlife|reincarnation|starseed|ascension|awakening|kundalini|soul|indigenous|traditional wisdom|ai|artificial intelligence|astrology|tarot|political|capitalism|socialism)\b",
        q,
    ))
    return {
        "transition": bool(re.search(r"\b(?:major change|change in (?:my|our) life|life change|life transition|transition|new chapter|what comes next|what comes after|lost since|since .*change|after .*change|starting over|beginning again|begin again|moving forward|identity|uncertain what comes next)\b", q)),
        "meaning": bool(re.search(r"\b(?:meaning|purpose|why am i here|what is the point|what does it all mean|make sense|understand the experience)\b", q)),
        "open_question": bool(re.search(r"\b(?:how do i make sense|what do people believe|what are the possibilities|is there more|what happens after|what if there is no|i don't know what to believe|not sure what to believe|does anyone know|can anyone know|different perspectives|many perspectives|open question|no single answer|not sure|uncertain)\b", q)),
        "explicit_framework": explicit_framework,
        "sensitive": bool(re.search(r"\b(?:grief|grieving|bereavement|bereaved|loss|lost|death|died|dying|loved one|trauma|abuse|coercion|suicid|self-harm|overdose)\b", q)),
        "risk": bool(re.search(r"\b(?:suicide|self-harm|overdose|abuse|coercion|immediate danger|unsafe|threatened)\b", q)),
    }


def _resource_frame_groups(doc: dict) -> set:
    title = _normalize_title(doc.get("title") or "").casefold()
    text = _clean_evidence_text(doc.get("text") or "").casefold()
    hay = f"{title} {text}"
    groups = set()
    if re.search(r"\b(?:spiritual|spirituality|religious|religion|mystical|mysticism|afterlife|reincarnation|starseed|ascension|awakening|kundalini|soul|indigenous|traditional wisdom|astrology|tarot)\b", hay):
        groups.add("worldview")
    if re.search(r"\b(?:political|capitalism|socialism)\b", hay):
        groups.add("political")
    return groups


def _is_specialized_framework_resource(doc: dict) -> bool:
    return bool(_resource_frame_groups(doc))


def _transition_evidence_fit(doc: dict, query: str) -> tuple[int, set]:
    title = _normalize_title(doc.get("title") or "").casefold()
    text = _clean_evidence_text(doc.get("text") or "").casefold()
    hay = f"{title} {text}"
    q = str(query or "").casefold()
    clusters = {
        "transition": bool(re.search(r"\b(?:transition|change|chapter|starting over|moving forward|uncertain|flux|reorientation|turning point|new beginning|life change)\b", hay)),
        "meaning": bool(re.search(r"\b(?:meaning|purpose|identity|sensemaking|sense-making|making sense)\b", hay)),
        "experience": bool(re.search(r"\b(?:experience|lived|personal|human|everyday|relationships|routine|role|journey|navigate|navigating)\b", hay)),
        "grounding": bool(re.search(r"\b(?:ground|grounding|practical|reflect|reflection|notice|naming|journal|practice)\b", hay)),
        "open": bool(re.search(r"\b(?:perspective|perspectives|possibilit|different views|different approaches|uncertainty|no single answer|question)\b", hay)),
        "worldview": _is_specialized_framework_resource(doc),
        "support": bool(re.search(r"\b(?:support|receive|receiving|care|cared|guilt|need|needing|help|helping)\b", hay)),
        "belief": bool(re.search(r"\b(?:belief|believe|faith|spiritual|religious|worldview)\b", hay)),
    }
    score = 0
    for key in ("transition", "meaning", "experience", "grounding", "open"):
        score += int(clusters[key])
    if re.search(r"\b(?:what comes next|major change|change in my life|life transition|new chapter|lost since|understand the experience|not sure what i believe|without being told what i should feel|without being told what i should believe)\b", q):
        if clusters["transition"] or clusters["meaning"] or clusters["experience"]:
            score += 2
    return score, clusters


def _is_query_aligned_transition_doorway(doc: dict, query: str) -> bool:
    qfit = _query_profile(query, [])
    if not qfit["transition"] or qfit["explicit_framework"]:
        return False
    score, clusters = _transition_evidence_fit(doc, query)
    if not clusters["transition"]:
        return False
    if not (clusters["experience"] or clusters["meaning"]):
        return False
    if not clusters["open"] and not qfit["meaning"]:
        return False
    if score < 10:
        return False
    return True


def _transition_doorway_score(doc: dict, query: str) -> int:
    score, clusters = _transition_evidence_fit(doc, query)
    qfit = _query_profile(query, [])
    score *= 5
    if clusters["transition"] and qfit["transition"]:
        score += 8
    if clusters["meaning"] and qfit["meaning"]:
        score += 5
    if clusters["open"] and qfit["open_question"]:
        score += 5
    if clusters["experience"]:
        score += 3
    if clusters["grounding"]:
        score += 3
    if clusters["support"] and not qfit["transition"]:
        score -= 9
    if clusters["belief"] and qfit["open_question"] and not qfit["explicit_framework"]:
        score -= 7
    if clusters["worldview"] and not qfit["explicit_framework"]:
        score -= 20
    return score


def _merge_recovered_documents(existing: list, recovered: list):
    merged = []
    seen = set()
    for doc in list(existing or []) + list(recovered or []):
        if not isinstance(doc, dict):
            continue
        key = str(doc.get("url") or doc.get("canonical_url") or doc.get("title") or "").casefold().rstrip("/")
        if not key or key in seen:
            continue
        seen.add(key)
        merged.append(doc)
    return merged


def _transition_retrieval_strategy(query: str):
    source = getattr(use_core, "_transition_retrieval_strategy", None)
    if callable(source):
        try:
            retrieved = source(query)
        except Exception:
            retrieved = []
    else:
        retrieved = []
    ranked = []
    seen = set()
    for doc in list(retrieved or []):
        if not isinstance(doc, dict):
            continue
        key = str(doc.get("url") or doc.get("canonical_url") or doc.get("title") or "").casefold().rstrip("/")
        if not key or key in seen:
            continue
        seen.add(key)
        if not _is_query_aligned_transition_doorway(doc, query):
            continue
        ranked.append((_transition_doorway_score(doc, query), doc))
    ranked.sort(key=lambda x: x[0], reverse=True)
    return [doc for _score, doc in ranked[:8]]


def _rebuild_context_blocks(docs: list) -> str:
    blocks = []
    for doc in docs:
        title = _normalize_title(doc.get("title") or "")
        url = str(doc.get("url") or doc.get("canonical_url") or "").strip()
        text = _clean_evidence_text(doc.get("text") or "")
        if title and re.match(r"^https?://\S+$", url, re.I):
            blocks.append(f"Title: {title}\nURL: {url}\nContent: {text}")
    return "\n\n---\n\n".join(blocks)


def _visitor_experience_contract(query: str, docs: list) -> dict:
    profile = _query_profile(query, docs)
    return {
        "visitor_experience": True,
        "preserve_visitor_agency": True,
        "preserve_epistemic_opening": bool(profile.get("open_question")),
        "avoid_unrequested_framework_as_primary": bool(profile.get("open_question") and not profile.get("explicit_framework")),
        "prefer_human_orientation_before_interpretation": True,
        "prefer_smallest_useful_doorway": True,
        "frame_neutral_generation": True,
        "risk_present": bool(profile.get("risk")),
        "allow_interpretive_evidence_as_non_authoritative": bool(profile.get("open_question") and not profile.get("explicit_framework")),
    }


def _call_original_with_calibrated_context(args, kwargs, context: str, contract: dict):
    call_kwargs = dict(kwargs)
    call_args = list(args)
    if "retrieved_context_blocks" in call_kwargs:
        call_kwargs["retrieved_context_blocks"] = context
    elif len(call_args) > 1:
        call_args[1] = context
    else:
        call_kwargs["retrieved_context_blocks"] = context
    if "canonical_link_context" in call_kwargs:
        call_kwargs["canonical_link_context"] = context
    elif len(call_args) > 4 and isinstance(call_args[4], str):
        call_args[4] = context
    if "orientational_frame" in call_kwargs and isinstance(call_kwargs["orientational_frame"], dict):
        frame = dict(call_kwargs["orientational_frame"])
        frame["visitor_experience_contract"] = contract
        call_kwargs["orientational_frame"] = frame
    elif len(call_args) > 3 and isinstance(call_args[3], dict):
        frame = dict(call_args[3])
        frame["visitor_experience_contract"] = contract
        call_args[3] = frame
    return _original_generate_llm_response(*call_args, **call_kwargs)


def _frame_neutral_response(query: str, docs: list):
    unavailable = getattr(use_core, "_frame_neutral_evidence_unavailable_response", None)
    if callable(unavailable):
        return unavailable(query)
    return {
        "response": "The Guide could not identify a sufficiently aligned canonical doorway for this transition question yet.",
        "resources": [],
    }


def _v383_finalize(*args, **kwargs):
    user_query = str(kwargs.get("user_query") or (args[0] if args else "") or "")
    intent = str(kwargs.get("intent") or (args[2] if len(args) > 2 else "") or "")
    raw_context = _context_blocks_from_kwargs(args, kwargs)
    docs = _parse_context_documents(raw_context)
    if not user_query or intent != "TOPICAL_INQUIRY":
        return _original_generate_llm_response(*args, **kwargs)

    profile = _query_profile(user_query, docs)
    is_open_transition = bool(profile.get("transition") and profile.get("open_question") and not profile.get("explicit_framework"))
    if is_open_transition:
        recovered = _transition_retrieval_strategy(user_query)
        existing_aligned = [doc for doc in docs if _is_query_aligned_transition_doorway(doc, user_query)]
        aligned = _merge_recovered_documents(existing_aligned, recovered)
        if not aligned:
            return _frame_neutral_response(user_query, docs)
        calibrated_docs = sorted(aligned, key=lambda doc: _transition_doorway_score(doc, user_query), reverse=True)[:6]
        calibrated_context = _rebuild_context_blocks(calibrated_docs)
        contract = _visitor_experience_contract(user_query, calibrated_docs)
        # Crucially, pass only transition-fit evidence into the protected generator.
        # No broad raw context, frame-neutral fallback, or legacy candidate set is supplied.
        return _call_original_with_calibrated_context(args, kwargs, calibrated_context, contract)

    if profile.get("explicit_framework"):
        return _original_generate_llm_response(*args, **kwargs)

    neutral_docs = [doc for doc in docs if not _is_specialized_framework_resource(doc)]
    if not neutral_docs:
        return _frame_neutral_response(user_query, docs)
    calibrated_context = _rebuild_context_blocks(neutral_docs[:8])
    contract = _visitor_experience_contract(user_query, neutral_docs[:8])
    return _call_original_with_calibrated_context(args, kwargs, calibrated_context, contract)


app = use_core.app
app.title = f"Find Your Way (USE) Navigation Engine {APP_VERSION}"
use_core.APP_VERSION = APP_VERSION
use_core.DEPLOYMENT_FINGERPRINT = DEPLOYMENT_FINGERPRINT
use_core.CANONICAL_BUILD_ID = CANONICAL_BUILD_ID
use_core.RUNTIME_SOURCE_SHA256 = RUNTIME_SOURCE_SHA256
use_core.EXPECTED_CORE_BLOB_SHA = EXPECTED_CORE_BLOB_SHA
use_core.generate_llm_response = _v383_finalize
print(
    f"USE v383 GUIDE BUILD IDENTITY: build_id={CANONICAL_BUILD_ID}, version={APP_VERSION}, "
    f"fingerprint={DEPLOYMENT_FINGERPRINT}, source_sha256={RUNTIME_SOURCE_SHA256}, core_blob_sha256={_core_runtime_sha}"
)
