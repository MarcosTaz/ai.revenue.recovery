'use strict';

const { validateProjectCase, STATUS: PROJECT_STATUS } = require('./project-model');
const { evaluateMiso2026RepaymentApplicability, STATUS: APPLICABILITY } = require('./miso-applicability');
const { evaluatePilotAdmission, OUTCOME: ADMISSION } = require('./pilot-admission');
const { evaluateNetworkUpgradeRepayment } = require('./gridrecover-core');
const { buildRecoveryDossier } = require('./dossier');

function runMiso2026RepaymentCase(input) {
  if (!input || typeof input !== 'object') return { stage: 'INTAKE', status: 'BLOCKED', reasons: ['INPUT_MISSING'] };

  const project = validateProjectCase(input.project);
  if (project.status !== PROJECT_STATUS.VALID) {
    return { stage: 'PROJECT_VALIDATION', status: 'BLOCKED', reasons: project.reasons };
  }

  const applicability = evaluateMiso2026RepaymentApplicability(input.applicability);
  if (applicability.status !== APPLICABILITY.APPLICABLE) {
    return { stage: 'RULE_APPLICABILITY', status: 'BLOCKED', applicability };
  }

  const admissionInput = {
    ...input.admission,
    lane_id: 'MISO_2026_NETWORK_UPGRADE_REPAYMENT',
    jurisdiction: input.project.jurisdiction,
    transmission_provider: input.project.transmission_provider,
    project_scope: 'LARGE_GENERATOR_GT_20MW',
    provider_rule_id: applicability.rule_id,
    provider_applicability_status: applicability.status
  };
  const admission = evaluatePilotAdmission(admissionInput);
  if (admission.outcome !== ADMISSION.PILOT_ADMISSIBLE) {
    return { stage: 'PILOT_ADMISSION', status: 'BLOCKED', admission };
  }

  const evaluation = evaluateNetworkUpgradeRepayment(input.economics_case);
  if (evaluation.status === 'UNKNOWN' || evaluation.status === 'NEEDS_REVIEW') {
    return { stage: 'ECONOMIC_EVALUATION', status: 'REVIEW_REQUIRED', evaluation };
  }

  const dossier = buildRecoveryDossier({
    caseMeta: {
      case_id: input.project.case_id,
      project_id: input.project.project_id,
      customer_id: input.project.customer_id,
      jurisdiction: input.project.jurisdiction,
      transmission_provider: input.project.transmission_provider,
      currency: input.project.currency
    },
    result: evaluation,
    sources: input.dossier_sources,
    calculations: input.calculations || [],
    uncertainties: input.uncertainties || [],
    nextAction: input.next_action
  });

  if (dossier.status === 'DOSSIER_BLOCKED') {
    return { stage: 'DOSSIER', status: 'BLOCKED', dossier };
  }

  return {
    stage: 'COMPLETE_ASSISTED_ANALYSIS',
    status: 'COMPLETE',
    lane_id: 'MISO_2026_NETWORK_UPGRADE_REPAYMENT',
    project_validation: project,
    applicability,
    admission,
    evaluation,
    dossier,
    commercial_truth: {
      customer_case_verified: false,
      recovered_cash_verified: false,
      revenue_received: false
    }
  };
}

module.exports = { runMiso2026RepaymentCase };
