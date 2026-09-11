import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent
source = (ROOT / "main.py").read_text(encoding="utf-8")
tree = ast.parse(source, filename="main.py")
assert any(isinstance(node, ast.FunctionDef) and node.name == "generate_llm_response" for node in tree.body)
assert any(isinstance(node, ast.FunctionDef) and node.name == "search_visitor" for node in tree.body)
app_assignments = [
    node for node in tree.body
    if isinstance(node, ast.Assign)
    and any(isinstance(target, ast.Name) and target.id == "app" for target in node.targets)
]
assert any(
    isinstance(node.value, ast.Attribute)
    and isinstance(node.value.value, ast.Name)
    and node.value.value.id == "use_core"
    and node.value.attr == "app"
    for node in app_assignments
), "main.py must export app = use_core.app for uvicorn main:app"
boundary_fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_v336_run_generation_boundary")
return_node = next(node for node in ast.walk(boundary_fn) if isinstance(node, ast.Return))
call = return_node.value
assert isinstance(call, ast.Call) and len(call.args) >= 4
assert isinstance(call.func, ast.Name) and call.func.id == "_v336_construct_visitor_answer"
assert [getattr(arg, "id", None) for arg in call.args[:4]] == ["answer", "user_query", "retrieved_context", "canonical_link_context"]
assert 'if __name__ == "__main__":' in source
compile(source, "main.py", "exec")
print("USE v338 ASGI/runtime-seam validation: PASS")
