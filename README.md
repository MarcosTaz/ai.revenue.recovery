# Aviation Recovery

Recovery-first software for airline/lessee aircraft-lease entitlements.

## Current status

**ASSISTED PILOT COMMERCIAL-READY**

The current product is suitable for bounded, human-reviewed recovery engagements. It is **not yet positioned as self-service enterprise SaaS**. The commercial unit is an assisted Recovery Scan / Forensic Reconciliation / Claim Dossier engagement with deterministic calculations, evidence lineage, red-team review, claim lifecycle tracking and settlement-truth reporting.

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

An external claim package requires the evidence-lineage gate to pass. A claim cannot be reported as `settled` without economic settlement evidence.

## Core components

- `aviation_recovery.py` — deterministic, contract-configured entitlement engine.
- `recovery_truth.py` — separates claim-ready value, review pipeline and blocked potential.
- `aviation_dossier.py` — internal review dossier and externalization lineage gate.
- `claim_package.py` — external claim-package renderer after gate approval.
- `claim_workflow.py` — claim lifecycle from detection through verified settlement.
- `aviation_io.py` — JSON ingestion/evaluation pipeline.
- `executive_report.py` — executive recovery truth reporting.
- `cli.py` — assisted operator entrypoint.

## Quickstart — synthetic pilot

Run the complete synthetic evaluation and executive-report flow:

```bash
python cli.py examples/pilot.json \
  --output evaluated.json \
  --report executive.md
```

Run all automated tests:

```bash
python -m unittest discover -s tests -v
```

The synthetic pilot intentionally includes both claim-ready value and a blocked candidate so reporting semantics can be verified.

## Commercial positioning

Primary buyer: airline CFO/Finance, Fleet/Asset Management, Engineering Finance, Procurement, Lease Management and internal audit teams managing leased aircraft or engines.

Initial assisted offer:

- **Recovery Scan** — portfolio/lease triage to locate high-probability missed claims.
- **Forensic Reconciliation** — reconstruct eligible amount, reserve balance, contribution mechanics and time-bar status.
- **Claim Dossier** — calculation, clause map, source evidence, exceptions and submission package.
- **Recovery Monitoring** — recurring detection of new maintenance events and approaching contractual deadlines.

Commercial operating material lives in:

- `docs/PILOT_SOW.md`
- `docs/PILOT_DATA_REQUEST.md`
- `docs/OPERATOR_RUNBOOK.md`
- `docs/CLAIM_DOSSIER.md`
- `docs/SECURITY_AND_CONFIDENTIALITY.md`
- `docs/GTM.md`
- `docs/OUTBOUND_PLAYBOOK.md`
- `docs/READINESS.md`

## Boundary of the current milestone

The current milestone proves a sellable assisted recovery workflow. Enterprise SaaS capabilities such as tenant administration, SSO, deep ERP/M&E integrations, customer self-service and formal external security assurance belong to the post-pilot scale phase; they are not required to sell or execute the bounded assisted pilot defined here.
