import pytest
from fsd_runtime import build_quantum_query, parse_evidence

def test_quantum_queries_use_only_mapped_responses():
    answers = [0,1,2,3,0,1,2,3,0,1]
    first = build_quantum_query(answers, "organization", "Q001_CORRESPONDENCE")
    second = build_quantum_query(answers, "organization", "Q002_CORRECTABILITY")
    assert "People notice it" in first
    assert "meaningful authority" not in first
    assert "meaningful authority" in second
    assert "Where might there be room" in second

def test_evidence_parser_accepts_only_canonical_site_urls():
    context = {"context_blocks": "Title: A Canonical Resource\nURL: https://geralddaquila.com/resource/\nContent: Evidence excerpt\n\n---\n\nTitle: External\nURL: https://example.com/page\nContent: Ignore"}
    result = parse_evidence(context)
    assert len(result) == 1
    assert result[0]["title"] == "A Canonical Resource"

def test_evidence_parser_rejects_insufficient_retrieval():
    assert parse_evidence({"context_blocks": "", "evidence_sufficiency_unavailable": True}) == []
    assert parse_evidence(None) == []

def test_evidence_parser_deduplicates_canonical_urls():
    block = "Title: A\nURL: https://geralddaquila.com/a/\nContent: text"
    result = parse_evidence({"context_blocks": block + "\n\n---\n\n" + block})
    assert len(result) == 1


from fsd_contract import CONTRACT_VERSION
from fsd_runtime import prepare_fsd_analysis


def _valid_payload(scale=None):
    value = {"contract_version": CONTRACT_VERSION, "answers": [0, 1, 2, 3, 0, 1, 2, 3, 0, 1]}
    if scale is not None:
        value["scale"] = scale
    return value


def test_prepare_analysis_retrieves_both_quanta_and_labels_evidence():
    calls = []
    def retrieve(query):
        calls.append(query)
        return {"context_blocks": (
            "Title: Correspondence Resource\\n"
            "URL: https://geralddaquila.com/correspondence/\\n"
            "Content: Canonical evidence about correspondence."
        )}
    result = prepare_fsd_analysis(_valid_payload("organization"), retrieve)
    assert len(calls) == 2
    assert "Correspondence" in calls[0]
    assert "Correctability" in calls[1]
    assert result["validated"]["scale"] == "organization"
    assert result["evidence"][0]["evidence_id"] == "E01"


def test_prepare_analysis_deduplicates_evidence_across_quantum_retrievals():
    block = (
        "Title: Shared Resource\\n"
        "URL: https://geralddaquila.com/shared/\\n"
        "Content: Independent canonical evidence."
    )
    result = prepare_fsd_analysis(_valid_payload(), lambda query: {"context_blocks": block})
    assert len(result["evidence"]) == 1


def test_prepare_analysis_fails_closed_when_both_retrievals_are_insufficient():
    calls = []
    def retrieve(query):
        calls.append(query)
        return {"context_blocks": "", "evidence_sufficiency_unavailable": True}
    with pytest.raises(RuntimeError, match="No sufficient canonical evidence"):
        prepare_fsd_analysis(_valid_payload(), retrieve)
    assert len(calls) == 2


def test_prepare_analysis_does_not_infer_a_scale():
    result = prepare_fsd_analysis(
        _valid_payload(),
        lambda query: {"context_blocks": (
            "Title: Resource\\n"
            "URL: https://geralddaquila.com/resource/\\n"
            "Content: Evidence for this test."
        )},
    )
    assert result["validated"]["scale"] is None
