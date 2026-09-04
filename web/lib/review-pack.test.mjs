import assert from 'node:assert/strict';
import test from 'node:test';

import { buildSyntheticReviewPack } from './review-pack.mjs';

const recoveryFinding = {
  findingId: 'f-1',
  state: 'RECOVERY_CANDIDATE',
  variance: 50000,
};

test('unreviewed recovery stays draft and unresolved', () => {
  const pack = buildSyntheticReviewPack({
    organizationId: 'synthetic-org',
    finding: recoveryFinding,
  });
  assert.equal(pack.status, 'DRAFT');
  assert.equal(pack.approvedRecoveryCandidates.length, 0);
  assert.equal(pack.unresolved.length, 1);
});

test('approved recovery requires reviewer identity and rationale', () => {
  const incomplete = buildSyntheticReviewPack({
    organizationId: 'synthetic-org',
    finding: recoveryFinding,
    review: { decision: 'APPROVED', reviewerId: '', rationale: '' },
  });
  assert.equal(incomplete.status, 'DRAFT');

  const approved = buildSyntheticReviewPack({
    organizationId: 'synthetic-org',
    finding: recoveryFinding,
    review: { decision: 'APPROVED', reviewerId: 'reviewer-1', rationale: 'Synthetic evidence reviewed.' },
  });
  assert.equal(approved.status, 'READY_FOR_CLIENT_FINANCE_REVIEW');
  assert.equal(approved.approvedRecoveryCandidates.length, 1);
});

test('payable exposure is visible without being netted into recovery', () => {
  const pack = buildSyntheticReviewPack({
    organizationId: 'synthetic-org',
    finding: { findingId: 'f-2', state: 'PAYABLE_CANDIDATE', variance: -25000 },
  });
  assert.equal(pack.status, 'NO_RECOVERY_PACK');
  assert.equal(pack.payableExposures.length, 1);
  assert.equal(pack.approvedRecoveryCandidates.length, 0);
});
