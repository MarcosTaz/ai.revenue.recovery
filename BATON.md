# BATON — Recovery Radar

MISSION: customer program cancellation / severe volume reduction → stranded exposure → contractual/commercial basis → independently reviewed evidence → defensible supplier claim pre-audit → review → settlement → verified payment.

REPOSITORY: `MarcosTaz/ai.revenue.recovery`
BRANCH: `recovery-radar/program-cancellation-claims`
BASE MAIN: `e9bce10a907b3c79b8702199e2cd78803a64c6d6`
MAIN SOURCE TRUTH AT RECOVERY: repository contained only `.gitkeep`; no prior Recovery Radar implementation was present in GitHub source.

BUSINESS_STATE: `SIGNAL / HIGH COMPETITIVE COLLISION / WTP UNKNOWN / COMMERCIAL SUCCESS UNPROVEN`.

TERMINAL_STATE: `T1 — PILOT CAPABLE`, restricted to `CONTROLLED_ASSISTED_HISTORICAL_PILOT`.
NEXT_TERMINAL: `T2 — REAL-CASE VALIDATED`.

T1 does not mean production SaaS, legal autonomy, external claim submission, buyer acceptance, willingness to pay, settlement or recovered cash.

SURVIVING WEDGE: **supplier-side cancellation-claim pre-audit** for customer program cancellation / severe volume reduction, especially stranded E&O / raw material / WIP / finished goods / tooling / NRE / supplier commitments. Do not broaden into generic AP recovery, warranty recovery or generic planning evidence.

DONE:
- deterministic event / exposure / entitlement / evidence / claim / settlement / payment model;
- exposure != entitlement != claimability != settlement != payment;
- tenant-scoped persistence for events, exposures, entitlements, evidence metadata/hashes, evidence reviews, entitlement reviews, claim cases, payments and audit events;
- mitigation and prior-reimbursement deductions;
- ownership fail-closed handling;
- duplicate economic-loss and disguised duplicate-economic-representation protection;
- mixed-currency separation; no scalar addition across currencies; mixed-currency case creation fails closed;
- non-finite/extreme numeric input fail-closed handling;
- zero-defensible-claim, partial-recovery, prior-compensation and mitigation cases;
- synthetic/adversarial coverage across raw material, WIP/FG, tooling/NRE, supplier commitments, evidence gaps/conflicts, unsupported/expired representations and failure cases;
- independent arithmetic oracle + claim-line scorer;
- structured claim package with calculation trace, evidence lineage, uncertainty and draft-claim output;
- line-specific missing-evidence actions with proof purpose, holder hint, blocked/value context and obtainability explicitly UNKNOWN;
- settlement/payment workflow with `SETTLED != PAID`;
- evidenced multi-payment records with duplicate/currency/overpayment controls;
- local token-authenticated application gateway; tenant and role derived from credential;
- random one-time API tokens, non-plaintext stored secrets, revocation and workspace-scoped roles;
- reviewer cannot source-write, create claims, submit, settle or record payment;
- same actor cannot create evidence/entitlement and then independently verify it under another key/role;
- SHA-256 evidence metadata registry; raw evidence bytes not persisted;
- wrong tenant/supplier/customer/program and signature/scope controls;
- documentary fact disagreement and contract-version/source ambiguity fail closed;
- registered + independently verified evidence gate;
- independently verified entitlement interpretation gate;
- canonical deterministic package export with SHA-256 manifest, atomic fsync write, post-write verification and tamper detection;
- verified SQLite backup with quick-check, FK check and whole-DB truth digest;
- rollback on interrupted critical writes;
- DB-lock, concurrency/retry, corrupted-backup and interrupted-write adversarial coverage;
- application-schema compatibility/version gate; unknown newer schema refuses startup; older schema requires explicit migration;
- strict `RECOVERY_RADAR_PILOT_BUNDLE_V1` loader with size/type/enum/path controls and content hashes derived from concrete evidence bytes;
- atomic pilot-bundle ingestion: event/exposure/entitlement/evidence/audit commit together or roll back together;
- exact bundle retry idempotency;
- assisted-pilot CLI: bootstrap, issue-key, import-bundle, review-evidence, review-entitlement, package, export, create-case;
- deterministic correctness acceptance for 2,000 claim lines;
- controlled historical-pilot protocol in `PILOT_RUNBOOK.md`.

PRODUCT_TRUTH:
A nonempty evidence-reference string is never proof. For the T1 assisted-pilot application, required evidence must be registered, correctly scoped and currently VERIFIED by an independent reviewer. Related entitlement interpretations must also be independently VERIFIED. Gate failure keeps/returns the line to a non-claimable/review state. `CLAIMABLE` remains an internal economic/evidence workflow conclusion, not legal certainty, settlement or cash. `PAID` requires evidenced payments reconciling to settlement.

CONTRACT_VERSION_TRUTH:
The system does not infer that a later contract or amendment automatically supersedes an earlier one. Competing records for the same source identity fail closed as ambiguous until a human commercial/legal reviewer resolves applicability outside the deterministic engine.

SECURITY_TRUTH:
Local application auth/tenant boundary is implemented and tested. Production IAM, public network transport, rate limiting, managed secrets, hosting hardening and production operational security are NOT claimed and are not required for T1 controlled local historical pilot.

PERSISTENCE_TRUTH:
Source graph, reviews, workflow, audit and evidence metadata/hash persist. Raw evidence bytes remain outside the registry. Pilot bundle ingestion is atomic and retry-safe. Backups are verified. Schema compatibility fails closed; no automatic data-transform migration is claimed.

LAST EXACT GREEN:
`61cdbbc81a37cef07333c7080b074f3f3a22b732` — GitHub Actions SUCCESS; **131 passed in 31.49s** on Python 3.13.15.

CURRENT_HEAD_STATE:
Documentation/runbook/BATON commits after `61cdbbc...` are `NOT_FULLY_VERIFIED` until exact-current-head GitHub Actions completes. Do not call the newest branch HEAD GREEN before that observation.

P0/P1:
No known unresolved P0/P1 in the covered local assisted-pilot surface at the last exact GREEN. This does not establish absence across production hosting/IAM or unknown real supplier data. Any material failure discovered by the historical pilot becomes ACTIVE immediately.

COMPETITION / KILL TEST:
- SupplyWhy materially collides with automotive supplier claim recovery around demand changes, inventory/cost exposure and evidence/recovery review.
- TRIGO materially collides with evidence-based program-cancellation claim auditing, especially buyer/OEM-side validation.
- Stellantis public supplier-claim audit roles prove an adversarial OEM audit function exists.
- Public automotive terms demonstrate time/evidence/category/ownership/tooling constraints and audit rights.

This kills generic “supplier claim evidence” positioning but leaves the narrower supplier-side **pre-audit before OEM scrutiny** hypothesis alive. Commercial differentiation/WTP remains unproven.

ACTIVE:
1. obtain exact-current-head CI GREEN after README/PILOT_READINESS/PILOT_RUNBOOK/BATON reconciliation;
2. if GREEN, execute T2 preparation: one controlled real/historical authorized supplier case protocol, ground-truth comparison sheet and measurement capture;
3. any current-head regression becomes ACTIVE repair before T2 work.

NEXT:
- T2 historical/real-case ground-truth runner and measurement artifact;
- record analyst preparation time, reviewer time, false positives/negatives, duplicate prevention, reviewer corrections and missing-evidence usefulness;
- compare modeled claimability to known submitted/accepted/settled/paid outcome when authorized outcome data exists;
- decide whether real-data failures require P0/P1 repair or wedge adjustment;
- only after real-case operational evidence, test willingness to pay / paid pilot.

WAIT:
- authorized real supplier/customer confidential historical data;
- any external claim submission / supplier or OEM communication;
- negotiation or settlement action;
- production deployment / secrets / provider configuration;
- spending;
- WTP or paid-pilot evidence;
- merge to `main` without explicit authorization.

REAL_WORLD_TRUTH:
REAL_CASES = 0
PAYING_CUSTOMERS = 0
VERIFIED_RECOVERY = €0
RECOVERY_RADAR_REVENUE_RECEIVED = €0
WTP = UNKNOWN

RESUME_AT:
`EXACT CURRENT HEAD CI → REPAIR IF RED → T2 HISTORICAL CASE MEASUREMENT INFRA → WAIT ONLY FOR AUTHORIZED REAL CASE DATA`.
