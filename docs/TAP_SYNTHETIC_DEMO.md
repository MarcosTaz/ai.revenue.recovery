# Aviation Recovery — TAP-Shaped Synthetic Demo

_Last prepared: 2026-09-04_

## Non-customer-data rule

This demonstration is **100% synthetic**. It is shaped around the type of lease / maintenance control problem relevant to a large leased-aircraft operator, but it is **not derived from TAP contracts, maintenance events, reserve balances, claims, invoices or settlements**.

Never present the numbers below as TAP findings.

## Demo objective

Show, in one short meeting, why Aviation Recovery does not equate “possible value” with recoverable or recovered value.

The synthetic cohort contains four candidates in EUR:

1. engine maintenance-reserve reimbursement with prior offsets — claim-ready;
2. lessor maintenance contribution with a contractual cap and prior payment — claim-ready;
3. maintenance-reserve candidate with incomplete technical / payment evidence — blocked;
4. redelivery adjustment with complete evidence but an approaching contractual deadline — review-required.

## Expected recovery truth

| Status | Candidates | Economic value |
| --- | ---: | ---: |
| Claim-ready | 2 | EUR 1,260,000 |
| Review-required | 1 | EUR 187,500 |
| Blocked potential | 1 | EUR 200,000 |
| Total identified before status filter | 4 | EUR 1,647,500 |

**Recovered / settled value in this demo: EUR 0.**

Nothing is called recovered merely because it is claim-ready.

## Candidate 1 — engine maintenance reserve

Synthetic economics:

- eligible cost: EUR 1.60m;
- available maintenance-reserve fund: EUR 1.10m;
- prior reimbursement: EUR 100k;
- already claimed: EUR 50k;
- complete required evidence;
- net claim-ready value: **EUR 950k**.

The meeting point: the engine invoice headline is not the entitlement. The rule, fund balance and prior offsets must reconcile first.

## Candidate 2 — lessor contribution

Synthetic economics:

- eligible cost: EUR 900k;
- contribution rate: 40%;
- contractual cap: EUR 400k;
- prior payment: EUR 50k;
- net claim-ready value: **EUR 310k**.

The meeting point: percentage economics, caps and prior settlement history must be handled deterministically rather than in an isolated spreadsheet calculation.

## Candidate 3 — blocked false recovery

Synthetic economics:

- apparent economic potential: EUR 200k;
- invoice exists;
- workscope missing;
- payment evidence missing.

The engine deliberately reports **blocked potential: EUR 200k** rather than claim-ready value.

The meeting point: Aviation Recovery is designed to suppress inflated recovery claims, not maximize a speculative headline number.

## Candidate 4 — redelivery adjustment under deadline pressure

Synthetic economics:

- eligible cost: EUR 300k;
- deductible: EUR 50k;
- contractual participation: 75%;
- calculated value: EUR 187.5k;
- supporting evidence present;
- 24 days remain before the synthetic contractual deadline.

Status: **review-required**, not claim-ready.

The meeting point: complete evidence is not the only control. Time-to-deadline is part of entitlement actionability.

## 15-minute meeting flow

### Minute 0–2 — frame the control question

Ask:

> For one leased-aircraft or engine event, can the organization prove end-to-end that the governing clause, eligible technical cost, reserve / contribution position, prior claims, deadline and final settlement all reconcile?

Do not ask whether TAP is “leaking money.”

### Minute 2–6 — show calculation truth

Run:

```bash
python cli.py examples/tap_synthetic_demo.json \
  --output tap_demo_evaluated.json \
  --report tap_demo_executive.md
```

Show why two candidates are ready while two are not.

### Minute 6–9 — show evidence lineage

Open the internal dossier for Candidate 3 and highlight that missing workscope / payment evidence blocks externalization.

### Minute 9–11 — show deadline actionability

Open Candidate 4 and show the deadline warning. Explain that the same underlying amount belongs in a review queue, not in a recovered-value headline.

### Minute 11–13 — show reporting discipline

Reinforce the vocabulary:

**identified -> blocked / review-required -> claim-ready -> submitted / approved -> settled / recovered**

Only the final settlement state is recovered value.

### Minute 13–15 — convert to paid pilot

Propose a bounded real cohort:

- 3–10 aircraft / engines;
- one maintenance or redelivery event family;
- 1–3 entitlement families;
- fixed evidence boundary;
- fixed fee;
- no enterprise integration required for first proof.

The next commercial step is a paid Recovery Scan, not a platform rollout.

## Demo output invariant

If code changes ever cause the demo to report the blocked EUR 200k or review-required EUR 187.5k as claim-ready recovery, CI must fail.

The regression test in `tests/test_tap_synthetic_demo.py` locks this truth separation.
