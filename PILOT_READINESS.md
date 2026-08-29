# GovMargin Gate 10 — pilot readiness

Current state: **NOT YET PILOT-READY / DESIGN-PARTNER-READY FOR SYNTHETIC DEMO ONLY**.

GovMargin may become assisted-pilot capable before full SaaS production readiness, but Gate 10 still requires a safe path for real contractor data and at least one controlled real-contractor execution. Synthetic engineering alone is insufficient.

## Gate 10 checklist

| Capability | State | Evidence / remaining work |
|---|---|---|
| Wedge frozen | PASS / NARROWED | Initial wedge is independent cross-system historical final-rate / closeout assurance for cost-reimbursement / CPFF contracts with FAR 52.216-7, settled final rates and fragmented historical truth. |
| Competitor kill-test | PASS WITH DOWNGRADE | Costpoint already supports cumulative claimed-vs-billed, over/under-billing adjustment identification and final billing/payment reporting. GovMargin must prove incremental value outside ordinary incumbent workflow. |
| Contract-type applicability guard | CORE PASS | CPFF/cost-reimbursement only when 52.216-7 and settled-rate evidence are present. T&M/LH/FFP fail closed unless dedicated logic exists. |
| Deterministic settled-rate true-up | PASS | Python + browser engines fail closed on unsupported terms/rates/numeric inputs. |
| Ceiling / funding safeguards | CORE PASS | 52.232-20/-22 rule objects + deterministic clause-specific safeguards; no automatic receivable from notice/excess conditions. |
| Final voucher reconciliation | CORE PASS | Settled-rate/physical-completion/evidence/release gates implemented. |
| Final payment reconciliation | CORE PASS | Approved completion voucher vs verified cumulative payments and evidenced refunds/credits/offsets; receivable/payable symmetry implemented. |
| Direct cost / ODC reconciliation | CORE PASS | Allowability/allocability/billability states supported; full Part 31 coverage remains broader work. |
| Fee reconciliation | CORE PASS | Supported fixed/percentage paths with fee ceiling. Commercial GovMargin pricing is fixed-fee; success-linked compensation disabled. |
| Multi-pool indirect calculation | CORE PASS | Supported settled pools deterministic; unsupported allocation judgment remains review-gated. |
| Payment reconciliation | CORE PASS | Verified invoice/payment shortfall and overpayment paths exist. |
| Synthetic A–Z portfolio | PASS AT TESTED CODE CHECKPOINT | False-positive traps assert no recovery; current suite includes broader funding/security/review tests. |
| Evidence lineage | CORE PASS | Evidence IDs, SHA-256, source locator, timestamp and rule IDs required for normalized bundles. |
| Raw evidence admission policy | CORE PASS AS GATE ONLY | `govmargin/evidence_intake.py` enforces tenant/filename/type/size/hash/external scan status. Unscanned/macro-enabled/invalid files fail closed. Actual scanner/object store/parser isolation remain absent. |
| Tenant-scoped normalized import | CORE PASS | CSV transaction/invoice importer rejects cross-tenant and duplicate data. |
| Tenant storage contract | CORE PASS AS REFERENCE ONLY | Immutable tenant-scoped reference store tested; not encrypted/durable production persistence. |
| Domain authorization | CORE PASS | ADMIN/ANALYST/REVIEWER/VIEWER role separation and cross-tenant denial. |
| Verified-session boundary | CORE PASS AS CONTRACT ONLY | `VerifiedSession` rejects unverified/expired/future/cross-tenant/role escalation. Production IdP cryptographic verification is still absent. |
| Human review | CORE PASS | Reviewer identity/role/decision/rationale/timestamp. Unreviewed recovery remains DRAFT. |
| Multi-review policy | CORE PASS | Recovery pack can require multiple independent approvals; duplicate reviewer or blocking review prevents promotion. |
| Recovery/evidence pack | CORE PASS | Recovery candidates, payables and unresolved states remain separate. |
| Tamper-evident audit primitive | CORE PASS | SHA-256 chained append-only reference primitive detects mutation/reordering/duplicates. Production persistent audit store absent. |
| Operation audit trace | CORE PASS AS REFERENCE | Trace builder links operation/review/output events to evidence IDs. Direct secure-operation integration write was connector-blocked and remains open. |
| Log redaction | CORE PASS | Structured reference redaction removes sensitive bank/tax/employee/raw-document/credential fields from log-safe payloads. |
| Customer-data operating policy | PASS AS SPEC | Real confidential data prohibited in repo/current synthetic web. Secure transfer/storage/retention/deletion prerequisites documented. Root `.gitignore` hardening attempted but connector-blocked. |
| Assisted-pilot input contract | PASS AS SPEC | `ASSISTED_PILOT_CHECKLIST.md` defines contract/rate/cost/billing/funding evidence and review gates. |
| Fixed-fee legal/commercial posture | PASS AS OPERATING RULE | `LEGAL_BOUNDARY.md`: fixed fees/subscriptions enabled as hypotheses; success-linked compensation/claim assignment disabled pending qualified review. |
| Pilot unit economics | PASS AS MODEL ONLY | Deterministic margin model exists. $7.5k/40h planning example is not market validation. |
| Partner channel map | PASS AS RESEARCH ONLY | Redstone/GRF/Aprio/PilieroMazza mapped as overlap/partner-validation targets; no signed partner. |
| Web synthetic workflow | CORE PASS | True-up + funding safeguard + human-review simulation + review-pack status. No real-data upload/review route. |
| Full Python test runner | PASS AT CODE CHECKPOINT | P0 unittest/pytest coverage defect fixed; workflow runs all pytest tests. Latest verified pre-doc checkpoint executed complete suite successfully. |
| Web test/build | PASS AT CODE CHECKPOINT | Deterministic browser tests + production Next build green on tested code checkpoint. |
| Security CI | PASS AT CODE CHECKPOINT | Python compile check + production npm dependency audit green after workflow repair. |
| Root repo secret/customer-data ignore | BLOCKED | `.gitignore` mutation was attempted and blocked by the connected GitHub safety layer. Policy still prohibits real customer data in repo. |
| Production authentication / IdP | NOT PASSED | No real IdP/session verification integration. |
| Persistent encrypted tenant datastore | NOT PASSED | No production DB/object store selected/configured. |
| Actual malware scanner / parser sandbox | NOT PASSED | Admission contract exists; service integration absent. |
| Persistent append-only audit history | NOT PASSED | Reference chain exists; production persistence absent. |
| Production backup / recovery / deletion | NOT PASSED | Policy/spec exists; no production datastore to exercise. |
| Dedicated deployment project | EXTERNALLY BLOCKED | Connected Vercel account contains unrelated projects and no GovMargin project; do not deploy into another product. |
| Real contractor data | NOT TESTED | No customer dataset processed. |
| Qualified accounting/legal review | NOT COMPLETED | Needed for reserved activities and any success-linked compensation. |
| Paid design partner | NONE | No paid customer. |
| Verified real incremental value vs incumbent workflow | NONE | Critical post-Costpoint-downgrade proof still absent. |
| Collected recovery / corrected payable | NONE | No verified real outcome. |

## CI truth

A prior P0 was found because the workflow used `unittest discover` while some new tests were pytest-style functions. The workflow now installs/runs `pytest`, so mixed test styles are actually executed.

Verified checkpoints during this execution slice include:

- Python functional suite green after the full-runner correction;
- web deterministic tests and Next production build green;
- Python source compile security job green;
- production npm dependency audit green.

Any later code-bearing HEAD must pass the same gates before being treated as verified.

## External infrastructure boundary

Gate 10 cannot be manufactured from reference code. Before real confidential customer documents enter the product, production infrastructure must provide:

1. cryptographically verified identity/session integration;
2. server-side tenant authorization;
3. encrypted persistent tenant data store;
4. immutable raw evidence storage;
5. actual malware/security scanning;
6. parser isolation;
7. persistent tamper-evident audit history;
8. secrets management;
9. backup/recovery and tested deletion;
10. production log redaction/telemetry policy;
11. dedicated deployment project/environment.

## Gate 10 real terminal path

Before changing Gate 10 to PASS, execute one controlled real-contractor engagement through:

`REAL CONTRACTOR → SECURE DATA HANDLING APPROVED → REAL CONTRACT/ORDERS/MODS → SOURCE-HASHED RATE/ACCOUNTING/BILLING/PAYMENT DATA → APPLICABLE RULES → DETERMINISTIC ECONOMICS → FUNDING/CEILING/CLOSEOUT GATES → HUMAN REVIEW → EVIDENCE PACK → CLIENT FINANCE VALIDATION`

The pilot must also record whether the finding was incremental to the customer's ordinary ERP/accountant process. After the stronger Costpoint evidence, a variance that Costpoint/current advisers had already surfaced does not validate GovMargin's independent-overlay wedge.

## Safe pre-pilot exposure

It is safe to demonstrate the current synthetic product and recruit a design partner while describing the product accurately as:

- pre-pilot / synthetic engineering surface;
- fixed-fee audit hypothesis;
- not legal advice;
- not CPA attestation;
- not an automated Government claim generator;
- not guaranteed to find a recovery;
- equally capable of surfacing payables/overbilling;
- designed to test independent cross-system historical reconciliation.

Do not ingest sensitive real customer documents into the current web/repository surface.
