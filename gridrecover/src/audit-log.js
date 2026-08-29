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

class AuditLog {
  constructor() { this.events = []; }

  append(event) {
    if (!event || !event.customer_id || !event.case_id || !event.actor_id || !event.action) throw new Error('AUDIT_EVENT_INCOMPLETE');
    if (!event.at || Number.isNaN(Date.parse(event.at))) throw new Error('AUDIT_TIMESTAMP_INVALID');
    const previous_hash = this.events.length ? this.events[this.events.length - 1].event_hash : null;
    const payload = { ...event, previous_hash };
    const event_hash = hash(stable(payload));
    const frozen = Object.freeze({ ...payload, event_hash });
    this.events.push(frozen);
    return frozen;
  }

  verify() {
    let previous_hash = null;
    for (const event of this.events) {
      const { event_hash, ...payload } = event;
      if (payload.previous_hash !== previous_hash) return false;
      if (hash(stable(payload)) !== event_hash) return false;
      previous_hash = event_hash;
    }
    return true;
  }

  listForCustomer(customerId) {
    return this.events.filter(e => e.customer_id === customerId).map(e => ({ ...e }));
  }
}

module.exports = { AuditLog, hash, stable };
