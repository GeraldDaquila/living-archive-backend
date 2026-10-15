<?php
/**
 * Isolated regression for LAN's hard subject-fit gate.
 *
 * Uses a tiny synthetic fixture because the production corpus/index are
 * recovered separately. This test proves the gate's behavior, not corpus
 * completeness or live WordPress behavior.
 */
define('ABSPATH', __DIR__ . '/');
if (!function_exists('wp_strip_all_tags')) {
    function wp_strip_all_tags($value) { return strip_tags((string)$value); }
}
if (!function_exists('esc_url_raw')) {
    function esc_url_raw($value) { return (string)$value; }
}
require_once __DIR__ . '/../includes/class-lan-engine.php';

function assert_true($condition, string $message): void {
    if (!$condition) {
        fwrite(STDERR, "FAIL: {$message}\n");
        exit(1);
    }
}

$dir = sys_get_temp_dir() . '/lan-subject-fit-' . bin2hex(random_bytes(5));
mkdir($dir, 0777, true);
$resource = static function(string $id, string $title, string $excerpt, string $content, array $categories = []): array {
    return [
        'id' => $id, 'title' => $title, 'url' => 'https://geralddaquila.com/' . $id . '/',
        'tier' => 'T1', 'resource_type' => 'page', 'endpoint_eligible' => true,
        'source_access_class' => 'public', 'content_access_status' => 'public',
        'excerpt' => $excerpt, 'content' => $content, 'source_categories' => $categories,
    ];
};
$resources = [
    $resource('institutional-case-library', 'Institutional Stewardship Case Library',
        'Case material about institutional accountability and responsibility.',
        'A library of cases about institutional stewardship, accountability, responsibility, and governance.',
        ['governance', 'institutional stewardship']),
    $resource('power-responsibility', 'The Difference Between Power and Responsibility',
        'Explains how power and responsibility relate in institutions and leadership.',
        'Institutional responsibility requires accountability for the use of power.',
        ['governance', 'responsibility']),
    $resource('institutional-consciousness', 'Institutional Consciousness',
        'Explores institutional behavior, shared responsibility, and systemic awareness.',
        'Institutions shape responsibility and collective governance.',
        ['institutional systems']),
    $resource('gesara-nodes', 'GESARA Nodes',
        'A discussion of financial abundance and cosmic nodes.',
        'Financial abundance and cosmic nodes are the focus of this page.',
        ['spirituality']),
];
file_put_contents($dir . '/corpus-runtime.json', json_encode([
    'schema_version' => 'fixture', 'resources' => $resources,
], JSON_UNESCAPED_SLASHES));
file_put_contents($dir . '/retrieval-index.json', json_encode([
    'document_count' => count($resources), 'postings' => [],
], JSON_UNESCAPED_SLASHES));
file_put_contents($dir . '/relationships.json', json_encode([
    'schema_version' => 'fixture', 'status' => 'not_available_from_supplied_exports', 'relationships' => [],
]));

$engine = new LAN_Engine($dir);
$reflect = new ReflectionClass($engine);
$invoke = static function(string $method, array $args = []) use ($reflect, $engine) {
    $m = $reflect->getMethod($method);
    $m->setAccessible(true);
    return $m->invokeArgs($engine, $args);
};
$question = 'Where can I find material about institutional responsibility? I want to understand what institutional responsibility means and where the Archive explores it.';
$focus = $invoke('subject_focus_tokens', [$question]);
assert_true(in_array('institutional', $focus, true), 'specific subject token institutional is preserved');
assert_true(in_array('responsibility', $focus, true), 'specific subject token responsibility is preserved');
assert_true(!in_array('material', $focus, true) && !in_array('archive', $focus, true), 'navigation wording is excluded from subject focus');

$prop = $reflect->getProperty('current_subject_focus_tokens');
$prop->setAccessible(true);
$prop->setValue($engine, $focus);
$fit = $invoke('subject_fit_score', [$resources[0], $focus]);
$unrelated_fit = $invoke('subject_fit_score', [$resources[3], $focus]);
assert_true($fit >= 1.0, 'directly relevant resource receives positive subject-fit score');
assert_true($unrelated_fit < 1.0, 'unrelated resource fails hard subject-fit threshold');

$candidates = [];
foreach ($resources as $i => $r) {
    $candidates[] = ['resource' => $r, 'score' => 3.0 - ($i * 0.1), 'anchor_score' => 3.0, 'anchor_terms' => []];
}
$filtered = $invoke('filter_subject_relevant_candidates', [$candidates]);
assert_true(count($filtered) === 3, 'irrelevant resource is removed before planning');

$plan = $invoke('deterministic_plan', [$candidates]);
$selected_ids = array_column($plan['selected'], 'id');
assert_true(count($selected_ids) === 3, 'fallback selects three relevant resources when three exist');
assert_true(!in_array('gesara-nodes', $selected_ids, true), 'deterministic fallback cannot pad with unrelated resource');

$candidate_map = [];
foreach ($candidates as $c) $candidate_map[$c['resource']['id']] = $c;
$bad_plan = ['selected' => [
    ['id' => 'institutional-case-library', 'door' => 'experience'],
    ['id' => 'power-responsibility', 'door' => 'pattern'],
    ['id' => 'gesara-nodes', 'door' => 'structure'],
]];
$issues = $invoke('plan_quality_issues', [$bad_plan, $candidate_map]);
assert_true((bool)array_filter($issues, static fn($issue) => strpos($issue, 'does not fit') !== false),
    'model-selected unrelated destination is rejected by plan validation');

$only_two = $invoke('filter_subject_relevant_candidates', [array_slice($candidates, 0, 2)]);
assert_true(count($only_two) === 2, 'insufficient-evidence path exposes only relevant candidates and never pads');

echo "LAN SUBJECT-FIT GATE FIXTURE: PASS\n";
