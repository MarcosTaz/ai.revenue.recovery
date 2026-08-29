# GovMargin competitor kill-test

## Decision

**The reconciliation problem is not novel. The surviving opportunity must be independent, multi-ERP, evidence-first forensic assurance rather than generic GovCon billing reconciliation.**

## Deltek Costpoint — strongest software substitute found

Current Deltek documentation materially narrows GovMargin's white-space claim.

### Schedule I — Cumulative Direct and Indirect Cost Claimed & Billed

Deltek documents Schedule I as a cumulative direct/indirect cost claimed-and-billed report. Its documentation states that the schedule can be used to identify:

- physically completed contracts for closeout; and
- contracts that may require billing adjustments because of over/under-billing.

Source:
- https://education.deltek.com/web/content/Costpoint/tech%20guides%20for%20ask%20dela/costpoint_bi_team_content_guide.pdf
- https://api.deltek.com/Product/Costpoint/8.1/GA/PromptsISchedCumDirIndirCostClaimedBilled.html

Important limitation in Deltek's own documentation: the Schedule I report assumes invoices are computed and posted in Costpoint, and manual invoices can lead to null/incorrect invoice-number information. That creates a potential independent-reconciliation value proposition where historical truth spans systems or manual records, but it is not proof of a market gap.

### Final Billing Report / Contract Closeout

Costpoint also exposes a Final Billing Report showing project-level:

- contract value;
- funded value;
- total billed amount;
- final invoice number/date/amount;
- final payment date;
- payment status.

Source:
- https://help.deltek.com/product/Costpoint/8.2/GA/CTMCNTR_Final_Billing_Report.html

Therefore GovMargin must never market itself as though established GovCon ERP products lack billing/closeout reconciliation.

## Consulting substitutes

GovCon accounting/advisory firms already perform much of the underlying work manually, including:

- incurred-cost submissions;
- provisional/final indirect-rate work;
- billing/invoice support;
- final-rate and closeout accounting;
- voucher review;
- DCAA support.

Examples validated in this research slice include Redstone Government Consulting, GRF CPAs & Advisors and Aprio.

This means the commercial comparison is not "GovMargin versus nothing." It is:

**internal GovCon finance + ERP + spreadsheet + accountant/consultant**

versus

**independent cross-system forensic reconstruction + evidence lineage + prioritized human-review workflow.**

## Surviving differentiation tests

GovMargin survives only if real pilots prove one or more of these advantages:

1. **Independent cross-system truth** — reconstructs history across Costpoint, Unanet, QuickBooks, migrations, manual invoices and bank/payment records without requiring ERP replacement.
2. **Historical forensic scope** — finds discrepancies that ordinary current-state ERP reports do not surface because source truth sits outside the active system.
3. **Evidence lineage** — every candidate/payable ties contract version, clause, rate agreement, source transaction, prior billing and payment evidence together.
4. **False-positive controls** — funding, ceilings, allowability, releases and final-rate status block false receivables deterministically.
5. **Symmetric economics** — payables/overbilling remain first-class results rather than being suppressed by recovery incentives.
6. **Review efficiency** — reduces qualified accountant/counsel time by delivering a smaller, pre-reconciled evidence pack.
7. **Portfolio/M&A overlay** — provides one independent rights/exposure schedule across acquired entities and heterogeneous systems.
8. **Continuous monitoring** — detects emerging earned/billed/paid drift without replacing the system of record.

If pilots do not show meaningful advantage on these dimensions, GovMargin should be rejected, narrowed or merged into a broader recovery platform.

## Claims GovMargin must not make

Do not claim:

- "ERPs do not detect underbilling";
- "Costpoint cannot reconcile claimed versus billed";
- "GovCon consultants only do compliance";
- "there is no existing over/under-billing workflow";
- "GovMargin invented final-rate reconciliation."

## Current white-space conclusion

A standalone product clearly matching the full proposed combination of **independent multi-ERP historical ingestion + source/effective-dated rules + expected economics + billed/paid reconstruction + symmetric recovery/payable workflow + evidence pack** was not identified in this search slice.

That conclusion remains **provisional**. Costpoint and specialist consulting cover substantial portions of the workflow, so defensibility must be demonstrated through real cross-system cases and delivery economics rather than feature checklists.
