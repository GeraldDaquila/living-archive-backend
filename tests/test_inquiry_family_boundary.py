from pathlib import Path


SOURCE = Path("general_guide_composition.py").read_text()


def test_inquiry_family_boundary_rejects_template_transfer_by_theme_alone():
    assert "INQUIRY-FAMILY BOUNDARY" in SOURCE
    assert "Gold Stars transfer discipline, not answer templates" in SOURCE
    assert "institutional decisions" in SOURCE
    assert "comparative, cultural, spiritual" in SOURCE


def test_comparative_spiritual_inquiry_has_its_own_response_boundary():
    assert "comparative questions about spiritual, religious, philosophical, or cultural traditions" in SOURCE
    assert "respect from uncritical acceptance" in SOURCE
    assert "approach each tradition on its own terms" in SOURCE
    assert "Do not import organisational outcomes, responsibilities, consequences, or decision-accountability templates" in SOURCE
