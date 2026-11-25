from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_cosmology_recovery_establishes_scientific_and_philosophical_domains_first():
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    start = source.index("    _cosmology_lived_question = bool(")
    end = source.index("    # Bounded relational uncertainty recovery.", start)
    block = source[start:end]

    science = block.index("In science, it is the study of the universe as a whole")
    philosophy = block.index("In philosophy and ordinary human reflection")
    worldview = block.index("A worldview is not the same thing as scientific cosmology")
    archive = block.index("The Living Archive explores one such interpretation")

    assert science < philosophy < worldview < archive
    assert "not scientific findings that prove one worldview correct" in block
    assert "should not be confused with the scientific discipline of cosmology" in block


def test_cosmology_lived_question_does_not_receive_unverified_glossary_doorway():
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    assert "No directly relevant canonical cosmology resource has been verified" in source
    assert "None if _cosmology_doorway_not_verified" in source


def test_general_guide_contract_requires_subject_first_domain_distinction():
    source = (ROOT / "general_guide_composition.py").read_text(encoding="utf-8")
    assert "SUBJECT-FIRST CONCEPTUAL EXPLANATION" in source
    assert "scientific cosmology—the study of the universe as a whole" in source
    assert "label it as the Archive's interpretation" in source
    assert "Resolve every part of a compound question." in source
