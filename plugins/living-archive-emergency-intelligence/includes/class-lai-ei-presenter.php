<?php
if (!defined('ABSPATH')) exit;

class LAEI_Presenter {
    public static function present($selection, $policy = 'acute_emergency') {
        $status = $selection['selection_status'] ?? 'FALLBACK_GENERAL_EMERGENCY';
        if ($status === 'SELECTED') {
            $r = $selection['primary'];
            $number = sanitize_text_field($r['number'] ?? '');
            $name = sanitize_text_field($r['display_name'] ?? 'Emergency Services');
            $location_text = self::location_text($selection['location'] ?? null);
            return [
                'title' => $name . ' — ' . $number,
                'primary_action' => 'Call ' . $number,
                'secondary' => [],
                'location_text' => $location_text,
                'supporting_text' => $location_text ? 'If you can, tell them your location when they answer.' : '',
                'actions' => $number ? [['type' => 'tel', 'value' => $number, 'label' => 'Call ' . $number]] : [],
            ];
        }
        if ($status === 'MULTIPLE_EQUIVALENT') {
            $parts = [];
            $actions = [];
            foreach (($selection['primary'] ?? []) as $r) {
                $n = sanitize_text_field($r['number'] ?? '');
                if ($n) { $parts[] = $n; $actions[] = ['type' => 'tel', 'value' => $n, 'label' => 'Call ' . $n]; }
            }
            $numbers = implode(' or ', $parts);
            return [
                'title' => 'Emergency — ' . $numbers,
                'primary_action' => 'Call ' . $numbers,
                'secondary' => [],
                'location_text' => self::location_text($selection['location'] ?? null),
                'supporting_text' => '',
                'actions' => $actions,
            ];
        }
        if ($status === 'LOCATION_REQUIRED') {
            return [
                'title' => 'Emergency assistance',
                'primary_action' => '',
                'secondary' => [],
                'location_text' => '',
                'supporting_text' => 'I want to make sure I give you the right local number. What country are you in right now?',
                'actions' => [],
            ];
        }
        return [
            'title' => 'Emergency assistance',
            'primary_action' => '',
            'secondary' => [],
            'location_text' => '',
            'supporting_text' => 'If you may be in immediate danger, please contact your local emergency service now or go to the nearest emergency department.',
            'actions' => [],
        ];
    }

    private static function location_text($location) {
        if (!$location || !isset($location['location'])) return '';
        $l = $location['location'];
        $parts = [];
        foreach (['locality','province','region','country'] as $key) {
            $v = $l[$key]['value'] ?? '';
            if ($v) $parts[] = sanitize_text_field($v);
        }
        if (!$parts) return '';
        return 'Your current location appears to be: ' . implode(', ', $parts);
    }
}
