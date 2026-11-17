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
    assert "GENERIC_RATIONALES.indexOf(rationale.toLowerCase())" in js
    assert "textContent" in js
    assert "innerHTML" not in js
    assert "CONTINUE EXPLORING" in js
    assert ".la-answer-doorway" in css and "#f7f5ef" in css
    for module in ("The Guide / USE", "HRN", "FSD", "SPE", "Public Living Archive Navigator", "Mini-USE"):
        assert module in spec
    assert "do not corroborate" in spec
    assert "three selected canonical destinations" in spec

    fsd = read("integrations/wordpress/living-archive-fsd-proxy/assets/fsd-app.js")
    hrn = read("plugins/human-relational-navigator/assets/relational-navigator.js")
    spe = read("wordpress/spe/03-JavaScript.js")
    spe_php = read("wordpress/spe/stewardship-pathway-engine.php")
    lan_php = read("wordpress/public-living-archive-navigator/living-archive-navigator.php")
    mini_api = read("wordpress/mini-use/class-api.php")
    guide = read("wordpress/guide/woody-snippet-76926-universal.html")
    guide_controller = read("wordpress/living-archive-guide-v489.324-answer-doorway-standard.js")
    lan = read("wordpress/public-living-archive-navigator/03-JavaScript.js")
    mini = read("wordpress/mini-use/mini-use.js")
    fsd_contract = read("fsd_episode_report_contract.py")

    assert "doorwayHelper.renderMany" in fsd
    assert 'ref.role==="conceptual_context_only"' in fsd
    assert 'rationale:ref.rationale' in fsd
    assert "window.LivingArchiveAnswerDoorway.render(wrap" in hrn
    assert "const rendered=helper.renderMany(d,items)" in spe
    assert "if(rendered!==3)d.replaceChildren()" in spe
    assert "helper.normalizeUrl(x.url)" in spe
    assert "innerHTML" not in spe
    assert "la-answer-doorway-standard" in spe_php
    assert "la-answer-doorway-standard" in lan_php
    assert "la-answer-doorway-standard" in mini_api
    assert "helper.renderMany(d,items)" in lan
    assert "innerHTML" not in lan
    assert "helper.renderMany(doorContainer, items)" in mini
    assert "innerHTML" not in mini
    assert "LivingArchiveAnswerDoorway.render(recommendation" in guide
    assert "link.href=doorway.url" not in guide
    assert "recommendation.replaceChildren()" in guide
    assert "var primaryDoorway=text.querySelector" in guide
    assert "primary.remove()" in guide
    assert "guide-controller-v489.324.js" in guide
    assert "helper.normalize(recommendation)" in guide_controller
    assert "helper.render(staging, normalized)" in guide_controller
    assert "link.href = url" not in guide_controller
    assert "sanitizeMarkdown(renderedAnswer)" in guide_controller
    assert "sanitizeMarkdown(html)" in guide
    assert "text.innerHTML=renderAnswer(answer)" not in guide
    assert "is_canonical_archive_url" in fsd_contract
    assert "parsed.username is None" in fsd_contract
    assert "not parsed.query" in fsd_contract
    print("ANSWER + DOORWAY STANDARD CONTRACT: PASS")

if __name__ == "__main__":
    main()
