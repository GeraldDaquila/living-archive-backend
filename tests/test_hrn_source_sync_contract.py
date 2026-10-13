"""Regression guard for the live-synchronized HRN missing-question boundary."""

from pathlib import Path


HRN_SOURCE = Path(__file__).resolve().parents[1] / "wordpress" / "hrn" / "human-relational-navigator.php"


def test_hrn_source_is_synchronized_to_live_release_and_advances_sequentially():
    source = HRN_SOURCE.read_text(encoding="utf-8")
    assert "Version: 0.5.311" in source
    assert "const VERSION = '0.5.311';" in source
    assert "RELEASE v0.5.311: complete missing opening questions" in source
    assert "RELEASE v0.5.310: use the visitor's specific-incident sequence" in source


def test_natural_feared_conversation_gets_grounded_question_completion():
    source = HRN_SOURCE.read_text(encoding="utf-8")
    assert "$feared_conversation =" in source
    assert r"\\b(?:conversation|talk|speaking|telling)\\b" in source
    assert r"\\b(?:afraid|fear|worried|worry|putting off|hesitat(?:e|ing)|change|lose|damage|ruin)\\b" in source
    assert "What part of the friendship are you most afraid might change if you have that conversation?" in source
    assert "What feels most at stake for you in having that conversation?" in source


def test_question_completion_remains_inside_existing_policy_gates():
    source = HRN_SOURCE.read_text(encoding="utf-8")
    insertion = source.index("$feared_conversation =")
    policy_loop = source.index("foreach ($fallbacks as $fallback)", insertion)
    policy_end = source.index("return $fallback;", policy_loop)
    gate = source[policy_loop:policy_end]
    assert "$this->question_is_generic_or_compound($fallback)" in gate
    assert "$this->question_prescriptive_violation($fallback)" in gate
    assert "$this->question_is_repeated($fallback, $history)" in gate
    assert "$this->question_semantically_aligned($fallback, $response, $message, $base_state)" in gate
