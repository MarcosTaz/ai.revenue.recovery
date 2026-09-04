'use strict';

const STATUS = Object.freeze({
  UNKNOWN: 'UNKNOWN',
  UPCOMING: 'UPCOMING',
  DUE_SOON: 'DUE_SOON',
  DUE_TODAY: 'DUE_TODAY',
  OVERDUE: 'OVERDUE',
  CLOSED: 'CLOSED'
});

function nonEmpty(v) { return typeof v === 'string' && v.trim().length > 0; }
function validDate(v) { return nonEmpty(v) && !Number.isNaN(Date.parse(v)); }
function isoDay(v) { return new Date(v).toISOString().slice(0, 10); }

function addCalendarDays(dateString, days) {
  const d = new Date(`${isoDay(dateString)}T00:00:00.000Z`);
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}

function evaluateDeadline(input, now = new Date().toISOString()) {
  const reasons = [];
  if (!input || typeof input !== 'object') return { status: STATUS.UNKNOWN, deadline_date: null, reasons: ['DEADLINE_INPUT_MISSING'] };
  if (!nonEmpty(input.deadline_id)) reasons.push('DEADLINE_ID_MISSING');
  if (!nonEmpty(input.case_id)) reasons.push('CASE_ID_MISSING');
  if (!nonEmpty(input.source_document_id)) reasons.push('SOURCE_DOCUMENT_ID_MISSING');
  if (!nonEmpty(input.source_sha256)) reasons.push('SOURCE_SHA256_MISSING');
  if (!nonEmpty(input.source_locator)) reasons.push('SOURCE_LOCATOR_MISSING');
  if (input.source_authority_verified !== true) reasons.push('SOURCE_AUTHORITY_NOT_VERIFIED');
  if (!validDate(now)) reasons.push('NOW_INVALID');

  let deadlineDate = null;
  let calculation = null;

  if (input.rule_type === 'FIXED_DATE') {
    if (!validDate(input.fixed_date)) reasons.push('FIXED_DATE_INVALID');
    else {
      deadlineDate = isoDay(input.fixed_date);
      calculation = { type: 'FIXED_DATE', source_value: deadlineDate };
    }
  } else if (input.rule_type === 'CALENDAR_DAYS_AFTER_EVENT') {
    if (!validDate(input.trigger_event_date)) reasons.push('TRIGGER_EVENT_DATE_INVALID');
    if (!Number.isInteger(input.days_after_event) || input.days_after_event < 0) reasons.push('DAYS_AFTER_EVENT_INVALID');
    if (!nonEmpty(input.trigger_event_source_sha256)) reasons.push('TRIGGER_EVENT_SOURCE_MISSING');
    if (!nonEmpty(input.trigger_event_locator)) reasons.push('TRIGGER_EVENT_LOCATOR_MISSING');
    if (input.trigger_event_verified !== true) reasons.push('TRIGGER_EVENT_NOT_VERIFIED');
    if (!reasons.some(r => r.startsWith('TRIGGER_') || r === 'DAYS_AFTER_EVENT_INVALID')) {
      deadlineDate = addCalendarDays(input.trigger_event_date, input.days_after_event);
      calculation = {
        type: 'CALENDAR_DAYS_AFTER_EVENT',
        trigger_event_date: isoDay(input.trigger_event_date),
        days_after_event: input.days_after_event,
        result: deadlineDate
      };
    }
  } else {
    reasons.push('DEADLINE_RULE_NOT_SUPPORTED');
  }

  if (reasons.length) return { status: STATUS.UNKNOWN, deadline_date: null, reasons: [...new Set(reasons)] };

  if (input.closed === true) {
    if (!validDate(input.closed_at) || !nonEmpty(input.closed_evidence_sha256)) {
      return { status: STATUS.UNKNOWN, deadline_date: deadlineDate, reasons: ['CLOSURE_EVIDENCE_INCOMPLETE'] };
    }
    return { status: STATUS.CLOSED, deadline_date: deadlineDate, days_remaining: null, calculation, reasons: ['VERIFIED_CLOSED'] };
  }

  const today = new Date(`${isoDay(now)}T00:00:00.000Z`);
  const due = new Date(`${deadlineDate}T00:00:00.000Z`);
  const daysRemaining = Math.round((due - today) / 86400000);
  const warningDays = Number.isInteger(input.warning_days) && input.warning_days >= 0 ? input.warning_days : 14;

  let status = STATUS.UPCOMING;
  if (daysRemaining < 0) status = STATUS.OVERDUE;
  else if (daysRemaining === 0) status = STATUS.DUE_TODAY;
  else if (daysRemaining <= warningDays) status = STATUS.DUE_SOON;

  return {
    status,
    deadline_date: deadlineDate,
    days_remaining: daysRemaining,
    warning_days: warningDays,
    calculation,
    source_binding: {
      document_id: input.source_document_id,
      sha256: input.source_sha256,
      locator: input.source_locator
    },
    limitations: [
      'business-day and holiday calendars are intentionally unsupported unless separately implemented for the controlling rule',
      'deadline status does not authorize automatic filing, claim submission, notice or legal action'
    ]
  };
}

module.exports = { STATUS, evaluateDeadline, addCalendarDays };
