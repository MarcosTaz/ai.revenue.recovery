'use strict';

const STATUS = Object.freeze({ VALID: 'VALID', UNKNOWN: 'UNKNOWN' });
const ALLOWED_TYPES = new Set(['NETWORK_UPGRADE_ASSIGNMENT', 'SECURITY_REQUIRED', 'REPAYABLE_BASIS', 'DEPOSIT', 'WITHDRAWAL_PENALTY']);

function nonEmpty(v) { return typeof v === 'string' && v.trim().length > 0; }
function finite(v) { return Number.isFinite(v) && v >= 0; }

function validateSnapshot(snapshot, label) {
  const reasons = [];
  if (!snapshot || typeof snapshot !== 'object') return [`${label}_SNAPSHOT_MISSING`];
  if (!nonEmpty(snapshot.snapshot_id)) reasons.push(`${label}_SNAPSHOT_ID_MISSING`);
  if (!nonEmpty(snapshot.source_sha256)) reasons.push(`${label}_SOURCE_SHA256_MISSING`);
  if (!nonEmpty(snapshot.source_document_id)) reasons.push(`${label}_SOURCE_DOCUMENT_ID_MISSING`);
  if (!nonEmpty(snapshot.source_locator)) reasons.push(`${label}_SOURCE_LOCATOR_MISSING`);
  if (snapshot.source_authority_verified !== true) reasons.push(`${label}_SOURCE_AUTHORITY_NOT_VERIFIED`);
  if (!Array.isArray(snapshot.lines)) reasons.push(`${label}_LINES_INVALID`);
  return reasons;
}

function normalizeLines(snapshot, label) {
  const reasons = [];
  const map = new Map();
  for (const [index, line] of snapshot.lines.entries()) {
    const prefix = `${label}_LINE_${index}`;
    if (!line || !nonEmpty(line.component_id)) { reasons.push(`${prefix}_COMPONENT_ID_MISSING`); continue; }
    if (!ALLOWED_TYPES.has(line.value_type)) reasons.push(`${prefix}_VALUE_TYPE_UNSUPPORTED`);
    if (!nonEmpty(line.currency)) reasons.push(`${prefix}_CURRENCY_MISSING`);
    if (!finite(line.amount)) reasons.push(`${prefix}_AMOUNT_INVALID`);
    if (!nonEmpty(line.source_sha256)) reasons.push(`${prefix}_SOURCE_SHA256_MISSING`);
    if (!nonEmpty(line.source_locator)) reasons.push(`${prefix}_SOURCE_LOCATOR_MISSING`);
    const key = `${line.value_type}\u0000${line.component_id}\u0000${line.currency}`;
    if (map.has(key)) reasons.push(`${prefix}_DUPLICATE_COMPONENT`);
    else map.set(key, { ...line });
  }
  return { map, reasons };
}

function evaluateScenarioDelta(input) {
  const reasons = [];
  if (!input || typeof input !== 'object') return { status: STATUS.UNKNOWN, reasons: ['INPUT_MISSING'] };
  if (!nonEmpty(input.case_id)) reasons.push('CASE_ID_MISSING');
  reasons.push(...validateSnapshot(input.baseline, 'BASELINE'));
  reasons.push(...validateSnapshot(input.current, 'CURRENT'));
  if (reasons.length) return { status: STATUS.UNKNOWN, reasons: [...new Set(reasons)] };

  const baseline = normalizeLines(input.baseline, 'BASELINE');
  const current = normalizeLines(input.current, 'CURRENT');
  reasons.push(...baseline.reasons, ...current.reasons);
  if (reasons.length) return { status: STATUS.UNKNOWN, reasons: [...new Set(reasons)] };

  const keys = new Set([...baseline.map.keys(), ...current.map.keys()]);
  const lines = [];
  const summary = {};

  function addSummary(type, currency, delta) {
    if (!summary[type]) summary[type] = {};
    summary[type][currency] = (summary[type][currency] || 0) + delta;
  }

  for (const key of keys) {
    const before = baseline.map.get(key) || null;
    const after = current.map.get(key) || null;
    const sample = after || before;
    const beforeAmount = before ? before.amount : 0;
    const afterAmount = after ? after.amount : 0;
    const delta = afterAmount - beforeAmount;
    addSummary(sample.value_type, sample.currency, delta);
    lines.push({
      component_id: sample.component_id,
      value_type: sample.value_type,
      currency: sample.currency,
      baseline_amount: beforeAmount,
      current_amount: afterAmount,
      delta,
      change_type: !before ? 'ADDED' : !after ? 'REMOVED' : delta === 0 ? 'UNCHANGED' : delta > 0 ? 'INCREASED' : 'DECREASED',
      baseline_source: before ? { sha256: before.source_sha256, locator: before.source_locator } : null,
      current_source: after ? { sha256: after.source_sha256, locator: after.source_locator } : null
    });
  }

  return {
    status: STATUS.VALID,
    case_id: input.case_id,
    baseline_snapshot_id: input.baseline.snapshot_id,
    current_snapshot_id: input.current.snapshot_id,
    summary,
    lines: lines.sort((a, b) => `${a.value_type}:${a.component_id}`.localeCompare(`${b.value_type}:${b.component_id}`)),
    interpretation: {
      negative_security_required_delta_means_less_security_required_not_cash_recovery: true,
      negative_network_upgrade_assignment_delta_means_lower_assignment_not_verified_refund: true,
      repayable_basis_delta_requires_recomputation_of_repayment_candidate: true
    }
  };
}

module.exports = { STATUS, ALLOWED_TYPES, evaluateScenarioDelta };
