/** User-facing Russian copy for the tax-setting section, kept out of the state machine. */
import type { TaxRateReadKind } from './settings-tax-feedback.js';
import { TAX_RATE_RECONCILING_MESSAGE } from './settings-tax-reconciliation.js';

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

export function busyMessage(kind: TaxRateReadKind): string {
  if (kind === 'initial') return TAX_RATE_LOADING_MESSAGE;
  if (kind === 'reconciliation') return TAX_RATE_RECONCILING_MESSAGE;
  return TAX_RATE_REFRESHING_MESSAGE;
}
