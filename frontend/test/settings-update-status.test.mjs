import test from 'node:test';
import assert from 'node:assert/strict';
import { isUpdateStatusDto, mountSettingsUpdateStatus, resetUpdateStatusCacheForTests, settingsUpdateStatusCardMarkup, updateStatusFromSettingsEnvelope } from '../dist-tests/settings-update-status/settings-update-status.js';
import { readFileSync } from 'node:fs';

const flush = () => new Promise((resolve) => setImmediate(resolve));

test('completed update is presented as a compact human-facing status', () => {
  const html = settingsUpdateStatusCardMarkup({ state: 'completed', to_app_version: '0.1.0', updated_at: '2026-08-13T20:00:00Z', message: 'Данные успешно подготовлены для этой версии приложения.', next_action: 'Можно продолжать работу.' });
  assert.match(html, /Обновление завершено/);
  assert.match(html, /Версия:<\/strong> 0.1.0/);
  assert.match(html, /Можно продолжать работу/);
});

test('attention state stays actionable and does not invent technical details', () => {
  const html = settingsUpdateStatusCardMarkup({ state: 'attention_required', to_app_version: null, updated_at: null, message: 'Состояние предыдущего обновления нельзя подтвердить автоматически.', next_action: 'Закройте приложение и откройте его снова.' });
  assert.match(html, /Нужно внимание/);
  for (const forbidden of ['operation_id', 'failure_category', 'schema_identity', 'stage_identity', 'backup_identity', 'traceback']) assert.doesNotMatch(html, new RegExp(forbidden));
});

test('backend-provided text is escaped and no update control is rendered', () => {
  const html = settingsUpdateStatusCardMarkup({ state: 'attention_required', to_app_version: '<script>', updated_at: null, message: '<img src=x onerror=alert(1)>', next_action: '<b>retry</b>' });
  assert.doesNotMatch(html, /<script>|<img|<b>/);
  assert.match(html, /&lt;script&gt;/);
  assert.doesNotMatch(html, /<button|data-action=.*update|проверить обновления/i);
});

test('DTO guard accepts only the bounded public contract', () => {
  const status = { state: 'completed', to_app_version: '0.1.0', updated_at: null, message: 'ok', next_action: 'continue' };
  assert.equal(isUpdateStatusDto(status), true);
  assert.deepEqual(updateStatusFromSettingsEnvelope({ update_status: status, operation_id: 'hidden' }), status);
  assert.equal(updateStatusFromSettingsEnvelope({ update_status: { ...status, state: 'started' } }), null);
});

test('mount uses existing Settings binding seam and caches the read for the UI session', async () => {
  resetUpdateStatusCacheForTests();
  const cards = [];
  let fetches = 0;
  const anchor = { insertAdjacentHTML(_position, html) { cards.push({ html, outerHTML: html, isConnected: true }); } };
  const root = { querySelector(selector) { if (selector === '[data-tax-rate-section]') return anchor; if (selector === '[data-update-status-card]') return cards.at(-1) ?? null; return null; } };
  const fetchStatus = async () => { fetches += 1; return { update_status: { state: 'completed', to_app_version: '0.1.0', updated_at: null, message: 'Готово.', next_action: 'Можно продолжать работу.' } }; };
  assert.equal(mountSettingsUpdateStatus(root, fetchStatus), true);
  await flush();
  assert.equal(fetches, 1);
  assert.match(cards[0].outerHTML, /Обновление завершено/);
  const secondRoot = { querySelector(selector) { if (selector === '[data-tax-rate-section]') return anchor; if (selector === '[data-update-status-card]') return null; return null; } };
  mountSettingsUpdateStatus(secondRoot, fetchStatus);
  assert.equal(fetches, 1);
});

test('settings integration does not touch protected main.ts and exposes no update mutation', () => {
  const bindings = readFileSync(new URL('../src/settings-tax-bindings.ts', import.meta.url), 'utf8');
  const presenter = readFileSync(new URL('../src/settings-update-status.ts', import.meta.url), 'utf8');
  assert.match(bindings, /mountSettingsUpdateStatus/);
  assert.match(presenter, /fetch\('\/api\/settings\/status'\)/);
  assert.doesNotMatch(presenter, /method:\s*['"](?:POST|PUT|PATCH|DELETE)/i);
});
