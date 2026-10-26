"""Structural regression for Guide provider fallback after a bounded slow failure."""
from pathlib import Path


def main():
    source = Path(__file__).resolve().parents[1].joinpath("provider_bank.py").read_text(encoding="utf-8")
    # Guide composition has a shared request deadline and an 18-second provider
    # window. A slow first provider must proceed to the existing budget-aware
    # fallback gate instead of stopping the serial chain at 2.8 seconds.
    assert source.count('if operation == "hrn_perception":\n                candidate_elapsed = time.monotonic() - attempt_started\n                slow_failure_stop = HRN_PERCEPTION_SLOW_FAILURE_STOP_SECONDS') == 2
    assert 'if operation in {"hrn_perception", "general_guide_composition"}:\n                candidate_elapsed = time.monotonic() - attempt_started' not in source
    assert "GENERAL_GUIDE_FAST_FAILURE_WINDOW_SECONDS = 18.0" in source
    assert "GENERAL_GUIDE_FAST_FALLBACK_MAX_CANDIDATES = 2" in source
    print("GUIDE BUDGET-AWARE SLOW-FAILURE FALLBACK QA: PASS")


if __name__ == "__main__":
    main()
