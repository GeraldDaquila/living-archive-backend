"""Static QA for the provider-neutral General Guide composition contract.

This suite deliberately avoids external provider calls. It verifies the architectural
seam, visitor-language boundary, operation registration, and golden calibration cases.
Live provider/E2E validation remains a deployment-stage responsibility.
"""

from pathlib import Path
import re

import general_guide_composition as composition
import provider_bank

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "main.py"
MAIN_TEXT = MAIN.read_text(encoding="utf-8")


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    assert_true('APP_VERSION = "v488.95"' in MAIN_TEXT, "main.py version is not v488.95")
    assert_true(
        "general_guide_composition.compose" in MAIN_TEXT,
        "ordinary Guide path is not bound to General Composition",
    )

    basic_start = MAIN_TEXT.find("def _basic_inquiry_response(")
    basic_end = MAIN_TEXT.find("def _v48894_general_guide_composition_self_audit", basic_start)
    basic_block = MAIN_TEXT[basic_start:basic_end]
    assert_true(
        "use_core.generate_llm_response" not in basic_block,
        "legacy single-provider generation remains in the all-purpose Guide path",
    )

    snapshot = composition.contract_snapshot()
    assert_true(snapshot["contract_version"] == "v1", "composition contract drift")
    assert_true(snapshot["provider_neutral"] is True, "composition is not provider-neutral")
    assert_true(
        snapshot["operation"] == "general_guide_composition",
        "composition operation identity drift",
    )

    requirements = provider_bank.OPERATION_REQUIREMENTS["general_guide_composition"]
    assert_true("composition" in requirements, "Provider Bank composition capability missing")
    assert_true("long_context" in requirements, "Provider Bank long-context capability missing")
    assert_true(
        provider_bank.OPERATION_TOKEN_FLOORS["general_guide_composition"] == 900,
        "General Guide token floor drift",
    )

    assert_true(
        composition._sanitize_candidate(
            "The Archive material [evidence excerpt bounded by USE]"
        )
        == "The Archive material.",
        "visitor-language sanitizer failed its structural probe",
    )
    assert_true(
        composition._question_shape(
            "What is stewardship and why is it important now more than ever?"
        )
        == "explanatory",
        "stewardship golden case is not classified as explanatory",
    )

    golden_cases = [
        (
            "What is photosynthesis?",
            "direct",
            "answer the question directly in ordinary language",
        ),
        (
            "What is stewardship and why is it important now more than ever?",
            "explanatory",
            "answer both the definition and present relevance",
        ),
        (
            "What makes a meaningful life?",
            "explanatory",
            "offer one useful distinction rather than a generic summary",
        ),
        (
            "Why do systems become harder to govern as they grow?",
            "explanatory",
            "explain the mechanism and significance rather than merely defining it",
        ),
        (
            "Where can I find the essays on grief?",
            "navigational",
            "help the visitor find the material without replacing navigation with essay prose",
        ),
        (
            "I keep feeling like I am doing everything right and still getting nowhere.",
            "reflective",
            "respond humanely without diagnosis or invented personal history",
        ),
    ]
    for query, expected_shape, quality_rule in golden_cases:
        actual = composition._question_shape(query)
        assert_true(
            actual == expected_shape,
            f"golden case shape mismatch: {query!r}: expected {expected_shape}, got {actual}",
        )
        assert_true(bool(quality_rule), "golden calibration rule missing")

    print("V488.95 GENERAL GUIDE COMPOSITION QA: PASS")
    print("provider_neutral=True")
    print("legacy_single_provider_all_purpose_path=absent")
    print("golden_calibration_cases=6")


if __name__ == "__main__":
    main()
