(() => {
  const els = {
    payload: document.getElementById('payload'),
    fileInput: document.getElementById('file-input'),
    loadExample: document.getElementById('load-example'),
    clearInput: document.getElementById('clear-input'),
    evaluate: document.getElementById('evaluate'),
    inputSignal: document.getElementById('input-signal'),
    inputLabel: document.getElementById('input-label'),
    errorBox: document.getElementById('error-box'),
    truth: document.getElementById('truth'),
    candidates: document.getElementById('candidates'),
    report: document.getElementById('report'),
    detailPanel: document.getElementById('detail-panel'),
    candidateBody: document.getElementById('candidate-body'),
    truthNote: document.getElementById('truth-note'),
    reportOutput: document.getElementById('report-output'),
    downloadJson: document.getElementById('download-json'),
    downloadReport: document.getElementById('download-report'),
    closeDetail: document.getElementById('close-detail'),
    detailTitle: document.getElementById('detail-title'),
    detailSummary: document.getElementById('detail-summary'),
    detailBlockers: document.getElementById('detail-blockers'),
    detailWarnings: document.getElementById('detail-warnings'),
    detailEvidence: document.getElementById('detail-evidence'),
    detailLineage: document.getElementById('detail-lineage'),
    detailTrace: document.getElementById('detail-trace'),
    metricReady: document.getElementById('metric-ready'),
    metricReadyCount: document.getElementById('metric-ready-count'),
    metricReview: document.getElementById('metric-review'),
    metricReviewCount: document.getElementById('metric-review-count'),
    metricBlocked: document.getElementById('metric-blocked'),
    metricBlockedCount: document.getElementById('metric-blocked-count'),
  };

  let latestResponse = null;
  let currentLabel = 'Manual cohort';

  const statusClass = (status) => `status-${String(status || 'unknown').replace(/[^a-z0-9_]/gi, '_')}`;

  function setInputState(kind, label) {
    els.inputSignal.className = `signal ${kind}`;
    els.inputLabel.textContent = label;
  }

  function showError(message) {
    els.errorBox.textContent = message;
    els.errorBox.hidden = false;
    setInputState('error', 'Input requires attention');
  }

  function clearError() {
    els.errorBox.hidden = true;
    els.errorBox.textContent = '';
  }

  function parsePayload() {
    const text = els.payload.value.trim();
    if (!text) throw new Error('Load or paste a Recovery Scan JSON cohort first.');
    let payload;
    try {
      payload = JSON.parse(text);
    } catch (error) {
      throw new Error(`Invalid JSON: ${error.message}`);
    }
    if (!payload || Array.isArray(payload) || typeof payload !== 'object') {
      throw new Error('The top-level JSON value must be an object containing rules and claims.');
    }
    return payload;
  }

  function prettyPayload(payload) {
    return JSON.stringify(payload, null, 2);
  }

  function money(value, currency) {
    const number = Number(value || 0);
    if (!Number.isFinite(number)) return `${currency || ''} ${value || '0'}`.trim();
    try {
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency && currency !== 'UNKNOWN' ? currency : 'USD',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      }).format(number);
    } catch (_) {
      return `${currency || ''} ${number.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`.trim();
    }
  }

  function safeText(value) {
    return value === null || value === undefined || value === '' ? '—' : String(value);
  }

  function listItems(target, values, formatter = safeText) {
    target.replaceChildren();
    const items = Array.isArray(values) ? values : [];
    if (!items.length) {
      const li = document.createElement('li');
      li.className = 'empty';
      li.textContent = 'None recorded';
      target.appendChild(li);
      return;
    }
    items.forEach((value) => {
      const li = document.createElement('li');
      li.textContent = formatter(value);
      target.appendChild(li);
    });
  }

  function renderSummary(summary, truthNote) {
    const currency = summary.currency || 'UNKNOWN';
    els.metricReady.textContent = money(summary.verified_claim_ready_recovery, currency);
    els.metricReadyCount.textContent = `${summary.claim_ready_count || 0} claim-ready candidate(s)`;
    els.metricReview.textContent = money(summary.review_required_pipeline, currency);
    els.metricReviewCount.textContent = `${summary.review_required_count || 0} candidate(s) require review`;
    els.metricBlocked.textContent = money(summary.blocked_potential, currency);
    els.metricBlockedCount.textContent = `${summary.blocked_count || 0} blocked candidate(s)`;
    els.truthNote.textContent = truthNote || '';
  }

  function primaryIssue(result) {
    const blockers = result.blocking_issues || [];
    const warnings = result.warnings || [];
    return blockers[0] || warnings[0] || '—';
  }

  function renderCandidates(evaluation) {
    const results = evaluation.results || [];
    els.candidateBody.replaceChildren();

    const sorted = [...results].sort((a, b) => Number(b.net_recoverable || 0) - Number(a.net_recoverable || 0));
    sorted.forEach((result) => {
      const tr = document.createElement('tr');

      const id = document.createElement('td');
      id.className = 'candidate-id';
      id.textContent = safeText(result.claim_id);

      const status = document.createElement('td');
      const chip = document.createElement('span');
      chip.className = `status-chip ${statusClass(result.status)}`;
      chip.textContent = safeText(result.status).replaceAll('_', ' ');
      status.appendChild(chip);

      const rule = document.createElement('td');
      rule.className = 'muted-cell';
      rule.textContent = safeText(result.rule_id);

      const amount = document.createElement('td');
      amount.className = 'numeric';
      amount.textContent = money(result.net_recoverable, result.currency);

      const issue = document.createElement('td');
      issue.className = 'muted-cell';
      issue.textContent = primaryIssue(result);

      const action = document.createElement('td');
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'row-action';
      button.textContent = 'Review';
      button.addEventListener('click', () => openCandidate(result.claim_id));
      action.appendChild(button);

      tr.append(id, status, rule, amount, issue, action);
      els.candidateBody.appendChild(tr);
    });
  }

  function createPill(label, value) {
    const pill = document.createElement('div');
    pill.className = 'detail-pill';
    pill.textContent = `${label}: ${value}`;
    return pill;
  }

  function openCandidate(claimId) {
    if (!latestResponse) return;
    const evaluation = latestResponse.evaluation;
    const result = (evaluation.results || []).find((item) => item.claim_id === claimId);
    const dossier = (evaluation.dossiers || []).find((item) => item.claim?.claim_id === claimId);
    if (!result) return;

    els.detailTitle.textContent = claimId;
    els.detailSummary.replaceChildren();
    els.detailSummary.append(
      createPill('Status', safeText(result.status).replaceAll('_', ' ')),
      createPill('Net', money(result.net_recoverable, result.currency)),
      createPill('Gross', money(result.gross_entitlement, result.currency)),
      createPill('Rule', safeText(result.rule_id)),
    );

    listItems(els.detailBlockers, result.blocking_issues);
    listItems(els.detailWarnings, result.warnings);
    listItems(
      els.detailEvidence,
      dossier?.evidence,
      (item) => `${safeText(item.evidence_type)} · ${safeText(item.evidence_id)} · ${safeText(item.source_name)}`,
    );
    listItems(els.detailLineage, dossier?.lineage_gaps);
    listItems(els.detailTrace, result.calculation_trace);

    els.detailPanel.hidden = false;
    els.detailPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function renderResponse(response) {
    latestResponse = response;
    const evaluation = response.evaluation || {};
    renderSummary(evaluation.summary || {}, response.truth_note);
    renderCandidates(evaluation);
    els.reportOutput.textContent = response.executive_report_markdown || '';
    els.truth.hidden = false;
    els.candidates.hidden = false;
    els.report.hidden = false;
    els.detailPanel.hidden = true;
    setInputState('ready', `${currentLabel} · evaluated`);
  }

  function download(filename, content, type) {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  }

  async function evaluate() {
    clearError();
    let payload;
    try {
      payload = parsePayload();
    } catch (error) {
      showError(error.message);
      return;
    }

    els.evaluate.disabled = true;
    els.evaluate.textContent = 'Evaluating…';
    setInputState('neutral', `${currentLabel} · evaluating`);

    try {
      const response = await fetch('/api/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || data.error || `Evaluation failed (${response.status})`);
      }
      renderResponse(data);
      els.truth.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (error) {
      showError(error.message || 'Evaluation failed.');
    } finally {
      els.evaluate.disabled = false;
      els.evaluate.textContent = 'Evaluate cohort';
    }
  }

  els.loadExample.addEventListener('click', async () => {
    clearError();
    try {
      const response = await fetch('/api/example', { cache: 'no-store' });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Could not load the synthetic example.');
      els.payload.value = prettyPayload(data.payload);
      currentLabel = 'Synthetic example';
      setInputState('ready', 'Synthetic example loaded · not customer data');
    } catch (error) {
      showError(error.message);
    }
  });

  els.fileInput.addEventListener('change', async (event) => {
    clearError();
    const file = event.target.files?.[0];
    if (!file) return;
    if (file.size > 2 * 1024 * 1024) {
      showError('The selected file exceeds the 2 MB assisted-console input limit.');
      return;
    }
    try {
      const text = await file.text();
      const parsed = JSON.parse(text);
      els.payload.value = prettyPayload(parsed);
      currentLabel = file.name;
      setInputState('ready', `${file.name} · loaded locally`);
    } catch (error) {
      showError(`Could not load ${file.name}: ${error.message}`);
    } finally {
      event.target.value = '';
    }
  });

  els.payload.addEventListener('input', () => {
    clearError();
    currentLabel = 'Manual cohort';
    setInputState(els.payload.value.trim() ? 'ready' : 'neutral', els.payload.value.trim() ? 'Manual cohort · unsaved' : 'No cohort loaded');
  });

  els.clearInput.addEventListener('click', () => {
    els.payload.value = '';
    latestResponse = null;
    currentLabel = 'Manual cohort';
    clearError();
    setInputState('neutral', 'No cohort loaded');
    els.truth.hidden = true;
    els.candidates.hidden = true;
    els.report.hidden = true;
    els.detailPanel.hidden = true;
  });

  els.evaluate.addEventListener('click', evaluate);
  els.closeDetail.addEventListener('click', () => { els.detailPanel.hidden = true; });

  els.downloadJson.addEventListener('click', () => {
    if (!latestResponse) return;
    download('aervind-evaluation.json', JSON.stringify(latestResponse.evaluation, null, 2), 'application/json');
  });

  els.downloadReport.addEventListener('click', () => {
    if (!latestResponse) return;
    download('aervind-executive-report.md', latestResponse.executive_report_markdown || '', 'text/markdown');
  });

  document.querySelectorAll('[data-scroll]').forEach((button) => {
    button.addEventListener('click', () => {
      const id = button.getAttribute('data-scroll');
      const target = document.getElementById(id);
      if (target && !target.hidden) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      document.querySelectorAll('.nav-item').forEach((item) => item.classList.toggle('active', item === button));
    });
  });
})();
