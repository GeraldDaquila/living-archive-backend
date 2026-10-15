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


def test_adjacent_resource_is_not_misrepresented_as_direct_coverage(monkeypatch):
    adjacent = _doc(
        "Stewardship Readiness",
        "https://geralddaquila.com/stewardship-readiness/",
        "This page offers progressive behavioral calibration, reflective "
        "assessment, and evidence-informed stewardship instruments. It discusses "
        "leadership, accountability, and institutional trust as parts of readiness."
    )
    monkeypatch.setattr(main, "_guide_node_registry_snapshot", lambda: [
        {"node_id":"adjacent", "status":"active", "title":adjacent["title"],
         "canonical_url":adjacent["url"], "purpose":"Leadership readiness",
         "semantic_hints":["stewardship readiness","leadership","institutional trust"]},
    ])
    doorway, evidence = main._guide_align_registered_discovery_doorway(SUBJECT, [adjacent])
    assert doorway is None
    assert evidence == []


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


def test_unregistered_canonical_page_cannot_authorize_discovery():
    direct = _doc(
        "Institutional Responsibility and Accountability",
        "https://geralddaquila.com/institutional-responsibility/",
        "Institutional responsibility concerns the duties of institutions, how "
        "they make decisions, and how they account for effects on the public. "
        "Institutional accountability includes transparent decisions and oversight."
    )
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
