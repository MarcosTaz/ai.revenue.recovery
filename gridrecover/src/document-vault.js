'use strict';

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');

function parseMasterKey(key) {
  if (Buffer.isBuffer(key) && key.length === 32) return key;
  if (typeof key === 'string' && /^[a-fA-F0-9]{64}$/.test(key)) return Buffer.from(key, 'hex');
  throw new Error('VAULT_MASTER_KEY_INVALID');
}

function safeId(value, label) {
  if (typeof value !== 'string' || !/^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$/.test(value)) throw new Error(`${label}_INVALID`);
  if (value.includes('..')) throw new Error(`${label}_INVALID`);
  return value;
}

function customerDirName(customerId) {
  return crypto.createHash('sha256').update(customerId, 'utf8').digest('hex');
}

function deriveCustomerKey(masterKey, customerId) {
  return Buffer.from(crypto.hkdfSync('sha256', masterKey, Buffer.from('gridrecover-document-vault-v1'), Buffer.from(customerId, 'utf8'), 32));
}

class DocumentVault {
  constructor({ rootDir, masterKey, maxBytes = 25 * 1024 * 1024 }) {
    if (!rootDir) throw new Error('VAULT_ROOT_REQUIRED');
    this.rootDir = path.resolve(rootDir);
    this.masterKey = parseMasterKey(masterKey);
    this.maxBytes = maxBytes;
    fs.mkdirSync(this.rootDir, { recursive: true, mode: 0o700 });
    fs.chmodSync(this.rootDir, 0o700);
  }

  _paths(customerId, documentId) {
    safeId(customerId, 'CUSTOMER_ID');
    safeId(documentId, 'DOCUMENT_ID');
    const dir = path.join(this.rootDir, customerDirName(customerId));
    return { dir, file: path.join(dir, `${documentId}.enc`) };
  }

  put({ customerId, documentId, documentType, bytes }) {
    safeId(documentType, 'DOCUMENT_TYPE');
    if (!Buffer.isBuffer(bytes)) bytes = Buffer.from(bytes || []);
    if (!bytes.length) throw new Error('DOCUMENT_EMPTY');
    if (bytes.length > this.maxBytes) throw new Error('DOCUMENT_TOO_LARGE');
    const { dir, file } = this._paths(customerId, documentId);
    fs.mkdirSync(dir, { recursive: true, mode: 0o700 });
    fs.chmodSync(dir, 0o700);
    if (fs.existsSync(file)) throw new Error('DOCUMENT_ID_EXISTS');

    const key = deriveCustomerKey(this.masterKey, customerId);
    const iv = crypto.randomBytes(12);
    const cipher = crypto.createCipheriv('aes-256-gcm', key, iv);
    const ciphertext = Buffer.concat([cipher.update(bytes), cipher.final()]);
    const tag = cipher.getAuthTag();
    const sourceSha256 = crypto.createHash('sha256').update(bytes).digest('hex');
    const envelope = {
      version: 1,
      algorithm: 'aes-256-gcm',
      customer_binding: customerDirName(customerId),
      document_id: documentId,
      document_type: documentType,
      source_sha256: sourceSha256,
      byte_length: bytes.length,
      iv: iv.toString('base64'),
      tag: tag.toString('base64'),
      ciphertext: ciphertext.toString('base64')
    };
    fs.writeFileSync(file, JSON.stringify(envelope), { encoding: 'utf8', mode: 0o600, flag: 'wx' });
    fs.chmodSync(file, 0o600);
    return { document_id: documentId, document_type: documentType, source_sha256: sourceSha256, byte_length: bytes.length };
  }

  get({ customerId, documentId }) {
    const { file } = this._paths(customerId, documentId);
    if (!fs.existsSync(file)) throw new Error('DOCUMENT_NOT_FOUND');
    let envelope;
    try { envelope = JSON.parse(fs.readFileSync(file, 'utf8')); }
    catch { throw new Error('VAULT_ENVELOPE_INVALID'); }
    if (!envelope || envelope.version !== 1 || envelope.algorithm !== 'aes-256-gcm') throw new Error('VAULT_ENVELOPE_INVALID');
    if (envelope.customer_binding !== customerDirName(customerId) || envelope.document_id !== documentId) throw new Error('VAULT_BINDING_INVALID');
    try {
      const key = deriveCustomerKey(this.masterKey, customerId);
      const decipher = crypto.createDecipheriv('aes-256-gcm', key, Buffer.from(envelope.iv, 'base64'));
      decipher.setAuthTag(Buffer.from(envelope.tag, 'base64'));
      const bytes = Buffer.concat([decipher.update(Buffer.from(envelope.ciphertext, 'base64')), decipher.final()]);
      const sha = crypto.createHash('sha256').update(bytes).digest('hex');
      if (sha !== envelope.source_sha256 || bytes.length !== envelope.byte_length) throw new Error('integrity');
      return { bytes, metadata: { document_id: envelope.document_id, document_type: envelope.document_type, source_sha256: envelope.source_sha256, byte_length: envelope.byte_length } };
    } catch {
      throw new Error('VAULT_AUTHENTICATION_FAILED');
    }
  }

  delete({ customerId, documentId }) {
    const { file } = this._paths(customerId, documentId);
    if (!fs.existsSync(file)) throw new Error('DOCUMENT_NOT_FOUND');
    fs.unlinkSync(file);
    return { deleted: true, document_id: documentId };
  }
}

module.exports = { DocumentVault, parseMasterKey, safeId, deriveCustomerKey, customerDirName };
