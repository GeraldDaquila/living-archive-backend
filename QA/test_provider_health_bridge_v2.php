<?php
declare(strict_types=1);

define('ARRAY_A', 'ARRAY_A');
define('ABSPATH', '/wordpress/');

class WP_Error {
    public $code;
    public $message;
    public $data;
    public function __construct($code, $message, $data = array()) {
        $this->code = $code;
        $this->message = $message;
        $this->data = $data;
    }
}
function is_wp_error($value) { return $value instanceof WP_Error; }
function sanitize_key($value) { return strtolower(preg_replace('/[^a-z0-9_\-]/', '', (string)$value)); }
function sanitize_text_field($value) { return trim(strip_tags((string)$value)); }
function wp_json_encode($value) {
    $GLOBALS['encode_calls'] = ($GLOBALS['encode_calls'] ?? 0) + 1;
    if (($GLOBALS['fail_encode_on'] ?? 0) === $GLOBALS['encode_calls']) {
        return false;
    }
    return json_encode($value);
}
function current_time($type, $gmt = false) { return gmdate('Y-m-d H:i:s'); }

class FakeResponse {
    public $data;
    public $headers = array();
    public function __construct($data) { $this->data = $data; }
    public function header($name, $value) { $this->headers[$name] = $value; }
}
function rest_ensure_response($data) { return new FakeResponse($data); }

class FakeRequest {
    private $body;
    public function __construct($body) { $this->body = $body; }
    public function get_json_params() { return $this->body; }
}

class FakeWpdb {
    public $prefix = 'wp_';
    public $last_error = '';
    public $rows = array();
    public $writes = 0;
    public $fail_replace_at = 0;
    public $fail_read = false;
    public $fail_commit = false;
    private $backup = null;

    public function query($sql) {
        $this->last_error = '';
        if ($sql === 'START TRANSACTION') {
            $this->backup = $this->rows;
            return 0;
        }
        if ($sql === 'COMMIT') {
            if ($this->fail_commit) {
                $this->last_error = 'simulated commit failure';
                return false;
            }
            $this->backup = null;
            return 0;
        }
        if ($sql === 'ROLLBACK') {
            if (is_array($this->backup)) {
                $this->rows = $this->backup;
            }
            $this->backup = null;
            return 0;
        }
        return 0;
    }

    public function prepare($query, ...$args) {
        $value = addslashes((string)($args[0] ?? ''));
        return str_replace('%s', "'" . $value . "'", $query);
    }

    public function get_var($sql) {
        $this->last_error = '';
        if ($this->fail_read) {
            $this->last_error = 'simulated read failure';
            return null;
        }
        if (!preg_match("/state_key = '([^']*)'/", $sql, $match)) {
            $this->last_error = 'unexpected SELECT';
            return null;
        }
        $key = stripslashes($match[1]);
        return $this->rows[$key]['payload'] ?? null;
    }

    public function replace($table, $data, $format) {
        $this->last_error = '';
        $this->writes++;
        if ($this->fail_replace_at > 0 && $this->writes === $this->fail_replace_at) {
            $this->last_error = 'simulated replace failure';
            return false;
        }
        $this->rows[$data['state_key']] = array(
            'state_key' => $data['state_key'],
            'payload' => $data['payload'],
            'updated_at' => $data['updated_at'],
        );
        return 1;
    }

    public function get_results($sql, $output) {
        $this->last_error = '';
        if ($this->fail_read) {
            $this->last_error = 'simulated result failure';
            return false;
        }
        $rows = array_values($this->rows);
        usort($rows, function($a, $b) {
            return strcmp($a['state_key'], $b['state_key']);
        });
        return array_slice($rows, 0, 100);
    }
}

require __DIR__ . '/provider_health_bridge_v2_candidate.php';

function check($condition, $message) {
    if (!$condition) {
        throw new RuntimeException('FAIL: ' . $message);
    }
}
function valid_body($count = 2) {
    $states = array();
    for ($i = 0; $i < $count; $i++) {
        $model = 'model-' . ($i + 1);
        $states['groq:' . $model] = array(
            'provider' => 'groq',
            'model' => $model,
            'state' => 'open',
            'failures' => 1,
            'consecutive_failures' => 1,
            'last_failure' => 20.0,
            'last_success' => 10.0,
            'cooldown_until' => 80.0,
            'last_operation' => 'hrn_relational',
            'probe_in_flight' => true,
        );
    }
    return array('contract_version' => 'v2', 'states' => $states);
}

$GLOBALS['wpdb'] = new FakeWpdb();
$GLOBALS['encode_calls'] = 0;
$GLOBALS['fail_encode_on'] = 0;

$response = la_provider_health_v2_write(new FakeRequest(valid_body()));
check(!is_wp_error($response), 'valid batch accepted');
check($response->data['success'] === true, 'success acknowledgement explicit');
check($response->data['submitted'] === 2 && $response->data['written'] === 2, 'exact counts returned');
check(count($GLOBALS['wpdb']->rows) === 2, 'both records committed');
$stored = json_decode($GLOBALS['wpdb']->rows['groq:model-1']['payload'], true);
check($stored['probe_in_flight'] === false, 'probe ownership forced false');

// Version mismatch is rejected before transaction or writes.
$before_writes = $GLOBALS['wpdb']->writes;
$invalid = valid_body();
$invalid['contract_version'] = 'v1';
$result = la_provider_health_v2_write(new FakeRequest($invalid));
check(is_wp_error($result), 'wrong contract version rejected');
check($GLOBALS['wpdb']->writes === $before_writes, 'wrong version writes nothing');

// One invalid record rejects the whole batch before any write.
$invalid = valid_body();
$invalid['states']['groq:model-2']['consecutive_failures'] = '2';
$result = la_provider_health_v2_write(new FakeRequest($invalid));
check(is_wp_error($result), 'invalid record rejected');
check($GLOBALS['wpdb']->writes === $before_writes, 'invalid batch writes nothing');

// Invalid key and >100 entries are rejected.
$invalid = valid_body(1);
$invalid['states']['bad key'] = $invalid['states']['groq:model-1'];
unset($invalid['states']['groq:model-1']);
check(is_wp_error(la_provider_health_v2_write(new FakeRequest($invalid))), 'invalid key rejected');
check(is_wp_error(la_provider_health_v2_write(new FakeRequest(valid_body(101)))), 'oversized batch rejected');
check($GLOBALS['wpdb']->writes === $before_writes, 'key and capacity failures write nothing');

// Input serialization failure is detected before opening a transaction.
$GLOBALS['encode_calls'] = 0;
$GLOBALS['fail_encode_on'] = 1;
$result = la_provider_health_v2_write(new FakeRequest(valid_body(1)));
check(is_wp_error($result), 'input serialization failure rejected');
check($GLOBALS['wpdb']->writes === $before_writes, 'serialization failure writes nothing');
$GLOBALS['fail_encode_on'] = 0;

// A merged-record serialization failure also occurs before the first DB write.
$GLOBALS['encode_calls'] = 0;
$GLOBALS['fail_encode_on'] = 2;
$result = la_provider_health_v2_write(new FakeRequest(valid_body(1)));
check(is_wp_error($result), 'merged serialization failure rejected');
check($GLOBALS['wpdb']->writes === $before_writes, 'merged serialization failure writes nothing');
$GLOBALS['fail_encode_on'] = 0;

// A failure on the second write rolls back the first write in the same batch.
$GLOBALS['wpdb'] = new FakeWpdb();
$GLOBALS['wpdb']->fail_replace_at = 2;
$result = la_provider_health_v2_write(new FakeRequest(valid_body(2)));
check(is_wp_error($result), 'mid-batch write failure rejected');
check(count($GLOBALS['wpdb']->rows) === 0, 'mid-batch write failure rolls back all rows');

// A database read error also rolls back the transaction.
$GLOBALS['wpdb'] = new FakeWpdb();
$GLOBALS['wpdb']->fail_read = true;
$result = la_provider_health_v2_write(new FakeRequest(valid_body(1)));
check(is_wp_error($result), 'database read failure rejected');
check(count($GLOBALS['wpdb']->rows) === 0, 'read failure commits no rows');

// A failed COMMIT must not produce a success acknowledgement.
$GLOBALS['wpdb'] = new FakeWpdb();
$GLOBALS['wpdb']->fail_commit = true;
$result = la_provider_health_v2_write(new FakeRequest(valid_body(1)));
check(is_wp_error($result), 'commit failure rejected');
check(count($GLOBALS['wpdb']->rows) === 0, 'commit failure rolls back rows');

// Python/PHP merge parity: operation context, equal timestamps, expired cooldown.
$local = array(
    'last_failure' => 10.0, 'last_success' => 5.0,
    'last_operation' => 'general_guide_composition',
    'failures' => 1, 'consecutive_failures' => 1, 'cooldown_until' => 20.0,
);
$remote = array(
    'last_failure' => 30.0, 'last_success' => 5.0,
    'last_operation' => 'hrn_relational',
    'failures' => 2, 'consecutive_failures' => 2, 'cooldown_until' => 90.0,
    'last_error' => 'read operation timed out', 'category' => 'provider_failure',
);
$merged = la_provider_health_v2_merge($local, $remote, 31.0);
check($merged['last_operation'] === 'hrn_relational', 'newer failure operation merged');
check($merged['state'] === 'open', 'unexpired cooldown remains open');

$local = array(
    'last_failure' => 30.0, 'last_success' => 5.0,
    'last_operation' => 'general_guide_composition',
    'failures' => 2, 'consecutive_failures' => 1, 'cooldown_until' => 90.0,
);
$remote = array(
    'last_failure' => 30.0, 'last_success' => 5.0,
    'last_operation' => 'hrn_relational',
    'failures' => 3, 'consecutive_failures' => 2, 'cooldown_until' => 100.0,
    'last_error' => 'request timed out', 'category' => 'provider_failure',
);
$merged = la_provider_health_v2_merge($local, $remote, 31.0);
check($merged['failures'] === 3 && $merged['consecutive_failures'] === 2, 'equal timestamp counters reconciled');
check($merged['last_operation'] === 'hrn_relational', 'equal timestamp operation follows higher failure count');

$merged = la_provider_health_v2_merge(
    array('last_failure' => 20.0, 'last_success' => 10.0, 'cooldown_until' => 25.0, 'quarantine_until' => 0.0),
    array('last_failure' => 20.0, 'last_success' => 10.0, 'cooldown_until' => 25.0, 'quarantine_until' => 0.0),
    30.0
);
check($merged['state'] === 'half_open', 'expired cooldown becomes half-open');
check($merged['probe_in_flight'] === false, 'probe ownership never restores');

$merged = la_provider_health_v2_merge(
    array('last_quality_failure' => 30.0, 'last_quality_success' => 10.0, 'quality_failures' => 2, 'quality_cooldown_until' => 330.0, 'quality_error' => 'reject'),
    array('last_quality_failure' => 30.0, 'last_quality_success' => 40.0, 'quality_failures' => 0, 'quality_cooldown_until' => 0.0, 'quality_error' => ''),
    41.0
);
check($merged['quality_failures'] === 0 && $merged['quality_cooldown_until'] === 0.0, 'newer quality success clears cooldown');

// GET is deterministic and bounded to 100 records.
$GLOBALS['wpdb'] = new FakeWpdb();
for ($i = 100; $i >= 0; $i--) {
    $key = sprintf('key:%03d', $i);
    $GLOBALS['wpdb']->rows[$key] = array(
        'state_key' => $key,
        'payload' => json_encode(array('provider' => 'test', 'probe_in_flight' => true)),
        'updated_at' => '2026-11-01 00:00:00',
    );
}
$response = la_provider_health_v2_read();
check(!is_wp_error($response), 'GET returns a valid response');
$read_states = get_object_vars($response->data['states']);
check(count($read_states) === 100, 'GET respects the explicit 100-row capacity');
check(array_key_first($read_states) === 'key:000', 'GET uses deterministic ascending key order');
check($read_states['key:000']['probe_in_flight'] === false, 'GET suppresses process-local probe ownership');

echo "PASS: WordPress provider-health v2 contract harness\n";
