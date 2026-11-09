<?php
if (!defined('ABSPATH')) exit;

class LAEI_Resource_Selector {
    public static function select($service_need, $location, $safety_state = 'unknown') {
        $service_need = sanitize_key($service_need);
        $service_aliases = [
            'emergency' => 'general_emergency',
            'emergency_medical' => 'medical',
            'medical_emergency' => 'medical',
            'crisis' => 'crisis_support',
            'mental_health' => 'mental_health_support',
            'suicide_crisis' => 'suicidal_crisis',
        ];
        $service_need = $service_aliases[$service_need] ?? $service_need;
        $allowed_services = [
            'general_emergency','police','fire','medical','rescue','traffic',
            'crisis_support','mental_health_support','emotional_distress','suicidal_crisis',
        ];
        if (!in_array($service_need, $allowed_services, true)) {
            return self::fallback('UNKNOWN', 'invalid_service_need');
        }
        $country = strtoupper((string)($location['location']['country']['value'] ?? ''));
        $status = $location['resolution_status'] ?? 'UNKNOWN';

        if (!$country || in_array($status, ['UNKNOWN', 'REFUSED'], true)) {
            return self::fallback($status, $status === 'REFUSED' ? 'location_refused' : 'location_unknown');
        }

        if (!LAEI_Registry::get_country($country)) {
            return self::fallback($status, 'unsupported_country');
        }

        $candidates = LAEI_Registry::get_resources($country, $service_need);
        if (!$candidates) {
            return self::fallback($status, 'no_matching_service');
        }

        $eligible = [];
        $verification_failures = [];
        foreach ($candidates as $resource) {
            if (($resource['status'] ?? '') !== 'active') continue;
            $verification = LAEI_Registry::get_verification($resource['verification_id'] ?? '');
            $verification_state = self::verification_state($verification, $resource['resource_id'] ?? '');
            if (!$verification_state['current']) {
                $verification_failures[$verification_state['reason']] = true;
                continue;
            }
            if (!self::coverage_applies($resource, $location)) continue;
            $resource['_verification'] = $verification;
            $eligible[] = $resource;
        }

        if (!$eligible) {
            $reason = 'no_eligible_resource';
            foreach ([
                'verification_expired',
                'verification_future_dated',
                'verification_invalid_dates',
                'verification_provenance_missing',
                'verification_unverified',
                'verification_missing',
            ] as $candidate_reason) {
                if (isset($verification_failures[$candidate_reason])) {
                    $reason = $candidate_reason;
                    break;
                }
            }
            return self::fallback($status, $reason);
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

    private static function verification_state($verification, $resource_id) {
        if (!is_array($verification)) return ['current' => false, 'reason' => 'verification_missing'];
        if (($verification['status'] ?? '') !== 'verified') return ['current' => false, 'reason' => 'verification_unverified'];
        if (!LAEI_Registry::verification_provenance_valid($verification, $resource_id)) {
            return ['current' => false, 'reason' => 'verification_provenance_missing'];
        }

        $verified_at = (string)($verification['verified_at'] ?? '');
        $review_due = (string)($verification['review_due'] ?? '');
        $verified_timestamp = self::utc_date_timestamp($verified_at, false);
        $review_timestamp = self::utc_date_timestamp($review_due, true);
        if ($verified_timestamp === false || $review_timestamp === false || $review_timestamp < $verified_timestamp) {
            return ['current' => false, 'reason' => 'verification_invalid_dates'];
        }

        $now = (int)current_time('timestamp', true);
        if ($verified_timestamp > $now) return ['current' => false, 'reason' => 'verification_future_dated'];
        if ($review_timestamp < $now) return ['current' => false, 'reason' => 'verification_expired'];

        return ['current' => true, 'reason' => null];
    }

    private static function utc_date_timestamp($value, $end_of_day = false) {
        if (!preg_match('/^\d{4}-\d{2}-\d{2}$/', $value)) return false;
        $date = DateTimeImmutable::createFromFormat('!Y-m-d', $value, new DateTimeZone('UTC'));
        $errors = DateTimeImmutable::getLastErrors();
        if (!$date || ($errors && ($errors['warning_count'] > 0 || $errors['error_count'] > 0))) return false;
        if ($date->format('Y-m-d') !== $value) return false;
        if ($end_of_day) $date = $date->setTime(23, 59, 59);
        return $date->getTimestamp();
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
        if ($reason === 'verification_future_dated') $selection_status = 'VERIFICATION_FUTURE_DATED';
        if ($reason === 'verification_invalid_dates') $selection_status = 'VERIFICATION_INVALID';
        if ($reason === 'verification_provenance_missing') $selection_status = 'VERIFICATION_PROVENANCE_MISSING';
        if ($reason === 'verification_unverified') $selection_status = 'VERIFICATION_UNVERIFIED';
        if ($reason === 'verification_missing') $selection_status = 'VERIFICATION_MISSING';
        if ($reason === 'invalid_service_need') $selection_status = 'INVALID_SERVICE_NEED';

        return [
            'selection_status' => $selection_status,
            'failure_reason' => $reason,
            'primary' => null,
            'secondary' => [],
            'location' => null,
        ];
    }
}
