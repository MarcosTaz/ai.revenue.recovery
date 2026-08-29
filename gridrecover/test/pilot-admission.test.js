'use strict';

const assert = require('assert');
const { OUTCOME, evaluatePilotAdmission } = require('../src/pilot-admission');

function valid() {
  return {
    lane_id: 'MISO_2026_NETWORK_UPGRADE_REPAYMENT',
    jurisdiction: 'US_FEDERAL_FERC',
    transmission_provider: 'MISO',
    project_scope: 'LARGE_GENERATOR_GT_20MW',
    provider_rule_id: 'MISO_GIA_11_4_1_NETWORK_UPGRADE_REPAYMENT_2026',
    provider_applicability_status: 'APPLICABLE',
    documents: [
      { type: 'EXECUTED_OR_FILED_LGIA', document_id: 'D1', sha256: 'h1' },
      { type: 'EFFECTIVE_PROVIDER_TARIFF_OR_LGIP', document_id: 'D2', sha256: 'h2' },
      { type: 'FERC_ACCEPTANCE_ORDER', document_id: 'D3', sha256: 'h3' },
      { type: 'REPAYABLE_BASIS', document_id: 'D4', sha256: 'h4' },
      { type: 'PAYMENT_OR_SECURITY_LEDGER', document_id: 'D5', sha256: 'h5' },
      { type: 'TRIGGER_EVENT_EVIDENCE', document_id: 'D6', sha256: 'h6' }
    ],
    rule_applicability_reviewer_independent: true,
    agreement_authority_reviewer_independent: true,
    customer_authorized_analysis: true,
    tenant_workspace_ready: true
  };
}

assert.equal(evaluatePilotAdmission(valid()).outcome, OUTCOME.PILOT_ADMISSIBLE);

{
  const i = valid(); i.documents = i.documents.filter(d => d.type !== 'EXECUTED_OR_FILED_LGIA');
  const r = evaluatePilotAdmission(i);
  assert.equal(r.outcome, OUTCOME.SOURCE_REQUIRED);
  assert(r.missing.includes('EXECUTED_OR_FILED_LGIA'));
}
{
  const i = valid(); i.documents = i.documents.filter(d => d.type !== 'REPAYABLE_BASIS');
  const r = evaluatePilotAdmission(i);
  assert.equal(r.outcome, OUTCOME.SOURCE_REQUIRED);
  assert(r.missing.includes('REPAYABLE_BASIS'));
}
{
  const i = valid(); i.jurisdiction = 'ERCOT_STATE_ONLY';
  assert.equal(evaluatePilotAdmission(i).outcome, OUTCOME.OUT_OF_SCOPE);
}
{
  const i = valid(); i.transmission_provider = 'PJM';
  assert.equal(evaluatePilotAdmission(i).outcome, OUTCOME.OUT_OF_SCOPE);
}
{
  const i = valid(); i.lane_id = 'GENERIC_FERC_CLUSTER_WITHDRAWAL';
  const r = evaluatePilotAdmission(i);
  assert.equal(r.outcome, OUTCOME.OUT_OF_SCOPE);
  assert(r.blockers.includes('LANE_NOT_PILOT_SUPPORTED'));
}
{
  const i = valid(); i.provider_applicability_status = 'NEEDS_VERSION_REVIEW';
  const r = evaluatePilotAdmission(i);
  assert.equal(r.outcome, OUTCOME.REVIEW_REQUIRED);
  assert(r.blockers.includes('PROVIDER_APPLICABILITY_NOT_PROVEN'));
}
{
  const i = valid(); i.customer_authorized_analysis = false;
  const r = evaluatePilotAdmission(i);
  assert.equal(r.outcome, OUTCOME.REVIEW_REQUIRED);
  assert(r.blockers.includes('CUSTOMER_AUTHORIZATION_REQUIRED'));
}
{
  const i = valid(); i.rule_applicability_reviewer_independent = false;
  const r = evaluatePilotAdmission(i);
  assert.equal(r.outcome, OUTCOME.REVIEW_REQUIRED);
  assert(r.blockers.includes('INDEPENDENT_RULE_REVIEW_REQUIRED'));
}
{
  const i = valid(); i.tenant_workspace_ready = false;
  const r = evaluatePilotAdmission(i);
  assert.equal(r.outcome, OUTCOME.REVIEW_REQUIRED);
  assert(r.blockers.includes('TENANT_WORKSPACE_REQUIRED'));
}

console.log('GRIDRECOVER pilot admission: 10/10 PASS');
