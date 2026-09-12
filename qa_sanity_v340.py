import py_compile
from pathlib import Path

py_compile.compile("main.py", doraise=True)
text = Path("main.py").read_text(encoding="utf-8")
assert 'APP_VERSION = "v340"' in text
assert 'USE-v340-universal-guide-orientation' in text
assert 'EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"' in text
assert 'def _question_alignment_score' in text
assert 'def _select_question_aligned_primary' in text
assert 'question-aligned Guide doorway used for topical inquiry' in text
print("v340 sanity validation passed")
