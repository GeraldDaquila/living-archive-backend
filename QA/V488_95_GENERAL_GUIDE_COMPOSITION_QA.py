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
USE_CORE = ROOT / "use_core.py"
USE_CORE_TEXT = USE_CORE.read_text(encoding="utf-8")


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    version_match = re.search(r'APP_VERSION = "(v[0-9.]+)"', MAIN_TEXT)
    assert_true(version_match is not None, "main.py production version is missing")
    app_version = version_match.group(1)
    assert_true(f'if str(APP_VERSION) != "{app_version}":' in MAIN_TEXT, "runtime version invariant does not match APP_VERSION")
    assert_true(f'DEPLOYMENT_FINGERPRINT = "USE-{app_version}-' in MAIN_TEXT, "deployment fingerprint does not match APP_VERSION")
    assert_true(f'CANONICAL_BUILD_ID = "USE-BUILD-{app_version}-' in MAIN_TEXT, "canonical build ID does not match APP_VERSION")
    assert_true("def _basic_inquiry_round1_deterministic_response(query, interpretation, context_data):" in MAIN_TEXT, "question-aware deterministic recovery is missing")
    recovery_start = MAIN_TEXT.find("def _basic_inquiry_round1_deterministic_response(")
    recovery_end = MAIN_TEXT.find("def _general_guide_authoritative_doorway", recovery_start)
    recovery_block = MAIN_TEXT[recovery_start:recovery_end]
    assert_true("I can't give you a reliable answer just now" not in recovery_block, "contradictory retry-later refusal remains in deterministic recovery")
    assert_true("bounded_general_knowledge_recovery" in recovery_block, "bounded general-knowledge recovery is missing")
    assert_true("def _general_guide_authoritative_doorway(query, context_data):" in MAIN_TEXT, "evidence-ranked recommendation selector is missing")
    assert_true("A syntactically valid URL is not proof of relevance" in MAIN_TEXT, "recommendation relevance guard is missing")
    assert_true("A title overlap alone is not enough to make a canonical doorway relevant." in MAIN_TEXT, "title-only doorway matches are not rejected")
    assert_true("def _wordpress_search_canonical_candidates(query, *, limit=3):" in MAIN_TEXT, "bounded provider-independent canonical search recovery is missing")
    assert_true("from concurrent.futures import ThreadPoolExecutor" in MAIN_TEXT and "executor.map(fetch_candidate, candidate_slice)" in MAIN_TEXT, "canonical search candidate fetches are not concurrent and order-preserving")
    assert_true("fallback_docs = _wordpress_search_canonical_candidates(query)" in MAIN_TEXT, "canonical search recovery is not connected to missing-doorway recovery")
    assert_true("primary = _canonical_primary_from_docs(evidence_docs, query, profile)" in MAIN_TEXT, "recovered candidates do not pass through the shared relevance gate")
    assert_true("score = (metrics[2], metrics[3], metrics[0], metrics[1], context[2], context[1], -index)" in MAIN_TEXT, "canonical doorway ranking does not prioritize evidence in the resource body")
    # Navigation selection is independent from answer synthesis sufficiency.
    evidence_boundary_start = MAIN_TEXT.find("if archive_evidence_unavailable:")
    evidence_boundary_end = MAIN_TEXT.find("# All ordinary questions use the same provider-neutral composition path", evidence_boundary_start)
    evidence_boundary = MAIN_TEXT[evidence_boundary_start:evidence_boundary_end]
    assert_true(evidence_boundary_start >= 0 and evidence_boundary_end > evidence_boundary_start, "evidence sufficiency boundary is missing")
    assert_true("authoritative_doorway = None" not in evidence_boundary, "synthesis insufficiency still erases an independently selected canonical doorway")
    assert_true('"canonical_link_context"' in evidence_boundary and '"context_blocks"' in evidence_boundary, "synthesis evidence is not isolated from the composition context")

    assert_true(
        "general_guide_composition.compose" in MAIN_TEXT,
        "ordinary Guide path is not bound to General Composition",
    )
    # Explanatory subject overlap must not authorize direct Guide Node handoff.
    assert_true("def _is_explicit_guide_destination_request(query):" in MAIN_TEXT, "explicit destination-intent boundary is missing")
    assert_true("if _is_explicit_guide_destination_request(query)" in MAIN_TEXT, "registry handoff is not guarded by explicit destination intent")
    assert_true('What is stewardship and why does it matter now more than ever?' in MAIN_TEXT, "reported explanatory-query regression probe is missing")
    assert_true("if glossary_term and _is_bounded_glossary_request(" in MAIN_TEXT, "direct Glossary handoff is not guarded by bounded-query validation")
    assert_true("embedded_term=embedded_glossary_term" in MAIN_TEXT, "direct Glossary handoff does not validate the original query shape")
    assert_true('USE v489.22 glossary invariant failed: reported compound stewardship question was misrouted to Glossary' in MAIN_TEXT, "reported compound Glossary regression probe is missing")

    basic_start = MAIN_TEXT.find("def _basic_inquiry_response(")
    basic_end = MAIN_TEXT.find("def _v48894_general_guide_composition_self_audit", basic_start)
    basic_block = MAIN_TEXT[basic_start:basic_end]
    assert_true(
        "use_core.generate_llm_response" not in basic_block,
        "legacy single-provider generation remains in the all-purpose Guide path",
    )

    assert_true("Apply explanatory discernment before composing" in composition._GENERAL_GUIDE_SYSTEM, "discernment prompt missing")
    assert_true("Use a concrete-example decision rule before composing" in composition._GENERAL_GUIDE_SYSTEM, "selective concrete-example decision rule missing")
    assert_true("Do not insert an example into a simple definition or answer when it adds no understanding" in composition._GENERAL_GUIDE_SYSTEM, "example restraint rule missing")
    assert_true("Make the example do explanatory work" in composition._GENERAL_GUIDE_SYSTEM, "example mechanism guidance missing")
    assert_true("Its relevance must be explainable in terms of the visitor's actual question" in composition._GENERAL_GUIDE_SYSTEM, "resource relevance contract missing")
    assert_true("Let the nature and complexity of the question determine the length" in composition._GENERAL_GUIDE_SYSTEM, "adaptive length guidance missing")
    assert_true("Do not impose a fixed word count" in composition._GENERAL_GUIDE_SYSTEM, "fixed length prohibition missing")
    assert_true("natural, conversational voice" in composition._GENERAL_GUIDE_SYSTEM, "conversational voice guidance missing")
    assert_true("Do not fabricate real-world case studies, statistics, quotations, or named authorities" in composition._GENERAL_GUIDE_SYSTEM, "example integrity boundary missing")
    snapshot = composition.contract_snapshot()
    assert_true(snapshot["contract_version"] == "v1.5", "composition contract drift")
    assert_true("The doorway is presented separately by The Guide after the answer" in composition._GENERAL_GUIDE_SYSTEM, "doorway presentation is not structurally separated from answer prose")
    assert_true(composition._requires_compound_explanatory_structure("What is stewardship and why is it important now more than ever?"), "compound explanatory golden case is not protected")
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
    try:
        composition._parse_factory([
            {
                "title": "Stewardship Today",
                "url": "https://geralddaquila.com/stewardship-today/",
                "content": "Grounding material.",
            }
        ], "What is stewardship and why is it important now more than ever?")(
            '{"response":"Definition paragraph.\n\nWhy-now paragraph.","doorway_title":"","response_shape":"explanatory"}'
        )
        raise AssertionError("compound explanatory answer with two paragraphs was accepted")
    except ValueError:
        pass

    # Provider-neutral seam test: simulate the bank rather than calling an external model.
    original_route = composition.route_with_model_bank

    class FakeCore:
        @staticmethod
        def context_blocks_to_documents(_blocks):
            return []

    captured_user_messages = []

    def fake_route(**kwargs):
        captured_user_messages.append(kwargs["messages"][-1]["content"])
        parsed = kwargs["parse"](
            '{"response":"Stewardship is about taking responsibility for something that matters beyond yourself.\\n\\nIt matters now because the consequences of our choices increasingly extend beyond the people or places immediately around us.\\n\\nThat makes stewardship less about control than about asking what we are responsible for and how we can care for it well.","doorway_title":"Stewardship Today","response_shape":"explanatory"}'
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
        assert_true("Stewardship is about taking responsibility" in composed["response"], "fake provider response was not preserved by composition")
        assert_true(composed["response_shape"] == "explanatory", "composition response shape drifted")
        empty_result = composition.compose(
            use_core=FakeCore(),
            query="Why does stewardship matter in everyday life?",
            context_data={},
        )
        assert_true(empty_result is not None, "empty Archive retrieval blocked a general-purpose answer")
        assert_true(
            "No relevant Archive material was retrieved" in captured_user_messages[-1],
            "empty-retrieval prompt did not preserve the general-knowledge lane",
        )
        assert_true(
            "do not invent Archive-specific claims or sources" in captured_user_messages[-1],
            "empty-retrieval prompt does not protect source integrity",
        )

        # Navigation must be supplied structurally by the Guide, never embedded
        # as provider-generated prose.
        try:
            composition._parse_factory([{
                "title": "Stewardship Today",
                "url": "https://geralddaquila.com/stewardship-today/",
                "content": "Grounding material.",
            }])(
                '{"response":"Answer. [Explore](https://geralddaquila.com/stewardship-today/)","doorway_title":"","response_shape":"general"}'
            )
            raise AssertionError("provider-generated doorway URL was accepted into visitor prose")
        except ValueError:
            pass

        # An imperfect optional doorway label must not invalidate the answer.
        def fake_route_with_bad_doorway(**kwargs):
            parsed = kwargs["parse"](
                '{"response":"Stewardship asks what we are responsible for and how we care for what affects more than ourselves.\\n\\nIt matters because our choices can affect people and systems beyond our immediate reach.\\n\\nThe useful question is not only what we control, but what we are responsible for.","doorway_title":"Provider Invented Doorway","response_shape":"explanatory"}'
            )
            return {"parsed": parsed, "provider": "fake_provider", "model": "fake_model"}

        composition.route_with_model_bank = fake_route_with_bad_doorway
        try:
            tolerant = composition.compose(
                use_core=FakeCore(),
                query="What is stewardship and why does it matter today?",
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

    # Recommendation is a first-class Guide response contract, independent of provider success.
    assert_true("def _normalize_authoritative_recommendation" in MAIN_TEXT, "recommendation normalization helper missing")
    assert_true('"recommendation": authoritative_doorway' in MAIN_TEXT, "ordinary response recommendation field is not bound to authoritative doorway")
    assert_true("authoritative_doorway = _normalize_authoritative_recommendation(" in MAIN_TEXT, "recommendation is not resolved before composition")
    assert_true("One relevant place to continue is [" not in MAIN_TEXT, "doorway prose still leaks into ordinary answer construction")
    assert_true('"recommendation": recovery_recommendation' in MAIN_TEXT, "recovery response lost structured recommendation")

    # Recommendation authority must terminate at USE's canonical link context;
    # it must never depend on provider-generated navigation.
    assert_true("_canonical_primary_from_docs(evidence_docs, query, profile)" in MAIN_TEXT, "Guide does not rank recommendation candidates against retrieved evidence")
    assert_true("A syntactically valid URL is not proof of relevance" in MAIN_TEXT, "preselected doorway is still trusted without relevance validation")
    assert_true("emit only a doorway" in MAIN_TEXT and "supported by the selected document's title, URL, and content" in MAIN_TEXT, "recommendation lacks evidence-backed selection contract")

    print("V489.14 GENERAL GUIDE COMPOSITION QA: PASS")
    print("provider_neutral=True")
    print("legacy_single_provider_all_purpose_path=absent")
    print("golden_calibration_cases=6")


if __name__ == "__main__":
    main()
