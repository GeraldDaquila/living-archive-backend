<?php
if (!defined('ABSPATH')) { exit; }

final class LAN_Engine {
    private string $data_dir;
    private static array $groq_model_cache = [
        'models' => [],
        'last_fetch' => 0,
        'terms_required_models' => [],
        'structural_failed_models' => [],
        'request_too_large_models' => [],
        'rate_limited_until' => [],
    ];
    private ?array $runtime = null;
    private ?array $index = null;
    private ?array $relationships = null;
    private string $relationships_data_status = 'not_available_from_supplied_exports';
    private array $by_id = [];
    private array $from = [];
    private array $current_input_for_fallback = [];
    private array $current_subject_focus_tokens = [];

    public function __construct(string $data_dir) {
        $this->data_dir = rtrim($data_dir, '/\\') . DIRECTORY_SEPARATOR;
        $this->load_data();
    }

    private function load_json(string $file): array {
        $path = $this->data_dir . $file;
        if (!is_readable($path)) throw new RuntimeException('Living Archive corpus file is unavailable: ' . $file);
        $raw = file_get_contents($path);
        if ($raw === false) throw new RuntimeException('Living Archive corpus file could not be read: ' . $file);
        $data = json_decode($raw, true);
        if (!is_array($data) || json_last_error() !== JSON_ERROR_NONE) throw new RuntimeException('Living Archive corpus JSON is invalid: ' . $file);
        return $data;
    }

    private function load_data(): void {
        $this->runtime = $this->load_json('corpus-runtime.json');
        $this->index = $this->load_json('retrieval-index.json');
        $relationship_data = $this->load_json('relationships.json');
        $this->relationships = $relationship_data['relationships'] ?? [];
        $this->relationships_data_status = (string)($relationship_data['status'] ?? 'not_available_from_supplied_exports');
        foreach (($this->runtime['resources'] ?? []) as $resource) {
            if (!empty($resource['id'])) $this->by_id[(string)$resource['id']] = $resource;
        }
        foreach ($this->relationships as $relationship) {
            $from = (string)($relationship['from'] ?? '');
            if ($from !== '') $this->from[$from][] = $relationship;
        }
    }

    public function corpus_status(): array {
        return [
            'version' => (string)($this->runtime['schema_version'] ?? ''),
            'resources' => count($this->by_id),
            'relationships' => count($this->relationships),
            'relationships_status' => $this->relationships_data_status,
        ];
    }

    public function navigate(array $input, string $api_key): array {
        $choice = $this->clean((string)($input['choice'] ?? ''));
        $situation = $this->clean((string)($input['situation'] ?? ''));
        $possibility = $this->clean((string)($input['possibility'] ?? ''));
        $clarification = $this->clean((string)($input['clarification'] ?? ''));
        if ($situation === '' && $possibility === '') throw new InvalidArgumentException('A situation or possibility is required.');
        if ($api_key === '') throw new RuntimeException('The Groq API key has not been configured.');

        $raw_input = [
            'entry_choice' => $choice,
            'situation' => $situation,
            'possibility' => $possibility,
            'clarification' => $clarification,
        ];
        $this->current_input_for_fallback = $raw_input;

        try {
            $interpretation = $this->interpret($api_key, $raw_input);
        } catch (Throwable $e) {
            if (strpos(strtolower($e->getMessage()), 'rejected the configured api key') !== false) throw $e;
            $interpretation = $this->deterministic_interpretation($raw_input);
        }

        if ($clarification === '' && empty($interpretation['sufficient'])) {
            $question = $this->clean((string)($interpretation['clarifying_question'] ?? ''));
            if ($question === '') $question = 'What part of this question feels most important to understand?';
            return [
                'version' => '0.3.3', 'clarification_used' => false, 'reflection' => '', 'selected' => [], 'why_each' => [],
                'door_roles' => [], 'needs_clarification' => true, 'clarifying_question' => $question,
                'movement_type' => 'continue', 'landscape' => $this->landscape_destinations(),
            ];
        }

        // NORTH-STAR RULE: interpretation can enrich grounded retrieval, but it
        // cannot create a new semantic universe. Candidate generation begins with
        // the visitor's own words. Hidden interpretation is only a bounded boost
        // inside that grounded candidate set.
        $raw_query = implode(' ', [$situation, $possibility, $clarification]);
        $this->current_subject_focus_tokens = $this->subject_focus_tokens($raw_query);
        $candidates = $this->retrieve($raw_query, 72, $interpretation);
        $candidates = $this->expand($candidates, 60);
        $candidates = $this->balance_domains($candidates, 40);
        $candidates = array_values(array_filter($candidates, fn($c) => $this->is_eligible($c['resource'] ?? [])));
        $candidates = $this->filter_subject_relevant_candidates($candidates);
        if (count($candidates) < 3) {
            return [
                'version' => '0.3.3', 'clarification_used' => false, 'reflection' => '', 'selected' => [], 'why_each' => [],
                'door_roles' => [], 'needs_clarification' => true,
                'clarifying_question' => 'I could not identify three clearly relevant resources from that wording. Are you most interested in institutional accountability, governance, or how power and responsibility relate?',
                'movement_type' => 'continue', 'landscape' => [], 'status' => 'insufficient_relevant_evidence',
            ];
        }

        $candidate_map = [];
        foreach ($candidates as $c) $candidate_map[(string)$c['resource']['id']] = $c;

        try {
            $plan = $this->plan_path($api_key, $raw_input, $interpretation, $candidates);
        } catch (Throwable $e) {
            if (strpos(strtolower($e->getMessage()), 'rejected the configured api key') !== false) throw $e;
            $plan = $this->deterministic_plan($candidates);
        }

        $plan_issues = $this->plan_quality_issues($plan, $candidate_map);
        if ($plan_issues) {
            try {
                $repaired = $this->repair_plan($api_key, $raw_input, $interpretation, $candidates, $plan, $plan_issues);
                if (!$this->plan_quality_issues($repaired, $candidate_map)) $plan = $repaired;
            } catch (Throwable $e) {
                // Keep the validated first plan if repair is unavailable.
            }
        }

        $selected_specs = is_array($plan['selected'] ?? null) ? $plan['selected'] : [];
        $selected = [];
        $door_roles = [];
        $selected_title_keys = [];
        foreach ($selected_specs as $spec) {
            if (!is_array($spec)) continue;
            $id = (string)($spec['id'] ?? '');
            if ($id === '' || !isset($candidate_map[$id])) continue;
            $r = $candidate_map[$id]['resource'];
            if (!$this->is_eligible($r)) continue;
            $title_key = $this->display_title_key($r);
            if ($title_key !== '' && isset($selected_title_keys[$title_key])) continue;
            $selected[] = $this->public_resource($r);
            if ($title_key !== '') $selected_title_keys[$title_key] = true;
            $door_roles[$id] = (string)($spec['door'] ?? 'experience');
            if (count($selected) >= 3) break;
        }
        if (count($selected) !== 3) {
            $plan = $this->deterministic_plan($candidates);
            $selected_specs = $plan['selected'];
            $selected = [];
            $door_roles = [];
            foreach ($selected_specs as $spec) {
                $id = (string)$spec['id'];
                if (!isset($candidate_map[$id])) continue;
                $selected[] = $this->public_resource($candidate_map[$id]['resource']);
                $door_roles[$id] = (string)($spec['door'] ?? 'experience');
            }
        }
        if (count($selected) !== 3) throw new RuntimeException('The path planner could not produce three grounded canonical destinations.');

        // The voice layer cannot change the path. It receives only the already
        // selected resources and their sequence, which keeps surface language
        // separate from semantic destination selection.
        try {
            $voice = $this->render_voice($api_key, $raw_input, $interpretation, $plan, $selected, $candidate_map);
        } catch (Throwable $e) {
            if (strpos(strtolower($e->getMessage()), 'rejected the configured api key') !== false) throw $e;
            $voice = $this->deterministic_voice($raw_input, $selected, $plan);
        }
        $voice_issues = $this->voice_quality_issues($voice, $selected);
        if ($voice_issues) {
            try {
                $repaired = $this->repair_voice($api_key, $raw_input, $interpretation, $plan, $selected, $voice, $voice_issues);
                if (!$this->voice_quality_issues($repaired, $selected)) $voice = $repaired;
            } catch (Throwable $e) {
                // Preserve a usable response rather than exposing provider errors.
            }
        }

        $why_each = [];
        foreach (($voice['reasons'] ?? []) as $item) {
            if (is_array($item) && isset($item['id'])) $why_each[(string)$item['id']] = $this->clean((string)($item['reason'] ?? ''));
        }
        foreach ($selected as $r) {
            $id = $r['id'];
            if (!isset($why_each[$id]) || $why_each[$id] === '') $why_each[$id] = 'This gives the question another place to go.';
        }

        return [
            'version' => '0.3.3',
            'clarification_used' => $clarification !== '',
            'reflection' => $this->clean((string)($voice['reflection'] ?? $this->deterministic_reflection($raw_input))),
            'selected' => $selected,
            'why_each' => $why_each,
            'door_roles' => $door_roles,
            'needs_clarification' => false,
            'clarifying_question' => '',
            'movement_type' => $this->clean((string)($plan['movement_type'] ?? 'continue')),
            'landscape' => $this->landscape_destinations(),
        ];
    }

    private function is_eligible(array $r): bool {
        return ($r['endpoint_eligible'] ?? null) === true
            && ($r['source_access_class'] ?? 'public') === 'public'
            && in_array(($r['tier'] ?? ''), ['T1','T2','T3'], true)
            && !empty($r['url']) && !empty($r['title'])
            && !in_array(($r['content_access_status'] ?? ''), ['unresolved','referenced_but_not_individually_indexed'], true);
    }

    private function public_resource(array $r): array {
        return [
            'id' => (string)$r['id'], 'title' => wp_strip_all_tags((string)$r['title']),
            'url' => esc_url_raw((string)$r['url']), 'resource_type' => (string)($r['resource_type'] ?? ''),
            'tier' => (string)($r['tier'] ?? ''), 'content_access_status' => (string)($r['content_access_status'] ?? ''),
        ];
    }

    private function landscape_destinations(): array {
        return [
            ['title' => 'The Living Archive Atlas', 'url' => 'https://geralddaquila.com/the-living-archive-atlas/'],
            ['title' => 'The Question Beneath the Questions', 'url' => 'https://geralddaquila.com/2026/08/12/the-question-beneath-the-questions/'],
            ['title' => 'The Human System', 'url' => 'https://geralddaquila.com/2026/08/12/the-human-system/'],
            ['title' => 'Becoming Fully Human', 'url' => 'https://geralddaquila.com/2026/08/12/the-architecture-of-human-development/'],
            ['title' => 'The Architecture of Identity', 'url' => 'https://geralddaquila.com/2026/08/12/the-architecture-of-identity/'],
            ['title' => 'Living Archives', 'url' => 'https://geralddaquila.com/living-archives/'],
        ];
    }

    private function retrieve(string $raw_query, int $limit = 60, array $interpretation = []): array {
        $query_tokens = $this->tokens($raw_query);
        if (!$query_tokens) return [];
        $scores = [];
        $evidence = [];
        $N = max(1, (int)($this->index['document_count'] ?? count($this->by_id)));

        foreach ($query_tokens as $token) {
            $postings = $this->index['postings'][$token] ?? [];
            $df = max(1, count($postings));
            // High-frequency words are deliberately weak even when they are not
            // conventional stop words. This prevents words such as "new" from
            // opening an unrelated spiritual/new-earth branch of the corpus.
            $is_focus_token = in_array($token, $this->current_subject_focus_tokens, true);
            if ($df > (int)floor($N * 0.08) && !$is_focus_token) continue;
            $idf = log(($N + 1) / ($df + 1)) + 1;
            foreach ($postings as $posting) {
                if (!is_array($posting) || count($posting) < 2) continue;
                $id = (string)$posting[0];
                if (!isset($this->by_id[$id])) continue;
                $weight = (float)$posting[1];
                $scores[$id] = ($scores[$id] ?? 0.0) + ($weight * $idf);
                $evidence[$id]['raw_terms'][$token] = true;
            }
        }

        // Re-rank only already-grounded candidates with interpretation evidence.
        // Interpretation may deepen a candidate's relevance; it may never create
        // a candidate that the visitor's own words did not ground.
        $interpretation_text = implode(' ', [
            (string)($interpretation['pattern'] ?? ''), (string)($interpretation['responsibility'] ?? ''),
            (string)($interpretation['tension'] ?? ''), (string)($interpretation['capacity'] ?? ''),
            (string)($interpretation['movement'] ?? ''), (string)($interpretation['scale'] ?? ''),
            (string)($interpretation['mode_of_inquiry'] ?? ''), (string)($interpretation['appreciative_signal'] ?? ''),
            implode(' ', is_array($interpretation['search_terms'] ?? null) ? $interpretation['search_terms'] : []),
        ]);
        $interpretation_tokens = $this->tokens($interpretation_text);
        foreach (array_keys($scores) as $id) {
            $r = $this->by_id[$id];
            $resource_text = strtolower(implode(' ', [
                (string)($r['title'] ?? ''), (string)($r['excerpt'] ?? ''),
                implode(' ', is_array($r['source_categories'] ?? null) ? $r['source_categories'] : []),
            ]));
            $resource_tokens = array_fill_keys($this->tokens($resource_text), true);
            $hits = 0;
            foreach ($interpretation_tokens as $t) if (isset($resource_tokens[$t])) $hits++;
            if ($hits > 0) $scores[$id] += min(2.5, $hits * 0.35); // bounded enrichment
        }

        arsort($scores, SORT_NUMERIC);
        $out = [];
        foreach (array_slice($scores, 0, $limit, true) as $id => $score) {
            if (!isset($this->by_id[$id])) continue;
            $r = $this->by_id[$id];
            $raw_terms = array_keys($evidence[$id]['raw_terms'] ?? []);
            $anchor = $this->anchor_score($r, $raw_terms, $raw_query, $score, $N);
            $out[] = ['resource' => $r, 'score' => (float)$score, 'anchor_score' => $anchor['score'], 'anchor_terms' => $anchor['terms'], 'anchor_evidence' => $anchor['evidence'], 'subject_fit_score' => $this->subject_fit_score($r, $this->current_subject_focus_tokens)];
        }
        usort($out, function(array $a, array $b): int {
            if ($this->current_subject_focus_tokens) {
                $fit = (float)($b['subject_fit_score'] ?? 0) <=> (float)($a['subject_fit_score'] ?? 0);
                if ($fit !== 0) return $fit;
            }
            $as = (float)($a['score'] ?? 0); $bs = (float)($b['score'] ?? 0);
            return $bs <=> $as;
        });
        return $out;
    }

    /**
     * Keep navigation language out of the subject signal. The visitor's own
     * specific nouns remain the basis for relevance; this is not a topic
     * classifier and it must never invent synonyms or relationships.
     */
    private function subject_focus_tokens(string $raw_query): array {
        $generic = array_flip([
            'material','materials','resource','resources','information','content','page','pages','site','website',
            'archive','living','find','locate','located','where','what','when','which','who','whom','whose','why','how',
            'about','means','mean','explore','explores','exploring','understand','understanding','understood','learn','learning',
            'want','wants','wanted','need','needs','needed','help','please','tell','show','give','provide','look','looking',
            'start','begin','begins','beginning','enter','access','available','matter','matters','now','today','more',
            'can','could','would','should','will','may','might','does','did','doing','is','are','was','were','be','been',
            'feel','feels','feeling','felt','experience','experiences','experienced','experiencing','through','within',
            'there','their','this','that','these','those','from','into','onto','over','under','between','among','across',
            'please','also','just','really','very','something','anything','everything','someone','anyone'
        ]);
        $tokens = $this->tokens($raw_query);
        $focus = [];
        foreach ($tokens as $token) {
            if (!isset($generic[$token])) $focus[$token] = true;
        }
        return array_values(array_keys($focus));
    }

    /**
     * Score direct evidence for the visitor's subject independently of the
     * broad lexical score. Title evidence is strongest; excerpt/category
     * evidence is next; body-only evidence is weaker. This score is a hard
     * eligibility gate, not merely a ranking bonus.
     */
    private function subject_fit_score(array $resource, array $focus_tokens): float {
        if (!$focus_tokens) return 0.0;
        $title = strtolower((string)($resource['title'] ?? ''));
        $excerpt = strtolower((string)($resource['excerpt'] ?? ''));
        $categories = strtolower(implode(' ', is_array($resource['source_categories'] ?? null) ? $resource['source_categories'] : []));
        $content = strtolower((string)($resource['content'] ?? ''));
        $title_tokens = array_fill_keys($this->tokens($title), true);
        $surface_tokens = array_fill_keys($this->tokens($excerpt . ' ' . $categories), true);
        $body_tokens = array_fill_keys($this->tokens($content), true);
        $score = 0.0;
        foreach ($focus_tokens as $token) {
            if (isset($title_tokens[$token])) {
                $score += 3.0;
            } elseif (isset($surface_tokens[$token])) {
                $score += 1.5;
            } elseif (isset($body_tokens[$token])) {
                $score += 0.5;
            }
        }
        return $score;
    }

    private function subject_fit_threshold(): float {
        // Multi-term subjects require at least two independent surface signals:
        // one term in the title and another in the title/excerpt/categories.
        return count($this->current_subject_focus_tokens) >= 2 ? 4.5 : 3.0;
    }

    /**
     * Apply one subject-fit rule to every retrieval route, including expanded
     * relationship candidates. Never pad a path with unrelated resources.
     */
    private function filter_subject_relevant_candidates(array $candidates): array {
        if (!$this->current_subject_focus_tokens) return $candidates;
        $filtered = [];
        foreach ($candidates as $candidate) {
            $resource = is_array($candidate['resource'] ?? null) ? $candidate['resource'] : [];
            $fit = $this->subject_fit_score($resource, $this->current_subject_focus_tokens);
            if ($fit < $this->subject_fit_threshold()) continue;
            $candidate['subject_fit_score'] = $fit;
            $filtered[] = $candidate;
        }
        return $filtered;
    }

    private function anchor_score(array $r, array $raw_terms, string $raw_query, float $lexical_score, int $N): array {
        $title = strtolower((string)($r['title'] ?? ''));
        $excerpt = strtolower((string)($r['excerpt'] ?? ''));
        $cats = strtolower(implode(' ', is_array($r['source_categories'] ?? null) ? $r['source_categories'] : []));
        $field_text = $title . ' ' . $excerpt . ' ' . $cats;
        $field_tokens = array_fill_keys($this->tokens($field_text), true);
        $terms = [];
        foreach ($raw_terms as $t) if (isset($field_tokens[$t])) $terms[] = $t;
        $phrase_hits = [];
        $qtokens = $this->tokens($raw_query);
        for ($i=0; $i<count($qtokens)-1; $i++) {
            $phrase = $qtokens[$i] . ' ' . $qtokens[$i+1];
            if (strpos($field_text, $phrase) !== false) $phrase_hits[] = $phrase;
        }
        $field_bonus = count(array_unique($terms)) * 0.75 + count($phrase_hits) * 1.5;
        $title_bonus = 0.0;
        foreach (array_unique($terms) as $t) if (strpos($title, $t) !== false) $title_bonus += 1.5;
        return ['score' => $lexical_score + $field_bonus + $title_bonus, 'terms' => array_values(array_unique($terms)), 'evidence' => ['title_terms'=>array_values(array_unique(array_filter($terms, fn($t)=>strpos($title,$t)!==false))), 'field_terms'=>array_values(array_unique($terms)), 'phrases'=>array_values(array_unique($phrase_hits))]];
    }

    private function balance_domains(array $candidates, int $limit = 40): array {
        if ($this->current_subject_focus_tokens) {
            foreach ($candidates as &$candidate) {
                $resource = is_array($candidate['resource'] ?? null) ? $candidate['resource'] : [];
                $candidate['subject_fit_score'] = $this->subject_fit_score($resource, $this->current_subject_focus_tokens);
            }
            unset($candidate);
        }
        usort($candidates, function(array $a, array $b): int {
            if ($this->current_subject_focus_tokens) {
                $fit = (float)($b['subject_fit_score'] ?? 0) <=> (float)($a['subject_fit_score'] ?? 0);
                if ($fit !== 0) return $fit;
            }
            $aa = (float)($a['anchor_score'] ?? $a['score'] ?? 0); $bb = (float)($b['anchor_score'] ?? $b['score'] ?? 0);
            return $bb <=> $aa;
        });
        return array_slice($candidates, 0, $limit);
    }

    private function expand(array $candidates, int $limit = 50): array {
        $scores = [];
        $meta = [];
        foreach ($candidates as $candidate) {
            $id = (string)$candidate['resource']['id'];
            $scores[$id] = max($scores[$id] ?? 0.0, (float)($candidate['anchor_score'] ?? $candidate['score'] ?? 0));
            $meta[$id] = $candidate;
        }
        // Canonical relationships, when they become available, may extend the
        // path, but only from already-grounded visitor candidates. No synthetic
        // canonical relationships are invented here.
        foreach (array_slice($candidates, 0, 16) as $candidate) {
            $id = (string)$candidate['resource']['id'];
            foreach (($this->from[$id] ?? []) as $relationship) {
                $to = (string)($relationship['to'] ?? '');
                if ($to === '' || !isset($this->by_id[$to]) || !$this->is_eligible($this->by_id[$to])) continue;
                $type = (string)($relationship['type'] ?? '');
                $boost = in_array($type, ['grounds','belongs_to','extends_into','prepares_for'], true) ? 1.0 : 0.5;
                $scores[$to] = max($scores[$to] ?? 0.0, ((float)$candidate['anchor_score'] * 0.72) + $boost);
                if (!isset($meta[$to])) $meta[$to] = ['resource'=>$this->by_id[$to],'score'=>$scores[$to],'anchor_score'=>$scores[$to]*0.65,'anchor_terms'=>[],'anchor_evidence'=>['derived_relationship'=>true]];
            }
        }
        arsort($scores, SORT_NUMERIC);
        $out=[];
        foreach (array_slice($scores,0,$limit,true) as $id=>$score) {
            $item=$meta[$id] ?? null; if (!$item) continue; $item['score']=(float)$score; $out[]=$item;
        }
        return $out;
    }

    private function deterministic_interpretation(array $input): array {
        $situation=$this->clean((string)($input['situation']??'')); $possibility=$this->clean((string)($input['possibility']??''));
        return ['situation'=>$situation,'pattern'=>'','responsibility'=>'','tension'=>'','capacity'=>'','movement'=>'','scale'=>'','mode_of_inquiry'=>'','appreciative_signal'=>'','constitutional_questions'=>[],'search_terms'=>$this->tokens($situation.' '.$possibility),'competing_interpretations'=>[],'sufficient'=>true,'clarifying_question'=>''];
    }

    private function deterministic_plan(array $candidates): array {
        // navigate() passes this method the already subject-filtered candidate set.
        // Keep the fallback deterministic over that bounded set; request-specific
        // focus is enforced before planning and again by plan_quality_issues().
        $pool=[]; foreach($candidates as $c){$id=(string)($c['resource']['id']??''); if($id!==''&&$this->is_eligible($c['resource']??[]))$pool[$id]=$c;}
        if(count($pool)<3) return ['selected'=>[],'movement_type'=>'continue'];
        $ids=array_keys($pool);
        $selected=[]; $used=[]; $used_titles=[];
        $roles=['experience','pattern','structure'];
        foreach($roles as $role){
            $best=null;$bestv=-INF;
            foreach($ids as $id){if(isset($used[$id]))continue;$r=$pool[$id]['resource'];$title_key=$this->display_title_key($r);if($title_key!==''&&isset($used_titles[$title_key]))continue;$text=strtolower(implode(' ',[(string)$r['title'],(string)$r['excerpt'],implode(' ',(array)($r['source_categories']??[]))]));
                $v=(float)($pool[$id]['anchor_score']??$pool[$id]['score']??0); if($this->current_subject_focus_tokens)$v += 10.0 * $this->subject_fit_score($r, $this->current_subject_focus_tokens);
                if($role==='experience' && preg_match('/relationship|belong|life|work|change|decision|leav|identity|authentic/i',$text))$v+=1.5;
                if($role==='pattern' && preg_match('/pattern|behavior|psycholog|assumption|identity|belong|group|relationship/i',$text))$v+=1.5;
                if($role==='structure' && preg_match('/system|society|community|institution|culture|group|structure/i',$text))$v+=1.5;
                if($v>$bestv){$bestv=$v;$best=$id;}
            }
            if($best===null)break;$used[$best]=true;$best_title_key=$this->display_title_key($pool[$best]['resource']);if($best_title_key!=='')$used_titles[$best_title_key]=true;$selected[]=['id'=>$best,'door'=>$role];
        }
        return ['selected'=>$selected,'movement_type'=>'deepening'];
    }

    private function display_title_key(array $resource): string {
        $title = html_entity_decode(wp_strip_all_tags((string)($resource['title'] ?? '')), ENT_QUOTES | ENT_HTML5, 'UTF-8');
        $title = function_exists('mb_strtolower') ? mb_strtolower($title, 'UTF-8') : strtolower($title);
        $title = preg_replace('/[^\p{L}\p{N}]+/u', ' ', $title);
        return trim((string)preg_replace('/\s+/u', ' ', (string)$title));
    }

    private function plan_quality_issues(array $plan, array $candidate_map): array {
        $issues=[];$sel=is_array($plan['selected']??null)?$plan['selected']:[];
        if(count($sel)!==3)$issues[]='exactly three grounded destinations required';
        $ids=[];$titles=[];$roles=[];
        foreach($sel as $s){if(!is_array($s)){ $issues[]='malformed destination';continue;} $id=(string)($s['id']??'');$role=(string)($s['door']??'');
            if($id===''||!isset($candidate_map[$id]))$issues[]='selected destination is not in grounded candidate set';
            if($id!=='')$ids[$id]=true;if(in_array($role,['experience','pattern','structure'],true))$roles[$role]=true;else $issues[]='invalid internal path role';
            if(isset($candidate_map[$id])){
                if((float)($candidate_map[$id]['anchor_score']??0)<1.5)$issues[]='destination has insufficient visitor-word grounding';
                if($this->current_subject_focus_tokens && $this->subject_fit_score(($candidate_map[$id]['resource']??[]), $this->current_subject_focus_tokens)<$this->subject_fit_threshold())$issues[]='destination does not fit the visitor\'s stated subject';
                $title_key=$this->display_title_key($candidate_map[$id]['resource']??[]);
                if($title_key!==''){
                    if(isset($titles[$title_key]))$issues[]='displayed destination titles are not distinct';
                    $titles[$title_key]=true;
                }
            }
        }
        if(count($ids)!==3)$issues[]='destinations are not distinct';
        if(count($roles)<2)$issues[]='path lacks meaningful internal differentiation';
        return array_values(array_unique($issues));
    }

    private function plan_packet(array $candidates): array {
        $packet=[]; foreach(array_slice($candidates,0,28) as $i=>$c){$r=$c['resource'];$packet[]=[
            'rank'=>$i+1,'id'=>(string)$r['id'],'title'=>wp_strip_all_tags((string)$r['title']),
            'tier'=>(string)($r['tier']??''),'type'=>(string)($r['resource_type']??''),
            'anchor_score'=>round((float)($c['anchor_score']??$c['score']??0),2),
            'anchor_terms'=>$c['anchor_terms']??[],'anchor_evidence'=>$c['anchor_evidence']??[],
            'excerpt'=>function_exists('mb_substr')?mb_substr(wp_strip_all_tags((string)($r['excerpt']??'')),0,900):substr(wp_strip_all_tags((string)($r['excerpt']??'')),0,900),
            'categories'=>$r['source_categories']??[],
        ];} return $packet;
    }

    private function plan_path(string $api_key,array $visitor,array $interpretation,array $candidates): array {
        $schema=['type'=>'object','properties'=>[
            'selected'=>['type'=>'array','minItems'=>3,'maxItems'=>3,'items'=>['type'=>'object','properties'=>['id'=>['type'=>'string'],'door'=>['type'=>'string','enum'=>['experience','pattern','structure']]],'required'=>['id','door'],'additionalProperties'=>false]],
            'movement_type'=>['type'=>'string','enum'=>['deepening','expanding','integrating','re-entry','continue']],
            'path_logic'=>['type'=>'array','minItems'=>3,'maxItems'=>3,'items'=>['type'=>'string']],
            'needs_clarification'=>['type'=>'boolean'],'clarifying_question'=>['type'=>'string']],
            'required'=>['selected','movement_type','path_logic','needs_clarification','clarifying_question'],'additionalProperties'=>false];
        $prompt=<<<'LANPLAN'
You are the hidden path-planning layer of the public Living Archive Navigator. Stewardship Pathway Engine 3.4.0 is the behavioral north star.

The visitor's actual words are the primary source of truth. The hidden interpretation is a lens, not a replacement for those words. Candidate resources are already grounded in the visitor's words. You may choose only from those supplied candidates.

The task is NOT to find three interesting or merely related articles. Build a small path through the visitor's inquiry.

Preserve the SPE sequence underneath the surface:
1. stay close to what is actually happening;
2. notice what is already alive, valued, questioned, or becoming possible;
3. follow the movement already present in the visitor's inquiry;
4. let the next doorway deepen, reveal a pattern, or widen the field only when the question earns that movement.

Appreciative inquiry is not praise. It means noticing the possibility, agency, curiosity, recognition, or value already present in the visitor's own words and allowing that to affect where the path goes.

Do not allow the hidden interpretation to pull the path into spirituality, psychology, systems, or any other domain unless the visitor's words and the supplied candidate evidence support that direction. A candidate with weak visitor-word grounding is not eligible merely because its title is interesting.

The three internal roles are checks, not a quota. experience stays close; pattern looks underneath or across recurrence; structure widens scale. Another sequence is valid when the visitor's actual inquiry calls for it.

The order matters. Choose three resources whose sequence changes what the visitor can notice next. If the same three would work equally well in any order, choose again.

Never invent IDs. Never choose anything outside the supplied candidates. Never choose protected/T4 material, access gates, generic category pages, or weakly grounded material.

If meaningful ambiguity remains about what the visitor is actually asking, you may request one small clarification instead of forcing a path. Do not clarify merely because the question is nuanced.

Return only JSON matching the schema.
LANPLAN;
        return $this->groq_json($api_key,[['role'=>'system','content'=>$prompt],['role'=>'user','content'=>wp_json_encode(['visitor_input'=>$visitor,'interpretation'=>$interpretation,'candidates'=>$this->plan_packet($candidates)],JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES)]],$schema,1500);
    }

    private function repair_plan(string $api_key,array $visitor,array $interpretation,array $candidates,array $plan,array $issues): array {
        $schema=['type'=>'object','properties'=>['selected'=>['type'=>'array','minItems'=>3,'maxItems'=>3,'items'=>['type'=>'object','properties'=>['id'=>['type'=>'string'],'door'=>['type'=>'string','enum'=>['experience','pattern','structure']]],'required'=>['id','door'],'additionalProperties'=>false]],'movement_type'=>['type'=>'string','enum'=>['deepening','expanding','integrating','re-entry','continue']],'path_logic'=>['type'=>'array','minItems'=>3,'maxItems'=>3,'items'=>['type'=>'string']],'needs_clarification'=>['type'=>'boolean'],'clarifying_question'=>['type'=>'string']],'required'=>['selected','movement_type','path_logic','needs_clarification','clarifying_question'],'additionalProperties'=>false];
        $prompt=<<<'LANREPAIRPLAN'
Repair the path, not the prose. The previous path failed one or more grounding/inquiry checks. Rebuild it from the visitor's actual words and the supplied grounded candidates.

Hard rule: a candidate must have a concrete connection to the visitor's words. Do not select a candidate merely because its title is compelling or because the hidden interpretation suggests a domain. The visitor's question outranks the interpretation.

Restore the Stewardship Pathway Engine 3.4.0 logic: recognize the situation, notice what is already alive or becoming possible, then move the inquiry one step at a time. The three doors must form a sequence, not a catalogue.

Do not invent IDs. Use only supplied candidates. Return JSON only.
LANREPAIRPLAN;
        return $this->groq_json($api_key,[['role'=>'system','content'=>$prompt],['role'=>'user','content'=>wp_json_encode(['visitor_input'=>$visitor,'interpretation'=>$interpretation,'previous_plan'=>$plan,'issues'=>$issues,'candidates'=>$this->plan_packet($candidates)],JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES)]],$schema,1300);
    }

    private function render_voice(string $api_key,array $visitor,array $interpretation,array $plan,array $selected,array $candidate_map): array {
        $packet=[]; foreach($plan['selected'] as $spec){$id=(string)$spec['id'];if(!isset($candidate_map[$id]))continue;$r=$candidate_map[$id]['resource'];$packet[]=['id'=>$id,'title'=>wp_strip_all_tags((string)$r['title']),'door'=>(string)($spec['door']??'experience'),'excerpt'=>function_exists('mb_substr')?mb_substr(wp_strip_all_tags((string)($r['excerpt']??'')),0,1000):substr(wp_strip_all_tags((string)($r['excerpt']??'')),0,1000)];}
        $schema=['type'=>'object','properties'=>['reflection'=>['type'=>'string'],'reasons'=>['type'=>'array','minItems'=>3,'maxItems'=>3,'items'=>['type'=>'object','properties'=>['id'=>['type'=>'string'],'reason'=>['type'=>'string']],'required'=>['id','reason'],'additionalProperties'=>false]]],'required'=>['reflection','reasons'],'additionalProperties'=>false];
        $prompt=<<<'LANVOICE'
You are the human-facing voice of the Living Archive Navigator. The path has already been selected. You do not choose or change destinations. Your job is to make the selected path feel like a natural continuation of the visitor's own question.

The visitor has brought a real question. Pay attention before directing them anywhere. Notice one precise distinction, contrast, change, or possibility that is actually present in their words. Leave the unresolved part open. Then let the three already-selected doors appear as natural places to continue.

The voice should embody the quiet human quality of the Stewardship Pathway Engine 3.4.0 without mentioning stewardship, formation, engines, AI, retrieval, or technique.

Warmth comes from attention, not emotional vocabulary. Compassion comes from not rushing to explain. Wisdom comes from knowing what to leave open. High EQ comes from noticing the human distinction without turning it into therapy.

Sound like a thoughtful, experienced person who has genuinely considered the question and has no need to prove that they understand it.

Do not diagnose, prescribe, flatter, reassure, moralize, or explain the visitor to themselves. Do not invent motives, wounds, childhood causes, personality traits, or emotions they did not name.

Do not say “You might find it useful,” “This piece highlights,” “The discussion shows,” “It explores,” “It examines,” “It offers,” “This resource,” “If you want to,” “There are a few places,” “I hear you,” “It sounds like,” “It seems like,” “What you have shared,” or similar catalogue/performed-empathy language.

Do not summarize the publications. Each reason should open the next thought that becomes available from the visitor's present position. It should feel like a quiet invitation into the selected doorway.

Reflection: 2-4 short sentences. Prefer concrete ordinary language. If the visitor has already noticed something important, recognize the distinction without praising it. Do not close the question.

Reasons: 1-2 short sentences each. Make them specific to this visitor and to the selected doorway. Vary sentence construction. Do not repeat the title. Do not call anything an article, resource, reading, candidate, recommendation, or destination.

The engineering underneath may be sophisticated. None of it should be audible. Elegant simplicity on the surface is the goal.

Return only JSON.
LANVOICE;
        return $this->groq_json($api_key,[['role'=>'system','content'=>$prompt],['role'=>'user','content'=>wp_json_encode(['visitor_input'=>$visitor,'interpretation'=>$interpretation,'path_plan'=>$plan,'selected'=>$packet],JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES)]],$schema,1300);
    }

    private function voice_quality_issues(array $voice,array $selected): array {
        $issues=[];$reflection=strtolower($this->clean((string)($voice['reflection']??'')));
        if($reflection==='')$issues[]='empty reflection';
        $banned=['you might find it useful','this piece highlights','the discussion shows','it explores','it examines','it offers','this resource','if you want to','there are a few places','i hear you','it sounds like','it seems like','what you have shared','lived experience','emotional landscape','holding space','nervous system','sensemaking','journey','retrieval','classification','algorithm','artificial intelligence'];
        foreach($banned as $p)if(strpos($reflection,$p)!==false)$issues[]='generic voice';
        $reasons=is_array($voice['reasons']??null)?$voice['reasons']:[];if(count($reasons)!==3)$issues[]='three reasons required';
        $ids=[];foreach($reasons as $r){$id=(string)($r['id']??'');$reason=strtolower($this->clean((string)($r['reason']??'')));if($id==='')$issues[]='reason id missing';$ids[$id]=true;if($reason==='')$issues[]='empty reason';foreach($banned as $p)if(strpos($reason,$p)!==false)$issues[]='catalogue voice';}
        foreach($selected as $r)if(!isset($ids[$r['id']]))$issues[]='missing selected reason';
        return array_values(array_unique($issues));
    }

    private function repair_voice(string $api_key,array $visitor,array $interpretation,array $plan,array $selected,array $voice,array $issues): array {
        $schema=['type'=>'object','properties'=>['reflection'=>['type'=>'string'],'reasons'=>['type'=>'array','minItems'=>3,'maxItems'=>3,'items'=>['type'=>'object','properties'=>['id'=>['type'=>'string'],'reason'=>['type'=>'string']],'required'=>['id','reason'],'additionalProperties'=>false]]],'required'=>['reflection','reasons'],'additionalProperties'=>false];
        $prompt=<<<'LANVOICEFIX'
Rewrite the human-facing response from scratch. Do not change the selected destinations. Remove any catalogue language, performed empathy, generic reassurance, or professionalized phrasing. Stay close to the visitor's actual words. Notice one precise human distinction and leave the question open. Each reason should create curiosity about the next thought, not explain relevance. Warmth should come from attention and restraint.
LANVOICEFIX;
        $packet=[];foreach($selected as $r)$packet[]=['id'=>$r['id'],'title'=>$r['title'],'excerpt'=>isset($this->by_id[$r['id']])?mb_substr(wp_strip_all_tags((string)($this->by_id[$r['id']]['excerpt']??'')),0,1000):''];
        return $this->groq_json($api_key,[['role'=>'system','content'=>$prompt],['role'=>'user','content'=>wp_json_encode(['visitor_input'=>$visitor,'path_plan'=>$plan,'selected'=>$packet,'previous_voice'=>$voice,'issues'=>$issues],JSON_UNESCAPED_UNICODE|JSON_UNESCAPED_SLASHES)]],$schema,1100);
    }

    private function deterministic_voice(array $input,array $selected,array $plan): array {
        $s=$this->clean((string)($input['situation']??''));
        if($s==='')$s=$this->clean((string)($input['possibility']??''));
        $reflection=$s!==''?'The question does not need to be settled all at once. There is enough in what you have written to look at it from a few different directions without closing it down.':'We can leave the question open and see what becomes clearer as you look around.';
        $reasons=[];
        foreach($selected as $i=>$r){$role=(string)($plan['selected'][$i]['door']??'experience');$reason=$role==='experience'?'This stays close to what is happening now.':($role==='pattern'?'This gives the question room to look underneath the immediate situation.':'This lets the question widen without leaving the thread that brought you here.');$reasons[]=['id'=>$r['id'],'reason'=>$reason];}
        return ['reflection'=>$reflection,'reasons'=>$reasons];
    }

    /**
     * Groq provider layer adapted from the battle-tested USE/The Guide model
     * handling pattern: live model discovery, capability-aware ordering,
     * model quarantine, request-size handling, rate-limit handling, and a
     * final deterministic recovery path at the navigation boundary.
     */
    private function groq_json(string $api_key, array $messages, array $schema, int $max_tokens): array {
        $models = $this->live_groq_models($api_key);
        if (!$models) {
            throw new RuntimeException('No usable Groq models are currently available.');
        }

        $last_error = 'The interpretation service returned no usable result.';

        foreach ($models as $model_id) {
            $profile = $this->groq_model_profile($model_id);
            try {
                $decoded = $this->groq_json_attempt($api_key, $model_id, $profile, $messages, $schema, $max_tokens);
                if ($this->schema_matches($decoded, $schema)) {
                    return $decoded;
                }

                self::$groq_model_cache['structural_failed_models'][$model_id] = true;
                $last_error = 'The interpretation service returned data outside the required structure.';
            } catch (Throwable $e) {
                $error_text = $e->getMessage();
                $last_error = $error_text;

                if ($this->is_auth_error($error_text)) {
                    throw new RuntimeException('The interpretation service rejected the configured API key.');
                }

                if ($this->is_terms_required_error($error_text)) {
                    self::$groq_model_cache['terms_required_models'][$model_id] = true;
                    continue;
                }

                if ($this->is_request_too_large_error($error_text)) {
                    self::$groq_model_cache['request_too_large_models'][$model_id] = true;
                    continue;
                }

                if ($this->is_rate_limit_error($error_text)) {
                    self::$groq_model_cache['rate_limited_until'][$model_id] = time() + $this->rate_limit_seconds($error_text);
                    continue;
                }

                // Provider/model-specific structural or unsupported-parameter
                // failures should not take the entire pathway down. Quarantine
                // the model for this PHP process and continue with the next one.
                if ($this->is_structural_provider_error($error_text)) {
                    self::$groq_model_cache['structural_failed_models'][$model_id] = true;
                    continue;
                }

                // Unknown transient/provider failures: try the next live model.
                continue;
            }
        }

        throw new RuntimeException($last_error);
    }

    private function live_groq_models(string $api_key): array {
        $now = time();
        $blocked = $this->blocked_groq_models($now);

        if (!empty(self::$groq_model_cache['models']) && ($now - (int)self::$groq_model_cache['last_fetch']) < 3600) {
            return array_values(array_filter(self::$groq_model_cache['models'], function ($model) use ($blocked) {
                return !isset($blocked[$model]);
            }));
        }

        $discovered = [];
        $response = wp_remote_get('https://api.groq.com/openai/v1/models', [
            'timeout' => 15,
            'headers' => [
                'Authorization' => 'Bearer ' . $api_key,
                'Content-Type' => 'application/json',
            ],
        ]);

        if (!is_wp_error($response)) {
            $status = wp_remote_retrieve_response_code($response);
            if ($status >= 200 && $status < 300) {
                $payload = json_decode(wp_remote_retrieve_body($response), true);
                foreach (($payload['data'] ?? []) as $model) {
                    $id = is_array($model) ? (string)($model['id'] ?? '') : '';
                    if ($id === '' || $this->is_non_text_model($id)) continue;
                    $discovered[] = $id;
                }
            }
        }

        // Known strict Structured Output models are always preferred when
        // present. Other live text models remain eligible through JSON Object
        // Mode, followed by local schema validation.
        $preferred = [
            'openai/gpt-oss-120b' => 100,
            'openai/gpt-oss-20b' => 90,
            'qwen/qwen3.8-27b' => 80,
        ];
        $discovered = array_values(array_unique($discovered));
        usort($discovered, function ($a, $b) use ($preferred) {
            $pa = $preferred[$a] ?? 10;
            $pb = $preferred[$b] ?? 10;
            if ($pa !== $pb) return $pb <=> $pa;
            return strcasecmp($a, $b);
        });

        if (!$discovered) {
            // The catalogue endpoint may be temporarily unavailable. Keep a
            // conservative known-good set so a transient discovery failure
            // does not erase the provider's executable candidates.
            $discovered = array_keys($preferred);
        }

        self::$groq_model_cache['models'] = $discovered;
        self::$groq_model_cache['last_fetch'] = $now;

        return array_values(array_filter($discovered, function ($model) use ($blocked) {
            return !isset($blocked[$model]);
        }));
    }

    private function blocked_groq_models(int $now): array {
        $blocked = [];
        foreach (['terms_required_models', 'structural_failed_models', 'request_too_large_models'] as $bucket) {
            foreach (self::$groq_model_cache[$bucket] as $model => $value) {
                if ($value) $blocked[$model] = true;
            }
        }
        foreach (self::$groq_model_cache['rate_limited_until'] as $model => $until) {
            if ((int)$until > $now) {
                $blocked[$model] = true;
            }
        }
        self::$groq_model_cache['rate_limited_until'] = array_filter(
            self::$groq_model_cache['rate_limited_until'],
            static function ($until) use ($now) { return (int)$until > $now; }
        );
        return $blocked;
    }

    private function groq_model_profile(string $model_id): array {
        $strict_models = [
            'openai/gpt-oss-20b',
            'openai/gpt-oss-120b',
            'qwen/qwen3.8-27b',
        ];
        $strict = in_array($model_id, $strict_models, true);
        $profile = [
            'strict' => $strict,
            'reasoning_effort' => $strict ? 'medium' : null,
            'include_reasoning' => false,
        ];
        return $profile;
    }

    private function groq_json_attempt(string $api_key, string $model_id, array $profile, array $messages, array $schema, int $max_tokens): array {
        $body = [
            'model' => $model_id,
            'messages' => $messages,
            'temperature' => 0.1,
            'max_completion_tokens' => $max_tokens,
        ];

        if ($profile['strict']) {
            $body['reasoning_effort'] = $profile['reasoning_effort'];
            $body['response_format'] = [
                'type' => 'json_schema',
                'json_schema' => [
                    'name' => 'living_archive_navigator_response',
                    'strict' => true,
                    'schema' => $schema,
                ],
            ];
        } else {
            // Groq documents JSON Object Mode as the broad compatibility path
            // for models that do not support strict Structured Outputs.
            $body['response_format'] = ['type' => 'json_object'];
            $body['messages'][0]['content'] .= ' Output a single valid JSON object matching the requested fields. Do not include markdown fences or commentary.';
        }

        // GPT-OSS exposes reasoning separately; suppressing it keeps the
        // visitor-facing structured content clean and reduces output pressure.
        if (strpos($model_id, 'openai/gpt-oss-') === 0) {
            $body['include_reasoning'] = false;
        }

        $args = [
            'timeout' => 45,
            'headers' => [
                'Authorization' => 'Bearer ' . $api_key,
                'Content-Type' => 'application/json',
            ],
            'body' => wp_json_encode($body, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES),
        ];

        $response = null;
        for ($attempt = 0; $attempt < 2; $attempt++) {
            $response = wp_remote_post('https://api.groq.com/openai/v1/chat/completions', $args);
            if (is_wp_error($response)) {
                if ($attempt === 0) { usleep(250000); continue; }
                throw new RuntimeException('The interpretation service could not be reached.');
            }
            $status = wp_remote_retrieve_response_code($response);
            if ($status >= 200 && $status < 300) break;
            $body_text = wp_remote_retrieve_body($response);
            if ($attempt === 0 && in_array($status, [429, 500, 502, 503, 504], true)) {
                usleep($status === 429 ? 500000 : 250000);
                continue;
            }
            throw new RuntimeException($this->groq_error_text($status, $body_text));
        }

        $raw = wp_remote_retrieve_body($response);
        $payload = json_decode($raw, true);
        if (!is_array($payload) || json_last_error() !== JSON_ERROR_NONE) {
            throw new RuntimeException('The interpretation service returned invalid JSON.');
        }
        $content = $payload['choices'][0]['message']['content'] ?? '';
        if (!is_string($content) || trim($content) === '') {
            throw new RuntimeException('The interpretation service returned no usable result.');
        }
        $decoded = json_decode(trim($content), true);
        if (!is_array($decoded) || json_last_error() !== JSON_ERROR_NONE) {
            throw new RuntimeException('The interpretation service returned malformed structured data.');
        }
        return $decoded;
    }

    private function groq_error_text(int $status, string $body): string {
        $payload = json_decode($body, true);
        $message = '';
        if (is_array($payload)) {
            $message = (string)($payload['error']['message'] ?? '');
            $code = (string)($payload['error']['code'] ?? '');
            if ($code !== '') $message .= ' ' . $code;
        }
        return trim('Groq HTTP ' . $status . ' ' . $message);
    }

    private function is_non_text_model(string $model_id): bool {
        $id = strtolower($model_id);
        foreach (['whisper', 'guard', 'audio', 'vision', 'tts', 'speech', 'transcribe', 'orpheus'] as $excluded) {
            if (strpos($id, $excluded) !== false) return true;
        }
        return false;
    }

    private function is_auth_error(string $error): bool {
        $e = strtolower($error);
        return strpos($e, 'http 401') !== false || strpos($e, 'http 403') !== false || strpos($e, 'invalid api key') !== false || strpos($e, 'authentication') !== false;
    }

    private function is_terms_required_error(string $error): bool {
        $e = strtolower($error);
        return strpos($e, 'terms') !== false && (strpos($e, 'required') !== false || strpos($e, 'accept') !== false);
    }

    private function is_request_too_large_error(string $error): bool {
        $e = strtolower($error);
        foreach (['request_too_large', 'request entity too large', 'context length', 'maximum context length', 'too many tokens', '413'] as $marker) {
            if (strpos($e, $marker) !== false) return true;
        }
        return false;
    }

    private function is_rate_limit_error(string $error): bool {
        $e = strtolower($error);
        foreach (['rate_limit_exceeded', 'rate limit reached', 'too many requests', '429'] as $marker) {
            if (strpos($e, $marker) !== false) return true;
        }
        return false;
    }

    private function is_structural_provider_error(string $error): bool {
        $e = strtolower($error);
        foreach (['response_format', 'json_schema', 'structured output', 'schema', 'unsupported parameter', 'invalid_request_error', 'bad request', 'http 400'] as $marker) {
            if (strpos($e, $marker) !== false) return true;
        }
        return false;
    }

    private function rate_limit_seconds(string $error): int {
        if (preg_match('/(?:try again in|retry after)\s+([0-9]+(?:\.[0-9]+)?)\s*s/i', $error, $m)) {
            return max(5, min(900, (int)ceil((float)$m[1])));
        }
        return 60;
    }

    private function schema_matches($value, array $schema): bool {
        $type = $schema['type'] ?? null;
        if ($type === 'object') {
            if (!is_array($value) || array_keys($value) !== array_keys(array_filter($value, 'is_string', ARRAY_FILTER_USE_KEY))) return false;
            foreach (($schema['required'] ?? []) as $required) {
                if (!array_key_exists($required, $value)) return false;
            }
            if (($schema['additionalProperties'] ?? true) === false) {
                foreach ($value as $key => $_) if (!array_key_exists($key, $schema['properties'] ?? [])) return false;
            }
            foreach (($schema['properties'] ?? []) as $key => $child) {
                if (array_key_exists($key, $value) && !$this->schema_matches($value[$key], $child)) return false;
            }
            return true;
        }
        if ($type === 'array') {
            if (!is_array($value)) return false;
            foreach ($value as $item) if (!$this->schema_matches($item, $schema['items'] ?? ['type' => 'string'])) return false;
            return true;
        }
        if ($type === 'string') {
            if (!is_string($value)) return false;
        } elseif ($type === 'boolean') {
            if (!is_bool($value)) return false;
        } elseif ($type === 'number') {
            if (!is_int($value) && !is_float($value)) return false;
        } elseif ($type === 'integer') {
            if (!is_int($value)) return false;
        } elseif ($type !== null) {
            return false;
        }
        if (isset($schema['enum']) && !in_array($value, $schema['enum'], true)) return false;
        return true;
    }

    private function tokens(string $value): array {
        $stop = array_flip(preg_split('/\s+/', 'the and of to in a for on with from into by as is are be this that what when where how an or not you your their our its it they them we us can may will through about after before between within across under over more less very all one two three four five six seven eight nine ten without just really also been being do does did have has had would could should shall might must than then there here some any each every both own same other another much many most few several such only still even too very via per while whose whom new recently initial became wanted raising dont don know means now first last thing things way ways something someone maybe perhaps sometimes often need needed needs trying tried try get got getting make made making begin beginning began joined join joining', -1, PREG_SPLIT_NO_EMPTY));
        preg_match_all("/[a-z0-9]+(?:['’\-][a-z0-9]+)?/i", strtolower($value), $matches);
        $out = [];
        foreach ($matches[0] as $token) {
            if (strlen($token) >= 3 && !isset($stop[$token])) $out[] = $token;
        }
        return array_values(array_unique($out));
    }

    private function clean(string $value): string {
        return trim((string)preg_replace('/\s+/u', ' ', wp_strip_all_tags($value)));
    }
}
