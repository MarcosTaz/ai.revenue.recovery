# Synthetic contractor portfolio A–Z

This portfolio is a truth table for GovMargin. Every case now has an executable path in `govmargin.synthetic` and an automated expected-state assertion in `tests/test_synthetic_portfolio.py`.

A synthetic PASS proves the implementation handles the designed trap. It does **not** prove real-world recovery frequency, legal entitlement or customer data quality.

| Case | Scenario | Expected truth |
|---|---|---|
| A | all rates correct, nothing recoverable | `NO_VARIANCE` |
| B | settled final indirect rate > cumulative billed economics | `RECOVERY_CANDIDATE` after gates |
| C | settled final economics < cumulative billings | `PAYABLE_CANDIDATE` |
| D | unallowable cost was billed | `PAYABLE_CANDIDATE` |
| E | supported allowable/allocable/billable cost omitted | `RECOVERY_CANDIDATE` |
| F | wrong / unsupported allocation base | `REQUIRES_REVIEW` |
| G | wrong / unsupported cost pool | `REQUIRES_REVIEW` |
| H | ceiling prevents additional billing | `NO_VARIANCE` in constrained synthetic case |
| I | funding limitation blocks positive variance | `REQUIRES_REVIEW` |
| J | unbilled allowable ODC | `RECOVERY_CANDIDATE` only when contract-billable |
| K | ODC not contractually billable | `NO_VARIANCE` when not previously billed |
| L | supported fixed-fee balance omitted | `RECOVERY_CANDIDATE` subject to fee terms/ceiling |
| M | modification adds funding | contract state changes only from supported modification; no recovery inferred solely from funding |
| N | modification changes ceiling | effective version controls ceiling; no recovery inferred solely from modification |
| O | prior invoice already contains amount | `NO_VARIANCE` |
| P | verified invoice payment shortfall | `RECOVERY_CANDIDATE` unless disputed/withheld |
| Q | final voucher omits supported economics before release blocker | `RECOVERY_CANDIDATE` |
| R | signed general release with apparent positive variance | `REQUIRES_REVIEW` |
| S | accounting-system migration without supported lineage | `UNKNOWN` |
| T | multiple task-order context | order-level candidate remains constrained to supported order funding/ceiling |
| U | multiple supported indirect pools | deterministic reproducible calculation, no variance by itself |
| V | wrong regulatory-version trap | `UNKNOWN`; current rule does not auto-apply to historic contract |
| W | contractor believes amount is due but cost is supported unallowable | `NO_VARIANCE` if unbilled; never recovery |
| X | insufficient contract evidence | `UNKNOWN` |
| Y | duplicate transaction | excluded; `NO_VARIANCE` |
| Z | positive arithmetic under provisional/unsettled rate | `REQUIRES_REVIEW`, never recovery |

## Explicit false-positive traps

Cases `C D F G H I K M N O R S W X Y Z` are asserted never to emit `RECOVERY_CANDIDATE` under their defined scenario.

Positive cases are deliberately limited to `B E J L P Q T`, each of which has a specific supported path rather than generic “unbilled = due” logic.

## Gate 9 status

**LOCAL PASS: A–Z executable, 46-test full Python suite GREEN as of 2026-08-29.**

Gate 9 becomes **CI PASS** only when the branch workflow independently executes the current HEAD successfully. Gate 10 remains open because real-file ingestion, tenant/auth controls, human-review workflow and an end-to-end evidence pack still require implementation and verification.
