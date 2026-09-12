from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "main.py"


def _function_source(source, name):
    tree = ast.parse(source)
    node = next(
        n for n in tree.body
        if isinstance(n, ast.FunctionDef) and n.name == name
    )
    return ast.get_source_segment(source, node)


def test_secondary_resource_link_strips_leading_emoji():
    source = MAIN.read_text(encoding="utf-8")
    text = _function_source(source, "_resource_link")
    assert "re.sub" in text
    assert "[\\U0001F300-\\U0001FAFF]" in text


def test_secondary_links_remain_canonical_markdown_links():
    source = MAIN.read_text(encoding="utf-8")
    text = _function_source(source, "_resource_link")
    assert "return f\"[{title}]({url})\"" in text
