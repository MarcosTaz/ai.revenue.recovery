# DebtRecover v0.4.4 source index

Canonical complete executable artifact: `/DebtRecover/debtrecover-factory-v0.4.4.zip` in persistent Library.

SHA-256: `13eb861df7ff385c902e2b1757c0ad93e9e03e25daaebe553eb8fceefbe8cf58`

Verification: 175/175 Python PASS; 4/4 web PASS.

Material v0.4.4 controls persisted in this subtree:
- Data API anonymous fallback is PostgreSQL `anonymous`, with no DebtRecover grants;
- JWT/Data API application path is PostgreSQL `authenticated` (NOLOGIN, no BYPASSRLS);
- tenant authorization derives from `auth.user_id()` + DebtRecover membership;
- application roles OWNER/ANALYST/REVIEWER are not PostgreSQL login roles;
- `DATA_API_RLS_POLICY_SIMULATION` is mandatory and PASS on the isolated synthetic Neon branch;
- no-JWT access is zero; simulated synthetic user A can see A, cannot see/insert B;
- OIDC token/JWKS cryptographic E2E remains FAIL/INCOMPLETE;
- real confidential borrower-data admission remains denied.

Strict truth: 0 real borrowers, 0 verified real recovery, EUR 0 verified real revenue, OUTBOUND_SENT=0. PR remains draft; no automatic merge.