'use strict';

const assert = require('assert');
const { ACTION, evaluateRetention, authorizeDeletion, buildDeletionReceipt } = require('../src/data-lifecycle');

const policy = {
  policy_id: 'RET-1', policy_sha256: 'a'.repeat(64), approved: true,
  rules: {
    SOURCE_DOCUMENT: { trigger: 'ENGAGEMENT_END', days_after_trigger: 90 },
    GENERATED_DOSSIER: { trigger: 'CASE_CLOSED', days_after_trigger: 365 }
  }
};
const record = {
  record_id: 'DOC-1', customer_id: 'A', record_type: 'SOURCE_DOCUMENT', legal_hold: false,
  triggers: { ENGAGEMENT_END: '2026-06-01' },
  trigger_evidence: { ENGAGEMENT_END: 'b'.repeat(64) }
};

let r = evaluateRetention({ record, policy, now: '2026-08-01T10:00:00Z' });
assert.equal(r.action, ACTION.RETAIN);
assert.equal(r.delete_on, '2026-08-30');

r = evaluateRetention({ record, policy, now: '2026-08-30T10:00:00Z' });
assert.equal(r.action, ACTION.DELETE_DUE);

const authorization = authorizeDeletion({
  evaluation: r,
  approval: { approved: true, requested_by: 'analyst-1', approved_by: 'admin-2', approved_at: '2026-08-30T11:00:00Z', approval_evidence_sha256: 'c'.repeat(64) }
});
assert.equal(authorization.authorized, true);

const receipt = buildDeletionReceipt({
  record_id: 'DOC-1', customer_id: 'A', source_sha256: 'd'.repeat(64), vault_deleted: true, metadata_tombstoned: true,
  at: '2026-08-30T11:05:00Z', actor_id: 'user:admin-2', authorization
});
assert.equal(receipt.content_retained, false);
assert.equal(receipt.vault_deleted, true);

{
  const hold = { ...record, legal_hold: true, legal_hold_at: '2026-08-01T10:00:00Z', legal_hold_evidence_sha256: 'e'.repeat(64) };
  assert.equal(evaluateRetention({ record: hold, policy, now: '2027-01-01T00:00:00Z' }).action, ACTION.LEGAL_HOLD);
}
{
  const hold = { ...record, legal_hold: true };
  assert.equal(evaluateRetention({ record: hold, policy, now: '2027-01-01T00:00:00Z' }).action, ACTION.UNKNOWN);
}
{
  const noTrigger = { ...record, triggers: {}, trigger_evidence: {} };
  const x = evaluateRetention({ record: noTrigger, policy, now: '2027-01-01T00:00:00Z' });
  assert.equal(x.action, ACTION.RETAIN);
  assert(x.reasons.includes('RETENTION_TRIGGER_NOT_YET_VERIFIED'));
}
{
  const badPolicy = { ...policy, approved: false };
  assert.equal(evaluateRetention({ record, policy: badPolicy, now: '2026-08-30' }).action, ACTION.UNKNOWN);
}
{
  assert.throws(() => authorizeDeletion({ evaluation: { action: ACTION.RETAIN } }), /DELETION_NOT_DUE/);
  assert.throws(() => authorizeDeletion({ evaluation: r, approval: { approved: true, requested_by: 'u', approved_by: 'u', approved_at: '2026-08-30', approval_evidence_sha256: 'x' } }), /DELETION_INDEPENDENT_APPROVAL_REQUIRED/);
}
{
  assert.throws(() => buildDeletionReceipt({ record_id: 'D', customer_id: 'A', source_sha256: 'x', vault_deleted: false, metadata_tombstoned: true, at: '2026-08-30', actor_id: 'u', authorization }), /DELETION_RECEIPT_INCOMPLETE/);
}

console.log('GRIDRECOVER data lifecycle: 12/12 PASS');
