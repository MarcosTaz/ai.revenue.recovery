'use strict';

const STAGE = Object.freeze({
  CANDIDATE: 'CANDIDATE',
  ACTION_READY: 'ACTION_READY',
  CLAIM_OR_REQUEST_SUBMITTED: 'CLAIM_OR_REQUEST_SUBMITTED',
  COUNTERPARTY_ACKNOWLEDGED: 'COUNTERPARTY_ACKNOWLEDGED',
  COUNTERPARTY_APPROVED: 'COUNTERPARTY_APPROVED',
  PAYMENT_REPORTED: 'PAYMENT_REPORTED',
  PAYMENT_VERIFIED: 'PAYMENT_VERIFIED'
});

function nonEmpty(v) { return typeof v === 'string' && v.trim().length > 0; }
function money(v) { return Number.isFinite(v) && v >= 0; }
function validDate(v) { return nonEmpty(v) && !Number.isNaN(Date.parse(v)); }

function evaluateRecoveryLifecycle(input) {
  const reasons = [];
  if (!input || typeof input !== 'object') return { stage: STAGE.CANDIDATE, verified_recovery_amount: null, reasons: ['INPUT_MISSING'] };
  const candidate = input.candidate || {};
  if (candidate.status !== 'SUPPORTED_CANDIDATE') reasons.push('SUPPORTED_CANDIDATE_REQUIRED');
  if (!money(candidate.amount) || !nonEmpty(candidate.currency)) reasons.push('CANDIDATE_AMOUNT_INVALID');
  if (!nonEmpty(candidate.artifact_sha256)) reasons.push('CANDIDATE_ARTIFACT_HASH_MISSING');

  const baseline = input.baseline || {};
  if (!money(baseline.expected_recovery_amount) || baseline.currency !== candidate.currency) reasons.push('BASELINE_INVALID');
  if (!validDate(baseline.frozen_at) || !nonEmpty(baseline.source_sha256)) reasons.push('BASELINE_PROVENANCE_MISSING');
  if (baseline.frozen_before_analysis !== true) reasons.push('BASELINE_NOT_FROZEN_BEFORE_ANALYSIS');

  if (reasons.length) return { stage: STAGE.CANDIDATE, verified_recovery_amount: null, incremental_verified_amount: null, reasons };

  let stage = STAGE.CANDIDATE;
  const review = input.review || {};
  if (review.state === 'APPROVED_FOR_CUSTOMER_ACTION' && nonEmpty(review.approval_sha256) && review.artifact_sha256 === candidate.artifact_sha256) {
    stage = STAGE.ACTION_READY;
  } else {
    return {
      stage,
      verified_recovery_amount: null,
      incremental_verified_amount: null,
      reasons: ['INDEPENDENT_ACTION_APPROVAL_REQUIRED']
    };
  }

  const submission = input.submission || null;
  if (!submission) return summary(stage, candidate, baseline);
  if (!validDate(submission.submitted_at) || !nonEmpty(submission.evidence_sha256) || !nonEmpty(submission.route) || submission.customer_authorized !== true) {
    return summary(stage, candidate, baseline, ['SUBMISSION_EVIDENCE_INCOMPLETE']);
  }
  stage = STAGE.CLAIM_OR_REQUEST_SUBMITTED;

  const counterparty = input.counterparty || null;
  if (!counterparty) return summary(stage, candidate, baseline);
  if (!validDate(counterparty.at) || !nonEmpty(counterparty.evidence_sha256) || !nonEmpty(counterparty.outcome)) {
    return summary(stage, candidate, baseline, ['COUNTERPARTY_EVIDENCE_INCOMPLETE']);
  }
  stage = STAGE.COUNTERPARTY_ACKNOWLEDGED;
  if (counterparty.outcome === 'APPROVED') {
    if (!money(counterparty.approved_amount) || counterparty.currency !== candidate.currency) {
      return summary(stage, candidate, baseline, ['COUNTERPARTY_APPROVAL_AMOUNT_INVALID']);
    }
    stage = STAGE.COUNTERPARTY_APPROVED;
  }

  const payment = input.payment || null;
  if (!payment) return summary(stage, candidate, baseline);
  if (!money(payment.reported_amount) || payment.currency !== candidate.currency || !validDate(payment.reported_at)) {
    return summary(stage, candidate, baseline, ['PAYMENT_REPORT_INVALID']);
  }
  stage = STAGE.PAYMENT_REPORTED;

  if (payment.verified !== true) return summary(stage, candidate, baseline);
  if (!money(payment.verified_amount) || payment.verified_amount !== payment.reported_amount) {
    return summary(stage, candidate, baseline, ['PAYMENT_VERIFIED_AMOUNT_MISMATCH']);
  }
  if (!nonEmpty(payment.payment_evidence_sha256) || !nonEmpty(payment.payment_reference) || !validDate(payment.value_date)) {
    return summary(stage, candidate, baseline, ['PAYMENT_VERIFICATION_EVIDENCE_INCOMPLETE']);
  }
  if (payment.matches_case !== true || payment.matches_counterparty !== true) {
    return summary(stage, candidate, baseline, ['PAYMENT_MATCH_NOT_VERIFIED']);
  }
  if (stage === STAGE.PAYMENT_REPORTED && counterparty.outcome === 'APPROVED' && money(counterparty.approved_amount) && payment.verified_amount > counterparty.approved_amount) {
    return summary(stage, candidate, baseline, ['PAYMENT_EXCEEDS_APPROVED_AMOUNT_REVIEW_REQUIRED']);
  }

  stage = STAGE.PAYMENT_VERIFIED;
  let incremental = null;
  const incrementality = input.incrementality || {};
  if (
    incrementality.verified === true &&
    nonEmpty(incrementality.evidence_sha256) &&
    nonEmpty(incrementality.reviewer_id) &&
    incrementality.reviewer_id !== incrementality.preparer_id &&
    money(incrementality.verified_incremental_amount) &&
    incrementality.currency === candidate.currency &&
    incrementality.verified_incremental_amount <= payment.verified_amount
  ) {
    incremental = incrementality.verified_incremental_amount;
  }

  return {
    stage,
    currency: candidate.currency,
    candidate_amount: candidate.amount,
    baseline_expected_recovery_amount: baseline.expected_recovery_amount,
    verified_recovery_amount: payment.verified_amount,
    incremental_verified_amount: incremental,
    recovered_cash_verified: true,
    incrementality_verified: incremental !== null,
    truth_boundary: {
      counterparty_approval_is_not_payment: true,
      reported_payment_is_not_verified_payment: true,
      verified_recovery_is_not_automatically_incremental: true,
      company_revenue_is_separate: true
    },
    reasons: incremental === null ? ['PAYMENT_VERIFIED_INCREMENTALITY_NOT_YET_VERIFIED'] : ['PAYMENT_AND_INCREMENTALITY_VERIFIED']
  };
}

function summary(stage, candidate, baseline, reasons = []) {
  return {
    stage,
    currency: candidate.currency,
    candidate_amount: candidate.amount,
    baseline_expected_recovery_amount: baseline.expected_recovery_amount,
    verified_recovery_amount: null,
    incremental_verified_amount: null,
    recovered_cash_verified: false,
    incrementality_verified: false,
    reasons
  };
}

module.exports = { STAGE, evaluateRecoveryLifecycle };
