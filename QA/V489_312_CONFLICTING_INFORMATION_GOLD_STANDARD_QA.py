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
        "the difficulty may not be a lack of information",
        "what deserves trust",
        "solid enough to act on",
        "separate what is known, what is inferred",
        "Do not use a generic empathy preamble",
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
        "This makes the real decision clearer than jumping immediately to a generic action plan.\\n\\n"
        "Next, compare a small number of realistic options against the purpose you are trying to serve. "
        "Consider likely benefits, foreseeable harms, who carries the costs, and what evidence would change the choice. "
        "Where other people are affected, include their knowledge and concerns rather than treating them as an afterthought.\\n\\n"
        "Finally, act on the best-supported option, explain the reasoning and limits, and review the consequences. "
        "A useful approach should improve understanding and accountability, not promise certainty."
    )
    assert not composition._has_conflicting_information_discernment(observed)

    recovery = composition._conflicting_information_discernment_recovery()
    assert composition._has_conflicting_information_discernment(recovery)
    assert "what deserves trust" in recovery
    assert "independently verified" in recovery
    print("CONFLICTING INFORMATION GOLD STANDARD CALIBRATION: PASS")

if __name__ == "__main__":
    main()
