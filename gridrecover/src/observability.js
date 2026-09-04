'use strict';

const METRICS = Object.freeze({
  HTTP_REQUEST: 'gridrecover_http_request_total',
  HTTP_ERROR: 'gridrecover_http_error_total',
  MUTATION_ROLLBACK: 'gridrecover_mutation_rollback_total',
  PERSISTENCE_FAILURE: 'gridrecover_persistence_failure_total',
  AUTH_FAILURE: 'gridrecover_auth_failure_total',
  DOCUMENT_INGEST: 'gridrecover_document_ingest_total',
  SOURCE_DRIFT: 'gridrecover_source_drift_total',
  DEADLINE_EXCEPTION: 'gridrecover_deadline_exception_total',
  INCIDENT_OPEN: 'gridrecover_incident_open_total'
});

const ALLOWED_LABELS = Object.freeze({
  [METRICS.HTTP_REQUEST]: new Set(['method', 'route_class', 'status_class']),
  [METRICS.HTTP_ERROR]: new Set(['route_class', 'error_class']),
  [METRICS.MUTATION_ROLLBACK]: new Set(['mutation_class', 'reason_class']),
  [METRICS.PERSISTENCE_FAILURE]: new Set(['operation_class']),
  [METRICS.AUTH_FAILURE]: new Set(['reason_class']),
  [METRICS.DOCUMENT_INGEST]: new Set(['document_type', 'extension', 'result']),
  [METRICS.SOURCE_DRIFT]: new Set(['source_type', 'change_class']),
  [METRICS.DEADLINE_EXCEPTION]: new Set(['deadline_status']),
  [METRICS.INCIDENT_OPEN]: new Set(['severity', 'incident_type'])
});

const FORBIDDEN_LABEL_FRAGMENTS = [
  'token', 'secret', 'password', 'authorization', 'email', 'name', 'document_id', 'case_id', 'customer_id',
  'user_id', 'payment', 'account', 'reference', 'sha', 'hash', 'locator', 'path', 'filename', 'body', 'payload'
];

function safeScalar(value) {
  return typeof value === 'string' && value.length > 0 && value.length <= 80 && /^[A-Za-z0-9_.:/-]+$/.test(value);
}

class SafeMetrics {
  constructor() { this.counters = new Map(); }

  increment(metric, labels = {}, by = 1) {
    if (!Object.values(METRICS).includes(metric)) throw new Error('METRIC_NOT_ALLOWED');
    if (!Number.isInteger(by) || by <= 0) throw new Error('METRIC_INCREMENT_INVALID');
    if (!labels || typeof labels !== 'object' || Array.isArray(labels)) throw new Error('METRIC_LABELS_INVALID');
    const allowed = ALLOWED_LABELS[metric];
    const normalized = {};
    for (const [key, value] of Object.entries(labels)) {
      const lower = key.toLowerCase();
      if (FORBIDDEN_LABEL_FRAGMENTS.some(fragment => lower.includes(fragment))) throw new Error('METRIC_SENSITIVE_LABEL_FORBIDDEN');
      if (!allowed.has(key)) throw new Error('METRIC_LABEL_NOT_ALLOWED');
      if (!safeScalar(value)) throw new Error('METRIC_LABEL_VALUE_INVALID');
      normalized[key] = value;
    }
    const key = `${metric}|${Object.keys(normalized).sort().map(k => `${k}=${normalized[k]}`).join(',')}`;
    this.counters.set(key, (this.counters.get(key) || 0) + by);
    return this.counters.get(key);
  }

  snapshot() {
    return [...this.counters.entries()].map(([key, value]) => ({ key, value }));
  }
}

function buildOperationalHealth({ audit_chain_valid, persistence_configured, auth_mode, vault_configured, open_incidents = [], last_backup_verified_at = null, now }) {
  const blockers = [];
  if (audit_chain_valid !== true) blockers.push('AUDIT_CHAIN_INVALID');
  if (persistence_configured !== true) blockers.push('PERSISTENCE_NOT_CONFIGURED');
  if (auth_mode !== 'HASHED_TTL_ROLE_REGISTRY') blockers.push('STRONG_AUTH_NOT_CONFIGURED');
  if (vault_configured !== true) blockers.push('DOCUMENT_VAULT_NOT_CONFIGURED');
  if (!now || Number.isNaN(Date.parse(now))) blockers.push('HEALTH_NOW_INVALID');

  const critical = Array.isArray(open_incidents) && open_incidents.some(i => ['SEV0', 'SEV1'].includes(i.severity) && i.state !== 'RESOLVED');
  if (critical) blockers.push('CRITICAL_INCIDENT_OPEN');

  let backup_age_hours = null;
  if (!last_backup_verified_at || Number.isNaN(Date.parse(last_backup_verified_at))) blockers.push('VERIFIED_BACKUP_MISSING');
  else if (now && !Number.isNaN(Date.parse(now))) {
    backup_age_hours = Math.floor((Date.parse(now) - Date.parse(last_backup_verified_at)) / 3600000);
    if (backup_age_hours < 0) blockers.push('BACKUP_TIMESTAMP_IN_FUTURE');
    else if (backup_age_hours > 24) blockers.push('VERIFIED_BACKUP_STALE');
  }

  return {
    status: blockers.length ? 'DEGRADED' : 'HEALTHY',
    blockers,
    backup_age_hours,
    open_incident_count: Array.isArray(open_incidents) ? open_incidents.filter(i => i.state !== 'RESOLVED').length : null,
    production_ready: false
  };
}

module.exports = { METRICS, ALLOWED_LABELS, FORBIDDEN_LABEL_FRAGMENTS, SafeMetrics, buildOperationalHealth };
