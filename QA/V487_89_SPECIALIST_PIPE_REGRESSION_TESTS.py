"""Current specialist-pipe regression probes.

These probes exercise two failure seams that previously could pass structural
checks while failing in production:
1. domain-specific specialist payload preservation through the common pipe;
2. transient HRN transport failure recovery at the Relationship adapter.
"""

from pathlib import Path
from unittest.mock import patch
import json
import urllib.error

from relationship_adapter import RelationshipAdapter
from specialist_adapters import (
    SpecialistAdapterContext,
    SpecialistAdapterRegistry,
    invoke_specialist,
)


ROOT = Path(__file__).resolve().parents[1]


class _FakeFormationAdapter:
    specialist_id = "formation"

    def process(self, context):
        return {
            "contract_version": "formation-v1",
            "request_id": context.request_id,
            "specialist_id": "formation",
            "status": "CONTRIBUTION",
            "voice_policy": "preserve_specialist_boundary",
            "interpretation": {
                "pathway": "The responsibility is changing shape.",
                "signals": {"responsibility_transition": True},
            },
            "movement": {"direction": "formation"},
            "canonical_candidates": [
                {
                    "id": "learning_arcs",
                    "title": "Learning Arcs",
                    "url": "https://geralddaquila.com/steward-access-12-learning-arcs/",
                }
            ],
            "boundary_notes": {"t4_destination_allowed": False},
            "safety_flags": {"safety_state": "green"},
        }


class _Response:
    def __init__(self, status, payload):
        self.status = status
        self._payload = payload

    def read(self):
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_domain_payload_survives_common_pipe():
    registry = SpecialistAdapterRegistry()
    registry.register(_FakeFormationAdapter())

    result = invoke_specialist(
        registry,
        request_id="qa-formation-payload-001",
        guide_version="qa-current",
        specialist_id="formation",
        original_question="I am carrying a larger responsibility.",
        recognized_territory="stewardship formation",
        processing_purpose="bounded formation navigation",
        guide_context={"situation": "A responsibility is changing."},
        safety_state="green",
    )

    assert result["status"] == "CONTRIBUTION"
    assert result["payload"]["interpretation"]["pathway"] == (
        "The responsibility is changing shape."
    )
    assert result["payload"]["movement"]["direction"] == "formation"
    assert result["canonical_candidates"][0]["id"] == "learning_arcs"


def test_relationship_adapter_retries_transient_503():
    adapter = RelationshipAdapter(endpoint="https://example.test/hrn", timeout=1.0)
    context = SpecialistAdapterContext(
        request_id="qa-hrn-retry-001",
        guide_version="v487.91",
        specialist_id="relationship",
        original_question="Something feels different between us.",
        recognized_territory="human relationships",
        processing_purpose="open relational exploration",
        guide_context={"conversation": ""},
        safety_state="green",
    )

    calls = {"count": 0}

    def fake_urlopen(request, timeout):
        calls["count"] += 1
        if calls["count"] == 1:
            body = json.dumps(
                {"ok": False, "retryable": True, "error": "transient composition failure"}
            ).encode("utf-8")
            raise urllib.error.HTTPError(
                request.full_url,
                503,
                "Service Unavailable",
                {},
                __import__("io").BytesIO(body),
            )
        return _Response(
            200,
            {
                "ok": True,
                "response": "There is something worth noticing in what is happening between you.",
                "clarity": "relational pattern",
                "movement_state": "explore",
                "resources": [],
            },
        )

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        result = adapter.process(context)

    assert calls["count"] == 2
    assert result["status"] == "CONTRIBUTION"
    assert result["human_response"].startswith("There is something worth noticing")
    assert result["voice_policy"] == "preserve_specialist_voice"


def test_current_main_contains_domain_payload_consumption_guards():
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    assert 'APP_VERSION = "v489.26"' in source
    assert "domain_payload = dict(hub_contribution.payload or {})" in source
    assert "interpretation_data = dict(domain_payload.get(\"interpretation\") or {})" in source
    assert "domain_payload = dict(contribution.get(\"payload\") or {})" in source
    assert "interpretation = dict(domain_payload.get(\"interpretation\") or {})" in source


if __name__ == "__main__":
    test_domain_payload_survives_common_pipe()
    test_relationship_adapter_retries_transient_503()
    test_current_main_contains_domain_payload_consumption_guards()
    print("current specialist-pipe regression probes: PASS")
