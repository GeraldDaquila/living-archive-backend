<?php
/**
 * Isolated EI registry provenance and expiry contract tests.
 * No WordPress installation, production database, or network calls required.
 */
define('ABSPATH', __DIR__ . '/');
$source_registry = __DIR__ . '/../../plugins/living-archive-emergency-intelligence/data/emergency-registry.json';
$temp_registry = tempnam(sys_get_temp_dir(), 'laei-registry-');
if ($temp_registry === false) throw new RuntimeException('Could not create temporary registry fixture.');
$registry_json = file_get_contents($source_registry);
if ($registry_json === false) throw new RuntimeException('Could not read canonical registry fixture.');
file_put_contents($temp_registry, $registry_json);
define('LAEI_REGISTRY_FILE', $temp_registry);

$GLOBALS['laei_test_now'] = strtotime('2026-11-09 12:00:00 UTC');
function current_time($type, $gmt = false) { return $GLOBALS['laei_test_now']; }
function sanitize_key($value) { return preg_replace('/[^a-z0-9_-]/', '', strtolower((string)$value)); }
function sanitize_text_field($value) { return trim(strip_tags((string)$value)); }

require_once __DIR__ . '/../../plugins/living-archive-emergency-intelligence/includes/class-lai-ei-registry.php';
require_once __DIR__ . '/../../plugins/living-archive-emergency-intelligence/includes/class-lai-ei-resource-selector.php';
require_once __DIR__ . '/../../plugins/living-archive-emergency-intelligence/includes/class-lai-ei-presenter.php';

function ei_assert($condition, $message) {
    if (!$condition) { fwrite(STDERR, "FAIL: " . $message . "\n"); exit(1); }
    echo "PASS: " . $message . "\n";
}
function ei_load_fixture($data) {
    file_put_contents(LAEI_REGISTRY_FILE, json_encode($data, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE));
    return LAEI_Registry::load(true);
}
function ei_location($country) {
    return [
        'resolution_status' => 'RESOLVED',
        'resource_selection_confidence' => 'high',
        'location' => [
            'country' => ['value' => $country],
            'region' => ['value' => 'NCR'],
        ],
    ];
}
function ei_actions($selection) {
    $presentation = LAEI_Presenter::present($selection, 'acute_emergency');
    return $presentation['actions'] ?? [];
}

$canonical = json_decode($registry_json, true);
ei_assert(is_array($canonical), 'canonical registry fixture parses as JSON');
ei_assert(($canonical['schema_version'] ?? '') === '0.2', 'registry uses the provenance-aware schema version');
ei_assert(LAEI_Registry::validate_candidate($canonical)['valid'] === true, 'complete canonical registry passes candidate validation');
ei_load_fixture($canonical);

$selected = LAEI_Resource_Selector::select('general_emergency', ei_location('PH'), 'acute');
ei_assert(($selected['selection_status'] ?? '') === 'SELECTED', 'current verified Philippines emergency resource is selected');
$selected_actions = ei_actions($selected);
ei_assert(count($selected_actions) === 1 && ($selected_actions[0]['value'] ?? '') === '911', 'current verified resource produces exactly its callable telephone action');

$expired = $canonical;
foreach ($expired['verification_records'] as &$record) {
    if ($record['verification_id'] === 'VER-PH-911-2026') $record['review_due'] = '2026-11-08';
}
unset($record);
ei_load_fixture($expired);
$expired_selection = LAEI_Resource_Selector::select('general_emergency', ei_location('PH'), 'acute');
ei_assert(($expired_selection['selection_status'] ?? '') === 'VERIFICATION_EXPIRED', 'expired verification is explicitly rejected');
ei_assert(count(ei_actions($expired_selection)) === 0, 'expired resource cannot generate a telephone action');

$future = $canonical;
foreach ($future['verification_records'] as &$record) {
    if ($record['verification_id'] === 'VER-PH-911-2026') $record['verified_at'] = '2026-11-10';
}
unset($record);
ei_load_fixture($future);
$future_selection = LAEI_Resource_Selector::select('general_emergency', ei_location('PH'), 'acute');
ei_assert(($future_selection['selection_status'] ?? '') === 'VERIFICATION_FUTURE_DATED', 'future-dated verification is explicitly rejected');
ei_assert(count(ei_actions($future_selection)) === 0, 'future-dated verification cannot generate a telephone action');

$unverified = $canonical;
foreach ($unverified['verification_records'] as &$record) {
    if ($record['verification_id'] === 'VER-PH-911-2026') $record['status'] = 'unverified';
}
unset($record);
ei_load_fixture($unverified);
$unverified_selection = LAEI_Resource_Selector::select('general_emergency', ei_location('PH'), 'acute');
ei_assert(($unverified_selection['selection_status'] ?? '') === 'VERIFICATION_UNVERIFIED', 'unverified resource is explicitly rejected');
ei_assert(count(ei_actions($unverified_selection)) === 0, 'unverified resource cannot generate a telephone action');

$no_sources = $canonical;
foreach ($no_sources['verification_records'] as &$record) {
    if ($record['verification_id'] === 'VER-PH-911-2026') $record['source_urls'] = [];
}
unset($record);
ei_assert(LAEI_Registry::validate_candidate($no_sources)['valid'] === false, 'candidate validator rejects a verification record without source URLs');
ei_load_fixture($no_sources);
$no_sources_selection = LAEI_Resource_Selector::select('general_emergency', ei_location('PH'), 'acute');
ei_assert(($no_sources_selection['selection_status'] ?? '') === 'VERIFICATION_PROVENANCE_MISSING', 'runtime selection rejects missing source provenance');
ei_assert(count(ei_actions($no_sources_selection)) === 0, 'missing source provenance cannot generate a telephone action');

$bad_url = $canonical;
foreach ($bad_url['verification_records'] as &$record) {
    if ($record['verification_id'] === 'VER-PH-911-2026') $record['source_urls'] = ['http://not-secure.example/source'];
}
unset($record);
ei_assert(LAEI_Registry::validate_candidate($bad_url)['valid'] === false, 'candidate validator rejects non-HTTPS source URLs');

$wrong_mapping = $canonical;
foreach ($wrong_mapping['verification_records'] as &$record) {
    if ($record['verification_id'] === 'VER-PH-911-2026') $record['resource_ids'] = ['US-911-GENERAL'];
}
unset($record);
ei_assert(LAEI_Registry::validate_candidate($wrong_mapping)['valid'] === false, 'candidate validator rejects verification records mapped to the wrong resource');
ei_load_fixture($wrong_mapping);
$wrong_mapping_selection = LAEI_Resource_Selector::select('general_emergency', ei_location('PH'), 'acute');
ei_assert(($wrong_mapping_selection['selection_status'] ?? '') === 'VERIFICATION_PROVENANCE_MISSING', 'runtime selection rejects a resource not explicitly mapped to its evidence');
ei_assert(count(ei_actions($wrong_mapping_selection)) === 0, 'mismatched resource-to-evidence mapping cannot generate a telephone action');

$missing_authority = $canonical;
foreach ($missing_authority['verification_records'] as &$record) {
    if ($record['verification_id'] === 'VER-PH-911-2026') unset($record['authority_level']);
}
unset($record);
ei_assert(LAEI_Registry::validate_candidate($missing_authority)['valid'] === false, 'candidate validator rejects missing authority metadata');
ei_load_fixture($missing_authority);
$missing_authority_selection = LAEI_Resource_Selector::select('general_emergency', ei_location('PH'), 'acute');
ei_assert(($missing_authority_selection['selection_status'] ?? '') === 'VERIFICATION_PROVENANCE_MISSING', 'runtime selection rejects incomplete authority metadata');
ei_assert(count(ei_actions($missing_authority_selection)) === 0, 'incomplete authority metadata cannot generate a telephone action');

$missing_verification = $canonical;
foreach ($missing_verification['resources'] as &$resource) {
    if ($resource['resource_id'] === 'PH-911-GENERAL') $resource['verification_id'] = 'VER-NOT-PRESENT';
}
unset($resource);
ei_load_fixture($missing_verification);
$missing_selection = LAEI_Resource_Selector::select('general_emergency', ei_location('PH'), 'acute');
ei_assert(($missing_selection['selection_status'] ?? '') === 'VERIFICATION_MISSING', 'missing verification record fails closed');
ei_assert(count(ei_actions($missing_selection)) === 0, 'missing verification record cannot generate a telephone action');

$invalid_date = $canonical;
foreach ($invalid_date['verification_records'] as &$record) {
    if ($record['verification_id'] === 'VER-PH-911-2026') $record['review_due'] = '2026-02-31';
}
unset($record);
ei_load_fixture($invalid_date);
$invalid_date_selection = LAEI_Resource_Selector::select('general_emergency', ei_location('PH'), 'acute');
ei_assert(($invalid_date_selection['selection_status'] ?? '') === 'VERIFICATION_INVALID', 'impossible calendar date is rejected');
ei_assert(count(ei_actions($invalid_date_selection)) === 0, 'invalid verification date cannot generate a telephone action');

ei_load_fixture($canonical);
$equivalent = LAEI_Resource_Selector::select('general_emergency', ei_location('GB'), 'acute');
ei_assert(($equivalent['selection_status'] ?? '') === 'MULTIPLE_EQUIVALENT', 'UK 999/112 equivalence remains available with shared explicit provenance');
$equivalent_actions = ei_actions($equivalent);
$equivalent_numbers = array_values(array_map(function($action) { return $action['value'] ?? ''; }, $equivalent_actions));
sort($equivalent_numbers);
ei_assert($equivalent_numbers === ['112','999'], 'both equivalent UK numbers are callable only while their shared verification remains current');

@unlink($temp_registry);
echo "All EI provenance and expiry contract tests passed.\n";
