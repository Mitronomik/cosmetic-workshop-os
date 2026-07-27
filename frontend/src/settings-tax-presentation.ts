import { formatTaxRateEffectiveAt, taxRatePercentLabel } from './settings-tax-contract.js';
import type { TaxRateFeedbackTone, TaxRateState } from './settings-tax-feedback.js';

export type TaxRateStatusKey = 'loading' | 'configured' | 'unconfigured' | 'unavailable';
export type TaxRateFeedbackItem = { tone: Exclude<TaxRateFeedbackTone, 'none'>; message: string };

export type TaxRatePresentation = {
  status: TaxRateStatusKey;
  valueLabel: string | null;
  stateText: string;
  effectiveAtText: string;
  draft: string;
  fieldError: string;
  feedbackItems: TaxRateFeedbackItem[];
  busy: boolean;
  mutationBusy: boolean;
  clearConfirmVisible: boolean;
  controlsDisabled: boolean;
  reconciliationRequired: boolean;
  canSave: boolean;
  canCancel: boolean;
  canClear: boolean;
  canRefresh: boolean;
};

export const TAX_RATE_SECTION_TITLE = 'Налоговая ставка для расчётов';
export const TAX_RATE_HELPER_TEXT = 'Используется для внутренней оценки налога с цены продажи. Это не налоговая отчётность.';
export const TAX_RATE_HISTORY_NOTE = 'Изменение ставки не пересчитывает уже подтверждённые производства, отчёты и созданные документы.';
export const TAX_RATE_MISSING_TEXT = 'Ставка пока не настроена. Налог и маржа будут показаны как недоступные.';
export const TAX_RATE_UNAVAILABLE_TEXT = 'Значение ставки сейчас недоступно. Обновите раздел, чтобы увидеть подтверждённое значение.';
export const TAX_RATE_LOADING_TEXT = 'Загружаем текущее значение ставки…';
export const TAX_RATE_CLEAR_WARNING = 'Убрать ставку? Пока ставка не настроена, налог и маржа будут показаны как недоступные. Уже подтверждённые производства и отчёты не изменятся.';

const ERROR_ID = 'settings-tax-rate-error';
const HINT_ID = 'settings-tax-rate-hint';

export function settingsTaxRatePresentation(state: TaxRateState): TaxRatePresentation {
  const mutationBusy = state.mutation !== null;
  const busy = mutationBusy || state.read !== null;
  const editable = state.status === 'ready' && state.confirmed !== null && !mutationBusy;
  // An unreconciled value is shown but is not confirmed enough to mutate from.
  const blocked = state.reconciliationRequired || state.detachedMutationPending;
  const configured = Boolean(state.confirmed?.is_configured);
  return {
    status: statusKey(state),
    valueLabel: taxRatePercentLabel(state.confirmed),
    stateText: stateText(state),
    effectiveAtText: configured ? formatTaxRateEffectiveAt(state.confirmed?.effective_at ?? null) : '',
    draft: state.draft,
    fieldError: state.fieldError,
    feedbackItems: feedbackItems(state),
    busy,
    mutationBusy,
    clearConfirmVisible: state.clearConfirmVisible,
    controlsDisabled: !editable,
    reconciliationRequired: state.reconciliationRequired,
    canSave: editable && !blocked,
    canCancel: editable,
    canClear: editable && configured && !blocked,
    canRefresh: !busy && !state.detachedMutationPending,
  };
}

function statusKey(state: TaxRateState): TaxRateStatusKey {
  if (state.confirmed === null) return state.status === 'error' ? 'unavailable' : 'loading';
  return state.confirmed.is_configured ? 'configured' : 'unconfigured';
}

function stateText(state: TaxRateState): string {
  const key = statusKey(state);
  if (key === 'loading') return TAX_RATE_LOADING_TEXT;
  if (key === 'unavailable') return TAX_RATE_UNAVAILABLE_TEXT;
  if (key === 'unconfigured') return TAX_RATE_MISSING_TEXT;
  return `Текущая ставка: ${taxRatePercentLabel(state.confirmed)}`;
}

function feedbackItems(state: TaxRateState): TaxRateFeedbackItem[] {
  const items: TaxRateFeedbackItem[] = [];
  if (state.feedback.neutral) items.push({ tone: 'neutral', message: state.feedback.neutral });
  if (state.feedback.success) items.push({ tone: 'success', message: state.feedback.success });
  if (state.feedback.warning) items.push({ tone: 'warning', message: state.feedback.warning });
  if (state.feedback.error) items.push({ tone: 'error', message: state.feedback.error });
  return items;
}

export type TaxRateFeedbackRenderer = (tone: TaxRateFeedbackItem['tone'], message: string) => string;

export function settingsTaxRateCardMarkup(view: TaxRatePresentation, renderFeedback: TaxRateFeedbackRenderer): string {
  const disabled = view.controlsDisabled ? 'disabled' : '';
  return [
    `<section class="card data-card settings-card settings-tax-card" data-tax-rate-section aria-labelledby="settings-tax-rate-heading">`,
    `<h2 id="settings-tax-rate-heading">${TAX_RATE_SECTION_TITLE}</h2>`,
    `<p id="${HINT_ID}">${TAX_RATE_HELPER_TEXT}</p>`,
    `<p class="next-step">${TAX_RATE_HISTORY_NOTE}</p>`,
    stateMarkup(view),
    `<div data-tax-rate-feedback>${view.feedbackItems.map((item) => renderFeedback(item.tone, item.message)).join('')}</div>`,
    formMarkup(view, disabled),
    clearConfirmMarkup(view, renderFeedback),
    `</section>`,
  ].join('');
}

function stateMarkup(view: TaxRatePresentation): string {
  const value = view.valueLabel ? `<strong data-tax-rate-value>${escapeHtml(view.valueLabel)}</strong>` : '';
  const effective = view.effectiveAtText
    ? `<p class="muted-text" data-tax-rate-effective-at>Действует с ${escapeHtml(view.effectiveAtText)}</p>`
    : '';
  return `<div class="settings-tax-state" data-tax-rate-status="${view.status}" role="status">${value}<p>${escapeHtml(view.stateText)}</p>${effective}</div>`;
}

function formMarkup(view: TaxRatePresentation, disabled: string): string {
  const error = view.fieldError
    ? `<p class="field-error" id="${ERROR_ID}" data-tax-rate-field-error>${escapeHtml(view.fieldError)}</p>`
    : `<p class="field-error" id="${ERROR_ID}" data-tax-rate-field-error hidden></p>`;
  return [
    `<form class="ingredient-form settings-tax-form" data-form="settings-tax-rate" aria-busy="${view.mutationBusy ? 'true' : 'false'}">`,
    `<div class="settings-tax-field"><label for="settings-tax-rate-input">Ставка в процентах</label>`,
    `<span class="settings-tax-input-wrap"><input id="settings-tax-rate-input" data-tax-rate-input type="text" inputmode="decimal" autocomplete="off" value="${escapeHtml(view.draft)}" placeholder="Например, 6" aria-describedby="${HINT_ID} ${ERROR_ID}" aria-invalid="${view.fieldError ? 'true' : 'false'}" ${disabled} />`,
    `<span class="settings-tax-unit" aria-hidden="true">%</span></span></div>`,
    error,
    `<div class="actions">`,
    `<button class="primary-action" type="submit" data-tax-rate-save ${view.canSave ? '' : 'disabled'}>${view.mutationBusy ? 'Сохраняем…' : 'Сохранить ставку'}</button>`,
    `<button class="secondary-action" type="button" data-tax-rate-cancel ${view.canCancel ? '' : 'disabled'}>Отменить изменения</button>`,
    `<button class="secondary-action" type="button" data-tax-rate-clear ${view.canClear ? '' : 'disabled'}>Убрать ставку</button>`,
    `<button class="secondary-action compact" type="button" data-tax-rate-refresh ${view.canRefresh ? '' : 'disabled'}>Обновить значение</button>`,
    `</div></form>`,
  ].join('');
}

function clearConfirmMarkup(view: TaxRatePresentation, renderFeedback: TaxRateFeedbackRenderer): string {
  if (!view.clearConfirmVisible) return `<div data-tax-rate-clear-confirm hidden></div>`;
  return [
    `<div class="confirm-panel" data-tax-rate-clear-confirm>`,
    renderFeedback('warning', TAX_RATE_CLEAR_WARNING),
    `<div class="actions">`,
    `<button class="primary-action" type="button" data-tax-rate-clear-accept ${view.mutationBusy ? 'disabled' : ''}>Да, убрать ставку</button>`,
    `<button class="secondary-action" type="button" data-tax-rate-clear-cancel ${view.mutationBusy ? 'disabled' : ''}>Оставить ставку</button>`,
    `</div></div>`,
  ].join('');
}

function escapeHtml(value: string): string {
  return value.replace(/[&<>'"]/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[char] ?? char));
}
