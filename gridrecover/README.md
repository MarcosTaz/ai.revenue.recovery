# GRIDRECOVER — Interconnection Capital, Deposit & Network-Upgrade Recovery

Status: **BUILT / NOT PILOT READY / NOT MARKET VALIDATED**

## Initial wedge

Independent developer-side interconnection capital assurance for FERC-jurisdictional large-generator projects, starting with:

1. post-COD Network Upgrade repayment reconciliation where the executed/filed LGIA contains FERC pro forma Article 11.4/11.5 crediting language or a verified materially equivalent provision;
2. pre-COD cluster-withdrawal capital reconciliation where the Transmission Provider's effective tariff/LGIP supports Network Upgrade cost-assignment reductions, associated financial-security reductions, or return of residual withdrawal-penalty funds.

The FERC pro forma documents are only a baseline. A customer finding requires the actual effective Transmission Provider tariff/procedure and the project's executed/filed agreement to be source-bound and matched.

## Truth boundary

GRIDRECOVER does not infer recovery from a deposit, security amount, network-upgrade balance, withdrawal, project cancellation or accounting balance alone.

Every supported candidate must bind:

`project -> jurisdiction -> provider -> effective tariff/rule -> executed agreement -> clause -> event -> payment/security evidence -> calculation -> offsets/receipts -> candidate`

Unsupported applicability returns `UNKNOWN` or `NEEDS_REVIEW`, never a recovery amount.

## Current deterministic core

`evaluateNetworkUpgradeRepayment()` currently supports a narrow synthetic Article 11.4 repayment reconciliation and fails closed when:

- jurisdiction/project scope is unsupported;
- executed LGIA is missing;
- Article 11.4.1-equivalent language is not verified;
- agreement provenance is missing or superseded;
- payment provenance/project-purpose match is missing;
- repayment trigger/schedule is unverified;
- economics are invalid;
- receipts exceed the verified advance.

Interest is intentionally excluded from the deterministic candidate until the exact contractual/regulatory methodology and dates are separately source-supported.

## Commercial truth

- real customer cases: 0
- real project documents: 0
- verified customer recoveries/releases: 0
- paid pilots: 0
- revenue: 0
- willingness to pay: unproven

Synthetic tests prove only system behavior.

## Next critical build sequence

1. canonical project/agreement/evidence model;
2. provider-specific effective-tariff applicability layer;
3. cluster-withdrawal security/release engine;
4. adversarial synthetic case pack;
5. evidence-linked recovery dossier;
6. customer/project isolation and audit trail;
7. assisted pilot intake;
8. pilot-ready security/support gates;
9. real qualified project exposure and pricing tests.

No automatic merge.
