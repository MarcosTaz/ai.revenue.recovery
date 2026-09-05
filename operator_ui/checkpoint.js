(() => {
  const nativeFetch = window.fetch.bind(window);
  const MUTATION_PATHS = new Set(['/api/workflow-transition', '/api/claim-package']);
  let caseDirty = false;

  function warningBox() {
    return document.getElementById('checkpoint-warning');
  }

  function showWarning(message) {
    const box = warningBox();
    if (!box) return;
    box.textContent = message;
    box.hidden = false;
  }

  function clearWarning() {
    const box = warningBox();
    if (!box) return;
    box.textContent = '';
    box.hidden = true;
  }

  function downloadCheckpoint(caseData, label) {
    const content = JSON.stringify(caseData, null, 2);
    const blob = new Blob([content], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const stamp = new Date().toISOString().replaceAll(':', '-');
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `AERVIND-case-${label}-${stamp}.json`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  }

  async function createValidatedCheckpoint(requestPayload, responseData, label) {
    if (!requestPayload?.payload || !responseData?.workflow) {
      throw new Error('mutation response did not contain checkpointable case state');
    }

    const exportResponse = await nativeFetch('/api/case-export', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        payload: requestPayload.payload,
        workflow: responseData.workflow,
      }),
    });
    const exportData = await exportResponse.json();
    if (!exportResponse.ok || !exportData?.case) {
      throw new Error(exportData?.detail || exportData?.error || 'validated case export failed');
    }

    downloadCheckpoint(exportData.case, label);
    caseDirty = false;
    clearWarning();
  }

  window.fetch = async function aervindCheckpointedFetch(input, init = {}) {
    const response = await nativeFetch(input, init);
    const url = typeof input === 'string' ? input : input?.url || '';
    let pathname = '';
    try {
      pathname = new URL(url, window.location.href).pathname;
    } catch (_) {
      return response;
    }

    const method = String(init?.method || 'GET').toUpperCase();
    if (method === 'POST' && pathname === '/api/case-export' && response.ok) {
      caseDirty = false;
      clearWarning();
      return response;
    }

    if (method !== 'POST' || !MUTATION_PATHS.has(pathname) || !response.ok) {
      return response;
    }

    let requestPayload;
    let responseData;
    try {
      requestPayload = JSON.parse(String(init?.body || '{}'));
      responseData = await response.clone().json();
    } catch (_) {
      return response;
    }

    caseDirty = true;
    const label = pathname === '/api/claim-package' ? 'claim-package' : 'lifecycle';
    try {
      await createValidatedCheckpoint(requestPayload, responseData, label);
    } catch (error) {
      showWarning(
        `Case state changed in memory, but the durable checkpoint download failed: ${error.message}. ` +
        'Use Export case file before closing this window.'
      );
    }
    return response;
  };

  window.addEventListener('beforeunload', (event) => {
    if (!caseDirty) return;
    event.preventDefault();
    event.returnValue = '';
  });
})();
