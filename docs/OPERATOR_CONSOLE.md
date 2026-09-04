# AERVIND Operator Console

Status: **READY FOR ASSISTED PILOT USE**

The Operator Console is the controlled browser workspace for AERVIND assisted Recovery Scans. It sits directly on the deterministic recovery engine and lifecycle controls. It is an operator tool for a professional engagement, not a public multi-tenant SaaS product.

## What the customer must provide

The first engagement does **not** require live ERP, M&E, lease-management, banking or airline-system access.

The customer supplies a bounded evidence cohort through an agreed transfer/storage route. Typical source material includes:

- governing lease and amendments;
- maintenance reserve / contribution statements;
- maintenance-event evidence, invoices and workscope;
- prior claim/submission records;
- prior reimbursement / settlement records;
- any other evidence specifically required by the governing entitlement terms.

PDFs, spreadsheets and controlled exports are sufficient for the first Recovery Scan. Source files stay in the engagement-approved evidence repository; the console works with a normalized JSON cohort and source references.

## Canonical operating chain

`source cohort -> deterministic evaluation -> blockers / review -> human review -> claim_ready -> claim package -> real external submission -> counterparty process -> verified settlement -> executive closeout`

Economic status and lifecycle are separate controls.

Economic status:

`blocked / review_required / claim_ready / zero_entitlement`

External lifecycle:

`detected -> reviewing -> claim_ready -> submitted -> acknowledged / disputed / approved / rejected -> settled`

Only evidence-backed settlement is recovered value.

## Start

No third-party Python packages are required.

```bash
python operator_app.py
```

Then open:

```text
http://127.0.0.1:8080
```

The server binds to localhost by default. Do not expose it publicly without an engagement-specific deployment and security design.

## Recovery Scan workflow

1. Load the normalized customer cohort or the explicitly synthetic demo.
2. Evaluate the cohort through the canonical `aviation_io.evaluate_payload` path.
3. Review management recovery truth and candidate ranking.
4. Open each candidate and inspect blockers, warnings, evidence, source lineage and calculation trace.
5. Start the auditable lifecycle at `detected -> reviewing`.
6. Move a candidate to workflow `claim_ready` only when the economic evaluator and source-lineage gate still pass.
7. Generate a claim package only from workflow `claim_ready` and after explicit human confirmation.
8. Store/export the portable AERVIND case file in the approved engagement location.
9. Submit externally through the customer-approved real channel outside this console.
10. Record `submitted` only after the real submission exists and capture its external reference.
11. Record acknowledgement, dispute, approval or rejection only from real counterparty evidence.
12. Record `settled` only with cash, credit memo, refund or contractually valid offset evidence.
13. Export the final executive report and case audit file.

## Portable case file

The console has no hidden server-side persistence. Durable assisted-pilot state is carried in an operator-exported AERVIND case file.

A case file contains:

- the normalized cohort;
- a SHA-256 binding to the reviewed cohort revision;
- claim lifecycle records;
- append-only audit events;
- external references for submission/counterparty events;
- settlement evidence reference and verified amount;
- generated claim-package artifact hashes.

The case file can be reopened in the console to resume the engagement.

### Revision integrity

Before release, a reviewing case may be rebound to a corrected/revised cohort and then re-reviewed.

Once any claim reaches a released lifecycle state (`claim_ready`, submitted, counterparty process or settled), the existing workflow is bound to that cohort digest. Silent source changes are rejected. A material source revision then requires a new reviewed case revision rather than rewriting the prior audit history.

## Claim-package integrity

The claim-package action:

- requires workflow state `claim_ready`;
- re-evaluates the current cohort from source inputs;
- re-checks blockers and source-lineage gaps;
- requires an accountable human actor;
- renders the canonical external package;
- records SHA-256 of the generated artifact in the case file;
- always returns `submission_status = not_submitted`.

Package generation never emails, uploads or submits the claim to a lessor or any external system.

## External lifecycle evidence

The console distinguishes internal review decisions from real external events.

- `submitted` requires an external submission evidence/reference identifier.
- acknowledgement, dispute, approval and external rejection require the corresponding counterparty evidence/reference.
- `settled` requires positive settlement evidence, currency, amount and reference.
- verified settlement cannot exceed the currently asserted claim amount; a larger settlement requires the claim economics to be revised and re-reviewed instead of silently inflating recovery.

Every transition records actor, reason and timezone-aware timestamp.

## Management truth

The executive report uses mutually exclusive economic buckets:

- verified settled recovery;
- claim-ready, not yet submitted;
- submitted / acknowledged / disputed / approved, unsettled;
- workflow review / rejected;
- review-required pipeline;
- blocked potential.

One candidate cannot appear simultaneously as settled recovery and claim-ready or unsettled external value.

## Security / data handling

The standard console:

- binds to `127.0.0.1`;
- processes request bodies in memory;
- does not log request bodies;
- does not write submitted cohorts to disk;
- emits `Cache-Control: no-store`;
- uses restrictive CSP, frame, referrer, cross-origin and browser permissions headers;
- has no analytics, third-party JS, advertising or telemetry;
- limits API bodies to 2 MB;
- never treats the browser console as the evidence repository.

The exported case file is **not encrypted by the application**. It may contain customer-normalized financial/evidence metadata and must therefore be stored/transferred only using the engagement-approved secure location.

## Synthetic demonstration

`Load synthetic example` reads `examples/pilot.json`.

It is clearly synthetic and must never be described as airline data, discovered leakage or proof that a target account missed an entitlement.

## Real-data acceptance gate

Before the first real cohort is loaded:

- signed commercial/confidentiality terms exist;
- customer legal entity and scope are known;
- assets/events/entitlement families are bounded;
- approved data-transfer and storage route is known;
- governing lease/amendment set is available;
- accountable AERVIND reviewer is named;
- customer owner/reviewer is known;
- source evidence is indexed with stable references;
- case exports have an approved storage location;
- the operator understands that external submission remains a separate real-world action.

## Deliberate non-features before scale

- no public customer login;
- no multi-tenancy;
- no SSO/MFA;
- no cloud persistence;
- no automatic legal interpretation;
- no direct airline-system integration;
- no automatic claim submission;
- no automatic settlement recognition;
- no hidden synchronization.

Add persistence, tenancy, SSO, document extraction or deep integrations only when a real paid buyer requires them or repeatable pilot evidence justifies the scale investment.
