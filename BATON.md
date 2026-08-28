# BATON — Recovery Radar

MISSION: cancellation/volume-reduction event → exposure → contractual basis → evidence → defensible claim → workflow → settlement → verified payment.

REPOSITORY: `MarcosTaz/ai.revenue.recovery`
BRANCH: `recovery-radar/program-cancellation-claims`
BASE MAIN: `e9bce10a907b3c79b8702199e2cd78803a64c6d6`
MAIN SOURCE TRUTH: repository contained only `.gitkeep`; implementation was absent from source.

BUSINESS_STATE: thesis preserved; commercial success UNPROVEN.

DONE:
- event model;
- exposure calculation;
- mitigation/prior-reimbursement deductions;
- entitlement support states;
- missing evidence;
- ownership fail-closed handling;
- duplicate economic-loss guard;
- claim package;
- zero-recovery and partial-recovery synthetic cases;
- independent oracle.

PRODUCT_TRUTH: `CLAIMABLE` is an evidence/economic construction state, not legal certainty, settlement or payment. `paid_total` is never inferred from claim value.

TEST_STATE: local pre-push deterministic suite `15 PASS`; exact-head CI pending.

ACTIVE: persist v0.1, exact-head CI, then implement settlement/payment state machine with SETTLED != PAID and tenant-safe persistence.
NEXT: synthetic RedTeam supplier, independent claim scorer, tenant isolation, backup/restore, document conflict/missing evidence attacks.
WAIT: real supplier/customer data, external claim submission, negotiation, production deployment, spending, WTP evidence.
RESUME_AT: exact-head CI → settlement/payment verification → tenant security.
