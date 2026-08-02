import test from 'node:test';
import assert from 'node:assert/strict';
import { createLocalArtifactRouteRuntime } from '../dist-tests/report-document-audit-contract/local-artifacts-reports-runtime.js';
import { transitionLocalArtifactsReportsRouteOwnership } from '../dist-tests/report-document-audit-contract/local-artifacts-reports-route.js';
import {
  REPORT_DOCUMENT_PENDING_AUDIT_COUNT_WARNING,
  REPORT_DOCUMENT_PENDING_AUDIT_MESSAGE,
  adoptReportDocumentPendingAuditCount,
  reportDocumentAuditResult,
  reportDocumentAuditWarning,
  reportDocumentPendingAuditCount,
} from '../dist-tests/report-document-audit-contract/report-document-audit-contract.js';

/**
 * CR-009 B1 frontend contract.
 *
 * The behaviour under test is that one HTTP 201 carries two results — the
 * document (authoritative) and its Journal entry (secondary) — and that the two
 * stay visibly separate: a pending Journal entry must read as success plus a
 * warning, never as a failed document, and must never cause a second POST.
 */

const messages = { loading:'loading', refreshing:'refreshing', reconciling:'reconciling', initialError:'initial error', refreshError:'refresh warning', refreshSuccess:'refresh ok', mutationBusy:'busy', mutationSuccess:'created', mutationError:'create failed', mutationAmbiguous:'ambiguous network', invalidMutationResponse:'invalid created', mutationRefreshWarning:'created but refresh failed', reconciliationFailed:'still cannot confirm' };

const flush = () => new Promise((resolve) => setImmediate(resolve));
function deferred(){let resolve,reject;const promise=new Promise((res,rej)=>{resolve=res;reject=rej});return {promise,resolve,reject};}

const documentMetadata = (id = 'workshop-overview-20260731-101112') => ({ id, document_type: 'workshop_overview', format: 'markdown', filename: `${id}.md`, metadata_filename: `${id}.json`, created_at: '2026-07-31T10:11:12Z', source: 'reports.overview', source_generated_at: '2026-07-31T10:11:00Z', title: 'Сводка мастерской', warnings_count: 0, size_bytes: 1024 });

const recordedResponse = (id) => ({ document: documentMetadata(id), message: 'Документ отчета создан.', audit_status: 'recorded', audit_message: null });
const pendingResponse = (id) => ({ document: documentMetadata(id), message: 'Документ отчета создан.', audit_status: 'pending', audit_message: REPORT_DOCUMENT_PENDING_AUDIT_MESSAGE });

const statusResponse = (pending = 0) => ({ documents_dir: '/local/exports/report-documents', available_formats: ['markdown'], available_document_types: ['workshop_overview'], can_create: true, documents_count: 1, message: 'Документы отчетов можно создавать вручную.', pending_audit_count: pending });

/**
 * A report-documents route wired exactly as `main.ts` wires it: the mutation
 * result carries the document plus the classified audit outcome, and the UI
 * state mirror is rebuilt the same way on every render.
 */
function makeReportDocumentsRoute() {
  const ui = { lastCreatedDocument: null, auditWarning: '', pendingAuditCount: null, reason: 'еженедельная проверка' };
  const h = { active: true, renders: 0, polite: [], assertive: [], focus: [], reads: [], mutations: [], postCount: 0, readCount: 0, ui };
  const runtime = createLocalArtifactRouteRuntime({
    route: 'reportDocuments',
    mutationKind: 'create-report-document',
    messages,
    read: () => { h.readCount++; const d = deferred(); h.reads.push(d); return d.promise; },
    mutate: () => { h.postCount++; const d = deferred(); h.mutations.push(d); return d.promise; },
    validateCreated: (c) => Boolean(c && c.auditValid && c.document && c.document.id && c.document.filename && c.document.format),
    ownsRoute: () => h.active,
    applyRead: (snapshot) => { ui.documents = snapshot.list.items; adoptReportDocumentPendingAuditCount(ui, snapshot.status); },
    applyCreated: (result) => { ui.lastCreatedDocument = result.document; ui.auditWarning = result.auditWarning; },
    render: () => { if (h.active) h.renders++; },
    announce: (message, kind) => h[kind === 'assertive' ? 'assertive' : 'polite'].push(message),
    focus: (key) => h.focus.push(key),
  });
  return { h, ui, runtime };
}

/** The `mutate` resolution `main.ts` builds from a create response. */
const mutationResult = (response) => {
  const audit = reportDocumentAuditResult(response);
  return { created: { document: response.document, auditValid: audit.valid, auditWarning: audit.warning }, message: `${response.message} Его можно открыть или скачать из списка ниже.`, commitAccepted: () => { } };
};

const visibleWarning = (ui) => reportDocumentAuditWarning(ui);

// ---------------------------------------------------------------------------
// Contract classification
// ---------------------------------------------------------------------------

test('a recorded response is valid only with an explicit null audit_message', () => {
  const result = reportDocumentAuditResult(recordedResponse());
  assert.deepEqual(result, { valid: true, status: 'recorded', warning: '' });
  // An absent field is an incomplete contract, not "recorded with no warning":
  // it cannot be told apart from a truncated or older-shaped body.
  assert.equal(reportDocumentAuditResult({ ...recordedResponse(), audit_message: undefined }).valid, false);
  const withoutMessage = { document: documentMetadata(), message: 'Документ отчета создан.', audit_status: 'recorded' };
  assert.equal(reportDocumentAuditResult(withoutMessage).valid, false);
});

test('a pending response is valid only with the exact accepted warning', () => {
  const result = reportDocumentAuditResult(pendingResponse());
  assert.equal(result.valid, true);
  assert.equal(result.status, 'pending');
  assert.equal(result.warning, REPORT_DOCUMENT_PENDING_AUDIT_MESSAGE);
  assert.equal(result.warning, 'Документ создан, но запись в журнал действий пока не добавлена. Приложение повторит попытку при следующем запуске или перед созданием следующего документа.');
});

test('an incomplete or unrecognized audit contract is invalid, never a silent success', () => {
  const document = documentMetadata();
  const base = { document, message: 'Документ отчета создан.' };
  for (const response of [
    base,
    { ...base, audit_status: 'pending' },
    { ...base, audit_status: 'pending', audit_message: null },
    { ...base, audit_status: 'pending', audit_message: 'какое-то другое предупреждение' },
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
    const result = reportDocumentAuditResult(response);
    assert.equal(result.valid, false, JSON.stringify(response));
    assert.equal(result.status, null);
    assert.equal(result.warning, '');
  }
});

test('a knowable pending count is an exact non-negative integer', () => {
  assert.equal(reportDocumentPendingAuditCount(statusResponse(3)), 3);
  assert.equal(reportDocumentPendingAuditCount(statusResponse(0)), 0);
  assert.equal(reportDocumentPendingAuditCount(statusResponse(1)), 1);
});

test('an unknowable pending count is null, never a fabricated zero', () => {
  // `null` and `0` are different answers: `0` is a claim that nothing is
  // pending, and the UI clears a standing warning on it. Anything we cannot
  // read must not be able to make that claim.
  const { pending_audit_count: _omitted, ...withoutField } = statusResponse(1);
  assert.equal(reportDocumentPendingAuditCount(withoutField), null);
  for (const value of [undefined, null, -1, -0.5, Number.NaN, Infinity, -Infinity, '2', '', {}, [], true, 0.5, 2.9]) {
    assert.equal(reportDocumentPendingAuditCount({ pending_audit_count: value }), null, String(value));
  }
  for (const status of [null, undefined, 'nope', 5]) {
    assert.equal(reportDocumentPendingAuditCount(status), null, String(status));
  }
});

test('one warning region: the created-document warning outranks the standing count warning', () => {
  assert.equal(reportDocumentAuditWarning({ auditWarning: '', pendingAuditCount: 0 }), '');
  assert.equal(reportDocumentAuditWarning({ auditWarning: '', pendingAuditCount: 2 }), REPORT_DOCUMENT_PENDING_AUDIT_COUNT_WARNING);
  assert.equal(reportDocumentAuditWarning({ auditWarning: REPORT_DOCUMENT_PENDING_AUDIT_MESSAGE, pendingAuditCount: 1 }), REPORT_DOCUMENT_PENDING_AUDIT_MESSAGE);
  // An unknown count shows nothing on its own, but never suppresses a warning
  // that a create already established.
  assert.equal(reportDocumentAuditWarning({ auditWarning: '', pendingAuditCount: null }), '');
  assert.equal(reportDocumentAuditWarning({ auditWarning: REPORT_DOCUMENT_PENDING_AUDIT_MESSAGE, pendingAuditCount: null }), REPORT_DOCUMENT_PENDING_AUDIT_MESSAGE);
});

test('adopting a malformed count preserves the last thing actually known', () => {
  for (const malformed of [{}, { pending_audit_count: undefined }, { pending_audit_count: '3' }, { pending_audit_count: -1 }, { pending_audit_count: 1.5 }, { pending_audit_count: Number.NaN }, { pending_audit_count: Infinity }, null, undefined]) {
    const state = { auditWarning: REPORT_DOCUMENT_PENDING_AUDIT_MESSAGE, pendingAuditCount: 2 };
    adoptReportDocumentPendingAuditCount(state, malformed);
    assert.equal(state.pendingAuditCount, 2, JSON.stringify(malformed));
    assert.equal(state.auditWarning, REPORT_DOCUMENT_PENDING_AUDIT_MESSAGE);
    assert.equal(reportDocumentAuditWarning(state), REPORT_DOCUMENT_PENDING_AUDIT_MESSAGE);
  }
});

test('adopting a validated zero is the only thing that clears the warning', () => {
  const cleared = { auditWarning: REPORT_DOCUMENT_PENDING_AUDIT_MESSAGE, pendingAuditCount: 1 };
  adoptReportDocumentPendingAuditCount(cleared, statusResponse(0));
  assert.equal(cleared.pendingAuditCount, 0);
  assert.equal(cleared.auditWarning, '');
  assert.equal(reportDocumentAuditWarning(cleared), '');

  const kept = { auditWarning: REPORT_DOCUMENT_PENDING_AUDIT_MESSAGE, pendingAuditCount: 1 };
  adoptReportDocumentPendingAuditCount(kept, statusResponse(3));
  assert.equal(kept.pendingAuditCount, 3);
  assert.equal(kept.auditWarning, REPORT_DOCUMENT_PENDING_AUDIT_MESSAGE);
});

test('neither user-facing warning exposes a filename, path, identifier or database wording', () => {
  for (const warning of [REPORT_DOCUMENT_PENDING_AUDIT_MESSAGE, REPORT_DOCUMENT_PENDING_AUDIT_COUNT_WARNING]) {
    for (const forbidden of ['.md', '.json', '.pdf', '/', '\\', 'SQLite', 'sqlite', 'operation', 'ledger', 'AuditLog', 'audit_', 'UUID']) {
      assert.ok(!warning.includes(forbidden), `${forbidden} must not appear in: ${warning}`);
    }
    assert.match(warning, /[а-яё]/i);
  }
});

// ---------------------------------------------------------------------------
// Recorded success
// ---------------------------------------------------------------------------

test('recorded success shows ordinary success, no warning, one POST and one refresh', async () => {
  const { h, ui, runtime } = makeReportDocumentsRoute();
  runtime.enter();
  runtime.load('initial');
  h.reads[0].resolve({ status: statusResponse(0), list: { items: [] } });
  await flush();

  runtime.create({ format: 'markdown' });
  assert.equal(h.postCount, 1);
  h.mutations[0].resolve(mutationResult(recordedResponse()));
  await flush();

  const presentation = runtime.presentation();
  assert.match(presentation.feedback.success, /Документ отчета создан\./);
  assert.equal(presentation.feedback.error, '');
  assert.equal(presentation.feedback.warning, '');
  assert.equal(visibleWarning(ui), '');
  assert.equal(ui.lastCreatedDocument.id, 'workshop-overview-20260731-101112');
  assert.equal(runtime.lifecycle.state.reconciliationRequired, false);
  // Exactly one refresh follows the create, and no second POST.
  assert.equal(h.readCount, 2);
  h.reads[1].resolve({ status: statusResponse(0), list: { items: [documentMetadata()] } });
  await flush();
  assert.equal(h.postCount, 1);
  assert.equal(visibleWarning(ui), '');
  assert.equal(h.polite.filter((m) => /Документ отчета создан/.test(m)).length, 1);
  assert.deepEqual(h.focus, ['b3-report-documents-last-created']);
});

// ---------------------------------------------------------------------------
// Pending success
// ---------------------------------------------------------------------------

test('pending success is a success plus a separate warning, not a failure', async () => {
  const { h, ui, runtime } = makeReportDocumentsRoute();
  runtime.enter();
  runtime.load('initial');
  h.reads[0].resolve({ status: statusResponse(0), list: { items: [] } });
  await flush();

  runtime.create({ format: 'markdown' });
  h.mutations[0].resolve(mutationResult(pendingResponse()));
  await flush();

  const presentation = runtime.presentation();
  // The document result itself is an ordinary success.
  assert.match(presentation.feedback.success, /Документ отчета создан\./);
  assert.equal(presentation.feedback.error, '');
  assert.equal(runtime.lifecycle.state.reconciliationRequired, false);
  // The Journal warning lives in its own region and is not the generic
  // ambiguous-network warning.
  assert.equal(visibleWarning(ui), REPORT_DOCUMENT_PENDING_AUDIT_MESSAGE);
  assert.notEqual(visibleWarning(ui), messages.mutationAmbiguous);
  assert.notEqual(visibleWarning(ui), messages.mutationError);
  // The created document metadata is retained.
  assert.equal(ui.lastCreatedDocument.id, 'workshop-overview-20260731-101112');
  assert.equal(ui.lastCreatedDocument.filename, 'workshop-overview-20260731-101112.md');
  assert.equal(h.postCount, 1);
});

test('the pending warning survives the refresh that follows the create', async () => {
  const { h, ui, runtime } = makeReportDocumentsRoute();
  runtime.enter();
  runtime.load('initial');
  h.reads[0].resolve({ status: statusResponse(0), list: { items: [] } });
  await flush();
  runtime.create({ format: 'markdown' });
  h.mutations[0].resolve(mutationResult(pendingResponse()));
  await flush();

  // The mutation refresh reports the operation as still pending.
  assert.equal(h.readCount, 2);
  h.reads[1].resolve({ status: statusResponse(1), list: { items: [documentMetadata()] } });
  await flush();

  assert.equal(ui.pendingAuditCount, 1);
  assert.equal(visibleWarning(ui), REPORT_DOCUMENT_PENDING_AUDIT_MESSAGE);
  assert.equal(h.postCount, 1);
  // An ordinary re-render derives the same warning from unchanged state.
  assert.equal(visibleWarning(ui), REPORT_DOCUMENT_PENDING_AUDIT_MESSAGE);
  assert.equal(visibleWarning(ui), REPORT_DOCUMENT_PENDING_AUDIT_MESSAGE);
});

test('the standing warning clears only when a later status read reports zero', async () => {
  const { h, ui, runtime } = makeReportDocumentsRoute();
  runtime.enter();
  runtime.load('initial');
  h.reads[0].resolve({ status: statusResponse(2), list: { items: [documentMetadata()] } });
  await flush();
  assert.equal(visibleWarning(ui), REPORT_DOCUMENT_PENDING_AUDIT_COUNT_WARNING);

  // Still pending: the warning stays.
  runtime.load('refresh');
  h.reads[1].resolve({ status: statusResponse(1), list: { items: [documentMetadata()] } });
  await flush();
  assert.equal(visibleWarning(ui), REPORT_DOCUMENT_PENDING_AUDIT_COUNT_WARNING);

  // A failed refresh must not clear it either — nothing was confirmed.
  runtime.load('refresh');
  h.reads[2].reject(new Error('read failed'));
  await flush();
  assert.equal(visibleWarning(ui), REPORT_DOCUMENT_PENDING_AUDIT_COUNT_WARNING);

  // Only an authoritative zero clears it.
  runtime.load('refresh');
  h.reads[3].resolve({ status: statusResponse(0), list: { items: [documentMetadata()] } });
  await flush();
  assert.equal(visibleWarning(ui), '');
  assert.equal(h.postCount, 0);
});

test('a pending create followed by a zero count clears both warnings', async () => {
  const { h, ui, runtime } = makeReportDocumentsRoute();
  runtime.enter();
  runtime.load('initial');
  h.reads[0].resolve({ status: statusResponse(0), list: { items: [] } });
  await flush();
  runtime.create({ format: 'markdown' });
  h.mutations[0].resolve(mutationResult(pendingResponse()));
  await flush();
  h.reads[1].resolve({ status: statusResponse(1), list: { items: [documentMetadata()] } });
  await flush();
  assert.equal(visibleWarning(ui), REPORT_DOCUMENT_PENDING_AUDIT_MESSAGE);

  // A later read after backend reconciliation reports nothing outstanding.
  runtime.load('refresh');
  h.reads[2].resolve({ status: statusResponse(0), list: { items: [documentMetadata()] } });
  await flush();

  assert.equal(ui.auditWarning, '');
  assert.equal(ui.pendingAuditCount, 0);
  assert.equal(visibleWarning(ui), '');
});

// ---------------------------------------------------------------------------
// Invalid contract
// ---------------------------------------------------------------------------

test('an invalid audit contract sends no second POST and shows no false success', async () => {
  const { h, ui, runtime } = makeReportDocumentsRoute();
  runtime.enter();
  runtime.load('initial');
  h.reads[0].resolve({ status: statusResponse(0), list: { items: [] } });
  await flush();

  runtime.create({ format: 'markdown' });
  h.mutations[0].resolve(mutationResult({ document: documentMetadata(), message: 'Документ отчета создан.', audit_status: 'pending', audit_message: null }));
  await flush();

  // Routed into the existing reconciliation path, not into an ordinary success.
  assert.equal(runtime.lifecycle.state.reconciliationRequired, true);
  assert.equal(runtime.presentation().feedback.success, '');
  assert.equal(runtime.presentation().feedback.error, messages.invalidMutationResponse);
  assert.equal(runtime.presentation().canCreate, false);
  assert.equal(ui.lastCreatedDocument, null);
  assert.equal(visibleWarning(ui), '');

  // A further create attempt while locked issues no POST.
  runtime.create({ format: 'markdown' });
  assert.equal(h.postCount, 1);
  runtime.reconcile();
  h.reads[1].resolve({ status: statusResponse(1), list: { items: [documentMetadata()] } });
  await flush();
  assert.equal(runtime.lifecycle.state.reconciliationRequired, false);
  assert.equal(h.postCount, 1);
});

test('a genuinely ambiguous network failure still uses the existing ambiguous warning', async () => {
  const { h, ui, runtime } = makeReportDocumentsRoute();
  runtime.enter();
  runtime.create({ format: 'markdown' });
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
  const { h, ui, runtime } = makeReportDocumentsRoute();
  runtime.enter();
  runtime.create({ format: 'markdown' });
  assert.equal(h.postCount, 1);
  runtime.leave();
  h.active = false;

  h.mutations[0].resolve(mutationResult(pendingResponse()));
  await flush();

  // No completion is announced or focused for a route the user has left.
  assert.deepEqual(h.polite, []);
  assert.deepEqual(h.assertive, []);
  assert.deepEqual(h.focus, []);
  assert.equal(ui.lastCreatedDocument, null);
  assert.equal(ui.auditWarning, '');
  assert.equal(runtime.lifecycle.state.reconciliationRequired, true);

  h.active = true;
  runtime.enter();
  runtime.reconcile();
  h.reads[0].resolve({ status: statusResponse(1), list: { items: [documentMetadata()] } });
  await flush();
  assert.equal(runtime.lifecycle.state.reconciliationRequired, false);
  // The authoritative status still surfaces the pending Journal state.
  assert.equal(visibleWarning(ui), REPORT_DOCUMENT_PENDING_AUDIT_COUNT_WARNING);
  assert.equal(h.postCount, 1);
});

test('navigating away and back preserves the pending obligation without a duplicate POST', async () => {
  const { h, ui, runtime } = makeReportDocumentsRoute();
  runtime.enter();
  runtime.load('initial');
  h.reads[0].resolve({ status: statusResponse(1), list: { items: [documentMetadata()] } });
  await flush();
  assert.equal(visibleWarning(ui), REPORT_DOCUMENT_PENDING_AUDIT_COUNT_WARNING);

  transitionLocalArtifactsReportsRouteOwnership({ reportDocuments: runtime }, 'reportDocuments', null);
  runtime.lifecycle.clearTransientFeedback();
  transitionLocalArtifactsReportsRouteOwnership({ reportDocuments: runtime }, null, 'reportDocuments');

  // The count is state, not transient feedback, so it survives navigation.
  assert.equal(visibleWarning(ui), REPORT_DOCUMENT_PENDING_AUDIT_COUNT_WARNING);
  assert.equal(h.postCount, 0);
});

test('pending success announces politely once and focuses the created-document target', async () => {
  const { h, runtime } = makeReportDocumentsRoute();
  runtime.enter();
  runtime.create({ format: 'markdown' });
  h.mutations[0].resolve(mutationResult(pendingResponse()));
  await flush();

  assert.equal(h.polite.length, 1);
  assert.match(h.polite[0], /Документ отчета создан\./);
  assert.deepEqual(h.assertive, []);
  assert.deepEqual(h.focus, ['b3-report-documents-last-created']);
});

// ---------------------------------------------------------------------------
// Production wiring and blast radius
// ---------------------------------------------------------------------------

const mainSource = async () => {
  const fs = await import('node:fs/promises');
  return fs.readFile(new URL('../src/main.ts', import.meta.url), 'utf8');
};

test('main.ts classifies the audit contract through the shared module, not inline', async () => {
  const source = await mainSource();
  assert.match(source, /import \{ adoptReportDocumentPendingAuditCount, reportDocumentAuditResult, reportDocumentAuditWarning, reportDocumentPendingAuditCount \} from '\.\/report-document-audit-contract\.js';/);
  assert.match(source, /reportDocumentAuditResult\(response\)/);
  assert.match(source, /reportDocumentsPendingAuditNotice\(\)/);
  // The accepted Russian strings are owned by the contract module alone.
  assert.doesNotMatch(source, /Документ создан, но запись в журнал действий/);
  assert.doesNotMatch(source, /Некоторые созданные документы ещё не добавлены/);
  // No re-POST or bespoke retry was introduced for a pending audit.
  assert.doesNotMatch(source, /audit_status === 'pending'[^\n]*createOverviewReportDocument/);
  assert.doesNotMatch(source, /setTimeout\([^\n]*createOverviewReportDocument/);
});

test('the pending notice is rendered as its own warning region, apart from the success message', async () => {
  const source = await mainSource();
  const notice = source.split('\n').find((line) => line.includes('function reportDocumentsPendingAuditNotice()'));
  assert.ok(notice, 'reportDocumentsPendingAuditNotice must exist');
  assert.ok(notice.includes('reportDocumentAuditWarning(reportDocumentsUiState)'), 'its text must come from the shared module');
  assert.ok(notice.includes("feedbackMessage('warning', warning)"), 'it must render as a warning region');
  // It is never rendered as an error tone.
  assert.doesNotMatch(source, /feedbackMessage\('error', warning\)/);
});

test('Backup and Export each use their own contract, never this one', async () => {
  const source = await mainSource();
  // CR-009 B2 gave exports their own contract module and B3 gave manual backups
  // theirs, each with its own backend-owned Russian wording. Sharing this one
  // would let a document's warning appear on /exports or /backups, which is the
  // reason the three were never generalized into one "artifact" abstraction.
  const backupMutate = source.split('\n').find((line) => line.includes('const backupRuntime = createLocalArtifactRouteRuntime'));
  const exportMutate = source.split('\n').find((line) => line.includes('const exportRuntime = createLocalArtifactRouteRuntime'));
  assert.ok(backupMutate && exportMutate);
  assert.doesNotMatch(backupMutate, /reportDocumentAudit/);
  assert.doesNotMatch(backupMutate, /exportAudit/);
  assert.match(backupMutate, /backupAuditResult/);
  assert.doesNotMatch(exportMutate, /reportDocumentAudit/);
  assert.doesNotMatch(exportMutate, /backupAudit/);
  assert.match(exportMutate, /exportAuditResult/);
});

test('the report-documents page keeps its focus targets and stays keyboard operable', async () => {
  const source = await mainSource();
  for (const key of ['b3-report-documents-retry', 'b3-report-documents-refresh', 'b3-report-documents-create', 'b3-report-documents-last-created', 'b3-report-documents-content']) {
    assert.match(source, new RegExp(`data-focus-key="${key}"`));
  }
  // The pending notice is inserted into the page grid, before the cards, and
  // introduces no new interactive control that would need its own binding.
  assert.match(source, /\$\{reportDocumentsPendingAuditNotice\(\)\}\$\{reportDocumentsUiState\.status === 'error'/);
});

test('desktop and narrow viewports share one warning region with no fixed width', async () => {
  const fs = await import('node:fs/promises');
  const styles = await fs.readFile(new URL('../src/styles.css', import.meta.url), 'utf8');
  const source = await mainSource();
  // The notice reuses the existing feedback component rather than introducing a
  // new element that would need its own responsive rules.
  const notice = source.split('\n').find((line) => line.includes('function reportDocumentsPendingAuditNotice()'));
  assert.ok(notice.includes('feedbackMessage('));
  assert.match(styles, /\.feedback/);
  assert.doesNotMatch(notice, /style="width:\s*\d+px/);
});

// ---------------------------------------------------------------------------
// Verification failure — never a created document
//
// The backend now refuses a document pair it could not verify, with a fixed
// HTTP 500 instead of `201 pending`. The route must present that as an ordinary
// error: no success text, no pending-Journal warning, one POST, no auto-retry.
// ---------------------------------------------------------------------------

const verificationFailure = () => {
  const error = new Error(
    'Не удалось проверить созданный документ отчета, поэтому он не считается надёжным. Данные мастерской не изменялись.',
  );
  error.status = 500;
  error.payload = {
    detail: {
      code: 'report_document_verification_failed',
      message: 'Не удалось проверить созданный документ отчета, поэтому он не считается надёжным. Данные мастерской не изменялись.',
      next_action: 'Повторите создание документа. Если ошибка повторяется, перезапустите приложение.',
    },
  };
  return error;
};

test('a verification failure is a definite error, not an ambiguous result', async () => {
  const { h, ui, runtime } = makeReportDocumentsRoute();
  runtime.enter();
  runtime.load('initial');
  h.reads[0].resolve({ status: statusResponse(0), list: { items: [], limit: 50, offset: 0, total: 0 } });
  await flush();

  runtime.create({ format: 'markdown' });
  assert.equal(h.postCount, 1);
  h.mutations[0].reject(verificationFailure());
  await flush();

  const presentation = runtime.presentation();
  // The existing error region, not the ambiguous-network warning.
  assert.equal(presentation.feedback.error, messages.mutationError);
  assert.equal(presentation.feedback.warning, '');
  assert.equal(presentation.feedback.success, '');
  // Never presented as a created document.
  assert.ok(!/Документ отчета создан/.test(presentation.feedback.success));
  assert.equal(ui.lastCreatedDocument, null);
  // No pending-Journal warning: this is not a verified artifact.
  assert.equal(visibleWarning(ui), '');
  assert.equal(ui.auditWarning, '');
  // One POST, no automatic retry, and no reconciliation lock.
  assert.equal(h.postCount, 1);
  assert.equal(runtime.lifecycle.state.reconciliationRequired, false);
});

test('a verification failure leaks no filename, path or verifier detail to the screen', async () => {
  const { h, ui, runtime } = makeReportDocumentsRoute();
  runtime.enter();
  runtime.create({ format: 'markdown' });
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
    'workshop-overview-20260731-101112',
    '/local/exports/report-documents',
    '.md',
    '.json',
    'operation_id',
    'sqlite',
    'size-mismatch',
  ]) {
    assert.ok(!shown.includes(forbidden), `leaked: ${forbidden}`);
  }
});

test('a later successful create still works after a verification failure', async () => {
  const { h, ui, runtime } = makeReportDocumentsRoute();
  runtime.enter();
  runtime.create({ format: 'markdown' });
  h.mutations[0].reject(verificationFailure());
  await flush();
  assert.equal(runtime.presentation().canCreate, true);

  runtime.create({ format: 'markdown' });
  assert.equal(h.postCount, 2);
  h.mutations[1].resolve(mutationResult(recordedResponse()));
  await flush();

  assert.match(runtime.presentation().feedback.success, /Документ отчета создан\./);
  assert.equal(visibleWarning(ui), '');
});
