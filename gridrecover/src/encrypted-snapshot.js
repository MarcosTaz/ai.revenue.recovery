'use strict';

const crypto = require('crypto');
const fs = require('fs');

function parseKey(key) {
  if (Buffer.isBuffer(key) && key.length === 32) return key;
  if (typeof key === 'string' && /^[a-fA-F0-9]{64}$/.test(key)) return Buffer.from(key, 'hex');
  throw new Error('SNAPSHOT_KEY_INVALID');
}

function saveEncryptedJson(filePath, value, keyInput) {
  const key = parseKey(keyInput);
  const iv = crypto.randomBytes(12);
  const cipher = crypto.createCipheriv('aes-256-gcm', key, iv);
  const plaintext = Buffer.from(JSON.stringify({ version: 1, value }), 'utf8');
  const ciphertext = Buffer.concat([cipher.update(plaintext), cipher.final()]);
  const tag = cipher.getAuthTag();
  const envelope = JSON.stringify({
    version: 1,
    algorithm: 'aes-256-gcm',
    iv: iv.toString('base64'),
    tag: tag.toString('base64'),
    ciphertext: ciphertext.toString('base64')
  });
  fs.writeFileSync(filePath, envelope, { encoding: 'utf8', mode: 0o600 });
  fs.chmodSync(filePath, 0o600);
}

function loadEncryptedJson(filePath, keyInput) {
  const key = parseKey(keyInput);
  let envelope;
  try { envelope = JSON.parse(fs.readFileSync(filePath, 'utf8')); }
  catch { throw new Error('SNAPSHOT_INVALID'); }
  if (!envelope || envelope.version !== 1 || envelope.algorithm !== 'aes-256-gcm') throw new Error('SNAPSHOT_FORMAT_UNSUPPORTED');
  try {
    const decipher = crypto.createDecipheriv('aes-256-gcm', key, Buffer.from(envelope.iv, 'base64'));
    decipher.setAuthTag(Buffer.from(envelope.tag, 'base64'));
    const plaintext = Buffer.concat([decipher.update(Buffer.from(envelope.ciphertext, 'base64')), decipher.final()]);
    const payload = JSON.parse(plaintext.toString('utf8'));
    if (payload.version !== 1) throw new Error('bad version');
    return payload.value;
  } catch {
    throw new Error('SNAPSHOT_AUTHENTICATION_FAILED');
  }
}

module.exports = { parseKey, saveEncryptedJson, loadEncryptedJson };
