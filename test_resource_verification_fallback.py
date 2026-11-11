import unittest
from general_guide_composition import is_generic_nonanswer

class ResourceVerificationFallbackTests(unittest.TestCase):
    def test_known_concept_resource_fallback_is_nonanswer(self):
        query = "What does it mean for an AI to be an interpreter rather than an authority?"
        response = ("Your question asks: what does it mean for an AI to be an interpreter rather than an authority.\n\n"
                    "I couldn't verify a reliable answer from the material available in this request, so I won't present a guess as fact.\n\n"
                    "I could not identify a sufficiently relevant Archive resource to recommend here.")
        self.assertTrue(is_generic_nonanswer(query, response))

if __name__ == "__main__":
    unittest.main()
