'use strict';

const ACTION = Object.freeze({ RETAIN: 'RETAIN', DELETE_DUE: 'DELETE_DUE', LEGAL_HOLD: 'LEGAL_HOLD', UNKNOWN: 'UNKNOWN' });

function nonEmpty(v) { return typeof v === 'string' && v.trim().length > 0; }
function validDate(v) { return nonEmpty(v) && !Number.isNaN(Date.parse(v)); }
function isoDay(v) { return new Date(v).toISOString().slice(0, 10); }
function addDays(date, days) {
  const d = new Date(`${isoDay(date)}T00:00:00.000Z`);
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}

function evaluateRetention({ record, policy, now }) {
  const reasons = [];
  if (!record || !nonEmpty(record.record_id) || !nonEmpty(record.customer_id) || !nonEmpty(record.record_type)) reasons.push('RECORD_IDENTITY_INVALID');
  if (!policy || !nonEmpty(policy.policy_id) || !nonEmpty(policy.policy_sha256) || policy.approved !== true) reasons.push('RETENTION_POLICY_NOT_VERIFIED');
  if (!validDate(now)) reasons.push('NOW_INVALID');
  if (reasons.length) return { action: ACTION.UNKNOWN, reasons };

  if (record.legal_hold === true) {
    if (!nonEmpty(record.legal_hold_evidence_sha256) || !validDate(record.legal_hold_at)) return { action: ACTION.UNKNOWN, reasons: ['LEGAL_HOLD_EVIDENCE_INCOMPLETE'] };
    return { action: ACTION.LEGAL_HOLD, delete_on: null, reasons: ['VERIFIED_LEGAL_HOLD'] };
  }

  const rule = policy.rules && policy.rules[record.record_type];
  if (!rule || !Number.isInteger(rule.days_after_trigger) || rule.days_after_trigger < 0 || !['ENGAGEMENT_END', 'CASE_CLOSED', 'DOCUMENT_SUPERSEDED'].includes(rule.trigger)) {
    return { action: ACTION.UNKNOWN, reasons: ['RETENTION_RULE_MISSING'] };
  }
  const triggerDate = record.triggers && record.triggers[rule.trigger];
  const triggerEvidence = record.trigger_evidence && record.trigger_evidence[rule.trigger];
  if (!validDate(triggerDate) || !nonEmpty(triggerEvidence)) return { action: ACTION.RETAIN, delete_on: null, reasons: ['RETENTION_TRIGGER_NOT_YET_VERIFIED'] };

  const deleteOn = addDays(triggerDate, rule.days_after_trigger);
  const due = Date.parse(`${isoDay(now)}T00:00:00Z`) >= Date.parse(`${deleteOn}T00:00:00Z`);
  return {
    action: due ? ACTION.DELETE_DUE : ACTION.RETAIN,
    delete_on: deleteOn,
    policy_id: policy.policy_id,
    policy_sha256: policy.policy_sha256,
    reasons: [due ? 'VERIFIED_RETENTION_PERIOD_EXPIRED' : 'RETENTION_PERIOD_ACTIVE']
  };
}

function authorizeDeletion({ evaluation, approval }) {
  if (!evaluation || evaluation.action !== ACTION.DELETE_DUE) throw new Error('DELETION_NOT_DUE');
  if (!approval || approval.approved !== true || !nonEmpty(approval.approved_by) || !validDate(approval.approved_at) || !nonEmpty(approval.approval_evidence_sha256)) {
    throw new Error('DELETION_APPROVAL_INCOMPLETE');
  }
  if (approval.requested_by === approval.approved_by) throw new Error('DELETION_INDEPENDENT_APPROVAL_REQUIRED');
  return {
    authorized: true,
    delete_on: evaluation.delete_on,
    approved_by: approval.approved_by,
    approved_at: approval.approved_at,
    approval_evidence_sha256: approval.approval_evidence_sha256
  };
}

function buildDeletionReceipt({ record_id, customer_id, source_sha256, vault_deleted, metadata_tombstoned, at, actor_id, authorization }) {
  if (!nonEmpty(record_id) || !nonEmpty(customer_id) || !nonEmpty(source_sha256) || vault_deleted !== true || metadata_tombstoned !== true || !validDate(at) || !nonEmpty(actor_id) || !authorization?.authorized) {
    throw new Error('DELETION_RECEIPT_INCOMPLETE');
  }
  return {
    record_id, customer_id, source_sha256,
    vault_deleted: true,
    metadata_tombstoned: true,
    deleted_at: at,
    actor_id,
    authorization_evidence_sha256: authorization.approval_evidence_sha256,
    content_retained: false
  };
}

module.exports = { ACTION, evaluateRetention, authorizeDeletion, buildDeletionReceipt, addDays };
