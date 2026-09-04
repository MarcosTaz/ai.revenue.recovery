'use strict';

const http = require('http');
const { createApi, readJson, tokenActorId, resolveCustomerForToken } = require('./web-api');
const { transactMutation } = require('./mutation-transaction');
const {
  listCases,
  buildPortfolio,
  updateCaseMetadata,
  evaluateAndStoreDeadline,
  evaluateAndStoreSourceDrift,
  evaluateAndStoreScenarioDelta
} = require('./workspace-service');

function json(res, status, body) {
  const payload = JSON.stringify(body);
  res.writeHead(status, {
    'content-type': 'application/json; charset=utf-8',
    'content-length': Buffer.byteLength(payload),
    'cache-control': 'no-store'
  });
  res.end(payload);
}

function createWorkspaceApi(options = {}) {
  const {
    tokenToCustomer = {}, authRegistry = null, requireStrongAuth = false,
    store, audit, persistState = null, requireDurability = false,
    now = () => new Date().toISOString()
  } = options;
  if (!store || !audit) throw new Error('WORKSPACE_STORE_AND_AUDIT_REQUIRED');
  const baseHandler = createApi(options);

  function principal(req) {
    const header = req.headers.authorization || '';
    const match = /^Bearer\s+(.+)$/.exec(header);
    if (!match) return null;
    const token = match[1];
    if (authRegistry && typeof authRegistry.resolve === 'function') {
      const p = authRegistry.resolve(token, now());
      if (!p) return null;
      return { ...p, actor_id: `user:${p.user_id}`, strong_auth: true };
    }
    if (requireStrongAuth) return null;
    const customerId = resolveCustomerForToken(tokenToCustomer, token);
    if (!customerId) return null;
    return { customer_id: customerId, user_id: null, role: 'ADMIN', actor_id: tokenActorId(token), strong_auth: false };
  }

  function allowed(p, permission) {
    if (!authRegistry) return true;
    return typeof authRegistry.can === 'function' && authRegistry.can(p, permission);
  }

  async function mutateDurably(mutate) {
    if (requireDurability && typeof persistState !== 'function') throw new Error('PERSISTENCE_REQUIRED');
    return transactMutation({
      store,
      audit,
      persist: typeof persistState === 'function'
        ? async ({ store: s, audit: a }) => {
            try { await persistState({ store: s, audit: a }); }
            catch (error) {
              if (error && error.message === 'PERSISTENCE_FAILED') throw error;
              const wrapped = new Error('PERSISTENCE_FAILED');
              wrapped.cause = error;
              throw wrapped;
            }
          }
        : null,
      mutate
    });
  }

  return async function workspaceHandler(req, res) {
    const url = new URL(req.url, 'http://localhost');
    const enhanced =
      (req.method === 'GET' && (url.pathname === '/api/cases' || url.pathname === '/api/portfolio')) ||
      (req.method === 'PATCH' && /^\/api\/cases\/[^/]+$/.test(url.pathname)) ||
      (req.method === 'POST' && /^\/api\/cases\/[^/]+\/(deadline|source-drift|scenario-delta)$/.test(url.pathname)) ||
      (req.method === 'GET' && /^\/api\/cases\/[^/]+\/audit$/.test(url.pathname));

    if (!enhanced) return baseHandler(req, res);

    try {
      if (requireStrongAuth && !authRegistry) return json(res, 503, { error: 'AUTH_REGISTRY_REQUIRED' });
      const p = principal(req);
      if (!p) return json(res, 401, { error: 'UNAUTHORIZED' });

      if (req.method === 'GET' && url.pathname === '/api/cases') {
        if (!allowed(p, 'CASE_READ')) return json(res, 403, { error: 'FORBIDDEN' });
        return json(res, 200, { cases: listCases(store, p) });
      }

      if (req.method === 'GET' && url.pathname === '/api/portfolio') {
        if (!allowed(p, 'CASE_READ')) return json(res, 403, { error: 'FORBIDDEN' });
        return json(res, 200, buildPortfolio(store, p));
      }

      const auditMatch = /^\/api\/cases\/([^/]+)\/audit$/.exec(url.pathname);
      if (req.method === 'GET' && auditMatch) {
        if (!allowed(p, 'CASE_READ')) return json(res, 403, { error: 'FORBIDDEN' });
        const caseId = decodeURIComponent(auditMatch[1]);
        try { store.getCase(p, caseId); }
        catch (error) { if (error.message === 'CASE_NOT_FOUND') return json(res, 404, { error: 'CASE_NOT_FOUND' }); throw error; }
        const events = audit.listForCustomer(p.customer_id).filter(event => event.case_id === caseId);
        return json(res, 200, { case_id: caseId, events });
      }

      const patchMatch = /^\/api\/cases\/([^/]+)$/.exec(url.pathname);
      if (req.method === 'PATCH' && patchMatch) {
        if (!allowed(p, 'CASE_WRITE')) return json(res, 403, { error: 'FORBIDDEN' });
        const caseId = decodeURIComponent(patchMatch[1]);
        const body = await readJson(req);
        const result = await mutateDurably(async () => {
          const updated = updateCaseMetadata(store, p, caseId, body.patch, body.expected_version);
          audit.append({ customer_id: p.customer_id, case_id: caseId, actor_id: p.actor_id, action: 'CASE_METADATA_UPDATED', at: now(), detail: { version: updated._version, fields: Object.keys(body.patch || {}).sort() } });
          return updated;
        });
        return json(res, 200, result);
      }

      const derivedMatch = /^\/api\/cases\/([^/]+)\/(deadline|source-drift|scenario-delta)$/.exec(url.pathname);
      if (req.method === 'POST' && derivedMatch) {
        if (!allowed(p, 'CASE_WRITE')) return json(res, 403, { error: 'FORBIDDEN' });
        const caseId = decodeURIComponent(derivedMatch[1]);
        const operation = derivedMatch[2];
        const body = await readJson(req);
        const expected = body.expected_version;
        const result = await mutateDurably(async () => {
          let updated;
          let action;
          if (operation === 'deadline') {
            updated = evaluateAndStoreDeadline(store, p, caseId, body.input, expected, now());
            action = 'DEADLINE_EVALUATED';
          } else if (operation === 'source-drift') {
            updated = evaluateAndStoreSourceDrift(store, p, caseId, body.input || {}, expected);
            action = 'SOURCE_DRIFT_EVALUATED';
          } else {
            updated = evaluateAndStoreScenarioDelta(store, p, caseId, body.input || {}, expected);
            action = 'SCENARIO_DELTA_EVALUATED';
          }
          audit.append({ customer_id: p.customer_id, case_id: caseId, actor_id: p.actor_id, action, at: now(), detail: { version: updated._version } });
          return updated;
        });
        return json(res, 200, result);
      }

      return baseHandler(req, res);
    } catch (error) {
      if (error.message === 'CASE_NOT_FOUND') return json(res, 404, { error: 'CASE_NOT_FOUND' });
      if (error.message === 'CASE_VERSION_CONFLICT') return json(res, 409, { error: 'CASE_VERSION_CONFLICT' });
      if (error.message === 'PERSISTENCE_REQUIRED' || error.message === 'PERSISTENCE_FAILED') return json(res, 503, { error: error.message });
      if (error.message === 'INVALID_JSON' || /^CASE_PATCH_/.test(error.message)) return json(res, 400, { error: error.message });
      return json(res, 500, { error: 'INTERNAL_ERROR' });
    }
  };
}

function startWorkspaceServer(options = {}, port = 0) {
  const server = http.createServer(createWorkspaceApi(options));
  return new Promise(resolve => server.listen(port, '127.0.0.1', () => resolve(server)));
}

module.exports = { createWorkspaceApi, startWorkspaceServer };
