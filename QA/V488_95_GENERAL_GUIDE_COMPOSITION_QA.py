"""Static QA for the provider-neutral General Guide composition contract.

This suite deliberately avoids external provider calls. It verifies the architectural
seam, visitor-language boundary, operation registration, and golden calibration cases.
Live provider/E2E validation remains a deployment-stage responsibility.
"""

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import general_guide_composition as composition
import provider_bank

MAIN = ROOT / "main.py"
MAIN_TEXT = MAIN.read_text(encoding="utf-8")


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    assert_true('APP_VERSION = "v489.02"' in MAIN_TEXT, "main.py version is not v489.00")
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
    assert_true(snapshot["contract_version"] == "v1.1", "composition contract drift")
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
            "The Archive material. [evidence excerpt bounded by USE]"
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

    assert_true(
        composition._sanitize_candidate("First paragraph.\n\nSecond paragraph.")
        == "First paragraph.\n\nSecond paragraph.",
        "composition sanitizer collapsed meaningful paragraph structure",
    )

    # Provider-neutral seam test: simulate the bank rather than calling an external model.
    original_route = composition.route_with_model_bank

    class FakeCore:
        @staticmethod
        def context_blocks_to_documents(_blocks):
            return []

    def fake_route(**kwargs):
        parsed = kwargs["parse"](
            '{"response":"Stewardship is about taking responsibility for something that matters beyond yourself. You can use that idea to ask what deserves care and what responsibility looks like in practice.","doorway_title":"Stewardship Today","response_shape":"explanatory"}'
        )
        return {
            "parsed": parsed,
            "provider": "fake_provider",
            "model": "fake_model",
            "preference_order": ["fake_provider:fake_model"],
        }

    composition.route_with_model_bank = fake_route
    try:
        composed = composition.compose(
            use_core=FakeCore(),
            query="What is stewardship and why is it important now more than ever?",
            context_data={
                "generation_authority_protected_docs": [
                    {
                        "title": "Stewardship Today",
                        "url": "https://geralddaquila.com/stewardship-today/",
                        "content": "Stewardship asks what we are responsible for and how we care for what affects more than ourselves.",
                    }
                ]
            },
        )
        assert_true(composed is not None, "provider-neutral composition seam returned no result")
        assert_true(composed["provider"] == "fake_provider", "provider identity did not cross the bank boundary")
        assert_true("You can use that idea" in composed["response"], "ordinary visitor language was falsely rejected")
        assert_true(composed["response_shape"] == "explanatory", "composition response shape drifted")

        # An imperfect optional doorway label must not invalidate the answer.
        def fake_route_with_bad_doorway(**kwargs):
            parsed = kwargs["parse"](
                '{"response":"Stewardship asks what we are responsible for and how we care for what affects more than ourselves.","doorway_title":"Provider Invented Doorway","response_shape":"explanatory"}'
            )
            return {"parsed": parsed, "provider": "fake_provider", "model": "fake_model"}

        composition.route_with_model_bank = fake_route_with_bad_doorway
        try:
            tolerant = composition.compose(
                use_core=FakeCore(),
                query="What is stewardship and why is it important now more than ever?",
                context_data={
                    "generation_authority_protected_docs": [
                        {
                            "title": "Stewardship Today",
                            "url": "https://geralddaquila.com/stewardship-today/",
                            "content": "Stewardship asks what we are responsible for and how we care for what affects more than ourselves.",
                        }
                    ]
                },
            )
            assert_true(tolerant is not None, "optional doorway metadata still invalidates composition")
            assert_true(tolerant["response_shape"] == "explanatory", "tolerant composition shape drifted")
            assert_true(tolerant["doorway_title"] == "", "unapproved doorway metadata was not neutralized")
        finally:
            composition.route_with_model_bank = original_route
    finally:
        composition.route_with_model_bank = original_route

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

    print("V489.02 GENERAL GUIDE COMPOSITION QA: PASS")
    print("provider_neutral=True")
    print("legacy_single_provider_all_purpose_path=absent")
    print("golden_calibration_cases=6")


if __name__ == "__main__":
    main()
