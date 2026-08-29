'use strict';

const FINDING = Object.freeze({
  SUPPORTED_CANDIDATE: 'SUPPORTED_CANDIDATE',
  NO_RECOVERY: 'NO_RECOVERY',
  UNKNOWN: 'UNKNOWN',
  NEEDS_REVIEW: 'NEEDS_REVIEW'
});

function finiteNonNegative(value) {
  return Number.isFinite(value) && value >= 0;
}

function nonEmpty(value) {
  return typeof value === 'string' && value.trim().length > 0;
}

function evaluateNetworkUpgradeRepayment(input) {
  const reasons = [];
  if (!input || typeof input !== 'object') {
    return { status: FINDING.UNKNOWN, candidate_amount: null, reasons: ['INPUT_MISSING'] };
  }

  const agreement = input.agreement || {};
  const evidence = input.evidence || {};
  const economics = input.economics || {};

  if (input.jurisdiction !== 'US_FEDERAL_FERC') reasons.push('JURISDICTION_NOT_SUPPORTED');
  if (input.project_scope !== 'LARGE_GENERATOR_GT_20MW') reasons.push('PROJECT_SCOPE_NOT_SUPPORTED');
  if (!nonEmpty(agreement.executed_lgia_id)) reasons.push('EXECUTED_LGIA_NOT_IDENTIFIED');
  if (agreement.article_11_4_1_match !== true) reasons.push('CREDITING_LANGUAGE_NOT_VERIFIED');
  if (!nonEmpty(agreement.source_document_hash)) reasons.push('AGREEMENT_SOURCE_HASH_MISSING');
  if (!nonEmpty(agreement.source_locator)) reasons.push('AGREEMENT_SOURCE_LOCATOR_MISSING');
  if (agreement.superseded === true) reasons.push('AGREEMENT_SUPERSEDED');

  if (!finiteNonNegative(economics.network_upgrade_amount_paid)) reasons.push('NETWORK_UPGRADE_PAYMENT_INVALID');
  if (!finiteNonNegative(economics.amounts_already_refunded)) reasons.push('REFUNDS_INVALID');
  if (!finiteNonNegative(economics.repayments_received)) reasons.push('REPAYMENTS_INVALID');
  if (!nonEmpty(evidence.payment_source_hash)) reasons.push('PAYMENT_EVIDENCE_MISSING');
  if (evidence.payment_matches_project !== true) reasons.push('PAYMENT_PROJECT_MATCH_NOT_VERIFIED');
  if (evidence.payment_is_network_upgrade !== true) reasons.push('PAYMENT_PURPOSE_NOT_VERIFIED');

  if (agreement.trigger_satisfied !== true) reasons.push('REPAYMENT_TRIGGER_NOT_VERIFIED');
  if (agreement.repayment_schedule_supported !== true) reasons.push('REPAYMENT_SCHEDULE_NOT_VERIFIED');

  if (reasons.length) {
    return { status: FINDING.UNKNOWN, candidate_amount: null, reasons: [...new Set(reasons)] };
  }

  const gross = economics.network_upgrade_amount_paid;
  const credited = economics.amounts_already_refunded + economics.repayments_received;
  const candidate = gross - credited;

  if (candidate < 0) {
    return { status: FINDING.NEEDS_REVIEW, candidate_amount: null, reasons: ['RECEIPTS_EXCEED_VERIFIED_ADVANCE'] };
  }
  if (candidate === 0) {
    return { status: FINDING.NO_RECOVERY, candidate_amount: 0, reasons: ['VERIFIED_ADVANCE_FULLY_REPAID_OR_REFUNDED'] };
  }

  return {
    status: FINDING.SUPPORTED_CANDIDATE,
    candidate_amount: candidate,
    currency: economics.currency || null,
    reasons: ['VERIFIED_UNREPAID_NETWORK_UPGRADE_ADVANCE'],
    limitations: [
      'candidate amount is not proof that payment is currently overdue',
      'interest is excluded unless separately source-supported',
      'customer/qualified reviewer must confirm current contractual timing and offsets'
    ]
  };
}

module.exports = { FINDING, evaluateNetworkUpgradeRepayment };
