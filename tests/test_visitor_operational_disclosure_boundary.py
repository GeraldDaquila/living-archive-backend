"""Regression tests for visitor-facing operational disclosure filtering."""

import ast
import re
from pathlib import Path


def _load_sanitizer():
    source = Path("main.py").read_text(encoding="utf-8")
    module = ast.parse(source, filename="main.py")
    function = next(
        node for node in module.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_sanitize_basic_inquiry_response"
    )
    isolated = ast.Module(body=[function], type_ignores=[])
    namespace = {"re": re}
    exec(compile(isolated, "main.py", "exec"), namespace)
    return namespace["_sanitize_basic_inquiry_response"]


def test_removes_operational_outage_paragraph_but_preserves_answer():
    sanitize = _load_sanitizer()
    answer = (
        "Transformation becomes rebranding when labels change but the "
        "behavior-producing structure remains intact.\n\n"
        "This is a bounded general-knowledge orientation because the Guide's "
        "live answer and canonical-retrieval services were unavailable on this attempt."
    )
    assert sanitize(answer) == (
        "Transformation becomes rebranding when labels change but the "
        "behavior-producing structure remains intact."
    )


def test_preserves_legitimate_grounding_and_related_continuation_language():
    sanitize = _load_sanitizer()
    answer = (
        "The answer is a general conceptual orientation.\n\n"
        "The separately selected Archive resource offers a related continuation."
    )
    assert sanitize(answer) == answer
