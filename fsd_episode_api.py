"""Authenticated episode-based FSD endpoint on the existing USE application."""
from __future__ import annotations

import json
from typing import Any

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from fsd_api import (
    MAX_BODY_BYTES,
    _check_rate_limit,
    authorize_provider_gateway,
    execute_provider_gateway,
)
from fsd_episode_contract import (
    CONTRACT_VERSION,
    FSDEpisodeContractError,
    ENUMS,
    validate_episode_payload,
)
from fsd_episode_report_contract import (
    FSDEpisodeReportError,
    validate_episode_report,
)
from fsd_runtime import parse_evidence

_REGISTERED_APPS = set()

REPORT_SCHEMA = {
    "name": "fsd_episode_report",
    "strict": False,
    "schema": {
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
            "episode_observation": {"type": "string"},
            "strengths": {"type": "array", "items": {"type": "string"}},
            "enabling_conditions": {"type": "array", "items": {"type": "string"}},
            "constraints": {"type": "array", "items": {"type": "string"}},
            "next_steps": {"type": "array", "items": {"type": "string"}},
            "archive_reference_ids": {"type": "array", "items": {"type": "string"}},
        },
        "required": [
            "summary", "episode_observation", "strengths", "enabling_conditions",
            "constraints", "next_steps", "archive_reference_ids",
        ],
        "additionalProperties": False,
    },
}

QUESTION_LABELS = {
    "scale": "Selected system boundary",
    "prior_understanding": "Prior understanding",
    "experience_type": "Consequential experience",
    "consequence_significance": "Consequence significance",
    "understanding_after": "Understanding after the experience",
    "reconsideration_basis": "Relationship between experience and reconsideration",
    "subsequent_response": "Subsequent response",
    "understanding_action_link": "Connection between understanding and response",
    "response_available": "Availability of meaningful response",
    "non_change_reason": "Reason for non-change or delay",
}


def _archive_context(use_core: Any) -> list[dict[str, Any]]:
    """Best-effort conceptual retrieval; never treated as episode corroboration."""
    queries = (
        "Living Archive conceptual explanation of Correspondence: consequential experience influencing understanding.",
        "Living Archive conceptual explanation of Correctability: revised understanding influencing subsequent decision or action.",
    )
    references: list[dict[str, Any]] = []
    seen = set()
    for query in queries:
        try:
            context = use_core.fetch_canonical_context(query)
        except Exception:
            continue
        for item in parse_evidence(context):
            url = item.get("url")
            if not url or url in seen:
                continue
            seen.add(url)
            references.append({
                "reference_id": f"A{len(references) + 1:02d}",
                "title": item["title"],
                "url": url,
                "excerpt": item["excerpt"],
            })
            if len(references) >= 6:
                return references
    return references


def _compose_episode_report(episode: dict[str, Any], references: list[dict[str, Any]], use_core: Any) -> dict[str, Any]:
    reported_answers = [
        {"question": QUESTION_LABELS[key], "selected_response": value}
        for key, value in episode.items()
        if key in QUESTION_LABELS
    ]
    context = [
        {"reference_id": item["reference_id"], "title": item["title"], "excerpt": item["excerpt"]}
        for item in references
    ]
    system = (
        "Prepare a cautious, appreciative reflection on exactly one respondent-reported episode. "
        "The structured answers are self-reported, not independently verified. Do not infer "
        "a stable system trait, institutional performance, causation, population pattern, or "
        "capacity beyond this episode. A decision not to change may be appropriate when change "
        "is unwarranted; more evidence, time, authority, or resources may be needed. Never call "
        "'not demonstrated' incapable or failed. Separate strengths, enabling conditions, "
        "constraints, and practical next steps. Do not invent strengths or enabling conditions: "
        "include them only when directly supported by the respondent's structured selections; "
        "otherwise return an empty list. Do not infer positive outcomes, successful learning, "
        "or effective governance from the mere presence of feedback, documentation, or an action. "
        "Next steps must be clearly framed as suggestions, not claims about what happened. "
        "Living Archive references are conceptual context only; they do not verify that the episode "
        "occurred and must not be described as evidence corroborating the respondent. Use only "
        "supplied Archive reference IDs. Return exactly the required JSON fields. Do not include "
        "internal reasoning labels or provider details."
    )
    user = {
        "contract_version": CONTRACT_VERSION,
        "respondent_reported_episode": reported_answers,
        "living_archive_conceptual_context_only": context,
        "limits": {
            "one_episode_only": True,
            "archive_does_not_corroborate_episode": True,
            "no_stable_capacity_claim": True,
            "max_list_items": 4,
            "max_item_characters": 260,
            "max_text_characters": 700,
            "max_archive_reference_ids": 6,
        },
    }
    try:
        result = execute_provider_gateway(
            operation="fsd_report_composition",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
            ],
            max_tokens=1100,
            use_core=use_core,
            schema=REPORT_SCHEMA,
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail={"code": "fsd_provider_bank_unavailable"}) from exc
    if not result.get("ok"):
        raise HTTPException(status_code=503, detail={"code": "fsd_provider_bank_unavailable"})
    try:
        report = validate_episode_report(result.get("result"), episode, references)
    except FSDEpisodeReportError as exc:
        raise HTTPException(status_code=502, detail={"code": "fsd_episode_report_rejected"}) from exc
    return {"ok": True, "contract_version": CONTRACT_VERSION, "report": report}


def _run_episode_analysis(payload: dict[str, Any], use_core: Any) -> dict[str, Any]:
    try:
        episode = validate_episode_payload(payload)
    except FSDEpisodeContractError as exc:
        raise HTTPException(status_code=400, detail={"code": "invalid_fsd_episode_request"}) from exc
    references = _archive_context(use_core)
    return _compose_episode_report(episode, references, use_core)


def register_fsd_episode_routes(app: Any, use_core: Any) -> None:
    """Register the versioned episode route once on the existing USE app."""
    app_id = id(app)
    if app_id in _REGISTERED_APPS:
        return
    _REGISTERED_APPS.add(app_id)

    @app.post("/api/fsd/analyze-episode")
    async def fsd_analyze_episode(request: Request):
        authorize_provider_gateway(request.headers.get("X-Living-Archive-Provider-Key"))
        _check_rate_limit("authenticated_fsd_ingress")
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > MAX_BODY_BYTES:
                    raise HTTPException(status_code=413, detail="FSD request is too large.")
            except ValueError as exc:
                raise HTTPException(status_code=400, detail="Invalid content length.") from exc
        chunks = []
        total = 0
        async for chunk in request.stream():
            total += len(chunk)
            if total > MAX_BODY_BYTES:
                raise HTTPException(status_code=413, detail="FSD request is too large.")
            chunks.append(chunk)
        try:
            payload = json.loads(b"".join(chunks).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise HTTPException(status_code=400, detail="FSD request must be valid JSON.") from exc
        if not isinstance(payload, dict):
            raise HTTPException(status_code=400, detail="FSD request must be an object.")
        result = await run_in_threadpool(_run_episode_analysis, payload, use_core)
        return JSONResponse(
            content=result,
            headers={
                "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
                "Pragma": "no-cache",
            },
        )
