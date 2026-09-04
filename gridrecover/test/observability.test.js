'use strict';

const assert = require('assert');
const { METRICS, SafeMetrics, buildOperationalHealth } = require('../src/observability');

const metrics = new SafeMetrics();
assert.equal(metrics.increment(METRICS.HTTP_REQUEST, { method: 'POST', route_class: 'cases', status_class: '2xx' }), 1);
assert.equal(metrics.increment(METRICS.HTTP_REQUEST, { method: 'POST', route_class: 'cases', status_class: '2xx' }), 2);
assert.equal(metrics.increment(METRICS.AUTH_FAILURE, { reason_class: 'expired' }), 1);
assert.equal(metrics.snapshot().length, 2);

assert.throws(() => metrics.increment('custom_secret_metric', {}), /METRIC_NOT_ALLOWED/);
assert.throws(() => metrics.increment(METRICS.HTTP_REQUEST, { customer_id: 'A' }), /METRIC_SENSITIVE_LABEL_FORBIDDEN/);
assert.throws(() => metrics.increment(METRICS.HTTP_REQUEST, { route: 'cases' }), /METRIC_LABEL_NOT_ALLOWED/);
assert.throws(() => metrics.increment(METRICS.DOCUMENT_INGEST, { filename: 'contract.pdf' }), /METRIC_SENSITIVE_LABEL_FORBIDDEN/);
assert.throws(() => metrics.increment(METRICS.HTTP_REQUEST, { method: 'POST raw body' }), /METRIC_LABEL_VALUE_INVALID/);
assert.throws(() => metrics.increment(METRICS.HTTP_REQUEST, {}, 0), /METRIC_INCREMENT_INVALID/);

{
  const h = buildOperationalHealth({
    audit_chain_valid: true,
    persistence_configured: true,
    auth_mode: 'HASHED_TTL_ROLE_REGISTRY',
    vault_configured: true,
    open_incidents: [],
    last_backup_verified_at: '2026-09-04T08:00:00Z',
    now: '2026-09-04T14:00:00Z'
  });
  assert.equal(h.status, 'HEALTHY');
  assert.equal(h.backup_age_hours, 6);
  assert.equal(h.production_ready, false);
}

{
  const h = buildOperationalHealth({
    audit_chain_valid: true,
    persistence_configured: true,
    auth_mode: 'HASHED_TTL_ROLE_REGISTRY',
    vault_configured: true,
    open_incidents: [{ severity: 'SEV0', state: 'OPEN' }],
    last_backup_verified_at: '2026-09-03T10:00:00Z',
    now: '2026-09-04T14:00:00Z'
  });
  assert.equal(h.status, 'DEGRADED');
  assert(h.blockers.includes('CRITICAL_INCIDENT_OPEN'));
  assert(h.blockers.includes('VERIFIED_BACKUP_STALE'));
}

{
  const h = buildOperationalHealth({
    audit_chain_valid: false,
    persistence_configured: false,
    auth_mode: 'DEV_STATIC_TOKEN_MAP',
    vault_configured: false,
    open_incidents: [],
    last_backup_verified_at: null,
    now: '2026-09-04T14:00:00Z'
  });
  assert.equal(h.status, 'DEGRADED');
  assert(h.blockers.includes('AUDIT_CHAIN_INVALID'));
  assert(h.blockers.includes('PERSISTENCE_NOT_CONFIGURED'));
  assert(h.blockers.includes('STRONG_AUTH_NOT_CONFIGURED'));
  assert(h.blockers.includes('DOCUMENT_VAULT_NOT_CONFIGURED'));
  assert(h.blockers.includes('VERIFIED_BACKUP_MISSING'));
}

console.log('GRIDRECOVER privacy-safe observability: 18/18 PASS');
