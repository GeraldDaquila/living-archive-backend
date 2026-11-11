"""Regression contract for the culture conceptual recovery doorway."""

import ast
import re
import unittest
from pathlib import Path

SOURCE = Path(__file__).with_name("main.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)
FUNCTION = next(
    node for node in TREE.body
    if isinstance(node, ast.FunctionDef)
    and node.name == "_established_general_knowledge_recovery"
)
COMPILED = compile(ast.Module(body=[FUNCTION], type_ignores=[]), "main.py", "exec")


class CultureDoorwayContractTests(unittest.TestCase):
    def setUp(self):
        namespace = {"re": re}
        exec(COMPILED, namespace)
        self.recover = namespace["_established_general_knowledge_recovery"]

    def test_culture_concept_preserves_reviewed_archive_doorway(self):
        result = self.recover(
            "How does culture shape what people can notice, value, and imagine?"
        )
        self.assertIsNotNone(result)
        self.assertEqual(
            result["fact_id"],
            "culture_shapes_attention_value_and_imagination",
        )
        doorway = result.get("doorway")
        self.assertIsInstance(doorway, dict)
        self.assertEqual(set(doorway), {"title", "url"})
        self.assertTrue(doorway["title"].strip())
        self.assertTrue(doorway["url"].startswith("https://geralddaquila.com/"))
        self.assertEqual(doorway["title"], "Rules of Reasoning")
        self.assertEqual(
            doorway["url"],
            "https://geralddaquila.com/rules-of-reasoning/",
        )


if __name__ == "__main__":
    unittest.main()
