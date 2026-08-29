'use strict';

const assert = require('assert');
const { FINDING, evaluateNetworkUpgradeRepayment } = require('../src/gridrecover-core');

function valid(overrides = {}) {
  const base = {
    jurisdiction: 'US_FEDERAL_FERC',
    project_scope: 'LARGE_GENERATOR_GT_20MW',
    agreement: {
      executed_lgia_id: 'LGIA-TEST-001',
      article_11_4_1_match: true,
      source_document_hash: 'sha256:agreement',
      source_locator: 'Article 11.4.1',
      superseded: false,
      trigger_satisfied: true,
      repayment_schedule_supported: true
    },
    economics: {
      network_upgrade_amount_paid: 1000000,
      amounts_already_refunded: 100000,
      repayments_received: 250000,
      currency: 'USD'
    },
    evidence: {
      payment_source_hash: 'sha256:payment',
      payment_matches_project: true,
      payment_is_network_upgrade: true
    }
  };
  return Object.assign(base, overrides);
}

{
  const r = evaluateNetworkUpgradeRepayment(valid());
  assert.equal(r.status, FINDING.SUPPORTED_CANDIDATE);
  assert.equal(r.candidate_amount, 650000);
}

{
  const i = valid();
  i.agreement.article_11_4_1_match = false;
  const r = evaluateNetworkUpgradeRepayment(i);
  assert.equal(r.status, FINDING.UNKNOWN);
  assert.equal(r.candidate_amount, null);
  assert(r.reasons.includes('CREDITING_LANGUAGE_NOT_VERIFIED'));
}

{
  const i = valid();
  i.agreement.executed_lgia_id = '';
  const r = evaluateNetworkUpgradeRepayment(i);
  assert.equal(r.status, FINDING.UNKNOWN);
  assert(r.reasons.includes('EXECUTED_LGIA_NOT_IDENTIFIED'));
}

{
  const i = valid();
  i.agreement.superseded = true;
  const r = evaluateNetworkUpgradeRepayment(i);
  assert.equal(r.status, FINDING.UNKNOWN);
  assert(r.reasons.includes('AGREEMENT_SUPERSEDED'));
}

{
  const i = valid();
  i.evidence.payment_matches_project = false;
  const r = evaluateNetworkUpgradeRepayment(i);
  assert.equal(r.status, FINDING.UNKNOWN);
  assert(r.reasons.includes('PAYMENT_PROJECT_MATCH_NOT_VERIFIED'));
}

{
  const i = valid();
  i.agreement.trigger_satisfied = false;
  const r = evaluateNetworkUpgradeRepayment(i);
  assert.equal(r.status, FINDING.UNKNOWN);
  assert(r.reasons.includes('REPAYMENT_TRIGGER_NOT_VERIFIED'));
}

{
  const i = valid();
  i.economics.amounts_already_refunded = 750000;
  i.economics.repayments_received = 250000;
  const r = evaluateNetworkUpgradeRepayment(i);
  assert.equal(r.status, FINDING.NO_RECOVERY);
  assert.equal(r.candidate_amount, 0);
}

{
  const i = valid();
  i.economics.amounts_already_refunded = 900000;
  i.economics.repayments_received = 250000;
  const r = evaluateNetworkUpgradeRepayment(i);
  assert.equal(r.status, FINDING.NEEDS_REVIEW);
  assert.equal(r.candidate_amount, null);
}

{
  const i = valid();
  i.jurisdiction = 'PJM';
  const r = evaluateNetworkUpgradeRepayment(i);
  assert.equal(r.status, FINDING.UNKNOWN);
  assert(r.reasons.includes('JURISDICTION_NOT_SUPPORTED'));
}

{
  const i = valid();
  i.economics.network_upgrade_amount_paid = -1;
  const r = evaluateNetworkUpgradeRepayment(i);
  assert.equal(r.status, FINDING.UNKNOWN);
  assert(r.reasons.includes('NETWORK_UPGRADE_PAYMENT_INVALID'));
}

console.log('GRIDRECOVER core: 10/10 PASS');
