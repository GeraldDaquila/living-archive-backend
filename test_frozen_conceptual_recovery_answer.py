import unittest
from deterministic_answer_recovery import compose_recovery

class FrozenConceptualRecoveryRegression(unittest.TestCase):
    def test_ai_interpreter_authority_answer_remains_frozen(self):
        answer = compose_recovery("What does it mean for an AI to be an interpreter rather than an authority?")
        self.assertTrue(answer.startswith("An AI acts as an interpreter rather than an authority"))
        self.assertEqual(len([p for p in answer.split("\\n\\n") if p.strip()]), 3)

if __name__ == "__main__":
    unittest.main()
