type HealthStatus = 'checking' | 'online' | 'offline';
type OnboardingStatus = 'loading' | 'ready' | 'unavailable';
type InventoryStatus = 'idle' | 'loading' | 'ready' | 'error';
type IngredientsStatus = 'idle' | 'loading' | 'ready' | 'error';
type CatalogSavingStatus = 'idle' | 'saving';
type CatalogCreateKind = 'category' | 'tag';
type CatalogOption = { id: number; name: string };
type CatalogControlState = { categorySearch: string; tagSearch: string; showAllTags: boolean };
type AssignmentDraft = { itemId: number | null; catalogCategoryId: number | null; catalogTagIds: number[] };
type CatalogStatusFilter = 'active' | 'archived' | 'all';
type CatalogBrowserFilters = { search: string; categoryId: number | 'none' | ''; tagIds: number[]; systemType: string; status: CatalogStatusFilter };
type IngredientLotsStatus = 'idle' | 'loading' | 'ready' | 'error';
type RecipesStatus = 'idle' | 'loading' | 'ready' | 'error';
type StockMovementsStatus = 'idle' | 'loading' | 'ready' | 'error';
type PackagingItemsStatus = 'idle' | 'loading' | 'ready' | 'error';
type CalculationStatus = 'idle' | 'loading' | 'ready' | 'error';
type IngredientFormMode = 'create' | 'edit';
type ClientFormMode = 'create' | 'edit';
type IngredientLotFormMode = 'create' | 'edit';
type PackagingItemFormMode = 'create' | 'edit';
type StockMovementLoadStatus = 'idle' | 'loading' | 'ready' | 'error';
type ClientsStatus = 'idle' | 'loading' | 'ready' | 'error';
type ClientRecipesStatus = 'idle' | 'loading' | 'ready' | 'error';
type ClientRecipeDetailStatus = 'idle' | 'loading' | 'ready' | 'error';

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

type Client = { id: number; full_name: string; phone: string; email: string; address: string; birthday: string | null; skin_notes: string; allergy_notes: string; preference_notes: string; contraindication_notes: string; notes: string; is_active: boolean; created_at: string; updated_at: string };
type ClientPayload = Pick<Client, 'full_name' | 'phone' | 'email' | 'address' | 'birthday' | 'skin_notes' | 'allergy_notes' | 'preference_notes' | 'contraindication_notes' | 'notes'>;
type ClientFormState = ClientPayload & { id: number | null };
type ClientsState = { items: Client[]; formMode: ClientFormMode; form: ClientFormState; includeInactive: boolean };

type ClientRecipe = { id: number; client_id: number; source_recipe_version_id: number; title: string; status: string; target_batch_size_value: string | null; target_batch_size_unit: string | null; personalization_notes: string; allergy_notes: string; preference_notes: string; contraindication_notes: string; notes: string; is_active: boolean; created_at: string; updated_at: string };
type ClientRecipeIngredient = { id: number; client_recipe_id: number; ingredient_id: number; source_recipe_ingredient_id: number | null; position: number; phase: string; amount_value: string; amount_unit: string; personalization_note: string; notes: string; created_at: string };
type ClientRecipeDetail = { client_recipe: ClientRecipe; ingredients: ClientRecipeIngredient[] };
type ClientRecipeFormState = { client_id: string; recipe_template_id: string; source_recipe_version_id: string; title: string; target_batch_size_value: string; target_batch_size_unit: string; personalization_notes: string; allergy_notes: string; preference_notes: string; contraindication_notes: string; notes: string };
type ClientRecipePayload = { client_id: number; source_recipe_version_id: number; title: string; target_batch_size_value: string | null; target_batch_size_unit: string | null; personalization_notes: string; allergy_notes: string; preference_notes: string; contraindication_notes: string; notes: string };
type ClientRecipesState = { items: ClientRecipe[]; clients: Client[]; templates: RecipeTemplate[]; versions: RecipeVersion[]; selectedTemplateId: number | null; selectedDetail: ClientRecipeDetail | null; form: ClientRecipeFormState; includeInactive: boolean; detailStatus: ClientRecipeDetailStatus };

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
  catalog_category_id: number | null;
  catalog_tag_ids: number[];
};

type CatalogCategory = { id: number; scope: string; parent_id: number | null; name: string; slug: string; sort_order: number; is_system: boolean; is_active: boolean; created_at: string; updated_at: string };
type CatalogTag = { id: number; scope: string; name: string; slug: string; color: string; is_active: boolean; created_at: string; updated_at: string };

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

type PackagingItem = {
  id: number;
  name: string;
  kind: string;
  unit: string;
  capacity_value: string | null;
  capacity_unit: string | null;
  material: string;
  supplier_hint: string;
  unit_cost: string | null;
  notes: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  catalog_category_id: number | null;
  catalog_tag_ids: number[];
};

type PackagingItemPayload = {
  name: string;
  kind: string;
  unit: string;
  capacity_value: string | null;
  capacity_unit: string | null;
  material: string;
  supplier_hint: string;
  unit_cost: string | null;
  notes: string;
};

type PackagingItemFormState = PackagingItemPayload & { id: number | null };
type PackagingItemsState = { items: PackagingItem[]; formMode: PackagingItemFormMode; form: PackagingItemFormState; catalogCategories: CatalogCategory[]; catalogTags: CatalogTag[]; catalogSaving: CatalogSavingStatus; catalogCreating: CatalogCreateKind | null; assignmentDraft: AssignmentDraft };


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
  catalogCategories: CatalogCategory[];
  catalogTags: CatalogTag[];
  catalogSaving: CatalogSavingStatus;
  catalogCreating: CatalogCreateKind | null;
  showCreateForm: boolean;
  filters: CatalogBrowserFilters;
  assignmentDraft: AssignmentDraft;
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
  catalog_category_id: number | null;
  catalog_tag_ids: number[];
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
type RecipeLineForm = { ingredient_id: string; position: string; phase: string; amount_value: string; amount_unit: string; notes: string };
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
  versionDetailStatus: 'idle' | 'loading' | 'ready' | 'error';
  ingredients: Ingredient[];
  templateForm: RecipeTemplatePayload;
  versionForm: RecipeVersionForm;
  calculation: RecipeCalculationResult | null;
  calculationTargetValue: string;
  calculationTargetUnit: string;
  catalogCategories: CatalogCategory[];
  catalogTags: CatalogTag[];
  catalogSaving: CatalogSavingStatus;
  catalogCreating: CatalogCreateKind | null;
};


type NavigationSection = 'Главная' | 'Рецепты' | 'Индивидуальные рецепты' | 'Клиенты' | 'Заказы' | 'Склад' | 'Компоненты' | 'Партии' | 'Движения сырья' | 'Тара' | 'Закупки' | 'Готовность' | 'Производство' | 'Импорт' | 'Отчеты' | 'Настройки' | 'Помощь';
type NavigationStatus = 'ready' | 'empty' | 'planned';
type NavigationItem = { label: string; section: NavigationSection; path: string; status: NavigationStatus };
type NavigationGroup = { title: string; items: NavigationItem[] };

const navigationGroups: NavigationGroup[] = [
  { title: 'Главная', items: [{ label: 'Обзор', section: 'Главная', path: '/', status: 'ready' }] },
  { title: 'Рецепты', items: [
    { label: 'Рецепты', section: 'Рецепты', path: '/recipes', status: 'empty' },
    { label: 'Индивидуальные рецепты', section: 'Индивидуальные рецепты', path: '/client-recipes', status: 'empty' },
  ] },
  { title: 'Клиенты', items: [
    { label: 'Клиенты', section: 'Клиенты', path: '/clients', status: 'empty' },
    { label: 'Заказы', section: 'Заказы', path: '/#orders', status: 'planned' },
  ] },
  { title: 'Склад', items: [
    { label: 'Обзор склада', section: 'Склад', path: '/inventory', status: 'ready' },
    { label: 'Компоненты', section: 'Компоненты', path: '/ingredients', status: 'empty' },
    { label: 'Приходы и партии', section: 'Партии', path: '/ingredient-lots', status: 'empty' },
    { label: 'Движения сырья', section: 'Движения сырья', path: '/stock-movements', status: 'empty' },
    { label: 'Тара', section: 'Тара', path: '/packaging-items', status: 'empty' },
    { label: 'Закупки', section: 'Закупки', path: '/#purchases', status: 'planned' },
  ] },
  { title: 'Производство', items: [
    { label: 'Готовность', section: 'Готовность', path: '/#production-readiness', status: 'planned' },
    { label: 'Производство', section: 'Производство', path: '/#production', status: 'planned' },
  ] },
  { title: 'Данные и настройки', items: [
    { label: 'Импорт', section: 'Импорт', path: '/#import', status: 'planned' },
    { label: 'Отчеты', section: 'Отчеты', path: '/#reports', status: 'planned' },
    { label: 'Настройки', section: 'Настройки', path: '/#settings', status: 'planned' },
    { label: 'Помощь', section: 'Помощь', path: '/#help', status: 'planned' },
  ] },
];
const stepLabels: Record<string, string> = {
  welcome: 'Познакомиться с рабочим пространством',
  data_location: 'Понять, где хранятся локальные данные',
  first_ingredient: 'Подготовить первый компонент',
  first_recipe: 'Подготовить первый рецепт',
  first_client: 'Подготовить первую карточку клиента',
  first_order: 'Подготовить первый заказ',
  first_backup: 'Запланировать первую резервную копию',
};

let activeSection: NavigationSection = sectionFromLocation();
const collapsedNavigationGroups = new Set<string>(navigationGroups.map((group) => group.title));
let healthStatus: HealthStatus = 'checking';
let onboardingStatus: OnboardingStatus = 'loading';
let onboardingState: OnboardingState | null = null;
let onboardingMessage = '';
let inventoryStatus: InventoryStatus = 'idle';
let inventoryState: InventoryState = { overview: null, ingredientLots: [], packagingItems: [] };
let inventoryError = '';
let clientsStatus: ClientsStatus = 'idle';
let clientsState: ClientsState = { items: [], formMode: 'create', form: emptyClientForm(), includeInactive: false };
let clientsError = '';
let clientsMessage = '';
let clientRecipesStatus: ClientRecipesStatus = 'idle';
let clientRecipesError = '';
let clientRecipesMessage = '';
let clientRecipesState: ClientRecipesState = { items: [], clients: [], templates: [], versions: [], selectedTemplateId: null, selectedDetail: null, form: emptyClientRecipeForm(), includeInactive: false, detailStatus: 'idle' };
let ingredientsStatus: IngredientsStatus = 'idle';
let ingredientsState: IngredientsState = { items: [], formMode: 'create', form: emptyIngredientForm(), catalogCategories: [], catalogTags: [], catalogSaving: 'idle', catalogCreating: null, showCreateForm: false, filters: emptyCatalogBrowserFilters(), assignmentDraft: emptyAssignmentDraft() };
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
let packagingItemsStatus: PackagingItemsStatus = 'idle';
let packagingItemsState: PackagingItemsState = { items: [], formMode: 'create', form: emptyPackagingItemForm(), catalogCategories: [], catalogTags: [], catalogSaving: 'idle', catalogCreating: null, assignmentDraft: emptyAssignmentDraft() };
let packagingItemsError = '';
let packagingItemsMessage = '';
let recipesStatus: RecipesStatus = 'idle';
let recipesError = '';
let recipesMessage = '';
let calculationStatus: CalculationStatus = 'idle';
let calculationError = '';
let recipesState: RecipesState = { templates: [], selectedTemplate: null, versions: [], selectedVersionDetail: null, versionDetailStatus: 'idle', ingredients: [], templateForm: emptyRecipeTemplateForm(), versionForm: emptyRecipeVersionForm(), calculation: null, calculationTargetValue: '', calculationTargetUnit: 'g', catalogCategories: [], catalogTags: [], catalogSaving: 'idle', catalogCreating: null };
let ingredientCatalogControls: CatalogControlState = { categorySearch: '', tagSearch: '', showAllTags: false };
let packagingCatalogControls: CatalogControlState = { categorySearch: '', tagSearch: '', showAllTags: false };

function sectionFromLocation(): NavigationSection {
  const routes: Record<string, NavigationSection> = {
    '/inventory': 'Склад',
    '/ingredients': 'Компоненты',
    '/ingredient-lots': 'Партии',
    '/stock-movements': 'Движения сырья',
    '/recipes': 'Рецепты',
    '/clients': 'Клиенты',
    '/client-recipes': 'Индивидуальные рецепты',
    '/packaging-items': 'Тара',
  };
  const placeholderRoutes: Record<string, NavigationSection> = {
    '#orders': 'Заказы',
    '#purchases': 'Закупки',
    '#production-readiness': 'Готовность',
    '#production': 'Производство',
    '#import': 'Импорт',
    '#reports': 'Отчеты',
    '#settings': 'Настройки',
    '#help': 'Помощь',
  };
  return routes[window.location.pathname] ?? placeholderRoutes[window.location.hash] ?? 'Главная';
}

function pathForSection(section: NavigationSection): string {
  return navigationGroups.flatMap((group) => group.items).find((item) => item.section === section)?.path ?? '/';
}

function labelForSection(section: NavigationSection): string {
  return navigationGroups.flatMap((group) => group.items).find((item) => item.section === section)?.label ?? section;
}

function loadSectionData(section: NavigationSection) {
  if (section === 'Склад') loadInventory();
  if (section === 'Компоненты') loadIngredients();
  if (section === 'Партии') loadIngredientLots();
  if (section === 'Движения сырья') loadStockMovements();
  if (section === 'Рецепты') loadRecipes();
  if (section === 'Клиенты') loadClients();
  if (section === 'Индивидуальные рецепты') loadClientRecipes();
  if (section === 'Тара') loadPackagingItems();
}

function renderActivePage(section: NavigationSection) {
  if (section === 'Главная') return dashboardPlaceholder();
  if (section === 'Склад') return inventoryPage();
  if (section === 'Компоненты') return ingredientsPage();
  if (section === 'Партии') return ingredientLotsPage();
  if (section === 'Движения сырья') return stockMovementsPage();
  if (section === 'Рецепты') return recipesPage();
  if (section === 'Клиенты') return clientsPage();
  if (section === 'Индивидуальные рецепты') return clientRecipesPage();
  if (section === 'Тара') return packagingItemsPage();
  return plannedSectionPlaceholder(section);
}

function activeGroupTitle() {
  return navigationGroups.find((group) => group.items.some((item) => item.section === activeSection))?.title ?? 'Главная';
}

function isNavigationGroupExpanded(group: NavigationGroup) {
  return group.title === activeGroupTitle() || !collapsedNavigationGroups.has(group.title);
}

function navigationItemMarkup(item: NavigationItem) {
  const statusLabel = item.status === 'planned' ? '<span class="nav-badge">скоро</span>' : '';
  return `<button class="nav-item ${item.section === activeSection ? 'active' : ''} status-${item.status}" type="button" data-section="${item.section}"><span>${escapeHtml(item.label)}</span>${statusLabel}</button>`;
}

function navigationMarkup() {
  return navigationGroups.map((group) => {
    const isExpanded = isNavigationGroupExpanded(group);
    const isActiveGroup = group.title === activeGroupTitle();
    return `<section class="nav-group ${isActiveGroup ? 'active-group' : ''}" aria-label="${escapeHtml(group.title)}"><button class="nav-group-toggle" type="button" data-nav-group="${escapeHtml(group.title)}" aria-expanded="${isExpanded}"><span>${escapeHtml(group.title)}</span><span aria-hidden="true">${isExpanded ? '−' : '+'}</span></button>${isExpanded ? `<div class="nav-group-items">${group.items.map(navigationItemMarkup).join('')}</div>` : ''}</section>`;
  }).join('');
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
        <nav class="navigation">${navigationMarkup()}</nav>
      </aside>
      <main class="content">
        <header class="topbar">
          <div><p class="eyebrow">Рабочее пространство</p><h1>${labelForSection(activeSection)}</h1></div>
          <span class="status ${healthStatus}">${healthLabel}</span>
        </header>
        ${renderActivePage(activeSection)}
      </main>
    </div>`;
  bindEvents(root);
}

function bindEvents(root: HTMLElement) {
  root.querySelector<HTMLImageElement>('.brand-mark img')?.addEventListener('error', (event) => { (event.currentTarget as HTMLImageElement).hidden = true; });
  root.querySelectorAll<HTMLButtonElement>('.nav-group-toggle').forEach((button) => {
    button.addEventListener('click', () => {
      const groupTitle = button.dataset.navGroup;
      if (!groupTitle || groupTitle === activeGroupTitle()) return;
      if (collapsedNavigationGroups.has(groupTitle)) collapsedNavigationGroups.delete(groupTitle); else collapsedNavigationGroups.add(groupTitle);
      render();
    });
  });
  root.querySelectorAll<HTMLButtonElement>('.nav-item').forEach((button) => {
    button.addEventListener('click', () => {
      activeSection = (button.dataset.section as NavigationSection | undefined) ?? 'Главная';
      window.history.pushState({}, '', pathForSection(activeSection));
      loadSectionData(activeSection);
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
  root.querySelectorAll<HTMLButtonElement>('[data-action="new-ingredient"]').forEach((button) => button.addEventListener('click', openIngredientCreateForm));
  root.querySelector<HTMLButtonElement>('[data-action="hide-ingredient-create-form"]')?.addEventListener('click', hideIngredientCreateForm);
  root.querySelector<HTMLButtonElement>('[data-action="cancel-ingredient-edit"]')?.addEventListener('click', cancelIngredientEdit);
  root.querySelectorAll<HTMLButtonElement>('[data-action="edit-ingredient"]').forEach((button) => button.addEventListener('click', () => startEditIngredient(Number(button.dataset.id))));
  root.querySelectorAll<HTMLButtonElement>('[data-action="deactivate-ingredient"]').forEach((button) => button.addEventListener('click', () => deactivateIngredient(Number(button.dataset.id))));
  root.querySelector<HTMLFormElement>('[data-form="ingredient"]')?.addEventListener('submit', submitIngredientForm);
  root.querySelector<HTMLFormElement>('[data-form="ingredient-catalog-category"]')?.addEventListener('submit', submitIngredientCatalogCategoryForm);
  root.querySelector<HTMLFormElement>('[data-form="ingredient-catalog-tag"]')?.addEventListener('submit', submitIngredientCatalogTagForm);
  root.querySelectorAll<HTMLButtonElement>('[data-action="assign-ingredient-category"]').forEach((button) => button.addEventListener('click', () => updateIngredientDraftCategory(Number(button.dataset.id), button.dataset.value ?? '')));
  root.querySelectorAll<HTMLInputElement>('[data-action="toggle-ingredient-tag"]').forEach((input) => input.addEventListener('change', () => updateIngredientDraftTag(Number(input.dataset.ingredientId), Number(input.value), input.checked)));
  root.querySelector<HTMLButtonElement>('[data-action="apply-ingredient-assignment"]')?.addEventListener('click', applyIngredientAssignmentDraft);
  root.querySelector<HTMLButtonElement>('[data-action="reset-ingredient-assignment"]')?.addEventListener('click', resetIngredientAssignmentDraft);
  root.querySelector<HTMLInputElement>('[data-action="filter-ingredients-search"]')?.addEventListener('input', (event) => updateIngredientFilterSearch(event.currentTarget as HTMLInputElement));
  root.querySelector<HTMLSelectElement>('[data-action="filter-ingredients-category"]')?.addEventListener('change', (event) => { ingredientsState.filters.categoryId = catalogCategoryFilterValue((event.currentTarget as HTMLSelectElement).value); render(); });
  root.querySelector<HTMLSelectElement>('[data-action="filter-ingredients-system"]')?.addEventListener('change', (event) => { ingredientsState.filters.systemType = (event.currentTarget as HTMLSelectElement).value; render(); });
  root.querySelector<HTMLSelectElement>('[data-action="filter-ingredients-status"]')?.addEventListener('change', (event) => { ingredientsState.filters.status = (event.currentTarget as HTMLSelectElement).value as CatalogStatusFilter; render(); });
  root.querySelector<HTMLSelectElement>('[data-action="add-ingredient-tag-filter"]')?.addEventListener('change', (event) => addIngredientTagFilter((event.currentTarget as HTMLSelectElement).value));
  root.querySelectorAll<HTMLButtonElement>('[data-action="remove-ingredient-tag-filter"]').forEach((button) => button.addEventListener('click', () => removeIngredientTagFilter(Number(button.dataset.id))));
  root.querySelectorAll<HTMLButtonElement>('[data-action="clear-ingredient-filter"]').forEach((button) => button.addEventListener('click', () => clearIngredientFilter(button.dataset.filter ?? '')));
  root.querySelectorAll<HTMLButtonElement>('[data-action="reset-ingredient-filters"]').forEach((button) => button.addEventListener('click', () => { ingredientsState.filters = emptyCatalogBrowserFilters(); render(); }));
  root.querySelector<HTMLInputElement>('[data-action="search-ingredient-category"]')?.addEventListener('input', (event) => updateCatalogSearch(ingredientCatalogControls, 'categorySearch', event.currentTarget as HTMLInputElement));
  root.querySelector<HTMLInputElement>('[data-action="search-ingredient-tags"]')?.addEventListener('input', (event) => updateCatalogSearch(ingredientCatalogControls, 'tagSearch', event.currentTarget as HTMLInputElement));
  root.querySelector<HTMLButtonElement>('[data-action="toggle-ingredient-tags"]')?.addEventListener('click', () => { ingredientCatalogControls.showAllTags = !ingredientCatalogControls.showAllTags; render(); });
  root.querySelector<HTMLButtonElement>('[data-action="reload-ingredient-lots"]')?.addEventListener('click', () => loadIngredientLots(true));
  root.querySelector<HTMLButtonElement>('[data-action="new-ingredient-lot"]')?.addEventListener('click', () => { ingredientLotsState.formMode = 'create'; ingredientLotsState.form = emptyIngredientLotForm(); ingredientLotsMessage = ''; ingredientLotsError = ''; render(); });
  root.querySelectorAll<HTMLButtonElement>('[data-action="edit-ingredient-lot"]').forEach((button) => button.addEventListener('click', () => startEditIngredientLot(Number(button.dataset.id))));
  root.querySelectorAll<HTMLButtonElement>('[data-action="deactivate-ingredient-lot"]').forEach((button) => button.addEventListener('click', () => deactivateIngredientLot(Number(button.dataset.id))));
  root.querySelector<HTMLFormElement>('[data-form="ingredient-lot"]')?.addEventListener('submit', submitIngredientLotForm);
  root.querySelector<HTMLButtonElement>('[data-action="reload-stock-movements"]')?.addEventListener('click', () => loadStockMovements(true));
  root.querySelector<HTMLSelectElement>('[data-action="select-stock-lot"]')?.addEventListener('change', (event) => selectStockMovementLot(Number((event.currentTarget as HTMLSelectElement).value)));
  root.querySelector<HTMLFormElement>('[data-form="stock-movement"]')?.addEventListener('submit', submitStockMovementForm);
  root.querySelector<HTMLButtonElement>('[data-action="reload-recipes"]')?.addEventListener('click', () => loadRecipes(true));
  root.querySelector<HTMLButtonElement>('[data-action="reload-recipe-ingredients"]')?.addEventListener('click', () => refreshRecipeIngredientOptions(true));
  root.querySelector<HTMLButtonElement>('[data-action="reload-clients"]')?.addEventListener('click', () => loadClients(true));
  root.querySelector<HTMLButtonElement>('[data-action="new-client"]')?.addEventListener('click', () => { clientsState.formMode = 'create'; clientsState.form = emptyClientForm(); clientsMessage = ''; clientsError = ''; render(); });
  root.querySelector<HTMLInputElement>('[data-action="toggle-archived-clients"]')?.addEventListener('change', (event) => { clientsState.includeInactive = (event.currentTarget as HTMLInputElement).checked; loadClients(true); });
  root.querySelectorAll<HTMLButtonElement>('[data-action="edit-client"]').forEach((button) => button.addEventListener('click', () => startEditClient(Number(button.dataset.id))));
  root.querySelectorAll<HTMLButtonElement>('[data-action="archive-client"]').forEach((button) => button.addEventListener('click', () => deactivateClient(Number(button.dataset.id))));
  root.querySelector<HTMLFormElement>('[data-form="client"]')?.addEventListener('submit', submitClientForm);
  root.querySelector<HTMLButtonElement>('[data-action="reload-client-recipes"]')?.addEventListener('click', () => loadClientRecipes(true));
  root.querySelector<HTMLInputElement>('[data-action="toggle-archived-client-recipes"]')?.addEventListener('change', (event) => { clientRecipesState.includeInactive = (event.currentTarget as HTMLInputElement).checked; loadClientRecipes(true); });
  root.querySelector<HTMLSelectElement>('[data-action="select-client-recipe-template"]')?.addEventListener('change', (event) => selectClientRecipeTemplate((event.currentTarget as HTMLSelectElement).value));
  root.querySelector<HTMLFormElement>('[data-form="client-recipe"]')?.addEventListener('submit', submitClientRecipeForm);
  root.querySelectorAll<HTMLButtonElement>('[data-action="open-client-recipe"]').forEach((button) => button.addEventListener('click', () => openClientRecipe(Number(button.dataset.id))));
  root.querySelectorAll<HTMLButtonElement>('[data-action="archive-client-recipe"]').forEach((button) => button.addEventListener('click', () => deactivateClientRecipe(Number(button.dataset.id))));
  root.querySelector<HTMLButtonElement>('[data-action="reload-packaging-items"]')?.addEventListener('click', () => loadPackagingItems(true));
  root.querySelector<HTMLButtonElement>('[data-action="new-packaging-item"]')?.addEventListener('click', resetPackagingItemForm);
  root.querySelectorAll<HTMLButtonElement>('[data-action="edit-packaging-item"]').forEach((button) => button.addEventListener('click', () => startEditPackagingItem(Number(button.dataset.id))));
  root.querySelectorAll<HTMLButtonElement>('[data-action="deactivate-packaging-item"]').forEach((button) => button.addEventListener('click', () => deactivatePackagingItem(Number(button.dataset.id))));
  root.querySelector<HTMLFormElement>('[data-form="packaging-item"]')?.addEventListener('submit', submitPackagingItemForm);
  root.querySelector<HTMLFormElement>('[data-form="packaging-catalog-category"]')?.addEventListener('submit', submitPackagingCatalogCategoryForm);
  root.querySelector<HTMLFormElement>('[data-form="packaging-catalog-tag"]')?.addEventListener('submit', submitPackagingCatalogTagForm);
  root.querySelectorAll<HTMLButtonElement>('[data-action="assign-packaging-category"]').forEach((button) => button.addEventListener('click', () => updatePackagingDraftCategory(Number(button.dataset.id), button.dataset.value ?? '')));
  root.querySelectorAll<HTMLInputElement>('[data-action="toggle-packaging-tag"]').forEach((input) => input.addEventListener('change', () => updatePackagingDraftTag(Number(input.dataset.packagingItemId), Number(input.value), input.checked)));
  root.querySelector<HTMLButtonElement>('[data-action="apply-packaging-assignment"]')?.addEventListener('click', applyPackagingAssignmentDraft);
  root.querySelector<HTMLButtonElement>('[data-action="reset-packaging-assignment"]')?.addEventListener('click', resetPackagingAssignmentDraft);
  root.querySelector<HTMLInputElement>('[data-action="search-packaging-category"]')?.addEventListener('input', (event) => updateCatalogSearch(packagingCatalogControls, 'categorySearch', event.currentTarget as HTMLInputElement));
  root.querySelector<HTMLInputElement>('[data-action="search-packaging-tags"]')?.addEventListener('input', (event) => updateCatalogSearch(packagingCatalogControls, 'tagSearch', event.currentTarget as HTMLInputElement));
  root.querySelector<HTMLButtonElement>('[data-action="toggle-packaging-tags"]')?.addEventListener('click', () => { packagingCatalogControls.showAllTags = !packagingCatalogControls.showAllTags; render(); });
  root.querySelector<HTMLFormElement>('[data-form="recipe-template"]')?.addEventListener('submit', submitRecipeTemplateForm);
  root.querySelector<HTMLFormElement>('[data-form="recipe-version"]')?.addEventListener('submit', submitRecipeVersionForm);
  root.querySelector<HTMLFormElement>('[data-form="recipe-calculation"]')?.addEventListener('submit', submitCalculationForm);
  root.querySelector<HTMLFormElement>('[data-form="recipe-catalog-category"]')?.addEventListener('submit', submitRecipeCatalogCategoryForm);
  root.querySelector<HTMLFormElement>('[data-form="recipe-catalog-tag"]')?.addEventListener('submit', submitRecipeCatalogTagForm);
  root.querySelector<HTMLSelectElement>('[data-action="assign-recipe-category"]')?.addEventListener('change', (event) => assignRecipeCategory(Number((event.currentTarget as HTMLSelectElement).dataset.id), (event.currentTarget as HTMLSelectElement).value));
  root.querySelectorAll<HTMLInputElement>('[data-action="toggle-recipe-tag"]').forEach((input) => input.addEventListener('change', () => assignRecipeTags(Number(input.dataset.recipeTemplateId))));
  root.querySelectorAll<HTMLButtonElement>('[data-action="open-recipe"]').forEach((button) => button.addEventListener('click', () => openRecipeTemplate(Number(button.dataset.id))));
  root.querySelectorAll<HTMLButtonElement>('[data-action="open-version"]').forEach((button) => button.addEventListener('click', () => openRecipeVersion(Number(button.dataset.id))));
  root.querySelector<HTMLButtonElement>('[data-action="add-recipe-line"]')?.addEventListener('click', addRecipeLine);
  root.querySelectorAll<HTMLButtonElement>('[data-action="remove-recipe-line"]').forEach((button) => button.addEventListener('click', () => removeRecipeLine(Number(button.dataset.index))));
}


function catalogOptions(items: CatalogOption[], search: string) {
  const normalized = search.trim().toLocaleLowerCase('ru-RU');
  if (!normalized) return items;
  return items.filter((item) => item.name.toLocaleLowerCase('ru-RU').includes(normalized));
}


function openIngredientCreateForm() {
  const current = ingredientsState.formMode === 'edit' && ingredientsState.form.id ? ingredientsState.items.find((ingredient) => ingredient.id === ingredientsState.form.id) ?? null : null;
  if (!confirmDiscardDirtyAssignment(assignmentDraftIsDirty(current, ingredientsState.assignmentDraft))) return;
  ingredientsState.formMode = 'create';
  ingredientsState.form = emptyIngredientForm();
  ingredientsState.assignmentDraft = emptyAssignmentDraft();
  ingredientsState.showCreateForm = true;
  ingredientsMessage = '';
  ingredientsError = '';
  render();
  focusIngredientFormName();
}

function hideIngredientCreateForm() {
  ingredientsState.formMode = 'create';
  ingredientsState.form = emptyIngredientForm();
  ingredientsState.assignmentDraft = emptyAssignmentDraft();
  ingredientsState.showCreateForm = false;
  ingredientsMessage = '';
  ingredientsError = '';
  render();
}

function focusIngredientFormName() {
  requestAnimationFrame(() => {
    const section = document.querySelector<HTMLElement>('[data-section="ingredient-form"]');
    section?.scrollIntoView({ block: 'start', behavior: 'smooth' });
    section?.querySelector<HTMLInputElement>('input[name="name"]')?.focus();
  });
}

function updateIngredientFilterSearch(input: HTMLInputElement) {
  const cursor = input.selectionStart ?? input.value.length;
  ingredientsState.filters.search = input.value;
  render();
  const nextInput = document.querySelector<HTMLInputElement>('[data-action="filter-ingredients-search"]');
  if (!nextInput) return;
  nextInput.focus();
  const nextCursor = Math.min(cursor, nextInput.value.length);
  nextInput.setSelectionRange(nextCursor, nextCursor);
}

function updateCatalogSearch(state: CatalogControlState, field: 'categorySearch' | 'tagSearch', input: HTMLInputElement) {
  const action = input.dataset.action;
  const cursor = input.selectionStart ?? input.value.length;
  state[field] = input.value;
  render();
  if (!action) return;
  const nextInput = document.querySelector<HTMLInputElement>(`[data-action="${action}"]`);
  if (!nextInput) return;
  nextInput.focus();
  const nextCursor = Math.min(cursor, nextInput.value.length);
  nextInput.setSelectionRange(nextCursor, nextCursor);
}


function emptyCatalogBrowserFilters(): CatalogBrowserFilters { return { search: '', categoryId: '', tagIds: [], systemType: '', status: 'active' }; }
function normalizeSearchText(value: string): string { return value.toLocaleLowerCase('ru-RU').trim(); }
function textMatchesSearch(searchableText: string, search: string): boolean { const normalized = normalizeSearchText(search); return !normalized || normalizeSearchText(searchableText).includes(normalized); }
function itemMatchesSelectedTags(itemTagIds: number[], selectedTagIds: number[]): boolean { return selectedTagIds.length === 0 || selectedTagIds.every((id) => itemTagIds.includes(id)); }
function itemMatchesCatalogCategory(itemCategoryId: number | null, categoryFilter: number | 'none' | ''): boolean { if (categoryFilter === '') return true; if (categoryFilter === 'none') return itemCategoryId === null; return itemCategoryId === categoryFilter; }
function filterCatalogItems<T>(items: T[], filters: CatalogBrowserFilters, selectors: { getSearchText: (item: T) => string; getCatalogCategoryId: (item: T) => number | null; getCatalogTagIds: (item: T) => number[]; getSystemType: (item: T) => string; getIsActive: (item: T) => boolean; }): T[] {
  return items.filter((item) => textMatchesSearch(selectors.getSearchText(item), filters.search)
    && itemMatchesCatalogCategory(selectors.getCatalogCategoryId(item), filters.categoryId)
    && itemMatchesSelectedTags(selectors.getCatalogTagIds(item), filters.tagIds)
    && (!filters.systemType || selectors.getSystemType(item) === filters.systemType)
    && (filters.status === 'all' || selectors.getIsActive(item) === (filters.status === 'active')));
}

function nextCatalogTagIds(currentIds: number[], tagId: number, checked: boolean) {
  const ids = new Set(currentIds);
  if (checked) ids.add(tagId); else ids.delete(tagId);
  return Array.from(ids);
}

function emptyAssignmentDraft(): AssignmentDraft { return { itemId: null, catalogCategoryId: null, catalogTagIds: [] }; }
function assignmentDraftFromItem(item: { id: number; catalog_category_id: number | null; catalog_tag_ids: number[] }): AssignmentDraft { return { itemId: item.id, catalogCategoryId: item.catalog_category_id, catalogTagIds: [...item.catalog_tag_ids] }; }
function sameNumberSet(left: number[], right: number[]) { if (left.length !== right.length) return false; const ids = new Set(left); return right.every((id) => ids.has(id)); }
function assignmentDraftIsDirty(item: { catalog_category_id: number | null; catalog_tag_ids: number[] } | null, draft: AssignmentDraft) { return item !== null && (draft.catalogCategoryId !== item.catalog_category_id || !sameNumberSet(draft.catalogTagIds, item.catalog_tag_ids)); }
function updateDraftCategory(draft: AssignmentDraft, value: string) { draft.catalogCategoryId = value ? Number(value) : null; }
function updateDraftTag(draft: AssignmentDraft, tagId: number, checked: boolean) { draft.catalogTagIds = nextCatalogTagIds(draft.catalogTagIds, tagId, checked); }
function resetAssignmentDraft(item: { id: number; catalog_category_id: number | null; catalog_tag_ids: number[] } | null) { return item ? assignmentDraftFromItem(item) : emptyAssignmentDraft(); }
function confirmDiscardDirtyAssignment(isDirty: boolean) { return !isDirty || window.confirm('Есть несохранённые изменения группы или меток. Перейти без сохранения?'); }

function visibleTagOptions(items: CatalogOption[], selectedIds: number[], state: CatalogControlState, limit = 10) {
  const filtered = catalogOptions(items, state.tagSearch);
  if (state.showAllTags || state.tagSearch.trim() || filtered.length <= limit) return filtered;
  const selected = filtered.filter((tag) => selectedIds.includes(tag.id));
  const selectedSet = new Set(selected.map((tag) => tag.id));
  return [...selected, ...filtered.filter((tag) => !selectedSet.has(tag.id)).slice(0, Math.max(limit - selected.length, 0))];
}

function catalogCategoryPicker(params: { itemId: number; selectedId: number | null; categories: CatalogOption[]; state: CatalogControlState; disabled: boolean; action: string; searchAction: string }) {
  const filtered = catalogOptions(params.categories, params.state.categorySearch);
  const selected = params.categories.find((category) => category.id === params.selectedId);
  const ungroupedSelected = params.selectedId === null;
  const optionButton = (label: string, value: string, selectedOption: boolean) => `<button class="catalog-option ${selectedOption ? 'selected' : ''}" type="button" data-action="${params.action}" data-id="${params.itemId}" data-value="${value}" ${params.disabled ? 'disabled' : ''}>${label}${selectedOption ? '<span>Выбрано</span>' : ''}</button>`;
  const groupOptions = filtered.map((category) => optionButton(escapeHtml(category.name), String(category.id), category.id === params.selectedId)).join('');
  const emptyState = params.categories.length === 0 ? '<p class="empty-hint">Группы пока не созданы. Создайте первую группу ниже.</p>' : filtered.length === 0 ? '<p class="empty-hint">По этому поиску групп нет. Можно создать новую группу ниже.</p>' : '';
  return `<div class="catalog-picker"><div class="catalog-picker-heading"><strong>Группа</strong><span>${selected ? escapeHtml(selected.name) : 'Без группы'}</span></div><p class="empty-hint">Группа помогает разложить записи по рабочим пространствам.</p><label>Найти группу<input data-action="${params.searchAction}" type="search" value="${escapeHtml(params.state.categorySearch)}" placeholder="Начните вводить название группы" ${params.disabled ? 'disabled' : ''} /></label><div class="catalog-option-list">${optionButton('Без группы', '', ungroupedSelected)}${groupOptions}</div>${emptyState}</div>`;
}

function catalogTagPicker(params: { itemId: number; selectedIds: number[]; tags: CatalogOption[]; state: CatalogControlState; disabled: boolean; toggleAction: string; itemDataName: string; searchAction: string; showMoreAction: string }) {
  const visible = visibleTagOptions(params.tags, params.selectedIds, params.state);
  const selected = params.tags.filter((tag) => params.selectedIds.includes(tag.id));
  const selectedChips = selected.length ? `<div class="tag-list selected-tags">${selected.map((tag) => `<span class="tag-chip selected readonly">${escapeHtml(tag.name)}</span>`).join('')}</div>` : '<p class="empty-hint">Метки еще не выбраны.</p>';
  const hiddenCount = Math.max(catalogOptions(params.tags, params.state.tagSearch).length - visible.length, 0);
  return `<div class="catalog-picker"><div class="catalog-picker-heading"><strong>Метки</strong><span>Можно выбрать несколько меток.</span></div><p class="empty-hint">Метки помогают быстро фильтровать и находить записи.</p><div><strong>Выбранные метки</strong>${selectedChips}</div><label>Найти метку<input data-action="${params.searchAction}" type="search" value="${escapeHtml(params.state.tagSearch)}" placeholder="Начните вводить название метки" ${params.disabled ? 'disabled' : ''} /></label>${params.tags.length === 0 ? '<p class="empty-hint">Метки пока не созданы. Создайте первую метку ниже.</p>' : visible.length === 0 ? '<p class="empty-hint">По этому поиску меток нет. Можно создать новую метку ниже.</p>' : `<div class="tag-picker limited-tags">${visible.map((tag) => `<label class="tag-chip ${params.selectedIds.includes(tag.id) ? 'selected' : ''}"><input type="checkbox" data-action="${params.toggleAction}" data-${params.itemDataName}="${params.itemId}" value="${tag.id}" ${params.selectedIds.includes(tag.id) ? 'checked' : ''} ${params.disabled ? 'disabled' : ''} />${escapeHtml(tag.name)}</label>`).join('')}</div>`}${hiddenCount > 0 ? `<button class="secondary-action compact" type="button" data-action="${params.showMoreAction}">Показать еще ${hiddenCount}</button>` : params.state.showAllTags && !params.state.tagSearch.trim() && params.tags.length > 10 ? `<button class="secondary-action compact" type="button" data-action="${params.showMoreAction}">Свернуть список меток</button>` : ''}</div>`;
}

function dashboardPlaceholder() {
  return `${onboardingCard()}<section class="card"><p class="card-kicker">Сегодня в мастерской</p><h2>Что уже можно открыть</h2><div class="readiness-grid"><div><h3>Работает сейчас</h3><ul><li>Рецепты</li><li>Индивидуальные рецепты</li><li>Клиенты</li><li>Компоненты</li><li>Складской обзор</li><li>Тара</li></ul></div><div><h3>Скоро</h3><ul><li>Заказы</li><li>Производство</li><li>Закупки</li><li>Импорт</li><li>Отчеты</li></ul></div></div></section>`;
}




function clientRecipesPage() {
  if (clientRecipesStatus === 'idle' || clientRecipesStatus === 'loading') return `<section class="card"><p class="card-kicker">Индивидуальные рецепты</p><h2>Загружаем индивидуальные рецепты…</h2><p>Получаем персональные формулы, клиентов и базовые рецепты из локального API.</p></section>`;
  if (clientRecipesStatus === 'error') return `<section class="card error-card"><p class="card-kicker">Индивидуальные рецепты</p><h2>Не удалось загрузить индивидуальные рецепты</h2><p>${clientRecipesError || 'Локальный API временно недоступен.'}</p><p class="next-step">Проверьте, что локальное приложение запущено, и попробуйте обновить раздел.</p><button class="primary-action" type="button" data-action="reload-client-recipes">Повторить загрузку</button></section>`;
  return `<div class="recipes-layout"><section class="card recipes-intro"><div><p class="card-kicker">Индивидуальные рецепты</p><h2>Индивидуальные рецепты</h2><p>Персональные формулы клиента на основе сохраненных версий рецептов.</p><p class="next-step">Индивидуальный рецепт создается как отдельная карточка клиента. Система берет сохраненную версию рецепта и создает персональную копию для работы с пожеланиями, ограничениями и заметками клиента.</p></div><div class="actions"><label><input type="checkbox" data-action="toggle-archived-client-recipes" ${clientRecipesState.includeInactive ? 'checked' : ''} /> Показывать архивные</label><button class="secondary-action" type="button" data-action="reload-client-recipes">Обновить</button></div></section>${clientRecipesMessage ? `<p class="page-message">${clientRecipesMessage}</p>` : ''}${clientRecipesError ? `<p class="page-message error-message">${clientRecipesError}</p>` : ''}<div class="recipe-columns"><div>${clientRecipeForm()}${clientRecipeList()}</div><div>${clientRecipeDetailPanel()}</div></div></div>`;
}
function clientRecipeForm() { const f = clientRecipesState.form; const noClients = clientRecipesState.clients.filter((c)=>c.is_active).length === 0; const noTemplates = clientRecipesState.templates.filter((t)=>t.is_active).length === 0; return `<section class="card form-card"><p class="card-kicker">Создание</p><h2>Создать индивидуальный рецепт</h2><form data-form="client-recipe" class="ingredient-form"><div class="form-grid"><label>Клиент<select name="client_id" required ${noClients ? 'disabled' : ''}><option value="">Выберите клиента</option>${clientRecipesState.clients.filter((c)=>c.is_active).map((c)=>`<option value="${c.id}" ${f.client_id===String(c.id)?'selected':''}>${escapeHtml(c.full_name)}</option>`).join('')}</select></label><label>Базовый рецепт<select name="recipe_template_id" data-action="select-client-recipe-template" required ${noTemplates ? 'disabled' : ''}><option value="">Выберите рецепт</option>${clientRecipesState.templates.filter((t)=>t.is_active).map((t)=>`<option value="${t.id}" ${f.recipe_template_id===String(t.id)?'selected':''}>${escapeHtml(t.name)}</option>`).join('')}</select></label><label>Версия рецепта<select name="source_recipe_version_id" required ${!f.recipe_template_id || clientRecipesState.versions.length === 0 ? 'disabled' : ''}><option value="">Выберите версию</option>${clientRecipesState.versions.map((v)=>`<option value="${v.id}" ${f.source_recipe_version_id===String(v.id)?'selected':''}>Версия №${v.version_number} · ${versionStatusLabel(v.status)} · ${escapeHtml(v.title || 'Без заголовка')}</option>`).join('')}</select></label><label>Название индивидуального рецепта<input name="title" required maxlength="180" value="${escapeHtml(f.title)}" placeholder="Например, Крем для Анны: без отдушки" /></label><label>Размер партии<input name="target_batch_size_value" inputmode="decimal" value="${escapeHtml(f.target_batch_size_value)}" placeholder="Например, 50" /></label><label>Единица<select name="target_batch_size_unit">${['g','ml','pcs'].map((u)=>`<option value="${u}" ${f.target_batch_size_unit===u?'selected':''}>${unitLabel(u)}</option>`).join('')}</select></label><label class="full-span">Персонализация<textarea name="personalization_notes" rows="2" maxlength="1200" placeholder="Что меняется для этого клиента">${escapeHtml(f.personalization_notes)}</textarea></label><label class="full-span">Аллергии<textarea name="allergy_notes" rows="2" maxlength="1200">${escapeHtml(f.allergy_notes)}</textarea></label><label class="full-span">Предпочтения<textarea name="preference_notes" rows="2" maxlength="1200">${escapeHtml(f.preference_notes)}</textarea></label><label class="full-span">Противопоказания<textarea name="contraindication_notes" rows="2" maxlength="1200">${escapeHtml(f.contraindication_notes)}</textarea></label><label class="full-span">Заметки<textarea name="notes" rows="3" maxlength="1600">${escapeHtml(f.notes)}</textarea></label></div>${noClients ? '<p class="empty-hint">Сначала создайте клиента в разделе «Клиенты».</p>' : ''}${noTemplates ? '<p class="empty-hint">Сначала создайте базовый рецепт в разделе «Рецепты».</p>' : ''}${f.recipe_template_id && clientRecipesState.versions.length === 0 ? '<p class="empty-hint">У выбранного рецепта пока нет версии. Сначала создайте версию рецепта в разделе «Рецепты».</p>' : ''}<p class="next-step">Frontend не меняет базовый рецепт и его версии: копию состава создает backend при сохранении карточки.</p><div class="actions"><button class="primary-action" type="submit" ${noClients || noTemplates ? 'disabled' : ''}>Создать индивидуальный рецепт</button></div></form></section>`; }
function clientRecipeList() { if (clientRecipesState.items.length === 0) return `<section class="card empty-card"><h2>Пока нет индивидуальных рецептов</h2><p>Пока нет индивидуальных рецептов. Создайте персональную формулу на основе версии рецепта и карточки клиента.</p><p class="next-step">Если список клиентов или рецептов пустой, сначала заполните разделы «Клиенты» и «Рецепты».</p></section>`; return `<section class="card data-card"><p class="card-kicker">Список</p><h2>Индивидуальные рецепты</h2><div class="table-wrap"><table><thead><tr><th>Название</th><th>Клиент</th><th>Версия</th><th>Партия</th><th>Статус</th><th>Действия</th></tr></thead><tbody>${clientRecipesState.items.map((r)=>`<tr><td>${escapeHtml(r.title)}</td><td>${escapeHtml(clientRecipeClientName(r.client_id))}</td><td>Версия #${r.source_recipe_version_id}</td><td>${batchLabel(r.target_batch_size_value, r.target_batch_size_unit)}</td><td><span class="pill ${r.is_active?'success':'muted'}">${r.is_active?'Активен':'Архив'}</span></td><td><button class="secondary-action compact" type="button" data-action="open-client-recipe" data-id="${r.id}">Подробнее</button>${r.is_active ? ` <button class="secondary-action compact danger-action" type="button" data-action="archive-client-recipe" data-id="${r.id}">Архивировать</button>` : ''}</td></tr>`).join('')}</tbody></table></div></section>`; }
function clientRecipeDetailPanel() { if (clientRecipesState.detailStatus === 'loading') return `<section class="card"><h2>Загружаем карточку…</h2><p>Получаем персональную формулу и снимок состава из backend.</p></section>`; const d = clientRecipesState.selectedDetail; if (!d) return `<section class="card empty-card"><h2>Откройте индивидуальный рецепт</h2><p>Выберите карточку в списке, чтобы увидеть заметки клиента и снимок состава.</p><p class="next-step">Редактирование индивидуального рецепта будет добавлено отдельным шагом. Сейчас можно создать карточку, посмотреть состав и архивировать ее.</p></section>`; const r = d.client_recipe; return `<section class="card data-card"><p class="card-kicker">Карточка клиента</p><h2>${escapeHtml(r.title)}</h2><p><strong>Клиент:</strong> ${escapeHtml(clientRecipeClientName(r.client_id))}</p><p><strong>Размер партии:</strong> ${batchLabel(r.target_batch_size_value, r.target_batch_size_unit)}</p><p><strong>Статус:</strong> ${r.is_active ? 'активен' : 'архив'}</p><div class="note-grid"><p><strong>Персонализация:</strong><br>${escapeHtml(r.personalization_notes || 'Не указана')}</p><p><strong>Аллергии:</strong><br>${escapeHtml(r.allergy_notes || 'Не указаны')}</p><p><strong>Предпочтения:</strong><br>${escapeHtml(r.preference_notes || 'Не указаны')}</p><p><strong>Противопоказания:</strong><br>${escapeHtml(r.contraindication_notes || 'Не указаны')}</p><p class="full-span"><strong>Заметки:</strong><br>${escapeHtml(r.notes || 'Нет заметок')}</p></div><p class="next-step">Состав скопирован из выбранной версии рецепта. Изменение базового рецепта не меняет эту персональную карточку автоматически.</p><h3>Снимок состава</h3>${d.ingredients.length === 0 ? '<p>Backend не вернул строки состава для этой карточки.</p>' : `<div class="table-wrap"><table><thead><tr><th>№</th><th>Фаза</th><th>Компонент</th><th>Количество</th><th>Заметки</th></tr></thead><tbody>${d.ingredients.slice().sort((a,b)=>a.position-b.position).map((line)=>`<tr><td>${line.position}</td><td>${escapeHtml(line.phase || 'Не указана')}</td><td>${escapeHtml(clientRecipeIngredientName(line.ingredient_id))}</td><td>${escapeHtml(line.amount_value)} ${unitLabel(line.amount_unit)}</td><td>${escapeHtml([line.personalization_note, line.notes].filter(Boolean).join(' · ') || 'Без заметок')}</td></tr>`).join('')}</tbody></table></div>`}</section>`; }

function clientsPage() {
  if (clientsStatus === 'idle' || clientsStatus === 'loading') return `<section class="card"><p class="card-kicker">Клиенты</p><h2>Загружаем клиентов…</h2><p>Получаем карточки клиентов из локального API.</p></section>`;
  if (clientsStatus === 'error') return `<section class="card error-card"><p class="card-kicker">Клиенты</p><h2>Не удалось загрузить клиентов</h2><p>${clientsError || 'Не удалось загрузить клиентов. Проверьте, что локальное приложение запущено.'}</p><p class="next-step">Проверьте, что локальное приложение запущено, и попробуйте обновить раздел.</p><button class="primary-action" type="button" data-action="reload-clients">Повторить загрузку</button></section>`;
  return `<div class="catalog-layout"><section class="card catalog-intro"><div><p class="card-kicker">Клиенты</p><h2>Клиенты</h2><p>Карточки клиентов, пожелания, ограничения и заметки для индивидуальных рецептов.</p><p class="next-step">Аллергии, предпочтения и противопоказания помогут позже безопасно создавать индивидуальные рецепты клиента.</p></div><div class="actions"><label><input type="checkbox" data-action="toggle-archived-clients" ${clientsState.includeInactive ? 'checked' : ''} /> Показывать архив</label><button class="secondary-action" type="button" data-action="new-client">Очистить форму</button></div></section>${clientsMessage ? `<p class="page-message">${clientsMessage}</p>` : ''}${clientsError ? `<p class="page-message error-message">${clientsError}</p>` : ''}${clientForm()}${clientList()}</div>`;
}

function clientForm() {
  const form = clientsState.form;
  const isEdit = clientsState.formMode === 'edit';
  return `<section class="card form-card"><p class="card-kicker">${isEdit ? 'Редактирование' : 'Создание'}</p><h2>${isEdit ? 'Изменить карточку клиента' : 'Создать клиента'}</h2><form data-form="client" class="ingredient-form"><div class="form-grid"><label>ФИО клиента<input name="full_name" required maxlength="200" value="${escapeHtml(form.full_name)}" placeholder="Например, Анна Иванова" /></label><label>Телефон<input name="phone" maxlength="80" value="${escapeHtml(form.phone)}" placeholder="+7 ..." /></label><label>Email<input name="email" type="email" maxlength="160" value="${escapeHtml(form.email)}" placeholder="Необязательно" /></label><label>Дата рождения<input name="birthday" type="date" value="${escapeHtml(form.birthday ?? '')}" /></label><label class="full-span">Адрес<input name="address" maxlength="300" value="${escapeHtml(form.address)}" placeholder="Необязательно" /></label><label class="full-span">Особенности кожи<textarea name="skin_notes" rows="2" maxlength="1200" placeholder="Например, чувствительная кожа">${escapeHtml(form.skin_notes)}</textarea></label><label class="full-span">Аллергии<textarea name="allergy_notes" rows="2" maxlength="1200" placeholder="Что важно учитывать в составах">${escapeHtml(form.allergy_notes)}</textarea></label><label class="full-span">Предпочтения<textarea name="preference_notes" rows="2" maxlength="1200" placeholder="Текстуры, ароматы, упаковка">${escapeHtml(form.preference_notes)}</textarea></label><label class="full-span">Противопоказания<textarea name="contraindication_notes" rows="2" maxlength="1200" placeholder="Ограничения, которые нельзя забыть">${escapeHtml(form.contraindication_notes)}</textarea></label><label class="full-span">Заметки<textarea name="notes" rows="3" maxlength="1600" placeholder="Рабочие заметки по клиенту">${escapeHtml(form.notes)}</textarea></label></div><p class="next-step">Аллергии, предпочтения и противопоказания помогут позже безопасно создавать индивидуальные рецепты клиента.</p><div class="actions"><button class="primary-action" type="submit">${isEdit ? 'Сохранить карточку' : 'Создать клиента'}</button>${isEdit ? '<button class="secondary-action" type="button" data-action="new-client">Отменить редактирование</button>' : ''}</div></form></section>`;
}

function clientList() {
  if (clientsState.items.length === 0) return `<section class="card empty-card"><h2>Пока нет клиентов</h2><p>Пока нет клиентов. Добавьте первого клиента, чтобы хранить пожелания, ограничения и заметки для будущих индивидуальных рецептов.</p><p class="next-step">Заполните ФИО и любые известные ограничения, затем нажмите «Создать клиента».</p></section>`;
  return `<section class="card data-card"><p class="card-kicker">Список</p><h2>${clientsState.includeInactive ? 'Все клиенты' : 'Активные клиенты'}</h2><div class="table-wrap"><table><thead><tr><th>Клиент</th><th>Контакты</th><th>Важные заметки</th><th>Статус</th><th>Действия</th></tr></thead><tbody>${clientsState.items.map((client) => `<tr><td><strong>${escapeHtml(client.full_name)}</strong><small>${client.birthday ? `Дата рождения: ${formatDate(client.birthday)}` : 'Дата рождения не указана'}</small></td><td>${client.phone ? escapeHtml(client.phone) : 'Телефон не указан'}<small>${client.email ? escapeHtml(client.email) : 'Email не указан'}</small></td><td>${clientNotesSummary(client)}</td><td><span class="pill ${client.is_active ? 'success' : 'muted'}">${client.is_active ? 'Активен' : 'Архив'}</span></td><td><div class="row-actions"><button class="secondary-action compact" type="button" data-action="edit-client" data-id="${client.id}">Изменить</button>${client.is_active ? `<button class="secondary-action compact danger-action" type="button" data-action="archive-client" data-id="${client.id}">Архивировать</button>` : ''}</div></td></tr>`).join('')}</tbody></table></div><p class="next-step">Архивирование не удаляет карточку клиента, а скрывает ее из активного списка.</p></section>`;
}

function ingredientsPage() {
  if (ingredientsStatus === 'idle' || ingredientsStatus === 'loading') return `<section class="card"><p class="card-kicker">Компоненты</p><h2>Загружаем компоненты…</h2><p>Получаем справочник компонентов из локального API.</p></section>`;
  if (ingredientsStatus === 'error') return `<section class="card error-card"><p class="card-kicker">Компоненты</p><h2>Не удалось загрузить компоненты</h2><p>${ingredientsError || 'Локальный API временно недоступен.'}</p><p class="next-step">Проверьте, что приложение запущено полностью, и попробуйте обновить раздел.</p><button class="primary-action" type="button" data-action="reload-ingredients">Повторить загрузку</button></section>`;
  const filtered = filteredIngredients();
  const isEdit = ingredientsState.formMode === 'edit';
  const isCreateActive = ingredientsState.formMode === 'create' && ingredientsState.showCreateForm;
  const activeWorkspace = isEdit ? `${ingredientForm()}${ingredientCatalogPanel()}` : isCreateActive ? ingredientForm() : '';
  const secondaryWorkspace = isEdit ? '' : isCreateActive ? ingredientCatalogPanel() : `${ingredientForm()}${ingredientCatalogPanel()}`;
  return `<div class="catalog-layout"><section class="card catalog-intro"><div><p class="card-kicker">Каталог компонентов</p><h2>Компоненты</h2><p>Сначала найдите существующий компонент по названию, группе, меткам, системному типу или статусу. Создание и редактирование доступны ниже, чтобы каталог оставался главным рабочим местом.</p><p class="next-step">Системный тип используется программой. Группа и метки — ваш способ организовать компоненты для поиска.</p></div><div class="actions"><button class="secondary-action" type="button" data-action="reload-ingredients">Обновить список</button><button class="primary-action" type="button" data-action="new-ingredient">Создать компонент</button></div></section>${ingredientsMessage ? `<p class="page-message">${ingredientsMessage}</p>` : ''}${ingredientsError ? `<p class="page-message error-message">${ingredientsError}</p>` : ''}${ingredientCatalogToolbar(filtered.length)}${activeWorkspace}${ingredientList(filtered)}${secondaryWorkspace}</div>`;
}

function ingredientCatalogToolbar(resultCount: number) {
  const f = ingredientsState.filters;
  const categoryOptionsHtml = [`<option value="" ${f.categoryId === '' ? 'selected' : ''}>Все группы</option>`, `<option value="none" ${f.categoryId === 'none' ? 'selected' : ''}>Без группы</option>`, ...ingredientsState.catalogCategories.map((category) => `<option value="${category.id}" ${f.categoryId === category.id ? 'selected' : ''}>${escapeHtml(category.name)}</option>`)].join('');
  const availableTags = ingredientsState.catalogTags.filter((tag) => !f.tagIds.includes(tag.id));
  const activeTagChips = f.tagIds.map((id) => ingredientsState.catalogTags.find((tag) => tag.id === id)).filter((tag): tag is CatalogTag => Boolean(tag)).map((tag) => `<span class="tag-chip selected">${escapeHtml(tag.name)} <button type="button" data-action="remove-ingredient-tag-filter" data-id="${tag.id}" aria-label="Убрать метку ${escapeHtml(tag.name)}">×</button></span>`).join('');
  const activeFilters = ingredientActiveFilterChips();
  return `<section class="card data-card catalog-browser"><p class="card-kicker">Каталог компонентов</p><h2>Найти компонент</h2><div class="catalog-toolbar"><label class="full-span">Поиск<input type="search" data-action="filter-ingredients-search" value="${escapeHtml(f.search)}" placeholder="Название, поставщик, INCI, заметки, применение или ограничения" /></label><label>Группа<select data-action="filter-ingredients-category">${categoryOptionsHtml}</select></label><label>Метки<select data-action="add-ingredient-tag-filter"><option value="">Все метки</option>${availableTags.map((tag) => `<option value="${tag.id}">${escapeHtml(tag.name)}</option>`).join('')}</select></label><label>Системный тип<select data-action="filter-ingredients-system"><option value="" ${f.systemType === '' ? 'selected' : ''}>Все типы</option>${ingredientSystemCategories().map((value) => `<option value="${value}" ${f.systemType === value ? 'selected' : ''}>${escapeHtml(categoryLabel(value))}</option>`).join('')}</select></label><label>Статус<select data-action="filter-ingredients-status"><option value="active" ${f.status === 'active' ? 'selected' : ''}>Активные</option><option value="archived" ${f.status === 'archived' ? 'selected' : ''}>Архив</option><option value="all" ${f.status === 'all' ? 'selected' : ''}>Все</option></select></label></div>${activeTagChips ? `<div class="active-filter-row"><strong>Метки:</strong>${activeTagChips}</div>` : ''}${activeFilters ? `<div class="active-filter-row"><strong>Активные фильтры:</strong>${activeFilters}</div>` : ''}<div class="catalog-summary"><span>Показаны компоненты: ${resultCount} из ${ingredientsState.items.length}</span><button class="secondary-action compact" type="button" data-action="reset-ingredient-filters">Сбросить фильтры</button></div></section>`;
}

function ingredientList(items: Ingredient[]) {
  if (ingredientsState.items.length === 0) return `<section class="card empty-card"><h2>Компонентов пока нет</h2><p>Добавьте первый компонент, чтобы потом учитывать партии и остатки на складе.</p><p class="next-step">Нажмите «Создать компонент», заполните название, единицу учета и при необходимости плотность, затем сохраните запись.</p></section>`;
  if (items.length === 0) return `<section class="card empty-card"><h2>По этим фильтрам компонентов не найдено.</h2><p>Попробуйте убрать часть условий поиска или вернуться к полному каталогу.</p><button class="secondary-action" type="button" data-action="reset-ingredient-filters">Сбросить фильтры</button></section>`;
  return `<section class="card data-card"><p class="card-kicker">Результаты каталога</p><h2>Найденные компоненты</h2><p class="catalog-results-summary">Показаны компоненты: ${items.length} из ${ingredientsState.items.length}</p><div class="table-wrap"><table class="compact-catalog-table"><thead><tr><th>Название</th><th>Системный тип</th><th>Ед. учета</th><th>Группа</th><th>Метки</th><th>Статус</th><th>Действия</th></tr></thead><tbody>${items.map((item) => `<tr><td><strong>${escapeHtml(item.name)}</strong><small>${item.supplier_hint ? escapeHtml(item.supplier_hint) : 'Поставщик не указан'}</small></td><td>${escapeHtml(categoryLabel(item.category))}</td><td>${unitLabel(item.default_unit)}</td><td>${escapeHtml(ingredientCatalogCategoryLabel(item))}</td><td>${ingredientTagChips(item)}</td><td><span class="pill ${item.is_active ? 'success' : 'muted'}">${item.is_active ? 'Активен' : 'Архив'}</span></td><td><div class="row-actions"><button class="secondary-action compact" type="button" data-action="edit-ingredient" data-id="${item.id}">Изменить</button>${item.is_active ? `<button class="secondary-action compact danger-action" type="button" data-action="deactivate-ingredient" data-id="${item.id}">Деактивировать</button>` : ''}</div></td></tr>`).join('')}</tbody></table></div></section>`;
}



function ingredientForm() {
  const form = ingredientsState.form;
  const isEdit = ingredientsState.formMode === 'edit';
  if (!isEdit && !ingredientsState.showCreateForm) return `<section class="card form-card collapsed-create-card"><div><p class="card-kicker">Создание</p><h2>Создать новый компонент</h2><p>Форма создания скрыта, чтобы каталог оставался первым рабочим экраном.</p></div><button class="primary-action" type="button" data-action="new-ingredient">Создать компонент</button></section>`;
  return `<section class="card form-card" data-section="ingredient-form"><p class="card-kicker">${isEdit ? 'Редактирование' : 'Создание'}</p><h2>${isEdit ? 'Изменить компонент' : 'Создать компонент'}</h2><form data-form="ingredient" class="ingredient-form"><div class="form-grid"><label>Название<input name="name" required maxlength="160" value="${escapeHtml(form.name)}" placeholder="Например, масло ши" /></label><label>Категория<select name="category">${categoryOptions(form.category)}</select></label><label>Единица учета<select name="default_unit">${unitOptions(form.default_unit)}</select></label><label>Плотность<input name="density_g_per_ml" inputmode="decimal" value="${escapeHtml(form.density_g_per_ml ?? '')}" placeholder="Например, 0.950" /></label><label>Поставщик<input name="supplier_hint" maxlength="160" value="${escapeHtml(form.supplier_hint)}" placeholder="Необязательно" /></label><label>INCI<input name="inci_name" maxlength="240" value="${escapeHtml(form.inci_name)}" placeholder="Необязательно" /></label><label class="full-span">Заметки<textarea name="notes" rows="3" maxlength="1200" placeholder="Короткие рабочие заметки">${escapeHtml(form.notes)}</textarea></label><label class="full-span">Ограничения и аллергены<textarea name="allergen_note" rows="2" maxlength="800" placeholder="Необязательно">${escapeHtml(form.allergen_note)}</textarea></label><label class="full-span">Применение<textarea name="usage_note" rows="2" maxlength="800" placeholder="Необязательно">${escapeHtml(form.usage_note)}</textarea></label></div><div class="actions"><button class="primary-action" type="submit">${isEdit ? 'Сохранить изменения' : 'Создать компонент'}</button>${isEdit ? '<button class="secondary-action" type="button" data-action="cancel-ingredient-edit">Отменить редактирование</button>' : '<button class="secondary-action" type="button" data-action="hide-ingredient-create-form">Вернуться к каталогу</button>'}</div></form></section>`;
}

function ingredientCatalogPanel() {
  const item = ingredientsState.formMode === 'edit' && ingredientsState.form.id ? ingredientsState.items.find((ingredient) => ingredient.id === ingredientsState.form.id) : null;
  const createControls = ingredientCatalogCreateControls();
  if (!item) return `<section class="card catalog-helper-card"><p class="card-kicker">Моя организация каталога</p><h2>Группа и метки</h2><p>Группа помогает разложить записи по рабочим пространствам. Метки помогают быстро фильтровать и находить записи.</p><p>Выберите компонент в списке через «Изменить», чтобы назначить ему группу и несколько меток.</p>${createControls}<p class="next-step">Системный тип остается отдельным полем и используется программой для расчетов и справочников.</p></section>`;
  const draft = ingredientsState.assignmentDraft.itemId === item.id ? ingredientsState.assignmentDraft : assignmentDraftFromItem(item);
  const isDirty = assignmentDraftIsDirty(item, draft);
  const draftNotice = isDirty ? '<p class="page-message">Есть несохранённые изменения</p>' : '';
  return `<section class="card form-card"><p class="card-kicker">Каталог компонента</p><h2>${escapeHtml(item.name)}</h2><p>Группа и метки помогают вам навести порядок в компонентах. Они не заменяют системный тип компонента.</p><div class="catalog-classification">${catalogCategoryPicker({ itemId: item.id, selectedId: draft.catalogCategoryId, categories: ingredientsState.catalogCategories, state: ingredientCatalogControls, disabled: ingredientsState.catalogSaving === 'saving', action: 'assign-ingredient-category', searchAction: 'search-ingredient-category' })}${catalogTagPicker({ itemId: item.id, selectedIds: draft.catalogTagIds, tags: ingredientsState.catalogTags, state: ingredientCatalogControls, disabled: ingredientsState.catalogSaving === 'saving', toggleAction: 'toggle-ingredient-tag', itemDataName: 'ingredient-id', searchAction: 'search-ingredient-tags', showMoreAction: 'toggle-ingredient-tags' })}</div>${draftNotice}<div class="actions"><button class="primary-action" type="button" data-action="apply-ingredient-assignment" ${!isDirty || ingredientsState.catalogSaving === 'saving' ? 'disabled' : ''}>${ingredientsState.catalogSaving === 'saving' ? 'Сохраняем…' : 'Применить изменения'}</button><button class="secondary-action" type="button" data-action="reset-ingredient-assignment" ${!isDirty || ingredientsState.catalogSaving === 'saving' ? 'disabled' : ''}>Сбросить</button></div>${createControls}<p class="next-step">Группа и метки изменяются как черновик. Нажмите «Применить изменения», чтобы сохранить их.</p></section>`;
}

function ingredientCatalogCreateControls() {
  const categoryDisabled = ingredientsState.catalogCreating === 'category' || ingredientsState.catalogSaving === 'saving';
  const tagDisabled = ingredientsState.catalogCreating === 'tag' || ingredientsState.catalogSaving === 'saving';
  return `<div class="catalog-create-grid"><form data-form="ingredient-catalog-category" class="catalog-create-form"><h3>Добавить группу</h3><label>Название группы<input name="name" required maxlength="160" placeholder="Например, Масла" ${categoryDisabled ? 'disabled' : ''} /></label><button class="secondary-action" type="submit" ${categoryDisabled ? 'disabled' : ''}>${ingredientsState.catalogCreating === 'category' ? 'Создаем…' : 'Создать группу'}</button></form><form data-form="ingredient-catalog-tag" class="catalog-create-form"><h3>Добавить метку</h3><label>Название метки<input name="name" required maxlength="160" placeholder="Например, Для лица" ${tagDisabled ? 'disabled' : ''} /></label><button class="secondary-action" type="submit" ${tagDisabled ? 'disabled' : ''}>${ingredientsState.catalogCreating === 'tag' ? 'Создаем…' : 'Создать метку'}</button></form></div>`;
}

function packagingItemsPage() {
  if (packagingItemsStatus === 'idle' || packagingItemsStatus === 'loading') return `<section class="card"><p class="card-kicker">Тара</p><h2>Загружаем тару…</h2><p>Получаем справочник тары из локального API.</p></section>`;
  if (packagingItemsStatus === 'error') return `<section class="card error-card"><p class="card-kicker">Тара</p><h2>Не удалось загрузить тару</h2><p>${packagingItemsError || 'Локальный API временно недоступен.'}</p><p class="next-step">Проверьте, что приложение запущено полностью, и попробуйте обновить раздел.</p><button class="primary-action" type="button" data-action="reload-packaging-items">Повторить загрузку</button></section>`;
  return `<div class="catalog-layout"><section class="card catalog-intro"><div><p class="card-kicker">Тара</p><h2>Справочник тары</h2><p>Добавляйте баночки, флаконы, крышки, этикетки и коробки. Остатки меняются через складские операции, а не здесь.</p><p class="next-step">Этот раздел описывает саму тару. Остатки и списания будут отдельными складскими операциями.</p></div><div class="actions"><button class="secondary-action" type="button" data-action="reload-packaging-items">Обновить список</button><button class="secondary-action" type="button" data-action="new-packaging-item">Очистить форму</button></div></section>${packagingItemsMessage ? `<p class="page-message">${packagingItemsMessage}</p>` : ''}${packagingItemsError ? `<p class="page-message error-message">${packagingItemsError}</p>` : ''}${packagingItemForm()}${packagingCatalogPanel()}${packagingItemsList()}</div>`;
}

function packagingItemForm() {
  const form = packagingItemsState.form;
  const isEdit = packagingItemsState.formMode === 'edit';
  return `<section class="card form-card"><p class="card-kicker">${isEdit ? 'Редактирование' : 'Создание'}</p><h2>${isEdit ? 'Изменить тару' : 'Добавить тару'}</h2><form data-form="packaging-item" class="ingredient-form"><div class="form-grid"><label>Название<input name="name" required maxlength="160" value="${escapeHtml(form.name)}" placeholder="Например, баночка 30 мл" /></label><label>Тип тары<select name="kind">${packagingKindOptions(form.kind)}</select></label><label>Единица учета<select name="unit">${packagingUnitOptions(form.unit)}</select></label><label>Объем<input name="capacity_value" inputmode="decimal" value="${escapeHtml(form.capacity_value ?? '')}" placeholder="Например, 30" /></label><label>Единица объема<select name="capacity_unit"><option value="" ${form.capacity_unit ? '' : 'selected'}>Не указана</option>${capacityUnitOptions(form.capacity_unit ?? '')}</select></label><label>Материал<input name="material" maxlength="120" value="${escapeHtml(form.material)}" placeholder="Стекло, пластик, бумага…" /></label><label>Поставщик<input name="supplier_hint" maxlength="160" value="${escapeHtml(form.supplier_hint)}" placeholder="Необязательно" /></label><label>Цена за единицу<input name="unit_cost" inputmode="decimal" value="${escapeHtml(form.unit_cost ?? '')}" placeholder="Например, 12.50" /></label><label class="full-span">Заметки<textarea name="notes" rows="3" maxlength="1200" placeholder="Короткие рабочие заметки о таре">${escapeHtml(form.notes)}</textarea></label></div><div class="actions"><button class="primary-action" type="submit">${isEdit ? 'Сохранить изменения' : 'Создать тару'}</button>${isEdit ? '<button class="secondary-action" type="button" data-action="new-packaging-item">Отменить редактирование</button>' : ''}</div><p class="next-step">Остатки, приход и списания не меняются в этой форме — для них будут отдельные складские операции.</p></form></section>`;
}

function packagingCatalogPanel() {
  const item = packagingItemsState.formMode === 'edit' && packagingItemsState.form.id ? packagingItemsState.items.find((packagingItem) => packagingItem.id === packagingItemsState.form.id) : null;
  const createControls = packagingCatalogCreateControls();
  const helperCopy = 'Тип тары — системный тип для учета. Группа и метки — ваш способ навести порядок в каталоге.';
  if (!item) return `<section class="card catalog-helper-card"><p class="card-kicker">Организация каталога тары</p><h2>Группа и метки</h2><p>${helperCopy}</p><p>Группа помогает разложить записи по рабочим пространствам. Метки помогают быстро фильтровать и находить записи.</p><p>Чтобы назначить их конкретной таре, нажмите «Изменить» у нужной тары.</p>${createControls}<p class="next-step">Созданные группы и метки появляются здесь сразу. Они не добавляются в выпадающий список «Тип тары».</p></section>`;
  const draft = packagingItemsState.assignmentDraft.itemId === item.id ? packagingItemsState.assignmentDraft : assignmentDraftFromItem(item);
  const isDirty = assignmentDraftIsDirty(item, draft);
  const draftNotice = isDirty ? '<p class="page-message">Есть несохранённые изменения</p>' : '';
  return `<section class="card form-card"><p class="card-kicker">Организация каталога тары</p><h2>Группа и метки</h2><p>${helperCopy}</p><div class="catalog-classification">${catalogCategoryPicker({ itemId: item.id, selectedId: draft.catalogCategoryId, categories: packagingItemsState.catalogCategories, state: packagingCatalogControls, disabled: packagingItemsState.catalogSaving === 'saving', action: 'assign-packaging-category', searchAction: 'search-packaging-category' })}${catalogTagPicker({ itemId: item.id, selectedIds: draft.catalogTagIds, tags: packagingItemsState.catalogTags, state: packagingCatalogControls, disabled: packagingItemsState.catalogSaving === 'saving', toggleAction: 'toggle-packaging-tag', itemDataName: 'packaging-item-id', searchAction: 'search-packaging-tags', showMoreAction: 'toggle-packaging-tags' })}</div>${draftNotice}<div class="actions"><button class="primary-action" type="button" data-action="apply-packaging-assignment" ${!isDirty || packagingItemsState.catalogSaving === 'saving' ? 'disabled' : ''}>${packagingItemsState.catalogSaving === 'saving' ? 'Сохраняем…' : 'Применить изменения'}</button><button class="secondary-action" type="button" data-action="reset-packaging-assignment" ${!isDirty || packagingItemsState.catalogSaving === 'saving' ? 'disabled' : ''}>Сбросить</button></div>${createControls}<p class="next-step">Группа и метки изменяются как черновик. Нажмите «Применить изменения», чтобы сохранить их.</p></section>`;
}

function packagingCatalogCreateControls() {
  const categoryDisabled = packagingItemsState.catalogCreating === 'category' || packagingItemsState.catalogSaving === 'saving';
  const tagDisabled = packagingItemsState.catalogCreating === 'tag' || packagingItemsState.catalogSaving === 'saving';
  return `<div class="catalog-create-grid"><form data-form="packaging-catalog-category" class="catalog-create-form"><h3>Добавить группу</h3><label>Название группы<input name="name" required maxlength="160" placeholder="Например, Баночки" ${categoryDisabled ? 'disabled' : ''} /></label><button class="secondary-action" type="submit" ${categoryDisabled ? 'disabled' : ''}>${packagingItemsState.catalogCreating === 'category' ? 'Создаем…' : 'Создать группу'}</button></form><form data-form="packaging-catalog-tag" class="catalog-create-form"><h3>Добавить метку</h3><label>Название метки<input name="name" required maxlength="160" placeholder="Например, Для кремов" ${tagDisabled ? 'disabled' : ''} /></label><button class="secondary-action" type="submit" ${tagDisabled ? 'disabled' : ''}>${packagingItemsState.catalogCreating === 'tag' ? 'Создаем…' : 'Создать метку'}</button></form></div>`;
}

function packagingItemsList() {
  if (packagingItemsState.items.length === 0) return `<section class="card empty-card"><h2>Тара пока не добавлена</h2><p>Тара пока не добавлена. Создайте первую баночку, флакон или этикетку.</p><p class="next-step">Следующее действие: заполните форму «Добавить тару» и нажмите «Создать тару».</p></section>`;
  return `<section class="card data-card"><p class="card-kicker">Список</p><h2>Тара и расходники</h2><div class="table-wrap"><table><thead><tr><th>Название</th><th>Тип</th><th>Моя группа</th><th>Метки</th><th>Ед. учета</th><th>Объем</th><th>Материал</th><th>Поставщик</th><th>Цена</th><th>Статус</th><th>Действия</th></tr></thead><tbody>${packagingItemsState.items.map((item) => `<tr><td><strong>${escapeHtml(item.name)}</strong><small>${item.notes ? escapeHtml(item.notes) : 'Без заметок'}</small></td><td>${packagingKindLabel(item.kind)}</td><td>${escapeHtml(packagingCatalogCategoryLabel(item))}</td><td>${packagingTagChips(item)}</td><td>${unitLabel(item.unit)}</td><td>${packagingItemCapacityLabel(item)}</td><td>${escapeHtml(item.material || 'Не указан')}</td><td>${escapeHtml(item.supplier_hint || 'Не указан')}</td><td>${item.unit_cost ? escapeHtml(item.unit_cost) : 'Не указана'}</td><td><span class="pill ${item.is_active ? 'success' : 'muted'}">${item.is_active ? 'Активна' : 'Неактивна'}</span></td><td><div class="row-actions"><button class="secondary-action compact" type="button" data-action="edit-packaging-item" data-id="${item.id}">Изменить</button>${item.is_active ? `<button class="secondary-action compact danger-action" type="button" data-action="deactivate-packaging-item" data-id="${item.id}">Деактивировать</button>` : ''}</div></td></tr>`).join('')}</tbody></table></div><p class="next-step">Здесь редактируется только карточка тары. Остатки не вводятся и не пересчитываются на этой странице.</p></section>`;
}

function ingredientLotsPage() {
  if (ingredientLotsStatus === 'idle' || ingredientLotsStatus === 'loading') return `<section class="card"><p class="card-kicker">Приходы и партии</p><h2>Загружаем приходы и партии…</h2><p>Получаем партии компонентов из локального API.</p></section>`;
  if (ingredientLotsStatus === 'error') return `<section class="card error-card"><p class="card-kicker">Приходы и партии</p><h2>Не удалось загрузить приходы и партии</h2><p>${ingredientLotsError || 'Локальный API временно недоступен.'}</p><p class="next-step">Проверьте, что приложение запущено полностью, и попробуйте обновить раздел.</p><button class="primary-action" type="button" data-action="reload-ingredient-lots">Повторить загрузку</button></section>`;
  return `<div class="catalog-layout"><section class="card catalog-intro"><div><p class="card-kicker">Приходы и партии</p><h2>Приходы и партии сырья</h2><p>Здесь хранится паспорт партии: компонент, поставщик, срок годности, цена и единица учета. Остаток не редактируется здесь и считается отдельными движениями сырья.</p></div><button class="secondary-action" type="button" data-action="new-ingredient-lot">Очистить форму</button></section>${ingredientLotsMessage ? `<p class="page-message">${ingredientLotsMessage}</p>` : ''}${ingredientLotsError ? `<p class="page-message error-message">${ingredientLotsError}</p>` : ''}${ingredientLotForm()}${ingredientLotList()}</div>`;
}

function ingredientLotForm() {
  const form = ingredientLotsState.form;
  const isEdit = ingredientLotsState.formMode === 'edit';
  const hasIngredients = ingredientLotsState.ingredients.length > 0;
  return `<section class="card form-card"><p class="card-kicker">${isEdit ? 'Редактирование' : 'Создание'}</p><h2>${isEdit ? 'Изменить партию' : 'Создать партию компонента'}</h2><p class="next-step">Количество партии добавляется отдельным движением сырья. Здесь хранится информация о партии: поставщик, срок годности, цена и единица учета.</p><form data-form="ingredient-lot" class="ingredient-form"><div class="form-grid"><label>Компонент<select name="ingredient_id" required ${hasIngredients ? '' : 'disabled'}><option value="">Выберите компонент</option>${ingredientLotsState.ingredients.map((item) => `<option value="${item.id}" ${String(item.id) === form.ingredient_id ? 'selected' : ''}>${escapeHtml(item.name)}</option>`).join('')}</select></label><label>Код партии<input name="lot_code" maxlength="120" value="${escapeHtml(form.lot_code)}" placeholder="Например, LOT-2026-01" /></label><label>Поставщик<input name="supplier_name" maxlength="160" value="${escapeHtml(form.supplier_name)}" placeholder="Необязательно" /></label><label>Единица учета<select name="unit">${lotUnitOptions(form.unit)}</select></label><label>Цена за единицу<input name="unit_cost" inputmode="decimal" value="${escapeHtml(form.unit_cost)}" placeholder="Например, 12.50" /></label><label>Общая стоимость<input name="total_cost" inputmode="decimal" value="${escapeHtml(form.total_cost)}" placeholder="Необязательно" /></label><label>Плотность<input name="density_g_per_ml" inputmode="decimal" value="${escapeHtml(form.density_g_per_ml)}" placeholder="Например, 0.950" /></label><label>Дата покупки<input name="purchased_at" type="date" value="${escapeHtml(form.purchased_at)}" /></label><label>Срок годности<input name="expires_at" type="date" value="${escapeHtml(form.expires_at)}" /></label><label class="full-span">Заметки<textarea name="notes" rows="3" maxlength="1200" placeholder="Короткие рабочие заметки о партии">${escapeHtml(form.notes)}</textarea></label></div><div class="actions"><button class="primary-action" type="submit" ${hasIngredients ? '' : 'disabled'}>${isEdit ? 'Сохранить изменения' : 'Создать партию'}</button>${isEdit ? '<button class="secondary-action" type="button" data-action="new-ingredient-lot">Отменить редактирование</button>' : ''}</div>${hasIngredients ? '' : '<p class="next-step">Сначала создайте активный компонент в разделе «Компоненты», затем вернитесь к партиям.</p>'}</form></section>`;
}

function ingredientLotList() {
  if (ingredientLotsState.lots.length === 0) return `<section class="card empty-card"><h2>Пока нет партий компонентов</h2><p>Создайте партию, чтобы указать поставщика, срок годности и цену закупки.</p><p class="next-step">Остаток считается по движениям склада. Чтобы добавить количество, используйте движение склада — это будет отдельный шаг.</p></section>`;
  return `<section class="card data-card"><p class="card-kicker">Список</p><h2>Приходы и партии</h2><div class="table-wrap"><table><thead><tr><th>Компонент</th><th>Партия</th><th>Поставщик</th><th>Ед. учета</th><th>Цена за единицу</th><th>Плотность</th><th>Дата покупки</th><th>Срок годности</th><th>Статус</th><th>Действия</th></tr></thead><tbody>${ingredientLotsState.lots.map((lot) => `<tr><td><strong>${escapeHtml(lotIngredientName(lot.ingredient_id))}</strong></td><td>${escapeHtml(lot.lot_code || 'Без номера')}<small>${escapeHtml(lot.notes || '')}</small></td><td>${escapeHtml(lot.supplier_name || 'Не указан')}</td><td>${unitLabel(lot.unit)}</td><td>${lot.unit_cost ? escapeHtml(lot.unit_cost) : 'Не указана'}</td><td>${lot.density_g_per_ml ? `${escapeHtml(lot.density_g_per_ml)} г/мл` : 'Не указана'}</td><td>${formatDate(lot.purchased_at)}</td><td>${formatDate(lot.expires_at)}</td><td><span class="pill ${lotStatusClass(lot)}">${lotStatusLabel(lot)}</span></td><td><div class="row-actions"><button class="secondary-action compact" type="button" data-action="edit-ingredient-lot" data-id="${lot.id}">Изменить</button>${lot.is_active ? `<button class="secondary-action compact danger-action" type="button" data-action="deactivate-ingredient-lot" data-id="${lot.id}">Деактивировать</button>` : ''}</div></td></tr>`).join('')}</tbody></table></div><p class="next-step">Остаток партии не редактируется в этой таблице: он будет считаться по движениям склада.</p></section>`;
}


function stockMovementsPage() {
  if (stockMovementsStatus === 'idle' || stockMovementsStatus === 'loading') return `<section class="card"><p class="card-kicker">Движения сырья</p><h2>Загружаем движения…</h2><p>Получаем партии компонентов и историю движений из локального API.</p></section>`;
  if (stockMovementsStatus === 'error') return `<section class="card error-card"><p class="card-kicker">Движения сырья</p><h2>Не удалось загрузить движения сырья</h2><p>${stockMovementsError || 'Локальный API временно недоступен.'}</p><p class="next-step">Проверьте, что приложение запущено полностью, и попробуйте обновить раздел.</p><button class="primary-action" type="button" data-action="reload-stock-movements">Повторить загрузку</button></section>`;
  if (stockMovementsState.lots.length === 0) return `<div class="catalog-layout"><section class="card catalog-intro"><div><p class="card-kicker">Движения сырья</p><h2>История движений компонентов</h2><p>Остаток партии считается по движениям. Старые движения не редактируются, чтобы история склада оставалась честной.</p></div><button class="secondary-action" type="button" data-action="reload-stock-movements">Обновить</button></section><section class="card empty-card"><h2>Пока нет партий для движений</h2><p>Сначала создайте компонент и партию. После этого можно будет добавить приход или списание.</p><p class="next-step">Текущий остаток нельзя ввести вручную: он появится после первого движения сырья.</p></section></div>`;
  return `<div class="catalog-layout"><section class="card catalog-intro"><div><p class="card-kicker">Движения сырья</p><h2>Движения сырья</h2><p>Остаток партии считается по движениям. Старые движения не редактируются, чтобы история склада оставалась честной.</p></div><button class="secondary-action" type="button" data-action="reload-stock-movements">Обновить</button></section>${stockMovementsMessage ? `<p class="page-message">${stockMovementsMessage}</p>` : ''}${stockMovementsError ? `<p class="page-message error-message">${stockMovementsError}</p>` : ''}${stockLotSelector()}${stockMovementForm()}${stockMovementHistory()}</div>`;
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
    ['Приходы и партии', overview.ingredient_lots_total], ['Есть остаток', overview.ingredient_lots_with_positive_balance], ['Нулевой остаток', overview.ingredient_lots_zero_balance], ['Просрочено', overview.ingredient_lots_expired], ['Скоро истекает', overview.ingredient_lots_expiring_soon], ['Тара', overview.packaging_items_total], ['Тара в наличии', overview.packaging_items_with_positive_balance], ['Тара без остатка', overview.packaging_items_zero_balance],
  ];
  return `<section class="overview-grid" aria-label="Сводка склада">${cards.map(([label, value]) => `<article class="metric-card"><span>${label}</span><strong>${value}</strong></article>`).join('')}</section>`;
}

function ingredientLotsTable(rows: IngredientLotBalance[]) {
  if (rows.length === 0) return emptyCard('Приходы и партии не найдены', 'Когда будут добавлены компоненты, партии и движения сырья, остатки появятся в этой таблице.');
  return `<section class="card data-card"><p class="card-kicker">Компоненты</p><h2>Приходы и партии в учете</h2><div class="table-wrap"><table><thead><tr><th>Компонент</th><th>Партия</th><th>Поставщик</th><th>Остаток</th><th>Ед.</th><th>Срок годности</th><th>Статус</th></tr></thead><tbody>${rows.map((row) => `<tr><td>${escapeHtml(row.ingredient_name)}</td><td>${escapeHtml(row.lot_code || 'Без номера')}</td><td>${escapeHtml(row.supplier || 'Не указан')}</td><td>${escapeHtml(row.balance_quantity)}</td><td>${unitLabel(row.unit)}</td><td>${formatDate(row.expiration_date)}</td><td><span class="pill ${ingredientStatusClass(row)}">${ingredientStatus(row)}</span></td></tr>`).join('')}</tbody></table></div></section>`;
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
function unitLabel(unit: string) { return ({ g: 'г', ml: 'мл', percent: '%', '%': '%', pcs: 'шт.' } as Record<string, string>)[unit] ?? escapeHtml(unit); }
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
function plannedSectionPlaceholder(section: NavigationSection) {
  const copy: Record<string, { title: string; now: string }> = {
    Заказы: { title: 'Заказы', now: 'Пока можно вести клиентов, рецепты и индивидуальные рецепты; заказы будут подключены отдельным безопасным шагом.' },
    Закупки: { title: 'Закупки', now: 'Пока можно заполнить компоненты, приходы и партии, тару и складские движения; рекомендации закупок появятся позже.' },
    Готовность: { title: 'Готовность производства', now: 'Пока можно проверить рецепты, компоненты, партии и тару вручную в складских разделах.' },
    Производство: { title: 'Производство', now: 'Пока можно подготовить рецепты, клиентов, компоненты, партии и тару; подтверждение производства и списание склада появятся позже.' },
    Импорт: { title: 'Импорт данных', now: 'Пока данные нужно добавлять через готовые формы компонентов, партий, тары, рецептов и клиентов.' },
    Отчеты: { title: 'Отчеты', now: 'Пока можно смотреть текущие списки и складской обзор; сводные отчеты появятся отдельным модулем.' },
    Настройки: { title: 'Настройки', now: 'Пока используются базовые локальные настройки приложения; пользовательский экран настроек появится позже.' },
    Помощь: { title: 'Помощь', now: 'Пока ориентируйтесь на понятные подсказки внутри рабочих разделов; отдельная справка появится позже.' },
  };
  const item = copy[section] ?? { title: labelForSection(section), now: 'Пока используйте готовые рабочие разделы из бокового меню.' };
  return `<section class="card planned-card"><p class="card-kicker">Запланированный модуль</p><h2>${escapeHtml(item.title)}</h2><p>Этот модуль запланирован, но еще не доступен в текущем MVP-срезе.</p><p class="next-step">Что можно сделать сейчас: ${escapeHtml(item.now)}</p></section>`;
}


function recipesPage() {
  if (recipesStatus === 'idle' || recipesStatus === 'loading') return `<section class="card"><p class="card-kicker">Рецепты</p><h2>Загружаем рецепты…</h2><p>Получаем шаблоны рецептов, версии и компоненты из локального API.</p></section>`;
  if (recipesStatus === 'error') return `<section class="card error-card"><p class="card-kicker">Рецепты</p><h2>Не удалось загрузить рецепты</h2><p>${recipesError || 'Локальный API временно недоступен.'}</p><p class="next-step">Проверьте, что приложение запущено полностью, и попробуйте обновить раздел.</p><button class="primary-action" type="button" data-action="reload-recipes">Повторить загрузку</button></section>`;
  return `<div class="recipes-layout"><section class="card recipes-intro"><div><p class="card-kicker">Рецепты</p><h2>Рабочее пространство рецептов</h2><p>Создавайте базовые рецепты и новые версии состава. Уже созданные версии здесь только просматриваются и рассчитываются — история не редактируется.</p></div><button class="secondary-action" type="button" data-action="reload-recipes">Обновить</button></section>${recipesMessage ? `<p class="page-message">${recipesMessage}</p>` : ''}${recipesError ? `<p class="page-message error-message">${recipesError}</p>` : ''}<div class="recipe-columns"><div>${recipeTemplateForm()}${recipeTemplateList()}</div><div>${recipeCatalogPanel()}${recipeDetailPanel()}</div></div></div>`;
}
function recipeTemplateForm() { const f = recipesState.templateForm; return `<section class="card form-card"><p class="card-kicker">Новый рецепт</p><h2>Создать рецепт</h2><form data-form="recipe-template" class="ingredient-form"><div class="form-grid"><label>Название рецепта<input name="name" required maxlength="160" value="${escapeHtml(f.name)}" placeholder="Например, базовый дневной крем" /></label><label>Тип продукта<input name="product_type" maxlength="120" value="${escapeHtml(f.product_type)}" placeholder="Крем, гель, тоник…" /></label><label class="full-span">Описание<textarea name="description" rows="3" maxlength="1200">${escapeHtml(f.description)}</textarea></label><label class="full-span">Заметки<textarea name="notes" rows="3" maxlength="1200">${escapeHtml(f.notes)}</textarea></label></div><div class="actions"><button class="primary-action" type="submit">Создать рецепт</button></div></form></section>`; }
function recipeTemplateList() { if (recipesState.templates.length === 0) return `<section class="card empty-card"><h2>Пока нет рецептов</h2><p>Пока нет рецептов. Сначала создайте базовый рецепт, затем добавьте версию с составом.</p><p class="next-step">Следующее действие: заполните форму «Создать рецепт».</p></section>`; return `<section class="card data-card"><p class="card-kicker">Список</p><h2>Рецепты</h2><div class="recipe-list">${recipesState.templates.map((t)=>`<article class="recipe-list-item ${recipesState.selectedTemplate?.id===t.id?'selected':''}"><div><strong>${escapeHtml(t.name)}</strong><small>${escapeHtml(t.product_type || 'Тип продукта не указан')} · <span class="pill ${t.is_active?'success':'muted'}">${t.is_active?'Активен':'Неактивен'}</span></small><small>Моя группа: ${escapeHtml(recipeCatalogCategoryLabel(t))}</small>${recipeTagChips(t)}</div><button class="secondary-action compact" type="button" data-action="open-recipe" data-id="${t.id}">Открыть</button></article>`).join('')}</div></section>`; }
function recipeCatalogPanel() { const template = recipesState.selectedTemplate; if (!template) return `<section class="card empty-card"><p class="card-kicker">Моя организация каталога</p><h2>Моя группа и метки</h2><p>Выберите рецепт, чтобы назначить ему группу и метки.</p><p class="next-step">Группы и метки помогают навести порядок в рецептах. Они не меняют версии рецепта и состав формулы.</p></section>`; const categoryDisabled = recipesState.catalogCreating === 'category'; const tagDisabled = recipesState.catalogCreating === 'tag'; return `<section class="card form-card"><p class="card-kicker">Моя организация каталога</p><h2>Моя группа и метки</h2><p>Группы и метки помогают навести порядок в рецептах. Они не меняют версии рецепта и состав формулы.</p><div class="catalog-classification"><label>Моя группа<select data-action="assign-recipe-category" data-id="${template.id}" ${recipesState.catalogSaving === 'saving' ? 'disabled' : ''}><option value="">Без моей группы</option>${recipesState.catalogCategories.map((category) => `<option value="${category.id}" ${category.id === template.catalog_category_id ? 'selected' : ''}>${escapeHtml(category.name)}</option>`).join('')}</select></label>${recipesState.catalogCategories.length === 0 ? '<p class="empty-hint">Группы рецептов пока не созданы. Создайте первую группу ниже.</p>' : ''}<div><strong>Метки</strong>${recipesState.catalogTags.length === 0 ? '<p class="empty-hint">Метки рецептов пока не созданы. Создайте первую метку ниже.</p>' : `<div class="tag-picker">${recipesState.catalogTags.map((tag) => `<label class="tag-chip ${template.catalog_tag_ids.includes(tag.id) ? 'selected' : ''}"><input type="checkbox" data-action="toggle-recipe-tag" data-recipe-template-id="${template.id}" value="${tag.id}" ${template.catalog_tag_ids.includes(tag.id) ? 'checked' : ''} ${recipesState.catalogSaving === 'saving' ? 'disabled' : ''} />${escapeHtml(tag.name)}</label>`).join('')}</div>`}</div></div><div class="catalog-create-grid"><form data-form="recipe-catalog-category" class="catalog-create-form"><h3>Добавить группу рецептов</h3><label>Название группы<input name="name" required maxlength="160" placeholder="Например, Кремы" ${categoryDisabled ? 'disabled' : ''} /></label><button class="secondary-action" type="submit" ${categoryDisabled ? 'disabled' : ''}>${recipesState.catalogCreating === 'category' ? 'Создаем…' : 'Создать группу'}</button></form><form data-form="recipe-catalog-tag" class="catalog-create-form"><h3>Добавить метку рецепта</h3><label>Название метки<input name="name" required maxlength="160" placeholder="Например, Для сухой кожи" ${tagDisabled ? 'disabled' : ''} /></label><button class="secondary-action" type="submit" ${tagDisabled ? 'disabled' : ''}>${recipesState.catalogCreating === 'tag' ? 'Создаем…' : 'Создать метку'}</button></form></div><p class="next-step">Группа и метки сохраняются сразу. Они помогают найти рецепт, но не меняют его версии и состав.</p></section>`; }
function recipeDetailPanel() { const template = recipesState.selectedTemplate; if (!template) return `<section class="card empty-card"><h2>Выберите рецепт</h2><p>Откройте рецепт из списка, чтобы увидеть версии, состав и расчет.</p><p class="next-step">Исторические версии не редактируются: для изменений создается новая версия.</p></section>`; return `<div class="recipe-detail-stack"><section class="card"><p class="card-kicker">Рецепт</p><h2>${escapeHtml(template.name)}</h2><p><strong>Тип:</strong> ${escapeHtml(template.product_type || 'не указан')}</p><p>${escapeHtml(template.description || 'Описание пока не заполнено.')}</p>${template.notes ? `<p class="next-step">${escapeHtml(template.notes)}</p>` : ''}<span class="pill ${template.is_active?'success':'muted'}">${template.is_active?'Активен':'Неактивен'}</span></section>${recipeVersionsList()}${recipeVersionForm()}${recipeVersionDetailPanel()}</div>`; }
function recipeVersionsList() { if (recipesState.versions.length === 0) return `<section class="card empty-card"><h2>Версий пока нет</h2><p>У рецепта пока нет версий. Создайте первую версию и добавьте состав из компонентов.</p></section>`; return `<section class="card data-card"><p class="card-kicker">Версии</p><h2>Версии рецепта</h2><div class="table-wrap"><table><thead><tr><th>Версия</th><th>Статус</th><th>Заголовок</th><th>Партия</th><th>Создана</th><th>Действие</th></tr></thead><tbody>${recipesState.versions.map((v)=>`<tr><td>№${v.version_number}</td><td><span class="pill ${versionStatusClass(v.status)}">${versionStatusLabel(v.status)}</span></td><td>${escapeHtml(v.title || 'Без заголовка')}</td><td>${batchLabel(v.target_batch_size_value, v.target_batch_size_unit)}</td><td>${formatDateTime(v.created_at)}</td><td><button class="secondary-action compact" type="button" data-action="open-version" data-id="${v.id}">Открыть</button></td></tr>`).join('')}</tbody></table></div></section>`; }
function recipeVersionForm() { const f=recipesState.versionForm; const noIngredients = recipesState.ingredients.length === 0; return `<section class="card form-card"><p class="card-kicker">Новая версия рецепта</p><h2>Новая версия рецепта</h2><p class="next-step">Сохранение создаст новую историческую версию. Уже сохраненная версия не изменится${recipesState.selectedVersionDetail ? `; новая версия будет связана с версией №${recipesState.selectedVersionDetail.version.version_number} как с источником.` : '.'}</p><form data-form="recipe-version" class="ingredient-form"><div class="form-grid"><label>Заголовок версии<input name="title" maxlength="160" value="${escapeHtml(f.title)}" placeholder="Например, v1 с ниацинамидом" /></label><label>Статус<select name="status">${['draft','active','archived'].map((x)=>`<option value="${x}" ${f.status===x?'selected':''}>${versionStatusLabel(x)}</option>`).join('')}</select></label><label>Размер партии<input name="target_batch_size_value" inputmode="decimal" value="${escapeHtml(f.target_batch_size_value)}" placeholder="Например, 100" /></label><label>Единица партии<select name="target_batch_size_unit">${['g','ml','pcs'].map((x)=>`<option value="${x}" ${f.target_batch_size_unit===x?'selected':''}>${unitLabel(x)}</option>`).join('')}</select></label><label class="full-span">Комментарий к изменениям<textarea name="change_note" rows="2">${escapeHtml(f.change_note)}</textarea></label><label class="full-span">Заметки<textarea name="notes" rows="2">${escapeHtml(f.notes)}</textarea></label></div><h3>Конструктор состава</h3><p class="next-step">Соберите состав из компонентов справочника. После сохранения будет создана новая версия рецепта. Сохраненные версии не изменяются автоматически.</p><p class="empty-hint">Фазы A, B, C и D помогают читать формулу по шагам приготовления. Позиция задает порядок строк внутри версии.</p>${noIngredients ? '<p class="empty-hint">В рецепте пока нельзя выбрать компонент: активные компоненты не найдены. Создайте компонент в разделе «Компоненты» или обновите список.</p><p class="next-step">Если компонент уже создан, нажмите «Обновить компоненты» и проверьте, что он не архивирован.</p>' : ''}<div class="recipe-lines">${f.ingredients.map(recipeLineForm).join('')}</div>${draftPercentHint()}<div class="actions"><button class="secondary-action" type="button" data-action="add-recipe-line" ${noIngredients ? 'disabled' : ''}>Добавить строку</button><button class="secondary-action" type="button" data-action="reload-recipe-ingredients">Обновить компоненты</button><button class="primary-action" type="submit" ${noIngredients ? 'disabled' : ''}>Сохранить новую версию</button></div></form></section>`; }
function recipeLineForm(line: RecipeLineForm, index: number) { const noIngredients = recipesState.ingredients.length === 0; return `<fieldset class="recipe-line"><legend>Строка ${index+1} · Фаза ${escapeHtml(line.phase || 'A')}</legend><label>Позиция<input name="position_${index}" required inputmode="numeric" value="${escapeHtml(line.position)}" placeholder="${index + 1}" /></label><label>Фаза<select name="phase_${index}">${phaseOptions(line.phase)}</select></label><label>Компонент<select name="ingredient_id_${index}" required ${noIngredients ? 'disabled' : ''}><option value="">${noIngredients ? 'Нет активных компонентов' : 'Выберите компонент'}</option>${recipesState.ingredients.map((i)=>`<option value="${i.id}" ${line.ingredient_id===String(i.id)?'selected':''}>${escapeHtml(i.name)}</option>`).join('')}</select></label><label>Количество<input name="amount_value_${index}" required inputmode="decimal" value="${escapeHtml(line.amount_value)}" placeholder="Например, 5 или 2.5" /></label><label>Единица<select name="amount_unit_${index}">${['percent','g','ml','pcs'].map((u)=>`<option value="${u}" ${line.amount_unit===u?'selected':''}>${unitLabel(u)}</option>`).join('')}</select></label><label class="full-span">Заметка<input name="notes_${index}" value="${escapeHtml(line.notes)}" placeholder="Необязательно" /></label>${recipesState.versionForm.ingredients.length>1?`<button class="secondary-action compact danger-action" type="button" data-action="remove-recipe-line" data-index="${index}">Удалить строку</button>`:''}</fieldset>`; }
function recipeVersionDetailPanel() { if (recipesState.versionDetailStatus === 'loading') return `<section class="card"><h2>Загружаем версию…</h2><p>Получаем сохраненный состав и расчет из backend.</p></section>`; if (recipesState.versionDetailStatus === 'error') return `<section class="card error-card"><h2>Не удалось загрузить версию рецепта</h2><p>Попробуйте открыть версию еще раз или обновить раздел.</p></section>`; const d=recipesState.selectedVersionDetail; if (!d) return ''; const v=d.version; const lines = d.ingredients.slice().sort((a,b)=>a.phase.localeCompare(b.phase) || a.position-b.position); return `<section class="card data-card"><p class="card-kicker">Сохраненная версия</p><h2>Версия №${v.version_number}</h2><p><strong>${escapeHtml(v.title || 'Без заголовка')}</strong> · ${versionStatusLabel(v.status)} · ${batchLabel(v.target_batch_size_value, v.target_batch_size_unit)}</p><p><strong>Комментарий к изменениям:</strong> ${escapeHtml(v.change_note || 'Не указан')}</p><p><strong>Заметки:</strong> ${escapeHtml(v.notes || 'Нет заметок')}</p><p class="next-step">Это сохраненная версия рецепта. Чтобы изменить состав, создайте новую версию на ее основе.</p>${d.ingredients.length===0?'<p class="empty-hint">В этой версии пока нет состава. Создайте новую версию с компонентами, чтобы использовать ее в индивидуальных рецептах и производстве.</p>':`<div class="table-wrap"><table><thead><tr><th>Позиция</th><th>Фаза</th><th>Компонент</th><th>Количество</th><th>Заметки</th></tr></thead><tbody>${lines.map((line)=>`<tr><td>${line.position}</td><td>${escapeHtml(line.phase || 'Не указана')}</td><td>${escapeHtml(ingredientName(line.ingredient_id))}</td><td>${escapeHtml(line.amount_value)} ${unitLabel(line.amount_unit)}</td><td>${escapeHtml(line.notes || 'Без заметок')}</td></tr>`).join('')}</tbody></table></div>`}${calculationPanel()}</section>`; }
function calculationPanel() { const c=recipesState.calculation; return `<div class="calculation-panel"><h3>Расчет версии</h3><form data-form="recipe-calculation" class="inline-form"><label>Целевой размер партии<input name="target_batch_size_value" inputmode="decimal" value="${escapeHtml(recipesState.calculationTargetValue)}" placeholder="Оставьте пустым для размера версии" /></label><label>Единица<select name="target_batch_size_unit"><option value="g" ${recipesState.calculationTargetUnit==='g'?'selected':''}>г</option><option value="ml" ${recipesState.calculationTargetUnit==='ml'?'selected':''}>мл</option></select></label><button class="primary-action" type="submit">Пересчитать</button></form>${calculationStatus==='loading'?'<p>Считаем на backend…</p>':''}${calculationError?`<p class="page-message error-message">${calculationError}</p>`:''}${c?calculationResult(c):'<p class="next-step">Backend расчет загрузится автоматически для сохраненной версии. Если нужно, укажите другой размер партии и пересчитайте.</p>'}</div>`; }
function calculationResult(c: RecipeCalculationResult) { return `<div class="calculation-result"><p><strong>Можно рассчитать:</strong> ${c.can_calculate?'да':'нет'} · <strong>Сумма процентов:</strong> ${escapeHtml(c.percent_total)}%</p>${c.issues.length?`<h4>${c.issues.some((i)=>i.severity==='error')?'Нужно исправить':'Предупреждения'}</h4><ul class="issue-list">${c.issues.map((i)=>`<li class="${i.severity==='error'?'danger-text':'warning-text'}">${escapeHtml(i.message)}${i.next_action?` <small>${escapeHtml(i.next_action)}</small>`:''}</li>`).join('')}</ul>`:''}<h4>Состав</h4>${c.lines.length?`<div class="table-wrap"><table><thead><tr><th>Компонент</th><th>Исходно</th><th>Рассчитано</th><th>Фаза</th><th>Комментарий</th></tr></thead><tbody>${c.lines.map((l)=>`<tr><td>${escapeHtml(l.ingredient_name)}</td><td>${escapeHtml(l.source_amount_value)} ${unitLabel(l.source_amount_unit)}</td><td>${l.calculated_amount_value?`${escapeHtml(l.calculated_amount_value)} ${unitLabel(l.calculated_amount_unit || '')}`:'—'}</td><td>${escapeHtml(l.phase || 'Не указана')}</td><td>${escapeHtml(l.calculation_note || '')}</td></tr>`).join('')}</tbody></table></div>`:'<p>Backend не вернул расчетных строк.</p>'}<h4>Итого по единицам</h4>${c.totals_by_unit.length?`<ul>${c.totals_by_unit.map((t)=>`<li>${escapeHtml(t.total_value)} ${unitLabel(t.unit)}</li>`).join('')}</ul>`:'<p>Итоги пока не рассчитаны.</p>'}</div>`; }


function emptyPackagingItemForm(): PackagingItemFormState { return { id: null, name: '', kind: 'jar', unit: 'pcs', capacity_value: null, capacity_unit: null, material: '', supplier_hint: '', unit_cost: null, notes: '' }; }
function packagingKindLabel(kind: string) { return ({ jar: 'Баночка', bottle: 'Флакон', tube: 'Туба', pump: 'Помпа', cap: 'Крышка', dropper: 'Пипетка', label: 'Этикетка', box: 'Коробка', bag: 'Пакет', other: 'Другое' } as Record<string, string>)[kind] ?? escapeHtml(kind); }
function packagingKindOptions(current: string) { return ['jar','bottle','tube','pump','cap','dropper','label','box','bag','other'].map((value) => `<option value="${value}" ${value === current ? 'selected' : ''}>${packagingKindLabel(value)}</option>`).join(''); }
function packagingUnitOptions(current: string) { return ['pcs'].map((value) => `<option value="${value}" ${value === current ? 'selected' : ''}>${unitLabel(value)}</option>`).join(''); }
function capacityUnitOptions(current: string) { return ['ml','g'].map((value) => `<option value="${value}" ${value === current ? 'selected' : ''}>${unitLabel(value)}</option>`).join(''); }
function packagingItemCapacityLabel(item: PackagingItem) { return item.capacity_value && item.capacity_unit ? `${escapeHtml(item.capacity_value)} ${unitLabel(item.capacity_unit)}` : 'Не указан'; }
function packagingItemPayloadFromForm(form: HTMLFormElement): PackagingItemPayload { const data = new FormData(form); const nullable = (name: string) => { const value = String(data.get(name) ?? '').trim(); return value || null; }; return { name: String(data.get('name') ?? '').trim(), kind: String(data.get('kind') ?? 'other'), unit: String(data.get('unit') ?? 'pcs'), capacity_value: nullable('capacity_value'), capacity_unit: nullable('capacity_unit'), material: String(data.get('material') ?? '').trim(), supplier_hint: String(data.get('supplier_hint') ?? '').trim(), unit_cost: nullable('unit_cost'), notes: String(data.get('notes') ?? '').trim() }; }

function packagingCatalogCategoryLabel(item: PackagingItem) { return packagingItemsState.catalogCategories.find((category) => category.id === item.catalog_category_id)?.name ?? 'Не выбрана'; }
function packagingTagChips(item: PackagingItem) { const tags = item.catalog_tag_ids.map((id) => packagingItemsState.catalogTags.find((tag) => tag.id === id)).filter((tag): tag is CatalogTag => Boolean(tag)); return tags.length ? `<div class="tag-list">${tags.map((tag) => `<span class="tag-chip readonly">${escapeHtml(tag.name)}</span>`).join('')}</div>` : 'Нет меток'; }

function emptyIngredientLotForm(): IngredientLotFormState { return { id: null, ingredient_id: '', lot_code: '', supplier_name: '', purchased_at: '', expires_at: '', unit: 'g', unit_cost: '', total_cost: '', density_g_per_ml: '', notes: '' }; }
function lotUnitOptions(current: string) { return ['g','ml','pcs'].map((value) => `<option value="${value}" ${value === current ? 'selected' : ''}>${unitLabel(value)}</option>`).join(''); }
function lotIngredientName(id: number) { return ingredientLotsState.ingredients.find((ingredient) => ingredient.id === id)?.name ?? 'Компонент'; }
function lotStatusLabel(lot: IngredientLot) { if (!lot.is_active) return 'Неактивна'; const status = expirationStatus(lot.expires_at); return status ?? 'Активна'; }
function lotStatusClass(lot: IngredientLot) { if (!lot.is_active) return 'muted'; const status = expirationStatus(lot.expires_at); if (status === 'Просрочена') return 'danger'; if (status === 'Скоро истекает') return 'warning'; if (status === 'Без срока годности') return 'muted'; return 'success'; }
function expirationStatus(value: string | null) { if (!value) return 'Без срока годности'; const today = new Date(); today.setHours(0, 0, 0, 0); const expires = new Date(`${value}T00:00:00`); const days = Math.ceil((expires.getTime() - today.getTime()) / 86400000); if (days < 0) return 'Просрочена'; if (days <= 30) return 'Скоро истекает'; return null; }
function ingredientLotPayloadFromForm(form: HTMLFormElement): IngredientLotPayload { const data = new FormData(form); const nullable = (name: string) => { const value = String(data.get(name) ?? '').trim(); return value || null; }; return { ingredient_id: Number(data.get('ingredient_id')), lot_code: String(data.get('lot_code') ?? '').trim(), supplier_name: String(data.get('supplier_name') ?? '').trim(), purchased_at: nullable('purchased_at'), expires_at: nullable('expires_at'), unit: String(data.get('unit') ?? 'g'), unit_cost: nullable('unit_cost'), total_cost: nullable('total_cost'), density_g_per_ml: nullable('density_g_per_ml'), notes: String(data.get('notes') ?? '').trim() }; }



function clientRecipeClientName(id: number) { return clientRecipesState.clients.find((c)=>c.id===id)?.full_name ?? `Клиент #${id}`; }
function clientRecipeIngredientName(id: number) { return recipesState.ingredients.find((i)=>i.id===id)?.name ?? ingredientsState.items.find((i)=>i.id===id)?.name ?? `Компонент #${id}`; }
function clientRecipePayloadFromForm(form: HTMLFormElement): ClientRecipePayload { const data = new FormData(form); const batch = String(data.get('target_batch_size_value') ?? '').trim(); return { client_id: Number(data.get('client_id')), source_recipe_version_id: Number(data.get('source_recipe_version_id')), title: String(data.get('title') ?? '').trim(), target_batch_size_value: batch || null, target_batch_size_unit: batch ? String(data.get('target_batch_size_unit') ?? 'g') : null, personalization_notes: String(data.get('personalization_notes') ?? '').trim(), allergy_notes: String(data.get('allergy_notes') ?? '').trim(), preference_notes: String(data.get('preference_notes') ?? '').trim(), contraindication_notes: String(data.get('contraindication_notes') ?? '').trim(), notes: String(data.get('notes') ?? '').trim() }; }
function saveClientRecipeFormFromDom() { const form = document.querySelector<HTMLFormElement>('[data-form="client-recipe"]'); if (!form) return; const data = new FormData(form); clientRecipesState.form = { client_id: String(data.get('client_id') ?? ''), recipe_template_id: String(data.get('recipe_template_id') ?? ''), source_recipe_version_id: String(data.get('source_recipe_version_id') ?? ''), title: String(data.get('title') ?? '').trim(), target_batch_size_value: String(data.get('target_batch_size_value') ?? '').trim(), target_batch_size_unit: String(data.get('target_batch_size_unit') ?? 'g'), personalization_notes: String(data.get('personalization_notes') ?? '').trim(), allergy_notes: String(data.get('allergy_notes') ?? '').trim(), preference_notes: String(data.get('preference_notes') ?? '').trim(), contraindication_notes: String(data.get('contraindication_notes') ?? '').trim(), notes: String(data.get('notes') ?? '').trim() }; }
function humanClientRecipeError(error: unknown) { const message = error instanceof Error ? error.message : ''; if (message.includes('Source recipe version has no ingredient lines')) return 'Не удалось создать индивидуальный рецепт: выбранная версия рецепта пустая. Добавьте состав в версии рецепта.'; if (message.includes('Client is inactive')) return 'Не удалось создать индивидуальный рецепт: выбранный клиент находится в архиве. Выберите активного клиента.'; if (message.includes('Ingredient is inactive')) return 'Не удалось создать индивидуальный рецепт: в версии рецепта есть архивный компонент. Проверьте состав версии.'; if (message.includes('Client was not found')) return 'Не удалось создать индивидуальный рецепт: выбранный клиент не найден. Обновите список клиентов.'; if (message.includes('Source recipe version was not found')) return 'Не удалось создать индивидуальный рецепт: выбранная версия рецепта не найдена. Обновите рецепты.'; return 'Не удалось создать индивидуальный рецепт. Проверьте клиента, версию рецепта и обязательные поля.'; }
function loadClientRecipes(force = false) { if (!force && (clientRecipesStatus === 'loading' || clientRecipesStatus === 'ready')) return; clientRecipesStatus = 'loading'; clientRecipesError = ''; render(); Promise.all([getClientRecipes(clientRecipesState.includeInactive), getClients(false), getRecipeTemplates(), getIngredients()]).then(([recipes, clients, templates, ingredients]) => { clientRecipesState.items = recipes.client_recipes; clientRecipesState.clients = clients.clients; clientRecipesState.templates = templates.recipe_templates; recipesState.ingredients = ingredients.ingredients; clientRecipesStatus = 'ready'; render(); }).catch(() => { clientRecipesStatus = 'error'; clientRecipesError = 'Не получилось получить индивидуальные рецепты, клиентов или базовые рецепты из локального API.'; render(); }); }
function selectClientRecipeTemplate(value: string) { saveClientRecipeFormFromDom(); clientRecipesState.form.recipe_template_id = value; clientRecipesState.form.source_recipe_version_id = ''; clientRecipesState.selectedTemplateId = value ? Number(value) : null; clientRecipesState.versions = []; clientRecipesError = ''; if (!value) { render(); return; } getRecipeVersions(Number(value)).then((response) => { clientRecipesState.versions = response.recipe_versions; render(); }).catch(() => { clientRecipesError = 'Не удалось загрузить версии выбранного рецепта. Попробуйте выбрать рецепт еще раз.'; render(); }); }
function submitClientRecipeForm(event: SubmitEvent) { event.preventDefault(); const form = event.currentTarget as HTMLFormElement; saveClientRecipeFormFromDom(); const payload = clientRecipePayloadFromForm(form); if (!payload.client_id) { clientRecipesError = 'Выберите клиента для индивидуального рецепта.'; clientRecipesMessage = ''; render(); return; } if (!payload.source_recipe_version_id) { clientRecipesError = 'Выберите версию рецепта. Если версий нет, создайте версию в разделе «Рецепты».'; clientRecipesMessage = ''; render(); return; } if (!payload.title) { clientRecipesError = 'Укажите название индивидуального рецепта, например «Крем для Анны: без отдушки».'; clientRecipesMessage = ''; render(); return; } createClientRecipe(payload).then((detail) => { clientRecipesMessage = 'Индивидуальный рецепт создан.'; clientRecipesError = ''; clientRecipesState.selectedDetail = detail; clientRecipesState.detailStatus = 'ready'; clientRecipesState.form = emptyClientRecipeForm(); clientRecipesState.versions = []; return getClientRecipes(clientRecipesState.includeInactive); }).then((response) => { clientRecipesState.items = response.client_recipes; clientRecipesStatus = 'ready'; render(); }).catch((error) => { clientRecipesMessage = ''; clientRecipesError = humanClientRecipeError(error); clientRecipesStatus = 'ready'; render(); }); }
function openClientRecipe(id: number) { clientRecipesState.detailStatus = 'loading'; clientRecipesError = ''; render(); getClientRecipe(id).then((detail) => { clientRecipesState.selectedDetail = detail; clientRecipesState.detailStatus = 'ready'; render(); }).catch(() => { clientRecipesState.detailStatus = 'error'; clientRecipesError = 'Не удалось открыть индивидуальный рецепт. Обновите список и попробуйте еще раз.'; render(); }); }
function deactivateClientRecipe(id: number) { const recipe = clientRecipesState.items.find((item)=>item.id===id); if (!recipe || !window.confirm('Архивировать индивидуальный рецепт? Карточка останется в истории, но не будет отображаться как активная.')) return; deactivateClientRecipeRequest(id).then(() => { clientRecipesMessage = 'Индивидуальный рецепт архивирован.'; clientRecipesError = ''; return getClientRecipes(clientRecipesState.includeInactive); }).then((response) => { clientRecipesState.items = response.client_recipes; if (clientRecipesState.selectedDetail?.client_recipe.id === id) clientRecipesState.selectedDetail = null; clientRecipesStatus = 'ready'; render(); }).catch(() => { clientRecipesMessage = ''; clientRecipesError = 'Не удалось архивировать индивидуальный рецепт. Попробуйте еще раз.'; clientRecipesStatus = 'ready'; render(); }); }

function emptyClientRecipeForm(): ClientRecipeFormState { return { client_id: '', recipe_template_id: '', source_recipe_version_id: '', title: '', target_batch_size_value: '', target_batch_size_unit: 'g', personalization_notes: '', allergy_notes: '', preference_notes: '', contraindication_notes: '', notes: '' }; }

function emptyClientForm(): ClientFormState { return { id: null, full_name: '', phone: '', email: '', address: '', birthday: null, skin_notes: '', allergy_notes: '', preference_notes: '', contraindication_notes: '', notes: '' }; }
function clientPayloadFromForm(form: HTMLFormElement): ClientPayload { const data = new FormData(form); const birthday = String(data.get('birthday') ?? '').trim(); return { full_name: String(data.get('full_name') ?? '').trim(), phone: String(data.get('phone') ?? '').trim(), email: String(data.get('email') ?? '').trim(), address: String(data.get('address') ?? '').trim(), birthday: birthday || null, skin_notes: String(data.get('skin_notes') ?? '').trim(), allergy_notes: String(data.get('allergy_notes') ?? '').trim(), preference_notes: String(data.get('preference_notes') ?? '').trim(), contraindication_notes: String(data.get('contraindication_notes') ?? '').trim(), notes: String(data.get('notes') ?? '').trim() }; }
function clientNotesSummary(client: Client) { const rows = [['Аллергии', client.allergy_notes], ['Предпочтения', client.preference_notes], ['Противопоказания', client.contraindication_notes]].filter(([, value]) => value); return rows.length ? `<ul>${rows.map(([label, value]) => `<li><strong>${label}:</strong> ${escapeHtml(value)}</li>`).join('')}</ul>` : 'Важные ограничения пока не указаны'; }
function loadClients(force = false) { if (!force && (clientsStatus === 'loading' || clientsStatus === 'ready')) return; clientsStatus = 'loading'; clientsError = ''; render(); getClients(clientsState.includeInactive).then((response) => { clientsState.items = response.clients; clientsStatus = 'ready'; render(); }).catch(() => { clientsStatus = 'error'; clientsError = 'Не удалось загрузить клиентов. Проверьте, что локальное приложение запущено.'; render(); }); }
function startEditClient(id: number) { const client = clientsState.items.find((item) => item.id === id); if (!client) return; clientsState.formMode = 'edit'; clientsState.form = { id: client.id, full_name: client.full_name, phone: client.phone, email: client.email, address: client.address, birthday: client.birthday, skin_notes: client.skin_notes, allergy_notes: client.allergy_notes, preference_notes: client.preference_notes, contraindication_notes: client.contraindication_notes, notes: client.notes }; clientsMessage = ''; clientsError = ''; render(); }
function submitClientForm(event: SubmitEvent) { event.preventDefault(); const payload = clientPayloadFromForm(event.currentTarget as HTMLFormElement); if (!payload.full_name) { clientsMessage = ''; clientsError = 'Укажите ФИО клиента, например «Анна Иванова».'; render(); return; } const isEdit = clientsState.formMode === 'edit' && clientsState.form.id; const request = isEdit ? updateClient(clientsState.form.id!, payload) : createClient(payload); request.then((client) => { clientsMessage = isEdit ? 'Карточка клиента обновлена.' : 'Клиент создан.'; clientsError = ''; clientsState.formMode = isEdit ? 'edit' : 'create'; clientsState.form = isEdit ? { ...payload, id: client.id } : emptyClientForm(); return getClients(clientsState.includeInactive); }).then((response) => { clientsState.items = response.clients; clientsStatus = 'ready'; render(); }).catch(() => { clientsMessage = ''; clientsError = 'Не удалось сохранить клиента. Проверьте ФИО и контактные поля, затем попробуйте еще раз.'; clientsStatus = 'ready'; render(); }); }
function deactivateClient(id: number) { const client = clientsState.items.find((item) => item.id === id); if (!client || !window.confirm('Архивировать клиента? Карточка останется в истории, но не будет отображаться в активном списке.')) return; deactivateClientRequest(id).then(() => { clientsMessage = 'Клиент архивирован.'; clientsError = ''; return getClients(clientsState.includeInactive); }).then((response) => { clientsState.items = response.clients; clientsStatus = 'ready'; if (clientsState.form.id === id) { clientsState.formMode = 'create'; clientsState.form = emptyClientForm(); } render(); }).catch(() => { clientsMessage = ''; clientsError = 'Не удалось архивировать клиента. Попробуйте еще раз.'; clientsStatus = 'ready'; render(); }); }


function ingredientSystemCategories() { return ['oil','butter','wax','emulsifier','humectant','active','preservative','fragrance','essential_oil','colorant','water_phase','additive','other']; }
function filteredIngredients() { return filterCatalogItems(ingredientsState.items, ingredientsState.filters, { getSearchText: ingredientSearchText, getCatalogCategoryId: (item) => item.catalog_category_id, getCatalogTagIds: (item) => item.catalog_tag_ids, getSystemType: (item) => item.category, getIsActive: (item) => item.is_active }); }
function ingredientSearchText(item: Ingredient) { return [item.name, item.supplier_hint, item.inci_name, item.notes, item.usage_note, item.allergen_note].join(' '); }
function catalogCategoryFilterValue(value: string): number | 'none' | '' { if (!value) return ''; if (value === 'none') return 'none'; return Number(value); }
function addIngredientTagFilter(value: string) { const id = Number(value); if (!id || ingredientsState.filters.tagIds.includes(id)) return; ingredientsState.filters.tagIds = [...ingredientsState.filters.tagIds, id]; render(); }
function removeIngredientTagFilter(id: number) { ingredientsState.filters.tagIds = ingredientsState.filters.tagIds.filter((tagId) => tagId !== id); render(); }
function clearIngredientFilter(filter: string) {
  if (filter === 'search') ingredientsState.filters.search = '';
  if (filter === 'category') ingredientsState.filters.categoryId = '';
  if (filter === 'system') ingredientsState.filters.systemType = '';
  if (filter === 'status') ingredientsState.filters.status = 'active';
  render();
}
function clearableIngredientFilterChip(label: string, filter: 'search' | 'category' | 'system' | 'status') { return `<span class="tag-chip selected">${label} <button type="button" data-action="clear-ingredient-filter" data-filter="${filter}" aria-label="Убрать фильтр ${label}">×</button></span>`; }
function ingredientActiveFilterChips() {
  const f = ingredientsState.filters;
  const chips: string[] = [];
  if (f.search.trim()) chips.push(clearableIngredientFilterChip(`Поиск: ${escapeHtml(f.search.trim())}`, 'search'));
  if (f.categoryId === 'none') chips.push(clearableIngredientFilterChip('Группа: Без группы', 'category'));
  if (typeof f.categoryId === 'number') chips.push(clearableIngredientFilterChip(`Группа: ${escapeHtml(ingredientsState.catalogCategories.find((category) => category.id === f.categoryId)?.name ?? 'Выбранная группа')}`, 'category'));
  if (f.systemType) chips.push(clearableIngredientFilterChip(`Системный тип: ${escapeHtml(categoryLabel(f.systemType))}`, 'system'));
  if (f.status !== 'active') chips.push(clearableIngredientFilterChip(`Статус: ${f.status === 'archived' ? 'Архив' : 'Все'}`, 'status'));
  return chips.join('');
}

function emptyIngredientForm(): IngredientFormState { return { id: null, name: '', category: 'other', default_unit: 'g', density_g_per_ml: null, notes: '', inci_name: '', supplier_hint: '', allergen_note: '', usage_note: '' }; }
function ingredientCatalogCategoryLabel(item: Ingredient) { return ingredientsState.catalogCategories.find((category) => category.id === item.catalog_category_id)?.name ?? 'Не выбрана'; }
function ingredientTagChips(item: Ingredient) { const tags = item.catalog_tag_ids.map((id) => ingredientsState.catalogTags.find((tag) => tag.id === id)).filter((tag): tag is CatalogTag => Boolean(tag)); return tags.length ? `<div class="tag-list">${tags.map((tag) => `<span class="tag-chip readonly">${escapeHtml(tag.name)}</span>`).join('')}</div>` : 'Нет меток'; }
function categoryLabel(category: string) { return ({ oil: 'Масло', butter: 'Баттер', wax: 'Воск', emulsifier: 'Эмульгатор', humectant: 'Увлажнитель', active: 'Актив', preservative: 'Консервант', fragrance: 'Отдушка', essential_oil: 'Эфирное масло', colorant: 'Краситель', water_phase: 'Водная фаза', additive: 'Добавка', other: 'Другое' } as Record<string, string>)[category] ?? category; }
function categoryOptions(current: string) { return ingredientSystemCategories().map((value) => `<option value="${value}" ${value === current ? 'selected' : ''}>${categoryLabel(value)}</option>`).join(''); }
function unitOptions(current: string) { return ['g','ml','percent','pcs'].map((value) => `<option value="${value}" ${value === current ? 'selected' : ''}>${unitLabel(value)}</option>`).join(''); }
function ingredientPayloadFromForm(form: HTMLFormElement): IngredientPayload { const data = new FormData(form); const density = String(data.get('density_g_per_ml') ?? '').trim(); return { name: String(data.get('name') ?? '').trim(), category: String(data.get('category') ?? 'other'), default_unit: String(data.get('default_unit') ?? 'g'), density_g_per_ml: density || null, notes: String(data.get('notes') ?? '').trim(), inci_name: String(data.get('inci_name') ?? '').trim(), supplier_hint: String(data.get('supplier_hint') ?? '').trim(), allergen_note: String(data.get('allergen_note') ?? '').trim(), usage_note: String(data.get('usage_note') ?? '').trim() }; }

function emptyRecipeTemplateForm(): RecipeTemplatePayload { return { name: '', product_type: '', description: '', notes: '' }; }
function emptyRecipeLine(position = 1): RecipeLineForm { return { ingredient_id: '', position: String(position), phase: 'A', amount_value: '', amount_unit: 'percent', notes: '' }; }
function emptyRecipeVersionForm(): RecipeVersionForm { return { title: '', status: 'draft', target_batch_size_value: '', target_batch_size_unit: 'g', notes: '', change_note: '', ingredients: [emptyRecipeLine()] }; }
function versionStatusLabel(status: string) { return ({ draft: 'Черновик', active: 'Активная', archived: 'Архивная' } as Record<string,string>)[status] ?? status; }
function versionStatusClass(status: string) { return status === 'active' ? 'success' : status === 'archived' ? 'muted' : 'warning'; }
function batchLabel(value: string | null, unit: string | null) { return value && unit ? `${escapeHtml(value)} ${unitLabel(unit)}` : 'Не указан'; }
function formatDateTime(value: string) { return value ? new Intl.DateTimeFormat('ru-RU', { dateStyle: 'short', timeStyle: 'short' }).format(new Date(value)) : 'Не указана'; }
function ingredientName(id: number) { return recipesState.ingredients.find((i)=>i.id===id)?.name ?? `Компонент #${id}`; }
function recipeCatalogCategoryLabel(item: RecipeTemplate) { return recipesState.catalogCategories.find((category) => category.id === item.catalog_category_id)?.name ?? 'Не выбрана'; }
function recipeTagChips(item: RecipeTemplate) { const tags = item.catalog_tag_ids.map((id) => recipesState.catalogTags.find((tag) => tag.id === id)).filter((tag): tag is CatalogTag => Boolean(tag)); return tags.length ? `<div class="tag-list">${tags.map((tag) => `<span class="tag-chip readonly">${escapeHtml(tag.name)}</span>`).join('')}</div>` : '<small>Метки: нет</small>'; }
function addRecipeLine() { saveVersionFormFromDom(); recipesState.versionForm.ingredients.push(emptyRecipeLine(recipesState.versionForm.ingredients.length + 1)); render(); }
function removeRecipeLine(index: number) { saveVersionFormFromDom(); recipesState.versionForm.ingredients.splice(index, 1); if (recipesState.versionForm.ingredients.length === 0) recipesState.versionForm.ingredients.push(emptyRecipeLine(recipesState.versionForm.ingredients.length + 1)); render(); }
function saveVersionFormFromDom() { const form=document.querySelector<HTMLFormElement>('[data-form="recipe-version"]'); if (!form) return; recipesState.versionForm = recipeVersionFormFromForm(form); }
function draftPercentTotalNumber() { return recipesState.versionForm.ingredients.reduce((sum, line) => line.amount_unit === 'percent' && line.amount_value.trim() && /^-?\d+([.,]\d+)?$/.test(line.amount_value.trim()) ? sum + Number(line.amount_value.trim().replace(',', '.')) : sum, 0); }
function draftPercentTotal() { const total = draftPercentTotalNumber(); return Number.isInteger(total) ? String(total) : String(Number(total.toFixed(4))); }
function draftPercentHint() { const total = draftPercentTotalNumber(); const isExact = Math.abs(total - 100) < 0.000001; return `<p class="next-step ${isExact ? 'success-text' : 'warning-text'}"><strong>Сумма процентов:</strong> ${escapeHtml(draftPercentTotal())}%. ${isExact ? 'Сумма процентов ровно 100%. После сохранения backend выполнит итоговый расчет версии.' : 'Проверьте сумму процентов. Итоговый расчет выполняется backend после сохранения версии.'}</p>`; }
function phaseOptions(current: string) { const selected = current || 'A'; return ['A','B','C','D'].map((phase) => `<option value="${phase}" ${selected===phase?'selected':''}>Фаза ${phase}</option>`).join(''); }
function validateRecipeVersionForm(form: RecipeVersionForm) { if (!recipesState.selectedTemplate) return 'Выберите базовый рецепт, для которого создается версия.'; for (const [index, line] of form.ingredients.entries()) { const row = index + 1; if (!line.ingredient_id) return `В строке ${row} выберите компонент из справочника.`; if (!line.amount_value) return `В строке ${row} укажите количество, например 5 или 2.5.`; if (!line.amount_unit) return `В строке ${row} выберите единицу: %, г, мл или шт.`; if (!/^\d+$/.test(line.position)) return `В строке ${row} позиция должна быть целым числом, например ${row}.`; } return ''; }
function recipeTemplatePayloadFromForm(form: HTMLFormElement): RecipeTemplatePayload { const data = new FormData(form); return { name: String(data.get('name') ?? '').trim(), product_type: String(data.get('product_type') ?? '').trim(), description: String(data.get('description') ?? '').trim(), notes: String(data.get('notes') ?? '').trim() }; }
function recipeVersionFormFromForm(form: HTMLFormElement): RecipeVersionForm { const data = new FormData(form); const ingredients = recipesState.versionForm.ingredients.map((_, index) => ({ ingredient_id: String(data.get(`ingredient_id_${index}`) ?? ''), position: String(data.get(`position_${index}`) ?? index + 1).trim(), phase: String(data.get(`phase_${index}`) ?? '').trim(), amount_value: String(data.get(`amount_value_${index}`) ?? '').trim(), amount_unit: String(data.get(`amount_unit_${index}`) ?? 'percent'), notes: String(data.get(`notes_${index}`) ?? '').trim() })); return { title: String(data.get('title') ?? '').trim(), status: String(data.get('status') ?? 'draft'), target_batch_size_value: String(data.get('target_batch_size_value') ?? '').trim(), target_batch_size_unit: String(data.get('target_batch_size_unit') ?? 'g'), notes: String(data.get('notes') ?? '').trim(), change_note: String(data.get('change_note') ?? '').trim(), ingredients }; }
function recipeVersionPayload(form: RecipeVersionForm) { return { title: form.title, status: form.status, target_batch_size_value: form.target_batch_size_value || null, target_batch_size_unit: form.target_batch_size_value ? form.target_batch_size_unit : null, notes: form.notes, change_note: form.change_note, created_from_version_id: recipesState.selectedVersionDetail?.version.id ?? null, ingredients: form.ingredients.map((line, index)=>({ ingredient_id: Number(line.ingredient_id), position: Number(line.position || index + 1), phase: line.phase, amount_value: line.amount_value, amount_unit: line.amount_unit, notes: line.notes })) }; }

function startEditIngredient(id: number) {
  const item = ingredientsState.items.find((ingredient) => ingredient.id === id);
  const current = ingredientsState.formMode === 'edit' && ingredientsState.form.id ? ingredientsState.items.find((ingredient) => ingredient.id === ingredientsState.form.id) ?? null : null;
  if (!item || !confirmDiscardDirtyAssignment(assignmentDraftIsDirty(current, ingredientsState.assignmentDraft))) return;
  ingredientsState.formMode = 'edit'; ingredientsState.showCreateForm = false; ingredientsState.form = { id: item.id, name: item.name, category: item.category, default_unit: item.default_unit, density_g_per_ml: item.density_g_per_ml, notes: item.notes, inci_name: item.inci_name, supplier_hint: item.supplier_hint, allergen_note: item.allergen_note, usage_note: item.usage_note }; ingredientsState.assignmentDraft = assignmentDraftFromItem(item); ingredientsMessage = ''; render();
}
function cancelIngredientEdit() {
  const current = ingredientsState.formMode === 'edit' && ingredientsState.form.id ? ingredientsState.items.find((ingredient) => ingredient.id === ingredientsState.form.id) ?? null : null;
  if (!confirmDiscardDirtyAssignment(assignmentDraftIsDirty(current, ingredientsState.assignmentDraft))) return;
  ingredientsState.formMode = 'create'; ingredientsState.form = emptyIngredientForm(); ingredientsState.assignmentDraft = emptyAssignmentDraft(); ingredientsState.showCreateForm = false; ingredientsMessage = ''; ingredientsError = ''; render();
}

function apiGet<T>(url: string): Promise<T> { return fetch(url).then((response) => { if (!response.ok) throw new Error('API request failed'); return response.json() as Promise<T>; }); }
function apiErrorMessage(payload: unknown) { if (typeof payload === 'string') return payload; if (payload && typeof payload === 'object' && 'detail' in payload) { const detail = (payload as { detail?: unknown }).detail; if (typeof detail === 'string') return detail; if (detail && typeof detail === 'object' && 'message' in detail) return String((detail as { message?: unknown }).message ?? 'API request failed'); } return 'API request failed'; }
function apiSend<T>(url: string, method: 'POST' | 'PUT', body?: unknown): Promise<T> { return fetch(url, { method, headers: body ? { 'Content-Type': 'application/json' } : undefined, body: body ? JSON.stringify(body) : undefined }).then(async (response) => { if (!response.ok) { let payload: unknown = null; try { payload = await response.json(); } catch { payload = null; } throw new Error(apiErrorMessage(payload)); } return response.json() as Promise<T>; }); }
function getClients(includeInactive = false) { return apiGet<{ clients: Client[] }>(`/api/clients${includeInactive ? '?include_inactive=true' : ''}`); }
function getClientRecipes(includeInactive = false) { return apiGet<{ client_recipes: ClientRecipe[] }>(`/api/client-recipes?include_inactive=${includeInactive ? 'true' : 'false'}`); }
function getClientRecipe(id: number) { return apiGet<ClientRecipeDetail>(`/api/client-recipes/${id}`); }
function createClientRecipe(payload: ClientRecipePayload) { return apiSend<ClientRecipeDetail>('/api/client-recipes', 'POST', payload); }
function deactivateClientRecipeRequest(id: number) { return apiSend<ClientRecipe>(`/api/client-recipes/${id}/deactivate`, 'POST'); }
function createClient(payload: ClientPayload) { return apiSend<Client>('/api/clients', 'POST', payload); }
function updateClient(id: number, payload: ClientPayload) { return apiSend<Client>(`/api/clients/${id}`, 'PUT', payload); }
function deactivateClientRequest(id: number) { return apiSend<Client>(`/api/clients/${id}/deactivate`, 'POST'); }
function getIngredients() { return apiGet<{ ingredients: Ingredient[] }>('/api/ingredients'); }
function getIngredientCatalogCategories() { return apiGet<{ categories: CatalogCategory[] }>('/api/catalog/categories?scope=ingredient'); }
function getIngredientCatalogTags() { return apiGet<{ tags: CatalogTag[] }>('/api/catalog/tags?scope=ingredient'); }
function createIngredientCatalogCategory(name: string) { return apiSend<CatalogCategory>('/api/catalog/categories', 'POST', { scope: 'ingredient', name, slug: null, parent_id: null, sort_order: 0 }); }
function createIngredientCatalogTag(name: string) { return apiSend<CatalogTag>('/api/catalog/tags', 'POST', { scope: 'ingredient', name, slug: null, color: '' }); }
function updateIngredientCatalogCategory(ingredientId: number, catalogCategoryId: number | null) { return apiSend<{ ok: boolean }>(`/api/ingredients/${ingredientId}/catalog-category`, 'PUT', { catalog_category_id: catalogCategoryId }); }
function updateIngredientCatalogTags(ingredientId: number, tagIds: number[]) { return apiSend<{ ok: boolean }>(`/api/ingredients/${ingredientId}/catalog-tags`, 'PUT', { tag_ids: tagIds }); }
function createIngredient(payload: IngredientPayload) { return apiSend<Ingredient>('/api/ingredients', 'POST', payload); }
function updateIngredient(id: number, payload: IngredientPayload) { return apiSend<Ingredient>(`/api/ingredients/${id}`, 'PUT', payload); }
function deactivateIngredientRequest(id: number) { return apiSend<Ingredient>(`/api/ingredients/${id}/deactivate`, 'POST'); }
function getIngredientLots() { return apiGet<{ lots: IngredientLot[] }>('/api/ingredient-lots'); }
function createIngredientLot(payload: IngredientLotPayload) { return apiSend<IngredientLot>('/api/ingredient-lots', 'POST', payload); }
function updateIngredientLot(id: number, payload: IngredientLotPayload) { return apiSend<IngredientLot>(`/api/ingredient-lots/${id}`, 'PUT', payload); }
function deactivateIngredientLotRequest(id: number) { return apiSend<IngredientLot>(`/api/ingredient-lots/${id}/deactivate`, 'POST'); }
function getPackagingItems() { return apiGet<{ packaging_items: PackagingItem[] }>('/api/packaging-items'); }
function createPackagingItem(payload: PackagingItemPayload) { return apiSend<PackagingItem>('/api/packaging-items', 'POST', payload); }
function updatePackagingItem(id: number, payload: PackagingItemPayload) { return apiSend<PackagingItem>(`/api/packaging-items/${id}`, 'PUT', payload); }
function deactivatePackagingItemRequest(id: number) { return apiSend<PackagingItem>(`/api/packaging-items/${id}/deactivate`, 'POST'); }
function getPackagingCatalogCategories() { return apiGet<{ categories: CatalogCategory[] }>('/api/catalog/categories?scope=packaging'); }
function getPackagingCatalogTags() { return apiGet<{ tags: CatalogTag[] }>('/api/catalog/tags?scope=packaging'); }
function createPackagingCatalogCategory(name: string) { return apiSend<CatalogCategory>('/api/catalog/categories', 'POST', { scope: 'packaging', name, slug: null, parent_id: null, sort_order: 0 }); }
function createPackagingCatalogTag(name: string) { return apiSend<CatalogTag>('/api/catalog/tags', 'POST', { scope: 'packaging', name, slug: null, color: '' }); }
function updatePackagingCatalogCategory(packagingItemId: number, catalogCategoryId: number | null) { return apiSend<{ entity_type: string; entity_id: number; catalog_category_id: number | null }>(`/api/packaging-items/${packagingItemId}/catalog-category`, 'PUT', { catalog_category_id: catalogCategoryId }); }
function updatePackagingCatalogTags(packagingItemId: number, tagIds: number[]) { return apiSend<{ entity_type: string; entity_id: number; tag_ids: number[] }>(`/api/packaging-items/${packagingItemId}/catalog-tags`, 'PUT', { tag_ids: tagIds }); }

function getRecipeTemplates() { return apiGet<{ recipe_templates: RecipeTemplate[] }>('/api/recipe-templates'); }
function getRecipeCatalogCategories() { return apiGet<{ categories: CatalogCategory[] }>('/api/catalog/categories?scope=recipe'); }
function getRecipeCatalogTags() { return apiGet<{ tags: CatalogTag[] }>('/api/catalog/tags?scope=recipe'); }
function createRecipeCatalogCategory(name: string) { return apiSend<CatalogCategory>('/api/catalog/categories', 'POST', { scope: 'recipe', name, slug: null, parent_id: null, sort_order: 0 }); }
function createRecipeCatalogTag(name: string) { return apiSend<CatalogTag>('/api/catalog/tags', 'POST', { scope: 'recipe', name, slug: null, color: '' }); }
function updateRecipeCatalogCategory(recipeTemplateId: number, catalogCategoryId: number | null) { return apiSend<{ entity_type: string; entity_id: number; catalog_category_id: number | null }>(`/api/recipe-templates/${recipeTemplateId}/catalog-category`, 'PUT', { catalog_category_id: catalogCategoryId }); }
function updateRecipeCatalogTags(recipeTemplateId: number, tagIds: number[]) { return apiSend<{ entity_type: string; entity_id: number; tag_ids: number[] }>(`/api/recipe-templates/${recipeTemplateId}/catalog-tags`, 'PUT', { tag_ids: tagIds }); }
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

function setRecipeIngredientOptions(ingredients: Ingredient[]) { recipesState.ingredients = ingredients.filter((i)=>i.is_active); }
function refreshRecipeIngredientOptions(showMessage = false) {
  saveVersionFormFromDom();
  return getIngredients().then((ingredients) => {
    setRecipeIngredientOptions(ingredients.ingredients);
    recipesStatus = 'ready';
    recipesError = '';
    if (showMessage) recipesMessage = 'Список активных компонентов обновлен. Если компонента нет в списке, проверьте, что он не архивирован.';
    render();
  }).catch(() => {
    recipesError = 'Не удалось обновить компоненты для конструктора рецепта. Проверьте локальное приложение и попробуйте обновить рецепты.';
    render();
  });
}
function loadRecipes(force = false) {
  if (!force && recipesStatus === 'loading') return;
  if (!force && recipesStatus === 'ready') { refreshRecipeIngredientOptions(); return; }
  saveVersionFormFromDom();
  recipesStatus = 'loading'; recipesError = ''; render();
  Promise.all([getRecipeTemplates(), getIngredients(), getRecipeCatalogCategories(), getRecipeCatalogTags()])
    .then(([templates, ingredients, categories, tags]) => { recipesState.templates = templates.recipe_templates; setRecipeIngredientOptions(ingredients.ingredients); recipesState.catalogCategories = categories.categories; recipesState.catalogTags = tags.tags; recipesStatus = 'ready'; render(); })
    .catch(() => { recipesStatus = 'error'; recipesError = 'Не получилось получить рецепты из локального API. Проверьте локальное приложение и попробуйте обновить раздел.'; render(); });
}
function openRecipeTemplate(id: number) {
  recipesError = ''; recipesMessage = '';
  Promise.all([getRecipeTemplate(id), getRecipeVersions(id)]).then(([template, versions]) => { recipesState.selectedTemplate = template; recipesState.versions = versions.recipe_versions; recipesState.selectedVersionDetail = null; recipesState.versionDetailStatus = 'idle'; recipesState.calculation = null; calculationStatus = 'idle'; render(); }).catch(() => { recipesError = 'Не удалось открыть рецепт. Попробуйте обновить страницу.'; render(); });
}
function openRecipeVersion(id: number) { recipesError = ''; calculationError = ''; recipesState.versionDetailStatus = 'loading'; recipesState.calculation = null; calculationStatus = 'loading'; render(); getRecipeVersionDetail(id).then((detail)=>{ recipesState.selectedVersionDetail = detail; recipesState.versionDetailStatus = 'ready'; recipesState.calculationTargetValue = detail.version.target_batch_size_value ?? ''; recipesState.calculationTargetUnit = detail.version.target_batch_size_unit === 'ml' ? 'ml' : 'g'; render(); return getRecipeCalculation(detail.version.id, recipesState.calculationTargetValue, recipesState.calculationTargetUnit); }).then((result)=>{ recipesState.calculation = result; calculationStatus = 'ready'; render(); }).catch(()=>{ if (recipesState.versionDetailStatus === 'ready') { calculationStatus = 'error'; calculationError = 'Не удалось выполнить расчет. Состав версии открыт, попробуйте пересчитать позже.'; } else { recipesState.versionDetailStatus = 'error'; calculationStatus = 'idle'; recipesError = 'Не удалось загрузить версию рецепта.'; } render(); }); }
function submitRecipeTemplateForm(event: SubmitEvent) { event.preventDefault(); const payload = recipeTemplatePayloadFromForm(event.currentTarget as HTMLFormElement); createRecipeTemplate(payload).then((template)=>{ recipesMessage = 'Рецепт создан.'; recipesError = ''; recipesState.templateForm = emptyRecipeTemplateForm(); return getRecipeTemplates().then((response)=>({template, response})); }).then(({template, response})=>{ recipesState.templates = response.recipe_templates; recipesStatus = 'ready'; openRecipeTemplate(template.id); }).catch(()=>{ recipesMessage = ''; recipesError = 'Не удалось создать рецепт. Проверьте название и попробуйте еще раз.'; recipesStatus = 'ready'; render(); }); }
function reloadRecipeCatalogData() { return Promise.all([getRecipeTemplates(), getRecipeCatalogCategories(), getRecipeCatalogTags()]).then(([templates, categories, tags]) => { recipesState.templates = templates.recipe_templates; recipesState.catalogCategories = categories.categories; recipesState.catalogTags = tags.tags; if (recipesState.selectedTemplate) recipesState.selectedTemplate = templates.recipe_templates.find((template) => template.id === recipesState.selectedTemplate?.id) ?? recipesState.selectedTemplate; recipesStatus = 'ready'; }); }
function submitRecipeCatalogCategoryForm(event: SubmitEvent) { event.preventDefault(); const name = String(new FormData(event.currentTarget as HTMLFormElement).get('name') ?? '').trim(); if (!name) { recipesError = 'Укажите название группы, например «Кремы».'; recipesMessage = ''; render(); return; } recipesState.catalogCreating = 'category'; recipesError = ''; render(); createRecipeCatalogCategory(name).then(() => reloadRecipeCatalogData()).then(() => { recipesMessage = 'Группа рецептов создана.'; recipesState.catalogCreating = null; render(); }).catch(() => { recipesState.catalogCreating = null; recipesMessage = ''; recipesError = 'Не удалось создать группу рецептов. Проверьте название и попробуйте еще раз.'; render(); }); }
function submitRecipeCatalogTagForm(event: SubmitEvent) { event.preventDefault(); const name = String(new FormData(event.currentTarget as HTMLFormElement).get('name') ?? '').trim(); if (!name) { recipesError = 'Укажите название метки, например «Для сухой кожи».'; recipesMessage = ''; render(); return; } recipesState.catalogCreating = 'tag'; recipesError = ''; render(); createRecipeCatalogTag(name).then(() => reloadRecipeCatalogData()).then(() => { recipesMessage = 'Метка рецепта создана.'; recipesState.catalogCreating = null; render(); }).catch(() => { recipesState.catalogCreating = null; recipesMessage = ''; recipesError = 'Не удалось создать метку рецепта. Проверьте название и попробуйте еще раз.'; render(); }); }
function assignRecipeCategory(recipeTemplateId: number, value: string) { if (!recipeTemplateId) return; recipesState.catalogSaving = 'saving'; recipesError = ''; render(); updateRecipeCatalogCategory(recipeTemplateId, value ? Number(value) : null).then(() => reloadRecipeCatalogData()).then(() => { recipesMessage = 'Моя группа рецепта сохранена.'; recipesState.catalogSaving = 'idle'; render(); }).catch(() => { recipesState.catalogSaving = 'idle'; recipesMessage = ''; recipesError = 'Не удалось сохранить группу рецепта. Проверьте, что группа активна, и попробуйте еще раз.'; render(); }); }
function assignRecipeTags(recipeTemplateId: number) { if (!recipeTemplateId) return; const tagIds = Array.from(document.querySelectorAll<HTMLInputElement>(`[data-action="toggle-recipe-tag"][data-recipe-template-id="${recipeTemplateId}"]:checked`)).map((input) => Number(input.value)); recipesState.catalogSaving = 'saving'; recipesError = ''; render(); updateRecipeCatalogTags(recipeTemplateId, tagIds).then(() => reloadRecipeCatalogData()).then(() => { recipesMessage = 'Метки рецепта сохранены.'; recipesState.catalogSaving = 'idle'; render(); }).catch(() => { recipesState.catalogSaving = 'idle'; recipesMessage = ''; recipesError = 'Не удалось сохранить метки рецепта. Проверьте, что метки активны, и попробуйте еще раз.'; render(); }); }
function submitRecipeVersionForm(event: SubmitEvent) { event.preventDefault(); if (!recipesState.selectedTemplate) return; const form = recipeVersionFormFromForm(event.currentTarget as HTMLFormElement); recipesState.versionForm = form; const validationError = validateRecipeVersionForm(form); if (validationError) { recipesMessage = ''; recipesError = validationError; render(); return; } createRecipeVersion(recipesState.selectedTemplate.id, recipeVersionPayload(form)).then((detail)=>{ recipesMessage = 'Новая версия рецепта сохранена. Теперь ее можно использовать для индивидуального рецепта клиента.'; recipesError = ''; recipesState.versionForm = emptyRecipeVersionForm(); recipesState.selectedVersionDetail = detail; recipesState.versionDetailStatus = 'ready'; return getRecipeVersions(recipesState.selectedTemplate!.id); }).then((response)=>{ recipesState.versions = response.recipe_versions; recipesState.calculation = null; calculationStatus = 'idle'; render(); if (recipesState.selectedVersionDetail) openRecipeVersion(recipesState.selectedVersionDetail.version.id); }).catch(()=>{ recipesMessage = ''; recipesError = 'Не удалось сохранить версию. Проверьте строки состава и попробуйте еще раз.'; render(); }); }
function submitCalculationForm(event: SubmitEvent) { event.preventDefault(); const detail = recipesState.selectedVersionDetail; if (!detail) return; const data = new FormData(event.currentTarget as HTMLFormElement); const value = String(data.get('target_batch_size_value') ?? '').trim(); const unit = String(data.get('target_batch_size_unit') ?? 'g'); recipesState.calculationTargetValue = value; recipesState.calculationTargetUnit = unit; calculationStatus = 'loading'; calculationError = ''; render(); getRecipeCalculation(detail.version.id, value, unit).then((result)=>{ recipesState.calculation = result; calculationStatus = 'ready'; render(); }).catch(()=>{ calculationStatus = 'error'; calculationError = 'Не удалось выполнить расчет. Проверьте размер партии и попробуйте еще раз.'; render(); }); }


function loadPackagingItems(force = false) {
  if (!force && (packagingItemsStatus === 'loading' || packagingItemsStatus === 'ready')) return;
  packagingItemsStatus = 'loading'; packagingItemsError = ''; render();
  Promise.all([getPackagingItems(), getPackagingCatalogCategories(), getPackagingCatalogTags()]).then(([response, categories, tags]) => { packagingItemsState.items = response.packaging_items; packagingItemsState.catalogCategories = categories.categories; packagingItemsState.catalogTags = tags.tags; packagingItemsStatus = 'ready'; render(); }).catch(() => { packagingItemsStatus = 'error'; packagingItemsError = 'Не получилось получить справочник тары из локального API.'; render(); });
}
function startEditPackagingItem(id: number) {
  const item = packagingItemsState.items.find((packagingItem) => packagingItem.id === id);
  const current = packagingItemsState.formMode === 'edit' && packagingItemsState.form.id ? packagingItemsState.items.find((packagingItem) => packagingItem.id === packagingItemsState.form.id) ?? null : null;
  if (!item || !confirmDiscardDirtyAssignment(assignmentDraftIsDirty(current, packagingItemsState.assignmentDraft))) return;
  packagingItemsState.formMode = 'edit'; packagingItemsState.form = { id: item.id, name: item.name, kind: item.kind, unit: item.unit, capacity_value: item.capacity_value, capacity_unit: item.capacity_unit, material: item.material, supplier_hint: item.supplier_hint, unit_cost: item.unit_cost, notes: item.notes }; packagingItemsState.assignmentDraft = assignmentDraftFromItem(item); packagingItemsMessage = ''; packagingItemsError = ''; render();
}
function resetPackagingItemForm() {
  const current = packagingItemsState.formMode === 'edit' && packagingItemsState.form.id ? packagingItemsState.items.find((packagingItem) => packagingItem.id === packagingItemsState.form.id) ?? null : null;
  if (!confirmDiscardDirtyAssignment(assignmentDraftIsDirty(current, packagingItemsState.assignmentDraft))) return;
  packagingItemsState.formMode = 'create'; packagingItemsState.form = emptyPackagingItemForm(); packagingItemsState.assignmentDraft = emptyAssignmentDraft(); packagingItemsMessage = ''; packagingItemsError = ''; render();
}
function submitPackagingItemForm(event: SubmitEvent) {
  event.preventDefault();
  const payload = packagingItemPayloadFromForm(event.currentTarget as HTMLFormElement);
  const request = packagingItemsState.formMode === 'edit' && packagingItemsState.form.id ? updatePackagingItem(packagingItemsState.form.id, payload) : createPackagingItem(payload);
  request.then(() => { packagingItemsMessage = packagingItemsState.formMode === 'edit' ? 'Тара сохранена. Остатки не изменялись.' : 'Тара создана. Остатки добавляются отдельными складскими операциями.'; packagingItemsError = ''; packagingItemsState.formMode = 'create'; packagingItemsState.form = emptyPackagingItemForm(); return getPackagingItems(); }).then((response) => { packagingItemsState.items = response.packaging_items; packagingItemsStatus = 'ready'; render(); }).catch(() => { packagingItemsMessage = ''; packagingItemsError = 'Не удалось сохранить тару. Проверьте название, тип, единицы и числовые поля.'; packagingItemsStatus = 'ready'; render(); });
}
function deactivatePackagingItem(id: number) {
  const item = packagingItemsState.items.find((packagingItem) => packagingItem.id === id);
  if (!item || !window.confirm(`Деактивировать тару «${item.name}»? Она не будет удалена из истории.`)) return;
  deactivatePackagingItemRequest(id).then(() => { packagingItemsMessage = 'Тара деактивирована. История и остатки склада не изменялись.'; packagingItemsError = ''; return getPackagingItems(); }).then((response) => { packagingItemsState.items = response.packaging_items; packagingItemsStatus = 'ready'; render(); }).catch(() => { packagingItemsMessage = ''; packagingItemsError = 'Не удалось деактивировать тару. Попробуйте еще раз.'; packagingItemsStatus = 'ready'; render(); });
}

function reloadPackagingCatalogData() { return Promise.all([getPackagingItems(), getPackagingCatalogCategories(), getPackagingCatalogTags()]).then(([items, categories, tags]) => { packagingItemsState.items = items.packaging_items; packagingItemsState.catalogCategories = categories.categories; packagingItemsState.catalogTags = tags.tags; packagingItemsStatus = 'ready'; }); }
function submitPackagingCatalogCategoryForm(event: SubmitEvent) { event.preventDefault(); const name = String(new FormData(event.currentTarget as HTMLFormElement).get('name') ?? '').trim(); if (!name) return; packagingItemsState.catalogCreating = 'category'; packagingItemsError = ''; render(); createPackagingCatalogCategory(name).then(() => reloadPackagingCatalogData()).then(() => { packagingItemsMessage = 'Группа тары создана.'; packagingItemsState.catalogCreating = null; render(); }).catch(() => { packagingItemsState.catalogCreating = null; packagingItemsError = 'Не удалось создать группу тары. Проверьте название и попробуйте еще раз.'; render(); }); }
function submitPackagingCatalogTagForm(event: SubmitEvent) { event.preventDefault(); const name = String(new FormData(event.currentTarget as HTMLFormElement).get('name') ?? '').trim(); if (!name) return; packagingItemsState.catalogCreating = 'tag'; packagingItemsError = ''; render(); createPackagingCatalogTag(name).then(() => reloadPackagingCatalogData()).then(() => { packagingItemsMessage = 'Метка тары создана.'; packagingItemsState.catalogCreating = null; render(); }).catch(() => { packagingItemsState.catalogCreating = null; packagingItemsError = 'Не удалось создать метку тары. Проверьте название и попробуйте еще раз.'; render(); }); }
function updatePackagingDraftCategory(packagingItemId: number, value: string) { if (packagingItemsState.assignmentDraft.itemId !== packagingItemId) return; updateDraftCategory(packagingItemsState.assignmentDraft, value); packagingItemsMessage = ''; render(); }
function updatePackagingDraftTag(packagingItemId: number, tagId: number, checked: boolean) { if (packagingItemsState.assignmentDraft.itemId !== packagingItemId || !tagId) return; updateDraftTag(packagingItemsState.assignmentDraft, tagId, checked); packagingItemsMessage = ''; render(); }
function resetPackagingAssignmentDraft() { const item = packagingItemsState.form.id ? packagingItemsState.items.find((packagingItem) => packagingItem.id === packagingItemsState.form.id) ?? null : null; packagingItemsState.assignmentDraft = resetAssignmentDraft(item); packagingItemsMessage = ''; render(); }
function applyPackagingAssignmentDraft() {
  const item = packagingItemsState.form.id ? packagingItemsState.items.find((packagingItem) => packagingItem.id === packagingItemsState.form.id) ?? null : null;
  const draft = packagingItemsState.assignmentDraft;
  if (!item || !draft.itemId || !assignmentDraftIsDirty(item, draft)) return;
  packagingItemsState.catalogSaving = 'saving'; packagingItemsError = ''; render();
  const request = (draft.catalogCategoryId !== item.catalog_category_id ? updatePackagingCatalogCategory(item.id, draft.catalogCategoryId) : Promise.resolve() as Promise<unknown>)
    .then(() => (!sameNumberSet(draft.catalogTagIds, item.catalog_tag_ids) ? updatePackagingCatalogTags(item.id, draft.catalogTagIds) : Promise.resolve() as Promise<unknown>))
    .then(() => reloadPackagingCatalogData());
  request.then(() => { const saved = packagingItemsState.items.find((packagingItem) => packagingItem.id === item.id) ?? null; packagingItemsState.assignmentDraft = resetAssignmentDraft(saved); packagingItemsMessage = 'Группа и метки тары сохранены.'; packagingItemsState.catalogSaving = 'idle'; render(); }).catch(() => { packagingItemsState.catalogSaving = 'idle'; packagingItemsMessage = ''; packagingItemsError = 'Не удалось сохранить группу или метки тары. Проверьте данные и попробуйте еще раз.'; render(); });
}

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
  request.then(() => { ingredientLotsMessage = ingredientLotsState.formMode === 'edit' ? 'Партия сохранена. Остаток не изменялся.' : 'Партия создана. Количество добавляется отдельным движением сырья.'; ingredientLotsError = ''; ingredientLotsState.formMode = 'create'; ingredientLotsState.form = emptyIngredientLotForm(); return getIngredientLots(); }).then((response) => { ingredientLotsState.lots = response.lots; ingredientLotsStatus = 'ready'; render(); }).catch(() => { ingredientLotsMessage = ''; ingredientLotsError = 'Не удалось сохранить партию. Проверьте обязательные поля и попробуйте еще раз.'; ingredientLotsStatus = 'ready'; render(); });
}
function deactivateIngredientLot(id: number) {
  const lot = ingredientLotsState.lots.find((item) => item.id === id);
  if (!lot || !window.confirm(`Деактивировать партию «${lot.lot_code || lotIngredientName(lot.ingredient_id)}»? Она не будет удалена из истории.`)) return;
  deactivateIngredientLotRequest(id).then(() => { ingredientLotsMessage = 'Партия деактивирована. История склада не изменялась.'; ingredientLotsError = ''; return getIngredientLots(); }).then((response) => { ingredientLotsState.lots = response.lots; ingredientLotsStatus = 'ready'; render(); }).catch(() => { ingredientLotsMessage = ''; ingredientLotsError = 'Не удалось деактивировать партию. Попробуйте еще раз.'; ingredientLotsStatus = 'ready'; render(); });
}

function loadIngredients(force = false) {
  if (!force && (ingredientsStatus === 'loading' || ingredientsStatus === 'ready')) return;
  ingredientsStatus = 'loading'; ingredientsError = ''; render();
  Promise.all([getIngredients(), getIngredientCatalogCategories(), getIngredientCatalogTags()]).then(([response, categories, tags]) => { ingredientsState.items = response.ingredients; ingredientsState.catalogCategories = categories.categories; ingredientsState.catalogTags = tags.tags; ingredientsStatus = 'ready'; render(); }).catch(() => { ingredientsStatus = 'error'; ingredientsError = 'Не получилось получить справочник компонентов или каталог групп и меток из локального API.'; render(); });
}
function submitIngredientForm(event: SubmitEvent) {
  event.preventDefault();
  const form = event.currentTarget as HTMLFormElement;
  const payload = ingredientPayloadFromForm(form);
  const request = ingredientsState.formMode === 'edit' && ingredientsState.form.id ? updateIngredient(ingredientsState.form.id, payload) : createIngredient(payload);
  request.then(() => { ingredientsMessage = ingredientsState.formMode === 'edit' ? 'Компонент сохранен.' : 'Компонент создан.'; ingredientsError = ''; ingredientsState.formMode = 'create'; ingredientsState.form = emptyIngredientForm(); return getIngredients(); }).then((response) => { ingredientsState.items = response.ingredients; if (recipesStatus === 'ready') setRecipeIngredientOptions(response.ingredients); ingredientsStatus = 'ready'; render(); }).catch(() => { ingredientsMessage = ''; ingredientsError = 'Не удалось сохранить компонент. Проверьте обязательные поля и попробуйте еще раз.'; ingredientsStatus = 'ready'; render(); });
}
function submitIngredientCatalogCategoryForm(event: SubmitEvent) {
  event.preventDefault();
  const form = event.currentTarget as HTMLFormElement;
  const name = String(new FormData(form).get('name') ?? '').trim();
  if (!name) { ingredientsError = 'Укажите название группы, например «Масла».'; ingredientsMessage = ''; render(); return; }
  ingredientsState.catalogCreating = 'category'; ingredientsError = ''; render();
  createIngredientCatalogCategory(name).then(() => Promise.all([getIngredientCatalogCategories(), getIngredients()])).then(([categories, response]) => { ingredientsState.catalogCategories = categories.categories; ingredientsState.items = response.ingredients; ingredientsState.catalogCreating = null; ingredientsMessage = 'Группа создана и доступна для компонентов.'; ingredientsStatus = 'ready'; render(); }).catch(() => { ingredientsState.catalogCreating = null; ingredientsMessage = ''; ingredientsError = 'Не удалось создать группу. Проверьте название и попробуйте еще раз.'; render(); });
}
function submitIngredientCatalogTagForm(event: SubmitEvent) {
  event.preventDefault();
  const form = event.currentTarget as HTMLFormElement;
  const name = String(new FormData(form).get('name') ?? '').trim();
  if (!name) { ingredientsError = 'Укажите название метки, например «Для лица».'; ingredientsMessage = ''; render(); return; }
  ingredientsState.catalogCreating = 'tag'; ingredientsError = ''; render();
  createIngredientCatalogTag(name).then(() => Promise.all([getIngredientCatalogTags(), getIngredients()])).then(([tags, response]) => { ingredientsState.catalogTags = tags.tags; ingredientsState.items = response.ingredients; ingredientsState.catalogCreating = null; ingredientsMessage = 'Метка создана и доступна для компонентов.'; ingredientsStatus = 'ready'; render(); }).catch(() => { ingredientsState.catalogCreating = null; ingredientsMessage = ''; ingredientsError = 'Не удалось создать метку. Проверьте название и попробуйте еще раз.'; render(); });
}
function updateIngredientDraftCategory(ingredientId: number, value: string) { if (ingredientsState.assignmentDraft.itemId !== ingredientId) return; updateDraftCategory(ingredientsState.assignmentDraft, value); ingredientsMessage = ''; render(); }
function updateIngredientDraftTag(ingredientId: number, tagId: number, checked: boolean) { if (ingredientsState.assignmentDraft.itemId !== ingredientId || !tagId) return; updateDraftTag(ingredientsState.assignmentDraft, tagId, checked); ingredientsMessage = ''; render(); }
function resetIngredientAssignmentDraft() { const item = ingredientsState.form.id ? ingredientsState.items.find((ingredient) => ingredient.id === ingredientsState.form.id) ?? null : null; ingredientsState.assignmentDraft = resetAssignmentDraft(item); ingredientsMessage = ''; render(); }
function applyIngredientAssignmentDraft() {
  const item = ingredientsState.form.id ? ingredientsState.items.find((ingredient) => ingredient.id === ingredientsState.form.id) ?? null : null;
  const draft = ingredientsState.assignmentDraft;
  if (!item || !draft.itemId || !assignmentDraftIsDirty(item, draft)) return;
  ingredientsState.catalogSaving = 'saving'; ingredientsError = ''; render();
  const request = (draft.catalogCategoryId !== item.catalog_category_id ? updateIngredientCatalogCategory(item.id, draft.catalogCategoryId) : Promise.resolve() as Promise<unknown>)
    .then(() => (!sameNumberSet(draft.catalogTagIds, item.catalog_tag_ids) ? updateIngredientCatalogTags(item.id, draft.catalogTagIds) : Promise.resolve() as Promise<unknown>))
    .then(() => getIngredients());
  request.then((response) => { ingredientsState.items = response.ingredients; const saved = response.ingredients.find((ingredient) => ingredient.id === item.id) ?? null; ingredientsState.assignmentDraft = resetAssignmentDraft(saved); ingredientsMessage = 'Группа и метки компонента сохранены.'; ingredientsState.catalogSaving = 'idle'; ingredientsStatus = 'ready'; render(); }).catch(() => { ingredientsState.catalogSaving = 'idle'; ingredientsMessage = ''; ingredientsError = 'Не удалось сохранить группу или метки. Проверьте данные и попробуйте еще раз.'; render(); });
}

function deactivateIngredient(id: number) {
  const item = ingredientsState.items.find((ingredient) => ingredient.id === id);
  if (!item || !window.confirm(`Деактивировать компонент «${item.name}»? Он не будет удален из истории.`)) return;
  deactivateIngredientRequest(id).then(() => { ingredientsMessage = 'Компонент деактивирован.'; ingredientsError = ''; return getIngredients(); }).then((response) => { ingredientsState.items = response.ingredients; if (recipesStatus === 'ready') setRecipeIngredientOptions(response.ingredients); ingredientsStatus = 'ready'; render(); }).catch(() => { ingredientsMessage = ''; ingredientsError = 'Не удалось деактивировать компонент. Попробуйте еще раз.'; ingredientsStatus = 'ready'; render(); });
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

window.addEventListener('popstate', () => { activeSection = sectionFromLocation(); loadSectionData(activeSection); render(); });
render();
fetch('/api/health').then((response) => { healthStatus = response.ok ? 'online' : 'offline'; render(); }).catch(() => { healthStatus = 'offline'; render(); });
loadOnboarding();
loadSectionData(activeSection);
