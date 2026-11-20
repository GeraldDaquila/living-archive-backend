from render import TaskContext, Workflows

app = Workflows()

@app.task(name="qa_healthcheck", timeout_seconds=60)
def qa_healthcheck(ctx: TaskContext) -> dict:
    return {
        "status": "ready",
        "purpose": "Standalone QA runner for Guide problem-boundary calibration",
    }

if __name__ == "__main__":
    app.start()
