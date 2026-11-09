<?php
/**
 * Disposable fixture test for the CLI-only EI/HRN snapshot and restore path.
 * Run: php tests/php/test_ei_hrn_release_snapshot.php
 */
function check(bool $condition, string $message): void {
    if (!$condition) throw new RuntimeException($message);
}
function remove_tree(string $path): void {
    if (!file_exists($path) && !is_link($path)) return;
    if (is_link($path) || is_file($path)) { unlink($path); return; }
    foreach (new DirectoryIterator($path) as $item) {
        if ($item->isDot()) continue;
        remove_tree($path . DIRECTORY_SEPARATOR . $item->getFilename());
    }
    rmdir($path);
}
$root = sys_get_temp_dir() . '/ei-hrn-snapshot-test-' . bin2hex(random_bytes(5));
$wp = $root . '/wordpress';
$out = $root . '/private-recovery';
$restore = $root . '/restored';
try {
    mkdir($wp . '/wp-content/plugins/human-relational-navigator', 0700, true);
    mkdir($wp . '/wp-content/plugins/living-archive-emergency-intelligence/data', 0700, true);
    mkdir($out, 0700, true);
    mkdir($restore, 0700, true);
    file_put_contents($wp . '/wp-content/plugins/human-relational-navigator/human-relational-navigator.php',
        "<?php\n/* Plugin Name: Human Relational Navigator\n * Version: 0.5.333\n */\n");
    file_put_contents($wp . '/wp-content/plugins/human-relational-navigator/includes.php', "<?php // fixture\n");
    file_put_contents($wp . '/wp-content/plugins/living-archive-emergency-intelligence/living-archive-emergency-intelligence.php',
        "<?php\n/* Plugin Name: Living Archive Emergency Intelligence\n * Version: 0.1.2\n */\n");
    file_put_contents($wp . '/wp-content/plugins/living-archive-emergency-intelligence/data/emergency-registry.json',
        json_encode(['schema_version' => '0.1', 'registry_version' => '2026.10.13.001']));
    $script = dirname(__DIR__, 2) . '/scripts/ei-hrn-release-snapshot.php';
    $command = escapeshellarg(PHP_BINARY) . ' ' . escapeshellarg($script)
        . ' --wp-root=' . escapeshellarg($wp) . ' --output-dir=' . escapeshellarg($out) . ' 2>&1';
    exec($command, $output, $status);
    check($status === 0, 'Snapshot command failed: ' . implode("\n", $output));
    $result = json_decode(implode("\n", $output), true);
    check(is_array($result) && ($result['status'] ?? '') === 'verified', 'Success response missing.');
    check(($result['hrn_version'] ?? '') === '0.5.333', 'HRN version was not read from fixture.');
    check(($result['ei_version'] ?? '') === '0.1.2', 'EI version was not read from fixture.');
    check(($result['registry_schema_version'] ?? '') === '0.1', 'Registry schema was not captured.');
    check(($result['registry_version'] ?? '') === '2026.10.13.001', 'Registry version was not captured.');

    $archive = $result['archive'];
    check(is_file($archive) && is_file($archive . '.sha256'), 'Archive or checksum sidecar missing.');
    check((fileperms($archive) & 0777) === 0400, 'Archive is not read-only.');
    check(hash_file('sha256', $archive) === $result['archive_sha256'], 'Archive checksum mismatch.');

    $zip = new ZipArchive();
    check($zip->open($archive, ZipArchive::CHECKCONS) === true, 'Archive cannot be reopened for restore test.');
    $manifest = json_decode($zip->getFromName('manifest.json'), true);
    check(is_array($manifest) && count($manifest['files']) === 4, 'Manifest file inventory incorrect.');
    foreach ($manifest['files'] as $entry) {
        $data = $zip->getFromName($entry['path']);
        check(is_string($data), 'Missing archive member: ' . $entry['path']);
        check(strlen($data) === $entry['size'], 'Archived byte size mismatch: ' . $entry['path']);
        check(hash('sha256', $data) === $entry['sha256'], 'Archived digest mismatch: ' . $entry['path']);
        $target = $restore . '/' . $entry['path'];
        if (!is_dir(dirname($target))) mkdir(dirname($target), 0700, true);
        file_put_contents($target, $data);
        check(filesize($target) === $entry['size'] && hash_file('sha256', $target) === $entry['sha256'],
            'Restored file did not match manifest: ' . $entry['path']);
    }
    $zip->close();

    // Safety gate: output under the public WordPress root must be refused.
    $inside = $wp . '/private';
    mkdir($inside, 0700);
    $badCommand = escapeshellarg(PHP_BINARY) . ' ' . escapeshellarg($script)
        . ' --wp-root=' . escapeshellarg($wp) . ' --output-dir=' . escapeshellarg($inside) . ' 2>&1';
    exec($badCommand, $badOutput, $badStatus);
    check($badStatus !== 0 && strpos(implode("\n", $badOutput), 'outside the WordPress root') !== false,
        'Public-root output was not refused.');

    // Safety gate: credential-like content must be refused.
    file_put_contents($wp . '/wp-content/plugins/human-relational-navigator/fixture-data.php',
        "<?php // ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890\n");
    $secretCommand = escapeshellarg(PHP_BINARY) . ' ' . escapeshellarg($script)
        . ' --wp-root=' . escapeshellarg($wp) . ' --output-dir=' . escapeshellarg($out) . ' 2>&1';
    exec($secretCommand, $secretOutput, $secretStatus);
    check($secretStatus !== 0 && strpos(implode("\n", $secretOutput), 'Credential-like material detected') !== false,
        'Credential-like content was not refused.');

    echo "PASS: snapshot creation, manifest hashing, archive reopen, checksum, restore rehearsal, public-root refusal, and credential refusal.\n";
} finally {
    remove_tree($root);
}
