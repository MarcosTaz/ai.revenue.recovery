# AERVIND

**AERVIND** is the canonical commercial brand for the Aviation Lease Entitlement Recovery product and assisted recovery operation.

Recovery-first software and assisted recovery operations for airline/lessee aircraft-lease entitlements.

## Brand / legal identity

- Canonical brand: **AERVIND**
- Product descriptor: **Aviation Lease Entitlement Recovery**
- Preferred legal-company form: **AERVIND, Unipessoal Lda.**, subject to formal Portuguese company-name admissibility and incorporation.
- Preferred primary domain: **aervind.com** (checked available on 2026-09-04; purchase not yet executed).

Until incorporation is complete, do not represent AERVIND as an already registered Portuguese company or invent NIPC/VAT, registered office, banking, insurance or signatory facts.

## Current status

**FIRST PAID PILOT READY — EXTERNAL EXECUTION GATE**

The product is ready for a bounded, human-reviewed paid airline Recovery Scan. It is **not positioned as self-service enterprise SaaS** yet.

Core product, recovery-truth controls, evidence lineage, claim workflow, synthetic E2E, buyer mapping, compliant channel strategy, TAP procurement preparation, capability statement and meeting-ready synthetic proof are complete for the first assisted engagement.

The remaining gate is external, not architectural: incorporation/selection of the real supplier legal identity, truthful procurement declarations, an authorized signatory where required, and explicit approval to register/contact/submit through the selected airline channel.

Canonical external milestone: GitHub issue **#15 — FIRST PAID AIRLINE PILOT — external execution gate**.

## Initial wedge

Recover and prove value already available under lease economics:

1. Maintenance-reserve reimbursements
2. Lessor maintenance contributions / cost-sharing
3. Security-deposit and prepaid-rent releases
4. End-of-lease adjustments

The product is deliberately **not** a generic lease-management system. It reconstructs contractual entitlement truth, reconciles it against maintenance/finance evidence, produces a human-reviewable recovery candidate, and generates a claim-ready evidence dossier.

## Canonical workflow

`lease -> clause/rule version -> asset/component -> maintenance event -> invoice/workscope evidence -> reserve/contribution ledger -> entitlement calculation -> exceptions/red-team -> human review -> claim package -> submission -> settlement -> recovery audit trail`

## Recovery-truth vocabulary

These states are intentionally distinct:

`identified -> blocked / review_required -> claim_ready -> submitted / approved -> settled / recovered`

Only evidence-backed settlement is reported as recovered value. Blocked, review-required, submitted or approved amounts must never inflate recovered value.

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
- `executive_report.py` — executive recovery-truth reporting.
- `cli.py` — assisted operator entrypoint.

## Quickstart — core synthetic pilot

```bash
python cli.py examples/pilot.json \
  --output evaluated.json \
  --report executive.md
```

## Quickstart — first-airline meeting demo

The TAP-shaped scenario is **100% synthetic** and must never be presented as TAP data or findings.

```bash
python cli.py examples/tap_synthetic_demo.json \
  --output tap_demo_evaluated.json \
  --report tap_demo_executive.md
```

Expected synthetic truth:

- claim-ready: **EUR 1,260,000**;
- review-required: **EUR 187,500**;
- blocked potential: **EUR 200,000**;
- settled/recovered: **EUR 0**.

Run all automated tests:

```bash
python -m unittest discover -s tests -v
```

## First commercial execution queue

1. **TAP Air Portugal** — preferred first reference; supplier onboarding / SAP Ariba path prepared.
2. **Norwegian** — CFO + Finance, Control & Fleet; direct professional route and corporate B2B routing mapped.
3. **Icelandair Group** — CFO + Technical & Maintenance / aircraft-leasing ownership mapped.
4. **Wizz Air** — high-value, harder-sale account; CFO + procurement/supply-chain route; IR excluded for cold commercial.
5. **airBaltic** — monitor/qualify rather than lead the first paid reference.

No target signal is evidence that an airline has missed claims.

## Commercial operating material

Product / delivery:

- `docs/PILOT_SOW.md`
- `docs/PILOT_DATA_REQUEST.md`
- `docs/OPERATOR_RUNBOOK.md`
- `docs/CLAIM_DOSSIER.md`
- `docs/SECURITY_AND_CONFIDENTIALITY.md`
- `docs/READINESS.md`

Commercial execution:

- `docs/GTM.md`
- `docs/OUTBOUND_PLAYBOOK.md`
- `docs/TARGET_ACCOUNTS.md`
- `docs/BUYER_MAP.md`
- `docs/PROSPECT_EVIDENCE.md`
- `docs/CONTACT_ROUTES.md`
- `docs/CHANNEL_STRATEGY.md`

First-reference / procurement:

- `docs/CAPABILITY_STATEMENT.md`
- `docs/TAP_SUPPLIER_INTAKE.md`
- `docs/TAP_LIVE_ONBOARDING_2026.md`
- `docs/PROCUREMENT_READINESS.md`
- `docs/TAP_SYNTHETIC_DEMO.md`
- `docs/BRAND_AND_ENTITY.md`
- `ops/CONTACT_ROUTES.csv`
- `ops/OUTBOUND_QUEUE.csv`

## External execution boundary

Do not fabricate or infer formal supplier facts such as registered legal entity status, registered address, VAT/tax number, company registration number, banking details, insurance, certifications, beneficial ownership or authorized signatory.

Do not use guessed buyer emails or prohibited cold-commercial infrastructure. Under the current setup, Primitive is not the AERVIND cold-prospecting channel.

Do not represent AERVIND as legal counsel, statutory auditor, MRO or airworthiness authority.

## Boundary of the current milestone

The assisted product can now be sold and executed as a bounded paid pilot. The next proof is **real airline contract/evidence data and a paid cohort**, not another internal architecture cycle.

Enterprise SaaS capabilities such as tenant administration, SSO, deep ERP/M&E integrations, customer self-service, automated multi-tenant billing and formal external security assurance remain post-pilot scale items unless a real buyer makes one a prerequisite.