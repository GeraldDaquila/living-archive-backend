"""Regression gate for the approved transparency/trust relational-synthesis Gold Star."""

from gold_star_lessons import active_quality_contribution
from scripts.guide_live_evaluation import evaluate_held
from general_guide_composition import has_conceptual_relationship_explanation, _has_transparency_trust_reciprocity

CASE = {
    "case_id": "heldout-transparency-trust-relational-synthesis-001",
    "query": "What is the relationship between transparency and trust?",
}
BENCHMARK_ID = "general-guide-relational-synthesis-concept-pairs-2026-11-24"


def test_transparency_trust_gold_star_is_retrieved_as_bounded_guidance():
    contribution = active_quality_contribution(CASE["query"])
    assert contribution is not None
    assert contribution["benchmark_id"] == BENCHMARK_ID
    assert contribution["authority_mode"] == "structural_guidance_only"
    assert contribution["candidates"][0]["discipline"]
    assert "deterministic" not in contribution["authority_mode"]


def test_transparency_trust_retrieval_fragment_is_rejected_as_live_answer():
    transport = {
        "status": 200,
        "error": None,
        "body": {
            "ok": True,
            "response": (
                "The Archive material available here offers this starting point: "
                "Why trust may be as important to societal resilience as roads, "
                "power grids, and communication networks—and why its erosion "
                "creates consequences far beyond politics."
            ),
            "recommendation": None,
            "provider": "deterministic_recovery",
            "model": "retrieval-excerpt",
            "response_provenance": {
                "class": "deterministic_recovery",
                "llm_invoked": False,
            },
        },
    }
    checks = evaluate_held(CASE, transport)
    failed = {item["name"] for item in checks if not item["passed"]}
    assert {
        "attributable_llm",
        "distinct_concept_roles",
        "relationship_mechanism",
        "reciprocal_but_not_identical",
        "not_retrieval_fragment",
    }.issubset(failed)


def test_transparency_trust_live_answer_requires_relationship_and_limits():
    answer = (
        "Transparency makes relevant decisions, reasons, evidence, and limits visible, "
        "while trust is the justified willingness to rely on conduct that proves dependable. "
        "Transparency enables scrutiny and correction because people can examine whether "
        "commitments are being kept. When an institution responds honestly, that scrutiny "
        "can strengthen trust; trust in turn makes people more willing to engage with "
        "disclosures. They reinforce one another but neither guarantees the other. "
        "Disclosure without context or accountability can mislead, and legitimate privacy "
        "and confidentiality must still be protected."
    )
    transport = {
        "status": 200,
        "error": None,
        "body": {
            "ok": True,
            "response": answer,
            "recommendation": None,
            "response_provenance": {
                "class": "llm",
                "llm_invoked": True,
                "provider": "test-provider",
                "model": "test-model",
            },
        },
    }
    checks = evaluate_held(CASE, transport)
    assert all(item["passed"] for item in checks), checks

def test_runtime_relationship_contract_accepts_explicit_reciprocal_transparency_wording():
    answer = (
        "Transparency can support justified trust by letting people verify whether an institution is acting as claimed, "
        "and by creating opportunities to catch and correct poor conduct. Reasonable trust can also make transparency "
        "more possible: people are more likely to share information, ask candid questions, and engage openly. "
        "Neither guarantees the other. Privacy and legitimate confidentiality must still be protected while decisions "
        "remain accountable."
    )
    assert has_conceptual_relationship_explanation(answer, CASE["query"]) is True
    assert _has_transparency_trust_reciprocity(answer) is True


def test_runtime_relationship_contract_still_rejects_one_way_transparency_claims():
    answer = (
        "Transparency can support trust by allowing people to inspect decisions and correct mistakes. "
        "Privacy and confidentiality still matter, and disclosure alone does not guarantee trust. "
        "Institutions should be clear about their decisions."
    )
    assert _has_transparency_trust_reciprocity(answer) is False
