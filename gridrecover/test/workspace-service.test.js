'use strict';

const assert = require('assert');
const { CaseStore } = require('../src/case-store');
const {
  sanitizeMetadataPatch, updateCaseMetadata, listCases, buildPortfolio,
  evaluateAndStoreDeadline, evaluateAndStoreSourceDrift, evaluateAndStoreScenarioDelta
} = require('../src/workspace-service');

const store = new CaseStore();
const actor = { customer_id: 'A' };
store.createCase(actor, {
  case_id: 'C1', customer_id: 'A', project_id: 'P1', project_name: 'Zulu', evidence: [],
  finding: { status: 'SUPPORTED_CANDIDATE', value: 1000, currency: 'USD', value_nature: 'CANDIDATE_REPAYMENT' }
});
store.createCase(actor, { case_id: 'C2', customer_id: 'A', project_id: 'P2', project_name: 'Alpha', evidence: [] });

assert.deepEqual(sanitizeMetadataPatch({ project_name: ' Updated ', next_action: ' Review ' }), { project_name: 'Updated', next_action: 'Review' });
assert.throws(() => sanitizeMetadataPatch({ finding: { status: 'RECOVERED' } }), /CASE_PATCH_FIELD_FORBIDDEN/);
assert.throws(() => sanitizeMetadataPatch({ project_name: { bad: true } }), /CASE_PATCH_VALUE_INVALID/);

let r = updateCaseMetadata(store, actor, 'C1', { next_action: 'Verify repayment schedule' }, 1);
assert.equal(r._version, 2);
assert.equal(r.next_action, 'Verify repayment schedule');
assert.throws(() => updateCaseMetadata(store, actor, 'C1', { next_action: 'stale' }, 1), /CASE_VERSION_CONFLICT/);

const listed = listCases(store, actor);
assert.equal(listed[0].case_id, 'C2');
assert.equal(listed[1].case_id, 'C1');

const portfolio = buildPortfolio(store, actor);
assert.equal(portfolio.status, 'VALID');
assert.equal(portfolio.case_count, 2);
assert.equal(portfolio.monetary.CANDIDATE_REPAYMENT.USD, 1000);

r = evaluateAndStoreDeadline(store, actor, 'C1', {
  deadline_id: 'DL-1', source_document_id: 'L1', source_sha256: 'sha256:l1', source_locator: 'Article X', source_authority_verified: true,
  rule_type: 'FIXED_DATE', fixed_date: '2026-09-10', warning_days: 14
}, 2, '2026-09-04T14:00:00Z');
assert.equal(r.deadline.status, 'DUE_SOON');
assert.equal(r._version, 3);

const previous = [{ document_id: 'T1', sha256: 'sha256:old', source_type: 'EFFECTIVE_PROVIDER_TARIFF', effective_version: '110.0.0', effective_date: '2026-02-04', locator: 'Art 11.4.1', authority_status: 'FERC_ACCEPTED' }];
const current = [{ ...previous[0], sha256: 'sha256:new', effective_version: '111.0.0' }];
r = evaluateAndStoreSourceDrift(store, actor, 'C1', { previous_sources: previous, current_sources: current }, 3);
assert.equal(r.source_health, 'DRIFT_DETECTED');
assert.equal(r.finding.status, 'STALE_REVIEW_REQUIRED');
assert.equal(r.finding.stale_reason, 'SOURCE_DRIFT');
assert.equal(r._version, 4);

r = evaluateAndStoreScenarioDelta(store, actor, 'C1', {
  baseline: {
    snapshot_id: 'S1', source_sha256: 'sha256:s1', source_document_id: 'D1', source_locator: 'schedule', source_authority_verified: true,
    lines: [{ component_id: 'SEC', value_type: 'SECURITY_REQUIRED', amount: 1000, currency: 'USD', source_sha256: 'sha256:b', source_locator: 'line1' }]
  },
  current: {
    snapshot_id: 'S2', source_sha256: 'sha256:s2', source_document_id: 'D2', source_locator: 'schedule', source_authority_verified: true,
    lines: [{ component_id: 'SEC', value_type: 'SECURITY_REQUIRED', amount: 600, currency: 'USD', source_sha256: 'sha256:c', source_locator: 'line1' }]
  }
}, 4);
assert.equal(r.last_scenario_delta.status, 'VALID');
assert.equal(r.last_scenario_delta.summary.SECURITY_REQUIRED.USD, -400);
assert.equal(r._version, 5);

assert.throws(() => evaluateAndStoreScenarioDelta(store, actor, 'C1', {}, 4), /CASE_VERSION_CONFLICT/);

console.log('GRIDRECOVER workspace service: 18/18 PASS');
