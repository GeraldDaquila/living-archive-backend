<?php
if (!defined('ABSPATH')) exit;

class LAEI_Resource_Selector {
    public static function select($service_need, $location, $safety_state = 'unknown') {
        $service_need = sanitize_key($service_need);
        $country = strtoupper((string)($location['location']['country']['value'] ?? ''));
        $status = $location['resolution_status'] ?? 'UNKNOWN';

        if (!$country || in_array($status, ['UNKNOWN', 'REFUSED'], true)) {
            return self::fallback($status, $status === 'REFUSED' ? 'location_refused' : 'location_unknown');
        }

        if (!LAEI_Registry::get_country($country)) {
            return self::fallback($status, 'unsupported_country');
        }

        $candidates = LAEI_Registry::get_resources($country, $service_need);
        if (!$candidates && $service_need === 'emergency') {
            $candidates = LAEI_Registry::get_resources($country, 'general_emergency');
        }
        if (!$candidates) {
            return self::fallback($status, 'no_matching_service');
        }

        $eligible = [];
        $expired_verification = false;
        foreach ($candidates as $resource) {
            $verification = LAEI_Registry::get_verification($resource['verification_id'] ?? '');
            if (($resource['status'] ?? '') !== 'active') continue;
            if (!self::verification_is_current($verification)) {
                if (is_array($verification) && ($verification['status'] ?? '') === 'verified') {
                    $expired_verification = true;
                }
                continue;
            }
            if (!self::coverage_applies($resource, $location)) continue;
            $resource['_verification'] = $verification;
            $eligible[] = $resource;
        }

        if (!$eligible) {
            return self::fallback($status, $expired_verification ? 'verification_expired' : 'no_eligible_resource');
        }

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
            'secondary' => array_slice($eligible, 1),
            'location' => $location,
            'resource_selection_confidence' => $location['resource_selection_confidence'] ?? 'unknown',
        ];
    }

    private static function verification_is_current($verification) {
        if (!is_array($verification) || ($verification['status'] ?? '') !== 'verified') return false;

        $verified_at = (string)($verification['verified_at'] ?? '');
        $review_due = (string)($verification['review_due'] ?? '');
        $date_pattern = '/^\\d{4}-\\d{2}-\\d{2}$/';

        if (!preg_match($date_pattern, $verified_at) || !preg_match($date_pattern, $review_due)) return false;

        $verified_timestamp = strtotime($verified_at . ' 00:00:00 UTC');
        $review_timestamp = strtotime($review_due . ' 23:59:59 UTC');
        $now = current_time('timestamp', true);

        if ($verified_timestamp === false || $review_timestamp === false) return false;
        if ($verified_timestamp > $now || $review_timestamp < $now) return false;
        if ($review_timestamp < $verified_timestamp) return false;

        return true;
    }

    private static function coverage_applies($resource, $location) {
        $coverage = $resource['coverage'] ?? 'national';
        if ($coverage === 'national') return true;
        $region = strtoupper((string)($location['location']['region']['value'] ?? ''));
        return $region !== '' && strtoupper((string)($resource['region_id'] ?? '')) === $region;
    }

    private static function fallback($status, $reason = 'no_eligible_resource') {
        $selection_status = 'FALLBACK_GENERAL_EMERGENCY';
        if ($status === 'UNKNOWN') $selection_status = 'LOCATION_REQUIRED';
        if ($status === 'REFUSED') $selection_status = 'LOCATION_REFUSED';
        if ($reason === 'unsupported_country') $selection_status = 'UNSUPPORTED_COUNTRY';
        if ($reason === 'no_matching_service') $selection_status = 'NO_MATCHING_SERVICE';
        if ($reason === 'verification_expired') $selection_status = 'VERIFICATION_EXPIRED';

        return [
            'selection_status' => $selection_status,
            'failure_reason' => $reason,
            'primary' => null,
            'secondary' => [],
            'location' => null,
        ];
    }
}
