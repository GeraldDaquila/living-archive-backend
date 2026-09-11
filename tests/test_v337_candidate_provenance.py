"""v337 candidate-provenance diagnostic scaffolding.

This test is intentionally non-invasive: it proves the repository contains the
existing authority seams we need to observe, without changing production
behavior or asserting unverified live retrieval outcomes.
"""
import inspect

import use_core


GRIEF_QUERY = (
    "What advise or essay from the Living Archive that you can recommend "
    "for someone who is grieving from the death of a love one?"
)


def test_v337_candidate_provenance_seams_exist():
    assert use_core._is_recommendation_question(GRIEF_QUERY)
    assert callable(use_core._adjudicate_recommendation_resource)
    assert callable(use_core.select_canonical_doorways)
    source = inspect.getsource(use_core.fetch_canonical_context)
    assert "task_authority_recommendation = _adjudicate_recommendation_resource" in source
    assert "authoritative_recommendation=task_authority_recommendation" in source
    assert "v265 recommendation-to-doorway coherence" in source


def test_v337_recommendation_audit_fixture_is_present():
    source = inspect.getsource(use_core._v243_recommendation_directness_adjudication_self_audit)
    assert "Journey Beyond: Exploring the Afterlife and Reincarnation Through Hypnosis and Near-Death Experiences" in source
    assert "The Transformative Power of Loss: Finding Meaning in Grief Through Spiritual and Scientific Wisdom" in source
