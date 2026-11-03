"""Stateless FSD orchestration helpers."""
from __future__ import annotations
import re
from urllib.parse import urlsplit
from fsd_contract import validate_diagnostic_payload, SCALES
from fsd_question_bank import QUESTIONS

MAX_EVIDENCE = 6
MAX_EXCERPT = 1400

def build_quantum_query(answers, scale, quantum):
    indices = (0, 1, 5, 6) if quantum == "Q001_CORRESPONDENCE" else (2, 3, 4, 7, 8, 9)
    label = "Correspondence" if quantum == "Q001_CORRESPONDENCE" else "Correctability"
    responses = " ".join(QUESTIONS[i][0] + " " + QUESTIONS[i][1][answers[i]] for i in indices)
    return f"Living Archive systems diagnostic: {label}. Scope: {scale or 'not specified'}. {responses}"

def parse_evidence(context):
    if not isinstance(context, dict) or not str(context.get("context_blocks") or "").strip():
        return []
    if any(context.get(k) for k in ("evidence_sufficiency_unavailable", "question_evidence_unavailable", "question_evidence_fit_unavailable")):
        return []
    found, seen = [], set()
    for block in re.split(r"\n\s*---\s*\n", str(context["context_blocks"])):
        title = re.search(r"^Title:\s*(.+)$", block, re.M)
        url = re.search(r"^URL:\s*(https://\S+)$", block, re.M)
        body = re.search(r"^Content:\s*(.*)$", block, re.M | re.S)
        if not (title and url and body):
            continue
        link = url.group(1).rstrip(").,;")
        if urlsplit(link).netloc.casefold() != "geralddaquila.com" or link in seen:
            continue
        excerpt = re.sub(r"\s+", " ", body.group(1)).strip()[:MAX_EXCERPT]
        if not excerpt:
            continue
        seen.add(link)
        found.append({"evidence_id": f"E{len(found)+1:02d}", "title": title.group(1).strip()[:200], "url": link, "excerpt": excerpt})
        if len(found) == MAX_EVIDENCE:
            break
    return found

def prepare_fsd_analysis(payload, retrieve):
    """Validate answers and prepare independently retrieved canonical evidence.

    This is deliberately not a diagnostic report generator. Provider composition
    and visitor-facing report validation belong to a later, separately tested
    integration boundary.
    """
    validated = validate_diagnostic_payload(payload)
    evidence, seen = [], set()
    for quantum in ("Q001_CORRESPONDENCE", "Q002_CORRECTABILITY"):
        context = retrieve(build_quantum_query(payload["answers"], validated["scale"], quantum))
        for item in parse_evidence(context):
            if item["url"] not in seen and len(evidence) < MAX_EVIDENCE:
                seen.add(item["url"])
                item["evidence_id"] = f"E{len(evidence)+1:02d}"
                item["quantum_id"] = quantum
                evidence.append(item)
    if not evidence:
        raise RuntimeError("No sufficient canonical evidence was retrieved.")
    return {"validated": validated, "evidence": evidence}
