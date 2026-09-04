# AERVIND

**AERVIND** is the canonical commercial brand for Aviation Lease Entitlement Recovery: assisted software and recovery operations for airline/lessee aircraft-lease economics.

## Brand / legal identity

- Canonical brand: **AERVIND**
- Product descriptor: **Aviation Lease Entitlement Recovery**
- Primary domain: **aervind.com** — registered on 2026-09-04 via Porkbun
- Initial supplier model: the operator's real Portuguese individual-professional activity, trading commercially as AERVIND where legally appropriate
- Future scale vehicle: **AERVIND, Unipessoal Lda.** only when buyer procurement, revenue, liability or accounting complexity justifies incorporation

Do not represent AERVIND as an already incorporated company while it operates through the individual professional supplier. Contracts and invoices must preserve the legally required supplier name, tax number and address. Never invent NIPC/VAT, registered office, banking, insurance, certification or signatory facts.

See `docs/SOLE_TRADER_LAUNCH.md`.

## Current status

**FIRST PAID PILOT READY — COMMERCIAL OUTREACH OPEN**

The product is ready for a bounded, human-reviewed airline Recovery Scan. It is intentionally **not** positioned as self-service enterprise SaaS before real buyer evidence requires that scale.

The current assisted product closes the operational path from customer evidence through deterministic reconciliation, source-lineage review, claim package, external-lifecycle audit and verified settlement reporting.

No live ERP, M&E, lease-management or banking-system access is required for the first Recovery Scan. PDFs, spreadsheets and controlled exports are sufficient when supplied through the agreed engagement route.

Canonical external milestone: GitHub issue **#15 — FIRST PAID AIRLINE PILOT — external execution gate**.

## Initial wedge

1. Maintenance-reserve reimbursements
2. Lessor maintenance contributions / cost-sharing
3. Security-deposit and prepaid-rent releases
4. Selected end-of-lease adjustments

AERVIND is a recovery/proof/control layer, not a generic lease-management system, MRO, legal adviser, statutory auditor or airworthiness authority.

## Canonical chain

`lease / amendment -> rule version -> asset / component -> maintenance event -> financial evidence -> reserve / contribution ledger -> entitlement calculation -> exclusions / deadline / prior-payment checks -> source lineage -> human review -> claim-ready package -> real submission -> counterparty process -> verified settlement -> executive closeout`

## Recovery truth

Economic status:

`blocked / review_required / claim_ready / zero_entitlement`

External lifecycle:

`detected -> reviewing -> claim_ready -> submitted -> acknowledged / disputed / approved / rejected -> settled`

Only evidence-backed settlement is recovered value.

AERVIND never combines identified, blocked, review-required, submitted or approved value with verified recovery.

## Product gates

A candidate cannot be released as `claim_ready` unless:

- governing lease/rule version is identified;
- event and affected asset/component are identified;
- required evidence is present or explicitly waived by a human reviewer where permitted;
- calculation is reproducible from stored inputs;
- prior reimbursement / claim offsets are reconciled;
- contractual deadline status is known;
- exclusions, caps, floors, deductibles and rates are evaluated;
- every material input has a source reference;
- the human lifecycle review explicitly reaches workflow `claim_ready`.

A generated claim package is re-evaluated at generation time, SHA-256 hashed into the portable case audit and always remains `not_submitted` until a real external submission occurs.

A claim reaches `settled` only when positive economic settlement evidence exists with amount, currency and reference.

## Core components

- `aviation_recovery.py` — deterministic contract-configured entitlement engine
- `aviation_io.py` — normalized ingestion, validation and source-lineage gating
- `recovery_truth.py` — conservative economic status summary
- `aviation_dossier.py` — internal review dossier and externalization gate
- `claim_package.py` — controlled external package renderer
- `claim_workflow.py` — auditable lifecycle and settlement rules
- `workflow_case.py` — portable case state, cohort revision binding and artifact audit
- `executive_report.py` — mutually exclusive management recovery buckets
- `operator_app.py` + `operator_ui/` — local assisted Recovery Control Room
- `cli.py` — command-line assisted evaluator

## Assisted operator console

```bash
python operator_app.py
```

Open:

```text
http://127.0.0.1:8080
```

The browser console supports:

- cohort JSON upload/paste;
- deterministic evaluation;
- recovery-truth dashboard;
- candidate drill-down;
- blockers, warnings, evidence, source lineage and calculation trace;
- auditable lifecycle transitions;
- external reference capture for real submission/counterparty events;
- human-gated claim-package generation;
- package artifact hashing;
- settlement-evidence recording;
- workflow-aware executive reporting;
- portable case export/reopen.

The server binds to localhost, processes request bodies in memory and does not create hidden server-side customer persistence. Durable assisted-pilot state exists only in the operator-exported AERVIND case file, which must be stored in the approved engagement location.

See `docs/OPERATOR_CONSOLE.md`.

## Synthetic proof

Core synthetic pilot:

```bash
python cli.py examples/pilot.json \
  --output evaluated.json \
  --report executive.md
```

TAP-shaped meeting demo:

```bash
python cli.py examples/tap_synthetic_demo.json \
  --output tap_demo_evaluated.json \
  --report tap_demo_executive.md
```

The TAP-shaped scenario is **100% synthetic** and must never be represented as TAP data, discovered leakage or a claim about TAP.

Expected synthetic TAP truth:

- claim-ready: **EUR 1,260,000**
- review-required: **EUR 187,500**
- blocked potential: **EUR 200,000**
- settled/recovered: **EUR 0**

Run regression tests:

```bash
python -m unittest discover -s tests -v
```

## First paid offer

Canonical first engagement:

**Recovery Scan — €9,500**

- up to 5 aircraft and/or engines;
- one primary entitlement family;
- up to 12 months of selected events;
- target 10 business days after the complete agreed minimum dataset;
- evidence-led candidate register, blockers, calculation trail and claim-ready dossier where gates pass;
- no recovery guarantee.

See `docs/FIRST_PAID_RECOVERY_SCAN_PROPOSAL.md` and `docs/PILOT_SOW.md`.

## Initial commercial execution queue

1. **TAP Air Portugal** — strategically valuable home-market reference; procurement path prepared
2. **Norwegian** — Finance / Control / Fleet route mapped
3. **Icelandair Group** — Finance + Technical/Maintenance/aircraft-leasing ownership mapped
4. **Wizz Air** — high-value, harder-sale account; finance + procurement/supply-chain route
5. **airBaltic** — qualify/monitor rather than force first-reference status

The first actual customer does **not** need to be TAP. Prefer the first qualified airline/operator that accepts a bounded paid Recovery Scan and can contract with the truthful initial supplier model without unnecessary overhead.

No public target signal is evidence that an airline has missed claims.

## Commercial operating material

Product / delivery:

- `docs/PILOT_SOW.md`
- `docs/PILOT_DATA_REQUEST.md`
- `docs/OPERATOR_RUNBOOK.md`
- `docs/OPERATOR_CONSOLE.md`
- `docs/CLAIM_DOSSIER.md`
- `docs/SECURITY_AND_CONFIDENTIALITY.md`
- `docs/READINESS.md`

Commercial execution:

- `docs/FIRST_PAID_RECOVERY_SCAN_PROPOSAL.md`
- `docs/GTM.md`
- `docs/OUTBOUND_PLAYBOOK.md`
- `docs/TARGET_ACCOUNTS.md`
- `docs/BUYER_MAP.md`
- `docs/PROSPECT_EVIDENCE.md`
- `docs/CONTACT_ROUTES.md`
- `docs/CHANNEL_STRATEGY.md`
- `docs/EMAIL_OPERATIONS.md`

Procurement / supplier truth:

- `docs/CAPABILITY_STATEMENT.md`
- `docs/PROCUREMENT_READINESS.md`
- `docs/TAP_SUPPLIER_INTAKE.md`
- `docs/TAP_LIVE_ONBOARDING_2026.md`
- `docs/BRAND_AND_ENTITY.md`
- `docs/SOLE_TRADER_LAUNCH.md`

## Remaining gates before real revenue

These are external/factual gates, not reasons to rebuild the product:

- complete `aervind.com` site routing/deployment before claiming the site is live;
- complete Primitive custom-domain DNS verification before claiming `@aervind.com` email is live;
- verify the real Portuguese professional activity classification covers the service before first paid delivery;
- use the real legal supplier/tax identity on customer documents;
- determine customer-specific VAT/invoicing treatment;
- satisfy actual buyer-specific procurement/security requirements;
- obtain a real paid cohort and governing customer evidence.

## Non-regression rules

Do not:

- invent missing contract terms;
- count blocked/review/submitted/approved value as recovered;
- silently modify a released cohort revision;
- fabricate external submission, approval or settlement events;
- generate a claim package without auditable workflow `claim_ready` state;
- infer target-airline leakage from public information;
- use guessed buyer emails or prohibited bulk-cold infrastructure;
- invent supplier legal/tax/banking/certification facts;
- hide legally required supplier identity behind the brand;
- represent AERVIND as legal counsel, statutory auditor, MRO or airworthiness authority.

## Boundary of the current milestone

The assisted product is ready to sell and operate as a bounded paid pilot. The next decisive proof is **real airline contract/evidence data and paid customer use**, not another internal architecture cycle.

Enterprise SaaS capabilities — tenant administration, SSO, deep ERP/M&E integrations, customer self-service, automated multi-tenant billing and formal external security assurance — remain post-pilot / buyer-driven unless a real buyer makes one a prerequisite.
