<?php
declare(strict_types=1);

define('ARRAY_A', 'ARRAY_A');
define('ABSPATH', '/wordpress/');

class WP_REST_Server { const READABLE = 'GET'; const CREATABLE = 'POST'; }
$GLOBALS['registered_routes'] = array();
function register_rest_route($namespace, $route, $args) {
    $GLOBALS['registered_routes'][] = array($namespace, $route, $args);
}

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
if (!function_exists('mb_substr')) { function mb_substr($value, $start, $length = null) { return $length === null ? substr($value, $start) : substr($value, $start, $length); } }
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
    private $raw_body;
    public function __construct($body, $raw_body = null) {
        $this->body = $body;
        $this->raw_body = $raw_body;
    }
    public function get_json_params() { return $this->body; }
    public function get_body() {
        return $this->raw_body !== null
            ? $this->raw_body
            : json_encode((object)$this->body, JSON_FORCE_OBJECT);
    }
}

class FakeWpdb {
    public $prefix = 'wp_';
    public $last_error = '';
    public $rows = array();
    public $writes = 0;
    public $batch_read_queries = 0;
    public $bulk_write_queries = 0;
    public $get_var_calls = 0;
    public $replace_calls = 0;
    public $fail_bulk_write = false;
    public $fail_read = false;
    public $fail_commit = false;
    private $backup = null;
    private $pending_select_keys = null;
    private $pending_bulk_values = null;

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
        if ($sql === 'FAKE_PROVIDER_HEALTH_BULK_UPSERT') {
            $this->bulk_write_queries++;
            $values = $this->pending_bulk_values;
            $this->pending_bulk_values = null;
            if (!is_array($values) || count($values) % 3 !== 0) {
                $this->last_error = 'invalid simulated bulk-upsert arguments';
                return false;
            }
            $record_count = (int)(count($values) / 3);
            $apply_count = $this->fail_bulk_write ? min(1, $record_count) : $record_count;
            for ($i = 0; $i < $apply_count; $i++) {
                $offset = $i * 3;
                $key = (string)$values[$offset];
                $this->rows[$key] = array(
                    'state_key' => $key,
                    'payload' => (string)$values[$offset + 1],
                    'updated_at' => (string)$values[$offset + 2],
                );
                $this->writes++;
            }
            if ($this->fail_bulk_write) {
                $this->last_error = 'simulated bulk-upsert failure after partial row application';
                return false;
            }
            return $record_count;
        }
        return 0;
    }

    public function prepare($query, ...$args) {
        $values = count($args) === 1 && is_array($args[0]) ? array_values($args[0]) : $args;
        if (strpos($query, 'WHERE state_key IN') !== false) {
            $this->pending_select_keys = $values;
            return $query;
        }
        if (strpos($query, 'INSERT INTO') === 0 && strpos($query, 'ON DUPLICATE KEY UPDATE') !== false) {
            $this->pending_bulk_values = $values;
            return 'FAKE_PROVIDER_HEALTH_BULK_UPSERT';
        }
        $prepared = $query;
        foreach ($values as $value) {
            $prepared = preg_replace('/%s/', "'" . addslashes((string)$value) . "'", $prepared, 1);
        }
        return $prepared;
    }

    public function get_var($sql) {
        $this->get_var_calls++;
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
        $this->replace_calls++;
        $this->last_error = '';
        $this->writes++;
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
        if (strpos($sql, 'WHERE state_key IN') !== false) {
            $this->batch_read_queries++;
            $keys = is_array($this->pending_select_keys) ? $this->pending_select_keys : array();
            $this->pending_select_keys = null;
            $rows = array();
            foreach ($keys as $key) {
                if (isset($this->rows[$key])) {
                    $rows[] = $this->rows[$key];
                }
            }
            return $rows;
        }
        $rows = array_values($this->rows);
        usort($rows, function($a, $b) {
            $updated = strcmp($b['updated_at'], $a['updated_at']);
            return $updated !== 0 ? $updated : strcmp($a['state_key'], $b['state_key']);
        });
        return array_slice($rows, 0, 100);
    }
}

class MariaDbWpdbAdapter {
    public $prefix = 'wp_';
    public $last_error = '';
    public $statement_count = 0;
    public $batch_read_queries = 0;
    public $batch_write_queries = 0;
    public $fail_commit = false;
    private $pdo;

    public function __construct(PDO $pdo) {
        $this->pdo = $pdo;
    }

    public function query($sql) {
        $this->last_error = '';
        $this->statement_count++;
        try {
            if ($sql === 'START TRANSACTION') {
                $this->pdo->beginTransaction();
                return 1;
            }
            if ($sql === 'COMMIT') {
                if ($this->fail_commit) {
                    $this->last_error = 'simulated commit failure';
                    return false;
                }
                $this->pdo->commit();
                return 1;
            }
            if ($sql === 'ROLLBACK') {
                if ($this->pdo->inTransaction()) {
                    $this->pdo->rollBack();
                }
                return 1;
            }
            if (strpos($sql, 'INSERT INTO') === 0 && strpos($sql, 'ON DUPLICATE KEY UPDATE') !== false) {
                $this->batch_write_queries++;
            }
            return $this->pdo->exec($sql);
        } catch (Throwable $error) {
            $this->last_error = $error->getMessage();
            return false;
        }
    }

    public function prepare($query, ...$args) {
        $values = count($args) === 1 && is_array($args[0]) ? array_values($args[0]) : $args;
        $parts = explode('%s', $query);
        if (count($parts) !== count($values) + 1) {
            throw new RuntimeException('Prepare argument count does not match SQL placeholders.');
        }
        $prepared = array_shift($parts);
        foreach ($values as $index => $value) {
            $prepared .= $this->pdo->quote((string)$value) . $parts[$index];
        }
        return $prepared;
    }

    public function get_results($sql, $output) {
        $this->last_error = '';
        $this->statement_count++;
        if (strpos($sql, 'WHERE state_key IN') !== false) {
            $this->batch_read_queries++;
        }
        try {
            $statement = $this->pdo->query($sql);
            return $statement->fetchAll(PDO::FETCH_ASSOC);
        } catch (Throwable $error) {
            $this->last_error = $error->getMessage();
            return false;
        }
    }
}

require __DIR__ . '/provider_health_bridge_v2_candidate.php';

function check($condition, $message) {
    if (!$condition) {
        throw new RuntimeException('FAIL: ' . $message);
    }
}
la_provider_health_v2_register_routes();
check(count($GLOBALS['registered_routes']) === 1, 'v2 route registration present');
$route = $GLOBALS['registered_routes'][0];
check($route[0] === 'living-archive/v1' && $route[1] === '/provider-health', 'v2 route path preserved');
check($route[2][0]['callback'] === 'la_provider_health_v2_read', 'GET callback wired');
check($route[2][1]['callback'] === 'la_provider_health_v2_write', 'POST callback wired');
check($route[2][0]['permission_callback'] === 'la_provider_health_authorized', 'existing auth boundary preserved');
$result = la_provider_health_v2_write(new FakeRequest(array(), '[]'));
check(is_wp_error($result), 'top-level JSON array rejected');
$result = la_provider_health_v2_write(new FakeRequest(array(), '{"contract_version":"v2","states":[]}'));
check(is_wp_error($result), 'states JSON array rejected');
$result = la_provider_health_v2_write(new FakeRequest(array(), '{"contract_version":"v2","states":{"groq:model-a":[]}}'));
check(is_wp_error($result), 'array-shaped state record rejected');
$GLOBALS['wpdb'] = new FakeWpdb();
$result = la_provider_health_v2_write(new FakeRequest(array(), '{"contract_version":"v2","states":{}}'));
check(!is_wp_error($result), 'empty states JSON object accepted');


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
check($GLOBALS['wpdb']->batch_read_queries === 1, 'two-record batch uses one locking SELECT');
check($GLOBALS['wpdb']->bulk_write_queries === 1, 'two-record batch uses one multi-row upsert');
check($GLOBALS['wpdb']->get_var_calls === 0 && $GLOBALS['wpdb']->replace_calls === 0, 'batch path avoids per-record database calls');

// A maximum-size batch keeps the same constant SQL round-trip count.
$before_batch_reads = $GLOBALS['wpdb']->batch_read_queries;
$before_bulk_writes = $GLOBALS['wpdb']->bulk_write_queries;
$response = la_provider_health_v2_write(new FakeRequest(valid_body(100)));
check(!is_wp_error($response), '100-record batch accepted');
check($response->data['submitted'] === 100 && $response->data['written'] === 100, '100-record batch acknowledgement exact');
check($GLOBALS['wpdb']->batch_read_queries - $before_batch_reads === 1, '100-record batch still uses one locking SELECT');
check($GLOBALS['wpdb']->bulk_write_queries - $before_bulk_writes === 1, '100-record batch still uses one multi-row upsert');
check($GLOBALS['wpdb']->get_var_calls === 0 && $GLOBALS['wpdb']->replace_calls === 0, '100-record batch has no per-record database calls');
check(count($GLOBALS['wpdb']->rows) === 100, '100-record batch committed all unique states');

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
$GLOBALS['wpdb']->fail_bulk_write = true;
$result = la_provider_health_v2_write(new FakeRequest(valid_body(2)));
check(is_wp_error($result), 'bulk write failure rejected');
check(count($GLOBALS['wpdb']->rows) === 0, 'partial bulk write failure rolls back all rows');

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
        'updated_at' => gmdate('Y-m-d H:i:s', 1793491200 + $i),
    );
}
$response = la_provider_health_v2_read();
check(!is_wp_error($response), 'GET returns a valid response');
$read_states = get_object_vars($response->data['states']);
check(count($read_states) === 100, 'GET respects the explicit 100-row capacity');
check(array_key_first($read_states) === 'key:100', 'GET prioritizes most recently updated state');
check(!isset($read_states['key:000']), 'GET capacity excludes the oldest state, not newer keys');
check($read_states['key:100']['probe_in_flight'] === false, 'GET suppresses process-local probe ownership');

$fixtures = json_decode(file_get_contents(__DIR__ . '/provider_health_merge_fixtures_v2.json'), true);
check(is_array($fixtures) && ($fixtures['contract_version'] ?? '') === 'v2', 'shared Python/PHP merge fixtures load');
foreach ($fixtures['cases'] as $case) {
    $merged = la_provider_health_v2_merge($case['local'], $case['remote'], $case['now']);
    foreach ($case['expected'] as $field => $expected) {
        $actual = $merged[$field] ?? null;
        if (is_int($expected) || is_float($expected)) {
            check((is_int($actual) || is_float($actual)) && (float)$actual === (float)$expected, $case['name'] . ':' . $field);
        } else {
            check($actual === $expected, $case['name'] . ':' . $field);
        }
    }
}

$merged = la_provider_health_v2_merge(
    array(
        'last_failure' => 40.0,
        'last_success' => 5.0,
        'last_operation' => 'new_operation',
        'failures' => 4,
        'consecutive_failures' => 3,
        'cooldown_until' => 100.0,
        'last_error' => 'newer local error',
        'category' => 'rate_limited',
    ),
    array(
        'last_failure' => 20.0,
        'last_success' => 5.0,
        'last_operation' => 'stale_remote_operation',
        'failures' => 1,
        'consecutive_failures' => 1,
        'cooldown_until' => 50.0,
        'last_error' => 'stale remote error',
        'category' => 'provider_failure',
    ),
    45.0
);
check($merged['last_operation'] === 'new_operation', 'stale remote failure cannot overwrite operation context');
check($merged['last_error'] === 'newer local error', 'stale remote failure cannot overwrite error');
check($merged['cooldown_until'] === 100.0, 'stale remote failure cannot reduce or replace local cooldown');

if (getenv('PROVIDER_HEALTH_MARIADB_DSN')) {
    $pdo = new PDO(
        (string)getenv('PROVIDER_HEALTH_MARIADB_DSN'),
        (string)getenv('PROVIDER_HEALTH_MARIADB_USER'),
        (string)getenv('PROVIDER_HEALTH_MARIADB_PASSWORD'),
        array(PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION)
    );
    $pdo->exec("DROP TABLE IF EXISTS wp_la_provider_health");
    $pdo->exec(
        "CREATE TABLE wp_la_provider_health (
            state_key varchar(191) NOT NULL,
            payload longtext NOT NULL,
            updated_at datetime NOT NULL,
            PRIMARY KEY (state_key)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"
    );

    $mariadb = new MariaDbWpdbAdapter($pdo);
    $GLOBALS['wpdb'] = $mariadb;
    $GLOBALS['encode_calls'] = 0;
    $GLOBALS['fail_encode_on'] = 0;
    $before_statements = $mariadb->statement_count;
    $response = la_provider_health_v2_write(new FakeRequest(valid_body(100)));
    check(!is_wp_error($response), 'MariaDB accepts 100-record transaction');
    check($response->data['success'] === true, 'MariaDB returns explicit success acknowledgement');
    check($response->data['submitted'] === 100 && $response->data['written'] === 100, 'MariaDB acknowledgement counts are exact');
    check($mariadb->batch_read_queries === 1, 'MariaDB uses one locking batch SELECT');
    check($mariadb->batch_write_queries === 1, 'MariaDB uses one multi-row upsert');
    check($mariadb->statement_count - $before_statements === 4, '100-record MariaDB write uses exactly four statements including transaction boundaries');
    $row_count = (int)$pdo->query("SELECT COUNT(*) FROM wp_la_provider_health")->fetchColumn();
    check($row_count === 100, 'MariaDB committed all 100 records');

    // A commit failure after the real multi-row upsert must roll back the entire transaction.
    $rollback_body = valid_body(1);
    $rollback_record = $rollback_body['states']['groq:model-1'];
    $rollback_body['states'] = array('groq:rollback-probe' => $rollback_record);
    $mariadb->fail_commit = true;
    $result = la_provider_health_v2_write(new FakeRequest($rollback_body));
    check(is_wp_error($result), 'MariaDB commit failure is rejected');
    check(!$pdo->inTransaction(), 'MariaDB transaction is closed after rollback');
    $rollback_count = (int)$pdo->query(
        "SELECT COUNT(*) FROM wp_la_provider_health WHERE state_key = 'groq:rollback-probe'"
    )->fetchColumn();
    check($rollback_count === 0, 'MariaDB commit failure rolls back the upserted row');

    $pdo->exec("DROP TABLE wp_la_provider_health");
    echo "PASS: MariaDB 11.8 set-based upsert, four-statement batch budget, and transaction rollback\n";
}

echo "PASS: WordPress provider-health v2 contract harness\n";
