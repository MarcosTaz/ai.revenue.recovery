# AERVIND — Assisted Operator Runbook

## Objective

Run a bounded Recovery Scan from intake to verified settlement without overstating contractual certainty, counterparty state or recovered value.

## Phase 0 — Controlled workstation

Run the Operator Console only on the controlled operator workstation:

```bash
python operator_app.py
```

Use `http://127.0.0.1:8080`. The console is loopback-only by design.

Operating rules:

- do not expose the console through a public tunnel, reverse proxy or shared LAN bind;
- do not paste unrestricted credentials, passwords, API keys or unrelated customer data into a cohort;
- source documents remain in the engagement-approved repository;
- the console processes the normalized cohort in memory;
- durable workflow state is the portable AERVIND case JSON downloaded by the operator;
- every successful lifecycle transition and claim-package generation triggers a validated case-checkpoint download;
- keep the latest checkpoint in the approved engagement storage location;
- if the checkpoint warning appears, use **Export case file** before closing the browser;
- the browser does not silently persist the customer cohort in localStorage/IndexedDB.

The portable JSON trail is validated and revision-bound, but it is not a cryptographically immutable archive and is not application-encrypted. Store it accordingly.

## Phase 1 — Scope lock

Record:

- customer entity;
- in-scope leases/assets/events;
- entitlement family;
- review period;
- governing currency assumptions;
- customer owners/reviewers;
- agreed output and commercial terms.

For the canonical first Recovery Scan, keep the agreed scope within up to 5 aircraft/engines, one primary entitlement family and up to 12 months of selected events unless a separately executed scope says otherwise.

Do not widen scope silently when unrelated opportunities are discovered. Add them to a separate opportunity register for customer approval.

## Phase 2 — Source inventory

Create an evidence index for every received document/export. Preserve original names and assign stable internal IDs. Mark duplicates and superseded versions; do not overwrite source history.

Reject or correct before evaluation:

- impossible dates;
- malformed evidence references;
- duplicate evidence IDs within a claim;
- non-finite numbers such as NaN or Infinity;
- invalid currency codes;
- arrays/objects in the wrong input fields.

## Phase 3 — Contract reconstruction

For every candidate:

1. identify governing lease and amendment version;
2. map entitlement trigger;
3. capture calculation formula and parameters;
4. capture exclusions, caps, floors, deductibles and escalation;
5. capture claim deadline and notice mechanics;
6. capture required evidence and approvals;
7. store source references for each material rule.

Unknown terms remain unknown. Do not convert them into assumed defaults.

## Phase 4 — Event / finance reconciliation

Match the maintenance event to technical and financial evidence. Reconcile:

- eligible cost;
- excluded costs;
- fund/contribution balance;
- prior claims;
- prior settlements;
- supplier/warranty credits where contractually relevant;
- deadlines.

Run the deterministic evaluator only after the input set is explicit.

## Phase 5 — Red-team

For each positive candidate, actively attempt to disprove it using the Claim Dossier red-team checklist. Record why the candidate survives or fails.

## Phase 6 — Human review

Reviewer outcomes:

- reject candidate;
- request evidence;
- request contract interpretation;
- accept economic calculation but hold externalization;
- approve claim-ready status.

A claim moves to `claim_ready` only after both the economic evaluator and source-lineage gate pass.

## Phase 7 — Claim package

Generate the external package with:

- concise claim cover summary;
- governing clause references;
- calculation schedule;
- required supporting evidence;
- submission method and deadline.

Package generation is a **local artifact action only**. The package is re-evaluated, SHA-256 hashed into the case audit and remains `not_submitted`. The console does not email, upload or transmit it.

Do not automatically include internal red-team commentary.

## Phase 8 — Submission and counterparty tracking

Under the current founder hold, **do not send or submit anything to a real person or organization**. Prepared packages and workflow states remain internal until that hold is explicitly lifted.

When real external activity is later authorized, record only events that actually happened, with exact evidence for:

- submitted;
- acknowledged;
- disputed;
- approved;
- rejected;
- reopened/reviewing.

Each transition requires actor and reason. External counterparty states require an external evidence/reference identifier where the workflow demands it.

The management `counterparty process` bucket carries AERVIND's **asserted unsettled amount**. A lifecycle label such as `approved` does not by itself prove a separately measured approved amount.

## Phase 9 — Settlement truth

`approved` is not `settled`.

Move to `settled` only when there is evidence of cash receipt, credit memo, refund or contractually valid offset. Record settlement amount, currency and evidence reference.

Settlement value must be positive, finite, in the claim currency and cannot exceed the asserted recovery amount in the current case revision.

## Phase 10 — Executive closeout

Report separately:

- verified settled recovery;
- claim-ready value not yet submitted;
- asserted value in the counterparty process, still unsettled;
- workflow review/rejected value;
- review-required pipeline;
- blocked potential with reasons;
- rejected/zero-entitlement candidates;
- upcoming contractual deadlines;
- unresolved evidence gaps.

Never add blocked potential or unsettled counterparty value to verified recovery.

## Case close / handover

Before closing the working session:

1. confirm the latest lifecycle/package action produced a downloaded checkpoint;
2. manually export a final case file as an additional closeout checkpoint;
3. reopen that exported case in the console and confirm the cohort digest, lifecycle and artifact counts;
4. store the final case file in the approved confidential location;
5. store generated claim/report artifacts with the same case revision context;
6. do not place real customer evidence or case files in the public GitHub repository.

## Quality stop conditions

Stop external release for a specific claim — while continuing work on other claims — when:

- governing contract version is unknown;
- required evidence is missing;
- calculation cannot be reproduced;
- duplicate/prior recovery is unresolved;
- time-bar status is unknown;
- asset/component mapping is inconsistent;
- currency normalization lacks a contractual or approved basis;
- reviewer has not approved externalization;
- the current cohort no longer matches the released workflow revision;
- the latest durable case checkpoint cannot be preserved.

A blocked claim must not block the rest of the portfolio workflow.
