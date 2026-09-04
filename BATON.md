# GOVMARGIN BATON

MISSION: borrower-independent contractor-side federal earned-revenue and margin recovery, beginning with defensible historical underbilling / settled indirect-rate true-up and final-voucher/closeout assurance.

BRANCH: `govmargin/federal-earned-revenue-recovery`
PR: #1 (DRAFT / DO NOT MERGE)

## CURRENT TERMINAL
T0 survived; progressing toward T1 pilot-capable. Real-customer economic proof remains absent.

## DONE
- Current executable wedge remains cost-reimbursement / CPFF with FAR 52.216-7 and evidence-backed settled final rates.
- Deterministic settled-rate, indirect-pool, direct-cost/ODC, fee, ceiling/funding, payment and final-voucher safeguards exist.
- Evidence lineage, tenant-scoped imports, domain authorization and human-review gating exist for normalized inputs.
- Added fail-closed contract-type applicability classifier in `govmargin/contract_type.py`.
- CPFF/cost-reimbursement is enabled only when 52.216-7 applicability and settled-final-rate evidence are present.
- T&M/LH and FFP are explicitly disabled rather than being incorrectly routed through the CPFF engine.
- Missing and unknown contract types remain UNKNOWN / disabled.
- Exact-head CI on `579143552f039ed3ce56253948de3efc1b40dce6`: all 3 checks SUCCESS.

## EVIDENCE
- `tests/test_contract_type_applicability.py` covers CPFF prerequisites, T&M/LH fail-closed behavior, FFP, unknown and missing types.
- Gate 10 `PILOT_READINESS.md` updated to distinguish CORE PASS of the applicability guard from still-unimplemented T&M/LH substantive rule coverage.

## ACTIVE
Reduce the next T1 blocker without widening the wedge: specify and test clause-specific funding safeguards / qualified-review states while preserving zero-false-recovery behavior.

## NEXT
1. Add explicit FAR 52.232-20 / 52.232-22 funding-rule objects only where supported by authoritative evidence and tests.
2. Keep raw-document ingestion, production identity/storage and real-customer data blocked until their security contracts exist.
3. Prepare a controlled assisted-pilot input checklist and truth-preserving review package.
4. Move to real design-partner validation when owner/external communication authority exists.

## WAIT / EXTERNAL
- Real contractor data and design partner.
- Qualified accounting/legal review for reserved activities and any success-fee model.
- Production identity, encrypted storage and deployment authority.

## SAFETY
No invented entitlement, no automatic claim filing, no automatic invoice/collection assertion, no production deploy, no merge, no real customer data in the current web surface.

## RESUME_AT
Implement the narrow clause-specific funding safeguard contract, test fail-closed edge cases, then reassess Gate 10.
