from general_guide_composition import _composition_response_shape_diagnostic


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
