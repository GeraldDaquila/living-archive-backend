"""Focused regression tests for the default, relevance-gated doorway contract."""
import ast
import re
import unittest
from pathlib import Path

SOURCE = Path(__file__).with_name("main.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)


def _node(name, kind):
    for item in TREE.body:
        if isinstance(item, kind) and getattr(item, "name", None) == name:
            return item
    raise AssertionError(f"missing {name}")


def _load_policy(registry):
    family_fn = _node("_select_verified_doorway_conceptual_family", ast.FunctionDef)
    fallback_fn = _node("_select_guide_node_fallback_doorway", ast.FunctionDef)
    mapping = next(
        item for item in TREE.body
        if isinstance(item, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "_VERIFIED_CONCEPTUAL_FAMILY_DOORWAYS"
                for target in item.targets)
    )
    module = ast.Module(body=[mapping, family_fn, fallback_fn], type_ignores=[])
    namespace = {
        "re": re,
        "_guide_node_registry_snapshot": lambda: registry,
    }
    exec(compile(ast.fix_missing_locations(module), "<doorway-policy>", "exec"), namespace)
    return namespace


class DefaultGroundedDoorwayContractTests(unittest.TestCase):
    def test_consequential_uncertainty_question_has_verified_compass_doorway(self):
        policy = _load_policy([])
        query = "How should people act when the future is uncertain but consequential?"
        family = policy["_select_verified_doorway_conceptual_family"](query)
        self.assertEqual(family, "consequential_action_under_uncertainty")
        doorway = policy["_VERIFIED_CONCEPTUAL_FAMILY_DOORWAYS"][family]
        self.assertEqual(doorway["title"], "The Sovereign Sensemaking Compass")
        self.assertEqual(doorway["url"], "https://geralddaquila.com/the-sovereign-sensemaking-compass")

    def test_uncertainty_alone_does_not_force_an_unrelated_doorway(self):
        policy = _load_policy([])
        self.assertIsNone(
            policy["_select_verified_doorway_conceptual_family"](
                "Why does uncertainty exist?"
            )
        )

    def test_registry_fallback_requires_multiple_grounded_terms(self):
        registry = [
            {
                "title": "Decision-Making Under Uncertainty",
                "url": "https://geralddaquila.com/decision-making-under-uncertainty",
                "purpose": "Practical orientation for consequential decisions under uncertainty",
                "semantic_hints": ["decision", "uncertainty", "consequences", "evidence"],
            }
        ]
        policy = _load_policy(registry)
        selected = policy["_select_guide_node_fallback_doorway"](
            "How should people make decisions under uncertainty?"
        )
        self.assertEqual(selected["title"], "Decision-Making Under Uncertainty")
        self.assertIsNone(
            policy["_select_guide_node_fallback_doorway"]("What is this?")
        )

    def test_last_mile_fallback_is_default_but_explicit_no_doorway_is_preserved(self):
        self.assertIn(
            "if (\n        not authoritative_doorway\n        and not _is_practical_stewardship_question(query)\n        and not (",
            SOURCE,
        )
        self.assertIn(
            'bool(_final_gold_standard.get("forbids_doorway"))',
            SOURCE,
        )


if __name__ == "__main__":
    unittest.main()
