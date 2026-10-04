"""Post-Oct.1 Guide hub pipe integrity audit.

This audit deliberately checks the transport/routing seams that can fail
before visitor experience testing:
- current mainline deployment identity is structurally bounded;
- specialist routing crosses the explicit hub contract;
- the protected core remains the only legacy FastAPI fallback;
- the hub does not contain retrieval/provider authority;
- no new specialist route is wired directly around the hub contract.
"""

from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]


def _source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def main():
    main_source = _source("main.py")
    hub_source = _source("hub_contracts.py")

    ast.parse(main_source, filename="main.py")
    ast.parse(hub_source, filename="hub_contracts.py")

    assert 'from hub_contracts import (' in main_source
    assert "build_hub_request" in main_source
    assert "route_spoke" in main_source
    assert main_source.count("route_spoke(") == 2

    # Relationship and Formation must both enter through the common hub pipe.
    for marker in (
        'specialist_id="relationship"',
        'specialist_id="formation"',
        "SPECIALIST_ADAPTER_REGISTRY",
        "invoke_specialist",
    ):
        assert marker in main_source, marker

    # The active request boundary has exactly two protected-app fallbacks: empty-query passthrough and normal non-specialist passthrough.
    assert main_source.count("_FASTAPI_APP(scope, _use_replay_receive(raw_body), send)") == 2
    assert "app = _use_request_boundary" in main_source

    # The hub contract itself must remain authority-light.
    lower_hub = hub_source.casefold()
    for forbidden in (
        "pinecone",
        "groq",
        "fetch_canonical_context",
        "generate_llm_response",
    ):
        assert forbidden not in lower_hub, forbidden

    # No specialist handoff may bypass the hub callable contract.
    for specialist_fn in (
        "_relationship_specialist_response",
        "_formation_specialist_response",
    ):
        tree = ast.parse(main_source)
        fn = next(
            node for node in tree.body
            if isinstance(node, ast.FunctionDef)
            and node.name == specialist_fn
        )
        segment = ast.get_source_segment(main_source, fn) or ""
        assert "route_spoke(" in segment, specialist_fn

    print("post-Oct.1 pipe integrity QA: PASS")


if __name__ == "__main__":
    main()
