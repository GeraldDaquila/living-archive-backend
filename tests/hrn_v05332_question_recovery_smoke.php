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

function add_action(...$args) {}
function add_shortcode(...$args) {}
function add_filter(...$args) {}
function get_option($key, $default = false) { return $default; }
function update_option(...$args) { return true; }
function add_option(...$args) { return true; }
function wp_json_encode($value, $options = 0, $depth = 512) { return json_encode($value, $options, $depth); }
function wp_strip_all_tags($value) { return strip_tags((string)$value); }
function remove_accents($value) { return (string)$value; }
function sanitize_key($value) { return preg_replace('/[^a-z0-9_\\-]/', '', strtolower((string)$value)); }
function plugin_basename($file) { return basename((string)$file); }
function get_plugins() { return array(); }
function is_plugin_active($file) { return false; }
function deactivate_plugins(...$args) {}
function register_activation_hook(...$args) {}

require __DIR__ . '/../recovery/live-hrn-v05330/candidate/human-relational-navigator.php';

$class = 'Living_Archive_Human_Relational_Navigator';
$instance = $class::instance();
$bad = 'What part of that effort is easiest to overlook when you look at the situation?';
$guard = new ReflectionMethod($class, 'question_is_generic_or_compound');
$guard->setAccessible(true);
if (!$guard->invoke($instance, $bad)) {
    fwrite(STDERR, "The abstract effort-overlook template was not rejected.\n");
    exit(1);
}

$message = "I care about a friend, but lately I feel I'm always the one making an effort. I don't want to judge them unfairly, but I also don't want to keep ignoring how I feel. How can I understand what's happening between us?";
$response = 'You described feeling like you are always the one making an effort while trying not to judge your friend unfairly. This leaves it unclear whether the imbalance is in the actual distribution of tasks or in how you are perceiving their participation.';
$complete = new ReflectionMethod($class, 'structural_question_completion_safe');
$complete->setAccessible(true);
$question = $complete->invoke($instance, $response, $message, array(), array());
$expected = 'What happens between you when you are the one making the effort?';
if ($question !== $expected) {
    fwrite(STDERR, "Unexpected recovered question: " . var_export($question, true) . "\n");
    exit(1);
}

$messageEffort = "I care about a friend, but lately I feel I'm always the one making an effort. I don't want to judge them unfairly, but I also don't want to keep ignoring how I feel. How can I understand what's happening between us?";
$effortResponseMethod = new ReflectionMethod($class, 'one_sided_effort_recovery_candidate');
$effortResponseMethod->setAccessible(true);
$effortResponse = $effortResponseMethod->invoke($instance, $messageEffort);
if (trim((string)$effortResponse) === '' || strpos($effortResponse, 'distribution of tasks') !== false) {
    fwrite(STDERR, "The one-sided-effort prose recovery did not produce grounded visitor-facing language.\n");
    exit(1);
}
$relevance = new ReflectionMethod($class, 'structured_recovery_candidate_is_relevant');
$relevance->setAccessible(true);
if (!$relevance->invoke($instance, $effortResponse, $messageEffort)) {
    fwrite(STDERR, "The one-sided-effort recovery candidate failed current-turn relevance.\n");
    exit(1);
}
$abstractGuard = new ReflectionMethod($class, 'one_sided_effort_response_violation');
$abstractGuard->setAccessible(true);
$abstractDraft = 'You described feeling like you are always the one making an effort while trying not to judge your friend unfairly. This leaves it unclear whether the imbalance is in the actual distribution of tasks or in how you are perceiving their participation.';
if (!$abstractGuard->invoke($instance, $abstractDraft, $messageEffort)) {
    fwrite(STDERR, "The known abstract task-allocation response was not rejected for the matching friendship-effort case.\n");
    exit(1);
}
$workMessage = "Our team is deciding how to distribute tasks across four roles for the next project.";
if ($abstractGuard->invoke($instance, 'We should review the distribution of tasks across the roles.', $workMessage)) {
    fwrite(STDERR, "The friendship-effort guard incorrectly rejected a workplace task-allocation discussion.\n");
    exit(1);
}
$shape = new ReflectionMethod($class, 'ordinary_response_shape_valid');
$shape->setAccessible(true);
if (!$shape->invoke($instance, $effortResponse, $expected)) {
    fwrite(STDERR, "The grounded recovery prose did not satisfy the ordinary response-shape contract.\n");
    exit(1);
}
$humanity = new ReflectionMethod($class, 'humanity_gate');
$humanity->setAccessible(true);
$humanResponse = $humanity->invoke($instance, $effortResponse, array());
if (trim((string)$humanResponse) === '') {
    fwrite(STDERR, "The grounded recovery prose failed the existing humanity/grounding gates.\n");
    exit(1);
}
$normalize = new ReflectionMethod($class, 'normalize_composition');
$normalize->setAccessible(true);
$abstractEnvelope = wp_json_encode(array(
    'response' => $abstractDraft,
    'question' => $expected,
    'rest' => false,
    'use_resource' => false,
    'resource_intro' => '',
));
$rejectedTurn = $normalize->invoke($instance, $abstractEnvelope, array(), $messageEffort, array(), false);
$failureProperty = new ReflectionProperty($class, 'last_composition_failure');
$failureProperty->setAccessible(true);
$failure = $failureProperty->getValue($instance);
if (is_array($rejectedTurn) && trim((string)($rejectedTurn['response'] ?? '')) !== '') {
    fwrite(STDERR, "The full composition normalizer did not reject the known abstract friendship-effort response.\n");
    exit(1);
}
if (($failure['reason'] ?? '') !== 'visitor_surface_policy_rejected') {
    fwrite(STDERR, "The known abstract response was rejected for an unexpected reason: " . var_export($failure['reason'] ?? null, true) . "\n");
    exit(1);
}
$fullRecovery = new ReflectionMethod($class, 'recover_structured_state_composition');
$fullRecovery->setAccessible(true);
$recoveredTurn = $fullRecovery->invoke($instance, array(), $messageEffort, $messageEffort, array(), array());
if (!is_array($recoveredTurn)
    || trim((string)($recoveredTurn['response'] ?? '')) === ''
    || trim((string)($recoveredTurn['question'] ?? '')) === '') {
    fwrite(STDERR, "The full provider-independent structured-state recovery path did not return a complete visitor-facing turn.\n");
    exit(1);
}
if (strpos(strtolower($recoveredTurn['response']), 'distribution of tasks') !== false
    || strpos(strtolower($recoveredTurn['response']), 'perceiving their participation') !== false) {
    fwrite(STDERR, "The full recovery path returned the known abstract task-allocation framing.\n");
    exit(1);
}

$recordFailure = new ReflectionMethod($class, 'record_provider_bridge_failure');
$recordFailure->setAccessible(true);
$recordFailure->invoke($instance, new WP_Error(
    'lah_rn_turn_provider_budget',
    'Provider budget exhausted; private message must not be logged.',
    array('stage' => 'turn_budget', 'provider_code' => 'turn_provider_budget_exhausted', 'retryable' => true)
), 'hrn_relational');
$failureAfterBridgeError = $failureProperty->getValue($instance);
$traceAfterBridgeError = $failureProperty->getDeclaringClass()->getProperty('last_provider_trace');
$traceAfterBridgeError->setAccessible(true);
$trace = $traceAfterBridgeError->getValue($instance);
if (($failureAfterBridgeError['reason'] ?? '') !== 'provider_budget_exhausted'
    || ($failureAfterBridgeError['provider_error_stage'] ?? '') !== 'turn_budget'
    || ($trace['failure_code'] ?? '') !== 'lah_rn_turn_provider_budget'
    || ($trace['failure_stage'] ?? '') !== 'turn_budget') {
    fwrite(STDERR, "Provider bridge errors did not preserve their failure class and stage.\n");
    exit(1);
}
if (strpos(json_encode($trace), 'private message must not be logged') !== false) {
    fwrite(STDERR, "Provider bridge diagnostics unexpectedly retained the raw provider error message.\n");
    exit(1);
}

echo "HRN v0.5.332 one-sided-effort prose, question recovery, and provider failure diagnostics smoke tests passed.\n";

