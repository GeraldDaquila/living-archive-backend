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
    'def _query_profile(user_query: str, docs: list) -> dict:',
    'def _guide_answer_architecture(user_query: str, primary: dict, docs: list) -> dict:',
    'def _select_secondary_pathways(docs: list, primary_title: str, profile: dict, limit: int = 2) -> list:',
):
    assert marker in source, marker

module = ast.parse(source)
fn_names = {node.name for node in module.body if isinstance(node, ast.FunctionDef)}
for required in (
    "_v339_canonical_recommendation_doorway",
    "_v336_construct_visitor_answer",
    "_v339_finalize_generation_response",
    "_v338_final_answer_boundary",
    "_v339_build_compassionate_recommendation_answer",
    "_query_profile",
    "_guide_answer_architecture",
    "_select_secondary_pathways",
):
    assert required in fn_names, required

builder = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == "_v339_build_compassionate_recommendation_answer")
builder_text = ast.get_source_segment(source, builder)
assert '"\\n\\n".join' in builder_text
assert "A gentle place to begin" in builder_text
assert "Take what feels useful" in builder_text
assert "_resource_link(doc)" in builder_text
assert "profile[\"risk\"]" in builder_text

actual_raw = hashlib.sha256(core).hexdigest()
actual_blob = hashlib.sha1(f"blob {len(core)}\0".encode("utf-8") + core).hexdigest()
assert actual_raw == EXPECTED_CORE_RAW_SHA256, (EXPECTED_CORE_RAW_SHA256, actual_raw)
assert actual_blob == EXPECTED_CORE_BLOB_SHA, (EXPECTED_CORE_BLOB_SHA, actual_blob)
assert EXPECTED_CORE_INTERNAL_SHA256 in core.decode("utf-8"), EXPECTED_CORE_INTERNAL_SHA256

print("USE v339 generalized Guide answer architecture validation: PASS")
print(f"protected_core_raw_sha256={actual_raw}")
print(f"protected_core_git_blob_sha={actual_blob}")
