import provider_bank


def test_retired_nemotron_3_super_model_aliases_to_3_5_super_vl():
    expected = "nvidia/nemotron-3.5-super-vl-120b-a12b"

    assert provider_bank.resolve_nvidia_model_id(
        "nvidia/nemotron-3-super-120b-a12b"
    ) == expected
    assert provider_bank.resolve_nvidia_model_id(
        "Nemotron 3 Super 120B A12B"
    ) == expected
    assert provider_bank.resolve_nvidia_model_id(
        "nvidia/nemotron-3.5-super-vl-120b-a12b"
    ) == expected


def test_nemotron_3_5_super_vl_is_eligible_for_general_guide_composition():
    capabilities = provider_bank._capabilities(
        "nvidia", "nvidia/nemotron-3.5-super-vl-120b-a12b"
    )

    assert {
        "json_object",
        "json_schema_best_effort",
        "text_generation",
        "reasoning",
        "long_context",
        "composition",
        "relational_analysis",
    }.issubset(capabilities)


def test_nemotron_3_5_super_vl_disables_separate_reasoning_channel_for_text_composition(monkeypatch):
    captured = {}

    def fake_http_json(url, headers, payload, provider, model, timeout=None):
        captured["payload"] = payload
        return {"choices": [{"message": {"content": '{"response":"ok"}'}}]}

    monkeypatch.setattr(provider_bank, "_http_json", fake_http_json)

    result = provider_bank._openai_compatible(
        "https://integrate.api.nvidia.com/v1",
        "test-key",
        "nvidia",
        "nvidia/nemotron-3.5-super-vl-120b-a12b",
        [{"role": "user", "content": "Respond with JSON."}],
        128,
        schema=None,
    )

    assert result == '{"response":"ok"}'
    assert captured["payload"]["chat_template_kwargs"] == {"enable_thinking": False}
