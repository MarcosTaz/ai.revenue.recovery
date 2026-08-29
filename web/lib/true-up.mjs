const cents = (value) => Math.round((value + Number.EPSILON) * 100) / 100;

const isNonnegativeFinite = (value) => Number.isFinite(value) && value >= 0;

export function computeIndirectTrueUp(input) {
  const allocationBase = Number(input.allocationBase);
  const finalRate = Number(input.finalRate);
  const billed = Number(input.billedIndirect);
  const hasCeiling = input.indirectCeilingAmount !== null && input.indirectCeilingAmount !== undefined && input.indirectCeilingAmount !== '';
  const hasFunding = input.remainingFunding !== null && input.remainingFunding !== undefined && input.remainingFunding !== '';
  const ceiling = hasCeiling ? Number(input.indirectCeilingAmount) : null;
  const funding = hasFunding ? Number(input.remainingFunding) : null;

  if (![allocationBase, finalRate, billed].every(isNonnegativeFinite)
      || (ceiling !== null && !isNonnegativeFinite(ceiling))
      || (funding !== null && !isNonnegativeFinite(funding))) {
    return {
      state: 'REQUIRES_REVIEW',
      expectedIndirect: null,
      variance: null,
      explanation: 'Non-finite or negative numeric inputs require explicit credit/adjustment review.',
    };
  }

  const billedRounded = cents(billed);

  if (!input.contractTermsVerified) {
    return { state: 'UNKNOWN', expectedIndirect: null, variance: null, explanation: 'Contract terms or clause applicability are not verified.' };
  }
  if (!input.finalRateSettled) {
    return { state: 'REQUIRES_REVIEW', expectedIndirect: null, variance: null, explanation: 'A proposed or provisional rate cannot create a verified recovery finding.' };
  }
  if (!input.allowabilitySupported || !input.allocabilitySupported) {
    return { state: 'REQUIRES_REVIEW', expectedIndirect: null, variance: null, explanation: 'Allowability and allocability must both be supported.' };
  }

  let expected = cents(allocationBase * finalRate);
  if (ceiling !== null) {
    expected = Math.min(expected, cents(ceiling));
  }
  const variance = cents(expected - billedRounded);

  if (variance > 0 && funding !== null && variance > cents(funding)) {
    return { state: 'REQUIRES_REVIEW', expectedIndirect: expected, variance, explanation: 'Positive variance exceeds verified remaining funding.' };
  }

  if (variance > 0) {
    return { state: 'RECOVERY_CANDIDATE', expectedIndirect: expected, variance, explanation: 'Settled final-rate economics exceed cumulative indirect billings.' };
  }
  if (variance < 0) {
    return { state: 'PAYABLE_CANDIDATE', expectedIndirect: expected, variance, explanation: 'Cumulative indirect billings exceed settled final-rate economics.' };
  }
  return { state: 'NO_VARIANCE', expectedIndirect: expected, variance, explanation: 'Cumulative indirect billings match settled final-rate economics.' };
}
