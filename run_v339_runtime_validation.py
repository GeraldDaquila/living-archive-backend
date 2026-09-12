from pathlib import Path
import ast
import hashlib

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "main.py"
CORE = ROOT / "use_core.py"
source = MAIN.read_text(encoding="utf-8")
core = CORE.read_bytes()

EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"
EXPECTED_CORE_RAW_SHA256 = "7576b432174633f7182c934891b388a36e9c0b743d0adee41f19e11917d91e81"
EXPECTED_CORE_INTERNAL_SHA256 = "ecbd5181958f95baedf397f715fa30ae0192005b9a39f005fe3c0ad8a8fb7ef2"

for marker in (
    'APP_VERSION = "v339"',
    'DEPLOYMENT_FINGERPRINT = "USE-v339-canonical-recommendation-doorway"',
    'CANONICAL_BUILD_ID = "USE-BUILD-v339-canonical-recommendation-doorway"',
    'CANONICAL_BUILD_PAYLOAD_SHA256 = "AUDIT_REQUIRED_RUNTIME_SOURCE_SHA256"',
    'EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"',
    'app = use_core.app',
    'use_core.generate_llm_response = _v339_finalize_generation_response',
):
    assert marker in source, marker

module = ast.parse(source)
fn_names = {node.name for node in module.body if isinstance(node, ast.FunctionDef)}
assert "_v339_canonical_recommendation_doorway" in fn_names
assert "_v336_construct_visitor_answer" in fn_names
assert "_v339_finalize_generation_response" in fn_names
assert "_v338_final_answer_boundary" in fn_names
assert "_v339_build_compassionate_recommendation_answer" in fn_names

fn = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == "_v339_canonical_recommendation_doorway")
fn_text = ast.get_source_segment(source, fn)
assert 'canonical_link = f"[{title}]({url})"' in fn_text
assert "return f\"{prefix}{canonical_link}." in fn_text

boundary = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == "_v338_final_answer_boundary")
boundary_text = ast.get_source_segment(source, boundary)
assert 'if use_core._is_recommendation_question(user_query):' in boundary_text
assert 'A useful place to begin is' in boundary_text
assert '_v339_build_compassionate_recommendation_answer' in boundary_text
assert 'without forcing certainty' in source
assert 'rather than asking grief to become something you simply resolve' in source

finalizer = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == "_v339_finalize_generation_response")
finalizer_text = ast.get_source_segment(source, finalizer)
assert '_context_blocks_from_kwargs(args, kwargs)' in finalizer_text
assert 'deterministic compassionate answer used; provider generation skipped' in finalizer_text

ctor = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == "_v336_construct_visitor_answer")
ctor_text = ast.get_source_segment(source, ctor)
assert ctor_text.count("_v339_canonical_recommendation_doorway(") == 1
assert "if use_core._is_recommendation_question(user_query):" in ctor_text

actual_raw = hashlib.sha256(core).hexdigest()
actual_blob = hashlib.sha1(f"blob {len(core)}\0".encode("utf-8") + core).hexdigest()
assert actual_raw == EXPECTED_CORE_RAW_SHA256, (EXPECTED_CORE_RAW_SHA256, actual_raw)
assert actual_blob == EXPECTED_CORE_BLOB_SHA, (EXPECTED_CORE_BLOB_SHA, actual_blob)
assert EXPECTED_CORE_INTERNAL_SHA256 in core.decode("utf-8"), EXPECTED_CORE_INTERNAL_SHA256

print("USE v339 runtime doorway validation: PASS")
print(f"protected_core_raw_sha256={actual_raw}")
print(f"protected_core_git_blob_sha={actual_blob}")
