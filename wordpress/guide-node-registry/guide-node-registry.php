<?php
/**
 * Plugin Name: Guide Node Registry
 * Description: Structural registry and navigation inspection boundary for The Guide.
 * Version: 0.1.2-draft
 * Author: Life.Understood.
 *
 * This plugin is intentionally non-intelligent. WordPress remains the
 * authoritative structural source. The Guide/USE consumes approved nodes.
 */

if ( ! defined( 'ABSPATH' ) ) {
    exit;
}

define( 'LA_GUIDE_NODE_REGISTRY_VERSION', 'v1' );
define( 'LA_GUIDE_NODE_REGISTRY_SCHEMA', 'v1' );

function la_guide_node_registry_records() {
    return array(
        array(
            'node_id'             => 'fractal-systems-diagnostic',
            'title'               => 'Fractal Systems Diagnostic',
            'branch'              => 'STEWARD JOURNEYS',
            'parent'              => 'Steward Journeys',
            'purpose'             => 'Locate where a human system is getting stuck and identify places worth examining next.',
            'asset_type'          => 'diagnostic',
            'canonical_url'       => 'https://geralddaquila.com/fractal-systems-diagnostic-2/',
            'access_class'        => 'public',
            'status'              => 'active',
            'menu_depth'          => 2,
            'discovery_priority'  => 'high',
            'semantic_hints'      => array( 'systems problem', 'organizational difficulty', 'stuck system', 'system pattern' ),
        ),
        array(
            'node_id'             => 'living-glossary',
            'title'               => 'Living Glossary',
            'branch'              => 'Resources',
            'parent'              => 'Resources',
            'purpose'             => 'Provide the Archive’s bounded meanings for recurring terms and concepts.',
            'asset_type'          => 'reference_system',
            'canonical_url'       => 'https://geralddaquila.com/glossary/',
            'access_class'        => 'public',
            'status'              => 'active',
            'menu_depth'          => 3,
            'discovery_priority'  => 'high',
            'semantic_hints'      => array( 'definition', 'what does this term mean', 'archive vocabulary', 'meaning of a term' ),
        ),
        array(
            'node_id'             => 'guardian-glyph-archives',
            'title'               => 'Guardian Glyph Archives',
            'branch'              => 'Resources',
            'parent'              => 'Glyph Atlas',
            'purpose'             => 'Explore the Archive’s glyph-based symbolic reference material through its native search experience.',
            'asset_type'          => 'searchable_archive',
            'canonical_url'       => 'https://geralddaquila.com/guardian-glyph-archives/',
            'access_class'        => 'public',
            'status'              => 'active',
            'menu_depth'          => 2,
            'discovery_priority'  => 'high',
            'semantic_hints'      => array( 'glyph', 'symbol', 'guardian glyph', 'glyph archive' ),
        ),
        array(
            'node_id'             => 'philippine-systems',
            'title'               => 'Philippine Systems, Society, and Culture',
            'branch'              => 'Core Pathways',
            'parent'              => 'Governance & Philippine Systems',
            'purpose'              => 'Explore Philippine society, culture, history, institutions, and systemic transformation.',
            'asset_type'          => 'knowledge_hub',
            'canonical_url'       => 'https://geralddaquila.com/understanding-the-philippines-culture-society-history-and-systemic-transformation/',
            'access_class'        => 'public',
            'status'              => 'active',
            'menu_depth'          => 3,
            'discovery_priority'  => 'high',
            'semantic_hints'      => array( 'Philippines', 'Filipino society', 'Philippine systems', 'culture', 'governance' ),
        ),
        array(
            'node_id'             => 'philippine-renewal-framework',
            'title'               => 'Philippine Renewal Framework',
            'branch'              => 'Knowledge Hubs',
            'parent'              => 'Knowledge Hubs',
            'purpose'              => 'Provide a systems-oriented framework for civic renewal, institutional trust, and long-term national stewardship.',
            'asset_type'          => 'knowledge_hub',
            'canonical_url'       => 'https://geralddaquila.com/2026/09/21/philippine-renewal-framework/',
            'access_class'        => 'public',
            'status'              => 'active',
            'menu_depth'          => 3,
            'discovery_priority'  => 'high',
            'semantic_hints'      => array( 'Philippine renewal', 'civic renewal', 'institutional trust', 'national stewardship' ),
        ),
        array(
            'node_id'             => 'access-institute-case-library',
            'title'               => 'Access the Institute Case Library',
            'branch'              => 'Steward Case Library (Micro)',
            'parent'              => 'Steward Case Library (Micro)',
            'purpose'              => 'Help visitors choose the appropriate entry pathway into the Institute case-learning ecosystem.',
            'asset_type'          => 'access_gateway',
            'canonical_url'       => 'https://geralddaquila.com/how-to-access-the-case-studies/',
            'access_class'        => 'mixed',
            'status'              => 'active',
            'menu_depth'          => 3,
            'discovery_priority'  => 'high',
            'semantic_hints'      => array( 'case library', 'leadership case', 'learning path', 'case study access' ),
        ),
        array(
            'node_id'             => 'leadership-challenge-navigator',
            'title'               => 'Leadership Challenge Navigator',
            'branch'              => 'Steward Case Library (Micro)',
            'parent'              => 'Steward Case Library (Micro)',
            'purpose'             => 'Help readers recognize the stewardship pattern beneath a present leadership, governance, institutional, or systems challenge before selecting cases or Learning Arcs.',
            'asset_type'          => 'navigator',
            'canonical_url'       => 'https://geralddaquila.com/leadership-challenge-navigator/',
            'access_class'        => 'public',
            'status'              => 'active',
            'menu_depth'          => 3,
            'discovery_priority'  => 'high',
            'semantic_hints'      => array( 'leadership challenge', 'leadership problem', 'governance challenge', 'systems challenge', 'leadership case', 'case studies', 'recurring pattern' ),
        ),
        array(
            'node_id'             => 'steward-readiness-instruments',
            'title'               => 'Steward Readiness Instruments',
            'branch'              => 'Stewardship Framework',
            'parent'              => 'Stewardship Readiness',
            'purpose'             => 'Provide the Archive’s developmental instruments for reflective assessment, behavioral calibration, relational accountability, and stewardship under institutional responsibility.',
            'asset_type'          => 'assessment_suite',
            'canonical_url'       => 'https://geralddaquila.com/stewardship-readiness/',
            'access_class'        => 'mixed',
            'status'              => 'active',
            'menu_depth'          => 3,
            'discovery_priority'  => 'high',
            'semantic_hints'      => array( 'steward readiness', 'stewardship readiness instruments', 'SRI', 'SRI-16', 'SRI-24', 'stewardship assessment', 'readiness assessment', 'assessment instruments' ),
        ),
        array(
            'node_id'             => 'learning-arcs',
            'title'               => 'Learning Arcs',
            'branch'              => 'Steward Case Library (Micro)',
            'parent'              => 'Steward Case Library (Micro)',
            'purpose'              => 'Guide readers through sequenced case-based learning around recurring stewardship patterns.',
            'asset_type'          => 'learning_pathway',
            'canonical_url'       => 'https://geralddaquila.com/steward-access-12-learning-arcs/',
            'access_class'        => 'steward',
            'status'              => 'active',
            'menu_depth'          => 3,
            'discovery_priority'  => 'high',
            'semantic_hints'      => array( 'learning arc', 'recurring leadership pattern', 'case sequence', 'stewardship learning' ),
        ),
        array(
            'node_id'             => 'stewardship-case-atlas',
            'title'               => 'Stewardship Case Atlas',
            'branch'              => 'Steward Case Library (Micro)',
            'parent'              => 'Steward Case Library (Micro)',
            'purpose'             => 'Provide the complete structured case-learning environment across leadership and governance dilemmas.',
            'asset_type'          => 'case_library',
            'canonical_url'       => 'https://geralddaquila.com/stewardship-case-atlas/',
            'access_class'        => 'purchase',
            'status'              => 'active',
            'menu_depth'          => 3,
            'discovery_priority'  => 'high',
            'semantic_hints'      => array( 'case atlas', 'leadership cases', 'governance cases', '48 case studies', '12 learning arcs' ),
        ),
        array(
            'node_id'             => 'applied-stewardship-toolkit',
            'title'               => 'Applied Stewardship Toolkit',
            'branch'              => 'Stewardship Practice',
            'parent'              => 'Stewardship Practice',
            'purpose'             => 'Provide practical governance instruments and templates for intentional communities and stewardship practice.',
            'asset_type'          => 'toolkit',
            'canonical_url'       => 'https://geralddaquila.com/applied-toolkit-governance-layers/',
            'access_class'        => 'public',
            'status'              => 'active',
            'menu_depth'          => 3,
            'discovery_priority'  => 'normal',
            'semantic_hints'      => array( 'governance toolkit', 'community governance', 'governance templates', 'stewardship tools' ),
        ),
    );
}

function la_guide_node_registry_validate( $record ) {
    $required = array(
        'node_id',
        'title',
        'branch',
        'purpose',
        'asset_type',
        'canonical_url',
        'access_class',
        'status',
    );

    foreach ( $required as $field ) {
        if ( empty( $record[ $field ] ) ) {
            return new WP_Error(
                'guide_node_invalid',
                'Guide Node is missing required field: ' . $field
            );
        }
    }

    if ( 'active' !== $record['status'] ) {
        return new WP_Error( 'guide_node_inactive', 'Guide Node is not active.' );
    }

    $parts = wp_parse_url( $record['canonical_url'] );
    if (
        empty( $parts['scheme'] ) ||
        'https' !== strtolower( $parts['scheme'] ) ||
        empty( $parts['host'] ) ||
        'geralddaquila.com' !== strtolower( $parts['host'] )
    ) {
        return new WP_Error(
            'guide_node_external_url',
            'Guide Node canonical URL must remain inside the public Archive.'
        );
    }

    return true;
}

function la_guide_node_registry_response( WP_REST_Request $request ) {
    $records = la_guide_node_registry_records();
    $active  = array();

    foreach ( $records as $record ) {
        $valid = la_guide_node_registry_validate( $record );
        if ( is_wp_error( $valid ) ) {
            continue;
        }
        $active[] = $record;
    }

    return rest_ensure_response(
        array(
            'ok'                       => true,
            'registry_version'         => LA_GUIDE_NODE_REGISTRY_VERSION,
            'schema_version'           => LA_GUIDE_NODE_REGISTRY_SCHEMA,
            'source'                   => 'wordpress',
            'authority'                => 'canonical',
            'node_count'               => count( $active ),
            'nodes'                    => $active,
        )
    );
}

function la_guide_navigation_walk_blocks( $blocks, $parent_id = null, $depth = 0 ) {
    $items = array();

    foreach ( (array) $blocks as $block ) {
        if ( empty( $block['blockName'] ) ) {
            continue;
        }

        $name = $block['blockName'];
        if ( 'core/navigation-link' === $name ) {
            $attrs = isset( $block['attrs'] ) && is_array( $block['attrs'] )
                ? $block['attrs']
                : array();

            $items[] = array(
                'source'     => 'wp_navigation',
                'item_type'  => 'link',
                'title'      => isset( $attrs['label'] ) ? wp_strip_all_tags( $attrs['label'] ) : '',
                'url'        => isset( $attrs['url'] ) ? esc_url_raw( $attrs['url'] ) : '',
                'parent_id'  => $parent_id,
                'depth'      => $depth,
            );
        }

        $child_parent = $parent_id;
        if ( 'core/navigation-submenu' === $name ) {
            $child_parent = md5( wp_json_encode( $block ) );
        }

        if ( ! empty( $block['innerBlocks'] ) ) {
            $items = array_merge(
                $items,
                la_guide_navigation_walk_blocks(
                    $block['innerBlocks'],
                    $child_parent,
                    $depth + ( 'core/navigation-submenu' === $name ? 1 : 0 )
                )
            );
        }
    }

    return $items;
}

function la_guide_navigation_sources() {
    $sources = array();

    $locations = get_nav_menu_locations();
    foreach ( (array) $locations as $location => $menu_id ) {
        if ( ! $menu_id ) {
            continue;
        }

        $items = wp_get_nav_menu_items( $menu_id );
        $depth_by_id = array();

        foreach ( (array) $items as $menu_item ) {
            $parent_id = (int) $menu_item->menu_item_parent;
            $depth = 0;

            if ( $parent_id && isset( $depth_by_id[ $parent_id ] ) ) {
                $depth = $depth_by_id[ $parent_id ] + 1;
            }

            $depth_by_id[ (int) $menu_item->ID ] = $depth;
        }

        $sources[] = array(
            'source'   => 'classic_menu',
            'location' => $location,
            'menu_id'  => (int) $menu_id,
            'items'    => array_map(
                static function ( $item ) use ( $depth_by_id ) {
                    return array(
                        'id'         => (int) $item->ID,
                        'title'      => wp_strip_all_tags( $item->title ),
                        'url'        => esc_url_raw( $item->url ),
                        'parent_id'  => (int) $item->menu_item_parent,
                        'depth'      => isset( $depth_by_id[ (int) $item->ID ] )
                            ? (int) $depth_by_id[ (int) $item->ID ]
                            : 0,
                    );
                },
                (array) $items
            ),
        );
    }

    if ( post_type_exists( 'wp_navigation' ) ) {
        $navigation_posts = get_posts(
            array(
                'post_type'      => 'wp_navigation',
                'post_status'    => 'publish',
                'posts_per_page' => -1,
            )
        );

        foreach ( $navigation_posts as $navigation ) {
            $sources[] = array(
                'source'   => 'wp_navigation',
                'id'       => (int) $navigation->ID,
                'title'    => wp_strip_all_tags( $navigation->post_title ),
                'items'    => la_guide_navigation_walk_blocks(
                    parse_blocks( $navigation->post_content )
                ),
            );
        }
    }

    return $sources;
}

function la_guide_navigation_response( WP_REST_Request $request ) {
    return rest_ensure_response(
        array(
            'ok'               => true,
            'registry_version' => LA_GUIDE_NODE_REGISTRY_VERSION,
            'source'           => 'wordpress',
            'authority'        => 'structural',
            'sources'          => la_guide_navigation_sources(),
        )
    );
}

function la_guide_node_registry_register_routes() {
    register_rest_route(
        'guide/v1',
        '/nodes',
        array(
            'methods'             => WP_REST_Server::READABLE,
            'callback'            => 'la_guide_node_registry_response',
            'permission_callback' => '__return_true',
        )
    );

    register_rest_route(
        'guide/v1',
        '/navigation',
        array(
            'methods'             => WP_REST_Server::READABLE,
            'callback'            => 'la_guide_navigation_response',
            'permission_callback' => '__return_true',
        )
    );
}

add_action( 'rest_api_init', 'la_guide_node_registry_register_routes' );
