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


def test_adapter_uses_ei_as_the_only_callable_resource_authority():
    source = HRN_PHP.read_text(encoding="utf-8")
    start = source.index("public function resource_location_handler")
    end = source.index("public function add_runtime_timing_headers", start)
    adapter = source[start:end]
    helper_start = source.index("private function resolve_ei_resource_bundle(")
    helper_end = source.index("private function safety_response(", helper_start)
    helper = source[helper_start:helper_end]

    assert "$this->resolve_ei_resource_bundle($country, $stage)" in adapter
    assert "function_exists('living_archive_emergency_resolve')" in helper
    assert "defined('LAEI_VERSION')" in helper
    assert "version_compare((string)LAEI_VERSION, '0.1.3', '>=')" in helper
    assert "living_archive_emergency_resolve($need" in helper
    assert "array('general_emergency', 'medical', 'crisis_support')" in helper
    assert "$selection_status === 'SELECTED'" in helper
    assert "$selection_status === 'MULTIPLE_EQUIVALENT'" in helper
    assert "$candidates = $selection['primary']" in helper
    assert "message" not in helper
    assert "conversation" not in helper
    assert "visitor_history" not in helper
    assert "$this->safety_resource_bundle(" not in adapter
    assert "$legacy" not in adapter
    assert "'resource_provenance'=>$bundle['resource_provenance']" in adapter
    assert "'resource_status'=>$bundle['resource_status']" in adapter


def test_hrn_does_not_treat_ip_country_detection_as_explicit_user_location():
    source = HRN_PHP.read_text(encoding="utf-8")
    assert "$country_explicit = ($country !== '')" in source
    assert "$safety_resource_country = $country_explicit ? $country : ''" in source
    assert "$this->safety_response($direct_stage, $safety_resource_country, $message)" in source


def test_initial_hrn_safety_response_uses_ei_or_requests_location_without_legacy_fallback():
    source = HRN_PHP.read_text(encoding="utf-8")
    start = source.index("private function safety_response(")
    end = source.index("private function safety_answer_class(", start)
    response = source[start:end]

    assert "$this->resolve_ei_resource_bundle($country_code, $stage)" in response
    assert "'resources'=>$bundle['resources']" in response
    assert "'location_required'=>($country_code === '')" in response
    assert "'resource_provenance'=>$bundle['resource_provenance']" in response
    assert "$this->safety_resource_bundle(" not in response
    assert "native_registry" not in response
    assert "findahelpline_fallback" not in response


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
    assert "if(response.country)country=String(response.country)" in source
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
