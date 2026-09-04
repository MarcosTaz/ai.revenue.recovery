'use strict';

const crypto = require('crypto');

const STATE = Object.freeze({
  DRAFT: 'DRAFT',
  READY_FOR_REVIEW: 'READY_FOR_REVIEW',
  APPROVED_FOR_CUSTOMER_ACTION: 'APPROVED_FOR_CUSTOMER_ACTION',
  REJECTED: 'REJECTED',
  STALE: 'STALE'
});

function stable(value) {
  if (Array.isArray(value)) return `[${value.map(stable).join(',')}]`;
  if (value && typeof value === 'object') return `{${Object.keys(value).sort().map(k => `${JSON.stringify(k)}:${stable(value[k])}`).join(',')}}`;
  return JSON.stringify(value);
}

function artifactHash(value) {
  return crypto.createHash('sha256').update(stable(value), 'utf8').digest('hex');
}

function createReviewRecord({ case_id, artifact, prepared_by, prepared_at }) {
  if (!case_id || !prepared_by || !prepared_at || Number.isNaN(Date.parse(prepared_at)) || !artifact) throw new Error('REVIEW_RECORD_INVALID');
  return {
    version: 1,
    case_id,
    state: STATE.DRAFT,
    artifact_sha256: artifactHash(artifact),
    prepared_by,
    prepared_at,
    submitted_at: null,
    reviewer_id: null,
    reviewed_at: null,
    decision_reason: null,
    source_set_sha256: null,
    approval_sha256: null
  };
}

function submitForReview(record, { actor_id, at, source_set_sha256 }) {
  if (!record || record.state !== STATE.DRAFT) throw new Error('REVIEW_STATE_INVALID');
  if (actor_id !== record.prepared_by) throw new Error('ONLY_PREPARER_CAN_SUBMIT');
  if (!at || Number.isNaN(Date.parse(at))) throw new Error('REVIEW_TIMESTAMP_INVALID');
  if (typeof source_set_sha256 !== 'string' || !/^[a-f0-9]{64}$/i.test(source_set_sha256)) throw new Error('SOURCE_SET_HASH_INVALID');
  return { ...record, state: STATE.READY_FOR_REVIEW, submitted_at: at, source_set_sha256: source_set_sha256.toLowerCase() };
}

function approveReview(record, { reviewer_id, at, artifact, source_set_sha256, source_health }) {
  if (!record || record.state !== STATE.READY_FOR_REVIEW) throw new Error('REVIEW_STATE_INVALID');
  if (!reviewer_id || reviewer_id === record.prepared_by) throw new Error('INDEPENDENT_REVIEWER_REQUIRED');
  if (!at || Number.isNaN(Date.parse(at))) throw new Error('REVIEW_TIMESTAMP_INVALID');
  if (source_health !== 'STABLE') throw new Error('SOURCE_HEALTH_NOT_STABLE');
  const currentArtifactHash = artifactHash(artifact);
  if (currentArtifactHash !== record.artifact_sha256) throw new Error('ARTIFACT_CHANGED_REVIEW_STALE');
  if (typeof source_set_sha256 !== 'string' || source_set_sha256.toLowerCase() !== record.source_set_sha256) throw new Error('SOURCE_SET_CHANGED_REVIEW_STALE');
  const approval_sha256 = artifactHash({ case_id: record.case_id, artifact_sha256: record.artifact_sha256, source_set_sha256: record.source_set_sha256, reviewer_id, at });
  return {
    ...record,
    state: STATE.APPROVED_FOR_CUSTOMER_ACTION,
    reviewer_id,
    reviewed_at: at,
    decision_reason: 'APPROVED_EXACT_ARTIFACT_AND_SOURCE_SET',
    approval_sha256
  };
}

function rejectReview(record, { reviewer_id, at, reason }) {
  if (!record || record.state !== STATE.READY_FOR_REVIEW) throw new Error('REVIEW_STATE_INVALID');
  if (!reviewer_id || reviewer_id === record.prepared_by) throw new Error('INDEPENDENT_REVIEWER_REQUIRED');
  if (!at || Number.isNaN(Date.parse(at)) || !reason) throw new Error('REJECTION_INPUT_INVALID');
  return { ...record, state: STATE.REJECTED, reviewer_id, reviewed_at: at, decision_reason: reason };
}

function invalidateReview(record, { reason, at }) {
  if (!record) throw new Error('REVIEW_RECORD_INVALID');
  if (![STATE.READY_FOR_REVIEW, STATE.APPROVED_FOR_CUSTOMER_ACTION].includes(record.state)) return record;
  if (!reason || !at || Number.isNaN(Date.parse(at))) throw new Error('INVALIDATION_INPUT_INVALID');
  return {
    ...record,
    state: STATE.STALE,
    reviewed_at: null,
    reviewer_id: null,
    approval_sha256: null,
    decision_reason: `STALE:${reason}`,
    invalidated_at: at
  };
}

module.exports = { STATE, stable, artifactHash, createReviewRecord, submitForReview, approveReview, rejectReview, invalidateReview };
