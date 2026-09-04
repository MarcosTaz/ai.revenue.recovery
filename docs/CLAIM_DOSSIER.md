# Aviation Recovery Claim Dossier Standard

Every proposed recovery must be reproducible by a reviewer who was not involved in the original analysis.

## 1. Executive claim card

- Claim ID
- Airline / lessee entity
- Lessor / counterparty
- Aircraft / engine / component identifier
- Lease ID and governing amendment/version
- Entitlement type
- Event date
- Contractual submission deadline
- Currency
- Gross contractual entitlement
- Prior payments / prior claims
- Net recoverable amount
- Current status: blocked / review required / claim ready / submitted / settled / rejected

## 2. Contract rule map

For each material rule:

- source document
- clause / schedule / exhibit
- effective dates
- entitlement trigger
- eligible cost definition
- excluded cost definition
- reserve or contribution mechanics
- caps / floors / deductibles
- escalation or indexation
- FX mechanics
- taxes / withholding treatment if contractually relevant
- submission deadline / notice mechanics
- required evidence
- approval discretion or conditions precedent

No rule is inferred when the source term is unknown. Unknown terms become blocking issues.

## 3. Maintenance-event evidence

Minimum expected evidence depends on the lease, but the product must be able to reference:

- MRO invoice(s)
- workscope
- shop findings / completion certificate
- LLP or life-limited component data where relevant
- aircraft / engine / component identifiers
- event completion date
- payment evidence
- technical records supporting qualifying event status

## 4. Financial reconciliation

The dossier must show:

- eligible cost build-up
- excluded/non-reimbursable line items
- reserve fund or lessor-contribution balance
- prior reimbursements
- claims already submitted
- credits / rebates / warranty recoveries affecting eligible cost when contractually required
- caps, floors, deductibles and contribution percentages
- resulting gross entitlement
- offsets
- net recovery candidate

## 5. Red-team checks

Before `claim_ready`, test for:

1. wrong lease or amendment version
2. event outside rule effective period
3. wrong aircraft/engine/component mapping
4. duplicate invoice or duplicate claim
5. non-qualifying maintenance event
6. excluded betterment / upgrade cost included
7. warranty or supplier credit not netted where required
8. cap/floor/deductible misapplied
9. reserve balance overstated
10. prior reimbursement omitted
11. deadline expired or approaching
12. missing notice / approval prerequisite
13. evidence mismatch between invoice, workscope and asset
14. currency mismatch or unapproved FX normalization
15. calculation that cannot be recreated from stored inputs

## 6. Human review

A human reviewer must explicitly accept or reject every material exception. Evidence waivers must be recorded with reviewer identity, timestamp and reason in the production implementation.

## 7. Submission package

The external-facing package should contain only what the lease requires plus a concise calculation schedule. Internal red-team notes remain in the audit trail unless strategically appropriate to disclose.

## 8. Settlement truth

A claim is not counted as recovered merely because it was submitted or acknowledged. Recovery closes only when settlement evidence exists, such as cash receipt, credit memo, offset confirmation or another contractually valid economic settlement.