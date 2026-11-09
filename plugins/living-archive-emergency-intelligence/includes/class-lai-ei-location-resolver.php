<?php
if (!defined('ABSPATH')) exit;

class LAEI_Location_Resolver {
    public static function resolve($input = []) {
        $input = is_array($input) ? $input : [];
        $country_candidates = [];
        $evidence = [];
        $conflicts = [];

        self::add_country($country_candidates, $evidence, $input['explicit_country'] ?? null, 'explicit_user_statement', 'high');
        self::add_country($country_candidates, $evidence, $input['browser_country'] ?? null, 'browser_geolocation', 'high');
        self::add_country($country_candidates, $evidence, $input['ip_country'] ?? null, 'ip_geolocation', 'medium');
        self::add_country($country_candidates, $evidence, $input['timezone_country'] ?? null, 'timezone', 'low');
        self::add_country($country_candidates, $evidence, $input['locale_country'] ?? null, 'language_locale', 'low');

        $status = 'UNKNOWN';
        $country = null;
        $country_confidence = 'unknown';

        if (!empty($country_candidates)) {
            usort($country_candidates, function($a, $b) { return $b['weight'] <=> $a['weight']; });
            $top = $country_candidates[0];
            $country = LAEI_Registry::resolve_country_id($top['value']);
            $country_confidence = $top['confidence'];
            if ($country === '') {
                $country = strtoupper((string)$top['value']);
                $country_confidence = 'unknown';
            }
            foreach ($country_candidates as &$candidate) {
                $resolved = LAEI_Registry::resolve_country_id($candidate['value']);
                if ($resolved !== '') $candidate['value'] = $resolved;
            }
            unset($candidate);
            $distinct = array_values(array_unique(array_map(function($x){ return $x['value']; }, $country_candidates)));
            if (count($distinct) > 1) {
                $conflicts[] = [
                    'scope' => 'country',
                    'values' => $distinct,
                    'resolution' => isset($input['explicit_country']) && trim((string)$input['explicit_country']) !== '' ? 'explicit_user_statement' : 'highest_strength_evidence'
                ];
            }
            $status = $country_confidence === 'high' ? 'RESOLVED' : 'PARTIALLY_RESOLVED';
        }

        if (!empty($input['refused'])) $status = 'REFUSED';

        $resource_confidence = 'unknown';
        if ($country) {
            $resource_confidence = self::resource_selection_confidence($country, $status);
        }

        return [
            'resolution_status' => $status,
            'location' => [
                'country' => ['value' => $country, 'confidence' => $country_confidence],
                'region' => ['value' => sanitize_text_field($input['region'] ?? ''), 'confidence' => !empty($input['region']) ? 'medium' : 'unknown'],
                'province' => ['value' => sanitize_text_field($input['province'] ?? ''), 'confidence' => !empty($input['province']) ? 'medium' : 'unknown'],
                'locality' => ['value' => sanitize_text_field($input['locality'] ?? ''), 'confidence' => !empty($input['locality']) ? 'medium' : 'unknown'],
                'address' => ['value' => sanitize_text_field($input['address'] ?? ''), 'confidence' => !empty($input['address']) ? 'medium' : 'unknown'],
            ],
            'evidence' => $evidence,
            'conflicts' => $conflicts,
            'user_confirmation' => !empty($input['user_confirmation']),
            'resource_selection_confidence' => $resource_confidence,
        ];
    }

    private static function add_country(&$candidates, &$evidence, $value, $source, $confidence) {
        if (!$value) return;
        $value = strtoupper(sanitize_text_field($value));
        // Explicit current user statements outrank all inferred location signals.
        $weights = [
            'explicit_user_statement' => 120,
            'browser_geolocation' => 100,
            'ip_geolocation' => 60,
            'timezone' => 20,
            'language_locale' => 10,
        ];
        $candidates[] = ['value' => $value, 'confidence' => $confidence, 'weight' => $weights[$source] ?? 0];
        $evidence[] = ['source' => $source, 'scope' => 'country', 'value' => $value, 'confidence' => $confidence];
    }

    private static function resource_selection_confidence($country, $status) {
        if ($status === 'REFUSED' || !$country) return 'unknown';
        $resources = LAEI_Registry::get_resources($country, 'general_emergency');
        $now = (int)current_time('timestamp', true);

        foreach ($resources as $resource) {
            if (($resource['status'] ?? '') !== 'active') continue;
            $verification = LAEI_Registry::get_verification($resource['verification_id'] ?? '');
            if (!is_array($verification) || ($verification['status'] ?? '') !== 'verified') continue;
            if (!LAEI_Registry::verification_provenance_valid($verification, $resource['resource_id'] ?? '')) continue;

            $verified_at = (string)($verification['verified_at'] ?? '');
            $review_due = (string)($verification['review_due'] ?? '');
            if (!LAEI_Registry::valid_iso_date($verified_at) || !LAEI_Registry::valid_iso_date($review_due)) continue;

            $verified = DateTimeImmutable::createFromFormat('!Y-m-d', $verified_at, new DateTimeZone('UTC'));
            $review = DateTimeImmutable::createFromFormat('!Y-m-d', $review_due, new DateTimeZone('UTC'));
            if (!$verified || !$review || $review < $verified) continue;
            if ($verified->getTimestamp() > $now || $review->setTime(23, 59, 59)->getTimestamp() < $now) continue;

            return 'high';
        }
        return 'unknown';
    }
}
