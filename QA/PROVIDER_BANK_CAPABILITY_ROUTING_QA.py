"""Provider Bank capability-routing structural QA.

This test proves that specialist operation eligibility is decided by the
Provider Bank, before a provider call, and that HRN composition does not
silently acquire strict-schema decoding.
"""

from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]


def main():
    source = (ROOT / "provider_bank.py").read_text(encoding="utf-8")
    ast.parse(source, filename="provider_bank.py")

    import provider_bank as pb

    # Reset process-local routing state for deterministic structural tests.
    pb._STATE = {"models": {}, "provider_cursor": 0, "model_cursors": {}}

    # The bank, not HRN, owns the operation capability matrix.
    assert "MODEL_CAPABILITIES" in source
    assert "OPERATION_REQUIREMENTS" in source
    assert "def _eligible(provider, model, operation, schema=None):" in source
    assert "capability_and_provider_health_aware_self_healing" in source

    # A model with known structured output but observed long-composition
    # weakness must not be offered to HRN composition.
    eligible, missing = pb._eligible("groq", "qwen/qwen3.8-27b", "hrn_relational")
    assert not eligible
    assert "composition" in missing

    # The same model remains eligible for ordinary structured retrieval.
    eligible, missing = pb._eligible("groq", "qwen/qwen3.8-27b", "atlas_finder")
    assert eligible and not missing

    # HRN composition must not infer strict schema requirements.
    assert pb._operation_requirements("hrn_relational", None) == {
        "json_object", "long_context", "composition", "relational_analysis"
    }

    # Explicit schema requests are stricter by design.
    eligible, missing = pb._eligible(
        "groq", "openai/gpt-oss-20b", "hrn_relational",
        schema={"name": "explicit"}
    )
    assert eligible and not missing
    assert "json_schema_strict" in pb._operation_requirements(
        "hrn_relational", {"name": "explicit"}
    )

    # Unknown models are fail-closed rather than silently promoted by discovery.
    eligible, missing = pb._eligible("groq", "unknown-model", "atlas_finder")
    assert not eligible
    assert "json_object" in missing

    # Candidate selection must apply capability filtering before health probing.
    class Core:
        def get_live_groq_models(self):
            return [
                "openai/gpt-oss-20b",
                "qwen/qwen3.8-27b",
            ]

    pb._STATE = {"models": {}, "provider_cursor": 0, "model_cursors": {}}
    candidates = pb.candidates(Core(), operation="hrn_relational")
    models = [item["model"] for item in candidates]
    assert "openai/gpt-oss-20b" in models
    assert "qwen/qwen3.8-27b" not in models

    # The operation floor belongs to the bank and cannot be lowered by a
    # specialist transport envelope.
    assert pb.OPERATION_TOKEN_FLOORS["hrn_relational"] >= 900
    assert "effective_max_tokens = max(int(max_tokens)" in source

    # Strict schema is explicitly requested only; HRN composition has no
    # implicit operation schema.
    assert "hrn_relational_recovery" in pb.OPERATION_SCHEMAS
    assert pb.OPERATION_SCHEMAS["hrn_relational_recovery"]["strict"] is True
    assert "effective_schema = schema if isinstance(schema, dict) else None" in source
    assert "provider contract recovery" in source

    print("Provider Bank capability-routing structural QA: PASS")


if __name__ == "__main__":
    main()
