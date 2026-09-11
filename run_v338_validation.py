from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parent
main_source = (ROOT / "main.py").read_text(encoding="utf-8")
core_source = (ROOT / "use_core.py").read_text(encoding="utf-8")

# v339 supersedes the v338 wrapper identity. Keep this compatibility probe
# focused on the recommendation-authority seams that remain invariant.
for required in (
    "_adjudicate_recommendation_resource",
    "A useful place to begin is {title}.",
    "_original_recommendation_output_authority",
    "_original_recommendation_resource_identity",
    "_v339_canonical_recommendation_doorway",
):
    assert required in main_source, required

for required in (
    "def _v338_recommendation_fit_sentence",
    "def _v338_build_recommendation_answer",
    "def _v338_final_answer_boundary",
    "def _v336_construct_visitor_answer",
):
    assert required in main_source, required

primary = "The Transformative Power of Loss: Finding Meaning in Grief Through Spiritual and Scientific Wisdom"
secondary = "Journey Beyond: Exploring the Afterlife and Reincarnation Through Hypnosis and Near-Death Experiences"
assert primary in core_source
assert secondary in core_source

compile(ast.parse(main_source), filename="main.py", mode="exec")
compile(ast.parse(core_source), filename="use_core.py", mode="exec")

print("USE recommendation boundary compatibility validation: PASS")
