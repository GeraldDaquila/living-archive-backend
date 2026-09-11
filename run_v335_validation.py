import ast
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "main.py"
CORE = ROOT / "use_core.py"
BASE_COMMIT = "b663397c04d1506392a3d227a0dc291ce02f109f"
PREVIOUS_FIXED_INPUT_CHARS = 3756
PREVIOUS_ESTIMATED_OUTPUT_CHARS = 1280
MAX_PROVIDER_INPUT_CHARS = 3800
MAX_PROVIDER_TOTAL_CHARS = 4600


def _extract_function(source, name):
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return ast.get_source_segment(source, node)
    raise AssertionError(f"function not found: {name}")


def _extract_assignment(source, name):
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return ast.get_source_segment(source, node)
    raise AssertionError(f"assignment not found: {name}")


def _literal_assignment(source, name):
    assignment = _extract_assignment(source, name)
    return ast.literal_eval(assignment.split("=", 1)[1].strip())
