<?php
/**
 * Plugin Name: Living Archive — Answer + Doorway Standard
 * Description: Shared, hardened visitor-facing doorway presentation for Living Archive modules.
 * Version: 1.0.4
 * Author: Living Archive
 */
if (!defined('ABSPATH')) { exit; }

define('LA_ANSWER_DOORWAY_VERSION', '1.0.4');
define('LA_ANSWER_DOORWAY_URL', plugin_dir_url(__FILE__));

function la_answer_doorway_is_canonical_url($value) {
    if (!is_string($value) || $value === '' || strlen($value) > 2048) return false;
    if (preg_match('/[\x00-\x20\x7F]/', $value)) return false;
    $parts = wp_parse_url($value);
    if (!is_array($parts)) return false;
    $scheme = strtolower((string)($parts['scheme'] ?? ''));
    $host = strtolower((string)($parts['host'] ?? ''));
    $port = $parts['port'] ?? null;
    $path = (string)($parts['path'] ?? '');
    return $scheme === 'https'
        && $host === 'geralddaquila.com'
        && !isset($parts['user'])
        && !isset($parts['pass'])
        && ($port === null || $port === 443)
        && $path !== ''
        && strpos($path, '/') === 0
        && !array_key_exists('query', $parts)
        && !array_key_exists('fragment', $parts);
}

function la_answer_doorway_is_grounded_rationale($value) {
    if (!is_string($value)) return false;
    $rationale = trim($value);
    if ($rationale === '' || strlen($rationale) > 600) return false;
    $normalized = strtolower(rtrim($rationale, " .!?\t\n\r\0\x0B"));
    $generic = array(
        'there is something here worth staying with',
        'this gives you a concrete place to continue with the question you are carrying',
        'there is something here worth exploring',
        'this is a useful place to continue',
        'this gives the question another place to go',
    );
    return !in_array($normalized, $generic, true);
}

function la_answer_doorway_filter_rest_response($response, $server, $request) {
    if (!($response instanceof WP_REST_Response) || !is_object($request) || !method_exists($request, 'get_route')) {
        return $response;
    }
    $route = $request->get_route();
    if (!in_array($route, array('/stewardship/v1/pathway', '/living-archive/v1/navigate'), true)) {
        return $response;
    }
    $data = $response->get_data();
    if (!is_array($data) || !isset($data['selected']) || !is_array($data['selected'])) {
        return $response;
    }

    $selected = array();
    $why_each = isset($data['why_each']) && is_array($data['why_each']) ? $data['why_each'] : array();
    $verified_why = array();

    foreach ($data['selected'] as $item) {
        if (!is_array($item)) continue;
        $id = isset($item['id']) ? (string)$item['id'] : '';
        $title = isset($item['title']) && is_string($item['title']) ? trim($item['title']) : '';
        $url = isset($item['url']) ? $item['url'] : '';
        $rationale = $id !== '' && isset($why_each[$id]) ? $why_each[$id] : '';
        $title_length = function_exists('mb_strlen') ? mb_strlen($title, 'UTF-8') : strlen($title);
        if ($id === '' || $title === '' || $title_length > 180) continue;
        if (!la_answer_doorway_is_canonical_url($url) || !la_answer_doorway_is_grounded_rationale($rationale)) continue;
        $selected[] = $item;
        $verified_why[$id] = trim($rationale);
    }

    $data['selected'] = $selected;
    $data['why_each'] = $verified_why;
    $response->set_data($data);
    return $response;
}
add_filter('rest_post_dispatch', 'la_answer_doorway_filter_rest_response', 99, 3);

add_action('wp_enqueue_scripts', function () {
    if (is_admin()) return;
    wp_enqueue_style(
        'la-answer-doorway-standard',
        LA_ANSWER_DOORWAY_URL . 'assets/answer-doorway.css',
        array(),
        LA_ANSWER_DOORWAY_VERSION
    );
    wp_enqueue_script(
        'la-answer-doorway-standard',
        LA_ANSWER_DOORWAY_URL . 'assets/answer-doorway.js',
        array(),
        LA_ANSWER_DOORWAY_VERSION,
        false
    );
}, 1);
