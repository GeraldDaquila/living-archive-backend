import main

def test_tools_and_purposes_inquiry_rejects_financial_doorway():
    query = "How does the Archive distinguish tools from the purposes they serve?"
    answer = "The Guide keeps direct Archive claims, cross-source synthesis, and interpretive orientation visibly distinct so it does not borrow authority it has not earned."
    financial = {"title": "Anchoring GESARA in Daily Life: Practical Tools for Embracing Financial Sovereignty", "text": "Practical tools for financial sovereignty and daily life."}
    assert not main._broad_conceptual_doorway_candidate_fit(query, answer, financial)
