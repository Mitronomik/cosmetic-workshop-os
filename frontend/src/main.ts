type HealthStatus = 'checking' | 'online' | 'offline';
type OnboardingStatus = 'loading' | 'ready' | 'unavailable';
type InventoryStatus = 'idle' | 'loading' | 'ready' | 'error';
type IngredientsStatus = 'idle' | 'loading' | 'ready' | 'error';
type IngredientFormMode = 'create' | 'edit';

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

type Ingredient = {
  id: number;
  name: string;
  category: string;
  default_unit: string;
  density_g_per_ml: string | null;
  is_active: boolean;
  notes: string;
  inci_name: string;
  supplier_hint: string;
  allergen_note: string;
  usage_note: string;
  created_at: string;
  updated_at: string;
};

type IngredientPayload = {
  name: string;
  category: string;
  default_unit: string;
  density_g_per_ml: string | null;
  notes: string;
  inci_name: string;
  supplier_hint: string;
  allergen_note: string;
  usage_note: string;
};

type IngredientFormState = IngredientPayload & { id: number | null };

type IngredientsState = {
  items: Ingredient[];
  formMode: IngredientFormMode;
  form: IngredientFormState;
};

const navigationItems = ['Главная','Компоненты','Рецепты','Клиенты','Заказы','Склад','Тара','Закупки','Производство','Импорт','Отчеты','Настройки','Помощь'];
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
let ingredientsStatus: IngredientsStatus = 'idle';
let ingredientsState: IngredientsState = { items: [], formMode: 'create', form: emptyIngredientForm() };
let ingredientsError = '';
let ingredientsMessage = '';

function sectionFromLocation() {
  if (window.location.pathname === '/inventory') return 'Склад';
  if (window.location.pathname === '/ingredients') return 'Компоненты';
  return 'Главная';
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
        ${activeSection === 'Главная' ? dashboardPlaceholder() : activeSection === 'Склад' ? inventoryPage() : activeSection === 'Компоненты' ? ingredientsPage() : sectionPlaceholder(activeSection)}
      </main>
    </div>`;
  bindEvents(root);
}

function bindEvents(root: HTMLElement) {
  root.querySelector<HTMLImageElement>('.brand-mark img')?.addEventListener('error', (event) => { (event.currentTarget as HTMLImageElement).hidden = true; });
  root.querySelectorAll<HTMLButtonElement>('.nav-item').forEach((button) => {
    button.addEventListener('click', () => {
      activeSection = button.dataset.section ?? 'Главная';
      window.history.pushState({}, '', activeSection === 'Склад' ? '/inventory' : activeSection === 'Компоненты' ? '/ingredients' : '/');
      if (activeSection === 'Склад') loadInventory();
      if (activeSection === 'Компоненты') loadIngredients();
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
  root.querySelector<HTMLButtonElement>('[data-action="reload-ingredients"]')?.addEventListener('click', () => loadIngredients(true));
  root.querySelector<HTMLButtonElement>('[data-action="new-ingredient"]')?.addEventListener('click', () => { ingredientsState.formMode = 'create'; ingredientsState.form = emptyIngredientForm(); ingredientsMessage = ''; ingredientsError = ''; render(); });
  root.querySelectorAll<HTMLButtonElement>('[data-action="edit-ingredient"]').forEach((button) => button.addEventListener('click', () => startEditIngredient(Number(button.dataset.id))));
  root.querySelectorAll<HTMLButtonElement>('[data-action="deactivate-ingredient"]').forEach((button) => button.addEventListener('click', () => deactivateIngredient(Number(button.dataset.id))));
  root.querySelector<HTMLFormElement>('[data-form="ingredient"]')?.addEventListener('submit', submitIngredientForm);
}

function dashboardPlaceholder() {
  return `${onboardingCard()}<section class="card"><p class="card-kicker">Сегодня в мастерской</p><h2>Первые рабочие разделы появятся постепенно</h2><p>Здесь будет спокойная рабочая панель: активные заказы, предупреждения, закупки, производство и резервные копии.</p><p class="next-step">Начните с компонентов, затем рецептов, клиентов и заказов. Каждый раздел будет подключаться отдельным безопасным шагом.</p></section>`;
}


function ingredientsPage() {
  if (ingredientsStatus === 'idle' || ingredientsStatus === 'loading') return `<section class="card"><p class="card-kicker">Компоненты</p><h2>Загружаем компоненты…</h2><p>Получаем справочник компонентов из локального API.</p></section>`;
  if (ingredientsStatus === 'error') return `<section class="card error-card"><p class="card-kicker">Компоненты</p><h2>Не удалось загрузить компоненты</h2><p>${ingredientsError || 'Локальный API временно недоступен.'}</p><p class="next-step">Проверьте, что приложение запущено полностью, и попробуйте обновить раздел.</p><button class="primary-action" type="button" data-action="reload-ingredients">Повторить загрузку</button></section>`;
  return `<div class="catalog-layout"><section class="card catalog-intro"><div><p class="card-kicker">Компоненты</p><h2>Справочник компонентов</h2><p>Добавляйте базовые записи компонентов, чтобы позже учитывать партии, остатки и рецептуры. Партии и движения склада в этом разделе не меняются.</p></div><button class="secondary-action" type="button" data-action="new-ingredient">Очистить форму</button></section>${ingredientsMessage ? `<p class="page-message">${ingredientsMessage}</p>` : ''}${ingredientsError ? `<p class="page-message error-message">${ingredientsError}</p>` : ''}${ingredientForm()}${ingredientList()}</div>`;
}

function ingredientForm() {
  const form = ingredientsState.form;
  const isEdit = ingredientsState.formMode === 'edit';
  return `<section class="card form-card"><p class="card-kicker">${isEdit ? 'Редактирование' : 'Создание'}</p><h2>${isEdit ? 'Изменить компонент' : 'Создать компонент'}</h2><form data-form="ingredient" class="ingredient-form"><div class="form-grid"><label>Название<input name="name" required maxlength="160" value="${escapeHtml(form.name)}" placeholder="Например, масло ши" /></label><label>Категория<select name="category">${categoryOptions(form.category)}</select></label><label>Единица учета<select name="default_unit">${unitOptions(form.default_unit)}</select></label><label>Плотность<input name="density_g_per_ml" inputmode="decimal" value="${escapeHtml(form.density_g_per_ml ?? '')}" placeholder="Например, 0.950" /></label><label>Поставщик<input name="supplier_hint" maxlength="160" value="${escapeHtml(form.supplier_hint)}" placeholder="Необязательно" /></label><label>INCI<input name="inci_name" maxlength="240" value="${escapeHtml(form.inci_name)}" placeholder="Необязательно" /></label><label class="full-span">Заметки<textarea name="notes" rows="3" maxlength="1200" placeholder="Короткие рабочие заметки">${escapeHtml(form.notes)}</textarea></label><label class="full-span">Ограничения и аллергены<textarea name="allergen_note" rows="2" maxlength="800" placeholder="Необязательно">${escapeHtml(form.allergen_note)}</textarea></label><label class="full-span">Применение<textarea name="usage_note" rows="2" maxlength="800" placeholder="Необязательно">${escapeHtml(form.usage_note)}</textarea></label></div><div class="actions"><button class="primary-action" type="submit">${isEdit ? 'Сохранить изменения' : 'Создать компонент'}</button>${isEdit ? '<button class="secondary-action" type="button" data-action="new-ingredient">Отменить редактирование</button>' : ''}</div></form></section>`;
}

function ingredientList() {
  if (ingredientsState.items.length === 0) return `<section class="card empty-card"><h2>Компонентов пока нет</h2><p>Добавьте первый компонент, чтобы потом учитывать партии и остатки на складе.</p><p class="next-step">Следующее действие: заполните название, единицу учета и при необходимости плотность, затем нажмите «Создать компонент».</p></section>`;
  return `<section class="card data-card"><p class="card-kicker">Список</p><h2>Компоненты</h2><div class="table-wrap"><table><thead><tr><th>Название</th><th>Ед. учета</th><th>Плотность</th><th>Статус</th><th>Заметки</th><th>Действия</th></tr></thead><tbody>${ingredientsState.items.map((item) => `<tr><td><strong>${escapeHtml(item.name)}</strong><small>${escapeHtml(categoryLabel(item.category))}${item.supplier_hint ? ` · ${escapeHtml(item.supplier_hint)}` : ''}</small></td><td>${unitLabel(item.default_unit)}</td><td>${item.density_g_per_ml ? `${escapeHtml(item.density_g_per_ml)} г/мл` : 'Не указана'}</td><td><span class="pill ${item.is_active ? 'success' : 'muted'}">${item.is_active ? 'Активен' : 'Неактивен'}</span></td><td>${escapeHtml(item.notes || 'Без заметок')}</td><td><div class="row-actions"><button class="secondary-action compact" type="button" data-action="edit-ingredient" data-id="${item.id}">Изменить</button>${item.is_active ? `<button class="secondary-action compact danger-action" type="button" data-action="deactivate-ingredient" data-id="${item.id}">Деактивировать</button>` : ''}</div></td></tr>`).join('')}</tbody></table></div></section>`;
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


function emptyIngredientForm(): IngredientFormState { return { id: null, name: '', category: 'other', default_unit: 'g', density_g_per_ml: null, notes: '', inci_name: '', supplier_hint: '', allergen_note: '', usage_note: '' }; }
function categoryLabel(category: string) { return ({ oil: 'Масло', butter: 'Баттер', wax: 'Воск', emulsifier: 'Эмульгатор', humectant: 'Увлажнитель', active: 'Актив', preservative: 'Консервант', fragrance: 'Отдушка', essential_oil: 'Эфирное масло', colorant: 'Краситель', water_phase: 'Водная фаза', additive: 'Добавка', other: 'Другое' } as Record<string, string>)[category] ?? category; }
function categoryOptions(current: string) { return ['oil','butter','wax','emulsifier','humectant','active','preservative','fragrance','essential_oil','colorant','water_phase','additive','other'].map((value) => `<option value="${value}" ${value === current ? 'selected' : ''}>${categoryLabel(value)}</option>`).join(''); }
function unitOptions(current: string) { return ['g','ml','pcs'].map((value) => `<option value="${value}" ${value === current ? 'selected' : ''}>${unitLabel(value)}</option>`).join(''); }
function ingredientPayloadFromForm(form: HTMLFormElement): IngredientPayload { const data = new FormData(form); const density = String(data.get('density_g_per_ml') ?? '').trim(); return { name: String(data.get('name') ?? '').trim(), category: String(data.get('category') ?? 'other'), default_unit: String(data.get('default_unit') ?? 'g'), density_g_per_ml: density || null, notes: String(data.get('notes') ?? '').trim(), inci_name: String(data.get('inci_name') ?? '').trim(), supplier_hint: String(data.get('supplier_hint') ?? '').trim(), allergen_note: String(data.get('allergen_note') ?? '').trim(), usage_note: String(data.get('usage_note') ?? '').trim() }; }
function startEditIngredient(id: number) { const item = ingredientsState.items.find((ingredient) => ingredient.id === id); if (!item) return; ingredientsState.formMode = 'edit'; ingredientsState.form = { id: item.id, name: item.name, category: item.category, default_unit: item.default_unit, density_g_per_ml: item.density_g_per_ml, notes: item.notes, inci_name: item.inci_name, supplier_hint: item.supplier_hint, allergen_note: item.allergen_note, usage_note: item.usage_note }; ingredientsMessage = ''; render(); }

function apiGet<T>(url: string): Promise<T> { return fetch(url).then((response) => { if (!response.ok) throw new Error('API request failed'); return response.json() as Promise<T>; }); }
function apiSend<T>(url: string, method: 'POST' | 'PUT', body?: unknown): Promise<T> { return fetch(url, { method, headers: body ? { 'Content-Type': 'application/json' } : undefined, body: body ? JSON.stringify(body) : undefined }).then((response) => { if (!response.ok) throw new Error('API request failed'); return response.json() as Promise<T>; }); }
function getIngredients() { return apiGet<{ ingredients: Ingredient[] }>('/api/ingredients'); }
function createIngredient(payload: IngredientPayload) { return apiSend<Ingredient>('/api/ingredients', 'POST', payload); }
function updateIngredient(id: number, payload: IngredientPayload) { return apiSend<Ingredient>(`/api/ingredients/${id}`, 'PUT', payload); }
function deactivateIngredientRequest(id: number) { return apiSend<Ingredient>(`/api/ingredients/${id}/deactivate`, 'POST'); }
function getInventoryOverview() { return apiGet<InventoryOverview>('/api/inventory/overview'); }
function getIngredientLotBalances() { return apiGet<{ ingredient_lot_balances: IngredientLotBalance[] }>('/api/inventory/ingredient-lot-balances'); }
function getPackagingBalances() { return apiGet<{ packaging_balances: PackagingBalance[] }>('/api/inventory/packaging-balances'); }


function loadIngredients(force = false) {
  if (!force && (ingredientsStatus === 'loading' || ingredientsStatus === 'ready')) return;
  ingredientsStatus = 'loading'; ingredientsError = ''; render();
  getIngredients().then((response) => { ingredientsState.items = response.ingredients; ingredientsStatus = 'ready'; render(); }).catch(() => { ingredientsStatus = 'error'; ingredientsError = 'Не получилось получить справочник компонентов из локального API.'; render(); });
}
function submitIngredientForm(event: SubmitEvent) {
  event.preventDefault();
  const form = event.currentTarget as HTMLFormElement;
  const payload = ingredientPayloadFromForm(form);
  const request = ingredientsState.formMode === 'edit' && ingredientsState.form.id ? updateIngredient(ingredientsState.form.id, payload) : createIngredient(payload);
  request.then(() => { ingredientsMessage = ingredientsState.formMode === 'edit' ? 'Компонент сохранен.' : 'Компонент создан.'; ingredientsError = ''; ingredientsState.formMode = 'create'; ingredientsState.form = emptyIngredientForm(); return getIngredients(); }).then((response) => { ingredientsState.items = response.ingredients; ingredientsStatus = 'ready'; render(); }).catch(() => { ingredientsMessage = ''; ingredientsError = 'Не удалось сохранить компонент. Проверьте обязательные поля и попробуйте еще раз.'; ingredientsStatus = 'ready'; render(); });
}
function deactivateIngredient(id: number) {
  const item = ingredientsState.items.find((ingredient) => ingredient.id === id);
  if (!item || !window.confirm(`Деактивировать компонент «${item.name}»? Он не будет удален из истории.`)) return;
  deactivateIngredientRequest(id).then(() => { ingredientsMessage = 'Компонент деактивирован.'; ingredientsError = ''; return getIngredients(); }).then((response) => { ingredientsState.items = response.ingredients; ingredientsStatus = 'ready'; render(); }).catch(() => { ingredientsMessage = ''; ingredientsError = 'Не удалось деактивировать компонент. Попробуйте еще раз.'; ingredientsStatus = 'ready'; render(); });
}

function loadInventory(force = false) {
  if (!force && (inventoryStatus === 'loading' || inventoryStatus === 'ready')) return;
  inventoryStatus = 'loading'; inventoryError = ''; render();
  Promise.all([getInventoryOverview(), getIngredientLotBalances(), getPackagingBalances()])
    .then(([overview, lots, packaging]) => { inventoryState = { overview, ingredientLots: lots.ingredient_lot_balances, packagingItems: packaging.packaging_balances }; inventoryStatus = 'ready'; render(); })
    .catch(() => { inventoryStatus = 'error'; inventoryError = 'Не получилось получить складскую сводку из локального API.'; render(); });
}
function loadOnboarding() { fetch('/api/onboarding').then((response) => { if (!response.ok) throw new Error('Onboarding is unavailable'); return response.json() as Promise<OnboardingState>; }).then((state) => { onboardingState = state; onboardingStatus = 'ready'; onboardingMessage = ''; render(); }).catch(() => { onboardingStatus = 'unavailable'; render(); }); }
function updateOnboarding(url: string, body?: Record<string, string>) { fetch(url, { method: 'POST', headers: body ? { 'Content-Type': 'application/json' } : undefined, body: body ? JSON.stringify(body) : undefined }).then((response) => { if (!response.ok) throw new Error('Onboarding update failed'); return response.json() as Promise<OnboardingState>; }).then((state) => { onboardingState = state; onboardingStatus = 'ready'; onboardingMessage = 'Сохранено в локальном рабочем пространстве.'; render(); }).catch(() => { onboardingStatus = 'unavailable'; onboardingMessage = ''; render(); }); }

window.addEventListener('popstate', () => { activeSection = sectionFromLocation(); if (activeSection === 'Склад') loadInventory(); if (activeSection === 'Компоненты') loadIngredients(); render(); });
render();
fetch('/api/health').then((response) => { healthStatus = response.ok ? 'online' : 'offline'; render(); }).catch(() => { healthStatus = 'offline'; render(); });
loadOnboarding();
if (activeSection === 'Склад') loadInventory();
if (activeSection === 'Компоненты') loadIngredients();
