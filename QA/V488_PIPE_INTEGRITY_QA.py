"""Post-Oct.1 Guide hub pipe integrity audit.

This audit checks the transport/routing seams that can fail before visitor
experience testing:
- current mainline deployment identity is structurally bounded;
- active specialist routing crosses the explicit hub contract;
- the protected core remains the only legacy FastAPI fallback;
- the hub does not contain retrieval/provider authority;
- retired HRN routing is observational only and is not reintroduced as a spoke.
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
    # Only the two active visitor-facing spokes use the hub. HRN's former
    # relationship specialist route is intentionally retired.
    assert main_source.count("route_spoke(") == 2

    for marker in (
        'specialist_id="formation"',
        'specialist_id="systems_ph"',
        "SPECIALIST_ADAPTER_REGISTRY",
        "invoke_specialist",
    ):
        assert marker in main_source, marker

    # HRN remains retired from visitor routing: the relationship classifier
    # may be observed, but no relationship specialist is invoked through hub.
    assert 'specialist_id="relationship"' not in main_source
    assert "def _relationship_specialist_response(" not in main_source
    assert 'if route_id == "relationship":' in main_source
    assert "rather than invoking the specialist" in main_source
    assert "The Guide relational inquiry retained natively" in main_source

    # The active request boundary has two protected-app fallbacks. Empty-query
    # passthrough remains direct; the normal non-specialist JSON path passes
    # through the shared final visitor-response guard.
    assert main_source.count("_FASTAPI_APP(scope, _use_replay_receive(raw_body), send)") == 1
    assert main_source.count("_FASTAPI_APP(scope, _use_replay_receive(raw_body), _send_with_final_visitor_boundary)") == 1
    assert "def _guide_finalize_visitor_payload(payload, query):" in main_source
    assert "def _guide_outer_visitor_response_boundary(scope, receive, send):" in main_source
    assert "app = streaming_entry(_guide_outer_visitor_response_boundary)" in main_source

    # The hub contract itself must remain authority-light.
    lower_hub = hub_source.casefold()
    for forbidden in (
        "pinecone",
        "groq",
        "fetch_canonical_context",
        "generate_llm_response",
    ):
        assert forbidden not in lower_hub, forbidden

    # Active specialist implementations must not bypass the hub callable.
    tree = ast.parse(main_source)
    for specialist_fn in (
        "_formation_specialist_response",
        "_philippine_systems_specialist_response",
    ):
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
