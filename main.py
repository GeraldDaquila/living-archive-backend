from pathlib import Path
import ast
import hashlib
ROOT = Path(__file__).resolve().parent
main_path = ROOT / "main.py"
core_path = ROOT / "use_core.py"
main_source = main_path.read_text(encoding="utf-8")
core_source = core_path.read_text(encoding="utf-8")
tree = ast.parse(main_source)
core_tree = ast.parse(core_source)
names = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
for name in ("_query_profile","_is_acute_risk_resource","_grief_pathway_fit","_select_secondary_pathways","_archive_bridge","_guide_answer_architecture","_build_sensitive_recommendation_answer","_transition_profile","_transition_retrieval_strategy","_direct_open_transition_response","_v390_finalize"):
    assert name in names, name
assert 'APP_VERSION = "v390"' in main_source
assert 'DEPLOYMENT_FINGERPRINT = "USE-v390-grief-local-refinement"' in main_source
assert 'CANONICAL_BUILD_ID = "USE-BUILD-v390-grief-local-refinement"' in main_source
assert 'EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"' in main_source
assert "_BENCHMARK_PRIMARY_TITLE" not in main_source
assert "_BENCHMARK_PRIMARY_URL" not in main_source
assert "use_core.generate_llm_response = _v390_finalize" in main_source
for marker in ("def _transition_profile","def _transition_evidence_fit","def _is_query_aligned_transition_doorway","def _transition_doorway_score","def _transition_retrieval_strategy","def _direct_open_transition_response"):
    assert marker in main_source
core_funcs = {n.name: n for n in core_tree.body if isinstance(n, ast.FunctionDef)}
assert "_run_generation_attempt" in core_funcs
attempt_source = ast.get_source_segment(core_source, core_funcs["_run_generation_attempt"])
assert "_enforce_recommendation_output_authority" in attempt_source
assert "_enforce_recommendation_resource_identity" in attempt_source
compile(tree, "main.py", "exec")
compile(core_tree, "use_core.py", "exec")
core_bytes = core_path.read_bytes()
actual_core_blob_sha = hashlib.sha1(f"blob {len(core_bytes)}\0".encode() + core_bytes).hexdigest()
assert actual_core_blob_sha == "fb3208a8d287f16562ffd640d89f65d5e8d18607"
print("USE v390 current validation: PASS")