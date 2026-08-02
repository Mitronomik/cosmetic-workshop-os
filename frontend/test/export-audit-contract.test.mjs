import test from 'node:test';
import assert from 'node:assert/strict';
import { createLocalArtifactRouteRuntime } from '../dist-tests/export-audit-contract/local-artifacts-reports-runtime.js';
import { transitionLocalArtifactsReportsRouteOwnership } from '../dist-tests/export-audit-contract/local-artifacts-reports-route.js';
import {
  EXPORT_PENDING_AUDIT_COUNT_WARNING,
  EXPORT_PENDING_AUDIT_MESSAGE,
  adoptExportPendingAuditCount,
  exportAuditResult,
  exportAuditWarning,
  exportPendingAuditCount,
} from '../dist-tests/export-audit-contract/export-audit-contract.js';

/**
 * CR-009 B2 frontend contract.
 *
 * The behaviour under test is that one HTTP 201 carries two results — the export
 * file (authoritative) and its Journal entry (secondary) — and that the two stay
 * visibly separate: a pending Journal entry must read as success plus a warning,
 * never as a failed export, and must never cause a second POST.
 */

const messages = { loading:'loading', refreshing:'refreshing', reconciling:'reconciling', initialError:'initial error', refreshError:'refresh warning', refreshSuccess:'refresh ok', mutationBusy:'busy', mutationSuccess:'created', mutationError:'create failed', mutationAmbiguous:'ambiguous network', invalidMutationResponse:'invalid created', mutationRefreshWarning:'created but refresh failed', reconciliationFailed:'still cannot confirm' };

const flush = () => new Promise((resolve) => setImmediate(resolve));
function deferred(){let resolve,reject;const promise=new Promise((res,rej)=>{resolve=res;reject=rej});return {promise,resolve,reject};}

const exportFile = (filename = '20260801T101112131415Z-cosmetic_workshop-export-before_import.json') => ({ filename, path: `/local/exports/${filename}`, created_at: '2026-08-01T10:11:12Z', reason: 'before_import', size_bytes: 3414 });

const recordedResponse = (filename) => ({ export: exportFile(filename), database_path: '/local/cosmetic_workshop.sqlite', export_dir: '/local/exports', entity_counts: { ingredients: 2 }, message: 'Экспорт создан.', audit_status: 'recorded', audit_message: null });
const pendingResponse = (filename) => ({ export: exportFile(filename), database_path: '/local/cosmetic_workshop.sqlite', export_dir: '/local/exports', entity_counts: { ingredients: 2 }, message: 'Экспорт создан.', audit_status: 'pending', audit_message: EXPORT_PENDING_AUDIT_MESSAGE });

const statusResponse = (pending = 0) => ({ database_path: '/local/cosmetic_workshop.sqlite', database_exists: true, database_size_bytes: 40960, export_dir: '/local/exports', export_dir_exists: true, export_count: 1, latest_export: exportFile(), pending_audit_count: pending });

/**
 * An exports route wired exactly as `main.ts` wires it: the mutation result
 * carries the export plus the classified audit outcome, and the UI state mirror
 * is rebuilt the same way on every render.
 */
function makeExportsRoute() {
  const ui = { lastCreatedExport: null, auditWarning: '', pendingAuditCount: null, reason: 'before_import' };
  const h = { active: true, renders: 0, polite: [], assertive: [], focus: [], reads: [], mutations: [], postCount: 0, readCount: 0, ui };
  const runtime = createLocalArtifactRouteRuntime({
    route: 'exports',
    mutationKind: 'create-export',
    messages,
    read: () => { h.readCount++; const d = deferred(); h.reads.push(d); return d.promise; },
    mutate: () => { h.postCount++; const d = deferred(); h.mutations.push(d); return d.promise; },
    validateCreated: (c) => Boolean(c && c.auditValid && c.export && c.export.filename && c.export.path),
    ownsRoute: () => h.active,
    applyRead: (snapshot) => { ui.exports = snapshot.list.exports; adoptExportPendingAuditCount(ui, snapshot.status); },
    applyCreated: (result) => { ui.lastCreatedExport = result.export; ui.auditWarning = result.auditWarning; },
    render: () => { if (h.active) h.renders++; },
    announce: (message, kind) => h[kind === 'assertive' ? 'assertive' : 'polite'].push(message),
    focus: (key) => h.focus.push(key),
  });
  return { h, ui, runtime };
}

/** The `mutate` resolution `main.ts` builds from a create response. */
const mutationResult = (response) => {
  const audit = exportAuditResult(response);
  return { created: { export: response.export, auditValid: audit.valid, auditWarning: audit.warning }, message: `${response.message} Файл: ${response.export.filename}`, commitAccepted: () => { } };
};

const visibleWarning = (ui) => exportAuditWarning(ui);

// ---------------------------------------------------------------------------
// Contract classification
// ---------------------------------------------------------------------------

test('a recorded response is valid only with an explicit null audit_message', () => {
  assert.deepEqual(exportAuditResult(recordedResponse()), { valid: true, status: 'recorded', warning: '' });
  // An absent field is an incomplete contract, not "recorded with no warning":
  // it cannot be told apart from a truncated or older-shaped body.
  assert.equal(exportAuditResult({ ...recordedResponse(), audit_message: undefined }).valid, false);
  const { audit_message: _omitted, ...withoutMessage } = recordedResponse();
  assert.equal(exportAuditResult(withoutMessage).valid, false);
});

test('a pending response is valid only with the exact accepted warning', () => {
  const result = exportAuditResult(pendingResponse());
  assert.equal(result.valid, true);
  assert.equal(result.status, 'pending');
  assert.equal(result.warning, EXPORT_PENDING_AUDIT_MESSAGE);
  assert.equal(result.warning, 'Экспорт создан, но запись в журнал действий пока не добавлена. Приложение повторит попытку при следующем запуске или перед созданием следующего экспорта.');
});

test('an incomplete or unrecognized audit contract is invalid, never a silent success', () => {
  const base = { export: exportFile(), message: 'Экспорт создан.' };
  for (const response of [
    base,
    { ...base, audit_status: 'pending' },
    { ...base, audit_status: 'pending', audit_message: null },
    { ...base, audit_status: 'pending', audit_message: 'какое-то другое предупреждение' },
    // The report-document warning must never be accepted on the exports route.
    { ...base, audit_status: 'pending', audit_message: 'Документ создан, но запись в журнал действий пока не добавлена. Приложение повторит попытку при следующем запуске или перед созданием следующего документа.' },
    { ...base, audit_status: 'recorded', audit_message: 'unexpected' },
    { ...base, audit_status: 'recorded' },
    { ...base, audit_status: 'recorded', audit_message: undefined },
    { ...base, audit_message: null },
    { ...base, audit_status: 'ok', audit_message: null },
    { ...base, audit_status: '', audit_message: null },
    { ...base, audit_status: 'RECORDED', audit_message: null },
    null,
    'nope',
    undefined,
  ]) {
    const result = exportAuditResult(response);
    assert.equal(result.valid, false, JSON.stringify(response));
    assert.equal(result.status, null);
    assert.equal(result.warning, '');
  }
});

test('a knowable pending count is an exact non-negative integer', () => {
  assert.equal(exportPendingAuditCount(statusResponse(3)), 3);
  assert.equal(exportPendingAuditCount(statusResponse(0)), 0);
  assert.equal(exportPendingAuditCount(statusResponse(1)), 1);
});

test('an unknowable pending count is null, never a fabricated zero', () => {
  // `null` and `0` are different answers: `0` is a claim that nothing is
  // pending, and the UI clears a standing warning on it. Anything we cannot
  // read must not be able to make that claim.
  const { pending_audit_count: _omitted, ...withoutField } = statusResponse(1);
  assert.equal(exportPendingAuditCount(withoutField), null);
  for (const value of [undefined, null, -1, -0.5, Number.NaN, Infinity, -Infinity, '2', '', {}, [], true, 0.5, 2.9]) {
    assert.equal(exportPendingAuditCount({ pending_audit_count: value }), null, String(value));
  }
  for (const status of [null, undefined, 'nope', 5]) {
    assert.equal(exportPendingAuditCount(status), null, String(status));
  }
});

test('one warning region: the created-export warning outranks the standing count warning', () => {
  assert.equal(exportAuditWarning({ auditWarning: '', pendingAuditCount: 0 }), '');
  assert.equal(exportAuditWarning({ auditWarning: '', pendingAuditCount: 2 }), EXPORT_PENDING_AUDIT_COUNT_WARNING);
  assert.equal(exportAuditWarning({ auditWarning: EXPORT_PENDING_AUDIT_MESSAGE, pendingAuditCount: 1 }), EXPORT_PENDING_AUDIT_MESSAGE);
  // An unknown count shows nothing on its own, but never suppresses a warning
  // that a create already established.
  assert.equal(exportAuditWarning({ auditWarning: '', pendingAuditCount: null }), '');
  assert.equal(exportAuditWarning({ auditWarning: EXPORT_PENDING_AUDIT_MESSAGE, pendingAuditCount: null }), EXPORT_PENDING_AUDIT_MESSAGE);
});

test('adopting a malformed count preserves the last thing actually known', () => {
  for (const malformed of [{}, { pending_audit_count: undefined }, { pending_audit_count: '3' }, { pending_audit_count: -1 }, { pending_audit_count: 1.5 }, { pending_audit_count: Number.NaN }, { pending_audit_count: Infinity }, null, undefined]) {
    const state = { auditWarning: EXPORT_PENDING_AUDIT_MESSAGE, pendingAuditCount: 2 };
    adoptExportPendingAuditCount(state, malformed);
    assert.equal(state.pendingAuditCount, 2, JSON.stringify(malformed));
    assert.equal(state.auditWarning, EXPORT_PENDING_AUDIT_MESSAGE);
    assert.equal(exportAuditWarning(state), EXPORT_PENDING_AUDIT_MESSAGE);
  }
});

test('adopting a validated zero is the only thing that clears the warning', () => {
  const cleared = { auditWarning: EXPORT_PENDING_AUDIT_MESSAGE, pendingAuditCount: 1 };
  adoptExportPendingAuditCount(cleared, statusResponse(0));
  assert.equal(cleared.pendingAuditCount, 0);
  assert.equal(cleared.auditWarning, '');
  assert.equal(exportAuditWarning(cleared), '');

  const kept = { auditWarning: EXPORT_PENDING_AUDIT_MESSAGE, pendingAuditCount: 1 };
  adoptExportPendingAuditCount(kept, statusResponse(3));
  assert.equal(kept.pendingAuditCount, 3);
  assert.equal(kept.auditWarning, EXPORT_PENDING_AUDIT_MESSAGE);
});

test('neither user-facing warning exposes a filename, path, identifier or database wording', () => {
  for (const warning of [EXPORT_PENDING_AUDIT_MESSAGE, EXPORT_PENDING_AUDIT_COUNT_WARNING]) {
    for (const forbidden of ['.json', '.sqlite', '/', '\\', 'SQLite', 'sqlite', 'operation', 'ledger', 'AuditLog', 'audit_', 'UUID']) {
      assert.ok(!warning.includes(forbidden), `${forbidden} must not appear in: ${warning}`);
    }
    assert.match(warning, /[а-яё]/i);
    // It must not read as a failed export.
    assert.ok(!warning.includes('не создан'), warning);
  }
});

// ---------------------------------------------------------------------------
// Recorded success
// ---------------------------------------------------------------------------

test('recorded success shows ordinary success, no warning, one POST and one refresh', async () => {
  const { h, ui, runtime } = makeExportsRoute();
  runtime.enter();
  runtime.load('initial');
  h.reads[0].resolve({ status: statusResponse(0), list: { exports: [] } });
  await flush();

  runtime.create({ reason: 'before_import' });
  assert.equal(h.postCount, 1);
  h.mutations[0].resolve(mutationResult(recordedResponse()));
  await flush();

  const presentation = runtime.presentation();
  assert.match(presentation.feedback.success, /Экспорт создан\./);
  assert.equal(presentation.feedback.error, '');
  assert.equal(presentation.feedback.warning, '');
  assert.equal(visibleWarning(ui), '');
  assert.equal(ui.lastCreatedExport.reason, 'before_import');
  assert.equal(runtime.lifecycle.state.reconciliationRequired, false);
  // Exactly one refresh follows the create, and no second POST.
  assert.equal(h.readCount, 2);
  h.reads[1].resolve({ status: statusResponse(0), list: { exports: [exportFile()] } });
  await flush();
  assert.equal(h.postCount, 1);
  assert.equal(visibleWarning(ui), '');
  assert.equal(h.polite.filter((m) => /Экспорт создан/.test(m)).length, 1);
  assert.deepEqual(h.focus, ['b3-exports-last-created']);
});

// ---------------------------------------------------------------------------
// Pending success
// ---------------------------------------------------------------------------

test('pending success is a success plus a separate warning, not a failure', async () => {
  const { h, ui, runtime } = makeExportsRoute();
  runtime.enter();
  runtime.load('initial');
  h.reads[0].resolve({ status: statusResponse(0), list: { exports: [] } });
  await flush();

  runtime.create({ reason: 'before_import' });
  h.mutations[0].resolve(mutationResult(pendingResponse()));
  await flush();

  const presentation = runtime.presentation();
  // The export result itself is an ordinary success.
  assert.match(presentation.feedback.success, /Экспорт создан\./);
  assert.equal(presentation.feedback.error, '');
  assert.equal(runtime.lifecycle.state.reconciliationRequired, false);
  // The Journal warning lives in its own region and is not the generic
  // ambiguous-network warning.
  assert.equal(visibleWarning(ui), EXPORT_PENDING_AUDIT_MESSAGE);
  assert.notEqual(visibleWarning(ui), messages.mutationAmbiguous);
  assert.notEqual(visibleWarning(ui), messages.mutationError);
  // The created export metadata is retained, including its canonical reason.
  assert.equal(ui.lastCreatedExport.filename, '20260801T101112131415Z-cosmetic_workshop-export-before_import.json');
  assert.equal(ui.lastCreatedExport.reason, 'before_import');
  assert.equal(h.postCount, 1);
});

test('the pending warning survives the refresh that follows the create', async () => {
  const { h, ui, runtime } = makeExportsRoute();
  runtime.enter();
  runtime.load('initial');
  h.reads[0].resolve({ status: statusResponse(0), list: { exports: [] } });
  await flush();
  runtime.create({ reason: 'before_import' });
  h.mutations[0].resolve(mutationResult(pendingResponse()));
  await flush();

  // The mutation refresh reports the operation as still pending.
  assert.equal(h.readCount, 2);
  h.reads[1].resolve({ status: statusResponse(1), list: { exports: [exportFile()] } });
  await flush();

  assert.equal(ui.pendingAuditCount, 1);
  assert.equal(visibleWarning(ui), EXPORT_PENDING_AUDIT_MESSAGE);
  assert.equal(h.postCount, 1);
  // An ordinary re-render derives the same warning from unchanged state.
  assert.equal(visibleWarning(ui), EXPORT_PENDING_AUDIT_MESSAGE);
});

test('the standing warning clears only when a later status read reports zero', async () => {
  const { h, ui, runtime } = makeExportsRoute();
  runtime.enter();
  runtime.load('initial');
  h.reads[0].resolve({ status: statusResponse(2), list: { exports: [exportFile()] } });
  await flush();
  assert.equal(visibleWarning(ui), EXPORT_PENDING_AUDIT_COUNT_WARNING);

  // Still pending: the warning stays.
  runtime.load('refresh');
  h.reads[1].resolve({ status: statusResponse(1), list: { exports: [exportFile()] } });
  await flush();
  assert.equal(visibleWarning(ui), EXPORT_PENDING_AUDIT_COUNT_WARNING);

  // A failed refresh must not clear it either — nothing was confirmed.
  runtime.load('refresh');
  h.reads[2].reject(new Error('read failed'));
  await flush();
  assert.equal(visibleWarning(ui), EXPORT_PENDING_AUDIT_COUNT_WARNING);

  // A malformed count must not clear it either.
  runtime.load('refresh');
  h.reads[3].resolve({ status: { ...statusResponse(1), pending_audit_count: 'нет' }, list: { exports: [exportFile()] } });
  await flush();
  assert.equal(visibleWarning(ui), EXPORT_PENDING_AUDIT_COUNT_WARNING);

  // Only an authoritative zero clears it.
  runtime.load('refresh');
  h.reads[4].resolve({ status: statusResponse(0), list: { exports: [exportFile()] } });
  await flush();
  assert.equal(visibleWarning(ui), '');
  // A status read never triggers a create.
  assert.equal(h.postCount, 0);
});

test('a pending create followed by a zero count clears both warnings', async () => {
  const { h, ui, runtime } = makeExportsRoute();
  runtime.enter();
  runtime.load('initial');
  h.reads[0].resolve({ status: statusResponse(0), list: { exports: [] } });
  await flush();
  runtime.create({ reason: 'before_import' });
  h.mutations[0].resolve(mutationResult(pendingResponse()));
  await flush();
  h.reads[1].resolve({ status: statusResponse(1), list: { exports: [exportFile()] } });
  await flush();
  assert.equal(visibleWarning(ui), EXPORT_PENDING_AUDIT_MESSAGE);

  // A later read after backend reconciliation reports nothing outstanding.
  runtime.load('refresh');
  h.reads[2].resolve({ status: statusResponse(0), list: { exports: [exportFile()] } });
  await flush();

  assert.equal(ui.auditWarning, '');
  assert.equal(ui.pendingAuditCount, 0);
  assert.equal(visibleWarning(ui), '');
});

// ---------------------------------------------------------------------------
// Invalid contract
// ---------------------------------------------------------------------------

test('an invalid audit contract sends no second POST and shows no false success', async () => {
  const { h, ui, runtime } = makeExportsRoute();
  runtime.enter();
  runtime.load('initial');
  h.reads[0].resolve({ status: statusResponse(0), list: { exports: [] } });
  await flush();

  runtime.create({ reason: 'before_import' });
  h.mutations[0].resolve(mutationResult({ export: exportFile(), message: 'Экспорт создан.', audit_status: 'pending', audit_message: null }));
  await flush();

  // Routed into the existing reconciliation path, not into an ordinary success.
  assert.equal(runtime.lifecycle.state.reconciliationRequired, true);
  assert.equal(runtime.presentation().feedback.success, '');
  assert.equal(runtime.presentation().feedback.error, messages.invalidMutationResponse);
  assert.equal(runtime.presentation().canCreate, false);
  assert.equal(ui.lastCreatedExport, null);
  assert.equal(visibleWarning(ui), '');

  // A further create attempt while locked issues no POST.
  runtime.create({ reason: 'before_import' });
  assert.equal(h.postCount, 1);
  runtime.reconcile();
  h.reads[1].resolve({ status: statusResponse(1), list: { exports: [exportFile()] } });
  await flush();
  assert.equal(runtime.lifecycle.state.reconciliationRequired, false);
  assert.equal(h.postCount, 1);
});

test('a genuinely ambiguous network failure still uses the existing ambiguous warning', async () => {
  const { h, ui, runtime } = makeExportsRoute();
  runtime.enter();
  runtime.create({ reason: 'before_import' });
  h.mutations[0].reject(new TypeError('Failed to fetch'));
  await flush();

  assert.equal(runtime.presentation().feedback.warning, messages.mutationAmbiguous);
  assert.equal(visibleWarning(ui), '');
  assert.equal(h.postCount, 1);
});

// ---------------------------------------------------------------------------
// Route ownership, detachment and accessibility
// ---------------------------------------------------------------------------

test('a pending success that settles after the route is left renders nothing and reconciles', async () => {
  const { h, ui, runtime } = makeExportsRoute();
  runtime.enter();
  runtime.create({ reason: 'before_import' });
  assert.equal(h.postCount, 1);
  runtime.leave();
  h.active = false;

  h.mutations[0].resolve(mutationResult(pendingResponse()));
  await flush();

  // No completion is announced or focused for a route the user has left.
  assert.deepEqual(h.polite, []);
  assert.deepEqual(h.assertive, []);
  assert.deepEqual(h.focus, []);
  assert.equal(ui.lastCreatedExport, null);
  assert.equal(ui.auditWarning, '');
  assert.equal(runtime.lifecycle.state.reconciliationRequired, true);

  h.active = true;
  runtime.enter();
  runtime.reconcile();
  h.reads[0].resolve({ status: statusResponse(1), list: { exports: [exportFile()] } });
  await flush();
  assert.equal(runtime.lifecycle.state.reconciliationRequired, false);
  // The authoritative status still surfaces the pending Journal state.
  assert.equal(visibleWarning(ui), EXPORT_PENDING_AUDIT_COUNT_WARNING);
  assert.equal(h.postCount, 1);
});

test('navigating away and back preserves the pending obligation without a duplicate POST', async () => {
  const { h, ui, runtime } = makeExportsRoute();
  runtime.enter();
  runtime.load('initial');
  h.reads[0].resolve({ status: statusResponse(1), list: { exports: [exportFile()] } });
  await flush();
  assert.equal(visibleWarning(ui), EXPORT_PENDING_AUDIT_COUNT_WARNING);

  transitionLocalArtifactsReportsRouteOwnership({ exports: runtime }, 'exports', null);
  runtime.lifecycle.clearTransientFeedback();
  transitionLocalArtifactsReportsRouteOwnership({ exports: runtime }, null, 'exports');

  // The count is state, not transient feedback, so it survives navigation.
  assert.equal(visibleWarning(ui), EXPORT_PENDING_AUDIT_COUNT_WARNING);
  assert.equal(h.postCount, 0);
});

test('pending success announces politely once and focuses the created-export target', async () => {
  const { h, runtime } = makeExportsRoute();
  runtime.enter();
  runtime.create({ reason: 'before_import' });
  h.mutations[0].resolve(mutationResult(pendingResponse()));
  await flush();

  assert.equal(h.polite.length, 1);
  assert.match(h.polite[0], /Экспорт создан\./);
  assert.deepEqual(h.assertive, []);
  assert.deepEqual(h.focus, ['b3-exports-last-created']);
});

// ---------------------------------------------------------------------------
// Production wiring and blast radius
// ---------------------------------------------------------------------------

const mainSource = async () => {
  const fs = await import('node:fs/promises');
  return fs.readFile(new URL('../src/main.ts', import.meta.url), 'utf8');
};

test('main.ts classifies the export audit contract through the shared module, not inline', async () => {
  const source = await mainSource();
  assert.match(source, /import \{ adoptExportPendingAuditCount, exportAuditResult, exportAuditWarning, exportPendingAuditCount \} from '\.\/export-audit-contract\.js';/);
  assert.match(source, /exportAuditResult\(response\)/);
  assert.match(source, /exportPendingAuditNotice\(\)/);
  // The accepted Russian strings are owned by the contract module alone.
  assert.doesNotMatch(source, /Экспорт создан, но запись в журнал действий/);
  assert.doesNotMatch(source, /Некоторые созданные экспорты ещё не добавлены/);
  // No re-POST or bespoke retry was introduced for a pending audit.
  assert.doesNotMatch(source, /audit_status === 'pending'[^\n]*createExport/);
  assert.doesNotMatch(source, /setTimeout\([^\n]*createExport/);
});

test('the pending notice is rendered as its own warning region, apart from the success message', async () => {
  const source = await mainSource();
  const notice = source.split('\n').find((line) => line.includes('function exportPendingAuditNotice()'));
  assert.ok(notice, 'exportPendingAuditNotice must exist');
  assert.ok(notice.includes('exportAuditWarning(exportUiState)'), 'its text must come from the shared module');
  assert.ok(notice.includes("feedbackMessage('warning', warning)"), 'it must render as a warning region');
  assert.doesNotMatch(source, /feedbackMessage\('error', warning\)/);
});

test('the create response reason is rendered as received and never reconstructed', async () => {
  const source = await mainSource();
  // CR-005/CR-006: the backend owns the canonical slug; the frontend only maps
  // known slugs to labels and otherwise renders them verbatim.
  assert.match(source, /function exportReasonLabelRaw/);
  assert.doesNotMatch(source, /normalizeExportReason|sanitizeExportReason/);
});

test('the exports route never reads another artifact kind\'s audit contract', async () => {
  const source = await mainSource();
  // C3-II-B3 has since given manual backups their own contract module. The
  // invariant this test protects is unchanged and is the reason the three
  // modules were never generalized: an export's warning must be unreachable
  // from the backups route, and a backup's from the exports route.
  const exportRuntime = source.split('\n').find((line) => line.includes('const exportRuntime = createLocalArtifactRouteRuntime'));
  assert.ok(exportRuntime);
  assert.doesNotMatch(exportRuntime, /backupAudit|reportDocumentAudit/);
  const backupRuntime = source.split('\n').find((line) => line.includes('const backupRuntime = createLocalArtifactRouteRuntime'));
  assert.ok(backupRuntime);
  assert.doesNotMatch(backupRuntime, /exportAudit/);
});

test('the exports page keeps its focus targets and stays keyboard operable', async () => {
  const source = await mainSource();
  for (const key of ['b3-exports-retry', 'b3-exports-refresh', 'b3-exports-create', 'b3-exports-last-created', 'b3-exports-content']) {
    assert.match(source, new RegExp(`data-focus-key="${key}"`));
  }
  // The pending notice is inserted into the page grid before the cards, and
  // introduces no new interactive control that would need its own binding.
  assert.match(source, /\$\{exportPendingAuditNotice\(\)\}/);
});

test('desktop and narrow viewports share one warning region with no fixed width', async () => {
  const fs = await import('node:fs/promises');
  const styles = await fs.readFile(new URL('../src/styles.css', import.meta.url), 'utf8');
  const source = await mainSource();
  // The notice reuses the existing feedback component rather than introducing a
  // new element that would need its own responsive rules.
  const notice = source.split('\n').find((line) => line.includes('function exportPendingAuditNotice()'));
  assert.ok(notice.includes('feedbackMessage('));
  assert.match(styles, /\.feedback/);
  assert.doesNotMatch(notice, /style="width:\s*\d+px/);
});

// ---------------------------------------------------------------------------
// Verification failure — never a created export
//
// The backend now refuses an export it could not verify, with a fixed HTTP 500
// instead of `201 pending`. The route must present that as an ordinary error:
// no success text, no pending-Journal warning, one POST, and no auto-retry.
// ---------------------------------------------------------------------------

const verificationFailure = () => {
  const error = new Error(
    'Не удалось проверить созданный экспорт, поэтому он не считается надёжным. Данные мастерской не изменялись.',
  );
  error.status = 500;
  error.payload = {
    detail: {
      code: 'export_verification_failed',
      message: 'Не удалось проверить созданный экспорт, поэтому он не считается надёжным. Данные мастерской не изменялись.',
      next_action: 'Повторите создание экспорта. Если ошибка повторяется, перезапустите приложение.',
    },
  };
  return error;
};

test('a verification failure is a definite error, not an ambiguous result', async () => {
  const { h, ui, runtime } = makeExportsRoute();
  runtime.enter();
  runtime.load('initial');
  h.reads[0].resolve({ status: statusResponse(0), list: { exports: [] } });
  await flush();

  runtime.create({ reason: 'before_import' });
  assert.equal(h.postCount, 1);
  h.mutations[0].reject(verificationFailure());
  await flush();

  const presentation = runtime.presentation();
  // The existing error region, not the ambiguous-network warning.
  assert.equal(presentation.feedback.error, messages.mutationError);
  assert.equal(presentation.feedback.warning, '');
  assert.equal(presentation.feedback.success, '');
  // Never presented as a created export.
  assert.ok(!/Экспорт создан/.test(presentation.feedback.success));
  assert.equal(ui.lastCreatedExport, null);
  // No pending-Journal warning: this is not a verified artifact.
  assert.equal(visibleWarning(ui), '');
  assert.equal(ui.auditWarning, '');
  // One POST, no automatic retry, and no reconciliation lock.
  assert.equal(h.postCount, 1);
  assert.equal(runtime.lifecycle.state.reconciliationRequired, false);
});

test('a verification failure leaks no filename, path or verifier detail to the screen', async () => {
  const { h, ui, runtime } = makeExportsRoute();
  runtime.enter();
  runtime.create({ reason: 'before_import' });
  h.mutations[0].reject(verificationFailure());
  await flush();

  const shown = [
    runtime.presentation().feedback.error,
    runtime.presentation().feedback.warning,
    runtime.presentation().feedback.success,
    visibleWarning(ui),
    ...h.polite,
    ...h.assertive,
  ].join(' ');
  for (const forbidden of [
    '20260801T101112131415Z',
    '/local/exports',
    'cosmetic_workshop.sqlite',
    'export_schema_version',
    'operation_id',
    'sqlite',
    'ingredients',
  ]) {
    assert.ok(!shown.includes(forbidden), `leaked: ${forbidden}`);
  }
});

test('a later successful create still works after a verification failure', async () => {
  const { h, ui, runtime } = makeExportsRoute();
  runtime.enter();
  runtime.create({ reason: 'before_import' });
  h.mutations[0].reject(verificationFailure());
  await flush();
  assert.equal(runtime.presentation().canCreate, true);

  runtime.create({ reason: 'before_import' });
  assert.equal(h.postCount, 2);
  h.mutations[1].resolve(mutationResult(recordedResponse()));
  await flush();

  assert.match(runtime.presentation().feedback.success, /Экспорт создан\./);
  assert.equal(visibleWarning(ui), '');
});
