type HealthStatus = 'checking' | 'online' | 'offline';
type OnboardingStatus = 'loading' | 'ready' | 'unavailable';
type InventoryStatus = 'idle' | 'loading' | 'ready' | 'error';

type OnboardingState = {
  has_started: boolean;
  is_completed: boolean;
  current_step: string;
  completed_steps: string[];
  available_steps: string[];
};

type InventoryOverview = {
  ingredient_lots_total: number;
  ingredient_lots_with_positive_balance: number;
  ingredient_lots_zero_balance: number;
  ingredient_lots_expired: number;
  ingredient_lots_expiring_soon: number;
  active_ingredient_lots_total: number;
  packaging_items_total: number;
  packaging_items_with_positive_balance: number;
  packaging_items_zero_balance: number;
  active_packaging_items_total: number;
  generated_at: string;
};

type IngredientLotBalance = {
  lot_id: number;
  ingredient_id: number;
  ingredient_name: string;
  lot_code: string;
  supplier: string;
  unit: string;
  balance_quantity: string;
  purchase_date: string | null;
  expiration_date: string | null;
  is_expired: boolean;
  expires_soon: boolean;
  days_until_expiration: number | null;
  is_active: boolean;
  has_positive_balance: boolean;
};

type PackagingBalance = {
  packaging_item_id: number;
  name: string;
  kind: string;
  kind_label: string;
  unit: string;
  balance_quantity: string;
  capacity_value: string | null;
  capacity_unit: string | null;
  material: string;
  is_active: boolean;
  has_positive_balance: boolean;
};

type InventoryState = {
  overview: InventoryOverview | null;
  ingredientLots: IngredientLotBalance[];
  packagingItems: PackagingBalance[];
};

const navigationItems = ['Главная','Рецепты','Клиенты','Заказы','Склад','Тара','Закупки','Производство','Импорт','Отчеты','Настройки','Помощь'];
const stepLabels: Record<string, string> = {
  welcome: 'Познакомиться с рабочим пространством',
  data_location: 'Понять, где хранятся локальные данные',
  first_ingredient: 'Подготовить первый компонент',
  first_recipe: 'Подготовить первый рецепт',
  first_client: 'Подготовить первую карточку клиента',
  first_order: 'Подготовить первый заказ',
  first_backup: 'Запланировать первую резервную копию',
};

let activeSection = sectionFromLocation();
let healthStatus: HealthStatus = 'checking';
let onboardingStatus: OnboardingStatus = 'loading';
let onboardingState: OnboardingState | null = null;
let onboardingMessage = '';
let inventoryStatus: InventoryStatus = 'idle';
let inventoryState: InventoryState = { overview: null, ingredientLots: [], packagingItems: [] };
let inventoryError = '';

function sectionFromLocation() {
  return window.location.pathname === '/inventory' ? 'Склад' : 'Главная';
}

function render() {
  const root = document.getElementById('root');
  if (!root) return;
  const healthLabel = { checking: 'Проверяем локальный API…', online: 'Локальный API доступен', offline: 'Локальный API пока недоступен' }[healthStatus];
  root.innerHTML = `
    <div class="app-shell">
      <aside class="sidebar" aria-label="Основная навигация">
        <div class="brand" aria-label="Мастерская косметолога">
          <div class="brand-mark" aria-hidden="true"><span class="brand-fallback">МК</span><img src="/brand/mch-logo.png" alt="" /></div>
          <div class="brand-copy"><p class="brand-kicker">Локальная система</p><p class="brand-name">Мастерская косметолога</p></div>
        </div>
        <nav class="navigation">${navigationItems.map((item) => `<button class="nav-item ${item === activeSection ? 'active' : ''}" type="button" data-section="${item}">${item}</button>`).join('')}</nav>
      </aside>
      <main class="content">
        <header class="topbar">
          <div><p class="eyebrow">Рабочее пространство</p><h1>${activeSection}</h1></div>
          <span class="status ${healthStatus}">${healthLabel}</span>
        </header>
        ${activeSection === 'Главная' ? dashboardPlaceholder() : activeSection === 'Склад' ? inventoryPage() : sectionPlaceholder(activeSection)}
      </main>
    </div>`;
  bindEvents(root);
}

function bindEvents(root: HTMLElement) {
  root.querySelector<HTMLImageElement>('.brand-mark img')?.addEventListener('error', (event) => { (event.currentTarget as HTMLImageElement).hidden = true; });
  root.querySelectorAll<HTMLButtonElement>('.nav-item').forEach((button) => {
    button.addEventListener('click', () => {
      activeSection = button.dataset.section ?? 'Главная';
      window.history.pushState({}, '', activeSection === 'Склад' ? '/inventory' : '/');
      if (activeSection === 'Склад') loadInventory();
      render();
    });
  });
  root.querySelector<HTMLButtonElement>('[data-action="start-onboarding"]')?.addEventListener('click', () => updateOnboarding('/api/onboarding/start'));
  root.querySelector<HTMLButtonElement>('[data-action="complete-step"]')?.addEventListener('click', (event) => {
    const step = (event.currentTarget as HTMLButtonElement).dataset.step;
    if (step) updateOnboarding('/api/onboarding/complete-step', { step });
  });
  root.querySelector<HTMLButtonElement>('[data-action="skip-onboarding"]')?.addEventListener('click', () => updateOnboarding('/api/onboarding/skip'));
  root.querySelector<HTMLButtonElement>('[data-action="reload-inventory"]')?.addEventListener('click', () => loadInventory(true));
}

function dashboardPlaceholder() {
  return `${onboardingCard()}<section class="card"><p class="card-kicker">Сегодня в мастерской</p><h2>Первые рабочие разделы появятся постепенно</h2><p>Здесь будет спокойная рабочая панель: активные заказы, предупреждения, закупки, производство и резервные копии.</p><p class="next-step">Начните с компонентов, затем рецептов, клиентов и заказов. Каждый раздел будет подключаться отдельным безопасным шагом.</p></section>`;
}

function inventoryPage() {
  if (inventoryStatus === 'idle' || inventoryStatus === 'loading') return `<section class="card"><p class="card-kicker">Склад</p><h2>Загружаем остатки…</h2><p>Получаем сводку по партиям компонентов и таре из локального API.</p></section>`;
  if (inventoryStatus === 'error') return `<section class="card error-card"><p class="card-kicker">Склад</p><h2>Не удалось загрузить склад</h2><p>${inventoryError || 'Локальный API временно недоступен.'}</p><p class="next-step">Проверьте, что приложение запущено полностью, и попробуйте обновить раздел.</p><button class="primary-action" type="button" data-action="reload-inventory">Повторить загрузку</button></section>`;
  const overview = inventoryState.overview;
  return `<div class="inventory-layout"><section class="card inventory-intro"><p class="card-kicker">Склад</p><h2>Обзор запасов</h2><p>Здесь показаны только текущие остатки, которые уже посчитаны backend read-моделями. На этой странице нет действий изменения склада.</p></section>${overview ? overviewCards(overview) : emptyCard('Сводка пока пуста', 'Когда появятся партии компонентов или тара, здесь будет краткая сводка.')} ${ingredientLotsTable(inventoryState.ingredientLots)} ${packagingTable(inventoryState.packagingItems)}</div>`;
}

function overviewCards(overview: InventoryOverview) {
  const cards: [string, number][] = [
    ['Партии компонентов', overview.ingredient_lots_total], ['Есть остаток', overview.ingredient_lots_with_positive_balance], ['Нулевой остаток', overview.ingredient_lots_zero_balance], ['Просрочено', overview.ingredient_lots_expired], ['Скоро истекает', overview.ingredient_lots_expiring_soon], ['Тара', overview.packaging_items_total], ['Тара в наличии', overview.packaging_items_with_positive_balance], ['Тара без остатка', overview.packaging_items_zero_balance],
  ];
  return `<section class="overview-grid" aria-label="Сводка склада">${cards.map(([label, value]) => `<article class="metric-card"><span>${label}</span><strong>${value}</strong></article>`).join('')}</section>`;
}

function ingredientLotsTable(rows: IngredientLotBalance[]) {
  if (rows.length === 0) return emptyCard('Партии компонентов не найдены', 'Когда будут добавлены компоненты, партии и движения склада, остатки появятся в этой таблице.');
  return `<section class="card data-card"><p class="card-kicker">Компоненты</p><h2>Партии в учете</h2><div class="table-wrap"><table><thead><tr><th>Компонент</th><th>Партия</th><th>Поставщик</th><th>Остаток</th><th>Ед.</th><th>Срок годности</th><th>Статус</th></tr></thead><tbody>${rows.map((row) => `<tr><td>${escapeHtml(row.ingredient_name)}</td><td>${escapeHtml(row.lot_code || 'Без номера')}</td><td>${escapeHtml(row.supplier || 'Не указан')}</td><td>${escapeHtml(row.balance_quantity)}</td><td>${unitLabel(row.unit)}</td><td>${formatDate(row.expiration_date)}</td><td><span class="pill ${ingredientStatusClass(row)}">${ingredientStatus(row)}</span></td></tr>`).join('')}</tbody></table></div></section>`;
}

function packagingTable(rows: PackagingBalance[]) {
  if (rows.length === 0) return emptyCard('Тара не найдена', 'Когда будут добавлены баночки, флаконы или расходники, остатки появятся в этой таблице.');
  return `<section class="card data-card"><p class="card-kicker">Тара</p><h2>Тара и расходники</h2><div class="table-wrap"><table><thead><tr><th>Тара</th><th>Тип</th><th>Объем</th><th>Материал</th><th>Остаток</th><th>Статус</th></tr></thead><tbody>${rows.map((row) => `<tr><td>${escapeHtml(row.name)}</td><td>${escapeHtml(row.kind_label)}</td><td>${capacityLabel(row)}</td><td>${escapeHtml(row.material || 'Не указан')}</td><td>${escapeHtml(row.balance_quantity)} ${unitLabel(row.unit)}</td><td><span class="pill ${packagingStatusClass(row)}">${packagingStatus(row)}</span></td></tr>`).join('')}</tbody></table></div></section>`;
}

function emptyCard(title: string, text: string) { return `<section class="card empty-card"><h2>${title}</h2><p>${text}</p><p class="next-step">Следующее действие: добавление данных будет доступно в отдельных безопасных разделах.</p></section>`; }
function ingredientStatus(row: IngredientLotBalance) { if (!row.is_active) return 'Неактивна'; if (row.is_expired) return 'Просрочено'; if (row.expires_soon) return 'Скоро истекает'; if (!row.expiration_date) return 'Без срока годности'; return row.has_positive_balance ? 'В наличии' : 'Нет остатка'; }
function ingredientStatusClass(row: IngredientLotBalance) { if (!row.is_active || !row.has_positive_balance) return 'muted'; if (row.is_expired) return 'danger'; if (row.expires_soon) return 'warning'; return 'success'; }
function packagingStatus(row: PackagingBalance) { if (!row.is_active) return 'Неактивна'; return row.has_positive_balance ? 'В наличии' : 'Нет остатка'; }
function packagingStatusClass(row: PackagingBalance) { if (!row.is_active || !row.has_positive_balance) return 'muted'; return 'success'; }
function unitLabel(unit: string) { return ({ g: 'г', ml: 'мл', pcs: 'шт.' } as Record<string, string>)[unit] ?? escapeHtml(unit); }
function capacityLabel(row: PackagingBalance) { return row.capacity_value && row.capacity_unit ? `${escapeHtml(row.capacity_value)} ${unitLabel(row.capacity_unit)}` : 'Не указан'; }
function formatDate(value: string | null) { return value ? new Intl.DateTimeFormat('ru-RU').format(new Date(`${value}T00:00:00`)) : 'Без срока'; }
function escapeHtml(value: string) { return value.replace(/[&<>'"]/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[char] ?? char)); }

function onboardingCard() {
  if (onboardingStatus === 'loading') return `<section class="card onboarding-card"><p class="card-kicker">Первый запуск</p><h2>Готовим рабочее пространство…</h2><p>Проверяем состояние первичной настройки.</p></section>`;
  if (onboardingStatus === 'unavailable') return `<section class="card onboarding-card"><p class="card-kicker">Первый запуск</p><h2>Добро пожаловать в Мастерскую косметолога</h2><p>Это локальная рабочая система. Даже если локальный API сейчас недоступен, вы можете осмотреть разделы приложения.</p><p class="next-step">Когда приложение будет запущено полностью, здесь появится чек-лист первичной настройки.</p></section>`;
  if (onboardingState?.is_completed) return `<section class="card onboarding-card"><p class="card-kicker">Первичная настройка</p><h2>Чек-лист первичной настройки закрыт</h2><p>Вы сможете вернуться к заполнению компонентов, рецептов, клиентов и заказов постепенно.</p></section>`;
  const currentStep = onboardingState?.current_step ?? 'welcome';
  const started = onboardingState?.has_started ?? false;
  return `<section class="card onboarding-card"><p class="card-kicker">Первый запуск</p><h2>Добро пожаловать в Мастерскую косметолога</h2><p>Это локальная рабочая система для вашей косметической мастерской. Данные хранятся на этом компьютере, отдельно от кода приложения.</p><div class="onboarding-note"><strong>Что важно:</strong> регулярно делайте резервные копии, а компоненты, рецепты, клиентов и заказы заполняйте постепенно.</div>${onboardingMessage ? `<p class="inline-message">${onboardingMessage}</p>` : ''}<ol class="checklist">${(onboardingState?.available_steps ?? Object.keys(stepLabels)).map((step) => checklistItem(step, currentStep)).join('')}</ol><div class="actions">${started ? `<button class="primary-action" type="button" data-action="complete-step" data-step="${currentStep}">Отметить текущий шаг</button>` : '<button class="primary-action" type="button" data-action="start-onboarding">Начать настройку</button>'}<button class="secondary-action" type="button" data-action="skip-onboarding">Пропустить пока</button></div></section>`;
}
function checklistItem(step: string, currentStep: string) { const isDone = onboardingState?.completed_steps.includes(step); const isCurrent = step === currentStep && !isDone; const marker = isDone ? '✓' : isCurrent ? '•' : '○'; return `<li class="${isDone ? 'done' : ''} ${isCurrent ? 'current' : ''}"><span>${marker}</span><div><strong>${stepLabels[step] ?? step}</strong><small>${stepHint(step)}</small></div></li>`; }
function stepHint(step: string) { return ({ welcome: 'Коротко понять назначение системы.', data_location: 'Данные остаются на этом компьютере; будущие резервные копии помогут защитить работу.', first_ingredient: 'Позже здесь появится добавление компонентов и плотностей.', first_recipe: 'Рецепты будут храниться версиями, без скрытого изменения истории.', first_client: 'Клиентские данные будут заполняться аккуратно и понятно.', first_order: 'Заказы и производство появятся отдельным roadmap-шагом.', first_backup: 'Резервные копии — обязательная привычка для локальной системы.' } as Record<string, string>)[step] ?? 'Шаг будет уточнен позже.'; }
function sectionPlaceholder(title: string) { const emptyStates: Record<string, string> = { Рецепты: 'Рецепты появятся здесь позже. Пока можно завершить первичную настройку на главной странице.', Клиенты: 'Клиенты появятся здесь позже. В будущих шагах здесь будут карточки клиентов и индивидуальные формулы.', Запасы: 'Складской обзор теперь доступен в разделе «Склад». Формы добавления компонентов и движений появятся отдельными PR.' }; return `<section class="card"><p class="card-kicker">Раздел приложения</p><h2>${title}</h2><p>${emptyStates[title] ?? 'Этот раздел подготовлен как понятная навигационная заглушка. Формы и бизнес-функции будут добавляться в отдельных PR.'}</p><p class="next-step">Следующее действие: дождаться реализации соответствующего roadmap-шага.</p></section>`; }

function apiGet<T>(url: string): Promise<T> { return fetch(url).then((response) => { if (!response.ok) throw new Error('API request failed'); return response.json() as Promise<T>; }); }
function getInventoryOverview() { return apiGet<InventoryOverview>('/api/inventory/overview'); }
function getIngredientLotBalances() { return apiGet<{ ingredient_lot_balances: IngredientLotBalance[] }>('/api/inventory/ingredient-lot-balances'); }
function getPackagingBalances() { return apiGet<{ packaging_balances: PackagingBalance[] }>('/api/inventory/packaging-balances'); }

function loadInventory(force = false) {
  if (!force && (inventoryStatus === 'loading' || inventoryStatus === 'ready')) return;
  inventoryStatus = 'loading'; inventoryError = ''; render();
  Promise.all([getInventoryOverview(), getIngredientLotBalances(), getPackagingBalances()])
    .then(([overview, lots, packaging]) => { inventoryState = { overview, ingredientLots: lots.ingredient_lot_balances, packagingItems: packaging.packaging_balances }; inventoryStatus = 'ready'; render(); })
    .catch(() => { inventoryStatus = 'error'; inventoryError = 'Не получилось получить складскую сводку из локального API.'; render(); });
}
function loadOnboarding() { fetch('/api/onboarding').then((response) => { if (!response.ok) throw new Error('Onboarding is unavailable'); return response.json() as Promise<OnboardingState>; }).then((state) => { onboardingState = state; onboardingStatus = 'ready'; onboardingMessage = ''; render(); }).catch(() => { onboardingStatus = 'unavailable'; render(); }); }
function updateOnboarding(url: string, body?: Record<string, string>) { fetch(url, { method: 'POST', headers: body ? { 'Content-Type': 'application/json' } : undefined, body: body ? JSON.stringify(body) : undefined }).then((response) => { if (!response.ok) throw new Error('Onboarding update failed'); return response.json() as Promise<OnboardingState>; }).then((state) => { onboardingState = state; onboardingStatus = 'ready'; onboardingMessage = 'Сохранено в локальном рабочем пространстве.'; render(); }).catch(() => { onboardingStatus = 'unavailable'; onboardingMessage = ''; render(); }); }

window.addEventListener('popstate', () => { activeSection = sectionFromLocation(); if (activeSection === 'Склад') loadInventory(); render(); });
render();
fetch('/api/health').then((response) => { healthStatus = response.ok ? 'online' : 'offline'; render(); }).catch(() => { healthStatus = 'offline'; render(); });
loadOnboarding();
if (activeSection === 'Склад') loadInventory();
