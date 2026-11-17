"""Contract for the shared Answer + Doorway mobile reading hierarchy."""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parent
DOORWAY_CSS = (
    ROOT / "wordpress/living-archive-answer-doorway-standard/assets/answer-doorway.css"
).read_text()
GUIDE_SNIPPET = (
    ROOT / "wordpress/guide/woody-snippet-76926-universal.html"
).read_text()
PLUGIN_PHP = (
    ROOT / "wordpress/living-archive-answer-doorway-standard/living-archive-answer-doorway-standard.php"
).read_text()


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

    def test_shared_asset_version_is_bumped_for_cache_refresh(self):
        self.assertIn("Version: 1.0.3", PLUGIN_PHP)
        self.assertIn("LA_ANSWER_DOORWAY_VERSION', '1.0.3'", PLUGIN_PHP)


if __name__ == "__main__":
    unittest.main()
