'use strict';

const assert = require('assert');
const { STATUS, evaluateDeadline } = require('../src/deadline-engine');

function fixed(overrides = {}) {
  return {
    deadline_id: 'DL-1', case_id: 'C1',
    source_document_id: 'LGIA-1', source_sha256: 'sha256:lgia', source_locator: 'Article X', source_authority_verified: true,
    rule_type: 'FIXED_DATE', fixed_date: '2026-09-20', warning_days: 14,
    ...overrides
  };
}

assert.equal(evaluateDeadline(fixed(), '2026-09-04T12:00:00Z').status, STATUS.UPCOMING);
assert.equal(evaluateDeadline(fixed(), '2026-09-10T12:00:00Z').status, STATUS.DUE_SOON);
assert.equal(evaluateDeadline(fixed(), '2026-09-20T12:00:00Z').status, STATUS.DUE_TODAY);
assert.equal(evaluateDeadline(fixed(), '2026-09-21T12:00:00Z').status, STATUS.OVERDUE);

{
  const r = evaluateDeadline({
    deadline_id: 'DL-2', case_id: 'C1', source_document_id: 'LGIA-1', source_sha256: 'sha256:lgia', source_locator: 'Article Y', source_authority_verified: true,
    rule_type: 'CALENDAR_DAYS_AFTER_EVENT', trigger_event_date: '2026-09-01', days_after_event: 30,
    trigger_event_source_sha256: 'sha256:event', trigger_event_locator: 'COD notice', trigger_event_verified: true
  }, '2026-09-04T12:00:00Z');
  assert.equal(r.deadline_date, '2026-10-01');
  assert.equal(r.status, STATUS.UPCOMING);
}

{
  const i = fixed(); delete i.source_sha256;
  assert.equal(evaluateDeadline(i).status, STATUS.UNKNOWN);
}
{
  const i = fixed(); i.source_authority_verified = false;
  assert.equal(evaluateDeadline(i).status, STATUS.UNKNOWN);
}
{
  const i = { ...fixed(), closed: true, closed_at: '2026-09-03T10:00:00Z', closed_evidence_sha256: 'sha256:closure' };
  assert.equal(evaluateDeadline(i).status, STATUS.CLOSED);
}
{
  const i = { ...fixed(), closed: true, closed_at: '2026-09-03T10:00:00Z' };
  assert.equal(evaluateDeadline(i).status, STATUS.UNKNOWN);
}
{
  const i = fixed({ rule_type: 'BUSINESS_DAYS_AFTER_EVENT' });
  const r = evaluateDeadline(i);
  assert.equal(r.status, STATUS.UNKNOWN);
  assert(r.reasons.includes('DEADLINE_RULE_NOT_SUPPORTED'));
}

console.log('GRIDRECOVER deadline engine: 10/10 PASS');
