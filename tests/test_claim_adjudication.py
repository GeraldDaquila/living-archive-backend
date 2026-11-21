from claim_adjudication import adjudicate_answer_claims


DOCS = [{
    "id": "source-1",
    "title": "Canonical source",
    "url": "https://geralddaquila.com/example/",
    "text": "The archive defines stewardship as responsible care of shared conditions.\n\nIt distinguishes responsibility from control.",
}]


def _extract(_answer):
    return [{"claim": "Stewardship is responsible care."}]


def _assess(outcome, quote=None, passage_index=0):
    def callback(_claim, passages):
        attrs = []
        if quote is not None:
            attrs = [{
                "passage_id": passages[passage_index]["passage_id"],
                "quote": quote,
            }]
        return {"outcome": outcome, "attributions": attrs}
    return callback


def test_supported_requires_exact_passage_quote():
    result = adjudicate_answer_claims(
        "Stewardship is responsible care.",
        DOCS,
        extract_claims=_extract,
        assess_claim=_assess("supported", "The archive defines stewardship as responsible care of shared conditions."),
    )
    assert result["status"] == "assessed"
    assert result["claims"][0]["outcome"] == "supported"
    assert result["claims"][0]["attributions"][0]["source_id"] == "source-1"


def test_partially_supported_is_retained_with_exact_attribution():
    result = adjudicate_answer_claims(
        "Stewardship is responsible care.",
        DOCS,
        extract_claims=_extract,
        assess_claim=_assess("partially_supported", "The archive defines stewardship as responsible care of shared conditions."),
    )
    assert result["claims"][0]["outcome"] == "partially_supported"


def test_contradiction_requires_exact_passage_quote():
    result = adjudicate_answer_claims(
        "Stewardship is control.",
        DOCS,
        extract_claims=_extract,
        assess_claim=_assess("contradicted", "It distinguishes responsibility from control."),
    )
    assert result["claims"][0]["outcome"] == "contradicted"


def test_missing_attribution_fails_closed():
    result = adjudicate_answer_claims(
        "answer", DOCS, extract_claims=_extract,
        assess_claim=_assess("supported"),
    )
    assert result["claims"][0]["outcome"] == "unassessed"
    assert result["claims"][0]["reason"] == "missing_passage_attribution"


def test_fabricated_or_inexact_quote_fails_closed():
    result = adjudicate_answer_claims(
        "answer", DOCS, extract_claims=_extract,
        assess_claim=_assess("supported", "The source proves this exact claim."),
    )
    assert result["claims"][0]["outcome"] == "unassessed"
    assert result["claims"][0]["reason"] == "unverifiable_passage_attribution"


def test_unknown_passage_id_fails_closed():
    def assessor(_claim, _passages):
        return {"outcome": "contradicted", "attributions": [{
            "passage_id": "not-a-real-passage", "quote": "control"
        }]}
    result = adjudicate_answer_claims("answer", DOCS, extract_claims=_extract, assess_claim=assessor)
    assert result["claims"][0]["outcome"] == "unassessed"


def test_provider_unavailable_retains_unassessed():
    result = adjudicate_answer_claims("answer", DOCS)
    assert result["status"] == "unassessed"
    assert result["reason"] == "adjudication_provider_unavailable"


def test_extractor_exception_retains_unassessed():
    def broken(_answer):
        raise RuntimeError("provider offline")
    result = adjudicate_answer_claims("answer", DOCS, extract_claims=broken, assess_claim=_assess("supported"))
    assert result["status"] == "unassessed"
    assert result["reason"] == "claim_extraction_failed"


def test_malformed_extraction_retains_unassessed():
    result = adjudicate_answer_claims("answer", DOCS, extract_claims=lambda _a: {"claim": "bad"}, assess_claim=_assess("supported"))
    assert result["reason"] == "malformed_claim_extraction"


def test_malformed_assessment_retains_unassessed():
    result = adjudicate_answer_claims("answer", DOCS, extract_claims=_extract, assess_claim=lambda _c, _p: ["bad"])
    assert result["claims"][0]["outcome"] == "unassessed"


def test_assessor_exception_retains_unassessed():
    def broken(_claim, _passages):
        raise RuntimeError("provider offline")
    result = adjudicate_answer_claims("answer", DOCS, extract_claims=_extract, assess_claim=broken)
    assert result["claims"][0]["outcome"] == "unassessed"


def test_no_retrieved_passage_is_no_relevant_public_source():
    result = adjudicate_answer_claims("answer", [])
    assert result["status"] == "no_relevant_public_source"


def test_non_evidentiary_outcomes_cannot_smuggle_attributions():
    result = adjudicate_answer_claims(
        "answer", DOCS, extract_claims=_extract,
        assess_claim=_assess("stale_or_unavailable", "The archive defines stewardship as responsible care of shared conditions."),
    )
    assert result["claims"][0]["outcome"] == "unassessed"


def test_claim_count_is_bounded():
    result = adjudicate_answer_claims(
        "answer", DOCS, extract_claims=lambda _a: [{"claim": str(i)} for i in range(33)],
        assess_claim=_assess("supported", "control"),
    )
    assert result["status"] == "unassessed"
    assert result["reason"] == "malformed_claim_extraction"



def test_stale_or_unavailable_outcome_is_preserved_without_attribution():
    result = adjudicate_answer_claims(
        "answer", DOCS, extract_claims=_extract,
        assess_claim=_assess("stale_or_unavailable"),
    )
    assert result["claims"][0]["outcome"] == "stale_or_unavailable"
    assert result["status"] == "assessed"


def test_no_relevant_public_source_outcome_is_preserved_per_claim():
    result = adjudicate_answer_claims(
        "answer", DOCS, extract_claims=_extract,
        assess_claim=_assess("no_relevant_public_source"),
    )
    assert result["claims"][0]["outcome"] == "no_relevant_public_source"


def test_mixed_claim_results_keep_individual_outcomes():
    def extract(_answer):
        return [{"claim": "claim one"}, {"claim": "claim two"}]
    def assess(claim, passages):
        if claim == "claim one":
            return {
                "outcome": "supported",
                "attributions": [{
                    "passage_id": passages[0]["passage_id"],
                    "quote": "The archive defines stewardship as responsible care of shared conditions.",
                }],
            }
        return {"outcome": "unassessed", "attributions": []}
    result = adjudicate_answer_claims("answer", DOCS, extract_claims=extract, assess_claim=assess)
    assert [item["outcome"] for item in result["claims"]] == ["supported", "unassessed"]
    assert result["status"] == "unassessed"
