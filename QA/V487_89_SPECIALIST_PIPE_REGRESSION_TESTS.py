"""Current specialist-pipe regression probes.

These probes exercise two failure seams that previously could pass structural
checks while failing in production:
1. domain-specific specialist payload preservation through the common pipe;
2. transient HRN transport failure recovery at the Relationship adapter.
"""

from pathlib import Path
from unittest.mock import patch
import json
import urllib.error

import provider_bank

from relationship_adapter import RelationshipAdapter
from specialist_adapters import (
    SpecialistAdapterContext,
    SpecialistAdapterRegistry,
    invoke_specialist,
)


ROOT = Path(__file__).resolve().parents[1]


class _FakeFormationAdapter:
    specialist_id = "formation"

    def process(self, context):
        return {
            "contract_version": "formation-v1",
            "request_id": context.request_id,
            "specialist_id": "formation",
            "status": "CONTRIBUTION",
            "voice_policy": "preserve_specialist_boundary",
            "interpretation": {
                "pathway": "The responsibility is changing shape.",
                "signals": {"responsibility_transition": True},
            },
            "movement": {"direction": "formation"},
            "canonical_candidates": [
                {
                    "id": "learning_arcs",
                    "title": "Learning Arcs",
                    "url": "https://geralddaquila.com/steward-access-12-learning-arcs/",
                }
            ],
            "boundary_notes": {"t4_destination_allowed": False},
            "safety_flags": {"safety_state": "green"},
        }


class _Response:
    def __init__(self, status, payload):
        self.status = status
        self._payload = payload

    def read(self):
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_domain_payload_survives_common_pipe():
    registry = SpecialistAdapterRegistry()
    registry.register(_FakeFormationAdapter())

    result = invoke_specialist(
        registry,
        request_id="qa-formation-payload-001",
        guide_version="qa-current",
        specialist_id="formation",
        original_question="I am carrying a larger responsibility.",
        recognized_territory="stewardship formation",
        processing_purpose="bounded formation navigation",
        guide_context={"situation": "A responsibility is changing."},
        safety_state="green",
    )

    assert result["status"] == "CONTRIBUTION"
    assert result["payload"]["interpretation"]["pathway"] == (
        "The responsibility is changing shape."
    )
    assert result["payload"]["movement"]["direction"] == "formation"
    assert result["canonical_candidates"][0]["id"] == "learning_arcs"


def test_relationship_adapter_retries_transient_503():
    adapter = RelationshipAdapter(endpoint="https://example.test/hrn", timeout=1.0)
    context = SpecialistAdapterContext(
        request_id="qa-hrn-retry-001",
        guide_version="v487.91",
        specialist_id="relationship",
        original_question="Something feels different between us.",
        recognized_territory="human relationships",
        processing_purpose="open relational exploration",
        guide_context={"conversation": ""},
        safety_state="green",
    )

    calls = {"count": 0}

    def fake_urlopen(request, timeout):
        calls["count"] += 1
        if calls["count"] == 1:
            body = json.dumps(
                {"ok": False, "retryable": True, "error": "transient composition failure"}
            ).encode("utf-8")
            raise urllib.error.HTTPError(
                request.full_url,
                503,
                "Service Unavailable",
                {},
                __import__("io").BytesIO(body),
            )
        return _Response(
            200,
            {
                "ok": True,
                "response": "There is something worth noticing in what is happening between you.",
                "clarity": "relational pattern",
                "movement_state": "explore",
                "resources": [],
            },
        )

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        result = adapter.process(context)

    assert calls["count"] == 2
    assert result["status"] == "CONTRIBUTION"
    assert result["human_response"].startswith("There is something worth noticing")
    assert result["voice_policy"] == "preserve_specialist_voice"













def test_hrn_voice_repair_contract_is_applied_at_provider_boundary():
    messages = [
        {"role": "system", "content": "Repair the response prose."},
        {"role": "user", "content": "Failed draft."},
    ]
    contracted = provider_bank._apply_hrn_voice_repair_contract(messages)
    assert "ordinary, concrete language" in contracted[0]["content"]
    assert "Avoid metaphors and abstract relationship theory." in contracted[0]["content"]
    assert "Do not add a question" in contracted[0]["content"]
    assert contracted[1]["content"] == "Failed draft."



def test_hrn_plain_language_contract_is_applied_at_provider_boundary():
    messages = [
        {"role": "system", "content": "Original HRN composition rules."},
        {"role": "user", "content": "Visitor's actual words."},
    ]
    contracted = provider_bank._apply_hrn_visitor_contract(messages)
    assert "plain, concrete, natural language" in contracted[0]["content"]
    assert "Do not advise, prescribe, coach" in contracted[0]["content"]
    assert contracted[0]["content"].index("Original HRN composition rules.") < contracted[0]["content"].index("plain, concrete, natural language")
    assert contracted[1]["content"] == "Visitor's actual words."










def test_hrn_rejects_abstract_causal_relationship_theory():
    parsed = {
        "response": "A relationship often reaches a limit because of unmet needs and mismatched expectations.",
        "question": "What matters most to you here?",
    }
    try:
        provider_bank._normalize_operation_result("hrn_relational", parsed)
    except ValueError as exc:
        assert "visitor-surface contract violation" in str(exc)
    else:
        raise AssertionError("abstract causal relationship theory must be rejected")



def test_hrn_rejects_unsupported_motive_attribution():
    parsed = {
        "response": "There is a difference between wanting to reach out and needing the other person to confirm your worth.",
        "question": "What matters most to you here?",
    }
    try:
        provider_bank._normalize_operation_result("hrn_relational", parsed)
    except ValueError as exc:
        assert "visitor-surface contract violation" in str(exc)
    else:
        raise AssertionError("unsupported motive attribution must be rejected")


def test_hrn_rejects_same_plane_formulaic_question():
    parsed = {
        "response": "You are unsure whether reaching out would help or pressure them.",
        "question": "What feels different when you hold those two sides together?",
    }
    try:
        provider_bank._normalize_operation_result("hrn_relational", parsed)
    except ValueError as exc:
        assert "question-surface contract violation" in str(exc)
    else:
        raise AssertionError("same-plane abstract question must be rejected")



def test_hrn_provider_gate_matches_prescriptive_policy():
    examples = [
        "You could reach out and ask whether they need space.",
        "Try to ask them directly what has changed.",
        "You need to talk to them about how you feel.",
        "I recommend you give them space for now.",
    ]
    for response in examples:
        parsed = {"response": response, "question": "What feels most uncertain here?"}
        try:
            provider_bank._normalize_operation_result("hrn_relational", parsed)
        except ValueError as exc:
            assert "visitor-surface contract violation" in str(exc)
        else:
            raise AssertionError("HRN prescriptive policy must reject: " + response)



def test_hrn_rejects_unsupported_intimacy_autonomy_inference():
    parsed = {
        "response": "The pull toward intimacy is now also felt as a threat to your autonomy, so the same emotional energy can be both a bridge and a boundary.",
        "question": "What matters most to you here?",
    }
    try:
        provider_bank._normalize_operation_result("hrn_relational", parsed)
    except ValueError as exc:
        assert "visitor-surface contract violation" in str(exc)
    else:
        raise AssertionError("unsupported intimacy/autonomy inference must be rejected")


def test_hrn_rejects_formulaic_abstract_followup_question():
    parsed = {
        "response": "You are unsure whether reaching out would help or pressure them.",
        "question": "What becomes visible when you notice the effort beneath the thing you are trying to do?",
    }
    try:
        provider_bank._normalize_operation_result("hrn_relational", parsed)
    except ValueError as exc:
        assert "question-surface contract violation" in str(exc)
    else:
        raise AssertionError("formulaic abstract question must be rejected")



def test_hrn_composition_rejects_formulaic_connective_and_inferred_state():
    parsed = {
        "response": "If you view your potential outreach as an intrusion, you are operating from a place of guilt. This distinction matters because it shifts the focus from managing your own anxiety about being unwanted to extending a hand without demands.",
        "question": "What matters to you?",
    }
    try:
        provider_bank._normalize_operation_result("hrn_relational", parsed)
    except ValueError as exc:
        assert "visitor-surface contract violation" in str(exc)
    else:
        raise AssertionError("formulaic connective and inferred-state language must be rejected")



def test_reflective_followup_is_not_misclassified_as_advice():
    reflective = {
        "response": "The distance is real, but its meaning is still unclear.",
        "question": "What feels different when you consider that?",
    }
    normalized = provider_bank._normalize_operation_result("hrn_relational", reflective)
    assert normalized["question"] == "What feels different when you consider that?"

    prescriptive = {
        "response": "You should consider reaching out.",
        "question": "What matters here?",
    }
    try:
        provider_bank._normalize_operation_result("hrn_relational", prescriptive)
    except ValueError as exc:
        assert "visitor-surface contract violation" in str(exc)
    else:
        raise AssertionError("explicit advice must still be rejected")


def test_hrn_provider_gate_matches_frozen_humanity_templates():
    for response in (
        "It sounds like the distance has changed what you expect from each other.",
        "You should reach out when you feel ready.",
        "It is important for you to set clear boundaries.",
    ):
        parsed = {"response": response, "question": "What matters here?"}
        try:
            provider_bank._normalize_operation_result("hrn_relational", parsed)
        except ValueError as exc:
            assert "visitor-surface contract violation" in str(exc)
        else:
            raise AssertionError("frozen HRN humanity-gate patterns must be rejected upstream")



def test_hrn_composition_rejects_abstract_indirect_advice():
    parsed = {
        "response": "Seeing that shift as a change in interpretation rather than intent lets you pause before reacting and opens the possibility of choosing a stance that feels more grounded.",
        "question": "What matters to you?",
    }
    try:
        provider_bank._normalize_operation_result("hrn_relational", parsed)
    except ValueError as exc:
        assert "visitor-surface contract violation" in str(exc)
    else:
        raise AssertionError("abstract indirect advice must be rejected")



def test_hrn_composition_rejects_action_guidance():
    parsed = {
        "response": "Seeing these as two separate steps matters because it allows you to stabilize your own position before engaging with the other party.",
        "question": "What matters to you?",
    }
    try:
        provider_bank._normalize_operation_result("hrn_relational", parsed)
    except ValueError as exc:
        assert "visitor-surface contract violation" in str(exc)
    else:
        raise AssertionError("action-guidance language must be rejected")



def test_hrn_composition_rejects_abstract_generalizations():
    parsed = {
        "response": "In many relational dynamics, space is a necessary condition for connection to re-emerge with clarity.",
        "question": "What matters to you?",
    }
    try:
        provider_bank._normalize_operation_result("hrn_relational", parsed)
    except ValueError as exc:
        assert "visitor-surface contract violation" in str(exc)
    else:
        raise AssertionError("abstract relationship generalizations must be rejected")



def test_hrn_composition_rejects_advice_shaped_language():
    parsed = {
        "response": "This opens the possibility of setting clear, flexible boundaries that feel caring.",
        "question": "What matters most to you here?",
    }
    try:
        provider_bank._normalize_operation_result("hrn_relational", parsed)
    except ValueError as exc:
        assert "visitor-surface contract violation" in str(exc)
    else:
        raise AssertionError("advice-shaped HRN language must be rejected")


def test_openrouter_does_not_send_response_format_and_rejects_empty_transport():
    with patch.object(
        provider_bank,
        "_http_json",
        side_effect=json.JSONDecodeError("Expecting value", "", 0),
    ) as request:
        try:
            provider_bank._openai_compatible(
                "https://openrouter.ai/api/v1",
                "test-key",
                "openrouter",
                "openrouter/free",
                [{"role": "system", "content": "Return one JSON object."}],
                500,
            )
        except provider_bank.ProviderCallError as exc:
            assert exc.category == "invalid_provider_response"
        else:
            raise AssertionError("empty OpenRouter transport response must be rejected")
    assert len(request.call_args_list) == 1
    assert "response_format" not in request.call_args_list[0].args[2]


def test_openrouter_rejects_empty_message_content_without_response_format():
    empty = {"choices": [{"message": {"content": ""}}]}
    with patch.object(provider_bank, "_http_json", return_value=empty) as request:
        try:
            provider_bank._openai_compatible(
                "https://openrouter.ai/api/v1",
                "test-key",
                "openrouter",
                "openrouter/free",
                [{"role": "system", "content": "Return one JSON object."}],
                500,
            )
        except provider_bank.ProviderCallError as exc:
            assert exc.category == "invalid_provider_response"
        else:
            raise AssertionError("empty OpenRouter message must be rejected")
    assert "response_format" not in request.call_args_list[0].args[2]


def test_openrouter_free_model_cascade_is_registered_for_contract_validation():
    configured = provider_bank.MODEL_CAPABILITIES
    for model in (
        "openrouter/free",
        "nvidia/nemotron-3-ultra-550b-a55b:free",
        "google/gemma-4-31b-it:free",
    ):
        capabilities = configured[("openrouter", model)]
        assert "composition" in capabilities
        assert "relational_analysis" in capabilities
        assert "json_object" in capabilities


def test_main_version_header_matches_release_identity():
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    assert source.startswith("# USE PRODUCTION VERSION: v489.70 —")
    assert 'APP_VERSION = "v489.70"' in source



def test_hrn_composition_rejects_internal_process_language():
    parsed = {
        "response": "The brief identifies a tension, but it lacks specific facts of the relationship.",
        "question": "What feels important here?",
    }
    try:
        provider_bank._normalize_operation_result("hrn_relational", parsed)
    except ValueError as exc:
        assert "visitor-surface contract violation" in str(exc)
    else:
        raise AssertionError("internal-process language must not reach HRN visitors")

    natural = {
        "response": "You are weighing your care for them against the wish not to intrude.",
        "question": "What does that tension mean to you?",
    }
    normalized = provider_bank._normalize_operation_result("hrn_relational", natural)
    assert normalized["response"].startswith("You are weighing")



def test_hrn_perception_has_enough_completion_budget_for_observer_json():
    assert provider_bank.OPERATION_TOKEN_FLOORS["hrn_perception"] >= 1600



def test_hrn_contract_trims_only_incomplete_trailing_sentence():
    parsed = {
        "response": "The first distinction is clear. The next sentence starts but does not finish",
        "question": "What stands out to you?",
    }
    normalized = provider_bank._normalize_operation_result("hrn_relational", parsed)
    assert normalized["response"] == "The first distinction is clear."
    assert normalized["response"].endswith(".")



def test_hrn_contract_recovery_falls_back_to_json_object_without_schema_capability():
    original = [{"role": "user", "content": "Someone I love has become distant."}]
    incomplete = json.dumps({
        "response": "This begins clearly but stops before the sentence is complete",
        "question": "What feels hardest?",
    })
    corrected = json.dumps({
        "response": "This is a complete and grounded observation.",
        "question": "What feels different when you consider that?",
    })
    pool = [{"provider": "groq", "model": "qwen-test", "index": 0}]

    with (
        patch.object(provider_bank, "select", return_value=pool),
        patch.object(provider_bank, "_call", side_effect=[incomplete, corrected]) as provider_call,
        patch.object(provider_bank, "_state", return_value={"state": "healthy"}),
        patch.object(provider_bank, "acquire_probe", return_value=True),
        patch.object(provider_bank, "_success"),
        patch.object(provider_bank, "_capabilities", return_value=frozenset({"json_object"})),
    ):
        result = provider_bank.route(
            use_core=None, messages=original, max_tokens=600,
            parse=json.loads, operation="hrn_relational",
        )

    assert result["parsed"]["response"].endswith(".")
    assert provider_call.call_count == 2
    assert provider_call.call_args_list[1].args[4] is None
    recovery_messages = provider_call.call_args_list[1].args[2]
    assert "complete response" in recovery_messages[-1]["content"]
    assert "end with sentence-final punctuation" in recovery_messages[-1]["content"]



def test_hrn_contract_rejects_truncated_response():
    incomplete = {
        "response": "This begins clearly but stops before the sentence is complete",
        "question": "What stands out to you?",
    }
    try:
        provider_bank._normalize_operation_result("hrn_relational", incomplete)
    except ValueError as exc:
        assert "complete response" in str(exc)
    else:
        raise AssertionError("incomplete HRN response should be rejected")

    complete = {
        "response": "This is a complete observation. The thought has landed.",
        "question": "What stands out to you?",
    }
    normalized = provider_bank._normalize_operation_result("hrn_relational", complete)
    assert normalized["response"].endswith(".")



def test_json_object_instruction_is_added_at_provider_boundary():
    messages = [{"role": "user", "content": "Explain the situation plainly."}]
    effective = provider_bank._ensure_json_object_instruction(messages, None)
    assert effective[0]["role"] == "system"
    assert "json object" in effective[0]["content"].casefold()
    assert messages == [{"role": "user", "content": "Explain the situation plainly."}]

    text_messages = [{"role": "user", "content": "Write a short sentence."}]
    assert provider_bank._ensure_json_object_instruction(
        text_messages, {"mode": "text"}
    ) is text_messages

    existing = [{"role": "system", "content": "Return valid JSON."}]
    assert provider_bank._ensure_json_object_instruction(existing, None) is existing



def test_hrn_contract_recovery_corrects_rejected_provider_output():
    original = [{"role": "user", "content": "Someone I love has become distant."}]
    rejected = json.dumps({"question": "What feels hardest?", "rest": False})
    corrected = json.dumps({
        "response": "You are trying to respect their space without letting the distance speak for you.",
        "question": "What makes reaching out feel risky right now?",
    })
    pool = [{"provider": "groq", "model": "test-model", "index": 0}]

    with (
        patch.object(provider_bank, "select", return_value=pool),
        patch.object(provider_bank, "_call", side_effect=[rejected, corrected]) as provider_call,
        patch.object(provider_bank, "_state", return_value={"state": "healthy"}),
        patch.object(provider_bank, "acquire_probe", return_value=True),
        patch.object(provider_bank, "_success"),
        patch.object(provider_bank, "_capabilities", return_value=frozenset({"json_schema_best_effort"})),
    ):
        result = provider_bank.route(
            use_core=None,
            messages=original,
            max_tokens=600,
            parse=json.loads,
            operation="hrn_relational",
        )

    assert result["parsed"]["response"] == (
        "You are trying to respect their space without letting the distance speak for you."
    )
    assert result["parsed"]["question"] == "What makes reaching out feel risky right now?"
    assert provider_call.call_count == 2
    recovery_messages = provider_call.call_args_list[1].args[2]
    assert any(message.get("role") == "user" and message.get("content") == original[0]["content"] for message in recovery_messages)
    assert recovery_messages[-2] == {"role": "assistant", "content": rejected}
    assert "requires response" in recovery_messages[-1]["content"]
    assert "Correct the output now." in recovery_messages[-1]["content"]
    assert original == [{"role": "user", "content": "Someone I love has become distant."}]


def test_current_main_contains_domain_payload_consumption_guards():
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    assert 'APP_VERSION = "v489.70"' in source
    assert "domain_payload = dict(hub_contribution.payload or {})" in source
    assert "interpretation_data = dict(domain_payload.get(\"interpretation\") or {})" in source
    assert "domain_payload = dict(contribution.get(\"payload\") or {})" in source
    assert "interpretation = dict(domain_payload.get(\"interpretation\") or {})" in source
    provider_bank_source = (ROOT / "provider_bank.py").read_text(encoding="utf-8")
    assert "raw_output = _call(use_core, item, effective_messages, effective_max_tokens, effective_schema)" in provider_bank_source
    assert "recovery_messages.append({" in provider_bank_source
    assert "Correct the output now." in provider_bank_source


def test_model_scoped_daily_tpd_does_not_quarantine_provider_siblings():
    model = "openai/gpt-oss-20b"
    sibling = "openai/gpt-oss-120b"
    states = {
        "groq:" + model: {"state": "healthy", "category": None, "quarantine_until": 0.0},
        "groq:" + sibling: {"state": "healthy", "category": None, "quarantine_until": 0.0},
    }

    def get_state(provider, selected_model):
        return states.setdefault(
            provider + ":" + selected_model,
            {"state": "healthy", "category": None, "quarantine_until": 0.0},
        )

    def record_failure(state, category, text, retry_after=None):
        state["state"] = "open"
        state["category"] = category
        return retry_after or 60.0

    message = (
        "Rate limit reached for model `openai/gpt-oss-20b` in organization `org` "
        "on tokens per day (TPD): Limit 200000, Used 198653, Requested 2295. "
        "Please try again in 6m49.536s."
    )
    error = provider_bank.ProviderCallError(
        message, "groq", model, 429, None, "http_error"
    )
    with (
        patch.object(provider_bank, "_STATE", {"models": states, "provider_cursor": 0, "model_cursors": {}}),
        patch.object(provider_bank, "_state", side_effect=get_state),
        patch.object(provider_bank, "record_failure", side_effect=record_failure),
        patch("builtins.print") as printed,
    ):
        provider_bank._failure(error, "groq", model)

    assert states["groq:" + model]["category"] == "rate_limited"
    assert states["groq:" + sibling]["state"] == "healthy"
    assert states["groq:" + sibling]["category"] is None
    assert any(
        "category=rate_limited" in str(call.args[0]) and "provider_wide=false" in str(call.args[0])
        for call in printed.call_args_list
    )


def test_account_wide_quota_still_quarantines_provider_siblings():
    model = "openai/gpt-oss-20b"
    sibling = "openai/gpt-oss-120b"
    states = {
        "groq:" + model: {"state": "healthy", "category": None, "quarantine_until": 0.0},
        "groq:" + sibling: {"state": "healthy", "category": None, "quarantine_until": 0.0},
    }

    def get_state(provider, selected_model):
        return states.setdefault(
            provider + ":" + selected_model,
            {"state": "healthy", "category": None, "quarantine_until": 0.0},
        )

    def record_failure(state, category, text, retry_after=None):
        state["state"] = "open"
        state["category"] = category
        return retry_after or 1800.0

    error = provider_bank.ProviderCallError(
        "You exceeded your current quota; please check your plan and billing details.",
        "groq", model, 429, None, "http_error"
    )
    with (
        patch.object(provider_bank, "_STATE", {"models": states, "provider_cursor": 0, "model_cursors": {}}),
        patch.object(provider_bank, "_state", side_effect=get_state),
        patch.object(provider_bank, "record_failure", side_effect=record_failure),
        patch("builtins.print") as printed,
    ):
        provider_bank._failure(error, "groq", model)

    assert states["groq:" + model]["category"] == "quota_or_billing"
    assert states["groq:" + sibling]["state"] == "open"
    assert states["groq:" + sibling]["category"] == "quota_or_billing"
    assert any(
        "category=quota_or_billing" in str(call.args[0]) and "provider_wide=true" in str(call.args[0])
        for call in printed.call_args_list
    )


if __name__ == "__main__":
    test_domain_payload_survives_common_pipe()
    test_relationship_adapter_retries_transient_503()
    test_hrn_contract_recovery_corrects_rejected_provider_output()
    test_json_object_instruction_is_added_at_provider_boundary()
    test_hrn_contract_rejects_truncated_response()
    test_hrn_contract_recovery_falls_back_to_json_object_without_schema_capability()
    test_hrn_contract_trims_only_incomplete_trailing_sentence()
    test_hrn_perception_has_enough_completion_budget_for_observer_json()
    test_hrn_composition_rejects_internal_process_language()
    test_hrn_composition_rejects_advice_shaped_language()
    test_hrn_voice_repair_contract_is_applied_at_provider_boundary()
    test_hrn_plain_language_contract_is_applied_at_provider_boundary()
    test_hrn_composition_rejects_abstract_generalizations()
    test_hrn_composition_rejects_action_guidance()
    test_hrn_composition_rejects_abstract_indirect_advice()
    test_reflective_followup_is_not_misclassified_as_advice()
    test_hrn_provider_gate_matches_frozen_humanity_templates()
    test_hrn_rejects_abstract_causal_relationship_theory()
    test_hrn_rejects_unsupported_motive_attribution()
    test_hrn_rejects_same_plane_formulaic_question()
    test_hrn_provider_gate_matches_prescriptive_policy()
    test_hrn_rejects_unsupported_intimacy_autonomy_inference()
    test_hrn_rejects_formulaic_abstract_followup_question()
    test_hrn_composition_rejects_formulaic_connective_and_inferred_state()
    test_main_version_header_matches_release_identity()
    test_current_main_contains_domain_payload_consumption_guards()
    test_model_scoped_daily_tpd_does_not_quarantine_provider_siblings()
    test_account_wide_quota_still_quarantines_provider_siblings()
    print("current specialist-pipe regression probes: PASS")
