<?php
/**
 * Plugin Name: Living Archive — FSD Proxy
 * Description: Server-side, rate-limited proxy for the versioned episode-based FSD endpoint.
 * Version: 0.2.3
 * Author: Living Archive
 */
if (!defined('ABSPATH')) { exit; }

if (!function_exists('la_fsd_proxy_is_enabled')) {
    function la_fsd_proxy_is_enabled() {
        return filter_var(get_option('la_fsd_proxy_enabled', false), FILTER_VALIDATE_BOOLEAN)
            && filter_var(get_option('la_fsd_proxy_staging_enabled', false), FILTER_VALIDATE_BOOLEAN);
    }
}

if (!function_exists('la_fsd_proxy_payload_is_valid')) {
    function la_fsd_proxy_payload_is_valid($payload) {
        if (!is_array($payload)) return false;
        $required = array('contract_version','scale','prior_understanding','experience_type','consequence_significance','understanding_after','reconsideration_basis','subsequent_response','understanding_action_link','response_available','non_change_reason');
        $allowed = array_merge($required, array('prior_understanding_detail','experience_detail'));
        if (array_diff(array_keys($payload), $allowed) || array_diff($required, array_keys($payload))) return false;
        if (($payload['contract_version'] ?? '') !== 'fsd-episode-v1') return false;
        $enums = array(
            'scale' => array('self','relationships','community','institution','civilization'),
            'prior_understanding' => array('clear','partial','disputed','unknown'),
            'experience_type' => array('observed_outcome','affected_party_feedback','documented_evidence','repeated_pattern','unexpected_consequence','other_unclear'),
            'consequence_significance' => array('material_outcome_or_decision','material_risk_or_mismatch','limited_or_ambiguous','unclear'),
            'understanding_after' => array('revised','qualified','examined_and_retained','not_reconsidered','no_opportunity','unknown'),
            'reconsideration_basis' => array('directly_changed_explanation','prompted_examination','considered_with_competing_evidence','no_clear_connection','unknown'),
            'subsequent_response' => array('decision_or_action_changed','tested_or_piloted','paused_pending_evidence','no_response','attempted_but_blocked','too_early_or_unknown'),
            'understanding_action_link' => array('directly_informed','partly_informed','unrelated_or_unclear','no_response_or_unknown'),
            'response_available' => array('yes','partly','no','unknown'),
            'non_change_reason' => array('not_warranted','more_evidence_needed','authority_or_resources_unavailable','competing_responsibilities_or_risks','resistance_or_existing_arrangements','insufficient_time','unclear','not_applicable')
        );
        foreach ($enums as $key => $choices) {
            if (!isset($payload[$key]) || !is_string($payload[$key]) || !in_array($payload[$key], $choices, true)) return false;
        }
        foreach (array('prior_understanding_detail' => 240, 'experience_detail' => 360) as $key => $limit) {
            if (!array_key_exists($key, $payload)) continue;
            if (!is_string($payload[$key])) return false;
            $length = function_exists('mb_strlen') ? mb_strlen(trim($payload[$key]), 'UTF-8') : strlen(trim($payload[$key]));
            if ($length > $limit) return false;
        }
        $response = $payload['subsequent_response'];
        $link = $payload['understanding_action_link'];
        if (in_array($response, array('no_response','too_early_or_unknown'), true) && in_array($link, array('directly_informed','partly_informed'), true)) return false;
        if (in_array($response, array('decision_or_action_changed','tested_or_piloted','paused_pending_evidence','attempted_but_blocked'), true) && $link === 'no_response_or_unknown') return false;
        if ($payload['response_available'] === 'no' && in_array($response, array('decision_or_action_changed','tested_or_piloted'), true)) return false;
        $non_change = in_array($response, array('no_response','attempted_but_blocked','paused_pending_evidence','too_early_or_unknown'), true);
        if (!$non_change && $payload['non_change_reason'] !== 'not_applicable') return false;
        if ($non_change && $payload['non_change_reason'] === 'not_applicable') return false;
        return true;
    }
}

if (!function_exists('la_fsd_proxy_rate_limited')) {
    function la_fsd_proxy_rate_limited() {
        $ip = (string)($_SERVER['REMOTE_ADDR'] ?? 'unknown');
        $ip_key = 'la_fsd_proxy_peer_' . hash('sha256', $ip);
        $ip_window = (int)floor(time() / 600);
        $peer = get_transient($ip_key);
        if (!is_array($peer) || (int)($peer['window'] ?? 0) !== $ip_window) $peer = array('window' => $ip_window, 'count' => 0);
        $peer['count'] = (int)$peer['count'] + 1;
        set_transient($ip_key, $peer, 660);
        $global_key = 'la_fsd_proxy_global_minute';
        $global_window = (int)floor(time() / 60);
        $global = get_transient($global_key);
        if (!is_array($global) || (int)($global['window'] ?? 0) !== $global_window) $global = array('window' => $global_window, 'count' => 0);
        $global['count'] = (int)$global['count'] + 1;
        set_transient($global_key, $global, 90);
        return $peer['count'] > 8 || $global['count'] > 120;
    }
}

// Apply privacy headers to every response on the FSD route, including WP_Error responses.
add_filter('rest_pre_serve_request', function ($served, $result, $request, $server) {
    if ($request instanceof WP_REST_Request && $request->get_route() === '/living-archive/v1/fsd-analyze' && !headers_sent()) {
        header('Cache-Control: no-store, no-cache, must-revalidate, max-age=0', true);
        header('Pragma: no-cache', true);
        header('Expires: 0', true);
    }
    return $served;
}, 10, 4);

add_action('rest_api_init', function () {
    if (!la_fsd_proxy_is_enabled()) return;
    register_rest_route('living-archive/v1', '/fsd-analyze', array(
        'methods' => WP_REST_Server::CREATABLE,
        'permission_callback' => '__return_true',
        'callback' => function ($request) {
            $origin = untrailingslashit((string)$request->get_header('origin'));
            $expected = untrailingslashit(home_url());
            if ($origin === '' || !hash_equals($expected, $origin)) return new WP_Error('la_fsd_origin_rejected', 'Request origin is not permitted.', array('status' => 403));
            if (la_fsd_proxy_rate_limited()) return new WP_Error('la_fsd_rate_limited', 'Please wait before starting another diagnostic.', array('status' => 429));
            $raw = (string)$request->get_body();
            if (strlen($raw) > 16384) return new WP_Error('la_fsd_request_too_large', 'Diagnostic request is too large.', array('status' => 413));
            $payload = json_decode($raw, true);
            if (!la_fsd_proxy_payload_is_valid($payload)) return new WP_Error('la_fsd_invalid_request', 'The diagnostic answers could not be validated.', array('status' => 400));
            if (!function_exists('la_provider_bank_shared_secret')) return new WP_Error('la_fsd_gateway_unavailable', 'The diagnostic service is not configured.', array('status' => 503));
            $secret = (string)la_provider_bank_shared_secret();
            if ($secret === '') return new WP_Error('la_fsd_gateway_unavailable', 'The diagnostic service is not configured.', array('status' => 503));
            $endpoints = array(
                'https://living-archive-backend.onrender.com/api/fsd/analyze-episode',
                'https://living-archive-backend-mirror.onrender.com/api/fsd/analyze-episode'
            );
            $last_status = 503;
            foreach ($endpoints as $endpoint) {
                $response = wp_remote_post($endpoint, array(
                    'timeout' => 35, 'redirection' => 0, 'limit_response_size' => 32768, 'sslverify' => true,
                    'headers' => array(
                        'Content-Type' => 'application/json', 'Accept' => 'application/json', 'Cache-Control' => 'no-store',
                        'X-Living-Archive-Provider-Key' => $secret, 'User-Agent' => 'Living-Archive-FSD-Proxy/0.2.3'
                    ),
                    'body' => wp_json_encode($payload)
                ));
                if (is_wp_error($response)) continue;
                $status = (int)wp_remote_retrieve_response_code($response);
                $body = json_decode(wp_remote_retrieve_body($response), true);
                $last_status = $status;
                if ($status === 200 && is_array($body) && !empty($body['ok'])
                    && ($body['contract_version'] ?? '') === 'fsd-episode-v1'
                    && isset($body['report']) && is_array($body['report'])
                    && isset($body['report']['episode_provenance'])
                    && ($body['report']['episode_provenance']['independently_verified'] ?? null) === false
                    && isset($body['report']['archive_references']) && is_array($body['report']['archive_references'])) {
                    $result = new WP_REST_Response($body, 200);
                    $result->header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0');
                    $result->header('Pragma', 'no-cache');
                    return $result;
                }
                if (in_array($status, array(400,401,403,413,422,429), true)) return new WP_Error('la_fsd_backend_rejected', 'The diagnostic could not be completed.', array('status' => $status, 'code' => 'fsd_request_rejected'));
            }
            return new WP_Error('la_fsd_backend_unavailable', 'The diagnostic service is temporarily unavailable.', array('status' => 503, 'upstream_status' => $last_status));
        }
    ));
});

add_action('wp_enqueue_scripts', function () {
    // Candidate assets load only on the private staging draft. The REST endpoint
    // remains independently disabled unless both explicit feature flags are true.
    if (!is_page(80594)) return;
    wp_enqueue_style('living-archive-fsd-episode', plugins_url('assets/fsd-app.css', __FILE__), array(), '0.2.3');
    wp_enqueue_script('living-archive-fsd-episode', plugins_url('assets/fsd-app.js', __FILE__), array(), '0.2.3', true);
});
