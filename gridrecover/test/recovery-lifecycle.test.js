'use strict';

const assert = require('assert');
const { STAGE, evaluateRecoveryLifecycle } = require('../src/recovery-lifecycle');

function base() {
  return {
    candidate: { status: 'SUPPORTED_CANDIDATE', amount: 2000000, currency: 'USD', artifact_sha256: 'a'.repeat(64) },
    baseline: { expected_recovery_amount: 500000, currency: 'USD', frozen_at: '2026-09-01T09:00:00Z', source_sha256: 'b'.repeat(64), frozen_before_analysis: true },
    review: { state: 'APPROVED_FOR_CUSTOMER_ACTION', approval_sha256: 'c'.repeat(64), artifact_sha256: 'a'.repeat(64) },
    submission: { submitted_at: '2026-09-02T10:00:00Z', evidence_sha256: 'd'.repeat(64), route: 'customer-authorized counterparty portal', customer_authorized: true },
    counterparty: { at: '2026-09-03T10:00:00Z', evidence_sha256: 'e'.repeat(64), outcome: 'APPROVED', approved_amount: 1500000, currency: 'USD' },
    payment: { reported_amount: 1500000, currency: 'USD', reported_at: '2026-09-04T10:00:00Z', verified: true, verified_amount: 1500000, payment_evidence_sha256: 'f'.repeat(64), payment_reference: 'WIRE-001', value_date: '2026-09-04', matches_case: true, matches_counterparty: true },
    incrementality: { verified: true, evidence_sha256: '1'.repeat(64), reviewer_id: 'reviewer-2', preparer_id: 'analyst-1', verified_incremental_amount: 1000000, currency: 'USD' }
  };
}

{
  const r = evaluateRecoveryLifecycle(base());
  assert.equal(r.stage, STAGE.PAYMENT_VERIFIED);
  assert.equal(r.verified_recovery_amount, 1500000);
  assert.equal(r.incremental_verified_amount, 1000000);
  assert.equal(r.recovered_cash_verified, true);
  assert.equal(r.incrementality_verified, true);
  assert.equal(r.truth_boundary.company_revenue_is_separate, true);
}
{
  const i = base(); delete i.payment.payment_evidence_sha256;
  const r = evaluateRecoveryLifecycle(i);
  assert.equal(r.stage, STAGE.PAYMENT_REPORTED);
  assert.equal(r.verified_recovery_amount, null);
}
{
  const i = base(); i.payment.verified = false;
  const r = evaluateRecoveryLifecycle(i);
  assert.equal(r.stage, STAGE.PAYMENT_REPORTED);
  assert.equal(r.recovered_cash_verified, false);
}
{
  const i = base(); delete i.payment;
  const r = evaluateRecoveryLifecycle(i);
  assert.equal(r.stage, STAGE.COUNTERPARTY_APPROVED);
  assert.equal(r.verified_recovery_amount, null);
}
{
  const i = base(); i.counterparty.outcome = 'ACKNOWLEDGED'; delete i.counterparty.approved_amount; delete i.payment;
  const r = evaluateRecoveryLifecycle(i);
  assert.equal(r.stage, STAGE.COUNTERPARTY_ACKNOWLEDGED);
}
{
  const i = base(); i.review.state = 'READY_FOR_REVIEW';
  const r = evaluateRecoveryLifecycle(i);
  assert.equal(r.stage, STAGE.CANDIDATE);
  assert(r.reasons.includes('INDEPENDENT_ACTION_APPROVAL_REQUIRED'));
}
{
  const i = base(); i.payment.verified_amount = 1600000;
  const r = evaluateRecoveryLifecycle(i);
  assert.equal(r.stage, STAGE.PAYMENT_REPORTED);
  assert(r.reasons.includes('PAYMENT_VERIFIED_AMOUNT_MISMATCH'));
}
{
  const i = base(); i.payment.reported_amount = 1600000; i.payment.verified_amount = 1600000;
  const r = evaluateRecoveryLifecycle(i);
  assert.equal(r.stage, STAGE.PAYMENT_REPORTED);
  assert(r.reasons.includes('PAYMENT_EXCEEDS_APPROVED_AMOUNT_REVIEW_REQUIRED'));
}
{
  const i = base(); i.incrementality.reviewer_id = i.incrementality.preparer_id;
  const r = evaluateRecoveryLifecycle(i);
  assert.equal(r.stage, STAGE.PAYMENT_VERIFIED);
  assert.equal(r.incremental_verified_amount, null);
  assert.equal(r.incrementality_verified, false);
}
{
  const i = base(); i.baseline.frozen_before_analysis = false;
  const r = evaluateRecoveryLifecycle(i);
  assert.equal(r.stage, STAGE.CANDIDATE);
  assert(r.reasons.includes('BASELINE_NOT_FROZEN_BEFORE_ANALYSIS'));
}
{
  const i = base(); i.payment.matches_case = false;
  const r = evaluateRecoveryLifecycle(i);
  assert.equal(r.stage, STAGE.PAYMENT_REPORTED);
  assert(r.reasons.includes('PAYMENT_MATCH_NOT_VERIFIED'));
}

console.log('GRIDRECOVER recovery lifecycle: 11/11 PASS');
