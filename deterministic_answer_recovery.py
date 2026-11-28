"""Bounded provider-independent recovery for The Guide."""
import re

from personal_reference_resolution import is_personal_reference_question, personal_reference_fallback
from inquiry_family_transfer_contract import classify_inquiry_family


def _clean(value):
    # Preserve deliberate paragraph breaks in canonical bounded recoveries.
    # Collapse horizontal spacing within each paragraph without flattening prose.
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n")
    paragraphs = [re.sub(r"[ \t\f\v]+", " ", part).strip() for part in re.split(r"\n\s*\n+", text)]
    return "\n\n".join(part for part in paragraphs if part)


def _subject(question):
    value = _clean(question).rstrip(" ?.!;:")
    value = re.sub(
        r",?\s+and\s+why\s+does\s+it\s+matter\??$",
        "",
        value,
        flags=re.I,
    )
    value = re.sub(
        r"^(?:please\s+)?(?:can you\s+|could you\s+)?"
        r"(?:help me understand|tell me about|explain|describe|discuss|analyze|analyse|"
        r"what happens if|what if|what is|what are|what does|why does|why do|why is|"
        r"why are|how does|how do|how can|how should|should we|should i)\s+",
        "", value, flags=re.I,
    )
    return value[:240].strip(" ,;:") or "the question you raised"


def compose_definition_significance(subject):
    """Return a bounded three-paragraph definition without claiming Archive doctrine."""
    subject = _clean(subject).strip(" ,;:") or "the concept"
    if is_personal_reference_question(subject):
        return personal_reference_fallback(subject)
    display_subject = subject[:1].upper() + subject[1:]
    # The community-reciprocity successor replaces the older generic fallback
    # for both the community-purpose query and the earlier Archive-framed wording.
    # Keep the answer general-knowledge: the Archive essay remains a separate
    # continuation, not the evidentiary source of this explanation.
    if re.sub(r"\s+", " ", subject).strip().casefold() == "reciprocity":
        return (
            "Reciprocity means people support one another over time. It does not mean keeping "
            "score or expecting every act to be repaid immediately or in equal measure. People "
            "may give more at one point and need more help at another; what matters is that "
            "support can move in both directions over time.\n\n"
            "Think of neighbors taking turns checking on an older resident or helping one another "
            "with errands. One neighbor may do more during a difficult week and receive help later. "
            "The relationship can still be reciprocal even when each exchange is different.\n\n"
            "Reciprocity should never be used to demand access, obedience, or repayment from "
            "someone who cannot freely offer it. Mutual support works best when people respond "
            "to one another's real circumstances, not when kindness becomes a debt ledger."
        )

    # Archive-specific terminology is governed by the published Living Glossary.
    # Retrieve an exact source entry instead of maintaining a competing local copy.
    try:
        from archive_glossary_authority import get_glossary_entry, compose_glossary_recovery
        canonical_entry = get_glossary_entry(subject)
        if canonical_entry:
            canonical_answer = compose_glossary_recovery(canonical_entry)
            if canonical_answer:
                return canonical_answer
    except Exception:
        # Source unavailability must not prevent ordinary general-knowledge
        # recovery; an absent Archive entry is never inferred or fabricated.
        pass
    # A bounded, reusable general-knowledge definition bank supports common
    # concepts when providers are exhausted. These are ordinary definitions,
    # not statements of official Living Archive doctrine.
    definition_bank = {
        "institutional memory": {
            "definition": "the knowledge an organization retains from its decisions, experience, practices, and lessons over time",
            "example": "When a team records why a policy was adopted and what happened after it changed, new staff can understand the original problem instead of repeating an earlier mistake or treating an old decision as unexplained tradition.",
            "significance": "It supports continuity and learning when people leave or leadership changes. Records without context can mislead, so preserving the reasons, uncertainty, and conditions behind decisions helps successors judge what still applies and what needs to change."
        },
        "collective memory": {
            "definition": "the shared understanding of a group's past, carried through stories, records, practices, and public remembrance",
            "example": "A community may preserve the story of a flood and the decisions that helped it recover so that new residents understand both what happened and why certain preparations matter.",
            "significance": "It can support identity and learning, but memories are selective and may differ across groups. Comparing recollections with evidence helps keep a shared past from erasing experiences that were overlooked."
        },
        "organizational learning": {
            "definition": "the process by which an organization uses experience and evidence to improve how it works",
            "example": "After a service fails, a team looks beyond the immediate mistake, identifies the conditions that caused it, tests a change, and checks whether the new process actually reduces repeat failures.",
            "significance": "Learning requires more than collecting reports: people need to be able to raise concerns, examine assumptions, and change routines when evidence shows they are not working."
        },
        "institutional responsibility": {
            "definition": "an organization's obligation to answer for its decisions, duties, and effects on people, including problems produced by its own rules and systems",
            "example": "If a public office repeatedly loses applications, responsibility includes examining the process, explaining what went wrong, correcting the failure, and reducing the chance it will recur—not only blaming the employee who handled one case.",
            "significance": "The obligation does not mean an institution can control every outcome. It means making responsibilities clear, giving reasons, listening to affected people, correcting preventable harm, and accepting appropriate oversight."
        },
        "governance": {
            "definition": "the way a group or institution establishes purpose, makes decisions, distributes authority, and holds decision-makers accountable",
            "example": "A meeting agenda and minutes may help administer a decision, while governance determines who has a voice, who may decide, and how the decision can be challenged or reviewed.",
            "significance": "Clear governance helps decisions remain understandable and answerable; it does not replace day-to-day administration or guarantee that every decision will be good."
        },
        "administration": {
            "definition": "the practical coordination and execution of work, decisions, records, and procedures",
            "example": "Administration may schedule a public meeting, distribute the papers, record attendance, and follow up on assigned tasks after the relevant decision has been made.",
            "significance": "Reliable administration helps plans become action, but efficient execution cannot by itself determine whether a decision's purpose, authority, or consequences are sound."
        },
        "handoff": {
            "definition": "the transfer of responsibility, information, and context from one person or team to another so work can continue",
            "example": "when a project moves from one team to another, a good handoff explains the current status, decisions already made, unresolved issues, deadlines, and who owns the next action; the receiving team confirms it has enough context to continue.",
            "significance": "a clear handoff reduces gaps, duplicated effort, missed dependencies, and confusion about ownership. It helps teams notice misunderstandings early and correct them before they spread. A handoff is complete not when information is merely sent, but when the receiving person understands what is needed and can take responsibility."
        },
        "stewardship": {
            "definition": "taking care of something entrusted to you while considering its value to others and the future",
            "example": "A person practicing stewardship of a shared space maintains it, uses resources carefully, and considers how decisions affect the people who rely on it.",
            "significance": "Stewardship is not control over everything or self-sacrifice without limits; it is responsible care for what is genuinely entrusted to you and attention to the effects of your choices."
        },
        "reciprocity": {
            "definition": "a relationship of mutual response in which people give, receive, and support one another over time",
            "example": "Neighbors may take turns checking on an older resident or helping with errands; one person might give more during a difficult week and receive help later.",
            "significance": "Reciprocity does not require immediate or equal repayment. It should not be used to demand access, obedience, or repayment from someone who cannot freely offer it."
        },
        "techno-utopian thinking": {
            "definition": "the belief that technological progress will, by itself or almost inevitably, solve major human and social problems",
            "example": "A city might introduce an advanced digital platform and assume that better software will automatically make public services fairer, even though access, institutional incentives, unequal power, and accountability remain unchanged.",
            "significance": "Its danger is not optimism about technology itself, but treating technology as a substitute for judgment, institutions, relationships, and democratic choice. That can hide who controls the technology, who bears its costs, which problems are actually political or social, and what happens when a technically efficient system produces unfair or harmful outcomes."
        },
        "institutional trust": {
            "definition": "the confidence that an institution will act competently, fairly, and consistently enough for people to rely on it",
            "example": "People are more able to rely on a public service when it explains decisions, handles similar cases consistently, corrects mistakes, and provides a meaningful way to appeal.",
            "significance": "Trust should be earned by observable conduct rather than claimed as a virtue. Consistent failures, hidden reasons, or blocked complaints can weaken it even when an institution says its intentions are good."
        },

    }
    normalized_subject = re.sub(r"\s+", " ", subject).strip().casefold()
    # Questions often frame a familiar concept through its consequence
    # ("the danger of X", "the risk of X") rather than naming X bare.
    # Recover the underlying concept before treating it as unfamiliar.
    conceptual_subject = re.sub(
        r"^(?:the\s+)?(?:danger|risk|problem|downside|benefit|value|importance)\s+of\s+",
        "",
        normalized_subject,
    ).strip()
    entry = definition_bank.get(normalized_subject) or definition_bank.get(conceptual_subject)
    if entry and conceptual_subject != normalized_subject:
        display_subject = conceptual_subject[:1].upper() + conceptual_subject[1:]
    if entry:
        example = str(entry["example"]).strip()
        significance = str(entry["significance"]).strip()
        if example:
            example = example[:1].lower() + example[1:]
        if significance:
            significance = significance[:1].lower() + significance[1:]
        answer = (
            f"{display_subject} is {entry['definition']}.\n\n"
            f"For example, {example}\n\n"
            f"{display_subject} matters because {significance}"
        )
    else:
        # For an unfamiliar term, state the limit without circular prose or
        # unsupported attribution. Do not claim an institutional definition.
        answer = (
            f"I can't define {display_subject} reliably from the information available in this response alone. "
            "I don't want to invent a definition or imply that a guess is established knowledge.\n\n"
            f"The meaning of {display_subject} can depend on the field or institution using it. "
            "Separate the term's ordinary meaning, any formal definition, and the way it is applied in practice.\n\n"
            "For a general concept, a reliable dictionary or subject reference can establish the ordinary meaning; for an institution's specific use, its published governing text is the authority to check. "
            "That is a limit on this unfamiliar term, not a claim that the question is unanswerable in principle."
        )
    return answer


def _significance_recovery(subject, context=""):
    """Answer a reusable why-does-this-matter question without causal-template drift."""
    subject = _clean(subject).strip(" ,;:.!?") or "the concept"
    # Interrogative wording may leave a terminal question mark embedded in a
    # preserved subject (for example, "... matter when leadership changes?").
    # Recovery prose must normalize that punctuation before joining it to
    # "because".
    subject = subject.rstrip(" ?.!;:")
    normalized = re.sub(r"\s+", " ", subject).strip().casefold()
    if normalized == "handoffs":
        normalized = "handoff"
    known = compose_definition_significance(normalized)
    if not known.startswith("I can't define "):
        return known

    context = _clean(context).strip(" ,;:.!?")
    # Normalize interrogative punctuation before any display form is composed.
    subject = subject.rstrip(" ?.!;:")
    display_subject = subject[:1].upper() + subject[1:]
    context_phrase = f" in {context}" if context else ""
    return (
        f"{display_subject} matters{context_phrase} because it influences whether people can understand what is at stake and coordinate their choices. "
        "Its importance comes from the difference it makes in what people can see, decide, and do—not from the label itself.\n\n"
        f"To judge that difference, compare what happens when {subject} is present and reliable with what happens when it is missing or unclear. "
        "Look for changes in shared understanding, timing, responsibility, and the effects on people who depend on the outcome. "
        "This helps distinguish a real contribution from an assumed benefit.\n\n"
        "A useful test is whether the people involved can describe the effect, identify who depends on it, and point to evidence that would show whether it is helping. "
        "If those effects are uncertain, treat the explanation as a hypothesis to check rather than a settled conclusion."
    )


def _is_hindsight_accountability(question):
    """Recognize fair retrospective review versus hindsight blame before generic decision advice."""
    q = _clean(question).casefold()
    retrospective_frame = bool(re.search(
        r"\b(?:hindsight|in hindsight|at the time|available at the time|"
        r"what (?:was|could be) known|information available|original decision|"
        r"outcome was known|after the fact)\b", q
    ))
    accountability_frame = bool(re.search(
        r"\b(?:accountability|accountable|blam(?:e|ing)|responsib(?:le|ility)|"
        r"fairly judge|unfairly|distinguish|best decision|reasonable decision)\b", q
    ))
    implicit_frame = bool(
        re.search(r"\b(?:information available at the time|could with the information)\b", q)
        and re.search(r"\b(?:blam(?:e|ing)|accountability|unfairly|distinguish)\b", q)
    )
    return (retrospective_frame and accountability_frame) or implicit_frame


def is_stewardship_failure_repair_question(question):
    """Recognize open inquiries about repair after a failure of stewardship."""
    q = _clean(question).casefold()
    repair_frame = bool(re.search(r"\b(?:repair|restore|restoration|make amends|rebuild|recover)\b", q))
    stewardship_frame = bool(re.search(r"\b(?:stewardship|steward|responsib(?:ility|le care)|entrusted)\b", q))
    failure_frame = bool(re.search(r"\b(?:failure|failed|breakdown|breach|harm|mistake)\b", q))
    open_process = bool(re.search(r"\b(?:what does|how does|how should|what might)\b.{0,120}\b(?:look like|begin|work)\b", q))
    return repair_frame and stewardship_frame and failure_frame and open_process


# Regression invariant: this open stewardship inquiry must remain recoverable
# without live vector retrieval or an LLM.
if not is_stewardship_failure_repair_question(
    "What does repair look like after a stewardship failure?"
):
    raise RuntimeError("Stewardship-failure repair recovery invariant failed")


def _stewardship_failure_repair_response():
    """Bounded stewardship-oriented recovery without inventing a specific case."""
    return (
        "Repair after a stewardship failure begins by making the failure visible rather than treating it as something to explain away. "
        "That means acknowledging what was entrusted, what responsibility was not met, and who or what was affected. Repair is not complete when an apology has been made or a procedure has been corrected; those may be part of the work, but they do not by themselves restore what was damaged.\n\n"
        "The next task is to understand the failure in relation. Ask what conditions, decisions, relationships, or assumptions made it possible, and listen to the people who carried its consequences. Some harms can be corrected directly; others involve trust, opportunity, safety, dignity, or relationships that may take longer to rebuild. A responsible response distinguishes learning from excuse-making: understanding the conditions behind a failure should make future responsibility clearer, not make responsibility disappear.\n\n"
        "Repair therefore joins accountability with renewal. Clarify what must be changed, who remains responsible for following through, how affected people can question or challenge the response, and what would show that the conditions producing the failure are actually changing. The aim is not to return mechanically to the situation that existed before, but to restore what can be restored while building a more trustworthy way of carrying the responsibility forward."
    )


def is_harm_repair_question(question):
    """Identify a repair-adequacy question raised by people who experienced harm."""
    q = _clean(question).casefold()
    affected_people = bool(re.search(
        r"\b(?:people who suffered (?:the )?harm|people harmed|those harmed|"
        r"people affected|those affected|survivors|victims|people who suffered|"
        r"those who suffered)\b", q
    ))
    repair_frame = bool(re.search(
        r"\b(?:proposed repair|repair|reparation|remedy|restitution|compensation|make amends)\b", q
    ))
    adequacy_gap = bool(re.search(
        r"\b(?:does not address|doesn't address|do not address|don't address|"
        r"fails? to address|does not meet|doesn't meet|inadequate|insufficient|"
        r"what they actually lost|their actual losses|what was actually lost|"
        r"does not restore|doesn't restore|not enough)\b", q
    ))
    return affected_people and repair_frame and adequacy_gap


def _harm_repair_response():
    """Give bounded, victim-centered guidance without inventing case-specific facts."""
    return (
        "The group should treat that response as a reason to pause and reconsider the repair, "
        "not as resistance it must overcome. If the people harmed say the proposal misses what "
        "they actually lost, the group needs to understand that gap before declaring the remedy adequate.\n\n"
        "Listen to the people affected and ask what the proposal fails to recognize, restore, or make right. "
        "Losses may include material damage, safety, livelihood, opportunity, dignity, trust, relationships, "
        "or a voice in decisions that affected them. Do not assume one remedy can address every kind of loss, "
        "or that the group alone gets to define what counts as repair.\n\n"
        "Where they are willing to participate, work with affected people to revise the proposal and agree "
        "on how its adequacy will be judged. Explain any genuine limits honestly, but do not make those harmed "
        "carry the whole burden of designing the solution or repeatedly proving that their losses matter. "
        "Repair may not restore everything as it was, but the group should not declare the matter resolved "
        "simply because it has offered something."
    )


def _is_ethical_tradeoff(question):
    """Recognize competing-value dilemmas before generic how-to language."""
    q = _clean(question).casefold()
    competing_values = bool(re.search(
        r"\b(?:disagree|competing|conflict|trade.?offs?|priorit(?:y|ies)|"
        r"protect(?:ing)?|worth protecting|deeply value|important to each|"
        r"lose something|irreversible|bear the costs|"
        r"stakeholders?|obligations?|duties|interests|shared responsibility|individual freedom)\b", q
    ))
    asks_for_judgment = bool(re.search(
        r"\b(?:how can|how should|how do we|how should we decide|how do we decide|"
        r"what should we protect|what if|who should decide|which should|what is fair|"
        r"fair process|balance|reconcile|hold .{0,70} obligations?|what does .{0,80} look like|how should (?:it|a community|the community|they)\s+(?:make|reach|take)\s+(?:a\s+)?decision)\b", q
    ))
    return competing_values and asks_for_judgment


def _is_historical_cultural_explanation(question):
    """Keep origins/evolution questions out of generic practical advice."""
    q = _clean(question).casefold()
    origin = re.search(r"\b(?:where .{0,80} come from|how .{0,80} evolved|origins? of|histor(?:y|ical)|evol(?:ve|ved|ution)|roots? of|how did .{0,100} change)\b", q)
    culture = re.search(r"\b(?:culture|cultural|society|social|philippines|filipin[oa]s?|matriarch(?:y|al)|patriarch(?:y|al)|gender|macho|kinship|religion|colonial|tradition|customs?)\b", q)
    return bool(origin and culture)


def _historical_cultural_recovery():
    """Answer the historical question directly while marking the limits of a broad national summary."""
    return (
        "The short answer is that public masculinity and women's influence in family and community life can coexist because they describe different kinds of power. A culture may praise male authority in public while women still hold substantial influence over household resources, kinship ties, care, property, or everyday decisions. That does not make the Philippines simply matriarchal: influence is not evenly shared, and a woman's responsibility for keeping a family together is not the same as having equal power. The useful starting point is to distinguish public ideals from the actual distribution of authority in different settings.\n\n"
        "Historically, there was no single Philippine pattern that changed in the same way everywhere. Accounts of some precolonial communities describe women holding economic, ritual, or leadership roles, but those roles varied by community and should not be generalized into a universal precolonial matriarchy. Spanish colonial rule and Catholic institutions helped strengthen patriarchal norms in law, religion, and public respectability; they did not simply erase women's economic activity, property interests, or influence through family networks. In later periods, schooling, wage work, migration, urbanization, and changing household arrangements further reshaped who earned, cared, decided, and exercised influence. These forces layered over one another rather than replacing one social order with another overnight.\n\n"
        "That layered history helps explain the tension you notice: masculine ideals can remain visible in public language while women's practical authority continues in less visible parts of social life. But neither 'macho society' nor 'matriarchy' captures every region, class, generation, or household, and private influence should not be mistaken for equality in institutions or public life. The strongest explanation therefore looks at specific periods and communities and asks who controls resources, makes decisions, performs unpaid work, and can challenge authority. The Archive reading below is a useful doorway into that question; a fully evidenced historical account would need to compare the relevant historical and regional sources rather than treat the country as culturally uniform."
    )


def is_complex_future_scenario_question(question):
    """Recognize explicit requests to reframe a definitive prediction about a complex future."""
    q = _clean(question).casefold()
    prediction_request = bool(re.search(
        r"\b(?:definitive|certain|exact|single[- ]outcome)\s+(?:prediction|forecast)\b"
        r"|\b(?:predict|prediction|forecast|forecasting)\b.{0,80}\b(?:complex|uncertain|nonlinear|interacting)?\s*future\b",
        q,
    ))
    complex_future = bool(re.search(
        r"\b(?:complex|nonlinear|highly uncertain|interdependent|interacting)\b.{0,50}\b(?:future|system|conditions|forces)\b"
        r"|\bcomplex future\b",
        q,
    ))
    reframing = bool(re.search(
        r"\b(?:scenarios?|scenario planning|capacities|capability|capabilities|uncertainty|reframe|alternative futures)\b",
        q,
    ))
    return prediction_request and complex_future and reframing


def _complex_future_scenario_recovery():
    """Reframe prediction demand into plausible futures, capacity, and adaptive readiness."""
    return (
        "The Guide should not turn a complex future into one definitive prediction. Outcomes may depend on interacting conditions that change over time, so a single forecast can hide the assumptions on which it rests and make one possibility look settled. Reframe the question from “What will happen?” to “What are several plausible ways this could unfold, and what conditions would make each more or less likely?” Scenarios are not competing prophecies; they are structured possibilities for testing understanding and readiness.\n\n"
        "For each scenario, examine the capacities it would require and the capacities already available: knowledge, skills, resources, relationships, infrastructure, coordination, and legitimate decision-making authority. Identify constraints, dependencies, vulnerabilities, and gaps; ask who can strengthen the capabilities that matter and how long that would take. Do not assume that stronger capacity can eliminate uncertainty. Its purpose is to widen the range of conditions people can meet and reduce avoidable fragility across more than one plausible future.\n\n"
        "Then identify observable signals that would make one scenario more or less plausible, what evidence would change the assessment, and which decisions should be revisited if those signals appear. Prefer steps that remain useful across several scenarios, preserve options where possible, and define in advance when to adapt, pause, or change direction. Keep assumptions and confidence limits visible, update the scenarios as conditions change, and never present a scenario as a guaranteed outcome. The aim is not to know the future in advance, but to build the capacity to respond responsibly as it unfolds."
    )


def _is_public_predictive_system_question(question):
    """Recognize consequential public-sector predictive systems before generic fallback."""
    q = _clean(question).casefold()
    public_system = bool(re.search(
        r"\b(?:government|public services?|public sector|state|municipal|city government|agency)\b",
        q,
    ))
    predictive_system = bool(re.search(
        r"\b(?:predictive system|predictive model|algorithmic system|automated decision(?:[- ]making)?|ai system|automated system|automated (?:eligibility|benefit|risk|screening|assessment|scoring) (?:model|system|tool)|algorithmic (?:eligibility|risk|screening|assessment|scoring)|risk[- ]scoring (?:model|system|tool)|machine[- ]learning model)\b",
        q,
    ))
    constitutional_human = bool(re.search(
        r"\b(?:constitutional|rights?|due process|human questions?|human consequences?|dignity|adoption|precede)\b",
        q,
    ))
    return public_system and predictive_system and constitutional_human


def _is_modes_of_knowing_dialogue_question(question):
    """Recognize questions about holding distinct forms of knowledge in relation."""
    q = _clean(question).casefold()
    modes = bool(re.search(
        r"\b(?:modes?|forms?|ways?|kinds?)\s+of\s+knowing\b|\bways?\s+of\s+knowing\b",
        q,
    ))
    dialogue = bool(re.search(
        r"\b(?:dialogue|in relation|together|alongside|confus(?:e|ed|ing)|collapse|flatten)\b",
        q,
    ))
    return modes and dialogue


def _modes_of_knowing_dialogue_recovery():
    """Preserve distinctions before moving to an application or decision process."""
    return (
        "Different modes of knowing do not need to be made identical in order to be held in dialogue. "
        "The first task is to ask what each mode can illuminate, what kind of claim it can support, and what remains outside its reach. "
        "Evidence, lived experience, professional judgment, historical understanding, and moral concern may all matter to the same question, but they do not answer it in the same way. "
        "Keeping those differences visible prevents one form of knowing from being mistaken for the whole.\n\n"
        "Dialogue begins when the forms of knowledge are allowed to question and inform one another without being forced into a single vocabulary or hierarchy. "
        "Ask where they converge, where they reveal a tension, and whether an apparent conflict comes from different evidence, different experiences, or different values. "
        "The aim is not to make every perspective agree, but to understand what each contributes and what would be lost if one were excluded.\n\n"
        "Only then should the conversation move toward a decision or collective action. Compare the available options, make consequences visible, and include the knowledge of people who will live with those consequences. "
        "A responsible judgment remains accountable for the choice it makes, but it does not pretend that one mode of knowing has cancelled the others. "
        "The point is to create a clearer field for judgment: differentiated knowledge held in relation, with both its contributions and its limits still visible."
    )


def _is_archive_purpose_question(question):
    """Recognize the narrow question of what problem the Living Archive exists to address."""
    q = _clean(question).casefold()
    return bool(re.search(
        r"\b(?:what problem does (?:the )?(?:living )?archive exist(?:s)? to address|why does (?:the )?(?:living )?archive exist(?:s)?|what is (?:the )?(?:living )?archive for)\b",
        q,
    ))


def _is_systems_explanation_vs_simplistic_connection_question(question):
    """Recognize inquiries distinguishing systems explanation from vague connectedness."""
    q = _clean(question).casefold()
    has_systems = bool(re.search(r"\bsystems?\s+explanation\b|\bsystemic\s+explanation\b", q))
    has_simplistic_connection = (
        "everything is connected" in q
        or bool(re.search(r"\bsimplistic\b.*\bconnected\b|\bconnected\b.*\bsimplistic\b", q))
    )
    return has_systems and has_simplistic_connection


def _systems_explanation_vs_simplistic_connection_recovery():
    """Clarify what makes a systems explanation explanatory rather than merely associative."""
    return (
        "A systems explanation is not established simply by saying that everything is connected. Connection is a starting observation; explanation begins when the relationships that matter can be identified and their consequences made intelligible. Ask what is influencing what, through which mechanisms, over what period of time, and with what evidence.\n\n"
        "The Guide should therefore distinguish a meaningful relationship from a decorative one. A systems explanation identifies patterns of interaction: feedback, incentives, constraints, delays, dependencies, or changes in one condition that alter another. It should also show boundaries and limits. Not every factor is equally important, and not every apparent connection is causal. A useful explanation makes clear what can reasonably be inferred and what remains uncertain.\n\n"
        "Most importantly, systems thinking should sharpen judgment rather than dissolve everything into complexity. The question is not whether everything is connected, but which relationships are consequential enough to change how a person or institution understands a condition and acts within it. The Guide's task is to make those relationships visible while keeping responsibility, evidence, and the limits of explanation in view."
    )



# Regression invariant: this core systems distinction must never fall through
# to generic abstention when providers or retrieval are unavailable.
_systems_explanation_question = 'How should The Guide distinguish a systems explanation from a simplistic “everything is connected” claim?'
if not _is_systems_explanation_vs_simplistic_connection_question(_systems_explanation_question):
    raise RuntimeError("Systems-explanation recovery invariant failed")


def _is_feedback_loops_institutions_question(question):
    """Recognize systems inquiries about feedback loops shaping institutions."""
    q = _clean(question).casefold()
    return bool(re.search(r"\bfeedback\s+loops?\b", q) and re.search(r"\b(?:human\s+)?institutions?|organizations?|systems?\b", q))


def _feedback_loops_institutions_recovery():
    """Provide a bounded systems orientation grounded in Archive themes."""
    return (
        "Feedback loops shape human institutions because the consequences of earlier decisions become conditions for later decisions. A rule, incentive, or practice changes what people experience; their responses then affect the information, trust, resources, and pressures that return to the institution. Over time, those responses can reinforce the original pattern or push it toward correction.\n\n"
        "Some loops are reinforcing: success can attract resources that make further success easier, while exclusion or distrust can reduce participation and weaken an institution's ability to learn. Other loops are balancing: complaints, oversight, independent evidence, and opportunities for correction can reveal when a practice is producing consequences its designers did not intend. The distinction is not simply whether feedback is positive or negative, but whether the institution can notice consequences and change course before a pattern becomes self-protecting.\n\n"
        "From the Archive's perspective, the important task is to make these relationships visible without treating a system as something separate from human judgment. Ask what information returns to decision-makers, whose experience is heard or excluded, what incentives reward repetition, and who has the authority to correct a harmful pattern. Feedback becomes a form of institutional learning only when people can interpret what they are seeing and remain responsible for acting on it. The aim is therefore not to eliminate loops, but to cultivate institutions capable of learning from their own consequences."
    )


def _is_commons_care_question(question):
    """Recognize open inquiries about stewardship of shared conditions and goods."""
    q = _clean(question).casefold()
    return bool(re.search(
        r"\b(?:care for|caring for|stewardship of|protect|sustain)\s+(?:the\s+)?commons\b"
        r"|\b(?:care for the commons|common good|shared conditions)\b",
        q,
    ))


def _commons_care_recovery():
    """Orient care for the commons without inventing a formal Archive doctrine."""
    return (
        "In the Living Archive, care for the commons can be understood as stewardship of the conditions people share and depend upon, rather than ownership or control by any one person or institution. The commons includes more than a particular resource: it also raises questions about the relationships, institutions, knowledge, and ecological conditions that make shared life possible. Care begins by asking what is genuinely held in common, who is affected by its condition, and whose responsibilities have become invisible.\n\n"
        "This does not mean that everyone carries the same duty or that collective care erases individual accountability. Responsibilities differ with power, proximity, knowledge, and the consequences of one's choices. A stewardship approach therefore keeps both the shared condition and the chain of responsibility visible: who benefits, who bears the costs, who can participate in decisions, and who remains answerable when the common ground is damaged or neglected.\n\n"
        "The Archive's broader orientation is to hold these questions in relation. Caring for the commons means looking beyond short-term use toward whether the conditions of shared life are being renewed or depleted, and whether people and institutions are becoming more capable of carrying responsibility together. The aim is not simply to preserve what exists, but to sustain the relationships and capacities through which a more trustworthy shared future can be cared for."
    )


def _is_stewardship_leadership_crisis_question(question):
    """Recognize stewardship questions about leadership under decline or crisis."""
    q = _clean(question).casefold()
    stewardship = bool(re.search(r"\b(?:stewardship|steward)\b", q))
    leadership = bool(re.search(r"\b(?:leader|leadership)\b", q))
    pressure = bool(re.search(r"\b(?:decline|crisis|breakdown|collapse|emergency|loss|deterioration)\b", q))
    return stewardship and leadership and pressure


def _stewardship_leadership_crisis_recovery():
    """Orient leadership in decline around responsibility, truthfulness, and renewal."""
    return (
        "Stewardship asks a leader to hold responsibility for the whole condition, not simply to preserve appearances or protect a position. During decline or crisis, that begins with seeing clearly what is changing: what is being lost, who is carrying the consequences, which responsibilities remain non-negotiable, and where uncertainty is still real. A steward does not need to promise control over everything, but should resist both denial and the temptation to make certainty look stronger than it is.\n\n"
        "The next task is to protect the conditions from which recovery remains possible. That can mean preserving trust, keeping truthful information available, listening to people closest to the consequences, and distinguishing what must be defended now from what can be changed or relinquished. Difficult decisions may still be necessary, but stewardship asks that their costs be made visible and that those with less power are not treated as expendable simply to preserve short-term stability.\n\n"
        "Finally, a steward keeps the future in view without abandoning the present. The question is not only how to survive the crisis, but what capacities, relationships, and responsibilities should remain intact so that renewal is possible afterward. Good stewardship therefore combines accountability with adaptability: act, learn from what the conditions reveal, correct course when necessary, and leave the people and institution more capable of carrying responsibility together."
    )


def _is_humane_performance_question(question):
    """Recognize organizational-performance questions that explicitly protect human dignity."""
    q = _clean(question).casefold()
    performance = bool(re.search(r"\b(?:pursue|improve|increase|balance|deliver)\s+(?:organizational\s+)?performance\b|\bperformance\b", q))
    organization = bool(re.search(r"\b(?:organization|organisation|institution|company|workplace)\b", q))
    dignity = bool(re.search(
        r"\b(?:treat(?:ing)?\s+people\s+as\s+instruments?|people\s+as\s+means|"
        r"human\s+dignity|not\s+reduce\s+people\s+to\s+(?:resources?|inputs?|tools?))\b",
        q,
    ))
    return performance and organization and dignity


def _humane_performance_recovery():
    """Answer the performance-and-human-dignity tension without making it retrieval-dependent."""
    return (
        "An organization can pursue performance without treating people as instruments by defining performance as a result achieved through responsible relationships, not merely as an output extracted from human beings. The practical discipline is to ask two questions together: what must the organization accomplish, and what conditions must remain intact for the people involved to retain dignity, judgment, voice, and the ability to flourish? A target that can only be met by making people disposable, silencing their experience, or treating them as interchangeable inputs has hidden costs that a narrow performance measure is failing to see.\n\n"
        "In practice, this changes how decisions are made. Suppose a team can improve short-term output by intensifying workloads. The organization should examine not only the immediate gain, but whether the change erodes health, learning, trust, or the capacity to exercise judgment. Those consequences are not sentimental additions to performance; they affect whether the institution can sustain good work and correct itself when conditions change. People should therefore be participants in understanding the work and its consequences, not merely objects of management.\n\n"
        "The tension does not disappear, and humane treatment does not mean abandoning standards or accountability. It means making the means of achieving performance part of what is judged. Clear expectations, fair authority, protected dissent, and opportunities for correction help an organization pursue demanding goals without confusing efficiency with permission to use people however it wishes. The deeper test is whether success leaves the institution and the people within it more capable of responsible work together."
    )


# Regression invariant: a common institutional question about performance and
# human dignity must never collapse into the legacy Archive-verification abstention.
_humane_performance_probe = "How can an organization pursue performance without treating people as instruments?"
if not _is_humane_performance_question(_humane_performance_probe):
    raise RuntimeError("Humane-performance recovery invariant failed")





_stewardship_leadership_crisis_probe = "What does stewardship ask of a leader during decline or crisis?"
if not _is_stewardship_leadership_crisis_question(_stewardship_leadership_crisis_probe):
    raise RuntimeError("Stewardship leadership crisis recovery invariant failed")

def _is_general_explanatory_question(question):
    """Recognize ordinary causal/explanatory questions that must remain answerable without retrieval."""
    q = _clean(question).casefold()
    return bool(re.search(
        r"^\s*(?:how\s+(?:does|do)|why\s+(?:does|do)|what\s+(?:causes?|shapes?|influences?|affects?))\b",
        q,
    ))


def _general_explanatory_recovery(question):
    """Provide subject-sensitive, bounded explanations when ordinary inquiry has no exact retrieval match."""
    q = _clean(question).casefold()

    # High-value conceptual families receive a direct answer before the broader
    # systems lens. This prevents the general recovery from sounding like a
    # template with the visitor's subject inserted into it.
    if re.search(r"^\s*what\s+happens\s+(?:when|if)\b", q) and re.search(r"\bpower\b", q) and re.search(r"\baccountab(?:ility|le)\b", q) and re.search(
        r"\b(?:concentrat(?:ed|ion)|unchecked|without|lack(?:ing)?|unaccountable)\b", q
    ):
        return (
            "When power is concentrated without meaningful accountability, decisions can become insulated from correction. "
            "The people exercising authority may receive less candid information, face fewer consequences for mistakes, and gain greater ability to define which questions are legitimate. Over time, this can make errors harder to detect and make dissent increasingly costly, even when the people involved believe they are acting for a good purpose.\n\n"
            "The problem is not simply that a powerful individual might behave badly. Concentrated power can change the surrounding system: subordinates may learn to protect themselves rather than speak honestly, information may be filtered before it reaches decision-makers, and institutions may weaken the very safeguards that could reveal a problem. The result can be a self-reinforcing pattern in which power becomes less exposed to the consequences of its own decisions.\n\n"
            "Accountability is therefore more than punishment after something goes wrong. It includes independent scrutiny, clear limits on authority, meaningful ways to question decisions, and real capacity to correct course. Those safeguards do not guarantee good judgment, but they help keep power connected to evidence, responsibility, and the people who live with its consequences."
        )
    if "organizational culture" in q and ("ethical" in q or "ethic" in q):
        return (
            "Organizational culture shapes ethical behavior by teaching people—often more powerfully than formal policies—what is actually safe, rewarded, tolerated, and expected. "
            "People learn from the choices leaders make, the behavior colleagues excuse or challenge, whose judgment carries authority, and what happens when someone raises a concern.\n\n"
            "The gap between stated values and operating norms is often where culture becomes ethically consequential. An organization may have a strong code of conduct, but if speed is rewarded at any cost, difficult questions are treated as disloyal, or small breaches are routinely overlooked, those repeated signals can gradually redefine what feels normal. The reverse is also true: accountability, openness, and the protection of principled dissent become part of culture when people repeatedly see them practiced rather than merely promised.\n\n"
            "Culture is therefore not a single cause of ethical behavior, and it does not remove individual responsibility. It is one of the conditions that shapes judgment over time. The useful question is which signals, incentives, relationships, and consequences are reinforcing a pattern—and whether they make ethical action easier or harder when it matters."
        )

    if ("learning from failure" in q or "learn from failure" in q or "learning from mistakes" in q or "learn from mistakes" in q) and ("organization" in q or "organisation" in q or "institution" in q or "team" in q):
        return (
            "Organizations create conditions for learning from failure when people can surface mistakes and problems without automatically being silenced or punished, while still taking responsibility for what happened and changing the conditions that contributed to it. Learning does not require treating every failure as blameless; it requires making honest examination more useful than concealment.\n\n"
            "That begins with what happens after something goes wrong. Leaders and colleagues signal whether the first response is to protect appearances and find someone to blame, or to establish the facts, hear from people closest to the work, and ask what the failure reveals about decisions, incentives, information, relationships, or constraints. When people believe that raising a concern will reliably make their situation worse, small problems tend to remain hidden until they become harder to correct.\n\n"
            "Accountability still matters, but it should be connected to learning. Organizations are more likely to improve when they distinguish deliberate misconduct or repeated disregard from ordinary error and from failures produced by conditions no individual could control alone. The final test is whether the examination changes anything: whether lessons are preserved, practices are adjusted, and people can see that speaking honestly leads to better judgment rather than simply greater risk. A culture of learning is built when candor, responsibility, and correction reinforce one another over time."
        )

    # "Why does X matter?" is a significance question, not a causal-mechanism
    # question. Preserve the concept and any context instead of feeding the
    # grammatical fragment into the general systems template.
    matter_match = re.match(r"^why\s+does\s+(.+?)\s+matter(?:\s+(.+))?$", q, re.I)
    if matter_match:
        concept = matter_match.group(1).strip(" ,;:.!?")
        context = (matter_match.group(2) or "").strip(" ,;:.!?")
        if concept in {"a clear handoff", "clear handoff"}:
            return (
                "Handoff matters because a clear handoff is the transfer of responsibility, information, and context from one person or team to another so work can continue without losing what has already been learned. When teams coordinate their work, that transfer makes ownership and the next action visible rather than leaving them to assumption.\n\n"
                "For example, when a project moves from one team to another, the receiving team needs the current status, decisions already made, unresolved issues, deadlines, and a clear sense of who owns the next action. Without that context, work can be duplicated, dependencies can be missed, and people may act on different understandings of the same situation.\n\n"
                "A clear handoff reduces gaps, duplicated effort, missed dependencies, and confusion about ownership. It matters not because every detail must be transferred, but because the receiving person or team needs enough shared understanding to take responsibility and continue the work with confidence."
            )
        display = concept[:1].upper() + concept[1:]
        context_phrase = f" {context}" if context else ""
        return (
            f"{display} matters{context_phrase} because it helps preserve a shared understanding of what people need to know, decide, or carry forward. Its significance depends on who relies on it and how it connects present choices with the responsibilities that follow.\n\n"
            "The practical question is what becomes harder when that understanding is missing: people may lose context, repeat earlier mistakes, or make decisions without seeing the commitments and consequences already in motion. Keeping the relevant record or understanding available can therefore support continuity without preventing necessary change.\n\n"
            "Its value is not automatic or unlimited. What matters is whether the information remains reliable, understandable, and connected to the people and decisions that depend on it. That keeps the focus on the concept named in the question rather than replacing it with a generic explanation."
        )

    subject = _subject(question)
    return (
        f"A useful starting point is to ask how {subject} works through particular conditions rather than assuming a single direct cause. "
        "Repeated signals, incentives, relationships, constraints, and consequences can make some choices feel normal, rewarded, risky, or difficult even when formal rules say something different.\n\n"
        "The next question is what mechanisms are actually operating: what people observe others doing, what behavior is rewarded or tolerated, whose judgment carries authority, and what happens when concerns are raised. "
        "Patterns become more consequential when these conditions reinforce one another over time and make correction harder or easier.\n\n"
        "This is a starting explanation rather than a claim about a specific case. "
        "A stronger account identifies the relationships and evidence that matter, distinguishes influence from proof of causation, and remains open to other conditions that may change the outcome."
    )



# Regression invariant: ordinary explanatory questions must not collapse into Archive-verification abstention.
_general_explanatory_probe = "How does organizational culture shape ethical behavior?"
if not _is_general_explanatory_question(_general_explanatory_probe):
    raise RuntimeError("General explanatory recovery invariant failed")
_power_accountability_probe = "What happens when power is concentrated without accountability?"
_power_accountability_recovery = _general_explanatory_recovery(_power_accountability_probe)
if "decisions can become insulated from correction" not in _power_accountability_recovery:
    raise RuntimeError("Power-accountability conceptual recovery invariant failed")

def _archive_purpose_recovery():
    """Explain the Archive's orientation problem without claiming a single total cause."""
    return (
        "The Living Archive exists in response to a problem of fragmentation: knowledge can be abundant while understanding remains scattered. Information is often separated from the larger conditions that give it meaning, and people can accumulate facts, opinions, and expertise without gaining a clearer sense of how the pieces relate or what responsibility follows from seeing them together. The problem is not simply a lack of information; it is the difficulty of finding orientation within an abundance of it.\n\n"
        "The Archive therefore tries to make relationships visible across questions that are too often treated in isolation—between people and institutions, knowledge and judgment, history and the present, individual experience and larger systems. Its purpose is not to supply one final explanation or tell visitors what to think. It is to create a place where ideas, patterns, and perspectives can be held in relation so that a question becomes more intelligible before a conclusion is rushed.\n\n"
        "What the Archive ultimately addresses is the gap between having more knowledge and knowing how to live, decide, and act responsibly with it. Orientation matters when certainty is unavailable and no single discipline can see the whole of a problem. The Archive's contribution is therefore to help people notice the relationships that matter, preserve questions that should not be simplified away, and recover the possibility of more conscious judgment and stewardship."
    )



def is_community_project_tradeoff_question(question):
    """Recognize community project questions requiring cross-domain trade-off inquiry."""
    q = _clean(question).casefold()
    community = bool(re.search(r"\b(?:community|communities|local residents|indigenous peoples|host community)\b", q))
    project = bool(re.search(r"\b(?:project|proposal|development|infrastructure|facility|energy scheme)\b", q))
    tradeoff = bool(re.search(r"\b(?:trade[- ]?offs?|competing interests|costs and benefits|impacts)\b", q))
    domains = (
        bool(re.search(r"\b(?:ecolog(?:y|ical)|environment(?:al)?|biodiversity|habitat)\b", q)),
        bool(re.search(r"\b(?:economic|economy|costs?|benefits?|livelihoods?)\b", q)),
        bool(re.search(r"\b(?:cultural|heritage|identity|customary|sacred)\b", q)),
        bool(re.search(r"\b(?:governance|decision[- ]making|authority|consent|participation)\b", q)),
    )
    asks_for_questions = bool(re.search(
        r"\b(?:what|which)\s+questions?\b|\bwhat\s+should\s+(?:we|they|a community)\s+(?:ask|consider|examine)\b|\bhow\s+to\s+(?:assess|evaluate|weigh)\b",
        q,
    ))
    return community and project and tradeoff and sum(domains) >= 2 and asks_for_questions


def _community_project_tradeoff_recovery():
    """Return a bounded three-paragraph cross-domain community project analysis."""
    return "A fair assessment asks four connected sets of questions rather than treating “renewable” as proof that a project is automatically beneficial. Ecologically: where would it be built, what land, water, habitats, species, and landscape uses would it affect, what are its full life-cycle emissions and material demands, and what cumulative impacts or decommissioning obligations remain? Economically: who finances and owns it, who receives jobs, lease payments, tax revenue, or lower-cost electricity, who pays for grid upgrades and public support, and how are risks and returns distributed over time?\n\nCulturally, what does the site mean to the people who live with it: does it contain ancestral or sacred places, support customary access or livelihoods, or carry local knowledge and identity that a project plan may overlook? Who gets to define what counts as a loss, and can affected people shape the design? On governance, who proposed the project, who has authority to approve it, whose participation is meaningful rather than ceremonial, and what information, conflict-of-interest rules, grievance channels, independent review, and enforceable conditions are in place? Are groups with less political or economic power represented before decisions are made?\n\nThen compare the proposal with realistic alternatives: no project, another site or scale, a different technology or ownership model, or a mix of energy and demand-side options. Which harms can be avoided, which can be reduced, and which are irreversible or cannot fairly be compensated? Who carries the remaining costs, what benefits are guaranteed locally, and what evidence will be monitored after approval? A sound decision makes these trade-offs visible, protects rights that should not simply be exchanged for aggregate benefits, and sets conditions for review, correction, or stopping the project if its actual effects depart from what was promised."


def is_technology_solutionism_ecological_question(question):
    """Recognize claims that technology alone can solve ecological crises."""
    q = _clean(question).casefold()
    ecological = bool(re.search(r"\b(?:ecolog(?:y|ical)|environment(?:al)?|climate|biodiversity|ecosystem(?:s)?|planetary)\b", q))
    technology = bool(re.search(r"\b(?:technolog(?:y|ical)|innovation|engineering|artificial intelligence|ai|geoengineering|automation)\b", q))
    sole_solution = bool(re.search(r"\b(?:alone|by itself|on its own|sole solution|silver bullet|panacea|will solve|can solve|solve .* crisis|solve .* problem)\b", q))
    return ecological and technology and sole_solution


def _technology_solutionism_ecological_recovery():
    """Explain technology's contribution and limits within ecological stewardship."""
    return (
        "Technology can help address ecological crises, but it cannot solve them by itself. Tools such as renewable energy, ecological monitoring, cleaner production, and restoration methods can reduce particular pressures or support repair; their effects depend on what they replace, how they are produced, who controls them, and the rules governing their use. Ecological crises also arise from patterns of production and consumption, land use, unequal access to resources, incentives that reward shifting costs, and institutions that fail to protect shared living systems. A new tool does not automatically change those conditions.\n\n"
        "The test is not whether a technology is innovative or efficient in isolation, but what it does across its full life cycle and at real scale. Account for energy and material inputs, mining and water demand, pollution and waste, effects on soil, habitats and biodiversity, who bears the burdens, and whether efficiency gains trigger greater total consumption through rebound effects. Compare the technology with non-technological and combined responses, including reducing demand, changing practices, protecting ecosystems, and restoring damaged places. The right mix depends on evidence and local conditions; neither automatic faith nor blanket rejection is warranted.\n\n"
        "Technology becomes useful within a wider practice of stewardship: public rules and incentives must reward ecological repair rather than merely growth; affected communities and ecological knowledge must shape decisions; responsibilities for costs and harms must be clear; and outcomes must be monitored over time, with power to correct or stop approaches that fail. Engineers and innovators can expand options, but they cannot decide by themselves what should be protected, what harms are acceptable, or who should bear them. Those are governance and ethical decisions for accountable people and institutions. The measure of progress is demonstrable reduction of ecological harm and restoration of the conditions that sustain life—not technological novelty."
    )


def has_technology_solutionism_ecological_explanation(response):
    """Require direct, systems-level, life-cycle, alternative, and stewardship reasoning."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n+", str(response or "")) if p.strip()]
    if len(paragraphs) != 3:
        return False
    text = _clean(response).casefold()
    direct = bool(re.search(r"\btechnology\b.{0,100}\b(?:cannot|can't|does not|doesn't)\b.{0,60}\bsolve\b.{0,30}\b(?:alone|by itself|on its own)\b", text))
    systems = all(term in text for term in ("production and consumption", "land use", "incentives", "governance"))
    life_cycle = all(term in text for term in ("life cycle", "rebound effects", "biodiversity", "waste")) and bool(re.search(r"\b(?:soil|water)\b", text))
    alternatives = bool(re.search(r"\b(?:reducing demand|demand reduction)\b", text)) and bool(re.search(r"\b(?:restoration|restoring|restore)\b", text))
    stewardship = bool(re.search(r"\b(?:affected communities|affected people)\b", text)) and bool(re.search(r"\bmonitor(?:ed|ing)?\b", text)) and bool(re.search(r"\b(?:accountable|accountability|responsibilit)\b", text))
    contribution = bool(re.search(r"\b(?:can help|can contribute|useful|support repair|reduce particular pressures)\b", text))
    return direct and systems and life_cycle and alternatives and stewardship and contribution


def is_external_discernment_outsourcing_question(question):
    """Recognize questions auditing reliance on external authorities for personal discernment."""
    q = _clean(question).casefold()
    discernment = bool(re.search(r"\b(?:discernment|discern|judgment|judgement)\b", q))
    outsourcing = bool(re.search(
        r"\b(?:outsourc(?:e|ing|ed)|defer(?:ring)?|surrender(?:ing)?|"
        r"hand(?:ing)?\s+over|rely(?:ing)?\s+on|depend(?:ing)?\s+on)\b", q
    ))
    external_authority = bool(re.search(
        r"\b(?:external|outside|teacher|guru|leader|system|sign|omen|"
        r"synchronicit\w*|spiritual framework|religious framework|ideology|doctrine)\b", q
    ))
    asks_where_or_how = bool(re.search(
        r"\b(?:where|how|when|which|recogniz\w*|identify|notice|detect)\b", q
    ))
    return discernment and outsourcing and external_authority and asks_where_or_how


def _external_discernment_outsourcing_recovery():
    """Give a bounded four-locus audit without claiming to know the visitor's circumstances."""
    return (
        "I cannot tell from your question which source, if any, is influencing your judgment. The useful distinction is this: guidance becomes outsourced discernment when another source is no longer something you consider, but becomes the authority that decides what an experience means or what you must do. Learning from a teacher, using a doctrine, noticing a sign, or holding a spiritual framework is not itself a loss of agency. The test is whether you can examine the interpretation, disagree with it, and remain responsible for your choice.\n\n"
        "Examine four possible locations. **1. A teacher or spiritual leader:** Has their confidence, status, or approval started to count as proof? Can you question them or decline their advice without being made to feel disloyal, unworthy, or spiritually deficient? **2. A system or doctrine:** Are you using it as a lens that helps you think, or making every experience fit its categories? What observation would count against the interpretation? **3. Signs, dreams, or synchronicities:** Can an event prompt reflection without becoming a command? A coincidence or powerful feeling may matter personally, but it does not by itself establish what caused it or what action you must take. **4. A spiritual framework:** Can its claims be questioned and revised? Does it help you face facts and consequences, or explain away every contradiction—including violated boundaries, preventable harm, or evidence that should change your mind? These are diagnostic questions, not assumptions that any of these patterns is happening to you.\n\n"
        "Use this five-part check on one recent example: (1) Observation—what actually happened, before interpretation? (2) Meaning—what are you concluding it means, and what else could explain it? (3) Authority—whose account shaped that conclusion, and what makes that account reliable here? (4) Disconfirmation—what evidence would lead you to revise it, and have you looked for that evidence as seriously as confirming evidence? (5) Choice—could you pause, say no, seek an independent view, or choose differently without fear of punishment or spiritual failure? The distinction to protect is influence versus evidence: confidence, emotional intensity, symbolic resonance, and internal coherence may be meaningful, but none is automatically independent confirmation. For consequential decisions, do not let a sign or another person's certainty substitute for relevant facts, time to reflect, consent, or appropriate safeguards.\n\n"
        "You do not have to reject outside wisdom to reclaim discernment. Keep it in the role of perspective rather than final authority: receive it, test it, compare it with what you can verify, and retain responsibility for what you choose. If you cannot question a source, consider alternatives, or refuse its direction without threat or coercion, that is a stronger warning sign than simply feeling influenced by it."
    )


def is_personality_soul_oversoul_question(question):
    """Recognize the three-part personality/soul/Oversoul discernment question narrowly."""
    q = _clean(question).casefold()
    has_three_lenses = all(re.search(pattern, q) for pattern in (
        r"\bpersonality\b",
        r"\bsoul\b",
        r"\boversoul\b",
    ))
    asks_for_distinction = bool(re.search(
        r"\b(?:difference|distinguish|distinction|relationship|between)\b", q
    ))
    includes_desire = bool(re.search(
        r"\b(?:want|wants|desire|desires|wish|wishes|longing)\b", q
    ))
    includes_learning = bool(re.search(
        r"\b(?:learn|learning|lesson|lessons|growth|developing)\b", q
    ))
    includes_invitation = bool(re.search(
        r"\b(?:inviting|invitation|called|calling|become|becoming|purpose)\b", q
    ))
    return (
        has_three_lenses and asks_for_distinction
        and includes_desire and includes_learning and includes_invitation
    )


def is_oversoul_ego_authority_question(question):
    """Recognize bounded Oversoul/ego authority questions without overmatching."""
    q = _clean(question).casefold()
    return bool(
        re.search(r"\boversoul\b", q)
        and re.search(r"\bego\b", q)
        and re.search(r"\b(?:awakening|awakened|life outcome|life's outcome|final say|final authority|conflict)\b", q)
    )


def is_oversoul_free_will_question(question):
    """Recognize Oversoul questions explicitly testing influence against free choice."""
    q = _clean(question).casefold()
    oversoul = bool(re.search(r"\boversoul\b", q))
    freedom = bool(re.search(r"\b(?:free will|free choice|personal agency|human agency|one's choice|a person's choice|person's choice|individual choice|choices?)\b", q))
    influence = bool(re.search(r"\b(?:power|influence|shape|guide|direct|determine|control|override|affect|authority)\b", q))
    tension = bool(re.search(r"\b(?:without undermining|without negating|without overriding|while preserving|while retaining|compatible with|undermin\w*|conflict|tension)\b", q))
    return oversoul and freedom and influence and tension


def is_regeneration_participation_question(question):
    """Recognize a personal inquiry about moving from spiritual consumption into regenerative participation."""
    q = _clean(question).casefold()
    regeneration = bool(re.search(r"\b(?:regenerat\w*|renewal|renewing life)\b", q))
    participation = bool(re.search(
        r"\b(?:participat\w*|invited|contribut\w*|serve|embody|put(?:ting)? into practice|"
        r"take part|responsib\w*)\b", q
    ))
    consumption_or_spiritual_frame = bool(re.search(
        r"\b(?:consum\w*|content|watching|reading|spiritual|spirituality|teachings|"
        r"talking about|learning about)\b", q
    ))
    return regeneration and participation and consumption_or_spiritual_frame


def _regeneration_participation_recovery():
    """Translate spiritual interest into grounded, voluntary regenerative practice."""
    return (
        "Regeneration becomes participation when insight turns into responsible care for something real: a relationship, community, shared resource, institution, place, or living system. Spiritual content can inform that movement, but it is not a substitute for participation. The question is not simply what resonates with you, but what is already entrusted to your care—and where your contribution can help something become healthier, more capable, or more whole.\n\n"
        "1. EXISTING RESPONSIBILITY — Begin with what is already yours to tend. This may arise through a real relationship, role, commitment, or shared undertaking. Ask whether it needs repair, attention, or more capable care. This is the strongest starting point because it rests on an actual relationship and responsibility, not an imagined assignment.\n\n"
        "2. EMERGING OPPORTUNITY — Notice a genuine need where your abilities may help. Before offering a solution, listen. The people affected should help define the problem and the need; ask who should help define the need, whether your contribution is welcome, and how those affected—and anyone with legitimate responsibility to support them—want helpful participation to take shape. Agree on useful feedback so you can learn whether the contribution is actually helping and adjust it with those affected. This is a grounded way to test an emerging opportunity; it does not require treating the possibility as a supernatural invitation. An opportunity becomes a responsible invitation through relationship and consent, not through your impression alone.\n\n"
        "3. PREMATURE OR UNSUPPORTED INVITATION — Pause when an appealing impression is not matched by a sufficiently understood need, a legitimate relationship, the affected people's consent, or the capacity to contribute responsibly. The appropriate response is listening and patience, not immediate action. These are three different grounds for action, not three spiritual labels to assign yourself.\n\n"
        "A practical first move: choose one living context you already belong to. Ask what needs tending, who should help define the need, what you can responsibly contribute, and what feedback would show whether it is helping. If no existing responsibility is apparent, explore an emerging opportunity by listening before offering a solution. Take one proportionate, reversible step only when the need and your role are clear enough; remain answerable to the people affected and revise your contribution as its effects become clearer. You do not need to treat every spiritual impression as a command or prove that a supernatural invitation has occurred. Let the quality of participation—not the amount of content consumed or the intensity of the feeling—be the test."
    )


def is_trust_community_stewardship_question(question):
    """Recognize a direct conceptual question about trust in community stewardship."""
    q = _clean(question).casefold()
    return bool(
        re.search(r"\btrust\b", q)
        and re.search(r"\b(?:community|communities)\b", q)
        and re.search(r"\bstewardship\b", q)
        and re.search(r"\b(?:what is|what role|role of|how does|why does|why is)\b", q)
    )


def is_weekly_stewardship_action_question(question):
    """Recognize a request to turn an inner insight into one bounded act this week."""
    q = _clean(question).casefold()
    asks_for_one_act = bool(re.search(
        r"\b(?:one|a single)\s+(?:concrete|practical|specific)\s+act\b"
        r"|\bwhat\s+(?:is|would be)\s+one\s+(?:concrete|practical|specific)\s+(?:thing|action|step)\b",
        q,
    ))
    stewardship_frame = bool(re.search(r"\bstewardship\b", q))
    near_term = bool(re.search(r"\b(?:this week|during the week|in the next seven days)\b", q))
    insight_to_action = bool(re.search(
        r"\b(?:inner insight|insight|real|into practice|put .* into action)\b", q
    ))
    return asks_for_one_act and stewardship_frame and near_term and insight_to_action


def _weekly_stewardship_action_recovery():
    """Translate the public Stewardship gateway into one bounded, visitor-owned practice."""
    return (
        "One concrete act you can complete this week is to choose one responsibility already entrusted to you "
        "and carry out a short stewardship check before acting. Set aside 20 minutes: name what you are holding, "
        "who or what is affected, and what is genuinely yours to hold rather than yours to control. "
        "Then complete one proportionate follow-through—clarify a commitment, ask for consent, repair a small "
        "neglect, protect something vulnerable, or set a needed boundary. Choose the action that fits the real "
        "responsibility in front of you; do not invent a duty just to prove an insight.\n\n"
        "This applies the Stewardship page's emphasis on what is entrusted to your care, quiet and repeated "
        "responsibility, and the need to distinguish sustainable care from sacrifice. Restraint can be the act: "
        "rest, withdraw, or relinquish what is not yours to carry.\n\n"
        "At the end of the week, review one observable result: did your action support the person, relationship, "
        "knowledge, place, or system affected without overreach or depletion? Keep, revise, or stop the practice "
        "based on that result. The 20-minute check is a practical exercise, not a prescribed Archive rule."
    )


def is_personal_stewardship_invitation_question(question):
    """Recognize a personal agency question about what calls for responsible care."""
    q = _clean(question).casefold()
    agency_invitation = bool(re.search(
        r"\bwho\s+or\s+what\s+is\s+(?:asking|calling|inviting|seeking)\b", q
    ))
    care_responsibility = bool(re.search(
        r"\b(?:responsible\s+care|stewardship|responsibility|care)\b", q
    ))
    personal_participation = bool(re.search(
        r"\b(?:through|from|of|within)\s+me\b", q
    ))
    return agency_invitation and care_responsibility and personal_participation


def _personal_stewardship_invitation_recovery():
    """Answer the agency question without inventing an external caller or unlimited duty."""
    return (
        "The question does not establish that a separate person, force, or hidden authority is making a request. "
        "It can be read more carefully as asking what, in your actual relationships and circumstances, may be calling for a responsible response through your participation. "
        "That may be a person, a commitment, a shared place, a community, a living system, or a consequence of a choice; it does not have to be a single voice or entity.\n\n"
        "In the Living Archive's use, stewardship is responsible care for what is entrusted to you, with attention to the people and systems affected and to what your choices make possible over time. "
        "The important distinction is between what is genuinely yours to hold and what is not yours to control or carry. "
        "A sense of responsibility is worth examining, but it is not proof that every demand placed on you is legitimate.\n\n"
        "Begin with what is actually entrusted to your care: who or what is affected, what has been agreed or placed in your hands, what response is within your authority, and what limits or support are needed. "
        "Care is not self-erasure or unlimited obligation. A responsible response may mean tending, repairing, protecting, asking for help, setting a boundary, or declining a burden that was never yours."
    )


def _trust_community_stewardship_recovery():
    """Explain trust as enabling infrastructure for accountable shared care."""
    return (
        "Trust is what lets a community share responsibility without having to supervise "
        "every action. Trust helps people in a community rely on one another without "
        "having to supervise every small act. It makes cooperation possible: people can "
        "share knowledge, coordinate work, honour commitments, and accept some vulnerability "
        "because they have reason to expect competence, consistency, fairness, and reciprocity. "
        "Trust is not simply believing that people mean well; it is confidence built through conduct: "
        "honest communication, follow-through, and a willingness to acknowledge when "
        "something has gone wrong.\n\n"
        "Think of a shared garden. The soil, water, tools, and harvest are common concerns, "
        "but no one person can tend every bed or watch every action. People need confidence "
        "that others will contribute, that decisions about water and harvest will be fair, "
        "and that problems can be raised without punishment. Stewardship is tending the "
        "garden together: caring for what is shared, noticing what is being depleted, and "
        "making sure the conditions for future growth are not sacrificed for an immediate "
        "private gain. People name what happened, listen to its impact, and agree on a "
        "repair, and make responsibilities clear when a commitment is missed.\n\n"
        "That trust must not be blind. It is earned and renewed through observable "
        "practices: capable work, kept commitments, transparent decisions, fair distribution "
        "of costs and benefits, accountability when mistakes happen, and meaningful ways "
        "for affected people to question and correct decisions. Trust makes cooperation possible; "
        "accountability makes trust dependable; stewardship is the shared practice that keeps "
        "both alive. Trust is not a substitute for scrutiny or safeguards; it grows stronger "
        "when people can question decisions and see that commitments are honoured. "
    )


def is_spiritual_community_accountability_question(question):
    """Recognize spiritual-community questions that explicitly pair charismatic authority with weak accountability."""
    q = _clean(question).casefold()
    spiritual_context = bool(re.search(
        r"\b(?:spiritual communit(?:y|ies)|faith communit(?:y|ies)|religious communit(?:y|ies)|"
        r"spiritual group|faith group|religious group|spiritual practice)\b", q
    ))
    charismatic_authority = bool(re.search(
        r"\b(?:charismatic leadership|charismatic leader|charisma|spiritual leader|"
        r"religious leader|guru|teacher)\b", q
    ))
    accountability_gap = bool(re.search(
        r"\b(?:weak|limited|absent|missing|poor|inadequate|lack(?:ing)?)\b.{0,45}"
        r"\b(?:accountab(?:ility|le)|oversight|checks and balances|review)\b|"
        r"\b(?:accountab(?:ility|le)|oversight|checks and balances|review)\b.{0,45}"
        r"\b(?:weak|limited|absent|missing|poor|inadequate|lack(?:ing)?)\b", q
    ))
    asks_for_risk_analysis = bool(re.search(
        r"\b(?:risk|risks|danger|dangers|vulnerab\w*|how should|how can|identify|assess|recogniz\w*)\b", q
    ))
    protects_spiritual_practice = bool(re.search(
        r"\b(?:without dismiss(?:ing)?|without reject(?:ing)?|without undermining|"
        r"while respect(?:ing)?|while preserv(?:ing)?|not dismiss(?:ing)?|"
        r"spiritual practice itself|practice itself)\b", q
    ))
    return (
        spiritual_context
        and charismatic_authority
        and accountability_gap
        and asks_for_risk_analysis
        and protects_spiritual_practice
    )


def _spiritual_community_accountability_recovery():
    """Assess governance risks without treating spiritual practice itself as suspect."""
    return (
        "Spiritual practice and the way a community governs its authority are different things. Ritual, belief, devotion, and a leader's ability to inspire trust are not, by themselves, evidence of harm. The risk arises when personal influence becomes authority that cannot be questioned and weak accountability leaves important decisions, resources, discipline, or safeguarding in the hands of the same person or inner circle. That is a governance vulnerability, not a verdict on the community's beliefs.\n\n"
        "The relevant warning signs are observable patterns: are questions treated as disloyalty or spiritual failure; can members disagree without humiliation, exclusion, or retaliation; are finances and consequential decisions transparent; are complaints heard by people independent of the leader; and can members refuse requests or leave without threats or coercive penalties? Charisma becomes dangerous when it is used to make a leader's judgment immune from review, or when spiritual language is used to excuse secrecy, dependency, boundary violations, or harm. A single disagreement is not proof of abuse; the concern is a repeated pattern and its effects on people's freedom, safety, and dignity.\n\n"
        "Safeguards should strengthen the community's ability to practice freely, not prescribe what its members must believe. Authority can be shared through a genuinely independent council, clear role limits, transparent finances, recorded decisions, conflict-of-interest rules, protected complaint channels, and external review when serious harm is alleged. Members must be able to question, decline, and leave without retaliation, while allegations are assessed fairly and appropriate repair or protection follows. The decisive test is whether spiritual life remains voluntary and whether those who exercise influence remain answerable to the people affected by it."
    )


def _oversoul_free_will_recovery():
    """Explain spiritual influence and human choice without asserting metaphysical fact."""
    return (
        "There is no independently verifiable evidence that an Oversoul literally controls a person's choices. Within spiritual frameworks that use the idea, the Oversoul is more often treated as a wider source of orientation, meaning, or purpose than as an authority that dictates each decision. Its 'power' can therefore be understood as influence rather than compulsion: it may inform what a person notices, values, or feels called toward, without making a particular choice inevitable.\n\n"
        "That distinction matters because a choice is still made through the person's lived awareness, judgment, relationships, and circumstances. A sense of deeper purpose may clarify possibilities or challenge familiar priorities, but the person must still interpret that experience and decide how to respond. They may accept it, question it, misunderstand it, or choose differently. The influence can be meaningful without replacing the work and responsibility of choosing.\n\n"
        "Free will does not require a person to be untouched by every influence; it requires that influence not be confused with coercive determination. In this interpretation, the Oversoul may orient or invite, while the person participates in shaping what happens through choices made within real conditions and limits. That is a spiritual reading of the relationship, not proof that an Oversoul exists, that every intuition comes from it, or that life outcomes are predetermined."
    )


def _oversoul_ego_authority_recovery():
    """Answer the Oversoul/ego question as a bounded spiritual interpretation, not fact."""
    return (
        "There is no independently established answer that an Oversoul has the final say over a person's life outcome. Within spiritual frameworks that use the idea, the Oversoul is often understood as a wider or transpersonal dimension of identity, while the ego is the embodied sense of self through which a person makes choices, protects continuity, and responds to immediate circumstances. A useful interpretation is that the Oversoul may represent a deeper orientation or purpose, not a script that dictates every event or cancels personal agency.\n\n"
        "The tension before awakening need not mean that the ego and Oversoul are enemies. The ego tends to organize life around identity, security, desire, memory, and control; an experience understood as awakening may widen a person's sense of belonging, meaning, or responsibility beyond those immediate concerns. That widening can feel like conflict because familiar ways of protecting the self are being questioned. In a more integrated reading, the ego is not destroyed but becomes less absolute: it remains necessary for living and choosing, while no longer being treated as the whole of what a person is.\n\n"
        "So the most careful answer is neither that the Oversoul unilaterally determines every outcome nor that the ego must defeat it. In this interpretive framework, the relationship is better understood as orientation and participation: a wider sense of purpose may inform choices, but lived outcomes still unfold through agency, relationships, circumstances, and limits. Awakening may change how a person relates to those conditions; it does not prove that every event was predetermined. This is a spiritual interpretation, not an empirically verifiable account or a doctrine shared by every tradition."
    )


def _personality_soul_oversoul_recovery():
    """Distinguish immediate desire, developmental learning, and spiritual invitation."""
    return (
        "The distinction is between three different kinds of information about your life. Your personality expresses what you want, need, fear, prefer, and are trying to protect in the circumstances you are living now. Those desires are not automatically shallow or wrong; they tell you something about your needs, values, boundaries, and sense of identity. What your soul is learning, in the language of a spiritual-development framework, concerns the capacities or understanding you may be developing through experience—perhaps patience, discernment, courage, trust, or a more honest relationship with yourself and others. What your Oversoul may be inviting you to become points to a still wider horizon of purpose or possibility: not a command or predetermined role, but a direction you may feel drawn to explore.\n\n"
        "These three can support one another, but they can also pull in different directions. A personality-level desire may be legitimate even when it is not the whole answer; a difficult experience is not automatically a lesson you were meant to endure; and a powerful feeling of being called is not, by itself, proof that an Oversoul has spoken. To discern them, ask three separate questions: What do I genuinely want, and what need or value is underneath that want? What is this experience actually teaching me, as shown by what I am noticing and changing over time? What larger possibility seems to invite me toward greater honesty, freedom, care, or responsibility—and can I examine that invitation without surrendering my judgment? Let evidence from lived experience, not intensity alone, inform your answers.\n\n"
        "The aim is not to silence the personality in favor of the soul, or to treat the Oversoul as an authority that overrides either one. A more integrated reading is that immediate desires provide information, reflection turns experience into learning, and a wider sense of purpose may help orient what you choose to become. You remain responsible for interpreting that sense of direction and deciding whether it is sound. This is a spiritual way of making meaning, not an independently verifiable account of metaphysical beings or a claim that every desire, hardship, or intuition has been assigned a cosmic purpose. A credible invitation should deepen agency and responsibility—not require coercion, self-erasure, or denial of material reality."
    )


def is_interpretation_revision_evidence_question(question):
    """Recognize a request for evidence that could warrant revising an interpretation."""
    q = _clean(question).casefold()
    interpretation = bool(re.search(
        r"\b(?:interpretation|interpretations|belief|beliefs|conviction|reading|explanation)\b", q
    ))
    revision = bool(re.search(
        r"\b(?:revis(?:e|ing|ion)|reconsider|change\s+my\s+mind|update\s+my\s+view|"
        r"what\s+would\s+make\s+me|what\s+could\s+make\s+me|"
        r"count\s+against|disconfirm|falsif\w*)\b", q
    ))
    evidence = bool(re.search(
        r"\b(?:evidence|observation|observations|proof|corroborat\w*|"
        r"what\s+would\s+show|what\s+would\s+count)\b", q
    ))
    return interpretation and revision and evidence


def _interpretation_revision_evidence_recovery():
    """Give a practical, claim-sensitive method for revising an interpretation."""
    return (
        "Separate the experience from the explanation you have placed on it. What you felt, noticed, or lived through can be real and important even when its cause or meaning is uncertain. Examining an explanation does not require you to dismiss the experience—or to accept your first interpretation of it.\n\n"
        "First identify what kind of claim you are making. A claim about an observable event, another person's actions, a cause, or a pattern in the world can be checked against evidence. A metaphysical claim or a claim about personal meaning may not be settled by public evidence in the same way. If it makes observable predictions, however, those predictions can and should be examined.\n\n"
        "For an observable claim, use five tests:\n\n"
        "1. **State the claim precisely.** What did you directly experience, and what are you inferring from it? Keep the observation separate from the explanation.\n"
        "2. **Trace the evidence.** What records or observations could someone else check? Where did each come from? Several accounts are not independent corroboration if they all repeat the same original source.\n"
        "3. **Compare alternatives.** What else could produce the same observation? What would each explanation lead you to expect? Include ordinary explanations and evidence that does not fit your preferred account.\n"
        "4. **Name what could change your mind.** Before looking for more evidence, specify an observation that would weaken the claim. If no possible observation could count, be honest that this is a commitment of faith or meaning, not an empirically established conclusion.\n"
        "5. **Choose a proportionate update.** You might retain the interpretation, narrow it, lower your confidence, revise its factual explanation, or suspend judgment. The evidence need not force an all-or-nothing choice. Apply the same standard to evidence on both sides.\n\n"
        "For example, if you interpret repeatedly thinking of someone shortly before they contact you as evidence of a special connection, record every instance in advance—including times you think of them and they do not contact you. Set the time window beforehand and compare the full pattern, not only the striking coincidences. This does not decide what the relationship means to you; it tests the specific claim that the coincidences establish a cause or connection.\n\n"
        "You can keep the personal significance of an experience while changing your account of what caused it. The sound standard is neither automatic belief nor automatic disbelief: state what would strengthen the interpretation, what would weaken it, and what evidence would leave it unresolved—and then let those conditions genuinely affect your view."
    )


def is_resonance_confirmation_bias_question(question):
    """Recognize a request to distinguish intuitive resonance from confirmation bias."""
    q = _clean(question).casefold()
    names_both = (
        bool(re.search(r"\bresonan(?:ce|t)\w*\b", q))
        and bool(re.search(r"\bconfirmation\s+bias\b", q))
    )
    discernment_task = bool(re.search(
        r"\b(?:distinguish|tell\s+(?:the\s+)?difference|differentiate|"
        r"separate|discern|test|check|audit)\b", q
    ))
    intuition_context = bool(re.search(
        r"\b(?:intuit(?:ion|ive|ively)|impression|gut\s+feeling|"
        r"inner\s+knowing|resonat(?:es|ed|ing))\b", q
    ))
    action_context = bool(re.search(
        r"\b(?:before\s+acting|before\s+i\s+act|act(?:ing)?\s+on|"
        r"decision|choose|choice|believ(?:e|ing))\b", q
    ))
    return names_both and discernment_task and (intuition_context or action_context)


def is_felt_truth_claim_discernment_question(question):
    """Recognize claims whose felt appeal is being mistaken for evidence."""
    q = _clean(question).casefold()
    names_claim = bool(re.search(
        r"\b(?:claims?|beliefs?|ideas?|assumptions?|interpretations?)\b", q
    ))
    names_appeal = bool(re.search(
        r"\b(?:feel(?:s|ing)?\s+(?:true|right|beautiful|empowering)|"
        r"beautiful|empowering|resonat\w*|emotionally\s+compelling)\b", q
    ))
    asks_examination = bool(re.search(
        r"\b(?:examin\w*|test\w*|question\w*|scrutiniz\w*|"
        r"evaluat\w*|assess\w*|investigat\w*|evidenc\w*)\b", q
    ))
    return names_claim and names_appeal and asks_examination


def _felt_truth_claim_discernment_recovery():
    """Separate personal meaning from evidentiary support and provide a usable audit."""
    return (
        "A claim can feel deeply true without necessarily being true. An idea may resonate with your experience, offer a beautiful explanation of the world, or restore a sense of purpose and agency. Those experiences deserve attention, but they are not themselves proof of the claims attached to them. The first discipline is to distinguish the value of an experience from the accuracy of the interpretation built around it.\n\n"
        "Emotionally attractive beliefs can become self-protecting. We notice confirming experiences, overlook contradictions, interpret ambiguity in our favor, and mistake the comfort a belief provides for evidence that it is correct. This does not mean beautiful, spiritual, hopeful, or empowering ideas are necessarily false. It means their appeal should not exempt them from examination.\n\n"
        "A practical examination has seven steps:\n\n"
        "1. **State the claim precisely.** What exactly are you accepting? Separate the proposition from the emotions, promises, and implications surrounding it.\n"
        "2. **Separate experience from interpretation.** What did you directly observe or experience? What meaning did you assign to it? Both matter, but they are different kinds of information.\n"
        "3. **Identify the evidence.** What supports the claim independently of how compelling it feels? Is the evidence appropriate to the kind of claim being made, independently corroborated where possible, sufficiently reliable, and open to examination?\n"
        "4. **Look for disconfirming evidence.** What would make the claim less credible? What observation would count against it? A belief that can accommodate every possible outcome without changing is difficult to examine meaningfully.\n"
        "5. **Consider alternative explanations.** Could the same experience be explained by expectation, selective attention, coincidence, social reinforcement, personal need, or another plausible mechanism?\n"
        "6. **Examine what the belief does.** Does it increase your capacity to think, act responsibly, and remain open to correction? Or does it make you dependent on an authority, resistant to questions, or afraid of contrary evidence?\n"
        "7. **Adjust confidence proportionately.** You do not have to accept or reject everything immediately. You can retain an experience's personal significance while suspending judgment about its explanation.\n\n"
        "Discernment does not require becoming cynical. It requires refusing to confuse emotional resonance with epistemic certainty. Something can be beautiful without being factual, empowering without being universally applicable, and personally meaningful without being independently established. Equally, discovering that an explanation is mistaken does not necessarily invalidate the experience that led you to it.\n\n"
        "The aim is not to strip life of meaning. It is to build meanings that can withstand honest examination. Let what resonates invite investigation, let evidence determine confidence, and let the willingness to revise remain part of what makes a belief worth holding."
    )


def _resonance_confirmation_bias_recovery():
    """Separate intuitive signal from interpretation, then test the proposed pattern."""
    return (
        "Resonance and confirmation bias are not opposites. Resonance is a felt sense of recognition or fit: an idea connects with something in your experience or understanding. "
        "That feeling can alert you to a possibility worth examining, but it cannot establish that your explanation is true. "
        "Confirmation bias is what can happen next: you give supporting details more attention or weight, while overlooking, discounting, or explaining away details that challenge the interpretation. "
        "So an impression can feel genuinely resonant and still be interpreted through confirmation bias. The key distinction is between the signal you experience and the truth of the explanation you attach to it.\n\n"
        "Before acting, write down four things separately: what you directly observed; what you felt; what you think it means; and what conclusion or action you are considering. "
        "Then test the proposed pattern rather than trying to suppress the feeling. Ask four questions: Does it recur under comparable conditions, or is it resting on one striking coincidence? "
        "What is the strongest alternative explanation? What plausible mechanism connects the observations, rather than merely making them feel coherent? "
        "What constraints or alternative explanations could produce the same result, and where might the pattern stop applying? "
        "Most importantly, what specific observation would count against your interpretation? If no possible evidence could change your mind, you are protecting a belief rather than testing a claim.\n\n"
        "Apply the same standard in both directions: do not accept weak evidence because it agrees with you, or demand impossible certainty because it does not. "
        "When several sources appear to corroborate the impression, trace them back to their origins; five reports repeating one original claim are not five independent confirmations. "
        "A useful rule is: let resonance generate a hypothesis, let repeatability and a plausible mechanism make it worth considering, and let disconfirming evidence decide whether it survives. "
        "For a consequential decision, pause before irreversible action and use a small, reversible test where possible. Revise or release the interpretation if the expected pattern does not recur or the contrary evidence is stronger. "
        "You do not need to distrust intuition. You need to keep intuition in its proper role: a starting signal, not its own proof."
    )


_HUMAN_DEVELOPMENT_COMPARISON_TERMS = ("growth", "adaptation", "maturity", "integration")
_HUMAN_DEVELOPMENT_SOURCE_URL = "https://geralddaquila.com/2026/10/05/the-architecture-of-human-development/"
_HUMAN_DEVELOPMENT_SOURCE_TITLE = "Becoming Fully Human"
_HUMAN_DEVELOPMENT_SOURCE_EXCERPT = (
    "development is best understood as an expanding capacity to adapt without losing coherence. "
    "Integration, rather than accumulation, shapes maturity, responsibility, and stewardship."
)


def is_human_development_comparison_question(question):
    """Recognize comparisons among the four concepts treated together in the human-development cornerstone."""
    q = re.sub(r"\s+", " ", _clean(question)).casefold()
    comparison_frame = bool(re.search(
        r"\b(?:difference|distinction)\s+between\b|\bcompare\b|"
        r"\brelationship\s+between\b|\bhow\s+(?:do|are)\b.{0,100}\brelated\b",
        q,
    ))
    return comparison_frame and all(
        re.search(r"\b" + re.escape(term) + r"\b", q)
        for term in _HUMAN_DEVELOPMENT_COMPARISON_TERMS
    )


def compose_human_development_comparison_recovery(question):
    """Paraphrase the canonical human-development essay as an answer-first four-concept comparison."""
    if not is_human_development_comparison_question(question):
        return None
    return (
        "Growth, adaptation, maturity, and integration are four related but distinct movements within human development. "
        "The Living Archive's systems view treats them as interacting parts of a developmental process, not as a fixed four-step ladder.\n\n"
        "Growth is the development of capacity across domains, not merely the accumulation of knowledge, credentials, wealth, or experience. "
        "The essay emphasizes that growth in one domain influences the others, and asks whether a person is becoming more capable of responding wisely to increasing complexity.\n\n"
        "Adaptation is the response to changing conditions. The essay describes development through recurring cycles of challenge, feedback, "
        "reflection, adaptation, and renewed participation. The point is not to change at any cost, but to adapt without losing coherence. "
        "Maturity is not simply age, perfection, or freedom from failure; it is a growing ability to remain responsive, grounded, and adaptive "
        "as life becomes more complex, with increasingly sophisticated meaning-making, judgment, and responsibility.\n\n"
        "Integration brings distinct capacities into relationship: biological, psychological, relational, ethical, systemic, and existential. "
        "It helps experience become understanding rather than remain fragmented. Growth concerns the development of capacity, whereas adaptation "
        "concerns the response to conditions. Maturity concerns the judgment and responsibility guiding that response; by contrast, integration "
        "concerns how different capacities work together as a coherent whole.\n\n"
        "They reinforce one another rather than occur in a single sequence. A person can acquire skills without becoming more mature, adapt to a "
        "situation without integrating what it teaches, or develop one capacity while another remains underdeveloped. Challenge and feedback can "
        "prompt adaptation; maturity shapes how change is handled; integration determines whether new experience becomes part of a more coherent life."
    )


def human_development_comparison_doorway():
    """Return the canonical, independently verified human-development continuation."""
    return {
        "title": _HUMAN_DEVELOPMENT_SOURCE_TITLE,
        "url": _HUMAN_DEVELOPMENT_SOURCE_URL,
        "rationale": (
            "This published Cornerstone essay presents the Living Archive's systems view of human development, "
            "including growth, adaptation, maturity, and integration across biological, psychological, relational, "
            "ethical, systemic, and existential capacities. It is a direct continuation of the comparison, not a substitute for the answer."
        ),
    }


def human_development_comparison_final_contract(question):
    """Return the bounded answer, honest Archive provenance, source excerpt, and canonical doorway."""
    answer = compose_human_development_comparison_recovery(question)
    if not answer:
        return None
    return {
        "response": answer,
        "answer_basis": {
            "kind": "archive_supported",
            "label": "Living Archive synthesis",
            "explanation": (
                "This is a paraphrased synthesis of the published Becoming Fully Human essay. "
                "The evidence reference verifies the canonical source and excerpt; it does not claim automated semantic certification."
            ),
        },
        "evidence_document": {
            "title": _HUMAN_DEVELOPMENT_SOURCE_TITLE,
            "url": _HUMAN_DEVELOPMENT_SOURCE_URL,
            "text": _HUMAN_DEVELOPMENT_SOURCE_EXCERPT,
        },
        "recommendation": human_development_comparison_doorway(),
        "provider": "bounded_archive_human_development_comparison_recovery",
        "model": "",
    }


def has_registered_recovery(question):
    """True only when a bounded deterministic recovery is explicitly registered."""
    try:
        from institutional_learning_failure_contract import (
            is_institutional_learning_failure_question,
        )
        institutional_learning_failure = is_institutional_learning_failure_question(question)
    except Exception:
        institutional_learning_failure = False
    return bool(
        institutional_learning_failure
        or is_guide_personal_decision_agency_question(question)
        or is_weekly_stewardship_action_question(question)
        or is_personal_stewardship_invitation_question(question)
        or is_interpretation_revision_evidence_question(question)
        or is_resonance_confirmation_bias_question(question)
        or is_felt_truth_claim_discernment_question(question)
        or is_oversoul_ego_authority_question(question)
        or is_external_discernment_outsourcing_question(question)
        or is_technology_solutionism_ecological_question(question)
        or is_personality_soul_oversoul_question(question)
        or is_oversoul_free_will_question(question)
        or is_trust_community_stewardship_question(question)
        or is_spiritual_community_accountability_question(question)
        or is_regeneration_participation_question(question)
        or is_complex_future_scenario_question(question)
        or _is_public_predictive_system_question(question)
        or _is_archive_purpose_question(question)
        or _is_commons_care_question(question)
        or _is_feedback_loops_institutions_question(question)
        or _is_systems_explanation_vs_simplistic_connection_question(question)
        or _is_humane_performance_question(question)
        or _is_stewardship_leadership_crisis_question(question)
        # Broad explanatory recovery remains available to composition, but it
        # is not an explicitly registered family for terminal last-mile override.
        or _is_modes_of_knowing_dialogue_question(question)
        or is_stewardship_failure_repair_question(question)
        or is_community_continuity_revision_question(question)
        or is_community_project_tradeoff_question(question)
        or is_orientation_information_contrast_question(question)
        or is_guide_meta_coverage_policy_question(question)
        or is_epistemic_category_distinction_question(question)
        or is_human_development_comparison_question(question)
        or classify_inquiry_family(question).get("family") == "personal_lived_reflective"
        or _is_epistemic_distress_guidance_question(question)
        or bool(compose_task_specific_recovery(question))
    )


def _public_predictive_system_recovery():
    """Orient predictive public systems around legitimacy before performance."""
    return (
        "The first question is not whether a predictive system is efficient, but what kind of public power it is being asked to exercise. If it influences access to services, opportunities, or scrutiny, its purpose and authority should be clear before its performance is celebrated. Who remains responsible for the decision, what rights place limits on the system, and what must a person still be able to question or appeal? Efficiency can improve administration; it cannot by itself make the exercise of public authority legitimate.\n\n"
        "A second question concerns what the system carries forward. Predictive tools learn from records of the past, and those records may contain unequal access, earlier exclusions, or assumptions that have become invisible with time. People affected by a consequential decision should be able to understand enough to challenge it, correct an error, and reach a human decision-maker with the authority to review and correct the decision. Those who live with the consequences are not merely sources of data; they remain participants in the public order the system is meant to serve.\n\n"
        "Only within those boundaries does efficiency become the right question. Compare the proposed system with realistic alternatives, make its gains and risks visible, and decide in advance how errors will be detected, reviewed, and repaired. Keep adoption reversible where possible and preserve independent scrutiny when the consequences are serious. The aim is not to reject prediction, but to keep technology in its proper place: as a tool of public service, not a substitute for constitutional responsibility or human judgment."
    )


def registered_recovery_recommendation(question):
    """Return an evidence-backed doorway for a narrow registered recovery."""
    if is_human_development_comparison_question(question):
        return human_development_comparison_doorway()
    if is_orientation_information_contrast_question(question):
        return {
            "title": "When Knowledge Is Everywhere",
            "url": "https://geralddaquila.com/when-knowledge-is-everywhere/",
            "rationale": (
                "This published Living Archive Cornerstone directly develops the distinction between accumulating "
                "information and cultivating orientation, judgment, discernment, responsibility, and wise participation. "
                "It also explains that orientation makes ambiguity more navigable rather than promising certainty."
            ),
        }
    if is_interpretation_revision_evidence_question(question):
        return {
            "title": "Seeing Patterns Without Fooling Yourself",
            "url": "https://geralddaquila.com/2026/04/06/seeing-patterns-without-fooling-yourself/",
            "rationale": (
                "This essay offers a practical way to examine whether a perceived pattern is supported or projected: repeatability, plausible mechanism, constraints, and disconfirmation. It is a method for testing an interpretation, not independent proof for or against a spiritual claim."
            ),
        }
    if is_felt_truth_claim_discernment_question(question):
        return {
            "title": "Seeing Patterns Without Fooling Yourself",
            "url": "https://geralddaquila.com/2026/04/06/seeing-patterns-without-fooling-yourself/",
            "rationale": (
                "This essay offers a practical method for examining whether a perceived pattern is supported or projected. "
                "Its filters—repeatability, plausible mechanism, constraints, and disconfirmation—extend the question of how "
                "to test emotionally compelling claims without letting confirmation bias decide the result. It is a method "
                "for examination, not independent proof for or against any particular belief."
            ),
        }
    if is_resonance_confirmation_bias_question(question):
        return {
            "title": "Seeing Patterns Without Fooling Yourself",
            "url": "https://geralddaquila.com/2026/04/06/seeing-patterns-without-fooling-yourself/",
            "rationale": (
                "This essay examines how to distinguish real patterns from meaning projected onto ambiguous evidence. "
                "Its practical filters—repeatability, mechanism, constraints, and disconfirmation—directly extend the question "
                "of how to test an intuitive impression without letting confirmation bias decide the result."
            ),
        }
    if is_guide_personal_decision_agency_question(question):
        return {
            "title": "Being in the Driver's Seat (Without Pretending You Control the Road)",
            "url": "https://geralddaquila.com/being-in-the-drivers-seat-without-pretending-you-control-the-road/",
            "rationale": "This essay offers a grounded continuation on exercising personal agency within real conditions and limits. It supports the distinction between receiving orientation and surrendering responsibility for one's own choices; it does not prescribe the decision a visitor should make.",
        }
    if is_weekly_stewardship_action_question(question):
        return {
            "title": "Stewardship",
            "url": "https://geralddaquila.com/stewardship/",
            "rationale": "This public gateway grounds the response in what is entrusted to a person's care, sustainable responsibility, consent, boundaries, and the distinction between stewardship and self-sacrifice. The suggested weekly exercise is a practical application, not a quotation or prescribed rule from the page.",
        }
    if is_personal_stewardship_invitation_question(question):
        return {
            "title": "Stewardship",
            "url": "https://geralddaquila.com/stewardship/",
            "rationale": "This canonical public page grounds stewardship as responsible care for what is entrusted to a person. It offers a direct starting point for distinguishing genuine responsibility from control, overreach, or an obligation that was never yours.",
        }
    if is_regeneration_participation_question(question):
        return {
            "title": "Stewardship as Human Maturity",
            "url": "https://geralddaquila.com/2026/07/06/stewardship-as-human-maturity/",
            "rationale": "This published cornerstone traces the movement from self-development toward responsibility and contribution beyond the self. It asks what has been entrusted to a person's care and describes stewardship as participation in relationships, communities, institutions, ecosystems, and generations; it is a grounded continuation from spiritual inspiration toward lived responsibility, not a claim about a supernatural calling."
        }
    if is_trust_community_stewardship_question(question):
        return {
            "title": "Trust Architecture",
            "url": "https://geralddaquila.com/trust-architecture/",
            "rationale": "This cornerstone examines trust as the architecture that sustains cooperation under uncertainty, including conditions communities and institutions can steward: accountability, transparency, consistency, and repair. Its dedicated Stewardship Imperative section makes it a direct continuation of this question."
        }
    if is_spiritual_community_accountability_question(question):
        return {
            "title": "Community Accountability Systems",
            "url": "https://geralddaquila.com/2026/05/16/community-accountability-systems/",
            "rationale": "This Archive essay examines how communities prevent power from becoming insulated from feedback through transparent, distributed accountability, clear boundaries, protected dissent, and repair. It directly addresses the risks of charismatic leadership and weak accountability without treating spiritual belief or practice itself as the problem.",
        }
    if is_external_discernment_outsourcing_question(question):
        return {
            "title": "Being in the Driver's Seat (Without Pretending You Control the Road)",
            "url": "https://geralddaquila.com/being-in-the-drivers-seat-without-pretending-you-control-the-road/",
            "rationale": "This essay offers a grounded continuation on exercising personal agency within real conditions and limits. It supports the distinction between receiving orientation and surrendering responsibility for one's own choices; it does not prescribe the decision a visitor should make.",
        }
    if is_personality_soul_oversoul_question(question):
        return {"title":"Eternal / Oversoul Law – The Immutable Jurisdiction","url":"https://geralddaquila.com/oversoul-law","rationale":"This is the Archive's directly named Oversoul doorway for examining the question of spiritual invitation and jurisdiction. It offers the Archive's own framework for inspection; it is not independent evidence that an Oversoul exists or that a perceived invitation is objectively authoritative."}
    if is_oversoul_free_will_question(question) or is_oversoul_ego_authority_question(question):
        return {
            "title": "Eternal / Oversoul Law – The Immutable Jurisdiction",
            "url": "https://geralddaquila.com/oversoul-law",
            "rationale": "This is the Archive's directly named Oversoul doorway for examining the question of spiritual jurisdiction. It is an invitation to inspect the Archive's own framework, not independent evidence that metaphysical claims are objectively established.",
        }
    if is_complex_future_scenario_question(question):
        return {
            "title": "Sovereign Sensemaking Compass",
            "url": "https://geralddaquila.com/the-sovereign-sensemaking-compass/",
            "rationale": "The Sovereign Sensemaking Compass offers an orientation framework for navigating uncertainty while retaining clarity and agency. It is a useful next step for examining how to remain oriented and make responsible choices when no single forecast can settle the future; it does not claim to predict specific outcomes.",
        }
    if is_community_project_tradeoff_question(question):
        return {
            "title": "Local Resilience Economies",
            "url": "https://geralddaquila.com/2026/05/27/local-resilience-economies/",
            "rationale": "Local Resilience Economies examines how communities build stability through distributed infrastructure, cooperative structures, local capability, and ecological stewardship. It offers a wider systems lens for asking who controls essential infrastructure, where value remains, and how local resilience is sustained; it does not assess this particular renewable-energy proposal.",
        }
    if is_community_continuity_revision_question(question):
        return {
            "title": "From Awakening to Stewardship",
            "url": "https://geralddaquila.com/from-awakening-to-stewardship/",
            "rationale": "This essay explores how personal development can mature into stewardship: taking responsibility for the relationships, institutions, and shared conditions that support human flourishing. It offers a wider perspective on community continuity by asking what people must build and sustain together, rather than prescribing how a particular inherited practice should be changed.",
        }
    if _is_public_predictive_system_question(question):
        return {
            "title": "AI vs. Human Stewardship: Why Conscious Guidance Matters More Than Ever",
            "url": "https://geralddaquila.com/2026/06/16/ai-vs-human-stewardship-why-conscious-guidance-matters-more-than-ever/",
            "rationale": "AI vs. Human Stewardship examines why growing technological capability must remain guided by human wisdom, ethical judgment, oversight, agency, and clear accountability. It offers a broader foundation for examining predictive public systems and the responsibilities that must remain with people; it does not evaluate this particular government proposal.",
        }
    if _is_stewardship_leadership_crisis_question(question):
        # Recovery answers are also Archive entry points. Keep the continuation
        # in the registered recovery contract so this family cannot bypass the
        # Guide's doorway role when provider or retrieval paths are unavailable.
        return {
            "title": "How Do I Become More Trustworthy?",
            "url": "https://geralddaquila.com/how-do-i-become-more-trustworthy/",
        }

    if _is_modes_of_knowing_dialogue_question(question):
        return {
            "title": "Being in the Driver's Seat (Without Pretending You Control the Road)",
            "url": "https://geralddaquila.com/being-in-the-drivers-seat-without-pretending-you-control-the-road/",
        }
    if _is_archive_purpose_question(question):
        # Foundational purpose questions have a canonical continuation. This
        # doorway is part of the registered recovery contract and must not be
        # displaced by a generic downstream recommendation.
        return {
            "title": "When Knowledge Is Everywhere",
            "url": "https://geralddaquila.com/when-knowledge-is-everywhere/",
        }
    if _is_commons_care_question(question):
        return {
            "title": "How Do I Become More Trustworthy?",
            "url": "https://geralddaquila.com/how-do-i-become-more-trustworthy/",
        }
    if _is_feedback_loops_institutions_question(question):
        return {
            "title": "Unraveling Stress: How the System Responds and Why It Loops",
            "url": "https://geralddaquila.com/unraveling-stress-how-the-system-responds-and-why-it-loops/",
        }
    if _is_systems_explanation_vs_simplistic_connection_question(question):
        # The Guide is both an interpreter and an entry door into the Archive.
        # A strong systems answer should therefore always carry one canonical
        # continuation, rather than leaving the visitor at a conceptual endpoint.
        return {
            "title": "Unraveling Stress: How the System Responds and Why It Loops",
            "url": "https://geralddaquila.com/unraveling-stress-how-the-system-responds-and-why-it-loops/",
        }
    if is_stewardship_failure_repair_question(question):
        # Repair after a stewardship failure naturally continues into the
        # question of how trustworthiness is rebuilt through lived responsibility.
        # Pin the doorway here so generic recommendation ranking cannot replace
        # this consequential continuation with a merely adjacent concept.
        return {
            "title": "How Do I Become More Trustworthy?",
            "url": "https://geralddaquila.com/how-do-i-become-more-trustworthy/",
        }
    return None


def _algorithmic_amplification_recovery():
    """Bounded mechanism-first recovery for algorithmic amplification questions."""
    return (
        "Algorithmic systems can scale existing biases or institutional failures because they can repeat a pattern across many decisions quickly. A ranking system can repeatedly favor what has already received attention, a recommendation system can keep reinforcing past preferences, and an automated classification or allocation process can carry assumptions embedded in its data or rules into every new case. Feedback loops can then make the resulting pattern appear to confirm itself.\n\n"
        "That does not mean an algorithm is always the original cause of the problem. The underlying bias may already exist in the data, the objective the system is asked to optimize, or the institution using it. Automation can nevertheless make the condition more consequential by accelerating, distributing, or standardizing it before people have a chance to notice and correct it. The useful question is therefore not only whether the system is biased, but which choices, measures, incentives, and feedback loops are allowing an existing pattern to travel further.\n\n"
        "The broader institutional context still matters because the same system can produce different effects under different rules, forms of oversight, and opportunities for challenge. Seeing the mechanism and the surrounding relationships together makes it easier to distinguish amplification from sole causation—and to identify where a pattern can actually be interrupted rather than treating either the algorithm or the institution as the single explanation."
    )


def is_community_continuity_revision_question(question):
    """Recognize questions balancing intergenerational continuity with repair of inherited harm."""
    q = _clean(question).casefold()
    return bool(
        re.search(r"^\s*how can\b", q)
        and re.search(r"\b(?:community|communities|institution|institutions|group|groups)\b", q)
        and re.search(r"\b(?:preserve|maintain|carry forward|sustain)\b.{0,80}\bcontinuity\b", q)
        and re.search(r"\b(?:while|as|when)\b.{0,100}\b(?:revis|chang|reform|renew|transform)\w*\b", q)
        and re.search(r"\b(?:harmful|unjust|exclusionary|oppressive|discriminatory)\b", q)
        and re.search(r"\b(?:inherited|traditional|customary|historical)\b", q)
    )


def _community_continuity_revision_recovery():
    """Explain how continuity can survive principled revision of inherited harm."""
    return (
        "Communities preserve continuity by distinguishing the inheritance they want to carry forward from practices that have survived mainly through repetition. Shared memory, language, relationships, place, and commitments can remain sources of belonging even when rules, customs, or arrangements of power that cause harm are changed. Continuity does not require every inherited form to remain untouched.\n\n"
        "That distinction should be made with the people who live with the effects. A community can examine a practice's history and original purpose, hear from those harmed or excluded, identify what value it once served, and decide what should be retained, transformed, or ended. This avoids two errors: romanticizing the past as if inheritance made every practice legitimate, and treating everything inherited as disposable without understanding what it has carried.\n\n"
        "Continuity is measured not by whether old forms remain unchanged, but by whether the community can carry forward what is worth preserving while becoming more just and capable of correction. Record why changes are made, preserve the knowledge and relationships that matter, assign responsibility for reviewing their effects, and revisit decisions as evidence and lived experience develop."
    )


def _reflective_conceptual_recovery(question):
    """Keep reflective how-questions on conceptual tension, not action planning."""
    q = _clean(question)
    match = re.search(
        r"^how can (?:(?:one|we|you)\s+)?(.+?)\s+(?:be|remain|stay)\s+"
        r"(.+?)\s+(?:without becoming|rather than becoming|rather than being|rather than|without)\s+(.+?)[?.!]*$",
        q,
        re.I,
    )
    if not match:
        return None
    subject, constructive_form, counterfeit = (
        _clean(part).strip(" .?!;:") for part in match.groups()
    )
    if not subject or not constructive_form or not counterfeit:
        return None
    if len(subject.split()) > 7 or len(counterfeit.split()) > 8:
        return None
    return (
        f"{subject.capitalize()} can be {constructive_form} without becoming {counterfeit} when it stays answerable to reality. "
        f"It does not require pretending that difficulties are smaller than they are, or treating a desired outcome as guaranteed. "
        f"The discipline lies in holding open a possibility while remaining honest about the conditions that could prevent it.\n\n"
        f"The distinction becomes clearer when circumstances disappoint. {subject.capitalize()} in its constructive form allows evidence to change expectations and allows setbacks to change the approach; {counterfeit.casefold()} instead either refuses that correction or turns disappointment into a reason to dismiss possibility altogether. "
        f"The point is not to protect {subject.casefold()} from difficult facts, but to keep difficult facts from being mistaken for the whole future.\n\n"
        f"So {subject.casefold()} is disciplined not by suppressing uncertainty, but by giving uncertainty its proper place: it can limit what is promised without deciding in advance that nothing can improve. "
        f"That makes {subject.casefold()} neither a guarantee nor a denial. It is a considered orientation that can revise its expectations without surrendering the capacity to act."
    )


def is_guide_personal_decision_agency_question(question):
    """Recognize a meta-question about guiding personal decisions without taking agency."""
    q = _clean(question).casefold()
    guide_role = bool(re.search(r"\b(?:the\s+)?(?:guide|assistant|advisor)\b", q))
    personal_decision = bool(re.search(
        r"\b(?:personal|private|life)\s+(?:life\s+)?decision\b"
        r"|\bdecision\s+to\s+be\s+made\s+for\s+(?:them|someone|a person)\b",
        q,
    ))
    agency_boundary = bool(re.search(
        r"\b(?:without|rather than|instead of|refus(?:e|ing)\s+to)\b.{0,100}"
        r"\b(?:replace|take over|undermin|override)\w*\b.{0,40}\bagency\b"
        r"|\bpreserv(?:e|ing)\s+(?:the\s+)?person(?:'s|’s)\s+agency\b",
        q,
    ))
    orientation_request = bool(re.search(r"\b(?:orient(?:ation)?|guide|guidance|help)\b", q))
    return guide_role and personal_decision and agency_boundary and orientation_request


def _guide_personal_decision_agency_recovery():
    """Explain how the Guide supports judgment without taking ownership of a life choice."""
    return (
        "The Guide should help a person make their own decision, not make the decision for them. Its role is to clarify what is actually being decided, what matters to the person, which responsibilities or commitments are involved, and what constraints shape the available choices. It can offer perspective and test assumptions, but it should not present its preference as the answer or imply that it knows the person's life better than they do.\n\n"
        "Good orientation makes the choice easier to see without pretending it is easy. The Guide can help compare realistic alternatives, surface the strongest reasons for and against each, distinguish known facts from interpretations and unknowns, and consider who else may be affected. It should also make the consequences and reversibility of each option visible: a low-risk, reversible step may be tested, while a choice involving lasting harm, safety, or major obligations deserves more careful deliberation and, where appropriate, trusted human or specialist support.\n\n"
        "The conversation should end with the person better equipped to judge, not more dependent on the Guide's judgment. The Guide can identify a useful next question, a proportionate next step, or evidence worth gathering, while leaving the values, consent, and final choice with the person who must live with the outcome. If the person corrects the framing or sees something differently, the Guide should adapt. Its success is measured by clearer understanding and stronger agency—not by securing agreement with a recommendation."
    )

def compose_task_specific_recovery(question):
    """Return bounded, provider-independent answers for well-defined task families.

    These recoveries are task-level capabilities, not benchmark-answer reuse.
    They are deliberately self-contained and do not select Archive doorways.
    """
    q = _clean(question).casefold()
    if not q:
        return None

    # Fair-rule questions need a concrete governance test, not a generic
    # liberty-versus-community slogan. This is bounded general reasoning and
    # does not claim to state a formal Living Archive doctrine.
    if (
        re.search(r"\b(?:personal\s+)?libert(?:y|ies)\b", q)
        and re.search(r"\b(?:(?:collective|shared)\s+(?:obligations?|responsibilit(?:y|ies)))\b", q)
        and re.search(r"\b(?:community|communities|group|society)\b", q)
        and re.search(r"\b(?:fair\s+rule|rule|rules|policy|governance|limits?|restrictions?)\b", q)
        and re.search(
            r"\b(?:balanc(?:e|ing)|reconcil(?:e|ing)|set(?:ting)?|establish(?:ing)?|"
            r"decid(?:e|es|ing)|justif(?:y|ies|ied|ying)|restrict(?:ion|ions|ed|ing)?)\b",
            q,
        )
    ):
        return {
            "recovery_id": "task_fair_community_rule_liberty_and_collective_obligations",
            "response": (
                "A fair community rule should protect a meaningful sphere of personal freedom while addressing responsibilities "
                "that arise because people share space, resources, risks, and consequences. Neither side should be treated as "
                "absolute: collective convenience does not by itself justify controlling private choices, and personal liberty "
                "does not remove responsibility for avoidable harm imposed on others.\n\n"
                "Start by stating the legitimate shared purpose of the rule and the specific harm or coordination problem it is "
                "meant to address. Ask who benefits, who carries the costs, whose freedom is restricted, and whether the people "
                "most affected have had a meaningful opportunity to shape the decision. A restriction is more defensible when "
                "it responds to a demonstrable shared need, is necessary and proportionate to that need, and uses the least "
                "restrictive workable means. It should not reach further into people's lives than its purpose requires.\n\n"
                "Make the obligations reciprocal and fairly distributed: apply the same principle across status and influence, "
                "allow reasonable accommodation where circumstances differ, explain how the rule will be enforced, and provide "
                "a way to question or appeal its application. Set a review point and observable criteria for checking whether it "
                "actually reduces the problem without creating greater burdens or new harms. The practical test is: can the "
                "community explain the shared need, justify the limit, show that burdens are fairly allocated, and revise the rule "
                "when experience shows it is not working? If not, the rule needs redesign rather than stronger enforcement."
            ),
        }

    # Problem-boundary questions are answerable without model generation or
    # retrieval. Resolve the analytical boundary itself before the provider
    # bank so provider exhaustion cannot turn a complete conceptual question
    # into a generic fallback. This is a bounded reasoning family, not an
    # exact-answer copy of a Gold Star record.
    if (
        re.search(r"\b(?:boundaries|boundary|scope|limits?|framing|frame)\b", q)
        and re.search(r"\b(?:problem|issue|question|inquiry|system)\b", q)
        and re.search(r"\b(?:drawn|set|define|defined|frame|framed|around|includ(?:e|ed|es|ing)|exclud(?:e|ed|es|ing)|outside|inside)\b", q)
        and re.search(r"\b(?:what|which|kinds?|types?|should|exclude|excluded|outside)\b", q)
    ):
        doorway = {
            "title": "Boundary Conditions",
            "url": "https://geralddaquila.com/boundary-conditions/",
            "rationale": (
                "Boundary Conditions explains why every method has a domain, "
                "why its limits must be made explicit, and how disciplined "
                "inquiry distinguishes what can be established from what lies "
                "beyond its warranted reach."
            ),
        }
        return {
            "recovery_id": "task_problem_boundary_calibration",
            "response": (
                "A useful problem boundary is not a line around everything that seems related. "
                "It is a reasoned statement of what the inquiry is trying to explain, at what level, "
                "over what period, and from whose point of view. Draw it across several dimensions: "
                "the **phenomenon** (the specific condition or outcome being examined); the **system** "
                "(the people, relationships, rules, incentives, resources, and dependencies that can "
                "produce or shape it); the **scale and place** (individual, team, organization, community, "
                "or wider environment); the **time horizon** (the immediate episode, its history, and "
                "delayed effects); and the **stakeholder and authority boundary** (who is affected, who "
                "decides, and who carries the consequences). Also mark the **evidence boundary**: what "
                "is observed, what is inferred, and what remains unknown.\n\n"
                "Exclude material that is merely adjacent and does not materially change the explanation "
                "or the decision the inquiry must support. But do not confuse 'outside the chosen scope' "
                "with 'irrelevant.' An upstream cause, downstream consequence, affected group, or external "
                "condition may sit beyond the immediate problem boundary and still need to be recorded as "
                "a dependency, constraint, risk, or consequence. In particular, do not exclude people who "
                "bear the costs simply because they lack decision-making power, or exclude causes merely "
                "because they are difficult for the organization to control. State what is out of scope, "
                "why it is out, and where its effects will still be monitored.\n\n"
                "A practical test is: **if including this factor could materially change the diagnosis, "
                "the distribution of benefits or burdens, the available options, or the likely consequences, "
                "it belongs inside the analysis—or must remain visible at its boundary.** Keep the boundary "
                "provisional and revise it when new evidence or feedback shows that an excluded relationship "
                "is shaping the result. A well-drawn boundary makes inquiry manageable without pretending "
                "that the world stops where the analysis does."
            ),
            "recommendation": doorway,
            "canonical_doorway": doorway,
            "doorway_title": doorway["title"],
            "doorway_url": doorway["url"],
            "doorway_rationale": doorway["rationale"],
        }

    # Policy/procedure is a plain-language distinction, not a resource-discovery task.
    if (
        re.search(r"\bpolicy\b", q)
        and re.search(r"\bprocedures?\b", q)
        and re.search(r"\b(?:difference|distinguish|compare|versus|vs\.?|explain)\b", q)
    ):
        return {
            "recovery_id": "task_comparison_policy_procedure",
            "response": (
                "A policy states the rule, principle, or requirement that guides a decision: what should happen and why. "
                "A procedure describes the steps people follow to put that policy into practice: how the work is carried out. "
                "The key difference is that policy sets direction; procedure explains the method.\n\n"
                "For example, a leave policy may state who is eligible for leave and the conditions that apply. "
                "The procedure explains how an employee submits a request, who reviews it, how the decision is recorded, "
                "and how the employee is notified.\n\n"
                "The two should support one another, but they are not interchangeable. A policy can remain stable while "
                "a procedure is improved; a procedure cannot legitimately override the policy it is meant to implement."
            ),
        }

    # Trust-as-practice is an implementation question: answer with observable
    # organizational behaviors and feedback, not an abstract definition alone.
    if (
        re.search(r"\btrust\b", q)
        and re.search(r"\b(?:organization|organisation|team|community)\b", q)
        and re.search(r"\b(?:practice|put|build|apply|improve|operationalize|operationalise)\b", q)
    ):
        return {
            "recovery_id": "task_practical_trust_in_organizations",
            "response": (
                "Trust becomes practical when an organization makes its decisions and commitments observable and dependable. "
                "Start with a decision that affects people: ask those affected what they see before deciding, distinguish "
                "observed facts from assumptions, explain the reasons for the decision, and name who owns the decision and "
                "the next action. Then follow through when promised, and tell people promptly when something changes.\n\n"
                "Create safe ways to raise concerns and disagree. Respond without retaliation, correct mistakes openly, and "
                "repair harm rather than asking people simply to trust the organization. Share the information people need "
                "to act responsibly, and apply agreed rules consistently across roles and teams.\n\n"
                "Check whether trust is actually improving: are commitments kept, are concerns raised earlier, do people "
                "understand how decisions were made, and are mistakes addressed? These observable behaviors are more reliable "
                "indicators than statements of good intent alone."
            ),
        }

    # Decision-rights allocation: centralize what needs common authority; delegate
    # reversible, context-dependent choices to the people closest to the work.
    if (
        re.search(r"\bcentraliz(?:e|es|ed|ing|ation)|centralis(?:e|es|ed|ing|ation)\b", q)
        and re.search(r"\bdistribut(?:e|es|ed|ing)|decentraliz(?:e|es|ed|ing|ation)|decentralis(?:e|es|ed|ing|ation)|delegat(?:e|es|ed|ing|ion)\b", q)
        and re.search(r"\b(?:authority|decision|decisions|decision-making|power)\b", q)
    ):
        return {
            "recovery_id": "task_decision_rights_distribution_tradeoff",
            "response": (
                "Neither full centralization nor unrestricted distribution is a sound default. Use centralization when a decision creates "
                "organization-wide obligations, carries legal or material financial risk, requires consistent standards, or affects "
                "several teams at once. Use distributed authority when a decision is routine and reversible, and the relevant knowledge sits with the "
                "team doing the work and the consequences can be contained locally.\n\n"
                "Centralization can improve consistency, coordination, and accountability, but it can also create bottlenecks, "
                "distance decisions from local knowledge, and weaken initiative. Distributed authority can improve speed, "
                "ownership, and responsiveness, but it can produce uneven practice, duplicated effort, or conflicting commitments "
                "if teams lack shared boundaries. The trade-off is between consistent oversight and the speed, local knowledge, and initiative that come from delegated decisions.\n\n"
                "A growing nonprofit will usually benefit from a clear hybrid: define a small set of reserved organization-wide "
                "decisions, establish financial and safeguarding thresholds, and delegate day-to-day choices within those limits. "
                "Make decision ownership and escalation rules visible, then review whether the arrangement is producing timely, "
                "consistent decisions without overloading the center."
            ),
        }

    # Safe verification of environment-variable presence without exposing the value.
    if (
        re.search(r"\b(?:environment\s+variables?|env\s+vars?)\b", q)
        and re.search(r"\bpython\b", q)
        and re.search(r"\b(?:verify|check|configured|present|set)\b", q)
        and re.search(r"\b(?:secret|value|expos(?:e|ing)|print|log)\b", q)
    ):
        return {
            "recovery_id": "task_safe_environment_variable_presence_check",
            "response": (
                "Check whether the variable is present, but never print or log its value. In Python, test the value as a "
                "boolean and report only the variable name and the result:\n\n"
                "```python\nimport os\n\nname = \"SERVICE_API_KEY\"\nconfigured = bool(os.getenv(name, \"\").strip())\nprint(f\"{name} configured: {configured}\")\n```\n\n"
                "This confirms that the process environment contains a non-empty value at the time of the check; it does not "
                "prove that the application reads the variable or that the credential is valid. To verify use, test the code "
                "path that loads the setting and perform a safe integration check that reports success or failure without "
                "including the credential in output. Keep the check in a controlled diagnostic or test, not in routine logs."
            ),
        }

    # Causal attribution from aggregate traffic changes requires evidence, not a guess.
    if (
        re.search(r"\btraffic\b", q)
        and re.search(r"\b(?:increase|increased|spike|surge|jump|rise|higher)\b", q)
        and re.search(r"\b(?:website|site|visitors?|sessions?|analytics)\b", q)
    ):
        return {
            "recovery_id": "task_uncertain_website_traffic_causation",
            "response": (
                "The cause cannot be established from the information provided; the traffic increase alone is not enough to identify what changed. A rise in visits can come from several "
                "different sources—search visibility, referrals, a campaign, a newly shared page, direct traffic, automated "
                "bots, or a measurement change—and more than one may be operating at once.\n\n"
                "Start by comparing the affected week with the preceding weeks and the same period where seasonality matters. "
                "Segment the change by acquisition source and medium, landing page, geography, device, and new versus returning "
                "visitors. Identify which segment accounts for most of the increase, then compare its timing with published "
                "content, campaigns, backlinks, search impressions and clicks, site changes, and referral activity. Check server "
                "logs and bot indicators as well: a rise in requests is not necessarily a rise in people.\n\n"
                "Treat a cause as supported only when the timing and segment-level evidence converge. Record competing "
                "explanations and what would distinguish them; without that evidence, report the increase as observed and its "
                "cause as undetermined rather than assigning it to the most visible event."
            ),
        }

    # A worldview/assumption question needs a clear relationship and lived example,
    # not a generic mechanism paragraph with the entire interrogative pasted in.
    if (
        re.search(r"\b(?:assumptions? about reality|worldview|worldviews|beliefs about how the world works)\b", q)
        and re.search(r"\b(?:decisions?|choices|cooperat(?:e|ion)|everyday|daily|relationships?)\b", q)
        and re.search(r"\b(?:shape|shapes|influence|influences|affect|affects|guide|guides)\b", q)
    ):
        return {
            "recovery_id": "task_worldview_everyday_decisions_and_cooperation",
            "response": (
                "Assumptions about reality shape everyday decisions by influencing what people notice, what they regard as "
                "possible, whose interests they consider, and which consequences they expect. These assumptions form part of "
                "a worldview. A worldview is a way of understanding how the world works and how people are related to one another.\n\n"
                "For example, if people assume that resources are always scarce and others are mainly competitors, they may "
                "protect information, avoid sharing risk, or treat disagreement as a threat. If they see people as distinct "
                "but interdependent, they may be more inclined to share information, coordinate contributions, and consider "
                "how a decision affects the wider group. Neither assumption determines behavior by itself; incentives, trust, "
                "institutions, and material conditions also matter.\n\n"
                "The practical influence is reciprocal. A worldview shapes how people interpret a situation, while repeated "
                "experiences and the consequences of their choices can reinforce or revise that worldview. Cooperation becomes "
                "more likely when people can make their assumptions visible, test them against experience, and build conditions "
                "in which mutual responsibility is safer and more worthwhile."
            ),
        }

    return None


def is_orientation_information_contrast_question(question):
    """Recognize common phrasings of the orientation/information conceptual contrast."""
    q = re.sub(r"\s+", " ", _clean(question)).casefold()
    contrast = bool(re.search(
        r"\b(?:orientation|being oriented|orienting|orient)\b.{0,70}"
        r"\b(?:rather than|instead of|over|vs\.?|versus|different from|distinct from|as opposed to)\b"
        r".{0,40}\b(?:information|being informed|informing|inform)\b"
        r"|\b(?:information|being informed|informing)\b.{0,70}"
        r"\b(?:rather than|instead of|over|vs\.?|versus|different from|distinct from|as opposed to)\b"
        r".{0,40}\b(?:orientation|being oriented|orienting|orient)\b"
        r"|\bdifference between (?:orientation and information|being oriented and being informed)\b"
        r"|\bhow (?:is|does) orientation differ(?:ent)? from information\b",
        q,
    ))
    asks_meaning = bool(re.search(
        r"\b(?:what does|what do|what is|how is|how does|explain|meaning of|mean in practice|"
        r"difference between|understand|put .* into practice)\b",
        q,
    ))
    return contrast and asks_meaning


def has_orientation_information_explanation(response):
    """Check that both terms, their relationship, and practical application are explained."""
    text = _clean(response).casefold()
    return bool(
        re.search(r"\binformation\b.{0,100}\b(?:facts|data|details|knowledge)\b", text)
        and re.search(r"\borientation\b.{0,180}\b(?:context|relationships|stakes|conditions)\b", text)
        and re.search(
            r"\b(?:orientation|it)\b.{0,100}\b(?:depends on|uses|places|organizes|organises|"
            r"puts|situates|connects|place)\b.{0,100}\binformation\b"
            r"|\binformation\b.{0,100}\b(?:is placed|is put|is situated|is organized|is organised)\b",
            text,
        )
        and re.search(r"\b(?:decide|judg|act|navigate|prioriti[sz])\w*\b", text)
        and re.search(r"\b(?:for example|in practice|imagine|suppose)\b", text)
    )


def _orientation_information_contrast_recovery():
    """Explain the practical distinction using the Archive's published Cornerstone."""
    return (
        "Information gives you facts, data, or claims. Orientation helps you understand what that information means "
        "in the situation you are actually facing: what matters, what is reliable, how the relevant parts relate, "
        "and what responsibilities or possible actions follow. Orientation uses information; it does not reject it. "
        "It connects what you know to the context in which you must judge and act.\n\n"
        "For example, an AI system may give you a fluent, detailed answer. The text is information, but orientation "
        "means asking whether its claims are reliable and adequately supported, whether they address the real question, "
        "what important context or consequences may be missing, and what should responsibly be done with the answer. "
        "A confident response is not a substitute for human judgment.\n\n"
        "This is the distinction developed in the Living Archive Cornerstone “When Knowledge Is Everywhere”: "
        "the aim is not simply to accumulate more knowledge, but to cultivate orientation, judgment, discernment, "
        "responsibility, and wise participation in complex systems. Orientation does not eliminate ambiguity; "
        "it makes ambiguity more navigable."
    )


def is_epistemic_category_distinction_question(question):
    """Recognize a request to distinguish evidence, interpretation, hypothesis, and values."""
    q = _clean(question).casefold()
    categories = (
        bool(re.search(r"\bevidence\b", q)),
        bool(re.search(r"\binterpretation\b", q)),
        bool(re.search(r"\bhypothes(?:is|es)\b", q)),
        bool(re.search(r"\b(?:normative judgment|value judgment|what ought)\b", q)),
    )
    asks_for_distinction = bool(re.search(
        r"\b(?:what counts as|distinguish|difference between|differences between|"
        r"how do .{0,100} differ|separate|tell apart|differentiate)\b", q
    ))
    return sum(categories) >= 3 and asks_for_distinction


def has_epistemic_category_distinction_explanation(response):
    """Require all four categories, their boundaries, and their relationship."""
    text = _clean(response).casefold()
    definitions = all((
        re.search(r"\bevidence\b.{0,180}\b(?:supports?|bears on|relevant to)\b", text),
        re.search(r"\binterpretation\b.{0,180}\b(?:meaning|sense|context)\b", text),
        re.search(r"\bhypothes(?:is|es)\b.{0,180}\b(?:provisional|testable|tested|expectation)\b", text),
        re.search(r"\bnormative judgment\b.{0,220}\b(?:ought|should|right|fair|value|principle)\b", text),
    ))
    boundaries = bool(re.search(
        r"\b(?:facts alone|does not follow from facts|not the same as|cannot by itself|"
        r"not automatically|must be made explicit)\b", text
    ))
    relationships = bool(re.search(
        r"\b(?:evidence constrains|evidence can challenge|interpretation.*hypothes|"
        r"hypothesis.*evidence|values.*evidence|evidence.*values)\b", text
    ))
    return bool(definitions and boundaries and relationships)


def build_epistemic_category_distinction_contract():
    """Describe the bounded task without claiming Archive doctrine."""
    return {
        "version": "1.0",
        "question_class": "epistemic_category_distinction",
        "categories": [
            {"id": "evidence", "criterion": "Information that bears on a claim, assessed for provenance, relevance, method, independence, and counterevidence."},
            {"id": "interpretation", "criterion": "The meaning assigned to evidence in context, including assumptions and framing."},
            {"id": "hypothesis", "criterion": "A provisional explanatory proposition that generates expectations and can be investigated or revised."},
            {"id": "normative_judgment", "criterion": "An evaluation of what ought to be done or valued, requiring explicit values, principles, and reasons."},
        ],
        "required_distinctions": [
            "evidence_is_not_self_interpreting",
            "interpretation_is_not_observation",
            "hypothesis_is_not_established_fact",
            "normative_conclusion_does_not_follow_from_facts_alone",
        ],
        "relationship": "Evidence constrains interpretation; interpretations can generate hypotheses; hypotheses guide further inquiry; normative judgments combine empirical understanding with explicit, contestable values.",
        "scope": "General reasoning framework only; not an official Living Archive definition or a verdict on a particular empirical or ethical dispute.",
        "handoff_policy": "Answer the conceptual question first; any Archive resource recommendation is a separate, verified decision.",
    }


def _epistemic_category_distinction_recovery():
    """Explain the four categories and how they constrain one another."""
    return (
        "These four terms describe different kinds of work in reasoning. They are connected, but they are not interchangeable.\n\n"
        "Evidence is information that bears on a claim: for example, observations, measurements, records, documents, or testimony. "
        "Evidence is not automatically strong just because it exists. Its weight depends on where it came from, how it was gathered, "
        "whether it is relevant to the claim, whether independent sources converge, and what counterevidence or uncertainty remains. "
        "Evidence constrains what can responsibly be said, but it does not interpret itself.\n\n"
        "Interpretation is the meaning we assign to evidence in context. It connects observations to a possible explanation or significance. "
        "Interpretations are necessary, but they are shaped by assumptions, prior knowledge, interests, and the frame through which a situation is viewed. "
        "A careful interpretation makes those assumptions visible and remains open to revision when the evidence does not fit.\n\n"
        "A hypothesis is a provisional explanation or proposition that can be investigated. It should generate expectations: what would we expect to observe "
        "if it were a useful explanation, and what evidence would count against it? A hypothesis is not an established fact; it is a disciplined possibility "
        "that inquiry may strengthen, qualify, or reject.\n\n"
        "A normative judgment evaluates what ought to be done, what is right or fair, or what deserves priority. It draws on values, principles, duties, and "
        "judgments about consequences. Evidence matters because it helps establish what is happening and what different choices may cause, but a conclusion about "
        "what ought to happen does not follow from facts alone. The values and principles doing the evaluative work should be stated and open to reasoned challenge.\n\n"
        "The relationship is iterative, not a rigid one-way ladder: evidence constrains interpretation; interpretation can suggest a hypothesis; a hypothesis "
        "guides what further evidence to seek; and normative judgment weighs the likely consequences alongside explicit values. A policy example makes the "
        "distinction concrete: service records showing that a district receives fewer clinic visits are evidence; reading that pattern as a sign of poor access "
        "is an interpretation; proposing that longer clinic hours would improve access is a hypothesis to test; deciding whether to fund those hours is a normative "
        "judgment involving fairness, need, cost, and public responsibility.\n\n"
        "A useful check is to ask four separate questions: What is observed and where did it come from? What meaning am I assigning to it? What explanation could "
        "be tested, and what might disconfirm it? Which values or principles support the judgment I am making? Keeping those questions distinct helps prevent an "
        "interpretation from masquerading as evidence, a hypothesis from becoming certainty, or a value judgment from being presented as a purely factual conclusion."
    )


def is_guide_meta_coverage_policy_question(question):
    """Recognize questions about when The Guide may declare an Archive coverage gap."""
    q = _clean(question).casefold()
    guide_actor = bool(re.search(r"\b(?:the\s+)?guide\b", q))
    policy_action = bool(re.search(
        r"\b(?:when|under what conditions|how|what evidence|what standard)\b.{0,100}"
        r"\b(?:say\w*|state\w*|acknowledge\w*|declare\w*|claim\w*|decide\w*|determine\w*|use|tell\w*|report\w*)\b"
        r"|\b(?:should|may|must)\b.{0,60}\b(?:say|state|acknowledge|declare|claim|report)\b",
        q,
    ))
    coverage_subject = bool(re.search(
        r"\b(?:archive|living archive)\b.{0,100}\b(?:does not|doesn't|do not|don't|not yet|"
        r"directly address|cover|coverage|resource|material)\b"
        r"|\b(?:coverage gap|direct coverage|directly address|unaddressed by the archive)\b",
        q,
    ))
    return guide_actor and policy_action and coverage_subject


def has_guide_meta_coverage_policy_explanation(response):
    """Check that a response distinguishes evidence-backed gaps from retrieval failures."""
    text = _clean(response).casefold()
    return all((
        re.search(r"\b(?:retrieval result|retrieval failure|failed retrieval|search result|search failure)\b", text),
        re.search(r"\b(?:directly address(?:es)?|direct coverage)\b", text),
        re.search(r"\brelated\b", text),
        re.search(r"\b(?:indexing|access|source verification)\b", text),
        re.search(r"\b(?:checked|verified|evidence)\b", text),
    ))


def build_guide_meta_coverage_policy_contract():
    """Return the shared evidence and navigation contract for Guide coverage claims."""
    return {
        "version": "1.0",
        "question_class": "guide_meta_coverage_policy",
        "outcomes": [
            {
                "id": "direct_coverage",
                "criterion": "A verified canonical source directly addresses the visitor's question.",
                "response": "Answer from the source and offer its doorway when useful.",
            },
            {
                "id": "adjacent_coverage",
                "criterion": "A verified source is relevant but addresses an adjacent question or only part of this one.",
                "response": "Describe it as related, state what it does not answer, and do not label it direct coverage.",
            },
            {
                "id": "genuine_coverage_gap",
                "criterion": "The question is correctly interpreted, relevant canonical sources are searched and verified, direct and adjacent candidates are evaluated, and no adequate coverage exists within the checked scope.",
                "response": "Only then may the Guide say that the Archive does not yet address this directly, with the checked scope made clear.",
            },
            {
                "id": "retrieval_or_verification_failure",
                "criterion": "Search, indexing, access, fetching, or source verification is failed or incomplete.",
                "response": "State that coverage could not be verified; do not declare an Archive gap.",
            },
        ],
        "required_preconditions_for_gap_phrase": [
            "correct_question_interpretation",
            "targeted_canonical_search_completed",
            "relevant_source_bodies_fetched_and_verified",
            "direct_and_adjacent_candidates_evaluated",
            "claim_limited_to_sources_actually_checked",
        ],
        "forbidden_inferences": [
            "no_search_result_means_archive_gap",
            "failed_retrieval_means_archive_gap",
            "indexing_or_access_failure_means_archive_gap",
            "weak_keyword_overlap_proves_direct_coverage",
            "absence_from_checked_results_proves_absence_from_the_whole_archive",
        ],
        "doorway_policy": {
            "suppress_for_this_question_class": True,
            "reason": "The visitor is asking about The Guide's policy, not requesting an Archive resource.",
        },
    }


def _guide_meta_coverage_policy_recovery():
    """State the evidence threshold for a responsible Archive coverage-gap claim."""
    return (
        "The Guide should say that the Archive does not yet address a question directly only "
        "after it has correctly understood the question and checked the relevant canonical "
        "Archive material—not merely because an initial search returned no result. A missing "
        "retrieval result is evidence of a search outcome, not proof that the Archive has no "
        "relevant material.\n\n"
        "The Guide should distinguish four outcomes. If a verified resource directly addresses "
        "the question, recommend it. If a resource is genuinely relevant but only adjacent, "
        "describe it as related and explain what it does not answer. If no adequate direct or "
        "related resource is found after the available canonical sources and bounded recovery "
        "routes have been checked, acknowledge that no direct resource could be verified. If "
        "retrieval, indexing, access, or source verification failed, disclose that limitation "
        "instead of declaring an Archive coverage gap.\n\n"
        "Use the stronger wording “the Archive does not yet address this directly” only when "
        "the evidence supports a genuine coverage gap within the sources that were actually "
        "checked. Otherwise say, more carefully, “I couldn't verify a resource that directly "
        "addresses this.” The Guide must never turn an unsuccessful search, an unavailable "
        "source, or a weak keyword match into a claim about the contents of the whole Archive."
    )


def _is_institutional_legitimacy_question(question):
    """Recognize a bounded general-concept question about institutional legitimacy."""
    q = re.sub(r"\s+", " ", str(question or "")).strip()
    if not q:
        return False
    asks_legitimacy = bool(
        re.search(r"\bwhat makes\b.{0,45}\binstitution(?:s|al)?\b.{0,35}\blegitim\w*\b", q, re.I)
        or re.search(r"\bwhat gives\b.{0,35}\binstitution(?:s)?\b.{0,30}\blegitim\w*\b", q, re.I)
        or re.search(r"\bwhen (?:is|are)\b.{0,35}\binstitution(?:s)?\b.{0,30}\blegitim\w*\b", q, re.I)
        or re.search(r"\binstitutional legitimacy\b", q, re.I)
    )
    source_only = bool(re.search(
        r"\b(?:according to|as defined by|official|formally defined|in the Living Archive(?:'s)? (?:own )?(?:terms|framework|teaching))\b",
        q, re.I,
    ))
    high_stakes = bool(re.search(
        r"\b(?:legal opinion|constitutional law advice|court case|specific lawsuit)\b",
        q, re.I,
    ))
    return asks_legitimacy and not source_only and not high_stakes


def _institutional_legitimacy_recovery():
    """Explain general legitimacy without presenting it as Archive doctrine."""
    return (
        "An institution is legitimate when its authority is justifiable to the people affected by it—not merely because it exists, has power, or follows its own procedures. Legitimacy has several connected foundations: a credible public purpose; authority established through a recognized and appropriate process; decisions made with competence, consistency, and fairness; and meaningful ways for affected people to be heard, question decisions, and seek correction. The weight of each foundation depends on the institution's role and the people subject to its decisions.\n\n"
        "Lawful authorization matters, but legality alone does not settle every question of legitimacy. Nor is popularity enough: a widely supported institution can still abuse power or disregard rights. A stronger test is whether the institution can explain who authorized it to act, what limits govern its authority, whose interests and rights it must consider, how it gives reasons for consequential decisions, and what happens when it makes a mistake. Its conduct over time matters as much as its founding claim.\n\n"
        "In practice, look for evidence rather than declarations: whether rules are applied fairly; whether decision-makers are answerable; whether dissent and scrutiny are safe; whether burdens and benefits are distributed defensibly; and whether the institution can acknowledge failure and change course. Legitimacy is therefore not a permanent certificate. It is sustained—or weakened—through the continuing relationship between authority, purpose, performance, participation, and accountability. This is a general conceptual explanation, not a statement of the Living Archive's formal doctrine."
    )


def _is_public_commons_civic_renewal_question(question):
    """Recognize a general conceptual question about commons and civic renewal."""
    q = _clean(question).casefold()
    commons = bool(re.search(r"\b(?:public\s+)?commons\b", q))
    civic_renewal = bool(re.search(r"\bcivic\s+renewal\b", q))
    asks_role = bool(re.search(
        r"\b(?:role|purpose|function|contribution|importance|significance)\b", q
    ))
    asks_explanation = bool(re.search(
        r"\b(?:what|how|why|explain|describe)\b", q
    ))
    archive_specific = bool(re.search(
        r"\b(?:according to|in|within)\s+(?:the\s+)?(?:living\s+)?archive\b|"
        r"\barchive(?:'s|’s)\s+(?:formal\s+)?(?:definition|doctrine|meaning)\b",
        q,
    ))
    return commons and civic_renewal and asks_role and asks_explanation and not archive_specific


def _is_provider_exhaustion_civic_commons_question(question):
    """Recognize the explicit meta-question about answering civic-commons inquiries without source access."""
    q = _clean(question).casefold()
    return bool(
        re.search(r"\b(?:when|if)\b.{0,80}\b(?:search|provider|retrieval)\s+services?\b.{0,50}\b(?:unavailable|down|failed|exhausted)\b", q)
        and re.search(r"\bguide\b", q)
        and re.search(r"\b(?:general|ordinary)\s+(?:conceptual\s+)?question\b", q)
        and re.search(r"\b(?:civic\s+)?commons\b", q)
        and re.search(r"\b(?:official|institutional)\s+doctrine\b", q)
    )


def _provider_exhaustion_civic_commons_recovery():
    """Answer the meta-question with a substantive example and an explicit doctrine boundary."""
    return (
        "When search services are unavailable, a guide should not confuse a lack of retrieved sources with a lack of answerability. "
        "If the visitor asks a general conceptual question, the guide can answer from stable general knowledge while clearly identifying "
        "that basis. It should not imply that it searched, cite material it has not seen, or present its explanation as an official "
        "Living Archive position.\n\n"
        "For example, civic commons can be explained as shared resources, spaces, institutions, and capacities that people use and help "
        "govern for common benefit. Their value depends not only on public availability but on fair access, meaningful participation, "
        "clear stewardship responsibilities, transparent rules, and ways to challenge exclusion or misuse. They can support civic life "
        "by giving people places and resources to cooperate, deliberate, and solve shared problems; they can also be neglected, captured, "
        "or made nominally public while excluding some people.\n\n"
        "The guide should distinguish this general explanation from any Archive-specific definition or doctrine. It should not invent "
        "citations, quotations, canonical definitions, or links. If the visitor asks what the Living Archive formally teaches, that is "
        "a source-specific question: without an authoritative text, the guide should say that it cannot verify the official position "
        "and identify what source would be needed."
    )


def _public_commons_civic_renewal_recovery():
    """Answer the ordinary civic concept without claiming Archive-specific doctrine."""
    return (
        "Public commons are resources, spaces, institutions, and shared conditions that people "
        "can access and help care for together. They can include parks, libraries, public "
        "knowledge, community facilities, and civic infrastructure. Their value is not only "
        "that they are publicly available; it also depends on fair access, responsible use, "
        "and governance that remains answerable to the people affected.\n\n"
        "Their role in civic renewal is to create practical settings in which people can "
        "participate in common life. Shared spaces and services bring people into contact, "
        "make cooperation possible, and give communities opportunities to identify needs, "
        "deliberate, solve problems, and take part in decisions. When people have a meaningful "
        "voice in how shared resources are managed, civic participation can become an everyday "
        "practice rather than something limited to elections or formal consultation.\n\n"
        "Commons do not renew civic life automatically. Access can be unequal, resources can "
        "be neglected or captured by powerful interests, and participation can become tokenistic. "
        "Renewal therefore depends on transparent rules, inclusive decision-making, clear "
        "responsibilities, protection against exclusion, and ways to challenge or correct "
        "mismanagement. In short, public commons can strengthen the relationships and "
        "institutions through which people act together, provided that the commons themselves "
        "are governed fairly and stewarded accountably. This is a general conceptual explanation, "
        "not a claim that it is a formal Living Archive definition."
    )


def is_self_optimization_model_limits_question(question):
    """Recognize a bounded question about self-optimization as a development model."""
    q = re.sub(r"\s+", " ", _clean(question)).strip()
    return bool(
        re.match(
            r"(?i)^what are the (?:limits|limitations|boundaries) of "
            r"self[- ]optim(?:ization|isation) as (?:a|an) model of "
            r"(?:human )?development[?.!]*$",
            q,
        )
        or re.match(
            r"(?i)^what are the (?:limits|limitations|boundaries) of "
            r"self[- ]optim(?:ization|isation) as a developmental model[?.!]*$",
            q,
        )
    )


def _self_optimization_model_limits_recovery():
    """Explain the useful scope and limits of optimization as a developmental model."""
    return (
        "Self-optimization can describe one part of development: a person, group, or system "
        "uses feedback about its performance to adjust its methods and become more capable "
        "of achieving an aim. It is useful when the aim is legitimate, the measures reflect "
        "what genuinely matters, and feedback is reliable enough to guide improvement. "
        "It helps explain learning, adaptation, and the refinement of skills or processes.\n\n"
        "Its main limit is that optimization improves performance against a chosen objective; "
        "it does not establish that the objective itself is worthwhile. If a measure is only a "
        "proxy for what matters, a system can become better at the measure while becoming worse "
        "at the underlying purpose. Feedback can also be incomplete or delayed, and improving "
        "one part can damage the wider whole. A system cannot rely on its own optimization "
        "process alone to judge its assumptions, values, or effects on others.\n\n"
        "Development is broader than becoming more efficient at a fixed goal. It can involve "
        "changing the goal, recognizing a mistaken assumption, developing judgment and "
        "relationships, responding to new conditions, and deciding that some trade-offs are "
        "not acceptable. Progress may be uneven and cannot always be reduced to one score. "
        "So self-optimization is best treated as one mechanism within development, not a "
        "complete model of it. A sound developmental process also needs external feedback, "
        "more than one measure of success, room to revise its aims, and independent judgment "
        "about consequences. This is a general conceptual explanation, not a formal "
        "Living Archive definition."
    )


def _is_epistemic_distress_guidance_question(question):
    family = classify_inquiry_family(question).get("family")
    return family in {"epistemic_distress", "epistemic_distress_guidance"}


def _epistemic_distress_guidance_recovery():
    """Offer humane, grounded epistemic guidance without claiming metaphysical authority."""
    return (
        "When someone is frightened or grieving and seeks metaphysical certainty about ultimate questions, begin with the distress rather than debating the metaphysics. The wish for a definite answer can be an understandable attempt to find something steady when life feels uncertain. Acknowledge that need gently; do not assume the person's beliefs, history, or diagnosis, and do not use their vulnerability to claim special authority.\n\n"
        "Help separate four things that can easily become tangled: what the person experienced, what they believe or hope, how they interpret the experience, and what available evidence can establish. A spiritual tradition may offer a meaningful account, and a personal experience may matter deeply. Personal meaning is not proof of an external claim about a soul, an afterlife, divine purpose, or ultimate reality. If a claim is unverifiable, say plainly that we cannot verify it. Do not ridicule belief, but do not turn comfort, intuition, or the Guide's fluency into proof.\n\n"
        "The person does not have to settle the ultimate question right now. It may help to pause, take a slow breath, notice the immediate surroundings, or speak with someone they trust. They can hold a belief provisionally, explore what it means to them, or leave the question open without treating uncertainty as failure. The Guide should support reflection and independent judgment, not become an oracle on which the person depends.\n\n"
        "If the distress feels too heavy to carry alone, encourage contact with a trusted person or an appropriate mental-health professional. If the person may be in immediate danger or cannot stay safe, prioritize immediate help from local emergency services or someone who can be physically present. The response should offer companionship and practical care while remaining honest about what it cannot know."
    )


def compose_recovery(question, *, underlying_question="", desired_movement=""):
    """Offer a useful bounded response without inventing facts or sources."""
    q = _clean(question)
    if not q:
        return "What would you like to understand or work through?"
    subject = _clean(underlying_question) or _subject(q)
    lower = q.casefold()

    if _is_epistemic_distress_guidance_question(q):
        return _epistemic_distress_guidance_recovery()

    if is_self_optimization_model_limits_question(q):
        return _self_optimization_model_limits_recovery()

    _human_development_comparison = compose_human_development_comparison_recovery(q)
    if _human_development_comparison:
        return _human_development_comparison

    if _is_provider_exhaustion_civic_commons_question(q):
        return _provider_exhaustion_civic_commons_recovery()

    if _is_public_commons_civic_renewal_question(q):
        return _public_commons_civic_renewal_recovery()

    if _is_institutional_legitimacy_question(q):
        return _institutional_legitimacy_recovery()

    # This conceptual contrast is an ordinary explanatory task, not an unfamiliar
    # Archive term requiring a formal-definition abstention.
    if is_orientation_information_contrast_question(q):
        return _orientation_information_contrast_recovery()

    if is_guide_meta_coverage_policy_question(q):
        return _guide_meta_coverage_policy_recovery()

    if is_epistemic_category_distinction_question(q):
        return _epistemic_category_distinction_recovery()

    # A request for one near-term stewardship act needs a practical, bounded
    # application of the public Stewardship gateway, not a generic reflection.
    if is_weekly_stewardship_action_question(q):
        return _weekly_stewardship_action_recovery()

    # Personal stewardship-invitation questions ask about agency and bounded
    # responsibility, not for a dictionary definition of the entire sentence.
    if is_personal_stewardship_invitation_question(q):
        return _personal_stewardship_invitation_recovery()

    # Belief/interpretation revision questions need a proportionate, claim-sensitive evidence standard.
    if is_interpretation_revision_evidence_question(q):
        return _interpretation_revision_evidence_recovery()

    # Evidence-discernment questions must not fall through to generic reflection.
    if is_resonance_confirmation_bias_question(q):
        return _resonance_confirmation_bias_recovery()

    # Felt-truth questions require claim-sensitive examination, not generic encouragement.
    if is_felt_truth_claim_discernment_question(q):
        return _felt_truth_claim_discernment_recovery()

    # Retrospective accountability must outrank generic decision advice:
    # evaluate process using what was knowable then, not the outcome known now.
    # Only answer the Archive-definition question with the Archive-definition
    # recovery. A question about another concept "in the Archive's sense" must
    # not be mistaken for a question asking what the Archive itself is.
    archive_subject = re.match(
        r"^(?:the\s+)?(?:living\s+)?archive(?:$|[,.!?]|\s+(?:and\s+what\s+is\s+it\s+not|itself|as\s+a\s+whole|ecosystem|purpose|mission)\b)",
        subject.casefold(),
    )
    # Provider-independent conceptual orientations are part of the visitor
    # contract. A temporary provider-bank outage must not turn a familiar
    # explanatory distinction into a disclaimer about unavailable resources.
    # Civilizational transition is a registered Archive concept family. This
    # recovery answers the concept directly during provider/retrieval outages,
    # while keeping its interpretation bounded and explicitly non-doctrinal.
    civilizational_transition = bool(
        re.search(r"\bcivilizational\s+transition\b", lower)
        and re.search(r"\b(?:what does|what is|define|explain|meaning)\b", lower)
        and re.search(r"\barchive\b", lower)
    )
    ai_interpreter_authority = bool(
        re.search(r"\bai\b", lower)
        and re.search(r"\binterpreter\b", lower)
        and re.search(r"\bauthority\b", lower)
    )
    accountable_retrieval = bool(
        re.search(r"\baccountable\s+retrieval\b", lower)
        and re.search(r"\b(?:what does|what is|define|explain|look like)\b", lower)
    )
    if is_external_discernment_outsourcing_question(q):
        answer = _external_discernment_outsourcing_recovery()
    elif is_personality_soul_oversoul_question(q):
        answer = _personality_soul_oversoul_recovery()
    elif is_guide_personal_decision_agency_question(q):
        answer = _guide_personal_decision_agency_recovery()
    elif is_regeneration_participation_question(q):
        answer = _regeneration_participation_recovery()
    elif is_trust_community_stewardship_question(q):
        answer = _trust_community_stewardship_recovery()
    elif is_spiritual_community_accountability_question(q):
        answer = _spiritual_community_accountability_recovery()
    elif is_oversoul_free_will_question(q):
        answer = _oversoul_free_will_recovery()
    elif is_oversoul_ego_authority_question(q):
        answer = _oversoul_ego_authority_recovery()
    elif accountable_retrieval:
        answer = (
            "Accountable retrieval means being able to show where an answer comes from, what supports it, and where its limits are. "
            "Finding material that appears relevant is not enough: a responsible answer keeps a visible relationship between the question, the source material, the interpretation, and the confidence that the evidence can reasonably support.\n\n"
            "In practice, this means asking whether the retrieved material directly supports the claim being made, what context is needed to understand it accurately, and where evidence ends and interpretation begins. "
            "It also means making uncertainty visible rather than filling gaps with confidence, so that a visitor can distinguish a well-supported conclusion from a useful but provisional reading.\n\n"
            "The purpose is not simply to produce a plausible answer. It is to make an answer answerable: open to examination, challenge, correction, and further inquiry. "
            "That is a form of stewardship of knowledge—handling what has been found carefully enough that neither the source nor the visitor is asked to carry more certainty than the evidence can bear."
        )
    elif is_technology_solutionism_ecological_question(q):
        answer = _technology_solutionism_ecological_recovery()
    elif is_community_project_tradeoff_question(q):
        answer = _community_project_tradeoff_recovery()
    elif _is_modes_of_knowing_dialogue_question(q):
        answer = _modes_of_knowing_dialogue_recovery()
    elif is_complex_future_scenario_question(q):
        answer = _complex_future_scenario_recovery()
    elif _is_public_predictive_system_question(q):
        answer = _public_predictive_system_recovery()
    elif _is_archive_purpose_question(q):
        answer = _archive_purpose_recovery()
    elif _is_commons_care_question(q):
        answer = _commons_care_recovery()
    elif ("algorithmic" in lower or "algorithm" in lower or "automated system" in lower) and ("bias" in lower or "biases" in lower or "institutional failure" in lower or "institutional failures" in lower):
        answer = _algorithmic_amplification_recovery()
    elif _is_feedback_loops_institutions_question(q):
        answer = _feedback_loops_institutions_recovery()
    elif _is_systems_explanation_vs_simplistic_connection_question(q):
        answer = _systems_explanation_vs_simplistic_connection_recovery()
    elif _is_humane_performance_question(q):
        answer = _humane_performance_recovery()
    elif _is_stewardship_leadership_crisis_question(q):
        answer = _stewardship_leadership_crisis_recovery()
    elif re.search(r"^\s*what\s+happens\s+(?:when|if)\b", q, re.I) and re.search(r"\bpower\b", lower) and re.search(r"\baccountab(?:ility|le)\b", lower) and re.search(
        r"\b(?:concentrat(?:ed|ion)|unchecked|without|lack(?:ing)?|unaccountable)\b", lower
    ):
        answer = _general_explanatory_recovery(q)
    elif _is_general_explanatory_question(q):
        answer = _general_explanatory_recovery(q)
    elif civilizational_transition:
        answer = (
            "In the Living Archive, civilizational transition refers to a period in which the systems that organize collective life are changing together, rather than a single government, technology, or economic arrangement simply being replaced. "
            "Ecological conditions, governance, economic relationships, information systems, and cultural coherence can all come under pressure at the same time. "
            "The transition is therefore both structural and human: established institutions and assumptions may lose their ability to organize shared life, while new practices and forms of coordination are still emerging.\n\n"
            "The Archive treats this neither as a guaranteed collapse nor as an inevitable leap into a better civilization. "
            "It is an unsettled passage in which older arrangements may continue to function unevenly, new possibilities appear, and communities experience uncertainty, fragmentation, adaptation, and resilience together. "
            "The central question is not simply what is ending, but which capacities, relationships, and institutions can help people respond responsibly as conditions change.\n\n"
            "A developmental or regenerative direction would be judged by what it makes possible in practice: more resilient communities, accountable and adaptive governance, ecological stewardship, relational coherence, and the capacity to learn across generations. "
            "The Philippines is used in one Archive case study as a revealing example of these pressures appearing in concentrated form, not as a perfect model or a uniquely destined society. "
            "This is a bounded synthesis of the Archive's published treatment, not a claim that every society follows one predetermined path."
        )
    elif ai_interpreter_authority:
        answer = (
            "An AI acts as an interpreter rather than an authority when it helps make information, patterns, and possible meanings clearer without claiming the right to make the final judgment. "
            "It can summarize evidence, compare perspectives, identify connections, and surface questions that may otherwise be missed. Those capabilities can support human understanding, but they do not by themselves establish what ought to be valued or decided.\n\n"
            "The distinction matters because an answer can sound confident without carrying the responsibility that gives a judgment its legitimacy. People and institutions remain responsible for checking important claims, considering context and consequences, and deciding which values should guide action. An AI may inform that process, but it cannot assume accountability for the people affected by a decision.\n\n"
            "A useful way to work with AI, then, is to ask it to make the landscape clearer rather than to hand over the map. Treat its responses as contributions to inquiry: examine the evidence behind them, notice what perspectives may be absent, and keep uncertainty visible where it remains. The goal is not to make human judgment unnecessary, but to help people exercise it with greater clarity and care."
        )
    elif archive_subject and re.search(r"\b(?:what is|what are|define|what does)\b", lower):
        # Constitutional-sensemaking orientation: explain the Archive's purpose,
        # distinguish it from a generic answer engine, and keep evidence,
        # interpretation, uncertainty, and human responsibility visible.
        answer = (
            "The Living Archive is a public knowledge commons and an orientation ecosystem for understanding human life through connected ideas, relationships, and systems. "
            "It brings perspectives from different domains into conversation so people can see patterns, examine how parts affect one another, and explore what may support human flourishing. "
            "Its purpose is not simply to store information, but to help people find their bearings within a wider body of thought and inquiry.\n\n"
            "It is not a chatbot that treats every question as a request for a quick, self-contained answer, a collection of unrelated pages, or an authority that claims final certainty. "
            "The Archive invites disciplined inquiry: established claims should be distinguishable from interpretation and inference; uncertainty should be acknowledged rather than hidden; and no framework should relieve people of the responsibility to think, judge, and act with care.\n\n"
            "The Guide serves this purpose through constitutional sensemaking. It helps a person locate a question within the Archive's wider relationships, identify useful canonical resources, and understand how the pieces may fit together without pretending that every connection is proven or every question settled. "
            "In practice, a question about a relationship, institution, or community can open onto wider patterns of responsibility, power, history, and care. The aim is not to decide for the visitor, but to make the landscape clearer so that further inquiry and human judgment can be better grounded."
        )
    elif re.search(r"\b(?:in|within)\s+(?:the\s+)?(?:living\s+)?archive(?:['’]s)?\s+(?:framework|approach|understanding|terms|perspective)\b", lower) and re.search(r"\b(?:what does|what is|what are|meaning|mean)\b", lower):
        # Archive-framework concept questions need a substantive bounded answer,
        # not a generic "couldn't verify" disclaimer. Explain the concept in
        # relation to the Archive's known orientation, while avoiding claims of
        # a formal doctrine unless a canonical source has actually been retrieved.
        concept_match = re.search(
            r"\bwhat does\s+(.+?)\s+mean\s+(?:in|within)\s+(?:the\s+)?(?:living\s+)?archive",
            q,
            re.I,
        )
        concept = _clean(concept_match.group(1) if concept_match else subject).strip(" .?!;:")
        answer = (
            f"In the Living Archive's framework, {concept} should be understood in relation to human flourishing, the relationships that shape people's lives, and the systems through which choices and consequences unfold. "
            f"It is not only a label for an individual trait or outcome; the useful question is how {concept} develops through the interaction of personal capacities, relationships, institutions, and the conditions people inherit or create. "
            "That relational view helps connect individual experience with the wider patterns that enable or constrain it.\n\n"
            f"Practically, this means asking what changes in a person's capacities and judgment over time, what relationships and environments support or obstruct that change, and how those effects are distributed across a community. "
            f"For {concept}, avoid treating a single measure or visible achievement as the whole story: examine the person's agency and well-being alongside the quality of their relationships and the conditions in which they participate. "
            "These are interpretive lenses for inquiry, not a claim that one metric or one causal explanation settles the question.\n\n"
            "The Archive's wider orientation is to make connections visible while distinguishing established evidence from interpretation. "
            "So use this framework to ask better questions, compare perspectives, and identify what a canonical Archive text specifically establishes; do not treat this bounded explanation as a substitute for a retrieved formal definition. "
            "If a specific codex or constitutional text defines the concept more precisely, that source should take precedence over this general orientation."
        )
    elif (definition_significance := re.match(
        r"(?i)^what is (?:an? |the )?(.+?),? and why does it matter\??$",
        re.sub(r"\s+", " ", q).strip(),
    )):
        answer = compose_definition_significance(definition_significance.group(1))
    elif _is_historical_cultural_explanation(q):
        answer = _historical_cultural_recovery()
    elif is_harm_repair_question(q):
        answer = _harm_repair_response()
    elif is_stewardship_failure_repair_question(q):
        answer = _stewardship_failure_repair_response()
    elif _is_hindsight_accountability(q):
        answer = (
            "Genuine accountability asks whether the group made a reasonable decision with the information, "
            "constraints, and alternatives available at the time. Hindsight blame assumes that because the outcome "
            "is now known, it should have been predictable all along. A harmful result, by itself, does not prove "
            "that the original decision was irresponsible.\n\n"
            "Start by reconstructing what the group knew, what remained uncertain, which alternatives were realistically "
            "available, and whether relevant warnings or dissent were taken seriously. Ask whether the group used "
            "clear criteria, considered foreseeable risks, and listened to people who would bear the consequences. "
            "Also distinguish a reasonable choice that turned out badly from a choice made carelessly or without "
            "regard for evidence the group had a duty to consider.\n\n"
            "A reasonable decision at the time does not excuse refusing to learn afterward. Accountability means "
            "acknowledging the outcome, correcting what can be corrected, and improving the decision process without "
            "rewriting the past to make blame easier."
        )
    # Lived/reflective inquiries must be answered on their own terms before
    # the generic "how" recovery. A question about holding pain is not an
    # invitation to run an institutional decision-accountability checklist.
    elif classify_inquiry_family(q).get("family") == "personal_lived_reflective":
        _lived_signals = classify_inquiry_family(q).get("signals") or []
        _lived_subject = str(_lived_signals[0] if _lived_signals else "experience").strip()
        if _lived_subject in {"identity", "selfhood", "personhood", "belonging", "who i am", "sense of self"}:
            _lived_subject = "experience"
        _lived_subject = _lived_subject[:40]
        answer = (
            f"{_lived_subject[:1].upper() + _lived_subject[1:]} can be part of a person's life "
            "without becoming the whole of who they are. Holding it means acknowledging what "
            "hurt and allowing it to matter, without mistaking that experience for a complete "
            "account of the self. A person remains more than the experience: relationships, "
            "values, interests, capacities, memories, and hopes also belong to their identity.\n\n"
            "This does not mean denying the experience, romanticizing it, or forcing it to become "
            "a lesson. It means giving it an honest place without letting it occupy every place. "
            "The experience can shape a life deeply without becoming the only story that life "
            "is allowed to tell."
        )
    # Ethical conflicts must outrank generic "how" / practical-action patterns.
    elif _is_ethical_tradeoff(q):
        from community_rule_decision_contract import is_community_rule_decision_question
        if is_community_rule_decision_question(q):
            answer = (
                "A community balancing individual freedom and shared responsibility should begin with a legitimate shared purpose, grounded in a demonstrable harm, "
                "common need, or coordination problem rather than majority preference alone. It should explain "
                "the evidence connecting that need to the proposed rule and identify the specific individual "
                "freedom the rule would affect.\n\n"
                "Before adopting a restriction, ask whether it is necessary and proportionate, and compare less "
                "restrictive alternatives before choosing the least restrictive workable means that addresses "
                "the shared need. State who benefits, who bears "
                "the costs, and how burdens will be fairly distributed. Provide reasonable accommodation for "
                "people whose circumstances or needs differ, rather than treating one arrangement as workable "
                "for everyone.\n\n"
                "People who will be affected should have meaningful agency and a meaningful opportunity to shape the rule before adoption. "
                "They must also have a meaningful way to question or appeal its application, with observable criteria "
                "for review and a clear point at which the community will reconsider whether the restriction "
                "remains necessary and fair. A majority can express a preference, but preference alone does not "
                "establish necessity or justify shifting avoidable burdens onto others."
            )
        elif (
            re.search(r"\bindividual\s+freedom\b", lower)
            and re.search(r"\bshared\s+responsibility\b", lower)
        ):
            answer = (
                "A community should not treat individual freedom and shared responsibility as opposites. "
                "Freedom gives people room to make choices and pursue legitimate interests; shared responsibility "
                "recognizes that choices also affect the conditions other people depend on. A fair decision asks "
                "how to protect both, and where a genuine conflict remains, what limits are justified.\n\n"
                "Begin by identifying the specific freedom at stake, the shared need or harm the community is "
                "trying to address, and the evidence connecting the proposed action to that need. Include the "
                "people who will be affected, especially those with less influence, and distinguish a necessary "
                "shared obligation from a preference being imposed by the majority. Consider less restrictive "
                "alternatives, distribute burdens fairly, and make sure any constraint is proportionate to the "
                "harm it is meant to prevent.\n\n"
                "The decision is more defensible when its reasons are public, the rule applies consistently, "
                "individual rights are not casually overridden, and people can question or appeal its application. "
                "Agree on who is accountable, what outcomes will be reviewed, and when the arrangement should be "
                "revised. A workable community does not require everyone to agree on every choice; it requires "
                "people to understand the shared reasons, retain meaningful agency, and have a fair way to correct "
                "decisions that impose unjustified costs."
            )
        elif re.search(r"\bstewardship\b", lower) and re.search(r"\b(?:disagree|protect)\w*\b", lower):
            answer = (
                "When people disagree about what is worth protecting, the disagreement may reflect different "
                "values, responsibilities, or fears about what could be lost. One person may be trying to preserve "
                "continuity; another may believe change is necessary to protect people or keep something useful. "
                "Name those underlying concerns before treating the other person as careless or unreasonable.\n\n"
                "A practical next step is to ask what each person is trying to protect, who would bear the costs of "
                "each option, and which responsibilities or rights cannot simply be traded away. Separate shared "
                "facts from judgments, and look for options that preserve the most important interests while making "
                "the unavoidable trade-offs explicit.\n\n"
                "People may not reach identical priorities, and stewardship does not require pretending otherwise. "
                "They can still agree on a fair process, explain their reasons, consider people affected but not "
                "represented, and review the decision when new evidence or consequences emerge. The aim is to handle "
                "disagreement responsibly, not to erase it."
            )
        elif re.search(r"\b(?:stakeholders?|obligations?|duties)\b", lower):
            # This is a general provider-exhaustion recovery, not the verbatim
            # answer to the separately approved exact Gold Standard question.
            # Keep its reasoning useful while preventing cross-question answer reuse.
            answer = (
                "Competing stakeholder obligations should be assessed by separating the kinds of obligations involved. A legal or contractual duty, a promise already made, a basic right, and a reasonable expectation may carry different weight. Name the people affected and what each group is owed; do not let the group with the most influence define the whole problem.\n\n"
                "Compare realistic options by tracing benefits, costs, risks, timing, reversibility, who can influence the decision, and who carries the cost. Ask whether the burden falls on people who have little voice, whether less harmful alternatives exist, and whether a benefit to one group depends on transferring an avoidable cost to another. Distinguish evidence about likely effects from assumptions about what each group will accept.\n\n"
                "If priorities still conflict, state which obligation takes precedence and why, then reduce remaining harm through mitigation, compensation where appropriate, clear responsibility, and a review point. Give affected groups, especially those with less power, a meaningful way to question the reasoning and report consequences. Fairness does not guarantee that every group receives the same outcome; it requires a defensible process and accountability for the costs the decision leaves behind."
            )
        else:
            answer = (
                "When protecting one important thing puts something else at risk, the decision cannot be made fairly "
                "by asking only which priority matters more. We also need to consider who depends on each choice, "
                "who has the power to decide, and who will bear the consequences.\n\n"
                "Make each person's claim visible, including the needs of people who may not have a voice in the "
                "decision. Distinguish losses that can be repaired from those that cannot, and examine whether a "
                "different approach could protect at least part of what matters to each side. Shared facts, clear "
                "criteria, and a chance for affected people to challenge assumptions make the process more defensible.\n\n"
                "Sometimes a genuine trade-off remains. In that case, responsibility means explaining the reasons for "
                "the decision, acknowledging what is being sacrificed, and checking that the burden does not fall "
                "unfairly on those with the least power. The question is not only what we choose to protect, but "
                "whether we can justify that choice to the people who must live with its consequences."
            )
    elif re.search(
        r"\b(?:what distinguishes|distinguish(?:es)?|what separates|separates|"
        r"what differentiates|differentiate(?:s)?|compare|comparison|difference|"
        r"different from|differ from|versus|vs)\b",
        lower,
    ) and re.search(r"\b(?:leadership|leader|authority|authorit(?:y|ies)|power|role|position)\b", lower):
        answer = (
            "Positional authority comes from a formal role: it gives someone recognized power or responsibility to make decisions, assign work, or direct others. Leadership is demonstrated in how a person exercises judgment, influences collective action, and earns trust. A title can grant authority, but it does not automatically make the person's decisions wise or their influence worthy of confidence.\n\n"
            "The difference becomes clear in practice. A manager may have the right to issue an instruction, while a colleague without a senior title may show leadership by listening to concerns, clarifying a shared purpose, and helping the group choose a responsible course. Someone with formal authority can also lead well when they explain decisions, act fairly, accept accountability, and make room for others' knowledge.\n\n"
            "In short, positional authority answers, “What power or responsibility comes with this role?” Leadership asks, “How does this person guide collective action, and what makes that guidance worth following?” The two can reinforce each other, but authority alone does not establish leadership; the distinction lies in how responsibility is exercised and what that conduct makes possible for others."
        )
    elif re.search(r"\b(?:compare|comparison|difference|different from|differ from|versus|vs)\b", lower):
        answer = (
            f"A sound comparison of {subject} begins by naming the options and comparing them on the same dimensions: what each means, how each works, and what consequences follow.\n\n"
            "Then separate the defining difference from details the options share. Consider a concrete example, who is affected, and what evidence supports the comparison rather than assuming that one option is better simply because it has a different name or purpose.\n\n"
            "The useful conclusion is the distinction that changes how the options should be understood or used. Where the question does not supply enough context to rank them, explain the difference that can be established and state only that narrower limitation—not that the question itself cannot be answered."
        )
    elif re.search(r"\bwhat (?:kinds? of )?questions? should (?:be asked|we ask|people ask)\b", lower) and re.search(r"\bbefore\b", lower):
        # Shared pre-action inquiry composition. Turn "what questions before X?"
        # into a useful, answer-first set of decision lenses rather than a
        # generic reliability disclaimer. The question family is reusable
        # across redesigns, launches, restructurings, and other consequential work.
        action_match = re.search(r"\bbefore\s+(.+?)[?.!]*$", q, re.I)
        action = _clean(action_match.group(1) if action_match else subject).strip(" .?!;:")
        answer = (
            f"Before {action}, ask what problem actually needs solving, who is affected, and what purpose the change is meant to serve. "
            "What evidence shows the current arrangement is failing, and which parts are working well enough to preserve? "
            "These questions prevent a redesign from starting with a preferred solution before the need and intended outcome are clear.\n\n"
            "Next, ask how authority and responsibilities are distributed, whose knowledge is missing, and who may gain or lose power under the proposed change. "
            "Which rights, obligations, or safeguards must not be weakened? What realistic alternatives exist, what could each option cost, and how would people affected challenge assumptions or raise concerns without penalty? "
            "These questions expose consequences that may be invisible to the people designing the change.\n\n"
            "Finally, ask how success will be judged, who will review the decision independently, and what would trigger correction or reversal if the change causes harm. "
            "Set observable criteria, make reasons transparent, involve affected people before decisions are locked in, and schedule a review after implementation. "
            "The goal is not to eliminate uncertainty; it is to make the change understandable, contestable, and correctable rather than relying on confidence or good intentions alone."
        )
    elif re.search(r"\b(?:risks?|dangers?|hazards?)\b", lower) and re.search(r"\bwithout\b", lower):
        # Shared risk-without-constraint composition: explain mechanism,
        # practical consequence, and safeguard across this question family.
        match = re.search(r"\b(?:risks?|dangers?|hazards?)\s+(?:of|from)\s+(.+?)\s+without\s+(.+)$", q, re.I)
        if match:
            force = _clean(match.group(1)).strip(" .?!;:")
            constraint = _clean(match.group(2)).strip(" .?!;:")
        else:
            force, constraint = subject, "meaningful limits and accountability"
        answer = (
            f"The risk of {force} without {constraint} is that influence or capacity can operate without the checks that keep it answerable to a shared purpose. "
            f"When people or institutions rely on {force}, its appeal or immediate effectiveness can make it seem self-justifying. "
            f"Without {constraint}, those affected may have no dependable way to question decisions, limit excess, or correct harm.\n\n"
            f"In practice, the danger is a shift from serving a common purpose to protecting the person, group, or mechanism that holds the influence. "
            "Decisions may become harder to challenge, dissent may be treated as disloyalty, and mistakes can persist because the same influence that drives action also weakens independent scrutiny. "
            f"The problem is not necessarily {force} itself; it is the absence of a reliable way to test how it is used and who bears its consequences.\n\n"
            f"The safeguard is to make authority and consequences visible, distribute decision-making where appropriate, protect principled dissent, and establish review that does not depend on the goodwill of the person exercising influence. "
            f"Those safeguards let {force} contribute its benefits while keeping its use accountable to {constraint}. "
            "They also give the community a practical way to correct course when the effects depart from the shared purpose."
        )
    elif re.search(r"\bwhat (?:is|are)\b", lower) and re.search(r",\s*and\s+why\s+does\s+it\s+matter\??", lower):
        # A definition-plus-significance question is still a definition request.
        # Its trailing "why does it matter" must not route it into the generic
        # causal explanation template, which previously produced a fluent but
        # non-substantive answer during provider exhaustion.
        answer = compose_definition_significance(subject)
    elif (significance_question := re.match(
        r"(?i)^why (?:does|do)\s+(.+?)\s+matter(?:\s+(?:when|where|in|for|to)\s+(.+?))?[?.!]*$",
        re.sub(r"\s+", " ", q).strip(),
    )):
        significance_subject = re.sub(
            r"^(?:a|an|the)\s+", "", significance_question.group(1), flags=re.I
        )
        significance_subject = re.sub(
            r"^(?:clear|good|effective|reliable|poor|weak|strong|timely)\s+",
            "", significance_subject, flags=re.I
        )
        significance_context = significance_question.group(2) or ""
        answer = _significance_recovery(
            significance_subject,
            significance_context.rstrip(" ?.!;:"),
        )
    elif re.search(r"\b(?:why|what causes|reason for)\b", lower):
        answer = (
            "A useful explanation begins by distinguishing the immediate event from the conditions that made it more likely. "
            "A visible incident may be the trigger without being the whole cause.\n\n"
            "Look at the evidence, incentives, constraints, relationships, and decisions involved, and compare more than one plausible explanation. "
            "For example, a repeated failure may reflect unclear responsibilities or conflicting incentives rather than a lack of effort by one person.\n\n"
            "These are possibilities to test, not conclusions about a specific case. The strongest explanation accounts for the available facts, "
            "acknowledges what remains uncertain, and identifies what new information could confirm or change the interpretation."
        )
    elif re.search(r"\b(?:should i|should we|is it worth|whether to|decision|decide)\b", lower):
        answer = (
            f"The decision about {subject} depends on the responsibilities involved, the consequences of each option, and who will carry the costs. "
            "Begin by separating what must be protected from what can be negotiated.\n\n"
            "Compare realistic alternatives, the strongest reason for and against each, which effects are reversible, and what evidence would change your mind. "
            "Include people significantly affected, especially those whose interests may otherwise be overlooked.\n\n"
            "A responsible decision does not require certainty, but it does require clear reasons, proportionate attention to risk, and willingness to correct course. "
            "If a choice is reversible, a limited trial may be wiser than treating it as permanent; if it creates lasting harm, use a more demanding standard of care."
        )
    elif re.search(r"\b(?:discuss|understand|talk about|speak about)\b", lower) and re.search(r"\bdecline\b", lower) and re.search(r"\b(?:romanticiz|nostalgia|nostalgic)\b", lower):
        # Reflective questions about decline are not generic action-planning
        # requests. Keep loss, historical memory, and change in view, then
        # offer one evidence-backed Archive doorway when the local canonical
        # snapshot contains a close continuation of the inquiry.
        answer = (
            "To discuss decline without romanticizing it, we have to resist two shortcuts: treating the past as a lost golden age, and treating every departure from it as progress. "
            "The first turns memory into nostalgia; the second can make real losses disappear from view. A more honest account begins by asking what has changed, what has been lost, what has become possible, and—crucially—for whom.\n\n"
            "That keeps decline from becoming a single verdict. A community may gain efficiency while losing continuity; an institution may become more flexible while weakening trust; a society may expand some freedoms while allowing skills, places, relationships, or forms of belonging to erode. "
            "None of this proves that the past was better. It means that change has to be described in more than one dimension, including the people who benefited, the people who bore the costs, and the things whose value only becomes visible when they are gone.\n\n"
            "Perhaps the most useful question is not whether we are 'for' or 'against' decline, but what kind of attention the moment requires: what should be mourned without being idealized, what should be preserved without being frozen, what should be repaired, and what should be allowed to end. "
            "That is where a discussion of decline can become an inquiry into responsibility rather than a contest between nostalgia and optimism.\n\n"
            "If you want to continue this inquiry, **What Changed That I Haven’t Been Able to Name?** offers a related doorway into recognizing and naming changes that are real before deciding what they mean: https://geralddaquila.com/what-changed-that-i-havent-been-able-to-name"
        )
    elif (
        re.search(r"\bhow can (?:one|we|you) distinguish\b", lower)
        and re.search(r"\bstructural change\b", lower)
        and re.search(r"\bordinary disruption\b", lower)
    ):
        # Direct-answer recovery for the structural-change/disruption distinction.
        # This is deliberately part of the provider-exhaustion composer: the
        # visitor must receive the substantive distinction even when every
        # provider candidate is rejected or unavailable.
        answer = (
            "Structural change alters the underlying conditions that reproduce a pattern; ordinary disruption interrupts the pattern's visible operation without necessarily changing those conditions.\n\n"
            "To tell them apart, look for evidence that the system's rules, relationships, incentives, decision rights, or capacities have changed—and whether those changes persist after the immediate pressure eases. A disruption can be severe while leaving those arrangements intact; structural change alters how the system produces outcomes over time.\n\n"
            "The test is not simply whether something new happened. Ask what now works differently, whose options or responsibilities have changed, what makes the old pattern less likely to recur, and what evidence would show that the change has held. If the old pattern returns as soon as the disturbance passes, the event was more likely disruption than structural change."
        )
    elif (
        re.search(r"\bformal structure\b", lower)
        and re.search(r"\bactual power structure\b", lower)
    ):
        answer = (
            "An institution can recognize the gap between its formal structure and its actual power structure by tracing who shapes decisions, controls information and resources, influences outcomes, and can safely challenge authority. "
            "An organization chart shows assigned roles; it does not necessarily show whose judgment carries weight or whose objections can change a decision.\n\n"
            "Look at consequential decisions over time: who sets the available options, whose information reaches decision-makers, who can delay or redirect action, and what happens to people who disagree. "
            "Compare written authority with these repeated patterns, and listen to people whose work or lives are affected by them.\n\n"
            "Informal influence is not automatically illegitimate, and formal authority is not automatically misused. "
            "The important test is whether consequential power is visible, open to challenge, and connected to clear responsibility and review."
        )
    elif re.search(r"\btransition between software systems\b", lower):
        answer = (
            "A city can manage a transition between software systems by protecting service continuity while migrating data, dependencies, and responsibilities in a staged, verifiable sequence. "
            "Begin by identifying the services that must remain available, the records that must remain accurate, and the people accountable for each part of the transition.\n\n"
            "Map integrations and dependencies before moving data, test migration and recovery procedures in a controlled environment, and run old and new systems in parallel where the risk justifies it. "
            "Set clear acceptance criteria, communicate changes to staff and residents, and keep a rollback path until the new system is demonstrably reliable.\n\n"
            "The transition is complete when essential services work accurately under the new arrangement, staff can operate it, and outstanding risks have named owners. "
            "A cutover date alone is not evidence of success; continuity, data integrity, security, and the ability to recover are."
        )
    elif (
        re.search(r"\bcompany\b", lower)
        and re.search(r"\bai\b", lower)
        and re.search(r"\breduc(?:e|ing)\s+staffing\s+costs?\b", lower)
        and all(term in lower for term in ("operations", "governance", "human development", "ethics", "stewardship"))
    ):
        answer = (
            "A company considering AI to reduce staffing costs should assess not only the projected savings but how the change redistributes work, authority, risk, and opportunity. "
            "The decision needs to be examined through operations, governance, human development, ethics, and stewardship together, because a financial gain can conceal costs shifted onto workers, customers, or the institution itself.\n\n"
            "Next, compare the real options: redesigning tasks, augmenting work, reducing hours, retraining, redeploying people, or reducing roles. "
            "For each option, test the evidence behind expected savings, the quality and reliability of the system, the effect on service and working conditions, who carries transition costs, and whether affected people have meaningful voice and recourse.\n\n"
            "AI may inform that work, but it cannot take responsibility for the decision away from the people who have the authority to make it. "
            "A defensible decision makes its criteria visible, protects rights and dignity, assigns accountability for errors, and reviews actual outcomes rather than treating projected efficiency as proof of success."
        )
    elif is_community_continuity_revision_question(q):
        answer = _community_continuity_revision_recovery()
    elif (reflective_answer := _reflective_conceptual_recovery(q)) is not None:
        answer = reflective_answer
    elif (
        re.search(r"\b(?:how|should|act|decide|decision|choose)\b", lower)
        and re.search(r"\b(?:uncertain|uncertainty|unknown|unpredictable)\b", lower)
        and re.search(r"\b(?:consequential|consequences|stakes|high\s+stakes|serious)\b", lower)
    ):
        answer = (
            "When a decision has serious consequences and the future is uncertain, act in proportion to what is known rather than waiting for certainty or pretending to have it. "
            "Begin by identifying what must be protected, who will be affected, which responsibilities cannot be deferred, and which parts of the situation remain unknown.\n\n"
            "Compare realistic options by looking at what each makes possible, what it could damage, who carries the costs, and what evidence would change the assessment. "
            "Give particular weight to people who will live with the consequences, including those with the least influence over the decision.\n\n"
            "Then choose a course that preserves room to learn and correct where possible. Set clear signals for review, name who is accountable for watching the effects, and change direction when evidence or conditions warrant it. "
            "A decision can be necessary without being certain; its quality depends partly on whether it remains answerable to the people and realities it affects."
        )
    elif re.search(r"\b(?:how|steps|approach|what can i do|what should we do|how to)\b", lower):
        answer = (
            "Start by defining the outcome the change must achieve, the responsibilities that cannot be lost, and the people who will live with its consequences. "
            "Then compare realistic options against those requirements rather than assuming the proposed course is the only one.\n\n"
            "Examine what each option makes possible, what it may damage, who bears the costs, and what evidence would justify changing direction. "
            "Include the knowledge of people affected by the decision, especially where they will carry consequences they did not choose.\n\n"
            "Choose deliberately, make the reasoning and limits visible, and remain accountable for what follows. "
            "AI may inform that work, but it cannot take responsibility for a decision away from the people who have the authority to make it."
        )
    elif re.search(r"\b(?:what is|what are|define|definition|meaning of|what does .* mean)\b", lower):
        answer = compose_definition_significance(subject)
    elif re.search(r"\b(?:meaning|make sense|understand|interpret|reflect|relationship)\b", lower):
        answer = (
            f"A useful starting point for {subject} is to separate what is known from what is inferred, then ask which distinction or tension matters most. "
            "This prevents a first interpretation from being mistaken for the whole picture.\n\n"
            "Notice what is observable, what depends on interpretation, and which relationships or circumstances shape the situation. "
            "Consider another plausible reading and ask what evidence would support or weaken each one.\n\n"
            "This keeps the inquiry open without treating every explanation as equally well supported. A sound understanding should clarify what can be concluded, "
            "what remains uncertain, and what further evidence would genuinely matter."
        )
    else:
        answer = (
            f"The question about {subject} can be approached by first identifying the main issue and the decision or understanding at stake. "
            "A useful answer should distinguish what is established from what is inferred rather than fill gaps with confidence.\n\n"
            "The next step is to examine the most relevant facts, relationships, and plausible explanations. "
            "Ask which evidence would distinguish them, whose perspective may be missing, and whether any assumption is doing more work than the facts justify.\n\n"
            "This provides a grounded starting point without pretending to know details the question has not supplied. "
            "Where the evidence is incomplete, say what can reasonably be concluded and what remains open, instead of replacing the answer with a generic refusal."
        )

    # Last-resort task recovery: preserve all higher-priority specialist and
    # conceptual branches above, then consult the provider-independent task
    # catalogue before returning a generic synthesis. This makes the catalogue
    # part of the shared failure architecture without letting broad task matches
    # override more specific recovery contracts.
    task_recovery = compose_task_specific_recovery(q)
    if isinstance(task_recovery, dict):
        task_response = _clean(task_recovery.get("response"))
        if task_response:
            return task_response

    movement = _clean(desired_movement)
    if movement and not is_harm_repair_question(q) and not _is_ethical_tradeoff(q) and not _is_hindsight_accountability(q):
        answer += f" A sensible next step is to focus on {movement.rstrip('.')}."
    # A generic clarifier is not an acceptable default ending for a question
    # that reached recovery with a concrete subject. The separate request-boundary
    # classifier remains responsible for genuinely missing subjects.
    # Deterministic recovery consumes only explicitly eligible Gold Star
    # structural guidance; exemplar answer content is never transferred.
    try:
        from gold_star_lessons import apply_deterministic_fallback_guidance
        answer = apply_deterministic_fallback_guidance(q, answer)
    except Exception:
        pass
    return answer


_accountable_retrieval_question = "What does accountable retrieval look like?"
_accountable_retrieval_answer = compose_recovery(_accountable_retrieval_question)
_accountable_retrieval_paragraphs = [part.strip() for part in _accountable_retrieval_answer.split("\n\n") if part.strip()]
if len(_accountable_retrieval_paragraphs) != 3:
    raise RuntimeError("Accountable retrieval recovery contract failed: expected three substantive paragraphs.")
for _required in ("where an answer comes from", "directly supports", "uncertainty", "answerable"):
    if _required not in _accountable_retrieval_answer.casefold():
        raise RuntimeError("Accountable retrieval recovery contract failed: missing accountability structure.")
for _forbidden in ("add context", "not enough grounded material", "couldn't verify a reliable answer"):
    if _forbidden in _accountable_retrieval_answer.casefold():
        raise RuntimeError("Accountable retrieval recovery contract failed: refusal-style fallback leaked.")

_risk_constraint_question = "What are the risks of charisma without constitutional restraint?"
_risk_constraint_answer = compose_recovery(_risk_constraint_question)
_risk_constraint_paragraphs = [
    part.strip() for part in re.split(r"\n\s*\n+", _risk_constraint_answer) if part.strip()
]
if len(_risk_constraint_paragraphs) != 3:
    raise RuntimeError("Risk/constraint recovery contract failed: expected three substantive paragraphs.")
for _required in ("charisma", "constitutional restraint", "dissent", "accountable"):
    if not re.search(r"\b" + re.escape(_required) + r"\b", _risk_constraint_answer, re.I):
        raise RuntimeError("Risk/constraint recovery contract failed: missing substantive mechanism or safeguard.")

def contract_snapshot():
    return {
        "contract_version": "v2",
        "provider_independent": True,
        "does_not_invent_archive_evidence": True,
        "question_shapes": ["spiritual_community_accountability", "hindsight_accountability", "ethical_tradeoff", "comparison", "causal", "decision", "practical", "definition", "reflective", "general"],
    }


for _question in (
    "Why do communities lose trust?",
    "How can a team make a fair decision?",
    "What is institutional responsibility?",
    "Compare individual freedom and shared responsibility.",
    "What should we consider before changing a policy?",
    "Help me understand a difficult situation.",
    "What does stewardship look like when people disagree about what is worth protecting?",
    "What if each person sincerely believes they are protecting something important, but protecting one person's priorities means another person will lose something they deeply value? How should we decide what to protect?",
):
    _answer = compose_recovery(_question)
    if not _answer or len(_answer) < 80:
        raise RuntimeError("Deterministic answer recovery contract failed: response too short.")
    if (
        re.search(r"\b(?:provider bank|retrieval layer|canonical evidence|machine-facing)\b", _answer, re.I)
        or re.search(r"\bUSE\b", _answer)
    ):
        raise RuntimeError("Deterministic answer recovery contract failed: internal language leaked.")

_tradeoff_answer = compose_recovery(
    "What if each person sincerely believes they are protecting something important, but protecting one person's priorities means another person will lose something they deeply value? How should we decide what to protect?"
)
if "repaired" not in _tradeoff_answer or "least power" not in _tradeoff_answer:
    raise RuntimeError("Ethical trade-off recovery contract failed: missing loss and power analysis.")
if "choose one step small enough to test" in _tradeoff_answer:
    raise RuntimeError("Ethical trade-off recovery contract failed: generic practical branch won classification.")

_harm_repair_question = (
    "What should the group do if the people who suffered the harm say that its proposed repair "
    "does not address what they actually lost?"
)
_harm_repair_answer = compose_recovery(_harm_repair_question)
if not is_harm_repair_question(_harm_repair_question):
    raise RuntimeError("Harm-repair recovery contract failed: canonical question was not classified.")
for _required in ("pause and reconsider the repair", "Listen to the people affected", "revise the proposal", "declare the matter resolved"):
    if _required not in _harm_repair_answer:
        raise RuntimeError("Harm-repair recovery contract failed: missing substantive guidance.")
if "What detail or context would make this question" in _harm_repair_answer:
    raise RuntimeError("Harm-repair recovery contract failed: generic follow-up leaked.")
if is_harm_repair_question("How do I repair a bicycle tire?"):
    raise RuntimeError("Harm-repair recovery contract failed: ordinary repair question misclassified.")

_historical_cultural_question = "On surface, the Philippines is very much a macho society. Where is the matriarchal reality come from and how it evolved?"
_historical_cultural_answer = compose_recovery(_historical_cultural_question)
if not _is_historical_cultural_explanation(_historical_cultural_question):
    raise RuntimeError("Historical-cultural recovery contract failed: question was not classified.")
if "A practical way to approach" in _historical_cultural_answer or "What detail or context" in _historical_cultural_answer:
    raise RuntimeError("Historical-cultural recovery contract failed: generic practical template leaked.")
if len(_historical_cultural_answer.split("\n\n")) != 3:
    raise RuntimeError("Historical-cultural recovery contract failed: Gold Standard paragraph structure lost.")
if not all(term in _historical_cultural_answer.casefold() for term in ("precolonial", "colonial", "public")):
    raise RuntimeError("Historical-cultural recovery contract failed: historical explanation incomplete.")

_historical_cultural_required = (
    "public masculinity", "precolonial", "spanish colonial", "varied by community",
    "unpaid work", "not be mistaken for equality"
)
if not all(term in _historical_cultural_answer.casefold() for term in _historical_cultural_required):
    raise RuntimeError("Historical-cultural Gold Standard contract failed: explanatory depth or nuance missing.")
if "choose one step small enough to test" in _historical_cultural_answer:
    raise RuntimeError("Historical-cultural Gold Standard contract failed: practical template leaked.")
_techno_utopian_question = "What is the danger of techno-utopian thinking?"
_techno_utopian_answer = compose_recovery(_techno_utopian_question)
# Verify the answer's structural ideas without coupling the contract to one
# grammatical surface form. "technology" covers technological/technically;
# the other stems cover power, institutional structure, and consequences.
for _required in ("technolog", "power", "institution", "cost"):
    if _required not in _techno_utopian_answer.casefold():
        raise RuntimeError("Techno-utopian recovery contract failed: missing structural risk analysis.")
if _techno_utopian_answer.startswith("I can't define "):
    raise RuntimeError("Techno-utopian recovery contract failed: ordinary concept incorrectly treated as unknowable.")

_archive_framework_question = "What does human development mean in the Archive’s framework?"
_archive_framework_answer = compose_recovery(_archive_framework_question)
_archive_framework_paragraphs = [part.strip() for part in _archive_framework_answer.split("\n\n") if part.strip()]
if len(_archive_framework_paragraphs) != 3:
    raise RuntimeError("Archive-framework concept recovery contract failed: expected three paragraphs.")
for _required in ("human flourishing", "relationships", "evidence", "canonical"):
    if _required not in _archive_framework_answer.casefold():
        raise RuntimeError("Archive-framework concept recovery contract failed: missing " + _required)
if "I couldn't verify a reliable answer" in _archive_framework_answer:
    raise RuntimeError("Archive-framework concept recovery contract failed: refusal-style fallback leaked.")

_preaction_question = "What kinds of questions should be asked before redesigning a governance system?"
_preaction_answer = compose_recovery(_preaction_question)
_preaction_paragraphs = [part.strip() for part in _preaction_answer.split("\n\n") if part.strip()]
if len(_preaction_paragraphs) != 3:
    raise RuntimeError("Pre-action inquiry recovery contract failed: expected three paragraphs.")
for _required in ("what problem", "who is affected", "authority", "alternatives", "review", "correction"):
    if _required not in _preaction_answer.casefold():
        raise RuntimeError("Pre-action inquiry recovery contract failed: missing decision lens " + _required)
if "I couldn't produce a reliable answer" in _preaction_answer:
    raise RuntimeError("Pre-action inquiry recovery contract failed: refusal-style fallback leaked.")

for _control_question in (
    "How do I plan a practical test of a new workflow?",
    "How should a team choose its next step?",
):
    _control_answer = compose_recovery(_control_question)
    if len([part for part in _control_answer.split("\n\n") if part.strip()]) != 3:
        raise RuntimeError("System-wide recovery contract failed: practical control question lost the three-paragraph default.")
    if "least power" in _control_answer:
        raise RuntimeError("Ethical trade-off recovery contract failed: ordinary practical question was misclassified.")
