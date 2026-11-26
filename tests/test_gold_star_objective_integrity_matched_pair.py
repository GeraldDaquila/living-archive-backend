import json
from pathlib import Path

import gold_star_lessons
from scripts.capture_gold_star_matched_pairs import _load_cases


ROOT = Path(__file__).resolve().parents[1]
CASE_SET = ROOT / "docs" / "qa" / "objective_integrity_matched_pair_cases.json"
TARGET_ID = "general-guide-developmental-stewardship-objective-integrity-2026-11-26"


def test_objective_integrity_pilot_is_preregistered_across_three_heldout_families():
    suite, cases, target = _load_cases(CASE_SET)
    assert suite["evaluation_id"] == "gold-star-objective-integrity-heldout-pilot-2026-11-26"
    assert target == TARGET_ID
    assert len(cases) == 6
    assert len({case["case_family"] for case in cases}) == 3
    assert all(case["case_id"].startswith("heldout-objective-integrity-") for case in cases)
    assert "community garden" not in " ".join(case["query"].lower() for case in cases)
    assert "school" not in " ".join(case["query"].lower() for case in cases)


def test_target_gold_star_is_retrieved_for_every_heldout_objective_integrity_case():
    suite, cases, target = _load_cases(CASE_SET)
    for case in cases:
        candidates = gold_star_lessons.select_lesson_candidates(case["query"], limit=4)
        assert target in {item["benchmark_id"] for item in candidates}, case["case_id"]


def test_objective_integrity_gold_star_is_excluded_from_unrelated_negative_control():
    suite, _, target = _load_cases(CASE_SET)
    candidates = gold_star_lessons.select_lesson_candidates(
        suite["negative_control_query"], limit=4
    )
    assert target not in {item["benchmark_id"] for item in candidates}


def test_each_case_has_a_case_specific_rubric_and_primary_transfer_dimension():
    _, cases, _ = _load_cases(CASE_SET)
    for case in cases:
        assert len(case["rubric"]) >= 4
        assert "objective_integrity_reasoning" in case["critical_dimensions"]
        assert len(set(case["critical_dimensions"])) == len(case["critical_dimensions"])

def test_gemini_pilot_is_separately_preregistered_after_groq_control_arm_rate_limit():
    from scripts.capture_gold_star_matched_pairs import _load_cases

    path = ROOT / "docs" / "qa" / "objective_integrity_matched_pair_cases_gemini.json"
    suite, cases, target = _load_cases(path)
    assert suite["evaluation_id"] == "gold-star-objective-integrity-heldout-pilot-gemini-2026-11-26"
    assert target == TARGET_ID
    assert suite["design"]["provider_pin"] == {
        "provider": "gemini",
        "model": "gemini-3.8-flash",
    }
    assert len(cases) == 6
    assert len({case["case_family"] for case in cases}) == 3
    assert "before any treatment arm ran" in suite["purpose"]


def test_gemini_heldout_queries_retrieve_target_and_negative_control_excludes_it():
    import gold_star_lessons
    from scripts.capture_gold_star_matched_pairs import _load_cases

    path = ROOT / "docs" / "qa" / "objective_integrity_matched_pair_cases_gemini.json"
    suite, cases, target = _load_cases(path)
    for case in cases:
        selected = gold_star_lessons.select_lesson_candidates(case["query"], limit=4)
        assert target in {item["benchmark_id"] for item in selected}, case["case_id"]
    negative = gold_star_lessons.select_lesson_candidates(suite["negative_control_query"], limit=4)
    assert target not in {item["benchmark_id"] for item in negative}


def test_generation_fingerprint_describes_actual_gemini_payload_not_groq_defaults():
    from scripts.capture_gold_star_matched_pairs import _generation_config_for_lane

    config = _generation_config_for_lane("gemini", "gemini-3.8-flash", {
        "route_operation": "general_guide_composition",
        "max_tokens": 1800,
        "schema_mode": "json_schema_best_effort",
        "schema_sha256": "effective-gemini-schema-sha",
        "provider_timeout_seconds": 10,
    }, 65)
    assert config["max_output_tokens"] == 1800
    assert config["temperature"] == "not_supplied_provider_default"
    assert config["response_mime_type"] == "application/json"
    assert config["response_schema_transform"] == "gemini_compatible_drop_additionalProperties"
    assert config["system_instruction"] == "separate_systemInstruction"
    assert config["thinking_level"] == "low"
    assert "reasoning_effort" not in config
    assert "max_completion_tokens" not in config


def test_workers_ai_pilot_is_separately_preregistered_after_groq_and_gemini_quota_failures():
    from scripts.capture_gold_star_matched_pairs import _load_cases

    path = ROOT / "docs" / "qa" / "objective_integrity_matched_pair_cases_workers_ai.json"
    suite, cases, target = _load_cases(path)
    assert suite["evaluation_id"] == "gold-star-objective-integrity-heldout-pilot-workers-ai-2026-11-26"
    assert target == TARGET_ID
    assert suite["design"]["provider_pin"] == {
        "provider": "workers_ai",
        "model": "@cf/zai-org/glm-4.7-flash",
    }
    assert len(cases) == 6
    assert len({case["case_family"] for case in cases}) == 3
    assert "before any treatment arm ran" in suite["purpose"]


def test_workers_ai_heldout_queries_retrieve_target_and_negative_control_excludes_it():
    import gold_star_lessons
    from scripts.capture_gold_star_matched_pairs import _load_cases

    path = ROOT / "docs" / "qa" / "objective_integrity_matched_pair_cases_workers_ai.json"
    suite, cases, target = _load_cases(path)
    for case in cases:
        selected = gold_star_lessons.select_lesson_candidates(case["query"], limit=4)
        assert target in {item["benchmark_id"] for item in selected}, case["case_id"]
    negative = gold_star_lessons.select_lesson_candidates(suite["negative_control_query"], limit=4)
    assert target not in {item["benchmark_id"] for item in negative}


def test_workers_ai_generation_fingerprint_describes_actual_payload():
    from scripts.capture_gold_star_matched_pairs import _generation_config_for_lane

    config = _generation_config_for_lane("workers_ai", "@cf/zai-org/glm-4.7-flash", {
        "route_operation": "general_guide_composition",
        "max_tokens": 1800,
        "schema_mode": "json_schema_best_effort",
        "schema_sha256": "effective-workers-schema-sha",
        "provider_timeout_seconds": 10,
    }, 65)
    assert config["max_tokens"] == 1800
    assert config["temperature"] == 0.0
    assert config["response_format"] == "json_schema"
    assert config["options_reject_if_busy"] is True
    assert config["message_adapter"] == "_workers_normalize_messages"
    assert config["transport_retry_policy"] == "single_http_attempt_no_provider_sdk_retry"


def test_groq_20b_pilot_is_separately_preregistered_after_model_scoped_120b_rate_limit():
    from scripts.capture_gold_star_matched_pairs import _load_cases

    path = ROOT / "docs" / "qa" / "objective_integrity_matched_pair_cases_groq_20b.json"
    suite, cases, target = _load_cases(path)
    assert suite["evaluation_id"] == "gold-star-objective-integrity-heldout-pilot-groq-20b-2026-11-26"
    assert target == TARGET_ID
    assert suite["design"]["provider_pin"] == {
        "provider": "groq",
        "model": "openai/gpt-oss-20b",
    }
    assert len(cases) == 6
    assert len({case["case_family"] for case in cases}) == 3
    assert "model-scoped HTTP 429" in suite["purpose"]


def test_groq_20b_heldout_queries_retrieve_target_and_negative_control_excludes_it():
    import gold_star_lessons
    from scripts.capture_gold_star_matched_pairs import _load_cases

    path = ROOT / "docs" / "qa" / "objective_integrity_matched_pair_cases_groq_20b.json"
    suite, cases, target = _load_cases(path)
    for case in cases:
        selected = gold_star_lessons.select_lesson_candidates(case["query"], limit=4)
        assert target in {item["benchmark_id"] for item in selected}, case["case_id"]
    negative = gold_star_lessons.select_lesson_candidates(suite["negative_control_query"], limit=4)
    assert target not in {item["benchmark_id"] for item in negative}
