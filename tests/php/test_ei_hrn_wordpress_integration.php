<?php
/**
 * Real WordPress REST integration tests for the EI-only emergency resource boundary.
 * Run with: wp eval-file tests/php/test_ei_hrn_wordpress_integration.php
 * Uses disposable WordPress/database state. Registry mutation is in-memory only.
 */
function ei_hrn_assert($ok, $message) {
    if (!$ok) { fwrite(STDERR, "FAIL: {$message}\n"); exit(1); }
    echo "PASS: {$message}\n";
}
if (!function_exists('rest_do_request') || !class_exists('WP_REST_Request')) {
    throw new RuntimeException('This test requires a bootstrapped WordPress installation.');
}
if (!class_exists('LAEI_Registry') || !defined('LAEI_REGISTRY_FILE')) {
    throw new RuntimeException('The EI plugin and registry must be loaded for this integration test.');
}

do_action('rest_api_init');
$server = rest_get_server();
$routes = $server->get_routes();
ei_hrn_assert(isset($routes['/living-archive/v1/emergency-resources']), 'HRN resource-only adapter route is registered');
ei_hrn_assert(isset($routes['/living-archive/emergency/v1/status']), 'EI status route is registered');
ei_hrn_assert(isset($routes['/living-archive/emergency/v1/resolve-bundle']), 'EI bundle resolver route is registered');

$status = rest_do_request(new WP_REST_Request('GET', '/living-archive/emergency/v1/status'));
ei_hrn_assert($status->get_status() === 200, 'EI status endpoint responds through WordPress REST dispatch');
$status_data = $status->get_data();
ei_hrn_assert(is_array($status_data) && ($status_data['plugin_version'] ?? '') === '0.1.3', 'EI status payload is serialized by WordPress REST');

$_SERVER['HTTP_CF_IPCOUNTRY'] = 'PH';
$unconfirmed = new WP_REST_Request('POST', '/living-archive/v1/relational-navigator');
$unconfirmed->set_header('content-type', 'application/json');
$unconfirmed->set_body_params([
    'message' => 'I want to kill myself.',
    'safety_stage' => 'green'
]);
$unconfirmed_response = rest_do_request($unconfirmed);
ei_hrn_assert($unconfirmed_response->get_status() === 200, 'safety interrupt responds when only IP-derived country evidence is available');
$unconfirmed_data = $unconfirmed_response->get_data();
ei_hrn_assert(($unconfirmed_data['safety_resources'] ?? null) === [], 'IP-derived country alone cannot produce callable EI resources');
ei_hrn_assert(!empty($unconfirmed_data['safety_location_required']), 'IP-derived country alone requires explicit country confirmation');
ei_hrn_assert(($unconfirmed_data['safety_resource_provenance'] ?? '') === 'ei_location_resolution_pending', 'unconfirmed location keeps EI resource resolution pending');
unset($_SERVER['HTTP_CF_IPCOUNTRY']);

$interrupt = new WP_REST_Request('POST', '/living-archive/v1/relational-navigator');
$interrupt->set_header('content-type', 'application/json');
$interrupt->set_body_params([
    'message' => 'I want to kill myself.',
    'safety_stage' => 'green',
    'country' => 'Philippines'
]);
$interrupt_response = rest_do_request($interrupt);
ei_hrn_assert($interrupt_response->get_status() === 200, 'deterministic HRN safety interrupt responds through WordPress REST');
$interrupt_data = $interrupt_response->get_data();
ei_hrn_assert(!empty($interrupt_data['safety_interrupt']), 'explicit safety signal interrupts ordinary interpretation');
ei_hrn_assert(!empty($interrupt_data['safety_resources']), 'HRN safety interrupt can return current resources resolved by EI');
ei_hrn_assert(empty($interrupt_data['safety_location_required']), 'known country does not trigger a redundant location prompt');
ei_hrn_assert(($interrupt_data['safety_resource_provenance'] ?? '') === 'ei_verified_only', 'HRN safety interrupt identifies EI as the sole resource authority');
foreach (($interrupt_data['safety_resources'] ?? []) as $resource) {
    ei_hrn_assert(($resource['verification_status'] ?? '') === 'verified_by_ei', 'every callable safety resource is marked as selected by EI verification');
}

$canonical = json_decode(file_get_contents(LAEI_REGISTRY_FILE), true);
if (!is_array($canonical)) throw new RuntimeException('Canonical EI registry fixture could not be loaded.');
$registry_property = new ReflectionProperty('LAEI_Registry', 'registry');
$registry_property->setAccessible(true);
function ei_hrn_set_registry($property, $fixture) {
    $property->setValue(null, $fixture);
}
function ei_hrn_request($country = 'Philippines') {
    $req = new WP_REST_Request('POST', '/living-archive/v1/emergency-resources');
    $req->set_header('content-type', 'application/json');
    $req->set_body_params([
        'country' => $country,
        'safety_stage' => 'acute_contact',
        'safety_question' => 'Can you contact emergency support now?',
        'safety_message' => 'Please contact emergency or crisis support now.'
    ]);
    return rest_do_request($req);
}
function ei_hrn_no_callable_resources($response, $message) {
    ei_hrn_assert($response->get_status() === 200, $message . ': route remains available');
    $data = $response->get_data();
    ei_hrn_assert(is_array($data) && ($data['operation'] ?? '') === 'resource_location_resolution', $message . ': response retains resource-only operation');
    ei_hrn_assert(($data['resources'] ?? null) === [], $message . ': no unverified or legacy resource is exposed');
    ei_hrn_assert(($data['resource_provenance'] ?? '') === 'ei_no_verified_fallback', $message . ': response identifies EI-only fail-closed outcome');
    ei_hrn_assert(!empty($data['note']), $message . ': safe explanatory guidance is supplied');
    return $data;
}

// Current verified resource: EI alone authorizes the callable action.
ei_hrn_set_registry($registry_property, $canonical);
$response = ei_hrn_request('Philippines');
ei_hrn_assert($response->get_status() === 200, 'verified Philippines resource request succeeds');
$data = $response->get_data();
ei_hrn_assert(($data['resource_provenance'] ?? '') === 'ei_verified_only', 'callable resource provenance identifies EI as sole authority');
ei_hrn_assert(count($data['resources'] ?? []) > 0, 'current verified EI resources are returned');
$phones = array_values(array_filter(array_map(function($r) { return $r['phone'] ?? ''; }, $data['resources'] ?? [])));
ei_hrn_assert(in_array('911', $phones, true), 'current verified Philippines emergency number is returned from EI');

// Expired verification must not be replaced by the legacy HRN number.
$expired = $canonical;
foreach ($expired['verification_records'] as &$record) {
    if (in_array(($record['verification_id'] ?? ''), ['VER-PH-911-2026','VER-PH-NCMH-2026'], true)) $record['review_due'] = '2026-11-08';
}
unset($record);
ei_hrn_set_registry($registry_property, $expired);
$expired_data = ei_hrn_no_callable_resources(ei_hrn_request('Philippines'), 'expired EI verification');

// Missing provenance must not be replaced by the legacy HRN number.
$missing_provenance = $canonical;
foreach ($missing_provenance['verification_records'] as &$record) {
    if (in_array(($record['verification_id'] ?? ''), ['VER-PH-911-2026','VER-PH-NCMH-2026'], true)) $record['source_urls'] = [];
}
unset($record);
ei_hrn_set_registry($registry_property, $missing_provenance);
$provenance_data = ei_hrn_no_callable_resources(ei_hrn_request('Philippines'), 'missing EI source provenance');

// Explicitly unverified records must not yield callable resources.
$unverified = $canonical;
foreach ($unverified['verification_records'] as &$record) {
    if (in_array(($record['verification_id'] ?? ''), ['VER-PH-911-2026','VER-PH-NCMH-2026'], true)) $record['status'] = 'unverified';
}
unset($record);
ei_hrn_set_registry($registry_property, $unverified);
$unverified_data = ei_hrn_no_callable_resources(ei_hrn_request('Philippines'), 'unverified EI record');

// No active matching EI resource: do not fall back to the legacy registry.
$no_active = $canonical;
foreach ($no_active['resources'] as &$resource) {
    if (($resource['country_id'] ?? '') === 'PH') $resource['status'] = 'retired';
}
unset($resource);
ei_hrn_set_registry($registry_property, $no_active);
$no_active_data = ei_hrn_no_callable_resources(ei_hrn_request('Philippines'), 'no active EI resource');

// Unsupported country must not cause an HRN registry telephone fallback.
ei_hrn_set_registry($registry_property, $canonical);
$unsupported_data = ei_hrn_no_callable_resources(ei_hrn_request('Japan'), 'country not covered by the EI registry');

// The adapter boundary continues to reject visitor answers and transcripts.
ei_hrn_set_registry($registry_property, $canonical);
$bad = new WP_REST_Request('POST', '/living-archive/v1/emergency-resources');
$bad->set_body_params([
    'country' => 'Philippines',
    'safety_stage' => 'acute_contact',
    'safety_question' => 'Can you contact emergency support now?',
    'safety_message' => 'Please contact emergency or crisis support now.',
    'message' => 'Yes, I can contact someone.'
]);
$bad_response = rest_do_request($bad);
ei_hrn_assert($bad_response->get_status() === 400, 'visitor-answer field is rejected by the actual REST callback');
ei_hrn_assert(($bad_response->get_data()['code'] ?? '') === 'lah_rn_visitor_content_not_accepted', 'visitor-answer rejection returns the expected WP_Error code');

$transcript = new WP_REST_Request('POST', '/living-archive/v1/emergency-resources');
$transcript->set_body_params([
    'country' => 'Philippines',
    'safety_stage' => 'acute_contact',
    'safety_question' => 'Can you contact emergency support now?',
    'safety_message' => 'Please contact emergency or crisis support now.',
    'conversation' => 'Private visitor transcript'
]);
$transcript_response = rest_do_request($transcript);
ei_hrn_assert($transcript_response->get_status() === 400, 'conversation transcript is rejected by the actual REST callback');

$unknown_payload = new WP_REST_Request('POST', '/living-archive/v1/emergency-resources');
$unknown_payload->set_body_params([
    'country' => 'Philippines',
    'safety_stage' => 'acute_contact',
    'safety_question' => 'Can you contact emergency support now?',
    'safety_message' => 'Please contact emergency or crisis support now.',
    'unregistered_payload' => 'Unrecognized content must be rejected.'
]);
$unknown_payload_response = rest_do_request($unknown_payload);
ei_hrn_assert($unknown_payload_response->get_status() === 400, 'arbitrary unregistered fields are rejected by the strict REST input allowlist');

// Restore the canonical in-memory registry for any subsequent tests in this process.
ei_hrn_set_registry($registry_property, $canonical);

echo "All EI-only fail-closed WordPress REST integration tests passed.\n";
