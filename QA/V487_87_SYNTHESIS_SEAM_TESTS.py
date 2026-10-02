from shared_intelligence_primitives import Claim, build_synthesis_material

def main():
    claims = (
        Claim(text="A supported proposition.", evidence_ids=("a",), claim_type="observation", epistemic="supported"),
        Claim(text="An interpretive proposition.", evidence_ids=("c",), claim_type="interpretation", epistemic="interpretive"),
    )
    material = build_synthesis_material(
        claims,
        relationship_statement="Two propositions sit beside one another.",
        unresolved_tensions=("Different readings remain possible.",),
        perspective_options=("Stay with the supported proposition.",),
    )
    assert material.claims == claims
    assert material.source_ids == ("a", "c")
    assert material.relationship_statement == "Two propositions sit beside one another."
    assert material.unresolved_tensions == ("Different readings remain possible.",)
    assert material.perspective_options == ("Stay with the supported proposition.",)
    print("v487.87 synthesis material compatibility probes: PASS")

if __name__ == "__main__":
    main()
