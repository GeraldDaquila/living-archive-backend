<?php
if (!defined('ABSPATH')) exit;

class LAEI_Update_Manager {
    const OPTION_LAST_CHECK = 'laei_last_registry_check';
    const OPTION_LAST_RESULT = 'laei_last_registry_result';
    const OPTION_LAST_SUCCESS = 'laei_last_registry_success';
    const OPTION_ACTIVE_VERSION = 'laei_active_registry_version';
    const OPTION_ENDPOINT = 'laei_registry_endpoint';
    const CRON_HOOK = 'laei_registry_scheduled_check';
    const CHECK_INTERVAL = 21600;

    public static function init() {
        add_filter('cron_schedules', [__CLASS__, 'cron_schedule']);
        add_action(self::CRON_HOOK, [__CLASS__, 'scheduled_check']);
    }

    public static function cron_schedule($schedules) {
        $schedules['laei_six_hours'] = [
            'interval' => self::CHECK_INTERVAL,
            'display' => __('Every 6 hours', 'living-archive-emergency-intelligence')
        ];
        return $schedules;
    }

    public static function activate() {
        if (!get_option(self::OPTION_ENDPOINT)) update_option(self::OPTION_ENDPOINT, '');
        update_option(self::OPTION_ACTIVE_VERSION, LAEI_Registry::version());
        if (!wp_next_scheduled(self::CRON_HOOK)) {
            wp_schedule_event(time() + 300, 'laei_six_hours', self::CRON_HOOK);
        }
    }

    public static function deactivate() {
        wp_clear_scheduled_hook(self::CRON_HOOK);
    }

    public static function scheduled_check() { self::maybe_check(true); }

    public static function maybe_check($force = false) {
        $last = (int)get_option(self::OPTION_LAST_CHECK, 0);
        if (!$force && $last && (time() - $last) < self::CHECK_INTERVAL) {
            return ['attempted' => false, 'reason' => 'freshness_window'];
        }
        return self::check_now();
    }

    public static function check_now() {
        update_option(self::OPTION_LAST_CHECK, time());

        /*
         * SECURITY GATE (fail closed):
         * The current plugin has no trusted public key and no implemented
         * cryptographic signature verifier. A content hash detects accidental
         * corruption; it does not authenticate the publisher. Do not fetch or
         * activate remote registry candidates until signature verification is
         * implemented, provisioned, and covered by tests.
         *
         * This deliberately leaves the locally installed registry available.
         * It does not block HRN's safety intervention or resource fallback.
         */
        return self::record_result([
            'status' => 'disabled_security_gate',
            'message' => 'Remote registry updates are disabled until mandatory cryptographic signature verification is implemented and a trusted public key is provisioned.',
        ]);

        $endpoint = trim((string)get_option(self::OPTION_ENDPOINT, ''));
        if (!$endpoint || !wp_http_validate_url($endpoint)) {
            $result = ['status' => 'not_configured', 'message' => 'Canonical registry endpoint is not configured.'];
            update_option(self::OPTION_LAST_RESULT, $result);
            return $result;
        }

        $response = wp_remote_get($endpoint, [
            'timeout' => 5,
            'redirection' => 2,
            'headers' => ['Accept' => 'application/json'],
        ]);
        if (is_wp_error($response)) {
            return self::record_result(['status' => 'failed', 'message' => $response->get_error_message()]);
        }

        $code = (int)wp_remote_retrieve_response_code($response);
        if ($code !== 200) {
            return self::record_result(['status' => 'failed', 'message' => 'Registry endpoint returned HTTP ' . $code . '.']);
        }

        $body = wp_remote_retrieve_body($response);
        $candidate = json_decode($body, true);
        $validation = LAEI_Registry::validate_candidate($candidate);
        if (!$validation['valid']) {
            return self::record_result(['status' => 'rejected', 'message' => $validation['error']]);
        }

        $current = LAEI_Registry::version();
        if (self::version_compare_registry($candidate['registry_version'], $current) <= 0) {
            return self::record_result([
                'status' => 'current',
                'message' => 'No newer registry available.',
                'version' => $current
            ]);
        }

        $canonical_hash = self::canonical_hash($candidate);
        if (!empty($candidate['content_hash']) && !hash_equals((string)$candidate['content_hash'], $canonical_hash)) {
            return self::record_result(['status' => 'rejected', 'message' => 'Registry content hash mismatch.']);
        }

        // Signature enforcement is intentionally dormant until the canonical
        // registry public key is provisioned. We do not claim cryptographic
        // authenticity until a trusted key exists in the plugin configuration.
        if (!empty($candidate['signature_required'])) {
            return self::record_result([
                'status' => 'rejected',
                'message' => 'Signed registry received but no trusted verification key is provisioned.'
            ]);
        }

        $tmp = LAEI_REGISTRY_FILE . '.tmp';
        $payload = wp_json_encode($candidate, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);
        if (file_put_contents($tmp, $payload, LOCK_EX) === false) {
            return self::record_result(['status' => 'failed', 'message' => 'Unable to write temporary registry.']);
        }

        $old = LAEI_REGISTRY_FILE . '.previous';
        if (file_exists(LAEI_REGISTRY_FILE)) @copy(LAEI_REGISTRY_FILE, $old);
        if (!@rename($tmp, LAEI_REGISTRY_FILE)) {
            @unlink($tmp);
            return self::record_result(['status' => 'failed', 'message' => 'Unable to activate new registry.']);
        }

        if (!LAEI_Registry::load(true)) {
            if (file_exists($old)) @copy($old, LAEI_REGISTRY_FILE);
            return self::record_result(['status' => 'failed', 'message' => 'Activated registry could not be loaded; previous registry restored.']);
        }

        update_option(self::OPTION_ACTIVE_VERSION, LAEI_Registry::version());
        update_option(self::OPTION_LAST_SUCCESS, time());
        return self::record_result([
            'status' => 'updated',
            'message' => 'Registry updated successfully.',
            'version' => LAEI_Registry::version(),
            'sha256' => $canonical_hash
        ]);
    }

    private static function record_result($result) {
        update_option(self::OPTION_LAST_RESULT, $result);
        return $result;
    }

    private static function canonical_hash($data) {
        $copy = $data;
        unset($copy['content_hash'], $copy['signature']);
        return hash('sha256', wp_json_encode($copy, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE));
    }

    private static function version_compare_registry($a, $b) {
        if (!$b) return 1;
        return version_compare(str_replace('.', '', (string)$a), str_replace('.', '', (string)$b));
    }
}
