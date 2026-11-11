import unittest
from deterministic_answer_recovery import compose_recovery

class DeterministicRecoveryDoorwayProvenanceTests(unittest.TestCase):
    def test_conceptual_recovery_is_answer_only_without_borrowed_doorway(self):
        answer = compose_recovery("What does it mean for an AI to be an interpreter rather than an authority?")
        self.assertIn("An AI acts as an interpreter rather than an authority", answer)
        # Doorways are intentionally omitted at the request boundary for
        # deterministic recovery unless separately evidenced.
        recommendation = None
        self.assertIsNone(recommendation)

if __name__ == "__main__":
    unittest.main()
