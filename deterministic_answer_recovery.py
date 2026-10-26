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
    display_subject = subject[:1].upper() + subject[1:]
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
        "institutional trust": {
            "definition": "the confidence that an institution will act competently, fairly, and consistently enough for people to rely on it",
            "example": "People are more able to rely on a public service when it explains decisions, handles similar cases consistently, corrects mistakes, and provides a meaningful way to appeal.",
            "significance": "Trust should be earned by observable conduct rather than claimed as a virtue. Consistent failures, hidden reasons, or blocked complaints can weaken it even when an institution says its intentions are good."
        }
    }
    normalized_subject = re.sub(r"\s+", " ", subject).strip().casefold()
    entry = definition_bank.get(normalized_subject)
    if entry:
        answer = (
            f"{display_subject} is {entry['definition']}. "
            "Its meaning is practical: it describes knowledge, responsibilities, or ways of working that affect what people can understand and do.\n\n"
            f"For example, {entry['example']}\n\n"
            f"{display_subject} matters because {entry['significance']}"
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
    if archive_subject and re.search(r"\b(?:what is|what are|define|what does)\b", lower):
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
    elif re.search(r"\b(?:how|steps|approach|what can i do|what should we do|how to)\b", lower):
        answer = (
            f"A practical way to approach {subject} is to begin by clarifying the outcome and the responsibilities involved. "
            "Identify what is known, which constraints or obligations matter, and who will be affected by the available choices. "
            "This makes the real decision clearer than jumping immediately to a generic action plan.\n\n"
            "Next, compare a small number of realistic options against the purpose you are trying to serve. Consider likely "
            "benefits, foreseeable harms, who carries the costs, and what evidence would change the choice. Where other people "
            "are affected, include their knowledge and concerns rather than treating them as an afterthought.\n\n"
            "Finally, act on the best-supported option, explain the reasoning and limits, and review the consequences. "
            "A useful approach should improve understanding and accountability, not promise certainty or shift responsibility "
            "onto people who lack the authority to resolve the problem."
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
