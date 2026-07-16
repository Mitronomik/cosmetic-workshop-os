export type FormValidationIssue = {
  field: string | null;
  message: string;
  code: string | null;
};

export type FormValidationState = {
  fieldErrors: Record<string, string[]>;
  formErrors: string[];
};

type FieldLabels = Record<string, string>;

const TRANSPORT_PREFIXES = new Set(['body', 'query', 'path']);
const DEFAULT_FORM_ERROR = 'Не удалось сохранить данные. Проверьте поля и попробуйте ещё раз.';

export const emptyFormValidationState = (): FormValidationState => ({ fieldErrors: {}, formErrors: [] });

export function hasFormValidationErrors(state: FormValidationState): boolean {
  return state.formErrors.length > 0 || Object.values(state.fieldErrors).some((messages) => messages.length > 0);
}

export function clearFieldValidation(state: FormValidationState, field: string): FormValidationState {
  if (!state.fieldErrors[field]) return state;
  const nextFieldErrors = { ...state.fieldErrors };
  delete nextFieldErrors[field];
  return { ...state, fieldErrors: nextFieldErrors };
}

export function normalizeBackendValidation(payload: unknown, fieldLabels: FieldLabels, fallbackMessage = DEFAULT_FORM_ERROR): FormValidationState {
  try {
    const issues = extractIssues(payload);
    const state = emptyFormValidationState();
    if (issues.length === 0) {
      const message = messageFromDetail(payload) ?? fallbackMessage;
      return { ...state, formErrors: [sanitizeMessage(message, fallbackMessage)] };
    }
    for (const issue of issues) {
      const message = sanitizeMessage(issue.message, fallbackMessage);
      const field = resolveKnownField(issue.field, fieldLabels);
      if (field) {
        const label = fieldLabels[field];
        const friendly = message.includes(label) ? message : `${label}: ${message}`;
        state.fieldErrors[field] = [...(state.fieldErrors[field] ?? []), friendly];
      } else {
        state.formErrors.push(message);
      }
    }
    if (!hasFormValidationErrors(state)) state.formErrors.push(fallbackMessage);
    return state;
  } catch {
    return { fieldErrors: {}, formErrors: [fallbackMessage] };
  }
}

function extractIssues(payload: unknown): FormValidationIssue[] {
  const result: FormValidationIssue[] = [];
  const root = isRecord(payload) ? payload : null;
  const detail = root?.detail;
  if (Array.isArray(detail)) {
    for (const item of detail) pushIssue(result, item);
  }
  if (isRecord(detail)) {
    if (Array.isArray(detail.issues)) for (const item of detail.issues) pushIssue(result, item);
    else pushIssue(result, detail);
  }
  if (root && Array.isArray(root.issues)) for (const item of root.issues) pushIssue(result, item);
  if (result.length === 0 && root) pushIssue(result, root);
  return result;
}

function pushIssue(result: FormValidationIssue[], item: unknown) {
  if (!isRecord(item)) return;
  const rawMessage = firstString(item.message, item.msg, item.detail);
  if (!rawMessage) return;
  result.push({
    field: fieldFromUnknown(item.field) ?? fieldFromUnknown(item.loc),
    message: rawMessage,
    code: firstString(item.code, item.type),
  });
}

function messageFromDetail(payload: unknown): string | null {
  if (typeof payload === 'string') return payload;
  if (!isRecord(payload)) return null;
  if (typeof payload.detail === 'string') return payload.detail;
  if (isRecord(payload.detail)) return firstString(payload.detail.message, payload.detail.msg);
  return firstString(payload.message, payload.msg);
}

function fieldFromUnknown(value: unknown): string | null {
  if (typeof value === 'string') return value;
  if (!Array.isArray(value)) return null;
  const parts = value.filter((part): part is string | number => typeof part === 'string' || typeof part === 'number').map(String);
  while (parts.length > 0 && TRANSPORT_PREFIXES.has(parts[0])) parts.shift();
  return parts.length ? parts.join('.') : null;
}

function resolveKnownField(field: string | null, labels: FieldLabels): string | null {
  if (!field) return null;
  const parts = field.split('.').filter(Boolean);
  if (parts.length === 0) return null;
  while (parts.length > 0 && TRANSPORT_PREFIXES.has(parts[0])) parts.shift();
  const exact = parts.join('.');
  if (Object.prototype.hasOwnProperty.call(labels, exact)) return exact;
  if (parts.length !== 1) return null;
  const candidate = parts[0];
  return Object.prototype.hasOwnProperty.call(labels, candidate) ? candidate : null;
}

function sanitizeMessage(value: unknown, fallback: string): string {
  const message = typeof value === 'string' ? value : fallback;
  const trimmed = message.replace(/[\u0000-\u001F\u007F]/g, ' ').replace(/\s+/g, ' ').trim();
  if (!trimmed) return fallback;
  if (/traceback|stack trace|sqlite|database|pydantic|validationerror|exception|\/api\//i.test(trimmed)) return fallback;
  return trimmed.slice(0, 280);
}

function firstString(...values: unknown[]): string | null {
  for (const value of values) if (typeof value === 'string' && value.trim()) return value;
  return null;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value);
}
