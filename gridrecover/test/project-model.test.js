'use strict';

const assert = require('assert');
const { STATUS, validateProjectCase } = require('../src/project-model');

function validCase() {
  return {
    case_id: 'CASE-001',
    customer_id: 'DEV-001',
    project_id: 'PROJECT-001',
    project_name: 'Synthetic Solar 250 MW',
    jurisdiction: 'US_FEDERAL_FERC',
    transmission_provider: 'TP-001',
    queue_or_interconnection_id: 'QUEUE-001',
    process_stage: 'LGIA_EXECUTED',
    currency: 'USD',
    ingested_by_user_id: 'analyst-uploader',
    rule_applicability_verified: true,
    agreement_authority_verified: true,
    rule_reviewer_id: 'reviewer-rule',
    agreement_reviewer_id: 'reviewer-agreement',
    effective_rule_source: {
      document_id: 'RULE-001',
      sha256: 'sha256:rule',
      locator: 'Article 11.4.1',
      document_type: 'TARIFF_OR_RULE',
      effective_or_execution_date: '2026-01-01',
      superseded: false
    },
    executed_agreement_source: {
      document_id: 'LGIA-001',
      sha256: 'sha256:lgia',
      locator: 'Article 11.4.1',
      document_type: 'EXECUTED_LGIA',
      effective_or_execution_date: '2025-06-01',
      superseded: false
    }
  };
}

{
  const r = validateProjectCase(validCase());
  assert.equal(r.status, STATUS.VALID);
  assert.deepEqual(r.reasons, []);
}

{
  const i = validCase();
  delete i.executed_agreement_source.sha256;
  const r = validateProjectCase(i);
  assert.equal(r.status, STATUS.INVALID);
  assert(r.reasons.includes('AGREEMENT_SHA256_MISSING'));
}

{
  const i = validCase();
  i.executed_agreement_source.superseded = true;
  const r = validateProjectCase(i);
  assert.equal(r.status, STATUS.INVALID);
  assert(r.reasons.includes('AGREEMENT_SUPERSESSION_CHAIN_MISSING'));
}

{
  const i = validCase();
  i.rule_reviewer_id = i.ingested_by_user_id;
  const r = validateProjectCase(i);
  assert.equal(r.status, STATUS.INVALID);
  assert(r.reasons.includes('RULE_SELF_ATTESTATION_FORBIDDEN'));
}

{
  const i = validCase();
  i.agreement_authority_verified = false;
  const r = validateProjectCase(i);
  assert.equal(r.status, STATUS.INVALID);
  assert(r.reasons.includes('AGREEMENT_AUTHORITY_NOT_VERIFIED'));
}

{
  const i = validCase();
  i.rule_applicability_verified = false;
  const r = validateProjectCase(i);
  assert.equal(r.status, STATUS.INVALID);
  assert(r.reasons.includes('RULE_APPLICABILITY_NOT_VERIFIED'));
}

console.log('GRIDRECOVER project model: 6/6 PASS');
