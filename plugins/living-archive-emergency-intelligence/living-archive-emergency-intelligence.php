<?php
/**
 * Plugin Name: Living Archive Emergency Intelligence
 * Description: Verified, independently updateable emergency-resource intelligence for Living Archive instruments.
 * Version: 0.1.3
 * Author: Living Archive
 * Requires at least: 6.2
 * Requires PHP: 7.4
 * License: GPL-2.0-or-later
 */

if (!defined('ABSPATH')) exit;

define('LAEI_VERSION', '0.1.3');
define('LAEI_FILE', __FILE__);
define('LAEI_DIR', plugin_dir_path(__FILE__));
define('LAEI_URL', plugin_dir_url(__FILE__));
define('LAEI_REGISTRY_FILE', LAEI_DIR . 'data/emergency-registry.json');
define('LAEI_TEST_FILE', LAEI_DIR . 'tests/emergency-tests.json');

auto_load_laei();

function auto_load_laei() {
    $files = [
        'class-lai-ei-registry.php',
        'class-lai-ei-update-manager.php',
        'class-lai-ei-location-resolver.php',
        'class-lai-ei-resource-selector.php',
        'class-lai-ei-presenter.php',
        'class-lai-ei-engine.php',
        'class-lai-ei-api.php',
        'class-lai-ei-admin.php',
    ];
    foreach ($files as $file) {
        require_once LAEI_DIR . 'includes/' . $file;
    }
}

register_activation_hook(__FILE__, ['LAEI_Update_Manager', 'activate']);
register_deactivation_hook(__FILE__, ['LAEI_Update_Manager', 'deactivate']);

add_action('plugins_loaded', function () {
    LAEI_Registry::init();
    LAEI_Update_Manager::init();
    LAEI_API::init();
    LAEI_Admin::init();
});

/**
 * Public service interface for Living Archive tools.
 * HRN and other instruments should call this interface rather than internal classes.
 */
function living_archive_emergency_resolve($service_need, $location = [], $safety_state = 'unknown', $presentation_policy = null) {
    return LAEI_Engine::resolve($service_need, $location, $safety_state, $presentation_policy);
}
