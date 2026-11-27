"""Conservative, source-independent question-sensitive Gold Star contracts.

A heuristic pass is never a semantic certification. Unknown tasks and fact
accuracy remain review-required; observable violations can be rejected.
"""
from __future__ import annotations
import re
from typing import Any

from inquiry_family_transfer_contract import classify_inquiry_family

from institutional_learning_failure_contract import (
    institutional_learning_failure_response_checks,
    is_institutional_learning_failure_question,
)

VERSION = "1.5"
_PATTERNS = {
    "explicit_no_handoff": re.compile(r"\b(?:do not|don't|without|no)\b.{0,80}\b(?:links?|resources?|recommendations?|follow[- ]?up|next steps?|doorways?)\b", re.I),
    "epistemic_category_distinction": re.compile(
        r"(?=.*\bevidence\b)(?=.*\binterpretation\b)(?=.*\bhypothes(?:is|es)\b)(?=.*\b(?:normative judgment|value judgment|what ought)\b)"
        r"(?=.*\b(?:what counts as|distinguish|difference|between|differ|separate)\b).*", re.I
    ),
    "guide_meta_coverage_policy": re.compile(
        r"\b(?:when|under what conditions|what evidence|what standard)\b.{0,100}"
        r"\b(?:should|may|must)\b.{0,60}\b(?:the\s+)?guide\b.{0,100}"
        r"\b(?:say|state|acknowledge|declare|claim|report)\b.{0,120}"
        r"\b(?:archive|coverage|directly address|does not yet address)\b",
        re.I,
    ),
    "technical_verification": re.compile(r"\b(?:verify|check|confirm|test)\b.{0,100}\b(?:environment variable|secret|configuration|configured|credential)\b", re.I),
    "uncertain_causation": re.compile(r"\bwhat caused\b|\bwhy did\b.{0,80}\b(?:increase|decrease|spike|drop|change)\b", re.I),
    "strategic_tradeoff": re.compile(r"\bshould\b.{0,100}\b(?:or|versus|vs\.?|rather than)\b", re.I),
    "practical_application": re.compile(r"\bhow can\b|\bhow do (?:i|we|they)\b|\bhow should\b", re.I),
    "comparison": re.compile(r"\b(?:difference between|differ from|compare|comparison|versus|vs\.?)\b", re.I),
    "conceptual_explanation": re.compile(r"\bwhat is\b.{0,100}\b(?:and why|why does|why is|how does|what makes)\b", re.I),
    "general_fact": re.compile(r"\b(?:what is|who is|when did|where is|how many|what temperature)\b", re.I),
}

def classify_question(query: str) -> dict[str, Any]:
    q = str(query or "").strip()
    if not q:
        return {"version": VERSION, "type": "unknown", "confidence": "none"}
    if is_institutional_learning_failure_question(q):
        return {"version": VERSION, "type": "institutional_learning_failure", "confidence": "high"}
    inquiry_family = classify_inquiry_family(q).get("family")
    if inquiry_family in {"epistemic_distress", "epistemic_distress_guidance"}:
        return {"version": VERSION, "type": inquiry_family, "confidence": "high"}
    if inquiry_family == "personal_lived_reflective":
        return {"version": VERSION, "type": "lived_reflective_inquiry", "confidence": "high"}
    # Explicit user constraints take precedence over generic task verbs.
    for kind in ("explicit_no_handoff", "guide_meta_coverage_policy", "epistemic_category_distinction", "technical_verification", "uncertain_causation", "strategic_tradeoff", "comparison", "conceptual_explanation", "practical_application", "general_fact"):
        if _PATTERNS[kind].search(q):
            return {"version": VERSION, "type": kind, "confidence": "high"}
    return {"version": VERSION, "type": "unknown", "confidence": "none"}

def remove_question_echo(query: str, answer: str) -> str:
    """Remove one verbatim question echo before scoring substantive answer content."""
    tokens = re.findall(r"[a-z0-9]+", str(query or "").casefold())
    if len(tokens) < 4:
        return str(answer or "")
    phrase = r"[\W_]+".join(re.escape(token) for token in tokens)
    pattern = r"(?<![a-z0-9])" + phrase + r"(?![a-z0-9])"
    return re.sub(pattern, " ", str(answer or ""), count=1, flags=re.I)


def _has(text: str, phrases: tuple[str, ...]) -> bool:
    return any(p in text for p in phrases)


def _extract_comparison_subjects(query: str) -> list[str]:
    """Extract comparison subjects without absorbing a trailing explanatory clause."""
    normalized = re.sub(r"\s+", " ", str(query or "")).strip()
    match = re.search(
        r"\b(?:difference|distinction)\s+between\s+(.+?)(?:[?!.]|$)",
        normalized,
        re.I,
    )
    if match:
        raw = match.group(1)
    else:
        match = re.search(r"\bcompare\s+(.+?)(?:[?!.]|$)", normalized, re.I)
        if not match:
            return []
        raw = match.group(1)

    # A comparison can be followed by an instruction about how to explain it.
    # Keep the noun phrase being compared; do not turn "explain how ..." into
    # a spurious comparison subject.
    raw = re.split(
        r"\s*(?:,\s*)?(?:and\s+)?(?:explain|describe|discuss|show|consider)\s+"
        r"(?:how|why|whether|what|the|their|its)\b",
        raw,
        maxsplit=1,
        flags=re.I,
    )[0]
    raw = re.sub(
        r"\b(?:in terms of|with regard to|in relation to|when it comes to)\b.*$",
        "",
        raw,
        flags=re.I,
    )
    raw = re.sub(
        r"\s*,?\s+(?:and|or|with|to|versus|vs\.?)\s+",
        ",",
        raw,
        flags=re.I,
    )
    subjects = [
        re.sub(r"^(?:the|a|an)\s+", "", part.strip(" ,;:.!?")).strip().casefold()
        for part in raw.split(",")
    ]
    subjects = [subject for subject in subjects if subject]
    return subjects if 2 <= len(subjects) <= 5 else []


def _comparison_subject_is_explained(subject: str, answer: str) -> bool:
    cue = r"(?:is|means|refers to|concerns|describes|brings|connects|represents|involves|denotes)"
    pattern = r"\b" + re.escape(subject) + r"\b.{0,240}\b" + cue + r"\b"
    return bool(re.search(pattern, answer, re.I))


def evaluate_semantic_contract(query: str, payload: Any) -> dict[str, Any]:
    """Reject detectable task-contract violations; never rewrite an answer."""
    if not isinstance(payload, dict):
        return {"version": VERSION, "status": "not_applicable", "reason": "non_object_payload"}
    if payload.get("ok") is False:
        return {"version": VERSION, "status": "not_applicable", "reason": "error_payload"}
    answer = next((str(payload.get(k) or "").strip() for k in ("response", "answer") if str(payload.get(k) or "").strip()), "")
    if not answer:
        return {"version": VERSION, "status": "fail", "reason": "missing_answer"}
    kind = classify_question(query)["type"]
    if kind == "unknown":
        return {"version": VERSION, "status": "review_required", "reason": "no_confident_task_contract", "question_type": kind, "checks": []}
    low = re.sub(r"\s+", " ", remove_question_echo(query, answer).casefold())
    checks: list[dict[str, Any]] = []
    def add(name: str, passed: bool, rationale: str, *, hard: bool = False) -> None:
        checks.append({"name": name, "passed": bool(passed), "rationale": rationale,
                       "severity": "hard" if hard else "review"})
    if kind == "institutional_learning_failure":
        for item in institutional_learning_failure_response_checks(low):
            add(
                item["name"],
                item["passed"],
                "Answer the causal question by distinguishing acknowledgment from learning, naming structural mechanisms, connecting understanding to changed action, and offering a calibrated corrective test.",
                hard=True,
            )
    elif kind == "explicit_no_handoff":
        add("no_resource_handoff", not payload.get("recommendation") and not re.search(r"https?://|www\.", answer, re.I), "Respect explicit no-resource/no-link instructions.", hard=True)
        add("no_unrequested_followup", not _has(low, ("would you like", "if you want, i can", "you may want to explore", "next, you could", "i recommend reading", "a useful next question", "the next question is", "the next step is", "a good next step", "one useful next step")), "Do not append an unrequested next step.")
    elif kind == "guide_meta_coverage_policy":
        coverage_ok = all((
            _has(low, ("directly address", "direct coverage")),
            _has(low, ("related", "adjacent")),
            _has(low, ("genuine coverage gap", "coverage gap")),
            _has(low, ("retrieval result", "retrieval failure", "failed retrieval", "search failure")),
            _has(low, ("indexing", "access", "source verification")),
            _has(low, ("checked", "verified", "evidence")),
        ))
        add("four_coverage_outcomes_distinguished", coverage_ok, "Separate direct, adjacent, genuine-gap, and retrieval/verification-failure outcomes.")
        add("no_gap_claim_from_retrieval_failure", not _has(low, ("failed retrieval proves a gap", "no search result proves a gap", "indexing failure means the archive has no")), "Retrieval or verification failure is not evidence of a genuine Archive gap.")
        doorway_aliases = (
            "recommendation", "recommendations", "canonical_doorway", "doorway",
            "doorway_title", "doorway_url", "authoritative_doorway",
            "canonical_recommendation", "archive_doorway",
            "recommendation_canonical_primary", "recommendation_canonical_secondary",
            "recommendation_canonical", "recommended_resource", "recommended_resources",
        )
        no_doorway = (
            not any(payload.get(key) for key in doorway_aliases)
            and not re.search(r"https?://|www\\.", answer, re.I)
        )
        add("no_archive_doorway_for_policy_question", no_doorway, "This is a Guide-policy question, not an Archive-resource request.")
    elif kind == "epistemic_category_distinction":
        category_checks = all((
            _has(low, ("evidence",)) and _has(low, ("observation", "records", "measurements", "testimony")),
            _has(low, ("interpretation",)) and _has(low, ("meaning", "context")),
            _has(low, ("hypothesis",)) and _has(low, ("provisional", "testable", "investigated")),
            _has(low, ("normative judgment",)) and _has(low, ("ought", "should", "values", "principles")),
        ))
        add("all_four_categories_defined", category_checks, "Define evidence, interpretation, hypothesis, and normative judgment distinctly.")
        add("fact_value_boundary", _has(low, ("facts alone", "does not follow from facts", "evidence matters", "values and principles")), "Do not present a normative conclusion as if it followed from facts alone.")
        add("categories_related_without_collapse", _has(low, ("evidence constrains", "hypothesis guides", "evidence to seek", "interpretation can suggest")), "Explain how the categories inform one another without treating them as interchangeable.")
        add("concrete_application", _has(low, ("for example", "for instance", "a policy example", "in practice")), "Show how the distinctions operate in a concrete case.")
    elif kind == "technical_verification":
        add("presence_not_disclosure", _has(low, ("os.getenv", "os.environ", "environment variable")) and _has(low, ("is not none", "bool(", "presence check", "configured")), "Explain a boolean/presence check.")
        add("secret_not_printed", not _has(low, ("print(os.getenv", "print(os.environ", "logger.info(os.getenv", "logging the secret value")), "Do not expose secret values.")
        add("config_vs_runtime_use", _has(low, ("runtime", "application reads", "application uses", "actually uses", "consumes the variable")), "Distinguish configuration presence from application use.")
    elif kind == "uncertain_causation":
        add("no_asserted_cause_without_evidence", not _has(low, ("the cause was definitely", "this was caused by", "the reason is certainly")), "Do not state a definite cause without supporting evidence.")
        add("calibrated_uncertainty", _has(low, ("cannot determine", "can't determine", "not enough information", "without analytics", "without data", "insufficient evidence", "would need")), "Do not invent a cause without evidence.")
        add("discriminating_evidence", _has(low, ("referral", "source", "utm", "analytics", "server log", "search console", "campaign", "bot")), "Name evidence that distinguishes explanations.")
        add("useful_investigation", _has(low, ("compare", "check", "inspect", "segment", "review", "investigate")), "Offer a practical evidence-gathering step.")
    elif kind == "strategic_tradeoff":
        add("alternatives_visible", _has(low, ("centraliz", "centralis", "distribut", "decentral", "delegate", "delegat")), "Address the alternatives named in the question.")
        add("tradeoffs_visible", _has(low, ("trade-off", "tradeoff", "risks", "risk", "costs", "cost", "benefits", "benefit", "advantages", "advantage", "disadvantages", "disadvantage")), "Make material costs and benefits visible.")
        add("conditional_judgment", _has(low, ("depends on", "when decisions", "when a decision", "if the decision", "routine local decisions", "strategic decisions", "recommend", "hybrid", "retain", "delegate")), "Give conditional reasoning rather than a universal slogan.")
    elif kind == "comparison":
        subjects = _extract_comparison_subjects(query)
        if subjects:
            add(
                "compared_subjects_covered",
                all(re.search(r"\b" + re.escape(subject) + r"\b", low) for subject in subjects),
                "Address every subject explicitly named in the comparison.",
                hard=True,
            )
            add(
                "compared_subjects_explained",
                all(_comparison_subject_is_explained(subject, low) for subject in subjects),
                "Explain what each named subject means or does; naming alone is not a comparison.",
                hard=True,
            )
        add(
            "comparative_structure",
            _has(low, (
                "whereas", "while", "by contrast", "in contrast", "unlike", "both",
                "difference", "compared with", "distinct", "not interchangeable",
                "not the same", "different from", "rather than", "separate from",
            )),
            "Make the distinction explicit rather than listing terms.",
            hard=True,
        )
        add(
            "relationship_explained",
            _has(low, (
                "interact", "interacting", "reinforce one another", "work together",
                "coherent whole", "interdependent", "not a fixed", "not a single sequence",
            )),
            "Where relevant, explain how the compared concepts relate without collapsing them.",
        )
    elif kind in {"epistemic_distress", "epistemic_distress_guidance"}:
        distress_present = bool(re.search(r"\b(?:distress|distressed|fear|grief|panic|overwhelmed|vulnerable|suffering|anguish)\b", low))
        epistemic_boundary = (
            bool(re.search(r"\b(?:experience|experienced)\b", low))
            and bool(re.search(r"\b(?:belief|interpretation|tradition)\b", low))
            and bool(re.search(r"\b(?:evidence|verifiable|establish)\b", low))
        )
        uncertainty_calibrated = bool(re.search(r"\b(?:cannot be known|cannot be established|cannot establish|cannot know|cannot verify|not know|not verifiable|unverifiable|uncertain|uncertainty|not proven|beyond available evidence|no reliable way to establish)\b", low))
        no_false_certainty = not bool(re.search(
            r"\b(?:definitely|certainly|undoubtedly|without doubt)\b.{0,60}\b(?:real|true|exists|proven|certain)\b"
            r"|\b(?:proven beyond doubt|i can guarantee|i know with certainty)\b",
            low,
        ))
        agency_present = bool(re.search(r"\b(?:agency|choice|decide|reflect|think|grounded|autonomy|without dependence)\b", low))
        humane_support = bool(re.search(r"\b(?:compassion|care|support|dignity|listen|acknowledge|human|frightening|painful|difficult)\b", low))
        present_grounding = bool(re.search(r"\b(?:right now|in this moment|today|for now|pause|slow down|breathe|feet on the floor|ground yourself|drink some water|rest|trusted person|someone you trust|not face this alone)\b", low))
        meaning_boundary = bool(re.search(r"\b(?:meaning|meaningful|personally meaningful|spiritual meaning|what it means to you)\b", low)) and bool(re.search(r"\b(?:does not prove|not proof|not establish|cannot establish|separate from|different from|distinct from|does not settle|not the same as)\b", low))
        add("recognizes_distress", distress_present, "Acknowledge the vulnerability and human need behind certainty-seeking.", hard=True)
        add("preserves_epistemic_boundary", epistemic_boundary, "Distinguish experience, belief, interpretation and evidence; do not present unverifiable metaphysical claims as established fact.", hard=True)
        add("calibrates_metaphysical_uncertainty", uncertainty_calibrated and no_false_certainty, "Make the limits of what can be established explicit; do not manufacture metaphysical certainty or exploit distress.", hard=True)
        add("supports_agency", agency_present, "Help the person retain their own judgment and agency rather than becoming dependent on the Guide.", hard=True)
        add("responds_humanely", humane_support, "Respond with compassion without dismissing the person's beliefs or experience.", hard=True)
        add("offers_present_grounding", present_grounding, "Offer one proportionate way to regain footing in the present, without assuming a diagnosis or prescribing a ritual.", hard=True)
        add("distinguishes_personal_meaning_from_proof", meaning_boundary, "Allow personal or spiritual meaning while making clear that meaning does not establish an external metaphysical fact.", hard=True)
    elif kind == "lived_reflective_inquiry":
        experience_present = bool(re.search(r"\b(?:pain|suffer\w*|hurt|grief|loss|bereave\w*|mourning|trauma|shame|fear|loneliness|heartbreak|wound\w*|hardship|identity|selfhood|personhood|belonging|who i am|sense of self)\b", low))
        experience_identity_relation = bool(re.search(
            r"\b(?:pain|suffer\w*|hurt|grief|loss|bereave\w*|mourning|trauma|shame|fear|loneliness|heartbreak|wound\w*|identity|selfhood|personhood|belonging|who i am|sense of self)\b"
            r".{0,180}\b(?:not|without|rather than|does not|doesn't|more than|no longer|all|whole)\b"
            r".{0,100}\b(?:identity|self|whole|person|story|who you are|who they are)\b"
            r"|\b(?:pain|suffer\w*|hurt|grief|loss|bereave\w*|mourning|trauma|shame|fear|loneliness|heartbreak|wound\w*|identity|selfhood|personhood|belonging|who i am|sense of self)\b"
            r".{0,120}\bpart of\b.{0,100}\b(?:identity|self|person|story)\b"
            r".{0,100}\b(?:without|not|rather than|whole|more than)\b"
            r"|\b(?:identity|self|who you are|who they are)\b"
            r".{0,100}\b(?:more than|not defined by|not reduced to|not the whole of)\b"
            r".{0,100}\b(?:pain|suffer\w*|hurt|grief|loss|bereave\w*|mourning|trauma|shame|fear|loneliness|heartbreak|wound\w*|identity|selfhood|personhood|belonging|who i am|sense of self)\b",
            low,
        ))
        add("addresses_named_lived_experience", experience_present, "The answer must engage the experience named by the visitor, not replace it with an adjacent planning framework.", hard=True)
        if classify_inquiry_family(query).get("identity_focus"):
            add("preserves_experience_identity_distinction", experience_identity_relation, "The answer must explicitly relate the experience to identity without allowing the experience to define the whole person.", hard=True)
    elif kind == "practical_application":
        add("actionable_content", _has(low, ("first", "start by", "begin by", "for example", "such as", "you can", "the organization can", "one practical")), "Provide an actionable operation or example.")
    elif kind == "conceptual_explanation":
        add("plain_language_definition", _has(low, (" is the study of", " is a way of understanding", " refers to", " means ", " is the study", " is concerned with")), "Define the central concept before extending it.")
        add("significance_or_implication", _has(low, ("matters because", "shapes", "influences", "affects", "helps people", "can shape", "choices", "values", "relationships")), "Connect the concept to the significance asked about.")
        add("concrete_application", _has(low, ("for example", "such as", "in practice", "for instance", "a person", "a community")), "Use a concrete example or practical implication where the question asks why it matters.")
    elif kind == "general_fact":
        return {"version": VERSION, "status": "review_required", "reason": "fact_accuracy_requires_evidence_or_case_rubric", "question_type": kind, "checks": []}
    failed = [c["name"] for c in checks if not c["passed"]]
    hard_failed = [c["name"] for c in checks if not c["passed"] and c.get("severity") == "hard"]
    review_flags = [c["name"] for c in checks if not c["passed"] and c.get("severity") != "hard"]
    return {"version": VERSION, "status": "fail" if hard_failed else "review_required",
            "reason": "observable_contract_violation" if hard_failed else "human_review_required",
            "question_type": kind, "checks": checks, "failed_checks": failed,
            "hard_failures": hard_failed, "review_flags": review_flags,
            "semantic_certification": False}
