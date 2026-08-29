'use strict';

function nonEmpty(v) { return typeof v === 'string' && v.trim().length > 0; }

function buildRecoveryDossier({ caseMeta, result, sources = [], calculations = [], uncertainties = [], nextAction }) {
  const errors = [];
  if (!caseMeta || !nonEmpty(caseMeta.case_id)) errors.push('CASE_ID_MISSING');
  if (!caseMeta || !nonEmpty(caseMeta.project_id)) errors.push('PROJECT_ID_MISSING');
  if (!caseMeta || !nonEmpty(caseMeta.customer_id)) errors.push('CUSTOMER_ID_MISSING');
  if (!caseMeta || !nonEmpty(caseMeta.jurisdiction)) errors.push('JURISDICTION_MISSING');
  if (!caseMeta || !nonEmpty(caseMeta.transmission_provider)) errors.push('TRANSMISSION_PROVIDER_MISSING');
  if (!result || !nonEmpty(result.status)) errors.push('RESULT_MISSING');
  if (!Array.isArray(sources) || sources.length === 0) errors.push('SOURCE_CHAIN_MISSING');
  if (!Array.isArray(calculations)) errors.push('CALCULATIONS_INVALID');
  if (!nonEmpty(nextAction)) errors.push('NEXT_ACTION_MISSING');

  for (const [index, s] of sources.entries()) {
    if (!s || !nonEmpty(s.document_id) || !nonEmpty(s.sha256) || !nonEmpty(s.locator)) {
      errors.push(`SOURCE_${index}_INCOMPLETE`);
    }
  }

  if (errors.length) return { status: 'DOSSIER_BLOCKED', errors: [...new Set(errors)] };

  const supportedCandidate = result.status === 'SUPPORTED_CANDIDATE';
  const value = result.cash_refund_candidate ?? result.security_release_candidate ?? result.candidate_amount ?? null;
  const valueNature = result.candidate_type || (result.candidate_amount != null ? 'CANDIDATE_REPAYMENT' : null);

  return {
    dossier_version: '0.1',
    case: {
      case_id: caseMeta.case_id,
      project_id: caseMeta.project_id,
      customer_id: caseMeta.customer_id,
      jurisdiction: caseMeta.jurisdiction,
      transmission_provider: caseMeta.transmission_provider
    },
    finding: {
      status: result.status,
      candidate_value: supportedCandidate ? value : null,
      currency: supportedCandidate ? (result.currency || caseMeta.currency || null) : null,
      value_nature: supportedCandidate ? valueNature : null,
      verified_recovery: false,
      payment_verified: false,
      wording: supportedCandidate
        ? 'Evidence-supported candidate requiring applicable counterparty action/review; not verified recovered cash.'
        : 'No supported recovery candidate is asserted from the current evidence.'
    },
    calculations,
    evidence_chain: sources.map(s => ({ document_id: s.document_id, sha256: s.sha256, locator: s.locator })),
    uncertainties: Array.isArray(uncertainties) ? uncertainties : [],
    next_action: nextAction,
    truth_boundary: {
      candidate_is_not_recovery: true,
      release_is_not_cash: result.candidate_type === 'CAPITAL_RELEASE_NOT_CASH_RECOVERY',
      payment_must_be_independently_verified: true
    }
  };
}

module.exports = { buildRecoveryDossier };
