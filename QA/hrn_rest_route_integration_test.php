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
        if ($operation === 'hrn_relational' && isset($GLOBALS['hrn_qa_composition_result'])) {
            return array(
                'provider'=>'isolated-qa','model'=>'missing-question-fixture','gateway_contract'=>'qa-v1',
                'provider_bank_contract'=>'qa-v1','result'=>(array)$GLOBALS['hrn_qa_composition_result']
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
$request->set_param('message','I can see that wanting to be understood and keeping boundaries can both matter.');
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
$assert(($data['version'] ?? '') === '0.5.324', 'isolated route executes the v0.5.324 candidate');
$assert(is_array($data) && trim((string)($data['response'] ?? '')) !== '', 'route returns a non-empty visitor-facing landing');
$assert(empty($data['question']), 'natural landing does not reopen with a question');
$assert(!empty($data['rest']) && empty($data['use_resource']), 'natural landing returns rest state without forced resource handoff');
$assert(stripos((string)$data['response'],'understood') !== false || stripos((string)$data['response'],'boundar') !== false, 'landing retains earned journey evidence');
$assert(strpos((string)$data['response'],'spiral_landing_composition_unavailable') === false, 'route does not leak internal failure reason');

// Continue the same visitor journey through explicit closure with every composition
// provider unavailable. This exercises the actual REST closure branch as well.
$closureMessage = 'I think I understand the pattern now. Please let this conversation land.';
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

 // Ordinary substantive turns must remain conversational when the provider returns
 // useful prose but omits its question and sets default rest/resource flags.
$ordinarySession = 'hrn-isolated-missing-question-v05311';
$ordinaryMessage = 'I keep putting off a conversation with a friend because I am afraid it will change the friendship.';
$GLOBALS['hrn_qa_observer'] = array_merge((array)$GLOBALS['hrn_qa_observer'], array(
    'observer_intention'=>'honesty and continuity in a friendship',
    'observer_contrast'=>'Honesty and continuity can both matter without guaranteeing a particular outcome.',
    'observer_so_what'=>'Treating honesty and continuity as distinct helps clarify what feels at stake.',
    'observer_delta'=>'The conversation itself and the future of the friendship are not identical.',
    'observer_horizon'=>'the relationship between honesty and continuity',
    'observer_decision'=>'CONTINUE',
    'observer_next_intention'=>'open a different vantage point',
    'situation'=>'fear that an honest conversation might change a friendship',
    'experience'=>$ordinaryMessage,
    'tension'=>'honesty and continuity',
    'pattern'=>'fear of change is delaying a conversation',
    'underlying_need'=>'to be understood',
    'desired_condition'=>'honesty without assuming a particular outcome',
    'emerging_delta'=>'the conversation and the future of the friendship are distinct',
    'perspective_delta'=>'the conversation and the future of the friendship are distinct',
    'body_of_thought'=>'',
    'current_fractal'=>'honesty and continuity in a friendship',
    'next_horizon'=>'the relationship between honesty and continuity',
    'conversation_purpose'=>'understand a difficult friendship',
    'movement_state'=>'exploring',
    'conversation_phase'=>'exploration',
    'fractal_stage'=>'exploration',
    'fractal_maturity'=>'immature',
    'fractal_complete'=>false,
    'fractal_summary'=>'',
    'last_nugget'=>'',
    'closure_signal'=>'',
    'leadership_need'=>'open_next_vantage'
));
$GLOBALS['hrn_qa_composition_result'] = array(
    'response'=>'A conversation can hold two different risks at once: saying what matters may change the friendship, while staying silent can leave the same uncertainty in place. Those are not the same kind of change, even if both feel consequential.',
    'question'=>'',
    'rest'=>true,
    'use_resource'=>true,
    'resource_intro'=>''
);
$ordinaryRequest = new WP_REST_Request('POST', '/living-archive/v1/relational-navigator');
$ordinaryRequest->set_header('content-type','application/json');
$ordinaryRequest->set_param('message',$ordinaryMessage);
$ordinaryRequest->set_param('original_question',$ordinaryMessage);
$ordinaryRequest->set_param('conversation','');
$ordinaryRequest->set_param('full_conversation','');
$ordinaryRequest->set_param('session_id',$ordinarySession);
$ordinaryRequest->set_param('unit_turns',1);
$ordinaryRequest->set_param('safety_stage','green');
set_error_handler(static function ($severity, $message, $file, $line) {
    if (!(error_reporting() & $severity)) return false;
    if (in_array($severity, array(E_WARNING, E_NOTICE, E_USER_WARNING, E_USER_NOTICE), true)) {
        throw new ErrorException($message, 0, $severity, $file, $line);
    }
    return false;
});
$ordinaryResponse = rest_do_request($ordinaryRequest);
restore_error_handler();
$ordinaryStatus = $ordinaryResponse instanceof WP_REST_Response ? $ordinaryResponse->get_status() : 500;
$ordinaryData = $ordinaryResponse instanceof WP_REST_Response ? $ordinaryResponse->get_data() : array('error'=>$ordinaryResponse instanceof WP_Error ? $ordinaryResponse->get_error_message() : 'unknown');
$assert($ordinaryStatus === 200 && !empty($ordinaryData['ok']), 'ordinary missing-question route returns HTTP 200; got HTTP '.$ordinaryStatus.' '.wp_json_encode($ordinaryData));
$assert(trim((string)($ordinaryData['response'] ?? '')) !== '', 'ordinary missing-question route preserves provider-written response prose');
$assert(trim((string)($ordinaryData['question'] ?? '')) !== '', 'ordinary missing-question route structurally completes the question without another provider');
$assert(stripos((string)$ordinaryData['question'],'friendship') !== false || stripos((string)$ordinaryData['question'],'conversation') !== false, 'structural question remains grounded in the visitor’s named relationship');
$assert(empty($ordinaryData['rest']) && empty($ordinaryData['use_resource']), 'successful question completion clears default rest/resource flags');

$secondMessage = "I want the friendship to remain warm, but I don't want to keep pretending everything is fine.";
$GLOBALS['hrn_qa_observer'] = array_merge((array)$GLOBALS['hrn_qa_observer'], array(
    'observer_intention'=>'warmth and honesty in a friendship',
    'observer_contrast'=>'Keeping a friendship warm and pretending everything is fine are not the same thing.',
    'observer_so_what'=>'The wish for closeness can coexist with recognition that something feels unresolved.',
    'observer_delta'=>'Warmth and concealment are different parts of the relationship.',
    'observer_horizon'=>'what warmth means when something is unspoken',
    'observer_decision'=>'CONTINUE',
    'observer_next_intention'=>'examine the relationship between warmth and honesty',
    'situation'=>'wanting warmth without pretending everything is fine',
    'experience'=>$secondMessage,
    'tension'=>'warmth and honesty',
    'pattern'=>'keeping things warm may conflict with acknowledging what is not fine',
    'underlying_need'=>'connection and honesty',
    'desired_condition'=>'warmth without pretending',
    'emerging_delta'=>'warmth and concealment are different parts of the relationship',
    'perspective_delta'=>'warmth and concealment are different parts of the relationship',
    'body_of_thought'=>(string)$ordinaryData['response'],
    'current_fractal'=>'warmth and honesty in a friendship',
    'next_horizon'=>'what warmth means when something is unspoken',
    'conversation_purpose'=>'understand a difficult friendship',
    'movement_state'=>'exploring',
    'conversation_phase'=>'exploration',
    'fractal_stage'=>'exploration',
    'fractal_maturity'=>'maturing',
    'fractal_complete'=>false,
    'fractal_summary'=>'',
    'last_nugget'=>(string)$ordinaryData['response'],
    'closure_signal'=>'none',
    'leadership_need'=>'lead_forward'
));
$GLOBALS['hrn_qa_composition_result'] = array(
    'response'=>'Keeping the friendship warm and pretending everything is fine are not quite the same thing. One points to the closeness you want to preserve; the other can leave what is difficult between you unspoken, even while the friendship looks unchanged from the outside.',
    'question'=>'When you think about having this conversation, what part of the friendship feels most at risk of changing?',
    'rest'=>false,
    'use_resource'=>false,
    'resource_intro'=>''
);
$secondRequest = new WP_REST_Request('POST', '/living-archive/v1/relational-navigator');
$secondRequest->set_header('content-type','application/json');
$secondRequest->set_param('message',$secondMessage);
$secondRequest->set_param('original_question',$ordinaryMessage);
$secondRequest->set_param('conversation','Visitor: '.$ordinaryMessage."\nAssistant: ".(string)$ordinaryData['response']."\nAssistant: ".(string)$ordinaryData['question']);
$secondRequest->set_param('full_conversation','Visitor: '.$ordinaryMessage."\nAssistant: ".(string)$ordinaryData['response']."\nAssistant: ".(string)$ordinaryData['question']."\nVisitor: ".$secondMessage);
$secondRequest->set_param('session_id',$ordinarySession);
$secondRequest->set_param('unit_turns',2);
$secondRequest->set_param('safety_stage','green');
set_error_handler(static function ($severity, $message, $file, $line) {
    if (!(error_reporting() & $severity)) return false;
    if (in_array($severity, array(E_WARNING, E_NOTICE, E_USER_WARNING, E_USER_NOTICE), true)) {
        throw new ErrorException($message, 0, $severity, $file, $line);
    }
    return false;
});
$secondResponse = rest_do_request($secondRequest);
restore_error_handler();
$secondStatus = $secondResponse instanceof WP_REST_Response ? $secondResponse->get_status() : 500;
$secondData = $secondResponse instanceof WP_REST_Response ? $secondResponse->get_data() : array('error'=>$secondResponse instanceof WP_Error ? $secondResponse->get_error_message() : 'unknown');
$assert($secondStatus === 200 && !empty($secondData['ok']), 'second ordinary round succeeds when the visitor names warmth and concealment; got HTTP '.$secondStatus.' '.wp_json_encode($secondData));
$assert(trim((string)($secondData['response'] ?? '')) !== '', 'second ordinary round preserves the visitor-grounded response');
$assert(trim((string)($secondData['question'] ?? '')) !== '', 'second ordinary round recovers a follow-up question without provider retries');
$assert(stripos((string)$secondData['question'],'friendship') !== false && (stripos((string)$secondData['question'],'warm') !== false || stripos((string)$secondData['question'],'unspoken') !== false), 'second-round question remains grounded in the warmth/concealment tension');
$assert(stripos((string)$secondData['question'],'at risk of changing') === false && stripos((string)$secondData['question'],'afraid might change') === false, 'second-round question does not repeat the prior fear-of-change inquiry');
$assert(empty($secondData['rest']) && empty($secondData['use_resource']), 'second-round question keeps the ordinary conversation open');




unset($GLOBALS['hrn_qa_composition_result']);

$thirdMessage = "I think the hardest part is that she may think I'm blaming her, when really I want us to understand each other better.";
$GLOBALS['hrn_qa_observer'] = array_merge((array)$GLOBALS['hrn_qa_observer'], array(
    'observer_intention'=>'blame and mutual understanding',
    'observer_contrast'=>'Blame and mutual understanding are not the same thing; the first focuses on fault, while the second asks what each person is trying to communicate.',
    'observer_so_what'=>'That distinction matters because a person can name an effect without deciding that the other person intended harm.',
    'observer_delta'=>'The focus can shift from proving fault to understanding what the interaction has meant.',
    'observer_horizon'=>'what it means to be understood without assigning fault',
    'observer_decision'=>'CONTINUE',
    'observer_next_intention'=>'separate impact from blame',
    'situation'=>'fear of being heard as blaming while wanting mutual understanding',
    'experience'=>$thirdMessage,
    'tension'=>'blame and mutual understanding',
    'pattern'=>'an honest account may be heard as assigning fault',
    'underlying_need'=>'mutual understanding',
    'desired_condition'=>'honesty without blame',
    'emerging_delta'=>'naming an effect is not the same as assigning intention',
    'perspective_delta'=>'naming an effect is not the same as assigning intention',
    'body_of_thought'=>'',
    'current_fractal'=>'blame and mutual understanding',
    'next_horizon'=>'what it means to be understood without assigning fault',
    'conversation_purpose'=>'understand a difficult friendship',
    'movement_state'=>'exploring',
    'conversation_phase'=>'exploration',
    'fractal_stage'=>'exploration',
    'fractal_maturity'=>'maturing',
    'fractal_complete'=>false,
    'fractal_summary'=>'',
    'last_nugget'=>'',
    'closure_signal'=>'none',
    'leadership_need'=>'lead_forward'
));
$thirdRequest = new WP_REST_Request('POST', '/living-archive/v1/relational-navigator');
$thirdRequest->set_header('content-type','application/json');
$thirdRequest->set_param('message',$thirdMessage);
$thirdRequest->set_param('original_question',$ordinaryMessage);
$thirdRequest->set_param('conversation','Visitor: '.$ordinaryMessage."\nAssistant: ".(string)$ordinaryData['response']."\nAssistant: ".(string)$ordinaryData['question']."\nVisitor: ".$secondMessage."\nAssistant: ".(string)$secondData['response']."\nAssistant: ".(string)$secondData['question']);
$thirdRequest->set_param('full_conversation','Visitor: '.$ordinaryMessage."\nAssistant: ".(string)$ordinaryData['response']."\nAssistant: ".(string)$ordinaryData['question']."\nVisitor: ".$secondMessage."\nAssistant: ".(string)$secondData['response']."\nAssistant: ".(string)$secondData['question']."\nVisitor: ".$thirdMessage);
$thirdRequest->set_param('session_id',$ordinarySession);
$thirdRequest->set_param('unit_turns',3);
$thirdRequest->set_param('safety_stage','green');
set_error_handler(static function ($severity, $message, $file, $line) {
    if (!(error_reporting() & $severity)) return false;
    if (in_array($severity, array(E_WARNING, E_NOTICE, E_USER_WARNING, E_USER_NOTICE), true)) {
        throw new ErrorException($message, 0, $severity, $file, $line);
    }
    return false;
});
$thirdResponse = rest_do_request($thirdRequest);
restore_error_handler();
$thirdStatus = $thirdResponse instanceof WP_REST_Response ? $thirdResponse->get_status() : 500;
$thirdData = $thirdResponse instanceof WP_REST_Response ? $thirdResponse->get_data() : array('error'=>$thirdResponse instanceof WP_Error ? $thirdResponse->get_error_message() : 'unknown');
$assert($thirdStatus === 200 && !empty($thirdData['ok']), 'third ordinary round recovers from provider exhaustion using current Observer evidence; got HTTP '.$thirdStatus.' '.wp_json_encode($thirdData));
$assert(stripos((string)($thirdData['response'] ?? ''),'blame') !== false && stripos((string)($thirdData['response'] ?? ''),'understanding') !== false, 'third-round recovery uses current-turn Observer contrast rather than prior-turn summary');
$assert(trim((string)($thirdData['question'] ?? '')) !== '', 'third-round recovery supplies a grounded continuation question');
$assert(stripos((string)$thirdData['question'],'understand') !== false || stripos((string)$thirdData['question'],'blame') !== false, 'third-round question opens the blame/understanding perspective');
$assert(empty($thirdData['rest']) && empty($thirdData['use_resource']), 'third-round recovery keeps ordinary conversation open');

$GLOBALS['hrn_qa_observer'] = array_merge((array)$GLOBALS['hrn_qa_observer'], array(
    'observer_intention'=>'honesty and continuity in a friendship',
    'observer_contrast'=>'Honesty and continuity can both matter without guaranteeing a particular outcome.',
    'observer_so_what'=>'That distinction helps separate the conversation itself from assumptions about what it will mean for the friendship.',
    'observer_delta'=>'The conversation and the future of the friendship are not identical.',
    'observer_horizon'=>'the relationship between honesty and continuity',
    'observer_decision'=>'CONTINUE',
    'situation'=>'fear that an honest conversation might change a friendship',
    'experience'=>$ordinaryMessage,
    'tension'=>'honesty and continuity',
    'pattern'=>'fear of change is delaying a conversation',
    'underlying_need'=>'to be understood',
    'desired_condition'=>'honesty without assuming a particular outcome',
    'emerging_delta'=>'the conversation and the future of the friendship are distinct',
    'perspective_delta'=>'the conversation and the future of the friendship are distinct',
    'current_fractal'=>'honesty and continuity in a friendship',
    'next_horizon'=>'the relationship between honesty and continuity',
    'fractal_maturity'=>'immature',
    'fractal_complete'=>false,
    'closure_signal'=>'none',
    'leadership_need'=>'open_next_vantage'
));
$GLOBALS['hrn_qa_composition_result'] = array(
    'response'=>'A conversation can hold two different risks at once: saying what matters may change the friendship, while staying silent can leave the same uncertainty in place. Those are not the same kind of change, even if both feel consequential. What you have just uncovered connects with an idea in the Archive about the tension between connection and authenticity.',
    'question'=>'What part of the friendship are you most afraid might change if you have that conversation?',
    'rest'=>false,
    'use_resource'=>false,
    'resource_intro'=>''
);
$resourceMessage = 'I keep putting off a conversation with a friend because I am afraid it will change the friendship.';
$resourceRequest = new WP_REST_Request('POST', '/living-archive/v1/relational-navigator');
$resourceRequest->set_header('content-type','application/json');
$resourceRequest->set_param('message',$resourceMessage);
$resourceRequest->set_param('original_question',$resourceMessage);
$resourceRequest->set_param('conversation','');
$resourceRequest->set_param('full_conversation','');
$resourceRequest->set_param('session_id','hrn-isolated-unselected-resource-offer-v05315');
$resourceRequest->set_param('unit_turns',1);
$resourceRequest->set_param('safety_stage','green');
set_error_handler(static function ($severity, $message, $file, $line) {
    if (!(error_reporting() & $severity)) return false;
    if (in_array($severity, array(E_WARNING, E_NOTICE, E_USER_WARNING, E_USER_NOTICE), true)) {
        throw new ErrorException($message, 0, $severity, $file, $line);
    }
    return false;
});
$resourceResponse = rest_do_request($resourceRequest);
restore_error_handler();
$resourceStatus = $resourceResponse instanceof WP_REST_Response ? $resourceResponse->get_status() : 500;
$resourceData = $resourceResponse instanceof WP_REST_Response ? $resourceResponse->get_data() : array('error'=>$resourceResponse instanceof WP_Error ? $resourceResponse->get_error_message() : 'unknown');
$assert($resourceStatus === 200 && !empty($resourceData['ok']), 'unselected-resource route returns HTTP 200; got HTTP '.$resourceStatus.' '.wp_json_encode($resourceData));
$assert(stripos((string)($resourceData['response'] ?? ''),'archive') === false, 'unselected-resource route removes the unrendered Archive promise');
$assert(stripos((string)($resourceData['response'] ?? ''),'connects with an idea') === false, 'unselected-resource route removes only the offer sentence');
$assert(trim((string)($resourceData['question'] ?? '')) !== '', 'unselected-resource route retains the ordinary follow-up question');
$assert(empty($resourceData['resources']), 'no canonical resource is falsely returned when use_resource is false');
$GLOBALS['hrn_qa_observer'] = array_merge((array)$GLOBALS['hrn_qa_observer'], array(
    'observer_intention'=>'honesty and continuity in a friendship',
    'observer_contrast'=>'A conversation can affect a friendship, but it does not determine what the friendship will become.',
    'observer_so_what'=>'Silence also leaves questions about the friendship unresolved.',
    'observer_delta'=>'The conversation and the future of the friendship are not identical.',
    'observer_horizon'=>'the relationship between honesty and continuity',
    'observer_decision'=>'CONTINUE',
    'observer_next_intention'=>'separate the conversation from assumptions about the outcome',
    'situation'=>'fear that a conversation may change a friendship',
    'experience'=>$resourceMessage,
    'tension'=>'honesty and continuity',
    'pattern'=>'fear of change is delaying a conversation',
    'underlying_need'=>'to be understood',
    'desired_condition'=>'honesty without assuming a particular outcome',
    'emerging_delta'=>'the conversation and the future of the friendship are distinct',
    'perspective_delta'=>'the conversation and the future of the friendship are distinct',
    'body_of_thought'=>'A conversation can affect a friendship, but it does not determine what the friendship will become. Silence also leaves questions about the friendship unresolved.',
    'current_fractal'=>'honesty and continuity in a friendship',
    'last_nugget'=>'the conversation and the future of the friendship are not identical',
    'next_horizon'=>'the relationship between honesty and continuity',
    'fractal_maturity'=>'maturing',
    'fractal_complete'=>false,
    'closure_signal'=>'none',
    'leadership_need'=>'lead_forward'
));
$GLOBALS['hrn_qa_composition_result'] = array(
    'response'=>'The hesitation to speak suggests that the friendship is already experiencing a shift, even if the conversation has not happened yet. Recognizing that the status quo is not fixed makes it possible to decide whether you want to guide that change or simply watch it happen.',
    'question'=>'What part of the friendship are you most afraid might change if you have that conversation?',
    'rest'=>false,
    'use_resource'=>false,
    'resource_intro'=>''
);
$policyRequest = new WP_REST_Request('POST', '/living-archive/v1/relational-navigator');
$policyRequest->set_header('content-type','application/json');
$policyRequest->set_param('message',$resourceMessage);
$policyRequest->set_param('original_question',$resourceMessage);
$policyRequest->set_param('conversation','');
$policyRequest->set_param('full_conversation','');
$policyRequest->set_param('session_id','hrn-isolated-soft-action-frame-v05315');
$policyRequest->set_param('unit_turns',1);
$policyRequest->set_param('safety_stage','green');
// Preserve the request payload across WordPress REST server reuse. Some WP test
// runs leave the request parameter-order map changed after a previous dispatch.
$policyRequest->set_body_params(array(
    'message'=>$resourceMessage,
    'original_question'=>$resourceMessage,
    'conversation'=>'',
    'full_conversation'=>'',
    'session_id'=>'hrn-isolated-soft-action-frame-v05315',
    'unit_turns'=>1,
    'safety_stage'=>'green'
));

$assert($policyRequest->get_param('message') === $resourceMessage, 'soft-action-frame request retains its message before REST dispatch');
set_error_handler(static function ($severity, $message, $file, $line) {
    if (!(error_reporting() & $severity)) return false;
    if (in_array($severity, array(E_WARNING, E_NOTICE, E_USER_WARNING, E_USER_NOTICE), true)) {
        throw new ErrorException($message, 0, $severity, $file, $line);
    }
    return false;
});
$policyResponse = rest_do_request($policyRequest);
restore_error_handler();
$policyStatus = $policyResponse instanceof WP_REST_Response ? $policyResponse->get_status() : 500;
$policyData = $policyResponse instanceof WP_REST_Response ? $policyResponse->get_data() : array('error'=>$policyResponse instanceof WP_Error ? $policyResponse->get_error_message() : 'unknown');
$assert($policyStatus === 503 && empty($policyData['ok']), 'soft-action-frame route fails closed when the deterministic writer can only repeat rejected prose; got HTTP '.$policyStatus.' '.wp_json_encode($policyData));
$policyEnvelope = wp_json_encode($policyData);
$assert(stripos((string)$policyEnvelope,'makes it possible') === false && stripos((string)$policyEnvelope,'guide that change') === false && stripos((string)$policyEnvelope,'watch it happen') === false, 'soft-action-frame text never leaks into the visitor-facing failure envelope');
$assert(($policyData['reason'] ?? '') === 'composition_policy_rejected', 'soft-action-frame failure identifies the policy boundary without exposing rejected prose');
unset($GLOBALS['hrn_qa_composition_result']);



echo "HRN ISOLATED REST ROUTE INTEGRATION: PASS\n";
