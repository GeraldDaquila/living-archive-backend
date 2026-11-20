"""Release-gated responsive and completed-state contract for Answer + Doorway."""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parent
DOORWAY_CSS = (
    ROOT.parent / "wordpress/living-archive-answer-doorway-standard/assets/answer-doorway.css"
).read_text(encoding="utf-8")
GUIDE_SNIPPET = (
    ROOT.parent / "wordpress/guide/woody-snippet-76926-universal.html"
).read_text(encoding="utf-8")
PLUGIN_PHP = (
    ROOT.parent / "wordpress/living-archive-answer-doorway-standard/living-archive-answer-doorway-standard.php"
).read_text(encoding="utf-8")


class AnswerDoorwayMobilePresentationTests(unittest.TestCase):
    def test_shared_doorway_has_readable_mobile_type_scale(self):
        self.assertIn("@media (max-width: 700px)", DOORWAY_CSS)
        self.assertIn("font-size: 12.5px !important", DOORWAY_CSS)
        self.assertIn("font-size: 15.5px !important", DOORWAY_CSS)
        self.assertIn("font-size: 17.5px !important", DOORWAY_CSS)
        self.assertIn("focus-visible", DOORWAY_CSS)

    def test_guide_mobile_answer_has_readable_type_and_paragraph_rhythm(self):
        self.assertIn("@media (max-width: 700px)", GUIDE_SNIPPET)
        self.assertIn('.archive-stage-wrapper[data-guide-instance="woody"] .response-box', GUIDE_SNIPPET)
        self.assertIn("padding: 22px 20px 24px !important", GUIDE_SNIPPET)
        self.assertIn('.archive-stage-wrapper[data-guide-instance="woody"] #archive-response-text', GUIDE_SNIPPET)
        self.assertIn("font-size: 20px !important", GUIDE_SNIPPET)
        self.assertIn("line-height: 1.7 !important", GUIDE_SNIPPET)
        self.assertIn("margin-bottom: 1.15em !important", GUIDE_SNIPPET)

    def test_completed_answer_has_no_reserved_interlude_space(self):
        selector = (
            '.archive-stage-wrapper[data-guide-instance="woody"] '
            '.archive-search-container .archive-waiting-interlude[aria-hidden="true"]'
        )
        self.assertIn(selector, DOORWAY_CSS)
        self.assertIn("display: none !important", DOORWAY_CSS)
        self.assertIn("min-height: 0 !important", DOORWAY_CSS)
        self.assertIn("height: 0 !important", DOORWAY_CSS)
        self.assertIn("overflow: hidden !important", DOORWAY_CSS)

    def test_mobile_answer_surface_and_shared_doorway_palette_are_preserved(self):
        self.assertIn("background: #f1f1f1 !important", DOORWAY_CSS)
        self.assertIn("border: 1px solid #ddd !important", DOORWAY_CSS)
        self.assertIn("background: #f7f5ef", DOORWAY_CSS)
        self.assertIn("border-left: 2px solid #b89443", DOORWAY_CSS)

    def test_desktop_base_and_mobile_breakpoint_both_remain_defined(self):
        # The shared base rules are the desktop/tablet baseline; the <=700px
        # block is the mobile override. These assertions guard the breakpoint
        # contract without pretending to be a real browser screenshot test.
        self.assertIn(".la-answer-doorway {", DOORWAY_CSS)
        self.assertIn("font-size: 15px !important", DOORWAY_CSS)
        self.assertIn("@media (max-width: 700px)", DOORWAY_CSS)
        self.assertIn("font-size: 15.5px !important", DOORWAY_CSS)

    def test_shared_asset_version_is_bumped_for_cache_refresh(self):
        self.assertIn("Version: 1.0.4", PLUGIN_PHP)
        self.assertIn("LA_ANSWER_DOORWAY_VERSION', '1.0.4'", PLUGIN_PHP)


if __name__ == "__main__":
    unittest.main()
