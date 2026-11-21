import main
import general_guide_composition as composition

QUESTION = "How can economic systems recognize unpaid care and commons maintenance?"
ABSTENTION = (
    "I do not have enough grounded material here to give a specific Archive-based answer, "
    "but the question can still be approached by making its central tension visible."
)

def test_final_boundary_overrides_care_commons_insufficiency_abstention():
    payload = {
        "ok": True,
        "query": QUESTION,
        "response": ABSTENTION,
        "recommendation": {
            "title": "Global Reset: Systems Change, Economic Transition, and Future Models",
            "url": "https://geralddaquila.com/global-reset-systems-change-economic-transition-and-future-models/",
        },
    }
    result = main._guide_finalize_visitor_payload(payload, QUESTION)
    assert composition._has_care_and_commons_economic_recognition_explanation(result["response"])
    assert "conditions that make other economic activity possible" in result["response"]
    assert "do not have enough grounded material" not in result["response"].casefold()
    assert result["recommendation"]["title"].startswith("Global Reset:")

def test_final_boundary_does_not_capture_unrelated_economic_question():
    assert not composition._requires_care_and_commons_economic_recognition(
        "How can economic systems improve productivity?"
    )
