'use strict';

const OUTCOME = Object.freeze({
  PILOT_ADMISSIBLE: 'PILOT_ADMISSIBLE',
  SOURCE_REQUIRED: 'SOURCE_REQUIRED',
  OUT_OF_SCOPE: 'OUT_OF_SCOPE',
  REVIEW_REQUIRED: 'REVIEW_REQUIRED'
});

const PILOT_SUPPORTED_LANES = Object.freeze({
  MISO_2026_NETWORK_UPGRADE_REPAYMENT: {
    jurisdiction: 'US_FEDERAL_FERC',
    transmission_provider: 'MISO',
    project_scope: 'LARGE_GENERATOR_GT_20MW',
    provider_rule_id: 'MISO_GIA_11_4_1_NETWORK_UPGRADE_REPAYMENT_2026'
  }
});

function hasDoc(docs, type) {
  return Array.isArray(docs) && docs.some(d => d && d.type === type && d.document_id && d.sha256);
}

function evaluatePilotAdmission(input) {
  const missing = [];
  const blockers = [];
  if (!input || typeof input !== 'object') return { outcome: OUTCOME.SOURCE_REQUIRED, missing: ['INTAKE'] };

  const lane = PILOT_SUPPORTED_LANES[input.lane_id];
  if (!lane) return { outcome: OUTCOME.OUT_OF_SCOPE, blockers: ['LANE_NOT_PILOT_SUPPORTED'] };
  if (input.jurisdiction !== lane.jurisdiction) return { outcome: OUTCOME.OUT_OF_SCOPE, blockers: ['JURISDICTION_NOT_SUPPORTED_FOR_LANE'] };
  if (input.transmission_provider !== lane.transmission_provider) return { outcome: OUTCOME.OUT_OF_SCOPE, blockers: ['TRANSMISSION_PROVIDER_NOT_SUPPORTED_FOR_LANE'] };
  if (input.project_scope !== lane.project_scope) return { outcome: OUTCOME.OUT_OF_SCOPE, blockers: ['PROJECT_SCOPE_NOT_SUPPORTED_FOR_LANE'] };
  if (input.provider_rule_id !== lane.provider_rule_id) blockers.push('PROVIDER_RULE_ID_NOT_PINNED');
  if (input.provider_applicability_status !== 'APPLICABLE') blockers.push('PROVIDER_APPLICABILITY_NOT_PROVEN');

  if (!hasDoc(input.documents, 'EXECUTED_OR_FILED_LGIA')) missing.push('EXECUTED_OR_FILED_LGIA');
  if (!hasDoc(input.documents, 'EFFECTIVE_PROVIDER_TARIFF_OR_LGIP')) missing.push('EFFECTIVE_PROVIDER_TARIFF_OR_LGIP');
  if (!hasDoc(input.documents, 'FERC_ACCEPTANCE_ORDER')) missing.push('FERC_ACCEPTANCE_ORDER');
  if (!hasDoc(input.documents, 'REPAYABLE_BASIS')) missing.push('REPAYABLE_BASIS');
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
    lane_id: input.lane_id,
    missing: [],
    blockers: [],
    limitations: [
      'admission proves only that the supported lane and minimum evidence package are present',
      'admission does not establish entitlement',
      'admission does not establish recoverable amount',
      'all project-specific amendments, Attachment FF treatment, payments, offsets and timing remain reviewable'
    ]
  };
}

module.exports = { OUTCOME, PILOT_SUPPORTED_LANES, evaluatePilotAdmission };
