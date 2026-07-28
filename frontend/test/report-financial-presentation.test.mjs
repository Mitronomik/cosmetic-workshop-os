import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import {
  financeReportDtoIsValid,
  overviewFinanceSummaryIsValid,
  reportsFinanceContractIsValid,
} from '../dist-tests/report-financial-presentation/report-financial-contract.js';
import {
  FINANCE_VALUE_UNAVAILABLE,
  renderFinanceReportSection,
  renderOverviewFinanceSummary,
} from '../dist-tests/report-financial-presentation/report-financial-presentation.js';

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

const formatters = { escapeHtml };

/** Renderings a null value must never collapse into. */
const ZERO_RENDERINGS = ['0', '0.00', '0 ₽', '0.00 ₽', '0%', '0 %', '0.00 %'];

function warning(code, message, field) {
  return { code, message, field };
}

/** A complete, internally consistent snapshot-backed finance response. */
function financeReport(overrides = {}) {
  return {
    generated_at: '2026-07-28T16:56:28Z',
    produced_order_count: 25,
    produced_orders_with_sale_price: 24,
    known_revenue: '10000.00',
    known_production_cost: '6000.00',
    known_tax: '600.00',
    known_margin: '1400.00',
    known_margin_percent: '35.00',
    complete_finance_record_count: 20,
    incomplete_margin_count: 5,
    missing_sale_price_count: 1,
    missing_cost_count: 5,
    tax_snapshot_record_count: 15,
    missing_tax_snapshot_count: 10,
    margin_snapshot_record_count: 14,
    missing_margin_snapshot_count: 11,
    warnings: [],
    ...overrides,
  };
}

/** The same response with every batch covered, so no warning applies. */
function completeFinanceReport(overrides = {}) {
  return financeReport({
    produced_order_count: 10,
    produced_orders_with_sale_price: 10,
    complete_finance_record_count: 10,
    incomplete_margin_count: 0,
    missing_sale_price_count: 0,
    missing_cost_count: 0,
    tax_snapshot_record_count: 10,
    missing_tax_snapshot_count: 0,
    margin_snapshot_record_count: 10,
    missing_margin_snapshot_count: 0,
    ...overrides,
  });
}

function financeView(overrides = {}) { return renderView(renderFinanceReportSection(financeReport(overrides), formatters)); }
function overviewView(overrides = {}) { return renderView(renderOverviewFinanceSummary(financeReport(overrides), formatters)); }

function metricText(view, key) {
  return view.querySelector(`[data-finance-metric="${key}"]`).querySelector('strong').textContent.trim();
}

function metricLabel(view, key) {
  return view.querySelector(`[data-finance-metric="${key}"]`).querySelector('span').textContent.trim();
}

// --------------------------------------------------------------------------
// Snapshot-backed values
// --------------------------------------------------------------------------

test('the five headline metrics show the backend values exactly as returned', () => {
  const view = financeView();

  assert.equal(metricText(view, 'known-revenue'), '10000.00 ₽');
  assert.equal(metricText(view, 'known-production-cost'), '6000.00 ₽');
  assert.equal(metricText(view, 'known-tax'), '600.00 ₽');
  assert.equal(metricText(view, 'known-margin'), '1400.00 ₽');
  assert.equal(metricText(view, 'known-margin-percent'), '35.00 %');
});

test('a configured zero tax is a real zero, never an unavailable value', () => {
  const view = financeView({ known_tax: '0.00' });
  const metric = view.querySelector('[data-finance-metric="known-tax"]');

  assert.equal(metricText(view, 'known-tax'), '0.00 ₽');
  assert.equal(metric.querySelector('[data-finance-value="known"]') !== null, true);
  assert.equal(metric.querySelector('[data-finance-value="unavailable"]'), null);
});

test('a zero aggregate margin and a zero percentage stay real zeros', () => {
  const view = financeView({ known_margin: '0.00', known_margin_percent: '0.00' });

  assert.equal(metricText(view, 'known-margin'), '0.00 ₽');
  assert.equal(metricText(view, 'known-margin-percent'), '0.00 %');
  assert.equal(view.querySelector('[data-finance-metric="known-margin"]').querySelector('[data-finance-value="unavailable"]'), null);
});

test('a negative margin keeps its sign and is marked negative', () => {
  const view = financeView({ known_margin: '-72.00', known_margin_percent: '-36.00' });

  assert.equal(metricText(view, 'known-margin'), '-72.00 ₽');
  assert.equal(metricText(view, 'known-margin-percent'), '-36.00 %');
  for (const key of ['known-margin', 'known-margin-percent']) {
    assert.equal(view.querySelector(`[data-finance-metric="${key}"]`).querySelector('[data-finance-sign="negative"]') !== null, true);
  }
});

test('a positive value is never marked negative', () => {
  const view = financeView();
  assert.equal(view.querySelector('[data-finance-sign="negative"]'), null);
});

test('an unavailable tax or margin says Недоступно and never collapses into a zero', () => {
  const view = financeView({ known_tax: null, known_margin: null, known_margin_percent: null });

  for (const key of ['known-tax', 'known-margin', 'known-margin-percent']) {
    assert.equal(metricText(view, key), FINANCE_VALUE_UNAVAILABLE);
    assert.equal(view.querySelector(`[data-finance-metric="${key}"]`).querySelector('[data-finance-value="unavailable"]') !== null, true);
    assert.equal(ZERO_RENDERINGS.includes(metricText(view, key)), false);
  }
});

test('an unavailable value never renders the raw word null or a DTO field name', () => {
  const markup = renderFinanceReportSection(financeReport({ known_tax: null, known_margin: null, known_margin_percent: null }), formatters);

  assert.equal(/\bnull\b/.test(markup), false);
  assert.equal(markup.includes('known_tax'), false);
  assert.equal(markup.includes('known_margin'), false);
  assert.equal(markup.includes('margin_snapshot_record_count'), false);
  assert.equal(markup.includes('production_batches'), false);
});

// --------------------------------------------------------------------------
// Coverage presentation
// --------------------------------------------------------------------------

test('tax and margin coverage are shown separately as X из Y партий', () => {
  const view = financeView();
  const lines = view.querySelectorAll('[data-finance-coverage-line]');

  assert.equal(lines.length, 2);
  assert.equal(lines[0].textContent.trim(), 'Налог зафиксирован: 15 из 25 партий');
  assert.equal(lines[1].textContent.trim(), 'Маржа зафиксирована: 14 из 25 партий');
});

test('coverage uses the backend counters even when tax and margin cover different batches', () => {
  const view = financeView({ tax_snapshot_record_count: 25, missing_tax_snapshot_count: 0, margin_snapshot_record_count: 3, missing_margin_snapshot_count: 22 });
  const lines = view.querySelectorAll('[data-finance-coverage-line]');

  assert.equal(lines[0].textContent.trim(), 'Налог зафиксирован: 25 из 25 партий');
  assert.equal(lines[1].textContent.trim(), 'Маржа зафиксирована: 3 из 25 партий');
});

test('incomplete coverage is explained in plain language when the backend warns about it', () => {
  for (const code of ['tax_unavailable', 'partial_tax_basis', 'margin_unavailable', 'partial_margin_basis']) {
    const view = financeView({ warnings: [warning(code, 'Текст предупреждения.', 'known_tax')] });
    const note = view.querySelector('[data-finance-incomplete-note="true"]');

    assert.notEqual(note, null, `${code} should explain incomplete coverage`);
    assert.equal(note.textContent.includes('Часть старых партий не содержит финансовых снимков.'), true);
    assert.equal(note.textContent.includes('Они не включены в налог и маржу.'), true);
  }
});

test('the incomplete-coverage note is absent when the backend reports full coverage', () => {
  assert.equal(renderView(renderFinanceReportSection(completeFinanceReport(), formatters)).querySelector('[data-finance-incomplete-note="true"]'), null);
});

test('the incomplete-coverage note is not inferred from a null value alone', () => {
  const view = financeView({ known_tax: null, known_margin: null, known_margin_percent: null, warnings: [] });
  assert.equal(view.querySelector('[data-finance-incomplete-note="true"]'), null);
});

// --------------------------------------------------------------------------
// Legacy paired counters
// --------------------------------------------------------------------------

test('the legacy paired counters use truthful labels in a separate secondary section', () => {
  const view = financeView();
  const section = view.querySelector('[data-finance-source-completeness="true"]');

  assert.notEqual(section, null);
  assert.equal(section.querySelector('h3').textContent.trim(), 'Полнота исходных данных');
  assert.equal(metricLabel(view, 'complete-finance-records'), 'Партий с ценой и себестоимостью');
  assert.equal(metricLabel(view, 'incomplete-finance-records'), 'Партий с неполной парой цены и себестоимости');
  assert.equal(metricText(view, 'complete-finance-records'), '20');
  assert.equal(metricText(view, 'incomplete-finance-records'), '5');
});

test('the legacy paired counters are never presented as snapshot coverage', () => {
  const view = financeView();
  const section = view.querySelector('[data-finance-source-completeness="true"]');

  // 20 and 5 are the paired counters; 15 and 14 are the snapshot counters. The
  // coverage lines must quote the snapshot counters, and the paired section must
  // not claim to describe what was recorded at production time.
  assert.equal(section.textContent.includes('зафиксирован'), false);
  assert.equal(section.textContent.includes('20 из 25'), false);
  for (const line of view.querySelectorAll('[data-finance-coverage-line]')) {
    assert.equal(line.textContent.includes('20'), false);
  }
});

test('the snapshot coverage lines sit outside the source-completeness section', () => {
  const view = financeView();
  assert.equal(view.querySelector('[data-finance-source-completeness="true"]').querySelectorAll('[data-finance-coverage-line]').length, 0);
});

test('the margin percentage is not labelled as a bare Маржа, %', () => {
  const view = financeView();
  const label = metricLabel(view, 'known-margin-percent');

  assert.notEqual(label, 'Маржа, %');
  assert.equal(label, 'Маржа по партиям с зафиксированными финансовыми данными');
});

// --------------------------------------------------------------------------
// Overview and Finance share one presentation
// --------------------------------------------------------------------------

test('the Overview finance summary shows the same values as the Finance tab', () => {
  const finance = financeView();
  const overview = overviewView();

  for (const key of ['known-revenue', 'known-production-cost', 'known-tax', 'known-margin', 'known-margin-percent']) {
    assert.equal(metricText(overview, key), metricText(finance, key));
    assert.equal(metricLabel(overview, key), metricLabel(finance, key));
  }
});

test('the Overview finance summary applies the same zero, negative and unavailable rules', () => {
  const overrides = { known_tax: '0.00', known_margin: '-72.00', known_margin_percent: null };
  const finance = financeView(overrides);
  const overview = overviewView(overrides);

  for (const key of ['known-tax', 'known-margin', 'known-margin-percent']) {
    assert.equal(metricText(overview, key), metricText(finance, key));
  }
  assert.equal(overview.querySelector('[data-finance-sign="negative"]') !== null, true);
  assert.equal(metricText(overview, 'known-margin-percent'), FINANCE_VALUE_UNAVAILABLE);
});

test('the Overview finance summary shows the same coverage lines', () => {
  const overview = overviewView();
  const lines = overview.querySelectorAll('[data-finance-coverage-line]');

  assert.equal(lines.length, 2);
  assert.equal(lines[0].textContent.trim(), 'Налог зафиксирован: 15 из 25 партий');
  assert.equal(lines[1].textContent.trim(), 'Маржа зафиксирована: 14 из 25 партий');
});

test('the Overview finance summary does not repeat the paired-input section', () => {
  assert.equal(overviewView().querySelector('[data-finance-source-completeness="true"]'), null);
});

// --------------------------------------------------------------------------
// Warnings are rendered once, by the existing panel
// --------------------------------------------------------------------------

test('backend warning messages are not repeated inside the finance blocks', () => {
  const message = 'Налог показан только по партиям, где он был зафиксирован при изготовлении.';
  const warnings = [warning('partial_tax_basis', message, 'known_tax')];

  for (const markup of [
    renderFinanceReportSection(financeReport({ warnings }), formatters),
    renderOverviewFinanceSummary(financeReport({ warnings }), formatters),
  ]) {
    assert.equal(markup.includes(message), false);
    assert.equal((markup.match(/Часть старых партий не содержит финансовых снимков\./g) || []).length, 1);
  }
});

test('several coverage warnings still produce exactly one explanation', () => {
  const warnings = [
    warning('partial_tax_basis', 'Налог показан только по части партий.', 'known_tax'),
    warning('partial_margin_basis', 'Маржа показана только по части партий.', 'known_margin'),
  ];
  const markup = renderFinanceReportSection(financeReport({ warnings }), formatters);

  assert.equal((markup.match(/Часть старых партий не содержит финансовых снимков\./g) || []).length, 1);
});

test('an unrelated backend warning does not trigger the coverage explanation', () => {
  const warnings = [warning('missing_sale_price', 'Не у всех произведённых заказов указана цена продажи.', 'known_revenue')];
  assert.equal(renderView(renderFinanceReportSection(completeFinanceReport({ warnings }), formatters)).querySelector('[data-finance-incomplete-note="true"]'), null);
});

// --------------------------------------------------------------------------
// DTO validation
// --------------------------------------------------------------------------

test('a complete snapshot-backed finance response is accepted', () => {
  assert.equal(financeReportDtoIsValid(financeReport()), true);
  assert.equal(overviewFinanceSummaryIsValid({ finance_summary: financeReport() }), true);
  assert.equal(reportsFinanceContractIsValid(financeReport(), { finance_summary: financeReport() }), true);
});

test('a response missing any additive key is rejected as outdated', () => {
  for (const key of ['known_tax', 'tax_snapshot_record_count', 'missing_tax_snapshot_count', 'margin_snapshot_record_count', 'missing_margin_snapshot_count']) {
    const payload = financeReport();
    delete payload[key];
    assert.equal(financeReportDtoIsValid(payload), false, `${key} must be required`);
  }
});

test('a partial additive contract is rejected even when the other keys are present', () => {
  const payload = financeReport();
  delete payload.margin_snapshot_record_count;
  delete payload.missing_margin_snapshot_count;
  assert.equal(financeReportDtoIsValid(payload), false);
});

test('a non-string monetary value is rejected and never coerced', () => {
  for (const key of ['known_revenue', 'known_production_cost', 'known_tax', 'known_margin', 'known_margin_percent']) {
    assert.equal(financeReportDtoIsValid(financeReport({ [key]: 600 })), false, `${key} must not accept a number`);
    assert.equal(financeReportDtoIsValid(financeReport({ [key]: undefined })), false, `${key} must not accept undefined`);
    assert.equal(financeReportDtoIsValid(financeReport({ [key]: {} })), false, `${key} must not accept an object`);
  }
});

test('an explicit null monetary value is accepted as a backend statement', () => {
  assert.equal(financeReportDtoIsValid(financeReport({ known_tax: null, known_margin: null, known_margin_percent: null })), true);
});

test('a malformed counter is rejected', () => {
  assert.equal(financeReportDtoIsValid(financeReport({ tax_snapshot_record_count: '15' })), false);
  assert.equal(financeReportDtoIsValid(financeReport({ tax_snapshot_record_count: null })), false);
});

test('a negative counter is rejected', () => {
  assert.equal(financeReportDtoIsValid(financeReport({ tax_snapshot_record_count: -15, missing_tax_snapshot_count: 40 })), false);
});

test('a fractional counter is rejected', () => {
  assert.equal(financeReportDtoIsValid(financeReport({ margin_snapshot_record_count: 14.5, missing_margin_snapshot_count: 10.5 })), false);
});

test('a counter pair that does not equal the produced order count is rejected', () => {
  assert.equal(financeReportDtoIsValid(financeReport({ tax_snapshot_record_count: 15, missing_tax_snapshot_count: 9 })), false);
  assert.equal(financeReportDtoIsValid(financeReport({ margin_snapshot_record_count: 14, missing_margin_snapshot_count: 12 })), false);
});

test('a malformed warning is rejected', () => {
  for (const malformed of [{ code: 'x' }, { code: 'x', message: 'y' }, { code: 1, message: 'y', field: null }, { code: 'x', message: 'y', field: 3 }, 'partial_tax_basis', null]) {
    assert.equal(financeReportDtoIsValid(financeReport({ warnings: [malformed] })), false);
  }
  assert.equal(financeReportDtoIsValid(financeReport({ warnings: 'partial_tax_basis' })), false);
});

test('a duplicated warning code is rejected', () => {
  const duplicated = [warning('partial_tax_basis', 'Один.', 'known_tax'), warning('partial_tax_basis', 'Два.', 'known_tax')];
  assert.equal(financeReportDtoIsValid(financeReport({ warnings: duplicated })), false);
});

test('a warning with a null field is accepted', () => {
  assert.equal(financeReportDtoIsValid(financeReport({ warnings: [warning('no_production_data', 'Производственных партий пока нет.', null)] })), true);
});

test('a malformed nested overview finance summary is rejected', () => {
  assert.equal(overviewFinanceSummaryIsValid({}), false);
  assert.equal(overviewFinanceSummaryIsValid({ finance_summary: null }), false);
  const missingKey = financeReport();
  delete missingKey.known_tax;
  assert.equal(overviewFinanceSummaryIsValid({ finance_summary: missingKey }), false);
  assert.equal(reportsFinanceContractIsValid(financeReport(), { finance_summary: missingKey }), false);
});

test('a non-object payload is rejected', () => {
  for (const payload of [null, undefined, 'finance', 42, []]) {
    assert.equal(financeReportDtoIsValid(payload), false);
    assert.equal(overviewFinanceSummaryIsValid(payload), false);
  }
});

test('a missing generated_at is rejected', () => {
  assert.equal(financeReportDtoIsValid(financeReport({ generated_at: '' })), false);
  const payload = financeReport();
  delete payload.generated_at;
  assert.equal(financeReportDtoIsValid(payload), false);
});

// --------------------------------------------------------------------------
// The focused modules stay display-only
// --------------------------------------------------------------------------

test('the focused report finance modules perform no financial arithmetic', () => {
  for (const name of ['report-financial-contract', 'report-financial-presentation']) {
    const source = readFileSync(new URL(`../src/${name}.ts`, import.meta.url), 'utf8');
    const code = source.replace(/\/\*\*[\s\S]*?\*\//g, '').replace(/^\s*\/\/.*$/gm, '');

    for (const forbidden of [/parseFloat/, /parseInt/, /\bNumber\(/, /\bMath\./, /\btoFixed\b/]) {
      assert.equal(forbidden.test(code), false, `${name}: unexpected numeric conversion ${forbidden}`);
    }
    // No re-derivation of a backend value: no arithmetic on a DTO field, and no
    // percentage conversion. The one addition in the contract module is the
    // counter-pair rejection guard, which reads `payload[key]` by index.
    for (const forbidden of [/\bfinance\.\w+\s*[-+*/]\s*[\w(]/, /\/\s*100\b/, /\*\s*100\b/]) {
      assert.equal(forbidden.test(code), false, `${name}: unexpected formula ${forbidden}`);
    }
  }
});

test('the application shell renders each finance surface through the focused module', () => {
  const shell = readFileSync(new URL('../src/main.ts', import.meta.url), 'utf8');

  assert.equal((shell.match(/renderFinanceReportSection\(/g) || []).length, 1);
  assert.equal((shell.match(/renderOverviewFinanceSummary\(/g) || []).length, 1);
  // The read path rejects a malformed finance contract before it is applied, so
  // the Reports route falls back to its retained snapshot rather than rendering
  // an unvalidated response.
  assert.equal(shell.includes('reportsFinanceContractIsValid(finance, overview)'), true);
  // The shell no longer owns a finance metric grid of its own.
  assert.equal(shell.includes("['Известная маржа'"), false);
  assert.equal(shell.includes("['Маржа, %'"), false);
});
