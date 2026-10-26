"""Deterministic CLSS contract regressions; these do not evaluate LLM semantic quality."""
import copy
import unittest

from clss.standalone_contract import (
    CONTRACT_VERSION, DOORWAYS, QUESTIONS, ContractError, validate_input, validate_output,
)


def valid_input(perspective="self"):
    return {
        "contract_version": CONTRACT_VERSION,
        "perspective": perspective,
        "answers": [
            {"answer_id": qid, "text": "" if qid == "q4" else f"example for {qid}"}
            for qid, _title, _help in QUESTIONS
        ],
    }


def valid_output(packet):
    return {
        "contract_version": CONTRACT_VERSION,
        "perspective": packet["perspective"],
        "evidence_map": [{
            "claim_id": "claim-1",
            "answer_refs": ["q2"],
            "evidence_kind": "reported",
            "coherence_dimension": "decisions_actions",
            "statement": "The account reports a specific decision.",
            "alternative_readings": ["The account may omit relevant constraints."],
            "uncertainty": "Independent corroboration is not yet available.",
        }],
        "supported_coherence": [],
        "possible_incoherence": [],
        "unresolved_questions": ["What corroborating account is available?"],
        "next_step": {
            "action": "Seek one independent account of the decision.",
            "rationale": "The current evidence is reported rather than independently corroborated.",
            "evidence_refs": ["q2"],
        },
        "doorway": {
            "status": "recommended",
            "stage_id": "stewardship_evidence",
            "title": DOORWAYS["stewardship_evidence"][0],
            "url": DOORWAYS["stewardship_evidence"][1],
            "rationale": "The central unresolved issue is evidence corroboration.",
        },
        "boundary_notes": ["This is not a suitability verdict."],
    }


class InputContractTests(unittest.TestCase):
    def test_preserves_nine_question_texts_and_ids(self):
        self.assertEqual(len(QUESTIONS), 9)
        self.assertEqual([q[0] for q in QUESTIONS], [f"q{i}" for i in range(1, 10)])
        self.assertEqual(QUESTIONS[0][1], "What responsibility or decision are you facing?")

    def test_accepts_both_perspectives_and_blank_answers(self):
        for perspective in ("self", "third_party"):
            packet = validate_input(valid_input(perspective))
            self.assertEqual(packet["perspective"], perspective)
            self.assertEqual(packet["answers"][3]["text"], "")

    def test_rejects_invalid_perspective(self):
        packet = valid_input("observer")
        with self.assertRaises(ContractError):
            validate_input(packet)

    def test_rejects_missing_or_duplicate_answer_ids(self):
        packet = valid_input()
        packet["answers"].pop()
        with self.assertRaises(ContractError):
            validate_input(packet)
        packet = valid_input()
        packet["answers"][1]["answer_id"] = "q1"
        with self.assertRaises(ContractError):
            validate_input(packet)

    def test_rejects_non_string_or_oversized_answers(self):
        packet = valid_input()
        packet["answers"][0]["text"] = None
        with self.assertRaises(ContractError):
            validate_input(packet)
        packet = valid_input()
        packet["answers"][0]["text"] = "x" * 12001
        with self.assertRaises(ContractError):
            validate_input(packet)


class OutputContractTests(unittest.TestCase):
    def setUp(self):
        self.packet = validate_input(valid_input("third_party"))
        self.output = valid_output(self.packet)

    def test_accepts_registered_doorway_and_answer_references(self):
        self.assertIs(validate_output(self.output, self.packet), self.output)

    def test_rejects_dangling_answer_reference(self):
        output = copy.deepcopy(self.output)
        output["evidence_map"][0]["answer_refs"] = ["q99"]
        with self.assertRaises(ContractError):
            validate_output(output, self.packet)

    def test_rejects_unregistered_or_mismatched_doorway(self):
        output = copy.deepcopy(self.output)
        output["doorway"]["url"] = "https://example.com/fake"
        with self.assertRaises(ContractError):
            validate_output(output, self.packet)
        output = copy.deepcopy(self.output)
        output["doorway"]["stage_id"] = "made_up"
        with self.assertRaises(ContractError):
            validate_output(output, self.packet)

    def test_allows_no_doorway_without_destination(self):
        output = copy.deepcopy(self.output)
        output["doorway"] = {
            "status": "insufficient_evidence",
            "stage_id": None, "title": None, "url": None, "rationale": None,
        }
        self.assertIs(validate_output(output, self.packet), output)

    def test_rejects_perspective_mismatch_and_invalid_evidence_kind(self):
        output = copy.deepcopy(self.output)
        output["perspective"] = "self"
        with self.assertRaises(ContractError):
            validate_output(output, self.packet)
        output = copy.deepcopy(self.output)
        output["evidence_map"][0]["evidence_kind"] = "proven_bad_person"
        with self.assertRaises(ContractError):
            validate_output(output, self.packet)

    def test_rejects_next_step_with_dangling_reference(self):
        output = copy.deepcopy(self.output)
        output["next_step"]["evidence_refs"] = ["missing-answer"]
        with self.assertRaises(ContractError):
            validate_output(output, self.packet)


if __name__ == "__main__":
    unittest.main()
