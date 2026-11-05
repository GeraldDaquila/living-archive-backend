"""Philippine Systems Lens specialist bridge."""
from __future__ import annotations
from typing import Mapping
from specialist_adapters import SpecialistAdapterContext
from specialist_registry import SPECIALIST_PIPE_CONTRACT_VERSION
PHILIPPINE_SYSTEMS_LENS_URL = "https://geralddaquila.com/understanding-the-philippines-culture-society-history-and-systemic-transformation/"
class PhilippineSystemsAdapter:
    specialist_id = "systems_ph"
    def process(self, context: SpecialistAdapterContext) -> Mapping[str, object]:
        combined = f"{context.original_question} {context.recognized_territory}".lower()
        philippines = ("philipp", "filipino", "filipina", "pinoy", "pilipinas")
        systems = ("system", "governance", "institution", "culture", "society", "history", "economy", "politic", "migration", "trust")
        if not any(x in combined for x in philippines) or not any(x in combined for x in systems):
            return _declined(context, "The inquiry does not clearly require a Philippine systems contribution.")
        return {"contract_version": SPECIALIST_PIPE_CONTRACT_VERSION,"request_id": context.request_id,"specialist_id": self.specialist_id,"status": "CONTRIBUTION","interpretation": "Treat the inquiry as an interacting Philippine condition rather than reducing it to a single cause or sector.","perspectives": ["historical inheritance","formal and informal institutions","culture and social trust","local adaptation and capacity"],"movement": "Offer the canonical Philippine Systems Lens when deeper contextual inquiry would improve orientation.","canonical_candidates": [{"url": PHILIPPINE_SYSTEMS_LENS_URL,"role": "specialist_doorway"}],"boundary_notes": "Orientation only; the Guide retains final interpretation, evidence validation, and visitor-facing response.","safety_flags": [],"payload": {"canonical_lens_url": PHILIPPINE_SYSTEMS_LENS_URL,"contextual_inquiry_available": True}}
def _declined(context: SpecialistAdapterContext, reason: str) -> Mapping[str, object]:
    return {"contract_version": SPECIALIST_PIPE_CONTRACT_VERSION,"request_id": context.request_id,"specialist_id": "systems_ph","status": "DECLINED","interpretation": None,"perspectives": [],"movement": None,"canonical_candidates": [],"boundary_notes": reason,"safety_flags": [],"payload": {}}
