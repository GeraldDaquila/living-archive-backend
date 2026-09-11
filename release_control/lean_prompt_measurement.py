"""Static release-control measurement harness for the v334 lean provider prompt.

This file does not alter production code. It is intentionally self-contained so
review can verify the acceptance arithmetic without importing the live engine.
"""

MAX_PROVIDER_INPUT_CHARS = 3800
MAX_PROVIDER_TOTAL_CHARS = 4600
RECOMMENDATION_MAX_COMPLETION_TOKENS = 256

LEAN_PROMPT = """You are The Guide for the Living Archive. Answer only from the supplied canonical evidence.

Answer the visitor's actual question directly. For topical or recommendation questions, orient them through the supplied Archive material and identify the strongest canonical doorway. Use additional resources only when they provide a distinct, evidence-supported contribution.

[QUESTION + RELATION]: Preserve the visitor's wording and open question. For synthesis or comparison, reason across the supplied resources rather than letting the first resource stand for the whole question. Explain only relationships established by the supplied Content; do not invent causes, mechanisms, definitions, or hidden premises.

[PROVENANCE]: Titles and URLs identify resources; Content is the evidence. Use no outside knowledge. When evidence is incomplete, state the boundary naturally. Never invent or alter resource identity or URL.

[RECOMMENDATION]: When the request asks what to read, recommend, or begin with, treat the adjudicated primary canonical resource as the first doorway and explain why it fits from supplied Content. Add companions only when the supplied evidence supports genuinely different routes.

[DESTINATION]: For explicit location or collection requests, use only evidence-established canonical destinations. Relevance is not destination or movement; say \"next\" only when D29 has explicitly validated a destination.

[SOVEREIGNTY]: Interpret the question, not the person. Do not diagnose, prescribe, psychologize, or tell the visitor what their experience means, should become, or should teach them. A specialized framework governs the answer only when the visitor names it; otherwise keep it attributed to the resource.

[COMPASSIONATE CARE]: For grief, bereavement, death, loss of a loved one, or another clearly vulnerable lived experience, respond gently and plainly. Describe what the resource explores. Do not state or imply that it provides or promises comfort, healing, peace, closure, meaning, purpose, hope, or another benefit to the visitor or to grieving people. Do not turn suffering into a required lesson or outcome. Attribute such framing to the source itself.

[VOICE]: Be a compassionate teacher: wise, humble, calm, emotionally intelligent, plain-spoken, and non-egoic. Preserve agency. Do not perform empathy, flatter, posture, or assume an inner state.

[OUTPUT]: Return only a finished visitor-facing answer inside <visitor_answer> tags. Use exact supplied canonical titles. No raw URLs, Markdown links, HTML, internal fields, process commentary, or reasoning."""


def estimate_output_chars(max_tokens: int = RECOMMENDATION_MAX_COMPLETION_TOKENS) -> int:
    return (max_tokens * 4 * 125 + 99) // 100


def fixed_input_chars(system_prompt: str, user_query: str, intent: str = "TOPICAL_INQUIRY") -> int:
    # This mirrors the production estimator's message-content basis. The exact
    # system message shape is intentionally represented explicitly here.
    user = f"Question: {user_query}\nIntent: {intent}\nEvidence:\n"
    return len(system_prompt) + len(user)


def preflight_capacity(system_prompt: str, user_query: str) -> dict:
    fixed = fixed_input_chars(system_prompt, user_query)
    reserve = estimate_output_chars()
    return {
        "fixed_input_chars": fixed,
        "estimated_output_chars": reserve,
        "input_capacity_remaining": MAX_PROVIDER_INPUT_CHARS - fixed,
        "total_capacity_remaining": MAX_PROVIDER_TOTAL_CHARS - fixed - reserve,
        "passes_fixed_envelope": fixed <= MAX_PROVIDER_INPUT_CHARS and fixed + reserve <= MAX_PROVIDER_TOTAL_CHARS,
    }


if __name__ == "__main__":
    probe = "What advise or essay from the Living Archive that you can recommend for someone who is grieving from the the death of a love one?"
    print(preflight_capacity(LEAN_PROMPT, probe))
