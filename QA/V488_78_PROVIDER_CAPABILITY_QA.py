"""Provider Bank capability arbitration structural QA for v488.78."""

from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]

def _source(path):
    return (ROOT / path).read_text(encoding="utf-8")

def main():
    source = _source("provider_bank.py")
    ast.parse(source, filename="provider_bank.py")

    assert 'CAPABILITY_POLICY_VERSION' in source or '"capability_policy_version": "1.3"' in source
    assert 'MODEL_CAPABILITIES' in source
    assert 'OPERATION_REQUIREMENTS' in source
    assert 'OPERATION_TOKEN_FLOORS' in source
    assert 'def _eligible(' in source
    assert 'def candidates(use_core, operation="generic", schema=None):' in source
    assert 'def select(use_core, operation="generic", schema=None):' in source
    assert 'effective_max_tokens = max(int(max_tokens), int(OPERATION_TOKEN_FLOORS.get(operation, 0)))' in source

    # The known live Qwen structured-output lane must not be eligible for the
    # long HRN composition operation merely because it supports JSON.
    assert '"composition"' not in source.split('("groq", "qwen/qwen3.8-27b"):', 1)[1].split('}),', 1)[0]

    # Capability policy must remain provider-neutral: operation selection is
    # expressed as required capabilities, not a named default LLM.
    assert 'hrn_relational": frozenset({"json_object", "long_context", "composition", "relational_analysis"})' in source
    assert 'provider=' in source and 'model=' in source

    print("v488.78 Provider Bank capability arbitration QA: PASS")

if __name__ == "__main__":
    main()
