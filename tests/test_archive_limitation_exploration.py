import unittest

from guide_direct_attribute_evidence import archive_limitation_response


class ArchiveLimitationExplorationTests(unittest.TestCase):
    def test_conceptual_relationship_fallback_splits_subjects_without_claiming_support(self):
        response = archive_limitation_response(
            "What is the role of trust in community stewardship?"
        )
        self.assertIn("'trust'", response)
        self.assertIn("'community stewardship'", response)
        self.assertIn("haven’t found enough support", response)
        self.assertIn("supports", response)
        self.assertNotIn("Trust Architecture", response)
        self.assertNotIn("Glossary", response)

    def test_nonmatching_question_keeps_generic_bounded_fallback(self):
        response = archive_limitation_response("Why is the sky blue?")
        self.assertIn("haven’t found enough support", response)
        self.assertIn("narrowing the question", response)


if __name__ == "__main__":
    unittest.main()
