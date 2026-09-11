# USE PRODUCTION VERSION: v334 — Compassionate Recommendation Boundary + The Guide
# Sole visitor-facing entrypoint: main.py remains the Render/Uvicorn production doorway.
# The intact v333 engine is preserved as use_core.py from the existing canonical v333 Git blob.
# v334 changes only the vulnerable-experience output boundary at runtime and binds release identity here.

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
CANONICAL_BUILD_PAYLOAD_SHA256 = "8e8338e19ad5496c6bda40b69f40b1cdaf77cdbea356470fcf83b3d1a0641bb3"
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

# Raw main.py provenance is intentionally advisory here. Render normalizes the
# deployed filesystem representation, so this runtime value is not a stable
# release invariant. Package and canonical build identity checks remain strict.

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
if _actual_payload != CANONICAL_BUILD_PAYLOAD_SHA256:
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


def _v334_compassionate_voice_violation(user_query: str, answer: str) -> str:
    """Reject grief/loss output that turns source framing into visitor benefit."""
    query = str(user_query or "").casefold()
    if not any(term in query for term in (
        "grief", "grieving", "bereavement", "bereaved", "death of", "died",
        "loss of a loved one", "lost my", "lost her", "lost his", "lost their",
        "mourning", "mourning the", "funeral",
    )):
        return ""
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


def _v334_compassionate_voice_self_audit() -> None:
    question = "What essay would you recommend for someone grieving the death of a loved one?"
    assert _v334_compassionate_voice_violation(
        question,
        "The material offers comfort by suggesting continuity and connection beyond death.",
    )
    assert _v334_compassionate_voice_violation(
        question,
        "This piece is helpful for people grieving because it provides hope and peace.",
    )
    assert _v334_compassionate_voice_violation(
        question,
        "You should find meaning in your grief and use this loss to become stronger.",
    )
    assert not _v334_compassionate_voice_violation(
        question,
        "The essay explores beliefs about continuity and connection beyond death. Its spiritual framing includes themes of hope and peace.",
    )
    assert not _v334_compassionate_voice_violation(
        question,
        "This piece explores grief through spiritual and psychological perspectives. It may be a gentle place to begin.",
    )


_v334_compassionate_voice_self_audit()

use_core._v308_compassionate_voice_violation = _v334_compassionate_voice_violation
use_core.APP_VERSION = APP_VERSION
use_core.DEPLOYMENT_FINGERPRINT = DEPLOYMENT_FINGERPRINT
use_core.CANONICAL_BUILD_ID = CANONICAL_BUILD_ID
use_core.CANONICAL_BUILD_PAYLOAD_SHA256 = CANONICAL_BUILD_PAYLOAD_SHA256
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
    f"core_sha256={_core_runtime_sha}"
)
