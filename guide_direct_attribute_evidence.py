"""Question-to-evidence contract for direct attribute questions.

This is deliberately corpus-agnostic: it checks whether the requested attribute
is actually represented in a candidate source, rather than allowing a shared
entity word to stand in for evidence.
"""
import re

_STOP = {"a", "an", "the", "of", "for", "to", "in", "on", "at", "by", "with"}
# These are conceptual framing terms, not direct factual properties. They must
# remain on the normal Archive-grounded inquiry path instead of being subjected
# to a literal attribute-string gate.
_CONCEPTUAL_ATTRIBUTE_TERMS = {
    "role", "purpose", "significance", "meaning", "importance", "relationship",
    "contribution", "impact", "function", "nature", "value",
}


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
    raw_terms = [token.casefold() for token in re.findall(r"[a-z0-9]+", phrase)]
    if not raw_terms or raw_terms[0] in _CONCEPTUAL_ATTRIBUTE_TERMS:
        return None
    terms = [token for token in raw_terms if token not in _STOP]
    return " ".join(terms) if terms else None


def direct_attribute_qualifier(question):
    """Return a material condition attached to a direct attribute question, if any."""
    value = re.sub(r"\s+", " ", str(question or "")).strip().rstrip(" ?!.")
    match = re.match(
        r"^(?:please\s+)?what\s+is\s+(?:the\s+)?(.+?)\s+of\s+(.+)$",
        value,
        flags=re.I,
    )
    if not match:
        return None
    subject = match.group(2)
    qualifier = re.search(
        r"\b(?:at|under|above|below|in|on|with|without|during|when|for)\s+(.+)$",
        subject,
        flags=re.I,
    )
    if not qualifier:
        return None
    terms = [token.casefold() for token in re.findall(r"[a-z0-9]+", qualifier.group(1))]
    return " ".join(terms) if terms else None


def direct_attribute_supported(question, document):
    """Require the attribute and any explicit condition in the source body."""
    phrase = direct_attribute_phrase(question)
    if not phrase:
        return True
    if not isinstance(document, dict):
        return False
    body = str(document.get("text") or document.get("content") or document.get("excerpt") or "").casefold()
    normalized_body = " ".join(re.findall(r"[a-z0-9]+", body))
    # Require the attribute as a phrase, plus any material qualifier such as
    # "sea level"; shared entity words alone are not enough.
    if not normalized_body or phrase not in normalized_body:
        return False
    qualifier = direct_attribute_qualifier(question)
    return not qualifier or qualifier in normalized_body


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



def select_authoritative_doorway(question, preselected, source_selector, context, *, resource_query=None, normalize=None):
    """Do not let an earlier preselection bypass direct-attribute evidence checks."""
    if direct_attribute_phrase(question):
        candidate = source_selector(resource_query or question, context)
    else:
        candidate = preselected or source_selector(resource_query or question, context)
    return normalize(candidate) if normalize else candidate
