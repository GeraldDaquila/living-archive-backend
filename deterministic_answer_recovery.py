def _regeneration_participation_recovery():
    """Translate spiritual interest into grounded, voluntary regenerative practice."""
    return (
        "Regeneration becomes participation when insight turns into responsible care for something real: a relationship, community, shared resource, institution, place, or living system. The question is not simply what resonates with you, but what is already entrusted to your care—and where your contribution can help something become healthier, more capable, or more whole.\n\n"
        "1. EXISTING RESPONSIBILITY — Begin with what is already yours to tend. This may arise through a real relationship, role, commitment, or shared undertaking. Ask whether it needs repair, attention, or more capable care. This is the strongest starting point because it rests on an actual relationship and responsibility, not an imagined assignment.\n\n"
        "2. EMERGING OPPORTUNITY — Notice a genuine need where your abilities may help. Before offering a solution, listen. The people affected should help define the problem, say whether your contribution is welcome, and shape what helpful participation would look like. An opportunity becomes a responsible invitation through relationship and consent, not through your impression alone.\n\n"
        "3. PREMATURE OR UNSUPPORTED INVITATION — Pause when an appealing impression is not matched by a sufficiently understood need, a legitimate relationship, the affected people's consent, or the capacity to contribute responsibly. The appropriate response is listening and patience, not immediate action. These are three different grounds for action, not spiritual labels to assign yourself.\n\n"
        "A practical first move: choose one living context you already belong to. Ask what needs tending, who should help define the need, what you can responsibly contribute, and what feedback would show whether it is helping. If no existing responsibility is apparent, explore an emerging opportunity by listening before offering a solution. Take one proportionate, reversible step only when the need and your role are clear enough; remain answerable to the people affected and revise your contribution as its effects become clearer. You do not need to treat every spiritual impression as a command or prove that a supernatural invitation has occurred. Let the quality of participation—not the amount of content consumed or the intensity of a feeling—be the test."
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


def _trust_community_stewardship_recovery():
    """Explain trust as enabling infrastructure for accountable shared care."""
    return (
        "Trust helps people in a community rely on one another without having to supervise every small act. It makes cooperation possible: people can share knowledge, coordinate work, honor commitments, and accept some vulnerability because they have reason to expect competence, consistency, fairness, and reciprocity. Trust is therefore more than a warm feeling between individuals; it is part of the social infrastructure that allows a community to act together.\n\n"
        "Think of a shared garden. The soil, water, tools, and harvest are common concerns, but no one person can tend every bed or watch every action. People need confidence that others will contribute, that decisions about water and harvest will be fair, and that problems can be raised without punishment. Stewardship is tending the garden together: caring for what is shared, noticing what is being depleted, and making sure the conditions for future growth are not sacrificed for an immediate private gain.\n\n"
        "That trust must not be blind. It is earned and renewed through observable practices: capable work, kept commitments, transparent decisions, fair distribution of costs and benefits, accountability when mistakes happen, and meaningful ways for affected people to question and correct decisions. Without those safeguards, calls for trust can shield power from scrutiny; without enough trust, even good plans become harder to coordinate. The practical test is whether people can cooperate while remaining free to ask questions, disagree, and repair what is not working."
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


def has_registered_recovery(question):
    """True only when a bounded deterministic recovery is explicitly registered."""
    return bool(
        is_guide_personal_decision_agency_question(question)
        or is_interpretation_revision_evidence_question(question)
        or is_resonance_confirmation_bias_question(question)
        or is_oversoul_ego_authority_question(question)
        or is_external_discernment_outsourcing_question(question)
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
        or _is_general_explanatory_question(question)
        or _is_modes_of_knowing_dialogue_question(question)
        or is_stewardship_failure_repair_question(question)
        or is_community_continuity_revision_question(question)
        or is_community_project_tradeoff_question(question)
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
    if is_interpretation_revision_evidence_question(question):
        return {
            "title": "Seeing Patterns Without Fooling Yourself",
            "url": "https://geralddaquila.com/2026/04/06/seeing-patterns-without-fooling-yourself/",
            "rationale": (
                "This essay offers a practical way to examine whether a perceived pattern is supported or projected: repeatability, plausible mechanism, constraints, and disconfirmation. It is a method for testing an interpretation, not independent proof for or against a spiritual claim."
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
    if is_regeneration_participation_question(question):
        return {
            "title": "Stewardship as Human Maturity",
            "url": "https://geralddaquila.com/2026/07/06/stewardship-as-human-maturity/",
            "rationale": "This published cornerstone traces the movement from self-development toward responsibility and contribution beyond the self. It asks what has been entrusted to a person's care and describes stewardship as participation in relationships, communities, institutions, ecosystems, and generations; it is a grounded continuation from spiritual inspiration toward lived responsibility, not a claim about a supernatural calling."
        }
    if is_trust_community_stewardship_question(question):
        return {
            "title": "Trust Architecture: The Missing Infrastructure Behind Functional Societies",
            "url": "https://geralddaquila.com/2026/09/07/trust-architecture-the-missing-infrastructure-behind-functional-societies/",
            "rationale": "This published essay explains trust as social infrastructure: it enables coordination, reduces the costs of cooperation, supports institutional legitimacy, and depends on competence, consistency, transparency, accountability, reciprocity, and fairness. It is a direct continuation for understanding trust in shared community stewardship."
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

def compose_recovery(question, *, underlying_question="", desired_movement=""):
    """Offer a useful bounded response without inventing facts or sources."""
    q = _clean(question)
    if not q:
        return "What would you like to understand or work through?"
    subject = _clean(underlying_question) or _subject(q)
    lower = q.casefold()

    # Belief/interpretation revision questions need a proportionate, claim-sensitive evidence standard.
    if is_interpretation_revision_evidence_question(q):
        return _interpretation_revision_evidence_recovery()

    # Evidence-discernment questions must not fall through to generic reflection.
    if is_resonance_confirmation_bias_question(q):
        return _resonance_confirmation_bias_recovery()

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
        answer = _significance_recovery(
            significance_subject,
            significance_context.rstrip(" ?.!;:"),
        )
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
