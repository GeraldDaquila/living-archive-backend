from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parent
main_source = (ROOT / "main.py").read_text(encoding="utf-8")
core_source = (ROOT / "use_core.py").read_text(encoding="utf-8")

assert 'APP_VERSION = "v338"' in main_source
assert "_v338_recommendation_fit_sentence" in main_source
assert "_v338_build_recommendation_answer" in main_source
assert "_adjudicate_recommendation_resource" in main_source
primary = "The Transformative Power of Loss: Finding Meaning in Grief Through Spiritual and Scientific Wisdom"
secondary = "Journey Beyond: Exploring the Afterlife and Reincarnation Through Hypnosis and Near-Death Experiences"
assert primary in core_source
assert secondary in core_source
ast.parse(main_source)
ast.parse(core_source)
print("USE v338 recommendation fit synthesis validation: PASS")
