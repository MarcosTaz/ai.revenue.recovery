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

function json(res, status, body) {
  const payload = JSON.stringify(body);
  res.writeHead(status, { 'content-type': 'application/json; charset=utf-8', 'content-length': Buffer.byteLength(payload), 'cache-control': 'no-store' });
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

function createApi({ tokenToCustomer = {}, store = new CaseStore(), audit = new AuditLog(), vault = null, now = () => new Date().toISOString() } = {}) {
  function actor(req) {
    const auth = req.headers.authorization || '';
    const match = /^Bearer\s+(.+)$/.exec(auth);
    if (!match || !tokenToCustomer[match[1]]) return null;
    return { customer_id: tokenToCustomer[match[1]], actor_id: tokenActorId(match[1]) };
  }

  return async function handler(req, res) {
    try {
      const url = new URL(req.url, 'http://localhost');
      if (req.method === 'GET' && url.pathname === '/health') {
        return json(res, 200, { ok: true, service: 'gridrecover', production_ready: false, document_vault: Boolean(vault) });
      }

      const a = actor(req);
      if (!a) return json(res, 401, { error: 'UNAUTHORIZED' });

      if (req.method === 'POST' && url.pathname === '/api/pilot-admission') {
        const body = await readJson(req);
        const result = evaluatePilotAdmission(body);
        audit.append({ customer_id: a.customer_id, case_id: body.case_id || 'INTAKE', actor_id: a.actor_id, action: 'PILOT_ADMISSION_EVALUATED', at: now(), detail: { outcome: result.outcome } });
        return json(res, 200, result);
      }

      if (req.method === 'POST' && url.pathname === '/api/cases') {
        const body = await readJson(req);
        if (body.customer_id && body.customer_id !== a.customer_id) return json(res, 403, { error: 'CROSS_TENANT_CREATE_DENIED' });
        const record = { ...body, customer_id: a.customer_id };
        const created = store.createCase(a, record);
        audit.append({ customer_id: a.customer_id, case_id: created.case_id, actor_id: a.actor_id, action: 'CASE_CREATED', at: now(), detail: { project_id: created.project_id || null } });
        return json(res, 201, created);
      }

      const documentUploadMatch = /^\/api\/cases\/([^/]+)\/documents$/.exec(url.pathname);
      if (req.method === 'POST' && documentUploadMatch) {
        if (!vault) return json(res, 503, { error: 'DOCUMENT_VAULT_UNAVAILABLE' });
        const caseId = decodeURIComponent(documentUploadMatch[1]);
        try { store.getCase(a, caseId); }
        catch (e) { if (e.message === 'CASE_NOT_FOUND') return json(res, 404, { error: 'CASE_NOT_FOUND' }); throw e; }

        const documentId = String(req.headers['x-document-id'] || '');
        const documentType = String(req.headers['x-document-type'] || '');
        const fileExtension = String(req.headers['x-file-extension'] || '').toLowerCase();
        const bytes = await readBytes(req, 25 * 1024 * 1024);
        const ingested = ingestDocumentBytes({ bytes, fileExtension, documentId, documentType });
        const saved = vault.put({ customerId: a.customer_id, documentId, documentType, bytes });
        if (saved.source_sha256 !== ingested.source_sha256) {
          try { vault.delete({ customerId: a.customer_id, documentId }); } catch {}
          throw new Error('VAULT_INGEST_HASH_MISMATCH');
        }
        try {
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
        } catch (error) {
          try { vault.delete({ customerId: a.customer_id, documentId }); } catch {}
          throw error;
        }
        audit.append({ customer_id: a.customer_id, case_id: caseId, actor_id: a.actor_id, action: 'DOCUMENT_INGESTED', at: now(), detail: { document_id: documentId, document_type: documentType, source_sha256: ingested.source_sha256, byte_length: ingested.byte_length } });
        return json(res, 201, { document_id: documentId, document_type: documentType, source_sha256: ingested.source_sha256, byte_length: ingested.byte_length, extraction_method: ingested.extraction_method, locator_count: ingested.locators.length });
      }

      const caseMatch = /^\/api\/cases\/([^/]+)$/.exec(url.pathname);
      if (req.method === 'GET' && caseMatch) {
        try { return json(res, 200, store.getCase(a, decodeURIComponent(caseMatch[1]))); }
        catch (e) { if (e.message === 'CASE_NOT_FOUND') return json(res, 404, { error: 'CASE_NOT_FOUND' }); throw e; }
      }

      if (req.method === 'POST' && url.pathname === '/api/evaluate/network-upgrade') {
        const body = await readJson(req);
        try { store.getCase(a, body.case_id); }
        catch (e) { if (e.message === 'CASE_NOT_FOUND') return json(res, 404, { error: 'CASE_NOT_FOUND' }); throw e; }
        const result = evaluateNetworkUpgradeRepayment(body.input);
        audit.append({ customer_id: a.customer_id, case_id: body.case_id, actor_id: a.actor_id, action: 'NETWORK_UPGRADE_EVALUATED', at: now(), detail: { status: result.status } });
        return json(res, 200, result);
      }

      if (req.method === 'POST' && url.pathname === '/api/evaluate/cluster-withdrawal') {
        const body = await readJson(req);
        try { store.getCase(a, body.case_id); }
        catch (e) { if (e.message === 'CASE_NOT_FOUND') return json(res, 404, { error: 'CASE_NOT_FOUND' }); throw e; }
        const result = evaluateClusterWithdrawalCapital(body.input);
        audit.append({ customer_id: a.customer_id, case_id: body.case_id, actor_id: a.actor_id, action: 'CLUSTER_WITHDRAWAL_EVALUATED', at: now(), detail: { status: result.status } });
        return json(res, 200, result);
      }

      if (req.method === 'POST' && url.pathname === '/api/dossiers') {
        const body = await readJson(req);
        let caseRecord;
        try { caseRecord = store.getCase(a, body.case_id); }
        catch (e) { if (e.message === 'CASE_NOT_FOUND') return json(res, 404, { error: 'CASE_NOT_FOUND' }); throw e; }
        const dossier = buildRecoveryDossier({ ...body, caseMeta: { ...body.caseMeta, case_id: body.case_id, customer_id: a.customer_id, project_id: body.caseMeta?.project_id || caseRecord.project_id } });
        audit.append({ customer_id: a.customer_id, case_id: body.case_id, actor_id: a.actor_id, action: 'DOSSIER_GENERATED', at: now(), detail: { status: dossier.status || dossier.finding?.status || null } });
        return json(res, dossier.status === 'DOSSIER_BLOCKED' ? 422 : 200, dossier);
      }

      return json(res, 404, { error: 'NOT_FOUND' });
    } catch (e) {
      if (e.message === 'PAYLOAD_TOO_LARGE' || e.message === 'DOCUMENT_TOO_LARGE') return json(res, 413, { error: e.message });
      if (e.message === 'INVALID_JSON') return json(res, 400, { error: e.message });
      if (/^(DOCUMENT_|PDF_|CUSTOMER_ID_|DOCUMENT_ID_|DOCUMENT_TYPE_)/.test(e.message)) return json(res, 400, { error: e.message });
      if (e.message === 'EVIDENCE_ID_EXISTS' || e.message === 'DOCUMENT_ID_EXISTS') return json(res, 409, { error: e.message });
      return json(res, 500, { error: 'INTERNAL_ERROR' });
    }
  };
}

function startServer(options = {}, port = 0) {
  const server = http.createServer(createApi(options));
  return new Promise(resolve => server.listen(port, '127.0.0.1', () => resolve(server)));
}

module.exports = { createApi, startServer, readJson, readBytes, tokenActorId };
