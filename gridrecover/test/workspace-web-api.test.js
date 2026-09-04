'use strict';

const assert = require('assert');
const { startWorkspaceServer } = require('../src/workspace-web-api');
const { CaseStore } = require('../src/case-store');
const { AuditLog } = require('../src/audit-log');
const { AuthRegistry } = require('../src/auth-registry');

(async () => {
  const auth = new AuthRegistry();
  const analyst = auth.issue({ customer_id: 'A', user_id: 'analyst-a', role: 'ANALYST', created_at: '2026-09-04T13:00:00Z', expires_at: '2026-09-05T13:00:00Z' });
  const viewer = auth.issue({ customer_id: 'A', user_id: 'viewer-a', role: 'VIEWER', created_at: '2026-09-04T13:00:00Z', expires_at: '2026-09-05T13:00:00Z' });
  const other = auth.issue({ customer_id: 'B', user_id: 'analyst-b', role: 'ANALYST', created_at: '2026-09-04T13:00:00Z', expires_at: '2026-09-05T13:00:00Z' });
  const store = new CaseStore();
  const audit = new AuditLog();
  store.createCase({ customer_id: 'A' }, { case_id: 'C1', customer_id: 'A', project_id: 'P1', project_name: 'Project One', evidence: [], finding: { status: 'SUPPORTED_CANDIDATE', value: 1000, currency: 'USD', value_nature: 'CANDIDATE_REPAYMENT' } });
  store.createCase({ customer_id: 'B' }, { case_id: 'C1', customer_id: 'B', project_id: 'PB', project_name: 'Other Tenant', evidence: [] });

  let persistCalls = 0;
  const server = await startWorkspaceServer({
    authRegistry: auth,
    requireStrongAuth: true,
    store,
    audit,
    requireDurability: true,
    persistState: async () => { persistCalls += 1; },
    now: () => '2026-09-04T14:00:00Z'
  });
  const base = `http://127.0.0.1:${server.address().port}`;
  const req = (route, token, method = 'GET', body = null) => fetch(base + route, {
    method,
    body: body == null ? null : JSON.stringify(body),
    headers: { authorization: `Bearer ${token}`, ...(body == null ? {} : { 'content-type': 'application/json' }) }
  });

  try {
    let r = await req('/api/cases', viewer.token);
    assert.equal(r.status, 200);
    let body = await r.json();
    assert.equal(body.cases.length, 1);
    assert.equal(body.cases[0].project_id, 'P1');

    r = await req('/api/portfolio', viewer.token);
    assert.equal(r.status, 200);
    body = await r.json();
    assert.equal(body.case_count, 1);
    assert.equal(body.monetary.CANDIDATE_REPAYMENT.USD, 1000);

    r = await req('/api/cases/C1', viewer.token, 'PATCH', { expected_version: 1, patch: { next_action: 'x' } });
    assert.equal(r.status, 403);

    r = await req('/api/cases/C1', analyst.token, 'PATCH', { expected_version: 1, patch: { next_action: 'Verify Attachment FF', project_name: 'Project One Updated' } });
    assert.equal(r.status, 200);
    body = await r.json();
    assert.equal(body._version, 2);
    assert.equal(body.next_action, 'Verify Attachment FF');
    assert.equal(persistCalls, 1);

    r = await req('/api/cases/C1', analyst.token, 'PATCH', { expected_version: 1, patch: { next_action: 'stale' } });
    assert.equal(r.status, 409);
    assert.equal((await r.json()).error, 'CASE_VERSION_CONFLICT');

    r = await req('/api/cases/C1', analyst.token, 'PATCH', { expected_version: 2, patch: { finding: { status: 'RECOVERED' } } });
    assert.equal(r.status, 400);
    assert.match((await r.json()).error, /CASE_PATCH_FIELD_FORBIDDEN/);

    r = await req('/api/cases/C1/deadline', analyst.token, 'POST', {
      expected_version: 2,
      input: { deadline_id: 'DL1', source_document_id: 'D1', source_sha256: 'sha256:d1', source_locator: 'Article X', source_authority_verified: true, rule_type: 'FIXED_DATE', fixed_date: '2026-09-10', warning_days: 14 }
    });
    assert.equal(r.status, 200);
    body = await r.json();
    assert.equal(body._version, 3);
    assert.equal(body.deadline.status, 'DUE_SOON');

    const previous = [{ document_id: 'T1', sha256: 'sha256:old', source_type: 'EFFECTIVE_PROVIDER_TARIFF', effective_version: '110.0.0', effective_date: '2026-02-04', locator: 'Article 11.4.1', authority_status: 'FERC_ACCEPTED' }];
    const current = [{ ...previous[0], sha256: 'sha256:new', effective_version: '111.0.0' }];
    r = await req('/api/cases/C1/source-drift', analyst.token, 'POST', { expected_version: 3, input: { previous_sources: previous, current_sources: current } });
    assert.equal(r.status, 200);
    body = await r.json();
    assert.equal(body._version, 4);
    assert.equal(body.source_health, 'DRIFT_DETECTED');
    assert.equal(body.finding.status, 'STALE_REVIEW_REQUIRED');

    r = await req('/api/cases/C1/audit', viewer.token);
    assert.equal(r.status, 200);
    body = await r.json();
    assert(body.events.some(e => e.action === 'CASE_METADATA_UPDATED'));
    assert(body.events.some(e => e.action === 'DEADLINE_EVALUATED'));
    assert(body.events.some(e => e.action === 'SOURCE_DRIFT_EVALUATED'));

    r = await req('/api/cases', other.token);
    assert.equal(r.status, 200);
    body = await r.json();
    assert.equal(body.cases.length, 1);
    assert.equal(body.cases[0].project_id, 'PB');

    console.log('GRIDRECOVER workspace web API: 20/20 PASS');
  } finally {
    await new Promise(resolve => server.close(resolve));
  }
})().catch(error => { console.error(error); process.exit(1); });
