"""v488.76 provider-resilience structural QA.

Guards the provider seams that failed in live traces:
- retired Gemini defaults cannot return;
- Gemini 3.x transport does not send deprecated sampling parameters;
- provider-output contract failures are quarantined as model-health failures;
- the production identity advances with the provider-boundary repair.
"""

from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]


def _source(path):
    return (ROOT / path).read_text(encoding="utf-8")


def main():
    resilience = _source("provider_resilience.py")
    provider = _source("provider_bank.py")
    main_source = _source("main.py")

    ast.parse(resilience, filename="provider_resilience.py")
    ast.parse(provider, filename="provider_bank.py")
    ast.parse(main_source, filename="main.py")

    assert '["gemini-2.5-flash"]' not in provider
    assert '["gemini-3.8-flash"]' in provider

    gemini_start = provider.index("def _gemini(")
    gemini_end = provider.index("\ndef _openai_compatible", gemini_start)
    gemini = provider[gemini_start:gemini_end]

    assert '"maxOutputTokens": max_tokens' in gemini
    assert '"responseMimeType": "application/json"' in gemini
    assert '"thinkingConfig": {"thinkingLevel": "low"}' in gemini
    assert '"temperature": 0.0' not in gemini

    failure_start = provider.index("def _failure(")
    failure_end = provider.index("\ndef _success(", failure_start)
    failure = provider[failure_start:failure_end]

    assert '"structured_output_contract"' in failure
    assert '"response must contain exactly"' in failure
    assert 's["quarantine_until"] = "structured_output_contract", now + 3600' in failure

    assert 'APP_VERSION = "v488.75"' in main_source
    assert 'DEPLOYMENT_FINGERPRINT = "USE-v488.75-provider-health-boundary"' in main_source
    assert 'CANONICAL_BUILD_ID = "USE-BUILD-v488.75-provider-health-boundary"' in main_source

    print("v488.75 provider-bank structural QA: PASS")


if __name__ == "__main__":
    main()
