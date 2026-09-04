'use strict';

const assert = require('assert');
const { CaseStore } = require('../src/case-store');
const { AuditLog } = require('../src/audit-log');
const { transactMutation } = require('../src/mutation-transaction');

(async () => {
  const actor = { customer_id: 'A' };
  const store = new CaseStore();
  const audit = new AuditLog();
  let persisted = 0;

  const created = await transactMutation({
    store,
    audit,
    persist: async ({ store: s, audit: a }) => {
      assert.equal(s.listCases(actor).length, 1);
      assert.equal(a.verify(), true);
      persisted += 1;
    },
    mutate: async () => {
      const record = store.createCase(actor, { case_id: 'C1', customer_id: 'A', project_id: 'P1', evidence: [] });
      audit.append({ customer_id: 'A', case_id: 'C1', actor_id: 'u1', action: 'CASE_CREATED', at: '2026-09-04T13:45:00Z', detail: {} });
      return record;
    }
  });
  assert.equal(created.case_id, 'C1');
  assert.equal(persisted, 1);
  assert.equal(store.listCases(actor).length, 1);
  assert.equal(audit.listForCustomer('A').length, 1);

  let externalRolledBack = false;
  await assert.rejects(() => transactMutation({
    store,
    audit,
    persist: async () => { throw new Error('PERSISTENCE_FAILED'); },
    rollbackExternal: async () => { externalRolledBack = true; },
    mutate: async () => {
      store.createCase(actor, { case_id: 'C2', customer_id: 'A', project_id: 'P2', evidence: [] });
      audit.append({ customer_id: 'A', case_id: 'C2', actor_id: 'u1', action: 'CASE_CREATED', at: '2026-09-04T13:46:00Z', detail: {} });
      return { ok: true };
    }
  }), /PERSISTENCE_FAILED/);
  assert.equal(externalRolledBack, true);
  assert.throws(() => store.getCase(actor, 'C2'), /CASE_NOT_FOUND/);
  assert.equal(audit.listForCustomer('A').length, 1);
  assert.equal(audit.verify(), true);

  await assert.rejects(() => transactMutation({
    store,
    audit,
    persist: async () => { throw new Error('PERSISTENCE_FAILED'); },
    mutate: async () => {
      store.appendEvidence(actor, 'C1', { document_id: 'D1', sha256: 'sha256:d1' });
      audit.append({ customer_id: 'A', case_id: 'C1', actor_id: 'u1', action: 'DOCUMENT_INGESTED', at: '2026-09-04T13:47:00Z', detail: {} });
    }
  }), /PERSISTENCE_FAILED/);
  assert.equal(store.getCase(actor, 'C1').evidence.length, 0);
  assert.equal(audit.listForCustomer('A').length, 1);

  await assert.rejects(() => transactMutation({
    store,
    audit,
    persist: async () => {},
    mutate: async () => {
      audit.append({ customer_id: 'A', case_id: 'C1', actor_id: 'u1', action: 'BROKEN_FLOW', at: '2026-09-04T13:48:00Z', detail: {} });
      throw new Error('MUTATION_FAILED');
    }
  }), /MUTATION_FAILED/);
  assert.equal(audit.listForCustomer('A').length, 1);

  const badStore = new CaseStore();
  badStore.replaceState = () => { throw new Error('rollback broken'); };
  await assert.rejects(() => transactMutation({
    store: badStore,
    audit: new AuditLog(),
    mutate: async () => { throw new Error('MUTATION_FAILED'); }
  }), /TRANSACTION_ROLLBACK_FAILED/);

  console.log('GRIDRECOVER mutation transaction: 14/14 PASS');
})().catch(err => { console.error(err); process.exit(1); });
