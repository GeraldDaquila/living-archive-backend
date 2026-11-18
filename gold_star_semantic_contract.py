"""Conservative, source-independent question-sensitive Gold Star contracts.

A heuristic pass is never a semantic certification. Unknown tasks and fact
accuracy remain review-required; observable violations can be rejected.
"""
from __future__ import annotations
import re
from typing import Any

VERSION = "1.0"
_PATTERNS = {
    "explicit_no_handoff": re.compile(r"\\b(?:do not|don't|without|no)\\b.{0,80}\\b(?:links?|resources?|recommendations?|follow[- ]?up|next steps?|doorways?)\\b", re.I),
    "technical_verification": re.compile(r"\\b(?:verify|check|confirm|test)\\b.{0,100}\\b(?:environment variable|secret|configuration|configured|credential)\\b", re.I),
    "uncertain_causation": re.compile(r"\\bwhat caused\\b|\\bwhy did\\b.{0,80}\\b(?:increase|decrease|spike|drop|change)\\b", re.I),
    "strategic_tradeoff": re.compile(r"\\bshould\\b.{0,100}\\b(?:or|versus|vs\\.?|rather than)\\b", re.I),
    "practical_application": re.compile(r"\\bhow can\\b|\\bhow do (?:i|we|they)\\b|\\bhow should\\b", re.I),
    "comparison": re.compile(r"\\b(?:difference between|differ from|compare|comparison|versus|vs\\.?)\\b", re.I),
    "general_fact": re.compile(r"\\b(?:what is|who is|when did|where is|how many|what temperature)\\b", re.I),
}

def classify_question(query: str) -> dict[str, Any]:
    q = str(query or "").strip()
    if not q:
        return {"version": VERSION, "type": "unknown", "confidence": "none"}
    # Explicit user constraints take precedence over generic task verbs.
    for kind in ("explicit_no_handoff", "technical_verification", "uncertain_causation", "strategic_tradeoff", "comparison", "practical_application", "general_fact"):
        if _PATTERNS[kind].search(q):
            return {"version": VERSION, "type": kind, "confidence": "high"}
    return {"version": VERSION, "type": "unknown", "confidence": "none"}

def _has(text: str, phrases: tuple[str, ...]) -> bool:
    return any(p in text for p in phrases)

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
    low = re.sub(r"\\s+", " ", answer.casefold())
    checks: list[dict[str, Any]] = []
    def add(name: str, passed: bool, rationale: str) -> None:
        checks.append({"name": name, "passed": bool(passed), "rationale": rationale})
    if kind == "explicit_no_handoff":
        add("no_resource_handoff", not payload.get("recommendation") and not re.search(r"https?://|www\\.", answer, re.I), "Respect explicit no-resource/no-link instructions.")
        add("no_unrequested_followup", not _has(low, ("would you like", "if you want, i can", "you may want to explore", "next, you could", "i recommend reading")), "Do not append an unrequested next step.")
    elif kind == "technical_verification":
        add("presence_not_disclosure", _has(low, ("os.getenv", "os.environ", "environment variable")) and _has(low, ("is not none", "bool(", "presence check", "configured")), "Explain a boolean/presence check.")
        add("secret_not_printed", not _has(low, ("print(os.getenv", "print(os.environ", "logger.info(os.getenv", "logging the secret value")), "Do not expose secret values.")
        add("config_vs_runtime_use", _has(low, ("runtime", "application reads", "application uses", "actually uses", "consumes the variable")), "Distinguish configuration presence from application use.")
    elif kind == "uncertain_causation":
        add("calibrated_uncertainty", _has(low, ("cannot determine", "can't determine", "not enough information", "without analytics", "without data", "insufficient evidence", "would need")), "Do not invent a cause without evidence.")
        add("discriminating_evidence", _has(low, ("referral", "source", "utm", "analytics", "server log", "search console", "campaign", "bot")), "Name evidence that distinguishes explanations.")
        add("useful_investigation", _has(low, ("compare", "check", "inspect", "segment", "review", "investigate")), "Offer a practical evidence-gathering step.")
    elif kind == "strategic_tradeoff":
        add("alternatives_visible", _has(low, ("centraliz", "centralis", "distribut", "decentral", "delegate", "delegat")), "Address the alternatives named in the question.")
        add("tradeoffs_visible", _has(low, ("trade-off", "tradeoff", "however", "risk", "cost", "benefit", "advantage", "disadvantage")), "Make material costs and benefits visible.")
        add("conditional_judgment", _has(low, ("depends on", "when ", "if ", "recommend", "hybrid", "retain", "delegate")), "Give conditional reasoning rather than a universal slogan.")
    elif kind == "comparison":
        add("comparative_structure", _has(low, ("whereas", "while", "by contrast", "unlike", "both", "difference", "compared with")), "Make the distinction explicit.")
    elif kind == "practical_application":
        add("actionable_content", _has(low, ("first", "start by", "begin by", "for example", "such as", "you can", "the organization can", "one practical")), "Provide an actionable operation or example.")
    elif kind == "general_fact":
        return {"version": VERSION, "status": "review_required", "reason": "fact_accuracy_requires_evidence_or_case_rubric", "question_type": kind, "checks": []}
    failed = [c["name"] for c in checks if not c["passed"]]
    return {"version": VERSION, "status": "fail" if failed else "review_required",
            "reason": "task_contract_violation" if failed else "heuristics_pass_human_review_still_required",
            "question_type": kind, "checks": checks, "failed_checks": failed,
            "semantic_certification": False}
