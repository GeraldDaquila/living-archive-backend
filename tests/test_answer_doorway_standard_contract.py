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

    fsd = read("integrations/wordpress/living-archive-fsd-proxy/assets/fsd-app.js")
    hrn = read("plugins/human-relational-navigator/assets/relational-navigator.js")
    spe = read("wordpress/spe/03-JavaScript.js")
    guide = read("wordpress/guide/woody-snippet-76926-universal.html")
    fsd_contract = read("fsd_episode_report_contract.py")

    assert "doorwayHelper.renderMany" in fsd
    assert 'ref.role==="conceptual_context_only"' in fsd
    assert "window.LivingArchiveAnswerDoorway.render(wrap" in hrn
    assert "helper.renderMany(d,items)!==3" in spe
    assert "helper.normalizeUrl(x.url)" in spe
    assert "innerHTML" not in spe
    assert "LivingArchiveAnswerDoorway.render(recommendation" in guide
    assert "link.href=doorway.url" not in guide
    assert "recommendation.replaceChildren()" in guide
    assert "is_canonical_archive_url" in fsd_contract
    assert "parsed.username is None" in fsd_contract
    assert "not parsed.query" in fsd_contract
    print("ANSWER + DOORWAY STANDARD CONTRACT: PASS")

if __name__ == "__main__":
    main()
