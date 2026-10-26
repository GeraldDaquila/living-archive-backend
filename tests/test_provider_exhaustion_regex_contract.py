"""Runtime boundary tests for provider-exhaustion definition recovery."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def test_exact_institutional_memory_question_matches_runtime_recovery_gate():
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    production_pattern = r'r"(?i)^what is (?:an? |the )?(.+?),? and why does it matter\??$"'
    production_normalizer = r're.sub(r"\s+", " ", str(query or "")).strip()'
    assert production_pattern in source
    assert production_normalizer in source

    query = "What is institutional memory, and why does it matter?"
    normalized = re.sub(r"\s+", " ", query).strip()
    match = re.match(
        r"(?i)^what is (?:an? |the )?(.+?),? and why does it matter\??$",
        normalized,
    )
    assert match
    assert match.group(1).strip(" ,;:").casefold() == "institutional memory"


def test_recovery_regressions_are_explicitly_invoked_by_composition_ci():
    workflow = (ROOT / ".github" / "workflows" / "general-guide-composition-contract.yml").read_text(encoding="utf-8")
    assert "tests/test_shared_definition_exhaustion_recovery.py" in workflow
    assert "tests/test_provider_exhaustion_regex_contract.py" in workflow
