<?php
declare(strict_types=1);

define('ABSPATH', __DIR__);
function add_action(...$args): void {}
function add_filter(...$args): void {}
function plugin_dir_url($file): string { return 'https://geralddaquila.com/wp-content/plugins/living-archive-answer-doorway-standard/'; }
function wp_parse_url($value) { return parse_url($value); }

class WP_REST_Response {
    private $data;
    public function __construct($data) { $this->data = $data; }
    public function get_data() { return $this->data; }
    public function set_data($data): void { $this->data = $data; }
}
class Test_REST_Request {
    private $route;
    public function __construct($route) { $this->route = $route; }
    public function get_route(): string { return $this->route; }
}

require __DIR__ . '/../wordpress/living-archive-answer-doorway-standard/living-archive-answer-doorway-standard.php';

$data = array(
    'selected' => array(
        array('id' => 'valid', 'title' => 'Systems and Governance', 'url' => 'https://geralddaquila.com/systems-structure/'),
        array('id' => 'generic', 'title' => 'Generic', 'url' => 'https://geralddaquila.com/generic/'),
        array('id' => 'external', 'title' => 'External', 'url' => 'https://evil.example/resource/'),
        array('id' => 'query', 'title' => 'Query', 'url' => 'https://geralddaquila.com/resource/?next=https://evil.example/'),
        array('id' => 'port', 'title' => 'Port', 'url' => 'https://geralddaquila.com:8443/resource/')
    ),
    'why_each' => array(
        'valid' => 'This resource examines system structure and governance arrangements.',
        'generic' => 'There is something here worth staying with.',
        'external' => 'This rationale is otherwise grounded.',
        'query' => 'This rationale is otherwise grounded.',
        'port' => 'This rationale is otherwise grounded.'
    ),
    'reflection' => 'A distinct reflection remains unchanged.'
);

$response = new WP_REST_Response($data);
$result = la_answer_doorway_filter_rest_response($response, null, new Test_REST_Request('/stewardship/v1/pathway'));
$filtered = $result->get_data();
if (count($filtered['selected']) !== 1 || $filtered['selected'][0]['id'] !== 'valid') {
    throw new RuntimeException('SPE response filter did not retain only the verified doorway.');
}
if (array_keys($filtered['why_each']) !== array('valid')) {
    throw new RuntimeException('SPE response filter did not reconcile why_each with selected destinations.');
}
if ($filtered['reflection'] !== $data['reflection']) {
    throw new RuntimeException('SPE response filter changed the module reflection.');
}

$navigator = new WP_REST_Response($data);
$navigator = la_answer_doorway_filter_rest_response($navigator, null, new Test_REST_Request('/living-archive/v1/navigate'));
if (count($navigator->get_data()['selected']) !== 1) {
    throw new RuntimeException('Navigator response filter did not apply the shared doorway contract.');
}

$unrelated = new WP_REST_Response($data);
$unrelated = la_answer_doorway_filter_rest_response($unrelated, null, new Test_REST_Request('/unrelated/v1/route'));
if (count($unrelated->get_data()['selected']) !== 5) {
    throw new RuntimeException('Shared filter altered an unrelated REST route.');
}

fwrite(STDOUT, "ANSWER DOORWAY REST FILTER TEST: PASS\n");
