"""Provenance-backed snapshot of a canonical Living Archive concept.

The published WordPress Glossary remains the editorial authority. Runtime
recovery uses this reviewed snapshot; update it only from the published entry.
"""

LAW_OF_ONE_CONCEPT_RECORD = {
    "fact_id": "archive_glossary_law_of_one",
    "subject": "Law of One",
    "classification": "Principle / Ethical Orientation",
    "doorway": {
        "title": "Law of One — Living Glossary",
        "url": "https://geralddaquila.com/glossary/",
    },
    "source": {
        "title": "The Living Glossary",
        "post_id": 5578,
        "slug": "glossary",
        "url": "https://geralddaquila.com/glossary/",
        "entry": "Law of One",
        "authority": "published_wordpress_glossary",
    },
    # Exact published entry text; do not independently paraphrase this record.
    "response": "A unifying principle expressing the inherent interconnectedness of all existence. In this framework, the Law of One is not a doctrine, channeling source, or external authority, but an ethical and perceptual orientation: recognition that harm, coercion, and extraction anywhere diminish coherence everywhere. Practiced maturely, it emphasizes unity without erasing individuality, sovereignty without isolation, and compassion without loss of responsibility. Unity is understood here as relational coherence, not sameness, fusion, or loss of agency.",
}
