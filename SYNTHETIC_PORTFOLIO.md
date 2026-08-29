# Synthetic contractor portfolio A–Z

This portfolio is a truth table for product development. A case is not considered PASS until the relevant engine path exists and has an automated assertion.

| Case | Scenario | Expected truth |
|---|---|---|
| A | All rates and billings correct | NO_VARIANCE |
| B | Settled final indirect rate > billed economics | RECOVERY_CANDIDATE if every limitation passes |
| C | Settled final indirect rate < billed economics | PAYABLE_CANDIDATE |
| D | Unallowable cost included | SUPPORTED_UNALLOWABLE / remove from entitlement |
| E | Supported allowable cost excluded | candidate only after allocability + contract terms pass |
| F | Wrong allocation base | REQUIRES_REVIEW until corrected deterministically |
| G | Wrong cost pool | REQUIRES_REVIEW until corrected deterministically |
| H | Ceiling prevents incremental billing | NO_RECOVERY / ceiling-constrained |
| I | Funding limitation prevents asserted recovery | REQUIRES_REVIEW; never auto-create receivable |
| J | Unbilled allowable ODC | RECOVERY_CANDIDATE only if contractually billable |
| K | ODC not contractually billable | NO_RECOVERY |
| L | Fee miscalculated | variance only after fee clause and formula are evidenced |
| M | Modification adds funding | funding ledger updates; no entitlement inferred solely from added funding |
| N | Modification changes ceiling | use effective contract version / modified ceiling |
| O | Prior invoice already contains amount | NO_DUPLICATE_RECOVERY |
| P | Payment shortfall after valid invoice | RECEIVABLE_CANDIDATE subject to payment evidence |
| Q | Final voucher missing supported amount | RECOVERY_CANDIDATE before release/deadline blockers |
| R | Contract already closed / release executed | REQUIRES_LEGAL_REVIEW; do not claim recoverability |
| S | Accounting-system migration | reconcile lineage across old/new ledgers; UNKNOWN where lineage breaks |
| T | Multiple task orders | calculate per applicable order ceilings/funding/terms |
| U | Multiple indirect pools | deterministic multi-layer allocation |
| V | Wrong regulatory-version trap | UNKNOWN / reject current rule until version applicability is proven |
| W | Contractor believes amount is due but expressly unallowable | SUPPORTED_UNALLOWABLE / NO_RECOVERY |
| X | Insufficient evidence | UNKNOWN |
| Y | Duplicate transaction | exclude duplicate and flag data-quality event |
| Z | False-positive recovery trap | NO_RECOVERY; P0 if product asserts receivable |

## Current automated coverage

Automated now: A, B, C, H (simple indirect ceiling), I (funding fail-closed), O (through cumulative billed amount), V (current rule applicability guard), X.

Partial / not yet implemented: D, E, F, G, J, K, L, M, N, P, Q, R, S, T, U, W, Y, Z.

Gate 9 remains **NOT PASSED** until every A–Z path has executable tests and the false-recovery traps remain zero.