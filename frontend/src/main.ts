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
type ClientStatusFilter = 'active' | 'archived' | 'all';
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
type ClientsState = { items: Client[]; formMode: ClientFormMode; form: ClientFormState; includeInactive: boolean; showCreateForm: boolean; filters: { search: string; status: ClientStatusFilter } };


type OrderStatus = 'new' | 'waiting_for_materials' | 'ready_to_produce' | 'in_progress' | 'produced' | 'delivered' | 'cancelled' | 'archived';
type Order = { id: number; client_id: number; recipe_version_id: number | null; client_recipe_id: number | null; product_name: string; target_batch_size_value: string; target_batch_size_unit: string; packaging_item_id: number | null; packaging_quantity: string | null; status: OrderStatus; sale_price: string | null; ordered_at: string | null; planned_production_at: string | null; produced_at: string | null; delivered_at: string | null; notes: string; is_active: boolean; created_at: string; updated_at: string };
type OrderFormMode = 'create' | 'edit';
type OrderSourceType = 'recipe_version' | 'client_recipe';
type OrderStatusFilter = 'active' | 'archived' | 'cancelled' | 'all';
type OrderFormState = { id: number | null; client_id: string; source_type: OrderSourceType; recipe_version_id: string; client_recipe_id: string; product_name: string; target_batch_size_value: string; target_batch_size_unit: string; packaging_item_id: string; packaging_quantity: string; sale_price: string; ordered_at: string; planned_production_at: string; notes: string };
type OrderPayload = { client_id: number | null; recipe_version_id: number | null; client_recipe_id: number | null; product_name: string; target_batch_size_value: string; target_batch_size_unit: string; packaging_item_id: number | null; packaging_quantity: string | null; sale_price: string | null; ordered_at: string | null; planned_production_at: string | null; notes: string };
type OrdersStatus = 'idle' | 'loading' | 'ready' | 'error';
type ProductionReadinessStatus = 'ready' | 'blocked' | 'warning';
type ProductionReadinessIssueSeverity = 'blocking' | 'warning' | 'info';
type ProductionReadinessIssue = { code: string; severity: ProductionReadinessIssueSeverity; message: string; field: string | null; entity_type: string | null; entity_id: number | null };
type ProductionReadinessLotSelection = { lot_id: number; lot_code: string | null; selected_quantity: string; unit: string; expires_at: string | null; is_expired: boolean; expires_soon: boolean };
type ProductionReadinessIngredientLine = { ingredient_id: number; ingredient_name: string; required_quantity: string; required_unit: string; available_quantity: string; missing_quantity: string | null; can_fulfill: boolean; selected_lots: ProductionReadinessLotSelection[]; warnings: ProductionReadinessIssue[] };
type ProductionReadinessPackagingLine = { packaging_item_id: number; name: string; required_quantity: string; available_quantity: string; missing_quantity: string | null; can_fulfill: boolean };
type ProductionReadinessResponse = { order_id: number; can_produce: boolean; status: ProductionReadinessStatus; blocking_issues: ProductionReadinessIssue[]; warnings: ProductionReadinessIssue[]; ingredients: ProductionReadinessIngredientLine[]; packaging: ProductionReadinessPackagingLine[]; estimated_cost: string | null; estimated_tax: string | null; estimated_margin: string | null; generated_at: string | null };
type ProductionBatchIngredientResponse = { id: number; production_batch_id: number; ingredient_id: number; ingredient_lot_id: number; ingredient_name_snapshot: string; lot_code_snapshot: string; required_quantity: string; consumed_quantity: string; unit: string; unit_cost_snapshot: string | null; total_cost_snapshot: string | null; expiration_date_snapshot: string | null; created_at: string };
type ProductionBatchPackagingResponse = { id: number; production_batch_id: number; packaging_item_id: number; packaging_name_snapshot: string; quantity: string; unit: string; unit_cost_snapshot: string | null; total_cost_snapshot: string | null; created_at: string };
type ProductionBatchDetailResponse = { id: number; order_id: number; product_name: string | null; client_id: number | null; client_name: string | null; recipe_version_id: number | null; client_recipe_id: number | null; final_batch_value: string; final_batch_unit: string; component_cost: string | null; packaging_cost: string | null; other_cost: string; total_cost: string | null; sale_price: string | null; tax: string | null; margin: string | null; margin_percent: string | null; produced_at: string; notes: string; created_at: string; ingredients: ProductionBatchIngredientResponse[]; packaging: ProductionBatchPackagingResponse[] };
type ProductionStatus = 'idle' | 'loading' | 'ready' | 'error';
type ProductionBatchListItem = { id: number; order_id: number; product_name: string; client_id: number; client_name: string | null; recipe_version_id: number | null; client_recipe_id: number | null; final_batch_value: string; final_batch_unit: string; total_cost: string | null; sale_price: string | null; tax: string | null; margin: string | null; margin_percent: string | null; produced_at: string; ingredient_line_count: number; packaging_line_count: number; notes: string };
type ProductionHistoryState = { batches: ProductionBatchListItem[]; selectedBatch: ProductionBatchDetailResponse | null; status: ProductionStatus; detailStatus: ProductionStatus; error: string; detailError: string; filters: { search: string } };


type AlertStatus = 'open' | 'resolved' | 'dismissed';
type AlertStatusFilter = 'open' | 'resolved' | 'dismissed' | 'all';
type AlertSeverity = 'info' | 'warning' | 'critical' | 'blocking';
type AlertType = 'low_ingredient_stock' | 'low_packaging_stock' | 'ingredient_expiration_soon' | 'ingredient_expired' | 'insufficient_materials_for_order' | 'insufficient_packaging_for_order';
type AlertResponse = { id: number; alert_key: string; type: AlertType; severity: AlertSeverity; message: string; related_entity_type: string; related_entity_id: number; recommended_action: string; status: AlertStatus; created_at: string; updated_at: string; resolved_at: string | null; dismissed_at: string | null };
type AlertListResponse = { alerts: AlertResponse[]; limit: number; offset: number };
type AlertGenerationResponse = { created_count: number; updated_count: number; resolved_count: number; open_count: number };
type AlertsState = { items: AlertResponse[]; status: 'idle' | 'loading' | 'ready' | 'error'; actionStatus: 'idle' | 'loading'; error: string; message: string; filters: { status: AlertStatusFilter; type: AlertType | ''; search: string }; lastGeneration: AlertGenerationResponse | null };

type OrdersState = { items: Order[]; clients: Client[]; templates: RecipeTemplate[]; versions: RecipeVersion[]; clientRecipes: ClientRecipe[]; packagingItems: PackagingItem[]; formMode: OrderFormMode; form: OrderFormState; showForm: boolean; selectedOrder: Order | null; includeInactive: boolean; filters: { search: string; status: OrderStatusFilter }; readinessByOrderId: Record<number, ProductionReadinessResponse>; readinessLoadingOrderId: number | null; readinessError: string; productionByOrderId: Record<number, ProductionBatchDetailResponse>; productionLoadingOrderId: number | null; productionError: string; productionConfirmingOrderId: number | null; productionNotesByOrderId: Record<number, string> };

type ClientRecipe = { id: number; client_id: number; source_recipe_version_id: number; title: string; status: string; target_batch_size_value: string | null; target_batch_size_unit: string | null; personalization_notes: string; allergy_notes: string; preference_notes: string; contraindication_notes: string; notes: string; is_active: boolean; created_at: string; updated_at: string };
type ClientRecipeIngredient = { id: number; client_recipe_id: number; ingredient_id: number; source_recipe_ingredient_id: number | null; position: number; phase: string; amount_value: string; amount_unit: string; personalization_note: string; notes: string; created_at: string };
type ClientRecipeDetail = { client_recipe: ClientRecipe; ingredients: ClientRecipeIngredient[] };
type ClientRecipeFormState = { client_id: string; recipe_template_id: string; source_recipe_version_id: string; title: string; target_batch_size_value: string; target_batch_size_unit: string; personalization_notes: string; allergy_notes: string; preference_notes: string; contraindication_notes: string; notes: string };
type ClientRecipePayload = { client_id: number; source_recipe_version_id: number; title: string; target_batch_size_value: string | null; target_batch_size_unit: string | null; personalization_notes: string; allergy_notes: string; preference_notes: string; contraindication_notes: string; notes: string };
type ClientRecipeIngredientUpdatePayload = { id?: number; ingredient_id: number; position: number; phase: string; amount_value: string; amount_unit: string; personalization_note: string; notes: string };
type ClientRecipeCompositionDraftLine = { id: number | null; ingredient_id: string; position: number; phase: string; amount_value: string; amount_unit: string; personalization_note: string; notes: string; lockedReason?: string };
type ClientRecipeCompositionEditorState = { isOpen: boolean; isSaving: boolean; draft: ClientRecipeCompositionDraftLine[]; error: string };
type ClientWishStatus = 'open' | 'planned' | 'resolved' | 'archived';
type ClientWishPriority = 'low' | 'normal' | 'high';
type ClientWish = { id: number; client_id: number; client_recipe_id: number | null; title: string; description: string; category: string; priority: ClientWishPriority; status: ClientWishStatus; is_active: boolean; created_at: string; updated_at: string; resolved_at: string | null };
type ClientWishCreatePayload = { client_recipe_id: number | null; title: string; description: string; category: string; priority: ClientWishPriority };
type ClientFeedback = { id: number; client_id: number; client_recipe_id: number | null; feedback_type: string; sentiment: string; rating: number | null; text: string; follow_up_needed: boolean; follow_up_note: string; occurred_at: string | null; created_at: string };
type ClientFeedbackCreatePayload = { client_recipe_id: number | null; feedback_type: string; sentiment: string; rating: number | null; text: string; follow_up_needed: boolean; follow_up_note: string; occurred_at: string | null };
type ClientWishFormState = { title: string; description: string; category: string; priority: ClientWishPriority; client_recipe_id: string };
type ClientFeedbackFormState = { feedback_type: string; sentiment: string; rating: string; text: string; follow_up_needed: boolean; follow_up_note: string; occurred_at: string; client_recipe_id: string };
type ClientCardState = { clientId: number | null; wishes: ClientWish[]; feedback: ClientFeedback[]; recipes: ClientRecipe[]; includeArchivedWishes: boolean; wishesStatus: 'idle' | 'loading' | 'ready' | 'error'; feedbackStatus: 'idle' | 'loading' | 'ready' | 'error'; recipesStatus: 'idle' | 'loading' | 'ready' | 'error'; showWishForm: boolean; showFeedbackForm: boolean; wishForm: ClientWishFormState; feedbackForm: ClientFeedbackFormState; wishError: string; feedbackError: string; savingWish: boolean; savingFeedback: boolean; changingWishId: number | null; archivingWishId: number | null };
type ClientRecipeStatusFilter = 'active' | 'archived' | 'all';
type ClientRecipeVersionsStatus = 'idle' | 'loading' | 'ready' | 'error';
type ClientRecipesState = { items: ClientRecipe[]; clients: Client[]; templates: RecipeTemplate[]; versions: RecipeVersion[]; versionsStatus: ClientRecipeVersionsStatus; selectedTemplateId: number | null; selectedDetail: ClientRecipeDetail | null; form: ClientRecipeFormState; includeInactive: boolean; detailStatus: ClientRecipeDetailStatus; showCreateForm: boolean; filters: { search: string; status: ClientRecipeStatusFilter; clientId: string }; compositionEditor: ClientRecipeCompositionEditorState };

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
type PackagingItemsState = { items: PackagingItem[]; formMode: PackagingItemFormMode; form: PackagingItemFormState; catalogCategories: CatalogCategory[]; catalogTags: CatalogTag[]; catalogSaving: CatalogSavingStatus; catalogCreating: CatalogCreateKind | null; showCreateForm: boolean; filters: CatalogBrowserFilters; assignmentDraft: AssignmentDraft };


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
  showCreateForm: boolean;
  filters: CatalogBrowserFilters;
};


type NavigationSection = 'Главная' | 'Алерты' | 'Рецепты' | 'Индивидуальные рецепты' | 'Клиенты' | 'Заказы' | 'Склад' | 'Компоненты' | 'Партии' | 'Движения сырья' | 'Тара' | 'Закупки' | 'Готовность' | 'Производство' | 'Импорт' | 'Отчеты' | 'Настройки' | 'Помощь';
type NavigationStatus = 'ready' | 'empty' | 'planned';
type NavigationItem = { label: string; section: NavigationSection; path: string; status: NavigationStatus };
type NavigationGroup = { title: string; items: NavigationItem[] };

const navigationGroups: NavigationGroup[] = [
  { title: 'Главная', items: [{ label: 'Обзор', section: 'Главная', path: '/', status: 'ready' }, { label: 'Алерты', section: 'Алерты', path: '/alerts', status: 'ready' }] },
  { title: 'Рецепты', items: [
    { label: 'Рецепты', section: 'Рецепты', path: '/recipes', status: 'empty' },
    { label: 'Индивидуальные рецепты', section: 'Индивидуальные рецепты', path: '/client-recipes', status: 'empty' },
  ] },
  { title: 'Клиенты', items: [
    { label: 'Клиенты', section: 'Клиенты', path: '/clients', status: 'empty' },
    { label: 'Заказы', section: 'Заказы', path: '/orders', status: 'empty' },
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
    { label: 'Производство', section: 'Производство', path: '/production', status: 'ready' },
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
let clientsState: ClientsState = { items: [], formMode: 'create', form: emptyClientForm(), includeInactive: false, showCreateForm: false, filters: { search: '', status: 'active' } };
let clientsError = '';
let clientsMessage = '';
let clientCardState: ClientCardState = emptyClientCardState();
let clientRecipesStatus: ClientRecipesStatus = 'idle';
let clientRecipesError = '';
let clientRecipesMessage = '';
let clientRecipesState: ClientRecipesState = { items: [], clients: [], templates: [], versions: [], versionsStatus: 'idle', selectedTemplateId: null, selectedDetail: null, form: emptyClientRecipeForm(), includeInactive: false, detailStatus: 'idle', showCreateForm: false, filters: { search: '', status: 'active', clientId: '' }, compositionEditor: emptyClientRecipeCompositionEditor() };
let ordersStatus: OrdersStatus = 'idle';
let ordersError = '';
let ordersMessage = '';
let productionHistoryState: ProductionHistoryState = { batches: [], selectedBatch: null, status: 'idle', detailStatus: 'idle', error: '', detailError: '', filters: { search: '' } };
let alertsState: AlertsState = { items: [], status: 'idle', actionStatus: 'idle', error: '', message: '', filters: { status: 'open', type: '', search: '' }, lastGeneration: null };
let ordersState: OrdersState = { items: [], clients: [], templates: [], versions: [], clientRecipes: [], packagingItems: [], formMode: 'create', form: emptyOrderForm(), showForm: false, selectedOrder: null, includeInactive: true, filters: { search: '', status: 'active' }, readinessByOrderId: {}, readinessLoadingOrderId: null, readinessError: '', productionByOrderId: {}, productionLoadingOrderId: null, productionError: '', productionConfirmingOrderId: null, productionNotesByOrderId: {} };
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
let packagingItemsState: PackagingItemsState = { items: [], formMode: 'create', form: emptyPackagingItemForm(), catalogCategories: [], catalogTags: [], catalogSaving: 'idle', catalogCreating: null, showCreateForm: false, filters: emptyCatalogBrowserFilters(), assignmentDraft: emptyAssignmentDraft() };
let packagingItemsError = '';
let packagingItemsMessage = '';
let recipesStatus: RecipesStatus = 'idle';
let recipesError = '';
let recipesMessage = '';
let calculationStatus: CalculationStatus = 'idle';
let calculationError = '';
let recipesState: RecipesState = { templates: [], selectedTemplate: null, versions: [], selectedVersionDetail: null, versionDetailStatus: 'idle', ingredients: [], templateForm: emptyRecipeTemplateForm(), versionForm: emptyRecipeVersionForm(), calculation: null, calculationTargetValue: '', calculationTargetUnit: 'g', catalogCategories: [], catalogTags: [], catalogSaving: 'idle', catalogCreating: null, showCreateForm: false, filters: emptyCatalogBrowserFilters() };
let ingredientCatalogControls: CatalogControlState = { categorySearch: '', tagSearch: '', showAllTags: false };
let packagingCatalogControls: CatalogControlState = { categorySearch: '', tagSearch: '', showAllTags: false };

function sectionFromLocation(): NavigationSection {
  const routes: Record<string, NavigationSection> = {
    '/alerts': 'Алерты',
    '/inventory': 'Склад',
    '/ingredients': 'Компоненты',
    '/ingredient-lots': 'Партии',
    '/stock-movements': 'Движения сырья',
    '/recipes': 'Рецепты',
    '/clients': 'Клиенты',
    '/client-recipes': 'Индивидуальные рецепты',
    '/orders': 'Заказы',
    '/production': 'Производство',
    '/packaging-items': 'Тара',
  };
  const placeholderRoutes: Record<string, NavigationSection> = {
    '#purchases': 'Закупки',
    '#production-readiness': 'Готовность',
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
  if (section === 'Алерты') loadAlerts();
  if (section === 'Склад') loadInventory();
  if (section === 'Компоненты') loadIngredients();
  if (section === 'Партии') loadIngredientLots();
  if (section === 'Движения сырья') loadStockMovements();
  if (section === 'Рецепты') loadRecipes();
  if (section === 'Клиенты') loadClients();
  if (section === 'Индивидуальные рецепты') loadClientRecipes();
  if (section === 'Заказы') loadOrders();
  if (section === 'Производство') loadProductionHistory();
  if (section === 'Тара') loadPackagingItems();
}

function renderActivePage(section: NavigationSection) {
  if (section === 'Главная') return dashboardPlaceholder();
  if (section === 'Алерты') return alertsPage();
  if (section === 'Склад') return inventoryPage();
  if (section === 'Компоненты') return ingredientsPage();
  if (section === 'Партии') return ingredientLotsPage();
  if (section === 'Движения сырья') return stockMovementsPage();
  if (section === 'Рецепты') return recipesPage();
  if (section === 'Клиенты') return clientsPage();
  if (section === 'Индивидуальные рецепты') return clientRecipesPage();
  if (section === 'Заказы') return ordersPage();
  if (section === 'Производство') return productionPage();
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
  root.querySelector<HTMLButtonElement>('[data-action="reload-alerts"]')?.addEventListener('click', () => loadAlerts(true));
  root.querySelector<HTMLButtonElement>('[data-action="regenerate-alerts"]')?.addEventListener('click', runAlertRegeneration);
  root.querySelector<HTMLInputElement>('[data-action="filter-alerts-search"]')?.addEventListener('input', (event) => updateAlertSearch(event.currentTarget as HTMLInputElement));
  root.querySelector<HTMLSelectElement>('[data-action="filter-alerts-status"]')?.addEventListener('change', (event) => { alertsState.filters.status = (event.currentTarget as HTMLSelectElement).value as AlertStatusFilter; loadAlerts(true); });
  root.querySelector<HTMLSelectElement>('[data-action="filter-alerts-type"]')?.addEventListener('change', (event) => { alertsState.filters.type = (event.currentTarget as HTMLSelectElement).value as AlertType | ''; loadAlerts(true); });
  root.querySelector<HTMLButtonElement>('[data-action="reset-alert-filters"]')?.addEventListener('click', () => { alertsState.filters = { status: 'open', type: '', search: '' }; loadAlerts(true); });
  root.querySelectorAll<HTMLButtonElement>('[data-action="resolve-alert"]').forEach((button) => button.addEventListener('click', () => runAlertAction(Number(button.dataset.id), 'resolve')));
  root.querySelectorAll<HTMLButtonElement>('[data-action="dismiss-alert"]').forEach((button) => button.addEventListener('click', () => runAlertAction(Number(button.dataset.id), 'dismiss')));
  root.querySelector<HTMLButtonElement>('[data-action="reload-orders"]')?.addEventListener('click', () => loadOrders(true));
  root.querySelectorAll<HTMLButtonElement>('[data-action="open-order-create"]').forEach((button) => button.addEventListener('click', openOrderCreate));
  root.querySelectorAll<HTMLButtonElement>('[data-action="open-order"]').forEach((button) => button.addEventListener('click', () => openOrder(Number(button.dataset.id))));
  root.querySelectorAll<HTMLButtonElement>('[data-action="edit-order"]').forEach((button) => button.addEventListener('click', () => editOrder(Number(button.dataset.id))));
  root.querySelectorAll<HTMLButtonElement>('[data-action="cancel-order"]').forEach((button) => button.addEventListener('click', () => cancelOrder(Number(button.dataset.id))));
  root.querySelectorAll<HTMLButtonElement>('[data-action="archive-order"]').forEach((button) => button.addEventListener('click', () => archiveOrder(Number(button.dataset.id))));
  root.querySelector<HTMLButtonElement>('[data-action="close-order-form"]')?.addEventListener('click', () => { ordersState.showForm = false; ordersState.form = emptyOrderForm(); render(); });
  root.querySelector<HTMLSelectElement>('[data-form="order"] select[name="client_id"]')?.addEventListener('change', () => { saveOrderFormDraftFromDom(); ordersState.form.client_recipe_id = ''; render(); });
  root.querySelector<HTMLButtonElement>('[data-action="close-order-detail"]')?.addEventListener('click', () => { ordersState.selectedOrder = null; render(); });
  root.querySelectorAll<HTMLButtonElement>('[data-action="check-order-readiness"], [data-action="retry-order-readiness"]').forEach((button) => button.addEventListener('click', () => checkOrderReadiness(Number(button.dataset.id))));
  root.querySelectorAll<HTMLButtonElement>('[data-action="open-production-confirmation"]').forEach((button) => button.addEventListener('click', () => openProductionConfirmation(Number(button.dataset.id))));
  root.querySelectorAll<HTMLButtonElement>('[data-action="cancel-production-confirmation"]').forEach((button) => button.addEventListener('click', () => cancelProductionConfirmation(Number(button.dataset.id))));
  root.querySelectorAll<HTMLButtonElement>('[data-action="confirm-production"]').forEach((button) => button.addEventListener('click', () => confirmProduction(Number(button.dataset.id))));
  root.querySelector<HTMLTextAreaElement>('[data-action="production-notes"]')?.addEventListener('input', (event) => { const id = Number((event.currentTarget as HTMLTextAreaElement).dataset.id); ordersState.productionNotesByOrderId[id] = (event.currentTarget as HTMLTextAreaElement).value; });
  root.querySelector<HTMLButtonElement>('[data-action="reload-production-history"]')?.addEventListener('click', () => loadProductionHistory(true));
  root.querySelector<HTMLInputElement>('[data-action="filter-production-search"]')?.addEventListener('input', (event) => { productionHistoryState.filters.search = (event.currentTarget as HTMLInputElement).value; render(); });
  root.querySelectorAll<HTMLButtonElement>('[data-action="open-production-batch"]').forEach((button) => button.addEventListener('click', () => openProductionBatch(Number(button.dataset.id))));
  root.querySelector<HTMLButtonElement>('[data-action="close-production-batch"]')?.addEventListener('click', () => { productionHistoryState.selectedBatch = null; productionHistoryState.detailStatus = 'idle'; render(); });
  root.querySelectorAll<HTMLButtonElement>('[data-action="open-order-production-batch"]').forEach((button) => button.addEventListener('click', () => openProductionBatchByOrder(Number(button.dataset.id))));
  root.querySelector<HTMLFormElement>('[data-form="order"]')?.addEventListener('submit', submitOrderForm);
  root.querySelector<HTMLInputElement>('[data-action="filter-orders-search"]')?.addEventListener('input', (event) => { ordersState.filters.search = (event.currentTarget as HTMLInputElement).value; render(); });
  root.querySelector<HTMLSelectElement>('[data-action="filter-orders-status"]')?.addEventListener('change', (event) => { ordersState.filters.status = (event.currentTarget as HTMLSelectElement).value as OrderStatusFilter; render(); });
  root.querySelector<HTMLButtonElement>('[data-action="reset-order-filters"]')?.addEventListener('click', () => { ordersState.filters = { search: '', status: 'active' }; render(); });
  root.querySelector<HTMLSelectElement>('[data-action="select-order-source-type"]')?.addEventListener('change', (event) => { saveOrderFormDraftFromDom(); ordersState.form.source_type = (event.currentTarget as HTMLSelectElement).value as OrderSourceType; ordersState.form.recipe_version_id = ''; ordersState.form.client_recipe_id = ''; render(); });
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
  root.querySelectorAll<HTMLButtonElement>('[data-action="open-recipe-create"]').forEach((button) => button.addEventListener('click', openRecipeCreateForm));
  root.querySelectorAll<HTMLButtonElement>('[data-action="hide-recipe-create"]').forEach((button) => button.addEventListener('click', hideRecipeCreateForm));
  root.querySelector<HTMLButtonElement>('[data-action="close-recipe-detail"]')?.addEventListener('click', closeRecipeDetail);
  root.querySelector<HTMLInputElement>('[data-action="filter-recipes-search"]')?.addEventListener('input', (event) => updateRecipeFilterSearch(event.currentTarget as HTMLInputElement));
  root.querySelector<HTMLSelectElement>('[data-action="filter-recipes-category"]')?.addEventListener('change', (event) => { recipesState.filters.categoryId = catalogCategoryFilterValue((event.currentTarget as HTMLSelectElement).value); render(); });
  root.querySelector<HTMLSelectElement>('[data-action="filter-recipes-status"]')?.addEventListener('change', (event) => { recipesState.filters.status = (event.currentTarget as HTMLSelectElement).value as CatalogStatusFilter; render(); });
  root.querySelectorAll<HTMLButtonElement>('[data-action="clear-recipe-filter"]').forEach((button) => button.addEventListener('click', () => clearRecipeFilter(button.dataset.filter ?? '')));
  root.querySelectorAll<HTMLButtonElement>('[data-action="reset-recipe-filters"]').forEach((button) => button.addEventListener('click', () => { recipesState.filters = emptyCatalogBrowserFilters(); render(); }));
  root.querySelector<HTMLButtonElement>('[data-action="reload-recipe-ingredients"]')?.addEventListener('click', () => refreshRecipeIngredientOptions(true));
  root.querySelector<HTMLButtonElement>('[data-action="reload-clients"]')?.addEventListener('click', () => loadClients(true));
  root.querySelectorAll<HTMLButtonElement>('[data-action="open-client-create"]').forEach((button) => button.addEventListener('click', openClientCreateForm));
  root.querySelectorAll<HTMLButtonElement>('[data-action="hide-client-create"]').forEach((button) => button.addEventListener('click', hideClientCreateForm));
  root.querySelectorAll<HTMLButtonElement>('[data-action="start-client-edit"]').forEach((button) => button.addEventListener('click', () => startEditClient(Number(button.dataset.id))));
  root.querySelectorAll<HTMLButtonElement>('[data-action="cancel-client-edit"]').forEach((button) => button.addEventListener('click', closeClientEdit));
  root.querySelector<HTMLInputElement>('[data-action="filter-clients-search"]')?.addEventListener('input', (event) => updateClientFilterSearch(event.currentTarget as HTMLInputElement));
  root.querySelector<HTMLSelectElement>('[data-action="filter-clients-status"]')?.addEventListener('change', (event) => updateClientStatusFilter((event.currentTarget as HTMLSelectElement).value as ClientStatusFilter));
  root.querySelectorAll<HTMLButtonElement>('[data-action="reset-client-filters"]').forEach((button) => button.addEventListener('click', resetClientFilters));
  root.querySelectorAll<HTMLButtonElement>('[data-action="clear-client-filter"]').forEach((button) => button.addEventListener('click', () => clearClientFilter(button.dataset.filter ?? '')));
  root.querySelectorAll<HTMLButtonElement>('[data-action="archive-client"]').forEach((button) => button.addEventListener('click', () => deactivateClient(Number(button.dataset.id))));
  root.querySelector<HTMLFormElement>('[data-form="client"]')?.addEventListener('submit', submitClientForm);
  root.querySelector<HTMLButtonElement>('[data-action="toggle-client-wish-form"]')?.addEventListener('click', toggleClientWishForm);
  root.querySelector<HTMLButtonElement>('[data-action="toggle-archived-client-wishes"]')?.addEventListener('click', toggleArchivedClientWishes);
  root.querySelector<HTMLFormElement>('[data-form="client-wish"]')?.addEventListener('submit', submitClientWishForm);
  root.querySelector<HTMLButtonElement>('[data-action="close-client-wish-form"]')?.addEventListener('click', closeClientWishForm);
  root.querySelectorAll<HTMLButtonElement>('[data-action="change-client-wish-status"]').forEach((button) => button.addEventListener('click', () => changeClientWishStatus(Number(button.dataset.id), button.dataset.status as ClientWishStatus)));
  root.querySelectorAll<HTMLButtonElement>('[data-action="archive-client-wish"]').forEach((button) => button.addEventListener('click', () => archiveClientWishFromCard(Number(button.dataset.id))));
  root.querySelector<HTMLButtonElement>('[data-action="toggle-client-feedback-form"]')?.addEventListener('click', toggleClientFeedbackForm);
  root.querySelector<HTMLFormElement>('[data-form="client-feedback"]')?.addEventListener('submit', submitClientFeedbackForm);
  root.querySelector<HTMLButtonElement>('[data-action="close-client-feedback-form"]')?.addEventListener('click', closeClientFeedbackForm);
  root.querySelector<HTMLButtonElement>('[data-action="reload-client-recipes"]')?.addEventListener('click', () => loadClientRecipes(true));
  root.querySelectorAll<HTMLButtonElement>('[data-action="open-client-recipe-create"]').forEach((button) => button.addEventListener('click', openClientRecipeCreate));
  root.querySelectorAll<HTMLButtonElement>('[data-action="hide-client-recipe-create"]').forEach((button) => button.addEventListener('click', hideClientRecipeCreate));
  root.querySelector<HTMLButtonElement>('[data-action="close-client-recipe-detail"]')?.addEventListener('click', closeClientRecipeDetail);
  root.querySelector<HTMLInputElement>('[data-action="filter-client-recipes-search"]')?.addEventListener('input', (event) => updateClientRecipeFilterSearch(event.currentTarget as HTMLInputElement));
  root.querySelector<HTMLSelectElement>('[data-action="filter-client-recipes-status"]')?.addEventListener('change', (event) => updateClientRecipeStatusFilter((event.currentTarget as HTMLSelectElement).value as ClientRecipeStatusFilter));
  root.querySelector<HTMLSelectElement>('[data-action="filter-client-recipes-client"]')?.addEventListener('change', (event) => { clientRecipesState.filters.clientId = (event.currentTarget as HTMLSelectElement).value; render(); });
  root.querySelectorAll<HTMLButtonElement>('[data-action="reset-client-recipe-filters"]').forEach((button) => button.addEventListener('click', resetClientRecipeFilters));
  root.querySelectorAll<HTMLButtonElement>('[data-action="clear-client-recipe-filter"]').forEach((button) => button.addEventListener('click', () => clearClientRecipeFilter(button.dataset.filter ?? '')));
  root.querySelector<HTMLSelectElement>('[data-action="select-client-recipe-template"]')?.addEventListener('change', (event) => selectClientRecipeTemplate((event.currentTarget as HTMLSelectElement).value));
  root.querySelector<HTMLFormElement>('[data-form="client-recipe"]')?.addEventListener('submit', submitClientRecipeForm);
  root.querySelectorAll<HTMLButtonElement>('[data-action="open-client-recipe-detail"]').forEach((button) => button.addEventListener('click', () => openClientRecipe(Number(button.dataset.id))));
  root.querySelectorAll<HTMLButtonElement>('[data-action="archive-client-recipe"]').forEach((button) => button.addEventListener('click', () => deactivateClientRecipe(Number(button.dataset.id))));
  root.querySelectorAll<HTMLButtonElement>('[data-action="restore-client-recipe"]').forEach((button) => button.addEventListener('click', () => restoreClientRecipe(Number(button.dataset.id))));
  root.querySelector<HTMLButtonElement>('[data-action="open-client-recipe-composition-editor"]')?.addEventListener('click', openClientRecipeCompositionEditor);
  root.querySelector<HTMLFormElement>('[data-form="client-recipe-composition"]')?.addEventListener('submit', submitClientRecipeCompositionEditor);
  root.querySelector<HTMLButtonElement>('[data-action="add-client-recipe-composition-line"]')?.addEventListener('click', addClientRecipeCompositionLine);
  root.querySelectorAll<HTMLButtonElement>('[data-action="remove-client-recipe-composition-line"]').forEach((button) => button.addEventListener('click', () => removeClientRecipeCompositionLine(Number(button.dataset.index))));
  root.querySelectorAll<HTMLButtonElement>('[data-action="move-client-recipe-composition-line"]').forEach((button) => button.addEventListener('click', () => moveClientRecipeCompositionLine(Number(button.dataset.index), Number(button.dataset.direction))));
  root.querySelector<HTMLButtonElement>('[data-action="reset-client-recipe-composition-editor"]')?.addEventListener('click', resetClientRecipeCompositionEditor);
  root.querySelector<HTMLButtonElement>('[data-action="close-client-recipe-composition-editor"]')?.addEventListener('click', closeClientRecipeCompositionEditor);
  root.querySelector<HTMLButtonElement>('[data-action="reload-packaging-items"]')?.addEventListener('click', () => loadPackagingItems(true));
  root.querySelectorAll<HTMLButtonElement>('[data-action="new-packaging-item"]').forEach((button) => button.addEventListener('click', openPackagingCreateForm));
  root.querySelector<HTMLButtonElement>('[data-action="hide-packaging-create-form"]')?.addEventListener('click', hidePackagingCreateForm);
  root.querySelector<HTMLButtonElement>('[data-action="cancel-packaging-edit"]')?.addEventListener('click', cancelPackagingEdit);
  root.querySelectorAll<HTMLButtonElement>('[data-action="edit-packaging-item"]').forEach((button) => button.addEventListener('click', () => startEditPackagingItem(Number(button.dataset.id))));
  root.querySelectorAll<HTMLButtonElement>('[data-action="deactivate-packaging-item"]').forEach((button) => button.addEventListener('click', () => deactivatePackagingItem(Number(button.dataset.id))));
  root.querySelector<HTMLFormElement>('[data-form="packaging-item"]')?.addEventListener('submit', submitPackagingItemForm);
  root.querySelector<HTMLInputElement>('[data-action="filter-packaging-search"]')?.addEventListener('input', (event) => updatePackagingFilterSearch(event.currentTarget as HTMLInputElement));
  root.querySelector<HTMLSelectElement>('[data-action="filter-packaging-category"]')?.addEventListener('change', (event) => { packagingItemsState.filters.categoryId = catalogCategoryFilterValue((event.currentTarget as HTMLSelectElement).value); render(); });
  root.querySelector<HTMLSelectElement>('[data-action="filter-packaging-kind"]')?.addEventListener('change', (event) => { packagingItemsState.filters.systemType = (event.currentTarget as HTMLSelectElement).value; render(); });
  root.querySelector<HTMLSelectElement>('[data-action="filter-packaging-status"]')?.addEventListener('change', (event) => { packagingItemsState.filters.status = (event.currentTarget as HTMLSelectElement).value as CatalogStatusFilter; render(); });
  root.querySelector<HTMLSelectElement>('[data-action="add-packaging-tag-filter"]')?.addEventListener('change', (event) => addPackagingTagFilter((event.currentTarget as HTMLSelectElement).value));
  root.querySelectorAll<HTMLButtonElement>('[data-action="remove-packaging-tag-filter"]').forEach((button) => button.addEventListener('click', () => removePackagingTagFilter(Number(button.dataset.id))));
  root.querySelectorAll<HTMLButtonElement>('[data-action="clear-packaging-filter"]').forEach((button) => button.addEventListener('click', () => clearPackagingFilter(button.dataset.filter ?? '')));
  root.querySelectorAll<HTMLButtonElement>('[data-action="reset-packaging-filters"]').forEach((button) => button.addEventListener('click', () => { packagingItemsState.filters = emptyCatalogBrowserFilters(); render(); }));
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


function alertSeverityLabel(severity: AlertSeverity) { return ({ info: 'Информация', warning: 'Предупреждение', critical: 'Критично', blocking: 'Блокирует работу' } as Record<AlertSeverity, string>)[severity] ?? severity; }
function alertStatusLabel(status: AlertStatus) { return ({ open: 'Открыт', resolved: 'Решён', dismissed: 'Скрыт' } as Record<AlertStatus, string>)[status] ?? status; }
function alertTypeLabel(type: AlertType | '') { const labels: Record<AlertType, string> = { low_ingredient_stock: 'Низкий остаток компонента', low_packaging_stock: 'Низкий остаток тары', ingredient_expiration_soon: 'Скоро истекает срок годности', ingredient_expired: 'Просроченная партия', insufficient_materials_for_order: 'Не хватает компонентов для заказа', insufficient_packaging_for_order: 'Не хватает тары для заказа' }; return type ? labels[type] ?? type : 'Все типы'; }
function alertRelatedEntityLabel(alert: AlertResponse) { const labels: Record<string, string> = { ingredient: 'Компонент', ingredient_lot: 'Партия компонента', packaging_item: 'Тара', order: 'Заказ' }; const label = labels[alert.related_entity_type] ?? 'Связанная запись'; return `${label} №${alert.related_entity_id}`; }
function alertPillClass(value: AlertSeverity | AlertStatus) { return value === 'blocking' || value === 'critical' ? 'danger' : value === 'warning' || value === 'dismissed' ? 'warning' : value === 'resolved' ? 'success' : value === 'open' ? 'info' : 'muted'; }
function alertTypeOptions(selected: AlertType | '') { const types: AlertType[] = ['low_ingredient_stock','low_packaging_stock','ingredient_expiration_soon','ingredient_expired','insufficient_materials_for_order','insufficient_packaging_for_order']; return `<option value="" ${selected === '' ? 'selected' : ''}>Все типы</option>${types.map((type) => `<option value="${type}" ${selected === type ? 'selected' : ''}>${alertTypeLabel(type)}</option>`).join('')}`; }
function filteredAlerts() { const search = normalizeSearchText(alertsState.filters.search); if (!search) return alertsState.items; return alertsState.items.filter((alert) => normalizeSearchText([alert.message, alert.recommended_action, alertRelatedEntityLabel(alert), String(alert.related_entity_id), alertTypeLabel(alert.type), alertStatusLabel(alert.status), alertSeverityLabel(alert.severity)].join(' ')).includes(search)); }
function alertsPage() {
  const items = filteredAlerts();
  return `<div class="catalog-layout"><section class="card catalog-intro"><div><p class="card-kicker">Рабочий помощник</p><h2>Алерты</h2><p>Здесь система показывает проблемы, которые могут помешать работе мастерской: остатки, сроки годности и нехватку материалов для заказов.</p><p class="next-step">Алерты не запускают списания, закупки или производство. Обновление, решение и скрытие выполняются только по вашему нажатию.</p></div><div class="actions"><button class="primary-action" type="button" data-action="regenerate-alerts" ${alertsState.actionStatus === 'loading' ? 'disabled' : ''}>${alertsState.actionStatus === 'loading' ? 'Обновляем…' : 'Обновить алерты'}</button><button class="secondary-action" type="button" data-action="reload-alerts">Загрузить список</button></div></section>${alertsState.message ? `<p class="page-message">${escapeHtml(alertsState.message)}</p>` : ''}${alertsState.error ? `<p class="page-message error-message">${escapeHtml(alertsState.error)}</p>` : ''}${alertsState.lastGeneration ? alertGenerationSummary(alertsState.lastGeneration) : ''}${alertFilterToolbar(items.length)}${alertsState.status === 'loading' || alertsState.status === 'idle' ? '<section class="card"><h2>Загружаем алерты…</h2><p>Получаем текущий список из локального приложения.</p></section>' : alertsState.status === 'error' ? '<section class="card error-card"><p class="card-kicker">Алерты</p><h2>Не удалось загрузить алерты</h2><p>Проверьте, что локальное приложение запущено.</p><button class="primary-action" type="button" data-action="reload-alerts">Повторить загрузку</button></section>' : alertList(items)}</div>`;
}
function alertGenerationSummary(result: AlertGenerationResponse) { return `<section class="card data-card"><p class="card-kicker">Результат обновления</p><h2>Алерты обновлены</h2><p>Новых — ${result.created_count}, обновлено — ${result.updated_count}, решено автоматически — ${result.resolved_count}, открытых — ${result.open_count}.</p></section>`; }
function alertFilterToolbar(resultCount: number) { const f = alertsState.filters; return `<section class="card data-card catalog-browser"><p class="card-kicker">Фильтры</p><h2>Найти нужный алерт</h2><div class="catalog-toolbar"><label class="full-span">Поиск<input type="search" data-action="filter-alerts-search" value="${escapeHtml(f.search)}" placeholder="Текст алерта, действие, тип или номер связанной записи" /></label><label>Статус<select data-action="filter-alerts-status"><option value="open" ${f.status === 'open' ? 'selected' : ''}>Открытые</option><option value="resolved" ${f.status === 'resolved' ? 'selected' : ''}>Решённые</option><option value="dismissed" ${f.status === 'dismissed' ? 'selected' : ''}>Скрытые</option><option value="all" ${f.status === 'all' ? 'selected' : ''}>Все</option></select></label><label>Тип<select data-action="filter-alerts-type">${alertTypeOptions(f.type)}</select></label></div><div class="catalog-summary"><span>Показаны алерты: ${resultCount} из ${alertsState.items.length}</span><button class="secondary-action compact" type="button" data-action="reset-alert-filters">Сбросить фильтры</button></div></section>`; }
function alertList(items: AlertResponse[]) { if (alertsState.items.length === 0 && alertsState.filters.status === 'open' && !alertsState.filters.type && !alertsState.filters.search) return `<section class="card empty-card"><h2>Открытых алертов нет</h2><p>Сейчас система не видит проблем, которые требуют внимания.</p><p class="next-step">Если вы изменили склад или заказы, нажмите «Обновить алерты».</p></section>`; if (items.length === 0) return `<section class="card empty-card"><h2>По этим фильтрам алертов нет</h2><p>Измените фильтр или сбросьте поиск.</p><button class="secondary-action" type="button" data-action="reset-alert-filters">Сбросить фильтры</button></section>`; return `<section class="card data-card"><p class="card-kicker">Список</p><h2>Алерты, требующие внимания</h2><div class="recipe-lines">${items.map(alertCard).join('')}</div></section>`; }
function alertCard(alert: AlertResponse) { const terminal = alert.status === 'resolved' ? 'Этот алерт уже закрыт.' : alert.status === 'dismissed' ? 'Этот алерт скрыт.' : ''; return `<article class="recipe-line alert-card"><div class="section-heading"><div><h3>${escapeHtml(alert.message)}</h3><p><span class="pill ${alertPillClass(alert.severity)}">${alertSeverityLabel(alert.severity)}</span> <span class="pill ${alertPillClass(alert.status)}">${alertStatusLabel(alert.status)}</span> <span class="pill muted">${alertTypeLabel(alert.type)}</span></p></div><small>Создан: ${formatDateTime(alert.created_at)}<br>Обновлён: ${formatDateTime(alert.updated_at)}</small></div><div class="readiness-grid"><div><strong>Что случилось?</strong><p>${escapeHtml(alert.message)}</p></div><div><strong>Насколько это важно?</strong><p>${alertSeverityLabel(alert.severity)}</p></div><div><strong>К чему относится?</strong><p>${escapeHtml(alertRelatedEntityLabel(alert))}</p></div><div><strong>Что сделать дальше?</strong><p>${escapeHtml(alert.recommended_action || 'Проверьте связанную запись и решите, нужно ли действие.')}</p></div></div>${alert.status === 'open' ? `<div class="actions"><button class="primary-action" type="button" data-action="resolve-alert" data-id="${alert.id}" ${alertsState.actionStatus === 'loading' ? 'disabled' : ''}>Отметить решённым</button><button class="secondary-action" type="button" data-action="dismiss-alert" data-id="${alert.id}" ${alertsState.actionStatus === 'loading' ? 'disabled' : ''}>Скрыть</button></div>` : `<p class="next-step">${terminal}</p>`}</article>`; }
function loadAlerts(force = false) { if (!force && (alertsState.status === 'loading' || alertsState.status === 'ready')) return; alertsState.status = 'loading'; alertsState.error = ''; render(); getAlerts(alertsState.filters).then((response) => { alertsState.items = response.alerts; alertsState.status = 'ready'; alertsState.error = ''; render(); }).catch(() => { alertsState.status = 'error'; alertsState.error = 'Не удалось загрузить алерты. Проверьте, что локальное приложение запущено.'; render(); }); }
function reloadAlertsAfterAction(message: string) { return getAlerts(alertsState.filters).then((response) => { alertsState.items = response.alerts; alertsState.status = 'ready'; alertsState.message = message; alertsState.error = ''; }); }
function runAlertAction(id: number, action: 'resolve' | 'dismiss') { alertsState.actionStatus = 'loading'; alertsState.message = ''; alertsState.error = ''; render(); const request = action === 'resolve' ? resolveAlert(id) : dismissAlert(id); request.then(() => reloadAlertsAfterAction(action === 'resolve' ? 'Алерт отмечен решённым.' : 'Алерт скрыт.')).catch(() => { alertsState.error = action === 'resolve' ? 'Не удалось отметить алерт решённым. Проверьте локальное приложение и попробуйте снова.' : 'Не удалось скрыть алерт. Проверьте локальное приложение и попробуйте снова.'; }).finally(() => { alertsState.actionStatus = 'idle'; render(); }); }
function runAlertRegeneration() { alertsState.actionStatus = 'loading'; alertsState.message = ''; alertsState.error = ''; render(); regenerateAlerts().then((result) => { alertsState.lastGeneration = result; return reloadAlertsAfterAction(`Алерты обновлены: новых — ${result.created_count}, обновлено — ${result.updated_count}, решено автоматически — ${result.resolved_count}, открытых — ${result.open_count}.`); }).catch(() => { alertsState.error = 'Не удалось обновить алерты. Проверьте локальное приложение и попробуйте снова.'; }).finally(() => { alertsState.actionStatus = 'idle'; render(); }); }
function updateAlertSearch(input: HTMLInputElement) { const cursor = input.selectionStart ?? input.value.length; alertsState.filters.search = input.value; render(); const next = document.querySelector<HTMLInputElement>('[data-action="filter-alerts-search"]'); next?.focus(); next?.setSelectionRange(Math.min(cursor, next.value.length), Math.min(cursor, next.value.length)); }

function dashboardPlaceholder() {
  return `${onboardingCard()}<section class="card"><p class="card-kicker">Сегодня в мастерской</p><h2>Что уже можно открыть</h2><div class="readiness-grid"><div><h3>Работает сейчас</h3><ul><li>Рецепты</li><li>Индивидуальные рецепты</li><li>Клиенты</li><li>Заказы</li><li>Компоненты</li><li>Складской обзор</li><li>Тара</li><li>История производства</li><li>Алерты</li></ul></div><div><h3>Скоро</h3><ul><li>Закупки</li><li>Импорт</li><li>Отчеты</li></ul></div></div></section>`;
}






function productionPage() {
  const visible = filteredProductionBatches();
  return `<section class="card"><p class="card-kicker">История изготовленных партий</p><h2>Производство</h2><p>Здесь показаны уже изготовленные партии. Это исторический журнал: данные партии и списания не редактируются.</p><div class="actions"><button class="secondary-action" type="button" data-action="reload-production-history">Обновить историю</button></div></section>${productionHistoryToolbar()}${productionHistoryState.error ? `<p class="page-message error-message">${escapeHtml(productionHistoryState.error)}</p>` : ''}${productionHistoryState.status === 'loading' ? '<section class="card"><p>Загружаем историю производства…</p></section>' : productionHistoryList(visible)}${productionHistoryDetailPanel()}`;
}
function productionHistoryToolbar() { return `<section class="card filter-card"><label>Поиск по истории<input data-action="filter-production-search" value="${escapeHtml(productionHistoryState.filters.search)}" placeholder="Продукт, клиент, заметка, номер заказа или партии" /></label></section>`; }
function filteredProductionBatches() { const q=productionHistoryState.filters.search.trim().toLowerCase(); if(!q) return productionHistoryState.batches; return productionHistoryState.batches.filter((b)=>[b.product_name,b.client_name??'',b.notes,String(b.order_id),String(b.id)].some((v)=>v.toLowerCase().includes(q))); }
function productionHistoryList(items: ProductionBatchListItem[]) { if (productionHistoryState.status === 'error') return `<section class="card empty-card"><h2>История недоступна</h2><p>Не удалось загрузить историю производства. Проверьте, что локальное приложение запущено.</p><button class="secondary-action" type="button" data-action="reload-production-history">Обновить историю</button></section>`; if (productionHistoryState.batches.length===0) return `<section class="card empty-card"><h2>Изготовленных партий пока нет</h2><p>Изготовленных партий пока нет. Они появятся здесь после подтверждения изготовления заказа.</p></section>`; if (items.length===0) return `<section class="card empty-card"><h2>Партии не найдены</h2><p>Измените поиск, чтобы снова увидеть историю.</p></section>`; return `<section class="card data-card"><div class="section-heading"><div><p class="card-kicker">Журнал</p><h2>Изготовленные партии</h2></div><span class="pill info">${items.length}</span></div><div class="table-wrap"><table class="compact-catalog-table"><thead><tr><th>Дата</th><th>Продукт</th><th>Клиент</th><th>Партия</th><th>Себестоимость</th><th>Цена/маржа</th><th>Списания</th><th>Действие</th></tr></thead><tbody>${items.map((b)=>`<tr class="${productionHistoryState.selectedBatch?.id===b.id?'catalog-row-selected':''}"><td>${formatDateTime(b.produced_at)}</td><td><strong>${escapeHtml(b.product_name)}</strong><small>Заказ №${b.order_id}</small></td><td>${escapeHtml(b.client_name || 'Клиент не указан')}</td><td>${quantityLabel(b.final_batch_value,b.final_batch_unit)}</td><td>${moneyOrMissing(b.total_cost)}</td><td>${moneyOrMissing(b.sale_price)}<small>Маржа: ${moneyOrMissing(b.margin)} · Налог: ${moneyOrMissing(b.tax)}</small></td><td>Компоненты: ${b.ingredient_line_count}<small>Тара: ${b.packaging_line_count}</small></td><td><button class="secondary-action compact" type="button" data-action="open-production-batch" data-id="${b.id}">Открыть партию</button></td></tr>`).join('')}</tbody></table></div><p class="next-step">Партии доступны только для просмотра. Изменения склада смотрите в складских движениях.</p></section>`; }
function productionHistoryDetailPanel() { const b=productionHistoryState.selectedBatch; if (productionHistoryState.detailStatus==='loading') return `<section class="card"><p>Открываем производственную партию…</p></section>`; if (productionHistoryState.detailStatus==='error') return `<section class="card empty-card"><h2>Не удалось открыть партию</h2><p>${escapeHtml(productionHistoryState.detailError || 'Не удалось открыть производственную партию. Обновите историю производства и попробуйте ещё раз.')}</p></section>`; if (!b) return ''; return `<section class="card data-card readiness-result"><div class="section-heading"><div><p class="card-kicker">Историческая партия</p><h2>Партия №${b.id}</h2></div><button class="secondary-action" type="button" data-action="close-production-batch">Вернуться к списку</button></div><div class="readiness-grid"><div><strong>Дата изготовления</strong><p>${formatDateTime(b.produced_at)}</p></div><div><strong>Заказ</strong><p>№${b.order_id}</p></div><div><strong>Продукт</strong><p>${escapeHtml(b.product_name || 'Не указан')}</p></div><div><strong>Клиент</strong><p>${escapeHtml(b.client_name || 'Не указан')}</p></div><div><strong>Источник</strong><p>${productionSourceLabel(b)}</p></div><div><strong>Размер партии</strong><p>${quantityLabel(b.final_batch_value,b.final_batch_unit)}</p></div></div>${b.notes ? `<p><strong>Заметка к партии:</strong><br>${escapeHtml(b.notes)}</p>` : '<p><strong>Заметка к партии:</strong> нет заметки.</p>'}<div class="readiness-block"><h3>Снимок себестоимости</h3><div class="readiness-grid"><div><strong>Компоненты</strong><p>${moneyOrMissing(b.component_cost)}</p></div><div><strong>Тара</strong><p>${moneyOrMissing(b.packaging_cost)}</p></div><div><strong>Прочие расходы</strong><p>${moneyOrMissing(b.other_cost)}</p></div><div><strong>Итого</strong><p>${moneyOrMissing(b.total_cost)}</p></div><div><strong>Цена продажи</strong><p>${moneyOrMissing(b.sale_price)}</p></div><div><strong>Налог</strong><p>${moneyOrMissing(b.tax)}</p></div><div><strong>Маржа</strong><p>${moneyOrMissing(b.margin)}</p></div><div><strong>Маржинальность</strong><p>${b.margin_percent ? `${escapeHtml(b.margin_percent)}%` : 'Не рассчитано'}</p></div></div><p class="next-step">Это снимок на момент изготовления. Значения не пересчитываются задним числом.</p></div>${productionIngredientsTable(b.ingredients)}${productionPackagingTable(b.packaging)}<p class="next-step">Партия доступна только для просмотра. Списания уже записаны как складские движения.</p></section>`; }
function productionSourceLabel(b: ProductionBatchDetailResponse) { if (b.client_recipe_id) return `Индивидуальная формула №${b.client_recipe_id}`; if (b.recipe_version_id) return `Базовая версия рецепта №${b.recipe_version_id}`; return 'Источник не указан'; }
function productionIngredientsTable(rows: ProductionBatchIngredientResponse[]) { return `<div class="readiness-block"><h3>Списанные компоненты</h3>${rows.length ? `<div class="table-wrap"><table class="compact-catalog-table"><thead><tr><th>Компонент</th><th>Партия</th><th>Нужно</th><th>Списано</th><th>Ед.</th><th>Цена за ед.</th><th>Стоимость</th><th>Срок годности</th></tr></thead><tbody>${rows.map((r)=>`<tr><td><strong>${escapeHtml(r.ingredient_name_snapshot)}</strong></td><td>${escapeHtml(r.lot_code_snapshot || 'Без номера')}</td><td>${escapeHtml(r.required_quantity)}</td><td>${escapeHtml(r.consumed_quantity)}</td><td>${unitLabel(r.unit)}</td><td>${moneyOrMissing(r.unit_cost_snapshot)}</td><td>${moneyOrMissing(r.total_cost_snapshot)}</td><td>${r.expiration_date_snapshot ? formatDate(r.expiration_date_snapshot) : 'Не указан'}</td></tr>`).join('')}</tbody></table></div>` : '<p class="empty-hint">Списания компонентов в снимке не найдены.</p>'}</div>`; }
function productionPackagingTable(rows: ProductionBatchPackagingResponse[]) { return `<div class="readiness-block"><h3>Списанная тара</h3>${rows.length ? `<div class="table-wrap"><table class="compact-catalog-table"><thead><tr><th>Тара</th><th>Количество</th><th>Ед.</th><th>Цена за ед.</th><th>Стоимость</th></tr></thead><tbody>${rows.map((r)=>`<tr><td><strong>${escapeHtml(r.packaging_name_snapshot)}</strong></td><td>${escapeHtml(r.quantity)}</td><td>${unitLabel(r.unit)}</td><td>${moneyOrMissing(r.unit_cost_snapshot)}</td><td>${moneyOrMissing(r.total_cost_snapshot)}</td></tr>`).join('')}</tbody></table></div>` : '<p class="empty-hint">Списания тары в снимке не найдены.</p>'}</div>`; }
function loadProductionHistory(force=false) { if(!force && (productionHistoryState.status==='loading'||productionHistoryState.status==='ready')) return; productionHistoryState.status='loading'; productionHistoryState.error=''; render(); getProductionBatches().then((response)=>{ productionHistoryState.batches=response.production_batches; productionHistoryState.status='ready'; productionHistoryState.error=''; render(); }).catch(()=>{ productionHistoryState.status='error'; productionHistoryState.error='Не удалось загрузить историю производства. Проверьте, что локальное приложение запущено.'; render(); }); }
function openProductionBatch(id:number) { productionHistoryState.detailStatus='loading'; productionHistoryState.detailError=''; render(); getProductionBatch(id).then((batch)=>{ productionHistoryState.selectedBatch=batch; productionHistoryState.detailStatus='ready'; render(); }).catch(()=>{ productionHistoryState.detailStatus='error'; productionHistoryState.detailError='Не удалось открыть производственную партию. Обновите историю производства и попробуйте ещё раз.'; render(); }); }
function openProductionBatchByOrder(id:number) { ordersState.productionLoadingOrderId=id; ordersState.productionError=''; render(); getProductionBatchByOrder(id).then((batch)=>{ ordersState.productionByOrderId[id]=batch; ordersState.productionLoadingOrderId=null; productionHistoryState.selectedBatch=batch; productionHistoryState.detailStatus='ready'; productionHistoryState.detailError=''; activeSection='Производство'; window.history.pushState({}, '', pathForSection(activeSection)); loadProductionHistory(true); render(); }).catch((e)=>{ ordersState.productionLoadingOrderId=null; const status=typeof e==='object' && e && 'status' in e ? Number((e as {status?: number}).status) : 0; ordersState.productionError=status===404 ? 'Для этого заказа производственная партия пока не найдена.' : 'Не удалось открыть производственную партию. Обновите историю производства и попробуйте ещё раз.'; render(); }); }

function emptyOrderForm(): OrderFormState { return { id: null, client_id: '', source_type: 'recipe_version', recipe_version_id: '', client_recipe_id: '', product_name: '', target_batch_size_value: '', target_batch_size_unit: 'g', packaging_item_id: '', packaging_quantity: '', sale_price: '', ordered_at: '', planned_production_at: '', notes: '' }; }
function ordersPage() {
  if (ordersStatus === 'idle' || ordersStatus === 'loading') return `<section class="card"><p class="card-kicker">Заказы</p><h2>Загружаем заказы…</h2><p>Получаем рабочий список заказов, клиентов, рецептов и тары из локального приложения.</p></section>`;
  if (ordersStatus === 'error') return `<section class="card error-card"><p class="card-kicker">Заказы</p><h2>Не удалось загрузить заказы</h2><p>${ordersError || 'Локальное приложение временно недоступно.'}</p><p class="next-step">Проверьте, что локальное приложение запущено, и попробуйте обновить раздел.</p><button class="primary-action" type="button" data-action="reload-orders">Повторить загрузку</button></section>`;
  const items = filteredOrders();
  const workspace = ordersState.showForm ? orderFormPanel() : ordersState.selectedOrder ? orderDetailPanel(ordersState.selectedOrder) : '';
  return `<div class="recipes-layout"><section class="card recipes-intro"><div><p class="card-kicker">Заказы</p><h2>Заказы клиентов</h2><p>Здесь можно создать заказ на основе сохранённой версии рецепта или индивидуальной формулы клиента.</p><p class="next-step">В этом разделе можно проверить готовность и явно подтвердить изготовление. Списание склада выполняется только локальным приложением после подтверждения.</p></div><div class="actions"><button class="primary-action" type="button" data-action="open-order-create">Создать заказ</button><button class="secondary-action" type="button" data-action="reload-orders">Обновить</button></div></section>${ordersMessage ? `<p class="page-message">${ordersMessage}</p>` : ''}${ordersError ? `<p class="page-message error-message">${ordersError}</p>` : ''}${orderFilterToolbar(items.length)}${workspace}${orderList(items)}</div>`;
}
function orderFilterToolbar(resultCount: number) { const f=ordersState.filters; return `<section class="card data-card catalog-browser"><p class="card-kicker">Рабочий список</p><h2>Найти заказ</h2><div class="catalog-toolbar"><label class="full-span">Поиск<input type="search" data-action="filter-orders-search" value="${escapeHtml(f.search)}" placeholder="Продукт, клиент, рецепт, тара или заметки" /></label><label>Статус<select data-action="filter-orders-status"><option value="active" ${f.status==='active'?'selected':''}>Активные</option><option value="cancelled" ${f.status==='cancelled'?'selected':''}>Отменённые</option><option value="archived" ${f.status==='archived'?'selected':''}>Архив</option><option value="all" ${f.status==='all'?'selected':''}>Все</option></select></label></div><div class="catalog-summary"><span>Показаны заказы: ${resultCount} из ${ordersState.items.length}</span><button class="secondary-action compact" type="button" data-action="reset-order-filters">Сбросить фильтры</button></div></section>`; }
function orderList(items: Order[]) { if (ordersState.items.length===0) return `<section class="card empty-card"><h2>Заказов пока нет</h2><p>Заказов пока нет. Создайте первый заказ на основе рецепта или индивидуальной формулы клиента.</p><button class="primary-action" type="button" data-action="open-order-create">Создать заказ</button></section>`; if (items.length===0) return `<section class="card empty-card"><h2>Заказы не найдены</h2><p>Измените поиск или статус, чтобы снова увидеть рабочий список.</p><button class="secondary-action" type="button" data-action="reset-order-filters">Сбросить фильтры</button></section>`; return `<section class="card data-card"><p class="card-kicker">Список</p><h2>Рабочие заказы</h2><div class="table-wrap"><table class="compact-catalog-table"><thead><tr><th>Продукт</th><th>Клиент</th><th>Основа</th><th>Партия</th><th>Тара</th><th>Статус</th><th>Дата/цена</th><th>Действия</th></tr></thead><tbody>${items.map((o)=>`<tr class="${ordersState.selectedOrder?.id===o.id?'catalog-row-selected':''} ${!o.is_active||o.status==='archived'?'archived-row':''}"><td><strong>${escapeHtml(o.product_name)}</strong><small>${escapeHtml(o.notes || 'Без заметок')}</small></td><td>${escapeHtml(orderClientName(o.client_id))}</td><td>${orderSourceLabel(o)}</td><td>${escapeHtml(o.target_batch_size_value)} ${unitLabel(o.target_batch_size_unit)}</td><td>${orderPackagingLabel(o)}</td><td><span class="pill ${orderStatusPill(o)}">${orderStatusLabel(o.status)}</span></td><td>${o.planned_production_at ? `План: ${formatDate(o.planned_production_at)}` : 'План не указан'}<small>${o.sale_price ? `Цена: ${escapeHtml(o.sale_price)} ₽` : 'Цена не указана'}</small></td><td><div class="row-actions"><button class="secondary-action compact" type="button" data-action="open-order" data-id="${o.id}">Открыть</button>${orderLifecycleButtons(o)}</div></td></tr>`).join('')}</tbody></table></div><p class="next-step">Изготовление запускается только из карточки заказа после проверки готовности и отдельного подтверждения.</p></section>`; }
function orderLifecycleButtons(o: Order) { if (!o.is_active || o.status==='archived') return ''; if (o.status==='cancelled') return `<button class="secondary-action compact danger-action" type="button" data-action="archive-order" data-id="${o.id}">Архивировать</button>`; return `<button class="secondary-action compact danger-action" type="button" data-action="cancel-order" data-id="${o.id}">Отменить заказ</button><button class="secondary-action compact danger-action" type="button" data-action="archive-order" data-id="${o.id}">Архивировать</button>`; }
function orderFormPanel() { const f=ordersState.form; const isEdit=ordersState.formMode==='edit'; const selected=ordersState.selectedOrder; const blocked=isEdit && selected ? (selected.status==='cancelled' || selected.status==='archived' || !selected.is_active) : false; const activeClients=ordersState.clients.filter(c=>c.is_active); const activeVersions=ordersState.versions.filter(v=>v.status!=='archived'); const clientRecipeOptions=ordersState.clientRecipes.filter(r=>r.is_active && (!f.client_id || String(r.client_id)===f.client_id)); const noClients=activeClients.length===0; const noSources=activeVersions.length===0 && ordersState.clientRecipes.filter(r=>r.is_active).length===0; if (blocked) return `<section class="card form-card"><h2>${selected?.status==='cancelled'?'Отменённый заказ нельзя редактировать.':'Архивный заказ нельзя редактировать.'}</h2><p class="next-step">Карточка остаётся в истории. Можно закрыть форму и создать новый заказ при необходимости.</p><button class="secondary-action" type="button" data-action="close-order-form">Закрыть</button></section>`; return `<section class="card form-card" data-section="order-form"><p class="card-kicker">${isEdit?'Редактирование':'Создание'}</p><h2>${isEdit?'Изменить заказ':'Создать заказ'}</h2><form data-form="order" class="ingredient-form"><div class="form-grid"><label>Клиент<select name="client_id" required ${noClients?'disabled':''}><option value="">Выберите клиента</option>${activeClients.map(c=>`<option value="${c.id}" ${f.client_id===String(c.id)?'selected':''}>${escapeHtml(c.full_name)}</option>`).join('')}</select></label><label>Основа заказа<select name="source_type" data-action="select-order-source-type"><option value="recipe_version" ${f.source_type==='recipe_version'?'selected':''}>Базовая версия рецепта</option><option value="client_recipe" ${f.source_type==='client_recipe'?'selected':''}>Индивидуальная формула клиента</option></select></label>${f.source_type==='recipe_version'?`<label class="full-span">Версия рецепта<select name="recipe_version_id" required ${activeVersions.length===0?'disabled':''}><option value="">Выберите версию</option>${activeVersions.map(v=>`<option value="${v.id}" ${f.recipe_version_id===String(v.id)?'selected':''}>${escapeHtml(orderVersionName(v))}</option>`).join('')}</select></label>`:`<label class="full-span">Индивидуальная формула<select name="client_recipe_id" required ${clientRecipeOptions.length===0?'disabled':''}><option value="">Выберите индивидуальную формулу</option>${clientRecipeOptions.map(r=>`<option value="${r.id}" ${f.client_recipe_id===String(r.id)?'selected':''}>${escapeHtml(r.title)} · ${escapeHtml(orderClientName(r.client_id))}</option>`).join('')}</select><small>${f.client_id?'Показаны формулы выбранного клиента.':'Выберите клиента, чтобы сузить список формул.'}</small></label>`}<label>Название продукта<input name="product_name" required maxlength="180" value="${escapeHtml(f.product_name)}" placeholder="Например, Крем дневной 50 мл" /></label><label>Размер партии<input name="target_batch_size_value" required inputmode="decimal" value="${escapeHtml(f.target_batch_size_value)}" placeholder="Например, 50" /></label><label>Единица<select name="target_batch_size_unit">${['g','ml','pcs'].map(u=>`<option value="${u}" ${f.target_batch_size_unit===u?'selected':''}>${unitLabel(u)}</option>`).join('')}</select></label><label>Тара<select name="packaging_item_id"><option value="">Без выбранной тары</option>${ordersState.packagingItems.filter(p=>p.is_active).map(p=>`<option value="${p.id}" ${f.packaging_item_id===String(p.id)?'selected':''}>${escapeHtml(p.name)}</option>`).join('')}</select></label><label>Количество тары<input name="packaging_quantity" inputmode="decimal" value="${escapeHtml(f.packaging_quantity)}" placeholder="Например, 1" /></label><label>Цена продажи<input name="sale_price" inputmode="decimal" value="${escapeHtml(f.sale_price)}" placeholder="Например, 2500" /></label><label>Дата заказа<input name="ordered_at" type="date" value="${escapeHtml(f.ordered_at)}" /></label><label>Плановая дата производства<input name="planned_production_at" type="date" value="${escapeHtml(f.planned_production_at)}" /></label><label class="full-span">Заметки<textarea name="notes" rows="3" maxlength="1600">${escapeHtml(f.notes)}</textarea></label></div>${noClients?'<p class="empty-hint">Сначала добавьте клиента, чтобы создать заказ.</p>':''}${noSources?'<p class="empty-hint">Для заказа нужен базовый рецепт или индивидуальная формула клиента.</p>':''}<p class="next-step">Форма не отправляет статус, дату производства или дату выдачи. Производство запускается отдельно из карточки заказа после проверки готовности.</p><div class="actions"><button class="primary-action" type="submit" ${noClients||noSources?'disabled':''}>${isEdit?'Сохранить изменения':'Создать заказ'}</button><button class="secondary-action" type="button" data-action="close-order-form">Закрыть форму</button></div></form></section>`; }
function orderDetailPanel(o: Order) {
  const closed = orderProductionClosed(o);
  const readinessAction = closed
    ? '<p class="next-step">Закрытые, выданные или уже изготовленные заказы нельзя проверять к производству.</p>'
    : `<button class="primary-action" type="button" data-action="check-order-readiness" data-id="${o.id}" ${ordersState.readinessLoadingOrderId === o.id ? 'disabled' : ''}>${ordersState.readinessLoadingOrderId === o.id ? 'Проверяем…' : 'Проверить изготовление'}</button>`;
  return `<section class="card data-card"><div class="section-heading"><div><p class="card-kicker">Карточка заказа</p><h2>${escapeHtml(o.product_name)}</h2></div><button class="secondary-action" type="button" data-action="close-order-detail">Закрыть карточку</button></div><p><strong>Клиент:</strong> ${escapeHtml(orderClientName(o.client_id))}</p><p><strong>Основа:</strong> ${orderSourceLabel(o)}</p><p><strong>Партия:</strong> ${escapeHtml(o.target_batch_size_value)} ${unitLabel(o.target_batch_size_unit)}</p><p><strong>Тара:</strong> ${orderPackagingLabel(o)}</p><p><strong>Статус:</strong> ${orderStatusLabel(o.status)}</p><p><strong>Дата заказа:</strong> ${o.ordered_at?formatDate(o.ordered_at):'Не указана'} · <strong>План производства:</strong> ${o.planned_production_at?formatDate(o.planned_production_at):'Не указан'}</p><p><strong>Цена:</strong> ${o.sale_price?`${escapeHtml(o.sale_price)} ₽`:'Не указана'}</p><p><strong>Заметки:</strong><br>${escapeHtml(o.notes || 'Нет заметок')}</p>${o.status==='cancelled'?'<p class="next-step">Отменённый заказ нельзя редактировать.</p>':(!o.is_active||o.status==='archived')?'<p class="next-step">Архивный заказ нельзя редактировать.</p>':'<p class="next-step">Можно изменить только безопасные поля заказа. Производственные статусы здесь не меняются.</p>'}<div class="actions">${(o.status==='cancelled'||!o.is_active||o.status==='archived')?'':`<button class="secondary-action" type="button" data-action="edit-order" data-id="${o.id}">Изменить заказ</button>`}${readinessAction}${orderLifecycleButtons(o)}</div></section>${orderReadinessPanel(o)}${orderProductionPanel(o)}`;
}
function orderReadinessPanel(o: Order) {
  if (orderProductionClosed(o)) return `<section class="card data-card"><p class="card-kicker">Проверка изготовления</p><h2>Проверка больше не нужна</h2><p class="next-step">Заказ уже изготовлен или закрыт. Повторная проверка готовности недоступна: складские списания и история партии уже фиксируются через производство.</p></section>`;
  const result = ordersState.readinessByOrderId[o.id];
  if (ordersState.readinessLoadingOrderId === o.id) return `<section class="card data-card"><p class="card-kicker">Проверка изготовления</p><h2>Проверяем компоненты, партии и тару…</h2><p class="next-step">Это только проверка. Склад не списан, партии не зарезервированы, заказ не переведён в производство.</p></section>`;
  if (ordersState.readinessError && ordersState.selectedOrder?.id === o.id) return `<section class="card error-card"><p class="card-kicker">Проверка изготовления</p><h2>Не удалось проверить готовность производства.</h2><p>${escapeHtml(ordersState.readinessError)}</p><p class="next-step">Проверьте, что локальное приложение запущено, и повторите проверку.</p><button class="primary-action" type="button" data-action="retry-order-readiness" data-id="${o.id}">Повторить проверку</button></section>`;
  if (!result) return `<section class="card data-card"><p class="card-kicker">Проверка изготовления</p><h2>Готовность к производству</h2><p>Проверка изготовления ещё не выполнялась. Нажмите «Проверить изготовление», чтобы увидеть, хватает ли компонентов и тары.</p><p class="next-step">Это только проверка. Склад не списан, партии не зарезервированы, заказ не переведён в производство.</p></section>`;
  return `<section class="card data-card readiness-result"><div class="section-heading"><div><p class="card-kicker">Проверка изготовления</p><h2>${readinessStatusLabel(result.status)}</h2></div><span class="pill ${readinessStatusPill(result.status)}">${result.can_produce ? 'Склад выглядит достаточным' : 'Есть препятствия'}</span></div><p class="next-step">Проверка ничего не списывает со склада и не меняет статус заказа.</p><p class="next-step">Это только проверка. Склад не списан, партии не зарезервированы, заказ не переведён в производство.</p>${result.generated_at ? `<p><strong>Проверено:</strong> ${formatDateTime(result.generated_at)}</p>` : ''}<p>${readinessNextAction(result.status)}</p>${readinessIssuesSection('Что мешает изготовлению', result.blocking_issues, 'Критичных препятствий нет.')}${readinessIssuesSection('На что обратить внимание', result.warnings, 'Предупреждений нет.')}${readinessIngredientsTable(result.ingredients)}${readinessPackagingTable(result.packaging)}${readinessEstimates(result)}</section>`;
}

function orderProductionPanel(o: Order) {
  const batch = ordersState.productionByOrderId[o.id];
  if (batch) return productionSuccessPanel(batch);
  if (orderProductionClosed(o)) { const canOpen=o.status==='produced'||o.status==='delivered'; return `<section class="card data-card"><p class="card-kicker">Изготовление</p><h2>Изготовление недоступно</h2><p class="next-step">Для закрытых, выданных, архивных или уже изготовленных заказов действие изготовления не показывается.</p>${ordersState.productionError && ordersState.selectedOrder?.id===o.id ? `<p class="page-message error-message">${escapeHtml(ordersState.productionError)}</p>` : ''}${canOpen ? `<div class="actions"><button class="secondary-action" type="button" data-action="open-order-production-batch" data-id="${o.id}" ${ordersState.productionLoadingOrderId===o.id?'disabled':''}>${ordersState.productionLoadingOrderId===o.id?'Открываем…':'Открыть партию'}</button></div>` : ''}</section>`; }
  const readiness = ordersState.readinessByOrderId[o.id];
  if (!readiness) return `<section class="card data-card"><p class="card-kicker">Изготовление</p><h2>Подтверждение изготовления</h2><p class="next-step">Сначала проверьте готовность изготовления.</p></section>`;
  if (!readiness.can_produce || readiness.status === 'blocked') return `<section class="card data-card"><p class="card-kicker">Изготовление</p><h2>Подтверждение изготовления</h2><p class="next-step">Производство недоступно, пока есть блокирующие замечания.</p></section>`;
  const notes = ordersState.productionNotesByOrderId[o.id] ?? '';
  const confirming = ordersState.productionConfirmingOrderId === o.id;
  const loading = ordersState.productionLoadingOrderId === o.id;
  return `<section class="card data-card"><p class="card-kicker">Изготовление</p><h2>Подтверждение изготовления</h2>${readiness.status === 'warning' ? '<p class="next-step">Есть предупреждения. Проверьте их перед подтверждением изготовления.</p>' : '<p class="next-step">Проверка готовности разрешает изготовление. Подтвердите действие только после проверки списка компонентов и тары.</p>'}${ordersState.productionError && ordersState.selectedOrder?.id === o.id ? `<p class="page-message error-message">${escapeHtml(ordersState.productionError)}</p>` : ''}${confirming ? `<div class="readiness-block"><h3>Подтвердите изготовление</h3><p>После подтверждения система создаст производственную партию, спишет компоненты и тару со склада и переведёт заказ в статус «Изготовлен».</p><p class="next-step">Это действие нельзя отменить в MVP.</p><label class="full-span">Заметка к партии<textarea data-action="production-notes" data-id="${o.id}" rows="3" maxlength="1600" placeholder="Необязательно">${escapeHtml(notes)}</textarea></label><div class="actions"><button class="primary-action" type="button" data-action="confirm-production" data-id="${o.id}" ${loading ? 'disabled' : ''}>${loading ? 'Изготавливаем…' : 'Подтвердить изготовление'}</button><button class="secondary-action" type="button" data-action="cancel-production-confirmation" data-id="${o.id}" ${loading ? 'disabled' : ''}>Отмена</button></div></div>` : `<div class="actions"><button class="primary-action" type="button" data-action="open-production-confirmation" data-id="${o.id}">Изготовить</button></div>`}</section>`;
}
function productionSuccessPanel(batch: ProductionBatchDetailResponse) { return `<section class="card data-card readiness-result"><div class="section-heading"><div><p class="card-kicker">Изготовление</p><h2>Заказ изготовлен</h2></div><span class="pill success">Партия №${batch.id}</span></div><div class="readiness-grid"><div><strong>Дата изготовления</strong><p>${formatDateTime(batch.produced_at)}</p></div><div><strong>Размер партии</strong><p>${quantityLabel(batch.final_batch_value, batch.final_batch_unit)}</p></div><div><strong>Итоговая себестоимость</strong><p>${moneyOrMissing(batch.total_cost)}</p></div><div><strong>Компоненты</strong><p>${moneyOrMissing(batch.component_cost)}</p></div><div><strong>Тара</strong><p>${moneyOrMissing(batch.packaging_cost)}</p></div><div><strong>Налог</strong><p>${moneyOrMissing(batch.tax)}</p></div><div><strong>Маржа</strong><p>${moneyOrMissing(batch.margin)}</p></div><div><strong>Списания компонентов</strong><p>${batch.ingredients.length}</p></div><div><strong>Списания тары</strong><p>${batch.packaging.length}</p></div></div>${batch.notes ? `<p><strong>Заметка:</strong><br>${escapeHtml(batch.notes)}</p>` : ''}<p class="next-step">Списание уже выполнено через складские движения. Исторические данные партии сохранены.</p></section>`; }
function orderProductionClosed(o: Order) { return !o.is_active || ['cancelled', 'archived', 'delivered', 'produced'].includes(o.status); }

function readinessStatusLabel(status: ProductionReadinessStatus) { return status === 'ready' ? 'Можно изготовить' : status === 'warning' ? 'Можно изготовить, но есть предупреждения' : 'Пока нельзя изготовить'; }
function readinessStatusPill(status: ProductionReadinessStatus) { return status === 'ready' ? 'success' : status === 'warning' ? 'warning' : 'danger'; }
function readinessNextAction(status: ProductionReadinessStatus) { return status === 'blocked' ? 'Сначала устраните препятствия: добавьте недостающие партии, тару или исправьте данные рецепта.' : status === 'warning' ? 'Проверьте предупреждения перед производством. Если всё верно, ниже появится кнопка явного подтверждения изготовления.' : 'Компонентов и тары хватает. Если всё верно, ниже появится кнопка явного подтверждения изготовления.'; }
function readinessIssuesSection(title: string, issues: ProductionReadinessIssue[], empty: string) { return `<div class="readiness-block"><h3>${title}</h3>${issues.length ? `<ul>${issues.map((issue) => `<li><span class="pill ${issue.severity === 'blocking' ? 'danger' : issue.severity === 'warning' ? 'warning' : 'info'}">${readinessSeverityLabel(issue.severity)}</span> ${escapeHtml(issue.message)}</li>`).join('')}</ul>` : `<p class="empty-hint">${empty}</p>`}</div>`; }
function readinessSeverityLabel(severity: ProductionReadinessIssueSeverity) { return severity === 'blocking' ? 'Стоп' : severity === 'warning' ? 'Важно' : 'Инфо'; }
function readinessIngredientsTable(lines: ProductionReadinessIngredientLine[]) { if (!lines.length) return `<div class="readiness-block"><h3>Компоненты</h3><p class="empty-hint">Компоненты не найдены в ответе проверки. Проверьте рецепт заказа.</p></div>`; return `<div class="readiness-block"><h3>Компоненты</h3><div class="table-wrap"><table class="compact-catalog-table"><thead><tr><th>Компонент</th><th>Нужно</th><th>Доступно</th><th>Не хватает</th><th>Статус</th><th>Выбранные партии</th></tr></thead><tbody>${lines.map((line) => `<tr><td><strong>${escapeHtml(line.ingredient_name)}</strong>${line.warnings.length ? `<small>${line.warnings.map((w)=>escapeHtml(w.message)).join('<br>')}</small>` : ''}</td><td>${quantityLabel(line.required_quantity, line.required_unit)}</td><td>${quantityLabel(line.available_quantity, line.required_unit)}</td><td>${missingQuantityLabel(line.missing_quantity, line.required_unit)}</td><td><span class="pill ${line.can_fulfill ? 'success' : 'danger'}">${line.can_fulfill ? 'Хватает' : 'Не хватает'}</span></td><td>${readinessLots(line.selected_lots)}</td></tr>`).join('')}</tbody></table></div></div>`; }
function readinessLots(lots: ProductionReadinessLotSelection[]) { if (!lots.length) return '<span class="empty-hint">Партии не подобраны.</span>'; return lots.map((lot) => `<div><strong>${escapeHtml(lot.lot_code || 'Без номера')}</strong> · ${quantityLabel(lot.selected_quantity, lot.unit)} · ${lot.expires_at ? `до ${formatDate(lot.expires_at)}` : 'срок не указан'} ${lot.is_expired ? '<span class="pill danger">Просрочена</span>' : lot.expires_soon ? '<span class="pill warning">Скоро истекает</span>' : ''}</div>`).join(''); }
function readinessPackagingTable(lines: ProductionReadinessPackagingLine[]) { return `<div class="readiness-block"><h3>Тара</h3>${lines.length ? `<div class="table-wrap"><table class="compact-catalog-table"><thead><tr><th>Тара</th><th>Нужно</th><th>Доступно</th><th>Не хватает</th><th>Статус</th></tr></thead><tbody>${lines.map((line) => `<tr><td><strong>${escapeHtml(line.name)}</strong></td><td>${escapeHtml(line.required_quantity)}</td><td>${escapeHtml(line.available_quantity)}</td><td>${escapeHtml(line.missing_quantity ?? '0')}</td><td><span class="pill ${line.can_fulfill ? 'success' : 'danger'}">${line.can_fulfill ? 'Хватает' : 'Не хватает'}</span></td></tr>`).join('')}</tbody></table></div>` : '<p class="empty-hint">Тара не выбрана или проверка тары не требуется.</p>'}</div>`; }
function readinessEstimates(result: ProductionReadinessResponse) { return `<div class="readiness-block"><h3>Предварительная экономика</h3><div class="readiness-grid"><div><strong>Ориентировочная себестоимость</strong><p>${moneyOrMissing(result.estimated_cost)}</p></div><div><strong>Налог</strong><p>${moneyOrMissing(result.estimated_tax)}</p></div><div><strong>Маржа</strong><p>${moneyOrMissing(result.estimated_margin)}</p></div></div><p class="next-step">Если налог или маржа не рассчитаны, интерфейс не подставляет налоговую ставку сам.</p></div>`; }
function quantityLabel(value: string, unit: string) { return `${escapeHtml(value)} ${unitLabel(unit)}`; }
function missingQuantityLabel(value: string | null, unit: string) { return value === null || value === '' ? `0 ${unitLabel(unit)}` : quantityLabel(value, unit); }
function moneyOrMissing(value: string | null) { return value === null || value === '' ? 'Не рассчитано' : `${escapeHtml(value)} ₽`; }
function orderStatusLabel(status: string) { return ({new:'Новый',waiting_for_materials:'Ждёт компонентов',ready_to_produce:'Готов к производству',in_progress:'В производстве',produced:'Произведён',delivered:'Выдан',cancelled:'Отменён',archived:'В архиве'} as Record<string,string>)[status] ?? 'Неизвестный статус'; }
function orderStatusPill(o: Order) { if (o.status==='cancelled') return 'danger'; if (!o.is_active || o.status==='archived') return 'muted'; if (['waiting_for_materials','in_progress'].includes(o.status)) return 'warning'; return 'success'; }
function orderClientName(id:number){ return ordersState.clients.find(c=>c.id===id)?.full_name ?? `Клиент ${id}`; }
function orderVersionName(v: RecipeVersion){ const template=ordersState.templates.find(t=>t.id===v.recipe_template_id); return `${template?.name ?? 'Базовый рецепт'} · версия №${v.version_number} · ${v.title || 'Без заголовка'}`; }
function orderSourceLabel(o: Order){ if (o.client_recipe_id) return `Индивидуальная формула: ${escapeHtml(ordersState.clientRecipes.find(r=>r.id===o.client_recipe_id)?.title ?? `№${o.client_recipe_id}`)}`; if (o.recipe_version_id) { const v=ordersState.versions.find(v=>v.id===o.recipe_version_id); return `Базовая версия рецепта: ${escapeHtml(v ? orderVersionName(v) : `№${o.recipe_version_id}`)}`; } return 'Источник не указан'; }
function orderPackagingLabel(o: Order){ const p=o.packaging_item_id ? ordersState.packagingItems.find(p=>p.id===o.packaging_item_id) : null; if (!p) return o.packaging_quantity ? `${escapeHtml(o.packaging_quantity)} · тара не выбрана` : 'Не выбрана'; return `${escapeHtml(p.name)}${o.packaging_quantity ? ` · ${escapeHtml(o.packaging_quantity)} ${unitLabel(p.unit)}` : ''}`; }
function filteredOrders(){ const search=ordersState.filters.search.trim().toLocaleLowerCase('ru-RU'); return ordersState.items.filter(o=>{ if (ordersState.filters.status==='active' && (o.status==='cancelled'||o.status==='archived'||!o.is_active)) return false; if (ordersState.filters.status==='cancelled' && o.status!=='cancelled') return false; if (ordersState.filters.status==='archived' && o.status!=='archived' && o.is_active) return false; if (!search) return true; return [o.product_name, o.notes, orderClientName(o.client_id), orderSourceLabel(o), orderPackagingLabel(o), orderStatusLabel(o.status)].join(' ').toLocaleLowerCase('ru-RU').includes(search); }); }

function saveOrderFormDraftFromDom() { const form = document.querySelector<HTMLFormElement>('[data-form="order"]'); if (!form) return; const data = new FormData(form); ordersState.form = { ...ordersState.form, client_id: String(data.get('client_id') || ''), source_type: String(data.get('source_type') || ordersState.form.source_type) as OrderSourceType, recipe_version_id: String(data.get('recipe_version_id') || ''), client_recipe_id: String(data.get('client_recipe_id') || ''), product_name: String(data.get('product_name') || ''), target_batch_size_value: String(data.get('target_batch_size_value') || ''), target_batch_size_unit: String(data.get('target_batch_size_unit') || 'g'), packaging_item_id: String(data.get('packaging_item_id') || ''), packaging_quantity: String(data.get('packaging_quantity') || ''), sale_price: String(data.get('sale_price') || ''), ordered_at: String(data.get('ordered_at') || ''), planned_production_at: String(data.get('planned_production_at') || ''), notes: String(data.get('notes') || '') }; }
function orderPayloadFromForm(form: HTMLFormElement): OrderPayload | string { const data=new FormData(form); const packagingItem=String(data.get('packaging_item_id') || ''); const packagingQty=String(data.get('packaging_quantity') || '').trim().replace(',','.'); if (packagingQty && !packagingItem) return 'Если указано количество тары, выберите саму тару.'; const sourceType=String(data.get('source_type')) as OrderSourceType; return { client_id: Number(data.get('client_id')) || null, recipe_version_id: sourceType==='recipe_version' ? Number(data.get('recipe_version_id')) || null : null, client_recipe_id: sourceType==='client_recipe' ? Number(data.get('client_recipe_id')) || null : null, product_name: String(data.get('product_name') || '').trim(), target_batch_size_value: String(data.get('target_batch_size_value') || '').trim().replace(',','.'), target_batch_size_unit: String(data.get('target_batch_size_unit') || 'g'), packaging_item_id: packagingItem ? Number(packagingItem) : null, packaging_quantity: packagingQty || null, sale_price: String(data.get('sale_price') || '').trim().replace(',','.') || null, ordered_at: String(data.get('ordered_at') || '') || null, planned_production_at: String(data.get('planned_production_at') || '') || null, notes: String(data.get('notes') || '') }; }
function formFromOrder(o: Order): OrderFormState { return { id:o.id, client_id:String(o.client_id), source_type:o.client_recipe_id?'client_recipe':'recipe_version', recipe_version_id:o.recipe_version_id?String(o.recipe_version_id):'', client_recipe_id:o.client_recipe_id?String(o.client_recipe_id):'', product_name:o.product_name, target_batch_size_value:o.target_batch_size_value, target_batch_size_unit:o.target_batch_size_unit, packaging_item_id:o.packaging_item_id?String(o.packaging_item_id):'', packaging_quantity:o.packaging_quantity ?? '', sale_price:o.sale_price ?? '', ordered_at:o.ordered_at ?? '', planned_production_at:o.planned_production_at ?? '', notes:o.notes }; }
function loadOrders(force=false){ if(!force && (ordersStatus==='loading'||ordersStatus==='ready')) return; ordersStatus='loading'; ordersError=''; render(); Promise.all([getOrders(true), getClients(true), getRecipeTemplates(), getClientRecipes(true), getPackagingItems()]).then(async ([orders, clients, templates, clientRecipes, packaging])=>{ const versionLists=await Promise.all(templates.recipe_templates.map(t=>getRecipeVersions(t.id).catch(()=>({recipe_versions:[]})))); ordersState.items=orders.orders; ordersState.clients=clients.clients; ordersState.templates=templates.recipe_templates; ordersState.versions=versionLists.flatMap(v=>v.recipe_versions); ordersState.clientRecipes=clientRecipes.client_recipes; ordersState.packagingItems=packaging.packaging_items; ordersStatus='ready'; render(); }).catch(()=>{ ordersStatus='error'; ordersError='Не удалось загрузить заказы. Проверьте локальное приложение и попробуйте ещё раз.'; render(); }); }
function openOrderCreate(){ ordersState.formMode='create'; ordersState.form=emptyOrderForm(); ordersState.showForm=true; ordersState.selectedOrder=null; ordersMessage=''; ordersError=''; render(); }
function openOrder(id:number){ const fallback=ordersState.items.find(i=>i.id===id) ?? null; ordersState.selectedOrder=fallback; ordersState.showForm=false; ordersMessage=''; ordersError=''; render(); getOrder(id).then((order)=>{ ordersState.selectedOrder=order; render(); }).catch(()=>{ ordersError='Не удалось открыть карточку заказа. Попробуйте обновить список.'; render(); }); }
function checkOrderReadiness(id:number){ const order=ordersState.selectedOrder?.id===id ? ordersState.selectedOrder : ordersState.items.find(i=>i.id===id) ?? null; if(!order || orderProductionClosed(order)) return; ordersState.readinessLoadingOrderId=id; ordersState.readinessError=''; render(); checkOrderProductionReadiness(id).then((result)=>{ ordersState.readinessByOrderId[id]=result; ordersState.readinessLoadingOrderId=null; ordersState.readinessError=''; render(); }).catch((e)=>{ ordersState.readinessLoadingOrderId=null; const msg=e instanceof Error && e.message && e.message !== 'API request failed' ? e.message : ''; ordersState.readinessError=msg || 'Не удалось проверить готовность производства.'; render(); }); }

function openProductionConfirmation(id:number){ const order=ordersState.selectedOrder?.id===id ? ordersState.selectedOrder : ordersState.items.find(i=>i.id===id) ?? null; const readiness=ordersState.readinessByOrderId[id]; if(!order || orderProductionClosed(order) || !readiness?.can_produce) return; ordersState.productionConfirmingOrderId=id; ordersState.productionError=''; render(); }
function cancelProductionConfirmation(id:number){ if(ordersState.productionLoadingOrderId===id) return; if(ordersState.productionConfirmingOrderId===id) ordersState.productionConfirmingOrderId=null; render(); }
function confirmProduction(id:number){ const order=ordersState.selectedOrder?.id===id ? ordersState.selectedOrder : ordersState.items.find(i=>i.id===id) ?? null; const readiness=ordersState.readinessByOrderId[id]; if(!order || orderProductionClosed(order) || !readiness?.can_produce) return; ordersState.productionLoadingOrderId=id; ordersState.productionError=''; render(); produceOrder(id, ordersState.productionNotesByOrderId[id]).then((batch)=>{ ordersState.productionByOrderId[id]=batch; delete ordersState.readinessByOrderId[id]; ordersState.productionLoadingOrderId=null; ordersState.productionConfirmingOrderId=null; ordersState.productionError=''; ordersState.productionNotesByOrderId[id]=''; return Promise.all([getOrders(true), getOrder(id)]); }).then(([orders, updated])=>{ ordersState.items=orders.orders; ordersState.selectedOrder=updated; render(); }).catch((e)=>{ ordersState.productionLoadingOrderId=null; ordersState.productionError=humanProductionError(e); render(); }); }

function editOrder(id:number){ const o=ordersState.items.find(i=>i.id===id); if(!o) return; ordersState.selectedOrder=o; ordersState.formMode='edit'; ordersState.form=formFromOrder(o); ordersState.showForm=true; ordersMessage=''; ordersError=''; render(); }
function submitOrderForm(event: SubmitEvent){ event.preventDefault(); const form=event.currentTarget as HTMLFormElement; const payload=orderPayloadFromForm(form); if (typeof payload==='string') { ordersError=payload; render(); return; } const request=ordersState.formMode==='edit' && ordersState.form.id ? updateOrder(ordersState.form.id, payload) : createOrder(payload); request.then((saved)=>{ ordersMessage=ordersState.formMode==='edit'?'Заказ сохранён.':'Заказ создан.'; ordersError=''; ordersState.selectedOrder=saved; ordersState.showForm=false; return getOrders(true); }).then((response)=>{ ordersState.items=response.orders; render(); }).catch((e)=>{ ordersError=humanOrderError(e); render(); }); }
function cancelOrder(id:number){ if(!window.confirm('Отменить заказ? Заказ останется в истории, склад и производство не будут затронуты.')) return; cancelOrderRequest(id).then((saved)=>{ ordersMessage='Заказ отменён.'; ordersError=''; ordersState.selectedOrder=saved; return getOrders(true); }).then(r=>{ ordersState.items=r.orders; render(); }).catch((e)=>{ ordersError=humanOrderError(e); render(); }); }
function archiveOrder(id:number){ if(!window.confirm('Архивировать заказ? Заказ не будет удалён и останется в истории.')) return; archiveOrderRequest(id).then((saved)=>{ ordersMessage='Заказ архивирован.'; ordersError=''; ordersState.selectedOrder=saved; return getOrders(true); }).then(r=>{ ordersState.items=r.orders; render(); }).catch((e)=>{ ordersError=humanOrderError(e); render(); }); }
function humanProductionError(e: unknown) { const status = typeof e === 'object' && e && 'status' in e ? Number((e as { status?: number }).status) : 0; const detail = e instanceof Error && e.message && e.message !== 'API request failed' ? ` ${e.message}` : ''; if (status === 422) return `Не получилось подтвердить изготовление: не передано явное подтверждение.${detail}`; if (status === 409) return `Заказ нельзя изготовить сейчас. Возможно, изменились остатки или данные заказа. Проверьте готовность ещё раз.${detail}`; if (status === 404) return `Заказ не найден. Обновите список заказов.${detail}`; if (e instanceof TypeError) return 'Не удалось связаться с локальным API. Проверьте, что приложение запущено.'; return detail.trim() || 'Не получилось подтвердить изготовление. Проверьте готовность ещё раз.'; }
function humanOrderError(e: unknown){ const msg=e instanceof Error ? e.message : ''; if (msg.includes('extra fields')) return 'Форма содержит поле, которое нельзя отправлять для заказа. Обновите страницу и попробуйте ещё раз.'; if (msg.includes('cancelled') || msg.includes('archived')) return 'Этот заказ уже отменён или находится в архиве, его нельзя редактировать.'; if (msg.includes('packaging')) return 'Проверьте выбранную тару и её количество.'; if (msg.includes('client')) return 'Проверьте выбранного клиента и индивидуальную формулу.'; return 'Не удалось сохранить заказ. Проверьте обязательные поля и попробуйте ещё раз.'; }


function clientRecipesPage() {
  if (clientRecipesStatus === 'idle' || clientRecipesStatus === 'loading') return `<section class="card"><p class="card-kicker">Индивидуальные рецепты клиентов</p><h2>Загружаем индивидуальные рецепты клиентов…</h2><p>Получаем персональные формулы, клиентов и базовые рецепты из локального приложения.</p></section>`;
  if (clientRecipesStatus === 'error') return `<section class="card error-card"><p class="card-kicker">Индивидуальные рецепты клиентов</p><h2>Не удалось загрузить индивидуальные рецепты клиентов</h2><p>${clientRecipesError || 'Локальное приложение временно недоступно.'}</p><p class="next-step">Проверьте, что локальное приложение запущено, и попробуйте обновить раздел.</p><button class="primary-action" type="button" data-action="reload-client-recipes">Повторить загрузку</button></section>`;
  const workspace = clientRecipesState.showCreateForm ? clientRecipeForm() : clientRecipesState.selectedDetail || clientRecipesState.detailStatus === 'loading' ? clientRecipeDetailPanel() : '';
  const items = filteredClientRecipes();
  return `<div class="recipes-layout"><section class="card recipes-intro"><div><p class="card-kicker">Индивидуальные рецепты клиентов</p><h2>Индивидуальные рецепты клиентов</h2><p>Здесь хранятся отдельные формулы, которые были адаптированы под конкретного клиента.</p><p class="next-step">Сначала найдите персональную формулу в списке. Создание и карточка открываются только когда нужны, а базовые версии рецептов не меняются автоматически.</p></div><div class="actions"><button class="primary-action" type="button" data-action="open-client-recipe-create">Создать индивидуальный рецепт</button><button class="secondary-action" type="button" data-action="reload-client-recipes">Обновить</button></div></section>${clientRecipesMessage ? `<p class="page-message">${clientRecipesMessage}</p>` : ''}${clientRecipesError ? `<p class="page-message error-message">${clientRecipesError}</p>` : ''}${clientRecipeFilterToolbar(items.length)}${workspace}${clientRecipeList(items)}${!workspace ? clientRecipeCreateHelper() : ''}</div>`;
}

function clientRecipeFilterToolbar(resultCount: number) {
  const f = clientRecipesState.filters;
  const clientOptions = clientRecipesState.clients.map((client) => `<option value="${client.id}" ${f.clientId === String(client.id) ? 'selected' : ''}>${escapeHtml(`${client.full_name}${client.is_active ? '' : ' (архив)'}`)}</option>`).join('');
  const activeFilters = clientRecipeActiveFilterChips();
  return `<section class="card data-card catalog-browser"><p class="card-kicker">Рабочий список</p><h2>Найти индивидуальный рецепт</h2><div class="catalog-toolbar"><label class="full-span">Поиск<input type="search" data-action="filter-client-recipes-search" value="${escapeHtml(f.search)}" placeholder="Название, клиент, статус, персонализация, аллергии, предпочтения или заметки" /></label><label>Статус<select data-action="filter-client-recipes-status"><option value="active" ${f.status === 'active' ? 'selected' : ''}>Активные</option><option value="archived" ${f.status === 'archived' ? 'selected' : ''}>Архив</option><option value="all" ${f.status === 'all' ? 'selected' : ''}>Все</option></select></label><label>Клиент<select data-action="filter-client-recipes-client"><option value="" ${f.clientId === '' ? 'selected' : ''}>Все клиенты</option>${clientOptions}</select></label></div>${activeFilters ? `<div class="active-filter-row"><strong>Активные фильтры:</strong>${activeFilters}</div>` : ''}<div class="catalog-summary"><span>Показаны индивидуальные рецепты: ${resultCount} из ${clientRecipesState.items.length}</span><button class="secondary-action compact" type="button" data-action="reset-client-recipe-filters">Сбросить фильтры</button></div></section>`;
}

function clientRecipeForm() {
  const f = clientRecipesState.form;
  const activeClients = clientRecipesState.clients.filter((c) => c.is_active);
  const activeTemplates = clientRecipesState.templates.filter((t) => t.is_active);
  const noClients = activeClients.length === 0;
  const noTemplates = activeTemplates.length === 0;
  const versionHelper = clientRecipeVersionHelperText();
  return `<section class="card form-card" data-section="client-recipe-form"><p class="card-kicker">Создание</p><h2>Создать индивидуальный рецепт</h2><p class="next-step">Выберите клиента, базовый рецепт и сохранённую версию состава. После сохранения появится отдельная формула для этого клиента.</p><form data-form="client-recipe" class="ingredient-form"><div class="form-grid"><label>Клиент<select name="client_id" required ${noClients ? 'disabled' : ''}><option value="">Выберите клиента</option>${activeClients.map((c)=>`<option value="${c.id}" ${f.client_id===String(c.id)?'selected':''}>${escapeHtml(c.full_name)}</option>`).join('')}</select></label><label>Базовый рецепт<select name="recipe_template_id" data-action="select-client-recipe-template" required ${noTemplates ? 'disabled' : ''}><option value="">Выберите базовый рецепт</option>${activeTemplates.map((t)=>`<option value="${t.id}" ${f.recipe_template_id===String(t.id)?'selected':''}>${escapeHtml(t.name)}</option>`).join('')}</select></label><label>Сохранённая версия состава<select name="source_recipe_version_id" required ${!f.recipe_template_id || clientRecipesState.versionsStatus === 'loading' || clientRecipesState.versions.length === 0 ? 'disabled' : ''}><option value="">Выберите сохранённую версию</option>${clientRecipesState.versions.map((v)=>`<option value="${v.id}" ${f.source_recipe_version_id===String(v.id)?'selected':''}>Версия №${v.version_number} · ${versionStatusLabel(v.status)} · ${escapeHtml(v.title || 'Без заголовка')}</option>`).join('')}</select><small>${versionHelper}</small></label><label>Название индивидуального рецепта<input name="title" data-field="client-recipe-title" required maxlength="180" value="${escapeHtml(f.title)}" placeholder="Например, Крем для Анны: без отдушки" /></label><label>Размер партии<input name="target_batch_size_value" inputmode="decimal" value="${escapeHtml(f.target_batch_size_value)}" placeholder="Например, 50" /></label><label>Единица<select name="target_batch_size_unit">${['g','ml','pcs'].map((u)=>`<option value="${u}" ${f.target_batch_size_unit===u?'selected':''}>${unitLabel(u)}</option>`).join('')}</select></label><label class="full-span">Персонализация<textarea name="personalization_notes" rows="2" maxlength="1200" placeholder="Что меняется для этого клиента">${escapeHtml(f.personalization_notes)}</textarea></label><label class="full-span">Аллергии<textarea name="allergy_notes" rows="2" maxlength="1200">${escapeHtml(f.allergy_notes)}</textarea></label><label class="full-span">Предпочтения<textarea name="preference_notes" rows="2" maxlength="1200">${escapeHtml(f.preference_notes)}</textarea></label><label class="full-span">Противопоказания<textarea name="contraindication_notes" rows="2" maxlength="1200">${escapeHtml(f.contraindication_notes)}</textarea></label><label class="full-span">Заметки<textarea name="notes" rows="3" maxlength="1600">${escapeHtml(f.notes)}</textarea></label></div>${noClients ? '<p class="empty-hint">Сначала добавьте активного клиента в разделе «Клиенты».</p>' : ''}${noTemplates ? '<p class="empty-hint">Сначала создайте базовый рецепт в разделе «Рецепты».</p>' : ''}<p class="next-step">Будет создана отдельная копия состава для клиента. Базовый рецепт останется без изменений.</p><p class="next-step">После сохранения откроется карточка индивидуального рецепта. В ней будет отдельная копия состава для выбранного клиента.</p><div class="actions"><button class="primary-action" type="submit" ${noClients || noTemplates ? 'disabled' : ''}>Сохранить индивидуальный рецепт</button><button class="secondary-action" type="button" data-action="hide-client-recipe-create">Закрыть форму</button></div></form></section>`;
}

function clientRecipeList(items: ClientRecipe[]) { if (clientRecipesState.items.length === 0) return `<section class="card empty-card"><h2>Пока нет индивидуальных рецептов</h2><p>Пока нет индивидуальных рецептов. Создайте персональную формулу на основе сохранённой версии состава и карточки клиента.</p><p class="next-step">Если список клиентов или рецептов пустой, сначала заполните разделы «Клиенты» и «Рецепты».</p><button class="primary-action" type="button" data-action="open-client-recipe-create">Создать индивидуальный рецепт</button></section>`; if (items.length === 0) return `<section class="card empty-card"><h2>По этим фильтрам индивидуальные рецепты не найдены</h2><p>Измените поиск, статус или клиента, чтобы снова увидеть рабочий список.</p><button class="secondary-action" type="button" data-action="reset-client-recipe-filters">Сбросить фильтры</button></section>`; return `<section class="card data-card"><p class="card-kicker">Список</p><h2>${clientRecipeListTitle()}</h2><div class="table-wrap"><table class="compact-catalog-table"><thead><tr><th>Рецепт</th><th>Клиент</th><th>Партия</th><th>Важное</th><th>Статус</th><th>Действия</th></tr></thead><tbody>${items.map((r)=>{ const isOpen = clientRecipesState.selectedDetail?.client_recipe.id === r.id && !clientRecipesState.showCreateForm; const isArchived = !r.is_active || r.status === 'archived'; const action = isArchived ? ` <button class="secondary-action compact" type="button" data-action="restore-client-recipe" data-id="${r.id}">Вернуть из архива</button>` : ` <button class="secondary-action compact danger-action" type="button" data-action="archive-client-recipe" data-id="${r.id}">Архивировать</button>`; return `<tr class="${isOpen ? 'catalog-row-selected' : ''}"><td><strong>${escapeHtml(r.title)}</strong>${isOpen ? '<small><span class="pill warning">Открыто</span></small>' : ''}</td><td>${escapeHtml(clientRecipeClientName(r.client_id))}</td><td>${batchLabel(r.target_batch_size_value, r.target_batch_size_unit)}</td><td>${clientRecipeNotesSummary(r)}</td><td><span class="pill ${isArchived?'muted':'success'}">${isArchived?'Архив':'Активен'}</span></td><td><div class="row-actions"><button class="secondary-action compact" type="button" data-action="open-client-recipe-detail" data-id="${r.id}">Открыть</button>${action}</div></td></tr>`; }).join('')}</tbody></table></div><p class="next-step">Список показывает только краткое резюме. Полные заметки и копия состава открываются в карточке.</p></section>`; }

function clientRecipeDetailPanel() { if (clientRecipesState.detailStatus === 'loading') return `<section class="card" data-section="client-recipe-detail"><h2>Загружаем карточку…</h2><p>Получаем персональную формулу и копию состава.</p></section>`; const d = clientRecipesState.selectedDetail; if (!d) return ''; const r = d.client_recipe; const canEdit = r.is_active && r.status !== 'archived'; const isArchived = !r.is_active || r.status === 'archived'; return `<section class="card data-card" data-section="client-recipe-detail"><div class="section-heading"><div><p class="card-kicker">Карточка клиента</p><h2>${escapeHtml(r.title)}</h2></div><button class="secondary-action" type="button" data-action="close-client-recipe-detail">Закрыть карточку</button></div><p><strong>Клиент:</strong> ${escapeHtml(clientRecipeClientName(r.client_id))}</p><p><strong>Размер партии:</strong> ${batchLabel(r.target_batch_size_value, r.target_batch_size_unit)}</p><p><strong>Статус:</strong> ${r.is_active ? 'активен' : 'архив'}</p><div class="note-grid"><p><strong>Персонализация:</strong><br>${escapeHtml(r.personalization_notes || 'Не указана')}</p><p><strong>Аллергии:</strong><br>${escapeHtml(r.allergy_notes || 'Не указаны')}</p><p><strong>Предпочтения:</strong><br>${escapeHtml(r.preference_notes || 'Не указаны')}</p><p><strong>Противопоказания:</strong><br>${escapeHtml(r.contraindication_notes || 'Не указаны')}</p><p class="full-span"><strong>Заметки:</strong><br>${escapeHtml(r.notes || 'Нет заметок')}</p></div><p class="next-step">Состав скопирован из выбранной версии рецепта. Изменение базового рецепта не меняет эту персональную карточку автоматически.</p>${canEdit ? '<div class="actions"><button class="primary-action" type="button" data-action="open-client-recipe-composition-editor">Изменить состав</button></div>' : '<p class="next-step">Архивный индивидуальный рецепт нельзя изменять. Он остаётся в истории. Его можно вернуть в работу.</p>'}${isArchived ? `<div class="actions"><button class="primary-action" type="button" data-action="restore-client-recipe" data-id="${r.id}">Вернуть из архива</button></div>` : ''}${clientRecipeCompositionEditorPanel()}<h3>Копия состава</h3>${d.ingredients.length === 0 ? '<p>В этой карточке пока нет строк состава. Добавьте первый компонент в редакторе состава.</p>' : `<div class="table-wrap"><table><thead><tr><th>№</th><th>Фаза</th><th>Компонент</th><th>Количество</th><th>Заметки</th></tr></thead><tbody>${d.ingredients.slice().sort((a,b)=>a.position-b.position).map((line)=>`<tr><td>${line.position}</td><td>${escapeHtml(line.phase || 'Не указана')}</td><td>${escapeHtml(clientRecipeIngredientName(line.ingredient_id))}</td><td>${escapeHtml(line.amount_value)} ${unitLabel(line.amount_unit)}</td><td>${escapeHtml([line.personalization_note, line.notes].filter(Boolean).join(' · ') || 'Без заметок')}</td></tr>`).join('')}</tbody></table></div>`}</section>`; }

function clientRecipeCreateHelper() { return `<section class="card catalog-helper-card"><p class="card-kicker">Создание</p><h2>Нужна новая персональная формула?</h2><p>Форма создания открывается отдельно, чтобы список индивидуальных рецептов оставался на виду.</p><button class="primary-action" type="button" data-action="open-client-recipe-create">Создать индивидуальный рецепт</button><p class="next-step">Выберите клиента, базовый рецепт и сохранённую версию состава. Будет создана отдельная копия состава для клиента.</p></section>`; }

function clientsPage() {
  if (clientsStatus === 'idle' || clientsStatus === 'loading') return `<section class="card"><p class="card-kicker">Клиенты</p><h2>Загружаем клиентов…</h2><p>Получаем карточки клиентов из локального API.</p></section>`;
  if (clientsStatus === 'error') return `<section class="card error-card"><p class="card-kicker">Клиенты</p><h2>Не удалось загрузить клиентов</h2><p>${clientsError || 'Не удалось загрузить клиентов. Проверьте, что локальное приложение запущено.'}</p><p class="next-step">Проверьте, что локальное приложение запущено, и попробуйте обновить раздел.</p><button class="primary-action" type="button" data-action="reload-clients">Повторить загрузку</button></section>`;
  const workspace = clientsState.formMode === 'edit' || clientsState.showCreateForm ? clientForm() : '';
  return `<div class="catalog-layout"><section class="card catalog-intro"><div><p class="card-kicker">Клиенты</p><h2>Клиенты</h2><p>Карточки клиентов, пожелания, ограничения и заметки для индивидуальных рецептов.</p><p class="next-step">Сначала найдите клиента в списке. Создание и редактирование открываются только когда нужно.</p></div><div class="actions"><button class="primary-action" type="button" data-action="open-client-create">Создать клиента</button><button class="secondary-action" type="button" data-action="reload-clients">Обновить</button></div></section>${clientsMessage ? `<p class="page-message">${clientsMessage}</p>` : ''}${clientsError ? `<p class="page-message error-message">${clientsError}</p>` : ''}${clientFilterToolbar()}${workspace}${clientList()}${!workspace ? clientCreateHelper() : ''}</div>`;
}

function clientFilterToolbar() {
  const f = clientsState.filters;
  const activeFilters = clientActiveFilterChips();
  return `<section class="card data-card catalog-browser"><p class="card-kicker">Рабочий список</p><h2>Найти клиента</h2><div class="catalog-toolbar"><label class="full-span">Поиск<input type="search" data-action="filter-clients-search" value="${escapeHtml(f.search)}" placeholder="ФИО, телефон, email, заметки, аллергии или предпочтения" /></label><label>Статус<select data-action="filter-clients-status"><option value="active" ${f.status === 'active' ? 'selected' : ''}>Активные</option><option value="archived" ${f.status === 'archived' ? 'selected' : ''}>Архив</option><option value="all" ${f.status === 'all' ? 'selected' : ''}>Все</option></select></label></div>${activeFilters ? `<div class="active-filter-row"><strong>Активные фильтры:</strong>${activeFilters}</div>` : ''}<div class="catalog-summary"><span>Показаны клиенты: ${filteredClients().length} из ${clientsState.items.length}</span><button class="secondary-action compact" type="button" data-action="reset-client-filters">Сбросить фильтры</button></div></section>`;
}

function clientForm() {
  const form = clientsState.form;
  const isEdit = clientsState.formMode === 'edit';
  return `<section class="card form-card"><p class="card-kicker">${isEdit ? 'Редактирование' : 'Создание'}</p><h2>${isEdit ? 'Изменить карточку клиента' : 'Создать клиента'}</h2><form data-form="client" class="ingredient-form"><div class="form-grid"><label>ФИО клиента<input name="full_name" data-field="client-full-name" required maxlength="200" value="${escapeHtml(form.full_name)}" placeholder="Например, Анна Иванова" /></label><label>Телефон<input name="phone" maxlength="80" value="${escapeHtml(form.phone)}" placeholder="+7 ..." /></label><label>Email<input name="email" type="email" maxlength="160" value="${escapeHtml(form.email)}" placeholder="Необязательно" /></label><label>Дата рождения<input name="birthday" type="date" value="${escapeHtml(form.birthday ?? '')}" /></label><label class="full-span">Адрес<input name="address" maxlength="300" value="${escapeHtml(form.address)}" placeholder="Необязательно" /></label><label class="full-span">Особенности кожи<textarea name="skin_notes" rows="2" maxlength="1200" placeholder="Например, чувствительная кожа">${escapeHtml(form.skin_notes)}</textarea></label><label class="full-span">Аллергии<textarea name="allergy_notes" rows="2" maxlength="1200" placeholder="Что важно учитывать в составах">${escapeHtml(form.allergy_notes)}</textarea></label><label class="full-span">Предпочтения<textarea name="preference_notes" rows="2" maxlength="1200" placeholder="Текстуры, ароматы, упаковка">${escapeHtml(form.preference_notes)}</textarea></label><label class="full-span">Противопоказания<textarea name="contraindication_notes" rows="2" maxlength="1200" placeholder="Ограничения, которые нельзя забыть">${escapeHtml(form.contraindication_notes)}</textarea></label><label class="full-span">Заметки<textarea name="notes" rows="3" maxlength="1600" placeholder="Рабочие заметки по клиенту">${escapeHtml(form.notes)}</textarea></label></div><p class="next-step">Аллергии, предпочтения и противопоказания помогут позже безопасно создавать индивидуальные рецепты клиента.</p><div class="actions"><button class="primary-action" type="submit">${isEdit ? 'Сохранить карточку' : 'Создать клиента'}</button>${isEdit ? '<button class="secondary-action" type="button" data-action="cancel-client-edit">Закрыть редактирование</button>' : '<button class="secondary-action" type="button" data-action="hide-client-create">Вернуться к списку</button>'}</div></form>${isEdit ? clientWishesSection() + clientFeedbackSection() : ''}</section>`;
}


function clientWishesSection() {
  const state = clientCardState;
  const wishes = state.includeArchivedWishes ? state.wishes : state.wishes.filter((wish) => wish.is_active && wish.status !== 'archived');
  const loading = state.wishesStatus === 'loading';
  return `<section class="card data-card"><div class="section-heading"><div><p class="card-kicker">Что учесть дальше</p><h2>Пожелания клиента</h2></div><div class="actions"><button class="secondary-action" type="button" data-action="toggle-archived-client-wishes">${state.includeArchivedWishes ? 'Скрыть архивные' : 'Показать архивные'}</button><button class="primary-action" type="button" data-action="toggle-client-wish-form">Добавить пожелание</button></div></div><p>Здесь можно записать, что клиент просил учесть в следующий раз: текстуру, аромат, упаковку, ингредиенты или ограничения.</p>${state.wishError ? `<p class="page-message error-message">${escapeHtml(state.wishError)}</p>` : ''}${state.showWishForm ? clientWishForm() : ''}${loading ? '<p>Загружаем пожелания клиента…</p>' : wishes.length === 0 ? '<p class="empty-hint">Пожеланий пока нет. Добавьте первое пожелание, чтобы не потерять важные детали клиента.</p>' : `<div class="recipe-lines">${wishes.map(clientWishCard).join('')}</div>`}</section>`;
}

function clientWishForm() {
  const form = clientCardState.wishForm;
  return `<form data-form="client-wish" class="ingredient-form"><h3>Новое пожелание</h3><div class="form-grid"><label class="full-span">Кратко о пожелании<input name="title" required maxlength="180" value="${escapeHtml(form.title)}" placeholder="Например, более лёгкая текстура" /></label><label>Категория<select name="category">${clientWishCategoryOptions(form.category)}</select></label><label>Важность<select name="priority">${clientWishPriorityOptions(form.priority)}</select></label>${clientRecipeLinkSelect(form.client_recipe_id)}<label class="full-span">Подробности<textarea name="description" rows="3" maxlength="1600" placeholder="Что именно просил клиент, какие детали важно не забыть">${escapeHtml(form.description)}</textarea></label></div><div class="actions"><button class="primary-action" type="submit" ${clientCardState.savingWish ? 'disabled' : ''}>${clientCardState.savingWish ? 'Сохраняем…' : 'Сохранить пожелание'}</button><button class="secondary-action" type="button" data-action="close-client-wish-form">Закрыть форму</button></div></form>`;
}

function clientWishCard(wish: ClientWish) {
  const archived = !wish.is_active || wish.status === 'archived';
  return `<article class="recipe-line"><div class="section-heading"><div><h3>${escapeHtml(wish.title)}</h3><p><span class="pill ${archived ? 'muted' : wish.status === 'resolved' ? 'success' : wish.status === 'planned' ? 'warning' : 'info'}">${clientWishStatusLabel(wish.status)}</span> <span class="pill muted">${clientWishPriorityLabel(wish.priority)}</span> <span class="pill muted">${clientWishCategoryLabel(wish.category)}</span></p></div><small>${formatDateTime(wish.created_at)}</small></div>${wish.description ? `<p>${escapeHtml(wish.description)}</p>` : '<p class="empty-hint">Без подробного описания.</p>'}${wish.client_recipe_id ? `<p class="next-step">Связано с индивидуальным рецептом: ${escapeHtml(clientCardRecipeTitle(wish.client_recipe_id))}</p>` : ''}${archived ? '<p class="next-step">Архивное пожелание доступно только для просмотра.</p>' : `<div class="actions">${clientWishStatusActions(wish)}<button class="secondary-action danger-action" type="button" data-action="archive-client-wish" data-id="${wish.id}" ${clientCardState.archivingWishId === wish.id ? 'disabled' : ''}>${clientCardState.archivingWishId === wish.id ? 'Архивируем…' : 'Архивировать'}</button></div>`}</article>`;
}

function clientWishStatusActions(wish: ClientWish) {
  const disabled = clientCardState.changingWishId === wish.id ? 'disabled' : '';
  const actions: string[] = [];
  if (wish.status !== 'open') actions.push(`<button class="secondary-action compact" type="button" data-action="change-client-wish-status" data-id="${wish.id}" data-status="open" ${disabled}>Вернуть в открытые</button>`);
  if (wish.status !== 'planned') actions.push(`<button class="secondary-action compact" type="button" data-action="change-client-wish-status" data-id="${wish.id}" data-status="planned" ${disabled}>Запланировать</button>`);
  if (wish.status !== 'resolved') actions.push(`<button class="secondary-action compact" type="button" data-action="change-client-wish-status" data-id="${wish.id}" data-status="resolved" ${disabled}>Отметить учтённым</button>`);
  return actions.join('');
}

function clientFeedbackSection() {
  const state = clientCardState;
  return `<section class="card data-card"><div class="section-heading"><div><p class="card-kicker">История после выдачи продукта</p><h2>Обратная связь</h2></div><button class="primary-action" type="button" data-action="toggle-client-feedback-form">Добавить отзыв</button></div><p>Здесь хранится история отзывов клиента после использования продукта. Эти записи не редактируются, чтобы сохранить историю.</p>${state.feedbackError ? `<p class="page-message error-message">${escapeHtml(state.feedbackError)}</p>` : ''}${state.showFeedbackForm ? clientFeedbackForm() : ''}${state.feedbackStatus === 'loading' ? '<p>Загружаем обратную связь…</p>' : state.feedback.length === 0 ? '<p class="empty-hint">Обратной связи пока нет. Добавьте отзыв после выдачи продукта или разговора с клиентом.</p>' : `<div class="recipe-lines">${state.feedback.map(clientFeedbackCard).join('')}</div>`}</section>`;
}

function clientFeedbackForm() {
  const form = clientCardState.feedbackForm;
  return `<form data-form="client-feedback" class="ingredient-form"><h3>Новая обратная связь</h3><div class="form-grid"><label>Тип отзыва<select name="feedback_type">${clientFeedbackTypeOptions(form.feedback_type)}</select></label><label>Настроение<select name="sentiment">${clientFeedbackSentimentOptions(form.sentiment)}</select></label><label>Оценка<input name="rating" type="number" min="1" max="5" value="${escapeHtml(form.rating)}" placeholder="1–5" /></label><label>Дата отзыва<input name="occurred_at" type="date" value="${escapeHtml(form.occurred_at)}" /></label>${clientRecipeLinkSelect(form.client_recipe_id)}<label class="full-span">Текст отзыва<textarea name="text" required rows="3" maxlength="2000" placeholder="Что клиенту понравилось или не подошло">${escapeHtml(form.text)}</textarea></label><label class="full-span"><input name="follow_up_needed" type="checkbox" ${form.follow_up_needed ? 'checked' : ''} /> Нужно учесть в следующий раз</label><label class="full-span">Что учесть<textarea name="follow_up_note" rows="2" maxlength="1200" placeholder="Необязательно">${escapeHtml(form.follow_up_note)}</textarea></label></div><div class="actions"><button class="primary-action" type="submit" ${clientCardState.savingFeedback ? 'disabled' : ''}>${clientCardState.savingFeedback ? 'Сохраняем…' : 'Сохранить отзыв'}</button><button class="secondary-action" type="button" data-action="close-client-feedback-form">Закрыть форму</button></div></form>`;
}

function clientFeedbackCard(item: ClientFeedback) {
  return `<article class="recipe-line"><div class="section-heading"><div><h3>${clientFeedbackTypeLabel(item.feedback_type)} · ${clientFeedbackSentimentLabel(item.sentiment)}</h3><p>${item.rating ? `Оценка: ${item.rating}/5` : 'Оценка не указана'}</p></div><small>${formatDate(item.occurred_at || item.created_at)}</small></div><p>${escapeHtml(item.text)}</p>${item.follow_up_needed ? `<p class="next-step"><strong>Учесть в следующий раз:</strong> ${escapeHtml(item.follow_up_note || 'Да, без дополнительной заметки.')}</p>` : ''}${item.client_recipe_id ? `<p class="next-step">Связано с индивидуальным рецептом: ${escapeHtml(clientCardRecipeTitle(item.client_recipe_id))}</p>` : ''}</article>`;
}

function clientList() {
  const items = filteredClients();
  if (clientsState.items.length === 0) return `<section class="card empty-card"><h2>Пока нет клиентов</h2><p>Пока нет клиентов. Добавьте первого клиента, чтобы хранить пожелания, ограничения и заметки для будущих индивидуальных рецептов.</p><p class="next-step">Нажмите «Создать клиента», заполните ФИО и любые известные ограничения.</p><button class="primary-action" type="button" data-action="open-client-create">Создать клиента</button></section>`;
  if (items.length === 0) return `<section class="card empty-card"><h2>По этим фильтрам клиентов не найдено</h2><p>Измените поиск или статус, чтобы снова увидеть рабочий список.</p><button class="secondary-action" type="button" data-action="reset-client-filters">Сбросить фильтры</button></section>`;
  return `<section class="card data-card"><p class="card-kicker">Список</p><h2>${clientListTitle()}</h2><div class="table-wrap"><table class="compact-catalog-table"><thead><tr><th>Клиент</th><th>Контакты</th><th>Важное</th><th>Статус</th><th>Действия</th></tr></thead><tbody>${items.map((client) => { const isEditing = clientsState.formMode === 'edit' && clientsState.form.id === client.id; return `<tr class="${isEditing ? 'catalog-row-selected' : ''}"><td><strong>${escapeHtml(client.full_name)}</strong>${isEditing ? '<small><span class="pill warning">Редактируется</span></small>' : ''}<small>${client.birthday ? `Дата рождения: ${formatDate(client.birthday)}` : 'Дата рождения не указана'}</small></td><td>${client.phone ? escapeHtml(client.phone) : 'Телефон не указан'}<small>${client.email ? escapeHtml(client.email) : 'Email не указан'}</small></td><td>${clientNotesSummary(client)}</td><td><span class="pill ${client.is_active ? 'success' : 'muted'}">${client.is_active ? 'Активен' : 'Архив'}</span></td><td><div class="row-actions"><button class="secondary-action compact" type="button" data-action="start-client-edit" data-id="${client.id}">Изменить</button>${client.is_active ? `<button class="secondary-action compact danger-action" type="button" data-action="archive-client" data-id="${client.id}">Архивировать</button>` : ''}</div></td></tr>`; }).join('')}</tbody></table></div><p class="next-step">Длинные заметки остаются в карточке редактирования, чтобы список был компактным.</p></section>`;
}

function clientCreateHelper() {
  return `<section class="card empty-card"><h2>Нужно добавить нового клиента?</h2><p>Форма создания скрыта, чтобы рабочий список оставался на первом экране.</p><button class="secondary-action" type="button" data-action="open-client-create">Создать клиента</button></section>`;
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
  const filtered = filteredPackagingItems();
  const isEdit = packagingItemsState.formMode === 'edit';
  const isCreateActive = packagingItemsState.formMode === 'create' && packagingItemsState.showCreateForm;
  const activeWorkspace = isEdit ? `${packagingItemForm()}${packagingCatalogPanel()}` : isCreateActive ? packagingItemForm() : '';
  const secondaryWorkspace = isEdit ? '' : isCreateActive ? packagingCatalogPanel() : `${packagingItemForm()}${packagingCatalogPanel()}`;
  return `<div class="catalog-layout"><section class="card catalog-intro"><div><p class="card-kicker">Каталог тары</p><h2>Тара и расходники</h2><p>Сначала найдите тару по названию, группе, меткам, типу или статусу. Создание и редактирование доступны ниже, чтобы каталог оставался главным рабочим местом.</p><p class="next-step">Тип тары используется системой. Группа и метки — ваш способ организовать каталог для поиска.</p></div><div class="actions"><button class="secondary-action" type="button" data-action="reload-packaging-items">Обновить список</button><button class="primary-action" type="button" data-action="new-packaging-item">Создать тару</button></div></section>${packagingItemsMessage ? `<p class="page-message">${packagingItemsMessage}</p>` : ''}${packagingItemsError ? `<p class="page-message error-message">${packagingItemsError}</p>` : ''}${packagingCatalogToolbar(filtered.length)}${activeWorkspace}${packagingItemsList(filtered)}${secondaryWorkspace}</div>`;
}

function packagingItemForm() {
  const form = packagingItemsState.form;
  const isEdit = packagingItemsState.formMode === 'edit';
  if (!isEdit && !packagingItemsState.showCreateForm) return `<section class="card form-card collapsed-create-card"><div><p class="card-kicker">Создание</p><h2>Создать новую тару</h2><p>Форма создания скрыта, чтобы каталог тары оставался первым рабочим экраном.</p></div><button class="primary-action" type="button" data-action="new-packaging-item">Создать тару</button></section>`;
  return `<section class="card form-card" data-section="packaging-form"><p class="card-kicker">${isEdit ? 'Редактирование' : 'Создание'}</p><h2>${isEdit ? 'Изменить тару' : 'Добавить тару'}</h2><form data-form="packaging-item" class="ingredient-form"><div class="form-grid"><label>Название<input name="name" required maxlength="160" value="${escapeHtml(form.name)}" placeholder="Например, баночка 30 мл" /></label><label>Тип тары<select name="kind">${packagingKindOptions(form.kind)}</select></label><label>Единица учета<select name="unit">${packagingUnitOptions(form.unit)}</select></label><label>Объем<input name="capacity_value" inputmode="decimal" value="${escapeHtml(form.capacity_value ?? '')}" placeholder="Например, 30" /></label><label>Единица объема<select name="capacity_unit"><option value="" ${form.capacity_unit ? '' : 'selected'}>Не указана</option>${capacityUnitOptions(form.capacity_unit ?? '')}</select></label><label>Материал<input name="material" maxlength="120" value="${escapeHtml(form.material)}" placeholder="Стекло, пластик, бумага…" /></label><label>Поставщик<input name="supplier_hint" maxlength="160" value="${escapeHtml(form.supplier_hint)}" placeholder="Необязательно" /></label><label>Цена за единицу<input name="unit_cost" inputmode="decimal" value="${escapeHtml(form.unit_cost ?? '')}" placeholder="Например, 12.50" /></label><label class="full-span">Заметки<textarea name="notes" rows="3" maxlength="1200" placeholder="Короткие рабочие заметки о таре">${escapeHtml(form.notes)}</textarea></label></div><div class="actions"><button class="primary-action" type="submit">${isEdit ? 'Сохранить изменения' : 'Создать тару'}</button>${isEdit ? '<button class="secondary-action" type="button" data-action="cancel-packaging-edit">Закрыть редактирование</button>' : '<button class="secondary-action" type="button" data-action="hide-packaging-create-form">Вернуться к каталогу</button>'}</div><p class="next-step">Остатки, приход и списания не меняются в этой форме — для них будут отдельные складские операции.</p></form></section>`;
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

function packagingCatalogToolbar(resultCount: number) {
  const f = packagingItemsState.filters;
  const categoryOptionsHtml = [`<option value="" ${f.categoryId === '' ? 'selected' : ''}>Все группы</option>`, `<option value="none" ${f.categoryId === 'none' ? 'selected' : ''}>Без группы</option>`, ...packagingItemsState.catalogCategories.map((category) => `<option value="${category.id}" ${f.categoryId === category.id ? 'selected' : ''}>${escapeHtml(category.name)}</option>`)].join('');
  const availableTags = packagingItemsState.catalogTags.filter((tag) => !f.tagIds.includes(tag.id));
  const activeTagChips = f.tagIds.map((id) => packagingItemsState.catalogTags.find((tag) => tag.id === id)).filter((tag): tag is CatalogTag => Boolean(tag)).map((tag) => `<span class="tag-chip selected">${escapeHtml(tag.name)} <button type="button" data-action="remove-packaging-tag-filter" data-id="${tag.id}" aria-label="Убрать метку ${escapeHtml(tag.name)}">×</button></span>`).join('');
  const activeFilters = packagingActiveFilterChips();
  return `<section class="card data-card catalog-browser"><p class="card-kicker">Каталог тары</p><h2>Найти тару</h2><div class="catalog-toolbar"><label class="full-span">Поиск<input type="search" data-action="filter-packaging-search" value="${escapeHtml(f.search)}" placeholder="Название, поставщик, заметки, материал или тип тары" /></label><label>Группа<select data-action="filter-packaging-category">${categoryOptionsHtml}</select></label><label>Метки<select data-action="add-packaging-tag-filter"><option value="">Все метки</option>${availableTags.map((tag) => `<option value="${tag.id}">${escapeHtml(tag.name)}</option>`).join('')}</select></label><label>Тип тары<select data-action="filter-packaging-kind"><option value="" ${f.systemType === '' ? 'selected' : ''}>Все типы</option>${packagingKindValues().map((value) => `<option value="${value}" ${f.systemType === value ? 'selected' : ''}>${packagingKindLabel(value)}</option>`).join('')}</select></label><label>Статус<select data-action="filter-packaging-status"><option value="active" ${f.status === 'active' ? 'selected' : ''}>Активные</option><option value="archived" ${f.status === 'archived' ? 'selected' : ''}>Архив</option><option value="all" ${f.status === 'all' ? 'selected' : ''}>Все</option></select></label></div>${activeTagChips ? `<div class="active-filter-row"><strong>Метки:</strong>${activeTagChips}</div>` : ''}${activeFilters ? `<div class="active-filter-row"><strong>Активные фильтры:</strong>${activeFilters}</div>` : ''}<div class="catalog-summary"><span>Показана тара: ${resultCount} из ${packagingItemsState.items.length}</span><button class="secondary-action compact" type="button" data-action="reset-packaging-filters">Сбросить фильтры</button></div></section>`;
}

function packagingItemsList(items: PackagingItem[]) {
  if (packagingItemsState.items.length === 0) return `<section class="card empty-card"><h2>Тара пока не добавлена</h2><p>Создайте первую баночку, флакон или этикетку.</p><p class="next-step">Следующее действие: нажмите «Создать тару», заполните форму и сохраните карточку.</p></section>`;
  if (items.length === 0) return `<section class="card empty-card"><h2>По этим фильтрам тара не найдена.</h2><p>Попробуйте убрать часть условий поиска или вернуться к полному каталогу.</p><button class="secondary-action" type="button" data-action="reset-packaging-filters">Сбросить фильтры</button></section>`;
  return `<section class="card data-card"><p class="card-kicker">Найденная тара</p><h2>Тара и расходники</h2><div class="table-wrap"><table class="compact-catalog-table"><thead><tr><th>Название</th><th>Тип</th><th>Ед. / объем</th><th>Группа</th><th>Метки</th><th>Статус</th><th>Действия</th></tr></thead><tbody>${items.map((item) => { const isEditing = packagingItemsState.formMode === 'edit' && packagingItemsState.form.id === item.id; return `<tr class="${isEditing ? 'catalog-row-selected' : ''}"><td><strong>${escapeHtml(item.name)}</strong>${isEditing ? '<small><span class="pill warning">Редактируется</span></small>' : ''}</td><td>${packagingKindLabel(item.kind)}</td><td>${unitLabel(item.unit)}${item.capacity_value && item.capacity_unit ? `<small>${packagingItemCapacityLabel(item)}</small>` : ''}</td><td>${escapeHtml(packagingCatalogCategoryLabel(item))}</td><td>${packagingTagChips(item)}</td><td><span class="pill ${item.is_active ? 'success' : 'muted'}">${item.is_active ? 'Активна' : 'Архив'}</span></td><td><div class="row-actions"><button class="secondary-action compact" type="button" data-action="edit-packaging-item" data-id="${item.id}">Изменить</button>${item.is_active ? `<button class="secondary-action compact danger-action" type="button" data-action="deactivate-packaging-item" data-id="${item.id}">Деактивировать</button>` : ''}</div></td></tr>`; }).join('')}</tbody></table></div><p class="next-step">Длинные заметки, поставщик, материал и цена остаются в форме редактирования, чтобы список был компактным.</p></section>`;
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
    Производство: { title: 'Производство', now: 'История изготовленных партий доступна в отдельном read-only журнале.' },
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
  const workspace = recipesState.showCreateForm ? recipeTemplateForm() : recipesState.selectedTemplate ? recipeDetailWorkspace() : '';
  const helper = !recipesState.showCreateForm && !recipesState.selectedTemplate ? recipeCreateHelperCard() : '';
  return `<div class="recipes-layout"><section class="card recipes-intro"><div><p class="card-kicker">Рецепты</p><h2>Каталог рецептов</h2><p>Сначала найдите сохраненный рецепт, затем открывайте создание, карточку или версии. Сохраненные версии только просматриваются и рассчитываются — история не редактируется.</p></div><div class="actions"><button class="primary-action" type="button" data-action="open-recipe-create">Создать рецепт</button><button class="secondary-action" type="button" data-action="reload-recipes">Обновить</button></div></section>${recipesMessage ? `<p class="page-message">${recipesMessage}</p>` : ''}${recipesError ? `<p class="page-message error-message">${recipesError}</p>` : ''}${recipeFilterToolbar()}${workspace}${recipeTemplateList()}${helper}</div>`;
}
function recipeFilterToolbar() { const f = recipesState.filters; const categoryOptionsHtml = [`<option value="" ${f.categoryId === '' ? 'selected' : ''}>Все группы</option>`, `<option value="none" ${f.categoryId === 'none' ? 'selected' : ''}>Без группы</option>`, ...recipesState.catalogCategories.map((category) => `<option value="${category.id}" ${f.categoryId === category.id ? 'selected' : ''}>${escapeHtml(category.name)}</option>`)].join(''); const activeFilters = recipeActiveFilterChips(); return `<section class="card data-card catalog-browser"><p class="card-kicker">Каталог рецептов</p><h2>Найти рецепт</h2><div class="catalog-toolbar"><label class="full-span">Поиск<input type="search" data-action="filter-recipes-search" value="${escapeHtml(f.search)}" placeholder="Название, тип продукта, описание, заметки или статус" /></label><label>Моя группа<select data-action="filter-recipes-category">${categoryOptionsHtml}</select></label><label>Статус<select data-action="filter-recipes-status"><option value="active" ${f.status === 'active' ? 'selected' : ''}>Активные</option><option value="archived" ${f.status === 'archived' ? 'selected' : ''}>Неактивные</option><option value="all" ${f.status === 'all' ? 'selected' : ''}>Все</option></select></label></div>${activeFilters ? `<div class="active-filter-row"><strong>Активные фильтры:</strong>${activeFilters}</div>` : ''}<div class="catalog-summary"><span>Показаны рецепты: ${filteredRecipeTemplates().length} из ${recipesState.templates.length}</span><button class="secondary-action compact" type="button" data-action="reset-recipe-filters">Сбросить фильтры</button></div></section>`; }
function recipeTemplateForm() { const f = recipesState.templateForm; return `<section class="card form-card"><div class="section-heading"><div><p class="card-kicker">Новый рецепт</p><h2>Создать рецепт</h2></div><button class="secondary-action compact" type="button" data-action="hide-recipe-create">Вернуться к каталогу</button></div><form data-form="recipe-template" class="ingredient-form"><div class="form-grid"><label>Название рецепта<input name="name" data-field="recipe-template-name" required maxlength="160" value="${escapeHtml(f.name)}" placeholder="Например, базовый дневной крем" /></label><label>Тип продукта<input name="product_type" maxlength="120" value="${escapeHtml(f.product_type)}" placeholder="Крем, гель, тоник…" /></label><label class="full-span">Описание<textarea name="description" rows="3" maxlength="1200">${escapeHtml(f.description)}</textarea></label><label class="full-span">Заметки<textarea name="notes" rows="3" maxlength="1200">${escapeHtml(f.notes)}</textarea></label></div><div class="actions"><button class="primary-action" type="submit">Создать рецепт</button><button class="secondary-action" type="button" data-action="hide-recipe-create">Вернуться к каталогу</button></div></form></section>`; }
function recipeCreateHelperCard() { return `<section class="card empty-card"><p class="card-kicker">Создание</p><h2>Нужно добавить новый рецепт?</h2><p>Форма создания скрыта, чтобы каталог оставался первым рабочим экраном.</p><p class="next-step">Нажмите «Создать рецепт», когда не нашли подходящую базовую формулу.</p><button class="primary-action" type="button" data-action="open-recipe-create">Создать рецепт</button></section>`; }
function recipeTemplateList() { const templates = filteredRecipeTemplates(); if (recipesState.templates.length === 0) return `<section class="card empty-card"><h2>Пока нет рецептов</h2><p>Пока нет рецептов. Создайте базовый рецепт, затем добавьте версию с составом.</p><p class="next-step">Следующее действие: нажмите «Создать рецепт».</p><button class="primary-action" type="button" data-action="open-recipe-create">Создать рецепт</button></section>`; if (templates.length === 0) return `<section class="card empty-card"><h2>По фильтрам рецепты не найдены</h2><p>Измените поиск или сбросьте фильтры, чтобы снова увидеть каталог.</p><button class="secondary-action" type="button" data-action="reset-recipe-filters">Сбросить фильтры</button></section>`; return `<section class="card data-card"><p class="card-kicker">Список</p><h2>Рецепты</h2><div class="recipe-list">${templates.map((t)=>`<article class="recipe-list-item ${recipesState.selectedTemplate?.id===t.id?'selected catalog-row-selected':''}"><div><strong>${escapeHtml(t.name)}</strong><small>${escapeHtml(t.product_type || 'Тип продукта не указан')} · <span class="pill ${t.is_active?'success':'muted'}">${t.is_active?'Активен':'Неактивен'}</span>${recipesState.selectedTemplate?.id===t.id?' · <span class="pill warning">Открыто</span>':''}</small><small>Моя группа: ${escapeHtml(recipeCatalogCategoryLabel(t))}</small>${recipeTagChips(t)}</div><button class="secondary-action compact" type="button" data-action="open-recipe" data-id="${t.id}">${recipesState.selectedTemplate?.id===t.id?'Открыто':'Открыть'}</button></article>`).join('')}</div></section>`; }
function recipeDetailWorkspace() { return `<div class="recipe-columns"><div>${recipeCatalogPanel()}</div><div>${recipeDetailPanel()}</div></div>`; }
function recipeCatalogPanel() { const template = recipesState.selectedTemplate; if (!template) return `<section class="card empty-card"><p class="card-kicker">Моя организация каталога</p><h2>Моя группа и метки</h2><p>Выберите рецепт, чтобы назначить ему группу и метки.</p><p class="next-step">Группы и метки помогают навести порядок в рецептах. Они не меняют версии рецепта и состав формулы.</p></section>`; const categoryDisabled = recipesState.catalogCreating === 'category'; const tagDisabled = recipesState.catalogCreating === 'tag'; return `<section class="card form-card"><p class="card-kicker">Моя организация каталога</p><h2>Моя группа и метки</h2><p>Группы и метки помогают навести порядок в рецептах. Они не меняют версии рецепта и состав формулы.</p><div class="catalog-classification"><label>Моя группа<select data-action="assign-recipe-category" data-id="${template.id}" ${recipesState.catalogSaving === 'saving' ? 'disabled' : ''}><option value="">Без моей группы</option>${recipesState.catalogCategories.map((category) => `<option value="${category.id}" ${category.id === template.catalog_category_id ? 'selected' : ''}>${escapeHtml(category.name)}</option>`).join('')}</select></label>${recipesState.catalogCategories.length === 0 ? '<p class="empty-hint">Группы рецептов пока не созданы. Создайте первую группу ниже.</p>' : ''}<div><strong>Метки</strong>${recipesState.catalogTags.length === 0 ? '<p class="empty-hint">Метки рецептов пока не созданы. Создайте первую метку ниже.</p>' : `<div class="tag-picker">${recipesState.catalogTags.map((tag) => `<label class="tag-chip ${template.catalog_tag_ids.includes(tag.id) ? 'selected' : ''}"><input type="checkbox" data-action="toggle-recipe-tag" data-recipe-template-id="${template.id}" value="${tag.id}" ${template.catalog_tag_ids.includes(tag.id) ? 'checked' : ''} ${recipesState.catalogSaving === 'saving' ? 'disabled' : ''} />${escapeHtml(tag.name)}</label>`).join('')}</div>`}</div></div><div class="catalog-create-grid"><form data-form="recipe-catalog-category" class="catalog-create-form"><h3>Добавить группу рецептов</h3><label>Название группы<input name="name" required maxlength="160" placeholder="Например, Кремы" ${categoryDisabled ? 'disabled' : ''} /></label><button class="secondary-action" type="submit" ${categoryDisabled ? 'disabled' : ''}>${recipesState.catalogCreating === 'category' ? 'Создаем…' : 'Создать группу'}</button></form><form data-form="recipe-catalog-tag" class="catalog-create-form"><h3>Добавить метку рецепта</h3><label>Название метки<input name="name" required maxlength="160" placeholder="Например, Для сухой кожи" ${tagDisabled ? 'disabled' : ''} /></label><button class="secondary-action" type="submit" ${tagDisabled ? 'disabled' : ''}>${recipesState.catalogCreating === 'tag' ? 'Создаем…' : 'Создать метку'}</button></form></div><p class="next-step">Группа и метки сохраняются сразу. Они помогают найти рецепт, но не меняют его версии и состав.</p></section>`; }
function recipeDetailPanel() { const template = recipesState.selectedTemplate; if (!template) return `<section class="card empty-card"><h2>Выберите рецепт</h2><p>Откройте рецепт из списка, чтобы увидеть версии, состав и расчет.</p><p class="next-step">Исторические версии не редактируются: для изменений создается новая версия.</p></section>`; return `<div class="recipe-detail-stack"><section class="card"><div class="section-heading"><div><p class="card-kicker">Рецепт</p><h2>${escapeHtml(template.name)}</h2></div><button class="secondary-action compact" type="button" data-action="close-recipe-detail">Закрыть рецепт</button></div><p><strong>Тип:</strong> ${escapeHtml(template.product_type || 'не указан')}</p><p>${escapeHtml(template.description || 'Описание пока не заполнено.')}</p>${template.notes ? `<p class="next-step">${escapeHtml(template.notes)}</p>` : ''}<span class="pill ${template.is_active?'success':'muted'}">${template.is_active?'Активен':'Неактивен'}</span></section>${recipeVersionsList()}${recipeVersionForm()}${recipeVersionDetailPanel()}</div>`; }
function recipeVersionsList() { if (recipesState.versions.length === 0) return `<section class="card empty-card"><h2>Версий пока нет</h2><p>У рецепта пока нет версий. Создайте первую версию и добавьте состав из компонентов.</p></section>`; return `<section class="card data-card"><p class="card-kicker">Версии</p><h2>Версии рецепта</h2><div class="table-wrap"><table><thead><tr><th>Версия</th><th>Статус</th><th>Заголовок</th><th>Партия</th><th>Создана</th><th>Действие</th></tr></thead><tbody>${recipesState.versions.map((v)=>`<tr><td>№${v.version_number}</td><td><span class="pill ${versionStatusClass(v.status)}">${versionStatusLabel(v.status)}</span></td><td>${escapeHtml(v.title || 'Без заголовка')}</td><td>${batchLabel(v.target_batch_size_value, v.target_batch_size_unit)}</td><td>${formatDateTime(v.created_at)}</td><td><button class="secondary-action compact" type="button" data-action="open-version" data-id="${v.id}">Открыть</button></td></tr>`).join('')}</tbody></table></div></section>`; }
function recipeVersionForm() { const f=recipesState.versionForm; const noIngredients = recipesState.ingredients.length === 0; return `<section class="card form-card"><p class="card-kicker">Новая версия рецепта</p><h2>Новая версия рецепта</h2><p class="next-step">Сохранение создаст новую историческую версию. Уже сохраненная версия не изменится${recipesState.selectedVersionDetail ? `; новая версия будет связана с версией №${recipesState.selectedVersionDetail.version.version_number} как с источником.` : '.'}</p><form data-form="recipe-version" class="ingredient-form"><div class="form-grid"><label>Заголовок версии<input name="title" maxlength="160" value="${escapeHtml(f.title)}" placeholder="Например, v1 с ниацинамидом" /></label><label>Статус<select name="status">${['draft','active','archived'].map((x)=>`<option value="${x}" ${f.status===x?'selected':''}>${versionStatusLabel(x)}</option>`).join('')}</select></label><label>Размер партии<input name="target_batch_size_value" inputmode="decimal" value="${escapeHtml(f.target_batch_size_value)}" placeholder="Например, 100" /></label><label>Единица партии<select name="target_batch_size_unit">${['g','ml','pcs'].map((x)=>`<option value="${x}" ${f.target_batch_size_unit===x?'selected':''}>${unitLabel(x)}</option>`).join('')}</select></label><label class="full-span">Комментарий к изменениям<textarea name="change_note" rows="2">${escapeHtml(f.change_note)}</textarea></label><label class="full-span">Заметки<textarea name="notes" rows="2">${escapeHtml(f.notes)}</textarea></label></div><h3>Конструктор состава</h3><p class="next-step">Соберите состав из компонентов справочника. После сохранения будет создана новая версия рецепта. Сохраненные версии не изменяются автоматически.</p><p class="empty-hint">Фазы A, B, C и D помогают читать формулу по шагам приготовления. Позиция задает порядок строк внутри версии.</p>${noIngredients ? '<p class="empty-hint">В рецепте пока нельзя выбрать компонент: активные компоненты не найдены. Создайте компонент в разделе «Компоненты» или обновите список.</p><p class="next-step">Если компонент уже создан, нажмите «Обновить список компонентов» и проверьте, что он не архивирован.</p>' : ''}<div class="recipe-lines">${f.ingredients.map(recipeLineForm).join('')}</div>${draftPercentHint()}<p class="next-step">Сначала добавьте компоненты в состав версии. Когда формула готова, нажмите «Сохранить версию рецепта». Сохранение создаст новую историческую версию и не изменит уже сохранённые версии.</p><div class="actions"><button class="secondary-action" type="button" data-action="add-recipe-line" ${noIngredients ? 'disabled' : ''}>Добавить компонент в состав</button><button class="secondary-action" type="button" data-action="reload-recipe-ingredients">Обновить список компонентов</button><button class="primary-action" type="submit" ${noIngredients ? 'disabled' : ''}>Сохранить версию рецепта</button></div></form></section>`; }
function recipeLineForm(line: RecipeLineForm, index: number) { const noIngredients = recipesState.ingredients.length === 0; return `<fieldset class="recipe-line"><legend>Строка ${index+1} · Фаза ${escapeHtml(line.phase || 'A')}</legend><label>Позиция<input name="position_${index}" required inputmode="numeric" value="${escapeHtml(line.position)}" placeholder="${index + 1}" /></label><label>Фаза<select name="phase_${index}">${phaseOptions(line.phase)}</select></label><label>Компонент<select name="ingredient_id_${index}" required ${noIngredients ? 'disabled' : ''}><option value="">${noIngredients ? 'Нет активных компонентов' : 'Выберите компонент'}</option>${recipesState.ingredients.map((i)=>`<option value="${i.id}" ${line.ingredient_id===String(i.id)?'selected':''}>${escapeHtml(i.name)}</option>`).join('')}</select></label><label>Количество<input name="amount_value_${index}" required inputmode="decimal" value="${escapeHtml(line.amount_value)}" placeholder="Например, 5 или 2.5" /></label><label>Единица<select name="amount_unit_${index}">${['percent','g','ml','pcs'].map((u)=>`<option value="${u}" ${line.amount_unit===u?'selected':''}>${unitLabel(u)}</option>`).join('')}</select></label><label class="full-span">Заметка<input name="notes_${index}" value="${escapeHtml(line.notes)}" placeholder="Необязательно" /></label>${recipesState.versionForm.ingredients.length>1?`<button class="secondary-action compact danger-action" type="button" data-action="remove-recipe-line" data-index="${index}">Удалить строку</button>`:''}</fieldset>`; }
function recipeVersionDetailPanel() { if (recipesState.versionDetailStatus === 'loading') return `<section class="card"><h2>Загружаем версию…</h2><p>Получаем сохраненный состав и расчет из backend.</p></section>`; if (recipesState.versionDetailStatus === 'error') return `<section class="card error-card"><h2>Не удалось загрузить версию рецепта</h2><p>Попробуйте открыть версию еще раз или обновить раздел.</p></section>`; const d=recipesState.selectedVersionDetail; if (!d) return ''; const v=d.version; const lines = d.ingredients.slice().sort((a,b)=>a.phase.localeCompare(b.phase) || a.position-b.position); return `<section class="card data-card"><p class="card-kicker">Сохраненная версия</p><h2>Версия №${v.version_number}</h2><p><strong>${escapeHtml(v.title || 'Без заголовка')}</strong> · ${versionStatusLabel(v.status)} · ${batchLabel(v.target_batch_size_value, v.target_batch_size_unit)}</p><p><strong>Комментарий к изменениям:</strong> ${escapeHtml(v.change_note || 'Не указан')}</p><p><strong>Заметки:</strong> ${escapeHtml(v.notes || 'Нет заметок')}</p><p class="next-step">Это сохраненная версия рецепта. Чтобы изменить состав, создайте новую версию на ее основе.</p>${d.ingredients.length===0?'<p class="empty-hint">В этой версии пока нет состава. Создайте новую версию с компонентами, чтобы использовать ее в индивидуальных рецептах и производстве.</p>':`<div class="table-wrap"><table><thead><tr><th>Позиция</th><th>Фаза</th><th>Компонент</th><th>Количество</th><th>Заметки</th></tr></thead><tbody>${lines.map((line)=>`<tr><td>${line.position}</td><td>${escapeHtml(line.phase || 'Не указана')}</td><td>${escapeHtml(ingredientName(line.ingredient_id))}</td><td>${escapeHtml(line.amount_value)} ${unitLabel(line.amount_unit)}</td><td>${escapeHtml(line.notes || 'Без заметок')}</td></tr>`).join('')}</tbody></table></div>`}${calculationPanel()}</section>`; }
function calculationPanel() { const c=recipesState.calculation; return `<div class="calculation-panel"><h3>Расчет версии</h3><form data-form="recipe-calculation" class="inline-form"><label>Целевой размер партии<input name="target_batch_size_value" inputmode="decimal" value="${escapeHtml(recipesState.calculationTargetValue)}" placeholder="Оставьте пустым для размера версии" /></label><label>Единица<select name="target_batch_size_unit"><option value="g" ${recipesState.calculationTargetUnit==='g'?'selected':''}>г</option><option value="ml" ${recipesState.calculationTargetUnit==='ml'?'selected':''}>мл</option></select></label><button class="primary-action" type="submit">Пересчитать</button></form>${calculationStatus==='loading'?'<p>Считаем на backend…</p>':''}${calculationError?`<p class="page-message error-message">${calculationError}</p>`:''}${c?calculationResult(c):'<p class="next-step">Backend расчет загрузится автоматически для сохраненной версии. Если нужно, укажите другой размер партии и пересчитайте.</p>'}</div>`; }
function calculationResult(c: RecipeCalculationResult) { return `<div class="calculation-result"><p><strong>Можно рассчитать:</strong> ${c.can_calculate?'да':'нет'} · <strong>Сумма процентов:</strong> ${escapeHtml(c.percent_total)}%</p>${c.issues.length?`<h4>${c.issues.some((i)=>i.severity==='error')?'Нужно исправить':'Предупреждения'}</h4><ul class="issue-list">${c.issues.map((i)=>`<li class="${i.severity==='error'?'danger-text':'warning-text'}">${escapeHtml(i.message)}${i.next_action?` <small>${escapeHtml(i.next_action)}</small>`:''}</li>`).join('')}</ul>`:''}<h4>Состав</h4>${c.lines.length?`<div class="table-wrap"><table><thead><tr><th>Компонент</th><th>Исходно</th><th>Рассчитано</th><th>Фаза</th><th>Комментарий</th></tr></thead><tbody>${c.lines.map((l)=>`<tr><td>${escapeHtml(l.ingredient_name)}</td><td>${escapeHtml(l.source_amount_value)} ${unitLabel(l.source_amount_unit)}</td><td>${l.calculated_amount_value?`${escapeHtml(l.calculated_amount_value)} ${unitLabel(l.calculated_amount_unit || '')}`:'—'}</td><td>${escapeHtml(l.phase || 'Не указана')}</td><td>${escapeHtml(l.calculation_note || '')}</td></tr>`).join('')}</tbody></table></div>`:'<p>Backend не вернул расчетных строк.</p>'}<h4>Итого по единицам</h4>${c.totals_by_unit.length?`<ul>${c.totals_by_unit.map((t)=>`<li>${escapeHtml(t.total_value)} ${unitLabel(t.unit)}</li>`).join('')}</ul>`:'<p>Итоги пока не рассчитаны.</p>'}</div>`; }


function emptyPackagingItemForm(): PackagingItemFormState { return { id: null, name: '', kind: 'jar', unit: 'pcs', capacity_value: null, capacity_unit: null, material: '', supplier_hint: '', unit_cost: null, notes: '' }; }
function packagingKindLabel(kind: string) { return ({ jar: 'Баночка', bottle: 'Флакон', tube: 'Туба', pump: 'Помпа', cap: 'Крышка', dropper: 'Пипетка', label: 'Этикетка', box: 'Коробка', bag: 'Пакет', other: 'Другое' } as Record<string, string>)[kind] ?? escapeHtml(kind); }
function packagingKindOptions(current: string) { return packagingKindValues().map((value) => `<option value="${value}" ${value === current ? 'selected' : ''}>${packagingKindLabel(value)}</option>`).join(''); }
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



function filteredClientRecipes() {
  const f = clientRecipesState.filters;
  return clientRecipesState.items.filter((recipe) => {
    if (f.status === 'active' && !recipe.is_active) return false;
    if (f.status === 'archived' && recipe.is_active) return false;
    if (f.clientId && recipe.client_id !== Number(f.clientId)) return false;
    return textMatchesSearch(clientRecipeSearchText(recipe), f.search);
  });
}
function clientRecipeSearchText(recipe: ClientRecipe) { return [recipe.title, recipe.is_active ? 'Активен' : 'Архив', recipe.status, recipe.personalization_notes, recipe.allergy_notes, recipe.preference_notes, recipe.contraindication_notes, recipe.notes, clientRecipeClientName(recipe.client_id)].join(' '); }
function clientRecipeListTitle() { if (clientRecipesState.filters.status === 'archived') return 'Архив индивидуальных рецептов'; if (clientRecipesState.filters.status === 'all') return 'Все индивидуальные рецепты'; return 'Активные индивидуальные рецепты'; }
function clientRecipeNotesSummary(recipe: ClientRecipe) { const rows = [['Персонализация', recipe.personalization_notes], ['Аллергии', recipe.allergy_notes], ['Предпочтения', recipe.preference_notes], ['Противопоказания', recipe.contraindication_notes], ['Заметки', recipe.notes]].filter(([, value]) => value); return rows.length ? `<ul>${rows.slice(0, 2).map(([label, value]) => `<li><strong>${label}:</strong> ${escapeHtml(shortText(value, 80))}</li>`).join('')}</ul>` : 'Особые заметки не указаны'; }
function clientRecipeVersionHelperText() { if (!clientRecipesState.form.recipe_template_id) return 'Сначала выберите базовый рецепт. После этого здесь появятся его сохранённые версии состава.'; if (clientRecipesState.versionsStatus === 'loading') return 'Загружаем сохранённые версии состава…'; if (clientRecipesState.versionsStatus === 'ready' && clientRecipesState.versions.length === 0) return 'У этого рецепта ещё нет сохранённой версии состава. Откройте раздел «Рецепты», добавьте состав и нажмите «Сохранить версию рецепта». После этого вернитесь сюда и выберите версию.'; if (clientRecipesState.versions.length > 0) return 'Выберите версию состава, из которой будет создана отдельная копия для клиента.'; return 'Сначала выберите базовый рецепт. После этого здесь появятся его сохранённые версии состава.'; }
function clientRecipeActiveFilterChips() { const chips: string[] = []; const f = clientRecipesState.filters; if (f.search.trim()) chips.push(clearableClientRecipeFilterChip(`Поиск: ${escapeHtml(f.search.trim())}`, 'search')); if (f.status !== 'active') chips.push(clearableClientRecipeFilterChip(`Статус: ${f.status === 'archived' ? 'Архив' : 'Все'}`, 'status')); if (f.clientId) chips.push(clearableClientRecipeFilterChip(`Клиент: ${escapeHtml(clientRecipeClientName(Number(f.clientId)))}`, 'client')); return chips.join(''); }
function clearableClientRecipeFilterChip(label: string, filter: 'search' | 'status' | 'client') { return `<span class="tag-chip selected">${label} <button type="button" data-action="clear-client-recipe-filter" data-filter="${filter}" aria-label="Убрать фильтр ${label}">×</button></span>`; }
function updateClientRecipeFilterSearch(input: HTMLInputElement) { const cursor = input.selectionStart ?? input.value.length; clientRecipesState.filters.search = input.value; render(); const nextInput = document.querySelector<HTMLInputElement>('[data-action="filter-client-recipes-search"]'); if (!nextInput) return; nextInput.focus(); const nextCursor = Math.min(cursor, nextInput.value.length); nextInput.setSelectionRange(nextCursor, nextCursor); }
function updateClientRecipeStatusFilter(status: ClientRecipeStatusFilter) { clientRecipesState.filters.status = status; clientRecipesState.includeInactive = status !== 'active'; loadClientRecipes(true); }
function resetClientRecipeFilters() { const shouldReload = clientRecipesState.includeInactive; clientRecipesState.filters = { search: '', status: 'active', clientId: '' }; clientRecipesState.includeInactive = false; if (shouldReload) loadClientRecipes(true); else render(); }
function clearClientRecipeFilter(filter: string) { if (filter === 'search') { clientRecipesState.filters.search = ''; render(); return; } if (filter === 'client') { clientRecipesState.filters.clientId = ''; render(); return; } if (filter === 'status') updateClientRecipeStatusFilter('active'); }
function openClientRecipeCreate() { clientRecipesState.compositionEditor = emptyClientRecipeCompositionEditor(); if (clientRecipesState.showCreateForm) { saveClientRecipeFormFromDom(); render(); focusClientRecipeTitle(); return; } clientRecipesState.showCreateForm = true; clientRecipesState.selectedDetail = null; clientRecipesState.detailStatus = 'idle'; clientRecipesState.form = emptyClientRecipeForm(); clientRecipesState.versions = []; clientRecipesState.versionsStatus = 'idle'; clientRecipesState.selectedTemplateId = null; clientRecipesMessage = ''; clientRecipesError = ''; render(); focusClientRecipeTitle(); refreshClientRecipeCreateDependencies(); }
function hideClientRecipeCreate() { clientRecipesState.showCreateForm = false; clientRecipesState.form = emptyClientRecipeForm(); clientRecipesState.versions = []; clientRecipesState.versionsStatus = 'idle'; clientRecipesState.selectedTemplateId = null; render(); }

function focusClientRecipeTitle() { requestAnimationFrame(() => document.querySelector<HTMLInputElement>('[data-field="client-recipe-title"]')?.focus()); }
function refreshClientRecipeCreateDependencies() { Promise.all([getClients(true), getRecipeTemplates(), getIngredients()]).then(([clients, templates, ingredients]) => { if (clientRecipesState.showCreateForm) saveClientRecipeFormFromDom(); clientRecipesState.clients = clients.clients; clientRecipesState.templates = templates.recipe_templates; recipesState.ingredients = ingredients.ingredients; render(); focusClientRecipeTitle(); }).catch(() => { clientRecipesError = 'Не удалось обновить клиентов и базовые рецепты. Проверьте локальное приложение и попробуйте ещё раз.'; render(); }); }
function closeClientRecipeDetail() { clientRecipesState.selectedDetail = null; clientRecipesState.detailStatus = 'idle'; clientRecipesState.compositionEditor = emptyClientRecipeCompositionEditor(); render(); }
function clientRecipeClientName(id: number) { return clientRecipesState.clients.find((c)=>c.id===id)?.full_name ?? `Клиент #${id}`; }
function clientRecipeIngredientName(id: number) { return recipesState.ingredients.find((i)=>i.id===id)?.name ?? ingredientsState.items.find((i)=>i.id===id)?.name ?? `Компонент #${id}`; }
function clientRecipePayloadFromForm(form: HTMLFormElement): ClientRecipePayload { const data = new FormData(form); const batch = String(data.get('target_batch_size_value') ?? '').trim(); return { client_id: Number(data.get('client_id')), source_recipe_version_id: Number(data.get('source_recipe_version_id')), title: String(data.get('title') ?? '').trim(), target_batch_size_value: batch || null, target_batch_size_unit: batch ? String(data.get('target_batch_size_unit') ?? 'g') : null, personalization_notes: String(data.get('personalization_notes') ?? '').trim(), allergy_notes: String(data.get('allergy_notes') ?? '').trim(), preference_notes: String(data.get('preference_notes') ?? '').trim(), contraindication_notes: String(data.get('contraindication_notes') ?? '').trim(), notes: String(data.get('notes') ?? '').trim() }; }
function saveClientRecipeFormFromDom() { const form = document.querySelector<HTMLFormElement>('[data-form="client-recipe"]'); if (!form) return; const data = new FormData(form); clientRecipesState.form = { client_id: String(data.get('client_id') ?? ''), recipe_template_id: String(data.get('recipe_template_id') ?? ''), source_recipe_version_id: String(data.get('source_recipe_version_id') ?? ''), title: String(data.get('title') ?? '').trim(), target_batch_size_value: String(data.get('target_batch_size_value') ?? '').trim(), target_batch_size_unit: String(data.get('target_batch_size_unit') ?? 'g'), personalization_notes: String(data.get('personalization_notes') ?? '').trim(), allergy_notes: String(data.get('allergy_notes') ?? '').trim(), preference_notes: String(data.get('preference_notes') ?? '').trim(), contraindication_notes: String(data.get('contraindication_notes') ?? '').trim(), notes: String(data.get('notes') ?? '').trim() }; }
function humanClientRecipeError(error: unknown) { const message = error instanceof Error ? error.message : ''; if (message.includes('Source recipe version has no ingredient lines')) return 'Не удалось создать индивидуальный рецепт: выбранная версия рецепта пустая. Добавьте состав в версии рецепта.'; if (message.includes('Client is inactive')) return 'Не удалось создать индивидуальный рецепт: выбранный клиент находится в архиве. Выберите активного клиента.'; if (message.includes('Ingredient is inactive')) return 'Не удалось создать индивидуальный рецепт: в версии рецепта есть архивный компонент. Проверьте состав версии.'; if (message.includes('Client was not found')) return 'Не удалось создать индивидуальный рецепт: выбранный клиент не найден. Обновите список клиентов.'; if (message.includes('Source recipe version was not found')) return 'Не удалось создать индивидуальный рецепт: выбранная версия рецепта не найдена. Обновите рецепты.'; return 'Не удалось создать индивидуальный рецепт. Проверьте клиента, версию рецепта и обязательные поля.'; }
function loadClientRecipes(force = false) { if (!force && (clientRecipesStatus === 'loading' || clientRecipesStatus === 'ready')) return; clientRecipesStatus = 'loading'; clientRecipesError = ''; render(); Promise.all([getClientRecipes(clientRecipesState.includeInactive), getClients(true), getRecipeTemplates(), getIngredients()]).then(([recipes, clients, templates, ingredients]) => { clientRecipesState.items = recipes.client_recipes; clientRecipesState.clients = clients.clients; clientRecipesState.templates = templates.recipe_templates; recipesState.ingredients = ingredients.ingredients; clientRecipesStatus = 'ready'; render(); }).catch(() => { clientRecipesStatus = 'error'; clientRecipesError = 'Не получилось получить индивидуальные рецепты, клиентов или базовые рецепты из локального приложения.'; render(); }); }
function selectClientRecipeTemplate(value: string) { saveClientRecipeFormFromDom(); clientRecipesState.form.recipe_template_id = value; clientRecipesState.form.source_recipe_version_id = ''; clientRecipesState.selectedTemplateId = value ? Number(value) : null; clientRecipesState.versions = []; clientRecipesState.versionsStatus = value ? 'loading' : 'idle'; clientRecipesError = ''; if (!value) { render(); return; } render(); getRecipeVersions(Number(value)).then((response) => { saveClientRecipeFormFromDom(); clientRecipesState.versions = response.recipe_versions; clientRecipesState.versionsStatus = 'ready'; render(); }).catch(() => { clientRecipesState.versionsStatus = 'error'; clientRecipesError = 'Не удалось загрузить сохранённые версии состава. Попробуйте выбрать базовый рецепт ещё раз.'; render(); }); }
function submitClientRecipeForm(event: SubmitEvent) { event.preventDefault(); const form = event.currentTarget as HTMLFormElement; saveClientRecipeFormFromDom(); const payload = clientRecipePayloadFromForm(form); if (!payload.client_id) { clientRecipesError = 'Выберите клиента, для которого создаётся индивидуальный рецепт.'; clientRecipesMessage = ''; render(); return; } if (!payload.source_recipe_version_id) { clientRecipesError = 'Выберите сохранённую версию состава. Если список пустой, сначала сохраните версию в разделе «Рецепты».'; clientRecipesMessage = ''; render(); return; } if (!payload.title) { clientRecipesError = 'Укажите название индивидуального рецепта, например «Крем для Анны: без отдушки».'; clientRecipesMessage = ''; render(); return; } createClientRecipe(payload).then((detail) => { clientRecipesMessage = 'Индивидуальный рецепт создан.'; clientRecipesError = ''; clientRecipesState.selectedDetail = detail; clientRecipesState.compositionEditor = emptyClientRecipeCompositionEditor(); clientRecipesState.detailStatus = 'ready'; clientRecipesState.showCreateForm = false; clientRecipesState.form = emptyClientRecipeForm(); clientRecipesState.versions = []; clientRecipesState.versionsStatus = 'idle'; clientRecipesState.selectedTemplateId = null; return getClientRecipes(clientRecipesState.includeInactive); }).then((response) => { clientRecipesState.items = response.client_recipes; clientRecipesStatus = 'ready'; render(); }).catch((error) => { clientRecipesMessage = ''; clientRecipesError = humanClientRecipeError(error); clientRecipesStatus = 'ready'; render(); }); }
function openClientRecipe(id: number) { clientRecipesState.showCreateForm = false; clientRecipesState.selectedDetail = null; clientRecipesState.compositionEditor = emptyClientRecipeCompositionEditor(); clientRecipesState.detailStatus = 'loading'; clientRecipesError = ''; render(); getClientRecipe(id).then((detail) => { clientRecipesState.selectedDetail = detail; clientRecipesState.detailStatus = 'ready'; render(); }).catch(() => { clientRecipesState.detailStatus = 'error'; clientRecipesError = 'Не удалось открыть индивидуальный рецепт. Обновите список и попробуйте еще раз.'; render(); }); }
function deactivateClientRecipe(id: number) { const recipe = clientRecipesState.items.find((item)=>item.id===id); if (!recipe || !window.confirm('Архивировать индивидуальный рецепт? Карточка останется в истории, но не будет отображаться как активная.')) return; deactivateClientRecipeRequest(id).then(() => { clientRecipesMessage = 'Индивидуальный рецепт архивирован.'; clientRecipesError = ''; return getClientRecipes(clientRecipesState.includeInactive); }).then((response) => { clientRecipesState.items = response.client_recipes; if (clientRecipesState.selectedDetail?.client_recipe.id === id) clientRecipesState.selectedDetail = null; clientRecipesStatus = 'ready'; render(); }).catch(() => { clientRecipesMessage = ''; clientRecipesError = 'Не удалось архивировать индивидуальный рецепт. Попробуйте еще раз.'; clientRecipesStatus = 'ready'; render(); }); }
function restoreClientRecipe(id: number) { if (!window.confirm('Вернуть индивидуальный рецепт из архива?')) return; restoreClientRecipeRequest(id).then((restored) => { clientRecipesMessage = 'Индивидуальный рецепт возвращён в работу.'; clientRecipesError = ''; clientRecipesState.filters.status = 'active'; clientRecipesState.includeInactive = false; clientRecipesState.compositionEditor = emptyClientRecipeCompositionEditor(); return Promise.all([getClientRecipes(false), getClientRecipe(restored.id)]); }).then(([response, detail]) => { clientRecipesState.items = response.client_recipes; clientRecipesState.selectedDetail = detail; clientRecipesState.detailStatus = 'ready'; clientRecipesState.showCreateForm = false; clientRecipesStatus = 'ready'; render(); }).catch(() => { clientRecipesMessage = ''; clientRecipesError = 'Не удалось вернуть индивидуальный рецепт из архива. Проверьте, что клиент активен, и попробуйте ещё раз.'; clientRecipesStatus = 'ready'; render(); }); }

function clientRecipeCompositionEditorPanel() { const editor = clientRecipesState.compositionEditor; if (!editor.isOpen) return ''; const locked = editor.draft.some((line) => line.lockedReason); const noActiveIngredients = activeClientRecipeIngredients().length === 0; return `<form data-form="client-recipe-composition" class="ingredient-form"><h3>Редактирование состава</h3><p class="next-step">Вы меняете копию состава для этого клиента. Базовый рецепт и его сохранённые версии не изменятся.</p>${locked ? '<p class="next-step warning-text">Некоторые строки используют архивные или недоступные компоненты. Их можно оставить без изменений или удалить, но нельзя редактировать.</p><p class="next-step warning-text">Порядок строк нельзя менять, пока в составе есть архивные или недоступные компоненты. Их можно оставить без изменений или удалить.</p>' : ''}${editor.error ? `<p class="page-message error-message">${escapeHtml(editor.error)}</p>` : ''}${noActiveIngredients ? '<p class="empty-hint">Нет активных компонентов для добавления. Создайте компонент в разделе «Компоненты» или обновите список.</p>' : ''}<div class="recipe-lines">${editor.draft.map(clientRecipeCompositionLineForm).join('')}</div><div class="actions"><button class="secondary-action" type="button" data-action="add-client-recipe-composition-line" ${noActiveIngredients ? 'disabled' : ''}>Добавить компонент</button><button class="secondary-action" type="button" data-action="reset-client-recipe-composition-editor">Сбросить изменения</button><button class="secondary-action" type="button" data-action="close-client-recipe-composition-editor">Закрыть редактирование</button><button class="primary-action" type="submit" ${editor.isSaving ? 'disabled' : ''}>${editor.isSaving ? 'Сохраняем…' : 'Сохранить состав'}</button></div></form>`; }
function clientRecipeCompositionLineForm(line: ClientRecipeCompositionDraftLine, index: number) { const locked = Boolean(line.lockedReason); const hasLockedLines = clientRecipesState.compositionEditor.draft.some((draftLine) => draftLine.lockedReason); const disableReorder = clientRecipesState.compositionEditor.isSaving || hasLockedLines; return `<fieldset class="recipe-line"><legend>Строка ${index + 1}${locked ? ' · только просмотр' : ''}</legend><label>Порядок<input value="${index + 1}" disabled /></label><label>Компонент${locked ? `<input value="${escapeHtml(line.lockedReason ?? '')}" disabled />` : `<select name="composition_ingredient_id_${index}" required><option value="">Выберите компонент</option>${activeClientRecipeIngredients().map((i)=>`<option value="${i.id}" ${line.ingredient_id===String(i.id)?'selected':''}>${escapeHtml(i.name)}</option>`).join('')}</select>`}</label><label>Количество<input name="composition_amount_value_${index}" required inputmode="decimal" value="${escapeHtml(line.amount_value)}" ${locked ? 'disabled' : ''} placeholder="Например, 5 или 2.5" /></label><label>Единица<select name="composition_amount_unit_${index}" ${locked ? 'disabled' : ''}>${['g','ml','percent','pcs'].map((u)=>`<option value="${u}" ${line.amount_unit===u?'selected':''}>${unitLabel(u)}</option>`).join('')}</select></label><label>Фаза<select name="composition_phase_${index}" ${locked ? 'disabled' : ''}>${clientRecipePhaseOptions(line.phase)}</select></label><label class="full-span">Заметка персонализации<textarea name="composition_personalization_note_${index}" rows="2" ${locked ? 'disabled' : ''}>${escapeHtml(line.personalization_note)}</textarea></label><label class="full-span">Заметки<textarea name="composition_notes_${index}" rows="2" ${locked ? 'disabled' : ''}>${escapeHtml(line.notes)}</textarea></label><div class="actions"><button class="secondary-action compact" type="button" data-action="move-client-recipe-composition-line" data-index="${index}" data-direction="-1" ${index === 0 || disableReorder ? 'disabled' : ''}>↑</button><button class="secondary-action compact" type="button" data-action="move-client-recipe-composition-line" data-index="${index}" data-direction="1" ${index === clientRecipesState.compositionEditor.draft.length - 1 || disableReorder ? 'disabled' : ''}>↓</button><button class="secondary-action compact danger-action" type="button" data-action="remove-client-recipe-composition-line" data-index="${index}">Удалить строку</button></div></fieldset>`; }
function activeClientRecipeIngredients() { return recipesState.ingredients.filter((i) => i.is_active); }
function emptyClientRecipeCompositionEditor(): ClientRecipeCompositionEditorState { return { isOpen: false, isSaving: false, draft: [], error: '' }; }
function clientRecipeCompositionDraftFromDetail(detail: ClientRecipeDetail) { return detail.ingredients.slice().sort((a,b)=>a.position-b.position).map((line, index) => { const active = activeClientRecipeIngredients().some((i)=>i.id===line.ingredient_id); return { id: line.id, ingredient_id: String(line.ingredient_id), position: line.position || index + 1, phase: line.phase || '', amount_value: String(line.amount_value ?? ''), amount_unit: line.amount_unit || 'g', personalization_note: line.personalization_note || '', notes: line.notes || '', lockedReason: active ? undefined : `Компонент #${line.ingredient_id} — архивный или недоступный` }; }); }
function saveClientRecipeCompositionDraftFromDom() { const form = document.querySelector<HTMLFormElement>('[data-form="client-recipe-composition"]'); if (!form) return; const data = new FormData(form); clientRecipesState.compositionEditor.draft = clientRecipesState.compositionEditor.draft.map((line, index) => line.lockedReason ? line : { ...line, ingredient_id: String(data.get(`composition_ingredient_id_${index}`) ?? '').trim(), phase: String(data.get(`composition_phase_${index}`) ?? '').trim(), amount_value: String(data.get(`composition_amount_value_${index}`) ?? '').trim(), amount_unit: String(data.get(`composition_amount_unit_${index}`) ?? 'g'), personalization_note: String(data.get(`composition_personalization_note_${index}`) ?? '').trim(), notes: String(data.get(`composition_notes_${index}`) ?? '').trim() }); }
function clientRecipeCompositionDraftIsDirty() { const detail = clientRecipesState.selectedDetail; if (!detail) return false; return JSON.stringify(clientRecipesState.compositionEditor.draft) !== JSON.stringify(clientRecipeCompositionDraftFromDetail(detail)); }
function openClientRecipeCompositionEditor() { const detail = clientRecipesState.selectedDetail; if (!detail || !detail.client_recipe.is_active || detail.client_recipe.status === 'archived') return; const open = () => { clientRecipesState.compositionEditor = { isOpen: true, isSaving: false, draft: clientRecipeCompositionDraftFromDetail(detail), error: '' }; render(); }; if (recipesState.ingredients.length === 0) getIngredients().then((r)=>{ recipesState.ingredients = r.ingredients; open(); }).catch(()=>{ clientRecipesState.compositionEditor.error = 'Не удалось обновить список компонентов. Попробуйте ещё раз.'; render(); }); else open(); }
function addClientRecipeCompositionLine() { saveClientRecipeCompositionDraftFromDom(); clientRecipesState.compositionEditor.draft.push({ id: null, ingredient_id: '', position: clientRecipesState.compositionEditor.draft.length + 1, phase: 'A', amount_value: '', amount_unit: 'g', personalization_note: '', notes: '' }); render(); }
function removeClientRecipeCompositionLine(index: number) { saveClientRecipeCompositionDraftFromDom(); clientRecipesState.compositionEditor.draft.splice(index, 1); render(); }
function moveClientRecipeCompositionLine(index: number, direction: number) { saveClientRecipeCompositionDraftFromDom(); if (clientRecipesState.compositionEditor.draft.some((line) => line.lockedReason)) return; const next = index + direction; const draft = clientRecipesState.compositionEditor.draft; if (next < 0 || next >= draft.length) return; [draft[index], draft[next]] = [draft[next], draft[index]]; render(); }
function resetClientRecipeCompositionEditor() { const detail = clientRecipesState.selectedDetail; if (!detail) return; clientRecipesState.compositionEditor = { isOpen: true, isSaving: false, draft: clientRecipeCompositionDraftFromDetail(detail), error: '' }; render(); }
function closeClientRecipeCompositionEditor() { saveClientRecipeCompositionDraftFromDom(); if (clientRecipeCompositionDraftIsDirty() && !window.confirm('Закрыть редактирование и потерять несохранённые изменения?')) return; clientRecipesState.compositionEditor = emptyClientRecipeCompositionEditor(); render(); }
function validateClientRecipeCompositionDraft() { const draft = clientRecipesState.compositionEditor.draft; if (draft.length === 0) return 'Добавьте хотя бы одну строку состава.'; for (const [index, line] of draft.entries()) { if (line.lockedReason) continue; const row = index + 1; if (!line.ingredient_id) return `В строке ${row} выберите компонент.`; if (!line.amount_value) return `В строке ${row} укажите количество.`; if (!/^\d+([.,]\d+)?$/.test(line.amount_value) || Number(line.amount_value.replace(',', '.')) <= 0) return `В строке ${row} количество должно быть положительным числом, например 5 или 2,5.`; if (!line.amount_unit) return `В строке ${row} выберите единицу измерения.`; } return ''; }
function clientRecipeCompositionPayload(): ClientRecipeIngredientUpdatePayload[] { return clientRecipesState.compositionEditor.draft.map((line, index) => ({ ...(line.id ? { id: line.id } : {}), ingredient_id: Number(line.ingredient_id), position: index + 1, phase: line.phase, amount_value: line.amount_value.replace(',', '.'), amount_unit: line.amount_unit, personalization_note: line.personalization_note, notes: line.notes })); }
function submitClientRecipeCompositionEditor(event: SubmitEvent) { event.preventDefault(); const detail = clientRecipesState.selectedDetail; if (!detail) return; saveClientRecipeCompositionDraftFromDom(); const error = validateClientRecipeCompositionDraft(); if (error) { clientRecipesState.compositionEditor.error = error; render(); return; } clientRecipesState.compositionEditor.isSaving = true; clientRecipesState.compositionEditor.error = ''; render(); updateClientRecipeIngredients(detail.client_recipe.id, clientRecipeCompositionPayload()).then((updated) => { clientRecipesState.selectedDetail = updated; clientRecipesState.detailStatus = 'ready'; clientRecipesState.compositionEditor = emptyClientRecipeCompositionEditor(); clientRecipesMessage = 'Состав индивидуального рецепта сохранён. Базовый рецепт не изменён.'; clientRecipesError = ''; render(); }).catch((error) => { clientRecipesState.compositionEditor.isSaving = false; clientRecipesState.compositionEditor.error = humanClientRecipeCompositionError(error); render(); }); }
function humanClientRecipeCompositionError(error: unknown) { const message = error instanceof Error ? error.message : ''; if (message.includes('Archived')) return 'Архивный индивидуальный рецепт нельзя изменять.'; if (message.includes('Inactive ingredient') || message.includes('inactive')) return 'Архивный компонент нельзя добавлять или изменять. Оставьте существующую строку без изменений или удалите её.'; if (message.includes('not found') || message.includes('Not Found')) return 'Не удалось сохранить состав: индивидуальный рецепт или компонент не найден. Обновите раздел и попробуйте ещё раз.'; if (message.includes('duplicate') || message.includes('validation') || message.includes('position') || message.includes('amount')) return 'Проверьте строки состава: количество, единицы измерения и порядок строк.'; return 'Не удалось сохранить состав индивидуального рецепта. Проверьте строки и попробуйте ещё раз.'; }

function emptyClientRecipeForm(): ClientRecipeFormState { return { client_id: '', recipe_template_id: '', source_recipe_version_id: '', title: '', target_batch_size_value: '', target_batch_size_unit: 'g', personalization_notes: '', allergy_notes: '', preference_notes: '', contraindication_notes: '', notes: '' }; }

function emptyClientForm(): ClientFormState { return { id: null, full_name: '', phone: '', email: '', address: '', birthday: null, skin_notes: '', allergy_notes: '', preference_notes: '', contraindication_notes: '', notes: '' }; }
function clientPayloadFromForm(form: HTMLFormElement): ClientPayload { const data = new FormData(form); const birthday = String(data.get('birthday') ?? '').trim(); return { full_name: String(data.get('full_name') ?? '').trim(), phone: String(data.get('phone') ?? '').trim(), email: String(data.get('email') ?? '').trim(), address: String(data.get('address') ?? '').trim(), birthday: birthday || null, skin_notes: String(data.get('skin_notes') ?? '').trim(), allergy_notes: String(data.get('allergy_notes') ?? '').trim(), preference_notes: String(data.get('preference_notes') ?? '').trim(), contraindication_notes: String(data.get('contraindication_notes') ?? '').trim(), notes: String(data.get('notes') ?? '').trim() }; }
function clientNotesSummary(client: Client) { const rows = [['Аллергии', client.allergy_notes], ['Предпочтения', client.preference_notes], ['Противопоказания', client.contraindication_notes]].filter(([, value]) => value); return rows.length ? `<ul>${rows.map(([label, value]) => `<li><strong>${label}:</strong> ${escapeHtml(shortText(value, 90))}</li>`).join('')}</ul>` : 'Важные ограничения пока не указаны'; }
function shortText(value: string, maxLength: number) { const normalized = value.replace(/\s+/g, ' ').trim(); return normalized.length > maxLength ? `${normalized.slice(0, maxLength - 1)}…` : normalized; }
function filteredClients() { const search = clientsState.filters.search.trim().toLowerCase(); return clientsState.items.filter((client) => { if (clientsState.filters.status === 'active' && !client.is_active) return false; if (clientsState.filters.status === 'archived' && client.is_active) return false; if (!search) return true; return [client.full_name, client.phone, client.email, client.notes, client.skin_notes, client.allergy_notes, client.preference_notes, client.contraindication_notes].some((value) => value.toLowerCase().includes(search)); }); }
function clientListTitle() { if (clientsState.filters.status === 'archived') return 'Архив клиентов'; if (clientsState.filters.status === 'all') return 'Все клиенты'; return 'Активные клиенты'; }
function clientActiveFilterChips() { const chips: string[] = []; if (clientsState.filters.search.trim()) chips.push(clearableClientFilterChip(`Поиск: ${escapeHtml(clientsState.filters.search.trim())}`, 'search')); if (clientsState.filters.status !== 'active') chips.push(clearableClientFilterChip(`Статус: ${clientsState.filters.status === 'archived' ? 'Архив' : 'Все'}`, 'status')); return chips.join(''); }
function clearableClientFilterChip(label: string, filter: 'search' | 'status') { return `<span class="tag-chip selected">${label} <button type="button" data-action="clear-client-filter" data-filter="${filter}" aria-label="Убрать фильтр ${label}">×</button></span>`; }
function updateClientFilterSearch(input: HTMLInputElement) { const cursor = input.selectionStart ?? input.value.length; clientsState.filters.search = input.value; render(); const nextInput = document.querySelector<HTMLInputElement>('[data-action="filter-clients-search"]'); if (!nextInput) return; nextInput.focus(); const nextCursor = Math.min(cursor, nextInput.value.length); nextInput.setSelectionRange(nextCursor, nextCursor); }
function updateClientStatusFilter(status: ClientStatusFilter) { clientsState.filters.status = status; clientsState.includeInactive = status !== 'active'; loadClients(true); }
function resetClientFilters() { const shouldReload = clientsState.includeInactive; clientsState.filters = { search: '', status: 'active' }; clientsState.includeInactive = false; if (shouldReload) loadClients(true); else render(); }
function clearClientFilter(filter: string) { if (filter === 'search') { clientsState.filters.search = ''; render(); return; } if (filter === 'status') updateClientStatusFilter('active'); }
function openClientCreateForm() { clientsState.formMode = 'create'; clientsState.showCreateForm = true; clientsState.form = emptyClientForm(); clientCardState = emptyClientCardState(); clientsMessage = ''; clientsError = ''; render(); focusClientName(); }
function hideClientCreateForm() { clientsState.showCreateForm = false; if (clientsState.formMode === 'create') { clientsState.form = emptyClientForm(); clientCardState = emptyClientCardState(); } render(); }

function emptyClientWishForm(): ClientWishFormState { return { title: '', description: '', category: 'other', priority: 'normal', client_recipe_id: '' }; }
function emptyClientFeedbackForm(): ClientFeedbackFormState { return { feedback_type: 'note', sentiment: 'neutral', rating: '', text: '', follow_up_needed: false, follow_up_note: '', occurred_at: '', client_recipe_id: '' }; }
function emptyClientCardState(): ClientCardState { return { clientId: null, wishes: [], feedback: [], recipes: [], includeArchivedWishes: false, wishesStatus: 'idle', feedbackStatus: 'idle', recipesStatus: 'idle', showWishForm: false, showFeedbackForm: false, wishForm: emptyClientWishForm(), feedbackForm: emptyClientFeedbackForm(), wishError: '', feedbackError: '', savingWish: false, savingFeedback: false, changingWishId: null, archivingWishId: null }; }
function syncClientCardDraftFormsFromDom() {
  if (clientCardState.showWishForm) {
    const form = document.querySelector<HTMLFormElement>('[data-form="client-wish"]');
    if (form) {
      const data = new FormData(form);
      clientCardState.wishForm = {
        title: String(data.get('title') ?? '').trim(),
        description: String(data.get('description') ?? '').trim(),
        category: String(data.get('category') ?? 'other'),
        priority: String(data.get('priority') ?? 'normal') as ClientWishPriority,
        client_recipe_id: String(data.get('client_recipe_id') ?? ''),
      };
    }
  }
  if (clientCardState.showFeedbackForm) {
    const form = document.querySelector<HTMLFormElement>('[data-form="client-feedback"]');
    if (form) {
      const data = new FormData(form);
      clientCardState.feedbackForm = {
        feedback_type: String(data.get('feedback_type') ?? 'note'),
        sentiment: String(data.get('sentiment') ?? 'neutral'),
        rating: String(data.get('rating') ?? '').trim(),
        text: String(data.get('text') ?? '').trim(),
        follow_up_needed: data.get('follow_up_needed') === 'on',
        follow_up_note: String(data.get('follow_up_note') ?? '').trim(),
        occurred_at: String(data.get('occurred_at') ?? '').trim(),
        client_recipe_id: String(data.get('client_recipe_id') ?? ''),
      };
    }
  }
}
function loadClientCardData(clientId: number) { clientCardState = { ...emptyClientCardState(), clientId }; render(); refreshClientWishes(); refreshClientFeedback(); clientCardState.recipesStatus = 'loading'; getClientRecipes(true).then((response) => { if (clientCardState.clientId !== clientId) return; syncClientCardDraftFormsFromDom(); clientCardState.recipes = response.client_recipes.filter((recipe) => recipe.client_id === clientId); clientCardState.recipesStatus = 'ready'; render(); }).catch(() => { syncClientCardDraftFormsFromDom(); clientCardState.recipesStatus = 'error'; render(); }); }
function refreshClientWishes() { const clientId = clientCardState.clientId; if (!clientId) return Promise.resolve(); syncClientCardDraftFormsFromDom(); clientCardState.wishesStatus = 'loading'; render(); return fetchClientWishes(clientId, clientCardState.includeArchivedWishes).then((wishes) => { if (clientCardState.clientId !== clientId) return; syncClientCardDraftFormsFromDom(); clientCardState.wishes = wishes; clientCardState.wishesStatus = 'ready'; render(); }).catch(() => { syncClientCardDraftFormsFromDom(); clientCardState.wishesStatus = 'error'; clientCardState.wishError = 'Не удалось загрузить пожелания клиента. Обновите карточку и попробуйте ещё раз.'; render(); }); }
function refreshClientFeedback() { const clientId = clientCardState.clientId; if (!clientId) return Promise.resolve(); syncClientCardDraftFormsFromDom(); clientCardState.feedbackStatus = 'loading'; render(); return fetchClientFeedback(clientId).then((feedback) => { if (clientCardState.clientId !== clientId) return; syncClientCardDraftFormsFromDom(); clientCardState.feedback = feedback; clientCardState.feedbackStatus = 'ready'; render(); }).catch(() => { syncClientCardDraftFormsFromDom(); clientCardState.feedbackStatus = 'error'; clientCardState.feedbackError = 'Не удалось загрузить обратную связь клиента. Обновите карточку и попробуйте ещё раз.'; render(); }); }
function toggleClientWishForm() { if (clientCardState.showWishForm) syncClientCardDraftFormsFromDom(); clientCardState.showWishForm = !clientCardState.showWishForm; clientCardState.wishError = ''; render(); }
function closeClientWishForm() { clientCardState.showWishForm = false; clientCardState.wishForm = emptyClientWishForm(); clientCardState.wishError = ''; render(); }
function toggleArchivedClientWishes() { clientCardState.includeArchivedWishes = !clientCardState.includeArchivedWishes; refreshClientWishes(); }
function submitClientWishForm(event: SubmitEvent) { event.preventDefault(); const clientId = clientCardState.clientId; if (!clientId) return; syncClientCardDraftFormsFromDom(); const form = clientCardState.wishForm; const payload: ClientWishCreatePayload = { title: form.title, description: form.description, category: form.category, priority: form.priority, client_recipe_id: nullableNumber(form.client_recipe_id) }; if (!payload.title) { clientCardState.wishError = 'Укажите краткое пожелание клиента.'; render(); return; } clientCardState.savingWish = true; clientCardState.wishError = ''; render(); createClientWish(clientId, payload).then(() => { clientCardState.showWishForm = false; clientCardState.wishForm = emptyClientWishForm(); clientCardState.savingWish = false; return refreshClientWishes(); }).catch((error) => { syncClientCardDraftFormsFromDom(); clientCardState.savingWish = false; clientCardState.wishError = humanWishFeedbackError(error, 'Не удалось сохранить пожелание. Проверьте поля и попробуйте ещё раз.'); render(); }); }
function changeClientWishStatus(wishId: number, status: ClientWishStatus) { if (!['open','planned','resolved'].includes(status)) return; syncClientCardDraftFormsFromDom(); clientCardState.changingWishId = wishId; clientCardState.wishError = ''; render(); updateClientWishStatus(wishId, status as 'open' | 'planned' | 'resolved').then(() => { syncClientCardDraftFormsFromDom(); clientCardState.changingWishId = null; return refreshClientWishes(); }).catch(() => { syncClientCardDraftFormsFromDom(); clientCardState.changingWishId = null; clientCardState.wishError = 'Не удалось изменить статус пожелания. Обновите карточку клиента и попробуйте ещё раз.'; render(); }); }
function archiveClientWishFromCard(wishId: number) { if (!window.confirm('Архивировать пожелание клиента? Оно останется в истории.')) return; syncClientCardDraftFormsFromDom(); clientCardState.archivingWishId = wishId; clientCardState.wishError = ''; render(); archiveClientWish(wishId).then(() => { syncClientCardDraftFormsFromDom(); clientCardState.archivingWishId = null; return refreshClientWishes(); }).catch(() => { syncClientCardDraftFormsFromDom(); clientCardState.archivingWishId = null; clientCardState.wishError = 'Не удалось архивировать пожелание. Попробуйте ещё раз.'; render(); }); }
function toggleClientFeedbackForm() { if (clientCardState.showFeedbackForm) syncClientCardDraftFormsFromDom(); clientCardState.showFeedbackForm = !clientCardState.showFeedbackForm; clientCardState.feedbackError = ''; render(); }
function closeClientFeedbackForm() { clientCardState.showFeedbackForm = false; clientCardState.feedbackForm = emptyClientFeedbackForm(); clientCardState.feedbackError = ''; render(); }
function submitClientFeedbackForm(event: SubmitEvent) { event.preventDefault(); const clientId = clientCardState.clientId; if (!clientId) return; syncClientCardDraftFormsFromDom(); const form = clientCardState.feedbackForm; const ratingRaw = form.rating.trim(); const payload: ClientFeedbackCreatePayload = { feedback_type: form.feedback_type, sentiment: form.sentiment, rating: ratingRaw ? Number(ratingRaw) : null, text: form.text, follow_up_needed: form.follow_up_needed, follow_up_note: form.follow_up_note, occurred_at: form.occurred_at || null, client_recipe_id: nullableNumber(form.client_recipe_id) }; if (!payload.text) { clientCardState.feedbackError = 'Запишите текст отзыва клиента.'; render(); return; } clientCardState.savingFeedback = true; clientCardState.feedbackError = ''; render(); createClientFeedback(clientId, payload).then(() => { clientCardState.showFeedbackForm = false; clientCardState.feedbackForm = emptyClientFeedbackForm(); clientCardState.savingFeedback = false; return refreshClientFeedback(); }).catch((error) => { syncClientCardDraftFormsFromDom(); clientCardState.savingFeedback = false; clientCardState.feedbackError = humanWishFeedbackError(error, 'Не удалось сохранить отзыв. Проверьте поля и попробуйте ещё раз.'); render(); }); }
function nullableNumber(value: string) { const trimmed = value.trim(); return trimmed ? Number(trimmed) : null; }
function humanWishFeedbackError(error: unknown, fallback: string) { const message = error instanceof Error ? error.message : ''; if (message.toLowerCase().includes('client') && message.toLowerCase().includes('recipe')) return 'Выбранный индивидуальный рецепт не относится к этому клиенту. Обновите карточку клиента и выберите рецепт ещё раз.'; return fallback; }
function clientRecipeLinkSelect(current: string) { const recipes = clientCardState.recipes; const options = [`<option value="">Без связи с индивидуальным рецептом</option>`, ...recipes.map((recipe) => `<option value="${recipe.id}" ${current === String(recipe.id) ? 'selected' : ''}>${escapeHtml(recipe.title)}${recipe.is_active ? '' : ' · архив'}</option>`)]; return `<label class="full-span">Индивидуальный рецепт<select name="client_recipe_id">${options.join('')}</select></label>`; }
function clientCardRecipeTitle(id: number) { return clientCardState.recipes.find((recipe) => recipe.id === id)?.title ?? 'индивидуальный рецепт'; }
function clientWishStatusLabel(value: string) { return ({ open: 'Открыто', planned: 'Запланировано', resolved: 'Учтено', archived: 'В архиве' } as Record<string,string>)[value] ?? 'Открыто'; }
function clientWishPriorityLabel(value: string) { return ({ low: 'Низкий', normal: 'Обычный', high: 'Важный' } as Record<string,string>)[value] ?? 'Обычный'; }
function clientWishCategoryLabel(value: string) { return ({ texture: 'Текстура', scent: 'Аромат', packaging: 'Упаковка', ingredient: 'Ингредиент', allergy: 'Аллергия', contraindication: 'Ограничение', effect: 'Эффект', price: 'Цена', other: 'Другое' } as Record<string,string>)[value] ?? 'Другое'; }
function clientFeedbackTypeLabel(value: string) { return ({ note: 'Заметка', reaction: 'Реакция', texture: 'Текстура', scent: 'Аромат', effect: 'Эффект', packaging: 'Упаковка', request: 'Просьба', other: 'Другое' } as Record<string,string>)[value] ?? 'Другое'; }
function clientFeedbackSentimentLabel(value: string) { return ({ positive: 'Положительный', neutral: 'Нейтральный', negative: 'Негативный', mixed: 'Смешанный' } as Record<string,string>)[value] ?? 'Нейтральный'; }
function clientWishCategoryOptions(current: string) { return ['texture','scent','packaging','ingredient','allergy','contraindication','effect','price','other'].map((v)=>`<option value="${v}" ${current===v?'selected':''}>${clientWishCategoryLabel(v)}</option>`).join(''); }
function clientWishPriorityOptions(current: string) { return ['low','normal','high'].map((v)=>`<option value="${v}" ${current===v?'selected':''}>${clientWishPriorityLabel(v)}</option>`).join(''); }
function clientFeedbackTypeOptions(current: string) { return ['note','reaction','texture','scent','effect','packaging','request','other'].map((v)=>`<option value="${v}" ${current===v?'selected':''}>${clientFeedbackTypeLabel(v)}</option>`).join(''); }
function clientFeedbackSentimentOptions(current: string) { return ['positive','neutral','negative','mixed'].map((v)=>`<option value="${v}" ${current===v?'selected':''}>${clientFeedbackSentimentLabel(v)}</option>`).join(''); }
function closeClientEdit() { clientsState.formMode = 'create'; clientsState.showCreateForm = false; clientsState.form = emptyClientForm(); clientCardState = emptyClientCardState(); clientsMessage = ''; clientsError = ''; render(); }
function focusClientName() { requestAnimationFrame(() => document.querySelector<HTMLInputElement>('[data-field="client-full-name"]')?.focus()); }
function loadClients(force = false) { if (!force && (clientsStatus === 'loading' || clientsStatus === 'ready')) return; clientsStatus = 'loading'; clientsError = ''; render(); getClients(clientsState.includeInactive).then((response) => { clientsState.items = response.clients; clientsStatus = 'ready'; render(); }).catch(() => { clientsStatus = 'error'; clientsError = 'Не удалось загрузить клиентов. Проверьте, что локальное приложение запущено.'; render(); }); }
function startEditClient(id: number) { const client = clientsState.items.find((item) => item.id === id); if (!client) return; clientsState.formMode = 'edit'; clientsState.showCreateForm = false; clientsState.form = { id: client.id, full_name: client.full_name, phone: client.phone, email: client.email, address: client.address, birthday: client.birthday, skin_notes: client.skin_notes, allergy_notes: client.allergy_notes, preference_notes: client.preference_notes, contraindication_notes: client.contraindication_notes, notes: client.notes }; clientsMessage = ''; clientsError = ''; loadClientCardData(id); render(); focusClientName(); }
function submitClientForm(event: SubmitEvent) {
  event.preventDefault();
  const isEdit = Boolean(clientsState.formMode === 'edit' && clientsState.form.id);
  if (isEdit) syncClientCardDraftFormsFromDom();
  const payload = clientPayloadFromForm(event.currentTarget as HTMLFormElement);
  if (!payload.full_name) {
    if (isEdit) syncClientCardDraftFormsFromDom();
    clientsMessage = '';
    clientsError = 'Укажите ФИО клиента, например «Анна Иванова».';
    render();
    return;
  }
  const request = isEdit ? updateClient(clientsState.form.id!, payload) : createClient(payload);
  request
    .then((client) => {
      clientsMessage = isEdit ? 'Карточка клиента обновлена.' : 'Клиент создан.';
      clientsError = '';
      clientsState.formMode = isEdit ? 'edit' : 'create';
      clientsState.showCreateForm = false;
      clientsState.form = isEdit ? { ...payload, id: client.id } : emptyClientForm();
      return getClients(clientsState.includeInactive);
    })
    .then((response) => {
      if (isEdit) syncClientCardDraftFormsFromDom();
      clientsState.items = response.clients;
      clientsStatus = 'ready';
      render();
    })
    .catch(() => {
      if (isEdit) syncClientCardDraftFormsFromDom();
      clientsMessage = '';
      clientsError = 'Не удалось сохранить клиента. Проверьте ФИО и контактные поля, затем попробуйте еще раз.';
      clientsStatus = 'ready';
      render();
    });
}
function deactivateClient(id: number) { const client = clientsState.items.find((item) => item.id === id); if (!client || !window.confirm('Архивировать клиента? Карточка останется в истории, но не будет отображаться в активном списке.')) return; deactivateClientRequest(id).then(() => { clientsMessage = 'Клиент архивирован.'; clientsError = ''; return getClients(clientsState.includeInactive); }).then((response) => { clientsState.items = response.clients; clientsStatus = 'ready'; if (clientsState.form.id === id) { clientsState.formMode = 'create'; clientsState.showCreateForm = false; clientsState.form = emptyClientForm(); } render(); }).catch(() => { clientsMessage = ''; clientsError = 'Не удалось архивировать клиента. Попробуйте еще раз.'; clientsStatus = 'ready'; render(); }); }


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

function packagingKindValues() { return ['jar','bottle','tube','pump','cap','dropper','label','box','bag','other']; }
function filteredPackagingItems() { return filterCatalogItems(packagingItemsState.items, packagingItemsState.filters, { getSearchText: packagingSearchText, getCatalogCategoryId: (item) => item.catalog_category_id, getCatalogTagIds: (item) => item.catalog_tag_ids, getSystemType: (item) => item.kind, getIsActive: (item) => item.is_active }); }
function packagingSearchText(item: PackagingItem) { return [item.name, item.notes, item.supplier_hint, item.material, packagingKindLabel(item.kind), item.kind].join(' '); }
function updatePackagingFilterSearch(input: HTMLInputElement) { const cursor = input.selectionStart ?? input.value.length; packagingItemsState.filters.search = input.value; render(); const nextInput = document.querySelector<HTMLInputElement>('[data-action="filter-packaging-search"]'); if (!nextInput) return; nextInput.focus(); const nextCursor = Math.min(cursor, nextInput.value.length); nextInput.setSelectionRange(nextCursor, nextCursor); }
function addPackagingTagFilter(value: string) { const id = Number(value); if (!id || packagingItemsState.filters.tagIds.includes(id)) return; packagingItemsState.filters.tagIds = [...packagingItemsState.filters.tagIds, id]; render(); }
function removePackagingTagFilter(id: number) { packagingItemsState.filters.tagIds = packagingItemsState.filters.tagIds.filter((tagId) => tagId !== id); render(); }
function clearPackagingFilter(filter: string) { if (filter === 'search') packagingItemsState.filters.search = ''; if (filter === 'category') packagingItemsState.filters.categoryId = ''; if (filter === 'kind') packagingItemsState.filters.systemType = ''; if (filter === 'status') packagingItemsState.filters.status = 'active'; render(); }
function clearablePackagingFilterChip(label: string, filter: 'search' | 'category' | 'kind' | 'status') { return `<span class="tag-chip selected">${label} <button type="button" data-action="clear-packaging-filter" data-filter="${filter}" aria-label="Убрать фильтр ${label}">×</button></span>`; }
function packagingActiveFilterChips() { const f = packagingItemsState.filters; const chips: string[] = []; if (f.search.trim()) chips.push(clearablePackagingFilterChip(`Поиск: ${escapeHtml(f.search.trim())}`, 'search')); if (f.categoryId === 'none') chips.push(clearablePackagingFilterChip('Группа: Без группы', 'category')); if (typeof f.categoryId === 'number') chips.push(clearablePackagingFilterChip(`Группа: ${escapeHtml(packagingItemsState.catalogCategories.find((category) => category.id === f.categoryId)?.name ?? 'Выбранная группа')}`, 'category')); if (f.systemType) chips.push(clearablePackagingFilterChip(`Тип тары: ${packagingKindLabel(f.systemType)}`, 'kind')); if (f.status !== 'active') chips.push(clearablePackagingFilterChip(`Статус: ${f.status === 'archived' ? 'Архив' : 'Все'}`, 'status')); return chips.join(''); }


function filteredRecipeTemplates() { return filterCatalogItems(recipesState.templates, recipesState.filters, { getSearchText: recipeSearchText, getCatalogCategoryId: (item) => item.catalog_category_id, getCatalogTagIds: (item) => item.catalog_tag_ids, getSystemType: () => '', getIsActive: (item) => item.is_active }); }
function recipeSearchText(item: RecipeTemplate) { return [item.name, item.product_type, item.description, item.notes, item.is_active ? 'активен active' : 'неактивен архив archived', recipeCatalogCategoryLabel(item), item.catalog_tag_ids.map((id) => recipesState.catalogTags.find((tag) => tag.id === id)?.name ?? '').join(' ')].join(' '); }
function updateRecipeFilterSearch(input: HTMLInputElement) { const cursor = input.selectionStart ?? input.value.length; recipesState.filters.search = input.value; render(); const nextInput = document.querySelector<HTMLInputElement>('[data-action="filter-recipes-search"]'); if (!nextInput) return; nextInput.focus(); const nextCursor = Math.min(cursor, nextInput.value.length); nextInput.setSelectionRange(nextCursor, nextCursor); }
function clearRecipeFilter(filter: string) { if (filter === 'search') recipesState.filters.search = ''; if (filter === 'category') recipesState.filters.categoryId = ''; if (filter === 'status') recipesState.filters.status = 'active'; render(); }
function clearableRecipeFilterChip(label: string, filter: 'search' | 'category' | 'status') { return `<span class="tag-chip selected">${label} <button type="button" data-action="clear-recipe-filter" data-filter="${filter}" aria-label="Убрать фильтр ${label}">×</button></span>`; }
function recipeActiveFilterChips() { const f = recipesState.filters; const chips: string[] = []; if (f.search.trim()) chips.push(clearableRecipeFilterChip(`Поиск: ${escapeHtml(f.search.trim())}`, 'search')); if (f.categoryId === 'none') chips.push(clearableRecipeFilterChip('Группа: Без группы', 'category')); if (typeof f.categoryId === 'number') chips.push(clearableRecipeFilterChip(`Группа: ${escapeHtml(recipesState.catalogCategories.find((category) => category.id === f.categoryId)?.name ?? 'Выбранная группа')}`, 'category')); if (f.status !== 'active') chips.push(clearableRecipeFilterChip(`Статус: ${f.status === 'archived' ? 'Неактивные' : 'Все'}`, 'status')); return chips.join(''); }
function openRecipeCreateForm() { recipesState.showCreateForm = true; recipesState.selectedTemplate = null; recipesState.versions = []; recipesState.selectedVersionDetail = null; recipesState.versionDetailStatus = 'idle'; recipesState.calculation = null; calculationStatus = 'idle'; recipesMessage = ''; recipesError = ''; render(); focusRecipeTemplateName(); }
function hideRecipeCreateForm() { saveRecipeTemplateFormFromDom(); recipesState.showCreateForm = false; recipesMessage = ''; recipesError = ''; render(); }
function closeRecipeDetail() { recipesState.versionForm = emptyRecipeVersionForm(); recipesState.selectedTemplate = null; recipesState.versions = []; recipesState.selectedVersionDetail = null; recipesState.versionDetailStatus = 'idle'; recipesState.calculation = null; calculationStatus = 'idle'; recipesMessage = ''; recipesError = ''; render(); }
function focusRecipeTemplateName() { requestAnimationFrame(() => document.querySelector<HTMLInputElement>('[data-field="recipe-template-name"]')?.focus()); }
function saveRecipeTemplateFormFromDom() { const form = document.querySelector<HTMLFormElement>('[data-form="recipe-template"]'); if (!form) return; recipesState.templateForm = recipeTemplatePayloadFromForm(form); }

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
function clientRecipePhaseOptions(current: string) { const standard = ['A','B','C','D']; const selected = current || 'A'; const options = standard.map((phase) => `<option value="${phase}" ${selected===phase?'selected':''}>Фаза ${phase}</option>`); if (selected && !standard.includes(selected)) options.push(`<option value="${escapeHtml(selected)}" selected>${escapeHtml(selected)} · текущая фаза</option>`); return options.join(''); }
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

function apiGet<T>(url: string): Promise<T> { return fetch(url).then(async (response) => { if (!response.ok) { let payload: unknown = null; try { payload = await response.json(); } catch { payload = null; } throw Object.assign(new Error(apiErrorMessage(payload)), { status: response.status }); } return response.json() as Promise<T>; }); }
function apiErrorMessage(payload: unknown) { if (typeof payload === 'string') return payload; if (payload && typeof payload === 'object' && 'detail' in payload) { const detail = (payload as { detail?: unknown }).detail; if (typeof detail === 'string') return detail; if (detail && typeof detail === 'object' && 'message' in detail) return String((detail as { message?: unknown }).message ?? 'API request failed'); } return 'API request failed'; }
function apiSend<T>(url: string, method: 'POST' | 'PUT', body?: unknown): Promise<T> { return fetch(url, { method, headers: body ? { 'Content-Type': 'application/json' } : undefined, body: body ? JSON.stringify(body) : undefined }).then(async (response) => { if (!response.ok) { let payload: unknown = null; try { payload = await response.json(); } catch { payload = null; } throw Object.assign(new Error(apiErrorMessage(payload)), { status: response.status }); } return response.json() as Promise<T>; }); }
function getAlerts(filters: AlertsState['filters']): Promise<AlertListResponse> { const params = new URLSearchParams({ status: filters.status, limit: '100', offset: '0' }); if (filters.type) params.set('type', filters.type); return apiGet<AlertListResponse>(`/api/alerts?${params.toString()}`); }
function regenerateAlerts(): Promise<AlertGenerationResponse> { return apiSend<AlertGenerationResponse>('/api/alerts/regenerate', 'POST'); }
function resolveAlert(id: number): Promise<AlertResponse> { return apiSend<AlertResponse>(`/api/alerts/${id}/resolve`, 'POST'); }
function dismissAlert(id: number): Promise<AlertResponse> { return apiSend<AlertResponse>(`/api/alerts/${id}/dismiss`, 'POST'); }
function getProductionBatches() { return apiGet<{ production_batches: ProductionBatchListItem[]; limit: number; offset: number }>('/api/production-batches'); }
function getProductionBatch(batchId: number) { return apiGet<ProductionBatchDetailResponse>(`/api/production-batches/${batchId}`); }
function getProductionBatchByOrder(orderId: number) { return apiGet<ProductionBatchDetailResponse>(`/api/orders/${orderId}/production-batch`); }
function getOrders(includeInactive = true) { return apiGet<{ orders: Order[] }>(`/api/orders?include_inactive=${includeInactive ? 'true' : 'false'}`); }
function getOrder(id: number) { return apiGet<Order>(`/api/orders/${id}`); }
function createOrder(payload: OrderPayload) { return apiSend<Order>('/api/orders', 'POST', payload); }
function updateOrder(id: number, payload: OrderPayload) { return apiSend<Order>(`/api/orders/${id}`, 'PUT', payload); }
function cancelOrderRequest(id: number) { return apiSend<Order>(`/api/orders/${id}/cancel`, 'POST'); }
function archiveOrderRequest(id: number) { return apiSend<Order>(`/api/orders/${id}/archive`, 'POST'); }
function checkOrderProductionReadiness(orderId: number): Promise<ProductionReadinessResponse> { return apiSend<ProductionReadinessResponse>(`/api/orders/${orderId}/check-production-readiness`, 'POST'); }
function produceOrder(orderId: number, notes?: string): Promise<ProductionBatchDetailResponse> { return apiSend<ProductionBatchDetailResponse>(`/api/orders/${orderId}/produce`, 'POST', { confirm: true, notes: notes?.trim() || null }); }
function getClients(includeInactive = false) { return apiGet<{ clients: Client[] }>(`/api/clients${includeInactive ? '?include_inactive=true' : ''}`); }
function getClientRecipes(includeInactive = false) { return apiGet<{ client_recipes: ClientRecipe[] }>(`/api/client-recipes?include_inactive=${includeInactive ? 'true' : 'false'}`); }
function getClientRecipe(id: number) { return apiGet<ClientRecipeDetail>(`/api/client-recipes/${id}`); }
function fetchClientWishes(clientId: number, includeInactive = false) { return apiGet<{ wishes: ClientWish[] }>(`/api/clients/${clientId}/wishes?include_inactive=${includeInactive ? 'true' : 'false'}`).then((response) => response.wishes); }
function createClientWish(clientId: number, payload: ClientWishCreatePayload) { return apiSend<ClientWish>(`/api/clients/${clientId}/wishes`, 'POST', payload); }
function updateClientWishStatus(wishId: number, status: 'open' | 'planned' | 'resolved') { return apiSend<ClientWish>(`/api/client-wishes/${wishId}/status`, 'PUT', { status }); }
function archiveClientWish(wishId: number) { return apiSend<ClientWish>(`/api/client-wishes/${wishId}/archive`, 'POST'); }
function fetchClientFeedback(clientId: number) { return apiGet<{ feedback: ClientFeedback[] }>(`/api/clients/${clientId}/feedback`).then((response) => response.feedback); }
function createClientFeedback(clientId: number, payload: ClientFeedbackCreatePayload) { return apiSend<ClientFeedback>(`/api/clients/${clientId}/feedback`, 'POST', payload); }
function createClientRecipe(payload: ClientRecipePayload) { return apiSend<ClientRecipeDetail>('/api/client-recipes', 'POST', payload); }
function updateClientRecipeIngredients(clientRecipeId: number, ingredients: ClientRecipeIngredientUpdatePayload[]) { return apiSend<ClientRecipeDetail>(`/api/client-recipes/${clientRecipeId}/ingredients`, 'PUT', { ingredients }); }
function deactivateClientRecipeRequest(id: number) { return apiSend<ClientRecipe>(`/api/client-recipes/${id}/deactivate`, 'POST'); }
function restoreClientRecipeRequest(id: number) { return apiSend<ClientRecipe>(`/api/client-recipes/${id}/restore`, 'POST'); }
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
  saveRecipeTemplateFormFromDom();
  recipesState.showCreateForm = false;
  recipesError = ''; recipesMessage = '';
  Promise.all([getRecipeTemplate(id), getRecipeVersions(id)]).then(([template, versions]) => { recipesState.selectedTemplate = template; recipesState.versions = versions.recipe_versions; recipesState.selectedVersionDetail = null; recipesState.versionDetailStatus = 'idle'; recipesState.calculation = null; calculationStatus = 'idle'; render(); }).catch(() => { recipesError = 'Не удалось открыть рецепт. Попробуйте обновить страницу.'; render(); });
}
function openRecipeVersion(id: number) { recipesError = ''; calculationError = ''; recipesState.versionDetailStatus = 'loading'; recipesState.calculation = null; calculationStatus = 'loading'; render(); getRecipeVersionDetail(id).then((detail)=>{ recipesState.selectedVersionDetail = detail; recipesState.versionDetailStatus = 'ready'; recipesState.calculationTargetValue = detail.version.target_batch_size_value ?? ''; recipesState.calculationTargetUnit = detail.version.target_batch_size_unit === 'ml' ? 'ml' : 'g'; render(); return getRecipeCalculation(detail.version.id, recipesState.calculationTargetValue, recipesState.calculationTargetUnit); }).then((result)=>{ recipesState.calculation = result; calculationStatus = 'ready'; render(); }).catch(()=>{ if (recipesState.versionDetailStatus === 'ready') { calculationStatus = 'error'; calculationError = 'Не удалось выполнить расчет. Состав версии открыт, попробуйте пересчитать позже.'; } else { recipesState.versionDetailStatus = 'error'; calculationStatus = 'idle'; recipesError = 'Не удалось загрузить версию рецепта.'; } render(); }); }
function submitRecipeTemplateForm(event: SubmitEvent) { event.preventDefault(); const payload = recipeTemplatePayloadFromForm(event.currentTarget as HTMLFormElement); recipesState.templateForm = payload; createRecipeTemplate(payload).then((template)=>{ recipesMessage = 'Рецепт создан.'; recipesError = ''; recipesState.templateForm = emptyRecipeTemplateForm(); recipesState.showCreateForm = false; return getRecipeTemplates().then((response)=>({template, response})); }).then(({template, response})=>{ recipesState.templates = response.recipe_templates; recipesStatus = 'ready'; openRecipeTemplate(template.id); }).catch(()=>{ recipesMessage = ''; recipesError = 'Не удалось создать рецепт. Проверьте название и попробуйте еще раз.'; recipesStatus = 'ready'; render(); }); }
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
  packagingItemsState.formMode = 'edit'; packagingItemsState.showCreateForm = false; packagingItemsState.form = { id: item.id, name: item.name, kind: item.kind, unit: item.unit, capacity_value: item.capacity_value, capacity_unit: item.capacity_unit, material: item.material, supplier_hint: item.supplier_hint, unit_cost: item.unit_cost, notes: item.notes }; packagingItemsState.assignmentDraft = assignmentDraftFromItem(item); packagingItemsMessage = ''; packagingItemsError = ''; render(); focusPackagingFormName();
}
function openPackagingCreateForm() {
  const current = packagingItemsState.formMode === 'edit' && packagingItemsState.form.id ? packagingItemsState.items.find((packagingItem) => packagingItem.id === packagingItemsState.form.id) ?? null : null;
  if (!confirmDiscardDirtyAssignment(assignmentDraftIsDirty(current, packagingItemsState.assignmentDraft))) return;
  packagingItemsState.formMode = 'create'; packagingItemsState.showCreateForm = true; packagingItemsState.form = emptyPackagingItemForm(); packagingItemsState.assignmentDraft = emptyAssignmentDraft(); packagingItemsMessage = ''; packagingItemsError = ''; render(); focusPackagingFormName();
}
function hidePackagingCreateForm() {
  packagingItemsState.formMode = 'create'; packagingItemsState.showCreateForm = false; packagingItemsState.form = emptyPackagingItemForm(); packagingItemsState.assignmentDraft = emptyAssignmentDraft(); packagingItemsMessage = ''; packagingItemsError = ''; render();
}
function focusPackagingFormName() {
  requestAnimationFrame(() => {
    const section = document.querySelector<HTMLElement>('[data-section="packaging-form"]');
    section?.scrollIntoView({ block: 'start', behavior: 'smooth' });
    section?.querySelector<HTMLInputElement>('input[name="name"]')?.focus();
  });
}
function cancelPackagingEdit() {
  const current = packagingItemsState.formMode === 'edit' && packagingItemsState.form.id ? packagingItemsState.items.find((packagingItem) => packagingItem.id === packagingItemsState.form.id) ?? null : null;
  if (!confirmDiscardDirtyAssignment(assignmentDraftIsDirty(current, packagingItemsState.assignmentDraft))) return;
  packagingItemsState.formMode = 'create'; packagingItemsState.showCreateForm = false; packagingItemsState.form = emptyPackagingItemForm(); packagingItemsState.assignmentDraft = emptyAssignmentDraft(); packagingItemsMessage = ''; packagingItemsError = ''; render();
}
function submitPackagingItemForm(event: SubmitEvent) {
  event.preventDefault();
  const payload = packagingItemPayloadFromForm(event.currentTarget as HTMLFormElement);
  const request = packagingItemsState.formMode === 'edit' && packagingItemsState.form.id ? updatePackagingItem(packagingItemsState.form.id, payload) : createPackagingItem(payload);
  request.then(() => { packagingItemsMessage = packagingItemsState.formMode === 'edit' ? 'Тара сохранена. Остатки не изменялись.' : 'Тара создана. Остатки добавляются отдельными складскими операциями.'; packagingItemsError = ''; packagingItemsState.formMode = 'create'; packagingItemsState.showCreateForm = false; packagingItemsState.form = emptyPackagingItemForm(); return getPackagingItems(); }).then((response) => { packagingItemsState.items = response.packaging_items; packagingItemsStatus = 'ready'; render(); }).catch(() => { packagingItemsMessage = ''; packagingItemsError = 'Не удалось сохранить тару. Проверьте название, тип, единицы и числовые поля.'; packagingItemsStatus = 'ready'; render(); });
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
