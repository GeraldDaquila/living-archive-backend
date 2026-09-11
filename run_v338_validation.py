from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parent
main_source = (ROOT / "main.py").read_text(encoding="utf-8")
core_source = (ROOT / "use_core.py").read_text(encoding="utf-8")

for required in (
    'APP_VERSION = "v337"',
    "_adjudicate_recommendation_resource",
    "A strong place to begin is {title}.",
    "_original_recommendation_output_authority",
    "_original_recommendation_resource_identity",
):
    # v338 preserves the v337 wrapper seam; no production version bump occurs
    # inside this experiment branch until promotion.
    assert required in main_source, required

primary = "The Transformative Power of Loss: Finding Meaning in Grief Through Spiritual and Scientific Wisdom"
secondary = "Journey Beyond: Exploring the Afterlife and Reincarnation Through Hypnosis and Near-Death Experiences"
assert primary in core_source
assert secondary in core_source

compile(ast.parse(main_source), filename="main.py", mode="exec")
compile(ast.parse(core_source), filename="use_core.py", mode="exec")

print("USE v338 recommendation boundary validation: PASS")
