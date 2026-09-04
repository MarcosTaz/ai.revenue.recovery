'use strict';

const assert = require('assert');
const { STATUS, evaluateScenarioDelta } = require('../src/scenario-delta');

function snapshot(id, sha, lines) {
  return {
    snapshot_id: id,
    source_sha256: sha,
    source_document_id: `${id}-DOC`,
    source_locator: 'allocation schedule',
    source_authority_verified: true,
    lines
  };
}

function line(component_id, value_type, amount, currency = 'USD', suffix = '') {
  return { component_id, value_type, amount, currency, source_sha256: `sha256:${component_id}${suffix}`, source_locator: `line:${component_id}` };
}

{
  const r = evaluateScenarioDelta({
    case_id: 'C1',
    baseline: snapshot('S1', 'sha256:s1', [
      line('NU-1', 'NETWORK_UPGRADE_ASSIGNMENT', 5000000),
      line('SEC-1', 'SECURITY_REQUIRED', 5000000),
      line('REP-1', 'REPAYABLE_BASIS', 3500000)
    ]),
    current: snapshot('S2', 'sha256:s2', [
      line('NU-1', 'NETWORK_UPGRADE_ASSIGNMENT', 3500000, 'USD', 'b'),
      line('SEC-1', 'SECURITY_REQUIRED', 3500000, 'USD', 'b'),
      line('REP-1', 'REPAYABLE_BASIS', 3000000, 'USD', 'b')
    ])
  });
  assert.equal(r.status, STATUS.VALID);
  assert.equal(r.summary.NETWORK_UPGRADE_ASSIGNMENT.USD, -1500000);
  assert.equal(r.summary.SECURITY_REQUIRED.USD, -1500000);
  assert.equal(r.summary.REPAYABLE_BASIS.USD, -500000);
  assert.equal(r.interpretation.negative_security_required_delta_means_less_security_required_not_cash_recovery, true);
}

{
  const r = evaluateScenarioDelta({
    case_id: 'C2',
    baseline: snapshot('S1', 'sha256:s1', [line('NU-1', 'NETWORK_UPGRADE_ASSIGNMENT', 100, 'USD')]),
    current: snapshot('S2', 'sha256:s2', [line('NU-2', 'NETWORK_UPGRADE_ASSIGNMENT', 50, 'USD')])
  });
  assert.equal(r.lines.find(x => x.component_id === 'NU-1').change_type, 'REMOVED');
  assert.equal(r.lines.find(x => x.component_id === 'NU-2').change_type, 'ADDED');
  assert.equal(r.summary.NETWORK_UPGRADE_ASSIGNMENT.USD, -50);
}

{
  const r = evaluateScenarioDelta({
    case_id: 'C3',
    baseline: snapshot('S1', 'sha256:s1', [line('SEC', 'SECURITY_REQUIRED', 100, 'USD')]),
    current: snapshot('S2', 'sha256:s2', [line('SEC', 'SECURITY_REQUIRED', 80, 'EUR')])
  });
  assert.equal(r.status, STATUS.VALID);
  assert.equal(r.summary.SECURITY_REQUIRED.USD, -100);
  assert.equal(r.summary.SECURITY_REQUIRED.EUR, 80);
}

{
  const bad = snapshot('S1', 'sha256:s1', [line('X', 'UNSUPPORTED', 1)]);
  const r = evaluateScenarioDelta({ case_id: 'C4', baseline: bad, current: snapshot('S2', 'sha256:s2', []) });
  assert.equal(r.status, STATUS.UNKNOWN);
  assert(r.reasons.some(x => x.includes('VALUE_TYPE_UNSUPPORTED')));
}

{
  const bad = snapshot('S1', 'sha256:s1', [line('X', 'DEPOSIT', -1)]);
  const r = evaluateScenarioDelta({ case_id: 'C5', baseline: bad, current: snapshot('S2', 'sha256:s2', []) });
  assert.equal(r.status, STATUS.UNKNOWN);
}

{
  const dup = snapshot('S1', 'sha256:s1', [line('X', 'DEPOSIT', 1), line('X', 'DEPOSIT', 2)]);
  const r = evaluateScenarioDelta({ case_id: 'C6', baseline: dup, current: snapshot('S2', 'sha256:s2', []) });
  assert.equal(r.status, STATUS.UNKNOWN);
  assert(r.reasons.some(x => x.includes('DUPLICATE_COMPONENT')));
}

console.log('GRIDRECOVER scenario delta: 6/6 PASS');
