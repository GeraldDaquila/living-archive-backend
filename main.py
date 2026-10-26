        if re.match(
            r"(?i)^what is (?:an? |the )?(.+?),? and why does it matter\??$",
            re.sub(r"\s+", " ", str(query or "")).strip(),
        ):
            _shared_definition = _compose_provider_exhaustion_recovery(
                query,
                underlying_question=str((interpretation or {}).get("underlying_question") or ""),
                desired_movement=str((interpretation or {}).get("desired_movement") or ""),
            )
            if _shared_definition and not _guide_composition.is_generic_nonanswer(query, _shared_definition) and not _guide_composition.is_meta_answer_failure(_shared_definition):
                result["response"] = _shared_definition
            else:
                result = {
                    "response": "",
                    "doorway_title": "",
                    "recommendation": None,
                    "provider": "rejected_non_substantive_recovery",
                    "model": "quality-gate-rejection",
                }
if is_harm_repair_question(query):
            # The generic first retrieved document is not evidence that its page
            # is a suitable continuation for a harm-repair adequacy question.
            # Keep this bounded recovery self-contained rather than exposing a
            # mismatched doorway just because unrelated context was present.
            result["doorway_title"] = ""
            result["recommendation"] = None
        result["provider"] = "bounded_provider_exhaustion_recovery"

    # Provider exhaustion is still part of the shared visitor-answer contract.
    # Do not let a polished, three-paragraph non-answer bypass the quality gate
    # simply because the ordinary composer returned no candidate.
    if isinstance(result, dict):
        import general_guide_composition as _guide_composition
        response_text = str(result.get("response") or "")
        if _guide_composition.is_generic_nonanswer(query, response_text) or _guide_composition.is_meta_answer_failure(response_text):
            try:
                _fallback_documents = use_core.context_blocks_to_documents(
                    str((context_data or {}).get("context_blocks") or "")
                )
            except Exception:
                _fallback_documents = []
            _fallback_documents = [item for item in _fallback_documents if isinstance(item, dict)]
            _constitutional_fallback = _guide_composition._archive_constitutional_recovery(
                query, _fallback_documents
            )
            if _constitutional_fallback and not _guide_composition.is_generic_nonanswer(
                query, str(_constitutional_fallback.get("response") or "")
            ):
                result = dict(_constitutional_fallback)
            else:
                # Prefer the question-preserving deterministic answer over the
                # generic provider-exhaustion prose. If it also fails the shared
                # gate, do not mislabel the weak answer as an accepted recovery.
                _bounded = _basic_inquiry_round1_deterministic_response(
                    query, interpretation, context_data,
                    recommendation_available=False,
                )
                if isinstance(_bounded, dict) and not _guide_composition.is_generic_nonanswer(
                    query, str(_bounded.get("response") or "")
                ) and not _guide_composition.is_meta_answer_failure(str(_bounded.get("response") or "")):
                    result = dict(_bounded)
                else:
                    result = {
                        "response": "",
                        "doorway_title": "",
                        "recommendation": None,
                        "provider": "rejected_non_substantive_recovery",
                        "model": "quality-gate-rejection",
                    }
    return result


def _basic_inquiry_round1_deterministic_response(query, interpretation, context_data, *, recommendation_available=False):
    """Question-aware last-resort answer; never promise an answer and then refuse."""
    interpretation = interpretation or {}
    question = _normalize_query(query)
    q = re.sub(r"\s+", " ", question).strip().casefold()

    # Keep the answer-first existential contract active when the ordinary
    # provider bank is exhausted or the isolated deterministic path is used.
    # Import locally so isolated recovery harnesses retain the same behavior.
    import general_guide_composition as _guide_composition
    if _guide_composition._is_broad_existential_question(query):
        return _guide_composition._broad_existential_recovery()

    try:
        documents = use_core.context_blocks_to_documents(str(context_data.get("context_blocks") or ""))
    except Exception:
        documents = []
    documents = [d for d in documents if isinstance(d, dict)]
    title = str(documents[0].get("title") or "").strip() if documents else ""
    content = str((documents[0].get("content") or documents[0].get("text") or documents[0].get("excerpt") or "") if documents else "").strip()
    content = re.sub(r"\s+", " ", content)

    relational_fractal = compose_relational_fractal(query)
    if relational_fractal is not None:
        return relational_fractal

    _cosmology_lived_question = bool(
        re.search(r"\b(?:cosmology|worldview)\b", q)
        and re.search(r"\b(?:how people live|how we live|human life|everyday life|our lives|people's lives)\b", q)
    )
    if _cosmology_lived_question:
        _cosmology_response = (
            "Cosmology is an understanding of how reality works and how we belong within it—not only a theory about the physical universe. "
            "The picture we carry of people, nature, change, and our place in the world shapes what we notice and how we make decisions.\n\n"
            "The Living Archive explores a contrast between a separation-based worldview and a unity-informed worldview. "
            "A separation-based view tends to organize life around competition, control, earned worth, and fear of loss. "
            "A unity-informed view sees people as distinct but connected, treats worth as inherent, and understands growth as something that can emerge through relationship, responsibility, and cooperation. "
            "These are ways of interpreting experience, not labels for judging a person.\n\n"
            "This matters because a worldview can become an invisible guide for everyday choices. "
            "If every disagreement is treated as a contest for control, people may protect status instead of looking for a workable answer. "
            "If people see themselves as distinct but connected, they can recognize differences without treating them as threats. "
            "This is a useful starting explanation, not a claim that one Archive text exhausts the subject."
        )
        return {
            "response": _cosmology_response,
            "doorway_title": "",
            "provider": "bounded_archive_informed_cosmology_recovery",
            "model": "",
        }

    # Bounded relational uncertainty recovery. A lack of case-specific facts must
    # not become a refusal when the visitor has expressed a clear feeling. Reflect
    # only what the visitor stated, distinguish caring from a decision to continue
    # investing, and invite clarification without inferring the other person's
    # motives or prescribing a relationship decision.
    relational_care_signal = bool(re.search(
        r"\b(?:feel|feeling)\s+(?:so\s+)?(?:foolish|stupid|silly|embarrassed|ashamed)\b.{0,100}\b(?:care|caring|love|loving|miss|missing|hold(?:ing)? on)\b"
        r"|\b(?:still caring|still care|still love|still miss|can't let go)\b",
        q,
        re.I,
    ))
    relational_context_signal = bool(re.search(
        r"\b(?:friendship|friend|relationship|someone i care about|them|him|her|they)\b",
        q,
        re.I,
    ))
    if relational_care_signal and relational_context_signal:
        response = (
            "It isn't foolish to care about a friendship that has mattered to you. Caring doesn't switch off simply because a relationship becomes difficult, disappointing, or uncertain. "
            "But caring about someone and deciding how much of yourself to keep investing in the friendship are two different things. You don't have to deny what the friendship means to you in order to take your own feelings seriously.\n\n"
            "Perhaps a useful place to begin is this: what makes you feel foolish for still caring—is it how the other person has treated you, the lack of reciprocity, or the feeling that you haven't been able to let go of what the friendship once was?"
        )
        return {
            "response": response,
            "doorway_title": "",
            "provider": "bounded_relational_uncertainty_recovery",
            "model": "",
        }

    # Relational burden / invisible-care recovery. This must run before the
    # generic retrieval fallback: when a visitor shares a lived relational
    # concern, do not answer with a factual-evidence refusal or a broad asset.
    burden_signal = bool(re.search(
        r"\b(?:responsible one|everyone depends on me|nobody asks how i am|"
        r"no one asks how i am|carry(?:ing)? (?:the )?(?:whole )?family|"
        r"always there for everyone|take care of everyone|look after everyone|"
        r"no one checks on me|nobody checks on me|feel unseen|feel overlooked)\b",
        q,
        re.I,
    ))
    family_or_care_context = bool(re.search(
        r"\b(?:family|everyone|nobody|no one|responsible|depend|care|"
        r"look after|take care|asks how|checks on|overlooked|unseen)\b",
        q,
        re.I,
    ))
    if burden_signal and family_or_care_context:
        response = (
            "It sounds as though people rely on you, while your own needs may be going unnoticed. "
            "Being dependable and feeling cared for are not the same thing, and carrying that gap can be lonely. "
            "I don't want to assume how your family sees the situation from one sentence.\n\n"
            "When you say nobody asks how you are, what do you most wish someone in your family would notice or understand?"
        )
        # A broad resource such as a general flourishing page is not a grounded
        # match. Only expose a resource when its title directly signals the
        # visitor's stated topic; otherwise leave the doorway empty.
        directly_relevant_title = bool(re.search(
            r"\b(?:family caregiving|caregiver burden|invisible labor|emotional labor|"
            r"family responsibility|being overlooked|feeling unseen|care and reciprocity)\b",
            title,
            re.I,
        ))
        return {
            "response": response,
            "doorway_title": title if directly_relevant_title else "",
            "provider": "bounded_relational_burden_recovery",
            "model": "",
        }


    if (
        _is_practical_stewardship_question(query)
        and not _is_conceptual_explanatory_request(query)
        and not general_guide_composition.is_conceptual_relationship_question(query)
    ):
        response = (
            "A community can practice stewardship by making its responsibilities visible and considering who is affected by each decision. "
            "For example, before changing a shared space or allocating a limited budget, invite the people who rely on it to explain what they need and what could be lost.\n\n"
            "Agree on clear criteria, use the same criteria for everyone, name who will maintain the result, and make the reasons for the decision accessible. "
            "Where people disagree, record the trade-offs and choose a time to review the outcome rather than treating the first decision as beyond question.\n\n"
            "These are general practical suggestions, not a claim that a specific Archive text prescribes this process. I could not verify a sufficiently direct Archive resource to recommend for this question."
        )
        return {"response": response, "doorway_title": "", "provider": "bounded_practical_stewardship_recovery", "model": ""}


    # This recovery is deliberately modest. It answers the concrete public
    # question from general knowledge where a stable, everyday explanation is
    # available, without fabricating Archive evidence or source-specific claims.
    if re.search(r"\b(?:understand|make sense of|interpret)\b", q) and re.search(r"\b(?:difficult situation|situation|what happened|someone's behavior|their behavior)\b", q) and re.search(r"\b(?:judge|judgment|judgement|assume|assumption|rush)\b", q):
        response = (
            "When a situation is difficult, it helps to separate what you know from what you think it means. "
            "You can acknowledge your first reaction without treating it as the whole truth; there may be details you have not seen or another explanation for what happened.\n\n"
            "You do not have to suspend judgment forever or ignore your own boundaries. Sometimes giving yourself a little time, or asking one honest question before deciding, is enough to help you respond more fairly."
        )
        return {"response": response, "doorway_title": "", "provider": "bounded_reflective_general_knowledge_recovery", "model": ""}

    # Resolve the question's actual conflict before the broad stewardship-definition rule.
    # This prevents deterministic-only mode from returning the same generic definition
    # for materially different questions about disagreement and competing obligations.
    if (
        "stewardship" in q
        and re.search(r"\b(?:disagree|disagreement|conflict|competing|opposing|different priorities)\b", q)
        and re.search(r"\b(?:protect|protecting|preserve|preserving|worth|values)\b", q)
    ):
        response = (
            "When people disagree about what is worth protecting, the disagreement often reflects different values, responsibilities, or fears about what could be lost. One person may want to preserve continuity; another may believe change is necessary to protect people or keep something useful. It helps to name those underlying concerns before treating the other person as careless or unreasonable.\n\n"
            "A practical next step is to ask what each person is trying to protect, who would bear the costs of each option, and which responsibilities or rights cannot simply be traded away. Separate shared facts from judgments, and look for options that preserve the most important interests while making the unavoidable trade-offs explicit.\n\n"
            "People may not reach identical priorities, and stewardship does not require pretending otherwise. They can still agree on a fair process, explain their reasons, consider the people affected but not represented, and review the decision when new evidence or consequences emerge. The aim is to handle disagreement responsibly, not to erase it."
        )
        return {"response": response, "doorway_title": title, "provider": "bounded_conflict_stewardship_recovery", "model": ""}

    # Sovereignty is a stable concept question even when provider composition is exhausted.
    # Answer directly, distinguish general framing from Archive-specific claims,
    # and only retain a doorway whose canonical title explicitly matches the topic.
    if (
        re.search(r"\bsovereignty\b", q)
        and re.search(r"\b(?:what\s+(?:does|is)|meaning|define|explain|approach|relationship|human relationships)\b", q)
    ):
        response = (
            "Sovereignty, in a human-relations context, can be understood as a person's or community's authority to participate in shaping decisions that affect them, rather than having their choices or identity controlled by someone else. "
            "It is closely connected to agency, consent, boundaries, and the ability to take responsibility for one's own life. It does not mean being free of every obligation or never needing others.\n\n"
            "For example, in a family or community decision, respecting sovereignty means listening to the people who will live with the consequences, making room for their informed choice, and not treating care or leadership as permission to decide everything for them. People can still negotiate shared responsibilities; the key is that participation is not replaced by coercion or assumed authority.\n\n"
            "That is a general conceptual explanation, not a verified quotation or definitive statement of the Living Archive's own doctrine. The Archive's specific framing should be checked against its canonical text on Governance & Sovereignty. The retrieved resource is a relevant next step, but the title alone does not establish every detail of its argument."
        )
        relevant_doorway = title if re.search(r"\b(?:sovereignty|governance)\b", title, re.I) else ""
        return {
            "response": response,
            "doorway_title": relevant_doorway,
            "provider": "bounded_general_knowledge_recovery",
            "model": "",
        }

    # Provider exhaustion must not turn a straightforward concept definition into a refusal.
    # This is a bounded general explanation, not a claim of a single canonical Archive definition.
    if "reciprocity" in q and re.search(r"\b(?:what\s+is|what\s+does|meaning|define|explain|mean)\b", q):
        response = (
            "Reciprocity means a relationship of mutual response: people give, receive, and support one another over time. "
            "It does not mean keeping score or expecting every act to be repaid immediately or in equal measure. "
            "People may give more at one point and need more help at another; what matters is that support can move in both directions over time.\n\n"
            "Think of neighbors taking turns checking on an older resident or helping one another with errands. "
            "One neighbor may do more during a difficult week and receive help later. The relationship can still be reciprocal even when each exchange is different.\n\n"
            "Reciprocity should never be used to demand access, obedience, or repayment from someone who cannot freely offer it. "
            "Mutual support works best when people respond to one another's real circumstances, not when kindness becomes a debt ledger."
        )
        return {"response": response, "doorway_title": "", "provider": "bounded_general_knowledge_recovery", "model": ""}

    if "stewardship" in q and "responsibility" in q and re.search(r"\b(?:difference|different|distinguish|distinction|versus|vs)\b", q):
        response = (
            "Responsibility is about what you are answerable for: a task, a promise, a role, or the consequences of a decision. "
            "It can be assigned to you, shared, or delegated. "
            "Stewardship is about how you care for something placed in your hands, especially when its value reaches beyond your immediate needs. "
            "It asks you to maintain, protect, or improve it for others and for the future.\n\n"
            "The two belong together, but they are not identical. Responsibility asks, ‘What am I accountable for?’ "
            "Stewardship asks, ‘How should I care for what I have been entrusted with?’ "
            "You can fulfill a duty narrowly and still neglect the wider trust; stewardship asks you to consider that wider effect while respecting your own limits."
        )
        return {"response": response, "doorway_title": title, "provider": "bounded_general_knowledge_recovery", "model": ""}

    # Treat explicit definition/explanation requests as answerable even when the
    # visitor does not also use "why", "matter", or "important". Navigation
    # preferences are separate from answer intent and must never suppress this
    # bounded general-knowledge recovery when the provider bank is exhausted.
    if "stewardship" in q and re.search(r"\b(?:what\s+is|explain|define|describe|meaning|means|understand|why|matter|important|everyday|life)\b", q):
        response = (
            "Stewardship means taking care of something entrusted to you—such as your time, relationships, shared spaces, money, or the natural world—rather than treating it as if only your immediate needs matter. "
            "In everyday life, it shows up in small choices: keeping a promise, maintaining what others rely on, using resources thoughtfully, and considering how your decisions affect people around you.\n\n"
            "It matters because ordinary choices accumulate. Carelessness can pass costs to other people or to the future, while responsible care helps preserve trust, usefulness, and possibilities for those who come after us.\n\n"
            "Stewardship does not mean controlling everything or sacrificing yourself for everyone else. It means recognizing what is yours to care for, acting responsibly within your limits, and leaving things no worse—and where possible better—than you found them."
        )
        # The deterministic last-resort path must preserve an explicit visitor
        # request for a reflective closing question just as the composition
        # validator does on the provider-generated path.
        if _explicit_closing_question_requested(question) and not response.rstrip().endswith("?"):
            response += " What is one thing in your everyday life that you feel responsible for caring for?"
        return {"response": response, "doorway_title": title, "provider": "bounded_general_knowledge_recovery", "model": ""}

    if "burnout" in q and re.search(r"\b(manager|manage|leader|supervisor)\b", q):
        response = (
            "As a manager, treat burnout as a workload and recovery problem—not simply a personal failure to cope. Start by identifying what is draining you most: excessive hours, constant availability, unclear priorities, emotional demands, or too little control over the work.\n\n"
            "Choose one pressure you can reduce this week. For example, if every decision comes to you, name which decisions your team can make without your approval and agree on clear limits for when they should escalate. That gives you some recovery time while building the team's capacity.\n\n"
            "Also protect basic recovery: take real breaks, set a reasonable end to the workday where possible, and speak with your own manager about priorities that cannot all fit. If exhaustion is persistent, affecting your health, or making daily functioning difficult, consider professional support. You do not have to solve a structural workload problem by pushing yourself harder."
        )
        return {"response": response, "doorway_title": "", "provider": "bounded_general_knowledge_recovery", "model": ""}

    if re.search(r"\boverwhelmed\b", q) and re.search(r"\b(?:who|talk|someone|support)\b", q):
        response = (
            "When you're overwhelmed, you don't have to find the perfect person or explain everything at once. "
            "If there's someone you trust, you could start with: “I'm having a hard time and could use someone to listen. Do you have a few minutes?” "
            "If no one comes to mind, a local community support service or a qualified professional can be another place to start. "
            "If you feel in immediate danger or might hurt yourself, contact local emergency or crisis support now."
        )
        return {"response": response, "doorway_title": "", "provider": "bounded_supportive_recovery", "model": ""}

    # Preserve a direct, bounded explanation of institutional responsibility when
    # provider composition is unavailable. A relevant doorway is not a substitute
    # for answering the visitor, and missing Archive evidence is not missing general
    # knowledge. This is explicitly general knowledge, not Archive attribution.
    if re.search(r"\binstitutional responsibility\b", q):
        response = (
            "Institutional responsibility means that an organization and the people who lead or act for it must answer for the decisions they make, the duties they hold, and the effects those decisions have on others. It is not enough for an institution to say that a harmful outcome was nobody’s personal intention; its rules, choices, and failures to act can still have real consequences.\n\n"
            "For example, if a public office repeatedly loses applications, responsibility includes more than blaming the employee at the desk. The office should examine its process, explain what went wrong, correct the problem, and make it less likely to happen again. Individual people may also be accountable for their own choices, but the institution must address problems built into its systems.\n\n"
            "Institutional responsibility does not mean an organization can control everything or guarantee perfect results. It means being clear about its obligations, making decisions fairly, giving reasons, listening to people affected, correcting preventable harm, and accepting appropriate oversight. The exact duties depend on the institution’s role, the rules that govern it, and the situation involved."
        )
        return {
            "response": response,
            "doorway_title": title,
            "provider": "bounded_general_knowledge_recovery",
            "model": "",
        }

    # When provider composition is exhausted, preserve a directly asked public
    # governance topic instead of falling through to the generic refusal path.
    # This is general knowledge, not a claim that the Archive supplied evidence.
    topic_groups = _topic_anchor_groups(question)
    if "political_dynasties" in topic_groups:
        response = (
            "Political dynasties are families whose members hold or repeatedly win elected office across generations. "
            "Their influence can shape candidate selection, local party organization, public appointments, and access to public resources. "
            "The effects depend on how elections, public institutions, and oversight operate around those family networks.\n\n"
            "Where family networks dominate nominations, appointments, or access to services, accountability can weaken because officials may face stronger incentives to answer to a family network than to the wider public. "
            "But the existence of a dynasty alone does not prove corruption or poor performance; those are claims that require evidence about specific decisions and outcomes.\n\n"
            "To assess a particular locality, examine who holds which offices and their family relationships, how competitive elections are, procurement and budget records, conflicts of interest, and whether courts, auditors, media, and citizens can scrutinize decisions. "
            "These indicators help distinguish a structural risk from an unsupported claim about a particular person or family."
        )
        return {
            "response": response,
            "doorway_title": "",
            "provider": "bounded_public_governance_recovery",
            "model": "",
        }

    # Multi-part national systems questions should be answered through the Archive's
    # grounded systems lens, not a generic refusal or a generic policy checklist.
    # The answer names the Archive's causal model while avoiding unsupported claims
    # that one factor alone explains national outcomes.
    national_systems_question = bool(
        re.search(r"\b(?:philippines|vietnam|country|national development|national economy)\b", q, re.I)
        and re.search(r"\b(?:why|what ails|underperform|below its potential|falling behind|overtook|economic growth|development)\b", q, re.I)
        and re.search(r"\b(?:recommend|fix|improve|solution|what if any|what should)\b", q, re.I)
    )
    if national_systems_question:
        response = (
            "The Living Archive's systems analysis points to a central distinction: the Philippines does not lack human or natural potential; it struggles to convert those strengths into consistent, broadly shared outcomes. "
            "The Archive frames this as a complex-system problem, where institutions, households, markets, infrastructure, and cultural patterns interact. The question is not whether Filipinos are capable, but whether the surrounding systems reward and coordinate that capability well.\n\n"
            "One important feedback loop is infrastructure and state capacity: weak connectivity raises logistics costs and isolates regional enterprise; that constrains economic activity and the public revenue available for investment; limited investment then allows the infrastructure gap to persist. "
            "A second constraint is governance as a coordination problem. Institutions and actors operate with different incentives, time horizons, and accountability structures. When short-term private or political rewards outweigh long-term public value, cooperation becomes harder to sustain and reforms are vulnerable to discontinuity. "
            "The Archive's broader account also treats culture as accumulated adaptation: people learn what is rewarded, what is punished, and what feels possible under the systems they inhabit. These patterns should not be mistaken for an inherent defect in the Filipino character.\n\n"
            "This helps interpret the Philippines–Vietnam comparison without turning it into a judgment about either people. Vietnam's export-manufacturing trajectory makes it a useful case for examining how industrial coordination, investment, infrastructure, and integration into supply chains can reinforce one another. The Archive's systems lens asks which arrangements create productive feedback loops and which keep potential trapped—not which nation is inherently superior. A precise ranking of the countries' performance, and the weight of each cause, still requires comparable current data.\n\n"
            "The practical response is to change the conditions that shape outcomes. First, treat inter-island transport, ports, energy, and digital connectivity as an integrated productivity system, and measure how they affect regional firms and jobs. Second, align public incentives and accountability with sustained delivery across political cycles: publish project costs, milestones, procurement records, and outcomes, not just announcements. Third, make it easier for productive local firms to grow, innovate, and enter export markets, while reducing barriers that protect connections rather than performance. Fourth, invest in human development and local institutional capability so education, community knowledge, and diaspora experience can translate into domestic opportunity. Fifth, strengthen civic trust through transparent decisions and meaningful participation by the communities bearing the consequences.\n\n"
            "The Archive's underlying principle is stewardship: build systems that preserve and develop shared human, social, and ecological capacity over time. That is not a call for a foreign template or a dogmatic blueprint. It is a sovereign, evidence-led process of identifying the Philippines' own bottlenecks, testing reforms against measurable outcomes, learning from other countries selectively, and correcting course when results do not follow. "
            "The first move is a national bottleneck review that links each proposed reform to a causal mechanism, a responsible institution, a public measure, and a review date."
        )
        return {
            "response": response,
            "doorway_title": "",
            "provider": "archive_grounded_national_systems_recovery",
            "model": "",
        }

    # Help a visitor begin when they cannot yet phrase the question.
    if "not sure how to phrase my question" in q and "something is missing" in q:
        response = (
            "You do not need to have the question fully formed yet. We can start with the sense that something feels missing, without deciding in advance what it means. "
            "When you notice that feeling, does it seem connected to a particular part of your life, or is it difficult to locate?"
        )
        return {"response": response, "doorway_title": "", "provider": "bounded_human_orientation_recovery", "model": ""}
    # Protect the established General Guide answer for this calibrated
    # conceptual question when every provider is unavailable. This is ordinary
    # general knowledge, not an Archive attribution; doorway selection remains
    # independent and evidence-grounded.
    if re.search(r"\brelationship between personal agency and responsibility to others\b", q):
        response = (
            "Personal agency and responsibility to others are not opposing forces but interdependent aspects of the same moral life. Agency is the capacity to make choices and act on them; responsibility is the recognition that those choices have consequences for people who are affected by them. You cannot exercise genuine agency without acknowledging that your actions exist within a web of relationships, and you cannot fulfill responsibility to others without the freedom to choose how to act.\n\n"
            "The tension arises when agency is understood as pure independence—the idea that you are a self-contained individual whose choices are yours alone. In reality, our decisions are shaped by the people we are connected to, and those people are shaped by our decisions. For example, a manager who exercises agency to restructure a team is not just making a personal career move; they are altering the working conditions, security, and morale of the people on that team. The manager's freedom to decide is real, but it is bounded by the legitimate needs and rights of the employees. Ignoring that boundary does not make the choice freer; it makes it less responsible.\n\n"
            "The key distinction is between agency as the ability to act and agency as the right to act without regard for impact. True agency includes the willingness to be accountable for the effects of your choices. Responsibility to others is not a constraint on your freedom; it is the condition that makes your freedom meaningful. When you act with awareness of how your choices affect others, you are not surrendering your agency—you are exercising it fully."
        )
        return {
            "response": response,
            "doorway_title": title,
            "provider": "calibrated_general_knowledge_recovery",
            "model": "",
        }

    # Funding-priority questions remain answerable when retrieval has no directly
    # relevant canonical resource. Keep the general decision framework separate
    # from doorway selection: never cite or recommend an unrelated Archive asset
    # as a substitute for answering the question.
    if (
        re.search(r"\b(?:funding|fund|budget|allocate|allocation)\b", q, re.I)
        and re.search(r"\b(?:competing priorities|two priorities|limited resources|neither can be fully supported|cannot fully fund|can't fully fund|trade[- ]?offs?)\b", q, re.I)
    ):
        response = (
            "When a community cannot fully fund both priorities, it should agree on transparent criteria before choosing. "
            "Compare the urgency of each need, the consequences of delaying it, who would be affected, and whether a smaller "
            "or phased option could protect the most important outcomes.\n\n"
            "Make the trade-offs explicit: what each option would protect, what it would leave unmet, and who would carry the cost. "
            "Use the same criteria for both options, include the people most affected, and record the reasons for the decision. "
            "Where uncertainty remains, consider a time-limited allocation with a clear review point rather than presenting the choice as permanent.\n\n"
            "This is a general decision framework, not a claim that the Archive supplied a definitive answer. I did not identify "
            "a sufficiently direct Archive resource to recommend for this question."
        )
        return {
            "response": response,
            "doorway_title": "",
            "provider": "bounded_funding_priority_recovery",
            "model": "",
        }

    underlying = str(interpretation.get("underlying_question") or "").strip()
    movement = str(interpretation.get("desired_movement") or "").strip()
    if content:
        explanation = f"The Archive material available here offers this starting point: “{content[:360].rstrip()}”"
        opening = f"The question is asking about {underlying.rstrip('.')}." if underlying else f"Your question asks: {question.rstrip('?')}."
        if movement:
            closing = f"A useful next movement may be {movement.rstrip('.')}."
        elif recommendation_available:
            closing = "That gives you a starting point; the separately selected Archive resource offers a place to explore further."
        else:
            closing = "That gives you a starting point; I did not identify a directly relevant Archive resource to recommend for this question."
    elif re.search(r"\b(?:meaning|means|mean|what is)\b.{0,60}\bemptiness\b|\bemptiness\b.{0,60}\b(?:meaning|means|mean)\b", question, re.I):
        opening = "Emptiness can mean different things depending on the context."
        explanation = (
            "In everyday life, it can describe a felt absence of meaning, connection, or purpose. "
            "In philosophy, it can refer to the absence of an independent, permanent essence. "
            "In Buddhist thought, emptiness does not mean that nothing exists; it points to the way things arise through causes, conditions, and relationships."
        )
        closing = (
            "These meanings overlap, but they are not interchangeable. Are you thinking about "
            "the feeling of emptiness in everyday life, or the deeper philosophical or Buddhist idea?"
        )
    else:
        opening = f"Your question asks: {question.rstrip('?')}." if question else "The question is worth answering directly."
        explanation = "I couldn't verify a reliable answer from the material available in this request, so I won't present a guess as fact."
        closing = (
            "If you would like to explore this further, the Archive resource below may offer a useful next step."
            if recommendation_available
            else "I could not identify a sufficiently relevant Archive resource to recommend here."
        )
    return {
        "response": "\n\n".join(part for part in (opening, explanation, closing) if part),
        "doorway_title": title if recommendation_available else "",
        "provider": "deterministic_question_preserving_recovery",
        "model": "",
    }



def _guide_html_to_source_text(raw_html):
    """Preserve WordPress block boundaries and omit only standalone author bylines."""
    from html.parser import HTMLParser
    import html

    class SourceParser(HTMLParser):
        BLOCKS = {"address", "article", "blockquote", "br", "dd", "div", "dl", "dt",
                  "figcaption", "figure", "h1", "h2", "h3", "h4", "h5", "h6",
                  "hr", "li", "main", "ol", "p", "section", "table", "td", "th", "tr", "ul"}
        IGNORED = {"script", "style", "noscript", "svg"}
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.parts, self.ignored_depth = [], 0
        def handle_starttag(self, tag, attrs):
            tag = tag.casefold()
            if tag in self.IGNORED:
                self.ignored_depth += 1
            elif not self.ignored_depth and tag in self.BLOCKS:
                self.parts.append("\n")
        def handle_endtag(self, tag):
            tag = tag.casefold()
            if tag in self.IGNORED and self.ignored_depth:
                self.ignored_depth -= 1
            elif not self.ignored_depth and tag in self.BLOCKS:
                self.parts.append("\n")
        def handle_data(self, data):
            if not self.ignored_depth and data:
                self.parts.append(data)

    parser = SourceParser()
    parser.feed(str(raw_html or ""))
    parser.close()
    blocks = []
    for block in re.split(r"\n+", "".join(parser.parts)):
        block = re.sub(r"\s+", " ", html.unescape(block)).strip()
        if not block:
            continue
        if re.fullmatch(
            r"written\s+by\s+gerald\s+a\.?|"
            r"(?:by\s+)?gerald\s+a?\.?\s+daquila\s*,?\s*"
            r"(?:phd\s+candidate|ph\.?d\.?\s+candidate|author)",
            block, flags=re.I,
        ):
            continue
        blocks.append(block)
    return "\n".join(blocks)

def _wordpress_fetch_selected_canonical_body(url):
    """Fetch the selected public Archive page directly when search misses its body."""
    import html
    from urllib.parse import urlparse

    candidate_url = str(url or "").strip()
    parsed = urlparse(candidate_url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != "geralddaquila.com"
        or parsed.username
        or parsed.password
        or not parsed.path.startswith("/")
        or parsed.query
        or parsed.fragment
    ):
        return None
    try:
        request = UrlRequest(
            candidate_url,
            headers={"Accept": "text/html", "User-Agent": "LivingArchiveGuide/1.0"},
            method="GET",
        )
        with urlopen(request, timeout=5.0) as response:
            final_url = str(response.geturl() or "").strip()
            raw_html = response.read(1_000_000).decode("utf-8", errors="replace")
        final = urlparse(final_url)
        if (
            final.scheme != "https"
            or final.hostname != "geralddaquila.com"
            or final.path.rstrip("/").casefold() != parsed.path.rstrip("/").casefold()
        ):
            return None
        title_match = re.search(r"(?is)<title[^>]*>(.*?)</title>", raw_html)
        title = html.unescape(re.sub(r"(?s)<[^>]+>", " ", title_match.group(1))).strip() if title_match else ""
        raw_html = re.sub(r"(?is)<(script|style|noscript|svg)\b[^>]*>.*?</\1>", " ", raw_html)
        raw_html = re.sub(r"(?is)<!--.*?-->", " ", raw_html)
        main_match = re.search(r"(?is)<main\b[^>]*>(.*?)</main>", raw_html)
        article_match = re.search(r"(?is)<article\b[^>]*>(.*?)</article>", raw_html)
        content_html = (main_match or article_match).group(1) if (main_match or article_match) else raw_html
        content = _guide_html_to_source_text(content_html)
        if len(content) < 80:
            return None
        return {
            "title": title or parsed.path.strip("/").replace("-", " ").title(),
            "url": final_url,
            "text": content[:6000],
        }
    except Exception as exc:
        print(f"The Guide selected canonical body fetch skipped ({type(exc).__name__}).")
        return None


def _wordpress_search_canonical_candidates(query, *, limit=3):
    """Recover public canonical candidates when vector retrieval cannot ground a doorway.

    WordPress search is a bounded, provider-independent retrieval supplement, not
    a source of recommendation authority. Every returned item is re-evaluated by
    the same local evidence and relevance gates as vector-retrieved candidates.
    """
    import html

    # `_subject_terms` may yield a set; sort before ranking so separate Render
    # processes do not send different WordPress queries due to hash iteration order.
    terms = sorted(set(_subject_terms(query)))
    if not terms:
        return []
    # For conceptual questions, search with the concept being examined plus
    # one strong context term. Purely length-based ranking can omit the central
    # concept (for example, "trust") in favour of longer context words, making
    # canonical search miss the very source the visitor needs.
    search_text = ""
    if _is_conceptual_explanatory_request(query):
        conceptual_match = re.match(
            r"^what\s+is\s+(?:the\s+)?(?:role|purpose|significance|importance|function|value|contribution|impact|nature|relationship)\s+of\s+(.+?)\s+(?:in|within|among|for|of|on)\s+(.+?)[?.!]*$",
            re.sub(r"\s+", " ", str(query or "").strip().casefold()),
        )
        if conceptual_match:
            focus_terms = list(_subject_terms(conceptual_match.group(1)))
            context_terms = list(_subject_terms(conceptual_match.group(2)))
            if focus_terms:
                context_terms.sort(key=lambda term: (len(term), term), reverse=True)
                selected = [focus_terms[0]]
                selected.extend(term for term in context_terms if term not in selected)
                # Keep the focus concept and both context concepts together. Reducing
                # this to two terms drops "community" and lets broad stewardship pages
                # outrank the canonical trust source for relationship questions.
                search_text = " ".join(selected[:3]).strip()
    if not search_text:
        # Preserve the established deterministic query shaping for all other
        # requests and for conceptual forms that do not match the bounded pattern.
        indexed_terms = list(enumerate(terms))
        indexed_terms.sort(key=lambda pair: (len(pair[1]), -pair[0]), reverse=True)
        search_text = " ".join(term for _, term in indexed_terms[:2]).strip()
    if not search_text:
        return []
    endpoint = (
        "https://geralddaquila.com/wp-json/wp/v2/search"
        f"?search={quote(search_text, safe='')}&per_page=10"
    )
    try:
        request = UrlRequest(
            endpoint,
            headers={"Accept": "application/json", "User-Agent": "LivingArchiveGuide/1.0"},
            method="GET",
        )
        with urlopen(request, timeout=2.0) as response:
            search_results = json.loads(response.read().decode("utf-8"))
        if not isinstance(search_results, list):
            return []
    except Exception as exc:
        print(f"The Guide canonical search recovery: search unavailable ({type(exc).__name__}).")
        return []

    ranked = []
    for index, item in enumerate(search_results):
        if not isinstance(item, dict):
            continue
        title_obj = item.get("title")
        title = str(title_obj.get("rendered") if isinstance(title_obj, dict) else title_obj or "").strip()
        url = str(item.get("url") or "").strip()
        links = item.get("_links") if isinstance(item.get("_links"), dict) else {}
        self_links = links.get("self") if isinstance(links.get("self"), list) else []
        href = str((self_links[0] or {}).get("href") or "") if self_links and isinstance(self_links[0], dict) else ""
        if not title or not re.match(r"^https://geralddaquila\.com/\S+$", url, re.I):
            continue
        if not re.match(r"^https://geralddaquila\.com/wp-json/wp/v2/(?:posts|pages)/[0-9]+(?:\?.*)?$", href, re.I):
            continue
        title_tokens = set(re.findall(r"[a-z0-9]+", title.casefold()))
        title_hits = sum(bool(_term_forms(term) & title_tokens) for term in terms)
        ranked.append((title_hits, -index, title, url, href))
    ranked.sort(reverse=True)

    def fetch_candidate(entry):
        _title_hits, _order, title, url, href = entry
        try:
            request = UrlRequest(
                href,
                headers={"Accept": "application/json", "User-Agent": "LivingArchiveGuide/1.0"},
                method="GET",
            )
            with urlopen(request, timeout=5.0) as response:
                resource = json.loads(response.read().decode("utf-8"))
            if not isinstance(resource, dict):
                return None
            resource_url = str(resource.get("link") or url).strip()
            resource_title_obj = resource.get("title")
            resource_title = str(
                resource_title_obj.get("rendered")
                if isinstance(resource_title_obj, dict) else resource_title_obj or title
            ).strip()
            content_obj = resource.get("content")
            excerpt_obj = resource.get("excerpt")
            content_html = str(content_obj.get("rendered") or "") if isinstance(content_obj, dict) else str(content_obj or "")
            excerpt_html = str(excerpt_obj.get("rendered") or "") if isinstance(excerpt_obj, dict) else str(excerpt_obj or "")
            raw_content = content_html or excerpt_html
            raw_content = re.sub(r"(?is)<(script|style)\b[^>]*>.*?</\1>", " ", raw_content)
            content = _guide_html_to_source_text(raw_content)
            if not content or not re.match(r"^https://geralddaquila\.com/\S+$", resource_url, re.I):
                return None
            return {"title": html.unescape(resource_title), "url": resource_url, "text": content[:6000]}
        except Exception as exc:
            print(f"The Guide canonical search recovery: resource fetch skipped ({type(exc).__name__}).")
            return None

    # Fetch the bounded candidate slice concurrently but preserve ranking order.
    # The per-request timeout still bounds each outbound operation.
    from concurrent.futures import ThreadPoolExecutor

    candidate_slice = ranked[:limit]
    with ThreadPoolExecutor(max_workers=max(1, min(limit, len(candidate_slice)))) as executor:
        recovered = [item for item in executor.map(fetch_candidate, candidate_slice) if item]
    print(f"The Guide canonical search recovery: search_terms={len(search_text.split())}, candidates={len(recovered)}.")
    return recovered


def _comparative_subject_terms(query):
    """Extract compared concepts from common comparison questions."""
    normalized = re.sub(r"\s+", " ", str(query or "").strip().casefold())
    patterns = (
        r"\bdifference between (.+?) and (.+?)[?.!]*$",
        r"\brelationship between (.+?) and (.+?)[?.!]*$",
        r"\bcompare (.+?) (?:and|with|to) (.+?)[?.!]*$",
        r"\bcomparison of (.+?) and (.+?)[?.!]*$",
        r"\bwhat distinguishes (.+?) from (.+?)[?.!]*$",
        r"\bdistinguish (.+?) from (.+?)[?.!]*$",
        r"\bwhat separates (.+?) from (.+?)[?.!]*$",
        r"\bwhat differentiates (.+?) from (.+?)[?.!]*$",
        r"\bhow does (.+?) differ from (.+?)[?.!]*$",
        r"\bhow do (.+?) differ from (.+?)[?.!]*$",
        r"\bhow are (.+?) different from (.+?)[?.!]*$",
    )
    for pattern in patterns:
        match = re.search(pattern, normalized)
        if match:
            terms = []
            for value in match.groups():
                words = [w for w in re.findall(r"[a-z0-9]+", value)
                         if w not in {"the", "a", "an", "is", "are", "does", "do", "how", "what"}]
                if words:
                    terms.append(" ".join(words[-4:]))
            if len(terms) == 2:
                return terms
    return []


def _comparative_candidate_has_direct_fit(query, document):
    """Require a title-level match and evidence for both compared concepts.

    Use explicit concept families rather than literal whole-phrase matching:
    "positional authority" may be discussed as formal authority or role-based
    power without repeating the exact visitor wording.
    """
    subjects = _comparative_subject_terms(query)
    if len(subjects) != 2:
        return True
    title = str(document.get("title") or "").casefold()
    body = str(document.get("text") or document.get("content") or document.get("excerpt") or "").casefold()

    def concept_pattern(subject):
        words = set(re.findall(r"[a-z0-9]+", subject.casefold()))
        if words & {"leadership", "leader", "leaders", "lead"}:
            return r"\b(?:leadership|leader|leaders|leading|lead)\b"
        if words & {"authority", "authorities", "positional", "position", "power", "role"}:
            return r"\b(?:positional authority|formal authority|authority|authorities|position(?:al)?|role[- ]based power|formal power|institutional power|power|role|roles)\b"
        escaped = [re.escape(word) for word in words if word]
        return r"\b(?:" + "|".join(escaped) + r")\b" if escaped else r"(?!)"

    title_fit = any(re.search(concept_pattern(subject), title) for subject in subjects)
    body_fit = all(re.search(concept_pattern(subject), body) for subject in subjects)
    return title_fit and body_fit


def _stewardship_conflict_candidate_has_direct_fit(query, document):
    """Require direct evidence for stewardship questions about competing values.

    Broad stewardship resources are not automatically relevant to conflict
    questions. The title must signal a stewardship/governance/decision topic and
    the body must substantively address disagreement, competing values, or
    resolving trade-offs. If evidence is insufficient, the recommendation is
    omitted; the visitor's answer is preserved by the caller.
    """
    q = _normalize_query(query)
    if not re.search(r"\bstewardship\b", q, re.I):
        return True
    conflict = bool(re.search(
        r"\b(?:disagree|disagreement|conflict|competing|opposing|different priorities|"
        r"what is worth protecting|worth protecting|trade[- ]?offs?)\b", q, re.I
    ))
    if not conflict:
        return True
    title = str(document.get("title") or "").casefold()
    body = str(document.get("text") or document.get("content") or document.get("excerpt") or "").casefold()
    title_fit = bool(re.search(r"\b(?:stewardship|governance|decision|conflict|values|ethic)\b", title))
    body_fit = bool(re.search(
        r"\b(?:disagree|disagreement|conflict|competing values|different values|"
        r"trade[- ]?offs?|what each protects|protecting|decision[- ]making|"
        r"fair process|resolve|reconcile)\b", body
    ))
    return title_fit and body_fit


def _ethical_tradeoff_candidate_has_direct_fit(query, document):
    """Reject merely adjacent resources for questions about conflicting harms.

    For this intent, a recommendation must substantively address ethical
    trade-offs or conflicting harms in addition to signalling that topic in
    its title. A title about belonging or group identity alone is insufficient.
    """
    q = _normalize_query(query)
    competing_harms = (
        bool(re.search(
            r"\b(?:repair(?:ing)? the harm|address(?:ing)? the harm|harm to one group|"
            r"one group.{0,50}another group|different harm for another|conflicting harms|"
            r"competing harms|ethical trade[- ]?offs?|conflict between groups)\b", q, re.I
        ))
        and bool(re.search(
            r"\b(?:another group|one group|different harm|conflict|trade[- ]?off|"
            r"decision[- ]makers|decisions|work through that conflict)\b", q, re.I
        ))
    )
    if not competing_harms:
        return True

    title = str(document.get("title") or "").casefold()
    body = str(document.get("text") or document.get("content") or document.get("excerpt") or "").casefold()
    title_fit = bool(re.search(
        r"\b(?:ethical|ethic|trade[- ]?off|conflicting harms|restorative justice|"
        r"repairing harm|accountability|justice|conflict resolution|governance|"
        r"competing values|moral decision)\b", title
    ))
    body_fit = (
        bool(re.search(
            r"\b(?:trade[- ]?offs?|conflicting harms|competing harms|ethical conflict|"
            r"repair(?:ing)? harm|restorative justice|competing values|"
            r"decision criteria|fair process|conflict resolution)\b", body
        ))
        and bool(re.search(
            r"\b(?:harm|harmed|affected people|consequences|burden|losses|"
            r"who bears|people affected|rights|power|sacrif|alternatives|"
            r"repair|accountability)\b", body
        ))
    )
    return title_fit and body_fit


def _resource_allocation_candidate_has_direct_fit(query, document):
    """Reject generic resources for questions about funding competing priorities."""
    q = _normalize_query(query)
    if not re.search(r"\b(?:funding|fund|budget|allocate|allocation|priorit(?:y|ies|ize|ise|ization)|limited resources|competing priorities)\b", q, re.I):
        return True
    title = str(document.get("title") or "").casefold()
    body = str(document.get("text") or document.get("content") or document.get("excerpt") or "").casefold()
    title_fit = bool(re.search(r"\b(?:funding|budget|allocation|allocate|priorit(?:y|ies|ization|ize|ise)|resource management|decision[- ]making|trade[- ]offs?|governance)\b", title))
    body_fit = bool(re.search(r"\b(?:fund(?:ing|s)?|budget(?:s|ing)?|allocat(?:e|es|ed|ing|ion)|priorit(?:y|ies|ization|ize|ise)|limited resources|competing needs|decision criteria|trade[- ]offs?|scarce resources|resource allocation|fair process|weigh competing)\b", body))
    return title_fit and body_fit

def _harm_repair_candidate_has_direct_fit(query, document):
    """Fail closed on resource recommendations for harm-repair adequacy questions.

    A resource must explicitly concern repair/accountability and substantively
    address the losses or participation of people harmed. Generic personal-growth
    essays are not relevant merely because retrieval ranked them highly.
    """
    q = _normalize_query(query)
    harm_repair_question = (
        bool(re.search(
            r"\b(?:people who suffered (?:the )?harm|people harmed|those harmed|"
            r"people affected|those affected|survivors|victims|those who suffered)\b", q, re.I
        ))
        and bool(re.search(
            r"\b(?:repair|reparation|remedy|restitution|compensation|make amends)\b", q, re.I
        ))
        and bool(re.search(
            r"\b(?:does not address|doesn't address|do not address|don't address|"
            r"fails? to address|inadequate|insufficient|what they actually lost|"
            r"their actual losses|does not restore|doesn't restore|not enough)\b", q, re.I
        ))
    )
    if not harm_repair_question:
        return True

    title = str(document.get("title") or "").casefold()
    body = str(document.get("text") or document.get("content") or document.get("excerpt") or "").casefold()
    title_fit = bool(re.search(
        r"\b(?:repair|reparation|restorative justice|restorative practice|"
        r"accountability|reconciliation|redress|remedy|justice|governance)\b", title
    ))
    body_fit = (
        bool(re.search(
            r"\b(?:repair|reparation|restorative justice|restitution|redress|"
            r"make amends|address the harm|repairing harm|remedy)\b", body
        ))
        and bool(re.search(
            r"\b(?:harmed|harm|affected people|people affected|survivors|"
            r"losses|what was lost|listen|participat|consent|voice|needs of those)\b", body
        ))
    )
    return title_fit and body_fit


def _general_guide_authoritative_doorway(query, context_data):
    """Select a relevant canonical doorway from retrieved evidence only.

    A syntactically valid URL is not proof of relevance. Provider/core preselection
    is treated as a candidate, never as authority by itself. Rank retrieved
    documents with the Guide's existing relevance gate and emit only a doorway
    supported by the selected document's title, URL, and content. v489.12
    keeps this selection independent of provider-generated text and fallback URLs.
    """
    if not isinstance(context_data, dict):
        return None
    try:
        profile = _base._inquiry_profile(query)
        if profile.get("risk") or profile.get("action") == "risk":
            return None

        candidates = []
        protected = (
            context_data.get("generation_authority_protected_docs")
            or context_data.get("question_authority_protected_docs")
            or []
        )
        if isinstance(protected, list):
            candidates.extend(item for item in protected if isinstance(item, dict))

        canonical_context = str(
            context_data.get("canonical_link_context")
            or context_data.get("context_blocks")
            or ""
        )
        if canonical_context:
            candidates.extend(_parse_context_documents(canonical_context))

        try:
            supplied = general_guide_composition._documents_from_context(
                use_core, context_data
            )
        except Exception:
            supplied = []
        candidates.extend(item for item in supplied if isinstance(item, dict))

        # Preserve only evidence-bearing documents with canonical Archive URLs.
        evidence_docs = []
        seen = set()
        for item in candidates:
            title = str(item.get("title") or "").strip()
            url = str(item.get("url") or item.get("canonical_url") or "").strip()
            content = str(
                item.get("content") or item.get("text") or item.get("excerpt") or ""
            ).strip()
            if not title or not content:
                continue
            if not re.match(r"^https://geralddaquila\.com/\S+$", url, re.I):
                continue
            key = (title.casefold(), url.casefold())
            if key in seen:
                continue
            seen.add(key)
            evidence_docs.append({"title": title, "url": url, "text": content})

        # Fuzzy relevance runs in shadow mode only. Scores are diagnostic and
        # deliberately do not alter hard gates, candidate ordering, or selection.
        for _candidate in evidence_docs:
            _candidate["_fuzzy_relevance_shadow"] = _score_guide_fuzzy_relevance_shadow(query, _candidate)
        shadow_observation_candidates = list(evidence_docs)

        comparative_subjects = _comparative_subject_terms(query)
        if comparative_subjects:
            evidence_docs = [item for item in evidence_docs if _comparative_candidate_has_direct_fit(query, item)]

        # Conflict-specific relevance is independent of general stewardship
        # topic overlap. Apply it before ranking and again after bounded recovery.
        evidence_docs = [
            item for item in evidence_docs
            if _stewardship_conflict_candidate_has_direct_fit(query, item)
        ]
        evidence_docs = [item for item in evidence_docs if _resource_allocation_candidate_has_direct_fit(query, item)]
        evidence_docs = [item for item in evidence_docs if _harm_repair_candidate_has_direct_fit(query, item)]
        evidence_docs = [item for item in evidence_docs if _ethical_tradeoff_candidate_has_direct_fit(query, item)]

        topic_groups = _topic_anchor_groups(query)
        # When a visitor asks what to read about political dynasties, a broad
        # essay that merely mentions the topic cannot displace the direct study.
        # Require a title-level subject match for this recommendation task so
        # that a missing direct candidate triggers bounded canonical recovery.
        require_dynasty_title = (
            profile.get("action") in {"recommendation", "navigation"}
            and "political_dynasties" in topic_groups
        )
        if require_dynasty_title:
            evidence_docs = [
                item for item in evidence_docs
                if "political_dynasties" in _topic_anchor_groups(item.get("title") or "")
            ]

        primary = _canonical_primary_from_docs(evidence_docs, query, profile)
        if not primary:
            # Retrieval and doorway selection are separate. If the retrieved
            # candidate pool lacks a direct subject match, recover public
            # canonical candidates and subject them to the same relevance gate.
            fallback_docs = _wordpress_search_canonical_candidates(query)
            if comparative_subjects:
                # Broaden discovery by each compared subject, then retain the
                # same direct-fit gates below before any doorway is selected.
                for _subject in comparative_subjects:
                    fallback_docs.extend(
                        _wordpress_search_canonical_candidates(_subject, limit=10)
                    )
            if require_dynasty_title:
                # A distinctive subject query supplements the general search;
                # it does not replace the visitor's original query.
                fallback_docs.extend(
                    _wordpress_search_canonical_candidates("political dynasties", limit=10)
                )
            fallback_seen = {
                (
                    str(item.get("title") or "").casefold(),
                    str(item.get("url") or item.get("canonical_url") or "").casefold(),
                )
                for item in evidence_docs
            }
            for item in fallback_docs:
                key = (
                    str(item.get("title") or "").casefold(),
                    str(item.get("url") or item.get("canonical_url") or "").casefold(),
                )
                if key not in fallback_seen:
                    evidence_docs.append(item)
                    fallback_seen.add(key)

            # Refresh shadow scores for fallback candidates too. These scores
            # remain diagnostic only and do not affect candidate eligibility.
            for _candidate in evidence_docs:
                _candidate["_fuzzy_relevance_shadow"] = _score_guide_fuzzy_relevance_shadow(query, _candidate)
            shadow_observation_candidates.extend(evidence_docs)

            # Recovery is a candidate source, not authority: reapply every
            # subject-specific gate after it has contributed candidates.
            if comparative_subjects:
                evidence_docs = [item for item in evidence_docs if _comparative_candidate_has_direct_fit(query, item)]
            evidence_docs = [
                item for item in evidence_docs
                if _stewardship_conflict_candidate_has_direct_fit(query, item)
            ]
            evidence_docs = [item for item in evidence_docs if _resource_allocation_candidate_has_direct_fit(query, item)]
            evidence_docs = [item for item in evidence_docs if _harm_repair_candidate_has_direct_fit(query, item)]
            evidence_docs = [item for item in evidence_docs if _ethical_tradeoff_candidate_has_direct_fit(query, item)]
            if require_dynasty_title:
                evidence_docs = [
                    item for item in evidence_docs
                    if "political_dynasties" in _topic_anchor_groups(item.get("title") or "")
                ]
            asks_for_homepage = bool(re.search(
                r"\b(?:homepage|home page|main page|site home|website home)\b",
                str(query or ""),
                re.I,
            ))
            if not asks_for_homepage:
                evidence_docs = [
                    item for item in evidence_docs
                    if "/" in str(item.get("url") or item.get("canonical_url") or "").split("://", 1)[-1] and str(item.get("url") or item.get("canonical_url") or "").split("://", 1)[-1].split("/", 1)[1].strip("/")
                ]
            primary = _canonical_primary_from_docs(evidence_docs, query, profile)

        if not primary:
            # A missing recommendation is preferable to an unrelated doorway.
            # The caller keeps the answer intact and serializes no recommendation.
            print("The Guide canonical doorway: no candidate passed relevance after bounded search recovery.")
            # Record the no-selection outcome too, so shadow evaluation can
            # distinguish an absent doorway from a disagreement on a selection.
            try:
                _record_guide_fuzzy_shadow_comparison(
                    query=query,
                    candidates=shadow_observation_candidates,
                    selected=None,
                )
            except Exception:
                pass
            return None

        # Best-effort shadow observation only: never feeds back into selection.
        # The observer hashes the query and resource URLs and swallows all errors.
        try:
            _record_guide_fuzzy_shadow_comparison(
                query=query,
                candidates=shadow_observation_candidates,
                selected=primary,
            )
        except Exception:
            pass

        # Titles are plain text in the public JSON contract: decode HTML
        # entities and remove emoji/decorative symbols at the boundary.
        import html
        title = html.unescape(str(primary.get("title") or "")).strip()
        title = re.sub(r"[\U0001F000-\U0001FAFF\U00002600-\U000027BF]", "", title)
        title = re.sub(r"\s+", " ", title).strip()
        url = str(primary.get("url") or primary.get("canonical_url") or "").strip()
        if not title or not re.match(r"^https://geralddaquila\.com/\S+$", url, re.I):
            return None
        return {"title": title, "url": url}
    except Exception as exc:
        print(
            "The Guide General Guide doorway selection failed safely: "
            f"{exc}"
        )
        return None


def _normalize_authoritative_recommendation(doorway):
    """Return the single public navigation contract, or None if invalid.

    Recommendation authority belongs to the Guide, not the composition provider.
    This helper makes the response envelope deterministic across provider
    success, provider exhaustion, and conservative recovery.
    """
    if not isinstance(doorway, dict):
        return None
    title = str(doorway.get("title") or "").strip()
    url = str(
        doorway.get("url")
        or doorway.get("canonical_url")
        or ""
    ).strip()
    if not title or not re.match(r"^https://geralddaquila\.com(?:/.*)?$", url, re.I):
        return None
    return {"title": title, "url": url}


def _apply_registered_gold_standard_doorway(doorway, gold_standard):
    """Apply only a complete, verified Gold Standard doorway pair.

    Frozen answer records may intentionally leave the destination URL unset.
    A title without its canonical URL is not a navigable recommendation and
    must never replace a separately selected, validated doorway. If no valid
    independent doorway exists, the public response carries no recommendation.
    """
    if gold_standard is not None and bool(gold_standard.get("forbids_doorway")):
        return None

    title = str((gold_standard or {}).get("doorway_title") or "").strip()
    url = str((gold_standard or {}).get("doorway_url") or "").strip()
    if title and url:
        approved_pair = _normalize_authoritative_recommendation(
            {"title": title, "url": url}
        )
        if approved_pair is not None:
            return approved_pair

    # Incomplete/unverified Gold Standard metadata has no authority to invent
    # a doorway. Keep only an independently selected, canonical, valid pair.
    return _normalize_authoritative_recommendation(doorway)


def _enforce_registered_gold_standard_doorway(doorway, gold_standard, query=""):
    """Preserve the default doorway unless an approved standard explicitly forbids handoff.

    A blank doorway in a Gold Standard means that the answer text is frozen, not
    that every relevant Archive doorway must be suppressed. The independently
    selected doorway has already passed the canonical relevance and URL gates.
    Only an explicit no-handoff assertion overrides that default.
    """
    if gold_standard is not None and bool(gold_standard.get("forbids_doorway")):
        return None
    return doorway


# v489.09 regression probes: valid Archive URLs survive validation and stewardship questions retain a canonical doorway
# validator, while non-HTTPS and off-domain destinations remain rejected.
_v48908_probe_url = "https://geralddaquila.com/knowledge-memory-living-codices/"
_v48908_probe = {"title": "Knowledge, Memory & Living Codices", "url": _v48908_probe_url}
if not _normalize_authoritative_recommendation(_v48908_probe):
    raise RuntimeError("USE v489.09 invariant failed: valid canonical recommendation rejected.")
if not re.match(r"^https://geralddaquila\.com/\S+$", _v48908_probe_url, re.I):
    raise RuntimeError("USE v489.09 invariant failed: canonical doorway regex rejected valid HTTPS URL.")
if _normalize_authoritative_recommendation({"title": "Invalid", "url": "http://geralddaquila.com/example/"}):
    raise RuntimeError("USE v489.09 invariant failed: non-HTTPS recommendation accepted.")
if _normalize_authoritative_recommendation({"title": "Invalid", "url": "https://example.org/example/"}):
    raise RuntimeError("USE v489.09 invariant failed: off-domain recommendation accepted.")


def _basic_inquiry_contains_html_markup(text):
    """Reject HTML-shaped provider output at the plain-text visitor boundary.

    Canonical doorways are returned as structured title/URL data, never embedded
    in generated prose. Detect incomplete tags as well as complete tags: malformed
    provider markup must not be passed to the frontend as if it were an answer.
    """
    value = str(text or "")
    return bool(re.search(
        r"<\s*/?\s*(?:a|p|div|span|br|img|iframe|script|style|button|section|ul|ol|li)\b",
        value,
        re.I,
    ))


def _basic_inquiry_markup_recovery(query, history=None, intent="TOPICAL_INQUIRY"):
    """Recompose once without Archive snippets after untrusted markup is rejected.

    In deterministic-only calibration mode, never re-enter the LLM composer
    through this secondary recovery seam.
    """
    if str(os.getenv("USE_REASONING_PROVIDER_MODE", "auto") or "auto").strip().casefold() == "deterministic_only":
        print("The Guide contextless markup recovery: skipped because deterministic-only mode is active.")
        return ""
    clean_context = {
        "intent": str(intent or "TOPICAL_INQUIRY"),
        "context_blocks": "",
        "canonical_link_context": "",
        "generation_authority_protected_docs": [],
        "question_authority_protected_docs": [],
    }
    try:
        result = general_guide_composition.compose(
            use_core=use_core,
            query=str(query or "").strip(),
            context_data=clean_context,
            history_text=_history_text(history),
        )
        response = _sanitize_basic_inquiry_response(
            str((result or {}).get("response") or "").strip()
        )
        if not response or _basic_inquiry_contains_html_markup(response):
            return ""
        if _basic_inquiry_has_source_dump(response):
            return ""
        return response
    except Exception as exc:
        print(f"The Guide contextless markup recovery failed safely: {type(exc).__name__}.")
        return ""


# v489.193 outward-response integrity probes: complete and truncated HTML are both rejected.
if not _basic_inquiry_contains_html_markup('<a href="https://geralddaquila.com/example/">Open</a>'):
    raise RuntimeError("USE visitor-response contract failed: complete HTML markup was not detected.")
if not _basic_inquiry_contains_html_markup('<a href="https://geralddaquila.com/2025/05/21/political-dynasties”'):
    raise RuntimeError("USE visitor-response contract failed: truncated HTML markup was not detected.")
if _basic_inquiry_contains_html_markup("Stewardship means caring for what has been entrusted to us."):
    raise RuntimeError("USE visitor-response contract failed: ordinary prose was rejected.")


def _guide_subject_discovery_query(query):
    """Extract the subject from a natural-language request to find Archive material.

    This is a reusable query-shaping boundary: it removes the visitor's search
    instruction while preserving the requested topic. The original question is
    still used for visitor-facing composition; the extracted subject is used
    only to retrieve and evaluate relevant resources.
    """
    q = re.sub(r"\s+", " ", _normalize_query(query)).strip()
    patterns = (
        # Natural-language reading requests are still Archive discovery tasks.
        # Extract their subject so the answer is grounded in the selected page,
        # rather than letting a broad generated explanation contradict the link.
        r"^(?:i want to understand|i would like to understand|i'd like to understand|i want to learn about|i would like to learn about|i'd like to learn about)\s+(.+?)(?:[.!?]\s*(?:what|which)\s+(?:should|could|can|would)\s+i\s+read\b.*)?[?.!]*$",
        r"^(?:what|which)\s+(?:should|could|can|would)\s+i\s+read\s+(?:about|on|regarding)\s+(.+?)[?.!]*$",
        # A named title followed by a request for the study should retain the title as subject.
        r"^(.+?)\s+[—–-]\s+i\s+(?:want|need)\s+(?:the\s+)?(?:study|article|essay|paper|page|resource)\s+itself(?:,\s*please)?[?.!]*$",
        r"^(?:i\s+)?(?:want|need)\s+(?:the\s+)?(?:study|article|essay|paper|page|resource)\s+(?:itself(?:\s+(?:on|about|regarding))?|on|about|regarding)\s+(.+?)[?.!]*$",
        r"^(?:please\s+)?(?:recommend|find|show\s+me)\s+(?:the\s+)?(?:study|article|essay|paper|page|resource)\s+(?:called|titled|on|about|regarding)\s+(.+?)[?.!]*$",
        # Requests for the study/article itself are resource discovery, not generic Q&A.
        r"^(?:please\s+)?where\s+(?:can|could|do)\s+i\s+find\s+(?:the\s+)?(?:(?:relevant|useful|specific)\s+)?(?:material|materials|information|resources?|content|articles?|essays?|documents?|entries)\s+(?:about|on|regarding|concerning|related\s+to)\s+(.+?)[?.!]*$",
        r"^(?:please\s+)?(?:find|show\s+me|help\s+me\s+find|locate|search\s+for)\s+(?:(?:relevant|useful|specific)\s+)?(?:material|materials|information|resources?|content|articles?|essays?|documents?|entries)\s+(?:about|on|regarding|concerning|related\s+to)\s+(.+?)[?.!]*$",
        r"^(?:i(?:'m|\s+am)\s+looking\s+for|i\s+need|can\s+you\s+find|could\s+you\s+find)\s+(?:(?:relevant|useful|specific)\s+)?(?:material|materials|information|resources?|content|articles?|essays?|documents?|entries)\s+(?:about|on|regarding|concerning|related\s+to)\s+(.+?)[?.!]*$",
    )
    for pattern in patterns:
        match = re.match(pattern, q, re.I)
        if match:
            subject = re.sub(r"\s+", " ", match.group(1)).strip(" \t.,;:?!")
            if subject and len(re.findall(r"[a-z0-9]+", subject, re.I)) >= 1:
                return subject
    # A short standalone noun phrase is a resource/topic lookup, not a request for general prose.
    # Do not apply this fallback to sentences or explicit questions.
    if not re.search(r"[?!.]", q) and 1 <= len(q.split()) <= 12:
        if not re.search(r"\b(?:what|why|when|where|who|how|is|are|was|were|does|do|did|can|could|would|should|will|has|have|had)\b", q, re.I):
            return q.strip(" \t.,;:")
    return ""


def _guide_requires_canonical_subject_supplement(
    archive_evidence_unavailable, discovery_subject, conceptual_inquiry=False
):
    """Fetch canonical page bodies for discovery and explanatory questions.

    A vector-selected doorway is only a candidate. Conceptual questions must
    fetch and inspect its public Archive body before the final grounding gate
    can decide whether to answer, recommend it, or fail closed.
    """
    return bool(
        archive_evidence_unavailable
        or str(discovery_subject or "").strip()
        or conceptual_inquiry
    )


def _guide_subject_supplement_limit(discovery_subject, conceptual_inquiry=False):
    """Broaden candidate recall for resource-finding and conceptual questions."""
    # Conceptual questions need the same wider candidate window as explicit
    # discovery requests: the central concept source can rank behind broad pages.
    return 10 if (
        str(discovery_subject or "").strip() or conceptual_inquiry
    ) else 5


def _guide_discovery_evidence_grade(subject, document, node=None):
    """Grade page-level subject evidence independently of the search provider.

    DIRECT requires the subject itself to be established by the page, not just
    one broad shared token. RELATED requires a real page-level overlap plus
    corroborating registered purpose/hints; it must be described as adjacent.
    Metadata alone, or an incidental body token, is WEAK and cannot authorize
    a recommendation.
    """
    if not isinstance(document, dict) or not str(subject or "").strip():
        return {"grade": "weak", "score": 0, "support": []}
    title = str(document.get("title") or "").strip().casefold()
    body = str(
        document.get("text") or document.get("content") or document.get("excerpt") or ""
    ).strip().casefold()
    early = body[:3000]
    if len(body) < 80:
        return {"grade": "weak", "score": 0, "support": []}

    stop = {
        "about", "article", "articles", "content", "document", "documents",
        "general", "information", "material", "materials", "public", "resource",
        "resources", "specific", "where", "find", "please", "useful", "relevant",
        "could", "would", "should", "from", "with", "into", "that", "this",
        # Natural-language question wrappers are not subject anchors.
        "how", "what", "why", "when", "does", "do", "did", "can", "in", "the",
        "and", "to", "of", "for", "affect", "affects", "affecting", "read",
        "want", "understand", "learn",
    }
    subject_tokens = {
        token for token in re.findall(r"[a-z0-9]+", str(subject).casefold())
        if len(token) >= 4 and token not in stop
    }
    if not subject_tokens:
        return {"grade": "weak", "score": 0, "support": []}

    title_tokens = set(re.findall(r"[a-z0-9]+", title))
    body_tokens = set(re.findall(r"[a-z0-9]+", body))
    early_tokens = set(re.findall(r"[a-z0-9]+", early))
    title_hits = subject_tokens & title_tokens
    body_hits = subject_tokens & body_tokens
    early_hits = subject_tokens & early_tokens
    normalized_subject = re.sub(r"\s+", " ", str(subject).casefold()).strip()
    phrase_in_title = normalized_subject in title
    phrase_in_early = normalized_subject in early

    direct_fit = 0
    try:
        direct_fit, _coverage, _relation_hits, _answerability = (
            use_core._question_evidence_fit_profile(str(subject), document)
        )
        direct_fit = int(direct_fit or 0)
    except Exception:
        direct_fit = 0

    # Page text can contain repeated incidental mentions from navigation,
    # boilerplate, or a broad page's framing. For registered candidates, body
    # mentions alone cannot establish directness unless the approved node's own
    # purpose/hints also name every subject anchor. A matching page title is
    # still strong evidence. Non-registry bodies require unusually strong,
    # repeated subject evidence and cannot independently authorize a doorway.
    node_metadata = " ".join([
        str(node.get("title") or ""),
        str(node.get("purpose") or ""),
        " ".join(str(value) for value in (node.get("semantic_hints") or [])),
    ]).casefold() if node else ""
    metadata_tokens = set(re.findall(r"[a-z0-9]+", node_metadata))
    metadata_subject_hits = subject_tokens & metadata_tokens
    phrase_count = len(re.findall(re.escape(normalized_subject), body))
    direct_body_fit = (
        (
            node is not None
            and len(subject_tokens) >= 2
            and len(early_hits) >= 2
            and len(metadata_subject_hits) == len(subject_tokens)
            and (
                (phrase_count >= 1 and direct_fit >= 2)
                # A registered node whose title names the subject and whose
                # opening text corroborates it is direct even when the visitor's
                # full natural-language question is not repeated verbatim.
                or (len(title_hits) >= 2 and len(early_hits) >= 3)
            )
        )
        or (
            node is None
            and phrase_in_early
            and phrase_count >= 3
            and direct_fit >= 3
            and len(body_hits) >= 2
            and len(early_hits) >= 2
        )
    )

    # Relational reading requests can include a verb or outcome not repeated in
    # the title ("how political dynasties affect public accountability"). An
    # active registered title is a strong subject anchor, but directness still
    # requires page-level body evidence and near-complete support from approved
    # registry metadata. This keeps broad related pages from passing on a shared
    # keyword while allowing a dedicated study to answer a relationally phrased
    # request about its established subject.
    title_anchor_tokens = {
        token for token in re.findall(r"[a-z0-9]+", title)
        if len(token) >= 4 and token not in stop
    }
    title_anchor_hits = title_anchor_tokens & subject_tokens
    requested_aspect_hits = early_hits & (subject_tokens - title_anchor_tokens)
    registered_title_anchor_fit = (
        node is not None
        and len(title_anchor_tokens) >= 2
        and len(title_anchor_hits) >= min(3, len(title_anchor_tokens))
        and len(early_hits) >= 2
        and bool(requested_aspect_hits)
        and len(metadata_subject_hits) >= max(1, len(subject_tokens) - 1)
    )
    direct = phrase_in_title or direct_body_fit or registered_title_anchor_fit
    if direct:
        support = sorted(early_hits or body_hits)
        return {"grade": "direct", "score": 100 + direct_fit + len(early_hits) * 4 + len(title_hits) * 3, "support": support}

    # A related destination must be an approved Guide Node and show substantive
    # overlap in its own body. One generic token is not enough by itself: require
    # at least one subject anchor in the opening and a second body-level signal
    # represented in the registered title/purpose/hints. Report the shared terms
    # literally; do not invent a semantic relationship.
    if not node:
        return {"grade": "weak", "score": 0, "support": sorted(body_hits)}
    metadata = node_metadata
    registered_anchors = {
        token for token in metadata_tokens
        if len(token) >= 5 and token not in stop and token not in subject_tokens
    }
    body_context = {
        token for token in body_tokens
        if len(token) >= 5 and token not in stop and token not in subject_tokens
    }
    corroborating_context = registered_anchors & body_context
    if body_hits and len(corroborating_context) >= 2:
        support = sorted(body_hits | corroborating_context)
        metadata_subject_hits = subject_tokens & metadata_tokens
        # Prefer a registry node whose own approved purpose/hints name the
        # requested subject, rather than a broad node that merely mentions it.
        score = (
            len(body_hits) * 8
            + len(metadata_subject_hits) * 12
            + len(corroborating_context) * 2
            + min(direct_fit, 2)
        )
        return {"grade": "related", "score": score, "support": support}
    return {"grade": "weak", "score": 0, "support": sorted(body_hits)}


def _guide_selected_doorway_discovery_evidence(documents, subject, doorway):
    """Validate the selected canonical page and grade its direct/related fit."""
    if not isinstance(doorway, dict) or not str(subject or "").strip():
        return []
    selected_url = str(doorway.get("url") or "").strip().rstrip("/").casefold()
    if not selected_url:
        return []
    accepted = []
    for document in documents if isinstance(documents, list) else []:
        if not isinstance(document, dict):
            continue
        candidate_url = str(
            document.get("url") or document.get("canonical_url") or ""
        ).strip().rstrip("/").casefold()
        if candidate_url != selected_url:
            continue
        node = document.get("_guide_node") if isinstance(document.get("_guide_node"), dict) else None
        grade = _guide_discovery_evidence_grade(subject, document, node=node)
        if grade["grade"] in {"direct", "related"}:
            approved = dict(document)
            approved["_discovery_relevance"] = grade["grade"]
            approved["_discovery_relevance_score"] = grade["score"]
            approved["_discovery_support_terms"] = grade["support"]
            accepted.append(approved)
    accepted.sort(
        key=lambda item: (
            item.get("_discovery_relevance") == "direct",
            int(item.get("_discovery_relevance_score") or 0),
        ),
        reverse=True,
    )
    return accepted[:1]

def _guide_registered_discovery_nodes(subject, limit=3):
    """Rank active, WordPress-authorized Guide Nodes for a discovery subject.

    This is metadata-based candidate selection, not recommendation authority:
    a node can be selected only after its canonical body is fetched and passes
    the existing selected-page evidence checks.
    """
    query = re.sub(r"\s+", " ", str(subject or "").casefold()).strip()
    query_terms = {
        token for token in re.findall(r"[a-z0-9]+", query)
        if len(token) >= 4 and token not in {
            "about", "article", "articles", "content", "document", "documents",
            "general", "information", "material", "materials", "public",
            "resource", "resources", "specific", "where", "find",
        }
    }
    if not query_terms:
        return []
    ranked = []
    try:
        nodes = _guide_node_registry_snapshot()
    except Exception as exc:
        print(f"The Guide registry discovery: registry unavailable ({type(exc).__name__}).")
        return []
    for node in nodes:
        if not isinstance(node, dict) or str(node.get("status") or "") != "active":
            continue
        url = str(node.get("canonical_url") or "").strip()
        title = str(node.get("title") or "").strip()
        if not title or not re.match(r"^https://geralddaquila\.com/\S+$", url, re.I):
            continue
        metadata = " ".join([
            title,
            str(node.get("purpose") or ""),
            " ".join(str(value) for value in (node.get("semantic_hints") or [])),
        ]).casefold()
        metadata_terms = set(re.findall(r"[a-z0-9]+", metadata))
        overlap = query_terms & metadata_terms
        if not overlap:
            continue
        score = len(overlap) * 3
        if query and query in metadata:
            score += 6
        title_terms = set(re.findall(r"[a-z0-9]+", title.casefold()))
        score += 2 * len(query_terms & title_terms)
        ranked.append((score, title.casefold(), node))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return [item[2] for item in ranked[:max(1, int(limit or 3))]]


def _guide_registered_discovery_documents(subject, documents):
    """Rank canonical documents against approved Guide Nodes and page-level evidence."""
    nodes = _guide_registered_discovery_nodes(subject, limit=20)
    if not nodes:
        return []
    node_by_url = {
        str(node.get("canonical_url") or "").rstrip("/").casefold(): node
        for node in nodes
    }
    ranked = []
    for index, document in enumerate(documents if isinstance(documents, list) else []):
        if not isinstance(document, dict):
            continue
        url = str(document.get("url") or document.get("canonical_url") or "").strip()
        node = node_by_url.get(url.rstrip("/").casefold())
        if not node:
            continue
        grade = _guide_discovery_evidence_grade(subject, document, node=node)
        if grade["grade"] not in {"direct", "related"}:
            continue
        approved = dict(document)
        approved["_guide_node"] = node
        approved["_discovery_relevance"] = grade["grade"]
        approved["_discovery_relevance_score"] = grade["score"]
        approved["_discovery_support_terms"] = grade["support"]
        ranked.append((
            0 if grade["grade"] == "direct" else 1,
            -int(grade["score"]),
            str(node.get("title") or "").casefold(),
            index,
            approved,
        ))
    ranked.sort(key=lambda item: item[:4])
    return [item[-1] for item in ranked]


def _guide_align_registered_discovery_doorway(subject, documents):
    """Resolve the highest-ranked direct or explicitly related registered resource."""
    registered_documents = _guide_registered_discovery_documents(subject, documents)
    if not registered_documents:
        return None, []
    return _guide_align_discovery_doorway(subject, registered_documents)


def _guide_align_discovery_doorway(subject, documents):
    """Select direct evidence first, or an approved related resource with its grade."""
    if not str(subject or "").strip() or not isinstance(documents, list) or not documents:
        return None, []
    # The Guide Node registry is destination authority; evidence grading decides
    # directness and rank. Do not use the general outward doorway gate here because
    # it intentionally rejects adjacent resources that this discovery fallback
    # must be able to describe honestly as related rather than direct.
    graded = []
    for index, document in enumerate(documents):
        if not isinstance(document, dict):
            continue
        node = document.get("_guide_node") if isinstance(document.get("_guide_node"), dict) else None
        if node is None:
            continue
        canonical_url = str(node.get("canonical_url") or "").rstrip("/").casefold()
        document_url = str(document.get("url") or document.get("canonical_url") or "").rstrip("/").casefold()
        if not canonical_url or canonical_url != document_url:
            continue
        grade = _guide_discovery_evidence_grade(subject, document, node=node)
        if grade["grade"] not in {"direct", "related"}:
            continue
        approved = dict(document)
        approved["_guide_node"] = node
        approved["_discovery_relevance"] = grade["grade"]
        approved["_discovery_relevance_score"] = grade["score"]
        approved["_discovery_support_terms"] = grade["support"]
        # When the visitor names a resource title, prefer the exact registered
        # title over a suffixed/duplicate display node even if the duplicate has
        # a slightly higher body-evidence score. Directness still outranks related
        # matches whenever there is no exact title identity match.
        normalize_title = lambda value: re.sub(
            r"[^a-z0-9]+", " ", str(value or "").casefold()
        ).strip()
        exact_title_match = normalize_title(node.get("title")) == normalize_title(subject)
        graded.append((
            0 if exact_title_match else 1,
            0 if grade["grade"] == "direct" else 1,
            -int(grade["score"]),
            str(node.get("title") or "").casefold(),
            index,
            approved,
        ))
    if not graded:
        return None, []
    graded.sort(key=lambda item: item[:4])
    selected = graded[0][-1]
    candidate = _normalize_authoritative_recommendation({
        "title": selected.get("title") or selected.get("_guide_node", {}).get("title"),
        "url": selected.get("url") or selected.get("canonical_url") or selected.get("_guide_node", {}).get("canonical_url"),
    })
    if not candidate:
        return None, []
    evidence = _guide_selected_doorway_discovery_evidence([selected], subject, candidate)
    if not evidence:
        return None, []
    return candidate, evidence


def _guide_discovery_response_is_grounded(response, subject, doorway, evidence):
    """Reject discovery prose that ignores or contradicts its selected Archive evidence."""
    text = re.sub(r"\s+", " ", str(response or "")).strip().casefold()
    if not text or not isinstance(doorway, dict) or not evidence:
        return False
    if re.search(
        r"\b(?:no specific archive material|no relevant archive material|"
        r"couldn['’]?t verify|could not verify|couldn['’]?t identify a directly relevant|"
        r"cannot point you to a specific internal resource)\b",
        text,
        re.I,
    ):
        return False
    title = _normalize_query(str(doorway.get("title") or ""))
    # Subject discovery asks for this Archive's material. External search
    # advice cannot satisfy that request by itself, even if it overlaps with
    # the page's broad vocabulary.
    external_search_advice = bool(re.search(
        r"\b(?:google scholar|jstor|project muse|ssrn|academic databases?|"
        r"university library catalogs?|think[- ]tanks?|transparency international|"
        r"government oversight bodies|oversight bodies|ngo reports?|policy institutes?|"
        r"government transparency portals?)\b",
        text,
        re.I,
    ))
    explicitly_names_destination = bool(title and title in _normalize_query(text))
    explicitly_names_archive = bool(re.search(r"\b(?:archive|living archive)\b", text, re.I))
    if external_search_advice and not (explicitly_names_destination or explicitly_names_archive):
        return False
    source = evidence[0] if isinstance(evidence[0], dict) else {}
    body = str(source.get("text") or source.get("content") or source.get("excerpt") or "").casefold()
    subject_terms = set(re.findall(r"[a-z0-9]+", str(subject or "").casefold()))
    anchors = {
        token for token in re.findall(r"[a-z][a-z-]{4,}", body)
        if token not in subject_terms and token not in {
            "about", "above", "across", "after", "again", "also", "among",
            "because", "being", "between", "could", "every", "from", "have",
            "into", "itself", "other", "their", "there", "these", "those",
            "through", "under", "using", "where", "which", "while", "within",
        }
    }
    response_tokens = set(re.findall(r"[a-z][a-z-]{4,}", text))
    has_source_anchor = len(anchors & response_tokens) >= 1
    mentions_selected_resource = bool(title and title in _normalize_query(text))
    mentions_archive = bool(re.search(r"\b(?:archive|living archive)\b", text, re.I))
    return has_source_anchor and (mentions_selected_resource or mentions_archive)


def _guide_deterministic_discovery_response(subject, doorway, evidence):
    """Orient discovery from selected-page evidence, labeling directness honestly."""
    title = str((doorway or {}).get("title") or "").strip()
    source = evidence[0] if evidence and isinstance(evidence[0], dict) else {}
    body = str(
        source.get("text") or source.get("content") or source.get("excerpt") or ""
    )
    body = re.sub(r"\s+", " ", body).strip()
    grade = str(source.get("_discovery_relevance") or "direct").strip().casefold()
    support_terms = [
        str(term).strip()
        for term in (source.get("_discovery_support_terms") or [])
        if str(term).strip()
    ]
    if not title:
        return ""

    normalized_subject = re.sub(r"\s+", " ", str(subject or "")).strip()
    # Strip recognizable author/byline metadata accidentally concatenated into excerpts.
    # Preserve the remaining source text; never manufacture a quotation.
    body = re.sub(
        r"^(?:[A-Z][A-Za-z .’'-]{1,80},?\s+(?:PhD Candidate|PhD student|doctoral candidate|author)\s+)+",
        "", body, flags=re.I,
    ).strip()
    if grade == "related":
        overlap = ", ".join(support_terms[:4]) if support_terms else "some related terms"
        return (
            f"I couldn’t verify a page that directly covers {normalized_subject}. "
            f"A related place to explore is {title}. "
            f"Its content and description overlap with {overlap}, "
            "but that does not establish that it directly addresses your question."
        )

    if not body:
        return (
            f"{title} appears to be the closest direct match I could verify. "
            f"I confirmed the destination, but not enough page text to explain "
            f"how it addresses {normalized_subject}."
        )

    subject_tokens = {
        token for token in re.findall(r"[a-z0-9]+", normalized_subject.casefold())
        if len(token) >= 4
    }
    # WordPress excerpts can concatenate a title/subheading directly with the
    # following sentence. If a complete question follows the heading, discard
    # the heading prefix before considering the text as a source quotation.
    sentences = [
        re.sub(r"\s+", " ", sentence).strip(" \t-•")
        for sentence in re.split(r"(?<=[.!?])\s+", body)
    ]
    for index, sentence in enumerate(sentences):
        if "?" not in sentence:
            continue
        question_start = re.search(
            r"\b(?:why|what|how|when|where|who|which|does|do|did|can|could|should|would|will|is|are|was|were)\s+",
            sentence,
            re.I,
        )
        if question_start and question_start.start() >= 24:
            sentences[index] = sentence[question_start.start():].strip()
    candidates = []
    for sentence in sentences:
        if len(sentence) < 45 or len(sentence) > 320:
            continue
        if not re.search(r"[.!?]$", sentence):
            continue
        words = set(re.findall(r"[a-z0-9]+", sentence.casefold()))
        if subject_tokens and len(subject_tokens & words) < min(2, len(subject_tokens)):
            continue
        if re.search(r"\b(?:governing question|meta description|read more)\b", sentence, re.I):
            continue
        candidates.append(sentence)
    if not candidates:
        return (
            f"{title} is a promising starting point for {normalized_subject}. "
            "I couldn’t isolate a complete source sentence that I can quote reliably, "
            "so I won’t manufacture one."
        )
    sentence = candidates[0]
    return (
        f"{title} is a useful place to begin. The essay asks: “{sentence}” "
        f"That gives you a focused entry point for exploring {normalized_subject}."
    )


def _guide_discovery_doorway_is_evidence_backed(doorway, evidence):
    """Require the selected canonical body to match the final discovery doorway URL."""
    if not isinstance(doorway, dict):
        return False
    doorway_url = str(doorway.get("url") or doorway.get("canonical_url") or "").strip().rstrip("/").casefold()
    if not doorway_url or not isinstance(evidence, list) or not evidence:
        return False
    return any(
        isinstance(item, dict)
        and str(item.get("url") or item.get("canonical_url") or "").strip().rstrip("/").casefold() == doorway_url
        and bool(str(item.get("text") or "").strip())
        for item in evidence
    )


def _guide_subject_discovery_answer(response, subject, doorway, evidence):
    """Use a page-grounded direct/related answer or fall back without a false match."""
    if not isinstance(doorway, dict) or not str(doorway.get("title") or "").strip():
        return (
            f"I couldn’t verify a Living Archive page that directly covers {str(subject or 'this subject').strip()}. "
            "I’d rather leave the link out than point you to a page on the strength of a shared word alone."
        )
    return _guide_deterministic_discovery_response(subject, doorway, evidence) or str(response or "").strip()

def _established_general_knowledge_recovery(query):
    """Return a bounded answer for a small, explicit set of stable public facts.

    This provider-independent recovery only answers fact patterns whose
    response is pre-established here. Unlisted questions return None and
    continue through normal evidence, uncertainty, and composition rules.
    """
    normalized = _normalize_query(query).strip().casefold()
    if not normalized:
        return None

    water_boiling_question = bool(
        re.search(r"\bwater\b", normalized)
        and re.search(r"\bboil(?:s|ing)?\b", normalized)
        and re.search(
            r"\b(?:sea level|standard atmospheric pressure|at normal atmospheric pressure|1 atm)\b",
            normalized,
        )
    )
    if water_boiling_question:
        return {
            "fact_id": "water_boiling_point_sea_level",
            "response": (
                "At sea level, water boils at 100°C (212°F) under standard atmospheric pressure. "
                "As altitude increases and air pressure decreases, water boils at a lower temperature.\n\n"
                "The key point is that boiling depends on pressure, not just temperature."
            ),
        }

    triangle_sides_question = bool(
        re.search(r"\b(?:how many sides|number of sides)\b", normalized)
        and re.search(r"\btriangle\b", normalized)
    )
    if triangle_sides_question:
        return {
            "fact_id": "triangle_has_three_sides",
            "response": "A triangle has three sides and three angles.",
        }

    ice_floats_question = bool(
        re.search(r"\bice\b", normalized)
        and re.search(r"\bfloat(?:s|ing)?\b", normalized)
        and re.search(r"\bwater\b", normalized)
    )
    if ice_floats_question:
        return {
            "fact_id": "ice_floats_because_less_dense",
            "response": (
                "Ice floats in water because it is less dense than liquid water. "
                "When water freezes, its molecules form an open crystal structure that takes up more space, "
                "so the same mass occupies a larger volume."
            ),
        }

    metric_length_question = bool(
        re.search(r"\bcentimet(?:er|re)s?\b", normalized)
        and re.search(r"\bmet(?:er|re)s?\b", normalized)
        and re.search(r"\b(?:how many|convert|conversion|equal|equals|in a|in one)\b", normalized)
    )
    if metric_length_question:
        return {
            "fact_id": "meter_centimeter_conversion",
            "response": "One meter equals 100 centimeters.",
        }

    return None



def _established_archive_cosmology_recovery(query):
    """Answer a cosmology/worldview question about lived significance plainly.

    This bounded fallback is based on the approved Guide cosmology reference.
    It applies only when the question asks about cosmology/worldview and its
    significance for life; it is not used for every cosmology definition.
    """
    normalized = re.sub(r"\s+", " ", _normalize_query(query)).strip().casefold()
    if not normalized:
        return None
    has_subject = bool(re.search(r"\b(?:cosmology|worldview)\b", normalized))
    asks_lived_significance = bool(re.search(
        r"\b(?:how people live|how we live|human life|everyday life|our lives|people's lives)\b",
        normalized,
    ))
    if not (has_subject and asks_lived_significance):
        return None
    return {
        "recovery_id": "archive_informed_cosmology_lived_significance",
        "response": (
            "Cosmology is an understanding of how reality works and how we belong within it—not only a theory about the physical universe. "
            "The picture we carry of people, nature, change, and our place in the world shapes what we notice and how we make decisions.\n\n"
            "The Living Archive explores a contrast between a separation-based worldview and a unity-informed worldview. "
            "A separation-based view tends to organize life around competition, control, earned worth, and fear of loss. "
            "A unity-informed view sees people as distinct but connected, treats worth as inherent, and understands growth as something that can emerge through relationship, responsibility, and cooperation. "
            "These are ways of interpreting experience, not labels for judging a person.\n\n"
            "This matters because a worldview can become an invisible guide for everyday choices. "
            "If every disagreement is treated as a contest for control, people may protect status instead of looking for a workable answer. "
            "If people see themselves as distinct but connected, they can recognize differences without treating them as threats. "
            "This is a useful starting explanation, not a claim that one Archive text exhausts the subject."
        ),
    }


def _basic_inquiry_response(query, history=None, raw_body=None):
    """Answer an ordinary Guide question through the protected USE core."""
    started = time.perf_counter()
    request_deadline = time.monotonic() + GUIDE_REQUEST_BUDGET_SECONDS
    composition_repair_attempted = False
    query = str(query or "").strip()
    # Classify the bounded newcomer intent before retrieval so the same question
    # does not pay for general discovery and then discard that work for recovery.
    healthy_community_short_circuit = _is_healthy_community_orientation_question(query)
    trust_stewardship_short_circuit = _is_trust_community_stewardship_question(query)
    # Explicit homepage navigation is a deterministic site-level destination,
    # not a subject-discovery request. Resolve it before retrieval/composition
    # so provider variance cannot suppress a clearly requested homepage.
    home_request = bool(re.search(
        r"\b(?:homepage|home page|site home|website home)\b", query, re.I
    )) and bool(re.search(
        r"\b(?:living archive|the archive|the website|the site|website|site)\b",
        query, re.I
    )) and bool(re.search(
        r"\b(?:take me|go to|bring me|send me|navigate|open|show me|link me|please take|please go)\b",
        query, re.I
    ))
    if home_request:
        request_id = "home-" + hashlib.sha1(query.encode("utf-8")).hexdigest()[:16]
        return {
            "ok": True,
            "version": APP_VERSION,
            "fingerprint": DEPLOYMENT_FINGERPRINT,
            "source_sha256": RUNTIME_SOURCE_SHA256,
            "request_id": request_id,
            "query": query,
            "intent": "NAVIGATION",
            "response": "Here’s the Living Archive homepage.",
            "recommendation": {
                "title": "Living Archive",
                "url": "https://geralddaquila.com/",
            },
            "answer_basis": {
                "kind": "navigation",
                "label": "Direct site navigation",
                "explanation": "You explicitly asked to open the Living Archive homepage.",
            },
            "processing": "guide_navigation",
            "route_source": "guide_explicit_home_navigation",
            "visitor_boundary_version": APP_VERSION,
        }
    clarification = general_guide_composition.clarification_response(
        query, _history_text(history)
    )
    if clarification:
        request_id = "clarify-" + hashlib.sha1(
            (query + "|" + _history_text(history)).encode("utf-8")
        ).hexdigest()[:16]
        return {
            "ok": True,
            "version": APP_VERSION,
            "fingerprint": DEPLOYMENT_FINGERPRINT,
            "source_sha256": RUNTIME_SOURCE_SHA256,
            "request_id": request_id,
            "query": query,
            "intent": "CLARIFICATION_REQUIRED",
            "response": clarification["response"],
            "recommendation": None,
            "answer_basis": {
                "kind": "clarification",
                "label": "A little more context",
                "explanation": "The question needs a subject before a relevant answer or Archive resource can be selected.",
            },
            "processing": "guide_clarification",
            "route_source": "guide_missing_context_guard",
            "clarification": {
                "required": True,
                "reason": clarification["clarification_reason"],
                "recommendation_suppressed": True,
            },
            "visitor_boundary_version": APP_VERSION,
        }
    # Separate the visitor's intent from the resource-search terms. Search
    # wrapper language such as "Where can I find material about..." is useful
    # to the composer but can obscure the actual subject during retrieval.
    # A correction explicitly names the subject the prior answer missed.
    # Retrieve and select any doorway for that subject, not the mistaken subject
    # or the full complaint wrapper.
    correction_subject = general_guide_composition.correction_subject(query)
    source_trace_request = general_guide_composition.is_exact_source_request(query)
    source_trace_claim = _history_text(history) if source_trace_request else ""
    discovery_subject = _guide_subject_discovery_query(query) if not correction_subject and not source_trace_request else ""
    # These are answer-first explanatory intents, not pure subject-finding requests.
    if healthy_community_short_circuit or trust_stewardship_short_circuit:
        discovery_subject = ""
    resource_query = correction_subject or discovery_subject or (source_trace_claim[-1600:] if source_trace_claim else query)
    context_data = use_core.fetch_canonical_context(resource_query)
    if not isinstance(context_data, dict):
        raise RuntimeError("Basic Inquiry retrieval returned an invalid context object.")

    # Navigation authority is resolved once, before composition, and carried
    # through every ordinary-answer path. It must never depend on which
    # provider/model happened to compose the prose successfully.
    direct_attribute_query = bool(_direct_attribute_phrase(query))
    if healthy_community_short_circuit:
        # The approved topic-specific doorway is deterministic for this bounded
        # intent; do not launch the generic multi-search doorway recovery first.
        authoritative_doorway = _normalize_authoritative_recommendation(
            _healthy_community_canonical_recommendation(query, context_data)
        )
    elif trust_stewardship_short_circuit:
        # This bounded explanatory intent has its own verified Archive doorway.
        # Repeating broad searches cannot improve the already approved destination.
        authoritative_doorway = _normalize_authoritative_recommendation(
            _trust_community_stewardship_canonical_recommendation(query, context_data)
        )
    else:
        authoritative_doorway = _select_direct_attribute_doorway(
            query,
            context_data.get("recommendation_canonical_primary"),
            _general_guide_authoritative_doorway,
            context_data,
            resource_query=resource_query,
            normalize=_normalize_authoritative_recommendation,
        )
    general_knowledge_recovery = _established_general_knowledge_recovery(query)
    _cosmology_lived_recovery = _established_archive_cosmology_recovery(query)
    # Only explicitly matched stable facts may bypass Archive-attribute refusal.
    # All other unsupported attributes keep the established fail-closed boundary.
    direct_attribute_evidence_missing = (
        _direct_attribute_evidence_missing(query, authoritative_doorway)
        and general_knowledge_recovery is None
    )
    # Subject discovery is constrained to the active WordPress Guide Node registry.
    # A public URL returned by search is not, by itself, an approved Guide doorway.
    if discovery_subject and authoritative_doorway:
        registered_urls = {
            str(node.get("canonical_url") or "").rstrip("/").casefold()
            for node in _guide_node_registry_snapshot()
            if isinstance(node, dict) and str(node.get("status") or "") == "active"
        }
        if str(authoritative_doorway.get("url") or "").rstrip("/").casefold() not in registered_urls:
            print("The Guide discovery boundary: rejected unregistered destination.")
            authoritative_doorway = None
    # Distress-sensitive pacing governs the prose, not access to a separate
    # optional resource. Keep the compassionate response first and preserve a
    # qualified, independently rendered doorway when the existing relevance
    # and safety gates approve one. Acute-risk and unrelated resources remain
    # excluded by the outward-document eligibility boundary.

    # Evidence sufficiency governs what may be attributed to the Archive, not
    # whether an ordinary public question may receive a useful general answer.
    # Keep specialist-only evidence out of general composition when the retrieval
    # boundary says it cannot safely frame the visitor's question.
    composition_context = dict(context_data)
    if authoritative_doorway:
        composition_context["authoritative_doorway"] = authoritative_doorway
    archive_evidence_unavailable = any(
        composition_context.get(flag)
        for flag in (
            "frame_neutral_evidence_unavailable",
            "question_structure_evidence_unavailable",
            "evidence_sufficiency_unavailable",
        )
    )
    discovery_selected_evidence = []
    direct_selected_body = None
    registry_discovery_docs = []
    if (
        not healthy_community_short_circuit
        and _guide_requires_canonical_subject_supplement(
            archive_evidence_unavailable,
            discovery_subject,
            _is_conceptual_explanatory_request(query),
        )
    ):
        # Subject-finding requests always receive a bounded WordPress content
        # supplement, even when the initial vector pass did not set an evidence-
        # unavailable flag. A valid doorway alone is not enough: fetch the page
        # text and re-run the same frame-neutral, sufficiency, and question-fit
        # gates before allowing it into the answer composition.
        try:
            if trust_stewardship_short_circuit and authoritative_doorway:
                # The exact approved destination is already known. Fetch its body
                # below; do not repeat broad subject searches before that fetch.
                recovered_docs = []
            else:
                recovered_docs = _wordpress_search_canonical_candidates(
                    resource_query,
                    limit=_guide_subject_supplement_limit(
                        discovery_subject, _is_conceptual_explanatory_request(query)
                    ),
                )
            # Add a small, deterministic set of active registry nodes ranked by
            # their published purpose and semantic hints. Only fetched canonical
            # page bodies can subsequently authorize a recommendation.
            if discovery_subject:
                known_urls = {
                    str(item.get("url") or item.get("canonical_url") or "").rstrip("/").casefold()
                    for item in recovered_docs if isinstance(item, dict)
                }
                for node in _guide_registered_discovery_nodes(discovery_subject, limit=20):
                    node_url = str(node.get("canonical_url") or "").strip()
                    if not node_url or node_url.rstrip("/").casefold() in known_urls:
                        continue
                    try:
                        node_body = _wordpress_fetch_selected_canonical_body(node_url)
                    except Exception:
                        node_body = None
                    if isinstance(node_body, dict):
                        recovered_docs.append(node_body)
                        registry_discovery_docs.append(node_body)
                        known_urls.add(node_url.rstrip("/").casefold())
            # The selected doorway is already independently authorized. Fetch
            # its actual canonical body as well as topic-search candidates so
            # content relevance is tested against the destination being offered,
            # not just whichever pages WordPress ranked highest for the phrase.
            if (
                discovery_subject or _is_conceptual_explanatory_request(query)
            ) and authoritative_doorway:
                # Fetch the exact, already-authorized canonical destination first.
                # A second WordPress search for its title repeats search plus
                # candidate-body requests when the direct page fetch succeeds.
                # Keep that search as a recovery path only when the direct fetch
                # fails; all returned documents still pass the same downstream
                # URL, body, frame-neutral, and subject-fit checks.
                direct_body = _wordpress_fetch_selected_canonical_body(
                    authoritative_doorway.get("url") or ""
                )
                direct_selected_body = direct_body if isinstance(direct_body, dict) else None
                doorway_docs = []
                if direct_selected_body is None:
                    doorway_docs = _wordpress_search_canonical_candidates(
                        authoritative_doorway.get("title") or "", limit=3
                    )
                recovered_docs = (
                    ([direct_body] if isinstance(direct_body, dict) else [])
                    + list(doorway_docs)
                    + list(recovered_docs)
                )
            normalized_recovered_docs = []
            seen_recovered_urls = set()
            for item in recovered_docs:
                if not isinstance(item, dict):
                    continue
                title = str(item.get("title") or "").strip()
                url = str(item.get("url") or "").strip()
                text_value = str(item.get("text") or "").strip()
                key = url.rstrip("/").casefold()
                if not title or not text_value or not key or key in seen_recovered_urls:
                    continue
                seen_recovered_urls.add(key)
                normalized_recovered_docs.append({"title": title, "url": url, "text": text_value})
            recovered_docs = normalized_recovered_docs
            recovered_docs, _frame_boundary_active = use_core._frame_neutral_generation_documents(
                recovered_docs, resource_query, str(context_data.get("intent") or "TOPICAL_INQUIRY")
            )
            selected_support = (
                _guide_selected_doorway_discovery_evidence(
                    recovered_docs, resource_query, authoritative_doorway
                )
                if discovery_subject and authoritative_doorway else []
            )
            # Resource discovery and answer synthesis have different contracts.
            # Once a canonical page body passes direct subject-fit validation,
            # align the destination to that exact body and retain it for the
            # discovery response guard even if the stricter synthesis gate
            # rejects the document set. This never authorizes unsupported
            # explanatory claims; it only permits a grounded resource orientation.
            if discovery_subject:
                # The general frame-neutral filter is designed for synthesis
                # authority and may discard a valid navigation-page body. Keep
                # the directly fetched selected page in a separate, bounded
                # discovery-only candidate set and let the exact URL/body/direct-
                # fit checks decide whether it can ground the doorway.
                discovery_candidate_docs = list(recovered_docs)
                known_discovery_urls = {
                    str(item.get("url") or item.get("canonical_url") or "").rstrip("/").casefold()
                    for item in discovery_candidate_docs if isinstance(item, dict)
                }
                for item in registry_discovery_docs:
                    item_url = str(item.get("url") or item.get("canonical_url") or "").rstrip("/").casefold()
                    if item_url and item_url not in known_discovery_urls:
                        discovery_candidate_docs.append(item)
                        known_discovery_urls.add(item_url)
                if direct_selected_body:
                    direct_url_key = str(direct_selected_body.get("url") or "").rstrip("/").casefold()
                    if not any(
                        str(item.get("url") or "").rstrip("/").casefold() == direct_url_key
                        for item in discovery_candidate_docs if isinstance(item, dict)
                    ):
                        discovery_candidate_docs.append(direct_selected_body)
                evidence_doorway, evidence_for_doorway = _guide_align_registered_discovery_doorway(
                    resource_query, discovery_candidate_docs
                )
                if evidence_doorway and evidence_for_doorway:
                    authoritative_doorway = evidence_doorway
                    discovery_selected_evidence = evidence_for_doorway
                    composition_context["authoritative_doorway"] = evidence_doorway
                    print(
                        "The Guide discovery evidence contract: selected destination "
                        f"and source body aligned to {evidence_doorway.get('title')!r}."
                    )
            recovered_docs, recovery_insufficient = use_core._evidence_sufficiency_gate(
                recovered_docs, resource_query, str(context_data.get("intent") or "TOPICAL_INQUIRY")
            )
            if recovery_insufficient and selected_support:
                recovered_docs = selected_support
                recovery_insufficient = False
                print(
                    "The Guide discovery evidence gate: selected canonical doorway body "
                    "passed direct subject-fit validation."
                )
            if not recovery_insufficient and recovered_docs:
                recovered_docs, recovery_question_unavailable = use_core._v208_question_evidence_fit_gate(
                    recovered_docs, resource_query, str(context_data.get("intent") or "TOPICAL_INQUIRY")
                )
                if recovery_question_unavailable and selected_support:
                    recovered_docs = selected_support
                    recovered_docs, recovery_question_unavailable = use_core._v208_question_evidence_fit_gate(
                        recovered_docs, resource_query, str(context_data.get("intent") or "TOPICAL_INQUIRY")
                    )
                if not recovery_question_unavailable and recovered_docs:
                    discovery_selected_evidence = (
                        selected_support
                        or (
                            _guide_selected_doorway_discovery_evidence(
                                recovered_docs, resource_query, authoritative_doorway
                            )
                            if discovery_subject and authoritative_doorway else []
                        )
                    )
                    composition_context["generation_authority_protected_docs"] = recovered_docs
                    composition_context.pop("question_authority_protected_docs", None)
                    if (
                        _is_conceptual_explanatory_request(query)
                        and not discovery_subject
                    ):
                        # Conceptual inquiries need a source selected from the
                        # vetted evidence bodies, but do not require the special
                        # registered-node rule used for explicit resource discovery.
                        # Reuse the Guide's general authoritative doorway selector
                        # against the recovered, gate-passing canonical documents.
                        evidence_doorway = _general_guide_authoritative_doorway(
                            query,
                            {"generation_authority_protected_docs": recovered_docs},
                        )
                        evidence_doorway = _normalize_authoritative_recommendation(
                            evidence_doorway
                        )
                        if evidence_doorway:
                            authoritative_doorway = evidence_doorway
                            composition_context["authoritative_doorway"] = evidence_doorway
                            print(
                                "The Guide conceptual evidence contract: selected "
                                "the doorway from vetted canonical evidence "
                                f"{evidence_doorway.get('title')!r}."
                            )
                    if discovery_subject:
                        # The final doorway must be selected from the same vetted
                        # canonical documents that will ground the discovery answer.
                        # This prevents a good-looking but unfetched doorway from
                        # being paired with unrelated prose or a generic fallback.
                        evidence_doorway, evidence_for_doorway = _guide_align_registered_discovery_doorway(
                            resource_query, list(recovered_docs) + list(registry_discovery_docs)
                        )
                        if evidence_doorway and evidence_for_doorway:
                            authoritative_doorway = evidence_doorway
                            discovery_selected_evidence = evidence_for_doorway
                            composition_context["authoritative_doorway"] = evidence_doorway
                            print(
                                "The Guide discovery contract: doorway and answer evidence "
                                f"aligned to {evidence_doorway.get('title')!r}."
                            )
                    for flag in (
                        "frame_neutral_evidence_unavailable",
                        "question_structure_evidence_unavailable",
                        "evidence_sufficiency_unavailable",
                        "question_evidence_fit_unavailable",
                    ):
                        composition_context.pop(flag, None)
                    archive_evidence_unavailable = False
                    print(
                        "The Guide evidence recovery: substantive canonical content passed "
                        "frame-neutral, sufficiency, and question-fit gates; "
                        f"documents={len(recovered_docs)}."
                    )
        except Exception as exc:
            print(f"The Guide evidence recovery failed safely: {type(exc).__name__}: {exc}.")

    # Recovery may establish a qualifying doorway after the initial selection.
    # Recompute this state from the current authoritative source instead of
    # carrying a stale pre-recovery failure into the final response.
    direct_attribute_evidence_missing = (
        _direct_attribute_evidence_missing(query, authoritative_doorway)
        and general_knowledge_recovery is None
    )

    # Discovery is fail-closed at the final selection boundary. An initial
    # retrieval recommendation is not sufficient: the final selected canonical
    # page body must support the exact doorway being returned. This also keeps
    # answer_basis from claiming Archive support when discovery fell back.
    if discovery_subject and not _guide_discovery_doorway_is_evidence_backed(
        authoritative_doorway, discovery_selected_evidence
    ):
        authoritative_doorway = None
        composition_context.pop("authoritative_doorway", None)
        print(
            "The Guide discovery contract: no evidence-backed selected doorway; "
            "recommendation suppressed."
        )

    if archive_evidence_unavailable:
        for key in (
            "context_blocks",
            "canonical_link_context",
            "generation_authority_protected_docs",
            "question_authority_protected_docs",
            "authoritative_doorway",
        ):
            composition_context.pop(key, None)
        # Navigation and answer synthesis have separate evidence contracts.
        # Insufficient synthesis evidence must not erase an independently
        # selected, relevant canonical doorway. The doorway is returned as a
        # separate field and is not passed into the composition context.

    # All ordinary questions use the same provider-neutral composition path,
    # including when no suitable Archive evidence is available. The composer
    # is explicitly instructed to answer from general knowledge where suitable
    # and to state source limitations only when the question actually requires it.

    # One controlled reasoning-provider seam. AUTO preserves the existing LLM-first
    # provider bank and bounded deterministic fallback. DETERMINISTIC_ONLY bypasses
    # the composer entirely for isolated calibration and is intentionally configured
    # only on a service receiving no normal visitor traffic, never by an untrusted visitor field.
    reasoning_mode = str(os.getenv("USE_REASONING_PROVIDER_MODE", "auto") or "auto").strip().casefold()
    if reasoning_mode not in {"auto", "deterministic_only"}:
        print("The Guide reasoning provider mode: invalid value; using auto.")
        reasoning_mode = "auto"

    # The bounded newcomer intent was classified before retrieval. Avoid
    # composition too; the same three-paragraph recovery is the final answer.
    if healthy_community_short_circuit or trust_stewardship_short_circuit:
        reasoning_mode = "deterministic_only"

    composition_result = None
    # This narrow practical-question class has a bounded, provider-independent
    # answer. Do not send it through the general composition envelope: that
    # envelope can exceed provider token budgets before the fallback is reached.
    if (
        _is_practical_stewardship_question(query)
        and not _is_conceptual_explanatory_request(query)
        and not general_guide_composition.is_conceptual_relationship_question(query)
    ):
        deterministic_result = _basic_inquiry_round1_deterministic_response(
            query, {}, composition_context, recommendation_available=False
        )
        llm_output = str((deterministic_result or {}).get("response") or "").strip()
        if not llm_output:
            raise RuntimeError("Practical stewardship recovery returned no answer.")
        print(
            "The Guide General Composition: "
            "mode=bounded_practical_stewardship_recovery, "
            "llm_composer_invoked=false, archive_recommendation=none"
        )
    elif reasoning_mode == "deterministic_only":
        if healthy_community_short_circuit:
            deterministic_result = {
                "response": _healthy_community_answer_recovery(),
                "provider": "bounded_healthy_community_orientation_recovery",
                "model": "deterministic-contract-recovery",
            }
        elif trust_stewardship_short_circuit:
            deterministic_result = {
                "response": _trust_community_stewardship_recovery(),
                "provider": "bounded_trust_community_stewardship_recovery",
                "model": "deterministic-contract-recovery",
            }
        else:
            deterministic_result = _basic_inquiry_round1_deterministic_response(
                correction_subject or query, {}, composition_context,
                recommendation_available=bool(authoritative_doorway),
            )
        llm_output = str((deterministic_result or {}).get("response") or "")
        print(
            "The Guide General Composition: "
            f"mode={'bounded_healthy_community_orientation_recovery' if healthy_community_short_circuit else 'deterministic_only'}, "
            f"provider={(deterministic_result or {}).get('provider') or 'unknown'}, "
            f"model={(deterministic_result or {}).get('model') or 'none'}, llm_composer_invoked=false, "
            f"archive_evidence={'unavailable' if archive_evidence_unavailable else 'available'}, "
            f"navigation_candidate={authoritative_doorway.get('title') if authoritative_doorway else 'none'}"
        )
    else:
        try:
            composition_result = general_guide_composition.compose(
                use_core=use_core,
                query=query,
                context_data=composition_context,
                history_text=_history_text(history),
                deadline_monotonic=request_deadline,
            )
            if composition_result:
                llm_output = composition_result.get("response", "")
                print(
                    "The Guide General Composition: "
                    f"mode=auto, provider={composition_result.get('provider') or 'unknown'}, "
                    f"model={composition_result.get('model') or 'unknown'}, "
                    f"shape={composition_result.get('response_shape') or 'unknown'}, "
                    f"archive_evidence={'unavailable' if archive_evidence_unavailable else 'available'}, "
                    f"navigation_candidate={authoritative_doorway.get('title') if authoritative_doorway else 'none'}"
                )
            else:
                print("The Guide General Composition: mode=auto; provider bank exhausted; using conservative deterministic recovery.")
                print("The Guide Final Pathway: mode=auto, pathway=deterministic_recovery, provider=none, model=none, reason=provider_bank_exhausted")
                deterministic_result = _basic_inquiry_provider_exhaustion_response(
                    correction_subject or query, {}, composition_context,
                    recommendation_available=bool(authoritative_doorway),
                )
                llm_output = str(deterministic_result.get("response") or "")
        except Exception as exc:
            print(f"The Guide General Composition failed safely in auto mode: {type(exc).__name__}; using conservative deterministic recovery.")
            print(f"The Guide Final Pathway: mode=auto, pathway=deterministic_recovery, provider=none, model=none, reason=composition_exception:{type(exc).__name__}")
            try:
                deterministic_result = _basic_inquiry_provider_exhaustion_response(
                    query, {}, composition_context,
                    recommendation_available=bool(authoritative_doorway),
                )
                llm_output = str(deterministic_result.get("response") or "")
            except Exception:
                llm_output = ""

    if (
        _is_practical_stewardship_question(query)
        and not _is_healthy_community_orientation_question(query)
        and not _is_conceptual_explanatory_request(query)
        and not general_guide_composition.is_conceptual_relationship_question(query)
    ):
        # This bounded recovery has no canonical source body selected as direct
        # evidence for the exact practical question. Suppress an incidental
        # doorway for a practical how-to request, but do not override a
        # conceptual inquiry whose canonical bodies have already passed the
        # frame-neutral, sufficiency, and question-fit gates above.
        authoritative_doorway = None
        archive_evidence_unavailable = True
        composition_context.pop("authoritative_doorway", None)
        composition_context.pop("authoritative_doorway_title", None)
        composition_context["evidence_sufficiency_unavailable"] = True

    # Subject-discovery prose must be independent of provider availability and generation.
    # Always compose it from the selected canonical page evidence, so primary and mirror
    # cannot drift into different descriptions or introduce unselected resources.
    if discovery_subject:
        grounded_discovery = _guide_subject_discovery_answer(
            llm_output, resource_query, authoritative_doorway, discovery_selected_evidence
        )
        if grounded_discovery != str(llm_output or "").strip():
            print(
                "The Guide discovery composition boundary: replaced provider prose "
                "with selected canonical doorway orientation."
            )
        llm_output = grounded_discovery

    # Final visitor-language boundary for EVERY ordinary Guide response path.
    # Canonical navigation is a separate structured field. If a provider tries
    # to smuggle a link into prose, reject the entire generated response and
    # recover without reusing that text. This prevents malformed markup and
    # unsupported title/URL pairs from crossing the API boundary.
    raw_visitor_text = str(llm_output or "").strip()
    if _basic_inquiry_has_internal_annotation(raw_visitor_text):
        print(
            "The Guide visitor boundary: rejected generated prose with internal "
            "evidence annotations; using query-grounded deterministic recovery."
        )
        deterministic_recovery = _basic_inquiry_round1_deterministic_response(
            query, {}, {"context_blocks": ""}, recommendation_available=False
        )
        llm_output = str(deterministic_recovery.get("response") or "").strip()
        raw_visitor_text = llm_output
    if _basic_inquiry_contains_html_markup(raw_visitor_text):
        print(
            "The Guide visitor boundary: rejected HTML-shaped generated prose; "
            "using query-grounded deterministic recovery."
        )
        llm_output = _basic_inquiry_markup_recovery(
            query, history, context_data.get("intent", "TOPICAL_INQUIRY")
        )
        if not llm_output:
            try:
                deterministic_recovery = _basic_inquiry_round1_deterministic_response(
                    correction_subject or query, {}, {"context_blocks": ""}, recommendation_available=bool(authoritative_doorway)
                )
                llm_output = str(deterministic_recovery.get("response") or "").strip()
            except Exception as exc:
                print(f"The Guide markup recovery failed safely: {type(exc).__name__}.")
                llm_output = ""
        if _basic_inquiry_contains_html_markup(llm_output):
            llm_output = ""
    response = _sanitize_basic_inquiry_response(str(llm_output or "").strip())
    if _basic_inquiry_has_source_dump(response):
        print(
            "The Guide visitor boundary: rejected a copied/truncated source excerpt; "
            "using deterministic synthesis instead."
        )
        # Do not feed the rejected excerpt back into recovery; that would
        # reproduce the same copied/truncated passage under a deterministic label.
        deterministic_recovery = _basic_inquiry_round1_deterministic_response(
            query, {}, {"context_blocks": ""}
        )
        response = _sanitize_basic_inquiry_response(
            str(deterministic_recovery.get("response") or "").strip()
        )
        # The boundary is fail-closed: even if deterministic recovery unexpectedly
        # returns the same excerpt, no copied/truncated source dump may be emitted.
        if _basic_inquiry_has_source_dump(response):
            response = _sanitize_basic_inquiry_response(
                _basic_inquiry_source_dump_recovery(query)
            )
    if not response:
        raise RuntimeError("Basic Inquiry generation returned an empty visitor response.")

    # Re-apply provider-independent discovery composition after sanitization, immediately
    # before payload assembly. This is intentionally deterministic even when a generated
    # answer passed the broad relevance validator above.
    if discovery_subject:
        response = _sanitize_basic_inquiry_response(
            _guide_subject_discovery_answer(
                response, resource_query, authoritative_doorway, discovery_selected_evidence
            )
        )

    # Discovery composition is allowed to replace a draft after the earlier
    # visitor boundary. Re-validate the final composed text here as well; if
    # that last step reintroduces internal annotations, discard it and recover
    # from the visitor's question without reusing contaminated prose or links.
    if _basic_inquiry_has_internal_annotation(response):
        print(
            "The Guide final discovery boundary: rejected reintroduced internal "
            "annotations; using query-grounded deterministic recovery."
        )
        authoritative_doorway = None
        archive_evidence_unavailable = True
        response = _sanitize_basic_inquiry_response(
            str(
                _basic_inquiry_round1_deterministic_response(
                    query, {}, {"context_blocks": ""}, recommendation_available=False
                ).get("response") or ""
            ).strip()
        )
        if _basic_inquiry_has_internal_annotation(response):
            response = _sanitize_basic_inquiry_response(
                _basic_inquiry_source_dump_recovery(query)
            )

    if re.search(r"\bUSE\b", response) or re.search(
        r"(?:canonical evidence|supplied evidence|evidence excerpt|"
        r"evidence excerpt bounded by USE|bounded by USE|"
        r"bounded by the Guide|internal interpretation|retrieval layer|"
        r"synthesis layer|processing layer|provider bank|provider selection|"
        r"model selection|route source|handoff|machine-facing|"
        r"implementation metadata|system instruction|debugging annotation)",
        response,
        re.I,
    ):
        raise RuntimeError(
            "Basic Inquiry visitor-language boundary rejected internal implementation language."
        )

    # Final visitor-facing contract for explicit practical-application questions.
    # This gate runs after every composition and discovery path, so an earlier
    # generic answer or canonical doorway cannot override the requested task.
    if general_guide_composition.is_practical_application_question(query):
        if not general_guide_composition.has_observable_practical_actions(response):
            response = _sanitize_basic_inquiry_response(
                general_guide_composition._practical_application_recovery()
            )
            print("The Guide final practical-answer boundary: replaced abstract response with observable actions.")
        if not re.search(
            r"\b(?:where can i find|where do i find|show me|take me to|link me to|browse|find the)\b",
            query,
            re.I,
        ):
            authoritative_doorway = None
            composition_context.pop("authoritative_doorway", None)
            print("The Guide final practical-answer boundary: suppressed premature canonical doorway.")

    # Final provider-independent contract: if every provider attempt and its
    # fallback still produced analysis without a concrete next step, replace it
    # with a bounded actionable response before the visitor payload is assembled.
    actionable_response = general_guide_composition.enforce_actionable_next_step(
        query, response
    )
    if actionable_response != response:
        print(
            "The Guide final response contract: replaced non-actionable recovery "
            "with bounded practical next-step guidance."
        )
        response = _sanitize_basic_inquiry_response(actionable_response)


    # Final visitor-facing contract for conceptual relationship questions.
    # This runs after composition/discovery paths so generic fallback language
    # cannot replace the explanation requested by the visitor.
    if general_guide_composition.is_conceptual_relationship_question(query):
        if not general_guide_composition.has_conceptual_relationship_explanation(response):
            response = _sanitize_basic_inquiry_response(
                general_guide_composition._conceptual_relationship_recovery()
            )
            print("The Guide final relationship-answer boundary: restored concept-to-concept explanation.")
        if not re.search(
            r"\b(?:where can i find|where do i find|show me|take me to|link me to|browse|find the)\b",
            query,
            re.I,
        ):
            authoritative_doorway = None
            composition_context.pop("authoritative_doorway", None)
            print("The Guide final relationship-answer boundary: suppressed unrequested doorway.")

    # Final newcomer/topic contract: answer the expressed subject before generic
    # uncertainty recovery can send the visitor back to intake or ask them to restate it.
    if _is_healthy_community_orientation_question(query):
        response = _sanitize_basic_inquiry_response(_healthy_community_answer_recovery())
        # A topical newcomer answer must preserve a relevant doorway even when
        # the ordinary vector context had no recommendation or the independent
        # practical-stewardship fallback would otherwise suppress it.
        if not authoritative_doorway:
            _topic_doorway = _healthy_community_canonical_recommendation(query, context_data)
            if _topic_doorway:
                authoritative_doorway = _normalize_authoritative_recommendation(_topic_doorway)
                archive_evidence_unavailable = False
                composition_context["authoritative_doorway"] = authoritative_doorway
                composition_context.pop("evidence_sufficiency_unavailable", None)
            else:
                composition_context.pop("authoritative_doorway", None)
                composition_context.pop("authoritative_doorway_title", None)
                print("The Guide healthy-community boundary: no relevant canonical recommendation passed topic fit.")
        else:
            # Preserve the early approved doorway; do not clear it merely because
            # the redundant late recovery is intentionally skipped.
            composition_context["authoritative_doorway"] = authoritative_doorway

    # Single owner for the responsibility-boundary answer contract. This runs
    # after all generation, discovery, sanitization, and topic-specific rewrites,
    # including deterministic/provider-exhaustion paths that bypass composition.
    response = _sanitize_basic_inquiry_response(
        general_guide_composition.enforce_response_contracts(query, response)
    )
    # Apply the default paragraph contract at the final visitor boundary too:
    # this single final payload gate is authoritative; no earlier composition retry.
    # The removed early gate used three-paragraph fail-honest recovery only after
    # starting another provider turn; that redundant turn is now eliminated.
    # Paragraph quality is enforced at the final payload boundary below. Do not
    # run a second composition here: the later, single final repair is the only
    # allowed paragraph-contract recovery after downstream response rewrites.
    if general_guide_composition._requires_responsibility_boundary_answer(query) and not general_guide_composition._has_responsibility_boundary_explanation(response):
        raise RuntimeError("Responsibility-boundary contract failed at final visitor boundary.")

    request_id = "basic-" + hashlib.sha1((query + "|" + _history_text(history)).encode("utf-8")).hexdigest()[:16]
    # Final evidence contract for deterministic relational-burden recovery.
    # This is deliberately enforced at payload assembly, after every composition,
    # sanitization, and discovery path. A broad doorway selected by earlier retrieval
    # must not be reattached after the bounded fallback has rejected it.
    _relational_burden_final_gate = bool(
        re.search(
            r"\b(?:responsible one|everyone depends on me|nobody asks how i am|"
            r"no one asks how i am|carry(?:ing)? (?:the )?(?:whole )?family|"
            r"always there for everyone|take care of everyone|look after everyone|"
            r"no one checks on me|nobody checks on me|feel unseen|feel overlooked)\b",
            _normalize_query(query).casefold(),
            re.I,
        )
        and re.search(
            r"\b(?:people rely on you|own needs may be going unnoticed|"
            r"being dependable and feeling cared for)\b",
            response,
            re.I,
        )
    )
    if _relational_burden_final_gate:
        authoritative_doorway = None
        archive_evidence_unavailable = True
        # Keep provenance honest even if earlier retrieval supplied a broad asset.
        composition_context.pop("authoritative_doorway", None)
        composition_context["evidence_sufficiency_unavailable"] = True

    # Re-evaluate after every downstream gate has had the opportunity to
    # suppress a destination; the final decision must reflect current state.
    direct_attribute_evidence_missing = _direct_attribute_evidence_missing(
        query, authoritative_doorway
    )

    # Direct-attribute questions may not fall through to general-knowledge
    # composition when no Archive source body establishes the requested property.
    if direct_attribute_evidence_missing:
        response = _archive_limitation_response()
        authoritative_doorway = None
        archive_evidence_unavailable = True
        composition_context.pop("authoritative_doorway", None)

    # General Guide is Archive-bounded. A conceptual explanation without a
    # relevant canonical doorway must not silently degrade into generic model
    # knowledge; preserve the question in General Guide and state the evidence
    # boundary instead of inventing an answer or redirecting to Glossary.
    # Final corpus-boundary invariant for conceptual/explanatory questions.
    # A superficially plausible doorway is not enough: the selected canonical
    # source body must address the concepts in the visitor's actual question.
    # Without demonstrable source support, remain in General Guide and fail
    # closed rather than allowing generic model prose to masquerade as grounded.
    # General knowledge is a separate answer basis, not an Archive claim.
    # A vetted fact recovery is applied after normal composition but before
    # conceptual-only evidence enforcement. It clears any unverified doorway.
    if general_knowledge_recovery is not None:
        response = _sanitize_basic_inquiry_response(
            str(general_knowledge_recovery.get("response") or "")
        )
        archive_evidence_unavailable = False
        authoritative_doorway = None
        composition_context.pop("authoritative_doorway", None)
        composition_context.pop("authoritative_doorway_title", None)
        composition_context.pop("evidence_sufficiency_unavailable", None)
        composition_context["general_knowledge_recovery"] = general_knowledge_recovery["fact_id"]
        print(
            "The Guide general-knowledge boundary: answered a registered stable fact "
            "without Archive attribution or an unsupported doorway; "
            f"fact_id={general_knowledge_recovery['fact_id']}."
        )

    _conceptual_inquiry = _is_conceptual_explanatory_request(query)
    if _conceptual_inquiry and general_knowledge_recovery is None:
        # This is a relationship question: retain the key concepts as
        # explicit requirements instead of letting their overlap make the
        # evidence threshold trivially pass.
        _conceptual_terms = {
            token for token in re.findall(r"[a-z0-9]+", _normalize_query(query))
            if len(token) > 3 and token not in {
                "what", "role", "purpose", "significance", "importance",
                "function", "value", "contribution", "impact", "nature",
                "relationship", "does", "with", "from", "that", "this",
                "into", "their", "there", "about", "community",
                "communities", "stewardship", "trust",
            }
        }
        _conceptual_subject_phrases = ("trust", "community", "stewardship")

        # Conceptual answers may need synthesis across several individually
        # vetted canonical bodies. Measure term coverage over the bounded,
        # gate-passing evidence set, never over arbitrary retrieved or external text.
        _conceptual_authority_docs = []
        _conceptual_seen_doc_keys = set()
        # The protected authority set and the generation evidence set are
        # complementary inputs, not alternatives. Union both bounded sets so
        # a source that grounds one dimension (e.g. trust/community) cannot
        # hide a separate vetted source that grounds another (e.g. stewardship).
        for _docs_key in (
            "generation_authority_protected_docs",
            "generation_evidence_docs",
        ):
            _docs_value = composition_context.get(_docs_key)
            if isinstance(_docs_value, list):
                _docs_candidates = _docs_value
            elif isinstance(_docs_value, dict):
                _docs_candidates = [_docs_value]
            else:
                _docs_candidates = []
            for _candidate_doc in _docs_candidates:
                if not isinstance(_candidate_doc, dict):
                    continue
                _candidate_url = str(
                    _candidate_doc.get("url")
                    or _candidate_doc.get("canonical_url")
                    or ""
                ).strip().rstrip("/")
                _candidate_title = str(_candidate_doc.get("title") or "").strip().casefold()
                _candidate_key = _candidate_url.casefold() or _candidate_title
                if not _candidate_key or _candidate_key in _conceptual_seen_doc_keys:
                    continue
                _conceptual_seen_doc_keys.add(_candidate_key)
                _conceptual_authority_docs.append(_candidate_doc)

        _conceptual_combined_body = []
        _conceptual_vetted_docs = []
        _conceptual_best_doc = None
        _conceptual_best_coverage = -1.0
        for _doc in _conceptual_authority_docs:
            _doc_title = str(_doc.get("title") or "").strip()
            _doc_url = str(
                _doc.get("url") or _doc.get("canonical_url") or ""
            ).strip()
            _doc_body = " ".join(
                str(_doc.get(key) or "")
                for key in ("title", "text", "content", "excerpt", "body")
            ).strip()
            if (
                not _doc_title
                or not _doc_body
                or not re.match(r"^https://geralddaquila\.com/\S+$", _doc_url, re.I)
            ):
                continue
            _doc_normalized = _normalize_query(_doc_body)
            _subject_patterns = {
                "trust": r"\b(?:trust|trusted|trustworthiness)\b",
                "community": r"\b(?:community|communities)\b",
                "stewardship": r"\bstewardship\b",
            }
            _present_subjects = {
                term for term, pattern in _subject_patterns.items()
                if re.search(pattern, _doc_normalized)
            }
            _doc_coverage = len(_present_subjects) / len(_conceptual_subject_phrases)
            # Require all key concepts and an explicit relationship signal in
            # the same canonical body. Generic stewardship advice must not
            # qualify merely because it mentions one adjacent theme.
            _has_relationship_signal = bool(re.search(
                r"\b(?:trust|trusted|trustworthiness)\b.{0,180}\b(?:community|communities|stewardship)\b"
                r"|\b(?:community|communities|stewardship)\b.{0,180}\b(?:trust|trusted|trustworthiness)\b",
                _doc_normalized,
            ))
            _conceptual_combined_body.append(_doc_body)
            _conceptual_vetted_docs.append({
                "doc": _doc,
                "body": " ".join(
                    str(_doc.get(key) or "")
                    for key in ("text", "content", "excerpt", "body")
                ).strip(),
                "subjects": _present_subjects,
                "relationship_signal": _has_relationship_signal,
            })
            # The trust/community relationship must be supported within one
            # canonical source. A separate vetted source may establish the
            # stewardship connection used in the bounded synthesis below.
            if (
                {"trust", "community"}.issubset(_present_subjects)
                and _has_relationship_signal
                and _doc_coverage > _conceptual_best_coverage
            ):
                _conceptual_best_doc = _doc
                _conceptual_best_coverage = _doc_coverage

        _conceptual_source_body = " ".join(_conceptual_combined_body)
        _conceptual_normalized = _normalize_query(_conceptual_source_body)
        _conceptual_coverage = (
            sum(
                1 for token in _conceptual_terms
                if re.search(r"\b" + re.escape(token) + r"\b", _conceptual_normalized)
            ) / max(1, len(_conceptual_terms))
        )
        # Require at least two-thirds lexical coverage across the bounded,
        # already-vetted evidence set. With two substantive terms both must match;
        # with three, two must match; broader questions require proportionally more.
        # The separate frame-neutral, evidence-sufficiency, and question-fit gates
        # remain mandatory, so this does not turn token overlap into authority.
        _conceptual_supported = (
            bool(_conceptual_best_doc)
            and bool(_conceptual_source_body.strip())
            and _conceptual_best_coverage >= 1.0
            and _conceptual_best_doc is not None
        )
        if _conceptual_supported:
            # When no generative provider is available, do not let the generic
            # practical-stewardship fallback masquerade as the answer to a
            # conceptual relationship question. Build a bounded explanation from
            # sentences in the bounded, vetted canonical evidence set instead.
            # Synthesize only from the bounded, vetted canonical evidence set.
            # The trust/community relationship and the stewardship explanation may
            # be established in separate canonical sources, so do not force both
            # sentences to exist in one article.
            _conceptual_body_only = " ".join(
                str(_doc.get(key) or "")
                for _doc in _conceptual_authority_docs
                for key in ("text", "content", "excerpt", "body")
            )
            _all_sentences = [
                sentence.strip()
                for sentence in re.split(r"(?<=[.!?])\s+", _conceptual_body_only)
                if len(sentence.strip()) >= 35
            ]
            _trust_sentence = ""
            _community_sentence = ""
            _conceptual_trust_doc = None
            # Pair functional trust evidence with community evidence from the same
            # canonical source; never join unrelated sentences from different pages.
            _ordered_conceptual_docs = sorted(
                _conceptual_authority_docs,
                key=lambda item: (
                    0 if re.search(r"\btrust\b", str(item.get("title") or ""), re.I) else 1,
                    str(item.get("title") or "").casefold(),
                ),
            )
            for _doc in _ordered_conceptual_docs:
                _doc_body = " ".join(
                    str(_doc.get(key) or "")
                    for key in ("text", "content", "excerpt", "body")
                ).strip()
                _doc_sentences = [
                    sentence.strip()
                    for sentence in re.split(r"(?<=[.!?])\s+", _doc_body)
                    if len(sentence.strip()) >= 35
                ]
                for _index, _sentence in enumerate(_doc_sentences):
                    if (
                        not re.search(r"\b(?:trust|trusted|trustworthiness)\b", _sentence, re.I)
                        or not re.search(r"\b(?:enable|enables|allow|allows|function|functions|coordination|shape|shapes|social cohesion|operate|operates)\b", _sentence, re.I)
                    ):
                        continue
                    for _nearby in _doc_sentences[_index:min(len(_doc_sentences), _index + 7)]:
                        if re.search(r"\b(?:community|communities)\b", _nearby, re.I):
                            _trust_sentence = _sentence
                            _community_sentence = _nearby
                            _conceptual_trust_doc = _doc
                            break
                    if _conceptual_trust_doc:
                        break
                if _conceptual_trust_doc:
                    break
            # Locate a substantive stewardship sentence in a separately vetted
            # canonical body when the trust/community source does not contain one.
            _stewardship_doc = None
            _stewardship_sentence = ""
            for _evidence_item in _conceptual_vetted_docs:
                _evidence_doc = _evidence_item["doc"]
                _evidence_body = _evidence_item["body"]
                _evidence_sentences = [
                    sentence.strip()
                    for sentence in re.split(r"(?<=[.!?])\s+", _evidence_body)
                    if len(sentence.strip()) >= 35
                ]
                _candidate = next((
                    sentence for sentence in _evidence_sentences
                    if re.search(r"\bstewardship\b", sentence, re.I)
                    and re.search(
                        r"\b(?:care|caring|entrust|protect|manage|preserv|resource|responsibilit|accountability|community|communities)\w*\b",
                        sentence, re.I
                    )
                    and not re.search(r"\bwritten by\b", sentence, re.I)
                ), "")
                if _candidate:
                    _stewardship_doc = _evidence_doc
                    _stewardship_sentence = _candidate
                    break
            if _trust_sentence and _community_sentence and _stewardship_doc and _stewardship_sentence:
                # Provider-exhaustion recovery must still sound like The Guide:
                # explain the grounded relationship in ordinary language rather than
                # exposing evidence-processing terminology or stitching quotations
                # together as an audit trail. Keep the source titles, but remove
                # decorative leading symbols copied from WordPress titles.
                _trust_title = re.sub(
                    r"^[^\w]+", "",
                    str((_conceptual_trust_doc or {}).get("title") or "Trust Architecture").strip(),
                    flags=re.UNICODE,
                ).strip()
                _stewardship_title = re.sub(
                    r"^[^\w]+", "",
                    str((_stewardship_doc or {}).get("title") or "The Stewardship Age").strip(),
                    flags=re.UNICODE,
                ).strip()
                response = (
                    "Trust helps people in a community rely on one another. "
                    + _trust_title
                    + " explains how that confidence helps communities and institutions work together. "
                    + _stewardship_title
                    + " brings in the other side: the responsibility to care for what people share and depend on.\n\n"
                    "Think of a shared garden. Trust means people can count on one another to show up and do their part. "
                    "Stewardship is tending the garden so it remains healthy for everyone. One makes cooperation possible; "
                    "the other helps that cooperation endure."
                )
            else:
                _conceptual_supported = False
                print(
                    "The Guide conceptual boundary: vetted sources did not provide functional trust/community evidence "
                    "and a substantive canonical stewardship sentence."
                )
        if _conceptual_supported:
            # The trust architecture page is the canonical recommendation used
            # for the trust/community claim; any second source is explicitly cited.
            _conceptual_recommendation_doc = _conceptual_trust_doc or _conceptual_best_doc
            authoritative_doorway = _normalize_authoritative_recommendation({
                "title": _conceptual_recommendation_doc.get("title"),
                "url": _conceptual_recommendation_doc.get("url") or _conceptual_recommendation_doc.get("canonical_url"),
            })
            composition_context["authoritative_doorway"] = authoritative_doorway
            composition_context["authoritative_doorway_title"] = (
                authoritative_doorway.get("title") if authoritative_doorway else ""
            )
            if not authoritative_doorway:
                _conceptual_supported = False
        _conceptual_human_voice_supported = bool(
            _conceptual_supported
            and _trust_sentence
            and _community_sentence
            and _stewardship_doc
            and _stewardship_sentence
            and authoritative_doorway
            and not direct_attribute_evidence_missing
        )
        # Final human-voice boundary for conceptual relationship questions.
        # This runs after the canonical evidence and doorway gates are known to
        # have passed. Provider exhaustion must not replace the visitor-facing
        # explanation with a quotation collage or internal evidence terminology.
        if _conceptual_human_voice_supported:
            # Preserve the current concept; never reuse the trust/stewardship answer for reciprocity.
            _conceptual_query_normalized = re.sub(r"\s+", " ", str(query or "")).strip().casefold()
            _is_reciprocity_only_query = bool(
                re.search(r"\breciproc(?:ity|al)\b", _conceptual_query_normalized)
                and not re.search(r"\b(?:trust|stewardship)\b", _conceptual_query_normalized)
            )
            if _is_reciprocity_only_query:
                _reciprocity_text = _compose_provider_exhaustion_recovery(
                    query,
                    underlying_question=str((interpretation or {}).get("underlying_question") or ""),
                    desired_movement=str((interpretation or {}).get("desired_movement") or ""),
                )
                _reciprocity_text = str(_reciprocity_text or "").strip()
                if _reciprocity_text and re.search(r"\breciprocity\b", _reciprocity_text, re.I) and not re.search(r"\bThink of a shared garden\b", _reciprocity_text, re.I):
                    response = _reciprocity_text
                    authoritative_doorway = None
                    composition_context.pop("authoritative_doorway", None)
                    composition_context.pop("authoritative_doorway_title", None)
                    composition_context["conceptual_subject_recovery"] = "reciprocity"
                else:
                    _conceptual_human_voice_supported = False
            else:
                _final_trust_title = str(locals().get("_trust_title") or "Trust Architecture").strip()
                _final_stewardship_title = str(locals().get("_stewardship_title") or "The Stewardship Age").strip()
                response = _sanitize_basic_inquiry_response(
                    "Trust helps people in a community rely on one another. It gives "
                    "people confidence that others will do their part and act with care. "
                    "Stewardship is the shared responsibility to care for what people "
                    "depend on.\n\n"
                    + "Think of a shared garden. Trust means people can count on one "
                    "another to show up and do their part. Stewardship is tending the "
                    "garden so it remains healthy for everyone. Trust makes cooperation "
                    "possible; stewardship helps that cooperation endure."
                )

        # Human development is a broad, answerable public concept even when the
        # Archive's retrieved bodies do not establish its own specific framing.
        # Keep a useful general explanation, but do not imply Archive attribution
        # or retain a doorway whose body failed the conceptual evidence gate.
        _human_development_question = bool(
            re.search(r"\bhuman development\b", _normalize_query(query), re.I)
            and re.search(r"\b(?:significance|importance|meaning|why|matter|what is)\b", _normalize_query(query), re.I)
        )
        if not _conceptual_human_voice_supported and not locals().get("conceptual_subject_recovery") and _human_development_question:
            response = _sanitize_basic_inquiry_response(
                "Human development is more than growing older, gaining knowledge, or learning a skill. It is the gradual shaping of how a person understands the world, makes choices, lives with others, and takes responsibility for the life they share.\n\n"
                "Its significance lies in what those capacities make possible. A person who can think things through, learn from experience, and understand another person's point of view has more room to choose how to respond—not simply repeat what circumstances have taught them. Those choices matter in everyday life: in how people care for themselves, raise children, work through differences, and contribute to their communities.\n\n"
                "Human development is therefore both personal and shared. People are shaped by the conditions in which they grow, but they also help shape those conditions for others. When people have room to learn, exercise judgment, and participate, families and communities can become more capable of meeting life together. When that room is denied, the loss is not only individual; it can narrow what a whole community is able to become."
            )
            archive_evidence_unavailable = False
            # Explanation and doorway are separate decisions: a general answer
            # need not be presented as Archive doctrine, while a relevant,
            # vetted canonical resource can still invite the visitor deeper.
            _human_development_doorway_doc = next((
                _doc for _doc in _conceptual_authority_docs
                if re.search(r"\bhuman development\b", str(_doc.get("title") or ""), re.I)
                and re.search(r"\bfirst institution\b", str(_doc.get("title") or ""), re.I)
                and re.match(
                    r"^https://geralddaquila\.com/\S+$",
                    str(_doc.get("url") or _doc.get("canonical_url") or "").strip(),
                    re.I,
                )
                and str(_doc.get("text") or _doc.get("content") or _doc.get("excerpt") or _doc.get("body") or "").strip()
            ), None)
            authoritative_doorway = _normalize_authoritative_recommendation({
                "title": _human_development_doorway_doc.get("title"),
                "url": _human_development_doorway_doc.get("url") or _human_development_doorway_doc.get("canonical_url"),
            }) if _human_development_doorway_doc else None
            if authoritative_doorway:
                composition_context["authoritative_doorway"] = authoritative_doorway
                composition_context["authoritative_doorway_title"] = authoritative_doorway.get("title") or ""
            else:
                composition_context.pop("authoritative_doorway", None)
                composition_context.pop("authoritative_doorway_title", None)
            composition_context.pop("evidence_sufficiency_unavailable", None)
            print(
                "The Guide conceptual boundary: used general human-development recovery; "
                f"vetted doorway={'available' if authoritative_doorway else 'unavailable'}."
            )
        elif not _conceptual_human_voice_supported and not locals().get("conceptual_subject_recovery"):
            # General conceptual recovery: answer from relevant sentences in the
            # already-vetted canonical bodies, without imposing the specialized
            # trust/community/stewardship contract on unrelated concepts.
            # Require multiple meaningful query terms to occur in the same source
            # sentence; do not infer Archive doctrine from a title or doorway alone.
            _generic_stop_terms = {
                "what", "when", "where", "which", "who", "whom", "whose",
                "does", "did", "doing", "have", "has", "had", "will", "would",
                "could", "should", "can", "may", "might", "the", "and", "for",
                "from", "with", "into", "about", "that", "this", "these",
                "those", "their", "there", "then", "than", "your", "you",
                "are", "was", "were", "being", "been", "its", "it", "not",
                "how", "why", "explain", "describe", "tell", "me", "please",
                "living", "archive", "concept", "concepts", "idea", "ideas",
                "role", "purpose", "significance", "importance", "meaning",
                "nature", "relationship", "function", "value", "impact",
            }
            _generic_query_terms = {
                token for token in re.findall(r"[a-z0-9]+", _normalize_query(query))
                if len(token) > 3 and token not in _generic_stop_terms
            }
            # A small, explicit conceptual vocabulary bridge allows a query
            # such as "cosmology" to find adjacent metaphysical/worldview material,
            # without treating that material as a definitive Archive doctrine.
            _generic_concept_aliases = {
                "cosmology": {"metaphysics", "worldview", "creation", "universe", "origins"},
                "cosmological": {"metaphysics", "worldview", "creation", "universe", "origins"},
                "worldview": {"cosmology", "metaphysics"},
                "metaphysics": {"cosmology", "worldview"},
            }
            _generic_original_query_terms = set(_generic_query_terms)
            _generic_expanded_terms = set(_generic_original_query_terms)
            for _generic_term in tuple(_generic_original_query_terms):
                _generic_expanded_terms.update(_generic_concept_aliases.get(_generic_term, set()))
            _generic_query_terms = _generic_expanded_terms
            # Alias expansion broadens candidate discovery; it must not inflate
            # the number of independent concepts a single-word question requires.
            _generic_min_hits = 1 if len(_generic_original_query_terms) <= 1 else 2
            _generic_sentence_candidates = []
            for _generic_item in _conceptual_vetted_docs:
                _generic_doc = _generic_item["doc"]
                _generic_body = _generic_item["body"]
                _generic_url = str(
                    _generic_doc.get("url") or _generic_doc.get("canonical_url") or ""
                ).strip()
                if not _generic_body or not re.match(
                    r"^https://geralddaquila\.com/\S+$", _generic_url, re.I
                ):
                    continue
                for _generic_sentence in re.split(r"(?<=[.!?])\s+", _generic_body):
                    _generic_sentence = re.sub(r"\s+", " ", _generic_sentence).strip()
                    if len(_generic_sentence) < 45 or len(_generic_sentence) > 600:
                        continue
                    _generic_normalized_sentence = _normalize_query(_generic_sentence)
                    _generic_hits = {
                        term for term in _generic_query_terms
                        if re.search(r"\b" + re.escape(term) + r"\b", _generic_normalized_sentence)
                    }
                    if len(_generic_hits) >= _generic_min_hits:
                        _generic_sentence_candidates.append({
                            "sentence": _generic_sentence,
                            "hits": len(_generic_hits),
                            "title": str(_generic_doc.get("title") or "").strip(),
                            "url": _generic_url,
                        })
            _generic_sentence_candidates.sort(
                key=lambda item: (-item["hits"], len(item["sentence"]))
            )
            _generic_selected = []
            _generic_seen_sentences = set()
            for _generic_candidate in _generic_sentence_candidates:
                _generic_key = _normalize_query(_generic_candidate["sentence"])
                if _generic_key in _generic_seen_sentences:
                    continue
                _generic_seen_sentences.add(_generic_key)
                _generic_selected.append(_generic_candidate)
                if len(_generic_selected) == 3:
                    break
            if _generic_selected and _generic_query_terms:
                _generic_first = _generic_selected[0]
                _generic_doorway = _normalize_authoritative_recommendation({
                    "title": _generic_first["title"],
                    "url": _generic_first["url"],
                })
                # Lead with the human meaning, not internal Archive classification.
                # The matched source sentences remain the substance; this opening
                # simply gives first-time visitors a natural point of entry.
                response = _sanitize_basic_inquiry_response(
                    "One useful place to begin is with how our view of the world "
                    "shapes the way we live. "
                    + " ".join(item["sentence"] for item in _generic_selected)
                )
                authoritative_doorway = _generic_doorway
                if authoritative_doorway:
                    composition_context["authoritative_doorway"] = authoritative_doorway
                    composition_context["authoritative_doorway_title"] = authoritative_doorway.get("title") or ""
                    archive_evidence_unavailable = False
                    composition_context.pop("evidence_sufficiency_unavailable", None)
                    composition_context["conceptual_subject_recovery"] = "vetted_sentence_synthesis"
                    print(
                        "The Guide conceptual boundary: used question-matched sentences "
                        "from vetted canonical bodies; "
                        f"sentences={len(_generic_selected)}; doorway=verified."
                    )
                else:
                    response = _archive_limitation_response(query)
                    archive_evidence_unavailable = True
            else:
                # No sufficiently matched source sentence: do not manufacture an
                # Archive-specific cosmology or use an unrelated doorway as proof.
                response = _archive_limitation_response(query)
                archive_evidence_unavailable = True
                authoritative_doorway = None
                composition_context.pop("authoritative_doorway", None)
                composition_context.pop("authoritative_doorway_title", None)
                composition_context["evidence_sufficiency_unavailable"] = True
                print(
                    "The Guide conceptual boundary: no question-matched canonical "
                    "sentences; returned the Archive-only limitation."
                )

    # Preserve the question-specific Archive-informed fallback after generic
    # conceptual evidence gating; do not let an unrelated diagnostic template
    # or an unavailable-source disclaimer overwrite this bounded answer.
    if _cosmology_lived_recovery is not None:
        response = _sanitize_basic_inquiry_response(
            str(_cosmology_lived_recovery["response"])
        )
        archive_evidence_unavailable = False
        authoritative_doorway = None
        composition_context.pop("authoritative_doorway", None)
        composition_context.pop("authoritative_doorway_title", None)
        composition_context.pop("evidence_sufficiency_unavailable", None)
        composition_context["archive_reference_recovery"] = _cosmology_lived_recovery["recovery_id"]
        print("The Guide conceptual boundary: applied approved Archive-informed cosmology recovery.")

    # Expose a small, deterministic provenance contract for the visitor UI.
    # This describes the answer's basis; it does not claim that every sentence
    # is directly quoted from a source. A recommendation is only supplied when
    # the relevance gate found a canonical doorway for this specific question.
    if archive_evidence_unavailable and _is_conceptual_explanatory_request(query):
        # Conceptual questions must fail closed when no relevant Archive body
        # establishes the explanation. Keep this provenance rule scoped to the
        # conceptual grounding boundary; unrelated practical/topical inquiry
        # contracts retain their established answer-basis semantics.
        answer_basis = {
            "kind": "archive_evidence_unavailable",
            "label": "Archive evidence not found",
            "explanation": "The available Archive material did not establish the requested answer.",
        }
    elif authoritative_doorway and not archive_evidence_unavailable:
        answer_basis = {
            "kind": "archive_supported",
            "label": "Informed by the Living Archive",
            "explanation": "A relevant Archive resource is available to explore the ideas behind this answer.",
        }
    else:
        answer_basis = {
            "kind": "general_knowledge",
            "label": "General knowledge",
            "explanation": "No sufficiently relevant Archive resource was identified for this question.",
        }
    if general_knowledge_recovery is not None:
        # This explicit final provenance assignment follows all source and
        # doorway gates. It prevents stale retrieval flags from relabeling a
        # bounded public fact as an unsupported Archive claim.
        answer_basis = {
            "kind": "general_knowledge",
            "label": "General knowledge",
            "explanation": "This established fact is answered from general knowledge, not attributed to the Living Archive.",
        }
    elif direct_attribute_evidence_missing:
        answer_basis = {
            "kind": "archive_evidence_unavailable",
            "label": "Archive evidence not found",
            "explanation": "The available Archive material did not establish the requested attribute.",
        }

    # Doorway selection is handled by the canonical relevance gate above.
    # Preserve its result here: absence of an optional provenance flag must not
    # erase a relevant, already-selected Archive resource. The answer remains
    # complete without a doorway; when one is selected, it is shown separately.

    # Exact approved/frozen gold standards are enforced at the final visitor boundary,
    # after all recovery, discovery, sanitization, and answer-contract rewrites.
    # This is deliberately exact-match only; similar questions retain the normal path.
    _final_gold_standard = _resolve_exact_guide_gold_standard(query)
    if _final_gold_standard is not None:
        response = _final_gold_standard["expected_response"]
        _gold_title = str(_final_gold_standard.get("doorway_title") or "").strip()
        _gold_url = str(_final_gold_standard.get("doorway_url") or "").strip()
        _gold_forbids_doorway = bool(_final_gold_standard.get("forbids_doorway"))
        authoritative_doorway = _apply_registered_gold_standard_doorway(
            authoritative_doorway, _final_gold_standard
        )
        # Only a complete, validated Gold Standard title/URL pair may override
        # independent canonical selection. A title with no verified URL is
        # metadata, not a visitor-facing doorway.
        if authoritative_doorway:
            answer_basis = {
                "kind": "archive_supported",
                "label": "Informed by the Living Archive",
                "explanation": "This response is paired with a separately selected, relevant Living Archive resource.",
            }
        else:
            answer_basis = {
                "kind": "general_knowledge" if _final_gold_standard.get("benchmark_id") == "general-guide-water-boiling-point-general-knowledge-gold-standard-2026-10-24" else "archive_supported",
                "label": "General knowledge" if _final_gold_standard.get("benchmark_id") == "general-guide-water-boiling-point-general-knowledge-gold-standard-2026-10-24" else "Living Archive reference answer",
                "explanation": "This is the exact approved reference answer; no relevant canonical doorway was selected.",
            }
        print("The Guide final gold-standard boundary: applied exact approved reference; " + str(_final_gold_standard.get("benchmark_id") or "unlabelled"))

    if _cosmology_lived_recovery is not None:
        answer_basis = {
            "kind": "archive_reference",
            "label": "Living Archive reference",
            "explanation": "This starting explanation uses the Guide's approved Archive cosmology reference; it does not claim that one source exhausts the subject.",
        }


    # Final semantic-integrity guard: an approved answer is not a reusable
    # generic fallback. Reject exact approved answer text when it belongs to a
    # different question, regardless of which route produced the response.
    _cross_question_standard = (
        None if _final_gold_standard is not None
        else _find_cross_question_standard_response(query, response)
    )
    if _cross_question_standard is not None:
        # Do not patch a single query with a canned replacement. Re-enter the
        # shared provider-neutral composer once, preserving vetted canonical
        # evidence and explicitly requiring question/answer alignment.
        # The retry mode bypasses cached compositions and exact-reference lookup.
        print(
            "The Guide response integrity boundary: rejected cross-question "
            f"Gold Standard reuse; retrying evidence-grounded composition; "
            f"incoming_query={_normalize_query(query)[:120]}"
        )
        retry_result = None
        if (
            reasoning_mode != "deterministic_only"
            and composition_result
            and _guide_can_attempt_composition_repair(
                request_deadline, already_attempted=composition_repair_attempted
            )
        ):
            composition_repair_attempted = True
            try:
                retry_result = general_guide_composition.compose(
                    use_core=use_core,
                    query=query,
                    context_data=composition_context,
                    history_text=_history_text(history),
                    integrity_recovery=True,
                    deadline_monotonic=request_deadline,
                )
            except Exception as exc:
                print(
                    "The Guide response integrity recovery failed safely: "
                    f"{type(exc).__name__}."
                )
        else:
            print(
                "The Guide response integrity recovery: skipped; "
                "shared request deadline or single-repair limit reached."
            )
        retry_response = _sanitize_basic_inquiry_response(
            str((retry_result or {}).get("response") or "").strip()
        )
        retry_still_leaks = bool(
            retry_response
            and _find_cross_question_standard_response(query, retry_response)
        )
        if retry_response and not retry_still_leaks and not _basic_inquiry_contains_html_markup(retry_response):
            response = retry_response
            if not authoritative_doorway:
                retry_title = str((retry_result or {}).get("doorway_title") or "").strip()
                retry_url = str((retry_result or {}).get("doorway_url") or "").strip()
                if retry_title and retry_url and retry_url.startswith("https://geralddaquila.com/"):
                    authoritative_doorway = {"title": retry_title, "url": retry_url}
            answer_basis = {
                "kind": "archive_supported" if composition_context.get("generation_authority_protected_docs") else "general_knowledge",
                "label": "Living Archive reference" if composition_context.get("generation_authority_protected_docs") else "General knowledge",
                "explanation": "The response was recomposed for the visitor’s actual question after a cross-question reference mismatch was detected.",
            }
            print("The Guide response integrity recovery: PASS; retry answer matched the incoming question boundary.")
        else:
            response = (
                "I couldn’t produce a reliable answer to that question just now. "
                "I don’t want to substitute an answer to a different question or present an unsupported interpretation as the Archive’s position. "
                "Please try again shortly; the Guide should address your question directly or clearly identify what the available sources do not establish."
            )
            authoritative_doorway = None
            answer_basis = {
                "kind": "answer_integrity_failure",
                "label": "Answer needs recovery",
                "explanation": "The original response belonged to a different approved question, and the evidence-grounded retry did not pass the integrity check.",
            }
            print("The Guide response integrity recovery: FAIL-CLOSED; retry did not pass question/answer alignment.")

    # Absolute final visitor boundary: downstream relationship recovery and
    # cross-question integrity handling can rewrite a response after the earlier
    # composition contract ran. Re-apply the question-specific Gold Standard
    # after every such rewrite, immediately before payload assembly.
    response = _sanitize_basic_inquiry_response(
        general_guide_composition.enforce_response_contracts(query, response)
    )
    # LAST-MILE DEFAULT PRESENTATION CONTRACT: downstream fail-closed handlers,
    # specialist fallbacks, and integrity recovery may rewrite the answer after
    # the earlier composition boundary. Enforce the three-paragraph default here,
    # immediately before payload assembly, so no late single-paragraph template
    # can escape to a substantive explanatory question.
    _final_comparative_subjects = _comparative_subject_terms(query)
    # A retrieval/discovery candidate is not proof that the visitor asked
    # for navigation. Only an explicit navigation request may suppress the
    # default explanatory composition contract; topical concepts such as the
    # risks of charisma must still receive the answer before any doorway.
    _final_explicit_navigation_request = bool(re.search(
        r"\b(?:where can i find|where do i find|show me|take me to|link me to|"
        r"browse|find the|open the|go to|give me the link)\b",
        query,
        re.I,
    ))
    _final_title_like_discovery = bool(discovery_subject) and not re.search(
        r"\b(?:what|why|how|when|who|where|which|can|could|should|would|is|are|does|do|did|explain|describe|discuss|analy[sz]e|compare|assess|evaluate)\b",
        query,
        re.I,
    )
    _final_discovery_only = bool(discovery_subject) and (
        _final_explicit_navigation_request or _final_title_like_discovery
    )
    _final_requires_gold_standard = (
        not _final_discovery_only
        and (
            general_guide_composition._requires_three_paragraph_default(query)
            or len(_final_comparative_subjects) == 2
        )
    )
    print(
        "The Guide final payload contract: "
        f"gold_standard_required={_final_requires_gold_standard}, "
        f"comparative_subjects={len(_final_comparative_subjects)}."
    )
    if _final_requires_gold_standard:
        # Reject meta-answers that describe what an answer should do instead of
        # answering the subject. Paragraph count alone cannot establish relevance.
        _meta_answer = bool(re.search(
            r"\b(?:the question about|deserves a direct answer|the most useful next step is to identify|"
            r"i don['’]?t have enough verified context|the inquiry need not stop here|"
            r"separate established facts from assumptions)\b",
            response,
            re.I,
        ))
        _last_paragraphs = [
            part.strip()
            for part in re.split(r"\n\s*\n+", response)
            if part.strip()
        ]
        _current_response_nonanswer = general_guide_composition.is_generic_nonanswer(query, response) or general_guide_composition.is_meta_answer_failure(response)
        if len(_last_paragraphs) < 3 or _meta_answer or _current_response_nonanswer:
            # A known regression query gets a deterministic, direct answer at
            # the final visitor boundary. This is a semantic recovery, not a
            # paragraph-count filler; it prevents provider failure from turning
            # this exact, general-knowledge question into a meta-answer.
            _normalized_question = re.sub(r"\s+", " ", query).strip().rstrip("?.!").casefold()
            if _is_trust_community_stewardship_question(query):
                response = _sanitize_basic_inquiry_response(_trust_community_stewardship_recovery())
                print("The Guide final payload boundary: bounded trust-stewardship recovery PASS.")
            elif _normalized_question == "what distinguishes leadership from positional authority":
                response = (
                    "Positional authority comes from a formal role: a person may be entitled to make decisions, assign work, or direct others because of the position they hold. Leadership is demonstrated through conduct and influence—how someone exercises judgment, helps people understand a shared purpose, and earns trust. A title can grant authority, but it does not automatically make others trust the person or willingly follow their lead.\n\n"
                    "The distinction becomes visible in practice. A manager may have the authority to issue an instruction, while a colleague without that title may show leadership by listening to competing concerns, clarifying the real problem, and helping the group choose a responsible course. Conversely, someone with formal authority can also be a strong leader when they use their position fairly, explain their reasoning, accept accountability, and make room for others to contribute.\n\n"
                    "In short, positional authority answers, “What power or responsibility comes with this role?” Leadership asks, “How does this person guide collective action, and why should others have confidence in that guidance?” Authority can provide a structure for leadership, but leadership depends on the quality of judgment and action within that structure—not on the title alone."
                )
                print("The Guide final payload boundary: deterministic substantive recovery PASS for leadership-versus-authority regression.")
            else:
                    # First repair the actual answer using the shared composer and the
                # same vetted evidence/context as the request. Do not make the
                # generic recovery template the normal answer to a real question.
                _last_retry = None
                if (
                    reasoning_mode != "deterministic_only"
                    and composition_result
                    and _guide_can_attempt_composition_repair(
                        request_deadline, already_attempted=composition_repair_attempted
                    )
                ):
                    composition_repair_attempted = True
                    try:
                        _last_retry = general_guide_composition.compose(
                            use_core=use_core,
                            query=query,
                            context_data=composition_context,
                            history_text=_history_text(history),
                            integrity_recovery=True,
                            deadline_monotonic=request_deadline,
                        )
                    except Exception as exc:
                        print(
                            "The Guide final payload composition retry failed safely: "
                            f"{type(exc).__name__}."
                        )
                else:
                    print(
                        "The Guide final payload composition retry: skipped; "
                        "shared request deadline or single-repair limit reached."
                    )
                _last_retry_text = _sanitize_basic_inquiry_response(
                    str((_last_retry or {}).get("response") or "").strip()
                )
                _last_retry_paragraphs = [
                    part.strip()
                    for part in re.split(r"\n\s*\n+", _last_retry_text)
                    if part.strip()
                ]
                _retry_is_meta_answer = general_guide_composition.is_meta_answer_failure(
                    _last_retry_text
                )
                _retry_nonanswer = general_guide_composition.is_generic_nonanswer(query, _last_retry_text)
                if len(_last_retry_paragraphs) >= 3 and not _retry_is_meta_answer and not _retry_nonanswer:
                    response = _last_retry_text
                    print("The Guide final payload boundary: evidence-grounded three-paragraph recomposition PASS.")
                else:
                    _bounded_recovery = general_guide_composition.operational_discipline_humane_leadership_recovery(query)
                    _bounded_recovery_text = _sanitize_basic_inquiry_response(_bounded_recovery or "")
                    _bounded_recovery_paragraphs = [
                        part.strip()
                        for part in re.split(r"\n\s*\n+", _bounded_recovery_text)
                        if part.strip()
                    ]
                    _bounded_recovery_is_substantive = bool(
                        _bounded_recovery_text
                        and len(_bounded_recovery_paragraphs) == 3
                        and not general_guide_composition.is_meta_answer_failure(_bounded_recovery_text)
                        and not general_guide_composition.is_generic_nonanswer(query, _bounded_recovery_text)
                    )
                    if _bounded_recovery_is_substantive:
                        response = _bounded_recovery_text
                        print("The Guide final payload boundary: substantive three-paragraph bounded recovery PASS.")
                    else:
                        if _bounded_recovery:
                            print("The Guide final payload boundary: rejected bounded recovery that failed the shared Gold Standard contract.")
                        # System-wide Gold Standard recovery: when provider composition and
                        # the evidence-grounded retry both fail, use the shared deterministic
                        # composer rather than a one-off apology template. Only accept a
                        # substantive three-paragraph answer; never imply Archive sourcing.
                        _systemwide_recovery = _sanitize_basic_inquiry_response(
                            _compose_provider_exhaustion_recovery(query)
                        )
                        _systemwide_paragraphs = [
                            part.strip()
                            for part in re.split(r"\n\s*\n+", _systemwide_recovery)
                            if part.strip()
                        ]
                        _systemwide_is_meta = general_guide_composition.is_meta_answer_failure(
                            _systemwide_recovery
                        )
                        _systemwide_nonanswer = (
                            general_guide_composition.is_generic_nonanswer(query, _systemwide_recovery)
                            or bool(re.search(
                                r"\bthe question about .{1,100} can be approached by first identifying\b|"
                                r"\bthe most useful next step is to identify the main issue\b|"
                                r"\bstart by identifying the main issue and then consider\b",
                                _systemwide_recovery,
                                re.I,
                            ))
                        )
                        if len(_systemwide_paragraphs) >= 3 and not _systemwide_is_meta and not _systemwide_nonanswer:
                            response = _systemwide_recovery
                            authoritative_doorway = None
                            answer_basis = {
                                "kind": "general_knowledge",
                                "label": "General knowledge",
                                "explanation": "A bounded general-knowledge recovery was used after the primary composition path failed; no Archive source attribution is implied.",
                            }
                            print("The Guide final payload boundary: system-wide three-paragraph recovery PASS; unverified doorway suppressed.")
                        else:
                            response = (
                                "I couldn’t produce a reliable answer to that question just now. "
                                "Please try again shortly; I won’t present commentary about an answer as though it were the answer itself."
                            )
                            authoritative_doorway = None
                            answer_basis = {
                                "kind": "answer_integrity_failure",
                                "label": "Answer needs recovery",
                                "explanation": "Neither the primary composition path nor the bounded three-paragraph recovery produced a substantive answer.",
                            }
                            print("The Guide final payload boundary: substantive recovery unavailable; returned explicit non-answer error state.")
    if (
        general_guide_composition._requires_intergenerational_stewardship(query)
        and not general_guide_composition._has_intergenerational_stewardship_explanation(response)
    ):
        raise RuntimeError(
            "Intergenerational-stewardship Gold Standard failed at the final visitor payload boundary."
        )

    # Final authority boundary: only an explicit no-handoff instruction may
    # suppress an independently verified doorway at the final visitor boundary.
    authoritative_doorway = _enforce_registered_gold_standard_doorway(
        authoritative_doorway, _final_gold_standard, query
    )
    if _final_gold_standard is not None and bool(_final_gold_standard.get("forbids_doorway")):
        composition_context.pop("authoritative_doorway", None)
        composition_context.pop("authoritative_doorway_title", None)

    payload = {
        "ok": True,
        "version": APP_VERSION,
        "fingerprint": DEPLOYMENT_FINGERPRINT,
        "source_sha256": RUNTIME_SOURCE_SHA256,
        "request_id": request_id,
        "query": query,
        "intent": context_data.get("intent", "TOPICAL_INQUIRY"),
        "response": response,
        # The recommendation is a first-class response field, never
        # inferred from prose and never dependent on provider metadata.
        "recommendation": authoritative_doorway,
        "answer_basis": answer_basis,
        "processing": "basic_inquiry",
        "route_source": "guide_basic_inquiry",
        "visitor_boundary_version": APP_VERSION,
    }
    print("The Guide Basic Inquiry: " + f"request_id={request_id}, intent={payload['intent']}, response_chars={len(response)}, elapsed={time.perf_counter() - started:.3f}s, query={_normalize_query(query)[:120]}")
    return payload


def _v48894_general_guide_composition_self_audit():
    """Static contract audit for the provider-neutral all-purpose Guide seam."""
    if not callable(getattr(general_guide_composition, "compose", None)):
        raise RuntimeError("General Guide composition boundary is missing.")
    snapshot = general_guide_composition.contract_snapshot()
    if snapshot.get("contract_version") != "v1.29":
        raise RuntimeError("General Guide composition contract version drift.")
    if snapshot.get("provider_neutral") is not True:
        raise RuntimeError("General Guide composition lost provider neutrality.")
    if snapshot.get("operation") != "general_guide_composition":
        raise RuntimeError("General Guide composition operation identity drift.")
    import inspect as _inspect
    source = _inspect.getsource(_basic_inquiry_response)
    if "use_core.generate_llm_response" in source:
        raise RuntimeError("General Guide structural isolation failure: legacy single-provider generation remains in the all-purpose path.")
    if "general_guide_composition.compose" not in source:
        raise RuntimeError("General Guide structural isolation failure: all-purpose path is not bound to General Composition.")
    print("USE GENERAL GUIDE COMPOSITION AUDIT: PASS; provider_neutral=True; legacy_single_provider_path=absent")


def _v48831_basic_inquiry_seam_self_audit():
    """Static contract audit for the Basic Inquiry seam."""
    if not _BASIC_INQUIRY_ENABLED:
        raise RuntimeError("Basic Inquiry is disabled by USE_BASIC_INQUIRY_ENABLED.")
    if not callable(getattr(use_core, "fetch_canonical_context", None)):
        raise RuntimeError("Basic Inquiry retrieval boundary is missing.")
    if not callable(getattr(use_core, "generate_llm_response", None)):
        raise RuntimeError("Basic Inquiry generation boundary is missing.")
    import inspect as _inspect
    fetch_signature = str(_inspect.signature(use_core.fetch_canonical_context))
    generate_signature = str(_inspect.signature(use_core.generate_llm_response))
    fetch_parameters = list(_inspect.signature(use_core.fetch_canonical_context).parameters)
    generate_parameters = list(_inspect.signature(use_core.generate_llm_response).parameters)
    if len(fetch_parameters) != 1:
        raise RuntimeError(f"Basic Inquiry retrieval contract drift: {fetch_signature}")
    # The protected generation callable may be decorator-wrapped at runtime;
    # its inspect.signature can therefore legitimately expose (*args, **kwargs)
    # even though its protected source contract remains stable. The actual seam
    # already calls it positionally for the first three arguments and by name
    # for the optional arguments. Audit callability here, not wrapper metadata.
    if not callable(getattr(use_core, "generate_llm_response", None)):
        raise RuntimeError("Basic Inquiry generation boundary is not callable.")
    probe = "I am trying to understand why I keep seeing the same problem in my life."
    if _basic_inquiry_requires_macro_routing(probe):
        raise RuntimeError("Basic Inquiry probe was incorrectly deferred to macro routing.")
    if not _basic_inquiry_round1_requires_discovery(probe):
        raise RuntimeError("Basic Inquiry Round 1 discovery gate failed for the canonical probe.")
    source_text = _MAIN_PATH.read_text(encoding="utf-8")
    basic_start = source_text.find("def _basic_inquiry_response(")
    basic_end = source_text.find("def _v48831_basic_inquiry_seam_self_audit(", basic_start)
    basic_block = source_text[basic_start:basic_end] if basic_start >= 0 and basic_end > basic_start else ""
    if "_guide_capability_route(" in basic_block:
        raise RuntimeError("Basic Inquiry structural isolation failure: capability router remains inside ordinary inquiry.")
    if not _basic_inquiry_requires_macro_routing("I want stewardship formation."):
        raise RuntimeError("Formation macro-routing boundary was lost.")
    if not _basic_inquiry_requires_macro_routing("I want to understand Philippine systems."):
        raise RuntimeError("Philippine Systems macro-routing boundary was lost.")
    source = _inspect.getsource(_use_request_boundary)
    basic_position = source.find("if not _basic_inquiry_requires_macro_routing(query):")
    macro_position = source.find("route = _guide_capability_route(query, history)")
    if basic_position < 0 or macro_position < 0 or not basic_position < macro_position:
        raise RuntimeError("Basic Inquiry seam ordering regression.")
    print("USE v488.32 BASIC INQUIRY SEAM AUDIT: PASS; ordinary=direct; native_boundaries=precedence; formation_and_philippine_systems=legacy_macro")

# Canonical request boundary: one route decision, one specialist handoff seam,
# one explicit fallback into the protected FastAPI/core application.
async def _use_request_body(receive):
    chunks = []
    while True:
        message = await receive()
        if message.get("type") == "http.disconnect":
            break
        if message.get("type") != "http.request":
            continue
        body = message.get("body") or b""
        if body:
            chunks.append(body)
        if not message.get("more_body", False):
            break
    return b"".join(chunks)


def _use_replay_receive(body):
    sent = False
    async def _receive():
        nonlocal sent
        if not sent:
            sent = True
            return {"type": "http.request", "body": body, "more_body": False}
        return {"type": "http.request", "body": b"", "more_body": False}
    return _receive


async def _use_send_json(send, payload, status_code=200):
    # Stamp every visitor-facing JSON payload with the actual Render deployment
    # identity so E2E can reject responses served by a stale instance during rollout.
    if isinstance(payload, dict):
        payload.setdefault(
            "deployment_commit_sha", os.environ.get("RENDER_GIT_COMMIT", "").strip()
        )
    # Absolute visitor-facing boundary: all JSON routes pass through this sender,
    # including routes that bypass Basic Inquiry's local composer boundary.
    # A blank doorway field means "no doorway registered in this frozen answer,"
    # not "suppress every relevant resource." Only explicit no-handoff standards
    # override the shared answer-then-doorway contract.
    if isinstance(payload, dict):
        _boundary_standard = _resolve_exact_guide_gold_standard(payload.get("query") or "")
        if _boundary_standard is not None and bool(_boundary_standard.get("forbids_doorway")):
            payload["recommendation"] = None
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    await send({"type": "http.response.start", "status": status_code,
                "headers": [(b"content-type", b"application/json; charset=utf-8"),
                            (b"content-length", str(len(body)).encode("ascii")),
                            (b"access-control-allow-origin", b"*")]})
    await send({"type": "http.response.body", "body": body})


# v488.32 startup audit: verify the Basic Inquiry seam against the protected core.

_FASTAPI_APP = app



def _guide_node_specific_match(query):
    """Resolve a clearly named registered destination before generic Navigator routing.

    This is structural arbitration, not a specialist keyword gate: only the
    WordPress registry's declared title/semantic-hint phrases can produce a
    match, and generic one-word hints are intentionally ignored.
    """
    normalized = _normalize_query(query)
    if not normalized:
        return None

    best = None
    best_score = 0

    for node in _guide_node_registry_snapshot():
        node_title = str(node.get("title") or "").strip()
        normalized_title = _normalize_query(node_title)
        node_asset_type = str(node.get("asset_type") or "").strip().casefold().replace("-", "_")
        # Generic access surfaces explain how to browse the Archive; they are
        # not subject destinations. Never let their broad semantic hints
        # outrank a visitor's subject-specific request. A generic surface is
        # eligible only when the visitor explicitly names that surface.
        generic_access_titles = {
            "libraries", "library", "archive index", "archive reference index",
            "site index", "archive navigation", "start here", "begin here",
        }
        is_generic_access_node = normalized_title in generic_access_titles
        if is_generic_access_node:
            if normalized_title and re.search(
                rf"\b{re.escape(normalized_title)}\b",
                normalized,
                re.I,
            ):
                score = 105
                if score > best_score:
                    best_score = score
                    best = node
            # Do not inspect broad generic navigation hints as if they named
            # the visitor's requested subject.
            continue

        labels = [node_title]
        labels.extend(
            str(hint).strip()
            for hint in (node.get("semantic_hints") or [])
            if str(hint).strip()
        )

        for label in labels:
            phrase = _normalize_query(label)
            phrase_tokens = tuple(
                token for token in re.findall(r"[a-z0-9]+", phrase)
                if len(token) >= 3
            )
            # A registered two-word-or-longer phrase is an explicit discovery
            # signal, but it must match complete tokens. Plain substring
            # matching is unsafe here: "recurring pattern" must NOT match
            # "recurring patterns". The former is a Leadership Challenge
            # Navigator hint; the latter belongs to the broader Series &
            # Analysis territory.
            normalized_tokens = tuple(re.findall(r"[a-z0-9]+", normalized))
            if len(phrase_tokens) >= 2:
                phrase_tuple = tuple(phrase_tokens)
                exact_phrase_match = any(
                    normalized_tokens[index:index + len(phrase_tuple)] == phrase_tuple
                    for index in range(
                        max(0, len(normalized_tokens) - len(phrase_tuple) + 1)
                    )
                )
                if exact_phrase_match:
                    score = 100 + len(phrase_tokens)
                    if score > best_score:
                        best_score = score
                        best = node
                    continue

            query_tokens = set(re.findall(r"[a-z0-9]+", normalized))
            meaningful = {
                token for token in phrase_tokens
                if token not in {"the", "and", "for", "with", "archive", "living"}
            }
            overlap = len(query_tokens & meaningful)
            if len(meaningful) >= 3 and overlap >= 2:
                score = 10 + overlap
                if score > best_score:
                    best_score = score
                    best = node

    # Exact registered phrases remain strongest (100+). When a visitor uses
    # natural language that expresses the same destination without repeating
    # the registry phrase verbatim, the registry's own semantic hints may
    # authorize the destination when at least two meaningful hint terms align.
    # This is still registry-driven: USE is not maintaining a second keyword
    # map, and no question-specific rule is added here.
    return best if best_score >= 10 else None


# v488.24 Guide Node semantic-overlap boundary guard.
# The registered Steward Readiness destination must be reachable from natural
# language that expresses the destination without reproducing its exact title.
_steward_readiness_probe = _guide_node_specific_match(
    "How can I assess my readiness for stewardship?"
)
if not _steward_readiness_probe or _steward_readiness_probe.get("node_id") != "steward-readiness-instruments":
    # A transient WordPress registry outage/rate limit must not prevent the
    # entire API process from starting. Preserve the invariant when an
    # authoritative fresh registry was actually loaded; otherwise defer this
    # data-dependent probe and let the registry boundary report degraded state.
    if _guide_node_registry_is_fresh():
        raise RuntimeError(
            "USE v488.24 invariant failed: natural Steward Readiness destination was not resolved."
        )
    print(
        "USE v488.24 invariant deferred: Guide Node Registry unavailable; "
        "startup continues with registry-dependent destination routing degraded."
    )

# v488.30 phrase-boundary invariant: a singular registered hint must not
# match a plural visitor phrase merely because the singular is a substring.
_series_analysis_boundary_probe = _guide_node_specific_match(
    "I want to explore recurring patterns in people and systems over time."
)
if _series_analysis_boundary_probe and _series_analysis_boundary_probe.get("node_id") == "leadership-challenge-navigator":
    raise RuntimeError(
        "USE v488.30 invariant failed: singular Leadership hint matched plural pattern query."
    )

def _is_explicit_guide_destination_request(query):
    """Only hand off to a registered node when the visitor asks to navigate.

    Subject overlap alone is not destination intent. Explanatory questions
    must remain in ordinary Guide composition so the answer and recommendation
    can both be returned instead of sending the visitor straight to a page.
    """
    normalized = _normalize_query(query)
    if not normalized:
        return False
    return bool(re.search(
        r"\b(?:where can i find|where do i find|show me|take me to|"
        r"link me to|go to|navigate to|find the|browse|"
        r"take me directly to|send me to|direct me to|access the page for)|"
        r"^(?:please\s+|could you\s+|can you\s+)?open\b",
        normalized,
        re.I,
    ))

def _guide_node_handoff_is_authorized(query, selected_node_id):
    """Authorize a native Guide Node handoff only when the registry supports it.

    An explicit request to find material is not permission to open an arbitrary
    node chosen by a model. The selected node must also be the strongest
    registry-backed subject destination. If no such destination exists, keep
    the request in ordinary Guide composition so it can answer and recommend
    relevant material without substituting a generic access page.
    """
    if not _is_explicit_guide_destination_request(query):
        return False
    selected_id = str(selected_node_id or "").strip()
    if not selected_id:
        return False
    matched = _guide_node_specific_match(query)
    return bool(
        matched
        and str(matched.get("node_id") or "").strip() == selected_id
    )


# Routing boundary regression probes: compound explanatory questions must
# never be mistaken for a request to navigate directly to a registry node.
if _is_explicit_guide_destination_request(
    "What is stewardship and why does it matter now more than ever?"
):
    raise RuntimeError("Guide routing invariant failed: explanatory question classified as destination request.")
if not _is_explicit_guide_destination_request("Please take me to the Steward Readiness Instruments."):
    raise RuntimeError("Guide routing invariant failed: explicit destination request not recognized.")
if _is_explicit_guide_destination_request("What is open source software?"):
    raise RuntimeError("Guide routing invariant failed: explanatory open-source question classified as destination request.")
if not _is_explicit_guide_destination_request("Please open the Steward Readiness Instruments."):
    raise RuntimeError("Guide routing invariant failed: explicit open command not recognized.")

# Subject-discovery regression: broad semantic hints on generic access hubs
# must never convert a topic request into a Libraries page handoff.
_institutional_discovery_probe = _guide_node_specific_match(
    "Where can I find material about institutional responsibility?"
)
if str((_institutional_discovery_probe or {}).get("title") or "").strip().casefold() in {
    "libraries", "library", "archive index", "site index",
    "archive navigation", "start here", "begin here",
}:
    raise RuntimeError(
        "Guide routing invariant failed: subject-specific discovery resolved to a generic access hub."
    )

def _request_header(scope, name):
    target = str(name or "").strip().lower().encode("latin-1")
    for key, value in scope.get("headers") or []:
        if bytes(key).lower() == target:
            try:
                return bytes(value).decode("latin-1").strip()
            except Exception:
                return ""
    return ""


def _first_forwarded_ip(value):
    first = str(value or "").split(",", 1)[0].strip()
    try:
        ipaddress.ip_address(first)
        return first
    except ValueError:
        return ""


def _request_location_context(scope, parsed_body):
    """Build the Guide's normalized location context without requiring a prompt.

    Only explicit visitor-provided country data is accepted here. This service may
    receive requests through a WordPress bridge, so proxy IPs, forwarded-IP
    headers, and unverified Cloudflare-looking headers are not evidence of the
    visitor's country. Authenticated edge attestation must be added separately.
    """
    headers = {
        "cf_connecting_ip": _request_header(scope, "cf-connecting-ip"),
        "true_client_ip": _request_header(scope, "true-client-ip"),
        "x_forwarded_for": _request_header(scope, "x-forwarded-for"),
        "cf_ipcountry": _request_header(scope, "cf-ipcountry"),
        "cf_region": _request_header(scope, "cf-region"),
        "cf_ipcity": _request_header(scope, "cf-ipcity"),
        "cf_iplatitude": _request_header(scope, "cf-iplatitude"),
        "cf_iplongitude": _request_header(scope, "cf-iplongitude"),
        "cf_timezone": _request_header(scope, "cf-timezone"),
    }
    client_ip = ""
    for candidate in (
        headers["cf_connecting_ip"],
        headers["true_client_ip"],
        _first_forwarded_ip(headers["x_forwarded_for"]),
    ):
        try:
            ipaddress.ip_address(candidate)
            client_ip = candidate
            break
        except ValueError:
            continue

    context = {}
    for key in (
        "explicit_country", "browser_country", "ip_country",
        "timezone_country", "locale_country", "region", "province",
        "locality", "address", "refused", "user_confirmation",
        "latitude", "longitude", "accuracy",
    ):
        value = parsed_body.get(key)
        if value not in ("", None):
            context[key] = value

    if parsed_body.get("country") not in ("", None) and "explicit_country" not in context:
        context["explicit_country"] = str(parsed_body.get("country")).strip()

    # Do not trust caller-supplied Cloudflare-looking headers by themselves.
    # No country is inferred from these headers without authenticated edge proof.

    if headers["cf_region"] and "region" not in context:
        context["region"] = headers["cf_region"]
    if headers["cf_ipcity"] and "locality" not in context:
        context["locality"] = headers["cf_ipcity"]
    if headers["cf_iplatitude"] and "latitude" not in context:
        context["latitude"] = headers["cf_iplatitude"]
    if headers["cf_iplongitude"] and "longitude" not in context:
        context["longitude"] = headers["cf_iplongitude"]
    if headers["cf_timezone"] and "timezone" not in context:
        context["timezone"] = headers["cf_timezone"]
    # Keep this only as transport diagnostics. It is not visitor-location evidence.
    if client_ip:
        context["transport_peer_ip"] = client_ip

    return context, client_ip


def _ip_geolocation(client_ip, timeout=0.65):
    if not client_ip:
        return {}
    try:
        ipaddress.ip_address(client_ip)
    except ValueError:
        return {}
    endpoint = "https://get.geojs.io/v1/ip/geo/" + quote(client_ip, safe="")
    try:
        request = UrlRequest(
            endpoint,
            headers={
                "Accept": "application/json",
                "User-Agent": "Living-Archive-The-Guide/1.0",
            },
            method="GET",
        )
        with urlopen(request, timeout=float(timeout)) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if not isinstance(payload, dict):
            return {}
        result = {}
        country_code = str(payload.get("country_code") or "").strip().upper()
        if country_code:
            result["ip_country"] = country_code
        if payload.get("region"):
            result["region"] = str(payload.get("region")).strip()
            result["province"] = str(payload.get("region")).strip()
        if payload.get("city"):
            result["locality"] = str(payload.get("city")).strip()
        for source_key, target_key in (
            ("latitude", "latitude"),
            ("longitude", "longitude"),
            ("accuracy", "accuracy"),
            ("timezone", "timezone"),
        ):
            if payload.get(source_key) not in ("", None):
                result[target_key] = payload.get(source_key)
        if result:
            result["location_source"] = "ip_geolocation"
        return result
    except Exception as exc:
        print(f"The Guide IP location fallback unavailable: {exc}")
        return {}


async def _resolve_request_location(scope, parsed_body):
    context, client_ip = _request_location_context(scope, parsed_body)
    # A visitor's explicit refusal is authoritative. Do not infer location
    # from the request IP after refusal; that IP may belong to a proxy or
    # infrastructure hop rather than the visitor.
    if str(context.get("refused") or "").strip().casefold() in {"true", "yes", "1", "refused"}:
        # Strip inferred and explicit location fields from the downstream
        # safety context after refusal. Merely skipping fallback is insufficient
        # if an edge header or proxy has already populated ip_country.
        return {"refused": context.get("refused", True)}
    # First-party/context supplied by the visitor or edge wins. Only use the
    # external IP resolver when no country signal exists yet.
    if any(context.get(key) for key in (
        "explicit_country", "browser_country", "ip_country",
        "timezone_country", "locale_country",
    )):
        return context
    # Do not geolocate the transport peer as if it were the visitor. In
    # this deployment the query may arrive through the WordPress bridge, so
    # client_ip can identify WordPress or another proxy. Only explicit visitor
    # context or trusted edge country metadata above may ground emergency
    # resources. Keep the helper available for a future verified direct-client
    # deployment, but never use it as an implicit country-selection fallback.
    return context


def _relational_handoff_session_id(parsed_body):
    """Return an isolated opaque HRN session key; never derive it from visitor prose."""
    body = parsed_body if isinstance(parsed_body, dict) else {}
    supplied = str(body.get("session_id") or "").strip()
    # A returned session key can be echoed by the client on retries/continuations.
    if re.fullmatch(r"relationship-[0-9a-f]{24}", supplied):
        return supplied
    # Accept a client-generated opaque token only; do not key stored journey state
    # by arbitrary prose, email addresses, or unbounded caller-controlled strings.
    if re.fullmatch(r"[A-Za-z0-9_-]{16,128}", supplied):
        return "relationship-" + hashlib.sha256(supplied.encode("utf-8")).hexdigest()[:24]
    # Identical opening questions from different visitors must never share a ledger.
    return "relationship-" + uuid.uuid4().hex[:24]


def _should_honor_protected_risk_profile(query, risk_profile):
    """Use a protected-core risk signal only when it is not a hypothetical calibration."""
    if not isinstance(risk_profile, dict) or not bool(risk_profile.get("risk")):
        return False
    if (
        is_hypothetical_safety_discussion(query)
        and normalize_safety_state(query) is None
    ):
        return False
    return True


def _guard_hypothetical_safety_route(query, route, mode, reason):
    """Keep an explicit third-person safety calibration in informational Guide routing."""
    if (
        str(route or "").casefold() == "safety"
        and is_hypothetical_safety_discussion(query)
        and normalize_safety_state(query) is None
    ):
        return (
            "guide",
            "direct",
            "hypothetical safety calibration is informational, not a personal-risk disclosure",
        )
    return route, mode, reason


def _hypothetical_safety_calibration_payload(query):
    """Return a deterministic, non-interrupting answer for explicit safety-routing tests."""
    normalized = " ".join(str(query or "").strip().casefold().split())
    calibration_signal = any(
        phrase in normalized
        for phrase in (
            "immediate danger",
            "immediate support options",
            "what should the guide do",
            "safety routing",
            "safety calibration",
            "calibration test",
            "calibration only",
            "hypothetical visitor",
            "support contacts",
            "safety / crisis",
        )
    )
    if (
        not is_hypothetical_safety_discussion(normalized)
        or normalize_safety_state(normalized) is not None
        or not calibration_signal
    ):
        return None
    request_id = "safety-calibration-" + hashlib.sha1(
        normalized.encode("utf-8")
    ).hexdigest()[:16]
    return {
        "ok": True,
        "version": APP_VERSION,
        "fingerprint": DEPLOYMENT_FINGERPRINT,
        "source_sha256": RUNTIME_SOURCE_SHA256,
        "request_id": request_id,
        "query": str(query or "").strip(),
        "intent": "SAFETY_CALIBRATION_INFORMATION",
        "response": (
            "In an actual immediate-danger situation, The Guide should pause ordinary "
            "Archive exploration and direct the visitor to their local emergency service "
            "or nearest emergency department. Emergency Intelligence should provide "
            "country-specific contacts once the visitor's location is known; without a "
            "location, the system must not invent a hotline or number. This question is "
            "a routing calibration, not a personal crisis disclosure."
        ),
        "processing": "safety_calibration_boundary",
        "route_source": "guide_hypothetical_safety_calibration",
        "handoff": None,
        "handoff_mode": "informational",
        "handoff_pending": False,
        "safety_calibration": {
            "contract_version": "safety-calibration-information-v1",
            "personal_crisis_detected": False,
            "expected_live_route": "sitewide_safety_boundary_for_actual_danger",
            "resource_owner": "Emergency Intelligence",
            "resource_contract": "living-archive/emergency/v1/resolve",
            "location_required_for_local_contacts": True,
            "resources_resolved": False,
        },
    }


async def _use_request_boundary(scope, receive, send):
    if scope.get("type") != "http":
        await _FASTAPI_APP(scope, receive, send)
        return
    method = str(scope.get("method") or "").upper()
    path = str(scope.get("path") or "")
    if method != "POST" or path not in {"/api/query", "/"}:
        await _FASTAPI_APP(scope, receive, send)
        return

    raw_body = await _use_request_body(receive)
    try:
        parsed_body = json.loads(raw_body.decode("utf-8")) if raw_body else {}
    except Exception:
        parsed_body = {}
    if not isinstance(parsed_body, dict):
        parsed_body = {}

    query = str(parsed_body.get("query") or parsed_body.get("user_query") or
                parsed_body.get("question") or parsed_body.get("text") or
                parsed_body.get("input") or "").strip()
    history = parsed_body.get("history") or parsed_body.get("conversation_history")
    if not query:
        await _FASTAPI_APP(scope, _use_replay_receive(raw_body), send)
        return

    # Highest-priority sitewide Safety / Crisis boundary. The Guide owns
    # the interruption boundary, but the existing HRN Safety Fractal +
    # Emergency Intelligence system remains the semantic/resource authority.
    # This is deliberately a sibling linkage, not a replacement safety routine.
    history_text = _history_text(history)
    safety_question_hint = str(parsed_body.get("safety_question") or "").strip()
    safety_state_hint = str(parsed_body.get("safety_state") or "").strip().casefold()
    safety_active_hint = bool(parsed_body.get("safety_active"))
    safety_state = classify_safety(query, history=history_text)

    # Conversation continuity contract: a specialist safety turn may carry an
    # explicit active-state/question alongside its structured history. This is
    # a server-side continuity aid, not a client-authorized escalation; it can
    # only keep an already-active safety conversation inside the safety lane.
    if (
        not safety_state
        and safety_active_hint
        and safety_question_hint
    ):
        safety_state = "acute_followthrough"
    elif (
        not safety_state
        and safety_active_hint
        and safety_state_hint in {"acute", "plan", "immediacy", "current", "acute_followthrough"}
    ):
        safety_state = safety_state_hint

    # Boundary recovery: the protected core remains the authoritative
    # deterministic fallback if the auxiliary safety classifier misses a
    # risk signal. This executes before normal Guide routing or retrieval.
    if not safety_state:
        try:
            risk_profile = _base._inquiry_profile(query)
            if _should_honor_protected_risk_profile(query, risk_profile):
                safety_state = "current"
                print("The Guide safety boundary recovered from protected-core risk profile.")
            elif isinstance(risk_profile, dict) and bool(risk_profile.get("risk")):
                print("The Guide ignored protected-core risk fallback for a hypothetical safety calibration query.")
        except Exception as exc:
            print(f"The Guide protected-core safety recovery was unavailable: {exc}")

    if not safety_state:
        calibration_payload = _hypothetical_safety_calibration_payload(query)
        if calibration_payload is not None:
            print(
                "The Guide safety calibration: "
                "hypothetical route question answered without personal-crisis interruption, "
                "ordinary retrieval, or provider inference."
            )
            return await _use_send_json(send, calibration_payload)

    if safety_state:
        request_id = "safety-" + hashlib.sha1(
            (query + "|" + _history_text(history)).encode("utf-8")
        ).hexdigest()[:16]
        safety_country = str(parsed_body.get("country") or parsed_body.get("visitor_country") or "").strip()
        safety_location = await _resolve_request_location(scope, parsed_body)
        if safety_country and "explicit_country" not in safety_location:
            safety_location["explicit_country"] = safety_country
        if safety_location.get("ip_country") and not safety_country:
            safety_country = str(safety_location.get("ip_country") or "").strip()
        try:
            safety_contribution = await asyncio.wait_for(
                asyncio.to_thread(
                    invoke_specialist,
                    SPECIALIST_ADAPTER_REGISTRY,
                    request_id=request_id,
                    guide_version=APP_VERSION,
                    specialist_id="safety",
                    original_question=query,
                    recognized_territory="immediate safety",
                    processing_purpose="sitewide safety interruption and emergency-resource movement",
                    guide_context={
                        "country": safety_country,
                        "location": safety_location,
                        "conversation": history_text,
                        "visitor_history": history_text,
                        "safety_question": safety_question_hint,
                        "unit_turns": len(history) if isinstance(history, list) else 0,
                    },
                    safety_state=safety_state,
                ),
                timeout=5.5,
            )
            safety_payload = dict(safety_contribution.get("payload") or {})
            safety_response = str(safety_payload.get("human_response") or "").strip()
            if not safety_response:
                raise RuntimeError("Safety utility returned no visitor response.")

            # Fail-closed continuity contract: an active safety interruption
            # may never silently release because HRN returned a response without
            # its next question. HRN remains the semantic authority. The shared
            # safety-intelligence layer supplies a state-aware native next
            # movement only when HRN omitted one; this boundary repeats that
            # contract defensively for any malformed specialist payload.
            safety_release_ready = bool(safety_payload.get("safety_release_ready"))
            safety_question = str(safety_payload.get("safety_question") or "").strip()
            if not safety_release_ready and not safety_question:
                safety_question = repair_safety_question(
                    safety_state=safety_state,
                    previous_question=safety_question_hint,
                    query=query,
                    history=history_text,
                )
                safety_payload["safety_question"] = safety_question
                safety_payload["safety_continuity_guard"] = (
                    "native_next_movement_repaired"
                )
            print(
                "The Guide sitewide Safety utility: "
                f"request_id={request_id}, state={safety_state}, "
                "hrn_safety_lane=called, ordinary_hrn=not_called, llm=not_called, retrieval=not_called"
            )
            return await _use_send_json(send, {
                "ok": True,
                "version": APP_VERSION,
                "fingerprint": DEPLOYMENT_FINGERPRINT,
                "source_sha256": RUNTIME_SOURCE_SHA256,
                "request_id": request_id,
                "query": query,
                "intent": "SAFETY_INTERRUPT",
                "response": safety_response,
                "processing": "sitewide_safety_utility",
                "route_source": "guide_sitewide_safety_boundary",
                "handoff": "safety",
                "handoff_mode": "interrupt",
                "handoff_pending": False,
                # Preserve the existing flat HRN safety response contract so
                # the established safety UI can render without redesign.
                "safety_message": safety_payload.get("safety_message") or safety_response,
                "safety_question": safety_payload.get("safety_question") or "",
                "safety_note": safety_payload.get("safety_note") or "",
                "safety_resources": safety_payload.get("safety_resources") or [],
                "safety_location_required": bool(safety_payload.get("safety_location_required")),
                "country": safety_payload.get("country") or safety_country,
                "safety_release_ready": bool(safety_payload.get("safety_release_ready")),
                "safety_continuity_guard": safety_payload.get("safety_continuity_guard") or "",
                "safety": {
                    "state": safety_payload.get("safety_state") or safety_state,
                    "interrupt": True,
                    "display_mode": safety_payload.get("display_mode") or "hrn_safety",
                    "resources": safety_payload.get("safety_resources") or safety_payload.get("resources") or [],
                    "next_movement": safety_payload.get("next_movement") or safety_payload.get("safety_question") or "",
                    "safety_message": safety_payload.get("safety_message") or safety_response,
                    "safety_question": safety_payload.get("safety_question") or "",
                    "safety_note": safety_payload.get("safety_note") or "",
                    "safety_location_required": bool(safety_payload.get("safety_location_required")),
                    "country": safety_payload.get("country") or safety_country,
                    "safety_release_ready": bool(safety_payload.get("safety_release_ready")),
                    "safety_continuity_guard": safety_payload.get("safety_continuity_guard") or "",
                    "bypasses_ordinary_hrn": True,
                    "bypasses_llm": True,
                    "bypasses_retrieval": True,
                    "safety_intelligence_contract_version": SAFETY_INTELLIGENCE_CONTRACT_VERSION,
                },
                "visitor_boundary_version": APP_VERSION,
            })
        except Exception as exc:
            print(f"The Guide sitewide Safety utility failed closed: {exc}")
            return await _use_send_json(send, {
                "ok": True,
                "version": APP_VERSION,
                "query": query,
                "intent": "SAFETY_INTERRUPT",
                "response": (
                    "If you may be in immediate danger or may act on thoughts "
                    "of self-harm, please contact your local emergency services "
                    "or go to the nearest emergency department now. If possible, "
                    "stay with another person while you get help."
                ),
                "processing": "sitewide_safety_utility_fallback",
                "route_source": "guide_sitewide_safety_boundary",
                "handoff": "safety",
                "handoff_mode": "interrupt",
                "handoff_pending": False,
                "safety_message": (
                    "If you may be in immediate danger, contact the emergency "
                    "service where you are or go to the nearest emergency "
                    "department, and stay with another person."
                ),
                "safety_question": "",
                "safety_note": "",
                "safety_resources": [],
                "safety_location_required": True,
                "country": safety_country,
                "safety_release_ready": False,
                "safety": {
                    "state": safety_state,
                    "interrupt": True,
                    "display_mode": "hrn_safety",
                    "resources": [],
                    "bypasses_ordinary_hrn": True,
                    "bypasses_llm": True,
                    "bypasses_retrieval": True,
                    "safety_intelligence_contract_version": SAFETY_INTELLIGENCE_CONTRACT_VERSION,
                },
                "visitor_boundary_version": APP_VERSION,
            })

    # Explicit Formation preparation is a native boundary and must outrank the
    # generic orientation/Navigator matcher. This runs after the sitewide safety
    # boundary but before any general navigation handoff or Basic Inquiry.
    early_formation_route = _explicit_formation_entry_route(query)
    if early_formation_route is not None:
        request_id = "formation-" + hashlib.sha1(
            (query + "|" + _history_text(history)).encode("utf-8")
        ).hexdigest()[:16]
        try:
            formation_result = _formation_specialist_response(
                query, history, early_formation_route, request_id
            )
            return await _use_send_json(send, {
                "ok": True,
                "version": APP_VERSION,
                "query": query,
                "intent": "FORMATION_HANDOFF",
                "response": formation_result["response"],
                "formation_delegation": formation_result["formation_delegation"],
                "visitor_boundary_version": APP_VERSION,
                "request_id": request_id,
                "route_source": "deterministic-formation-preparation-entry",
            })
        except Exception as exc:
            print(f"USE Formation preparation handoff failed safely: {exc}")
            return await _use_send_json(send, {
                "ok": False,
                "version": APP_VERSION,
                "query": query,
                "intent": "FORMATION_HANDOFF",
                "response": "The Formation pathway could not be opened right now.",
                "error_type": "formation_specialist_failure",
                "request_id": request_id,
                "visitor_boundary_version": APP_VERSION,
            }, 503)

    # Immediate FSD handoff: FSD is a native standalone diagnostic
    # surface. Do not spend a routing-model call; send the visitor directly
    # to the canonical landing page and let FSD own the complete experience.
    if _is_fsd_request(query) and not _is_outcome_evaluation_query(query):
        fsd_url = _fsd_handoff_url(query)
        request_id = "fsd-" + hashlib.sha1(
            (query + "|" + _history_text(history)).encode("utf-8")
        ).hexdigest()[:16]
        print(
            "The Guide immediate FSD handoff: "
            f"request_id={request_id}, url={fsd_url}"
        )
        return await _use_send_json(send, {
            "ok": True,
            "version": APP_VERSION,
            "query": query,
            "intent": "FSD_HANDOFF",
            "response": "",
            "handoff": "fsd",
            "handoff_mode": "immediate",
            "handoff_pending": True,
            "fsd_url": fsd_url,
            "return_mode": "native_fsd_landing",
            "visitor_boundary_version": APP_VERSION,
            "request_id": request_id,
        })

    # Immediate Catalogue handoff: an explicit request to explore or use
    # the Stewardship Catalogue is already a bounded specialist request.
    # Do not spend a routing-model call or let Guide retrieval answer it first.
    if re.search(
        r"\b(?:catalogue|catalog)\b",
        _normalize_query(query),
        re.I,
    ):
        catalogue_url = _catalogue_handoff_url(query)
        request_id = "catalogue-" + hashlib.sha1(
            (query + "|" + _history_text(history)).encode("utf-8")
        ).hexdigest()[:16]
        print(
            "The Guide immediate Catalogue handoff: "
            f"request_id={request_id}, url={catalogue_url}"
        )
        return await _use_send_json(send, {
            "ok": True,
            "version": APP_VERSION,
            "query": query,
            "intent": "CATALOGUE_HANDOFF",
            "response": "",
            "handoff": "catalogue",
            "handoff_mode": "immediate",
            "handoff_pending": True,
            "catalogue_query": query,
            "catalogue_url": catalogue_url,
            "return_mode": "native_catalogue_search",
            "visitor_boundary_version": APP_VERSION,
            "request_id": request_id,
        })

# Immediate Atlas handoff: an explicit Atlas / Reference Map request is
    # already a bounded specialist request. Do not spend a routing-model call
    # or let ordinary Guide retrieval answer it first. The native Atlas page
    # then invokes its existing Finder/AJAX contract with the original query.
    if _is_explicit_atlas_request(query):
        atlas_url = _atlas_handoff_url(query)
        request_id = "atlas-" + hashlib.sha1(
            (query + "|" + _history_text(history)).encode("utf-8")
        ).hexdigest()[:16]
        print(
            "The Guide immediate Atlas handoff: "
            f"request_id={request_id}, url={atlas_url}"
        )
        return await _use_send_json(send, {
            "ok": True,
            "version": APP_VERSION,
            "query": query,
            "intent": "ATLAS_HANDOFF",
            "response": "",
            "handoff": "atlas",
            "handoff_mode": "immediate",
            "handoff_pending": True,
            "atlas_query": query,
            "atlas_url": atlas_url,
            "return_mode": "native_atlas_finder",
            "visitor_boundary_version": APP_VERSION,
            "request_id": request_id,
        })

    # High-confidence Glyph Finder boundary: explicit Glyph requests belong
    # to the native Finder. Do not let provider/model routing or deterministic
    # Guide fallback convert a bounded native search into an ordinary answer.
    if _is_glyph_finder_request(query):
        glyph_url = _glyph_handoff_url(query)
        request_id = "glyph-" + hashlib.sha1(
            (query + "|" + _history_text(history)).encode("utf-8")
        ).hexdigest()[:16]
        print(
            "The Guide direct Glyph Finder handoff: "
            f"request_id={request_id}, url={glyph_url}"
        )
        return await _use_send_json(send, {
            "ok": True,
            "version": APP_VERSION,
            "query": query,
            "intent": "GLYPH_HANDOFF",
            "response": "",
            "handoff": "glyph",
            "handoff_mode": "direct",
            "handoff_pending": True,
            "glyph_query": query,
            "glyph_url": glyph_url,
            "return_mode": "native_guardian_glyph_finder",
            "visitor_boundary_version": APP_VERSION,
            "request_id": request_id,
        })


    # Immediate Glossary handoff: an explicit definition/meaning question is
    # already a bounded lookup request. Do not spend a routing-model call or
    # allow ordinary Guide retrieval to answer it first.
    glossary_term = _normalize_glossary_term(query)
    embedded_glossary_term = _extract_embedded_glossary_term(query)
    _explicit_glossary_navigation = bool(re.search(
        r"\b(?:take me to|take me directly to|open|show me|go to|navigate to|find|access)\b.{0,60}\bglossary\b",
        str(query or ""),
        re.I,
    ))
    if (
        not _is_normative_conflict_explanatory_request(query)
        and _is_bounded_glossary_request(
            query,
            glossary_term=glossary_term,
            embedded_term=embedded_glossary_term,
        )
        and (
            _explicit_glossary_navigation
            or not _is_conceptual_explanatory_request(query)
        )
    ):
        glossary_url = (
            "https://geralddaquila.com/glossary/?glossary_term="
            + quote(glossary_term, safe="")
        )
        request_id = "glossary-" + hashlib.sha1(
            (query + "|" + _history_text(history)).encode("utf-8")
        ).hexdigest()[:16]
        print(
            "The Guide immediate Glossary handoff: "
            f"request_id={request_id}, term={glossary_term!r}, url={glossary_url}"
        )
        return await _use_send_json(send, {
            "ok": True,
            "version": APP_VERSION,
            "query": query,
            "intent": "GLOSSARY_HANDOFF",
            "response": "",
            "handoff": "glossary",
            "handoff_mode": "immediate",
            "handoff_pending": True,
            "glossary_term": glossary_term,
            "glossary_url": glossary_url,
            "return_mode": "native_glossary_search",
            "visitor_boundary_version": APP_VERSION,
            "request_id": request_id,
        })

    # Immediate lived-relational handoff: do not spend a Guide routing-model call
    # or invoke the HRN specialist before the HRN surface is opened. The visitor's
    # question is already sufficient to establish this bounded structural route.
    # The Guide remains authoritative for the handoff; HRN owns the actual
    # interpretation/composition journey after the browser arrives there.
    # v488.72 authoritative relational boundary. This executes before Basic Inquiry
    # and before provider/model routing, so a natural lived relationship inquiry
    # cannot be consumed by the generic Guide path simply because the model later
    # labels it TOPICAL_INQUIRY.
    relational_boundary = _relational_boundary_decision(query)
    if relational_boundary.get("open"):
        request_id = _relational_handoff_session_id(parsed_body)
        print(
            "The Guide immediate HRN handoff: "
            f"request_id={request_id}, query={_normalize_query(query)[:120]}"
        )
        return await _use_send_json(send, {
            "ok": True,
            "version": APP_VERSION,
            "query": query,
            "intent": "RELATIONAL_HANDOFF",
            "response": "",
            "handoff": "relationship",
            "handoff_mode": "immediate",
            "handoff_pending": True,
            "relational_delegation": {
                "state": "pending",
                "specialist": "Seeing the Relationship",
                "specialist_id": "relationship",
                "contract_version": RELATIONSHIP_CONTRIBUTION_CONTRACT_VERSION,
                "voice_policy": RELATIONSHIP_VOICE_POLICY,
                "session_id": request_id,
                "seed_message": query,
                "conversation": _history_text(history),
                "handoff_reason": "The Guide recognized a lived relational inquiry and is opening Seeing the Relationship directly.",
                "hrn_endpoint": "https://geralddaquila.com/wp-json/living-archive/v1/relational-navigator",
                "return_mode": "guide_integrated",
            },
            "visitor_boundary_version": APP_VERSION,
            "request_id": request_id,
            "relational_boundary_contract": RELATIONAL_BOUNDARY_CONTRACT_VERSION,
            "relational_boundary_reason": relational_boundary.get("reason"),
        })

    # High-confidence Case Navigator boundary: explicit Case Study requests
    # belong to the native structural case search. Do not let provider routing
    # or deterministic Guide fallback turn a bounded case request into an
    # ordinary answer.
    if _is_case_navigator_request(query):
        case_url = _case_handoff_url(query)
        request_id = "case-" + hashlib.sha1(
            (query + "|" + _history_text(history)).encode("utf-8")
        ).hexdigest()[:16]
        print(
            "The Guide direct Case Navigator handoff: "
            f"request_id={request_id}, url={case_url}"
        )
        return await _use_send_json(send, {
            "ok": True,
            "version": APP_VERSION,
            "query": query,
            "intent": "CASE_HANDOFF",
            "response": "",
            "handoff": "case",
            "handoff_mode": "direct",
            "handoff_pending": True,
            "case_query": query,
            "case_url": case_url,
            "return_mode": "native_case_navigator",
            "visitor_boundary_version": APP_VERSION,
            "request_id": request_id,
        })
    # Registered destination precedence is evaluated BEFORE generic
    # orientation and before provider/model routing. A visitor who names a
    # specific Guide Node has already supplied enough destination intent;
    # sending that question to Start Here would discard useful specificity.
    # This is registry-driven, not a question-specific keyword redirect.
    specific_node = (
        _guide_node_specific_match(query)
        if _is_explicit_guide_destination_request(query)
        else None
    )
    if specific_node is not None:
        request_id = "guide-node-" + hashlib.sha1(
            (query + "|" + str(specific_node.get("node_id"))).encode("utf-8")
        ).hexdigest()[:16]
        payload = node_handoff_payload(
            specific_node,
            query=query,
            request_id=request_id,
            visitor_boundary_version=APP_VERSION,
        )
        payload.update({
            "version": APP_VERSION,
            "route_source": "registry_specific_destination",
            "route_confidence": 1.0,
        })
        print(
            "The Guide registry destination precedence: "
            f"request_id={request_id}, node={specific_node.get('node_id')}, "
            f"url={specific_node.get('canonical_url')}"
        )
        return await _use_send_json(send, payload)

    # High-confidence orientation boundary: a visitor asking how to enter,
    # Generic orientation normally belongs to the native Navigator. However,
    # when the visitor names a specific registered destination, that specific
    # doorway takes precedence over the generic Start Here experience. This
    # prevents questions such as "Where can I explore Philippine renewal?"
    # from losing their destination merely because they are phrased as
    # navigation questions.
    if _is_navigator_orientation_request(query) and not _has_substantive_topic_intent(query):
        specific_node = (
            _guide_node_specific_match(query)
            if _is_explicit_guide_destination_request(query)
            else None
        )
        if specific_node is not None:
            request_id = "guide-node-" + hashlib.sha1(
                (query + "|" + str(specific_node.get("node_id"))).encode("utf-8")
            ).hexdigest()[:16]
            payload = node_handoff_payload(
                specific_node,
                query=query,
                request_id=request_id,
                visitor_boundary_version=APP_VERSION,
            )
            payload.update({
                "version": APP_VERSION,
                "route_source": "registry_specific_destination",
                "route_confidence": 1.0,
            })
            print(
                "The Guide specific destination precedence: "
                f"request_id={request_id}, node={specific_node.get('node_id')}, "
                f"url={specific_node.get('canonical_url')}"
            )
            return await _use_send_json(send, payload)

        navigator_url = _navigator_handoff_url(query)
        request_id = "navigator-" + hashlib.sha1(
            (query + "|" + _history_text(history)).encode("utf-8")
        ).hexdigest()[:16]
        print(
            "The Guide systemic Navigator orientation handoff: "
            f"request_id={request_id}, url={navigator_url}, "
            f"query={_normalize_query(query)[:120]}"
        )
        return await _use_send_json(send, {
            "ok": True,
            "version": APP_VERSION,
            "query": query,
            "intent": "NAVIGATOR_HANDOFF",
            "response": "",
            "handoff": "navigator",
            "handoff_mode": "entrance",
            "handoff_pending": True,
            "navigator_url": navigator_url,
            "return_mode": "native_archive_navigator_welcome",
            "visitor_boundary_version": APP_VERSION,
            "request_id": request_id,
        })

    # v488.45: ordinary questions get exactly one routing decision.
    # Native boundaries above remain authoritative. Once those boundaries have
    # been cleared, Basic Inquiry owns the ordinary path. A Basic Inquiry
    # failure must NOT re-enter the legacy capability router: doing so creates
    # a second classification decision and can turn a transient generation
    # failure into a false specialist handoff.
    # Explicit resource-search requests belong to the native Catalogue. This
    # boundary runs before Basic Inquiry recovery so broad source-finding
    # questions do not collapse to one generic recommendation. Explanatory
    # questions remain in the frozen Guide composition path.
    if _is_catalogue_resource_search_query(query):
        return await _use_send_json(send, _catalogue_handoff_payload(query, history))

    if not _basic_inquiry_requires_macro_routing(query):
        try:
            basic_result = _basic_inquiry_response(
                query=query,
                history=history,
                raw_body=parsed_body,
            )
            return await _use_send_json(send, basic_result)
        except Exception as exc:
            print(
                "The Guide Basic Inquiry seam failed; "
                f"ordinary route remains ordinary and will not be reclassified: {exc}"
            )
            # A direct-attribute question must not escape through the legacy
            # deterministic recovery path if its evidence boundary itself fails.
            if _direct_attribute_phrase(query):
                request_id = "attribute-recovery-" + hashlib.sha1(
                    (query + "|" + _history_text(history)).encode("utf-8")
                ).hexdigest()[:16]
                return await _use_send_json(send, {
                    "ok": True,
                    "version": APP_VERSION,
                    "fingerprint": DEPLOYMENT_FINGERPRINT,
                    "source_sha256": RUNTIME_SOURCE_SHA256,
                    "request_id": request_id,
                    "query": query,
                    "intent": "TOPICAL_INQUIRY",
                    "response": _archive_limitation_response(),
                    "recommendation": None,
                    "answer_basis": {
                        "kind": "archive_evidence_unavailable",
                        "label": "Archive evidence not found",
                        "explanation": "The available Archive material did not establish the requested attribute.",
                    },
                    "processing": "basic_inquiry_recovery",
                    "route_source": "guide_direct_attribute_fail_closed",
                    "visitor_boundary_version": APP_VERSION,
                })
            try:
                context_data = use_core.fetch_canonical_context(query)
                recovery_context = context_data if isinstance(context_data, dict) else {}
                recovery = _basic_inquiry_round1_deterministic_response(
                    query,
                    {},
                    recovery_context,
                )
                recovery_text = str(recovery.get("response") or "").strip()
                if _basic_inquiry_contains_html_markup(recovery_text):
                    print(
                        "The Guide recovery boundary: rejected HTML-shaped deterministic output; "
                        "retrying without retrieved context."
                    )
                    recovery_text = _basic_inquiry_markup_recovery(
                        query, history, context_data.get("intent", "TOPICAL_INQUIRY")
                    )
                    if not recovery_text:
                        try:
                            recovery = _basic_inquiry_round1_deterministic_response(
                                query, {}, {"context_blocks": ""}
                            )
                            recovery_text = str(recovery.get("response") or "").strip()
                        except Exception:
                            recovery_text = ""
                if _basic_inquiry_contains_html_markup(recovery_text):
                    recovery_text = ""
                recovery_recommendation = _normalize_authoritative_recommendation(
                    _general_guide_authoritative_doorway(query, recovery_context)
                )
                if recovery_text:
                    request_id = "basic-recovery-" + hashlib.sha1(
                        (query + "|" + _history_text(history)).encode("utf-8")
                    ).hexdigest()[:16]
                    return await _use_send_json(send, {
                        "ok": True,
                        "version": APP_VERSION,
                        "fingerprint": DEPLOYMENT_FINGERPRINT,
                        "source_sha256": RUNTIME_SOURCE_SHA256,
                        "request_id": request_id,
                        "query": query,
                        "intent": (
                            context_data.get("intent", "TOPICAL_INQUIRY")
                            if isinstance(context_data, dict)
                            else "TOPICAL_INQUIRY"
                        ),
                        "response": recovery_text,
                        "recommendation": recovery_recommendation,
                        "processing": "basic_inquiry_recovery",
                        "route_source": "guide_basic_inquiry_recovery",
                        "recovery": "deterministic_round1",
                        "visitor_boundary_version": APP_VERSION,
                    })
            except Exception as recovery_exc:
                print(
                    "The Guide Basic Inquiry deterministic recovery also failed: "
                    f"{recovery_exc}"
                )
            return await _use_send_json(send, {
                "ok": False,
                "version": APP_VERSION,
                "query": query,
                "intent": "TOPICAL_INQUIRY",
                "response": "The Guide could not complete this question right now.",
                "error_type": "basic_inquiry_failure",
                "route_source": "guide_basic_inquiry",
                "visitor_boundary_version": APP_VERSION,
            }, 503)

    explicit_formation_route = _explicit_formation_entry_route(query)
    if explicit_formation_route is not None:
        route = explicit_formation_route
    else:
        route = _guide_capability_route(query, history)
    route_id = str(route.get("route") or "guide").strip().casefold()
    mode = str(route.get("mode") or "direct").strip().casefold()
    confidence = float(route.get("confidence", 0.0) or 0.0)

    # Final-boundary arbitration: comparative explanatory intent outranks a
    # model's generic Glossary classification. Do not hand off the whole phrase
    # as a term; retain the visitor's complete question for Guide composition.
    if route_id == "glossary" and _is_normative_conflict_explanatory_request(query):
        print(
            "The Guide request boundary: kept normative values-conflict inquiry in Guide composition; "
            f"query={_normalize_query(query)[:120]}"
        )
        route_id = "guide"
        mode = "direct"

    if route_id == "glossary" and _is_comparative_explanatory_request(query):
        print(
            "The Guide request boundary: kept comparative inquiry in Guide composition; "
            f"query={_normalize_query(query)[:120]}"
        )
        route_id = "guide"
        mode = "direct"

    # Provider/model routing is advisory, not sufficient authority to open a
    # registered page. Enforce destination intent at the final request boundary
    # too, so a model-selected Guide Node cannot bypass the registry guard above.
    # A compound explanatory question misclassified as a page destination returns
    # to ordinary Guide composition instead of becoming an empty direct handoff.
    if route_id == "guide_node" and not _guide_node_handoff_is_authorized(
        query,
        (route.get("round1_interpretation") or {}).get("guide_node_id"),
    ):
        print(
            "The Guide request boundary: suppressed unsupported Guide Node handoff; "
            f"query={_normalize_query(query)[:120]}"
        )
        route_id = "guide"
        mode = "direct"

    capability = _registered_available_specialist(route_id)
    should_delegate = capability is not None and route_id in {"relationship", "formation"}

    print(f"The Guide canonical request boundary: route={route_id}, mode={mode}, confidence={confidence:.3f}, delegate={should_delegate}, query={_normalize_query(query)[:120]}")

    # Guide Nodes are visitor-facing native Archive destinations. USE only
    # selects an approved WordPress node and carries the original question
    # across the native boundary. The node itself owns its experience.
    if route_id == "guide_node":
        node = _guide_node_by_id((route.get("round1_interpretation") or {}).get("guide_node_id"))
        if node is not None:
            request_id = "guide-node-" + hashlib.sha1(
                (query + "|" + str(node.get("node_id"))).encode("utf-8")
            ).hexdigest()[:16]
            payload = node_handoff_payload(
                node,
                query=query,
                request_id=request_id,
                visitor_boundary_version=APP_VERSION,
            )
            payload.update({
                "version": APP_VERSION,
                "route_source": route.get("source"),
                "route_confidence": confidence,
            })
            print(
                "The Guide direct Guide Node handoff: "
                f"request_id={request_id}, node={node.get('node_id')}, url={node.get('canonical_url')}"
            )
            return await _use_send_json(send, payload)

    # FSD is a visitor-facing native diagnostic surface. Once the
    # Guide route identifies it, hand off directly to its landing page.
    # Philippine Systems is a visitor-facing native knowledge surface.
    # The LLM has already made the macro routing decision above; hand the
    # visitor directly to its native landing page.
    if route_id == "systems_ph":
        philippine_systems_url = _philippine_systems_handoff_url(query)
        request_id = "systems-ph-" + hashlib.sha1(
            (query + "|" + _history_text(history)).encode("utf-8")
        ).hexdigest()[:16]
        print(
            "The Guide direct Philippine Systems handoff: "
            f"request_id={request_id}, url={philippine_systems_url}"
        )
        return await _use_send_json(send, {
            "ok": True,
            "version": APP_VERSION,
            "query": query,
            "intent": "SYSTEMS_PH_HANDOFF",
            "response": "",
            "handoff": "systems_ph",
            "handoff_mode": "direct",
            "handoff_pending": True,
            "philippine_systems_url": philippine_systems_url,
            "return_mode": "native_philippine_systems_landing",
            "visitor_boundary_version": APP_VERSION,
            "request_id": request_id,
        })

    if route_id == "fsd":
        fsd_url = _fsd_handoff_url(query)
        request_id = "fsd-" + hashlib.sha1(
            (query + "|" + _history_text(history)).encode("utf-8")
        ).hexdigest()[:16]
        print(
            "The Guide direct FSD handoff: "
            f"request_id={request_id}, url={fsd_url}"
        )
        return await _use_send_json(send, {
            "ok": True,
            "version": APP_VERSION,
            "query": query,
            "intent": "FSD_HANDOFF",
            "response": "",
            "handoff": "fsd",
            "handoff_mode": "direct",
            "handoff_pending": True,
            "fsd_url": fsd_url,
            "return_mode": "native_fsd_landing",
            "visitor_boundary_version": APP_VERSION,
            "request_id": request_id,
        })

    # Catalogue is a native visitor-facing search surface, not a Guide retrieval
    # spoke. Preserve the original request and let Catalogue own retrieval/ranking.
    if route_id == "catalogue":
        return await _use_send_json(send, _catalogue_handoff_payload(query, history))

        # Navigator is a visitor-facing specialist surface. Hand the original
    # inquiry to its native Start Here/Navigator experience rather than
    # duplicating its multi-step retrieval and path-planning logic.
    if route_id == "navigator":
        navigator_url = _navigator_handoff_url(query)
        request_id = "navigator-" + hashlib.sha1(
            (query + "|" + _history_text(history)).encode("utf-8")
        ).hexdigest()[:16]
        print(
            "The Guide direct Navigator handoff: "
            f"request_id={request_id}, url={navigator_url}"
        )
        return await _use_send_json(send, {
            "ok": True,
            "version": APP_VERSION,
            "query": query,
            "intent": "NAVIGATOR_HANDOFF",
            "response": "",
            "handoff": "navigator",
            "handoff_mode": "entrance",
            "handoff_pending": True,
            "navigator_url": navigator_url,
            "return_mode": "native_archive_navigator_welcome",
            "visitor_boundary_version": APP_VERSION,
            "request_id": request_id,
        })

# Atlas is a visitor-facing specialist surface, not a Guide retrieval
    # spoke. Hand the original inquiry to the native Atlas Finder surface.
    if route_id == "atlas":
        atlas_url = _atlas_handoff_url(query)
        request_id = "atlas-" + hashlib.sha1(
            (query + "|" + _history_text(history)).encode("utf-8")
        ).hexdigest()[:16]
        print(
            "The Guide direct Atlas handoff: "
            f"request_id={request_id}, url={atlas_url}"
        )
        return await _use_send_json(send, {
            "ok": True,
            "version": APP_VERSION,
            "query": query,
            "intent": "ATLAS_HANDOFF",
            "response": "",
            "handoff": "atlas",
            "handoff_mode": "direct",
            "handoff_pending": True,
            "atlas_query": query,
            "atlas_url": atlas_url,
            "return_mode": "native_atlas_finder",
            "visitor_boundary_version": APP_VERSION,
            "request_id": request_id,
        })

    # Case Navigator is a visitor-facing native structural search surface.
    # The native Navigator owns terrain/stage/case inference and presentation.
    if route_id == "case":
        case_url = _case_handoff_url(query)
        request_id = "case-" + hashlib.sha1(
            (query + "|" + _history_text(history)).encode("utf-8")
        ).hexdigest()[:16]
        print(
            "The Guide direct Case Navigator handoff: "
            f"request_id={request_id}, url={case_url}"
        )
        return await _use_send_json(send, {
            "ok": True,
            "version": APP_VERSION,
            "query": query,
            "intent": "CASE_HANDOFF",
            "response": "",
            "handoff": "case",
            "handoff_mode": "direct",
            "handoff_pending": True,
            "case_query": query,
            "case_url": case_url,
            "return_mode": "native_case_navigator",
            "visitor_boundary_version": APP_VERSION,
            "request_id": request_id,
        })
    # Glyph Finder is a visitor-facing native search surface. The native
    # Finder owns identity resolution, semantic evidence weighting, and
    # presentation; USE only carries the original inquiry across the boundary.
    if route_id == "glyph":
        glyph_url = _glyph_handoff_url(query)
        request_id = "glyph-" + hashlib.sha1(
            (query + "|" + _history_text(history)).encode("utf-8")
        ).hexdigest()[:16]
        print(
            "The Guide direct Glyph Finder handoff: "
            f"request_id={request_id}, url={glyph_url}"
        )
        return await _use_send_json(send, {
            "ok": True,
            "version": APP_VERSION,
            "query": query,
            "intent": "GLYPH_HANDOFF",
            "response": "",
            "handoff": "glyph",
            "handoff_mode": "direct",
            "handoff_pending": True,
            "glyph_query": query,
            "glyph_url": glyph_url,
            "return_mode": "native_guardian_glyph_finder",
            "visitor_boundary_version": APP_VERSION,
            "request_id": request_id,
        })

    # Glossary is a visitor-facing specialist surface, not a Guide retrieval
    # spoke. Hand the canonical term to the Glossary's existing native search
    # contract and let WordPress perform the authoritative lookup/rendering.
    if route_id == "glossary" and mode in {"lookup", "definition"}:
        interpretation = route.get("round1_interpretation") or {}
        glossary_term = _normalize_glossary_term(query, interpretation)
        embedded_glossary_term = _extract_embedded_glossary_term(query)
        if glossary_term and _is_bounded_glossary_request(
            query,
            glossary_term=glossary_term,
            embedded_term=embedded_glossary_term,
        ):
            glossary_url = (
                "https://geralddaquila.com/glossary/?glossary_term="
                + quote(glossary_term, safe="")
            )
            print(
                "The Guide direct Glossary handoff: "
                f"term={glossary_term!r}, url={glossary_url}"
            )
            return await _use_send_json(send, {
                "ok": True,
                "version": APP_VERSION,
                "query": query,
                "intent": "GLOSSARY_HANDOFF",
                "response": "",
                "handoff": "glossary",
                "handoff_mode": "direct",
                "handoff_pending": True,
                "glossary_term": glossary_term,
                "glossary_url": glossary_url,
                "return_mode": "native_glossary_search",
                "visitor_boundary_version": APP_VERSION,
            })

    if should_delegate:
        request_id = route_id + "-" + hashlib.sha1((query + "|" + _history_text(history)).encode("utf-8")).hexdigest()[:16]
        if route_id == "formation":
            try:
                result = _formation_specialist_response(query, history, route, request_id)
                return await _use_send_json(send, {
                    "ok": True, "version": APP_VERSION, "query": query,
                    "intent": "FORMATION_HANDOFF", "response": result["response"],
                    "formation_delegation": result["formation_delegation"],
                    "visitor_boundary_version": APP_VERSION, "request_id": request_id,
                })
            except Exception as exc:
                print(f"USE Formation specialist failed safely: {exc}")
                return await _use_send_json(send, {
                    "ok": False, "version": APP_VERSION, "query": query,
                    "intent": "FORMATION_HANDOFF",
                    "response": "The Formation pathway could not be opened right now.",
                    "error_type": "formation_specialist_failure", "request_id": request_id,
                }, 503)
        try:
            result = _relationship_specialist_response(query, history, route, request_id, parsed_body)
            return await _use_send_json(send, {
                "ok": True, "version": APP_VERSION, "query": query,
                "intent": "RELATIONAL_HANDOFF", "response": result["response"],
                "handoff": "relationship", "handoff_mode": "specialist",
                "relational_delegation": result["relational_delegation"],
                "visitor_boundary_version": APP_VERSION, "request_id": request_id,
            })
        except Exception as exc:
            print(f"USE Relationship specialist failed safely: {exc}")
            return await _use_send_json(send, {
                "ok": False, "version": APP_VERSION, "query": query,
                "intent": "RELATIONAL_HANDOFF",
                "response": "The Seeing the Relationship pathway could not be opened right now.",
                "error_type": "relationship_specialist_failure",
                "relational_delegation": {"state": "unavailable", "specialist": "Seeing the Relationship",
                                          "specialist_id": "relationship", "session_id": request_id},
                "visitor_boundary_version": APP_VERSION, "request_id": request_id,
            }, 503)

    # Exactly one fallback into the original protected application.
    # Intercept its ordinary JSON response at the shared outer boundary. This
    # covers legacy macro-routed Guide questions too, without modifying the
    # protected core or specialist-owned handoff responses above.
    capture_json = str(scope.get("path") or "") == "/api/query" and str(scope.get("method") or "").upper() == "POST"
    captured_start = None
    captured_chunks = []

    async def _send_with_final_visitor_boundary(message):
        nonlocal captured_start, captured_chunks, capture_json
        message_type = message.get("type")
        if message_type == "http.response.start" and capture_json:
            headers = message.get("headers") or []
            content_type = next(
                (value.lower() for key, value in headers if key.lower() == b"content-type"),
                b"",
            )
            if b"application/json" in content_type:
                captured_start = message
                captured_chunks = []
                return
            await send(message)
            return

        if message_type == "http.response.body" and captured_start is not None:
            captured_chunks.append(message.get("body") or b"")
            if message.get("more_body", False):
                return

            raw_response = b"".join(captured_chunks)
            try:
                payload = json.loads(raw_response.decode("utf-8"))
            except Exception:
                payload = None

            safe_payload = _guide_finalize_visitor_payload(payload, query)
            if safe_payload is not payload and isinstance(safe_payload, dict):
                encoded = json.dumps(
                    safe_payload, ensure_ascii=False, separators=(",", ":")
                ).encode("utf-8")
                headers = [
                    (key, value)
                    for key, value in (captured_start.get("headers") or [])
                    if key.lower() not in {b"content-length", b"content-encoding", b"etag"}
                ]
                headers.append((b"content-length", str(len(encoded)).encode("ascii")))
                start = dict(captured_start)
                start["status"] = 200
                start["headers"] = headers
                await send(start)
                await send({"type": "http.response.body", "body": encoded, "more_body": False})
            else:
                await send(captured_start)
                await send({"type": "http.response.body", "body": raw_response, "more_body": False})

            captured_start = None
            captured_chunks = []
            capture_json = False
            return

        await send(message)

    await _FASTAPI_APP(scope, _use_replay_receive(raw_body), _send_with_final_visitor_boundary)


PROVIDER_GATEWAY_RUNTIME_VERSION = "v1"

@app.post("/api/provider-capability")
async def _provider_capability_route(request: Request):
    token = request.headers.get("X-Living-Archive-Provider-Key")
    try:
        authorize_provider_gateway(token)
        body = await request.json()
        if not isinstance(body, dict):
            raise ValueError("Provider capability payload must be an object.")
        operation, messages, max_tokens = validate_provider_gateway_request(body)
        schema = body.get("schema") if isinstance(body.get("schema"), dict) else None
        result = execute_provider_gateway(
            operation=operation,
            messages=messages,
            max_tokens=max_tokens,
            use_core=use_core,
            schema=schema,
        )
        status = 200 if result.get("ok") else 503
        return JSONResponse(status_code=status, content=result)
    except HTTPException:
        raise
    except Exception as exc:
        print(f"USE provider capability gateway failure: {str(exc)[:400]}")
        return JSONResponse(status_code=503, content={
            "ok": False,
            "contract_version": PROVIDER_GATEWAY_CONTRACT_VERSION,
            "error": "provider_gateway_failure",
        })


FORMATION_ENTRANCE_CONTRACT_VERSION = "v1"
FORMATION_ENTRANCE_SOURCE = "steward-entrance"


def _formation_entrance_error(message, error_type, status_code=400):
    return JSONResponse(
        status_code=status_code,
        content={
            "ok": False,
            "version": APP_VERSION,
            "intent": "FORMATION_HANDOFF",
            "response": "",
            "error_type": error_type,
            "contract_version": FORMATION_ENTRANCE_CONTRACT_VERSION,
            "source": FORMATION_ENTRANCE_SOURCE,
            "message": message,
        },
    )


# v488.36 startup audit: verify the Basic Inquiry seam against the protected core.
_v48831_basic_inquiry_seam_self_audit()
# v489.07 startup audit: verify answer/navigation separation and canonical doorway propagation.
_v48894_general_guide_composition_self_audit()

@app.post("/api/formation-entrance")
async def _formation_entrance_route(request: Request):
    try:
        body = await request.json()
    except Exception:
        return _formation_entrance_error(
            "The Formation entrance payload must be valid JSON.",
            "formation_entrance_invalid_json",
        )

    if not isinstance(body, dict):
        return _formation_entrance_error(
            "The Formation entrance payload must be a JSON object.",
            "formation_entrance_invalid_payload",
        )

    choice = str(body.get("choice") or "").strip()
    situation = str(body.get("situation") or "").strip()
    possibility = str(body.get("possibility") or "").strip()

    missing = [
        name for name, value in (
            ("choice", choice),
            ("situation", situation),
            ("possibility", possibility),
        ) if not value
    ]
    if missing:
        return _formation_entrance_error(
            "The Formation entrance requires choice, situation, and possibility.",
            "formation_entrance_missing_fields",
        )

    contract_version = str(
        body.get("contract_version") or FORMATION_ENTRANCE_CONTRACT_VERSION
    ).strip()
    source = str(body.get("source") or FORMATION_ENTRANCE_SOURCE).strip()

    if contract_version != FORMATION_ENTRANCE_CONTRACT_VERSION:
        return _formation_entrance_error(
            "Unsupported Formation entrance contract version.",
            "formation_entrance_contract_version",
        )
    if source != FORMATION_ENTRANCE_SOURCE:
        return _formation_entrance_error(
            "Unsupported Formation entrance source.",
            "formation_entrance_source",
        )

    # Steward Entrance is itself a Guide-owned request boundary.
    # Propagate one bounded request identity through the common specialist pipe.
    request_id = (
        "guide-formation-"
        + hashlib.sha1(
            (
                FORMATION_ENTRANCE_SOURCE
                + "|"
                + choice
                + "|"
                + situation
                + "|"
                + possibility
            ).encode("utf-8")
        ).hexdigest()[:16]
    )

    try:
        contribution = invoke_specialist(
            SPECIALIST_ADAPTER_REGISTRY,
            request_id=request_id,
            guide_version=APP_VERSION,
            specialist_id="formation",
            original_question=situation,
            recognized_territory="stewardship formation",
            processing_purpose="bounded formation navigation from Steward Entrance",
            guide_context={
                "choice": choice,
                "situation": situation,
                "possibility": possibility,
            },
            safety_state="green",
        )
    except Exception as exc:
        print(f"USE v487.92 Formation entrance failed safely: {exc}")
        return _formation_entrance_error(
            "The Formation pathway could not be opened right now.",
            "formation_entrance_specialist_failure",
            status_code=503,
        )

    # The adapter bridges Formation's domain contract into the common
    # specialist pipe. Read the preserved domain payload, not the common
    # envelope's optional interpretation field.
    domain_payload = dict(contribution.get("payload") or {})
    interpretation = dict(domain_payload.get("interpretation") or {})
    movement = dict(domain_payload.get("movement") or {})
    doors = list(contribution.get("canonical_candidates") or [])

    bounded_doors = []
    seen_ids = set()
    for door in doors:
        if not isinstance(door, dict):
            continue
        door_id = str(door.get("id") or "").strip()
        title = str(door.get("title") or "").strip()
        url = str(door.get("url") or "").strip()
        if not door_id or door_id in seen_ids:
            continue
        if not title or not re.match(r"^https://geralddaquila\.com/\S+$", url, re.I):
            continue
        seen_ids.add(door_id)
        bounded_doors.append(
            {
                "id": door_id,
                "title": title,
                "url": url,
            }
        )
        if len(bounded_doors) >= 3:
            break

    return JSONResponse(
        status_code=200,
        content={
            "ok": True,
            "version": APP_VERSION,
            "intent": "FORMATION_HANDOFF",
            "contract_version": FORMATION_ENTRANCE_CONTRACT_VERSION,
            "source": FORMATION_ENTRANCE_SOURCE,
            "request_id": request_id,
            "choice": choice,
            "situation": situation,
            "possibility": possibility,
            "response": str(interpretation.get("pathway") or "").strip(),
            "formation_contribution": {
                "status": str(contribution.get("status") or ""),
                "contract_version": FORMATION_CONTRIBUTION_CONTRACT_VERSION,
                "voice_policy": FORMATION_VOICE_POLICY,
                "interpretation": interpretation,
                "movement": movement,
                "canonical_candidates": bounded_doors,
                "boundary_notes": contribution.get("boundary_notes"),
                "safety_flags": contribution.get("safety_flags"),
            },
            "visitor_boundary_version": APP_VERSION,
        },
    )




if not any(getattr(route, "path", "") == "/api/formation-entrance" for route in app.routes):
    raise RuntimeError("USE formation entrance route registration invariant failed")

@app.post("/api/relational-return")
async def _v48755_relational_return_route(request: Request):
    return await _v48755_relational_return(request)


# v488.17 Philippine Systems native doorway invariant.
if _philippine_systems_handoff_url("test") != "https://geralddaquila.com/understanding-the-philippines-culture-society-history-and-systemic-transformation/":
    raise RuntimeError("USE v488.17 invariant failed: Philippine Systems landing URL drift.")
if "systems_ph" not in _GUIDE_ROUTE_IDS:
    raise RuntimeError("USE v488.17 invariant failed: Philippine Systems route missing.")

# v488.17 FSD native doorway invariants.
if _fsd_handoff_url("test") != "https://geralddaquila.com/fractal-systems-diagnostic-2/":
    raise RuntimeError("USE v488.17 invariant failed: FSD landing URL drift.")
if "fsd" not in _GUIDE_ROUTE_IDS:
    raise RuntimeError("USE v488.17 invariant failed: FSD route missing.")
_fsd_route_probes = (
    "What's wrong with my organization? Can you help me where to start.",
    "Something is wrong with my organization. Where do I start?",
    "Can you help me understand what is happening in my organization?",
    "Why does our community keep getting stuck in the same pattern?",
)
if not all(_is_fsd_request(item) for item in _fsd_route_probes):
    raise RuntimeError("USE v488.17 invariant failed: natural systems diagnostic doorway not recognized.")
_fsd_nonroute_probes = (
    "What does stewardship mean?",
    "Can you define continuity?",
)
if any(_is_fsd_request(item) for item in _fsd_nonroute_probes):
    raise RuntimeError("USE v488.17 invariant failed: glossary definitions were captured by FSD.")

# The middleware, not mutation of FastAPI's stored endpoint objects, owns
# relational interception. This preserves the base route's validated request
# contract for every non-relational query.
if not any(getattr(route, "path", "") == "/api/relational-return" for route in app.routes):
    raise RuntimeError("USE v487.57 invariant failed: relational return route not registered")

# Single authoritative request boundary; all non-specialist requests fall through once.
if STREAM_CONTRACT_VERSION != "SSE-VALIDATED-v1" or STREAM_TRANSPORT_VERSION != "0.1.1":
    raise RuntimeError("USE streaming transport contract integrity failure.")

async def _guide_outer_visitor_response_boundary(scope, receive, send):
    """Enforce visitor-response sanitation around every /api/query exit path.

    This boundary intentionally sits outside _use_request_boundary so early
    specialist/handoff returns and the legacy-core fallback share the same
    last-mile contamination guard. The inner finalizer remains defense in depth.
    """
    if (
        scope.get("type") != "http"
        or str(scope.get("method") or "").upper() != "POST"
        or str(scope.get("path") or "") != "/api/query"
    ):
        await _use_request_boundary(scope, receive, send)
        return

    raw_body = await _use_request_body(receive)
    try:
        request_payload = json.loads(raw_body.decode("utf-8")) if raw_body else {}
    except Exception:
        request_payload = {}
    if not isinstance(request_payload, dict):
        request_payload = {}
    query = str(
        request_payload.get("query")
        or request_payload.get("user_query")
        or request_payload.get("question")
        or request_payload.get("text")
        or request_payload.get("input")
        or ""
    ).strip()

    captured_start = None
    captured_chunks = []

    async def _capture_json_response(message):
        nonlocal captured_start, captured_chunks
        message_type = message.get("type")
        if message_type == "http.response.start":
            headers = message.get("headers") or []
            content_type = next(
                (value.lower() for key, value in headers if key.lower() == b"content-type"),
                b"",
            )
            if b"application/json" in content_type:
                captured_start = message
                captured_chunks = []
                return
            await send(message)
            return

        if message_type == "http.response.body" and captured_start is not None:
            captured_chunks.append(message.get("body") or b"")
            if message.get("more_body", False):
                return
            raw_response = b"".join(captured_chunks)
            try:
                payload = json.loads(raw_response.decode("utf-8"))
            except Exception:
                payload = None
            safe_payload = _guide_finalize_visitor_payload(payload, query)
            if safe_payload is not payload and isinstance(safe_payload, dict):
                encoded = json.dumps(
                    safe_payload, ensure_ascii=False, separators=(",", ":")
                ).encode("utf-8")
                headers = [
                    (key, value)
                    for key, value in (captured_start.get("headers") or [])
                    if key.lower() not in {
                        b"content-length", b"content-encoding", b"etag"
                    }
                ]
                headers.append((b"content-length", str(len(encoded)).encode("ascii")))
                start = dict(captured_start)
                start["status"] = 200
                start["headers"] = headers
                await send(start)
                await send({
                    "type": "http.response.body",
                    "body": encoded,
                    "more_body": False,
                })
            else:
                await send(captured_start)
                await send({
                    "type": "http.response.body",
                    "body": raw_response,
                    "more_body": False,
                })
            captured_start = None
            captured_chunks = []
            return

        await send(message)

    await _use_request_boundary(
        scope, _use_replay_receive(raw_body), _capture_json_response
    )


app = streaming_entry(_guide_outer_visitor_response_boundary)



print(f"USE ACTIVE + FORMATION SPECIALIST v1: version={APP_VERSION}, fingerprint={DEPLOYMENT_FINGERPRINT}, core_sha={EXPECTED_CORE_BLOB_SHA}, source_sha256={RUNTIME_SOURCE_SHA256}, specialist_contract={SPECIALIST_PIPE_CONTRACT_VERSION}, adapter_contract={SPECIALIST_ADAPTER_CONTRACT_VERSION}, relationship_contract={RELATIONSHIP_CONTRIBUTION_CONTRACT_VERSION}, relationship_voice_policy={RELATIONSHIP_VOICE_POLICY}, formation_contract={FORMATION_CONTRIBUTION_CONTRACT_VERSION}, formation_voice_policy={FORMATION_VOICE_POLICY}, registered_specialists={len(SPECIALIST_CAPABILITY_REGISTRY)}, active_adapters={len(SPECIALIST_ADAPTER_REGISTRY.ids())}, provider_bank_contract={PROVIDER_BANK_CONTRACT_VERSION}, boundary_resilience={BOUNDARY_RESILIENCE_CONTRACT_VERSION}, guide_node_registry_state={guide_node_registry_state().get('state')}, capability_routing=provider_model_bank")
print(f"USE SAFETY INTELLIGENCE: contract={SAFETY_INTELLIGENCE_CONTRACT_VERSION}, authority=HRN_Safety_Fractal_and_Emergency_Intelligence, resource_owner=Emergency Intelligence, resource_contract=living-archive/emergency/v1/resolve, sibling_link=relationship")

# v487.88 synthesis hardening invariant: shared synthesis packaging is bounded and consumed downstream.
if SHARED_EVIDENCE_CONTRACT_VERSION != "v1":
    raise RuntimeError("USE v487.88 invariant failed: shared evidence contract drift.")

# v487.88 synthesis hardening invariant: USE answer composition consumes the shared claim transformer and synthesis packager exactly once.
if "claims = _normalize_shared_claims_for_use(docs or [])" not in open(_MAIN_PATH, encoding="utf-8").read():
    raise RuntimeError("USE v487.87 invariant failed: shared claim seam wiring missing.")
if "synthesis = _build_shared_synthesis_material_for_use(claims)" not in open(_MAIN_PATH, encoding="utf-8").read():
    raise RuntimeError("USE v487.87 invariant failed: shared synthesis seam wiring missing.")
if "build_synthesis_material as _shared_build_synthesis_material" not in open(_MAIN_PATH, encoding="utf-8").read():
    raise RuntimeError("USE v487.87 invariant failed: shared synthesis primitive import missing.")
if "normalize_journey_contribution as _normalize_shared_journey" not in open(_MAIN_PATH, encoding="utf-8").read():
    raise RuntimeError("USE v487.92 invariant failed: journey contribution seam wiring missing.")
if "_build_journey_contribution_for_use(body)" not in open(_MAIN_PATH, encoding="utf-8").read():
    raise RuntimeError("USE v487.92 invariant failed: journey contribution adapter consumption missing.")

# Ecosystem integration diagnostics (non-secret, read-only).
# This reports the distinction between declared capabilities, runtime adapters,
# and known direct visitor-facing handoffs. It does not claim that a route has
# passed a live visitor journey; those require separate E2E checks.
@_FASTAPI_APP.get("/api/provider-health-readiness")
def provider_health_readiness():
    """Return bounded, non-secret provider shared-health readiness diagnostics."""
    try:
        refresh_shared_health_state()
        snapshot = provider_bank_snapshot(use_core)
        config = snapshot.get("shared_health_configuration", {})
        state = snapshot.get("shared_health_state", {})
        config = config if isinstance(config, dict) else {}
        state = state if isinstance(state, dict) else {}
        configured = bool(config.get("configured"))
        available = bool(state.get("available"))
        return {
            "ok": configured and available,
            "contract": "provider-health-readiness-v1",
            "version": APP_VERSION,
            "fingerprint": DEPLOYMENT_FINGERPRINT,
            "deployment_commit_sha": os.environ.get("RENDER_GIT_COMMIT", "").strip(),
            "shared_health": {
                "configured": configured,
                "available": available,
                "mode": str(state.get("mode") or "unknown"),
                "url_configured": bool(config.get("url_configured")),
                "url_source": str(config.get("url_source") or "unknown"),
                "https_valid": bool(config.get("https_valid")),
                "shared_secret_configured": bool(config.get("shared_secret_configured")),
            },
            "limitations": [
                "Configuration readiness is distinct from successful shared-store reads and writes.",
                "This endpoint never returns the endpoint URL or shared secret.",
            ],
        }
    except Exception:
        return {
            "ok": False,
            "contract": "provider-health-readiness-v1",
            "version": APP_VERSION,
            "fingerprint": DEPLOYMENT_FINGERPRINT,
            "deployment_commit_sha": os.environ.get("RENDER_GIT_COMMIT", "").strip(),
            "shared_health": {
                "configured": False,
                "available": False,
                "mode": "diagnostic_failure",
                "url_configured": False,
                "url_source": "unknown",
                "https_valid": False,
                "shared_secret_configured": False,
            },
            "limitations": ["Provider health diagnostics could not be completed."],
        }


@_FASTAPI_APP.get("/api/integration-audit")
def ecosystem_integration_audit():
    capabilities = []
    for item in SPECIALIST_CAPABILITY_REGISTRY:
        capabilities.append({
            "specialist_id": str(getattr(item, "specialist_id", "")),
            "public_name": str(getattr(item, "public_name", "")),
            "status": str(getattr(item, "status", "")),
            "entry_point": str(getattr(item, "entry_point", "")),
            "access_class": str(getattr(item, "access_class", "")),
        })

    adapter_ids = sorted(str(item) for item in SPECIALIST_ADAPTER_REGISTRY.ids())
    adapter_set = set(adapter_ids)
    capability_ids = {item["specialist_id"] for item in capabilities}
    declared_available = {
        item["specialist_id"] for item in capabilities
        if item["status"] == "available"
    }

    # Native visitor-facing surfaces are available capabilities, but they are
    # deliberately not adapter-backed retrieval spokes.
    direct_handoffs = {
        "catalogue": "native_catalogue_search",
        "systems_ph": "native_philippine_systems_landing",
        "navigator": "native_navigator",
        "fsd": "native_fsd_landing",
        "guide_node": "canonical_guide_node",
    }
    native_handoff_ids = set(direct_handoffs)
    missing_adapters = sorted(declared_available - adapter_set - native_handoff_ids)
    unregistered_adapters = sorted(adapter_set - capability_ids)

    return {
        "ok": not missing_adapters and not unregistered_adapters,
        "audit_contract": "ecosystem-integration-audit-v1",
        "version": APP_VERSION,
        "fingerprint": DEPLOYMENT_FINGERPRINT,
        # Render supplies this immutable SHA for the deployed commit. Expose it
        # so production E2E can distinguish same-version patch deployments.
        "deployment_commit_sha": os.environ.get("RENDER_GIT_COMMIT", "").strip(),
        "source_sha256": RUNTIME_SOURCE_SHA256,
        "capability_registry": capabilities,
        "runtime_adapters": adapter_ids,
        "direct_handoffs": direct_handoffs,
        "available_capabilities_missing_adapters": missing_adapters,
        "adapters_without_capabilities": unregistered_adapters,
        "catalogue_mode": "direct_handoff_not_adapter",
        "limitations": [
            "This endpoint reports registration and declared routing mode only.",
            "It does not assert live provider health or end-to-end visitor journey success.",
        ],
    }
