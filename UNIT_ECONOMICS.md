# GovMargin pilot unit economics — operating hypothesis

## Status

**MODELLED, NOT MARKET-VALIDATED.**

The purpose of this model is to prevent GovMargin from accepting a first pilot whose delivery burden destroys gross margin. It does not prove willingness to pay, CAC, sales cycle or recovery frequency.

Executable model: `govmargin/economics.py`.

## Design-partner baseline

Commercial hypothesis from `PILOT_OFFER.md`:

- fixed fee: **$7,500**;
- one contractor entity;
- up to five contracts / task orders;
- up to two completed fiscal years;
- assisted evidence/rate/billing/payment reconciliation.

### Internal planning case

Assumptions only:

- delivery hours: 40;
- loaded delivery cost: $75/hour;
- software/data variable cost: $250;
- other direct delivery cost: $250;
- no partner share in the first direct pilot.

Deterministic result:

- revenue: $7,500;
- labor cost: $3,000;
- total direct cost: $3,500;
- gross profit: $4,000;
- gross margin: **53.33%**;
- effective revenue per delivery hour: $187.50.

This is a planning scenario, not an actual customer result.

## Delivery-hour guardrail

At:

- $7,500 fixed fee;
- $75 loaded hourly cost;
- $500 non-labor direct cost;
- 50% target gross margin;

maximum modeled delivery time is **43.33 hours**.

If the scoped pilot appears likely to exceed that limit, GovMargin should do one of:

1. reduce contract/year scope;
2. require cleaner normalized data;
3. increase fixed price;
4. explicitly treat the engagement as a subsidized research/design-partner pilot and record the subsidy;
5. reject the engagement if it cannot generate enough learning or commercial value.

Never hide excess delivery labor to manufacture margin.

## Partner-channel guardrail

Partner revenue share is modeled as a direct cost. Example only:

- $10,000 fixed audit;
- 20 delivery hours × $100 loaded cost = $2,000 labor;
- 20% partner share = $2,000;
- total direct cost = $4,000 before other variable cost;
- modeled gross margin = 60%.

A partner share must be evaluated against actual CAC reduction and review-time savings. Referral economics are not valid merely because the percentage fits the spreadsheet.

## Metrics required from every real pilot

Capture:

- quoted fixed fee;
- actual collected audit revenue;
- contractor revenue/cost base reviewed;
- contracts and fiscal years reviewed;
- data-preparation hours;
- GovMargin delivery hours by activity;
- qualified accounting/legal review hours and cost;
- software/storage/processing variable cost;
- partner/referral cost;
- direct delivery cost;
- gross profit and gross margin;
- days from signed engagement to usable dataset;
- days to first defensible finding;
- days to final finance-review pack;
- finding count by recovery/payable/no-variance/review/unknown;
- verified incremental recovery or avoided overpayment, if any;
- time to billing/collection where customer action follows;
- customer renewal/monitoring interest.

## Commercial gate

Do not call the pricing model validated until real pilots demonstrate both:

1. customer willingness to pay the fixed audit fee; and
2. repeatable delivery economics at an acceptable gross margin.

A large theoretical recovery does not compensate for an unscalable audit process.
