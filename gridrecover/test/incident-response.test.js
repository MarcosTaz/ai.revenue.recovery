'use strict';

const assert = require('assert');
const {
  STATE, createIncident, acknowledgeIncident, containIncident,
  recordCustomerNotification, resolveIncident, incidentSla
} = require('../src/incident-response');

let i = createIncident({
  incident_id: 'INC-001', type: 'DATA_INTEGRITY', severity: 'SEV1',
  detected_at: '2026-09-04T14:00:00Z', detected_by: 'monitor:ci',
  summary: 'Evidence-chain mismatch detected', customer_id: 'A', case_id: 'C1',
  safe_details: { detector: 'hash-mismatch', affected_component: 'document-vault' }
});
assert.equal(i.state, STATE.OPEN);
assert.equal(incidentSla(i, '2026-09-04T14:30:00Z').acknowledge_breached, false);
assert.equal(incidentSla(i, '2026-09-04T15:01:00Z').acknowledge_breached, true);

i = acknowledgeIncident(i, { at: '2026-09-04T14:20:00Z', actor_id: 'user:ops-1' });
assert.equal(i.state, STATE.ACKNOWLEDGED);
assert.equal(incidentSla(i, '2026-09-04T18:30:00Z').acknowledge_breached, false);
assert.equal(incidentSla(i, '2026-09-04T18:30:00Z').contain_breached, true);

i = containIncident(i, {
  at: '2026-09-04T15:00:00Z', actor_id: 'user:ops-1', evidence_sha256: 'a'.repeat(64),
  action: 'Disabled affected document path and preserved evidence', customer_impact_stopped: true
});
assert.equal(i.state, STATE.CONTAINED);

assert.throws(() => resolveIncident(i, {
  at: '2026-09-04T16:00:00Z', actor_id: 'user:ops-2', root_cause: 'Fixture corruption', corrective_action: 'Corrected fixture',
  resolution_evidence_sha256: 'b'.repeat(64), regression_test_id: 'document-ingest', regression_passed: true
}), /INCIDENT_NOTIFICATION_DECISION_REQUIRED/);

i = recordCustomerNotification(i, {
  required: false,
  decision_basis: 'Synthetic CI-only incident; no customer data or customer service impact.'
});

i = resolveIncident(i, {
  at: '2026-09-04T16:00:00Z', actor_id: 'user:ops-2', root_cause: 'Fixture corruption', corrective_action: 'Restored source-valid fixture and isolated CI test family',
  resolution_evidence_sha256: 'b'.repeat(64), regression_test_id: 'document-ingest', regression_passed: true
});
assert.equal(i.state, STATE.RESOLVED);
assert.equal(incidentSla(i, '2026-09-04T17:00:00Z').status, 'CLOSED');

assert.throws(() => createIncident({
  incident_id: 'INC-X', type: 'SECURITY_OR_TENANT_ISOLATION', severity: 'SEV0',
  detected_at: '2026-09-04T14:00:00Z', detected_by: 'x', summary: 'x',
  safe_details: { token: 'secret-value' }
}), /INCIDENT_SENSITIVE_DETAIL_FORBIDDEN/);

assert.throws(() => containIncident(createIncident({
  incident_id: 'INC-Y', type: 'SERVICE_AVAILABILITY', severity: 'SEV2', detected_at: '2026-09-04T14:00:00Z', detected_by: 'x', summary: 'x'
}), {
  at: '2026-09-04T14:20:00Z', actor_id: 'u', evidence_sha256: 'c'.repeat(64), action: 'Restarted', customer_impact_stopped: false
}), /INCIDENT_CONTAINMENT_INVALID/);

let z = createIncident({
  incident_id: 'INC-Z', type: 'AUTHENTICATION_OR_AUTHORIZATION', severity: 'SEV0', detected_at: '2026-09-04T14:00:00Z', detected_by: 'x', summary: 'x'
});
z = containIncident(z, { at: '2026-09-04T14:10:00Z', actor_id: 'u', evidence_sha256: 'd'.repeat(64), action: 'Revoked credentials', customer_impact_stopped: true });
z = recordCustomerNotification(z, { required: true, at: '2026-09-04T14:12:00Z', evidence_sha256: 'e'.repeat(64), channel: 'approved incident contact', decision_basis: 'Customer impact confirmed' });
assert.throws(() => resolveIncident(z, {
  at: '2026-09-04T14:30:00Z', actor_id: 'u2', root_cause: 'bad auth', corrective_action: 'fixed auth', resolution_evidence_sha256: 'f'.repeat(64), regression_test_id: 'auth', regression_passed: false
}), /INCIDENT_REGRESSION_NOT_GREEN/);

assert.throws(() => acknowledgeIncident(createIncident({
  incident_id: 'INC-T', type: 'DATA_INTEGRITY', severity: 'SEV2', detected_at: '2026-09-04T14:00:00Z', detected_by: 'x', summary: 'x'
}), { at: '2026-09-04T13:59:00Z', actor_id: 'u' }), /INCIDENT_TIME_ORDER_INVALID/);

console.log('GRIDRECOVER incident response: 15/15 PASS');
