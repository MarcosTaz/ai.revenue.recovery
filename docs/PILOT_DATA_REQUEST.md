# Aviation Recovery — Pilot Data Request

This checklist is designed for a bounded assisted recovery pilot. Request the minimum data needed for the agreed scope; do not request an entire airline data estate by default.

## 1. Scope identifiers

For each in-scope asset/event:

- airline / lessee legal entity
- lessor / counterparty
- lease ID
- aircraft registration / MSN where relevant
- engine ESN or component identifier where relevant
- maintenance event type
- event start/completion date
- internal owner for Fleet/Lease/Engineering Finance

## 2. Governing contract package

Required for rule reconstruction:

- executed lease
- amendments
- side letters affecting maintenance, reserves, contributions, security or redelivery
- schedules/exhibits defining maintenance reserve rates, contribution mechanics, caps/floors/deductibles and claim procedures
- notices/consents that modify the governing position

Prefer PDF originals plus a simple document index.

## 3. Maintenance event evidence

Depending on entitlement type:

- MRO invoice(s)
- workscope / final workscope
- completion certificate / release-to-service evidence
- shop findings
- LLP/component detail where the lease calculation depends on life status
- technical records required by the relevant claim provision
- payment proof where payment is a condition to reimbursement

## 4. Reserve / contribution records

- lessor maintenance reserve statements
- reserve invoices and payment history
- fund balance by component / event category
- lessor contribution statements
- security deposit ledger
- prepaid rent ledger where in scope
- end-of-lease adjustment schedules where in scope

## 5. Prior claims and settlement history

- claims register
- prior claim packages
- lessor responses
- approved / rejected amounts
- debit/credit memos
- settlement agreements
- cash receipt or offset evidence

This prevents double recovery and helps reconstruct counterparty interpretation history.

## 6. Finance reconciliation inputs

Only where needed for the selected claims:

- AP invoice extract
- GL lines tied to the maintenance event
- payment ledger
- supplier credits / warranty recoveries that may affect eligible cost
- FX rate source if the lease requires currency normalization

## 7. Deadline / notice evidence

- submission deadline language
- notice addresses / portals / required delivery method
- prior notices sent
- acknowledgment dates
- any granted extensions or waivers

## 8. Minimum metadata format

A CSV/Excel index is sufficient for assisted onboarding with these columns:

`asset_id, lease_id, counterparty, entitlement_type, event_date, document_type, document_name, source_reference, currency, amount, notes`

## 9. Data minimization rules

Do not request:

- passenger data;
- crew personal records;
- unrelated HR data;
- unrelated operational safety data;
- full ERP exports when a scoped extract is sufficient.

If sensitive information appears incidentally, isolate and restrict it rather than expanding the pilot scope.

## 10. Pilot intake completeness gate

A candidate may be analysed with partial data, but it must be labelled with explicit gaps. External claim release remains blocked until the governing rule and every material calculation input have sufficient lineage for review.