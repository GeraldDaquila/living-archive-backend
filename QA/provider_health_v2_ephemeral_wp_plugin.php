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
