<?php
/**
 * Plugin Name: Living Archive — Provider Bridge Deadline Guard
 * Description: Reserves bounded time for one HRN relational mirror replay and one recovery-only primary call within the existing turn deadline.
 * Version: 1.2.2
 * Author: Living Archive
 */
if (!defined('ABSPATH')) { exit; }

if (!function_exists('la_hrn_provider_bridge_is_bounded_recovery_request')) {
    /**
     * Identify only the server-authored HRN recovery writer. Visitor text is
     * never inspected for this marker; it must appear in a system-role message.
     */
    function la_hrn_provider_bridge_is_bounded_recovery_request($args) {
        if (!is_array($args)) return false;
        $payload = json_decode((string)($args['body'] ?? ''), true);
        if (!is_array($payload)) return false;
        if (sanitize_key((string)($payload['operation'] ?? '')) !== 'hrn_relational') return false;
        $messages = $payload['messages'] ?? array();
        if (!is_array($messages)) return false;
        $markers = array(
            'You are the bounded recovery writer for a live human conversation after the primary composition attempt could not be used.',
            'STRICT VOICE RECOVERY — same ordinary relational operation.',
        );
        foreach ($messages as $message) {
            if (!is_array($message) || (string)($message['role'] ?? '') !== 'system') continue;
            $content = (string)($message['content'] ?? '');
            foreach ($markers as $marker) {
                if (strpos($content, $marker) !== false) return true;
            }
        }
        return false;
    }
}

add_filter('http_request_args', function ($args, $url) {
    $url = (string)$url;
    $primary = strpos($url, 'https://living-archive-backend.onrender.com/api/provider-capability') === 0;
    $mirror = strpos($url, 'https://living-archive-backend-mirror.onrender.com/api/provider-capability') === 0;
    if (!$primary && !$mirror) return $args;

    // The browser-facing HRN experience has a short patience budget. Establish
    // one shared 11.5-second provider-turn deadline on the first provider request,
    // while respecting any stricter deadline established by the protected writer.
    if (!array_key_exists('la_hrn_fast_deadline_started_at', $GLOBALS)) {
        $GLOBALS['la_hrn_fast_deadline_started_at'] = microtime(true);
        $fast_deadline = $GLOBALS['la_hrn_fast_deadline_started_at'] + 11.5;
        $existing = (float)($GLOBALS['lah_hrn_turn_deadline'] ?? 0);
        $GLOBALS['lah_hrn_turn_deadline'] = $existing > 0 ? min($existing, $fast_deadline) : $fast_deadline;
    }

    if ($primary) {
        if (!array_key_exists('lah_hrn_mirror_replay_used', $GLOBALS)) {
            $GLOBALS['lah_hrn_mirror_replay_used'] = false;
        }
        if (!array_key_exists('lah_hrn_recovery_attempt_used', $GLOBALS)) {
            $GLOBALS['lah_hrn_recovery_attempt_used'] = false;
        }
        $GLOBALS['la_provider_bridge_primary_started_at'] = microtime(true);
        unset($GLOBALS['la_provider_bridge_primary_response'], $GLOBALS['la_provider_bridge_primary_result'], $GLOBALS['la_provider_bridge_primary_elapsed']);
        $payload = json_decode((string)($args['body'] ?? ''), true);
        $GLOBALS['la_provider_bridge_primary_operation'] = is_array($payload) ? sanitize_key((string)($payload['operation'] ?? '')) : '';
    }

    $operation = (string)($GLOBALS['la_provider_bridge_primary_operation'] ?? '');
    $base_timeout = $primary ? 4.0 : 2.8;
    if ($primary && $operation === 'hrn_perception') $base_timeout = 2.0;
    // Reserve the remaining turn budget for the existing recovery writer.
    // The relational mirror request is bounded to two seconds; recovery is also
    // bounded to two seconds, with the shared deadline retaining its 350ms buffer.
    if ($mirror
        && $operation === 'hrn_relational'
        && empty($GLOBALS['lah_hrn_mirror_replay_used'])) {
        $base_timeout = 2.0;
    }
    if ($primary && la_hrn_provider_bridge_is_bounded_recovery_request($args)) {
        $base_timeout = 2.0;
    }

    $deadline = (float)($GLOBALS['lah_hrn_turn_deadline'] ?? 0);
    if ($deadline > 0) {
        $remaining = $deadline - microtime(true);
        $base_timeout = min($base_timeout, max(0.8, $remaining - 0.35));
    }
    $args['timeout'] = min((float)($args['timeout'] ?? $base_timeout), $base_timeout);
    return $args;
}, 99, 2);

add_filter('http_response', function ($response, $args, $url) {
    if (strpos((string)$url, 'https://living-archive-backend.onrender.com/api/provider-capability') !== 0) return $response;
    $GLOBALS['la_provider_bridge_primary_response'] = $response;
    return $response;
}, 10, 3);

add_action('http_api_debug', function ($response, $context, $class, $parsed_args, $url) {
    if ($context !== 'response' || strpos((string)$url, 'https://living-archive-backend.onrender.com/api/provider-capability') !== 0) return;
    $GLOBALS['la_provider_bridge_primary_result'] = $response;
    $started = (float)($GLOBALS['la_provider_bridge_primary_started_at'] ?? 0);
    if ($started > 0) $GLOBALS['la_provider_bridge_primary_elapsed'] = max(0.0, microtime(true) - $started);
}, 10, 5);

add_filter('pre_http_request', function ($preempt, $args, $url) {
    if ($preempt !== false) return $preempt;
    $url = (string)$url;
    $primary_endpoint = strpos($url, 'https://living-archive-backend.onrender.com/api/provider-capability') === 0;
    $mirror_endpoint = strpos($url, 'https://living-archive-backend-mirror.onrender.com/api/provider-capability') === 0;
    if (!$primary_endpoint && !$mirror_endpoint) return $preempt;

    $deadline = (float)($GLOBALS['lah_hrn_turn_deadline'] ?? 0);
    if ($deadline > 0 && microtime(true) >= ($deadline - 0.35)) {
        error_log('[LA Provider Bridge Deadline Guard] Provider-bank call suppressed; strict HRN visitor-turn deadline exhausted.');
        return new WP_Error('la_provider_bridge_turn_deadline_exhausted', 'The HRN provider-call budget has expired.', array(
            'stage' => 'provider_bank_transport', 'retryable' => true, 'reason' => 'whole_turn_deadline_exhausted'
        ));
    }

    if ($primary_endpoint) {
        $recovery_request = la_hrn_provider_bridge_is_bounded_recovery_request($args);
        if (!empty($GLOBALS['lah_hrn_recovery_attempt_used'])) {
            error_log('[LA Provider Bridge Deadline Guard] Further primary call suppressed; bounded recovery attempt already consumed.');
            return new WP_Error('la_provider_bridge_turn_attempt_budget_exhausted', 'The HRN turn has already consumed its single bounded recovery attempt.', array(
                'stage'=>'provider_bank_transport','retryable'=>true,'reason'=>'whole_turn_recovery_attempt_used'
            ));
        }
        if ($recovery_request) {
            $remaining = $deadline > 0 ? $deadline - microtime(true) : 0.0;
            // This is the one recovery writer already present in HRN. It may run
            // after a mirror replay or directly on primary when the mirror would
            // leave too little time. Never exceed the existing turn deadline.
            if ($deadline > 0 && $remaining >= 2.35) {
                $GLOBALS['lah_hrn_recovery_attempt_used'] = true;
                $after_mirror = !empty($GLOBALS['lah_hrn_mirror_replay_used']);
                error_log('[LA Provider Bridge Deadline Guard] Allowing one bounded recovery-only primary call; after_mirror=' . ($after_mirror ? 'true' : 'false') . ' remaining=' . round($remaining, 2) . 's timeout_cap=2.0s.');
                return $preempt;
            }
            error_log('[LA Provider Bridge Deadline Guard] Recovery-only primary call suppressed; insufficient turn budget remaining=' . round($remaining, 2) . 's.');
            return new WP_Error('la_provider_bridge_recovery_budget_exhausted', 'Insufficient HRN turn budget remains for the bounded recovery writer.', array(
                'stage'=>'provider_bank_transport','retryable'=>true,'reason'=>'recovery_budget_exhausted','remaining_seconds'=>round($remaining, 2)
            ));
        }
        if (!empty($GLOBALS['lah_hrn_mirror_replay_used'])) {
            error_log('[LA Provider Bridge Deadline Guard] Further primary call suppressed; whole-turn mirror replay already consumed.');
            return new WP_Error('la_provider_bridge_turn_attempt_budget_exhausted', 'The HRN turn has consumed its primary attempt and single mirror replay.', array(
                'stage'=>'provider_bank_transport','retryable'=>true,'reason'=>'whole_turn_attempt_budget_exhausted'
            ));
        }
        return $preempt;
    }

    if (!$mirror_endpoint) return $preempt;

    if (!empty($GLOBALS['lah_hrn_mirror_replay_used'])) {
        error_log('[LA Provider Bridge Deadline Guard] Mirror replay suppressed; whole-turn retry already consumed.');
        $prior = $GLOBALS['la_provider_bridge_primary_result'] ?? ($GLOBALS['la_provider_bridge_primary_response'] ?? null);
        if ($prior instanceof WP_Error || is_array($prior)) return $prior;
        return new WP_Error('la_provider_bridge_mirror_retry_already_used', 'The HRN turn has already consumed its single mirror replay.', array(
            'stage'=>'provider_bank_transport','retryable'=>true,'reason'=>'whole_turn_mirror_retry_used'
        ));
    }
    if (!empty($GLOBALS['lah_hrn_recovery_attempt_used'])) {
        error_log('[LA Provider Bridge Deadline Guard] Mirror replay suppressed; recovery attempt already consumed.');
        $prior = $GLOBALS['la_provider_bridge_primary_result'] ?? ($GLOBALS['la_provider_bridge_primary_response'] ?? null);
        if ($prior instanceof WP_Error || is_array($prior)) return $prior;
        return new WP_Error('la_provider_bridge_mirror_retry_after_recovery_suppressed', 'The HRN recovery attempt has already been consumed.', array(
            'stage'=>'provider_bank_transport','retryable'=>true,'reason'=>'recovery_attempt_already_used'
        ));
    }

    $primary = $GLOBALS['la_provider_bridge_primary_result'] ?? ($GLOBALS['la_provider_bridge_primary_response'] ?? null);
    $elapsed = (float)($GLOBALS['la_provider_bridge_primary_elapsed'] ?? 0);
    if ($elapsed <= 0) {
        $started = (float)($GLOBALS['la_provider_bridge_primary_started_at'] ?? 0);
        if ($started > 0) $elapsed = max(0.0, microtime(true) - $started);
    }
    $status = is_array($primary) ? (int)($primary['response']['code'] ?? 0) : 0;
    $operation = (string)($GLOBALS['la_provider_bridge_primary_operation'] ?? '');

    if ($operation === 'hrn_perception') {
        error_log('[LA Provider Bridge Deadline Guard] Perception replay suppressed; preserving turn budget for relational composition.');
        if ($primary instanceof WP_Error || is_array($primary)) return $primary;
        return new WP_Error('la_provider_bridge_perception_replay_suppressed', 'Perception failed; preserving the remaining budget for relational composition.', array(
            'stage'=>'provider_bank_transport','retryable'=>true,'reason'=>'perception_budget_reserved'
        ));
    }

    if ($operation !== 'hrn_relational') {
        error_log('[LA Provider Bridge Deadline Guard] Mirror replay suppressed for non-writer operation=' . ($operation ?: 'unknown') . '.');
        if ($primary instanceof WP_Error || is_array($primary)) return $primary;
        return new WP_Error('la_provider_bridge_non_writer_replay_suppressed', 'A supporting HRN operation failed; preserving the mirror replay for relational composition.', array(
            'stage'=>'provider_bank_transport','retryable'=>true,'reason'=>'writer_retry_reserved','operation'=>$operation
        ));
    }

    // A relational mirror replay is worthwhile only if the same turn can still
    // accommodate the existing recovery writer. Otherwise return the primary
    // failure and let HRN spend the remaining bounded budget on recovery directly.
    $remaining_for_mirror = $deadline > 0 ? $deadline - microtime(true) : 0.0;
    if ($deadline <= 0 || $remaining_for_mirror < 4.4) {
        error_log('[LA Provider Bridge Deadline Guard] Mirror replay suppressed to reserve bounded recovery time; remaining=' . round($remaining_for_mirror, 2) . 's required=4.4s.');
        return $primary instanceof WP_Error ? $primary : (is_array($primary) ? $primary : new WP_Error(
            'la_provider_bridge_mirror_budget_reserved', 'The mirror replay was skipped to preserve time for the bounded HRN recovery writer.',
            array('stage'=>'provider_bank_transport','retryable'=>true,'reason'=>'mirror_budget_reserved_for_recovery','remaining_seconds'=>round($remaining_for_mirror, 2))
        ));
    }

    // Retry only after a completed slow/failed writer attempt and only when the
    // remaining whole-turn budget can accommodate the bounded mirror request.
    if ($elapsed >= 2.5 && (is_wp_error($primary) || $status >= 500 || $status === 0)) {
        $remaining = $deadline > 0 ? $deadline - microtime(true) : 0.0;
        $ambiguous = is_wp_error($primary) || $status === 0;
        $budget_exhausted = $deadline > 0 && $remaining < 4.4;
        if ($budget_exhausted) {
            error_log('[LA Provider Bridge Deadline Guard] Mirror replay suppressed; insufficient turn budget remaining=' . round($remaining, 2) . 's.');
            return $primary instanceof WP_Error ? $primary : (is_array($primary) ? $primary : new WP_Error(
                'la_provider_bridge_primary_slow_failure', 'The primary provider-bank operation failed after consuming its bounded window.',
                array('stage'=>'provider_bank_transport','retryable'=>true,'reason'=>'slow_primary_failure')
            ));
        }
        error_log('[LA Provider Bridge Deadline Guard] Allowing the single bounded relational mirror replay; elapsed=' . round($elapsed, 2) . 's remaining=' . round($remaining, 2) . 's ambiguous=' . ($ambiguous ? 'true' : 'false') . '.');
    }

    $GLOBALS['lah_hrn_mirror_replay_used'] = true;
    error_log('[LA Provider Bridge Deadline Guard] Consuming the single whole-turn mirror replay for operation=' . ($operation ?: 'unknown') . '.');
    return $preempt;
}, 10, 3);
