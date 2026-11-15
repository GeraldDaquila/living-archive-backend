"""Regression contract for stewardship-centered technology doorways."""

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "general_guide_composition.py"
tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
target = next(
    node for node in tree.body
    if isinstance(node, ast.FunctionDef)
    and node.name == "_stewardship_technology_canonical_doorway"
)
namespace = {"re": re, "_normalize_space": lambda value: re.sub(r"\s+", " ", str(value or "")).strip()}
exec(compile(ast.Module(body=[target], type_ignores=[]), str(SOURCE), "exec"), namespace)
doorway = namespace["_stewardship_technology_canonical_doorway"]

question = "What role should technology play in a stewardship-centered society?"
result = doorway(question)
assert result == {
    "doorway_title": "Foundations of Stewardship Governance",
    "doorway_url": "https://geralddaquila.com/foundations-of-stewardship-governance",
}

assert doorway("What role should technology play in society?")["doorway_title"] == ""
assert doorway("How should stewardship shape technology?")["doorway_title"] == ""

print("STEWARDSHIP TECHNOLOGY DOORWAY QA: PASS")
