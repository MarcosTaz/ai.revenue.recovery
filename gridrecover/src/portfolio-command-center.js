'use strict';

const PRIORITY = Object.freeze({ CRITICAL: 4, HIGH: 3, MEDIUM: 2, NORMAL: 1, UNKNOWN: 0 });

function nonEmpty(v) { return typeof v === 'string' && v.trim().length > 0; }
function finiteNonNegative(v) { return Number.isFinite(v) && v >= 0; }

function addMoney(bucket, nature, currency, amount) {
  if (!bucket[nature]) bucket[nature] = {};
  bucket[nature][currency] = (bucket[nature][currency] || 0) + amount;
}

function classifyPriority(item) {
  const reasons = [];
  const deadlineStatus = item.deadline?.status || 'UNKNOWN';
  const sourceHealth = item.source_health || 'UNKNOWN';
  const candidateActive = item.finding?.status === 'SUPPORTED_CANDIDATE';

  if (sourceHealth === 'DRIFT_DETECTED' && candidateActive) {
    return { level: 'CRITICAL', reasons: ['SOURCE_DRIFT_INVALIDATES_ACTIVE_CANDIDATE'] };
  }
  if (deadlineStatus === 'OVERDUE') {
    return { level: 'CRITICAL', reasons: ['SOURCE_BOUND_DEADLINE_OVERDUE'] };
  }
  if (deadlineStatus === 'DUE_TODAY') {
    return { level: 'CRITICAL', reasons: ['SOURCE_BOUND_DEADLINE_DUE_TODAY'] };
  }
  if (deadlineStatus === 'DUE_SOON' && candidateActive) {
    return { level: 'HIGH', reasons: ['CANDIDATE_WITH_NEAR_DEADLINE'] };
  }
  if (sourceHealth === 'UNKNOWN') reasons.push('SOURCE_HEALTH_UNKNOWN');
  if (item.admission_status === 'SOURCE_REQUIRED') reasons.push('SOURCE_REQUIRED');
  if (item.admission_status === 'REVIEW_REQUIRED') reasons.push('REVIEW_REQUIRED');
  if (candidateActive) reasons.push('SUPPORTED_CANDIDATE_REQUIRES_ACTION');

  if (reasons.includes('SOURCE_HEALTH_UNKNOWN') || reasons.includes('SOURCE_REQUIRED')) {
    return { level: 'HIGH', reasons };
  }
  if (reasons.includes('REVIEW_REQUIRED') || candidateActive) {
    return { level: 'MEDIUM', reasons };
  }
  return { level: 'NORMAL', reasons: reasons.length ? reasons : ['NO_IMMEDIATE_EXCEPTION'] };
}

function buildPortfolioCommandCenter(items) {
  if (!Array.isArray(items)) return { status: 'UNKNOWN', reasons: ['PORTFOLIO_INPUT_INVALID'] };

  const errors = [];
  const monetary = {};
  const deadline_counts = {};
  const source_health_counts = {};
  const rows = [];
  let verifiedRecoveryCount = 0;

  for (const [index, item] of items.entries()) {
    if (!item || !nonEmpty(item.case_id)) { errors.push(`ITEM_${index}_CASE_ID_MISSING`); continue; }
    if (!nonEmpty(item.project_id)) errors.push(`ITEM_${index}_PROJECT_ID_MISSING`);

    if (item.finding?.status === 'SUPPORTED_CANDIDATE') {
      if (!finiteNonNegative(item.finding.value) || !nonEmpty(item.finding.currency) || !nonEmpty(item.finding.value_nature)) {
        errors.push(`ITEM_${index}_CANDIDATE_INVALID`);
      } else {
        addMoney(monetary, item.finding.value_nature, item.finding.currency, item.finding.value);
      }
    }

    if (item.verified_recovery) {
      const vr = item.verified_recovery;
      if (vr.payment_verified === true && finiteNonNegative(vr.amount) && nonEmpty(vr.currency)) {
        addMoney(monetary, 'VERIFIED_RECOVERED_CASH', vr.currency, vr.amount);
        verifiedRecoveryCount += 1;
      } else if (vr.payment_verified === true) {
        errors.push(`ITEM_${index}_VERIFIED_RECOVERY_INVALID`);
      }
    }

    const deadlineStatus = item.deadline?.status || 'UNKNOWN';
    deadline_counts[deadlineStatus] = (deadline_counts[deadlineStatus] || 0) + 1;
    const sourceHealth = item.source_health || 'UNKNOWN';
    source_health_counts[sourceHealth] = (source_health_counts[sourceHealth] || 0) + 1;
    const priority = classifyPriority(item);

    rows.push({
      case_id: item.case_id,
      project_id: item.project_id || null,
      project_name: item.project_name || null,
      priority: priority.level,
      priority_reasons: priority.reasons,
      finding_status: item.finding?.status || 'UNKNOWN',
      value_nature: item.finding?.value_nature || null,
      candidate_value: item.finding?.status === 'SUPPORTED_CANDIDATE' ? item.finding.value : null,
      currency: item.finding?.status === 'SUPPORTED_CANDIDATE' ? item.finding.currency : null,
      deadline_status: deadlineStatus,
      days_remaining: item.deadline?.days_remaining ?? null,
      source_health: sourceHealth,
      admission_status: item.admission_status || 'UNKNOWN',
      next_action: item.next_action || null
    });
  }

  if (errors.length) return { status: 'UNKNOWN', reasons: [...new Set(errors)] };

  rows.sort((a, b) => {
    const priorityDelta = PRIORITY[b.priority] - PRIORITY[a.priority];
    if (priorityDelta) return priorityDelta;
    const da = a.days_remaining == null ? Number.POSITIVE_INFINITY : a.days_remaining;
    const db = b.days_remaining == null ? Number.POSITIVE_INFINITY : b.days_remaining;
    return da - db;
  });

  return {
    status: 'VALID',
    case_count: rows.length,
    monetary,
    verified_recovery_case_count: verifiedRecoveryCount,
    deadline_counts,
    source_health_counts,
    priority_counts: rows.reduce((acc, row) => { acc[row.priority] = (acc[row.priority] || 0) + 1; return acc; }, {}),
    rows,
    truth_boundary: {
      candidate_totals_are_not_verified_recovery: true,
      security_release_is_not_cash: true,
      mixed_currencies_are_never_summed: true,
      priority_is_rule_based_and_explainable: true
    }
  };
}

module.exports = { PRIORITY, classifyPriority, buildPortfolioCommandCenter };
