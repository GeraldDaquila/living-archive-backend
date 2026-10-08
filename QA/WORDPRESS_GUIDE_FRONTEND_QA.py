"""Static release gate for the repository-owned Guide frontend snapshot."""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "wordpress" / "the-guide-frontend.html"
SOURCE = SOURCE_PATH.read_text(encoding="utf-8")


def main() -> None:
    build_match = re.search(
        r"var USE_FRONTEND_BUILD = '([^']+)'",
        SOURCE,
    )
    assert build_match, "Guide frontend build marker is missing."
    build = build_match.group(1)
    assert re.fullmatch(r"v[0-9]+\.[0-9]+", build), "Guide frontend build marker is malformed."

    assert SOURCE.count("function installGuideSubmitController(") == 1, (
        "Guide must have exactly one submission controller definition."
    )
    assert len(re.findall(
        r"document\.addEventListener\(\s*'submit'",
        SOURCE,
    )) == 1, "Guide must have exactly one document-level submit listener."
    assert not re.search(
        r"form\.addEventListener\(\s*'submit'",
        SOURCE,
    ), "Competing form-level submit listener detected."
    assert not re.search(
        r"function installGuide(?:Frontend|DelegatedSubmit)Controller\(",
        SOURCE,
    ), "Legacy competing submission controller detected."
    assert SOURCE.count("installGuideSubmitController();") == 1, (
        "Guide submission controller must be installed exactly once."
    )

    assert SOURCE.count("function renderAuthoritativeRecommendation(data)") == 1, (
        "Authoritative recommendation renderer is missing or duplicated."
    )
    assert len(re.findall(
        r"^\s*renderAuthoritativeRecommendation\(data\);\s*$",
        SOURCE,
        re.MULTILINE,
    )) == 1, "Ordinary response must invoke the recommendation renderer exactly once."
    assert "responseText.appendChild(block);" in SOURCE, (
        "Recommendation must be rendered in the visible response surface."
    )
    assert r"geralddaquila\.com" in SOURCE, (
        "Canonical recommendation URL validation is missing."
    )
    assert ".archive-inline-recommendation" in SOURCE, (
        "Inline recommendation presentation is missing."
    )
    assert "There may be something worth staying with here" not in SOURCE, (
        "Manufactured generic visitor-facing fallback detected."
    )

    print(f"Guide frontend structural QA: PASS ({build})")
    print("submission_owners=1")
    print("authoritative_recommendation_renderers=1")


if __name__ == "__main__":
    main()
