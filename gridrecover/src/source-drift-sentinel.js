'use strict';

const STATUS = Object.freeze({
  STABLE: 'STABLE',
  DRIFT_DETECTED: 'DRIFT_DETECTED',
  UNKNOWN: 'UNKNOWN'
});

function nonEmpty(v) { return typeof v === 'string' && v.trim().length > 0; }

function evaluateSourceDrift(previous, current) {
  const reasons = [];
  if (!previous || !current) return { status: STATUS.UNKNOWN, invalidate_findings: true, reasons: ['SOURCE_SNAPSHOT_MISSING'] };
  for (const [label, source] of [['PREVIOUS', previous], ['CURRENT', current]]) {
    if (!nonEmpty(source.document_id)) reasons.push(`${label}_DOCUMENT_ID_MISSING`);
    if (!nonEmpty(source.sha256)) reasons.push(`${label}_SHA256_MISSING`);
    if (!nonEmpty(source.source_type)) reasons.push(`${label}_SOURCE_TYPE_MISSING`);
    if (!nonEmpty(source.effective_version)) reasons.push(`${label}_EFFECTIVE_VERSION_MISSING`);
  }
  if (reasons.length) return { status: STATUS.UNKNOWN, invalidate_findings: true, reasons };

  const changes = [];
  if (previous.document_id !== current.document_id) changes.push('DOCUMENT_ID_CHANGED');
  if (previous.sha256 !== current.sha256) changes.push('SOURCE_BYTES_CHANGED');
  if (previous.effective_version !== current.effective_version) changes.push('EFFECTIVE_VERSION_CHANGED');
  if ((previous.effective_date || null) !== (current.effective_date || null)) changes.push('EFFECTIVE_DATE_CHANGED');
  if ((previous.locator || null) !== (current.locator || null)) changes.push('LOCATOR_CHANGED');
  if ((previous.authority_status || null) !== (current.authority_status || null)) changes.push('AUTHORITY_STATUS_CHANGED');

  if (!changes.length) {
    return {
      status: STATUS.STABLE,
      invalidate_findings: false,
      requires_re_review: false,
      changes: []
    };
  }

  return {
    status: STATUS.DRIFT_DETECTED,
    invalidate_findings: true,
    requires_re_review: true,
    changes,
    action: 'Re-bind provider rule/agreement applicability and recompute all dependent findings before customer action.'
  };
}

function evaluateDependencySet(previousSources, currentSources) {
  if (!Array.isArray(previousSources) || !Array.isArray(currentSources)) {
    return { status: STATUS.UNKNOWN, invalidate_findings: true, reasons: ['DEPENDENCY_SET_INVALID'] };
  }
  const currentByType = new Map(currentSources.map(s => [s.source_type, s]));
  const results = [];
  let invalidate = false;

  for (const previous of previousSources) {
    const current = currentByType.get(previous.source_type);
    const result = evaluateSourceDrift(previous, current);
    results.push({ source_type: previous.source_type, ...result });
    if (result.invalidate_findings) invalidate = true;
  }

  for (const current of currentSources) {
    if (!previousSources.some(p => p.source_type === current.source_type)) {
      results.push({ source_type: current.source_type, status: STATUS.DRIFT_DETECTED, invalidate_findings: true, requires_re_review: true, changes: ['NEW_DEPENDENCY_SOURCE'] });
      invalidate = true;
    }
  }

  return {
    status: invalidate ? STATUS.DRIFT_DETECTED : STATUS.STABLE,
    invalidate_findings: invalidate,
    results
  };
}

module.exports = { STATUS, evaluateSourceDrift, evaluateDependencySet };
