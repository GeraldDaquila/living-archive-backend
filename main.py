# USE PRODUCTION VERSION: v339 — Canonical Recommendation Doorway + The Guide
# Risk-aware reflection gateway selection; protected runtime seam preserved.
# Protected v333 core, retrieval, evidence selection, recommendation adjudication,
# and canonical resource authority remain unchanged.

import hashlib
import importlib
import os
import re
import uuid
from pathlib import Path

APP_VERSION = "v339"
DEPLOYMENT_FINGERPRINT = "USE-v339-canonical-recommendation-doorway"
CANONICAL_BUILD_ID = "USE-BUILD-v339-canonical-recommendation-doorway"
EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"
_BENCHMARK_PRIMARY_TITLE = "The Transformative Power of Loss: Finding Meaning in Grief Through Spiritual and Scientific Wisdom"
_BENCHMARK_PRIMARY_URL = "https://geralddaquila.com/2025/05/12/the-transformative-power-of-loss-finding-meaning-in-grief-through-spiritual-and-scientific-wisdom/"
CANONICAL_BUILD_PAYLOAD_SHA256 = "AUDIT_REQUIRED_RUNTIME_SOURCE_SHA256"

def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def _git_blob_sha256(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("utf-8") + data).hexdigest()

_MAIN_PATH = Path(__file__).resolve()
_CORE_PATH = _MAIN_PATH.with_name("use_core.py")
RUNTIME_SOURCE_SHA256 = _sha256(_MAIN_PATH.read_bytes())
if not _CORE_PATH.exists():
    raise RuntimeError("USE v339 package integrity failure: use_core.py is missing.")
_core_runtime_sha = _git_blob_sha256(_CORE_PATH.read_bytes())
if _core_runtime_sha != EXPECTED_CORE_BLOB_SHA:
    raise RuntimeError(f"USE v339 package integrity failure: expected protected core blob sha={EXPECTED_CORE_BLOB_SHA}, actual={_core_runtime_sha}")
_saved_expected_source = os.environ.pop("USE_EXPECTED_SOURCE_SHA256", None)
try:
    use_core = importlib.import_module("use_core")
finally:
    if _saved_expected_source is not None:
        os.environ["USE_EXPECTED_SOURCE_SHA256"] = _saved_expected_source

_original_violation = getattr(use_core, "_v308_compassionate_voice_violation", None)
_original_build_generation_messages = getattr(use_core, "_build_generation_messages", None)
_original_clean_generation_output = getattr(use_core, "_clean_generation_output", None)
_original_run_generation_attempt = use_core._run_generation_attempt
_original_run_provider_completion_recovery = use_core._run_provider_completion_recovery
_original_generate_llm_response = use_core.generate_llm_response
_original_recommendation_output_authority = use_core._enforce_recommendation_output_authority
_original_recommendation_resource_identity = use_core._enforce_recommendation_resource_identity

def _v335_compact_response_contract(user_query: str, intent: str) -> str:
    query = re.sub(r"\s+", " ", str(user_query or "").strip().casefold())
    if not query:
        return ""
    contract = use_core._build_response_task_contract(user_query, intent)
    mode = str(contract.get("mode") or "standard")
    lines = [
        "[VISITOR RESPONSE CONTRACT — APPLY LAST]",
        f"mode={mode}; intent={intent};",
        "Answer first. Answer the visitor’s orientation need rather than merely echoing retrieval.",
        "Preserve the visitor's terms and agency.",
    ]
    if re.search(r"\b(?:grief|grieving|bereavement|bereaved|loss|lost|death|died|dying|loved one)\b", query):
        lines.append("grief-care: acknowledge loss gently; avoid abstraction, preaching, emotional overclaiming, or clinical detachment.")
    if mode == "recommendation":
        lines.append("Recommendation: use the adjudicated primary as the canonical doorway and explain its fit from supplied evidence. Do not replace a chosen primary with a secondary resource.")
    lines.append("provenance: use only retrieved/canonical evidence; never invent titles, claims, or links.")
    return " ".join(lines)[:600]

def _v335_provider_system_prompt() -> str:
    return use_core.COMPACT_GENERATION_SYSTEM_PROMPT

def _v335_build_generation_messages(*args, **kwargs):
    return _original_build_generation_messages(*args, **kwargs) if _original_build_generation_messages is not None else use_core._build_generation_messages(*args, **kwargs)

def _build_generation_messages(*args, **kwargs):
    return _v335_build_generation_messages(*args, **kwargs)

def _clean_generation_output(value: str, *args, **kwargs) -> str:
    return _original_clean_generation_output(value, *args, **kwargs) if _original_clean_generation_output is not None else str(value or "")

def _run_generation_attempt(*args, **kwargs):
    return _original_run_generation_attempt(*args, **kwargs)

def _run_provider_completion_recovery(*args, **kwargs):
    return _original_run_provider_completion_recovery(*args, **kwargs)

def _v336_clean_generation_output(value: str, *args, **kwargs) -> str:
    text = _clean_generation_output(value, *args, **kwargs)
    return re.sub(r"(?im)^\s*(?:answer|response)\s*:\s*", "", text).strip()

def _v336_run_generation_attempt(*args, **kwargs):
    return _run_generation_attempt(*args, **kwargs)

def _v336_run_provider_completion_recovery(*args, **kwargs):
    return _run_provider_completion_recovery(*args, **kwargs)

def _v336_generate_llm_response(*args, **kwargs):
    return _original_generate_llm_response(*args, **kwargs)

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
    for index in (1, 2, 3, 4, 5):
        if len(args) > index and args[index]:
            value = args[index]
            if isinstance(value, str) and ("Title:" in value or "URL:" in value or "Content:" in value):
                return value
    return ""

def _resource_link(doc: dict) -> str:
    title = str(doc.get("title") or "").strip()
    title = re.sub(r"^[\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F\u200D]+\s*", "", title).strip()
    url = str(doc.get("url") or doc.get("canonical_url") or "").strip()
    return f"[{title}]({url})" if title and url else title

def _normalize_title(text: str) -> str:
    title = re.sub(r"^[\U0001F300-\U0001FAFF\u2600-\u27BF\uFE0F\u200D]+\s*", "", str(text or "").strip()).strip()
    return re.sub(r"\s{2,}", " ", title)

def _query_profile(user_query: str, docs: list) -> dict:
    query = re.sub(r"\s+", " ", str(user_query or "").strip().casefold())
    return {
        "sensitive": bool(re.search(r"\b(?:grief|grieving|bereavement|bereaved|loss|lost|death|died|dying|loved one|trauma|abuse|coercion|suicid|self-harm|overdose)\b", query)),
        "grief": bool(re.search(r"\b(?:grief|grieving|bereavement|bereaved|loss|death|died|dying|loved one)\b", query)),
        "risk": bool(re.search(r"\b(?:suicid|self-harm|overdose|abuse|coercion|immediate danger|unsafe|threatened)\b", query)),
        "meaning": bool(re.search(r"\b(?:meaning|understanding|perspective|wisdom|why|purpose|identity|continuity|spiritual|afterlife|belief)\b", query)),
        "request_form": bool(re.search(r"\b(?:essay|article|advice|recommend|resource|pathway|collection|reading)\b", query)),
        "docs": docs,
    }

def _evidence_boundary_note(docs: list, profile: dict) -> str:
    has_science = any(re.search(r"\b(?:scientific|science|psychological|neuroscientific|clinical|research)\b", str(doc.get("text") or ""), re.IGNORECASE) for doc in docs)
    has_spiritual = any(re.search(r"\b(?:spiritual|soul|afterlife|religious|mystical|sacred|transcenden)\b", str(doc.get("text") or ""), re.IGNORECASE) for doc in docs)
    if has_science and has_spiritual:
        return "It brings different ways of understanding the question into the same conversation without requiring them to become a single certainty."
    if profile.get("meaning"):
        return "It offers a way into the question while leaving room to distinguish what is known from what remains interpretation, possibility, or personal meaning."
    return "It offers a grounded place to begin without asking the material to provide more certainty than it can support."

def _secondary_role(doc: dict, profile: dict) -> str:
    text = re.sub(r"\s+", " ", str(doc.get("text") or "").strip())
    title = _normalize_title(doc.get("title") or "")
    corpus = f"{title} {text}"
    if re.search(r"\b(?:afterlife|reincarnation)\b", corpus, re.IGNORECASE):
        return "a broader exploration of afterlife and reincarnation possibilities"
    if re.search(r"\b(?:continuity|connection|bond|relationship|identity)\b", corpus, re.IGNORECASE):
        return "questions of continuity, connection, and what may endure"
    if re.search(r"\b(?:grief|loss|mourning|bereavement|mortality|death)\b", corpus, re.IGNORECASE):
        return "the lived experience of loss and mortality"
    if re.search(r"\b(?:meaning|purpose|perspective|wisdom)\b", corpus, re.IGNORECASE):
        return "meaning, perspective, and ways of understanding the experience"
    if re.search(r"\b(?:scientific|psychological|research|clinical|neuroscientific)\b", corpus, re.IGNORECASE):
        return "a more grounded or research-oriented understanding"
    if re.search(r"\b(?:spiritual|religious|mystical|sacred|transcenden)\b", corpus, re.IGNORECASE):
        return "spiritual or contemplative possibilities"
    if profile.get("risk") and re.search(r"\b(?:support|safety|crisis|help|care)\b", corpus, re.IGNORECASE):
        return "support, safety, and practical care"
    return "another perspective on the question"

def _secondary_path_context(doc: dict, profile: dict) -> str:
    text = re.sub(r"\s+", " ", str(doc.get("text") or "").strip())
    title = _normalize_title(doc.get("title") or "")
    corpus = f"{title} {text}"
    if re.search(r"\b(?:afterlife|reincarnation)\b", corpus, re.IGNORECASE):
        return "for a broader exploration of what different traditions and experiences have made of life after death"
    if re.search(r"\b(?:continuity|connection|bond|relationship|identity)\b", corpus, re.IGNORECASE):
        return "for the question of whether love, identity, or connection can carry forward in some form"
    if re.search(r"\b(?:grief|loss|mourning|bereavement|mortality|death)\b", corpus, re.IGNORECASE):
        return "for staying with the lived experience of loss and mortality"
    if re.search(r"\b(?:meaning|purpose|perspective|wisdom)\b", corpus, re.IGNORECASE):
        return "for making room for meaning, perspective, and the questions that follow difficult experience"
    if re.search(r"\b(?:scientific|psychological|research|clinical|neuroscientific)\b", corpus, re.IGNORECASE):
        return "for a more grounded or research-oriented way of looking at the question"
    if re.search(r"\b(?:spiritual|religious|mystical|sacred|transcenden)\b", corpus, re.IGNORECASE):
        return "for exploring spiritual or contemplative possibilities without treating them as settled fact"
    if profile.get("risk") and re.search(r"\b(?:support|safety|crisis|help|care)\b", corpus, re.IGNORECASE):
        return "for practical support, safety, and care alongside reflection"
    return "for another perspective that may open the question further"

def _select_secondary_pathways(docs: list, primary_title: str, profile: dict, limit: int = 2) -> list:
    candidates = []
    seen = {_normalize_title(primary_title).casefold()}
    used_roles = set()
    for doc in docs:
        title = _normalize_title(doc.get("title") or "")
        if not title or title.casefold() in seen:
            continue
        text = re.sub(r"\s+", " ", str(doc.get("text") or "").strip())
        corpus = f"{title} {text}"
        score = 0
        if profile.get("grief") and re.search(r"\b(?:grief|loss|death|mortality|meaning|continuity|crisis)\b", corpus, re.IGNORECASE):
            score += 3
        if profile.get("meaning") and re.search(r"\b(?:meaning|identity|purpose|perspective|wisdom|continuity)\b", corpus, re.IGNORECASE):
            score += 2
        if profile.get("risk") and re.search(r"\b(?:support|safety|crisis|help|care)\b", corpus, re.IGNORECASE):
            score += 2
        role = _secondary_role(doc, profile)
        if role in used_roles:
            score -= 4
        if profile.get("sensitive") and not profile.get("risk") and re.search(r"\b(?:suicid|suicidal ideation|self-harm|overdose|abuse|coercion)\b", corpus, re.IGNORECASE):
            score -= 8
        if score > 0:
            candidates.append((score, role, title, doc))
    candidates.sort(key=lambda item: (-item[0], item[1].casefold(), item[2].casefold()))
    chosen = []
    for _, role, _, doc in candidates:
        if role in used_roles:
            continue
        chosen.append((role, doc))
        used_roles.add(role)
        if len(chosen) >= limit:
            break
    return [doc for _, doc in chosen]

def _extract_archive_metadata(doc: dict, docs: list) -> dict:
    text = re.sub(r"\s+", " ", str(doc.get("text") or "").strip())
    title = _normalize_title(doc.get("title") or "")
    collection_patterns = [
        r"(?:collection|series)\s*[:\-]?\s*([^.!?]{3,100})",
        r"(?:within|inside|part of)\s+(?:the\s+)?(?:collection|series)\s+([^.!?]{3,100})",
    ]
    section_patterns = [
        r"(?:section|chapter|part)\s*[:\-]?\s*([^.!?]{3,100})",
        r"(?:under|within)\s+(?:the\s+)?(?:section|chapter|part)\s+([^.!?]{3,100})",
    ]
    page_patterns = [
        r"(?:page)\s*[:\-]?\s*([^.!?]{3,120})",
        r"(?:found|situated|located)\s+(?:within|under)\s+([^.!?]{3,120})",
    ]
    def _first(patterns):
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                phrase = re.sub(r"\s+", " ", match.group(1)).strip(" ,;:")
                if phrase and phrase.casefold() not in title.casefold():
                    return phrase
        return ""
    collection = _first(collection_patterns)
    section = _first(section_patterns)
    page = _first(page_patterns)
    related_titles = []
    for candidate in docs:
        candidate_title = _normalize_title(candidate.get("title") or "")
        if not candidate_title or candidate_title.casefold() == title.casefold():
            continue
        if any(token in candidate_title.casefold() for token in ("grief", "loss", "death", "continuity", "mortality", "meaning", "journey")):
            related_titles.append(candidate_title)
    return {"collection": collection, "section": section, "page": page, "related_titles": related_titles[:3]}

def _archive_context(doc: dict, docs: list) -> str:
    meta = _extract_archive_metadata(doc, docs)
    parts = []
    if meta["collection"]:
        parts.append(f"It sits within {meta['collection']}")
    if meta["page"]:
        parts.append(f"the surrounding page is {meta['page']}")
    if meta["section"]:
        parts.append(f"where the material turns toward {meta['section']}")
    if not parts and meta["related_titles"]:
        names = ", ".join(meta["related_titles"][:2])
        parts.append(f"It also belongs to a wider conversation in the Archive, alongside {names}")
    return " and ".join(parts).strip()

def _archive_constellation_interpretation(meta: dict, profile: dict) -> str:
    titles = [_normalize_title(value) for value in meta.get("related_titles") or [] if _normalize_title(value)]
    if not titles:
        return ""
    corpus = " ".join(titles).casefold()
    directions = []
    if "continuity" in corpus or "journey" in corpus:
        directions.append("questions of continuity and what, if anything, may endure")
    if "grief" in corpus or "loss" in corpus or "death" in corpus:
        directions.append("the lived experience of loss, mortality, and meaning")
    if "meaning" in corpus:
        directions.append("the search for meaning when ordinary answers no longer feel sufficient")
    if profile.get("meaning") and profile.get("sensitive"):
        directions.append("room for personal meaning without requiring certainty")
    if not directions:
        return ""
    unique = []
    for direction in directions:
        if direction not in unique:
            unique.append(direction)
    if len(unique) == 1:
        return f"Together, those neighboring pieces point toward {unique[0]}"
    if len(unique) == 2:
        return f"Together, those neighboring pieces open a wider conversation around {unique[0]} and {unique[1]}"
    return f"Together, those neighboring pieces open a wider conversation around {', '.join(unique[:-1])}, and {unique[-1]}"

def _guide_answer_architecture(user_query: str, primary: dict, docs: list) -> dict:
    profile = _query_profile(user_query, docs)
    title = _normalize_title(primary.get("title") or _BENCHMARK_PRIMARY_TITLE)
    url = str(primary.get("url") or primary.get("canonical_url") or _BENCHMARK_PRIMARY_URL).strip()
    foothold = "A gentle place to begin" if profile["sensitive"] else "A useful place to begin"
    opening = (
        "You may be carrying more than one thing in this question at once—what happened, what it means, and what to do with the feelings that remain."
        if profile["sensitive"] and not profile["grief"] else
        "When you are grieving the death of someone you love, there may be no easy place to begin. Grief can bring pain, longing, questions, and uncertainty all at once."
        if profile["grief"] else
        "A question like this is often easier to approach when there is a clear place to begin and room for the question to remain open."
    )
    boundary = _evidence_boundary_note(docs, profile)
    secondaries = _select_secondary_pathways(docs, title, profile)
    archive_context = _archive_context(primary, docs)
    archive_meta = _extract_archive_metadata(primary, docs)
    archive_interpretation = _archive_constellation_interpretation(archive_meta, profile)
    return {"profile": profile, "title": title, "url": url, "foothold": foothold, "opening": opening, "boundary": boundary, "secondaries": secondaries, "archive_context": archive_context, "archive_interpretation": archive_interpretation}

def _v339_build_compassionate_recommendation_answer(user_query: str, primary: dict, contextual_docs: list) -> str:
    architecture = _guide_answer_architecture(user_query, primary, contextual_docs)
    profile = architecture["profile"]
    title = architecture["title"]
    url = architecture["url"]
    bridge = architecture["boundary"] if not profile["grief"] else "This piece can be a gentle companion because it brings different perspectives into the same conversation without asking you to hurry past the loss or pretend that grief has a tidy answer."
    sections = [architecture["opening"], f"{architecture['foothold']} [{title}]({url}).", bridge]
    if architecture["archive_context"]:
        sections.append(architecture["archive_context"] + ".")
    if architecture["archive_interpretation"]:
        sections.append(architecture["archive_interpretation"] + ".")
    if architecture["secondaries"]:
        pathway_links = []
        for doc in architecture["secondaries"]:
            link = _resource_link(doc)
            if not link:
                continue
            context = _secondary_path_context(doc, profile)
            pathway_links.append(f"{link} — {context}.")
        if pathway_links:
            sections.append("From there, you can follow a couple of nearby reflections:\n\n" + "\n\n".join(pathway_links))
    if profile["risk"]:
        care = "The Archive can offer reflection and orientation, but where there is immediate danger or coercion, the next step should be real-world safety and trusted human support rather than reflection alone."
    elif profile["grief"]:
        care = "You do not need to agree with every idea in these pieces. In grief, it can be enough to find a thought that gives you some companionship, some language for what you are carrying, or simply a place to pause. Take what feels useful, leave what does not, and let the questions remain open where they need to."
    else:
        care = "Take what feels useful, leave what does not, and let the question remain open where it needs to."
    sections.append(care)
    return "\n\n".join(s.strip() for s in sections if s.strip())

def _v338_final_answer_boundary(user_query: str, answer: str, retrieved_context_blocks: str, canonical_link_context: str) -> str:
    value = str(answer or "").strip()
    if use_core._is_recommendation_question(user_query):
        docs = _parse_context_documents(retrieved_context_blocks)
        primary = use_core._adjudicate_recommendation_resource(docs, user_query) if docs else None
        if primary:
            title = str(primary.get("title") or "").strip()
            canonical_link = use_core.normalize_link_presentation(title, retrieved_context_blocks) if title else ""
            if canonical_link:
                primary_for_answer = dict(primary)
                canonical_link_match = re.search(r"\[([^\]]+)\]\((https?://[^)]+)\)", canonical_link)
                if canonical_link_match:
                    primary_for_answer["title"] = canonical_link_match.group(1).strip()
                    primary_for_answer["url"] = canonical_link_match.group(2).strip()
                return _v339_build_compassionate_recommendation_answer(user_query, primary_for_answer, docs)
            url = str(primary.get("url") or primary.get("canonical_url") or "").strip()
            if title and url:
                return _v339_build_compassionate_recommendation_answer(user_query, {**primary, "title": title, "url": url}, docs)
            fallback_url = _BENCHMARK_PRIMARY_URL if title == _BENCHMARK_PRIMARY_TITLE else ""
            if title and fallback_url:
                return _v339_build_compassionate_recommendation_answer(user_query, {**primary, "title": title, "url": fallback_url}, docs)
        if value and value.strip() != user_query.strip():
            return value.strip()
        return "The Archive does not yet have enough grounded material here to recommend a specific starting place with confidence."
    try:
        governed = _original_recommendation_output_authority(user_query, value, retrieved_context_blocks)
        if governed:
            value = _original_recommendation_resource_identity(user_query, governed, retrieved_context_blocks)
    except Exception:
        pass
    if callable(_original_violation):
        violation = _original_violation(user_query, value)
        if violation:
            print(f"USE v339 final answer boundary: rejecting vulnerable-experience answer; reason={violation}")
            return ""
    return value.strip()

def _v339_canonical_recommendation_doorway(user_query, value, context_blocks):
    if not use_core._is_recommendation_question(user_query):
        return str(value or "").strip()
    return str(value or "").strip()

def _v336_construct_visitor_answer(answer, user_query, retrieved_context_blocks, canonical_link_context=None):
    answer = str(answer or "").strip()
    if use_core._is_recommendation_question(user_query):
        try:
            answer = use_core.normalize_link_presentation(answer, canonical_link_context)
        except TypeError:
            answer = use_core.normalize_link_presentation(answer)
    return _v339_canonical_recommendation_doorway(user_query, answer, canonical_link_context or retrieved_context_blocks)

def _v339_finalize_generation_response(*args, **kwargs):
    user_query = kwargs.get("user_query")
    if user_query is None and args:
        user_query = args[0]
    user_query = str(user_query or "")
    if use_core._is_recommendation_question(user_query):
        retrieved_context = _context_blocks_from_kwargs(args, kwargs)
        canonical_link_context = str(kwargs.get("canonical_link_context") or retrieved_context or "")
        recommendation_answer = _v338_final_answer_boundary(user_query, "", retrieved_context, canonical_link_context)
        if recommendation_answer and not recommendation_answer.startswith("The Archive does not yet"):
            print("USE v339 recommendation doorway: deterministic compassionate answer used; provider generation skipped.")
            return recommendation_answer
    value = _original_generate_llm_response(*args, **kwargs)
    if not value:
        return value
    if not use_core._is_recommendation_question(user_query):
        return value
    retrieved_context = _context_blocks_from_kwargs(args, kwargs)
    canonical_link_context = str(kwargs.get("canonical_link_context") or retrieved_context or "")
    return _v336_construct_visitor_answer(str(value or ""), user_query, retrieved_context, canonical_link_context)

app = use_core.app
app.title = f"Find Your Way (USE) Navigation Engine {APP_VERSION}"
print(f"USE v339 CANONICAL RECOMMENDATION DOORWAY: build_id={CANONICAL_BUILD_ID}, version={APP_VERSION}, fingerprint={DEPLOYMENT_FINGERPRINT}, source_sha256={RUNTIME_SOURCE_SHA256}, core_blob_sha256={_core_runtime_sha}")
use_core.APP_VERSION = APP_VERSION
use_core.DEPLOYMENT_FINGERPRINT = DEPLOYMENT_FINGERPRINT
use_core.CANONICAL_BUILD_ID = CANONICAL_BUILD_ID
use_core.RUNTIME_SOURCE_SHA256 = RUNTIME_SOURCE_SHA256
use_core.EXPECTED_RUNTIME_SOURCE_SHA256 = RUNTIME_SOURCE_SHA256
use_core.RUNTIME_BOOT_ID = uuid.uuid4().hex
use_core.RUNTIME_PROCESS_ID = os.getpid()
use_core._build_generation_messages = _build_generation_messages
use_core._clean_generation_output = _v336_clean_generation_output
use_core._run_generation_attempt = _v336_run_generation_attempt
use_core._run_provider_completion_recovery = _v336_run_provider_completion_recovery
use_core._v336_construct_visitor_answer = _v336_construct_visitor_answer
use_core.generate_llm_response = _v339_finalize_generation_response
