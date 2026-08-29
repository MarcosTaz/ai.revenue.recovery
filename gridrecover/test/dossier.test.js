'use strict';

const assert = require('assert');
const { buildRecoveryDossier } = require('../src/dossier');

const meta = {
  case_id: 'CASE-1', project_id: 'PROJECT-1', customer_id: 'CUSTOMER-1',
  jurisdiction: 'US_FEDERAL_FERC', transmission_provider: 'TP-1', currency: 'USD'
};
const sources = [
  { document_id: 'LGIA-1', sha256: 'sha256:lgia', locator: 'Article 11.4.1' },
  { document_id: 'PAY-1', sha256: 'sha256:pay', locator: 'payment line 1' }
];

{
  const d = buildRecoveryDossier({
    caseMeta: meta,
    result: { status: 'SUPPORTED_CANDIDATE', candidate_amount: 650000, currency: 'USD' },
    sources,
    calculations: [{ formula: '1000000-100000-250000', result: 650000 }],
    uncertainties: ['current due date requires reviewer confirmation'],
    nextAction: 'Verify current repayment schedule and send controlled reconciliation to counterparty.'
  });
  assert.equal(d.finding.candidate_value, 650000);
  assert.equal(d.finding.verified_recovery, false);
  assert.equal(d.finding.payment_verified, false);
  assert.equal(d.truth_boundary.candidate_is_not_recovery, true);
}

{
  const d = buildRecoveryDossier({
    caseMeta: meta,
    result: { status: 'SUPPORTED_CANDIDATE', candidate_type: 'CAPITAL_RELEASE_NOT_CASH_RECOVERY', security_release_candidate: 1500000, currency: 'USD' },
    sources,
    calculations: [{ formula: '5000000-3500000', result: 1500000 }],
    uncertainties: [],
    nextAction: 'Confirm effective amended security requirement with Transmission Provider.'
  });
  assert.equal(d.finding.candidate_value, 1500000);
  assert.equal(d.truth_boundary.release_is_not_cash, true);
  assert.equal(d.finding.verified_recovery, false);
}

{
  const d = buildRecoveryDossier({
    caseMeta: meta,
    result: { status: 'NO_RECOVERY', candidate_amount: 0, currency: 'USD' },
    sources,
    calculations: [],
    uncertainties: [],
    nextAction: 'Close case as true null unless new source evidence arrives.'
  });
  assert.equal(d.finding.candidate_value, null);
  assert.equal(d.finding.currency, null);
  assert.match(d.finding.wording, /No supported recovery candidate/);
}

{
  const d = buildRecoveryDossier({
    caseMeta: meta,
    result: { status: 'SUPPORTED_CANDIDATE', candidate_amount: 1 },
    sources: [],
    calculations: [],
    uncertainties: [],
    nextAction: 'Review.'
  });
  assert.equal(d.status, 'DOSSIER_BLOCKED');
  assert(d.errors.includes('SOURCE_CHAIN_MISSING'));
}

console.log('GRIDRECOVER dossier: 4/4 PASS');
