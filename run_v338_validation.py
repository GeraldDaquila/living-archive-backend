from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parent
main_source = (ROOT / "main.py").read_text(encoding="utf-8")
core_source = (ROOT / "use_core.py").read_text(encoding="utf-8")

for required in (
    'APP_VERSION = "v338"',
    "_adjudicate_recommendation_resource",
    "A strong place to begin is {title}.",
    "_original_recommendation_output_authority",
    "_original_recommendation_resource_identity",
):
    assert required in main_source, required

for required in (
    "def _v338_construct_recommendation_fit",
    "def _v337_apply_recommendation_authority",
    "def _v337_final_answer_boundary",
    "def _v336_construct_visitor_answer",
):
    assert required in main_source, required

primary = "The Transformative Power of Loss: Finding Meaning in Grief Through Spiritual and Scientific Wisdom"
secondary = "Journey Beyond: Exploring the Afterlife and Reincarnation Through Hypnosis and Near-Death Experiences"
assert primary in core_source
assert secondary in core_source

compile(ast.parse(main_source), filename="main.py", mode="exec")
compile(ast.parse(core_source), filename="use_core.py", mode="exec")

print("USE v338 recommendation boundary validation: PASS")
