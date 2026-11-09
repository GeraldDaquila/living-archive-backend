<?php
if (!defined('ABSPATH')) exit;

class LAEI_Resource_Selector {
    public static function select($service_need, $location, $safety_state = 'unknown') {
        $service_need = sanitize_key($service_need);
        $country = strtoupper((string)($location['location']['country']['value'] ?? ''));
        $status = $location['resolution_status'] ?? 'UNKNOWN';

        if (!$country || in_array($status, ['UNKNOWN', 'REFUSED'], true)) {
            return self::fallback($status);
        }

        $candidates = LAEI_Registry::get_resources($country, $service_need);
        if (!$candidates && $service_need === 'emergency') {
            $candidates = LAEI_Registry::get_resources($country, 'general_emergency');
        }

        $eligible = [];
        foreach ($candidates as $resource) {
            $verification = LAEI_Registry::get_verification($resource['verification_id'] ?? '');
            if (($verification['status'] ?? '') !== 'verified') continue;
            if (($resource['status'] ?? '') !== 'active') continue;
            if (!self::coverage_applies($resource, $location)) continue;
            $resource['_verification'] = $verification;
            $eligible[] = $resource;
        }

        if (!$eligible) return self::fallback($status);

        usort($eligible, function($a, $b) {
            return (int)($b['presentation_priority'] ?? 0) <=> (int)($a['presentation_priority'] ?? 0);
        });

        $equivalence = [];
        foreach ($eligible as $resource) {
            $group = $resource['equivalence_group'] ?? null;
            if ($group) $equivalence[$group][] = $resource;
        }
        if ($equivalence) {
            foreach ($equivalence as $group => $resources) {
                if (count($resources) > 1) {
                    return [
                        'selection_status' => 'MULTIPLE_EQUIVALENT',
                        'primary' => array_slice($resources, 0, 2),
                        'secondary' => [],
                        'equivalence_group' => $group,
                        'location' => $location,
                    ];
                }
            }
        }

        return [
            'selection_status' => 'SELECTED',
            'primary' => $eligible[0],
            'secondary' => [],
            'location' => $location,
            'resource_selection_confidence' => $location['resource_selection_confidence'] ?? 'unknown',
        ];
    }

    private static function coverage_applies($resource, $location) {
        $coverage = $resource['coverage'] ?? 'national';
        if ($coverage === 'national') return true;
        $region = strtoupper((string)($location['location']['region']['value'] ?? ''));
        return $region !== '' && strtoupper((string)($resource['region_id'] ?? '')) === $region;
    }

    private static function fallback($status) {
        return [
            'selection_status' => $status === 'UNKNOWN' ? 'LOCATION_REQUIRED' : 'FALLBACK_GENERAL_EMERGENCY',
            'primary' => null,
            'secondary' => [],
            'location' => null,
        ];
    }
}
