# Recovery Radar — Historical Pilot Data Handling

Status: `EXTERNAL-READY DRAFT / NOT A PRODUCTION SECURITY CERTIFICATION`

This statement describes the current **local controlled historical-pilot** architecture only. It does not claim SOC 2, ISO 27001, production IAM, managed key custody, public-cloud hardening, or application-level database encryption.

## Current processing model

Recovery Radar v0.2.2 is a local Python/SQLite operator application.

For the controlled pilot:

- the application can be run on an operator-controlled local machine/environment;
- the current repository has no declared runtime dependency on a remote SaaS/API service;
- no ERP/EDI/PLM write access is required for the first historical pilot;
- no OEM/customer communication is performed by the application;
- production hosting is outside the current T1 boundary.

This does not prevent the operator's own operating system, backup software, endpoint management, file-sync tools, or infrastructure from transmitting data. Those controls remain the pilot operator's responsibility.

## Raw evidence files

Examples include contracts, purchase orders, notices, cost exports, tooling approvals, mitigation records and reimbursement records.

Current boundary:

- raw evidence files remain in the operator-controlled pilot directory;
- Recovery Radar reads referenced file bytes to calculate SHA-256 identity hashes and construct evidence metadata;
- the evidence registry does **not** persist raw document bytes;
- the raw evidence directory therefore remains a separate retention/security responsibility;
- deleting a raw source file later does not erase normalized facts, metadata, hashes, reviews or audit records already stored in the Recovery Radar database.

## What the SQLite database stores

The local database can contain confidential structured pilot information, including:

- workspace identity;
- normalized recovery event records;
- customer/program/part aliases or identifiers supplied by the operator;
- exposure quantities, unit costs, currencies, ownership, mitigation and prior-reimbursement fields;
- entitlement-basis references and support states;
- evidence metadata, source references and SHA-256 content hashes;
- evidence and entitlement review events;
- claim-case workflow data;
- payment/settlement workflow records when explicitly entered;
- audit events;
- API credential identities, salts and derived secret hashes.

API-key plaintext secrets are not stored in the database after issuance.

## Encryption boundary

Recovery Radar does **not** currently implement application-level encryption of the SQLite database or raw evidence files.

For a confidential pilot, use an operator-controlled machine/storage volume with the organization's approved disk/file encryption and access controls. Do not describe Recovery Radar itself as providing encrypted-at-rest storage unless that capability is separately implemented and verified.

## Authentication / access boundary

The local application implements:

- workspace-scoped API credentials;
- roles `ADMIN`, `ANALYST`, `REVIEWER`;
- workspace/role derived from the credential rather than caller-selected tenant fields;
- salted PBKDF2-HMAC-SHA256 derived credential secrets rather than stored plaintext API secrets;
- key revocation;
- reviewer/source-writer separation;
- same-actor self-verification prevention for evidence and entitlement records.

It does **not** currently claim:

- enterprise SSO;
- MFA;
- password recovery;
- public-network transport security;
- managed secret vault integration;
- rate limiting;
- SIEM integration;
- production intrusion monitoring.

Those are not required for the current controlled local historical-pilot boundary and would be separate production-readiness work.

## Source-scope manifest

Before a T2-quality comparison, the operator can create `RECOVERY_RADAR_SOURCE_SCOPE_V1` using `scope-manifest`.

The manifest contains normalized case identity/economic fields and evidence metadata/content hashes. It deliberately does **not** embed raw evidence bytes.

Treat both the manifest and its hashes as confidential pilot metadata because they can reveal source identifiers and economic structure.

A source-scope SHA proves modeled dataset identity for comparison. It is **not** authorization, encryption, completeness proof, legal admissibility or proof of entitlement.

## Exports

Recovery Radar can create deterministic source-scope, claim-package and T2 scorecard JSON artifacts.

These artifacts may contain confidential normalized economic, evidence-lineage, review, audit or source-identity information. They are confidential pilot artifacts even though raw evidence bytes are not embedded.

The application:

- writes supported exports atomically;
- produces SHA-256 manifests/identities for integrity verification;
- verifies written bytes after export where implemented;
- binds T2 scoring to the persisted normalized source scope when the ground-truth file records `source_scope_sha256`.

A SHA-256 hash proves byte/data identity for comparison; it is **not encryption** and does not make an artifact non-confidential.

## Authorization/provenance boundary

Actual participant/data-owner authorization remains external to Recovery Radar.

The application may record an authorization reference, case origin and ground-truth method, but deliberately marks these as not independently verified. The presence of those fields cannot establish legal authority, T2, WTP, customer acceptance or recovered cash.

Use `PILOT_AUTHORIZATION_RECORD.md` and `PILOT_PROVENANCE.md` to retain the external governance chain without misrepresenting application metadata as proof.

## Backups

The tested SQLite backup path verifies:

- SQLite structural integrity;
- foreign-key integrity;
- whole-database truth digest consistency.

Backup verification is an integrity feature, not a confidentiality control. Pilot backup files must receive the same access/encryption handling as the source database.

## Data minimization for the first pilot

Prefer:

- one closed historical case only;
- stable customer/program aliases where names are unnecessary;
- only case-relevant cost and evidence records;
- no unrelated customer/program data;
- no production credentials;
- no personal data unless genuinely required and authorized;
- no live dispute communications;
- local/offline operation where the participant's policy permits it.

Do not deliberately strip a field if doing so would make ownership, program linkage, contractual scope, mitigation, reimbursement, or historical outcome impossible to review. The objective is **minimum sufficient evidence**, not maximum redaction at the cost of truth.

## Data deletion / retention truth

Recovery Radar does not currently provide a production retention-policy engine or automated secure-delete guarantee.

For a controlled pilot, retention/deletion must be handled by the operator under the agreed pilot process, including:

- raw evidence directory;
- SQLite database;
- database backups;
- exported source-scope manifests;
- exported claim packages;
- exported T2 scorecards;
- any separately stored authorization/ground-truth/reviewer notes.

Do not promise cryptographic erasure or certified deletion unless separately implemented and verified.

## Recommended first-pilot operating controls

Before receiving confidential files, agree on:

1. authorized case and data owner;
2. designated local processing machine/environment;
3. approved storage encryption/access controls outside Recovery Radar;
4. analyst and independent reviewer identities;
5. allowed aliases/redactions;
6. where raw evidence may be stored;
7. where manifests/exports/backups may be stored;
8. retention/deletion date/process;
9. prohibition on external claim/customer communication from the pilot;
10. a stop/escalation path if unexpected sensitive or unrelated data appears.

## Current truth

No real supplier/customer confidential historical dataset has been received by this Factory.

`REAL_CASES = 0`

`WTP = UNKNOWN`

This document is a factual description of the current local-pilot architecture, not a security certification or contractual data-processing agreement.