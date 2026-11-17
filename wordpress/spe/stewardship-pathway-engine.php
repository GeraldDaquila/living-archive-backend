<?php
/**
 * Plugin Name: Stewardship Pathway Engine
 * Description: Canonical Stewardship Pathway interpretation, retrieval, and coherence engine.
 * Version: 3.4.4
 * Author: Gerald Alba Daquila / Living Archive
 * License: GPL-2.0-or-later
 */
if (!defined('ABSPATH')) { exit; }

define('SPE_VERSION', '3.4.4');
define('SPE_DIR', plugin_dir_path(__FILE__));
define('SPE_URL', plugin_dir_url(__FILE__));

require_once SPE_DIR . 'includes/class-spe-engine.php';

final class Stewardship_Pathway_Plugin {
    private static ?self $instance = null;
    private ?SPE_Engine $engine = null;

    public static function instance(): self {
        if (self::$instance === null) self::$instance = new self();
        return self::$instance;
    }

    private function __construct() {
        add_action('wp_enqueue_scripts', [$this, 'assets']);
        add_shortcode('stewardship_pathway', [$this, 'shortcode']);
        add_action('rest_api_init', [$this, 'routes']);
        add_action('admin_menu', [$this, 'admin_menu']);
        add_action('admin_init', [$this, 'settings']);
        add_action('admin_notices', [$this, 'admin_notice']);
    }

    private function engine(): SPE_Engine {
        if ($this->engine === null) $this->engine = new SPE_Engine(SPE_DIR . 'data');
        return $this->engine;
    }

    public function assets(): void {
        if (!is_singular()) return;
        global $post;
        if (!$post || !has_shortcode((string)$post->post_content, 'stewardship_pathway')) return;
        wp_enqueue_style('spe-style', SPE_URL . 'assets/02-CSS.css', [], SPE_VERSION);
        wp_enqueue_script('spe-script', SPE_URL . 'assets/03-JavaScript.js', ['la-answer-doorway-standard'], SPE_VERSION, true);
        wp_localize_script('spe-script', 'STEWARDSHIP_PATHWAY_CONFIG', [
            'endpoint' => esc_url_raw(rest_url('stewardship/v1/pathway')),
            'timeoutMs' => 50000,
        ]);
    }

    public function shortcode(): string {
        $file = SPE_DIR . 'assets/01-HTML.html';
        if (!is_readable($file)) return '<p>Stewardship Pathway is temporarily unavailable.</p>';
        $html = file_get_contents($file);
        if ($html === false) return '<p>Stewardship Pathway is temporarily unavailable.</p>';
        return $html;
    }

    public function routes(): void {
        register_rest_route('stewardship/v1', '/pathway', [
            'methods' => WP_REST_Server::CREATABLE,
            'callback' => [$this, 'pathway'],
            'permission_callback' => '__return_true',
        ]);
    }

    public function pathway(WP_REST_Request $request): WP_REST_Response {
        if (!$this->rate_ok()) return new WP_REST_Response(['message' => 'Please wait a moment before trying again.'], 429);
        $params = $request->get_json_params();
        if (!is_array($params)) return new WP_REST_Response(['message' => 'Invalid request.'], 400);
        $choice = $this->limit((string)($params['choice'] ?? ''), 120);
        $situation = $this->limit((string)($params['situation'] ?? ''), 3000);
        $possibility = $this->limit((string)($params['possibility'] ?? ''), 2000);
        if ($situation === '' && $possibility === '') return new WP_REST_Response(['message' => 'Please describe what is happening.'], 400);
        $key = trim((string)get_option('spe_groq_api_key', ''));
        $input = [
            'choice' => $choice,
            'situation' => $situation,
            'possibility' => $possibility,
        ];
        try {
            // Native Formation bridge: keep the Stewardship Pathway Engine as
            // the WordPress boundary while delegating interpretation to the
            // bounded Formation specialist in the canonical backend.
            $bridge = $this->formation_bridge($input);
            if (is_array($bridge)) {
                try {
                    $formation_result = $this->formation_result($bridge);
                    if (is_array($formation_result)) {
                        return new WP_REST_Response($formation_result, 200);
                    }
                } catch (Throwable $formation_error) {
                    // A malformed specialist contribution must never become a
                    // WordPress boundary outage. Fall through to the bounded
                    // local engine instead of converting a specialist contract
                    // defect into a visitor-facing 5xx.
                    error_log('Stewardship Pathway Engine Formation boundary fallback: ' . $formation_error->getMessage());
                }
            }

            // Formation bridge is an enhancement, never a single point of
            // failure. If the canonical backend cannot be reached, preserve
            // the established local Stewardship Pathway Engine contract.
            if ($key === '') return new WP_REST_Response(['message' => 'The pathway service is not configured.'], 503);
            $result = $this->engine()->navigate($input, $key);
            return new WP_REST_Response($result, 200);
        } catch (InvalidArgumentException $e) {
            return new WP_REST_Response(['message' => 'Please tell us a little more about what is happening.'], 400);
        } catch (Throwable $e) {
            if (defined('WP_DEBUG') && WP_DEBUG) error_log('Stewardship Pathway Engine: ' . $e->getMessage());
            return new WP_REST_Response(['message' => 'The pathway could not be opened right now. Please try again shortly.'], 502);
        }
    }

    private function formation_bridge(array $input): ?array {
        $endpoint = trim((string)get_option('spe_formation_endpoint', 'https://living-archive-backend.onrender.com/api/formation-entrance'));
        if ($endpoint === '') return null;
        if (!preg_match('#^https://living-archive-backend\.onrender\.com/api/formation-entrance$#', $endpoint)) {
            return null;
        }

        $shared_secret = function_exists('la_provider_bank_shared_secret')
            ? trim((string)la_provider_bank_shared_secret())
            : '';
        if ($shared_secret === '') {
            error_log('Stewardship Pathway Engine: Provider Bank authentication helper unavailable; using local fallback.');
            return null;
        }

        $payload = [
            'choice' => (string)($input['choice'] ?? ''),
            'situation' => (string)($input['situation'] ?? ''),
            'possibility' => (string)($input['possibility'] ?? ''),
            'source' => 'steward-entrance',
            'contract_version' => 'v1',
        ];

        $response = wp_remote_post($endpoint, [
            'timeout' => 45,
            'headers' => [
                'Content-Type' => 'application/json',
                'X-Living-Archive-Provider-Key' => $shared_secret,
            ],
            'body' => wp_json_encode($payload, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES),
        ]);
        if (is_wp_error($response)) {
            return null;
        }
        $status = wp_remote_retrieve_response_code($response);
        $body = wp_remote_retrieve_body($response);
        if ($status < 200 || $status >= 300) {
            return null;
        }
        $decoded = json_decode($body, true);
        if (!is_array($decoded)) {
            return null;
        }
        $contribution = $decoded['formation_contribution'] ?? null;
        if (!is_array($contribution)) {
            return null;
        }

        // Preserve the backend's Guide request identity in the WordPress
        // boundary. This keeps the request traceable without changing the
        // visitor-facing response contract.
        $request_id = trim((string)($decoded['request_id'] ?? ''));
        if ($request_id !== '') {
            $contribution['_guide_request_id'] = $request_id;
        }

        // Normalize the specialist response at the WordPress boundary. The
        // bridge is considered usable only when it carries the contribution
        // identity, a successful contribution status, and at least one
        // canonical candidate. This prevents a transport-successful but
        // semantically incomplete specialist response from short-circuiting
        // the established local fallback path.
        if (trim((string)($contribution['_guide_request_id'] ?? '')) === '') {
            return null;
        }
        if (strtoupper(trim((string)($contribution['status'] ?? ''))) !== 'CONTRIBUTION') {
            return null;
        }
        if (!is_array($contribution['canonical_candidates'] ?? null)) {
            return null;
        }
        if (count($contribution['canonical_candidates']) < 1) {
            return null;
        }

        $contribution['_formation_response'] = trim((string)($decoded['response'] ?? ''));
        return $contribution;
    }

    
    private function formation_result(array $contribution): array {
        $guide_request_id = trim((string)($contribution['_guide_request_id'] ?? ''));

        $status = (string)($contribution['status'] ?? 'FAILED');
        if ($status !== 'CONTRIBUTION') {
            // Do not invent visitor-facing prose when the specialist has no
            // contribution. Preserve the existing UI contract while signaling
            // that WordPress should use its bounded failure/decline path.
            throw new RuntimeException('Formation specialist returned ' . $status . '.');
        }

        $doors = [];
        $seen_ids = [];
        foreach (($contribution['canonical_candidates'] ?? []) as $candidate) {
            if (!is_array($candidate)) continue;
            $id = trim((string)($candidate['id'] ?? ''));
            $url = esc_url_raw((string)($candidate['url'] ?? ''));
            $title = wp_strip_all_tags((string)($candidate['title'] ?? ''));
            if ($id === '' || isset($seen_ids[$id]) || $url === '' || $title === '') continue;
            $seen_ids[$id] = true;
            $doors[] = [
                'id' => $id,
                'title' => $title,
                'url' => $url,
                'resource_type' => (string)($candidate['resource_type'] ?? ''),
                'domain' => (string)($candidate['domain'] ?? ''),
                'content_access_status' => (string)($candidate['content_access_status'] ?? ''),
            ];
            if (count($doors) >= 3) break;
        }

        // The visitor contract is three coherent doors. A specialist must not
        // be able to collapse the entrance into a partial result. If an older
        // Formation response returns fewer than three valid candidates, fill
        // the remaining positions from the same canonical Formation set.
        $formation_fallbacks = [
            ['id' => 'learning_arcs', 'title' => 'Learning Arcs', 'url' => 'https://geralddaquila.com/steward-access-12-learning-arcs/'],
            ['id' => 'stewardship_frameworks', 'title' => 'Stewardship Frameworks', 'url' => 'https://geralddaquila.com/stewardship-framework/'],
            ['id' => 'stewardship_practice', 'title' => 'Stewardship Practice', 'url' => 'https://geralddaquila.com/stewardship-practice/'],
            ['id' => 'governance_foundations', 'title' => 'Governance Foundations', 'url' => 'https://geralddaquila.com/governance-foundations/'],
        ];
        foreach ($formation_fallbacks as $fallback) {
            if (count($doors) >= 3) break;
            if (isset($seen_ids[$fallback['id']])) continue;
            $seen_ids[$fallback['id']] = true;
            $doors[] = $fallback;
        }

        if (count($doors) !== 3) {
            throw new RuntimeException('Formation boundary could not construct three canonical destinations.');
        }

        $interpretation = is_array($contribution['interpretation'] ?? null) ? $contribution['interpretation'] : [];
        $movement = is_array($contribution['movement'] ?? null) ? $contribution['movement'] : [];
        $reflection = $this->formation_reflection($interpretation, (string)($contribution['_formation_response'] ?? ''));
        $why_text = $this->formation_movement_text($movement, $interpretation);
        $why_by_id = [
            'learning_arcs' => 'Explore learning that can help you carry responsibility as it changes.',
            'governance_foundations' => 'Examine how responsibility, authority, and shared decisions can be held.',
            'stewardship_practice' => 'Bring the question into practice and integration.',
            'stewardship_frameworks' => 'Find an orienting framework for the responsibility you are carrying.',
        ];
        $why = [];
        foreach ($doors as $door) {
            $why[$door['id']] = $why_by_id[$door['id']] ?? $why_text;
        }

        return [
            'version' => SPE_VERSION,
            'reflection' => $reflection,
            'selected' => $doors,
            'why_each' => $why,
            'needs_clarification' => false,
            'clarifying_question' => '',
            'movement_type' => 'continue',
            'landscape' => $this->landscape_destinations(),
            'formation' => [
                'status' => $status,
                'contract_version' => (string)($contribution['contract_version'] ?? 'v1'),
                'voice_policy' => (string)($contribution['voice_policy'] ?? 'preserve_specialist_boundary'),
                'boundary_notes' => $contribution['boundary_notes'] ?? [],
                'safety_flags' => $contribution['safety_flags'] ?? [],
            ],
        ];
    }

    private function landscape_destinations(): array {
        return [
            ['title' => 'Stewardship Archive', 'url' => 'https://geralddaquila.com/stewardship-archive/'],
            ['title' => 'Learning Arcs', 'url' => 'https://geralddaquila.com/steward-access-12-learning-arcs/'],
            ['title' => 'Governance & Institution Building', 'url' => 'https://geralddaquila.com/governance-institution-building/'],
            ['title' => 'Stewardship Practice', 'url' => 'https://geralddaquila.com/stewardship-practice/'],
            ['title' => 'Stewardship Case Library', 'url' => 'https://geralddaquila.com/applied-stewardship-case-library/'],
            ['title' => 'Stewardship Frameworks', 'url' => 'https://geralddaquila.com/stewardship-framework/'],
            ['title' => 'Coherent Leadership Selection System', 'url' => 'https://geralddaquila.com/coherent-leadership-selection-system-clss-2/'],
            ['title' => 'Stewardship Readiness Institute', 'url' => 'https://geralddaquila.com/professional-framework/professional-framework/'],
        ];
    }

    private function formation_reflection(array $interpretation, string $response = ''): string {
        foreach (['pathway', 'summary', 'situation', 'presenting_situation', 'responsibility', 'tension'] as $field) {
            $value = trim((string)($interpretation[$field] ?? ''));
            if ($value !== '') return wp_strip_all_tags($value);
        }
        $response = wp_strip_all_tags(trim($response));
        if ($response !== '') return $response;
        return 'Something in what you described may be worth looking at from another angle.';
    }

    private function formation_movement_text(array $movement, array $interpretation): string {
        foreach (['description', 'summary', 'text'] as $field) {
            $value = trim((string)($movement[$field] ?? ''));
            if ($value !== '') return wp_strip_all_tags($value);
        }
        foreach (['tension', 'capacity', 'responsibility'] as $field) {
            $value = trim((string)($interpretation[$field] ?? ''));
            if ($value !== '') return wp_strip_all_tags($value);
        }
        return 'Each destination offers a different way to explore the responsibility you described.';
    }

    private function rate_ok(): bool {
        $ip = isset($_SERVER['REMOTE_ADDR']) ? (string)$_SERVER['REMOTE_ADDR'] : 'unknown';
        $key = 'spe_rl_' . hash_hmac('sha256', $ip, wp_salt('auth'));
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
        add_options_page('Stewardship Pathway', 'Stewardship Pathway', 'manage_options', 'stewardship-pathway', [$this, 'settings_page']);
    }

    public function settings(): void {
        register_setting('spe_settings', 'spe_groq_api_key', [
            'type' => 'string',
            'sanitize_callback' => function($value) {
                $value = trim((string)$value);
                if ($value === '') return (string)get_option('spe_groq_api_key', '');
                return $value;
            },
            'default' => '',
        ]);
        add_settings_section('spe_main', 'Pathway Engine', '__return_false', 'stewardship-pathway');
        add_settings_field('spe_groq_api_key', 'Groq API key', [$this, 'key_field'], 'stewardship-pathway', 'spe_main');
        register_setting('spe_settings', 'spe_formation_endpoint', [
            'type' => 'string',
            'sanitize_callback' => static function($value) { return trim((string)$value); },
            'default' => 'https://living-archive-backend.onrender.com/api/formation-entrance',
        ]);
        add_settings_field('spe_formation_endpoint', 'Formation bridge endpoint', [$this, 'formation_endpoint_field'], 'stewardship-pathway', 'spe_main');
    }

    public function key_field(): void {
        echo '<input type="password" name="spe_groq_api_key" value="" class="regular-text" autocomplete="new-password" placeholder="Leave blank to keep the existing key">';
        echo '<p class="description">The key is stored server-side and is never sent to the visitor browser.</p>';
    }

    public function formation_endpoint_field(): void {
        $endpoint = (string)get_option('spe_formation_endpoint', 'https://living-archive-backend.onrender.com/api/formation-entrance');
        echo '<input type="url" name="spe_formation_endpoint" value="' . esc_attr($endpoint) . '" class="regular-text" autocomplete="off">';
        echo '<p class="description">Native WordPress bridge for the bounded Formation specialist. The visitor browser never calls Render directly.</p>';
    }

    public function settings_page(): void {
        if (!current_user_can('manage_options')) return;
        $status = $this->engine()->corpus_status();
        echo '<div class="wrap"><h1>Stewardship Pathway</h1>';
        echo '<p>The engine is installed as the native Stewardship Pathway Engine. The visitor browser calls WordPress; WordPress may bridge the request to the bounded Formation specialist in the Living Archive backend.</p>';
        echo '<h2>Corpus</h2><p>Version ' . esc_html($status['version']) . ' · ' . esc_html((string)$status['resources']) . ' routable resources · ' . esc_html((string)$status['relationships']) . ' relationships</p>';
        echo '<form method="post" action="options.php">';
        settings_fields('spe_settings');
        do_settings_sections('stewardship-pathway');
        submit_button('Save Groq API key');
        echo '</form></div>';
    }

    public function admin_notice(): void {
        if (!current_user_can('manage_options')) return;
        if (trim((string)get_option('spe_groq_api_key', '')) !== '') return;
        $screen = function_exists('get_current_screen') ? get_current_screen() : null;
        if (!$screen || strpos((string)$screen->id, 'stewardship') === false) return;
        echo '<div class="notice notice-warning"><p><strong>Stewardship Pathway:</strong> add the Groq API key under Settings → Stewardship Pathway before using the pathway.</p></div>';
    }
}

Stewardship_Pathway_Plugin::instance();
