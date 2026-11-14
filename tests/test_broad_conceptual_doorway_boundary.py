import main

def test_broad_conceptual_doorway_requires_subject_continuity():
    query = "How does the Archive distinguish tools from the purposes they serve?"
    answer = "The Guide keeps direct Archive claims, cross-source synthesis, and interpretive orientation visibly distinct so it does not borrow authority it has not earned."
    unrelated = {"title": "Financial Sovereignty and Economic Independence", "text": "A resource about finance, money, and economic self-determination."}
    related = {"title": "Source, Synthesis, and Orientation in the Living Archive", "text": "How source claims, synthesis, interpretation, and traceability remain distinct."}
    assert not main._broad_conceptual_doorway_candidate_fit(query, answer, unrelated)
    assert main._broad_conceptual_doorway_candidate_fit(query, answer, related)
