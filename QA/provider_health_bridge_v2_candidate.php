<?php
/**
 * TEST candidate for the Living Archive Provider Health v2 WordPress bridge.
 *
 * This file is intentionally not loaded by WordPress and contains no secret.
 * Integrate only after TEST transaction and cross-language acceptance:
 * 1. Require this file from the existing plugin's main file.
 * 2. Replace its v1 route hook with add_action('rest_api_init', 'la_provider_health_v2_register_routes').
 * 3. Register la_provider_health_v2_install_schema on the main plugin activation hook.
 * The existing table is unchanged; no active WordPress file is modified here.
 */

if (!defined('LA_PROVIDER_HEALTH_V2_CONTRACT')) {
    define('LA_PROVIDER_HEALTH_V2_CONTRACT', 'v2');
}
if (!defined('LA_PROVIDER_HEALTH_V2_MAX_STATES')) {
    define('LA_PROVIDER_HEALTH_V2_MAX_STATES', 100);
}

function la_provider_health_v2_table_name() {
    global $wpdb;
    return $wpdb->prefix . 'la_provider_health';
}

/**
 * Controlled install/activation hook only. Never call from ordinary GET/POST.
 * The existing production table already uses this schema and InnoDB.
 */
function la_provider_health_v2_install_schema() {
    global $wpdb;
    require_once ABSPATH . 'wp-admin/includes/upgrade.php';
    $table = la_provider_health_v2_table_name();
    $charset = $wpdb->get_charset_collate();
    $sql = "CREATE TABLE {$table} (
        state_key varchar(191) NOT NULL,
        payload longtext NOT NULL,
        updated_at datetime NOT NULL,
        PRIMARY KEY  (state_key)
    ) ENGINE=InnoDB {$charset};";
    dbDelta($sql);
}

function la_provider_health_v2_error($code, $message, $status) {
    return new WP_Error($code, $message, array('status' => (int)$status));
}

function la_provider_health_v2_validate_batch($body) {
    if (!is_array($body) || ($body['contract_version'] ?? null) !== LA_PROVIDER_HEALTH_V2_CONTRACT) {
        return la_provider_health_v2_error(
            'la_provider_health_contract_mismatch',
            'A supported provider-health contract version is required.',
            400
        );
    }

    $states = $body['states'] ?? null;
    if (!is_array($states) || count($states) > LA_PROVIDER_HEALTH_V2_MAX_STATES) {
        return la_provider_health_v2_error(
            'la_provider_health_invalid_batch',
            'A bounded provider-health states object is required.',
            400
        );
    }

    $string_fields = array(
        'provider', 'operation', 'state', 'category', 'last_operation',
        'model', 'last_error', 'quality_error',
    );
    $key_fields = array('provider', 'operation', 'state', 'category', 'last_operation');
    $integer_fields = array('failures', 'consecutive_failures', 'quality_failures');
    $number_fields = array(
        'cooldown_until', 'quarantine_until', 'last_success', 'last_failure',
        'last_quality_failure', 'last_quality_success', 'quality_cooldown_until',
    );
    $allowed_fields = array_merge(
        $string_fields,
        $integer_fields,
        $number_fields,
        array('probe_in_flight')
    );

    $normalized_batch = array();
    foreach ($states as $key => $record) {
        if (!is_string($key) || strlen($key) < 1 || strlen($key) > 191
            || !preg_match('/^[a-z0-9_:@.\/-]{1,191}$/i', $key)) {
            return la_provider_health_v2_error(
                'la_provider_health_invalid_key',
                'A provider-health state key is invalid.',
                400
            );
        }
        if (!is_array($record)) {
            return la_provider_health_v2_error(
                'la_provider_health_invalid_record',
                'Every provider-health record must be an object.',
                400
            );
        }
        foreach (array_keys($record) as $field) {
            if (!is_string($field) || !in_array($field, $allowed_fields, true)) {
                return la_provider_health_v2_error(
                    'la_provider_health_unknown_field',
                    'A provider-health record contains an unsupported field.',
                    400
                );
            }
        }

        $normalized = array();
        foreach ($string_fields as $field) {
            if (!array_key_exists($field, $record)) {
                continue;
            }
            if (!is_string($record[$field])) {
                return la_provider_health_v2_error(
                    'la_provider_health_invalid_field_type',
                    'A provider-health text field has an invalid type.',
                    400
                );
            }
            if (in_array($field, $key_fields, true)) {
                $normalized[$field] = sanitize_key($record[$field]);
            } else {
                $limit = $field === 'last_error' ? 500 : ($field === 'quality_error' ? 300 : 191);
                $normalized[$field] = mb_substr(sanitize_text_field($record[$field]), 0, $limit);
            }
        }

        if (isset($normalized['state']) && !in_array(
            $normalized['state'],
            array('healthy', 'degraded', 'open', 'half_open'),
            true
        )) {
            return la_provider_health_v2_error(
                'la_provider_health_invalid_state',
                'A provider-health state value is unsupported.',
                400
            );
        }

        foreach ($integer_fields as $field) {
            if (!array_key_exists($field, $record)) {
                continue;
            }
            if (!is_int($record[$field]) || $record[$field] < 0) {
                return la_provider_health_v2_error(
                    'la_provider_health_invalid_counter',
                    'Provider-health counters must be non-negative integers.',
                    400
                );
            }
            $normalized[$field] = $record[$field];
        }

        foreach ($number_fields as $field) {
            if (!array_key_exists($field, $record)) {
                continue;
            }
            $value = $record[$field];
            if ((!is_int($value) && !is_float($value))
                || !is_finite((float)$value)
                || (float)$value < 0) {
                return la_provider_health_v2_error(
                    'la_provider_health_invalid_timestamp',
                    'Provider-health timestamps and cooldowns must be finite non-negative numbers.',
                    400
                );
            }
            $normalized[$field] = (float)$value;
        }

        if (array_key_exists('probe_in_flight', $record) && !is_bool($record['probe_in_flight'])) {
            return la_provider_health_v2_error(
                'la_provider_health_invalid_probe_flag',
                'The probe ownership flag must be boolean.',
                400
            );
        }
        // Probe ownership is process-local and is never accepted as durable state.
        $normalized['probe_in_flight'] = false;

        $encoded = wp_json_encode($normalized);
        if (!is_string($encoded) || $encoded === '') {
            return la_provider_health_v2_error(
                'la_provider_health_serialization_failed',
                'A provider-health record could not be serialized.',
                400
            );
        }
        $normalized_batch[] = array(
            'key' => $key,
            'record' => $normalized,
        );
    }

    return $normalized_batch;
}

function la_provider_health_v2_merge($old, $incoming, $now = null) {
    if (!is_array($old) || !$old) {
        $merged = is_array($incoming) ? $incoming : array();
        $merged['probe_in_flight'] = false;
        return $merged;
    }

    $now = $now === null ? time() : (float)$now;
    $old_failure = (float)($old['last_failure'] ?? 0);
    $new_failure = (float)($incoming['last_failure'] ?? 0);
    $old_success = (float)($old['last_success'] ?? 0);
    $new_success = (float)($incoming['last_success'] ?? 0);
    $latest_failure = max($old_failure, $new_failure);
    $latest_success = max($old_success, $new_success);
    $merged = $old;

    if ($new_failure > $old_failure) {
        foreach (array(
            'failures', 'consecutive_failures', 'last_error', 'category',
            'cooldown_until', 'quarantine_until', 'last_operation',
        ) as $field) {
            if (array_key_exists($field, $incoming)) {
                $merged[$field] = $incoming[$field];
            }
        }
    } elseif ($new_failure === $old_failure && $new_failure > 0) {
        $old_consecutive = (int)($old['consecutive_failures'] ?? 0);
        $new_consecutive = (int)($incoming['consecutive_failures'] ?? 0);
        $merged['failures'] = max((int)($old['failures'] ?? 0), (int)($incoming['failures'] ?? 0));
        $merged['consecutive_failures'] = max($old_consecutive, $new_consecutive);
        $merged['cooldown_until'] = max((float)($old['cooldown_until'] ?? 0), (float)($incoming['cooldown_until'] ?? 0));
        $merged['quarantine_until'] = max((float)($old['quarantine_until'] ?? 0), (float)($incoming['quarantine_until'] ?? 0));
        if (!empty($incoming['last_error'])) {
            $merged['last_error'] = $incoming['last_error'];
            $merged['category'] = $incoming['category'] ?? ($old['category'] ?? '');
        }
        if ($new_consecutive > $old_consecutive && !empty($incoming['last_operation'])) {
            $merged['last_operation'] = $incoming['last_operation'];
        } elseif (empty($old['last_operation']) && !empty($incoming['last_operation'])) {
            $merged['last_operation'] = $incoming['last_operation'];
        }
    }

    $merged['last_failure'] = $latest_failure;
    $merged['last_success'] = $latest_success;
    $merged['probe_in_flight'] = false;

    $old_quality_failure = (float)($old['last_quality_failure'] ?? 0);
    $new_quality_failure = (float)($incoming['last_quality_failure'] ?? 0);
    $old_quality_success = (float)($old['last_quality_success'] ?? 0);
    $new_quality_success = (float)($incoming['last_quality_success'] ?? 0);
    $latest_quality_failure = max($old_quality_failure, $new_quality_failure);
    $latest_quality_success = max($old_quality_success, $new_quality_success);
    $merged['last_quality_failure'] = $latest_quality_failure;
    $merged['last_quality_success'] = $latest_quality_success;

    if ($new_quality_failure > $old_quality_failure) {
        foreach (array('quality_failures', 'quality_cooldown_until', 'quality_error') as $field) {
            if (array_key_exists($field, $incoming)) {
                $merged[$field] = $incoming[$field];
            }
        }
    } elseif ($new_quality_failure === $old_quality_failure && $new_quality_failure > 0) {
        $merged['quality_failures'] = max((int)($old['quality_failures'] ?? 0), (int)($incoming['quality_failures'] ?? 0));
        $merged['quality_cooldown_until'] = max((float)($old['quality_cooldown_until'] ?? 0), (float)($incoming['quality_cooldown_until'] ?? 0));
        if (!empty($incoming['quality_error'])) {
            $merged['quality_error'] = $incoming['quality_error'];
        }
    }

    if ($latest_quality_success >= $latest_quality_failure) {
        $merged['quality_failures'] = 0;
        $merged['quality_cooldown_until'] = 0.0;
        $merged['quality_error'] = '';
    }

    if ($latest_success >= $latest_failure) {
        $merged['state'] = 'healthy';
        $merged['consecutive_failures'] = 0;
        $merged['cooldown_until'] = 0.0;
        $merged['quarantine_until'] = 0.0;
        $merged['last_error'] = '';
        $merged['category'] = '';
    } else {
        $merged['state'] = max(
            (float)($merged['cooldown_until'] ?? 0),
            (float)($merged['quarantine_until'] ?? 0)
        ) > $now ? 'open' : 'half_open';
    }

    return $merged;
}

/**
 * Replace the existing v1 rest_api_init route block with this registration.
 * Keep the current la_provider_health_authorized permission callback unchanged.
 */
function la_provider_health_v2_register_routes() {
    register_rest_route('living-archive/v1', '/provider-health', array(
        array(
            'methods' => WP_REST_Server::READABLE,
            'permission_callback' => 'la_provider_health_authorized',
            'callback' => 'la_provider_health_v2_read',
        ),
        array(
            'methods' => WP_REST_Server::CREATABLE,
            'permission_callback' => 'la_provider_health_authorized',
            'callback' => 'la_provider_health_v2_write',
        ),
    ));
}

function la_provider_health_v2_read() {
    global $wpdb;
    $table = la_provider_health_v2_table_name();
    // Stable capacity policy: retain the 100 most recently updated states;
    // use state_key as a deterministic tie-breaker and response ordering.
    // This prevents older alphabetically early keys from starving new models.
    $rows = $wpdb->get_results(
        "SELECT state_key, payload FROM {$table} ORDER BY updated_at DESC, state_key ASC LIMIT 100",
        ARRAY_A
    );
    if ($rows === false || !empty($wpdb->last_error)) {
        return la_provider_health_v2_error(
            'la_provider_health_read_failed',
            'Shared provider-health state could not be read.',
            500
        );
    }

    $states = array();
    foreach ((array)$rows as $row) {
        $key = (string)($row['state_key'] ?? '');
        $payload = (string)($row['payload'] ?? '');
        $value = json_decode($payload, true);
        if ($key === '' || !is_array($value)) {
            return la_provider_health_v2_error(
                'la_provider_health_corrupt_row',
                'A stored provider-health record is invalid.',
                500
            );
        }
        $value['probe_in_flight'] = false;
        $states[$key] = $value;
    }

    $response = rest_ensure_response(array(
        'contract_version' => LA_PROVIDER_HEALTH_V2_CONTRACT,
        'states' => (object)$states,
    ));
    $response->header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0');
    $response->header('Pragma', 'no-cache');
    return $response;
}

function la_provider_health_v2_write($request) {
    global $wpdb;
    // get_json_params() loses the distinction between JSON objects and arrays
    // when WordPress decodes associatively. Inspect the raw JSON shape first so
    // an empty/list-shaped states value cannot masquerade as an object.
    $raw_body = is_object($request) && method_exists($request, 'get_body')
        ? $request->get_body()
        : null;
    $decoded_shape = is_string($raw_body) ? json_decode($raw_body) : null;
    if (!($decoded_shape instanceof stdClass)
        || !property_exists($decoded_shape, 'states')
        || !($decoded_shape->states instanceof stdClass)) {
        return la_provider_health_v2_error(
            'la_provider_health_invalid_batch_shape',
            'The request body and states collection must be JSON objects.',
            400
        );
    }
    foreach ($decoded_shape->states as $record) {
        if (!($record instanceof stdClass)) {
            return la_provider_health_v2_error(
                'la_provider_health_invalid_record_shape',
                'Every provider-health record must be a JSON object.',
                400
            );
        }
    }
    $body = json_decode($raw_body, true);
    $batch = la_provider_health_v2_validate_batch($body);
    if (is_wp_error($batch)) {
        return $batch;
    }

    $table = la_provider_health_v2_table_name();
    $written = 0;

    // An empty object is a valid no-op acknowledgement; avoid opening a DB transaction.
    if (!$batch) {
        $response = rest_ensure_response(array(
            'contract_version' => LA_PROVIDER_HEALTH_V2_CONTRACT,
            'success' => true,
            'submitted' => 0,
            'written' => 0,
        ));
        $response->header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0');
        $response->header('Pragma', 'no-cache');
        return $response;
    }

    if ($wpdb->query('START TRANSACTION') === false) {
        return la_provider_health_v2_error(
            'la_provider_health_transaction_start_failed',
            'Shared provider-health transaction could not be started.',
            500
        );
    }

    try {
        // Materialize missing keys before the locking read. Two transactions
        // cannot both hold a gap lock for the same absent key and then race to
        // insert it: INSERT IGNORE serializes the unique-key creation first.
        // The placeholder rows are inside this transaction and are replaced
        // with fully merged payloads before commit; rollback removes them.
        $updated_at = current_time('mysql', true);
        $seed_values = array_fill(0, count($batch), '(%s, %s, %s)');
        $seed_args = array();
        foreach ($batch as $entry) {
            $seed_args[] = $entry['key'];
            $seed_args[] = '{}';
            $seed_args[] = $updated_at;
        }
        $seed_sql = "INSERT IGNORE INTO {$table} (state_key, payload, updated_at) VALUES "
            . implode(',', $seed_values);
        $prepared_seed_sql = $wpdb->prepare($seed_sql, $seed_args);
        if (!is_string($prepared_seed_sql) || $prepared_seed_sql === '') {
            throw new RuntimeException('Provider-health key reservation could not be prepared.');
        }
        $seed_result = $wpdb->query($prepared_seed_sql);
        if ($seed_result === false || !empty($wpdb->last_error)) {
            throw new RuntimeException('Provider-health keys could not be reserved.');
        }

        // One indexed locking read for the complete batch, not one SELECT per state.
        // Every requested key now exists, so FOR UPDATE takes row locks rather
        // than competing gap locks for previously absent keys.
        $keys = array_column($batch, 'key');
        $key_placeholders = implode(',', array_fill(0, count($keys), '%s'));
        $select_sql = $wpdb->prepare(
            "SELECT state_key, payload FROM {$table} WHERE state_key IN ({$key_placeholders}) FOR UPDATE",
            $keys
        );
        if (!is_string($select_sql) || $select_sql === '') {
            throw new RuntimeException('Provider-health batch read could not be prepared.');
        }
        $existing_rows = $wpdb->get_results($select_sql, ARRAY_A);
        if ($existing_rows === false || !empty($wpdb->last_error)) {
            throw new RuntimeException('Provider-health batch read failed.');
        }

        $existing_by_key = array();
        foreach ((array)$existing_rows as $row) {
            $key = (string)($row['state_key'] ?? '');
            $payload = (string)($row['payload'] ?? '');
            $existing = json_decode($payload, true);
            if ($key === '' || !is_array($existing)) {
                throw new RuntimeException('Stored provider-health row is corrupt.');
            }
            $existing_by_key[$key] = $existing;
        }

        // Merge and serialize every record before the single set-based write.
        $prepared = array();
        foreach ($batch as $entry) {
            $key = $entry['key'];
            $existing = $existing_by_key[$key] ?? array();
            $merged = la_provider_health_v2_merge($existing, $entry['record']);
            $encoded = wp_json_encode($merged);
            if (!is_string($encoded) || $encoded === '') {
                throw new RuntimeException('Merged provider-health row could not be serialized.');
            }
            $prepared[] = array('key' => $key, 'payload' => $encoded);
        }

        // One multi-row upsert commits the complete prepared batch. VALUES()
        // remains compatible with the site's MariaDB 11.x and supported MySQL.
        $value_placeholders = array_fill(0, count($prepared), '(%s, %s, %s)');
        $write_args = array();
        foreach ($prepared as $entry) {
            $write_args[] = $entry['key'];
            $write_args[] = $entry['payload'];
            $write_args[] = $updated_at;
        }
        $upsert_sql = "INSERT INTO {$table} (state_key, payload, updated_at) VALUES "
            . implode(',', $value_placeholders)
            . " ON DUPLICATE KEY UPDATE payload = VALUES(payload), updated_at = VALUES(updated_at)";
        $prepared_sql = $wpdb->prepare($upsert_sql, $write_args);
        if (!is_string($prepared_sql) || $prepared_sql === '') {
            throw new RuntimeException('Provider-health batch write could not be prepared.');
        }

        $result = $wpdb->query($prepared_sql);
        if ($result === false || !empty($wpdb->last_error)) {
            throw new RuntimeException('Provider-health batch write failed.');
        }
        // A successful single SQL statement inside this transaction commits all
        // submitted keys; affected-row counts are not used because MySQL/MariaDB
        // report different values for inserts, updates, and unchanged updates.
        $written = count($prepared);

        if ($wpdb->query('COMMIT') === false || !empty($wpdb->last_error)) {
            throw new RuntimeException('Provider-health transaction commit failed.');
        }
    } catch (Throwable $error) {
        $wpdb->query('ROLLBACK');
        return la_provider_health_v2_error(
            'la_provider_health_batch_rolled_back',
            'The provider-health batch was not committed.',
            500
        );
    }

    $response = rest_ensure_response(array(
        'contract_version' => LA_PROVIDER_HEALTH_V2_CONTRACT,
        'success' => true,
        'submitted' => count($batch),
        'written' => $written,
    ));
    $response->header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0');
    $response->header('Pragma', 'no-cache');
    return $response;
}
