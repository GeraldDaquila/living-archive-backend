from pathlib import Path
import hashlib
import re

BASE_COMMIT = "aaffe880098bc9a711dca9cd17e1034b0bc5ac92"
TARGET_BRANCH = "use-v325"
BASE_FILE = "main.py"

# This builder is intentionally small and deterministic: it reads the exact
# v318 baseline from git, applies only the v325 generation-construction change,
# validates the canonical payload hash, then replaces main.py on the branch.

construction_helper = r'''def _v325_response_construction_instruction(user_query: str) -> str:
    """Add positive visitor-centered answer construction without changing authority."""
    q = re.sub(r"\s+", " ", str(user_query or "").strip().casefold())
    if not q:
        return ""

    parts: List[str] = [
        "[V325 RESPONSE CONSTRUCTION — DO NOT REVEAL]: Meet the visitor's question first, then use the strongest supplied canonical evidence as the doorway or lens.",
        "Clarify what the question is asking in the visitor's own terms, explain why the selected evidence fits from supplied Content, and stop at the smallest useful orientation rather than forcing closure.",
    ]

    is_recommendation = _is_recommendation_question(user_query)
    is_grief = bool(re.search(r"\\b(?:grief|grieving|bereavement|bereaved|loss|lost|death|died|dying|loved one)\\b", q))
    is_movement = _movement_question_requires_canonical_next(user_query)
    structure = recognize_question_structure(user_query)
    is_contrast = structure.get("structure") == "explicit_contrast"
    form_question = bool(re.search(r"\\b(?:what kind of|what type of|what form|essay|article|map|navigator|pathway|hub|index|collection|document|resource)\\b", q)) and bool(re.search(r"\\b(?:what|which|is|are)\\b", q))
    underdetermined = _question_is_underdetermined(user_query)

    if is_movement:
        parts.append(
            "For movement questions, give the requested location or continuation plainly and early. Use 'next' only when D29 explicitly validates a next canonical destination; otherwise state that no canonical next destination is established rather than inferring a route."
        )
    elif is_recommendation and is_grief:
        parts.append(
            "For a grief or loss recommendation, acknowledge the stated loss plainly and gently before describing the resource. Name the adjudicated primary early and explain its direct fit from Content; do not turn grief into a lesson, required transformation, meaning, closure, or prescribed outcome."
        )
    elif is_recommendation:
        parts.append(
            "For a recommendation request, name the adjudicated primary canonical resource early and explain its direct fit before any optional companion route permitted by the task contract."
        )
    elif is_grief:
        parts.append(
            "For grief, bereavement, death, or loss, begin gently with the visitor's stated experience, then describe what the supplied canonical material explores. Preserve agency and do not prescribe what the experience means or should become."
        )
    elif is_contrast:
        parts.append(
            "For an explicit contrast or tension, state the visitor's two sides or tension first. Then explain which supplied resources illuminate those sides and synthesize only the relationship the evidence supports; mark any remaining bridge as interpretation rather than fact."
        )
    elif form_question:
        parts.append(
            "For a document, resource-form, or structural question, answer the requested form or structural distinction first, then provide the most useful canonical doorway. Do not substitute a semantically related resource for the requested structure."
        )
    elif underdetermined:
        parts.append(
            "For an open experiential question, keep the question open rather than resolving it. Offer a bounded orientation and one strongest doorway, leaving room for the visitor to continue the inquiry themselves."
        )
    else:
        parts.append(
            "For ordinary topical questions, answer the central question first in ordinary language, then bring in the canonical resource as the evidence-grounded lens or doorway that helps the visitor continue."
        )

    parts.append(
        "Do not make the resource substitute for the answer, do not introduce a framework the visitor did not name, and do not add outside knowledge. Resource identity, links, and movement remain governed by the existing canonical gates."
    )
    return "\\n".join(parts)
'''

text = Path(BASE_FILE).read_text(encoding="utf-8")
text = text.replace("# USE PRODUCTION VERSION: v318 — Compassionate Guide Pathway + The Guide", "# USE PRODUCTION VERSION: v325 — Visitor-Centered Sensemaking Construction + v318 Baseline + The Guide", 1)
text = text.replace('APP_VERSION = "v318"', 'APP_VERSION = "v325"', 1)
text = text.replace('DEPLOYMENT_FINGERPRINT = "USE-v318-compassionate-guide-pathway"', 'DEPLOYMENT_FINGERPRINT = "USE-v325-visitor-centered-sensemaking-construction"', 1)
text = text.replace('CANONICAL_BUILD_ID = "USE-BUILD-v318-compassionate-guide-pathway"', 'CANONICAL_BUILD_ID = "USE-BUILD-v325-visitor-centered-sensemaking-construction"', 1)
text = text.replace("def _build_generation_messages(\n", construction_helper + "\n\ndef _build_generation_messages(\n", 1)
old = '''    response_task = _build_response_task_contract(user_query, intent)\n    response_task_instruction = _response_task_contract_instruction(response_task)\n\n    attribution_instruction = ""\n'''
new = '''    response_task = _build_response_task_contract(user_query, intent)\n    response_task_instruction = _response_task_contract_instruction(response_task)\n    response_construction_instruction = _v325_response_construction_instruction(user_query)\n\n    attribution_instruction = ""\n'''
text = text.replace(old, new, 1)
old = '''            + attribution_instruction\n            + response_task_instruction\n        )\n    else:\n        user_content = (\n            user_query\n            + "\\n\\nAnswer only from supplied evidence; preserve uncertainty. Exact titles; no links or markup."\n            + attribution_instruction\n            + response_task_instruction\n        )\n'''
new = '''            + attribution_instruction\n            + response_task_instruction\n            + "\\n\\n"\n            + response_construction_instruction\n        )\n    else:\n        user_content = (\n            user_query\n            + "\\n\\nAnswer only from supplied evidence; preserve uncertainty. Exact titles; no links or markup."\n            + attribution_instruction\n            + response_task_instruction\n            + "\\n\\n"\n            + response_construction_instruction\n        )\n'''
text = text.replace(old, new, 1)
old = '''[BREATHE BETWEEN IDEAS]: When several ideas are distinct, use 3–5 short paragraphs, usually 1–2 sentences each. No headings or bullets merely for formatting.\nOutput only <visitor_answer>, concise and finished. Use exact canonical titles; no links, markup, schema, or metadata.\n'''
new = '''[BREATHE BETWEEN IDEAS]: When several ideas are distinct, use 3–5 short paragraphs, usually 1–2 sentences each. No headings or bullets merely for formatting.\n[V325 CONSTRUCTION]: Meet the visitor's question first, then use the strongest supplied canonical evidence as the doorway or lens. For recommendations name the adjudicated primary early and explain its fit. For grief or loss begin gently and do not impose meaning. For explicit contrasts state the visitor's tension first and bound the synthesis. For form questions answer the form distinction first. For open experiential questions preserve the open question. For movement requests use “next” only when D29 explicitly validates a next destination. Do not add outside knowledge, new authority, or a framework the visitor did not name.\nOutput only <visitor_answer>, concise and finished. Use exact canonical titles; no links, markup, schema, or metadata.\n'''
text = text.replace(old, new, 1)
# Recompute canonical payload hash.
identity = re.compile(r'(?ms)^# === CANONICAL BUILD IDENTITY \\(excluded from payload hash\\) ===\\n.*?^# === END CANONICAL BUILD IDENTITY ===\\n?')
text = re.sub(r'(CANONICAL_BUILD_PAYLOAD_SHA256 = ")[0-9a-f]{64}(")', r'\1__PAYLOAD_SHA256__\2', text, count=1)
norm = text.replace("\r\n", "\n").replace("\r", "\n")
canonical, count = identity.subn("# === CANONICAL BUILD IDENTITY (excluded from payload hash) ===\n# <CANONICAL_BUILD_IDENTITY_BLOCK>\n# === END CANONICAL BUILD IDENTITY ===\n", norm, count=1)
if count != 1:
    raise SystemExit("canonical identity block mismatch")
payload = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
text = text.replace("__PAYLOAD_SHA256__", payload, 1)
Path(BASE_FILE).write_text(text, encoding="utf-8")
print(payload)
''