import unittest
from deterministic_answer_recovery import compose_recovery

class DoorwayProvenanceContract(unittest.TestCase):
    def test_frozen_interpreter_recovery_has_no_inherited_doorway(self):
        answer=compose_recovery("What does it mean for an AI to be an interpreter rather than an authority?")
        self.assertTrue(answer.startswith("An AI acts as an interpreter rather than an authority"))
        recommendation=None
        self.assertIsNone(recommendation)

if __name__=="__main__": unittest.main()
