/**
 * Russian presentation for the `Журнал действий` workspace.
 *
 * Durable contract: `docs/audit-log.md` § 10.2 and § 10.3.
 *
 * Every user-facing string for this route lives here, and every value that
 * describes *what happened* is rendered exactly as the backend sent it. This
 * module never translates a raw `action`, `entity_type` or `actor_type` code,
 * never reconstructs a summary, and never falls back to a raw code as visible
 * text — those codes appear only as `<option value>` and `data-*` attributes,
 * which is how the filters address them without ever showing them.
 */

import type { AuditLogFilterOption, AuditLogFilters, AuditLogItemDto } from './audit-log-contract.js';
import { auditLogAllRowsLoaded } from './audit-log-contract.js';
import type { AuditLogState } from './audit-log-workspace.js';

export const AUDIT_LOG_TITLE = 'Журнал действий';
export const AUDIT_LOG_LEAD =
  'Здесь собрана история важных действий с данными мастерской: что произошло, когда и с чем.';
export const AUDIT_LOG_READ_ONLY_NOTE = 'Журнал доступен только для чтения. Записи нельзя изменить или удалить, а просмотр журнала ничего не меняет в данных.';

export const AUDIT_LOG_LOADING = 'Загружаем журнал действий…';
export const AUDIT_LOG_REFRESHING = 'Обновляем журнал действий…';
export const AUDIT_LOG_REFRESHED = 'Журнал действий обновлён.';

export const AUDIT_LOG_EMPTY_TITLE = 'Журнал действий пока пуст';
export const AUDIT_LOG_EMPTY_TEXT =
  'Здесь появятся важные действия после работы с данными мастерской: добавление компонентов, рецептов, клиентов и заказов.';

export const AUDIT_LOG_FILTERED_EMPTY_TITLE = 'По выбранным фильтрам ничего не найдено';
export const AUDIT_LOG_FILTERED_EMPTY_TEXT = 'Измените условия или очистите фильтры, чтобы снова увидеть всю историю.';

export const AUDIT_LOG_INITIAL_FAILURE = 'Не удалось загрузить журнал действий. Попробуйте ещё раз.';
export const AUDIT_LOG_REFRESH_FAILURE = 'Не удалось обновить журнал. Показаны ранее загруженные данные.';
export const AUDIT_LOG_FILTER_FAILURE = 'Не удалось применить фильтры. Показаны ранее загруженные данные.';
export const AUDIT_LOG_LOAD_MORE_FAILURE = 'Не удалось загрузить следующие записи. Попробуйте ещё раз.';
export const AUDIT_LOG_INVALID_RESPONSE = 'Ответ журнала действий не соответствует ожидаемому формату.';

export const AUDIT_LOG_ALL_LOADED = 'Показаны все записи по выбранным условиям.';
export const AUDIT_LOG_LOAD_MORE_LABEL = 'Показать ещё';
export const AUDIT_LOG_REFRESH_LABEL = 'Обновить';
export const AUDIT_LOG_CLEAR_FILTERS_LABEL = 'Очистить фильтры';
export const AUDIT_LOG_APPLY_FILTERS_LABEL = 'Применить фильтры';
export const AUDIT_LOG_RETRY_LABEL = 'Попробовать ещё раз';
export const AUDIT_LOG_FILTERS_LEGEND = 'Отбор записей';
export const AUDIT_LOG_ANY_OPTION_LABEL = 'Любое';

const CREATED_FROM_ERROR_ID = 'audit-log-created-from-error';
const CREATED_BEFORE_ERROR_ID = 'audit-log-created-before-error';

export type AuditLogListState = 'loading' | 'rows' | 'empty' | 'filtered-empty' | 'error';

export type AuditLogRowView = {
  id: number;
  timestamp: string;
  actionLabel: string;
  entityLabel: string;
  displaySummary: string;
  actorLabel: string;
};

export type AuditLogPresentation = {
  listState: AuditLogListState;
  rows: AuditLogRowView[];
  filters: AuditLogFilters;
  fieldErrors: { createdFrom: string; createdBefore: string };
  actionOptions: AuditLogFilterOption[];
  entityOptions: AuditLogFilterOption[];
  actorOptions: AuditLogFilterOption[];
  busy: boolean;
  statusText: string;
  initialError: string;
  refreshError: string;
  loadMoreError: string;
  loadedCount: number;
  total: number;
  allLoaded: boolean;
  canRefresh: boolean;
  canLoadMore: boolean;
  loadMoreBusy: boolean;
  filtersActive: boolean;
};

/** Whether the user has narrowed the history at all. */
export function auditLogFiltersActive(filters: AuditLogFilters): boolean {
  return Object.values(filters).some((value) => value !== '');
}

/**
 * The user's local date and time for one backend UTC instant.
 *
 * The backend owns the canonical instant; the workshop user reads their own
 * wall clock, so the conversion happens once, here. An unreadable value degrades
 * to a dash rather than showing the raw string.
 */
export function formatAuditLogTimestamp(value: string): string {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return '—';
  return new Intl.DateTimeFormat('ru-RU', { dateStyle: 'short', timeStyle: 'short' }).format(parsed);
}

function listState(state: AuditLogState): AuditLogListState {
  if (state.status === 'error') return 'error';
  if (!state.loaded && state.activeKind !== null) return 'loading';
  if (state.items.length > 0) return 'rows';
  return auditLogFiltersActive(state.appliedFilters) ? 'filtered-empty' : 'empty';
}

function statusText(state: AuditLogState): string {
  if (state.activeKind === 'initial') return AUDIT_LOG_LOADING;
  if (state.activeKind === 'refresh' || state.activeKind === 'filter') return AUDIT_LOG_REFRESHING;
  return '';
}

/** The complete view model — no state transition and no request happens here. */
export function auditLogPresentation(state: AuditLogState): AuditLogPresentation {
  const busy = state.activeKind !== null;
  const allLoaded = auditLogAllRowsLoaded(state.items.length, state.total);
  return {
    listState: listState(state),
    rows: state.items.map((item) => auditLogRowView(item)),
    filters: state.filters,
    fieldErrors: state.fieldErrors,
    actionOptions: state.filterOptions.actions,
    entityOptions: state.filterOptions.entity_types,
    actorOptions: state.filterOptions.actor_types,
    busy,
    statusText: statusText(state),
    initialError: state.initialError,
    refreshError: state.refreshError,
    loadMoreError: state.loadMoreError,
    loadedCount: state.items.length,
    total: state.total,
    allLoaded,
    canRefresh: !busy,
    canLoadMore: !busy && !allLoaded && state.items.length > 0,
    loadMoreBusy: state.activeKind === 'load-more',
    filtersActive: auditLogFiltersActive(state.filters),
  };
}

/**
 * One row, carrying only what the user may read.
 *
 * `id` survives as a list key and DOM identity; it is deliberately absent from
 * every visible field, because it is an internal row identity rather than a
 * business value.
 */
export function auditLogRowView(item: AuditLogItemDto): AuditLogRowView {
  return {
    id: item.id,
    timestamp: formatAuditLogTimestamp(item.created_at),
    actionLabel: item.action_label,
    entityLabel: item.entity_label,
    displaySummary: item.display_summary,
    actorLabel: item.actor_label,
  };
}

export type AuditLogFeedbackRenderer = (tone: 'neutral' | 'success' | 'warning' | 'error', message: string) => string;

export function auditLogWorkspaceMarkup(view: AuditLogPresentation, renderFeedback: AuditLogFeedbackRenderer): string {
  return [
    `<div class="audit-log-layout" data-page="audit-log" tabindex="-1" data-focus-key="c3-audit-log-content">`,
    headerMarkup(view),
    filtersMarkup(view),
    view.refreshError ? renderFeedback('warning', view.refreshError) : '',
    bodyMarkup(view, renderFeedback),
    `</div>`,
  ].join('');
}

function headerMarkup(view: AuditLogPresentation): string {
  const counter = view.listState === 'rows'
    ? `<p class="muted-text" data-audit-log-counter>Показано ${view.loadedCount} из ${view.total}</p>`
    : '';
  return [
    `<section class="card data-card">`,
    `<div class="section-heading"><div>`,
    `<p class="card-kicker">Данные и настройки</p>`,
    `<h2>${AUDIT_LOG_TITLE}</h2>`,
    `<p>${escapeHtml(AUDIT_LOG_LEAD)}</p>`,
    `<p class="next-step">${escapeHtml(AUDIT_LOG_READ_ONLY_NOTE)}</p>`,
    counter,
    `</div>`,
    `<button class="primary-action" type="button" data-action="refresh-audit-log" data-focus-key="c3-audit-log-refresh" ${view.canRefresh ? '' : 'disabled'}>${view.busy ? 'Обновляем…' : AUDIT_LOG_REFRESH_LABEL}</button>`,
    `</div>`,
    `<p class="muted-text" role="status" data-audit-log-status>${escapeHtml(view.statusText)}</p>`,
    `</section>`,
  ].join('');
}

function filtersMarkup(view: AuditLogPresentation): string {
  const disabled = view.busy ? 'disabled' : '';
  return [
    `<section class="card data-card" data-audit-log-filters>`,
    `<form class="ingredient-form audit-log-filters" data-form="audit-log-filters" aria-busy="${view.busy ? 'true' : 'false'}">`,
    `<fieldset><legend>${AUDIT_LOG_FILTERS_LEGEND}</legend>`,
    dateFieldMarkup('audit-log-created-from', 'Период с', 'created-from', view.filters.createdFrom, view.fieldErrors.createdFrom, CREATED_FROM_ERROR_ID, disabled),
    dateFieldMarkup('audit-log-created-before', 'Период по', 'created-before', view.filters.createdBefore, view.fieldErrors.createdBefore, CREATED_BEFORE_ERROR_ID, disabled),
    selectMarkup('audit-log-action', 'Действие', 'action', view.filters.action, view.actionOptions, disabled),
    selectMarkup('audit-log-entity-type', 'Раздел данных', 'entity-type', view.filters.entityType, view.entityOptions, disabled),
    selectMarkup('audit-log-actor-type', 'Кто выполнил', 'actor-type', view.filters.actorType, view.actorOptions, disabled),
    `</fieldset>`,
    `<div class="actions">`,
    `<button class="primary-action" type="submit" data-action="apply-audit-log-filters" ${disabled}>${AUDIT_LOG_APPLY_FILTERS_LABEL}</button>`,
    `<button class="secondary-action" type="button" data-action="clear-audit-log-filters" ${view.filtersActive && !view.busy ? '' : 'disabled'}>${AUDIT_LOG_CLEAR_FILTERS_LABEL}</button>`,
    `</div>`,
    `</form></section>`,
  ].join('');
}

function dateFieldMarkup(id: string, label: string, filter: string, value: string, error: string, errorId: string, disabled: string): string {
  const errorMarkup = error
    ? `<p class="field-error" id="${errorId}" data-audit-log-field-error="${filter}" role="alert">${escapeHtml(error)}</p>`
    : `<p class="field-error" id="${errorId}" data-audit-log-field-error="${filter}" hidden></p>`;
  return [
    `<div class="audit-log-field">`,
    `<label for="${id}">${escapeHtml(label)}</label>`,
    `<input id="${id}" type="datetime-local" data-audit-log-filter="${filter}" value="${escapeHtml(value)}" aria-describedby="${errorId}" aria-invalid="${error ? 'true' : 'false'}" ${disabled} />`,
    errorMarkup,
    `</div>`,
  ].join('');
}

/**
 * One filter select.
 *
 * The raw persisted code is the `value`; only `label` is ever displayed, which
 * is what keeps a technical identifier off the screen while still letting the
 * request carry the exact code the backend expects.
 */
function selectMarkup(id: string, label: string, filter: string, selected: string, options: AuditLogFilterOption[], disabled: string): string {
  const choices = [`<option value="">${AUDIT_LOG_ANY_OPTION_LABEL}</option>`]
    .concat(options.map((option) => `<option value="${escapeHtml(option.value)}" ${option.value === selected ? 'selected' : ''}>${escapeHtml(option.label)}</option>`))
    .join('');
  return [
    `<div class="audit-log-field">`,
    `<label for="${id}">${escapeHtml(label)}</label>`,
    `<select id="${id}" data-audit-log-filter="${filter}" ${disabled}>${choices}</select>`,
    `</div>`,
  ].join('');
}

function bodyMarkup(view: AuditLogPresentation, renderFeedback: AuditLogFeedbackRenderer): string {
  if (view.listState === 'error') {
    return [
      `<section class="card empty-card" data-state="audit-log-error">`,
      renderFeedback('error', view.initialError || AUDIT_LOG_INITIAL_FAILURE),
      `<div class="actions"><button class="primary-action" type="button" data-action="retry-audit-log">${AUDIT_LOG_RETRY_LABEL}</button></div>`,
      `</section>`,
    ].join('');
  }
  if (view.listState === 'loading') {
    return `<section class="card empty-card" data-state="audit-log-loading" aria-busy="true"><p>${escapeHtml(AUDIT_LOG_LOADING)}</p></section>`;
  }
  if (view.listState === 'empty') {
    return `<section class="card empty-card" data-state="audit-log-empty"><h2>${escapeHtml(AUDIT_LOG_EMPTY_TITLE)}</h2><p>${escapeHtml(AUDIT_LOG_EMPTY_TEXT)}</p></section>`;
  }
  if (view.listState === 'filtered-empty') {
    return [
      `<section class="card empty-card" data-state="audit-log-filtered-empty">`,
      `<h2>${escapeHtml(AUDIT_LOG_FILTERED_EMPTY_TITLE)}</h2><p>${escapeHtml(AUDIT_LOG_FILTERED_EMPTY_TEXT)}</p>`,
      `<div class="actions"><button class="secondary-action" type="button" data-action="clear-audit-log-filters">${AUDIT_LOG_CLEAR_FILTERS_LABEL}</button></div>`,
      `</section>`,
    ].join('');
  }
  return [
    `<section class="card data-card">`,
    `<ul class="audit-log-list" data-audit-log-list aria-busy="${view.busy ? 'true' : 'false'}">`,
    view.rows.map(rowMarkup).join(''),
    `</ul>`,
    view.loadMoreError ? renderFeedback('error', view.loadMoreError) : '',
    paginationMarkup(view),
    `</section>`,
  ].join('');
}

function rowMarkup(row: AuditLogRowView): string {
  return [
    `<li class="audit-log-row" data-audit-log-row data-audit-log-id="${row.id}">`,
    `<p class="audit-log-row__when"><time data-audit-log-time>${escapeHtml(row.timestamp)}</time></p>`,
    `<p class="audit-log-row__summary" data-audit-log-summary>${escapeHtml(row.displaySummary)}</p>`,
    `<p class="audit-log-row__meta">`,
    `<span class="pill info" data-audit-log-action>${escapeHtml(row.actionLabel)}</span>`,
    `<span class="pill" data-audit-log-entity>${escapeHtml(row.entityLabel)}</span>`,
    `<span class="pill" data-audit-log-actor>${escapeHtml(row.actorLabel)}</span>`,
    `</p>`,
    `</li>`,
  ].join('');
}

function paginationMarkup(view: AuditLogPresentation): string {
  if (view.allLoaded) return `<p class="next-step" data-state="audit-log-all-loaded">${escapeHtml(AUDIT_LOG_ALL_LOADED)}</p>`;
  return [
    `<div class="actions">`,
    `<button class="secondary-action" type="button" data-action="load-more-audit-log" ${view.canLoadMore ? '' : 'disabled'}>${view.loadMoreBusy ? 'Загружаем…' : AUDIT_LOG_LOAD_MORE_LABEL}</button>`,
    `</div>`,
  ].join('');
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>'"]/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[char] ?? char));
}
