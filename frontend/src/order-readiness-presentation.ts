export type ProductionReadinessStatus = 'ready' | 'blocked' | 'warning';
export type ProductionReadinessIssueSeverity = 'blocking' | 'warning' | 'info';
export type ProductionReadinessIssue = { code: string; severity: ProductionReadinessIssueSeverity; message: string; field: string | null; entity_type: string | null; entity_id: number | null };
export type ProductionReadinessLotSelection = { lot_id: number; lot_code: string | null; selected_quantity: string; unit: string; expires_at: string | null; is_expired: boolean; expires_soon: boolean };
export type ProductionReadinessIngredientLine = { ingredient_id: number; ingredient_name: string; required_quantity: string; required_unit: string; available_quantity: string; missing_quantity: string | null; can_fulfill: boolean; selected_lots: ProductionReadinessLotSelection[]; warnings: ProductionReadinessIssue[] };
export type ProductionReadinessPackagingLine = { packaging_item_id: number; name: string; required_quantity: string; available_quantity: string; missing_quantity: string | null; can_fulfill: boolean };
export type ProductionReadinessResponse = { order_id: number; can_produce: boolean; status: ProductionReadinessStatus; blocking_issues: ProductionReadinessIssue[]; warnings: ProductionReadinessIssue[]; ingredients: ProductionReadinessIngredientLine[]; packaging: ProductionReadinessPackagingLine[]; estimated_cost: string | null; estimated_tax: string | null; estimated_margin: string | null; generated_at: string | null };

export type OrderReadinessPresentationFormatters = {
  escapeHtml(value: string): string;
  formatDate(value: string): string;
  formatDateTime(value: string): string;
  quantityLabel(value: string | null | undefined, unit: string | null | undefined): string;
  missingQuantityLabel(value: string | null, unit: string): string;
  moneyOrMissing(value: string | null): string;
};

export type OrderReadinessPanelInput = {
  orderId: number;
  closed: boolean;
  busy: boolean;
  error: string;
  result: ProductionReadinessResponse | null | undefined;
  current: boolean;
};

export type OrderProductionGateInput = {
  orderId: number;
  readiness: ProductionReadinessResponse | null | undefined;
  hasCachedReadiness: boolean;
  confirming: boolean;
  loading: boolean;
  blockedByOperation: boolean;
  persistentWriteActive: boolean;
  notes: string;
  error: string;
  recoveryAction: string;
  uncertain: boolean;
};

export type OrderPersistentWritePresentationOwner = {
  kind: 'production' | 'cancel' | 'archive';
  orderId: number;
} | null;

export type OrderLifecycleActionsInput = {
  orderId: number;
  isActive: boolean;
  status: string;
  sameOrderOperationActive: boolean;
  persistentOwner: OrderPersistentWritePresentationOwner;
};

export function renderOrderLifecycleActions(input: OrderLifecycleActionsInput): string {
  if (!input.isActive || input.status === 'archived') return '';
  const disabled = input.sameOrderOperationActive || Boolean(input.persistentOwner);
  const cancelPending = input.persistentOwner?.kind === 'cancel' && input.persistentOwner.orderId === input.orderId;
  const archivePending = input.persistentOwner?.kind === 'archive' && input.persistentOwner.orderId === input.orderId;
  const cancel = `<button class="secondary-action compact danger-action" type="button" data-action="cancel-order" data-id="${input.orderId}" ${disabled ? 'disabled' : ''}${cancelPending ? ' aria-busy="true" data-order-lifecycle-pending="cancel"' : ''}>${cancelPending ? 'Отменяем…' : 'Отменить заказ'}</button>`;
  const archive = `<button class="secondary-action compact danger-action" type="button" data-action="archive-order" data-id="${input.orderId}" ${disabled ? 'disabled' : ''}${archivePending ? ' aria-busy="true" data-order-lifecycle-pending="archive"' : ''}>${archivePending ? 'Архивируем…' : 'Архивировать'}</button>`;
  return input.status === 'cancelled' ? archive : `${cancel}${archive}`;
}

export function renderOrderRowActions(input: OrderLifecycleActionsInput): string {
  return `<div class="row-actions"><button class="secondary-action compact" type="button" data-action="open-order" data-id="${input.orderId}">Открыть</button>${renderOrderLifecycleActions(input)}</div>`;
}

export function renderOrderPersistentWriteNotice(active: boolean, sameOrder: boolean): string {
  if (!active) return '';
  return `<p class="next-step" data-order-persistent-write-notice="${sameOrder ? 'current' : 'other'}">${sameOrder
    ? 'Дождитесь завершения текущего действия с заказом. После этого снова будут доступны изготовление, отмена и архивирование.'
    : 'Сейчас выполняется действие с другим заказом. Карточки можно просматривать и проверять готовность, но изготовление, отмена и архивирование временно недоступны.'}</p>`;
}

export function renderOrderReadinessPanel(
  input: OrderReadinessPanelInput,
  formatters: OrderReadinessPresentationFormatters,
): string {
  if (input.closed) {
    return '<section class="card data-card"><p class="card-kicker">Проверка изготовления</p><h2>Проверка больше не нужна</h2><p class="next-step">Заказ уже изготовлен или закрыт. Повторная проверка готовности недоступна: складские списания и история партии уже фиксируются через производство.</p></section>';
  }
  if (input.busy) {
    return `<section class="card data-card" data-order-readiness-busy="true" data-order-readiness-focus-anchor="true" data-id="${input.orderId}" tabindex="-1" aria-busy="true" aria-labelledby="order-readiness-loading-title"><p class="card-kicker">Проверка изготовления</p><h2 id="order-readiness-loading-title">Проверяем…</h2><p>Сверяем рецепт, компоненты, партии и тару.</p><p class="next-step">Это только проверка. Склад не списан, партии не зарезервированы, заказ не переведён в производство.</p></section>`;
  }
  if (input.error) {
    return `<section class="card error-card" data-order-readiness-error="true" data-order-readiness-focus-anchor="true" data-id="${input.orderId}" tabindex="-1"><p class="card-kicker">Сбой проверки</p><h2>Результат готовности не получен</h2><p>${formatters.escapeHtml(input.error)}</p><p class="next-step">Это системная ошибка запроса, а не результат «производство заблокировано». Можно безопасно повторить только проверку.</p><button class="primary-action" type="button" data-action="retry-order-readiness" data-id="${input.orderId}">Повторить проверку</button></section>`;
  }
  if (!input.result) {
    return '<section class="card data-card"><p class="card-kicker">Проверка изготовления</p><h2>Готовность к производству</h2><p>Проверка изготовления ещё не выполнялась. Нажмите «Проверить изготовление», чтобы увидеть, хватает ли компонентов и тары.</p><p class="next-step">Это только проверка. Склад не списан, партии не зарезервированы, заказ не переведён в производство.</p></section>';
  }
  return renderReadinessResult(input.result, !input.current, formatters);
}

export function renderOrderProductionGate(
  input: OrderProductionGateInput,
  escapeHtml: (value: string) => string,
): string {
  const error = input.error ? `<div class="page-message error-message" data-order-production-failure="true" data-order-production-focus-anchor="failure" tabindex="-1"><p>${escapeHtml(input.error)}</p>${input.recoveryAction ? `<p class="next-step">${escapeHtml(input.recoveryAction)}</p>` : ''}<button class="primary-action" type="button" data-action="reconcile-production-outcome" data-id="${input.orderId}">${input.uncertain ? 'Проверить результат изготовления' : 'Обновить заказ безопасно'}</button></div>` : '';
  if (!input.readiness) {
    if (input.error) return `<section class="card data-card" data-order-production-state="failure"><p class="card-kicker">Изготовление</p><h2>Нужно проверить результат изготовления</h2>${error}</section>`;
    return `<section class="card data-card"><p class="card-kicker">Изготовление</p><h2>Подтверждение изготовления</h2><p class="next-step">${input.hasCachedReadiness ? 'Текущий результат проверки отсутствует. Повторите проверку перед изготовлением.' : 'Сначала проверьте готовность изготовления.'}</p></section>`;
  }
  if (!input.readiness.can_produce || input.readiness.status === 'blocked') {
    return `<section class="card data-card"><p class="card-kicker">Изготовление</p><h2>Подтверждение изготовления</h2>${error}<p class="next-step">Производство недоступно, пока есть блокирующие замечания.</p></section>`;
  }
  const operationBlocked = input.blockedByOperation || input.persistentWriteActive;
  const operationNote = input.loading
    ? '<p class="next-step">Изготовление выполняется… Дождитесь завершения, прежде чем запускать другое действие с заказом.</p>'
    : input.persistentWriteActive
      ? '<p class="next-step">Сейчас выполняется изготовление, отмена или архивирование заказа. Дождитесь завершения текущего действия.</p>'
      : input.blockedByOperation
        ? '<p class="next-step">Дождитесь завершения текущей операции с заказом. После неё повторите проверку готовности.</p>'
        : input.readiness.status === 'warning'
          ? '<p class="next-step">Есть предупреждения. Проверьте их перед подтверждением изготовления.</p>'
          : '<p class="next-step">Проверка готовности разрешает изготовление. Подтвердите действие только после проверки списка компонентов и тары.</p>';
  if (input.confirming) {
    return `<section class="card data-card" data-order-production-focus-anchor="confirmation" tabindex="-1"><p class="card-kicker">Изготовление</p><h2>Подтверждение изготовления</h2>${operationNote}${error}<div class="readiness-block" ${input.loading ? 'aria-busy="true"' : ''}><h3>Подтвердите изготовление</h3><p>После подтверждения система создаст производственную партию, спишет компоненты и тару со склада и переведёт заказ в статус «Изготовлен».</p><p class="next-step">Это действие нельзя отменить в MVP.</p><label class="full-span">Заметка к партии<textarea data-action="production-notes" data-id="${input.orderId}" rows="3" maxlength="1600" placeholder="Необязательно" ${input.loading || operationBlocked ? 'disabled' : ''}>${escapeHtml(input.notes)}</textarea></label><div class="actions"><button class="primary-action" type="button" data-action="confirm-production" data-id="${input.orderId}" ${input.loading ? 'aria-busy="true"' : ''} ${input.loading || operationBlocked ? 'disabled' : ''}>${input.loading ? 'Изготавливаем…' : 'Подтвердить изготовление'}</button><button class="secondary-action" type="button" data-action="cancel-production-confirmation" data-id="${input.orderId}" ${input.loading ? 'disabled' : ''}>Отмена</button></div></div></section>`;
  }
  return `<section class="card data-card"><p class="card-kicker">Изготовление</p><h2>Подтверждение изготовления</h2>${operationNote}${error}<div class="actions"><button class="primary-action" type="button" data-action="open-production-confirmation" data-id="${input.orderId}" ${operationBlocked ? 'disabled' : ''}>Изготовить</button></div></section>`;
}

function renderReadinessResult(
  result: ProductionReadinessResponse,
  stale: boolean,
  f: OrderReadinessPresentationFormatters,
): string {
  return `<section class="card data-card readiness-result" data-order-readiness-result="${stale ? 'stale' : 'current'}" data-order-readiness-focus-anchor="true" data-id="${result.order_id}" tabindex="-1"><div class="section-heading"><div><p class="card-kicker">${stale ? 'Предыдущая проверка' : 'Проверка изготовления'}</p><h2>${stale ? 'Результат нужно обновить' : readinessStatusLabel(result.status)}</h2></div><span class="pill ${stale ? 'warning' : readinessStatusPill(result.status)}">${stale ? 'Не разрешает изготовление' : result.can_produce ? 'Склад выглядит достаточным' : 'Есть препятствия'}</span></div>${stale ? '<p class="page-message warning-message">После этой проверки заказ изменился или была запущена более новая проверка. Результат сохранён для справки, но изготовление по нему недоступно.</p>' : ''}<p class="next-step">Это только проверка. Склад не списан, партии не зарезервированы, заказ не переведён в производство.</p>${result.generated_at ? `<p><strong>Проверено:</strong> ${f.formatDateTime(result.generated_at)}</p>` : ''}<p>${stale ? 'Запустите проверку ещё раз, чтобы получить текущий результат.' : readinessNextAction(result.status)}</p>${readinessIssuesSection('Что мешает изготовлению', result.blocking_issues, 'Критичных препятствий нет.', result, f.escapeHtml)}${readinessIssuesSection('На что обратить внимание', result.warnings, 'Предупреждений нет.', result, f.escapeHtml)}${readinessIngredientsTable(result.ingredients, f)}${readinessPackagingTable(result.packaging, f)}${readinessEstimates(result, f)}</section>`;
}

function readinessStatusLabel(status: ProductionReadinessStatus) { return status === 'ready' ? 'Можно изготовить' : status === 'warning' ? 'Можно изготовить, но есть предупреждения' : 'Пока нельзя изготовить'; }
function readinessStatusPill(status: ProductionReadinessStatus) { return status === 'ready' ? 'success' : status === 'warning' ? 'warning' : 'danger'; }
function readinessNextAction(status: ProductionReadinessStatus) { return status === 'blocked' ? 'Сначала устраните препятствия: добавьте недостающие партии, тару или исправьте данные рецепта.' : status === 'warning' ? 'Проверьте предупреждения перед производством. Если всё верно, ниже появится кнопка явного подтверждения изготовления.' : 'Компонентов и тары хватает. Если всё верно, ниже появится кнопка явного подтверждения изготовления.'; }
function readinessSeverityLabel(severity: ProductionReadinessIssueSeverity) { return severity === 'blocking' ? 'Стоп' : severity === 'warning' ? 'Важно' : 'Инфо'; }

function readinessIssueContext(issue: ProductionReadinessIssue, result: ProductionReadinessResponse) {
  if (issue.entity_type === 'recipe_version' || issue.entity_type === 'client_recipe') return 'Рецепт или индивидуальная формула';
  if (issue.entity_type === 'ingredient') return result.ingredients.find((line) => line.ingredient_id === issue.entity_id)?.ingredient_name || 'Компонент рецепта';
  if (issue.entity_type === 'ingredient_lot') {
    const lot = result.ingredients.flatMap((line) => line.selected_lots).find((item) => item.lot_id === issue.entity_id);
    return lot?.lot_code ? `Партия «${lot.lot_code}»` : 'Партия компонента';
  }
  if (issue.entity_type === 'packaging_item') return result.packaging.find((line) => line.packaging_item_id === issue.entity_id)?.name || 'Тара';
  if (issue.entity_type === 'order') return 'Заказ';
  return 'Общие замечания';
}

function readinessIssuesSection(title: string, issues: ProductionReadinessIssue[], empty: string, result: ProductionReadinessResponse, escapeHtml: (value: string) => string) {
  const groups = new Map<string, ProductionReadinessIssue[]>();
  issues.forEach((issue) => { const context = readinessIssueContext(issue, result); groups.set(context, [...(groups.get(context) || []), issue]); });
  return `<div class="readiness-block"><h3>${title}</h3>${issues.length ? [...groups.entries()].map(([context, items]) => `<div class="readiness-issue-group"><h4>${escapeHtml(context)}</h4><ul>${items.map((issue) => `<li><span class="pill ${issue.severity === 'blocking' ? 'danger' : issue.severity === 'warning' ? 'warning' : 'info'}">${readinessSeverityLabel(issue.severity)}</span> ${escapeHtml(issue.message)}</li>`).join('')}</ul></div>`).join('') : `<p class="empty-hint">${empty}</p>`}</div>`;
}

function readinessIngredientsTable(lines: ProductionReadinessIngredientLine[], f: OrderReadinessPresentationFormatters) {
  if (!lines.length) return '<div class="readiness-block"><h3>Компоненты</h3><p class="empty-hint">Компоненты не найдены в ответе проверки. Проверьте рецепт заказа.</p></div>';
  return `<div class="readiness-block"><h3>Компоненты</h3><div class="table-wrap"><table class="compact-catalog-table"><thead><tr><th>Компонент</th><th>Нужно</th><th>Доступно</th><th>Не хватает</th><th>Статус</th><th>Выбранные партии</th></tr></thead><tbody>${lines.map((line) => `<tr><td><strong>${f.escapeHtml(line.ingredient_name)}</strong>${line.warnings.length ? `<small>${line.warnings.map((warning) => f.escapeHtml(warning.message)).join('<br>')}</small>` : ''}</td><td>${f.quantityLabel(line.required_quantity, line.required_unit)}</td><td>${f.quantityLabel(line.available_quantity, line.required_unit)}</td><td>${f.missingQuantityLabel(line.missing_quantity, line.required_unit)}</td><td><span class="pill ${line.can_fulfill ? 'success' : 'danger'}">${line.can_fulfill ? 'Хватает' : 'Не хватает'}</span></td><td>${readinessLots(line.selected_lots, f)}</td></tr>`).join('')}</tbody></table></div></div>`;
}

function readinessLots(lots: ProductionReadinessLotSelection[], f: OrderReadinessPresentationFormatters) {
  if (!lots.length) return '<span class="empty-hint">Партии не подобраны.</span>';
  return lots.map((lot) => `<div><strong>${f.escapeHtml(lot.lot_code || 'Без номера')}</strong> · ${f.quantityLabel(lot.selected_quantity, lot.unit)} · ${lot.expires_at ? `до ${f.formatDate(lot.expires_at)}` : 'срок не указан'} ${lot.is_expired ? '<span class="pill danger">Просрочена</span>' : lot.expires_soon ? '<span class="pill warning">Скоро истекает</span>' : ''}</div>`).join('');
}

function readinessPackagingTable(lines: ProductionReadinessPackagingLine[], f: OrderReadinessPresentationFormatters) {
  return `<div class="readiness-block"><h3>Тара</h3>${lines.length ? `<div class="table-wrap"><table class="compact-catalog-table"><thead><tr><th>Тара</th><th>Нужно</th><th>Доступно</th><th>Не хватает</th><th>Статус</th></tr></thead><tbody>${lines.map((line) => `<tr><td><strong>${f.escapeHtml(line.name)}</strong></td><td>${f.quantityLabel(line.required_quantity, 'pcs')}</td><td>${f.quantityLabel(line.available_quantity, 'pcs')}</td><td>${f.missingQuantityLabel(line.missing_quantity, 'pcs')}</td><td><span class="pill ${line.can_fulfill ? 'success' : 'danger'}">${line.can_fulfill ? 'Хватает' : 'Не хватает'}</span></td></tr>`).join('')}</tbody></table></div>` : '<p class="empty-hint">Тара не выбрана или проверка тары не требуется.</p>'}</div>`;
}

function readinessEstimates(result: ProductionReadinessResponse, f: OrderReadinessPresentationFormatters) {
  return `<div class="readiness-block"><h3>Предварительная экономика</h3><div class="readiness-grid"><div><strong>Ориентировочная себестоимость</strong><p>${f.moneyOrMissing(result.estimated_cost)}</p></div><div><strong>Налог</strong><p>${f.moneyOrMissing(result.estimated_tax)}</p></div><div><strong>Маржа</strong><p>${f.moneyOrMissing(result.estimated_margin)}</p></div></div><p class="next-step">Если налог или маржа не рассчитаны, интерфейс не подставляет налоговую ставку сам.</p></div>`;
}
