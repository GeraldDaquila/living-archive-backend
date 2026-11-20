"""Regression tests for visitor-facing operational disclosure filtering."""

import main


def test_removes_operational_outage_paragraph_but_preserves_answer():
    answer = (
        "Transformation becomes rebranding when labels change but the "
        "behavior-producing structure remains intact.\n\n"
        "This is a bounded general-knowledge orientation because the Guide's "
        "live answer and canonical-retrieval services were unavailable on this attempt."
    )
    assert main._sanitize_basic_inquiry_response(answer) == (
        "Transformation becomes rebranding when labels change but the "
        "behavior-producing structure remains intact."
    )


def test_preserves_legitimate_grounding_and_related_continuation_language():
    answer = (
        "The answer is a general conceptual orientation.\n\n"
        "The separately selected Archive resource offers a related continuation."
    )
    assert main._sanitize_basic_inquiry_response(answer) == answer
