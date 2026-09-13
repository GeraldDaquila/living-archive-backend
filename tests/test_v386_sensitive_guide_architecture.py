from pathlib import Path
import ast, hashlib
ROOT=Path(__file__).resolve().parents[1]
MAIN=ROOT/'main.py'
CORE=ROOT/'use_core.py'
EXPECTED='fb3208a8d287f16562ffd640d89f65d5e8d18607'
def _blob(data): return hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest()
def test_candidate_compiles(): ast.parse(MAIN.read_text(encoding='utf-8'))
def test_core_identity(): assert _blob(CORE.read_bytes())==EXPECTED
def test_transition_and_sensitive_seams():
 s=MAIN.read_text(encoding='utf-8'); f=next(n for n in ast.parse(s).body if isinstance(n,ast.FunctionDef) and n.name=='_v386_finalize'); t=ast.get_source_segment(s,f); assert 'is_open_transition' in t and '_build_sensitive_recommendation_answer' in t
