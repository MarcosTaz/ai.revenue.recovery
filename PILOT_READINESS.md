# GovMargin Gate 10 — pilot readiness

Current state: **NOT YET PILOT-READY**.

GovMargin may become assisted-pilot capable before it becomes a fully automated SaaS product. Gate 10 is intentionally narrower than production readiness but still requires a safe real-contractor path.

## Gate 10 checklist

| Capability | State | Evidence / remaining work |
|---|---|---|
| Contract economics wedge frozen | PASS | Cost-reimbursement / CPFF with FAR 52.216-7 and settled final rates is wedge #1. |
| Contract-type applicability guard | CORE PASS | Executable classifier enables only the current CPFF/cost-reimbursement wedge when FAR 52.216-7 and settled-final-rate evidence are present. T&M/LH and FFP fail closed as unsupported; their distinct substantive billing/rate rules remain NOT ENABLED. |
| Deterministic settled-rate true-up | PASS | Python + browser engines fail closed on unsupported terms/rates/numeric inputs. |
| Ceiling / funding safeguards | CORE PASS | Deterministic safeguards exist plus source-linked FAR 52.232-20 and 52.232-22 notice/excess-limit rule objects. Contract-specific threshold/window, estimated cost or actual allotment, and written Contracting Officer action remain evidence requirements. A notice/excess condition never creates an automatic receivable. |
| Direct cost / ODC reconciliation | CORE PASS | Allowability/allocability/billability states supported; complete FAR Part 31 cost-principle coverage not implemented. |
| Fee reconciliation | CORE PASS | Fixed / supported percentage paths implemented with fee ceiling. |
| Multi-pool indirect calculation | CORE PASS | Supported settled pools calculate deterministically; broader allocation logic remains review-gated. |
| Payment reconciliation | CORE PASS | Verified invoice vs payment path implemented symmetrically. |
| Final voucher / release safeguard | CORE PASS | Apparent positive variance plus release => qualified review, not automatic recovery. |
| Synthetic A–Z portfolio | LOCAL PASS | All A–Z executable; false-positive traps assert no recovery. |
| Evidence lineage | PASS FOR NORMALIZED BUNDLE | Evidence IDs, SHA-256, source locator, observed timestamp and rule IDs required. |
| Tenant-scoped data import | CORE PASS | CSV transaction/invoice importer rejects cross-tenant and duplicate data. |
| Domain authorization | CORE PASS | ADMIN/ANALYST/REVIEWER/VIEWER separation and cross-tenant denial implemented; real identity/session integration absent. |
| Human review | CORE PASS | Reviewer identity/role/decision/rationale/timestamp modeled; unreviewed recovery remains DRAFT. |
| Recovery/evidence pack | CORE PASS | Approved candidates, payables and unresolved findings remain separate. |
| Assisted normalized end-to-end operation | LOCAL PASS | JSON bundle → rule/evidence validation → deterministic finding → DRAFT pack → optional human-review promotion; CLI exists. |
| Assisted-pilot intake contract | PASS AS SPEC | `ASSISTED_PILOT_CHECKLIST.md` now defines contract/rate/cost/billing/funding evidence minimums, admissibility gates, qualified-review triggers and terminal truth states. It is not yet exercised on real contractor data. |
| Python CI coverage | NOT_FULLY_VERIFIED CURRENT HEAD | A P0 verification defect was found: new pytest-style tests were not executed by the prior `unittest discover` workflow. Workflow changed to install and run `pytest`; current-head CI confirmation is required before restoring GREEN status. |
| Raw contract/rate document intake | NOT PASSED | Secure upload, immutable object storage, parser isolation and malware/content controls not implemented. |
| Production authentication/session | NOT PASSED | Domain auth exists; no production IdP/session binding. |
| Persistent encrypted tenant datastore | NOT PASSED | No production data store selected/configured. |
| Append-only audit persistence | NOT PASSED | Audit-event model exists but no production persistence. |
| Web workflow for import/review/pack | NOT PASSED | Current web app remains a synthetic assurance surface; it now exposes the narrower CPFF wedge and 52.232-20/-22 funding safeguards but does not provide secure real-data import/review. |
| Deployment | EXTERNALLY BLOCKED | Connected Vercel deploy action previously exposed a schema mismatch; do not reuse unrelated projects or invent credentials. |
| Real contractor data | NOT TESTED | No real contractor dataset has been processed. |
| Qualified accounting/legal review | NOT COMPLETED | Required before reserved accounting/legal activities and before enabling any success-fee model. |
| Real paid pilot | NONE | No paid customer, verified real underbilling or collected recovery yet. |

## Funding-rule evidence

Current authoritative FAR text confirms that both Limitation of Cost (52.232-20) and Limitation of Funds (52.232-22) permit the notice window to vary from 30–90 days and the threshold from 75–85 percent. 52.232-20 is keyed to the evidenced estimated cost; 52.232-22 is keyed to the amount actually allotted. Both require written Contracting Officer action for the relevant increase, and change orders alone do not authorize excess cost unless they include the required increase. GovMargin therefore treats funding-limit exceptions as review conditions, not inferred receivables.

## Contract-type guard evidence

Executable coverage lives in `govmargin/contract_type.py` with tests in `tests/test_contract_type_applicability.py`. The guard intentionally does **not** treat T&M/LH or FFP as supported simply because a clause string is present.

## CI correction

The prior workflow used `python -m unittest discover -v`. The repository contains both `unittest.TestCase` tests and pytest-style top-level `test_*` functions, so a green unittest run did not prove execution of the complete suite. The workflow now runs `python -m pytest -q`. Gate 9 cannot be called exact-head GREEN again until that corrected workflow passes on the current branch head.

## Gate 10 minimum terminal path

Before changing Gate 10 to PASS, execute one controlled real-contractor engagement through:

`REAL CONTRACTOR → REAL CONTRACT + ORDERS/MODS → SOURCE-HASHED RATE/ACCOUNTING/BILLING DATA → APPLICABLE RULES → DETERMINISTIC ECONOMICS → BILLING/PAYMENT RECONCILIATION → HUMAN REVIEW → EVIDENCE PACK → CLIENT FINANCE VALIDATION`

A claim filing or cash recovery is **not** required to call the product pilot-ready. But a synthetic-only path is insufficient.

## Pre-pilot safe exposure

It is safe to demonstrate the synthetic product and recruit a design partner using the fixed-fee pilot hypothesis, provided GovMargin is described accurately as:

- pre-pilot / assisted audit capability;
- not legal advice;
- not a CPA attestation;
- not an automated Government claim generator;
- not guaranteed to find a recovery;
- equally capable of surfacing overbilling/payables.

Do not ingest sensitive real customer documents into the current web surface until production identity/storage/security controls exist. A controlled offline/assisted pilot may use separately secured customer-approved data handling only after those controls are specified and verified for the engagement.
