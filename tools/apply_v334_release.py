from pathlib import Path
import hashlib
import re

path = Path("main.py")
source = path.read_text(encoding="utf-8")
expected_baseline = "ecbd5181958f95baedf397f715fa30ae0192005b9a39f005fe3c0ad8a8fb7ef2"
actual_baseline = hashlib.sha256(source.encode("utf-8")).hexdigest()
if actual_baseline != expected_baseline:
    raise SystemExit(f"Unexpected baseline SHA: {actual_baseline}")

replacements = [
    ("# USE PRODUCTION VERSION: v333 — Visitor-Centered Sensemaking Construction + The Guide", "# USE PRODUCTION VERSION: v334 — Compassionate Recommendation Boundary + The Guide"),
    ('APP_VERSION = "v333"', 'APP_VERSION = "v334"'),
    ('DEPLOYMENT_FINGERPRINT = "USE-v333-visitor-centered-sensemaking-construction"', 'DEPLOYMENT_FINGERPRINT = "USE-v334-compassionate-recommendation-boundary"'),
    ('CANONICAL_BUILD_ID = "USE-BUILD-v333-visitor-centered-sensemaking-construction"', 'CANONICAL_BUILD_ID = "USE-BUILD-v334-compassionate-recommendation-boundary"'),
    ('"Explain its direct fit and value from substantive Content in 2–4 concise sentences, using specific supported details rather than title inference."', '"Explain why it is directly relevant to the question from substantive Content in 2–4 concise sentences, using specific supported details rather than title inference. For grief, bereavement, death or loss questions, do not describe emotional, spiritual, therapeutic, or personal benefit to the visitor; describe what the resource explores and attribute any such framing to the resource."'),
    ('    """Static self-audit for the v333 visitor-centered construction layer."""', '    """Static self-audit for the established visitor-centered construction layer."""'),
    ("    if 'APP_VERSION = ' not in source or 'v333' not in source:\n        raise RuntimeError(\"v333 self-audit failure: version identity missing.\")", "    if 'APP_VERSION = ' not in source or 'DEPLOYMENT_FINGERPRINT = ' not in source:\n        raise RuntimeError(\"visitor-centered construction self-audit failure: version identity missing.\")"),
    ('        raise RuntimeError("v333 self-audit failure: construction instruction missing.")', '        raise RuntimeError("visitor-centered construction self-audit failure: construction instruction missing.")'),
    ('        raise RuntimeError("v333 self-audit failure: construction instruction not wired.")', '        raise RuntimeError("visitor-centered construction self-audit failure: construction instruction not wired.")'),
    ('        raise RuntimeError("v333 self-audit failure: compact generation path missing.")', '        raise RuntimeError("visitor-centered construction self-audit failure: compact generation path missing.")'),
]
for old, new in replacements:
    if old not in source:
        raise SystemExit(f"Required source pattern missing: {old[:100]}")
    source = source.replace(old, new, 1)

old_recommendation = (
    '        "is the adjudicated primary doorway. Name it and explain why it fits from "\n'
    '        "Content in 2–4 concise sentences. When supplied contextual evidence clearly "\n'
    '        "supports a distinct follow-on question or route, briefly mention 1–2 optional "\n'
    '        "companions and why each may matter; do not catalog resources or substitute "\n'
    '        "the primary."'
)
new_recommendation = (
    '        "is the adjudicated primary doorway. Name it and explain why it is relevant "\n'
    '        "to the visitor\'s question from substantive Content in 2–4 concise sentences. "\n'
    '        "Do not turn a source\'s claims about comfort, healing, hope, meaning, purpose, "\n'
    '        "peace, closure, or benefit into an asserted outcome for the visitor; attribute "\n'
    '        "such framing to the source when relevant. When supplied contextual evidence "\n'
    '        "clearly supports a distinct follow-on question or route, briefly mention 1–2 "\n'
    '        "optional companions and why each may matter; do not catalog resources or "\n'
    '        "substitute the primary."'
)
if old_recommendation not in source:
    raise SystemExit("Original recommendation contract not found")
source = source.replace(old_recommendation, new_recommendation, 1)

anchor = '        (r"\\b(?:find|discover|create)\\s+(?:meaning|purpose|closure|wisdom)\\s+(?:in|from)\\s+your\\s+(?:grief|loss|pain)\\b", "prescribed meaning-making"),\n'
insert = anchor + (
    '        (r"\\b(?:offering|offers|providing|provides|bringing|brings|giving|gives)\\s+(?:comfort|healing|peace|closure|meaning|purpose|hope)\\b", "asserted visitor benefit"),\n'
    '        (r"\\b(?:offer|offers|offering|provide|provides|providing|bring|brings|bringing|give|gives|giving)\\s+(?:comfort|healing|peace|closure|meaning|purpose|hope)\\s+(?:to|for)\\s+(?:the\\s+)?(?:visitor|reader|person|someone|those\\s+grieving)\\b", "asserted visitor benefit"),\n'
    '        (r"\\b(?:helps?|helping|supports?|supporting)\\s+(?:those|people|someone|a person|the reader|you)\\s+(?:who are|who is|with)?\\s*(?:grieving|grief|bereaved|bereavement|loss)\\b", "asserted visitor benefit"),\n'
    '        (r"\\b(?:comfort|healing|peace|closure|meaning|purpose|hope)\\s+(?:for|to)\\s+(?:those|people|someone|the reader|you)\\s+(?:who are|who is|with)?\\s*(?:grieving|grief|bereaved|bereavement|loss)\\b", "asserted visitor benefit"),\n'
)
if anchor not in source:
    raise SystemExit("Compassionate guard anchor not found")
source = source.replace(anchor, insert, 1)

needle = '''    assert _v308_compassionate_voice_violation(\n        "What essay would you recommend for someone grieving the death of a loved one?",\n        "The material offers comfort by suggesting continuity and connection beyond death.",\n    )\n'''
block = '''    assert _v308_compassionate_voice_violation(\n        "What essay would you recommend for someone grieving the death of a loved one?",\n        "The material offers comfort by suggesting continuity and connection beyond death.",\n    )\n    assert _v308_compassionate_voice_violation(\n        "What essay would you recommend for someone grieving the death of a loved one?",\n        "This piece is helpful for people grieving because it provides hope and peace.",\n    )\n    assert not _v308_compassionate_voice_violation(\n        "What essay would you recommend for someone grieving the death of a loved one?",\n        "The essay explores beliefs about continuity and connection beyond death. Its spiritual framing includes themes of hope and peace.",\n    )\n    for benefit in (\n        "The material provides comfort for those grieving the death of a loved one.",\n        "The material brings peace to someone grieving.",\n        "The material gives meaning to those grieving.",\n        "The material offers healing to the reader.",\n        "The material helps those grieving find closure.",\n    ):\n        assert _v308_compassionate_voice_violation(\n            "What essay would you recommend for someone grieving the death of a loved one?",\n            benefit,\n        )\n'''
if needle not in source:
    raise SystemExit("Compassionate self-audit insertion point not found")
source = source.replace(needle, block, 1)

identity_re = re.compile(r'(?ms)^# === CANONICAL BUILD IDENTITY \(excluded from payload hash\) ===\n.*?^# === END CANONICAL BUILD IDENTITY ===\n?')
placeholder = '# === CANONICAL BUILD IDENTITY (excluded from payload hash) ===\n# <CANONICAL_BUILD_IDENTITY_BLOCK>\n# === END CANONICAL BUILD IDENTITY ===\n'
canonical_source = identity_re.sub(placeholder, source, count=1)
canonical = hashlib.sha256(canonical_source.encode("utf-8")).hexdigest()
source = identity_re.sub(
    '# === CANONICAL BUILD IDENTITY (excluded from payload hash) ===\n'
    'CANONICAL_BUILD_ID = "USE-BUILD-v334-compassionate-recommendation-boundary"\n'
    f'CANONICAL_BUILD_PAYLOAD_SHA256 = "{canonical}"\n'
    '# === END CANONICAL BUILD IDENTITY ===\n',
    source,
    count=1,
)
raw = hashlib.sha256(source.encode("utf-8")).hexdigest()
if raw != "b7497393a1c67674f050939ca608bf44650ad64126055145a0f84181eca441b6":
    raise SystemExit(f"Unexpected v334 raw SHA after patch: {raw}")
path.write_text(source, encoding="utf-8")
print(f"v334 applied; raw_sha256={raw}; canonical_sha256={canonical}")
