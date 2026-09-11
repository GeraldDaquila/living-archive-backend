# USE EXPERIMENTAL VERSION: v335 — Compact Visitor Response Contract + The Guide
# Experimental branch only. Production main remains protected at v334.

import hashlib
import importlib
import os
import re
import uuid
from pathlib import Path

APP_VERSION = "v335"
DEPLOYMENT_FINGERPRINT = "USE-v335-compact-visitor-response-contract"
CANONICAL_BUILD_ID = "USE-BUILD-v335-compact-visitor-response-contract"
EXPECTED_CORE_SOURCE_SHA256 = "ecbd5181958f95baedf397f715fa30ae0192005b9a39f005fe3c0ad8a8fb7ef2"

# === CANONICAL BUILD IDENTITY (excluded from payload hash) ===
CANONICAL_BUILD_PAYLOAD_SHA256 = "PLACEHOLDER_RECOMPUTE_REQUIRED"
# === END CANONICAL BUILD IDENTITY ===


def _canonical_source_payload(source: str) -> str:
    source = source.replace("\r\n", "\n").replace("\r", "\n")
    pattern = re.compile(
        r"(?ms)^# === CANONICAL BUILD IDENTITY \(excluded from payload hash\) ===\n"
        r".*?"
        r"^# === END CANONICAL BUILD IDENTITY ===\n?"
    )
    normalized, count = pattern.subn(
        "# === CANONICAL BUILD IDENTITY (excluded from payload hash) ===\n"
        "# <CANONICAL_BUILD_IDENTITY_BLOCK>\n"
        "# === END CANONICAL BUILD IDENTITY ===\n",
        source,
        count=1,
    )
    if count != 1:
        raise RuntimeError("USE v335 build identity failure: identity block missing.")
    return normalized


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


_MAIN_PATH = Path(__file__).resolve()
_CORE_PATH = _MAIN_PATH.with_name("use_core.py")
RUNTIME_SOURCE_SHA256 = _sha256(_MAIN_PATH.read_bytes())

if not _CORE_PATH.exists():
    raise RuntimeError("USE v335 package integrity failure: use_core.py is missing.")

_core_runtime_sha = _sha256(_CORE_PATH.read_bytes())
if _core_runtime_sha != EXPECTED_CORE_SOURCE_SHA256:
    raise RuntimeError(
        "USE v335 package integrity failure: "
        f"expected core sha={EXPECTED_CORE_SOURCE_SHA256}, actual={_core_runtime_sha}"
    )

_actual_payload = _sha256(
    _canonical_source_payload(_MAIN_PATH.read_text(encoding="utf-8")).encode("utf-8")
)
if CANONICAL_BUILD_PAYLOAD_SHA256 not in {"", "PLACEHOLDER_RECOMPUTE_REQUIRED"} and _actual_payload != CANONICAL_BUILD_PAYLOAD_SHA256:
    raise RuntimeError(
        "USE v335 canonical build identity mismatch: "
        f"expected={CANONICAL_BUILD_PAYLOAD_SHA256}, actual={_actual_payload}"
    )

_saved_expected_source = os.environ.pop("USE_EXPECTED_SOURCE_SHA256", None)
try:
    use_core = importlib.import_module("use_core")
finally:
    if _saved_expected_source is not None:
        os.environ["USE_EXPECTED_SOURCE_SHA256"] = _saved_expected_source

_original_violation = use_core._v308_compassionate_voice_violation
_original_build_generation_messages = use_core._build_generation_messages
_original_clean_generation_output = use_core._clean_generation_output
_original_run_generation_attempt = use_core._run_generation_attempt
_original_run_provider_completion_recovery = use_core._run_provider_completion_recovery


def _extract_query(args, kwargs):
    query = kwargs.get("user_query")
    if query is not None:
        return str(query)
    if len(args) >= 2:
        return str(args[1])
    return ""


def _v335_compact_response_contract(user_query: str) -> str:
    """Build a small provider task contract from existing deterministic state."""
    query = re.sub(r"\s+", " ", str(user_query or "").strip().casefold())
    if not query:
        return ""

    contract = use_core._build_response_task_contract(
        user_query, "TOPICAL_INQUIRY"
    )
    mode = str(contract.get("mode") or "standard")
    presentation = use_core._response_presentation_mode(user_query)
    is_grief = bool(
        re.search(
            r"\b(?:grief|grieving|bereavement|bereaved|loss|lost|death|died|dying|loved one)\b",
            query,
        )
    )
    is_movement = use_core._movement_question_requires_canonical_next(user_query)
    structure = use_core.recognize_question_structure(user_query)
    is_contrast = structure.get("structure") == "explicit_contrast"
    is_form = bool(
        re.search(
            r"\b(?:what kind of|what type of|what form|essay|article|map|navigator|pathway|hub|index|collection|document|resource)\b",
            query,
        )
    ) and bool(re.search(r"\b(?:what|which|is|are)\b", query))
    underdetermined = use_core._question_is_underdetermined(user_query)

    shape = "answer-first"
    if is_movement:
        shape = "movement-answer-first"
    elif mode == "recommendation":
        shape = "recommendation: recognition -> primary doorway -> direct fit -> agency"
    elif is_contrast:
        shape = "contrast: state tension -> distinguish evidence -> bounded synthesis"
    elif is_form:
        shape = "structure-first: answer requested form -> doorway"
    elif underdetermined:
        shape = "open-inquiry: orient -> strongest doorway -> preserve openness"
    elif is_grief:
        shape = "gentle-orientation: stated experience -> source-grounded doorway -> agency"

    lines = [
        "[VISITOR RESPONSE CONTRACT — DO NOT REVEAL]",
        f"task={mode}; presentation={presentation}; shape={shape};",
        "Answer the visitor's question before making the resource the answer. Use supplied Content for resource fit. Preserve the visitor's terms and agency.",
    ]
    if is_grief:
        lines.append(
            "Grief-care: acknowledge the stated loss gently; describe what the source explores; do not prescribe meaning, healing, closure, transformation, purpose, hope, or any personal outcome."
        )
    if mode == "recommendation":
        lines.append(
            "Recommendation: name the adjudicated primary early; explain its direct fit from Content; include companions only when the task contract permits them."
        )
    if is_movement:
        lines.append(
            "Movement: use 'next' only when D29 validates a canonical next destination."
        )
    if is_contrast:
        lines.append(
            "Relation: synthesize only relationships established by supplied evidence; do not invent causal bridges."
        )
    return "\n".join(lines)


def _v335_build_generation_messages(*args, **kwargs):
    """Restore the existing compact v333 prompt and append only task shape."""
    messages = list(_original_build_generation_messages(*args, **kwargs))
    query = kwargs.get("user_query")
    if query is None and args:
        query = args[0]
    if not messages:
        return messages

    system_message = dict(messages[0])
    system_message["content"] = use_core.COMPACT_GENERATION_SYSTEM_PROMPT.strip()
    contract = _v335_compact_response_contract(str(query or ""))
    if contract:
        system_message["content"] += "\n\n" + contract
    messages[0] = system_message
    return messages


def _v335_clean_generation_output(*args, **kwargs):
    cleaned = _original_clean_generation_output(*args, **kwargs)
    user_query = kwargs.get("user_query")
    if user_query is None and len(args) >= 4:
        user_query = args[3]
    violation = use_core._v308_compassionate_voice_violation(
        str(user_query or ""), cleaned
    )
    if violation:
        print(
            "USE v335 final answer boundary: rejecting vulnerable-experience answer; "
            f"reason={violation}"
        )
        return ""
    return cleaned


def _v335_run_generation_attempt(*args, **kwargs):
    answer = _original_run_generation_attempt(*args, **kwargs)
    violation = use_core._v308_compassionate_voice_violation(
        _extract_query(args, kwargs), answer
    )
    if violation:
        print(
            "USE v335 generation/output boundary: rejecting vulnerable-experience answer; "
            f"reason={violation}"
        )
        return ""
    return answer


def _v335_run_provider_completion_recovery(*args, **kwargs):
    answer = _original_run_provider_completion_recovery(*args, **kwargs)
    violation = use_core._v308_compassionate_voice_violation(
        _extract_query(args, kwargs), answer
    )
    if violation:
        print(
            "USE v335 recovery/output boundary: rejecting vulnerable-experience answer; "
            f"reason={violation}"
        )
        return ""
    return answer


# The generation wrapper remains inherited. Only the provider-system-message
# seam and the existing final compassionate boundary are experimental here.
use_core._build_generation_messages = _v335_build_generation_messages
use_core._clean_generation_output = _v335_clean_generation_output
use_core._run_generation_attempt = _v335_run_generation_attempt
use_core._run_provider_completion_recovery = _v335_run_provider_completion_recovery
use_core.APP_VERSION = APP_VERSION
use_core.DEPLOYMENT_FINGERPRINT = DEPLOYMENT_FINGERPRINT
use_core.CANONICAL_BUILD_ID = CANONICAL_BUILD_ID
use_core.CANONICAL_BUILD_PAYLOAD_SHA256 = _actual_payload
use_core.RUNTIME_SOURCE_SHA256 = RUNTIME_SOURCE_SHA256
use_core.EXPECTED_RUNTIME_SOURCE_SHA256 = RUNTIME_SOURCE_SHA256
use_core.RUNTIME_BOOT_ID = uuid.uuid4().hex
use_core.RUNTIME_PROCESS_ID = os.getpid()

app = use_core.app
app.title = f"Find Your Way (USE) Navigation Engine {APP_VERSION}"

print(
    "USE v335 EXPERIMENTAL RESPONSE CONTRACT: "
    f"build_id={CANONICAL_BUILD_ID}, version={APP_VERSION}, "
    f"fingerprint={DEPLOYMENT_FINGERPRINT}, source_sha256={RUNTIME_SOURCE_SHA256}, "
    f"core_sha256={_core_runtime_sha}, payload_sha256={_actual_payload}"
)
