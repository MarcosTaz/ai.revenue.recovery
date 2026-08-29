'use strict';

const assert = require('assert');
const { runMiso2026RepaymentCase } = require('../src/miso-case-runner');

function valid() {
  return {
    project: {
      case_id: 'CASE-MISO-1', customer_id: 'DEV-1', project_id: 'P-1', project_name: 'Synthetic Wind 200 MW',
      jurisdiction: 'US_FEDERAL_FERC', transmission_provider: 'MISO', queue_or_interconnection_id: 'J-1',
      process_stage: 'COMMERCIAL_OPERATION', currency: 'USD', ingested_by_user_id: 'uploader',
      rule_applicability_verified: true, agreement_authority_verified: true,
      rule_reviewer_id: 'review-rule', agreement_reviewer_id: 'review-agreement',
      effective_rule_source: { document_id: 'TARIFF-1', sha256: 'sha256:tariff', locator: 'Attachment X Appendix 6 GIA 110.0.0 Article 11.4.1', document_type: 'TARIFF_OR_RULE', effective_or_execution_date: '2026-02-04', superseded: false },
      executed_agreement_source: { document_id: 'LGIA-1', sha256: 'sha256:lgia', locator: 'Article 11.4.1', document_type: 'EXECUTED_LGIA', effective_or_execution_date: '2026-03-01', superseded: false }
    },
    applicability: {
      jurisdiction: 'US_FEDERAL_FERC', transmission_provider: 'MISO', project_scope: 'LARGE_GENERATOR_GT_20MW',
      project_gia_source_hash: 'sha256:lgia', project_gia_article_locator: 'Article 11.4.1', project_gia_article_11_4_1_match: true,
      provider_tariff_source_hash: 'sha256:tariff', ferc_acceptance_source_hash: 'sha256:order', ferc_acceptance_accession: '20260203-3023',
      project_gia_tariff_record_verified: true, project_gia_tariff_record: '110.0.0', provider_tariff_effective_date: '2026-02-04'
    },
    admission: {
      documents: [
        { type: 'EXECUTED_OR_FILED_LGIA', document_id: 'LGIA-1', sha256: 'sha256:lgia' },
        { type: 'EFFECTIVE_PROVIDER_TARIFF_OR_LGIP', document_id: 'TARIFF-1', sha256: 'sha256:tariff' },
        { type: 'FERC_ACCEPTANCE_ORDER', document_id: 'ORDER-1', sha256: 'sha256:order' },
        { type: 'REPAYABLE_BASIS', document_id: 'FF-1', sha256: 'sha256:ff' },
        { type: 'PAYMENT_OR_SECURITY_LEDGER', document_id: 'PAY-1', sha256: 'sha256:pay' },
        { type: 'TRIGGER_EVENT_EVIDENCE', document_id: 'COD-1', sha256: 'sha256:cod' }
      ],
      rule_applicability_reviewer_independent: true, agreement_authority_reviewer_independent: true,
      customer_authorized_analysis: true, tenant_workspace_ready: true
    },
    economics_case: {
      jurisdiction: 'US_FEDERAL_FERC', project_scope: 'LARGE_GENERATOR_GT_20MW',
      agreement: { executed_lgia_id: 'LGIA-1', article_11_4_1_match: true, source_document_hash: 'sha256:lgia', source_locator: 'Article 11.4.1', superseded: false, trigger_satisfied: true, repayment_schedule_supported: true },
      economics: { network_upgrade_amount_paid: 5000000, repayable_network_upgrade_amount: 3500000, amounts_already_refunded: 500000, repayments_received: 1000000, currency: 'USD' },
      evidence: { payment_source_hash: 'sha256:pay', payment_matches_project: true, payment_is_network_upgrade: true, repayable_basis_source_hash: 'sha256:ff', repayable_basis_locator: 'Attachment FF allocation', repayable_basis_verified: true }
    },
    dossier_sources: [
      { document_id: 'LGIA-1', sha256: 'sha256:lgia', locator: 'Article 11.4.1' },
      { document_id: 'TARIFF-1', sha256: 'sha256:tariff', locator: 'Attachment X Appendix 6 GIA 110.0.0' },
      { document_id: 'ORDER-1', sha256: 'sha256:order', locator: 'ER26-677-000 Appendix' },
      { document_id: 'FF-1', sha256: 'sha256:ff', locator: 'Attachment FF allocation' },
      { document_id: 'PAY-1', sha256: 'sha256:pay', locator: 'payment ledger' }
    ],
    calculations: [{ formula: '3500000-500000-1000000', result: 2000000 }],
    uncertainties: ['current payment due date still requires project-specific confirmation'],
    next_action: 'Reviewer confirms current schedule/offsets before customer or counterparty action.'
  };
}

{
  const r = runMiso2026RepaymentCase(valid());
  assert.equal(r.status, 'COMPLETE');
  assert.equal(r.stage, 'COMPLETE_ASSISTED_ANALYSIS');
  assert.equal(r.evaluation.candidate_amount, 2000000);
  assert.equal(r.evaluation.verified_total_network_upgrade_paid, 5000000);
  assert.equal(r.evaluation.verified_repayable_base, 3500000);
  assert.equal(r.dossier.finding.candidate_value, 2000000);
  assert.equal(r.dossier.finding.verified_recovery, false);
  assert.equal(r.commercial_truth.customer_case_verified, false);
}

{
  const i = valid(); i.applicability.project_gia_tariff_record = '108.0.0';
  const r = runMiso2026RepaymentCase(i);
  assert.equal(r.stage, 'RULE_APPLICABILITY');
  assert.equal(r.status, 'BLOCKED');
}

{
  const i = valid(); i.admission.documents = i.admission.documents.filter(d => d.type !== 'REPAYABLE_BASIS');
  const r = runMiso2026RepaymentCase(i);
  assert.equal(r.stage, 'PILOT_ADMISSION');
  assert.equal(r.status, 'BLOCKED');
}

{
  const i = valid(); i.economics_case.evidence.repayable_basis_verified = false;
  const r = runMiso2026RepaymentCase(i);
  assert.equal(r.stage, 'ECONOMIC_EVALUATION');
  assert.equal(r.status, 'REVIEW_REQUIRED');
}

{
  const i = valid(); i.project.agreement_reviewer_id = 'uploader';
  const r = runMiso2026RepaymentCase(i);
  assert.equal(r.stage, 'PROJECT_VALIDATION');
  assert.equal(r.status, 'BLOCKED');
}

console.log('GRIDRECOVER MISO end-to-end runner: 5/5 PASS');
