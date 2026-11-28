#!/usr/bin/env python3
"""Audit repeated approved Gold Star questions and their explicit exemplar lineage.

This is an audit/reporting layer only. It never edits, renumbers, merges, or
changes authority on canonical registry records. Semantic similarity is not
inferred: families are grouped only by normalized exact question text.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "docs" / "qa" / "gold_star_registry.json"
APPROVED_STATUS = "USER_APPROVED_GOLD_STANDARD"
QUALITY_CLASS = "user_approved_response_quality_exemplar"


def normalize_question(value: str | None) -> str:
    """Match the registry validator's exact-question normalization."""
    text = unicodedata.normalize("NFKC", str(value or ""))
    text = re.sub(r"[‐‑‒–—−]", "-", text)
    text = re.sub(r"[‘’ʼ＇]", "'", text)
    text = re.sub(r"\s+", " ", text).strip().lower()
    return re.sub(r"[?.!]+$", "", text).strip()


def _capabilities(record: dict) -> dict:
    return record.get("gold_star_capabilities") or {}


def _is_quality_exemplar(record: dict) -> bool:
    return _capabilities(record).get("generation_class") == QUALITY_CLASS


def classify_family(records: list[dict]) -> tuple[str, list[dict]]:
    """Classify a repeated exact-question group using explicit record links."""
    by_id = {item.get("benchmark_id"): item for item in records}
    edges = []

    for item in records:
        item_id = item.get("benchmark_id")
        predecessor_id = str(item.get("replaces_exact_query_runtime_authority_of") or "").strip()
        successor_id = str(item.get("superseded_by_benchmark_id") or "").strip()
        paired_id = str(item.get("paired_active_benchmark_id") or "").strip()

        if predecessor_id in by_id:
            predecessor = by_id[predecessor_id]
            reciprocal = predecessor.get("runtime_exact_query_successor") == item_id
            if reciprocal:
                edges.append({"type": "exact_query_successor", "from": predecessor_id, "to": item_id})
        if successor_id in by_id:
            successor = by_id[successor_id]
            reciprocal = successor.get("replaces_exact_query_runtime_authority_of") == item_id
            if reciprocal:
                edges.append({"type": "superseded_historical_reference", "from": item_id, "to": successor_id})
        if paired_id in by_id:
            edges.append({"type": "paired_response_quality_exemplar", "from": paired_id, "to": item_id})

    edge_types = {edge["type"] for edge in edges}
    if "exact_query_successor" in edge_types and "superseded_historical_reference" in edge_types:
        family_type = "explicit_successor_and_supersession_lineage"
    elif "exact_query_successor" in edge_types:
        family_type = "explicit_exact_query_successor_lineage"
    elif "superseded_historical_reference" in edge_types:
        family_type = "explicit_supersession_lineage"
    elif "paired_response_quality_exemplar" in edge_types:
        family_type = "explicit_paired_response_quality_exemplar"
    elif all(
        _is_quality_exemplar(item)
        and _capabilities(item).get("standalone_response_quality_exemplar") is True
        and not item.get("replaces_exact_query_runtime_authority_of")
        and not item.get("superseded_by_benchmark_id")
        and not item.get("paired_active_benchmark_id")
        for item in records
    ):
        family_type = "multiple_standalone_response_quality_exemplars"
    else:
        family_type = "REVIEW_REQUIRED"

    return family_type, edges


def build_audit(registry: dict) -> dict:
    records = registry.get("records") or []
    approved = [item for item in records if item.get("status") == APPROVED_STATUS]
    groups = defaultdict(list)
    for item in approved:
        normalized = normalize_question(item.get("query"))
        if normalized:
            groups[normalized].append(item)

    families = []
    for normalized, members in sorted(groups.items()):
        if len(members) < 2:
            continue
        family_type, edges = classify_family(members)
        answer_groups = defaultdict(list)
        for item in members:
            answer = re.sub(r"\s+", " ", str(item.get("expected_response") or "")).strip()
            if answer:
                answer_hash = hashlib.sha256(answer.encode("utf-8")).hexdigest()
                answer_groups[answer_hash].append(item.get("benchmark_id"))
        duplicate_answers = [ids for ids in answer_groups.values() if len(ids) > 1]
        family_id = "qf-" + hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
        families.append({
            "family_id": family_id,
            "normalized_question": normalized,
            "display_question": members[0].get("query"),
            "family_type": family_type,
            "record_count": len(members),
            "distinct_response_count": len(answer_groups),
            "identical_response_groups": duplicate_answers,
            "lineage_edges": edges,
            "benchmark_ids": sorted(item.get("benchmark_id") for item in members),
        })

    review_required = [item for item in families if item["family_type"] == "REVIEW_REQUIRED"]
    return {
        "audit_version": "1.0.0",
        "registry_id": registry.get("registry_id"),
        "approved_record_count": len(approved),
        "unique_normalized_question_family_count": len(groups),
        "repeated_question_family_count": len(families),
        "repeated_question_record_count": sum(item["record_count"] for item in families),
        "identical_response_group_count": sum(bool(item["identical_response_groups"]) for item in families),
        "review_required_family_count": len(review_required),
        "families": families,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    registry = json.loads(args.registry.read_text(encoding="utf-8"))
    report = build_audit(registry)
    rendered = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(
        "GOLD STAR QUESTION-FAMILY AUDIT: "
        f"{report['unique_normalized_question_family_count']} unique normalized question families; "
        f"{report['repeated_question_family_count']} repeated families; "
        f"{report['review_required_family_count']} require review; "
        f"{report['identical_response_group_count']} identical-answer groups"
    )
    if report["review_required_family_count"] or report["identical_response_group_count"]:
        print(rendered)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
