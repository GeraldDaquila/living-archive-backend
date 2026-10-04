"""Production adapter for the Living Archive Seeing the Relationship plugin.

The adapter talks only to the plugin's documented WordPress REST surface.
It does not reproduce HRN's reasoning or rewrite HRN's language.

The Guide supplies bounded request context. HRN returns its own human-facing
response, relational state, movement, and canonical-resource material. The
Guide remains responsible for deciding when to invoke this adapter and how
to integrate the validated contribution.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Mapping

from specialist_adapters import SpecialistAdapter, SpecialistAdapterContext
from relationship_contribution import (
    RELATIONSHIP_VOICE_POLICY,
    validate_relationship_contribution,
)


DEFAULT_HRN_ENDPOINT = (
    "https://geralddaquila.com/wp-json/living-archive/v1/relational-navigator"
)


class RelationshipAdapter(SpecialistAdapter):
    specialist_id = "relationship"

    def __init__(self, endpoint: str | None = None, timeout: float = 12.0) -> None:
        self.endpoint = (
            str(endpoint or os.getenv("HRN_ENDPOINT_URL") or DEFAULT_HRN_ENDPOINT)
            .strip()
        )
        self.timeout = float(timeout)

    def process(self, context: SpecialistAdapterContext) -> Mapping[str, Any]:
        guide_context = dict(context.guide_context or {})
        payload = {
            "message": context.original_question,
            "conversation": str(
                guide_context.get("conversation")
                or guide_context.get("conversation_text")
                or ""
            ),
            "visitor_history": str(
                guide_context.get("visitor_history") or ""
            ),
            "unit_turns": int(guide_context.get("unit_turns") or 0),
            "safety_stage": str(context.safety_state or "green"),
            "safety_question": str(
                guide_context.get("safety_question") or ""
            ),
            "country": str(guide_context.get("country") or ""),
        }

        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            self.endpoint,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "Living-Archive-The-Guide/HRN-Adapter",
            },
            method="POST",
        )

        # HRN composition is deliberately retryable at its REST boundary.
        # A transient 503 can occur when the provider rejects one generated draft
        # and immediately succeeds on the next composition attempt. The specialist
        # adapter must absorb that transient operation failure rather than turning
        # it into a Guide-level 503 on the first occurrence.
        last_failure: str | None = None
        data: Mapping[str, Any] | None = None

        for attempt in range(2):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    raw = response.read().decode("utf-8", errors="replace")
                    status_code = int(getattr(response, "status", 200))
            except urllib.error.HTTPError as exc:
                status_code = int(exc.code)
                raw = exc.read().decode("utf-8", errors="replace")
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                if attempt == 0:
                    last_failure = f"Seeing the Relationship transport failed: {exc}"
                    time.sleep(1.0)
                    continue
                raise RuntimeError(
                    f"Seeing the Relationship transport failed: {exc}"
                ) from exc

            if status_code < 200 or status_code >= 300:
                last_failure = f"Seeing the Relationship returned HTTP {status_code}."
                if attempt == 0 and status_code in {429, 502, 503, 504}:
                    time.sleep(1.0)
                    continue
                raise RuntimeError(last_failure)

            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError as exc:
                if attempt == 0:
                    last_failure = "Seeing the Relationship returned non-JSON data."
                    time.sleep(1.0)
                    continue
                raise RuntimeError(
                    "Seeing the Relationship returned non-JSON data."
                ) from exc

            if not isinstance(parsed, Mapping):
                if attempt == 0:
                    last_failure = "Seeing the Relationship returned an invalid response envelope."
                    time.sleep(1.0)
                    continue
                raise RuntimeError(last_failure or "Seeing the Relationship returned an invalid response envelope.")

            if not parsed.get("ok"):
                last_failure = "Seeing the Relationship returned an unsuccessful response."
                if attempt == 0 and bool(parsed.get("retryable")):
                    time.sleep(1.0)
                    continue
                raise RuntimeError(last_failure)

            data = parsed
            break

        if data is None:
            raise RuntimeError(last_failure or "Seeing the Relationship returned no usable response.")

        safety_interrupt = bool(data.get("safety_interrupt"))
        status = "CONTRIBUTION"

        if safety_interrupt:
            status = "CONTRIBUTION"

        contribution = {
            "contract_version": "v1",
            "request_id": context.request_id,
            "specialist_id": self.specialist_id,
            "status": status,
            "voice_policy": RELATIONSHIP_VOICE_POLICY,
            "human_response": str(data.get("response") or ""),
            "interpretation": {
                "clarity": data.get("clarity"),
                "service_orientation": data.get("service_orientation"),
                "conversation_phase": data.get("conversation_phase"),
                "thread_summary": data.get("thread_summary"),
                "working_hypothesis": data.get("working_hypothesis"),
                "unresolved": data.get("unresolved"),
                "underlying_need": data.get("underlying_need"),
                "desired_condition": data.get("desired_condition"),
                "emerging_delta": data.get("emerging_delta"),
                "perspective_delta": data.get("perspective_delta"),
                "body_of_thought": data.get("body_of_thought"),
            },
            "perspectives": [],
            "movement": {
                "movement_state": data.get("movement_state"),
                "question": data.get("question"),
                "rest": data.get("rest"),
                "fractal_stage": data.get("fractal_stage"),
                "fractal_transition": data.get("fractal_transition"),
                "new_terrain": data.get("new_terrain"),
                "completed_insight": data.get("completed_insight"),
                "next_horizon": data.get("next_horizon"),
                "current_fractal": data.get("current_fractal"),
                "fractal_maturity": data.get("fractal_maturity"),
                "pivot_signal": data.get("pivot_signal"),
                "leadership_need": data.get("leadership_need"),
                "topic_shift": data.get("topic_shift"),
            },
            "canonical_candidates": data.get("resources") or [],
            "journey": {
                "journey_state": data.get("journey_state"),
                "journey_action": data.get("journey_action"),
                "spiral_complete": data.get("spiral_complete"),
                "journey_complete": data.get("journey_complete"),
                "fractal_complete": data.get("fractal_complete"),
                "fractal_summary": data.get("fractal_summary"),
                "fractal_records": data.get("fractal_records") or [],
                "round_synthesis_history": data.get("round_synthesis_history") or [],
                "segment_index": data.get("segment_index"),
                "segment_opening": data.get("segment_opening"),
                "body_of_thought": data.get("body_of_thought"),
                "journey_synthesis": data.get("journey_synthesis"),
                "guide_return_ready": data.get("guide_return_ready"),
                "display_mode": data.get("display_mode") or "hrn",
            },
            "boundary_notes": {
                "hrn_version": data.get("version"),
                "safety_interrupt": safety_interrupt,
            },
            "safety_flags": {
                "safety": data.get("safety"),
                "safety_interrupt": safety_interrupt,
                "safety_question": data.get("safety_question"),
            },
        }

        return validate_relationship_contribution(contribution)
