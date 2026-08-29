# GovMargin historical recovery audit protocol

## Scope

Initial audit: **settled-final-rate, final-voucher and closeout economic reconciliation** for U.S. federal flexibly priced contracts.

The audit determines economic variance. It does not itself provide a legal opinion, CPA attestation, certified claim, or representation before the Government.

## Stage 0 — admissibility gate

Do not calculate a recovery candidate until the minimum record exists:

- signed contract and applicable task/delivery order;
- modification chain;
- contract type and relevant clauses;
- performance and fiscal-year periods;
- provisional/billing rates used;
- settled final indirect-rate agreement where a final-rate true-up is asserted;
- cumulative billings;
- payment evidence;
- enough job-cost / ledger data to reconstruct the base;
- identified ceilings and funding limitations.

Missing critical evidence => `UNKNOWN` or `REQUIRES_REVIEW`.

## Stage 1 — contract truth

Build a versioned contract register:

`CONTRACT → ORDER → VERSION → MODIFICATION → EFFECTIVE DATE → CLAUSES → FUNDING → CEILINGS → FEE TERMS`

No later modification may be back-applied to an earlier period without evidence that it is effective for that period.

## Stage 2 — rate truth

For every fiscal year:

- identify provisional/billing rates actually used;
- identify rate proposal state;
- identify negotiated/settled final rates;
- map rate agreement evidence;
- reconstruct pools and allocation bases;
- preserve unresolved questioned/unallowable items separately.

A proposed final rate is not a settled final rate.

## Stage 3 — cost truth

Reconcile source transactions to:

- direct labor;
- ODC/travel/material/subcontract cost;
- indirect pools;
- allocation bases;
- duplicate / reversal / transfer state;
- allowability state;
- allocability state;
- contract billability state.

No accounting expense is presumed to be a contract cost.

## Stage 4 — expected economics

Compute deterministically:

- supported direct cost;
- supported indirect cost by pool/layer;
- fee according to evidenced contract formula;
- ceiling limitations;
- order-level limitations;
- funding limitations;
- cumulative expected billing.

Store every input and formula version.

## Stage 5 — billing and cash reconciliation

Compare:

`EXPECTED BILLING → ACTUAL CUMULATIVE BILLING → VERIFIED PAYMENTS`

Keep separately:

- recovery candidates;
- payable / overbilling candidates;
- no-variance items;
- requires-review items;
- unknowns.

Never net unfavorable findings away from favorable ones.

## Stage 6 — final-voucher / closeout gate

Check:

- physical completion;
- final-rate settlement;
- completion voucher/final invoice;
- release status and any reservations;
- contract closeout state;
- deadlines / accrual issues requiring legal review;
- remaining funds / deobligations where evidenced.

Signed releases, disputed deadlines, claim accrual or jurisdiction questions => `REQUIRES_LEGAL_REVIEW` before recovery assertion.

## Stage 7 — finding qualification

A finding is client-actionable only after it contains:

- contract/order/version;
- period;
- source transaction(s);
- regulatory/contract rule lineage;
- rate evidence;
- allowability/allocability status;
- ceiling/funding checks;
- expected amount;
- billed amount;
- paid amount where relevant;
- variance;
- procedural blocker/deadline status;
- evidence hashes/locations;
- assumptions;
- confidence;
- human review status.

## Stage 8 — output pack

Deliver:

1. executive economic schedule — earned / billed / paid / candidate / payable / unknown;
2. contract-level reconciliation workbook/export;
3. evidence index;
4. rule/contract lineage sheet;
5. candidate memo for customer finance review;
6. issue list requiring CPA/accounting review;
7. issue list requiring counsel review;
8. closeout / final-voucher action queue.

Only a qualified professional or authorized client representative converts a candidate into any reserved legal/accounting action.
