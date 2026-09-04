# DealRecover PostgreSQL platform roles

DealRecover deliberately separates **platform role provisioning** from **database migrations**.

`db/001_baseline.sql` must never create or elevate cluster roles. It fails closed unless the following roles already exist with the required posture.

## `dealrecover_rls`

- `NOLOGIN`
- `NOINHERIT`
- `NOSUPERUSER`
- `NOCREATEDB`
- `NOCREATEROLE`
- `NOREPLICATION`
- `NOBYPASSRLS`

This is the authorization role used inside each tenant transaction via `SET LOCAL ROLE dealrecover_rls`.

## `dealrecover_runtime`

- `LOGIN`
- `NOINHERIT`
- `NOSUPERUSER`
- `NOCREATEDB`
- `NOCREATEROLE`
- `NOREPLICATION`
- `NOBYPASSRLS`
- member of `dealrecover_rls`

The application `DATABASE_URL` authenticates as this role. The application never connects as the database owner.

## Canonical database grants

`dealrecover_rls` receives only the operations used by the runtime:

| Object | Privileges |
| --- | --- |
| tenants | SELECT, INSERT |
| memberships | SELECT, INSERT, UPDATE |
| deals | SELECT, INSERT |
| documents | SELECT, INSERT |
| analyses | SELECT, INSERT |
| dossiers | SELECT, INSERT |
| dispute_events | SELECT, INSERT |
| outcomes | SELECT, INSERT |
| audit_events | SELECT, INSERT |
| billing | SELECT, INSERT, UPDATE |
| document_blobs | SELECT, INSERT |
| api_sessions | SELECT |
| dispute_events_id_seq | USAGE |
| audit_events_seq_seq | USAGE |
| app_tenant_id() | EXECUTE |

`audit_events` is append-only to the runtime. `document_blobs` is immutable to the runtime after insert. The runtime cannot mint API sessions.

## Tenant isolation contract

Every one of the 12 DealRecover tables has RLS enabled **and forced**. The `tenant_isolation` policy is bound to `public.app_tenant_id()`, which reads `app.tenant_id` from the current transaction.

Every runtime transaction must execute, in order:

1. `BEGIN`
2. `SET LOCAL ROLE dealrecover_rls`
3. `set_config('app.tenant_id', <tenant>, true)`
4. tenant-scoped SQL
5. `COMMIT` or `ROLLBACK`

`db/verify.sql` is the executable acceptance gate for this contract.
