from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "main.py"


def _load_sensitive_builder():
    source = MAIN.read_text(encoding="utf-8")
    tree = ast.parse(source)
    wanted = {"_parse_context_documents", "_query_profile", "_evidence_boundary_note", "_secondary_role", "_is_acute_risk_resource", "_select_secondary_pathways", "_extract_archive_metadata", "_archive_context", "_archive_bridge", "_guide_answer_architecture", "_build_sensitive_recommendation_answer"}
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in wanted]
    code = "\n\n".join(ast.get_source_segment(source, node) for node in nodes)
    namespace = {"re": __import__("re")}
    exec(compile(code, str(MAIN), "exec"), namespace)
    return namespace["_build_sensitive_recommendation_answer"], namespace


def test_v387_builds_canonical_link_only_from_supplied_evidence():
    build, _namespace = _load_sensitive_builder()
    primary = {"title": "Primary Essay", "url": "https://example.com/primary", "text": "A grounded reflection on grief and loss."}
    secondary = {"title": "Continuity Essay", "url": "https://example.com/continuity", "text": "A reflection on grief, continuity, and meaning."}
    risk = {"title": "Crisis Essay", "url": "https://example.com/crisis", "text": "suicidal ideation and acute crisis intervention."}
    docs = [primary, secondary, risk]
    result = build("Can you recommend an essay for someone grieving the death of a loved one?", primary, docs)
    assert "[Primary Essay](https://example.com/primary)" in result
    assert "https://example.com/continuity" in result
    assert "https://example.com/crisis" not in result


def test_v387_does_not_invent_links_without_valid_primary():
    build, _namespace = _load_sensitive_builder()
    result = build("Recommend an essay", {"title": "No URL", "url": "", "text": "grief"}, [])
    assert result == ""
