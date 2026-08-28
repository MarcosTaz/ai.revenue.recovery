# Recovery Radar

Evidence-first system for constructing and defending supplier recovery claims after customer program cancellation or severe volume reduction.

## Current product truth — v0.3

Source is isolated on `recovery-radar/program-cancellation-claims`; `main` originally contained only `.gitkeep` and remains untouched.

Implemented:

- deterministic cancellation / volume-reduction event model;
- stranded exposure categories: raw material, E&O, WIP, finished goods, tooling, NRE, supplier commitments and dedicated capacity;
- mitigation and prior-reimbursement deduction;
- exposure != entitlement != claimability != settlement != payment;
- ownership fail-closed checks and duplicate economic-loss protection;
- missing-evidence detection and explicit contractual support states;
- partial support with defensible caps and legal/high-risk human-review routing;
- independent arithmetic and claim-line ground-truth scoring;
- Alpha Components, zero-recovery, partial-recovery and RedTeam Industrial fixtures;
- settlement/payment workflow where `SETTLED != PAID`;
- multiple evidenced payments with duplicate/currency/overpayment controls;
- tenant-scoped SQLite claim and evidence-metadata persistence with audit events;
- backup/restore economic-digest verification;
- service methods scoped by a pre-authenticated `Principal`, not caller-selected tenant IDs;
- reviewer cannot create, submit, negotiate, settle or record payment;
- SHA-256 evidence-document registry with duplicate/version conflict controls;
- wrong tenant/supplier/customer/program and unconfirmed signature surfaced for review;
- extracted document text explicitly treated as untrusted data;
- documentary fact disagreements fail closed to `CONFLICTING` when precedence is not modeled;
- **registered evidence claimability gate**: nonempty source-reference strings are not enough to make a claim package ready. Required event, cost/inventory, contract/support, mitigation and reimbursement sources must be registered and correctly scoped.

### Claimability boundary

The economic engine can produce a candidate `CLAIMABLE` / `REQUIRES_REVIEW` state from supplied records, but a customer-facing claim package is not ready until `apply_registered_evidence_gate()` has verified the required source records against the evidence registry. Missing or wrong-scope registered evidence downgrades the affected line to `POTENTIAL_ENTITLEMENT`.

This explicitly prevents an arbitrary URI string such as `contract://...` from being treated as sufficient proof by the package workflow.

### Other boundaries

- `CLAIMABLE` is an economic/evidence workflow state, not a legal conclusion.
- `REQUIRES_REVIEW` is not customer approval.
- `SETTLED` is not `PAID`.
- claim value never becomes recovered cash without evidenced payment records.
- `Principal` assumes authentication already occurred outside this module; production authentication/session infrastructure is **not implemented**.
- raw document bytes are not persisted by the registry; current persistence stores identity metadata and content hashes.
- full event/exposure/entitlement persistence and source-document parsing are not yet implemented.

## Current verification

Exact commit `dec1f0893592900ac0d3b04c66250b19b6d61dcd` passed GitHub Actions with **46 tests** on Python 3.13.15 before this README update.

Synthetic correctness is not commercial proof and does not establish collectibility or willingness to pay.
