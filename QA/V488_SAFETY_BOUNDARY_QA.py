import re
"""Sitewide Safety Boundary Regression QA v488.67.

Checks deterministic safety normalization, active safety follow-through, and the
Guide's fail-closed interruption boundary without invoking the protected core
or any live provider.
"""

from pathlib import Path
import ast
import json

ROOT = Path(__file__).resolve().parents[1]


def _source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def main():
    safety_source = _source("safety_intelligence.py")
    main_source = _source("main.py")

    ast.parse(safety_source, filename="safety_intelligence.py")
    ast.parse(main_source, filename="main.py")

    namespace = {}
    exec(compile(safety_source, "safety_intelligence.py", "exec"), namespace, namespace)
    classify = namespace["normalize_safety_state"]
    semantic_candidate = namespace["_semantic_safety_candidate"]
    fast_initial = namespace["_initial_deterministic_safety_response"]
    normalize_resolution = namespace["normalize_safety_resolution"]
    repair = namespace["repair_safety_question"]
    assert namespace["SAFETY_INTELLIGENCE_CONTRACT_VERSION"] == "v2.6"

    assert classify("I don't want to live anymore.") in {"current", "acute"}
    assert classify("I don’t want to live anymore.") in {"current", "acute"}
    assert classify("I'm thinking of killing myself.") == "current"
    assert classify("I am going to kill myself.") == "acute"
    assert classify("Someone I care about is talking about suicide.") == "support"
    assert classify("What is suicide?") is None
    assert classify("What does self-harm mean?") is None

    # Ordinary relational conflict must not be escalated into the sitewide
    # safety lane, and must not even pay the semantic-detector latency cost.
    ordinary_relational_query = (
        "Whenever I bring up something that bothers me, my partner becomes defensive. "
        "Then I get angry, they withdraw, and eventually we stop talking. "
        "A few days later everything seems fine until the same thing happens again."
    )
    assert classify(ordinary_relational_query) is None
    assert semantic_candidate(ordinary_relational_query) is False
    assert semantic_candidate("I don't want to live anymore.") is True
    assert semantic_candidate("I'm thinking of killing myself.") is True
    assert classify("I want to die.") == "acute"

    # High-confidence first-turn safety disclosures must have an immediate,
    # provider-independent movement. The HRN safety composer is not allowed
    # to become the critical path for this first question.
    fast = fast_initial(query="I want to die.", safety_state="acute", country="NL", emergency_resolution={})
    assert fast["safety"] == "acute"
    assert fast["safety_question"] == "Do you think you might act on these thoughts right now?"
    assert fast["safety_release_ready"] is False
    assert fast["resolver_status"] == "deterministic_initial_fast_path"
    assert "another person" in fast["safety_message"].casefold()

    # Unscoped HRN hotline numbers must never leak into an unknown-location
    # safety response. The verified emergency registry alone controls numbers.
    unknown_location = {
        "location": {
            "resolution_status": "UNKNOWN",
            "location": {"country": {"value": None}},
        },
        "selection": {"selection_status": "LOCATION_REQUIRED", "primary": []},
    }
    hrn_with_us_numbers = {
        "safety": "acute_connection",
        "safety_interrupt": True,
        "safety_message": "Please stay with another person while we make sure you are safe.",
        "safety_question": "Are you safe from acting on these thoughts right now?",
        "safety_note": "Stay with another person.",
        "safety_resources": [
            {"title": "911 — Emergency assistance", "phone": "911"},
            {"title": "988 — Suicide & Crisis Lifeline", "phone": "988"},
        ],
        "safety_location_required": False,
        "country": "US",
        "safety_release_ready": False,
    }
    unlocated = normalize_resolution(
        hrn_with_us_numbers,
        requested_state="acute",
        country="",
        emergency_resolution=unknown_location,
    )
    assert unlocated["safety_resources"] == []
    assert unlocated["safety_location_required"] is True
    assert unlocated["country"] == ""
    assert "won't guess" in unlocated["safety_note"]

    verified_ph = {
        "location": {
            "resolution_status": "RESOLVED",
            "location": {"country": {"value": "PH"}},
        },
        "selection": {
            "selection_status": "SELECTED",
            "primary": {
                "display_name": "Unified 911 Emergency Hotline",
                "number": "911",
                "service_types": ["general_emergency"],
                "presentation_priority": 100,
                "_verification": {"source": "DILG", "evidence_type": "official_government_publication", "status": "verified"},
            },
        },
    }
    located = normalize_resolution(
        hrn_with_us_numbers,
        requested_state="acute",
        country="PH",
        emergency_resolution=verified_ph,
    )
    assert [resource["phone"] for resource in located["safety_resources"]] == ["911"]
    assert located["country"] == "PH"
    assert located["safety_location_required"] is False
    assert semantic_candidate("I am angry because my partner hurt my feelings.") is False

    # State-aware continuity repair: a missing HRN question must advance the
    # native safety sequence rather than repeat one generic presence question.
    assert repair(
        safety_state="acute",
        previous_question="",
        query="I want to kill myself.",
    ) == "Do you think you might act on these thoughts right now?"
    assert repair(
        safety_state="acute_followthrough",
        previous_question="Do you think you might act on these thoughts right now?",
        query="yes",
    ) == "Have you moved away from anything you could use to hurt yourself?"
    assert repair(
        safety_state="acute_followthrough",
        previous_question="Have you moved away from anything you could use to hurt yourself?",
        query="yes",
    ) == "Is there someone you trust who can stay with you right now?"
    assert repair(
        safety_state="acute_followthrough",
        previous_question="Is there someone you trust who can stay with you right now?",
        query="yes",
    ) == "Can you contact emergency or crisis support now?"
    assert repair(
        safety_state="acute_followthrough",
        previous_question="Can you contact emergency or crisis support now?",
        query="yes",
    ) == "Are you safe from acting on these thoughts right now?"
    assert classify(
        "yes",
        history=(
            "visitor: I want to kill myself.\n"
            "assistant: Is there someone you trust who can stay with you right now?"
        ),
    ) == "acute_followthrough"

    # Conversation-boundary regression: an assistant safety turn carries both
    # its human-facing message and its active safety question. The serializer
    # must preserve both so short answers remain inside the native safety loop.
    main_namespace = {}
    main_tree = ast.parse(main_source, filename="main.py")
    history_fn = next(
        node for node in main_tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_history_text"
    )
    history_module = ast.Module(body=[history_fn], type_ignores=[])
    ast.fix_missing_locations(history_module)
    exec(compile(history_module, "main.py", "exec"), main_namespace, main_namespace)
    serialized = main_namespace["_history_text"]([
        {"role": "visitor", "content": "I don't want to live anymore."},
        {
            "role": "assistant",
            "content": "Thank you for telling me. I want to take what you're saying seriously.",
            "question": "Do you think you might act on these thoughts right now?",
        },
        {"role": "visitor", "content": "yes"},
    ])
    assert "Do you think you might act on these thoughts right now?" in serialized
    assert 'safety_question_hint = str(parsed_body.get("safety_question") or "").strip()' in main_source
    assert 'safety_active_hint = bool(parsed_body.get("safety_active"))' in main_source
    assert 'safety_state = "acute_followthrough"' in main_source
    assert '"safety_question": safety_question_hint' in main_source
    assert "safety_continuity_guard" in main_source
    assert "native_next_movement_repaired" in main_source
    assert "repair_safety_question(" in main_source
    assert "if not safety_release_ready and not safety_question:" in main_source
    # Explicit visitor refusal must stop IP-derived location fallback; a proxy
    # or server IP must not be presented as the visitor's country.
    assert 'if str(context.get("refused") or "").strip().casefold() in {"true", "yes", "1", "refused"}:' in main_source
    refusal_segment = main_source[main_source.index("async def _resolve_request_location"):main_source.index("async def _use_request_boundary")]
    assert 'return {"refused": context.get("refused", True)}' in refusal_segment
    assert "Strip inferred and explicit location fields from the downstream" in refusal_segment
    version_match = re.search(r'APP_VERSION = "(v[0-9.]+)"', main_source)
    assert version_match, "APP_VERSION missing"
    app_version = version_match.group(1)
    assert f'if str(APP_VERSION) != "{app_version}":' in main_source
    assert 'SAFETY_BOUNDARY_CONTRACT_VERSION = "v488.68"' in main_source
    assert f'DEPLOYMENT_FINGERPRINT = "USE-{app_version}-' in main_source
    assert classify("yes", history=serialized) == "acute_followthrough"

    assert classify(
        "yes",
        history=(
            "visitor: I don’t want to live anymore.\n"
            "assistant: Do you think you might act on these thoughts right now?"
        ),
    ) == "acute_followthrough"

    safety_segment = main_source[
        main_source.index("safety_state = classify_safety"):
        main_source.index("# Immediate FSD handoff")
    ]
    assert '"intent": "SAFETY_INTERRUPT"' in safety_segment
    assert "return await _use_send_json(send" in safety_segment
    assert '"bypasses_ordinary_hrn": True' in safety_segment
    assert '"bypasses_llm": True' in safety_segment
    assert '"bypasses_retrieval": True' in safety_segment
    assert "_FASTAPI_APP" not in safety_segment

    # The protected core remains immutable from the safety QA perspective.
    assert 'EXPECTED_CORE_BLOB_SHA = "fb3208a8d287f16562ffd640d89f65d5e8d18607"' in main_source

    print("sitewide safety boundary QA: PASS")


if __name__ == "__main__":
    main()
