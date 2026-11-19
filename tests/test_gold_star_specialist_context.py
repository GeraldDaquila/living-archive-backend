"""Gold Star v2 contract propagation through the Guide hub boundary."""
from hub_contracts import build_hub_request, route_spoke
from gold_star_question_contract import build_question_contract
from gold_star_route_capabilities import specialist_capability


def test_question_and_specialist_capability_context_survive_hub_dispatch():
    question = "How can Philippine systems reinforce one another?"
    context = {
        "gold_star_question_contract": build_question_contract(question),
        "gold_star_specialist_capability": specialist_capability("systems_ph"),
    }
    request = build_hub_request(
        request_id="qa-systems-001",
        guide_version="test",
        original_question=question,
        recognized_territory="Philippine systems",
        processing_purpose="bounded systems orientation",
        guide_context=context,
        safety_state="green",
    )
    observed = {}

    def invoke(**kwargs):
        observed.update(kwargs)
        return {
            "contract_version": "v1",
            "request_id": kwargs["request_id"],
            "specialist_id": kwargs["specialist_id"],
            "status": "CONTRIBUTION",
            "payload": {"interpretation": {"summary": "bounded contribution"}},
        }

    contribution = route_spoke(
        request=request,
        specialist_id="systems_ph",
        invoke=invoke,
    )
    assert observed["guide_context"]["gold_star_question_contract"] == context["gold_star_question_contract"]
    assert observed["guide_context"]["gold_star_specialist_capability"] == context["gold_star_specialist_capability"]
    assert contribution.status == "CONTRIBUTION"


def test_specialist_context_is_not_mislabeled_as_visitor_ready_answer():
    question = "What should I learn from this situation?"
    context = {
        "gold_star_question_contract": build_question_contract(question),
        "gold_star_specialist_capability": specialist_capability("formation"),
    }
    request = build_hub_request(
        request_id="qa-formation-001",
        guide_version="test",
        original_question=question,
        recognized_territory="stewardship formation",
        processing_purpose="bounded formation navigation",
        guide_context=context,
    )
    assert request.guide_context["gold_star_question_contract"]["version"]
    assert request.guide_context["gold_star_specialist_capability"]["scope"].startswith("Bounded formation")
    # Hub contribution remains an internal contribution; visitor readiness is
    # not asserted by the hub or by capability metadata.



def test_guide_runtime_supplies_contracts_to_both_active_specialist_hub_paths():
    from pathlib import Path

    source = Path(__file__).resolve().parents[1].joinpath("main.py").read_text(encoding="utf-8")
    assert '_gold_star_specialist_capability("systems_ph")' in source
    assert '_gold_star_specialist_capability("formation")' in source
    assert '_build_gold_star_question_contract(query)' in source
    assert '"route_source": "deterministic-systems-preparation-entry"' in source
    assert '"route_source": "deterministic-formation-preparation-entry"' in source
