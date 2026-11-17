"""Static integration guards for the shared visitor-facing doorway contract."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def read(path):
    return (ROOT.parent / path).read_text(encoding="utf-8")

def main():
    js = read("wordpress/living-archive-answer-doorway-standard/assets/answer-doorway.js")
    css = read("wordpress/living-archive-answer-doorway-standard/assets/answer-doorway.css")
    spec = read("docs/architecture/LIVING_ARCHIVE_ANSWER_DOORWAY_STANDARD.md")

    assert "https:" in js and "geralddaquila.com" in js
    assert "url.username" in js and "url.password" in js
    assert "url.search" in js and "url.hash" in js
    assert "title.length > 180" in js and "rationale.length > 600" in js
    assert "textContent" in js
    assert "innerHTML" not in js
    assert "CONTINUE EXPLORING" in js
    assert ".la-answer-doorway" in css and "#f7f5ef" in css
    for module in ("The Guide / USE", "HRN", "FSD", "SPE"):
        assert module in spec
    assert "do not corroborate" in spec
    assert "three selected canonical destinations" in spec
    print("ANSWER + DOORWAY STANDARD CONTRACT: PASS")

if __name__ == "__main__":
    main()
