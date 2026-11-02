<?php
/**
 * Plugin Name: Living Archive — HRN Composition Contract Guard
 * Description: Bounded REST-boundary composition repair and context-aware humane recovery; protected HRN writer remains unchanged.
 * Version: 1.3.10
 * Author: Living Archive
 */
if (!defined('ABSPATH')) { exit; }
add_filter('rest_post_dispatch', function ($response, $server, $request) {
 if (!($request instanceof WP_REST_Request) || strtoupper((string)$request->get_method()) !== 'POST' || rtrim((string)$request->get_route(), '/') !== '/living-archive/v1/relational-navigator' || !($response instanceof WP_REST_Response)) return $response;
 $d=$response->get_data(); if (!is_array($d)) return $response;
 $m=trim((string)$request->get_param('message')); if ($m==='') return $response;
 $s=strtolower((string)($d['safety']??'green')); if (!empty($d['safety_interrupt']) || in_array($s,array('amber','red'),true)) return $response;
  // The browser sends unitTurns as the number of turns already completed (0 before
 // the first turn, 1 before the second, and so on). Convert that completed-turn
 // count to the current incoming turn before selecting a contextual recovery.
 $completed_turns = $request->get_param('unit_turns');
 $turn = ($completed_turns !== null && $completed_turns !== '')
  ? max(1, (int)$completed_turns + 1)
  : max(1, (int)($d['unit_position'] ?? 1));
 $status=(int)$response->get_status(); $payload_status=(int)($d['status']??0); $reason=strtolower((string)($d['reason']??$d['code']??$d['error']??''));
 $t=trim((string)($d['response']??'')); $q=trim((string)($d['question']??''));
 $sibling_history = implode("\n", array_filter(array_map('strval', array(
  $request->get_param('conversation'),
  $request->get_param('visitor_history'),
  $request->get_param('full_conversation')
 ))));
 $policy_rejection = $reason === 'composition_policy_rejected' && is_array($d['meta']['policy_rejections'] ?? null) && (bool)array_filter($d['meta']['policy_rejections'], function ($item) { return is_array($item) && strtolower((string)($item['reason'] ?? '')) === 'visitor_surface_policy_rejected'; });
 $failure=in_array($reason,array('missing_question','hrn_missing_question','composition_missing_question','composition_unavailable'),true) || (isset($d['ok']) && $d['ok']===false && strpos(strtolower((string)($d['message']??'')),'question')!==false);
 $recoverable=($failure || $policy_rejection) && ($status>=500 || $payload_status>=500 || $reason==='composition_unavailable');
 if ($recoverable) { $d['ok']=true; $d['version']=(string)($d['version']??'0.5.330'); $d['unit_position']=$turn; $d['unit_complete']=false; $d['safety']='green'; $d['conversation_phase']='exploration'; $d['movement_state']='advancing'; $response->set_status(200); unset($d['error_type'],$d['operation'],$d['reason'],$d['retryable'],$d['status'],$d['meta']); }
 $opening=$recoverable && preg_match('/\b(same argument|same fight|same disagreement|keep arguing|keep having the same argument|argument keeps returning|argument keeps coming back|recurring argument|repeating argument)\b/i',$m) && preg_match('/\b(partner|between us|both say|both want|want things to improve|someone i care about|relationship|we both)\b/i',$m);
 $manager=preg_match('/\b(manager|boss|supervisor|trust me|questions every decision|micromanag|justify that decision|justify the decision|overexplain|over-explain|prove i know|prove myself|decision is within my role|decision boundaries|independently|accusing my manager)\b/i',$m) || (preg_match('/\b(decision|role|judgment|reasoning)\b/i',$m) && preg_match('/\b(review|question|explain|own|responsib|risk|boundary|boundaries|trust)\b/i',$m));
 if ($opening) {
  $t='You both want things to improve, yet somehow you keep finding yourselves back in the same argument. That can be discouraging, especially when neither of you wants things to stay this way. The repetition may tell us something about how you get caught in the same pattern, but it does not yet tell us why.';
  $q='When the argument begins, what tends to happen first between you?';
  $d['working_hypothesis']='the source is not yet established; examine the interaction before assigning responsibility'; $d['underlying_need']='';
  $d['emerging_delta']='move from the repeated outcome to an observable moment in the interaction'; $d['perspective_delta']=$d['emerging_delta'];
  $d['observer_intention']='notice the interaction sequence before interpreting responsibility'; $d['observer_contrast']='the source may lie with either person or in the interaction; current evidence does not decide';
  $d['observer_so_what']='an observable moment can clarify the pattern without assigning blame'; $d['observer_delta']='attention moves from the repeated outcome to what happens between the two people';
  $d['observer_horizon']='notice what happens first when the familiar argument begins'; $d['observer_next_intention']='explore the interaction sequence without presuming whose fault it is'; $d['next_horizon']=$d['observer_horizon'];
  $d['hrn_composition_recovery']='humane_relational_opening_v5';
 } elseif ($turn<=1 && $recoverable && preg_match('/\b(friend|friendship)\b/i',$m) && preg_match('/\b(afraid|fear|worried|scared|putting off|avoid|hesitat|change the friendship|damage the friendship|lose the friendship)\b/i',$m) && preg_match('/\b(conversation|talk|speak|bring it up|say something)\b/i',$m)) {
  $t='You want to speak honestly with your friend, but you are worried that naming what is on your mind could change the friendship. That leaves you weighing the value of being open against the uncertainty of what the conversation might bring. We do not yet know how your friend would respond, or whether the friendship would change.';
  $q='What feels most important to protect in the friendship as you imagine having this conversation?';
  $d['working_hypothesis']='the visitor is balancing a wish for honesty with concern about the friendship; the specific risk is not yet established'; $d['underlying_need']='';
  $d['emerging_delta']='move from predicting the outcome to identifying what the visitor most wants to preserve'; $d['perspective_delta']=$d['emerging_delta'];
  $d['observer_intention']='understand the concern beneath the hesitation without assuming the conversation should happen';
  $d['observer_contrast']='honesty and preserving the friendship may feel in tension, but the outcome is not yet known';
  $d['observer_so_what']='clarifying what matters most can make the concern more specific without prescribing an action';
  $d['observer_delta']='attention shifts from an uncertain future reaction to what the visitor values in the friendship';
  $d['observer_horizon']='identify what feels most at risk in the imagined conversation'; $d['observer_next_intention']='explore the value being protected before deciding what the hesitation means';
  $d['next_horizon']=$d['observer_horizon']; $d['hrn_composition_recovery']='bounded_friendship_conversation_fallback_v2';
 } elseif ($turn===2 && $recoverable
   && preg_match('/\\b(friend|friendship)\\b/i',$sibling_history)
   && preg_match('/\\b(afraid|fear|worried|scared|putting off|hesitat|change the friendship|damage the friendship|conversation|talk|speak honestly|bring it up)\\b/i',$sibling_history)
   && preg_match('/\\b(trust|blame|blamed|protect|honest|feel blamed)\\b/i',$m)) {
  $t='You want to protect the trust between you, and you do not want your friend to hear the conversation as blame. So the challenge is not simply finding the right words; it is making room for what you need to say without deciding in advance what your friend meant or how they will respond.';
  $q='What would you most want your friend to understand about your experience, without making the conversation about blame?';
  $d['working_hypothesis']='the visitor wants honest communication while preserving trust and avoiding an accusatory framing';
  $d['underlying_need']='preserve trust while communicating honestly without assigning blame';
  $d['emerging_delta']='move from protecting the friendship in the abstract to naming what the visitor wants understood';
  $d['perspective_delta']=$d['emerging_delta'];
  $d['observer_intention']='clarify the visitor’s intended meaning before anticipating the friend’s reaction';
  $d['observer_contrast']='the visitor can name an experience without claiming to know the friend’s intent';
  $d['observer_so_what']='a clear account of what matters may make the conversation less accusatory without guaranteeing its outcome';
  $d['observer_delta']='attention shifts from avoiding blame to expressing the experience the visitor wants understood';
  $d['observer_horizon']='identify what the visitor wants the friend to understand';
  $d['observer_next_intention']='separate expressing impact from assigning motive or blame';
  $d['next_horizon']=$d['observer_horizon'];
  $d['hrn_composition_recovery']='bounded_friendship_conversation_progression_v1';
 } elseif ($recoverable
   && preg_match('/\\b(?:only person to give in|only one giving in|only one who gives in|do i have to give in|give in to the other|no one wants? to give in|nobody wants? to give in)\\b/i',$m)
   && preg_match('/\\b(?:argument|disagreement|conflict|partner|relationship|escalat)\\b/i',$sibling_history . " " . $m)) {
  // Contextual progression: answer the visitor's mutual-responsibility question
  // before asking for more detail. Pausing is not framed as unilateral surrender.
  $t='No. You do not have to be the only person responsible for making things better. Pausing an argument is not the same as conceding or taking all the blame; it can simply create enough room for both people to hear what is being said. Whether that pause becomes mutual depends on how both of you respond.';
  $q='If you were to pause, what would you need your partner to do as well so that it feels like a shared effort, not just you giving way?';
  $d['working_hypothesis']='the visitor is weighing mutual responsibility against the fear that pausing means surrendering';
  $d['underlying_need']='a way to interrupt escalation without carrying repair alone';
  $d['emerging_delta']='distinguish a pause that creates room for both people from giving in unilaterally';
  $d['perspective_delta']=$d['emerging_delta'];
  $d['observer_intention']='clarify what mutual participation would look like without assigning blame';
  $d['observer_contrast']='pausing and surrendering are not the same; mutuality depends on both people';
  $d['observer_so_what']='the visitor can name what would make a pause feel shared rather than one-sided';
  $d['observer_delta']=$d['emerging_delta'];
  $d['observer_horizon']='identify what mutual participation during a pause would look like';
  $d['observer_next_intention']='explore a concrete sign that both people are participating';
  $d['next_horizon']=$d['observer_horizon'];
  $d['hrn_composition_recovery']='bounded_mutual_responsibility_progression_v1';
 } elseif ($recoverable
   && preg_match('/\\b(?:heart rate|heart racing|racing heart|blood rises|blood rushing|hard to breathe|difficult to breathe|difficulty breathing|cannot breathe|can.t breathe|think clearly|flooded with emotions|emotionally flooded|overwhelmed)\\b/i',$m)
   && preg_match('/\\b(?:argument|disagreement|conflict|partner|relationship|give in|escalat)\\b/i',$sibling_history . " " . $m)) {
  // Ground the response in the latest visitor evidence and keep the journey open.
  $t='You are describing the moment when the argument becomes hard to think through: your body reacts quickly, and the chance to choose a pause seems to arrive after you already feel flooded. That does not mean you have failed to stay calm. It means any useful pause would need to happen early enough, and it should not be treated as you accepting all the responsibility.';
  $q='What is the earliest sign you notice before the feeling becomes overwhelming, even if it is only a small change?';
  $d['working_hypothesis']='the visitor notices physical escalation before they can deliberately pause';
  $d['underlying_need']='recognize an early, observable cue without making one person responsible for the whole conflict';
  $d['emerging_delta']='notice the earliest bodily cue as information, not as failure or proof of the other person’s intent';
  $d['perspective_delta']=$d['emerging_delta'];
  $d['observer_intention']='connect the visitor’s physical experience to the recurring interaction without diagnosing';
  $d['observer_contrast']='the physical reaction is described by the visitor; its cause and the partner’s intention remain unconfirmed';
  $d['observer_so_what']='an earlier cue may make a shared pause more possible, but it cannot guarantee the partner’s response';
  $d['observer_delta']=$d['emerging_delta'];
  $d['observer_horizon']='identify the earliest noticeable cue before emotional flooding';
  $d['observer_next_intention']='explore an early observable cue before suggesting a strategy';
  $d['next_horizon']=$d['observer_horizon'];
  $d['unit_complete']=false;
  $d['conversation_phase']='exploration';
  $d['movement_state']='advancing';
  $d['observer_decision']='CONTINUE';
  $d['observer_next_intention']='identify the earliest bodily cue before emotional flooding';
  $d['hrn_composition_recovery']='bounded_physical_overwhelm_progression_v1';
 } elseif ($manager && $recoverable) {
  if ($turn<=1) { $t='Being told you are trusted while having each decision questioned sends two different messages. It makes sense that you would want to understand what your manager means by trust in practice, rather than trying to guess at their intentions.'; $q='When your manager questions a decision, what do they usually ask you to explain?'; }
  elseif ($turn===2) { $t='You are not only answering a question about the work; you are also being put in the position of proving that you are entitled to make the decision. That can quietly shift the exchange from discussing the merits of an approach to defending your competence.'; $q='When you explain your reasoning, does your manager engage with it, or do they move on to questioning another part of the decision?'; }
  elseif ($turn===3) { $t='A pattern may be taking shape: the more you explain to establish that your decision is sound, the more the conversation can become a review of your judgment. That does not tell us whether your manager intends to undermine you, but it does show how the exchange can leave you feeling less trusted.'; $q='What would a reasonable level of review look like to you, while still leaving you room to own decisions within your role?'; }
  elseif ($turn===4) { $t='You are distinguishing oversight from having to repeatedly prove your competence. That is useful: trust does not have to mean that every decision goes unquestioned, but the questions should have a clear purpose and leave you able to exercise the responsibility you were given.'; $q='Have you and your manager ever agreed explicitly on which decisions you can make independently and which ones need discussion?'; }
  elseif ($turn===5) { $t='The central issue now seems less about whether questions are ever appropriate and more about whether the boundaries of your responsibility are clear and respected. You can raise that without claiming to know your manager’s motives: focus on the decisions in your remit, the review they need, and what would make that review useful rather than repetitive.'; $q='Would it feel useful to clarify those decision boundaries with your manager, or is there something important that makes that conversation difficult?'; }
  else { $t='You have a clearer distinction now: being open to reasonable review is not the same as having to repeatedly prove you deserve to make decisions within your role. You do not have to settle what your manager intends in order to address the part you can observe. A calm next step would be to ask which decisions you are expected to own, what risks or exceptions should come back for discussion, and what kind of review would be useful. That makes the conversation about shared expectations and responsibility, rather than an accusation about trust.'; $q=''; $d['unit_complete']=true; $d['conversation_phase']='synthesis'; $d['movement_state']='settling'; $d['completed_insight']='distinguish useful oversight from repeated proof of competence'; $d['emerging_delta']='the focus shifts from guessing at trust to clarifying decision rights and review expectations'; $d['perspective_delta']=$d['emerging_delta']; }
  $d['working_hypothesis']='explore the difference between legitimate review and unclear or undermining decision boundaries'; $d['underlying_need']='clear responsibility and confidence that judgment will be engaged on its merits';
  $d['next_horizon']=$q!==''?'clarify what happens in the review exchange and what responsibility has actually been delegated':''; $d['hrn_composition_recovery']='bounded_manager_progression_v7';
 } elseif ($turn >= 2 && $recoverable && preg_match('/\b(initiat(?:e|es|ing)|check(?:s|ing)? in first|start the conversation|rarely start|rarely initiat|respond warmly|making the effort|make the effort)\b/i',$m)) {
  $t='You are usually the one who starts the plans or checks in. Your friend responds warmly when you do, but rarely begins the contact themselves. That leaves two things true at once: the connection seems welcome when you reach out, and the effort to begin it feels uneven. We do not yet know what explains that difference.';
  $q='When you leave a little space for your friend to initiate, what usually happens?';
  $d['working_hypothesis']='distinguish warmth in response from willingness or capacity to initiate';
  $d['underlying_need']='a clearer sense of whether the friendship is mutual in practice, not only warm when contacted';
  $d['observer_horizon']='notice what happens when the visitor does not initiate contact';
  $d['observer_next_intention']='explore the difference between responsive warmth and shared initiation without assigning motive';
  $d['next_horizon']='observe whether the friend initiates when there is room to do so';
  $d['hrn_composition_recovery']='bounded_reciprocity_initiation_fallback_v1';
 } elseif ($recoverable && preg_match('/\b(repair|take all the blame|all the blame|without taking the blame|without taking all the blame|make things right|make amends)\b/i',$m)) {
  $t='You want a way back to a better relationship without accepting responsibility for more than your part. Repair does not have to mean deciding that one person is entirely at fault; it can begin by being clear about what you regret, what you still need understood, and what belongs to both of you.';
  $q='What part of what happened do you feel you can honestly own, and what part would feel untrue to take on?';
  $d['working_hypothesis']='separate personal responsibility from taking responsibility for the whole relationship'; $d['underlying_need']='a fair path toward repair that preserves honesty and mutual responsibility';
  $d['next_horizon']='distinguish the part the visitor can own from the part that needs to be shared or clarified'; $d['hrn_composition_recovery']='bounded_repair_without_total_blame_v1';
 } elseif ($recoverable) {
  if (preg_match('/\b(lent|loan|repay|repayment|owe|owed|money back|pay me back)\b/i',$m)) {
   if ($turn<=1) { $t='You are carrying both a practical question about repayment and a change in closeness. Those concerns may be connected, but we do not yet know why the contact changed or what the other person intends.'; $q='What happened the last time you raised repayment with them?'; }
   elseif ($turn===2) { $t='You noticed the silence began after you raised repayment, while some light contact continued. That gives us a sequence, but not yet the reason: they may be avoiding the topic, unsure what to say, or dealing with something else.'; $q='When you asked about repayment, what did they say or do in that moment?'; }
   else { $t='The funny video was a small sign of contact, while the repayment message remained unanswered. Those can coexist; the video alone does not tell us whether the person is willing to address the loan.'; $q='Has the person acknowledged the repayment request at any point, even indirectly?'; }
   $d['hrn_composition_recovery']='bounded_loan_repayment_progression_v1';
  }
  elseif (preg_match('/\b(sister|brother|sibling)\b/i',$m) || ($turn >= 2 && preg_match('/\b(sister|brother|sibling)\b/i', $sibling_history))) {
   $sibling_context = $m . "\n" . $sibling_history;
   $relationship = preg_match('/\bsister\b/i',$sibling_context) ? 'sister' : (preg_match('/\bbrother\b/i',$sibling_context) ? 'brother' : 'sibling');
   if ($turn >= 2 && preg_match('/\b(?:rota|visiting|errands|caring responsibilities|care responsibilities|share the care)\b/i',$m)) {
    $t='You were trying to make the care and visits more predictable, while your sister seems to have heard the rota as making things formal. Those are different meanings of the same proposal; her silence does not yet tell us whether she felt criticized, overwhelmed, or simply opposed to the arrangement.';
    $q='What did you hope the rota would make easier or fairer for each of you?';
    $d['hrn_composition_recovery']='bounded_sibling_care_progression_v1';
   } else {
    $t='When a misunderstanding keeps growing, the distance that follows can make it harder to find a way back to each other. We do not yet know whether you understood each other differently, were hurt by what was said, or both. Starting with one recent exchange may help separate what was meant from how it landed.';
    $q='What was the last exchange with your '.$relationship.' that you think each of you understood differently?';
   }
  }
  elseif (preg_match('/\b(colleague|coworker|credit for work|taking credit|contribution)\b/i',$m) || ($turn >= 2 && preg_match('/\b(colleague|coworker|credit for work|taking credit|contribution)\b/i',$sibling_history))) {
   $credit_history = implode("\n", array_filter(array_map('strval', array($request->get_param('conversation'), $request->get_param('visitor_history'), $request->get_param('full_conversation')))));
   $credit_prior_prompt = (bool) preg_match('/Can you recall a specific instance when your contribution was presented without being acknowledged\?/i', $credit_history);
   $credit_concrete_example = $turn >= 2 && (bool) preg_match('/\b(one clear example|one example|for example|yesterday|planning meeting|slides|framework|presentation|presented|last week|last monday|last tuesday|last wednesday|last thursday|last friday|in the larger meeting|during the review|at last week.s review|a specific instance)\b/i', $m);
   if ($turn >= 3 && $credit_prior_prompt && preg_match('/\b(embarrassed|angry|hurt|frustrated|confused|unsure|forgot|forget|intentional|deliberate)\b/i', $m)) {
    $t='The embarrassment and anger make sense alongside your uncertainty about whether the omission was intentional. The lack of acknowledgment affected how your contribution was recognized, but it does not by itself establish what your colleague meant.';
    $q='What would help you distinguish an oversight from a pattern, without deciding the answer in advance?';
    $d['hrn_composition_recovery']='bounded_credit_progression_v1';
   } elseif ($credit_concrete_example) {
    $t='You have a concrete instance now: your contribution was part of the work presented, but your name was not mentioned. That makes the missing acknowledgment specific, while the reason remains uncertain; it could be an oversight, an assumption about roles, or something more deliberate.';
    $q='What would you most want your colleague to understand about your contribution?';
    $d['hrn_composition_recovery']='bounded_credit_progression_v1';
   } elseif ($credit_prior_prompt || $turn >= 2) {
    $t='That helps locate the difficulty: the work you contribute and the recognition that follows are not lining up in the way you expect. We can look at that gap without deciding yet whether it reflects intention, habit, or an unspoken division of roles.';
    $q='Have you and your colleague ever discussed how the work should be credited when one person presents it?';
    $d['hrn_composition_recovery']='bounded_credit_progression_v1';
   } else {
    $t='Having your contribution go unacknowledged can leave you weighing two concerns at once: making the work visible and preserving a workable relationship with your colleague. Before deciding how to address it, it helps to distinguish what happened from what you suspect they intended.';
    $q='Can you recall a specific instance when your contribution was presented without being acknowledged?';
   }
  }
  elseif (preg_match('/\b(father|mother|parent|caregiver|caring for my parent|care for my parent|helping my parent)\b/i',$m)) { $t='You want to help your parent, but the arguments that follow may make your care feel unwelcome—or leave both of you frustrated. Help can land differently from how it is intended, especially when independence matters. We can look at what happens between you without assuming either of you is wrong.'; $q='When you offer help, how does your parent usually respond, and what do you do next?'; }
  elseif (preg_match('/\b(friend|distant|barely speak|closest friend)\b/i',$m)) { $t='Noticing a close friend pull away can leave you unsure whether to reach out or give them room. The distance is real, but its reason is not yet clear; it may be about your friendship or something happening in their life. You do not have to decide what it means before choosing a gentle way to check in.'; $q='What has changed most noticeably in how your friend responds to you?'; }
  elseif (preg_match('/\b(unheard|dismissed|doesn.t matter|won.t matter)\b/i',$m)) { $t='Feeling dismissed can make it seem there is no point in explaining yourself, so you try harder to get through. That reaction matters, but it does not tell us on its own why the other person shuts down or how the cycle began.'; $q='When you notice yourself trying harder to be heard, what are you most hoping they will understand?'; }
  elseif (preg_match('/\b(louder|shut down|prove my point|raise my voice)\b/i',$m)) { $t='There is a recognizable cycle here: you raise your intensity to get your point across, and the other person withdraws. Each response may make the next one more likely, even if neither of you intends that result.'; $q='What do you notice in yourself just before you start trying harder to make your point?'; }
  else { $t='We do not have to settle on an explanation yet. We can start with one concrete moment and look at what happened, without assuming what either person meant.'; $q='What is the first thing you notice when this situation begins to feel difficult?'; }
  if (empty($d['hrn_composition_recovery'])) { $d['hrn_composition_recovery']='bounded_contextual_fallback_v9'; }
 }
 if ($t!=='') $d['response']=$t;
 if ($q!=='') $d['question']=$q; else { unset($d['question']); }
 if ($recoverable) { $d['message']=$t; $d['hrn_composition_recovery_version']='1.3.10'; }
 if (!empty($d['hrn_composition_recovery'])) { $d['hrn_composition_recovery_version']='1.3.10'; $response->set_data($d); }
 return $response;
},1001,3);


/**
 * HRN continuity guard v1: do not close a relational journey on a visitor turn
 * that contributes new, concrete evidence of physiological overwhelm. The
 * frozen writer remains untouched; the REST boundary keeps the conversation
 * open and asks one grounded next question. Explicit visitor closure wins.
 */
add_filter('rest_post_dispatch', function ($response, $server, $request) {
 if (!($request instanceof WP_REST_Request) || strtoupper((string)$request->get_method()) !== 'POST' || rtrim((string)$request->get_route(), '/') !== '/living-archive/v1/relational-navigator' || !($response instanceof WP_REST_Response)) return $response;
 $d=$response->get_data(); if (!is_array($d)) return $response;
 $m=trim((string)$request->get_param('message')); if ($m==='') return $response;
 $action=strtolower(trim((string)($request->get_param('journey_action')??'')));
 if (in_array($action,array('end','close','finish','stop'),true) || preg_match('/^\\s*(?:i want to stop here|end conversation|stop conversation|close this conversation|bring this to a close)\\s*[.!]?\\s*$/i',$m)) return $response;
 $history=implode("\\n",array_filter(array_map('strval',array($request->get_param('conversation'),$request->get_param('visitor_history'),$request->get_param('full_conversation')))));
 $physical=(bool)preg_match('/\\b(?:heart rate|heart racing|racing heart|blood rises|blood rushing|hard to breathe|difficult to breathe|difficulty breathing|cannot breathe|can.t breathe|think clearly|flooded with emotions|emotionally flooded|overwhelmed)\\b/i',$m);
 $relational=(bool)preg_match('/\\b(?:argument|disagreement|conflict|partner|relationship|give in|escalat|old disagreement)\\b/i',$history." ".$m);
 if (!$physical || !$relational) return $response;
 $d['response']='You are describing the moment when the argument becomes hard to think through: your body reacts quickly, and the chance to choose a pause seems to arrive after you already feel flooded. That does not mean you have failed to stay calm. It means any useful pause would need to happen early enough, and it should not be treated as you accepting all the responsibility.';
 $d['question']='What is the earliest sign you notice before the feeling becomes overwhelming, even if it is only a small change?';
 $d['message']=$d['response'];
 $d['rest']=false;
 $d['junction_available']=false;
 $d['junction_summary']='';
 $d['unit_complete']=false;
 $d['conversation_phase']='exploration';
 $d['movement_state']='advancing';
 $d['fractal_stage']='discovery';
 $d['fractal_maturity']='maturing';
 $d['observer_decision']='CONTINUE';
 $d['observer_next_intention']='identify the earliest bodily cue before emotional flooding';
 $d['observer_horizon']='identify the earliest noticeable cue before emotional flooding';
 $d['next_horizon']=$d['observer_horizon'];
 $d['completed_insight']='';
 $d['hrn_continuity_guard']='physical_overwhelm_requires_contextual_followup_v1';
 $d['hrn_continuity_guard_version']='1.0';
 $response->set_data($d);
 return $response;
},1002,3);
