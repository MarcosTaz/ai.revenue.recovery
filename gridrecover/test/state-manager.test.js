'use strict';

const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { CaseStore } = require('../src/case-store');
const { AuditLog } = require('../src/audit-log');
const { snapshotState, restoreState } = require('../src/state-manager');

const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'gridrecover-state-'));
const file = path.join(dir, 'operational.enc');
const key = '33'.repeat(32);
const wrong = '44'.repeat(32);
const actor = { customer_id: 'A' };

try {
  const store = new CaseStore();
  store.createCase(actor, { case_id: 'C1', customer_id: 'A', project_id: 'P1', evidence: [] });
  store.appendEvidence(actor, 'C1', { document_id: 'D1', sha256: 'sha256:d1', locator: 'Article 11.4.1' });
  const audit = new AuditLog();
  audit.append({ customer_id: 'A', case_id: 'C1', actor_id: 'u1', action: 'CASE_CREATED', at: '2026-08-29T20:00:00Z', detail: {} });
  audit.append({ customer_id: 'A', case_id: 'C1', actor_id: 'u2', action: 'EVIDENCE_ADDED', at: '2026-08-29T20:01:00Z', detail: { document_id: 'D1' } });

  const meta = snapshotState(file, key, store, audit);
  assert.equal(meta.cases, 1);
  assert.equal(meta.audit_events, 2);

  const restored = restoreState(file, key);
  assert.equal(restored.store.getCase(actor, 'C1').project_id, 'P1');
  assert.equal(restored.store.getCase(actor, 'C1').evidence[0].document_id, 'D1');
  assert.equal(restored.audit.verify(), true);
  assert.equal(restored.audit.listForCustomer('A').length, 2);

  restored.store.createCase(actor, { case_id: 'C2', customer_id: 'A', project_id: 'P2', evidence: [] });
  restored.audit.append({ customer_id: 'A', case_id: 'C2', actor_id: 'u3', action: 'CASE_CREATED', at: '2026-08-29T20:02:00Z', detail: {} });
  assert.equal(restored.store.listCases(actor).length, 2);
  assert.equal(restored.audit.verify(), true);

  assert.throws(() => restoreState(file, wrong), /SNAPSHOT_AUTHENTICATION_FAILED/);

  console.log('GRIDRECOVER operational restart: 10/10 PASS');
} finally {
  fs.rmSync(dir, { recursive: true, force: true });
}
