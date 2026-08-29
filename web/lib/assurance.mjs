const validAmount = (value) => value === null || value === undefined || (Number.isFinite(Number(value)) && Number(value) >= 0);

export function computeAssuranceSnapshot(input) {
  const expected = input.supportedExpectedBilling;
  const billed = input.cumulativeBilled;
  const paid = input.cumulativePaid;

  if (![expected, billed, paid].every(validAmount)) {
    return { state: 'REQUIRES_REVIEW', explanation: 'Negative or non-finite economic inputs require review.' };
  }
  if (input.expresslyUnallowable) {
    return {
      state: 'NOT_ALLOWABLE',
      earnedSupported: null,
      billed: billed == null ? null : Number(billed),
      paid: paid == null ? null : Number(paid),
      supportedUnbilled: null,
      explanation: 'An expressly unallowable item cannot become supported earned revenue.',
    };
  }
  if (!input.evidenceComplete || expected == null || billed == null) {
    return { state: 'UNKNOWN', explanation: 'Expected economics and cumulative billing require complete evidence.' };
  }
  if (![input.contractTermsSupported, input.allowabilitySupported, input.allocabilitySupported, input.finalRateSettledWhenRequired].every(Boolean)) {
    return {
      state: 'REQUIRES_REVIEW',
      earnedSupported: Number(expected),
      billed: Number(billed),
      paid: paid == null ? null : Number(paid),
      explanation: 'Contract, cost or final-rate prerequisites are not fully supported.',
    };
  }

  const earnedValue = Number(expected);
  const billedValue = Number(billed);
  const paidValue = paid == null ? null : Number(paid);

  if (!input.fundingSupported || !input.ceilingSupported || input.proceduralRisk) {
    return {
      state: 'AT_RISK',
      earnedSupported: earnedValue,
      billed: billedValue,
      paid: paidValue,
      supportedUnbilled: null,
      explanation: 'Funding, ceiling or procedural risk prevents promotion to supported unbilled revenue.',
    };
  }
  if (billedValue > earnedValue) {
    return {
      state: 'PAYABLE_EXPOSURE',
      earnedSupported: earnedValue,
      billed: billedValue,
      paid: paidValue,
      payableExposure: billedValue - earnedValue,
      explanation: 'Cumulative billing exceeds supported expected economics.',
    };
  }
  if (earnedValue > billedValue) {
    return {
      state: 'SUPPORTED_UNBILLED',
      earnedSupported: earnedValue,
      billed: billedValue,
      paid: paidValue,
      supportedUnbilled: earnedValue - billedValue,
      explanation: 'Supported expected economics exceed cumulative billing after current deterministic gates.',
    };
  }
  if (paidValue == null) {
    return {
      state: 'UNKNOWN',
      earnedSupported: earnedValue,
      billed: billedValue,
      paid: null,
      explanation: 'Billing is current but payment evidence is incomplete.',
    };
  }
  if (paidValue < billedValue) {
    return {
      state: 'PAYMENT_SHORTFALL',
      earnedSupported: earnedValue,
      billed: billedValue,
      paid: paidValue,
      paymentShortfall: billedValue - paidValue,
      explanation: 'Verified payments are below supported cumulative billing.',
    };
  }
  if (paidValue > billedValue) {
    return {
      state: 'REQUIRES_REVIEW',
      earnedSupported: earnedValue,
      billed: billedValue,
      paid: paidValue,
      payableExposure: paidValue - billedValue,
      explanation: 'Verified payments exceed cumulative billing and require cash-application/refund review.',
    };
  }
  return {
    state: 'CURRENT',
    earnedSupported: earnedValue,
    billed: billedValue,
    paid: paidValue,
    supportedUnbilled: 0,
    paymentShortfall: 0,
    payableExposure: 0,
    explanation: 'Supported expected economics, cumulative billing and verified payment are aligned.',
  };
}
