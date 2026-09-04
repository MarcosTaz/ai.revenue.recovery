# AERVIND — Security & Confidentiality Baseline

_Last reviewed: 2026-09-05_

This baseline governs assisted Recovery Scans before any enterprise-scale SaaS deployment or deep airline-system integration.

It is an operating-control document, **not a security certification, audit report, penetration-test claim or regulatory attestation**.

## Security objective

Protect highly confidential lease, maintenance, commercial and financial information while using the smallest evidence footprint needed to prove or disprove an entitlement.

## Data handling principles

1. **Scope minimization** — receive only the assets, leases, events and finance evidence needed for the agreed cohort.
2. **No live-system access by default** — the first Recovery Scan operates from customer-approved documents/exports rather than credentials to ERP, M&E, lease-management or banking systems.
3. **Source preservation** — original documents remain unchanged in the engagement-approved repository; AERVIND records controlled source references.
4. **Need-to-know access** — customer material is available only to personnel needed to perform/review the engagement.
5. **No training use** — confidential customer material is not repurposed as training data, marketing material or demo corpus.
6. **Synthetic demos by default** — demonstrations use synthetic data unless a customer expressly approves a sanitized example under agreed terms.
7. **Evidence lineage** — every material calculation input has a stable source reference.
8. **Human release** — automated economic output cannot alone authorize an external claim package.
9. **External-event truth** — submission, acknowledgement, dispute, approval and rejection are recorded only after real evidence exists.
10. **Settlement truth** — recovered value requires positive cash, credit, refund or contractually valid offset evidence.

## Pre-intake gate

Before receiving real airline data, record:

- customer legal entity;
- commercial/engagement owner;
- AERVIND accountable operator/reviewer;
- agreed aircraft/engine/event/entitlement scope;
- permitted source-document transfer channel;
- approved working/evidence repository;
- approved AERVIND case-file storage location;
- retention/deletion requirement;
- authorized users/reviewers;
- NDA / confidentiality status;
- escalation contact for suspected data exposure.

Do not receive production customer evidence casually by consumer messaging, personal cloud folders or another unapproved route when the customer has specified a controlled channel.

## Current assisted-console boundary

The standard AERVIND Operator Console is intentionally local-only.

It:

- **refuses non-loopback bind addresses** rather than merely defaulting to localhost;
- accepts `localhost` / loopback IP authorities only;
- rejects non-loopback client addresses and non-loopback `Host` headers;
- rejects browser state-changing requests whose `Origin` does not exactly match the local authority;
- uses a bounded idle request timeout and daemon request workers;
- rejects unsupported transfer-encoded request bodies, incomplete request bodies and pathological JSON structures;
- limits request bodies to **2 MB**;
- has no public customer login or hosted customer endpoint;
- processes API request bodies in memory;
- does not persist submitted cohort bodies server-side;
- does not log request bodies;
- does not load third-party JavaScript, analytics or telemetry;
- returns `Cache-Control: no-store`;
- uses restrictive Content Security Policy, frame, referrer, cross-origin and browser-permission headers;
- does not connect directly to airline operational systems;
- does not transmit claim packages externally.

This is a deliberate assisted-pilot architecture, not a substitute for enterprise authentication/tenant controls. A broad hosted deployment would require a different control model.

Source documents should remain outside the console in the approved evidence repository. The normalized cohort stores evidence metadata/source references rather than embedding full source files.

## Portable case file

Durable assisted-pilot workflow state exists in an operator-exported AERVIND case file.

The case file can contain confidential normalized financial values, source references, lifecycle history and counterparty references. **The application does not encrypt the exported case file itself.**

Therefore:

- store it only in the engagement-approved encrypted/controlled location;
- do not email it through an unapproved channel;
- do not commit it to Git or any public repository;
- apply the same customer classification as the underlying engagement work product;
- remove local working copies at engagement close when required by retention terms.

The case file includes a SHA-256 digest binding released workflow state to the reviewed cohort revision. Material source changes after release must create a new reviewed revision rather than silently rewriting prior audit history.

## Credentials and secrets

AERVIND does not need customer system credentials for the standard first scan.

Do not accept or store unrestricted customer passwords, API keys or banking credentials merely because they are offered. If a future buyer requires an integration, design and approve that integration separately with unique identities, least privilege, revocation, environment separation and buyer-approved scope.

Never place API keys, passwords, banking credentials, private tax identifiers or customer secrets in the public repository.

## Logging policy

Application and operational logs must avoid raw contract text, full invoice content, bank details and customer evidence payloads.

Prefer:

- case/claim IDs;
- hashes;
- timestamps;
- lifecycle transitions;
- actor identity;
- source-reference identifiers;
- artifact hashes;
- generic error categories.

The standard local console uses the Python HTTP server's request metadata logging but never request-body logging.

## Claim-package controls

Before generation:

- current economic status must still be `claim_ready`;
- workflow lifecycle must be `claim_ready`;
- source-lineage gaps must be empty;
- human release confirmation and actor identity are required.

Generation is audited by content SHA-256 and remains `not_submitted`. The console has no external-send function.

Internal red-team commentary and unrelated evidence do not enter the external package by default.

## External lifecycle evidence

AERVIND records but does not fabricate external activity.

- submission requires a real external submission reference;
- acknowledgement/dispute/approval/rejection requires corresponding evidence where the state is external;
- settlement requires type, amount, currency and evidence reference;
- settlement cannot exceed the currently reviewed/asserted amount without revising and re-reviewing the economics.

While `docs/REAL_OUTREACH_HOLD.md` is active, no external claim/counterparty communication is authorized even if the console can record such a state from independently supplied evidence.

## Retention / deletion

Each engagement must define retention or deletion/return requirements.

At closeout:

1. identify source documents, normalized cohorts, AERVIND case files, exports and claim packages covered by the requirement;
2. preserve only records contractually/legally required for support or audit;
3. delete/return material according to engagement terms;
4. remove unnecessary local working copies;
5. record the closeout/retention action.

Do not claim automated deletion, immutable retention enforcement or certified destruction: the current assisted model relies on the agreed controlled repository and operator procedure.

## Incident response baseline

If confidential material may have been exposed:

1. stop further disclosure/access where possible;
2. preserve relevant audit evidence without spreading affected data;
3. identify customer, scope and data categories affected;
4. notify designated internal/customer escalation contacts according to contractual/legal requirements;
5. remediate the cause before resuming affected processing;
6. document containment and corrective actions.

This is an operating procedure, not a claim of a staffed 24/7 SOC or contractual incident-response SLA.

## Current claims we do not make

AERVIND does **not** currently claim:

- SOC 2, ISO 27001 or equivalent certification;
- external penetration-test certification;
- formal hosted multi-tenant isolation;
- SSO/SAML/OIDC/RBAC for a hosted product;
- application-level encryption of portable case exports;
- managed backup/PITR/disaster-recovery guarantees;
- a staffed 24/7 SOC or security SLA;
- customer-data residency guarantees beyond the actual agreed storage route;
- a fixed controller/processor role before the engagement facts are assessed.

## Buyer-driven enterprise controls

Before a broad hosted enterprise deployment, add as required:

- tenant isolation;
- RBAC;
- SSO/SAML/OIDC;
- MFA policy;
- durable immutable server-side audit history;
- configurable retention/deletion;
- encryption-at-rest design and key management;
- backup/disaster-recovery objectives;
- vulnerability/dependency management;
- security testing;
- vendor/subprocessor inventory;
- privacy/security contractual documentation;
- formal external security assurance required by the buyer.

Do not claim these controls or certifications before they actually exist.
