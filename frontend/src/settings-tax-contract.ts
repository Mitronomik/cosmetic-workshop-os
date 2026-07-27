export type TaxRateSettingDto = {
  tax_rate_percent: string | null;
  is_configured: boolean;
  effective_at: string | null;
  message: string;
};

export type TaxRatePayload = { tax_rate_percent: string | null };

export type TaxRateInputCheck =
  | { ok: true; payload: string }
  | { ok: false; code: 'empty' | 'format' | 'precision' | 'range'; message: string };

export const TAX_RATE_EMPTY_MESSAGE = 'Введите ставку в процентах, например 6. Чтобы убрать ставку, используйте «Убрать ставку».';
export const TAX_RATE_FORMAT_MESSAGE = 'Ставку нужно указать числом, например 6 или 6,5.';
export const TAX_RATE_PRECISION_MESSAGE = 'Допустимо не больше двух знаков после запятой, например 6,5 или 6,05.';
export const TAX_RATE_RANGE_MESSAGE = 'Ставка должна быть от 0 до 100 процентов.';

const SHAPE = /^[0-9]+([.][0-9]+)?$/;

/** Validate user input and return the decimal string the backend expects. */
export function checkTaxRateInput(raw: string): TaxRateInputCheck {
  const text = raw.trim().replace(',', '.');
  if (!text) return { ok: false, code: 'empty', message: TAX_RATE_EMPTY_MESSAGE };
  if (!SHAPE.test(text)) return { ok: false, code: 'format', message: TAX_RATE_FORMAT_MESSAGE };
  const [, fraction = ''] = text.split('.');
  if (fraction.length > 2) return { ok: false, code: 'precision', message: TAX_RATE_PRECISION_MESSAGE };
  const numeric = Number(text);
  if (!Number.isFinite(numeric) || numeric > 100) return { ok: false, code: 'range', message: TAX_RATE_RANGE_MESSAGE };
  return { ok: true, payload: canonicalTaxRateText(text, fraction) };
}

/** Normalize an accepted input to the canonical two-decimal decimal string. */
function canonicalTaxRateText(text: string, fraction: string): string {
  const [whole = '0'] = text.split('.');
  return `${whole}.${(fraction + '00').slice(0, 2)}`;
}

export function isTaxRateSettingDto(value: unknown): value is TaxRateSettingDto {
  if (!value || typeof value !== 'object') return false;
  const dto = value as Record<string, unknown>;
  if (typeof dto.is_configured !== 'boolean' || typeof dto.message !== 'string') return false;
  const percentIsString = typeof dto.tax_rate_percent === 'string';
  const effectiveIsString = typeof dto.effective_at === 'string';
  if (dto.is_configured) return percentIsString && effectiveIsString;
  return dto.tax_rate_percent === null && dto.effective_at === null;
}

/** The editable text for a confirmed backend value; never invents a zero. */
export function taxRateInputValue(dto: TaxRateSettingDto | null): string {
  return dto?.is_configured && dto.tax_rate_percent ? dto.tax_rate_percent : '';
}

export function taxRatePercentLabel(dto: TaxRateSettingDto | null): string | null {
  return dto?.is_configured && dto.tax_rate_percent ? `${dto.tax_rate_percent}%` : null;
}

const MONTHS = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'];

/** Human-readable Russian rendering of the backend ISO-8601 UTC timestamp. */
export function formatTaxRateEffectiveAt(effectiveAt: string | null): string {
  if (!effectiveAt) return '';
  const match = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})Z$/.exec(effectiveAt);
  if (!match) return effectiveAt;
  const [, year, month, day, hour, minute] = match;
  const monthLabel = MONTHS[Number(month) - 1] ?? month;
  return `${Number(day)} ${monthLabel} ${year}, ${hour}:${minute} UTC`;
}
