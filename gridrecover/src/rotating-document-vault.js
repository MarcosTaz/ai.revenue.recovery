'use strict';

const crypto = require('crypto');
const fs = require('fs');
const path = require('path');
const { parseMasterKey, safeId, customerDirName } = require('./document-vault');

function nonEmpty(v) { return typeof v === 'string' && v.trim().length > 0; }
function deriveVersionedCustomerKey(masterKey, customerId, keyVersion) {
  return Buffer.from(crypto.hkdfSync(
    'sha256',
    masterKey,
    Buffer.from(`gridrecover-document-vault-v2:${keyVersion}`),
    Buffer.from(customerId, 'utf8'),
    32
  ));
}

class RotatingDocumentVault {
  constructor({ rootDir, keyring, activeKeyVersion, maxBytes = 25 * 1024 * 1024 }) {
    if (!rootDir) throw new Error('VAULT_ROOT_REQUIRED');
    if (!keyring || typeof keyring !== 'object' || Array.isArray(keyring)) throw new Error('VAULT_KEYRING_INVALID');
    if (!nonEmpty(activeKeyVersion) || !Object.prototype.hasOwnProperty.call(keyring, activeKeyVersion)) throw new Error('VAULT_ACTIVE_KEY_INVALID');
    this.rootDir = path.resolve(rootDir);
    this.keys = new Map();
    for (const [version, key] of Object.entries(keyring)) {
      safeId(version, 'KEY_VERSION');
      this.keys.set(version, parseMasterKey(key));
    }
    this.activeKeyVersion = activeKeyVersion;
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

  _encryptEnvelope({ customerId, documentId, documentType, bytes, keyVersion }) {
    const masterKey = this.keys.get(keyVersion);
    if (!masterKey) throw new Error('VAULT_KEY_VERSION_UNAVAILABLE');
    const key = deriveVersionedCustomerKey(masterKey, customerId, keyVersion);
    const iv = crypto.randomBytes(12);
    const cipher = crypto.createCipheriv('aes-256-gcm', key, iv);
    const ciphertext = Buffer.concat([cipher.update(bytes), cipher.final()]);
    const tag = cipher.getAuthTag();
    const sourceSha256 = crypto.createHash('sha256').update(bytes).digest('hex');
    return {
      version: 2,
      algorithm: 'aes-256-gcm',
      key_version: keyVersion,
      customer_binding: customerDirName(customerId),
      document_id: documentId,
      document_type: documentType,
      source_sha256: sourceSha256,
      byte_length: bytes.length,
      iv: iv.toString('base64'),
      tag: tag.toString('base64'),
      ciphertext: ciphertext.toString('base64')
    };
  }

  _decryptEnvelope(customerId, documentId, envelope) {
    if (!envelope || envelope.version !== 2 || envelope.algorithm !== 'aes-256-gcm' || !nonEmpty(envelope.key_version)) throw new Error('VAULT_ENVELOPE_INVALID');
    if (envelope.customer_binding !== customerDirName(customerId) || envelope.document_id !== documentId) throw new Error('VAULT_BINDING_INVALID');
    const masterKey = this.keys.get(envelope.key_version);
    if (!masterKey) throw new Error('VAULT_KEY_VERSION_UNAVAILABLE');
    try {
      const key = deriveVersionedCustomerKey(masterKey, customerId, envelope.key_version);
      const decipher = crypto.createDecipheriv('aes-256-gcm', key, Buffer.from(envelope.iv, 'base64'));
      decipher.setAuthTag(Buffer.from(envelope.tag, 'base64'));
      const bytes = Buffer.concat([decipher.update(Buffer.from(envelope.ciphertext, 'base64')), decipher.final()]);
      const sha = crypto.createHash('sha256').update(bytes).digest('hex');
      if (sha !== envelope.source_sha256 || bytes.length !== envelope.byte_length) throw new Error('integrity');
      return bytes;
    } catch (error) {
      if (error.message === 'VAULT_KEY_VERSION_UNAVAILABLE') throw error;
      throw new Error('VAULT_AUTHENTICATION_FAILED');
    }
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
    const envelope = this._encryptEnvelope({ customerId, documentId, documentType, bytes, keyVersion: this.activeKeyVersion });
    fs.writeFileSync(file, JSON.stringify(envelope), { encoding: 'utf8', mode: 0o600, flag: 'wx' });
    fs.chmodSync(file, 0o600);
    return { document_id: documentId, document_type: documentType, source_sha256: envelope.source_sha256, byte_length: bytes.length, key_version: envelope.key_version };
  }

  get({ customerId, documentId }) {
    const { file } = this._paths(customerId, documentId);
    if (!fs.existsSync(file)) throw new Error('DOCUMENT_NOT_FOUND');
    let envelope;
    try { envelope = JSON.parse(fs.readFileSync(file, 'utf8')); }
    catch { throw new Error('VAULT_ENVELOPE_INVALID'); }
    const bytes = this._decryptEnvelope(customerId, documentId, envelope);
    return {
      bytes,
      metadata: {
        document_id: envelope.document_id,
        document_type: envelope.document_type,
        source_sha256: envelope.source_sha256,
        byte_length: envelope.byte_length,
        key_version: envelope.key_version
      }
    };
  }

  delete({ customerId, documentId }) {
    const { file } = this._paths(customerId, documentId);
    if (!fs.existsSync(file)) throw new Error('DOCUMENT_NOT_FOUND');
    fs.unlinkSync(file);
    return { deleted: true, document_id: documentId };
  }

  rotateCustomer({ customerId, targetKeyVersion = this.activeKeyVersion }) {
    safeId(customerId, 'CUSTOMER_ID');
    if (!this.keys.has(targetKeyVersion)) throw new Error('VAULT_KEY_VERSION_UNAVAILABLE');
    const dir = path.join(this.rootDir, customerDirName(customerId));
    if (!fs.existsSync(dir)) return { customer_id: customerId, target_key_version: targetKeyVersion, rotated: 0, skipped: 0 };
    const files = fs.readdirSync(dir).filter(name => name.endsWith('.enc'));
    let rotated = 0;
    let skipped = 0;
    for (const name of files) {
      const file = path.join(dir, name);
      let envelope;
      try { envelope = JSON.parse(fs.readFileSync(file, 'utf8')); }
      catch { throw new Error('VAULT_ENVELOPE_INVALID'); }
      const documentId = envelope.document_id;
      if (envelope.key_version === targetKeyVersion) { skipped += 1; continue; }
      const bytes = this._decryptEnvelope(customerId, documentId, envelope);
      const replacement = this._encryptEnvelope({ customerId, documentId, documentType: envelope.document_type, bytes, keyVersion: targetKeyVersion });
      if (replacement.source_sha256 !== envelope.source_sha256) throw new Error('VAULT_ROTATION_HASH_MISMATCH');
      const tmp = `${file}.${crypto.randomUUID()}.tmp`;
      fs.writeFileSync(tmp, JSON.stringify(replacement), { encoding: 'utf8', mode: 0o600, flag: 'wx' });
      fs.chmodSync(tmp, 0o600);
      const verifyEnvelope = JSON.parse(fs.readFileSync(tmp, 'utf8'));
      const verifyBytes = this._decryptEnvelope(customerId, documentId, verifyEnvelope);
      if (!verifyBytes.equals(bytes)) { fs.unlinkSync(tmp); throw new Error('VAULT_ROTATION_VERIFY_FAILED'); }
      fs.renameSync(tmp, file);
      rotated += 1;
    }
    return { customer_id: customerId, target_key_version: targetKeyVersion, rotated, skipped };
  }
}

module.exports = { RotatingDocumentVault, deriveVersionedCustomerKey };
