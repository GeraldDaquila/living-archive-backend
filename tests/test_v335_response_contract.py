import ast
from pathlib import Path


def _load_main_source():
    return Path(__file__).resolve().parents[1].joinpath("main.py").read_text(encoding="utf-8")


def test_v335_uses_existing_compact_prompt():
    source = _load_main_source()
    tree = ast.parse(source)
    names = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert "_v335_compact_response_contract" in names
    assert "_v335_build_generation_messages" in names
    assert "COMPACT_GENERATION_SYSTEM_PROMPT" in source
    assert "_LEAN_PROVIDER_SYSTEM_PROMPT" not in source


def test_v335_contract_preserves_intent_binding():
    source = _load_main_source()
    assert "_v335_compact_response_contract(str(query or \"\"), intent)" in source
    assert "_build_response_task_contract(user_query, intent)" in source
    assert "_build_response_task_contract(\n        user_query, \"TOPICAL_INQUIRY\"" not in source


def test_v335_does_not_touch_retrieval_or_link_authority():
    source = _load_main_source()
    assert "fetch_canonical_context" not in source
    assert "select_canonical_doorways" not in source
    assert "sanitize_canonical_links" not in source
    assert "normalize_link_presentation" not in source


def test_v335_core_integrity_guard_is_present():
    source = _load_main_source()
    assert 'EXPECTED_CORE_SOURCE_SHA256 = "ecbd5181958f95baedf397f715fa30ae0192005b9a39f005fe3c0ad8a8fb7ef2"' in source
    assert "_core_runtime_sha != EXPECTED_CORE_SOURCE_SHA256" in source
