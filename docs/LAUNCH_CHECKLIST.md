# AERVIND — Zero-Overhead Launch Checklist

_Last reviewed: 2026-09-05_

## Current execution boundary

**NO REAL OUTREACH / NO REAL EXTERNAL SEND** until the founder explicitly lifts this hold.

Allowed while the hold is active:

- product engineering and tests;
- synthetic demonstrations;
- public-source research;
- private account briefs and buyer-route research;
- website/DNS/mail infrastructure configuration that does not message a real person;
- draft emails, proposals and meeting material that remain unsent;
- inbound monitoring and reply drafting without sending.

Not allowed while the hold is active:

- email, LinkedIn message, contact-form submission or other message to a real prospect, partner, supplier or airline;
- automated outbound test to a real external mailbox;
- enrolling real contacts in outreach sequences;
- external claim submission or counterparty communication.

The hold overrides any older document that describes outreach as open. Preparing outreach is not authorization to send it.

## Already complete

- [x] Canonical brand: AERVIND
- [x] Product descriptor: Aviation Lease Entitlement Recovery
- [x] Canonical first offer: Recovery Scan — EUR 9,500
- [x] Deterministic entitlement engine
- [x] Evidence-lineage and human externalization gates
- [x] Settlement-truth reporting
- [x] Auditable external lifecycle and portable case state
- [x] Local operator console
- [x] Loopback-only network boundary and Host/Origin hardening
- [x] Synthetic airline demos
- [x] Ten private account-specific Recovery Exposure Briefs
- [x] Private buyer-route register and operating plan
- [x] Capability statement
- [x] Pilot SOW / data request / client intake guide
- [x] Security/confidentiality baseline
- [x] Static commercial landing page
- [x] Static Vercel deployment configuration
- [x] Vercel project `aervind` created
- [x] Canonical landing page deployed and HTTP/HTTPS runtime checked at `aervind.vercel.app`
- [x] Vercel runtime checked with no observed runtime errors at deployment validation time
- [x] Initial legal operating model documented: real Portuguese individual professional trading as AERVIND where legally appropriate
- [x] Company incorporation removed from pre-revenue critical path
- [x] **aervind.com** registered through Porkbun on 2026-09-04
- [x] Real-outreach hold is repository-enforced and regression-tested

## Remaining domain / web gate

- [x] Purchase **aervind.com**.
- [x] Create and validate the static Vercel project/deployment.
- [x] Verify temporary-host HTTPS and core security headers.
- [ ] Attach **aervind.com** to the Vercel project.
- [ ] Publish the Vercel-required website DNS records in Porkbun.
- [ ] Verify `https://aervind.com` and canonical redirect/host behavior.
- [ ] Only after the official domain is verified, permit search indexing of the public marketing site.

Until the custom domain is attached, `aervind.vercel.app` is a **technical temporary host**, not the canonical public business address.

The domain is already owned. Do not buy secondary domains or paid hosting merely for appearance before proof requires them.

## Remaining branded-email gate

- [x] Claim `aervind.com` in the selected Primitive Email organization.
- [x] Re-check Primitive verification status without sending any message.
- [ ] Publish required MX / ownership / SPF / DKIM / DMARC / TLS-RPT records in Porkbun.
- [ ] Re-run Primitive DNS verification with no real-recipient message.
- [ ] Keep any real-recipient inbound/outbound delivery test disabled while the real-outreach hold is active.

Latest verified infrastructure truth on 2026-09-05: Primitive reports the MX and `_primitive` ownership records as missing, and SPF/DKIM/DMARC/TLS-RPT as not matching the required values. Branded mail must therefore **not** be described as live or verified.

See `docs/EMAIL_OPERATIONS.md`.

## Portuguese activity truth before first paid service

- [ ] Verify the operator's real Portuguese activity registration.
- [ ] If needed, add an activity classification that covers AERVIND's actual service. Current working classification: **CAE Rev.4 70200 — Atividades de consultoria para os negócios e outra consultoria para a gestão**.
- [ ] Verify customer-specific VAT/invoicing treatment before signature/invoice.
- [ ] Do not place the operator's NIF, tax address or banking data in the public repository.

## Per-customer gate before signature / evidence intake

- [ ] Founder has explicitly lifted the real-outreach hold for the relevant commercial process.
- [ ] Real customer legal entity identified.
- [ ] Billing address / VAT or tax identifier verified where applicable.
- [ ] Customer accepts the truthful initial supplier model or explicitly requires a company.
- [ ] Scope and price agreed.
- [ ] Applicable VAT / invoicing treatment verified.
- [ ] Procurement / insurance / compliance requirements confirmed.
- [ ] Confidentiality and data-transfer/storage terms agreed before real lease/maintenance evidence is received.
- [ ] Customer and AERVIND accountable reviewers identified.

## Default first commercial package

**Recovery Scan — EUR 9,500**

- up to **5 aircraft and/or engines**;
- **1 primary entitlement family**;
- up to **12 months** of selected events;
- **50% on engagement / scope confirmation**;
- **50% on delivery**;
- target **10 business days** after the complete agreed minimum dataset is received;
- no guarantee of recoverable value;
- no live customer-system access required.

Use `docs/FIRST_PAID_RECOVERY_SCAN_PROPOSAL.md` as the proposal baseline.

## Commercial launch sequence

1. Keep product, proof and buyer material complete under the no-send hold.
2. Keep the temporary Vercel host technically valid but non-canonical.
3. Attach and verify `aervind.com` when the registrar/project action is available.
4. Complete branded-mail DNS verification without messaging a real person.
5. Verify Portuguese activity/tax facts before rendering the first paid service.
6. Maintain account-specific research, private briefs and unsent drafts.
7. Begin real account-based outreach only after the founder explicitly lifts the hold.
8. Prioritize a bounded Recovery Scan over software/SaaS selling.
9. Receive customer evidence only under agreed confidentiality/handling controls.
10. Execute the deterministic recovery workflow and report economic/workflow states separately.
11. Reassess incorporation only when a real buyer or actual economics justify it.

## No-spend rule before proof

Do not add paid ads, paid SaaS infrastructure, secondary domains, self-service billing, SSO, deep integrations or a Portuguese company merely for appearance before real commercial evidence requires them.
