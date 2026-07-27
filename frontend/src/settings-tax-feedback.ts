import {
  checkTaxRateInput,
  isTaxRateSettingDto,
  taxRateInputValue,
  type TaxRateSettingDto,
} from './settings-tax-contract.js';

export type TaxRateReadKind = 'initial' | 'refresh' | 'mutation-refresh';
export type TaxRateMutationKind = 'save' | 'clear';
export type TaxRateFeedbackTone = 'none' | 'neutral' | 'success' | 'warning' | 'error';
export type TaxRateAnnouncement = 'none' | 'polite' | 'assertive';

export type TaxRateOwner = { requestId: number; routeGeneration: number };
export type TaxRateReadOwner = TaxRateOwner & { kind: TaxRateReadKind };
export type TaxRateMutationOwner = TaxRateOwner & { kind: TaxRateMutationKind };
export type TaxRateStart<TOwner> =
  | { accepted: true; owner: TOwner; payload?: string | null }
  | { accepted: false; reason: TaxRateRejection };
export type TaxRateRejection = 'read-active' | 'mutation-active' | 'not-ready' | 'invalid-input' | 'not-confirmed' | 'nothing-to-clear';
export type TaxRateSettled = { accepted: boolean; announcement: TaxRateAnnouncement; message: string; knownSuccess?: boolean };

export type TaxRateFeedback = { tone: TaxRateFeedbackTone; neutral: string; success: string; warning: string; error: string };
export type TaxRateState = {
  routeGeneration: number;
  status: 'idle' | 'loading' | 'ready' | 'error';
  confirmed: TaxRateSettingDto | null;
  draft: string;
  fieldError: string;
  read: TaxRateReadOwner | null;
  mutation: TaxRateMutationOwner | null;
  clearConfirmVisible: boolean;
  feedback: TaxRateFeedback;
};

export const TAX_RATE_LOADING_MESSAGE = 'Загружаем налоговую ставку…';
export const TAX_RATE_REFRESHING_MESSAGE = 'Обновляем налоговую ставку…';
export const TAX_RATE_SAVING_MESSAGE = 'Сохраняем налоговую ставку…';
export const TAX_RATE_CLEARING_MESSAGE = 'Убираем налоговую ставку…';
export const TAX_RATE_INITIAL_ERROR = 'Не удалось загрузить налоговую ставку. Рецепты, склад и заказы не изменялись.';
export const TAX_RATE_REFRESH_WARNING = 'Не удалось обновить налоговую ставку. Показано последнее подтверждённое значение.';
export const TAX_RATE_SAVE_ERROR = 'Не удалось сохранить налоговую ставку. Предыдущее значение осталось без изменений.';
export const TAX_RATE_CLEAR_ERROR = 'Не удалось убрать налоговую ставку. Предыдущее значение осталось без изменений.';
export const TAX_RATE_INVALID_RESPONSE = 'Локальное приложение вернуло неожиданный ответ. Обновите налоговую ставку и проверьте значение.';
export const TAX_RATE_CANCEL_MESSAGE = 'Изменения отменены. Восстановлено последнее сохранённое значение.';
export const TAX_RATE_REFRESH_SUCCESS = 'Налоговая ставка обновлена.';

const idleFeedback = (): TaxRateFeedback => ({ tone: 'none', neutral: '', success: '', warning: '', error: '' });
const ignored = (): TaxRateSettled => ({ accepted: false, announcement: 'none', message: '' });

export class SettingsTaxRateFeedbackLifecycle {
  readonly state: TaxRateState;
  private nextRequestId = 0;

  constructor() {
    this.state = { routeGeneration: 0, status: 'idle', confirmed: null, draft: '', fieldError: '', read: null, mutation: null, clearConfirmVisible: false, feedback: idleFeedback() };
  }

  enterRoute() {
    this.state.routeGeneration += 1;
    this.state.read = null;
    this.state.clearConfirmVisible = false;
    this.state.feedback = idleFeedback();
  }

  leaveRoute() {
    this.state.routeGeneration += 1;
    this.state.read = null;
    this.state.mutation = null;
    this.state.clearConfirmVisible = false;
    this.state.feedback = idleFeedback();
  }

  startRead(kind: TaxRateReadKind): TaxRateStart<TaxRateReadOwner> {
    if (this.state.read) return { accepted: false, reason: 'read-active' };
    if (this.state.mutation) return { accepted: false, reason: 'mutation-active' };
    const owner: TaxRateReadOwner = { requestId: ++this.nextRequestId, routeGeneration: this.state.routeGeneration, kind };
    this.state.read = owner;
    if (kind === 'initial' && !this.state.confirmed) this.state.status = 'loading';
    // A mutation-refresh reconciles a already-confirmed success, so it must not
    // add a busy message next to that success.
    if (kind !== 'mutation-refresh') {
      this.state.feedback = { ...this.state.feedback, tone: 'neutral', neutral: kind === 'initial' ? TAX_RATE_LOADING_MESSAGE : TAX_RATE_REFRESHING_MESSAGE, error: '' };
    }
    return { accepted: true, owner };
  }

  finishReadSuccess(owner: TaxRateReadOwner, value: unknown): TaxRateSettled {
    if (!this.owns(this.state.read, owner)) return ignored();
    this.state.read = null;
    if (!isTaxRateSettingDto(value)) return this.presentInvalidResponse();
    const keptSuccess = owner.kind === 'mutation-refresh' ? this.state.feedback.success : '';
    this.applyConfirmed(value);
    const refreshed = owner.kind === 'refresh';
    this.state.feedback = { ...idleFeedback(), tone: refreshed ? 'success' : keptSuccess ? 'success' : 'none', success: refreshed ? TAX_RATE_REFRESH_SUCCESS : keptSuccess };
    return refreshed ? { accepted: true, announcement: 'polite', message: TAX_RATE_REFRESH_SUCCESS } : { accepted: true, announcement: 'none', message: '' };
  }

  finishReadFailure(owner: TaxRateReadOwner): TaxRateSettled {
    if (!this.owns(this.state.read, owner)) return ignored();
    this.state.read = null;
    if (!this.state.confirmed) {
      this.state.status = 'error';
      this.state.feedback = { ...idleFeedback(), tone: 'error', error: TAX_RATE_INITIAL_ERROR };
      return { accepted: true, announcement: 'assertive', message: TAX_RATE_INITIAL_ERROR };
    }
    this.state.feedback = { ...this.state.feedback, tone: 'warning', neutral: '', warning: TAX_RATE_REFRESH_WARNING, error: '' };
    return { accepted: true, announcement: 'polite', message: TAX_RATE_REFRESH_WARNING };
  }

  setDraft(text: string) {
    this.state.draft = text;
    this.state.fieldError = '';
    this.state.feedback = { ...idleFeedback(), tone: this.state.feedback.warning ? 'warning' : 'none', warning: this.state.feedback.warning };
  }

  cancelEdit(): TaxRateSettled {
    if (!this.canEdit()) return ignored();
    this.state.draft = taxRateInputValue(this.state.confirmed);
    this.state.fieldError = '';
    this.state.clearConfirmVisible = false;
    this.state.feedback = { ...idleFeedback(), tone: 'neutral', neutral: TAX_RATE_CANCEL_MESSAGE };
    return { accepted: true, announcement: 'polite', message: TAX_RATE_CANCEL_MESSAGE };
  }

  requestClearConfirmation(): TaxRateStart<never> {
    if (!this.canEdit()) return { accepted: false, reason: this.state.mutation ? 'mutation-active' : 'not-ready' };
    if (!this.state.confirmed?.is_configured) return { accepted: false, reason: 'nothing-to-clear' };
    this.state.clearConfirmVisible = true;
    this.state.fieldError = '';
    return { accepted: true, owner: undefined as never };
  }

  cancelClearConfirmation() {
    this.state.clearConfirmVisible = false;
  }

  startSave(): TaxRateStart<TaxRateMutationOwner> {
    const blocked = this.mutationBlocked();
    if (blocked) return { accepted: false, reason: blocked };
    const checked = checkTaxRateInput(this.state.draft);
    if (!checked.ok) {
      this.state.fieldError = checked.message;
      this.state.feedback = { ...idleFeedback(), tone: 'error', error: checked.message };
      return { accepted: false, reason: 'invalid-input' };
    }
    return { accepted: true, owner: this.beginMutation('save', TAX_RATE_SAVING_MESSAGE), payload: checked.payload };
  }

  startClear(): TaxRateStart<TaxRateMutationOwner> {
    const blocked = this.mutationBlocked();
    if (blocked) return { accepted: false, reason: blocked };
    if (!this.state.clearConfirmVisible) return { accepted: false, reason: 'not-confirmed' };
    return { accepted: true, owner: this.beginMutation('clear', TAX_RATE_CLEARING_MESSAGE), payload: null };
  }

  finishMutationSuccess(owner: TaxRateMutationOwner, value: unknown): TaxRateSettled {
    if (!this.owns(this.state.mutation, owner)) return ignored();
    this.state.mutation = null;
    if (!isTaxRateSettingDto(value)) return this.presentInvalidResponse();
    this.applyConfirmed(value);
    this.state.clearConfirmVisible = false;
    this.state.feedback = { ...idleFeedback(), tone: 'success', success: value.message };
    return { accepted: true, announcement: 'polite', message: value.message, knownSuccess: true };
  }

  finishMutationFailure(owner: TaxRateMutationOwner, fieldError = ''): TaxRateSettled {
    if (!this.owns(this.state.mutation, owner)) return ignored();
    const kind = this.state.mutation?.kind;
    this.state.mutation = null;
    const message = kind === 'clear' ? TAX_RATE_CLEAR_ERROR : TAX_RATE_SAVE_ERROR;
    this.state.fieldError = kind === 'save' ? fieldError : '';
    this.state.feedback = { ...idleFeedback(), tone: 'error', error: fieldError || message };
    return { accepted: true, announcement: 'assertive', message: fieldError || message };
  }

  canEdit() {
    return this.state.status === 'ready' && this.state.confirmed !== null && this.state.mutation === null;
  }

  private beginMutation(kind: TaxRateMutationKind, busyMessage: string): TaxRateMutationOwner {
    const owner: TaxRateMutationOwner = { requestId: ++this.nextRequestId, routeGeneration: this.state.routeGeneration, kind };
    this.state.mutation = owner;
    this.state.fieldError = '';
    this.state.feedback = { ...idleFeedback(), tone: 'neutral', neutral: busyMessage };
    return owner;
  }

  private mutationBlocked(): TaxRateRejection | null {
    if (this.state.mutation) return 'mutation-active';
    if (this.state.read) return 'read-active';
    if (this.state.status !== 'ready' || this.state.confirmed === null) return 'not-ready';
    return null;
  }

  private applyConfirmed(dto: TaxRateSettingDto) {
    this.state.status = 'ready';
    this.state.confirmed = dto;
    this.state.draft = taxRateInputValue(dto);
    this.state.fieldError = '';
  }

  private presentInvalidResponse(): TaxRateSettled {
    this.state.clearConfirmVisible = false;
    if (!this.state.confirmed) this.state.status = 'error';
    this.state.feedback = { ...idleFeedback(), tone: 'error', error: TAX_RATE_INVALID_RESPONSE };
    return { accepted: true, announcement: 'assertive', message: TAX_RATE_INVALID_RESPONSE };
  }

  private owns<T extends TaxRateOwner>(current: T | null, owner: TaxRateOwner) {
    return Boolean(current && current.requestId === owner.requestId && current.routeGeneration === owner.routeGeneration && owner.routeGeneration === this.state.routeGeneration);
  }
}
