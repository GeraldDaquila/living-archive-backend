import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

os.environ["USE_REASONING_PROVIDER_MODE"] = "deterministic_only"
os.environ["USE_PINECONE_RETRIEVAL_BYPASS"] = "true"

from main import app


async def post_query(question: str) -> dict:
    body = json.dumps({"query": question, "history": []}).encode("utf-8")
    messages = []
    sent_body = False

    async def receive():
        nonlocal sent_body
        if not sent_body:
            sent_body = True
            return {"type": "http.request", "body": body, "more_body": False}
        return {"type": "http.disconnect"}

    async def send(message):
        messages.append(message)

    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/api/query",
        "raw_path": b"/api/query",
        "query_string": b"",
        "headers": [
            (b"host", b"guide-qa.local"),
            (b"content-type", b"application/json"),
            (b"content-length", str(len(body)).encode("ascii")),
            (b"accept", b"application/json"),
        ],
        "client": ("127.0.0.1", 12345),
        "server": ("127.0.0.1", 80),
    }
    await app(scope, receive, send)
    starts = [item for item in messages if item.get("type") == "http.response.start"]
    chunks = [item.get("body", b"") for item in messages if item.get("type") == "http.response.body"]
    if not starts:
        raise AssertionError(f"No HTTP response start for query: {question}")
    status = starts[-1].get("status")
    raw = b"".join(chunks)
    if status != 200:
        raise AssertionError(f"Guide API returned HTTP {status}: {raw.decode('utf-8', errors='replace')[:2000]}")
    return json.loads(raw.decode("utf-8"))


async def main():
    questions = (
        "What kinds of boundaries should be drawn around a problem, and what do they exclude?",
        "How should I define the boundaries around a system problem, and what stays outside scope?",
        "When framing a problem, what should be included and excluded?",
    )
    for question in questions:
        print("REQUEST", question, flush=True)
        result = await post_query(question)
        answer = result.get("response")
        doorway = result.get("recommendation") or result.get("canonical_doorway") or {}
        assert isinstance(answer, str), (question, type(answer).__name__)
        assert len(answer) > 700, (question, len(answer))
        assert "outside the chosen scope" in answer.casefold(), question
        assert doorway.get("title") == "Boundary Conditions", (question, doorway)
        assert doorway.get("url") == "https://geralddaquila.com/boundary-conditions/", (question, doorway)
        assert result.get("processing") == "task_specific_deterministic_recovery", (question, result.get("processing"))
        assert result.get("route_source") == "guide_early_deterministic_boundary", (question, result.get("route_source"))
        assert result.get("doorway_selection_source") == "registered_task_recovery", (question, result.get("doorway_selection_source"))
        assert result.get("response_provenance", {}).get("class") == "deterministic_recovery", question
        print("PASS", question, len(answer), doorway["title"], flush=True)


if __name__ == "__main__":
    asyncio.run(main())
