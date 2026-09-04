'use strict';

const http = require('http');
const crypto = require('crypto');
const { CaseStore } = require('./case-store');
const { AuditLog } = require('./audit-log');
const { evaluatePilotAdmission } = require('./pilot-admission');
const { evaluateNetworkUpgradeRepayment } = require('./gridrecover-core');
const { evaluateClusterWithdrawalCapital } = require('./cluster-withdrawal');
const { buildRecoveryDossier } = require('./dossier');
const { ingestDocumentBytes } = require('./document-ingest');
const { transactMutation } = require('./mutation-transaction');

function json(res, status, body) {
  const payload = JSON.stringify(body);
  res.writeHead(status, {
    'content-type': 'application/json; charset=utf-8',
    'content-length': Buffer.byteLength(payload),
    'cache-control': 'no-store'
  });
  res.end(payload);
}

async function readBytes(req, limit) {
  const chunks = [];
  let size = 0;
  for await (const chunk of req) {
    size += chunk.length;
    if (size > limit) throw new Error('PAYLOAD_TOO_LARGE');
    chunks.push(chunk);
  }
  return Buffer.concat(chunks);
}

async function readJson(req, limit = 1024 * 1024) {
  const bytes = await readBytes(req, limit);
  if (!bytes.length) return {};
  try { return JSON.parse(bytes.toString('utf8')); }
  catch { throw new Error('INVALID_JSON'); }
}

function tokenActorId(token) {
  return `token-sha256:${crypto.createHash('sha256').update(token, 'utf8').digest('hex').slice(0, 24)}`;
}

function resolveCustomerForToken(tokenToCustomer, token) {
  if (!tokenToCustomer || typeof tokenToCustomer !== 'object') return null;
  if (!Object.prototype.hasOwnProperty.call(tokenToCustomer, token)) return null;
  const customerId = tokenToCustomer[token];
  if (typeof customerId !== 'string' || !customerId.trim()) return null;
  return customerId;
}

function createApi({
  tokenToCustomer = {},
  authRegistry = null,
  requireStrongAuth = false,
  store = new CaseStore(),
  audit = new AuditLog(),
  vault = null,
  persistState = null,
  requireDurability = false,
  now = () => new Date().toISOString()
} = {}) {
  function actor(req) {
    const auth = req.headers.authorization || '';
    const match = /^Bearer\s+(.+)$/.exec(auth);
    if (!match) return null;
    const token = match[1];

    if (authRegistry && typeof authRegistry.resolve === 'function') {
      const principal = authRegistry.resolve(token, now());
      if (!principal) return null;
      return {
        customer_id: principal.customer_id,
        user_id: principal.user_id,
        role: principal.role,
        token_id: principal.token_id,
        actor_id: `user:${principal.user_id}`,
        strong_auth: true
      };
    }

    if (requireStrongAuth) return null;
    const customerId = resolveCustomerForToken(tokenToCustomer, token);
    if (!customerId) return null;
    return { customer_id: customerId, user_id: null, role: 'ADMIN', token_id: null, actor_id: tokenActorId(token), strong_auth: false };
  }

  function allowed(a, permission) {
    if (!authRegistry) return true;
    return typeof authRegistry.can === 'function' && authRegistry.can(a, permission);
  }

  async function mutateDurably({ mutate, rollbackExternal = null }) {
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
      mutate,
      rollbackExternal
    });
  }

  return async function handler(req, res) {
    try {
      const url = new URL(req.url, 'http://localhost');
      if (req.method === 'GET' && url.pathname === '/health') {
        return json(res, 200, {
          ok: true,
          service: 'gridrecover',
          production_ready: false,
          document_vault: Boolean(vault),
          durable_mutations: typeof persistState === 'function',
          durability_required: Boolean(requireDurability),
          auth_mode: authRegistry ? 'HASHED_TTL_ROLE_REGISTRY' : 'DEV_STATIC_TOKEN_MAP',
          strong_auth_required: Boolean(requireStrongAuth)
        });
      }

      if (requireStrongAuth && !authRegistry) return json(res, 503, { error: 'AUTH_REGISTRY_REQUIRED' });
      const a = actor(req);
      if (!a) return json(res, 401, { error: 'UNAUTHORIZED' });

      if (req.method === 'POST' && url.pathname === '/api/pilot-admission') {
        if (!allowed(a, 'CASE_WRITE')) return json(res, 403, { error: 'FORBIDDEN' });
        const body = await readJson(req);
        const result = evaluatePilotAdmission(body);
        await mutateDurably({
          mutate: async () => {
            audit.append({ customer_id: a.customer_id, case_id: body.case_id || 'INTAKE', actor_id: a.actor_id, action: 'PILOT_ADMISSION_EVALUATED', at: now(), detail: { outcome: result.outcome } });
            return result;
          }
        });
        return json(res, 200, result);
      }

      if (req.method === 'POST' && url.pathname === '/api/cases') {
        if (!allowed(a, 'CASE_WRITE')) return json(res, 403, { error: 'FORBIDDEN' });
        const body = await readJson(req);
        if (body.customer_id && body.customer_id !== a.customer_id) return json(res, 403, { error: 'CROSS_TENANT_CREATE_DENIED' });
        const record = { ...body, customer_id: a.customer_id };
        const created = await mutateDurably({
          mutate: async () => {
            const result = store.createCase(a, record);
            audit.append({ customer_id: a.customer_id, case_id: result.case_id, actor_id: a.actor_id, action: 'CASE_CREATED', at: now(), detail: { project_id: result.project_id || null } });
            return result;
          }
        });
        return json(res, 201, created);
      }

      const documentUploadMatch = /^\/api\/cases\/([^/]+)\/documents$/.exec(url.pathname);
      if (req.method === 'POST' && documentUploadMatch) {
        if (!allowed(a, 'DOCUMENT_UPLOAD')) return json(res, 403, { error: 'FORBIDDEN' });
        if (!vault) return json(res, 503, { error: 'DOCUMENT_VAULT_UNAVAILABLE' });
        const caseId = decodeURIComponent(documentUploadMatch[1]);
        try { store.getCase(a, caseId); }
        catch (e) { if (e.message === 'CASE_NOT_FOUND') return json(res, 404, { error: 'CASE_NOT_FOUND' }); throw e; }

        const documentId = String(req.headers['x-document-id'] || '');
        const documentType = String(req.headers['x-document-type'] || '');
        const fileExtension = String(req.headers['x-file-extension'] || '').toLowerCase();
        const bytes = await readBytes(req, 25 * 1024 * 1024);
        const ingested = ingestDocumentBytes({ bytes, fileExtension, documentId, documentType });
        let vaultCreated = false;

        const result = await mutateDurably({
          mutate: async () => {
            const saved = vault.put({ customerId: a.customer_id, documentId, documentType, bytes });
            vaultCreated = true;
            if (saved.source_sha256 !== ingested.source_sha256) throw new Error('VAULT_INGEST_HASH_MISMATCH');
            store.appendEvidence(a, caseId, {
              document_id: documentId,
              document_type: documentType,
              source_sha256: ingested.source_sha256,
              sha256: ingested.source_sha256,
              byte_length: ingested.byte_length,
              file_extension: fileExtension,
              extraction_method: ingested.extraction_method,
              locator_count: ingested.locators.length,
              locators: ingested.locators
            });
            audit.append({ customer_id: a.customer_id, case_id: caseId, actor_id: a.actor_id, action: 'DOCUMENT_INGESTED', at: now(), detail: { document_id: documentId, document_type: documentType, source_sha256: ingested.source_sha256, byte_length: ingested.byte_length } });
            return { document_id: documentId, document_type: documentType, source_sha256: ingested.source_sha256, byte_length: ingested.byte_length, extraction_method: ingested.extraction_method, locator_count: ingested.locators.length };
          },
          rollbackExternal: async () => {
            if (!vaultCreated) return;
            try { vault.delete({ customerId: a.customer_id, documentId }); }
            catch (error) { if (error.message !== 'DOCUMENT_NOT_FOUND') throw error; }
          }
        });
        return json(res, 201, result);
      }

      const caseMatch = /^\/api\/cases\/([^/]+)$/.exec(url.pathname);
      if (req.method === 'GET' && caseMatch) {
        if (!allowed(a, 'CASE_READ')) return json(res, 403, { error: 'FORBIDDEN' });
        try { return json(res, 200, store.getCase(a, decodeURIComponent(caseMatch[1]))); }
        catch (e) { if (e.message === 'CASE_NOT_FOUND') return json(res, 404, { error: 'CASE_NOT_FOUND' }); throw e; }
      }

      if (req.method === 'POST' && url.pathname === '/api/evaluate/network-upgrade') {
        if (!allowed(a, 'CASE_WRITE')) return json(res, 403, { error: 'FORBIDDEN' });
        const body = await readJson(req);
        try { store.getCase(a, body.case_id); }
        catch (e) { if (e.message === 'CASE_NOT_FOUND') return json(res, 404, { error: 'CASE_NOT_FOUND' }); throw e; }
        const result = evaluateNetworkUpgradeRepayment(body.input);
        await mutateDurably({
          mutate: async () => {
            audit.append({ customer_id: a.customer_id, case_id: body.case_id, actor_id: a.actor_id, action: 'NETWORK_UPGRADE_EVALUATED', at: now(), detail: { status: result.status } });
            return result;
          }
        });
        return json(res, 200, result);
      }

      if (req.method === 'POST' && url.pathname === '/api/evaluate/cluster-withdrawal') {
        if (!allowed(a, 'CASE_WRITE')) return json(res, 403, { error: 'FORBIDDEN' });
        const body = await readJson(req);
        try { store.getCase(a, body.case_id); }
        catch (e) { if (e.message === 'CASE_NOT_FOUND') return json(res, 404, { error: 'CASE_NOT_FOUND' }); throw e; }
        const result = evaluateClusterWithdrawalCapital(body.input);
        await mutateDurably({
          mutate: async () => {
            audit.append({ customer_id: a.customer_id, case_id: body.case_id, actor_id: a.actor_id, action: 'CLUSTER_WITHDRAWAL_EVALUATED', at: now(), detail: { status: result.status } });
            return result;
          }
        });
        return json(res, 200, result);
      }

      if (req.method === 'POST' && url.pathname === '/api/dossiers') {
        if (!allowed(a, 'CASE_WRITE')) return json(res, 403, { error: 'FORBIDDEN' });
        const body = await readJson(req);
        let caseRecord;
        try { caseRecord = store.getCase(a, body.case_id); }
        catch (e) { if (e.message === 'CASE_NOT_FOUND') return json(res, 404, { error: 'CASE_NOT_FOUND' }); throw e; }
        const dossier = buildRecoveryDossier({
          ...body,
          caseMeta: { ...body.caseMeta, case_id: body.case_id, customer_id: a.customer_id, project_id: body.caseMeta?.project_id || caseRecord.project_id }
        });
        await mutateDurably({
          mutate: async () => {
            audit.append({ customer_id: a.customer_id, case_id: body.case_id, actor_id: a.actor_id, action: 'DOSSIER_GENERATED', at: now(), detail: { status: dossier.status || dossier.finding?.status || null } });
            return dossier;
          }
        });
        return json(res, dossier.status === 'DOSSIER_BLOCKED' ? 422 : 200, dossier);
      }

      return json(res, 404, { error: 'NOT_FOUND' });
    } catch (e) {
      if (e.message === 'PAYLOAD_TOO_LARGE' || e.message === 'DOCUMENT_TOO_LARGE') return json(res, 413, { error: e.message });
      if (e.message === 'EVIDENCE_ID_EXISTS' || e.message === 'DOCUMENT_ID_EXISTS' || e.message === 'CASE_ID_EXISTS') return json(res, 409, { error: e.message });
      if (e.message === 'PERSISTENCE_REQUIRED' || e.message === 'PERSISTENCE_FAILED') return json(res, 503, { error: e.message });
      if (e.message === 'INVALID_JSON') return json(res, 400, { error: e.message });
      if (/^(DOCUMENT_|PDF_|CUSTOMER_ID_|DOCUMENT_ID_|DOCUMENT_TYPE_)/.test(e.message)) return json(res, 400, { error: e.message });
      return json(res, 500, { error: 'INTERNAL_ERROR' });
    }
  };
}

function startServer(options = {}, port = 0) {
  const server = http.createServer(createApi(options));
  return new Promise(resolve => server.listen(port, '127.0.0.1', () => resolve(server)));
}

module.exports = { createApi, startServer, readJson, readBytes, tokenActorId, resolveCustomerForToken };
