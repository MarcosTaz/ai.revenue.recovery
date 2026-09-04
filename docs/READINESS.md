# Aviation Recovery — Commercial Readiness

_Status basis: assisted, human-reviewed pilot; not self-service enterprise SaaS._

## Readiness verdict

**ASSISTED PILOT COMMERCIAL-READY**

A bounded customer engagement can be sold and executed with the current product when customer contract/evidence inputs are supplied under agreed confidentiality/data-handling terms and material contract interpretation remains human-reviewed.

The assisted operator product now closes the operational path from source cohort through deterministic evaluation, human review, claim package, external-lifecycle evidence recording and verified settlement reporting. It does not require live access to airline systems for the first scan.

## Gate matrix

| Capability | Status | Evidence in repository |
|---|---|---|
| Deterministic entitlement calculation | READY | `aviation_recovery.py`, engine tests |
| Maintenance-reserve reimbursement wedge | READY | engine formulas + synthetic pilot |
| Lessor contribution / cost-sharing | READY | entitlement types/formulas + tests |
| Deposit/prepaid-rent/EOL extensibility | READY FOR RULE-CONFIGURED PILOTS | entitlement taxonomy; lease-specific rules remain source-configured |
| Rule/version effective dates | READY | `EntitlementRule.effective_from/effective_to` |
| Caps/floors/deductibles/rates | READY | engine + tests |
| Deadline/time-bar controls | READY | engine + deadline tests |
| Required-evidence controls | READY | engine + dossier tests |
| Input chronology / malformed evidence fail-conservative controls | READY | engine + IO regression tests |
| Source lineage | READY | `aviation_dossier.py`, IO lineage gate |
| Source-revision binding after release | READY | `workflow_case.py` cohort SHA-256 binding |
| Human review before externalization | READY | lifecycle + dossier gates |
| False-positive red team | READY AS OPERATING STANDARD | Claim Dossier + operator runbook |
| Prior-payment / prior-claim offsets | READY | engine + tests |
| Recovery-truth reporting | READY | `recovery_truth.py`, `executive_report.py` |
| Mutually exclusive management buckets | READY | workflow-aware executive reporting |
| Claim package | READY | package renderer + audited console generation |
| Package artifact hash / generation audit | READY | portable case workflow artifacts |
| Submission / dispute / approval workflow | READY FOR ASSISTED RECORDING | `claim_workflow.py`, operator console; console records but never performs external submission |
| External submission/reference evidence | READY | lifecycle transition gate |
| Settlement truth | READY | positive economic-evidence gate + amount/currency/reference controls |
| Audit-event model | READY FOR ASSISTED PILOT | actor, reason, time, external refs, settlement refs, contiguous lifecycle checks |
| Portable durable case state | READY FOR ASSISTED PILOT | operator-exported AERVIND case file; no hidden server persistence |
| Synthetic E2E demonstration | READY | `examples/pilot.json`, TAP-shaped synthetic demo |
| Automated regression gate | READY | GitHub Actions + unittest suite |
| Pilot data request | READY | `docs/PILOT_DATA_REQUEST.md` |
| Security/confidentiality baseline | READY FOR ASSISTED PILOT | `docs/SECURITY_AND_CONFIDENTIALITY.md`, local console headers/boundary |
| Operator runbook | READY | `docs/OPERATOR_RUNBOOK.md`, `docs/OPERATOR_CONSOLE.md` |
| Pilot SOW / commercial structure | READY | `docs/PILOT_SOW.md`, first paid proposal |
| Public first-engagement explanation | READY | no-system-access and bounded-scan site positioning |
| ICP / discovery / account routing | READY | GTM, target accounts, buyer map, channel strategy |
| Branded operational email | CONFIGURATION GATE | domain registered; Primitive custom-domain DNS verification still required before branded mail is claimed live |
| Public marketing site at `aervind.com` | DEPLOYMENT GATE | static site ready; domain routing/deployment must be completed before claiming it is live |
| Portuguese activity/tax suitability for first invoice | EXTERNAL FACTUAL GATE | verify real supplier activity classification and customer-specific invoicing/VAT treatment |
| Self-service customer UI | POST-PILOT | not required for assisted-pilot milestone |
| SSO / enterprise RBAC / tenant admin | POST-PILOT | scale-phase, buyer-driven |
| Deep M&E / ERP integrations | POST-PILOT | scale only after value proof / buyer requirement |
| Formal external security certification | POST-PILOT | never claim before obtained |

## Commercial acceptance test

Before accepting real airline data, confirm:

1. Signed commercial/confidentiality terms exist.
2. Real customer legal entity is known.
3. Scope is bounded by assets/events/entitlement families and review period.
4. Customer and AERVIND accountable reviewers are named.
5. Permitted data-transfer/storage method and case-file location are agreed.
6. Governing lease/amendment documents exist for the selected cohort.
7. Prior claims/reimbursements/settlements can be reconciled in scope.
8. External claim submission remains customer-approved and human-controlled.
9. Any success-fee definition uses evidence-backed settlement rather than identified or approved value.
10. Supplier activity/tax/invoicing treatment is verified for that customer.

These are engagement prerequisites, not missing recovery-engine features.

## What the first paid pilot must prove

1. **Truth:** governing economic entitlements can be reconstructed without inventing missing terms.
2. **Recovery:** the scoped population contains either claim-ready/resolvable value or defensible assurance that the tested controls close.
3. **Control:** the customer can see exactly why each candidate passes, fails, returns to review or settles.
4. **Evidence:** source lineage, submission events and settlement states remain auditable.
5. **Commercial value:** verified recovery or assurance justifies expansion beyond the bounded scan.

## Deliberate scale boundary

Do not delay first revenue for SaaS features. Add persistent multi-customer storage, tenant isolation, RBAC, SSO/MFA, document extraction, deep system integrations and formal external security assurance only after a paid engagement demonstrates repeatable value or a real buyer makes a capability a procurement requirement.
