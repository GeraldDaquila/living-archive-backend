<?php
/**
 * Real disposable WordPress REST integration for standalone EI.
 * Run with: wp eval-file wp-content/test_ei_wordpress_rest_integration.php
 */
function ei_wp_assert($condition, $message) {
    if (!$condition) {
        fwrite(STDERR, "FAIL: " . $message . "\n");
        exit(1);
    }
    echo "PASS: " . $message . "\n";
}

$server = rest_get_server();
$routes = $server->get_routes();
$resolve_route = '/living-archive/emergency/v1/resolve';
$status_route = '/living-archive/emergency/v1/status';

ei_wp_assert(isset($routes[$resolve_route]), 'standalone EI resolve route registers in real WordPress REST bootstrap');
ei_wp_assert(isset($routes[$status_route]), 'standalone EI status route registers in real WordPress REST bootstrap');
ei_wp_assert(!class_exists('Living_Archive_Human_Relational_Navigator'), 'EI integration test does not load or depend on HRN');

$request = new WP_REST_Request('POST', $resolve_route);
$request->set_param('service_need', 'general_emergency');
$request->set_param('safety_state', 'acute');
$request->set_param('location', ['explicit_country' => 'PH']);
$response = rest_do_request($request);
ei_wp_assert(!is_wp_error($response), 'valid EI resource request does not return a WordPress error');
ei_wp_assert($response->get_status() === 200, 'valid EI resource request returns HTTP 200');
$data = $response->get_data();
ei_wp_assert(($data['engine_version'] ?? '') === '0.1.3', 'REST response identifies the standalone EI engine version');
ei_wp_assert(($data['registry_version'] ?? '') === '2026.11.09.001', 'REST response identifies the local canonical registry version');
ei_wp_assert(($data['selection']['selection_status'] ?? '') === 'SELECTED', 'verified Philippines emergency resource is selected');
ei_wp_assert(($data['presentation']['actions'][0]['value'] ?? '') === '911', 'verified Philippines emergency resource produces its telephone action');

$unknown = new WP_REST_Request('POST', $resolve_route);
$unknown->set_param('service_need', 'general_emergency');
$unknown->set_param('safety_state', 'acute');
$unknown->set_param('location', []);
$unknown_response = rest_do_request($unknown);
$unknown_data = $unknown_response->get_data();
ei_wp_assert(($unknown_data['selection']['selection_status'] ?? '') === 'LOCATION_REQUIRED', 'unknown location requests location confirmation');
ei_wp_assert(empty($unknown_data['presentation']['actions']), 'unknown location produces no callable telephone action');

$refused = new WP_REST_Request('POST', $resolve_route);
$refused->set_param('service_need', 'general_emergency');
$refused->set_param('safety_state', 'acute');
$refused->set_param('location', ['explicit_country' => 'PH', 'refused' => true]);
$refused_response = rest_do_request($refused);
$refused_data = $refused_response->get_data();
ei_wp_assert(($refused_data['selection']['selection_status'] ?? '') === 'LOCATION_REFUSED', 'refused location remains an explicit refusal state');
ei_wp_assert(empty($refused_data['presentation']['actions']), 'refused location produces no callable telephone action');

$unsupported = new WP_REST_Request('POST', $resolve_route);
$unsupported->set_param('service_need', 'general_emergency');
$unsupported->set_param('safety_state', 'acute');
$unsupported->set_param('location', ['explicit_country' => 'Japan']);
$unsupported_response = rest_do_request($unsupported);
$unsupported_data = $unsupported_response->get_data();
ei_wp_assert(($unsupported_data['selection']['selection_status'] ?? '') === 'UNSUPPORTED_COUNTRY', 'unsupported explicit country is distinguished from unknown location');
ei_wp_assert(empty($unsupported_data['presentation']['actions']), 'unsupported country produces no callable telephone action');

$get_resolve = new WP_REST_Request('GET', $resolve_route);
$get_response = rest_do_request($get_resolve);
ei_wp_assert($get_response->get_status() >= 400, 'resource resolution route rejects GET requests');

$status_response = rest_do_request(new WP_REST_Request('GET', $status_route));
ei_wp_assert($status_response->get_status() === 200, 'read-only EI status route responds successfully');

$visitor_content = new WP_REST_Request('POST', $resolve_route);
$visitor_content->set_param('service_need', 'general_emergency');
$visitor_content->set_param('location', ['explicit_country' => 'PH']);
$visitor_content->set_param('message', 'This visitor answer must not enter EI.');
$visitor_content_response = rest_do_request($visitor_content);
ei_wp_assert($visitor_content_response->get_status() === 400, 'EI rejects visitor message content at the REST boundary');

$extra_location = new WP_REST_Request('POST', $resolve_route);
$extra_location->set_param('service_need', 'general_emergency');
$extra_location->set_param('location', ['explicit_country' => 'PH', 'visitor_history' => 'not accepted']);
$extra_location_response = rest_do_request($extra_location);
ei_wp_assert($extra_location_response->get_status() === 400, 'EI rejects transcript-like fields inside location context');

$oversized_location = new WP_REST_Request('POST', $resolve_route);
$oversized_location->set_param('service_need', 'general_emergency');
$oversized_location->set_param('location', ['explicit_country' => str_repeat('P', 81)]);
$oversized_location_response = rest_do_request($oversized_location);
ei_wp_assert($oversized_location_response->get_status() === 400, 'EI rejects overlength location values');

$invalid_service = new WP_REST_Request('POST', $resolve_route);
$invalid_service->set_param('service_need', 'not_a_real_service');
$invalid_service->set_param('location', ['explicit_country' => 'PH']);
$invalid_service_response = rest_do_request($invalid_service);
ei_wp_assert($invalid_service_response->get_status() === 400, 'EI rejects unsupported service categories');

$update_result = get_option(LAEI_Update_Manager::OPTION_LAST_RESULT, []);
ei_wp_assert(($update_result['status'] ?? '') === 'disabled_security_gate', 'real WordPress runtime records remote updates as disabled fail-closed');
echo "All standalone EI WordPress REST integration tests passed.\n";
