'use strict';

const { buildPortfolioCommandCenter } = require('./portfolio-command-center');
const { evaluateDeadline } = require('./deadline-engine');
const { evaluateDependencySet } = require('./source-drift-sentinel');
const { evaluateScenarioDelta } = require('./scenario-delta');

const EDITABLE_METADATA = new Set([
  'project_name',
  'transmission_provider',
  'queue_or_interconnection_id',
  'process_stage',
  'next_action',
  'owner_label'
]);

function sanitizeMetadataPatch(patch) {
  if (!patch || typeof patch !== 'object' || Array.isArray(patch)) throw new Error('CASE_PATCH_INVALID');
  const output = {};
  for (const [key, value] of Object.entries(patch)) {
    if (!EDITABLE_METADATA.has(key)) throw new Error(`CASE_PATCH_FIELD_FORBIDDEN:${key}`);
    if (value != null && typeof value !== 'string') throw new Error(`CASE_PATCH_VALUE_INVALID:${key}`);
    if (typeof value === 'string' && value.length > 500) throw new Error(`CASE_PATCH_VALUE_TOO_LONG:${key}`);
    output[key] = value == null ? null : value.trim();
  }
  return output;
}

function updateCaseMetadata(store, actor, caseId, patch, expectedVersion) {
  const safe = sanitizeMetadataPatch(patch);
  return store.updateCase(actor, caseId, current => ({ ...current, ...safe }), expectedVersion);
}

function listCases(store, actor) {
  return store.listCases(actor).sort((a, b) => String(a.project_name || a.case_id).localeCompare(String(b.project_name || b.case_id)));
}

function portfolioItemFromCase(record) {
  const recovery = record.recovery || null;
  return {
    case_id: record.case_id,
    project_id: record.project_id,
    project_name: record.project_name || null,
    finding: record.finding || { status: 'UNKNOWN' },
    deadline: record.deadline || { status: 'UNKNOWN', days_remaining: null },
    source_health: record.source_health || 'UNKNOWN',
    admission_status: record.admission_status || 'UNKNOWN',
    verified_recovery: recovery && recovery.recovered_cash_verified === true
      ? { payment_verified: true, amount: recovery.verified_recovery_amount, currency: recovery.currency }
      : null,
    next_action: record.next_action || null
  };
}

function buildPortfolio(store, actor) {
  return buildPortfolioCommandCenter(store.listCases(actor).map(portfolioItemFromCase));
}

function evaluateAndStoreDeadline(store, actor, caseId, input, expectedVersion, now) {
  const result = evaluateDeadline({ ...input, case_id: caseId }, now);
  return store.updateCase(actor, caseId, current => ({ ...current, deadline: result }), expectedVersion);
}

function evaluateAndStoreSourceDrift(store, actor, caseId, { previous_sources, current_sources }, expectedVersion) {
  const result = evaluateDependencySet(previous_sources, current_sources);
  return store.updateCase(actor, caseId, current => ({
    ...current,
    source_health: result.status,
    source_drift: result,
    finding: result.invalidate_findings === true && current.finding?.status === 'SUPPORTED_CANDIDATE'
      ? { ...current.finding, status: 'STALE_REVIEW_REQUIRED', stale_reason: 'SOURCE_DRIFT' }
      : current.finding
  }), expectedVersion);
}

function evaluateAndStoreScenarioDelta(store, actor, caseId, input, expectedVersion) {
  const result = evaluateScenarioDelta({ ...input, case_id: caseId });
  return store.updateCase(actor, caseId, current => ({ ...current, last_scenario_delta: result }), expectedVersion);
}

module.exports = {
  EDITABLE_METADATA,
  sanitizeMetadataPatch,
  updateCaseMetadata,
  listCases,
  portfolioItemFromCase,
  buildPortfolio,
  evaluateAndStoreDeadline,
  evaluateAndStoreSourceDrift,
  evaluateAndStoreScenarioDelta
};
