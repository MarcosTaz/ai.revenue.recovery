# AERVIND Operator Console

Status: **READY FOR ASSISTED PILOT USE**

The Operator Console is a thin browser interface over the existing deterministic AERVIND recovery engine. It is intentionally an **operator tool**, not a customer-facing multi-tenant SaaS product.

## Purpose

The console makes the first paid Recovery Scan operational without requiring a customer to adopt new software or grant access to ERP, M&E, lease-management or banking systems.

The customer supplies a bounded exported evidence cohort. AERVIND loads the normalized JSON representation, evaluates the entitlement rules, exposes blockers and lineage gaps, and produces a candidate register plus executive report.

Canonical chain:

`lease rule -> maintenance event -> financial inputs -> evidence -> entitlement calculation -> blocker/review gate -> candidate register -> executive report`

External claim submission remains a separate human-approved step.

## Start

No third-party Python packages are required.

```bash
python operator_app.py
```

Then open:

```text
http://127.0.0.1:8080
```

Optional binding:

```bash
python operator_app.py --host 127.0.0.1 --port 8090
```

Do not bind the assisted console to a public interface unless an engagement-specific deployment/security design has been approved.

## Operator workflow

1. Load a customer-normalized Recovery Scan JSON cohort, or the synthetic example for demonstration.
2. Evaluate the cohort.
3. Review the recovery-truth summary.
4. Inspect each candidate's blockers, warnings, evidence references, lineage gaps and calculation trace.
5. Export the evaluated JSON and executive Markdown report.
6. Resolve evidence gaps or contract-review questions outside the console.
7. Re-run the cohort after controlled changes.
8. Externalize only claim-ready items that pass the existing dossier/human-release gates.
9. Track submission, approval and settlement in the canonical claim workflow.

## What the console does

- evaluates the same `aviation_io.evaluate_payload` path used by the CLI;
- preserves deterministic calculation and recovery-truth rules;
- exposes claim-ready, review-required and blocked values separately;
- renders a sortable candidate register;
- opens a detailed review view per candidate;
- exposes evidence IDs, source-lineage gaps and calculation trace;
- exports the evaluated payload;
- renders/exports the executive recovery report;
- includes a synthetic example loader for safe demonstrations.

## What the console deliberately does not do

- no customer login;
- no tenant administration;
- no SSO/MFA;
- no cloud persistence;
- no automatic document extraction;
- no automatic legal interpretation;
- no external claim submission;
- no automatic settlement recognition;
- no direct ERP/M&E/bank access;
- no hidden background synchronization.

Those are not accidental omissions. They keep the first paid engagement bounded and reduce customer security/procurement friction until real buyer evidence justifies scale work.

## Data handling

The standard server binds to `127.0.0.1` and processes request payloads in memory. It does not write submitted customer payloads to disk and sends `Cache-Control: no-store` on responses.

The operator remains responsible for the approved engagement-specific storage/transfer method for source documents and normalized cohorts. Do not treat the console itself as a document repository.

Request bodies are limited to 2 MB. Large source documents should remain in the approved evidence repository and be represented by controlled source references in the normalized payload rather than embedded in the JSON.

## Recovery truth

The UI intentionally displays **Verified recovered = 0** for a scan evaluation unless settlement evidence is separately represented through the canonical claim workflow.

Claim-ready value is not recovered cash.
Review-required value is not recovered cash.
Blocked potential is not recovered cash.
Submitted or approved value is not recovered cash.

Only evidence-backed economic settlement may be reported as recovered.

## Synthetic demonstration

`Load synthetic example` reads `examples/pilot.json`.

The UI labels it as synthetic. It must never be represented as airline data, a discovered customer leakage amount or proof that a target account has missed entitlements.

## Acceptance gate

Before using the console on real airline data:

- confidentiality/commercial terms are in place;
- the scoped asset/event population is agreed;
- the customer-approved data transfer/storage route is known;
- the governing lease/amendment set is available;
- an accountable human reviewer is named;
- no public network exposure is introduced by convenience;
- exports are stored only in the agreed engagement location.

## Scale trigger

Do not turn this console into self-service enterprise SaaS by default. Add persistence, tenancy, RBAC, SSO, document ingestion or deep integrations only when a real paid engagement demonstrates repeatable value or a buyer makes the capability a procurement requirement.
