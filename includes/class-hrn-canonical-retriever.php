<?php
if (!defined('ABSPATH')) { exit; }

final class HRN_Canonical_Retriever {
    private $runtime = array();
    private $index = array();
    private $by_id = array();
    private $protected_runtime = array();
    private $protected_index = array();
    private $protected_by_id = array();
    private $cartography = array();

    public function __construct($data_dir) {
        $data_dir = rtrim($data_dir, '/\\');
        $this->runtime = $this->load_json($data_dir . '/corpus-runtime.json');
        $this->index = $this->load_json($data_dir . '/retrieval-index.json');
        $cartography_file = $data_dir . '/archive-cartography.json';
        if (is_readable($cartography_file)) $this->cartography = $this->load_json($cartography_file);
        foreach (($this->runtime['resources'] ?? array()) as $resource) {
            if (!empty($resource['id'])) $this->by_id[(string)$resource['id']] = $resource;
        }

        $protected_file = $data_dir . '/stewardship-protected.php';
        if (is_readable($protected_file)) {
            $protected = require $protected_file;
            if (is_array($protected)) {
                $this->protected_runtime = $protected;
                foreach (($protected['resources'] ?? array()) as $resource) {
                    if (!empty($resource['id'])) $this->protected_by_id[(string)$resource['id']] = $resource;
                }
            }
        }
        $protected_index_file = $data_dir . '/t4-retrieval-index.json';
        if (is_readable($protected_index_file)) {
            $this->protected_index = $this->load_json($protected_index_file);
        }
    }

    public function status() {
        $tiers = (array)($this->runtime['tier_counts'] ?? array());
        if (!empty($this->protected_by_id)) $tiers['T4'] = count($this->protected_by_id);
        return array(
            'schema_version' => (string)($this->runtime['schema_version'] ?? ''),
            'resource_count' => count($this->by_id) + count($this->protected_by_id),
            'document_count' => (int)($this->index['document_count'] ?? count($this->by_id)) + (int)($this->protected_index['document_count'] ?? count($this->protected_by_id)),
            'tier_counts' => $tiers,
            'relationships_included' => false,
            'cartography_included' => !empty($this->cartography['territories']),
            'cartography_basis' => (string)($this->cartography['basis'] ?? ''),
            'public_source' => 'Public Living Archive Navigator canonical snapshot',
            'protected_source' => empty($this->protected_by_id) ? 'unavailable' : 'T4 protected canonical registry',
        );
    }

    public function retrieve($query, $limit=5, $interpretation=array(), $include_protected=false) {
        $query = trim((string)$query);
        $limit = max(1, min(5, (int)$limit));
        if ($query === '') return array();

        $public = $this->retrieve_from_index($query, $limit, $interpretation, $this->index, $this->by_id, false);
        $protected = $include_protected && !empty($this->protected_by_id)
            ? $this->retrieve_from_index($query, $limit, $interpretation, $this->protected_index, $this->protected_by_id, true)
            : array();

        $out = array_merge($public, $protected);
        usort($out, static function($a, $b) {
            $aa = (float)($a['anchor_score'] ?? $a['score'] ?? 0);
            $bb = (float)($b['anchor_score'] ?? $b['score'] ?? 0);
            return $bb <=> $aa;
        });
        return array_slice($out, 0, $limit);
    }

    public function protected_horizon($query, $limit=3, $interpretation=array()) {
        if (empty($this->protected_by_id)) return array();
        $matches = $this->retrieve_from_index($query, max(1, min(3, (int)$limit)), $interpretation, $this->protected_index, $this->protected_by_id, true);
        $out = array();
        foreach ($matches as $match) {
            $r = $match['resource'];
            $out[] = array(
                'id' => (string)($r['id'] ?? ''),
                'title' => wp_strip_all_tags((string)($r['title'] ?? '')),
                'score' => (float)($match['anchor_score'] ?? $match['score'] ?? 0),
                'tier' => 'T4',
            );
        }
        return $out;
    }

    private function retrieve_from_index($query, $limit, $interpretation, $index, $by_id, $protected) {
        $tokens = $this->tokens($query);
        if (!$tokens || !is_array($index) || empty($by_id)) return array();

        $scores = array();
        $evidence = array();
        $N = max(1, (int)($index['document_count'] ?? count($by_id)));
        $max_df = (int)floor($N * 0.08);

        foreach ($tokens as $token) {
            $postings = $index['postings'][$token] ?? array();
            $df = max(1, count($postings));
            if ($df > $max_df) continue;
            $idf = log(($N + 1) / ($df + 1)) + 1;
            foreach ($postings as $posting) {
                if (!is_array($posting) || count($posting) < 2) continue;
                $id = (string)$posting[0];
                if (!isset($by_id[$id])) continue;
                $weight = (float)$posting[1];
                $scores[$id] = ($scores[$id] ?? 0.0) + ($weight * $idf);
                $evidence[$id]['raw_terms'][$token] = true;
            }
        }

        $interpretation_text = implode(' ', array(
            (string)($interpretation['pattern'] ?? ''),
            (string)($interpretation['responsibility'] ?? ''),
            (string)($interpretation['tension'] ?? ''),
            (string)($interpretation['capacity'] ?? ''),
            (string)($interpretation['movement'] ?? ''),
            (string)($interpretation['scale'] ?? ''),
            (string)($interpretation['mode_of_inquiry'] ?? ''),
            (string)($interpretation['appreciative_signal'] ?? ''),
            (string)($interpretation['service_orientation'] ?? ''),
            (string)($interpretation['possibility'] ?? ''),
            implode(' ', is_array($interpretation['search_terms'] ?? null) ? $interpretation['search_terms'] : array())
        ));
        $interpretation_tokens = $this->tokens($interpretation_text);

        foreach (array_keys($scores) as $id) {
            $r = $by_id[$id];
            $resource_text = strtolower(implode(' ', array(
                (string)($r['title'] ?? ''),
                (string)($r['excerpt'] ?? ''),
                implode(' ', is_array($r['source_categories'] ?? null) ? $r['source_categories'] : array()),
            )));
            $resource_tokens = array_fill_keys($this->tokens($resource_text), true);
            $hits = 0;
            foreach ($interpretation_tokens as $t) if (isset($resource_tokens[$t])) $hits++;
            if ($hits > 0) $scores[$id] += min(2.5, $hits * 0.35);
        }

        // Archive cartography does not replace lexical retrieval; it gives the
        // navigator a map of the territory so a conceptually adjacent doorway
        // can outrank a merely word-matching resource. The map is derived from
        // canonical tags/titles/excerpts and explicitly makes no claim of
        // canonical relationship edges.
        $requested_territories = $this->normalize_terms($interpretation['archive_territories'] ?? array());
        $requested_perspectives = $this->normalize_terms($interpretation['archive_perspectives'] ?? array());
        if (!empty($requested_territories) || !empty($requested_perspectives)) {
            // Seed candidates from the map even when lexical overlap is weak.
            // This is the step that turns cartography from annotation into
            // navigation: a neighboring territory can surface a doorway that
            // the visitor did not name explicitly.
            if (!empty($requested_territories) && !empty($this->cartography['resources'])) {
                foreach ($by_id as $id => $r) {
                    if (!$this->is_eligible($r, $protected)) continue;
                    $cm = $this->cartography['resources'][$id] ?? array();
                    $territories = array_map('strtolower', (array)($cm['territories'] ?? array()));
                    $t_hits = count(array_intersect($requested_territories, $territories));
                    if ($t_hits > 0) {
                        $strengths = (array)($cm['territory_strength'] ?? array());
                        $seed = 0.6 + ($t_hits * 1.15);
                        foreach ($requested_territories as $rt) {
                            $seed += min(1.5, (float)($strengths[$rt] ?? 0) * 0.35);
                        }
                        if (!isset($scores[$id]) || $scores[$id] < $seed) $scores[$id] = $seed;
                    }
                }
            }
            foreach (array_keys($scores) as $id) {
                $cm = $this->cartography['resources'][$id] ?? array();
                $territories = array_map('strtolower', (array)($cm['territories'] ?? array()));
                $perspectives = array_map('strtolower', (array)($cm['perspectives'] ?? array()));
                $t_hits = count(array_intersect($requested_territories, $territories));
                $p_hits = count(array_intersect($requested_perspectives, $perspectives));
                if ($t_hits > 0) $scores[$id] += min(4.5, $t_hits * 1.65);
                if ($p_hits > 0) $scores[$id] += min(2.5, $p_hits * 0.8);
            }
        }

        arsort($scores, SORT_NUMERIC);
        $out = array();
        foreach (array_slice($scores, 0, $limit, true) as $id => $score) {
            if (!isset($by_id[$id])) continue;
            $r = $by_id[$id];
            if (!$this->is_eligible($r, $protected)) continue;
            $raw_terms = array_keys($evidence[$id]['raw_terms'] ?? array());
            $anchor = $this->anchor_score($r, $raw_terms, $query, (float)$score);
            $cm = $this->cartography['resources'][$id] ?? array();
            $out[] = array(
                'resource' => $r,
                'score' => (float)$score,
                'anchor_score' => $anchor['score'],
                'anchor_terms' => $anchor['terms'],
                'anchor_evidence' => $anchor['evidence'],
                'cartography' => $cm,
            );
        }
        return $out;
    }

    private function is_eligible($r, $protected=false) {
        if (!is_array($r) || ($r['endpoint_eligible'] ?? null) !== true) return false;
        if (empty($r['url']) || empty($r['title'])) return false;
        if (!in_array(($r['tier'] ?? ''), $protected ? array('T4') : array('T1','T2','T3'), true)) return false;
        if (!$protected && ($r['source_access_class'] ?? 'public') !== 'public') return false;
        if ($protected && ($r['source_access_class'] ?? '') !== 'steward_protected') return false;
        if (in_array(($r['content_access_status'] ?? ''), array('unresolved','referenced_but_not_individually_indexed'), true)) return false;
        return true;
    }

    private function anchor_score($r, $raw_terms, $raw_query, $lexical_score) {
        $title = strtolower((string)($r['title'] ?? ''));
        $excerpt = strtolower((string)($r['excerpt'] ?? ''));
        $cats = strtolower(implode(' ', is_array($r['source_categories'] ?? null) ? $r['source_categories'] : array()));
        $field_text = $title . ' ' . $excerpt . ' ' . $cats;
        $field_tokens = array_fill_keys($this->tokens($field_text), true);
        $terms = array();
        foreach ($raw_terms as $t) if (isset($field_tokens[$t])) $terms[] = $t;
        $phrase_hits = array();
        $qtokens = $this->tokens($raw_query);
        for ($i=0; $i<count($qtokens)-1; $i++) {
            $phrase = $qtokens[$i] . ' ' . $qtokens[$i+1];
            if (strpos($field_text, $phrase) !== false) $phrase_hits[] = $phrase;
        }
        $field_bonus = count(array_unique($terms)) * 0.75 + count($phrase_hits) * 1.5;
        $title_bonus = 0.0;
        foreach (array_unique($terms) as $t) if (strpos($title, $t) !== false) $title_bonus += 1.5;
        return array(
            'score' => $lexical_score + $field_bonus + $title_bonus,
            'terms' => array_values(array_unique($terms)),
            'evidence' => array(
                'title_terms' => array_values(array_unique(array_filter($terms, function($t) use ($title) { return strpos($title, $t) !== false; }))),
                'field_terms' => array_values(array_unique($terms)),
                'phrases' => array_values(array_unique($phrase_hits)),
            )
        );
    }

    private function normalize_terms($value) {
        if (!is_array($value)) $value = array($value);
        $out = array();
        foreach ($value as $item) {
            if (is_scalar($item)) {
                $v = strtolower(trim((string)$item));
                if ($v !== '') $out[] = $v;
            }
        }
        return array_values(array_unique($out));
    }

    private function tokens($text) {
        $text = strtolower((string)$text);
        $stop = array_flip(preg_split('/\s+/', 'the and of to in a for on with from into by as is are be this that what when where how an or not you your their our its it they them we us can may will through about after before between within across under over more less very all one two three four five six seven eight nine ten without just really also been being do does did have has had would could should shall might must than then there here some any each every both own same other another much many most few several such only still even too via per while whose whom new recently initial became wanted raising dont don know means now first last thing things way ways something someone maybe perhaps sometimes often need needed needs trying tried try get got getting make made making begin beginning began joined join joining', -1, PREG_SPLIT_NO_EMPTY));
        preg_match_all("/[a-z0-9]+(?:['’\-][a-z0-9]+)?/i", $text, $matches);
        $out = array();
        foreach ($matches[0] as $token) {
            if (strlen($token) >= 3 && !isset($stop[$token])) $out[] = $token;
        }
        return array_values(array_unique($out));
    }

    private function load_json($file) {
        if (!is_readable($file)) throw new RuntimeException('HRN canonical data file could not be read: ' . $file);
        $raw = file_get_contents($file);
        $data = json_decode($raw, true);
        if (!is_array($data) || json_last_error() !== JSON_ERROR_NONE) throw new RuntimeException('HRN canonical data JSON is invalid: ' . $file);
        return $data;
    }
}
