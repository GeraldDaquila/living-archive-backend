from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parent
main_source = (ROOT / "main.py").read_text(encoding="utf-8")
core_source = (ROOT / "use_core.py").read_text(encoding="utf-8")

for required in (
    'APP_VERSION = "v339"',
    'DEPLOYMENT_FINGERPRINT = "USE-v339-canonical-recommendation-doorway"',
    "_adjudicate_recommendation_resource",
    "A useful place to begin is {title}.",
    "_original_recommendation_output_authority",
    "_original_recommendation_resource_identity",
    "_v339_canonical_recommendation_doorway",
):
    assert required in main_source, required

assert 'CANONICAL_BUILD_PAYLOAD_SHA256 = "__PAYLOAD_SHA256__"' not in main_source
assert 'CANONICAL_BUILD_PAYLOAD_SHA256 = "PLACEHOLDER_RECOMPUTE_REQUIRED"' not in main_source
assert "RUNTIME_SOURCE_SHA256" in main_source
assert "RUNTIME_BOOT_ID" in main_source
assert "RUNTIME_PROCESS_ID" in main_source
assert "app = use_core.app" in main_source
assert "RUNTIME_SOURCE_SHA256 = _sha256(_MAIN_PATH.read_bytes())" in main_source
assert "_core_runtime_sha != EXPECTED_CORE_SOURCE_SHA256" in main_source

for required in (
    "def _v338_recommendation_fit_sentence",
    "def _v338_build_recommendation_answer",
    "def _v338_final_answer_boundary",
    "def _v339_canonical_recommendation_doorway",
    "def _v336_construct_visitor_answer",
):
    assert required in main_source

primary = "The Transformative Power of Loss: Finding Meaning in Grief Through Spiritual and Scientific Wisdom"
secondary = "Journey Beyond: Exploring the Afterlife and Reincarnation Through Hypnosis and Near-Death Experiences"
# Protected-core production content remains fixed; the benchmark identity is
# owned by the wrapper/validation layer rather than duplicated into the core.
assert primary in main_source
assert secondary in main_source

compile(ast.parse(main_source), filename="main.py", mode="exec")
compile(ast.parse(core_source), filename="use_core.py", mode="exec")

print("USE v339 recommendation boundary validation: PASS")
