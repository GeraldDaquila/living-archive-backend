"""Question-to-evidence contract for direct attribute questions.

This is deliberately corpus-agnostic: it checks whether the requested attribute
is actually represented in a candidate source, rather than allowing a shared
entity word to stand in for evidence.
"""
import re

_STOP = {"a", "an", "the", "of", "for", "to", "in", "on", "at", "by", "with"}


def direct_attribute_phrase(question):
    """Return a multiword attribute in a direct 'what is X of Y' question."""
    value = re.sub(r"\s+", " ", str(question or "")).strip().rstrip(" ?!.")
    match = re.match(
        r"^(?:please\s+)?what\s+is\s+(?:the\s+)?(.+?)\s+of\s+(.+)$",
        value,
        flags=re.I,
    )
    if not match:
        return None
    phrase = re.sub(r"\s+", " ", match.group(1)).strip(" ,;:")
    terms = [token.casefold() for token in re.findall(r"[a-z0-9]+", phrase) if token.casefold() not in _STOP]
    # Keep this contract conservative: one-word classifications can be
    # ambiguous, while multiword attributes have a clear evidence obligation.
    return " ".join(terms) if len(terms) >= 2 else None


def direct_attribute_supported(question, document):
    """Require source-body support for the requested attribute, not just entity overlap."""
    phrase = direct_attribute_phrase(question)
    if not phrase:
        return True
    if not isinstance(document, dict):
        return False
    body = str(document.get("text") or document.get("content") or document.get("excerpt") or "").casefold()
    normalized_body = " ".join(re.findall(r"[a-z0-9]+", body))
    # Require the attribute phrase as a phrase, not scattered term mentions.
    return bool(normalized_body) and phrase in normalized_body


def should_fail_closed(archive_evidence_unavailable, discovery_subject=False):
    """Fail closed for ordinary inquiries without evidence; discovery has its own page-body gate."""
    return bool(archive_evidence_unavailable) and not bool(discovery_subject)


def archive_limitation_response():
    """Visitor-facing corpus-only response when no suitable Archive evidence exists."""
    return (
        "I couldn’t establish an answer to that question from the Living Archive’s "
        "available material. I won’t substitute outside knowledge or attach a "
        "resource that has not been shown to address what you asked."
    )
