from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "main.py"


def test_recommendation_builder_is_chunked_and_links_secondaries():
    source = MAIN.read_text(encoding="utf-8")
    tree = ast.parse(source)
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_v339_build_compassionate_recommendation_answer")
    text = ast.get_source_segment(source, fn)
    assert '"\\n\\n".join' in text
    assert "A gentle place to begin is" in text
    assert "Take what feels useful" in text
    assert "_resource_link(doc)" in text
    assert "if not doc_title or doc_title == title:" in text
