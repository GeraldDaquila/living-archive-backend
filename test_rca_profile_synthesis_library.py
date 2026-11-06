"""Deterministic QA for the RCA synthesis routing library v1.1."""
import itertools, json
from pathlib import Path

LIB = json.loads(Path(__file__).with_name("rca_profile_synthesis_library_v1.json").read_text())
DIMS = ("Resonance","Coherence","Correspondence","Correctability")
BANDS = (1.4,2.2,3.0,3.8,4.6)

def select(scores):
    avg=sum(scores)/4; spread=max(scores)-min(scores)
    shape="HighBalanced" if spread<.6 and avg>=4.2 else "LowBalanced" if spread<.6 and avg<2.6 else "Balanced" if spread<.6 else "Uneven"
    rel=[("R_P",scores[0]-scores[2]),("C_P",scores[1]-scores[2]),("P_K",scores[2]-scores[3]),("K_C",scores[3]-scores[1]),("R_C",scores[0]-scores[1]),("P_R",scores[2]-scores[0])]
    rel=sorted((x for x in rel if x[1]>=.8),key=lambda x:x[1],reverse=True)
    return rel[0][0] if rel else shape

def test_625_band_vectors_route_to_existing_narrative():
    routed={select(v) for v in itertools.product(BANDS, repeat=4)}
    available=set(LIB["profile_shapes"]) | set(LIB["relational_patterns"])
    assert routed <= available
    assert len(list(itertools.product(BANDS,repeat=4))) == 625

def test_individual_and_collective_are_distinct_for_every_pattern():
    for key, item in LIB["relational_patterns"].items():
        assert item["individual"] != item["collective"]
        assert item["so_what_individual"] != item["so_what_collective"]
        assert item["doorway_individual"] != item["doorway_collective"]

def test_all_dimensions_have_plain_language_and_both_doorways():
    for d in DIMS:
        assert LIB["dimensions"][d]["plain_question"]
        assert LIB["capacity_doorways"][d]["individual"]
        assert LIB["capacity_doorways"][d]["collective"]

def test_synthesis_contract_forbids_generic_fixed_output():
    contract=LIB["composition_contract"]
    assert contract["paragraphs"] == 3
    assert "generic paragraph repeated regardless of score vector" in contract["anti_genericity"]

def test_perspective_narratives_name_distinct_exploration_domains():
    assert "authority" in LIB["relational_patterns"]["P_K"]["collective"]
    assert "first interpretation" in LIB["relational_patterns"]["R_P"]["individual"]
    assert "whose experience" in LIB["relational_patterns"]["P_R"]["collective"]


def test_boundary_and_tie_contract_is_explicit():
    validation = LIB["simulation_validation"]
    gaps = {item["gap"]: item["expected"] for item in validation["boundary_cases"]}
    assert "no relational pattern" in gaps[0.79]
    assert "qualifies" in gaps[0.80]
    assert LIB["pattern_precedence"][0] == "P_K"

def test_all_625_band_vectors_have_deterministic_output():
    for vector in itertools.product(BANDS, repeat=4):
        selected = select(vector)
        assert selected in set(LIB["profile_shapes"]) | set(LIB["relational_patterns"])

def test_capacity_context_is_available_for_all_dimensions():
    for dimension in DIMS:
        assert LIB["strongest_capacity_meaning"][dimension]["individual"]
        assert LIB["strongest_capacity_meaning"][dimension]["collective"]
        assert LIB["lowest_capacity_context"][dimension]["individual"]
        assert LIB["lowest_capacity_context"][dimension]["collective"]


def test_simulation_matrix_has_contrasting_profiles():
    cases = LIB["simulation_matrix"]["cases"]
    assert len(cases) >= 10
    ids = {case["id"] for case in cases}
    assert {"I-02","C-01","I-03","C-02"} <= ids
    for case in cases:
        assert set(case["scores"]) == set(DIMS)
        assert case["expected_pattern"]
        assert case["editorial_question"]
