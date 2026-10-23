<?php
/**
 * Plugin Name: Living Archive Canonical Evidence Bridge
 * Description: Read-only, bounded text access for published Living Archive resources.
 * Version: 0.1.0
 * Author: Life.Understood.
 */

if (!defined('ABSPATH')) {
    exit;
}

add_action('rest_api_init', function () {
    register_rest_route('living-archive/v1', '/canonical-evidence/(?P<id>\d+)', [
        'methods' => WP_REST_Server::READABLE,
        'permission_callback' => '__return_true',
        'args' => [
            'id' => [
                'validate_callback' => function ($value) {
                    return is_numeric($value) && (int) $value > 0;
                },
            ],
        ],
        'callback' => function (WP_REST_Request $request) {
            $post_id = absint($request->get_param('id'));
            $post = get_post($post_id);

            if (
                !$post ||
                $post->post_status !== 'publish' ||
                post_password_required($post)
            ) {
                return new WP_Error(
                    'canonical_resource_not_found',
                    'Published canonical resource not found.',
                    ['status' => 404]
                );
            }

            $post_type = get_post_type_object($post->post_type);
            if (!$post_type || !is_post_type_viewable($post_type)) {
                return new WP_Error(
                    'canonical_resource_not_found',
                    'Published canonical resource not found.',
                    ['status' => 404]
                );
            }

            // Read stored published content directly. Do not run the_content
            // filters, render the theme, or execute shortcodes.
            $content = (string) $post->post_content;
            $content = preg_replace(
                '/<\/(?:p|h[1-6]|li|blockquote|div|section|article|tr)>/i',
                "\n",
                $content
            );
            $content = preg_replace('/<!--.*?-->/s', ' ', $content);
            $content = strip_shortcodes($content);
            $content = wp_strip_all_tags($content, false);
            $content = html_entity_decode(
                $content,
                ENT_QUOTES | ENT_HTML5,
                get_bloginfo('charset') ?: 'UTF-8'
            );
            $content = preg_replace('/[ \t\x{00A0}]+/u', ' ', $content);
            $content = preg_replace('/\s*\n\s*/u', "\n", $content);
            $content = preg_replace('/\n{3,}/', "\n\n", $content);
            $content = trim($content);

            $content_length = function_exists('mb_strlen')
                ? mb_strlen($content, 'UTF-8')
                : strlen($content);

            if ($content_length < 80) {
                return new WP_Error(
                    'canonical_resource_body_unavailable',
                    'Published resource does not contain enough readable text.',
                    ['status' => 404]
                );
            }

            $limit = 20000;
            $truncated = $content_length > $limit;
            $bounded_text = function_exists('mb_substr')
                ? mb_substr($content, 0, $limit, 'UTF-8')
                : substr($content, 0, $limit);

            $response = rest_ensure_response([
                'id' => $post_id,
                'title' => get_the_title($post),
                'url' => get_permalink($post),
                'text' => $bounded_text,
                'text_length' => function_exists('mb_strlen')
                    ? mb_strlen($bounded_text, 'UTF-8')
                    : strlen($bounded_text),
                'truncated' => $truncated,
                'modified_gmt' => $post->post_modified_gmt,
                'source' => 'published_wordpress_content',
            ]);
            $response->header('Cache-Control', 'public, max-age=300');
            return $response;
        },
    ]);
});
