'use strict';

const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { startServer, tokenActorId } = require('../src/web-api');
const { DocumentVault } = require('../src/document-vault');

const secretToken = 'super-secret-bearer-value';
const actorId = tokenActorId(secretToken);
assert.match(actorId, /^token-sha256:[a-f0-9]{24}$/);
assert.equal(actorId.includes(secretToken), false);
assert.equal(actorId.includes(secretToken.slice(0, 8)), false);

(async () => {
  const vaultDir = fs.mkdtempSync(path.join(os.tmpdir(), 'gridrecover-api-vault-'));
  const vault = new DocumentVault({ rootDir: vaultDir, masterKey: '66'.repeat(32) });
  const server = await startServer({ tokenToCustomer: { tokenA: 'A', tokenB: 'B' }, vault, now: () => '2026-08-29T20:00:00Z' });
  const port = server.address().port;
  const base = `http://127.0.0.1:${port}`;
  const req = (route, options = {}, token = 'tokenA') => fetch(base + route, {
    ...options,
    headers: { 'content-type': 'application/json', ...(token ? { authorization: `Bearer ${token}` } : {}), ...(options.headers || {}) }
  });

  try {
    let r = await fetch(base + '/health');
    assert.equal(r.status, 200);
    const health = await r.json();
    assert.equal(health.production_ready, false);
    assert.equal(health.document_vault, true);

    r = await req('/api/cases', { method: 'POST', body: JSON.stringify({ case_id: 'C1', project_id: 'P1' }) }, null);
    assert.equal(r.status, 401);

    r = await req('/api/cases', { method: 'POST', body: JSON.stringify({ case_id: 'C1', project_id: 'P1' }) });
    assert.equal(r.status, 201);
    assert.equal((await r.json()).customer_id, 'A');

    r = await req('/api/cases', { method: 'POST', body: JSON.stringify({ case_id: 'X', project_id: 'PX', customer_id: 'B' }) });
    assert.equal(r.status, 403);

    r = await req('/api/cases/C1', { method: 'GET' }, 'tokenB');
    assert.equal(r.status, 404);

    const docBytes = Buffer.from('Article 11.4.1\nMISO repayment source test\n', 'utf8');
    r = await req('/api/cases/C1/documents', {
      method: 'POST', body: docBytes,
      headers: { 'content-type': 'application/octet-stream', 'x-document-id': 'LGIA-UPLOAD-1', 'x-document-type': 'EXECUTED_LGIA', 'x-file-extension': '.txt' }
    });
    assert.equal(r.status, 201);
    const upload = await r.json();
    assert.equal(upload.document_id, 'LGIA-UPLOAD-1');
    assert.equal(upload.extraction_method, 'utf8-direct');
    assert(upload.locator_count >= 2);

    r = await req('/api/cases/C1', { method: 'GET' });
    const afterUpload = await r.json();
    assert.equal(afterUpload.evidence.length, 1);
    assert.equal(afterUpload.evidence[0].source_sha256, upload.source_sha256);
    assert.equal(afterUpload.evidence[0].locators[0].source_sha256, upload.source_sha256);

    r = await req('/api/cases/C1/documents', {
      method: 'POST', body: docBytes,
      headers: { 'content-type': 'application/octet-stream', 'x-document-id': 'B-DOC', 'x-document-type': 'EXECUTED_LGIA', 'x-file-extension': '.txt' }
    }, 'tokenB');
    assert.equal(r.status, 404);

    r = await req('/api/cases/C1/documents', {
      method: 'POST', body: docBytes,
      headers: { 'content-type': 'application/octet-stream', 'x-document-id': 'LGIA-UPLOAD-1', 'x-document-type': 'EXECUTED_LGIA', 'x-file-extension': '.txt' }
    });
    assert.equal(r.status, 409);

    r = await req('/api/cases/C1/documents', {
      method: 'POST', body: Buffer.from('not a pdf'),
      headers: { 'content-type': 'application/pdf', 'x-document-id': 'BAD-PDF', 'x-document-type': 'EXECUTED_LGIA', 'x-file-extension': '.pdf' }
    });
    assert.equal(r.status, 400);

    const networkInput = {
      jurisdiction: 'US_FEDERAL_FERC', project_scope: 'LARGE_GENERATOR_GT_20MW',
      agreement: { executed_lgia_id: 'LGIA-1', article_11_4_1_match: true, source_document_hash: 'sha256:a', source_locator: 'Article 11.4.1', superseded: false, trigger_satisfied: true, repayment_schedule_supported: true },
      economics: { network_upgrade_amount_paid: 1000, repayable_network_upgrade_amount: 700, amounts_already_refunded: 100, repayments_received: 200, currency: 'USD' },
      evidence: { payment_source_hash: 'sha256:p', payment_matches_project: true, payment_is_network_upgrade: true, repayable_basis_source_hash: 'sha256:r', repayable_basis_locator: 'Attachment FF allocation', repayable_basis_verified: true }
    };
    r = await req('/api/evaluate/network-upgrade', { method: 'POST', body: JSON.stringify({ case_id: 'C1', input: networkInput }) });
    assert.equal(r.status, 200);
    const evaluation = await r.json();
    assert.equal(evaluation.candidate_amount, 400);
    assert.equal(evaluation.verified_total_network_upgrade_paid, 1000);
    assert.equal(evaluation.verified_repayable_base, 700);

    r = await req('/api/evaluate/network-upgrade', { method: 'POST', body: JSON.stringify({ case_id: 'C1', input: networkInput }) }, 'tokenB');
    assert.equal(r.status, 404);

    r = await req('/api/dossiers', { method: 'POST', body: JSON.stringify({
      case_id: 'C1',
      caseMeta: { project_id: 'P1', jurisdiction: 'US_FEDERAL_FERC', transmission_provider: 'MISO', currency: 'USD' },
      result: { status: 'SUPPORTED_CANDIDATE', candidate_amount: 400, currency: 'USD' },
      sources: [
        { document_id: 'LGIA-1', sha256: 'sha256:a', locator: 'Article 11.4.1' },
        { document_id: 'REPAYABLE-1', sha256: 'sha256:r', locator: 'Attachment FF allocation' }
      ],
      calculations: [{ formula: '700-100-200', result: 400 }],
      uncertainties: [],
      nextAction: 'Controlled reviewer confirmation.'
    }) });
    assert.equal(r.status, 200);
    const d = await r.json();
    assert.equal(d.finding.verified_recovery, false);
    assert.equal(d.finding.candidate_value, 400);

    r = await req('/api/cases/C1', { method: 'GET' });
    assert.equal(r.status, 200);
    assert.equal((await r.json()).customer_id, 'A');

    console.log('GRIDRECOVER web API + document upload: 23/23 PASS');
  } finally {
    await new Promise(resolve => server.close(resolve));
    fs.rmSync(vaultDir, { recursive: true, force: true });
  }
})().catch(err => { console.error(err); process.exit(1); });
