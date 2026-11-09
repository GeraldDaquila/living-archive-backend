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
         * This plugin does not yet implement cryptographic signature
         * verification against a provisioned trusted public key. A content
         * hash detects accidental corruption; it does not authenticate the
         * publisher. Therefore remote registry updates are disabled.
         *
         * The locally installed registry remains available. This gate does
         * not block HRN's safety state machine or its existing fallback.
         */
        return self::record_result([
            'status' => 'disabled_security_gate',
            'message' => 'Remote registry updates are disabled until mandatory cryptographic signature verification is implemented, provisioned, and tested.',
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
