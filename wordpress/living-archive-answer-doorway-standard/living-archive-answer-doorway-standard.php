<?php
/**
 * Plugin Name: Living Archive — Answer + Doorway Standard
 * Description: Shared, hardened visitor-facing doorway presentation for Living Archive modules.
 * Version: 1.0.0
 * Author: Living Archive
 */
if (!defined('ABSPATH')) { exit; }

define('LA_ANSWER_DOORWAY_VERSION', '1.0.0');
define('LA_ANSWER_DOORWAY_URL', plugin_dir_url(__FILE__));

add_action('wp_enqueue_scripts', function () {
    if (is_admin()) return;
    // Small, dependency-free shared renderer. Load before module scripts so
    // every adapter consumes the same URL and DOM safety boundary.
    wp_enqueue_style(
        'la-answer-doorway-standard',
        LA_ANSWER_DOORWAY_URL . 'assets/answer-doorway.css',
        array(),
        LA_ANSWER_DOORWAY_VERSION
    );
    wp_enqueue_script(
        'la-answer-doorway-standard',
        LA_ANSWER_DOORWAY_URL . 'assets/answer-doorway.js',
        array(),
        LA_ANSWER_DOORWAY_VERSION,
        false
    );
}, 1);
