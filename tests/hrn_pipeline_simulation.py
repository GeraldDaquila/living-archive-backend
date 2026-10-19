"""In-memory HRN request-pipeline simulation for safety and E2E contract tests.

This is a test harness only. It does not call WordPress, network providers, or any
persistent store. It must never be wired into the production request path.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import re
from typing import Any, Callable


def _signature(value: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9 ]+", " ", value.casefold()).split())


def _safe_event(stage: str, **fields: Any) -> dict[str, Any]:
    """Allow only non-content diagnostics; never accept visitor text or secrets."""
    allowed = {"provider_id", "outcome", "reason"}
    event = {"stage": stage}
    for key, value in fields.items():
        if key in allowed and isinstance(value, (str, int, bool)):
            event[key] = value
    return event


class SimulatedHRNPipeline:
    """Single-commit pipeline with injectable providers and in-memory state."""

    def __init__(self, primary: Callable[[dict[str, Any]], dict[str, Any]],
                 fallback: Callable[[dict[str, Any]], dict[str, Any]]):
        self.primary = primary
        self.fallback = fallback
        self.ledgers: dict[str, dict[str, Any]] = {}
        self.receipts: dict[str, dict[str, Any]] = {}
        self.events: list[dict[str, Any]] = []
        self.commit_count = 0

    def process(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        original = deepcopy(snapshot)
        session_id = str(original.get("session_id") or "")
        request_id = str(original.get("request_id") or "")
        turn_id = str(original.get("visitor_turn_id") or "")
        if not session_id or not request_id or not turn_id or not str(original.get("visitor_message") or "").strip():
            self.events.append(_safe_event("entrance", request_id=request_id, session_id=session_id,
                                           turn_id=turn_id, outcome="rejected", reason="missing_identity_or_message"))
            return {"status": "retryable_failure", "committed": False, "reason": "invalid_request"}

        receipt_key = sha256(f"{session_id}|{turn_id}".encode()).hexdigest()
        if receipt_key in self.receipts:
            self.events.append(_safe_event("idempotency", request_id=request_id, session_id=session_id,
                                           turn_id=turn_id, outcome="replayed"))
            return deepcopy(self.receipts[receipt_key])

        committed = deepcopy(self.ledgers.get(session_id, {
            "session_id": session_id, "turn_number": 0, "visitor_evidence": [],
            "responses": [], "moves": [], "questions": [], "pending_visitor_evidence": None, "closed": False,
        }))
        if committed.get("closed"):
            self.events.append(_safe_event("snapshot", request_id=request_id, session_id=session_id,
                                           turn_id=turn_id, outcome="rejected", reason="journey_already_closed"))
            return {"status": "retryable_failure", "committed": False, "reason": "journey_closed"}

        expected_turn = int(committed["turn_number"]) + 1
        if int(original.get("turn_number") or 0) != expected_turn:
            self.events.append(_safe_event("snapshot", request_id=request_id, session_id=session_id,
                                           turn_id=turn_id, outcome="rejected", reason="turn_conflict"))
            return {"status": "retryable_failure", "committed": False, "reason": "turn_conflict"}

        # The current turn is staged separately. Neither provider can mutate committed state.
        staged = deepcopy(original)
        staged["committed_ledger"] = deepcopy(committed)
        staged["prior_responses"] = list(committed["responses"])
        staged["prior_moves"] = list(committed["moves"])
        staged["prior_questions"] = list(committed["questions"])
        staged["current_evidence_delta"] = {
            "turn_id": turn_id,
            "visitor_message_sha256": sha256(str(original["visitor_message"]).encode()).hexdigest(),
        }
        immutable_before = deepcopy(staged)

        self.events.append(_safe_event("provider_select", request_id=request_id, session_id=session_id,
                                       turn_id=turn_id, provider_id="primary", outcome="selected"))
        try:
            result = self.primary(deepcopy(staged))
        except Exception:
            result = None
        provider_id = "primary"
        if not self._valid(result, staged, committed):
            self.events.append(_safe_event("provider_validate", request_id=request_id, session_id=session_id,
                                           turn_id=turn_id, provider_id="primary", outcome="rejected",
                                           reason="provider_failure_or_invalid_result"))
            self.events.append(_safe_event("provider_select", request_id=request_id, session_id=session_id,
                                           turn_id=turn_id, provider_id="fallback", outcome="selected"))
            try:
                result = self.fallback(deepcopy(immutable_before))
            except Exception:
                result = None
            provider_id = "fallback"

        # Provider input must remain stable even if a provider tried to mutate its copy.
        if staged != immutable_before:
            self.events.append(_safe_event("snapshot_integrity", request_id=request_id, session_id=session_id,
                                           turn_id=turn_id, outcome="failed"))
            return {"status": "retryable_failure", "committed": False, "reason": "snapshot_integrity_failure"}

        if not self._valid(result, immutable_before, committed):
            # Preserve the current visitor contribution for retry without advancing
            # the turn, writing assistant synthesis, or logging raw visitor content.
            pending_ledger = deepcopy(committed)
            pending_ledger["pending_visitor_evidence"] = {
                "turn_id": turn_id,
                "message_sha256": immutable_before["current_evidence_delta"]["visitor_message_sha256"],
            }
            self.ledgers[session_id] = pending_ledger
            self.events.append(_safe_event("commit", request_id=request_id, session_id=session_id,
                                           turn_id=turn_id, provider_id=provider_id, outcome="refused",
                                           reason="no_valid_nonrepeating_response"))
            return {"status": "retryable_failure", "committed": False, "reason": "no_valid_result"}

        response = str(result["response_draft"]).strip()
        # A provider's proposed state is never authoritative; the pipeline owns the commit.
        next_ledger = deepcopy(committed)
        next_ledger["turn_number"] = expected_turn
        next_ledger["pending_visitor_evidence"] = None
        next_ledger["visitor_evidence"] = (next_ledger["visitor_evidence"] + [{
            "turn_id": turn_id,
            "message_sha256": immutable_before["current_evidence_delta"]["visitor_message_sha256"],
        }])[-8:]
        next_ledger["responses"] = (next_ledger["responses"] + [response])[-8:]
        next_ledger["moves"] = (next_ledger["moves"] + [str(result["next_move"])])[-8:]
        next_ledger["questions"] = (next_ledger["questions"] + [str(result.get("question") or "")])[-8:]
        next_ledger["closed"] = str(result["next_move"]) == "close"
        self.ledgers[session_id] = next_ledger
        self.commit_count += 1
        envelope = {
            "status": "success", "committed": True, "session_id": session_id,
            "visitor_turn_id": turn_id, "turn_number": expected_turn,
            "provider_id": provider_id, "response": response,
            "move": str(result["next_move"]), "closed": next_ledger["closed"],
        }
        self.receipts[receipt_key] = deepcopy(envelope)
        self.events.append(_safe_event("commit", request_id=request_id, session_id=session_id,
                                       turn_id=turn_id, provider_id=provider_id, outcome="committed"))
        return envelope

    @staticmethod
    def _valid(result: Any, snapshot: dict[str, Any], committed: dict[str, Any]) -> bool:
        if not isinstance(result, dict) or result.get("status") != "success":
            return False
        if result.get("session_id") != snapshot.get("session_id"):
            return False
        if result.get("visitor_turn_id") != snapshot.get("visitor_turn_id"):
            return False
        response = result.get("response_draft")
        move = result.get("next_move")
        if not isinstance(response, str) or not response.strip():
            return False
        if move not in {"clarify", "distinguish", "deepen", "reflect", "close"}:
            return False
        signature = _signature(response)
        if not signature or any(signature == _signature(previous) for previous in committed["responses"]):
            return False
        # Question novelty is independent of response novelty: changing the prose
        # while asking the same question must not be treated as journey movement.
        question = result.get("question")
        if question is not None and str(question).strip():
            question_signature = _signature(str(question))
            if any(question_signature == _signature(str(previous))
                   for previous in committed["questions"] if str(previous).strip()):
                return False
        if not isinstance(result.get("evidence_delta"), list) or not result["evidence_delta"]:
            return False
        return True


def scripted_provider(move: str, response: str, evidence: str,
                      *, status: str = "success", session_override: str | None = None,
                      mutate_input: bool = False, question: str = "") -> Callable[[dict[str, Any]], dict[str, Any]]:
    """Build a deterministic provider fixture for pipeline simulations."""
    def provider(snapshot: dict[str, Any]) -> dict[str, Any]:
        if mutate_input:
            snapshot["committed_ledger"]["turn_number"] = 999
        return {
            "status": status,
            "session_id": session_override if session_override is not None else snapshot.get("session_id"),
            "visitor_turn_id": snapshot.get("visitor_turn_id"),
            "evidence_delta": [evidence],
            "next_move": move,
            "response_draft": response,
            "question": question,
            "proposed_state_delta": {"turn_number": 999999, "session_id": "provider-must-not-own-commit"},
        }
    return provider
