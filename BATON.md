# BATON — Recovery Radar

MISSION: customer program cancellation / severe volume reduction → stranded exposure → contractual/commercial basis → independently reviewed evidence → defensible supplier claim pre-audit → review → settlement → verified payment.

REPOSITORY: `MarcosTaz/ai.revenue.recovery`
BRANCH: `recovery-radar/program-cancellation-claims`
VERSION: `v0.2.1`
BASE MAIN: `e9bce10a907b3c79b8702199e2cd78803a64c6d6`
MAIN: untouched by this Factory lane.

BUSINESS_STATE: `SIGNAL / HIGH COMPETITIVE COLLISION / WTP UNKNOWN / COMMERCIAL SUCCESS UNPROVEN`.

TERMINAL_STATE: `T1 — PILOT CAPABLE`, restricted to `CONTROLLED_ASSISTED_HISTORICAL_PILOT`.
NEXT_TERMINAL: `T2 — REAL-CASE VALIDATED`.
T2_MEASUREMENT_INFRA: `READY_LOCAL / REAL_CASE_NOT_RUN`.
ACQUISITION_PREP: `READY / NOT SENT`.

T1 does not mean production SaaS, legal autonomy, external claim submission, buyer acceptance, willingness to pay, settlement or recovered cash. T2 cannot be promoted by a synthetic fixture, caller-selected case label, scorecard field or free-text WTP note.

SURVIVING WEDGE: **supplier-side cancellation-claim pre-audit before OEM scrutiny** for customer program cancellation / severe volume reduction, especially stranded E&O / raw material / WIP / finished goods / tooling / NRE / supplier commitments. Do not broaden into generic AP recovery, warranty recovery or generic planning evidence.

DONE — PRODUCT:
- deterministic event / exposure / entitlement / evidence / claim / settlement / payment model;
- exposure != entitlement != claimability != settlement != payment;
- tenant-scoped SQLite persistence for events, exposures, entitlements, evidence metadata/hashes, reviews, claims, payments and audit;
- mitigation and prior-reimbursement deductions;
- ownership fail-closed handling;
- duplicate economic-loss and disguised duplicate-economic-representation protection;
- mixed-currency separation; no scalar EUR+USD style aggregation; mixed-currency case creation fails closed;
- non-finite/extreme numeric fail-closed handling;
- zero / partial / full recovery synthetic cases and broad adversarial portfolio;
- structured claim package with calculation trace, evidence lineage, uncertainty, missing-evidence actions and draft-claim output;
- missing-evidence actions preserve obtainability as UNKNOWN rather than inventing probability;
- settlement/payment workflow with `SETTLED != PAID`;
- local API-key authentication, tenant scope and role derived from credential;
- random one-time API tokens, derived stored secrets, revocation and workspace-scoped roles;
- reviewer cannot source-write, create claims, submit, settle or record payment;
- same actor cannot create evidence/entitlement and then independently verify it under another key/role;
- raw evidence bytes are not persisted; evidence identity/metadata/content hashes are persisted;
- documentary disagreements and contract-version/source ambiguity fail closed;
- registered + independently verified evidence gate;
- independently verified entitlement interpretation gate;
- canonical deterministic package export with SHA-256 manifest, atomic fsync write, post-write verification and tamper detection;
- verified SQLite backup with quick-check, FK check and whole-DB truth digest;
- rollback, DB-lock, concurrency/retry, corrupted-backup and interrupted-write coverage;
- schema compatibility/version gate; unknown newer schema refuses startup; older schema requires explicit migration;
- strict `RECOVERY_RADAR_PILOT_BUNDLE_V1` loader with size/type/enum/path controls and hashes derived from concrete local evidence bytes;
- atomic pilot-bundle ingestion; exact retry idempotent;
- CLI: bootstrap, issue-key, import-bundle, review-evidence, review-entitlement, package, export, create-case, score-historical;
- deterministic correctness acceptance for 2,000 claim lines.

DONE — T2 MEASUREMENT:
- strict `RECOVERY_RADAR_GROUND_TRUTH_V1` parser;
- explicit case origin + ground-truth completeness;
- FP/FN, state mismatch, currency mismatch, signed/absolute value error and operational metrics;
- WTP always remains `UNKNOWN_EXTERNAL` inside the scorecard; free-text WTP reference is only `RECORDED_NOT_INDEPENDENTLY_VERIFIED`;
- synthetic input classified `NON_REAL_CASE_MEASUREMENT_ONLY`;
- real-case label classified only `REAL_CASE_MEASUREMENT_INPUT`, not proof of authorization or T2;
- `terminal_promotion=NOT_INFERRED_FROM_SCORECARD`;
- final scorecard metadata SHA-bound and atomically exported as `RECOVERY_RADAR_T2_SCORECARD_V1`;
- authenticated CLI→persisted analysis→ground truth→scorecard-file path tested end-to-end;
- copyable pilot-bundle and ground-truth templates are regression-tested against current parsers;
- default ground-truth template starts `case_origin=UNKNOWN`, `ground_truth_complete=false`, disposition `UNKNOWN`.

DONE — PILOT EXECUTION / ACQUISITION PREP:
- `PILOT_START_HERE.md` = single operator path;
- `PILOT_RUNBOOK.md` = controlled historical pilot + T2 protocol;
- `PILOT_ACQUISITION.md` = evidence-backed target/qualification plan;
- `PILOT_OUTREACH_DRAFTS.md` = Dauch/Magna/Dana messages, explicitly NOT SENT;
- `PILOT_OFFER.md` = initial **€4,500 ex VAT fixed-scope historical-case pilot** hypothesis; unvalidated price;
- `PILOT_ONE_PAGER.md` = buyer-facing explanation;
- `PILOT_DATA_REQUEST.md` = minimum authorized historical dataset;
- `PILOT_DATA_HANDLING.md` = honest local confidentiality/security boundary with no SOC2/encryption-at-rest/production-IAM claims;
- `examples/pilot-bundle-template.json` and `examples/ground-truth-template.json` = onboarding templates.

CURRENT TARGET ORDER:
1. **Dauch / former AAM — closed e-Beam cancellation claim**;
2. **Magna — closed North American EV cancellation/reduction recovery case**;
3. **Dana — closed customer-cancelled / severe-volume-decline EV program**.

DAUCH PUBLIC-TRUTH BOUNDARY:
- 2024: approximately US$70M of balance-sheet assets associated with the terminated e-Beam program and public belief that the full amount was recoverable, while ultimate recovery remained uncertain;
- January 2026: final settlement; approximately US$28M expected reimbursement of capitalized engineering/design/development costs; additional public write-offs were recorded;
- **do not describe this as a proven “US$70M claim → US$28M settlement” haircut**. The US$70M was not disclosed as a line-level original claim amount and the public settlement/accounting figures are not proven apples-to-apples without authorized internal records.

PRODUCT_TRUTH:
A reference string is never proof. Required evidence must be registered, correctly scoped and currently VERIFIED by an independent reviewer; related entitlement interpretations must also be independently VERIFIED. `CLAIMABLE` is an internal economic/evidence workflow conclusion, not legal certainty, customer acceptance, settlement or cash. `PAID` requires evidenced payments reconciling to settlement.

T2_TRUTH:
The application constructs reproducible measurement artifacts but cannot decide that a real case validates the product. T2 requires Factory review of authorized real/historical evidence and absence of unresolved material truth-integrity failures. WTP, customer acceptance and recovered cash remain separate external facts.

SECURITY_TRUTH:
Local auth/tenant/reviewer boundaries are implemented and tested. Raw evidence stays in the operator-controlled directory; SQLite stores normalized source truth, evidence metadata/hashes, review/workflow/audit state. Recovery Radar itself does not currently claim application-level database encryption, SSO, MFA, managed-secret-vault integration, public-network transport security, SOC2/ISO certification or production hosting security.

LAST EXACT GREEN:
`ef79d948f8ac14edb000ff8f0d32bbfdb3d9484c` — GitHub Actions SUCCESS; **149 passed in 33.26s** on Python 3.13.15.

CURRENT_HEAD_STATE:
This BATON-only commit advances HEAD beyond `ef79d948...`; exact-current-head CI must be observed before the BATON commit itself is called GREEN. Any regression becomes ACTIVE immediately.

P0/P1:
No known unresolved P0/P1 in the covered local assisted-pilot + T2-measurement surface at the last exact GREEN. This does not establish absence across production hosting/IAM or unknown real supplier data. Any material historical-pilot failure becomes ACTIVE immediately.

COMPETITION / KILL TEST:
- SupplyWhy materially collides with automotive supplier claim recovery around demand changes, inventory/cost exposure and evidence/recovery review;
- TRIGO materially collides with evidence-based cancellation claim auditing and shows that physical/on-site verification can be material;
- Stellantis public supplier-claim audit roles prove an adversarial OEM audit function;
- public automotive terms demonstrate timing/evidence/category/ownership/tooling/audit constraints.

Generic “supplier claim evidence” positioning is killed. The narrower supplier-side **pre-audit before OEM scrutiny** hypothesis survives but commercial differentiation/WTP remains unproven.

ACTIVE:
1. observe exact-current-head CI for this BATON commit;
2. if RED, repair immediately;
3. if GREEN, safe internal T1/T2/acquisition preparation is materially complete and ACTIVE becomes `WAIT_FOR_EXTERNAL_AUTHORIZATION_OR_AUTHORIZED_REAL_CASE_DATA`.

NEXT — WHEN EXTERNALLY AUTHORIZED:
- use prepared Dauch-first outreach or another explicitly authorized route;
- qualify closed historical status and data authority before requesting files;
- issue `PILOT_DATA_REQUEST.md` only after participation is authorized;
- run `import-bundle → independent review → package/export → independent ground truth → score-historical`;
- measure false positives/negatives, reviewer corrections, evidence usefulness, time-to-package and value error;
- compare historical claim/settlement/payment only as a separate observed outcome;
- any material miss becomes P0/P1/P2 repair before T2 promotion;
- test the €4,500 paid-pilot hypothesis only through actual budget/price action; free pilot remains learning-only.

WAIT:
- explicit authorization for external outreach/contact-form submission;
- authorized real supplier/customer historical data;
- external claim submission / supplier or OEM communication;
- negotiation or settlement action;
- production deployment / secrets / provider configuration;
- spending;
- independently verified WTP / paid-pilot evidence;
- merge to `main` without explicit authorization.

REAL_WORLD_TRUTH:
REAL_CASES = 0
PAYING_CUSTOMERS = 0
VERIFIED_RECOVERY = €0
RECOVERY_RADAR_REVENUE_RECEIVED = €0
WTP = UNKNOWN
OUTREACH_SENT = 0

RESUME_AT:
`EXACT CURRENT HEAD CI → REPAIR IF RED → IF GREEN WAIT FOR EXTERNAL AUTHORIZATION OR AUTHORIZED REAL CASE → EXECUTE PREPARED PILOT PATH`.
