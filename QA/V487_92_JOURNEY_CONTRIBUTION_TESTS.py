from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import _build_journey_contribution_for_use
from shared_intelligence_primitives import JourneyContribution

def main():
    contribution = _build_journey_contribution_for_use({
        "original_question": "<b>Why am I angry?</b>",
        "conversation": "<p>We explored the pattern.</p>",
        "thread_summary": "A changing view of the tension.",
        "working_hypothesis": "The anger may be carrying a boundary signal.",
        "completed_insight": "I noticed the anger changes when I feel unheard.",
        "perspective_delta": "I can see the interaction differently now.",
        "body_of_thought": "The living thread became more specific.",
        "underlying_need": "To understand what matters beneath the reaction.",
        "desired_condition": "More clarity before deciding.",
        "next_horizon": "Carry the perspective into the relationship.",
        "resource_fit": "A doorway may extend this reflection.",
        "journey_synthesis": "The whole journey clarified the pattern.",
        "journey_action": "END",
        "journey_ledger": {"state": "complete", "segments": 2},
        "fractal_records": [{"summary": "first"}],
        "round_synthesis_history": [{"round": 1, "text": "opening"}],
    })
    assert isinstance(contribution, JourneyContribution)
    assert contribution.original_question == "Why am I angry?"
    assert contribution.conversation == "We explored the pattern."
    assert contribution.journey_action == "end"
    assert contribution.journey_ledger == {"state": "complete", "segments": 2}
    assert len(contribution.fractal_records) == 1
    assert len(contribution.round_synthesis_history) == 1
    assert _build_journey_contribution_for_use({}).conversation == ""
    print("v487.92 journey contribution compatibility probes: PASS")

if __name__ == "__main__":
    main()
