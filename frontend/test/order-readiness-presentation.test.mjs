import test from 'node:test';
import assert from 'node:assert/strict';
import { renderOrderProductionGate, renderOrderReadinessPanel } from '../dist-tests/order-readiness-presentation/order-readiness-presentation.js';

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

const formatters = {
  escapeHtml,
  formatDate: (value) => `DATE:${value}`,
  formatDateTime: (value) => `DATETIME:${value}`,
  quantityLabel: (value, unit) => `${value ?? '—'} ${unit ?? ''}`.trim(),
  missingQuantityLabel: (value, unit) => `${value ?? '0'} ${unit}`,
  moneyOrMissing: (value) => value === null ? 'Не рассчитано' : `${value} ₽`,
};

function issue(overrides = {}) { return { code: 'issue', severity: 'warning', message: 'Проверьте заказ', field: null, entity_type: 'order', entity_id: 1, ...overrides }; }
function ingredient(overrides = {}) { return { ingredient_id: 10, ingredient_name: 'Гидролат', required_quantity: '50', required_unit: 'g', available_quantity: '100', missing_quantity: null, can_fulfill: true, selected_lots: [{ lot_id: 20, lot_code: 'LOT-20', selected_quantity: '50', unit: 'g', expires_at: '2026-12-01', is_expired: false, expires_soon: false }], warnings: [], ...overrides }; }
function packaging(overrides = {}) { return { packaging_item_id: 30, name: 'Банка', required_quantity: '1', available_quantity: '2', missing_quantity: null, can_fulfill: true, ...overrides }; }
function readiness(overrides = {}) { return { order_id: 1, can_produce: true, status: 'ready', blocking_issues: [], warnings: [], ingredients: [ingredient()], packaging: [packaging()], estimated_cost: '120.00', estimated_tax: null, estimated_margin: null, generated_at: '2026-07-19T10:00:00Z', ...overrides }; }
function readinessPanel(overrides = {}) { return renderView(renderOrderReadinessPanel({ orderId: 1, closed: false, busy: false, error: '', result: readiness(), current: true, ...overrides }, formatters)); }
function productionGate(overrides = {}) { return renderView(renderOrderProductionGate({ orderId: 1, readiness: readiness(), hasCachedReadiness: true, confirming: false, loading: false, blockedByOperation: false, notes: '', error: '', ...overrides }, escapeHtml)); }

test('ready, warning-only and blocked responses render as distinct valid readiness results', () => {
  const ready = readinessPanel();
  assert.equal(ready.querySelector('[data-order-readiness-result="current"]').querySelector('h2').textContent, 'Можно изготовить');
  assert.equal(ready.querySelector('.success').textContent, 'Склад выглядит достаточным');

  const warning = readinessPanel({ result: readiness({ status: 'warning', warnings: [issue({ message: 'Партия скоро истекает', entity_type: 'ingredient_lot', entity_id: 20 })] }) });
  assert.equal(warning.querySelector('h2').textContent, 'Можно изготовить, но есть предупреждения');
  assert.equal(warning.querySelector('h4').textContent, 'Партия «LOT-20»');
  assert.equal(warning.querySelector('li').textContent.trim(), 'Важно Партия скоро истекает');

  const blocked = readinessPanel({ result: readiness({ can_produce: false, status: 'blocked', blocking_issues: [issue({ severity: 'blocking', message: 'Не хватает тары', entity_type: 'packaging_item', entity_id: 30 })], packaging: [packaging({ can_fulfill: false, available_quantity: '0', missing_quantity: '1' })] }) });
  assert.equal(blocked.querySelector('h2').textContent, 'Пока нельзя изготовить');
  assert.equal(blocked.querySelector('h4').textContent, 'Банка');
  assert.equal(blocked.querySelector('[data-order-readiness-error="true"]'), null);
  assert.equal(productionGate({ readiness: readiness({ can_produce: false, status: 'blocked' }) }).querySelector('button[data-action="open-production-confirmation"]'), null);
});

test('system failure is separate from blocked readiness and exposes one retry action', () => {
  const view = readinessPanel({ result: null, error: 'Локальное приложение недоступно <details>' });
  assert.equal(view.querySelector('[data-order-readiness-error="true"]').querySelector('h2').textContent, 'Результат готовности не получен');
  assert.equal(view.querySelectorAll('button[data-action="retry-order-readiness"]').length, 1);
  assert.equal(view.querySelector('[data-order-readiness-result="current"]'), null);
  assert.equal(view.querySelector('details'), null);
  assert.equal(view.querySelector('p').textContent, 'Сбой проверки');
});

test('stale result remains visible but cannot expose Production Confirmation', () => {
  const stale = readinessPanel({ current: false });
  assert.equal(stale.querySelector('[data-order-readiness-result="stale"]').querySelector('h2').textContent, 'Результат нужно обновить');
  assert.equal(stale.querySelector('.warning').textContent, 'Не разрешает изготовление');
  const gate = productionGate({ readiness: null, hasCachedReadiness: true });
  assert.equal(gate.querySelector('button[data-action="open-production-confirmation"]'), null);
  assert.equal(gate.querySelector('p.next-step').textContent, 'Текущий результат проверки отсутствует. Повторите проверку перед изготовлением.');
});

test('backend issue text and component, lot and packaging context labels render only as escaped text', () => {
  const result = readiness({
    status: 'warning',
    ingredients: [ingredient({ ingredient_name: 'Компонент <img src=x>', selected_lots: [{ lot_id: 20, lot_code: 'LOT <script>alert(1)</script>', selected_quantity: '50', unit: 'g', expires_at: null, is_expired: false, expires_soon: true }] })],
    packaging: [packaging({ name: 'Тара <svg onload=alert(1)>' })],
    warnings: [
      issue({ message: 'Сообщение <script>alert(2)</script>', entity_type: 'ingredient', entity_id: 10 }),
      issue({ message: 'Партия требует внимания', entity_type: 'ingredient_lot', entity_id: 20 }),
      issue({ message: 'Тара требует внимания', entity_type: 'packaging_item', entity_id: 30 }),
    ],
  });
  const view = readinessPanel({ result });
  assert.equal(view.querySelector('script'), null);
  assert.equal(view.querySelector('img'), null);
  assert.equal(view.querySelector('svg'), null);
  assert.deepEqual(view.querySelectorAll('h4').map((node) => node.textContent), ['Компонент <img src=x>', 'Партия «LOT <script>alert(1)</script>»', 'Тара <svg onload=alert(1)>']);
  assert.equal(view.querySelectorAll('li')[0].textContent.trim(), 'Важно Сообщение <script>alert(2)</script>');
});

test('loading view exposes honest checking text and busy semantics', () => {
  const view = readinessPanel({ busy: true, result: null });
  const busy = view.querySelector('[data-order-readiness-busy="true"]');
  assert.equal(busy.getAttribute('aria-busy'), 'true');
  assert.equal(busy.querySelector('h2').textContent, 'Проверяем…');
  assert.equal(view.querySelector('[data-order-readiness-result="current"]'), null);
});

test('Production Confirmation is rendered only for a current positive unlocked result', () => {
  assert.equal(productionGate().querySelectorAll('button[data-action="open-production-confirmation"]').length, 1);
  assert.equal(productionGate({ readiness: readiness({ status: 'warning' }) }).querySelectorAll('button[data-action="open-production-confirmation"]').length, 1);
  assert.equal(productionGate({ readiness: null }).querySelector('button[data-action="open-production-confirmation"]'), null);
  assert.equal(productionGate({ readiness: readiness({ status: 'blocked', can_produce: false }) }).querySelector('button[data-action="open-production-confirmation"]'), null);
  const operationBlocked = productionGate({ blockedByOperation: true });
  assert.equal(operationBlocked.querySelector('button[data-action="open-production-confirmation"]').hasAttribute('disabled'), true);
});
