# GovMargin validation — 2026-08-29

## Decision

Status: **NARROWED_VALIDATION_WITH_MATERIALITY_OPEN**.

The economic mechanism is source-proven, but stronger incumbent evidence now requires a narrower thesis. GovMargin must prove incremental value over ordinary GovCon ERP + finance/accounting workflows, especially where historical truth is fragmented across systems, migrations, manual invoices or acquired entities.

Current thesis score: **79 / 100**.

## Primary-source facts

1. FAR 52.216-7(d) requires final annual indirect rates and requires contractors to update billings after final-rate settlement. FAR 52.216-7(e) makes billing rates provisional and adjustable to prevent substantial overpayment or underpayment.
2. FAR 52.216-7(h) provides a stronger final-payment anchor: after approval of the completion invoice/voucher and compliance with contract terms, remaining supported allowable costs/unpaid fee are reconciled for final payment, while refunds/rebates/credits and other amounts owed to the Government remain relevant. This supports symmetric contractor-receivable / Government-payable reconciliation, not one-way recovery marketing.
3. FAR 42.704 directs billing rates to approximate anticipated final rates and permits prospective or retroactive revision to prevent substantial overpayment or underpayment.
4. FAR 42.705 requires a completion invoice/voucher after final annual indirect rates are settled and permits unilateral Government determination if the contractor fails to submit it on time.
5. FAR 4.804 requires settlement of prior-year indirect rates, contract audit, final invoice submission and funds review before closeout for relevant contracts.
6. FAR 33.206 generally requires contractor claims to be submitted within six years after accrual; FAR 33.207 requires contractor certification for claims over $100,000.
7. FAR 3.4 restricts contingent fees tied to soliciting or obtaining Government contracts. That does not itself resolve post-award recovery compensation.
8. FAR 31.205-33 separately states that professional/consultant service costs are generally allowable only when reasonable and not contingent upon recovery of the costs from the Government. GovMargin therefore does not promise that its fees are reimbursable contract costs.
9. 31 U.S.C. § 3727 restricts assignment of claims/interests in claims against the United States subject to statutory conditions/exceptions. GovMargin therefore does not take ownership of or payment rights in Government claims without qualified legal review.
10. FAR 16.307 limits FAR 52.216-7 applicability: cost-reimbursement contracts are the primary wedge; for noncommercial T&M it applies with FAR 52.232-7 only to the actual-cost materials portion. FAR 52.216-7 does not apply to labor-hour contracts.
11. FAR 31.201-2 makes allowability depend on reasonableness, allocability, applicable CAS/GAAP treatment, contract terms and Part 31 limitations. An incurred accounting expense is not automatically billable contract cost.
12. FAR 52.232-20 and 52.232-22 create distinct estimated-cost/allotted-funds safeguards. Contract-specific notice thresholds/windows and written Contracting Officer actions must be evidenced before any excess-cost theory is considered.
13. FAR 42.708 permits quick closeout only under defined conditions and warns that special contract provisions can limit recovery of otherwise allowable indirect costs. Quick-closeout rates are contract-specific and not a precedent for other contracts.

## Problem / materiality evidence

- DCAA ICE/incurred-cost workflows require reconciliation of books, direct costs, allocation bases and cumulative claimed/billed amounts.
- Public court records document seven-figure indirect-rate/funding disputes, including the Reliability and Performance Technologies matter. These prove material exposure can exist; disputed claims are not counted as recovered cash.
- Public Government guidance recognizes that contractors may fail to submit final vouchers because of lack of accounting staff, insufficient financial records or a credit balance due to the Government. This supports operational reconciliation risk but does not establish underbilling frequency.
- Redstone practitioner material warns that signing a release after understating a final voucher can eliminate later recovery opportunities. This is directional practitioner evidence, not representative statistics.

## Competition kill-test — material correction

### Deltek Costpoint is a stronger substitute than previously recorded

Deltek documentation states that Schedule I — Cumulative Direct and Indirect Cost Claimed & Billed can identify:

- physically complete contracts for closeout; and
- contracts that may require billing adjustments because of over/under-billing.

Deltek's Final Billing Report also includes contract/funded value, total billed, final invoice amount/date, final payment date and payment status.

Therefore GovMargin must not claim that GovCon ERP products lack claimed-versus-billed or final-payment reconciliation.

Deltek documentation also notes assumptions/limitations around invoices being computed/posted in Costpoint and manual invoice metadata. That creates a possible independent cross-system wedge but is not proof of customer demand.

### Other strong substitutes

- DCAA ICE / Contractor Submission Portal: official incurred-cost/PBR submission infrastructure.
- GovCon accountants/advisers such as Redstone, GRF and Aprio: indirect rates, incurred-cost submissions, billing, DCAA support and closeout.
- Government-contract counsel such as PilieroMazza: claims, appeals and financial/legal recovery mechanics.

The actual comparison is therefore:

**internal GovCon finance + ERP + spreadsheets + specialist accountant/counsel**

versus

**independent cross-system forensic reconstruction + deterministic controls + evidence lineage + prioritized qualified review.**

## Surviving wedge

Freeze the pilot wedge as:

**Independent cross-system historical final-rate / closeout economic assurance for cost-reimbursement / CPFF contracts where active ERP reports may not contain the complete historical truth.**

Priority trigger cases:

1. ERP/accounting migration;
2. manually issued or externally generated invoices;
3. acquired contractor / PE portfolio with heterogeneous systems;
4. controller/CFO turnover and institutional-knowledge loss;
5. aged closeouts with settled rates but fragmented billing/payment records;
6. historical data spread across Costpoint/Unanet/QuickBooks/spreadsheets/bank evidence;
7. need for independent evidence pack before qualified accountant/counsel review.

The product must prove one of these cases creates material incremental value over the incumbent workflow. If not, reject/narrow/merge.

## Initial ICP — narrowed for pilot discovery

Prioritize contractors with:

- roughly $5M–$50M federal-contract revenue;
- cost-reimbursement / CPFF contracts containing evidenced FAR 52.216-7;
- settled-final-rate or closeout history;
- at least one cross-system/migration/manual-history trigger;
- one to five historical contracts/orders suitable for controlled pilot reconstruction;
- finance leadership willing to validate both favorable and unfavorable findings.

Buyer: CFO / Controller / GovCon Finance Lead. Secondary: PE operating/diligence team.

Deprioritize ordinary Costpoint environments where current Schedule I / closeout reporting plus existing GovCon accounting support already gives complete trusted historical truth.

## Contract-type ranking

1. **Cost-reimbursement / CPFF** with 52.216-7, settled final rates, reconstructable historical billings/payments and cross-system trigger.
2. **T&M actual-cost materials portion** only with clause-specific 52.216-7 + 52.232-7 support.
3. **T&M labor** only after a dedicated 52.232-7 hours/category/rate engine exists.
4. **Labor-hour** only after dedicated 52.232-7 logic; never route through 52.216-7 final-indirect labor theory.
5. Other flexibly priced/incentive/redeterminable contracts only after their own rule engines are proven.
6. Ordinary firm-fixed-price is not an initial indirect-rate recovery wedge.

## Compensation / professional boundary

Launch posture is fixed-fee audit + fixed subscription only.

Disabled pending qualified legal/accounting review:

- percentage-of-recovery compensation;
- assignment/ownership of Government receivables/claims;
- claim certification/representation;
- legal opinions;
- CPA attestations;
- representations that GovMargin's fee is itself an allowable Government-contract cost.

See `LEGAL_BOUNDARY.md`.

## Gate state

- Gate 1 Underbilling problem proven: **PARTIAL PASS** — mechanism and material cases proven; representative frequency open.
- Gate 2 Recoverable value proven: **PARTIAL PASS** — final-rate/final-payment mechanism proven; representative collected-value distribution open.
- Gate 3 Competition mapped: **PASS WITH MATERIAL INCUMBENT CORRECTION**.
- Gate 4 Recovery-first wedge survives: **NARROW PROVISIONAL PASS** — only independent cross-system historical assurance survives.
- Gate 5 ICP selected: **PASS FOR NARROW PILOT DISCOVERY**.
- Gate 6 Legal/regulatory boundary defensible: **PASS FOR FIXED-FEE ANALYTICAL PILOT, QUALIFIED REVIEW STILL REQUIRED**.
- Gate 7 Rule engine: **CORE PASS FOR INITIAL 52.216-7 / 52.232-20 / 52.232-22 WEDGE; broader universe open**.
- Gate 8 Calculation engine: **CORE PASS FOR INITIAL WEDGE** — settled indirect true-up, costs, fee, ceilings/funding, voucher/final-payment/payment symmetry are deterministic.
- Gate 9 Synthetic portfolio: **PASS SUBJECT TO CURRENT-HEAD CI** — A–Z and expanding red-team suite exist; every new HEAD must remain green.
- Gate 10 Pilot-ready: **NOT PASSED** — real identity/storage/scanner/deployment and real-contractor validation remain external/infrastructure gaps.

## Current commercial truth

- no real contractor processed;
- no paid audit;
- no verified collected recovery;
- no validated average recovery percentage;
- no validated CAC or sales cycle;
- no signed channel partner;
- $7,500 design-partner price is a hypothesis;
- unit economics are modeled, not observed.

## Source registry additions

- https://www.acquisition.gov/far/52.216-7
- https://www.acquisition.gov/far/42.704
- https://www.acquisition.gov/far/42.705
- https://www.acquisition.gov/far/42.708
- https://www.acquisition.gov/far/subpart-4.8
- https://www.acquisition.gov/far/33.206
- https://www.acquisition.gov/far/33.207
- https://www.acquisition.gov/far/subpart-3.4
- https://www.acquisition.gov/far/31.205-33
- https://www.acquisition.gov/far/16.307
- https://www.acquisition.gov/far/52.232-7
- https://www.acquisition.gov/far/31.201-2
- https://www.acquisition.gov/far/31.201-3
- https://www.acquisition.gov/far/31.201-4
- https://www.acquisition.gov/far/52.232-20
- https://www.acquisition.gov/far/52.232-22
- https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title31-section3727
- https://education.deltek.com/web/content/Costpoint/tech%20guides%20for%20ask%20dela/costpoint_bi_team_content_guide.pdf
- https://help.deltek.com/product/Costpoint/8.2/GA/CTMCNTR_Final_Billing_Report.html
- https://redstonegci.com/consulting/operational-support-services/accounting-services-support/
- https://www.grfcpa.com/people/paul-h-calabrese/
- https://www.aprio.com/people/brian-bender/
- https://www.pilieromazza.com/contract-claims-101-financial-fundamentals-part-3/

## Materiality work still required

Do not publish an average recovery percentage. The next empirical proof must come from controlled real design-partner audits that distinguish:

- variance visible in the customer's ordinary ERP/accountant workflow;
- incremental variance surfaced only by independent cross-system reconstruction;
- gross calculation difference;
- qualified finding;
- valid customer billing/true-up action;
- cash actually collected or payable corrected.
