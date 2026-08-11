import type { RestoreControlSnapshot } from './restore-control-contract.js';
import type { RestoreControlView } from './restore-control-runtime.js';

export type RestoreControlPresentationOptions = {
  confirmationOpen?: boolean;
};

function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char] ?? char));
}

function isExecutionState(snapshot: RestoreControlSnapshot | null): boolean {
  return snapshot?.state === 'restoring'
    || snapshot?.state === 'restore_completed'
    || snapshot?.state === 'restore_failed'
    || snapshot?.state === 'restore_blocked';
}

function stateCopy(
  snapshot: RestoreControlSnapshot | null,
  executePending: boolean,
): { title: string; body: string; tone: 'neutral' | 'success' | 'warning' | 'error' } {
  if (!snapshot) return { title: 'Подключаем безопасное восстановление', body: 'Проверяем локальную сессию приложения.', tone: 'neutral' };
  if (snapshot.state === 'selecting') return { title: 'Выберите резервную копию', body: 'Открыто системное окно macOS. Выберите файл резервной копии или отмените выбор.', tone: 'neutral' };
  if (snapshot.state === 'validating') return { title: 'Проверяем резервную копию', body: 'Приложение проверяет файл без изменения рабочих данных.', tone: 'neutral' };
  if (snapshot.state === 'accepted' && executePending) return { title: 'Запрос на восстановление отправлен', body: 'Ответ от приложения ещё не получен. Восстановление уже могло начаться; не запускайте новое действие и дождитесь результата или безопасно повторите предыдущую команду.', tone: 'neutral' };
  if (snapshot.state === 'accepted') return { title: 'Копия проверена', body: 'Резервная копия подходит для восстановления. Рабочие данные не изменены, восстановление ещё не запускалось.', tone: 'success' };
  if (snapshot.state === 'rejected') return { title: 'Эта копия не подходит', body: snapshot.message || 'Выберите другую резервную копию и повторите проверку.', tone: 'warning' };
  if (snapshot.state === 'cancelled') return { title: 'Проверка остановлена', body: snapshot.message || 'Данные мастерской не изменились. Можно выбрать файл снова.', tone: 'neutral' };
  if (snapshot.state === 'technical_failure') return { title: 'Не удалось проверить копию', body: 'Данные мастерской не изменились. Попробуйте выбрать файл ещё раз. Если проблема повторяется, перезапустите приложение.', tone: 'error' };
  if (snapshot.state === 'restoring') return { title: 'Восстанавливаем данные мастерской', body: snapshot.message || 'Приложение выполняет восстановление. Не закрывайте приложение и дождитесь результата.', tone: 'neutral' };
  if (snapshot.state === 'restore_completed') return { title: 'Восстановление завершено', body: snapshot.message || 'Данные восстановлены, приложение снова готово к работе.', tone: 'success' };
  if (snapshot.state === 'restore_failed') return { title: 'Восстановление не завершено', body: snapshot.message || 'Приложение не смогло завершить восстановление. Следуйте безопасной подсказке и не повторяйте действие вслепую.', tone: 'warning' };
  if (snapshot.state === 'restore_blocked') return { title: 'Нужно перезапустить приложение', body: snapshot.message || 'Продолжить обычную работу сейчас небезопасно. Перезапустите приложение и следуйте подсказке на экране.', tone: 'error' };
  return { title: 'Готово к выбору файла', body: 'Сначала выберите резервную копию и дождитесь проверки.', tone: 'neutral' };
}

function feedback(
  tone: 'neutral' | 'success' | 'warning' | 'error',
  title: string,
  body: string,
  executionState: boolean,
): string {
  const className = tone === 'neutral' ? 'info' : tone;
  const kicker = executionState ? 'Статус восстановления' : 'Статус проверки';
  const pill = executionState
    ? tone === 'success' ? 'Завершено' : tone === 'warning' ? 'Не завершено' : tone === 'error' ? 'Нужен перезапуск' : 'В процессе'
    : tone === 'success' ? 'Проверено' : tone === 'warning' ? 'Нужен другой файл' : tone === 'error' ? 'Не удалось' : 'Без изменения данных';
  return `<section class="card data-card restore-status-card" aria-live="polite"><div class="section-heading"><div><p class="card-kicker">${kicker}</p><h2>${escapeHtml(title)}</h2></div><span class="pill ${className}">${pill}</span></div><p>${escapeHtml(body)}</p></section>`;
}

function confirmationMarkup(view: RestoreControlView, open: boolean): string {
  const snapshot = view.snapshot;
  if (!open || snapshot?.state !== 'accepted' || view.pending || view.availability !== 'ready' || !view.hasSession || !view.protocolSafe) return '';
  const filename = snapshot.filename ? `<strong>${escapeHtml(snapshot.filename)}</strong>` : '<strong>выбранной резервной копии</strong>';
  return `<dialog class="card data-card restore-confirmation-dialog" data-restore-confirmation aria-labelledby="restore-confirmation-title" aria-describedby="restore-confirmation-body" style="width:min(680px,calc(100vw - 32px));max-width:680px;">
    <p class="card-kicker">Подтверждение восстановления</p>
    <h2 id="restore-confirmation-title">Заменить текущие данные мастерской?</h2>
    <div id="restore-confirmation-body">
      <p>Данные мастерской будут заменены данными из ${filename}.</p>
      <p>Во время восстановления приложение может быть временно недоступно. Перед заменой существующий механизм восстановления автоматически создаст защитную копию текущей базы данных.</p>
      <p class="next-step"><strong>Важно:</strong> после запуска восстановление нельзя отменить с этого экрана. Дождитесь итогового сообщения приложения.</p>
    </div>
    <div class="actions">
      <button class="secondary-action" type="button" data-restore-action="confirm-dismiss" autofocus>Вернуться</button>
      <button class="danger-action" type="button" data-restore-action="confirm-execute">Восстановить данные</button>
    </div>
  </dialog>`;
}

export function restoreControlMarkup(view: RestoreControlView, options: RestoreControlPresentationOptions = {}): string {
  const snapshot = view.snapshot;
  const pending = view.pending;
  const executePending = pending?.action === 'execute';
  const current = stateCopy(snapshot, executePending);
  const executionState = isExecutionState(snapshot) || executePending;
  const selectingBusy = snapshot?.state === 'selecting' || snapshot?.state === 'validating';
  const restoring = snapshot?.state === 'restoring';
  const finalExecutionState = snapshot?.state === 'restore_completed' || snapshot?.state === 'restore_failed' || snapshot?.state === 'restore_blocked';
  const canMutate = view.hasSession && view.protocolSafe && view.availability === 'ready' && !pending;
  const selectLabel = snapshot?.state === 'accepted'
    ? 'Выбрать другую копию'
    : snapshot?.state === 'rejected' || snapshot?.state === 'cancelled' || snapshot?.state === 'technical_failure'
      ? 'Выбрать файл снова'
      : 'Выбрать и проверить файл';

  const unavailable = !view.hasSession || view.availability === 'protocol_error';
  const networkOnly = view.hasSession && view.availability === 'network_error';
  const displayNotice = !view.hasSession && view.availability === 'network_error'
    ? 'Не удалось завершить безопасное подключение к восстановлению. Одноразовая сессия могла быть использована, поэтому перезапустите «Мастерскую косметолога» и откройте восстановление снова.'
    : view.notice;
  const filename = snapshot?.filename ? `<dl class="metadata-list"><div><dt>Выбранный файл</dt><dd>${escapeHtml(snapshot.filename)}</dd></div><div><dt>Проверка</dt><dd>${snapshot.state === 'accepted' || executionState ? 'Совместимость подтверждена' : 'Результат показан выше'}</dd></div></dl>` : '';
  const notice = displayNotice ? `<section class="card ${unavailable ? 'error-card' : 'data-card'}"><h2>${unavailable ? 'Восстановление недоступно' : pending ? 'Последнее действие требует повторения' : 'Связь с локальной сессией прервана'}</h2><p>${escapeHtml(displayNotice)}</p>${networkOnly && !pending ? '<div class="actions"><button class="secondary-action" type="button" data-restore-action="refresh">Проверить соединение</button></div>' : ''}${pending ? '<div class="actions"><button class="primary-action" type="button" data-restore-action="retry">Повторить последнее действие</button></div>' : ''}</section>` : '';

  let actionMarkup = '';
  let nextTitle = 'Выберите резервную копию';
  let nextCopy = 'Выбор и проверка не меняют рецепты, клиентов, заказы, склад или производство.';

  if (unavailable) {
    actionMarkup = '';
  } else if (pending) {
    actionMarkup = '<p class="next-step">Новое действие отключено, пока не разрешён результат предыдущей команды.</p>';
    if (executePending) {
      nextTitle = 'Дождитесь результата запуска восстановления';
      nextCopy = 'Ответ на запуск восстановления ещё не получен. Восстановление уже могло начаться; не запускайте новое действие. Если ответ потерян, безопасно повторите только предыдущую команду.';
    } else {
      nextTitle = 'Дождитесь результата команды';
    }
  } else if (selectingBusy) {
    actionMarkup = `<div class="actions"><button class="secondary-action" type="button" data-restore-action="cancel" ${canMutate ? '' : 'disabled'}>Отменить проверку</button></div>`;
    nextTitle = 'Дождитесь окончания проверки';
  } else if (snapshot?.state === 'accepted') {
    actionMarkup = `<div class="actions"><button class="secondary-action" type="button" data-restore-action="select" ${canMutate ? '' : 'disabled'}>Выбрать другую копию</button><button class="danger-action" type="button" data-restore-action="confirm-open" ${canMutate ? '' : 'disabled'}>Восстановить данные</button></div>`;
    nextTitle = 'Копия готова к восстановлению';
    nextCopy = 'Запуск возможен только после отдельного подтверждения. До подтверждения текущие данные мастерской не меняются.';
  } else if (restoring) {
    actionMarkup = '<p class="next-step"><strong>Восстановление уже запущено.</strong> На этом этапе нельзя выбрать другой файл или отменить восстановление. Дождитесь итогового сообщения приложения.</p>';
    nextTitle = 'Дождитесь завершения';
    nextCopy = 'Приложение продолжает проверять состояние восстановления через локальный канал управления. Процент выполнения не показывается, потому что безопасного точного прогресса нет.';
  } else if (finalExecutionState) {
    nextTitle = snapshot?.state === 'restore_completed' ? 'Можно продолжать работу' : 'Следуйте сообщению приложения';
    nextCopy = 'Этот экран показывает только безопасный итог локального механизма восстановления. Подробные технические стадии и внутренние пути не отображаются.';
  } else {
    actionMarkup = `<div class="actions"><button class="primary-action" type="button" data-restore-action="select" ${canMutate ? '' : 'disabled'}>${escapeHtml(selectLabel)}</button></div>`;
  }

  const boundaryMarkup = executionState
    ? '<section class="card data-card"><p class="card-kicker">Безопасная граница</p><h2>Что видит браузер</h2><ul class="checklist compact-list"><li>Браузер получает только безопасное состояние и сообщение локального приложения.</li><li>Полный путь к резервной копии, служебные файлы и внутренняя запись восстановления не передаются на страницу.</li><li>Во время восстановления нельзя запустить второе восстановление или отменить уже начатое действие.</li></ul></section>'
    : '<section class="card data-card"><p class="card-kicker">Безопасная граница</p><h2>Что здесь происходит</h2><ul class="checklist compact-list"><li>Файл выбирается системным окном macOS, а не загружается браузером.</li><li>Браузер получает только безопасный результат проверки и имя файла.</li><li>До отдельного подтверждения рабочая база данных не заменяется.</li><li>Полный путь к файлу остаётся внутри локального приложения.</li></ul></section>';

  return `<div class="page-grid backup-page restore-control-page" data-restore-control-page tabindex="-1" data-restore-focus>
    <section class="card data-card dashboard-hero">
      <div><p class="card-kicker">Восстановление данных</p><h2>Восстановление из резервной копии</h2><p>Выберите локальную резервную копию через системное окно macOS. Приложение сначала проверит файл, а перед фактической заменой данных отдельно попросит подтверждение.</p><p class="next-step"><strong>Важно:</strong> проверка файла безопасна и сама по себе не изменяет рабочие данные.</p></div>
      <div class="actions"><button class="secondary-action" type="button" data-restore-action="back">Вернуться к резервным копиям</button></div>
    </section>
    ${notice}
    ${feedback(current.tone, current.title, current.body, executionState)}
    ${filename ? `<section class="card data-card"><p class="card-kicker">Проверенный источник</p><h2>Сведения о выбранной копии</h2>${filename}<p class="next-step">Полный путь к файлу остаётся внутри локального приложения и не показывается в браузере.</p></section>` : ''}
    <section class="card data-card"><p class="card-kicker">Следующий шаг</p><h2>${escapeHtml(nextTitle)}</h2>${actionMarkup}<p class="next-step">${escapeHtml(nextCopy)}</p></section>
    ${boundaryMarkup}
    ${confirmationMarkup(view, Boolean(options.confirmationOpen))}
  </div>`;
}

export function restoreEntryButtonMarkup(): string {
  return '<button class="secondary-action" type="button" data-restore-action="open">Восстановить из резервной копии</button>';
}
