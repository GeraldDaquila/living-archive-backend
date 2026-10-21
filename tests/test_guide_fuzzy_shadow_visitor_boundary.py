"""Regression contract: fuzzy relevance diagnostics never cross visitor boundaries.

Source-structure checks guard explicit visitor allowlists; runtime normalization
checks verify that injected diagnostics are stripped from public recommendations.
This does not replace live JSON/SSE end-to-end testing.
"""
import ast
from pathlib import Path

import main

ROOT = Path(__file__).resolve().parents[1]
MAIN = (ROOT / "main.py").read_text(encoding="utf-8")
TREE = ast.parse(MAIN)


def _function(name):
    return next(
        node for node in TREE.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name
    )


def _source(node):
    return ast.get_source_segment(MAIN, node)


def test_shadow_score_is_confined_to_internal_candidate_diagnostics():
    source = _source(_function("_general_guide_authoritative_doorway"))
    assert "_fuzzy_relevance_shadow" in source
    assert "diagnostic" in source.lower()
    # The public doorway is explicitly reconstructed from only canonical title/URL.
    assert 'return {"title": title, "url": url}' in source
    assert '"_fuzzy_relevance_shadow":' not in source


def test_basic_inquiry_visitor_payload_is_an_explicit_allowlist():
    source = _source(_function("_basic_inquiry_response"))
    assert "payload = {" in source
    payload_start = source.index("payload = {")
    payload_end = source.index("\n    }", payload_start)
    payload_source = source[payload_start:payload_end]
    for public_key in (
        '"ok":', '"version":', '"fingerprint":', '"source_sha256":',
        '"request_id":', '"query":', '"intent":', '"response":',
        '"recommendation":', '"answer_basis":', '"processing":',
        '"route_source":', '"visitor_boundary_version":',
    ):
        assert public_key in payload_source
    for diagnostic_key in (
        "_fuzzy_relevance_shadow", "overall_shadow_score",
        "ethical_tradeoff", "harm_repair", "query_title_overlap",
        "query_body_overlap",
    ):
        assert diagnostic_key not in payload_source


def test_public_doorway_normalizer_drops_unrecognized_diagnostic_fields():
    source = _source(_function("_normalize_authoritative_recommendation"))
    assert 'return {"title": title, "url": url}' in source
    assert "_fuzzy_relevance_shadow" not in source
    assert "overall_shadow_score" not in source
