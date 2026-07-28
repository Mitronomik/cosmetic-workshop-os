/**
 * The `C2-III-A` Order and `ProductionBatch` financial presentation.
 *
 * Durable contract: `docs/decisions/0012-c2-financial-calculation-snapshots.md`.
 *
 * This module renders backend-owned financial values and nothing else. It never
 * calculates tax, margin or a percentage, never derives the estimate status from
 * which fields are `null`, never reads the current Settings tax rate as a
 * substitute for a historical snapshot, and never compares an estimate with an
 * actual result.
 *
 * Three states stay visibly distinct everywhere:
 *
 * - a backend `"0.00"` renders as a real zero;
 * - `null` renders as `Недоступно` and is never shown as `0`, `0.00`, `0 ₽` or `0%`;
 * - a negative value keeps its sign and is marked as negative.
 *
 * Financial warnings are backend-owned readiness warnings and are rendered by the
 * existing readiness warning section only. This module adds no warning of its own
 * and never duplicates one inside a financial block.
 */

import type {
  BatchFinancialSnapshot,
  BatchIngredientCostLine,
  BatchListFinancials,
  BatchPackagingCostLine,
  FinancialEstimateStatus,
  ReadinessFinancials,
} from './production-financial-contract.js';

// The contract module owns the financial DTO shapes; this module is the single
// financial presentation entry point the app shell imports from, so the input
// types it renders are re-exported here rather than adding a second import
// source at the call site.
export type { BatchFinancialSnapshot, BatchListFinancials, ReadinessFinancials } from './production-financial-contract.js';

/** The application formatters a financial block reuses. */
export type FinancialPresentationFormatters = {
  escapeHtml(value: string): string;
  formatDateTime(value: string): string;
};

/** The formatters the moved per-line cost tables already used in the shell. */
export type BatchCostTableFormatters = {
  escapeHtml(value: string): string;
  formatDecimalForDisplay(value: string | null | undefined, maxFractionDigits?: number): string;
  unitLabel(unit: string): string;
  moneyOrMissing(value: string | null): string;
  formatDate(value: string | null): string;
};

/** The one label used for every unavailable financial value. */
export const FINANCIAL_VALUE_UNAVAILABLE = 'Недоступно';

const ESTIMATE_STATUS_LABELS: Record<FinancialEstimateStatus, string> = {
  available: 'Доступно',
  partial: 'Частично',
  unavailable: 'Недоступно',
};

/**
 * Pill styling per backend status. The label above always travels with it, so
 * the status is never communicated by colour alone.
 */
const ESTIMATE_STATUS_PILLS: Record<FinancialEstimateStatus, string> = {
  available: 'success',
  partial: 'warning',
  unavailable: 'muted',
};

/** The human-readable label for a backend financial status, taken as given. */
export function financialEstimateStatusLabel(status: FinancialEstimateStatus): string {
  return ESTIMATE_STATUS_LABELS[status];
}

/**
 * Whether a backend value carries a minus sign.
 *
 * This is a character check on the string the backend returned, not a
 * comparison and not a conversion: a negative margin must stay visibly negative
 * rather than being clamped or rendered like a zero.
 */
function hasNegativeSign(value: string): boolean {
  return value.startsWith('-');
}

function unavailableValue(): string {
  return `<span class="muted-text" data-financial-value="unavailable">${FINANCIAL_VALUE_UNAVAILABLE}</span>`;
}

function knownValue(rendered: string, raw: string): string {
  return hasNegativeSign(raw)
    ? `<span class="danger-text" data-financial-value="known" data-financial-sign="negative">${rendered}</span>`
    : `<span data-financial-value="known">${rendered}</span>`;
}

/** A money value, exactly as the backend returned it, with the ruble suffix. */
function moneyValue(f: FinancialPresentationFormatters, value: string | null): string {
  return value === null ? unavailableValue() : knownValue(`${f.escapeHtml(value)} ₽`, value);
}

/** A percentage value — a margin percentage or a tax rate — never reformatted. */
function percentValue(f: FinancialPresentationFormatters, value: string | null): string {
  return value === null ? unavailableValue() : knownValue(`${f.escapeHtml(value)} %`, value);
}

/** A backend timestamp rendered through the existing application formatter. */
function timestampValue(f: FinancialPresentationFormatters, value: string | null): string {
  return value === null
    ? unavailableValue()
    : `<span data-financial-value="known">${f.escapeHtml(f.formatDateTime(value))}</span>`;
}

function metric(label: string, value: string, key: string): string {
  return `<div data-financial-metric="${key}"><strong>${label}</strong><p>${value}</p></div>`;
}

/**
 * The Order readiness financial estimate.
 *
 * Rendered inside the existing readiness result card, next to the existing
 * physical readiness blocks. It does not change `can_produce`, the physical
 * readiness status, or whether a warning blocks production.
 */
export function renderReadinessFinancialSection(
  result: ReadinessFinancials,
  f: FinancialPresentationFormatters,
): string {
  const status = result.financial_estimate_status;
  const effectiveAt = result.tax_rate_effective_at === null
    ? ''
    : `<p class="muted-text" data-financial-rate-effective-at="true">Ставка действует с: ${f.escapeHtml(f.formatDateTime(result.tax_rate_effective_at))}</p>`;
  return `<div class="readiness-block" data-readiness-financials="true"><div class="section-heading"><h3>Предварительная экономика</h3><span class="pill ${ESTIMATE_STATUS_PILLS[status]}" data-financial-estimate-status="${status}">Оценка: ${ESTIMATE_STATUS_LABELS[status]}</span></div><div class="readiness-grid">${metric('Цена продажи', moneyValue(f, result.sale_price), 'sale-price')}${metric('Ориентировочная себестоимость', moneyValue(f, result.estimated_cost), 'estimated-cost')}${metric('Ставка налога', percentValue(f, result.tax_rate_percent), 'tax-rate')}${metric('Налог', moneyValue(f, result.estimated_tax), 'estimated-tax')}${metric('Маржа', moneyValue(f, result.estimated_margin), 'estimated-margin')}${metric('Маржа, %', percentValue(f, result.estimated_margin_percent), 'estimated-margin-percent')}</div>${effectiveAt}<p class="next-step">Это оценка на момент проверки. Приложение не подставляет налоговую ставку само и ничего не пересчитывает в интерфейсе.</p></div>`;
}

/**
 * The immutable financial result of a produced batch.
 *
 * One template serves both the production-success card and the existing batch
 * detail of a produced or delivered Order, so the two can never drift apart. No
 * estimate-versus-actual variance is shown, and the current Settings rate is
 * never compared with the historical snapshot.
 */
export function renderBatchFinancialSnapshot(
  batch: BatchFinancialSnapshot,
  f: FinancialPresentationFormatters,
): string {
  return `<div class="readiness-block" data-batch-financials="true"><h3>Фактическая экономика партии</h3><div class="readiness-grid">${metric('Цена продажи', moneyValue(f, batch.sale_price), 'sale-price')}${metric('Себестоимость', moneyValue(f, batch.total_cost), 'total-cost')}${metric('Ставка налога при изготовлении', percentValue(f, batch.tax_rate_percent_snapshot), 'tax-rate-snapshot')}${metric('Ставка действовала с', timestampValue(f, batch.tax_rate_effective_at_snapshot), 'tax-rate-effective-at-snapshot')}${metric('Налог', moneyValue(f, batch.tax), 'tax')}${metric('Маржа', moneyValue(f, batch.margin), 'margin')}${metric('Маржа, %', percentValue(f, batch.margin_percent), 'margin-percent')}</div><p class="next-step">Финансовые значения зафиксированы при изготовлении и не меняются вместе с текущими настройками.</p></div>`;
}

/**
 * The compact operational financial summary of one production-history row.
 *
 * Two existing table cells, using only the five fields the list DTO carries. The
 * rate snapshots stay detail-only and never appear here.
 */
export function renderBatchListFinancialCells(
  item: BatchListFinancials,
  f: FinancialPresentationFormatters,
): string {
  return `<td data-batch-list-financials="cost">${moneyValue(f, item.sale_price)}<small>Себестоимость: ${moneyValue(f, item.total_cost)}</small></td><td data-batch-list-financials="result">Маржа: ${moneyValue(f, item.margin)}<small>Налог: ${moneyValue(f, item.tax)} · Маржа, %: ${percentValue(f, item.margin_percent)}</small></td>`;
}

/** The two column headings the cells above fill. */
export function renderBatchListFinancialHeadings(): string {
  return '<th>Цена и себестоимость</th><th>Маржа и налог</th>';
}

/**
 * The per-line cost snapshots of a produced batch.
 *
 * Moved unchanged out of the application shell so the batch financial
 * presentation lives in one focused module. The markup, copy and the existing
 * `moneyOrMissing` formatting are preserved exactly.
 */
export function renderBatchCostTables(
  batch: { ingredients: BatchIngredientCostLine[]; packaging: BatchPackagingCostLine[] },
  f: BatchCostTableFormatters,
): string {
  return `${renderBatchIngredientCostTable(batch.ingredients, f)}${renderBatchPackagingCostTable(batch.packaging, f)}`;
}

function renderBatchIngredientCostTable(rows: BatchIngredientCostLine[], f: BatchCostTableFormatters): string {
  return `<div class="readiness-block"><h3>Списанные компоненты</h3>${rows.length ? `<div class="table-wrap"><table class="compact-catalog-table"><thead><tr><th>Компонент</th><th>Партия</th><th>Нужно</th><th>Списано</th><th>Ед.</th><th>Цена за ед.</th><th>Стоимость</th><th>Срок годности</th></tr></thead><tbody>${rows.map((r) => `<tr><td><strong>${f.escapeHtml(r.ingredient_name_snapshot)}</strong></td><td>${f.escapeHtml(r.lot_code_snapshot || 'Без номера')}</td><td>${f.formatDecimalForDisplay(r.required_quantity)}</td><td>${f.formatDecimalForDisplay(r.consumed_quantity)}</td><td>${f.unitLabel(r.unit)}</td><td>${f.moneyOrMissing(r.unit_cost_snapshot)}</td><td>${f.moneyOrMissing(r.total_cost_snapshot)}</td><td>${r.expiration_date_snapshot ? f.formatDate(r.expiration_date_snapshot) : 'Не указан'}</td></tr>`).join('')}</tbody></table></div>` : '<p class="empty-hint">Списания компонентов в снимке не найдены.</p>'}</div>`;
}

function renderBatchPackagingCostTable(rows: BatchPackagingCostLine[], f: BatchCostTableFormatters): string {
  return `<div class="readiness-block"><h3>Списанная тара</h3>${rows.length ? `<div class="table-wrap"><table class="compact-catalog-table"><thead><tr><th>Тара</th><th>Количество</th><th>Ед.</th><th>Цена за ед.</th><th>Стоимость</th></tr></thead><tbody>${rows.map((r) => `<tr><td><strong>${f.escapeHtml(r.packaging_name_snapshot)}</strong></td><td>${f.formatDecimalForDisplay(r.quantity)}</td><td>${f.unitLabel(r.unit)}</td><td>${f.moneyOrMissing(r.unit_cost_snapshot)}</td><td>${f.moneyOrMissing(r.total_cost_snapshot)}</td></tr>`).join('')}</tbody></table></div>` : '<p class="empty-hint">Списания тары в снимке не найдены.</p>'}</div>`;
}
