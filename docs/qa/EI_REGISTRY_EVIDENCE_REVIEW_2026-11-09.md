# EI Registry Evidence Review — 2026-11-09

## Scope and decision

This is a QA evidence ledger for the Emergency Intelligence registry used by Living Archive. It does not authorize a production upload, registry activation, WordPress mutation, or deployment. The local registry remains authoritative while remote updates remain disabled pending cryptographic publisher authentication.

## Independently checked entries

| Country / service | Registry value | Independent evidence | QA conclusion |
|---|---|---|---|
| Philippines / unified emergency | 911 | Philippine eHotlines government directory lists National Emergency Hotline 911; DILG-NCR says Unified 911 is the country's single hotline for police, fire, medical and other emergencies (launched 2026-07-22). | Corroborated |
| Philippines / NCMH crisis | 0917-899-8727 | DSWD WiSUPPORT FAQ lists NCMH mobile 0917-899-8727 and states service is 24/7; eHotlines directory also lists NCMH. The current NCMH official contact search result lists 0917-899-8727 and other channels. | Corroborated; add NCMH direct source URL to verification record |
| United States / general emergency | 911 | FCC 911/E911 guidance identifies 911 as the universal emergency number. It also cautions that emergency services through a PSAP may not be available in every locality. | Number corroborated; coverage wording must not overstate universal service availability |
| Germany / general, medical, fire | 112 | German Federal Ministry of Health emergency reform FAQ (status 2026-10-15) says 112 directly reaches a rescue control centre for life-threatening emergencies or serious health disorders; official German government portal identifies 112 for fire and emergency services. | Corroborated |
| China / police | 110 | UK FCDO China travel advice lists 110 police; official Chinese government pages also list this. | Corroborated |
| China / fire and rescue | 119 | UK FCDO China travel advice lists 119 fire; official Chinese government pages list 119 fire. | Corroborated |
| China / medical | 120 | UK FCDO China travel advice lists 120 ambulance; official Chinese government pages list 120 medical rescue. | Corroborated |
| China / traffic police | 122 | UK FCDO China travel advice lists 122 traffic police; official Chinese government pages list 122 traffic accident police. | Corroborated |
| United Kingdom / emergency | 999 and 112 | GOV.UK identifies both as national UK emergency numbers. | Corroborated |

## Primary source references

- Philippines government emergency hotline directory: https://ehotlines.e.gov.ph/
- DILG-NCR Unified 911 announcement (2026-07-22): https://ncr.dilg.gov.ph/dilg-leads-nationwide-campaign-for-unified-911-emergency-hotline/
- DILG 2026 Unified 911 performance notice: https://www.dilg.gov.ph/news/DILG-Unified-911-hits-9615-efficiency-handles-127-million-calls/NC-2026-1272
- DSWD WiSUPPORT FAQ / NCMH crisis hotlines: https://ekwentomo.dswd.gov.ph/faqs/
- NCMH official contact page: https://ncmh.gov.ph/contact-us/
- US FCC 911/E911 guidance: https://www.fcc.gov/general/9-1-1-and-e9-1-1-services
- US National 911 Program: https://www.911.gov/
- German Federal Ministry of Health emergency reform FAQ: https://www.bundesgesundheitsministerium.de/service/gesetze-und-verordnungen/guv-21-lp/notfallreform/faq-notfallreform
- German official government portal: https://www.make-it-in-germany.com/en/arriving-living/getting-started/everyday-knowledge
- China emergency services: https://www.gov.uk/foreign-travel-advice/china/getting-help
- China government emergency number listing (Beijing Communications Administration): https://bjca.miit.gov.cn/zwgk/tzgg/art/2022/art_8d4eb93ee3424f30826c97ee400e8937.html
- UK GOV.UK emergency numbers: https://www.gov.uk/guidance/999-and-112-the-uks-national-emergency-numbers

## Evidence gaps and corrective requirements

1. Existing verification records use generic source labels (for example, "DILG" or "Chinese government sources") instead of durable per-resource evidence URLs. Update the registry schema to require a source URL per verification record and, where one verification record covers multiple service numbers, explicit evidence mapping to each resource.
2. US resource coverage is labelled national. Keep 911 as the national number, but add a caution / scope note that PSAP capability and coverage may vary locally and must not be represented as guaranteed uniform service availability.
3. Germany architecture currently identifies only one 112 number for general, medical and fire. This is broadly supported, but 110 police must not be incorrectly implied to be covered by 112; registry service mapping should preserve the distinct police channel.
4. China source mapping must distinguish 110 police, 119 fire/rescue, 120 ambulance/medical, and 122 road traffic police. Do not use a generic source string without per-resource evidence.
5. Philippines NCMH entry should include its direct official NCMH contact page URL in addition to DSWD and eHotlines corroboration. Recheck the currently published alternate telephone numbers before any registry change.
6. Each active resource must be excluded from selection if its verification is absent, future-dated, expired, malformed, or not explicitly verified.
7. Diagnostic assertions must test that unverified and expired resources yield no callable telephone action; do not treat an emergency fallback as proof that the stale resource itself is valid.
8. QA must validate the exact rendered resource/action payload, not just that a verification record exists.

## Implementation observations from code review

- Registry `validate_structure()` validates required arrays and basic shape; `validate_candidate()` validates referential integrity but the runtime registry load path calls `validate_structure()` only.
- Resource selector does check active status and current verification dates before choosing registry resources; it fails closed when no eligible resource is available.
- The registry's `signature_required` field is false, but the updater currently disables remote updates pending cryptographic signature verification. Preserve this fail-closed updater behavior.
- The admin diagnostic currently runs the fixture set and checks selected numbers/status. Expand it to exercise invalid/expired verification, resource-to-source association, and output action gating.
- The existing WordPress REST integration harness uses a test-only empty canonical retriever stub. This test validates WordPress REST bootstrap/dispatch, not canonical retrieval integration, and the limitation must remain explicit.

## Release gate

No EI/HRN production release until:
- per-resource source URL and evidence mapping are present and independently checked;
- verification-expiry and signature/authentication cases are tested;
- unsupported/refused/unknown location behavior remains fail-closed;
- HRN location-only boundary remains intact (no visitor answers or transcripts accepted);
- live disposable WordPress REST integration and browser E2E pass;
- emergency phone actions are asserted only for currently verified selections.

This review is evidence and acceptance criteria only. No production services, Render configuration, WordPress plugins, registry data, or live deployments were modified by this review.
