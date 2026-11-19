"""The shared question contract reaches specialist execution context."""
import specialist_adapters as adapters


class _FakeAdapter:
    specialist_id = "fake_specialist"

    def __init__(self):
        self.context = None

    def process(self, context):
        self.context = context
        return {
            "contract_version": adapters.SPECIALIST_PIPE_CONTRACT_VERSION,
            "request_id": context.request_id,
            "specialist_id": context.specialist_id,
            "status": "complete",
            "voice_policy": "guide_integrates",
            "canonical_candidates": [],
            "boundary_notes": [],
            "safety_flags": [],
        }


class _FakeRegistry:
    def __init__(self, adapter):
        self.adapter = adapter

    def get(self, specialist_id):
        return self.adapter if specialist_id == self.adapter.specialist_id else None


def test_specialist_receives_validated_shared_question_contract(monkeypatch):
    adapter = _FakeAdapter()
    monkeypatch.setattr(adapters, "specialist_invocation_allowed", lambda _: True)
    monkeypatch.setattr(adapters, "validate_specialist_contribution", lambda value, **_: value)

    result = adapters.invoke_specialist(
        _FakeRegistry(adapter),
        request_id="qa-request-1",
        guide_version="qa",
        specialist_id="fake_specialist",
        original_question="How can a team verify that a configuration change worked?",
        recognized_territory="testing",
        processing_purpose="verification",
    )

    contract = adapter.context.question_contract
    assert result["request_id"] == "qa-request-1"
    assert contract["version"]
    assert contract["task"]["primary"] == "technical_verification_candidate"
    assert contract["task"]["semantic_resolution"] == "required"
    assert contract["uncertainty"]["task_candidate_confidence"] == "not_semantically_certified"


def test_specialist_contract_preserves_unknown_tasks_without_false_classification(monkeypatch):
    adapter = _FakeAdapter()
    monkeypatch.setattr(adapters, "specialist_invocation_allowed", lambda _: True)
    monkeypatch.setattr(adapters, "validate_specialist_contribution", lambda value, **_: value)

    adapters.invoke_specialist(
        _FakeRegistry(adapter),
        request_id="qa-request-2",
        guide_version="qa",
        specialist_id="fake_specialist",
        original_question="A thought about the future.",
        recognized_territory="open inquiry",
        processing_purpose="orientation",
    )

    contract = adapter.context.question_contract
    assert contract["task"]["primary"] == "unresolved"
    assert contract["task"]["candidate_source"] == "none"
    assert contract["uncertainty"]["classification_confidence"] == "not_scored"
