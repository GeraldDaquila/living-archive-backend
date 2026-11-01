<?php
declare(strict_types=1);

$base = rtrim((string)getenv('PROVIDER_HEALTH_WP_BASE_URL'), '/');
$secret = (string)getenv('PROVIDER_HEALTH_WP_SECRET');
if ($base === '' || $secret === '') {
    throw new RuntimeException('Ephemeral WordPress URL and test secret are required.');
}
$endpoint = $base . '/?rest_route=/living-archive/v1/provider-health';

function wp_check($condition, $message) {
    if (!$condition) {
        throw new RuntimeException('FAIL: ' . $message);
    }
}

function wp_request($url, $method, $body = null, $authenticated = true) {
    global $secret;
    $headers = array('Accept: application/json');
    if ($body !== null) {
        $headers[] = 'Content-Type: application/json';
    }
    if ($authenticated) {
        $headers[] = 'X-Living-Archive-Provider-Key: ' . $secret;
    }
    $options = array(
        'http' => array(
            'method' => $method,
            'header' => implode("\r\n", $headers),
            'ignore_errors' => true,
            'follow_location' => 0,
            'max_redirects' => 0,
            'timeout' => 15,
        ),
    );
    if ($body !== null) {
        $options['http']['content'] = $body;
    }
    $context = stream_context_create($options);
    $response = @file_get_contents($url, false, $context);
    $status_line = $http_response_header[0] ?? '';
    preg_match('/\s([0-9]{3})\s/', $status_line, $match);
    $status = isset($match[1]) ? (int)$match[1] : 0;
    $decoded = is_string($response) ? json_decode($response, true) : null;
    return array($status, $decoded, is_string($response) ? $response : '');
}

list($unauthorized_status) = wp_request($endpoint, 'GET', null, false);
wp_check(in_array($unauthorized_status, array(401, 403), true), 'REST route rejects missing shared secret');

$invalid_contract = json_encode(array(
    'contract_version' => 'v1',
    'states' => new stdClass(),
));
list($invalid_status) = wp_request($endpoint, 'POST', $invalid_contract);
wp_check($invalid_status === 400, 'REST route rejects wrong contract version');

$invalid_shape = '{"contract_version":"v2","states":[]}';
list($shape_status) = wp_request($endpoint, 'POST', $invalid_shape);
wp_check($shape_status === 400, 'REST route rejects list-shaped states collection');

$empty_body = json_encode(array(
    'contract_version' => 'v2',
    'states' => new stdClass(),
));
list($empty_status, $empty_response) = wp_request($endpoint, 'POST', $empty_body);
wp_check($empty_status === 200, 'REST route accepts an empty object as a no-op batch');
wp_check(($empty_response['success'] ?? false) === true, 'empty batch returns explicit success');
wp_check(($empty_response['submitted'] ?? null) === 0 && ($empty_response['written'] ?? null) === 0, 'empty batch acknowledgement is exact');

$initial_states = array(
    'groq:wp-model-a' => array(
        'provider' => 'groq',
        'model' => 'wp-model-a',
        'operation' => 'hrn_relational',
        'state' => 'open',
        'failures' => 1,
        'consecutive_failures' => 1,
        'last_failure' => 20,
        'last_success' => 10,
        'cooldown_until' => 80,
        'last_operation' => 'hrn_relational',
        'probe_in_flight' => true,
    ),
    'groq:wp-model-b' => array(
        'provider' => 'groq',
        'model' => 'wp-model-b',
        'operation' => 'mini_use',
        'state' => 'healthy',
        'failures' => 0,
        'consecutive_failures' => 0,
        'last_success' => 30,
        'last_failure' => 0,
        'probe_in_flight' => false,
    ),
);
$initial_body = json_encode(array(
    'contract_version' => 'v2',
    'states' => (object)$initial_states,
));
list($initial_status, $initial_response) = wp_request($endpoint, 'POST', $initial_body);
wp_check($initial_status === 200, 'real WordPress REST POST accepts valid state batch');
wp_check(($initial_response['success'] ?? false) === true, 'real WordPress REST POST returns success');
wp_check(($initial_response['submitted'] ?? null) === 2 && ($initial_response['written'] ?? null) === 2, 'real WordPress REST POST acknowledges exact counts');

list($get_status, $get_response) = wp_request($endpoint, 'GET');
wp_check($get_status === 200, 'real WordPress REST GET succeeds');
wp_check(($get_response['contract_version'] ?? null) === 'v2', 'real WordPress REST GET returns v2 contract');
$get_states = $get_response['states'] ?? array();
wp_check(isset($get_states['groq:wp-model-a'], $get_states['groq:wp-model-b']), 'real WordPress REST GET returns both stored states');
wp_check(($get_states['groq:wp-model-a']['probe_in_flight'] ?? null) === false, 'real WordPress REST GET suppresses process-local probe ownership');

function wp_concurrent_posts($url, array $bodies) {
    global $secret;
    if (!function_exists('curl_multi_init')) {
        throw new RuntimeException('cURL multi support is required for the concurrent REST acceptance test.');
    }

    $multi = curl_multi_init();
    $handles = array();
    foreach ($bodies as $index => $body) {
        $handle = curl_init($url);
        curl_setopt_array($handle, array(
            CURLOPT_POST => true,
            CURLOPT_POSTFIELDS => $body,
            CURLOPT_HTTPHEADER => array(
                'Accept: application/json',
                'Content-Type: application/json',
                'X-Living-Archive-Provider-Key: ' . $secret,
            ),
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_FOLLOWLOCATION => false,
            CURLOPT_TIMEOUT => 15,
        ));
        curl_multi_add_handle($multi, $handle);
        $handles[$index] = $handle;
    }

    do {
        $multi_status = curl_multi_exec($multi, $running);
        if ($running && $multi_status === CURLM_OK) {
            $selected = curl_multi_select($multi, 1.0);
            if ($selected === -1) {
                usleep(1000);
            }
        }
    } while ($running && $multi_status === CURLM_OK);

    $results = array();
    foreach ($handles as $index => $handle) {
        $raw = curl_multi_getcontent($handle);
        $results[$index] = array(
            'status' => (int)curl_getinfo($handle, CURLINFO_HTTP_CODE),
            'body' => is_string($raw) ? json_decode($raw, true) : null,
        );
        curl_multi_remove_handle($multi, $handle);
        curl_close($handle);
    }
    curl_multi_close($multi);

    if ($multi_status !== CURLM_OK) {
        throw new RuntimeException('Concurrent provider-health HTTP requests did not complete cleanly.');
    }
    return $results;
}

$race_key = 'groq:000-concurrent-new-key';
$race_body_old = json_encode(array(
    'contract_version' => 'v2',
    'states' => (object)array(
        $race_key => array(
            'provider' => 'groq',
            'model' => 'concurrent-new-key',
            'operation' => 'hrn_relational',
            'state' => 'open',
            'failures' => 1,
            'consecutive_failures' => 1,
            'last_failure' => 2001,
            'last_success' => 0,
            'cooldown_until' => 3000,
            'last_operation' => 'hrn_relational',
            'last_error' => 'older concurrent failure',
        ),
    ),
));
$race_body_new = json_encode(array(
    'contract_version' => 'v2',
    'states' => (object)array(
        $race_key => array(
            'provider' => 'groq',
            'model' => 'concurrent-new-key',
            'operation' => 'general_guide_composition',
            'state' => 'open',
            'failures' => 2,
            'consecutive_failures' => 2,
            'last_failure' => 2002,
            'last_success' => 0,
            'cooldown_until' => 3100,
            'last_operation' => 'general_guide_composition',
            'last_error' => 'newer concurrent failure',
        ),
    ),
));
$race_results = wp_concurrent_posts($endpoint, array($race_body_old, $race_body_new));
foreach ($race_results as $index => $race_result) {
    wp_check($race_result['status'] === 200, 'concurrent new-key POST ' . $index . ' succeeds without deadlock or partial failure');
    wp_check(($race_result['body']['success'] ?? false) === true, 'concurrent new-key POST ' . $index . ' returns success');
    wp_check(($race_result['body']['submitted'] ?? null) === 1 && ($race_result['body']['written'] ?? null) === 1, 'concurrent new-key POST ' . $index . ' acknowledges exact counts');
}
list($race_get_status, $race_get_response) = wp_request($endpoint, 'GET');
wp_check($race_get_status === 200, 'GET after concurrent new-key writes succeeds');
$race_state = $race_get_response['states'][$race_key] ?? array();
wp_check(($race_state['last_failure'] ?? null) === 2002.0, 'concurrent new-key writes retain the newer failure timestamp');
wp_check(($race_state['last_operation'] ?? null) === 'general_guide_composition', 'concurrent new-key writes retain the newer operation context');
wp_check(($race_state['consecutive_failures'] ?? null) === 2, 'concurrent new-key writes retain the higher consecutive failure count');

$bulk_states = new stdClass();
for ($i = 1; $i <= 100; $i++) {
    $model = sprintf('bulk-%03d', $i);
    $key = 'groq:' . $model;
    $bulk_states->{$key} = array(
        'provider' => 'groq',
        'model' => $model,
        'operation' => 'hrn_relational',
        'state' => 'healthy',
        'failures' => 0,
        'consecutive_failures' => 0,
        'last_success' => 100 + $i,
        'last_failure' => 0,
        'probe_in_flight' => false,
    );
}
$bulk_body = json_encode(array(
    'contract_version' => 'v2',
    'states' => $bulk_states,
));
list($bulk_status, $bulk_response) = wp_request($endpoint, 'POST', $bulk_body);
wp_check($bulk_status === 200, 'real WordPress REST accepts maximum 100-record batch');
wp_check(($bulk_response['submitted'] ?? null) === 100 && ($bulk_response['written'] ?? null) === 100, 'real WordPress REST acknowledges maximum batch exactly');

list($bulk_get_status, $bulk_get_response) = wp_request($endpoint, 'GET');
wp_check($bulk_get_status === 200, 'real WordPress REST GET after bulk write succeeds');
$bulk_get_states = $bulk_get_response['states'] ?? array();
wp_check(count($bulk_get_states) === 100, 'real WordPress REST GET retains exactly the 100 most recently updated states');
wp_check(isset($bulk_get_states['groq:bulk-001'], $bulk_get_states['groq:bulk-100']), 'real WordPress REST GET retains the full recent bulk window');

$pdo = new PDO(
    (string)getenv('PROVIDER_HEALTH_MARIADB_DSN'),
    (string)getenv('PROVIDER_HEALTH_MARIADB_USER'),
    (string)getenv('PROVIDER_HEALTH_MARIADB_PASSWORD'),
    array(PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION)
);
$trigger = 'provider_health_v2_fail_second';
$pdo->exec("DROP TRIGGER IF EXISTS {$trigger}");
$pdo->exec(
    "CREATE TRIGGER {$trigger}
     BEFORE INSERT ON wp_la_provider_health
     FOR EACH ROW
     BEGIN
       IF NEW.state_key = 'groq:rollback-probe' THEN
         SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'synthetic provider-health write failure';
       END IF;
     END"
);
try {
    $rollback_states = new stdClass();
    $rollback_states->{'groq:rollback-before'} = $initial_states['groq:wp-model-a'];
    $rollback_states->{'groq:rollback-probe'} = $initial_states['groq:wp-model-b'];
    $rollback_body = json_encode(array(
        'contract_version' => 'v2',
        'states' => $rollback_states,
    ));
    list($rollback_status) = wp_request($endpoint, 'POST', $rollback_body);
    wp_check($rollback_status === 500, 'real WordPress REST reports a failed multi-row write');
    $rollback_count = (int)$pdo->query(
        "SELECT COUNT(*) FROM wp_la_provider_health WHERE state_key IN ('groq:rollback-before', 'groq:rollback-probe')"
    )->fetchColumn();
    wp_check($rollback_count === 0, 'real WordPress/MariaDB rolls back the entire multi-row write after a mid-batch trigger failure');
} finally {
    $pdo->exec("DROP TRIGGER IF EXISTS {$trigger}");
}

echo "PASS: WordPress 7.1.4 REST route, auth, schema activation, v2 contract, and 100-record MariaDB batch integration\n";
