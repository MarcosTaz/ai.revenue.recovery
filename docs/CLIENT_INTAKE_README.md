# AERVIND — Recovery Scan Client Intake Guide

_For the canonical first Recovery Scan: EUR 9,500 · up to 5 aircraft/engines · 1 primary entitlement family · up to 12 months of selected events · target 10 business days after the complete agreed minimum dataset._

## Objective

Give AERVIND a small, controlled evidence set that can answer one question end to end:

**What did the governing lease provide, what happened, what amount is economically supportable, what has already been claimed/paid, and what can be proven through settlement?**

No live access to airline systems is required for this first engagement.

## Recommended data-room structure

Use the customer's approved secure repository. A simple structure is sufficient:

```text
00_SCOPE_AND_INDEX/
01_CONTRACTS/
02_EVENTS_AND_MAINTENANCE/
03_RESERVE_OR_CONTRIBUTION/
04_FINANCE/
05_PRIOR_CLAIMS_AND_SETTLEMENTS/
06_NOTICES_AND_DEADLINES/
```

Do not move source files merely to satisfy this example if the customer already has a controlled repository. Stable source references are more important than cosmetic folder names.

## 00 — Scope and index

Provide:

- named customer business owner;
- list of in-scope assets/events;
- selected entitlement family;
- completed `recovery_scan_evidence_index.csv`;
- any short note needed to explain source-system/export conventions.

## 01 — Contracts

Provide only the governing material needed for the selected entitlement:

- executed lease;
- relevant amendments;
- relevant schedules/exhibits;
- relevant side letters/notices/waivers.

Do not send unrelated commercial schedules unless they are necessary to interpret the selected entitlement.

## 02 — Events and maintenance

Provide event evidence required by the governing rule, such as:

- invoice;
- final workscope;
- completion/release evidence;
- shop findings or component-life detail if contractually relevant.

## 03 — Reserve or contribution

Provide the statement/ledger needed to establish the available fund or contribution position for the selected event.

## 04 — Finance

Provide only the scoped financial records required to support the calculation or reimbursement condition, for example:

- AP/GL event extract;
- payment evidence;
- supplier credit / warranty recovery if economically relevant;
- required FX source.

## 05 — Prior claims and settlements

Provide known prior submissions, responses, approvals/rejections and settlement evidence for the selected cohort. This is a core duplicate-recovery control.

## 06 — Notices and deadlines

Provide notice mechanics, prior notices/submissions, portal/email evidence and extensions/waivers when deadline or delivery method affects entitlement.

## File and reference discipline

- preserve original filenames where possible;
- use stable IDs for assets/events;
- do not overwrite earlier contract versions;
- identify superseded documents rather than deleting provenance;
- do not put passwords/API keys in filenames, spreadsheets or notes;
- each material number used in a claim must be traceable to a source reference.

## What AERVIND does after intake

1. locks the agreed cohort;
2. inventories the evidence;
3. reconstructs the governing entitlement rule;
4. reconciles event and finance evidence;
5. tests prior claims/payments, exclusions and deadlines;
6. red-teams positive candidates;
7. assigns each candidate an explicit status;
8. prepares claim-ready material only where gates pass;
9. records external lifecycle events only after real evidence exists;
10. reports recovered value only after settlement evidence.

## Minimum completeness

The **10 business days** target starts when the minimum dataset required by the agreed entitlement family is complete enough to perform the contracted scan.

AERVIND can begin intake/triage with partial material, but material gaps remain explicit and may block claim-ready release.

## Security

Use only the transfer/storage route agreed for the engagement. Do not send unrestricted system credentials or unrelated personal/operational data.

AERVIND's portable case file is confidential work product. It is not application-encrypted and must be stored in the approved secure location.
