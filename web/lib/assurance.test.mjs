import assert from 'node:assert/strict';
import test from 'node:test';

import { computeAssuranceSnapshot } from './assurance.mjs';

const base = {
  supportedExpectedBilling: 1000,
  cumulativeBilled: 1000,
  cumulativePaid: 1000,
  evidenceComplete: true,
  contractTermsSupported: true,
  allowabilitySupported: true,
  allocabilitySupported: true,
  fundingSupported: true,
  ceilingSupported: true,
  finalRateSettledWhenRequired: true,
  proceduralRisk: false,
  expresslyUnallowable: false,
};

test('current supported economics stay current', () => {
  assert.equal(computeAssuranceSnapshot(base).state, 'CURRENT');
});

test('supported unbilled is emitted only after all gates', () => {
  const supported = computeAssuranceSnapshot({ ...base, cumulativeBilled: 800, cumulativePaid: 800 });
  assert.equal(supported.state, 'SUPPORTED_UNBILLED');
  assert.equal(supported.supportedUnbilled, 200);

  const atRisk = computeAssuranceSnapshot({ ...base, cumulativeBilled: 800, cumulativePaid: 800, fundingSupported: false });
  assert.equal(atRisk.state, 'AT_RISK');
  assert.equal(atRisk.supportedUnbilled, null);
});

test('payable and payment shortfall remain separate', () => {
  const payable = computeAssuranceSnapshot({ ...base, cumulativeBilled: 1100, cumulativePaid: 1100 });
  assert.equal(payable.state, 'PAYABLE_EXPOSURE');
  assert.equal(payable.payableExposure, 100);

  const shortfall = computeAssuranceSnapshot({ ...base, cumulativePaid: 900 });
  assert.equal(shortfall.state, 'PAYMENT_SHORTFALL');
  assert.equal(shortfall.paymentShortfall, 100);
});

test('unknown or unallowable truth cannot become supported revenue', () => {
  assert.equal(computeAssuranceSnapshot({ ...base, evidenceComplete: false }).state, 'UNKNOWN');
  const unallowable = computeAssuranceSnapshot({ ...base, expresslyUnallowable: true, cumulativeBilled: 500 });
  assert.equal(unallowable.state, 'NOT_ALLOWABLE');
  assert.equal(unallowable.earnedSupported, null);
});
