'use strict';

const assert = require('assert');
const { STATUS, evaluateSourceDrift, evaluateDependencySet } = require('../src/source-drift-sentinel');

function source(overrides = {}) {
  return {
    document_id: 'TARIFF-110',
    sha256: 'sha256:aaa',
    source_type: 'EFFECTIVE_PROVIDER_TARIFF',
    effective_version: '110.0.0',
    effective_date: '2026-02-04',
    locator: 'Article 11.4.1',
    authority_status: 'FERC_ACCEPTED',
    ...overrides
  };
}

assert.equal(evaluateSourceDrift(source(), source()).status, STATUS.STABLE);

{
  const r = evaluateSourceDrift(source(), source({ sha256: 'sha256:bbb' }));
  assert.equal(r.status, STATUS.DRIFT_DETECTED);
  assert.equal(r.invalidate_findings, true);
  assert(r.changes.includes('SOURCE_BYTES_CHANGED'));
}
{
  const r = evaluateSourceDrift(source(), source({ effective_version: '111.0.0' }));
  assert.equal(r.status, STATUS.DRIFT_DETECTED);
  assert(r.changes.includes('EFFECTIVE_VERSION_CHANGED'));
}
{
  const r = evaluateSourceDrift(source(), source({ authority_status: 'SUPERSEDED' }));
  assert.equal(r.status, STATUS.DRIFT_DETECTED);
  assert(r.changes.includes('AUTHORITY_STATUS_CHANGED'));
}
{
  const r = evaluateSourceDrift(source(), null);
  assert.equal(r.status, STATUS.UNKNOWN);
  assert.equal(r.invalidate_findings, true);
}
{
  const previous = [source(), source({ document_id: 'LGIA-1', sha256: 'sha256:lgia', source_type: 'PROJECT_LGIA', effective_version: 'EXECUTED-1' })];
  const current = previous.map(x => ({ ...x }));
  assert.equal(evaluateDependencySet(previous, current).status, STATUS.STABLE);
}
{
  const previous = [source()];
  const current = [source({ sha256: 'sha256:changed' })];
  assert.equal(evaluateDependencySet(previous, current).invalidate_findings, true);
}
{
  const previous = [source()];
  const current = [source(), source({ document_id: 'AMEND-1', sha256: 'sha256:amend', source_type: 'PROJECT_AMENDMENT', effective_version: 'A1' })];
  const r = evaluateDependencySet(previous, current);
  assert.equal(r.status, STATUS.DRIFT_DETECTED);
  assert(r.results.some(x => x.changes && x.changes.includes('NEW_DEPENDENCY_SOURCE')));
}

console.log('GRIDRECOVER source drift sentinel: 8/8 PASS');
