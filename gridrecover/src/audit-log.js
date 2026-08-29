'use strict';

const crypto = require('crypto');

function hash(value) {
  return crypto.createHash('sha256').update(value, 'utf8').digest('hex');
}

function stable(value) {
  if (Array.isArray(value)) return `[${value.map(stable).join(',')}]`;
  if (value && typeof value === 'object') {
    return `{${Object.keys(value).sort().map(k => `${JSON.stringify(k)}:${stable(value[k])}`).join(',')}}`;
  }
  return JSON.stringify(value);
}

function clone(value) { return JSON.parse(JSON.stringify(value)); }

function validateEvents(initialEvents) {
  if (!Array.isArray(initialEvents)) throw new Error('AUDIT_STATE_INVALID');
  const events = initialEvents.map(event => Object.freeze(clone(event)));
  let previous_hash = null;
  for (const event of events) {
    if (!event || typeof event !== 'object' || !event.event_hash) throw new Error('AUDIT_CHAIN_INVALID');
    const { event_hash, ...payload } = event;
    if (payload.previous_hash !== previous_hash || hash(stable(payload)) !== event_hash) throw new Error('AUDIT_CHAIN_INVALID');
    previous_hash = event_hash;
  }
  return events;
}

class AuditLog {
  constructor(initialEvents = []) {
    this.events = validateEvents(initialEvents);
  }

  static fromState(state) {
    if (!state || state.version !== 1 || !Array.isArray(state.events)) throw new Error('AUDIT_STATE_INVALID');
    return new AuditLog(state.events);
  }

  replaceState(state) {
    if (!state || state.version !== 1 || !Array.isArray(state.events)) throw new Error('AUDIT_STATE_INVALID');
    const next = validateEvents(state.events);
    this.events = next;
    return this.exportState();
  }

  exportState() {
    return { version: 1, events: this.events.map(clone) };
  }

  append(event) {
    if (!event || !event.customer_id || !event.case_id || !event.actor_id || !event.action) throw new Error('AUDIT_EVENT_INCOMPLETE');
    if (!event.at || Number.isNaN(Date.parse(event.at))) throw new Error('AUDIT_TIMESTAMP_INVALID');
    const previous_hash = this.events.length ? this.events[this.events.length - 1].event_hash : null;
    const payload = clone({ ...event, previous_hash });
    const event_hash = hash(stable(payload));
    const frozen = Object.freeze({ ...payload, event_hash });
    this.events.push(frozen);
    return clone(frozen);
  }

  verify() {
    try { validateEvents(this.events); return true; }
    catch { return false; }
  }

  listForCustomer(customerId) {
    return this.events.filter(e => e.customer_id === customerId).map(clone);
  }
}

module.exports = { AuditLog, hash, stable };
