import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { checkTaxRateInput, formatTaxRateEffectiveAt, isTaxRateSettingDto, taxRateInputValue, taxRatePercentLabel } from '../dist-tests/settings-tax-feedback/settings-tax-contract.js';
import { SettingsTaxRateFeedbackLifecycle, TAX_RATE_CANCEL_MESSAGE, TAX_RATE_CLEAR_ERROR, TAX_RATE_INITIAL_ERROR, TAX_RATE_INVALID_RESPONSE, TAX_RATE_REFRESH_WARNING, TAX_RATE_SAVE_ERROR } from '../dist-tests/settings-tax-feedback/settings-tax-feedback.js';
import { TAX_RATE_HELPER_TEXT, TAX_RATE_MISSING_TEXT, TAX_RATE_SECTION_TITLE, settingsTaxRateCardMarkup, settingsTaxRatePresentation } from '../dist-tests/settings-tax-feedback/settings-tax-presentation.js';
import { bindSettingsTaxRateControls } from '../dist-tests/settings-tax-feedback/settings-tax-bindings.js';
import { SettingsTaxRateRuntime } from '../dist-tests/settings-tax-feedback/settings-tax-runtime.js';
import { isWorkshopProfileDirty, isWorkshopProfileFormAvailable, workshopProfileCardMarkup } from '../dist-tests/settings-tax-feedback/settings-profile-presentation.js';

const configured = (percent = '6.00', effective = '2026-07-27T10:28:54Z', message = 'Налоговая ставка для расчётов настроена.') => ({ tax_rate_percent: percent, is_configured: true, effective_at: effective, message });
const unconfigured = (message = 'Налоговая ставка для расчётов пока не настроена.') => ({ tax_rate_percent: null, is_configured: false, effective_at: null, message });
const flush = () => new Promise((resolve) => setImmediate(resolve));

function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((res, rej) => { resolve = res; reject = rej; });
  return { promise, resolve, reject };
}

function harness() {
  const h = { active: true, renders: 0, polite: [], assertive: [], reads: [], saves: [], payloads: [] };
  const runtime = new SettingsTaxRateRuntime({
    read: () => { const d = deferred(); h.reads.push(d); return d.promise; },
    save: (payload) => { h.payloads.push(payload); const d = deferred(); h.saves.push(d); return d.promise; },
    ownsRoute: () => h.active,
    render: () => { if (h.active) h.renders += 1; },
    announce: (message, kind) => h[kind === 'assertive' ? 'assertive' : 'polite'].push(message),
    fieldErrorFromFailure: (error) => error?.fieldError ?? '',
  });
  runtime.enter();
  return { h, runtime };
}

async function loaded(dto = configured()) {
  const { h, runtime } = harness();
  runtime.load('initial');
  h.reads[0].resolve(dto);
  await flush();
  return { h, runtime };
}

test('input normalization accepts the contract forms and sends a canonical decimal string', () => {
  assert.deepEqual(checkTaxRateInput('6'), { ok: true, payload: '6.00' });
  assert.deepEqual(checkTaxRateInput('6,5'), { ok: true, payload: '6.50' });
  assert.deepEqual(checkTaxRateInput('6.5'), { ok: true, payload: '6.50' });
  assert.deepEqual(checkTaxRateInput(' 0 '), { ok: true, payload: '0.00' });
  assert.deepEqual(checkTaxRateInput('100'), { ok: true, payload: '100.00' });
  assert.deepEqual(checkTaxRateInput('6.00'), { ok: true, payload: '6.00' });
});

test('invalid input is classified and never silently corrected', () => {
  assert.equal(checkTaxRateInput('6.005').code, 'precision');
  assert.equal(checkTaxRateInput('6,005').code, 'precision');
  assert.equal(checkTaxRateInput('').code, 'empty');
  assert.equal(checkTaxRateInput('   ').code, 'empty');
  assert.equal(checkTaxRateInput('-1').code, 'format');
  assert.equal(checkTaxRateInput('6e1').code, 'format');
  assert.equal(checkTaxRateInput('шесть').code, 'format');
  assert.equal(checkTaxRateInput('101').code, 'range');
  assert.equal(checkTaxRateInput('100.01').code, 'range');
  for (const raw of ['6.005', '', '-1', '101']) assert.equal(checkTaxRateInput(raw).payload, undefined);
});

test('response guard rejects shapes that disagree with the configured flag', () => {
  assert.equal(isTaxRateSettingDto(configured()), true);
  assert.equal(isTaxRateSettingDto(unconfigured()), true);
  assert.equal(isTaxRateSettingDto({ ...configured(), tax_rate_percent: 6 }), false);
  assert.equal(isTaxRateSettingDto({ ...configured(), effective_at: null }), false);
  assert.equal(isTaxRateSettingDto({ ...unconfigured(), tax_rate_percent: '0.00' }), false);
  assert.equal(isTaxRateSettingDto(null), false);
});

test('unknown or missing backend value is never coerced to zero', () => {
  assert.equal(taxRateInputValue(null), '');
  assert.equal(taxRateInputValue(unconfigured()), '');
  assert.equal(taxRatePercentLabel(null), null);
  assert.equal(taxRatePercentLabel(unconfigured()), null);
  assert.equal(taxRatePercentLabel(configured('0.00')), '0.00%');
});

test('effective time is formatted for humans and not shown when unconfigured', () => {
  assert.equal(formatTaxRateEffectiveAt('2026-07-27T10:28:54Z'), '27 июля 2026, 10:28 UTC');
  assert.equal(formatTaxRateEffectiveAt(null), '');
  const view = settingsTaxRatePresentation({ ...new SettingsTaxRateFeedbackLifecycle().state, status: 'ready', confirmed: unconfigured() });
  assert.equal(view.effectiveAtText, '');
});

test('unconfigured presentation explains the missing state without inventing a value', async () => {
  const { runtime } = await loaded(unconfigured());
  const view = runtime.presentation();
  assert.equal(view.status, 'unconfigured');
  assert.equal(view.valueLabel, null);
  assert.equal(view.stateText, TAX_RATE_MISSING_TEXT);
  assert.equal(view.draft, '');
  assert.equal(view.canClear, false);
  assert.equal(view.canSave, true);
});

test('configured presentation shows the canonical value and effective time', async () => {
  const { runtime } = await loaded(configured('6.00'));
  const view = runtime.presentation();
  assert.equal(view.status, 'configured');
  assert.equal(view.valueLabel, '6.00%');
  assert.equal(view.effectiveAtText, '27 июля 2026, 10:28 UTC');
  assert.equal(view.draft, '6.00');
  assert.equal(view.canClear, true);
});

test('configured zero is presented as configured, not as missing', async () => {
  const { runtime } = await loaded(configured('0.00'));
  const view = runtime.presentation();
  assert.equal(view.status, 'configured');
  assert.equal(view.valueLabel, '0.00%');
  assert.notEqual(view.stateText, TAX_RATE_MISSING_TEXT);
  assert.equal(view.canClear, true);
});

test('save sends the normalized decimal string and shows the backend message on success', async () => {
  const { h, runtime } = await loaded(unconfigured());
  runtime.updateDraft('6,5');
  runtime.submit();
  assert.deepEqual(h.payloads, [{ tax_rate_percent: '6.50' }]);
  assert.equal(runtime.presentation().mutationBusy, true);
  assert.equal(runtime.presentation().controlsDisabled, true);
  h.saves[0].resolve(configured('6.50', '2026-07-27T11:00:00Z', 'Налоговая ставка для расчётов сохранена.'));
  await flush();
  const view = runtime.presentation();
  assert.equal(view.valueLabel, '6.50%');
  assert.deepEqual(view.feedbackItems, [{ tone: 'success', message: 'Налоговая ставка для расчётов сохранена.' }]);
  assert.equal(h.polite.at(-1), 'Налоговая ставка для расчётов сохранена.');
  assert.equal(view.mutationBusy, false);
});

test('a no-op save is reported with the honest backend message', async () => {
  const { h, runtime } = await loaded(configured('6.00'));
  runtime.updateDraft('6');
  runtime.submit();
  h.saves[0].resolve(configured('6.00', '2026-07-27T10:28:54Z', 'Налоговая ставка уже сохранена без изменений.'));
  await flush();
  const view = runtime.presentation();
  assert.deepEqual(view.feedbackItems, [{ tone: 'success', message: 'Налоговая ставка уже сохранена без изменений.' }]);
  assert.equal(view.effectiveAtText, '27 июля 2026, 10:28 UTC');
});

test('invalid precision keeps the typed value, shows a field error and sends no request', async () => {
  const { h, runtime } = await loaded(configured('6.00'));
  runtime.updateDraft('6.005');
  const started = runtime.submit();
  assert.equal(started.accepted, false);
  assert.equal(started.reason, 'invalid-input');
  assert.equal(h.saves.length, 0);
  const view = runtime.presentation();
  assert.equal(view.draft, '6.005');
  assert.match(view.fieldError, /двух знаков/);
  assert.equal(view.valueLabel, '6.00%');
  assert.equal(h.assertive.at(-1), view.fieldError);
});

test('mutation failure keeps the previous confirmed value and reports a save error', async () => {
  const { h, runtime } = await loaded(configured('6.00'));
  runtime.updateDraft('7');
  runtime.submit();
  h.saves[0].reject(new Error('network'));
  await flush();
  const view = runtime.presentation();
  assert.equal(view.valueLabel, '6.00%');
  assert.deepEqual(view.feedbackItems, [{ tone: 'error', message: TAX_RATE_SAVE_ERROR }]);
  assert.equal(h.assertive.at(-1), TAX_RATE_SAVE_ERROR);
});

test('a backend field error is attached to the input on mutation failure', async () => {
  const { h, runtime } = await loaded(configured('6.00'));
  runtime.updateDraft('7');
  runtime.submit();
  h.saves[0].reject({ fieldError: 'Ставка должна быть от 0 до 100 процентов.' });
  await flush();
  assert.equal(runtime.presentation().fieldError, 'Ставка должна быть от 0 до 100 процентов.');
});

test('initial read failure shows an initial error without a fabricated value', async () => {
  const { h, runtime } = harness();
  runtime.load('initial');
  h.reads[0].reject(new Error('offline'));
  await flush();
  const view = runtime.presentation();
  assert.equal(view.status, 'unavailable');
  assert.equal(view.valueLabel, null);
  assert.deepEqual(view.feedbackItems, [{ tone: 'error', message: TAX_RATE_INITIAL_ERROR }]);
  assert.equal(view.canSave, false);
  assert.equal(h.assertive.at(-1), TAX_RATE_INITIAL_ERROR);
});

test('refresh failure keeps the confirmed value and stays a warning, not an error', async () => {
  const { h, runtime } = await loaded(configured('6.00'));
  runtime.refresh();
  h.reads[1].reject(new Error('offline'));
  await flush();
  const view = runtime.presentation();
  assert.equal(view.valueLabel, '6.00%');
  assert.deepEqual(view.feedbackItems, [{ tone: 'warning', message: TAX_RATE_REFRESH_WARNING }]);
});

test('successful mutation plus failing refresh stays a known success with a warning', async () => {
  const { h, runtime } = await loaded(unconfigured());
  runtime.updateDraft('6');
  runtime.submit();
  h.saves[0].resolve(configured('6.00', '2026-07-27T11:00:00Z', 'Налоговая ставка для расчётов сохранена.'));
  await flush();
  assert.equal(h.reads.length, 2);
  h.reads[1].reject(new Error('offline'));
  await flush();
  const view = runtime.presentation();
  assert.equal(view.valueLabel, '6.00%');
  assert.deepEqual(view.feedbackItems, [
    { tone: 'success', message: 'Налоговая ставка для расчётов сохранена.' },
    { tone: 'warning', message: TAX_RATE_REFRESH_WARNING },
  ]);
  assert.equal(view.feedbackItems.some((item) => item.tone === 'error'), false);
});

test('successful mutation plus successful refresh keeps the success message once', async () => {
  const { h, runtime } = await loaded(unconfigured());
  runtime.updateDraft('6');
  runtime.submit();
  h.saves[0].resolve(configured('6.00', '2026-07-27T11:00:00Z', 'Налоговая ставка для расчётов сохранена.'));
  await flush();
  h.reads[1].resolve(configured('6.00', '2026-07-27T11:00:00Z'));
  await flush();
  assert.deepEqual(runtime.presentation().feedbackItems, [{ tone: 'success', message: 'Налоговая ставка для расчётов сохранена.' }]);
});

test('cancel restores the last confirmed value and sends no request', async () => {
  const { h, runtime } = await loaded(configured('6.00'));
  runtime.updateDraft('42');
  runtime.cancelEdit();
  const view = runtime.presentation();
  assert.equal(view.draft, '6.00');
  assert.equal(view.fieldError, '');
  assert.equal(h.saves.length, 0);
  assert.equal(h.reads.length, 1);
  assert.deepEqual(view.feedbackItems, [{ tone: 'neutral', message: TAX_RATE_CANCEL_MESSAGE }]);
});

test('clear requires explicit confirmation before any request', async () => {
  const { h, runtime } = await loaded(configured('6.00'));
  const blocked = runtime.confirmClear();
  assert.equal(blocked.accepted, false);
  assert.equal(blocked.reason, 'not-confirmed');
  assert.equal(h.saves.length, 0);
  runtime.requestClear();
  assert.equal(runtime.presentation().clearConfirmVisible, true);
  runtime.confirmClear();
  assert.deepEqual(h.payloads, [{ tax_rate_percent: null }]);
});

test('clear confirmation can be cancelled without a request', async () => {
  const { h, runtime } = await loaded(configured('6.00'));
  runtime.requestClear();
  runtime.cancelClear();
  assert.equal(runtime.presentation().clearConfirmVisible, false);
  assert.equal(h.saves.length, 0);
  assert.equal(runtime.presentation().valueLabel, '6.00%');
});

test('clear cannot be requested when nothing is configured', async () => {
  const { runtime } = await loaded(unconfigured());
  const rejected = runtime.requestClear();
  assert.equal(rejected.accepted, false);
  assert.equal(rejected.reason, 'nothing-to-clear');
  assert.equal(runtime.presentation().clearConfirmVisible, false);
});

test('clear pending scopes the section and success returns the unconfigured state', async () => {
  const { h, runtime } = await loaded(configured('6.00'));
  runtime.requestClear();
  runtime.confirmClear();
  assert.equal(runtime.presentation().mutationBusy, true);
  h.saves[0].resolve(unconfigured('Налоговая ставка для расчётов очищена.'));
  await flush();
  const view = runtime.presentation();
  assert.equal(view.status, 'unconfigured');
  assert.equal(view.valueLabel, null);
  assert.equal(view.effectiveAtText, '');
  assert.equal(view.clearConfirmVisible, false);
  assert.deepEqual(view.feedbackItems, [{ tone: 'success', message: 'Налоговая ставка для расчётов очищена.' }]);
});

test('clear failure preserves the configured value and reports a clear error', async () => {
  const { h, runtime } = await loaded(configured('6.00'));
  runtime.requestClear();
  runtime.confirmClear();
  h.saves[0].reject(new Error('offline'));
  await flush();
  const view = runtime.presentation();
  assert.equal(view.valueLabel, '6.00%');
  assert.deepEqual(view.feedbackItems, [{ tone: 'error', message: TAX_RATE_CLEAR_ERROR }]);
});

test('duplicate save and duplicate clear are blocked while a mutation is pending', async () => {
  const { h, runtime } = await loaded(configured('6.00'));
  runtime.updateDraft('7');
  runtime.submit();
  const duplicateSave = runtime.submit();
  assert.equal(duplicateSave.accepted, false);
  assert.equal(duplicateSave.reason, 'mutation-active');
  assert.equal(runtime.requestClear().accepted, false);
  assert.equal(runtime.confirmClear().accepted, false);
  assert.equal(h.saves.length, 1);
  h.saves[0].resolve(configured('7.00', '2026-07-27T12:00:00Z', 'Налоговая ставка для расчётов изменена.'));
  await flush();
  assert.equal(h.saves.length, 1);
});

test('a stale mutation callback after route exit never presents or applies', async () => {
  const { h, runtime } = await loaded(configured('6.00'));
  runtime.updateDraft('7');
  runtime.submit();
  runtime.leave();
  h.active = false;
  const rendersBefore = h.renders;
  h.saves[0].resolve(configured('7.00', '2026-07-27T12:00:00Z', 'Изменена.'));
  await flush();
  assert.equal(h.renders, rendersBefore);
  assert.deepEqual(h.polite, []);
  assert.deepEqual(h.assertive, []);
  assert.equal(runtime.lifecycle.state.confirmed.tax_rate_percent, '6.00');
});

test('a stale read callback after route exit never presents', async () => {
  const { h, runtime } = await loaded(configured('6.00'));
  runtime.refresh();
  runtime.leave();
  h.active = false;
  const rendersBefore = h.renders;
  h.reads[1].resolve(configured('9.00', '2026-07-27T13:00:00Z'));
  await flush();
  assert.equal(h.renders, rendersBefore);
  assert.equal(runtime.lifecycle.state.confirmed.tax_rate_percent, '6.00');
});

test('an invalid mutation response is surfaced instead of being applied', async () => {
  const { h, runtime } = await loaded(configured('6.00'));
  runtime.updateDraft('7');
  runtime.submit();
  h.saves[0].resolve({ tax_rate_percent: 7, is_configured: true, effective_at: null, message: 'ok' });
  await flush();
  const view = runtime.presentation();
  assert.equal(view.valueLabel, '6.00%');
  assert.deepEqual(view.feedbackItems, [{ tone: 'error', message: TAX_RATE_INVALID_RESPONSE }]);
  assert.equal(h.reads.length, 1);
});

test('the section renders every stable smoke selector', async () => {
  const { runtime } = await loaded(configured('6.00'));
  runtime.requestClear();
  const markup = settingsTaxRateCardMarkup(runtime.presentation(), (tone, message) => `<p data-feedback-tone="${tone}">${message}</p>`);
  for (const selector of [
    'data-tax-rate-section',
    'data-tax-rate-status="configured"',
    'data-tax-rate-value',
    'data-tax-rate-effective-at',
    'data-tax-rate-input',
    'data-tax-rate-save',
    'data-tax-rate-cancel',
    'data-tax-rate-clear',
    'data-tax-rate-clear-confirm',
    'data-tax-rate-clear-accept',
    'data-tax-rate-clear-cancel',
    'data-tax-rate-refresh',
    'data-tax-rate-feedback',
    'data-tax-rate-field-error',
    'data-form="settings-tax-rate"',
  ]) assert.ok(markup.includes(selector), `missing ${selector}`);
  assert.ok(markup.includes(TAX_RATE_SECTION_TITLE));
  assert.ok(markup.includes(TAX_RATE_HELPER_TEXT));
  assert.ok(markup.includes('>%<'));
  assert.ok(markup.includes('aria-describedby="settings-tax-rate-hint settings-tax-rate-error"'));
});

test('the section markup never leaks API names, keys, JSON or tax-law promises', async () => {
  const { h, runtime } = await loaded(configured('6.00'));
  runtime.refresh();
  h.reads[1].reject(new Error('offline'));
  await flush();
  const markup = settingsTaxRateCardMarkup(runtime.presentation(), (tone, message) => `<p data-feedback-tone="${tone}">${message}</p>`);
  for (const forbidden of ['/api/', 'default_tax_rate', 'tax.default_rate', 'app_setting', 'tax_rate_setting_changed', 'AuditLog', 'УСН', 'НДС', 'деклараци']) {
    assert.equal(markup.includes(forbidden), false, `leaked ${forbidden}`);
  }
});

test('invalid input marks the field and links the error to the input', async () => {
  const { runtime } = await loaded(configured('6.00'));
  runtime.updateDraft('6.005');
  runtime.submit();
  const markup = settingsTaxRateCardMarkup(runtime.presentation(), (tone, message) => `<p data-feedback-tone="${tone}">${message}</p>`);
  assert.ok(markup.includes('aria-invalid="true"'));
  assert.ok(markup.includes('value="6.005"'));
  assert.ok(/data-tax-rate-field-error>[^<]*двух знаков/.test(markup));
});

test('pending state is scoped to the tax section controls only', async () => {
  const { h, runtime } = await loaded(configured('6.00'));
  runtime.updateDraft('7');
  runtime.submit();
  const markup = settingsTaxRateCardMarkup(runtime.presentation(), (tone, message) => `<p data-feedback-tone="${tone}">${message}</p>`);
  assert.ok(markup.includes('aria-busy="true"'));
  assert.equal(markup.includes('data-workshop-profile'), false);
  const profileState = { status: 'ready', actionStatus: 'idle', profile: { workshop_name: 'Мастерская', master_name: '', workshop_contact_text: '', workshop_note: '' }, draft: { workshop_name: 'Мастерская 2', master_name: '', workshop_contact_text: '', workshop_note: '' }, error: '', message: '' };
  const profileMarkup = workshopProfileCardMarkup(profileState, { renderFeedback: (tone, message) => `<p data-feedback-tone="${tone}">${message}</p>`, actionsMarkup: '<button type="button">Открыть документы отчётов</button>' });
  assert.equal(profileMarkup.includes('data-tax-rate'), false);
  assert.ok(profileMarkup.includes('data-workshop-profile-save'));
  assert.equal(/data-workshop-profile-save\s+disabled/.test(profileMarkup), false);
  void h;
});

test('workshop-profile rendering contract is unaffected by the extraction', () => {
  const profile = { workshop_name: 'Мастерская', master_name: 'Мария', workshop_contact_text: 'Телефон', workshop_note: 'Уход' };
  const ready = { status: 'ready', actionStatus: 'idle', profile, draft: { ...profile }, error: '', message: '' };
  assert.equal(isWorkshopProfileFormAvailable(ready), true);
  assert.equal(isWorkshopProfileDirty(ready), false);
  const dirty = { ...ready, draft: { ...profile, workshop_name: 'Другая' } };
  assert.equal(isWorkshopProfileDirty(dirty), true);
  assert.equal(isWorkshopProfileFormAvailable({ ...ready, actionStatus: 'saving' }), false);
  assert.equal(isWorkshopProfileFormAvailable({ ...ready, status: 'loading' }), false);
  assert.equal(isWorkshopProfileDirty({ ...ready, profile: null }), false);
  const helpers = { renderFeedback: (tone, message) => `<p data-feedback-tone="${tone}">${message}</p>`, actionsMarkup: '<button type="button">Открыть документы отчётов</button>' };
  const markup = workshopProfileCardMarkup(dirty, helpers);
  assert.ok(markup.includes('data-form="workshop-profile"'));
  assert.ok(markup.includes('data-workshop-profile-field="workshop_name"'));
  assert.ok(markup.includes('data-workshop-profile-field="master_name"'));
  assert.ok(markup.includes('data-workshop-profile-field="workshop_contact_text"'));
  assert.ok(markup.includes('data-workshop-profile-field="workshop_note"'));
  assert.ok(markup.includes('data-workshop-profile-dirty-notice '));
  assert.ok(markup.includes('data-action="cancel-workshop-profile"'));
  assert.ok(markup.includes('Сохранить профиль'));
  assert.ok(markup.includes('maxlength="120"'));
  assert.ok(workshopProfileCardMarkup({ ...ready, status: 'error', profile: null }, helpers).includes('data-action="reload-workshop-profile"'));
  assert.ok(workshopProfileCardMarkup({ ...ready, status: 'loading' }, helpers).includes('Загружаем профиль мастерской…'));
  assert.ok(workshopProfileCardMarkup({ ...ready, message: 'Сохранено' }, helpers).includes('data-workshop-profile-result'));
  assert.ok(workshopProfileCardMarkup({ ...ready, actionStatus: 'saving' }, helpers).includes('aria-busy="true"'));
});

test('the frontend performs no tax or margin arithmetic', () => {
  const sources = ['settings-tax-contract.js', 'settings-tax-feedback.js', 'settings-tax-presentation.js', 'settings-tax-runtime.js', 'settings-tax-bindings.js'];
  for (const name of sources) {
    const source = readFileSync(new URL(`../dist-tests/settings-tax-feedback/${name}`, import.meta.url), 'utf8');
    assert.equal(/\/\s*100/.test(source), false, `${name} divides by 100`);
    assert.equal(/sale_price|margin|tax_amount/.test(source), false, `${name} references calculation inputs`);
  }
});

class Control {
  constructor(attrs) {
    this.attrs = attrs;
    this.listeners = [];
  }

  addEventListener(type, cb) { this.listeners.push({ type, cb }); }
}

class StrictRoot {
  constructor(controls) { this.controls = controls; }

  matches(control, selector) {
    const withValue = [...selector.matchAll(/\[([^=\]]+)="([^"]+)"\]/g)].map(([, key, value]) => [key, value]);
    const bare = [...selector.matchAll(/\[([a-z-]+)\]/g)].map(([, key]) => key);
    if (withValue.length) return withValue.every(([key, value]) => control.attrs[key] === value);
    return bare.length > 0 && bare.every((key) => key in control.attrs);
  }

  querySelectorAll(selector) { return this.controls.filter((control) => this.matches(control, selector)); }
}

test('bindings attach exactly once to each stable tax control and ignore others', () => {
  const controls = [
    new Control({ 'data-form': 'settings-tax-rate' }),
    new Control({ 'data-tax-rate-input': '' }),
    new Control({ 'data-tax-rate-cancel': '' }),
    new Control({ 'data-tax-rate-clear': '' }),
    new Control({ 'data-tax-rate-clear-accept': '' }),
    new Control({ 'data-tax-rate-clear-cancel': '' }),
    new Control({ 'data-tax-rate-refresh': '' }),
    new Control({ 'data-form': 'workshop-profile' }),
    new Control({ 'data-workshop-profile-save': '' }),
  ];
  const calls = [];
  const counts = bindSettingsTaxRateControls(new StrictRoot(controls), {
    submitTaxRate: () => calls.push('submit'),
    updateTaxRateDraft: () => calls.push('draft'),
    cancelTaxRateEdit: () => calls.push('cancel'),
    requestTaxRateClear: () => calls.push('clear'),
    confirmTaxRateClear: () => calls.push('clear-accept'),
    cancelTaxRateClear: () => calls.push('clear-cancel'),
    refreshTaxRate: () => calls.push('refresh'),
  });
  assert.deepEqual(counts, { form: 1, input: 1, cancel: 1, clear: 1, clearAccept: 1, clearCancel: 1, refresh: 1 });
  assert.equal(controls.at(-1).listeners.length, 0);
  assert.equal(controls.at(-2).listeners.length, 0);
  for (const control of controls) assert.equal(new Set(control.listeners.map((l) => l.type)).size, control.listeners.length);
  for (const control of controls.slice(0, 7)) control.listeners.forEach(({ cb }) => cb({ preventDefault() {}, currentTarget: { value: '6' } }));
  assert.deepEqual(calls, ['submit', 'draft', 'cancel', 'clear', 'clear-accept', 'clear-cancel', 'refresh']);
});
