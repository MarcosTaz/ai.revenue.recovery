'use strict';

const crypto = require('crypto');

const ROLES = Object.freeze(['ADMIN', 'ANALYST', 'REVIEWER', 'VIEWER']);
const PERMISSIONS = Object.freeze({
  ADMIN: new Set(['CASE_READ', 'CASE_WRITE', 'DOCUMENT_UPLOAD', 'REVIEW_SUBMIT', 'REVIEW_APPROVE', 'BILLING_READ', 'BILLING_WRITE', 'ADMIN']),
  ANALYST: new Set(['CASE_READ', 'CASE_WRITE', 'DOCUMENT_UPLOAD', 'REVIEW_SUBMIT']),
  REVIEWER: new Set(['CASE_READ', 'REVIEW_APPROVE']),
  VIEWER: new Set(['CASE_READ'])
});

function nonEmpty(v) { return typeof v === 'string' && v.trim().length > 0; }
function validDate(v) { return nonEmpty(v) && !Number.isNaN(Date.parse(v)); }
function hashToken(token) { return crypto.createHash('sha256').update(token, 'utf8').digest('hex'); }

function timingSafeHexEqual(a, b) {
  if (typeof a !== 'string' || typeof b !== 'string' || a.length !== b.length) return false;
  try { return crypto.timingSafeEqual(Buffer.from(a, 'hex'), Buffer.from(b, 'hex')); }
  catch { return false; }
}

class AuthRegistry {
  constructor(initial = []) {
    if (!Array.isArray(initial)) throw new Error('AUTH_STATE_INVALID');
    this.records = initial.map(record => this._validateStored(record));
  }

  _validateStored(record) {
    if (!record || !nonEmpty(record.token_id) || !/^[a-f0-9]{64}$/i.test(record.token_sha256 || '')) throw new Error('AUTH_STATE_INVALID');
    if (!nonEmpty(record.customer_id) || !nonEmpty(record.user_id) || !ROLES.includes(record.role)) throw new Error('AUTH_STATE_INVALID');
    if (!validDate(record.created_at) || !validDate(record.expires_at)) throw new Error('AUTH_STATE_INVALID');
    if (record.revoked_at != null && !validDate(record.revoked_at)) throw new Error('AUTH_STATE_INVALID');
    return Object.freeze({ ...record, token_sha256: record.token_sha256.toLowerCase() });
  }

  issue({ customer_id, user_id, role, created_at, expires_at }) {
    if (!nonEmpty(customer_id) || !nonEmpty(user_id) || !ROLES.includes(role) || !validDate(created_at) || !validDate(expires_at)) throw new Error('AUTH_ISSUE_INVALID');
    if (Date.parse(expires_at) <= Date.parse(created_at)) throw new Error('AUTH_EXPIRY_INVALID');
    const token = crypto.randomBytes(32).toString('base64url');
    const token_sha256 = hashToken(token);
    const token_id = crypto.randomUUID();
    const stored = this._validateStored({ token_id, token_sha256, customer_id, user_id, role, created_at, expires_at, revoked_at: null });
    this.records.push(stored);
    return { token, token_id, customer_id, user_id, role, expires_at };
  }

  resolve(token, now = new Date().toISOString()) {
    if (!nonEmpty(token) || !validDate(now)) return null;
    const presented = hashToken(token);
    const record = this.records.find(r => timingSafeHexEqual(r.token_sha256, presented));
    if (!record || record.revoked_at != null || Date.parse(now) >= Date.parse(record.expires_at)) return null;
    return { token_id: record.token_id, customer_id: record.customer_id, user_id: record.user_id, role: record.role, expires_at: record.expires_at };
  }

  revoke(token_id, revoked_at) {
    if (!nonEmpty(token_id) || !validDate(revoked_at)) throw new Error('AUTH_REVOKE_INVALID');
    const index = this.records.findIndex(r => r.token_id === token_id);
    if (index < 0) throw new Error('AUTH_TOKEN_NOT_FOUND');
    const current = this.records[index];
    if (current.revoked_at) return { token_id, revoked_at: current.revoked_at, already_revoked: true };
    this.records[index] = this._validateStored({ ...current, revoked_at });
    return { token_id, revoked_at, already_revoked: false };
  }

  can(principal, permission) {
    if (!principal || !ROLES.includes(principal.role)) return false;
    return PERMISSIONS[principal.role].has(permission);
  }

  exportState() {
    return { version: 1, records: this.records.map(r => ({ ...r })) };
  }

  static fromState(state) {
    if (!state || state.version !== 1 || !Array.isArray(state.records)) throw new Error('AUTH_STATE_INVALID');
    return new AuthRegistry(state.records);
  }
}

module.exports = { AuthRegistry, ROLES, PERMISSIONS, hashToken, timingSafeHexEqual };
