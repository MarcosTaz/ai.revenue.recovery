# AERVIND

**AERVIND — Aviation Lease Entitlement Recovery**

Assisted recovery-control software and professional operations for airline/lessee aircraft and engine lease economics.

## Current state

**PRODUCT: FIRST PAID RECOVERY SCAN READY**  
**REAL OUTREACH: HOLD ACTIVE — NO REAL EXTERNAL SEND**

AERVIND can execute a bounded, human-reviewed Recovery Scan from customer-supplied documents and controlled exports. The product closes the assisted path from governing contract evidence through deterministic reconciliation, human review, claim package, external-lifecycle evidence recording and verified settlement reporting.

The founder has explicitly prohibited any message to a real person or organization until that hold is explicitly lifted. Product readiness, a live domain, a discovered buyer route or a prepared draft do **not** authorize sending.

See `docs/REAL_OUTREACH_HOLD.md` and `docs/LAUNCH_ACCEPTANCE.md`.

## Brand and supplier truth

- Canonical brand: **AERVIND**
- Product descriptor: **Aviation Lease Entitlement Recovery**
- Primary domain: **aervind.com** — registered through Porkbun on 2026-09-04
- Initial supplier model: the operator's real Portuguese individual-professional activity, trading commercially as AERVIND where legally appropriate
- Future scale vehicle: **AERVIND, Unipessoal Lda.** only when buyer procurement, revenue, liability or accounting complexity justifies incorporation

Do not represent AERVIND as an incorporated company unless incorporation actually exists. Contracts and invoices must preserve the legally required supplier identity. Never invent tax, banking, insurance, certification or signatory facts.

## Canonical first engagement

**Recovery Scan — EUR 9,500**

- up to **5 aircraft and/or engines**;
- **1 primary entitlement family**;
- up to **12 months** of selected events;
- target **10 business days** after the complete agreed minimum dataset is received;
- **50% on engagement / scope confirmation, 50% on delivery**;
- no guarantee that recoverable value exists.

The first scan does **not** require live access to airline ERP, M&E, lease-management or banking systems. PDFs, spreadsheets and controlled exports are sufficient when the agreed minimum evidence set is complete.

Canonical commercial documents:

- `docs/FIRST_PAID_RECOVERY_SCAN_PROPOSAL.md`
- `docs/PILOT_SOW.md`
- `docs/PILOT_DATA_REQUEST.md`
- `docs/CLIENT_INTAKE_README.md`
- `docs/CAPABILITY_STATEMENT.md`

## Initial entitlement wedge

1. maintenance-reserve reimbursements;
2. lessor maintenance contributions / cost-sharing;
3. security-deposit and prepaid-rent releases;
4. selected end-of-lease adjustments.

AERVIND is a recovery/proof/control layer. It is not legal counsel, a statutory auditor, an MRO or an airworthiness authority.

## Canonical recovery chain

`lease / amendment → rule version → asset / component → maintenance event → financial evidence → reserve / contribution ledger → entitlement calculation → exclusions / deadline / prior-payment checks → source lineage → human review → claim-ready package → real submission evidence → counterparty process → verified settlement → executive closeout`

## Recovery truth

Economic status:

`blocked / review_required / claim_ready / zero_entitlement`

External lifecycle:

`detected → reviewing → claim_ready → submitted → acknowledged / disputed / approved / rejected → settled`

**Only evidence-backed settlement counts as recovered value.**

Identified, blocked, review-required, submitted or approved value is never reported as recovered.

## Product gates

A candidate cannot be released as `claim_ready` unless the relevant gates pass, including:

- governing lease/rule version identified;
- asset/component and event identified;
- calculation reproducible from stored inputs;
- exclusions, caps, floors, deductibles and rates evaluated;
- prior reimbursement / claim offsets reconciled;
- deadline status known;
- material inputs linked to source references;
- required evidence present or explicitly handled by a permitted human-review rule;
- human lifecycle review reaches `claim_ready`.

A claim package is re-evaluated at generation time, hashed into the portable case audit and remains `not_submitted` until a real external submission event is evidenced.

`settled` requires positive economic settlement evidence with amount, currency and reference.

## Core components

- `aviation_recovery.py` — deterministic entitlement engine
- `aviation_io.py` — normalized ingestion, validation and lineage gating
- `recovery_truth.py` — conservative economic status summary
- `aviation_dossier.py` — review dossier and externalization gate
- `claim_package.py` — controlled claim-package renderer
- `claim_workflow.py` — auditable external lifecycle and settlement rules
- `workflow_case.py` — portable case state, schema/revision binding and artifact audit
- `executive_report.py` — mutually exclusive management buckets
- `operator_app.py` + `operator_ui/` — local assisted Recovery Control Room
- `cli.py` — command-line evaluator

## Operator console

Run locally:

```bash
python operator_app.py
```

Open:

```text
http://127.0.0.1:8080
```

The console supports cohort intake, deterministic evaluation, recovery-truth summaries, candidate drill-down, source lineage, lifecycle transitions, human-gated package generation, artifact hashing, settlement recording, executive reporting and portable case export/reopen.

It binds to localhost by default and does not create hidden customer persistence. Durable assisted-pilot state is the operator-exported case file, which is confidential work product and must be stored in the approved engagement location.

## Synthetic proof only

Core synthetic pilot:

```bash
python cli.py examples/pilot.json --output evaluated.json --report executive.md
```

TAP-shaped synthetic demo:

```bash
python cli.py examples/tap_synthetic_demo.json --output tap_demo_evaluated.json --report tap_demo_executive.md
```

The TAP-shaped scenario is **100% synthetic**. It must never be represented as TAP data, discovered leakage or a claim about TAP.

Expected synthetic demo truth:

- claim-ready: **EUR 1,260,000**
- review-required: **EUR 187,500**
- blocked potential: **EUR 200,000**
- settled/recovered: **EUR 0**

## Tests

```bash
python -m unittest discover -s tests -v
```

The suite covers recovery calculations, ingestion, evidence/lineage gates, dossier externalization, claim packages, lifecycle truth, settlement invariants, executive reporting, portable cases, operator-console behavior, landing-page truth, canonical launch-offer consistency and the current no-real-outreach execution boundary.

## Commercial preparation under the hold

Allowed now:

- public-source account research;
- private buyer briefs and route mapping;
- unsent proposals, emails, videos and meeting material;
- synthetic demonstrations;
- website/DNS/mail infrastructure work that does not message a real person;
- inbound monitoring and response drafting without sending.

Not authorized now:

- email, LinkedIn, contact-form or other outbound message to a real person or organization;
- real-recipient delivery tests;
- automated sequence enrollment that can transmit a message;
- external claim submission or counterparty communication.

## Remaining external gates

These are factual/operational gates, not reasons to rebuild the recovery engine:

- publish and verify `aervind.com` before claiming the public site is live;
- complete Primitive custom-domain DNS verification before claiming branded mail is DNS-ready;
- keep real-recipient mail testing disabled while the outreach hold is active;
- verify the real Portuguese professional activity classification before first paid delivery;
- verify customer-specific VAT/invoicing and supplier requirements before signature/invoice;
- agree confidentiality/data-transfer controls before receiving real airline evidence;
- obtain a real paid cohort only after real commercial activity is explicitly authorized.

## Deliberate scale boundary

Do not delay a first paid assisted engagement for self-service SaaS features. Multi-tenant persistence, SSO/RBAC, deep ERP/M&E integrations, automated billing and formal external security assurance remain post-pilot / buyer-driven unless a real procurement requirement makes one necessary.

Do not invent customers, recoveries, contracts, payments, external submissions, certifications or market proof.
