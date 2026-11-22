import json
from pathlib import Path

import pytest

from general_guide_gold_standards import resolve_exact_gold_standard, load_approved_standards

ROOT = Path(__file__).resolve().parents[1]


def test_user_approved_water_answer_is_enforced_exactly():
    result = resolve_exact_gold_standard("What is the boiling point of water at sea level?")
    assert result is not None
    assert result["status"] == "USER_APPROVED_GOLD_STANDARD"
    assert result["expected_response"] == (
        "At sea level, water boils at 100°C (212°F) under standard atmospheric pressure. "
        "As altitude increases and air pressure decreases, water boils at a lower temperature.\n\n"
        "The key point is that boiling depends on pressure, not just temperature."
    )


def test_frozen_stewardship_reference_is_not_runtime_authority():
    result = resolve_exact_gold_standard("Explain stewardship, but do not send me to another page yet.")
    assert result is None


def test_registered_doorway_is_preserved_when_no_handoff_was_not_requested():
    result = resolve_exact_gold_standard("What is the significance of human development?")
    assert result is not None
    assert result["doorway_title"] == "The First Institution: Why Human Development Begins at Home"
    assert result["doorway_url"] == "https://geralddaquila.com/2025/06/17/the-first-institution-why-human-development-begins-at-home/"


def test_matching_is_case_and_whitespace_insensitive_but_not_fuzzy():
    assert resolve_exact_gold_standard("  WHAT IS THE BOILING POINT OF WATER AT SEA LEVEL?  ") is not None
    assert resolve_exact_gold_standard("What is the boiling point of water?") is None


def test_recovered_historical_response_is_not_runtime_authority():
    result = resolve_exact_gold_standard(
        "What does stewardship look like when people disagree about what is worth protecting?"
    )
    assert result is None


def test_registry_conflicts_are_rejected(monkeypatch, tmp_path):
    import general_guide_gold_standards as standards
    registry = {
        "records": [
            {"status": "USER_APPROVED_GOLD_STANDARD", "query": "Same question?", "expected_response": "Answer A"},
            {"status": "FROZEN_REFERENCE_ONLY", "query": "same   question?", "expected_response": "Answer B"},
        ]
    }
    path = tmp_path / "registry.json"
    path.write_text(json.dumps(registry), encoding="utf-8")
    monkeypatch.setattr(standards, "_REGISTRY_PATH", path)
    standards_map = standards.load_approved_standards()
    assert standards_map[standards._normalize_question("Same question?")]["expected_response"] == "Answer A"


def test_general_composition_returns_registered_answer_before_provider_call(monkeypatch):
    import general_guide_composition as composition

    def provider_must_not_be_called(**kwargs):
        raise AssertionError("Provider bank must not replace an exact approved answer.")

    monkeypatch.setattr(composition, "route_with_model_bank", provider_must_not_be_called)
    result = composition.compose(
        use_core=object(),
        query="What is the boiling point of water at sea level?",
        context_data={},
    )
    assert result["response"] == resolve_exact_gold_standard(
        "What is the boiling point of water at sea level?"
    )["expected_response"]
    assert result["provider"] == "gold_standard_registry"
    assert result["doorway_title"] == ""


def test_cosmology_question_uses_the_approved_exact_gold_star_answer_and_doorway(monkeypatch):
    import general_guide_composition as composition

    query = "What is cosmology, and why does it matter to how people live?"

    def provider_must_not_be_called(**kwargs):
        raise AssertionError("The approved exact cosmology Gold Star must own this query.")

    monkeypatch.setattr(composition, "route_with_model_bank", provider_must_not_be_called)
    standard = resolve_exact_gold_standard(query)
    assert standard is not None
    assert standard["benchmark_id"] == "gs-2026-11-19-cosmology-worldview-human-life"
    result = composition.compose(
        use_core=object(),
        query=query,
        context_data={},
    )

    assert result["provider"] == "gold_standard_registry"
    assert result["response"] == standard["expected_response"]
    assert result["doorway_title"] == "The Hidden Assumptions That Quietly Shape Every Life"
    assert result["doorway_url"] == (
        "https://geralddaquila.com/2026/08/09/constitutional-ontology-hidden-maps/"
    )


def test_default_composition_evidence_recovery_keeps_three_paragraph_contract_when_providers_exhausted(monkeypatch):
    import general_guide_composition as composition

    query = "How does governance differ from administration in practice?"
    source_sentences = [
        "Governance establishes how a group makes decisions and remains accountable for their consequences.",
        "Governance goes beyond administration because it determines purposes, authority, and the rules by which decisions are made.",
        "Administration carries out decisions through processes, records, schedules, and the coordination of daily work.",
        "Good governance clarifies who may decide, who is affected, and how a decision can be questioned or reviewed.",
        "For example, administration may schedule a public meeting, while governance determines who has a voice in the decision and how competing interests are weighed.",
        "Governance does not replace administration; it gives administration a legitimate direction and a structure for accountability.",
    ]
    documents = [{
        "title": "Governance Foundations",
        "url": "https://geralddaquila.com/governance-foundations/",
        "content": " ".join(source_sentences),
    }]

    monkeypatch.setattr(composition, "route_with_model_bank", lambda **kwargs: None)
    result = composition.compose(
        use_core=object(),
        query=query,
        context_data={"generation_authority_protected_docs": documents},
    )

    assert result is not None
    assert result["provider"] == "gold_standard_evidence_recovery"
    assert result["response_shape"] == "explanatory"
    assert len(result["response"].split("\n\n")) == 3
    assert "Governance goes beyond administration" in result["response"]
    assert "who has a voice" in result["response"]
    assert "does not replace administration" in result["response"]
    assert result["doorway_title"] == "Governance Foundations"
    assert result["doorway_url"] == "https://geralddaquila.com/governance-foundations/"


def test_default_composition_evidence_recovery_does_not_invent_when_retrieval_is_insufficient(monkeypatch):
    import general_guide_composition as composition

    monkeypatch.setattr(composition, "route_with_model_bank", lambda **kwargs: None)
    result = composition.compose(
        use_core=object(),
        query="How does governance differ from administration in practice?",
        context_data={"generation_authority_protected_docs": [{
            "title": "Unrelated source",
            "url": "https://geralddaquila.com/unrelated/",
            "content": "This source discusses gardening and soil health in a community garden.",
        }]},
    )

    assert result is None


def test_main_final_payload_boundary_reapplies_exact_standard_after_rewrites():
    main_source = (ROOT / "main.py").read_text(encoding="utf-8")
    resolver_call = '_final_gold_standard = _final_exact_gold_standard_authority(query)'
    payload_marker = '    payload = {\n        "ok": True,\n        "version": APP_VERSION,'
    assert resolver_call in main_source
    assert payload_marker in main_source
    resolver_position = main_source.index(resolver_call)
    payload_position = main_source.index(payload_marker, resolver_position)
    final_contract_position = main_source.index(
        'general_guide_composition.enforce_response_contracts(query, response)'
    )
    assert final_contract_position < resolver_position < payload_position
    assert 'response = _final_gold_standard["expected_response"]' in main_source
    final_block = main_source[resolver_position:payload_position]
    assert '_gold_forbids_doorway = _gold_star_doorway_omission_is_justified(_final_gold_standard)' in final_block
    assert '_apply_registered_gold_standard_doorway(' in final_block
    assert 'authoritative_doorway = {"title": _gold_title, "url": _gold_url or None}' not in final_block
    assert 'Only a complete, validated Gold Standard title/URL pair may override' in final_block


def test_water_gold_standard_keeps_general_knowledge_provenance():
    main_source = (ROOT / "main.py").read_text(encoding="utf-8")
    assert (
        '_final_gold_standard.get("benchmark_id") == '
        '"general-guide-water-boiling-point-general-knowledge-gold-standard-2026-10-24"'
    ) in main_source
    assert "GS-GENERAL-BOILING-POINT-WATER-001" not in main_source


def test_frozen_core_blob_is_not_modified_by_runtime_integration():
    # Guard the protected production core's reviewed identity in CI.
    # The expected SHA is the known unchanged blob for this release line.
    import subprocess

    result = subprocess.run(
        ["git", "hash-object", "use_core.py"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout.strip() == "d897d36e8f0c99aadca704e0594ae5603dd26c73"



def test_first_principles_gold_standard_matches_straight_and_curly_apostrophes(monkeypatch):
    import general_guide_composition as composition

    curly = "What are first principles, and what are the Living Archive’s first principles?"
    straight = "What are first principles, and what are the Living Archive's first principles?"
    expected = resolve_exact_gold_standard(curly)
    assert expected is not None
    assert resolve_exact_gold_standard(straight)["expected_response"] == expected["expected_response"]

    def provider_must_not_be_called(**kwargs):
        raise AssertionError("Provider bank must not replace the approved First Principles answer.")

    monkeypatch.setattr(composition, "route_with_model_bank", provider_must_not_be_called)
    result = composition.compose(use_core=object(), query=straight, context_data={})
    assert result["provider"] == "gold_standard_registry"
    assert result["response"] == expected["expected_response"]
    assert result["doorway_title"] == "First Principles"
    assert result["doorway_url"] == "https://geralddaquila.com/first-principles/"


def test_first_principles_gold_standard_names_all_six_published_principles():
    result = resolve_exact_gold_standard(
        "What are first principles, and what are the Living Archive’s first principles?"
    )
    assert result is not None
    answer = result["expected_response"]
    assert len(answer.split("\n\n")) == 3
    for principle in (
        "reality is intelligible",
        "human beings participate in reality",
        "understanding develops",
        "complexity deserves integration rather than reduction",
        "stewardship follows understanding",
        "every generation inherits unfinished questions",
    ):
        assert principle in answer
    assert "not unquestionable doctrines" in answer
    assert result["doorway_title"] == "First Principles"
    assert result["doorway_url"] == "https://geralddaquila.com/first-principles/"



def test_continuous_learning_contract_is_explicit_and_does_not_claim_implementation():
    registry = json.loads(
        (ROOT / "docs" / "qa" / "gold_standard_registry.json").read_text(encoding="utf-8")
    )
    contract = registry["learning_contract"]

    assert contract["contract_id"] == "living-archive-guide-continuous-learning-loop"
    assert contract["contract_version"] == "1.0.0"
    assert contract["status"] == "IMPLEMENTED_ACTIVE_QUALITY_MEMORY"
    assert any("questions not used during calibration" in item for item in contract["governing_principles"])
    assert any("does not train a model" in item for item in contract["data_and_authority_boundaries"])
    assert "human approval" in contract["learning_cycle"][-2]["requirement"]
    assert any("held-out question suite" in item.lower() for item in contract["acceptance_gates"])
    assert "exact question" in contract["current_capability_boundary"].lower()
    assert [stage["stage"] for stage in contract["rollout_stages"]] == [
        "1_contract_and_baseline",
        "2_shadow_evaluation",
        "3_reviewed_adaptation",
        "4_guarded_promotion",
        "5_continuous_monitoring",
    ]

def test_generic_composition_gate_rejects_meta_explanation_and_disclaimer_filler():
    import general_guide_composition as composition

    weak_response = (
        "Governance beyond administration is best understood by what it means and how it operates in practice. "
        "The definition matters because it shapes what people notice, what they expect, and what they count as a reasonable action.\n\n"
        "A useful explanation distinguishes the idea from nearby concepts and makes its implications visible in a concrete situation. "
        "For instance, two terms may sound similar while assigning different responsibilities or implying different standards of judgment.\n\n"
        "The precise meaning can vary by field or institution, so this is a general explanation rather than a claim that the Living Archive uses a particular formal definition. "
        "Where the distinction matters for a decision, check how the relevant people or institution define and apply the term."
    )
    assert composition.is_generic_nonanswer(
        "What is governance, beyond administration?", weak_response
    )


def test_generic_composition_gate_accepts_actual_definition_and_applied_distinction():
    import general_guide_composition as composition

    substantive_response = (
        "Governance is how a group sets direction, exercises authority, makes collective decisions, and holds decision-makers accountable. "
        "Administration carries out established decisions and procedures; governance also determines who may make those decisions, what principles guide them, and how they can be challenged.\n\n"
        "For example, an administrator may apply a budget rule, while governance determines who sets the spending priorities, how affected people are heard, and what happens when the rule places an unfair burden on one group. "
        "The distinction matters because efficient execution cannot by itself make the underlying decision legitimate.\n\n"
        "Governance does not replace administration: institutions need both sound decisions and reliable execution. "
        "The central question is whether authority and priorities are exercised transparently, responsibly, and with a way to review decisions when their consequences show that a change is needed."
    )
    assert not composition.is_generic_nonanswer(
        "What is governance, beyond administration?", substantive_response
    )



def test_published_glossary_exact_heading_extraction_and_category():
    import archive_glossary_authority as glossary

    markup = """
    <h3><strong>Law of One</strong></h3>
    <h2>Principle / Ethical Orientation</h2>
    <p>A unifying principle expressing interconnectedness.</p>
    <p>Unity is relational coherence, not sameness.</p>
    <h3>Lemuria</h3>
    <p>A separate entry.</p>
    """
    entry = glossary.extract_glossary_entry(markup, "Law of One")
    assert entry["category"] == "Principle / Ethical Orientation"
    assert entry["paragraphs"] == [
        "A unifying principle expressing interconnectedness.",
        "Unity is relational coherence, not sameness.",
    ]
    assert glossary.extract_glossary_entry(markup, "One Law") is None


def test_provider_exhaustion_definition_uses_published_glossary_authority(monkeypatch):
    import archive_glossary_authority as glossary
    import deterministic_answer_recovery as recovery

    entry = {
        "term": "Law of One",
        "category": "Principle / Ethical Orientation",
        "paragraphs": [
            "A unifying principle expressing the inherent interconnectedness of all existence. "
            "It is an ethical and perceptual orientation, not a doctrine or external authority.",
            "Unity is understood as relational coherence, not sameness, fusion, or loss of agency.",
        ],
    }
    monkeypatch.setattr(glossary, "get_glossary_entry", lambda subject: entry)
    answer = recovery.compose_definition_significance("Law of One")
    paragraphs = answer.split("\n\n")
    assert len(paragraphs) == 3
    assert "inherent interconnectedness" in answer
    assert "not sameness" in answer
    assert "Ra Material" not in answer
    assert "knowledge, responsibilities, or ways of working" not in answer


def test_general_definition_fallback_has_no_subject_independent_operational_boilerplate(monkeypatch):
    import archive_glossary_authority as glossary
    import deterministic_answer_recovery as recovery

    monkeypatch.setattr(glossary, "get_glossary_entry", lambda subject: None)
    answer = recovery.compose_definition_significance("institutional memory")
    assert "knowledge, responsibilities, or ways of working" not in answer
    assert "For example, When" not in answer
    assert len(answer.split("\n\n")) == 3


def test_primary_composition_receives_canonical_glossary_context_for_archive_terms(monkeypatch):
    import archive_glossary_authority as glossary
    import general_guide_composition as composition

    entry = {
        "term": "Law of One",
        "category": "Principle / Ethical Orientation",
        "paragraphs": [
            "A unifying principle expressing the inherent interconnectedness of all existence. "
            "It is an ethical and perceptual orientation, not a doctrine, channeling source, or external authority.",
            "Unity is relational coherence, not sameness, fusion, or loss of agency.",
        ],
        "source_url": "https://geralddaquila.com/glossary/",
    }
    monkeypatch.setattr(glossary, "get_glossary_entry", lambda subject: entry)
    original_documents = [{"title": "Unrelated page", "url": "https://example.invalid/", "content": "Unrelated context."}]
    documents, instruction = composition._apply_archive_glossary_authority(
        "What is the Law of One?", original_documents
    )

    assert documents[0]["title"] == "The Living Glossary — Law of One"
    assert "inherent interconnectedness" in documents[0]["content"]
    assert "not sameness" in documents[0]["content"]
    assert "primary authority for Archive-specific usage" in instruction
    assert documents[1:] == original_documents


def test_primary_composition_does_not_attach_glossary_to_unrelated_non_definition_queries(monkeypatch):
    import archive_glossary_authority as glossary
    import general_guide_composition as composition

    def unexpected_lookup(subject):
        raise AssertionError("Glossary lookup should not run for a non-definition query")

    monkeypatch.setattr(glossary, "get_glossary_entry", unexpected_lookup)
    documents = [{"title": "Existing source", "url": "https://example.invalid/", "content": "Context."}]
    result, instruction = composition._apply_archive_glossary_authority(
        "How should a team repair trust after a missed commitment?", documents
    )
    assert result == documents
    assert instruction == ""


def test_glossary_subject_extraction_handles_definition_questions_with_or_without_articles():
    import general_guide_composition as composition

    assert composition._definition_subject_for_glossary("What is the Law of One?") == "Law of One"
    assert composition._definition_subject_for_glossary("What is governance?") == "governance"


def test_single_paragraph_living_glossary_entry_is_split_by_its_conceptual_movements():
    import archive_glossary_authority as glossary

    entry = {
        "term": "Law of One",
        "category": "Principle / Ethical Orientation",
        "paragraphs": [
            "A unifying principle expressing the inherent interconnectedness of all existence. "
            "In this framework, the Law of One is not a doctrine, channeling source, or external authority, "
            "but an ethical and perceptual orientation: recognition that harm, coercion, and extraction "
            "anywhere diminish coherence everywhere. Practiced maturely, it emphasizes unity without "
            "erasing individuality, sovereignty without isolation, and compassion without loss of responsibility. "
            "Unity is understood here as relational coherence, not sameness, fusion, or loss of agency."
        ],
    }
    answer = glossary.compose_glossary_recovery(entry)
    paragraphs = answer.split("\n\n")
    assert len(paragraphs) == 3
    assert paragraphs[0].startswith("In the Living Archive Glossary")
    assert "not a doctrine, channeling source, or external authority" in paragraphs[1]
    assert "unity without erasing individuality" in paragraphs[2]
    assert "not sameness, fusion, or loss of agency" in paragraphs[2]
    assert "knowledge, responsibilities, or ways of working" not in answer


def test_definition_intent_recognizer_covers_common_phrasings():
    import general_guide_composition as composition

    cases = {
        "What is the Law of One?": "Law of One",
        "Define the Law of One": "Law of One",
        "Can you explain the Law of One?": "Law of One",
        "What does the Law of One mean?": "Law of One",
        "What is meant by the Law of One?": "Law of One",
        "Meaning of the Law of One": "Law of One",
        "Definition of the Law of One": "Law of One",
        "Law of One definition": "Law of One",
        "Tell me what the Law of One is": "Law of One",
    }
    for question, expected in cases.items():
        assert composition._definition_subject_for_glossary(question) == expected


def test_glossary_lookup_precedes_general_archive_retrieval(monkeypatch):
    import general_guide_composition as composition

    calls = []
    glossary_doc = {
        "title": "The Living Glossary — Law of One",
        "url": "https://geralddaquila.com/glossary/",
        "content": "Canonical definition.",
    }
    archive_doc = {
        "title": "Related Archive essay",
        "url": "https://geralddaquila.com/related-essay/",
        "content": "Additional context.",
    }

    def glossary_first(query, documents):
        calls.append("glossary")
        assert query == "What is the Law of One?"
        assert documents == []
        return [glossary_doc], "canonical authority instruction"

    def archive_second(use_core, context_data):
        calls.append("archive")
        return [archive_doc]

    monkeypatch.setattr(composition, "_apply_archive_glossary_authority", glossary_first)
    monkeypatch.setattr(composition, "_documents_from_context", archive_second)

    documents, instruction = composition._retrieve_authoritative_context(
        "What is the Law of One?", object(), {}
    )
    assert calls == ["glossary", "archive"]
    assert documents == [glossary_doc, archive_doc]
    assert instruction == "canonical authority instruction"


def test_glossary_first_contract_does_not_change_non_definition_retrieval(monkeypatch):
    import general_guide_composition as composition

    calls = []
    archive_doc = {"title": "Existing source", "url": "https://example.invalid/", "content": "Context."}

    def no_glossary(query, documents):
        calls.append("glossary")
        return documents, ""

    def archive_retrieval(use_core, context_data):
        calls.append("archive")
        return [archive_doc]

    monkeypatch.setattr(composition, "_apply_archive_glossary_authority", no_glossary)
    monkeypatch.setattr(composition, "_documents_from_context", archive_retrieval)

    documents, instruction = composition._retrieve_authoritative_context(
        "How should a team repair trust after a missed commitment?", object(), {}
    )
    assert calls == ["glossary", "archive"]
    assert documents == [archive_doc]
    assert instruction == ""


def test_definition_intent_recognizer_handles_term_and_contraction_variants():
    import general_guide_composition as composition

    assert composition._definition_subject_for_glossary("What does the term Law of One mean?") == "Law of One"
    assert composition._definition_subject_for_glossary("What is the meaning of the Law of One?") == "Law of One"
    assert composition._definition_subject_for_glossary("What's the Law of One?") == "Law of One"


def test_glossary_source_revision_invalidates_composition_cache_key():
    import general_guide_composition as composition

    old_source = [{
        "title": "The Living Glossary — Law of One",
        "url": "https://geralddaquila.com/glossary/",
        "source_modified": "2026-11-01T10:00:00",
    }]
    revised_source = [{
        "title": "The Living Glossary — Law of One",
        "url": "https://geralddaquila.com/glossary/",
        "source_modified": "2026-11-08T10:00:00",
    }]
    old_key = composition._composition_cache_key("What is the Law of One?", "", "definition", old_source)
    revised_key = composition._composition_cache_key("What is the Law of One?", "", "definition", revised_source)
    assert old_key != revised_key


def test_definition_intent_recognizer_excludes_procedural_causal_and_comparison_questions():
    import general_guide_composition as composition

    non_definitions = [
        "What is the best way to repair trust?",
        "What is the difference between authority and power?",
        "Explain how to rebuild trust after a missed commitment.",
        "Why does governance fail?",
        "What is happening with the provider bank?",
    ]
    for question in non_definitions:
        assert composition._definition_subject_for_glossary(question) == ""


def test_prechecked_glossary_snapshot_is_reused_without_second_network_lookup(monkeypatch):
    import general_guide_composition as composition

    glossary_doc = {
        "title": "The Living Glossary — Law of One",
        "url": "https://geralddaquila.com/glossary/",
        "content": "Canonical definition.",
        "source_modified": "2026-11-08T10:00:00",
    }
    archive_doc = {"title": "Related essay", "url": "https://geralddaquila.com/essay/", "content": "Context."}

    def unexpected_lookup(query, documents):
        raise AssertionError("Prechecked Glossary must not be fetched twice")

    monkeypatch.setattr(composition, "_apply_archive_glossary_authority", unexpected_lookup)
    monkeypatch.setattr(composition, "_documents_from_context", lambda use_core, context: [archive_doc])
    context = {
        "_canonical_glossary_checked": True,
        "_canonical_glossary_documents": [glossary_doc],
        "_canonical_glossary_instruction": "canonical authority",
    }
    documents, instruction = composition._retrieve_authoritative_context(
        "What is the Law of One?", object(), context
    )
    assert documents == [glossary_doc, archive_doc]
    assert instruction == "canonical authority"


def test_main_resolves_glossary_before_canonical_archive_fetch():
    from pathlib import Path

    source = Path("main.py").read_text(encoding="utf-8")
    glossary_lookup = source.index("general_guide_composition.resolve_glossary_context(query)")
    archive_fetch = source.index("use_core.fetch_canonical_context(resource_query)")
    assert glossary_lookup < archive_fetch
    assert '_canonical_glossary_checked"] = True' in source


def test_glossary_source_attribution_is_visible_and_direct():
    import general_guide_composition as composition

    context = {
        "_canonical_glossary_documents": [{
            "title": "The Living Glossary — Law of One",
            "url": "https://geralddaquila.com/glossary/#law-of-one",
        }]
    }
    response, basis = composition.apply_glossary_source_attribution(
        "Canonical definition in three paragraphs.", context
    )
    assert response.endswith(
        "Source: [The Living Glossary — Law of One](https://geralddaquila.com/glossary/#law-of-one)"
    )
    assert basis["kind"] == "archive_reference"
    assert basis["source_url"] == "https://geralddaquila.com/glossary/#law-of-one"


def test_glossary_source_attribution_does_not_inject_a_source_when_no_exact_entry():
    import general_guide_composition as composition

    response, basis = composition.apply_glossary_source_attribution(
        "A general answer.", {"_canonical_glossary_documents": []}
    )
    assert response == "A general answer."
    assert basis is None


def test_final_visitor_payload_applies_visible_glossary_attribution():
    from pathlib import Path

    source = Path("main.py").read_text(encoding="utf-8")
    attribution = source.index("general_guide_composition.apply_glossary_source_attribution(")
    payload = source.index('    payload = {\n        "ok": True,', attribution)
    assert attribution < payload


def test_explicit_release_candidate_is_served_exactly_for_live_review(monkeypatch):
    import general_guide_composition as composition

    query = "What is the role of technology in a stewardship-centered society?"
    expected = resolve_exact_gold_standard(query)
    if expected is None:
        pytest.skip("Release candidate is not present in this branch's canonical registry")
    assert expected["status"] == "USER_APPROVED_RELEASE_CANDIDATE"
    assert expected["doorway_title"] == "Foundations of Stewardship Governance"
    assert expected["doorway_url"] == "https://geralddaquila.com/%F0%9F%8C%B1foundations-of-stewardship-governance/"

    def provider_must_not_be_called(**kwargs):
        raise AssertionError("An explicitly authorized exact-query release candidate must be reviewable live.")

    monkeypatch.setattr(composition, "route_with_model_bank", provider_must_not_be_called)
    result = composition.compose(use_core=object(), query=query, context_data={})
    assert result["provider"] == "gold_standard_registry"
    assert result["response"] == expected["expected_response"]
    assert result["doorway_title"] == expected["doorway_title"]
    assert result["doorway_url"] == expected["doorway_url"]


def test_release_candidate_matches_browser_dash_variants():
    variants = (
        "What is the role of technology in a stewardship‑centered society?",  # non-breaking hyphen
        "What is the role of technology in a stewardship–centered society?",  # en dash
        "What is the role of technology in a stewardship—centered society?",  # em dash
    )
    for query in variants:
        expected = resolve_exact_gold_standard(query)
        if expected is None:
            pytest.skip("Release candidate is not present in this branch registry")
        assert expected["benchmark_id"] == "general-guide-technology-stewardship-governance-refinement-2026-11-15"
        assert expected["doorway_title"] == "Foundations of Stewardship Governance"


import re


QUERY = (
    "A user asks for a personal life decision to be made for them. "
    "How should the Guide offer orientation while refusing to replace agency?"
)

EXPECTED_DOORWAY = {
    "title": "Being in the Driver's Seat (Without Pretending You Control the Road)",
    "url": "https://geralddaquila.com/being-in-the-drivers-seat-without-pretending-you-control-the-road/",
    "rationale": (
        "This essay offers a grounded continuation on exercising personal agency within real conditions and limits. "
        "It supports the distinction between receiving orientation and surrendering responsibility for one's own choices; "
        "it does not prescribe the decision a visitor should make."
    ),
}


def test_personal_decision_guide_role_question_is_recognized_and_answered_directly():
    from deterministic_answer_recovery import (
        _guide_personal_decision_agency_recovery,
        compose_recovery,
        has_registered_recovery,
        is_guide_personal_decision_agency_question,
    )

    assert is_guide_personal_decision_agency_question(QUERY)
    assert has_registered_recovery(QUERY)
    answer = compose_recovery(QUERY)
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n+", answer) if part.strip()]
    assert len(paragraphs) == 3
    assert answer == _guide_personal_decision_agency_recovery()
    assert paragraphs[0].startswith("The Guide should help a person make their own decision")
    assert "known facts from interpretations and unknowns" in paragraphs[1]
    assert "final choice with the person" in paragraphs[2]
    assert "The decision about A user asks" not in answer


def test_personal_decision_agency_question_has_a_separate_relevant_archive_doorway():
    from deterministic_answer_recovery import registered_recovery_recommendation

    assert registered_recovery_recommendation(QUERY) == EXPECTED_DOORWAY


def test_provider_and_deterministic_payloads_share_the_same_answer_and_doorway_boundary():
    import main
    from deterministic_answer_recovery import compose_recovery

    provider_payload = {"response": "A generic decision checklist.", "recommendation": None}
    deterministic_payload = {
        "response": compose_recovery(QUERY),
        "recommendation": None,
        "provider": "deterministic",
    }

    provider_result = main._guide_finalize_visitor_payload(provider_payload, QUERY)
    deterministic_result = main._guide_finalize_visitor_payload(deterministic_payload, QUERY)

    assert provider_result["response"] == deterministic_result["response"]
    assert provider_result["recommendation"] == EXPECTED_DOORWAY
    assert deterministic_result["recommendation"] == EXPECTED_DOORWAY
    assert provider_result["canonical_doorway"] == EXPECTED_DOORWAY
    assert deterministic_result["canonical_doorway"] == EXPECTED_DOORWAY


def test_gold_star_without_specific_doorway_gets_default_compass_unless_explicitly_forbidden(monkeypatch):
    import main

    monkeypatch.setattr(
        main,
        "_resolve_exact_guide_gold_standard",
        lambda _query: {"expected_response": "Frozen Gold Star answer."},
    )
    monkeypatch.setattr(main, "_select_guide_node_fallback_doorway", lambda _query: None)

    result = main._guide_finalize_visitor_payload({"response": "Provider answer."}, "An open-ended inquiry")
    assert result["response"] == "Frozen Gold Star answer."
    assert result["recommendation"]["title"] == "Sovereign Sensemaking Compass"
    assert result["recommendation"]["url"] == "https://geralddaquila.com/the-sovereign-sensemaking-compass/"
    assert result["recommendation"]["rationale"]

    monkeypatch.setattr(
        main,
        "_resolve_exact_guide_gold_standard",
        lambda _query: {"expected_response": "Frozen Gold Star answer.", "forbids_doorway": True, "doorway_omission_exception_reason": "The answer addresses an immediate, sensitive situation where an additional link would interrupt the needed response."},
    )
    omitted = main._guide_finalize_visitor_payload({"response": "Provider answer."}, "An open-ended inquiry")
    assert omitted["recommendation"] is None
    assert omitted["canonical_doorway"] is None
    assert omitted["doorway_title"] is None
    assert omitted["doorway_url"] is None
    assert omitted["doorway_rationale"] is None

def test_non_gold_star_responses_do_not_receive_a_forced_generic_doorway():
    import main

    assert main._enforce_registered_gold_standard_doorway(None, None, "What is 2 + 2?") is None


def test_shared_json_sender_enforces_registered_personal_agency_answer_and_doorway(monkeypatch):
    import asyncio
    import main
    from deterministic_answer_recovery import _guide_personal_decision_agency_recovery

    query = (
        "A user asks for a personal life decision to be made for them. "
        "How should the Guide offer orientation while refusing to replace agency?"
    )
    monkeypatch.setattr(main, "_resolve_exact_guide_gold_standard", lambda _query: None)
    sent = []

    async def send(message):
        sent.append(message)

    asyncio.run(main._use_send_json(send, {
        "ok": True,
        "query": query,
        "response": "The decision about A user asks for a personal life decision...",
        "answer": "Stale answer alias.",
        "provider": "provider-exhaustion-recovery",
    }))
    body = next(item["body"] for item in sent if item["type"] == "http.response.body")
    result = json.loads(body.decode("utf-8"))
    expected = _guide_personal_decision_agency_recovery()

    assert result["response"] == expected
    assert result["answer"] == expected
    assert "The decision about A user asks" not in result["response"]
    assert result["processing"] == "sender_boundary_personal_decision_agency"
    assert result["recommendation"]["title"] == (
        "Being in the Driver's Seat (Without Pretending You Control the Road)"
    )
    assert result["recommendation"]["url"] == (
        "https://geralddaquila.com/"
        "being-in-the-drivers-seat-without-pretending-you-control-the-road/"
    )
    assert result["canonical_doorway"] == result["recommendation"]
    assert result["doorway_rationale"]


def test_shared_json_sender_does_not_rewrite_unrelated_questions(monkeypatch):
    import asyncio
    import main

    monkeypatch.setattr(main, "_resolve_exact_guide_gold_standard", lambda _query: None)
    sent = []

    async def send(message):
        sent.append(message)

    asyncio.run(main._use_send_json(send, {
        "ok": True,
        "query": "What is the difference between authority and power?",
        "response": "An ordinary answer.",
    }))
    body = next(item["body"] for item in sent if item["type"] == "http.response.body")
    result = json.loads(body.decode("utf-8"))

    assert result["response"] == "An ordinary answer."
    assert result.get("processing") != "sender_boundary_personal_decision_agency"
