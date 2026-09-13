from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parent
main_source = (ROOT / "main.py").read_text(encoding="utf-8")
core_source = (ROOT / "use_core.py").read_text(encoding="utf-8")

for name in (
    "_v387_finalize",
    "_build_sensitive_recommendation_answer",
    "_select_secondary_pathways",
    "_is_acute_risk_resource",
):
    assert any(isinstance(node, ast.FunctionDef) and node.name == name for node in ast.parse(main_source).body), name

finalize = next(node for node in ast.parse(main_source).body if isinstance(node, ast.FunctionDef) and node.name == "_v387_finalize")
finalize_source = ast.get_source_segment(main_source, finalize)
assert "_original_generate_llm_response" in finalize_source
assert "_adjudicate_recommendation_resource" in finalize_source
assert "_build_sensitive_recommendation_answer" in finalize_source
assert "_transition_profile" in main_source
assert "_transition_retrieval_strategy" in main_source
assert "_direct_open_transition_response" in main_source
assert "_BENCHMARK_PRIMARY_TITLE" not in main_source
assert "_BENCHMARK_PRIMARY_URL" not in main_source
assert 'APP_VERSION = "v387"' in main_source
assert 'DEPLOYMENT_FINGERPRINT = "USE-v387-secondary-pathway-relevance"' in main_source
assert 'CANONICAL_BUILD_ID = "USE-BUILD-v387-secondary-pathway-relevance"' in main_source

attempt = next(node for node in ast.parse(core_source).body if isinstance(node, ast.FunctionDef) and node.name == "_run_generation_attempt")
attempt_source = ast.get_source_segment(core_source, attempt)
assert "_enforce_recommendation_output_authority" in attempt_source
assert "_enforce_recommendation_resource_identity" in attempt_source

compile(ast.parse(main_source), filename="main.py", mode="exec")
compile(ast.parse(core_source), filename="use_core.py", mode="exec")
print("USE v387 authority validation: PASS")
