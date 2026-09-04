(() => {
  const els = {
    payload: document.getElementById('payload'),
    fileInput: document.getElementById('file-input'),
    caseFileInput: document.getElementById('case-file-input'),
    loadExample: document.getElementById('load-example'),
    clearInput: document.getElementById('clear-input'),
    evaluate: document.getElementById('evaluate'),
    exportCase: document.getElementById('export-case'),
    caseRevision: document.getElementById('case-revision'),
    inputSignal: document.getElementById('input-signal'),
    inputLabel: document.getElementById('input-label'),
    errorBox: document.getElementById('error-box'),
    truth: document.getElementById('truth'),
    candidates: document.getElementById('candidates'),
    lifecycle: document.getElementById('lifecycle'),
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
    claimPackageActions: document.getElementById('claim-package-actions'),
    claimPackageStatus: document.getElementById('claim-package-status'),
    generateClaimPackage: document.getElementById('generate-claim-package'),
    metricSettled: document.getElementById('metric-settled'),
    metricReady: document.getElementById('metric-ready'),
    metricExternal: document.getElementById('metric-external'),
    metricReview: document.getElementById('metric-review'),
    metricWorkflowReview: document.getElementById('metric-workflow-review'),
    metricBlocked: document.getElementById('metric-blocked'),
    workflowStateBadge: document.getElementById('workflow-state-badge'),
    workflowClaimId: document.getElementById('workflow-claim-id'),
    workflowTarget: document.getElementById('workflow-target'),
    workflowActor: document.getElementById('workflow-actor'),
    workflowTime: document.getElementById('workflow-time'),
    workflowReason: document.getElementById('workflow-reason'),
    workflowReference: document.getElementById('workflow-reference'),
    settlementFields: document.getElementById('settlement-fields'),
    settlementType: document.getElementById('settlement-type'),
    settlementAmount: document.getElementById('settlement-amount'),
    settlementCurrency: document.getElementById('settlement-currency'),
    settlementReference: document.getElementById('settlement-reference'),
    recordTransition: document.getElementById('record-transition'),
    workflowAudit: document.getElementById('workflow-audit'),
    auditCount: document.getElementById('audit-count'),
    workflowArtifacts: document.getElementById('workflow-artifacts'),
    artifactCount: document.getElementById('artifact-count'),
  };

  let latestResponse = null;
  let workflowBundle = null;
  let currentLabel = 'Manual cohort';
  let currentClaimId = null;

  const statusClass = (status) => `status-${String(status || 'unknown').replace(/[^a-z0-9_]/gi, '_')}`;
  const lifecycleClass = (status) => `lifecycle-${String(status || 'none').replace(/[^a-z0-9_]/gi, '_')}`;

  function setInputState(kind, label) {
    els.inputSignal.className = `signal ${kind}`;
    els.inputLabel.textContent = label;
  }

  function showError(message) {
    els.errorBox.textContent = message;
    els.errorBox.hidden = false;
    setInputState('error', 'Input or case state requires attention');
  }

  function clearError() {
    els.errorBox.hidden = true;
    els.errorBox.textContent = '';
  }

  function resetEvaluationViews({ preserveWorkflow = true } = {}) {
    latestResponse = null;
    currentClaimId = null;
    if (!preserveWorkflow) workflowBundle = null;
    els.truth.hidden = true;
    els.candidates.hidden = true;
    els.lifecycle.hidden = true;
    els.report.hidden = true;
    els.detailPanel.hidden = true;
    els.claimPackageActions.hidden = true;
    els.claimPackageStatus.textContent = 'Not generated';
    els.exportCase.disabled = true;
    renderWorkflowSelection();
    renderCaseRevision();
  }

  function parsePayload() {
    const text = els.payload.value.trim();
    if (!text) throw new Error('Load or paste a Recovery Scan cohort first.');
    let payload;
    try {
      payload = JSON.parse(text);
    } catch (error) {
      throw new Error(`Invalid JSON: ${error.message}`);
    }
    if (!payload || Array.isArray(payload) || typeof payload !== 'object') {
      throw new Error('The top-level JSON value must be a cohort object containing rules and claims.');
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

  function labelState(value) {
    return safeText(value).replaceAll('_', ' ');
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

  function workflowRecord(claimId) {
    const records = latestResponse?.workflow_view?.records || [];
    return records.find((item) => item.claim_id === claimId) || null;
  }

  function workflowEvents(claimId) {
    return (latestResponse?.workflow_view?.events || []).filter((item) => item.claim_id === claimId);
  }

  function workflowArtifacts(claimId) {
    return (latestResponse?.workflow_view?.artifacts || []).filter((item) => item.claim_id === claimId);
  }

  function renderCaseRevision() {
    const digest = workflowBundle?.cohort_digest || latestResponse?.workflow?.cohort_digest;
    if (!digest) {
      els.caseRevision.textContent = 'No case revision bound';
      return;
    }
    els.caseRevision.textContent = `Case revision · ${digest.slice(0, 12)}`;
  }

  function renderManagementTruth(summary) {
    const currency = summary.currency || 'UNKNOWN';
    els.metricSettled.textContent = money(summary.verified_settled_recovery, currency);
    els.metricReady.textContent = money(summary.claim_ready_not_submitted, currency);
    els.metricExternal.textContent = money(summary.external_unsettled, currency);
    els.metricReview.textContent = money(summary.review_required_pipeline, currency);
    els.metricWorkflowReview.textContent = money(summary.workflow_review_or_rejected, currency);
    els.metricBlocked.textContent = money(summary.blocked_potential, currency);
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
      chip.textContent = labelState(result.status);
      status.appendChild(chip);

      const lifecycle = document.createElement('td');
      const record = workflowRecord(result.claim_id);
      const lifeChip = document.createElement('span');
      lifeChip.className = `lifecycle-chip ${lifecycleClass(record?.lifecycle)}`;
      lifeChip.textContent = record ? labelState(record.lifecycle) : 'not started';
      lifecycle.appendChild(lifeChip);

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
      button.textContent = 'Open';
      button.addEventListener('click', () => openCandidate(result.claim_id));
      action.appendChild(button);

      tr.append(id, status, lifecycle, rule, amount, issue, action);
      els.candidateBody.appendChild(tr);
    });
  }

  function createPill(label, value) {
    const pill = document.createElement('div');
    pill.className = 'detail-pill';
    pill.textContent = `${label}: ${value}`;
    return pill;
  }

  function formatEventTime(value) {
    if (!value) return '—';
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
  }

  function renderAudit(claimId) {
    const events = claimId ? workflowEvents(claimId) : [];
    const artifacts = claimId ? workflowArtifacts(claimId) : [];

    els.workflowAudit.replaceChildren();
    els.auditCount.textContent = `${events.length} event${events.length === 1 ? '' : 's'}`;
    if (!events.length) {
      const li = document.createElement('li');
      li.className = 'empty';
      li.textContent = claimId ? 'No lifecycle event recorded yet.' : 'Select a candidate to inspect its lifecycle.';
      els.workflowAudit.appendChild(li);
    } else {
      events.forEach((event) => {
        const li = document.createElement('li');
        const title = document.createElement('strong');
        title.textContent = `${labelState(event.from_state)} → ${labelState(event.to_state)}`;
        const meta = document.createElement('span');
        const refs = [event.external_reference, event.settlement_reference].filter(Boolean).join(' · ');
        meta.textContent = `${formatEventTime(event.occurred_at)} · ${event.actor}${refs ? ` · ${refs}` : ''}`;
        const reason = document.createElement('p');
        reason.textContent = event.reason;
        li.append(title, meta, reason);
        els.workflowAudit.appendChild(li);
      });
    }

    els.workflowArtifacts.replaceChildren();
    els.artifactCount.textContent = String(artifacts.length);
    if (!artifacts.length) {
      const li = document.createElement('li');
      li.className = 'empty';
      li.textContent = 'No artifacts recorded.';
      els.workflowArtifacts.appendChild(li);
    } else {
      artifacts.forEach((artifact) => {
        const li = document.createElement('li');
        const title = document.createElement('strong');
        title.textContent = labelState(artifact.kind);
        const meta = document.createElement('span');
        meta.textContent = `${formatEventTime(artifact.generated_at)} · ${artifact.generated_by} · SHA-256 ${artifact.content_sha256.slice(0, 12)}… · ${labelState(artifact.submission_status)}`;
        li.append(title, meta);
        els.workflowArtifacts.appendChild(li);
      });
    }
  }

  function setDefaultWorkflowTime() {
    const now = new Date();
    const offsetMs = now.getTimezoneOffset() * 60 * 1000;
    els.workflowTime.value = new Date(now.getTime() - offsetMs).toISOString().slice(0, 16);
  }

  function selectedTransitionNeedsSettlement() {
    return els.workflowTarget.value === 'settled';
  }

  function updateTransitionForm() {
    els.settlementFields.hidden = !selectedTransitionNeedsSettlement();
    const hasTarget = Boolean(els.workflowTarget.value);
    els.recordTransition.disabled = !currentClaimId || !hasTarget;
  }

  function renderWorkflowSelection() {
    const claimId = currentClaimId;
    els.workflowClaimId.value = claimId || '';
    els.workflowTarget.replaceChildren();

    if (!claimId || !latestResponse) {
      const option = document.createElement('option');
      option.value = '';
      option.textContent = 'Select candidate first';
      els.workflowTarget.appendChild(option);
      els.workflowTarget.disabled = true;
      els.recordTransition.disabled = true;
      els.workflowStateBadge.textContent = 'No candidate selected';
      renderAudit(null);
      return;
    }

    const record = workflowRecord(claimId);
    const transitions = record?.allowed_transitions || ['reviewing'];
    els.workflowStateBadge.textContent = record ? `Current · ${labelState(record.lifecycle)}` : 'Current · detected (not yet recorded)';
    els.workflowStateBadge.className = `truth-lock ${lifecycleClass(record?.lifecycle || 'detected')}`;

    const placeholder = document.createElement('option');
    placeholder.value = '';
    placeholder.textContent = transitions.length ? 'Choose next state' : 'Lifecycle complete';
    els.workflowTarget.appendChild(placeholder);
    transitions.forEach((state) => {
      const option = document.createElement('option');
      option.value = state;
      option.textContent = labelState(state);
      els.workflowTarget.appendChild(option);
    });
    els.workflowTarget.disabled = transitions.length === 0;
    els.recordTransition.disabled = true;

    const result = (latestResponse.evaluation?.results || []).find((item) => item.claim_id === claimId);
    els.settlementCurrency.value = result?.currency && result.currency !== 'UNKNOWN' ? result.currency : '';
    renderAudit(claimId);
    setDefaultWorkflowTime();
    updateTransitionForm();
  }

  function openCandidate(claimId) {
    if (!latestResponse) return;
    const evaluation = latestResponse.evaluation;
    const result = (evaluation.results || []).find((item) => item.claim_id === claimId);
    const dossier = (evaluation.dossiers || []).find((item) => item.claim?.claim_id === claimId);
    if (!result) return;

    currentClaimId = claimId;
    const record = workflowRecord(claimId);
    els.detailTitle.textContent = claimId;
    els.detailSummary.replaceChildren();
    els.detailSummary.append(
      createPill('Economic', labelState(result.status)),
      createPill('Lifecycle', record ? labelState(record.lifecycle) : 'not started'),
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

    const canGeneratePackage = result.status === 'claim_ready'
      && record?.lifecycle === 'claim_ready'
      && !(result.blocking_issues || []).length
      && !(dossier?.lineage_gaps || []).length;
    els.claimPackageActions.hidden = !canGeneratePackage;
    const artifactCount = workflowArtifacts(claimId).length;
    els.claimPackageStatus.textContent = canGeneratePackage
      ? `${artifactCount} package artifact(s) recorded · none submitted by AERVIND`
      : 'Requires economic claim-ready status and auditable workflow claim_ready state';

    renderWorkflowSelection();
    els.detailPanel.hidden = false;
    els.lifecycle.hidden = false;
    els.detailPanel.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function renderResponse(response, { keepCandidate = true } = {}) {
    const previousClaimId = keepCandidate ? currentClaimId : null;
    latestResponse = response;
    workflowBundle = response.workflow || null;
    const evaluation = response.evaluation || {};
    renderManagementTruth(response.management_truth || {});
    renderCandidates(evaluation);
    els.truthNote.textContent = response.truth_note || '';
    els.reportOutput.textContent = response.executive_report_markdown || '';
    els.truth.hidden = false;
    els.candidates.hidden = false;
    els.lifecycle.hidden = false;
    els.report.hidden = false;
    els.exportCase.disabled = false;
    setInputState('ready', `${currentLabel} · evaluated`);
    renderCaseRevision();

    if (previousClaimId && (evaluation.results || []).some((item) => item.claim_id === previousClaimId)) {
      currentClaimId = previousClaimId;
      openCandidate(previousClaimId);
    } else {
      currentClaimId = null;
      els.detailPanel.hidden = true;
      els.claimPackageActions.hidden = true;
      renderWorkflowSelection();
    }
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

  async function postJson(path, body) {
    const response = await fetch(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || data.error || `Request failed (${response.status})`);
    return data;
  }

  async function evaluateCase({ scroll = true } = {}) {
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
      const data = await postJson('/api/evaluate-case', { payload, workflow: workflowBundle });
      renderResponse(data, { keepCandidate: false });
      if (scroll) els.truth.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (error) {
      showError(error.message || 'Evaluation failed.');
    } finally {
      els.evaluate.disabled = false;
      els.evaluate.textContent = 'Evaluate case';
    }
  }

  async function recordTransition() {
    clearError();
    if (!currentClaimId || !els.workflowTarget.value) return;
    const actor = els.workflowActor.value.trim();
    const reason = els.workflowReason.value.trim();
    const rawTime = els.workflowTime.value;
    if (!actor || !reason || !rawTime) {
      showError('Actor, event time and reason are required for every lifecycle transition.');
      return;
    }

    let occurredAt;
    try {
      occurredAt = new Date(rawTime).toISOString();
    } catch (_) {
      showError('Event time is invalid.');
      return;
    }

    let payload;
    try {
      payload = parsePayload();
    } catch (error) {
      showError(error.message);
      return;
    }

    const target = els.workflowTarget.value;
    const body = {
      payload,
      workflow: workflowBundle,
      claim_id: currentClaimId,
      target,
      occurred_at: occurredAt,
      actor,
      reason,
      external_reference: els.workflowReference.value.trim() || null,
    };

    if (target === 'settled') {
      const amount = els.settlementAmount.value.trim();
      const currency = els.settlementCurrency.value.trim().toUpperCase();
      const reference = els.settlementReference.value.trim();
      if (!amount || !currency || !reference) {
        showError('Settlement amount, currency and evidence reference are required.');
        return;
      }
      body.settlement = {
        settlement_type: els.settlementType.value,
        amount,
        currency,
        reference,
      };
    }

    const priorText = els.recordTransition.textContent;
    els.recordTransition.disabled = true;
    els.recordTransition.textContent = 'Validating transition…';
    try {
      const data = await postJson('/api/workflow-transition', body);
      workflowBundle = data.workflow;
      renderResponse(data, { keepCandidate: true });
      els.workflowReason.value = '';
      els.workflowReference.value = '';
      els.settlementAmount.value = '';
      els.settlementReference.value = '';
    } catch (error) {
      showError(error.message || 'Workflow transition was rejected.');
    } finally {
      els.recordTransition.textContent = priorText;
      updateTransitionForm();
    }
  }

  async function generateClaimPackage() {
    clearError();
    if (!currentClaimId) {
      showError('Select a claim-ready candidate first.');
      return;
    }
    const actor = els.workflowActor.value.trim();
    if (!actor) {
      showError('Enter the accountable operator/reviewer in Actor before generating a package.');
      return;
    }

    let payload;
    try {
      payload = parsePayload();
    } catch (error) {
      showError(error.message);
      return;
    }

    const confirmed = window.confirm(
      'Confirm that human review is complete and you want to generate this claim package. Generation is audited but does not submit, email or transmit the package.'
    );
    if (!confirmed) return;

    const claimId = currentClaimId;
    els.generateClaimPackage.disabled = true;
    els.generateClaimPackage.textContent = 'Re-validating gates…';
    els.claimPackageStatus.textContent = 'Re-evaluating current cohort and workflow revision…';
    try {
      const data = await postJson('/api/claim-package', {
        payload,
        workflow: workflowBundle,
        claim_id: claimId,
        human_release_confirmed: true,
        generated_at: new Date().toISOString(),
        generated_by: actor,
      });
      if (data.submission_status !== 'not_submitted') {
        throw new Error('Safety gate failed: unexpected submission state.');
      }
      workflowBundle = data.workflow;
      download(`${claimId}-claim-package.md`, data.claim_package_markdown || '', 'text/markdown');
      renderResponse(data, { keepCandidate: true });
      els.claimPackageStatus.textContent = 'Package generated, hashed and recorded · not submitted';
    } catch (error) {
      els.claimPackageStatus.textContent = 'Generation blocked';
      showError(error.message || 'Claim package generation failed.');
    } finally {
      els.generateClaimPackage.disabled = false;
      els.generateClaimPackage.textContent = 'Generate · never submits';
    }
  }

  async function exportCase() {
    clearError();
    let payload;
    try {
      payload = parsePayload();
    } catch (error) {
      showError(error.message);
      return;
    }
    els.exportCase.disabled = true;
    const prior = els.exportCase.textContent;
    els.exportCase.textContent = 'Validating case…';
    try {
      const data = await postJson('/api/case-export', { payload, workflow: workflowBundle });
      const date = new Date().toISOString().slice(0, 10);
      download(`AERVIND-case-${date}.json`, JSON.stringify(data.case, null, 2), 'application/json');
    } catch (error) {
      showError(error.message || 'Case export failed.');
    } finally {
      els.exportCase.disabled = !latestResponse;
      els.exportCase.textContent = prior;
    }
  }

  els.loadExample.addEventListener('click', async () => {
    clearError();
    try {
      const response = await fetch('/api/example', { cache: 'no-store' });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Could not load the synthetic example.');
      resetEvaluationViews({ preserveWorkflow: false });
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
      if (parsed?.kind === 'aervind_assisted_case') {
        throw new Error('This is an AERVIND case file. Use “Open case file” so its audit state is preserved.');
      }
      resetEvaluationViews({ preserveWorkflow: false });
      els.payload.value = prettyPayload(parsed);
      currentLabel = file.name;
      setInputState('ready', `${file.name} · cohort loaded`);
    } catch (error) {
      showError(`Could not load ${file.name}: ${error.message}`);
    } finally {
      event.target.value = '';
    }
  });

  els.caseFileInput.addEventListener('change', async (event) => {
    clearError();
    const file = event.target.files?.[0];
    if (!file) return;
    if (file.size > 2 * 1024 * 1024) {
      showError('The selected case file exceeds the 2 MB assisted-console input limit.');
      return;
    }
    try {
      const parsed = JSON.parse(await file.text());
      if (parsed?.kind !== 'aervind_assisted_case' || !parsed.cohort || !parsed.workflow) {
        throw new Error('File is not a valid AERVIND assisted case export.');
      }
      resetEvaluationViews({ preserveWorkflow: false });
      workflowBundle = parsed.workflow;
      els.payload.value = prettyPayload(parsed.cohort);
      currentLabel = file.name;
      setInputState('ready', `${file.name} · case loaded`);
      renderCaseRevision();
      await evaluateCase({ scroll: false });
    } catch (error) {
      showError(`Could not open ${file.name}: ${error.message}`);
    } finally {
      event.target.value = '';
    }
  });

  els.payload.addEventListener('input', () => {
    clearError();
    if (latestResponse) resetEvaluationViews({ preserveWorkflow: true });
    currentLabel = 'Manual cohort';
    setInputState(
      els.payload.value.trim() ? 'ready' : 'neutral',
      els.payload.value.trim() ? 'Manual cohort · re-evaluation required' : 'No cohort loaded',
    );
  });

  els.clearInput.addEventListener('click', () => {
    els.payload.value = '';
    currentLabel = 'Manual cohort';
    clearError();
    resetEvaluationViews({ preserveWorkflow: false });
    setInputState('neutral', 'No cohort loaded');
  });

  els.workflowTarget.addEventListener('change', updateTransitionForm);
  els.evaluate.addEventListener('click', () => evaluateCase());
  els.recordTransition.addEventListener('click', recordTransition);
  els.generateClaimPackage.addEventListener('click', generateClaimPackage);
  els.exportCase.addEventListener('click', exportCase);

  els.closeDetail.addEventListener('click', () => {
    currentClaimId = null;
    els.detailPanel.hidden = true;
    els.claimPackageActions.hidden = true;
    renderWorkflowSelection();
  });

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

  setDefaultWorkflowTime();
  renderWorkflowSelection();
  renderCaseRevision();
})();
