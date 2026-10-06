"""Adapter for the sitewide Safety / Crisis utility."""
from __future__ import annotations
from typing import Any, Mapping
from safety_utility import build_safety_contribution

class SafetyUtilityAdapter:
    specialist_id = "safety"
    def process(self, context) -> Mapping[str, Any]:
        guide_context = dict(context.guide_context or {})
        return build_safety_contribution(
            request_id=context.request_id,
            query=context.original_question,
            safety_state=str(context.safety_state or "amber"),
            country=str(guide_context.get("country") or ""),
        )
