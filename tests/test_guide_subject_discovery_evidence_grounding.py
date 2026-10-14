"""Subject-discovery retrieval must separate search intent from the requested topic."""

import main


def test_extracts_subject_from_where_can_i_find_material_question():
    assert main._guide_subject_discovery_query(
        "Where can I find material about institutional responsibility?"
    ) == "institutional responsibility"


def test_extracts_subject_from_resource_and_information_variants():
    assert main._guide_subject_discovery_query(
        "Could you find resources on institutional accountability?"
    ) == "institutional accountability"
    assert main._guide_subject_discovery_query(
        "I need information regarding public governance."
    ) == "public governance"
    assert main._guide_subject_discovery_query(
        "Show me articles related to institutional trust"
    ) == "institutional trust"


def test_preserves_the_topic_without_rewriting_ordinary_questions():
    assert main._guide_subject_discovery_query(
        "Why does institutional responsibility matter?"
    ) == ""


def test_subject_query_does_not_hard_code_a_specific_archive_topic():
    assert main._guide_subject_discovery_query(
        "Where can I find essays about community accountability?"
    ) == "community accountability"
    assert main._guide_subject_discovery_query(
        "Where can I find documents about public health governance?"
    ) == "public health governance"



def test_subject_discovery_always_triggers_canonical_content_supplement():
    assert main._guide_requires_canonical_subject_supplement(
        False, "institutional responsibility"
    )
    assert main._guide_requires_canonical_subject_supplement(
        True, "institutional responsibility"
    )


def test_ordinary_queries_only_trigger_recovery_when_evidence_is_unavailable():
    assert main._guide_requires_canonical_subject_supplement(True, "")
    assert not main._guide_requires_canonical_subject_supplement(False, "")
