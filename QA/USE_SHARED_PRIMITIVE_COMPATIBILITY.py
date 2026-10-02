"""v487.84 compatibility harness between legacy USE transformations and
the isolated shared primitives.

The legacy implementation is copied here as a small test oracle rather than
imported from production. No production code is changed.
"""
from __future__ import annotations

import re

from shared_intelligence_primitives import (
    build_epistemic_tag,
    normalize_claims,
    normalize_doorway_candidates,
    normalize_evidence,
)


def legacy_clean(value) -> str:
    value = re.sub(r"<[^>]+>", " ", str(value or ""))
    value = re.sub(r"https?://\S+|www\.\S+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def legacy_normalize_documents(documents):
    output = []
    seen = set()
    for document in documents:
        if not isinstance(document, dict):
            continue
        title = legacy_clean(document.get("title"))
        url = str(document.get("url") or document.get("canonical_url") or "").strip()
        text = legacy_clean(
            document.get("text")
            or document.get("content")
            or document.get("excerpt")
        )
        if not title or not re.match(r"^https://\S+$", url, re.I) or not text:
            continue
        key = (url, title.casefold())
        if key in seen:
            continue
        seen.add(key)
        output.append(
            {
                "id": str(document.get("id") or f"source:{len(output) + 1}"),
                "title": title,
                "url": url,
                "text": text,
            }
        )
    return output


def legacy_claims(items, evidence_ids):
    allowed = {str(x) for x in evidence_ids}
    output = []
    seen = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        text = legacy_clean(item.get("text"))
        if not text:
            continue
        key = re.sub(r"\W+", " ", text.casefold()).strip()
        if not key or key in seen:
            continue
        seen.add(key)
        refs = tuple(str(ref) for ref in item.get("evidence_ids", ()) if str(ref) in allowed)
        claim_type = item.get("claim_type") or "exploration"
        epistemic = item.get("epistemic") or "uncertain"
        if claim_type not in {
            "definition", "relationship", "observation", "interpretation", "exploration"
        }:
            claim_type = "exploration"
        if epistemic not in {
            "supported", "inferred", "interpretive", "visitor-originated", "uncertain"
        }:
            epistemic = "uncertain"
        output.append(
            {
                "text": text,
                "evidence_ids": refs,
                "claim_type": claim_type,
                "epistemic": epistemic,
            }
        )
    return output


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
        {
            "title": "Reject me",
            "url": "http://example.org/",
            "text": "Not HTTPS.",
        },
    ]

    legacy_docs = legacy_normalize_documents(documents)
    shared_docs = normalize_evidence(documents)
    assert [
        (d["title"], d["url"], d["text"]) for d in legacy_docs
    ] == [
        (d.title, d.url, d.text) for d in shared_docs
    ]

    legacy_claim_list = legacy_claims(
        [
            {
                "text": "Attention is shaped by context.",
                "evidence_ids": ["doc-a"],
                "claim_type": "observation",
                "epistemic": "supported",
            },
            {
                "text": "Attention is shaped by context.",
                "evidence_ids": ["doc-a"],
                "claim_type": "observation",
                "epistemic": "supported",
            },
            {
                "text": "This is an interpretation.",
                "evidence_ids": ["missing"],
                "claim_type": "interpretation",
                "epistemic": "interpretive",
            },
        ],
        evidence_ids=["doc-a"],
    )
    shared_claim_list = normalize_claims(
        [
            {
                "text": "Attention is shaped by context.",
                "evidence_ids": ["doc-a"],
                "claim_type": "observation",
                "epistemic": "supported",
            },
            {
                "text": "Attention is shaped by context.",
                "evidence_ids": ["doc-a"],
                "claim_type": "observation",
                "epistemic": "supported",
            },
            {
                "text": "This is an interpretation.",
                "evidence_ids": ["missing"],
                "claim_type": "interpretation",
                "epistemic": "interpretive",
            },
        ],
        evidence_ids=["doc-a"],
    )
    assert [
        (x["text"], x["evidence_ids"], x["claim_type"], x["epistemic"])
        for x in legacy_claim_list
    ] == [
        (x.text, x.evidence_ids, x.claim_type, x.epistemic)
        for x in shared_claim_list
    ]

    assert build_epistemic_tag(supported=True) == "supported"
    assert build_epistemic_tag(interpretive=True) == "interpretive"
    assert build_epistemic_tag(visitor_originated=True, supported=True) == "visitor-originated"
    assert build_epistemic_tag(uncertain=True, supported=True) == "uncertain"

    candidate_maps = [
        {
            "title": "Attention",
            "url": "https://geralddaquila.com/attention/",
            "relevance_basis": "direct",
            "source_ids": ["doc-a"],
            "candidate_rank": 1,
        },
        {
            "title": "Attention",
            "url": "https://geralddaquila.com/attention/",
            "relevance_basis": "duplicate",
        },
    ]
    doorways = normalize_doorway_candidates(candidate_maps)
    assert len(doorways) == 1
    assert doorways[0].title == "Attention"
    assert doorways[0].url.endswith("/attention/")

    print("v487.84 USE/shared primitive compatibility: PASS")
    print("document normalization: equivalent")
    print("claim normalization: equivalent")
    print("epistemic tagging: equivalent")
    print("doorway candidate normalization: bounded")
    print("production runtime: untouched")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
