"""Sitewide Safety Boundary Regression QA.

Checks deterministic safety normalization, active safety follow-through, and the
Guide's fail-closed interruption boundary without invoking the protected core
or any live provider.
"""

from pathlib import Path
import ast
import json

ROOT = Path(__file__).resolve().parents[1]


def _source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def main():
    safety_source = _source("safety_intelligence.py")
    main_source = _source("main.py")

    ast.parse(safety_source, filename="safety_intelligence.py")
    ast.parse(main_source, filename="main.py")

    namespace = {}
    exec(compile(safety_source, "safety_intelligence.py", "exec"), namespace, namespace)
    classify = namespace["normalize_safety_state"]

    assert classify("I don't want to live anymore.") in {"current", "acute"}
    assert classify("I don’t want to live anymore.") in {"current", "acute"}
    assert classify("I'm thinking of killing myself.") == "current"
    assert classify("I am going to kill myself.") == "acute"
    assert classify("Someone I care about is talking about suicide.") == "support"

    assert classify(
        "yes",
        history=(
            "visitor: I don’t want to live anymore.\n"
            "assistant: Do you think you might act on these thoughts right now?"
        ),
    ) == "acute_followthrough"

    safety_segment = main_source[
        main_source.index("safety_state = classify_safety"):
        main_source.index("# Immediate FSD handoff")
    ]
    assert '"intent": "SAFETY_INTERRUPT"' in safety_segment
    assert "return await _use_send_json(send" in safety_segment
    assert '"bypasses_ordinary_hrn": True' in safety_segment
    assert '"bypasses_llm": True' in safety_segment
    assert '"bypasses_retrieval": True' in safety_segment
    assert "_FASTAPI_APP" not in safety_segment

    # The protected core remains immutable from the safety QA perspective.
    assert 'EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"' in main_source

    print("sitewide safety boundary QA: PASS")


if __name__ == "__main__":
    main()
