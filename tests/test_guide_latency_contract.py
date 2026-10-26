"""Regression tests for the Guide's single-pass Gold Standard latency contract.

These source-level tests deliberately avoid importing the production app (which
initializes external integrations at import time). They protect the orchestration
invariants that prevent a late formatting failure from triggering another LLM turn.
"""
import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN_SOURCE = (ROOT / "main.py").read_text(encoding="utf-8")
MAIN_TREE = ast.parse(MAIN_SOURCE)


def _function(name):
    return next(
        node for node in MAIN_TREE.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == name
    )


def _contains_composer_call(node):
    return any(
        isinstance(item, ast.Call)
        and isinstance(item.func, ast.Attribute)
        and item.func.attr == "compose"
        and isinstance(item.func.value, ast.Name)
        and item.func.value.id == "general_guide_composition"
        for item in ast.walk(node)
    )


class GuideLatencyContractTests(unittest.TestCase):
    def test_healthy_community_recovery_is_three_paragraphs(self):
        function = _function("_healthy_community_answer_recovery")
        returned = next(node for node in ast.walk(function) if isinstance(node, ast.Return))
        response = ast.literal_eval(returned.value)
        self.assertEqual(
            len([part for part in response.split("\n\n") if part.strip()]),
            3,
            "The governed newcomer recovery must satisfy the default three-paragraph contract.",
        )

    def test_healthy_community_path_short_circuits_provider_composition(self):
        function = _function("_basic_inquiry_response")
        branches = [
            node for node in ast.walk(function)
            if isinstance(node, ast.If)
            and isinstance(node.test, ast.Call)
            and isinstance(node.test.func, ast.Name)
            and node.test.func.id == "_is_healthy_community_orientation_question"
        ]
        self.assertEqual(len(branches), 1, "Expected one explicit governed newcomer branch.")
        self.assertFalse(
            _contains_composer_call(branches[0]),
            "The deterministic newcomer branch must not invoke the model composer.",
        )
        source_position = MAIN_SOURCE.index(
            "if _is_healthy_community_orientation_question(query):",
            MAIN_SOURCE.index("def _basic_inquiry_response("),
        )
        compose_position = MAIN_SOURCE.index(
            "composition_result = general_guide_composition.compose(",
            source_position,
        )
        self.assertLess(source_position, compose_position)

    def test_final_paragraph_guard_never_reenters_composer(self):
        start = MAIN_SOURCE.index(
            "# LAST-MILE GOLD STANDARD CONTRACT: enforce the presentation floor"
        )
        end = MAIN_SOURCE.index(
            "if general_guide_composition._requires_responsibility_boundary_answer(query)",
            start,
        )
        final_guard = ast.parse(MAIN_SOURCE[start:end])
        self.assertFalse(
            _contains_composer_call(final_guard),
            "A last-mile formatting failure must fail honestly, not start another LLM turn.",
        )
        self.assertIn("second_composition_attempt=false", MAIN_SOURCE[start:end])


if __name__ == "__main__":
    unittest.main()
