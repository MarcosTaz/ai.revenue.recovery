'use strict';

const assert = require('assert');
const { startServer } = require('../src/web-api');
const { CaseStore } = require('../src/case-store');
const { AuditLog } = require('../src/audit-log');
const { AuthRegistry } = require('../src/auth-registry');

async function withServer(options, fn) {
  const server = await startServer(options);
  const base = `http://127.0.0.1:${server.address().port}`;
  try { await fn(base); }
  finally { await new Promise(resolve => server.close(resolve)); }
}

function request(base, route, token, method = 'GET', body = null) {
  return fetch(base + route, {
    method,
    body,
    headers: { ...(token ? { authorization: `Bearer ${token}` } : {}), ...(body ? { 'content-type': 'application/json' } : {}) }
  });
}

(async () => {
  const auth = new AuthRegistry();
  const analyst = auth.issue({ customer_id: 'A', user_id: 'analyst-a', role: 'ANALYST', created_at: '2026-09-04T13:00:00Z', expires_at: '2026-09-05T13:00:00Z' });
  const viewer = auth.issue({ customer_id: 'A', user_id: 'viewer-a', role: 'VIEWER', created_at: '2026-09-04T13:00:00Z', expires_at: '2026-09-05T13:00:00Z' });
  const reviewer = auth.issue({ customer_id: 'A', user_id: 'reviewer-a', role: 'REVIEWER', created_at: '2026-09-04T13:00:00Z', expires_at: '2026-09-05T13:00:00Z' });
  const other = auth.issue({ customer_id: 'B', user_id: 'analyst-b', role: 'ANALYST', created_at: '2026-09-04T13:00:00Z', expires_at: '2026-09-05T13:00:00Z' });
  const expired = auth.issue({ customer_id: 'A', user_id: 'expired-a', role: 'ANALYST', created_at: '2026-09-03T10:00:00Z', expires_at: '2026-09-04T13:30:00Z' });

  const store = new CaseStore();
  const audit = new AuditLog();
  await withServer({ authRegistry: auth, requireStrongAuth: true, store, audit, now: () => '2026-09-04T14:00:00Z' }, async base => {
    let r = await fetch(base + '/health');
    let h = await r.json();
    assert.equal(h.auth_mode, 'HASHED_TTL_ROLE_REGISTRY');
    assert.equal(h.strong_auth_required, true);

    r = await request(base, '/api/cases', null, 'POST', JSON.stringify({ case_id: 'C0', project_id: 'P0' }));
    assert.equal(r.status, 401);
    r = await request(base, '/api/cases', expired.token, 'POST', JSON.stringify({ case_id: 'C0', project_id: 'P0' }));
    assert.equal(r.status, 401);
    r = await request(base, '/api/cases', viewer.token, 'POST', JSON.stringify({ case_id: 'C0', project_id: 'P0' }));
    assert.equal(r.status, 403);
    r = await request(base, '/api/cases', reviewer.token, 'POST', JSON.stringify({ case_id: 'C0', project_id: 'P0' }));
    assert.equal(r.status, 403);

    r = await request(base, '/api/cases', analyst.token, 'POST', JSON.stringify({ case_id: 'C1', project_id: 'P1', evidence: [] }));
    assert.equal(r.status, 201);
    assert.equal((await r.json()).customer_id, 'A');
    r = await request(base, '/api/cases/C1', viewer.token);
    assert.equal(r.status, 200);
    r = await request(base, '/api/cases/C1', reviewer.token);
    assert.equal(r.status, 200);
    r = await request(base, '/api/cases/C1', other.token);
    assert.equal(r.status, 404);

    const evaluation = {
      case_id: 'C1', input: {
        jurisdiction: 'US_FEDERAL_FERC', project_scope: 'LARGE_GENERATOR_GT_20MW',
        agreement: { executed_lgia_id: 'L1', article_11_4_1_match: true, source_document_hash: 'h', source_locator: 'A', superseded: false, trigger_satisfied: true, repayment_schedule_supported: true },
        economics: { network_upgrade_amount_paid: 100, repayable_network_upgrade_amount: 100, amounts_already_refunded: 0, repayments_received: 0, currency: 'USD' },
        evidence: { payment_source_hash: 'p', payment_matches_project: true, payment_is_network_upgrade: true, repayable_basis_source_hash: 'r', repayable_basis_locator: 'FF', repayable_basis_verified: true }
      }
    };
    r = await request(base, '/api/evaluate/network-upgrade', reviewer.token, 'POST', JSON.stringify(evaluation));
    assert.equal(r.status, 403);
    r = await request(base, '/api/evaluate/network-upgrade', analyst.token, 'POST', JSON.stringify(evaluation));
    assert.equal(r.status, 200);
    assert.equal((await r.json()).candidate_amount, 100);

    const events = audit.listForCustomer('A');
    assert(events.some(e => e.actor_id === 'user:analyst-a' && e.action === 'CASE_CREATED'));
    assert.equal(JSON.stringify(events).includes(analyst.token), false);
  });

  const revoked = auth.issue({ customer_id: 'A', user_id: 'revoked-a', role: 'ANALYST', created_at: '2026-09-04T13:00:00Z', expires_at: '2026-09-05T13:00:00Z' });
  auth.revoke(revoked.token_id, '2026-09-04T13:50:00Z');
  await withServer({ authRegistry: auth, requireStrongAuth: true, now: () => '2026-09-04T14:00:00Z' }, async base => {
    const r = await request(base, '/api/cases', revoked.token, 'POST', JSON.stringify({ case_id: 'X', project_id: 'X' }));
    assert.equal(r.status, 401);
  });

  await withServer({ requireStrongAuth: true, tokenToCustomer: { dev: 'A' } }, async base => {
    const r = await request(base, '/api/cases', 'dev', 'POST', JSON.stringify({ case_id: 'X', project_id: 'X' }));
    assert.equal(r.status, 503);
    assert.equal((await r.json()).error, 'AUTH_REGISTRY_REQUIRED');
  });

  console.log('GRIDRECOVER strong auth API: 18/18 PASS');
})().catch(err => { console.error(err); process.exit(1); });
