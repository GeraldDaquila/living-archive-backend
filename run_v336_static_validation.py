import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "main.py"
CORE = ROOT / "use_core.py"


def _source(path):
    return path.read_text(encoding="utf-8")


def _functions(source):
    tree = ast.parse(source)
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def main():
    main = _source(MAIN)
    core = _source(CORE)

    assert "APP_VERSION = \"v336\"" in main
    assert "DEPLOYMENT_FINGERPRINT = \"USE-v336-visitor-answer-construction\"" in main
    assert "_v335_build_generation_messages" in _functions(main)
    assert "_v336_construct_visitor_answer" in _functions(main)

    # v336 must remain a final visitor-facing layer, not a retrieval rewrite.
    forbidden_retrieval_definitions = (
        "def fetch_canonical_context",
        "def select_canonical_doorways",
        "def _query_index",
        "def generate_embedding",
    )
    for marker in forbidden_retrieval_definitions:
        assert marker not in main

    # Canonical presentation remains owned by protected use_core.py.
    assert "def normalize_link_presentation" in core
    assert "use_core.normalize_link_presentation" in main

    # Visitor contract guards.
    for marker in (
        "Answer first",
        "adjudicated primary",
        "Preserve the visitor's terms and agency.",
        "Movement: say 'next' only when D29 validates the destination.",
        "There is no supplied canonical",
        "The strongest place to begin in the Archive is",
    ):
        assert marker in main

    # The new layer must remain compact and provider-independent.
    start = main.index("def _v336_construct_visitor_answer")
    end = main.index("def _v335_build_generation_messages", start)
    fn = main[start:end]
    assert len(fn) < 9000
    assert "groq" not in fn.casefold()
    assert "pinecone" not in fn.casefold()

    print("V336 VISITOR ANSWER STATIC VALIDATION: PASS")


if __name__ == "__main__":
    main()
