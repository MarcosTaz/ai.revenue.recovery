'use strict';

const { CaseStore } = require('./case-store');
const { AuditLog } = require('./audit-log');
const { saveEncryptedJson, loadEncryptedJson } = require('./encrypted-snapshot');

function snapshotState(filePath, key, store, audit) {
  if (!(store instanceof CaseStore)) throw new Error('CASE_STORE_REQUIRED');
  if (!(audit instanceof AuditLog)) throw new Error('AUDIT_LOG_REQUIRED');
  if (!audit.verify()) throw new Error('AUDIT_CHAIN_INVALID');
  const state = {
    version: 1,
    case_store: store.exportState(),
    audit_log: audit.exportState()
  };
  saveEncryptedJson(filePath, state, key);
  return { version: 1, cases: state.case_store.cases.length, audit_events: state.audit_log.events.length };
}

function restoreState(filePath, key) {
  const state = loadEncryptedJson(filePath, key);
  if (!state || state.version !== 1 || !state.case_store || !state.audit_log) throw new Error('OPERATIONAL_STATE_INVALID');
  const store = CaseStore.fromState(state.case_store);
  const audit = AuditLog.fromState(state.audit_log);
  return { store, audit };
}

module.exports = { snapshotState, restoreState };
