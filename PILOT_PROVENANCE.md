# Recovery Radar — Historical Pilot Provenance Chain

Status: `T1/T2 OPERATING CONTROL`

Purpose: ensure a historical validation result can be reconstructed without allowing application metadata to manufacture authorization, independence or commercial truth.

## Required chain

`HUMAN AUTHORIZATION RECORD`
→ `NORMALIZED PILOT BUNDLE + CONCRETE EVIDENCE FILES`
→ `SOURCE-SCOPE MANIFEST`
→ `ATOMIC IMPORT`
→ `INDEPENDENT EVIDENCE / ENTITLEMENT REVIEW`
→ `CLAIM PACKAGE + PACKAGE HASH`
→ `FROZEN HUMAN GROUND TRUTH`
→ `T2 SCORECARD + SCORECARD HASH`.

## 1. Human authorization remains external truth

Use `PILOT_AUTHORIZATION_RECORD.md` as a checklist/reference template, but retain the actual participant approval in the controlled system/process required by the data owner.

Recovery Radar does not validate whether the approver had legal authority. A stored `authorization_reference` therefore means only:

`RECORDED_NOT_INDEPENDENTLY_VERIFIED`.

It cannot promote T2, WTP, customer acceptance or any recovery claim.

## 2. Freeze the normalized source scope before comparison

With an authenticated pilot workspace token:

```text
recovery-radar scope-manifest \
  --db pilot.db \
  --bundle bundle.json \
  --output source-scope.json
```

The manifest binds:

- event identity/type/date and expected/revised volumes;
- every normalized exposure identity, category, quantity, cost, currency, ownership, mitigation and prior-reimbursement field/reference;
- every entitlement identity, support state, documentary reference, cap and legal-review flag;
- evidence identity/scope/version/date/signature metadata;
- SHA-256 of the concrete evidence file bytes.

Raw evidence bytes are not embedded.

Changing a relevant economic value or evidence file changes `source_scope_sha256`.

The hash establishes identity of the modeled source scope. It does **not** prove completeness, correctness, ownership, authorization or legal admissibility.

## 3. Preserve ground-truth independence separately

The neutral `examples/ground-truth-template.json` records:

```json
{
  "provenance": {
    "authorization_reference": null,
    "source_scope_sha256": null,
    "ground_truth_method": "UNKNOWN"
  }
}
```

Allowed `ground_truth_method` values:

- `BLIND` — reviewer prepared/froze ground truth before seeing Recovery Radar first-pass output;
- `ASSISTED` — reviewer had exposure to Recovery Radar output or the reference required assisted adjudication;
- `UNKNOWN` — independence cannot be established.

These values are human-recorded metadata and remain `RECORDED_NOT_INDEPENDENTLY_VERIFIED` inside the application.

## 4. Bind provenance into the scorecard

`score-historical` carries the recorded provenance into the final scorecard and recomputes the final scorecard SHA-256 after provenance/classification metadata is added.

Therefore changing the authorization reference, source-scope hash or ground-truth method changes the final scorecard identity.

The scorecard continues to state:

- `terminal_promotion = NOT_INFERRED_FROM_SCORECARD`;
- WTP = `UNKNOWN_EXTERNAL` unless independently established outside this self-authored artifact;
- customer acceptance/recovered cash are not inferred.

## 5. Retain the minimum audit set

For every real/historical T2 candidate retain together:

1. exact Recovery Radar commit SHA;
2. external authorization/approval reference;
3. normalized bundle used for the run;
4. `source-scope.json` + source-scope SHA-256 and artifact SHA-256;
5. raw evidence files under the participant's approved controls;
6. independent evidence/entitlement review record;
7. deterministic claim-package export + SHA-256;
8. frozen ground-truth file + independently calculated file hash;
9. recorded blind/assisted/unknown method;
10. deterministic T2 scorecard + SHA-256;
11. known historical submitted/accepted/settled/paid observations when authorized;
12. unresolved uncertainty and any repair/rerun history.

## Stop conditions

Do not treat the run as T2-quality evidence when:

- authorization is absent/unclear;
- source scope changed after ground truth without a new manifest/rerun;
- ground truth was edited silently after seeing the score;
- the claimed blind method cannot be supported operationally;
- source/evidence hashes do not match the frozen run;
- material P0/P1 truth-integrity defects remain;
- historical outcome is being substituted for entitlement truth;
- a self-authored WTP note is being used as commercial validation.

The application preserves provenance; Factory/human review decides what that provenance actually proves.