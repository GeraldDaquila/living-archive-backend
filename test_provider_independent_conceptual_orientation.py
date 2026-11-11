import unittest
from deterministic_answer_recovery import compose_recovery

class ProviderIndependentConceptualOrientationTests(unittest.TestCase):
    def test_ai_interpreter_authority_survives_provider_exhaustion(self):
        answer = compose_recovery("What does it mean for an AI to be an interpreter rather than an authority?")
        self.assertIn("interpreter rather than an authority", answer)
        self.assertNotIn("couldn't verify a reliable answer", answer.lower())
        self.assertEqual(len([p for p in answer.split("\n\n") if p.strip()]), 3)

if __name__ == "__main__":
    unittest.main()
