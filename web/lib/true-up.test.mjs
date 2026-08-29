import test from 'node:test';
import assert from 'node:assert/strict';
import { computeIndirectTrueUp } from './true-up.mjs';

const base = {
  allocationBase: 1_000_000,
  finalRate: 0.25,
  billedIndirect: 200_000,
  contractTermsVerified: true,
  finalRateSettled: true,
  allowabilitySupported: true,
  allocabilitySupported: true,
  indirectCeilingAmount: null,
  remainingFunding: 100_000,
};

test('creates recovery candidate only after gates pass', () => {
  const result = computeIndirectTrueUp(base);
  assert.equal(result.state, 'RECOVERY_CANDIDATE');
  assert.equal(result.variance, 50_000);
});

test('flags payable symmetrically', () => {
  const result = computeIndirectTrueUp({ ...base, billedIndirect: 300_000 });
  assert.equal(result.state, 'PAYABLE_CANDIDATE');
  assert.equal(result.variance, -50_000);
});

test('unsettled rate fails closed', () => {
  const result = computeIndirectTrueUp({ ...base, finalRateSettled: false });
  assert.equal(result.state, 'REQUIRES_REVIEW');
  assert.equal(result.variance, null);
});

test('missing contract applicability is unknown', () => {
  const result = computeIndirectTrueUp({ ...base, contractTermsVerified: false });
  assert.equal(result.state, 'UNKNOWN');
});

test('ceiling prevents false recovery', () => {
  const result = computeIndirectTrueUp({ ...base, indirectCeilingAmount: 200_000 });
  assert.equal(result.state, 'NO_VARIANCE');
  assert.equal(result.variance, 0);
});

test('funding shortfall requires review', () => {
  const result = computeIndirectTrueUp({ ...base, remainingFunding: 10_000 });
  assert.equal(result.state, 'REQUIRES_REVIEW');
  assert.equal(result.variance, 50_000);
});

test('negative inputs fail closed', () => {
  const result = computeIndirectTrueUp({ ...base, allocationBase: -1 });
  assert.equal(result.state, 'REQUIRES_REVIEW');
  assert.equal(result.variance, null);
});

test('non-finite inputs fail closed', () => {
  const result = computeIndirectTrueUp({ ...base, finalRate: Number.NaN });
  assert.equal(result.state, 'REQUIRES_REVIEW');
  assert.equal(result.variance, null);
});
