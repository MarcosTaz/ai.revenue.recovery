'use strict';

const SEVERITY = Object.freeze({ SEV0: 0, SEV1: 1, SEV2: 2, SEV3: 3 });
const STATE = Object.freeze({ OPEN: 'OPEN', ACKNOWLEDGED: 'ACKNOWLEDGED', CONTAINED: 'CONTAINED', RESOLVED: 'RESOLVED' });
const INCIDENT_TYPES = new Set([
  'SECURITY_OR_TENANT_ISOLATION',
  'DATA_INTEGRITY',
  'DURABILITY_OR_BACKUP',
  'AUTHENTICATION_OR_AUTHORIZATION',
  'SOURCE_DRIFT_OR_RULE_AUTHORITY',
  'PAYMENT_OR_BILLING_INTEGRITY',
  'SERVICE_AVAILABILITY'
]);
const FORBIDDEN_DETAIL_KEYS = new Set(['password', 'token', 'authorization', 'secret', 'private_key', 'raw_document', 'document_bytes', 'payment_account']);

function nonEmpty(v) { return typeof v === 'string' && v.trim().length > 0; }
function validDate(v) { return nonEmpty(v) && !Number.isNaN(Date.parse(v)); }

function validateSafeDetails(value, path = '') {
  if (value == null || typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') return;
  if (Array.isArray(value)) {
    value.forEach((item, i) => validateSafeDetails(item, `${path}[${i}]`));
    return;
  }
  if (typeof value !== 'object') throw new Error('INCIDENT_DETAILS_INVALID');
  for (const [key, child] of Object.entries(value)) {
    if (FORBIDDEN_DETAIL_KEYS.has(key.toLowerCase())) throw new Error('INCIDENT_SENSITIVE_DETAIL_FORBIDDEN');
    validateSafeDetails(child, path ? `${path}.${key}` : key);
  }
}

function createIncident({ incident_id, type, severity, detected_at, detected_by, summary, customer_id = null, case_id = null, safe_details = {} }) {
  if (!nonEmpty(incident_id) || !INCIDENT_TYPES.has(type) || !Object.prototype.hasOwnProperty.call(SEVERITY, severity)) throw new Error('INCIDENT_IDENTITY_INVALID');
  if (!validDate(detected_at) || !nonEmpty(detected_by) || !nonEmpty(summary)) throw new Error('INCIDENT_INPUT_INVALID');
  validateSafeDetails(safe_details);
  return {
    version: 1,
    incident_id,
    type,
    severity,
    state: STATE.OPEN,
    detected_at,
    detected_by,
    summary,
    customer_id,
    case_id,
    safe_details: JSON.parse(JSON.stringify(safe_details)),
    acknowledged_at: null,
    acknowledged_by: null,
    containment: null,
    resolution: null,
    customer_notification: null
  };
}

function acknowledgeIncident(record, { at, actor_id }) {
  if (!record || record.state !== STATE.OPEN) throw new Error('INCIDENT_STATE_INVALID');
  if (!validDate(at) || !nonEmpty(actor_id)) throw new Error('INCIDENT_ACK_INVALID');
  if (Date.parse(at) < Date.parse(record.detected_at)) throw new Error('INCIDENT_TIME_ORDER_INVALID');
  return { ...record, state: STATE.ACKNOWLEDGED, acknowledged_at: at, acknowledged_by: actor_id };
}

function containIncident(record, { at, actor_id, evidence_sha256, action, customer_impact_stopped }) {
  if (!record || ![STATE.OPEN, STATE.ACKNOWLEDGED].includes(record.state)) throw new Error('INCIDENT_STATE_INVALID');
  if (!validDate(at) || !nonEmpty(actor_id) || !nonEmpty(evidence_sha256) || !nonEmpty(action) || customer_impact_stopped !== true) throw new Error('INCIDENT_CONTAINMENT_INVALID');
  if (Date.parse(at) < Date.parse(record.detected_at)) throw new Error('INCIDENT_TIME_ORDER_INVALID');
  return {
    ...record,
    state: STATE.CONTAINED,
    containment: { at, actor_id, evidence_sha256, action, customer_impact_stopped: true }
  };
}

function recordCustomerNotification(record, { required, at = null, evidence_sha256 = null, channel = null, decision_basis }) {
  if (!record || !nonEmpty(decision_basis) || typeof required !== 'boolean') throw new Error('INCIDENT_NOTIFICATION_DECISION_INVALID');
  if (required && (!validDate(at) || !nonEmpty(evidence_sha256) || !nonEmpty(channel))) throw new Error('INCIDENT_NOTIFICATION_EVIDENCE_REQUIRED');
  return {
    ...record,
    customer_notification: { required, at, evidence_sha256, channel, decision_basis }
  };
}

function resolveIncident(record, { at, actor_id, root_cause, corrective_action, resolution_evidence_sha256, regression_test_id, regression_passed }) {
  if (!record || record.state !== STATE.CONTAINED) throw new Error('INCIDENT_STATE_INVALID');
  if (!validDate(at) || !nonEmpty(actor_id) || !nonEmpty(root_cause) || !nonEmpty(corrective_action) || !nonEmpty(resolution_evidence_sha256) || !nonEmpty(regression_test_id)) throw new Error('INCIDENT_RESOLUTION_INVALID');
  if (regression_passed !== true) throw new Error('INCIDENT_REGRESSION_NOT_GREEN');
  if (!record.customer_notification) throw new Error('INCIDENT_NOTIFICATION_DECISION_REQUIRED');
  if (Date.parse(at) < Date.parse(record.containment.at)) throw new Error('INCIDENT_TIME_ORDER_INVALID');
  return {
    ...record,
    state: STATE.RESOLVED,
    resolution: { at, actor_id, root_cause, corrective_action, resolution_evidence_sha256, regression_test_id, regression_passed: true }
  };
}

function incidentSla(record, now) {
  if (!record || !validDate(record.detected_at) || !validDate(now)) return { status: 'UNKNOWN' };
  const targets = {
    SEV0: { acknowledge_minutes: 15, contain_minutes: 60 },
    SEV1: { acknowledge_minutes: 60, contain_minutes: 240 },
    SEV2: { acknowledge_minutes: 240, contain_minutes: 1440 },
    SEV3: { acknowledge_minutes: 1440, contain_minutes: 4320 }
  }[record.severity];
  if (!targets) return { status: 'UNKNOWN' };
  const elapsed = Math.max(0, Math.floor((Date.parse(now) - Date.parse(record.detected_at)) / 60000));
  return {
    status: record.state === STATE.RESOLVED ? 'CLOSED' : 'ACTIVE',
    elapsed_minutes: elapsed,
    acknowledge_target_minutes: targets.acknowledge_minutes,
    contain_target_minutes: targets.contain_minutes,
    acknowledge_breached: !record.acknowledged_at && elapsed > targets.acknowledge_minutes,
    contain_breached: !record.containment && elapsed > targets.contain_minutes
  };
}

module.exports = {
  SEVERITY, STATE, INCIDENT_TYPES, FORBIDDEN_DETAIL_KEYS,
  createIncident, acknowledgeIncident, containIncident, recordCustomerNotification, resolveIncident, incidentSla, validateSafeDetails
};
