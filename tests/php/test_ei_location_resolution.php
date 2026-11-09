<?php
/**
 * Standalone EI location precedence and confidence tests.
 * Uses a disposable local registry fixture; no WordPress or network access.
 */
define('ABSPATH', __DIR__ . '/');
$source_registry = __DIR__ . '/../../plugins/living-archive-emergency-intelligence/data/emergency-registry.json';
$temp_registry = tempnam(sys_get_temp_dir(), 'laei-location-');
if ($temp_registry === false) throw new RuntimeException('Could not create temporary registry fixture.');
$registry_json = file_get_contents($source_registry);
if ($registry_json === false) throw new RuntimeException('Could not read canonical registry fixture.');
file_put_contents($temp_registry, $registry_json);
define('LAEI_REGISTRY_FILE', $temp_registry);

$GLOBALS['laei_location_test_now'] = strtotime('2026-11-09 12:00:00 UTC');
function current_time($type, $gmt = false) { return $GLOBALS['laei_location_test_now']; }
function sanitize_key($value) { return preg_replace('/[^a-z0-9_-]/', '', strtolower((string)$value)); }
function sanitize_text_field($value) { return trim(strip_tags((string)$value)); }

require_once __DIR__ . '/../../plugins/living-archive-emergency-intelligence/includes/class-lai-ei-registry.php';
require_once __DIR__ . '/../../plugins/living-archive-emergency-intelligence/includes/class-lai-ei-location-resolver.php';

function location_assert($condition, $message) {
    if (!$condition) { fwrite(STDERR, "FAIL: " . $message . "\n"); exit(1); }
    echo "PASS: " . $message . "\n";
}

$explicit = LAEI_Location_Resolver::resolve([
    'explicit_country' => 'Philippines',
    'browser_country' => 'United States',
    'ip_country' => 'Germany',
]);
location_assert(($explicit['location']['country']['value'] ?? '') === 'PH', 'explicit current user statement outranks browser and IP evidence');
location_assert(($explicit['conflicts'][0]['resolution'] ?? '') === 'explicit_user_statement', 'conflicting evidence records the explicit-user resolution rule');
location_assert(in_array('US', $explicit['conflicts'][0]['values'] ?? [], true), 'browser conflict remains visible in provenance');

$browser = LAEI_Location_Resolver::resolve([
    'browser_country' => 'United States',
    'ip_country' => 'Philippines',
]);
location_assert(($browser['location']['country']['value'] ?? '') === 'US', 'browser geolocation outranks lower-confidence IP inference');

$unsupported = LAEI_Location_Resolver::resolve([
    'explicit_country' => 'Japan',
    'browser_country' => 'Philippines',
]);
location_assert(($unsupported['location']['country']['value'] ?? '') === 'JAPAN', 'unsupported explicit country is not silently replaced by inferred country');
location_assert(($unsupported['resource_selection_confidence'] ?? '') === 'unknown', 'unsupported explicit country does not receive resource confidence');

$refused = LAEI_Location_Resolver::resolve(['explicit_country' => 'Philippines', 'refused' => true]);
location_assert(($refused['resolution_status'] ?? '') === 'REFUSED', 'explicit location refusal overrides inferred resolution');
location_assert(($refused['resource_selection_confidence'] ?? '') === 'unknown', 'refused location has unknown resource confidence');

$current = LAEI_Location_Resolver::resolve(['explicit_country' => 'Philippines']);
location_assert(($current['resource_selection_confidence'] ?? '') === 'high', 'current provenance-backed verification produces high resource confidence');

$expired_data = json_decode($registry_json, true);
foreach ($expired_data['verification_records'] as &$record) {
    if (($record['verification_id'] ?? '') === 'VER-PH-911-2026') $record['review_due'] = '2026-11-08';
}
unset($record);
file_put_contents(LAEI_REGISTRY_FILE, json_encode($expired_data, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE));
LAEI_Registry::load(true);
$expired = LAEI_Location_Resolver::resolve(['explicit_country' => 'Philippines']);
location_assert(($expired['resource_selection_confidence'] ?? '') === 'unknown', 'expired verification cannot inflate location resource confidence');

@unlink($temp_registry);
echo "All EI location precedence and confidence tests passed.\n";
