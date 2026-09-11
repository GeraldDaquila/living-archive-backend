import ast
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "main.py"
CORE = ROOT / "use_core.py"
BASE_COMMIT = "b663397c04d1506392a3d227a0dc291ce02f109f"
PREVIOUS_FIXED_INPUT_CHARS = 3756
PREVIOUS_ESTIMATED_OUTPUT_CHARS = 1280
MAX_PROVIDER_INPUT_CHARS = 3800
MAX_PROVIDER_TOTAL_CHARS = 4600


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


def _literal_assignment(source, name):
    assignment = _extract_assignment(source, name)
    return ast.literal_eval(assignment.split("=", 1)[1].strip())


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


def _load_provider_prompt():
    source = MAIN.read_text(encoding="utf-8")
    fn = _extract_function(source, "_v335_provider_system_prompt")
    ns = {"re": re, "use_core": type("StubCore", (), {})()}
    ns["use_core"].COMPACT_GENERATION_SYSTEM_PROMPT = _literal_assignment(
        CORE.read_text(encoding="utf-8"), "COMPACT_GENERATION_SYSTEM_PROMPT"
    )
    exec(compile(fn, "<v335_provider_prompt>", "exec"), ns)
    return ns["_v335_provider_system_prompt"]()


def _baseline_main_source():
    return subprocess.check_output(
        ["git", "show", f"{BASE_COMMIT}:main.py"],
        cwd=ROOT,
        text=True,
    )


def main():
    main_source = MAIN.read_text(encoding="utf-8")
    core_source = CORE.read_text(encoding="utf-8")

    assert "_LEAN_PROVIDER_SYSTEM_PROMPT" not in main_source
    assert "COMPACT_GENERATION_SYSTEM_PROMPT" in main_source
    assert "_build_response_task_contract(user_query, intent)" in main_source
    assert "fetch_canonical_context" not in main_source
    assert "select_canonical_doorways" not in main_source
    assert "sanitize_canonical_links" not in main_source
    # v336 deliberately invokes the protected canonical presentation boundary.
    assert "use_core.normalize_link_presentation" in main_source

    compact_prompt = _literal_assignment(core_source, "COMPACT_GENERATION_SYSTEM_PROMPT")
    provider_prompt = _load_provider_prompt()
    baseline_source = _baseline_main_source()
    lean_prompt = _literal_assignment(baseline_source, "_LEAN_PROVIDER_SYSTEM_PROMPT")

    assert "[RECOMMENDATION QUALITY]" in compact_prompt
    assert "[BREATHE BETWEEN IDEAS]" in compact_prompt
    assert "[PROVENANCE + SYNTHESIS]" in compact_prompt
    assert "[RECOMMENDATION QUALITY]" not in provider_prompt
    assert "[BREATHE BETWEEN IDEAS]" not in provider_prompt
    assert "[PROVENANCE + SYNTHESIS]" not in provider_prompt
    assert "[EVIDENCE]" in provider_prompt
    assert "[VISITOR VOICE]" in provider_prompt
    assert "[COMPASSIONATE CARE]" in provider_prompt

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

    contracts = [build_contract(query, intent) for query, intent in cases]
    for (query, intent), contract in zip(cases, contracts):
        assert contract.startswith("[VISITOR RESPONSE CONTRACT")
        assert f"intent={intent};" in contract
        assert len(contract) <= 600, len(contract)

    max_system_chars = max(len(provider_prompt) + len(c) for c in contracts)
    projected_fixed_input = PREVIOUS_FIXED_INPUT_CHARS - len(lean_prompt) + max_system_chars
    projected_total = projected_fixed_input + PREVIOUS_ESTIMATED_OUTPUT_CHARS

    print(f"baseline_lean_prompt_chars={len(lean_prompt)}")
    print(f"protected_compact_prompt_chars={len(compact_prompt)}")
    print(f"derived_provider_prompt_chars={len(provider_prompt)}")
    print(f"max_contract_chars={max(map(len, contracts))}")
    print(f"max_system_chars={max_system_chars}")
    print(f"v334_observed_fixed_input_chars={PREVIOUS_FIXED_INPUT_CHARS}")
    print(f"v335_projected_fixed_input_chars={projected_fixed_input}")
    print(f"v335_projected_total_chars={projected_total}")

    assert len(provider_prompt) < 1600, len(provider_prompt)
    assert projected_fixed_input < MAX_PROVIDER_INPUT_CHARS, projected_fixed_input
    assert projected_total < MAX_PROVIDER_TOTAL_CHARS, projected_total
    print("V335 PROVIDER ENVELOPE PROJECTION: PASS")


if __name__ == "__main__":
    main()
