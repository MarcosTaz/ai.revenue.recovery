'use strict';

const REQUIRED_TEST_FAMILIES = Object.freeze([
  'economics_core',
  'project_provenance',
  'tenant_isolation',
  'audit_integrity',
  'durability_rollback',
  'document_provenance',
  'document_vault',
  'miso_applicability',
  'miso_e2e',
  'deadline_engine',
  'source_drift',
  'scenario_delta',
  'portfolio_command_center',
  'four_eyes_review',
  'verified_recovery_lifecycle',
  'billing_lifecycle',
  'strong_auth',
  'incident_response',
  'privacy_safe_observability'
]);

const STATUS = Object.freeze({
  NOT_READY: 'NOT_READY',
  TECHNICAL_PILOT_READY: 'TECHNICAL_PILOT_READY',
  CUSTOMER_PILOT_READY: 'CUSTOMER_PILOT_READY'
});

function nonEmpty(v) { return typeof v === 'string' && v.trim().length > 0; }
function sha(v) { return typeof v === 'string' && /^[a-f0-9]{40}$/i.test(v); }
function sha256(v) { return typeof v === 'string' && /^[a-f0-9]{64}$/i.test(v); }
function validDate(v) { return nonEmpty(v) && !Number.isNaN(Date.parse(v)); }

function evaluatePilotReadiness(input, now = new Date().toISOString()) {
  const technicalBlockers = [];
  const commercialBlockers = [];
  if (!input || typeof input !== 'object') return { status: STATUS.NOT_READY, technical_blockers: ['READINESS_INPUT_MISSING'], commercial_blockers: [] };

  const ci = input.ci || {};
  if (!sha(ci.head_sha) || !sha(ci.tested_sha) || ci.head_sha !== ci.tested_sha) technicalBlockers.push('CI_NOT_EXACT_HEAD');
  if (ci.conclusion !== 'success') technicalBlockers.push('CI_NOT_GREEN');
  if (!nonEmpty(ci.run_id)) technicalBlockers.push('CI_RUN_ID_MISSING');

  const families = input.test_families || {};
  for (const family of REQUIRED_TEST_FAMILIES) {
    if (families[family] !== 'success') technicalBlockers.push(`TEST_FAMILY_NOT_GREEN:${family}`);
  }

  if (input.supported_lane !== 'MISO_2026_NETWORK_UPGRADE_REPAYMENT') technicalBlockers.push('SUPPORTED_LANE_NOT_PINNED');
  if (input.auth_mode !== 'HASHED_TTL_ROLE_REGISTRY' || input.strong_auth_required !== true) technicalBlockers.push('STRONG_AUTH_NOT_ENFORCED');
  if (input.tenant_isolation_verified !== true) technicalBlockers.push('TENANT_ISOLATION_NOT_VERIFIED');
  if (input.document_vault_encrypted !== true) technicalBlockers.push('DOCUMENT_VAULT_NOT_ENCRYPTED');
  if (input.durable_mutations_required !== true) technicalBlockers.push('DURABLE_MUTATIONS_NOT_REQUIRED');
  if (input.audit_chain_verified !== true) technicalBlockers.push('AUDIT_CHAIN_NOT_VERIFIED');
  if (input.source_drift_invalidation_enabled !== true) technicalBlockers.push('SOURCE_DRIFT_INVALIDATION_NOT_ENABLED');
  if (input.four_eyes_review_required !== true) technicalBlockers.push('FOUR_EYES_REVIEW_NOT_REQUIRED');
  if (input.incident_response_ready !== true) technicalBlockers.push('INCIDENT_RESPONSE_NOT_READY');
  if (input.privacy_safe_observability_ready !== true) technicalBlockers.push('OBSERVABILITY_NOT_READY');

  const backup = input.backup || {};
  if (!validDate(now)) technicalBlockers.push('READINESS_NOW_INVALID');
  if (backup.encrypted !== true || backup.restore_test_passed !== true || !validDate(backup.last_restore_test_at) || !sha256(backup.restore_evidence_sha256)) {
    technicalBlockers.push('BACKUP_RESTORE_NOT_VERIFIED');
  } else if (validDate(now)) {
    const ageHours = Math.floor((Date.parse(now) - Date.parse(backup.last_restore_test_at)) / 3600000);
    if (ageHours < 0 || ageHours > 168) technicalBlockers.push('BACKUP_RESTORE_EVIDENCE_STALE');
  }

  const incidents = Array.isArray(input.open_incidents) ? input.open_incidents : [];
  if (incidents.some(i => ['SEV0', 'SEV1'].includes(i.severity) && i.state !== 'RESOLVED')) technicalBlockers.push('CRITICAL_INCIDENT_OPEN');

  const commercial = input.customer_pilot || {};
  if (commercial.business_identity_verified !== true) commercialBlockers.push('BUSINESS_IDENTITY_NOT_VERIFIED');
  if (commercial.customer_support_route_verified !== true) commercialBlockers.push('CUSTOMER_SUPPORT_ROUTE_NOT_VERIFIED');
  if (commercial.privacy_notice_ready !== true || !sha256(commercial.privacy_notice_sha256)) commercialBlockers.push('PRIVACY_NOTICE_NOT_READY');
  if (commercial.data_processing_terms_ready !== true || !sha256(commercial.data_processing_terms_sha256)) commercialBlockers.push('DATA_PROCESSING_TERMS_NOT_READY');
  if (commercial.pilot_engagement_terms_ready !== true || !sha256(commercial.pilot_engagement_terms_sha256)) commercialBlockers.push('PILOT_TERMS_NOT_READY');
  if (commercial.pricing_defined !== true) commercialBlockers.push('PILOT_PRICING_NOT_DEFINED');
  if (commercial.external_action_policy === 'CUSTOMER_AUTHORIZED_ONLY' !== true) commercialBlockers.push('EXTERNAL_ACTION_POLICY_NOT_PINNED');

  const technicalReady = technicalBlockers.length === 0;
  const customerReady = technicalReady && commercialBlockers.length === 0;
  return {
    status: customerReady ? STATUS.CUSTOMER_PILOT_READY : technicalReady ? STATUS.TECHNICAL_PILOT_READY : STATUS.NOT_READY,
    technical_blockers: [...new Set(technicalBlockers)],
    commercial_blockers: [...new Set(commercialBlockers)],
    truth_boundary: {
      technical_pilot_ready_is_not_market_validated: true,
      customer_pilot_ready_is_not_customer_verified: true,
      synthetic_tests_do_not_prove_recovery: true,
      domain_and_production_launch_are_separate_gates: true
    }
  };
}

module.exports = { REQUIRED_TEST_FAMILIES, STATUS, evaluatePilotReadiness };
