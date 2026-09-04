'use strict';

const assert = require('assert');
const { REQUIRED_TEST_FAMILIES, STATUS, evaluatePilotReadiness } = require('../src/pilot-readiness');

function valid() {
  const tests = {};
  for (const family of REQUIRED_TEST_FAMILIES) tests[family] = 'success';
  return {
    ci: { head_sha: 'a'.repeat(40), tested_sha: 'a'.repeat(40), conclusion: 'success', run_id: '123' },
    test_families: tests,
    supported_lane: 'MISO_2026_NETWORK_UPGRADE_REPAYMENT',
    auth_mode: 'HASHED_TTL_ROLE_REGISTRY',
    strong_auth_required: true,
    tenant_isolation_verified: true,
    document_vault_encrypted: true,
    durable_mutations_required: true,
    audit_chain_verified: true,
    source_drift_invalidation_enabled: true,
    four_eyes_review_required: true,
    incident_response_ready: true,
    privacy_safe_observability_ready: true,
    backup: { encrypted: true, restore_test_passed: true, last_restore_test_at: '2026-09-04T10:00:00Z', restore_evidence_sha256: 'b'.repeat(64) },
    open_incidents: [],
    customer_pilot: {
      business_identity_verified: true,
      customer_support_route_verified: true,
      privacy_notice_ready: true,
      privacy_notice_sha256: 'c'.repeat(64),
      data_processing_terms_ready: true,
      data_processing_terms_sha256: 'd'.repeat(64),
      pilot_engagement_terms_ready: true,
      pilot_engagement_terms_sha256: 'e'.repeat(64),
      pricing_defined: true,
      external_action_policy: 'CUSTOMER_AUTHORIZED_ONLY'
    }
  };
}

{
  const r = evaluatePilotReadiness(valid(), '2026-09-04T14:00:00Z');
  assert.equal(r.status, STATUS.CUSTOMER_PILOT_READY);
  assert.deepEqual(r.technical_blockers, []);
  assert.deepEqual(r.commercial_blockers, []);
  assert.equal(r.truth_boundary.customer_pilot_ready_is_not_customer_verified, true);
}
{
  const i = valid(); i.customer_pilot.business_identity_verified = false;
  const r = evaluatePilotReadiness(i, '2026-09-04T14:00:00Z');
  assert.equal(r.status, STATUS.TECHNICAL_PILOT_READY);
  assert(r.commercial_blockers.includes('BUSINESS_IDENTITY_NOT_VERIFIED'));
}
{
  const i = valid(); i.ci.tested_sha = 'f'.repeat(40);
  const r = evaluatePilotReadiness(i, '2026-09-04T14:00:00Z');
  assert.equal(r.status, STATUS.NOT_READY);
  assert(r.technical_blockers.includes('CI_NOT_EXACT_HEAD'));
}
{
  const i = valid(); i.test_families.strong_auth = 'failure';
  const r = evaluatePilotReadiness(i, '2026-09-04T14:00:00Z');
  assert.equal(r.status, STATUS.NOT_READY);
  assert(r.technical_blockers.includes('TEST_FAMILY_NOT_GREEN:strong_auth'));
}
{
  const i = valid(); i.open_incidents = [{ severity: 'SEV0', state: 'OPEN' }];
  const r = evaluatePilotReadiness(i, '2026-09-04T14:00:00Z');
  assert.equal(r.status, STATUS.NOT_READY);
  assert(r.technical_blockers.includes('CRITICAL_INCIDENT_OPEN'));
}
{
  const i = valid(); i.backup.last_restore_test_at = '2026-08-20T10:00:00Z';
  const r = evaluatePilotReadiness(i, '2026-09-04T14:00:00Z');
  assert.equal(r.status, STATUS.NOT_READY);
  assert(r.technical_blockers.includes('BACKUP_RESTORE_EVIDENCE_STALE'));
}
{
  const i = valid(); i.customer_pilot.external_action_policy = 'AUTO_SEND';
  const r = evaluatePilotReadiness(i, '2026-09-04T14:00:00Z');
  assert.equal(r.status, STATUS.TECHNICAL_PILOT_READY);
  assert(r.commercial_blockers.includes('EXTERNAL_ACTION_POLICY_NOT_PINNED'));
}
{
  const i = valid(); delete i.customer_pilot.privacy_notice_sha256;
  const r = evaluatePilotReadiness(i, '2026-09-04T14:00:00Z');
  assert.equal(r.status, STATUS.TECHNICAL_PILOT_READY);
  assert(r.commercial_blockers.includes('PRIVACY_NOTICE_NOT_READY'));
}

console.log('GRIDRECOVER pilot readiness: 8/8 PASS');
