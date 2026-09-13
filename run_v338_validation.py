from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parent
main_source = (ROOT / "main.py").read_text(encoding="utf-8")
core_source = (ROOT / "use_core.py").read_text(encoding="utf-8")

for required in (
    'APP_VERSION = "v387"',
    'DEPLOYMENT_FINGERPRINT = "USE-v387-secondary-pathway-relevance"',
    'CANONICAL_BUILD_ID = "USE-BUILD-v387-secondary-pathway-relevance"',
    "_original_recommendation_output_authority",
    "_original_recommendation_resource_identity",
    "_select_secondary_pathways",
    "_is_acute_risk_resource",
    "_archive_bridge",
    "use_core.app",
):
    assert required in main_source, required

assert 'CANONICAL_BUILD_PAYLOAD_SHA256 = "__PAYLOAD_SHA256__"' not in main_source
assert 'CANONICAL_BUILD_PAYLOAD_SHA256 = "PLACEHOLDER_RECOMPUTE_REQUIRED"' not in main_source
assert "RUNTIME_SOURCE_SHA256" in main_source
assert "USE REQUEST START:" in core_source
assert "X-USE-Build-ID" in core_source
assert "X-USE-Version" in core_source
assert "X-USE-Fingerprint" in core_source
assert "X-USE-Source-SHA256" in core_source

for required in (
    "def _transition_profile",
    "def _transition_retrieval_strategy",
    "def _direct_open_transition_response",
    "def _v387_finalize",
    "def _query_profile",
    "def _guide_answer_architecture",
    "def _build_sensitive_recommendation_answer",
):
    assert required in main_source, required

assert "_BENCHMARK_PRIMARY_TITLE" not in main_source
assert "_BENCHMARK_PRIMARY_URL" not in main_source

compile(ast.parse(main_source), filename="main.py", mode="exec")
compile(ast.parse(core_source), filename="use_core.py", mode="exec")

print("USE v387 compatibility validation: PASS")
