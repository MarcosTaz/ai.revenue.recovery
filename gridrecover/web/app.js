'use strict';

(() => {
  let accessToken = null;
  let cases = [];
  let portfolio = null;
  let selectedCase = null;
  let toastTimer = null;

  const $ = selector => document.querySelector(selector);
  const $$ = selector => [...document.querySelectorAll(selector)];
  const sessionDialog = $('#sessionDialog');
  const caseDialog = $('#caseDialog');
  const newCaseDialog = $('#newCaseDialog');

  function escapeHtml(value) {
    return String(value ?? '')
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#039;');
  }

  function toast(message, isError = false) {
    const el = $('#toast');
    el.textContent = message;
    el.classList.toggle('error', isError);
    el.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => el.classList.remove('show'), 3400);
  }

  async function api(path, options = {}) {
    if (!accessToken) throw new Error('SESSION_REQUIRED');
    const headers = new Headers(options.headers || {});
    headers.set('Authorization', `Bearer ${accessToken}`);
    const response = await fetch(path, { ...options, headers, cache: 'no-store' });
    let body = null;
    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/json')) body = await response.json();
    else body = await response.text();
    if (!response.ok) {
      const error = new Error(body?.error || `HTTP_${response.status}`);
      error.status = response.status;
      error.body = body;
      throw error;
    }
    return body;
  }

  function money(value, currency) {
    if (!Number.isFinite(value)) return '—';
    try {
      return new Intl.NumberFormat(undefined, { style: 'currency', currency, maximumFractionDigits: 0 }).format(value);
    } catch {
      return `${currency || ''} ${Math.round(value).toLocaleString()}`.trim();
    }
  }

  function multiCurrency(bucket) {
    if (!bucket || typeof bucket !== 'object') return '—';
    const entries = Object.entries(bucket).filter(([, value]) => Number.isFinite(value) && value !== 0);
    if (!entries.length) return '—';
    return entries.map(([currency, value]) => money(value, currency)).join(' · ');
  }

  function candidateCash() {
    const byCurrency = {};
    for (const nature of ['CANDIDATE_REPAYMENT', 'CASH_REFUND_CANDIDATE']) {
      for (const [currency, value] of Object.entries(portfolio?.monetary?.[nature] || {})) {
        byCurrency[currency] = (byCurrency[currency] || 0) + value;
      }
    }
    return multiCurrency(byCurrency);
  }

  function badge(label, kind = '') {
    return `<span class="badge ${kind}">${escapeHtml(label)}</span>`;
  }

  function priorityKind(priority) {
    return priority === 'CRITICAL' ? 'critical' : priority === 'HIGH' ? 'high' : priority === 'NORMAL' ? 'good' : '';
  }

  function deadlineKind(status) {
    return ['OVERDUE', 'DUE_TODAY'].includes(status) ? 'critical' : status === 'DUE_SOON' ? 'high' : status === 'CLOSED' ? 'good' : '';
  }

  function renderPortfolio() {
    $('#metricCases').textContent = String(portfolio?.case_count ?? 0);
    $('#metricCandidate').textContent = candidateCash();
    $('#metricRecovered').textContent = multiCurrency(portfolio?.monetary?.VERIFIED_RECOVERED_CASH);
    $('#metricCritical').textContent = String(portfolio?.priority_counts?.CRITICAL || 0);
    $('#truthChip').textContent = portfolio?.verified_recovery_case_count
      ? `${portfolio.verified_recovery_case_count} payment-verified recovery case${portfolio.verified_recovery_case_count === 1 ? '' : 's'}`
      : 'Commercial truth · 0 verified recoveries';

    const rows = portfolio?.rows || [];
    $('#priorityTable').innerHTML = rows.length ? `
      <table>
        <thead><tr><th>Project</th><th>Priority</th><th>Finding</th><th>Deadline</th><th>Source</th><th>Next action</th></tr></thead>
        <tbody>${rows.slice(0, 8).map(row => `
          <tr class="clickable" data-case-id="${escapeHtml(row.case_id)}">
            <td><span class="cell-title">${escapeHtml(row.project_name || row.project_id || row.case_id)}</span><span class="cell-sub">${escapeHtml(row.case_id)}</span></td>
            <td>${badge(row.priority, priorityKind(row.priority))}</td>
            <td>${badge(row.finding_status || 'UNKNOWN')}</td>
            <td>${badge(row.deadline_status || 'UNKNOWN', deadlineKind(row.deadline_status))}<span class="cell-sub">${row.days_remaining == null ? '' : `${row.days_remaining} days`}</span></td>
            <td>${badge(row.source_health || 'UNKNOWN', row.source_health === 'STABLE' ? 'good' : row.source_health === 'DRIFT_DETECTED' ? 'critical' : 'high')}</td>
            <td>${escapeHtml(row.next_action || '—')}</td>
          </tr>`).join('')}</tbody>
      </table>` : `<div class="empty-state">No cases yet. Create the first project workspace without inventing recovery value.</div>`;

    $('#exceptionsTable').innerHTML = rows.filter(row => row.priority === 'CRITICAL' || row.priority === 'HIGH').length
      ? `<table><thead><tr><th>Project</th><th>Exception</th><th>Deadline</th><th>Source health</th><th>Action</th></tr></thead><tbody>${rows
          .filter(row => row.priority === 'CRITICAL' || row.priority === 'HIGH')
          .map(row => `<tr class="clickable" data-case-id="${escapeHtml(row.case_id)}"><td><span class="cell-title">${escapeHtml(row.project_name || row.project_id)}</span></td><td>${badge(row.priority, priorityKind(row.priority))}<span class="cell-sub">${escapeHtml((row.priority_reasons || []).join(' · '))}</span></td><td>${badge(row.deadline_status, deadlineKind(row.deadline_status))}</td><td>${badge(row.source_health, row.source_health === 'DRIFT_DETECTED' ? 'critical' : '')}</td><td>${escapeHtml(row.next_action || 'Review evidence')}</td></tr>`)
          .join('')}</tbody></table>`
      : `<div class="empty-state">No critical or high-priority exceptions in the current tenant workspace.</div>`;
  }

  function renderCases(filter = '') {
    const q = filter.trim().toLowerCase();
    const list = cases.filter(record => [record.case_id, record.project_id, record.project_name, record.queue_or_interconnection_id, record.transmission_provider]
      .some(value => String(value || '').toLowerCase().includes(q)));
    $('#casesTable').innerHTML = list.length ? `
      <table>
        <thead><tr><th>Project</th><th>Provider</th><th>Queue / ID</th><th>Stage</th><th>Evidence</th><th>Version</th></tr></thead>
        <tbody>${list.map(record => `
          <tr class="clickable" data-case-id="${escapeHtml(record.case_id)}">
            <td><span class="cell-title">${escapeHtml(record.project_name || record.project_id || record.case_id)}</span><span class="cell-sub">${escapeHtml(record.case_id)}</span></td>
            <td>${escapeHtml(record.transmission_provider || '—')}</td>
            <td>${escapeHtml(record.queue_or_interconnection_id || '—')}</td>
            <td>${badge(record.process_stage || 'UNSET')}</td>
            <td>${Array.isArray(record.evidence) ? record.evidence.length : 0}</td>
            <td>v${escapeHtml(record._version || 1)}</td>
          </tr>`).join('')}</tbody>
      </table>` : `<div class="empty-state">${q ? 'No matching cases.' : 'No cases in this tenant workspace.'}</div>`;
  }

  async function loadData() {
    const [caseResponse, portfolioResponse] = await Promise.all([api('/api/cases'), api('/api/portfolio')]);
    cases = caseResponse.cases || [];
    portfolio = portfolioResponse;
    renderCases($('#caseSearch')?.value || '');
    renderPortfolio();
  }

  function switchView(view) {
    $$('.nav-item').forEach(button => button.classList.toggle('active', button.dataset.view === view));
    $$('.view').forEach(section => section.classList.toggle('active', section.id === `view-${view}`));
    const titles = { command: 'Command Center', cases: 'Cases', evidence: 'Evidence', exceptions: 'Exceptions', readiness: 'Readiness' };
    $('#pageTitle').textContent = titles[view] || 'GRIDRECOVER';
  }

  async function openCase(caseId) {
    try {
      const [record, auditResponse] = await Promise.all([api(`/api/cases/${encodeURIComponent(caseId)}`), api(`/api/cases/${encodeURIComponent(caseId)}/audit`)]);
      selectedCase = record;
      $('#caseDialogTitle').textContent = record.project_name || record.project_id || record.case_id;
      const evidence = Array.isArray(record.evidence) ? record.evidence : [];
      const events = auditResponse.events || [];
      $('#caseDetail').innerHTML = `
        <div class="case-hero">
          <section class="case-card">
            <p class="eyebrow">Workspace</p>
            <div class="case-kv">
              <div class="kv"><span>Case ID</span><strong>${escapeHtml(record.case_id)}</strong></div>
              <div class="kv"><span>Version</span><strong>v${escapeHtml(record._version || 1)}</strong></div>
              <div class="kv"><span>Project ID</span><strong>${escapeHtml(record.project_id || '—')}</strong></div>
              <div class="kv"><span>Queue / interconnection</span><strong>${escapeHtml(record.queue_or_interconnection_id || '—')}</strong></div>
              <div class="kv"><span>Provider</span><strong>${escapeHtml(record.transmission_provider || '—')}</strong></div>
              <div class="kv"><span>Source health</span><strong>${escapeHtml(record.source_health || 'UNKNOWN')}</strong></div>
            </div>
          </section>
          <section class="case-card">
            <p class="eyebrow">Truth</p>
            <div class="case-kv">
              <div class="kv"><span>Finding</span><strong>${escapeHtml(record.finding?.status || 'UNKNOWN')}</strong></div>
              <div class="kv"><span>Deadline</span><strong>${escapeHtml(record.deadline?.status || 'UNKNOWN')}</strong></div>
              <div class="kv"><span>Admission</span><strong>${escapeHtml(record.admission_status || 'UNKNOWN')}</strong></div>
              <div class="kv"><span>Verified recovery</span><strong>${record.recovery?.recovered_cash_verified ? money(record.recovery.verified_recovery_amount, record.recovery.currency) : 'None verified'}</strong></div>
            </div>
          </section>
        </div>

        <section class="case-card">
          <p class="eyebrow">Metadata</p>
          <form id="metadataForm" class="inline-form">
            <label>Project name<input name="project_name" value="${escapeHtml(record.project_name || '')}" /></label>
            <label>Next action<input name="next_action" value="${escapeHtml(record.next_action || '')}" /></label>
            <button class="primary-button" type="submit">Save</button>
          </form>
        </section>

        <section class="case-card">
          <p class="eyebrow">Deadline</p>
          <form id="deadlineForm" class="inline-form">
            <label>Fixed deadline<input name="fixed_date" type="date" required /></label>
            <label>Source document ID<input name="source_document_id" required /></label>
            <label>Source SHA / reference<input name="source_sha256" required /></label>
            <label>Source locator<input name="source_locator" required /></label>
            <button class="ghost-button" type="submit">Evaluate deadline</button>
          </form>
          <p class="muted">Only a source-authority-verified fixed date is accepted from this UI. Business-day calculations remain fail-closed.</p>
        </section>

        <section class="case-card">
          <div class="panel-head"><div><p class="eyebrow">Evidence vault</p><h3>${evidence.length} source document${evidence.length === 1 ? '' : 's'}</h3></div></div>
          <div class="document-list">${evidence.length ? evidence.map(doc => `
            <div class="document-row"><div><strong>${escapeHtml(doc.document_type || doc.document_id)}</strong><small>${escapeHtml(doc.document_id)} · ${escapeHtml(doc.extraction_method || 'source-bound')}</small></div><div>${badge(String(doc.source_sha256 || doc.sha256 || '').slice(0, 12) + '…', 'good')}</div></div>`).join('') : `<div class="empty-state">No evidence uploaded yet.</div>`}</div>
          <form id="uploadForm" class="file-drop" style="margin-top:12px">
            <div class="inline-form">
              <label>Document ID<input name="document_id" required maxlength="120" /></label>
              <label>Type<input name="document_type" value="EXECUTED_LGIA" required maxlength="120" /></label>
              <label>File<input name="file" type="file" accept=".pdf,.txt,.md,.csv,.json" required /></label>
              <button class="primary-button" type="submit">Encrypt & ingest</button>
            </div>
          </form>
        </section>

        <section class="case-card">
          <p class="eyebrow">Audit trail</p>
          <div class="audit-list">${events.length ? events.slice().reverse().slice(0, 20).map(event => `
            <div class="audit-row"><div><strong>${escapeHtml(event.action)}</strong><small>${escapeHtml(event.actor_id)} · ${escapeHtml(event.at)}</small></div><div>${badge(String(event.event_hash || '').slice(0, 10) + '…')}</div></div>`).join('') : `<div class="empty-state">No audit events recorded.</div>`}</div>
        </section>`;

      bindCaseForms();
      caseDialog.showModal();
    } catch (error) {
      toast(`Could not open case: ${error.message}`, true);
    }
  }

  function bindCaseForms() {
    $('#metadataForm')?.addEventListener('submit', async event => {
      event.preventDefault();
      const form = new FormData(event.currentTarget);
      try {
        const updated = await api(`/api/cases/${encodeURIComponent(selectedCase.case_id)}`, {
          method: 'PATCH',
          headers: { 'content-type': 'application/json' },
          body: JSON.stringify({ expected_version: selectedCase._version, patch: { project_name: form.get('project_name'), next_action: form.get('next_action') } })
        });
        selectedCase = updated;
        toast(`Case saved as v${updated._version}`);
        await loadData();
        await openCase(updated.case_id);
      } catch (error) {
        toast(error.message === 'CASE_VERSION_CONFLICT' ? 'Case changed elsewhere. Reloaded latest version.' : `Save failed: ${error.message}`, true);
        if (error.message === 'CASE_VERSION_CONFLICT') await openCase(selectedCase.case_id);
      }
    });

    $('#deadlineForm')?.addEventListener('submit', async event => {
      event.preventDefault();
      const form = new FormData(event.currentTarget);
      try {
        const updated = await api(`/api/cases/${encodeURIComponent(selectedCase.case_id)}/deadline`, {
          method: 'POST',
          headers: { 'content-type': 'application/json' },
          body: JSON.stringify({
            expected_version: selectedCase._version,
            input: {
              deadline_id: `UI-${selectedCase.case_id}-${form.get('fixed_date')}`,
              source_document_id: form.get('source_document_id'),
              source_sha256: form.get('source_sha256'),
              source_locator: form.get('source_locator'),
              source_authority_verified: true,
              rule_type: 'FIXED_DATE',
              fixed_date: form.get('fixed_date'),
              warning_days: 14
            }
          })
        });
        selectedCase = updated;
        toast(`Deadline: ${updated.deadline.status}`);
        await loadData();
        await openCase(updated.case_id);
      } catch (error) { toast(`Deadline failed: ${error.message}`, true); }
    });

    $('#uploadForm')?.addEventListener('submit', async event => {
      event.preventDefault();
      const form = new FormData(event.currentTarget);
      const file = form.get('file');
      if (!(file instanceof File) || !file.size) return toast('Choose a source document.', true);
      const extension = file.name.includes('.') ? `.${file.name.split('.').pop().toLowerCase()}` : '';
      try {
        await api(`/api/cases/${encodeURIComponent(selectedCase.case_id)}/documents`, {
          method: 'POST',
          headers: {
            'content-type': 'application/octet-stream',
            'x-document-id': String(form.get('document_id')),
            'x-document-type': String(form.get('document_type')),
            'x-file-extension': extension
          },
          body: await file.arrayBuffer()
        });
        toast('Document encrypted, hashed and ingested.');
        await loadData();
        await openCase(selectedCase.case_id);
      } catch (error) { toast(`Upload failed: ${error.message}`, true); }
    });
  }

  async function createCase(form) {
    const data = new FormData(form);
    const payload = {
      case_id: String(data.get('case_id')).trim(),
      project_id: String(data.get('project_id')).trim(),
      project_name: String(data.get('project_name')).trim(),
      transmission_provider: String(data.get('transmission_provider')).trim(),
      queue_or_interconnection_id: String(data.get('queue_or_interconnection_id')).trim(),
      process_stage: 'INTAKE',
      evidence: [],
      source_health: 'UNKNOWN',
      admission_status: 'UNKNOWN',
      next_action: 'Bind effective tariff, project GIA, repayable basis and payment evidence.'
    };
    await api('/api/cases', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(payload) });
    await loadData();
    return payload.case_id;
  }

  $('#sessionForm').addEventListener('submit', async event => {
    event.preventDefault();
    const token = $('#tokenInput').value.trim();
    if (!token) return;
    accessToken = token;
    $('#sessionError').textContent = '';
    try {
      await loadData();
      $('#tokenInput').value = '';
      sessionDialog.close();
      toast('Secure session connected. Token retained in memory only.');
    } catch (error) {
      accessToken = null;
      $('#sessionError').textContent = error.status === 401 ? 'Invalid, expired or revoked access token.' : `Connection failed: ${error.message}`;
    }
  });

  $('#disconnectBtn').addEventListener('click', () => {
    accessToken = null;
    cases = [];
    portfolio = null;
    selectedCase = null;
    renderCases();
    renderPortfolio();
    sessionDialog.showModal();
  });

  $('#newCaseBtn').addEventListener('click', () => {
    $('#newCaseError').textContent = '';
    $('#newCaseForm').reset();
    newCaseDialog.showModal();
  });
  $('#cancelNewCase').addEventListener('click', () => newCaseDialog.close());
  $('#newCaseForm').addEventListener('submit', async event => {
    event.preventDefault();
    $('#newCaseError').textContent = '';
    try {
      const id = await createCase(event.currentTarget);
      newCaseDialog.close();
      toast('Case created. No recovery value is assumed.');
      await openCase(id);
    } catch (error) { $('#newCaseError').textContent = error.message; }
  });

  $('#closeCaseDialog').addEventListener('click', () => caseDialog.close());
  $('#caseSearch').addEventListener('input', event => renderCases(event.target.value));
  $('#nav').addEventListener('click', event => {
    const button = event.target.closest('[data-view]');
    if (button) switchView(button.dataset.view);
  });
  document.body.addEventListener('click', event => {
    const jump = event.target.closest('[data-view-jump]');
    if (jump) switchView(jump.dataset.viewJump);
    const row = event.target.closest('[data-case-id]');
    if (row) openCase(row.dataset.caseId);
  });

  renderCases();
  renderPortfolio();
  sessionDialog.showModal();
})();
