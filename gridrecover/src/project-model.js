'use strict';

const STATUS = Object.freeze({ VALID: 'VALID', INVALID: 'INVALID' });

function nonEmpty(v) { return typeof v === 'string' && v.trim().length > 0; }
function isoDate(v) { return nonEmpty(v) && !Number.isNaN(Date.parse(v)); }

function validateSource(source, label) {
  const reasons = [];
  if (!source || typeof source !== 'object') return [`${label}_SOURCE_MISSING`];
  if (!nonEmpty(source.document_id)) reasons.push(`${label}_DOCUMENT_ID_MISSING`);
  if (!nonEmpty(source.sha256)) reasons.push(`${label}_SHA256_MISSING`);
  if (!nonEmpty(source.locator)) reasons.push(`${label}_LOCATOR_MISSING`);
  if (!nonEmpty(source.document_type)) reasons.push(`${label}_DOCUMENT_TYPE_MISSING`);
  if (!isoDate(source.effective_or_execution_date)) reasons.push(`${label}_DATE_INVALID`);
  if (source.superseded === true && !nonEmpty(source.superseded_by_document_id)) {
    reasons.push(`${label}_SUPERSESSION_CHAIN_MISSING`);
  }
  return reasons;
}

function validateProjectCase(input) {
  const reasons = [];
  if (!input || typeof input !== 'object') return { status: STATUS.INVALID, reasons: ['CASE_MISSING'] };
  if (!nonEmpty(input.case_id)) reasons.push('CASE_ID_MISSING');
  if (!nonEmpty(input.customer_id)) reasons.push('CUSTOMER_ID_MISSING');
  if (!nonEmpty(input.project_id)) reasons.push('PROJECT_ID_MISSING');
  if (!nonEmpty(input.project_name)) reasons.push('PROJECT_NAME_MISSING');
  if (!nonEmpty(input.jurisdiction)) reasons.push('JURISDICTION_MISSING');
  if (!nonEmpty(input.transmission_provider)) reasons.push('TRANSMISSION_PROVIDER_MISSING');
  if (!nonEmpty(input.queue_or_interconnection_id)) reasons.push('QUEUE_OR_INTERCONNECTION_ID_MISSING');
  if (!nonEmpty(input.process_stage)) reasons.push('PROCESS_STAGE_MISSING');
  if (!nonEmpty(input.currency)) reasons.push('CURRENCY_MISSING');

  reasons.push(...validateSource(input.effective_rule_source, 'RULE'));
  reasons.push(...validateSource(input.executed_agreement_source, 'AGREEMENT'));

  if (input.customer_id === input.transmission_provider) reasons.push('CUSTOMER_PROVIDER_ID_COLLISION');
  if (input.rule_applicability_verified !== true) reasons.push('RULE_APPLICABILITY_NOT_VERIFIED');
  if (input.agreement_authority_verified !== true) reasons.push('AGREEMENT_AUTHORITY_NOT_VERIFIED');
  if (!nonEmpty(input.rule_reviewer_id)) reasons.push('RULE_REVIEWER_MISSING');
  if (!nonEmpty(input.agreement_reviewer_id)) reasons.push('AGREEMENT_REVIEWER_MISSING');
  if (input.rule_reviewer_id && input.rule_reviewer_id === input.ingested_by_user_id) reasons.push('RULE_SELF_ATTESTATION_FORBIDDEN');
  if (input.agreement_reviewer_id && input.agreement_reviewer_id === input.ingested_by_user_id) reasons.push('AGREEMENT_SELF_ATTESTATION_FORBIDDEN');

  return { status: reasons.length ? STATUS.INVALID : STATUS.VALID, reasons: [...new Set(reasons)] };
}

module.exports = { STATUS, validateProjectCase, validateSource };
