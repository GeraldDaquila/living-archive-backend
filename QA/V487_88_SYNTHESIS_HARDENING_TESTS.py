from shared_intelligence_primitives import Claim, build_synthesis_material

def main():
    claims=(
        Claim(text="A supported proposition.", evidence_ids=("a",), claim_type="observation", epistemic="supported"),
        Claim(text="An interpretive proposition.", evidence_ids=("c",), claim_type="interpretation", epistemic="interpretive"),
    )
    material=build_synthesis_material(claims)
    assert material.claims==claims
    assert material.source_ids==("a","c")
    print("v487.88 synthesis hardening compatibility probes: PASS")
if __name__=="__main__": main()
