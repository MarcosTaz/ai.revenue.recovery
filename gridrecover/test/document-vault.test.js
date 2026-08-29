'use strict';

const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { DocumentVault } = require('../src/document-vault');

const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'gridrecover-vault-'));
const key = '55'.repeat(32);

try {
  const vault = new DocumentVault({ rootDir: dir, masterKey: key, maxBytes: 1024 });
  const source = Buffer.from('Article 11.4.1\nRepayable portion evidence\n', 'utf8');
  const saved = vault.put({ customerId: 'CUSTOMER-A', documentId: 'LGIA-1', documentType: 'EXECUTED_LGIA', bytes: source });
  assert.equal(saved.document_id, 'LGIA-1');
  assert.equal(saved.byte_length, source.length);

  const got = vault.get({ customerId: 'CUSTOMER-A', documentId: 'LGIA-1' });
  assert.equal(got.bytes.equals(source), true);
  assert.equal(got.metadata.source_sha256, saved.source_sha256);

  assert.throws(() => vault.get({ customerId: 'CUSTOMER-B', documentId: 'LGIA-1' }), /DOCUMENT_NOT_FOUND/);
  assert.throws(() => vault.put({ customerId: 'CUSTOMER-A', documentId: 'LGIA-1', documentType: 'EXECUTED_LGIA', bytes: source }), /DOCUMENT_ID_EXISTS/);
  assert.throws(() => vault.put({ customerId: '../A', documentId: 'X', documentType: 'T', bytes: source }), /CUSTOMER_ID_INVALID/);
  assert.throws(() => vault.put({ customerId: 'CUSTOMER-A', documentId: '../X', documentType: 'T', bytes: source }), /DOCUMENT_ID_INVALID/);
  assert.throws(() => vault.put({ customerId: 'CUSTOMER-A', documentId: 'BIG', documentType: 'T', bytes: Buffer.alloc(2048) }), /DOCUMENT_TOO_LARGE/);

  const customerDir = fs.readdirSync(dir)[0];
  const file = path.join(dir, customerDir, 'LGIA-1.enc');
  assert.equal(fs.statSync(file).mode & 0o777, 0o600);
  const envelope = JSON.parse(fs.readFileSync(file, 'utf8'));
  assert.equal(JSON.stringify(envelope).includes(source.toString('utf8')), false);
  const ciphertext = Buffer.from(envelope.ciphertext, 'base64');
  ciphertext[0] ^= 0xff;
  envelope.ciphertext = ciphertext.toString('base64');
  fs.writeFileSync(file, JSON.stringify(envelope), 'utf8');
  assert.throws(() => vault.get({ customerId: 'CUSTOMER-A', documentId: 'LGIA-1' }), /VAULT_AUTHENTICATION_FAILED/);

  const vault2 = new DocumentVault({ rootDir: path.join(dir, 'delete-vault'), masterKey: key });
  vault2.put({ customerId: 'CUSTOMER-A', documentId: 'D1', documentType: 'T', bytes: Buffer.from('x') });
  assert.equal(vault2.delete({ customerId: 'CUSTOMER-A', documentId: 'D1' }).deleted, true);
  assert.throws(() => vault2.get({ customerId: 'CUSTOMER-A', documentId: 'D1' }), /DOCUMENT_NOT_FOUND/);

  console.log('GRIDRECOVER document vault: 14/14 PASS');
} finally {
  fs.rmSync(dir, { recursive: true, force: true });
}
