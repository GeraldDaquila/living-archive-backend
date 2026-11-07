"""Read the published Living Glossary as the authority for Archive-specific terms.

The Guide must not maintain a competing hard-coded glossary. This adapter retrieves
one canonical WordPress page, extracts an exact heading match, and caches the parsed
entries briefly. Network failure returns no authority; callers must not invent one.
"""
from __future__ import annotations

import html
import json
import re
import threading
import time
from urllib.request import Request, urlopen

GLOSSARY_PAGE_ID = 5578
GLOSSARY_URL = "https://geralddaquila.com/wp-json/wp/v2/pages/5578?_fields=id,modified,content"
FRESH_TTL_SECONDS = 300.0
STALE_TTL_SECONDS = 3600.0
FETCH_TIMEOUT_SECONDS = 2.0
FAILURE_RETRY_SECONDS = 30.0

_lock = threading.Lock()
_cache = {"modified": "", "fetched_at": 0.0, "last_attempt": 0.0}


def _plain_text(markup: str) -> str:
    value = re.sub(r"<[^>]+>", " ", str(markup or ""))
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def _normalize(value: str) -> str:
    value = _plain_text(value).casefold()
    value = re.sub(r"[^\w\s-]", "", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value.removeprefix("the ").strip()


def extract_glossary_entry(markup: str, term: str, *, modified: str = ""):
    """Return an exact term entry, or None when the Glossary has no exact heading."""
    target = _normalize(term)
    if not target:
        return None

    # Parse the page into heading-delimited sections. Classification headings
    # immediately following the term heading are metadata, not new entries.
    heading_pattern = re.compile(r"<h([2-6])\b[^>]*>(.*?)</h\1>", re.I | re.S)
    headings = list(heading_pattern.finditer(str(markup or "")))
    for index, match in enumerate(headings):
        heading_text = _plain_text(match.group(2))
        if _normalize(heading_text) != target:
            continue
        category = ""
        section_start = match.end()
        next_index = index + 1
        if next_index < len(headings):
            candidate = _plain_text(headings[next_index].group(2))
            is_category = (
                len(candidate) <= 90
                and not candidate.casefold().startswith("see also")
                and (
                    "/" in candidate
                    or candidate.casefold() in {
                        "descriptive", "conceptual", "symbolic", "functional",
                        "ethical", "systems", "integrative", "archetypal",
                    }
                )
            )
            if is_category:
                category = candidate
                section_start = headings[next_index].end()
                next_index += 1
        end = headings[next_index].start() if next_index < len(headings) else len(markup)
        section = str(markup)[section_start:end]
        paragraphs = [
            _plain_text(item)
            for item in re.findall(r"<p\b[^>]*>(.*?)</p>", section, re.I | re.S)
        ]
        paragraphs = [item for item in paragraphs if item]
        if not paragraphs:
            # Some legacy entries are written as plain block text/list items.
            paragraphs = [
                _plain_text(item)
                for item in re.findall(r"<li\b[^>]*>(.*?)</li>", section, re.I | re.S)
            ]
            paragraphs = [item for item in paragraphs if item]
        if not paragraphs:
            return None
        return {
            "term": heading_text,
            "category": category,
            "paragraphs": paragraphs,
            "source_url": "https://geralddaquila.com/glossary/",
            "source_page_id": GLOSSARY_PAGE_ID,
            "source_modified": modified,
        }
    return None


def _fetch_page():
    request = Request(
        GLOSSARY_URL,
        headers={
            "Accept": "application/json",
            "User-Agent": "Living-Archive-Guide/1.0",
            "Cache-Control": "no-cache",
        },
    )
    with urlopen(request, timeout=FETCH_TIMEOUT_SECONDS) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Glossary endpoint returned a non-object payload")
    content = payload.get("content")
    rendered = content.get("rendered") if isinstance(content, dict) else ""
    if not isinstance(rendered, str) or not rendered.strip():
        raise ValueError("Glossary endpoint did not return rendered page content")
    return rendered, str(payload.get("modified") or "")


def _refresh_cache():
    now = time.monotonic()
    if now - float(_cache["fetched_at"]) < FRESH_TTL_SECONDS:
        return True
    if now - float(_cache["last_attempt"]) < FAILURE_RETRY_SECONDS:
        return bool(_cache.get("markup")) and (
            now - float(_cache["fetched_at"]) < STALE_TTL_SECONDS
        )
    with _lock:
        now = time.monotonic()
        if now - float(_cache["fetched_at"]) < FRESH_TTL_SECONDS:
            return True
        if now - float(_cache["last_attempt"]) < FAILURE_RETRY_SECONDS:
            return bool(_cache.get("markup")) and (
                now - float(_cache["fetched_at"]) < STALE_TTL_SECONDS
            )
        _cache["last_attempt"] = now
        try:
            markup, modified = _fetch_page()
            # Cache page markup only; entries are extracted on demand so the
            # cache does not become a second manually maintained dictionary.
            _cache.update({"markup": markup, "modified": modified, "fetched_at": now})
            return True
        except Exception:
            # Keep the last known published snapshot for a bounded stale window.
            return bool(_cache.get("markup")) and (
                now - float(_cache["fetched_at"]) < STALE_TTL_SECONDS
            )


def get_glossary_entry(term: str):
    """Fetch an exact canonical entry, using bounded fresh/stale cache semantics."""
    if not _refresh_cache():
        return None
    entry = extract_glossary_entry(
        _cache.get("markup", ""),
        term,
        modified=_cache.get("modified", ""),
    )
    return entry


def compose_glossary_recovery(entry):
    """Compose a source-led, Archive-specific explanation without importing outside doctrine."""
    if not isinstance(entry, dict):
        return ""
    paragraphs = [str(item).strip() for item in entry.get("paragraphs", []) if str(item).strip()]
    if not paragraphs:
        return ""
    term = str(entry.get("term") or "This term").strip()
    category = str(entry.get("category") or "").strip()
    intro = f"In the Living Archive Glossary, {term} is classified as {category}." if category else (
        f"In the Living Archive Glossary, {term} has a defined, context-specific meaning."
    )
    first_paragraph = f"{intro} {paragraphs[0]}"
    if len(paragraphs) >= 2:
        second_paragraph = paragraphs[1]
    else:
        second_paragraph = (
            f"The entry's wording should be read in its stated context. "
            f"It does not establish meanings or implications beyond the definition given for {term}."
        )
    closing = (
        "This is the Archive's own usage of the term, not a universal dictionary definition. "
        "Other traditions or disciplines may use the same words differently, so those meanings "
        "should be identified separately rather than blended into this one."
    )
    return "\n\n".join([first_paragraph, second_paragraph, closing])
