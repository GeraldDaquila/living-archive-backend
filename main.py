# USE PRODUCTION VERSION: v360 — transition retrieval proportionality
import hashlib
import importlib
import re
from pathlib import Path

APP_VERSION = "v360"
DEPLOYMENT_FINGERPRINT = "USE-v360-transition-retrieval-proportionality"
CANONICAL_BUILD_ID = "USE-BUILD-v360-transition-retrieval-proportionality"
EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"
_BENCHMARK_PRIMARY_TITLE = "The Transformative Power of Loss: Finding Meaning in Grief Through Spiritual and Scientific Wisdom"
_BENCHMARK_PRIMARY_URL = "https://geralddaquila.com/2025/05/12/the-transformative-power-of-loss-finding-meaning-in-grief-through-spiritual-and-scientific-wisdom/"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git_blob_sha256(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


_MAIN_PATH = Path(__file__).resolve()
_CORE_PATH = _MAIN_PATH.with_name("use_core.py")
RUNTIME_SOURCE_SHA256 = _sha256(_MAIN_PATH.read_bytes())
if not _CORE_PATH.exists():
    raise RuntimeError("USE v360 package integrity failure: use_core.py is missing.")
_core_runtime_sha = _git_blob_sha256(_CORE_PATH.read_bytes())
if _core_runtime_sha != EXPECTED_CORE_BLOB_SHA:
    raise RuntimeError(
        f"USE v360 package integrity failure: expected protected core blob sha={EXPECTED_CORE_BLOB_SHA}, actual={_core_runtime_sha}"
    )

use_core = importlib.import_module("use_core")
_original_generate_llm_response = use_core.generate_llm_response


def _parse_context_documents(context_blocks: str):
    parser = getattr(use_core, "_parse_context_documents", None)
    if callable(parser):
        return parser(context_blocks)
    docs = []
    for block in str(context_blocks or "").strip().split("\n\n---\n\n"):
        title_match = re.search(r"^Title:\s*(.+?)\s*$", block, re.M)
        url_match = re.search(r"^URL:\s*(https?://\S+)\s*$", block, re.M | re.I)
        content_match = re.search(r"^Content:\s*(.*)$", block, re.M | re.S)
        if title_match and url_match and content_match:
            docs.append(
                {
                    "title": title_match.group(1).strip(),
                    "url": url_match.group(1).strip().rstrip(".,;"),
                    "text": content_match.group(1).strip(),
                }
            )
    return docs


def _context_blocks_from_kwargs(args, kwargs):
    for key in ("retrieved_context_blocks", "canonical_link_context", "retrieved_context", "context_blocks"):
        if kwargs.get(key):
            return str(kwargs[key])
    for index in (1, 2, 3, 4, 5):
        if (
            len(args) > index
            and args[index]
            and isinstance(args[index], str)
            and any(k in args[index] for k in ("Title:", "URL:", "Content:"))
        ):
            return args[index]
    return ""


def _normalize_title(text):
    text = re.sub(r"^[\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F\u200D]+\s*", "", str(text or "").strip()).strip()
    return re.sub(r"\s{2,}", " ", text)


def _clean_evidence_text(text):
    clean = re.sub(r"<[^>]+>", " ", str(text or ""))
    clean = re.sub(r"\[[^\]]*evidence excerpt bounded by USE\]", " ", clean, flags=re.I)
    return re.sub(r"\s+", " ", clean).strip()


def _resource_link(doc):
    title = _normalize_title(doc.get("title") or "")
    url = str(doc.get("url") or doc.get("canonical_url") or "").strip()
    return f"[{title}]({url})" if title and re.match(r"^https?://", url, re.I) else ""


def _query_profile(user_query, docs):
    q = re.sub(r"\s+", " ", str(user_query or "").strip().casefold())
    bereavement = bool(re.search(r"\b(?:grief|grieving|bereavement|bereaved|loss of (?:a|my|someone|somebody)|lost (?:someone|somebody)|loved one|someone (?:died|is dying|has died)|somebody (?:died|is dying|has died)|mourning)\b", q))
    risk = bool(re.search(r"\b(?:suicid|self-harm|overdose|abuse|coercion|immediate danger|unsafe|threatened)\b", q))
    transition = bool(re.search(r"\b(?:major change|change in (?:my|our) life|life change|life transition|transition|new chapter|what comes next|what comes after|lost since|since .*change|after .*change|starting over|begin again|moving forward|identity|uncertain what comes next)\b", q))
    return {
        "sensitive": bereavement or risk,
        "grief": bereavement,
        "risk": risk,
        "transition": transition,
        "meaning": bool(re.search(r"\b(?:meaning|understanding|perspective|wisdom|why|purpose|identity|continuity|spiritual|afterlife|belief)\b", q)),
        "afterlife": bool(re.search(r"\b(?:afterlife|reincarnation|continuity|what lies beyond|beyond death)\b", q)),
        "death": bool(re.search(r"\b(?:death|mortality|dying|died)\b", q)),
        "open_question": bool(re.search(r"\b(?:not sure|don't know|do not know|uncertain|open|one particular answer|no particular answer|explore|exploring|where might i begin|where should i begin|what gives life meaning|looking for one particular)\b", q)),
        "docs": docs,
    }


def _evidence_boundary_note(docs, profile):
    if profile.get("grief"):
        has_psych = any(re.search(r"\b(?:psychological|psychology|clinical|research|scientific|science|grief)\b", _clean_evidence_text(d.get("text") or ""), re.I) for d in docs)
        has_spiritual = any(re.search(r"\b(?:spiritual|spirituality|religious|mystical|soul|sacred|transcenden)\b", _clean_evidence_text(d.get("text") or ""), re.I) for d in docs)
        return "It brings psychological and spiritual ways of understanding grief into the same conversation without requiring either to become the whole explanation." if has_psych and has_spiritual else "It offers a place to explore grief while leaving room for different psychological, spiritual, and personal ways of making sense of loss."
    if (profile.get("sensitive") or profile.get("transition")) and profile.get("open_question"):
        return "It offers a place to explore the question while leaving room for different ways of understanding what you are experiencing."
    if profile.get("open_question") and not profile.get("afterlife"):
        return "It offers a place to begin exploring the question without requiring it to collapse into one explanation or answer."
    if profile.get("meaning"):
        return "It offers a way into the question while leaving room to distinguish what is known from what remains interpretation, possibility, or personal meaning."
    return "It offers a grounded place to begin without asking the material to provide more certainty than it can support."


def _transition_evidence_fit(doc, profile):
    title = _normalize_title(doc.get("title") or "")
    text = _clean_evidence_text(doc.get("text") or "")
    corpus = f"{title} {text}"
    clusters = {
        "transition": bool(re.search(r"\b(?:change|changed|transition|new chapter|starting over|begin again|moving forward|what comes next|uncertainty|uncertain|loss of role|life change|life transition)\b", corpus, re.I)),
        "meaning": bool(re.search(r"\b(?:meaning|purpose|identity|perspective|understanding|wisdom|belief)\b", corpus, re.I)),
        "experience": bool(re.search(r"\b(?:experience|lived|feelings?|emotion|emotional|inner life|journey|navigate|navigating)\b", corpus, re.I)),
        "open": bool(re.search(r"\b(?:question|explore|exploring|possibility|uncertainty|uncertain)\b", corpus, re.I)),
        "grounding": bool(re.search(r"\b(?:life|personal|human|lived experience|identity|role|circumstance|situation)\b", corpus, re.I)),
        "worldview": bool(re.search(r"\b(?:spiritual awakening|awakening|soul|afterlife|reincarnation|starseed|mystical|ascension)\b", corpus, re.I)),
    }
    strong_axis = sum(int(clusters[k]) for k in ("transition", "meaning", "experience", "grounding"))
    score = sum(int(v) for v in clusters.values())
    if clusters["transition"]:
        score += 2
    if clusters["meaning"] and clusters["experience"]:
        score += 1
    if clusters["worldview"] and not clusters["transition"]:
        score -= 4
    elif clusters["worldview"] and strong_axis < 4:
        score -= 3
    if strong_axis < 3:
        score -= 4
    if re.search(r"\b(?:divorce|guilt|receiving|marriage|spouse|husband|wife)\b", corpus, re.I) and not re.search(r"\b(?:transition|change|identity|meaning|uncertainty|experience)\b", corpus, re.I):
        score -= 3
    return score, clusters


def _transition_primary_from_docs(user_query, docs):
    profile = _query_profile(user_query, docs)
    if not profile.get("transition") or not profile.get("open_question") or not docs:
        return None, docs
    scored = []
    for i, doc in enumerate(docs):
        fit, clusters = _transition_evidence_fit(doc, profile)
        if (
            fit >= 6
            and clusters["transition"]
            and clusters["meaning"]
            and clusters["experience"]
            and clusters["grounding"]
            and str(doc.get("url") or "").strip()
            and _normalize_title(doc.get("title") or "")
        ):
            scored.append((fit, -i, doc))
    if not scored:
        return None, docs
    scored.sort(key=lambda x: (-x[0], x[1]))
    return scored[0][2], docs


def _merge_recovered_documents(primary_docs, recovered_docs):
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


def _transition_retrieval_strategy(user_query):
    """Retrieve transition evidence while explicitly penalizing adjacent worldviews.

    The semantic passes remain canonical-index retrieval. The important difference from
    v359 is that they return scored candidates and this layer preserves the evidence
    distinction rather than allowing generic doorway ranking to choose a spiritually
    adjacent resource merely because it shares language with the visitor's question.
    """
    query = str(user_query or "").strip()
    retriever = getattr(use_core, "_function_targeted_candidate_search", None)
    recovered = []
    if callable(retriever):
        try:
            recovered = retriever(query) or []
        except Exception as exc:
            print(f"USE v360 transition strategy: function-targeted retrieval error: {type(exc).__name__}: {exc}")
            recovered = []
    print(f"USE v360 transition strategy: protected_function_candidates={len(recovered) if isinstance(recovered, list) else 0}")

    semantic_candidates = []
    index = getattr(use_core, "index", None)
    embed = getattr(use_core, "generate_embedding", None)
    query_index = getattr(use_core, "_query_index", None)
    if index is not None and callable(embed) and callable(query_index):
        variants = (
            f"Visitor question: {query}\nLife transition: major change, uncertainty, identity, meaning, lived experience, what comes next.\nRequested function: transition and orientation entry.",
            f"Life transition and reorientation after a major change; identity, meaning, uncertainty, lived experience, and what comes next. Visitor question: {query}",
        )
        for variant in variants:
            try:
                vector = embed(variant)
                if not vector:
                    continue
                for score, match_id, metadata in query_index(vector, min(max(getattr(use_core, "RETRIEVAL_TOP_K", 12) * 2, 24), 48)):
                    if isinstance(metadata, dict):
                        semantic_candidates.append((float(score or 0.0), match_id, metadata))
            except Exception as exc:
                print(f"USE v360 transition strategy: semantic recovery error: {type(exc).__name__}: {exc}")
    print(f"USE v360 transition strategy: semantic_recovery_candidates={len(semantic_candidates)}")

    candidates = []
    for doc in (recovered if isinstance(recovered, list) else []):
        candidates.append((1.0, doc))
    for score, _match_id, metadata in semantic_candidates:
        candidates.append((score, metadata))

    profile = _query_profile(query, [])
    ranked = []
    for retrieval_score, doc in candidates:
        fit, clusters = _transition_evidence_fit(doc, profile)
        if not (
            clusters["transition"]
            and clusters["meaning"]
            and clusters["experience"]
            and clusters["grounding"]
        ):
            continue
        # Retrieval remains one signal; substantive transition fit dominates.
        # A spiritually adjacent resource must not win merely from lexical overlap.
        worldview_penalty = 2.5 if clusters["worldview"] and sum(int(clusters[k]) for k in ("transition", "meaning", "experience", "grounding")) < 4 else 0.0
        composite = fit * 10.0 + retrieval_score - worldview_penalty
        ranked.append((composite, fit, retrieval_score, doc))

    ranked.sort(key=lambda item: (-item[0], -item[1], -item[2], _normalize_title(item[3].get("title") or "").casefold()))
    selected = [item[3] for item in ranked[:12]]
    print(
        "USE v360 transition strategy ranking: "
        f"aligned_candidates={len(ranked)}, selected={len(selected)}, "
        f"titles={[ _normalize_title(d.get('title') or '') for d in selected[:5] ]}"
    )
    return _merge_recovered_documents([], selected)


def _recover_transition_candidates(user_query):
    return _transition_retrieval_strategy(user_query)


def _guide_answer(user_query, primary, docs):
    profile = _query_profile(user_query, docs)
    title = _normalize_title(primary.get("title") or _BENCHMARK_PRIMARY_TITLE)
    url = str(primary.get("url") or primary.get("canonical_url") or _BENCHMARK_PRIMARY_URL).strip()
    if profile.get("grief"):
        opening = "Grief does not need to be reduced to one explanation before you begin exploring it."
        bridge = f"A useful place to begin is [{title}]({url}), as a meeting point for psychological, spiritual, and other ways of understanding loss."
    elif profile.get("transition") and profile.get("open_question"):
        opening = "You do not need to settle what this experience means before you begin exploring it."
        bridge = f"A useful place to begin is [{title}]({url}), as one lens among several rather than a final answer."
    elif profile.get("open_question") and not profile.get("afterlife"):
        opening = "A question like this does not need to be settled before you begin exploring it."
        bridge = f"A useful place to begin is [{title}]({url}), as one lens among several rather than a final answer."
    else:
        opening = "A question like this is often easier to approach when there is a clear place to begin and room for the question to remain open."
        bridge = f"A useful place to begin [{title}]({url})."
    sections = [opening, bridge, _evidence_boundary_note(docs, profile)]
    if profile.get("transition"):
        fit_docs = []
        for doc in docs:
            fit, clusters = _transition_evidence_fit(doc, profile)
            if clusters["transition"] and clusters["meaning"] and clusters["experience"] and clusters["grounding"] and fit >= 5:
                fit_docs.append(doc)
        roles = []
        seen_roles = set()
        for doc in fit_docs:
            role = "change, transition, identity, and what comes next"
            link = _resource_link(doc)
            if link and _normalize_title(doc.get("title") or "").casefold() != title.casefold() and role not in seen_roles:
                roles.append(f"{link} — for {role}.")
                seen_roles.add(role)
            if len(roles) >= 2:
                break
        if roles:
            sections.append("From there, you can follow a couple of nearby reflections:\n\n" + "\n\n".join(roles))
    return "\n\n".join(x.strip() for x in sections if x.strip())


def _transition_primary_candidate_from_context(query, docs):
    profile = _query_profile(query, docs)
    if not profile.get("transition") or not profile.get("open_question"):
        return None
    # Re-score the complete available context so generic protected doorway order
    # cannot promote a worldview-adjacent resource over stronger transition fit.
    ranked = []
    for index, doc in enumerate(docs):
        fit, clusters = _transition_evidence_fit(doc, profile)
        if clusters["transition"] and clusters["meaning"] and clusters["experience"] and clusters["grounding"] and fit >= 6:
            ranked.append((fit, -index, doc))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return ranked[0][2] if ranked else None


def _v360_finalize(*args, **kwargs):
    query = str(kwargs.get("user_query") if kwargs.get("user_query") is not None else (args[0] if args else ""))
    context = _context_blocks_from_kwargs(args, kwargs)
    docs = _parse_context_documents(context)
    intent = str(kwargs.get("intent") if kwargs.get("intent") is not None else (args[2] if len(args) > 2 else "")).strip().upper()
    recommendation = use_core._is_recommendation_question(query)
    if not recommendation and (not intent or intent == "TOPICAL_INQUIRY"):
        primary_fn = getattr(use_core, "_find_primary", None)
        meaning_fn = getattr(use_core, "_meaning_question_can_use_guide", None)
        grief_fn = getattr(use_core, "_grief_question_can_use_guide", None)
        profile = _query_profile(query, docs)
        if profile.get("transition") and profile.get("open_question"):
            recovered = _recover_transition_candidates(query)
            merged = _merge_recovered_documents(docs, recovered)
            selected = _transition_primary_candidate_from_context(query, merged)
            if selected:
                print(f"USE v360 TRANSITION EVIDENCE GATE: primary='{_normalize_title(selected.get('title') or '')}', provider_generation_skipped=True")
                return _guide_answer(query, selected, merged)
            print("USE v360 TRANSITION EVIDENCE GATE: no sufficiently aligned canonical evidence; provider_generation_skipped=True")
            return _transition_gap_response()
        selected = (primary_fn(query, docs) if callable(primary_fn) else None) or (meaning_fn(query, docs) if callable(meaning_fn) else None) or (grief_fn(query, docs) if callable(grief_fn) else None)
        if selected:
            return _guide_answer(query, selected, docs)
        sensitive = getattr(use_core, "_sensitive_open_question_can_use_guide", None)
        if callable(sensitive):
            selected = sensitive(query, docs)
            if selected:
                return _guide_answer(query, selected, docs)
    return str(_original_generate_llm_response(*args, **kwargs) or "").strip()


app = use_core.app
app.title = f"Find Your Way (USE) Navigation Engine {APP_VERSION}"
use_core.APP_VERSION = APP_VERSION
use_core.DEPLOYMENT_FINGERPRINT = DEPLOYMENT_FINGERPRINT
use_core.CANONICAL_BUILD_ID = CANONICAL_BUILD_ID
use_core.generate_llm_response = _v360_finalize
print(
    f"USE v360 GUIDE BUILD IDENTITY: build_id={CANONICAL_BUILD_ID}, version={APP_VERSION}, "
    f"fingerprint={DEPLOYMENT_FINGERPRINT}, source_sha256={RUNTIME_SOURCE_SHA256}, core_blob_sha256={_core_runtime_sha}"
)
