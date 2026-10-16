<?php
declare(strict_types=1);

if (!defined('ABSPATH')) define('ABSPATH', '/');
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
echo "HRN v0.5.331 grounded question-recovery smoke test passed.\n";
