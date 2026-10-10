"""Behavioral regression test for adaptive HRN provider-lane arbitration."""
import os
import provider_bank


def main():
    old_order = os.environ.get("USE_LLM_PROVIDER_ORDER")
    os.environ["USE_LLM_PROVIDER_ORDER"] = "groq,workers_ai,nvidia"
    original_candidates = provider_bank.candidates
    try:
        provider_bank.candidates = lambda use_core, operation="generic", schema=None: [
            {"provider": "groq", "model": "gpt-oss", "health_state": "degraded",
             "quality_failures": 0, "consecutive_failures": 3, "transport_failures": 2,
             "last_success": 0.0, "capabilities": []},
            {"provider": "workers_ai", "model": "glm", "health_state": "healthy",
             "quality_failures": 0, "consecutive_failures": 0, "transport_failures": 0,
             "last_success": 100.0, "capabilities": []},
            {"provider": "nvidia", "model": "nemotron", "health_state": "healthy",
             "quality_failures": 0, "consecutive_failures": 0, "transport_failures": 0,
             "last_success": 90.0, "capabilities": []},
        ]
        provider_bank._STATE["provider_cursor"] = 0
        provider_bank._STATE["model_cursors"] = {}
        selected = provider_bank.select(None, operation="hrn_relational")
        providers = [item["provider"] for item in selected]
        assert providers[:3] == ["workers_ai", "nvidia", "groq"], (
            "HRN lane ranking failed to prefer healthy, recently successful providers; "
            f"received {providers}"
        )
        print("V489.84 HRN PROVIDER-LANE ARBITRATION TEST: PASS")
        print("health_and_recent_success_precede_stale_configured_priority=True")
    finally:
        provider_bank.candidates = original_candidates
        if old_order is None:
            os.environ.pop("USE_LLM_PROVIDER_ORDER", None)
        else:
            os.environ["USE_LLM_PROVIDER_ORDER"] = old_order


if __name__ == "__main__":
    main()
