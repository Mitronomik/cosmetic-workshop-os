import type { RestoreControlSnapshot } from './restore-control-contract.js';
import type { RestoreControlView } from './restore-control-runtime.js';

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char] ?? char));
}

function stateCopy(snapshot: RestoreControlSnapshot | null): { title: string; body: string; tone: 'neutral' | 'success' | 'warning' | 'error' } {
  if (!snapshot) return { title: 'Подключаем безопасное восстановление', body: 'Проверяем локальную сессию приложения.', tone: 'neutral' };
  if (snapshot.state === 'selecting') return { title: 'Выберите резервную копию', body: 'Открыто системное окно macOS. Выберите файл резервной копии или отмените выбор.', tone: 'neutral' };
  if (snapshot.state === 'validating') return { title: 'Проверяем резервную копию', body: 'Приложение проверяет файл без изменения рабочих данных.', tone: 'neutral' };
  if (snapshot.state === 'accepted') return { title: 'Копия проверена', body: 'Резервная копия подходит для будущего восстановления. Рабочие данные не изменены, восстановление ещё не запускалось.', tone: 'success' };
  if (snapshot.state === 'rejected') return { title: 'Эта копия не подходит', body: snapshot.message || 'Выберите другую резервную копию и повторите проверку.', tone: 'warning' };
  if (snapshot.state === 'cancelled') return { title: 'Проверка остановлена', body: snapshot.message || 'Данные мастерской не изменились. Можно выбрать файл снова.', tone: 'neutral' };
  if (snapshot.state === 'technical_failure') return { title: 'Не удалось проверить копию', body: 'Данные мастерской не изменились. Попробуйте выбрать файл ещё раз. Если проблема повторяется, перезапустите приложение.', tone: 'error' };
  return { title: 'Готово к выбору файла', body: 'На этом шаге данные мастерской не изменяются. Сначала выберите файл и дождитесь проверки.', tone: 'neutral' };
}

function feedback(tone: 'neutral' | 'success' | 'warning' | 'error', title: string, body: string): string {
  const className = tone === 'neutral' ? 'info' : tone;
  return `<section class="card data-card restore-status-card" aria-live="polite"><div class="section-heading"><div><p class="card-kicker">Статус проверки</p><h2>${escapeHtml(title)}</h2></div><span class="pill ${className}">${tone === 'success' ? 'Проверено' : tone === 'warning' ? 'Нужен другой файл' : tone === 'error' ? 'Не удалось' : 'Без изменения данных'}</span></div><p>${escapeHtml(body)}</p></section>`;
}

export function restoreControlMarkup(view: RestoreControlView): string {
  const snapshot = view.snapshot;
  const current = stateCopy(snapshot);
  const busy = snapshot?.state === 'selecting' || snapshot?.state === 'validating';
  const pending = view.pending;
  const canMutate = view.hasSession && view.protocolSafe && view.availability === 'ready' && !pending;
  const selectLabel = snapshot?.state === 'accepted' ? 'Выбрать другую копию' : snapshot?.state === 'rejected' || snapshot?.state === 'cancelled' || snapshot?.state === 'technical_failure' ? 'Выбрать файл снова' : 'Выбрать и проверить файл';

  const unavailable = !view.hasSession || view.availability === 'protocol_error';
  const networkOnly = view.hasSession && view.availability === 'network_error';
  const filename = snapshot?.filename ? `<dl class="metadata-list"><div><dt>Выбранный файл</dt><dd>${escapeHtml(snapshot.filename)}</dd></div><div><dt>Проверка</dt><dd>${snapshot.state === 'accepted' ? 'Совместимость подтверждена' : 'Результат показан выше'}</dd></div></dl>` : '';
  const notice = view.notice ? `<section class="card ${unavailable ? 'error-card' : 'data-card'}"><h2>${unavailable ? 'Восстановление недоступно' : pending ? 'Последнее действие требует повторения' : 'Связь с локальной сессией прервана'}</h2><p>${escapeHtml(view.notice)}</p>${networkOnly && !pending ? '<div class="actions"><button class="secondary-action" type="button" data-restore-action="refresh">Проверить соединение</button></div>' : ''}${pending ? '<div class="actions"><button class="primary-action" type="button" data-restore-action="retry">Повторить последнее действие</button></div>' : ''}</section>` : '';

  const actionMarkup = unavailable
    ? ''
    : pending
      ? '<p class="next-step">Новое действие отключено, пока не разрешён результат предыдущей команды.</p>'
      : busy
        ? `<div class="actions"><button class="secondary-action" type="button" data-restore-action="cancel" ${canMutate ? '' : 'disabled'}>Отменить проверку</button></div>`
        : `<div class="actions"><button class="primary-action" type="button" data-restore-action="select" ${canMutate ? '' : 'disabled'}>${escapeHtml(selectLabel)}</button></div>`;

  return `<div class="page-grid backup-page restore-control-page" data-restore-control-page tabindex="-1" data-restore-focus>
    <section class="card data-card dashboard-hero">
      <div><p class="card-kicker">Безопасная проверка</p><h2>Восстановление из резервной копии</h2><p>Выберите локальный файл через системное окно macOS. Приложение проверит копию, но не будет менять текущую базу данных.</p><p class="next-step"><strong>Важно:</strong> на этом экране восстановление ещё не запускается. После успешной проверки рабочие данные останутся без изменений.</p></div>
      <div class="actions"><button class="secondary-action" type="button" data-restore-action="back">Вернуться к резервным копиям</button></div>
    </section>
    ${notice}
    ${feedback(current.tone, current.title, current.body)}
    ${filename ? `<section class="card data-card"><p class="card-kicker">Проверенный источник</p><h2>Сведения о выбранной копии</h2>${filename}<p class="next-step">Полный путь к файлу остаётся внутри локального приложения и не показывается в браузере.</p></section>` : ''}
    <section class="card data-card"><p class="card-kicker">Следующий шаг</p><h2>${busy ? 'Дождитесь окончания проверки' : snapshot?.state === 'accepted' ? 'Проверка завершена' : 'Выберите резервную копию'}</h2>${actionMarkup}<p class="next-step">Выбор и проверка не создают складских движений, не меняют рецепты, клиентов, заказы или производство.</p></section>
    <section class="card data-card"><p class="card-kicker">Граница текущего этапа</p><h2>Что здесь происходит</h2><ul class="checklist compact-list"><li>Файл выбирается системным окном macOS, а не загружается браузером.</li><li>Браузер получает только безопасный результат проверки и имя файла.</li><li>Рабочая база данных на этом этапе не заменяется.</li><li>Кнопки запуска окончательного восстановления на этом экране нет.</li></ul></section>
  </div>`;
}

export function restoreEntryButtonMarkup(): string {
  return '<button class="secondary-action" type="button" data-restore-action="open">Восстановить из резервной копии</button>';
}
