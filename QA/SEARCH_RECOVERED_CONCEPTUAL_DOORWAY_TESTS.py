"""Regression contract for weak search-recovered conceptual doorways."""

import re

QUESTION = "What does it mean for an AI to be an interpreter rather than an authority?"

def eligible(question, candidate):
    stop = {
        "what", "does", "mean", "rather", "than", "for", "with", "that",
        "this", "from", "into", "about", "when", "where", "which", "have",
        "has", "been", "being", "the", "and", "or", "but", "how", "why",
        "can", "could", "would", "should", "are", "is", "an", "a", "to",
        "of", "in", "on", "by", "it", "its", "final", "right",
    }
    salient = {
        token.casefold()
        for token in re.findall(r"[A-Za-z][A-Za-z'-]{2,}", question)
        if token.casefold() not in stop
    }
    title_words = set(re.findall(r"[A-Za-z][A-Za-z'-]{2,}", candidate.get("title", "").casefold()))
    body_words = set(re.findall(r"[A-Za-z][A-Za-z'-]{2,}", candidate.get("text", "").casefold()))
    return bool(salient & title_words) or len(salient & body_words) >= 2

def main():
    law = {"title": "Law", "text": "A broad discussion of institutions and authority."}
    assert not eligible(QUESTION, law)

    relevant = {
        "title": "AI and Human Judgment",
        "text": "This explores interpretation, authority, and human responsibility.",
    }
    assert eligible(QUESTION, relevant)
    print("SEARCH-RECOVERED CONCEPTUAL DOORWAY QA: PASS")

if __name__ == "__main__":
    main()
