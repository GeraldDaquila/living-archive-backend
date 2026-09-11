from pathlib import Path
import ast
import re

ROOT = Path(__file__).resolve().parent
main_source = (ROOT / "main.py").read_text(encoding="utf-8")
core_source = (ROOT / "use_core.py").read_text(encoding="utf-8")

assert 'APP_VERSION = "v337"' in main_source
assert "_adjudicate_recommendation_resource" in main_source
assert "A strong place to begin is {title}." in main_source
assert "_original_recommendation_output_authority" in main_source
assert "_original_recommendation_resource_identity" in main_source

# The canonical v241 benchmark must remain encoded in the protected core.
primary = "The Transformative Power of Loss: Finding Meaning in Grief Through Spiritual and Scientific Wisdom"
secondary = "Journey Beyond: Exploring the Afterlife and Reincarnation Through Hypnosis and Near-Death Experiences"
assert primary in core_source
assert secondary in core_source

# Compile both production modules.
compile(ast.parse(main_source), filename="main.py", mode="exec")
compile(ast.parse(core_source), filename="use_core.py", mode="exec")
print("USE v338 recommendation boundary validation: PASS")
