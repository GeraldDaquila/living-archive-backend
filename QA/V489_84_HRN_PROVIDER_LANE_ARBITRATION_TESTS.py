"""Behavioral regression test for bounded HRN provider arbitration."""
import os
import provider_bank


def main():
    old_order = os.environ.get("USE_LLM_PROVIDER_ORDER")
    old_cap = os.environ.get("USE_HRN_PROVIDER_BANK_MAX_ATTEMPTS")
    os.environ["USE_LLM_PROVIDER_ORDER"] = "groq,workers_ai,nvidia"
    try:
        os.environ.pop("USE_HRN_PROVIDER_BANK_MAX_ATTEMPTS", None)
        assert provider_bank._hrn_attempt_cap() == 1
        os.environ["USE_HRN_PROVIDER_BANK_MAX_ATTEMPTS"] = "2"
        assert provider_bank._hrn_attempt_cap() == 2
        os.environ["USE_HRN_PROVIDER_BANK_MAX_ATTEMPTS"] = "99"
        assert provider_bank._hrn_attempt_cap() == 2
        os.environ["USE_HRN_PROVIDER_BANK_MAX_ATTEMPTS"] = "invalid"
        assert provider_bank._hrn_attempt_cap() == 1

        original_candidates = provider_bank.candidates
        try:
            provider_bank.candidates = lambda use_core, operation="generic", schema=None: [
                {"provider": "groq", "model": "gpt-oss", "health_state": "degraded",
                 "quality_failures": 0, "consecutive_failures": 3, "transport_failures": 2,
                 "last_success": 0.0, "capabilities": []},
                {"provider": "workers_ai", "model": "gemma-slow", "health_state": "healthy",
                 "quality_failures": 0, "consecutive_failures": 0, "transport_failures": 0,
                 "last_success": 100.0, "capabilities": ["composition"]},
                {"provider": "workers_ai", "model": "llama-fast", "health_state": "healthy",
                 "quality_failures": 0, "consecutive_failures": 0, "transport_failures": 0,
                 "last_success": 50.0, "capabilities": ["composition", "low_latency"]},
                {"provider": "nvidia", "model": "nemotron", "health_state": "healthy",
                 "quality_failures": 0, "consecutive_failures": 0, "transport_failures": 0,
                 "last_success": 90.0, "capabilities": ["composition"]},
            ]
            provider_bank._STATE["provider_cursor"] = 0
            provider_bank._STATE["model_cursors"] = {}
            selected = provider_bank.select(None, operation="hrn_relational")
            providers = [item["provider"] for item in selected]
            assert providers[:3] == ["workers_ai", "nvidia", "groq"], (
                "HRN lane ranking failed to prefer healthy providers; received " + str(providers)
            )
            assert selected[0]["model"] == "llama-fast", (
                "A low-latency eligible model must outrank a slower sibling inside the same healthy provider lane."
            )
            assert selected[3]["model"] == "gemma-slow", (
                "The slower sibling should remain available as the next candidate, not be removed."
            )
        finally:
            provider_bank.candidates = original_candidates
        print("V489.94 HRN PROVIDER BUDGET/ARBITRATION TEST: PASS")
        print("default_hrn_attempts=1; bounded_override=2; low_latency_preference=enabled")
    finally:
        if old_order is None:
            os.environ.pop("USE_LLM_PROVIDER_ORDER", None)
        else:
            os.environ["USE_LLM_PROVIDER_ORDER"] = old_order
        if old_cap is None:
            os.environ.pop("USE_HRN_PROVIDER_BANK_MAX_ATTEMPTS", None)
        else:
            os.environ["USE_HRN_PROVIDER_BANK_MAX_ATTEMPTS"] = old_cap


if __name__ == "__main__":
    main()
