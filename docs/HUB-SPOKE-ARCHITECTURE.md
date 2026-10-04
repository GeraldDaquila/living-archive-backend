# Hub Architecture Correction — Post-Oct. 1

## Canonical topology

The Guide / USE is the **HUB** and remains the center of the system.

Specialist capabilities are **SPOKES** connected to the hub.

Examples of spokes:
- Seeing the Relationship / HRN
- Stewardship Pathway Engine / SPE
- Learning Arc Navigator / LAN
- future bounded specialists

The preserved pre-Oct. 1 USE implementation is itself repurposed as a **general-purpose utility spoke**. It is not the hub.

## Correct flow

visitor
→ **Guide / USE hub**
→ determine the appropriate spoke or hub-level handling
→ specialist spoke, when warranted
→ specialist-owned work
→ normalized contribution back to **Guide / USE hub**
→ shared canonical/navigation handling
→ visitor

For non-specialized work:

visitor
→ **Guide / USE hub**
→ **General Use Utility spoke (legacy USE)**
→ contribution/result
→ **Guide / USE hub**
→ visitor

## Ownership

### Guide / USE hub

Owns:
- the visitor request and session boundary
- orientation and interpretation
- recognition of whether a spoke is warranted
- spoke authorization and handoff
- common contribution validation
- common synthesis/navigation integration
- final visitor response boundary
- the system's shared canonical doorway/navigation authority

The hub should coordinate; it should not absorb each spoke's domain reasoning.

### Specialist spokes

Own:
- domain-specific reasoning
- domain-specific models/providers
- specialist voice and interaction logic
- specialist state and internal processing
- specialist contribution material

A spoke returns through an explicit contract. It does not become a hidden dependency of another spoke.

### Legacy USE general-purpose utility spoke

Owns:
- broad questions that do not warrant a dedicated specialist
- compatibility and fallback utility work
- experimental/general-purpose behavior
- future learning that may later be harvested into the hub

It is deliberately subordinate to the hub.

## Architectural correction

The prior description that characterized the specialist contract as a "hub" separate from USE was inverted.

`hub_contracts.py` should therefore be understood as a **hub-side contract module**, not a replacement hub or competing architecture. It exists to define the hub's common language with its spokes.

The canonical architecture is:

**USE / The Guide = HUB**
**HRN / SPE / LAN / etc. = SPOKES**
**Legacy USE general utility = one SPOKE**

## Design principle

The center remains intelligent and authoritative about orchestration, while the spokes remain specialized and independently evolvable.

We preserve the old USE learning without allowing the old implementation to define the new hub.
