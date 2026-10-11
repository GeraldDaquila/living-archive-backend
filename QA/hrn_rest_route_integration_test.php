<?php
/**
 * Isolated WordPress REST-dispatch integration test for HRN natural landing.
 * Boots the candidate plugin and invokes its registered REST route. Provider HTTP
 * is deterministic: the observer returns an earned STOP; composition fails so the
 * candidate must use its real policy-gated local landing recovery.
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

add_filter('pre_http_request', static function ($preempt, $args, $url) use ($earned, $purpose) {
    if (strpos((string)$url, 'api.groq.com') === false) return new WP_Error('hrn_qa_external_http_blocked', 'External HTTP is disabled in isolated HRN QA.');
    $body = json_decode((string)($args['body'] ?? ''), true);
    $messages = is_array($body) ? (array)($body['messages'] ?? array()) : array();
    $system = '';
    foreach ($messages as $message) {
        if (is_array($message) && ($message['role'] ?? '') === 'system') { $system = (string)($message['content'] ?? ''); break; }
    }
    if (strpos($system, 'observer_intention, observer_contrast, observer_so_what, observer_delta, observer_horizon, observer_decision, observer_next_intention') !== false) {
        $observer = array(
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
        $responseBody = array('choices'=>array(array('message'=>array('content'=>wp_json_encode($observer)))));
        return array('headers'=>array('content-type'=>'application/json'),'body'=>wp_json_encode($responseBody),
            'response'=>array('code'=>200,'message'=>'OK'),'cookies'=>array(),'filename'=>null);
    }
    return new WP_Error('hrn_qa_composition_unavailable', 'Synthetic provider composition failure.');
}, 10, 3);

$request = new WP_REST_Request('POST', '/living-archive/v1/relational-navigator');
$request->set_header('content-type','application/json');
$request->set_param('message','I can see that wanting to be understood and keeping boundaries can both matter. Please let this conversation land.');
$request->set_param('original_question','I want to understand a difficult friendship without losing my boundaries.');
$request->set_param('conversation','Assistant: Wanting to be understood and keeping personal boundaries can both matter, even while the other person’s intention remains unknown.');
$request->set_param('full_conversation','Assistant: Wanting to be understood and keeping personal boundaries can both matter, even while the other person’s intention remains unknown.');
$request->set_param('session_id',$session);
$request->set_param('unit_turns',3);
$request->set_param('safety_stage','green');

$response = rest_do_request($request);
$status = $response instanceof WP_REST_Response ? $response->get_status() : 500;
$data = $response instanceof WP_REST_Response ? $response->get_data() : array('error'=>$response instanceof WP_Error ? $response->get_error_message() : 'unknown');
$assert($status === 200, 'registered REST route returns HTTP 200 after provider composition failure; got '.$status.' '.wp_json_encode($data));
$assert(is_array($data) && trim((string)($data['response'] ?? '')) !== '', 'route returns a non-empty visitor-facing landing');
$assert(empty($data['question']), 'natural landing does not reopen with a question');
$assert(!empty($data['rest']) && empty($data['use_resource']), 'natural landing returns rest state without forced resource handoff');
$assert(stripos((string)$data['response'],'understood') !== false || stripos((string)$data['response'],'boundar') !== false, 'landing retains earned journey evidence');
$assert(strpos((string)$data['response'],'spiral_landing_composition_unavailable') === false, 'route does not leak internal failure reason');
echo "HRN ISOLATED REST ROUTE INTEGRATION: PASS\n";
