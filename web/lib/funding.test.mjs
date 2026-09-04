import assert from 'node:assert/strict';
import test from 'node:test';

import { evaluateFundingSafeguard } from './funding.mjs';

test('52.232-20 uses estimated cost and never creates automatic recovery', () => {
  const result = evaluateFundingSafeguard({
    clause: '52.232-20',
    costsIncurred: 700,
    expectedNextNoticeWindowCosts: 60,
    estimatedCost: 1000,
    allottedFunds: 100,
  });
  assert.equal(result.verifiedLimit, 1000);
  assert.equal(result.state, 'NOTICE_THRESHOLD_REACHED');
  assert.equal(result.automaticRecoveryAllowed, false);
});

test('52.232-22 uses actual allotment and flags exhaustion', () => {
  const result = evaluateFundingSafeguard({
    clause: '52.232-22',
    costsIncurred: 805,
    expectedNextNoticeWindowCosts: 10,
    estimatedCost: 2000,
    allottedFunds: 800,
  });
  assert.equal(result.verifiedLimit, 800);
  assert.equal(result.state, 'FUNDING_EXHAUSTED_REVIEW_REQUIRED');
  assert.equal(result.automaticRecoveryAllowed, false);
});

test('unsupported clause and missing limit fail closed', () => {
  const unsupported = evaluateFundingSafeguard({
    clause: '52.232-99',
    costsIncurred: 100,
    expectedNextNoticeWindowCosts: 100,
  });
  assert.equal(unsupported.state, 'UNKNOWN');

  const missing = evaluateFundingSafeguard({
    clause: '52.232-22',
    costsIncurred: 100,
    expectedNextNoticeWindowCosts: 100,
  });
  assert.equal(missing.state, 'UNKNOWN');
  assert.equal(missing.automaticRecoveryAllowed, false);
});

test('notice terms outside FAR-supported configurable ranges require review', () => {
  const badThreshold = evaluateFundingSafeguard({
    clause: '52.232-20',
    costsIncurred: 1,
    expectedNextNoticeWindowCosts: 1,
    estimatedCost: 100,
    noticeThresholdPercent: 0.9,
  });
  assert.equal(badThreshold.state, 'REQUIRES_REVIEW');

  const badWindow = evaluateFundingSafeguard({
    clause: '52.232-20',
    costsIncurred: 1,
    expectedNextNoticeWindowCosts: 1,
    estimatedCost: 100,
    noticeWindowDays: 10,
  });
  assert.equal(badWindow.state, 'REQUIRES_REVIEW');
});
