"""Regression tests for preserving real provider provenance through final assembly."""
import ast
from pathlib import Path


def _basic_inquiry_ast():
    source = (Path(__file__).resolve().parents[1] / "main.py").read_text(encoding="utf-8")
    module = ast.parse(source)
    function = next(
        node for node in module.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "_basic_inquiry_response"
    )
    return source, function


def test_basic_inquiry_preserves_composition_until_an_explicit_deterministic_override():
    source, function = _basic_inquiry_ast()
    assignments = {"composition_result": [], "deterministic_result": []}
    for node in ast.walk(function):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        for target in targets:
            if isinstance(target, ast.Name) and target.id in assignments:
                if isinstance(node.value, ast.Constant) and node.value.value is None:
                    assignments[target.id].append(node.lineno)

    composition_initializers = assignments["composition_result"]
    deterministic_initializers = assignments["deterministic_result"]
    assert len(composition_initializers) == 2, (
        "Composition may be initialized once and cleared only at the explicit "
        "trust/community deterministic override."
    )
    assert len(deterministic_initializers) == 1, (
        "The deterministic result must be initialized once before routing."
    )

    first_compose = min(
        node.lineno for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "compose"
    )
    metric_line = next(
        node.lineno for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "print"
        and bool(node.args)
        and "USE RESPONSE METRIC:" in (ast.get_source_segment(source, node.args[0]) or "")
    )
    first_init, explicit_override_clear = sorted(composition_initializers)
    assert first_init < first_compose < explicit_override_clear < metric_line
    assert deterministic_initializers[0] < first_compose

    source, _ = _basic_inquiry_ast()
    source_lines = source.splitlines()
    assert any(
        "deterministic_result = {" in line
        for line in source_lines[max(0, explicit_override_clear - 16):explicit_override_clear - 1]
    ), "The only late composition reset must follow an explicit deterministic result assignment."


def test_llm_attribution_requires_the_final_answer_to_match_the_provider_candidate():
    source, _ = _basic_inquiry_ast()
    assert "_llm_candidate_text = _sanitize_basic_inquiry_response(" in source
    assert "_final_response_text = _sanitize_basic_inquiry_response(str(response or \"\")" in source
    assert "_final_response_text == _llm_candidate_text" in source
    assert '_provider_name = "deterministic_final_boundary"' in source
    assert 'and not _llm_invoked' in source
    assert 'and not _registered_gold_standard_composition' in source
    assert '_provider_name = str(deterministic_result.get("provider") or "deterministic_recovery").strip()' in source

def test_registered_gold_standard_reference_is_deterministic_not_an_llm():
    source, function = _basic_inquiry_ast()
    module = ast.parse(source)
    helper = next(
        node for node in module.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "_is_registered_gold_standard_composition_result"
    )
    namespace = {}
    isolated = ast.Module(body=[helper], type_ignores=[])
    exec(compile(isolated, "<isolated-provenance-helper>", "exec"), namespace)
    classify = namespace["_is_registered_gold_standard_composition_result"]

    assert classify({
        "provider": "gold_standard_registry",
        "model": "approved-reference",
        "response": "The registered exact answer.",
    })
    assert not classify({"provider": "groq", "model": "llama-3"})
    assert not classify({"provider": "gold_standard_registry", "model": "live-model"})
    assert not classify(None)

    function_source = ast.get_source_segment(source, function)
    assert "_registered_gold_standard_composition = (" in function_source
    assert "and not _registered_gold_standard_composition" in function_source
    assert "if (\n        composition_result\n        and not _llm_invoked\n        and not _registered_gold_standard_composition" in function_source
    assert "_registered_gold_standard_composition\n        or (" in function_source

def test_response_metric_carries_opaque_request_ledger_correlation_without_replacing_legacy_id():
    source, function = _basic_inquiry_ast()
    function_source = ast.get_source_segment(source, function)
    assert "_gold_star_ledger.current_request_context()" in function_source
    assert "_gold_star_request_context.get(\"request_id\")" in function_source
    assert 'request_id={request_id}' in function_source
    assert "request_correlation_id={_gold_star_request_correlation_id or 'unavailable'}" in function_source



def test_llm_attribution_requires_a_registered_provider_model_pair():
    import main

    assert main._is_attributable_provider_model("groq", "openai/gpt-oss-120b")
    assert main._is_attributable_provider_model("nvidia", "nvidia/nemotron-3.5-super-vl-120b-a12b")
    assert not main._is_attributable_provider_model(
        "gold_standard_evidence_recovery", "extractive-deterministic"
    )
    assert not main._is_attributable_provider_model(
        "bounded_provider_exhaustion_recovery", "deterministic-contract-recovery"
    )
    assert not main._is_attributable_provider_model("gold_standard_registry", "approved-reference")
    assert not main._is_attributable_provider_model("groq", "unregistered-model")


def test_non_provider_composition_recovery_keeps_its_identity_without_claiming_llm():
    source, function = _basic_inquiry_ast()
    function_source = ast.get_source_segment(source, function)
    assert "_deterministic_composition_recovery = bool(" in function_source
    assert "elif not _deterministic_composition_recovery:" in function_source
    assert 'elif deterministic_result or _deterministic_composition_recovery:' in function_source
    assert '_response_provenance = "deterministic_recovery"' in function_source


def test_llm_attribution_requires_verified_provider_execution_not_only_registered_labels():
    source, function = _basic_inquiry_ast()
    function_source = ast.get_source_segment(source, function)
    assert 'composition_result.get("_provider_execution_verified") is True' in function_source
    assert "_is_attributable_provider_model(_provider_name, _model_name)" in function_source

    provider_bank = (Path(__file__).resolve().parents[1] / "provider_bank.py").read_text(encoding="utf-8")
    assert '"_provider_execution_verified": True' in provider_bank
    composition = (Path(__file__).resolve().parents[1] / "general_guide_composition.py").read_text(encoding="utf-8")
    assert '"_provider_execution_verified": result.get("_provider_execution_verified") is True' in composition

    # A registered provider/model pair without the execution marker is not
    # sufficient evidence that an external model actually ran.
    assert 'and composition_result.get("_provider_execution_verified") is True' in function_source
    assert 'and composition_result.get("_provider_execution_verified") is not True' in function_source
