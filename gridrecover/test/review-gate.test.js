'use strict';

const assert = require('assert');
const {
  STATE, artifactHash, createReviewRecord, submitForReview,
  approveReview, rejectReview, invalidateReview
} = require('../src/review-gate');

const artifact = { finding: { status: 'SUPPORTED_CANDIDATE', candidate_amount: 2000000 }, sources: ['A', 'B'] };
const sourceSet = artifactHash({ sources: ['A', 'B'] });

let r = createReviewRecord({ case_id: 'C1', artifact, prepared_by: 'analyst-1', prepared_at: '2026-09-04T13:50:00Z' });
assert.equal(r.state, STATE.DRAFT);
assert.equal(r.artifact_sha256, artifactHash(artifact));

r = submitForReview(r, { actor_id: 'analyst-1', at: '2026-09-04T13:51:00Z', source_set_sha256: sourceSet });
assert.equal(r.state, STATE.READY_FOR_REVIEW);

assert.throws(() => approveReview(r, {
  reviewer_id: 'analyst-1', at: '2026-09-04T13:52:00Z', artifact, source_set_sha256: sourceSet, source_health: 'STABLE'
}), /INDEPENDENT_REVIEWER_REQUIRED/);

assert.throws(() => approveReview(r, {
  reviewer_id: 'reviewer-2', at: '2026-09-04T13:52:00Z', artifact: { ...artifact, changed: true }, source_set_sha256: sourceSet, source_health: 'STABLE'
}), /ARTIFACT_CHANGED_REVIEW_STALE/);

assert.throws(() => approveReview(r, {
  reviewer_id: 'reviewer-2', at: '2026-09-04T13:52:00Z', artifact, source_set_sha256: '0'.repeat(64), source_health: 'STABLE'
}), /SOURCE_SET_CHANGED_REVIEW_STALE/);

assert.throws(() => approveReview(r, {
  reviewer_id: 'reviewer-2', at: '2026-09-04T13:52:00Z', artifact, source_set_sha256: sourceSet, source_health: 'DRIFT_DETECTED'
}), /SOURCE_HEALTH_NOT_STABLE/);

const approved = approveReview(r, {
  reviewer_id: 'reviewer-2', at: '2026-09-04T13:52:00Z', artifact, source_set_sha256: sourceSet, source_health: 'STABLE'
});
assert.equal(approved.state, STATE.APPROVED_FOR_CUSTOMER_ACTION);
assert.match(approved.approval_sha256, /^[a-f0-9]{64}$/);

const stale = invalidateReview(approved, { reason: 'SOURCE_DRIFT', at: '2026-09-04T13:53:00Z' });
assert.equal(stale.state, STATE.STALE);
assert.equal(stale.approval_sha256, null);
assert.match(stale.decision_reason, /^STALE:/);

let rejectable = createReviewRecord({ case_id: 'C2', artifact, prepared_by: 'analyst-1', prepared_at: '2026-09-04T13:50:00Z' });
rejectable = submitForReview(rejectable, { actor_id: 'analyst-1', at: '2026-09-04T13:51:00Z', source_set_sha256: sourceSet });
const rejected = rejectReview(rejectable, { reviewer_id: 'reviewer-3', at: '2026-09-04T13:52:00Z', reason: 'Repayable basis not sufficiently supported' });
assert.equal(rejected.state, STATE.REJECTED);
assert.equal(rejected.decision_reason, 'Repayable basis not sufficiently supported');

assert.throws(() => submitForReview(createReviewRecord({ case_id: 'C3', artifact, prepared_by: 'a', prepared_at: '2026-09-04T13:50:00Z' }), {
  actor_id: 'b', at: '2026-09-04T13:51:00Z', source_set_sha256: sourceSet
}), /ONLY_PREPARER_CAN_SUBMIT/);

console.log('GRIDRECOVER review gate: 13/13 PASS');
