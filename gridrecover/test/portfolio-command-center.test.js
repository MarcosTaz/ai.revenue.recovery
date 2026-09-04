'use strict';

const assert = require('assert');
const { buildPortfolioCommandCenter, classifyPriority } = require('../src/portfolio-command-center');

const items = [
  {
    case_id: 'C1', project_id: 'P1', project_name: 'Wind 1',
    finding: { status: 'SUPPORTED_CANDIDATE', value: 2000000, currency: 'USD', value_nature: 'CANDIDATE_REPAYMENT' },
    deadline: { status: 'DUE_SOON', days_remaining: 5 }, source_health: 'STABLE', admission_status: 'PILOT_ADMISSIBLE', next_action: 'Review schedule.'
  },
  {
    case_id: 'C2', project_id: 'P2', project_name: 'Solar 2',
    finding: { status: 'SUPPORTED_CANDIDATE', value: 1500000, currency: 'USD', value_nature: 'CAPITAL_RELEASE_NOT_CASH_RECOVERY' },
    deadline: { status: 'UPCOMING', days_remaining: 40 }, source_health: 'DRIFT_DETECTED', admission_status: 'REVIEW_REQUIRED'
  },
  {
    case_id: 'C3', project_id: 'P3', project_name: 'Storage 3',
    finding: { status: 'NO_RECOVERY', value: 0, currency: 'EUR', value_nature: 'CANDIDATE_REPAYMENT' },
    deadline: { status: 'OVERDUE', days_remaining: -2 }, source_health: 'STABLE', admission_status: 'PILOT_ADMISSIBLE',
    verified_recovery: { amount: 250000, currency: 'EUR', payment_verified: true }
  },
  {
    case_id: 'C4', project_id: 'P4', project_name: 'Solar 4',
    finding: { status: 'SUPPORTED_CANDIDATE', value: 300000, currency: 'EUR', value_nature: 'CASH_REFUND_CANDIDATE' },
    deadline: { status: 'UPCOMING', days_remaining: 90 }, source_health: 'UNKNOWN', admission_status: 'SOURCE_REQUIRED'
  }
];

const r = buildPortfolioCommandCenter(items);
assert.equal(r.status, 'VALID');
assert.equal(r.case_count, 4);
assert.equal(r.monetary.CANDIDATE_REPAYMENT.USD, 2000000);
assert.equal(r.monetary.CAPITAL_RELEASE_NOT_CASH_RECOVERY.USD, 1500000);
assert.equal(r.monetary.CASH_REFUND_CANDIDATE.EUR, 300000);
assert.equal(r.monetary.VERIFIED_RECOVERED_CASH.EUR, 250000);
assert.equal(r.verified_recovery_case_count, 1);
assert.equal(r.rows[0].priority, 'CRITICAL');
assert(['C2', 'C3'].includes(r.rows[0].case_id));
assert.equal(r.truth_boundary.mixed_currencies_are_never_summed, true);
assert.equal(r.truth_boundary.security_release_is_not_cash, true);

{
  const p = classifyPriority(items[0]);
  assert.equal(p.level, 'HIGH');
  assert(p.reasons.includes('CANDIDATE_WITH_NEAR_DEADLINE'));
}
{
  const p = classifyPriority(items[1]);
  assert.equal(p.level, 'CRITICAL');
  assert(p.reasons.includes('SOURCE_DRIFT_INVALIDATES_ACTIVE_CANDIDATE'));
}
{
  const bad = buildPortfolioCommandCenter([{ case_id: 'X', project_id: 'P', finding: { status: 'SUPPORTED_CANDIDATE', value: -1, currency: 'USD', value_nature: 'CANDIDATE_REPAYMENT' } }]);
  assert.equal(bad.status, 'UNKNOWN');
}
{
  const bad = buildPortfolioCommandCenter([{ case_id: 'X', project_id: 'P', verified_recovery: { payment_verified: true, amount: -1, currency: 'USD' } }]);
  assert.equal(bad.status, 'UNKNOWN');
}
{
  const unverified = buildPortfolioCommandCenter([{ case_id: 'X', project_id: 'P', verified_recovery: { payment_verified: false, amount: 999999, currency: 'USD' } }]);
  assert.equal(unverified.status, 'VALID');
  assert.equal(unverified.monetary.VERIFIED_RECOVERED_CASH, undefined);
}

console.log('GRIDRECOVER portfolio command center: 16/16 PASS');
