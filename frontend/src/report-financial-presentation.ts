/**
 * The `C2-III-B` `/reports` finance presentation.
 *
 * Durable contract: `docs/reports.md` § *Accepted `C2-III-B` snapshot
 * aggregation contract*.
 *
 * This module displays backend-owned finance values and nothing else. It never
 * calculates known tax, known margin, a margin percentage, a margin basis,
 * snapshot coverage, a missing counter or a report status; it never sums a
 * financial value; and it never infers a warning state from which fields happen
 * to be `null` — the backend states its warnings, and only those are used.
 *
 * Three states stay visibly distinct everywhere:
 *
 * - a backend `"0.00"` renders as a real zero;
 * - `null` renders as `Недоступно`, never as `0`, `0.00`, `0 ₽` or `0%`;
 * - a negative value keeps its sign and is marked as negative.
 *
 * The Overview tab and the Finance tab both render through the helpers here, so
 * the two can never drift into two different presentations of one DTO. The
 * backend warning list itself is rendered once by the existing Reports warning
 * panel; this module adds no copy of it, only a plain-language explanation of
 * what incomplete coverage means for the totals above it — stated separately
 * for tax and for margin, because the batches missing one are not the batches
 * missing the other.
 */

import type { FinanceReportResponse, ReportWarning } from './report-financial-contract.js';

export type { FinanceReportResponse, ReportWarning } from './report-financial-contract.js';

/** The application formatter the finance blocks reuse. */
export type FinanceReportFormatters = {
  escapeHtml(value: string): string;
};

/** The one label used for every unavailable finance value. */
export const FINANCE_VALUE_UNAVAILABLE = 'Недоступно';

/**
 * The metric labels. `known_margin_percent` is deliberately not called just
 * `Маржа, %`: it covers only the batches that saved a margin, and the label has
 * to say so on its own, without depending on a nearby note being read.
 */
const LABELS = {
  knownRevenue: 'Известная выручка',
  knownProductionCost: 'Известная себестоимость',
  knownTax: 'Зафиксированный налог',
  knownMargin: 'Зафиксированная маржа',
  knownMarginPercent: 'Маржа по партиям с зафиксированными финансовыми данными',
  completeFinanceRecords: 'Партий с ценой и себестоимостью',
  incompleteFinanceRecords: 'Партий с неполной парой цены и себестоимости',
  missingSalePrice: 'Без цены продажи',
  missingCost: 'Без себестоимости',
  producedOrders: 'Произведённых партий',
  withSalePrice: 'С ценой продажи',
} as const;

/**
 * The backend codes that mean a total covers only some batches, kept apart by
 * which total they are about.
 *
 * Tax coverage and margin coverage are separate facts: a batch can have saved a
 * tax and no margin, or a margin and no tax. Nothing here merges the two code
 * sets, because doing so would state that one set of batches is missing from
 * both totals when the backend only said one total was incomplete.
 */
const INCOMPLETE_TAX_CODES = ['tax_unavailable', 'partial_tax_basis'] as const;
const INCOMPLETE_MARGIN_CODES = ['margin_unavailable', 'partial_margin_basis'] as const;

/**
 * Whether a backend value carries a minus sign.
 *
 * A character check on the string the backend returned — not a comparison and
 * not a conversion — so a negative margin stays visibly negative instead of
 * being clamped or rendered like a zero.
 */
function hasNegativeSign(value: string): boolean {
  return value.startsWith('-');
}

function unavailableValue(): string {
  return `<span class="muted-text" data-finance-value="unavailable">${FINANCE_VALUE_UNAVAILABLE}</span>`;
}

function knownValue(rendered: string, raw: string): string {
  return hasNegativeSign(raw)
    ? `<span class="danger-text" data-finance-value="known" data-finance-sign="negative">${rendered}</span>`
    : `<span data-finance-value="known">${rendered}</span>`;
}

/** A money value, exactly as the backend returned it, with the ruble suffix. */
function moneyValue(f: FinanceReportFormatters, value: string | null): string {
  return value === null ? unavailableValue() : knownValue(`${f.escapeHtml(value)} ₽`, value);
}

/** A percentage value, never reformatted and never recomputed. */
function percentValue(f: FinanceReportFormatters, value: string | null): string {
  return value === null ? unavailableValue() : knownValue(`${f.escapeHtml(value)} %`, value);
}

/** A backend counter, shown as the whole number the backend stated. */
function countValue(value: number): string {
  return `<span data-finance-value="count">${value}</span>`;
}

function metric(label: string, value: string, key: string): string {
  return `<article class="metric-card" data-finance-metric="${key}"><span>${label}</span><strong>${value}</strong></article>`;
}

function metricGrid(cards: string): string {
  return `<div class="overview-grid">${cards}</div>`;
}

/**
 * The five headline finance metrics, in the order the workshop reads them:
 * what came in, what it cost, what was set aside as tax, what was left, and
 * what share that was.
 */
function headlineMetrics(finance: FinanceReportResponse, f: FinanceReportFormatters): string {
  return metricGrid(
    metric(LABELS.knownRevenue, moneyValue(f, finance.known_revenue), 'known-revenue')
    + metric(LABELS.knownProductionCost, moneyValue(f, finance.known_production_cost), 'known-production-cost')
    + metric(LABELS.knownTax, moneyValue(f, finance.known_tax), 'known-tax')
    + metric(LABELS.knownMargin, moneyValue(f, finance.known_margin), 'known-margin')
    + metric(LABELS.knownMarginPercent, percentValue(f, finance.known_margin_percent), 'known-margin-percent'),
  );
}

/**
 * How many batches each total actually covers, in the backend's own counts.
 *
 * Both numbers come straight from the response. Tax and margin coverage can
 * legitimately differ from each other, so they are stated separately rather
 * than merged into one "completeness" figure.
 */
function coverageLines(finance: FinanceReportResponse): string {
  const total = countValue(finance.produced_order_count);
  return `<ul class="finance-coverage" data-finance-coverage="true"><li data-finance-coverage-line="tax">Налог зафиксирован: ${countValue(finance.tax_snapshot_record_count)} из ${total} партий</li><li data-finance-coverage-line="margin">Маржа зафиксирована: ${countValue(finance.margin_snapshot_record_count)} из ${total} партий</li></ul>`;
}

/** One plain-language note about a single total, stated at most once. */
function coverageNote(total: string, text: string): string {
  return `<p class="page-message" data-finance-incomplete-note="true" data-finance-incomplete-note-line="${total}">${text}</p>`;
}

/**
 * The plain-language explanation of incomplete coverage.
 *
 * Shown only when the backend said a total is incomplete, and said separately
 * for each total it said it about. A missing tax snapshot and a missing margin
 * snapshot are different batches, so the tax note never claims the batches it
 * describes are absent from the margin, and the margin note never claims they
 * are absent from the tax. When the backend reports both, both notes appear —
 * two statements about two subsets, rather than one statement that would read
 * as a single set of batches missing from everything.
 *
 * The notes come from the backend warning codes alone. A `null` total is not
 * evidence of anything on its own, and each note is emitted at most once no
 * matter how many coverage codes the backend sent about the same total.
 *
 * These explain what the totals above leave out; they do not restate the
 * backend warning messages, which the existing Reports warning panel already
 * shows exactly once. Neither note calls the affected batches old: the backend
 * states how many batches saved each value, not when they were produced.
 */
function incompleteCoverageNotes(warnings: ReportWarning[]): string {
  const codes = new Set(warnings.map((warning) => warning.code));
  const taxIncomplete = INCOMPLETE_TAX_CODES.some((code) => codes.has(code));
  const marginIncomplete = INCOMPLETE_MARGIN_CODES.some((code) => codes.has(code));
  return (taxIncomplete ? coverageNote('tax', 'Часть партий не содержит сохранённых данных о налоге. Они не включены в сумму налога.') : '')
    + (marginIncomplete ? coverageNote('margin', 'Часть партий не содержит сохранённых данных о марже. Они не включены в сумму маржи и расчёт её процента.') : '');
}

/**
 * The legacy paired sale-price/cost counters.
 *
 * These describe how complete the *source data* is, not how many batches saved
 * a tax or margin snapshot, so they stay in a clearly separate secondary
 * section with labels that say exactly what they count.
 */
function sourceDataCompletenessSection(finance: FinanceReportResponse): string {
  return `<div class="readiness-block" data-finance-source-completeness="true"><h3>Полнота исходных данных</h3><p class="muted-text">Это данные, введённые по партиям. Они не показывают, у скольких партий сохранены налог и маржа.</p>${metricGrid(
    metric(LABELS.completeFinanceRecords, countValue(finance.complete_finance_record_count), 'complete-finance-records')
    + metric(LABELS.incompleteFinanceRecords, countValue(finance.incomplete_margin_count), 'incomplete-finance-records')
    + metric(LABELS.missingSalePrice, countValue(finance.missing_sale_price_count), 'missing-sale-price')
    + metric(LABELS.missingCost, countValue(finance.missing_cost_count), 'missing-cost'),
  )}</div>`;
}

/**
 * The Finance tab body.
 *
 * Rendered inside the existing Reports finance card, above the existing warning
 * panel that the route already renders.
 */
export function renderFinanceReportSection(finance: FinanceReportResponse, f: FinanceReportFormatters): string {
  return `<div data-finance-report="true"><p class="page-message">Это операционная сводка мастерской, а не бухгалтерский отчёт. Налог и маржа показаны такими, какими они были сохранены при изготовлении партий, и не пересчитываются по текущей ставке.</p>${metricGrid(
    metric(LABELS.producedOrders, countValue(finance.produced_order_count), 'produced-order-count')
    + metric(LABELS.withSalePrice, countValue(finance.produced_orders_with_sale_price), 'produced-orders-with-sale-price'),
  )}${headlineMetrics(finance, f)}${coverageLines(finance)}${incompleteCoverageNotes(finance.warnings)}${sourceDataCompletenessSection(finance)}</div>`;
}

/**
 * The user-facing name of the report value a backend warning is about.
 *
 * A backend warning carries the DTO field it affects, which is a developer
 * name. Showing `known_tax` to a workshop owner explains nothing, so each field
 * the report warnings can reference is given the same wording the metric above
 * it uses, and an unrecognized field is shown as nothing at all rather than
 * leaking a raw name.
 */
const WARNING_FIELD_LABELS: Record<string, string> = {
  known_revenue: LABELS.knownRevenue,
  known_production_cost: LABELS.knownProductionCost,
  known_tax: LABELS.knownTax,
  known_margin: LABELS.knownMargin,
  known_margin_percent: LABELS.knownMarginPercent,
  total_known_cost: 'Известная себестоимость партий',
  produced_quantity_totals: 'Объёмы производства',
  orders_missing_recipe: 'Заказы без рецептуры',
};

/** The label for a warning's field, or `null` when there is nothing to show. */
export function reportWarningFieldLabel(field: string | null): string | null {
  return field === null ? null : WARNING_FIELD_LABELS[field] ?? null;
}

/**
 * The Overview tab finance summary.
 *
 * The same values, the same labels and the same unavailable/zero/negative rules
 * as the Finance tab — a shorter view of one DTO, never a second calculation.
 */
export function renderOverviewFinanceSummary(finance: FinanceReportResponse, f: FinanceReportFormatters): string {
  return `<div class="readiness-block" data-overview-finance-summary="true"><h3>Финансы</h3>${headlineMetrics(finance, f)}${coverageLines(finance)}${incompleteCoverageNotes(finance.warnings)}</div>`;
}
