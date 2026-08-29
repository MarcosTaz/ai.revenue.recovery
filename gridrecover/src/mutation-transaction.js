'use strict';

async function transactMutation({ store, audit, persist = null, mutate, rollbackExternal = null }) {
  if (!store || typeof store.exportState !== 'function' || typeof store.replaceState !== 'function') throw new Error('TRANSACTION_STORE_INVALID');
  if (!audit || typeof audit.exportState !== 'function' || typeof audit.replaceState !== 'function') throw new Error('TRANSACTION_AUDIT_INVALID');
  if (typeof mutate !== 'function') throw new Error('TRANSACTION_MUTATE_REQUIRED');

  const storeBefore = store.exportState();
  const auditBefore = audit.exportState();

  try {
    const result = await mutate();
    if (persist) await persist({ store, audit });
    return result;
  } catch (error) {
    let rollbackError = null;
    try { store.replaceState(storeBefore); } catch (e) { rollbackError = e; }
    try { audit.replaceState(auditBefore); } catch (e) { rollbackError = rollbackError || e; }
    if (rollbackExternal) {
      try { await rollbackExternal(); } catch (e) { rollbackError = rollbackError || e; }
    }
    if (rollbackError) {
      const fatal = new Error('TRANSACTION_ROLLBACK_FAILED');
      fatal.cause = rollbackError;
      throw fatal;
    }
    if (error && error.message === 'PERSISTENCE_FAILED') throw error;
    throw error;
  }
}

module.exports = { transactMutation };
