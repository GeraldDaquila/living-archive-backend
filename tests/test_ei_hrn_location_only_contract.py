"""Source-contract tests for the isolated EI/HRN location-only resource operation."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HRN_PHP = ROOT / "plugins/human-relational-navigator/human-relational-navigator.php"
HRN_JS = ROOT / "plugins/human-relational-navigator/assets/relational-navigator.js"


def test_location_route_is_separate_from_conversation_route():
    source = HRN_PHP.read_text(encoding="utf-8")
    assert "'/emergency-resources'" in source
    assert "'callback' => array($this, 'resource_location_handler')" in source
    assert "'emergency_endpoint' => esc_url_raw(rest_url(self::REST_NS . '/emergency-resources'))" in source


def test_resource_adapter_never_enters_hrn_safety_answer_or_conversation_pipeline():
    source = HRN_PHP.read_text(encoding="utf-8")
    start = source.index("public function resource_location_handler")
    end = source.index("public function add_runtime_timing_headers", start)
    adapter = source[start:end]

    for forbidden in (
        "safety_answer_class(",
        "safety_transition(",
        "rest_handler_inner(",
        "get_param('message')",
        "get_param('conversation')",
        "get_param('visitor_history')",
    ):
        assert forbidden not in adapter

    assert "'stage'=>$stage" in adapter
    assert "'safety'=>$stage" in adapter
    assert "'question'=>$question" in adapter
    assert "'safety_question'=>$question" in adapter
    assert "'message'=>$message" in adapter


def test_adapter_uses_ei_first_and_retains_legacy_continuity_fallback():
    source = HRN_PHP.read_text(encoding="utf-8")
    start = source.index("public function resource_location_handler")
    end = source.index("public function add_runtime_timing_headers", start)
    adapter = source[start:end]

    assert "function_exists('living_archive_emergency_resolve')" in adapter
    assert "living_archive_emergency_resolve($need" in adapter
    assert "array('general_emergency', 'medical', 'crisis_support')" in adapter
    assert "($selection['selection_status'] ?? '') !== 'SELECTED'" in adapter
    assert "$this->safety_resource_bundle($country, $stage, '')" in adapter
    assert "foreach (($legacy['resources'] ?? array()) as $resource)" in adapter


def test_frontend_location_submission_sends_no_visitor_answer_or_transcript():
    source = HRN_JS.read_text(encoding="utf-8")
    start = source.index("function submitSafetyLocation(v)")
    end = source.index("function returnCompletedJourneyToGuide", start)
    submit = source[start:end]

    assert "LAHRN.emergency_endpoint" in submit
    assert "country:v" in submit
    assert "safety_stage:safetyStage" in submit
    assert "safety_question:safetyQuestion" in submit
    assert "safety_message:safetyMessage" in submit
    for forbidden in ("message:v", "conversation:", "visitor_history:"):
        assert forbidden not in submit


def test_frozen_hrn_safety_methods_remain_present():
    source = HRN_PHP.read_text(encoding="utf-8")
    for method in (
        "deterministic_safety_signal",
        "explicit_suicide_language",
        "safety_answer_class",
        "safety_transition",
        "safety_response",
        "rest_handler_inner",
    ):
        assert f"function {method}(" in source
