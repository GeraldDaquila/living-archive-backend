#!/usr/bin/env python3
"""Manually invoked, bounded live response evaluation for The Guide."""
from __future__ import annotations
import argparse, hashlib, json, re, subprocess, sys, time, uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from gold_star_semantic_contract import remove_question_echo as _remove_question_echo
from community_rule_decision_contract import evaluate_community_rule_response
from humility_spiritual_maturity_contract import evaluate_humility_spiritual_maturity_response

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs/qa/gold_standard_registry.json"
SUITE = ROOT / "docs/qa/guide_learning_evaluation_set.json"
CRITICAL_SUITE = ROOT / "docs/qa/guide_live_critical_evaluation_cases.json"
PRIMARY = "https://living-archive-backend.onrender.com"
ALLOWED = {PRIMARY, "https://living-archive-backend-mirror.onrender.com"}
# Run provider-sensitive critical transfer cases before the sampled Gold Standards.
# This preserves every acceptance criterion while reducing false failures from shared TPM exhaustion.
PROVIDER_PRIORITY_HELDOUT_IDS = (
    "heldout-community-rule-design-transfer-001",
    "heldout-transparency-trust-relational-synthesis-001",
    "heldout-humility-spiritual-maturity-nearmiss-001",
)
# Use a distinct but semantically equivalent question so the attribution probe
# cannot inherit a cached answer from the primary visitor smoke.
# This probe tests fresh provider attribution only; it does not certify Gold Star application.
PROVIDER_PROBE_QUERY = (
    "A policy helps employees but shifts costs to customers and nearby residents. "
    "How should leaders compare these benefits and burdens and decide who should bear the costs? "
    "Explicitly name employees, customers, and nearby residents, and explain who benefits and who bears the costs. "
    "Answer directly in one concise paragraph. Do not include URLs, links, or resource recommendations."
)

def build_provider_probe_query():
    """Return a semantically stable probe with a unique cache key per evaluation run."""
    return (
        PROVIDER_PROBE_QUERY
        + "\nDiagnostic uniqueness token: "
        + uuid.uuid4().hex
        + ". Do not mention this token in the answer."
    )


def file_commit(path):
    try:
        return subprocess.check_output(["git","log","-1","--format=%H","--",str(path.relative_to(ROOT))],cwd=ROOT,text=True,stderr=subprocess.DEVNULL).strip() or None
    except (OSError, subprocess.CalledProcessError):
        return None

def paragraphs(text):
    return [p.strip() for p in re.split(r"\n\s*\n", text.strip()) if p.strip()]

def post(base, question):
    req=Request(base.rstrip("/")+"/api/query",data=json.dumps({"query":question},ensure_ascii=False).encode(),headers={"Content-Type":"application/json","Accept":"application/json"},method="POST")
    try:
        with urlopen(req,timeout=35) as res:
            raw,status=res.read(),res.status
    except HTTPError as e:
        raw,status=e.read(),e.code
    except (URLError,TimeoutError,OSError) as e:
        return {"status":None,"error":f"{type(e).__name__}: {e}","body":None}
    try: body=json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError,json.JSONDecodeError): body=None
    return {"status":status,"error":None,"body":body,"raw_body":raw.decode("utf-8",errors="replace")[:12000] if body is None else None}

def get_json(url, timeout=90):
    request = Request(url, headers={"Accept": "application/json"}, method="GET")
    try:
        with urlopen(request, timeout=timeout) as response:
            raw, status = response.read(), response.status
    except HTTPError as exc:
        raw, status = exc.read(), exc.code
    except (URLError, TimeoutError, OSError) as exc:
        return {"status": None, "error": f"{type(exc).__name__}: {exc}", "body": None}
    try:
        body = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        body = None
    return {"status": status, "error": None, "body": body}


def verify_runtime_identity(base, expected_commit, timeout_seconds=300):
    """Wait for the exact evaluated source commit before issuing synthetic visitor requests."""
    if not expected_commit:
        raise RuntimeError("Cannot verify target identity without a checked-out Git commit.")
    deadline = time.monotonic() + max(0, int(timeout_seconds))
    last = None
    while True:
        last = get_json(base.rstrip("/") + "/api/integration-audit", timeout=90)
        body = last.get("body") if isinstance(last, dict) else None
        status = last.get("status") if isinstance(last, dict) else None
        if status == 200 and isinstance(body, dict):
            deployed_commit = str(body.get("deployment_commit_sha") or "").strip()
            if deployed_commit == expected_commit:
                return {
                    "deployment_commit_sha": deployed_commit,
                    "version": body.get("version"),
                    "fingerprint": body.get("fingerprint"),
                    "source_sha256": body.get("source_sha256"),
                    "audit_contract": body.get("audit_contract"),
                    "integration_audit_ok": body.get("ok") is True,
                    "integration_audit_warnings": {
                        "available_capabilities_missing_adapters": body.get("available_capabilities_missing_adapters") or [],
                        "adapters_without_capabilities": body.get("adapters_without_capabilities") or [],
                    },
                    "verified_at": datetime.now(timezone.utc).isoformat(),
                }
            last_error = f"target commit {deployed_commit or 'missing'} does not match expected {expected_commit}"
        elif status is None or (isinstance(status, int) and status >= 500):
            last_error = f"transient integration audit failure: status={status} error={last.get('error')}"
        else:
            raise RuntimeError(f"Integration audit rejected: status={status} error={last.get('error')}")
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise RuntimeError(f"Timed out waiting for primary runtime identity: {last_error}")
        time.sleep(min(10, remaining))


def check(name, ok, detail):
    return {"name":name,"passed":bool(ok),"detail":detail}


def select_gold_standard_sample(records, limit=6):
    """Select a stable, evenly spaced subset; full registry coverage stays in offline CI."""
    ordered = sorted(
        [item for item in records if isinstance(item, dict)],
        key=lambda item: str(item.get("benchmark_id") or item.get("query") or ""),
    )
    limit = max(0, int(limit))
    if limit == 0:
        return []
    if len(ordered) <= limit:
        return ordered
    if limit == 1:
        return [ordered[len(ordered) // 2]]
    indices = [round(index * (len(ordered) - 1) / (limit - 1)) for index in range(limit)]
    return [ordered[index] for index in indices]


def prioritize_heldout_cases(cases):
    """Return provider-sensitive critical cases first without dropping or duplicating any case."""
    priority_ids = set(PROVIDER_PRIORITY_HELDOUT_IDS)
    by_id = {
        str(case.get("case_id")): case
        for case in cases
        if isinstance(case, dict) and case.get("case_id")
    }
    priority = [by_id[case_id] for case_id in PROVIDER_PRIORITY_HELDOUT_IDS if case_id in by_id]
    remaining = [
        case for case in cases
        if not isinstance(case, dict) or str(case.get("case_id") or "") not in priority_ids
    ]
    return priority, remaining


def classify_llm_payload(body):
    """Require explicit final-answer LLM provenance; provider attempts alone do not count."""
    body = body if isinstance(body, dict) else {}
    provenance = body.get("response_provenance")
    provenance = provenance if isinstance(provenance, dict) else {}
    declared_class = str(provenance.get("class") or "").strip().casefold()
    provider = str(body.get("provider") or provenance.get("provider") or "").strip()
    model = str(body.get("model") or provenance.get("model") or "").strip()
    envelope = body.get("answer_envelope")
    envelope = envelope if isinstance(envelope, dict) else {}
    envelope_evidence = envelope.get("evidence")
    envelope_evidence = envelope_evidence if isinstance(envelope_evidence, dict) else {}
    envelope_route = envelope.get("route")
    envelope_route = envelope_route if isinstance(envelope_route, dict) else {}
    envelope_class = str(envelope_evidence.get("provenance_class") or "").strip().casefold()
    provider_present = envelope_route.get("provider_present") is True
    model_present = envelope_route.get("model_present") is True
    llm_invoked = provenance.get("llm_invoked") is True
    deterministic_markers = ("deterministic", "fallback", "recovery", "gold_standard_registry")
    is_deterministic = any(
        marker in (provider + " " + model + " " + declared_class + " " + envelope_class).casefold()
        for marker in deterministic_markers
    )
    explicit_llm = (
        declared_class in {"llm", "language_model", "model_generation"}
        and llm_invoked
        and bool(provider and model)
    )
    envelope_llm = (
        envelope_class in {"llm", "language_model", "model_generation"}
        and provider_present
        and model_present
    )
    verified = bool((explicit_llm or envelope_llm) and not is_deterministic)
    return verified, {
        "declared_class": declared_class or None,
        "envelope_class": envelope_class or None,
        "provider": provider or None,
        "model": model or None,
        "provider_present": provider_present,
        "model_present": model_present,
        "llm_invoked": llm_invoked,
        "verification_basis": (
            "explicit_response_provenance" if explicit_llm else
            "answer_envelope_provenance" if envelope_llm and verified else
            "insufficient_or_deterministic_final_output_provenance"
        ),
    }


def has_stakeholder_tradeoff_explanation(response):
    """Require the provider probe to address the stakeholder trade-off it actually asks about."""
    text = re.sub(r"\s+", " ", str(response or "")).casefold()
    names_affected_groups = (
        "employees" in text
        and "customers" in text
        and any(term in text for term in ("local residents", "nearby residents", "residents"))
    )
    explains_tradeoff = bool(re.search(r"\b(?:trade[- ]?offs?|benefits?|costs?|burdens?)\b", text))
    makes_reasoning_explicit = bool(re.search(r"\b(?:weigh|weighing|explicit|explain|accountab|consider)\w*\b", text))
    return names_affected_groups and explains_tradeoff and makes_reasoning_explicit


def provider_invocation_id(body):
    """Return the provider invocation ID attached to the final visitor response, if any."""
    provenance = body.get("response_provenance") if isinstance(body, dict) else None
    if not isinstance(provenance, dict):
        return None
    value = str(provenance.get("provider_invocation_id") or "").strip()
    return value or None


def visitor_request_correlation_id(body):
    """Return the request-local correlation ID, distinct from stable request_id."""
    if not isinstance(body, dict):
        return None
    value = str(body.get("request_correlation_id") or "").strip().casefold()
    return value if re.fullmatch(r"[0-9a-f]{32}", value) else None


def claim_adjudication_summary(body):
    value = body.get("claim_adjudication") if isinstance(body, dict) else None
    if not isinstance(value, dict):
        return None
    return {
        "status": value.get("status"),
        "reason": value.get("reason"),
        "claim_count": value.get("claim_count"),
        "outcome_counts": value.get("outcome_counts") if isinstance(value.get("outcome_counts"), dict) else None,
    }

def evaluate_gold(record, transport):
    body=transport.get("body") if isinstance(transport.get("body"),dict) else {}
    answer=body.get("response","")
    answer=answer if isinstance(answer,str) else ""
    out=[
      check("http_200",transport.get("status")==200,f"HTTP status {transport.get('status')}; {transport.get('error') or ''}"),
      check("api_ok",body.get("ok") is True,"API must return ok=true."),
      check("nonempty_answer",bool(answer.strip()),"Answer must be non-empty.")
    ]
    assertions=[str(x) for x in record.get("assertions",[])]
    text=" ".join(assertions)
    capabilities=record.get("gold_star_capabilities")
    capabilities=capabilities if isinstance(capabilities,dict) else {}
    if capabilities:
        # Explicit capability metadata is authoritative: an immutable exemplar
        # is not necessarily authorized for exact runtime delivery.
        exact=capabilities.get("exact_answer_authority") is True
    else:
        # Preserve legacy exact-answer behaviour only for records without
        # capability metadata, or with an explicit exact-delivery instruction.
        exact=(record.get("status")=="USER_APPROVED_GOLD_STANDARD" or "Do not change expected_response" in str(record.get("freeze_policy","")) or any("exact approved reference answer" in a.casefold() or "exactly matches the frozen" in a.casefold() for a in assertions))
    if exact: out.append(check("exact_answer",answer==str(record.get("expected_response","")),"Exact answer required by approval/freeze policy."))
    if re.search(r"exactly three (?:substantive )?paragraphs|answer has exactly three paragraphs",text,re.I):
        out.append(check("three_paragraph_shape",len(paragraphs(answer))==3,f"Observed {len(paragraphs(answer))} paragraphs."))
    rec=body.get("recommendation")
    no_doorway=bool(re.search(r"forbids direct page handoff|do not attach an unsolicited .*doorway|do not attach a resource doorway",text,re.I))
    if no_doorway: out.append(check("no_unrequested_doorway",rec in (None,{}),f"Observed recommendation: {rec!r}"))
    expected=record.get("expected_doorway") or {}
    if not no_doorway and (expected.get("title") or expected.get("url")):
        observed=rec if isinstance(rec,dict) else {}
        if expected.get("title") is not None:
            out.append(check("doorway_title",observed.get("title")==expected.get("title"),f"Expected {expected.get('title')!r}; observed {observed.get('title')!r}."))
        if expected.get("url") is not None:
            out.append(check("doorway_url",observed.get("url")==expected.get("url"),f"Expected {expected.get('url')!r}; observed {observed.get('url')!r}."))
    return out

def evaluate_held(case, transport, *, require_attributable_llm=True, expected_doorway=None):
    body=transport.get("body") if isinstance(transport.get("body"),dict) else {}
    answer=body.get("response","")
    answer=answer if isinstance(answer,str) else ""
    scoring_answer = _remove_question_echo(case.get("query", ""), answer)
    low = scoring_answer.casefold()
    rec=body.get("recommendation")
    out=[check("http_200",transport.get("status")==200,f"HTTP status {transport.get('status')}; {transport.get('error') or ''}"),check("api_ok",body.get("ok") is True,"API must return ok=true."),check("nonempty_answer",bool(answer.strip()),"Answer must be non-empty.")]
    cid=case.get("case_id","")
    if cid=="heldout-water-boiling-point-001":
        out += [check("general_fact_celsius",bool(re.search(r"\b100(?:\.0)?\s*°?\s*c\b",answer,re.I)),"Must state 100°C."),check("general_fact_fahrenheit",bool(re.search(r"\b212(?:\.0)?\s*°?\s*f\b",answer,re.I)),"Must state 212°F."),check("no_false_refusal",not any(x in low for x in ("i don't have enough","not enough verified","can't answer","cannot answer")),"Must not refuse a well-established fact."),check("no_irrelevant_doorway",rec in (None,{}),f"Observed recommendation: {rec!r}")]
    elif cid=="heldout-cosmology-life-001":
        definition=any(x in low for x in ("cosmology is","cosmology refers","cosmology concerns","understanding of reality","picture of reality","worldview","how the universe works","how life works"))
        significance=any(x in low for x in ("values","choices","relationships","how people live","how we live","decisions"))
        example=any(x in low for x in ("for example","for instance","when a person","in everyday life","such as")) or bool(re.search(r"\bif\s+(?:every|people|a person|someone|we|you)\b",low))
        wrong=any(x in low for x in ("separate the immediate event","conditions that made it more likely","incentives and constraints","what detail or context would make this question most concrete"))
        out += [check("defines_cosmology",definition,"Define cosmology before implications."),check("explains_lived_significance",significance,"Connect worldview to values, choices, relationships, or daily life."),check("concrete_implication",example,"Include a concrete example or implication."),check("no_wrong_specialist_routing",not wrong,"Do not use an unrelated recurring-problem diagnostic template.")]
    elif cid=="heldout-practical-trust-001":
        actions=sum(bool(re.search(p,low)) for p in (r"\bask\b.*\bpeople affected\b",r"\bexplain\b.*\breasons\b",r"\bfollow through\b",r"\bcheck with\b",r"\bseparate\b.*\bfacts\b",r"\bname who is responsible\b"))
        jargon=any(x in low for x in ("canonical evidence","provider bank","retrieval layer","synthesis layer"))
        doorway_title=str(rec.get("title") or "") if isinstance(rec,dict) else ""
        doorway_url=str(rec.get("url") or "") if isinstance(rec,dict) else ""
        doorway_label=(doorway_title+" "+doorway_url).casefold()
        relevant_doorway=bool(isinstance(rec,dict) and doorway_url.startswith("https://geralddaquila.com/") and re.search(r"trust|steward|organization|community",doorway_label))
        doorway_ok=bool(isinstance(rec,dict) and doorway_url.startswith("https://geralddaquila.com/") and doorway_title.strip() and str(rec.get("rationale") or "").strip())
        out += [
            check("concrete_actions",actions>=2,f"Found {actions} concrete action signals; need at least two."),
            check("plain_language",not jargon,"Avoid internal technical terms."),
            check("relevant_optional_doorway",relevant_doorway,f"Keep a relevant optional doorway separate from the practical answer; observed {rec!r}."),
            check("optional_doorway_is_canonical_and_visitor_facing",doorway_ok,f"Observed recommendation: {rec!r}"),
        ]
    elif cid=="heldout-strategic-governance-001":
        central=any(x in low for x in ("centraliz","centralis","consistent direction","coordination","oversight"))
        distributed=any(x in low for x in ("distribut","decentral","delegat","local decision","team-level"))
        tradeoffs=any(x in low for x in ("trade-off","tradeoff","risks","risk","costs","cost","benefits","benefit","advantages","advantage","disadvantages","disadvantage"))
        conditions=any(x in low for x in (
            "when decisions", "if the decision", "depends on", "as it grows",
            "decision type", "routine local decisions", "strategic decisions",
            "use centralization when", "use centralized authority when",
            "use distributed authority when", "use decentralization when",
        ))
        recommendation=any(x in low for x in ("hybrid","balance","retain","delegate","recommend","should"))
        out += [check("compares_both_models",central and distributed,"Address both centralized and distributed authority."),check("makes_tradeoffs_visible",tradeoffs,"Surface meaningful costs, benefits, or risks."),check("uses_conditional_reasoning",conditions,"Explain when each arrangement is appropriate."),check("offers_reasoned_direction",recommendation,"Give a conditional recommendation, not just a list.")]
    elif cid=="heldout-technical-verification-001":
        presence=any(x in low for x in ("os.getenv","os.environ.get","os.environ","environment variable","environmental variable"))
        boolean=any(x in low for x in ("is not none","bool(","is not empty","presence check","configured"))
        secret_safety=not any(x in low for x in ("print(os.getenv","print(os.environ","log(os.getenv","logger.info(os.getenv"))
        usage=any(x in low for x in ("runtime","application","read","consume","use the variable","actually uses","actually read"))
        out += [check("safe_presence_check",presence and boolean,"Describe a boolean/presence check, not disclosure of the value."),check("secret_not_printed",secret_safety,"Do not recommend printing or logging the secret."),check("configuration_vs_usage",usage,"Distinguish presence in configuration from application consumption.")]
    elif cid=="heldout-uncertain-causation-001":
        uncertainty=any(x in low for x in (
            "can't determine", "cannot determine", "cannot be established",
            "not enough information", "without analytics", "without data",
            "would need", "not possible to identify", "insufficient evidence",
        ))
        evidence=any(x in low for x in ("referral","source","utm","search console","analytics","landing page","campaign","bot","server log"))
        steps=any(x in low for x in ("compare","check","inspect","segment","review","investigate","break down"))
        no_fabrication=not any(x in low for x in ("the cause was definitely","this was caused by","the reason is certainly"))
        out += [check("calibrates_uncertainty",uncertainty,"State that the cause cannot be established from the information provided."),check("names_discriminating_evidence",evidence,"Identify evidence that could distinguish causes."),check("offers_investigation",steps,"Give a practical investigation step."),check("avoids_false_causation",no_fabrication,"Do not assert an unsupported cause.")]
    elif cid=="heldout-transparency-trust-relational-synthesis-001":
        attributable, provenance = classify_llm_payload(body)
        distinct_roles = (
            ("transparency" in low and any(term in low for term in ("visible", "visibility", "disclosure", "inspectable", "scrutiny")))
            and ("trust" in low and any(term in low for term in (
                "rely", "confidence", "dependable", "reliance", "justified trust",
                "earned rather than assumed", "trust feel earned",
            )))
        )
        mechanism = any(term in low for term in (
            "because", "enables", "allows", "allowing", "makes it possible",
            "basis for scrutiny",
        )) or (
            "letting people verify" in low and "catch and correct" in low
        ) or (
            "letting people see" in low and "open to scrutiny" in low
        ) or (
            "making decisions" in low and "open to scrutiny" in low
            and "support justified trust" in low
        )
        reciprocal = any(term in low for term in (
            "reinforce one another", "reinforce each other", "mutually reinforce",
            "mutually reinforcing", "strengthen one another", "strengthen each other",
            "work both ways", "works both ways", "other direction", "in two directions",
            "two directions", "in both directions", "conversely", "vice versa",
            "reciprocal", "in turn", "also makes",
        )) or "also make transparency more possible" in low
        boundary = any(term in low for term in (
            "neither guarantees", "does not guarantee", "not guarantee", "not the same",
            "not equivalent", "conditional, not automatic", "one does not substitute for the other",
        ))
        privacy_boundary = any(term in low for term in (
            "privacy", "confidential", "confidentiality", "sensitive information",
            "personal information", "private information",
        ))
        contextual_accountability = any(term in low for term in (
            "context", "mislead", "accountability", "accountable", "answerable",
        ))
        limits = privacy_boundary and contextual_accountability
        retrieval_only = (
            len(low.split()) < 65
            or low.startswith("the archive material available here offers")
            or low.startswith("a useful starting point")
        )
        out += [
            check("attributable_llm", attributable, f"Relational synthesis must be attributable to an invoked model; observed {provenance!r}."),
            check("distinct_concept_roles", distinct_roles, "Distinguish transparency as inspectability/disclosure from trust as justified reliance."),
            check("relationship_mechanism", mechanism, "Explain how transparency enables scrutiny and correction that can support justified trust."),
            check("reciprocal_but_not_identical", reciprocal and boundary, "Explain reciprocal reinforcement without equating the concepts or treating either as a guarantee."),
            check("legitimate_disclosure_limits", limits, "Explicitly preserve a privacy/confidentiality boundary as well as context or accountability; accountability alone is insufficient."),
            check("not_retrieval_fragment", not retrieval_only, "A source excerpt or short retrieval fragment is not an answer to a relational question."),
            check("no_unapproved_doorway", rec in (None, {}), f"This benchmark has no approved doorway; observed {rec!r}."),
        ]
    elif cid=="heldout-community-rule-design-transfer-001":
        if require_attributable_llm:
            attributable, provenance = classify_llm_payload(body)
            out.append(check(
                "attributable_llm",
                attributable,
                f"Community-rule transfer must be produced by an attributable LLM response, not deterministic fallback; observed {provenance!r}.",
            ))
        community_query = case.get("query") or "How should a community decide whether limits on personal liberty are justified by shared obligations and risks?"
        community_report = evaluate_community_rule_response(community_query, answer)
        community_checks = community_report.get("checks") or {}
        purpose = community_checks.get("legitimate_shared_purpose", False)
        proportionality = community_checks.get("necessity_and_least_restrictive_means", False)
        burden = community_checks.get("fair_burden_allocation", False)
        accommodation = community_checks.get("reasonable_accommodation", False)
        participation = community_checks.get("affected_party_participation", False)
        appeal = community_checks.get("appeal_and_review", False)
        majority_only = bool(community_report.get("majority_only"))
        doorway_title=str(rec.get("title") or "") if isinstance(rec,dict) else ""
        doorway_url=str(rec.get("url") or "") if isinstance(rec,dict) else ""
        expected_title=str((expected_doorway or {}).get("title") or "").strip()
        expected_url=str((expected_doorway or {}).get("url") or "").strip()
        doorway=bool(
            expected_title and expected_url and isinstance(rec,dict)
            and doorway_title.strip()==expected_title
            and doorway_url.strip()==expected_url
        )
        rationale=str(rec.get("rationale") or "") if isinstance(rec,dict) else ""
        clean_rationale=(
            bool(rationale.strip())
            and not any(x in rationale.casefold() for x in ("meta description","seo description","table of contents","chapter 1","preface"))
            and not bool(re.match(r"^\s*(?:foreword|introduction|abstract|contents|chapter\s+\d+)",rationale,re.I))
        )
        out += [
            check("legitimate_shared_purpose",purpose,"Name a legitimate shared purpose and demonstrable shared need."),
            check("necessity_and_least_restrictive_means",proportionality,"Test necessity, proportionality, and less restrictive workable means."),
            check("fair_burden_allocation",burden,"Make distribution of benefits, costs, and burdens visible."),
            check("reasonable_accommodation",accommodation,"Identify reasonable accommodation or adjustments for people whose needs differ."),
            check("affected_party_participation",participation,"Require meaningful participation in designing or shaping the rule; later appeal alone does not qualify."),
            check("appeal_and_review",appeal,"Provide appeal or challenge and observable review criteria."),
            check("no_majority_or_convenience_shortcut",not majority_only,"Do not treat majority preference or convenience as sufficient justification."),
            check("relevant_archive_doorway",doorway,"Provide a separate, optional, verified Archive doorway after the answer."),
            check("visitor_facing_doorway_rationale",clean_rationale,"Do not expose source-page prose or internal CMS metadata in the doorway rationale."),
        ]
    elif cid=="heldout-humility-spiritual-maturity-nearmiss-001":
        if require_attributable_llm:
            attributable, provenance = classify_llm_payload(body)
            out.append(check(
                "attributable_llm",
                attributable,
                f"Humility/spiritual-maturity near-miss must be answered by an attributable model response, not deterministic fallback; observed {provenance!r}.",
            ))
        humility_contract = evaluate_humility_spiritual_maturity_response(str(case.get("query") or ""), answer)
        humility_checks = humility_contract.get("checks") or {}
        expected_title = str((expected_doorway or {}).get("title") or "").strip()
        expected_url = str((expected_doorway or {}).get("url") or "").strip()
        doorway_title = str(rec.get("title") or "").strip() if isinstance(rec, dict) else ""
        doorway_url = str(rec.get("url") or "").strip() if isinstance(rec, dict) else ""
        doorway = bool(
            expected_title and expected_url and isinstance(rec, dict)
            and doorway_title == expected_title
            and doorway_url == expected_url
        )
        rationale = str(rec.get("rationale") or "") if isinstance(rec, dict) else ""
        clean_rationale = (
            bool(rationale.strip())
            and not any(term in rationale.casefold() for term in (
                "meta description", "seo description", "table of contents",
                "chapter 1", "preface", "post id", "wordpress",
            ))
            and not bool(re.match(
                r"^\s*(?:foreword|introduction|abstract|contents|chapter\s+\d+)",
                rationale,
                re.I,
            ))
        )
        no_inline_url = not bool(re.search(r"https?://|www\.", answer, re.I))
        no_orphaned_terminal_quote = not bool(re.search(r"(?<=[.!?])['’]\s*$", answer))
        out += [
            check("names_both_concepts", humility_checks.get("names_both_concepts", False), "Address humility and spiritual maturity as distinct but related concepts."),
            check("relationship_mechanism", humility_checks.get("relationship_mechanism", False), "Explain in one sentence how humility supports spiritual maturity."),
            check("relationship_direction_or_boundary", humility_checks.get("relationship_direction_or_boundary", False), "State that the relationship is conditional or not automatic."),
            check("humility_supports_learning_and_correction", humility_checks.get("humility_supports_learning_and_correction", False), "Explain how humility supports learning, honest self-appraisal, correction, and openness or accountability."),
            check("maturity_as_lived_conduct", humility_checks.get("maturity_as_lived_conduct", False), "Describe maturity as lived conduct rather than claimed status."),
            check("not_self_erasure_or_self_contempt", humility_checks.get("not_self_erasure_or_self_contempt", False), "Distinguish humility from self-erasure, diminished self-worth, or self-contempt."),
            check("preserves_appropriate_boundaries", humility_checks.get("preserves_appropriate_boundaries", False), "State that humility does not require surrendering appropriate boundaries."),
            check("not_passivity_or_automatic_compliance", humility_checks.get("not_passivity_or_automatic_compliance", False), "Distinguish humility from passivity, blind obedience, or automatic compliance."),
            check("does_not_guarantee_maturity", humility_checks.get("does_not_guarantee_maturity", False), "Do not claim humility alone guarantees spiritual maturity."),
            check("relevant_reviewed_archive_doorway", doorway, f"Provide the exact reviewed humility/spiritual-maturity doorway separately from the answer; observed {rec!r}."),
            check("visitor_facing_doorway_rationale", clean_rationale, "Keep the doorway rationale concise and visitor-facing, without source-page or CMS residue."),
            check("answer_contains_no_inline_resource_url", no_inline_url, "Keep the optional Archive destination in the separate doorway field, not embedded in the answer."),
            check("no_orphaned_terminal_quote", no_orphaned_terminal_quote, "Do not leave a stray quote delimiter after the final sentence."),
        ]
    elif cid=="heldout-explicit-no-handoff-001":
        distinction=any(x in low for x in ("policy sets","policy defines","policy establishes","procedure describes","procedure explains","steps for","what must be done","what should be done"))
        no_links=not bool(re.search(r"https?://|www\.",answer,re.I))
        no_followup=not any(x in low for x in ("would you like","if you want, i can","you may want to explore","next, you could","i recommend reading","a useful next question","the next question is","the next step is","a good next step","one useful next step"))
        out += [check("explains_policy_procedure",distinction,"Explain the governing rule versus the steps for carrying it out."),check("no_links_or_doorways",no_links and rec in (None,{}),"Honor the explicit no-resource/no-link instruction."),check("no_unrequested_followup",no_followup,"Do not append a follow-up offer or next step.")]
    else: out.append(check("known_heldout_case",False,f"No evaluator registered for {cid!r}."))
    return out

def build_human_review_template(rubric, applicable_critical=None):
    """Return an explicitly pending human scorecard; never auto-approve a response."""
    dimensions = rubric.get("dimensions", []) if isinstance(rubric, dict) else []
    dimension_ids = [
        item.get("id") for item in dimensions
        if isinstance(item, dict) and item.get("id")
    ]
    critical = (
        list(applicable_critical)
        if applicable_critical is not None
        else list(rubric.get("critical_dimensions", [])) if isinstance(rubric, dict) else []
    )
    # Case-specific critical dimensions must be scoreable fields too.
    score_dimension_ids = list(dict.fromkeys([*dimension_ids, *critical]))
    return {
        "status": "PENDING",
        "reviewer": None,
        "reviewed_at": None,
        "decision": "PENDING",
        "critical_dimensions": critical,
        "scores": {dimension_id: None for dimension_id in score_dimension_ids},
        "reviewer_notes": "",
        "instruction": "Complete every applicable dimension; use NA only with a reason. Automated checks cannot approve a lesson.",
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url",default=PRIMARY)
    parser.add_argument("--output",default="artifacts/guide-live-evaluation-report.json")
    parser.add_argument("--delay-seconds",type=float,default=.25)
    parser.add_argument("--max-gold-standards",type=int,default=6)
    parser.add_argument("--identity-wait-seconds",type=int,default=300)
    args=parser.parse_args()
    base=args.base_url.rstrip("/")
    if base not in ALLOWED: parser.error("base URL must be the primary or mirror Render service")
    if args.max_gold_standards < 1: parser.error("--max-gold-standards must be at least 1")
    rb,sb,cb=REGISTRY.read_bytes(),SUITE.read_bytes(),CRITICAL_SUITE.read_bytes()
    registry,suite,critical_suite=json.loads(rb),json.loads(sb),json.loads(cb)
    core_cases=suite.get("cases",[])
    critical_cases=critical_suite.get("cases",[])
    core_ids={str(x.get("case_id")) for x in core_cases if isinstance(x,dict)}
    critical_ids={str(x.get("case_id")) for x in critical_cases if isinstance(x,dict)}
    if not critical_cases or core_ids.intersection(critical_ids):
        raise RuntimeError("Critical live evaluation cases must be non-empty and disjoint from the calibration suite.")
    heldout_cases=[*core_cases,*critical_cases]
    registry_by_id={
        str(record.get("benchmark_id")): record
        for record in registry.get("records",[])
        if isinstance(record,dict) and record.get("benchmark_id")
    }
    eligible_records=[r for r in registry.get("records",[]) if r.get("subsystem")=="general-purpose-guide" and r.get("status") in {"USER_APPROVED_GOLD_STANDARD","FROZEN_REFERENCE_ONLY"} and r.get("query") and r.get("expected_response")]
    records=select_gold_standard_sample(eligible_records,args.max_gold_standards)
    expected_commit=subprocess.run(["git","rev-parse","HEAD"],cwd=ROOT,text=True,capture_output=True).stdout.strip() or None
    runtime_identity=verify_runtime_identity(base,expected_commit,args.identity_wait_seconds)
    priority_heldout_cases,remaining_heldout_cases=prioritize_heldout_cases(heldout_cases)
    workload=[("held_out",x) for x in priority_heldout_cases]+[("gold_standard",x) for x in records]+[("held_out",x) for x in remaining_heldout_cases]
    report={"report_schema_version":"1.2.0","evaluation_started_at":datetime.now(timezone.utc).isoformat(),"target_base_url":base,"registry_id":registry.get("registry_id"),"registry_status":registry.get("registry_status"),"registry_file_sha256":hashlib.sha256(rb).hexdigest(),"registry_file_commit":file_commit(REGISTRY),"evaluation_suite_id":suite.get("suite_id"),"evaluation_suite_version":suite.get("suite_version"),"human_review_rubric_dimensions":[d.get("id") for d in suite.get("human_review_rubric",{}).get("dimensions",[]) if isinstance(d,dict) and d.get("id")],"evaluation_suite_file_sha256":hashlib.sha256(sb).hexdigest(),"critical_evaluation_suite_id":critical_suite.get("suite_id"),"critical_evaluation_suite_version":critical_suite.get("suite_version"),"critical_evaluation_suite_file_sha256":hashlib.sha256(cb).hexdigest(),"git_commit":expected_commit,"runtime_identity":runtime_identity,"gold_standard_registry_count":len(eligible_records),"gold_standard_sample_policy":"stable_evenly_spaced_by_benchmark_id","gold_standard_count":len(records),"max_gold_standards":args.max_gold_standards,"heldout_count":len(heldout_cases),"calibration_heldout_count":len(core_cases),"critical_live_case_count":len(critical_cases),"results":[]}
    for index,(split,item) in enumerate(workload):
        if index and args.delay_seconds>0: time.sleep(args.delay_seconds)
        question=item["query"]
        request_started_at=datetime.now(timezone.utc).isoformat()
        transport=post(base,question)
        request_completed_at=datetime.now(timezone.utc).isoformat()
        body=transport.get("body")
        body=body if isinstance(body,dict) else None
        expected_doorway=None
        if split=="gold_standard":
            checks=evaluate_gold(item,transport)
        else:
            source_ids=item.get("source_benchmark_ids",[])
            source_record=next(
                (registry_by_id.get(str(source_id)) for source_id in source_ids if registry_by_id.get(str(source_id))),
                None,
            )
            expected_doorway = item.get("expected_doorway")
            if not isinstance(expected_doorway, dict):
                expected_doorway = source_record.get("expected_doorway") if isinstance(source_record,dict) else None
            checks=evaluate_held(item,transport,expected_doorway=expected_doorway)
            if str(item.get("case_id") or "") in PROVIDER_PRIORITY_HELDOUT_IDS:
                checks.append(check(
                    "provider_invocation_id",
                    bool(provider_invocation_id(body)),
                    "Critical held-out visitor response must include its final provider invocation ID; a provider label alone is insufficient.",
                ))
        request_correlation = visitor_request_correlation_id(body)
        checks.append(check(
            "request_correlation_id",
            bool(request_correlation),
            "Visitor response must expose the 32-hex request-local ID used by final-delivery telemetry.",
        ))
        report["results"].append({"evaluation_sequence":index+1,"request_started_at":request_started_at,"request_completed_at":request_completed_at,"benchmark_id":item.get("benchmark_id") if split=="gold_standard" else item.get("case_id"),"split":split,"status":item.get("status") if split=="gold_standard" else None,"query":question,"checks":checks,"passed":all(x["passed"] for x in checks),"transport_status":transport.get("status"),"transport_error":transport.get("error"),"response":body.get("response") if body else None,"expected_doorway":expected_doorway,"recommendation":body.get("recommendation") if body else None,"canonical_doorway":body.get("canonical_doorway") if body else None,"doorway_decision":body.get("doorway_decision") if body else None,"doorway_omission_reason":body.get("doorway_omission_reason") if body else None,"deployment_commit_sha":body.get("deployment_commit_sha") if body else None,"answer_basis":body.get("answer_basis") if body else None,"intent":body.get("intent") if body else None,"processing":body.get("processing") if body else None,"request_id":body.get("request_id") if body else None,"request_correlation_id":request_correlation,"response_provenance":body.get("response_provenance") if body else None,"answer_envelope":body.get("answer_envelope") if body else None,"provider":body.get("provider") if body else None,"model":body.get("model") if body else None,"claim_adjudication":claim_adjudication_summary(body),"raw_body":transport.get("raw_body"),"human_review":build_human_review_template(suite.get("human_review_rubric",{}),item.get("critical_dimensions") if split=="held_out" else None)})
    # Run the bounded attribution probe only after all workload cases. The probe is
    # diagnostic, not a prerequisite for the critical held-out cases; running it
    # first can exhaust shared provider health/cooldown capacity and starve them.
    provider_probe_query_value=build_provider_probe_query()
    provider_probe_started_at=datetime.now(timezone.utc).isoformat()
    provider_probe_transport=post(base,provider_probe_query_value)
    provider_probe_completed_at=datetime.now(timezone.utc).isoformat()
    provider_probe_body=provider_probe_transport.get("body")
    provider_probe_body=provider_probe_body if isinstance(provider_probe_body,dict) else {}
    provider_probe_llm,provider_probe_provenance=classify_llm_payload(provider_probe_body)
    provider_probe_invocation_id=provider_invocation_id(provider_probe_body)
    provider_probe_correlation_id=visitor_request_correlation_id(provider_probe_body)
    provider_probe_checks=[
        check("http_200",provider_probe_transport.get("status")==200,f"HTTP status {provider_probe_transport.get('status')}; {provider_probe_transport.get('error') or ''}"),
        check("api_ok",provider_probe_body.get("ok") is True,"API must return ok=true."),
        check("nonempty_answer",bool(str(provider_probe_body.get("response") or "").strip()),"Provider probe must return a non-empty answer."),
        check("stakeholder_tradeoff_explanation",has_stakeholder_tradeoff_explanation(provider_probe_body.get("response")),"The probe must name employees, customers, and local residents and explain the benefit/cost trade-off."),
        check("attributable_llm",provider_probe_llm,"Final visitor response must carry explicit LLM provenance; provider attempts alone do not count."),
        check("provider_invocation_id",bool(provider_probe_invocation_id),"The final visitor response must include a provider invocation ID; a provider label alone is insufficient."),
        check("request_correlation_id",bool(provider_probe_correlation_id),"The provider probe must expose the request-local ID used by final-delivery telemetry."),
    ]
    report["provider_probe"]={"purpose":"provider_attribution_only_not_gold_star_effectiveness","query":provider_probe_query_value,"request_started_at":provider_probe_started_at,"request_completed_at":provider_probe_completed_at,"transport_status":provider_probe_transport.get("status"),"transport_error":provider_probe_transport.get("error"),"request_id":provider_probe_body.get("request_id"),"request_correlation_id":provider_probe_correlation_id,"provider_invocation_id":provider_probe_invocation_id,"response_provenance":provider_probe_body.get("response_provenance"),"answer_envelope":provider_probe_body.get("answer_envelope"),"provider_provenance":provider_probe_provenance,"attributable_llm":provider_probe_llm,"provider_probe_checks":provider_probe_checks,"response":provider_probe_body.get("response"),"human_review":build_human_review_template(suite.get("human_review_rubric",{})) if provider_probe_llm else None}

    gold=[x for x in report["results"] if x["split"]=="gold_standard"]; held=[x for x in report["results"] if x["split"]=="held_out"]
    report["summary"]={"gold_standards_passed":sum(x["passed"] for x in gold),"gold_standards_total":len(gold),"gold_standard_registry_total":len(eligible_records),"heldout_passed":sum(x["passed"] for x in held),"heldout_total":len(held),"failed_gold_standard_ids":[x["benchmark_id"] for x in gold if not x["passed"]],"failed_heldout_ids":[x["benchmark_id"] for x in held if not x["passed"]],"provider_probe_attributable_llm":provider_probe_llm,"provider_probe_provider":provider_probe_provenance.get("provider"),"provider_probe_model":provider_probe_provenance.get("model"),"provider_probe_passed":all(x["passed"] for x in provider_probe_checks),"provider_probe_has_invocation_id":bool(provider_probe_invocation_id),"provider_probe_has_request_correlation_id":bool(provider_probe_correlation_id),"all_visitor_results_have_request_correlation_ids":all(bool(x.get("request_correlation_id")) for x in report["results"]),"overall_pass":all(x["passed"] for x in report["results"]),"interpretation":"Live run is a bounded sample of registered Gold Standards plus the complete held-out set. The critical held-out cases independently require attributable model provenance and a final provider invocation ID. The separate provider probe is diagnostic only and runs after the workload so it cannot consume capacity needed by critical cases. Heuristic checks require human review; no lesson is promoted automatically."}
    report["evaluation_finished_at"]=datetime.now(timezone.utc).isoformat()
    out=Path(args.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report["summary"],ensure_ascii=False,indent=2)); print(f"Full report: {out}")
    return 0 if report["summary"]["overall_pass"] else 1

if __name__=="__main__": sys.exit(main())
