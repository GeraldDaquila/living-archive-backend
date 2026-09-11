from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "main.py"
CORE = ROOT / "use_core.py"
source = MAIN.read_text(encoding="utf-8")
core = CORE.read_text(encoding="utf-8")

PRIMARY = "The Transformative Power of Loss: Finding Meaning in Grief Through Spiritual and Scientific Wisdom"
PRIMARY_URL = "https://geralddaquila.com/2025/05/12/the-transformative-power-of-loss-finding-meaning-in-grief-through-spiritual-and-scientific-wisdom/"
SECONDARY = "Journey Beyond: Exploring the Afterlife and Reincarnation Through Hypnosis and Near-Death Experiences"

assert 'APP_VERSION = "v339"' in source
assert PRIMARY in source
assert PRIMARY_URL in source
assert 'app = use_core.app' in source

module = ast.parse(source)
fn_nodes = {node.name: node for node in module.body if isinstance(node, ast.FunctionDef)}
assert "_v339_canonical_recommendation_doorway" in fn_nodes
assert "_v336_construct_visitor_answer" in fn_nodes

# The v339 final doorway must rebuild the canonical primary link, never merely
# preserve whatever the provider happened to return.
doorway = ast.get_source_segment(source, fn_nodes["_v339_canonical_recommendation_doorway"])
assert 'canonical_link = f"[{title}]({url})"' in doorway
assert 'prefix = "A useful place to begin is "' in doorway
assert 'return f"{prefix}{canonical_link}.' in doorway

# The visitor constructor must invoke that doorway after link normalization.
ctor = ast.get_source_segment(source, fn_nodes["_v336_construct_visitor_answer"])
assert ctor.count("_v339_canonical_recommendation_doorway(") == 1
assert ctor.find("normalize_link_presentation") < ctor.find("_v339_canonical_recommendation_doorway")

# The source must not retain the old response-path identity ambiguity: the
# provider-facing core seam must remain exported back to the wrapper.
assert "use_core._clean_generation_output = _v336_clean_generation_output" in source
assert "use_core._run_generation_attempt = _v336_run_generation_attempt" in source
assert "use_core._run_provider_completion_recovery = _v336_run_provider_completion_recovery" in source

# Recommendation task logic must be present in the protected core.
assert "_is_recommendation_question" in core
assert "_adjudicate_recommendation_resource" in core
assert "RECOMMENDATION_PRIMARY_EVIDENCE_MAX_CHARS" in core

# The observed benchmark secondary must remain known only as a secondary audit
# resource; it must not replace the canonical primary contract.
assert SECONDARY in source

print("USE v339 recommendation contract validation: PASS")
