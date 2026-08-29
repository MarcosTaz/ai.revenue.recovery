# BATON — Recovery Radar

MISSION: customer program cancellation / severe volume reduction → stranded exposure → contractual/commercial basis → independently reviewed evidence → defensible supplier claim pre-audit → review → settlement → verified payment.

REPOSITORY: `MarcosTaz/ai.revenue.recovery`
BRANCH: `recovery-radar/program-cancellation-claims`
VERSION: `v0.2.2`
BASE MAIN: `e9bce10a907b3c79b8702199e2cd78803a64c6d6`
MAIN: untouched by this Factory lane.
PR: `#2` — Draft / `DO NOT MERGE` without explicit authorization.

BUSINESS_STATE: `SIGNAL / HIGH COMPETITIVE COLLISION / WTP UNKNOWN / COMMERCIAL SUCCESS UNPROVEN`.

TERMINAL_STATE: `T1 — PILOT CAPABLE`, restricted to `CONTROLLED_ASSISTED_HISTORICAL_PILOT`.
NEXT_TERMINAL: `T2 — REAL-CASE VALIDATED`.
T2_MEASUREMENT_INFRA: `READY_LOCAL / SOURCE-SCOPE-BOUND / REAL_CASE_NOT_RUN`.
ACQUISITION_PREP: `READY / NOT SENT`.

T1 does not mean production SaaS, legal autonomy, external claim submission, buyer acceptance, willingness to pay, settlement or recovered cash. T2 cannot be promoted by a synthetic fixture, caller-selected case label, authorization reference, scope hash, scorecard field or free-text WTP note.

SURVIVING WEDGE: **supplier-side cancellation-claim pre-audit before OEM scrutiny** for customer program cancellation / severe volume reduction, especially stranded E&O / raw material / WIP / finished goods / tooling / NRE / supplier commitments. Do not broaden into generic AP recovery, warranty recovery or generic planning evidence.

DONE — PRODUCT:
- deterministic event / exposure / entitlement / evidence / claim / settlement / payment model;
- exposure != entitlement != claimability != settlement != payment;
- tenant-scoped SQLite persistence for source graph, reviews, claims, payments and audit;
- mitigation and prior-reimbursement deductions;
- ownership fail-closed handling;
- duplicate economic-loss and disguised duplicate-economic-representation protection;
- mixed-currency separation; no scalar cross-currency aggregation; mixed-currency claim creation fails closed;
- non-finite/extreme numeric fail-closed handling;
- zero / partial / full recovery synthetic cases and broad adversarial portfolio;
- structured claim package with calculation trace, evidence lineage, uncertainty, missing-evidence actions and draft-claim output;
- missing-evidence obtainability remains UNKNOWN rather than a fabricated probability;
- settlement/payment workflow with `SETTLED != PAID`;
- local token-authenticated application gateway; tenant/role derived from credential;
- random one-time API tokens, derived stored secrets, revocation and workspace-scoped roles;
- reviewer cannot source-write, create claims, submit, settle or record payment;
- source creator cannot independently verify own evidence/entitlement under another key;
- raw evidence bytes not persisted; identity/metadata/content hashes persist;
- documentary disagreements and contract-version/source ambiguity fail closed;
- registered + independently verified evidence gate;
- independently verified entitlement interpretation gate;
- deterministic claim export with SHA-256 manifest, atomic fsync write, post-write verification and tamper detection;
- verified SQLite backup with quick-check, FK check and whole-DB truth digest;
- rollback, DB-lock, concurrency/retry, corrupted-backup and interrupted-write coverage;
- schema compatibility/version gate; future schema refuses startup; older schema requires explicit migration;
- strict `RECOVERY_RADAR_PILOT_BUNDLE_V1` with size/type/enum/path controls and hashes derived from concrete evidence bytes;
- atomic pilot-bundle ingestion; exact retry idempotent;
- CLI commands: bootstrap, issue-key, scope-manifest, import-bundle, review-evidence, review-entitlement, package, export, create-case, score-historical;
- deterministic correctness acceptance for 2,000 claim lines.

DONE — SOURCE PROVENANCE / T2 MEASUREMENT:
- `RECOVERY_RADAR_SOURCE_SCOPE_V1` binds complete normalized event volumes, exposure economics, ownership, mitigation/reimbursement, entitlement support/caps/references and evidence metadata/content hashes;
- source-scope manifest embeds no raw evidence bytes;
- changes to relevant economics or evidence bytes change source-scope SHA;
- source-scope artifact is written atomically and returns both scope SHA and artifact SHA;
- actual human/data-owner authorization remains external truth; `PILOT_AUTHORIZATION_RECORD.md` is not self-authorizing;
- strict `RECOVERY_RADAR_GROUND_TRUTH_V1` parser;
- optional provenance: authorization reference, source-scope SHA and `BLIND / ASSISTED / UNKNOWN` ground-truth method;
- caller-recorded provenance is explicitly not independently verified by the application;
- `case_origin_status=RECORDED_NOT_INDEPENDENTLY_VERIFIED` even when caller selects `REAL_AUTHORIZED_HISTORICAL_CASE`;
- FP/FN, state mismatch, currency mismatch, signed/absolute value error and operational metrics;
- WTP remains `UNKNOWN_EXTERNAL`; free-text WTP reference is only recorded/unverified metadata;
- `terminal_promotion=NOT_INFERRED_FROM_SCORECARD`;
- score-historical reconstructs current persisted source scope and fails with `SOURCE_SCOPE_SHA256_MISMATCH` before writing a scorecard if the recorded scope differs;
- successful scorecard records persisted scope hash/status;
- final scorecard SHA is recomputed after persisted-scope status and all case/provenance metadata are present;
- atomic deterministic `RECOVERY_RADAR_T2_SCORECARD_V1` export;
- synthetic input remains `NON_REAL_CASE_MEASUREMENT_ONLY`;
- copyable templates are regression-tested against current parsers.

DONE — PILOT / ACQUISITION PREP:
- `PILOT_START_HERE.md` single operator path;
- `PILOT_RUNBOOK.md` source-scope-bound controlled pilot protocol;
- `PILOT_PROVENANCE.md` full provenance chain;
- `PILOT_AUTHORIZATION_RECORD.md` human governance checklist/reference;
- `GROUND_TRUTH_PROTOCOL.md` blind/assisted/unknown reference protocol;
- `PILOT_ACQUISITION.md` qualification plan with separate measurement-quality order;
- `PILOT_ROUTING_MATRIX.md` separates case fit from public routing fit;
- `PILOT_OUTREACH_DRAFTS.md` prepared, NOT SENT;
- `PILOT_OFFER.md` initial **€4,500 ex VAT fixed-scope historical-case pilot** hypothesis, unvalidated;
- `PILOT_ONE_PAGER.md`, `PILOT_DATA_REQUEST.md`, `PILOT_DATA_HANDLING.md` prepared;
- parser-aligned pilot and ground-truth templates prepared.

CURRENT T2 MEASUREMENT-QUALITY ORDER:
1. **Dauch / former AAM — closed e-Beam cancellation claim**;
2. **Dee Zee / BrightDrop — only if authorized internal records include a usable historical outcome**;
3. **Magna — one specifically closed North American EV cancellation/reduction recovery case**;
4. **Dana — one closed cancelled/severe-volume-decline case, useful for zero/partial-recovery falsification**.

ROUTING TRUTH:
Do not fabricate a response-probability score. Use only an appropriate verified public route after explicit authorization. Dauch has a suitable general business inquiry. Magna has group/general inquiry. Dana has a business inquiry with a vendor-solicitation caveat. Dee Zee's publicly indexed OEM form is quoting-only and must not be misused. A legitimate warm introduction overrides route order without changing case fit.

DAUCH PUBLIC-TRUTH BOUNDARY:
- public 2024 program-associated ~US$70M balance-sheet assets were not disclosed as a line-level original claim amount;
- January 2026 settlement and ~US$28M expected ED&D reimbursement plus write-offs are not proven apples-to-apples with that ~US$70M figure;
- never describe the public facts as a proven “US$70M claim → US$28M settlement” haircut without authorized internal category-level records.

PRODUCT_TRUTH:
A reference string is never proof. Required evidence must be registered, correctly scoped and currently VERIFIED by an independent reviewer; related entitlement interpretations must also be independently VERIFIED. `CLAIMABLE` is an internal economic/evidence workflow conclusion, not legal certainty, customer acceptance, settlement or cash. `PAID` requires evidenced payments reconciling to settlement.

PROVENANCE_TRUTH:
A source-scope hash verifies modeled dataset identity, not authority or correctness. Authorization reference/case origin/ground-truth method are caller/human recorded and not independently authenticated by the application. Source-scope mismatch blocks scoring. Ground-truth independence and legal data authorization remain external governance facts.

T2_TRUTH:
The application constructs reproducible measurement artifacts but cannot decide that a real case validates the product. T2 requires Factory review of actually authorized real/historical evidence, sufficiently independent ground truth and absence of unresolved material truth-integrity failures. WTP, customer acceptance and recovered cash remain separate external facts.

SECURITY_TRUTH:
Local auth/tenant/reviewer boundaries are implemented and tested. Raw evidence stays in the operator-controlled directory. Recovery Radar does not claim application-level DB encryption, SSO, MFA, managed-secret-vault integration, public-network transport security, SOC2/ISO certification or production hosting security; these are outside T1 controlled local pilot scope.

LAST EXACT GREEN:
`8bd2ed8b80a3d52bccce88661959bbf24a4b1594` — GitHub Actions SUCCESS; **159 passed in 34.00s** on Python 3.13.15.

CURRENT_HEAD_STATE:
v0.2.2 source-provenance/test/documentation commits after `8bd2ed8...` require their own exact-head CI observation. Do not call a newer HEAD GREEN until GitHub Actions confirms it. Any regression becomes ACTIVE immediately.

P0/P1:
No known unresolved P0/P1 at the last exact GREEN. Recent changes specifically harden source-scope drift and self-reported case-origin/provenance truth. Their regression state remains pending until exact-current-head CI succeeds.

COMPETITION / KILL TEST:
- SupplyWhy materially collides with automotive supplier claim recovery around demand changes, inventory/cost exposure and evidence/recovery review;
- TRIGO materially collides with evidence-based cancellation claim auditing and shows physical/on-site verification can be material;
- Stellantis public supplier-claim audit roles prove an adversarial OEM audit function;
- public automotive terms demonstrate timing/evidence/category/ownership/tooling/audit constraints.

Generic “supplier claim evidence” positioning is killed. The narrower supplier-side **pre-audit before OEM scrutiny** hypothesis survives but commercial differentiation/WTP remains unproven.

ACTIVE:
1. observe exact-current-head CI for v0.2.2 provenance/docs/tests;
2. repair immediately if RED;
3. if GREEN, inspect repository one final time for remaining safe internal gaps/TODO/drift;
4. only when none remain does ACTIVE become `WAIT_FOR_EXTERNAL_AUTHORIZATION_OR_AUTHORIZED_REAL_CASE_DATA`.

NEXT — WHEN EXTERNALLY AUTHORIZED:
- use an explicitly authorized appropriate route, starting with Dauch when case/access conditions remain strongest;
- qualify closed historical status and data authority before requesting files;
- issue `PILOT_DATA_REQUEST.md` only after participation is authorized;
- retain actual authorization, freeze source scope, import/review/package/export, freeze independent ground truth, then score;
- measure FP/FN, reviewer corrections, evidence usefulness, time-to-package and value error;
- compare historical claim/settlement/payment only as a separate observed outcome;
- any material miss becomes P0/P1/P2 repair before T2 promotion;
- test the €4,500 price only through actual budget/price action; a free pilot remains learning-only.

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
`EXACT CURRENT HEAD CI → REPAIR IF RED → FINAL INTERNAL DRIFT/TODO AUDIT → WAIT ONLY ON GENUINE EXTERNAL DEPENDENCY`.