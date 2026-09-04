# AERVIND — Recovery Scan Data Request

_Status: customer-facing minimum-necessary intake checklist for the canonical EUR 9,500 first Recovery Scan._

## Principle

AERVIND requests the smallest evidence cohort needed for the agreed scope: up to **5 aircraft and/or engines**, **1 primary entitlement family**, and up to **12 months** of selected events.

**No live airline-system access or customer credentials are required.** PDFs, spreadsheets and controlled exports are sufficient for the first Recovery Scan.

Do not provide an entire airline data estate when a scoped extract is sufficient.

## 1. Scope identifiers

For each in-scope asset/event, provide where applicable:

- customer / lessee legal entity;
- lessor / counterparty;
- lease ID or stable agreement reference;
- aircraft registration / MSN;
- engine ESN or component identifier;
- selected entitlement family;
- maintenance/event type;
- event start/completion date;
- internal business owner for factual questions.

## 2. Governing contract package

Provide the documents needed to establish the actual rule in force for the selected cohort:

- executed lease;
- relevant amendments;
- side letters affecting the selected entitlement;
- schedules/exhibits defining rates, contribution mechanics, caps/floors/deductibles, exclusions, evidence requirements or claim procedures;
- relevant notices/consents/waivers/extensions that modify the governing position.

Prefer original PDFs plus a simple document index. If several versions exist, include enough information to identify which version governed the selected event.

## 3. Event / maintenance evidence

Only where relevant to the selected entitlement:

- MRO invoice(s);
- final workscope / workscope reconciliation;
- completion certificate / release-to-service evidence;
- shop findings;
- LLP/component detail where the calculation depends on life status;
- technical evidence expressly required by the governing provision;
- payment evidence where payment is a contractual condition to reimbursement.

## 4. Reserve / contribution evidence

Only the records needed for the selected family:

- maintenance reserve statements;
- reserve invoices/payment history;
- fund balance by component/event category;
- lessor contribution statements;
- security-deposit ledger if that family is in scope;
- prepaid-rent ledger if that family is in scope;
- end-of-lease adjustment schedule if that family is in scope.

## 5. Prior claim and settlement history

For the selected cohort, provide known:

- claim register entries;
- prior claim packages;
- lessor/counterparty responses;
- approved/rejected amounts;
- debit/credit memos;
- settlement agreements;
- cash receipt/refund/contractual-offset evidence.

This is necessary to reduce duplicate-recovery risk and reconstruct counterparty history.

## 6. Scoped finance reconciliation inputs

Only where needed for the selected events:

- AP invoice extract;
- GL lines tied to the event;
- payment ledger;
- supplier credits / warranty recoveries that may affect eligible cost;
- FX rate source where the governing terms require currency normalization.

A scoped CSV/Excel export is preferred over unrestricted finance-system access.

## 7. Deadline / notice evidence

Where the entitlement is deadline-sensitive, provide:

- governing deadline/notice language;
- notice address, portal or required delivery method;
- prior notices/submissions;
- acknowledgements;
- extensions or waivers.

## 8. Evidence index

Include one index row per source document/export. The canonical customer template is `templates/recovery_scan_evidence_index.csv`.

Required columns:

`asset_id,lease_id,counterparty,entitlement_family,event_id,event_date,document_type,document_name,source_reference,currency,amount,notes`

Rules:

- `source_reference` must uniquely identify the supplied source/location used by the engagement;
- do not place passwords, API keys or access credentials in the index;
- amounts may be blank when a document is non-financial;
- preserve original source filenames rather than renaming away useful provenance.

## 9. Minimum-complete dataset gate

The 10-business-day target begins only when the agreed minimum cohort is sufficiently complete to perform the contracted scan.

For the selected entitlement family, the minimum normally requires:

1. governing contract/amendment material sufficient to reconstruct the rule;
2. stable asset/event identifiers;
3. event evidence sufficient to establish the trigger;
4. financial inputs required by the rule;
5. known prior claim/reimbursement/settlement history in scope;
6. source references for material inputs;
7. customer owner available to resolve factual gaps.

Partial material can be assessed during intake, but unresolved material gaps remain explicit and can block claim-ready release.

## 10. Data minimization

Do not provide unless specifically required and agreed:

- passenger data;
- crew personal records;
- unrelated HR data;
- unrelated operational safety data;
- unrestricted mailbox exports;
- full ERP/M&E/database dumps;
- customer usernames/passwords/API credentials;
- unrelated bank-account transaction history.

If sensitive or unrelated information appears incidentally, isolate/restrict it rather than expanding the engagement scope.

## 11. Transfer, storage and closeout

Before real source evidence is transferred, agree:

- approved transfer channel;
- approved evidence repository / working location;
- who may access the material;
- location for AERVIND portable case exports;
- retention/deletion or return requirement;
- customer escalation contact for suspected data exposure.

The AERVIND Operator Console is not the source-document repository. Normalized cohorts and case exports may contain confidential financial/evidence metadata and must be handled under the same engagement controls.
