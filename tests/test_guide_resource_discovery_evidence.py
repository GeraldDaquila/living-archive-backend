"""
Resource discovery QA for The Guide.

Subject discovery must rank the strongest source-supported resource, distinguish
direct coverage from adjacent overlap, and never make a registry doorway eligible
on metadata alone.
"""
import main


QUERY = "Where can I find material about institutional responsibility?"
SUBJECT = "institutional responsibility"


def _doc(title, url, text):
    return {"title": title, "url": url, "text": text}


def test_find_material_intent_keeps_subject_and_discards_search_wrapper():
    assert main._guide_subject_discovery_query(QUERY) == SUBJECT
    assert main._guide_subject_discovery_query(
        "Please find useful resources related to institutional accountability."
    ) == "institutional accountability"


def test_registered_direct_resource_wins_over_adjacent_stewardship_resource(monkeypatch):
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
    monkeypatch.setattr(main, "_guide_node_registry_snapshot", lambda: [
        {"node_id":"direct", "status":"active", "title":direct["title"],
         "canonical_url":direct["url"], "purpose":"Institutional responsibility duties and accountability",
         "semantic_hints":["institutional responsibility","institutional accountability"]},
        {"node_id":"adjacent", "status":"active", "title":adjacent["title"],
         "canonical_url":adjacent["url"], "purpose":"Leadership readiness",
         "semantic_hints":["stewardship readiness","leadership","institutional trust"]},
    ])
    doorway, evidence = main._guide_align_registered_discovery_doorway(
        SUBJECT, [adjacent, direct]
    )
    assert doorway is not None
    assert doorway["title"] == "Institutional Responsibility and Accountability"
    assert evidence and evidence[0]["url"] == direct["url"]
    assert evidence[0]["_discovery_relevance"] == "direct"

    # When the direct page is absent, the same registry may supply a related
    # destination, but it must never outrank a direct body match.
    related_only, related_evidence = main._guide_align_registered_discovery_doorway(
        SUBJECT, [adjacent]
    )
    assert related_only is not None
    assert related_only["title"] == "Stewardship Readiness"
    assert related_evidence[0]["_discovery_relevance"] == "related"




def test_only_one_shared_word_without_registered_context_is_weak():
    document = _doc(
        "General Leadership",
        "https://geralddaquila.com/general-leadership/",
        "A general overview of leadership and personal development for teams."
    )
    grade = main._guide_discovery_evidence_grade(SUBJECT, document, node=None)
    assert grade["grade"] == "weak"

def test_related_resource_can_be_offered_only_with_related_grade(monkeypatch):
    adjacent = _doc(
        "Stewardship Readiness",
        "https://geralddaquila.com/stewardship-readiness/",
        "This page offers progressive behavioral calibration, reflective "
        "assessment, and evidence-informed stewardship instruments. It discusses "
        "leadership, accountability, and institutional trust as parts of readiness."
    )
    monkeypatch.setattr(main, "_guide_node_registry_snapshot", lambda: [
        {"node_id":"adjacent", "status":"active", "title":adjacent["title"],
         "canonical_url":adjacent["url"], "purpose":"Leadership readiness and institutional trust",
         "semantic_hints":["stewardship readiness","leadership","institutional trust"]},
    ])
    doorway, evidence = main._guide_align_registered_discovery_doorway(SUBJECT, [adjacent])
    assert doorway is not None
    assert doorway["title"] == "Stewardship Readiness"
    assert evidence and evidence[0]["_discovery_relevance"] == "related"
    response = main._guide_deterministic_discovery_response(SUBJECT, doorway, evidence)
    assert "didn’t verify a page that directly covers institutional responsibility" in response
    assert "related starting point" in response
    assert "does not establish that the page directly treats institutional responsibility" in response


def test_weak_resource_fails_closed_when_only_title_or_metadata_overlaps(monkeypatch):
    weak = _doc(
        "Institutional Responsibility",
        "https://geralddaquila.com/institutional-responsibility/",
        "A broad introduction to reflective leadership and personal development."
    )
    monkeypatch.setattr(main, "_guide_node_registry_snapshot", lambda: [
        {"node_id":"weak", "status":"active", "title":weak["title"],
         "canonical_url":weak["url"], "purpose":"Personal development",
         "semantic_hints":["institutional responsibility"]},
    ])
    doorway, evidence = main._guide_align_registered_discovery_doorway(SUBJECT, [weak])
    assert doorway is None
    assert evidence == []


def test_unregistered_canonical_page_cannot_authorize_discovery(monkeypatch):
    direct = _doc(
        "Institutional Responsibility and Accountability",
        "https://geralddaquila.com/institutional-responsibility/",
        "Institutional responsibility concerns the duties of institutions, how "
        "they make decisions, and how they account for effects on the public. "
        "Institutional accountability includes transparent decisions and oversight."
    )
    monkeypatch.setattr(main, "_guide_node_registry_snapshot", lambda: [])
    doorway, evidence = main._guide_align_registered_discovery_doorway(SUBJECT, [direct])
    assert doorway is None
    assert evidence == []


def test_discovery_answer_explains_a_related_starting_point_only_if_verified():
    related = _doc(
        "Stewardship Readiness",
        "https://geralddaquila.com/stewardship-readiness/",
        "This page offers progressive behavioral calibration and reflective "
        "assessment. It discusses leadership, accountability, and institutional "
        "trust as parts of readiness."
    )
    doorway = {"title":related["title"],"url":related["url"]}
    # No page excerpt or lexical overlap should be enough to claim direct coverage.
    assert main._guide_selected_doorway_discovery_evidence([related], SUBJECT, doorway) == []


def test_multi_concept_subject_fit_guard_remains_additive():
    query = (
        "How do political dynasties, public institutions, and local accountability "
        "interact in the Philippines?"
    )
    direct = _doc(
        "Political Dynasties in the Philippines",
        "https://geralddaquila.com/political-dynasties/",
        "Political dynasties shape local power. Public institutions can be "
        "weakened when accountability is limited. Local accountability and "
        "institutional checks affect how governance works."
    )
    assert main._topic_specific_candidate_fit(query, direct)
