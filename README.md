# Recovery Radar

Evidence-first system for constructing and defending supplier recovery claims after customer program cancellation or severe volume reduction.

## Current product truth — v0.2

Source was established on the isolated branch `recovery-radar/program-cancellation-claims`; `main` originally contained only `.gitkeep`.

Implemented:

- deterministic cancellation / volume-reduction event model;
- stranded exposure categories including raw material, E&O, WIP, finished goods, tooling, NRE, supplier commitments and dedicated capacity;
- mitigation and prior-reimbursement deductions;
- explicit separation of exposure, entitlement, claimability, settlement and payment;
- ownership fail-closed checks;
- duplicate economic-loss protection;
- missing-evidence detection;
- contractual/support states including conflicting and unsupported outcomes;
- partial support with defensible recovery caps;
- high-risk/legal interpretation routed to human review;
- auditable claim package projection;
- settlement workflow where `SETTLED != PAID`;
- multiple evidenced partial payments with overpayment/duplicate/currency controls;
- tenant-scoped SQLite claim persistence and audit trail;
- business service scoped by an already-authenticated `Principal` rather than caller-supplied workspace IDs;
- reviewer authority limited to evidence/review states; reviewer cannot submit, negotiate, settle or record payment;
- backup/restore economic-digest verification;
- independent arithmetic and claim-line ground-truth scoring;
- Alpha Components, zero-recovery, partial-recovery and RedTeam Industrial synthetic cases.

Current exact tested semantics include a RedTeam portfolio with customer-owned tooling, missing entitlement, missing mitigation evidence, duplicate economic losses, negative quantity, partial support and already-reimbursed amounts. Synthetic oracle results have zero false claims, missed claims, overclaims, underclaims and state mismatches for the covered fixture. This proves deterministic behavior only; it is not evidence that a real OEM will accept or pay a claim.

## Important boundaries

- `CLAIMABLE` is not a legal conclusion.
- `REQUIRES_REVIEW` is not claim approval.
- `SETTLED` is not `PAID`.
- claim value never becomes recovered cash without evidenced payment records.
- the current `Principal` object assumes authentication has already occurred outside this module; real authentication/session infrastructure is **not implemented**.
- persistence currently covers claim workflow/payment state, not the complete event/exposure/document graph.

Still required for PILOT_READY includes real auth/session verification, broader tenant attack surface, event/exposure/evidence persistence, document ingestion/conflict attacks, complete synthetic supplier factory, backup-corruption/migration/DB-lock failure tests, scale/export acceptance, and no known P0/P1 at exact-head CI.
