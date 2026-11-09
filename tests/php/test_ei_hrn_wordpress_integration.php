<?php
/**
 * Real WordPress REST integration smoke tests for EI + HRN.
 * Run with: wp eval-file tests/php/test_ei_hrn_wordpress_integration.php
 * Uses disposable WordPress/database state and the repository's test-only
 * canonical-retriever stub. No production keys, endpoints, or corpus are used.
 */
function ei_hrn_assert($ok, $message) {
    if (!$ok) { fwrite(STDERR, "FAIL: {$message}\n"); exit(1); }
    echo "PASS: {$message}\n";
}
if (!function_exists('rest_do_request') || !class_exists('WP_REST_Request')) {
    throw new RuntimeException('This test requires a bootstrapped WordPress installation.');
}
do_action('rest_api_init');
$server = rest_get_server();
$routes = $server->get_routes();
ei_hrn_assert(isset($routes['/living-archive/v1/emergency-resources']), 'HRN resource-only route is registered by real WordPress REST bootstrap');
ei_hrn_assert(isset($routes['/living-archive/emergency/v1/status']), 'EI status route is registered by real WordPress REST bootstrap');
ei_hrn_assert(isset($routes['/living-archive/emergency/v1/resolve-bundle']), 'EI bundle resolver route is registered by real WordPress REST bootstrap');

$status = rest_do_request(new WP_REST_Request('GET', '/living-archive/emergency/v1/status'));
ei_hrn_assert($status->get_status() === 200, 'EI status endpoint responds through WordPress REST dispatch');
$status_data = $status->get_data();
ei_hrn_assert(is_array($status_data) && ($status_data['plugin_version'] ?? '') === '0.1.2', 'EI status payload is serialized by WordPress REST');

$req = new WP_REST_Request('POST', '/living-archive/v1/emergency-resources');
$req->set_header('content-type', 'application/json');
$req->set_body_params([
    'country' => 'Philippines',
    'safety_stage' => 'acute_contact',
    'safety_question' => 'Can you contact emergency support now?',
    'safety_message' => 'Please tell me which country you are in.'
]);
$response = rest_do_request($req);
ei_hrn_assert($response->get_status() === 200, 'HRN location-only route executes through real WordPress REST dispatch');
$data = $response->get_data();
ei_hrn_assert(is_array($data) && ($data['operation'] ?? '') === 'resource_location_resolution', 'HRN response retains resource-only operation marker');
ei_hrn_assert(($data['stage'] ?? '') === 'acute_contact', 'HRN active safety stage survives real REST dispatch');
ei_hrn_assert(($data['question'] ?? '') === 'Can you contact emergency support now?', 'HRN active safety question survives real REST dispatch');
ei_hrn_assert(($data['message'] ?? '') === 'Please tell me which country you are in.', 'HRN existing prompt survives real REST dispatch');
ei_hrn_assert(isset($data['resources']) && is_array($data['resources']), 'HRN response contains a structured resource list');
ei_hrn_assert(in_array(($data['resource_provenance'] ?? ''), ['ei_with_hrn_legacy_fallback','hrn_legacy_fallback'], true), 'HRN resource provenance is explicit');

$bad = new WP_REST_Request('POST', '/living-archive/v1/emergency-resources');
$bad->set_body_params([
    'country' => 'Philippines',
    'safety_stage' => 'acute_contact',
    'safety_question' => 'Can you contact emergency support now?',
    'safety_message' => 'Please tell me which country you are in.',
    'message' => 'Yes, I can contact someone.'
]);
$bad_response = rest_do_request($bad);
ei_hrn_assert($bad_response->get_status() === 400, 'visitor-answer field is rejected by the actual REST callback with HTTP 400');
$bad_data = $bad_response->get_data();
ei_hrn_assert(($bad_data['code'] ?? '') === 'lah_rn_visitor_content_not_accepted', 'visitor-answer rejection returns the expected WP_Error code');

$transcript = new WP_REST_Request('POST', '/living-archive/v1/emergency-resources');
$transcript->set_body_params([
    'country' => 'Philippines',
    'safety_stage' => 'acute_contact',
    'safety_question' => 'Can you contact emergency support now?',
    'safety_message' => 'Please tell me which country you are in.',
    'conversation' => 'Private visitor transcript'
]);
$transcript_response = rest_do_request($transcript);
ei_hrn_assert($transcript_response->get_status() === 400, 'conversation transcript is rejected by the actual REST callback');

$unknown = new WP_REST_Request('POST', '/living-archive/v1/emergency-resources');
$unknown->set_body_params([
    'country' => 'Atlantis',
    'safety_stage' => 'acute_contact',
    'safety_question' => 'Can you contact emergency support now?',
    'safety_message' => 'Please tell me which country you are in.'
]);
$unknown_response = rest_do_request($unknown);
ei_hrn_assert($unknown_response->get_status() === 400, 'unsupported country fails closed through real REST dispatch');

$invalid_stage = new WP_REST_Request('POST', '/living-archive/v1/emergency-resources');
$invalid_stage->set_body_params([
    'country' => 'Philippines',
    'safety_stage' => 'not-a-real-stage',
    'safety_question' => 'Can you contact emergency support now?',
    'safety_message' => 'Please tell me which country you are in.'
]);
$stage_response = rest_do_request($invalid_stage);
ei_hrn_assert($stage_response->get_status() === 400, 'invalid safety stage fails closed through real REST dispatch');

echo "All real WordPress EI-HRN REST integration smoke tests passed.\n";
