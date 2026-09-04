# AERVIND — Commercial & Operational Readiness

_Last reviewed: 2026-09-05_

_Status basis: assisted, human-reviewed service; not self-service enterprise SaaS._

## Readiness verdict

**PRODUCT / DELIVERY: ASSISTED PILOT READY**

**REAL OUTREACH: HOLD ACTIVE — NO REAL EXTERNAL SEND**

**PUBLIC SITE: TEMPORARY VERCEL HOST LIVE; `aervind.com` CUSTOM ROUTING PENDING**

**BRANDED EMAIL: DNS CONFIGURATION PENDING**

A bounded Recovery Scan can be executed with the current product once a real engagement is authorized, contracted and supplied with evidence under agreed confidentiality/data-handling terms. Product readiness does not authorize real prospect contact while `docs/REAL_OUTREACH_HOLD.md` is active.

## Gate matrix

| Capability | Status | Evidence / boundary |
| --- | --- | --- |
| Deterministic entitlement calculation | READY | `aviation_recovery.py` + regression tests |
| Maintenance-reserve reimbursement wedge | READY | engine formulas + synthetic pilot |
| Lessor contribution / cost-sharing | READY | configured entitlement types + tests |
| Deposit/prepaid-rent/EOL extensibility | RULE-CONFIGURED PILOT | lease-specific rules remain source-grounded |
| Rule/version effective dates | READY | engine |
| Caps/floors/deductibles/rates | READY | engine + tests |
| Deadline/time-bar controls | READY | engine + tests |
| Required-evidence controls | READY | engine + dossier tests |
| Malformed/chronologically invalid input | FAIL-CONSERVATIVE | IO/engine regression tests |
| Source lineage | READY | dossier + IO lineage gate |
| Cohort revision binding | READY | SHA-256 binding in `workflow_case.py` |
| Human review before externalization | READY | lifecycle + dossier gates |
| False-positive / duplicate-recovery controls | READY | engine + operating runbook |
| Recovery-truth reporting | READY | `recovery_truth.py`, `executive_report.py` |
| Mutually exclusive management buckets | READY | workflow-aware reporting |
| Claim package | READY | human-gated renderer |
| Package artifact hash / audit | READY | portable-case artifact audit |
| Submission/dispute/approval lifecycle | READY FOR ASSISTED RECORDING | console records evidence; it never submits externally |
| Settlement truth | READY | amount/currency/reference evidence gate |
| Portable case state | READY FOR ASSISTED PILOT | export/reopen; no hidden server persistence |
| Synthetic E2E | READY | `examples/pilot.json`, TAP-shaped synthetic demo |
| Automated regression suite | READY | GitHub Actions + unittest |
| Customer data request / intake | READY | minimum-necessary evidence model |
| Local console network boundary | HARDENED | loopback-only bind, local client/Host, same-authority browser POST Origin |
| Request-body controls | HARDENED | 2 MB cap, timeout, no transfer encoding, incomplete/complex JSON rejection |
| Security/confidentiality baseline | READY FOR ASSISTED PILOT | truthful non-certification baseline |
| Commercial offer | READY | EUR 9,500 / 5 assets / 1 family / 12 months / 10 business days |
| Private buyer preparation | READY | 10 researched account briefs and route register; unsent |
| Real outbound | HOLD | explicit founder no-send instruction |
| Temporary technical site | LIVE | `aervind.vercel.app`, canonical static page, HTTPS/security headers |
| Official `aervind.com` website | ROUTING GATE | domain registered; custom-domain attach/DNS still pending |
| Branded `@aervind.com` email | DNS GATE | Primitive claim exists; MX/ownership/SPF/DKIM/DMARC/TLS-RPT not yet valid |
| Portuguese activity/tax suitability | EXTERNAL FACTUAL GATE | verify real activity and customer-specific invoicing/VAT before paid delivery |
| Self-service customer UI | POST-PILOT | not required for assisted milestone |
| SSO / enterprise RBAC / tenant admin | POST-PILOT | buyer-driven scale capability |
| Deep M&E / ERP integrations | POST-PILOT | only after proof / buyer requirement |
| Formal external security certification | NOT HELD | never claim before actually obtained |

## Commercial acceptance test before receiving real airline evidence

All must pass:

1. the active real-outreach hold has been explicitly lifted for the real commercial process;
2. real customer legal entity is known;
3. signed commercial/confidentiality terms exist;
4. scope is bounded to the agreed assets/events/entitlement family and review period;
5. customer and AERVIND accountable reviewers are named;
6. permitted transfer/storage route and case-file location are agreed;
7. governing lease/amendment material exists for the cohort;
8. prior claims/reimbursements/settlements can be reconciled in scope;
9. external claim submission remains customer-approved and human-controlled;
10. supplier activity/tax/invoicing treatment is verified for that customer.

These are engagement prerequisites, not missing recovery-engine features.

## What the first paid pilot must prove

1. **Truth** — governing economics can be reconstructed without inventing missing terms.
2. **Control** — every candidate's status and calculation are explainable and source-grounded.
3. **Evidence** — lineage, workflow and settlement states remain auditable.
4. **Outcome** — the cohort either produces supportable exceptions/value or defensible assurance that the tested control closes.
5. **Commercial value** — the outcome justifies or rejects expansion based on evidence, not optimism.

A pilot does not need a positive recovery claim to be valid.

## Current external blockers

The remaining pre-market gates are intentionally narrow:

- attach and verify `aervind.com` as the official web domain;
- publish/verify Primitive mail DNS records in Porkbun;
- keep any real-recipient mail test disabled while the no-send hold is active;
- verify actual Portuguese activity/tax status before paid delivery;
- later satisfy real buyer-specific procurement/security requirements truthfully.

None of these justify rebuilding the core product.

## Deliberate scale boundary

Do not add hosted multi-customer persistence, tenant administration, SSO/RBAC, document extraction, deep integrations, automated billing or formal security-certification claims merely to look larger. Add them only after a real buyer requirement or paid proof makes the capability economically necessary.
