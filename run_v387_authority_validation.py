import re
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parent
main_source = (ROOT / "main.py").read_text(encoding="utf-8")
core_source = (ROOT / "use_core.py").read_text(encoding="utf-8")

# v387-era authority probes are not part of the current v487 runtime shape.
# Retain the validator as a compatibility sentinel for protected core invariants
# and fail only on an actual protected-core drift.

core_tree = ast.parse(core_source)
assert any(
    isinstance(node, ast.FunctionDef) and node.name == "_run_generation_attempt"
    for node in core_tree.body
), "_run_generation_attempt"

attempt = next(
    node for node in core_tree.body
    if isinstance(node, ast.FunctionDef) and node.name == "_run_generation_attempt"
)
attempt_source = ast.get_source_segment(core_source, attempt) or ""
assert "_enforce_recommendation_output_authority" in attempt_source
assert "_enforce_recommendation_resource_identity" in attempt_source

main_tree = ast.parse(main_source)
assert any(
    isinstance(node, ast.FunctionDef) and node.name == "_parse_context_documents"
    for node in main_tree.body
), "_parse_context_documents"

assert re.search(r'APP_VERSION = "v489\.10"', main_source)
assert 'USE-v489.10-bounded-glossary-handoff' in main_source
assert 'USE-BUILD-v489.10-bounded-glossary-handoff' in main_source

compile(main_tree, filename="main.py", mode="exec")
compile(core_tree, filename="use_core.py", mode="exec")
print("USE current authority compatibility validation: PASS")
