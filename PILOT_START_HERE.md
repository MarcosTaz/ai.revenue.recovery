# Recovery Radar — Pilot Start Here

Status: `T1 PILOT CAPABLE / T2 MEASUREMENT READY / REAL CASE NOT RUN`

This is the shortest supported path. Do not invent a parallel process.

## 1. Qualify one closed historical case

Use `PILOT_ACQUISITION.md`.

Best current order:

1. Dauch / former AAM — closed e-Beam cancellation claim;
2. Magna — closed North American EV cancellation/reduction recovery case;
3. Dana — closed customer-cancelled / severe-volume-decline EV program.

Do not infer supplier exposure from an OEM cancellation alone.

## 2. Commercial test

Use `PILOT_OFFER.md`.

Current hypothesis only:

**€4,500 ex VAT fixed scope / one historical case.**

This is not validated WTP. A free pilot is learning-only.

External messages are drafted in `PILOT_OUTREACH_DRAFTS.md` but remain **NOT SENT / OWNER AUTHORIZATION REQUIRED**.

## 3. Request only the minimum authorized data

Use `PILOT_DATA_REQUEST.md`.

No ERP write access, no live customer communication, no unrelated customer/program data.

## 4. Normalize the case

Copy:

`examples/pilot-bundle-template.json`

Keep stable aliases consistent. Preserve source currencies. Missing evidence stays missing; do not invent references.

The template is tested against the current parser.

## 5. Run the assisted historical pilot

Follow `PILOT_RUNBOOK.md` exactly:

`bootstrap → issue distinct analyst/reviewer identities → import-bundle → independent evidence review → independent entitlement review → package → export → optional internal case`.

Stop on unresolved mixed currency, ownership, duplicate economics, evidence ambiguity, contract-version ambiguity, unsupported mitigation/prior reimbursement, or integrity/schema failure.

## 6. Prepare independent historical ground truth

Copy:

`examples/ground-truth-template.json`

It intentionally starts with:

- `case_origin = UNKNOWN`;
- `ground_truth_complete = false`;
- line disposition = `UNKNOWN`.

Change these only when independently supported. A caller-selected real-case label is not proof of authorization.

## 7. Produce the T2 measurement artifact

Run:

```text
recovery-radar score-historical \
  --db pilot.db \
  --event-id EV-001 \
  --supplier-id SUP-001 \
  --ground-truth ground-truth.json \
  --output t2-scorecard.json
```

Preserve the SHA-256 manifest.

The scorecard measures FP/FN, state/currency/value error and supplied operational metrics. It cannot promote T2, WTP, customer acceptance, settlement or recovered cash.

## Terminal decision

`T2 — REAL-CASE VALIDATED` is a Factory evidence decision after an authorized historical/real case is reviewed.

Any material truth-integrity failure becomes ACTIVE repair before promotion.

## External-action boundary

Until explicitly authorized, do not:

- send outreach;
- submit contact forms;
- request confidential files;
- submit a claim;
- contact an OEM/customer;
- negotiate or settle;
- spend money;
- deploy publicly;
- merge to `main`.
