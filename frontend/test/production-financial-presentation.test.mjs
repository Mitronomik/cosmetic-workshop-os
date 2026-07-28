import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import {
  FINANCIAL_ESTIMATE_STATUSES,
  financialEstimateStatusIsValid,
  readinessFinancialsAreValid,
} from '../dist-tests/production-financial-presentation/production-financial-contract.js';
import {
  FINANCIAL_VALUE_UNAVAILABLE,
  financialEstimateStatusLabel,
  renderBatchFinancialSnapshot,
  renderBatchListFinancialCells,
  renderBatchListFinancialHeadings,
  renderReadinessFinancialSection,
} from '../dist-tests/production-financial-presentation/production-financial-presentation.js';

// --------------------------------------------------------------------------
// Minimal read-only view over rendered markup
// --------------------------------------------------------------------------

const voidTags = new Set(['br', 'hr', 'img', 'input', 'link', 'meta']);

class ViewNode {
  constructor(tag = '', attrs = {}, text = '') { this.tag = tag; this.attrs = attrs; this.children = []; this.text = text; }
  append(node) { this.children.push(node); }
  get textContent() { return this.tag === '#text' ? this.text : this.children.map((child) => child.textContent).join(''); }
  getAttribute(name) { return this.attrs[name] ?? null; }
  hasAttribute(name) { return Object.hasOwn(this.attrs, name); }
  querySelector(selector) { return this.querySelectorAll(selector)[0] ?? null; }
  querySelectorAll(selector) {
    const found = [];
    const visit = (node) => { for (const child of node.children) { if (child.matches(selector)) found.push(child); visit(child); } };
    visit(this);
    return found;
  }
  matches(selector) {
    if (this.tag === '#text') return false;
    const match = selector.match(/^([a-z0-9-]+)?(?:\.([a-z0-9_-]+))?(?:\[([a-z0-9-]+)(?:="([^"]*)")?\])?$/i);
    if (!match) throw new Error(`Unsupported test selector: ${selector}`);
    const [, tag, className, attribute, value] = match;
    if (tag && this.tag !== tag.toLowerCase()) return false;
    if (className && !(this.attrs.class ?? '').split(/\s+/).includes(className)) return false;
    if (attribute && !this.hasAttribute(attribute)) return false;
    return value === undefined || this.attrs[attribute] === value;
  }
}

function decodeEntities(value) {
  return value.replaceAll('&lt;', '<').replaceAll('&gt;', '>').replaceAll('&quot;', '"').replaceAll('&#39;', "'").replaceAll('&amp;', '&');
}

function renderView(markup) {
  const root = new ViewNode('root');
  const stack = [root];
  for (const token of markup.match(/<[^>]+>|[^<]+/g) ?? []) {
    if (token.startsWith('</')) { stack.pop(); continue; }
    if (token.startsWith('<')) {
      const open = token.match(/^<([a-z0-9-]+)([^>]*)>/i);
      if (!open) continue;
      const tag = open[1].toLowerCase();
      const attrs = {};
      for (const attribute of open[2].matchAll(/([a-z0-9-]+)(?:="([^"]*)")?/gi)) attrs[attribute[1]] = decodeEntities(attribute[2] ?? '');
      const node = new ViewNode(tag, attrs);
      stack.at(-1).append(node);
      if (!voidTags.has(tag) && !token.endsWith('/>')) stack.push(node);
      continue;
    }
    stack.at(-1).append(new ViewNode('#text', {}, decodeEntities(token)));
  }
  return root;
}

function escapeHtml(value) {
  return value.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;').replaceAll("'", '&#39;');
}

const formatters = { escapeHtml, formatDateTime: (value) => `ЧЕЛОВЕКОЧИТАЕМО:${value}` };

/** Renderings a null value must never collapse into. */
const ZERO_RENDERINGS = ['0', '0.00', '0 ₽', '0.00 ₽', '0%', '0 %', '0.00 %'];

function readinessFinancials(overrides = {}) {
  return {
    sale_price: '300.00',
    estimated_cost: '120.00',
    tax_rate_percent: '6.00',
    tax_rate_effective_at: '2026-07-27T19:44:53Z',
    estimated_tax: '18.00',
    estimated_margin: '162.00',
    estimated_margin_percent: '54.00',
    financial_estimate_status: 'available',
    ...overrides,
  };
}

function batchFinancials(overrides = {}) {
  return {
    sale_price: '300.00',
    total_cost: '120.00',
    tax_rate_percent_snapshot: '6.00',
    tax_rate_effective_at_snapshot: '2026-07-27T19:44:53Z',
    tax: '18.00',
    margin: '162.00',
    margin_percent: '54.00',
    ...overrides,
  };
}

function listFinancials(overrides = {}) {
  return { sale_price: '300.00', total_cost: '120.00', tax: '18.00', margin: '162.00', margin_percent: '54.00', ...overrides };
}

function readinessView(overrides = {}) { return renderView(renderReadinessFinancialSection(readinessFinancials(overrides), formatters)); }
function batchView(overrides = {}) { return renderView(renderBatchFinancialSnapshot(batchFinancials(overrides), formatters)); }
function listView(overrides = {}) { return renderView(`<table><tbody><tr>${renderBatchListFinancialCells(listFinancials(overrides), formatters)}</tr></tbody></table>`); }

function metric(view, key) { return view.querySelector(`[data-financial-metric="${key}"]`); }
function metricText(view, key) { return metric(view, key).querySelector('p').textContent.trim(); }

// --------------------------------------------------------------------------
// Readiness financial estimate
// --------------------------------------------------------------------------

test('the three backend financial statuses render with their accepted Russian labels', () => {
  const expected = { available: 'Доступно', partial: 'Частично', unavailable: 'Недоступно' };
  const pills = { available: 'success', partial: 'warning', unavailable: 'muted' };

  for (const status of FINANCIAL_ESTIMATE_STATUSES) {
    const view = readinessView({ financial_estimate_status: status });
    const pill = view.querySelector(`[data-financial-estimate-status="${status}"]`);

    assert.equal(financialEstimateStatusLabel(status), expected[status], status);
    // The label always travels with the pill, so status is never colour-only.
    assert.match(pill.textContent, new RegExp(`${expected[status]}$`), status);
    assert.equal(pill.getAttribute('class').split(/\s+/).includes(pills[status]), true, status);
  }
});

test('the rendered status comes from the backend field and is never derived from null values', () => {
  // Every financial value is unavailable, yet the backend still says `partial`.
  const view = readinessView({
    financial_estimate_status: 'partial',
    sale_price: null,
    estimated_cost: null,
    estimated_tax: null,
    estimated_margin: null,
    estimated_margin_percent: null,
  });

  assert.equal(view.querySelector('[data-financial-estimate-status="partial"]') !== null, true);
  assert.equal(view.querySelector('[data-financial-estimate-status="unavailable"]'), null);

  // And the mirror case: complete values with a backend `unavailable` verdict.
  const complete = readinessView({ financial_estimate_status: 'unavailable' });
  assert.equal(complete.querySelector('[data-financial-estimate-status="unavailable"]') !== null, true);
  assert.equal(metricText(complete, 'estimated-margin'), '162.00 ₽');
});

test('every authorized readiness financial field is displayed', () => {
  const view = readinessView();

  assert.equal(metricText(view, 'sale-price'), '300.00 ₽');
  assert.equal(metricText(view, 'estimated-cost'), '120.00 ₽');
  assert.equal(metricText(view, 'tax-rate'), '6.00 %');
  assert.equal(metricText(view, 'estimated-tax'), '18.00 ₽');
  assert.equal(metricText(view, 'estimated-margin'), '162.00 ₽');
  assert.equal(metricText(view, 'estimated-margin-percent'), '54.00 %');
  assert.deepEqual(
    view.querySelectorAll('[data-financial-metric]').map((node) => node.querySelector('strong').textContent),
    ['Цена продажи', 'Ориентировочная себестоимость', 'Ставка налога', 'Налог', 'Маржа', 'Маржа, %'],
  );
});

test('a configured rate shows a human-readable effective timestamp and never the raw API value', () => {
  const view = readinessView();
  const effectiveAt = view.querySelector('[data-financial-rate-effective-at="true"]');

  assert.equal(effectiveAt.textContent, 'Ставка действует с: ЧЕЛОВЕКОЧИТАЕМО:2026-07-27T19:44:53Z');
  // The formatter output is what the user reads; the raw ISO string is never
  // exposed on its own as technical text.
  assert.equal(/(^|[^:])2026-07-27T19:44:53Z/.test(view.textContent), false);
});

test('a configured zero rate is a real zero, and a missing rate is never shown as 0%', () => {
  const zero = readinessView({ tax_rate_percent: '0.00', estimated_tax: '0.00', estimated_margin: '180.00', estimated_margin_percent: '60.00' });
  assert.equal(metricText(zero, 'tax-rate'), '0.00 %');
  assert.equal(metricText(zero, 'estimated-tax'), '0.00 ₽');
  assert.equal(zero.querySelector('[data-financial-rate-effective-at="true"]') !== null, true);

  // A missing rate and an invalid persisted rate both reach the frontend as the
  // one `null/null` pair, and neither may be rendered as a configured zero.
  const missing = readinessView({
    tax_rate_percent: null,
    tax_rate_effective_at: null,
    estimated_tax: null,
    estimated_margin: null,
    estimated_margin_percent: null,
    financial_estimate_status: 'partial',
  });
  assert.equal(metricText(missing, 'tax-rate'), FINANCIAL_VALUE_UNAVAILABLE);
  assert.equal(metric(missing, 'tax-rate').querySelector('[data-financial-value="unavailable"]') !== null, true);
  assert.equal(missing.querySelector('[data-financial-rate-effective-at="true"]'), null);
});

test('a missing sale price or cost is unavailable, while a zero sale price stays a real zero', () => {
  const missing = readinessView({ sale_price: null, estimated_cost: null, estimated_margin: null, estimated_margin_percent: null, financial_estimate_status: 'partial' });
  assert.equal(metricText(missing, 'sale-price'), FINANCIAL_VALUE_UNAVAILABLE);
  assert.equal(metricText(missing, 'estimated-cost'), FINANCIAL_VALUE_UNAVAILABLE);
  for (const key of ['sale-price', 'estimated-cost', 'estimated-margin']) {
    assert.equal(ZERO_RENDERINGS.includes(metricText(missing, key)), false, key);
  }

  const zeroSalePrice = readinessView({ sale_price: '0.00', estimated_tax: '0.00', estimated_margin: '-120.00', estimated_margin_percent: null, financial_estimate_status: 'partial' });
  assert.equal(metricText(zeroSalePrice, 'sale-price'), '0.00 ₽');
  assert.equal(metric(zeroSalePrice, 'sale-price').querySelector('[data-financial-value="known"]') !== null, true);
  assert.equal(metricText(zeroSalePrice, 'estimated-margin-percent'), FINANCIAL_VALUE_UNAVAILABLE);
});

test('positive, zero and negative margins stay distinguishable and are never clamped', () => {
  const positive = readinessView();
  assert.equal(metric(positive, 'estimated-margin').querySelector('[data-financial-sign="negative"]'), null);

  const zero = readinessView({ estimated_margin: '0.00', estimated_margin_percent: '0.00' });
  assert.equal(metricText(zero, 'estimated-margin'), '0.00 ₽');
  assert.equal(metricText(zero, 'estimated-margin-percent'), '0.00 %');
  assert.equal(metric(zero, 'estimated-margin').querySelector('[data-financial-sign="negative"]'), null);

  const negative = readinessView({ estimated_margin: '-45.50', estimated_margin_percent: '-15.17' });
  assert.equal(metricText(negative, 'estimated-margin'), '-45.50 ₽');
  assert.equal(metricText(negative, 'estimated-margin-percent'), '-15.17 %');
  assert.equal(metric(negative, 'estimated-margin').querySelector('[data-financial-sign="negative"]') !== null, true);
  assert.equal(metric(negative, 'estimated-margin-percent').querySelector('[data-financial-sign="negative"]') !== null, true);
});

test('the readiness financial block carries no warning of its own', () => {
  const view = readinessView({ financial_estimate_status: 'unavailable', sale_price: null, estimated_tax: null, estimated_margin: null, estimated_margin_percent: null });

  // Backend readiness warnings are rendered once by the existing warning
  // section; this block must never restate or alias one.
  for (const forbidden of ['предупрежд', 'Ставка налога не настроена', 'Не удалось', 'ошибк']) {
    assert.equal(view.textContent.toLowerCase().includes(forbidden.toLowerCase()), false, forbidden);
  }
  assert.equal(view.querySelector('.warning-message'), null);
  assert.equal(view.querySelector('.error-message'), null);
});

// --------------------------------------------------------------------------
// Immutable ProductionBatch financial snapshot
// --------------------------------------------------------------------------

test('the immutable batch snapshot displays every persisted financial value with fixed-at-production context', () => {
  const view = batchView();

  assert.deepEqual(
    view.querySelectorAll('[data-financial-metric]').map((node) => node.querySelector('strong').textContent),
    ['Цена продажи', 'Себестоимость', 'Ставка налога при изготовлении', 'Ставка действовала с', 'Налог', 'Маржа', 'Маржа, %'],
  );
  assert.equal(metricText(view, 'sale-price'), '300.00 ₽');
  assert.equal(metricText(view, 'total-cost'), '120.00 ₽');
  assert.equal(metricText(view, 'tax-rate-snapshot'), '6.00 %');
  assert.equal(metricText(view, 'tax-rate-effective-at-snapshot'), 'ЧЕЛОВЕКОЧИТАЕМО:2026-07-27T19:44:53Z');
  assert.equal(metricText(view, 'tax'), '18.00 ₽');
  assert.equal(metricText(view, 'margin'), '162.00 ₽');
  assert.equal(metricText(view, 'margin-percent'), '54.00 %');
  assert.equal(view.querySelector('h3').textContent, 'Фактическая экономика партии');
  assert.match(view.textContent, /зафиксированы при изготовлении и не меняются вместе с текущими настройками/);
});

test('an old batch with a null snapshot pair reads as unavailable, never as zero', () => {
  const historical = batchView({ tax_rate_percent_snapshot: null, tax_rate_effective_at_snapshot: null, tax: null, margin: null, margin_percent: null });

  for (const key of ['tax-rate-snapshot', 'tax-rate-effective-at-snapshot', 'tax', 'margin', 'margin-percent']) {
    assert.equal(metricText(historical, key), FINANCIAL_VALUE_UNAVAILABLE, key);
    assert.equal(ZERO_RENDERINGS.includes(metricText(historical, key)), false, key);
  }
});

test('a configured zero snapshot stays a real zero and a negative snapshot stays negative', () => {
  const zero = batchView({ tax_rate_percent_snapshot: '0.00', tax: '0.00' });
  assert.equal(metricText(zero, 'tax-rate-snapshot'), '0.00 %');
  assert.equal(metricText(zero, 'tax'), '0.00 ₽');
  assert.equal(metricText(zero, 'tax-rate-effective-at-snapshot'), 'ЧЕЛОВЕКОЧИТАЕМО:2026-07-27T19:44:53Z');

  const negative = batchView({ margin: '-30.00', margin_percent: '-10.00' });
  assert.equal(metricText(negative, 'margin'), '-30.00 ₽');
  assert.equal(metricText(negative, 'margin-percent'), '-10.00 %');
  assert.equal(metric(negative, 'margin').querySelector('[data-financial-sign="negative"]') !== null, true);
});

test('the batch snapshot exposes no raw timestamp, no DTO field name and no estimate comparison', () => {
  const markup = renderBatchFinancialSnapshot(batchFinancials(), formatters);

  for (const forbidden of ['tax_rate_percent_snapshot', 'tax_rate_effective_at_snapshot', 'margin_percent', 'sale_price', 'total_cost']) {
    assert.equal(markup.includes(forbidden), false, forbidden);
  }
  assert.equal(/(^|[^:])2026-07-27T19:44:53Z/.test(renderView(markup).textContent), false);
  for (const forbidden of ['Оценка', 'Отклонение', 'Разница', 'Текущая ставка', 'Настройк']) {
    assert.equal(markup.includes(forbidden), false, forbidden);
  }
});

test('one template renders the production-success result and an existing batch identically', () => {
  const snapshot = batchFinancials();

  assert.equal(renderBatchFinancialSnapshot(snapshot, formatters), renderBatchFinancialSnapshot({ ...snapshot }, formatters));

  // The application shell must call the one shared renderer from both the
  // production-success card and the historical batch detail.
  const shell = readFileSync(new URL('../src/main.ts', import.meta.url), 'utf8');
  assert.equal((shell.match(/renderBatchFinancialSnapshot\(/g) || []).length, 2);
});

// --------------------------------------------------------------------------
// Production history list
// --------------------------------------------------------------------------

test('the compact list summary shows the five existing list fields and no rate snapshot', () => {
  const view = listView();
  const cells = view.querySelectorAll('[data-batch-list-financials]');

  assert.equal(cells.length, 2);
  assert.match(view.textContent, /300\.00 ₽/);
  assert.match(view.textContent, /Себестоимость: 120\.00 ₽/);
  assert.match(view.textContent, /Маржа: 162\.00 ₽/);
  assert.match(view.textContent, /Налог: 18\.00 ₽/);
  assert.match(view.textContent, /Маржа, %: 54\.00 %/);
  assert.equal(renderBatchListFinancialHeadings(), '<th>Цена и себестоимость</th><th>Маржа и налог</th>');
});

test('the list never renders a rate snapshot even when the caller passes one', () => {
  const markup = renderBatchListFinancialCells(
    { ...listFinancials(), tax_rate_percent_snapshot: '6.00', tax_rate_effective_at_snapshot: '2026-07-27T19:44:53Z' },
    formatters,
  );

  assert.equal(markup.includes('2026-07-27'), false);
  assert.equal(markup.includes('Ставка'), false);
  assert.equal(markup.includes('при изготовлении'), false);
});

test('list zero, negative and unavailable values stay distinguishable', () => {
  const zero = listView({ tax: '0.00', margin: '0.00', margin_percent: '0.00' });
  assert.match(zero.textContent, /Налог: 0\.00 ₽/);
  assert.match(zero.textContent, /Маржа: 0\.00 ₽/);

  const negative = listView({ margin: '-42.00', margin_percent: '-14.00' });
  assert.match(negative.textContent, /Маржа: -42\.00 ₽/);
  assert.equal(negative.querySelector('[data-financial-sign="negative"]') !== null, true);

  const unavailable = listView({ sale_price: null, total_cost: null, tax: null, margin: null, margin_percent: null });
  assert.equal(unavailable.querySelectorAll('[data-financial-value="unavailable"]').length, 5);
  assert.equal(unavailable.querySelector('[data-financial-value="known"]'), null);
  assert.equal(/\d/.test(unavailable.textContent), false, 'no fabricated numeric value');
});

// --------------------------------------------------------------------------
// Financial DTO contract
// --------------------------------------------------------------------------

test('a complete readiness financial contract is accepted, including explicit null/null', () => {
  assert.equal(readinessFinancialsAreValid(readinessFinancials()), true);
  assert.equal(readinessFinancialsAreValid(readinessFinancials({
    sale_price: null,
    estimated_cost: null,
    tax_rate_percent: null,
    tax_rate_effective_at: null,
    estimated_tax: null,
    estimated_margin: null,
    estimated_margin_percent: null,
    financial_estimate_status: 'unavailable',
  })), true);
  assert.equal(readinessFinancialsAreValid(readinessFinancials({ tax_rate_percent: '0.00' })), true);
});

test('a readiness payload missing any additive financial key is untrusted', () => {
  for (const key of Object.keys(readinessFinancials())) {
    const outdated = readinessFinancials();
    delete outdated[key];
    assert.equal(readinessFinancialsAreValid(outdated), false, `missing ${key}`);
  }
  assert.equal(readinessFinancialsAreValid(null), false);
  assert.equal(readinessFinancialsAreValid([readinessFinancials()]), false);
});

test('an unknown financial status is rejected instead of being normalized', () => {
  for (const status of FINANCIAL_ESTIMATE_STATUSES) assert.equal(financialEstimateStatusIsValid(status), true, status);
  for (const status of ['Available', 'AVAILABLE', 'ready', 'known', '', ' available', null, undefined, 0, 1, true, {}, ['available']]) {
    assert.equal(financialEstimateStatusIsValid(status), false, JSON.stringify(status));
    assert.equal(readinessFinancialsAreValid(readinessFinancials({ financial_estimate_status: status })), false, JSON.stringify(status));
  }
});

test('a partial, malformed or non-string rate context is rejected rather than repaired', () => {
  for (const overrides of [
    { tax_rate_percent: '6.00', tax_rate_effective_at: null },
    { tax_rate_percent: null, tax_rate_effective_at: '2026-07-27T19:44:53Z' },
    { tax_rate_percent: '6' },
    { tax_rate_percent: '6.0' },
    { tax_rate_percent: '06.00' },
    { tax_rate_percent: '100.01' },
    { tax_rate_percent: 6 },
    { tax_rate_effective_at: '2026-07-27 19:44:53' },
    { tax_rate_effective_at: '2026-07-27T19:44:53.000Z' },
    { tax_rate_effective_at: '2026-07-27T19:44:53+03:00' },
    { tax_rate_effective_at: '2026-02-30T00:00:00Z' },
  ]) {
    assert.equal(readinessFinancialsAreValid(readinessFinancials(overrides)), false, JSON.stringify(overrides));
  }
});

test('a money or percentage result field must be a string or an explicit null', () => {
  for (const key of ['sale_price', 'estimated_cost', 'estimated_tax', 'estimated_margin', 'estimated_margin_percent']) {
    for (const value of [0, 120, true, {}, ['120.00'], undefined]) {
      assert.equal(readinessFinancialsAreValid(readinessFinancials({ [key]: value })), false, `${key}=${JSON.stringify(value)}`);
    }
    assert.equal(readinessFinancialsAreValid(readinessFinancials({ [key]: null })), true, `${key}=null`);
  }
});

// --------------------------------------------------------------------------
// Ownership boundary
// --------------------------------------------------------------------------

test('the financial modules contain no arithmetic and no duplicated tax or margin formula', () => {
  for (const name of ['production-financial-contract', 'production-financial-presentation']) {
    const source = readFileSync(new URL(`../src/${name}.ts`, import.meta.url), 'utf8');
    const code = source.replace(/\/\*\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '');

    for (const forbidden of [/parseFloat/, /parseInt/, /\bNumber\(/, /\bMath\./, /\btoFixed\b/]) {
      assert.equal(forbidden.test(code), false, `${name}: unexpected numeric conversion ${forbidden}`);
    }
    // No re-derivation of a backend formula: no arithmetic operator applied to
    // a DTO value, and no `/ 100` or `* 100` percentage conversion.
    for (const forbidden of [/\b(?:result|batch|item|payload|value)\.\w+\s*[-+*/]\s*[\w(]/, /\/\s*100\b/, /\*\s*100\b/]) {
      assert.equal(forbidden.test(code), false, `${name}: unexpected formula ${forbidden}`);
    }
  }
});
