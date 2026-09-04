# GovMargin pilot offer

## Offer

**Independent Cross-System Final-Rate & Closeout Reconciliation**

For a U.S. federal contractor with historical cost-reimbursement / CPFF contracts, GovMargin independently reconstructs supported contract economics and compares them with cumulative billings and verified payments.

The first design-partner pilot is intentionally aimed at cases where historical truth may be fragmented across an ERP migration, manual invoice history, acquired entity, spreadsheet records or payment systems. It is **not** positioned as a replacement for Costpoint/Unanet or qualified GovCon accounting.

## Included pilot scope

- one contractor legal entity;
- up to five cost-reimbursement / CPFF contracts or task orders;
- up to two completed fiscal years with evidenced FAR 52.216-7 and settled-final-rate / closeout exposure;
- one explicit cross-system/history-fragmentation trigger;
- contract + modification register;
- contract-type / clause applicability check;
- provisional/billing-rate versus settled-final-rate reconciliation;
- selected supported direct-cost / ODC review;
- fee, funding and ceiling reconciliation where terms are evidenced;
- FAR 52.232-20 / 52.232-22 safeguard where incorporated;
- cumulative invoice/voucher and verified payment comparison;
- approved completion-voucher / final-payment reconciliation where evidence exists;
- symmetric recovery and payable/overbilling findings;
- evidence / rule lineage;
- human review pack and qualified-review queue;
- comparison against what the customer's ordinary ERP/accountant process had already surfaced.

## Explicitly outside first-wedge scope

Unless separately implemented and tested:

- T&M labor reconciliation;
- labor-hour reconciliation;
- firm-fixed-price margin recovery;
- unsupported contract types;
- open/unsettled final-rate theories presented as verified recovery;
- broad FAR Part 31 automated judgment.

## Excluded reserved activities

GovMargin does not by default provide:

- legal advice;
- Contract Disputes Act claim representation;
- claim certification;
- litigation strategy;
- CPA attestation / audit opinion;
- negotiation with DCAA or a Contracting Officer as professional representative;
- unsupported allowability/allocability judgments;
- ownership/assignment of Government receivables;
- success-linked compensation before qualified review.

See `LEGAL_BOUNDARY.md`.

## Pilot deliverable

Every reviewed item terminates truthfully in one of:

1. **SUPPORTED RECOVERY CANDIDATE**
2. **SUPPORTED PAYABLE / OVERBILLING EXPOSURE**
3. **NO MATERIAL VARIANCE**
4. **REQUIRES ACCOUNTING REVIEW**
5. **REQUIRES LEGAL REVIEW**
6. **INSUFFICIENT EVIDENCE / UNKNOWN**

Never promise a recovery before the audit.

## Pricing — test hypothesis

### Design-partner pilot

**$7,500 fixed** for the controlled scope above.

Reasons for fixed-fee launch:

- preserves symmetric audit truth;
- avoids assuming recovery-contingent compensation is permissible;
- avoids incentive to suppress payables;
- produces real time-to-deliver and gross-margin evidence;
- directly tests willingness to pay for the independent cross-system layer.

### Internal delivery guardrail

The executable `govmargin/economics.py` model currently uses a planning example where $7,500, 40 delivery hours at $75 loaded cost/hour and $500 non-labor direct cost yields 53.33% modeled gross margin.

At the same cost assumptions, a 50% target gross margin implies approximately **43.33 maximum delivery hours**.

These are planning assumptions, not validated economics. See `UNIT_ECONOMICS.md`.

### Expansion hypotheses only after pilot evidence

- $15,000–$35,000 fixed forensic audit for larger contract sets;
- fixed annual continuous-assurance subscription;
- PE / M&A portfolio pricing;
- fixed partner wholesale / co-delivery pricing.

A fixed + success component remains **disabled** until qualified legal/accounting review explicitly clears the structure and its conflict safeguards.

## Ideal design partner

Prioritize a contractor with:

- approximately $5M–$50M federal-contract revenue;
- completed cost-reimbursement / CPFF history;
- evidenced 52.216-7 applicability and settled final rates;
- at least one migration/manual-invoice/acquisition/finance-turnover/aged-closeout trigger;
- enough source records to reconstruct one contract-year;
- finance leadership willing to validate both favorable and unfavorable findings;
- willingness to compare GovMargin results with existing ERP/accountant work.

Deprioritize:

- FFP-only portfolios;
- T&M/LH-only portfolios;
- ordinary current-state Costpoint environments with complete trusted Schedule I / closeout reporting and no fragmented-history trigger;
- engagements expecting GovMargin to manufacture or represent a claim.

## Pilot success criteria

A design-partner pilot is useful only if GovMargin can:

- securely receive a permitted real dataset under an approved data-handling plan;
- reconstruct at least one contract-year deterministically;
- preserve source/rule lineage;
- produce zero known false receivables;
- surface payables with the same rigor as recoveries;
- obtain client finance / qualified-review agreement on the calculation trail;
- measure actual delivery hours/data friction/gross margin;
- establish what was **incremental** to the existing ERP/accounting workflow;
- establish whether the customer would pay for continuing assurance.

A zero-recovery pilot can validate accuracy and monitoring value, but it does not validate recovery frequency. A variance already known through ordinary Costpoint/accounting workflow does not validate the independent-overlay wedge.
