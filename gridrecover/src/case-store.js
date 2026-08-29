'use strict';

class CaseStore {
  constructor() {
    this.cases = new Map();
  }

  createCase(actor, record) {
    if (!actor || !actor.customer_id) throw new Error('AUTH_REQUIRED');
    if (!record || !record.case_id) throw new Error('CASE_ID_REQUIRED');
    if (record.customer_id !== actor.customer_id) throw new Error('CROSS_TENANT_CREATE_DENIED');
    if (this.cases.has(record.case_id)) throw new Error('CASE_ID_EXISTS');
    const frozen = Object.freeze(JSON.parse(JSON.stringify(record)));
    this.cases.set(record.case_id, frozen);
    return frozen;
  }

  getCase(actor, caseId) {
    if (!actor || !actor.customer_id) throw new Error('AUTH_REQUIRED');
    const record = this.cases.get(caseId);
    if (!record || record.customer_id !== actor.customer_id) throw new Error('CASE_NOT_FOUND');
    return JSON.parse(JSON.stringify(record));
  }

  listCases(actor) {
    if (!actor || !actor.customer_id) throw new Error('AUTH_REQUIRED');
    return [...this.cases.values()]
      .filter(r => r.customer_id === actor.customer_id)
      .map(r => JSON.parse(JSON.stringify(r)));
  }

  appendEvidence(actor, caseId, evidence) {
    const record = this.getCase(actor, caseId);
    if (!evidence || !evidence.document_id || !evidence.sha256) throw new Error('EVIDENCE_PROVENANCE_REQUIRED');
    const current = Array.isArray(record.evidence) ? record.evidence : [];
    if (current.some(e => e.document_id === evidence.document_id)) throw new Error('EVIDENCE_ID_EXISTS');
    const updated = Object.freeze({ ...record, evidence: [...current, Object.freeze(JSON.parse(JSON.stringify(evidence)))] });
    this.cases.set(caseId, updated);
    return JSON.parse(JSON.stringify(updated));
  }
}

module.exports = { CaseStore };
