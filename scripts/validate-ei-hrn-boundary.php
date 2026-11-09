<?php
$phpPath = 'plugins/human-relational-navigator/human-relational-navigator.php';
$jsPath = 'plugins/human-relational-navigator/assets/relational-navigator.js';
$php = file_get_contents($phpPath);
$js = file_get_contents($jsPath);
if ($php === false || $js === false) {
    fwrite(STDERR, "Required HRN source files are missing.\n");
    exit(1);
}
$start = strpos($php, 'public function resource_location_handler');
$end = strpos($php, 'public function add_runtime_timing_headers', $start === false ? 0 : $start);
if ($start === false || $end === false) {
    fwrite(STDERR, "Resource-only adapter boundary is missing.\n");
    exit(1);
}
$adapter = substr($php, $start, $end - $start);
foreach (array('safety_answer_class(', 'safety_transition(', 'rest_handler_inner(') as $forbidden) {
    if (strpos($adapter, $forbidden) !== false) {
        fwrite(STDERR, "Forbidden safety/conversation call in adapter: " . $forbidden . "\n");
        exit(1);
    }
}
if (strpos($php, 'living_archive_emergency_resolve($need') === false) {
    fwrite(STDERR, "EI public resolver is not wired into the adapter.\n");
    exit(1);
}
if (strpos($adapter, '$this->safety_resource_bundle(') !== false || strpos($adapter, '$legacy') !== false) {
    fwrite(STDERR, "Legacy HRN resource fallback remains in the EI adapter.\\n");
    exit(1);
}
if (strpos($adapter, "'resource_provenance'=>\$bundle['resource_provenance']") === false ||
    strpos($php, "'ei_no_verified_fallback'") === false ||
    strpos($php, "'ei_verified_only'") === false) {
    fwrite(STDERR, "EI-only provenance states are missing from the shared resolver/adapter.\\n");
    exit(1);
}
$safetyStart = strpos($php, 'private function safety_response(');
$safetyEnd = strpos($php, 'private function safety_answer_class(', $safetyStart === false ? 0 : $safetyStart);
if ($safetyStart === false || $safetyEnd === false) {
    fwrite(STDERR, "HRN safety response boundary is missing.\\n");
    exit(1);
}
$safetyResponse = substr($php, $safetyStart, $safetyEnd - $safetyStart);
if (strpos($safetyResponse, '$this->resolve_ei_resource_bundle($country_code, $stage)') === false ||
    strpos($safetyResponse, "'resources'=>\$bundle['resources']") === false ||
    strpos($safetyResponse, "'location_required'=>($country_code === '')") === false ||
    strpos($safetyResponse, '$this->safety_resource_bundle(') !== false) {
    fwrite(STDERR, "Initial HRN safety response is not using the EI-only resource resolver.\\n");
    exit(1);
}
$jsStart = strpos($js, 'function submitSafetyLocation(v)');
$jsEnd = strpos($js, 'function returnCompletedJourneyToGuide', $jsStart === false ? 0 : $jsStart);
if ($jsStart === false || $jsEnd === false) {
    fwrite(STDERR, "Frontend location submission function is missing.\n");
    exit(1);
}
$submit = substr($js, $jsStart, $jsEnd - $jsStart);
if (strpos($submit, 'LAHRN.emergency_endpoint') === false) {
    fwrite(STDERR, "Frontend does not use the dedicated resource endpoint.\n");
    exit(1);
}
foreach (array('message:v', 'conversation:', 'visitor_history:') as $forbidden) {
    if (strpos($submit, $forbidden) !== false) {
        fwrite(STDERR, "Location request contains conversation field: " . $forbidden . "\n");
        exit(1);
    }
}
echo "Location-only boundary assertions passed.\n";
