# Recovery Radar — PILOT_READY gate

Status vocabulary: `PROVEN_LOCAL`, `PARTIAL`, `ABSENT`, `UNKNOWN_EXTERNAL`.

| Gate | State | Evidence / gap |
|---|---|---|
| Canonical source | PROVEN_LOCAL | Dedicated branch in `MarcosTaz/ai.revenue.recovery`; `main` left unchanged. |
| Functional application | PARTIAL | Deterministic product core exists; no complete customer-facing app. |
| Event model | PROVEN_LOCAL | Cancellation, volume reduction and other event types represented. |
| Exposure engine | PROVEN_LOCAL | Category, quantity, unit cost, mitigation, reimbursement and net exposure. |
| Entitlement model | PROVEN_LOCAL | Supported/partial/conflicting/not-supported/unknown with contractual references. |
| Calculation engine | PROVEN_LOCAL | Deterministic decimal calculations + independent arithmetic oracle. |
| Mitigation | PROVEN_LOCAL | Deducted and evidence-gated; excessive mitigation fails closed. |
| Evidence graph | PARTIAL | Analysis lineage + persistent evidence identity/hash metadata + registered-evidence gate exist; full event/exposure/entitlement/document relationship persistence is incomplete. |
| Missing-evidence engine | PROVEN_LOCAL | Missing contract/cost/ownership/mitigation/reimbursement/support evidence surfaced. |
| Duplicate control | PROVEN_LOCAL | Same economic-loss ID cannot be silently claimed across multiple exposure lines; duplicate document content/version IDs are also controlled. |
| Claim package | PROVEN_LOCAL | Structured package refuses economic-ready status when registered evidence gate has not run. |
| Workflow | PROVEN_LOCAL | Detection through settlement/payment states implemented. |
| Payment-state separation | PROVEN_LOCAL | `SETTLED != PAID`; evidenced payments must reconcile exactly to settlement before PAID. |
| Synthetic suppliers | PARTIAL | Alpha + zero/partial cases + RedTeam; Nova/Titan/Legacy/Distressed remain. |
| Independent oracle | PROVEN_LOCAL | Arithmetic oracle + independent claim-line scoring. |
| Zero-recovery cases | PROVEN_LOCAL | Large exposure can correctly return €0 defensible claim. |
| Partial-recovery cases | PROVEN_LOCAL | €1M exposure / €420k reviewable cap preserved. |
| Adversarial cases | PARTIAL | Ownership, duplicates, missing mitigation, negative quantity, reimbursement, partial support, wrong document identity, unsigned contract, document duplicate/version conflicts, prompt-injection text and documentary fact conflicts covered. More document/version precedence cases remain. |
| Tenant isolation | PARTIAL | Claim and evidence store/service scope plus guessed-ID/injection tests exist; actual authentication/session boundary absent. |
| Backup/restore | PARTIAL | Claim/payment/evidence metadata economic digest preserved; corruption/migration/failure injections absent. |
| Exact-head CI GREEN | PARTIAL | `dec1f089...` passed 46 tests; current documentation commits moved branch afterward and require their own CI observation. |
| No known P0/P1 | UNKNOWN_EXTERNAL | No known P0/P1 in covered deterministic surface; incomplete auth/raw-document/failure surfaces prevent a global claim. |

## Current verdict

`PILOT_READY = NO`

Highest-value remaining gates:

1. exact-current-head CI GREEN;
2. full event/exposure/entitlement/evidence-link persistence;
3. authenticated identity/session boundary;
4. broader document conflicts/version precedence and raw-document attack handling;
5. Nova/Titan/Legacy/Distressed synthetic suppliers;
6. DB lock, partial import, migration failure and backup-corruption tests;
7. scale/export acceptance and then a controlled historical supplier pilot.
