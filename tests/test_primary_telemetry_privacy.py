"""Regression checks that USE operational telemetry never stores visitor query text."""

from pathlib import Path
import unittest


class PrimaryTelemetryPrivacyTests(unittest.TestCase):
    def test_operational_logs_record_lengths_not_raw_visitor_questions(self):
        source = (Path(__file__).resolve().parents[1] / "main.py").read_text(encoding="utf-8")

        self.assertNotIn("query={_normalize_query(query_str)[:120]}", source)
        self.assertNotIn("query={_normalize_query(query)[:120]}", source)
        self.assertIn("query_chars={len(query_str)}", source)
        self.assertIn("query_chars={len(query)}", source)

        for line in source.splitlines():
            if "print(" in line or "logger." in line:
                self.assertNotIn("query=%r", line)
                self.assertNotIn("question=%r", line)
                self.assertNotIn("conversation=%r", line)


if __name__ == "__main__":
    unittest.main()
