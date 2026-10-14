<?php
/**
 * Plugin Name: Living Archive — HRN Command Boundary Adapter
 * Description: Normalizes explicit visitor closure commands and returns completed HRN journeys to USE for a grounded canonical doorway, without modifying the frozen HRN writer.
 * Version: 1.2.1
 * Author: Living Archive
 */
if (!defined('ABSPATH')) { exit; }

add_filter('rest_request_before_callbacks', function ($response, $handler, $request) {
    if ($response !== null) return $response;
    if (!($request instanceof WP_REST_Request)) return $response;
    if (strtoupper((string)$request->get_method()) !== 'POST') return $response;
    if (rtrim((string)$request->get_route(), '/') !== '/living-archive/v1/relational-navigator') return $response;

    $message = strtolower(trim((string)$request->get_param('message')));
    $commands = array('stop', 'end', 'done', 'finish', 'close', 'end conversation', 'stop conversation', 'end chat', 'stop chat');
    if (!in_array($message, $commands, true)) return $response;

    $request->set_param('message', 'I want to stop here');
    $request->set_param('journey_action', 'end');
    $request->set_param('hrn_boundary_command', $message);
    return $response;
}, 5, 3);

/**
 * Keep the frozen HRN writer untouched. When a completed journey is returned,
 * ask USE for the grounded canonical doorway. If whole-journey synthesis alone
 * fails after an explicit visitor close, reuse the last grounded HRN observation
 * (minus its question) as a bounded landing rather than forcing the visitor to retry.
 */
add_filter('rest_post_dispatch', function ($response, $server, $request) {
    if (!($request instanceof WP_REST_Request)) return $response;
    if (strtoupper((string)$request->get_method()) !== 'POST') return $response;
    if (rtrim((string)$request->get_route(), '/') !== '/living-archive/v1/relational-navigator') return $response;
    if (!($response instanceof WP_REST_Response)) return $response;

    $data = $response->get_data();
    if (!is_array($data)) return $response;

    $message = strtolower(trim((string)$request->get_param('message')));
    $boundary_command = strtolower(trim((string)$request->get_param('hrn_boundary_command')));
    $journey_action = strtolower(trim((string)$request->get_param('journey_action')));
    $visitor_requested_close = in_array($journey_action, array('end', 'close'), true)
        || in_array($boundary_command, array('stop', 'end', 'done', 'finish', 'close', 'end conversation', 'stop conversation', 'end chat', 'stop chat'), true)
        || (bool)preg_match('/\b(i want to stop here|i want to (?:stop|end|finish|close)|i am done|i\x27m done|leave it here|leave this here|please synthesize|please summarize)\b/i', $message);

    $is_synthesis_failure = (
        sanitize_key((string)($data['operation'] ?? '')) === 'whole_journey_synthesis'
        || sanitize_key((string)($data['reason'] ?? '')) === 'synthesis_unavailable'
    );
    if (empty($data['unit_complete']) && $visitor_requested_close && $is_synthesis_failure) {
        if (!empty($data['safety_interrupt'])) return $response;
        $safety = $data['safety'] ?? '';
        if (is_string($safety) && in_array(strtolower($safety), array('amber', 'red'), true)) return $response;

        $conversation = $request->get_param('conversation');
        if (!is_string($conversation) && is_array($conversation)) $conversation = wp_json_encode($conversation);
        if (!is_string($conversation) || $conversation === '') {
            $conversation = $request->get_param('full_conversation') ?: $request->get_param('visitor_history');
            if (is_array($conversation)) $conversation = wp_json_encode($conversation);
            if (!is_string($conversation)) $conversation = '';
        }
        $turns = json_decode($conversation, true);
        $last_assistant = '';
        if (is_array($turns)) {
            for ($i = count($turns) - 1; $i >= 0; $i--) {
                if (!is_array($turns[$i])) continue;
                $role = strtolower((string)($turns[$i]['role'] ?? ''));
                if (in_array($role, array('assistant', 'hrn', 'seeing the relationship'), true)) {
                    $last_assistant = trim((string)($turns[$i]['content'] ?? ''));
                    if ($last_assistant !== '') break;
                }
            }
        }
        if ($last_assistant === '') return $response;
        $grounded_landing = trim((string)preg_replace('/\s+[^.!?]*\?\s*$/u', '', $last_assistant));
        if ($grounded_landing === '') $grounded_landing = $last_assistant;

        $ledger = is_array($data['journey_ledger'] ?? null) ? $data['journey_ledger'] : array();
        $session_id = (string)($ledger['session_id'] ?? $request->get_param('session_id') ?? '');
        $original_question = trim((string)(
            $request->get_param('original_question')
            ?: $request->get_param('query')
            ?: $request->get_param('initial_question')
        ));
        if ($original_question === '' && is_array($turns)) {
            foreach ($turns as $turn) {
                if (!is_array($turn)) continue;
                if (in_array(strtolower((string)($turn['role'] ?? '')), array('user', 'visitor', 'human'), true)) {
                    $original_question = trim((string)($turn['content'] ?? ''));
                    if ($original_question !== '') break;
                }
            }
        }

        $data = array(
            'ok' => true,
            'version' => (string)($data['version'] ?? '0.5.330'),
            'response' => $grounded_landing,
            'question' => '',
            'rest' => true,
            'use_resource' => false,
            'resource_intro' => '',
            'resources' => array(),
            'unit_position' => (int)($data['meta']['unit_position'] ?? $request->get_param('unit_turns') ?? 0),
            'unit_complete' => true,
            'junction_available' => false,
            'conversation_phase' => 'integration',
            'movement_state' => 'consolidating',
            'thread_summary' => $original_question,
            'completed_insight' => $grounded_landing,
            'body_of_thought' => $grounded_landing,
            'journey_synthesis' => $grounded_landing,
            'journey_ledger' => array_merge($ledger, array('session_id' => $session_id)),
            'fractal_records' => is_array($data['fractal_records'] ?? null) ? $data['fractal_records'] : array(),
            'round_synthesis_history' => is_array($data['round_synthesis_history'] ?? null) ? $data['round_synthesis_history'] : array(),
            'return_handoff_status' => 'grounded_close_recovered_after_synthesis_unavailable',
        );
        $response->set_status(200);
        $response->set_data($data);
    }

    $data = $response->get_data();
    if (!is_array($data) || empty($data['unit_complete'])) return $response;
    if (!empty($data['safety_interrupt'])) return $response;
    if (!empty($data['junction_available']) || !empty($data['canonical_doorway'])) return $response;

    $safety = $data['safety'] ?? '';
    if (is_string($safety) && in_array(strtolower($safety), array('amber', 'red'), true)) return $response;
    if (is_array($safety)) {
        $safety_level = strtolower((string)($safety['level'] ?? $safety['state'] ?? ''));
        if (in_array($safety_level, array('amber', 'red'), true)) return $response;
    }

    $conversation = $request->get_param('conversation');
    if (is_array($conversation)) $conversation = wp_json_encode($conversation);
    if (!is_string($conversation) || $conversation === '') {
        $conversation = $request->get_param('full_conversation') ?: $request->get_param('visitor_history');
        if (is_array($conversation)) $conversation = wp_json_encode($conversation);
        if (!is_string($conversation)) $conversation = '';
    }

    $original_question = trim((string)(
        $request->get_param('original_question')
        ?: $request->get_param('query')
        ?: $request->get_param('initial_question')
    ));
    if ($original_question === '' && $conversation !== '') {
        $turns = json_decode($conversation, true);
        if (is_array($turns)) {
            foreach ($turns as $turn) {
                if (!is_array($turn)) continue;
                if (in_array(strtolower((string)($turn['role'] ?? '')), array('user', 'visitor', 'human'), true)) {
                    $original_question = trim((string)($turn['content'] ?? ''));
                    if ($original_question !== '') break;
                }
            }
        }
    }
    if ($original_question === '') return $response;

    $ledger = is_array($data['journey_ledger'] ?? null) ? $data['journey_ledger'] : array();
    $payload = array(
        'session_id' => (string)($ledger['session_id'] ?? $request->get_param('session_id') ?? ''),
        'original_question' => $original_question,
        'conversation' => $conversation,
        'thread_summary' => (string)($data['thread_summary'] ?? ''),
        'completed_insight' => (string)($data['completed_insight'] ?? ''),
        'perspective_delta' => (string)($data['perspective_delta'] ?? ''),
        'body_of_thought' => (string)($data['body_of_thought'] ?? ''),
        'underlying_need' => (string)($data['underlying_need'] ?? ''),
        'desired_condition' => (string)($data['desired_condition'] ?? ''),
        'next_horizon' => (string)($data['next_horizon'] ?? ''),
        'resource_fit' => (string)($data['resource_fit'] ?? ''),
        'journey_synthesis' => (string)($data['journey_synthesis'] ?? ''),
        'journey_action' => 'end',
        'journey_ledger' => $ledger,
        'fractal_records' => is_array($data['fractal_records'] ?? null) ? $data['fractal_records'] : array(),
        'round_synthesis_history' => is_array($data['round_synthesis_history'] ?? null) ? $data['round_synthesis_history'] : array(),
    );

    $endpoints = array(
        'https://living-archive-backend.onrender.com/api/relational-return',
        'https://living-archive-backend-mirror.onrender.com/api/relational-return',
    );
    $returned = null;
    foreach ($endpoints as $endpoint) {
        $remote = wp_remote_post($endpoint, array(
            'timeout' => 15,
            'redirection' => 0,
            'headers' => array('Content-Type' => 'application/json', 'Accept' => 'application/json'),
            'body' => wp_json_encode($payload),
        ));
        if (is_wp_error($remote)) continue;
        $status = (int)wp_remote_retrieve_response_code($remote);
        if ($status < 200 || $status >= 300) continue;
        $decoded = json_decode((string)wp_remote_retrieve_body($remote), true);
        if (!is_array($decoded) || empty($decoded['ok'])) continue;
        $returned = $decoded;
        break;
    }

    if (!is_array($returned)) return $response;

    $doorway = $returned['canonical_doorway'] ?? null;
    if (!is_array($doorway) || empty($doorway['title']) || empty($doorway['url'])) {
        $data['junction_available'] = false;
        $data['resources'] = array();
        $data['resource_intro'] = '';
        $data['return_handoff_status'] = 'no_grounded_doorway';
        $response->set_data($data);
        return $response;
    }

    $title = wp_strip_all_tags((string)$doorway['title']);
    $url = esc_url_raw((string)$doorway['url']);
    if ($title === '' || $url === '' || !wp_http_validate_url($url)) return $response;

    $data['junction_available'] = true;
    $data['unit_complete'] = true;
    $data['question'] = '';
    $data['rest'] = true;
    $data['use_resource'] = true;
    $data['canonical_doorway'] = array('title' => $title, 'url' => $url);
    $data['resources'] = array(array('title' => $title, 'url' => $url));
    $intro = trim((string)($returned['response'] ?? ''));
    $context = strtolower((string)($data['journey_synthesis'] ?? $data['completed_insight'] ?? ''));
    $title_context = strtolower($title);
    if (
        strpos($intro, 'There is a place in the Archive that may carry this new perspective further.') !== false
        && preg_match('/\\b(scope|deadline|agreement|work)\\b/i', $context)
        && strpos($title_context, 'conflict') !== false
        && strpos($title_context, 'conversation') !== false
    ) {
        $intro = 'You were trying to discuss what changed in the work, but the conversation shifted toward judging your reaction. This piece looks at what happens when a conversation can no longer hold the conflict itself.';
    }
    $data['resource_intro'] = $intro;
    $data['junction_summary'] = trim((string)($data['journey_synthesis'] ?? $data['completed_insight'] ?? ''));
    if (isset($returned['relational_journey'])) $data['relational_journey'] = $returned['relational_journey'];
    $data['return_handoff_status'] = 'canonical_doorway_ready';
    $data['return_handoff_version'] = (string)($returned['version'] ?? '');
    $response->set_data($data);
    return $response;
}, 99, 3);
