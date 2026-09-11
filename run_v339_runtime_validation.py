from pathlib import Path
import ast
import hashlib

ROOT = Path(__file__).resolve().parent
source = (ROOT / "main.py").read_text(encoding="utf-8")
core = (ROOT / "use_core.py").read_bytes()

for marker in (
    'APP_VERSION = "v339"',
    'DEPLOYMENT_FINGERPRINT = "USE-v339-canonical-recommendation-doorway"',
    'CANONICAL_BUILD_ID = "USE-BUILD-v339-canonical-recommendation-doorway"',
    'CANONICAL_BUILD_PAYLOAD_SHA256 = "AUDIT_REQUIRED_RUNTIME_SOURCE_SHA256"',
    'EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"',
    'app = use_core.app',
):
    assert marker in source, marker

module = ast.parse(source)
fn_names = {node.name for node in module.body if isinstance(node, ast.FunctionDef)}
assert "_v339_canonical_recommendation_doorway" in fn_names
assert "_v336_construct_visitor_answer" in fn_names
assert "_git_blob_sha256" in fn_names

fn = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == "_v339_canonical_recommendation_doorway")
fn_text = ast.get_source_segment(source, fn)
assert 'canonical_link = f"[{title}]({url})"' in fn_text
assert "return f\"{prefix}{canonical_link}." in fn_text

ctor = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == "_v336_construct_visitor_answer")
ctor_text = ast.get_source_segment(source, ctor)
assert ctor_text.count("_v339_canonical_recommendation_doorway(") == 1
assert ctor_text.find("normalize_link_presentation") < ctor_text.find("_v339_canonical_recommendation_doorway")

expected = "fb3208a8d287f16562ffd640d89f65d5e8d18607"
actual = hashlib.sha1(f"blob {len(core)}\0".encode("utf-8") + core).hexdigest()
assert actual == expected, (expected, actual)

print("USE v339 runtime doorway validation: PASS")
print(f"protected_core_git_blob_sha={actual}")
