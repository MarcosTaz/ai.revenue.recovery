# Recovery Radar — Controlled Historical Pilot Runbook

## Purpose

Run one authorized historical supplier cancellation / severe-volume-reduction case through Recovery Radar without influencing a live claim or pretending the software is a legal decision-maker.

T1 scope is intentionally assisted:

`AUTHORIZED HISTORICAL CASE`
→ `NORMALIZE BUNDLE`
→ `ATOMIC IMPORT`
→ `INDEPENDENT REVIEW`
→ `ANALYZE`
→ `MISSING-EVIDENCE ACTIONS`
→ `PACKAGE`
→ `DETERMINISTIC EXPORT`
→ `OPTIONAL INTERNAL CASE`
→ `COMPARE WITH HUMAN / KNOWN OUTCOME`.

No external submission, negotiation, settlement instruction or customer/OEM communication is part of this runbook.

## Roles

Use distinct human/operator identities:

- `ADMIN`: workspace/key administration. May also perform analyst work, but must not act as the independent reviewer of source records they created.
- `ANALYST`: normalizes and imports event/exposure/entitlement/evidence source records; may create internal claim cases after gates pass.
- `REVIEWER`: independently verifies or rejects individual evidence documents and entitlement interpretations. Cannot source-write, create claims, submit, settle or record payment.

The source creator and reviewer must have different `actor_id` values. Separate keys with the same actor identity do not satisfy independence.

## Data authorization boundary

Before import, record outside the application that the operator is authorized to use the historical case data.

Recovery Radar's pilot registry stores structured source records plus evidence metadata/content hashes. Raw evidence file bytes remain in the operator-controlled pilot directory and are not persisted into the Recovery Radar evidence registry.

Do not import:

- data outside the authorized case scope;
- credentials/secrets embedded in evidence files unless explicitly required and authorized;
- live customer communication for automated sending;
- information that the operator cannot lawfully process for the pilot.

## Local setup

Install the package in an isolated Python environment from the exact branch/commit chosen for the pilot.

The operator CLI is exposed as:

```text
recovery-radar
```

Authenticated commands read the API token from:

```text
RECOVERY_RADAR_TOKEN
```

Do not place long-lived API secrets inside the pilot bundle or commit them to Git.

## 1. Bootstrap workspace

```text
recovery-radar bootstrap \
  --db pilot.db \
  --workspace PILOT-001 \
  --name "Historical Supplier Pilot" \
  --actor owner
```

The bootstrap secret is returned once. Store it using the operator's normal secret-management controls.

## 2. Issue distinct analyst and reviewer keys

Set `RECOVERY_RADAR_TOKEN` to the ADMIN token, then issue:

```text
recovery-radar issue-key --db pilot.db --actor analyst-1 --role ANALYST
recovery-radar issue-key --db pilot.db --actor reviewer-1 --role REVIEWER
```

The two actor IDs must remain distinct.

## 3. Prepare the normalized bundle

Use format:

```text
RECOVERY_RADAR_PILOT_BUNDLE_V1
```

The bundle represents exactly one modeled event plus its exposure lines, entitlement interpretations and available evidence-file references.

Important truth rules:

- missing documentary references may remain empty/null where supported by the schema; do not invent them to satisfy the importer;
- monetary quantities must remain in their source currency;
- do not pre-convert mixed currencies to manufacture a combined total;
- `support_state=SUPPORTED` is still analyst-normalized input and does not become verified entitlement until reviewer approval;
- evidence hashes are derived from referenced file bytes by the loader; do not manufacture hashes;
- if a source is genuinely absent, leave the absence explicit so the missing-evidence engine can report it.

## 4. Back up before import when reusing an existing workspace

For a fresh pilot DB this is optional. For any reused DB, create and verify a backup using the tested Storage backup path before importing new truth.

Do not continue if backup verification fails.

## 5. Atomic import

Set `RECOVERY_RADAR_TOKEN` to the ANALYST token:

```text
recovery-radar import-bundle --db pilot.db --bundle bundle.json
```

Expected boundary:

- event/exposure/entitlement/evidence metadata + audit events commit atomically;
- exact retry is idempotent;
- any conflict/interruption rolls the new bundle transaction back;
- successful import returns `verification_state=REVIEW_REQUIRED`.

Import success is not claim readiness.

## 6. Independent evidence review

Set `RECOVERY_RADAR_TOKEN` to the REVIEWER token.

Review documents individually:

```text
recovery-radar review-evidence \
  --db pilot.db \
  --document-id D-001 \
  --state VERIFIED \
  --note "Matched source file to case/customer/program and supporting record"
```

Use `REJECTED` whenever identity, scope, signature/confirmation, ambiguity or substance is not acceptable for the modeled use.

Do not bulk-verify merely because files were imported.

## 7. Independent entitlement review

Review each structured entitlement interpretation separately:

```text
recovery-radar review-entitlement \
  --db pilot.db \
  --entitlement-id ENT-001 \
  --state VERIFIED \
  --note "Commercial/legal reviewer accepts this structured interpretation for pilot analysis"
```

A later or competing contract version does not automatically supersede another. If precedence is ambiguous, keep/revert the interpretation to review/rejected outside the claimable path.

## 8. Build package

Set `RECOVERY_RADAR_TOKEN` to an authorized ANALYST/ADMIN token:

```text
recovery-radar package \
  --db pilot.db \
  --event-id EV-001 \
  --supplier-id SUP-001
```

Inspect at minimum:

- `executive_summary`;
- `claim_line_items`;
- `exposure_by_category`;
- `entitlement_basis` and review states;
- `calculation_trace`;
- mitigation and prior compensation;
- evidence lineage;
- `missing_evidence_actions`;
- uncertainty/conflicts;
- `recoverability`;
- draft claim package;
- audit trail.

## 9. Stop conditions before internal claim creation

Do not create a case when any of these applies:

- mixed currencies remain unsplit;
- evidence required for a claim line is unregistered/unverified/wrong-scope/ambiguous;
- entitlement interpretation is unverified/rejected/ambiguous;
- duplicate economic representation is unresolved;
- ownership is unknown where material;
- mitigation or prior compensation is unsupported;
- contract/version precedence requires a human determination that has not occurred;
- source data is outside supported numeric bounds;
- schema compatibility gate refuses startup;
- backup/storage integrity is uncertain;
- operator cannot explain a modeled amount from source evidence and calculation trace.

## 10. Deterministic export

```text
recovery-radar export \
  --db pilot.db \
  --event-id EV-001 \
  --supplier-id SUP-001 \
  --output delivery.json
```

Preserve the returned SHA-256 manifest with the pilot record. The export is deterministic for the same package truth and is verified after atomic write.

## 11. Optional internal claim case

Only after the claimability gates pass:

```text
recovery-radar create-case \
  --db pilot.db \
  --event-id EV-001 \
  --supplier-id SUP-001
```

This creates an internal workflow case. It does not submit anything externally.

## 12. T2 measurement sheet

For the historical case, record independently of Recovery Radar:

- number/value of exposure lines in human ground truth;
- number/value correctly identified by Recovery Radar;
- false positives;
- false negatives/missed exposures;
- duplicate/overclaim prevented;
- reviewer changes to evidence state;
- reviewer changes to entitlement state;
- missing-evidence actions judged useful/not useful;
- analyst preparation minutes;
- reviewer minutes;
- total time to auditable package;
- known historical submitted/accepted/settled/paid amount, if authorized and available;
- reasons for differences between modeled claimability and known outcome;
- whether the operator would repeat the workflow;
- WTP only if a real decision-maker explicitly provides it.

Never convert absent outcome/WTP data into a modeled success claim.

## T2 decision

Promote to `T2 — REAL-CASE VALIDATED` only when the historical/real case produces enough evidence to judge correctness and operational usefulness without unresolved material false-positive/false-negative or truth-integrity failures.

If a material defect is found, stop terminal promotion, classify it P0/P1/P2, repair, rerun the synthetic/adversarial suite, then rerun the affected historical test.
