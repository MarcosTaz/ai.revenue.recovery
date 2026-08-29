'use strict';

function clone(value) { return JSON.parse(JSON.stringify(value)); }
function freezeRecord(record) { return Object.freeze(clone(record)); }

class CaseStore {
  constructor(initialRecords = []) {
    this.cases = new Map();
    if (!Array.isArray(initialRecords)) throw new Error('CASE_STATE_INVALID');
    for (const record of initialRecords) {
      if (!record || !record.case_id || !record.customer_id) throw new Error('CASE_STATE_INVALID');
      if (this.cases.has(record.case_id)) throw new Error('CASE_STATE_DUPLICATE_ID');
      this.cases.set(record.case_id, freezeRecord(record));
    }
  }

  static fromState(state) {
    if (!state || state.version !== 1 || !Array.isArray(state.cases)) throw new Error('CASE_STATE_INVALID');
    return new CaseStore(state.cases);
  }

  exportState() {
    return { version: 1, cases: [...this.cases.values()].map(clone) };
  }

  createCase(actor, record) {
    if (!actor || !actor.customer_id) throw new Error('AUTH_REQUIRED');
    if (!record || !record.case_id) throw new Error('CASE_ID_REQUIRED');
    if (record.customer_id !== actor.customer_id) throw new Error('CROSS_TENANT_CREATE_DENIED');
    if (this.cases.has(record.case_id)) throw new Error('CASE_ID_EXISTS');
    const frozen = freezeRecord(record);
    this.cases.set(record.case_id, frozen);
    return clone(frozen);
  }

  getCase(actor, caseId) {
    if (!actor || !actor.customer_id) throw new Error('AUTH_REQUIRED');
    const record = this.cases.get(caseId);
    if (!record || record.customer_id !== actor.customer_id) throw new Error('CASE_NOT_FOUND');
    return clone(record);
  }

  listCases(actor) {
    if (!actor || !actor.customer_id) throw new Error('AUTH_REQUIRED');
    return [...this.cases.values()].filter(r => r.customer_id === actor.customer_id).map(clone);
  }

  appendEvidence(actor, caseId, evidence) {
    const record = this.getCase(actor, caseId);
    if (!evidence || !evidence.document_id || !evidence.sha256) throw new Error('EVIDENCE_PROVENANCE_REQUIRED');
    const current = Array.isArray(record.evidence) ? record.evidence : [];
    if (current.some(e => e.document_id === evidence.document_id)) throw new Error('EVIDENCE_ID_EXISTS');
    const updated = freezeRecord({ ...record, evidence: [...current, freezeRecord(evidence)] });
    this.cases.set(caseId, updated);
    return clone(updated);
  }
}

module.exports = { CaseStore };
