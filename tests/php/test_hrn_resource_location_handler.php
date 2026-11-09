<?php
/**
 * Isolated execution tests for the HRN resource-only handler.
 * This is not a full WordPress bootstrap or browser/integration test.
 */
define('ABSPATH', __DIR__ . '/');
class WP_REST_Server { const CREATABLE = 'POST'; }
class WP_REST_Request {
    private $params;
    public function __construct($params) { $this->params = $params; }
    public function get_param($key) { return $this->params[$key] ?? null; }
}
class WP_Error {
    private $code; private $message; private $data;
    public function __construct($code, $message, $data = array()) { $this->code=$code; $this->message=$message; $this->data=$data; }
    public function get_error_code() { return $this->code; }
    public function get_error_data() { return $this->data; }
}
$GLOBALS['la_test_options'] = array();
$GLOBALS['la_test_routes'] = array();
$GLOBALS['la_test_ei_mode'] = 'selected';
$GLOBALS['la_test_ei_calls'] = array();
function get_option($key, $default = false) { return $GLOBALS['la_test_options'][$key] ?? $default; }
function update_option($key, $value, $autoload = null) { $GLOBALS['la_test_options'][$key] = $value; return true; }
function add_action(...$args) {}
function add_filter(...$args) {}
function add_shortcode(...$args) {}
function register_activation_hook(...$args) {}
function register_rest_route($namespace, $route, $args) { $GLOBALS['la_test_routes'][$namespace.$route] = $args; }
function sanitize_key($value) { return preg_replace('/[^a-z0-9_\\-]/', '', strtolower((string)$value)); }
function sanitize_text_field($value) { return trim(strip_tags((string)$value)); }
function rest_ensure_response($value) { return $value; }
function __return_true() { return true; }
function living_archive_emergency_resolve($need, $location, $stage, $policy) {
    $GLOBALS['la_test_ei_calls'][] = array($need, $location, $stage, $policy);
    if ($GLOBALS['la_test_ei_mode'] === 'throw') throw new RuntimeException('EI unavailable');
    if ($GLOBALS['la_test_ei_mode'] === 'empty') return array('selection'=>array('selection_status'=>'NO_MATCH'));
    if ($need === 'general_emergency') {
        if ($GLOBALS['la_test_ei_mode'] === 'equivalent') return array('registry_version'=>'test-registry', 'selection'=>array('selection_status'=>'MULTIPLE_EQUIVALENT','primary'=>array(
            array('number'=>'999','display_name'=>'Emergency services'),
            array('number'=>'112','display_name'=>'Emergency services')
        )));
        return array('registry_version'=>'test-registry', 'selection'=>array('selection_status'=>'SELECTED','primary'=>array('number'=>'911','display_name'=>'Emergency services')));
    }
    return array('registry_version'=>'test-registry', 'selection'=>array('selection_status'=>'NO_MATCH'));
}
require_once __DIR__ . '/../../plugins/human-relational-navigator/human-relational-navigator.php';

function assert_true($condition, $message) {
    if (!$condition) { fwrite(STDERR, "FAIL: ".$message."\n"); exit(1); }
    echo "PASS: ".$message."\n";
}
$hrn = Living_Archive_Human_Relational_Navigator::instance();
$question = 'Can you contact emergency or crisis support now?';
$safety_message = 'Please tell me which country you are in.';
$request = new WP_REST_Request(array('country'=>'United Kingdom','safety_stage'=>'acute_contact','safety_question'=>$question,'safety_message'=>$safety_message));
$GLOBALS['la_test_ei_mode'] = 'equivalent';
$GLOBALS['la_test_ei_calls'] = array();
$response = $hrn->resource_location_handler($request);
assert_true(is_array($response) && ($response['operation'] ?? '') === 'resource_location_resolution', 'resource-only handler executes and returns its operation marker');
assert_true(($response['stage'] ?? '') === 'acute_contact', 'active safety stage is preserved exactly');
assert_true(($response['question'] ?? '') === $question && ($response['safety_question'] ?? '') === $question, 'active safety question is preserved exactly');
assert_true(($response['message'] ?? '') === $safety_message, 'safety prompt text is preserved exactly');
$phones = array_values(array_filter(array_map(function($r){ return $r['phone'] ?? ''; }, $response['resources'] ?? array())));
assert_true(in_array('999', $phones, true) && in_array('112', $phones, true), 'equivalent emergency numbers are both retained');
assert_true(count($GLOBALS['la_test_ei_calls']) === 3, 'EI is queried for the three defined resource categories');
assert_true(($response['ei_registry_version'] ?? '') === 'test-registry', 'EI registry version is surfaced');

$GLOBALS['la_test_ei_mode'] = 'throw';
$GLOBALS['la_test_ei_calls'] = array();
$fallback = $hrn->resource_location_handler($request);
assert_true(is_array($fallback) && !empty($fallback['resources']), 'EI exception retains HRN legacy resources');
assert_true(($fallback['stage'] ?? '') === 'acute_contact' && ($fallback['question'] ?? '') === $question, 'EI outage does not alter the active safety stage or question');
assert_true(($fallback['resource_provenance'] ?? '') === 'hrn_legacy_fallback', 'EI outage is labelled as legacy fallback');

$GLOBALS['la_test_ei_mode'] = 'empty';
$unsupported = $hrn->resource_location_handler(new WP_REST_Request(array('country'=>'Atlantis','safety_stage'=>'acute_contact','safety_question'=>$question,'safety_message'=>$safety_message)));
assert_true(is_array($unsupported) && !empty($unsupported['resources']), 'unsupported country retains directory fallback resource');
assert_true(($unsupported['stage'] ?? '') === 'acute_contact', 'unsupported country does not change safety stage');

$invalid = $hrn->resource_location_handler(new WP_REST_Request(array('country'=>'PH','safety_stage'=>'not-a-stage','safety_question'=>$question,'safety_message'=>$safety_message)));
assert_true($invalid instanceof WP_Error && $invalid->get_error_code() === 'lah_rn_invalid_safety_stage', 'invalid safety stage fails closed');

$routes = $GLOBALS['la_test_routes'];
$route = $routes['living-archive/v1/emergency-resources'] ?? array();
assert_true(($route['permission_callback'] ?? '') === '__return_true', 'public route registration is explicit (rate limiting remains a separate security review)');
echo "All isolated HRN handler execution tests passed.\n";
