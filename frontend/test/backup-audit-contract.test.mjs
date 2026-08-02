import test from 'node:test';
import assert from 'node:assert/strict';
import { createLocalArtifactRouteRuntime } from '../dist-tests/backup-audit-contract/local-artifacts-reports-runtime.js';
import { transitionLocalArtifactsReportsRouteOwnership } from '../dist-tests/backup-audit-contract/local-artifacts-reports-route.js';
import {
  BACKUP_PENDING_AUDIT_COUNT_WARNING,
  BACKUP_PENDING_AUDIT_MESSAGE,
  adoptBackupPendingAuditCount,
  backupAuditResult,
  backupAuditWarning,
  backupPendingAuditCount,
} from '../dist-tests/backup-audit-contract/backup-audit-contract.js';

/**
 * CR-009 B3 frontend contract.
 *
 * The behaviour under test is that one HTTP 201 carries two results — the backup
 * file (authoritative) and its Journal entry (secondary) — and that the two stay
 * visibly separate: a pending Journal entry must read as success plus a warning,
 * never as a failed backup, and must never cause a second POST.
 *
 * By the time this response exists the backup is already a verified,
 * transactionally consistent SQLite snapshot (ADR 0015), so a pending Journal
 * entry says nothing whatever about the safety of the copy the user just made.
 * The wording must not imply otherwise.
 */

const messages = { loading:'loading', refreshing:'refreshing', reconciling:'reconciling', initialError:'initial error', refreshError:'refresh warning', refreshSuccess:'refresh ok', mutationBusy:'busy', mutationSuccess:'created', mutationError:'create failed', mutationAmbiguous:'ambiguous network', invalidMutationResponse:'invalid created', mutationRefreshWarning:'created but refresh failed', reconciliationFailed:'still cannot confirm' };

const flush = () => new Promise((resolve) => setImmediate(resolve));
function deferred(){let resolve,reject;const promise=new Promise((res,rej)=>{resolve=res;reject=rej});return {promise,resolve,reject};}

const backupFile = (filename = '20260801T101112131415Z-cosmetic_workshop-before_import.sqlite') => ({ filename, path: `/local/backups/${filename}`, created_at: '2026-08-01T10:11:12Z', reason: 'before_import', size_bytes: 417792 });

const recordedResponse = (filename) => ({ backup: backupFile(filename), database_path: '/local/cosmetic_workshop.sqlite', backup_dir: '/local/backups', message: 'Резервная копия создана.', audit_status: 'recorded', audit_message: null });
const pendingResponse = (filename) => ({ backup: backupFile(filename), database_path: '/local/cosmetic_workshop.sqlite', backup_dir: '/local/backups', message: 'Резервная копия создана.', audit_status: 'pending', audit_message: BACKUP_PENDING_AUDIT_MESSAGE });

const statusResponse = (pending = 0) => ({ database_path: '/local/cosmetic_workshop.sqlite', database_exists: true, database_size_bytes: 40960, backup_dir: '/local/backups', backup_dir_exists: true, backup_count: 1, latest_backup: backupFile(), pending_audit_count: pending });

/**
 * A backups route wired exactly as `main.ts` wires it: the mutation result
 * carries the backup plus the classified audit outcome, and the UI state mirror
 * is rebuilt the same way on every render.
 */
function makeBackupsRoute() {
  const ui = { lastCreatedBackup: null, auditWarning: '', pendingAuditCount: null, reason: 'before_import' };
  const h = { active: true, renders: 0, polite: [], assertive: [], focus: [], reads: [], mutations: [], postCount: 0, readCount: 0, ui };
  const runtime = createLocalArtifactRouteRuntime({
    route: 'backups',
    mutationKind: 'create-backup',
    messages,
    read: () => { h.readCount++; const d = deferred(); h.reads.push(d); return d.promise; },
    mutate: () => { h.postCount++; const d = deferred(); h.mutations.push(d); return d.promise; },
    validateCreated: (c) => Boolean(c && c.auditValid && c.backup && c.backup.filename && c.backup.path),
    ownsRoute: () => h.active,
    applyRead: (snapshot) => { ui.backups = snapshot.list.backups; adoptBackupPendingAuditCount(ui, snapshot.status); },
    applyCreated: (result) => { ui.lastCreatedBackup = result.backup; ui.auditWarning = result.auditWarning; },
    render: () => { if (h.active) h.renders++; },
    announce: (message, kind) => h[kind === 'assertive' ? 'assertive' : 'polite'].push(message),
    focus: (key) => h.focus.push(key),
  });
  return { h, ui, runtime };
}

/** The `mutate` resolution `main.ts` builds from a create response. */
const mutationResult = (response) => {
  const audit = backupAuditResult(response);
  return { created: { backup: response.backup, auditValid: audit.valid, auditWarning: audit.warning }, message: `${response.message} Файл: ${response.backup.filename}` };
};

const visibleWarning = (ui) => backupAuditWarning(ui);

// ---------------------------------------------------------------------------
// Contract classification
// ---------------------------------------------------------------------------

test('a recorded response is valid only with an explicit null audit_message', () => {
  assert.deepEqual(backupAuditResult(recordedResponse()), { valid: true, status: 'recorded', warning: '' });
  // An absent field is an incomplete contract, not "recorded with no warning":
  // it cannot be told apart from a truncated or older-shaped body.
  assert.equal(backupAuditResult({ ...recordedResponse(), audit_message: undefined }).valid, false);
  const { audit_message: _omitted, ...withoutMessage } = recordedResponse();
  assert.equal(backupAuditResult(withoutMessage).valid, false);
});

test('a pending response is valid only with the exact accepted warning', () => {
  const result = backupAuditResult(pendingResponse());
  assert.equal(result.valid, true);
  assert.equal(result.status, 'pending');
  assert.equal(result.warning, BACKUP_PENDING_AUDIT_MESSAGE);
  assert.equal(result.warning, 'Резервная копия создана, но запись в журнал действий пока не добавлена. Приложение повторит попытку при следующем запуске или перед созданием следующей резервной копии.');
});

test('an incomplete or unrecognized audit contract is invalid, never a silent success', () => {
  const base = { backup: backupFile(), message: 'Резервная копия создана.' };
  for (const response of [
    base,
    { ...base, audit_status: 'pending' },
    { ...base, audit_status: 'pending', audit_message: null },
    { ...base, audit_status: 'pending', audit_message: 'какое-то другое предупреждение' },
    // Another artifact kind's accepted warning must never pass here.
    { ...base, audit_status: 'pending', audit_message: 'Экспорт создан, но запись в журнал действий пока не добавлена. Приложение повторит попытку при следующем запуске или перед созданием следующего экспорта.' },
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
    const result = backupAuditResult(response);
    assert.equal(result.valid, false, JSON.stringify(response));
    assert.equal(result.status, null);
    assert.equal(result.warning, '');
  }
});

test('a knowable pending count is an exact non-negative integer', () => {
  assert.equal(backupPendingAuditCount(statusResponse(3)), 3);
  assert.equal(backupPendingAuditCount(statusResponse(0)), 0);
  assert.equal(backupPendingAuditCount(statusResponse(1)), 1);
});

test('an unknowable pending count is null, never a fabricated zero', () => {
  // `null` and `0` are different answers: `0` is a claim that nothing is
  // pending, and the UI clears a standing warning on it. Anything we cannot
  // read must not be able to make that claim.
  const { pending_audit_count: _omitted, ...withoutField } = statusResponse(1);
  assert.equal(backupPendingAuditCount(withoutField), null);
  for (const value of [undefined, null, -1, -0.5, Number.NaN, Infinity, -Infinity, '2', '', {}, [], true, 0.5, 2.9]) {
    assert.equal(backupPendingAuditCount({ pending_audit_count: value }), null, String(value));
  }
  for (const status of [null, undefined, 'nope', 5]) {
    assert.equal(backupPendingAuditCount(status), null, String(status));
  }
});

test('one warning region: the created-backup warning outranks the standing count warning', () => {
  assert.equal(backupAuditWarning({ auditWarning: '', pendingAuditCount: 0 }), '');
  assert.equal(backupAuditWarning({ auditWarning: '', pendingAuditCount: 2 }), BACKUP_PENDING_AUDIT_COUNT_WARNING);
  assert.equal(backupAuditWarning({ auditWarning: BACKUP_PENDING_AUDIT_MESSAGE, pendingAuditCount: 1 }), BACKUP_PENDING_AUDIT_MESSAGE);
  // An unknown count shows nothing on its own, but never suppresses a warning
  // that a create already established.
  assert.equal(backupAuditWarning({ auditWarning: '', pendingAuditCount: null }), '');
  assert.equal(backupAuditWarning({ auditWarning: BACKUP_PENDING_AUDIT_MESSAGE, pendingAuditCount: null }), BACKUP_PENDING_AUDIT_MESSAGE);
});

test('adopting a malformed count preserves the last thing actually known', () => {
  for (const malformed of [{}, { pending_audit_count: undefined }, { pending_audit_count: '3' }, { pending_audit_count: -1 }, { pending_audit_count: 1.5 }, { pending_audit_count: Number.NaN }, { pending_audit_count: Infinity }, null, undefined]) {
    const state = { auditWarning: BACKUP_PENDING_AUDIT_MESSAGE, pendingAuditCount: 2 };
    adoptBackupPendingAuditCount(state, malformed);
    assert.equal(state.pendingAuditCount, 2, JSON.stringify(malformed));
    assert.equal(state.auditWarning, BACKUP_PENDING_AUDIT_MESSAGE);
    assert.equal(backupAuditWarning(state), BACKUP_PENDING_AUDIT_MESSAGE);
  }
});

test('adopting a validated zero is the only thing that clears the warning', () => {
  const cleared = { auditWarning: BACKUP_PENDING_AUDIT_MESSAGE, pendingAuditCount: 1 };
  adoptBackupPendingAuditCount(cleared, statusResponse(0));
  assert.equal(cleared.pendingAuditCount, 0);
  assert.equal(cleared.auditWarning, '');
  assert.equal(backupAuditWarning(cleared), '');

  const kept = { auditWarning: BACKUP_PENDING_AUDIT_MESSAGE, pendingAuditCount: 1 };
  adoptBackupPendingAuditCount(kept, statusResponse(3));
  assert.equal(kept.pendingAuditCount, 3);
  assert.equal(kept.auditWarning, BACKUP_PENDING_AUDIT_MESSAGE);
});

test('neither user-facing warning exposes a filename, path, identifier or database wording', () => {
  for (const warning of [BACKUP_PENDING_AUDIT_MESSAGE, BACKUP_PENDING_AUDIT_COUNT_WARNING]) {
    for (const forbidden of ['.sqlite', '.db', '.json', '/', '\\', 'SQLite', 'sqlite', 'WAL', 'quick_check', 'operation', 'ledger', 'AuditLog', 'audit_', 'UUID']) {
      assert.ok(!warning.includes(forbidden), `${forbidden} must not appear in: ${warning}`);
    }
    assert.match(warning, /[а-яё]/i);
    // It must not read as a failed backup, and must not cast doubt on the
    // snapshot itself — the copy is already verified when this is shown.
    assert.ok(!warning.includes('не создан'), warning);
    assert.ok(!warning.includes('повреж'), warning);
  }
});

// ---------------------------------------------------------------------------
// Recorded success
// ---------------------------------------------------------------------------

test('recorded success shows ordinary success, no warning, one POST and one refresh', async () => {
  const { h, ui, runtime } = makeBackupsRoute();
  runtime.enter();
  runtime.load('initial');
  h.reads[0].resolve({ status: statusResponse(0), list: { backups: [] } });
  await flush();

  runtime.create({ reason: 'before_import' });
  assert.equal(h.postCount, 1);
  h.mutations[0].resolve(mutationResult(recordedResponse()));
  await flush();

  const presentation = runtime.presentation();
  assert.match(presentation.feedback.success, /Резервная копия создана\./);
  assert.equal(presentation.feedback.error, '');
  assert.equal(presentation.feedback.warning, '');
  assert.equal(visibleWarning(ui), '');
  assert.equal(ui.lastCreatedBackup.reason, 'before_import');
  assert.equal(runtime.lifecycle.state.reconciliationRequired, false);
  // Exactly one refresh follows the create, and no second POST.
  assert.equal(h.readCount, 2);
  h.reads[1].resolve({ status: statusResponse(0), list: { backups: [backupFile()] } });
  await flush();
  assert.equal(h.postCount, 1);
  assert.equal(visibleWarning(ui), '');
  assert.equal(h.polite.filter((m) => /Резервная копия создана/.test(m)).length, 1);
  assert.deepEqual(h.focus, ['b3-backups-last-created']);
});

// ---------------------------------------------------------------------------
// Pending success
// ---------------------------------------------------------------------------

test('pending success is a success plus a separate warning, not a failure', async () => {
  const { h, ui, runtime } = makeBackupsRoute();
  runtime.enter();
  runtime.load('initial');
  h.reads[0].resolve({ status: statusResponse(0), list: { backups: [] } });
  await flush();

  runtime.create({ reason: 'before_import' });
  h.mutations[0].resolve(mutationResult(pendingResponse()));
  await flush();

  const presentation = runtime.presentation();
  // The backup result itself is an ordinary success.
  assert.match(presentation.feedback.success, /Резервная копия создана\./);
  assert.equal(presentation.feedback.error, '');
  assert.equal(runtime.lifecycle.state.reconciliationRequired, false);
  // The Journal warning lives in its own region and is not the generic
  // ambiguous-network warning.
  assert.equal(visibleWarning(ui), BACKUP_PENDING_AUDIT_MESSAGE);
  assert.notEqual(visibleWarning(ui), messages.mutationAmbiguous);
  assert.notEqual(visibleWarning(ui), messages.mutationError);
  // The created backup metadata is retained, including its canonical reason.
  assert.equal(ui.lastCreatedBackup.filename, '20260801T101112131415Z-cosmetic_workshop-before_import.sqlite');
  assert.equal(ui.lastCreatedBackup.reason, 'before_import');
  assert.equal(h.postCount, 1);
});

test('the pending warning survives the refresh that follows the create', async () => {
  const { h, ui, runtime } = makeBackupsRoute();
  runtime.enter();
  runtime.load('initial');
  h.reads[0].resolve({ status: statusResponse(0), list: { backups: [] } });
  await flush();
  runtime.create({ reason: 'before_import' });
  h.mutations[0].resolve(mutationResult(pendingResponse()));
  await flush();

  // The mutation refresh reports the operation as still pending.
  assert.equal(h.readCount, 2);
  h.reads[1].resolve({ status: statusResponse(1), list: { backups: [backupFile()] } });
  await flush();

  assert.equal(ui.pendingAuditCount, 1);
  assert.equal(visibleWarning(ui), BACKUP_PENDING_AUDIT_MESSAGE);
  assert.equal(h.postCount, 1);
  // An ordinary re-render derives the same warning from unchanged state.
  assert.equal(visibleWarning(ui), BACKUP_PENDING_AUDIT_MESSAGE);
});

test('the standing warning clears only when a later status read reports zero', async () => {
  const { h, ui, runtime } = makeBackupsRoute();
  runtime.enter();
  runtime.load('initial');
  h.reads[0].resolve({ status: statusResponse(2), list: { backups: [backupFile()] } });
  await flush();
  assert.equal(visibleWarning(ui), BACKUP_PENDING_AUDIT_COUNT_WARNING);

  // Still pending: the warning stays.
  runtime.load('refresh');
  h.reads[1].resolve({ status: statusResponse(1), list: { backups: [backupFile()] } });
  await flush();
  assert.equal(visibleWarning(ui), BACKUP_PENDING_AUDIT_COUNT_WARNING);

  // A failed refresh must not clear it either — nothing was confirmed.
  runtime.load('refresh');
  h.reads[2].reject(new Error('read failed'));
  await flush();
  assert.equal(visibleWarning(ui), BACKUP_PENDING_AUDIT_COUNT_WARNING);

  // A malformed count must not clear it either.
  runtime.load('refresh');
  h.reads[3].resolve({ status: { ...statusResponse(1), pending_audit_count: 'нет' }, list: { backups: [backupFile()] } });
  await flush();
  assert.equal(visibleWarning(ui), BACKUP_PENDING_AUDIT_COUNT_WARNING);

  // Only an authoritative zero clears it.
  runtime.load('refresh');
  h.reads[4].resolve({ status: statusResponse(0), list: { backups: [backupFile()] } });
  await flush();
  assert.equal(visibleWarning(ui), '');
  // A status read never triggers a create.
  assert.equal(h.postCount, 0);
});

test('a pending create followed by a zero count clears both warnings', async () => {
  const { h, ui, runtime } = makeBackupsRoute();
  runtime.enter();
  runtime.load('initial');
  h.reads[0].resolve({ status: statusResponse(0), list: { backups: [] } });
  await flush();
  runtime.create({ reason: 'before_import' });
  h.mutations[0].resolve(mutationResult(pendingResponse()));
  await flush();
  h.reads[1].resolve({ status: statusResponse(1), list: { backups: [backupFile()] } });
  await flush();
  assert.equal(visibleWarning(ui), BACKUP_PENDING_AUDIT_MESSAGE);

  // A later read after backend reconciliation reports nothing outstanding.
  runtime.load('refresh');
  h.reads[2].resolve({ status: statusResponse(0), list: { backups: [backupFile()] } });
  await flush();

  assert.equal(ui.auditWarning, '');
  assert.equal(ui.pendingAuditCount, 0);
  assert.equal(visibleWarning(ui), '');
});

// ---------------------------------------------------------------------------
// Invalid contract
// ---------------------------------------------------------------------------

test('an invalid audit contract sends no second POST and shows no false success', async () => {
  const { h, ui, runtime } = makeBackupsRoute();
  runtime.enter();
  runtime.load('initial');
  h.reads[0].resolve({ status: statusResponse(0), list: { backups: [] } });
  await flush();

  runtime.create({ reason: 'before_import' });
  h.mutations[0].resolve(mutationResult({ backup: backupFile(), message: 'Резервная копия создана.', audit_status: 'pending', audit_message: null }));
  await flush();

  // Routed into the existing reconciliation path, not into an ordinary success.
  assert.equal(runtime.lifecycle.state.reconciliationRequired, true);
  assert.equal(runtime.presentation().feedback.success, '');
  assert.equal(runtime.presentation().feedback.error, messages.invalidMutationResponse);
  assert.equal(runtime.presentation().canCreate, false);
  assert.equal(ui.lastCreatedBackup, null);
  assert.equal(visibleWarning(ui), '');

  // A further create attempt while locked issues no POST.
  runtime.create({ reason: 'before_import' });
  assert.equal(h.postCount, 1);
  runtime.reconcile();
  h.reads[1].resolve({ status: statusResponse(1), list: { backups: [backupFile()] } });
  await flush();
  assert.equal(runtime.lifecycle.state.reconciliationRequired, false);
  assert.equal(h.postCount, 1);
});

test('a genuinely ambiguous network failure still uses the existing ambiguous warning', async () => {
  const { h, ui, runtime } = makeBackupsRoute();
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
  const { h, ui, runtime } = makeBackupsRoute();
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
  assert.equal(ui.lastCreatedBackup, null);
  assert.equal(ui.auditWarning, '');
  assert.equal(runtime.lifecycle.state.reconciliationRequired, true);

  h.active = true;
  runtime.enter();
  runtime.reconcile();
  h.reads[0].resolve({ status: statusResponse(1), list: { backups: [backupFile()] } });
  await flush();
  assert.equal(runtime.lifecycle.state.reconciliationRequired, false);
  // The authoritative status still surfaces the pending Journal state.
  assert.equal(visibleWarning(ui), BACKUP_PENDING_AUDIT_COUNT_WARNING);
  assert.equal(h.postCount, 1);
});

test('navigating away and back preserves the pending obligation without a duplicate POST', async () => {
  const { h, ui, runtime } = makeBackupsRoute();
  runtime.enter();
  runtime.load('initial');
  h.reads[0].resolve({ status: statusResponse(1), list: { backups: [backupFile()] } });
  await flush();
  assert.equal(visibleWarning(ui), BACKUP_PENDING_AUDIT_COUNT_WARNING);

  transitionLocalArtifactsReportsRouteOwnership({ backups: runtime }, 'backups', null);
  runtime.lifecycle.clearTransientFeedback();
  transitionLocalArtifactsReportsRouteOwnership({ backups: runtime }, null, 'backups');

  // The count is state, not transient feedback, so it survives navigation.
  assert.equal(visibleWarning(ui), BACKUP_PENDING_AUDIT_COUNT_WARNING);
  assert.equal(h.postCount, 0);
});

test('pending success announces politely once and focuses the created-backup target', async () => {
  const { h, runtime } = makeBackupsRoute();
  runtime.enter();
  runtime.create({ reason: 'before_import' });
  h.mutations[0].resolve(mutationResult(pendingResponse()));
  await flush();

  assert.equal(h.polite.length, 1);
  assert.match(h.polite[0], /Резервная копия создана\./);
  assert.deepEqual(h.assertive, []);
  assert.deepEqual(h.focus, ['b3-backups-last-created']);
});

// ---------------------------------------------------------------------------
// Production wiring and blast radius
// ---------------------------------------------------------------------------

const mainSource = async () => {
  const fs = await import('node:fs/promises');
  return fs.readFile(new URL('../src/main.ts', import.meta.url), 'utf8');
};

test('main.ts classifies the backup audit contract through the shared module, not inline', async () => {
  const source = await mainSource();
  assert.match(source, /import \{ adoptBackupPendingAuditCount, backupAuditResult, backupAuditWarning, backupPendingAuditCount \} from '\.\/backup-audit-contract\.js';/);
  assert.match(source, /backupAuditResult\(response\)/);
  assert.match(source, /backupPendingAuditNotice\(\)/);
  // The accepted Russian strings are owned by the contract module alone.
  assert.doesNotMatch(source, /Резервная копия создана, но запись в журнал действий/);
  assert.doesNotMatch(source, /Некоторые созданные резервные копии ещё не добавлены/);
  // No re-POST or bespoke retry was introduced for a pending audit.
  assert.doesNotMatch(source, /audit_status === 'pending'[^\n]*createBackup/);
  assert.doesNotMatch(source, /setTimeout\([^\n]*createBackup/);
});

test('the pending notice is rendered as its own warning region, apart from the success message', async () => {
  const source = await mainSource();
  const notice = source.split('\n').find((line) => line.includes('function backupPendingAuditNotice()'));
  assert.ok(notice, 'backupPendingAuditNotice must exist');
  assert.ok(notice.includes('backupAuditWarning(backupUiState)'), 'its text must come from the shared module');
  assert.ok(notice.includes("feedbackMessage('warning', warning)"), 'it must render as a warning region');
  assert.doesNotMatch(source, /feedbackMessage\('error', warning\)/);
});

test('each artifact route reads only its own audit contract', async () => {
  const source = await mainSource();
  const line = (needle) => source.split('\n').find((row) => row.includes(needle));

  const backupRuntime = line('const backupRuntime = createLocalArtifactRouteRuntime');
  assert.ok(backupRuntime);
  assert.ok(backupRuntime.includes('backupAuditResult('));
  assert.ok(backupRuntime.includes('adoptBackupPendingAuditCount('));
  // A shared "artifact" abstraction would make it possible to show an export's
  // warning on the backups page. The three contracts stay separate.
  assert.doesNotMatch(backupRuntime, /exportAudit|reportDocumentAudit/);

  const exportRuntime = line('const exportRuntime = createLocalArtifactRouteRuntime');
  assert.ok(exportRuntime);
  assert.doesNotMatch(exportRuntime, /backupAudit/);
});

test('the create response reason is rendered as received and never reconstructed', async () => {
  const source = await mainSource();
  // CR-005: the backend owns the canonical slug; the frontend only maps known
  // slugs to labels and otherwise renders them verbatim.
  assert.match(source, /function backupReasonLabelRaw/);
  assert.doesNotMatch(source, /normalizeBackupReason|sanitizeBackupReason/);
});

test('the backups page keeps its focus targets and stays keyboard operable', async () => {
  const source = await mainSource();
  for (const key of ['b3-backups-retry', 'b3-backups-refresh', 'b3-backups-create', 'b3-backups-last-created', 'b3-backups-content']) {
    assert.match(source, new RegExp(`data-focus-key="${key}"`));
  }
  // The pending notice is inserted into the page grid before the cards, and
  // introduces no new interactive control that would need its own binding.
  assert.match(source, /\$\{backupPendingAuditNotice\(\)\}/);
});

test('desktop and narrow viewports share one warning region with no fixed width', async () => {
  const fs = await import('node:fs/promises');
  const styles = await fs.readFile(new URL('../src/styles.css', import.meta.url), 'utf8');
  const source = await mainSource();
  // The notice reuses the existing feedback component rather than introducing a
  // new element that would need its own responsive rules.
  const notice = source.split('\n').find((line) => line.includes('function backupPendingAuditNotice()'));
  assert.ok(notice.includes('feedbackMessage('));
  assert.match(styles, /\.feedback/);
  assert.doesNotMatch(notice, /style="width:\s*\d+px/);
});
