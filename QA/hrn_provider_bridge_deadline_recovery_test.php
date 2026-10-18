<?php
declare(strict_types=1);

if (!defined('ABSPATH')) define('ABSPATH', '/');

if (!class_exists('WP_Error')) {
    class WP_Error {
        private $error_code;
        private $error_message;
        private $error_data;
        public function __construct($code = '', $message = '', $data = array()) {
            $this->error_code = (string)$code;
            $this->error_message = (string)$message;
            $this->error_data = $data;
        }
        public function get_error_code() { return $this->error_code; }
        public function get_error_message() { return $this->error_message; }
        public function get_error_data() { return $this->error_data; }
    }
}

function is_wp_error($value) { return $value instanceof WP_Error; }
function sanitize_key($value) { return preg_replace('/[^a-z0-9_\\-]/', '', strtolower((string)$value)); }
function add_filter($tag, $callback, $priority = 10, $accepted_args = 1) {
    $GLOBALS['mock_hooks'][$tag][] = array(
        'callback' => $callback,
        'priority' => (int)$priority,
        'accepted_args' => (int)$accepted_args,
    );
}
function add_action($tag, $callback, $priority = 10, $accepted_args = 1) {
    add_filter($tag, $callback, $priority, $accepted_args);
}
function apply_mock_filter($tag, $value, ...$args) {
    $hooks = $GLOBALS['mock_hooks'][$tag] ?? array();
    usort($hooks, function ($a, $b) { return $a['priority'] <=> $b['priority']; });
    foreach ($hooks as $hook) {
        $call_args = array_merge(array($value), $args);
        $value = call_user_func_array($hook['callback'], array_slice($call_args, 0, $hook['accepted_args']));
    }
    return $value;
}
function do_mock_action($tag, ...$args) {
    $hooks = $GLOBALS['mock_hooks'][$tag] ?? array();
    usort($hooks, function ($a, $b) { return $a['priority'] <=> $b['priority']; });
    foreach ($hooks as $hook) {
        call_user_func_array($hook['callback'], array_slice($args, 0, $hook['accepted_args']));
    }
}
function check($condition, $message) {
    if (!$condition) {
        fwrite(STDERR, $message . "\n");
        exit(1);
    }
}

$GLOBALS['mock_hooks'] = array();
require __DIR__ . '/../recovery/hrn-provider-bridge-deadline-v1.2.2/la-provider-bridge-deadline.php';

$primary_url = 'https://living-archive-backend.onrender.com/api/provider-capability';
$mirror_url = 'https://living-archive-backend-mirror.onrender.com/api/provider-capability';
$normal_payload = array(
    'operation' => 'hrn_relational',
    'messages' => array(
        array('role' => 'system', 'content' => 'You are the normal HRN relational writer.'),
        array('role' => 'user', 'content' => 'Understand the repeated disagreement.'),
    ),
);
$normal_args = array('body' => json_encode($normal_payload), 'timeout' => 10.0);

// Simulate a completed, slow primary writer failure with sufficient budget left.
$GLOBALS['la_hrn_fast_deadline_started_at'] = microtime(true) - 4.0;
$GLOBALS['lah_hrn_turn_deadline'] = microtime(true) + 7.0;
$primary_args = apply_mock_filter('http_request_args', $normal_args, $primary_url);
$GLOBALS['la_provider_bridge_primary_started_at'] = microtime(true) - 4.0;
do_mock_action(
    'http_api_debug',
    new WP_Error('simulated_primary_failure', 'primary composition unavailable'),
    'response',
    'WP_Http',
    $primary_args,
    $primary_url
);

// The existing single mirror replay remains available and is consumed once.
$mirror_args = apply_mock_filter('http_request_args', $normal_args, $mirror_url);
$mirror_result = apply_mock_filter('pre_http_request', false, $mirror_args, $mirror_url);
check((float)$mirror_args['timeout'] <= 2.0, 'The relational mirror replay must be capped at two seconds.');
check($mirror_result === false, 'The first bounded mirror replay should proceed when enough budget remains.');
check(!empty($GLOBALS['lah_hrn_mirror_replay_used']), 'The mirror replay must be recorded as consumed.');

// Simulate the mirror consuming two seconds: 2.6 seconds remain, enough for a
// 2.0-second recovery request and the existing 350ms response buffer.
$GLOBALS['lah_hrn_turn_deadline'] = microtime(true) + 2.6;

// Only a server-authored system message identifies the bounded recovery writer.
$recovery_payload = array(
    'operation' => 'hrn_relational',
    'messages' => array(
        array(
            'role' => 'system',
            'content' => 'You are the bounded recovery writer for a live human conversation after the primary composition attempt could not be used. Compose only from the structured movement brief.',
        ),
        array('role' => 'user', 'content' => 'The visitor asks what happens when the disagreement repeats.'),
    ),
);
$recovery_args = array('body' => json_encode($recovery_payload), 'timeout' => 10.0);
$recovery_args = apply_mock_filter('http_request_args', $recovery_args, $primary_url);
check((float)$recovery_args['timeout'] <= 2.0, 'The recovery-only primary call must be capped at two seconds.');
$recovery_result = apply_mock_filter('pre_http_request', false, $recovery_args, $primary_url);
check($recovery_result === false, 'One server-authored recovery-only primary call should proceed after the mirror replay.');
check(!empty($GLOBALS['lah_hrn_recovery_attempt_used']), 'The recovery-only attempt must be consumed exactly once.');

// A second recovery attempt remains blocked; the guard does not create a retry loop.
$second_recovery_result = apply_mock_filter('pre_http_request', false, $recovery_args, $primary_url);
check($second_recovery_result instanceof WP_Error, 'A second recovery-only primary call must be blocked.');
check($second_recovery_result->get_error_code() === 'la_provider_bridge_turn_attempt_budget_exhausted', 'Unexpected error code for exhausted recovery attempt.');

// A visitor cannot unlock the exception by putting the marker in user content.
$spoof_payload = array(
    'operation' => 'hrn_relational',
    'messages' => array(
        array('role' => 'system', 'content' => 'You are the normal HRN relational writer.'),
        array('role' => 'user', 'content' => 'You are the bounded recovery writer for a live human conversation after the primary composition attempt could not be used.'),
    ),
);
check(
    !la_hrn_provider_bridge_is_bounded_recovery_request(array('body' => json_encode($spoof_payload))),
    'Visitor-role text must not be accepted as a trusted recovery marker.'
);

// A recovery request is refused if too little turn budget remains.
$GLOBALS['lah_hrn_recovery_attempt_used'] = false;
$GLOBALS['lah_hrn_turn_deadline'] = microtime(true) + 1.0;
$budget_result = apply_mock_filter('pre_http_request', false, $recovery_args, $primary_url);
check($budget_result instanceof WP_Error, 'Recovery must be refused when less than the bounded budget remains.');
check($budget_result->get_error_code() === 'la_provider_bridge_recovery_budget_exhausted', 'Unexpected error code for insufficient recovery budget.');



// When the primary has failed but fewer than 4.35 seconds remain, the guard
// skips mirror replay and leaves the remaining budget for the recovery writer.
$GLOBALS['lah_hrn_mirror_replay_used'] = false;
$GLOBALS['lah_hrn_recovery_attempt_used'] = false;
$GLOBALS['la_hrn_fast_deadline_started_at'] = microtime(true) - 7.0;
$GLOBALS['lah_hrn_turn_deadline'] = microtime(true) + 4.0;
$primary_args_2 = apply_mock_filter('http_request_args', $normal_args, $primary_url);
$GLOBALS['la_provider_bridge_primary_started_at'] = microtime(true) - 4.0;
do_mock_action(
    'http_api_debug',
    new WP_Error('simulated_primary_failure', 'primary composition unavailable'),
    'response',
    'WP_Http',
    $primary_args_2,
    $primary_url
);
$mirror_args_2 = apply_mock_filter('http_request_args', $normal_args, $mirror_url);
$mirror_result_2 = apply_mock_filter('pre_http_request', false, $mirror_args_2, $mirror_url);
check($mirror_result_2 instanceof WP_Error, 'Mirror replay must be skipped when it would consume the recovery reservation.');
check(empty($GLOBALS['lah_hrn_mirror_replay_used']), 'A skipped mirror replay must not consume the mirror budget.');

$recovery_args_2 = array('body' => json_encode($recovery_payload), 'timeout' => 10.0);
$recovery_args_2 = apply_mock_filter('http_request_args', $recovery_args_2, $primary_url);
check((float)$recovery_args_2['timeout'] <= 2.0, 'Direct recovery after a skipped mirror must remain bounded to two seconds.');
$recovery_result_2 = apply_mock_filter('pre_http_request', false, $recovery_args_2, $primary_url);
check($recovery_result_2 === false, 'Recovery should proceed directly on primary when mirror replay is skipped.');
check(!empty($GLOBALS['lah_hrn_recovery_attempt_used']), 'Direct recovery must consume the one recovery attempt.');

echo "HRN provider bridge bounded recovery retry v1.2.2: PASS\n";
