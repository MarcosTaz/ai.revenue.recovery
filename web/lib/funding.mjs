const finiteNonnegative = (value) => Number.isFinite(value) && value >= 0;

export function evaluateFundingSafeguard(input) {
  const clause = input.clause ?? null;
  const incurred = Number(input.costsIncurred);
  const projectedNext = Number(input.expectedNextNoticeWindowCosts);
  const thresholdPercent = Number(input.noticeThresholdPercent ?? 0.75);
  const noticeWindowDays = Number(input.noticeWindowDays ?? 60);

  if (!['52.232-20', '52.232-22'].includes(clause)) {
    return { state: 'UNKNOWN', automaticRecoveryAllowed: false, explanation: 'No supported funding clause is evidenced.' };
  }
  if (![incurred, projectedNext, thresholdPercent, noticeWindowDays].every(Number.isFinite)
      || incurred < 0 || projectedNext < 0
      || thresholdPercent < 0.75 || thresholdPercent > 0.85
      || noticeWindowDays < 30 || noticeWindowDays > 90) {
    return { state: 'REQUIRES_REVIEW', automaticRecoveryAllowed: false, explanation: 'Funding inputs or notice terms are outside the supported evidenced range.' };
  }

  const limitRaw = clause === '52.232-20' ? input.estimatedCost : input.allottedFunds;
  if (limitRaw === null || limitRaw === undefined || limitRaw === '') {
    return { state: 'UNKNOWN', automaticRecoveryAllowed: false, explanation: clause === '52.232-20' ? 'Estimated cost is required.' : 'Actually allotted funds are required.' };
  }
  const limit = Number(limitRaw);
  if (!finiteNonnegative(limit)) {
    return { state: 'REQUIRES_REVIEW', automaticRecoveryAllowed: false, explanation: 'The evidenced cost/funding limit must be finite and nonnegative.' };
  }

  const projected = incurred + projectedNext;
  const threshold = limit * thresholdPercent;
  if (incurred > limit) {
    return {
      state: clause === '52.232-20' ? 'EXCESS_COST_REVIEW_REQUIRED' : 'FUNDING_EXHAUSTED_REVIEW_REQUIRED',
      verifiedLimit: limit,
      projectedCostAtNoticeWindow: projected,
      thresholdAmount: threshold,
      automaticRecoveryAllowed: false,
      explanation: 'Costs exceed the evidenced contractual limit. Written Contracting Officer action may be material; no automatic receivable is created.',
    };
  }
  if (projected >= threshold) {
    return {
      state: 'NOTICE_THRESHOLD_REACHED',
      verifiedLimit: limit,
      projectedCostAtNoticeWindow: projected,
      thresholdAmount: threshold,
      automaticRecoveryAllowed: false,
      explanation: 'The evidenced notice threshold is met. Preserve notice evidence; do not infer additional funding or reimbursement.',
    };
  }
  return {
    state: 'WITHIN_VERIFIED_LIMIT',
    verifiedLimit: limit,
    projectedCostAtNoticeWindow: projected,
    thresholdAmount: threshold,
    automaticRecoveryAllowed: false,
    explanation: 'Current plus projected costs remain below the evidenced notice threshold.',
  };
}
