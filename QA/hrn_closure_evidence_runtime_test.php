<?php
/**
 * Execute the actual closure-evidence method extracted from the HRN candidate.
 * This avoids booting or activating the production WordPress plugin in CI.
 */
$sourcePath = __DIR__ . '/../wordpress/hrn/human-relational-navigator.php';
$source = file_get_contents($sourcePath);
if (!is_string($source) || $source === '') {
    fwrite(STDERR, "Unable to read HRN candidate source.\n");
    exit(1);
}
$functionStart = strpos($source, 'function closure_synthesis_carries_journey_evidence(');
$methodStart = $functionStart === false
    ? false
    : strrpos(substr($source, 0, $functionStart), 'private function');
$methodEnd = $functionStart === false
    ? false
    : strpos($source, 'private function closure_synthesis_is_bounded(', $functionStart);
if ($methodStart === false || $methodEnd === false || $methodEnd <= $methodStart) {
    fwrite(STDERR, "Unable to isolate the closure-evidence method.\n");
    exit(1);
}
$method = substr($source, $methodStart, $methodEnd - $methodStart);
if (!function_exists('wp_strip_all_tags')) {
    function wp_strip_all_tags($value) { return strip_tags((string)$value); }
}
eval('class HRNClosureEvidenceHarness { ' . $method . ' }');
$harness = new HRNClosureEvidenceHarness();
$reflection = new ReflectionMethod($harness, 'closure_synthesis_carries_journey_evidence');
$reflection->setAccessible(true);
$assert = function ($expected, $text, $state, $label) use ($harness, $reflection) {
    $actual = $reflection->invoke($harness, $text, $state);
    if ($actual !== $expected) {
        fwrite(STDERR, $label . ': expected ' . var_export($expected, true) . ', got ' . var_export($actual, true) . "\n");
        exit(1);
    }
    echo "PASS: " . $label . "\n";
};
$earned = "I think the distinction is that I can acknowledge my friend's experience without denying my own feelings. Please synthesize what we discussed.";
$aligned = "You can acknowledge your friend's experience without denying your own feelings. Both experiences can be recognized without deciding what the other person intended.";
$generic = "The conversation has clarified a distinction in the experience, while leaving its uncertain parts unclaimed.";
$assert(true, $aligned, array('closure_message' => $earned), 'visitor-authored insight survives closure command stripping');
$assert(false, $generic, array('closure_message' => $earned), 'generic synthesis cannot pass on the visitor statement alone');
$assert(false, $generic, array('closure_message' => 'Please synthesize what we discussed.'), 'bare synthesis request is not journey evidence');
$assert(false, $generic, array('closure_message' => 'I have reached enough for now.'), 'bare stop command is not journey evidence');
$assert(true, 'The silence does not establish rejection; that feeling does not prove the other person’s intention.', array('perspective_delta' => 'Silence alone does not establish rejection, even when uncertainty feels uncomfortable.'), 'existing ledger evidence path remains intact');
