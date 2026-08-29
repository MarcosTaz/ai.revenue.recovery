'use strict';

const STATUS = Object.freeze({
  APPLICABLE: 'APPLICABLE',
  NEEDS_VERSION_REVIEW: 'NEEDS_VERSION_REVIEW',
  NOT_APPLICABLE: 'NOT_APPLICABLE',
  UNKNOWN: 'UNKNOWN'
});

function nonEmpty(v) { return typeof v === 'string' && v.trim().length > 0; }

function evaluateMiso2026RepaymentApplicability(input) {
  const missing = [];
  if (!input || typeof input !== 'object') return { status: STATUS.UNKNOWN, reasons: ['INPUT_MISSING'] };
  if (input.jurisdiction !== 'US_FEDERAL_FERC') return { status: STATUS.NOT_APPLICABLE, reasons: ['JURISDICTION_NOT_MISO_FERC'] };
  if (input.transmission_provider !== 'MISO') return { status: STATUS.NOT_APPLICABLE, reasons: ['TRANSMISSION_PROVIDER_NOT_MISO'] };
  if (input.project_scope !== 'LARGE_GENERATOR_GT_20MW') return { status: STATUS.NOT_APPLICABLE, reasons: ['PROJECT_SCOPE_NOT_SUPPORTED'] };

  if (!nonEmpty(input.project_gia_source_hash)) missing.push('PROJECT_GIA_SOURCE_MISSING');
  if (!nonEmpty(input.project_gia_article_locator)) missing.push('PROJECT_GIA_ARTICLE_LOCATOR_MISSING');
  if (input.project_gia_article_11_4_1_match !== true) missing.push('PROJECT_GIA_ARTICLE_MATCH_NOT_VERIFIED');
  if (!nonEmpty(input.provider_tariff_source_hash)) missing.push('PROVIDER_TARIFF_SOURCE_MISSING');
  if (!nonEmpty(input.ferc_acceptance_source_hash)) missing.push('FERC_ACCEPTANCE_SOURCE_MISSING');
  if (input.ferc_acceptance_accession !== '20260203-3023') missing.push('FERC_ACCEPTANCE_ACCESSION_MISMATCH');

  if (missing.length) return { status: STATUS.UNKNOWN, reasons: missing };

  if (input.project_gia_tariff_record_verified !== true || !nonEmpty(input.project_gia_tariff_record)) {
    return { status: STATUS.NEEDS_VERSION_REVIEW, reasons: ['PROJECT_GIA_TARIFF_RECORD_NOT_VERIFIED'] };
  }
  if (input.project_gia_tariff_record !== '110.0.0') {
    return { status: STATUS.NEEDS_VERSION_REVIEW, reasons: ['PROJECT_GIA_USES_DIFFERENT_TARIFF_RECORD'] };
  }
  if (input.provider_tariff_effective_date !== '2026-02-04') {
    return { status: STATUS.NEEDS_VERSION_REVIEW, reasons: ['PROVIDER_TARIFF_EFFECTIVE_DATE_MISMATCH'] };
  }

  return {
    status: STATUS.APPLICABLE,
    rule_id: 'MISO_GIA_11_4_1_NETWORK_UPGRADE_REPAYMENT_2026',
    accepted_tariff_record: '110.0.0',
    effective_date: '2026-02-04',
    limitations: [
      'applicability does not establish that a specific Network Upgrade amount is repayable',
      'Attachment FF repayable-portion evidence remains mandatory',
      'project-specific amendments and superseding agreements remain controlling'
    ]
  };
}

module.exports = { STATUS, evaluateMiso2026RepaymentApplicability };
