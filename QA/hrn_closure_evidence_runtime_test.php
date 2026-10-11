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
    'conversation' => json_encode(array(array('role' => 'assistant', 'content' => 'Silence alone does not establish rejection, even when uncertainty feels uncomfortable.'))),
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

$bareState = array('closure_message' => $bareCommand);
$bareLanding = invoke_hrn_private($harness, 'local_grounded_closure_synthesis', array($bareState));
$assert(true, $bareLanding === '', 'bare closure command cannot fabricate a local insight landing');
