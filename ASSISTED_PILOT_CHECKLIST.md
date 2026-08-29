# GovMargin assisted-pilot intake and execution checklist

## Purpose

This checklist defines the minimum controlled input package for a human-supervised GovMargin pilot. It does not authorize autonomous legal, accounting, billing or claim action.

## 1. Contractor identity and scope

Required before analysis:

- contractor legal entity and organization identifier;
- pilot fiscal years and contract/order population;
- named client finance owner;
- named qualified accounting reviewer where accounting judgment is required;
- named counsel contact where legal interpretation, release, claim or jurisdiction questions arise.

Missing ownership or scope => `INTAKE_BLOCKED`.

## 2. Contract truth package

For every in-scope contract/order:

- signed contract;
- task/delivery order where applicable;
- complete modification chain for the reviewed period;
- contract type as stated in source documents;
- effective dates;
- FAR/DFARS/agency clauses actually incorporated;
- estimated cost, ceiling and funding schedule;
- fee terms;
- relevant release / closeout documents.

No inferred clause incorporation. No later modification is back-applied without evidence.

## 3. Rate truth package

For every reviewed fiscal year:

- provisional/billing rates actually used;
- indirect cost proposal state;
- final indirect cost rate agreement or other evidence of settlement;
- settlement effective date;
- pool definitions;
- allocation bases;
- any questioned/unallowable-cost resolution relevant to the rate.

Proposed or modeled rates are not settled final rates.

## 4. Cost truth package

Minimum normalized data:

- general ledger extract;
- job-cost ledger;
- timekeeping/labor distribution;
- direct labor by contract/order;
- ODC/travel/material/subcontract transactions in reviewed categories;
- indirect pool transactions;
- allocation-base transactions;
- transaction identifiers sufficient for duplicate/reversal detection.

Every imported record must retain source lineage and tenant ownership.

## 5. Billing and cash truth package

Required:

- cumulative invoices/vouchers for the reviewed period;
- invoice identifiers and dates;
- billed cost and fee components where available;
- payment remittances / cash application evidence;
- withheld/offset amounts where evidenced;
- final voucher / completion invoice state.

Invoice issue date alone is not payment evidence.

## 6. Funding safeguard package

Where FAR 52.232-20 is evidenced:

- contract-specific estimated-cost amount;
- contract-specific notice percentage;
- contract-specific notice window;
- written notices;
- written Contracting Officer increases;
- modifications affecting estimated cost.

Where FAR 52.232-22 is evidenced:

- amount actually allotted for the relevant period/order;
- items/period covered by the allotment where stated;
- contract-specific notice percentage and window;
- written notices;
- written Contracting Officer increases in allotment;
- modifications affecting allotted funds.

A forecast, change order or informal communication does not by itself create additional funding.

## 7. Automated admissibility gates

The assisted pilot may calculate only when:

1. organization/tenant ownership is valid;
2. contract/order/version is identified;
3. contract type is supported by the current wedge;
4. required clause evidence is present;
5. settled final-rate evidence is present when a final-rate true-up is asserted;
6. source transactions pass validation and duplicate checks;
7. ceiling/funding inputs are evidenced;
8. prior billings are complete enough for cumulative reconciliation.

Failure of any required gate => `UNKNOWN` or `REQUIRES_REVIEW`, never a recovery assertion.

## 8. Human review gates

Human approval is required before a candidate enters a client-facing action pack.

Accounting review triggers include:

- allowability judgment not deterministically supported;
- allocability disputes;
- pool/base classification judgment;
- cost transfers or related-party costs;
- unresolved final-rate settlement ambiguity.

Legal review triggers include:

- signed releases or reservations;
- claim accrual / statute / jurisdiction questions;
- Contract Disputes Act issues;
- disputed entitlement or contract interpretation;
- certified claim or representation decisions.

## 9. Truth-preserving output states

Every analyzed item must terminate in one of:

- `SUPPORTED_RECOVERY_CANDIDATE`;
- `SUPPORTED_PAYABLE_OR_OVERBILLING`;
- `NO_MATERIAL_VARIANCE`;
- `REQUIRES_ACCOUNTING_REVIEW`;
- `REQUIRES_LEGAL_REVIEW`;
- `INSUFFICIENT_EVIDENCE`;
- `UNKNOWN`.

No favorable and unfavorable findings are silently netted.

## 10. Pilot completion standard

A pilot is complete only when it produces:

- contract/order/version register;
- source-to-transaction evidence index;
- applicable-rule lineage;
- deterministic calculation trace;
- cumulative billed-versus-expected schedule;
- payment reconciliation;
- funding/ceiling safeguard result;
- human-review disposition;
- executive schedule separating receivables, payables, no-variance and unknowns;
- preserved audit trail.

A pilot is not a verified recovery until the client completes the appropriate billing/true-up action and the economic outcome is evidenced.
