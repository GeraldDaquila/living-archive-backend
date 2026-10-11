"""Regression tests for existential/lived-experience routing versus Glossary lookup."""

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "main.py"
tree = ast.parse(SOURCE.read_text(encoding="utf-8"))

required = {
    "_is_lived_experience_explanatory_request",
    "_is_comparative_explanatory_request",
    "_normalize_glossary_term",
    "_is_bounded_glossary_request",
}
nodes = [
    node for node in tree.body
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    and node.name in required
]
found = {node.name for node in nodes}
missing = required - found
if missing:
    raise AssertionError(f"Missing routing contract functions: {sorted(missing)}")

namespace = {
    "re": re,
    "_extract_embedded_glossary_term": lambda _query: "",
}
exec(compile(ast.Module(body=nodes, type_ignores=[]), str(SOURCE), "exec"), namespace)

lived = namespace["_is_lived_experience_explanatory_request"]
normalize = namespace["_normalize_glossary_term"]
bounded = namespace["_is_bounded_glossary_request"]

# This exact production regression must not be treated as a dictionary lookup.
query = "What does it mean to live with uncertainty?"
assert lived(query) is True
assert bounded(query, glossary_term=normalize(query)) is False

# Neighboring existential/lived-experience phrasings also remain in Guide.
for query in (
    "What does it mean to live through grief?",
    "What is it like to live with uncertainty?",
    "How can I live with not knowing what comes next?",
    "What does it mean to face loss?",
):
    assert lived(query) is True, query
    assert bounded(query, glossary_term=normalize(query)) is False, query

# Genuine bounded definitions must remain eligible for native Glossary lookup.
for query in (
    "What does uncertainty mean?",
    "What is stewardship?",
    "What does stewardship mean here?",
):
    assert lived(query) is False, query
    assert bounded(query, glossary_term=normalize(query)) is True, query

print("PASS: lived-experience questions stay in Guide; bounded definitions stay in Glossary.")
