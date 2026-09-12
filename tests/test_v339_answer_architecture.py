from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "main.py"


def _function_source(source, name):
    tree = ast.parse(source)
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    return ast.get_source_segment(source, node)


def test_generalized_guide_architecture_has_holistic_contract():
    source = MAIN.read_text(encoding="utf-8")
    assert "human reality" in source
    assert "humane foothold" in source
    assert "epistemic" in source
    assert "reflection pathway" in source
    assert "route" in source.lower()


def test_answer_architecture_is_structural_not_grief_only():
    source = MAIN.read_text(encoding="utf-8")
    text = _function_source(source, "_guide_answer_architecture")
    assert "_query_profile(user_query, docs)" in text
    assert "_select_secondary_pathways(docs, title, profile)" in text
    assert "profile[\"sensitive\"]" in text
    assert "profile[\"grief\"]" in text


def test_secondary_pathways_are_evidence_ranked_and_canonical():
    source = MAIN.read_text(encoding="utf-8")
    text = _function_source(source, "_select_secondary_pathways")
    assert "score" in text
    assert "_normalize_title" in text
    assert "return [doc for _, _, doc in candidates[:limit]]" in text
    link_text = _function_source(source, "_resource_link")
    assert "return f\"[{title}]({url})\"" in link_text


def test_sensitive_answers_have_risk_branch_without_generic_disclaimer():
    source = MAIN.read_text(encoding="utf-8")
    text = _function_source(source, "_query_profile")
    assert "suicid" in text
    assert "abuse" in text
    assert "coercion" in text
    builder = _function_source(source, "_v339_build_compassionate_recommendation_answer")
    assert "profile[\"risk\"]" in builder
    assert "immediate danger" in builder


def test_existing_strengths_are_preserved():
    source = MAIN.read_text(encoding="utf-8")
    builder = _function_source(source, "_v339_build_compassionate_recommendation_answer")
    assert '"\\n\\n".join' in builder
    assert "A gentle place to begin" in builder
    assert "Take what feels useful" in builder
    assert "_resource_link(doc)" in builder
