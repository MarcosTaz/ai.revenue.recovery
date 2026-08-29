# Recovery Radar — Pilot Start Here

Status: `T1 PILOT CAPABLE / T2 MEASUREMENT READY / REAL CASE NOT RUN`

This is the shortest supported path. Do not invent a parallel process.

## 1. Qualify one closed historical case

Use `PILOT_ACQUISITION.md`, `PILOT_ACCOUNT_SHORTLIST.md` and `PILOT_ROUTING_MATRIX.md`.

Current **T2 measurement-quality** order:

1. Dauch / former AAM — closed e-Beam cancellation claim with a known public settlement event;
2. Dee Zee / BrightDrop — strong supplier/program/industrialization link **only if** an authorized internal historical outcome exists;
3. Magna — one specifically closed North American EV cancellation/reduction recovery case;
4. Dana — one closed customer-cancelled / severe-volume-decline EV case, especially useful for zero/partial-recovery falsification.

Do not confuse case fit with routing fit. Do not infer supplier exposure from an OEM cancellation alone.

## 2. Commercial test

Use `PILOT_OFFER.md`.

Current hypothesis only:

**€4,500 ex VAT fixed scope / one historical case.**

This is not validated WTP. A free pilot is learning-only.

External messages are drafted in `PILOT_OUTREACH_DRAFTS.md` but remain **NOT SENT / OWNER AUTHORIZATION REQUIRED**.

## 3. Record human authorization before confidential processing

Use `PILOT_AUTHORIZATION_RECORD.md` and the participant's actual controlled approval process.

The application cannot prove that an approver had authority. Any authorization reference later stored in a scorecard remains `RECORDED_NOT_INDEPENDENTLY_VERIFIED`.

## 4. Request only the minimum authorized data

Use `PILOT_DATA_REQUEST.md` and `PILOT_DATA_HANDLING.md`.

No ERP write access, no live customer communication, no unrelated customer/program data.

## 5. Normalize the case

Copy:

`examples/pilot-bundle-template.json`

Keep stable aliases consistent. Preserve source currencies. Missing evidence stays missing; do not invent references.

The template is tested against the current parser.

## 6. Freeze the source scope before analysis/comparison

With an authenticated workspace token:

```text
recovery-radar scope-manifest \
  --db pilot.db \
  --bundle bundle.json \
  --output source-scope.json
```

Preserve both the returned `source_scope_sha256` and the exported artifact SHA-256. The manifest binds normalized economic inputs and concrete evidence-file hashes without embedding raw evidence bytes.

A scope hash proves identity, **not authorization or correctness**. See `PILOT_PROVENANCE.md`.

## 7. Run the assisted historical pilot

Follow `PILOT_RUNBOOK.md` exactly:

`bootstrap → issue distinct analyst/reviewer identities → source-scope freeze → import-bundle → independent evidence review → independent entitlement review → package → export → optional internal case`.

Stop on unresolved mixed currency, ownership, duplicate economics, evidence ambiguity, contract-version ambiguity, unsupported mitigation/prior reimbursement, or integrity/schema failure.

## 8. Prepare independent historical ground truth

Copy:

`examples/ground-truth-template.json`

It intentionally starts with:

- `case_origin = UNKNOWN`;
- `ground_truth_complete = false`;
- `provenance.authorization_reference = null`;
- `provenance.source_scope_sha256 = null`;
- `provenance.ground_truth_method = UNKNOWN`;
- no pre-populated line.

Change these only when externally supported. A caller-selected real-case label or authorization reference is not proof of authorization.

Use `GROUND_TRUTH_PROTOCOL.md` to distinguish `BLIND`, `ASSISTED` and `UNKNOWN` ground-truth preparation.

## 9. Produce the T2 measurement artifact

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

The scorecard measures FP/FN, state/currency/value error and supplied operational metrics. It records provenance metadata as non-authoritative and cannot promote T2, WTP, customer acceptance, settlement or recovered cash.

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