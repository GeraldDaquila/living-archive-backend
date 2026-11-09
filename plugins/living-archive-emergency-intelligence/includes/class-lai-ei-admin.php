<?php
if (!defined('ABSPATH')) exit;

class LAEI_Admin {
    public static function init() {
        add_action('admin_menu', [__CLASS__, 'menu']);
        add_action('admin_init', [__CLASS__, 'settings']);
        add_action('admin_post_laei_check_now', [__CLASS__, 'check_now']);
        add_action('admin_post_laei_run_tests', [__CLASS__, 'run_tests']);
    }

    public static function menu() {
        add_management_page('Emergency Intelligence', 'Emergency Intelligence', 'manage_options', 'laei', [__CLASS__, 'page']);
    }

    public static function settings() {
        register_setting('laei_settings', LAEI_Update_Manager::OPTION_ENDPOINT, [
            'sanitize_callback' => function($value) { return esc_url_raw(trim((string)$value)); }
        ]);
    }

    public static function page() {
        if (!current_user_can('manage_options')) return;
        $result = get_option(LAEI_Update_Manager::OPTION_LAST_RESULT, null);
        $last = (int)get_option(LAEI_Update_Manager::OPTION_LAST_CHECK, 0);
        $success = (int)get_option(LAEI_Update_Manager::OPTION_LAST_SUCCESS, 0);
        $endpoint = esc_attr((string)get_option(LAEI_Update_Manager::OPTION_ENDPOINT, ''));
        $tests = get_transient('laei_test_results');
        ?>
        <div class="wrap">
            <h1>Living Archive Emergency Intelligence</h1>
            <table class="widefat striped" style="max-width:900px">
                <tbody>
                    <tr><th>Plugin Version</th><td><?php echo esc_html(LAEI_VERSION); ?></td></tr>
                    <tr><th>Registry Version</th><td><?php echo esc_html(LAEI_Registry::version()); ?></td></tr>
                    <tr><th>Last Checked</th><td><?php echo $last ? esc_html(wp_date('Y-m-d H:i:s', $last)) : 'Never'; ?></td></tr>
                    <tr><th>Last Successful Update</th><td><?php echo $success ? esc_html(wp_date('Y-m-d H:i:s', $success)) : 'Never'; ?></td></tr>
                    <tr><th>Last Result</th><td><pre><?php echo esc_html(wp_json_encode($result, JSON_PRETTY_PRINT)); ?></pre></td></tr>
                </tbody>
            </table>

            <h2>Canonical Registry Endpoint</h2>
            <form method="post" action="options.php">
                <?php settings_fields('laei_settings'); ?>
                <input type="url" name="<?php echo esc_attr(LAEI_Update_Manager::OPTION_ENDPOINT); ?>" value="<?php echo $endpoint; ?>" class="regular-text" placeholder="https://.../emergency-registry.json" />
                <?php submit_button('Save Endpoint', 'secondary'); ?>
            </form>

            <p>
                <a class="button button-primary" href="<?php echo esc_url(wp_nonce_url(admin_url('admin-post.php?action=laei_check_now'), 'laei_check_now')); ?>">Check for Update Now</a>
                <a class="button" href="<?php echo esc_url(wp_nonce_url(admin_url('admin-post.php?action=laei_run_tests'), 'laei_run_tests')); ?>">Run Diagnostics</a>
            </p>

            <?php if (is_array($tests)): ?>
                <h2>Last Diagnostic Run</h2>
                <table class="widefat striped" style="max-width:900px">
                    <thead><tr><th>Test</th><th>Result</th><th>Actual</th></tr></thead>
                    <tbody>
                    <?php foreach ($tests as $test): ?>
                        <tr>
                            <td><?php echo esc_html($test['id']); ?></td>
                            <td><?php echo !empty($test['pass']) ? 'PASS' : 'FAIL'; ?></td>
                            <td><code><?php echo esc_html($test['actual']); ?></code></td>
                        </tr>
                    <?php endforeach; ?>
                    </tbody>
                </table>
            <?php endif; ?>
        </div>
        <?php
    }

    public static function check_now() {
        if (!current_user_can('manage_options')) wp_die('Unauthorized.');
        check_admin_referer('laei_check_now');
        LAEI_Update_Manager::check_now();
        wp_safe_redirect(admin_url('tools.php?page=laei'));
        exit;
    }

    public static function run_tests() {
        if (!current_user_can('manage_options')) wp_die('Unauthorized.');
        check_admin_referer('laei_run_tests');
        $tests = file_exists(LAEI_TEST_FILE) ? json_decode(file_get_contents(LAEI_TEST_FILE), true) : [];
        $results = [];
        foreach (($tests['tests'] ?? []) as $test) {
            $location = [];
            if (!empty($test['country'])) $location['explicit_country'] = $test['country'];
            if (!empty($test['refused'])) $location['refused'] = true;
            $out = LAEI_Engine::resolve($test['service_need'], $location, 'diagnostic');
            $numbers = [];
            $primary = $out['selection']['primary'] ?? null;
            if (is_array($primary) && isset($primary[0])) {
                foreach ($primary as $r) $numbers[] = $r['number'] ?? '';
            } elseif (is_array($primary)) {
                $numbers[] = $primary['number'] ?? '';
            }
            $pass = true;
            if (!empty($test['expected'])) $pass = $numbers === $test['expected'];
            if (!empty($test['expected_equivalence_group'])) $pass = (($out['selection']['equivalence_group'] ?? '') === $test['expected_equivalence_group']);
            if (!empty($test['expected_status'])) $pass = (($out['selection']['selection_status'] ?? '') === $test['expected_status']);
            $results[] = ['id' => $test['id'], 'pass' => $pass, 'actual' => $out['selection']['selection_status'] . ' ' . wp_json_encode($numbers)];
        }
        set_transient('laei_test_results', $results, 300);
        wp_safe_redirect(admin_url('tools.php?page=laei'));
        exit;
    }
}
