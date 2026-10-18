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


def test_selected_page_evidence_requires_registered_node_and_real_body_fit(monkeypatch):
    related = _doc(
        "Stewardship Readiness",
        "https://geralddaquila.com/stewardship-readiness/",
        "This page offers progressive behavioral calibration and reflective "
        "assessment. It discusses leadership, accountability, and institutional "
        "trust as parts of readiness."
    )
    doorway = {"title": related["title"], "url": related["url"]}
    monkeypatch.setattr(main, "_guide_node_registry_snapshot", lambda: [])
    assert main._guide_selected_doorway_discovery_evidence(
        [related], SUBJECT, doorway
    ) == []

    node = {
        "node_id": "adjacent", "status": "active",
        "title": related["title"], "canonical_url": related["url"],
        "purpose": "Leadership readiness and institutional trust",
        "semantic_hints": ["leadership", "institutional trust"],
    }
    verified = dict(related, _guide_node=node)
    evidence = main._guide_selected_doorway_discovery_evidence(
        [verified], SUBJECT, doorway
    )
    assert evidence and evidence[0]["_discovery_relevance"] == "related"


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


def test_single_body_mention_is_related_not_direct_on_a_broad_page(monkeypatch):
    document = _doc(
        "Leadership Challenge Navigator",
        "https://geralddaquila.com/leadership-challenge-navigator/",
        "This navigator supports leadership challenges and team decision-making. "
        "Institutional responsibility is one concern among many. The page focuses "
        "on leadership, accountability, institutional trust, communication, and "
        "working through difficult organizational choices."
    )
    node = {
        "node_id": "leadership", "status": "active",
        "title": "Leadership Challenge Navigator",
        "canonical_url": document["url"],
        "purpose": "Leadership challenges, accountability, and institutional trust",
        "semantic_hints": ["leadership", "accountability", "institutional trust"],
    }
    monkeypatch.setattr(
        main.use_core,
        "_question_evidence_fit_profile",
        lambda *_args, **_kwargs: (2, 0, [], 0),
    )
    grade = main._guide_discovery_evidence_grade(SUBJECT, document, node=node)
    assert grade["grade"] == "related"


def test_subject_explicit_registry_purpose_outranks_broad_related_node(monkeypatch):
    related = _doc(
        "Stewardship Readiness",
        "https://geralddaquila.com/stewardship-readiness/",
        "This page connects institutional responsibility with leadership, "
        "accountability, institutional trust, and stewardship practice. It offers "
        "a structured starting point for reflection on how organizations act."
    )
    broad = _doc(
        "Leadership Challenge Navigator",
        "https://geralddaquila.com/leadership-challenge-navigator/",
        "This page connects institutional responsibility with leadership, "
        "accountability, institutional trust, and stewardship practice. It offers "
        "a structured starting point for reflection on how organizations act."
    )
    monkeypatch.setattr(
        main.use_core,
        "_question_evidence_fit_profile",
        lambda *_args, **_kwargs: (2, 0, [], 0),
    )
    monkeypatch.setattr(main, "_guide_node_registry_snapshot", lambda: [
        {
            "node_id": "leadership", "status": "active",
            "title": broad["title"], "canonical_url": broad["url"],
            "purpose": "Leadership readiness and institutional trust",
            "semantic_hints": ["leadership", "institutional trust"],
        },
        {
            "node_id": "stewardship", "status": "active",
            "title": related["title"], "canonical_url": related["url"],
            "purpose": "Institutional responsibility, accountability, and stewardship readiness",
            "semantic_hints": ["institutional responsibility", "accountability", "stewardship"],
        },
    ])
    doorway, evidence = main._guide_align_registered_discovery_doorway(
        SUBJECT, [broad, related]
    )
    assert doorway is not None
    assert doorway["title"] == "Stewardship Readiness"
    assert evidence and evidence[0]["_discovery_relevance"] == "direct"


def test_repeated_incidental_mentions_do_not_make_registry_misaligned_page_direct(monkeypatch):
    broad = _doc(
        "Leadership Challenge Navigator",
        "https://geralddaquila.com/leadership-challenge-navigator/",
        "This navigator supports leadership challenges and team decision-making. "
        "Institutional responsibility appears as one example among several. "
        "Visitors may encounter institutional responsibility while reviewing "
        "leadership, accountability, institutional trust, and systems challenges. "
        "The page primarily helps readers choose leadership cases and learning arcs."
    )
    node = {
        "node_id": "leadership", "status": "active",
        "title": "Leadership Challenge Navigator",
        "canonical_url": broad["url"],
        "purpose": "Recognize the stewardship pattern beneath leadership, governance, institutional, or systems challenges.",
        "semantic_hints": ["leadership challenge", "governance challenge", "systems challenge"],
    }
    monkeypatch.setattr(
        main.use_core,
        "_question_evidence_fit_profile",
        lambda *_args, **_kwargs: (4, 0, [], 0),
    )
    grade = main._guide_discovery_evidence_grade(SUBJECT, broad, node=node)
    assert grade["grade"] == "related"



def test_political_dynasty_discovery_extracts_full_subject_without_search_wrapper():
    query = "Where can I find material about political dynasties in the Philippines?"
    subject = main._guide_subject_discovery_query(query)
    assert subject == "political dynasties in the Philippines"


def test_political_dynasty_direct_source_beats_broad_governance_resource(monkeypatch):
    query = "Where can I find material about political dynasties in the Philippines?"
    direct = _doc(
        "Political Dynasties in the Philippines",
        "https://geralddaquila.com/political-dynasties/",
        "Political dynasties in the Philippines shape local power, electoral "
        "competition, and access to public office. The concentration of family "
        "power can affect public accountability, institutional checks, and "
        "citizens' ability to hold elected officials responsible."
    )
    adjacent = _doc(
        "Good Governance and Public Institutions",
        "https://geralddaquila.com/good-governance/",
        "Good governance depends on transparent institutions, public "
        "accountability, fair processes, and effective oversight. These "
        "principles help citizens assess how public institutions exercise power."
    )
    monkeypatch.setattr(main, "_guide_node_registry_snapshot", lambda: [
        {
            "node_id": "dynasties",
            "status": "active",
            "title": direct["title"],
            "canonical_url": direct["url"],
            "purpose": "Political dynasties in the Philippines, local power, elections, and accountability",
            "semantic_hints": ["political dynasties", "Philippine politics", "public accountability"],
        },
        {
            "node_id": "governance",
            "status": "active",
            "title": adjacent["title"],
            "canonical_url": adjacent["url"],
            "purpose": "Good governance and accountable public institutions",
            "semantic_hints": ["good governance", "public institutions", "accountability"],
        },
    ])
    subject = main._guide_subject_discovery_query(query)
    doorway, evidence = main._guide_align_registered_discovery_doorway(
        subject, [adjacent, direct]
    )
    assert doorway is not None
    assert doorway["title"] == direct["title"]
    assert evidence and evidence[0]["url"] == direct["url"]
    assert evidence[0]["_discovery_relevance"] == "direct"


def test_political_dynasty_query_rejects_governance_only_candidate():
    query = "How do political dynasties affect public accountability in the Philippines?"
    governance_only = _doc(
        "Good Governance and Public Institutions",
        "https://geralddaquila.com/good-governance/",
        "Good governance depends on transparent institutions, public "
        "accountability, fair processes, and effective oversight in the Philippines."
    )
    assert not main._topic_specific_candidate_fit(query, governance_only)


def test_political_dynasty_query_accepts_opening_that_supports_distinctive_subject():
    query = "How do political dynasties affect public accountability in the Philippines?"
    direct = _doc(
        "Political Dynasties in the Philippines",
        "https://geralddaquila.com/political-dynasties/",
        "Political dynasties in the Philippines shape local power and elections. "
        "Public accountability and institutional checks affect how elected "
        "officials are held responsible."
    )
    assert main._topic_specific_candidate_fit(query, direct)
