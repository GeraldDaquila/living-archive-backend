"""Regression tests for the Guide's autonomy-evidence final visitor boundary.

The production module is intentionally not imported: this isolates the exact
finalizer branch from provider, retrieval, and application startup dependencies.
"""
import ast
import re
from pathlib import Path


def _load_finalizer():
    source = (Path(__file__).resolve().parents[1] / "main.py").read_text(encoding="utf-8")
    module = ast.parse(source)
    function = next(
        node for node in module.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_guide_finalize_visitor_payload"
    )
    isolated = ast.Module(body=[function], type_ignores=[])
    namespace = {
        "re": re,
        "APP_VERSION": "test",
        "_resolve_exact_guide_gold_standard": lambda _query: None,
        "_gold_star_doorway_omission_is_justified": lambda _standard: False,
        "general_guide_composition": type(
            "Composition",
            (),
            {
                "_requires_autonomy_evidence_evaluation": staticmethod(lambda _query: True),
                "_has_autonomy_evidence_evaluation": staticmethod(
                    lambda text: "AUTONOMY-EVIDENCE-FRAMEWORK" in str(text)
                ),
                "_autonomy_evidence_evaluation_recovery": staticmethod(
                    lambda _query: {
                        "response": "AUTONOMY-EVIDENCE-FRAMEWORK: assess autonomy, adaptation, resilience, and improvement with auditable evidence."
                    }
                ),
            },
        ),
    }
    exec(compile(isolated, "main.py", "exec"), namespace)
    return namespace["_guide_finalize_visitor_payload"]


def test_autonomy_evidence_finalizer_reads_response_from_payload_before_validation():
    finalize = _load_finalizer()

    result = finalize(
        {"ok": True, "response": "An earlier route supplied a noncompliant answer."},
        "What evidence demonstrates genuine autonomy, adaptivity, resilience, and improvement?",
    )

    assert result["response"].startswith("AUTONOMY-EVIDENCE-FRAMEWORK:")
    assert result["processing"] == "final_visitor_boundary_autonomy_evidence_evaluation"
    assert result["recommendation"] is None
    assert result["doorway_title"] is None


def test_autonomy_evidence_finalizer_accepts_existing_compliant_response():
    finalize = _load_finalizer()
    answer = "AUTONOMY-EVIDENCE-FRAMEWORK: evidence is independently evaluated."

    result = finalize(
        {"ok": True, "response": answer},
        "What evidence demonstrates genuine autonomy, adaptivity, resilience, and improvement?",
    )

    assert result["response"] == answer
