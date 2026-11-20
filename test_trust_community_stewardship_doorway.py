"""Regression tests for the Trust-in-community-stewardship answer and doorway contract.

These tests extract only the small, deterministic contract functions from main.py.
They deliberately avoid importing the production ASGI graph and its external services.
"""
import ast
import html
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = (ROOT / "main.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


def load_contract_functions():
    wanted = {
        "_is_trust_community_stewardship_question",
        "_trust_community_stewardship_recovery",
        "_trust_community_stewardship_canonical_recommendation",
        "_trust_community_stewardship_final_contract",
    }
    nodes = [
        node for node in TREE.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name in wanted
    ]
    found = {node.name for node in nodes}
    if found != wanted:
        raise AssertionError(f"Missing contract functions: {sorted(wanted - found)}")
    namespace = {"re": re}
    module = ast.Module(body=nodes, type_ignores=[])
    exec(compile(module, str(ROOT / "main.py"), "exec"), namespace)
    return namespace


CONTRACT = load_contract_functions()


class TrustCommunityStewardshipDoorwayTests(unittest.TestCase):
    QUERY = "What is the role of trust in community stewardship?"
    EXPECTED_URL = "https://geralddaquila.com/trust-architecture/"

    def test_exact_question_is_recognized(self):
        self.assertTrue(CONTRACT["_is_trust_community_stewardship_question"](self.QUERY))

    def test_unrelated_question_is_not_captured(self):
        self.assertFalse(
            CONTRACT["_is_trust_community_stewardship_question"](
                "What is the role of reciprocity in a community?"
            )
        )

    def test_final_contract_keeps_answer_and_doorway_separate(self):
        result = CONTRACT["_trust_community_stewardship_final_contract"](self.QUERY)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["answer_basis"]["kind"], "general_knowledge")
        self.assertEqual(result["recommendation"]["url"], self.EXPECTED_URL)
        self.assertTrue(result["recommendation"]["rationale"])
        self.assertIn("accountability makes trust dependable", result["response"])

    def test_answer_contains_a_real_markdown_doorway(self):
        response = CONTRACT["_trust_community_stewardship_recovery"]()
        self.assertIn(
            f"[Trust Architecture cornerstone]({self.EXPECTED_URL})",
            response,
        )

    def test_final_payload_exports_nested_and_flat_doorway_contract(self):
        payload_node = next(
            node for node in ast.walk(TREE)
            if isinstance(node, ast.Dict)
            and any(
                isinstance(key, ast.Constant)
                and key.value == "canonical_doorway"
                for key in node.keys
            )
            and any(
                isinstance(key, ast.Constant)
                and key.value == "response"
                for key in node.keys
            )
        )
        keys = {
            key.value for key in payload_node.keys
            if isinstance(key, ast.Constant) and isinstance(key.value, str)
        }
        self.assertTrue({
            "recommendation", "canonical_doorway", "doorway_title",
            "doorway_url", "doorway_rationale", "doorway_decision",
            "doorway_selection_status", "doorway_selection_evaluated",
            "doorway_selection_source",
        }.issubset(keys))


if __name__ == "__main__":
    unittest.main()
