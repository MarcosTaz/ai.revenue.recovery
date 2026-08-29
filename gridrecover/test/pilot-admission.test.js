'use strict';

const assert = require('assert');
const { OUTCOME, evaluatePilotAdmission } = require('../src/pilot-admission');

function valid() {
  return {
    jurisdiction: 'US_FEDERAL_FERC',
    project_scope: 'LARGE_GENERATOR_GT_20MW',
    documents: [
      { type: 'EXECUTED_OR_FILED_LGIA', document_id: 'D1', sha256: 'h1' },
      { type: 'EFFECTIVE_PROVIDER_TARIFF_OR_LGIP', document_id: 'D2', sha256: 'h2' },
      { type: 'PAYMENT_OR_SECURITY_LEDGER', document_id: 'D3', sha256: 'h3' },
      { type: 'TRIGGER_EVENT_EVIDENCE', document_id: 'D4', sha256: 'h4' }
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
  const i = valid(); i.jurisdiction = 'ERCOT_STATE_ONLY';
  assert.equal(evaluatePilotAdmission(i).outcome, OUTCOME.OUT_OF_SCOPE);
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

console.log('GRIDRECOVER pilot admission: 6/6 PASS');
