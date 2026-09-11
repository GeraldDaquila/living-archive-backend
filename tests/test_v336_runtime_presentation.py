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
        name for name in (
            "_v336_construct_visitor_answer",
            "_v339_canonical_recommendation_doorway",
            "_v338_final_answer_boundary",
            "_v338_build_recommendation_answer",
            "_v337_apply_recommendation_authority",
        )
    }
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in wanted]
    code = "\n\n".join(ast.get_source_segment(source, node) for node in nodes)
    namespace = {
        "re": __import__("re"),
        "use_core": type("Core", (), {
            "_is_recommendation_question": lambda _q: True,
            "normalize_link_presentation": lambda title, ctx: f"[{title}]({PRIMARY_URL})" if PRIMARY in title else title,
            "_adjudicate_recommendation_resource": lambda docs, _q: docs[0] if docs else None,
            "_movement_question_requires_canonical_next": lambda _q: False,
            "recognize_question_structure": lambda _q: {"structure": ""},
            "_question_is_underdetermined": lambda _q: False,
        })(),
        "_original_violation": lambda *_a: None,
        "_original_recommendation_output_authority": lambda _q, answer, _c: answer,
        "_original_recommendation_resource_identity": lambda _q, answer, _c: answer,
        "_v338_recommendation_fit_sentence": lambda _q, _p: "",
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
