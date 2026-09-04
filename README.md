# GovMargin

Government Contract Earned-Revenue & Margin Recovery.

GovMargin is a contractor-side, evidence-first economic-assurance system for U.S. federal contracts. It reconstructs supported contract economics, compares them with cumulative billings and verified payments, and preserves both contractor-side receivables and Government-side payables without incentive bias.

## Current thesis

Status: **NARROWED BUILD / PILOT-PREP — 79/100**.

The economic mechanism is real, but the competitive white space is narrower than originally assumed. Deltek Costpoint already supports cumulative claimed-versus-billed analysis, over/under-billing adjustment identification and final billing/payment closeout reporting.

Therefore the surviving first wedge is not generic billing reconciliation. It is:

> **Independent cross-system historical final-rate / closeout economic assurance for cost-reimbursement / CPFF contracts where the full history is fragmented across ERPs, migrations, manual invoices, acquired entities, spreadsheets, rate agreements and payment records.**

Real pilots must prove incremental value over the contractor's ordinary ERP + GovCon accountant workflow.

## Initial executable scope

Current deterministic/review-gated coverage includes:

- contract-type applicability guard for the CPFF/cost-reimbursement wedge;
- FAR 52.216-7 final-rate update / completion voucher / final-payment rule anchors;
- FAR 52.232-20 / 52.232-22 funding safeguards;
- settled indirect-rate true-up;
- direct cost / ODC checks;
- multi-pool allocation calculation;
- fee/ceiling/funding controls;
- final-voucher and final-payment reconciliation;
- invoice/payment reconciliation;
- tenant-scoped normalized import;
- evidence SHA-256 lineage;
- role authorization + verified-session reference boundary;
- human review and optional independent multi-approval policy;
- recovery/payable/unresolved evidence packs;
- tamper-evident audit-chain primitives;
- raw-evidence admission contract;
- sensitive-log redaction;
- synthetic A–Z and red-team tests;
- browser true-up/funding/human-review demonstration;
- deterministic pilot unit economics;
- continuous earned/billed/paid assurance snapshot;
- PE/M&A economic rights-and-exposure schedule.

## Non-negotiable safety

- No invented allowability, allocability, entitlement, rates, funding, ceilings or receivables.
- Positive and negative variances are treated symmetrically.
- Contract applicability and source version must be evidenced.
- Funding/notice conditions never become automatic recovery rights.
- A proposed or provisional rate is not a settled-final-rate entitlement.
- Legal/accounting judgment is routed to qualified review.
- Financial arithmetic is deterministic and reproducible.
- Real customer confidential data is prohibited from the current repository/synthetic web surface.
- No automatic claim filing or representation.
- No automatic merge.

## Commercial posture

Design-partner hypothesis:

- one entity;
- up to five cost-reimbursement / CPFF contracts/orders;
- up to two completed fiscal years;
- explicit fragmented-history / cross-system trigger;
- **$7,500 fixed-fee pilot hypothesis**.

Success-linked compensation is disabled pending qualified legal/accounting review. No paid customer, real contractor dataset, collected recovery, validated average recovery percentage, signed partner channel or validated CAC/sales cycle exists yet.

## Gate 10

GovMargin is **not yet pilot-ready for confidential real customer data** because production identity, encrypted persistence, actual file scanning/parser isolation, persistent audit storage, backup/deletion controls and a dedicated deployment project remain incomplete or externally blocked.

The current web product is a synthetic/pre-pilot engineering surface.

## Key project truth

- `VALIDATION.md` — regulatory, competition and commercial validation.
- `COMPETITION.md` — stronger Costpoint/substitute kill-test.
- `PILOT_READINESS.md` — Gate-10 controls and blockers.
- `LEGAL_BOUNDARY.md` — fixed-fee launch boundary.
- `PILOT_OFFER.md` — narrowed design-partner offer.
- `ASSISTED_PILOT_CHECKLIST.md` — controlled real-pilot input/review path.
- `UNIT_ECONOMICS.md` — modeled delivery guardrails.
- `PARTNER_CHANNEL.md` — accounting/legal partner-validation targets.
- `CUSTOMER_DATA_POLICY.md` — pre-production data prohibition/handling rules.
- `BATON.md` — exact continuity state.
