"""Privacy-safe stable reason codes for provider contract rejections.

Only static validator messages are classified. Never emit the raw message,
visitor prompt, or generated response into provider diagnostics.
"""

import re


_REASON_RULES = (
    (r"^general composition returned invalid JSON$", "invalid_json"),
    (r"^general composition response was not an object$", "response_not_object"),
    (r"^general composition returned an empty response$", "empty_response"),
    (r"^general composition response is too short$", "response_too_short"),
    (r"^general composition response is too long$", "response_too_long"),
    (r"method-comparison answer requires the three-paragraph", "method_comparison_paragraphs"),
    (r"three-paragraph Guide Gold Standard", "three_paragraph_minimum"),
    (r"meta-answer/failure text", "meta_answer_failure"),
    (r"generic metadiscourse", "generic_nonanswer"),
    (r"conflicting-information answer", "conflicting_information_coverage"),
    (r"intergenerational stewardship answer", "intergenerational_coverage"),
    (r"practical next-step answer", "practical_action_missing"),
    (r"recurring-problem answer", "recurring_problem_mechanism_missing"),
    (r"outcome-evaluation answer", "outcome_evaluation_coverage"),
    (r"multi-step practical advice must use separate Markdown list lines", "list_line_format"),
    (r"plain stewardship explanation must not introduce an unsolicited list", "unsolicited_stewardship_list"),
    (r"plain stewardship explanation requires one recognizable everyday anchor", "stewardship_everyday_anchor_missing"),
    (r"plain stewardship explanation must clarify the limits of responsibility", "stewardship_boundary_missing"),
    (r"method-comparison answer must distinguish every method", "method_comparison_coverage"),
    (r"abstract concept definition requires one useful everyday example", "concept_example_missing"),
    (r"abstract concept definition must use readable paragraph breaks", "concept_paragraph_breaks"),
    (r"circular meta-definition", "archive_definition_circular"),
    (r"must define the actual concept in its opening paragraph", "archive_definition_opening"),
    (r"must answer in the named institutional context", "archive_context_missing"),
    (r"must give substantive conceptual content in the opening paragraph", "archive_conceptual_content_missing"),
    (r"must not retreat into generic disclaimer language", "archive_disclaimer"),
    (r"conceptual relationship answer must develop beyond", "conceptual_relationship_depth"),
    (r"conceptual relationship answer must resolve", "conceptual_relationship_tension"),
    (r"compound explanatory composition requires", "compound_structure_missing"),
    (r"explicit follow-up invitation request requires a closing question", "closing_question_missing"),
    (r"explicit follow-up invitation request requires exactly one question", "closing_question_count"),
    (r"distress response opened with formulaic sympathy", "distress_formulaic_opening"),
    (r"distress response must end with one gentle follow-up question", "distress_closing_question_missing"),
    (r"distress response must ask only one follow-up question", "distress_question_count"),
    (r"distress response rushed into task-management advice", "distress_task_advice"),
    (r"general composition exposed internal implementation language", "internal_language_exposure"),
    (r"general composition returned an invalid response shape", "invalid_response_shape"),
    (r"general composition embedded a navigation URL", "embedded_navigation_markdown"),
    (r"general composition exposed a URL", "raw_url_exposure"),
)


def contract_reason_code(reason: str) -> str:
    """Map a static validator message to a bounded, non-sensitive diagnostic code."""
    message = str(reason or "")
    for pattern, code in _REASON_RULES:
        if re.search(pattern, message, flags=re.IGNORECASE):
            return code
    return "unclassified_contract"
