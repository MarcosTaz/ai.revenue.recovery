# GovMargin customer-data handling policy — pre-production

## Current rule

**Do not place real customer contract, accounting, employee, banking, invoice/payment or claim material in this GitHub repository or in the current synthetic web surface.**

The repository is an engineering environment, not an approved customer document store.

## Data classes

### Public / synthetic — permitted in repository

- public FAR/DFARS citations and public case references;
- synthetic contractors and transactions;
- generated non-customer test fixtures;
- public competitor/partner research;
- schemas, rules and deterministic test cases that contain no customer data.

### Customer confidential — prohibited in repository

- signed contracts or modifications supplied by a customer;
- rate agreements that are not public;
- general-ledger/job-cost/timekeeping exports;
- employee names, labor details or PII;
- bank/remittance details;
- invoices, vouchers, payment evidence or accounting-system exports;
- legal advice, claim drafts or privileged material;
- credentials, API tokens or system passwords.

## Pilot intake prerequisite

Before a real design-partner dataset is accepted, the engagement must define and verify:

1. approved secure transfer mechanism;
2. named data owner at the customer;
3. named GovMargin access roles;
4. tenant identifier and access isolation;
5. storage location and encryption posture;
6. immutable original-evidence policy;
7. external malware/security scanning path for uploaded files;
8. parser isolation boundary;
9. retention period;
10. deletion procedure;
11. backup/recovery behavior;
12. log redaction;
13. incident contact/escalation;
14. whether any data may be used for anonymized product learning.

If these are not approved, real-data intake is blocked.

## Minimum retention principle

Retain only what is necessary for the engagement and agreed audit trail.

Proposed default to validate with counsel/customer:

- raw customer evidence: engagement duration + short agreed review/appeal window;
- normalized derived data: same or shorter unless needed for continuing assurance;
- audit hashes/identifiers: retain only as permitted by the engagement and privacy obligations;
- credentials/secrets: never retain in business data;
- rejected uploads: delete/quarantine according to the scanning provider's incident policy, not normal evidence retention.

No default retention period is presented as legally sufficient until the engagement jurisdiction and contractual obligations are reviewed.

## Deletion requirements

A production implementation must support:

- organization-scoped deletion request;
- inventory of raw and derived objects;
- deletion status/audit record without retaining deleted confidential content;
- backup-expiry policy;
- exception handling for legal hold or contractual retention obligations;
- confirmation to the authorized customer owner.

## Logging

Production telemetry must prefer identifiers, hashes, rule IDs and state transitions.

Do not log by default:

- raw ledger lines;
- raw contract text;
- bank information;
- tax identifiers;
- employee PII;
- credentials/tokens;
- full invoice line detail;
- document bytes.

`govmargin/redaction.py` provides a reference log-safe structural redaction layer; production logging must still enforce the policy server-side.

## Anonymized outcome learning

No customer outcome enters the GovMargin moat dataset unless the engagement terms and customer authorization permit it.

At minimum remove direct customer identifiers and prohibit re-identification. High-value or unusual cases may remain identifiable even after superficial field removal; those require additional privacy review before inclusion.

## Repository protection blocker

A root `.gitignore` containing explicit customer-data/secrets paths was attempted in the current execution slice but the connected GitHub mutation was blocked by the tool safety layer. Until that file can be persisted, the policy prohibition above is the controlling repository rule and real customer data remains disallowed entirely.
