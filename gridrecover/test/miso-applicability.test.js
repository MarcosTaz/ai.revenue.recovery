'use strict';

const assert = require('assert');
const { STATUS, evaluateMiso2026RepaymentApplicability } = require('../src/miso-applicability');

function valid() {
  return {
    jurisdiction: 'US_FEDERAL_FERC',
    transmission_provider: 'MISO',
    project_scope: 'LARGE_GENERATOR_GT_20MW',
    project_gia_source_hash: 'sha256:gia',
    project_gia_article_locator: 'Article 11.4.1',
    project_gia_article_11_4_1_match: true,
    provider_tariff_source_hash: 'sha256:tariff',
    ferc_acceptance_source_hash: 'sha256:order',
    ferc_acceptance_accession: '20260203-3023',
    project_gia_tariff_record_verified: true,
    project_gia_tariff_record: '110.0.0',
    provider_tariff_effective_date: '2026-02-04'
  };
}

assert.equal(evaluateMiso2026RepaymentApplicability(valid()).status, STATUS.APPLICABLE);

{
  const i = valid(); i.transmission_provider = 'PJM';
  assert.equal(evaluateMiso2026RepaymentApplicability(i).status, STATUS.NOT_APPLICABLE);
}
{
  const i = valid(); i.project_gia_tariff_record_verified = false;
  assert.equal(evaluateMiso2026RepaymentApplicability(i).status, STATUS.NEEDS_VERSION_REVIEW);
}
{
  const i = valid(); i.project_gia_tariff_record = '108.0.0';
  const r = evaluateMiso2026RepaymentApplicability(i);
  assert.equal(r.status, STATUS.NEEDS_VERSION_REVIEW);
  assert(r.reasons.includes('PROJECT_GIA_USES_DIFFERENT_TARIFF_RECORD'));
}
{
  const i = valid(); delete i.ferc_acceptance_source_hash;
  assert.equal(evaluateMiso2026RepaymentApplicability(i).status, STATUS.UNKNOWN);
}
{
  const i = valid(); i.ferc_acceptance_accession = 'wrong';
  const r = evaluateMiso2026RepaymentApplicability(i);
  assert.equal(r.status, STATUS.UNKNOWN);
  assert(r.reasons.includes('FERC_ACCEPTANCE_ACCESSION_MISMATCH'));
}
{
  const i = valid(); i.provider_tariff_effective_date = '2025-01-01';
  assert.equal(evaluateMiso2026RepaymentApplicability(i).status, STATUS.NEEDS_VERSION_REVIEW);
}

console.log('GRIDRECOVER MISO applicability: 7/7 PASS');
