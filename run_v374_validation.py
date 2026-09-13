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
    'APP_VERSION = "v374"',
    'DEPLOYMENT_FINGERPRINT = "USE-v374-visitor-experience-authority-calibration"',
    'CANONICAL_BUILD_ID = "USE-BUILD-v374-visitor-experience-authority-calibration"',
    'EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"',
    'def _visitor_experience_contract',
    'def _frame_neutral_generation_documents',
    'def _requested_frame_groups',
    'def _resource_frame_groups',
    'def _call_original_with_calibrated_context',
    'use_core.generate_llm_response = _v374_finalize',
):
    assert marker in source, marker

module = ast.parse(source)
fn_names = {node.name for node in module.body if isinstance(node, ast.FunctionDef)}
for required in (
    "_query_profile",
    "_resource_frame_groups",
    "_is_specialized_framework_resource",
    "_requested_frame_groups",
    "_frame_neutral_generation_documents",
    "_transition_retrieval_strategy",
    "_visitor_experience_contract",
    "_call_original_with_calibrated_context",
    "_v374_finalize",
):
    assert required in fn_names, required

finalize = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == "_v374_finalize")
finalize_text = ast.get_source_segment(source, finalize)
assert "_guide_answer(" not in finalize_text
assert "_call_original_with_calibrated_context" in finalize_text
assert "_transition_retrieval_strategy" in finalize_text
assert "_frame_neutral_generation_documents" in finalize_text

# The live transition doorway that exposed the architectural defect must be
# classified as a composite framework for an uncommitted visitor state.
ns = {}
exec(compile(ast.Module(body=[node for node in module.body if isinstance(node, ast.FunctionDef) or isinstance(node, ast.Assign)], type_ignores=[]), "main.py", "exec"), ns)
transition_doc = {
    "title": "Thriving in the Age of Flux: Harnessing AI, Indigenous Wisdom, and Spiritual Insight to Navigate Epochal Change",
    "url": "https://geralddaquila.com/2025/06/05/thriving-in-the-age-of-flux-harnessing-ai-indigenous-wisdom-and-spiritual-insight-to-navigate-epochal-change/",
    "text": "AI, Indigenous wisdom, spiritual insight, and epochal change.",
}
assert ns["_is_specialized_framework_resource"](transition_doc) is True
assert ns["_requested_frame_groups"]("I am not sure what I believe and want to explore what comes next") == set()

actual_raw = hashlib.sha256(core).hexdigest()
actual_blob = hashlib.sha1(f"blob {len(core)}\0".encode("utf-8") + core).hexdigest()
assert actual_raw == EXPECTED_CORE_RAW_SHA256, (EXPECTED_CORE_RAW_SHA256, actual_raw)
assert actual_blob == EXPECTED_CORE_BLOB_SHA, (EXPECTED_CORE_BLOB_SHA, actual_blob)
assert EXPECTED_CORE_INTERNAL_SHA256 in core.decode("utf-8"), EXPECTED_CORE_INTERNAL_SHA256

print("USE v374 visitor-experience structural validation: PASS")
print(f"protected_core_raw_sha256={actual_raw}")
print(f"protected_core_git_blob_sha={actual_blob}")
