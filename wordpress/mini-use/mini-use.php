<?php
/**
 * Plugin Name: Mini-USE — Stewardship Catalogue Navigator
 * Description: WordPress adapter for the Render-hosted Mini-USE Stewardship Catalogue navigator.
 * Version: 0.2.41
 * Author: Gerald A. Daquila
 */
if (!defined('ABSPATH')) exit;
define('MINI_USE_VERSION','0.2.41');
define('MINI_USE_BACKEND_URL','https://mini-use-payhip.onrender.com');
define('MINI_USE_DIR',plugin_dir_path(__FILE__));
define('MINI_USE_URL',plugin_dir_url(__FILE__));
require_once MINI_USE_DIR.'includes/class-catalogue.php';
require_once MINI_USE_DIR.'includes/class-retrieval.php';
require_once MINI_USE_DIR.'includes/class-groq.php';
require_once MINI_USE_DIR.'includes/class-api.php';
require_once MINI_USE_DIR.'includes/class-settings.php';
require_once MINI_USE_DIR.'includes/class-validator.php';
Mini_Use_Settings::init();
Mini_Use_API::init();
add_shortcode('mini_use',function($atts=[]){return Mini_Use_API::shortcode($atts);});
register_activation_hook(__FILE__,['Mini_Use_Validator','activation_check']);
