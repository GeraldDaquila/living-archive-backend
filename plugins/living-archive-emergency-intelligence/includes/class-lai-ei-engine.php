<?php
if (!defined('ABSPATH')) exit;

class LAEI_Engine {
    public static function resolve($service_need, $location_input = [], $safety_state = 'unknown', $presentation_policy = null) {
        // Never block the emergency path on an update check.
        LAEI_Update_Manager::maybe_check(false);

        $location = LAEI_Location_Resolver::resolve($location_input);
        $selection = LAEI_Resource_Selector::select($service_need, $location, $safety_state);
        $policy = $presentation_policy ?: (($safety_state === 'acute') ? 'acute_emergency' : 'support');
        $presentation = LAEI_Presenter::present($selection, $policy);

        return [
            'engine_version' => LAEI_VERSION,
            'registry_version' => LAEI_Registry::version(),
            'safety_state' => sanitize_key($safety_state),
            'service_need' => sanitize_key($service_need),
            'location' => $location,
            'selection' => $selection,
            'presentation' => $presentation,
        ];
    }
}
