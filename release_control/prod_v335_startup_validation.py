from pathlib import Path

source = Path("main.py").read_text(encoding="utf-8")
assert "# USE PRODUCTION VERSION: v335" in source
assert "Experimental branch only" not in source
assert 'EXPECTED_CORE_SOURCE_SHA256 = "ecbd5181958f95baedf397f715fa30ae0192005b9a39f005fe3c0ad8a8fb7ef2"' in source
assert "PLACEHOLDER_RECOMPUTE_REQUIRED" in source
assert "CANONICAL_BUILD_PAYLOAD_SHA256" in source
assert "_core_runtime_sha != EXPECTED_CORE_SOURCE_SHA256" in source
print("V335 STARTUP IDENTITY REGRESSION: PASS")
