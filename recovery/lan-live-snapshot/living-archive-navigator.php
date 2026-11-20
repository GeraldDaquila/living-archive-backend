<?php
/**
 * Plugin Name: Living Archive Navigator
 * Description: Public Living Archive inquiry, retrieval, and three-door canonical navigation engine.
 * Version: 0.3.3
 * Author: Gerald Alba Daquila / Living Archive
 * License: GPL-2.0-or-later
 */
if (!defined('ABSPATH')) { exit; }

define('LAN_VERSION', '0.3.3');
define('LAN_DIR', plugin_dir_path(__FILE__));
define('LAN_URL', plugin_dir_url(__FILE__));

require_once LAN_DIR . 'includes/class-lan-engine.php';

final class Living_Archive_Navigator_Plugin {
    private static ?self $instance = null;
    private ?LAN_Engine $engine = null;

    public static function instance(): self {
        if (self::$instance === null) self::$instance = new self();
        return self::$instance;
    }

    private function __construct() {
        add_action('wp_enqueue_scripts', [$this, 'assets']);
        add_shortcode('living_archive_navigator', [$this, 'shortcode']);
        add_action('rest_api_init', [$this, 'routes']);
        add_action('admin_menu', [$this, 'admin_menu']);
        add_action('admin_init', [$this, 'settings']);
        add_action('admin_notices', [$this, 'admin_notice']);
    }

    private function engine(): LAN_Engine {
        if ($this->engine === null) $this->engine = new LAN_Engine(LAN_DIR . 'data');
        return $this->engine;
    }

    public function assets(): void {
        if (!is_singular()) return;
        global $post;
        if (!$post || !has_shortcode((string)$post->post_content, 'living_archive_navigator')) return;
        wp_enqueue_style('living-archive-navigator-style', LAN_URL . 'assets/02-CSS.css', [], LAN_VERSION);
        wp_enqueue_script('living-archive-navigator-script', LAN_URL . 'assets/03-JavaScript.js', [], LAN_VERSION, true);
        wp_localize_script('living-archive-navigator-script', 'LIVING_ARCHIVE_NAVIGATOR_CONFIG', [
            'endpoint' => esc_url_raw(rest_url('living-archive/v1/navigate')),
            'timeoutMs' => 50000,
        ]);
    }

    public function shortcode(): string {
        $file = LAN_DIR . 'assets/01-HTML.html';
        if (!is_readable($file)) return '<p>The Living Archive Navigator is temporarily unavailable.</p>';
        $html = file_get_contents($file);
        if ($html === false) return '<p>The Living Archive Navigator is temporarily unavailable.</p>';
        return $html;
    }

    public function routes(): void {
        register_rest_route('living-archive/v1', '/navigate', [
            'methods' => WP_REST_Server::CREATABLE,
            'callback' => [$this, 'navigate'],
            'permission_callback' => '__return_true',
        ]);
    }

    public function navigate(WP_REST_Request $request): WP_REST_Response {
        if (!$this->rate_ok()) return new WP_REST_Response(['message' => 'Please wait a moment before trying again.'], 429);
        $params = $request->get_json_params();
        if (!is_array($params)) return new WP_REST_Response(['message' => 'Invalid request.'], 400);
        $choice = $this->limit((string)($params['choice'] ?? ''), 120);
        $situation = $this->limit((string)($params['situation'] ?? ''), 3000);
        $possibility = $this->limit((string)($params['possibility'] ?? ''), 2000);
        $clarification = $this->limit((string)($params['clarification'] ?? ''), 2000);
        if ($situation === '' && $possibility === '') return new WP_REST_Response(['message' => 'Please describe the question you are carrying.'], 400);
        $key = trim((string)get_option('lan_groq_api_key', ''));
        if ($key === '') return new WP_REST_Response(['message' => 'The navigator service is not configured.'], 503);
        try {
            $result = $this->engine()->navigate(['choice' => $choice, 'situation' => $situation, 'possibility' => $possibility, 'clarification' => $clarification], $key);
            return new WP_REST_Response($result, 200);
        } catch (InvalidArgumentException $e) {
            return new WP_REST_Response(['message' => 'Please tell us a little more about the question.'], 400);
        } catch (Throwable $e) {
            if (defined('WP_DEBUG') && WP_DEBUG) error_log('Living Archive Navigator: ' . $e->getMessage());
            return new WP_REST_Response(['message' => 'The path could not be opened right now. Please try again shortly.'], 502);
        }
    }

    private function rate_ok(): bool {
        $ip = isset($_SERVER['REMOTE_ADDR']) ? (string)$_SERVER['REMOTE_ADDR'] : 'unknown';
        $key = 'lan_rl_' . hash_hmac('sha256', $ip, wp_salt('auth'));
        $count = (int)get_transient($key);
        if ($count >= 12) return false;
        set_transient($key, $count + 1, 10 * MINUTE_IN_SECONDS);
        return true;
    }

    private function limit(string $value, int $max): string {
        $value = trim((string)preg_replace('/\s+/u', ' ', wp_strip_all_tags($value)));
        return function_exists('mb_substr') ? mb_substr($value, 0, $max) : substr($value, 0, $max);
    }

    public function admin_menu(): void {
        add_options_page('Living Archive Navigator', 'Living Archive Navigator', 'manage_options', 'living-archive-navigator', [$this, 'settings_page']);
    }

    public function settings(): void {
        register_setting('lan_settings', 'lan_groq_api_key', [
            'type' => 'string',
            'sanitize_callback' => function($value) {
                $value = trim((string)$value);
                if ($value === '') return (string)get_option('lan_groq_api_key', '');
                return $value;
            },
            'default' => '',
        ]);
        add_settings_section('lan_main', 'Navigator Engine', '__return_false', 'living-archive-navigator');
        add_settings_field('lan_groq_api_key', 'Groq API key', [$this, 'key_field'], 'living-archive-navigator', 'lan_main');
    }

    public function key_field(): void {
        echo '<input type="password" name="lan_groq_api_key" value="" class="regular-text" autocomplete="new-password" placeholder="Leave blank to keep the existing key">';
        echo '<p class="description">The key is stored server-side and is never sent to the visitor browser.</p>';
    }

    public function settings_page(): void {
        if (!current_user_can('manage_options')) return;
        $status = $this->engine()->corpus_status();
        echo '<div class="wrap"><h1>Living Archive Navigator</h1>';
        echo '<p>This is the public Living Archive navigation engine. It uses the audited public T1–T3 corpus only.</p>';
        echo '<h2>Corpus</h2><p>Version ' . esc_html($status['version']) . ' · ' . esc_html((string)$status['resources']) . ' public resources · ' . esc_html((string)$status['relationships']) . ' relationship edges available</p>';
        echo '<p>Relationship status: ' . esc_html($status['relationships_status']) . '</p>';
        echo '<form method="post" action="options.php">';
        settings_fields('lan_settings');
        do_settings_sections('living-archive-navigator');
        submit_button('Save Groq API key');
        echo '</form></div>';
    }

    public function admin_notice(): void {
        if (!current_user_can('manage_options')) return;
        if (trim((string)get_option('lan_groq_api_key', '')) !== '') return;
        $screen = function_exists('get_current_screen') ? get_current_screen() : null;
        if (!$screen || strpos((string)$screen->id, 'living-archive-navigator') === false) return;
        echo '<div class="notice notice-warning"><p><strong>Living Archive Navigator:</strong> add the Groq API key under Settings → Living Archive Navigator before using the navigator.</p></div>';
    }
}

Living_Archive_Navigator_Plugin::instance();
