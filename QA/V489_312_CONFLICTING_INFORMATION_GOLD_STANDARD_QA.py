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
    print("CONFLICTING INFORMATION GOLD STANDARD CALIBRATION: PASS")

if __name__ == "__main__":
    main()
