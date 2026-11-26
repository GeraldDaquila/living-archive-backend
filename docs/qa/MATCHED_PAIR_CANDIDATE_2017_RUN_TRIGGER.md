# Candidate-local matched-pair QA run

This one-use QA branch is a merge snapshot of current `main` at commit `6cbec8a8180a2285517f79b1c0dd9465f0c0fded`. It preserves the dedicated QA marker and uses the exact current production candidate source, registry, and held-out case set.

This marker update requests the dedicated GitHub Actions push gate. The provider-backed capture is restricted to Groq `openai/gpt-oss-120b`, with the workflow's bounded timeout and inter-call spacing. No Render task or production deployment is involved.

The capture is an experiment: it does not by itself establish Gold Star efficacy. Blind-review evidence and the unblinding key are retained as separate workflow artifacts.
