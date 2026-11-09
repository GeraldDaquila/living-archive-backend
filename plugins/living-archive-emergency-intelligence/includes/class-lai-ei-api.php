<?php
if (!defined('ABSPATH')) exit;

class LAEI_API {
    public static function init() {
        add_action('rest_api_init', [__CLASS__, 'routes']);
    }

    public static function routes() {
        register_rest_route('living-archive/emergency/v1', '/status', [
            'methods' => WP_REST_Server::READABLE,
            'callback' => [__CLASS__, 'status'],
            'permission_callback' => '__return_true',
        ]);
        register_rest_route('living-archive/emergency/v1', '/resolve', [
            'methods' => WP_REST_Server::CREATABLE,
            'callback' => [__CLASS__, 'resolve'],
            'permission_callback' => '__return_true',
            'args' => [
                'service_need' => ['required' => true, 'type' => 'string'],
                'safety_state' => ['required' => false, 'type' => 'string'],
                'location' => ['required' => false, 'type' => 'object'],
            ],
        ]);
    }

    public static function status() {
        return rest_ensure_response([
            'plugin_version' => LAEI_VERSION,
            'registry_version' => LAEI_Registry::version(),
            'last_checked' => get_option(LAEI_Update_Manager::OPTION_LAST_CHECK, 0),
            'last_success' => get_option(LAEI_Update_Manager::OPTION_LAST_SUCCESS, 0),
            'last_result' => get_option(LAEI_Update_Manager::OPTION_LAST_RESULT, null),
        ]);
    }

    public static function resolve(WP_REST_Request $request) {
        $service = sanitize_key($request->get_param('service_need'));
        $safety = sanitize_key($request->get_param('safety_state') ?: 'unknown');
        $location = $request->get_param('location');
        if (!is_array($location)) $location = [];
        return rest_ensure_response(LAEI_Engine::resolve($service, $location, $safety));
    }
}
