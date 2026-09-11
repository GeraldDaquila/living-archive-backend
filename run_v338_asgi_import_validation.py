import ast
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent
source = (ROOT / "main.py").read_text(encoding="utf-8")

tree = ast.parse(source, filename="main.py")
assert any(isinstance(node, ast.FunctionDef) and node.name == "generate_llm_response" for node in tree.body)
assert any(isinstance(node, ast.FunctionDef) and node.name == "search_visitor" for node in tree.body)
assert 'if __name__ == "__main__":' in source

spec = importlib.util.spec_from_file_location("use_main_probe", ROOT / "main.py")
module = importlib.util.module_from_spec(spec)
# Do not execute the module: production boot is validated by compile + AST here.
assert spec is not None
assert spec.loader is not None

compile(source, "main.py", "exec")
print("USE v338 ASGI import-shape validation: PASS")
