"""Gold Star visitor contract for AI-led workforce restructuring questions.

The contract is intentionally narrow: it applies only when a question names
AI/automation, workforce impact, an organizational setting, and a cost or
restructuring motive. It gives provider and deterministic routes the same
minimum answer standard without forcing this frame onto unrelated AI questions.
"""
import re


def is_ai_workforce_restructuring_question(question):
    text = str(question or "")
    return bool(
        re.search(r"\b(?:ai|artificial intelligence|automation|automated systems)\b", text, re.I)
        and re.search(r"\b(?:staff(?:ing)?|workforce|employees?|labor|jobs?|headcount|layoffs?)\b", text, re.I)
        and re.search(r"\b(?:company|companies|business|businesses|organization|organisation|employer|enterprise|workplace|firm)\b", text, re.I)
        and re.search(r"\b(?:costs?|reduce|reduc\w*|cut|lower|efficien\w*|replace|displac\w*|restructur\w*|automat\w*)\b", text, re.I)
    )


def recovery_response():
    """Return the bounded three-paragraph Gold Star response for this question family."""
    return (
        "An organization should assess AI-led staffing reductions as a redesign of work and responsibility, not simply as a way to lower payroll. The case is credible only if the company can show which tasks can be automated safely, what work remains or is created, whether service and quality can be maintained, and whether the savings exceed the full costs of adoption.\n\n"
        "Operationally, map tasks rather than treating whole roles as interchangeable; measure integration, supervision, error correction, security, maintenance, and transition costs alongside payroll savings. Governance must identify who sets the system's objectives, approves its use, monitors errors and bias, and remains answerable when workers or customers are harmed. Compare layoffs with alternatives such as redesigning roles, reducing repetitive work, retraining, redeployment, or shorter hours.\n\n"
        "The human-development and ethical test is how the gains and burdens are distributed. A stewardship approach treats productivity gains as a responsibility to strengthen the work system and the people within it, not simply as a private saving. Employees should have meaningful notice and a voice in redesign, realistic opportunities to develop new skills, and fair treatment if roles disappear; customers and communities also matter where service quality or local livelihoods are affected. A responsible decision begins with a limited, reviewable pilot and clear measures of productivity, quality, error, workload, and worker outcomes. If benefits depend on hidden human labor, degraded service, or shifting risk onto people with little power, the proposal is not genuine efficiency but cost transfer."
    )


def has_gold_star_coverage(response):
    """Check paragraph roles and subject coverage, not merely paragraph count."""
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n+", str(response or "")) if part.strip()]
    if len(paragraphs) != 3:
        return False
    first, second, third = paragraphs
    if re.match(
        r"^(?:for a question like this|the first task|the first step|the guide should|the inquiry begins)",
        first,
        re.I,
    ):
        return False
    first_ok = (
        re.search(r"\b(?:ai|artificial intelligence|automation)\b", first, re.I)
        and re.search(r"\b(?:staffing|workforce|workers?|employees?|roles?)\b", first, re.I)
        and re.search(r"\b(?:assess|evaluate|treat|regard|consider)\b", first, re.I)
        and re.search(r"\b(?:cost|payroll|efficien|responsib|work)\w*\b", first, re.I)
    )
    second_ok = (
        re.search(r"\boperational\w*\b", second, re.I)
        and re.search(r"\bgovernance\b", second, re.I)
        and re.search(r"\b(?:oversight|supervis|accountab|answerab)\w*\b", second, re.I)
        and re.search(r"\b(?:integration|maintenance|transition|retrain|redeploy)\w*\b", second, re.I)
    )
    third_ok = (
        re.search(r"\b(?:human-development|human development|employees?|workers?)\b", third, re.I)
        and re.search(r"\b(?:ethical|ethics|fair|fairness)\w*\b", third, re.I)
        re.search(r"\bstewardship\b", third, re.I)
        and re.search(r"\b(?:pilot|review|measure|monitor|correct)\w*\b", third, re.I)
    )
    return bool(first_ok and second_ok and third_ok)
