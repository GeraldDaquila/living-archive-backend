"""Regression tests for semantic progression and non-mutating adaptive guidance."""

from pathlib import Path

import general_guide_composition as composition

ROOT = Path(__file__).resolve().parents[1]
QUERY = "How can one distinguish structural change from ordinary disruption?"

SCREENSHOT_RESPONSE = (
    "Structural change alters the underlying conditions that reproduce a pattern; ordinary disruption interrupts the pattern's visible operation without necessarily changing those conditions.\n\n"
    "To tell them apart, look for evidence that the system's rules, relationships, incentives, decision rights, or capabilities have changed—and whether those changes persist after the immediate pressure eases. A disruption can be severe while leaving those arrangements intact; structural change alters how the system produces outcomes over time.\n\n"
    "The test is not simply whether something new happened. Ask what now works differently, whose options or responsibilities have changed, what makes the old pattern less likely to recur, and what evidence would show that the change has held. If the old pattern returns as soon as the disturbance passes, the event was more likely disruption than structural change."
)

VALID_APPLIED_CONCLUSION = (
    "Structural change alters the conditions that keep producing a pattern; ordinary disruption interrupts what is happening without necessarily changing those conditions.\n\n"
    "You can look for changes to decision rights, incentives, rules, relationships, and capabilities, then check whether those changes remain once the immediate pressure has eased. A temporary pause or unusually strong response is not enough evidence on its own.\n\n"
    "Apply that distinction by checking the system after the urgent episode has passed: can people now make different decisions, do resources flow differently, and can the previous pattern still reproduce itself? If the old outcome returns under normal conditions, the intervention changed the episode, not the system's capacity to produce it."
)


def test_screenshot_style_conclusion_that_reopens_both_sides_is_rejected():
    paragraphs = [part.strip() for part in SCREENSHOT_RESPONSE.split("\n\n") if part.strip()]
    assert composition._paragraph_three_reopens_comparison(QUERY, paragraphs)
    assert composition.is_generic_nonanswer(QUERY, SCREENSHOT_RESPONSE)


def test_applied_conclusion_that_derives_a_new_post_event_test_is_preserved():
    paragraphs = [part.strip() for part in VALID_APPLIED_CONCLUSION.split("\n\n") if part.strip()]
    assert not composition._paragraph_three_reopens_comparison(QUERY, paragraphs)
    assert not composition.is_generic_nonanswer(QUERY, VALID_APPLIED_CONCLUSION)


def test_provider_templates_integrate_gold_star_discipline_without_appending_it_to_paragraph_three():
    source = (ROOT / "general_guide_composition.py").read_text(encoding="utf-8")
    assert "GOLD STAR INTEGRATION RULE:" in source
    assert "Never append lesson wording, an abstention boundary, or a meta-label as a substitute for the answer's own conclusion." in source
    assert "Integrate a relevant discipline invisibly into the reasoning operation" in source
    assert "If subject relevance is weak, ignore the lesson." in source


def test_deterministic_template_gives_paragraph_three_a_new_correctability_function():
    from deterministic_answer_recovery import compose_recovery

    answer = compose_recovery(
        "How should people act when the future is uncertain but consequential?"
    )
    paragraphs = [part.strip() for part in answer.split("\n\n") if part.strip()]
    assert len(paragraphs) == 3
    assert "who will be affected" in paragraphs[0]
    assert "Compare realistic options" in paragraphs[1]
    assert "preserves room to learn and correct" in paragraphs[2]
    assert "signals for review" in paragraphs[2]
    assert "Distinguish strain and transition" not in answer
    assert "A useful way to examine this is:" not in answer


def test_deterministic_gold_star_guidance_is_not_appended_to_visitor_answers():
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    assert "_apply_deterministic_fallback_guidance" not in source
    assert "Apply the deterministic Gold Star adapter outside the question-preserving" not in source


def test_compact_llm_contract_blocks_unrequested_ai_and_gold_star_content_transfer():
    prompt = composition._GENERAL_GUIDE_SYSTEM_COMPACT
    assert "Do not introduce AI, artificial intelligence, or another adjacent subject unless the visitor explicitly asks about it." in prompt
    assert "Never append lesson wording, an abstention boundary, or a meta-label as a substitute for the answer's own conclusion." in prompt
    assert "The conclusion must follow from this question's reasoning" in prompt
