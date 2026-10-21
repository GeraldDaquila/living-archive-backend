"""Regression tests for the Guide's bounded relational-burden fallback.

The test extracts the production function from main.py and executes it with narrow
stubs so these tests exercise the real branch without importing the full service.
"""
import ast
import re
import unittest
from pathlib import Path
from types import SimpleNamespace


SOURCE = Path(__file__).with_name("main.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)
FUNCTION = next(
    node for node in TREE.body
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    and node.name == "_basic_inquiry_round1_deterministic_response"
)
COMPILED = compile(ast.Module(body=[FUNCTION], type_ignores=[]), "main.py", "exec")


class GuideRelationalQuestionRecoveryTests(unittest.TestCase):
    def setUp(self):
        namespace = {
            "re": re,
            "_normalize_query": lambda value: " ".join(str(value or "").split()),
            "compose_relational_fractal": lambda query: None,
            "_topic_anchor_groups": lambda query: [],
            "use_core": SimpleNamespace(
                context_blocks_to_documents=lambda value: [{"title": value, "content": ""}] if value else []
            ),
            "_is_practical_stewardship_question": lambda query: False,
        }
        exec(COMPILED, namespace)
        self.recover = namespace["_basic_inquiry_round1_deterministic_response"]

    def run_recovery(self, query, title="Human Flourishing"):
        return self.recover(
            query,
            {"underlying_question": "", "desired_movement": ""},
            {"context_blocks": title},
            recommendation_available=bool(title),
        )

    def test_family_responsibility_gets_relational_response_not_refusal(self):
        result = self.run_recovery(
            "I am always the responsible one in my family. Everyone depends on me, but nobody asks how I am."
        )
        self.assertEqual(result["provider"], "bounded_relational_burden_recovery")
        self.assertIn("people rely on you", result["response"])
        self.assertIn("what do you most wish someone in your family would notice", result["response"])
        self.assertNotIn("couldn't verify a reliable answer", result["response"])

    def test_broad_resource_is_not_presented_as_relevant(self):
        result = self.run_recovery(
            "I am always the responsible one in my family. Everyone depends on me, but nobody asks how I am.",
            title="Human Flourishing",
        )
        self.assertEqual(result["doorway_title"], "")

    def test_directly_relevant_resource_can_be_preserved(self):
        result = self.run_recovery(
            "I am always the responsible one in my family. Everyone depends on me, but nobody asks how I am.",
            title="Family Responsibility and Care",
        )
        self.assertEqual(result["doorway_title"], "Family Responsibility and Care")

    def test_national_systems_question_gets_structured_bounded_analysis(self):
        result = self.run_recovery(
            "What ails the Philippines, despite its rich natural resources, hard working and adaptable people, "
            "why is the country performing well below its potential? Lately, even Vietnam overtook it. "
            "What if any, would you recommend to fix the situation?",
            title="Filipino Identity and Culture",
        )
        self.assertEqual(result["provider"], "archive_grounded_national_systems_recovery")
        self.assertEqual(result["doorway_title"], "")
        response = result["response"].casefold()
        self.assertIn("complex-system problem", response)
        self.assertIn("feedback loop is infrastructure and state capacity", response)
        self.assertIn("philippines–vietnam comparison", response)
        self.assertIn("stewardship", response)
        self.assertIn("not be mistaken for an inherent defect in the filipino character", response)
        self.assertNotIn("couldn't verify a reliable answer", response)
        self.assertGreaterEqual(response.count(chr(10) + chr(10)), 3)

    def test_national_systems_recovery_does_not_capture_unrelated_questions(self):
        result = self.run_recovery(
            "What is the capital of Japan?",
            title="",
        )
        self.assertEqual(result["provider"], "deterministic_question_preserving_recovery")

    def test_unrelated_factual_question_does_not_enter_relational_route(self):
        result = self.run_recovery("What is the capital of Japan?", title="")
        self.assertEqual(result["provider"], "deterministic_question_preserving_recovery")
        self.assertNotIn("people rely on you", result["response"])


if __name__ == "__main__":
    unittest.main()
