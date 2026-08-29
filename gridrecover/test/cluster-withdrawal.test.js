'use strict';

const assert = require('assert');
const { RESULT, evaluateClusterWithdrawalCapital } = require('../src/cluster-withdrawal');

function common(role) {
  return {
    jurisdiction: 'US_FEDERAL_FERC',
    project_scope: 'LARGE_GENERATOR_GT_20MW_CLUSTER_PROCESS',
    transmission_provider: 'TP-001',
    provider_tariff_document_hash: 'sha256:tariff',
    provider_tariff_locator: 'Section 3.7.1.2.4/3.7.1.2.5',
    provider_rule_match_verified: true,
    cluster_id: 'CLUSTER-001',
    withdrawal_event_source_hash: 'sha256:withdrawal',
    withdrawal_event_verified: true,
    role,
    currency: 'USD'
  };
}

{
  const i = Object.assign(common('REMAINING_CUSTOMER'), {
    original_network_upgrade_assignment: 5000000,
    amended_network_upgrade_assignment: 3500000,
    original_security_required: 5000000,
    amended_security_required: 3500000,
    amended_lgia_or_notice_hash: 'sha256:amended',
    amended_assignment_effective: true
  });
  const r = evaluateClusterWithdrawalCapital(i);
  assert.equal(r.status, RESULT.SUPPORTED_CANDIDATE);
  assert.equal(r.assignment_reduction, 1500000);
  assert.equal(r.security_release_candidate, 1500000);
  assert.equal(r.candidate_type, 'CAPITAL_RELEASE_NOT_CASH_RECOVERY');
}

{
  const i = Object.assign(common('REMAINING_CUSTOMER'), {
    original_network_upgrade_assignment: 5000000,
    amended_network_upgrade_assignment: 5000000,
    original_security_required: 5000000,
    amended_security_required: 5000000,
    amended_lgia_or_notice_hash: 'sha256:amended',
    amended_assignment_effective: true
  });
  const r = evaluateClusterWithdrawalCapital(i);
  assert.equal(r.status, RESULT.NO_RECOVERY);
}

{
  const i = Object.assign(common('REMAINING_CUSTOMER'), {
    original_network_upgrade_assignment: 5000000,
    amended_network_upgrade_assignment: 5500000,
    original_security_required: 5000000,
    amended_security_required: 5500000,
    amended_lgia_or_notice_hash: 'sha256:amended',
    amended_assignment_effective: true
  });
  const r = evaluateClusterWithdrawalCapital(i);
  assert.equal(r.status, RESULT.NEEDS_REVIEW);
}

{
  const i = Object.assign(common('WITHDRAWN_CUSTOMER'), {
    withdrawal_penalty_paid: 1000000,
    penalty_applied_to_study_costs: 150000,
    penalty_applied_to_shared_cost_increases: 500000,
    penalty_already_returned: 100000,
    final_distribution_complete: true,
    final_distribution_source_hash: 'sha256:distribution'
  });
  const r = evaluateClusterWithdrawalCapital(i);
  assert.equal(r.status, RESULT.SUPPORTED_CANDIDATE);
  assert.equal(r.cash_refund_candidate, 250000);
  assert.equal(r.candidate_type, 'CASH_REFUND_CANDIDATE');
}

{
  const i = Object.assign(common('WITHDRAWN_CUSTOMER'), {
    withdrawal_penalty_paid: 1000000,
    penalty_applied_to_study_costs: 150000,
    penalty_applied_to_shared_cost_increases: 850000,
    penalty_already_returned: 0,
    final_distribution_complete: true,
    final_distribution_source_hash: 'sha256:distribution'
  });
  const r = evaluateClusterWithdrawalCapital(i);
  assert.equal(r.status, RESULT.NO_RECOVERY);
}

{
  const i = Object.assign(common('WITHDRAWN_CUSTOMER'), {
    withdrawal_penalty_paid: 1000000,
    penalty_applied_to_study_costs: 150000,
    penalty_applied_to_shared_cost_increases: 500000,
    penalty_already_returned: 0,
    final_distribution_complete: false,
    final_distribution_source_hash: 'sha256:distribution'
  });
  const r = evaluateClusterWithdrawalCapital(i);
  assert.equal(r.status, RESULT.UNKNOWN);
  assert(r.reasons.includes('FINAL_DISTRIBUTION_NOT_VERIFIED'));
}

{
  const i = Object.assign(common('WITHDRAWN_CUSTOMER'), {
    withdrawal_penalty_paid: 1000000,
    penalty_applied_to_study_costs: 800000,
    penalty_applied_to_shared_cost_increases: 500000,
    penalty_already_returned: 0,
    final_distribution_complete: true,
    final_distribution_source_hash: 'sha256:distribution'
  });
  const r = evaluateClusterWithdrawalCapital(i);
  assert.equal(r.status, RESULT.NEEDS_REVIEW);
}

{
  const i = Object.assign(common('WITHDRAWN_CUSTOMER'), {
    withdrawal_penalty_paid: 1000000,
    penalty_applied_to_study_costs: 0,
    penalty_applied_to_shared_cost_increases: 0,
    penalty_already_returned: 0,
    final_distribution_complete: true,
    final_distribution_source_hash: 'sha256:distribution'
  });
  i.provider_rule_match_verified = false;
  const r = evaluateClusterWithdrawalCapital(i);
  assert.equal(r.status, RESULT.UNKNOWN);
  assert(r.reasons.includes('PROVIDER_RULE_MATCH_NOT_VERIFIED'));
}

console.log('GRIDRECOVER cluster withdrawal: 8/8 PASS');
