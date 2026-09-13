from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parent
main_source = (ROOT / "main.py").read_text(encoding="utf-8")
core_source = (ROOT / "use_core.py").read_text(encoding="utf-8")

tree = ast.parse(main_source)
names = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
for name in (
    "_query_profile",
    "_is_acute_risk_resource",
    "_select_secondary_pathways",
    "_archive_bridge",
    "_guide_answer_architecture",
    "_build_sensitive_recommendation_answer",
    "_transition_profile",
    "_transition_retrieval_strategy",
    "_direct_open_transition_response",
    "_v387_finalize",
):
    assert name in names, name

assert 'APP_VERSION = "v387"' in main_source
assert 'DEPLOYMENT_FINGERPRINT = "USE-v387-secondary-pathway-relevance"' in main_source
assert 'CANONICAL_BUILD_ID = "USE-BUILD-v387-secondary-pathway-relevance"' in main_source
assert "_BENCHMARK_PRIMARY_TITLE" not in main_source
assert "_BENCHMARK_PRIMARY_URL" not in main_source
assert "app=use_core.app" in main_source or "app = use_core.app" in main_source

core_tree = ast.parse(core_source)
core_funcs = {n.name: n for n in core_tree.body if isinstance(n, ast.FunctionDef)}
assert "_run_generation_attempt" in core_funcs
attempt_source = ast.get_source_segment(core_source, core_funcs["_run_generation_attempt"])
assert "_enforce_recommendation_output_authority" in attempt_source
assert "_enforce_recommendation_resource_identity" in attempt_source

compile(tree, "main.py", "exec")
compile(core_tree, "use_core.py", "exec")
print("USE v387 current validation: PASS")
