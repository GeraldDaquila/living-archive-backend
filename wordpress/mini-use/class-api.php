<?php
if(!defined('ABSPATH'))exit;
class Mini_Use_API{
 public static function init(){
  add_action('rest_api_init',function(){
   $args=['methods'=>'POST','permission_callback'=>'__return_true','callback'=>[__CLASS__,'navigate'],'args'=>['query'=>['required'=>true,'type'=>'string','sanitize_callback'=>'sanitize_text_field']]];
   register_rest_route('mini-use/v1','/navigate',$args);
   register_rest_route('mini-use/v1','/health',['methods'=>'GET','permission_callback'=>'__return_true','callback'=>[__CLASS__,'health']]);
   register_rest_route('mini-use/v1','/catalogue/stats',['methods'=>'GET','permission_callback'=>'__return_true','callback'=>[__CLASS__,'stats']]);
  });
  add_action('init',function(){add_rewrite_rule('^api/navigate/?$','index.php?mini_use_route=navigate','top');add_rewrite_rule('^api/health/?$','index.php?mini_use_route=health','top');add_rewrite_rule('^api/catalogue/stats/?$','index.php?mini_use_route=stats','top');});
  add_filter('query_vars',function($vars){$vars[]='mini_use_route';return $vars;});
  add_action('template_redirect',[__CLASS__,'legacy_route']);
 }
 public static function assets(){
  wp_enqueue_script('mini-use-js',MINI_USE_URL.'assets/mini-use.js',['la-answer-doorway-standard'],MINI_USE_VERSION,true);
  wp_enqueue_style('mini-use-css',MINI_USE_URL.'assets/mini-use.css',[],MINI_USE_VERSION);
 }
 public static function legacy_route(){
  $route=get_query_var('mini_use_route');
  if(!$route)return;
  nocache_headers();header('Content-Type: application/json; charset='.get_option('blog_charset','UTF-8'));
  if($route==='navigate'){
   if(strtoupper($_SERVER['REQUEST_METHOD']??'GET')!=='POST'){status_header(405);echo wp_json_encode(['code'=>'method_not_allowed','message'=>'POST required']);exit;}
   $raw=file_get_contents('php://input');$body=json_decode($raw,true);$query=is_array($body)?($body['query']??''):'';
   $request=new WP_REST_Request('POST','/mini-use/v1/navigate');$request->set_param('query',$query);$result=self::navigate($request);self::emit($result);exit;
  }
  if($route==='health'){self::emit(self::health());exit;}
  if($route==='stats'){self::emit(self::stats());exit;}
 }
 private static function emit($result){if(is_wp_error($result)){status_header($result->get_error_data()['status']??500);echo wp_json_encode(['code'=>$result->get_error_code(),'message'=>$result->get_error_message()]);return;}echo wp_json_encode($result);}
 private static function backend_request($path,$method='GET',$payload=null,$timeout=25){
  $base=defined('MINI_USE_BACKEND_URL')?MINI_USE_BACKEND_URL:'https://mini-use-payhip.onrender.com';
  $url=rtrim((string)$base,'/').$path;
  $args=['timeout'=>max(1,(int)$timeout),'redirection'=>0,'headers'=>['Accept'=>'application/json']];
  if(strtoupper($method)==='POST'){
   $args['headers']['Content-Type']='application/json';
   $args['body']=wp_json_encode(is_array($payload)?$payload:[]);
   $response=wp_remote_post($url,$args);
  }else{
   $response=wp_remote_get($url,$args);
  }
  if(is_wp_error($response))return new WP_Error('mini_use_backend_unavailable','The Catalogue is temporarily unavailable. Please try again shortly.',['status'=>503,'backend'=>'mini-use-payhip']);
  $status=(int)wp_remote_retrieve_response_code($response);
  $data=json_decode((string)wp_remote_retrieve_body($response),true);
  if($status===404){
   $detail=is_array($data)&&isset($data['detail'])&&is_array($data['detail'])?$data['detail']:[];
   $message=isset($detail['message'])&&is_scalar($detail['message'])?sanitize_text_field((string)$detail['message']):'';
   if($message==='')$message='No validated Catalogue contribution found for this question.';
   if(strlen($message)>180)$message=substr($message,0,180);
   return new WP_Error('mini_use_no_catalogue_fit',$message,['status'=>404,'backend_status'=>404,'backend'=>'mini-use-payhip']);
  }
  if($status<200||$status>=300)return new WP_Error('mini_use_backend_http_error','The Catalogue is temporarily unavailable. Please try again shortly.',['status'=>$status>=500?503:502,'backend_status'=>$status,'backend'=>'mini-use-payhip']);
  if(!is_array($data))return new WP_Error('mini_use_backend_invalid_json','The Catalogue returned an invalid response. Please try again shortly.',['status'=>502,'backend'=>'mini-use-payhip']);
  return $data;
 }

 public static function navigate($r) {
  if (!self::allow_request()) return new WP_Error('rate_limited','Too many requests. Please wait a moment and try again.',['status'=>429]);
  $query=trim((string)$r->get_param('query'));
  if($query==='')return new WP_Error('empty_query','A query is required',['status'=>400]);
  $length=function_exists('mb_strlen')?mb_strlen($query):strlen($query);
  if($length>1200)return new WP_Error('query_too_long','Please keep the question under 1,200 characters.',['status'=>400]);
  $result=self::backend_request('/api/navigate','POST',['query'=>$query],45);
  if(is_wp_error($result))return $result;
  if(!isset($result['doors'])||!is_array($result['doors'])||!isset($result['synthesis'])||!is_string($result['synthesis'])){
   return new WP_Error('mini_use_backend_contract_error','The Catalogue returned an incomplete result. Please try again shortly.',['status'=>502,'backend'=>'mini-use-payhip']);
  }
  return $result;
 }
 private static function valid_overview($text){
  $text=trim((string)$text);
  if($text===''||mb_strlen($text)>360)return false;
  if(preg_match('/(?:resource type:|terrain:|movement:|human terrain|for questions around|this resource provides|this may help|catalogue analyst)/i',$text))return false;
  $words=preg_match_all('/\b[\p{L}\p{N}][\p{L}\p{N}\x27-]*\b/u',$text,$m);
  return $words>=8&&$words<=45;
 }
 private static function allow_request(){if(!function_exists('get_transient'))return true;$ip=$_SERVER['REMOTE_ADDR']??'unknown';$key='mini_use_rl_'.md5($ip);$count=(int)get_transient($key);if($count>=12)return false;set_transient($key,$count+1,60);return true;}
 public static function health(){
  $health=self::backend_request('/health','GET',null,25);
  if(is_wp_error($health))return new WP_Error('mini_use_backend_unavailable','The Catalogue backend is temporarily unavailable.',['status'=>503,'adapter_version'=>MINI_USE_VERSION]);
  $health['adapter_version']=MINI_USE_VERSION;
  $health['backend']='mini-use-payhip';
  $health['backend_url']=rtrim(defined('MINI_USE_BACKEND_URL')?MINI_USE_BACKEND_URL:'https://mini-use-payhip.onrender.com','/');
  return $health;
 }
 public static function stats(){
  return self::backend_request('/api/catalogue/stats','GET',null,25);
 }
 private static function type($a){$rf=(array)($a['resource_function']??[]);if(array_intersect(['case-based','case-based learning','facilitation','field practice'],$rf))return 'practice';if(in_array('reference/source text',$rf,true))return 'source';if(array_intersect(['reflection/workbook','toolkit/implementation'],$rf))return 'work';return 'orientation';}
 public static function shortcode($atts=[]){
  self::assets();
  $query_id=function_exists('wp_unique_id')?wp_unique_id('mini-use-query-'):'mini-use-query-'.wp_rand(1000,999999);
  $atts=shortcode_atts(['placeholder'=>'e.g. What are you trying to make sense of right now?'],$atts,'mini_use');
  ob_start(); ?>
  <section class="mini-use-plugin" data-endpoint="<?php echo esc_url(rest_url('mini-use/v1/navigate')); ?>">
   <div class="mini-use-shell">
    <form class="mini-use-form">
     <label class="mini-use-prompt" for="<?php echo esc_attr($query_id); ?>">Describe what you’re trying to understand.</label>
     <textarea id="<?php echo esc_attr($query_id); ?>" class="mini-use-query" rows="4" placeholder="<?php echo esc_attr($atts['placeholder']); ?>"></textarea>
     <button type="submit" class="mini-use-submit">
      <span class="mini-use-submit-label">Explore the Catalogue</span>
      <span class="mini-use-spinner" aria-hidden="true"></span>
     </button>
    </form>
    <div class="mini-use-status" aria-live="polite"></div>
    <div class="mini-use-results" hidden></div>
   </div>
  </section>
  <script>(function(){
   var loader=document.currentScript,root=loader&&loader.previousElementSibling;
   if(!root||!root.matches('.mini-use-plugin'))return;
   function boot(){if(window.MiniUsePlugin&&typeof window.MiniUsePlugin.init==='function'){window.MiniUsePlugin.init(root);return true;}return false;}
   if(boot())return;
   var script=document.createElement('script');
   script.src=<?php echo wp_json_encode(MINI_USE_URL.'assets/mini-use.js?ver='.MINI_USE_VERSION); ?>;
   script.async=true;
   script.onload=function(){if(!boot()){var status=root.querySelector('.mini-use-status');if(status)status.textContent='The catalogue search is unavailable right now. Please refresh and try again.';}};
   script.onerror=function(){var status=root.querySelector('.mini-use-status');if(status)status.textContent='The catalogue search is unavailable right now. Please refresh and try again.';};
   document.head.appendChild(script);
  })();</script>
  <?php return ob_get_clean();
 }
}
