"""Regression tests for evidence-grounded subject resource discovery."""
import main


QUERY = "Where can I find material about institutional responsibility?"
SUBJECT = main._guide_subject_discovery_query(QUERY)


def _doc(title, url, text):
    return {"title": title, "url": url, "text": text}


def test_resource_finding_query_is_reduced_to_subject_not_search_wrapper():
    assert SUBJECT == "institutional responsibility"


def test_direct_institutional_responsibility_evidence_outranks_adjacent_stewardship():
    direct = _doc(
        "Institutional Responsibility and Accountability",
        "https://geralddaquila.com/institutional-responsibility/",
        "Institutional responsibility concerns the duties of institutions, how "
        "they make decisions, and how they account for effects on the public. "
        "Institutional accountability includes transparent decisions, oversight, "
        "and remedies when an institution fails to meet its duties."
    )
    adjacent = _doc(
        "Stewardship Readiness",
        "https://geralddaquila.com/stewardship-readiness/",
        "This page offers progressive behavioral calibration, reflective "
        "assessment, and evidence-informed stewardship instruments. It discusses "
        "leadership, accountability, and institutional trust as parts of readiness."
    )
    doorway, evidence = main._guide_align_registered_discovery_doorway(
        SUBJECT, [adjacent, direct]
    )
    assert doorway is not None
    assert doorway["title"] == "Institutional Responsibility and Accountability"
    assert evidence and evidence[0]["url"] == direct["url"]


def test_related_resource_is_not_misrepresented_as_direct_coverage():
    adjacent = _doc(
        "Stewardship Readiness",
        "https://geralddaquila.com/stewardship-readiness/",
        "This page offers progressive behavioral calibration, reflective "
        "assessment, and evidence-informed stewardship instruments. It discusses "
        "leadership, accountability, and institutional trust as parts of readiness."
    )
    doorway, evidence = main._guide_align_registered_discovery_doorway(
        SUBJECT, [adjacent]
    )
    # A related resource is not enough to claim the subject is directly covered.
    assert doorway is None
    assert evidence == []


def test_no_verified_resource_fails_closed_without_inventing_a_doorway():
    weak = _doc(
        "Stewardship Readiness",
        "https://geralddaquila.com/stewardship-readiness/",
        "Reflective assessment and personal development for better leadership."
    )
    doorway, evidence = main._guide_align_registered_discovery_doorway(
        SUBJECT, [weak]
    )
    assert doorway is None
    assert evidence == []


def test_multi_concept_topic_regression_remains_intact():
    query = (
        "How do political dynasties, public institutions, and local accountability "
        "interact in the Philippines?"
    )
    direct = _doc(
        "Political Dynasties in the Philippines",
        "https://geralddaquila.com/political-dynasties/",
        "Political dynasties shape local power. Public institutions can be "
        "weakened when accountability is limited."
    )
    assert main._topic_specific_candidate_fit(query, direct)
