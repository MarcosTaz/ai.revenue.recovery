# Aviation Recovery

Recovery-first software for airline/lessee aircraft-lease entitlements.

## Initial wedge

Recover value that is already contractually available but missed, under-claimed, delayed, or poorly evidenced:

1. Maintenance-reserve reimbursements
2. Lessor maintenance contributions / cost-sharing
3. Security-deposit and prepaid-rent releases
4. End-of-lease adjustments

The product is deliberately **not** a generic lease-management system. It reconstructs contractual entitlement truth, reconciles it against maintenance/finance evidence, produces a human-reviewable recovery candidate, and generates a claim-ready evidence dossier.

## Canonical workflow

`lease -> clause/rule version -> asset/component -> maintenance event -> invoice/workscope evidence -> reserve/contribution ledger -> entitlement calculation -> exceptions/red-team -> human review -> claim package -> submission -> settlement -> recovery audit trail`

## Product gates

A recovery candidate cannot become `claim_ready` unless:

- the governing lease/rule version is identified;
- the maintenance event and affected component are identified;
- required evidence is present or explicitly waived by a human reviewer;
- the calculation is reproducible from stored inputs;
- prior reimbursements / settlements have been reconciled;
- contractual time-bar/deadline status is known;
- all material exclusions and caps/floors have been evaluated;
- the dossier contains source references for every material input.

## Core engine

`aviation_recovery.py` contains a deterministic, contract-configured entitlement evaluator. It does not guess contract law or invent missing terms. It returns blocking issues when evidence or rule data is missing and supports multiple rule formulas so lease-specific language can be represented explicitly.

## Commercial positioning

Primary buyer: airline CFO/Finance, Fleet/Asset Management, Engineering Finance, Procurement, Lease Management and internal audit teams managing leased aircraft or engines.

Initial assisted offer:

- **Recovery Scan** — portfolio/lease triage to locate high-probability missed claims.
- **Forensic Reconciliation** — reconstruct eligible amount, reserve balance, contribution mechanics and time-bar status.
- **Claim Dossier** — calculation, clause map, source evidence, exceptions and submission package.
- **Recovery Monitoring** — recurring detection of new maintenance events and approaching contractual deadlines.

The first product milestone is an assisted, audit-grade pilot rather than self-service SaaS.