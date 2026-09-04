# Aviation Recovery — Commercial Readiness

_Status basis: assisted, human-reviewed pilot; not self-service enterprise SaaS._

## Readiness verdict

**ASSISTED PILOT COMMERCIAL-READY**

A bounded customer engagement can be sold and executed now using the current workflow, provided customer contract/evidence inputs are supplied under an agreed confidentiality arrangement and material contract interpretation remains human-reviewed.

The assisted operator product now has both CLI and browser-console execution paths over the same deterministic engine. The browser console is deliberately local/no-persistence by default; it is not a public customer SaaS deployment.

## Gate matrix

| Capability | Status | Evidence in repository |
|---|---|---|
| Deterministic entitlement calculation | READY | `aviation_recovery.py`, engine tests |
| Maintenance-reserve reimbursement wedge | READY | engine formulas + synthetic pilot |
| Lessor contribution / cost-sharing | READY | entitlement types/formulas + tests |
| Deposit/prepaid-rent/EOL extensibility | READY FOR RULE-CONFIGURED PILOTS | entitlement taxonomy supports these families; lease-specific rules still require source-grounded configuration |
| Rule/version effective dates | READY | `EntitlementRule.effective_from/effective_to` |
| Caps/floors/deductibles/rates | READY | engine + tests |
| Deadline/time-bar controls | READY | engine + deadline tests |
| Required-evidence controls | READY | engine + dossier tests |
| Source lineage | READY | `aviation_dossier.py` |
| Human review before externalization | READY | dossier/workflow gates |
| False-positive red team | READY AS OPERATING STANDARD | `docs/CLAIM_DOSSIER.md`, operator runbook |
| Prior-payment / prior-claim offsets | READY | engine + tests |
| Recovery-truth reporting | READY | `recovery_truth.py`, `executive_report.py` |
| Claim package | READY | `claim_package.py` + tests |
| Submission / dispute / approval workflow | READY | `claim_workflow.py` + tests |
| Settlement truth | READY | economic-evidence gate + workflow tests |
| Audit-event model | READY FOR ASSISTED PILOT | transition events exist; production persistence/identity hardening is scale-phase work |
| Synthetic E2E demonstration | READY | `examples/pilot.json`, CLI, CLI tests |
| Assisted browser operator console | READY | `operator_app.py`, `operator_ui/`, `tests/test_operator_app.py` |
| Candidate drill-down / calculation trace | READY | operator console + evaluation dossiers |
| Executive report export | READY | `executive_report.py` + operator console |
| Automated regression gate | READY | GitHub Actions + unittest suite |
| Pilot data request | READY | `docs/PILOT_DATA_REQUEST.md` |
| Security/confidentiality baseline | READY FOR ASSISTED PILOT | `docs/SECURITY_AND_CONFIDENTIALITY.md` |
| Operator runbook | READY | `docs/OPERATOR_RUNBOOK.md`, `docs/OPERATOR_CONSOLE.md` |
| Pilot SOW / commercial structure | READY | `docs/PILOT_SOW.md` |
| ICP / discovery / outbound | READY | `docs/GTM.md`, `docs/OUTBOUND_PLAYBOOK.md` |
| Self-service customer portal | POST-PILOT | not required for assisted-pilot milestone |
| SSO / enterprise RBAC / tenant admin | POST-PILOT | scale-phase control |
| Deep M&E / ERP integrations | POST-PILOT | scale after proof of recovery value |
| Formal external security certification | POST-PILOT | do not claim before obtained |

## Commercial acceptance test

Before taking a first customer engagement, confirm these engagement-specific conditions:

1. Signed commercial/confidentiality terms exist.
2. Pilot scope is bounded by assets/events/entitlement families.
3. Customer names an accountable business reviewer.
4. Permitted data-transfer/storage method is agreed.
5. Governing lease/amendment documents are available for the selected claims.
6. Prior claims/settlements can be reconciled within the supplied scope.
7. External claim submission remains customer-approved/human-reviewed.
8. Success fees, if any, define recovery using settlement evidence rather than identified value.

These are customer-engagement prerequisites, not missing product engineering.

## What the first paid pilot should prove

A first paid pilot should answer four questions with evidence:

1. **Truth:** Can the product reconstruct the governing economic entitlement without inventing missing terms?
2. **Recovery:** Does the scoped population contain claim-ready or resolvable blocked value?
3. **Control:** Can the customer see why each candidate passes, fails or remains blocked?
4. **Commercial value:** Is the verified recovery or assurance value large enough to justify expanding the engagement?

## Post-pilot scale priorities

Only after assisted pilots prove repeatable value, prioritize:

1. persistent multi-customer data model and durable audit store;
2. customer/reviewer portal over the proven operator workflow;
3. tenant isolation, RBAC, SSO/MFA and enterprise audit controls;
4. document ingestion/extraction assistance with human validation;
5. M&E / ERP / lease-management integrations;
6. deadline/event monitoring automation;
7. configurable customer reporting and export;
8. formal security assurance required by enterprise buyers.

The product should not delay first revenue waiting for these scale features.
