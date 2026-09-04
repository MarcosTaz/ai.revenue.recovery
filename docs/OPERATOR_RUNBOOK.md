# Aviation Recovery — Assisted Operator Runbook

## Objective

Run a bounded recovery engagement from intake to verified settlement without overstating contractual certainty or recovered value.

## Phase 1 — Scope lock

Record:

- customer entity;
- in-scope leases/assets/events;
- entitlement families;
- review period;
- governing currency assumptions;
- customer owners/reviewers;
- agreed output and commercial terms.

Do not widen scope silently when unrelated opportunities are discovered. Add them to a separate opportunity register for customer approval.

## Phase 2 — Source inventory

Create an evidence index for every received document/export. Preserve original names and assign stable internal IDs. Mark duplicates and superseded versions; do not overwrite source history.

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

Do not automatically include internal red-team commentary.

## Phase 8 — Submission and counterparty tracking

Track exact timestamps and evidence for:

- submitted;
- acknowledged;
- disputed;
- approved;
- rejected;
- reopened/reviewing.

Each transition requires actor and reason in the audit trail.

## Phase 9 — Settlement truth

`approved` is not `settled`.

Move to `settled` only when there is evidence of cash receipt, credit memo, refund or contractually valid offset. Record settlement amount, currency and evidence reference.

## Phase 10 — Executive closeout

Report separately:

- verified settled recovery;
- claim-ready value not yet submitted;
- submitted/approved but unsettled value;
- review-required pipeline;
- blocked potential with reasons;
- rejected/zero-entitlement candidates;
- upcoming contractual deadlines;
- unresolved evidence gaps.

Never add blocked potential to verified recovery.

## Quality stop conditions

Stop external release for a specific claim — while continuing work on other claims — when:

- governing contract version is unknown;
- required evidence is missing;
- calculation cannot be reproduced;
- duplicate/prior recovery is unresolved;
- time-bar status is unknown;
- asset/component mapping is inconsistent;
- currency normalization lacks a contractual or approved basis;
- reviewer has not approved externalization.

A blocked claim must not block the rest of the portfolio workflow.