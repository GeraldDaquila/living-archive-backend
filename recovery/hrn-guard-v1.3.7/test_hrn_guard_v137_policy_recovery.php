<?php
declare(strict_types=1);
define('ABSPATH', __DIR__);
$GLOBALS['test_filters'] = [];
function add_filter($hook, $callback, $priority = 10, $accepted_args = 1) { $GLOBALS['test_filters'][$hook] = $callback; }
class WP_REST_Request {
    private array $params; private string $route; private string $method;
    public function __construct(array $params, string $route='/living-archive/v1/relational-navigator', string $method='POST') { $this->params=$params; $this->route=$route; $this->method=$method; }
    public function get_method() { return $this->method; }
    public function get_route() { return $this->route; }
    public function get_param($key) { return $this->params[$key] ?? null; }
}
class WP_REST_Response {
    private array $data; private int $status;
    public function __construct(array $data, int $status) { $this->data=$data; $this->status=$status; }
    public function get_data() { return $this->data; }
    public function set_data($data) { $this->data=$data; }
    public function get_status() { return $this->status; }
    public function set_status($status) { $this->status=$status; }
}
function check(bool $ok, string $message): void { if (!$ok) { fwrite(STDERR, "FAIL: {$message}\n"); exit(1); } }
require __DIR__ . '/living-archive-hrn-composition-contract-guard.php';
$guard = $GLOBALS['test_filters']['rest_post_dispatch'] ?? null;
check(is_callable($guard), 'REST response guard registered');
$input = 'I keep putting off a conversation with a friend because I am afraid it will change the friendship.';
$request = new WP_REST_Request(['message'=>$input, 'unit_turns'=>1]);
$rejected = new WP_REST_Response([
    'ok'=>false, 'version'=>'0.5.332', 'error_type'=>'retryable_operation_failure',
    'operation'=>'round_response_composition', 'reason'=>'composition_policy_rejected',
    'retryable'=>true, 'response'=>'', 'message'=>'The conversation could not be composed right now. Please try again.',
    'status'=>503, 'meta'=>['policy_rejections'=>[['provider'=>'provider_bank','reason'=>'visitor_surface_policy_rejected']]]
], 503);
$fixed = $guard($rejected, null, $request);
$payload = $fixed->get_data();
check($fixed->get_status() === 200, 'recognized visitor-surface rejection recovers to bounded response');
check(($payload['ok'] ?? false) === true, 'recovered envelope is successful');
check(trim((string)($payload['response'] ?? '')) !== '', 'recovery response is non-empty');
check(trim((string)($payload['question'] ?? '')) !== '', 'recovery includes a distinct follow-up question');
check(($payload['hrn_composition_recovery'] ?? '') === 'bounded_friendship_conversation_fallback_v1', 'specific friendship-conversation fallback is selected');
check(str_contains((string)$payload['response'], 'worried that naming what is on your mind could change the friendship'), 'recovery reflects the actual stated concern');
check(str_contains((string)$payload['question'], 'What feels most important to protect'), 'follow-up explores the visitor concern without prescribing action');
check(($payload['hrn_composition_recovery_version'] ?? '') === '1.3.7', 'candidate recovery version is recorded');
$safety = new WP_REST_Response(['ok'=>false,'safety'=>'red','safety_interrupt'=>true,'reason'=>'composition_policy_rejected','status'=>503,'meta'=>['policy_rejections'=>[['reason'=>'visitor_surface_policy_rejected']]]], 503);
$safetyFixed = $guard($safety, null, $request);
check($safetyFixed->get_status() === 503, 'safety interrupt is never replaced');
check(($safetyFixed->get_data()['safety_interrupt'] ?? false) === true, 'safety interrupt is preserved');
$healthy = new WP_REST_Response(['ok'=>true,'response'=>'Original valid answer','question'=>'Original valid question','safety'=>'green'], 200);
$healthyFixed = $guard($healthy, null, $request);
check($healthyFixed->get_status() === 200, 'healthy response status unchanged');
check(($healthyFixed->get_data()['response'] ?? '') === 'Original valid answer', 'healthy response body unchanged');
check(($healthyFixed->get_data()['question'] ?? '') === 'Original valid question', 'healthy question unchanged');
$wrongReason = new WP_REST_Response(['ok'=>false,'reason'=>'composition_policy_rejected','status'=>503,'meta'=>['policy_rejections'=>[['reason'=>'other_policy_rejection']]]], 503);
$wrongReasonFixed = $guard($wrongReason, null, $request);
check($wrongReasonFixed->get_status() === 503, 'unrecognized policy rejection is not recovered');
$clientError = new WP_REST_Response(['ok'=>false,'reason'=>'composition_policy_rejected','status'=>422,'meta'=>['policy_rejections'=>[['reason'=>'visitor_surface_policy_rejected']]]], 422);
$clientErrorFixed = $guard($clientError, null, $request);
check($clientErrorFixed->get_status() === 422, 'non-5xx policy rejection is not recovered');
echo "PASS: HRN guard v1.3.7 specific friendship recovery, exact rejection match, safety exclusion, and healthy-response preservation\\n";
