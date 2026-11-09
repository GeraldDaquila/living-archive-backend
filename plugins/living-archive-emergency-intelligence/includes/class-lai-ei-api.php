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
        // EI accepts resource-resolution context only, never visitor answers or transcripts.
        foreach (['message','visitor_answer','original_question','query','conversation','visitor_history','transcript','session_id'] as $forbidden) {
            if ($request->get_param($forbidden) !== null) {
                return new WP_Error('laei_visitor_content_not_accepted', 'Emergency Intelligence accepts location and service context only.', ['status' => 400]);
            }
        }

        $service_raw = $request->get_param('service_need');
        if (!is_string($service_raw) || strlen($service_raw) > 64) {
            return new WP_Error('laei_invalid_service_need', 'A valid service category is required.', ['status' => 400]);
        }
        $service = sanitize_key($service_raw);
        $allowed_services = [
            'general_emergency','police','fire','medical','rescue','traffic',
            'crisis_support','mental_health_support','emotional_distress','suicidal_crisis',
            'emergency','emergency_medical','medical_emergency','crisis','mental_health','suicide_crisis',
        ];
        if (!in_array($service, $allowed_services, true)) {
            return new WP_Error('laei_invalid_service_need', 'The requested service category is not supported.', ['status' => 400]);
        }

        $safety_raw = $request->get_param('safety_state');
        $safety = $safety_raw === null || $safety_raw === '' ? 'unknown' : (is_string($safety_raw) ? sanitize_key($safety_raw) : '');
        if (!in_array($safety, ['unknown','green','amber','acute','diagnostic'], true)) {
            return new WP_Error('laei_invalid_safety_state', 'The supplied safety context is invalid.', ['status' => 400]);
        }

        $location = $request->get_param('location');
        if ($location === null) $location = [];
        if (!is_array($location)) {
            return new WP_Error('laei_invalid_location', 'Location context must be an object.', ['status' => 400]);
        }

        $string_limits = [
            'explicit_country' => 80,
            'browser_country' => 80,
            'ip_country' => 80,
            'timezone_country' => 80,
            'locale_country' => 80,
            'region' => 100,
            'province' => 100,
            'locality' => 100,
            'address' => 250,
        ];
        $allowed_location_keys = array_merge(array_keys($string_limits), ['refused','user_confirmation']);
        foreach ($location as $key => $value) {
            if (!in_array($key, $allowed_location_keys, true)) {
                return new WP_Error('laei_invalid_location_field', 'Location context contains an unsupported field.', ['status' => 400]);
            }
            if (isset($string_limits[$key])) {
                if ($value !== null && (!is_string($value) || strlen($value) > $string_limits[$key])) {
                    return new WP_Error('laei_invalid_location_value', 'A location value has an invalid type or exceeds its length limit.', ['status' => 400]);
                }
                if (is_string($value)) $location[$key] = sanitize_text_field($value);
            } elseif ($value !== null && !is_bool($value)) {
                return new WP_Error('laei_invalid_location_value', 'Location confirmation flags must be boolean.', ['status' => 400]);
            }
        }

        return rest_ensure_response(LAEI_Engine::resolve($service, $location, $safety));
    }
}
