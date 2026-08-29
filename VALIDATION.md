# GovMargin validation — 2026-08-29

## Decision

Status: **VALIDATED_WITH_MATERIALITY_OPEN**.

The economic mechanism is real and source-proven. The broad thesis is not yet entitled to claim a representative underbilling frequency or average recovery size.

## Primary-source facts

1. FAR 52.216-7(d) requires final annual indirect rates and requires contractors to update billings after final-rate settlement. FAR 52.216-7(e) states billing rates are provisional and may be revised to prevent substantial overpayment or underpayment.
2. FAR 42.704 directs billing rates to approximate anticipated final rates and permits prospective or retroactive revision to prevent substantial overpayment or underpayment.
3. FAR 42.705 requires a completion invoice/voucher after final annual indirect rates are settled.
4. FAR 4.804 requires settlement of prior-year indirect rates, contract audit, final invoice submission and funds review before closeout for relevant contracts.
5. FAR 33.206 generally requires contractor claims to be submitted within six years after accrual; FAR 33.207 requires contractor certification for claims over $100,000.
6. FAR 3.4's contingent-fee restriction is expressly scoped to soliciting or obtaining Government contracts. This does not by itself validate a recovery contingency fee; state professional-practice, claims-representation and ethics rules still require qualified review.
7. The False Claims Act creates material downside for knowingly false payment requests and knowingly avoiding repayment obligations, reinforcing symmetric underbilling/overbilling treatment.
8. FAR 16.307 limits the applicability of FAR 52.216-7: it applies to cost-reimbursement contracts and, for noncommercial T&M contracts, only in conjunction with FAR 52.232-7 for the actual-cost materials portion. FAR 52.216-7 does **not** apply to labor-hour contracts. This correction narrows the initial wedge and prevents a false final-indirect-rate theory from being applied to T&M/LH labor.
9. FAR 31.201-2 makes allowability depend on reasonableness, allocability, applicable CAS/GAAP treatment, contract terms and Part 31 limitations. FAR 31.201-3 and 31.201-4 separately define reasonableness and allocability. A booked cost therefore cannot be promoted to billable entitlement merely because it was incurred.
10. FAR 52.232-20 and 52.232-22 create distinct cost/funding limitations for relevant cost-reimbursement contracts; these limitations must be contract-applicability checked before asserting additional reimbursement.

## Problem evidence

- DCAA's ICE model and incurred-cost submission framework require reconciliation of books, direct costs, allocation bases and cumulative claimed/billed amounts.
- Deltek Costpoint includes incurred-cost schedules, provisional indirect billing, burden calculations, ceilings and cumulative claimed/billed reporting. This proves the workflow is important enough to be embedded in incumbent ERP tooling.
- Redstone Government Consulting warns contractors that if the final voucher understates amounts due and a release of claims is signed, those amounts may be lost.
- Practitioner guidance also reports recurring reconciliation failures between cumulative incurred costs and final vouchers. This is directional evidence, not a frequency estimate.

## Competition kill-test

### Strong substitutes

- Deltek Costpoint: deep GovCon ERP, provisional billing, indirect-rate computation, ICS schedules, ceilings and billing.
- DCAA ICE / Contractor Submission Portal: official incurred-cost and PBR submission infrastructure; compliance/submission, not contractor-side historical recovery analytics.
- GovCon accounting/consulting firms such as Redstone and CPA firms: manually perform incurred-cost, rate, audit and closeout work.

### Surviving wedge

GovMargin must not compete as another accounting system. The surviving wedge is:

**Independent, multi-ERP, recovery-first historical economic reconciliation overlay**

that ingests contract/modification/rate/accounting/billing/payment evidence, deterministically reconstructs expected economics, proves lineage, surfaces both receivables and payables, and produces a human-review recovery/closeout pack.

No strong product was found in this validation slice that clearly combines historical contract data + accounting data + regulatory applicability + expected billing + actual billing/payment + recovery workflow as an independent overlay. This is a provisional white-space conclusion, not proof of absence.

## Initial ICP — frozen for pilot discovery

Prioritize contractors with:

- roughly $5M–$50M federal-contract revenue;
- multiple cost-reimbursement / CPFF contracts with FAR 52.216-7 exposure and settled-final-rate or closeout history;
- optionally T&M exposure, but only through the contractually applicable 52.232-7 / actual-cost-material paths rather than by importing the cost-reimbursement true-up theory into labor billing;
- at least two fiscal years with final-rate, final-voucher or closeout exposure;
- enough complexity to create reconciliation risk but without a large specialized GovCon finance team;
- one trigger: ERP/accounting migration, CFO/controller turnover, acquisition, unresolved final indirect rates, aged closeouts, or large unbilled balances.

Buyer: CFO / Controller / GovCon Finance Lead. Secondary: PE operating or diligence team.

## Contract-type ranking

1. **Cost-reimbursement / CPFF** contracts containing FAR 52.216-7, with settled final rates and reconstructable cumulative billings.
2. **T&M actual-cost materials portion** where FAR 52.216-7 applies in conjunction with FAR 52.232-7 and the contract evidence supports the specific material/indirect treatment.
3. **T&M labor billing** under FAR 52.232-7 as a separate labor-rate/category/hours reconciliation module; do not use the 52.216-7 final-indirect-rate engine for labor.
4. **Labor-hour contracts** only after a dedicated 52.232-7 labor engine exists; 52.216-7 does not apply.
5. Other flexibly priced / incentive / redeterminable contracts only after their own clause-specific engines are proven.
6. Ordinary firm-fixed-price is not an initial indirect-rate recovery wedge.

## Gate state

- Gate 1 Underbilling problem proven: **PARTIAL PASS** — mechanism + practitioner evidence; representative frequency open.
- Gate 2 Recoverable value proven: **PARTIAL PASS** — contractual payment/adjustment mechanism proven; representative dollar distribution open.
- Gate 3 Competition mapped: **PASS for initial slice**.
- Gate 4 Recovery-first wedge survives: **PROVISIONAL PASS**.
- Gate 5 ICP selected: **PASS for pilot discovery**.
- Gate 6 Legal/regulatory boundary defensible: **PASS WITH QUALIFIED-REVIEW REQUIREMENTS**.
- Gate 7 Rule engine: **IN PROGRESS** — source-linked/effective-dated core exists; broader clause universe remains open.
- Gate 8 Calculation engine: **PASS FOR INITIAL SETTLED-INDIRECT-RATE WEDGE / broader engine IN PROGRESS**.
- Gate 9 Synthetic contractor portfolio: **LOCAL PASS A–Z; CURRENT-HEAD CI VERIFICATION REQUIRED**.
- Gate 10 Pilot-ready: **IN PROGRESS / NOT PASSED** — assisted normalized audit, evidence lineage, tenant-scoped import and human review exist; production auth/storage/raw-document workflow, deployment and real-contractor validation remain open.

## Source registry

- https://www.acquisition.gov/far/52.216-7
- https://www.acquisition.gov/far/42.704
- https://www.acquisition.gov/far/42.705
- https://www.acquisition.gov/far/subpart-4.8
- https://www.acquisition.gov/far/33.206
- https://www.acquisition.gov/far/33.207
- https://www.acquisition.gov/far/subpart-3.4
- https://www.acquisition.gov/far/16.307
- https://www.acquisition.gov/far/52.232-7
- https://www.acquisition.gov/far/31.201-2
- https://www.acquisition.gov/far/31.201-3
- https://www.acquisition.gov/far/31.201-4
- https://www.acquisition.gov/far/52.232-20
- https://www.acquisition.gov/far/52.232-22
- https://www.dcaa.mil/Checklists-Tools/ICE-Model/
- https://www.dcaa.mil/Business-Apps/Contractor-Submission-Portal/
- https://help.deltek.com/Products/Costpoint/8.2/GA/ICSReps.html
- https://help.deltek.com/Products/Costpoint/8.2/GA/Billing.html
- https://info.redstonegci.com/blog/how-to-optimize-your-government-contract-closeout-experience

## Materiality work still required

Do not publish an average recovery percentage yet. Next evidence work: public case decisions, contractor disclosures, consultant case studies, and anonymized pilot data that can distinguish gross billing differences from amounts actually recoverable after allowability, allocability, ceilings, funding, prior billing, releases and procedural deadlines.
