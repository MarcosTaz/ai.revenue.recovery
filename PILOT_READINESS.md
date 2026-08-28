# Recovery Radar — PILOT_READY gate

Status vocabulary: `PROVEN_LOCAL`, `PARTIAL`, `ABSENT`, `UNKNOWN_EXTERNAL`.

| Gate | State | Evidence / gap |
|---|---|---|
| Canonical source | PROVEN_LOCAL | Dedicated branch in `MarcosTaz/ai.revenue.recovery`; `main` left unchanged. |
| Functional application | PARTIAL | Deterministic Python product core exists; no complete customer-facing app. |
| Event model | PROVEN_LOCAL | Cancellation, volume reduction and other event types represented. |
| Exposure engine | PROVEN_LOCAL | Category, quantity, unit cost, mitigation, reimbursement and net exposure. |
| Entitlement model | PROVEN_LOCAL | Supported/partial/conflicting/not-supported/unknown with contractual references. |
| Calculation engine | PROVEN_LOCAL | Deterministic decimal calculations + independent arithmetic oracle. |
| Mitigation | PROVEN_LOCAL | Deducted and evidence-gated; excessive mitigation fails closed. |
| Evidence graph | PARTIAL | Lineage exists in analysis; complete persisted evidence/document graph is absent. |
| Missing-evidence engine | PROVEN_LOCAL | Missing contract/cost/ownership/mitigation/reimbursement/support evidence surfaced. |
| Duplicate control | PROVEN_LOCAL | Same economic-loss ID cannot be silently claimed through multiple exposure lines. |
| Claim package | PROVEN_LOCAL | Structured auditable package with legal boundary and missing evidence. |
| Workflow | PROVEN_LOCAL | Detection through settlement/payment states implemented. |
| Payment-state separation | PROVEN_LOCAL | `SETTLED != PAID`; evidenced payments must exactly reconcile to settlement before PAID. |
| Synthetic suppliers | PARTIAL | Alpha + zero/partial cases + RedTeam; Nova/Titan/Legacy/Distressed remain. |
| Independent oracle | PROVEN_LOCAL | Arithmetic oracle + independent claim-line scoring. |
| Zero-recovery cases | PROVEN_LOCAL | Large exposure can correctly return €0 defensible claim. |
| Partial-recovery cases | PROVEN_LOCAL | €1M exposure / €420k reviewable cap preserved. |
| Adversarial cases | PARTIAL | Ownership, duplicates, missing mitigation, negative quantity, reimbursement and partial-support attacks covered; broader document attacks absent. |
| Tenant isolation | PARTIAL | Store/service scope and IDOR-style tests exist; real authentication/session boundary absent. |
| Backup/restore | PARTIAL | Claim/payment economic digest preserved; corruption/migration/failure injections absent. |
| Exact-head CI GREEN | PENDING_CURRENT_HEAD | Last exact tested head `15f34174...` ran 27 tests GREEN; documentation/research commits moved branch afterward. |
| No known P0/P1 | UNKNOWN_EXTERNAL | No known P0/P1 in covered surface; incomplete auth/document/failure surfaces prevent a global claim. |

## Current verdict

`PILOT_READY = NO`

The highest-value remaining gates are not UI polish. They are:

1. authenticated identity/session boundary;
2. persisted evidence/document lineage;
3. document conflicts and untrusted-document attacks;
4. broader supplier synthetic factory and oracle coverage;
5. failure/migration/backup-corruption tests;
6. exact-current-head CI GREEN after every material change.
