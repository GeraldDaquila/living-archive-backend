import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

PORT = 10001
env = os.environ.copy()
env["PORT"] = str(PORT)
env["USE_REASONING_PROVIDER_MODE"] = "deterministic_only"
env["USE_PINECONE_RETRIEVAL_BYPASS"] = "true"
server = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", str(PORT)],
    env=env,
)


def ask(question: str) -> dict:
    body = json.dumps({"query": question, "history": []}).encode("utf-8")
    request = urllib.request.Request(
        f"http://127.0.0.1:{PORT}/api/query",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    deadline = time.monotonic() + 90
    last_error = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                payload = json.loads(response.read().decode("utf-8"))
                assert response.status == 200
                return payload
        except urllib.error.HTTPError as exc:
            body_text = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Guide QA API returned HTTP {exc.code}: {body_text[:2000]}"
            ) from exc
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            last_error = exc
            if server.poll() is not None:
                raise RuntimeError(f"Guide QA server exited: {exc}") from exc
            time.sleep(1)
    raise RuntimeError(f"Guide QA API timed out after 90 seconds: {last_error!r}")


try:
    print(f"Guide QA smoke server pid={server.pid}", flush=True)
    questions = (
        "What kinds of boundaries should be drawn around a problem, and what do they exclude?",
        "How should I define the boundaries around a system problem, and what stays outside scope?",
        "When framing a problem, what should be included and excluded?",
        "What should be inside the scope of a problem, and what should remain outside it?",
    )
    for question in questions:
        print("REQUEST", question, flush=True)
        result = ask(question)
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
finally:
    server.terminate()
    try:
        server.wait(timeout=10)
    except subprocess.TimeoutExpired:
        server.kill()
        server.wait(timeout=5)
