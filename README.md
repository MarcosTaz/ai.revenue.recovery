# Recovery Radar

Evidence-first supplier-side cancellation-claim pre-audit for customer program cancellation or severe volume reduction.

## Current product truth — v0.2.1

Source is isolated on `recovery-radar/program-cancellation-claims`; `main` remains untouched.

Recovery Radar is currently a **controlled assisted-pilot application**, exposed through a local operator CLI. It is **not** a public SaaS, production IAM deployment, autonomous legal-liability engine, or proof of commercial demand.

### Start here

For the shortest supported historical-pilot path, use `PILOT_START_HERE.md`.

Supporting material:

- `PILOT_ACQUISITION.md` — evidence-backed candidate/qualification plan;
- `PILOT_OUTREACH_DRAFTS.md` — prepared but **NOT SENT** outreach drafts;
- `PILOT_OFFER.md` — current unvalidated €4,500 ex-VAT fixed-scope price hypothesis;
- `PILOT_ONE_PAGER.md` — buyer-facing pilot explanation;
- `PILOT_DATA_REQUEST.md` — minimum authorized historical data request;
- `PILOT_DATA_HANDLING.md` — exact local confidentiality/security boundary without production-security claims;
- `PILOT_RUNBOOK.md` — controlled assisted execution and T2 measurement protocol;
- `examples/pilot-bundle-template.json` — parser-aligned normalized input template;
- `examples/ground-truth-template.json` — fail-closed ground-truth template starting at `case_origin=UNKNOWN`.

No outreach has been sent and no real supplier dataset has been received by this Factory.

Implemented and tested:

- deterministic cancellation / volume-reduction event model;
- stranded exposure categories: raw material, E&O, WIP, finished goods, tooling, NRE, supplier commitments and dedicated capacity;
- mitigation and prior-reimbursement deduction;
- exposure != entitlement != claimability != settlement != payment;
- ownership fail-closed checks;
- duplicate economic-loss and duplicate economic-representation protection;
- mixed-currency fail-closed handling with totals separated by currency and no false scalar aggregation;
- non-finite and unsupported-range economic input rejection;
- missing-evidence detection plus line-specific retrieval actions without invented obtainability probability;
- partial support with defensible caps and legal/high-risk review routing;
- independent arithmetic and claim-line ground-truth scoring;
- settlement/payment workflow where `SETTLED != PAID`;
- multiple evidenced payments with duplicate/currency/overpayment controls;
- tenant-scoped SQLite persistence for events, exposures, entitlements, claim cases, evidence metadata/hashes, reviews and audit events;
- token-authenticated local application gateway; workspace and role are derived from the credential, not caller-selected business parameters;
- one-time bootstrap/admin credential, PBKDF-protected stored API-key secrets, key revocation and tenant-scoped roles;
- independent evidence verification: registration/upload != verification;
- independent entitlement verification: analyst-entered support state != verified entitlement;
- reviewer cannot source-write, submit, settle or record payment;
- same actor cannot create evidence/entitlement and then independently verify it under another role;
- SHA-256 evidence registry with duplicate/version conflict and scope controls;
- documentary disagreements and ambiguous contract versions fail closed rather than silently selecting precedence;
- registered-and-reviewed evidence claimability gate for event, cost/inventory, contractual/support and conditional mitigation/reimbursement evidence;
- deterministic claim package with calculation trace, lineage, uncertainty, missing-evidence actions and draft-claim output;
- canonical claim-package export with SHA-256 manifest, atomic write, fsync, round-trip verification and tamper detection;
- verified SQLite backup with integrity / foreign-key checks and whole-database truth digest;
- rollback protection for interrupted critical writes;
- DB-lock, concurrency, retry and corrupted-backup adversarial tests;
- application-schema compatibility gate that refuses unknown newer schemas and requires explicit migration for older versions;
- strict pilot-bundle loader with size limits, enum/type validation, path-escape/symlink controls and evidence hashes derived from concrete file bytes;
- atomic, retry-safe pilot-bundle ingestion: event/exposure/entitlement/evidence/audit commit together or roll back together;
- assisted-pilot CLI: `bootstrap`, `issue-key`, `import-bundle`, `review-evidence`, `review-entitlement`, `package`, `export`, `create-case`, `score-historical`;
- strict historical-ground-truth input adapter with explicit case origin, completeness flag, FP/FN/state/currency/value measurement and operational metrics;
- WTP truth boundary: a text/reference can be recorded, but cannot self-promote WTP beyond `UNKNOWN_EXTERNAL`;
- historical scorecard output with final-artifact SHA-256 binding, deterministic JSON envelope and atomic/fsync export;
- synthetic scorecards are explicitly `NON_REAL_CASE_MEASUREMENT_ONLY` and can never auto-promote T2;
- deterministic correctness acceptance with 2,000 claim lines;
- broad synthetic/adversarial portfolio covering full, partial and zero recovery, prior compensation, mitigation, WIP/FG, NRE, supplier commitments, missing evidence, unsupported/expired representations, documentary conflict, duplicate economics, mixed currency and failure recovery;
- executable example bundle/ground-truth templates tested against the current parsers so pilot onboarding examples cannot silently drift from implementation.

### Claimability boundary

The economic engine may identify a candidate amount from normalized records. That amount does not become usable claim-package money merely because source-reference strings exist.

For the assisted-pilot application, required source records must be registered, correctly scoped and currently `VERIFIED` by an independent reviewer. The related entitlement interpretation must also be independently `VERIFIED`. Failure of either boundary keeps or returns the line to a non-claimable/review state.

`CLAIMABLE` remains an internal economic/evidence workflow conclusion. It is **not** legal certainty, customer acceptance, settlement or cash.

### Evidence and contract-version boundary

Recovery Radar stores evidence identity, metadata and content hashes; it does not persist raw evidence bytes. Pilot-bundle evidence hashes are derived from local file bytes, not accepted from a caller-provided hash.

If multiple registered documents compete for the same source identity, the system fails closed as ambiguous. It does not infer that a later contract automatically supersedes an earlier contract. Contract precedence remains a human commercial/legal decision.

### Currency boundary

Recovery Radar does not add EUR + USD (or any other mixed currencies) into one scalar amount. Mixed-currency analyses expose `totals_by_currency`, mark the package `MULTI_CURRENCY_SPLIT_REQUIRED`, and cannot create a single claim case until the currencies are split or otherwise handled outside the current model.

### Assisted-pilot operating boundary

The supported T1 path is:

`workspace bootstrap → distinct analyst/reviewer identities → normalized historical bundle import → independent evidence + entitlement review → evidence-gated analysis → package → deterministic export → optional internal claim case → explicit historical ground truth → deterministic scorecard`.

External claim submission, OEM/supplier communication, negotiation, settlement action, production hosting and production IAM are outside the T1 assisted-pilot boundary.

### T2 measurement boundary

`score-historical` compares the current gated analysis to an explicit `RECOVERY_RADAR_GROUND_TRUTH_V1` file and writes a deterministic `RECOVERY_RADAR_T2_SCORECARD_V1` artifact.

The scorecard measures false positives, false negatives, state mismatches, currency mismatches, amount error by currency and supplied operational metrics. `case_origin=REAL_AUTHORIZED_HISTORICAL_CASE` only labels the measurement input; it is **not proof of authorization and does not auto-promote T2**. `terminal_promotion` is always `NOT_INFERRED_FROM_SCORECARD`.

The copyable default ground-truth template starts at `case_origin=UNKNOWN`, `ground_truth_complete=false` and an `UNKNOWN` line disposition to avoid creating real-case status through copy/paste.

Synthetic or self-declared evidence cannot establish customer acceptance, recovered cash or willingness to pay.

## Current verification

Exact commit `13ebeb2aa75ee52427623cccf0f1f223c2bf2750` passed GitHub Actions with **147 tests** on Python 3.13.15.

Subsequent onboarding/template/documentation commits include executable-template regression tests and require their own exact-head CI observation before the newest branch HEAD is called GREEN.

## Business truth

`SIGNAL / HIGH COMPETITIVE COLLISION / WTP UNKNOWN / COMMERCIAL SUCCESS UNPROVEN`.

Synthetic correctness, pilot capability and a safe assisted workflow are **not** evidence of willingness to pay, collectibility, real-world claim acceptance or recovered revenue.
