"""Regression tests for contextual relevance of lived-uncertainty recommendations."""
import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "main.py"
tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
required = {"_normalize_query", "_is_lived_uncertainty_inquiry", "_uncertainty_resource_direct_fit"}
nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in required]
found = {node.name for node in nodes}
missing = required - found
if missing:
    raise AssertionError(f"Missing uncertainty relevance contract functions: {sorted(missing)}")

def normalize_query(value):
    return re.sub(r"\s+", " ", str(value or "").strip().casefold())

namespace = {"re": re, "_normalize_query": normalize_query}
exec(compile(ast.Module(body=[node for node in nodes if node.name != "_normalize_query"], type_ignores=[]), str(SOURCE), "exec"), namespace)
is_lived = namespace["_is_lived_uncertainty_inquiry"]
direct_fit = namespace["_uncertainty_resource_direct_fit"]

query = "What does it mean to live with uncertainty?"
assert is_lived(query)

institutional_decoy = {
    "title": "Why Trust Breaks Down in Philippine Systems: Institutions, Uncertainty, and Survival",
    "url": "https://geralddaquila.com/example-institutional-uncertainty/",
    "text": "Institutional trust, governance, and uncertainty shape public systems and survival.",
}
assert not direct_fit(query, institutional_decoy), "Institutional title overlap must not pass as lived-experience fit."

personal_resource = {
    "title": "Living with Uncertainty: Making Decisions Without All the Answers",
    "url": "https://geralddaquila.com/example-lived-uncertainty/",
    "text": "Living with uncertainty means making decisions without all the answers, learning to tolerate ambiguity, and adapting as everyday life changes.",
}
assert direct_fit(query, personal_resource), "A directly relevant lived-uncertainty resource should pass."

# A visitor asking about institutions should not be subject to the personal-experience exclusion.
institutional_query = "Why does uncertainty undermine trust in Philippine institutions?"
assert not is_lived(institutional_query)
assert direct_fit(institutional_query, institutional_decoy)

print("PASS: lived uncertainty requires lived-context evidence; institutional uncertainty remains available for institutional questions.")
