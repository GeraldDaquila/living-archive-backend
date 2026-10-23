#!/usr/bin/env python3
"""Capture one real Guide API response for an explicitly selected registry candidate.

This is an opt-in QA utility, not a production runtime component. It performs exactly
one POST per invocation and refuses to send unless --confirm-live-request is supplied.
It never promotes captured output to an approved gold standard.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY = ROOT / "docs" / "qa" / "gold_standard_registry.json"
ALLOWED_HOSTS = {
    "living-archive-backend.onrender.com",
    "living-archive-backend-mirror.onrender.com",
}
CANDIDATE_STATUS = "MODEL_RECONSTRUCTION_CANDIDATE_NOT_LIVE_REPLAY"


def load_candidate(registry_path: Path, benchmark_id: str) -> dict:
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    matches = [r for r in registry.get("records", []) if r.get("benchmark_id") == benchmark_id]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one registry record for {benchmark_id!r}; found {len(matches)}")
    record = matches[0]
    if record.get("status") != CANDIDATE_STATUS:
        raise ValueError(f"Record status must be {CANDIDATE_STATUS}; got {record.get('status')!r}")
    if not record.get("query") or not record.get("reconstruction_candidate_response"):
        raise ValueError("Selected record is missing its query or labelled reconstruction candidate")
    if record.get("expected_response") is not None:
        raise ValueError("Refusing to replay a record that already has expected_response populated")
    return record


def validate_endpoint(endpoint: str) -> str:
    parsed = urlparse(endpoint)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS:
        raise ValueError("Endpoint must be HTTPS on the primary or mirror Living Archive Render host")
    if parsed.path.rstrip("/") not in {"", "/api/query"}:
        raise ValueError("Endpoint path must be the service root or /api/query")
    if parsed.query or parsed.fragment or parsed.username or parsed.password:
        raise ValueError("Endpoint must not contain query, fragment, or embedded credentials")
    return endpoint.rstrip("/") if parsed.path in {"", "/"} else endpoint


def capture_one(record: dict, endpoint: str, registry_commit: str, timeout: float = 75.0) -> dict:
    body = json.dumps({"query": record["query"], "history": []}, ensure_ascii=False).encode("utf-8")
    request = Request(endpoint, data=body, headers={
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "LivingArchive-GoldStandard-QA-Replay/1.0",
    }, method="POST")
    captured_at = datetime.now(timezone.utc).isoformat()
    try:
        with urlopen(request, timeout=timeout) as response:
            status = response.status
            response_bytes = response.read()
            response_headers = dict(response.headers.items())
    except HTTPError as exc:
        status = exc.code
        response_bytes = exc.read()
        response_headers = dict(exc.headers.items()) if exc.headers else {}
    except (URLError, TimeoutError) as exc:
        raise RuntimeError(f"Guide API request failed before a response was captured: {exc}") from exc

    response_text = response_bytes.decode("utf-8", errors="replace")
    try:
        payload = json.loads(response_text)
    except json.JSONDecodeError:
        payload = None
    return {
        "capture_type": "LIVE_GUIDE_API_REPLAY",
        "capture_status": "CAPTURED_HTTP_RESPONSE",
        "captured_at_utc": captured_at,
        "benchmark_id": record["benchmark_id"],
        "original_gold_standard_number": record.get("original_gold_standard_number"),
        "query": record["query"],
        "endpoint": endpoint,
        "http_status": status,
        "registry_commit": registry_commit or None,
        "application_version": payload.get("version") if isinstance(payload, dict) else None,
        "deployment_fingerprint": payload.get("fingerprint") if isinstance(payload, dict) else None,
        "source_sha256": payload.get("source_sha256") if isinstance(payload, dict) else None,
        "request_id": payload.get("request_id") if isinstance(payload, dict) else None,
        "response_sha256": hashlib.sha256(response_bytes).hexdigest(),
        "response_headers": {
            key: value for key, value in response_headers.items()
            if key.lower() in {"content-type", "date", "server", "x-render-origin-server"}
        },
        "response_payload": payload,
        "response_text": response_text if payload is None else None,
        "classification": "LIVE_CAPTURE_NOT_YET_REVIEWED",
        "historical_exact": False,
        "user_approved": False,
        "candidate_answer_for_comparison_only": record["reconstruction_candidate_response"],
        "evidence_boundary": (
            "This is the response captured by this one live API request at the stated time. "
            "It is not proof of the historical answer, does not prove the UI rendered it, "
            "and is not user-approved."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark-id", required=True, help="Exact registry benchmark_id; one question per invocation")
    parser.add_argument("--endpoint", required=True, help="HTTPS primary or mirror service URL, optionally ending in /api/query")
    parser.add_argument("--output", required=True, type=Path, help="Path to write the JSON capture")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--registry-commit", default=os.environ.get("QA_REGISTRY_COMMIT", ""))
    parser.add_argument("--confirm-live-request", action="store_true", help="Required explicit opt-in to send one live request")
    args = parser.parse_args()

    if not args.confirm_live_request:
        parser.error("refusing live traffic without --confirm-live-request")
    try:
        endpoint = validate_endpoint(args.endpoint)
        record = load_candidate(args.registry, args.benchmark_id)
        if endpoint.rstrip("/").endswith("/api/query"):
            api_endpoint = endpoint
        else:
            api_endpoint = endpoint.rstrip("/") + "/api/query"
        capture = capture_one(record, api_endpoint, args.registry_commit)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(capture, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"capture failed: {exc}", file=sys.stderr)
        return 2

    print(json.dumps({
        "capture_status": capture["capture_status"],
        "benchmark_id": capture["benchmark_id"],
        "http_status": capture["http_status"],
        "application_version": capture["application_version"],
        "request_id": capture["request_id"],
        "response_sha256": capture["response_sha256"],
        "output": str(args.output),
        "classification": capture["classification"],
    }, ensure_ascii=False))
    return 0 if capture["http_status"] == 200 and isinstance(capture["response_payload"], dict) else 1


if __name__ == "__main__":
    raise SystemExit(main())
