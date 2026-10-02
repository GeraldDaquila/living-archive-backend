"""Focused compatibility tests for the v487.85 production seam."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from shared_evidence import normalize_documents_for_use

def main() -> int:
    documents = [
        {
            "id": "doc-a",
            "title": "<b>Attention</b>",
            "url": "https://geralddaquila.com/attention/",
            "text": "<p>Attention is shaped by context.</p> https://example.org/ignored",
        },
        {
            "id": "doc-a-duplicate",
            "title": "Attention",
            "url": "https://geralddaquila.com/attention/",
            "text": "Duplicate.",
        },
        {"title": "HTTP", "url": "http://example.org/", "text": "Reject."},
        {"title": "No text", "url": "https://geralddaquila.com/no-text/"},
    ]
    actual = normalize_documents_for_use(documents, provenance="retrieved-context")
    assert actual == [{
        "id": "doc-a",
        "title": "Attention",
        "url": "https://geralddaquila.com/attention/",
        "text": "Attention is shaped by context.",
    }]

    canonical = normalize_documents_for_use([
        {
            "title": "Canonical",
            "canonical_url": "https://geralddaquila.com/canonical/",
            "excerpt": "<p>Canonical excerpt.</p>",
        }
    ])
    assert canonical == [{
        "id": "source:1",
        "title": "Canonical",
        "url": "https://geralddaquila.com/canonical/",
        "text": "Canonical excerpt.",
    }]

    malformed = normalize_documents_for_use([
        {"title": "bad", "url": "https://", "text": "x"},
        {"title": "bad2", "url": "javascript:alert(1)", "text": "x"},
        "not-a-document",
    ])
    assert malformed == []

    print("v487.85 seam regression tests: PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
