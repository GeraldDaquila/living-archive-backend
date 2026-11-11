import unittest
from general_guide_composition import is_generic_nonanswer

class VerificationFallbackClassificationTests(unittest.TestCase):
    def test_live_verification_abstention_is_generic_nonanswer(self):
        query = "What does it mean for an AI to be an interpreter rather than an authority?"
        response = ("I can't define it reliably from the information available in this response alone. "
                    "I don't want to invent a definition or imply that a guess is established knowledge.\n\n"
                    "For a general concept, a reliable dictionary or subject reference can establish the ordinary meaning.")
        self.assertTrue(is_generic_nonanswer(query, response))

if __name__ == "__main__":
    unittest.main()
