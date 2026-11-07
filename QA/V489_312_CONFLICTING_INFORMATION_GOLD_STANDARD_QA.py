"""Gold Standard calibration for conflicting-information overload recognition."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import general_guide_composition as composition

QUERY = (
    "I feel overwhelmed by conflicting information and opinions. "
    "How can I regain my bearings and know what is real enough to act on?"
)

def main():
    prompt = composition._GENERAL_GUIDE_SYSTEM
    required = (
        "treat the task first as epistemic orientation",
        "competing claims make it hard to judge what deserves trust",
        "directly known or independently verified",
        "interpretation/inference",
        "independent corroboration",
        "action threshold proportionate to the stakes",
        "must be rejected",
    )
    for phrase in required:
        assert phrase in prompt, f"Missing recognition calibration: {phrase}"

    assert composition._requires_three_paragraph_default(QUERY) is True
    assert composition._requires_conflicting_information_discernment(QUERY) is True

    # The observed visitor answer is fluent and three paragraphs, but opens
    # with governance/action planning and never establishes epistemic bearings.
    observed = (
        "A practical way to approach this is to begin by clarifying the outcome and the responsibilities involved. "
        "Identify what is known, which constraints or obligations matter, and who will be affected by the available choices. "
        "This makes the real decision clearer than jumping immediately to a generic action plan.\n\n"
        "Next, compare a small number of realistic options against the purpose you are trying to serve. "
        "Consider likely benefits, foreseeable harms, who carries the costs, and what evidence would change the choice. "
        "Where other people are affected, include their knowledge and concerns rather than treating them as an afterthought.\n\n"
        "Finally, act on the best-supported option, explain the reasoning and limits, and review the consequences. "
        "A useful approach should improve understanding and accountability, not promise certainty."
    )
    assert not composition._has_conflicting_information_discernment(observed)

    recovery = composition._conflicting_information_discernment_recovery()
    assert composition._has_conflicting_information_discernment(recovery)
    assert "what deserves trust" in recovery
    assert "independently verified" in recovery

    # Positive control: equivalent language, not just the exact recovery wording.
    equivalent_good_answer = (
        "When accounts contradict one another, the hard part is deciding which account is dependable; "
        "the answer is not simply to gather more information. Begin by asking what is actually established "
        "and why any source merits confidence.\n\n"
        "Separate observations and independently confirmed facts from interpretations, predictions, and "
        "assumptions that have not been tested. Compare the original evidence, check whether genuinely "
        "independent sources corroborate it, and identify what finding would cause you to revise your view.\n\n"
        "Set the threshold by the consequences of the decision. For a low-stakes choice that can be reversed, "
        "the strongest available evidence may be enough to act cautiously; where the consequences are serious "
        "or difficult to undo, require stronger support and make the remaining uncertainty explicit."
    )
    assert composition._has_conflicting_information_discernment(equivalent_good_answer)

    # Negative controls: keywords elsewhere cannot compensate for a failure
    # to recognize the visitor's trust problem in the opening paragraph.
    late_recognition = (
        "Start with the outcome, stakeholders, and an action plan. Decide who is responsible "
        "and compare the available options.\n\n"
        "Later, distinguish what is known from assumptions, review sources and evidence, "
        "and ask what would change your mind.\n\n"
        "Set an action threshold proportionate to the stakes and prefer reversible decisions. "
        "Conflicting claims can make trust difficult; the issue is not simply more information."
    )
    assert not composition._has_conflicting_information_discernment(late_recognition)

    # Query classification controls: catch a close paraphrase and avoid
    # triggering on a generic question about conflicting information alone.
    paraphrased_query = (
        "I am lost among competing claims and sources. How do I know which ones "
        "are trustworthy and what I can safely rely on?"
    )
    assert composition._requires_conflicting_information_discernment(paraphrased_query)
    assert not composition._requires_conflicting_information_discernment(
        "What are the main differences between two competing theories?"
    )


    # Provider-health isolation: an editorial rejection increments only the
    # operation/model quality state and does not mark transport health failed.
    import copy
    import provider_bank
    original_state = copy.deepcopy(provider_bank._STATE)
    original_persist = provider_bank._persist_shared_state
    try:
        provider_bank._persist_shared_state = lambda: None
        provider_bank._STATE = {"models": {}, "quality": {}}
        provider_bank._record_quality_rejection(
            "qa_provider", "qa_model", "general_guide_composition",
            "conflicting-information answer must recognize the trust problem first",
        )
        quality = provider_bank._quality_state(
            "general_guide_composition", "qa_provider", "qa_model"
        )
        health = provider_bank._state("qa_provider", "qa_model")
        assert quality["quality_failures"] == 1
        assert quality["quality_error"] == "contract_rejection"
        assert quality["quality_cooldown_until"] > 0
        assert health.get("state") == "healthy"
        assert int(health.get("failures", 0) or 0) == 0
    finally:
        provider_bank._STATE = original_state
        provider_bank._persist_shared_state = original_persist


    # Exercise the real Provider Bank route loop without network calls. The
    # first candidate is rejected by the Guide contract; the next candidate
    # must be attempted. A second run rejects all three bounded candidates.
    original_bank_state = copy.deepcopy(provider_bank._STATE)
    patched = {}
    def patch(name, value):
        patched[name] = getattr(provider_bank, name)
        setattr(provider_bank, name, value)
    try:
        provider_bank._STATE = {"models": {}, "quality": {}}
        patch("_persist_shared_state", lambda: None)
        patch("_sync_shared_state", lambda *args, **kwargs: None)
        patch("select", lambda *args, **kwargs: [
            {"provider": "qa_a", "model": "m1", "health_state": "healthy"},
            {"provider": "qa_b", "model": "m2", "health_state": "healthy"},
            {"provider": "qa_c", "model": "m3", "health_state": "healthy"},
        ])
        patch("_blocked_for_operation", lambda *args, **kwargs: False)
        patch("_provider_call_timeout", lambda *args, **kwargs: 3.0)
        patch("_predictive_shadow_metrics", lambda *args, **kwargs: {
            "ewma_latency_seconds": 0.1, "timeout_risk": 0.0, "deadline_fit": True
        })
        patch("_record_predictive_shadow", lambda *args, **kwargs: None)
        patch("_quota_guarded_call", lambda use_core, item, *args, **kwargs: item["model"])
        patch("_success", lambda *args, **kwargs: None)

        attempted = []
        def reject_then_accept(raw):
            attempted.append(raw)
            if raw == "m1":
                raise ValueError(
                    "conflicting-information answer must recognize the trust problem first"
                )
            return {"response": "accepted"}

        routed = provider_bank.route(
            use_core={}, messages=[{"role": "user", "content": QUERY}],
            max_tokens=300, parse=reject_then_accept,
            operation="general_guide_composition",
        )
        assert len(attempted) == 2, f"Expected primary rejection then fallback success, got {attempted}"
        assert routed is not None, "Fallback candidate did not return a result"
        rejected_quality = provider_bank._quality_state(
            "general_guide_composition", "qa_a", "m1"
        )
        rejected_health = provider_bank._state("qa_a", "m1")
        assert rejected_quality.get("quality_error") == "contract_rejection"
        assert rejected_quality.get("quality_failures") == 1
        assert rejected_health.get("state") == "healthy"
        assert int(rejected_health.get("failures", 0) or 0) == 0

        provider_bank._STATE = {"models": {}, "quality": {}}
        exhausted_attempts = []
        def reject_every_candidate(raw):
            exhausted_attempts.append(raw)
            raise ValueError(
                "conflicting-information answer must recognize the trust problem first"
            )

        exhausted = provider_bank.route(
            use_core={}, messages=[{"role": "user", "content": QUERY}],
            max_tokens=300, parse=reject_every_candidate,
            operation="general_guide_composition",
        )
        assert exhausted is None, "Exhausted quality-rejected candidates should return no route result"
        assert len(exhausted_attempts) == 3, (
            "Expected one primary plus two bounded fallback attempts; "
            f"got {exhausted_attempts}"
        )
        for provider, model in (("qa_a", "m1"), ("qa_b", "m2"), ("qa_c", "m3")):
            health = provider_bank._state(provider, model)
            quality = provider_bank._quality_state(
                "general_guide_composition", provider, model
            )
            assert health.get("state") == "healthy"
            assert int(health.get("failures", 0) or 0) == 0
            assert quality.get("quality_error") == "contract_rejection"
    finally:
        provider_bank._STATE = original_bank_state
        for name, value in patched.items():
            setattr(provider_bank, name, value)

    print("CONFLICTING INFORMATION GOLD STANDARD CALIBRATION: PASS")

if __name__ == "__main__":
    main()
