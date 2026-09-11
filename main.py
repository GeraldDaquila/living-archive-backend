# USE PRODUCTION VERSION: v334 — Compassionate Recommendation Boundary + The Guide
# Sole visitor-facing entrypoint: main.py remains the Render/Uvicorn production doorway.
# The intact v333 engine is preserved as use_core.py from the existing canonical v333 Git blob.
# v334 changes the vulnerable-experience generation/output boundary and binds release identity here.

import hashlib
import importlib
import os
import re
import uuid
from pathlib import Path

APP_VERSION = "v334"
DEPLOYMENT_FINGERPRINT = "USE-v334-compassionate-recommendation-boundary"
CANONICAL_BUILD_ID = "USE-BUILD-v334-compassionate-recommendation-boundary"
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
        raise RuntimeError("USE v334 build identity failure: identity block missing.")
    return normalized


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


_MAIN_PATH = Path(__file__).resolve()
_CORE_PATH = _MAIN_PATH.with_name("use_core.py")
RUNTIME_SOURCE_SHA256 = _sha256(_MAIN_PATH.read_bytes())

if not _CORE_PATH.exists():
    raise RuntimeError("USE v334 package integrity failure: use_core.py is missing.")

_core_runtime_sha = _sha256(_CORE_PATH.read_bytes())
if _core_runtime_sha != EXPECTED_CORE_SOURCE_SHA256:
    raise RuntimeError(
        "USE v334 package integrity failure: "
        f"expected core sha={EXPECTED_CORE_SOURCE_SHA256}, actual={_core_runtime_sha}"
    )

_actual_payload = _sha256(
    _canonical_source_payload(_MAIN_PATH.read_text(encoding="utf-8")).encode("utf-8")
)
if CANONICAL_BUILD_PAYLOAD_SHA256 not in {"", "PLACEHOLDER_RECOMPUTE_REQUIRED"} and _actual_payload != CANONICAL_BUILD_PAYLOAD_SHA256:
    raise RuntimeError(
        "USE v334 canonical build identity mismatch: "
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


def _v334_compassionate_voice_violation(user_query: str, answer: str) -> str:
    """Reject vulnerable-experience output that converts source framing into visitor benefit."""
    query = str(user_query or "").casefold()
    vulnerable = (
        "grief", "grieving", "bereavement", "bereaved", "death of", "died",
        "loss of a loved one", "lost my", "lost her", "lost his", "lost their",
        "mourning", "mourning the", "funeral",
    )
    if not any(term in query for term in vulnerable):
        return _original_violation(user_query, answer)

    text = re.sub(r"\s+", " ", str(answer or "")).strip().casefold()
    if not text:
        return ""

    patterns = (
        (r"\byou\s+(?:should|need to|must|have to)\b", "prescriptive second-person language"),
        (r"\byou\s+(?:need|have)\s+to\s+(?:find|discover|create)\s+(?:meaning|purpose|closure|wisdom)\b", "prescribed meaning/closure"),
        (r"\byou\s+(?:will|can)\s+(?:grow|heal|transform|become stronger)\b", "asserted personal outcome"),
        (r"\byour\s+(?:grief|loss|suffering|pain)\s+(?:is|will be)\s+(?:a\s+)?(?:transformative|healing|purposeful|necessary|gift|lesson)\b", "asserted transformative meaning"),
        (r"\byour\s+(?:grief|loss|suffering|pain)\s+(?:will|can)\s+(?:transform|heal|make you stronger|give you meaning)\b", "asserted transformative outcome"),
        (r"\b(?:find|discover|create)\s+(?:meaning|purpose|closure|wisdom)\s+(?:in|from)\s+your\s+(?:grief|loss|pain)\b", "prescribed meaning-making"),
        (r"\b(?:offering|offers|providing|provides|bringing|brings|giving|gives)\s+(?:comfort|healing|peace|closure|meaning|purpose|hope)\b", "asserted visitor benefit"),
        (r"\b(?:helps?|helping|supports?|supporting)\s+(?:those|people|someone|a person|the reader|you)\s+(?:who are|who is|with)?\s*(?:grieving|grief|bereaved|bereavement|loss)\b", "asserted visitor benefit"),
        (r"\b(?:comfort|healing|peace|closure|meaning|purpose|hope)\s+(?:for|to)\s+(?:those|people|someone|the reader|you)\s+(?:who are|who is|with)?\s*(?:grieving|grief|bereaved|bereavement|loss)\b", "asserted visitor benefit"),
    )
    for pattern, reason in patterns:
        if re.search(pattern, text):
            return reason
    return ""


def _v334_generation_instruction(user_query: str) -> str:
    """Strengthen the positive generation instruction for vulnerable grief/loss questions."""
    query = str(user_query or "").casefold()
    vulnerable = (
        "grief", "grieving", "bereavement", "bereaved", "death of", "died",
        "loss of a loved one", "lost my", "lost her", "lost his", "lost their",
        "mourning", "mourning the", "funeral",
    )
    if not any(term in query for term in vulnerable):
        return ""
    return (
        "[V334 COMPASSIONATE RECOMMENDATION BOUNDARY — DO NOT REVEAL]: "
        "This visitor is asking from a stated experience of grief, bereavement, death, or loss. "
        "Answer the recommendation request directly and gently. Name the adjudicated primary resource early. "
        "Describe only what that resource's supplied Content explores or frames. "
        "Do not state or imply that the resource offers, provides, brings, gives, or promises comfort, healing, peace, closure, meaning, purpose, hope, or another benefit to grieving people or to this visitor. "
        "Do not convert a source's description of the afterlife, soul, continuity, or any other spiritual claim into a conclusion about what the visitor will experience or receive. "
        "Attribute specialized or spiritual framing to the resource itself: use forms such as 'the piece explores', 'the book presents', or 'the material describes'. "
        "Explain why the resource fits the literal question from its supplied Content, not by asserting a visitor outcome. "
        "Preserve the visitor's sovereignty and do not tell them what their grief means, should become, or should teach them."
    )


def _v334_build_generation_messages(*args, **kwargs):
    """Inject v334 positive construction at the actual provider-message seam."""
    messages = _original_build_generation_messages(*args, **kwargs)
    query = kwargs.get("user_query")
    if query is None and len(args) >= 1:
        query = args[0]
    instruction = _v334_generation_instruction(str(query or ""))
    if instruction and messages:
        system_message = dict(messages[0])
        system_message["content"] = str(system_message.get("content", "")) + "\n\n" + instruction
        messages = [system_message, *messages[1:]]
    return messages


def _v334_clean_generation_output(*args, **kwargs):
    """Apply the v334 compassionate boundary at the final cleaned-answer seam."""
    cleaned = _original_clean_generation_output(*args, **kwargs)
    user_query = kwargs.get("user_query")
    if user_query is None and len(args) >= 4:
        user_query = args[3]
    if user_query is None:
        user_query = ""
    violation = _v334_compassionate_voice_violation(str(user_query), cleaned)
    if not violation:
        return cleaned
    print(
        "USE v334 final answer boundary: rejecting cleaned vulnerable-experience answer; "
        f"reason={violation}"
    )
    return ""


def _apply_v334_generation_boundary(user_query: str, answer: str) -> str:
    """Reject vulnerable-experience generation before it can reach the visitor."""
    violation = _v334_compassionate_voice_violation(user_query, answer)
    if not violation:
        return answer
    print(
        "USE v334 generation/output boundary: rejecting vulnerable-experience answer; "
        f"reason={violation}"
    )
    return ""


_original_run_generation_attempt = use_core._run_generation_attempt
_original_run_provider_completion_recovery = use_core._run_provider_completion_recovery


def _extract_query_from_generation_args(args, kwargs):
    query = kwargs.get("user_query")
    if query is not None:
        return str(query)
    if len(args) >= 2:
        return str(args[1])
    return ""


def _v334_run_generation_attempt(*args, **kwargs):
    answer = _original_run_generation_attempt(*args, **kwargs)
    user_query = _extract_query_from_generation_args(args, kwargs)
    return _apply_v334_generation_boundary(user_query, answer)


def _v334_run_provider_completion_recovery(*args, **kwargs):
    answer = _original_run_provider_completion_recovery(*args, **kwargs)
    user_query = _extract_query_from_generation_args(args, kwargs)
    return _apply_v334_generation_boundary(user_query, answer)


use_core._build_generation_messages = _v334_build_generation_messages
use_core._clean_generation_output = _v334_clean_generation_output
use_core._v308_compassionate_voice_violation = _v334_compassionate_voice_violation
use_core._run_generation_attempt = _v334_run_generation_attempt
use_core._run_provider_completion_recovery = _v334_run_provider_completion_recovery
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
    "USE v334 RECOVERY ENTRYPOINT: "
    f"build_id={CANONICAL_BUILD_ID}, version={APP_VERSION}, "
    f"fingerprint={DEPLOYMENT_FINGERPRINT}, source_sha256={RUNTIME_SOURCE_SHA256}, "
    f"core_sha256={_core_runtime_sha}, payload_sha256={_actual_payload}"
)