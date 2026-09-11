import ast
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "main.py"
CORE = ROOT / "use_core.py"


def _extract_function(source, name):
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return ast.get_source_segment(source, node)
    raise AssertionError(f"function not found: {name}")


def _extract_assignment(source, name):
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return ast.get_source_segment(source, node)
    raise AssertionError(f"assignment not found: {name}")


def _load_contract_builder():
    source = MAIN.read_text(encoding="utf-8")
    fn = _extract_function(source, "_v335_compact_response_contract")
    ns = {
        "re": re,
        "use_core": type(
            "StubCore",
            (),
            {
                "_build_response_task_contract": staticmethod(
                    lambda _q, intent: {
                        "mode": "recommendation" if intent == "RECOMMENDATION" else "standard"
                    }
                ),
                "_response_presentation_mode": staticmethod(lambda _q: "prose"),
                "_movement_question_requires_canonical_next": staticmethod(
                    lambda q: bool(re.search(r"\bnext\b", q, flags=re.I))
                ),
                "recognize_question_structure": staticmethod(lambda _q: {"structure": ""}),
                "_question_is_underdetermined": staticmethod(lambda _q: False),
            },
        )(),
    }
    exec(compile(fn, "<v335_contract>", "exec"), ns)
    return ns["_v335_compact_response_contract"]


def main():
    main_source = MAIN.read_text(encoding="utf-8")
    core_source = CORE.read_text(encoding="utf-8")

    assert "_LEAN_PROVIDER_SYSTEM_PROMPT" not in main_source
    assert "COMPACT_GENERATION_SYSTEM_PROMPT" in main_source
    assert "_build_response_task_contract(user_query, intent)" in main_source
    assert "fetch_canonical_context" not in main_source
    assert "select_canonical_doorways" not in main_source
    assert "sanitize_canonical_links" not in main_source
    assert "normalize_link_presentation" not in main_source

    compact_assignment = _extract_assignment(core_source, "COMPACT_GENERATION_SYSTEM_PROMPT")
    compact_prompt = ast.literal_eval(compact_assignment.split("=", 1)[1].strip())

    build_contract = _load_contract_builder()
    cases = [
        (
            "What advise or essay from the Living Archive that you can recommend for someone who is grieving from the death of a loved one?",
            "RECOMMENDATION",
        ),
        (
            "What does the Archive say about grief and meaning after loss?",
            "TOPICAL_INQUIRY",
        ),
        (
            "Where can I go next from this pathway?",
            "MOVEMENT",
        ),
    ]

    contracts = []
    for query, intent in cases:
        contract = build_contract(query, intent)
        contracts.append(contract)
        assert contract.startswith("[VISITOR RESPONSE CONTRACT")
        assert f"intent={intent};" in contract
        assert len(contract) <= 1100, len(contract)

    fixed_estimate = max(len(compact_prompt) + len(c) for c in contracts)
    assert len(compact_prompt) < 2600, len(compact_prompt)
    assert fixed_estimate < 3600, fixed_estimate

    print(f"compact_prompt_chars={len(compact_prompt)}")
    print(f"max_contract_chars={max(map(len, contracts))}")
    print(f"estimated_max_system_chars={fixed_estimate}")
    print("V335 STATIC CONTRACT VALIDATION: PASS")


if __name__ == "__main__":
    main()
