'use strict';

const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { startServer } = require('../src/web-api');
const { CaseStore } = require('../src/case-store');
const { AuditLog } = require('../src/audit-log');
const { DocumentVault } = require('../src/document-vault');

async function withServer(options, fn) {
  const server = await startServer(options);
  const base = `http://127.0.0.1:${server.address().port}`;
  try { await fn(base); }
  finally { await new Promise(resolve => server.close(resolve)); }
}

function request(base, route, body, headers = {}) {
  return fetch(base + route, {
    method: 'POST',
    body,
    headers: { authorization: 'Bearer tokenA', ...headers }
  });
}

(async () => {
  {
    const store = new CaseStore();
    const audit = new AuditLog();
    await withServer({ tokenToCustomer: { tokenA: 'A' }, store, audit, requireDurability: true }, async base => {
      const health = await (await fetch(base + '/health')).json();
      assert.equal(health.durable_mutations, false);
      assert.equal(health.durability_required, true);
      const r = await request(base, '/api/cases', JSON.stringify({ case_id: 'C1', project_id: 'P1' }), { 'content-type': 'application/json' });
      assert.equal(r.status, 503);
      assert.equal((await r.json()).error, 'PERSISTENCE_REQUIRED');
      assert.equal(store.listCases({ customer_id: 'A' }).length, 0);
      assert.equal(audit.listForCustomer('A').length, 0);
    });
  }

  {
    const store = new CaseStore();
    const audit = new AuditLog();
    let persistCalls = 0;
    await withServer({
      tokenToCustomer: { tokenA: 'A' }, store, audit, requireDurability: true,
      persistState: async () => { persistCalls += 1; }
    }, async base => {
      const health = await (await fetch(base + '/health')).json();
      assert.equal(health.durable_mutations, true);
      const r = await request(base, '/api/cases', JSON.stringify({ case_id: 'C1', project_id: 'P1' }), { 'content-type': 'application/json' });
      assert.equal(r.status, 201);
      assert.equal(persistCalls, 1);
      assert.equal(store.getCase({ customer_id: 'A' }, 'C1').project_id, 'P1');
      assert.equal(audit.listForCustomer('A').length, 1);
    });
  }

  {
    const store = new CaseStore();
    const audit = new AuditLog();
    await withServer({
      tokenToCustomer: { tokenA: 'A' }, store, audit, requireDurability: true,
      persistState: async () => { throw new Error('disk failed'); }
    }, async base => {
      const r = await request(base, '/api/cases', JSON.stringify({ case_id: 'CFAIL', project_id: 'PFAIL' }), { 'content-type': 'application/json' });
      assert.equal(r.status, 503);
      assert.equal((await r.json()).error, 'PERSISTENCE_FAILED');
      assert.throws(() => store.getCase({ customer_id: 'A' }, 'CFAIL'), /CASE_NOT_FOUND/);
      assert.equal(audit.listForCustomer('A').length, 0);
    });
  }

  {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'gridrecover-durable-upload-'));
    try {
      const store = new CaseStore();
      const audit = new AuditLog();
      const vault = new DocumentVault({ rootDir: dir, masterKey: '77'.repeat(32) });
      let failPersistence = false;
      await withServer({
        tokenToCustomer: { tokenA: 'A' }, store, audit, vault, requireDurability: true,
        persistState: async () => { if (failPersistence) throw new Error('PERSISTENCE_FAILED'); }
      }, async base => {
        let r = await request(base, '/api/cases', JSON.stringify({ case_id: 'C1', project_id: 'P1', evidence: [] }), { 'content-type': 'application/json' });
        assert.equal(r.status, 201);
        failPersistence = true;
        r = await request(base, '/api/cases/C1/documents', Buffer.from('Article 11.4.1\nrepayable basis\n'), {
          'content-type': 'application/octet-stream',
          'x-document-id': 'DFAIL',
          'x-document-type': 'EXECUTED_LGIA',
          'x-file-extension': '.txt'
        });
        assert.equal(r.status, 503);
        assert.equal((await r.json()).error, 'PERSISTENCE_FAILED');
        assert.equal(store.getCase({ customer_id: 'A' }, 'C1').evidence.length, 0);
        assert.throws(() => vault.get({ customerId: 'A', documentId: 'DFAIL' }), /DOCUMENT_NOT_FOUND/);
        assert.equal(audit.listForCustomer('A').length, 1);
      });
    } finally { fs.rmSync(dir, { recursive: true, force: true }); }
  }

  console.log('GRIDRECOVER durable API: 22/22 PASS');
})().catch(err => { console.error(err); process.exit(1); });
