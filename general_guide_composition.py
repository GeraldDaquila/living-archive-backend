"""Provider-neutral General Guide composition seam.

This module owns the all-purpose visitor-answer contract for The Guide.
It does not select a provider itself. All generative work crosses the
Provider Bank so no individual LLM is an architectural dependency.
"""

import hashlib
import json
import re
import threading
import logging
import time
from collections import OrderedDict
from typing import Any, Dict, List, Optional

from gold_star_question_contract import build_question_contract, validate_question_contract
from guide_incomplete_knowledge import build_incomplete_knowledge_plan
from gold_star_adjudication_trace import (
    build_adjudication_trace as _build_gold_star_adjudication_trace,
    mark_composition_result as _mark_gold_star_composition_result,
    validate_trace as _validate_gold_star_adjudication_trace,
)

from general_guide_gold_standards import resolve_exact_gold_standard as _registered_exact_gold_standard
import comparative_traditions_contract as _comparative_traditions_contract
from gold_star_lessons import (shadow_observation as _gold_star_shadow_observation, active_quality_contribution as _gold_star_active_quality_contribution)

from provider_bank import (
    CONTRACT_VERSION as PROVIDER_BANK_CONTRACT_VERSION,
    route as route_with_model_bank,
)

CONTRACT_VERSION = "v1.54"
VISITOR_LANGUAGE_BOUNDARY_VERSION = "v1"
OPERATION = "general_guide_composition"

GOLD_STAR_ADAPTIVE_INTELLIGENCE_STANDARD_VERSION = "2.0"
_GOLD_STAR_ADAPTIVE_INTELLIGENCE_SYSTEM_CONTRACT = """GOLD STAR ADAPTIVE INTELLIGENCE STANDARD v2.0 — QUESTION-DEPENDENT QUALITY CONTRACT

Apply these eight dimensions as quality expectations, not as eight mandatory sections or a universal response template:
1. PROSE — clear, precise, readable, appropriately toned, economical, and expressive in service of understanding.
2. STRUCTURE — choose organization, progression, hierarchy, and presentation appropriate to this question; do not force a fixed paragraph count or sequence.
3. COHERENCE — maintain logical consistency, connected reasoning, conceptual integrity, and conclusions supported by premises and evidence.
4. QUESTION-FIT AND COMPETENCE — identify the visitor's actual task, domain, requested deliverable, and stakes; use suitable subject-specific knowledge and reasoning rather than a neighboring or generic answer.
5. DISCERNMENT AND EPISTEMIC INTEGRITY — distinguish established facts, source-grounded claims, interpretation, inference, uncertainty, and unknowns; calibrate confidence and disclose material limits.
6. RESOLUTION AND PRACTICAL UTILITY — deliver the value the question calls for: an explanation, distinction, method, decision framework, practical action, synthesis, or appropriately bounded answer. Resolve the question before optional navigation or follow-up.
7. CONTINUITY AND DEVELOPMENTAL VALUE — offer a next step or canonical resource only when it genuinely advances this inquiry. Respect explicit requests for no handoff or follow-up; never manufacture engagement.
8. ADAPTIVE LEARNING INTEGRITY — use approved evidence only within its recorded capability, qualifying context, and abstention boundary. Transfer reviewed reasoning discipline only; never transfer exemplar-specific wording, answer text, factual claims, examples, citations, or doorways to another question.

This contract establishes a question-sensitive quality floor. It does not guarantee factual correctness, domain expertise, or semantic certification. When evidence is incomplete, state the limit and provide the best useful bounded answer. Do not turn every answer into a framework, checklist, or three-paragraph template. Adapt the depth and structure to the visitor's actual task.
"""

