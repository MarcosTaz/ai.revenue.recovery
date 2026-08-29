'use strict';

const assert = require('assert');
const { startServer, tokenActorId } = require('../src/web-api');

const secretToken = 'super-secret-bearer-value';
const actorId = tokenActorId(secretToken);
assert.match(actorId, /^token-sha256:[a-f0-9]{24}$/);
assert.equal(actorId.includes(secretToken), false);
assert.equal(actorId.includes(secretToken.slice(0, 8)), false);

(async () => {
  const server = await startServer({ tokenToCustomer: { tokenA: 'A', tokenB: 'B' }, now: () => '2026-08-29T20:00:00Z' });
  const port = server.address().port;
  const base = `http://127.0.0.1:${port}`;
  const req = (path, options = {}, token = 'tokenA') => fetch(base + path, {
    ...options,
    headers: { 'content-type': 'application/json', ...(token ? { authorization: `Bearer ${token}` } : {}), ...(options.headers || {}) }
  });

  try {
    let r = await fetch(base + '/health');
    assert.equal(r.status, 200);
    assert.equal((await r.json()).production_ready, false);

    r = await req('/api/cases', { method: 'POST', body: JSON.stringify({ case_id: 'C1', project_id: 'P1' }) }, null);
    assert.equal(r.status, 401);

    r = await req('/api/cases', { method: 'POST', body: JSON.stringify({ case_id: 'C1', project_id: 'P1' }) });
    assert.equal(r.status, 201);
    assert.equal((await r.json()).customer_id, 'A');

    r = await req('/api/cases', { method: 'POST', body: JSON.stringify({ case_id: 'X', project_id: 'PX', customer_id: 'B' }) });
    assert.equal(r.status, 403);

    r = await req('/api/cases/C1', { method: 'GET' }, 'tokenB');
    assert.equal(r.status, 404);

    const networkInput = {
      jurisdiction: 'US_FEDERAL_FERC', project_scope: 'LARGE_GENERATOR_GT_20MW',
      agreement: { executed_lgia_id: 'LGIA-1', article_11_4_1_match: true, source_document_hash: 'sha256:a', source_locator: 'Article 11.4.1', superseded: false, trigger_satisfied: true, repayment_schedule_supported: true },
      economics: { network_upgrade_amount_paid: 1000, amounts_already_refunded: 100, repayments_received: 200, currency: 'USD' },
      evidence: { payment_source_hash: 'sha256:p', payment_matches_project: true, payment_is_network_upgrade: true }
    };
    r = await req('/api/evaluate/network-upgrade', { method: 'POST', body: JSON.stringify({ case_id: 'C1', input: networkInput }) });
    assert.equal(r.status, 200);
    assert.equal((await r.json()).candidate_amount, 700);

    r = await req('/api/evaluate/network-upgrade', { method: 'POST', body: JSON.stringify({ case_id: 'C1', input: networkInput }) }, 'tokenB');
    assert.equal(r.status, 404);

    r = await req('/api/dossiers', { method: 'POST', body: JSON.stringify({
      case_id: 'C1',
      caseMeta: { project_id: 'P1', jurisdiction: 'US_FEDERAL_FERC', transmission_provider: 'TP-1', currency: 'USD' },
      result: { status: 'SUPPORTED_CANDIDATE', candidate_amount: 700, currency: 'USD' },
      sources: [{ document_id: 'LGIA-1', sha256: 'sha256:a', locator: 'Article 11.4.1' }],
      calculations: [{ formula: '1000-100-200', result: 700 }],
      uncertainties: [],
      nextAction: 'Controlled reviewer confirmation.'
    }) });
    assert.equal(r.status, 200);
    const d = await r.json();
    assert.equal(d.finding.verified_recovery, false);
    assert.equal(d.finding.candidate_value, 700);

    r = await req('/api/cases/C1', { method: 'GET' });
    assert.equal(r.status, 200);
    assert.equal((await r.json()).customer_id, 'A');

    console.log('GRIDRECOVER web API: 12/12 PASS');
  } finally {
    await new Promise(resolve => server.close(resolve));
  }
})().catch(err => { console.error(err); process.exit(1); });
