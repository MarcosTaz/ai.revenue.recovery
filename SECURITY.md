# GovMargin security and truth boundaries

GovMargin processes sensitive contractor contract, accounting, billing and payment data. A technically correct formula is not acceptable if tenant isolation, evidence integrity or review controls fail.

## P0 threat classes

### Cross-tenant data leakage

Required controls:
- every persisted business object carries `organization_id`;
- authorization is evaluated against the requested organization, not a client-supplied display field;
- imports reject rows belonging to another organization;
- resource access asserts organization equality;
- duplicate/ambiguous active memberships fail closed;
- no portfolio aggregation across organizations unless data is deliberately anonymized and separately approved.

Current state:
- tenant-scoped CSV ingestion implemented;
- domain authorization roles/actions implemented;
- immutable tenant-store reference contract implemented and tested for cross-tenant lookup failure / overwrite rejection;
- production identity provider/session/database row-level controls **not yet implemented**.

### False government receivable

Required controls:
- no LLM arithmetic becomes financial truth;
- non-finite/negative unexpected values fail closed;
- recovery candidates require evidence lineage and rule lineage;
- provisional/proposed final rates cannot create a verified final-rate candidate;
- ceilings/funding/prior billings are explicit gates;
- FAR 52.232-20 / 52.232-22 notice and excess-limit conditions never become automatic receivables;
- payables/overbilling remain visible and are never netted away;
- unreviewed recovery candidates remain `DRAFT`;
- qualified legal/accounting questions remain review-gated.

### Malicious or untrusted documents

Treat every uploaded document as untrusted data.

Required controls before production upload:
- content-type and file-size allowlist;
- malware/security scanning in the storage pipeline;
- cryptographic content hash at ingestion;
- immutable original evidence object;
- parser output stored separately from the original;
- extracted instructions are data, never executable system instructions;
- prompt-injection text inside contracts/invoices must not change model/system policy or calculation rules;
- no automatic external links, macros, scripts or embedded executables;
- parsing failure produces `UNKNOWN`, not inferred contract terms.

Current state:
- evidence hashes/references exist;
- `govmargin/evidence_intake.py` implements a fail-closed metadata/hash/size/content-type/scan-status admission gate;
- macro-enabled spreadsheet content types are not allowlisted;
- unscanned files are ineligible for storage/parsing in the reference gate;
- **no actual malware scanner, immutable object store or parser isolation service is connected yet**.

### Evidence tampering / lineage loss

Required controls:
- SHA-256 for original evidence;
- immutable evidence IDs;
- source locator and observed timestamp;
- audit events for import, calculation, review and export;
- no silent replacement of rate agreements, invoices or contract versions;
- every revised calculation points to the evidence/rule versions used.

Current state:
- evidence refs and immutable review records exist;
- `govmargin/audit.py` provides a SHA-256 hash-chained append-only audit primitive with tamper/reorder/duplicate detection tests;
- `govmargin/audit_trace.py` can build an operation-level trace with evidence lineage;
- **production append-only persistence is not implemented**.

### Authorization / reviewer conflict

Roles currently modeled:
- ADMIN
- ANALYST
- REVIEWER
- VIEWER

Separation target:
- analyst may import/run calculations but may not approve findings;
- reviewer may review but may not import/alter source financial data;
- viewer is read-only;
- production approval records reviewer identity, role, rationale and timestamp.

For high-value or legally sensitive findings, add configurable dual review before external action.

### Secrets and credentials

- never commit API keys, Vercel tokens, database credentials or customer credentials;
- use environment/secret stores with least privilege;
- rotate credentials after suspected disclosure;
- no customer accounting credentials in prompt text or logs.

### Logging and privacy

Production target:
- never log raw GL lines, bank details, tax identifiers, employee PII or contract attachments by default;
- log identifiers, hashes, state transitions and safe diagnostics;
- redact structured error payloads before user-visible or telemetry output;
- define retention/deletion policy before accepting real customer data.

## LLM boundary

An LLM may assist with:
- document classification;
- extraction proposals;
- source navigation;
- anomaly prioritization;
- explanation drafts.

An LLM may not independently establish:
- contract applicability;
- allowability;
- allocability;
- final rate status;
- funding availability;
- legal claim viability;
- a government receivable;
- arithmetic truth.

Those outputs require source-backed deterministic/review-gated state transitions.

## Deployment gate

Do not call GovMargin production-safe until all are verified:

1. real authentication/session validation;
2. server-side tenant authorization on every protected operation;
3. encrypted persistent storage appropriate for sensitive customer data;
4. secure raw-document upload/scanning pipeline;
5. persistent append-only or equivalently tamper-evident audit history;
6. secret management;
7. backup/recovery and deletion controls;
8. dependency/security scanning;
9. production error/log redaction;
10. adversarial cross-tenant and malicious-document tests.

Connected Vercel account inspection currently shows no dedicated GovMargin project. Do not deploy into unrelated existing projects.

Until these gates pass, the application is a **synthetic/pre-pilot engineering surface**, not a production customer-data system.
