type HealthStatus = 'checking' | 'online' | 'offline';
type OnboardingStatus = 'loading' | 'ready' | 'unavailable';
type InventoryStatus = 'idle' | 'loading' | 'ready' | 'error';
type IngredientsStatus = 'idle' | 'loading' | 'ready' | 'error';
type IngredientLotsStatus = 'idle' | 'loading' | 'ready' | 'error';
type RecipesStatus = 'idle' | 'loading' | 'ready' | 'error';
type StockMovementsStatus = 'idle' | 'loading' | 'ready' | 'error';
type CalculationStatus = 'idle' | 'loading' | 'ready' | 'error';
type IngredientFormMode = 'create' | 'edit';
type IngredientLotFormMode = 'create' | 'edit';
type StockMovementLoadStatus = 'idle' | 'loading' | 'ready' | 'error';

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

type IngredientLot = {
  id: number; ingredient_id: number; lot_code: string; supplier_name: string; purchased_at: string | null; expires_at: string | null; unit: string; unit_cost: string | null; total_cost: string | null; density_g_per_ml: string | null; notes: string; is_active: boolean; created_at: string; updated_at: string;
};

type IngredientLotPayload = {
  ingredient_id: number; lot_code: string; supplier_name: string; purchased_at: string | null; expires_at: string | null; unit: string; unit_cost: string | null; total_cost: string | null; density_g_per_ml: string | null; notes: string;
};

type IngredientLotFormState = { id: number | null; ingredient_id: string; lot_code: string; supplier_name: string; purchased_at: string; expires_at: string; unit: string; unit_cost: string; total_cost: string; density_g_per_ml: string; notes: string };

type IngredientLotsState = { lots: IngredientLot[]; ingredients: Ingredient[]; formMode: IngredientLotFormMode; form: IngredientLotFormState };

type StockMovement = { id: number; ingredient_lot_id: number; ingredient_id: number; movement_type: string; quantity: string; unit: string; direction: string; reason: string; occurred_at: string; note: string; reference_type: string | null; reference_id: string | null; source: string; correction_of_movement_id: number | null; created_at: string };
type IngredientLotBalanceResponse = { ingredient_lot_id: number; quantity: string };
type StockMovementFormState = { ingredient_lot_id: string; movement_type: string; quantity: string; unit: string; occurred_at: string; reason: string; source: string; note: string };
type StockMovementsState = { lots: IngredientLot[]; ingredients: Ingredient[]; selectedLotId: number | null; balance: IngredientLotBalanceResponse | null; movements: StockMovement[]; form: StockMovementFormState; detailStatus: StockMovementLoadStatus };
type StockMovementPayload = { ingredient_lot_id: number; movement_type: string; quantity: string; unit: string; occurred_at: string | null; reason: string; source: string; note: string };

type IngredientsState = {
  items: Ingredient[];
  formMode: IngredientFormMode;
  form: IngredientFormState;
};

type RecipeTemplate = {
  id: number;
  name: string;
  product_type: string;
  description: string;
  notes: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

type RecipeVersion = {
  id: number;
  recipe_template_id: number;
  version_number: number;
  status: string;
  title: string;
  target_batch_size_value: string | null;
  target_batch_size_unit: string | null;
  notes: string;
  change_note: string;
  created_from_version_id: number | null;
  created_at: string;
  updated_at: string;
};

type RecipeIngredientLine = {
  id: number;
  recipe_version_id: number;
  ingredient_id: number;
  position: number;
  phase: string;
  amount_value: string;
  amount_unit: string;
  notes: string;
  created_at: string;
};

type RecipeVersionDetail = { version: RecipeVersion; ingredients: RecipeIngredientLine[] };
type RecipeTemplatePayload = Pick<RecipeTemplate, 'name' | 'product_type' | 'description' | 'notes'>;
type RecipeLineForm = { ingredient_id: string; amount_value: string; amount_unit: string; phase: string; notes: string };
type RecipeVersionForm = { title: string; status: string; target_batch_size_value: string; target_batch_size_unit: string; notes: string; change_note: string; ingredients: RecipeLineForm[] };

type RecipeCalculationIssue = { severity: string; code: string; field: string | null; message: string; next_action: string | null };
type RecipeCalculationLine = { recipe_ingredient_id: number; position: number; phase: string; ingredient_id: number; ingredient_name: string; source_amount_value: string; source_amount_unit: string; calculated_amount_value: string | null; calculated_amount_unit: string | null; calculation_note: string };
type RecipeCalculationTotal = { unit: string; total_value: string };
type RecipeCalculationResult = { recipe_version_id: number; recipe_template_id: number; recipe_name: string; version_number: number; status: string; target_batch_size_value: string | null; target_batch_size_unit: string | null; percent_total: string; can_calculate: boolean; issues: RecipeCalculationIssue[]; lines: RecipeCalculationLine[]; totals_by_unit: RecipeCalculationTotal[]; generated_at: string };

type RecipesState = {
  templates: RecipeTemplate[];
  selectedTemplate: RecipeTemplate | null;
  versions: RecipeVersion[];
  selectedVersionDetail: RecipeVersionDetail | null;
  ingredients: Ingredient[];
  templateForm: RecipeTemplatePayload;
  versionForm: RecipeVersionForm;
  calculation: RecipeCalculationResult | null;
  calculationTargetValue: string;
  calculationTargetUnit: string;
};


const navigationItems = ['Главная','Компоненты','Партии','Движения склада','Рецепты','Клиенты','Заказы','Склад','Тара','Закупки','Производство','Импорт','Отчеты','Настройки','Помощь'];
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
let ingredientLotsStatus: IngredientLotsStatus = 'idle';
let ingredientLotsState: IngredientLotsState = { lots: [], ingredients: [], formMode: 'create', form: emptyIngredientLotForm() };
let ingredientLotsError = '';
let ingredientLotsMessage = '';
let stockMovementsStatus: StockMovementsStatus = 'idle';
let stockMovementsState: StockMovementsState = { lots: [], ingredients: [], selectedLotId: null, balance: null, movements: [], form: emptyStockMovementForm(), detailStatus: 'idle' };
let stockMovementsError = '';
let stockMovementsMessage = '';
let recipesStatus: RecipesStatus = 'idle';
let recipesError = '';
let recipesMessage = '';
let calculationStatus: CalculationStatus = 'idle';
let calculationError = '';
let recipesState: RecipesState = { templates: [], selectedTemplate: null, versions: [], selectedVersionDetail: null, ingredients: [], templateForm: emptyRecipeTemplateForm(), versionForm: emptyRecipeVersionForm(), calculation: null, calculationTargetValue: '', calculationTargetUnit: 'g' };

function sectionFromLocation() {
  if (window.location.pathname === '/inventory') return 'Склад';
  if (window.location.pathname === '/ingredients') return 'Компоненты';
  if (window.location.pathname === '/ingredient-lots') return 'Партии';
  if (window.location.pathname === '/stock-movements') return 'Движения склада';
  if (window.location.pathname === '/recipes') return 'Рецепты';
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
        ${activeSection === 'Главная' ? dashboardPlaceholder() : activeSection === 'Склад' ? inventoryPage() : activeSection === 'Компоненты' ? ingredientsPage() : activeSection === 'Партии' ? ingredientLotsPage() : activeSection === 'Движения склада' ? stockMovementsPage() : activeSection === 'Рецепты' ? recipesPage() : sectionPlaceholder(activeSection)}
      </main>
    </div>`;
  bindEvents(root);
}

function bindEvents(root: HTMLElement) {
  root.querySelector<HTMLImageElement>('.brand-mark img')?.addEventListener('error', (event) => { (event.currentTarget as HTMLImageElement).hidden = true; });
  root.querySelectorAll<HTMLButtonElement>('.nav-item').forEach((button) => {
    button.addEventListener('click', () => {
      activeSection = button.dataset.section ?? 'Главная';
      window.history.pushState({}, '', activeSection === 'Склад' ? '/inventory' : activeSection === 'Компоненты' ? '/ingredients' : activeSection === 'Партии' ? '/ingredient-lots' : activeSection === 'Движения склада' ? '/stock-movements' : activeSection === 'Рецепты' ? '/recipes' : '/');
      if (activeSection === 'Склад') loadInventory();
      if (activeSection === 'Компоненты') loadIngredients();
      if (activeSection === 'Партии') loadIngredientLots();
      if (activeSection === 'Движения склада') loadStockMovements();
      if (activeSection === 'Рецепты') loadRecipes();
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
  root.querySelector<HTMLButtonElement>('[data-action="reload-ingredient-lots"]')?.addEventListener('click', () => loadIngredientLots(true));
  root.querySelector<HTMLButtonElement>('[data-action="new-ingredient-lot"]')?.addEventListener('click', () => { ingredientLotsState.formMode = 'create'; ingredientLotsState.form = emptyIngredientLotForm(); ingredientLotsMessage = ''; ingredientLotsError = ''; render(); });
  root.querySelectorAll<HTMLButtonElement>('[data-action="edit-ingredient-lot"]').forEach((button) => button.addEventListener('click', () => startEditIngredientLot(Number(button.dataset.id))));
  root.querySelectorAll<HTMLButtonElement>('[data-action="deactivate-ingredient-lot"]').forEach((button) => button.addEventListener('click', () => deactivateIngredientLot(Number(button.dataset.id))));
  root.querySelector<HTMLFormElement>('[data-form="ingredient-lot"]')?.addEventListener('submit', submitIngredientLotForm);
  root.querySelector<HTMLButtonElement>('[data-action="reload-stock-movements"]')?.addEventListener('click', () => loadStockMovements(true));
  root.querySelector<HTMLSelectElement>('[data-action="select-stock-lot"]')?.addEventListener('change', (event) => selectStockMovementLot(Number((event.currentTarget as HTMLSelectElement).value)));
  root.querySelector<HTMLFormElement>('[data-form="stock-movement"]')?.addEventListener('submit', submitStockMovementForm);
  root.querySelector<HTMLButtonElement>('[data-action="reload-recipes"]')?.addEventListener('click', () => loadRecipes(true));
  root.querySelector<HTMLFormElement>('[data-form="recipe-template"]')?.addEventListener('submit', submitRecipeTemplateForm);
  root.querySelector<HTMLFormElement>('[data-form="recipe-version"]')?.addEventListener('submit', submitRecipeVersionForm);
  root.querySelector<HTMLFormElement>('[data-form="recipe-calculation"]')?.addEventListener('submit', submitCalculationForm);
  root.querySelectorAll<HTMLButtonElement>('[data-action="open-recipe"]').forEach((button) => button.addEventListener('click', () => openRecipeTemplate(Number(button.dataset.id))));
  root.querySelectorAll<HTMLButtonElement>('[data-action="open-version"]').forEach((button) => button.addEventListener('click', () => openRecipeVersion(Number(button.dataset.id))));
  root.querySelector<HTMLButtonElement>('[data-action="add-recipe-line"]')?.addEventListener('click', addRecipeLine);
  root.querySelectorAll<HTMLButtonElement>('[data-action="remove-recipe-line"]').forEach((button) => button.addEventListener('click', () => removeRecipeLine(Number(button.dataset.index))));
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

function ingredientLotsPage() {
  if (ingredientLotsStatus === 'idle' || ingredientLotsStatus === 'loading') return `<section class="card"><p class="card-kicker">Партии компонентов</p><h2>Загружаем партии…</h2><p>Получаем партии компонентов из локального API.</p></section>`;
  if (ingredientLotsStatus === 'error') return `<section class="card error-card"><p class="card-kicker">Партии компонентов</p><h2>Не удалось загрузить партии</h2><p>${ingredientLotsError || 'Локальный API временно недоступен.'}</p><p class="next-step">Проверьте, что приложение запущено полностью, и попробуйте обновить раздел.</p><button class="primary-action" type="button" data-action="reload-ingredient-lots">Повторить загрузку</button></section>`;
  return `<div class="catalog-layout"><section class="card catalog-intro"><div><p class="card-kicker">Партии компонентов</p><h2>Партии закупленных компонентов</h2><p>Здесь хранится паспорт партии: компонент, поставщик, срок годности, цена и единица учета. Остаток не редактируется здесь и считается отдельными движениями склада.</p></div><button class="secondary-action" type="button" data-action="new-ingredient-lot">Очистить форму</button></section>${ingredientLotsMessage ? `<p class="page-message">${ingredientLotsMessage}</p>` : ''}${ingredientLotsError ? `<p class="page-message error-message">${ingredientLotsError}</p>` : ''}${ingredientLotForm()}${ingredientLotList()}</div>`;
}

function ingredientLotForm() {
  const form = ingredientLotsState.form;
  const isEdit = ingredientLotsState.formMode === 'edit';
  const hasIngredients = ingredientLotsState.ingredients.length > 0;
  return `<section class="card form-card"><p class="card-kicker">${isEdit ? 'Редактирование' : 'Создание'}</p><h2>${isEdit ? 'Изменить партию' : 'Создать партию компонента'}</h2><p class="next-step">Количество партии добавляется отдельным движением склада. Здесь хранится информация о партии: поставщик, срок годности, цена и единица учета.</p><form data-form="ingredient-lot" class="ingredient-form"><div class="form-grid"><label>Компонент<select name="ingredient_id" required ${hasIngredients ? '' : 'disabled'}><option value="">Выберите компонент</option>${ingredientLotsState.ingredients.map((item) => `<option value="${item.id}" ${String(item.id) === form.ingredient_id ? 'selected' : ''}>${escapeHtml(item.name)}</option>`).join('')}</select></label><label>Код партии<input name="lot_code" maxlength="120" value="${escapeHtml(form.lot_code)}" placeholder="Например, LOT-2026-01" /></label><label>Поставщик<input name="supplier_name" maxlength="160" value="${escapeHtml(form.supplier_name)}" placeholder="Необязательно" /></label><label>Единица учета<select name="unit">${lotUnitOptions(form.unit)}</select></label><label>Цена за единицу<input name="unit_cost" inputmode="decimal" value="${escapeHtml(form.unit_cost)}" placeholder="Например, 12.50" /></label><label>Общая стоимость<input name="total_cost" inputmode="decimal" value="${escapeHtml(form.total_cost)}" placeholder="Необязательно" /></label><label>Плотность<input name="density_g_per_ml" inputmode="decimal" value="${escapeHtml(form.density_g_per_ml)}" placeholder="Например, 0.950" /></label><label>Дата покупки<input name="purchased_at" type="date" value="${escapeHtml(form.purchased_at)}" /></label><label>Срок годности<input name="expires_at" type="date" value="${escapeHtml(form.expires_at)}" /></label><label class="full-span">Заметки<textarea name="notes" rows="3" maxlength="1200" placeholder="Короткие рабочие заметки о партии">${escapeHtml(form.notes)}</textarea></label></div><div class="actions"><button class="primary-action" type="submit" ${hasIngredients ? '' : 'disabled'}>${isEdit ? 'Сохранить изменения' : 'Создать партию'}</button>${isEdit ? '<button class="secondary-action" type="button" data-action="new-ingredient-lot">Отменить редактирование</button>' : ''}</div>${hasIngredients ? '' : '<p class="next-step">Сначала создайте активный компонент в разделе «Компоненты», затем вернитесь к партиям.</p>'}</form></section>`;
}

function ingredientLotList() {
  if (ingredientLotsState.lots.length === 0) return `<section class="card empty-card"><h2>Пока нет партий компонентов</h2><p>Создайте партию, чтобы указать поставщика, срок годности и цену закупки.</p><p class="next-step">Остаток считается по движениям склада. Чтобы добавить количество, используйте движение склада — это будет отдельный шаг.</p></section>`;
  return `<section class="card data-card"><p class="card-kicker">Список</p><h2>Партии компонентов</h2><div class="table-wrap"><table><thead><tr><th>Компонент</th><th>Партия</th><th>Поставщик</th><th>Ед. учета</th><th>Цена за единицу</th><th>Плотность</th><th>Дата покупки</th><th>Срок годности</th><th>Статус</th><th>Действия</th></tr></thead><tbody>${ingredientLotsState.lots.map((lot) => `<tr><td><strong>${escapeHtml(lotIngredientName(lot.ingredient_id))}</strong></td><td>${escapeHtml(lot.lot_code || 'Без номера')}<small>${escapeHtml(lot.notes || '')}</small></td><td>${escapeHtml(lot.supplier_name || 'Не указан')}</td><td>${unitLabel(lot.unit)}</td><td>${lot.unit_cost ? escapeHtml(lot.unit_cost) : 'Не указана'}</td><td>${lot.density_g_per_ml ? `${escapeHtml(lot.density_g_per_ml)} г/мл` : 'Не указана'}</td><td>${formatDate(lot.purchased_at)}</td><td>${formatDate(lot.expires_at)}</td><td><span class="pill ${lotStatusClass(lot)}">${lotStatusLabel(lot)}</span></td><td><div class="row-actions"><button class="secondary-action compact" type="button" data-action="edit-ingredient-lot" data-id="${lot.id}">Изменить</button>${lot.is_active ? `<button class="secondary-action compact danger-action" type="button" data-action="deactivate-ingredient-lot" data-id="${lot.id}">Деактивировать</button>` : ''}</div></td></tr>`).join('')}</tbody></table></div><p class="next-step">Остаток партии не редактируется в этой таблице: он будет считаться по движениям склада.</p></section>`;
}


function stockMovementsPage() {
  if (stockMovementsStatus === 'idle' || stockMovementsStatus === 'loading') return `<section class="card"><p class="card-kicker">Движения склада</p><h2>Загружаем движения…</h2><p>Получаем партии компонентов и историю движений из локального API.</p></section>`;
  if (stockMovementsStatus === 'error') return `<section class="card error-card"><p class="card-kicker">Движения склада</p><h2>Не удалось загрузить движения склада</h2><p>${stockMovementsError || 'Локальный API временно недоступен.'}</p><p class="next-step">Проверьте, что приложение запущено полностью, и попробуйте обновить раздел.</p><button class="primary-action" type="button" data-action="reload-stock-movements">Повторить загрузку</button></section>`;
  if (stockMovementsState.lots.length === 0) return `<div class="catalog-layout"><section class="card catalog-intro"><div><p class="card-kicker">Движения склада</p><h2>История движений компонентов</h2><p>Остаток партии считается по движениям. Старые движения не редактируются, чтобы история склада оставалась честной.</p></div><button class="secondary-action" type="button" data-action="reload-stock-movements">Обновить</button></section><section class="card empty-card"><h2>Пока нет партий для движений</h2><p>Сначала создайте компонент и партию. После этого можно будет добавить приход или списание.</p><p class="next-step">Текущий остаток нельзя ввести вручную: он появится после первого движения склада.</p></section></div>`;
  return `<div class="catalog-layout"><section class="card catalog-intro"><div><p class="card-kicker">Движения склада</p><h2>Движения склада</h2><p>Остаток партии считается по движениям. Старые движения не редактируются, чтобы история склада оставалась честной.</p></div><button class="secondary-action" type="button" data-action="reload-stock-movements">Обновить</button></section>${stockMovementsMessage ? `<p class="page-message">${stockMovementsMessage}</p>` : ''}${stockMovementsError ? `<p class="page-message error-message">${stockMovementsError}</p>` : ''}${stockLotSelector()}${stockMovementForm()}${stockMovementHistory()}</div>`;
}

function stockLotSelector() {
  const selected = stockMovementsState.selectedLotId;
  return `<section class="card form-card"><p class="card-kicker">Партия</p><h2>Выберите партию компонента</h2><div class="form-grid"><label class="full-span">Партия<select data-action="select-stock-lot"><option value="">Выберите партию</option>${stockMovementsState.lots.map((lot) => `<option value="${lot.id}" ${lot.id === selected ? 'selected' : ''}>${escapeHtml(stockLotLabel(lot))}</option>`).join('')}</select></label></div>${stockMovementsState.detailStatus === 'loading' ? '<p class="next-step">Загружаем текущий остаток и историю выбранной партии…</p>' : ''}${stockBalanceCard()}</section>`;
}

function stockBalanceCard() {
  if (!stockMovementsState.selectedLotId) return `<p class="next-step">Выберите партию, чтобы увидеть backend-derived остаток и историю движений.</p>`;
  if (stockMovementsState.detailStatus === 'error') return `<p class="next-step error-message">Не удалось получить остаток или историю партии. Попробуйте обновить раздел.</p>`;
  if (!stockMovementsState.balance) return '';
  const lot = selectedStockLot();
  return `<div class="balance-card" aria-label="Текущий остаток"><span>Текущий остаток</span><strong>${escapeHtml(stockMovementsState.balance.quantity)} ${unitLabel(lot?.unit ?? '')}</strong><small>Остаток считается по истории движений.</small></div>`;
}

function stockMovementForm() {
  const lot = selectedStockLot();
  if (!lot) return '';
  const form = stockMovementsState.form;
  return `<section class="card form-card"><p class="card-kicker">Новое движение</p><h2>Добавить движение по выбранной партии</h2><p class="next-step">Для списаний и возвратов backend проверит, что остаток партии не станет отрицательным. История движений не редактируется и не удаляется.</p><form data-form="stock-movement" class="ingredient-form"><div class="form-grid"><label>Партия<input value="${escapeHtml(stockLotLabel(lot))}" readonly /></label><label>Тип движения<select name="movement_type">${movementTypeOptions(form.movement_type)}</select></label><label>Количество<input name="quantity" required inputmode="decimal" value="${escapeHtml(form.quantity)}" placeholder="Например, 100 или 12.500" /></label><label>Единица<input name="unit" value="${unitLabel(lot.unit)}" readonly /></label><label>Дата движения<input name="occurred_at" type="datetime-local" value="${escapeHtml(form.occurred_at)}" /></label><label>Источник<select name="source"><option value="manual" ${form.source === 'manual' ? 'selected' : ''}>Вручную</option><option value="import" ${form.source === 'import' ? 'selected' : ''}>Импорт</option><option value="system" ${form.source === 'system' ? 'selected' : ''}>Система</option></select></label><label class="full-span">Причина<input name="reason" maxlength="240" value="${escapeHtml(form.reason)}" placeholder="Например, закупка, списание просрочки" /></label><label class="full-span">Заметки<textarea name="note" rows="3" maxlength="1200" placeholder="Необязательно">${escapeHtml(form.note)}</textarea></label></div><div class="actions"><button class="primary-action" type="submit">Создать движение</button></div></form></section>`;
}

function stockMovementHistory() {
  if (!stockMovementsState.selectedLotId) return '';
  if (stockMovementsState.movements.length === 0) return `<section class="card empty-card"><h2>Движений по партии пока нет</h2><p>Создайте приход, чтобы зафиксировать начальный остаток партии. Текущий остаток останется расчетным.</p></section>`;
  return `<section class="card data-card"><p class="card-kicker">История</p><h2>Движения выбранной партии</h2><div class="table-wrap"><table><thead><tr><th>Дата</th><th>Тип движения</th><th>Количество</th><th>Ед.</th><th>Причина</th><th>Источник</th><th>Заметки</th></tr></thead><tbody>${stockMovementsState.movements.map((movement) => `<tr><td>${formatDateTime(movement.occurred_at)}</td><td>${movementTypeLabel(movement.movement_type)}</td><td>${escapeHtml(movement.quantity)}</td><td>${unitLabel(movement.unit)}</td><td>${escapeHtml(movement.reason || 'Не указана')}</td><td>${sourceLabel(movement.source)}</td><td>${escapeHtml(movement.note || 'Без заметок')}</td></tr>`).join('')}</tbody></table></div><p class="next-step">Это журнал склада: старые движения не редактируются и не удаляются.</p></section>`;
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
function unitLabel(unit: string) { return ({ g: 'г', ml: 'мл', percent: '%', pcs: 'шт.' } as Record<string, string>)[unit] ?? escapeHtml(unit); }
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


function recipesPage() {
  if (recipesStatus === 'idle' || recipesStatus === 'loading') return `<section class="card"><p class="card-kicker">Рецепты</p><h2>Загружаем рецепты…</h2><p>Получаем шаблоны рецептов, версии и компоненты из локального API.</p></section>`;
  if (recipesStatus === 'error') return `<section class="card error-card"><p class="card-kicker">Рецепты</p><h2>Не удалось загрузить рецепты</h2><p>${recipesError || 'Локальный API временно недоступен.'}</p><p class="next-step">Проверьте, что приложение запущено полностью, и попробуйте обновить раздел.</p><button class="primary-action" type="button" data-action="reload-recipes">Повторить загрузку</button></section>`;
  return `<div class="recipes-layout"><section class="card recipes-intro"><div><p class="card-kicker">Рецепты</p><h2>Рабочее пространство рецептов</h2><p>Создавайте базовые рецепты и новые версии состава. Уже созданные версии здесь только просматриваются и рассчитываются — история не редактируется.</p></div><button class="secondary-action" type="button" data-action="reload-recipes">Обновить</button></section>${recipesMessage ? `<p class="page-message">${recipesMessage}</p>` : ''}${recipesError ? `<p class="page-message error-message">${recipesError}</p>` : ''}<div class="recipe-columns"><div>${recipeTemplateForm()}${recipeTemplateList()}</div><div>${recipeDetailPanel()}</div></div></div>`;
}
function recipeTemplateForm() { const f = recipesState.templateForm; return `<section class="card form-card"><p class="card-kicker">Новый рецепт</p><h2>Создать рецепт</h2><form data-form="recipe-template" class="ingredient-form"><div class="form-grid"><label>Название рецепта<input name="name" required maxlength="160" value="${escapeHtml(f.name)}" placeholder="Например, базовый дневной крем" /></label><label>Тип продукта<input name="product_type" maxlength="120" value="${escapeHtml(f.product_type)}" placeholder="Крем, гель, тоник…" /></label><label class="full-span">Описание<textarea name="description" rows="3" maxlength="1200">${escapeHtml(f.description)}</textarea></label><label class="full-span">Заметки<textarea name="notes" rows="3" maxlength="1200">${escapeHtml(f.notes)}</textarea></label></div><div class="actions"><button class="primary-action" type="submit">Создать рецепт</button></div></form></section>`; }
function recipeTemplateList() { if (recipesState.templates.length === 0) return `<section class="card empty-card"><h2>Пока нет рецептов</h2><p>Пока нет рецептов. Создайте первый рецепт, чтобы хранить составы и версии.</p><p class="next-step">Следующее действие: заполните форму «Создать рецепт».</p></section>`; return `<section class="card data-card"><p class="card-kicker">Список</p><h2>Рецепты</h2><div class="recipe-list">${recipesState.templates.map((t)=>`<article class="recipe-list-item ${recipesState.selectedTemplate?.id===t.id?'selected':''}"><div><strong>${escapeHtml(t.name)}</strong><small>${escapeHtml(t.product_type || 'Тип продукта не указан')} · <span class="pill ${t.is_active?'success':'muted'}">${t.is_active?'Активен':'Неактивен'}</span></small></div><button class="secondary-action compact" type="button" data-action="open-recipe" data-id="${t.id}">Открыть</button></article>`).join('')}</div></section>`; }
function recipeDetailPanel() { const template = recipesState.selectedTemplate; if (!template) return `<section class="card empty-card"><h2>Выберите рецепт</h2><p>Откройте рецепт из списка, чтобы увидеть версии, состав и расчет.</p><p class="next-step">Исторические версии не редактируются: для изменений создается новая версия.</p></section>`; return `<div class="recipe-detail-stack"><section class="card"><p class="card-kicker">Рецепт</p><h2>${escapeHtml(template.name)}</h2><p><strong>Тип:</strong> ${escapeHtml(template.product_type || 'не указан')}</p><p>${escapeHtml(template.description || 'Описание пока не заполнено.')}</p>${template.notes ? `<p class="next-step">${escapeHtml(template.notes)}</p>` : ''}<span class="pill ${template.is_active?'success':'muted'}">${template.is_active?'Активен':'Неактивен'}</span></section>${recipeVersionsList()}${recipeVersionForm()}${recipeVersionDetailPanel()}</div>`; }
function recipeVersionsList() { if (recipesState.versions.length === 0) return `<section class="card empty-card"><h2>Версий пока нет</h2><p>Создайте первую версию, чтобы сохранить состав рецепта.</p></section>`; return `<section class="card data-card"><p class="card-kicker">Версии</p><h2>Версии рецепта</h2><div class="table-wrap"><table><thead><tr><th>Версия</th><th>Статус</th><th>Заголовок</th><th>Партия</th><th>Создана</th><th>Действие</th></tr></thead><tbody>${recipesState.versions.map((v)=>`<tr><td>№${v.version_number}</td><td><span class="pill ${versionStatusClass(v.status)}">${versionStatusLabel(v.status)}</span></td><td>${escapeHtml(v.title || 'Без заголовка')}</td><td>${batchLabel(v.target_batch_size_value, v.target_batch_size_unit)}</td><td>${formatDateTime(v.created_at)}</td><td><button class="secondary-action compact" type="button" data-action="open-version" data-id="${v.id}">Открыть</button></td></tr>`).join('')}</tbody></table></div></section>`; }
function recipeVersionForm() { const f=recipesState.versionForm; return `<section class="card form-card"><p class="card-kicker">Новая версия</p><h2>Создать версию</h2><form data-form="recipe-version" class="ingredient-form"><div class="form-grid"><label>Заголовок версии<input name="title" maxlength="160" value="${escapeHtml(f.title)}" placeholder="Например, v1 с ниацинамидом" /></label><label>Статус<select name="status">${['draft','active','archived'].map((x)=>`<option value="${x}" ${f.status===x?'selected':''}>${versionStatusLabel(x)}</option>`).join('')}</select></label><label>Размер партии<input name="target_batch_size_value" inputmode="decimal" value="${escapeHtml(f.target_batch_size_value)}" placeholder="Например, 100" /></label><label>Единица партии<select name="target_batch_size_unit">${['g','ml','pcs'].map((x)=>`<option value="${x}" ${f.target_batch_size_unit===x?'selected':''}>${unitLabel(x)}</option>`).join('')}</select></label><label class="full-span">Заметки<textarea name="notes" rows="2">${escapeHtml(f.notes)}</textarea></label><label class="full-span">Что изменилось<textarea name="change_note" rows="2">${escapeHtml(f.change_note)}</textarea></label></div><h3>Состав</h3><div class="recipe-lines">${f.ingredients.map(recipeLineForm).join('')}</div><div class="actions"><button class="secondary-action" type="button" data-action="add-recipe-line">Добавить строку</button><button class="primary-action" type="submit">Создать версию</button></div></form></section>`; }
function recipeLineForm(line: RecipeLineForm, index: number) { return `<fieldset class="recipe-line"><legend>Строка ${index+1}</legend><label>Компонент<select name="ingredient_id_${index}" required><option value="">Выберите компонент</option>${recipesState.ingredients.map((i)=>`<option value="${i.id}" ${line.ingredient_id===String(i.id)?'selected':''}>${escapeHtml(i.name)}</option>`).join('')}</select></label><label>Количество<input name="amount_value_${index}" required inputmode="decimal" value="${escapeHtml(line.amount_value)}" placeholder="Например, 5" /></label><label>Единица<select name="amount_unit_${index}">${['g','ml','percent','pcs'].map((u)=>`<option value="${u}" ${line.amount_unit===u?'selected':''}>${unitLabel(u)}</option>`).join('')}</select></label><label>Фаза<input name="phase_${index}" value="${escapeHtml(line.phase)}" placeholder="Водная фаза" /></label><label class="full-span">Заметки<input name="notes_${index}" value="${escapeHtml(line.notes)}" placeholder="Необязательно" /></label>${recipesState.versionForm.ingredients.length>1?`<button class="secondary-action compact danger-action" type="button" data-action="remove-recipe-line" data-index="${index}">Убрать строку</button>`:''}</fieldset>`; }
function recipeVersionDetailPanel() { const d=recipesState.selectedVersionDetail; if (!d) return ''; const v=d.version; return `<section class="card data-card"><p class="card-kicker">Состав</p><h2>Версия №${v.version_number}</h2><p><strong>${escapeHtml(v.title || 'Без заголовка')}</strong> · ${versionStatusLabel(v.status)} · ${batchLabel(v.target_batch_size_value, v.target_batch_size_unit)}</p>${d.ingredients.length===0?'<p>В этой версии пока нет строк состава.</p>':`<div class="table-wrap"><table><thead><tr><th>№</th><th>Компонент</th><th>Количество</th><th>Фаза</th><th>Заметки</th></tr></thead><tbody>${d.ingredients.slice().sort((a,b)=>a.position-b.position).map((line)=>`<tr><td>${line.position}</td><td>${escapeHtml(ingredientName(line.ingredient_id))}</td><td>${escapeHtml(line.amount_value)} ${unitLabel(line.amount_unit)}</td><td>${escapeHtml(line.phase || 'Не указана')}</td><td>${escapeHtml(line.notes || 'Без заметок')}</td></tr>`).join('')}</tbody></table></div>`}${calculationPanel()}</section>`; }
function calculationPanel() { const c=recipesState.calculation; return `<div class="calculation-panel"><h3>Расчет</h3><form data-form="recipe-calculation" class="inline-form"><label>Целевой размер партии<input name="target_batch_size_value" inputmode="decimal" value="${escapeHtml(recipesState.calculationTargetValue)}" placeholder="Оставьте пустым для размера версии" /></label><label>Единица<select name="target_batch_size_unit"><option value="g" ${recipesState.calculationTargetUnit==='g'?'selected':''}>г</option><option value="ml" ${recipesState.calculationTargetUnit==='ml'?'selected':''}>мл</option></select></label><button class="primary-action" type="submit">Рассчитать</button></form>${calculationStatus==='loading'?'<p>Считаем на backend…</p>':''}${calculationError?`<p class="page-message error-message">${calculationError}</p>`:''}${c?calculationResult(c):'<p class="next-step">Нажмите «Рассчитать», чтобы получить строки, итоги и предупреждения из backend.</p>'}</div>`; }
function calculationResult(c: RecipeCalculationResult) { return `<div class="calculation-result"><p><strong>Можно рассчитать:</strong> ${c.can_calculate?'да':'нет'} · <strong>Сумма процентов:</strong> ${escapeHtml(c.percent_total)}%</p>${c.issues.length?`<h4>${c.issues.some((i)=>i.severity==='error')?'Нужно исправить':'Предупреждения'}</h4><ul class="issue-list">${c.issues.map((i)=>`<li class="${i.severity==='error'?'danger-text':'warning-text'}">${escapeHtml(i.message)}${i.next_action?` <small>${escapeHtml(i.next_action)}</small>`:''}</li>`).join('')}</ul>`:''}<h4>Состав</h4>${c.lines.length?`<div class="table-wrap"><table><thead><tr><th>Компонент</th><th>Исходно</th><th>Рассчитано</th><th>Фаза</th><th>Комментарий</th></tr></thead><tbody>${c.lines.map((l)=>`<tr><td>${escapeHtml(l.ingredient_name)}</td><td>${escapeHtml(l.source_amount_value)} ${unitLabel(l.source_amount_unit)}</td><td>${l.calculated_amount_value?`${escapeHtml(l.calculated_amount_value)} ${unitLabel(l.calculated_amount_unit || '')}`:'—'}</td><td>${escapeHtml(l.phase || 'Не указана')}</td><td>${escapeHtml(l.calculation_note || '')}</td></tr>`).join('')}</tbody></table></div>`:'<p>Backend не вернул расчетных строк.</p>'}<h4>Итого по единицам</h4>${c.totals_by_unit.length?`<ul>${c.totals_by_unit.map((t)=>`<li>${escapeHtml(t.total_value)} ${unitLabel(t.unit)}</li>`).join('')}</ul>`:'<p>Итоги пока не рассчитаны.</p>'}</div>`; }

function emptyIngredientLotForm(): IngredientLotFormState { return { id: null, ingredient_id: '', lot_code: '', supplier_name: '', purchased_at: '', expires_at: '', unit: 'g', unit_cost: '', total_cost: '', density_g_per_ml: '', notes: '' }; }
function lotUnitOptions(current: string) { return ['g','ml','pcs'].map((value) => `<option value="${value}" ${value === current ? 'selected' : ''}>${unitLabel(value)}</option>`).join(''); }
function lotIngredientName(id: number) { return ingredientLotsState.ingredients.find((ingredient) => ingredient.id === id)?.name ?? 'Компонент'; }
function lotStatusLabel(lot: IngredientLot) { if (!lot.is_active) return 'Неактивна'; const status = expirationStatus(lot.expires_at); return status ?? 'Активна'; }
function lotStatusClass(lot: IngredientLot) { if (!lot.is_active) return 'muted'; const status = expirationStatus(lot.expires_at); if (status === 'Просрочена') return 'danger'; if (status === 'Скоро истекает') return 'warning'; if (status === 'Без срока годности') return 'muted'; return 'success'; }
function expirationStatus(value: string | null) { if (!value) return 'Без срока годности'; const today = new Date(); today.setHours(0, 0, 0, 0); const expires = new Date(`${value}T00:00:00`); const days = Math.ceil((expires.getTime() - today.getTime()) / 86400000); if (days < 0) return 'Просрочена'; if (days <= 30) return 'Скоро истекает'; return null; }
function ingredientLotPayloadFromForm(form: HTMLFormElement): IngredientLotPayload { const data = new FormData(form); const nullable = (name: string) => { const value = String(data.get(name) ?? '').trim(); return value || null; }; return { ingredient_id: Number(data.get('ingredient_id')), lot_code: String(data.get('lot_code') ?? '').trim(), supplier_name: String(data.get('supplier_name') ?? '').trim(), purchased_at: nullable('purchased_at'), expires_at: nullable('expires_at'), unit: String(data.get('unit') ?? 'g'), unit_cost: nullable('unit_cost'), total_cost: nullable('total_cost'), density_g_per_ml: nullable('density_g_per_ml'), notes: String(data.get('notes') ?? '').trim() }; }

function emptyIngredientForm(): IngredientFormState { return { id: null, name: '', category: 'other', default_unit: 'g', density_g_per_ml: null, notes: '', inci_name: '', supplier_hint: '', allergen_note: '', usage_note: '' }; }
function categoryLabel(category: string) { return ({ oil: 'Масло', butter: 'Баттер', wax: 'Воск', emulsifier: 'Эмульгатор', humectant: 'Увлажнитель', active: 'Актив', preservative: 'Консервант', fragrance: 'Отдушка', essential_oil: 'Эфирное масло', colorant: 'Краситель', water_phase: 'Водная фаза', additive: 'Добавка', other: 'Другое' } as Record<string, string>)[category] ?? category; }
function categoryOptions(current: string) { return ['oil','butter','wax','emulsifier','humectant','active','preservative','fragrance','essential_oil','colorant','water_phase','additive','other'].map((value) => `<option value="${value}" ${value === current ? 'selected' : ''}>${categoryLabel(value)}</option>`).join(''); }
function unitOptions(current: string) { return ['g','ml','percent','pcs'].map((value) => `<option value="${value}" ${value === current ? 'selected' : ''}>${unitLabel(value)}</option>`).join(''); }
function ingredientPayloadFromForm(form: HTMLFormElement): IngredientPayload { const data = new FormData(form); const density = String(data.get('density_g_per_ml') ?? '').trim(); return { name: String(data.get('name') ?? '').trim(), category: String(data.get('category') ?? 'other'), default_unit: String(data.get('default_unit') ?? 'g'), density_g_per_ml: density || null, notes: String(data.get('notes') ?? '').trim(), inci_name: String(data.get('inci_name') ?? '').trim(), supplier_hint: String(data.get('supplier_hint') ?? '').trim(), allergen_note: String(data.get('allergen_note') ?? '').trim(), usage_note: String(data.get('usage_note') ?? '').trim() }; }

function emptyRecipeTemplateForm(): RecipeTemplatePayload { return { name: '', product_type: '', description: '', notes: '' }; }
function emptyRecipeLine(): RecipeLineForm { return { ingredient_id: '', amount_value: '', amount_unit: 'percent', phase: '', notes: '' }; }
function emptyRecipeVersionForm(): RecipeVersionForm { return { title: '', status: 'draft', target_batch_size_value: '', target_batch_size_unit: 'g', notes: '', change_note: '', ingredients: [emptyRecipeLine()] }; }
function versionStatusLabel(status: string) { return ({ draft: 'Черновик', active: 'Активная', archived: 'Архивная' } as Record<string,string>)[status] ?? status; }
function versionStatusClass(status: string) { return status === 'active' ? 'success' : status === 'archived' ? 'muted' : 'warning'; }
function batchLabel(value: string | null, unit: string | null) { return value && unit ? `${escapeHtml(value)} ${unitLabel(unit)}` : 'Не указан'; }
function formatDateTime(value: string) { return value ? new Intl.DateTimeFormat('ru-RU', { dateStyle: 'short', timeStyle: 'short' }).format(new Date(value)) : 'Не указана'; }
function ingredientName(id: number) { return recipesState.ingredients.find((i)=>i.id===id)?.name ?? 'Компонент'; }
function addRecipeLine() { saveVersionFormFromDom(); recipesState.versionForm.ingredients.push(emptyRecipeLine()); render(); }
function removeRecipeLine(index: number) { saveVersionFormFromDom(); recipesState.versionForm.ingredients.splice(index, 1); if (recipesState.versionForm.ingredients.length === 0) recipesState.versionForm.ingredients.push(emptyRecipeLine()); render(); }
function saveVersionFormFromDom() { const form=document.querySelector<HTMLFormElement>('[data-form="recipe-version"]'); if (!form) return; recipesState.versionForm = recipeVersionFormFromForm(form); }
function recipeTemplatePayloadFromForm(form: HTMLFormElement): RecipeTemplatePayload { const data = new FormData(form); return { name: String(data.get('name') ?? '').trim(), product_type: String(data.get('product_type') ?? '').trim(), description: String(data.get('description') ?? '').trim(), notes: String(data.get('notes') ?? '').trim() }; }
function recipeVersionFormFromForm(form: HTMLFormElement): RecipeVersionForm { const data = new FormData(form); const ingredients = recipesState.versionForm.ingredients.map((_, index) => ({ ingredient_id: String(data.get(`ingredient_id_${index}`) ?? ''), amount_value: String(data.get(`amount_value_${index}`) ?? '').trim(), amount_unit: String(data.get(`amount_unit_${index}`) ?? 'percent'), phase: String(data.get(`phase_${index}`) ?? '').trim(), notes: String(data.get(`notes_${index}`) ?? '').trim() })); return { title: String(data.get('title') ?? '').trim(), status: String(data.get('status') ?? 'draft'), target_batch_size_value: String(data.get('target_batch_size_value') ?? '').trim(), target_batch_size_unit: String(data.get('target_batch_size_unit') ?? 'g'), notes: String(data.get('notes') ?? '').trim(), change_note: String(data.get('change_note') ?? '').trim(), ingredients }; }
function recipeVersionPayload(form: RecipeVersionForm) { return { title: form.title, status: form.status, target_batch_size_value: form.target_batch_size_value || null, target_batch_size_unit: form.target_batch_size_value ? form.target_batch_size_unit : null, notes: form.notes, change_note: form.change_note, ingredients: form.ingredients.filter((line)=>line.ingredient_id && line.amount_value).map((line, index)=>({ ingredient_id: Number(line.ingredient_id), position: index + 1, phase: line.phase, amount_value: line.amount_value, amount_unit: line.amount_unit, notes: line.notes })) }; }

function startEditIngredient(id: number) { const item = ingredientsState.items.find((ingredient) => ingredient.id === id); if (!item) return; ingredientsState.formMode = 'edit'; ingredientsState.form = { id: item.id, name: item.name, category: item.category, default_unit: item.default_unit, density_g_per_ml: item.density_g_per_ml, notes: item.notes, inci_name: item.inci_name, supplier_hint: item.supplier_hint, allergen_note: item.allergen_note, usage_note: item.usage_note }; ingredientsMessage = ''; render(); }

function apiGet<T>(url: string): Promise<T> { return fetch(url).then((response) => { if (!response.ok) throw new Error('API request failed'); return response.json() as Promise<T>; }); }
function apiSend<T>(url: string, method: 'POST' | 'PUT', body?: unknown): Promise<T> { return fetch(url, { method, headers: body ? { 'Content-Type': 'application/json' } : undefined, body: body ? JSON.stringify(body) : undefined }).then((response) => { if (!response.ok) throw new Error('API request failed'); return response.json() as Promise<T>; }); }
function getIngredients() { return apiGet<{ ingredients: Ingredient[] }>('/api/ingredients'); }
function createIngredient(payload: IngredientPayload) { return apiSend<Ingredient>('/api/ingredients', 'POST', payload); }
function updateIngredient(id: number, payload: IngredientPayload) { return apiSend<Ingredient>(`/api/ingredients/${id}`, 'PUT', payload); }
function deactivateIngredientRequest(id: number) { return apiSend<Ingredient>(`/api/ingredients/${id}/deactivate`, 'POST'); }
function getIngredientLots() { return apiGet<{ lots: IngredientLot[] }>('/api/ingredient-lots'); }
function createIngredientLot(payload: IngredientLotPayload) { return apiSend<IngredientLot>('/api/ingredient-lots', 'POST', payload); }
function updateIngredientLot(id: number, payload: IngredientLotPayload) { return apiSend<IngredientLot>(`/api/ingredient-lots/${id}`, 'PUT', payload); }
function deactivateIngredientLotRequest(id: number) { return apiSend<IngredientLot>(`/api/ingredient-lots/${id}/deactivate`, 'POST'); }

function getRecipeTemplates() { return apiGet<{ recipe_templates: RecipeTemplate[] }>('/api/recipe-templates'); }
function createRecipeTemplate(payload: RecipeTemplatePayload) { return apiSend<RecipeTemplate>('/api/recipe-templates', 'POST', payload); }
function getRecipeTemplate(id: number) { return apiGet<RecipeTemplate>(`/api/recipe-templates/${id}`); }
function getRecipeVersions(templateId: number) { return apiGet<{ recipe_versions: RecipeVersion[] }>(`/api/recipe-templates/${templateId}/versions`); }
function createRecipeVersion(templateId: number, payload: ReturnType<typeof recipeVersionPayload>) { return apiSend<RecipeVersionDetail>(`/api/recipe-templates/${templateId}/versions`, 'POST', payload); }
function getRecipeVersionDetail(versionId: number) { return apiGet<RecipeVersionDetail>(`/api/recipe-versions/${versionId}`); }
function getRecipeCalculation(versionId: number, value?: string, unit?: string) { const params = new URLSearchParams(); if (value) { params.set('target_batch_size_value', value); params.set('target_batch_size_unit', unit || 'g'); } const query = params.toString(); return apiGet<RecipeCalculationResult>(`/api/recipe-versions/${versionId}/calculation${query ? `?${query}` : ''}`); }

function getStockMovementsByLot(lotId: number) { return apiGet<{ movements: StockMovement[] }>(`/api/ingredient-lots/${lotId}/movements`); }
function getIngredientLotBalance(lotId: number) { return apiGet<IngredientLotBalanceResponse>(`/api/ingredient-lots/${lotId}/balance`); }
function createStockMovement(payload: StockMovementPayload) { return apiSend<StockMovement>('/api/stock-movements', 'POST', payload); }

function getInventoryOverview() { return apiGet<InventoryOverview>('/api/inventory/overview'); }
function getIngredientLotBalances() { return apiGet<{ ingredient_lot_balances: IngredientLotBalance[] }>('/api/inventory/ingredient-lot-balances'); }
function getPackagingBalances() { return apiGet<{ packaging_balances: PackagingBalance[] }>('/api/inventory/packaging-balances'); }



function emptyStockMovementForm(): StockMovementFormState { return { ingredient_lot_id: '', movement_type: 'receipt', quantity: '', unit: '', occurred_at: '', reason: '', source: 'manual', note: '' }; }
function selectedStockLot() { return stockMovementsState.lots.find((lot) => lot.id === stockMovementsState.selectedLotId) ?? null; }
function stockLotLabel(lot: IngredientLot) { return `${lotIngredientNameForStock(lot.ingredient_id)} - ${lot.lot_code || 'без номера'} - ${lot.supplier_name || 'поставщик не указан'} - ${unitLabel(lot.unit)}`; }
function lotIngredientNameForStock(id: number) { return stockMovementsState.ingredients.find((item) => item.id === id)?.name ?? ingredientLotsState.ingredients.find((item) => item.id === id)?.name ?? 'Компонент'; }
function movementTypeLabel(type: string) { return ({ receipt: 'Приход', manual_adjustment_in: 'Корректировка +', manual_adjustment_out: 'Корректировка -', write_off: 'Списание', return_to_supplier: 'Возврат поставщику' } as Record<string,string>)[type] ?? escapeHtml(type); }
function movementTypeOptions(selected: string) { return ['receipt','manual_adjustment_in','manual_adjustment_out','write_off','return_to_supplier'].map((type) => `<option value="${type}" ${type === selected ? 'selected' : ''}>${movementTypeLabel(type)}</option>`).join(''); }
function sourceLabel(source: string) { return ({ manual: 'Вручную', import: 'Импорт', system: 'Система' } as Record<string,string>)[source] ?? escapeHtml(source); }
function stockMovementPayloadFromForm(form: HTMLFormElement): StockMovementPayload { const data = new FormData(form); const lot = selectedStockLot(); return { ingredient_lot_id: lot?.id ?? 0, movement_type: String(data.get('movement_type') ?? 'receipt'), quantity: String(data.get('quantity') ?? '').trim(), unit: lot?.unit ?? '', occurred_at: String(data.get('occurred_at') ?? '').trim() || null, reason: String(data.get('reason') ?? '').trim(), source: String(data.get('source') ?? 'manual'), note: String(data.get('note') ?? '').trim() }; }
function saveStockMovementFormFromDom() { const form = document.querySelector<HTMLFormElement>('[data-form="stock-movement"]'); if (!form) return; const payload = stockMovementPayloadFromForm(form); stockMovementsState.form = { ingredient_lot_id: String(payload.ingredient_lot_id), movement_type: payload.movement_type, quantity: payload.quantity, unit: payload.unit, occurred_at: payload.occurred_at ?? '', reason: payload.reason, source: payload.source, note: payload.note }; }

function loadStockMovements(force = false) {
  if (!force && (stockMovementsStatus === 'loading' || stockMovementsStatus === 'ready')) return;
  stockMovementsStatus = 'loading'; stockMovementsError = ''; render();
  Promise.all([getIngredientLots(), getIngredients()]).then(([lots, ingredients]) => {
    stockMovementsState.lots = lots.lots.filter((lot) => lot.is_active);
    stockMovementsState.ingredients = ingredients.ingredients;
    stockMovementsStatus = 'ready';
    if (!stockMovementsState.selectedLotId && stockMovementsState.lots.length > 0) stockMovementsState.selectedLotId = stockMovementsState.lots[0].id;
    render();
    if (stockMovementsState.selectedLotId) loadSelectedStockMovementLot(stockMovementsState.selectedLotId);
  }).catch(() => { stockMovementsStatus = 'error'; stockMovementsError = 'Не получилось получить партии компонентов из локального API.'; render(); });
}
function selectStockMovementLot(lotId: number) { saveStockMovementFormFromDom(); stockMovementsState.selectedLotId = lotId || null; stockMovementsState.form = { ...emptyStockMovementForm(), ingredient_lot_id: lotId ? String(lotId) : '' }; stockMovementsMessage = ''; stockMovementsError = ''; render(); if (lotId) loadSelectedStockMovementLot(lotId); }
function loadSelectedStockMovementLot(lotId: number) { stockMovementsState.detailStatus = 'loading'; stockMovementsState.balance = null; stockMovementsState.movements = []; render(); Promise.all([getIngredientLotBalance(lotId), getStockMovementsByLot(lotId)]).then(([balance, movements]) => { stockMovementsState.balance = balance; stockMovementsState.movements = movements.movements; stockMovementsState.detailStatus = 'ready'; render(); }).catch(() => { stockMovementsState.detailStatus = 'error'; stockMovementsError = 'Не удалось загрузить остаток или историю выбранной партии.'; render(); }); }
function submitStockMovementForm(event: SubmitEvent) { event.preventDefault(); const payload = stockMovementPayloadFromForm(event.currentTarget as HTMLFormElement); if (!payload.ingredient_lot_id) return; createStockMovement(payload).then(() => { stockMovementsMessage = 'Движение создано. Текущий остаток пересчитан backend по истории.'; stockMovementsError = ''; stockMovementsState.form = { ...emptyStockMovementForm(), ingredient_lot_id: String(payload.ingredient_lot_id) }; loadSelectedStockMovementLot(payload.ingredient_lot_id); }).catch(() => { stockMovementsMessage = ''; stockMovementsError = 'Не удалось создать движение. Проверьте количество, единицу партии и что списание не делает остаток отрицательным.'; render(); }); }

function loadRecipes(force = false) {
  if (!force && (recipesStatus === 'loading' || recipesStatus === 'ready')) return;
  recipesStatus = 'loading'; recipesError = ''; render();
  Promise.all([getRecipeTemplates(), getIngredients()])
    .then(([templates, ingredients]) => { recipesState.templates = templates.recipe_templates; recipesState.ingredients = ingredients.ingredients.filter((i)=>i.is_active); recipesStatus = 'ready'; render(); })
    .catch(() => { recipesStatus = 'error'; recipesError = 'Не получилось получить рецепты из локального API.'; render(); });
}
function openRecipeTemplate(id: number) {
  recipesError = ''; recipesMessage = '';
  Promise.all([getRecipeTemplate(id), getRecipeVersions(id)]).then(([template, versions]) => { recipesState.selectedTemplate = template; recipesState.versions = versions.recipe_versions; recipesState.selectedVersionDetail = null; recipesState.calculation = null; calculationStatus = 'idle'; render(); }).catch(() => { recipesError = 'Не удалось открыть рецепт. Попробуйте обновить страницу.'; render(); });
}
function openRecipeVersion(id: number) { recipesError = ''; calculationError = ''; getRecipeVersionDetail(id).then((detail)=>{ recipesState.selectedVersionDetail = detail; recipesState.calculation = null; recipesState.calculationTargetValue = detail.version.target_batch_size_value ?? ''; recipesState.calculationTargetUnit = detail.version.target_batch_size_unit === 'ml' ? 'ml' : 'g'; calculationStatus = 'idle'; render(); }).catch(()=>{ recipesError = 'Не удалось открыть версию рецепта.'; render(); }); }
function submitRecipeTemplateForm(event: SubmitEvent) { event.preventDefault(); const payload = recipeTemplatePayloadFromForm(event.currentTarget as HTMLFormElement); createRecipeTemplate(payload).then((template)=>{ recipesMessage = 'Рецепт создан.'; recipesError = ''; recipesState.templateForm = emptyRecipeTemplateForm(); return getRecipeTemplates().then((response)=>({template, response})); }).then(({template, response})=>{ recipesState.templates = response.recipe_templates; recipesStatus = 'ready'; openRecipeTemplate(template.id); }).catch(()=>{ recipesMessage = ''; recipesError = 'Не удалось создать рецепт. Проверьте название и попробуйте еще раз.'; recipesStatus = 'ready'; render(); }); }
function submitRecipeVersionForm(event: SubmitEvent) { event.preventDefault(); if (!recipesState.selectedTemplate) return; const form = recipeVersionFormFromForm(event.currentTarget as HTMLFormElement); recipesState.versionForm = form; createRecipeVersion(recipesState.selectedTemplate.id, recipeVersionPayload(form)).then((detail)=>{ recipesMessage = 'Новая версия рецепта создана. Исторические версии не изменялись.'; recipesError = ''; recipesState.versionForm = emptyRecipeVersionForm(); recipesState.selectedVersionDetail = detail; return getRecipeVersions(recipesState.selectedTemplate!.id); }).then((response)=>{ recipesState.versions = response.recipe_versions; recipesState.calculation = null; calculationStatus = 'idle'; render(); }).catch(()=>{ recipesMessage = ''; recipesError = 'Не удалось создать версию. Проверьте строки состава и попробуйте еще раз.'; render(); }); }
function submitCalculationForm(event: SubmitEvent) { event.preventDefault(); const detail = recipesState.selectedVersionDetail; if (!detail) return; const data = new FormData(event.currentTarget as HTMLFormElement); const value = String(data.get('target_batch_size_value') ?? '').trim(); const unit = String(data.get('target_batch_size_unit') ?? 'g'); recipesState.calculationTargetValue = value; recipesState.calculationTargetUnit = unit; calculationStatus = 'loading'; calculationError = ''; render(); getRecipeCalculation(detail.version.id, value, unit).then((result)=>{ recipesState.calculation = result; calculationStatus = 'ready'; render(); }).catch(()=>{ calculationStatus = 'error'; calculationError = 'Не удалось выполнить расчет. Проверьте размер партии и попробуйте еще раз.'; render(); }); }

function loadIngredientLots(force = false) {
  if (!force && (ingredientLotsStatus === 'loading' || ingredientLotsStatus === 'ready')) return;
  ingredientLotsStatus = 'loading'; ingredientLotsError = ''; render();
  Promise.all([getIngredientLots(), getIngredients()])
    .then(([lots, ingredients]) => { ingredientLotsState.lots = lots.lots; ingredientLotsState.ingredients = ingredients.ingredients.filter((i)=>i.is_active); ingredientLotsStatus = 'ready'; render(); })
    .catch(() => { ingredientLotsStatus = 'error'; ingredientLotsError = 'Не получилось получить партии компонентов из локального API.'; render(); });
}
function startEditIngredientLot(id: number) { const lot = ingredientLotsState.lots.find((item) => item.id === id); if (!lot) return; ingredientLotsState.formMode = 'edit'; ingredientLotsState.form = { id: lot.id, ingredient_id: String(lot.ingredient_id), lot_code: lot.lot_code, supplier_name: lot.supplier_name, purchased_at: lot.purchased_at ?? '', expires_at: lot.expires_at ?? '', unit: lot.unit, unit_cost: lot.unit_cost ?? '', total_cost: lot.total_cost ?? '', density_g_per_ml: lot.density_g_per_ml ?? '', notes: lot.notes }; ingredientLotsMessage = ''; render(); }
function submitIngredientLotForm(event: SubmitEvent) {
  event.preventDefault();
  const payload = ingredientLotPayloadFromForm(event.currentTarget as HTMLFormElement);
  const request = ingredientLotsState.formMode === 'edit' && ingredientLotsState.form.id ? updateIngredientLot(ingredientLotsState.form.id, payload) : createIngredientLot(payload);
  request.then(() => { ingredientLotsMessage = ingredientLotsState.formMode === 'edit' ? 'Партия сохранена. Остаток не изменялся.' : 'Партия создана. Количество добавляется отдельным движением склада.'; ingredientLotsError = ''; ingredientLotsState.formMode = 'create'; ingredientLotsState.form = emptyIngredientLotForm(); return getIngredientLots(); }).then((response) => { ingredientLotsState.lots = response.lots; ingredientLotsStatus = 'ready'; render(); }).catch(() => { ingredientLotsMessage = ''; ingredientLotsError = 'Не удалось сохранить партию. Проверьте обязательные поля и попробуйте еще раз.'; ingredientLotsStatus = 'ready'; render(); });
}
function deactivateIngredientLot(id: number) {
  const lot = ingredientLotsState.lots.find((item) => item.id === id);
  if (!lot || !window.confirm(`Деактивировать партию «${lot.lot_code || lotIngredientName(lot.ingredient_id)}»? Она не будет удалена из истории.`)) return;
  deactivateIngredientLotRequest(id).then(() => { ingredientLotsMessage = 'Партия деактивирована. История склада не изменялась.'; ingredientLotsError = ''; return getIngredientLots(); }).then((response) => { ingredientLotsState.lots = response.lots; ingredientLotsStatus = 'ready'; render(); }).catch(() => { ingredientLotsMessage = ''; ingredientLotsError = 'Не удалось деактивировать партию. Попробуйте еще раз.'; ingredientLotsStatus = 'ready'; render(); });
}

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

window.addEventListener('popstate', () => { activeSection = sectionFromLocation(); if (activeSection === 'Склад') loadInventory(); if (activeSection === 'Компоненты') loadIngredients(); if (activeSection === 'Партии') loadIngredientLots(); if (activeSection === 'Движения склада') loadStockMovements(); if (activeSection === 'Рецепты') loadRecipes(); render(); });
render();
fetch('/api/health').then((response) => { healthStatus = response.ok ? 'online' : 'offline'; render(); }).catch(() => { healthStatus = 'offline'; render(); });
loadOnboarding();
if (activeSection === 'Склад') loadInventory();
if (activeSection === 'Компоненты') loadIngredients();
if (activeSection === 'Партии') loadIngredientLots();
if (activeSection === 'Движения склада') loadStockMovements();
if (activeSection === 'Рецепты') loadRecipes();
