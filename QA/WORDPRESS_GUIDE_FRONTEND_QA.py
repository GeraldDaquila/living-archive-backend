"""Static release gate for the repository-owned Guide HTML and JS sources."""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "wordpress" / "the-guide-frontend.html"
JS_PATH = ROOT / "wordpress" / "the-guide-frontend.js"
HTML = HTML_PATH.read_text(encoding="utf-8")
JS = JS_PATH.read_text(encoding="utf-8")


def main() -> None:
    build_match = re.search(r"var USE_FRONTEND_BUILD = '([^']+)'", JS)
    assert build_match, "Guide JavaScript build marker is missing."
    build = build_match.group(1)
    assert re.fullmatch(r"v[0-9]+\.[0-9]+", build), "Guide build marker is malformed."

    assert f"living-archive-guide-{build}.js" in HTML, (
        "Guide HTML does not load the matching external JavaScript asset."
    )
    assert 'data-no-optimize="1" data-no-defer="1"' in HTML, (
        "External Guide controller must be excluded from optimizer/defer rewriting."
    )
    assert "function installGuideSubmitController(" not in HTML, (
        "JavaScript must not be embedded in WordPress page content."
    )
    assert "&#038;" not in JS, "Source JS must not contain HTML-escaped operators."

    assert JS.count("function installGuideSubmitController(") == 1, (
        "Guide must have exactly one submission controller definition."
    )
    assert len(re.findall(
        r"document\.addEventListener\(\s*'submit'",
        JS,
    )) == 1, "Guide must have exactly one document-level submit listener."
    assert not re.search(
        r"form\.addEventListener\(\s*'submit'",
        JS,
    ), "Competing form-level submit listener detected."
    assert not re.search(
        r"function installGuide(?:Frontend|DelegatedSubmit)Controller\(",
        JS,
    ), "Legacy competing submission controller detected."
    assert JS.count("installGuideSubmitController();") == 1, (
        "Guide submission controller must be installed exactly once."
    )

    assert JS.count("function renderAuthoritativeRecommendation(data)") == 1, (
        "Authoritative recommendation renderer is missing or duplicated."
    )
    assert len(re.findall(
        r"^\s*renderAuthoritativeRecommendation\(data\);\s*$",
        JS,
        re.MULTILINE,
    )) == 1, "Ordinary response must invoke the recommendation renderer exactly once."
    assert "responseText.appendChild(block);" in JS, (
        "Recommendation must be rendered in the visible response surface."
    )
    assert r"geralddaquila\.com" in JS, (
        "Canonical recommendation URL validation is missing."
    )
    assert ".archive-inline-recommendation" in JS, (
        "Inline recommendation presentation is missing."
    )
    assert "There may be something worth staying with here" not in JS, (
        "Manufactured generic visitor-facing fallback detected."
    )

    print(f"Guide frontend structural QA: PASS ({build})")
    print("external_javascript_asset=true")
    print("submission_owners=1")
    print("authoritative_recommendation_renderers=1")


if __name__ == "__main__":
    main()
