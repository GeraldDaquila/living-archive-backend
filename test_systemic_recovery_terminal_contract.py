"""API-boundary regression for registered systemic mechanism recovery."""

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).parent
MAIN = (ROOT / "main.py").read_text(encoding="utf-8")
COMPOSITION = (ROOT / "general_guide_composition.py").read_text(encoding="utf-8")
QUESTION = "How can algorithmic systems scale existing biases or institutional failures?"


class SystemicRecoveryTerminalContractTests(unittest.TestCase):
    def test_shared_recovery_recognizes_exact_question(self):
        self.assertIn('r"\\bhow (?:can|do|does|might|could)', COMPOSITION)
        self.assertIn("Algorithmic systems can scale existing biases", COMPOSITION)

    def test_api_deterministic_recovery_accepts_bounded_mechanism_class(self):
        tree = ast.parse(MAIN)
        fn = next(
            node for node in tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "_basic_inquiry_round1_deterministic_response"
        )
        source = ast.get_source_segment(MAIN, fn)
        self.assertIn("_systemic_mechanism_recovery", source)
        self.assertIn("is_conceptual_relationship_question(query)", source)

    def test_final_boundary_uses_registered_recovery_before_terminal_error(self):
        tree = ast.parse(MAIN)
        source = MAIN
        self.assertIn("_deterministic_recovery = _basic_inquiry_round1_deterministic_response(", source)
        self.assertIn("elif _deterministic_valid:", source)
        self.assertIn("deterministic registered recovery PASS", source)
        self.assertLess(
            source.index("_deterministic_recovery = _basic_inquiry_round1_deterministic_response("),
            source.index("I couldn’t produce a reliable answer to that question just now."),
        )

    def test_registered_mechanism_recovery_has_shape_aware_quality_admission(self):
        source = MAIN
        self.assertIn("_deterministic_registered_mechanism", source)
        self.assertIn('== "bounded_conceptual_relationship_recovery"', source)
        self.assertIn("is_conceptual_relationship_question(query)", source)
        self.assertIn("is_meta_answer_failure(_deterministic_text)", source)

    def test_final_boundary_preserves_general_knowledge_basis_and_terminal_guard(self):
        source = MAIN
        self.assertIn('"kind": "general_knowledge"', source)
        self.assertIn("answer-only recovery unavailable; returned explicit non-answer error state", source)


if __name__ == "__main__":
    unittest.main()
