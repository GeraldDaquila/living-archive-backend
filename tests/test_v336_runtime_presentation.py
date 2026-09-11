import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "main.py"

PRIMARY = "The Transformative Power of Loss: Finding Meaning in Grief Through Spiritual and Scientific Wisdom"
PRIMARY_URL = "https://geralddaquila.com/2025/05/12/the-transformative-power-of-loss-finding-meaning-in-grief-through-spiritual-and-scientific-wisdom/"


def _load_constructor():
    source = MAIN.read_text(encoding="utf-8")
    tree = ast.parse(source)
    wanted = {
        "_parse_context_documents",
        "_v338_recommendation_fit_sentence",
        "_v336_construct_visitor_answer",
        "_v339_canonical_recommendation_doorway",
        "_v338_final_answer_boundary",
        "_v338_build_recommendation_answer",
        "_v337_apply_recommendation_authority",
    }
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in wanted]
    code = "\n\n".join(ast.get_source_segment(source, node) for node in nodes)

    class Core:
        def _is_recommendation_question(self, _q):
            return True
        def normalize_link_presentation(self, title, _ctx):
            return f"[{title}]({PRIMARY_URL})" if PRIMARY in title else title
        def _adjudicate_recommendation_resource(self, docs, _q):
            return docs[0] if docs else None
        def _movement_question_requires_canonical_next(self, _q):
            return False
        def recognize_question_structure(self, _q):
            return {"structure": ""}
        def _question_is_underdetermined(self, _q):
            return False

    namespace = {
        "re": __import__("re"),
        "use_core": Core(),
        "_original_violation": lambda *_a: None,
        "_original_recommendation_output_authority": lambda _q, answer, _c: answer,
        "_original_recommendation_resource_identity": lambda _q, answer, _c: answer,
    }
    exec(compile(code, str(MAIN), "exec"), namespace)
    return namespace["_v336_construct_visitor_answer"]


def test_v336_rebuilds_exact_canonical_link():
    construct = _load_constructor()
    answer = "A strong place to begin is The Transformative Power of Loss: Finding Meaning in Grief Through Spiritual and Scientific Wisdom."
    context = (
        "Title: The Transformative Power of Loss: Finding Meaning in Grief Through Spiritual and Scientific Wisdom\n"
        f"URL: {PRIMARY_URL}\n"
        "Content: The work addresses grief, loss, and death through spiritual and scientific framing."
    )
    result = construct(answer, "What advise or essay can you recommend for someone grieving the death of a loved one?", context, context)
    assert f"[{PRIMARY}]({PRIMARY_URL})" in result


def test_v336_does_not_invent_links_without_canonical_context():
    construct = _load_constructor()
    answer = "A useful place to begin is The Transformative Power of Loss."
    result = construct(answer, "Recommend an essay", "", "")
    assert "https://" not in result
