"""Full-corpus metadata crosslink for The Guide.

The inventory is built from the canonical Pinecone index, not mini-USE.
It is read-only, bounded, access-filtered, and cached per process. An
incomplete inventory is never represented as exhaustive and is never used
to expand visitor evidence.
"""
from __future__ import annotations

import html
import json
import os
import re
import threading
import time
from collections import Counter
from typing import Any
from urllib.request import Request as UrlRequest, urlopen

_PAGE_SIZE = 100
_MAX_VECTORS = 50000
_REFRESH_SECONDS = 31 * 24 * 60 * 60  # monthly safety interval
_MAX_ASSETS_PER_QUERY = 4
_STOPWORDS = {
    "about", "after", "again", "also", "among", "and", "are", "around",
    "because", "been", "before", "being", "between", "both", "but", "can",
    "could", "does", "from", "have", "into", "just", "more", "most", "not",
    "only", "other", "over", "same", "should", "some", "such", "than", "that",
    "their", "them", "then", "there", "these", "they", "this", "those", "through",
    "under", "very", "what", "when", "where", "which", "while", "with", "would",
    "your", "you", "the", "for", "was", "were", "will", "how", "why", "who",
    "does", "did", "its", "our", "out", "his", "her", "she", "him", "has",
}

_LOCK = threading.RLock()
_REFRESH_LOCK = threading.Lock()
_SNAPSHOT: dict[str, Any] | None = None
_LAST_REFRESH = 0.0
_LAST_ATTEMPT = 0.0
_RETRY_SECONDS = 60
_PINECONE_REQUEST_TIMEOUT = 15
_CROSSLINK_FETCH_TIMEOUT = 5
_PRIMARY_RENDER_SERVICE_ID = "srv-da98sm2jnfac73d2ki5g"
_INVENTORY_WALL_BUDGET_SECONDS = 600
_WP_REGISTRY_PAGE_SIZE = 100
_WP_REGISTRY_MAX_PAGES = 50
_WP_REGISTRY_TIMEOUT_SECONDS = 3.0
_WP_REGISTRY_CACHE_TTL_SECONDS = 21600
_REFRESH_THREAD: threading.Thread | None = None
_WP_CANONICAL_CACHE: dict[str, dict[str, str]] = {}
_WP_CANONICAL_CACHE_AT = 0.0


def _log(message: str) -> None:
    print(message, flush=True)


def _field(value: Any, key: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(key, default)
    getter = getattr(value, "get", None)
    if callable(getter):
        try:
            return getter(key, default)
        except Exception:
            pass
    return getattr(value, key, default)


def _text(value: Any, limit: int = 2400) -> str:
    if isinstance(value, (list, tuple, set)):
        value = " ".join(str(item) for item in value)
    if not isinstance(value, (str, int, float)):
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()[:limit]


def _tokens(value: Any) -> set[str]:
    words = re.findall(r"[a-z0-9][a-z0-9'-]{1,}", _text(value, 8000).casefold())
    return {word.strip("'-") for word in words if len(word) > 2 and word not in _STOPWORDS}


def _normalize_url(value: Any) -> str:
    url = _text(value, 1000).strip()
    if not re.match(r"^https://[^\s]+$", url, re.I):
        return ""
    return url.rstrip("/").casefold()


def _canonical_title_key(value: Any) -> str:
    normalized = html.unescape(re.sub(r"<[^>]*>", " ", _text(value, 300))).casefold()
    return re.sub(r"\W+", " ", normalized).strip()


def _load_wp_canonical_map() -> dict[str, dict[str, str]]:
    """Load a bounded public WordPress ID -> canonical URL/title registry.

    Only published posts and pages are included. A URL is later assigned only
    when both the WordPress ID and normalized title match the Pinecone record.
    """
    global _WP_CANONICAL_CACHE, _WP_CANONICAL_CACHE_AT
    if str(os.getenv("RENDER", "")).casefold() != "true":
        return {}
    now = time.monotonic()
    if _WP_CANONICAL_CACHE and now - _WP_CANONICAL_CACHE_AT < _WP_REGISTRY_CACHE_TTL_SECONDS:
        return dict(_WP_CANONICAL_CACHE)

    registry: dict[str, dict[str, str]] = {}
    ambiguous_ids: set[str] = set()
    counts = {"posts": 0, "pages": 0}
    try:
        for post_type in ("posts", "pages"):
            page = 1
            while page <= _WP_REGISTRY_MAX_PAGES:
                endpoint = (
                    "https://geralddaquila.com/wp-json/wp/v2/"
                    f"{post_type}?per_page={_WP_REGISTRY_PAGE_SIZE}&page={page}&_fields=id,link,title"
                )
                request = UrlRequest(
                    endpoint,
                    headers={"Accept": "application/json", "User-Agent": "LivingArchiveGuide/1.0"},
                    method="GET",
                )
                with urlopen(request, timeout=_WP_REGISTRY_TIMEOUT_SECONDS) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                if not isinstance(payload, list):
                    raise RuntimeError(f"WordPress {post_type} registry response was not a list")
                counts[post_type] += len(payload)
                for item in payload:
                    if not isinstance(item, dict):
                        continue
                    wp_id = str(item.get("id") or "").strip()
                    title_obj = item.get("title")
                    title = title_obj.get("rendered") if isinstance(title_obj, dict) else title_obj
                    title_key = _canonical_title_key(title)
                    url = _normalize_url(item.get("link"))
                    if not wp_id.isdigit() or not title_key or not url:
                        continue
                    if not re.match(r"^https://geralddaquila\.com/\S+$", url, re.I):
                        continue
                    entry = {"url": url, "title_key": title_key}
                    existing = registry.get(wp_id)
                    if existing and existing != entry:
                        ambiguous_ids.add(wp_id)
                    else:
                        registry[wp_id] = entry
                if len(payload) < _WP_REGISTRY_PAGE_SIZE:
                    break
                page += 1
            if page > _WP_REGISTRY_MAX_PAGES:
                raise RuntimeError(f"WordPress {post_type} registry exceeded page limit")
    except Exception as exc:
        _log(f"USE archive meta-crosslink WordPress registry: status=unavailable, error={type(exc).__name__}")
        return {}

    for wp_id in ambiguous_ids:
        registry.pop(wp_id, None)
    _WP_CANONICAL_CACHE = dict(registry)
    _WP_CANONICAL_CACHE_AT = now
    _log(
        "USE archive meta-crosslink WordPress registry: status=complete, "
        f"posts={counts['posts']}, pages={counts['pages']}, "
        f"unique_ids={len(registry)}, ambiguous_ids={len(ambiguous_ids)}"
    )
    return dict(registry)


def _pinecone_call(method: Any, *, timeout: float = _PINECONE_REQUEST_TIMEOUT, **kwargs: Any) -> Any:
    """Apply a bounded per-request timeout, retaining compatibility with test doubles/older SDKs."""
    try:
        return method(timeout=timeout, **kwargs)
    except TypeError as exc:
        if "timeout" not in str(exc):
            raise
        return method(**kwargs)


def _namespace_specs(index: Any) -> tuple[list[tuple[str, int | None]], int | None, int]:
    stats = _pinecone_call(index.describe_index_stats)
    dimension = _field(stats, "dimension")
    if dimension is None or int(dimension) != 384:
        raise RuntimeError("Canonical Pinecone index must remain 384-dimensional")
    namespaces = _field(stats, "namespaces", {}) or {}
    total = _field(stats, "total_vector_count")
    specs: list[tuple[str, int | None]] = []
    if isinstance(namespaces, dict) and namespaces:
        for name, summary in namespaces.items():
            namespace = "" if str(name) == "__default__" else str(name)
            count = _field(summary, "vector_count")
            specs.append((namespace, int(count) if count is not None else None))
    else:
        specs.append(("", int(total) if total is not None else None))
    return specs, int(total) if total is not None else None, int(dimension)


def _list_page(index: Any, namespace: str, token: str | None):
    method = getattr(index, "list_paginated", None)
    if callable(method):
        return _pinecone_call(method, limit=_PAGE_SIZE, pagination_token=token, namespace=namespace)
    # Compatibility fallback for SDK versions exposing only the paginator.
    if token is None and callable(getattr(index, "list", None)):
        pages = _pinecone_call(index.list, limit=_PAGE_SIZE, namespace=namespace)
        return next(iter(pages), None)
    raise RuntimeError("Pinecone index does not expose paginated vector listing")


def _vector_ids(page: Any) -> list[str]:
    vectors = _field(page, "vectors", []) or []
    ids = []
    for item in vectors:
        value = _field(item, "id")
        if value:
            ids.append(str(value))
    return ids


def _next_token(page: Any) -> str | None:
    pagination = _field(page, "pagination")
    value = _field(pagination, "next")
    return str(value) if value else None


def _metadata_for(vector: Any) -> dict[str, Any]:
    metadata = _field(vector, "metadata", {})
    return dict(metadata) if isinstance(metadata, dict) else {}


def _eligible(metadata: dict[str, Any], core: Any) -> bool:
    access_check = getattr(core, "_use_corpus_access_eligible", None)
    archived_check = getattr(core, "_is_archived_canonical_resource", None)
    if callable(access_check) and not access_check(metadata):
        return False
    if callable(archived_check) and archived_check(metadata):
        return False
    return bool(metadata)


def build_inventory(index: Any, core: Any, *, max_vectors: int = _MAX_VECTORS) -> dict[str, Any]:
    """Exhaustively list and fetch vector metadata across all namespaces."""
    if index is None:
        raise RuntimeError("Canonical Pinecone index is unavailable")
    started = time.monotonic()
    stage = "describe_index_stats"
    _log("USE archive meta-crosslink inventory: status=starting, stage=describe_index_stats")
    try:
        specs, expected_total, dimension = _namespace_specs(index)
    except Exception as exc:
        _log(f"USE archive meta-crosslink inventory: status=failed, stage={stage}, error={type(exc).__name__}")
        raise
    _log(
        "USE archive meta-crosslink inventory: status=running, stage=namespace_plan, "
        f"namespaces={len(specs)}, expected_vectors={expected_total}, dimension={dimension}"
    )
    wp_canonical_map = _load_wp_canonical_map()
    if expected_total is not None and expected_total > max_vectors:
        raise RuntimeError(f"Corpus exceeds bounded inventory limit ({expected_total}>{max_vectors})")

    assets: dict[str, dict[str, Any]] = {}
    # Preserve exact WordPress identity separately from title-based grouping.
    wp_id_urls: dict[str, set[str]] = {}
    asset_wp_ids: dict[str, set[str]] = {}
    listed_count = 0
    fetched_count = 0
    missing_metadata = 0
    metadata_key_counts: Counter[str] = Counter()
    url_field_presence: Counter[str] = Counter()
    wp_id_vector_count = 0
    wp_id_url_recovered = 0
    wp_id_title_mismatch = 0
    wp_id_unmatched = 0
    url_field_candidates = (
        "url", "canonical_url", "permalink", "source_url", "sourceUrl",
        "wp_url", "post_url", "origin_url", "href", "link", "guid",
    )
    ineligible_count = 0
    archived_count = 0
    truncated = False
    listed_ids_by_namespace: dict[str, set[str]] = {}
    fetched_ids_by_namespace: dict[str, set[str]] = {}

    def ingest_vector(vector_id: str, vector: Any, namespace: str) -> None:
        nonlocal missing_metadata, ineligible_count, wp_id_vector_count
        nonlocal wp_id_url_recovered, wp_id_title_mismatch, wp_id_unmatched
        root_id = str(getattr(core, "ROOT_NODE_ID", "") or "")
        if root_id and str(vector_id) == root_id:
            return
        metadata = _metadata_for(vector)
        if not metadata:
            missing_metadata += 1
            return
        for metadata_key in metadata:
            metadata_key_counts[str(metadata_key)] += 1
        for candidate_field in url_field_candidates:
            if _normalize_url(metadata.get(candidate_field)):
                url_field_presence[candidate_field] += 1
        if not _eligible(metadata, core):
            ineligible_count += 1
            return
        title = _text(metadata.get("title") or metadata.get("name"), 300)
        url = _normalize_url(metadata.get("url") or metadata.get("canonical_url"))
        wp_id = str(metadata.get("wp_id") or "").strip()
        if wp_id.isdigit():
            wp_id_vector_count += 1
        if not url and wp_id.isdigit():
            wp_record = wp_canonical_map.get(wp_id)
            if wp_record and _canonical_title_key(title) == wp_record["title_key"]:
                url = _normalize_url(wp_record["url"])
                wp_id_url_recovered += 1
            elif wp_record:
                wp_id_title_mismatch += 1
            else:
                wp_id_unmatched += 1
        if not title:
            missing_metadata += 1
            return
        key = "url:" + url if url else "title:" + re.sub(r"\W+", " ", title.casefold()).strip()
        if not key or key == "title:":
            key = f"id:{namespace}:{vector_id}"
        if wp_id.isdigit() and url:
            wp_id_urls.setdefault(wp_id, set()).add(url)
        if wp_id.isdigit():
            asset_wp_ids.setdefault(key, set()).add(wp_id)
        asset = assets.setdefault(key, {
            "asset_key": key,
            "title": title,
            "url": url,
            "namespace": namespace,
            "tier": _text(metadata.get("tier") or metadata.get("archive_tier"), 40),
            "resource_type": _text(metadata.get("resource_type") or metadata.get("type") or metadata.get("category"), 120),
            "access_class": _text(metadata.get("access_class") or metadata.get("access"), 40),
            "summary": "",
            "sample": "",
            "vector_refs": [],
            "vector_count": 0,
        })
        asset["vector_count"] += 1
        if len(asset["vector_refs"]) < 4:
            asset["vector_refs"].append({"id": str(vector_id), "namespace": namespace})
        summary = " ".join(filter(None, (
            _text(metadata.get("summary"), 500),
            _text(metadata.get("description"), 500),
            _text(metadata.get("excerpt"), 500),
            _text(metadata.get("keywords"), 300),
            _text(metadata.get("tags"), 300),
        )))
        if summary and len(asset["summary"]) < 1200:
            asset["summary"] = (asset["summary"] + " " + summary)[:1200]
        sample = _text(metadata.get("text") or metadata.get("content") or metadata.get("body"), 1000)
        if sample and len(asset["sample"]) < 2400:
            asset["sample"] = (asset["sample"] + " " + sample)[:2400]

    for namespace, namespace_count in specs:
        token = None
        seen_tokens: set[str] = set()
        namespace_listed = 0
        page_number = 0
        while True:
            if time.monotonic() - started > _INVENTORY_WALL_BUDGET_SECONDS:
                raise RuntimeError("inventory wall-clock budget exceeded")
            page_number += 1
            stage = f"list_namespace_page_{page_number}"
            try:
                page = _list_page(index, namespace, token)
            except Exception as exc:
                _log(
                    "USE archive meta-crosslink inventory: status=failed, "
                    f"stage={stage}, error={type(exc).__name__}, "
                    f"listed_vectors={listed_count}, fetched_vectors={fetched_count}"
                )
                raise
            if page is None:
                break
            ids = _vector_ids(page)
            if not ids:
                token = _next_token(page)
                if not token:
                    break
                continue
            if listed_count + len(ids) > max_vectors:
                ids = ids[:max(0, max_vectors - listed_count)]
                truncated = True
            listed_count += len(ids)
            listed_namespace_ids = listed_ids_by_namespace.setdefault(namespace, set())
            new_ids = [str(vector_id) for vector_id in ids if str(vector_id) not in listed_namespace_ids]
            listed_namespace_ids.update(new_ids)
            namespace_listed += len(new_ids)

            _log(
                "USE archive meta-crosslink inventory: status=running, "
                f"stage={stage}, namespace={namespace or '__default__'}, "
                f"page_vectors={len(ids)}, listed_vectors={listed_count}/{expected_total}"
            )
            for offset in range(0, len(ids), _PAGE_SIZE):
                if time.monotonic() - started > _INVENTORY_WALL_BUDGET_SECONDS:
                    raise RuntimeError("inventory wall-clock budget exceeded")
                batch = ids[offset:offset + _PAGE_SIZE]
                stage = f"fetch_namespace_page_{page_number}_batch_{offset // _PAGE_SIZE + 1}"
                try:
                    response = _pinecone_call(index.fetch, ids=batch, namespace=namespace)
                except Exception as exc:
                    _log(
                        "USE archive meta-crosslink inventory: status=failed, "
                        f"stage={stage}, error={type(exc).__name__}, "
                        f"listed_vectors={listed_count}, fetched_vectors={fetched_count}"
                    )
                    raise
                vectors = _field(response, "vectors", {}) or {}
                if not isinstance(vectors, dict):
                    vectors = {}
                namespace_fetched_ids = fetched_ids_by_namespace.setdefault(namespace, set())
                for vector_id, vector in vectors.items():
                    normalized_vector_id = str(vector_id)
                    if normalized_vector_id in namespace_fetched_ids:
                        continue
                    namespace_fetched_ids.add(normalized_vector_id)
                    fetched_count += 1
                    ingest_vector(normalized_vector_id, vector, namespace)

            token = _next_token(page)
            if token and token in seen_tokens:
                raise RuntimeError("Pinecone pagination token repeated")
            if token:
                seen_tokens.add(token)
            if truncated or not token:
                break
        if namespace_count is not None and namespace_listed != namespace_count:
            # Do not claim complete coverage if Pinecone's count and listing disagree.
            truncated = True

    # Retry IDs that were listed but omitted from a fetch response.
    for namespace, namespace_ids in listed_ids_by_namespace.items():
        missing_ids = sorted(namespace_ids - fetched_ids_by_namespace.get(namespace, set()))
        for attempt in range(1, 3):
            if not missing_ids:
                break
            _log(
                "USE archive meta-crosslink inventory: status=retrying, "
                f"namespace={namespace or '__default__'}, missing_fetch_ids={len(missing_ids)}, attempt={attempt}"
            )
            for offset in range(0, len(missing_ids), _PAGE_SIZE):
                if time.monotonic() - started > _INVENTORY_WALL_BUDGET_SECONDS:
                    raise RuntimeError("inventory wall-clock budget exceeded during missing-vector retry")
                batch = missing_ids[offset:offset + _PAGE_SIZE]
                try:
                    response = _pinecone_call(index.fetch, ids=batch, namespace=namespace)
                except Exception as exc:
                    _log(
                        "USE archive meta-crosslink inventory: status=retry_failed, "
                        f"namespace={namespace or '__default__'}, attempt={attempt}, error={type(exc).__name__}"
                    )
                    continue
                vectors = _field(response, "vectors", {}) or {}
                if not isinstance(vectors, dict):
                    continue
                namespace_fetched_ids = fetched_ids_by_namespace.setdefault(namespace, set())
                for vector_id, vector in vectors.items():
                    normalized_vector_id = str(vector_id)
                    if normalized_vector_id in namespace_fetched_ids:
                        continue
                    namespace_fetched_ids.add(normalized_vector_id)
                    fetched_count += 1
                    ingest_vector(normalized_vector_id, vector, namespace)
            missing_ids = sorted(namespace_ids - fetched_ids_by_namespace.get(namespace, set()))

    unique_listed_count = sum(len(ids) for ids in listed_ids_by_namespace.values())
    duplicate_listed_count = max(0, listed_count - unique_listed_count)

    # Repair chunk-level URL omissions first through exact WordPress identity.
    # Historical chunks can lose URL metadata while retaining their shared wp_id.
    # Only a one-to-one canonical destination is accepted; conflicts fail closed.
    for asset_key, asset in list(assets.items()):
        if asset.get("url"):
            continue
        wp_ids = asset_wp_ids.get(asset_key, set())
        if len(wp_ids) != 1:
            continue
        urls = wp_id_urls.get(next(iter(wp_ids)), set())
        if len(urls) != 1:
            continue
        recovered_url = next(iter(urls))
        target_key = "url:" + recovered_url
        target = assets.get(target_key)
        if target is None:
            asset["url"] = recovered_url
            assets[target_key] = asset
            del assets[asset_key]
            asset_wp_ids[target_key] = asset_wp_ids.pop(asset_key, set())
            continue
        target["vector_count"] += asset["vector_count"]
        for ref in asset["vector_refs"]:
            if len(target["vector_refs"]) >= 4:
                break
            if ref not in target["vector_refs"]:
                target["vector_refs"].append(ref)
        if asset.get("summary"):
            target["summary"] = (target["summary"] + " " + asset["summary"])[:1200]
        if asset.get("sample"):
            target["sample"] = (target["sample"] + " " + asset["sample"])[:2400]
        asset_wp_ids.setdefault(target_key, set()).update(wp_ids)
        del assets[asset_key]
        asset_wp_ids.pop(asset_key, None)

    # Repair chunk-level URL omissions only when an exact title maps to one
    # and only one canonical URL. Ambiguous duplicate titles remain unlinked.
    title_urls: dict[str, set[str]] = {}
    for asset_key, asset in assets.items():
        if asset.get("url"):
            title_key = re.sub(r"\W+", " ", asset["title"].casefold()).strip()
            title_urls.setdefault(title_key, set()).add(asset_key)
    for asset_key, asset in list(assets.items()):
        if asset.get("url"):
            continue
        title_key = re.sub(r"\W+", " ", asset["title"].casefold()).strip()
        matches = title_urls.get(title_key, set())
        if len(matches) != 1:
            continue
        target = assets[next(iter(matches))]
        target["vector_count"] += asset["vector_count"]
        for ref in asset["vector_refs"]:
            if len(target["vector_refs"]) >= 4:
                break
            if ref not in target["vector_refs"]:
                target["vector_refs"].append(ref)
        if asset.get("summary"):
            target["summary"] = (target["summary"] + " " + asset["summary"])[:1200]
        if asset.get("sample"):
            target["sample"] = (target["sample"] + " " + asset["sample"])[:2400]
        del assets[asset_key]

    titles: dict[str, set[str]] = {}
    for asset in assets.values():
        title_key = re.sub(r"\W+", " ", asset["title"].casefold()).strip()
        titles.setdefault(title_key, set()).add(asset["url"] or asset["asset_key"])
    duplicate_titles = sum(1 for urls in titles.values() if len(urls) > 1)
    complete = (
        not truncated
        and expected_total is not None
        and unique_listed_count == expected_total
        and fetched_count == unique_listed_count
        and missing_metadata == 0
    )
    missing_url_assets = sum(1 for asset in assets.values() if not asset.get("url"))
    crosslink_ready = complete and missing_url_assets == 0
    elapsed = round(time.monotonic() - started, 3)
    return {
        "contract": "archive-crosslink-inventory-v1",
        "status": "complete" if complete else "incomplete",
        "complete": complete,
        "crosslink_ready": crosslink_ready,
        "missing_url_asset_count": missing_url_assets,
        "expected_vector_count": expected_total,
        "dimension": dimension,
        "listed_vector_count": listed_count,
        "unique_listed_vector_count": unique_listed_count,
        "duplicate_listed_vector_count": duplicate_listed_count,
        "fetched_vector_count": fetched_count,
        "asset_count": len(assets),
        "missing_metadata_count": missing_metadata,
        "metadata_key_counts": dict(metadata_key_counts),
        "url_field_presence": dict(url_field_presence),
        "wp_registry_id_count": len(wp_canonical_map),
        "wp_id_vector_count": wp_id_vector_count,
        "wp_id_url_recovered_vector_count": wp_id_url_recovered,
        "wp_id_title_mismatch_vector_count": wp_id_title_mismatch,
        "wp_id_unmatched_vector_count": wp_id_unmatched,
        "unfetched_vector_count": max(0, unique_listed_count - fetched_count),
        "ineligible_vector_count": ineligible_count,
        "duplicate_title_count": duplicate_titles,
        "namespace_count": len(specs),
        "assets": list(assets.values()),
        "elapsed_seconds": elapsed,
        "refreshed_at": time.time(),
    }


def should_start_refresh(service_id: str | None) -> bool:
    """Only the canonical primary Render service owns the full-corpus snapshot.

    A missing service ID is treated as local development, where refresh remains enabled.
    """
    normalized = str(service_id or "").strip()
    return not normalized or normalized == _PRIMARY_RENDER_SERVICE_ID


def start_refresh(index: Any, core: Any, *, force: bool = False) -> bool:
    """Start one bounded full-corpus refresh.

    Normal operation uses the validated in-process snapshot. Automatic rebuilds
    are limited to a monthly safety interval; force=True is for deliberate refresh.
    """
    if index is None:
        return False
    global _REFRESH_THREAD, _LAST_ATTEMPT
    now = time.monotonic()
    with _LOCK:
        if not force and _SNAPSHOT is not None and now - _LAST_REFRESH < _REFRESH_SECONDS:
            return False
        if not force and _SNAPSHOT is None and now - _LAST_ATTEMPT < _RETRY_SECONDS:
            return False
        if _REFRESH_THREAD is not None and _REFRESH_THREAD.is_alive():
            return False
        if not _REFRESH_LOCK.acquire(blocking=False):
            return False
        thread = threading.Thread(
            target=_refresh_worker,
            args=(index, core),
            name="guide-archive-crosslink-inventory",
            daemon=True,
        )
        _REFRESH_THREAD = thread
        _LAST_ATTEMPT = now
        thread.start()
        _log("USE archive meta-crosslink inventory: refresh_scheduled=true")
        return True


def _refresh_worker(index: Any, core: Any) -> None:
    global _SNAPSHOT, _LAST_REFRESH, _REFRESH_THREAD
    worker_started = time.monotonic()
    _log("USE archive meta-crosslink inventory: worker_started=true")
    try:
        snapshot = build_inventory(index, core)
        with _LOCK:
            _SNAPSHOT = snapshot
            _LAST_REFRESH = time.monotonic()
        _log(
            "USE archive meta-crosslink inventory: "
            f"status={snapshot['status']}, namespaces={snapshot['namespace_count']}, "
            f"vectors={snapshot['listed_vector_count']}/{snapshot['expected_vector_count']}, "
            f"fetched_vectors={snapshot['fetched_vector_count']}/{snapshot['listed_vector_count']}, "
            f"unique_listed_vectors={snapshot['unique_listed_vector_count']}, "
            f"duplicate_listed_vectors={snapshot['duplicate_listed_vector_count']}, "
            f"unfetched_vectors={snapshot['unfetched_vector_count']}, "
            f"assets={snapshot['asset_count']}, missing_metadata={snapshot['missing_metadata_count']}, "
            f"missing_urls={snapshot['missing_url_asset_count']}, "
            f"url_field_presence={snapshot['url_field_presence']}, metadata_keys={sorted(snapshot['metadata_key_counts'])}, "
            f"wp_registry_ids={snapshot['wp_registry_id_count']}, wp_id_vectors={snapshot['wp_id_vector_count']}, "
            f"wp_id_url_recovered={snapshot['wp_id_url_recovered_vector_count']}, "
            f"wp_id_title_mismatch={snapshot['wp_id_title_mismatch_vector_count']}, "
            f"wp_id_unmatched={snapshot['wp_id_unmatched_vector_count']}, "
            f"crosslink_ready={snapshot['crosslink_ready']}, duplicates={snapshot['duplicate_title_count']}, "
            f"elapsed_seconds={snapshot['elapsed_seconds']}"
        )
    except Exception as exc:
        _log(f"USE archive meta-crosslink inventory unavailable: error={type(exc).__name__}, elapsed_seconds={round(time.monotonic() - worker_started, 3)}")
    finally:
        with _LOCK:
            _REFRESH_THREAD = None
        _REFRESH_LOCK.release()


def inventory_snapshot() -> dict[str, Any] | None:
    with _LOCK:
        if _SNAPSHOT is None:
            return None
        return {key: value for key, value in _SNAPSHOT.items() if key != "assets"}


def _asset_score(query_tokens: set[str], seed_tokens: set[str], asset: dict[str, Any]) -> float:
    title_tokens = _tokens(asset.get("title"))
    summary_tokens = _tokens(asset.get("summary"))
    sample_tokens = _tokens(asset.get("sample"))
    searchable = summary_tokens | sample_tokens | _tokens(asset.get("resource_type"))
    score = 0.0
    score += 4.0 * len(query_tokens & title_tokens)
    score += 1.7 * len(query_tokens & summary_tokens)
    score += 0.7 * len(query_tokens & sample_tokens)
    score += 1.2 * len(query_tokens & _tokens(asset.get("resource_type")))
    score += 0.65 * len(seed_tokens & title_tokens)
    score += 0.25 * len(seed_tokens & searchable)
    if len(query_tokens) >= 2 and query_tokens.issubset(title_tokens | summary_tokens | sample_tokens):
        score += 2.0
    return score


def select_crosslinks(
    query: str,
    seed_documents: list[dict[str, Any]],
    snapshot: dict[str, Any] | None,
    *,
    limit: int = _MAX_ASSETS_PER_QUERY,
) -> list[dict[str, Any]]:
    """Rank public canonical assets across the complete inventory."""
    if not isinstance(snapshot, dict) or not snapshot.get("crosslink_ready"):
        return []
    query_tokens = _tokens(query)
    if not query_tokens:
        return []
    existing_urls = {
        _normalize_url(doc.get("url") or doc.get("canonical_url"))
        for doc in seed_documents or []
    }
    seed_tokens: set[str] = set()
    for doc in seed_documents or []:
        seed_tokens.update(_tokens(doc.get("title")))
    ranked = []
    for asset in snapshot.get("assets", []):
        if not isinstance(asset, dict) or not asset.get("url") or asset["url"] in existing_urls:
            continue
        score = _asset_score(query_tokens, seed_tokens, asset)
        if score >= 3.0:
            ranked.append((score, asset))
    ranked.sort(key=lambda item: (-item[0], str(item[1].get("title") or "")))
    return [asset for _, asset in ranked[:max(0, min(int(limit), 8))]]


def fetch_crosslink_documents(index: Any, core: Any, assets: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Fetch only selected vector records and reapply canonical public gates."""
    if index is None or not assets:
        return []
    documents: list[dict[str, str]] = []
    seen_urls: set[str] = set()
    for asset in assets:
        refs = asset.get("vector_refs") or []
        for ref in refs:
            if not isinstance(ref, dict) or not ref.get("id"):
                continue
            try:
                response = _pinecone_call(index.fetch, timeout=_CROSSLINK_FETCH_TIMEOUT, ids=[str(ref["id"])], namespace=str(ref.get("namespace") or ""))
                vectors = _field(response, "vectors", {}) or {}
                vector = vectors.get(str(ref["id"])) if isinstance(vectors, dict) else None
                metadata = _metadata_for(vector) if vector is not None else {}
                if not metadata or not _eligible(metadata, core):
                    continue
                title = _text(metadata.get("title") or metadata.get("name"), 300)
                url = _text(metadata.get("url") or metadata.get("canonical_url"), 1000)
                normalized_url = _normalize_url(url)
                content_fn = getattr(core, "_resource_content", None)
                body = _text(content_fn(metadata) if callable(content_fn) else (
                    metadata.get("text") or metadata.get("content") or metadata.get("excerpt")
                ), 5000)
                if not title or not normalized_url or not body or normalized_url in seen_urls:
                    continue
                usable = getattr(core, "_has_usable_destination", None)
                if callable(usable) and not usable(metadata):
                    continue
                navigable = getattr(core, "_is_navigable_canonical_resource", None)
                if callable(navigable) and not navigable(metadata):
                    continue
                documents.append({"title": title, "url": url, "text": body})
                seen_urls.add(normalized_url)
                break
            except Exception:
                continue
    return documents


def expand_context(
    query: str,
    seed_documents: list[dict[str, Any]],
    index: Any,
    core: Any,
) -> list[dict[str, str]]:
    """Return a small, verified evidence expansion; never use partial inventories."""
    if index is None:
        return []
    with _LOCK:
        snapshot = _SNAPSHOT
    if snapshot is None:
        # A process restart may require one bounded rebuild. Once a validated
        # snapshot exists, normal requests do not trigger repeated corpus scans.
        start_refresh(index, core)
        return []
    if not snapshot.get("crosslink_ready"):
        # Preserve fail-closed behavior without repeatedly spending Pinecone
        # operations on an inventory that has already failed validation.
        return []
    start_refresh(index, core)
    assets = select_crosslinks(query, seed_documents, snapshot)
    return fetch_crosslink_documents(index, core, assets)


__all__ = [
    "build_inventory",
    "expand_context",
    "fetch_crosslink_documents",
    "inventory_snapshot",
    "select_crosslinks",
    "should_start_refresh",
    "start_refresh",
]
