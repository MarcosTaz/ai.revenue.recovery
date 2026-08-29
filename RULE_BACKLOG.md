# GovMargin regulatory rule backlog

Current canonical reference snapshot: **FAR FAC 2026-01, effective 2026-03-13**, unless a contract-specific historic clause/version controls. A current FAR page is never back-applied automatically to an older contract.

The backlog is ordered by false-recovery risk, not by breadth.

## P0 — required before a real cost-reimbursement pilot is called pilot-ready

### FAR 31.201-2 — Determining allowability

Source: https://www.acquisition.gov/far/31.201-2

Engine requirement:
- represent the conjunctive allowability gates: reasonableness, allocability, applicable CAS/GAAP treatment, contract terms and Part 31 limitations;
- require supporting records;
- never equate accounting expense with allowable contract cost.

Status: **TEXT VERIFIED / GENERAL RULE NOT YET EXECUTABLE AS A COMPLETE COST-PRINCIPLE ENGINE**.

### FAR 31.201-3 — Determining reasonableness

Source: https://www.acquisition.gov/far/31.201-3

Engine requirement:
- default to `REQUIRES_REVIEW` unless the relevant reasonableness evidence/test is expressly supported;
- never attach a presumption of reasonableness merely because the contractor incurred the cost.

Status: **TEXT VERIFIED / REVIEW-GATED IMPLEMENTATION REQUIRED**.

### FAR 31.201-4 — Determining allocability

Source: https://www.acquisition.gov/far/31.201-4

Engine requirement:
- support specific-contract allocation;
- proportional shared-benefit allocation;
- necessary-overall-operation allocation only when evidence supports the relationship;
- preserve cost-object lineage.

Status: **TEXT VERIFIED / CORE `SupportState` EXISTS / DETAILED TESTS REQUIRED**.

### FAR 52.232-20 — Limitation of Cost

Source: https://www.acquisition.gov/far/52.232-20

Applicability source: https://www.acquisition.gov/far/32.706-2

Engine requirement:
- clause-applicability gate;
- estimated-cost ceiling;
- notice/evidence state;
- no automatic reimbursement above the applicable estimated cost;
- legal review for disputed exceptions, notice or waiver theories.

Status: **TEXT VERIFIED / GENERIC FUNDING-CEILING SAFEGUARD EXISTS / CLAUSE-SPECIFIC RULE REQUIRED**.

### FAR 52.232-22 — Limitation of Funds

Source: https://www.acquisition.gov/far/52.232-22

Applicability source: https://www.acquisition.gov/far/32.706-2

Engine requirement:
- allotted-funds ledger by effective contract/order version;
- period/items covered by the allotment where applicable;
- no candidate above supported available funding without review;
- distinguish added funding from additional entitlement.

Status: **TEXT VERIFIED / GENERIC FUNDING SAFEGUARD EXISTS / CLAUSE-SPECIFIC RULE REQUIRED**.

### FAR 52.216-7 — Allowable Cost and Payment

Source: https://www.acquisition.gov/far/52.216-7

Current executable entries:
- `FAR_52_216_7_D2V_UPDATE_BILLINGS`
- `FAR_52_216_7_D5_COMPLETION_VOUCHER`
- `FAR_52_216_7_E_BILLING_RATE_ADJUSTMENT`

Still required:
- historical clause versions;
- final-rate settlement evidence model;
- completion-voucher timing extensions;
- contract-specific exceptions/alternates;
- integration with final-payment/release evidence.

Status: **CORE EXECUTABLE / HISTORIC VERSION COVERAGE INCOMPLETE**.

## P1 — T&M / labor-hour module, explicitly separate from the initial CPFF engine

### FAR 16.307 — clause applicability

Source: https://www.acquisition.gov/far/16.307

Critical invariant:
- 52.216-7 applies to cost-reimbursement contracts;
- for applicable T&M contracts it operates with 52.232-7 only for the actual-cost materials portion;
- 52.216-7 does **not** apply to labor-hour contracts.

Status: **TEXT VERIFIED / MUST BECOME CONTRACT-CLASSIFIER GUARD BEFORE T&M/LH RELEASE**.

### FAR 52.232-7 — Payments under T&M and Labor-Hour Contracts

Source: https://www.acquisition.gov/far/52.232-7

Required dedicated engines:
- labor category qualification;
- prescribed hourly rate × supported direct labor hours;
- subcontractor/affiliate labor treatment where clause text applies;
- materials/ODC actual-cost treatment;
- applicable indirect expenses for materials;
- payment/withhold and invoice reconciliation.

Status: **NOT IMPLEMENTED; T&M/LH LABOR RECOVERY MUST NOT USE THE 52.216-7 INDIRECT TRUE-UP ENGINE**.

## P1 — closeout / procedural safeguards

Required source-linked rule objects for:
- FAR 42.705 final indirect rate settlement process;
- FAR 4.804 closeout prerequisites;
- FAR 33.206 claim-accrual/timing review trigger;
- FAR 33.207 certification trigger for claims above the applicable threshold;
- contract-specific release/final-payment language and reservations.

Status: **DOCUMENTED / PARTIAL SAFEGUARDS EXIST / LEGAL-REVIEW ROUTING REQUIRED**.

## P2 — cost-category depth

Add only after the P0 gates work on real pilot data:
- compensation;
- travel;
- selected professional/service costs;
- subcontracts;
- materials;
- related-party / intercompany costs;
- expressly unallowable categories;
- agency-specific supplements and DFARS clauses actually present in target contracts.

Do not build a generic “AI says allowable” classifier. Each cost rule needs source, version, applicability, exclusions, evidence requirements and a deterministic/review-gated test.

## Version-control invariant

Every production rule must record:

`SOURCE → SECTION → SOURCE VERSION → EFFECTIVE DATE → CONTRACT/CLAUSE APPLICABILITY → TEST → EXCLUSIONS → REQUIRED EVIDENCE → REVIEW STATE`.

If any link is unresolved, output `UNKNOWN` or `REQUIRES_REVIEW`, never a recovery assertion.
