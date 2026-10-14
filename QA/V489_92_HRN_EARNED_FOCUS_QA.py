"""Behavioral probes for HRN earned-perspective canonical selection."""
import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "main.py"
tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
required = {"_normalize_query", "_relational_communication_focus", "_relational_discernment_focus", "_relational_return_topic_anchor", "_relational_return_conflict_topic_fit", "_relational_return_is_generic_doorway", "_relational_return_workplace_change_focus", "_relational_return_workplace_change_fit", "_relational_return_earned_focus_fit"}
nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in required]
found = {node.name for node in nodes}
if found != required:
    raise AssertionError(f"Missing earned-focus contract functions: {sorted(required - found)}")

def normalize_query(value):
    return re.sub(r"\s+", " ", str(value or "").strip().casefold())

namespace = {"re": re, "_normalize_query": normalize_query}
exec(compile(ast.Module(body=[node for node in nodes if node.name != "_normalize_query"], type_ignores=[]), str(SOURCE), "exec"), namespace)
anchor = namespace["_relational_return_topic_anchor"]
fit = namespace["_relational_return_earned_focus_fit"]

opening = "I care about a friend, but lately I feel I'm always the one making an effort. I don't want to judge them unfairly, but I also don't want to keep ignoring how I feel."
need = "To feel valued and understand the relationship without unfairly judging the friend or silencing my own feelings."
delta = "The visitor now sees the ambiguity as lying in interpretation rather than in the friend's behavior alone, opening space to examine what can actually be observed."
focus = " ".join((opening, need, delta, anchor(opening, need, delta)))

direct_resource = {
    "title": "Learning to Love Without Losing Yourself",
    "url": "https://geralddaquila.com/2026/01/27/learning-to-love-without-losing-yourself/",
    "text": "This piece explores relationships, overgiving, self-sacrifice, enduring imbalance, and giving as proof of worth. Where someone giving more and someone receiving more was normalized, being needed felt like being valued. Healthy love can support mutual respect and mutual support.",
}
discernment_resource = {
    "title": "The Heart of Connection: Why Relationships Work—and Why They Break",
    "url": "https://geralddaquila.com/2025/05/19/the-heart-of-connection-understanding-and-sustaining-relationships-across-all-walks-of-life/",
    "text": "Relationships are shaped by perception, how behavior is interpreted, communication, boundaries, and the assumptions people make about one another.",
}
institutional_decoy = {
    "title": "A Simple Story About Separation, Sharing, and the Way We Built the World",
    "url": "https://geralddaquila.com/example-separation-sharing/",
    "text": "This essay discusses separation, sharing, civilization, and how society was built.",
}
assert "Relational effort imbalance" in focus
assert "Relational discernment" in focus
assert fit(focus, direct_resource), "A resource directly addressing overgiving and mutuality should pass."
assert fit(focus, discernment_resource), "A resource directly addressing interpretation of behavior should pass."
assert not fit(focus, institutional_decoy), "Broad conceptual overlap must not pass as a relational gift."

print("PASS: HRN earned focus supports relevant relational doorways and rejects unrelated conceptual material.")
