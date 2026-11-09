<?php
/**
 * EI remote-update security gate regression.
 * Confirms that registry refresh is fail-closed until signature verification exists.
 */
define('ABSPATH', __DIR__ . '/');
define('LAEI_VERSION', '0.1.3');

$GLOBALS['ei_options'] = [];
$GLOBALS['ei_http_calls'] = 0;

function get_option($key, $default = false) {
    return array_key_exists($key, $GLOBALS['ei_options']) ? $GLOBALS['ei_options'][$key] : $default;
}
function update_option($key, $value) {
    $GLOBALS['ei_options'][$key] = $value;
    return true;
}
function wp_remote_get($url, $args = []) {
    $GLOBALS['ei_http_calls']++;
    throw new RuntimeException('Network access must not occur in this test.');
}

require_once __DIR__ . '/../../plugins/living-archive-emergency-intelligence/includes/class-lai-ei-update-manager.php';

$result = LAEI_Update_Manager::check_now();
if (($result['status'] ?? '') !== 'disabled_security_gate') {
    fwrite(STDERR, "FAIL: remote update gate did not fail closed.\n");
    exit(1);
}
if ($GLOBALS['ei_http_calls'] !== 0) {
    fwrite(STDERR, "FAIL: remote update gate attempted an HTTP request.\n");
    exit(1);
}
if (($GLOBALS['ei_options'][LAEI_Update_Manager::OPTION_LAST_RESULT]['status'] ?? '') !== 'disabled_security_gate') {
    fwrite(STDERR, "FAIL: disabled security status was not recorded.\n");
    exit(1);
}
echo "PASS: remote registry updates remain disabled without trusted-key signature verification.\n";
