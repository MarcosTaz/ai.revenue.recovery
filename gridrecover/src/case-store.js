'use strict';

function clone(value) { return JSON.parse(JSON.stringify(value)); }
function freezeRecord(record) { return Object.freeze(clone(record)); }
function tenantCaseKey(customerId, caseId) { return `${customerId}\u0000${caseId}`; }

function normalizeRecord(record) {
  const version = Number.isInteger(record._version) && record._version >= 1 ? record._version : 1;
  return { ...record, _version: version };
}

function buildMap(initialRecords) {
  if (!Array.isArray(initialRecords)) throw new Error('CASE_STATE_INVALID');
  const next = new Map();
  for (const record of initialRecords) {
    if (!record || !record.case_id || !record.customer_id) throw new Error('CASE_STATE_INVALID');
    const normalized = normalizeRecord(record);
    const key = tenantCaseKey(normalized.customer_id, normalized.case_id);
    if (next.has(key)) throw new Error('CASE_STATE_DUPLICATE_ID');
    next.set(key, freezeRecord(normalized));
  }
  return next;
}

class CaseStore {
  constructor(initialRecords = []) {
    this.cases = buildMap(initialRecords);
  }

  static fromState(state) {
    if (!state || state.version !== 1 || !Array.isArray(state.cases)) throw new Error('CASE_STATE_INVALID');
    return new CaseStore(state.cases);
  }

  replaceState(state) {
    if (!state || state.version !== 1 || !Array.isArray(state.cases)) throw new Error('CASE_STATE_INVALID');
    const next = buildMap(state.cases);
    this.cases = next;
    return this.exportState();
  }

  exportState() {
    return { version: 1, cases: [...this.cases.values()].map(clone) };
  }

  createCase(actor, record) {
    if (!actor || !actor.customer_id) throw new Error('AUTH_REQUIRED');
    if (!record || !record.case_id) throw new Error('CASE_ID_REQUIRED');
    if (record.customer_id !== actor.customer_id) throw new Error('CROSS_TENANT_CREATE_DENIED');
    const key = tenantCaseKey(actor.customer_id, record.case_id);
    if (this.cases.has(key)) throw new Error('CASE_ID_EXISTS');
    const frozen = freezeRecord(normalizeRecord(record));
    this.cases.set(key, frozen);
    return clone(frozen);
  }

  getCase(actor, caseId) {
    if (!actor || !actor.customer_id) throw new Error('AUTH_REQUIRED');
    const record = this.cases.get(tenantCaseKey(actor.customer_id, caseId));
    if (!record) throw new Error('CASE_NOT_FOUND');
    return clone(record);
  }

  listCases(actor) {
    if (!actor || !actor.customer_id) throw new Error('AUTH_REQUIRED');
    return [...this.cases.values()].filter(r => r.customer_id === actor.customer_id).map(clone);
  }

  updateCase(actor, caseId, updater, expectedVersion = null) {
    if (!actor || !actor.customer_id) throw new Error('AUTH_REQUIRED');
    if (typeof updater !== 'function') throw new Error('CASE_UPDATER_REQUIRED');
    const current = this.getCase(actor, caseId);
    if (expectedVersion != null && expectedVersion !== current._version) throw new Error('CASE_VERSION_CONFLICT');
    const proposed = updater(clone(current));
    if (!proposed || typeof proposed !== 'object') throw new Error('CASE_UPDATE_INVALID');
    if (proposed.case_id !== current.case_id || proposed.customer_id !== current.customer_id) throw new Error('CASE_IDENTITY_IMMUTABLE');
    const next = normalizeRecord({ ...proposed, _version: current._version + 1 });
    const frozen = freezeRecord(next);
    this.cases.set(tenantCaseKey(actor.customer_id, caseId), frozen);
    return clone(frozen);
  }

  appendEvidence(actor, caseId, evidence) {
    if (!evidence || !evidence.document_id || !evidence.sha256) throw new Error('EVIDENCE_PROVENANCE_REQUIRED');
    let output;
    this.updateCase(actor, caseId, current => {
      const evidenceList = Array.isArray(current.evidence) ? current.evidence : [];
      if (evidenceList.some(e => e.document_id === evidence.document_id)) throw new Error('EVIDENCE_ID_EXISTS');
      output = { ...current, evidence: [...evidenceList, freezeRecord(evidence)] };
      return output;
    });
    return this.getCase(actor, caseId);
  }
}

module.exports = { CaseStore, tenantCaseKey, normalizeRecord };
