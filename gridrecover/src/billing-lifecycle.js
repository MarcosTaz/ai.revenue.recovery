'use strict';

const STATUS = Object.freeze({
  NOT_ELIGIBLE: 'NOT_ELIGIBLE',
  INVOICE_ELIGIBLE: 'INVOICE_ELIGIBLE',
  INVOICED: 'INVOICED',
  REVENUE_RECEIVED: 'REVENUE_RECEIVED'
});

function nonEmpty(v) { return typeof v === 'string' && v.trim().length > 0; }
function money(v) { return Number.isFinite(v) && v >= 0; }
function validDate(v) { return nonEmpty(v) && !Number.isNaN(Date.parse(v)); }

function evaluateSuccessFeeEligibility({ engagement, recovery }) {
  const reasons = [];
  if (!engagement || engagement.signed !== true) reasons.push('SIGNED_ENGAGEMENT_REQUIRED');
  if (!engagement || !nonEmpty(engagement.terms_evidence_sha256)) reasons.push('ENGAGEMENT_TERMS_EVIDENCE_MISSING');
  if (!engagement || !validDate(engagement.signed_at)) reasons.push('ENGAGEMENT_SIGNED_AT_INVALID');
  if (!engagement || !Number.isFinite(engagement.success_fee_rate) || engagement.success_fee_rate < 0 || engagement.success_fee_rate > 1) reasons.push('SUCCESS_FEE_RATE_INVALID');
  if (!engagement || !nonEmpty(engagement.currency)) reasons.push('ENGAGEMENT_CURRENCY_MISSING');
  if (!recovery || recovery.stage !== 'PAYMENT_VERIFIED' || recovery.recovered_cash_verified !== true) reasons.push('VERIFIED_RECOVERY_REQUIRED');
  if (!recovery || recovery.incrementality_verified !== true || !money(recovery.incremental_verified_amount)) reasons.push('VERIFIED_INCREMENTALITY_REQUIRED');
  if (engagement && recovery && engagement.currency !== recovery.currency) reasons.push('CURRENCY_MISMATCH');

  if (reasons.length) return { status: STATUS.NOT_ELIGIBLE, success_fee_amount: null, reasons };
  const fee = Math.round(recovery.incremental_verified_amount * engagement.success_fee_rate * 100) / 100;
  return {
    status: STATUS.INVOICE_ELIGIBLE,
    success_fee_amount: fee,
    currency: engagement.currency,
    fee_basis: {
      verified_incremental_recovery: recovery.incremental_verified_amount,
      rate: engagement.success_fee_rate
    },
    reasons: ['SIGNED_TERMS_AND_VERIFIED_INCREMENTALITY']
  };
}

function issueInvoice({ eligibility, invoice_id, issued_at, invoice_evidence_sha256 }) {
  if (!eligibility || eligibility.status !== STATUS.INVOICE_ELIGIBLE) throw new Error('INVOICE_NOT_ELIGIBLE');
  if (!nonEmpty(invoice_id) || !validDate(issued_at) || !nonEmpty(invoice_evidence_sha256)) throw new Error('INVOICE_EVIDENCE_INCOMPLETE');
  return {
    status: STATUS.INVOICED,
    invoice_id,
    issued_at,
    invoice_evidence_sha256,
    amount: eligibility.success_fee_amount,
    currency: eligibility.currency,
    fee_basis: eligibility.fee_basis,
    revenue_received: false
  };
}

function verifyInvoicePayment({ invoice, payment }) {
  if (!invoice || invoice.status !== STATUS.INVOICED) throw new Error('INVOICE_REQUIRED');
  const reasons = [];
  if (!payment || payment.verified !== true) reasons.push('INVOICE_PAYMENT_NOT_VERIFIED');
  if (!payment || !money(payment.amount) || payment.amount !== invoice.amount) reasons.push('INVOICE_PAYMENT_AMOUNT_MISMATCH');
  if (!payment || payment.currency !== invoice.currency) reasons.push('INVOICE_PAYMENT_CURRENCY_MISMATCH');
  if (!payment || !validDate(payment.value_date)) reasons.push('INVOICE_PAYMENT_DATE_INVALID');
  if (!payment || !nonEmpty(payment.evidence_sha256) || !nonEmpty(payment.payment_reference)) reasons.push('INVOICE_PAYMENT_EVIDENCE_MISSING');
  if (!payment || payment.matches_invoice !== true) reasons.push('INVOICE_PAYMENT_MATCH_NOT_VERIFIED');

  if (reasons.length) return { ...invoice, status: STATUS.INVOICED, revenue_received: false, reasons };
  return {
    ...invoice,
    status: STATUS.REVENUE_RECEIVED,
    revenue_received: true,
    revenue_received_amount: payment.amount,
    revenue_value_date: payment.value_date,
    payment_reference: payment.payment_reference,
    payment_evidence_sha256: payment.evidence_sha256,
    reasons: ['INVOICE_PAYMENT_VERIFIED']
  };
}

module.exports = { STATUS, evaluateSuccessFeeEligibility, issueInvoice, verifyInvoicePayment };
