"""Static validation of the v487.80 shared contract draft."""
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
TEXT = (ROOT / "QA" / "SHARED_CONTRACT_DRAFT.md").read_text(encoding="utf-8")

REQUIRED = (
    "EvidenceItem",
    "Claim",
    "Inquiry / Movement",
    "Epistemic Classification",
    "Synthesis Material",
    "Doorway Candidate",
    "Operation Result",
    "Visitor Language Boundary",
    "READY",
    "DELEGATE",
    "NEEDS_RETRY",
    "UNAVAILABLE",
)
FORBIDDEN_RUNTIME_IMPORTS = ("shared_intelligence", "SHARED_INTELLIGENCE", "general_utility")

def main() -> int:
    for marker in REQUIRED:
        assert marker in TEXT, marker
    for runtime in ("main.py", "main_v487_28_runtime.py", "use_core.py"):
        source = (ROOT / runtime).read_text(encoding="utf-8")
        for marker in FORBIDDEN_RUNTIME_IMPORTS:
            assert marker not in source, (runtime, marker)
    ast.parse((ROOT / "QA" / "SHARED_INTELLIGENCE_MATRIX.py").read_text(encoding="utf-8"))
    print("v487.80 shared contract draft: PASS")
    print("production wiring: ABSENT")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
