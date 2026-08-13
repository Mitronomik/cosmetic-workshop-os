export type UpdateStatusState = 'not_required' | 'completed' | 'attention_required';
export type UpdateStatusDto = {
  state: UpdateStatusState;
  to_app_version: string | null;
  updated_at: string | null;
  message: string;
  next_action: string;
};

type SettingsStatusEnvelope = { update_status: UpdateStatusDto };
type MountRoot = {
  querySelector: <T = Element>(selector: string) => T | null;
};
type Anchor = { insertAdjacentHTML: (position: 'afterend', html: string) => void };
type StatusCard = { outerHTML: string; isConnected?: boolean };
type FetchStatus = () => Promise<unknown>;

let cachedStatus: UpdateStatusDto | null | undefined;
let statusRequest: Promise<UpdateStatusDto | null> | null = null;

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }[char] ?? char));
}

function stateLabel(state: UpdateStatusState): string {
  if (state === 'completed') return 'Обновление завершено';
  if (state === 'attention_required') return 'Нужно внимание';
  return 'Обновление не требовалось';
}

function tone(state: UpdateStatusState): 'neutral' | 'success' | 'warning' {
  if (state === 'completed') return 'success';
  if (state === 'attention_required') return 'warning';
  return 'neutral';
}

export function isUpdateStatusDto(value: unknown): value is UpdateStatusDto {
  if (!value || typeof value !== 'object') return false;
  const item = value as Record<string, unknown>;
  return (item.state === 'not_required' || item.state === 'completed' || item.state === 'attention_required')
    && (item.to_app_version === null || typeof item.to_app_version === 'string')
    && (item.updated_at === null || typeof item.updated_at === 'string')
    && typeof item.message === 'string'
    && typeof item.next_action === 'string';
}

export function updateStatusFromSettingsEnvelope(value: unknown): UpdateStatusDto | null {
  if (!value || typeof value !== 'object' || !('update_status' in value)) return null;
  const candidate = (value as SettingsStatusEnvelope).update_status;
  return isUpdateStatusDto(candidate) ? candidate : null;
}

export function settingsUpdateStatusCardMarkup(status: UpdateStatusDto | null, unavailable = false): string {
  if (!status) {
    return `<section class="card data-card settings-card" data-update-status-card><p class="card-kicker">Безопасность данных</p><h2>Обновление данных</h2><p>${unavailable ? 'Не удалось показать состояние обновления. Другие настройки продолжают работать независимо.' : 'Проверяем состояние последнего обновления…'}</p></section>`;
  }
  const version = status.to_app_version ? `<p><strong>Версия:</strong> ${escapeHtml(status.to_app_version)}</p>` : '';
  return `<section class="card data-card settings-card" data-update-status-card><p class="card-kicker">Безопасность данных</p><h2>Обновление данных</h2><div class="feedback-message feedback-message--${tone(status.state)}"><strong class="feedback-message__label">${stateLabel(status.state)}</strong><div class="feedback-message__body"><p>${escapeHtml(status.message)}</p></div></div>${version}<p><strong>Что делать:</strong> ${escapeHtml(status.next_action)}</p></section>`;
}

async function defaultFetchStatus(): Promise<unknown> {
  const response = await fetch('/api/settings/status');
  if (!response.ok) throw new Error('settings update status unavailable');
  return response.json();
}

export function resetUpdateStatusCacheForTests(): void {
  cachedStatus = undefined;
  statusRequest = null;
}

export function mountSettingsUpdateStatus(root: MountRoot, fetchStatus: FetchStatus = defaultFetchStatus): boolean {
  if (root.querySelector<StatusCard>('[data-update-status-card]')) return true;
  const anchor = root.querySelector<Anchor>('[data-tax-rate-section]');
  if (!anchor) return false;

  const initial = cachedStatus === undefined
    ? settingsUpdateStatusCardMarkup(null)
    : settingsUpdateStatusCardMarkup(cachedStatus, cachedStatus === null);
  anchor.insertAdjacentHTML('afterend', initial);
  if (cachedStatus !== undefined) return true;

  if (statusRequest === null) {
    statusRequest = fetchStatus()
      .then((value) => updateStatusFromSettingsEnvelope(value))
      .catch(() => null)
      .then((status) => { cachedStatus = status; return status; });
  }
  const mounted = root.querySelector<StatusCard>('[data-update-status-card]');
  statusRequest.then((status) => {
    if (mounted && mounted.isConnected !== false) mounted.outerHTML = settingsUpdateStatusCardMarkup(status, status === null);
  });
  return true;
}
