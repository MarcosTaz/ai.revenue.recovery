# Recovery Radar — T1 / PILOT CAPABLE gate

Status vocabulary: `PROVEN_LOCAL`, `PARTIAL`, `ABSENT`, `UNKNOWN_EXTERNAL`.

## Verdict

`T1 — PILOT CAPABLE = YES_FOR_CONTROLLED_ASSISTED_HISTORICAL_PILOT`

This promotion is deliberately narrow. The local assisted application can ingest an authorized historical supplier case, preserve uncertainty, require independent review, generate an auditable package, export it reproducibly, freeze the normalized source scope and score persisted truth against explicit historical ground truth.

It does **not** mean production SaaS readiness, autonomous legal determination, live claim submission, customer acceptance, willingness to pay, recovered cash or commercial validation.

| Gate | State | Evidence / remaining boundary |
|---|---|---|
| Canonical source | PROVEN_LOCAL | Dedicated branch in `MarcosTaz/ai.revenue.recovery`; `main` remains untouched. |
| Assisted-pilot application | PROVEN_LOCAL | Local CLI path exists from workspace bootstrap through scope freeze, import, review, package/export, internal case and historical scorecard. |
| Event model | PROVEN_LOCAL | Cancellation, severe volume reduction and related modeled event types persist tenant-scoped. |
| Exposure engine | PROVEN_LOCAL | Category, quantity, unit cost, mitigation, prior reimbursement, ownership and net exposure. |
| Entitlement model | PROVEN_LOCAL | Supported/partial/conflicting/not-supported/unknown; analyst-entered support does not count until independently reviewed. |
| Calculation engine | PROVEN_LOCAL | Deterministic Decimal calculations, arithmetic oracle, non-finite/extreme-input fail-closed behavior. |
| Mixed currency | PROVEN_LOCAL | Per-currency totals; no false scalar aggregation; mixed-currency case creation requires split. |
| Mitigation / prior compensation | PROVEN_LOCAL | Both deducted, lineage-aware and evidence-gated; excessive offsets fail closed. |
| Source graph persistence | PROVEN_LOCAL | Event, exposure, entitlement, evidence metadata/hash, review, claim, payment and audit state persist tenant-scoped. |
| Evidence graph | PROVEN_LOCAL | Source identity/hash, scope, lineage, independent review state and audit trail persist. Raw evidence bytes deliberately stay outside the DB. |
| Missing-evidence engine | PROVEN_LOCAL | Line-specific missing evidence, proof purpose, holder hint, blocking/value context and UNKNOWN obtainability probability. |
| Duplicate control | PROVEN_LOCAL | Duplicate economic-loss IDs, disguised duplicate economics, document content and document-version conflicts fail closed. |
| Contract/version ambiguity | PROVEN_LOCAL | Competing source identities fail closed; no automatic “later contract supersedes earlier contract” inference. |
| Claim package | PROVEN_LOCAL | Executive summary, line items, category/currency exposure, trace, entitlement, evidence, uncertainty, missing-evidence actions, recoverability and draft claim. |
| Export | PROVEN_LOCAL | Canonical deterministic JSON envelope, SHA-256 manifest, atomic/fsync write, post-write verification and tamper detection. |
| Workflow | PROVEN_LOCAL | Detection/analysis/review/claim-ready/submission/settlement/payment states represented; reviewer cannot perform commercial disposition. |
| Payment-state separation | PROVEN_LOCAL | `SETTLED != PAID`; evidenced payments reconcile to settlement before PAID. |
| Authentication + tenant boundary | PROVEN_LOCAL | Local API-key gateway derives workspace/role from token, stores no raw secret, supports revocation and rejects cross-tenant access. Production IAM/transport/rate limiting remain outside T1. |
| Reviewer independence | PROVEN_LOCAL | Evidence and entitlement review require REVIEWER role plus actor identity different from source creator. Reviewer cannot source-write. |
| Atomic pilot import | PROVEN_LOCAL | Bundle uses one SQLite transaction; conflicts/interrupted audit roll back all new rows; exact retry is idempotent. |
| Input safety | PROVEN_LOCAL | Bundle/file limits, strict enums/types, non-finite rejection, currency-code shape check, path-escape and direct-symlink rejection. |
| Backup/restore | PROVEN_LOCAL | Backup verifies SQLite integrity, FK integrity and whole-DB truth digest; corrupted backups are rejected. |
| Failure recovery | PROVEN_LOCAL | Interrupted writes, DB lock, concurrent submission/retry, partial import and backup corruption covered in adversarial tests. |
| Schema compatibility | PROVEN_LOCAL | Required table/column manifest + schema version; unknown newer DB refuses startup; older version requires explicit migration. |
| Scale correctness | PROVEN_LOCAL | Exact deterministic economics proven with 2,000 claim lines. No latency/SLA claim. |
| Synthetic/adversarial portfolio | PROVEN_LOCAL | Full/partial/zero recovery, compensation, mitigation, multiple exposure categories, evidence gaps/conflicts, unsupported representations, duplicates, malformed economics, currency and failure cases. |
| Source-scope freeze | PROVEN_LOCAL | `RECOVERY_RADAR_SOURCE_SCOPE_V1` binds normalized event volumes, exposure economics, entitlement fields/caps and concrete evidence-file hashes; raw evidence bytes are not embedded. |
| Source-scope economic integrity | PROVEN_LOCAL | Changing relevant quantity/cost/evidence content changes the source-scope SHA; identity hash cannot silently survive changed economics. |
| Human authorization boundary | PROVEN_LOCAL | Application explicitly does not infer authorization from case labels, hashes or references; `PILOT_AUTHORIZATION_RECORD.md` is governance support only. Actual authorization remains external. |
| T2 ground-truth adapter | PROVEN_LOCAL | `RECOVERY_RADAR_GROUND_TRUTH_V1` requires explicit case origin/completeness, typed lines/metrics and strict provenance fields. |
| Ground-truth independence metadata | PROVEN_LOCAL | `BLIND / ASSISTED / UNKNOWN` is recorded but explicitly not independently verified by the application. |
| T2 source binding | PROVEN_LOCAL | When a ground-truth scope hash is supplied, `score-historical` reconstructs persisted source truth and refuses `SOURCE_SCOPE_SHA256_MISMATCH` before scorecard write. |
| T2 scorecard | PROVEN_LOCAL | FP/FN, state/currency mismatch and amount-error measurement; final metadata including persisted-scope status is SHA-bound and atomically exported. |
| T2 truth boundary | PROVEN_LOCAL | Synthetic input is measurement-only; caller-selected case origin is marked `RECORDED_NOT_INDEPENDENTLY_VERIFIED`; WTP remains `UNKNOWN_EXTERNAL`; no scorecard field promotes T2. |
| Latest exact GREEN checkpoint | PROVEN_LOCAL | `8bd2ed8b80a3d52bccce88661959bbf24a4b1594` passed GitHub Actions with **159 tests**. Subsequent v0.2.2/docs/tests commits require exact-current-head CI before they replace this checkpoint. |
| Known P0/P1 in covered assisted-pilot surface | PROVEN_LOCAL | No known unresolved P0/P1 at the last exact GREEN. Later changes must pass exact-head CI before inheriting this statement. |
| Real supplier historical case | ABSENT | No confidential/authorized real supplier dataset has been run. |
| T2 real-case validation | ABSENT | Measurement infrastructure exists, but T2 cannot be reached without an actually authorized historical/real case and Factory review. |
| Commercial/WTP validation | ABSENT | No paid pilot, buyer commitment, recovered cash or independently verified WTP evidence. |
| Production deployment | ABSENT | No public production service; deliberately not required for T1 controlled assisted pilot. |

## T1 operating boundary

The allowed T1 execution is a **controlled historical supplier pilot**, preferably a closed/known case so measurement cannot influence an unauthorized live commercial dispute.

Required preconditions:

1. actual participant/data-owner authorization retained outside the app;
2. distinct source analyst and independent reviewer actors;
3. local authorized storage under the pilot operator's controls;
4. normalized source scope frozen before comparison;
5. no automated external submission, OEM/supplier communication, negotiation or settlement;
6. every claimable line traceable to current independently verified evidence and entitlement interpretation;
7. mixed currencies split before case creation;
8. uncertainty, conflicts and missing evidence remain visible rather than guessed.

## T2 target

`T2 — REAL-CASE VALIDATED`

Promotion beyond T1 requires evidence from at least one actually authorized historical/real supplier case. The pilot must measure, rather than assume:

- claim/exposure completeness against human ground truth;
- false-positive / false-negative and duplicate-recovery rates;
- reviewer corrections to entitlement/evidence states;
- reviewer time and time-to-package;
- missing-evidence usefulness;
- source-scope stability/reproducibility;
- difference between modeled claimability and actual accepted/settled/recovered outcome when outcome data exists;
- practical data-preparation burden;
- qualitative repeat-use signal;
- WTP only when independently evidenced outside the self-authored scorecard.

The application creates the reproducible artifacts needed for that decision but cannot authenticate the human authorization, prove ground-truth independence or promote the terminal itself.

Until a real case is run and reviewed, business status remains `SIGNAL / HIGH COMPETITIVE COLLISION / WTP UNKNOWN`.