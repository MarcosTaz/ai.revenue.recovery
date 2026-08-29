# Recovery Radar — Historical Pilot Data Request

Status: `EXTERNAL-READY DRAFT / NOT SENT / OWNER AUTHORIZATION REQUIRED`

Purpose: request the **minimum** records needed to test one closed historical customer program cancellation / severe volume reduction without requiring ERP access, live-system integration, or customer/OEM communication.

## Pilot boundary

The pilot is retrospective and local/offline. Recovery Radar does not submit a claim, contact the customer, negotiate settlement, provide a legal opinion, or assume that stranded cost is recoverable.

Please provide only records you are authorized to share for the selected historical matter. Stable aliases may replace customer/program/part names where needed, as long as the same aliases are used consistently across all records.

## 1 — Event evidence

Required:

- stable case / program alias;
- customer alias;
- cancellation, termination, stop-order, or severe volume-reduction date;
- customer notice, PO/release change, forecast change, or equivalent source showing the event;
- original expected volume / commitment where available;
- revised or cancelled volume / commitment;
- affected part/program identifiers or stable aliases.

Preferred formats: PDF, email export, spreadsheet/CSV, PO/release export, or other human-readable source file.

## 2 — Economic exposure

Provide one row per distinct economic loss. Do not combine currencies.

Minimum fields:

| Field | Meaning |
|---|---|
| economic_loss_id | Stable unique ID for the loss |
| category | RAW_MATERIAL / E_AND_O / WIP / FINISHED_GOODS / TOOLING / NRE / SUPPLIER_COMMITMENTS / DEDICATED_CAPACITY / OTHER |
| quantity | Quantity or cost-unit count |
| unit_cost | Source-basis unit cost |
| currency | Three-letter source currency, e.g. EUR / USD |
| cost_record | Ledger, inventory, invoice, tooling, engineering, or other cost source |
| ownership | SUPPLIER / CUSTOMER / UNKNOWN |
| program_link | How this cost is tied to the selected customer/program |

Where relevant also provide:

- reusable / transferable quantity or value;
- resale, scrap, reuse, supplier-cancellation, or other mitigation amount + source;
- prior credit, reimbursement, settlement, or payment amount + source;
- explanation for any allocation across multiple programs.

Do not net values manually if the gross cost, mitigation, and prior reimbursement can be supplied separately.

## 3 — Contractual / commercial basis

Provide the records the historical team actually relied on, including where the final conclusion was **non-recoverable**.

Useful records include:

- purchase order / sourcing award;
- supply agreement / terms and conditions;
- cancellation / termination clause;
- tooling agreement / approval;
- engineering or NRE authorization;
- customer commercial approval;
- relevant amendment/version history that existed around the event date;
- category-specific caps, exclusions, ownership, or mitigation requirements.

Do not pre-label a later contract/amendment as superseding an earlier one unless a knowledgeable reviewer can establish that applicability.

## 4 — Historical claim / internal recovery analysis

If one existed, provide:

- original submitted claim or internal recovery workbook;
- line/category amounts;
- supporting-document index;
- customer/auditor questions or challenged lines;
- revised claim versions;
- internal reviewer notes where authorized.

This is highly valuable for measuring completeness and overclaim prevention, but is not required merely to import the event/exposure records.

## 5 — Historical outcome / ground truth

After Recovery Radar's first-pass output has been frozen, a knowledgeable reviewer should prepare the comparison truth independently where practical.

Please record, if known and authorized:

- lines/categories accepted as recoverable;
- lines/categories rejected / written off / unresolved;
- reasons for material differences;
- final accepted or settled amount by currency;
- payment amount/date/evidence if paid;
- whether physical inspection materially affected the historical decision;
- whether legal/commercial negotiation changed the outcome independently of documentary support.

A settlement is an observed commercial outcome, not automatic proof that every line was legally right or wrong.

## 6 — Operational measurement

If reconstructable, record:

- analyst preparation time;
- reviewer time;
- major evidence-state corrections;
- major entitlement-state corrections;
- missing-evidence requests that were useful / not useful;
- whether the team would repeat this workflow on another historical case.

These metrics measure workflow usefulness. They do not establish willingness to pay.

## File-handling rules

For the first pilot:

- no production credentials;
- no ERP write access;
- no unrelated customer/program records;
- no live customer/OEM communication;
- no source files larger than needed for the selected case;
- raw evidence files remain in the operator-controlled pilot directory; Recovery Radar persists structured records plus evidence metadata/content hashes, not the raw document bytes;
- mixed currencies remain separate;
- missing evidence remains explicitly missing rather than being reconstructed from memory.

## Minimum viable dataset

A case is usually usable for first-pass analysis when all of the following exist:

1. one evidenced cancellation/termination/reduction event;
2. at least one program-linked economic-loss line with a cost/inventory/tooling/engineering record;
3. at least one relevant contractual/commercial basis record **or an explicit absence that can be measured**;
4. ownership status for material assets/costs where relevant;
5. mitigation/prior reimbursement records where non-zero;
6. a knowledgeable independent reviewer for the historical comparison.

A known historical submitted/settled/paid outcome makes the case substantially stronger for T2 validation, but Recovery Radar can also correctly test a zero-recovery or non-recoverable case.

## Before sending files

Confirm only:

- the matter is closed/historical or explicitly authorized for retrospective analysis;
- the sender is authorized to share the selected records;
- unrelated customer/program information has been removed or isolated;
- a separate reviewer can later prepare the historical ground truth without being instructed to match Recovery Radar's output.

If any of these cannot be satisfied, stop before data transfer and re-scope the pilot.

No data has been requested or received by this Factory yet.
