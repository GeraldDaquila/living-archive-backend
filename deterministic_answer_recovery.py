"""Bounded provider-independent recovery for The Guide."""
import re


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
    display_subject = subject[:1].upper() + subject[1:]
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
    subject = _clean(subject).strip(" ,;:") or "the concept"
    normalized = re.sub(r"\s+", " ", subject).strip().casefold()
    if normalized == "handoffs":
        normalized = "handoff"
    known = compose_definition_significance(normalized)
    if not known.startswith("I can't define "):
        return known

    display_subject = subject[:1].upper() + subject[1:]
    context = _clean(context).strip(" ,;:")
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
        r"stakeholders?|obligations?|duties|interests)\b", q
    ))
    asks_for_judgment = bool(re.search(
        r"\b(?:how can|how should|how do we|how should we decide|how do we decide|"
        r"what should we protect|what if|who should decide|which should|what is fair|"
        r"fair process|balance|reconcile|hold .{0,70} obligations?|what does .{0,80} look like)\b", q
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


def _is_public_predictive_system_question(question):
    """Recognize consequential public-sector predictive systems before generic fallback."""
    q = _clean(question).casefold()
    public_system = bool(re.search(
        r"\b(?:government|public services?|public sector|state|municipal|city government|agency)\b",
        q,
    ))
    predictive_system = bool(re.search(
        r"\b(?:predictive system|predictive model|algorithmic system|automated decision|ai system|automated system)\b",
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
    #
    # Power-and-accountability questions are ordinary answerable conceptual
    # inquiries. They must not collapse into an Archive-evidence disclaimer
    # merely because retrieval does not return an exact canonical passage.
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
if not _is_general_explanatory_question(_power_accountability_probe):
    raise RuntimeError("Power-accountability explanatory recovery invariant failed")
if len(_general_explanatory_recovery(_power_accountability_probe)) < 500:
    raise RuntimeError("Power-accountability recovery produced an insufficient conceptual answer")

def _archive_purpose_recovery():
    """Explain the Archive's orientation problem without claiming a single total cause."""
    return (
        "The Living Archive exists in response to a problem of fragmentation: knowledge can be abundant while understanding remains scattered. Information is often separated from the larger conditions that give it meaning, and people can accumulate facts, opinions, and expertise without gaining a clearer sense of how the pieces relate or what responsibility follows from seeing them together. The problem is not simply a lack of information; it is the difficulty of finding orientation within an abundance of it.\n\n"
        "The Archive therefore tries to make relationships visible across questions that are too often treated in isolation—between people and institutions, knowledge and judgment, history and the present, individual experience and larger systems. Its purpose is not to supply one final explanation or tell visitors what to think. It is to create a place where ideas, patterns, and perspectives can be held in relation so that a question becomes more intelligible before a conclusion is rushed.\n\n"
        "What the Archive ultimately addresses is the gap between having more knowledge and knowing how to live, decide, and act responsibly with it. Orientation matters when certainty is unavailable and no single discipline can see the whole of a problem. The Archive's contribution is therefore to help people notice the relationships that matter, preserve questions that should not be simplified away, and recover the possibility of more conscious judgment and stewardship."
    )


def has_registered_recovery(question):
    """True only when a bounded deterministic recovery is explicitly registered."""
    return bool(
        _is_public_predictive_system_question(question)
        or _is_archive_purpose_question(question)
        or _is_commons_care_question(question)
        or _is_feedback_loops_institutions_question(question)
        or _is_systems_explanation_vs_simplistic_connection_question(question)
        or _is_humane_performance_question(question)
        or _is_stewardship_leadership_crisis_question(question)
        or _is_general_explanatory_question(question)
        or _is_modes_of_knowing_dialogue_question(question)
        or is_stewardship_failure_repair_question(question)
    )


def _public_predictive_system_recovery():
    """Orient predictive public systems around legitimacy before performance."""
    return (
        "The first question is not whether a predictive system is efficient, but what kind of public power it is being asked to exercise. If it influences access to services, opportunities, or scrutiny, its purpose and authority should be clear before its performance is celebrated. Who remains responsible for the decision, what rights place limits on the system, and what must a person still be able to question or appeal? Efficiency can improve administration; it cannot by itself make the exercise of public authority legitimate.\n\n"
        "A second question concerns what the system carries forward. Predictive tools learn from records of the past, and those records may contain unequal access, earlier exclusions, or assumptions that have become invisible with time. People affected by a consequential decision should be able to understand enough to challenge it, correct an error, and reach a responsible human authority. Those who live with the consequences are not merely sources of data; they remain participants in the public order the system is meant to serve.\n\n"
        "Only within those boundaries does efficiency become the right question. Compare the proposed system with realistic alternatives, make its gains and risks visible, and decide in advance how errors will be detected, reviewed, and repaired. Keep adoption reversible where possible and preserve independent scrutiny when the consequences are serious. The aim is not to reject prediction, but to keep technology in its proper place: as a tool of public service, not a substitute for constitutional responsibility or human judgment."
    )


def registered_recovery_recommendation(question):
    """Return an evidence-backed doorway for a narrow registered recovery."""
    if _is_public_predictive_system_question(question):
        return {
            "title": "AI vs. Human Stewardship: Why Conscious Guidance Matters More Than Ever",
            "url": "https://geralddaquila.com/2026/06/16/ai-vs-human-stewardship-why-conscious-guidance-matters-more-than-ever/",
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


def compose_recovery(question, *, underlying_question="", desired_movement=""):
    """Offer a useful bounded response without inventing facts or sources."""
    q = _clean(question)
    if not q:
        return "What would you like to understand or work through?"
    subject = _clean(underlying_question) or _subject(q)
    lower = q.casefold()

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
    if _is_modes_of_knowing_dialogue_question(q):
        answer = _modes_of_knowing_dialogue_recovery()
    elif _is_public_predictive_system_question(q):
        answer = _public_predictive_system_recovery()
    elif _is_archive_purpose_question(q):
        answer = _archive_purpose_recovery()
    elif _is_commons_care_question(q):
        answer = _commons_care_recovery()
    elif _is_feedback_loops_institutions_question(q):
        answer = _feedback_loops_institutions_recovery()
    elif _is_systems_explanation_vs_simplistic_connection_question(q):
        answer = _systems_explanation_vs_simplistic_connection_recovery()
    elif _is_humane_performance_question(q):
        answer = _humane_performance_recovery()
    elif _is_stewardship_leadership_crisis_question(q):
        answer = _stewardship_leadership_crisis_recovery()
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
    # Ethical conflicts must outrank generic "how" / practical-action patterns.
    elif _is_ethical_tradeoff(q):
        if re.search(r"\bstewardship\b", lower) and re.search(r"\b(?:disagree|protect)\w*\b", lower):
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
            answer = (
                "Leaders can hold competing stakeholder obligations by treating them as responsibilities to weigh openly, not as a contest in which one group must automatically win. Start by naming each obligation, the people who depend on it, and the legitimate interests or rights at stake. Separate commitments that must be honored from preferences that can be negotiated, and make any real conflict explicit rather than promising everyone everything.\n\n"
                "Then compare the consequences of realistic options: who benefits, who carries the cost, what harm may be irreversible, and whether people affected have had a meaningful chance to be heard. Apply consistent criteria such as duty, fairness, evidence, proportionality, and long-term effects. Where one obligation must take priority, explain why that criterion applies and look for ways to reduce or repair the burden placed on others.\n\n"
                "No decision will always satisfy every stakeholder, and equal consideration does not mean identical outcomes. Responsible leadership means giving each obligation a fair hearing, being transparent about trade-offs, refusing to shift costs onto people with less power merely because they are easier to ignore, and revisiting the decision when evidence or circumstances change. Trust grows when people can see both the reasoning and the accountability behind a difficult choice."
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
        answer = _significance_recovery(significance_subject, significance_context)
    elif re.search(r"\b(?:why|what causes|reason for)\b", lower):
        answer = (
            f"The most useful explanation for why {subject} begins by distinguishing the immediate event from the conditions that made it more likely. "
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
    elif re.search(r"\b(?:how|steps|approach|what can i do|what should we do|how to)\b", lower):
        answer = (
            f"For a question like {subject}, the first task is to make the decision visible. "
            "What outcome is the organisation trying to achieve, what responsibilities does it carry, and who will live with the consequences? "
            "Those questions bring operations, governance, human development, ethics, and stewardship into the same frame without pretending they are separate problems.\n\n"
            "From there, compare the real options rather than assuming that the proposed course is the only one. "
            "Look at what each option makes possible, what it may damage, who bears the costs, and what evidence would justify changing direction. "
            "The knowledge of people affected by the decision belongs in that assessment, especially where they will carry consequences they did not choose.\n\n"
            "The point is not to make the decision for the organisation, but to make the grounds for acting clearer. "
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

    movement = _clean(desired_movement)
    if movement and not is_harm_repair_question(q) and not _is_ethical_tradeoff(q) and not _is_hindsight_accountability(q):
        answer += f" A sensible next step is to focus on {movement.rstrip('.')}."
    # A generic clarifier is not an acceptable default ending for a question
    # that reached recovery with a concrete subject. The separate request-boundary
    # classifier remains responsible for genuinely missing subjects.
    return answer


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
        "question_shapes": ["hindsight_accountability", "ethical_tradeoff", "comparison", "causal", "decision", "practical", "definition", "reflective", "general"],
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
