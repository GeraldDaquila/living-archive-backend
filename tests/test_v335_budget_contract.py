import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path):
    return path.read_text(encoding="utf-8")


def _extract_string_assignment(source, name):
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    value = ast.literal_eval(node.value)
                    assert isinstance(value, str)
                    return value
    raise AssertionError(f"missing string assignment: {name}")


def _extract_function(source, name):
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"missing function: {name}")


def _contract_function():
    source = _read(ROOT / "main.py")
    node = _extract_function(source, "_v335_compact_response_contract")
    module = ast.Module(body=[node], type_ignores=[])
    namespace = {
        "re": re,
        "use_core": _CoreStub(),
    }
    exec(compile(module, "<v335-contract>", "exec"), namespace)
    return namespace["_v335_compact_response_contract"]


class _CoreStub:
    def _build_response_task_contract(self, query, intent):
        return {"mode": "recommendation" if "recommend" in query.lower() else "standard"}

    def _response_presentation_mode(self, query):
        return "prose"

    def _movement_question_requires_canonical_next(self, query):
        return "next" in query.lower() or "where" in query.lower() and "find" in query.lower()

    def recognize_question_structure(self, query):
        return {"structure": "explicit_contrast" if " versus " in query.lower() else ""}

    def _question_is_underdetermined(self, query):
        return False


def test_compact_generation_system_prompt_has_real_budget_margin():
    source = _read(ROOT / "use_core.py")
    prompt = _extract_string_assignment(source, "COMPACT_GENERATION_SYSTEM_PROMPT")
    assert 0 < len(prompt) < 2600


def test_representative_v335_contracts_are_bounded():
    build = _contract_function()
    queries = [
        "What advise or essay from the Living Archive can you recommend for someone who is grieving from the death of a loved one?",
        "What should I read next about meaning and grief?",
        "What is the difference between these two approaches versus one another?",
        "Where can I find the collection?",
    ]
    sizes = [len(build(query, "TOPICAL_INQUIRY")) for query in queries]
    assert max(sizes) < 1100


def test_v335_total_static_prompt_envelope_is_bounded():
    core_source = _read(ROOT / "use_core.py")
    main_source = _read(ROOT / "main.py")
    prompt = _extract_string_assignment(core_source, "COMPACT_GENERATION_SYSTEM_PROMPT")
    contract = _contract_function()
    representative = contract(
        "What advise or essay from the Living Archive can you recommend for someone who is grieving from the death of a loved one?",
        "TOPICAL_INQUIRY",
    )
    # Leave explicit headroom below the 3800-character provider-input cap.
    # This is a static guard only; actual assembled-message measurement remains
    # a runtime deployment gate.
    assert len(prompt) + len(representative) < 3300
    assert "MAX_PROVIDER_INPUT_CHARS = 3800" in core_source
    assert "COMPACT_GENERATION_SYSTEM_PROMPT" in main_source
