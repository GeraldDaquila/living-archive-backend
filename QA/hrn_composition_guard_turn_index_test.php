<?php
/**
 * Isolated WordPress test for the HRN composition guard's browser turn index.
 * The browser sends completed-turn count, not the index of the incoming turn.
 */
if (!defined('ABSPATH') || !class_exists('WP_REST_Request') || !class_exists('WP_REST_Response')) {
    fwrite(STDERR, "WordPress runtime is not loaded.\n");
    exit(1);
}
$assert = static function ($condition, $label) {
    if (!$condition) { fwrite(STDERR, "FAIL: " . $label . "\n"); exit(1); }
    echo "PASS: " . $label . "\n";
};
$run = static function ($message, $completedTurns, $history = '', $overrides = array(), $status = 503, $includeTurns = true) {
    $request = new WP_REST_Request('POST', '/living-archive/v1/relational-navigator');
    $request->set_param('message', $message);
    if ($includeTurns) $request->set_param('unit_turns', $completedTurns);
    $request->set_param('conversation', $history);
    $request->set_param('visitor_history', '');
    $request->set_param('full_conversation', '');
    $base = array(
        'ok' => false,
        'status' => 503,
        'reason' => 'composition_unavailable',
        'response' => '',
        'question' => '',
        'meta' => array(),
    );
    $response = new WP_REST_Response(array_merge($base, $overrides), $status);
    $server = rest_get_server();
    $filtered = apply_filters('rest_post_dispatch', $response, $server, $request);
    if (!($filtered instanceof WP_REST_Response)) {
        fwrite(STDERR, "FAIL: guard returned an unexpected response type.\n");
        exit(1);
    }
    return $filtered;
};

$firstMessage = 'I keep putting off a conversation with my friend because I am afraid it will change the friendship.';
$first = $run($firstMessage, 0);
$firstData = $first->get_data();
$assert($first->get_status() === 200, 'completed-turn count 0 maps to incoming turn 1');
$assert(($firstData['hrn_composition_recovery'] ?? '') === 'bounded_friendship_conversation_fallback_v2', 'first visitor turn selects the friendship opening recovery');
$assert(strpos((string)($firstData['question'] ?? ''), 'What feels most important to protect') !== false, 'first visitor turn receives the opening question');
$assert(($firstData['hrn_composition_recovery_version'] ?? '') === '1.3.10', 'candidate recovery version is reported');

$history = "Visitor: " . $firstMessage . "\nNavigator: You want to speak honestly with your friend, but you are worried that naming what is on your mind could change the friendship.";
$secondMessage = 'I want to protect the trust between us and I do not want my friend to feel blamed.';
$second = $run($secondMessage, 1, $history);
$secondData = $second->get_data();
$assert($second->get_status() === 200, 'completed-turn count 1 maps to incoming turn 2');
$assert(($secondData['hrn_composition_recovery'] ?? '') === 'bounded_friendship_conversation_progression_v1', 'second visitor turn selects contextual friendship progression, not the generic opening fallback');
$assert(strpos((string)($secondData['response'] ?? ''), 'protect the trust') !== false, 'second-turn response preserves the new trust and blame distinction');
$assert(strpos((string)($secondData['question'] ?? ''), 'What would you most want your friend to understand') !== false, 'second-turn question follows the visitor’s latest contribution');

$managerMessage = 'My manager questions every decision and asks me to justify my reasoning again.';
$third = $run($managerMessage, 2, 'Visitor: My manager says they trust me, but they question every decision.');
$thirdData = $third->get_data();
$assert($third->get_status() === 200, 'completed-turn count 2 maps to incoming turn 3');
$assert(($thirdData['hrn_composition_recovery'] ?? '') === 'bounded_manager_progression_v7', 'third visitor turn selects the third manager progression');
$assert(strpos((string)($thirdData['question'] ?? ''), 'What would a reasonable level of review look like') !== false, 'third-turn manager question is selected');

$fallback = $run($managerMessage, null, '', array('unit_position' => 3), 503, false);
$fallbackData = $fallback->get_data();
$assert(($fallbackData['hrn_composition_recovery'] ?? '') === 'bounded_manager_progression_v7', 'server unit_position remains the fallback when unit_turns is absent');

$safety = $run($secondMessage, 1, $history, array('safety_interrupt' => true, 'safety' => 'amber'), 503);
$safetyData = $safety->get_data();
$assert($safety->get_status() === 503 && empty($safetyData['hrn_composition_recovery']), 'safety interruption bypasses composition recovery unchanged');

$valid = $run($managerMessage, 2, '', array('ok' => true, 'status' => 200, 'reason' => '', 'response' => 'Already composed safely.', 'question' => 'What did the review look like?'), 200);
$validData = $valid->get_data();
$assert($valid->get_status() === 200 && ($validData['response'] ?? '') === 'Already composed safely.', 'valid responses pass through without recovery rewriting');

echo "All HRN composition-guard turn-index tests passed.\n";
