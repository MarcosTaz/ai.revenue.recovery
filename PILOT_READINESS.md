# Recovery Radar — T1 / PILOT CAPABLE gate

Status vocabulary: `PROVEN_LOCAL`, `PARTIAL`, `ABSENT`, `UNKNOWN_EXTERNAL`.

## Verdict

`T1 — PILOT CAPABLE = YES_FOR_CONTROLLED_ASSISTED_HISTORICAL_PILOT`

This promotion is deliberately narrow. It means the local assisted application has a tested path to ingest an authorized historical supplier case, preserve uncertainty, require independent review, generate an auditable package and export it reproducibly.

It does **not** mean production SaaS readiness, autonomous legal determination, live claim submission, customer acceptance, willingness to pay, recovered cash or commercial validation.

| Gate | State | Evidence / remaining boundary |
|---|---|---|
| Canonical source | PROVEN_LOCAL | Dedicated branch in `MarcosTaz/ai.revenue.recovery`; `main` remains untouched. |
| Assisted-pilot application | PROVEN_LOCAL | Local CLI/operator path exists from workspace bootstrap through bundle import, review, package/export and internal case creation. Public/customer-facing web app is not part of T1. |
| Event model | PROVEN_LOCAL | Cancellation, severe volume reduction and related modeled event types persist tenant-scoped. |
| Exposure engine | PROVEN_LOCAL | Category, quantity, unit cost, mitigation, prior reimbursement, ownership and net exposure. |
| Entitlement model | PROVEN_LOCAL | Supported/partial/conflicting/not-supported/unknown; structured support does not count until independently reviewed. |
| Calculation engine | PROVEN_LOCAL | Deterministic Decimal calculations, arithmetic oracle, non-finite/extreme-input fail-closed behavior. |
| Mixed currency | PROVEN_LOCAL | Per-currency totals; no false scalar aggregation; mixed-currency case creation requires split. |
| Mitigation / prior compensation | PROVEN_LOCAL | Both deducted, lineage-aware and evidence-gated; excessive offsets fail closed. |
| Source graph persistence | PROVEN_LOCAL | Event, exposure, entitlement, evidence metadata/hash, review, claim, payment and audit state persist tenant-scoped. |
| Evidence graph | PROVEN_LOCAL | Source identity/hash, scope, lineage, independent review state and audit trail persist. Raw evidence bytes are deliberately not persisted. |
| Missing-evidence engine | PROVEN_LOCAL | Line-specific missing evidence, proof purpose, holder hint, blocking/value context and UNKNOWN obtainability probability. |
| Duplicate control | PROVEN_LOCAL | Duplicate economic-loss IDs, disguised duplicate economics, document content and document-version conflicts fail closed. |
| Contract/version ambiguity | PROVEN_LOCAL | Competing source identities fail closed; no automatic “later contract supersedes earlier contract” inference. |
| Claim package | PROVEN_LOCAL | Executive summary, line items, category/currency exposure, trace, entitlement, evidence, uncertainty, missing-evidence actions, recoverability and draft claim. |
| Export | PROVEN_LOCAL | Canonical deterministic JSON envelope, SHA-256 manifest, atomic/fsync write, post-write verification and tamper detection. |
| Workflow | PROVEN_LOCAL | Detection/analysis/review/claim-ready/submission/settlement/payment states represented; reviewer cannot perform commercial disposition. |
| Payment-state separation | PROVEN_LOCAL | `SETTLED != PAID`; evidenced payment records reconcile to settlement before PAID. |
| Authentication + tenant boundary | PROVEN_LOCAL | Local API-key gateway derives workspace/role from token, stores no raw secret, supports revocation and rejects cross-tenant access. Production IAM/transport/rate limiting remain outside T1. |
| Reviewer independence | PROVEN_LOCAL | Evidence and entitlement review require REVIEWER role plus actor identity different from source creator. Reviewer cannot source-write. |
| Atomic pilot import | PROVEN_LOCAL | Bundle uses one SQLite transaction; conflicts/interrupted audit roll back all new rows; exact retry is idempotent. |
| Input safety | PROVEN_LOCAL | Bundle/file limits, strict enums/types, non-finite rejection, currency-code shape check, path-escape and direct-symlink rejection. |
| Backup/restore | PROVEN_LOCAL | Backup verifies SQLite integrity, FK integrity and whole-DB truth digest; corrupted backups are rejected. |
| Failure recovery | PROVEN_LOCAL | Interrupted writes, DB lock, concurrent submission/retry, partial import and backup corruption covered in local adversarial tests. |
| Schema compatibility | PROVEN_LOCAL | Required table/column manifest + schema version; unknown newer DB refuses startup; older version requires explicit migration. No automatic data-transform migration is claimed. |
| Scale correctness | PROVEN_LOCAL | Exact deterministic economics proven with 2,000 claim lines. No latency/SLA claim. |
| Synthetic/adversarial portfolio | PROVEN_LOCAL | Full/partial/zero recovery, compensation, mitigation, multiple exposure categories, evidence gaps/conflicts, unsupported representations, duplicates, malformed economics, currency and failure cases. |
| Latest exact code HEAD CI | PROVEN_LOCAL | `61cdbbc81a37cef07333c7080b074f3f3a22b732` — GitHub Actions SUCCESS, **131 passed**. Documentation commits after it require their own exact-head CI observation. |
| Known P0/P1 in covered assisted-pilot surface | PROVEN_LOCAL | No known unresolved P0/P1 after the current adversarial suite. This is not a claim about production hosting/IAM or unknown real-data failure modes. |
| Real supplier historical case | ABSENT | No confidential real supplier dataset has been authorized/run. |
| Commercial/WTP validation | ABSENT | No paid pilot, buyer commitment, recovered cash or WTP evidence. |
| Production deployment | ABSENT | No public production service; deliberately not required for T1 controlled assisted pilot. |

## T1 operating boundary

The allowed T1 execution is a **controlled historical supplier pilot**, preferably a closed or already-known cancellation/reduction case so Recovery Radar can be measured without influencing a live commercial dispute.

Required preconditions:

1. explicit authorization to use the case data;
2. distinct source analyst and independent reviewer actors;
3. local authorized storage under the pilot operator's controls;
4. no automated external submission, OEM/supplier communication, negotiation or settlement;
5. every claimable line traceable to current independently verified evidence and entitlement interpretation;
6. mixed currencies split before case creation;
7. uncertainty, conflicts and missing evidence remain visible rather than guessed.

## T2 target

`T2 — REAL-CASE VALIDATED`

Promotion beyond T1 requires evidence from at least one authorized historical/real supplier case. The pilot must measure, rather than assume:

- claim/exposure completeness against human ground truth;
- false-positive / false-negative and duplicate-recovery rates;
- reviewer corrections to entitlement/evidence states;
- reviewer time and time-to-package;
- missing-evidence usefulness;
- difference between modeled claimability and actual accepted/settled/recovered outcome when outcome data exists;
- practical data-preparation burden;
- qualitative repeat-use signal;
- WTP only when explicitly evidenced.

Until then, business status remains `SIGNAL / HIGH COMPETITIVE COLLISION / WTP UNKNOWN`.
