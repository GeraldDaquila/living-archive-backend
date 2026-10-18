import main


def test_registered_direct_title_and_opening_body_grade_as_direct():
    subject = "how political dynasties affect public accountability in the philippines"
    document = {
        "title": "Political Dynasties in the Philippines",
        "url": (
            "https://geralddaquila.com/2025/05/21/"
            "political-dynasties-in-the-philippines-a-network-analysis-of-power-structures-and-their-socioeconomic-impacts/"
        ),
        "text": (
            "Political dynasties in the Philippines shape electoral competition and "
            "family networks. The study examines how concentrated family influence "
            "can affect public accountability, institutional checks, governance, and "
            "socioeconomic outcomes. It considers how citizens can scrutinize public "
            "decisions and hold elected officials responsible. The analysis maps "
            "dynastic influence and discusses reforms that can reduce entrenched "
            "inequality and strengthen inclusive governance."
        ),
    }
    node = {
        "node_id": "political-dynasties-philippines-study",
        "title": "Political Dynasties in the Philippines",
        "purpose": (
            "Provide a direct, source-grounded study of how political dynasties "
            "shape power structures, public accountability, governance, and "
            "socioeconomic outcomes in the Philippines."
        ),
        "semantic_hints": [
            "political dynasties",
            "political dynasty",
            "dynastic politics",
            "public accountability",
            "governance",
            "socioeconomic impacts",
            "power structures",
            "Philippines",
        ],
    }

    grade = main._guide_discovery_evidence_grade(subject, document, node=node)

    assert grade["grade"] == "direct"
    assert {"political", "dynasties", "accountability", "philippines"}.issubset(
        set(grade["support"])
    )
