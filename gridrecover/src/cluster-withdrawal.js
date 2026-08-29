'use strict';

const RESULT = Object.freeze({
  SUPPORTED_CANDIDATE: 'SUPPORTED_CANDIDATE',
  NO_RECOVERY: 'NO_RECOVERY',
  UNKNOWN: 'UNKNOWN',
  NEEDS_REVIEW: 'NEEDS_REVIEW'
});

function nonEmpty(v) { return typeof v === 'string' && v.trim().length > 0; }
function nn(v) { return Number.isFinite(v) && v >= 0; }

function commonChecks(input) {
  const reasons = [];
  if (!input || typeof input !== 'object') return ['INPUT_MISSING'];
  if (input.jurisdiction !== 'US_FEDERAL_FERC') reasons.push('JURISDICTION_NOT_SUPPORTED');
  if (input.project_scope !== 'LARGE_GENERATOR_GT_20MW_CLUSTER_PROCESS') reasons.push('PROJECT_SCOPE_NOT_SUPPORTED');
  if (!nonEmpty(input.transmission_provider)) reasons.push('TRANSMISSION_PROVIDER_MISSING');
  if (!nonEmpty(input.provider_tariff_document_hash)) reasons.push('PROVIDER_TARIFF_SOURCE_MISSING');
  if (!nonEmpty(input.provider_tariff_locator)) reasons.push('PROVIDER_TARIFF_LOCATOR_MISSING');
  if (input.provider_rule_match_verified !== true) reasons.push('PROVIDER_RULE_MATCH_NOT_VERIFIED');
  if (!nonEmpty(input.cluster_id)) reasons.push('CLUSTER_ID_MISSING');
  if (!nonEmpty(input.withdrawal_event_source_hash)) reasons.push('WITHDRAWAL_EVENT_SOURCE_MISSING');
  if (input.withdrawal_event_verified !== true) reasons.push('WITHDRAWAL_EVENT_NOT_VERIFIED');
  return reasons;
}

function evaluateClusterWithdrawalCapital(input) {
  const reasons = commonChecks(input);
  if (reasons.length) return { status: RESULT.UNKNOWN, reasons: [...new Set(reasons)] };

  if (input.role === 'REMAINING_CUSTOMER') {
    if (!nn(input.original_network_upgrade_assignment)) reasons.push('ORIGINAL_ASSIGNMENT_INVALID');
    if (!nn(input.amended_network_upgrade_assignment)) reasons.push('AMENDED_ASSIGNMENT_INVALID');
    if (!nn(input.original_security_required)) reasons.push('ORIGINAL_SECURITY_INVALID');
    if (!nn(input.amended_security_required)) reasons.push('AMENDED_SECURITY_INVALID');
    if (!nonEmpty(input.amended_lgia_or_notice_hash)) reasons.push('AMENDED_LGIA_OR_NOTICE_MISSING');
    if (input.amended_assignment_effective !== true) reasons.push('AMENDED_ASSIGNMENT_NOT_EFFECTIVE');
    if (reasons.length) return { status: RESULT.UNKNOWN, reasons: [...new Set(reasons)] };

    const assignmentReduction = input.original_network_upgrade_assignment - input.amended_network_upgrade_assignment;
    const securityReduction = input.original_security_required - input.amended_security_required;
    if (assignmentReduction < 0 || securityReduction < 0) {
      return { status: RESULT.NEEDS_REVIEW, reasons: ['AMENDED_VALUES_INCREASE_CAPITAL_REQUIREMENT'] };
    }
    if (assignmentReduction === 0 && securityReduction === 0) {
      return { status: RESULT.NO_RECOVERY, assignment_reduction: 0, security_release_candidate: 0, reasons: ['NO_VERIFIED_REDUCTION'] };
    }
    return {
      status: RESULT.SUPPORTED_CANDIDATE,
      candidate_type: 'CAPITAL_RELEASE_NOT_CASH_RECOVERY',
      assignment_reduction: assignmentReduction,
      security_release_candidate: securityReduction,
      currency: input.currency || null,
      reasons: ['VERIFIED_AMENDED_CLUSTER_ASSIGNMENT']
    };
  }

  if (input.role === 'WITHDRAWN_CUSTOMER') {
    if (!nn(input.withdrawal_penalty_paid)) reasons.push('WITHDRAWAL_PENALTY_INVALID');
    if (!nn(input.penalty_applied_to_study_costs)) reasons.push('STUDY_COST_APPLICATION_INVALID');
    if (!nn(input.penalty_applied_to_shared_cost_increases)) reasons.push('SHARED_COST_APPLICATION_INVALID');
    if (!nn(input.penalty_already_returned)) reasons.push('RETURNED_AMOUNT_INVALID');
    if (input.final_distribution_complete !== true) reasons.push('FINAL_DISTRIBUTION_NOT_VERIFIED');
    if (!nonEmpty(input.final_distribution_source_hash)) reasons.push('FINAL_DISTRIBUTION_SOURCE_MISSING');
    if (reasons.length) return { status: RESULT.UNKNOWN, reasons: [...new Set(reasons)] };

    const residual = input.withdrawal_penalty_paid - input.penalty_applied_to_study_costs - input.penalty_applied_to_shared_cost_increases - input.penalty_already_returned;
    if (residual < 0) {
      return { status: RESULT.NEEDS_REVIEW, reasons: ['PENALTY_APPLICATIONS_EXCEED_VERIFIED_PAYMENT'] };
    }
    if (residual === 0) {
      return { status: RESULT.NO_RECOVERY, cash_refund_candidate: 0, reasons: ['NO_RESIDUAL_PENALTY_FUNDS'] };
    }
    return {
      status: RESULT.SUPPORTED_CANDIDATE,
      candidate_type: 'CASH_REFUND_CANDIDATE',
      cash_refund_candidate: residual,
      currency: input.currency || null,
      reasons: ['VERIFIED_RESIDUAL_WITHDRAWAL_PENALTY']
    };
  }

  return { status: RESULT.UNKNOWN, reasons: ['ROLE_NOT_SUPPORTED'] };
}

module.exports = { RESULT, evaluateClusterWithdrawalCapital };
