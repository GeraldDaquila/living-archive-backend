"""Regression tests for retrieval and navigation integrity primitives."""
import unittest
from guide_runtime import _valid_doc_url, _candidate_sentences, _extract_claims

class RetrievalNavigationIntegrityTests(unittest.TestCase):
    def test_invalid_or_missing_urls_are_not_accepted(self):
        self.assertEqual(_valid_doc_url({}), "")
        self.assertEqual(_valid_doc_url({"url":"javascript:alert(1)"}), "")
        self.assertEqual(_valid_doc_url({"url":"ftp://example.test/x"}), "")
        self.assertEqual(_valid_doc_url({"url":"https://example.test/a"}), "https://example.test/a")

    def test_missing_evidence_does_not_become_a_claim(self):
        docs=[{"title":"Title only","url":"https://example.test/a","text":""}]
        self.assertEqual(_extract_claims(_candidate_sentences("meaning and systems",docs)), [])

    def test_duplicate_evidence_is_deduplicated(self):
        sentence="Systems can become difficult to correct when feedback is ignored."
        docs=[
            {"title":"One","url":"https://example.test/1","text":sentence},
            {"title":"Two","url":"https://example.test/2","text":sentence},
        ]
        claims=_extract_claims(_candidate_sentences("systems feedback correct",docs))
        self.assertEqual(len(claims),1)

    def test_risk_material_is_not_mixed_into_general_navigation(self):
        docs=[
            {"title":"Risk","url":"https://example.test/r","text":"Suicide and immediate danger require crisis intervention."},
            {"title":"General","url":"https://example.test/g","text":"Systems change depends on learning from feedback over time."},
        ]
        candidates=_candidate_sentences("systems feedback",docs)
        self.assertEqual(len(candidates),1)
        self.assertEqual(candidates[0]["title"],"General")

if __name__=="__main__":
    unittest.main()
