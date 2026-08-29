# Recovery Radar — Independent Ground Truth Protocol

Status: `T2 VALIDATION CONTROL`

Purpose: prevent Recovery Radar's own output from becoming the reference used to score Recovery Radar.

## Primary rule

For an authorized historical case, establish the human reference **before the person creating the reference sees the Recovery Radar first-pass output whenever the historical record allows this**.

Never copy model-selected economic-loss IDs, dispositions, amounts, missing-evidence findings or claim lines into the human reference merely because the system produced them.

The neutral repository template is:

`examples/ground-truth-template.json`

It intentionally contains no pre-populated loss line.

## Preferred sequence — blind benchmark

1. authorize the historical case and freeze the source dataset;
2. give the human ground-truth reviewer the historical source records and known historical outcome, but not the Recovery Radar result;
3. have the reviewer enumerate economic losses and assign disposition / source currency / expected amount where defensible;
4. record whether the reference is exhaustive enough for `ground_truth_complete=true`;
5. freeze/hash the human reference outside the Recovery Radar scorecard path;
6. only then reveal/run the Recovery Radar result;
7. run `score-historical` against the frozen reference;
8. investigate differences without retroactively editing the original reference to make the product look correct.

If a reference error is discovered, preserve both versions and the reason for correction. Do not silently overwrite history.

## When blind ground truth is impossible

Sometimes the available human reviewer may already have seen the model output, or the historical file may not contain a pre-existing independent loss ledger.

In that case:

- the scorecard may still be useful for assisted adjudication;
- record outside the scorecard that the reference was not blind;
- do **not** present FP/FN/value-error results as an unbiased product-accuracy benchmark;
- do not promote T2 solely from that case;
- prefer a second case with blind ground truth before making general accuracy claims.

The application currently does not infer this independence automatically. Human Factory review owns this classification.

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

`wtp_evidence_reference` is only a recorded external reference and remains `RECORDED_NOT_INDEPENDENTLY_VERIFIED` inside the application. WTP is promoted only by separate Factory review of real decision-maker evidence.

## Minimum evidence retained with a T2 result

Retain together:

- exact Recovery Radar commit SHA;
- authorized-case identifier that does not expose unnecessary confidential data;
- frozen source-data scope;
- frozen ground-truth file + its independent hash;
- whether ground truth was blind or assisted;
- deterministic claim-package export + SHA-256;
- deterministic T2 scorecard export + SHA-256;
- reviewer corrections and rationale;
- known historical submitted/accepted/settled/paid outcomes when authorized;
- unresolved uncertainty.

## Promotion rule

One high synthetic score proves deterministic behavior only.

One assisted-adjudication historical score is useful evidence but is not enough for a general accuracy claim.

`T2 — REAL-CASE VALIDATED` requires Factory review of at least one authorized historical/real case with sufficiently independent ground truth and no unresolved material truth-integrity defect. A second independent case is preferred before broader accuracy or market claims.
