"""Bounded fallback retrieval from the public Life.Understood. WordPress site.

This module is deliberately independent of Cowboy MCP: runtime requests use only
the site's anonymous WordPress REST API. Internal canonical retrieval remains
the authority; callers should invoke this client only after their normal
relevance/evidence gate reports insufficient evidence.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
import logging
import re
import threading
import time
from typing import Any, Callable, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlparse
from urllib.request import Request, urlopen

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


class _VisibleText(HTMLParser):
    """Extract visible text while dropping non-content and site chrome."""

    _DROP = {"script", "style", "nav", "header", "footer", "form", "noscript"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._drop_depth = 0
        self.parts: List[str] = []

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag.lower() in self._DROP:
            self._drop_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in self._DROP and self._drop_depth:
            self._drop_depth -= 1
        elif tag.lower() in {"p", "div", "li", "h1", "h2", "h3", "h4", "br", "hr"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._drop_depth and data.strip():
            self.parts.append(data.strip())


def _clean_text(value: Any) -> str:
    raw = str(value or "")
    # Reject documents containing known access-control shortcodes rather than
    # risk exposing enclosed member-only text from stored block content.
    if _PRIVATE_SHORTCODE_RE.search(raw):
        return ""
    raw = _BLOCK_COMMENT_RE.sub(" ", raw)
    raw = _SHORTCODE_RE.sub(" ", raw)
    parser = _VisibleText()
    try:
        parser.feed(raw)
        parser.close()
    except Exception:
        return ""
    text = re.sub(r"[\t\r ]+", " ", " ".join(parser.parts))
    text = re.sub(r"\n\s*\n+", "\n", text).strip()
    return text[:MAX_PASSAGE_CHARS]


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


def normalize_public_post(
    post: Dict[str, Any],
    *,
    retrieved_at: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Convert one anonymous REST post into USE's canonical resource shape."""
    if not isinstance(post, dict):
        return None
    if post.get("status") != "publish" or post.get("type") not in _ALLOWED_TYPES:
        return None
    content = post.get("content")
    if not isinstance(content, dict) or content.get("protected") is True:
        return None
    title_data = post.get("title")
    title = title_data.get("rendered", "") if isinstance(title_data, dict) else title_data
    title = re.sub(r"<[^>]+>", " ", str(title or "")).strip()
    url = post.get("link")
    if not title or not _safe_public_url(url):
        return None
    text = _clean_text(content.get("rendered", ""))
    if len(text) < 80:
        return None
    modified = str(post.get("modified_gmt") or post.get("modified") or "").strip()
    return {
        "id": f"live-wp-{post.get('id')}",
        "title": title[:240],
        "url": str(url),
        "text": text,
        "content": text,
        "resource_type": "public_live_site",
        "source": "public_living_archive_live_site",
        "source_status": "published_public_rest",
        "wordpress_post_id": int(post["id"]) if str(post.get("id", "")).isdigit() else None,
        "source_modified_at": modified or None,
        "retrieved_at": retrieved_at or datetime.now(timezone.utc).isoformat(),
        "canonical_source_url": str(url),
        "evidence_provenance": {
            "source": "public_living_archive_live_site",
            "canonical_url": str(url),
            "title": title[:240],
            "wordpress_post_id": int(post["id"]) if str(post.get("id", "")).isdigit() else None,
            "source_modified_at": modified or None,
            "retrieved_at": retrieved_at or datetime.now(timezone.utc).isoformat(),
            "passage": text,
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
        request = Request(
            url,
            headers={"Accept": "application/json", "User-Agent": "USE-Public-Archive-Fallback/1.0"},
        )
        with urlopen(request, timeout=timeout) as response:
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
                route = "posts" if subtype == "post" else "pages"
                endpoint = f"{REST_ROOT}/{route}/{int(post_id)}?"
                endpoint += urlencode({
                    "context": "view",
                    "_fields": "id,status,type,link,title,content,modified,modified_gmt",
                })
                post = self._get(endpoint)
                document = normalize_public_post(post)
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
