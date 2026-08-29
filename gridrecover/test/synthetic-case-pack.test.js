'use strict';

const assert = require('assert');
const fs = require('fs');
const path = require('path');
const { evaluateNetworkUpgradeRepayment } = require('../src/gridrecover-core');
const { evaluateClusterWithdrawalCapital } = require('../src/cluster-withdrawal');

const cases = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'fixtures', 'synthetic-cases.json'), 'utf8'));
let passed = 0;

for (const c of cases) {
  let result;
  if (c.engine === 'network_upgrade_repayment') result = evaluateNetworkUpgradeRepayment(c.input);
  else if (c.engine === 'cluster_withdrawal') result = evaluateClusterWithdrawalCapital(c.input);
  else throw new Error(`Unknown engine ${c.engine}`);

  for (const [key, value] of Object.entries(c.expected)) {
    assert.deepStrictEqual(result[key], value, `${c.case_id}: expected ${key}=${value}, got ${result[key]}`);
  }
  passed += 1;
}

assert.equal(passed, cases.length);
console.log(`GRIDRECOVER synthetic case pack: ${passed}/${cases.length} PASS`);
