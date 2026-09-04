# AERVIND — Launch Acceptance Standard

AERVIND is not considered operationally ready merely because the entitlement engine passes tests or the landing page exists. The launch boundary is the combined state below.

## Product truth

Required:

- deterministic entitlement calculation;
- source-lineage gating;
- malformed/contradictory input fails conservatively;
- human review before claim package release;
- generated package remains `not_submitted` until a real external event exists;
- external workflow states require evidence references;
- verified settlement is the only recovered-value state;
- management buckets are mutually exclusive;
- portable case state binds to the evaluated cohort revision and schema version.

## First-offer truth

All canonical buyer-facing material must agree on:

- **Recovery Scan — EUR 9,500**;
- up to **5 aircraft and/or engines**;
- **1 primary entitlement family**;
- up to **12 months** of selected events;
- target **10 business days** after the complete agreed minimum dataset;
- **50% at engagement/scope confirmation, 50% at delivery**;
- no guarantee that recoverable value exists;
- no live ERP, M&E, lease-management or banking-system access required for the first scan.

Legacy first-offer ranges must not silently return to canonical buyer documents.

## Customer-data boundary

Before any real evidence is received:

- customer and scope are real and identified;
- confidentiality / transfer route is agreed;
- only minimum-necessary evidence is requested;
- no unrestricted customer credentials are accepted;
- portable case exports are treated as confidential work product;
- real customer data is never written to the public repository.

## Infrastructure boundary

Before AERVIND claims a public service is live:

- `aervind.com` routes to the intended static site over HTTPS;
- canonical host/redirect behavior is verified;
- branded mail DNS records pass before `@aervind.com` is called live;
- DNS verification is kept separate from real-recipient delivery testing;
- no paid infrastructure is added merely for appearance before proof requires it.

## Legal / supplier boundary

Before a first paid engagement:

- actual Portuguese professional activity is verified as covering the service;
- customer-specific VAT/invoicing treatment is verified;
- proposal, contract and invoice use the truthful supplier identity required by law;
- AERVIND is not represented as an incorporated company unless incorporation actually exists;
- no legal, audit, MRO, airworthiness or guaranteed-recovery claims are made.

## Current external-send boundary

`docs/REAL_OUTREACH_HOLD.md` is currently authoritative: **no real outbound message or real-recipient mail test is authorized** until the founder explicitly lifts that hold.

## Acceptance evidence

Repository acceptance is demonstrated by:

```bash
python -m unittest discover -s tests -v
```

The repository test suite includes launch-commercial consistency and no-send execution-boundary assertions in addition to the recovery engine, lifecycle, dossier, reporting, operator-console and site tests.
