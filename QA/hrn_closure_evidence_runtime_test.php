<?php
/**
 * Exercise the actual HRN candidate closure methods without activating or
 * replacing the production WordPress plugin. This checks the local closure
 * fallback and its evidence/boundedness gates as a connected operation.
 */
$sourcePath = __DIR__ . '/../wordpress/hrn/human-relational-navigator.php';
$source = file_get_contents($sourcePath);
if (!is_string($source) || $source === '') {
    fwrite(STDERR, "Unable to read HRN candidate source.\n");
    exit(1);
}

function extract_hrn_private_method($source, $name) {
    $signature = 'private function ' . $name . '(';
    $start = strpos($source, $signature);
    if ($start === false) return false;
    $searchFrom = $start + strlen($signature);
    $ends = array();
    foreach (array("\n    private function ", "\n    public function ") as $marker) {
        $end = strpos($source, $marker, $searchFrom);
        if ($end !== false) $ends[] = $end;
    }
    if (empty($ends)) return false;
    $end = min($ends);
    if ($end <= $start) return false;
    return substr($source, $start, $end - $start);
}

$requiredMethods = array(
    'local_grounded_closure_synthesis',
    'provider_independent_terminal_closure',
    'closure_synthesis_carries_journey_evidence',
    'closure_synthesis_is_bounded',
    'humanity_gate',
    'recover_natural_landing_response',
);
$methods = array();
foreach ($requiredMethods as $name) {
    $method = extract_hrn_private_method($source, $name);
    if (!is_string($method) || $method === '') {
        fwrite(STDERR, "Unable to isolate HRN candidate method: " . $name . "\n");
        exit(1);
    }
    $methods[] = $method;
}

if (!function_exists('wp_json_encode')) { function wp_json_encode($value, $flags = 0) { return json_encode($value, $flags); } }
if (!function_exists('wp_strip_all_tags')) {
    function wp_strip_all_tags($value) { return strip_tags((string)$value); }
}

// Policy stubs deliberately accept ordinary visitor-safe text. The real
// candidate humanity_gate and closure bounds/evidence methods still execute.
$stubs = <<<'PHP'
private function prescriptive_response_violation($text) { return array('blocked' => false); }
private function relational_grounding_violation($text) { return array('blocked' => false); }
private function visitor_surface_language_violation($text) { return array('blocked' => false); }
private function normalize_visitor_surface_language($text) { return trim((string)$text); }
private function bounded_context_text($text, $limit, $sentence_boundary = false) {
    return substr((string)$text, 0, max(0, (int)$limit));
}
PHP;

eval('class HRNClosureEvidenceHarness { ' . $stubs . ' ' . implode("\n", $methods) . ' }');
$harness = new HRNClosureEvidenceHarness();

function invoke_hrn_private($object, $methodName, $arguments) {
    $reflection = new ReflectionMethod($object, $methodName);
    $reflection->setAccessible(true);
    return $reflection->invokeArgs($object, $arguments);
}

$assert = function ($expected, $actual, $label) {
    if ($actual !== $expected) {
        fwrite(STDERR, $label . ': expected ' . var_export($expected, true) . ', got ' . var_export($actual, true) . "\n");
        exit(1);
    }
    echo "PASS: " . $label . "\n";
};

// Exact closure message that reproduced the live v0.5.277 spiral_landing 503.
$earned = "I can see that I may be treating being understood and protecting myself as opposites, when both can matter. Please synthesize what we have learned and close the conversation.";
$aligned = "Being understood and protecting yourself do not have to be opposites. Both can matter, and one does not establish the other person's intentions.";
$generic = "The conversation has clarified a distinction in the experience, while leaving its uncertain parts unclaimed.";
$bareCommand = "Please synthesize what we have learned and close the conversation.";

$assert(true, invoke_hrn_private($harness, 'closure_synthesis_carries_journey_evidence', array($aligned, array('closure_message' => $earned))), 'visitor insight survives closure-command stripping');
$assert(false, invoke_hrn_private($harness, 'closure_synthesis_carries_journey_evidence', array($generic, array('closure_message' => $earned))), 'generic synthesis cannot pass on visitor statement alone');
$assert(false, invoke_hrn_private($harness, 'closure_synthesis_carries_journey_evidence', array($generic, array('closure_message' => $bareCommand))), 'bare closure command is not journey evidence');
$assert(false, invoke_hrn_private($harness, 'closure_synthesis_carries_journey_evidence', array($generic, array('closure_message' => 'Please synthesize what we discussed.'))), 'bare synthesis request is not journey evidence');
$assert(false, invoke_hrn_private($harness, 'closure_synthesis_carries_journey_evidence', array($generic, array('closure_message' => 'I have reached enough for now.'))), 'bare stop command is not journey evidence');
$assert(true, invoke_hrn_private($harness, 'closure_synthesis_carries_journey_evidence', array(
    'The silence does not establish rejection; that feeling does not prove the other person’s intention.',
    array('perspective_delta' => 'Silence alone does not establish rejection, even when uncertainty feels uncomfortable.')
)), 'existing ledger evidence path remains intact');

// Exercise the natural-junction recovery helper itself, not only its source contract.
$naturalLandingState = array(
    'conversation' => '',
    'completed_insight' => 'Silence alone does not establish rejection, even when uncertainty feels uncomfortable.',
    'perspective_delta' => 'Silence alone does not establish rejection, even when uncertainty feels uncomfortable.',
    'emerging_delta' => 'Silence alone does not establish rejection, even when uncertainty feels uncomfortable.',
    'thread_summary' => 'friendship and boundaries',
    'grounding_anchor' => array(
        'title' => 'Silence and Rejection After Conflict',
        'proposition' => 'Silence alone does not establish rejection, even when uncertainty feels uncomfortable.',
    ),
);
$naturalResponse = invoke_hrn_private($harness, 'recover_natural_landing_response', array($naturalLandingState));
$assert(true, is_array($naturalResponse) && trim((string)($naturalResponse['response'] ?? '')) !== '', 'natural junction recovers with a grounded local response');
$assert('', (string)($naturalResponse['question'] ?? ''), 'natural junction recovery does not reopen with another question');
$assert(true, !empty($naturalResponse['rest']) && empty($naturalResponse['use_resource']), 'natural junction recovery preserves rest and does not force a resource handoff');
$emptyEvidenceResponse = invoke_hrn_private($harness, 'recover_natural_landing_response', array(array(
    'conversation' => '',
    'grounding_anchor' => array('title' => 'Silence and Rejection', 'proposition' => 'Silence alone does not establish rejection, even when uncertainty feels uncomfortable.'),
)));
$assert(true, $emptyEvidenceResponse === null, 'natural junction recovery rejects a landing without earned journey evidence');

// Exercise the actual local fallback + actual boundedness + actual evidence gate
// as one connected operation, using the exact visitor closure that failed live.
$state = array(
    'closure_message' => $earned,
    'conversation' => json_encode(array(array('role' => 'assistant', 'content' => 'Silence alone does not establish rejection, even when uncertainty feels uncomfortable.'))),
    'grounding_anchor' => array(
        'title' => 'Silence and Rejection After Conflict',
        'proposition' => 'Silence alone does not establish rejection, even when uncertainty feels uncomfortable.',
    ),
);
$landing = invoke_hrn_private($harness, 'local_grounded_closure_synthesis', array($state));
$assert(true, is_string($landing) && trim($landing) !== '', 'local closure fallback produces a landing for the reproduced visitor insight');
$assert(true, invoke_hrn_private($harness, 'closure_synthesis_is_bounded', array($landing)), 'local closure fallback respects terminal boundedness');
$assert(true, invoke_hrn_private($harness, 'closure_synthesis_carries_journey_evidence', array($landing, $state)), 'local closure landing preserves earned visitor evidence');


// Reproduce the live hurt-to-tone sequence. The terminal fallback must retain
// only the visitor's stated sequence and must pass the real closure-shape and
// visitor-evidence gates without depending on any provider.
$toneTurn1 = 'Usually I try to explain the words that hurt me, and then the conversation shifts to how I said them.';
$toneTurn2 = 'I wonder whether my hurt can be heard if I cannot explain it perfectly.';
$toneState = array(
    'closure_message' => 'I think I understand the pattern now. Please let this conversation land.',
    'conversation' => "Visitor: " . $toneTurn1 . "\nHRN: The conversation turns to how those words were said.\nVisitor: " . $toneTurn2 . "\nHRN: What would tell you that the hurt itself had been heard, even if the explanation were imperfect?",
    'visitor_turn_evidence' => array($toneTurn1, $toneTurn2),
    'observer_contrast' => 'The conversation shifts from the original hurt to how it was said; tone becomes the focus.',
    'observer_intention' => $toneTurn2,
    'perspective_delta' => 'The words that hurt and the way they were said have become separate focuses.',
    'completed_insight' => 'The visitor wonders whether hurt can be heard without a perfect explanation.',
    'last_nugget' => 'The hurt can be discussed separately from the way it was said.',
    'body_of_thought' => 'The conversation shifts from the original hurt to how it was said.',
    'current_terrain' => $toneTurn2,
    'journey_purpose' => 'understand the recurring hurt-and-tone argument',
    'thread_summary' => 'the original hurt and the way it was said',
    'grounding_anchor' => array(),
    'archive_grounding' => '',
);
$toneClosure = invoke_hrn_private($harness, 'provider_independent_terminal_closure', array($toneState));
$assert(true, is_string($toneClosure) && strpos($toneClosure, 'the discussion turns to how those words were said') !== false, 'terminal closure retains the exact hurt-to-words sequence');
$assert(true, invoke_hrn_private($harness, 'closure_synthesis_is_bounded', array($toneClosure)), 'terminal hurt-to-tone closure meets two-paragraph boundedness');
$assert(true, invoke_hrn_private($harness, 'closure_synthesis_carries_journey_evidence', array($toneClosure, $toneState)), 'terminal hurt-to-tone closure overlaps accepted visitor turns');

$bareState = array('closure_message' => $bareCommand);
$bareLanding = invoke_hrn_private($harness, 'local_grounded_closure_synthesis', array($bareState));
$assert(true, $bareLanding === '', 'bare closure command cannot fabricate a local insight landing');
