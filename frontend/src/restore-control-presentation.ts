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

function isFinalExecutionState(snapshot: RestoreControlSnapshot | null): boolean {
  return snapshot?.state === 'restore_completed'
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
  if (snapshot.state === 'restore_completed') return { title: 'Восстановление завершено', body: snapshot.message || 'Локальное приложение подтвердило успешное завершение восстановления и готовность обычной работы.', tone: 'success' };
  if (snapshot.state === 'restore_failed') return { title: 'Восстановление не завершено', body: snapshot.message || 'Локальное приложение сообщило, что восстановление не завершилось успешно. Обычная работа снова доступна, но этот статус сам по себе не означает, что данные остались прежними или были автоматически возвращены.', tone: 'warning' };
  if (snapshot.state === 'restore_blocked') return { title: 'Обычная работа временно недоступна', body: snapshot.message || 'Локальное приложение не подтвердило безопасное продолжение обычной работы в этом запуске. Требуется перезапуск.', tone: 'error' };
  return { title: 'Готово к выбору файла', body: 'Сначала выберите резервную копию и дождитесь проверки.', tone: 'neutral' };
}

function feedback(
  tone: 'neutral' | 'success' | 'warning' | 'error',
  title: string,
  body: string,
  executionState: boolean,
  unknownState: boolean,
): string {
  const className = tone === 'neutral' ? 'info' : tone;
  const kicker = executionState || unknownState ? 'Статус восстановления' : 'Статус проверки';
  const pill = unknownState
    ? 'Статус неизвестен'
    : executionState
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

function executionBoundaryMarkup(
  snapshot: RestoreControlSnapshot | null,
  resultUnknown: boolean,
  executionState: boolean,
): string {
  if (resultUnknown) {
    return '<section class="card data-card"><p class="card-kicker">Безопасный следующий шаг</p><h2>Состояние восстановления сейчас неизвестно</h2><ul class="checklist compact-list"><li>Потеря безопасной локальной сессии не подтверждает ни успешное завершение, ни ошибку восстановления.</li><li>Этот экран не может подтвердить текущее состояние данных, поэтому не запускайте новое восстановление.</li><li>Перезапустите «Мастерскую косметолога» обычным способом и следуйте сообщению после запуска.</li></ul></section>';
  }
  if (snapshot?.state === 'restore_completed') {
    return '<section class="card data-card"><p class="card-kicker">Что подтверждено</p><h2>Обычная работа снова доступна</h2><ul class="checklist compact-list"><li>Локальное приложение подтвердило успешное завершение восстановления.</li><li>Обычный рабочий режим приложения снова готов к использованию.</li><li>Служебные пути, внутренние записи и технические стадии на странице не показываются.</li></ul></section>';
  }
  if (snapshot?.state === 'restore_failed') {
    return '<section class="card data-card"><p class="card-kicker">Что известно</p><h2>Обычная работа снова доступна</h2><ul class="checklist compact-list"><li>Локальное приложение завершило попытку восстановления без подтверждённого успеха.</li><li>Этот итог не означает автоматически, что рабочие данные остались прежними или были возвращены к предыдущему состоянию.</li><li>Перед новой попыткой сначала проверьте нужные данные и выбранную резервную копию; не повторяйте восстановление вслепую.</li></ul></section>';
  }
  if (snapshot?.state === 'restore_blocked') {
    return '<section class="card error-card"><p class="card-kicker">Что делать дальше</p><h2>Перезапустите «Мастерскую косметолога»</h2><ul class="checklist compact-list"><li>Обычная работа в текущем запуске не подтверждена как безопасная.</li><li>Закройте приложение и откройте его снова обычным способом.</li><li>Если после перезапуска блокировка повторяется, воспользуйтесь разделом «Помощь» и не запускайте восстановление повторно вслепую.</li></ul></section>';
  }
  if (executionState) {
    return '<section class="card data-card"><p class="card-kicker">Безопасная граница</p><h2>Что видит браузер</h2><ul class="checklist compact-list"><li>Браузер получает только безопасное состояние и сообщение локального приложения.</li><li>Полный путь к резервной копии, служебные файлы и внутренняя запись восстановления не передаются на страницу.</li><li>Во время восстановления нельзя запустить второе восстановление или отменить уже начатое действие.</li></ul></section>';
  }
  return '<section class="card data-card"><p class="card-kicker">Безопасная граница</p><h2>Что здесь происходит</h2><ul class="checklist compact-list"><li>Файл выбирается системным окном macOS, а не загружается браузером.</li><li>Браузер получает только безопасный результат проверки и имя файла.</li><li>До отдельного подтверждения рабочая база данных не заменяется.</li><li>Полный путь к файлу остаётся внутри локального приложения.</li></ul></section>';
}

export function restoreControlMarkup(view: RestoreControlView, options: RestoreControlPresentationOptions = {}): string {
  const snapshot = view.snapshot;
  const pending = view.pending;
  const executePending = pending?.action === 'execute';
  const restoring = snapshot?.state === 'restoring';
  const finalExecutionState = isFinalExecutionState(snapshot);
  const authoritativeFinalState = finalExecutionState
    && view.hasSession
    && view.availability !== 'unavailable'
    && view.availability !== 'initializing';
  const unavailable = view.availability === 'unavailable'
    || view.availability === 'protocol_error'
    || (!view.hasSession && view.availability !== 'initializing');
  const resultUnknownAfterExecute = !authoritativeFinalState && (executePending || restoring) && (
    view.availability === 'network_error'
    || unavailable
    || !view.protocolSafe
  );
  const resultUnknown = !authoritativeFinalState && (resultUnknownAfterExecute || unavailable);
  const current = resultUnknown
    ? {
        title: resultUnknownAfterExecute ? 'Итог восстановления пока неизвестен' : 'Состояние восстановления сейчас неизвестно',
        body: resultUnknownAfterExecute
          ? 'Связь с локальным приложением прервана после запуска восстановления. Это не подтверждает ни успешное завершение, ни ошибку. Не запускайте новое восстановление, пока итог не станет известен.'
          : 'Локальная сессия восстановления недоступна, поэтому этот экран не может подтвердить текущий результат восстановления или состояние данных. Перезапустите «Мастерскую косметолога» обычным способом и следуйте сообщению после запуска.',
        tone: 'neutral' as const,
      }
    : stateCopy(snapshot, executePending);
  const executionState = isExecutionState(snapshot) || executePending || resultUnknown;
  const selectingBusy = snapshot?.state === 'selecting' || snapshot?.state === 'validating';
  const canMutate = view.hasSession && view.protocolSafe && view.availability === 'ready' && !pending;
  const selectLabel = snapshot?.state === 'accepted'
    ? 'Выбрать другую копию'
    : snapshot?.state === 'rejected' || snapshot?.state === 'cancelled' || snapshot?.state === 'technical_failure'
      ? 'Выбрать файл снова'
      : 'Выбрать и проверить файл';

  const networkOnly = view.hasSession && view.availability === 'network_error';
  const displayNotice = authoritativeFinalState
    ? ''
    : resultUnknownAfterExecute
      ? 'Связь с локальной сессией прервана после запуска восстановления. Итог пока неизвестен. Если доступно повторение предыдущей команды, оно повторит только тот же защищённый запрос; иначе перезапустите «Мастерскую косметолога» обычным способом и следуйте сообщению после запуска.'
      : unavailable
        ? view.notice || 'Локальная сессия восстановления недоступна. Перезапустите «Мастерскую косметолога» обычным способом и следуйте сообщению после запуска.'
        : view.notice;
  const filename = snapshot?.filename ? `<dl class="metadata-list"><div><dt>Выбранный файл</dt><dd>${escapeHtml(snapshot.filename)}</dd></div><div><dt>Проверка</dt><dd>${snapshot.state === 'accepted' || executionState ? 'Совместимость подтверждена' : 'Результат показан выше'}</dd></div></dl>` : '';
  const canRetryPending = networkOnly && Boolean(pending) && view.protocolSafe;
  const retryAction = canRetryPending
    ? `<div class="actions"><button class="secondary-action" type="button" data-restore-action="retry">${executePending ? 'Повторить только предыдущую команду' : 'Повторить последнее действие'}</button></div>`
    : '';
  const refreshAction = networkOnly && !pending
    ? '<div class="actions"><button class="secondary-action" type="button" data-restore-action="refresh">Проверить соединение</button></div>'
    : '';
  const notice = displayNotice
    ? `<section class="card ${unavailable ? 'error-card' : 'data-card'}"><h2>${resultUnknownAfterExecute ? 'Связь с приложением прервана' : unavailable ? 'Восстановление недоступно' : pending ? 'Последнее действие требует повторения' : 'Связь с локальной сессией прервана'}</h2><p>${escapeHtml(displayNotice)}</p>${refreshAction}${retryAction}</section>`
    : '';

  let actionMarkup = '';
  let nextTitle = 'Выберите резервную копию';
  let nextCopy = 'Выбор и проверка не меняют рецепты, клиентов, заказы, склад или производство.';

  if (authoritativeFinalState) {
    if (snapshot?.state === 'restore_completed') {
      nextTitle = 'Можно продолжать работу';
      nextCopy = 'Восстановление завершено успешно, и обычный режим приложения снова доступен. Можно вернуться к резервным копиям и продолжить работу.';
    } else if (snapshot?.state === 'restore_failed') {
      nextTitle = 'Сначала проверьте итог и данные';
      nextCopy = 'Обычная работа снова доступна. Не делайте вывод, что данные точно остались прежними или были автоматически возвращены: ориентируйтесь на итоговое сообщение выше. Не запускайте новое восстановление вслепую.';
    } else {
      nextTitle = 'Перезапустите приложение';
      nextCopy = 'Обычная работа в этом запуске не подтверждена как безопасная. Закройте «Мастерскую косметолога» и откройте её снова. Если блокировка повторится, воспользуйтесь разделом «Помощь».';
    }
  } else if (resultUnknownAfterExecute) {
    nextTitle = 'Не запускайте новое восстановление';
    nextCopy = 'Итог текущего запуска неизвестен. Попробуйте восстановить связь. Если сессия больше недоступна, перезапустите «Мастерскую косметолога» обычным способом и следуйте сообщению после запуска.';
  } else if (unavailable) {
    nextTitle = 'Перезапустите приложение';
    nextCopy = 'Состояние восстановления сейчас неизвестно. Этот экран не может подтвердить результат или состояние данных. Перезапустите «Мастерскую косметолога» обычным способом и следуйте сообщению после запуска.';
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
  } else {
    actionMarkup = `<div class="actions"><button class="primary-action" type="button" data-restore-action="select" ${canMutate ? '' : 'disabled'}>${escapeHtml(selectLabel)}</button></div>`;
  }

  let heroBody = 'Выберите локальную резервную копию через системное окно macOS. Приложение сначала проверит файл, а перед фактической заменой данных отдельно попросит подтверждение.';
  let heroImportant = 'Проверка файла безопасна и сама по себе не изменяет рабочие данные.';
  if (resultUnknownAfterExecute) {
    heroBody = 'Запуск восстановления уже мог быть принят локальным приложением, но браузер пока не знает итог.';
    heroImportant = 'Не запускайте новое восстановление и не делайте вывод об успехе или ошибке, пока безопасный итог не станет известен.';
  } else if (restoring) {
    heroBody = 'Восстановление уже запущено локальным приложением. Дождитесь итогового состояния.';
    heroImportant = 'На этом этапе нельзя отменить восстановление или выбрать другой файл.';
  } else if (snapshot?.state === 'restore_completed') {
    heroBody = 'Локальное приложение подтвердило успешное завершение восстановления и готовность обычной работы.';
    heroImportant = 'Ниже показан безопасный итог и следующий шаг без технических деталей.';
  } else if (snapshot?.state === 'restore_failed') {
    heroBody = 'Попытка восстановления завершилась без подтверждённого успеха, но обычная работа снова доступна.';
    heroImportant = 'Не делайте вывод о состоянии данных сверх итогового сообщения локального приложения.';
  } else if (snapshot?.state === 'restore_blocked') {
    heroBody = 'Локальное приложение не подтвердило безопасное продолжение обычной работы в этом запуске.';
    heroImportant = 'Не возвращайтесь к обычной работе и не запускайте восстановление повторно вслепую — сначала перезапустите приложение.';
  } else if (unavailable) {
    heroBody = 'Локальная сессия восстановления сейчас недоступна.';
    heroImportant = 'Этот экран не может подтвердить результат восстановления или состояние данных. Перезапустите «Мастерскую косметолога» обычным способом и следуйте сообщению после запуска.';
  }
  const finalBackAllowed = authoritativeFinalState
    && (snapshot?.state === 'restore_completed' || snapshot?.state === 'restore_failed');
  const heroBackAllowed = finalBackAllowed || (
    !finalExecutionState
    && !resultUnknown
    && !unavailable
    && !executePending
    && snapshot?.state !== 'restoring'
  );
  const heroActions = heroBackAllowed
    ? '<div class="actions"><button class="secondary-action" type="button" data-restore-action="back">Вернуться к резервным копиям</button></div>'
    : '';

  const boundaryMarkup = executionBoundaryMarkup(snapshot, resultUnknown, executionState);

  return `<div class="page-grid backup-page restore-control-page" data-restore-control-page tabindex="-1" data-restore-focus>
    <section class="card data-card dashboard-hero">
      <div><p class="card-kicker">Восстановление данных</p><h2>Восстановление из резервной копии</h2><p>${escapeHtml(heroBody)}</p><p class="next-step"><strong>Важно:</strong> ${escapeHtml(heroImportant)}</p></div>
      ${heroActions}
    </section>
    ${notice}
    ${feedback(current.tone, current.title, current.body, executionState, resultUnknown)}
    ${filename ? `<section class="card data-card"><p class="card-kicker">Проверенный источник</p><h2>Сведения о выбранной копии</h2>${filename}<p class="next-step">Полный путь к файлу остаётся внутри локального приложения и не показывается в браузере.</p></section>` : ''}
    <section class="card data-card"><p class="card-kicker">Следующий шаг</p><h2>${escapeHtml(nextTitle)}</h2>${actionMarkup}<p class="next-step">${escapeHtml(nextCopy)}</p></section>
    ${boundaryMarkup}
    ${confirmationMarkup(view, Boolean(options.confirmationOpen))}
  </div>`;
}

export function restoreEntryButtonMarkup(): string {
  return '<button class="secondary-action" type="button" data-restore-action="open">Восстановить из резервной копии</button>';
}
