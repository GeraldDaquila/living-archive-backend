"""Single-call Provider Bank adapter for visitor-safe claim adjudication.

The caller must pass only documents parsed from visitor-visible public retrieval.
No retrieval, direct provider SDK, visitor logging, or protected-source access lives here.
"""
from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any


def build_provider_adjudicator(use_core: Any, deadline_monotonic: float):
    """Return one bounded, provider-neutral adjudication callback."""
    def adjudicate(answer: str, passages: Sequence[Mapping[str, str]]):
        from provider_bank import route

        bounded_passages = [
            {
                "passage_id": str(item.get("passage_id") or ""),
                "source_status": str(item.get("source_status") or ""),
                "text": str(item.get("text") or "")[:1600],
            }
            for item in list(passages or [])[:16]
            if isinstance(item, Mapping)
        ]
        if not bounded_passages:
            return None

        request = {
            "answer": str(answer or "")[:6000],
            "passages": bounded_passages,
            "required_outcomes": [
                "supported",
                "partially_supported",
                "contradicted",
                "stale_or_unavailable",
                "no_relevant_public_source",
            ],
            "required_claim_fields": [
                "claim",
                "answer_quote",
                "outcome",
                "reason",
                "attributions",
            ],
            "attribution_fields": ["passage_id", "quote"],
        }
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a bounded evidence adjudicator. Extract the material factual "
                    "claims from the supplied answer, include an exact contiguous answer_quote copied verbatim from it for every extracted claim, and assess each only against the "
                    "supplied retrieved passages. Return one JSON object with a 'claims' "
                    "array. Each claim must use exactly one required outcome. Use "
                    "'supported' only when the passage directly supports the claim; "
                    "'partially_supported' when it supports only part; 'contradicted' "
                    "only when the passage directly conflicts; 'stale_or_unavailable' "
                    "only when a supplied passage has explicit source_status metadata "
                    "marking it stale or unavailable; otherwise do not infer staleness; "
                    "and 'no_relevant_public_source' when these public passages do not "
                    "address the claim. If you cannot make a reliable finding, use "
                    "'unassessed'. Never infer a quote, passage ID, source, date, or fact. "
                    "For supported, partially_supported, and contradicted, provide at "
                    "least one exact contiguous quote copied verbatim from the identified "
                    "passage and its exact passage_id. For other outcomes, use an empty "
                    "attributions array. Do not treat absence of support as contradiction. "
                    "Do not include anything outside the JSON object."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(request, ensure_ascii=False, separators=(",", ":")),
            },
        ]

        def parse(raw):
            if isinstance(raw, Mapping):
                parsed = dict(raw)
            else:
                try:
                    parsed = json.loads(str(raw or "").strip())
                except (TypeError, ValueError, json.JSONDecodeError):
                    return None
            if not isinstance(parsed, dict) or not isinstance(parsed.get("claims"), list):
                return None
            return parsed

        result = route(
            use_core=use_core,
            messages=messages,
            max_tokens=1500,
            parse=parse,
            operation="claim_adjudication",
            deadline_monotonic=deadline_monotonic,
        )
        if not isinstance(result, Mapping):
            return None
        return result.get("claims")

    return adjudicate
