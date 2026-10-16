"""Static boundary regression tests for the tracked HRN WordPress source.

These tests deliberately fail while Archive grounding overwrites relational
understanding. They do not claim to validate the inaccessible live plugin.
"""
from pathlib import Path
import re

HRN = Path(__file__).resolve().parents[1] / "wordpress/hrn/human-relational-navigator.php"


def _source():
    return HRN.read_text(encoding="utf-8")


def test_archive_grounding_must_not_overwrite_relational_understanding():
    source = _source()
    # Canonical grounding must be available as separate evidence, not as a
    # replacement for the visitor's own relational understanding.
    assert not re.search(
        r"\$validated\s*\[\s*['\"]relational_understanding['\"]\s*\]"
        r"\s*=\s*\$validated\s*\[\s*['\"]archive_grounded_understanding['\"]\s*\]",
        source,
    ), "Archive grounding overwrites the HRN relational-understanding channel"


def test_archive_resources_are_only_passed_for_explicit_resource_requests():
    source = _source()
    assert "$visitor_resource_request = $this->visitor_requests_resource($message);" in source
    assert "$composer_resources = $visitor_resource_request ? $resources : array();" in source


def test_frozen_hrn_voice_methods_remain_present():
    source = _source()
    for method in (
        "groq_compose",
        "groq_recover_composition",
        "structural_question_completion",
        "select_response_form",
    ):
        assert re.search(r"function\s+" + method + r"\s*\(", source), method
