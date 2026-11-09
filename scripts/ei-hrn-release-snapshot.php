<?php
/**
 * CLI-only, byte-verifiable HRN/EI release snapshot.
 *
 * Usage:
 *   php scripts/ei-hrn-release-snapshot.php --wp-root=/path/to/wordpress --output-dir=/private/recovery
 *
 * The output directory must already exist, be writable, have mode 0700, and be
 * outside the WordPress root. This tool never writes into WordPress.
 */
if (PHP_SAPI !== 'cli') {
    fwrite(STDERR, "CLI only.\n");
    exit(2);
}
if (!class_exists('ZipArchive')) {
    fwrite(STDERR, "ZipArchive extension is required.\n");
    exit(2);
}

function snapshot_fail(string $message): void {
    throw new RuntimeException($message);
}
function snapshot_inside(string $path, string $root): bool {
    $root = rtrim($root, DIRECTORY_SEPARATOR) . DIRECTORY_SEPARATOR;
    return strncmp($path, $root, strlen($root)) === 0;
}
function snapshot_plugin_version(string $mainFile): string {
    $source = file_get_contents($mainFile);
    if ($source === false || !preg_match('/^[ \t*#]*Version:\s*([^\r\n]+)/mi', $source, $match)) {
        snapshot_fail("Cannot read plugin Version header: " . basename($mainFile));
    }
    return trim($match[1]);
}
function snapshot_scan_tree(string $directory, string $archivePrefix): array {
    $base = realpath($directory);
    if ($base === false || !is_dir($base)) snapshot_fail("Plugin directory missing: {$directory}");
    $files = [];
    $iterator = new RecursiveIteratorIterator(
        new RecursiveDirectoryIterator($base, FilesystemIterator::SKIP_DOTS),
        RecursiveIteratorIterator::SELF_FIRST
    );
    foreach ($iterator as $item) {
        $path = $item->getPathname();
        if ($item->isLink()) snapshot_fail("Symlinks are not permitted in plugin trees: {$path}");
        if ($item->isDir()) continue;
        if (!$item->isFile()) snapshot_fail("Non-regular file found: {$path}");
        $name = basename($path);
        if (preg_match('/(^\.env(?:\.|$)|secret|credential|private[-_.]?key|(^|[._-])token([._-]|$)|\.pem$|\.key$|\.p12$|\.pfx$|\.log$|\.sql(?:\.gz)?$)/i', $name)) {
            snapshot_fail("Sensitive or volatile filename requires manual resolution before capture: {$path}");
        }
        $contents = file_get_contents($path);
        if ($contents === false) snapshot_fail("Cannot read file: {$path}");
        if (preg_match('/-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|\bAKIA[0-9A-Z]{16}\b|\bgh[pousr]_[A-Za-z0-9]{20,}\b|\bsk-[A-Za-z0-9]{20,}\b|\bAIza[0-9A-Za-z_-]{30,}\b/', $contents)) {
            snapshot_fail("Credential-like material detected; refusing capture: {$path}");
        }
        $relative = str_replace(DIRECTORY_SEPARATOR, '/', substr($path, strlen($base) + 1));
        $files[] = [
            'source' => $path,
            'archive_path' => $archivePrefix . '/' . $relative,
            'size' => filesize($path),
            'sha256' => hash_file('sha256', $path),
        ];
    }
    if (!$files) snapshot_fail("Plugin tree is empty: {$directory}");
    usort($files, fn($a, $b) => strcmp($a['archive_path'], $b['archive_path']));
    return $files;
}
function snapshot_zip_hash(ZipArchive $zip, string $entry): array {
    $stream = $zip->getStream($entry);
    if (!$stream) snapshot_fail("Cannot reopen archive entry: {$entry}");
    $context = hash_init('sha256');
    $size = hash_update_stream($context, $stream);
    fclose($stream);
    return ['size' => $size, 'sha256' => hash_final($context)];
}

try {
    $options = getopt('', ['wp-root:', 'output-dir:']);
    if (empty($options['wp-root']) || empty($options['output-dir'])) {
        snapshot_fail('Both --wp-root and --output-dir are required.');
    }
    $wpRoot = realpath($options['wp-root']);
    $outputDir = realpath($options['output-dir']);
    if ($wpRoot === false || !is_dir($wpRoot)) snapshot_fail('WordPress root does not exist.');
    if ($outputDir === false || !is_dir($outputDir) || !is_writable($outputDir)) snapshot_fail('Output directory must already exist and be writable.');
    if (snapshot_inside($outputDir, $wpRoot) || $outputDir === $wpRoot) snapshot_fail('Output directory must be outside the WordPress root.');
    if ((fileperms($outputDir) & 0077) !== 0) snapshot_fail('Output directory permissions must be 0700 (no group/world access).');

    $pluginsRoot = realpath($wpRoot . '/wp-content/plugins');
    if ($pluginsRoot === false) snapshot_fail('WordPress plugins directory not found.');
    $hrnDir = $pluginsRoot . '/human-relational-navigator';
    $eiDir = $pluginsRoot . '/living-archive-emergency-intelligence';
    $hrnMain = $hrnDir . '/human-relational-navigator.php';
    $eiMain = $eiDir . '/living-archive-emergency-intelligence.php';
    $registryPath = $eiDir . '/data/emergency-registry.json';
    foreach ([$hrnMain, $eiMain, $registryPath] as $required) {
        if (!is_file($required) || is_link($required)) snapshot_fail("Required release file missing or unsafe: {$required}");
    }

    $registryRaw = file_get_contents($registryPath);
    $registry = json_decode((string)$registryRaw, true);
    if (!is_array($registry) || empty($registry['schema_version']) || empty($registry['registry_version'])) {
        snapshot_fail('EI registry JSON is invalid or lacks schema_version/registry_version.');
    }

    $files = array_merge(
        snapshot_scan_tree($hrnDir, 'human-relational-navigator'),
        snapshot_scan_tree($eiDir, 'living-archive-emergency-intelligence')
    );
    $manifest = [
        'format' => 'living-archive-ei-hrn-release-snapshot',
        'format_version' => 1,
        'captured_at_utc' => gmdate('Y-m-d\TH:i:s\Z'),
        'wordpress_root_label' => basename($wpRoot),
        'plugins' => [
            'human-relational-navigator' => ['version' => snapshot_plugin_version($hrnMain)],
            'living-archive-emergency-intelligence' => [
                'version' => snapshot_plugin_version($eiMain),
                'registry_schema_version' => (string)$registry['schema_version'],
                'registry_version' => (string)$registry['registry_version'],
            ],
        ],
        'files' => array_map(static function ($file) {
            return [
                'path' => $file['archive_path'],
                'size' => $file['size'],
                'sha256' => $file['sha256'],
            ];
        }, $files),
    ];

    $stamp = gmdate('Ymd\THis\Z');
    $archivePath = $outputDir . '/ei-hrn-release-' . $stamp . '.zip';
    $checksumPath = $archivePath . '.sha256';
    if (file_exists($archivePath) || file_exists($checksumPath)) snapshot_fail('Snapshot filename collision; retry in a new second.');
    $zip = new ZipArchive();
    if ($zip->open($archivePath, ZipArchive::CREATE | ZipArchive::EXCL) !== true) snapshot_fail('Could not create archive.');
    foreach ($files as $file) {
        if (!$zip->addFile($file['source'], $file['archive_path'])) snapshot_fail('Could not add file: ' . $file['archive_path']);
    }
    $manifestJson = json_encode($manifest, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES);
    if ($manifestJson === false || !$zip->addFromString('manifest.json', $manifestJson . "\n")) snapshot_fail('Could not write manifest.');
    if (!$zip->close()) snapshot_fail('Could not finalize archive.');

    $verify = new ZipArchive();
    if ($verify->open($archivePath, ZipArchive::CHECKCONS) !== true) snapshot_fail('Archive failed consistency/reopen check.');
    $expected = ['manifest.json' => true];
    foreach ($manifest['files'] as $entry) $expected[$entry['path']] = true;
    $actual = [];
    for ($i = 0; $i < $verify->numFiles; $i++) {
        $stat = $verify->statIndex($i);
        if (!$stat || isset($actual[$stat['name']])) snapshot_fail('Duplicate or unreadable archive entry.');
        $actual[$stat['name']] = true;
    }
    if (array_diff_key($expected, $actual) || array_diff_key($actual, $expected)) snapshot_fail('Archive entry set does not exactly match manifest.');
    $archivedManifest = $verify->getFromName('manifest.json');
    if (!is_string($archivedManifest) || json_decode($archivedManifest, true) !== $manifest) snapshot_fail('Embedded manifest mismatch.');
    foreach ($manifest['files'] as $entry) {
        $actualHash = snapshot_zip_hash($verify, $entry['path']);
        if ($actualHash['size'] !== $entry['size'] || !hash_equals($entry['sha256'], $actualHash['sha256'])) {
            snapshot_fail('Archive verification failed for: ' . $entry['path']);
        }
    }
    $verify->close();

    $archiveHash = hash_file('sha256', $archivePath);
    if (!$archiveHash) snapshot_fail('Cannot calculate archive checksum.');
    if (file_put_contents($checksumPath, $archiveHash . '  ' . basename($archivePath) . "\n", LOCK_EX) === false) {
        snapshot_fail('Cannot write archive checksum sidecar.');
    }
    if (!hash_equals($archiveHash, hash_file('sha256', $archivePath))) snapshot_fail('Second archive checksum verification failed.');
    if (!chmod($archivePath, 0400) || !chmod($checksumPath, 0400)) snapshot_fail('Could not make verified artifacts read-only.');

    echo json_encode([
        'status' => 'verified',
        'archive' => $archivePath,
        'archive_sha256' => $archiveHash,
        'manifest_entries' => count($manifest['files']),
        'hrn_version' => $manifest['plugins']['human-relational-navigator']['version'],
        'ei_version' => $manifest['plugins']['living-archive-emergency-intelligence']['version'],
        'registry_schema_version' => $manifest['plugins']['living-archive-emergency-intelligence']['registry_schema_version'],
        'registry_version' => $manifest['plugins']['living-archive-emergency-intelligence']['registry_version'],
    ], JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES) . "\n";
} catch (Throwable $error) {
    if (isset($archivePath) && is_file($archivePath) && !isset($archiveHash)) @unlink($archivePath);
    if (isset($checksumPath) && is_file($checksumPath) && !isset($archiveHash)) @unlink($checksumPath);
    fwrite(STDERR, 'SNAPSHOT REFUSED: ' . $error->getMessage() . "\n");
    exit(1);
}
