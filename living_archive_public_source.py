"""Bounded fallback retrieval from the public Life.Understood. WordPress site.

This module is deliberately independent of Cowboy MCP: runtime requests use only
the site's anonymous WordPress REST API. Internal canonical retrieval remains
the authority; callers should invoke this client only after their normal
relevance/evidence gate reports insufficient evidence.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import logging
import re
import threading
import time
from typing import Any, Callable, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

LOGGER = logging.getLogger(__name__)

SITE_ORIGIN = "https://geralddaquila.com"
REST_ROOT = SITE_ORIGIN + "/wp-json/wp/v2"
MAX_RESULTS = 5
MAX_PASSAGE_CHARS = 1800
MAX_RESPONSE_BYTES = 1_000_000
REQUEST_TIMEOUT_SECONDS = 2.5
CACHE_TTL_SECONDS = 60
_ALLOWED_TYPES = {"post", "page"}
_BLOCK_COMMENT_RE = re.compile(r"<!--\s*/?wp:[\s\S]*?-->", re.I)
_SHORTCODE_RE = re.compile(r"\[/?[a-zA-Z][\w:-]*(?:\s[^\]]*)?\]", re.I)
_PRIVATE_SHORTCODE_RE = re.compile(
    r"\[/?(?:swpm|member|members|protected|password|steward|guardian|t4)[\w:-]*"
    r"(?:\s[^\]]*)?\]",
    re.I,
)
_PRIVATE_PATH_RE = re.compile(
    r"/(?:guardian(?:-portal|-stewardship)?|stewardship-archive|stewardship-materials|"
    r"stewardship-operations|stewardship-access-entrance|t4-codex)(?:/|$)",
    re.I,
)
_QUERY_TOKEN_RE = re.compile(r"[a-z0-9]{3,}", re.I)


def _safe_public_url(value: Any) -> bool:
    try:
        parsed = urlparse(str(value or ""))
    except Exception:
        return False
    return (
        parsed.scheme == "https"
        and parsed.hostname == "geralddaquila.com"
        and not parsed.username
        and not parsed.password
        and not _PRIVATE_PATH_RE.search(parsed.path or "/")
    )


def normalize_public_evidence(
    payload: Dict[str, Any],
    *,
    retrieved_at: Optional[str] = None,
    expected_post_id: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """Validate the site's dedicated public canonical-evidence endpoint."""
    if not isinstance(payload, dict):
        return None
    if payload.get("source") != "published_wordpress_content":
        return None
    post_id = payload.get("id")
    if not str(post_id or "").isdigit() or int(post_id) <= 0:
        return None
    if expected_post_id is not None and int(post_id) != int(expected_post_id):
        return None
    title = re.sub(r"<[^>]+>", " ", str(payload.get("title") or "")).strip()
    url = payload.get("url")
    if not title or not _safe_public_url(url):
        return None
    text = str(payload.get("text") or "").strip()
    # The site bridge strips registered shortcodes without executing them.
    # Reject residual access-control tokens rather than risking a partial leak.
    if _PRIVATE_SHORTCODE_RE.search(text) or len(text) < 80:
        return None
    text = text[:MAX_PASSAGE_CHARS]
    modified = str(payload.get("modified_gmt") or "").strip()
    observed_at = retrieved_at or datetime.now(timezone.utc).isoformat()
    return {
        "id": f"live-wp-{int(post_id)}",
        "title": title[:240],
        "url": str(url),
        "text": text,
        "content": text,
        "resource_type": "public_live_site",
        "source": "public_living_archive_live_site",
        "source_status": "published_public_canonical_evidence_endpoint",
        "source_trust": "untrusted_external_evidence_not_instructions",
        "wordpress_post_id": int(post_id),
        "source_modified_at": modified or None,
        "retrieved_at": observed_at,
        "canonical_source_url": str(url),
        "evidence_provenance": {
            "source": "public_living_archive_live_site",
            "canonical_url": str(url),
            "title": title[:240],
            "wordpress_post_id": int(post_id),
            "source_modified_at": modified or None,
            "retrieved_at": observed_at,
            "passage": text,
            "trust_boundary": "untrusted_external_evidence_not_instructions",
        },
    }


@dataclass
class _CacheEntry:
    expires_at: float
    documents: List[Dict[str, Any]]


class PublicLivingArchiveClient:
    """Anonymous, bounded REST search; all failures return an empty result."""

    def __init__(
        self,
        *,
        http_get: Optional[Callable[[str, float], Any]] = None,
        timeout: float = REQUEST_TIMEOUT_SECONDS,
        ttl: float = CACHE_TTL_SECONDS,
        max_results: int = MAX_RESULTS,
    ) -> None:
        self._http_get = http_get or self._default_http_get
        self._timeout = min(max(float(timeout), 0.1), 5.0)
        self._ttl = min(max(float(ttl), 0.0), 300.0)
        self._max_results = min(max(int(max_results), 1), MAX_RESULTS)
        self._cache: Dict[str, _CacheEntry] = {}
        self._lock = threading.Lock()

    @staticmethod
    def _default_http_get(url: str, timeout: float) -> Any:
        class _SameHostRedirects(HTTPRedirectHandler):
            def redirect_request(self, request, response, code, message, headers, new_url):
                target = urlparse(new_url)
                if target.scheme != "https" or target.hostname != "geralddaquila.com":
                    raise HTTPError(new_url, code, "cross-host redirect rejected", headers, response)
                return super().redirect_request(request, response, code, message, headers, new_url)

        request = Request(
            url,
            headers={"Accept": "application/json", "User-Agent": "USE-Public-Archive-Fallback/1.0"},
        )
        opener = build_opener(_SameHostRedirects())
        with opener.open(request, timeout=timeout) as response:
            if response.status != 200:
                raise URLError(f"unexpected HTTP status {response.status}")
            payload = response.read(MAX_RESPONSE_BYTES + 1)
        if len(payload) > MAX_RESPONSE_BYTES:
            raise ValueError("public source response exceeded byte limit")
        return json.loads(payload.decode("utf-8"))

    def _get(self, url: str) -> Any:
        return self._http_get(url, self._timeout)

    def search(self, query: str) -> List[Dict[str, Any]]:
        query = str(query or "").strip()
        tokens = _QUERY_TOKEN_RE.findall(query.lower())
        if len(query) < 4 or not tokens:
            return []
        cache_key = " ".join(tokens[:16])
        now = time.monotonic()
        with self._lock:
            cached = self._cache.get(cache_key)
            if cached and cached.expires_at > now:
                return [dict(item) for item in cached.documents]
        try:
            search_url = REST_ROOT + "/search?" + urlencode({
                "search": query[:240],
                "per_page": self._max_results,
                "type": "post",
                "_fields": "id,url,type,subtype,title",
            })
            hits = self._get(search_url)
            if not isinstance(hits, list):
                raise ValueError("invalid WordPress search response")
            docs: List[Dict[str, Any]] = []
            for hit in hits[: self._max_results]:
                if not isinstance(hit, dict):
                    continue
                subtype = str(hit.get("subtype") or "").lower()
                if subtype not in _ALLOWED_TYPES:
                    continue
                post_id = hit.get("id")
                if not str(post_id).isdigit():
                    continue
                endpoint = (
                    SITE_ORIGIN
                    + f"/wp-json/living-archive/v1/canonical-evidence/{int(post_id)}"
                )
                try:
                    evidence = self._get(endpoint)
                except HTTPError as exc:
                    # A 404/403 is the canonical bridge's expected fail-closed
                    # response for unpublished or protected candidates. Skip
                    # that candidate without discarding other public hits.
                    if exc.code in {403, 404}:
                        continue
                    raise
                document = normalize_public_evidence(
                    evidence,
                    expected_post_id=int(post_id),
                )
                if document:
                    docs.append(document)
            # Deterministic lexical ranking over normalized visible content.
            query_terms = set(tokens)
            docs.sort(
                key=lambda doc: (
                    len(query_terms & set(_QUERY_TOKEN_RE.findall(
                        (doc.get("title", "") + " " + doc.get("text", "")).lower()
                    ))),
                    len(doc.get("text", "")),
                ),
                reverse=True,
            )
            docs = docs[: self._max_results]
            with self._lock:
                self._cache[cache_key] = _CacheEntry(now + self._ttl, [dict(x) for x in docs])
            LOGGER.info(
                "USE public-source fallback succeeded=%s source_count=%d",
                bool(docs), len(docs),
            )
            return docs
        except Exception as exc:
            # Do not log the query, response body, or exception payload: they may
            # contain visitor text or source content.
            LOGGER.warning("USE public-source fallback unavailable error_type=%s", type(exc).__name__)
            return []
