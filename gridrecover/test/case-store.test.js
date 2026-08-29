'use strict';

const assert = require('assert');
const { CaseStore } = require('../src/case-store');

const store = new CaseStore();
const a = { customer_id: 'CUSTOMER-A' };
const b = { customer_id: 'CUSTOMER-B' };

store.createCase(a, { case_id: 'CASE-A1', customer_id: 'CUSTOMER-A', project_id: 'PA', evidence: [] });
store.createCase(b, { case_id: 'CASE-B1', customer_id: 'CUSTOMER-B', project_id: 'PB', evidence: [] });

assert.equal(store.listCases(a).length, 1);
assert.equal(store.listCases(b).length, 1);
assert.equal(store.getCase(a, 'CASE-A1').project_id, 'PA');
assert.throws(() => store.getCase(a, 'CASE-B1'), /CASE_NOT_FOUND/);
assert.throws(() => store.createCase(a, { case_id: 'CASE-X', customer_id: 'CUSTOMER-B' }), /CROSS_TENANT_CREATE_DENIED/);
assert.throws(() => store.getCase(null, 'CASE-A1'), /AUTH_REQUIRED/);

store.appendEvidence(a, 'CASE-A1', { document_id: 'DOC-1', sha256: 'sha256:doc1', locator: 'p1' });
assert.equal(store.getCase(a, 'CASE-A1').evidence.length, 1);
assert.throws(() => store.appendEvidence(b, 'CASE-A1', { document_id: 'DOC-2', sha256: 'sha256:doc2' }), /CASE_NOT_FOUND/);
assert.throws(() => store.appendEvidence(a, 'CASE-A1', { document_id: 'DOC-1', sha256: 'sha256:doc1' }), /EVIDENCE_ID_EXISTS/);
assert.throws(() => store.appendEvidence(a, 'CASE-A1', { document_id: 'DOC-2' }), /EVIDENCE_PROVENANCE_REQUIRED/);

const copy = store.getCase(a, 'CASE-A1');
copy.project_id = 'TAMPERED';
assert.equal(store.getCase(a, 'CASE-A1').project_id, 'PA');

console.log('GRIDRECOVER case store security: 10/10 PASS');
