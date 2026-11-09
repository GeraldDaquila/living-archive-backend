<?php
if (!defined('ABSPATH')) exit;

class LAEI_Registry {
    private static $registry = null;

    public static function init() {
        self::load();
    }

    public static function load($force = false) {
        if (self::$registry !== null && !$force) return self::$registry;
        if (!file_exists(LAEI_REGISTRY_FILE)) return null;
        $json = file_get_contents(LAEI_REGISTRY_FILE);
        $data = json_decode($json, true);
        if (!is_array($data)) return null;
        if (!self::validate_structure($data)) return null;
        self::$registry = $data;
        return self::$registry;
    }

    public static function get() { return self::load(); }

    public static function version() {
        $r = self::load();
        return $r['registry_version'] ?? null;
    }

    public static function resolve_country_id($country_input) {
        $value = strtoupper(trim((string)$country_input));
        if ($value === '') return '';
        $r = self::load();
        foreach (($r['countries'] ?? []) as $country) {
            $id = strtoupper((string)($country['country_id'] ?? ''));
            $iso = strtoupper((string)($country['iso2'] ?? ''));
            if ($value === $id || $value === $iso) return $id;
            foreach (($country['aliases'] ?? []) as $alias) {
                if ($value === strtoupper(trim((string)$alias))) return $id;
            }
            if ($value === strtoupper(trim((string)($country['name'] ?? '')))) return $id;
        }
        return '';
    }

    public static function get_country($country_id) {
        $resolved = self::resolve_country_id($country_id);
        if ($resolved === '') return null;
        $r = self::load();
        foreach (($r['countries'] ?? []) as $country) {
            if (($country['country_id'] ?? '') === $resolved) return $country;
        }
        return null;
    }

    public static function get_architecture($architecture_id) {
        $r = self::load();
        foreach (($r['architectures'] ?? []) as $architecture) {
            if (($architecture['architecture_id'] ?? '') === $architecture_id) return $architecture;
        }
        return null;
    }

    public static function get_resources($country_id = null, $service_need = null) {
        $r = self::load();
        $out = [];
        $resolved_country = $country_id ? self::resolve_country_id($country_id) : '';
        if ($country_id && $resolved_country === '') return [];
        foreach (($r['resources'] ?? []) as $resource) {
            if ($resolved_country && ($resource['country_id'] ?? '') !== $resolved_country) continue;
            if ($service_need && !in_array($service_need, $resource['service_types'] ?? [], true)) continue;
            $out[] = $resource;
        }
        return $out;
    }

    public static function get_verification($verification_id) {
        $r = self::load();
        foreach (($r['verification_records'] ?? []) as $record) {
            if (($record['verification_id'] ?? '') === $verification_id) return $record;
        }
        return null;
    }

    public static function source_urls_valid($urls) {
        if (!is_array($urls) || empty($urls)) return false;
        foreach ($urls as $url) {
            if (!is_string($url) || filter_var($url, FILTER_VALIDATE_URL) === false) return false;
            $parts = parse_url($url);
            if (!is_array($parts) || strtolower((string)($parts['scheme'] ?? '')) !== 'https' || empty($parts['host'])) return false;
        }
        return true;
    }

    public static function verification_provenance_valid($record, $resource_id) {
        if (!is_array($record) || !is_array($record['resource_ids'] ?? null)) return false;
        if (!in_array((string)$resource_id, $record['resource_ids'], true)) return false;
        if (empty($record['source']) || !self::source_urls_valid($record['source_urls'] ?? null)) return false;
        return true;
    }

    public static function get_overrides() {
        $r = self::load();
        return $r['regional_overrides'] ?? [];
    }

    public static function validate_structure($data) {
        if (!is_array($data)) return false;
        foreach (['registry_version','schema_version','countries','architectures','resources','verification_records'] as $key) {
            if (!array_key_exists($key, $data)) return false;
        }
        if (!is_array($data['countries']) || !is_array($data['architectures']) || !is_array($data['resources']) || !is_array($data['verification_records'])) return false;
        return true;
    }

    public static function validate_candidate($data) {
        if (!self::validate_structure($data)) return ['valid' => false, 'error' => 'Invalid registry structure.'];
        if (($data['schema_version'] ?? '') !== '0.2') return ['valid' => false, 'error' => 'Unsupported schema version.'];
        if (!preg_match('/^\d{4}\.\d{2}\.\d{2}\.\d{3}$/', (string)($data['registry_version'] ?? ''))) {
            return ['valid' => false, 'error' => 'Invalid registry version.'];
        }

        $country_ids = [];
        foreach ($data['countries'] as $country) {
            foreach (['country_id','iso2','name','emergency_architecture_id','status'] as $key) {
                if (empty($country[$key])) return ['valid' => false, 'error' => 'Country missing required fields.'];
            }
            $country_id = strtoupper((string)$country['country_id']);
            if (isset($country_ids[$country_id])) return ['valid' => false, 'error' => 'Duplicate country ID.'];
            if (!preg_match('/^[A-Z]{2}$/', $country_id)) return ['valid' => false, 'error' => 'Invalid country ID.'];
            if (strtoupper((string)$country['iso2']) !== $country_id) return ['valid' => false, 'error' => 'Country ISO2 mismatch.'];
            if (($country['status'] ?? '') !== 'active') return ['valid' => false, 'error' => 'Country is not active.'];
            if (isset($country['aliases']) && !is_array($country['aliases'])) return ['valid' => false, 'error' => 'Country aliases must be an array.'];
            $country_ids[$country_id] = true;
        }

        $architecture_ids = [];
        foreach ($data['architectures'] as $architecture) {
            if (empty($architecture['architecture_id']) || empty($architecture['architecture_type']) || empty($architecture['services']) || !is_array($architecture['services'])) {
                return ['valid' => false, 'error' => 'Architecture missing required fields.'];
            }
            if (isset($architecture_ids[$architecture['architecture_id']])) return ['valid' => false, 'error' => 'Duplicate architecture ID.'];
            $architecture_ids[$architecture['architecture_id']] = true;
        }

        foreach ($data['countries'] as $country) {
            if (!isset($architecture_ids[$country['emergency_architecture_id']])) return ['valid' => false, 'error' => 'Country references unknown architecture.'];
        }

        $verification_ids = [];
        $verification_records = [];
        foreach ($data['verification_records'] as $record) {
            if (!is_array($record)) return ['valid' => false, 'error' => 'Verification record must be an object.'];
            foreach (['verification_id','status','authority_level','verification_scope','verified_at','review_due','source','resource_ids','source_urls'] as $key) {
                if (!array_key_exists($key, $record) || (is_string($record[$key]) && trim($record[$key]) === '') || $record[$key] === null) {
                    return ['valid' => false, 'error' => 'Verification record missing required fields.'];
                }
            }
            if (isset($verification_ids[$record['verification_id']])) return ['valid' => false, 'error' => 'Duplicate verification ID.'];
            if (!in_array($record['status'], ['verified','unverified','rejected'], true)) return ['valid' => false, 'error' => 'Verification record has invalid status.'];
            if (!preg_match('/^\d{4}-\d{2}-\d{2}$/', (string)$record['verified_at']) || strtotime($record['verified_at'] . ' 00:00:00 UTC') === false) {
                return ['valid' => false, 'error' => 'Verification record has invalid verified_at date.'];
            }
            if (!preg_match('/^\\d{4}-\\d{2}-\\d{2}$/', (string)$record['review_due']) || strtotime($record['review_due'] . ' 23:59:59 UTC') === false) {
                return ['valid' => false, 'error' => 'Verification record has invalid review_due date.'];
            }
            if (!is_array($record['resource_ids']) || empty($record['resource_ids'])) return ['valid' => false, 'error' => 'Verification record must map to one or more resource IDs.'];
            foreach ($record['resource_ids'] as $resource_id) {
                if (!is_string($resource_id) || trim($resource_id) === '') return ['valid' => false, 'error' => 'Verification record has an invalid resource ID mapping.'];
            }
            if (!self::source_urls_valid($record['source_urls'])) return ['valid' => false, 'error' => 'Verification record must contain valid HTTPS source URLs.'];
            $verification_ids[$record['verification_id']] = true;
            $verification_records[$record['verification_id']] = $record;
        }

        $resource_ids = [];
        foreach ($data['resources'] as $resource) {
            foreach (['resource_id','country_id','number','display_name','verification_id','status','coverage'] as $key) {
                if (empty($resource[$key])) return ['valid' => false, 'error' => 'Resource missing required fields.'];
            }
            if (isset($resource_ids[$resource['resource_id']])) return ['valid' => false, 'error' => 'Duplicate resource ID.'];
            $resource_ids[$resource['resource_id']] = true;
            if (!isset($country_ids[strtoupper((string)$resource['country_id'])])) return ['valid' => false, 'error' => 'Resource references unknown country.'];
            if (!is_array($resource['service_types'] ?? null) || empty($resource['service_types'])) return ['valid' => false, 'error' => 'Resource has no service types.'];
            if (!isset($verification_ids[$resource['verification_id']])) return ['valid' => false, 'error' => 'Resource has no verification record.'];
            if (!self::verification_provenance_valid($verification_records[$resource['verification_id']], $resource['resource_id'])) {
                return ['valid' => false, 'error' => 'Resource is not explicitly mapped to its verification sources.'];
            }
            if (!in_array($resource['status'], ['active','retired'], true)) return ['valid' => false, 'error' => 'Resource has invalid status.'];
            if (!in_array($resource['coverage'], ['national','regional','local'], true)) return ['valid' => false, 'error' => 'Resource has invalid coverage.'];
            if (($resource['coverage'] !== 'national') && empty($resource['region_id'])) return ['valid' => false, 'error' => 'Regional or local resource missing region ID.'];
        }

        foreach ($verification_records as $record) {
            foreach ($record['resource_ids'] as $mapped_resource_id) {
                if (!isset($resource_ids[$mapped_resource_id])) return ['valid' => false, 'error' => 'Verification record references an unknown resource.'];
            }
        }

        return ['valid' => true, 'error' => null];
    }
}
