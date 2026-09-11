import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "main.py"


def _extract_function(source, name):
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(source, node)
    raise AssertionError(f"missing function: {name}")


def _load_constructor():
    source = MAIN.read_text(encoding="utf-8")
    fn = _extract_function(source, "_v336_construct_visitor_answer")
    class StubCore:
        @staticmethod
        def normalize_link_presentation(answer, context):
            pairs = re.findall(
                r"(?ms)^Title:\s*(.+?)\s*$\nURL:\s*(https?://\S+)\s*$\nContent:\s*(.*?)(?=\n\n---\n\n|\Z)",
                context,
            )
            for title, url, _content in pairs:
                answer = re.sub(
                    rf"(?<![\w\]]){re.escape(title)}(?![\w])",
                    f"[{title}]({url})",
                    answer,
                    flags=re.IGNORECASE,
                )
            return answer
    ns = {"re": re, "use_core": StubCore()}
    exec(fn, ns)
    return ns["_v336_construct_visitor_answer"]


def test_v336_rebuilds_exact_canonical_link():
    construct = _load_constructor()
    answer = "A strong place to begin is The Transformative Power of Loss: Finding Meaning in Grief Through Spiritual and Scientific Wisdom."
    context = (
        "Title: The Transformative Power of Loss: Finding Meaning in Grief Through Spiritual and Scientific Wisdom\n"
        "URL: https://geralddaquila.com/2025/05/12/the-transformative-power-of-loss-finding-meaning-in-grief-through-spiritual-and-scientific-wisdom/\n"
        "Content: The work addresses grief, loss, and death through spiritual and scientific framing."
    )
    result = construct(answer, "What advise or essay can you recommend for someone grieving the death of a loved one?", context, context)
    assert "[The Transformative Power of Loss: Finding Meaning in Grief Through Spiritual and Scientific Wisdom](https://geralddaquila.com/2025/05/12/the-transformative-power-of-loss-finding-meaning-in-grief-through-spiritual-and-scientific-wisdom/)" in result


def test_v336_removes_machine_boundary_language():
    construct = _load_constructor()
    answer = "There is no supplied canonical essay or advice from the Living Archive that directly addresses this request."
    result = construct(answer, "Recommend an essay", "", "")
    assert "supplied canonical" not in result.casefold()
    assert "retrieval" not in result.casefold()
    assert "provider" not in result.casefold()


def test_v336_does_not_invent_links_without_canonical_context():
    construct = _load_constructor()
    answer = "A useful place to begin is The Transformative Power of Loss."
    result = construct(answer, "Recommend an essay", "", "")
    assert "http://" not in result
    assert "https://" not in result
    assert "[The Transformative Power of Loss]" not in result
