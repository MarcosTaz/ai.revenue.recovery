'use strict';

const OUTCOME = Object.freeze({
  PILOT_ADMISSIBLE: 'PILOT_ADMISSIBLE',
  SOURCE_REQUIRED: 'SOURCE_REQUIRED',
  OUT_OF_SCOPE: 'OUT_OF_SCOPE',
  REVIEW_REQUIRED: 'REVIEW_REQUIRED'
});

function hasDoc(docs, type) {
  return Array.isArray(docs) && docs.some(d => d && d.type === type && d.document_id && d.sha256);
}

function evaluatePilotAdmission(input) {
  const missing = [];
  const blockers = [];
  if (!input || typeof input !== 'object') return { outcome: OUTCOME.SOURCE_REQUIRED, missing: ['INTAKE'] };
  if (input.jurisdiction !== 'US_FEDERAL_FERC') return { outcome: OUTCOME.OUT_OF_SCOPE, blockers: ['JURISDICTION_NOT_SUPPORTED'] };
  if (!['LARGE_GENERATOR_GT_20MW', 'LARGE_GENERATOR_GT_20MW_CLUSTER_PROCESS'].includes(input.project_scope)) {
    return { outcome: OUTCOME.OUT_OF_SCOPE, blockers: ['PROJECT_SCOPE_NOT_SUPPORTED'] };
  }

  if (!hasDoc(input.documents, 'EXECUTED_OR_FILED_LGIA')) missing.push('EXECUTED_OR_FILED_LGIA');
  if (!hasDoc(input.documents, 'EFFECTIVE_PROVIDER_TARIFF_OR_LGIP')) missing.push('EFFECTIVE_PROVIDER_TARIFF_OR_LGIP');
  if (!hasDoc(input.documents, 'PAYMENT_OR_SECURITY_LEDGER')) missing.push('PAYMENT_OR_SECURITY_LEDGER');
  if (!hasDoc(input.documents, 'TRIGGER_EVENT_EVIDENCE')) missing.push('TRIGGER_EVENT_EVIDENCE');

  if (input.rule_applicability_reviewer_independent !== true) blockers.push('INDEPENDENT_RULE_REVIEW_REQUIRED');
  if (input.agreement_authority_reviewer_independent !== true) blockers.push('INDEPENDENT_AGREEMENT_REVIEW_REQUIRED');
  if (input.customer_authorized_analysis !== true) blockers.push('CUSTOMER_AUTHORIZATION_REQUIRED');
  if (input.tenant_workspace_ready !== true) blockers.push('TENANT_WORKSPACE_REQUIRED');

  if (missing.length) return { outcome: OUTCOME.SOURCE_REQUIRED, missing, blockers };
  if (blockers.length) return { outcome: OUTCOME.REVIEW_REQUIRED, missing: [], blockers };
  return {
    outcome: OUTCOME.PILOT_ADMISSIBLE,
    missing: [],
    blockers: [],
    limitations: ['admission does not establish entitlement', 'admission does not establish recoverable amount']
  };
}

module.exports = { OUTCOME, evaluatePilotAdmission };
