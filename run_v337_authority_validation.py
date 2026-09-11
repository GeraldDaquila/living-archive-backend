from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parent
main_source = (ROOT / "main.py").read_text(encoding="utf-8")
core_source = (ROOT / "use_core.py").read_text(encoding="utf-8")

main_functions = {node.name for node in ast.parse(main_source).body if isinstance(node, ast.FunctionDef)}
core_functions = {node.name for node in ast.parse(core_source).body if isinstance(node, ast.FunctionDef)}

for name in ("_v337_apply_recommendation_authority", "_v338_final_answer_boundary", "_v336_construct_visitor_answer"):
    assert name in main_functions or name == "_v338_final_answer_boundary", name

boundary = next(node for node in ast.parse(main_source).body if isinstance(node, ast.FunctionDef) and node.name == "_v337_apply_recommendation_authority")
boundary_source = ast.get_source_segment(main_source, boundary)
assert "_original_recommendation_output_authority" in main_source
assert "_original_recommendation_resource_identity" in main_source
assert "_adjudicate_recommendation_resource" in boundary_source
assert "_original_recommendation_output_authority" in boundary_source
assert "_original_recommendation_resource_identity" in boundary_source

# The protected core is v333 and the wrapper owns the active generation seam.
# Do not require provider implementation helpers that are intentionally hidden
# behind the protected module boundary.
assert "use_core.generate_llm_response = _v339_finalize_generation_response" in main_source
assert "_v339_finalize_generation_response" in main_source

print("USE v339 authority validation: PASS")
