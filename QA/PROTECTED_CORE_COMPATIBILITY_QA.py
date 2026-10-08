"""Current protected-core compatibility gate.

This validator intentionally does not pin the mutable Guide runtime to a
historical v387/v488 version. It verifies the live main.py identity is
self-consistent and that the protected use_core invariants remain present.
"""

from pathlib import Path
import ast
import hashlib
import re

ROOT = Path(__file__).resolve().parents[1]
main_path = ROOT / "main.py"
core_path = ROOT / "use_core.py"
main_source = main_path.read_text(encoding="utf-8")
core_source = core_path.read_text(encoding="utf-8")

main_tree = ast.parse(main_source, filename="main.py")
core_tree = ast.parse(core_source, filename="use_core.py")

version_match = re.search(r'^APP_VERSION = "(v[0-9]+\.[0-9]+)"$', main_source, re.MULTILINE)
assert version_match, "Current APP_VERSION is missing or malformed."
version = version_match.group(1)

assert f'DEPLOYMENT_FINGERPRINT = "USE-{version}-' in main_source, "Deployment fingerprint does not match APP_VERSION."
assert f'CANONICAL_BUILD_ID = "USE-BUILD-{version}-' in main_source, "Canonical build ID does not match APP_VERSION."

expected_match = re.search(r'^EXPECTED_CORE_BLOB_SHA = "([0-9a-f]{40})"$', main_source, re.MULTILINE)
assert expected_match, "Expected protected-core blob SHA is missing."
core_bytes = core_path.read_bytes()
actual_core_sha = hashlib.sha1(f"blob {len(core_bytes)}\0".encode() + core_bytes).hexdigest()
assert actual_core_sha == expected_match.group(1), "Protected use_core.py blob identity changed."

functions = {
    node.name: node
    for node in core_tree.body
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
}
assert "_run_generation_attempt" in functions, "Protected generation attempt boundary is missing."
attempt_source = ast.get_source_segment(core_source, functions["_run_generation_attempt"]) or ""
assert "_enforce_recommendation_output_authority" in attempt_source, "Recommendation output authority boundary is missing."
assert "_enforce_recommendation_resource_identity" in attempt_source, "Recommendation resource identity boundary is missing."

assert 'use_core.APP_VERSION = APP_VERSION' in main_source, "Runtime version is not propagated to protected core."
assert 'use_core.EXPECTED_CORE_BLOB_SHA = EXPECTED_CORE_BLOB_SHA' in main_source, "Protected-core identity is not propagated."
assert "app = _base.app" in main_source, "FastAPI application ownership changed unexpectedly."

compile(main_tree, filename="main.py", mode="exec")
compile(core_tree, filename="use_core.py", mode="exec")
print(f"Protected core compatibility validation: PASS ({version})")
