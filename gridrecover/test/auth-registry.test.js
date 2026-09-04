'use strict';

const assert = require('assert');
const { AuthRegistry, hashToken } = require('../src/auth-registry');

const auth = new AuthRegistry();
const issued = auth.issue({
  customer_id: 'CUSTOMER-A', user_id: 'user-1', role: 'ANALYST',
  created_at: '2026-09-04T13:00:00Z', expires_at: '2026-09-05T13:00:00Z'
});

assert.equal(typeof issued.token, 'string');
assert(issued.token.length > 20);
const state = auth.exportState();
assert.equal(state.records.length, 1);
assert.equal(state.records[0].token_sha256, hashToken(issued.token));
assert.equal(JSON.stringify(state).includes(issued.token), false);

const principal = auth.resolve(issued.token, '2026-09-04T14:00:00Z');
assert.equal(principal.customer_id, 'CUSTOMER-A');
assert.equal(principal.user_id, 'user-1');
assert.equal(principal.role, 'ANALYST');
assert.equal(auth.can(principal, 'CASE_WRITE'), true);
assert.equal(auth.can(principal, 'REVIEW_APPROVE'), false);
assert.equal(auth.resolve(issued.token, '2026-09-05T13:00:00Z'), null);
assert.equal(auth.resolve('wrong-token', '2026-09-04T14:00:00Z'), null);

const reviewer = auth.issue({ customer_id: 'CUSTOMER-A', user_id: 'reviewer-1', role: 'REVIEWER', created_at: '2026-09-04T13:00:00Z', expires_at: '2026-09-05T13:00:00Z' });
const rp = auth.resolve(reviewer.token, '2026-09-04T14:00:00Z');
assert.equal(auth.can(rp, 'REVIEW_APPROVE'), true);
assert.equal(auth.can(rp, 'CASE_WRITE'), false);

const revoked = auth.revoke(reviewer.token_id, '2026-09-04T15:00:00Z');
assert.equal(revoked.already_revoked, false);
assert.equal(auth.resolve(reviewer.token, '2026-09-04T15:01:00Z'), null);
assert.equal(auth.revoke(reviewer.token_id, '2026-09-04T15:02:00Z').already_revoked, true);

const restored = AuthRegistry.fromState(auth.exportState());
assert.equal(restored.resolve(issued.token, '2026-09-04T14:00:00Z').user_id, 'user-1');
assert.equal(JSON.stringify(restored.exportState()).includes(issued.token), false);

assert.throws(() => auth.issue({ customer_id: 'A', user_id: 'u', role: 'ROOT', created_at: '2026-09-04', expires_at: '2026-09-05' }), /AUTH_ISSUE_INVALID/);
assert.throws(() => auth.issue({ customer_id: 'A', user_id: 'u', role: 'VIEWER', created_at: '2026-09-05', expires_at: '2026-09-04' }), /AUTH_EXPIRY_INVALID/);
assert.throws(() => AuthRegistry.fromState({ version: 1, records: [{ token_id: 'x' }] }), /AUTH_STATE_INVALID/);

console.log('GRIDRECOVER auth registry: 21/21 PASS');
