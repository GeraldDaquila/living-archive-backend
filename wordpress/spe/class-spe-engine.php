<?php
if (!defined('ABSPATH')) { exit; }

final class SPE_Engine {
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
    private array $by_id = [];
    private array $from = [];

    public function __construct(string $data_dir) {
        $this->data_dir = rtrim($data_dir, '/\\') . DIRECTORY_SEPARATOR;
        $this->load_data();
    }

    private function load_json(string $file): array {
        $path = $this->data_dir . $file;
        if (!is_readable($path)) {
            throw new RuntimeException('Stewardship corpus file is unavailable: ' . $file);
        }
        $raw = file_get_contents($path);
        if ($raw === false) {
            throw new RuntimeException('Stewardship corpus file could not be read: ' . $file);
        }
        $data = json_decode($raw, true);
        if (!is_array($data) || json_last_error() !== JSON_ERROR_NONE) {
            throw new RuntimeException('Stewardship corpus JSON is invalid: ' . $file);
        }
        return $data;
    }

    private function load_data(): void {
        $this->runtime = $this->load_json('corpus-runtime.json');
        $this->index = $this->load_json('retrieval-index.json');
        $relationship_data = $this->load_json('relationships.json');
        $this->relationships = $relationship_data['relationships'] ?? [];

        foreach (($this->runtime['resources'] ?? []) as $resource) {
            if (!empty($resource['id'])) {
                $this->by_id[(string)$resource['id']] = $resource;
            }
        }
        foreach ($this->relationships as $relationship) {
            $from = (string)($relationship['from'] ?? '');
            if ($from !== '') {
                $this->from[$from][] = $relationship;
            }
        }
    }

    public function corpus_status(): array {
        return [
            'version' => (string)($this->runtime['version'] ?? ''),
            'resources' => count($this->by_id),
            'relationships' => count($this->relationships),
        ];
    }

    public function navigate(array $input, string $api_key): array {
        $choice = $this->clean((string)($input['choice'] ?? ''));
        $situation = $this->clean((string)($input['situation'] ?? ''));
        $possibility = $this->clean((string)($input['possibility'] ?? ''));
        if ($situation === '' && $possibility === '') {
            throw new InvalidArgumentException('A situation or possibility is required.');
        }
        if ($api_key === '') {
            throw new RuntimeException('The Groq API key has not been configured.');
        }

        $raw_input = [
            'entry_choice' => $choice,
            'situation' => $situation,
            'possibility' => $possibility,
        ];

        try {
            $interpretation = $this->interpret($api_key, $raw_input);
        } catch (Throwable $e) {
            // Mirror The Guide's deterministic provider recovery principle:
            // provider failure must not erase the visitor's path. Preserve the
            // visitor's own words and continue using only the local corpus.
            if (strpos(strtolower($e->getMessage()), 'rejected the configured api key') !== false) {
                throw $e;
            }
            $interpretation = $this->deterministic_interpretation($raw_input);
        }

        $search_terms = is_array($interpretation['search_terms'] ?? null) ? $interpretation['search_terms'] : [];
        $query = implode(' ', array_merge([$choice, $situation, $possibility], $search_terms, [
            (string)($interpretation['responsibility'] ?? ''),
            (string)($interpretation['tension'] ?? ''),
            (string)($interpretation['capacity'] ?? ''),
            (string)($interpretation['movement'] ?? ''),
            implode(' ', is_array($interpretation['constitutional_questions'] ?? null) ? $interpretation['constitutional_questions'] : []),
        ]));

        $candidates = $this->expand($this->retrieve($query, 60, $interpretation), 60);
        $candidates = $this->balance_domains($candidates, 40);
        $candidates = array_values(array_filter($candidates, function ($candidate) {
            $r = $candidate['resource'];
            return ($r['endpoint_eligible'] ?? null) === true
                && !empty($r['url'])
                && !empty($r['title'])
                && ($r['resource_type'] ?? '') !== 'access'
                && !in_array(($r['content_access_status'] ?? ''), ['unresolved', 'referenced_but_not_individually_indexed'], true);
        }));

        if (!$candidates) {
            throw new RuntimeException('No eligible canonical resources were retrieved.');
        }

        try {
            $decision = $this->choose($api_key, $interpretation, $candidates);
        } catch (Throwable $e) {
            if (strpos(strtolower($e->getMessage()), 'rejected the configured api key') !== false) {
                throw $e;
            }
            $decision = $this->deterministic_decision($candidates);
        }
        $selected_ids = is_array($decision['selected_ids'] ?? null) ? $decision['selected_ids'] : [];

        $selected = [];
        foreach ($selected_ids as $id) {
            $id = (string)$id;
            if (!isset($this->by_id[$id])) {
                continue;
            }
            $r = $this->by_id[$id];
            if (!$this->is_eligible($r)) {
                continue;
            }
            $selected[] = $this->public_resource($r);
            if (count($selected) >= 3) break;
        }

        if (count($selected) < 3 && count($candidates) >= 3) {
            foreach ($candidates as $candidate) {
                $r = $candidate['resource'] ?? [];
                if (!$this->is_eligible($r)) continue;
                $id = (string)($r['id'] ?? '');
                $already = false;
                foreach ($selected as $resource) {
                    if ((string)$resource['id'] === $id) { $already = true; break; }
                }
                if ($already) continue;
                $selected[] = $this->public_resource($r);
                if (count($selected) >= 3) break;
            }
        }

        if (count($selected) < 3) {
            throw new RuntimeException('The coherence layer could not produce three eligible canonical destinations.');
        }

        $why_each = [];
        foreach (($decision['why_each'] ?? []) as $item) {
            if (is_array($item) && isset($item['id'])) {
                $why_each[(string)$item['id']] = $this->clean((string)($item['reason'] ?? ''));
            }
        }
        $safe_why = [];
        foreach ($selected as $resource) {
            $id = $resource['id'];
            $safe_why[$id] = !empty($why_each[$id]) ? $why_each[$id] : '';
        }

        return [
            'version' => '3.4.0',
            'reflection' => $this->clean((string)($decision['reflection'] ?? 'There is something here worth staying with.')),
            'selected' => $selected,
            'why_each' => $safe_why,
            'needs_clarification' => !empty($decision['needs_clarification']),
            'clarifying_question' => $this->clean((string)($decision['clarifying_question'] ?? '')),
            'movement_type' => $this->clean((string)($decision['movement_type'] ?? 'continue')),
            'landscape' => $this->landscape_destinations(),
        ];
    }

    private function is_eligible(array $r): bool {
        return ($r['endpoint_eligible'] ?? null) === true
            && !empty($r['url'])
            && !empty($r['title'])
            && ($r['resource_type'] ?? '') !== 'access'
            && !in_array(($r['content_access_status'] ?? ''), ['unresolved', 'referenced_but_not_individually_indexed'], true);
    }

    private function public_resource(array $r): array {
        $out = [
            'id' => (string)$r['id'],
            'title' => wp_strip_all_tags((string)$r['title']),
            'url' => esc_url_raw((string)$r['url']),
            'resource_type' => (string)($r['resource_type'] ?? ''),
            'domain' => (string)($r['domain'] ?? ''),
            'content_access_status' => (string)($r['content_access_status'] ?? ''),
        ];
        return $out;
    }

    private function landscape_destinations(): array {
        return [
            ['title' => 'Stewardship Archive', 'url' => 'https://geralddaquila.com/stewardship-archive/'],
            ['title' => 'Learning Arcs', 'url' => 'https://geralddaquila.com/steward-access-12-learning-arcs/'],
            ['title' => 'Governance & Institution Building', 'url' => 'https://geralddaquila.com/governance-institution-building/'],
            ['title' => 'Stewardship Practice', 'url' => 'https://geralddaquila.com/stewardship-practice/'],
            ['title' => 'Stewardship Case Library', 'url' => 'https://geralddaquila.com/applied-stewardship-case-library/'],
            ['title' => 'Stewardship Frameworks', 'url' => 'https://geralddaquila.com/stewardship-framework/'],
            ['title' => 'Coherent Leadership Selection System', 'url' => 'https://geralddaquila.com/coherent-leadership-selection-system-clss-2/'],
            ['title' => 'Stewardship Readiness Institute', 'url' => 'https://geralddaquila.com/professional-framework/professional-framework/'],
        ];
    }

    private function retrieve(string $query, int $limit = 40, array $interpretation = []): array {
        $query_tokens = array_values(array_unique($this->tokens($query)));
        $query_set = array_fill_keys($query_tokens, true);
        $scores = [];

        foreach ($query_tokens as $token) {
            foreach (($this->index['postings'][$token] ?? []) as $posting) {
                if (!is_array($posting) || count($posting) < 2) continue;
                $id = (string)$posting[0];
                $weight = (float)$posting[1];
                $scores[$id] = ($scores[$id] ?? 0.0) + $weight;
            }
        }

        // Add a bounded metadata layer. The corpus already carries editorial
        // situation/capacity tags; use them as structured signals rather than
        // relying on lexical occurrence alone.
        $interpretation_text = implode(' ', [
            (string)($interpretation['responsibility'] ?? ''),
            (string)($interpretation['tension'] ?? ''),
            (string)($interpretation['capacity'] ?? ''),
            (string)($interpretation['movement'] ?? ''),
            (string)($interpretation['scale'] ?? ''),
            (string)($interpretation['appreciative_signal'] ?? ''),
            implode(' ', is_array($interpretation['constitutional_questions'] ?? null) ? $interpretation['constitutional_questions'] : []),
            implode(' ', is_array($interpretation['search_terms'] ?? null) ? $interpretation['search_terms'] : []),
        ]);
        $signal_tokens = array_values(array_unique($this->tokens($interpretation_text . ' ' . $query)));
        $signal_set = array_fill_keys($signal_tokens, true);
        $constitutional_signal = !empty($interpretation['constitutional_questions'])
            || isset($signal_set['constitutional'])
            || isset($signal_set['constitution']);

        foreach ($this->by_id as $id => $resource) {
            $tag_tokens = [];
            foreach (['situation_tags', 'capacity_tags'] as $field) {
                foreach (($resource[$field] ?? []) as $tag) {
                    $tag_tokens = array_merge($tag_tokens, $this->tokens((string)$tag));
                }
            }
            if (!$tag_tokens) continue;
            $tag_hits = 0;
            foreach (array_unique($tag_tokens) as $tag_token) {
                if (isset($query_set[$tag_token]) || isset($signal_set[$tag_token])) $tag_hits++;
            }
            if ($tag_hits > 0) {
                $scores[$id] = ($scores[$id] ?? 0.0) + min(4.0, $tag_hits * 1.25);
            }
            if ($constitutional_signal && ($resource['domain'] ?? '') === 'T4') {
                $scores[$id] = ($scores[$id] ?? 0.0) + 1.5;
            }
        }

        arsort($scores, SORT_NUMERIC);
        $out = [];
        foreach (array_slice($scores, 0, $limit, true) as $id => $score) {
            if (isset($this->by_id[$id])) {
                $out[] = ['resource' => $this->by_id[$id], 'score' => (float)$score];
            }
        }
        return $out;
    }

    private function balance_domains(array $candidates, int $limit = 40): array {
        $groups = ['T2_T3' => [], 'T4' => [], 'other' => []];
        foreach ($candidates as $candidate) {
            $domain = (string)($candidate['resource']['domain'] ?? 'other');
            if (!isset($groups[$domain])) $domain = 'other';
            $groups[$domain][] = $candidate;
        }
        foreach ($groups as &$group) {
            usort($group, static function(array $a, array $b): int {
                return ((float)($b['score'] ?? 0)) <=> ((float)($a['score'] ?? 0));
            });
        }
        unset($group);

        // Preserve the strongest candidates from each canonical domain so the
        // coherence layer can genuinely compare T2–T3 and T4. This does not
        // force either domain into the final three doors.
        $out = [];
        $per_domain = max(1, intdiv($limit, 2));
        foreach (['T2_T3', 'T4'] as $domain) {
            foreach (array_slice($groups[$domain], 0, $per_domain) as $candidate) {
                $out[] = $candidate;
            }
        }
        foreach ($groups['other'] as $candidate) {
            if (count($out) >= $limit) break;
            $out[] = $candidate;
        }
        if (count($out) < $limit) {
            $seen = [];
            foreach ($out as $candidate) $seen[(string)$candidate['resource']['id']] = true;
            foreach (array_merge($groups['T2_T3'], $groups['T4']) as $candidate) {
                $id = (string)$candidate['resource']['id'];
                if (isset($seen[$id])) continue;
                $out[] = $candidate;
                $seen[$id] = true;
                if (count($out) >= $limit) break;
            }
        }
        usort($out, static function(array $a, array $b): int {
            return ((float)($b['score'] ?? 0)) <=> ((float)($a['score'] ?? 0));
        });
        return array_slice($out, 0, $limit);
    }

    private function expand(array $candidates, int $limit = 50): array {
        $scores = [];
        foreach ($candidates as $candidate) {
            $id = (string)$candidate['resource']['id'];
            $scores[$id] = max($scores[$id] ?? 0.0, (float)$candidate['score']);
        }
        foreach (array_slice($candidates, 0, 16) as $candidate) {
            $id = (string)$candidate['resource']['id'];
            foreach (($this->from[$id] ?? []) as $relationship) {
                $to = (string)($relationship['to'] ?? '');
                if ($to === '' || !isset($this->by_id[$to])) continue;
                $type = (string)($relationship['type'] ?? '');
                $boost = in_array($type, ['grounds', 'belongs_to', 'extends_into', 'prepares_for'], true) ? 1.5 : 0.8;
                $score = ((float)$candidate['score'] * 0.72) + $boost;
                $scores[$to] = max($scores[$to] ?? 0.0, $score);
            }
        }
        arsort($scores, SORT_NUMERIC);
        $out = [];
        foreach (array_slice($scores, 0, $limit, true) as $id => $score) {
            if (isset($this->by_id[$id])) $out[] = ['resource' => $this->by_id[$id], 'score' => (float)$score];
        }
        return $out;
    }

    private function deterministic_interpretation(array $input): array {
        $situation = $this->clean((string)($input['situation'] ?? ''));
        $possibility = $this->clean((string)($input['possibility'] ?? ''));
        return [
            'situation' => $situation,
            'responsibility' => '',
            'tension' => '',
            'capacity' => '',
            'movement' => '',
            'scale' => '',
            'appreciative_signal' => '',
            'constitutional_questions' => [],
            'search_terms' => $this->tokens($situation . ' ' . $possibility),
            'competing_interpretations' => [],
        ];
    }

    private function deterministic_decision(array $candidates): array {
        $ids = [];
        foreach ($candidates as $candidate) {
            $r = $candidate['resource'] ?? [];
            if (!$this->is_eligible($r)) continue;
            $id = (string)$r['id'];
            if ($id === '' || in_array($id, $ids, true)) continue;
            $ids[] = $id;
            if (count($ids) >= 3) break;
        }
        $why = [];
        foreach ($ids as $id) {
            $why[] = [
                'id' => $id,
                'reason' => '',
            ];
        }
        return [
            'reflection' => 'There is something here worth staying with.',
            'selected_ids' => $ids,
            'why_each' => $why,
            'needs_clarification' => false,
            'clarifying_question' => '',
            'movement_type' => 'continue',
        ];
    }

    private function interpret(string $api_key, array $input): array {
        $schema = [
            'type' => 'object',
            'properties' => [
                'situation' => ['type' => 'string'],
                'responsibility' => ['type' => 'string'],
                'tension' => ['type' => 'string'],
                'capacity' => ['type' => 'string'],
                'movement' => ['type' => 'string'],
                'scale' => ['type' => 'string'],
                'appreciative_signal' => ['type' => 'string'],
                'constitutional_questions' => ['type' => 'array', 'items' => ['type' => 'string']],
                'search_terms' => ['type' => 'array', 'items' => ['type' => 'string']],
                'competing_interpretations' => ['type' => 'array', 'items' => ['type' => 'string']],
            ],
            'required' => ['situation','responsibility','tension','capacity','movement','scale','appreciative_signal','constitutional_questions','search_terms','competing_interpretations'],
            'additionalProperties' => false,
        ];
        return $this->groq_json($api_key, [
            [
                'role' => 'system',
                'content' => 'You are the hidden interpretation layer of a Stewardship pathway tool. The visitor has already crossed Steward Access and belongs inside the work. Never assess readiness, belonging, worthiness, level, personality, competence, or eligibility. Never diagnose or rank. Interpret the human situation so canonical resources can be found. Preserve ambiguity. Do not invent facts. Use ordinary language in the fields. constitutional_questions should contain only genuine constitutional questions raised by the situation; otherwise an empty array. search_terms should be concise concepts useful for retrieval.',
            ],
            ['role' => 'user', 'content' => wp_json_encode($input, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES)],
        ], $schema, 900);
    }

    private function choose(string $api_key, array $interpretation, array $candidates): array {
        $packet = [];
        foreach (array_slice($candidates, 0, 18) as $i => $candidate) {
            $r = $candidate['resource'];
            $packet[] = [
                'rank' => $i + 1,
                'id' => (string)$r['id'],
                'title' => wp_strip_all_tags((string)$r['title']),
                'domain' => (string)($r['domain'] ?? ''),
                'type' => (string)($r['resource_type'] ?? ''),
                'access' => (string)($r['content_access_status'] ?? ''),
                'situation_tags' => $r['situation_tags'] ?? [],
                'capacity_tags' => $r['capacity_tags'] ?? [],
                'excerpt' => function_exists('mb_substr') ? mb_substr(wp_strip_all_tags((string)($r['content'] ?? '')), 0, 600) : substr(wp_strip_all_tags((string)($r['content'] ?? '')), 0, 600),
            ];
        }
        $schema = [
            'type' => 'object',
            'properties' => [
                'reflection' => ['type' => 'string'],
                'selected_ids' => ['type' => 'array', 'items' => ['type' => 'string'], 'minItems' => 3, 'maxItems' => 3],
                'why_each' => ['type' => 'array', 'items' => ['type' => 'object', 'properties' => ['id' => ['type' => 'string'], 'reason' => ['type' => 'string']], 'required' => ['id','reason'], 'additionalProperties' => false]],
                'needs_clarification' => ['type' => 'boolean'],
                'clarifying_question' => ['type' => 'string'],
                'movement_type' => ['type' => 'string', 'enum' => ['deepening','expanding','integrating','re-entry','continue']],
            ],
            'required' => ['reflection','selected_ids','why_each','needs_clarification','clarifying_question','movement_type'],
            'additionalProperties' => false,
        ];
        $decision = $this->groq_json($api_key, [
            [
                'role' => 'system',
                'content' => 'You are the coherence layer of a Stewardship pathway engine. Choose exactly three canonical individual resources from the supplied candidates whenever at least three defensible candidates are supplied. The response schema requires exactly three selections; do not return one or two. Select three distinct resources that form a coherent continuation of the visitor’s question. Never pad with an arbitrary resource just to satisfy the count. T2–T3 and T4 are co-equal; do not force one of each. Do not choose by keyword alone. Choose where the visitor’s present question can genuinely continue. Never invent an ID. Never select an access/threshold resource or a category/collection page as a final door. Cases are secondary unless they genuinely illuminate the question. T4 is constitutional ground, not a higher level. If ambiguity is meaningful, preserve it and optionally ask one clarifying question. The reflection and reasons must sound like a patient, wise human guide—not a machine, assessment, or formula. Do not mention scores, signals, algorithms, formation, or AI.',
            ],
            ['role' => 'user', 'content' => wp_json_encode(['interpretation' => $interpretation, 'candidates' => $packet], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES)],
        ], $schema, 1600);
        return $decision;
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
                    'name' => 'stewardship_pathway_response',
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
        $stop = array_flip(preg_split('/\s+/', 'the and of to in a for on with from into by as is are be this that what when where how an or not you your their our its it they them we us can may will through about after before between within across under over more less very all one two three four five six seven eight nine ten', -1, PREG_SPLIT_NO_EMPTY));
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
