# Living Archive — Canonical Ecosystem Architecture Register

**Status:** Canonical governance register  
**Purpose:** Prevent architectural sprawl by making the role, authority, and lifecycle of every service explicit.

## Constitutional rule

The Living Archive ecosystem has **one canonical codebase and one canonical intelligence authority**. Redundancy is permitted at the serving layer for resilience; it must not create competing knowledge authorities.

No service may be treated as production infrastructure merely because it remains deployed.

---

## 1. Canonical production serving

| Component | Role | Authority | Lifecycle |
|---|---|---|---|
| USE Primary — `living-archive-backend` | Primary live Guide serving node | Production serving | **KEEP** |
| USE2-Mirror — `living-archive-backend-mirror` | Active secondary Guide serving node and counterpart capacity | Production serving / resilience | **KEEP** |

### Active-active contract

The two nodes share one canonical codebase and participate in a hard-wired runtime contract:

- Primary normally retains approximately 70% of Guide composition workload.
- USE2-Mirror receives approximately 30% through the authenticated peer-only capability boundary.
- If a local Guide provider bank exhausts bounded capacity, the counterpart receives one bounded opportunity before deterministic recovery.
- The counterpart does not recursively delegate.
- Geographic separation is intentional resilience, not a second intelligence authority.

---

## 2. Canonical intelligence and quality authority

The Gold Star repository is **singular and canonical**.

Its approved exemplars may participate in the Guide's live quality and deterministic recovery architecture. The Gold Star QA/HRN validation function is a quality gate and audit environment; it is **not a competing production repository or alternative intelligence authority**.

**Rule:** Gold Star authority must not fork across serving nodes or QA environments.

---

## 3. Product-specific services

| Component | Role | Lifecycle |
|---|---|---|
| mini-USE-payhip | Catalogue/product navigation function | **KEEP — separate product function** |

Product-specific services do not become part of the Guide's active-active serving topology unless explicitly promoted through an architectural decision.

---

## 4. Experimental and legacy services

| Service | Current branch/purpose | Classification | Required action |
|---|---|---|---|
| living-archive-predictive-shadow | Predictive provider experiment | **EXPERIMENT** | Must retain an explicit purpose, owner, success criterion, and expiry/review date |
| living-archive-v340-qa | Historical QA environment | **RETIRED CANDIDATE** | Do not use for current production architecture; retain only pending deliberate retirement decision |
| living-archive-v334-lean-control | Historical control environment | **RETIRED CANDIDATE** | Do not use for current production architecture; retain only pending deliberate retirement decision |

### Experiment rule

An active experiment without a current architectural purpose and review date is infrastructure sprawl. Experiments must be either renewed explicitly or retired.

---

## 5. Service admission rule

Before a new service is created, the architecture must answer:

1. What canonical function does it serve?
2. Why can an existing node not perform that function?
3. Is it production, resilience, QA, experiment, or product-specific?
4. Does it create a new intelligence authority or duplicate an existing one?
5. What is its owner and review/expiry date?
6. What is its retirement path?

If these questions cannot be answered, the service should not be created.

---

## 6. Canonical topology

```
                    LIVING ARCHIVE
             Canonical Code + Intelligence
                          |
             +------------+------------+
             |                         |
        USE PRIMARY                 USE2-MIRROR
        Production                    Production
          ~70%                          ~30%
             \                         /
              \-- bounded counterpart --/
                         |
                 Provider capacity
                         |
          Gold Star-informed quality
             and deterministic recovery

      QA validates the architecture; it does not
      become a competing intelligence authority.
```

---

## Governance conclusion

The ecosystem is intentionally small:

**One canonical authority. Two serving nodes. One bounded QA function. Product-specific services only where justified. Experiments are temporary. Legacy infrastructure is not architecture.**

Any future architectural change must update this register in the same change set that alters the service topology.
