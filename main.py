# USE PRODUCTION VERSION: v374 — visitor-experience authority calibration
# Structural intervention: preserve protected core architecture while governing
# visitor-state / resource-frame authority before generation. Transition recovery
# remains bounded evidence recovery; it is no longer a separate answer engine.
import hashlib
import importlib
import re
from pathlib import Path

APP_VERSION = "v374"
DEPLOYMENT_FINGERPRINT = "USE-v374-visitor-experience-authority-calibration"
CANONICAL_BUILD_ID = "USE-BUILD-v374-visitor-experience-authority-calibration"
EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git_blob_sha256(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode()).hexdigest()


_MAIN_PATH = Path(__file__).resolve()
_CORE_PATH = _MAIN_PATH.with_name("use_core.py")
RUNTIME_SOURCE_SHA256 = _sha256(_MAIN_PATH.read_bytes())
if not _CORE_PATH.exists():
    raise RuntimeError("USE v374 package integrity failure: use_core.py is missing.")
_core_runtime_sha = _git_blob_sha256(_CORE_PATH.read_bytes())
if _core_runtime_sha != EXPECTED_CORE_BLOB_SHA:
    raise RuntimeError(
        f"USE v374 package integrity failure: expected protected core blob sha={EXPECTED_CORE_BLOB_SHA}, actual={_core_runtime_sha}"
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
        "sensitive": bool(re.search(r"\b(?:grief|grieving|bereavement|bereaved|loss|lost|death|died|dying|loved one|trauma|abuse|coercion|suicid|self-harm|overdose)\b", q)),
        "grief": bool(re.search(r"\b(?:grief|grieving|bereavement|bereaved|loss of (?:a|my|someone|somebody)|lost (?:someone|somebody)|loved one|mourning)\b", q)),
        "risk": bool(re.search(r"\b(?:suicid|self-harm|overdose|abuse|coercion|immediate danger|unsafe|threatened)\b", q)),
        "transition": bool(re.search(r"\b(?:major change|change in (?:my|our) life|life change|life transition|transition|new chapter|what comes next|what comes after|lost since|since .*change|after .*change|starting over|begin again|moving forward|identity|uncertain what comes next)\b", q)),
        "meaning": bool(re.search(r"\b(?:meaning|understanding|perspective|wisdom|why|purpose|identity|continuity|belief)\b", q)),
        "afterlife": bool(re.search(r"\b(?:afterlife|reincarnation|continuity|what lies beyond|beyond death)\b", q)),
        "death": bool(re.search(r"\b(?:death|mortality|dying|died)\b", q)),
        "open_question": bool(re.search(r"\b(?:not sure|don't know|do not know|uncertain|open|one particular answer|no particular answer|explore|exploring|where might i begin|where should i begin|what gives life meaning|looking for one particular)\b", q)),
        "explicit_framework": explicit_framework,
        "docs": docs,
    }


_FRAME_SIGNAL_GROUPS = {
    "worldview": (
        r"\b(?:spiritual|spirituality|religious|religion|mystical|mysticism|sacred|transcenden(?:t|ce)|soul|afterlife|reincarnation|indigenous wisdom|traditional wisdom)\b",
    ),
    "technology": (r"\b(?:artificial intelligence|\bAI\b|technology|technological)\b",),
    "esoteric": (r"\b(?:astrology|tarot|starseed|ascension|kundalini|channeling|channeled|akashic|twin flame|nonduality|manifestation)\b",),
    "political": (r"\b(?:political|capitalism|socialism|marxist|conservative|liberal ideology|political ideology)\b",),
    "therapeutic": (r"\b(?:therapy|therapeutic|clinical|psychoanalytic|CBT|diagnos(?:is|tic)|trauma framework)\b",),
    "academic": (r"\b(?:scientific|science|neuroscience|research-based|empirical|academic framework)\b",),
}


def _resource_frame_groups(doc: dict) -> set:
    title = _normalize_title(doc.get("title") or "")
    text = _clean_evidence_text(doc.get("text") or "")
    corpus = f"{title} {text}"
    groups = set()
    for group, patterns in _FRAME_SIGNAL_GROUPS.items():
        if any(re.search(pattern, corpus, re.I) for pattern in patterns):
            groups.add(group)
    return groups


def _is_specialized_framework_resource(doc: dict) -> bool:
    core_fn = getattr(use_core, "_is_specialized_framework_resource", None)
    if callable(core_fn):
        try:
            if bool(core_fn(doc)):
                return True
        except Exception:
            pass
    groups = _resource_frame_groups(doc)
    return len(groups) >= 2 or "esoteric" in groups or ("worldview" in groups and bool(
        re.search(r"\b(?:spiritual|religious|mystical|sacred|soul|afterlife|reincarnation|indigenous wisdom|traditional wisdom)\b", _normalize_title(doc.get("title") or ""), re.I)
    ))


def _requested_frame_groups(query: str) -> set:
    groups = set()
    q = str(query or "")
    for group, patterns in _FRAME_SIGNAL_GROUPS.items():
        if any(re.search(pattern, q, re.I) for pattern in patterns):
            groups.add(group)
    return groups


def _frame_neutral_generation_documents(query: str, intent: str, docs: list) -> tuple[list, bool]:
    if intent != "TOPICAL_INQUIRY":
        return docs, False
    profile = _query_profile(query, docs)
    if not profile.get("open_question"):
        return docs, False

    core_boundary = getattr(use_core, "_frame_neutral_generation_documents", None)
    bounded = False
    candidate_docs = docs
    if callable(core_boundary):
        try:
            candidate_docs, bounded = core_boundary(docs, query, intent)
        except Exception as exc:
            print(f"USE v374 frame-neutral boundary integration error: {type(exc).__name__}: {exc}")
            candidate_docs = docs

    requested_groups = _requested_frame_groups(query)
    neutral = [
        doc for doc in candidate_docs
        if (not _is_specialized_framework_resource(doc))
        or bool(_resource_frame_groups(doc) & requested_groups)
    ]
    if neutral and len(neutral) < len(candidate_docs):
        bounded = True
    if bounded and neutral:
        print(
            "USE v374 VISITOR EXPERIENCE AUTHORITY: "
            f"open_question=True, neutral_generation_documents={len(neutral)}, "
            f"excluded_framework_documents={len(candidate_docs) - len(neutral)}"
        )
        return neutral, True
    if bounded and not neutral:
        return [], True
    return candidate_docs, False


def _merge_recovered_documents(primary_docs: list, recovered_docs: list) -> list:
    merged = []
    seen = set()
    for doc in list(primary_docs or []) + list(recovered_docs or []):
        if not isinstance(doc, dict):
            continue
        title = _normalize_title(doc.get("title") or "")
        url = str(doc.get("url") or doc.get("canonical_url") or "").strip()
        key = url.casefold().rstrip("/") if url else title.casefold()
        if not title or not key or key in seen or not re.match(r"^https?://", url, re.I):
            continue
        merged.append({**doc, "title": title, "url": url, "text": _clean_evidence_text(doc.get("text") or "")})
        seen.add(key)
    return merged


def _transition_evidence_fit(doc: dict, profile: dict):
    title = _normalize_title(doc.get("title") or "")
    text = _clean_evidence_text(doc.get("text") or "")
    corpus = f"{title} {text}"
    clusters = {
        "transition": bool(re.search(r"\b(?:change|changed|transition|new chapter|starting over|begin again|moving forward|what comes next|uncertainty|uncertain|loss of role|life change|life transition|turning point|reorientation|reorient)\b", corpus, re.I)),
        "meaning": bool(re.search(r"\b(?:meaning|purpose|identity|perspective|understanding|wisdom|belief|significance|sense-making)\b", corpus, re.I)),
        "experience": bool(re.search(r"\b(?:experience|lived|feelings?|emotion|emotional|inner life|journey|navigate|navigating|felt|feel)\b", corpus, re.I)),
        "open": bool(re.search(r"\b(?:question|explore|exploring|possibility|uncertainty|uncertain|different ways|multiple ways|not one answer|no single answer|perspective|perspectives)\b", corpus, re.I)),
        "grounding": bool(re.search(r"\b(?:life|personal|human|lived experience|identity|role|circumstance|situation|relationships?|work|family)\b", corpus, re.I)),
        "worldview": bool(_is_specialized_framework_resource(doc)),
    }
    axes = sum(int(clusters[k]) for k in ("transition", "meaning", "experience", "grounding"))
    score = sum(int(v) for v in clusters.values())
    if clusters["transition"]:
        score += 2
    if clusters["meaning"] and clusters["experience"]:
        score += 1
    if clusters["open"]:
        score += 1
    if clusters["worldview"]:
        score -= 4
    if axes < 3:
        score -= 3
    return score, clusters


def _transition_retrieval_strategy(user_query: str) -> list:
    query = str(user_query or "").strip()
    profile = _query_profile(query, [])
    recovered = []
    retriever = getattr(use_core, "_function_targeted_candidate_search", None)
    if callable(retriever):
        try:
            recovered = retriever(query) or []
        except Exception as exc:
            print(f"USE v374 transition function-targeted retrieval error: {type(exc).__name__}: {exc}")
    semantic = []
    embed = getattr(use_core, "generate_embedding", None)
    query_index = getattr(use_core, "_query_index", None)
    if callable(embed) and callable(query_index):
        variants = (
            f"Visitor question: {query}\nRequested resource function: orientation entry after a major life change. Visitor axes: uncertainty, identity, meaning, lived experience, reorientation, what comes next. Open inquiry: preserve multiple possible interpretations without prescribing a worldview.",
            f"Life transition, reorientation and meaning-making after major change; identity, uncertainty, lived experience, relationships, work, family, perspective, and what comes next. Seek broad human orientation resources, not a specialized worldview unless the visitor explicitly requests one.",
            f"How people navigate major life changes, changing identities, uncertainty, purpose, relationships, work, family, and making sense of a new chapter. Open, worldview-neutral perspectives are preferred.",
        )
        for variant in variants:
            try:
                vector = embed(variant)
                if not vector:
                    continue
                for score, _, metadata in query_index(vector, min(max(getattr(use_core, "RETRIEVAL_TOP_K", 12) * 4, 48), 96)):
                    if isinstance(metadata, dict):
                        semantic.append((float(score or 0.0), metadata))
            except Exception as exc:
                print(f"USE v374 transition semantic recovery error: {type(exc).__name__}: {exc}")
    sources = []
    if isinstance(recovered, list):
        for rank, doc in enumerate(recovered[:30]):
            sources.append((1.0 + max(0, 30 - rank) * 0.005, doc, "function"))
    for rank, (score, doc) in enumerate(semantic):
        sources.append((float(score or 0.0) + max(0, 48 - rank) * 0.001, doc, "semantic"))
    ranked = []
    seen = set()
    for retrieval_score, doc, source in sources:
        if not isinstance(doc, dict):
            continue
        if _is_specialized_framework_resource(doc) and not profile.get("explicit_framework"):
            continue
        key = str(doc.get("url") or doc.get("canonical_url") or doc.get("title") or "").casefold().rstrip("/")
        if not key or key in seen:
            continue
        seen.add(key)
        fit, clusters = _transition_evidence_fit(doc, profile)
        axes = sum(int(clusters[k]) for k in ("transition", "meaning", "experience", "grounding"))
        if axes >= 3 and clusters["transition"] and clusters["open"] and fit >= 4 and not clusters["worldview"]:
            authority = fit + (7 if axes == 4 else 0) + (2 if clusters["meaning"] and clusters["experience"] else 0) + (2 if source == "function" else 0)
            ranked.append((authority, axes, retrieval_score, doc))
    ranked.sort(key=lambda x: (x[0], x[1], x[2]), reverse=True)
    return _merge_recovered_documents([], [x[3] for x in ranked[:24]])


def _rebuild_context_blocks(docs: list) -> str:
    blocks = []
    for doc in docs:
        title = _normalize_title(doc.get("title") or "")
        url = str(doc.get("url") or doc.get("canonical_url") or "").strip()
        text = _clean_evidence_text(doc.get("text") or "")
        if title and re.match(r"^https?://\S+$", url, re.I):
            blocks.append(f"Title: {title}\nURL: {url}\nContent: {text}")
    return "\n\n---\n\n".join(blocks)


def _visitor_experience_contract(query: str, docs: list, frame_neutral: bool) -> dict:
    profile = _query_profile(query, docs)
    return {
        "visitor_experience": True,
        "preserve_visitor_agency": True,
        "preserve_epistemic_opening": bool(profile.get("open_question")),
        "avoid_unrequested_framework_as_primary": bool(profile.get("open_question") and not profile.get("explicit_framework")),
        "prefer_human_orientation_before_interpretation": True,
        "prefer_smallest_useful_doorway": True,
        "frame_neutral_generation": bool(frame_neutral),
        "risk_present": bool(profile.get("risk")),
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


def _v374_finalize(*args, **kwargs):
    query = str(kwargs.get("user_query") if kwargs.get("user_query") is not None else (args[0] if args else ""))
    context = _context_blocks_from_kwargs(args, kwargs)
    intent = str(kwargs.get("intent") if kwargs.get("intent") is not None else (args[2] if len(args) > 2 else "")).strip().upper()
    recommendation = use_core._is_recommendation_question(query)

    if recommendation or intent != "TOPICAL_INQUIRY":
        return str(_original_generate_llm_response(*args, **kwargs) or "").strip()

    docs = _parse_context_documents(context)
    profile = _query_profile(query, docs)
    if profile.get("transition") and profile.get("open_question"):
        recovered = _transition_retrieval_strategy(query)
        docs = _merge_recovered_documents(docs, recovered)

    generation_docs, frame_neutral = _frame_neutral_generation_documents(query, intent, docs)
    if not generation_docs:
        unavailable = getattr(use_core, "_frame_neutral_evidence_unavailable_response", None)
        if callable(unavailable):
            return str(unavailable(query) or "").strip()
        return str(_original_generate_llm_response(*args, **kwargs) or "").strip()

    calibrated_context = _rebuild_context_blocks(generation_docs)
    contract = _visitor_experience_contract(query, generation_docs, frame_neutral)
    print(
        "USE v374 VISITOR EXPERIENCE GATE: "
        f"intent={intent}, open_question={profile.get('open_question')}, "
        f"transition_recovery={profile.get('transition')}, "
        f"frame_neutral={frame_neutral}, docs={len(generation_docs)}"
    )
    return str(_call_original_with_calibrated_context(args, kwargs, calibrated_context, contract) or "").strip()


app = use_core.app
app.title = f"Find Your Way (USE) Navigation Engine {APP_VERSION}"
use_core.APP_VERSION = APP_VERSION
use_core.DEPLOYMENT_FINGERPRINT = DEPLOYMENT_FINGERPRINT
use_core.CANONICAL_BUILD_ID = CANONICAL_BUILD_ID
use_core.RUNTIME_SOURCE_SHA256 = RUNTIME_SOURCE_SHA256
use_core.EXPECTED_CORE_BLOB_SHA = EXPECTED_CORE_BLOB_SHA
use_core.generate_llm_response = _v374_finalize
print(
    f"USE v374 GUIDE BUILD IDENTITY: build_id={CANONICAL_BUILD_ID}, version={APP_VERSION}, "
    f"fingerprint={DEPLOYMENT_FINGERPRINT}, source_sha256={RUNTIME_SOURCE_SHA256}, core_blob_sha256={_core_runtime_sha}"
)
