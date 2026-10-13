<?php
/**
 * Isolated WordPress REST-dispatch integration test for HRN natural landing.
 * The candidate plugin and actual registered REST route execute in WordPress.
 * Only the shared Provider Bank Bridge is stubbed: perception returns an earned
 * STOP and relational composition fails, forcing the real local recovery path.
 */
if (!defined('ABSPATH') || !class_exists('WP_REST_Request')) {
    fwrite(STDERR, "WordPress runtime is not loaded.\n");
    exit(1);
}
$assert = static function ($condition, $label) {
    if (!$condition) { fwrite(STDERR, "FAIL: " . $label . "\n"); exit(1); }
    echo "PASS: " . $label . "\n";
};
$session = 'hrn-isolated-natural-landing-v05279';
$earned = 'Wanting to be understood and keeping personal boundaries can both matter, even while the other person’s intention remains unknown.';
$purpose = 'a friendship where understanding and personal boundaries both matter';
$GLOBALS['hrn_qa_earned'] = $earned;
$GLOBALS['hrn_qa_purpose'] = $purpose;
$GLOBALS['hrn_qa_operations'] = array();
$GLOBALS['hrn_qa_observer'] = array(
    'observer_intention'=>'friendship and boundaries','observer_contrast'=>$earned,'observer_so_what'=>$earned,
    'observer_delta'=>$earned,'observer_horizon'=>'','observer_decision'=>'STOP','observer_next_intention'=>'',
    'situation'=>'a friendship with uncertainty about being understood','parties'=>'the visitor and a friend',
    'experience'=>$earned,'tension'=>'being understood and maintaining boundaries',
    'pattern'=>'the meaning of the other person’s response remains uncertain','underlying_need'=>'understanding',
    'desired_condition'=>'clarity without a forced verdict','emerging_delta'=>$earned,'perspective_delta'=>$earned,
    'unresolved'=>'the other person’s intention remains unknown','body_of_thought'=>$earned,'current_fractal'=>$purpose,
    'next_horizon'=>'','conversation_purpose'=>$purpose,'working_hypothesis'=>$earned,'movement_state'=>'consolidating',
    'conversation_phase'=>'integration','service_orientation'=>'unclear','fractal_stage'=>'rest','fractal_maturity'=>'complete',
    'fractal_complete'=>true,'fractal_summary'=>$earned,'last_nugget'=>$earned,'closure_signal'=>'invite_close',
    'leadership_need'=>'integrate_and_land'
);

// In the isolated WordPress runtime the production Provider Bank Bridge plugin is
// intentionally absent. Stub only its public function contract, not HRN internals.
if (!function_exists('la_provider_bank_request')) {
    function la_provider_bank_request($operation, $messages, $max_tokens, $schema) {
        $GLOBALS['hrn_qa_operations'][] = (string)$operation;
        if ($operation === 'hrn_perception') {
            return array(
                'provider'=>'isolated-qa','model'=>'observer-fixture','gateway_contract'=>'qa-v1',
                'provider_bank_contract'=>'qa-v1','result'=>(array)$GLOBALS['hrn_qa_observer']
            );
        }
        return new WP_Error('hrn_qa_composition_unavailable', 'Synthetic provider composition failure.');
    }
}

$ledger = array(
    'state_version'=>'1.5','session_id'=>$session,'turn'=>3,'journey_purpose'=>$purpose,'current_terrain'=>$purpose,
    'movement_status'=>'integrating','fractal_stage'=>'rest','fractal_maturity'=>'complete','leadership_need'=>'integrate_and_land',
    'fractal_complete'=>true,'observer_decision'=>'STOP','closure_signal'=>'invite_close','last_fractal_summary'=>$earned,
    'last_nugget'=>$earned,'completed_insights'=>array($earned),'perspective_delta'=>$earned,'last_delta'=>$earned,
    'body_of_thought'=>$earned,'round_synthesis_history'=>array($earned),'fractal_records'=>array($earned),
    'unresolved'=>'the other person’s intention remains unknown'
);
$ledgerKey = 'lah_rn_journey_' . substr(hash('sha256', '1.5|' . $session), 0, 32);
set_transient($ledgerKey, $ledger, 86400);

$request = new WP_REST_Request('POST', '/living-archive/v1/relational-navigator');
$request->set_header('content-type','application/json');
$request->set_param('message','I can see that wanting to be understood and keeping boundaries can both matter. Please let this conversation land.');
$request->set_param('original_question','I want to understand a difficult friendship without losing my boundaries.');
$request->set_param('conversation','Assistant: Wanting to be understood and keeping personal boundaries can both matter, even while the other person’s intention remains unknown.');
$request->set_param('full_conversation','Assistant: Wanting to be understood and keeping personal boundaries can both matter, even while the other person’s intention remains unknown.');
$request->set_param('session_id',$session);
$request->set_param('unit_turns',3);
$request->set_param('safety_stage','green');

set_error_handler(static function ($severity, $message, $file, $line) {
    if (!(error_reporting() & $severity)) return false;
    if (in_array($severity, array(E_WARNING, E_NOTICE, E_USER_WARNING, E_USER_NOTICE), true)) {
        throw new ErrorException($message, 0, $severity, $file, $line);
    }
    return false;
});
$response = rest_do_request($request);
restore_error_handler();
$status = $response instanceof WP_REST_Response ? $response->get_status() : 500;
$data = $response instanceof WP_REST_Response ? $response->get_data() : array('error'=>$response instanceof WP_Error ? $response->get_error_message() : 'unknown');
$assert(class_exists('HRN_Canonical_Retriever'), 'tracked canonical retriever class is loaded in isolated WordPress');
$assert(in_array('hrn_perception', $GLOBALS['hrn_qa_operations'], true), 'real REST handler calls the Provider Bank perception contract');
$assert(in_array('hrn_relational', $GLOBALS['hrn_qa_operations'], true), 'natural landing reaches the relational composition operation');
$assert($status === 200 && !empty($data['ok']), 'registered REST route completes successfully; got HTTP '.$status.' '.wp_json_encode($data));
$assert(($data['version'] ?? '') === '0.5.280', 'isolated route executes the v0.5.311 candidate');
$assert(is_array($data) && trim((string)($data['response'] ?? '')) !== '', 'route returns a non-empty visitor-facing landing');
$assert(empty($data['question']), 'natural landing does not reopen with a question');
$assert(!empty($data['rest']) && empty($data['use_resource']), 'natural landing returns rest state without forced resource handoff');
$assert(stripos((string)$data['response'],'understood') !== false || stripos((string)$data['response'],'boundar') !== false, 'landing retains earned journey evidence');
$assert(strpos((string)$data['response'],'spiral_landing_composition_unavailable') === false, 'route does not leak internal failure reason');

// Continue the same visitor journey through explicit closure with every composition
// provider unavailable. This exercises the actual REST closure branch as well.
$closureMessage = 'I can see that I may be treating being understood and protecting myself as opposites, when both can matter. Please synthesize what we have learned and close the conversation.';
$closureRequest = new WP_REST_Request('POST', '/living-archive/v1/relational-navigator');
$closureRequest->set_header('content-type','application/json');
$closureRequest->set_param('message',$closureMessage);
$closureRequest->set_param('original_question','I want to understand a difficult friendship without losing my boundaries.');
$closureRequest->set_param('conversation','Assistant: '.(string)$data['response']."\\nVisitor: ".$closureMessage);
$closureRequest->set_param('full_conversation','Assistant: '.(string)$data['response']."\\nVisitor: ".$closureMessage);
$closureRequest->set_param('session_id',$session);
$closureRequest->set_param('journey_action','end');
$closureRequest->set_param('unit_turns',4);
$closureRequest->set_param('safety_stage','green');
set_error_handler(static function ($severity, $message, $file, $line) {
    if (!(error_reporting() & $severity)) return false;
    if (in_array($severity, array(E_WARNING, E_NOTICE, E_USER_WARNING, E_USER_NOTICE), true)) {
        throw new ErrorException($message, 0, $severity, $file, $line);
    }
    return false;
});
$closureResponse = rest_do_request($closureRequest);
restore_error_handler();
$closureStatus = $closureResponse instanceof WP_REST_Response ? $closureResponse->get_status() : 500;
$closureData = $closureResponse instanceof WP_REST_Response ? $closureResponse->get_data() : array('error'=>$closureResponse instanceof WP_Error ? $closureResponse->get_error_message() : 'unknown');
$assert($closureStatus === 200 && !empty($closureData['ok']), 'explicit closure REST route succeeds with composition provider unavailable; got HTTP '.$closureStatus.' '.wp_json_encode($closureData));
$assert(trim((string)($closureData['response'] ?? '')) !== '', 'explicit closure returns a non-empty synthesis');
$assert(empty($closureData['question']), 'explicit closure does not reopen with a question');
$assert(stripos((string)$closureData['response'],'understood') !== false || stripos((string)$closureData['response'],'boundar') !== false, 'explicit closure retains visitor-authored evidence');
echo "HRN ISOLATED REST ROUTE INTEGRATION: PASS\n";
