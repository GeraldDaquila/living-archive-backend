<?php
/**
 * Plugin Name: Provider Health v2 Ephemeral CI Test
 * Description: Isolated WordPress integration fixture for the Provider Health v2 bridge.
 * Version: 0.1.0
 */
if (!defined('ABSPATH')) {
    exit;
}

if (!function_exists('la_provider_bank_shared_secret')) {
    function la_provider_bank_shared_secret() {
        return 'provider-health-v2-ephemeral-ci-only-secret';
    }
}

if (!function_exists('la_provider_health_authorized')) {
    function la_provider_health_authorized($request) {
        $expected = (string)la_provider_bank_shared_secret();
        $supplied = is_object($request) && method_exists($request, 'get_header')
            ? (string)$request->get_header('x-living-archive-provider-key')
            : '';
        return $expected !== '' && $supplied !== '' && hash_equals($expected, $supplied);
    }
}

require_once __DIR__ . '/provider_health_bridge_v2_candidate.php';

register_activation_hook(__FILE__, 'la_provider_health_v2_install_schema');
add_action('rest_api_init', 'la_provider_health_v2_register_routes');


/* Temporary CI diagnostic: inspect the registered route and invoke its auth callback without credentials. */
add_action('rest_api_init', function () {
    register_rest_route('provider-health-test/v1', '/auth-diagnostic', array(
        'methods' => WP_REST_Server::READABLE,
        'permission_callback' => '__return_true',
        'callback' => function () {
            $routes = rest_get_server()->get_routes();
            $endpoints = $routes['/living-archive/v1/provider-health'] ?? array();
            $get = $endpoints[0] ?? array();
            $probe = new WP_REST_Request('GET', '/living-archive/v1/provider-health');
            $permission = $get['permission_callback'] ?? null;
            return array(
                'auth_without_header' => la_provider_health_authorized($probe),
                'endpoint_count' => count($endpoints),
                'get_permission_callback' => is_string($permission) ? $permission : gettype($permission),
                'get_permission_callable' => is_callable($permission),
                'get_callback' => is_string($get['callback'] ?? null) ? $get['callback'] : gettype($get['callback'] ?? null),
                'get_methods' => $get['methods'] ?? null,
            );
        },
    ));
}, 99);
