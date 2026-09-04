# Aviation Recovery — Compliant Channel Strategy

_Last reviewed: 2026-09-04_

## Objective

Move from a verified buyer map to channels that can legitimately start a first paid Recovery Scan conversation without guessed emails, misuse of customer/IR channels, or an outbound provider whose terms prohibit unsolicited commercial email.

The commercial motion is dual-threaded:

**strategic sponsor** (CFO / finance-fleet owner) + **institutional intake** (procurement / supplier / non-customer business route).

## Channel classes

- `DIRECT_PROFESSIONAL` — verified professional profile or other direct business route to a named buyer.
- `BUSINESS_INTAKE` — official supplier onboarding, procurement portal, sourcing channel or non-customer corporate routing path.
- `IR_ROUTING_ONLY` — investor relations may be used solely to ask for internal routing where no better route exists and the company does not prohibit the use.
- `CUSTOMER_SERVICE_NOT_FOR_B2B` — passenger/customer-service channels are not a prospecting route.
- `PROHIBITED_FOR_COLD` — channel/provider rules make unsolicited commercial use inappropriate.

## 1. TAP Air Portugal — strongest institutional entry

### Strategic sponsor

Renato Inácio — CFO.

A direct buyer email has not been publicly verified, so do not infer one.

### Institutional intake

TAP publishes a dedicated supplier program and centralized Procurement Area. Its supplier information states that procurement covers roughly EUR 2 billion in annual spend. The categories most relevant to Aviation Recovery are:

- **Professional and Financial Services** under Corporate Services;
- **Engines** and **Tools and Services** under M&E Procurement.

TAP's supplier onboarding page states that companies wishing to collaborate should register through the supplier onboarding process. TAP uses SAP Ariba for supplier onboarding and procure-to-order workflows, and registration is described as important for being considered for future opportunities.

Official sources:

- https://www.tapairportugal.com/en/about-us/suppliers/about-tap-for-suppliers
- https://www.tapairportugal.com/en/about-us/suppliers/how-we-do-business/working-together

### Recommended motion

1. Strategic sponsor: Renato Inácio via a verified direct professional route if found.
2. Institutional: register / prepare for TAP supplier onboarding under Professional and Financial Services, with M&E relevance explicitly described.
3. Proposal: bounded Recovery Scan, not a software subscription.
4. Procurement artifact: capability statement + data/security summary + SOW + price band.

**Status:** `DIRECT_ROUTE_PENDING + BUSINESS_INTAKE_VERIFIED`.

---

## 2. Norwegian — direct sponsor + corporate routing + Ariba

### Strategic sponsor

Hans-Jørgen Wibstad — CFO.

Verified professional route:

- https://no.linkedin.com/in/hans-j%C3%B8rgen-wibstad-2482276b

### Institutional intake

Norwegian's official contact page says non-customer enquiries should use:

- `post.reception@norwegian.com`

This is a better internal-routing channel for a B2B request than passenger support or IR.

Norwegian also publishes vendor guidelines stating that vendors must be registered in the vendor portal Ariba before invoicing.

Official sources:

- https://www.norwegian.com/no/infourl/infoidhelpandcontact/
- https://www.norwegian.com/en/about/vendor-guidelines-invoicing/

### Recommended motion

1. Strategic sponsor: Hans-Jørgen Wibstad direct professional route.
2. Parallel internal-routing request: ask `post.reception@norwegian.com` to route the proposal to Finance, Control & Fleet / relevant sourcing owner.
3. If qualified, move through Ariba/vendor registration before contracting/invoicing.
4. Do not send a sales pitch to Accounts Payable; `accountspayable@norwegian.com` is for AP-process questions.

**Status:** `DIRECT_PROFESSIONAL_VERIFIED + BUSINESS_ROUTING_VERIFIED + VENDOR_PORTAL_VERIFIED`.

---

## 3. Icelandair Group — direct sponsor first; procurement exists but no public intake found

### Strategic sponsor

Ívar S. Kristinsson — CFO, previously Managing Director of Icelandair Fleet.

Verified professional route:

- https://is.linkedin.com/in/ivarkr

Technical / lease co-owners already mapped:

- Leifur Magnússon — VP Technical and Maintenance;
- Árni Hermannsson — Managing Director, Aircraft Leasing and Consulting.

### Institutional evidence

Icelandair Group publicly maintains a Supplier Code of Conduct and procurement policy/governance framework. Current public reporting states the company is centralizing and improving procurement functions. However, no current public supplier-registration or procurement-intake page was found in the reviewed official web pages.

Official governance source:

- https://www.icelandairgroup.com/governance

### Recommended motion

1. Lead through Ívar's verified professional route.
2. Ask for the correct Procurement / Technical & Maintenance internal owner during qualification.
3. Do not use customer-service or corporate-travel channels as a substitute for supplier intake.
4. Use IR only as a last-resort routing request, not as the primary commercial pitch.

**Status:** `DIRECT_PROFESSIONAL_VERIFIED + PROCUREMENT_EXISTS + PUBLIC_INTAKE_UNRESOLVED`.

---

## 4. Wizz Air — direct sponsor / procurement-owner route; do not use IR

### Strategic sponsor

Veronika Špaňárová — CFO.

Verified professional route:

- https://hu.linkedin.com/in/veronika-%C5%A1pa%C5%88%C3%A1rov%C3%A1-396786181

### Institutional / functional route

Wizz publicly identifies Julia Brix as Supply Chain Officer. Its current supply-chain materials state that the function includes acquisition and purchasing. A July 2026 Fleet Procurement Manager posting is especially relevant: it describes responsibility for purchasing, financing and managing the fleet; aircraft and engine tenders; lessor and bank relationships; lease-expiry redeliveries; financial analysis; and cooperation with Corporate Finance.

Official sources:

- https://corporate.wizzair.com/corporate-governance/leadership-team/
- https://careers.wizzair.com/content/office_supplyChain/?locale=en_US
- https://careers.wizzair.com/job/Budapest-Fleet-Acquisition-Manager-H-1095/1395367933/

No public general supplier-onboarding intake was found in the reviewed official pages.

Wizz explicitly states that its published Investor Relations contacts are for investment-related inquiries only. Do not use IR for cold commercial outreach.

### Recommended motion

1. Strategic sponsor: Veronika via verified professional route.
2. Functional sponsor: target Fleet Procurement / Supply Chain through a verified professional route when identified.
3. Position the service as an independent evidence/recovery control on one engine or lease-event cohort.
4. Do not use Wizz IR or passenger call-center channels.

**Status:** `DIRECT_PROFESSIONAL_VERIFIED + PROCUREMENT_FUNCTION_VERIFIED + PUBLIC_INTAKE_UNRESOLVED + IR_PROHIBITED_FOR_COLD`.

---

## Primitive Email decision

Primitive is **not** the cold-prospecting channel for Aviation Recovery under the current setup.

Two separate constraints apply:

1. the current account does not have unrestricted `send_to_any_domain` recipient access; and
2. Primitive's published Terms of Service prohibit unsolicited bulk **or commercial** email.

Official sources:

- https://www.primitive.dev/terms
- https://docs.primitive.dev/docs/sending

Primitive remains suitable for operational mail and reply-based workflows that comply with its terms and recipient gates. It must not be used to bypass the commercial-outreach restriction.

**Status:** `PROHIBITED_FOR_COLD`.

---

## Canonical first-wave execution order

### TAP

**Sponsor:** Renato Inácio

**Institutional path:** TAP supplier onboarding / SAP Ariba / Professional and Financial Services, with M&E recovery-control relevance.

### Norwegian

**Sponsor:** Hans-Jørgen Wibstad

**Institutional path:** `post.reception@norwegian.com` for internal B2B routing -> Finance, Control & Fleet / sourcing -> Ariba vendor registration if qualified.

### Icelandair

**Sponsor:** Ívar S. Kristinsson

**Institutional path:** obtain internal Procurement / Technical owner through sponsor; no public supplier intake currently verified.

### Wizz

**Sponsor:** Veronika Špaňárová

**Functional path:** Fleet Procurement / Supply Chain; no public supplier intake currently verified; IR is excluded.

## Send / submission gate

No external commercial message or supplier registration is executed until the exact channel and sender identity are known and the side effect is explicitly approved when required by the tool or platform.

Until then, the product can safely prepare every commercial artifact, qualification package and routing instruction needed for the first paid pilot.