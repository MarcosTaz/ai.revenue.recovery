'use strict';

const assert = require('assert');
const { STATUS, evaluateSuccessFeeEligibility, issueInvoice, verifyInvoicePayment } = require('../src/billing-lifecycle');

const engagement = {
  signed: true,
  terms_evidence_sha256: 'a'.repeat(64),
  signed_at: '2026-09-01T10:00:00Z',
  success_fee_rate: 0.15,
  currency: 'USD'
};
const recovery = {
  stage: 'PAYMENT_VERIFIED',
  recovered_cash_verified: true,
  incrementality_verified: true,
  incremental_verified_amount: 1000000,
  currency: 'USD'
};

const eligible = evaluateSuccessFeeEligibility({ engagement, recovery });
assert.equal(eligible.status, STATUS.INVOICE_ELIGIBLE);
assert.equal(eligible.success_fee_amount, 150000);

{
  const i = { ...recovery, incrementality_verified: false };
  const r = evaluateSuccessFeeEligibility({ engagement, recovery: i });
  assert.equal(r.status, STATUS.NOT_ELIGIBLE);
  assert.equal(r.success_fee_amount, null);
}
{
  const e = { ...engagement, signed: false };
  assert.equal(evaluateSuccessFeeEligibility({ engagement: e, recovery }).status, STATUS.NOT_ELIGIBLE);
}
{
  const e = { ...engagement, success_fee_rate: 1.1 };
  assert.equal(evaluateSuccessFeeEligibility({ engagement: e, recovery }).status, STATUS.NOT_ELIGIBLE);
}
{
  const invoice = issueInvoice({ eligibility: eligible, invoice_id: 'INV-001', issued_at: '2026-09-05T10:00:00Z', invoice_evidence_sha256: 'b'.repeat(64) });
  assert.equal(invoice.status, STATUS.INVOICED);
  assert.equal(invoice.revenue_received, false);
  assert.equal(invoice.amount, 150000);

  const notPaid = verifyInvoicePayment({ invoice, payment: { verified: false, amount: 150000, currency: 'USD', value_date: '2026-09-06', evidence_sha256: 'c'.repeat(64), payment_reference: 'P1', matches_invoice: true } });
  assert.equal(notPaid.status, STATUS.INVOICED);
  assert.equal(notPaid.revenue_received, false);

  const paid = verifyInvoicePayment({ invoice, payment: { verified: true, amount: 150000, currency: 'USD', value_date: '2026-09-06', evidence_sha256: 'c'.repeat(64), payment_reference: 'P1', matches_invoice: true } });
  assert.equal(paid.status, STATUS.REVENUE_RECEIVED);
  assert.equal(paid.revenue_received_amount, 150000);
}
{
  const invoice = issueInvoice({ eligibility: eligible, invoice_id: 'INV-002', issued_at: '2026-09-05T10:00:00Z', invoice_evidence_sha256: 'b'.repeat(64) });
  const wrong = verifyInvoicePayment({ invoice, payment: { verified: true, amount: 149999, currency: 'USD', value_date: '2026-09-06', evidence_sha256: 'c'.repeat(64), payment_reference: 'P2', matches_invoice: true } });
  assert.equal(wrong.status, STATUS.INVOICED);
  assert.equal(wrong.revenue_received, false);
}
assert.throws(() => issueInvoice({ eligibility: { status: STATUS.NOT_ELIGIBLE } }), /INVOICE_NOT_ELIGIBLE/);

console.log('GRIDRECOVER billing lifecycle: 12/12 PASS');
