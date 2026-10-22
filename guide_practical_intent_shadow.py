"""Shadow-only intent diagnostics for practical-application questions.

This module is not imported by production request handling. It measures whether
questions asking how to enact a value are recognized as action-seeking rather
than being collapsed into generic reflective inquiry.
"""
import re

_PRACTICAL_APPLICATION_PATTERNS = (
    r"\bwhat would (?:i|we|they|an organization|the organization) actually do differently\b",
    r"\bwhat (?:would|could|should) .{0,60} do differently\b",
    r"\bhow (?:do|does|can|could|should|would) .{0,60} put .{1,60} into practice\b",
    r"\bhow .{0,60} work in practice\b",
    r"\bwhat .{0,60} look like (?:in practice|day to day|day-to-day)\b",
    r"\bhow .{0,60} live by (?:it|that value|those values|this principle)\b",
    r"\bwhat practical changes .{0,60} make\b",
)

_CONCEPTUAL_PATTERNS = (
    r"\bwhy .{0,50} matter\b",
    r"\bwhat is the importance of\b",
    r"\bwhat does .{0,50} mean\b",
    r"\bdefine\b",
)

_ACTION_MARKERS = (
    r"\b(?:make commitments visible|agree on who will do what|communicate early)",
    r"\b(?:explain|publish|document) (?:the reasons|decision reasons|why a decision)",
    r"\b(?:safe to raise concerns|raise concerns without punishment|respond to dissent)",
    r"\b(?:acknowledge|own) (?:their|our|a leader's|leadership's)? ?(?:mistakes|error|responsibility)",
    r"\b(?:repair|restore|rebuild) trust",
    r"\b(?:follow through|close the loop|report back)",
)


def classify_practical_application_intent(query):
    """Return a conservative shadow label; never influences production routing."""
    q = re.sub(r"\s+", " ", str(query or "").casefold()).strip()
    if any(re.search(pattern, q) for pattern in _PRACTICAL_APPLICATION_PATTERNS):
        return "practical_application"
    if any(re.search(pattern, q) for pattern in _CONCEPTUAL_PATTERNS):
        return "conceptual"
    return "other"


def has_observable_organizational_practice(response):
    """Check for concrete organizational behaviors, not abstract inquiry alone."""
    text = re.sub(r"\s+", " ", str(response or "").casefold()).strip()
    return sum(bool(re.search(pattern, text)) for pattern in _ACTION_MARKERS) >= 2
