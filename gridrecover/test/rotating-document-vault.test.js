'use strict';

const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { RotatingDocumentVault } = require('../src/rotating-document-vault');

const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'gridrecover-vault-v2-'));
try {
  const vault = new RotatingDocumentVault({
    rootDir: dir,
    keyring: { k1: '11'.repeat(32), k2: '22'.repeat(32) },
    activeKeyVersion: 'k1'
  });
  const bytes = Buffer.from('MISO LGIA Article 11.4.1 source', 'utf8');
  const saved = vault.put({ customerId: 'A', documentId: 'D1', documentType: 'EXECUTED_LGIA', bytes });
  assert.equal(saved.key_version, 'k1');
  assert.equal(vault.get({ customerId: 'A', documentId: 'D1' }).bytes.equals(bytes), true);
  assert.equal(vault.get({ customerId: 'A', documentId: 'D1' }).metadata.key_version, 'k1');

  vault.put({ customerId: 'B', documentId: 'D1', documentType: 'EXECUTED_LGIA', bytes: Buffer.from('tenant B') });
  assert.equal(vault.get({ customerId: 'B', documentId: 'D1' }).bytes.toString(), 'tenant B');
  assert.equal(vault.get({ customerId: 'A', documentId: 'D1' }).bytes.toString(), 'MISO LGIA Article 11.4.1 source');

  const beforeSha = vault.get({ customerId: 'A', documentId: 'D1' }).metadata.source_sha256;
  const rotated = vault.rotateCustomer({ customerId: 'A', targetKeyVersion: 'k2' });
  assert.equal(rotated.rotated, 1);
  assert.equal(rotated.skipped, 0);
  const after = vault.get({ customerId: 'A', documentId: 'D1' });
  assert.equal(after.metadata.key_version, 'k2');
  assert.equal(after.metadata.source_sha256, beforeSha);
  assert.equal(after.bytes.equals(bytes), true);

  const again = vault.rotateCustomer({ customerId: 'A', targetKeyVersion: 'k2' });
  assert.equal(again.rotated, 0);
  assert.equal(again.skipped, 1);
  assert.equal(vault.get({ customerId: 'B', documentId: 'D1' }).metadata.key_version, 'k1');

  const customerDir = fs.readdirSync(dir).find(name => {
    const full = path.join(dir, name);
    return fs.statSync(full).isDirectory() && fs.existsSync(path.join(full, 'D1.enc'));
  });
  assert(customerDir);
  const envelopes = fs.readdirSync(path.join(dir, customerDir));
  assert.equal(envelopes.some(name => name.endsWith('.tmp')), false);

  assert.throws(() => vault.rotateCustomer({ customerId: 'A', targetKeyVersion: 'missing' }), /VAULT_KEY_VERSION_UNAVAILABLE/);
  assert.throws(() => new RotatingDocumentVault({ rootDir: path.join(dir, 'bad'), keyring: { k1: 'short' }, activeKeyVersion: 'k1' }), /VAULT_MASTER_KEY_INVALID/);

  const unavailable = new RotatingDocumentVault({ rootDir: path.join(dir, 'unavailable'), keyring: { k2: '22'.repeat(32) }, activeKeyVersion: 'k2' });
  const sourceVault = new RotatingDocumentVault({ rootDir: path.join(dir, 'unavailable'), keyring: { k1: '11'.repeat(32), k2: '22'.repeat(32) }, activeKeyVersion: 'k1' });
  sourceVault.put({ customerId: 'A', documentId: 'OLD', documentType: 'T', bytes: Buffer.from('old') });
  assert.throws(() => unavailable.get({ customerId: 'A', documentId: 'OLD' }), /VAULT_KEY_VERSION_UNAVAILABLE/);

  assert.equal(vault.delete({ customerId: 'A', documentId: 'D1' }).deleted, true);
  assert.throws(() => vault.get({ customerId: 'A', documentId: 'D1' }), /DOCUMENT_NOT_FOUND/);

  console.log('GRIDRECOVER rotating document vault: 19/19 PASS');
} finally {
  fs.rmSync(dir, { recursive: true, force: true });
}
