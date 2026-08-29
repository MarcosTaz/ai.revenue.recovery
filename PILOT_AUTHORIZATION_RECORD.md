# Recovery Radar — Historical Pilot Authorization Record

Status: `TEMPLATE / HUMAN GOVERNANCE ARTIFACT / NOT SELF-AUTHORIZING`

Purpose: create an auditable reference for the human authorization that must exist **before** confidential historical case data is processed. Completing this template does not make authorization legally valid by itself; the operator must retain whatever approval/signature/process the participant actually requires.

## Case identity

- Pilot case alias:
- Supplier/participant legal entity:
- Customer/program alias if sanitized:
- Historical event type:
- Historical/closed matter confirmed by:
- Live dispute involved? `YES / NO / UNKNOWN`

If `YES` or `UNKNOWN`, stop unless the authorized data owner explicitly approves retrospective processing and confirms the pilot will not influence an unauthorized live submission/negotiation.

## Authorization

- Data owner / approving function:
- Approval reference or controlled-system record ID:
- Approval date:
- Authorized operator:
- Authorized purpose: `RETROSPECTIVE CANCELLATION-CLAIM PRE-AUDIT VALIDATION`
- Approved processing environment:
- Approved storage location/control class:
- Allowed reviewer identity/function:
- Allowed data categories:
- Explicitly excluded data categories:
- Allowed aliases/redactions:
- Retention/deletion requirement:
- Export/backup handling requirement:

Do not put credentials, secrets, or unnecessary personal data in this repository template.

## Source-scope freeze

Before analysis, run the authenticated operator command:

```text
recovery-radar scope-manifest \
  --db pilot.db \
  --bundle bundle.json \
  --output source-scope.json
```

Record the returned:

- `source_scope_sha256`:
- source-scope artifact SHA-256:
- source-scope file location/reference:
- exact Recovery Radar commit SHA:

The source-scope hash freezes normalized economic inputs, documentary references and concrete evidence-file content hashes. It does **not** embed raw evidence bytes and it does **not** prove that the operator was authorized to use those sources.

## Ground-truth independence

- Ground-truth reviewer:
- Did the reviewer see the Recovery Radar first-pass output before freezing ground truth? `YES / NO / UNKNOWN`
- Ground-truth method recorded for scorecard: `BLIND / ASSISTED / UNKNOWN`
- Frozen ground-truth file reference:
- Independent ground-truth file SHA-256:

Use `BLIND` only when the reference was prepared without exposure to Recovery Radar's first-pass result. This is a recorded human assertion, not something the application can independently verify.

## Scorecard linkage

In `RECOVERY_RADAR_GROUND_TRUTH_V1`, set only the metadata that is actually supported:

```json
{
  "provenance": {
    "authorization_reference": "<controlled approval/reference>",
    "source_scope_sha256": "<64-char lowercase SHA-256 from source-scope manifest>",
    "ground_truth_method": "BLIND"
  }
}
```

Recovery Radar deliberately records these fields as **not independently verified**. Their presence cannot auto-promote `case_origin`, T2, customer acceptance, WTP, settlement or recovered cash.

## Final operator check

Proceed only when all are true:

- [ ] the case is authorized for the stated retrospective purpose;
- [ ] source data is limited to the authorized scope;
- [ ] source-scope manifest is frozen before comparison;
- [ ] analyst and reviewer actors are appropriately separated;
- [ ] ground truth is independently frozen or its non-blind limitation is recorded;
- [ ] live claim/customer communication is outside the pilot unless separately authorized;
- [ ] retention/deletion and export handling are understood;
- [ ] the exact application commit is recorded.

If any mandatory item is unresolved, keep the case outside T2 promotion and preserve the gap explicitly.