from general_guide_composition import _composition_response_shape_diagnostic, _normalize_composition_envelope


def test_composition_response_shape_diagnostic_reports_only_safe_metadata():
    private_answer = "PRIVATE GENERATED ANSWER MUST NOT BE LOGGED"
    parsed = {
        "response": private_answer,
        "response_shape": "general",
        "adaptive_adjudication": {"status": "accepted"},
    }

    diagnostic = _composition_response_shape_diagnostic(parsed, '{"response":"..."}')

    assert "response_key_present=True" in diagnostic
    assert "response_type=str" in diagnostic
    assert f"response_raw_chars={len(private_answer)}" in diagnostic
    assert "response_sanitized_chars=" in diagnostic
    assert "envelope_chars=" in diagnostic
    assert "top_level_keys=adaptive_adjudication,response,response_shape" in diagnostic
    assert private_answer not in diagnostic


def test_composition_response_shape_diagnostic_distinguishes_missing_and_empty_response():
    missing = _composition_response_shape_diagnostic({"response_shape": "general"}, "{}")
    empty = _composition_response_shape_diagnostic({"response": "", "response_shape": "general"}, '{"response":""}')

    assert "response_key_present=False" in missing
    assert "response_type=NoneType" in missing
    assert "response_key_present=True" in empty
    assert "response_type=str" in empty
    assert "response_raw_chars=0" in empty



def test_composition_response_shape_diagnostic_reports_alternate_envelope_metadata_without_content():
    private_answer = "PRIVATE ANSWER TEXT MUST NEVER APPEAR"
    parsed = {
        "answer": private_answer,
        "doorway": {"title": "A private doorway title", "url": "https://example.invalid/private"},
    }

    diagnostic = _composition_response_shape_diagnostic(parsed, '{"answer":"..."}')

    assert "answer_key_present=True" in diagnostic
    assert "answer_type=str" in diagnostic
    assert f"answer_raw_chars={len(private_answer)}" in diagnostic
    assert "answer_sanitized_chars=" in diagnostic
    assert "doorway_type=dict" in diagnostic
    assert "doorway_keys=title,url" in diagnostic
    assert private_answer not in diagnostic
    assert "A private doorway title" not in diagnostic
    assert "https://example.invalid/private" not in diagnostic



def test_alternate_answer_envelope_normalizes_without_trusting_provider_doorway():
    answer = "A substantive visitor-facing answer with more than enough content to validate."
    normalized = _normalize_composition_envelope({
        "answer": answer,
        "doorway": "Provider-supplied doorway metadata",
    })

    assert normalized["response"] == answer
    assert normalized["response_shape"] == "general"
    assert "doorway_title" not in normalized
    assert "doorway" in normalized


def test_alternate_answer_envelope_does_not_coerce_non_string_answer():
    normalized = _normalize_composition_envelope({
        "answer": {"text": "must not be coerced"},
    })

    assert "response" not in normalized
    assert normalized["response_shape"] == "general"


def test_explicit_response_takes_precedence_over_alternate_answer():
    normalized = _normalize_composition_envelope({
        "response": "Canonical response field wins.",
        "answer": "Conflicting alternate answer must be ignored.",
        "response_shape": "direct",
    })

    assert normalized["response"] == "Canonical response field wins."
    assert normalized["response_shape"] == "direct"
