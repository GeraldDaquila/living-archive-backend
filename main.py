# USE PRODUCTION VERSION: v392 — adjudicated primary doorway recovery
import hashlib
import importlib
import re
from pathlib import Path

APP_VERSION = "v392"
DEPLOYMENT_FINGERPRINT = "USE-v392-adjudicated-primary-doorway-recovery"
CANONICAL_BUILD_ID = "USE-BUILD-v392-adjudicated-primary-doorway-recovery"
EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git_blob_sha256(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


_MAIN_PATH = Path(__file__).resolve()
_CORE_PATH = _MAIN_PATH.with_name("use_core.py")
RUNTIME_SOURCE_SHA256 = _sha256(_MAIN_PATH.read_bytes())
if not _CORE_PATH.exists():
    raise RuntimeError("USE v392 package integrity failure: use_core.py is missing.")
_core_runtime_sha = _git_blob_sha256(_CORE_PATH.read_bytes())
if _core_runtime_sha != EXPECTED_CORE_BLOB_SHA:
    raise RuntimeError(
        f"USE v392 package integrity failure: expected protected core blob sha={EXPECTED_CORE_BLOB_SHA}, actual={_core_runtime_sha}"
    )

use_core = importlib.import_module("use_core")
_original_generate_llm_response = use_core.generate_llm_response


def _parse_context_documents(context_blocks: str):
    parser = getattr(use_core, "context_blocks_to_documents", None)
    if callable(parser):
        try:
            parsed = parser(str(context_blocks or ""))
            if isinstance(parsed, list):
                return parsed
        except Exception:
            pass
    docs = []
    for block in str(context_blocks or "").strip().split("\n\n---\n\n"):
        tm = re.search(r"^Title:\s*(.+?)\s*$", block, re.M)
        um = re.search(r"^URL:\s*(https?://\S+)\s*$", block, re.M | re.I)
        cm = re.search(r"^Content:\s*(.*)$", block, re.M | re.S)
        if tm and um and cm:
            docs.append(
                {
                    "title": tm.group(1).strip(),
                    "url": um.group(1).strip().rstrip(".,;"),
                    "text": cm.group(1).strip(),
                }
            )
    return docs


def _safe_documents(value) -> list:
    return value if isinstance(value, list) else []


def _context_layers(args, kwargs):
    generation = ""
    source = "none"
    for key in ("retrieved_context_blocks", "retrieved_context", "context_blocks"):
        if kwargs.get(key):
            generation = str(kwargs[key])
            source = key
            break
    if not generation:
        for index in (1, 4, 5):
            if (
                len(args) > index
                and isinstance(args[index], str)
                and any(k in args[index] for k in ("Title:", "URL:", "Content:"))
            ):
                generation = args[index]
                source = f"args[{index}]"
                break

    canonical = str(kwargs.get("canonical_link_context") or "")
    protected = _safe_documents(
        kwargs.get("protected_documents")
        or kwargs.get("question_authority_protected_docs")
        or kwargs.get("generation_authority_protected_docs")
    )
    return source, generation, canonical, protected


def _normalize_title(text: str) -> str:
    return re.sub(r"\s{2,}", " ", str(text or "").strip())


def _canonical_url(doc: dict) -> str:
    return str(doc.get("url") or doc.get("canonical_url") or "").strip()


def _clean_evidence_text(text: str) -> str:
    clean = re.sub(r"<[^>]+>", " ", str(text or ""))
    clean = re.sub(r"\[[^\]]*evidence excerpt bounded by USE\]", " ", clean, flags=re.I)
    return re.sub(r"\s+", " ", clean).strip()


def _resource_identity(doc: dict) -> str:
    url = _canonical_url(doc).rstrip("/").casefold()
    if url:
        return f"url:{url}"
    title = _normalize_title(doc.get("title") or "").casefold()
    return f"title:{title}" if title else ""


def _identity_index(docs: list) -> dict:
    index = {}
    for doc in docs:
        if not isinstance(doc, dict):
            continue
        title_key = _normalize_title(doc.get("title") or "").casefold()
        url_key = _canonical_url(doc).rstrip("/").casefold()
        if url_key:
            index.setdefault(("url", url_key), doc)
        if title_key:
            index.setdefault(("title", title_key), doc)
    return index


def _find_canonical_identity(primary: dict, canonical_docs: list) -> dict | None:
    """Restore exact canonical identity for an upstream-selected primary.

    The protected question-specific authority already selected the resource.
    This function never re-ranks or rejects that selection; canonical context is
    used only to recover authoritative URL/title/content identity.
    """
    if not isinstance(primary, dict):
        return None
    canonical_index = _identity_index(canonical_docs)
    url_key = _canonical_url(primary).rstrip("/").casefold()
    title_key = _normalize_title(primary.get("title") or "").casefold()

    canonical = canonical_index.get(("url", url_key)) if url_key else None
    if canonical is None and title_key:
        canonical = canonical_index.get(("title", title_key))

    if canonical is None:
        if re.match(r"^https?://\S+$", _canonical_url(primary), re.I) and _normalize_title(primary.get("title") or ""):
            return dict(primary)
        return None

    merged = dict(canonical)
    for key, value in primary.items():
        if value not in (None, ""):
            merged[key] = value
    merged["url"] = _canonical_url(canonical) or _canonical_url(primary)
    merged["title"] = _normalize_title(canonical.get("title") or primary.get("title") or "")
    if not re.match(r"^https?://\S+$", merged["url"], re.I):
        return None
    if not merged["title"]:
        return None
    return merged


def _select_adjudicated_primary(protected_docs: list, canonical_docs: list) -> dict | None:
    """Use the first valid protected question-specific resource as doorway authority."""
    canonical_index = _identity_index(canonical_docs)
    for protected in protected_docs:
        if not isinstance(protected, dict):
            continue
        # Protected order is adjudicated upstream. Do not score or reorder it here.
        recovered = _find_canonical_identity(protected, canonical_docs)
        if recovered:
            return recovered

        # Safe fallback when canonical context is unavailable: only the protected
        # document itself may provide the identity; no other retrieved document may.
        title = _normalize_title(protected.get("title") or "")
        url = _canonical_url(protected)
        if title and re.match(r"^https?://\S+$", url, re.I):
            return dict(protected)

    return None


def _query_profile(user_query: str) -> dict:
    q = re.sub(r"\s+", " ", str(user_query or "").strip().casefold())
    return {
        "transition": bool(
            re.search(
                r"\b(?:major change|change in (?:my|our) life|life change|life transition|transition|new chapter|what comes next|what comes after|lost since|since .*change|after .*change|starting over|beginning again|begin again|moving forward|identity|uncertain what comes next)\b",
                q,
            )
        ),
        "meaning": bool(
            re.search(
                r"\b(?:meaning|purpose|why am i here|what is the point|what does it all mean|make sense|understand the experience)\b",
                q,
            )
        ),
        "open_question": bool(
            re.search(
                r"\b(?:how do i make sense|what do people believe|what are the possibilities|is there more|what happens after|what if there is no|i don't know what to believe|not sure what to believe|does anyone know|can anyone know|different perspectives|many perspectives|open question|no single answer|not sure|uncertain)\b",
                q,
            )
        ),
        "explicit_framework": bool(
            re.search(
                r"\b(?:spiritual|spirituality|religious|religion|mystical|mysticism|afterlife|reincarnation|starseed|ascension|awakening|kundalini|soul|indigenous|traditional wisdom|ai|artificial intelligence|astrology|tarot|political|capitalism|socialism)\b",
                q,
            )
        ),
    }


def _direct_open_transition_response(primary: dict | None) -> str:
    if not primary:
        return "<visitor_answer>A possible place to begin is with the transition itself: what changed, what feels uncertain now, and what remains open rather than already decided. The material available here does not establish one particular belief about what your experience means, so the question can remain open while you explore it.</visitor_answer>"

    title = _normalize_title(primary.get("title") or "")
    url = _canonical_url(primary)
    if not title or not re.match(r"^https?://\S+$", url, re.I):
        return "<visitor_answer>A possible place to begin is with the transition itself: what changed, what feels uncertain now, and what remains open.</visitor_answer>"

    return (
        "<visitor_answer>"
        "A possible place to begin is with the transition itself: a major change can leave what comes next genuinely open, "
        "especially while you are still finding your own language for what the experience means. The material surfaced here "
        "can offer a lens for that inquiry without requiring you to adopt a particular belief.\n\n"
        f"One useful doorway is [{title}]({url}). Because this doorway carries its own framing, you do not need to take that framing "
        "as the answer to what your experience means."
        "</visitor_answer>"
    )


def _v392_finalize(*args, **kwargs):
    user_query = str(kwargs.get("user_query") or (args[0] if args else "") or "")
    intent = str(kwargs.get("intent") or (args[2] if len(args) > 2 else "") or "")
    source, generation_context, canonical_context, protected_docs = _context_layers(args, kwargs)

    if not user_query or intent != "TOPICAL_INQUIRY":
        return _original_generate_llm_response(*args, **kwargs)

    profile = _query_profile(user_query)
    if not (profile["transition"] and profile["open_question"] and not profile["explicit_framework"]):
        return _original_generate_llm_response(*args, **kwargs)

    canonical_docs = _parse_context_documents(canonical_context)
    primary = _select_adjudicated_primary(protected_docs, canonical_docs)

    print(
        "USE v392 transition doorway: "
        f"source={source}, protected_docs={len(protected_docs)}, canonical_docs={len(canonical_docs)}, "
        f"generation_context={'present' if generation_context else 'absent'}, "
        f"selected={_normalize_title(primary.get('title') or '') if primary else 'NONE'}"
    )
    return _direct_open_transition_response(primary)


app = use_core.app
app.title = f"Find Your Way (USE) Navigation Engine {APP_VERSION}"
use_core.APP_VERSION = APP_VERSION
use_core.DEPLOYMENT_FINGERPRINT = DEPLOYMENT_FINGERPRINT
use_core.CANONICAL_BUILD_ID = CANONICAL_BUILD_ID
use_core.RUNTIME_SOURCE_SHA256 = RUNTIME_SOURCE_SHA256
use_core.EXPECTED_CORE_BLOB_SHA = EXPECTED_CORE_BLOB_SHA
use_core.generate_llm_response = _v392_finalize
print(
    f"USE v392 GUIDE BUILD IDENTITY: build_id={CANONICAL_BUILD_ID}, version={APP_VERSION}, "
    f"fingerprint={DEPLOYMENT_FINGERPRINT}, source_sha256={RUNTIME_SOURCE_SHA256}, "
    f"core_blob_sha256={_core_runtime_sha}"
)