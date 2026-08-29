'use strict';

const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { saveEncryptedJson, loadEncryptedJson } = require('../src/encrypted-snapshot');

const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'gridrecover-'));
const file = path.join(dir, 'state.enc');
const key = '11'.repeat(32);
const wrong = '22'.repeat(32);

try {
  saveEncryptedJson(file, { cases: [{ case_id: 'C1', customer_id: 'A' }], audit_head: 'h1' }, key);
  const restored = loadEncryptedJson(file, key);
  assert.equal(restored.cases[0].case_id, 'C1');
  assert.equal(restored.audit_head, 'h1');
  assert.equal(fs.statSync(file).mode & 0o777, 0o600);
  assert.throws(() => loadEncryptedJson(file, wrong), /SNAPSHOT_AUTHENTICATION_FAILED/);

  const envelope = JSON.parse(fs.readFileSync(file, 'utf8'));
  const bytes = Buffer.from(envelope.ciphertext, 'base64');
  bytes[0] ^= 0xff;
  envelope.ciphertext = bytes.toString('base64');
  fs.writeFileSync(file, JSON.stringify(envelope), 'utf8');
  assert.throws(() => loadEncryptedJson(file, key), /SNAPSHOT_AUTHENTICATION_FAILED/);

  assert.throws(() => saveEncryptedJson(file, {}, 'short'), /SNAPSHOT_KEY_INVALID/);
  console.log('GRIDRECOVER encrypted snapshot: 6/6 PASS');
} finally {
  fs.rmSync(dir, { recursive: true, force: true });
}
