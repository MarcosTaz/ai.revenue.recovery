# DealRecover v0.7.3.1 — Release Runbook

## Release intent

This release converts the managed DealRecover runtime from an environment-specific pilot into a reproducible, gated release candidate.

## Mandatory gates

No merge or deployment is accepted unless all of these are green:

1. Managed source bundle SHA-256 matches `1016ebb297cd0efe14bc80f1e0e2b0e759fe55e7c393428b5ada92b1bb646673` while the legacy bundle remains in the tree.
2. Effective runtime source passes `node --check`.
3. Production Dockerfile builds successfully.
4. PostgreSQL 18 starts from an empty database.
5. `dealrecover_rls` and `dealrecover_runtime` satisfy the least-privilege preflight.
6. `db/001_baseline.sql` applies from zero.
7. `db/verify.sql` passes: 12 tables, FORCE RLS, tenant policies, minimal grants and behavioral cross-tenant isolation.
8. Managed API boots while authenticated to PostgreSQL as `dealrecover_runtime` and switching locally to `dealrecover_rls`.
9. `/health` and `/ready` both return success.
10. Hardened customer E2E passes all 32 checks, including positive working-capital recovery, dispute lifecycle, recovery evidence, billing, encrypted document roundtrip, analysis/dossier retrieval, tamper-evident audit and cross-tenant denial.

The canonical CI implementation is `.github/workflows/dealrecover-tests.yml`.

## Production invariants

- Railway root: `/dealrecover`
- Railway builder: Dockerfile
- Railway health gate: `/ready`
- Railway replicas: 1 until load evidence justifies scaling
- Preferred app region: US East / IAD while Neon remains in AWS us-east-2
- PostgreSQL transport in production: `sslmode=verify-full`
- Database runtime role: `dealrecover_rls`
- Runtime login: `dealrecover_runtime`
- All 12 DealRecover tables: FORCE RLS
- Audit: append-only to runtime and SHA-256 hash chained
- Document content: encrypted before persistence; plaintext is never the database blob value

## Required application variables

- `DATABASE_URL`
- `DEALRECOVER_DB_RUNTIME_ROLE=dealrecover_rls`
- `DEALRECOVER_DEPLOY_MODE=managed`
- `DEALRECOVER_MANAGED_BOOTSTRAP_MODULE=./src/managedBootstrap.js`
- `DEALRECOVER_VAULT_KEY_B64` — exactly 32 decoded bytes
- `NODE_ENV=production`

Never place variable values in Git.

## Deployment sequence

1. Green CI on release branch.
2. Review `main...release` changed-file set; DealRecover release must not modify unrelated products.
3. Merge release PR only after all required checks are green and the PR is mergeable.
4. Point Railway source to `main` at `/dealrecover` only after the merged commit is visible.
5. Deploy with `/ready` as the platform health gate.
6. Run the hardened E2E against the deployed managed API.
7. Query Neon for final analysis/dossier lineage, audit-chain validity and encrypted blob persistence.
8. Record the successful deployment ID and commit SHA in the release evidence.

## Rollback

Application rollback is independent from database rollback when no schema migration has been applied:

1. Repoint/redeploy the last known-good Railway commit.
2. Require `/ready` success.
3. Run the hardened E2E before declaring rollback complete.

For database-affecting future releases:

1. Create a Neon snapshot or point-in-time recovery checkpoint before applying schema changes where the plan supports it.
2. Never reset or restore the production branch without explicit operator approval and a documented target checkpoint.
3. Prefer forward-fix migrations when safe; destructive rollback is the last resort.

## Current Neon plan constraints

The current Neon project is on `free_v3`. At release preparation time:

- automatic backup schedules are not enabled for this project;
- the manual snapshot quota is already consumed;
- the protected-branch quota is already consumed;
- history retention is 6 hours.

These are infrastructure-plan constraints, not application defects. Until the plan is upgraded, compensating controls are the canonical migration, clean-database CI reconstruction, an isolated validation branch, the existing manual snapshot, and mandatory post-deploy E2E.

## Evidence already established before main integration

- Railway managed production runtime green on `/ready`.
- Production HTTP E2E: 32/32 PASS.
- Working-capital synthetic recovery: EUR 10 supported and recovered.
- Billing terminal state: `PAID_EXTERNALLY`.
- Audit chain: 13 material events, verified head hash, cross-tenant audit 404.
- Encrypted document roundtrip proven; ciphertext persisted instead of plaintext.
- Clean PostgreSQL 18 reconstruction and 32-gate CI proven on GitHub Actions.
