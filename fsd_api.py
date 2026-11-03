"""Authenticated FSD analysis endpoint registered on the existing USE app.

No new service, retriever, persistence layer, or browser-held credential is used.
"""
from __future__ import annotations

import json
import threading
import time
from collections import defaultdict, deque
from typing import Any

from fastapi import HTTPException, Request
from starlette.concurrency import run_in_threadpool

from fsd_contract import CONTRACT_VERSION, FSDContractError, validate_diagnostic_payload
from fsd_runtime import prepare_fsd_analysis
from fsd_report_contract import FSDReportContractError, validate_fsd_report
from provider_gateway_service import (
    authorize as authorize_provider_gateway,
    execute as execute_provider_gateway,
)

MAX_BODY_BYTES = 16_384
RATE_WINDOW_SECONDS = 60.0
RATE_MAX_REQUESTS = 30
_RATE_LOCK = threading.Lock()
_RATE_EVENTS: dict[str, deque[float]] = defaultdict(deque)
_REGISTERED_APPS: set[int] = set()

_REPORT_SCHEMA = {
    "name": "fsd_two_quantum_report",
    "strict": False,
    "schema": {
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
            "recurring_condition": {"type": "string"},
            "reported_signal": {"type": "string"},
            "strengths": {"type": "array", "items": {"type": "string"}},
            "enabling_conditions": {"type": "array", "items": {"type": "string"}},
            "constraints": {"type": "array", "items": {"type": "string"}},
            "next_steps": {"type": "array", "items": {"type": "string"}},
            "evidence_ids": {"type": "array", "items": {"type": "string"}},
        },
        "required": [
            "summary", "recurring_condition", "reported_signal", "strengths",
            "enabling_conditions", "constraints", "next_steps", "evidence_ids",
        ],
        "additionalProperties": False,
    },
}


def _check_rate_limit(client_key: str) -> None:
    now = time.monotonic()
    with _RATE_LOCK:
        events = _RATE_EVENTS[client_key]
        while events and now - events[0] > RATE_WINDOW_SECONDS:
            events.popleft()
        if len(events) >= RATE_MAX_REQUESTS:
            raise HTTPException(status_code=429, detail="FSD request limit reached.")
        events.append(now)


def _compose_report(payload: dict[str, Any], analysis: dict[str, Any]) -> dict[str, Any]:
    validated = analysis["validated"]
    evidence = analysis["evidence"]
    quantum_coverage = {item.get("quantum_id") for item in evidence}
    if quantum_coverage != {"Q001_CORRESPONDENCE", "Q002_CORRECTABILITY"}:
        raise HTTPException(
            status_code=422,
            detail={"code": "insufficient_independent_quantum_evidence"},
        )

    evidence_for_prompt = [
        {
            "evidence_id": item["evidence_id"],
            "quantum": item["quantum_id"],
            "title": item["title"],
            "excerpt": item["excerpt"],
        }
        for item in evidence
    ]
    system = (
        "You prepare a cautious, appreciative systems diagnostic report. "
        "Return exactly one JSON object matching the supplied schema. "
        "Use only the server-provided evidence IDs. Do not invent sources, URLs, "
        "facts, causal certainty, or findings at unselected scales. "
        "Describe the selected scale as visitor-reported, not independently proven. "
        "Separate strengths, enabling conditions, constraints, and practical next steps. "
        "The recurring condition must be a cautious synthesis supported by both "
        "quantum evidence sets. If evidence does not support a coherent condition, "
        "state that the evidence is insufficient in the report rather than guessing. "
        "Never expose internal process labels or provider/model information."
    )
    user = {
        "diagnostic_contract": CONTRACT_VERSION,
        "scale": validated["scale"] or "not selected",
        "quantum_summaries": validated["quantum_summaries"],
        "canonical_evidence": evidence_for_prompt,
        "answer_selections": payload["answers"],
        "output_rules": {
            "exact_fields": sorted(_REPORT_SCHEMA["schema"]["properties"]),
            "maximum_list_items": 4,
            "maximum_evidence_ids": 6,
            "evidence_ids_only": True,
            "do_not_infer_other_scales": True,
        },
    }
    result = execute_provider_gateway(
        operation="fsd_report_composition",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
        ],
        max_tokens=1400,
        use_core=_compose_report.use_core,
        schema=_REPORT_SCHEMA,
    )
    if not result.get("ok"):
        raise HTTPException(
            status_code=503,
            detail={"code": "fsd_provider_bank_unavailable"},
        )
    try:
        report = validate_fsd_report(
            result.get("result"),
            evidence,
            validated["scale"],
        )
    except FSDReportContractError as exc:
        raise HTTPException(
            status_code=502,
            detail={"code": "fsd_report_contract_rejected"},
        ) from exc

    return {
        "ok": True,
        "contract_version": CONTRACT_VERSION,
        "quantum_summaries": validated["quantum_summaries"],
        "report": report,
    }


def _run_analysis(payload: dict[str, Any], use_core: Any) -> dict[str, Any]:
    try:
        validated = validate_diagnostic_payload(payload)
        analysis = prepare_fsd_analysis(
            payload,
            retrieve=use_core.fetch_canonical_context,
        )
    except FSDContractError as exc:
        raise HTTPException(status_code=400, detail={"code": "invalid_fsd_request"}) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": "insufficient_canonical_evidence"},
        ) from exc
    _compose_report.use_core = use_core
    return _compose_report(payload, analysis)


def register_fsd_routes(app: Any, use_core: Any) -> None:
    """Register once on the existing FastAPI app; callable from guide_runtime."""
    app_key = id(app)
    if app_key in _REGISTERED_APPS:
        return
    _REGISTERED_APPS.add(app_key)

    @app.post("/api/fsd/analyze")
    async def fsd_analyze(request: Request):
        authorize_provider_gateway(
            request.headers.get("X-Living-Archive-Provider-Key")
        )
        client_key = request.client.host if request.client else "unknown"
        _check_rate_limit(client_key)
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > MAX_BODY_BYTES:
                    raise HTTPException(status_code=413, detail="FSD request is too large.")
            except ValueError as exc:
                raise HTTPException(status_code=400, detail="Invalid content length.") from exc
        raw = await request.body()
        if len(raw) > MAX_BODY_BYTES:
            raise HTTPException(status_code=413, detail="FSD request is too large.")
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise HTTPException(status_code=400, detail="FSD request must be valid JSON.") from exc
        if not isinstance(payload, dict):
            raise HTTPException(status_code=400, detail="FSD request must be an object.")
        return await run_in_threadpool(_run_analysis, payload, use_core)
