# Recovery Radar — Cancellation Claim Historical Pre-Audit Benchmark

Status: `BUYER-FACING DRAFT / NOT SENT / COMMERCIAL HYPOTHESIS`

## Before a cancellation claim goes to the customer, what will the auditor attack?

Recovery Radar is a supplier-side pre-audit for closed or historical customer program cancellations, terminated purchase orders and severe volume reductions.

It reconstructs the claim from source evidence and separates five things that are often mixed together in spreadsheets:

**economic exposure → recoverability basis → evidence quality → review uncertainty → actual settlement/payment.**

A large stranded cost does not automatically become a claim. A claim does not automatically become settlement. Settlement does not automatically become cash.

## First pilot: one closed historical case

Use one matter where the historical outcome is already known, so the test cannot influence a live customer dispute.

Good examples include stranded:

- raw material / E&O;
- WIP / finished goods;
- tooling;
- engineering / NRE;
- supplier commitments;
- dedicated capacity.

The first pilot requires **no ERP write access, no live system integration, and no customer/OEM communication**.

## What we test

Given the records that existed around the event, Recovery Radar asks:

- What economic exposure can actually be reconstructed from source records?
- Is ownership clear?
- What was mitigated, reused, resold, scrapped, cancelled, credited or already reimbursed?
- What contractual/commercial basis supports each recovery line?
- Which evidence is missing, ambiguous, wrong-scope or conflicting?
- Are there duplicate/double-counted economic losses?
- Are currencies being kept separate rather than added into a false total?
- Which lines can be supported, which require human review, and which should not be claimed?
- How does the pre-audit compare with independent historical ground truth and the known outcome?

## Deliverables

For one qualified historical case:

1. normalized event / exposure / entitlement / evidence map;
2. line-level calculation trace;
3. mitigation + prior-reimbursement reconciliation;
4. evidence and entitlement review states;
5. missing-evidence / ambiguity / duplicate-risk map;
6. structured pre-audit claim package;
7. deterministic export with SHA-256 integrity manifest;
8. historical validation scorecard measuring false positives, false negatives, state/currency/value error and reviewer corrections;
9. executive readout: matched, missed, overcalled, undercalled, evidence burden and next-use implications.

## Human review stays in the loop

Recovery Radar does **not** decide legal liability.

Contract interpretation, amendment precedence, ambiguous commercial terms, physical verification and negotiation remain human decisions where required.

The system deliberately fails closed instead of inventing certainty.

## Data boundary

The first pilot can run locally/offline in an operator-controlled environment.

Raw evidence files remain in the operator-controlled pilot directory; Recovery Radar persists normalized source records plus evidence metadata/content hashes, not raw evidence bytes.

The current local application does not claim SOC 2, production IAM or application-level encryption-at-rest. Confidential pilot storage therefore uses the participant/operator's approved local encryption and access controls.

See `PILOT_DATA_HANDLING.md` for the exact current boundary.

## Initial fixed-scope price hypothesis

**€4,500 ex VAT — one historical program/cancellation case.**

Assumed scope:

- one event/program;
- one primary currency, or separable currency groups;
- up to 1,000 economic exposure lines;
- up to 100 evidence records;
- one source analyst path + one independent reviewer path;
- remote/local review only;
- no custom connector or live customer contact;
- one package + scorecard + executive readout.

This is the current commercial test price, not validated market pricing.

## What success means

A successful first pilot does **not** mean “the model found more money.”

Success means we can measure whether the process:

- reconstructs the right exposure;
- avoids unsupported or duplicate claims;
- surfaces the right missing evidence;
- preserves uncertainty instead of hiding it;
- reduces reviewer effort or improves completeness;
- produces a traceable package that can survive internal scrutiny;
- is useful enough that the supplier would use it again.

Willingness to pay remains a separate commercial fact and is only evidenced by an actual budget/price action.

## What we need to start

Only after participation is authorized:

- one closed/historical case;
- event notice/release/PO/forecast evidence;
- program-linked cost/exposure records;
- relevant contractual/commercial basis;
- mitigation/prior-reimbursement records where applicable;
- a knowledgeable independent reviewer;
- original claim/outcome data where available.

The exact minimum request is in `PILOT_DATA_REQUEST.md`.

## Current product state

`T1 — PILOT CAPABLE` for a controlled assisted historical pilot.

`T2 — REAL-CASE VALIDATED` has **not** been reached because no authorized real supplier case has yet been run.

No customer, recovery or revenue claim is made by this one-pager.
