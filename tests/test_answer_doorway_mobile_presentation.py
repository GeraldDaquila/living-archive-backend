"""Contract for the shared Answer + Doorway mobile reading hierarchy."""
from pathlib import Path
import re
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
        self.assertRegex(DOORWAY_CSS, r"@media\s*\(max-width:\s*700px\)")
        self.assertRegex(DOORWAY_CSS, r"\.la-answer-doorway \.la-answer-doorway__label\s*\{[^}]*font-size:\s*12px")
        self.assertRegex(DOORWAY_CSS, r"\.la-answer-doorway \.la-answer-doorway__rationale\s*\{[^}]*font-size:\s*15px")
        self.assertRegex(DOORWAY_CSS, r"\.la-answer-doorway \.la-answer-doorway__link\s*\{[^}]*font-size:\s*17px")
        self.assertIn("focus-visible", DOORWAY_CSS)

    def test_guide_mobile_answer_is_not_shrunk_by_global_layout(self):
        mobile = re.search(
            r"@media\s*\(max-width:\s*700px\)\s*\{(.*?)\n\}",
            GUIDE_SNIPPET,
            re.S,
        )
        self.assertIsNotNone(mobile)
        css = mobile.group(1)
        self.assertIn(".response-box", css)
        self.assertIn("padding: 22px 20px 24px", css)
        self.assertRegex(css, r"\.archive-stage-wrapper\[data-guide-instance=\\"woody\\"\] #archive-response-text\s*\{[^}]*font-size:\s*20px")
        self.assertRegex(css, r"\.archive-stage-wrapper\[data-guide-instance=\\"woody\\"\] #archive-response-text\s*\{[^}]*line-height:\s*1\.7")

    def test_shared_asset_version_is_bumped_for_cache_refresh(self):
        self.assertIn("Version: 1.0.3", PLUGIN_PHP)
        self.assertIn("LA_ANSWER_DOORWAY_VERSION', '1.0.3'", PLUGIN_PHP)


if __name__ == "__main__":
    unittest.main()
