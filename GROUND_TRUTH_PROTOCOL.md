# Recovery Radar — Independent Ground Truth Protocol

Status: `T2 VALIDATION CONTROL`

Purpose: prevent Recovery Radar's own output, a changed source dataset or self-reported metadata from becoming the reference used to score Recovery Radar.

## Primary rule

For an authorized historical case, establish the human reference **before the person creating the reference sees the Recovery Radar first-pass output whenever the historical record allows this**.

Never copy model-selected economic-loss IDs, dispositions, amounts, missing-evidence findings or claim lines into the human reference merely because the system produced them.

The neutral repository template is:

`examples/ground-truth-template.json`

It intentionally contains no pre-populated loss line and starts with `case_origin=UNKNOWN`, `ground_truth_complete=false`, no authorization/source-scope reference and `ground_truth_method=UNKNOWN`.

## Preferred sequence — blind benchmark

1. retain the real human/data-owner authorization outside the application;
2. normalize the authorized bundle and concrete evidence files;
3. run `scope-manifest` and freeze `source_scope_sha256` before product comparison;
4. give the human ground-truth reviewer the authorized historical source records and known historical outcome, but not the Recovery Radar first-pass result;
5. have the reviewer enumerate economic losses and assign disposition / source currency / expected amount where defensible;
6. record whether the reference is exhaustive enough for `ground_truth_complete=true`;
7. set `ground_truth_method=BLIND` only if the reviewer truly had no first-pass exposure;
8. record the frozen source-scope hash and, where supported, an external authorization reference in the ground-truth provenance block;
9. freeze/hash the human reference independently of Recovery Radar;
10. only then reveal/run the Recovery Radar result;
11. run `score-historical` against the frozen reference;
12. preserve the deterministic scorecard and hashes;
13. investigate differences without retroactively editing the original reference to make the product look correct.

If a reference error is discovered, preserve both versions and the reason for correction. Do not silently overwrite history.

## Source-scope binding

`source_scope_sha256` is not a decorative field.

When it is recorded in the ground-truth provenance block, `score-historical` reconstructs the current persisted normalized event/exposure/entitlement/evidence scope and compares the hashes. A mismatch fails closed with:

`SOURCE_SCOPE_SHA256_MISMATCH`

and no scorecard is written.

This prevents a reference frozen against dataset A from silently scoring dataset B.

The source-scope hash binds normalized economics and evidence-file content hashes. It proves identity of the modeled scope only. It does not prove authorization, completeness, correctness or legal admissibility.

See `PILOT_PROVENANCE.md` for the full chain.

## Provenance fields are not self-authenticating

The ground-truth file may record:

- `case_origin`;
- `provenance.authorization_reference`;
- `provenance.source_scope_sha256`;
- `provenance.ground_truth_method`.

Recovery Radar deliberately treats these as recorded metadata.

The scorecard marks caller-recorded case origin with:

`case_origin_status = RECORDED_NOT_INDEPENDENTLY_VERIFIED`.

An authorization reference is likewise recorded, not independently verified. The application cannot determine whether the named approver had legal authority.

A matching source-scope hash verifies dataset identity, not authorization.

## When blind ground truth is impossible

Sometimes the available human reviewer may already have seen the model output, or the historical file may not contain a pre-existing independent loss ledger.

In that case:

- use `ground_truth_method=ASSISTED` when that is known;
- use `UNKNOWN` when independence cannot be established;
- the scorecard may still be useful for adjudication;
- do **not** present FP/FN/value-error results as an unbiased product-accuracy benchmark;
- do not promote T2 solely from that case;
- prefer a second case with blind ground truth before making general accuracy claims.

The application records the method but does not independently verify it. Human Factory review owns the evidentiary interpretation.

## Ground-truth completeness

Set `ground_truth_complete=true` only if the reviewer has enough source coverage to treat unexpected modeled positive losses as genuine false-positive candidates.

Use `false` when:

- only selected known losses were reviewed;
- the historical file is incomplete;
- major source systems are missing;
- the reviewer cannot reasonably assert exhaustiveness.

An incomplete reference can identify some misses/errors but cannot prove that every unexpected modeled positive is false.

## Unknown truth

Use disposition `UNKNOWN` when the human record cannot defend a positive or negative answer.

`UNKNOWN` is not:

- a product success;
- a false positive;
- a false negative;
- a reason to manufacture a value estimate.

## Historical outcome is not identical to entitlement truth

Keep these facts separate:

- modeled claimability;
- human ground-truth view;
- amount submitted historically;
- amount accepted;
- settlement amount;
- amount actually paid/credited.

A commercial compromise can settle below a defensible claim; a paid amount does not prove that every claim line was legally correct; an unpaid amount does not prove there was no entitlement.

## WTP boundary

The T2 scorecard never validates willingness to pay.

`wtp_evidence_reference` is only a recorded external reference and remains `RECORDED_NOT_INDEPENDENTLY_VERIFIED` inside the application. `commercial_truth.wtp` stays `UNKNOWN_EXTERNAL`. WTP is promoted only by separate Factory review of real decision-maker evidence.

## Minimum evidence retained with a T2 result

Retain together:

- exact Recovery Radar commit SHA;
- external authorization/approval reference;
- authorized-case alias that does not expose unnecessary confidential data;
- normalized bundle;
- `source-scope.json` + source-scope and artifact SHA-256;
- raw evidence files under the participant's approved controls;
- frozen ground-truth file + its independently calculated file hash;
- recorded `BLIND / ASSISTED / UNKNOWN` method;
- deterministic claim-package export + SHA-256;
- deterministic T2 scorecard export + SHA-256;
- reviewer corrections and rationale;
- known historical submitted/accepted/settled/paid outcomes when authorized;
- unresolved uncertainty and any repair/rerun history.

## Promotion rule

One high synthetic score proves deterministic behavior only.

One assisted-adjudication historical score is useful evidence but is not enough for a general accuracy claim.

A scorecard cannot auto-promote T2 regardless of `case_origin`, authorization reference or apparent score.

`T2 — REAL-CASE VALIDATED` requires Factory review of at least one actually authorized historical/real case with sufficiently independent ground truth, source-scope integrity and no unresolved material truth-integrity defect. A second independent case is preferred before broader accuracy or market claims.