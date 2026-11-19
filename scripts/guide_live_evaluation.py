#!/usr/bin/env python3
"""Manually invoked, bounded live response evaluation for The Guide."""
from __future__ import annotations
import argparse, hashlib, json, re, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from gold_star_semantic_contract import remove_question_echo as _remove_question_echo

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "docs/qa/gold_standard_registry.json"
SUITE = ROOT / "docs/qa/guide_learning_evaluation_set.json"
PRIMARY = "https://living-archive-backend.onrender.com"
ALLOWED = {PRIMARY, "https://living-archive-backend-mirror.onrender.com"}

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

def check(name, ok, detail):
    return {"name":name,"passed":bool(ok),"detail":detail}

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

def evaluate_held(case, transport):
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
        out += [check("concrete_actions",actions>=2,f"Found {actions} concrete action signals; need at least two."),check("plain_language",not jargon,"Avoid internal technical terms."),check("no_unrequested_doorway",rec in (None,{}),f"Observed recommendation: {rec!r}")]
    elif cid=="heldout-strategic-governance-001":
        central=any(x in low for x in ("centraliz","centralis","consistent direction","coordination","oversight"))
        distributed=any(x in low for x in ("distribut","decentral","delegat","local decision","team-level"))
        tradeoffs=any(x in low for x in ("trade-off","tradeoff","risks","risk","costs","cost","benefits","benefit","advantages","advantage","disadvantages","disadvantage"))
        conditions=any(x in low for x in ("when decisions","if the decision","depends on","as it grows","decision type","routine local decisions","strategic decisions"))
        recommendation=any(x in low for x in ("hybrid","balance","retain","delegate","recommend","should"))
        out += [check("compares_both_models",central and distributed,"Address both centralized and distributed authority."),check("makes_tradeoffs_visible",tradeoffs,"Surface meaningful costs, benefits, or risks."),check("uses_conditional_reasoning",conditions,"Explain when each arrangement is appropriate."),check("offers_reasoned_direction",recommendation,"Give a conditional recommendation, not just a list.")]
    elif cid=="heldout-technical-verification-001":
        presence=any(x in low for x in ("os.getenv","os.environ.get","os.environ","environment variable","environmental variable"))
        boolean=any(x in low for x in ("is not none","bool(","is not empty","presence check","configured"))
        secret_safety=not any(x in low for x in ("print(os.getenv","print(os.environ","log(os.getenv","logger.info(os.getenv"))
        usage=any(x in low for x in ("runtime","application","read","consume","use the variable","actually uses","actually read"))
        out += [check("safe_presence_check",presence and boolean,"Describe a boolean/presence check, not disclosure of the value."),check("secret_not_printed",secret_safety,"Do not recommend printing or logging the secret."),check("configuration_vs_usage",usage,"Distinguish presence in configuration from application consumption.")]
    elif cid=="heldout-uncertain-causation-001":
        uncertainty=any(x in low for x in ("can't determine","cannot determine","not enough information","without analytics","without data","would need","not possible to identify","insufficient evidence"))
        evidence=any(x in low for x in ("referral","source","utm","search console","analytics","landing page","campaign","bot","server log"))
        steps=any(x in low for x in ("compare","check","inspect","segment","review","investigate","break down"))
        no_fabrication=not any(x in low for x in ("the cause was definitely","this was caused by","the reason is certainly"))
        out += [check("calibrates_uncertainty",uncertainty,"State that the cause cannot be established from the information provided."),check("names_discriminating_evidence",evidence,"Identify evidence that could distinguish causes."),check("offers_investigation",steps,"Give a practical investigation step."),check("avoids_false_causation",no_fabrication,"Do not assert an unsupported cause.")]
    elif cid=="heldout-explicit-no-handoff-001":
        distinction=any(x in low for x in ("policy sets","policy defines","policy establishes","procedure describes","procedure explains","steps for","what must be done","what should be done"))
        no_links=not bool(re.search(r"https?://|www\.",answer,re.I))
        no_followup=not any(x in low for x in ("would you like","if you want, i can","you may want to explore","next, you could","i recommend reading"))
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
    args=parser.parse_args()
    base=args.base_url.rstrip("/")
    if base not in ALLOWED: parser.error("base URL must be the primary or mirror Render service")
    rb,sb=REGISTRY.read_bytes(),SUITE.read_bytes()
    registry,suite=json.loads(rb),json.loads(sb)
    records=[r for r in registry.get("records",[]) if r.get("subsystem")=="general-purpose-guide" and r.get("status") in {"USER_APPROVED_GOLD_STANDARD","FROZEN_REFERENCE_ONLY"} and r.get("query") and r.get("expected_response")]
    workload=[("gold_standard",x) for x in records]+[("held_out",x) for x in suite.get("cases",[])]
    report={"report_schema_version":"1.0.0","evaluation_started_at":datetime.now(timezone.utc).isoformat(),"target_base_url":base,"registry_id":registry.get("registry_id"),"registry_status":registry.get("registry_status"),"registry_file_sha256":hashlib.sha256(rb).hexdigest(),"registry_file_commit":file_commit(REGISTRY),"evaluation_suite_id":suite.get("suite_id"),"evaluation_suite_version":suite.get("suite_version"),"human_review_rubric_dimensions":[d.get("id") for d in suite.get("human_review_rubric",{}).get("dimensions",[]) if isinstance(d,dict) and d.get("id")],"evaluation_suite_file_sha256":hashlib.sha256(sb).hexdigest(),"git_commit":subprocess.run(["git","rev-parse","HEAD"],cwd=ROOT,text=True,capture_output=True).stdout.strip() or None,"runtime_identity":None,"gold_standard_count":len(records),"heldout_count":len(suite.get("cases",[])),"results":[]}
    for index,(split,item) in enumerate(workload):
        if index and args.delay_seconds>0: time.sleep(args.delay_seconds)
        question=item["query"]; transport=post(base,question); body=transport.get("body")
        body=body if isinstance(body,dict) else None
        checks=evaluate_gold(item,transport) if split=="gold_standard" else evaluate_held(item,transport)
        if body and report["runtime_identity"] is None: report["runtime_identity"]={"version":body.get("version"),"fingerprint":body.get("fingerprint"),"source_sha256":body.get("source_sha256")}
        report["results"].append({"benchmark_id":item.get("benchmark_id") if split=="gold_standard" else item.get("case_id"),"split":split,"status":item.get("status") if split=="gold_standard" else None,"query":question,"checks":checks,"passed":all(x["passed"] for x in checks),"transport_status":transport.get("status"),"transport_error":transport.get("error"),"response":body.get("response") if body else None,"recommendation":body.get("recommendation") if body else None,"answer_basis":body.get("answer_basis") if body else None,"intent":body.get("intent") if body else None,"processing":body.get("processing") if body else None,"request_id":body.get("request_id") if body else None,"raw_body":transport.get("raw_body"),"human_review":build_human_review_template(suite.get("human_review_rubric",{}),item.get("critical_dimensions") if split=="held_out" else None)})
    gold=[x for x in report["results"] if x["split"]=="gold_standard"]; held=[x for x in report["results"] if x["split"]=="held_out"]
    report["summary"]={"gold_standards_passed":sum(x["passed"] for x in gold),"gold_standards_total":len(gold),"heldout_passed":sum(x["passed"] for x in held),"heldout_total":len(held),"failed_gold_standard_ids":[x["benchmark_id"] for x in gold if not x["passed"]],"failed_heldout_ids":[x["benchmark_id"] for x in held if not x["passed"]],"overall_pass":all(x["passed"] for x in report["results"]),"interpretation":"Held-out checks are bounded heuristics requiring human review; no lesson is promoted automatically."}
    report["evaluation_finished_at"]=datetime.now(timezone.utc).isoformat()
    out=Path(args.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report["summary"],ensure_ascii=False,indent=2)); print(f"Full report: {out}")
    return 0 if report["summary"]["overall_pass"] else 1

if __name__=="__main__": sys.exit(main())
