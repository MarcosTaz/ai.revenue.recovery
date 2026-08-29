'use strict';

const assert = require('assert');
const { AuditLog } = require('../src/audit-log');

const log = new AuditLog();
const e1 = log.append({ customer_id: 'A', case_id: 'C1', actor_id: 'u1', action: 'CASE_CREATED', at: '2026-08-29T20:00:00Z', detail: { project: 'P1' } });
const e2 = log.append({ customer_id: 'A', case_id: 'C1', actor_id: 'u2', action: 'RULE_REVIEWED', at: '2026-08-29T20:01:00Z', detail: { rule: 'R1' } });
const e3 = log.append({ customer_id: 'B', case_id: 'C2', actor_id: 'u3', action: 'CASE_CREATED', at: '2026-08-29T20:02:00Z', detail: { project: 'P2' } });

assert.equal(e1.previous_hash, null);
assert.equal(e2.previous_hash, e1.event_hash);
assert.equal(e3.previous_hash, e2.event_hash);
assert.equal(log.verify(), true);
assert.equal(log.listForCustomer('A').length, 2);
assert.equal(log.listForCustomer('B').length, 1);
assert.throws(() => log.append({ customer_id: 'A' }), /AUDIT_EVENT_INCOMPLETE/);
assert.throws(() => log.append({ customer_id: 'A', case_id: 'C1', actor_id: 'u1', action: 'X', at: 'not-a-date' }), /AUDIT_TIMESTAMP_INVALID/);

const state = log.exportState();
assert.equal(state.version, 1);
assert.equal(state.events.length, 3);
const restarted = AuditLog.fromState(state);
assert.equal(restarted.verify(), true);
assert.equal(restarted.listForCustomer('A').length, 2);
const e4 = restarted.append({ customer_id: 'A', case_id: 'C1', actor_id: 'u4', action: 'DOSSIER_GENERATED', at: '2026-08-29T20:03:00Z', detail: { status: 'SUPPORTED_CANDIDATE' } });
assert.equal(e4.previous_hash, e3.event_hash);
assert.equal(restarted.verify(), true);

const tamperedState = log.exportState();
tamperedState.events[1].action = 'TAMPERED';
assert.throws(() => AuditLog.fromState(tamperedState), /AUDIT_CHAIN_INVALID/);
assert.throws(() => AuditLog.fromState({ version: 2, events: [] }), /AUDIT_STATE_INVALID/);

state.events[0].action = 'MUTATED_AFTER_RESTORE';
assert.equal(restarted.verify(), true);
assert.equal(restarted.listForCustomer('A')[0].action, 'CASE_CREATED');

const original = log.events[1];
log.events[1] = { ...original, action: 'TAMPERED' };
assert.equal(log.verify(), false);

console.log('GRIDRECOVER audit log security/restart: 17/17 PASS');
