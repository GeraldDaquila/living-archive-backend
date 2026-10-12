"""Runtime-independent contract probes for shared intelligence."""
from __future__ import annotations

from dataclasses import asdict
import re


STATUS = {"READY", "DELEGATE", "NEEDS_RETRY", "UNAVAILABLE"}
CLAIM_TYPES = {"definition", "relationship", "observation", "interpretation", "exploration"}
EPISTEMIC = {"supported", "inferred", "interpretive", "visitor-originated", "uncertain"}


def _valid_url(value: str) -> bool:
    return bool(re.match(r"^https://\S+$", value or "", re.I))


def validate_evidence(item: dict) -> None:
    assert item.get("id")
    assert item.get("title")
    assert _valid_url(item.get("url", ""))
    assert item.get("text")


def validate_claim(claim: dict) -> None:
    assert claim.get("text")
    assert claim.get("claim_type") in CLAIM_TYPES
    assert isinstance(claim.get("evidence_ids", []), list)
    if claim.get("epistemic") is not None:
        assert claim["epistemic"] in EPISTEMIC


def validate_result(result: dict) -> None:
    assert result.get("status") in STATUS
    assert result.get("contract_version")
    if result["status"] == "READY":
        assert result.get("payload") is not None
    else:
        assert result.get("reason")


def main() -> int:
    evidence = {
        "id": "site:example",
        "title": "Example",
        "url": "https://geralddaquila.com/example/",
        "text": "A complete source passage.",
        "provenance": "canonical",
    }
    claim = {
        "text": "A complete proposition.",
        "evidence_ids": ["site:example"],
        "claim_type": "observation",
        "epistemic": "supported",
    }
    result = {
        "status": "READY",
        "mode": "general",
        "payload": {"claims": [claim]},
        "reason": "",
        "contract_version": "v1",
    }

    validate_evidence(evidence)
    validate_claim(claim)
    validate_result(result)

    for status in STATUS - {"READY"}:
        validate_result({"status": status, "mode": "general", "payload": None, "reason": "bounded state", "contract_version": "v1"})

    print("shared contract probes: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
