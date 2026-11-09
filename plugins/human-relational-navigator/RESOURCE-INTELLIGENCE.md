# Human Relational Navigator — Resource Intelligence v0.5.13

## Purpose

HRN now separates safety logic from country-specific resource data.

The safety engine decides the safety state and immediate action. The Resource Intelligence layer selects the smallest relevant set of verified resources for that state and the visitor's country.

## Resource hierarchy

1. Native registry — first-line resources with official/service provenance.
2. Find A Helpline — global fallback for countries or services not yet represented in the native registry.
3. No resource is presented as independently verified by Living Archive unless its record carries `verification=official` and a provenance source.

Find A Helpline is treated as an external verified-directory source, not as Living Archive's own emergency registry.

## Selection model

Resource records contain:

- country
- service type
- situation tags
- priority
- hours
- channels
- source
- source type
- verification status
- source URL

The presenter scores resources against the current safety state and latest visitor message. Medical-emergency records are preferred when the latest message indicates injury, overdose, ingestion, or another medical emergency. Immediate-safety resources are preferred for acute danger when no medical event is indicated.

Country-specific programming is not used to decide the safety state. Country differences are represented as data.

## Find A Helpline fallback

For a recognized country code without a native registry record, HRN creates a country-specific Find A Helpline doorway at:

`https://findahelpline.com/countries/{ISO-2-code}`

If the country cannot be resolved to an ISO-2 code, HRN asks the visitor for country information and retains the general Find A Helpline doorway as fallback.

## Verification policy

Native first-line emergency resources should be independently grounded in an official government or service source before being promoted to the acute first-line presenter.

Find A Helpline's own verification status is retained as provenance. It is not silently converted into Living Archive verification.

## Current native registry

The native registry now covers the site's ten highest-traffic countries shown in the supplied nine-month analytics snapshot. Five countries were already present; five were added in v0.5.13.

- Philippines: 911; NCMH 1553
- United States: 911; 988
- China: 110 for immediate safety; 120 for medical emergency; 12356 for psychological assistance
- Canada: 911; 9-8-8 Suicide Crisis Helpline
- Germany: 112; TelefonSeelsorge 116 123
- Australia: 000; Lifeline 13 11 14
- Singapore: 999 for police emergencies; 995 for medical emergencies; Samaritans of Singapore 1767
- United Kingdom: 999; Samaritans 116 123
- Hong Kong: 999; The Samaritan Befrienders Hong Kong 2389 2222
- Netherlands: 112; 113 Suicide Prevention (113 and 0800-0113 are free; 113 is the preferred short number)

The registry remains deliberately data-driven. Countries outside this native set continue to use the Find A Helpline fallback rather than country-specific safety code.



## Netherlands registry note

The current native presentation uses **113** as the primary crisis number. 113 Zelfmoordpreventie states that 113 became free in October 2025 and is now the preferred short number; 0800-0113 remains free and available. The registry keeps 0800-0113 as an alternate number rather than presenting it as the primary card number.


## Archive Cartography v0.5.31
The ordinary relational engine now has a deterministic cartographic layer spanning all 2,007 canonical resources, including protected T4. The map is derived from canonical tags, titles and excerpts and explicitly does not claim canonical relationship edges. It organizes resources into 14 broad territories and perspective types and allows territory-aware retrieval to surface a doorway even when the visitor has not used the Archive's own vocabulary. Access rules remain authoritative; T4 remains protected.


## Constitutional Epistemic Boundary (v0.5.35)

HRN is deliberately a **bounded school of thought** rather than an open-ended general-purpose worldview engine.

The visitor has freedom of movement: they may introduce any experience, belief, religion, philosophy, metaphysics, social theory, or outside framework. HRN may examine what the visitor brings. But HRN's own substantive ground remains the Living Archive and its constitutional frame of abundance, unity, sovereignty, freedom, reciprocity, interdependence, stewardship, service, regenerative systems, human flourishing, and related canonical principles.

The source hierarchy is:

1. **Visitor material** — the visitor's own experience and explicitly introduced worldview.
2. **Archive material** — canonical Living Archive content and cartography; authoritative ground for HRN's own substantive contribution.
3. **Model reasoning** — Groq's synthesis and language capability; never an unmarked source of worldview or cosmology.
4. **External knowledge** — not introduced as HRN authority in ordinary operation; no web/browser retrieval is enabled.

This boundary is injected at the Groq API boundary for every call, including interpretation, composition, recovery, navigation repair, and whole-journey synthesis. It is constitutional rather than a conversational preference.


## Current package baseline — v0.5.37
The resource-intelligence layer is unchanged by the v0.5.37 Guide-bridge correction. The package version is advanced so WordPress asset caches and package documentation align with the executable plugin.
