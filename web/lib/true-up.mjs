const cents = (value) => Math.round((value + Number.EPSILON) * 100) / 100;

export function computeIndirectTrueUp(input) {
  const billed = cents(Number(input.billedIndirect || 0));

  if (!input.contractTermsVerified) {
    return { state: 'UNKNOWN', expectedIndirect: null, variance: null, explanation: 'Contract terms or clause applicability are not verified.' };
  }
  if (!input.finalRateSettled) {
    return { state: 'REQUIRES_REVIEW', expectedIndirect: null, variance: null, explanation: 'A proposed or provisional rate cannot create a verified recovery finding.' };
  }
  if (!input.allowabilitySupported || !input.allocabilitySupported) {
    return { state: 'REQUIRES_REVIEW', expectedIndirect: null, variance: null, explanation: 'Allowability and allocability must both be supported.' };
  }

  let expected = cents(Number(input.allocationBase) * Number(input.finalRate));
  if (input.indirectCeilingAmount !== null && input.indirectCeilingAmount !== undefined && input.indirectCeilingAmount !== '') {
    expected = Math.min(expected, cents(Number(input.indirectCeilingAmount)));
  }
  const variance = cents(expected - billed);

  if (variance > 0 && input.remainingFunding !== null && input.remainingFunding !== undefined && input.remainingFunding !== '') {
    const funding = cents(Number(input.remainingFunding));
    if (variance > funding) {
      return { state: 'REQUIRES_REVIEW', expectedIndirect: expected, variance, explanation: 'Positive variance exceeds verified remaining funding.' };
    }
  }

  if (variance > 0) {
    return { state: 'RECOVERY_CANDIDATE', expectedIndirect: expected, variance, explanation: 'Settled final-rate economics exceed cumulative indirect billings.' };
  }
  if (variance < 0) {
    return { state: 'PAYABLE_CANDIDATE', expectedIndirect: expected, variance, explanation: 'Cumulative indirect billings exceed settled final-rate economics.' };
  }
  return { state: 'NO_VARIANCE', expectedIndirect: expected, variance, explanation: 'Cumulative indirect billings match settled final-rate economics.' };
}
