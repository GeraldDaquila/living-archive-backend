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

        @staticmethod
        def _is_recommendation_question(query):
            return "recommend" in query.casefold()

        @staticmethod
        def _adjudicate_recommendation_resource(docs, _query):
            return docs[0] if docs else None

    def doorway(query, value, context):
        if not StubCore._is_recommendation_question(query):
            return value.strip()
        match = re.search(
            r"^Title:\s*(.+?)\s*$\nURL:\s*(https?://\S+)\s*$\nContent:\s*(.*)$",
            context,
            flags=re.MULTILINE | re.DOTALL,
        )
        if not match:
            return value.strip()
        title, url, content = match.groups()
        clean = re.sub(r"\[([^\]]+)\]\(https?://[^)]*\)", r"\1", value)
        clean = clean.replace(title, "").strip(" .")
        return f"A useful place to begin is [{title}]({url}). It is a direct fit because it addresses grief, loss, and death in its own framing."

    ns = {
        "re": re,
        "use_core": StubCore(),
        "_v338_final_answer_boundary": lambda _q, answer, _c: answer,
        "_v339_canonical_recommendation_doorway": doorway,
    }
    exec(fn, ns)
    return ns["_v336_construct_visitor_answer"]


def test_v339_runtime_restores_missing_recommendation_url():
    construct = _load_constructor()
    title = "The Transformative Power of Loss: Finding Meaning in Grief Through Spiritual and Scientific Wisdom"
    url = "https://geralddaquila.com/2025/05/12/the-transformative-power-of-loss-finding-meaning-in-grief-through-spiritual-and-scientific-wisdom/"
    context = (
        f"Title: {title}\n"
        f"URL: {url}\n"
        "Content: The work addresses grief, loss, and death through spiritual and scientific framing."
    )
    result = construct(
        f"A useful place to begin is {title}.",
        "What advise or essay can you recommend for someone grieving the death of a loved one?",
        context,
        context,
    )
    assert f"[{title}]({url})" in result


def test_v339_runtime_does_not_invent_a_link_without_context():
    construct = _load_constructor()
    result = construct("A useful place to begin is The Transformative Power of Loss.", "Recommend an essay", "", "")
    assert "http://" not in result
    assert "https://" not in result
