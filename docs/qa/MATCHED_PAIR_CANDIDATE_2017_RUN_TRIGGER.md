# Candidate-local matched-pair QA run

This one-use QA branch is pinned to final candidate source commit `d6e6686f0e34ba03a7a1a4240320963e13dd4632` from PR #2018, which carries the PR #2017 implementation and regression corrections.

This marker commit triggers the dedicated GitHub Actions push gate. The application source, registry, held-out cases, and provider/model pins are inherited unchanged from the candidate source commit.

The capture is restricted to Groq `openai/gpt-oss-120b`, with the workflow's bounded timeout and inter-call spacing. No Render task or production deployment is involved.
