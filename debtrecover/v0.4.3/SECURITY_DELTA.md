# DebtRecover v0.4.3 security / truth delta

External environment: synthetic-only Neon branch `debtrecover-v042-synthetic`.

## P0 repair 1 — cross-tenant relational integrity

RLS correctly isolated direct reads/writes, but red-team reproduced a subtler defect: an `evidence_metadata` row labelled organization A could reference a case belonging to organization B. The canonical v0.4.3 schema binds dependent rows through composite `(case_id, organization_id)` foreign keys. The same tenant/case binding applies to evidence, findings, outcomes and audit; finding supersession is also tenant-bound.

The reproduced cross-tenant insert is now rejected.

## P0 repair 2 — outcome truth

The first external outcomes constraint blocked `VERIFIED_PAID` without payment evidence but accepted `VERIFIED_ZERO` with positive `verified_capture`. v0.4.3 adds `outcomes_state_capture_truth`:

- `UNVERIFIED` / `VERIFIED_ZERO`: capture = 0, payment hash = NULL;
- `VERIFIED_PARTIAL` / `VERIFIED_PAID`: capture > 0, payment hash required.

Invalid zero-state capture is now rejected; valid zero and paid synthetic probes pass.

## P0 repair 3 — real-data gate composition

Configuration/provider names alone can no longer unlock borrower-data intake. `require_real_data_ready(env, provider_probes)` requires both complete configuration and fresh external provider acceptance.

`OIDC_TOKEN_JWKS_VERIFY` is a mandatory live probe.

## P0 repair 4 — provider evidence ordering

Provider acceptance no longer uses “any fresh PASS”. The freshest observation controls each probe type. A newer FAIL overrides an older PASS, and conflicting latest observations are rejected as ambiguous.

## Current admission

External provider acceptance = FALSE. Real confidential borrower-data admission = DENIED.
