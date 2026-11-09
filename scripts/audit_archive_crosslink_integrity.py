"""Read-only integrity audit for the published Living Archive crosslink snapshot.

This command compares the versioned v2 snapshot with an independently collected
published WordPress posts/pages registry. It never writes to WordPress, the
snapshot, the checksum, Pinecone, or the running Guide.

Usage:
  python -m scripts.audit_archive_crosslink_integrity
  python -m scripts.audit_archive_crosslink_integrity --skip-link-check
  python -m scripts.audit_archive_crosslink_integrity --output-dir ./audit-output

Reachability is reported as a metadata-addressability diagnostic, not as a
proof that a URL will be selected for every possible visitor question.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import time
import unicodedata
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_PATH = ROOT / "archive_crosslink_snapshot.json"
CHECKSUM_PATH = ROOT / "archive_crosslink_snapshot.sha256"
WP_API = "https://geralddaquila.com/wp-json/wp/v2"
PAGE_SIZE = 100
MAX_PAGES = 50
REQUEST_TIMEOUT = 12
LINK_TIMEOUT = 8
USER_AGENT = "LivingArchiveTerritorialIntegrityAudit/1.0"
AUDIT_VERSION = "1.0.0"


def clean_text(value: Any, limit: int = 1000) -> str:
    if isinstance(value, dict):
        value = value.get("rendered", "")
    if not isinstance(value, (str, int, float)):
        return ""
    text = html.unescape(re.sub(r"<[^>]*>", " ", str(value)))
    return re.sub(r"\s+", " ", text).strip()[:limit]


def normalize_url(value: Any) -> str:
    raw = clean_text(value, 2000)
    if not raw:
        return ""
    parts = urlsplit(raw)
    if parts.scheme.lower() != "https" or parts.netloc.lower() != "geralddaquila.com":
        return ""
    # Canonicalize trailing slash and host case; preserve path case and query.
    path = parts.path.rstrip("/")
    return urlunsplit(("https", "geralddaquila.com", path, parts.query, ""))


def title_key(value: Any) -> str:
    normalized = unicodedata.normalize("NFKC", clean_text(value, 1000)).casefold()
    return re.sub(r"\W+", " ", normalized, flags=re.UNICODE).strip()


def digest_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load_snapshot(path: Path) -> tuple[dict[str, Any], str, int]:
    raw = path.read_bytes()
    snapshot = json.loads(raw.decode("utf-8"))
    if not isinstance(snapshot, dict):
        raise ValueError("Snapshot root must be a JSON object")
    if snapshot.get("contract") != "archive-crosslink-inventory-v2":
        raise ValueError("Only archive-crosslink-inventory-v2 is supported")
    if snapshot.get("source") != "wordpress-canonical-registry":
        raise ValueError("Snapshot source is not wordpress-canonical-registry")
    if snapshot.get("crosslink_ready") is not True or snapshot.get("complete") is not True:
        raise ValueError("Snapshot is not marked complete and crosslink-ready")
    assets = snapshot.get("assets")
    if not isinstance(assets, list):
        raise ValueError("Snapshot assets must be a list")
    return snapshot, digest_bytes(raw), len(raw)


def load_checksum(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip().split()[0].lower()


def fetch_registry_type(post_type: str) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    page_reports: list[dict[str, Any]] = []
    for page in range(1, MAX_PAGES + 1):
        url = (
            f"{WP_API}/{post_type}?per_page={PAGE_SIZE}&page={page}"
            "&status=publish&_fields=id,link,title,modified"
        )
        request = Request(url, headers={"Accept": "application/json", "User-Agent": USER_AGENT})
        started = time.monotonic()
        try:
            with urlopen(request, timeout=REQUEST_TIMEOUT) as response:
                payload = json.loads(response.read().decode("utf-8"))
                headers = response.headers
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"WordPress {post_type} page {page} failed: {type(exc).__name__}: {exc}") from exc
        if not isinstance(payload, list):
            raise RuntimeError(f"WordPress {post_type} page {page} returned a non-list payload")
        page_reports.append({
            "page": page,
            "records": len(payload),
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "total_header": headers.get("X-WP-Total"),
            "total_pages_header": headers.get("X-WP-TotalPages"),
        })
        for item in payload:
            if not isinstance(item, dict):
                continue
            wp_id = str(item.get("id") or "").strip()
            title = clean_text(item.get("title"))
            url = normalize_url(item.get("link"))
            if not wp_id.isdigit():
                continue
            records.append({
                "wp_id": wp_id,
                "post_type": post_type[:-1],
                "title": title,
                "title_key": title_key(title),
                "url": url,
                "modified": clean_text(item.get("modified"), 100),
            })
        total_pages = headers.get("X-WP-TotalPages")
        if total_pages and page >= int(total_pages):
            break
        if len(payload) < PAGE_SIZE:
            break
    else:
        raise RuntimeError(f"WordPress {post_type} registry exceeded {MAX_PAGES} pages")
    return {
        "records": records,
        "pages": page_reports,
        "total_header": page_reports[0]["total_header"] if page_reports else None,
        "total_pages_header": page_reports[0]["total_pages_header"] if page_reports else None,
    }


def grouped_duplicates(records: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        key = record.get(field) or ""
        if key:
            grouped[str(key)].append(record)
    output = []
    for key, matches in sorted(grouped.items()):
        if len(matches) > 1:
            output.append({
                "key": key,
                "count": len(matches),
                "records": [
                    {k: record.get(k) for k in ("wp_id", "post_type", "title", "url")}
                    for record in matches
                ],
            })
    return output


def compare_registry(snapshot_assets: list[dict[str, Any]], registry: list[dict[str, Any]]) -> dict[str, Any]:
    snapshot_by_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    registry_by_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for asset in snapshot_assets:
        wp_id = str(asset.get("wp_id") or "").strip()
        if wp_id:
            snapshot_by_id[wp_id].append(asset)
    for record in registry:
        registry_by_id[str(record["wp_id"])].append(record)

    snapshot_ids = set(snapshot_by_id)
    registry_ids = set(registry_by_id)
    missing_ids = sorted(registry_ids - snapshot_ids, key=int)
    stale_ids = sorted(snapshot_ids - registry_ids, key=int)
    identity_mismatch = []
    for wp_id in sorted(snapshot_ids & registry_ids, key=int):
        snap = snapshot_by_id[wp_id][0]
        canon = registry_by_id[wp_id][0]
        if normalize_url(snap.get("url")) != canon.get("url") or title_key(snap.get("title")) != canon.get("title_key"):
            identity_mismatch.append({
                "wp_id": wp_id,
                "snapshot": {"title": snap.get("title"), "url": snap.get("url")},
                "wordpress": {"title": canon.get("title"), "url": canon.get("url")},
            })
    return {
        "registry_identity_count": len(registry_ids),
        "snapshot_identity_count": len(snapshot_ids),
        "registry_record_count": len(registry),
        "snapshot_asset_count": len(snapshot_assets),
        "missing_wp_ids": missing_ids,
        "stale_wp_ids": stale_ids,
        "duplicate_wp_ids_in_registry": grouped_duplicates(registry, "wp_id"),
        "duplicate_wp_ids_in_snapshot": grouped_duplicates([
            {"wp_id": str(a.get("wp_id") or ""), "post_type": a.get("resource_type"), "title": a.get("title"), "url": a.get("url")}
            for a in snapshot_assets
        ], "wp_id"),
        "identity_mismatches": identity_mismatch,
        "duplicate_canonical_urls_in_registry": grouped_duplicates(registry, "url"),
        "duplicate_canonical_urls_in_snapshot": grouped_duplicates([
            {"wp_id": str(a.get("wp_id") or ""), "post_type": a.get("resource_type"), "title": a.get("title"), "url": normalize_url(a.get("url"))}
            for a in snapshot_assets
        ], "url"),
        "duplicate_normalized_titles_in_registry": grouped_duplicates(registry, "title_key"),
        "duplicate_normalized_titles_in_snapshot": grouped_duplicates([
            {"wp_id": str(a.get("wp_id") or ""), "post_type": a.get("resource_type"), "title": a.get("title"), "url": a.get("url"), "title_key": title_key(a.get("title"))}
            for a in snapshot_assets
        ], "title_key"),
    }


def metadata_addressability(assets: list[dict[str, Any]]) -> dict[str, Any]:
    # This mirrors the selector's usable fields without importing production code
    # or coupling this audit command to visitor runtime imports.
    addressable = []
    non_addressable = []
    for asset in assets:
        title = clean_text(asset.get("title"))
        summary = clean_text(asset.get("summary"))
        resource_type = clean_text(asset.get("resource_type"))
        url = normalize_url(asset.get("url"))
        reason = []
        if not title:
            reason.append("missing_title")
        if not url:
            reason.append("invalid_or_missing_canonical_url")
        searchable_text = " ".join((title, summary, resource_type)).strip()
        if len(searchable_text) < 3:
            reason.append("insufficient_searchable_metadata")
        record = {
            "wp_id": str(asset.get("wp_id") or ""),
            "title": title,
            "url": url,
            "resource_type": resource_type,
            "summary_present": bool(summary),
        }
        if reason:
            non_addressable.append({**record, "reasons": reason})
        else:
            addressable.append(record)
    return {
        "addressable_count": len(addressable),
        "non_addressable_count": len(non_addressable),
        "addressable_assets": addressable,
        "non_addressable_assets": non_addressable,
        "definition": "Addressability checks presence of title, canonical URL, and resource type. It is not proof of relevance for every possible visitor query.",
    }


def check_destination(asset: dict[str, Any]) -> dict[str, Any]:
    url = normalize_url(asset.get("url"))
    base = {"wp_id": str(asset.get("wp_id") or ""), "title": clean_text(asset.get("title")), "url": url}
    if not url:
        return {**base, "status": "invalid_url", "http_status": None, "final_url": None}
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,*/*;q=0.8"}, method="HEAD")
    try:
        with urlopen(request, timeout=LINK_TIMEOUT) as response:
            return {
                **base,
                "status": "ok" if 200 <= response.status < 400 else "http_error",
                "http_status": response.status,
                "final_url": response.geturl(),
            }
    except HTTPError as exc:
        # Some hosts reject HEAD while allowing GET. Try a bounded GET for common cases.
        if exc.code not in (403, 405, 501):
            return {**base, "status": "http_error", "http_status": exc.code, "final_url": exc.geturl()}
    except (URLError, TimeoutError) as exc:
        return {**base, "status": "network_error", "http_status": None, "error": type(exc).__name__, "final_url": None}
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,*/*;q=0.8", "Range": "bytes=0-0"}, method="GET")
    try:
        with urlopen(request, timeout=LINK_TIMEOUT) as response:
            return {
                **base,
                "status": "ok" if 200 <= response.status < 400 else "http_error",
                "http_status": response.status,
                "final_url": response.geturl(),
                "method": "GET",
            }
    except HTTPError as exc:
        return {**base, "status": "http_error", "http_status": exc.code, "final_url": exc.geturl(), "method": "GET"}
    except (URLError, TimeoutError) as exc:
        return {**base, "status": "network_error", "http_status": None, "error": type(exc).__name__, "final_url": None, "method": "GET"}


def build_report(snapshot: dict[str, Any], snapshot_sha: str, snapshot_bytes: int,
                 checksum_expected: str, registry_data: dict[str, Any],
                 link_results: list[dict[str, Any]], link_check_performed: bool) -> dict[str, Any]:
    assets = snapshot.get("assets", [])
    posts = registry_data["posts"]["records"]
    pages = registry_data["pages"]["records"]
    registry = posts + pages
    comparison = compare_registry(assets, registry)
    addressability = metadata_addressability(assets)
    refreshed_at = float(snapshot.get("refreshed_at") or 0)
    age_seconds = max(0.0, time.time() - refreshed_at)
    actual_sha_matches = bool(checksum_expected and checksum_expected == snapshot_sha)
    broken = [item for item in link_results if item["status"] != "ok"]
    redirects = [item for item in link_results if item.get("status") == "ok" and normalize_url(item.get("final_url")) != item.get("url")]
    canonical_match = not (
        comparison["missing_wp_ids"] or comparison["stale_wp_ids"] or comparison["identity_mismatches"]
        or comparison["duplicate_wp_ids_in_registry"] or comparison["duplicate_wp_ids_in_snapshot"]
    )
    links_ok = link_check_performed and not broken
    complete = bool(
        actual_sha_matches and canonical_match and comparison["snapshot_identity_count"] == len(assets)
        and addressability["non_addressable_count"] == 0 and links_ok
    )
    return {
        "audit_contract": "crosslink-territorial-integrity-v1",
        "audit_version": AUDIT_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "read-only-wordpress-canonical-registry-and-versioned-snapshot",
        "production_mutations_performed": False,
        "pinecone_access_performed": False,
        "snapshot": {
            "path": str(SNAPSHOT_PATH.name),
            "contract": snapshot.get("contract"),
            "source": snapshot.get("source"),
            "asset_count_declared": snapshot.get("asset_count"),
            "asset_count_actual": len(assets),
            "refreshed_at": datetime.fromtimestamp(refreshed_at, timezone.utc).isoformat() if refreshed_at else None,
            "age_seconds": round(age_seconds, 1),
            "age_days": round(age_seconds / 86400, 2),
            "checksum": {"expected": checksum_expected or None, "actual": snapshot_sha, "matches": actual_sha_matches},
            "bytes": snapshot_bytes,
        },
        "wordpress_registry": {
            "posts": {
                "record_count": len(posts),
                "page_count": len(registry_data["posts"]["pages"]),
                "rest_total_header": registry_data["posts"]["total_header"],
                "rest_total_pages_header": registry_data["posts"]["total_pages_header"],
            },
            "pages": {
                "record_count": len(pages),
                "page_count": len(registry_data["pages"]["pages"]),
                "rest_total_header": registry_data["pages"]["total_header"],
                "rest_total_pages_header": registry_data["pages"]["total_pages_header"],
            },
            "total_records": len(registry),
        },
        "canonical_identity": comparison,
        "metadata_addressability": addressability,
        "destination_integrity": {
            "performed": link_check_performed,
            "checked_count": len(link_results),
            "broken_count": len(broken),
            "redirect_count": len(redirects),
            "results": link_results,
        },
        "overall_status": "COMPLETE" if complete else "ATTENTION REQUIRED",
        "completeness_gates": {
            "snapshot_checksum_matches": actual_sha_matches,
            "canonical_identity_reconciled": canonical_match,
            "all_snapshot_assets_have_unique_wp_identity": comparison["snapshot_identity_count"] == len(assets),
            "all_assets_metadata_addressable": addressability["non_addressable_count"] == 0,
            "destination_check_performed": link_check_performed,
            "no_broken_destinations": link_check_performed and not broken,
        },
        "notes": [
            "This is a read-only diagnostic. It never mutates WordPress, the snapshot, Pinecone, or production runtime.",
            "Duplicate titles and URLs are reported as evidence for human review; they are not silently treated as interchangeable identities.",
            "Addressability is a necessary metadata condition, not proof that each asset is semantically reachable for every query.",
            "A complete status requires a full destination check. Use --skip-link-check only for a faster identity-only diagnostic, which will remain ATTENTION REQUIRED.",
        ],
    }


def render_markdown(report: dict[str, Any]) -> str:
    snap = report["snapshot"]
    wp = report["wordpress_registry"]
    identity = report["canonical_identity"]
    address = report["metadata_addressability"]
    links = report["destination_integrity"]
    gates = report["completeness_gates"]
    rows = [
        "# Crosslink Territorial Integrity",
        "",
        f"- Generated: {report['generated_at']}",
        f"- Overall status: **{report['overall_status']}**",
        f"- Snapshot refreshed: {snap['refreshed_at']} ({snap['age_days']} days old)",
        f"- Snapshot checksum: {'PASS' if gates['snapshot_checksum_matches'] else 'FAIL'}",
        "",
        "| Measure | Result |",
        "|---|---:|",
        f"| WordPress published posts | {wp['posts']['record_count']} |",
        f"| WordPress published pages | {wp['pages']['record_count']} |",
        f"| WordPress published records | {wp['total_records']} |",
        f"| Snapshot assets | {snap['asset_count_actual']} |",
        f"| Snapshot identity coverage | {identity['snapshot_identity_count']} / {identity['registry_identity_count']} ({(identity['snapshot_identity_count'] / max(1, identity['registry_identity_count']) * 100):.2f}%) |",
        f"| Missing WordPress IDs | {len(identity['missing_wp_ids'])} |",
        f"| Stale snapshot IDs | {len(identity['stale_wp_ids'])} |",
        f"| Duplicate IDs in WordPress | {len(identity['duplicate_wp_ids_in_registry'])} |",
        f"| Duplicate canonical URLs in WordPress | {len(identity['duplicate_canonical_urls_in_registry'])} |",
        f"| Duplicate titles in WordPress | {len(identity['duplicate_normalized_titles_in_registry'])} |",
        f"| Identity mismatches | {len(identity['identity_mismatches'])} |",
        f"| Metadata-addressable assets | {address['addressable_count']} / {snap['asset_count_actual']} |",
        f"| Non-addressable assets | {address['non_addressable_count']} |",
        f"| Destinations checked | {links['checked_count']} |",
        f"| Broken destinations | {links['broken_count']} |",
        f"| Redirects | {links['redirect_count']} |",
        "",
        "## Completeness gates",
        "",
    ]
    for gate, passed in gates.items():
        rows.append(f"- [{'x' if passed else ' '}] {gate.replace('_', ' ')}")
    rows += [
        "",
        "## Interpretation",
        "",
        "A duplicate title does not mean two WordPress IDs are the same asset. A duplicate URL does not mean the ID can be discarded without an explicit canonicalization rule. Review the detailed JSON findings before changing publisher behavior.",
        "",
        "Metadata addressability means an asset has a title, a valid canonical URL, and a resource type. It does not prove relevance for every visitor query; selector-level reachability should be separately measured by query fixtures.",
        "",
        "## Detailed discrepancy files",
        "",
        "- See JSON output for full missing/stale ID lists, duplicate groups, identity mismatches, individual link-check outcomes, and all non-addressable assets.",
        "",
    ]
    return "\n".join(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, default=SNAPSHOT_PATH)
    parser.add_argument("--checksum", type=Path, default=CHECKSUM_PATH)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "audit-output")
    parser.add_argument("--skip-link-check", action="store_true", help="Skip destination HEAD/GET checks; report remains ATTENTION REQUIRED")
    parser.add_argument("--max-link-checks", type=int, default=0, help="Limit destination checks (0 means all; report remains ATTENTION REQUIRED when limited)")
    args = parser.parse_args()

    snapshot, snapshot_sha, snapshot_bytes = load_snapshot(args.snapshot)
    checksum_expected = load_checksum(args.checksum)
    registry_data = {
        "posts": fetch_registry_type("posts"),
        "pages": fetch_registry_type("pages"),
    }

    link_results: list[dict[str, Any]] = []
    link_check_performed = False
    assets = snapshot.get("assets", [])
    if not args.skip_link_check:
        selected = assets if args.max_link_checks <= 0 else assets[:args.max_link_checks]
        for asset in selected:
            link_results.append(check_destination(asset))
        link_check_performed = len(selected) == len(assets) and len(assets) > 0

    report = build_report(
        snapshot, snapshot_sha, snapshot_bytes, checksum_expected,
        registry_data, link_results, link_check_performed,
    )
    if not link_check_performed:
        report["completeness_gates"]["destination_check_performed"] = False
        report["completeness_gates"]["no_broken_destinations"] = False
        report["overall_status"] = "ATTENTION REQUIRED"

    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "crosslink_territorial_integrity.json"
    md_path = args.output_dir / "crosslink_territorial_integrity.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    print(render_markdown(report))
    print(f"\nJSON report: {json_path}")
    print(f"Markdown report: {md_path}")
    return 0 if report["overall_status"] == "COMPLETE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
