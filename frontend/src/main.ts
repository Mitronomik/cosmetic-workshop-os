import { clearFieldValidation, clearIndexedCollectionValidation, emptyFormValidationState, normalizeBackendValidation, type FormValidationState } from './form-validation.js';
import { applyValidationToClientForm, applyValidationToIngredientForm, applyValidationToIngredientLotForm, applyValidationToPackagingItemForm, applyValidationToRecipeTemplateForm, applyValidationToRecipeVersionForm, applyValidationToStockMovementForm } from './targeted-validation-update.js';
import { createRecipeMutationLifecycle, createStockMovementLotDetailLifecycle, disableRecipeTemplateMutationControls, disableRecipeVersionMutationControls, mutationDisabled, mutationReadonly, restoreMutationGuards, restoreRecipeMutationControls, packagingPageMutationActiveState, type StockMovementLotDetailRequest } from './mutation-lifecycle.js';
type FeedbackTone = 'neutral' | 'success' | 'warning' | 'error';
const feedbackToneLabels: Record<FeedbackTone, string> = { neutral: 'Сообщение', success: 'Готово', warning: 'Внимание', error: 'Не удалось' };

function feedbackMessage(tone: FeedbackTone, message: string, details = '') {
  const safeMessage = escapeHtml(message);
  return `<div class="feedback-message feedback-message--${tone}" data-feedback-tone="${tone}"><strong class="feedback-message__label">${feedbackToneLabels[tone]}</strong><div class="feedback-message__body"><p>${safeMessage}</p>${details}</div></div>`;
}

function ensureAnnouncementRegions() {
  let container = document.querySelector<HTMLElement>('[data-announcement-regions]');
  if (!container) {
    container = document.createElement('div');
    container.className = 'visually-hidden';
    container.dataset.announcementRegions = 'true';
    container.innerHTML = '<div data-announcer="polite" role="status" aria-atomic="true"></div><div data-announcer="assertive" role="alert" aria-atomic="true"></div>';
    document.body.appendChild(container);
  }
}

function announcer(kind: 'polite' | 'assertive') {
  ensureAnnouncementRegions();
  return document.querySelector<HTMLElement>(`[data-announcer="${kind}"]`);
}

function clearFeedbackAnnouncement() {
  announcer('polite')!.textContent = '';
  announcer('assertive')!.textContent = '';
}

function announcePolite(message: string) {
  const polite = announcer('polite');
  const assertive = announcer('assertive');
  if (!polite || !assertive) return;
  assertive.textContent = '';
  if (polite.textContent === message) return;
  polite.textContent = message;
}

function announceAssertive(message: string) {
  const polite = announcer('polite');
  const assertive = announcer('assertive');
  if (!polite || !assertive) return;
  polite.textContent = '';
  if (assertive.textContent === message) return;
  assertive.textContent = message;
}
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

type SettingStatus = 'editable_now' | 'read_only_now' | 'safe_mvp_candidate' | 'requires_backend_rules' | 'v2_or_later' | 'not_mvp';
type SettingsCapabilityStatus = 'ready' | 'available' | 'planned' | 'disabled';
type AppSettingsInfo = { product_name: string; repository_name: string | null; mode: string; local_first: boolean; internet_required: boolean; version?: string | null };
type LocalDataStatus = { user_data_separate_from_code: boolean; user_data_path_available: boolean; user_data_path_display: string | null; backup_before_migration_required: boolean; message: string };
type SettingsCapability = { id: string; title: string; status: SettingsCapabilityStatus; route: string | null; description: string; mutates_from_settings: boolean };
type SettingsDefinition = { id: string; title: string; status: SettingStatus; affects_calculations: boolean; affects_historical_data: boolean; requires_backend_service: boolean; description: string; safety_note: string };
type SettingsGroup = { id: string; title: string; description: string; items: SettingsDefinition[] };
type SettingsWarning = { code: string; message: string; severity: 'info' | 'warning' };
type SettingsStatusResponse = { generated_at: string; app: AppSettingsInfo; local_data: LocalDataStatus; capabilities: SettingsCapability[]; setting_groups: SettingsGroup[]; editable_settings_available: boolean; message: string; warnings: SettingsWarning[] };
type SettingsUiState = { status: 'idle' | 'loading' | 'ready' | 'error'; data: SettingsStatusResponse | null; error: string };
type WorkshopProfile = { workshop_name: string; master_name: string; workshop_contact_text: string; workshop_note: string };
type WorkshopProfileResponse = { profile: WorkshopProfile; is_configured: boolean; updated_at: string | null; message: string };
type WorkshopProfileUiState = { status: 'idle' | 'loading' | 'ready' | 'error'; actionStatus: 'idle' | 'saving'; profile: WorkshopProfile | null; draft: WorkshopProfile; error: string; message: string };

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
type DashboardStatus = 'idle' | 'loading' | 'ready' | 'error';
type DashboardState = { status: DashboardStatus; error: string; message: string; orders: Order[]; clients: Client[]; alerts: AlertResponse[]; purchaseSuggestions: PurchaseSuggestionResponse[]; productionBatches: ProductionBatchListItem[] };
type BackupFileResponse = { filename: string; path: string; created_at: string | null; reason: string | null; size_bytes: number };
type BackupStatusResponse = { database_path: string; database_exists: boolean; database_size_bytes: number | null; backup_dir: string; backup_dir_exists: boolean; backup_count: number; latest_backup: BackupFileResponse | null };
type BackupListResponse = { backups: BackupFileResponse[]; backup_dir: string };
type BackupCreateRequest = { reason?: string | null };
type BackupCreateResponse = { backup: BackupFileResponse; database_path: string; backup_dir: string; message: string };
type BackupUiState = { status: 'idle' | 'loading' | 'ready' | 'error'; actionStatus: 'idle' | 'creating'; error: string; message: string; backupStatus: BackupStatusResponse | null; backups: BackupFileResponse[]; reason: string; customReason: string; lastCreatedBackup: BackupFileResponse | null };
type ExportFileResponse = { filename: string; path: string; created_at: string | null; reason: string | null; size_bytes: number };
type ExportStatusResponse = { database_path: string; database_exists: boolean; database_size_bytes: number | null; export_dir: string; export_dir_exists: boolean; export_count: number; latest_export: ExportFileResponse | null };
type ExportListResponse = { exports: ExportFileResponse[]; export_dir: string };
type ExportCreateRequest = { reason?: string | null };
type ExportCreateResponse = { export: ExportFileResponse; database_path: string; export_dir: string; entity_counts: Record<string, number>; message: string };
type ExportUiState = { status: 'idle' | 'loading' | 'ready' | 'error'; actionStatus: 'idle' | 'creating'; error: string; message: string; exportStatus: ExportStatusResponse | null; exports: ExportFileResponse[]; reason: string; customReason: string; lastCreatedExport: ExportFileResponse | null; lastEntityCounts: Record<string, number> };
type DemoDataInstallRequest = { confirm_install: boolean; understand_demo_data: boolean };
type DemoDataClearRequest = { confirm_clear: boolean };
type DemoDataStatusResponse = { is_installed: boolean; active_session_id: number | null; demo_version: string; can_install: boolean; can_clear: boolean; has_business_data: boolean; has_non_demo_business_data: boolean; created_counts: Record<string, number>; blocking_reasons: string[]; message: string };
type DemoDataInstallResponse = { session_id: number; demo_version: string; created_counts: Record<string, number>; message: string };
type DemoDataClearResponse = { session_id: number; deleted_counts: Record<string, number>; message: string };
type DemoDataUiState = { status: 'idle' | 'loading' | 'ready' | 'error'; actionStatus: 'idle' | 'installing' | 'clearing'; error: string; message: string; demoStatus: DemoDataStatusResponse | null; installConfirmChecked: boolean; understandDemoChecked: boolean; clearConfirmChecked: boolean; showInstallConfirm: boolean; showClearConfirm: boolean; lastInstallResult: DemoDataInstallResponse | null; lastClearResult: DemoDataClearResponse | null };

type ImportTargetResponse = { type: string; label: string; required_columns: string[]; optional_columns: string[] };
type ImportTargetsResponse = { targets: ImportTargetResponse[] };
type ImportApplyReadiness = { can_apply: boolean; status: string; blocking_error_count: number; warning_count: number; valid_row_count: number; invalid_row_count: number; blocking_reasons: string[]; warnings: string[]; next_action: string };
type ImportDraftSummary = { id: number; source_id: number; target_type: string; status: string; row_count: number; valid_row_count: number; invalid_row_count: number; warning_count: number; error_count: number; headers: string[]; summary?: Record<string, unknown>; apply_readiness?: ImportApplyReadiness; created_at: string; updated_at?: string | null };
type ImportIssue = { severity: 'info' | 'warning' | 'error' | string; code: string; message: string; row_number: number | null; field: string | null };
type ApiIssue = { severity?: string; code?: string; message?: string; row_number?: number | null; field?: string | null };
type ApiErrorWithDetails = Error & { status?: number; issues?: ApiIssue[]; payload?: unknown };
type ImportPreviewRow = { id?: number; row_number: number; raw_values: Record<string, unknown>; normalized_values: Record<string, unknown>; issues: ImportIssue[]; status: string };
type ImportDraftCreateResponse = { draft: ImportDraftSummary; preview_rows: ImportPreviewRow[]; issues: ImportIssue[]; message: string };
type ImportDraftListParams = { status?: string; targetType?: string; limit?: number; offset?: number };
type ImportDraftListResponse = { drafts: ImportDraftSummary[]; limit?: number; offset?: number; total?: number };
type ImportSourceResponse = { id: number; original_filename: string; content_type: string | null; file_extension: string; file_size_bytes: number; target_type: string; status: string; created_at: string };
type ImportDraftDetailResponse = { draft: ImportDraftSummary; source: ImportSourceResponse; preview_rows: ImportPreviewRow[]; issues: ImportIssue[]; limit?: number; offset?: number; total_rows?: number };
type ImportDraftCancelResponse = { draft: ImportDraftSummary; message: string };
type ImportDraftApplyRequest = { confirm_apply: boolean; backup_acknowledged: boolean; allow_warnings?: boolean };
type ImportApplyCreatedRecordResponse = { target_type: string; row_number: number; record_id: number; label: string };
type ImportDraftApplyResultResponse = { draft_id: number; target_type: string; applied_at: string; applied_row_count: number; created_count: number; created_records: ImportApplyCreatedRecordResponse[]; warnings: string[] };
type ImportDraftApplyResponse = { draft: ImportDraftSummary; apply_result: ImportDraftApplyResultResponse; message: string };
type ImportUiState = { status: 'idle' | 'loading' | 'ready' | 'error'; actionStatus: 'idle' | 'uploading' | 'cancelling'; applyStatus: 'idle' | 'confirming' | 'applying' | 'success' | 'error'; error: string; message: string; applyError: string; applyErrorIssues: ApiIssue[]; applyMessage: string; applyRefreshWarning: string; applyConfirmChecked: boolean; backupAcknowledged: boolean; allowWarnings: boolean; lastApplyResult: ImportDraftApplyResultResponse | null; showApplyConfirm: boolean; targets: ImportTargetResponse[]; drafts: ImportDraftSummary[]; selectedDraft: ImportDraftDetailResponse | null; selectedDraftStatus: 'idle' | 'loading' | 'ready' | 'error'; selectedDraftError: string; selectedTargetType: string; selectedFileName: string; filters: { status: string; targetType: string } };
const APPLY_SUPPORTED_IMPORT_TARGETS = new Set(['ingredients', 'clients', 'recipe_templates', 'packaging_items']);


type AlertStatus = 'open' | 'resolved' | 'dismissed';
type AlertStatusFilter = 'open' | 'resolved' | 'dismissed' | 'all';
type AlertSeverity = 'info' | 'warning' | 'critical' | 'blocking';
type AlertType = 'low_ingredient_stock' | 'low_packaging_stock' | 'ingredient_expiration_soon' | 'ingredient_expired' | 'insufficient_materials_for_order' | 'insufficient_packaging_for_order';
type AlertResponse = { id: number; alert_key: string; type: AlertType; severity: AlertSeverity; message: string; related_entity_type: string; related_entity_id: number; recommended_action: string; status: AlertStatus; created_at: string; updated_at: string; resolved_at: string | null; dismissed_at: string | null };
type AlertListResponse = { alerts: AlertResponse[]; limit: number; offset: number };
type AlertGenerationResponse = { created_count: number; updated_count: number; resolved_count: number; open_count: number };
type AlertsState = { items: AlertResponse[]; status: 'idle' | 'loading' | 'ready' | 'error'; actionStatus: 'idle' | 'loading'; error: string; message: string; filters: { status: AlertStatusFilter; type: AlertType | ''; search: string }; lastGeneration: AlertGenerationResponse | null };

type PurchaseSuggestionStatus = 'open' | 'purchased' | 'dismissed' | 'archived';
type PurchaseSuggestionStatusFilter = PurchaseSuggestionStatus | 'all';
type PurchaseSuggestionItemType = 'ingredient' | 'packaging';
type PurchaseSuggestionItemTypeFilter = PurchaseSuggestionItemType | '';
type PurchaseSuggestionReason = 'below_minimum_stock' | 'insufficient_for_order' | 'predicted_shortage' | 'expiration_replacement' | 'manual';
type PurchaseSuggestionReasonFilter = PurchaseSuggestionReason | '';
type PurchaseSuggestionResponse = { id: number; suggestion_key: string; item_type: PurchaseSuggestionItemType; item_id: number; item_name_snapshot: string; recommended_quantity: string; unit: string; reason: PurchaseSuggestionReason; source_entity_type: string; source_entity_id: number | null; message: string; status: PurchaseSuggestionStatus; notes: string; created_at: string; updated_at: string; resolved_at: string | null };
type PurchaseSuggestionListResponse = { purchase_suggestions: PurchaseSuggestionResponse[]; limit: number; offset: number };
type PurchaseSuggestionGenerationResponse = { created_count: number; updated_count: number; archived_count: number; open_count: number };
type ManualPurchaseSuggestionRequest = { item_type: PurchaseSuggestionItemType; item_id: number; recommended_quantity: string; unit: string; notes: string };
type PurchaseSuggestionUpdateRequest = { recommended_quantity: string; unit: string; notes: string };
type PurchaseSuggestionsState = { items: PurchaseSuggestionResponse[]; status: 'idle' | 'loading' | 'ready' | 'error'; actionStatus: 'idle' | 'loading'; error: string; message: string; filters: { status: PurchaseSuggestionStatusFilter; reason: PurchaseSuggestionReasonFilter; itemType: PurchaseSuggestionItemTypeFilter; search: string }; lastGeneration: PurchaseSuggestionGenerationResponse | null; showManualForm: boolean; manualForm: { item_type: PurchaseSuggestionItemType; item_id: string; recommended_quantity: string; unit: string; notes: string }; editingSuggestionId: number | null; editForm: { recommended_quantity: string; unit: string; notes: string } };


type OrdersState = { items: Order[]; clients: Client[]; templates: RecipeTemplate[]; versions: RecipeVersion[]; clientRecipes: ClientRecipe[]; packagingItems: PackagingItem[]; formMode: OrderFormMode; form: OrderFormState; showForm: boolean; selectedOrder: Order | null; includeInactive: boolean; filters: { search: string; status: OrderStatusFilter }; referenceLoading: boolean; referenceError: string; readinessByOrderId: Record<number, ProductionReadinessResponse>; readinessLoadingOrderId: number | null; readinessError: string; productionByOrderId: Record<number, ProductionBatchDetailResponse>; productionLoadingOrderId: number | null; productionError: string; productionConfirmingOrderId: number | null; productionNotesByOrderId: Record<number, string> };

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



type ReportWarning = { code: string; message: string; field: string | null };
type QuantityTotal = { unit: string; quantity: string };
type InventoryReportResponse = { generated_at: string; total_active_ingredients: number; total_active_ingredient_lots: number; ingredient_lots_with_positive_balance: number; expired_ingredient_lots: number; expiring_soon_ingredient_lots: number; active_packaging_items: number; packaging_items_with_positive_balance: number; open_low_stock_alerts: number; open_purchase_suggestions: number; warnings: ReportWarning[] };
type OrdersReportResponse = { generated_at: string; total_orders: number; active_orders: number; new_orders: number; waiting_for_materials: number; ready_to_produce: number; in_progress: number; produced: number; delivered: number; cancelled: number; archived: number; orders_missing_recipe: number; warnings: ReportWarning[] };
type ProductionReportResponse = { generated_at: string; total_production_batches: number; batches_in_period: number; last_production_date: string | null; produced_orders_count: number; produced_quantity_totals: QuantityTotal[]; total_known_cost: string | null; missing_cost_count: number; warnings: ReportWarning[] };
type FinanceReportResponse = { generated_at: string; produced_order_count: number; produced_orders_with_sale_price: number; known_revenue: string | null; known_production_cost: string | null; known_margin: string | null; known_margin_percent: string | null; complete_finance_record_count: number; incomplete_margin_count: number; missing_sale_price_count: number; missing_cost_count: number; warnings: ReportWarning[] };
type AlertsReportSummary = { open_alerts: number; critical_or_blocking_alerts: number };
type PurchaseReportSummary = { open_purchase_suggestions: number };
type OverviewReportResponse = { generated_at: string; inventory_summary: InventoryReportResponse; orders_summary: OrdersReportResponse; production_summary: ProductionReportResponse; alerts_summary: AlertsReportSummary; purchase_summary: PurchaseReportSummary; finance_summary: FinanceReportResponse; warnings: ReportWarning[] };
type ReportTab = 'overview' | 'inventory' | 'orders' | 'production' | 'finance';
type ReportsUiState = { status: 'idle' | 'loading' | 'ready' | 'error'; selectedReport: ReportTab; error: string; message: string; overview: OverviewReportResponse | null; inventory: InventoryReportResponse | null; orders: OrdersReportResponse | null; production: ProductionReportResponse | null; finance: FinanceReportResponse | null };
type ReportDocumentMetadata = { id: string; document_type: string; format: string; filename: string; metadata_filename: string | null; created_at: string; source: string; source_generated_at: string | null; title: string; warnings_count: number; size_bytes: number };
type ReportDocumentStatusResponse = { documents_dir: string; available_formats: string[]; available_document_types: string[]; can_create: boolean; documents_count: number; message: string };
type ReportDocumentListResponse = { items: ReportDocumentMetadata[]; limit: number; offset: number; total: number };
type ReportOverviewDocumentCreateRequest = { format?: 'markdown' | 'pdf'; reason?: string };
type ReportDocumentCreateResponse = { document: ReportDocumentMetadata; message: string };
type ReportDocumentsUiState = { status: 'idle' | 'loading' | 'ready' | 'error'; actionStatus: 'idle' | 'creating'; error: string; message: string; documentStatus: ReportDocumentStatusResponse | null; documents: ReportDocumentMetadata[]; lastCreatedDocument: ReportDocumentMetadata | null; reason: string };

type NavigationSection = 'Главная' | 'Алерты' | 'Демо-данные' | 'Резервные копии' | 'Рецепты' | 'Индивидуальные рецепты' | 'Клиенты' | 'Заказы' | 'Склад' | 'Компоненты' | 'Партии' | 'Движения сырья' | 'Тара' | 'Закупки' | 'Производство' | 'Экспорт' | 'Документы отчетов' | 'Импорт' | 'Отчеты' | 'Настройки' | 'Помощь';
type NavigationStatus = 'ready' | 'empty' | 'planned';
type NavigationItem = { label: string; section: NavigationSection; path: string; status: NavigationStatus };
type NavigationGroup = { title: string; items: NavigationItem[] };
type HelpArticle = { id: string; title: string; category: string; summary: string; body: string[]; relatedSections?: NavigationSection[]; warning?: string };
type HelpUiState = { search: string; category: string; selectedArticleId: string };

const navigationGroups: NavigationGroup[] = [
  { title: 'Главная', items: [{ label: 'Обзор', section: 'Главная', path: '/', status: 'ready' }, { label: 'Алерты', section: 'Алерты', path: '/alerts', status: 'ready' }] },
  { title: 'Рецепты', items: [
    { label: 'Рецепты', section: 'Рецепты', path: '/recipes', status: 'ready' },
    { label: 'Индивидуальные рецепты', section: 'Индивидуальные рецепты', path: '/client-recipes', status: 'ready' },
  ] },
  { title: 'Клиенты', items: [
    { label: 'Клиенты', section: 'Клиенты', path: '/clients', status: 'ready' },
    { label: 'Заказы', section: 'Заказы', path: '/orders', status: 'ready' },
  ] },
  { title: 'Склад', items: [
    { label: 'Обзор склада', section: 'Склад', path: '/inventory', status: 'ready' },
    { label: 'Компоненты', section: 'Компоненты', path: '/ingredients', status: 'ready' },
    { label: 'Приходы и партии', section: 'Партии', path: '/ingredient-lots', status: 'ready' },
    { label: 'Движения сырья', section: 'Движения сырья', path: '/stock-movements', status: 'ready' },
    { label: 'Тара', section: 'Тара', path: '/packaging-items', status: 'ready' },
    { label: 'Закупки', section: 'Закупки', path: '/purchase-suggestions', status: 'ready' },
  ] },
  { title: 'Производство', items: [
    { label: 'Производство', section: 'Производство', path: '/production', status: 'ready' },
  ] },
  { title: 'Данные и настройки', items: [
    { label: 'Резервные копии', section: 'Резервные копии', path: '/backups', status: 'ready' },
    { label: 'Экспорт', section: 'Экспорт', path: '/exports', status: 'ready' },
    { label: 'Документы отчётов', section: 'Документы отчетов', path: '/report-documents', status: 'ready' },
    { label: 'Импорт', section: 'Импорт', path: '/imports', status: 'ready' },
    { label: 'Демо-данные', section: 'Демо-данные', path: '/demo-data', status: 'ready' },
    { label: 'Отчёты', section: 'Отчеты', path: '/reports', status: 'ready' },
    { label: 'Настройки', section: 'Настройки', path: '/settings', status: 'ready' },
    { label: 'Помощь', section: 'Помощь', path: '/help', status: 'ready' },
  ] },
];

const helpCategories = ['Первые шаги', 'Склад', 'Рецепты', 'Клиенты', 'Заказы и производство', 'Алерты и закупки', 'Данные и безопасность', 'Импорт и демо-данные'];
const helpArticles: HelpArticle[] = [
  { id: 'getting-started', title: 'Как начать работу', category: 'Первые шаги', summary: 'Безопасный порядок первого запуска: от списка первых шагов и демо до заказа и резервной копии.', relatedSections: ['Главная', 'Демо-данные', 'Компоненты', 'Партии', 'Тара', 'Рецепты', 'Клиенты', 'Заказы', 'Резервные копии', 'Экспорт'], warning: 'Перед импортом, обновлением или большой правкой создайте резервную копию или экспорт.', body: ['Откройте главную страницу и пройдите список первых шагов: он подсказывает, какие разделы заполнять первыми.', 'Если хотите потренироваться, сначала установите демо-данные. Они ставятся только явно и не нужны для реальной работы.', 'Добавьте компоненты, затем партии компонентов и движения прихода. Отдельно добавьте тару и её остатки.', 'Создайте рецепты и версии, затем клиентов и индивидуальные рецепты при необходимости.', 'Создайте заказ, проверьте готовность в заказе и запускайте производство только когда предупреждения понятны и материалов хватает.', 'Перед рискованными изменениями — импортом, обновлением приложения или массовыми правками — сделайте резервную копию или экспорт.'] },
  { id: 'ingredient', title: 'Что такое компонент', category: 'Склад', summary: 'Компонент — это сырьё или материал, но не конкретная купленная партия.', relatedSections: ['Компоненты', 'Партии', 'Движения сырья'], body: ['Компонент — это карточка сырья: масло, эмульгатор, актив, консервант или другой материал.', 'В карточке хранятся название, единица, плотность для перевода мл в граммы и рабочие заметки.', 'Компонент не равен партии: один компонент можно купить несколько раз с разными сроками и ценой.', 'Остатки живут не в карточке компонента, а через партии и движения склада.'] },
  { id: 'ingredient-lot', title: 'Что такое партия компонента', category: 'Склад', summary: 'Партия — конкретная покупка компонента со сроком, ценой и поставщиком.', relatedSections: ['Партии', 'Движения сырья', 'Склад'], body: ['Партия — это купленный batch компонента: например, 500 г масла ши от конкретного поставщика.', 'У партии можно указать поставщика, дату покупки, цену, срок годности и номер партии.', 'Партии нужны для FEFO: система выбирает то, что истекает раньше, при проверке готовности и производстве.', 'Не редактируйте остаток напрямую. Добавляйте приход, списание или коррекцию через движения.'] },
  { id: 'ingredient-movements', title: 'Как работают движения сырья', category: 'Склад', summary: 'Любое изменение остатка сырья фиксируется отдельным движением.', relatedSections: ['Движения сырья', 'Партии', 'Склад'], warning: 'Историю движений нельзя тихо переписывать: исправления лучше делать новым корректирующим движением.', body: ['Движение показывает, почему остаток изменился: приход, списание, коррекция или другое основание.', 'Движения сохраняют историю склада и помогают понять, что произошло с партией.', 'Производство создаёт списания автоматически после явного подтверждения пользователя.', 'Если нашли ошибку, добавьте корректирующее движение вместо скрытого изменения старой записи.'] },
  { id: 'packaging', title: 'Что такое тара', category: 'Склад', summary: 'Тара и расходники учитываются отдельно от компонентов.', relatedSections: ['Тара', 'Заказы', 'Склад'], body: ['Тара — это баночки, флаконы, крышки, пипетки, этикетки, коробки и другие расходники.', 'Остаток тары считается отдельно от сырья, потому что заказ может быть готов по рецепту, но заблокирован из-за упаковки.', 'Движения тары показывают приход, списание или коррекцию количества.', 'В заказе можно выбрать тару и количество, чтобы проверка готовности учитывала упаковку.'] },
  { id: 'recipe-versions', title: 'Как устроены рецепты и версии', category: 'Рецепты', summary: 'Карточка рецепта хранит продукт, версия — конкретную формулу.', relatedSections: ['Рецепты'], warning: 'Не меняйте смысл старой версии задним числом: для важных изменений создавайте новую версию.', body: ['Рецепт — это карточка продукта, например «Дневной крем».', 'Версия рецепта — конкретная формула с компонентами, фазами, процентами или фиксированными количествами.', 'Версии защищают историю: заказ и производство должны ссылаться на точную формулу, которая использовалась.', 'После сохранения приложение проверяет состав и показывает расчёт процентов, граммов и предупреждения.'] },
  { id: 'client-recipes', title: 'Индивидуальные рецепты клиентов', category: 'Рецепты', summary: 'Индивидуальная формула — отдельный производственный рецепт для клиента.', relatedSections: ['Индивидуальные рецепты', 'Клиенты', 'Рецепты'], body: ['Индивидуальный рецепт связан с конкретным клиентом и может быть создан на основе версии базового рецепта.', 'Он полезен для персональных предпочтений, аллергий, противопоказаний и особых пожеланий.', 'Это не обычная заметка в карточке клиента, а отдельная формула, которую можно использовать в заказе.', 'Храните причину индивидуализации и важные ограничения аккуратно, чтобы не потерять контекст.'] },
  { id: 'clients-wishes-feedback', title: 'Клиенты, пожелания и обратная связь', category: 'Клиенты', summary: 'Карточка клиента хранит контакты, предпочтения, пожелания и реакции.', relatedSections: ['Клиенты', 'Индивидуальные рецепты'], body: ['В карточке клиента можно хранить контакты, предпочтения, противопоказания и важные заметки.', 'Пожелания — это будущие запросы клиента: что изменить, попробовать или учесть позже.', 'Обратная связь фиксирует реакцию после использования продукта или заказа.', 'История помогает мягко улучшать формулы и не полагаться на память.'] },
  { id: 'orders', title: 'Заказы', category: 'Заказы и производство', summary: 'Заказ связывает клиента, формулу, размер партии, тару и цену.', relatedSections: ['Заказы', 'Клиенты', 'Рецепты', 'Индивидуальные рецепты'], body: ['Заказ отвечает на вопросы: для кого, что изготовить, по какой формуле, в каком объёме, в какой таре и по какой цене.', 'Статусы помогают отделить новые заказы, ожидание материалов, готовность к производству, изготовленные, выданные и отменённые.', 'Перед производством всегда запускайте проверку готовности.', 'Пока заказ не подтверждён к производству, склад не списывается.'] },
  { id: 'production-readiness', title: 'Проверка готовности производства', category: 'Заказы и производство', summary: 'Проверка показывает, хватает ли сырья и тары, но ничего не списывает.', relatedSections: ['Заказы', 'Склад', 'Тара'], body: ['Проверка готовности смотрит требуемые компоненты, партии, тару, предупреждения и примерную себестоимость.', 'Проверка готовности подбирает доступные партии по безопасным правилам, в том числе с учётом ближайшего срока годности.', 'Блокеры и предупреждения нужно прочитать до производства: нехватка, срок годности, плотность, проценты рецепта.', 'Проверка не меняет данные и не списывает склад — это только предварительный просмотр.'] },
  { id: 'production-confirmation', title: 'Производство и списание', category: 'Заказы и производство', summary: 'Производство запускается явно и создаёт историю со списаниями.', relatedSections: ['Заказы', 'Производство', 'Склад'], warning: 'Не запускайте производство, если предупреждения непонятны или материалы фактически не готовы.', body: ['Производство выполняется только после явного подтверждения в заказе.', 'При успешном производстве компоненты и тара списываются транзакционно: не должно быть частичного списания при ошибке.', 'Создаётся история производства с фактической партией и доступными расчётными показателями. Если себестоимость, налог или маржа не рассчитаны, приложение показывает это явно.', 'Если производство не прошло, проверьте сообщение и повторите после исправления причины.'] },
  { id: 'alerts', title: 'Алерты', category: 'Алерты и закупки', summary: 'Алерты показывают низкие остатки, сроки годности и нехватку материалов.', relatedSections: ['Алерты', 'Закупки', 'Склад'], body: ['Алерты помогают увидеть, что требует внимания: низкий остаток, скорое истечение срока, истёкший компонент или нехватка для заказа.', 'Обновление алертов запускается явно. Оно не покупает, не списывает и не меняет рецепты.', 'У каждого алерта есть рекомендуемое действие: проверить партию, добавить закупку, пополнить склад или открыть связанный раздел.', 'Закрывайте или скрывайте алерт только когда понимаете, почему он больше не нужен.'] },
  { id: 'purchases', title: 'Закупки', category: 'Алерты и закупки', summary: 'Закупочные предложения помогают планировать покупки, но не добавляют остатки.', relatedSections: ['Закупки', 'Партии', 'Тара'], body: ['Закупки показывают, что стоит купить из-за низкого остатка, нехватки для заказа, прогноза или замены просроченного.', 'Предложение можно обработать, отложить или создать вручную.', 'Отметка «куплено» не добавляет сырьё или тару на склад.', 'После реальной покупки добавьте партию компонента и движение прихода либо движение тары.'] },
  { id: 'backup-export', title: 'Резервные копии и экспорт', category: 'Данные и безопасность', summary: 'Резервная копия защищает рабочие данные, экспорт создаёт отдельный локальный файл для проверки или передачи.', relatedSections: ['Резервные копии', 'Экспорт'], warning: 'Создавайте резервную копию перед импортом, обновлением приложения и большими изменениями.', body: ['Резервная копия — это отдельная защитная копия рабочих данных мастерской. Она создаётся только по явному действию пользователя и не меняет рабочие записи.', 'Экспорт создаёт отдельный локальный файл в формате JSON для проверки данных или передачи. Экспорт тоже запускается только явно и не меняет рабочие записи.', 'Файлы остаются на этом компьютере в локальной папке данных мастерской.', 'Восстановление резервной копии не выполняется с текущего экрана резервных копий, а экспортированный JSON-файл сейчас нельзя загрузить обратно через экран экспорта.'] },
  { id: 'import', title: 'Импорт', category: 'Импорт и демо-данные', summary: 'Импорт идёт через черновик, проверку, подтверждение и применение.', relatedSections: ['Импорт', 'Резервные копии'], warning: 'Проверьте ошибки и создайте резервную копию до применения импорта.', body: ['Импорт поддерживает CSV и XLSX и сначала создаёт черновик с предпросмотром строк.', 'Пользователь выбирает цель, проверяет найденные ошибки и предупреждения, затем явно подтверждает применение.', 'Применение поддержано только для безопасных целей: компоненты, клиенты, рецепты и тара. Партии компонентов и заказы пока не применяются импортом.', 'Не применяйте файл, если значения выглядят не так: исправьте таблицу и загрузите заново.'] },
  { id: 'demo-data', title: 'Демо-данные', category: 'Импорт и демо-данные', summary: 'Демо помогает познакомиться с приложением без ручного заполнения.', relatedSections: ['Демо-данные', 'Главная'], body: ['Демо-данные необязательны и устанавливаются только по явному подтверждению.', 'Установка блокируется, если в базе уже есть реальные рабочие данные.', 'Демо-записи помечены «Демо ·», чтобы их не перепутать с настоящими.', 'Очистка удаляет только отслеженные демо-данные и тоже требует подтверждения. Демо не создаёт резервную копию или экспорт автоматически.'] },
];

const stepLabels: Record<string, string> = {
  welcome: 'Познакомиться с рабочим пространством',
  data_location: 'Понять, где хранятся локальные данные',
  first_ingredient: 'Добавить первый компонент',
  first_ingredient_lot: 'Добавить первую партию компонента',
  first_packaging: 'Добавить первую тару',
  first_recipe: 'Создать первый рецепт',
  first_client: 'Создать первого клиента',
  first_client_recipe: 'Создать индивидуальный рецепт клиента',
  first_order: 'Создать первый заказ',
  production_readiness: 'Проверить готовность производства',
  first_production: 'Провести первое производство',
  alerts_and_purchases: 'Проверить алерты и закупки',
  backup_and_export: 'Создать резервную копию или экспорт',
  import_draft: 'Проверить импорт через черновик',
};

type OnboardingStepUi = { hint: string; sections: NavigationSection[] };
const onboardingStepUi: Record<string, OnboardingStepUi> = {
  welcome: { hint: 'Коротко понять назначение системы и основные разделы.', sections: ['Главная'] },
  data_location: { hint: 'Данные остаются на этом MacBook; резервные копии и экспорт помогают защитить работу.', sections: ['Резервные копии', 'Экспорт'] },
  first_ingredient: { hint: 'Откройте компоненты и добавьте сырье с единицей, плотностью и минимальным остатком.', sections: ['Компоненты'] },
  first_ingredient_lot: { hint: 'Добавьте партию компонента со сроком годности, ценой и поставщиком.', sections: ['Партии'] },
  first_packaging: { hint: 'Добавьте баночки, флаконы, крышки или расходники для будущих заказов.', sections: ['Тара'] },
  first_recipe: { hint: 'Создайте карточку рецепта и версию с процентами или фиксированными количествами.', sections: ['Рецепты'] },
  first_client: { hint: 'Добавьте клиента без лишней технической информации и с аккуратными заметками.', sections: ['Клиенты'] },
  first_client_recipe: { hint: 'Создайте индивидуальный рецепт на основе версии рецепта для конкретного клиента.', sections: ['Индивидуальные рецепты'] },
  first_order: { hint: 'Создайте заказ: клиент, формула, размер партии, тара и цена продажи.', sections: ['Заказы'] },
  production_readiness: { hint: 'В заказах проверьте материалы, тару, предупреждения, себестоимость и маржу перед производством.', sections: ['Заказы'] },
  first_production: { hint: 'Проведите производство только после явного подтверждения. После успешного выполнения приложение спишет выбранные материалы и тару и сохранит историю производства.', sections: ['Заказы', 'Производство'] },
  alerts_and_purchases: { hint: 'Проверьте низкие остатки, сроки годности и список закупок.', sections: ['Алерты', 'Закупки'] },
  backup_and_export: { hint: 'Создайте резервную копию или экспорт перед важными изменениями.', sections: ['Резервные копии', 'Экспорт'] },
  import_draft: { hint: 'Загрузите CSV/XLSX в черновик, проверьте ошибки и применяйте только поддерживаемые типы.', sections: ['Импорт'] },
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
let clientsRefreshWarning = '';
let clientValidation = emptyFormValidationState();
let clientSubmitting = false;
let clientSubmitToken = 0;
let clientCardState: ClientCardState = emptyClientCardState();
let clientRecipesStatus: ClientRecipesStatus = 'idle';
let clientRecipesError = '';
let clientRecipesMessage = '';
let clientRecipesState: ClientRecipesState = { items: [], clients: [], templates: [], versions: [], versionsStatus: 'idle', selectedTemplateId: null, selectedDetail: null, form: emptyClientRecipeForm(), includeInactive: false, detailStatus: 'idle', showCreateForm: false, filters: { search: '', status: 'active', clientId: '' }, compositionEditor: emptyClientRecipeCompositionEditor() };
let ordersStatus: OrdersStatus = 'idle';
let ordersError = '';
let ordersMessage = '';
let productionHistoryState: ProductionHistoryState = { batches: [], selectedBatch: null, status: 'idle', detailStatus: 'idle', error: '', detailError: '', filters: { search: '' } };
let dashboardState: DashboardState = { status: 'idle', error: '', message: '', orders: [], clients: [], alerts: [], purchaseSuggestions: [], productionBatches: [] };
let backupUiState: BackupUiState = { status: 'idle', actionStatus: 'idle', error: '', message: '', backupStatus: null, backups: [], reason: 'manual', customReason: '', lastCreatedBackup: null };
let exportUiState: ExportUiState = { status: 'idle', actionStatus: 'idle', error: '', message: '', exportStatus: null, exports: [], reason: 'manual', customReason: '', lastCreatedExport: null, lastEntityCounts: {} };
let demoDataUiState: DemoDataUiState = { status: 'idle', actionStatus: 'idle', error: '', message: '', demoStatus: null, installConfirmChecked: false, understandDemoChecked: false, clearConfirmChecked: false, showInstallConfirm: false, showClearConfirm: false, lastInstallResult: null, lastClearResult: null };
let importUiState: ImportUiState = { status: 'idle', actionStatus: 'idle', applyStatus: 'idle', error: '', message: '', applyError: '', applyErrorIssues: [], applyMessage: '', applyRefreshWarning: '', applyConfirmChecked: false, backupAcknowledged: false, allowWarnings: false, lastApplyResult: null, showApplyConfirm: false, targets: [], drafts: [], selectedDraft: null, selectedDraftStatus: 'idle', selectedDraftError: '', selectedTargetType: '', selectedFileName: '', filters: { status: '', targetType: '' } };
let alertsState: AlertsState = { items: [], status: 'idle', actionStatus: 'idle', error: '', message: '', filters: { status: 'open', type: '', search: '' }, lastGeneration: null };
let purchaseSuggestionsState: PurchaseSuggestionsState = { items: [], status: 'idle', actionStatus: 'idle', error: '', message: '', filters: { status: 'open', reason: '', itemType: '', search: '' }, lastGeneration: null, showManualForm: false, manualForm: { item_type: 'ingredient', item_id: '', recommended_quantity: '', unit: 'g', notes: '' }, editingSuggestionId: null, editForm: { recommended_quantity: '', unit: '', notes: '' } };
let ordersState: OrdersState = { items: [], clients: [], templates: [], versions: [], clientRecipes: [], packagingItems: [], formMode: 'create', form: emptyOrderForm(), showForm: false, selectedOrder: null, includeInactive: true, filters: { search: '', status: 'active' }, referenceLoading: false, referenceError: '', readinessByOrderId: {}, readinessLoadingOrderId: null, readinessError: '', productionByOrderId: {}, productionLoadingOrderId: null, productionError: '', productionConfirmingOrderId: null, productionNotesByOrderId: {} };
let ingredientsStatus: IngredientsStatus = 'idle';
let ingredientsState: IngredientsState = { items: [], formMode: 'create', form: emptyIngredientForm(), catalogCategories: [], catalogTags: [], catalogSaving: 'idle', catalogCreating: null, showCreateForm: false, filters: emptyCatalogBrowserFilters(), assignmentDraft: emptyAssignmentDraft() };
let ingredientsError = '';
let ingredientsMessage = '';
let ingredientsRefreshWarning = '';
let ingredientValidation = emptyFormValidationState();
let ingredientSubmitting = false;
let ingredientSubmitToken = 0;
let ingredientLotsStatus: IngredientLotsStatus = 'idle';
let ingredientLotsState: IngredientLotsState = { lots: [], ingredients: [], formMode: 'create', form: emptyIngredientLotForm() };
let ingredientLotsError = '';
let ingredientLotsMessage = '';
let ingredientLotsRefreshWarning = '';
let ingredientLotValidation = emptyFormValidationState();
let ingredientLotSubmitting = false;
let ingredientLotSubmitToken = 0;
let stockMovementsStatus: StockMovementsStatus = 'idle';
let stockMovementsState: StockMovementsState = { lots: [], ingredients: [], selectedLotId: null, balance: null, movements: [], form: emptyStockMovementForm(), detailStatus: 'idle' };
let stockMovementsError = '';
let stockMovementsMessage = '';
let stockMovementsRefreshWarning = '';
let stockMovementValidation = emptyFormValidationState();
let stockMovementSubmitting = false;
let stockMovementSubmitToken = 0;
const stockMovementLotDetailLifecycle = createStockMovementLotDetailLifecycle();
let packagingItemsStatus: PackagingItemsStatus = 'idle';
let packagingItemsState: PackagingItemsState = { items: [], formMode: 'create', form: emptyPackagingItemForm(), catalogCategories: [], catalogTags: [], catalogSaving: 'idle', catalogCreating: null, showCreateForm: false, filters: emptyCatalogBrowserFilters(), assignmentDraft: emptyAssignmentDraft() };
let packagingItemsError = '';
let packagingItemsMessage = '';
let packagingItemsRefreshWarning = '';
let packagingItemValidation = emptyFormValidationState();
let packagingItemSubmitting = false;
let packagingItemSubmitToken = 0;
let packagingItemDeactivatingId: number | null = null;
function packagingPageMutationActive() {
  return packagingPageMutationActiveState({ packagingItemSubmitting, catalogSaving: packagingItemsState.catalogSaving, catalogCreating: packagingItemsState.catalogCreating, deactivatingId: packagingItemDeactivatingId });
}
function recipePageMutationActive() { return recipeTemplateSubmitting || recipeVersionSubmitting; }
let recipesStatus: RecipesStatus = 'idle';
let recipesError = '';
let recipesMessage = '';
let recipesRefreshWarning = '';
let recipeTemplateValidation = emptyFormValidationState();
let recipeVersionValidation = emptyFormValidationState();
let recipeTemplateSubmitting = false;
let recipeVersionSubmitting = false;
let recipeTemplateSubmitToken = 0;
let recipeVersionSubmitToken = 0;
const recipeTemplateMutationLifecycle = createRecipeMutationLifecycle();
const recipeVersionMutationLifecycle = createRecipeMutationLifecycle();
let recipeVersionRefreshToken = 0;
let calculationStatus: CalculationStatus = 'idle';
let calculationError = '';
let recipesState: RecipesState = { templates: [], selectedTemplate: null, versions: [], selectedVersionDetail: null, versionDetailStatus: 'idle', ingredients: [], templateForm: emptyRecipeTemplateForm(), versionForm: emptyRecipeVersionForm(), calculation: null, calculationTargetValue: '', calculationTargetUnit: 'g', catalogCategories: [], catalogTags: [], catalogSaving: 'idle', catalogCreating: null, showCreateForm: false, filters: emptyCatalogBrowserFilters() };
let ingredientCatalogControls: CatalogControlState = { categorySearch: '', tagSearch: '', showAllTags: false };
let packagingCatalogControls: CatalogControlState = { categorySearch: '', tagSearch: '', showAllTags: false };
let helpUiState: HelpUiState = { search: '', category: '', selectedArticleId: 'getting-started' };
let reportsUiState: ReportsUiState = { status: 'idle', selectedReport: 'overview', error: '', message: '', overview: null, inventory: null, orders: null, production: null, finance: null };
let reportDocumentsUiState: ReportDocumentsUiState = { status: 'idle', actionStatus: 'idle', error: '', message: '', documentStatus: null, documents: [], lastCreatedDocument: null, reason: '' };
let settingsUiState: SettingsUiState = { status: 'idle', data: null, error: '' };
const emptyWorkshopProfile = (): WorkshopProfile => ({ workshop_name: '', master_name: '', workshop_contact_text: '', workshop_note: '' });
let workshopProfileUiState: WorkshopProfileUiState = { status: 'idle', actionStatus: 'idle', profile: null, draft: emptyWorkshopProfile(), error: '', message: '' };

function sectionFromLocation(): NavigationSection {
  const routes: Record<string, NavigationSection> = {
    '/alerts': 'Алерты',
    '/backups': 'Резервные копии',
    '/exports': 'Экспорт',
    '/report-documents': 'Документы отчетов',
    '/imports': 'Импорт',
    '/demo-data': 'Демо-данные',
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
    '/purchase-suggestions': 'Закупки',
    '/reports': 'Отчеты',
    '/settings': 'Настройки',
    '/help': 'Помощь',
  };
  const placeholderRoutes: Record<string, NavigationSection> = {
    '#purchases': 'Закупки',
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
  if (section === 'Главная') loadDashboard();
  if (section === 'Алерты') loadAlerts();
  if (section === 'Резервные копии') loadBackups();
  if (section === 'Экспорт') loadExports();
  if (section === 'Документы отчетов') loadReportDocuments();
  if (section === 'Импорт') loadImports();
  if (section === 'Демо-данные') loadDemoDataStatus();
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
  if (section === 'Закупки') loadPurchaseSuggestions();
  if (section === 'Отчеты') loadReports();
  if (section === 'Настройки') { loadSettingsStatus(); loadWorkshopProfile(); }
}

function renderActivePage(section: NavigationSection) {
  if (section === 'Главная') return dashboardPage();
  if (section === 'Алерты') return alertsPage();
  if (section === 'Резервные копии') return backupPage();
  if (section === 'Экспорт') return exportPage();
  if (section === 'Документы отчетов') return reportDocumentsPage();
  if (section === 'Импорт') return importPage();
  if (section === 'Демо-данные') return demoDataPage();
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
  if (section === 'Закупки') return purchaseSuggestionsPage();
  if (section === 'Отчеты') return reportsPage();
  if (section === 'Настройки') return settingsPage();
  if (section === 'Помощь') return helpPage();
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
  const healthMarkup = healthStatus === 'offline' ? '<span class="status offline"><strong>Не удалось загрузить данные</strong><small>Перезапустите «Мастерскую косметолога» и повторите попытку.</small></span>' : '';
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
          ${healthMarkup}
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
  root.querySelector<HTMLButtonElement>('[data-action="reload-dashboard"]')?.addEventListener('click', () => loadDashboard(true));
  root.querySelector<HTMLButtonElement>('[data-action="reload-reports"]')?.addEventListener('click', () => loadReports(true));
  root.querySelector<HTMLButtonElement>('[data-action="reload-report-documents"]')?.addEventListener('click', () => loadReportDocuments(true));
  root.querySelector<HTMLFormElement>('[data-form="report-document-create"]')?.addEventListener('submit', submitReportDocumentCreateForm);
  root.querySelector<HTMLInputElement>('[data-action="report-document-reason"]')?.addEventListener('input', (event) => { reportDocumentsUiState.reason = (event.currentTarget as HTMLInputElement).value.slice(0, 80); });
  root.querySelectorAll<HTMLButtonElement>('[data-action="navigate-report-documents-related"]').forEach((button) => button.addEventListener('click', () => navigateToSection(button.dataset.section as NavigationSection | undefined)));
  root.querySelectorAll<HTMLButtonElement>('[data-action="select-report-tab"]').forEach((button) => button.addEventListener('click', () => { reportsUiState.selectedReport = (button.dataset.report as ReportTab | undefined) ?? 'overview'; render(); }));
  root.querySelectorAll<HTMLButtonElement>('[data-action="navigate-report-related"]').forEach((button) => button.addEventListener('click', () => navigateToSection(button.dataset.section as NavigationSection | undefined)));
  root.querySelector<HTMLButtonElement>('[data-action="reload-backups"]')?.addEventListener('click', () => loadBackups(true));
  root.querySelector<HTMLButtonElement>('[data-action="reload-exports"]')?.addEventListener('click', () => loadExports(true));
  root.querySelector<HTMLButtonElement>('[data-action="reload-imports"]')?.addEventListener('click', () => loadImports(true));
  root.querySelector<HTMLButtonElement>('[data-action="reload-demo-data"]')?.addEventListener('click', () => loadDemoDataStatus(true));
  root.querySelector<HTMLButtonElement>('[data-action="show-demo-install-confirm"]')?.addEventListener('click', showDemoInstallConfirm);
  root.querySelector<HTMLButtonElement>('[data-action="hide-demo-install-confirm"]')?.addEventListener('click', hideDemoInstallConfirm);
  root.querySelectorAll<HTMLInputElement>('[data-action="toggle-demo-install-check"]').forEach((input) => input.addEventListener('change', updateDemoInstallChecks));
  root.querySelector<HTMLButtonElement>('[data-action="install-demo-data"]')?.addEventListener('click', installDemoDataFromUi);
  root.querySelector<HTMLButtonElement>('[data-action="show-demo-clear-confirm"]')?.addEventListener('click', showDemoClearConfirm);
  root.querySelector<HTMLButtonElement>('[data-action="hide-demo-clear-confirm"]')?.addEventListener('click', hideDemoClearConfirm);
  root.querySelectorAll<HTMLInputElement>('[data-action="toggle-demo-clear-check"]').forEach((input) => input.addEventListener('change', updateDemoClearChecks));
  root.querySelector<HTMLButtonElement>('[data-action="clear-demo-data"]')?.addEventListener('click', clearDemoDataFromUi);
  root.querySelectorAll<HTMLButtonElement>('[data-action="navigate-demo-related"]').forEach((button) => button.addEventListener('click', () => navigateToSection(button.dataset.section as NavigationSection | undefined)));
  root.querySelector<HTMLFormElement>('[data-form="import-draft"]')?.addEventListener('submit', submitImportDraftForm);
  root.querySelector<HTMLSelectElement>('[data-action="select-import-target"]')?.addEventListener('change', (event) => { importUiState.selectedTargetType = (event.currentTarget as HTMLSelectElement).value; importUiState.error = ''; });
  root.querySelector<HTMLInputElement>('[data-action="select-import-file"]')?.addEventListener('change', (event) => { importUiState.selectedFileName = (event.currentTarget as HTMLInputElement).files?.[0]?.name ?? ''; importUiState.error = ''; });
  root.querySelectorAll<HTMLButtonElement>('[data-action="open-import-draft"]').forEach((button) => button.addEventListener('click', () => openImportDraft(Number(button.dataset.id))));
  root.querySelectorAll<HTMLButtonElement>('[data-action="cancel-import-draft"]').forEach((button) => button.addEventListener('click', () => cancelImportDraftFromUi(Number(button.dataset.id))));
  root.querySelector<HTMLButtonElement>('[data-action="show-import-apply-confirm"]')?.addEventListener('click', showImportApplyConfirmation);
  root.querySelector<HTMLButtonElement>('[data-action="hide-import-apply-confirm"]')?.addEventListener('click', hideImportApplyConfirmation);
  root.querySelector<HTMLButtonElement>('[data-action="apply-import-draft"]')?.addEventListener('click', applySelectedImportDraftFromUi);
  root.querySelectorAll<HTMLInputElement>('[data-action="toggle-import-apply-check"]').forEach((input) => input.addEventListener('change', () => updateImportApplyChecks()));
  root.querySelectorAll<HTMLButtonElement>('[data-action="navigate-import-related"]').forEach((button) => button.addEventListener('click', () => navigateToSection(button.dataset.section as NavigationSection | undefined)));
  root.querySelectorAll<HTMLButtonElement>('[data-action="navigate-onboarding-step"]').forEach((button) => button.addEventListener('click', () => navigateToSection(button.dataset.section as NavigationSection | undefined)));
  root.querySelector<HTMLButtonElement>('[data-action="reset-onboarding"]')?.addEventListener('click', () => updateOnboarding('/api/onboarding/reset'));
  root.querySelector<HTMLSelectElement>('[data-action="filter-import-status"]')?.addEventListener('change', (event) => { importUiState.filters.status = (event.currentTarget as HTMLSelectElement).value; loadImports(true); });
  root.querySelector<HTMLSelectElement>('[data-action="filter-import-target"]')?.addEventListener('change', (event) => { importUiState.filters.targetType = (event.currentTarget as HTMLSelectElement).value; loadImports(true); });
  root.querySelector<HTMLButtonElement>('[data-action="reset-import-filters"]')?.addEventListener('click', () => { importUiState.filters = { status: '', targetType: '' }; loadImports(true); });
  root.querySelector<HTMLFormElement>('[data-form="export-create"]')?.addEventListener('submit', submitExportCreateForm);
  root.querySelector<HTMLButtonElement>('[data-action="create-export"]')?.addEventListener('click', () => submitExportCreate());
  root.querySelector<HTMLSelectElement>('[data-action="select-export-reason"]')?.addEventListener('change', (event) => { exportUiState.reason = (event.currentTarget as HTMLSelectElement).value; exportUiState.message = ''; exportUiState.error = ''; render(); });
  root.querySelector<HTMLInputElement>('[data-action="custom-export-reason"]')?.addEventListener('input', (event) => { exportUiState.customReason = (event.currentTarget as HTMLInputElement).value.slice(0, 80); });
  root.querySelector<HTMLFormElement>('[data-form="backup-create"]')?.addEventListener('submit', submitBackupCreateForm);
  root.querySelector<HTMLButtonElement>('[data-action="create-backup"]')?.addEventListener('click', () => submitBackupCreate());
  root.querySelector<HTMLSelectElement>('[data-action="select-backup-reason"]')?.addEventListener('change', (event) => { backupUiState.reason = (event.currentTarget as HTMLSelectElement).value; backupUiState.message = ''; backupUiState.error = ''; render(); });
  root.querySelector<HTMLInputElement>('[data-action="custom-backup-reason"]')?.addEventListener('input', (event) => { backupUiState.customReason = (event.currentTarget as HTMLInputElement).value.slice(0, 80); });
  root.querySelector<HTMLInputElement>('[data-action="filter-help-search"]')?.addEventListener('input', (event) => updateHelpSearch(event.currentTarget as HTMLInputElement));
  root.querySelector<HTMLSelectElement>('[data-action="filter-help-category"]')?.addEventListener('change', (event) => { helpUiState.category = (event.currentTarget as HTMLSelectElement).value; render(); });
  root.querySelectorAll<HTMLButtonElement>('[data-action="open-help-article"]').forEach((button) => button.addEventListener('click', () => { helpUiState.selectedArticleId = button.dataset.id || 'getting-started'; render(); }));
  root.querySelectorAll<HTMLButtonElement>('[data-action="reset-help-filters"]').forEach((button) => button.addEventListener('click', () => { helpUiState.search = ''; helpUiState.category = ''; helpUiState.selectedArticleId = 'getting-started'; render(); }));
  root.querySelectorAll<HTMLButtonElement>('[data-action="navigate-help-related"]').forEach((button) => button.addEventListener('click', () => navigateToSection(button.dataset.section as NavigationSection | undefined)));
  root.querySelectorAll<HTMLButtonElement>('[data-action="navigate-settings-target"]').forEach((button) => button.addEventListener('click', () => navigateToSection(button.dataset.section as NavigationSection | undefined)));
  root.querySelectorAll<HTMLButtonElement>('[data-action="reload-settings-status"]').forEach((button) => button.addEventListener('click', () => loadSettingsStatus(true)));
  root.querySelectorAll<HTMLButtonElement>('[data-action="reload-workshop-profile"]').forEach((button) => button.addEventListener('click', () => loadWorkshopProfile(true)));
  root.querySelector<HTMLFormElement>('[data-form="workshop-profile"]')?.addEventListener('submit', submitWorkshopProfileForm);
  root.querySelector<HTMLButtonElement>('[data-action="cancel-workshop-profile"]')?.addEventListener('click', cancelWorkshopProfileChanges);
  root.querySelectorAll<HTMLInputElement | HTMLTextAreaElement>('[data-workshop-profile-field]').forEach((input) => input.addEventListener('input', updateWorkshopProfileDraft));
  root.querySelectorAll<HTMLButtonElement>('[data-nav-section]').forEach((button) => button.addEventListener('click', () => {
    activeSection = (button.dataset.navSection as NavigationSection | undefined) ?? 'Главная';
    window.history.pushState({}, '', pathForSection(activeSection));
    loadSectionData(activeSection);
    render();
  }));
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
  root.querySelector<HTMLButtonElement>('[data-action="reload-purchase-suggestions"]')?.addEventListener('click', () => loadPurchaseSuggestions(true));
  root.querySelector<HTMLButtonElement>('[data-action="regenerate-purchase-suggestions"]')?.addEventListener('click', runPurchaseSuggestionRegeneration);
  root.querySelector<HTMLInputElement>('[data-action="filter-purchase-search"]')?.addEventListener('input', (event) => updatePurchaseSuggestionSearch(event.currentTarget as HTMLInputElement));
  root.querySelector<HTMLSelectElement>('[data-action="filter-purchase-status"]')?.addEventListener('change', (event) => { purchaseSuggestionsState.filters.status = (event.currentTarget as HTMLSelectElement).value as PurchaseSuggestionStatusFilter; loadPurchaseSuggestions(true); });
  root.querySelector<HTMLSelectElement>('[data-action="filter-purchase-reason"]')?.addEventListener('change', (event) => { purchaseSuggestionsState.filters.reason = (event.currentTarget as HTMLSelectElement).value as PurchaseSuggestionReasonFilter; loadPurchaseSuggestions(true); });
  root.querySelector<HTMLSelectElement>('[data-action="filter-purchase-item-type"]')?.addEventListener('change', (event) => { purchaseSuggestionsState.filters.itemType = (event.currentTarget as HTMLSelectElement).value as PurchaseSuggestionItemTypeFilter; loadPurchaseSuggestions(true); });
  root.querySelector<HTMLButtonElement>('[data-action="reset-purchase-filters"]')?.addEventListener('click', () => { purchaseSuggestionsState.filters = { status: 'open', reason: '', itemType: '', search: '' }; loadPurchaseSuggestions(true); });
  root.querySelector<HTMLButtonElement>('[data-action="open-manual-purchase-form"]')?.addEventListener('click', openManualPurchaseSuggestionForm);
  root.querySelector<HTMLButtonElement>('[data-action="cancel-manual-purchase-form"]')?.addEventListener('click', () => { purchaseSuggestionsState.showManualForm = false; purchaseSuggestionsState.manualForm = emptyManualPurchaseSuggestionForm(); purchaseSuggestionsState.error = ''; render(); });
  root.querySelector<HTMLSelectElement>('[data-action="manual-purchase-item-type"]')?.addEventListener('change', (event) => changeManualPurchaseItemType((event.currentTarget as HTMLSelectElement).value as PurchaseSuggestionItemType));
  root.querySelector<HTMLFormElement>('[data-form="manual-purchase-suggestion"]')?.addEventListener('submit', submitManualPurchaseSuggestionForm);
  root.querySelectorAll<HTMLButtonElement>('[data-action="edit-purchase-suggestion"]').forEach((button) => button.addEventListener('click', () => startPurchaseSuggestionEdit(Number(button.dataset.id))));
  root.querySelector<HTMLButtonElement>('[data-action="cancel-purchase-edit"]')?.addEventListener('click', () => { purchaseSuggestionsState.editingSuggestionId = null; purchaseSuggestionsState.editForm = { recommended_quantity: '', unit: '', notes: '' }; render(); });
  root.querySelector<HTMLFormElement>('[data-form="purchase-suggestion-edit"]')?.addEventListener('submit', submitPurchaseSuggestionEditForm);
  root.querySelectorAll<HTMLButtonElement>('[data-action="mark-purchase-suggestion-purchased"]').forEach((button) => button.addEventListener('click', () => markPurchaseSuggestionAsPurchased(Number(button.dataset.id))));
  root.querySelectorAll<HTMLButtonElement>('[data-action="dismiss-purchase-suggestion"]').forEach((button) => button.addEventListener('click', () => dismissPurchaseSuggestionFromCard(Number(button.dataset.id))));
  root.querySelector<HTMLButtonElement>('[data-action="reload-orders"]')?.addEventListener('click', () => loadOrders(true));
  root.querySelector<HTMLButtonElement>('[data-action="reload-order-references"]')?.addEventListener('click', reloadOrderReferencesForForm);
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
  root.querySelectorAll<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>('[data-form="ingredient"] [name]').forEach((input) => input.addEventListener('input', () => { saveIngredientFormFromDom(); clearIngredientFieldError(input.name, input); }));
  root.querySelectorAll<HTMLSelectElement>('[data-form="ingredient"] select[name]').forEach((input) => input.addEventListener('change', () => { saveIngredientFormFromDom(); clearIngredientFieldError(input.name, input); }));
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
  root.querySelector<HTMLButtonElement>('[data-action="new-ingredient-lot"]')?.addEventListener('click', openIngredientLotCreateForm);
  root.querySelectorAll<HTMLButtonElement>('[data-action="edit-ingredient-lot"]').forEach((button) => button.addEventListener('click', () => startEditIngredientLot(Number(button.dataset.id))));
  root.querySelectorAll<HTMLButtonElement>('[data-action="deactivate-ingredient-lot"]').forEach((button) => button.addEventListener('click', () => deactivateIngredientLot(Number(button.dataset.id))));
  root.querySelector<HTMLFormElement>('[data-form="ingredient-lot"]')?.addEventListener('submit', submitIngredientLotForm);
  root.querySelectorAll<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>('[data-form="ingredient-lot"] [name]').forEach((input) => input.addEventListener('input', () => { saveIngredientLotFormFromDom(); clearIngredientLotFieldError(input.name, input); }));
  root.querySelectorAll<HTMLSelectElement>('[data-form="ingredient-lot"] select[name]').forEach((input) => input.addEventListener('change', () => { saveIngredientLotFormFromDom(); clearIngredientLotFieldError(input.name, input); }));
  root.querySelector<HTMLButtonElement>('[data-action="reload-stock-movements"]')?.addEventListener('click', () => loadStockMovements(true));
  root.querySelector<HTMLSelectElement>('[data-action="select-stock-lot"]')?.addEventListener('change', (event) => selectStockMovementLot(Number((event.currentTarget as HTMLSelectElement).value)));
  root.querySelector<HTMLFormElement>('[data-form="stock-movement"]')?.addEventListener('submit', submitStockMovementForm);
  root.querySelectorAll<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>('[data-form="stock-movement"] [name]').forEach((input) => input.addEventListener('input', () => { saveStockMovementFormFromDom(); clearStockMovementFieldError(input.name, input); }));
  root.querySelectorAll<HTMLSelectElement>('[data-form="stock-movement"] select[name]').forEach((input) => input.addEventListener('change', () => { saveStockMovementFormFromDom(); clearStockMovementFieldError(input.name, input); }));
  root.querySelector<HTMLButtonElement>('[data-action="reload-recipes"]')?.addEventListener('click', () => { if (recipePageMutationActive()) return; loadRecipes(true); });
  root.querySelectorAll<HTMLButtonElement>('[data-action="open-recipe-create"]').forEach((button) => button.addEventListener('click', openRecipeCreateForm));
  root.querySelectorAll<HTMLButtonElement>('[data-action="hide-recipe-create"]').forEach((button) => button.addEventListener('click', hideRecipeCreateForm));
  root.querySelector<HTMLButtonElement>('[data-action="close-recipe-detail"]')?.addEventListener('click', closeRecipeDetail);
  root.querySelector<HTMLInputElement>('[data-action="filter-recipes-search"]')?.addEventListener('input', (event) => { if (recipePageMutationActive()) return; updateRecipeFilterSearch(event.currentTarget as HTMLInputElement); });
  root.querySelector<HTMLSelectElement>('[data-action="filter-recipes-category"]')?.addEventListener('change', (event) => { if (recipePageMutationActive()) return; recipesState.filters.categoryId = catalogCategoryFilterValue((event.currentTarget as HTMLSelectElement).value); render(); });
  root.querySelector<HTMLSelectElement>('[data-action="filter-recipes-status"]')?.addEventListener('change', (event) => { if (recipePageMutationActive()) return; recipesState.filters.status = (event.currentTarget as HTMLSelectElement).value as CatalogStatusFilter; render(); });
  root.querySelectorAll<HTMLButtonElement>('[data-action="clear-recipe-filter"]').forEach((button) => button.addEventListener('click', () => { if (recipePageMutationActive()) return; clearRecipeFilter(button.dataset.filter ?? ''); }));
  root.querySelectorAll<HTMLButtonElement>('[data-action="reset-recipe-filters"]').forEach((button) => button.addEventListener('click', () => { if (recipePageMutationActive()) return; recipesState.filters = emptyCatalogBrowserFilters(); render(); }));
  root.querySelector<HTMLButtonElement>('[data-action="reload-recipe-ingredients"]')?.addEventListener('click', () => { if (recipePageMutationActive()) return; refreshRecipeIngredientOptions(true); });
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
  root.querySelectorAll<HTMLInputElement | HTMLTextAreaElement>('[data-form="client"] [name]').forEach((input) => input.addEventListener('input', () => { saveClientFormFromDom(); clearClientFieldError(input.name, input); }));
  root.querySelectorAll<HTMLInputElement>('[data-form="client"] input[type="date"][name]').forEach((input) => input.addEventListener('change', () => { saveClientFormFromDom(); clearClientFieldError(input.name, input); }));
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
  root.querySelector<HTMLButtonElement>('[data-action="reload-packaging-items"]')?.addEventListener('click', () => { if (packagingPageMutationActive()) return; loadPackagingItems(true); });
  root.querySelectorAll<HTMLButtonElement>('[data-action="new-packaging-item"]').forEach((button) => button.addEventListener('click', openPackagingCreateForm));
  root.querySelector<HTMLButtonElement>('[data-action="hide-packaging-create-form"]')?.addEventListener('click', hidePackagingCreateForm);
  root.querySelector<HTMLButtonElement>('[data-action="cancel-packaging-edit"]')?.addEventListener('click', cancelPackagingEdit);
  root.querySelectorAll<HTMLButtonElement>('[data-action="edit-packaging-item"]').forEach((button) => button.addEventListener('click', () => startEditPackagingItem(Number(button.dataset.id))));
  root.querySelectorAll<HTMLButtonElement>('[data-action="deactivate-packaging-item"]').forEach((button) => button.addEventListener('click', () => deactivatePackagingItem(Number(button.dataset.id))));
  root.querySelector<HTMLFormElement>('[data-form="packaging-item"]')?.addEventListener('submit', submitPackagingItemForm);
  root.querySelectorAll<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>('[data-form="packaging-item"] [name]').forEach((input) => input.addEventListener('input', () => { savePackagingItemFormFromDom(); clearPackagingItemFieldError(input.name, input); }));
  root.querySelectorAll<HTMLSelectElement>('[data-form="packaging-item"] select[name]').forEach((input) => input.addEventListener('change', () => { savePackagingItemFormFromDom(); clearPackagingItemFieldError(input.name, input); }));
  root.querySelector<HTMLInputElement>('[data-action="filter-packaging-search"]')?.addEventListener('input', (event) => { if (packagingPageMutationActive()) return; updatePackagingFilterSearch(event.currentTarget as HTMLInputElement); });
  root.querySelector<HTMLSelectElement>('[data-action="filter-packaging-category"]')?.addEventListener('change', (event) => { if (packagingPageMutationActive()) return; packagingItemsState.filters.categoryId = catalogCategoryFilterValue((event.currentTarget as HTMLSelectElement).value); render(); });
  root.querySelector<HTMLSelectElement>('[data-action="filter-packaging-kind"]')?.addEventListener('change', (event) => { if (packagingPageMutationActive()) return; packagingItemsState.filters.systemType = (event.currentTarget as HTMLSelectElement).value; render(); });
  root.querySelector<HTMLSelectElement>('[data-action="filter-packaging-status"]')?.addEventListener('change', (event) => { if (packagingPageMutationActive()) return; packagingItemsState.filters.status = (event.currentTarget as HTMLSelectElement).value as CatalogStatusFilter; render(); });
  root.querySelector<HTMLSelectElement>('[data-action="add-packaging-tag-filter"]')?.addEventListener('change', (event) => { if (packagingPageMutationActive()) return; addPackagingTagFilter((event.currentTarget as HTMLSelectElement).value); });
  root.querySelectorAll<HTMLButtonElement>('[data-action="remove-packaging-tag-filter"]').forEach((button) => button.addEventListener('click', () => { if (packagingPageMutationActive()) return; removePackagingTagFilter(Number(button.dataset.id)); }));
  root.querySelectorAll<HTMLButtonElement>('[data-action="clear-packaging-filter"]').forEach((button) => button.addEventListener('click', () => { if (packagingPageMutationActive()) return; clearPackagingFilter(button.dataset.filter ?? ''); }));
  root.querySelectorAll<HTMLButtonElement>('[data-action="reset-packaging-filters"]').forEach((button) => button.addEventListener('click', () => { if (packagingPageMutationActive()) return; packagingItemsState.filters = emptyCatalogBrowserFilters(); render(); }));
  root.querySelector<HTMLFormElement>('[data-form="packaging-catalog-category"]')?.addEventListener('submit', (event) => { if (packagingPageMutationActive()) { event.preventDefault(); return; } submitPackagingCatalogCategoryForm(event); });
  root.querySelector<HTMLFormElement>('[data-form="packaging-catalog-tag"]')?.addEventListener('submit', (event) => { if (packagingPageMutationActive()) { event.preventDefault(); return; } submitPackagingCatalogTagForm(event); });
  root.querySelectorAll<HTMLButtonElement>('[data-action="assign-packaging-category"]').forEach((button) => button.addEventListener('click', () => { if (packagingPageMutationActive()) return; updatePackagingDraftCategory(Number(button.dataset.id), button.dataset.value ?? ''); }));
  root.querySelectorAll<HTMLInputElement>('[data-action="toggle-packaging-tag"]').forEach((input) => input.addEventListener('change', () => { if (packagingPageMutationActive()) return; updatePackagingDraftTag(Number(input.dataset.packagingItemId), Number(input.value), input.checked); }));
  root.querySelector<HTMLButtonElement>('[data-action="apply-packaging-assignment"]')?.addEventListener('click', () => { if (packagingPageMutationActive()) return; applyPackagingAssignmentDraft(); });
  root.querySelector<HTMLButtonElement>('[data-action="reset-packaging-assignment"]')?.addEventListener('click', () => { if (packagingPageMutationActive()) return; resetPackagingAssignmentDraft(); });
  root.querySelector<HTMLInputElement>('[data-action="search-packaging-category"]')?.addEventListener('input', (event) => { if (packagingPageMutationActive()) return; updateCatalogSearch(packagingCatalogControls, 'categorySearch', event.currentTarget as HTMLInputElement); });
  root.querySelector<HTMLInputElement>('[data-action="search-packaging-tags"]')?.addEventListener('input', (event) => { if (packagingPageMutationActive()) return; updateCatalogSearch(packagingCatalogControls, 'tagSearch', event.currentTarget as HTMLInputElement); });
  root.querySelector<HTMLButtonElement>('[data-action="toggle-packaging-tags"]')?.addEventListener('click', () => { if (packagingPageMutationActive()) return; packagingCatalogControls.showAllTags = !packagingCatalogControls.showAllTags; render(); });
  root.querySelector<HTMLFormElement>('[data-form="recipe-template"]')?.addEventListener('submit', submitRecipeTemplateForm);
  root.querySelectorAll<HTMLInputElement | HTMLTextAreaElement>('[data-form="recipe-template"] [name]').forEach((input) => input.addEventListener('input', () => { saveRecipeTemplateFormFromDom(); clearRecipeTemplateFieldError(input.name, input); }));
  root.querySelector<HTMLFormElement>('[data-form="recipe-version"]')?.addEventListener('submit', submitRecipeVersionForm);
  root.querySelectorAll<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>('[data-form="recipe-version"] [name]').forEach((input) => input.addEventListener('input', () => { saveVersionFormFromDom(); clearRecipeVersionFieldError(input.name, input); }));
  root.querySelectorAll<HTMLSelectElement>('[data-form="recipe-version"] select[name]').forEach((input) => input.addEventListener('change', () => { saveVersionFormFromDom(); clearRecipeVersionFieldError(input.name, input); }));
  root.querySelector<HTMLFormElement>('[data-form="recipe-calculation"]')?.addEventListener('submit', submitCalculationForm);
  root.querySelector<HTMLFormElement>('[data-form="recipe-catalog-category"]')?.addEventListener('submit', (event) => { if (recipePageMutationActive()) { event.preventDefault(); return; } submitRecipeCatalogCategoryForm(event); });
  root.querySelector<HTMLFormElement>('[data-form="recipe-catalog-tag"]')?.addEventListener('submit', (event) => { if (recipePageMutationActive()) { event.preventDefault(); return; } submitRecipeCatalogTagForm(event); });
  root.querySelector<HTMLSelectElement>('[data-action="assign-recipe-category"]')?.addEventListener('change', (event) => { if (recipePageMutationActive()) return; assignRecipeCategory(Number((event.currentTarget as HTMLSelectElement).dataset.id), (event.currentTarget as HTMLSelectElement).value); });
  root.querySelectorAll<HTMLInputElement>('[data-action="toggle-recipe-tag"]').forEach((input) => input.addEventListener('change', () => { if (recipePageMutationActive()) return; assignRecipeTags(Number(input.dataset.recipeTemplateId)); }));
  root.querySelectorAll<HTMLButtonElement>('[data-action="open-recipe"]').forEach((button) => button.addEventListener('click', () => openRecipeTemplate(Number(button.dataset.id))));
  root.querySelectorAll<HTMLButtonElement>('[data-action="open-version"]').forEach((button) => button.addEventListener('click', () => { if (recipePageMutationActive()) return; openRecipeVersion(Number(button.dataset.id)); }));
  root.querySelector<HTMLButtonElement>('[data-action="add-recipe-line"]')?.addEventListener('click', () => { if (recipePageMutationActive()) return; addRecipeLine(); });
  root.querySelectorAll<HTMLButtonElement>('[data-action="remove-recipe-line"]').forEach((button) => button.addEventListener('click', () => { if (recipePageMutationActive()) return; removeRecipeLine(Number(button.dataset.index)); }));
}


function catalogOptions(items: CatalogOption[], search: string) {
  const normalized = search.trim().toLocaleLowerCase('ru-RU');
  if (!normalized) return items;
  return items.filter((item) => item.name.toLocaleLowerCase('ru-RU').includes(normalized));
}


function openIngredientCreateForm() {
  if (ingredientSubmitting) return;
  const current = ingredientsState.formMode === 'edit' && ingredientsState.form.id ? ingredientsState.items.find((ingredient) => ingredient.id === ingredientsState.form.id) ?? null : null;
  if (!confirmDiscardDirtyAssignment(assignmentDraftIsDirty(current, ingredientsState.assignmentDraft))) return;
  ingredientsState.formMode = 'create';
  ingredientsState.form = emptyIngredientForm();
  ingredientsState.assignmentDraft = emptyAssignmentDraft();
  ingredientsState.showCreateForm = true;
  ingredientsMessage = '';
  ingredientsError = '';
  ingredientsRefreshWarning = '';
  ingredientValidation = emptyFormValidationState();
  render();
  focusIngredientFormName();
}

function hideIngredientCreateForm() {
  if (ingredientSubmitting) return;
  ingredientSubmitToken += 1;
  ingredientsState.formMode = 'create';
  ingredientsState.form = emptyIngredientForm();
  ingredientsState.assignmentDraft = emptyAssignmentDraft();
  ingredientsState.showCreateForm = false;
  ingredientsMessage = '';
  ingredientsError = '';
  ingredientsRefreshWarning = '';
  ingredientValidation = emptyFormValidationState();
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


function purchaseSuggestionStatusLabel(status: PurchaseSuggestionStatus) { return ({ open: 'Открыто', purchased: 'Куплено', dismissed: 'Скрыто', archived: 'Архив' } as Record<PurchaseSuggestionStatus, string>)[status] ?? status; }
function purchaseSuggestionItemTypeLabel(type: PurchaseSuggestionItemType | '') { if (!type) return 'Все типы'; return ({ ingredient: 'Компонент', packaging: 'Тара' } as Record<PurchaseSuggestionItemType, string>)[type] ?? type; }
function purchaseSuggestionReasonLabel(reason: PurchaseSuggestionReason | '') { if (!reason) return 'Все причины'; return ({ below_minimum_stock: 'Ниже минимального остатка', insufficient_for_order: 'Не хватает для заказа', predicted_shortage: 'Прогнозируемая нехватка', expiration_replacement: 'Замена из-за срока годности', manual: 'Добавлено вручную' } as Record<PurchaseSuggestionReason, string>)[reason] ?? reason; }
function purchaseSuggestionSourceLabel(suggestion: PurchaseSuggestionResponse) { const id = suggestion.source_entity_id; if (suggestion.source_entity_type === 'manual') return 'Ручное добавление'; const labels: Record<string, string> = { ingredient: 'Компонент', packaging_item: 'Тара', order: 'Заказ', ingredient_lot: 'Партия компонента' }; const label = labels[suggestion.source_entity_type] ?? 'Связанная запись'; return id ? `${label} №${id}` : label; }
function purchaseSuggestionPillClass(value: PurchaseSuggestionStatus) { return value === 'open' ? 'info' : value === 'purchased' ? 'success' : value === 'dismissed' ? 'warning' : 'muted'; }
function purchaseSuggestionReasonOptions(selected: PurchaseSuggestionReasonFilter) { const reasons: PurchaseSuggestionReason[] = ['below_minimum_stock','insufficient_for_order','predicted_shortage','expiration_replacement','manual']; return `<option value="" ${selected === '' ? 'selected' : ''}>Все причины</option>${reasons.map((reason) => `<option value="${reason}" ${selected === reason ? 'selected' : ''}>${purchaseSuggestionReasonLabel(reason)}</option>`).join('')}`; }
function filteredPurchaseSuggestions() { const search = normalizeSearchText(purchaseSuggestionsState.filters.search); if (!search) return purchaseSuggestionsState.items; return purchaseSuggestionsState.items.filter((item) => normalizeSearchText([item.item_name_snapshot, item.message, item.notes, purchaseSuggestionReasonLabel(item.reason), purchaseSuggestionSourceLabel(item), String(item.id), String(item.source_entity_id ?? ''), item.source_entity_type].join(' ')).includes(search)); }
function emptyManualPurchaseSuggestionForm(): PurchaseSuggestionsState['manualForm'] { return { item_type: 'ingredient', item_id: '', recommended_quantity: '', unit: 'g', notes: '' }; }
function defaultPurchaseSuggestionUnit(type: PurchaseSuggestionItemType) { return type === 'ingredient' ? 'g' : 'pcs'; }
function purchaseSuggestionsPage() { const items = filteredPurchaseSuggestions(); return `<div class="catalog-layout"><section class="card catalog-intro"><div><p class="card-kicker">Рабочий помощник</p><h2>Закупки</h2><p>Здесь система собирает предложения, что стоит купить для заказов и минимальных остатков.</p><p class="next-step">Отметка «куплено» закрывает рекомендацию, но не добавляет сырьё или тару на склад. После фактической покупки внесите приход отдельно через партии компонентов или движение тары.</p></div><div class="actions"><button class="primary-action" type="button" data-action="regenerate-purchase-suggestions" ${purchaseSuggestionsState.actionStatus === 'loading' ? 'disabled' : ''}>${purchaseSuggestionsState.actionStatus === 'loading' ? 'Обновляем…' : 'Обновить предложения'}</button><button class="secondary-action" type="button" data-action="open-manual-purchase-form">Добавить вручную</button><button class="secondary-action" type="button" data-action="reload-purchase-suggestions">Загрузить список</button></div></section>${purchaseSuggestionsState.message ? `<p class="page-message">${escapeHtml(purchaseSuggestionsState.message)}</p>` : ''}${purchaseSuggestionsState.error ? `<p class="page-message error-message">${escapeHtml(purchaseSuggestionsState.error)}</p>` : ''}${purchaseSuggestionsState.lastGeneration ? purchaseSuggestionGenerationSummary(purchaseSuggestionsState.lastGeneration) : ''}${purchaseSuggestionFilterToolbar(items.length)}${purchaseSuggestionsState.showManualForm ? manualPurchaseSuggestionForm() : ''}${purchaseSuggestionsState.status === 'loading' || purchaseSuggestionsState.status === 'idle' ? '<section class="card"><h2>Загружаем закупочные предложения…</h2><p>Получаем текущий список из локального приложения.</p></section>' : purchaseSuggestionsState.status === 'error' ? '<section class="card error-card"><p class="card-kicker">Закупки</p><h2>Не удалось загрузить закупочные предложения</h2><p>Проверьте, что локальное приложение запущено.</p><button class="primary-action" type="button" data-action="reload-purchase-suggestions">Повторить загрузку</button></section>' : purchaseSuggestionList(items)}</div>`; }
function purchaseSuggestionGenerationSummary(result: PurchaseSuggestionGenerationResponse) { return `<section class="card data-card"><p class="card-kicker">Результат обновления</p><h2>Предложения обновлены</h2><p>Новых — ${result.created_count}, обновлено — ${result.updated_count}, перенесено в архив — ${result.archived_count}, открытых — ${result.open_count}.</p></section>`; }
function purchaseSuggestionFilterToolbar(resultCount: number) { const f = purchaseSuggestionsState.filters; return `<section class="card data-card catalog-browser"><p class="card-kicker">Фильтры</p><h2>Найти нужную закупку</h2><div class="catalog-toolbar"><label class="full-span">Поиск<input type="search" data-action="filter-purchase-search" value="${escapeHtml(f.search)}" placeholder="Название, сообщение, заметка, причина, источник или номер" /></label><label>Статус<select data-action="filter-purchase-status"><option value="open" ${f.status === 'open' ? 'selected' : ''}>Открыто</option><option value="purchased" ${f.status === 'purchased' ? 'selected' : ''}>Куплено</option><option value="dismissed" ${f.status === 'dismissed' ? 'selected' : ''}>Скрыто</option><option value="archived" ${f.status === 'archived' ? 'selected' : ''}>Архив</option><option value="all" ${f.status === 'all' ? 'selected' : ''}>Все</option></select></label><label>Причина<select data-action="filter-purchase-reason">${purchaseSuggestionReasonOptions(f.reason)}</select></label><label>Тип позиции<select data-action="filter-purchase-item-type"><option value="" ${f.itemType === '' ? 'selected' : ''}>Все типы</option><option value="ingredient" ${f.itemType === 'ingredient' ? 'selected' : ''}>Компонент</option><option value="packaging" ${f.itemType === 'packaging' ? 'selected' : ''}>Тара</option></select></label></div><div class="catalog-summary"><span>Показаны предложения: ${resultCount} из ${purchaseSuggestionsState.items.length}</span><button class="secondary-action compact" type="button" data-action="reset-purchase-filters">Сбросить фильтры</button></div></section>`; }
function manualPurchaseSuggestionForm() { const f = purchaseSuggestionsState.manualForm; const options = f.item_type === 'ingredient' ? ingredientsState.items.filter((i) => i.is_active).map((i) => `<option value="${i.id}" ${f.item_id === String(i.id) ? 'selected' : ''}>${escapeHtml(i.name)}</option>`).join('') : packagingItemsState.items.filter((i) => i.is_active).map((i) => `<option value="${i.id}" ${f.item_id === String(i.id) ? 'selected' : ''}>${escapeHtml(i.name)}</option>`).join(''); return `<section class="card form-card"><p class="card-kicker">Ручное предложение</p><h2>Добавить позицию в закупки</h2><form data-form="manual-purchase-suggestion" class="ingredient-form"><div class="form-grid"><label>Что покупаем<select name="item_type" data-action="manual-purchase-item-type"><option value="ingredient" ${f.item_type === 'ingredient' ? 'selected' : ''}>Компонент</option><option value="packaging" ${f.item_type === 'packaging' ? 'selected' : ''}>Тара</option></select></label><label>Позиция<select name="item_id" required><option value="">Выберите позицию</option>${options}</select></label><label>Сколько купить<input name="recommended_quantity" required inputmode="decimal" value="${escapeHtml(f.recommended_quantity)}" placeholder="Например, 100" /></label><label>Единица<input name="unit" required value="${escapeHtml(f.unit)}" placeholder="g или pcs" /></label><label class="full-span">Заметка<textarea name="notes" rows="3" maxlength="1600" placeholder="Почему добавляете вручную">${escapeHtml(f.notes)}</textarea></label></div><p class="next-step">Это только рекомендация к покупке. Форма не добавляет остатки на склад.</p><div class="actions"><button class="primary-action" type="submit" ${purchaseSuggestionsState.actionStatus === 'loading' ? 'disabled' : ''}>Сохранить предложение</button><button class="secondary-action" type="button" data-action="cancel-manual-purchase-form">Отмена</button></div></form></section>`; }
function purchaseSuggestionList(items: PurchaseSuggestionResponse[]) { if (purchaseSuggestionsState.items.length === 0 && purchaseSuggestionsState.filters.status === 'open' && !purchaseSuggestionsState.filters.reason && !purchaseSuggestionsState.filters.itemType && !purchaseSuggestionsState.filters.search) return `<section class="card empty-card"><h2>Открытых предложений закупки нет</h2><p>Сейчас система не видит позиций, которые нужно купить.</p><p class="next-step">Если вы изменили склад или заказы, нажмите «Обновить предложения».</p></section>`; if (items.length === 0) return `<section class="card empty-card"><h2>По этим фильтрам предложений нет</h2><p>Измените фильтр или сбросьте поиск.</p><button class="secondary-action" type="button" data-action="reset-purchase-filters">Сбросить фильтры</button></section>`; return `<section class="card data-card"><p class="card-kicker">Список</p><h2>Закупочные предложения</h2><div class="recipe-lines">${items.map(purchaseSuggestionCard).join('')}</div></section>`; }
function purchaseSuggestionCard(item: PurchaseSuggestionResponse) { const isEditing = purchaseSuggestionsState.editingSuggestionId === item.id; const closedCopy = item.status === 'purchased' ? 'Это предложение уже закрыто.' : item.status === 'dismissed' ? 'Это предложение скрыто.' : 'Это предложение перенесено в архив.'; const actions = item.status === 'open' ? (isEditing ? purchaseSuggestionEditForm() : `<div class="actions"><button class="secondary-action" type="button" data-action="edit-purchase-suggestion" data-id="${item.id}">Редактировать</button><button class="primary-action" type="button" data-action="mark-purchase-suggestion-purchased" data-id="${item.id}" ${purchaseSuggestionsState.actionStatus === 'loading' ? 'disabled' : ''}>Отметить купленным</button><button class="secondary-action" type="button" data-action="dismiss-purchase-suggestion" data-id="${item.id}" ${purchaseSuggestionsState.actionStatus === 'loading' ? 'disabled' : ''}>Скрыть</button></div>`) : `<p class="next-step">${closedCopy}</p>`; return `<article class="recipe-line alert-card"><div class="section-heading"><div><h3>${escapeHtml(item.item_name_snapshot)}</h3><p><span class="pill ${purchaseSuggestionPillClass(item.status)}">${purchaseSuggestionStatusLabel(item.status)}</span> <span class="pill muted">${purchaseSuggestionItemTypeLabel(item.item_type)}</span> <span class="pill warning">${purchaseSuggestionReasonLabel(item.reason)}</span></p></div><small>Создано: ${formatDateTime(item.created_at)}<br>Обновлено: ${formatDateTime(item.updated_at)}</small></div><div class="readiness-grid"><div><strong>Что купить</strong><p>${escapeHtml(item.item_name_snapshot)}</p></div><div><strong>Сколько</strong><p>${escapeHtml(item.recommended_quantity)} ${escapeHtml(item.unit)}</p></div><div><strong>Почему</strong><p>${purchaseSuggestionReasonLabel(item.reason)}<br>${escapeHtml(item.message || 'Причина описана в типе предложения.')}</p></div><div><strong>Связано с</strong><p>${escapeHtml(purchaseSuggestionSourceLabel(item))}</p></div><div><strong>Заметка</strong><p>${escapeHtml(item.notes || 'Нет заметки')}</p></div><div><strong>Что можно сделать дальше</strong><p>${item.status === 'open' ? 'Проверьте позицию, затем купите и внесите приход отдельно.' : closedCopy}</p></div></div>${actions}</article>`; }
function purchaseSuggestionEditForm() { const f = purchaseSuggestionsState.editForm; return `<form data-form="purchase-suggestion-edit" class="ingredient-form"><div class="form-grid"><label>Сколько купить<input name="recommended_quantity" required inputmode="decimal" value="${escapeHtml(f.recommended_quantity)}" /></label><label>Единица<input name="unit" required value="${escapeHtml(f.unit)}" /></label><label class="full-span">Заметка<textarea name="notes" rows="3" maxlength="1600">${escapeHtml(f.notes)}</textarea></label></div><p class="next-step">Можно менять только количество, единицу и заметку. Позиция, причина и статус не редактируются.</p><div class="actions"><button class="primary-action" type="submit" ${purchaseSuggestionsState.actionStatus === 'loading' ? 'disabled' : ''}>Сохранить</button><button class="secondary-action" type="button" data-action="cancel-purchase-edit">Отмена</button></div></form>`; }
function loadPurchaseSuggestions(force = false) { if (!force && (purchaseSuggestionsState.status === 'loading' || purchaseSuggestionsState.status === 'ready')) return; purchaseSuggestionsState.status = 'loading'; purchaseSuggestionsState.error = ''; render(); Promise.all([getPurchaseSuggestions(purchaseSuggestionsState.filters), getIngredients(), getPackagingItems()]).then(([response, ingredients, packaging]) => { purchaseSuggestionsState.items = response.purchase_suggestions; ingredientsState.items = ingredients.ingredients; packagingItemsState.items = packaging.packaging_items; purchaseSuggestionsState.status = 'ready'; purchaseSuggestionsState.error = ''; render(); }).catch(() => { purchaseSuggestionsState.status = 'error'; purchaseSuggestionsState.error = 'Не удалось загрузить закупочные предложения. Проверьте, что локальное приложение запущено.'; render(); }); }
function reloadPurchaseSuggestionsAfterAction(message: string) { return getPurchaseSuggestions(purchaseSuggestionsState.filters).then((response) => { purchaseSuggestionsState.items = response.purchase_suggestions; purchaseSuggestionsState.status = 'ready'; purchaseSuggestionsState.message = message; purchaseSuggestionsState.error = ''; }); }
function runPurchaseSuggestionRegeneration() { purchaseSuggestionsState.actionStatus = 'loading'; purchaseSuggestionsState.message = ''; purchaseSuggestionsState.error = ''; render(); regeneratePurchaseSuggestions().then((result) => { purchaseSuggestionsState.lastGeneration = result; return reloadPurchaseSuggestionsAfterAction(`Предложения обновлены: новых — ${result.created_count}, обновлено — ${result.updated_count}, перенесено в архив — ${result.archived_count}, открытых — ${result.open_count}.`); }).catch(() => { purchaseSuggestionsState.error = 'Не удалось обновить предложения. Проверьте локальное приложение и попробуйте снова.'; }).finally(() => { purchaseSuggestionsState.actionStatus = 'idle'; render(); }); }
function updatePurchaseSuggestionSearch(input: HTMLInputElement) { const cursor = input.selectionStart ?? input.value.length; purchaseSuggestionsState.filters.search = input.value; render(); const next = document.querySelector<HTMLInputElement>('[data-action="filter-purchase-search"]'); next?.focus(); next?.setSelectionRange(Math.min(cursor, next.value.length), Math.min(cursor, next.value.length)); }
function openManualPurchaseSuggestionForm() { purchaseSuggestionsState.showManualForm = true; purchaseSuggestionsState.manualForm = emptyManualPurchaseSuggestionForm(); purchaseSuggestionsState.message = ''; purchaseSuggestionsState.error = ''; if (!ingredientsState.items.length || !packagingItemsState.items.length) { Promise.all([getIngredients(), getPackagingItems()]).then(([ingredients, packaging]) => { ingredientsState.items = ingredients.ingredients; packagingItemsState.items = packaging.packaging_items; render(); }).catch(() => { purchaseSuggestionsState.error = 'Не удалось загрузить справочники компонентов и тары для ручного предложения.'; render(); }); } render(); }
function syncManualPurchaseSuggestionFormFromDom() { const form = document.querySelector<HTMLFormElement>('[data-form="manual-purchase-suggestion"]'); if (!form) return; const data = new FormData(form); purchaseSuggestionsState.manualForm = { item_type: String(data.get('item_type') ?? purchaseSuggestionsState.manualForm.item_type) as PurchaseSuggestionItemType, item_id: String(data.get('item_id') ?? '').trim(), recommended_quantity: String(data.get('recommended_quantity') ?? '').trim(), unit: String(data.get('unit') ?? '').trim(), notes: String(data.get('notes') ?? '').trim() }; }
function changeManualPurchaseItemType(nextType: PurchaseSuggestionItemType) { syncManualPurchaseSuggestionFormFromDom(); const previousType = purchaseSuggestionsState.manualForm.item_type; const previousDefaultUnit = defaultPurchaseSuggestionUnit(previousType); const nextDefaultUnit = defaultPurchaseSuggestionUnit(nextType); const currentUnit = purchaseSuggestionsState.manualForm.unit.trim(); purchaseSuggestionsState.manualForm = { ...purchaseSuggestionsState.manualForm, item_type: nextType, item_id: '', unit: !currentUnit || currentUnit === previousDefaultUnit ? nextDefaultUnit : currentUnit }; render(); }
function manualPurchaseSuggestionPayload(form: HTMLFormElement): ManualPurchaseSuggestionRequest | string { const data = new FormData(form); const itemType = String(data.get('item_type') ?? 'ingredient') as PurchaseSuggestionItemType; const itemId = String(data.get('item_id') ?? '').trim(); const quantity = String(data.get('recommended_quantity') ?? '').trim(); const unit = String(data.get('unit') ?? '').trim(); const notes = String(data.get('notes') ?? '').trim(); purchaseSuggestionsState.manualForm = { item_type: itemType, item_id: itemId, recommended_quantity: quantity, unit, notes }; if (!itemId) return 'Выберите компонент или тару из списка.'; if (!quantity) return 'Укажите количество для закупки, например 100.'; if (!unit) return 'Укажите единицу измерения, например g или pcs.'; return { item_type: itemType, item_id: Number(itemId), recommended_quantity: quantity, unit, notes }; }
function submitManualPurchaseSuggestionForm(event: SubmitEvent) { event.preventDefault(); const payload = manualPurchaseSuggestionPayload(event.currentTarget as HTMLFormElement); if (typeof payload === 'string') { purchaseSuggestionsState.error = payload; purchaseSuggestionsState.message = ''; render(); return; } purchaseSuggestionsState.actionStatus = 'loading'; purchaseSuggestionsState.error = ''; render(); createManualPurchaseSuggestion(payload).then(() => { purchaseSuggestionsState.showManualForm = false; purchaseSuggestionsState.manualForm = emptyManualPurchaseSuggestionForm(); return reloadPurchaseSuggestionsAfterAction('Предложение добавлено вручную.'); }).catch(() => { purchaseSuggestionsState.error = 'Не удалось сохранить предложение. Проверьте количество, единицу измерения и выбранную позицию.'; }).finally(() => { purchaseSuggestionsState.actionStatus = 'idle'; render(); }); }
function startPurchaseSuggestionEdit(id: number) { const item = purchaseSuggestionsState.items.find((suggestion) => suggestion.id === id); if (!item || item.status !== 'open') return; purchaseSuggestionsState.editingSuggestionId = id; purchaseSuggestionsState.editForm = { recommended_quantity: item.recommended_quantity, unit: item.unit, notes: item.notes }; purchaseSuggestionsState.message = ''; purchaseSuggestionsState.error = ''; render(); }
function submitPurchaseSuggestionEditForm(event: SubmitEvent) { event.preventDefault(); const id = purchaseSuggestionsState.editingSuggestionId; if (!id) return; const data = new FormData(event.currentTarget as HTMLFormElement); const payload = { recommended_quantity: String(data.get('recommended_quantity') ?? '').trim(), unit: String(data.get('unit') ?? '').trim(), notes: String(data.get('notes') ?? '').trim() }; purchaseSuggestionsState.editForm = payload; if (!payload.recommended_quantity || !payload.unit) { purchaseSuggestionsState.error = 'Укажите количество и единицу измерения.'; render(); return; } purchaseSuggestionsState.actionStatus = 'loading'; purchaseSuggestionsState.error = ''; render(); updatePurchaseSuggestion(id, payload).then(() => { purchaseSuggestionsState.editingSuggestionId = null; return reloadPurchaseSuggestionsAfterAction('Предложение обновлено.'); }).catch(() => { purchaseSuggestionsState.error = 'Не удалось сохранить предложение. Проверьте количество, единицу измерения и выбранную позицию.'; }).finally(() => { purchaseSuggestionsState.actionStatus = 'idle'; render(); }); }
function markPurchaseSuggestionAsPurchased(id: number) { purchaseSuggestionsState.actionStatus = 'loading'; purchaseSuggestionsState.message = ''; purchaseSuggestionsState.error = ''; render(); markPurchaseSuggestionPurchased(id).then(() => reloadPurchaseSuggestionsAfterAction('Предложение отмечено как купленное. Склад не изменён — внесите приход отдельно, когда товар фактически поступит.')).catch(() => { purchaseSuggestionsState.error = 'Не удалось отметить предложение купленным. Проверьте локальное приложение и попробуйте снова.'; }).finally(() => { purchaseSuggestionsState.actionStatus = 'idle'; render(); }); }
function dismissPurchaseSuggestionFromCard(id: number) { purchaseSuggestionsState.actionStatus = 'loading'; purchaseSuggestionsState.message = ''; purchaseSuggestionsState.error = ''; render(); dismissPurchaseSuggestion(id).then(() => reloadPurchaseSuggestionsAfterAction('Предложение скрыто.')).catch(() => { purchaseSuggestionsState.error = 'Не удалось скрыть предложение. Проверьте локальное приложение и попробуйте снова.'; }).finally(() => { purchaseSuggestionsState.actionStatus = 'idle'; render(); }); }

function loadDashboard(force = false) {
  if (!force && (dashboardState.status === 'loading' || dashboardState.status === 'ready')) return;
  const hadDataBeforeLoad = dashboardHasData();
  dashboardState.status = 'loading';
  dashboardState.error = '';
  dashboardState.message = '';
  render();
  Promise.all([
    getOrders(true),
    getClients(true),
    getAlerts({ status: 'open', type: '', search: '' }),
    getPurchaseSuggestions({ status: 'open', reason: '', itemType: '', search: '' }),
    getProductionBatches(),
  ]).then(([orders, clients, alerts, purchaseSuggestions, productionBatches]) => {
    dashboardState = {
      status: 'ready',
      error: '',
      message: force ? 'Обзор обновлён. Данные только перечитаны из приложения.' : '',
      orders: orders.orders,
      clients: clients.clients,
      alerts: alerts.alerts,
      purchaseSuggestions: purchaseSuggestions.purchase_suggestions,
      productionBatches: productionBatches.production_batches,
    };
    render();
  }).catch(() => {
    dashboardState.status = 'error';
    dashboardState.error = hadDataBeforeLoad ? 'Не удалось обновить обзор. Показываем последние загруженные данные.' : 'Не удалось загрузить обзор мастерской. Проверьте, что локальное приложение запущено, и попробуйте снова.';
    dashboardState.message = '';
    render();
  });
}

function dashboardPage() {
  const canShowOverview = dashboardCanShowOverview();
  const activeOrders = canShowOverview ? dashboardActiveOrders() : [];
  const waitingOrders = activeOrders.filter((order) => order.status === 'waiting_for_materials');
  const readyOrders = activeOrders.filter((order) => order.status === 'ready_to_produce');
  const recentBatches = canShowOverview ? dashboardState.productionBatches.slice(0, 3) : [];
  return `<div class="dashboard-layout">${dashboardHeader()}${onboardingCard()}${dashboardState.status === 'loading' && !canShowOverview ? dashboardLoadingCard() : ''}${dashboardState.status === 'error' && !canShowOverview ? dashboardErrorCard() : ''}${dashboardState.status === 'error' && canShowOverview ? dashboardSoftErrorMessage() : ''}${dashboardState.status === 'loading' && canShowOverview ? dashboardRefreshingMessage() : ''}${dashboardState.message ? dashboardMessage() : ''}${dashboardDemoDataCard()}${dashboardReportsCard()}${dashboardHelpCard()}${canShowOverview ? `${dashboardPriorityCards(activeOrders, waitingOrders, readyOrders, recentBatches)}${dashboardNextActions(waitingOrders, readyOrders)}<div class="dashboard-columns">${dashboardOrdersBlock(activeOrders)}${dashboardAlertsBlock()}${dashboardPurchaseBlock()}${dashboardProductionBlock(recentBatches)}${dashboardQuickActions()}${dashboardBackupReminder()}</div>` : ''}</div>`;
}

function dashboardHeader() { const isLoading = dashboardState.status === 'loading'; return `<section class="card data-card dashboard-hero"><div><p class="card-kicker">Сегодня в мастерской</p><h2>Сегодня в мастерской</h2><p>Короткий обзор того, что требует внимания: заказы, алерты, закупки и последние партии.</p></div><div class="actions"><button class="secondary-action" type="button" data-action="reload-dashboard" ${isLoading ? 'disabled' : ''}>${isLoading ? 'Обновляем…' : 'Обновить обзор'}</button></div></section>`; }
function dashboardHasData() { return dashboardState.orders.length > 0 || dashboardState.clients.length > 0 || dashboardState.alerts.length > 0 || dashboardState.purchaseSuggestions.length > 0 || dashboardState.productionBatches.length > 0; }
function dashboardCanShowOverview() { return dashboardState.status === 'ready' || (dashboardState.status === 'loading' && dashboardHasData()) || (dashboardState.status === 'error' && dashboardHasData()); }
function dashboardLoadingCard() { return '<section class="card"><p>Загружаем обзор мастерской…</p></section>'; }
function dashboardMessage() { return `<p class="page-message">${escapeHtml(dashboardState.message)}</p>`; }
function dashboardRefreshingMessage() { return '<p class="page-message">Обновляем обзор…</p>'; }
function dashboardSoftErrorMessage() { return `<p class="page-message error-message">${escapeHtml(dashboardState.error || 'Не удалось обновить обзор. Показываем последние загруженные данные.')}</p>`; }
function dashboardErrorCard() { return `<section class="card error-card"><h2>Не удалось загрузить обзор мастерской</h2><p>Проверьте, что локальное приложение запущено, и попробуйте снова.</p><div class="actions"><button class="secondary-action" type="button" data-action="reload-dashboard">Повторить</button></div></section>`; }
function dashboardActiveOrders() { return dashboardState.orders.filter((order) => order.is_active && !['cancelled', 'archived', 'delivered'].includes(order.status)); }
function dashboardPriorityCards(activeOrders: Order[], waitingOrders: Order[], readyOrders: Order[], recentBatches: ProductionBatchListItem[]) { const cards = [['Активные заказы', activeOrders.length], ['Ждут материалов', waitingOrders.length], ['Готовы к производству', readyOrders.length], ['Открытые алерты', dashboardState.alerts.length], ['Купить', dashboardState.purchaseSuggestions.length], ['Последние партии', recentBatches.length]]; return `<section class="overview-grid">${cards.map(([label, value]) => `<div class="metric-card"><span>${escapeHtml(String(label))}</span><strong>${value}</strong></div>`).join('')}</section>`; }
function dashboardNextActions(waitingOrders: Order[], readyOrders: Order[]) { const hasCriticalAlerts = dashboardState.alerts.some((alert) => alert.severity === 'critical' || alert.severity === 'blocking'); const actions: string[] = []; if (hasCriticalAlerts) actions.push('Сначала проверьте критичные алерты.'); if (waitingOrders.length) actions.push('Проверьте заказы, которые ждут компонентов или тары.'); if (dashboardState.purchaseSuggestions.length) actions.push('Откройте закупки и обработайте позиции, которые нужно купить.'); if (readyOrders.length) actions.push('Есть заказы, которые можно готовить к изготовлению.'); if (!actions.length) actions.push('Критичных задач сейчас нет. Можно продолжать плановую работу.'); return `<section class="card data-card"><p class="card-kicker">Что сделать сегодня</p><h2>Следующие шаги</h2><ul class="checklist dashboard-actions-list">${actions.map((action, index) => `<li><span>${index + 1}</span><strong>${escapeHtml(action)}</strong><small>Это подсказка по текущим данным. Действия выполняются только в соответствующих разделах.</small></li>`).join('')}</ul></section>`; }
function dashboardOrdersBlock(activeOrders: Order[]) { return dashboardSection('Активные заказы', 'Что сейчас в работе', activeOrders.length ? activeOrders.slice(0, 5).map((order) => `<article class="dashboard-list-item"><strong>Заказ №${order.id} · ${escapeHtml(order.product_name || 'Продукт не указан')}</strong><small>${orderClientLabel(order)} · ${orderStatusLabel(order.status)} · ${quantityLabel(order.target_batch_size_value, order.target_batch_size_unit)}</small></article>`).join('') : '<p class="empty-hint">Активных заказов пока нет.</p>', 'Открыть заказы', 'Заказы'); }
function dashboardAlertsBlock() { return dashboardSection('Алерты', 'Что требует внимания', dashboardState.alerts.length ? dashboardState.alerts.slice(0, 5).map((alert) => `<article class="dashboard-list-item"><strong>${alertSeverityLabel(alert.severity)} · ${alertTypeLabel(alert.type)}</strong><small>${escapeHtml(alert.message)}</small>${alert.recommended_action ? `<small>Что сделать: ${escapeHtml(alert.recommended_action)}</small>` : ''}</article>`).join('') : '<p class="empty-hint">Открытых алертов нет.</p>', 'Открыть алерты', 'Алерты'); }
function dashboardPurchaseBlock() { return dashboardSection('Закупки', 'Что нужно купить', dashboardState.purchaseSuggestions.length ? dashboardState.purchaseSuggestions.slice(0, 5).map((suggestion) => `<article class="dashboard-list-item"><strong>${escapeHtml(suggestion.item_name_snapshot)}</strong><small>${quantityLabel(suggestion.recommended_quantity, suggestion.unit)} · ${purchaseSuggestionReasonLabel(suggestion.reason)}</small>${suggestion.message ? `<small>${escapeHtml(suggestion.message)}</small>` : ''}${suggestion.notes ? `<small>Заметка: ${escapeHtml(suggestion.notes)}</small>` : ''}</article>`).join('') : '<p class="empty-hint">Открытых закупочных предложений нет.</p>', 'Открыть закупки', 'Закупки'); }
function dashboardProductionBlock(recentBatches: ProductionBatchListItem[]) { return dashboardSection('Последние партии', 'Что уже изготовлено', recentBatches.length ? recentBatches.map((batch) => `<article class="dashboard-list-item"><strong>${formatDateTime(batch.produced_at)} · ${escapeHtml(batch.product_name || 'Продукт не указан')}</strong><small>${escapeHtml(batch.client_name || 'Клиент не указан')} · ${quantityLabel(batch.final_batch_value, batch.final_batch_unit)} · ${moneyOrMissing(batch.total_cost)}</small></article>`).join('') : '<p class="empty-hint">Изготовленных партий пока нет.</p>', 'Открыть производство', 'Производство'); }
function dashboardQuickActions() { const actions: Array<[string, NavigationSection]> = [['Новый заказ', 'Заказы'], ['Компоненты', 'Компоненты'], ['Партии компонентов', 'Партии'], ['Тара', 'Тара'], ['Алерты', 'Алерты'], ['Закупки', 'Закупки'], ['Производство', 'Производство']]; return `<section class="card data-card"><p class="card-kicker">Быстрые действия</p><h2>Куда перейти</h2><div class="actions">${actions.map(([label, section]) => `<button class="secondary-action" type="button" data-nav-section="${section}">${label}</button>`).join('')}</div><p class="next-step">Кнопки только открывают существующие разделы и не меняют данные.</p></section>`; }
function dashboardDemoDataCard() { return `<section class="card data-card"><p class="card-kicker">Пример для знакомства</p><h2>Демо-данные</h2><p>Хотите посмотреть пример заполненной мастерской? Откройте демо-режим.</p><div class="actions"><button class="secondary-action compact" type="button" data-nav-section="Демо-данные">Открыть демо-данные</button></div><p class="next-step">Кнопка только открывает раздел. Установка и очистка запускаются там отдельным явным подтверждением.</p></section>`; }
function dashboardReportsCard() { return `<section class="card data-card"><p class="card-kicker">Отчёты</p><h2>Сводка мастерской</h2><p>Посмотреть сводку по складу, заказам, производству и финансам.</p><div class="actions"><button class="secondary-action compact" type="button" data-nav-section="Отчеты">Открыть отчёты</button></div><p class="next-step">Кнопка открывает сводку и не меняет данные мастерской.</p></section>`; }

function dashboardHelpCard() { return `<section class="card data-card"><p class="card-kicker">Подсказки</p><h2>Помощь по мастерской</h2><p>Короткие объяснения основных разделов: склад, рецепты, заказы, импорт и безопасность данных.</p><div class="actions"><button class="secondary-action compact" type="button" data-nav-section="Помощь">Открыть помощь</button></div><p class="next-step">Кнопка только открывает справку и ничего не меняет в данных.</p></section>`; }
function dashboardBackupReminder() { return `<section class="card data-card"><p class="card-kicker">Резервная копия</p><h2>Резервная копия перед важными изменениями</h2><p>Перед большим импортом, обновлением приложения или существенными изменениями рабочих данных создайте резервную копию.</p><div class="actions"><button class="secondary-action compact" type="button" data-nav-section="Резервные копии">Открыть резервные копии</button></div><p class="next-step">Кнопка только открывает раздел. Резервная копия создаётся там отдельным явным нажатием.</p></section>`; }
function dashboardSection(kicker: string, title: string, body: string, buttonLabel: string, section: NavigationSection) { return `<section class="card data-card dashboard-section"><div class="section-heading"><div><p class="card-kicker">${escapeHtml(kicker)}</p><h2>${escapeHtml(title)}</h2></div><button class="secondary-action compact" type="button" data-nav-section="${section}">${escapeHtml(buttonLabel)}</button></div><div class="dashboard-list">${body}</div></section>`; }
function orderClientLabel(order: Order) { const client = dashboardState.clients.find((item) => item.id === order.client_id) ?? null; return client?.full_name ? escapeHtml(client.full_name) : `Клиент №${order.client_id}`; }






function productionPage() {
  const visible = filteredProductionBatches();
  return `<section class="card"><p class="card-kicker">История изготовленных партий</p><h2>Производство</h2><p>Здесь показаны уже изготовленные партии. Это исторический журнал: данные партии и списания не редактируются.</p><div class="actions"><button class="secondary-action" type="button" data-action="reload-production-history">Обновить историю</button></div></section>${productionHistoryToolbar()}${productionHistoryState.error ? `<p class="page-message error-message">${escapeHtml(productionHistoryState.error)}</p>` : ''}${productionHistoryState.status === 'loading' ? '<section class="card"><p>Загружаем историю производства…</p></section>' : productionHistoryList(visible)}${productionHistoryDetailPanel()}`;
}
function productionHistoryToolbar() { return `<section class="card filter-card"><label>Поиск по истории<input data-action="filter-production-search" value="${escapeHtml(productionHistoryState.filters.search)}" placeholder="Продукт, клиент, заметка, номер заказа или партии" /></label></section>`; }
function filteredProductionBatches() { const q=productionHistoryState.filters.search.trim().toLowerCase(); if(!q) return productionHistoryState.batches; return productionHistoryState.batches.filter((b)=>[b.product_name,b.client_name??'',b.notes,String(b.order_id),String(b.id)].some((v)=>v.toLowerCase().includes(q))); }
function loadBackups(force = false) {
  if (!force && (backupUiState.status === 'loading' || backupUiState.status === 'ready')) return;
  backupUiState.status = 'loading';
  backupUiState.error = '';
  if (force) backupUiState.message = '';
  render();
  Promise.all([getBackupStatus(), getBackups()])
    .then(([status, list]) => {
      backupUiState.status = 'ready';
      backupUiState.backupStatus = status;
      backupUiState.backups = list.backups;
      backupUiState.error = '';
      render();
    })
    .catch(() => {
      backupUiState.status = 'error';
      backupUiState.error = 'Не удалось загрузить сведения о резервных копиях. Проверьте, что локальное приложение запущено, и попробуйте снова.';
      render();
    });
}

function submitBackupCreateForm(event: SubmitEvent) { event.preventDefault(); submitBackupCreate(); }
function submitBackupCreate() {
  if (backupUiState.actionStatus === 'creating') return;
  const status = backupUiState.backupStatus;
  if (!status?.database_exists) {
    backupUiState.error = 'База данных пока не найдена. Сначала запустите приложение и создайте рабочие данные.';
    backupUiState.message = '';
    render();
    return;
  }
  const rawReason = backupUiState.reason === 'custom' ? backupUiState.customReason.trim() : backupUiState.reason;
  const reason = rawReason || 'manual';
  backupUiState.actionStatus = 'creating';
  backupUiState.error = '';
  backupUiState.message = '';
  render();
  createBackup({ reason })
    .then((response) => {
      backupUiState.lastCreatedBackup = response.backup;
      backupUiState.message = `${response.message || 'Резервная копия создана.'} Файл: ${response.backup.filename}`;
      return Promise.all([getBackupStatus(), getBackups()]);
    })
    .then(([statusResponse, list]) => {
      backupUiState.backupStatus = statusResponse;
      backupUiState.backups = list.backups;
      backupUiState.status = 'ready';
      backupUiState.actionStatus = 'idle';
      render();
    })
    .catch(() => {
      backupUiState.actionStatus = 'idle';
      backupUiState.error = 'Не удалось создать резервную копию. Проверьте, что база данных существует и локальное приложение запущено.';
      backupUiState.message = '';
      render();
    });
}


function loadExports(force = false) {
  if (!force && (exportUiState.status === 'loading' || exportUiState.status === 'ready')) return;
  exportUiState.status = 'loading';
  exportUiState.error = '';
  if (force) exportUiState.message = '';
  render();
  Promise.all([getExportStatus(), getExports()])
    .then(([status, list]) => {
      exportUiState.status = 'ready';
      exportUiState.exportStatus = status;
      exportUiState.exports = list.exports;
      exportUiState.error = '';
      render();
    })
    .catch(() => {
      exportUiState.status = 'error';
      exportUiState.error = 'Не удалось загрузить сведения об экспортах. Проверьте, что локальное приложение запущено, и попробуйте снова.';
      render();
    });
}

function submitExportCreateForm(event: SubmitEvent) { event.preventDefault(); submitExportCreate(); }
function submitExportCreate() {
  if (exportUiState.actionStatus === 'creating') return;
  const status = exportUiState.exportStatus;
  if (!status?.database_exists) {
    exportUiState.error = 'База данных пока не найдена. Сначала запустите приложение и создайте рабочие данные.';
    exportUiState.message = '';
    render();
    return;
  }
  const rawReason = exportUiState.reason === 'custom' ? exportUiState.customReason.trim() : exportUiState.reason;
  const reason = rawReason || 'manual';
  exportUiState.actionStatus = 'creating';
  exportUiState.error = '';
  exportUiState.message = '';
  clearFeedbackAnnouncement();
  render();
  createExport({ reason })
    .then((response) => {
      exportUiState.lastCreatedExport = response.export;
      exportUiState.lastEntityCounts = response.entity_counts || {};
      const successMessage = `${response.message || 'Экспорт создан.'} Файл: ${response.export.filename}`;
      exportUiState.message = successMessage;
      announcePolite(successMessage);
      return Promise.all([getExportStatus(), getExports()])
        .then(([statusResponse, list]) => {
          exportUiState.exportStatus = statusResponse;
          exportUiState.exports = list.exports;
          exportUiState.status = 'ready';
          exportUiState.actionStatus = 'idle';
          render();
        })
        .catch(() => {
          exportUiState.status = 'ready';
          exportUiState.actionStatus = 'idle';
          exportUiState.error = '';
          exportUiState.message = `${successMessage} Не удалось обновить список экспортов. Нажмите «Обновить», чтобы перечитать данные.`;
          render();
        });
    })
    .catch(() => {
      exportUiState.actionStatus = 'idle';
      exportUiState.error = 'Не удалось создать экспорт. Проверьте, что база данных существует и локальное приложение запущено.';
      exportUiState.message = '';
      announceAssertive(exportUiState.error);
      render();
    });
}

function exportPage() {
  const isLoading = exportUiState.status === 'loading';
  const status = exportUiState.exportStatus;
  const createDisabled = exportUiState.actionStatus === 'creating' || isLoading || !status?.database_exists;
  return `<div class="page-grid backup-page">
    <section class="card data-card dashboard-hero">
      <div><p class="card-kicker">Копия данных для проверки и переноса</p><h2>Экспорт данных</h2><p>Экспорт создаёт отдельный локальный файл с копией основных данных мастерской. Файл сохраняется в формате JSON и не изменяет рабочие записи.</p><p class="next-step">Файл сохраняется локально на этом MacBook в папке экспортов. Загрузить его обратно через этот экран нельзя.</p></div>
      <div class="actions"><button class="secondary-action" type="button" data-action="reload-exports" ${isLoading ? 'disabled' : ''}>${isLoading ? 'Обновляем…' : 'Обновить'}</button><button class="primary-action" type="button" data-action="create-export" ${createDisabled ? 'disabled' : ''}>${exportUiState.actionStatus === 'creating' ? 'Создаём экспорт…' : 'Создать экспорт'}</button></div>
    </section>
    ${exportUiState.error ? feedbackMessage('error', exportUiState.error) : ''}
    ${exportUiState.message ? feedbackMessage('success', exportUiState.message) : ''}
    ${exportUiState.status === 'error' && !status ? exportLoadErrorCard() : `${exportStatusCards()}${exportCreateCard()}${exportEntityCountsCard()}${exportHistoryCard()}${exportNonGoalsCard()}`}
  </div>`;
}

function exportLoadErrorCard() { return `<section class="card error-card"><h2>Сведения недоступны</h2><p>Не удалось загрузить сведения об экспортах.</p><p>Проверьте, что локальное приложение запущено, и попробуйте снова.</p><div class="actions"><button class="secondary-action" type="button" data-action="reload-exports">Обновить</button></div></section>`; }
function exportStatusCards() {
  const status = exportUiState.exportStatus;
  if (exportUiState.status === 'loading' && !status) return '<section class="card"><p>Загружаем сведения о базе и экспортах…</p></section>';
  if (!status) return '';
  const latest = status.latest_export ? `${escapeHtml(status.latest_export.filename)} · ${formatDateTime(status.latest_export.created_at || '')}` : 'Пока нет';
  return `<section class="overview-grid">
    <div class="metric-card"><span>База данных</span><strong>${status.database_exists ? 'База найдена' : 'База данных пока не найдена'}</strong></div>
    <div class="metric-card wide"><span>Расположение базы</span><strong class="path-text">${escapeHtml(status.database_path)}</strong></div>
    <div class="metric-card"><span>Размер базы</span><strong>${formatFileSize(status.database_size_bytes)}</strong></div>
    <div class="metric-card wide"><span>Папка экспорта</span><strong>${status.export_dir_exists ? 'Папка экспортов найдена' : 'Папка экспортов ещё не создана. Она появится после первого созданного экспорта.'}</strong><small class="path-text">${escapeHtml(status.export_dir)}</small></div>
    <div class="metric-card"><span>Количество экспортов</span><strong>${status.export_count}</strong></div>
    <div class="metric-card wide"><span>Последний экспорт</span><strong>${latest}</strong></div>
  </section>`;
}
function exportCreateCard() {
  const status = exportUiState.exportStatus;
  const disabled = exportUiState.actionStatus === 'creating' || exportUiState.status === 'loading' || !status?.database_exists;
  return `<section class="card data-card"><p class="card-kicker">Явное действие</p><h2>Создать экспорт</h2><p>Экспорт включает основные данные: рецепты, клиентов, заказы, склад, производство, алерты и закупки. Этот файл можно использовать для проверки или переноса данных, но загрузить его обратно через этот экран нельзя.</p>${!status?.database_exists ? feedbackMessage('error', 'Сначала запустите приложение и создайте рабочую базу данных.') : ''}<form class="form-grid" data-form="export-create" aria-busy="${exportUiState.actionStatus === 'creating' ? 'true' : 'false'}"><label>Причина<select name="reason" data-action="select-export-reason"><option value="manual" ${exportUiState.reason === 'manual' ? 'selected' : ''}>Обычный экспорт</option><option value="before_import" ${exportUiState.reason === 'before_import' ? 'selected' : ''}>Перед импортом</option><option value="before_update" ${exportUiState.reason === 'before_update' ? 'selected' : ''}>Перед обновлением приложения</option><option value="before_large_edit" ${exportUiState.reason === 'before_large_edit' ? 'selected' : ''}>Перед крупными изменениями</option><option value="support_snapshot" ${exportUiState.reason === 'support_snapshot' ? 'selected' : ''}>Для поддержки</option><option value="custom" ${exportUiState.reason === 'custom' ? 'selected' : ''}>Своя причина</option></select></label>${exportUiState.reason === 'custom' ? `<label>Своя причина<input name="customReason" maxlength="80" value="${escapeHtml(exportUiState.customReason)}" data-action="custom-export-reason" placeholder="Например: перед обращением в поддержку" /></label>` : ''}<div class="actions"><button class="primary-action" type="submit" ${disabled ? 'disabled' : ''}>${exportUiState.actionStatus === 'creating' ? 'Создаём экспорт…' : 'Создать экспорт'}</button></div></form>${exportUiState.lastCreatedExport ? `<p class="next-step">Последний созданный файл экспорта: <strong>${escapeHtml(exportUiState.lastCreatedExport.filename)}</strong></p>` : '<p class="next-step">Создание экспорта не запускается автоматически и не меняет рабочие данные.</p>'}</section>`;
}
function exportEntityCountsCard() {
  const entries = Object.entries(exportUiState.lastEntityCounts || {});
  if (!entries.length) return '';
  return `<section class="card data-card"><div class="section-heading"><div><p class="card-kicker">Снимок данных</p><h2>Что попало в экспорт</h2></div><span class="pill info">${entries.length}</span></div><div class="overview-grid compact-overview">${entries.map(([key, value]) => `<div class="metric-card"><span>${exportEntityLabel(key)}</span><strong>${value}</strong></div>`).join('')}</div><p class="next-step">Здесь показано количество записей, включённых в созданный файл. Рабочие данные при этом не изменяются.</p></section>`;
}
function exportHistoryCard() {
  if (!exportUiState.exports.length) return `<section class="card empty-card"><h2>История экспортов</h2><p>Экспортов пока нет.</p><p>Создайте первый экспорт перед импортом, переносом или крупными изменениями.</p></section>`;
  return `<section class="card data-card"><div class="section-heading"><div><p class="card-kicker">Локальные файлы экспорта</p><h2>История экспортов</h2></div><span class="pill info">${exportUiState.exports.length}</span></div><div class="backup-list">${exportUiState.exports.map(exportHistoryItem).join('')}</div></section>`;
}
function exportHistoryItem(item: ExportFileResponse) { return `<article class="recipe-line backup-item"><div class="section-heading"><div><h3>${escapeHtml(item.filename)}</h3><p><span class="pill info">${exportReasonLabel(item.reason)}</span> <span class="pill muted">${formatFileSize(item.size_bytes)}</span></p></div><small>${formatDateTime(item.created_at || '')}</small></div><p><strong>Локальный путь:</strong><br><code class="path-text">${escapeHtml(item.path)}</code></p><p class="next-step">Это отдельная копия данных. Загрузить её обратно через этот экран нельзя.</p></article>`; }
function exportNonGoalsCard() { return `<section class="card data-card"><p class="card-kicker">Границы экрана</p><h2>Что важно знать</h2><ul class="checklist compact-list"><li>Экспорт создаётся только после явного нажатия.</li><li>Файл хранится локально на этом MacBook.</li><li>Экспорт не изменяет рабочие данные.</li><li>Загрузить файл экспорта обратно через этот экран нельзя.</li><li>На этом экране не создаются CSV, XLSX или PDF-файлы.</li><li>Автоматическая отправка файлов в облако не выполняется.</li></ul></section>`; }
function exportReasonLabel(reason: string | null): string { return ({ manual: 'Обычный экспорт', before_import: 'Перед импортом', before_update: 'Перед обновлением', before_large_edit: 'Перед крупными изменениями', support_snapshot: 'Для поддержки' } as Record<string, string>)[reason || ''] ?? (reason ? escapeHtml(reason) : 'Не указана'); }
function exportEntityLabel(key: string): string {
  return ({
    app_settings: 'Настройки приложения',
    ingredients: 'Компоненты',
    ingredient_lots: 'Партии компонентов',
    stock_movements: 'Движения сырья',
    packaging_items: 'Тара',
    packaging_stock_movements: 'Движения тары',
    catalog_categories: 'Группы каталога',
    catalog_tags: 'Метки каталога',
    ingredient_catalog_tags: 'Метки компонентов',
    packaging_item_catalog_tags: 'Метки тары',
    recipe_template_catalog_tags: 'Метки рецептов',
    recipe_templates: 'Рецепты',
    recipe_versions: 'Версии рецептов',
    recipe_ingredients: 'Составы версий',
    clients: 'Клиенты',
    client_recipes: 'Индивидуальные рецепты',
    client_recipe_ingredients: 'Составы индивидуальных рецептов',
    client_wishes: 'Пожелания клиентов',
    client_feedback: 'Обратная связь',
    orders: 'Заказы',
    production_batches: 'Производственные партии',
    production_batch_ingredients: 'Списания компонентов',
    production_batch_packaging: 'Списания тары',
    alerts: 'Алерты',
    purchase_suggestions: 'Закупочные предложения',
    audit_logs: 'Журнал действий',
  } as Record<string, string>)[key] ?? escapeHtml(key);
}


function loadDemoDataStatus(force = false) {
  if (!force && (demoDataUiState.status === 'loading' || demoDataUiState.status === 'ready')) return;
  demoDataUiState.status = 'loading';
  demoDataUiState.error = '';
  if (force) demoDataUiState.message = '';
  render();
  getDemoDataStatus()
    .then((status) => { demoDataUiState.status = 'ready'; demoDataUiState.demoStatus = status; demoDataUiState.error = ''; render(); })
    .catch(() => { demoDataUiState.status = 'error'; demoDataUiState.error = 'Не удалось загрузить статус демо-данных. Проверьте, что локальное приложение запущено.'; render(); });
}
function showDemoInstallConfirm() { demoDataUiState.showInstallConfirm = true; demoDataUiState.showClearConfirm = false; demoDataUiState.error = ''; demoDataUiState.message = ''; render(); }
function hideDemoInstallConfirm() { demoDataUiState.showInstallConfirm = false; demoDataUiState.installConfirmChecked = false; demoDataUiState.understandDemoChecked = false; render(); }
function updateDemoInstallChecks() { demoDataUiState.installConfirmChecked = !!document.querySelector<HTMLInputElement>('input[name="demo_install_confirm"]')?.checked; demoDataUiState.understandDemoChecked = !!document.querySelector<HTMLInputElement>('input[name="demo_understand"]')?.checked; render(); }
function showDemoClearConfirm() { demoDataUiState.showClearConfirm = true; demoDataUiState.showInstallConfirm = false; demoDataUiState.error = ''; demoDataUiState.message = ''; render(); }
function hideDemoClearConfirm() { demoDataUiState.showClearConfirm = false; demoDataUiState.clearConfirmChecked = false; render(); }
function updateDemoClearChecks() { demoDataUiState.clearConfirmChecked = !!document.querySelector<HTMLInputElement>('input[name="demo_clear_confirm"]')?.checked; render(); }
function demoErrorDetails(error: unknown) { const message = error instanceof Error ? error.message : ''; return message && message !== 'API request failed' ? ` ${message}` : ''; }
function refreshDemoStatusAfterActionError(errorMessage: string) {
  demoDataUiState.error = errorMessage;
  demoDataUiState.message = '';
  announceAssertive(errorMessage);
  return getDemoDataStatus()
    .then((status) => { demoDataUiState.demoStatus = status; demoDataUiState.status = 'ready'; })
    .catch(() => { if (!demoDataUiState.demoStatus) demoDataUiState.status = 'error'; })
    .finally(() => { demoDataUiState.actionStatus = 'idle'; render(); });
}
function installDemoDataFromUi() {
  if (demoDataUiState.actionStatus !== 'idle') return;
  if (!demoDataUiState.demoStatus?.can_install || !demoDataUiState.installConfirmChecked || !demoDataUiState.understandDemoChecked) return;
  demoDataUiState.actionStatus = 'installing'; demoDataUiState.error = ''; demoDataUiState.message = ''; clearFeedbackAnnouncement(); render();
  installDemoData({ confirm_install: true, understand_demo_data: true })
    .then((response) => {
      demoDataUiState.lastInstallResult = response;
      demoDataUiState.lastClearResult = null;
      const successMessage = response.message || 'Демо-данные установлены. Теперь можно открыть разделы и посмотреть пример работы.';
      demoDataUiState.message = successMessage;
      announcePolite(successMessage);
      demoDataUiState.showInstallConfirm = false;
      demoDataUiState.installConfirmChecked = false;
      demoDataUiState.understandDemoChecked = false;
      return getDemoDataStatus()
        .then((status) => { demoDataUiState.demoStatus = status; demoDataUiState.status = 'ready'; demoDataUiState.actionStatus = 'idle'; render(); })
        .catch(() => { demoDataUiState.status = 'ready'; demoDataUiState.actionStatus = 'idle'; demoDataUiState.error = ''; demoDataUiState.message = `${successMessage} Не удалось обновить статус демо-данных. Нажмите «Обновить статус», чтобы перечитать данные.`; render(); });
    })
    .catch((error) => { const message = `Не удалось установить демо-данные. Рабочие данные не были частично изменены.${demoErrorDetails(error)}`; refreshDemoStatusAfterActionError(message); });
}
function clearDemoDataFromUi() {
  if (demoDataUiState.actionStatus !== 'idle') return;
  if (!demoDataUiState.demoStatus?.can_clear || !demoDataUiState.clearConfirmChecked) return;
  demoDataUiState.actionStatus = 'clearing'; demoDataUiState.error = ''; demoDataUiState.message = ''; clearFeedbackAnnouncement(); render();
  clearDemoData({ confirm_clear: true })
    .then((response) => {
      demoDataUiState.lastClearResult = response;
      demoDataUiState.lastInstallResult = null;
      const successMessage = response.message || 'Демо-данные очищены.';
      demoDataUiState.message = successMessage;
      announcePolite(successMessage);
      demoDataUiState.showClearConfirm = false;
      demoDataUiState.clearConfirmChecked = false;
      return getDemoDataStatus()
        .then((status) => { demoDataUiState.demoStatus = status; demoDataUiState.status = 'ready'; demoDataUiState.actionStatus = 'idle'; render(); })
        .catch(() => { demoDataUiState.status = 'ready'; demoDataUiState.actionStatus = 'idle'; demoDataUiState.error = ''; demoDataUiState.message = `${successMessage} Не удалось обновить статус демо-данных. Нажмите «Обновить статус», чтобы перечитать данные.`; render(); });
    })
    .catch((error) => { const message = `Не удалось очистить демо-данные. Реальные данные не удалялись.${demoErrorDetails(error)}`; refreshDemoStatusAfterActionError(message); });
}
function demoDataPage() {
  const isLoading = demoDataUiState.status === 'loading';
  const status = demoDataUiState.demoStatus;
  return `<div class="page-grid backup-page demo-data-page">
    <section class="card data-card dashboard-hero"><div><p class="card-kicker">Безопасный пример</p><h2>Демо-данные</h2><p>Включите демонстрационный набор, чтобы посмотреть, как работает мастерская: склад, рецепты, клиенты, заказы, готовность производства, алерты и закупки.</p><p class="next-step">Демо-данные не устанавливаются автоматически. Их можно добавить только вручную и только если рабочая база подходит для этого.</p></div><div class="actions"><button class="secondary-action" type="button" data-action="reload-demo-data" ${isLoading ? 'disabled' : ''}>${isLoading ? 'Обновляем…' : 'Обновить статус'}</button></div></section>
    ${demoDataUiState.error ? feedbackMessage('error', demoDataUiState.error) : ''}
    ${demoDataUiState.message ? feedbackMessage('success', demoDataUiState.message) : ''}
    ${demoDataUiState.status === 'error' && !status ? demoLoadErrorCard() : `${demoStatusCards()}${demoDatasetCard()}${demoInstallCard()}${demoClearCard()}${demoCountsCard()}${demoBoundariesCard()}`}
  </div>`;
}
function demoLoadErrorCard() { return `<section class="card error-card"><h2>Статус недоступен</h2><p>Не удалось загрузить статус демо-данных. Проверьте, что локальное приложение запущено.</p><div class="actions"><button class="secondary-action" type="button" data-action="reload-demo-data">Повторить</button></div></section>`; }
function demoStatusCards() { const s = demoDataUiState.demoStatus; if (demoDataUiState.status === 'loading' && !s) return '<section class="card"><p>Загружаем статус демо-режима…</p></section>'; if (!s) return ''; return `<section class="overview-grid"><div class="metric-card"><span>Статус демо-режима</span><strong>${s.is_installed ? 'Демо-данные установлены' : 'Демо-данные ещё не установлены'}</strong></div><div class="metric-card"><span>Версия демо-набора</span><strong>${escapeHtml(s.demo_version || 'Не указана')}</strong></div><div class="metric-card"><span>Можно установить</span><strong>${s.can_install ? 'Да' : 'Нет'}</strong></div><div class="metric-card"><span>Можно очистить</span><strong>${s.can_clear ? 'Да' : 'Нет'}</strong></div><div class="metric-card"><span>Рабочие данные в базе</span><strong>${s.has_business_data ? 'В базе есть рабочие данные' : 'В базе нет рабочих данных'}</strong></div><div class="metric-card"><span>Недемо-данные</span><strong>${s.has_non_demo_business_data ? 'Есть' : 'Нет'}</strong></div>${s.active_session_id ? `<div class="metric-card"><span>Активная демо-сессия</span><strong>#${s.active_session_id}</strong></div>` : ''}</section>${s.message ? feedbackMessage('neutral', s.message) : ''}${demoBlockingReasons(s.blocking_reasons)}`; }
function demoBlockingReasons(reasons: string[] = []) { if (!reasons.length) return ''; return `<section class="card error-card"><h2>Действие сейчас недоступно</h2><p>Причины блокировки:</p><ul class="issue-list">${reasons.map((reason) => `<li>${escapeHtml(reason)}</li>`).join('')}</ul></section>`; }
function demoDatasetCard() { return `<section class="card data-card"><p class="card-kicker">Что будет добавлено</p><h2>Пример заполненной мастерской</h2><p>Демо-набор создаёт примерные записи с префиксом «Демо ·»: компоненты, партии, движения, тару, рецепты, клиентов и заказы. Производство не запускается автоматически.</p><ul class="checklist compact-list"><li>Компоненты и партии</li><li>Тара и движения тары</li><li>Рецепты и версии</li><li>Клиенты и индивидуальный рецепт</li><li>Заказы для проверки готовности</li><li>Условия для алертов и закупок</li></ul></section>`; }
function demoInstallCard() { const s = demoDataUiState.demoStatus; if (!s || s.is_installed) return ''; const disabled = demoDataUiState.actionStatus !== 'idle' || !s.can_install; return `<section class="card data-card"><p class="card-kicker">Явное действие</p><h2>Установить демо-данные</h2>${!s.can_install ? `${feedbackMessage('error', 'Сейчас демо-данные нельзя установить. Причины указаны ниже.')}${s.has_non_demo_business_data ? '<p class="warning-text">В этой базе уже есть рабочие данные. Чтобы не смешивать их с примером, установка демо-данных заблокирована.</p>' : ''}` : '<p>После установки появится примерный сценарий для знакомства с разделами приложения.</p>'}<div class="actions"><button class="primary-action" type="button" data-action="show-demo-install-confirm" ${disabled ? 'disabled' : ''}>Перейти к установке</button></div>${demoDataUiState.showInstallConfirm ? demoInstallConfirmPanel() : ''}</section>`; }
function demoInstallConfirmPanel() { const disabled = demoDataUiState.actionStatus === 'installing' || !demoDataUiState.installConfirmChecked || !demoDataUiState.understandDemoChecked; return `<div class="confirm-panel" aria-busy="${demoDataUiState.actionStatus === 'installing' ? 'true' : 'false'}"><h3>Подтвердите установку демо-данных</h3><p>После установки в базе появятся примерные записи с префиксом «Демо ·». Это поможет посмотреть рабочий сценарий, но не заменяет ваши реальные данные.</p><label class="checkbox-line"><input type="checkbox" name="demo_install_confirm" data-action="toggle-demo-install-check" ${demoDataUiState.installConfirmChecked ? 'checked' : ''} /> Я понимаю, что в базу будут добавлены демонстрационные записи.</label><label class="checkbox-line"><input type="checkbox" name="demo_understand" data-action="toggle-demo-install-check" ${demoDataUiState.understandDemoChecked ? 'checked' : ''} /> Я понимаю, что демо-данные не должны смешиваться с реальными рабочими данными.</label><div class="actions"><button class="primary-action" type="button" data-action="install-demo-data" ${disabled ? 'disabled' : ''}>${demoDataUiState.actionStatus === 'installing' ? 'Устанавливаем…' : 'Установить демо-данные'}</button><button class="secondary-action" type="button" data-action="hide-demo-install-confirm" ${demoDataUiState.actionStatus === 'installing' ? 'disabled' : ''}>Отмена</button></div></div>`; }
function demoClearCard() { const s = demoDataUiState.demoStatus; if (!s || (!s.is_installed && !s.can_clear)) return ''; const disabled = demoDataUiState.actionStatus !== 'idle' || !s.can_clear; return `<section class="card data-card"><p class="card-kicker">Только отслеженные записи</p><h2>Очистить демо-данные</h2><p>Очистка удаляет только записи, созданные в демонстрационном режиме. Реальные записи пользователя удаляться не должны.</p>${!s.can_clear && s.is_installed ? feedbackMessage('error', 'Сейчас демо-данные нельзя очистить. Проверьте причины выше.') : ''}<div class="actions"><button class="danger-action" type="button" data-action="show-demo-clear-confirm" ${disabled ? 'disabled' : ''}>Перейти к очистке</button></div>${demoDataUiState.showClearConfirm ? demoClearConfirmPanel() : ''}</section>`; }
function demoClearConfirmPanel() { const disabled = demoDataUiState.actionStatus === 'clearing' || !demoDataUiState.clearConfirmChecked; return `<div class="confirm-panel" aria-busy="${demoDataUiState.actionStatus === 'clearing' ? 'true' : 'false'}"><h3>Подтвердите очистку демо-данных</h3><p>Будут удалены только отслеженные демо-записи. Если эти данные уже используются в рабочей базе, приложение не позволит их удалить.</p><label class="checkbox-line"><input type="checkbox" name="demo_clear_confirm" data-action="toggle-demo-clear-check" ${demoDataUiState.clearConfirmChecked ? 'checked' : ''} /> Я понимаю, что будут удалены отслеженные демо-записи.</label><div class="actions"><button class="danger-action" type="button" data-action="clear-demo-data" ${disabled ? 'disabled' : ''}>${demoDataUiState.actionStatus === 'clearing' ? 'Очищаем…' : 'Очистить демо-данные'}</button><button class="secondary-action" type="button" data-action="hide-demo-clear-confirm" ${demoDataUiState.actionStatus === 'clearing' ? 'disabled' : ''}>Отмена</button></div></div>`; }
function demoCountsCard() { const counts = demoDataUiState.lastInstallResult?.created_counts || demoDataUiState.lastClearResult?.deleted_counts || demoDataUiState.demoStatus?.created_counts || {}; const entries = Object.entries(counts).filter(([, value]) => Number(value) > 0); if (!entries.length) return ''; const title = demoDataUiState.lastClearResult ? 'Что удалено' : 'Что создано или отслеживается'; return `<section class="card data-card"><div class="section-heading"><div><p class="card-kicker">Состав демо-данных</p><h2>${title}</h2></div><span class="pill info">${entries.length}</span></div><div class="overview-grid compact-overview">${entries.map(([key, value]) => `<div class="metric-card"><span>${demoCountLabel(key)}</span><strong>${value}</strong></div>`).join('')}</div>${demoDataUiState.lastInstallResult ? demoSuccessNavigation() : ''}</section>`; }
function demoSuccessNavigation() { const buttons: Array<[string, NavigationSection]> = [['Открыть компоненты', 'Компоненты'], ['Открыть склад', 'Склад'], ['Открыть рецепты', 'Рецепты'], ['Открыть клиентов', 'Клиенты'], ['Открыть заказы', 'Заказы'], ['Открыть алерты', 'Алерты'], ['Открыть закупки', 'Закупки']]; return `<p class="next-step">Демо-данные установлены. Теперь можно открыть разделы и посмотреть пример работы.</p><div class="actions">${buttons.map(([label, section]) => `<button class="secondary-action compact" type="button" data-action="navigate-demo-related" data-section="${section}">${label}</button>`).join('')}</div>`; }
function demoBoundariesCard() { return `<section class="card data-card"><p class="card-kicker">Без скрытых действий</p><h2>Честные границы демо-режима</h2><ul class="checklist compact-list"><li>Демо-данные не устанавливаются автоматически</li><li>Демо-режим не удаляет реальные данные</li><li>Резервные копии и экспорт не создаются автоматически</li><li>Производство не запускается автоматически</li><li>Импорт не применяется автоматически</li><li>Облачная синхронизация, распознавание документов и создание PDF не относятся к демо-режиму</li></ul></section>`; }
const demoCountLabels: Record<string, string> = {
  ingredients: 'Компоненты',
  ingredient_lots: 'Партии компонентов',
  recipes: 'Рецепты',
  recipe_templates: 'Рецепты',
  recipe_versions: 'Версии рецептов',
  recipe_ingredients: 'Составы рецептов',
  clients: 'Клиенты',
  client_recipes: 'Индивидуальные рецепты',
  client_recipe_ingredients: 'Составы индивидуальных рецептов',
  orders: 'Заказы',
  packaging_items: 'Тара',
  stock_movements: 'Складские движения',
  packaging_stock_movements: 'Движения тары',
  production_batches: 'Производство',
  alerts: 'Алерты',
  purchase_suggestions: 'Закупочный список',
};
function demoCountLabel(key: string): string { return demoCountLabels[key] ?? 'Другие данные'; }

function loadImports(force = false) {
  if (!force && (importUiState.status === 'loading' || importUiState.status === 'ready')) return;
  importUiState.status = 'loading';
  importUiState.error = '';
  if (force) importUiState.message = '';
  render();
  Promise.all([getImportTargets(), getImportDrafts(importUiState.filters)])
    .then(([targets, list]) => {
      importUiState.status = 'ready';
      importUiState.targets = targets.targets;
      importUiState.drafts = list.drafts;
      if (!importUiState.selectedTargetType && targets.targets[0]) importUiState.selectedTargetType = targets.targets[0].type;
      importUiState.error = '';
      render();
    })
    .catch(() => {
      importUiState.status = 'error';
      importUiState.error = 'Не удалось загрузить сведения об импорте. Проверьте, что локальное приложение запущено, и попробуйте снова.';
      render();
    });
}

function submitImportDraftForm(event: SubmitEvent) { event.preventDefault(); submitImportDraft(event.currentTarget as HTMLFormElement); }
function submitImportDraft(form: HTMLFormElement) {
  if (importUiState.actionStatus === 'uploading') return;
  const targetType = importUiState.selectedTargetType || (form.elements.namedItem('target_type') as HTMLSelectElement | null)?.value || '';
  const file = (form.elements.namedItem('file') as HTMLInputElement | null)?.files?.[0] ?? null;
  if (!targetType) { importUiState.error = 'Выберите тип данных для импорта.'; importUiState.message = ''; render(); return; }
  if (!file || !/\.(csv|xlsx)$/i.test(file.name)) { importUiState.error = 'Выберите файл CSV или XLSX.'; importUiState.message = ''; render(); return; }
  resetImportApplyState();
  importUiState.actionStatus = 'uploading';
  importUiState.error = '';
  importUiState.message = '';
  clearFeedbackAnnouncement();
  render();
  createImportDraft(file, targetType)
    .then((response) => {
      resetImportApplyState();
      const successMessage = response.message || 'Черновик импорта создан. Данные ещё не внесены в систему.';
      importUiState.message = successMessage;
      announcePolite(successMessage);
      importUiState.selectedFileName = '';
      form.reset();
      return Promise.all([getImportDrafts(importUiState.filters), getImportDraft(response.draft.id)])
        .then(([list, detail]) => {
          importUiState.drafts = list.drafts;
          importUiState.selectedDraft = detail;
          importUiState.selectedDraftStatus = 'ready';
          importUiState.status = 'ready';
          importUiState.actionStatus = 'idle';
          render();
        })
        .catch(() => {
          importUiState.status = 'ready';
          importUiState.actionStatus = 'idle';
          importUiState.error = '';
          importUiState.message = `${successMessage} Не удалось обновить список или открыть предпросмотр. Нажмите «Обновить», чтобы перечитать черновики.`;
          render();
        });
    })
    .catch((error) => {
      importUiState.actionStatus = 'idle';
      importUiState.error = error instanceof Error && error.message !== 'API request failed'
        ? error.message
        : 'Не удалось создать черновик импорта. Проверьте формат CSV/XLSX и попробуйте снова.';
      importUiState.message = '';
      announceAssertive(importUiState.error);
      render();
    });
}

function resetImportApplyState() { importUiState.applyStatus = 'idle'; importUiState.applyError = ''; importUiState.applyErrorIssues = []; importUiState.applyMessage = ''; importUiState.applyRefreshWarning = ''; importUiState.applyConfirmChecked = false; importUiState.backupAcknowledged = false; importUiState.allowWarnings = false; importUiState.lastApplyResult = null; importUiState.showApplyConfirm = false; }
function openImportDraft(id: number) {
  resetImportApplyState();
  importUiState.selectedDraftStatus = 'loading';
  importUiState.selectedDraftError = '';
  render();
  getImportDraft(id)
    .then((detail) => { importUiState.selectedDraft = detail; importUiState.selectedDraftStatus = 'ready'; importUiState.lastApplyResult = getDraftApplyResult(detail.draft); render(); })
    .catch(() => { importUiState.selectedDraftStatus = 'error'; importUiState.selectedDraftError = 'Не удалось открыть черновик импорта.'; render(); });
}

function cancelImportDraftFromUi(id: number) {
  if (!window.confirm('Отменить черновик импорта? Рабочие данные не изменятся.')) return;
  importUiState.actionStatus = 'cancelling';
  importUiState.error = '';
  importUiState.message = '';
  clearFeedbackAnnouncement();
  render();
  cancelImportDraft(id)
    .then((response) => {
      const successMessage = response.message || 'Черновик импорта отменён. Рабочие данные не изменены.';
      importUiState.message = successMessage;
      announcePolite(successMessage);
      return Promise.all([getImportDrafts(importUiState.filters), getImportDraft(response.draft.id)])
        .then(([list, detail]) => {
          importUiState.drafts = list.drafts;
          importUiState.selectedDraft = detail;
          importUiState.selectedDraftStatus = 'ready';
          importUiState.actionStatus = 'idle';
          render();
        })
        .catch(() => {
          importUiState.actionStatus = 'idle';
          importUiState.error = '';
          importUiState.message = `${successMessage} Не удалось обновить список или предпросмотр. Нажмите «Обновить», чтобы перечитать черновики.`;
          render();
        });
    })
    .catch((error) => { importUiState.actionStatus = 'idle'; importUiState.error = error instanceof Error && error.message !== 'API request failed' ? error.message : 'Не удалось отменить черновик импорта.'; importUiState.message = ''; announceAssertive(importUiState.error); render(); });
}


function showImportApplyConfirmation() { if (!canShowApplyButton(importUiState.selectedDraft)) return; importUiState.applyStatus = 'confirming'; importUiState.showApplyConfirm = true; importUiState.applyError = ''; importUiState.applyErrorIssues = []; importUiState.applyMessage = ''; importUiState.applyRefreshWarning = ''; render(); }
function hideImportApplyConfirmation() { importUiState.showApplyConfirm = false; importUiState.applyStatus = 'idle'; importUiState.applyError = ''; importUiState.applyErrorIssues = []; importUiState.applyMessage = ''; importUiState.applyRefreshWarning = ''; importUiState.applyConfirmChecked = false; importUiState.backupAcknowledged = false; importUiState.allowWarnings = false; render(); }
function updateImportApplyChecks() { importUiState.applyConfirmChecked = Boolean(document.querySelector<HTMLInputElement>('input[name="import_apply_confirm"]')?.checked); importUiState.backupAcknowledged = Boolean(document.querySelector<HTMLInputElement>('input[name="import_backup_acknowledged"]')?.checked); importUiState.allowWarnings = Boolean(document.querySelector<HTMLInputElement>('input[name="import_allow_warnings"]')?.checked); importUiState.applyError = ''; importUiState.applyErrorIssues = []; render(); }
function applySelectedImportDraftFromUi() {
  const detail = importUiState.selectedDraft;
  if (!detail || !canShowApplyButton(detail) || importUiState.applyStatus === 'applying') return;
  const needsWarningAck = detail.draft.apply_readiness?.status === 'ready_with_warnings';
  if (!importUiState.applyConfirmChecked || !importUiState.backupAcknowledged || (needsWarningAck && !importUiState.allowWarnings)) { importUiState.applyError = needsWarningAck ? 'Перед применением подтвердите запись в базу, backup и разрешение применить черновик с предупреждениями.' : 'Перед применением подтвердите запись в базу и backup.'; render(); return; }
  importUiState.applyStatus = 'applying'; importUiState.applyError = ''; importUiState.applyErrorIssues = []; importUiState.applyMessage = ''; importUiState.applyRefreshWarning = ''; clearFeedbackAnnouncement(); render();
  applyImportDraft(detail.draft.id, { confirm_apply: true, backup_acknowledged: true, allow_warnings: needsWarningAck ? true : importUiState.allowWarnings })
    .then((response) => {
      const successMessage = response.message || 'Черновик импорта применён. Данные внесены в систему.';
      importUiState.selectedDraft = { ...detail, draft: response.draft };
      importUiState.selectedDraftStatus = 'ready';
      importUiState.applyStatus = 'success';
      importUiState.showApplyConfirm = false;
      importUiState.applyMessage = successMessage;
      importUiState.applyError = '';
      importUiState.applyErrorIssues = [];
      importUiState.applyRefreshWarning = '';
      importUiState.lastApplyResult = response.apply_result;
      importUiState.applyConfirmChecked = false;
      importUiState.backupAcknowledged = false;
      importUiState.allowWarnings = false;
      announcePolite(successMessage);
      return Promise.all([getImportDrafts(importUiState.filters), getImportDraft(response.draft.id)])
        .then(([list, refreshed]) => {
          importUiState.drafts = list.drafts;
          importUiState.selectedDraft = refreshed;
          importUiState.selectedDraftStatus = 'ready';
          importUiState.lastApplyResult = response.apply_result || getDraftApplyResult(refreshed.draft);
          importUiState.applyRefreshWarning = '';
          render();
        })
        .catch(() => {
          importUiState.applyRefreshWarning = 'Черновик применён, данные внесены в систему. Не удалось обновить список или предпросмотр. Нажмите «Обновить», чтобы перечитать данные.';
          render();
        });
    })
    .catch((error) => { const apiError = error as ApiErrorWithDetails; importUiState.applyStatus = 'error'; importUiState.applyError = importApplyErrorMessage(error); importUiState.applyErrorIssues = Array.isArray(apiError?.issues) ? apiError.issues : []; importUiState.applyRefreshWarning = ''; announceAssertive(importUiState.applyError); render(); });
}
function importApplyErrorMessage(error: unknown) {
  const apiError = error as ApiErrorWithDetails;
  const status = typeof apiError?.status === 'number' ? apiError.status : 0;
  const message = error instanceof Error && error.message !== 'API request failed' ? error.message : '';
  const issueMessages = Array.isArray(apiError?.issues)
    ? apiError.issues.map((issue) => { const row = issue.row_number ? `Строка ${issue.row_number}: ` : ''; return issue.message ? `${row}${issue.message}` : ''; }).filter(Boolean)
    : [];
  const details = issueMessages.length ? ` Детали: ${issueMessages.join(' ')}` : (message ? ` Детали: ${message}` : '');
  if (/backup/i.test(message) || /резерв/i.test(message)) return `Перед применением нужно подтвердить, что резервная копия создана или не требуется.${details && !details.includes(message) ? details : ''}`;
  if (/warning/i.test(message) || /предупреж/i.test(message)) return `Черновик содержит предупреждения. Чтобы продолжить, отметьте разрешение на применение с предупреждениями.${details && !details.includes(message) ? details : ''}`;
  if (status === 409) return `Применение отклонено: есть конфликт или дубликат. Исправьте файл и создайте новый черновик.${details}`;
  return `Не удалось применить черновик. Рабочие данные не были частично изменены.${details}`;
}

function importApplyErrorMarkup() {
  if (!importUiState.applyError) return '';
  const issues = importUiState.applyErrorIssues || [];
  const issueList = issues.length ? `<ul class="issue-list">${issues.map((issue) => { const row = issue.row_number ? `Строка ${issue.row_number}` : 'Общий конфликт'; const field = issue.field ? ` · поле ${escapeHtml(String(issue.field))}` : ''; const code = issue.code ? ` · ${escapeHtml(String(issue.code))}` : ''; return `<li><strong>${row}${field}</strong>: ${escapeHtml(String(issue.message || 'Проверьте строку.'))}<br><small>${code}</small></li>`; }).join('')}</ul>` : '';
  return feedbackMessage('error', importUiState.applyError, `${issueList}<p class="next-step">Рабочие данные не были частично изменены.</p>`);
}

function navigateToSection(section: NavigationSection | undefined) { if (!section) return; activeSection = section; window.history.pushState({}, '', pathForSection(activeSection)); loadSectionData(activeSection); render(); }

function importPage() {
  const isLoading = importUiState.status === 'loading';
  return `<div class="page-grid backup-page import-page">
    <section class="card data-card dashboard-hero"><div><p class="card-kicker">Безопасный черновик</p><h2>Импорт данных</h2><p>Сначала создайте черновик из файла CSV или XLSX. Проверьте найденные данные и ошибки. Записи будут добавлены в систему только после подтверждения и применения черновика.</p></div><div class="actions"><button class="secondary-action" type="button" data-action="reload-imports" ${isLoading ? 'disabled' : ''}>${isLoading ? 'Обновляем…' : 'Обновить'}</button></div></section>
    ${importUiState.error ? feedbackMessage('error', importUiState.error) : ''}
    ${importUiState.message ? feedbackMessage('success', importUiState.message) : ''}
    ${importUiState.status === 'error' && !importUiState.targets.length ? importLoadErrorCard() : `${importUploadCard()}${importTargetsCard()}${importBackupRecommendationCard()}${importDraftsCard()}${importDraftDetailCard()}${importNonGoalsCard()}`}
  </div>`;
}
function importLoadErrorCard() { return `<section class="card error-card"><h2>Сведения недоступны</h2><p>Не удалось загрузить сведения об импорте.</p><p>Проверьте, что локальное приложение запущено, и попробуйте снова.</p><div class="actions"><button class="secondary-action" type="button" data-action="reload-imports">Обновить</button></div></section>`; }
function importUploadCard() {
  const target = importUiState.targets.find((item) => item.type === importUiState.selectedTargetType);
  const disabled = importUiState.actionStatus === 'uploading' || importUiState.status === 'loading';
  return `<section class="card data-card"><p class="card-kicker">Явное действие</p><h2>Создать черновик импорта</h2><p>Поддерживаются CSV и XLSX. Первая непустая строка должна быть строкой заголовков.</p><form class="form-grid" data-form="import-draft" aria-busy="${importUiState.actionStatus === 'uploading' ? 'true' : 'false'}"><label>Тип данных<select name="target_type" data-action="select-import-target"><option value="">Выберите раздел</option>${importUiState.targets.map((item) => `<option value="${escapeHtml(item.type)}" ${item.type === importUiState.selectedTargetType ? 'selected' : ''}>${escapeHtml(item.label)}</option>`).join('')}</select></label><label>Файл CSV/XLSX<input name="file" type="file" accept=".csv,.xlsx" data-action="select-import-file" /></label><div class="actions"><button class="primary-action" type="submit" ${disabled ? 'disabled' : ''}>${importUiState.actionStatus === 'uploading' ? 'Загружаем файл…' : 'Создать черновик'}</button></div></form>${target ? `<p class="next-step">Для «${escapeHtml(target.label)}» обязательные столбцы: ${escapeHtml(target.required_columns.join(', ') || 'нет')}.</p>` : '<p class="next-step">Выберите тип данных и файл. Приложение создаст черновик и покажет результат проверки перед применением.</p>'}</section>`;
}
function importTargetsCard() {
  if (importUiState.status === 'loading' && !importUiState.targets.length) return '<section class="card"><p>Загружаем поддерживаемые типы импорта…</p></section>';
  return `<section class="card data-card"><div class="section-heading"><div><p class="card-kicker">Форматы</p><h2>Какие файлы можно загрузить</h2></div><span class="pill info">${importUiState.targets.length}</span></div>${importUiState.targets.length ? `<div class="recipe-list">${importUiState.targets.map((target) => `<article class="recipe-line"><h3>${escapeHtml(target.label)}</h3><p>Обязательные столбцы: <strong>${escapeHtml(target.required_columns.join(', ') || 'нет')}</strong></p>${target.optional_columns.length ? `<p class="muted-text">Дополнительные столбцы: ${escapeHtml(target.optional_columns.join(', '))}</p>` : ''}</article>`).join('')}</div>` : '<p>Список целей импорта пока недоступен. Нажмите «Обновить».</p>'}</section>`;
}
function importDraftsCard() {
  const targetOptions = importUiState.targets.map((target) => `<option value="${escapeHtml(target.type)}" ${importUiState.filters.targetType === target.type ? 'selected' : ''}>${escapeHtml(target.label)}</option>`).join('');
  if (!importUiState.drafts.length) return `<section class="card empty-card"><div class="section-heading"><div><p class="card-kicker">Черновики</p><h2>Черновики импорта</h2></div></div><div class="form-grid compact-form"><label>Статус<select data-action="filter-import-status"><option value="">Все</option>${importDraftFilterStatuses().map((status) => `<option value="${status}" ${importUiState.filters.status === status ? 'selected' : ''}>${importDraftStatusLabel(status)}</option>`).join('')}</select></label><label>Тип<select data-action="filter-import-target"><option value="">Все</option>${targetOptions}</select></label><div class="actions"><button class="secondary-action" type="button" data-action="reset-import-filters">Сбросить</button></div></div><p>Черновиков импорта пока нет.</p><p>Загрузите CSV/XLSX, чтобы проверить данные перед импортом.</p></section>`;
  return `<section class="card data-card"><div class="section-heading"><div><p class="card-kicker">Черновики</p><h2>Черновики импорта</h2></div><span class="pill info">${importUiState.drafts.length}</span></div><div class="form-grid compact-form"><label>Статус<select data-action="filter-import-status"><option value="">Все</option>${importDraftFilterStatuses().map((status) => `<option value="${status}" ${importUiState.filters.status === status ? 'selected' : ''}>${importDraftStatusLabel(status)}</option>`).join('')}</select></label><label>Тип<select data-action="filter-import-target"><option value="">Все</option>${targetOptions}</select></label><div class="actions"><button class="secondary-action" type="button" data-action="reset-import-filters">Сбросить</button></div></div><div class="backup-list">${importUiState.drafts.map(importDraftItem).join('')}</div></section>`;
}
function importDraftItem(draft: ImportDraftSummary) { const canCancel = draft.status === 'draft'; const readiness = draft.apply_readiness; return `<article class="recipe-line backup-item"><div class="section-heading"><div><h3>${importTargetLabel(draft.target_type)} · черновик #${draft.id}</h3><p><span class="pill info">${importDraftStatusLabel(draft.status)}</span> ${readiness ? `<span class="pill ${importReadinessPill(readiness.status)}">${importReadinessLabel(readiness.status)}</span>` : ''} <span class="pill muted">строк: ${draft.row_count}</span> <span class="pill ${draft.error_count ? 'danger' : 'success'}">ошибок: ${draft.error_count}</span> <span class="pill ${draft.warning_count ? 'warning' : 'muted'}">предупреждений: ${draft.warning_count}</span></p></div><small>${formatDateTime(draft.created_at || '')}</small></div><p>Корректных строк: <strong>${draft.valid_row_count}</strong>, строк с ошибками: <strong>${draft.invalid_row_count}</strong>.</p>${readiness ? `<p class="next-step">${escapeHtml(readiness.next_action)}</p>` : ''}<div class="actions"><button class="secondary-action" type="button" data-action="open-import-draft" data-id="${draft.id}">Открыть</button>${canCancel ? `<button class="danger-action" type="button" data-action="cancel-import-draft" data-id="${draft.id}" ${importUiState.actionStatus === 'cancelling' ? 'disabled' : ''}>Отменить</button>` : ''}</div></article>`; }
function importDraftDetailCard() {
  if (importUiState.selectedDraftStatus === 'loading') return '<section class="card"><p>Открываем черновик импорта…</p></section>';
  if (importUiState.selectedDraftStatus === 'error') return `<section class="card error-card"><h2>Черновик недоступен</h2><p>${escapeHtml(importUiState.selectedDraftError || 'Не удалось открыть черновик импорта.')}</p></section>`;
  const detail = importUiState.selectedDraft;
  if (!detail) return `<section class="card empty-card"><h2>Предпросмотр черновика</h2><p>Выберите черновик из списка или создайте новый из CSV/XLSX.</p><p class="next-step">Это только предпросмотр. Реальные данные мастерской ещё не изменены.</p></section>`;
  const d = detail.draft;
  return `<section class="card data-card"><div class="section-heading"><div><p class="card-kicker">Предпросмотр</p><h2>Предпросмотр черновика</h2></div><span class="pill info">${importDraftStatusLabel(d.status)}</span></div><p class="next-step">Это только предпросмотр. Реальные данные мастерской ещё не изменены.</p><div class="overview-grid compact-overview"><div class="metric-card"><span>Файл</span><strong>${escapeHtml(detail.source.original_filename)}</strong><small>${formatFileSize(detail.source.file_size_bytes)}</small></div><div class="metric-card"><span>Тип</span><strong>${importTargetLabel(d.target_type)}</strong></div><div class="metric-card"><span>Строки</span><strong>${d.row_count}</strong></div><div class="metric-card"><span>Корректные</span><strong>${d.valid_row_count}</strong></div><div class="metric-card"><span>С ошибками</span><strong>${d.invalid_row_count}</strong></div><div class="metric-card"><span>Предупреждения / ошибки</span><strong>${d.warning_count} / ${d.error_count}</strong></div></div><p><strong>Заголовки:</strong> ${escapeHtml(d.headers.join(', ') || 'не найдены')}</p>${importReadinessPanel(d)}${importApplySection(detail)}${importIssuesMarkup(detail.issues)}${importIssueCountsMarkup(d)}${importPreviewRowsMarkup(detail)}</section>`;
}

function importReadinessPanel(draft: ImportDraftSummary) {
  const readiness = draft.apply_readiness;
  if (!readiness) return '';
  const copy = ({ ready: 'Черновик готов к применению.', ready_with_warnings: 'Черновик можно готовить к применению, но сначала проверьте предупреждения.', blocked: 'Черновик нельзя применять: есть ошибки, которые нужно исправить в файле.', cancelled: 'Черновик отменён. Рабочие данные не изменены.', failed: 'Черновик не удалось проверить. Рабочие данные не изменены.' } as Record<string, string>)[readiness.status] ?? readiness.next_action;
  return `<div class="subsection readiness-panel"><div class="section-heading"><div><h3>Готовность черновика</h3><p>${escapeHtml(copy)}</p></div><span class="pill ${importReadinessPill(readiness.status)}">${importReadinessLabel(readiness.status)}</span></div><div class="overview-grid compact-overview"><div class="metric-card"><span>Можно готовить к применению</span><strong>${readiness.can_apply ? 'Да' : 'Нет'}</strong></div><div class="metric-card"><span>Блокирующие ошибки</span><strong>${readiness.blocking_error_count}</strong></div><div class="metric-card"><span>Предупреждения / заметки</span><strong>${readiness.warning_count}</strong></div></div>${readiness.blocking_reasons.length ? `<p class="warning-text">${readiness.blocking_reasons.map(escapeHtml).join('<br>')}</p>` : ''}${readiness.warnings.length ? `<p class="next-step">${readiness.warnings.map(escapeHtml).join('<br>')}</p>` : ''}<p class="next-step">Проверка выполнена по данным мастерской. Применение доступно только через явное подтверждение ниже.</p></div>`;
}

function importApplySection(detail: ImportDraftDetailResponse) {
  const draft = detail.draft;
  const readiness = draft.apply_readiness;
  const result = importUiState.lastApplyResult || getDraftApplyResult(draft);
  const unsupported = !APPLY_SUPPORTED_IMPORT_TARGETS.has(draft.target_type);
  const blockedReasons = readiness?.blocking_reasons ?? [];
  const status = draft.status;
  const success = importUiState.applyStatus === 'success' && result ? importApplyResultMarkup(result) : '';
  if (status === 'applied') { const refreshWarning = importUiState.applyRefreshWarning ? feedbackMessage('warning', importUiState.applyRefreshWarning) : ''; return `<div class="subsection apply-panel" aria-busy="${importUiState.applyStatus === 'applying' ? 'true' : 'false'}"><h3>Применение черновика</h3>${feedbackMessage('neutral', 'Черновик уже применён.')}${refreshWarning}${result ? importApplyResultMarkup(result) : ''}</div>`; }
  if (status === 'cancelled') return `<div class="subsection apply-panel"><h3>Применение черновика</h3><p>Черновик отменён. Рабочие данные не изменены.</p></div>`;
  if (status === 'failed') return `<div class="subsection apply-panel"><h3>Применение черновика</h3>${feedbackMessage('error', 'Черновик не готов к применению из-за ошибки обработки.')}</div>`;
  if (!readiness || readiness.can_apply === false || status === 'blocked' || readiness.status === 'blocked') return `<div class="subsection apply-panel"><h3>Применение черновика</h3>${feedbackMessage('error', 'Черновик нельзя применить: сначала исправьте ошибки в файле и создайте новый черновик.')}${blockedReasons.length ? `<p class="warning-text">${blockedReasons.map(escapeHtml).join('<br>')}</p>` : ''}</div>`;
  if (unsupported) return `<div class="subsection apply-panel"><h3>Применение черновика</h3><p>Этот тип черновика пока нельзя применить из интерфейса.</p><p class="next-step">Применение доступно только для безопасных типов: компоненты, клиенты, карточки рецептов и тара. Партии компонентов и заказы пока остаются только на уровне черновика.</p></div>`;
  const warningCopy = readiness.status === 'ready_with_warnings' ? '<p class="warning-text">Черновик можно применить, но в нём есть предупреждения. Проверьте их перед продолжением.</p>' : '<p class="next-step">Черновик готов к применению.</p>';
  return `<div class="subsection apply-panel" aria-busy="${importUiState.applyStatus === 'applying' ? 'true' : 'false'}"><h3>Применение черновика</h3>${importUiState.applyError ? `${importApplyErrorMarkup()}` : ''}${importUiState.applyMessage ? feedbackMessage('success', importUiState.applyMessage) : ''}${success}${warningCopy}${importUiState.showApplyConfirm ? importApplyConfirmPanel(detail) : `<div class="actions"><button class="primary-action" type="button" data-action="show-import-apply-confirm">Перейти к подтверждению</button></div>`}</div>`;
}
function importApplyConfirmPanel(detail: ImportDraftDetailResponse) {
  const draft = detail.draft; const readiness = draft.apply_readiness; const needsWarningAck = readiness?.status === 'ready_with_warnings'; const disabled = importUiState.applyStatus === 'applying' || !importUiState.applyConfirmChecked || !importUiState.backupAcknowledged || (needsWarningAck && !importUiState.allowWarnings);
  return `<div class="confirm-panel"><h3>Подтвердите применение</h3><p>После применения данные из черновика будут записаны в рабочую базу. Это действие нельзя считать простым предпросмотром.</p><div class="overview-grid compact-overview"><div class="metric-card"><span>Тип импорта</span><strong>${applyTargetLabel(draft.target_type)}</strong></div><div class="metric-card"><span>Количество строк</span><strong>${draft.row_count}</strong></div><div class="metric-card"><span>Готовых строк</span><strong>${draft.valid_row_count}</strong></div><div class="metric-card"><span>Ошибок</span><strong>${draft.error_count}</strong></div><div class="metric-card"><span>Предупреждений</span><strong>${draft.warning_count}</strong></div></div><p><strong>Что будет создано:</strong> ${applyTargetActionCopy(draft.target_type)}</p><p class="warning-text">Существующие записи не обновляются автоматически. Если приложение найдёт дубликаты или конфликт, применение будет отменено полностью.</p><p class="next-step">Перед применением импорта рекомендуется создать резервную копию. Система не создаёт её автоматически.</p><div class="actions"><button class="secondary-action" type="button" data-action="navigate-import-related" data-section="Резервные копии">Открыть резервные копии</button><button class="secondary-action" type="button" data-action="navigate-import-related" data-section="Экспорт">Открыть экспорт</button></div><label class="checkbox-line"><input type="checkbox" name="import_apply_confirm" data-action="toggle-import-apply-check" ${importUiState.applyConfirmChecked ? 'checked' : ''} /> Я понимаю, что это внесёт данные в рабочую базу.</label><label class="checkbox-line"><input type="checkbox" name="import_backup_acknowledged" data-action="toggle-import-apply-check" ${importUiState.backupAcknowledged ? 'checked' : ''} /> Я создал(а) резервную копию или понимаю, что применяю импорт без неё.</label>${needsWarningAck ? `<label class="checkbox-line"><input type="checkbox" name="import_allow_warnings" data-action="toggle-import-apply-check" ${importUiState.allowWarnings ? 'checked' : ''} /> Я проверил(а) предупреждения и разрешаю применить черновик с предупреждениями.</label>` : ''}<div class="actions"><button class="primary-action" type="button" data-action="apply-import-draft" ${disabled ? 'disabled' : ''}>${importUiState.applyStatus === 'applying' ? 'Применяем…' : 'Применить черновик'}</button><button class="secondary-action" type="button" data-action="hide-import-apply-confirm" ${importUiState.applyStatus === 'applying' ? 'disabled' : ''}>Вернуться к предпросмотру</button></div></div>`;
}
function importApplyResultMarkup(result: ImportDraftApplyResultResponse) { return `<div class="subsection">${feedbackMessage('success', 'Черновик импорта применён. Данные внесены в систему.')}<p><strong>Создано записей:</strong> ${result.created_count}</p>${result.created_records.length ? `<div class="backup-list">${result.created_records.map((record) => `<article class="recipe-line"><p>Строка ${record.row_number} → ${applyTargetSingularLabel(record.target_type)} «${escapeHtml(record.label)}» #${record.record_id}</p></article>`).join('')}</div>` : '<p class="empty-hint">Список созданных записей не получен.</p>'}<p class="next-step">Если нужно проверить результат, откройте соответствующий раздел: Компоненты, Клиенты, Рецепты или Тара.</p><div class="actions">${importApplyNavigationButtons(result.target_type)}</div></div>`; }
function importApplyNavigationButtons(targetType: string) { const section = ({ ingredients: 'Компоненты', clients: 'Клиенты', recipe_templates: 'Рецепты', packaging_items: 'Тара' } as Record<string, NavigationSection>)[targetType]; return section ? `<button class="secondary-action" type="button" data-action="navigate-import-related" data-section="${section}">Открыть ${section.toLowerCase()}</button>` : ''; }
function getDraftApplyResult(draft: ImportDraftSummary | null): ImportDraftApplyResultResponse | null { const value = draft?.summary?.apply_result; return value && typeof value === 'object' ? value as ImportDraftApplyResultResponse : null; }
function canShowApplyButton(detail: ImportDraftDetailResponse | null): boolean { if (!detail) return false; const draft = detail.draft; const readiness = draft.apply_readiness; return draft.status !== 'applied' && draft.status !== 'cancelled' && draft.status !== 'failed' && draft.status !== 'blocked' && Boolean(readiness?.can_apply) && (readiness?.status === 'ready' || readiness?.status === 'ready_with_warnings') && APPLY_SUPPORTED_IMPORT_TARGETS.has(draft.target_type); }
function applyTargetLabel(targetType: string): string { return importTargetLabel(targetType); }
function applyTargetSingularLabel(targetType: string): string { return ({ ingredients: 'Компонент', clients: 'Клиент', recipe_templates: 'Рецепт-карточка', packaging_items: 'Тара' } as Record<string, string>)[targetType] ?? applyTargetLabel(targetType); }
function applyTargetActionCopy(targetType: string): string { return ({ ingredients: 'Будут созданы новые компоненты.', clients: 'Будут созданы новые клиенты.', recipe_templates: 'Будут созданы новые карточки рецептов без состава.', packaging_items: 'Будут созданы новые позиции тары без движения остатков.' } as Record<string, string>)[targetType] ?? 'Приложение определит безопасные создаваемые записи.'; }

function importIssueCodeLabel(code: string): string {
  return ({
    header_alias_used: 'Распознан альтернативный заголовок',
    decimal_comma_normalized: 'Запятая в числе заменена на точку',
    ambiguous_decimal: 'Неоднозначное число',
    invalid_positive_decimal: 'Число должно быть больше нуля',
    invalid_non_negative_decimal: 'Число не может быть отрицательным',
    unit_alias_normalized: 'Единица измерения распознана',
    date_format_normalized: 'Дата приведена к формату YYYY-MM-DD',
    invalid_email: 'Email выглядит некорректно',
    invalid_id: 'ID должен быть положительным целым числом',
    unknown_column: 'Неизвестный столбец',
    missing_required_column: 'Не найден обязательный столбец',
    missing_required_value: 'Не заполнено обязательное поле',
    invalid_decimal: 'Некорректное число',
    invalid_date: 'Некорректная дата',
    invalid_unit: 'Неизвестная единица измерения',
    duplicate_header: 'Повторяющийся заголовок',
    missing_header: 'Пустой заголовок',
    empty_file: 'Файл пустой',
    unsupported_file_type: 'Неподдерживаемый тип файла',
    file_too_large: 'Файл слишком большой',
    too_many_rows: 'Слишком много строк',
    too_many_columns: 'Слишком много столбцов',
  } as Record<string, string>)[code] ?? code;
}
function importIssueCountsMarkup(draft: ImportDraftSummary) { const summary = draft.summary || {}; const counts = summary.issue_counts_by_code as Record<string, number> | undefined; if (!counts || !Object.keys(counts).length) return ''; return `<div class="subsection"><h3>Сводка кодов проверки</h3><p>${Object.entries(counts).map(([code, count]) => `${escapeHtml(importIssueCodeLabel(code))}: ${count}`).join(' · ')}</p></div>`; }
function importReadinessLabel(status: string): string { return ({ ready: 'Готов', ready_with_warnings: 'Готов с предупреждениями', blocked: 'Заблокирован', cancelled: 'Отменён', failed: 'Ошибка', applied: 'Применён' } as Record<string, string>)[status] ?? status; }
function importReadinessPill(status: string): string { return ({ ready: 'success', ready_with_warnings: 'warning', blocked: 'danger', cancelled: 'muted', failed: 'danger', applied: 'success' } as Record<string, string>)[status] ?? 'muted'; }
function importIssuesMarkup(issues: ImportIssue[]) { return `<div class="subsection"><h3>Ошибки и предупреждения</h3>${issues.length ? `<div class="recipe-list">${issues.map((issue) => `<article class="recipe-line"><p><span class="pill ${importIssueSeverityPill(issue.severity)}">${importIssueSeverityLabel(issue.severity)}</span> ${escapeHtml(issue.message)}</p><p class="muted-text">${issue.row_number ? `Строка ${issue.row_number}. ` : ''}${issue.field ? `Поле: ${escapeHtml(issue.field)}. ` : ''}${issue.code ? `Код: ${escapeHtml(issue.code)}.` : ''}</p></article>`).join('')}</div>` : '<p class="next-step">Критичных ошибок в предпросмотре не найдено.</p>'}</div>`; }
function importPreviewRowsMarkup(detail: ImportDraftDetailResponse) { const headers = detail.draft.headers.length ? detail.draft.headers : Array.from(new Set(detail.preview_rows.flatMap((row) => Object.keys(row.normalized_values || row.raw_values || {})))); if (!detail.preview_rows.length) return '<div class="subsection"><h3>Первые строки файла</h3><p>Строки предпросмотра не получены.</p></div>'; return `<div class="subsection"><h3>Первые строки файла</h3><div class="table-wrapper"><table class="data-table"><thead><tr><th>Строка</th><th>Статус</th>${headers.map((header) => `<th>${escapeHtml(header)}</th>`).join('')}<th>Замечания</th></tr></thead><tbody>${detail.preview_rows.map((row) => `<tr class="${row.issues.some((issue) => issue.severity === 'error') ? 'row-error' : ''}"><td>${row.row_number}</td><td>${escapeHtml(importDraftStatusLabel(row.status))}</td>${headers.map((header) => `<td>${escapeHtml(formatImportCellValue((row.normalized_values || {})[header] ?? (row.raw_values || {})[header]))}</td>`).join('')}<td>${row.issues.map((issue) => `${importIssueSeverityLabel(issue.severity)}: ${issue.message}`).map(escapeHtml).join('<br>') || '—'}</td></tr>`).join('')}</tbody></table></div><p class="next-step">Строки нельзя редактировать на этом шаге. Если нужен другой результат, исправьте файл и загрузите новый черновик.</p></div>`; }
function importBackupRecommendationCard() { return `<section class="card data-card"><p class="card-kicker">Перед применением</p><h2>Резервная копия перед импортом</h2><p>Перед применением импорта сделайте резервную копию. Система не создаёт резервную копию или экспорт автоматически; эти кнопки только открывают нужные разделы.</p><div class="actions"><button class="secondary-action" type="button" data-nav-section="Резервные копии">Открыть резервные копии</button><button class="secondary-action" type="button" data-nav-section="Экспорт">Открыть экспорт</button></div></section>`; }
function importNonGoalsCard() { return `<section class="card data-card"><p class="card-kicker">Честные границы</p><h2>Что сейчас не делает импорт</h2><p>Экран создаёт черновик, показывает предпросмотр и ошибки, а применение доступно только для поддерживаемых безопасных типов после явного подтверждения.</p><ul class="checklist compact-list"><li>Партии компонентов и заказы остаются черновиками и не применяются в рабочие данные.</li><li>Сопоставление столбцов вручную на этом экране не настраивается.</li><li>PDF, изображения и OCR не импортируются.</li><li>Резервная копия перед импортом не создаётся автоматически.</li><li>Экспортированный JSON нельзя загрузить обратно через этот экран.</li><li>Облачный импорт не выполняется.</li></ul></section>`; }
function importTargetLabel(type: string): string { return importUiState.targets.find((target) => target.type === type)?.label ?? escapeHtml(type); }
function importDraftFilterStatuses(): string[] { return ['draft', 'applied', 'failed', 'cancelled']; }
function importDraftStatusLabel(status: string): string { return ({ draft: 'Черновик', failed: 'Ошибка', cancelled: 'Отменён', applied: 'Применён', uploaded: 'Загружен', parsed: 'Разобран', valid: 'Проверено', invalid: 'Есть ошибки' } as Record<string, string>)[status] ?? escapeHtml(status); }
function importIssueSeverityLabel(severity: string): string { return ({ error: 'Ошибка', warning: 'Предупреждение', info: 'Информация' } as Record<string, string>)[severity] ?? escapeHtml(severity); }
function importIssueSeverityPill(severity: string): string { return severity === 'error' ? 'danger' : severity === 'warning' ? 'warning' : 'info'; }
function formatImportCellValue(value: unknown): string { if (value == null || value === '') return '—'; if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') return String(value); return '[сложное значение]'; }

function backupPage() {
  const isLoading = backupUiState.status === 'loading';
  const status = backupUiState.backupStatus;
  const createDisabled = backupUiState.actionStatus === 'creating' || isLoading || !status?.database_exists;
  return `<div class="page-grid backup-page">
    <section class="card data-card dashboard-hero">
      <div><p class="card-kicker">Локальная защита данных</p><h2>Резервные копии</h2><p>Резервная копия сохраняет текущее состояние данных мастерской в отдельном локальном файле.</p><p class="next-step">Создание копии не изменяет рецепты, клиентов, заказы, склад или производство. На этом экране можно создавать и просматривать резервные копии. Восстановление данных здесь не выполняется.</p></div>
      <div class="actions"><button class="secondary-action" type="button" data-action="reload-backups" ${isLoading ? 'disabled' : ''}>${isLoading ? 'Обновляем…' : 'Обновить'}</button><button class="primary-action" type="button" data-action="create-backup" ${createDisabled ? 'disabled' : ''}>${backupUiState.actionStatus === 'creating' ? 'Создаём копию…' : 'Создать резервную копию'}</button></div>
    </section>
    ${backupUiState.error ? `<p class="page-message error-message">${escapeHtml(backupUiState.error)}</p>` : ''}
    ${backupUiState.message ? `<p class="page-message">${escapeHtml(backupUiState.message)}</p>` : ''}
    ${backupUiState.status === 'error' && !status ? backupLoadErrorCard() : `${backupStatusCards()}${backupCreateCard()}${backupHistoryCard()}${backupNonGoalsCard()}`}
  </div>`;
}

function backupLoadErrorCard() { return `<section class="card error-card"><h2>Сведения недоступны</h2><p>Не удалось загрузить сведения о резервных копиях.</p><p>Проверьте, что локальное приложение запущено, и попробуйте снова.</p><div class="actions"><button class="secondary-action" type="button" data-action="reload-backups">Обновить</button></div></section>`; }
function backupStatusCards() {
  const status = backupUiState.backupStatus;
  if (backupUiState.status === 'loading' && !status) return '<section class="card"><p>Загружаем сведения о базе и резервных копиях…</p></section>';
  if (!status) return '';
  const latest = status.latest_backup ? `${escapeHtml(status.latest_backup.filename)} · ${formatDateTime(status.latest_backup.created_at || '')}` : 'Пока нет';
  return `<section class="overview-grid">
    <div class="metric-card"><span>База данных</span><strong>${status.database_exists ? 'База найдена' : 'База данных пока не найдена'}</strong></div>
    <div class="metric-card wide"><span>Расположение базы</span><strong class="path-text">${escapeHtml(status.database_path)}</strong></div>
    <div class="metric-card"><span>Размер базы</span><strong>${formatFileSize(status.database_size_bytes)}</strong></div>
    <div class="metric-card wide"><span>Папка резервных копий</span><strong>${status.backup_dir_exists ? 'Папка резервных копий найдена' : 'Папка резервных копий ещё не создана. Она появится после первой созданной резервной копии.'}</strong><small class="path-text">${escapeHtml(status.backup_dir)}</small></div>
    <div class="metric-card"><span>Количество копий</span><strong>${status.backup_count}</strong></div>
    <div class="metric-card wide"><span>Последняя копия</span><strong>${latest}</strong></div>
  </section>`;
}
function backupCreateCard() {
  const status = backupUiState.backupStatus;
  const disabled = backupUiState.actionStatus === 'creating' || backupUiState.status === 'loading' || !status?.database_exists;
  return `<section class="card data-card"><p class="card-kicker">Явное действие</p><h2>Создать резервную копию</h2><p>Нажмите кнопку перед большим импортом, обновлением приложения или существенными изменениями рабочих данных. Приложение сохранит отдельный локальный файл резервной копии.</p>${!status?.database_exists ? '<p class="page-message error-message">Сначала запустите приложение и создайте рабочую базу данных.</p>' : ''}<form class="form-grid" data-form="backup-create"><label>Причина<select name="reason" data-action="select-backup-reason"><option value="manual" ${backupUiState.reason === 'manual' ? 'selected' : ''}>Обычная резервная копия</option><option value="before_import" ${backupUiState.reason === 'before_import' ? 'selected' : ''}>Перед импортом</option><option value="before_update" ${backupUiState.reason === 'before_update' ? 'selected' : ''}>Перед обновлением приложения</option><option value="before_large_edit" ${backupUiState.reason === 'before_large_edit' ? 'selected' : ''}>Перед крупными изменениями</option><option value="custom" ${backupUiState.reason === 'custom' ? 'selected' : ''}>Своя причина</option></select></label>${backupUiState.reason === 'custom' ? `<label>Своя причина<input name="customReason" maxlength="80" value="${escapeHtml(backupUiState.customReason)}" data-action="custom-backup-reason" placeholder="Например: перед правкой рецептов" /></label>` : ''}<div class="actions"><button class="primary-action" type="submit" ${disabled ? 'disabled' : ''}>${backupUiState.actionStatus === 'creating' ? 'Создаём копию…' : 'Создать резервную копию'}</button></div></form>${backupUiState.lastCreatedBackup ? `<p class="next-step">Последний созданный файл: <strong>${escapeHtml(backupUiState.lastCreatedBackup.filename)}</strong></p>` : '<p class="next-step">Создание копии не запускается автоматически и не меняет рабочие данные.</p>'}</section>`;
}
function backupHistoryCard() {
  if (!backupUiState.backups.length) return `<section class="card empty-card"><h2>История резервных копий</h2><p>Резервных копий пока нет.</p><p>Создайте первую копию перед импортом или крупными изменениями.</p></section>`;
  return `<section class="card data-card"><div class="section-heading"><div><p class="card-kicker">Локальные файлы</p><h2>История резервных копий</h2></div><span class="pill info">${backupUiState.backups.length}</span></div><div class="backup-list">${backupUiState.backups.map(backupHistoryItem).join('')}</div></section>`;
}
function backupHistoryItem(backup: BackupFileResponse) { return `<article class="recipe-line backup-item"><div class="section-heading"><div><h3>${escapeHtml(backup.filename)}</h3><p><span class="pill info">${backupReasonLabel(backup.reason)}</span> <span class="pill muted">${formatFileSize(backup.size_bytes)}</span></p></div><small>${formatDateTime(backup.created_at || '')}</small></div><p><strong>Локальный путь:</strong><br><code class="path-text">${escapeHtml(backup.path)}</code></p><p class="next-step">Это файл резервной копии. Восстановление данных на этом экране не выполняется.</p></article>`; }
function backupNonGoalsCard() { return `<section class="card data-card"><p class="card-kicker">Границы экрана</p><h2>Что важно знать</h2><ul class="checklist compact-list"><li>Резервная копия создаётся только после явного нажатия.</li><li>Копия хранится локально на этом MacBook.</li><li>Создание копии не изменяет рабочие данные.</li><li>Восстановление данных на этом экране не выполняется.</li><li>Автоматическое создание копий по расписанию не выполняется.</li></ul></section>`; }
function formatFileSize(bytes: number | null | undefined): string { if (bytes == null || Number.isNaN(bytes)) return 'Не указано'; if (bytes === 0) return '0 Б'; const units = ['Б', 'КБ', 'МБ', 'ГБ']; let value = bytes; let unitIndex = 0; while (value >= 1024 && unitIndex < units.length - 1) { value /= 1024; unitIndex += 1; } return `${new Intl.NumberFormat('ru-RU', { maximumFractionDigits: value >= 10 || unitIndex === 0 ? 0 : 1 }).format(value)} ${units[unitIndex]}`; }
function backupReasonLabel(reason: string | null): string { return ({ manual: 'Обычная копия', before_import: 'Перед импортом', before_update: 'Перед обновлением', before_large_edit: 'Перед крупными изменениями' } as Record<string, string>)[reason || ''] ?? (reason ? escapeHtml(reason) : 'Не указана'); }

function productionHistoryList(items: ProductionBatchListItem[]) { if (productionHistoryState.status === 'error') return `<section class="card empty-card"><h2>История недоступна</h2><p>Не удалось загрузить историю производства. Проверьте, что локальное приложение запущено.</p><button class="secondary-action" type="button" data-action="reload-production-history">Обновить историю</button></section>`; if (productionHistoryState.batches.length===0) return `<section class="card empty-card"><h2>Изготовленных партий пока нет</h2><p>Изготовленных партий пока нет. Они появятся здесь после подтверждения изготовления заказа.</p></section>`; if (items.length===0) return `<section class="card empty-card"><h2>Партии не найдены</h2><p>Измените поиск, чтобы снова увидеть историю.</p></section>`; return `<section class="card data-card"><div class="section-heading"><div><p class="card-kicker">Журнал</p><h2>Изготовленные партии</h2></div><span class="pill info">${items.length}</span></div><div class="table-wrap"><table class="compact-catalog-table"><thead><tr><th>Дата</th><th>Продукт</th><th>Клиент</th><th>Партия</th><th>Себестоимость</th><th>Цена/маржа</th><th>Списания</th><th>Действие</th></tr></thead><tbody>${items.map((b)=>`<tr class="${productionHistoryState.selectedBatch?.id===b.id?'catalog-row-selected':''}"><td>${formatDateTime(b.produced_at)}</td><td><strong>${escapeHtml(b.product_name)}</strong><small>Заказ №${b.order_id}</small></td><td>${escapeHtml(b.client_name || 'Клиент не указан')}</td><td>${quantityLabel(b.final_batch_value,b.final_batch_unit)}</td><td>${moneyOrMissing(b.total_cost)}</td><td>${moneyOrMissing(b.sale_price)}<small>Маржа: ${moneyOrMissing(b.margin)} · Налог: ${moneyOrMissing(b.tax)}</small></td><td>Компоненты: ${b.ingredient_line_count}<small>Тара: ${b.packaging_line_count}</small></td><td><button class="secondary-action compact" type="button" data-action="open-production-batch" data-id="${b.id}">Открыть партию</button></td></tr>`).join('')}</tbody></table></div><p class="next-step">Партии доступны только для просмотра. Изменения склада смотрите в складских движениях.</p></section>`; }
function productionHistoryDetailPanel() { const b=productionHistoryState.selectedBatch; if (productionHistoryState.detailStatus==='loading') return `<section class="card"><p>Открываем производственную партию…</p></section>`; if (productionHistoryState.detailStatus==='error') return `<section class="card empty-card"><h2>Не удалось открыть партию</h2><p>${escapeHtml(productionHistoryState.detailError || 'Не удалось открыть производственную партию. Обновите историю производства и попробуйте ещё раз.')}</p></section>`; if (!b) return ''; return `<section class="card data-card readiness-result"><div class="section-heading"><div><p class="card-kicker">Историческая партия</p><h2>Партия №${b.id}</h2></div><button class="secondary-action" type="button" data-action="close-production-batch">Вернуться к списку</button></div><div class="readiness-grid"><div><strong>Дата изготовления</strong><p>${formatDateTime(b.produced_at)}</p></div><div><strong>Заказ</strong><p>№${b.order_id}</p></div><div><strong>Продукт</strong><p>${escapeHtml(b.product_name || 'Не указан')}</p></div><div><strong>Клиент</strong><p>${escapeHtml(b.client_name || 'Не указан')}</p></div><div><strong>Источник</strong><p>${productionSourceLabel(b)}</p></div><div><strong>Размер партии</strong><p>${quantityLabel(b.final_batch_value,b.final_batch_unit)}</p></div></div>${b.notes ? `<p><strong>Заметка к партии:</strong><br>${escapeHtml(b.notes)}</p>` : '<p><strong>Заметка к партии:</strong> нет заметки.</p>'}<div class="readiness-block"><h3>Снимок себестоимости</h3><div class="readiness-grid"><div><strong>Компоненты</strong><p>${moneyOrMissing(b.component_cost)}</p></div><div><strong>Тара</strong><p>${moneyOrMissing(b.packaging_cost)}</p></div><div><strong>Прочие расходы</strong><p>${moneyOrMissing(b.other_cost)}</p></div><div><strong>Итого</strong><p>${moneyOrMissing(b.total_cost)}</p></div><div><strong>Цена продажи</strong><p>${moneyOrMissing(b.sale_price)}</p></div><div><strong>Налог</strong><p>${moneyOrMissing(b.tax)}</p></div><div><strong>Маржа</strong><p>${moneyOrMissing(b.margin)}</p></div><div><strong>Маржинальность</strong><p>${b.margin_percent ? `${escapeHtml(b.margin_percent)}%` : 'Не рассчитано'}</p></div></div><p class="next-step">Это снимок на момент изготовления. Значения не пересчитываются задним числом.</p></div>${productionIngredientsTable(b.ingredients)}${productionPackagingTable(b.packaging)}<p class="next-step">Партия доступна только для просмотра. Списания уже записаны как складские движения.</p></section>`; }
function productionSourceLabel(b: ProductionBatchDetailResponse) { if (b.client_recipe_id) return `Индивидуальная формула №${b.client_recipe_id}`; if (b.recipe_version_id) return `Базовая версия рецепта №${b.recipe_version_id}`; return 'Источник не указан'; }
function productionIngredientsTable(rows: ProductionBatchIngredientResponse[]) { return `<div class="readiness-block"><h3>Списанные компоненты</h3>${rows.length ? `<div class="table-wrap"><table class="compact-catalog-table"><thead><tr><th>Компонент</th><th>Партия</th><th>Нужно</th><th>Списано</th><th>Ед.</th><th>Цена за ед.</th><th>Стоимость</th><th>Срок годности</th></tr></thead><tbody>${rows.map((r)=>`<tr><td><strong>${escapeHtml(r.ingredient_name_snapshot)}</strong></td><td>${escapeHtml(r.lot_code_snapshot || 'Без номера')}</td><td>${formatDecimalForDisplay(r.required_quantity)}</td><td>${formatDecimalForDisplay(r.consumed_quantity)}</td><td>${unitLabel(r.unit)}</td><td>${moneyOrMissing(r.unit_cost_snapshot)}</td><td>${moneyOrMissing(r.total_cost_snapshot)}</td><td>${r.expiration_date_snapshot ? formatDate(r.expiration_date_snapshot) : 'Не указан'}</td></tr>`).join('')}</tbody></table></div>` : '<p class="empty-hint">Списания компонентов в снимке не найдены.</p>'}</div>`; }
function productionPackagingTable(rows: ProductionBatchPackagingResponse[]) { return `<div class="readiness-block"><h3>Списанная тара</h3>${rows.length ? `<div class="table-wrap"><table class="compact-catalog-table"><thead><tr><th>Тара</th><th>Количество</th><th>Ед.</th><th>Цена за ед.</th><th>Стоимость</th></tr></thead><tbody>${rows.map((r)=>`<tr><td><strong>${escapeHtml(r.packaging_name_snapshot)}</strong></td><td>${formatDecimalForDisplay(r.quantity)}</td><td>${unitLabel(r.unit)}</td><td>${moneyOrMissing(r.unit_cost_snapshot)}</td><td>${moneyOrMissing(r.total_cost_snapshot)}</td></tr>`).join('')}</tbody></table></div>` : '<p class="empty-hint">Списания тары в снимке не найдены.</p>'}</div>`; }
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
function orderList(items: Order[]) { if (ordersState.items.length===0) return `<section class="card empty-card"><h2>Заказов пока нет</h2><p>Заказов пока нет. Создайте первый заказ на основе рецепта или индивидуальной формулы клиента.</p><button class="primary-action" type="button" data-action="open-order-create">Создать заказ</button></section>`; if (items.length===0) return `<section class="card empty-card"><h2>Заказы не найдены</h2><p>Измените поиск или статус, чтобы снова увидеть рабочий список.</p><button class="secondary-action" type="button" data-action="reset-order-filters">Сбросить фильтры</button></section>`; return `<section class="card data-card"><p class="card-kicker">Список</p><h2>Рабочие заказы</h2><div class="table-wrap"><table class="compact-catalog-table"><thead><tr><th>Продукт</th><th>Клиент</th><th>Основа</th><th>Партия</th><th>Тара</th><th>Статус</th><th>Дата/цена</th><th>Действия</th></tr></thead><tbody>${items.map((o)=>`<tr class="${ordersState.selectedOrder?.id===o.id?'catalog-row-selected':''} ${!o.is_active||o.status==='archived'?'archived-row':''}"><td><strong>${escapeHtml(o.product_name)}</strong><small>${escapeHtml(o.notes || 'Без заметок')}</small></td><td>${escapeHtml(orderClientName(o.client_id))}</td><td>${orderSourceLabel(o)}</td><td>${quantityLabel(o.target_batch_size_value, o.target_batch_size_unit)}</td><td>${orderPackagingLabel(o)}</td><td><span class="pill ${orderStatusPill(o)}">${orderStatusLabel(o.status)}</span></td><td>${o.planned_production_at ? `План: ${formatDate(o.planned_production_at)}` : 'План не указан'}<small>${o.sale_price ? `Цена: ${escapeHtml(o.sale_price)} ₽` : 'Цена не указана'}</small></td><td><div class="row-actions"><button class="secondary-action compact" type="button" data-action="open-order" data-id="${o.id}">Открыть</button>${orderLifecycleButtons(o)}</div></td></tr>`).join('')}</tbody></table></div><p class="next-step">Изготовление запускается только из карточки заказа после проверки готовности и отдельного подтверждения.</p></section>`; }
function orderLifecycleButtons(o: Order) { if (!o.is_active || o.status==='archived') return ''; if (o.status==='cancelled') return `<button class="secondary-action compact danger-action" type="button" data-action="archive-order" data-id="${o.id}">Архивировать</button>`; return `<button class="secondary-action compact danger-action" type="button" data-action="cancel-order" data-id="${o.id}">Отменить заказ</button><button class="secondary-action compact danger-action" type="button" data-action="archive-order" data-id="${o.id}">Архивировать</button>`; }
function orderFormPanel() { const f=ordersState.form; const isEdit=ordersState.formMode==='edit'; const selected=ordersState.selectedOrder; const blocked=isEdit && selected ? (selected.status==='cancelled' || selected.status==='archived' || !selected.is_active) : false; const activeClients=ordersState.clients.filter(c=>c.is_active); const activeVersions=ordersState.versions.filter(v=>v.status!=='archived'); const clientRecipeOptions=ordersState.clientRecipes.filter(r=>r.is_active && (!f.client_id || String(r.client_id)===f.client_id)); const noClients=activeClients.length===0; const noSources=activeVersions.length===0 && ordersState.clientRecipes.filter(r=>r.is_active).length===0; if (blocked) return `<section class="card form-card"><h2>${selected?.status==='cancelled'?'Отменённый заказ нельзя редактировать.':'Архивный заказ нельзя редактировать.'}</h2><p class="next-step">Карточка остаётся в истории. Можно закрыть форму и создать новый заказ при необходимости.</p><button class="secondary-action" type="button" data-action="close-order-form">Закрыть</button></section>`; if (ordersState.referenceLoading) return `<section class="card form-card" data-section="order-form"><p class="card-kicker">${isEdit?'Редактирование':'Создание'}</p><h2>${isEdit?'Изменить заказ':'Создать заказ'}</h2><p>Загружаем клиентов, рецепты и тару для заказа…</p><p class="next-step">Форма откроется с актуальными списками, чтобы клиент и рецепт не были пустыми из-за старого кэша.</p><button class="secondary-action" type="button" data-action="close-order-form">Закрыть форму</button></section>`; if (ordersState.referenceError) return `<section class="card form-card error-card" data-section="order-form"><p class="card-kicker">${isEdit?'Редактирование':'Создание'}</p><h2>${isEdit?'Изменить заказ':'Создать заказ'}</h2><p>${escapeHtml(ordersState.referenceError)}</p><p class="next-step">Повторная загрузка обновит только клиентов, рецепты и тару для формы заказа.</p><div class="actions"><button class="primary-action" type="button" data-action="reload-order-references">Повторить загрузку</button><button class="secondary-action" type="button" data-action="close-order-form">Закрыть форму</button></div></section>`; return `<section class="card form-card" data-section="order-form"><p class="card-kicker">${isEdit?'Редактирование':'Создание'}</p><h2>${isEdit?'Изменить заказ':'Создать заказ'}</h2><form data-form="order" class="ingredient-form"><div class="form-grid"><label>Клиент<select name="client_id" required ${noClients?'disabled':''}><option value="">Выберите клиента</option>${activeClients.map(c=>`<option value="${c.id}" ${f.client_id===String(c.id)?'selected':''}>${escapeHtml(c.full_name)}</option>`).join('')}</select></label><label>Основа заказа<select name="source_type" data-action="select-order-source-type"><option value="recipe_version" ${f.source_type==='recipe_version'?'selected':''}>Базовая версия рецепта</option><option value="client_recipe" ${f.source_type==='client_recipe'?'selected':''}>Индивидуальная формула клиента</option></select></label>${f.source_type==='recipe_version'?`<label class="full-span">Версия рецепта<select name="recipe_version_id" required ${activeVersions.length===0?'disabled':''}><option value="">Выберите версию</option>${activeVersions.map(v=>`<option value="${v.id}" ${f.recipe_version_id===String(v.id)?'selected':''}>${escapeHtml(orderVersionName(v))}</option>`).join('')}</select></label>`:`<label class="full-span">Индивидуальная формула<select name="client_recipe_id" required ${clientRecipeOptions.length===0?'disabled':''}><option value="">Выберите индивидуальную формулу</option>${clientRecipeOptions.map(r=>`<option value="${r.id}" ${f.client_recipe_id===String(r.id)?'selected':''}>${escapeHtml(r.title)} · ${escapeHtml(orderClientName(r.client_id))}</option>`).join('')}</select><small>${f.client_id?'Показаны формулы выбранного клиента.':'Выберите клиента, чтобы сузить список формул.'}</small></label>`}<label>Название продукта<input name="product_name" required maxlength="180" value="${escapeHtml(f.product_name)}" placeholder="Например, Крем дневной 50 мл" /></label><label>Размер партии<input name="target_batch_size_value" required inputmode="decimal" value="${escapeHtml(f.target_batch_size_value)}" placeholder="Например, 50" /></label><label>Единица<select name="target_batch_size_unit">${['g','ml','pcs'].map(u=>`<option value="${u}" ${f.target_batch_size_unit===u?'selected':''}>${unitLabel(u)}</option>`).join('')}</select></label><label>Тара<select name="packaging_item_id"><option value="">Без выбранной тары</option>${ordersState.packagingItems.filter(p=>p.is_active).map(p=>`<option value="${p.id}" ${f.packaging_item_id===String(p.id)?'selected':''}>${escapeHtml(p.name)}</option>`).join('')}</select></label><label>Количество тары<input name="packaging_quantity" inputmode="decimal" value="${escapeHtml(f.packaging_quantity)}" placeholder="Например, 1" /></label><label>Цена продажи<input name="sale_price" inputmode="decimal" value="${escapeHtml(f.sale_price)}" placeholder="Например, 2500" /></label><label>Дата заказа<input name="ordered_at" type="date" value="${escapeHtml(f.ordered_at)}" /></label><label>Плановая дата производства<input name="planned_production_at" type="date" value="${escapeHtml(f.planned_production_at)}" /></label><label class="full-span">Заметки<textarea name="notes" rows="3" maxlength="1600">${escapeHtml(f.notes)}</textarea></label></div>${noClients?'<p class="empty-hint">Сначала добавьте клиента, чтобы создать заказ.</p>':''}${noSources?'<p class="empty-hint">Для заказа нужен базовый рецепт или индивидуальная формула клиента.</p>':''}<p class="next-step">Форма не отправляет статус, дату производства или дату выдачи. Производство запускается отдельно из карточки заказа после проверки готовности.</p><div class="actions"><button class="primary-action" type="submit" ${noClients||noSources?'disabled':''}>${isEdit?'Сохранить изменения':'Создать заказ'}</button><button class="secondary-action" type="button" data-action="close-order-form">Закрыть форму</button></div></form></section>`; }
function orderDetailPanel(o: Order) {
  const closed = orderProductionClosed(o);
  const readinessAction = closed
    ? '<p class="next-step">Закрытые, выданные или уже изготовленные заказы нельзя проверять к производству.</p>'
    : `<button class="primary-action" type="button" data-action="check-order-readiness" data-id="${o.id}" ${ordersState.readinessLoadingOrderId === o.id ? 'disabled' : ''}>${ordersState.readinessLoadingOrderId === o.id ? 'Проверяем…' : 'Проверить изготовление'}</button>`;
  return `<section class="card data-card"><div class="section-heading"><div><p class="card-kicker">Карточка заказа</p><h2>${escapeHtml(o.product_name)}</h2></div><button class="secondary-action" type="button" data-action="close-order-detail">Закрыть карточку</button></div><p><strong>Клиент:</strong> ${escapeHtml(orderClientName(o.client_id))}</p><p><strong>Основа:</strong> ${orderSourceLabel(o)}</p><p><strong>Партия:</strong> ${quantityLabel(o.target_batch_size_value, o.target_batch_size_unit)}</p><p><strong>Тара:</strong> ${orderPackagingLabel(o)}</p><p><strong>Статус:</strong> ${orderStatusLabel(o.status)}</p><p><strong>Дата заказа:</strong> ${o.ordered_at?formatDate(o.ordered_at):'Не указана'} · <strong>План производства:</strong> ${o.planned_production_at?formatDate(o.planned_production_at):'Не указан'}</p><p><strong>Цена:</strong> ${o.sale_price?`${escapeHtml(o.sale_price)} ₽`:'Не указана'}</p><p><strong>Заметки:</strong><br>${escapeHtml(o.notes || 'Нет заметок')}</p>${o.status==='cancelled'?'<p class="next-step">Отменённый заказ нельзя редактировать.</p>':(!o.is_active||o.status==='archived')?'<p class="next-step">Архивный заказ нельзя редактировать.</p>':'<p class="next-step">Можно изменить только безопасные поля заказа. Производственные статусы здесь не меняются.</p>'}<div class="actions">${(o.status==='cancelled'||!o.is_active||o.status==='archived')?'':`<button class="secondary-action" type="button" data-action="edit-order" data-id="${o.id}">Изменить заказ</button>`}${readinessAction}${orderLifecycleButtons(o)}</div></section>${orderReadinessPanel(o)}${orderProductionPanel(o)}`;
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
function readinessPackagingTable(lines: ProductionReadinessPackagingLine[]) { return `<div class="readiness-block"><h3>Тара</h3>${lines.length ? `<div class="table-wrap"><table class="compact-catalog-table"><thead><tr><th>Тара</th><th>Нужно</th><th>Доступно</th><th>Не хватает</th><th>Статус</th></tr></thead><tbody>${lines.map((line) => `<tr><td><strong>${escapeHtml(line.name)}</strong></td><td>${quantityLabel(line.required_quantity, 'pcs')}</td><td>${quantityLabel(line.available_quantity, 'pcs')}</td><td>${missingQuantityLabel(line.missing_quantity, 'pcs')}</td><td><span class="pill ${line.can_fulfill ? 'success' : 'danger'}">${line.can_fulfill ? 'Хватает' : 'Не хватает'}</span></td></tr>`).join('')}</tbody></table></div>` : '<p class="empty-hint">Тара не выбрана или проверка тары не требуется.</p>'}</div>`; }
function readinessEstimates(result: ProductionReadinessResponse) { return `<div class="readiness-block"><h3>Предварительная экономика</h3><div class="readiness-grid"><div><strong>Ориентировочная себестоимость</strong><p>${moneyOrMissing(result.estimated_cost)}</p></div><div><strong>Налог</strong><p>${moneyOrMissing(result.estimated_tax)}</p></div><div><strong>Маржа</strong><p>${moneyOrMissing(result.estimated_margin)}</p></div></div><p class="next-step">Если налог или маржа не рассчитаны, интерфейс не подставляет налоговую ставку сам.</p></div>`; }
function formatDecimalForDisplay(value: string | null | undefined, maxFractionDigits = 3): string { if (value === null || value === undefined || value === '') return ''; const normalized = String(value).trim().replace(',', '.'); if (!/^-?\d+(\.\d+)?$/.test(normalized)) return escapeHtml(String(value)); const negative = normalized.startsWith('-'); const unsigned = negative ? normalized.slice(1) : normalized; const [integerPartRaw, fractionPart = ''] = unsigned.split('.'); const integerPart = integerPartRaw || '0'; const trimmedFraction = fractionPart.replace(/0+$/, '').slice(0, maxFractionDigits); const integerWithSpaces = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, ' '); return `${negative ? '-' : ''}${trimmedFraction ? `${integerWithSpaces},${trimmedFraction}` : integerWithSpaces}`; }
function normalizeDecimalInput(value: string | null | undefined): string { return String(value ?? '').trim().replace(',', '.'); }
function quantityLabel(value: string | null | undefined, unit: string | null | undefined) { const displayValue = formatDecimalForDisplay(value); const displayUnit = unit ? unitLabel(unit) : ''; return displayValue ? `${displayValue}${displayUnit ? ` ${displayUnit}` : ''}` : 'Не указано'; }
function missingQuantityLabel(value: string | null, unit: string) { return value === null || value === '' ? `0 ${unitLabel(unit)}` : quantityLabel(value, unit); }
function moneyOrMissing(value: string | null) { return value === null || value === '' ? 'Не рассчитано' : `${escapeHtml(value)} ₽`; }
function orderStatusLabel(status: string) { return ({new:'Новый',waiting_for_materials:'Ждёт компонентов',ready_to_produce:'Готов к производству',in_progress:'В производстве',produced:'Произведён',delivered:'Выдан',cancelled:'Отменён',archived:'В архиве'} as Record<string,string>)[status] ?? 'Неизвестный статус'; }
function orderStatusPill(o: Order) { if (o.status==='cancelled') return 'danger'; if (!o.is_active || o.status==='archived') return 'muted'; if (['waiting_for_materials','in_progress'].includes(o.status)) return 'warning'; return 'success'; }
function orderClientName(id:number){ return ordersState.clients.find(c=>c.id===id)?.full_name ?? `Клиент ${id}`; }
function orderVersionName(v: RecipeVersion){ const template=ordersState.templates.find(t=>t.id===v.recipe_template_id); return `${template?.name ?? 'Базовый рецепт'} · версия №${v.version_number} · ${v.title || 'Без заголовка'}`; }
function orderSourceLabel(o: Order){ if (o.client_recipe_id) return `Индивидуальная формула: ${escapeHtml(ordersState.clientRecipes.find(r=>r.id===o.client_recipe_id)?.title ?? `№${o.client_recipe_id}`)}`; if (o.recipe_version_id) { const v=ordersState.versions.find(v=>v.id===o.recipe_version_id); return `Базовая версия рецепта: ${escapeHtml(v ? orderVersionName(v) : `№${o.recipe_version_id}`)}`; } return 'Источник не указан'; }
function orderPackagingLabel(o: Order){ const p=o.packaging_item_id ? ordersState.packagingItems.find(p=>p.id===o.packaging_item_id) : null; if (!p) return o.packaging_quantity ? `${formatDecimalForDisplay(o.packaging_quantity)} · тара не выбрана` : 'Не выбрана'; return `${escapeHtml(p.name)}${o.packaging_quantity ? ` · ${quantityLabel(o.packaging_quantity, p.unit)}` : ''}`; }
function filteredOrders(){ const search=ordersState.filters.search.trim().toLocaleLowerCase('ru-RU'); return ordersState.items.filter(o=>{ if (ordersState.filters.status==='active' && (o.status==='cancelled'||o.status==='archived'||!o.is_active)) return false; if (ordersState.filters.status==='cancelled' && o.status!=='cancelled') return false; if (ordersState.filters.status==='archived' && o.status!=='archived' && o.is_active) return false; if (!search) return true; return [o.product_name, o.notes, orderClientName(o.client_id), orderSourceLabel(o), orderPackagingLabel(o), orderStatusLabel(o.status)].join(' ').toLocaleLowerCase('ru-RU').includes(search); }); }

function saveOrderFormDraftFromDom() { const form = document.querySelector<HTMLFormElement>('[data-form="order"]'); if (!form) return; const data = new FormData(form); ordersState.form = { ...ordersState.form, client_id: String(data.get('client_id') || ''), source_type: String(data.get('source_type') || ordersState.form.source_type) as OrderSourceType, recipe_version_id: String(data.get('recipe_version_id') || ''), client_recipe_id: String(data.get('client_recipe_id') || ''), product_name: String(data.get('product_name') || ''), target_batch_size_value: String(data.get('target_batch_size_value') || ''), target_batch_size_unit: String(data.get('target_batch_size_unit') || 'g'), packaging_item_id: String(data.get('packaging_item_id') || ''), packaging_quantity: String(data.get('packaging_quantity') || ''), sale_price: String(data.get('sale_price') || ''), ordered_at: String(data.get('ordered_at') || ''), planned_production_at: String(data.get('planned_production_at') || ''), notes: String(data.get('notes') || '') }; }
function orderPayloadFromForm(form: HTMLFormElement): OrderPayload | string { const data=new FormData(form); const packagingItem=String(data.get('packaging_item_id') || ''); const packagingQty=normalizeDecimalInput(String(data.get('packaging_quantity') || '')); if (packagingQty && !packagingItem) return 'Если указано количество тары, выберите саму тару.'; const sourceType=String(data.get('source_type')) as OrderSourceType; return { client_id: Number(data.get('client_id')) || null, recipe_version_id: sourceType==='recipe_version' ? Number(data.get('recipe_version_id')) || null : null, client_recipe_id: sourceType==='client_recipe' ? Number(data.get('client_recipe_id')) || null : null, product_name: String(data.get('product_name') || '').trim(), target_batch_size_value: normalizeDecimalInput(String(data.get('target_batch_size_value') || '')), target_batch_size_unit: String(data.get('target_batch_size_unit') || 'g'), packaging_item_id: packagingItem ? Number(packagingItem) : null, packaging_quantity: packagingQty || null, sale_price: normalizeDecimalInput(String(data.get('sale_price') || '')) || null, ordered_at: String(data.get('ordered_at') || '') || null, planned_production_at: String(data.get('planned_production_at') || '') || null, notes: String(data.get('notes') || '') }; }
function formFromOrder(o: Order): OrderFormState { return { id:o.id, client_id:String(o.client_id), source_type:o.client_recipe_id?'client_recipe':'recipe_version', recipe_version_id:o.recipe_version_id?String(o.recipe_version_id):'', client_recipe_id:o.client_recipe_id?String(o.client_recipe_id):'', product_name:o.product_name, target_batch_size_value:o.target_batch_size_value, target_batch_size_unit:o.target_batch_size_unit, packaging_item_id:o.packaging_item_id?String(o.packaging_item_id):'', packaging_quantity:o.packaging_quantity ?? '', sale_price:o.sale_price ?? '', ordered_at:o.ordered_at ?? '', planned_production_at:o.planned_production_at ?? '', notes:o.notes }; }
function loadOrderReferenceData(): Promise<void> { return Promise.all([getClients(true), getRecipeTemplates(), getClientRecipes(true), getPackagingItems()]).then(async ([clients, templates, clientRecipes, packaging])=>{ const versionLists=await Promise.all(templates.recipe_templates.map(t=>getRecipeVersions(t.id).catch(()=>({recipe_versions:[]})))); ordersState.clients=clients.clients; ordersState.templates=templates.recipe_templates; ordersState.versions=versionLists.flatMap(v=>v.recipe_versions); ordersState.clientRecipes=clientRecipes.client_recipes; ordersState.packagingItems=packaging.packaging_items; }); }
function loadOrders(force=false){ if(!force && ordersStatus==='loading') return; if(!force && ordersStatus==='ready') return; ordersStatus='loading'; ordersError=''; render(); Promise.all([getOrders(true), loadOrderReferenceData()]).then(([orders])=>{ ordersState.items=orders.orders; ordersStatus='ready'; render(); }).catch(()=>{ ordersStatus='error'; ordersError='Не удалось загрузить заказы. Проверьте локальное приложение и попробуйте ещё раз.'; render(); }); }
function focusOrderFormClient() { requestAnimationFrame(() => { document.querySelector<HTMLSelectElement>('[data-form="order"] select[name="client_id"]')?.focus(); }); }
function reloadOrderReferencesForForm(){ if (ordersState.referenceLoading) return; ordersState.referenceLoading=true; ordersState.referenceError=''; render(); loadOrderReferenceData().then(()=>{ ordersState.referenceLoading=false; ordersState.referenceError=''; ordersStatus='ready'; render(); focusOrderFormClient(); }).catch(()=>{ ordersState.referenceLoading=false; ordersState.referenceError='Не удалось загрузить клиентов и рецепты для заказа. Проверьте локальное приложение и попробуйте ещё раз.'; render(); }); }
function openOrderCreate(){ if (ordersState.referenceLoading && ordersState.showForm && ordersState.formMode==='create') return; ordersState.formMode='create'; ordersState.form=emptyOrderForm(); ordersState.showForm=true; ordersState.selectedOrder=null; ordersMessage=''; ordersError=''; ordersState.referenceLoading=true; ordersState.referenceError=''; render(); loadOrderReferenceData().then(()=>{ ordersState.referenceLoading=false; ordersState.referenceError=''; ordersStatus='ready'; render(); focusOrderFormClient(); }).catch(()=>{ ordersState.referenceLoading=false; ordersState.referenceError='Не удалось загрузить клиентов и рецепты для заказа. Проверьте локальное приложение и попробуйте ещё раз.'; render(); }); }
function openOrder(id:number){ const fallback=ordersState.items.find(i=>i.id===id) ?? null; ordersState.selectedOrder=fallback; ordersState.showForm=false; ordersMessage=''; ordersError=''; render(); getOrder(id).then((order)=>{ ordersState.selectedOrder=order; render(); }).catch(()=>{ ordersError='Не удалось открыть карточку заказа. Попробуйте обновить список.'; render(); }); }
function checkOrderReadiness(id:number){ const order=ordersState.selectedOrder?.id===id ? ordersState.selectedOrder : ordersState.items.find(i=>i.id===id) ?? null; if(!order || orderProductionClosed(order)) return; ordersState.readinessLoadingOrderId=id; ordersState.readinessError=''; render(); checkOrderProductionReadiness(id).then((result)=>{ ordersState.readinessByOrderId[id]=result; ordersState.readinessLoadingOrderId=null; ordersState.readinessError=''; render(); }).catch((e)=>{ ordersState.readinessLoadingOrderId=null; const msg=e instanceof Error && e.message && e.message !== 'API request failed' ? e.message : ''; ordersState.readinessError=msg || 'Не удалось проверить готовность производства.'; render(); }); }

function openProductionConfirmation(id:number){ const order=ordersState.selectedOrder?.id===id ? ordersState.selectedOrder : ordersState.items.find(i=>i.id===id) ?? null; const readiness=ordersState.readinessByOrderId[id]; if(!order || orderProductionClosed(order) || !readiness?.can_produce) return; ordersState.productionConfirmingOrderId=id; ordersState.productionError=''; render(); }
function cancelProductionConfirmation(id:number){ if(ordersState.productionLoadingOrderId===id) return; if(ordersState.productionConfirmingOrderId===id) ordersState.productionConfirmingOrderId=null; render(); }
function confirmProduction(id:number){ const order=ordersState.selectedOrder?.id===id ? ordersState.selectedOrder : ordersState.items.find(i=>i.id===id) ?? null; const readiness=ordersState.readinessByOrderId[id]; if(!order || orderProductionClosed(order) || !readiness?.can_produce) return; ordersState.productionLoadingOrderId=id; ordersState.productionError=''; render(); produceOrder(id, ordersState.productionNotesByOrderId[id]).then((batch)=>{ ordersState.productionByOrderId[id]=batch; delete ordersState.readinessByOrderId[id]; ordersState.productionLoadingOrderId=null; ordersState.productionConfirmingOrderId=null; ordersState.productionError=''; ordersState.productionNotesByOrderId[id]=''; return Promise.all([getOrders(true), getOrder(id)]); }).then(([orders, updated])=>{ ordersState.items=orders.orders; ordersState.selectedOrder=updated; render(); }).catch((e)=>{ ordersState.productionLoadingOrderId=null; ordersState.productionError=humanProductionError(e); render(); }); }

function editOrder(id:number){ const o=ordersState.items.find(i=>i.id===id); if(!o) return; ordersState.selectedOrder=o; ordersState.formMode='edit'; ordersState.form=formFromOrder(o); ordersState.showForm=true; ordersMessage=''; ordersError=''; ordersState.referenceLoading=true; ordersState.referenceError=''; render(); loadOrderReferenceData().then(()=>{ ordersState.referenceLoading=false; ordersState.referenceError=''; render(); focusOrderFormClient(); }).catch(()=>{ ordersState.referenceLoading=false; ordersState.referenceError='Не удалось загрузить клиентов и рецепты для заказа. Проверьте локальное приложение и попробуйте ещё раз.'; render(); }); }
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
  if (clientsStatus === 'idle' || clientsStatus === 'loading') return `<section class="card"><p class="card-kicker">Клиенты</p><h2>Загружаем клиентов…</h2><p>Загружаем карточки клиентов.</p></section>`;
  if (clientsStatus === 'error') return `<section class="card error-card"><p class="card-kicker">Клиенты</p><h2>Не удалось загрузить клиентов</h2><p>${clientsError || 'Не удалось загрузить клиентов. Проверьте, что локальное приложение запущено.'}</p><p class="next-step">Проверьте, что локальное приложение запущено, и попробуйте обновить раздел.</p><button class="primary-action" type="button" data-action="reload-clients">Повторить загрузку</button></section>`;
  const workspace = clientsState.formMode === 'edit' || clientsState.showCreateForm ? clientForm() : '';
  return `<div class="catalog-layout"><section class="card catalog-intro"><div><p class="card-kicker">Клиенты</p><h2>Клиенты</h2><p>Карточки клиентов, пожелания, ограничения и заметки для индивидуальных рецептов.</p><p class="next-step">Сначала найдите клиента в списке. Создание и редактирование открываются только когда нужно.</p></div><div class="actions"><button class="primary-action" type="button" data-action="open-client-create" ${clientSubmitting ? 'disabled' : ''}>Создать клиента</button><button class="secondary-action" type="button" data-action="reload-clients">Обновить</button></div></section>${clientsMessage ? `<p class="page-message">${clientsMessage}</p>` : ''}${clientsRefreshWarning ? `<p class="page-message warning-message">${clientsRefreshWarning}</p>` : ''}${clientsError ? `<p class="page-message error-message">${clientsError}</p>` : ''}${clientFilterToolbar()}${workspace}${clientList()}${!workspace ? clientCreateHelper() : ''}</div>`;
}

function clientFilterToolbar() {
  const f = clientsState.filters;
  const activeFilters = clientActiveFilterChips();
  return `<section class="card data-card catalog-browser"><p class="card-kicker">Рабочий список</p><h2>Найти клиента</h2><div class="catalog-toolbar"><label class="full-span">Поиск<input type="search" data-action="filter-clients-search" value="${escapeHtml(f.search)}" placeholder="ФИО, телефон, email, заметки, аллергии или предпочтения" /></label><label>Статус<select data-action="filter-clients-status"><option value="active" ${f.status === 'active' ? 'selected' : ''}>Активные</option><option value="archived" ${f.status === 'archived' ? 'selected' : ''}>Архив</option><option value="all" ${f.status === 'all' ? 'selected' : ''}>Все</option></select></label></div>${activeFilters ? `<div class="active-filter-row"><strong>Активные фильтры:</strong>${activeFilters}</div>` : ''}<div class="catalog-summary"><span>Показаны клиенты: ${filteredClients().length} из ${clientsState.items.length}</span><button class="secondary-action compact" type="button" data-action="reset-client-filters">Сбросить фильтры</button></div></section>`;
}

function clientForm() {
  const form = clientsState.form;
  const isEdit = clientsState.formMode === 'edit';
  const secondaryAction = isEdit
    ? `<button class="secondary-action" type="button" data-action="cancel-client-edit" ${clientSubmitting ? 'disabled' : ''}>Закрыть редактирование</button>`
    : `<button class="secondary-action" type="button" data-action="hide-client-create" ${clientSubmitting ? 'disabled' : ''}>Вернуться к списку</button>`;
  return `<section class="card form-card"><p class="card-kicker">${isEdit ? 'Редактирование' : 'Создание'}</p><h2>${isEdit ? 'Изменить карточку клиента' : 'Создать клиента'}</h2><form data-form="client" class="ingredient-form" novalidate>${validationSummary(clientValidation, 'Проверьте форму клиента')}<div class="form-grid">${clientField(`ФИО клиента<input name="full_name" data-field="client-full-name" required maxlength="200" value="${escapeHtml(form.full_name)}" placeholder="Например, Анна Иванова"${clientFieldAttrs('full_name')} />`, 'full_name')}${clientField(`Телефон<input name="phone" maxlength="80" value="${escapeHtml(form.phone)}" placeholder="+7 ..."${clientFieldAttrs('phone')} />`, 'phone')}${clientField(`Email<input name="email" type="email" maxlength="160" value="${escapeHtml(form.email)}" placeholder="Необязательно"${clientFieldAttrs('email')} />`, 'email')}${clientField(`Дата рождения<input name="birthday" type="date" value="${escapeHtml(form.birthday ?? '')}"${clientFieldAttrs('birthday')} />`, 'birthday')}${clientField(`Адрес<input name="address" maxlength="300" value="${escapeHtml(form.address)}" placeholder="Необязательно"${clientFieldAttrs('address')} />`, 'address', true)}${clientField(`Особенности кожи<textarea name="skin_notes" rows="2" maxlength="1200" placeholder="Например, чувствительная кожа"${clientFieldAttrs('skin_notes')}>${escapeHtml(form.skin_notes)}</textarea>`, 'skin_notes', true)}${clientField(`Аллергии<textarea name="allergy_notes" rows="2" maxlength="1200" placeholder="Что важно учитывать в составах"${clientFieldAttrs('allergy_notes')}>${escapeHtml(form.allergy_notes)}</textarea>`, 'allergy_notes', true)}${clientField(`Предпочтения<textarea name="preference_notes" rows="2" maxlength="1200" placeholder="Текстуры, ароматы, упаковка"${clientFieldAttrs('preference_notes')}>${escapeHtml(form.preference_notes)}</textarea>`, 'preference_notes', true)}${clientField(`Противопоказания<textarea name="contraindication_notes" rows="2" maxlength="1200" placeholder="Ограничения, которые нельзя забыть"${clientFieldAttrs('contraindication_notes')}>${escapeHtml(form.contraindication_notes)}</textarea>`, 'contraindication_notes', true)}${clientField(`Заметки<textarea name="notes" rows="3" maxlength="1600" placeholder="Рабочие заметки по клиенту"${clientFieldAttrs('notes')}>${escapeHtml(form.notes)}</textarea>`, 'notes', true)}</div><p class="next-step">Аллергии, предпочтения и противопоказания помогут позже безопасно создавать индивидуальные рецепты клиента.</p><div class="actions"><button class="primary-action" type="submit" ${clientSubmitting ? 'disabled' : ''}>${clientSubmitting ? 'Сохраняем…' : isEdit ? 'Сохранить карточку' : 'Создать клиента'}</button>${secondaryAction}</div></form>${isEdit ? clientWishesSection() + clientFeedbackSection() : ''}</section>`;
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
  return `<section class="card data-card"><p class="card-kicker">Список</p><h2>${clientListTitle()}</h2><div class="table-wrap"><table class="compact-catalog-table"><thead><tr><th>Клиент</th><th>Контакты</th><th>Важное</th><th>Статус</th><th>Действия</th></tr></thead><tbody>${items.map((client) => { const isEditing = clientsState.formMode === 'edit' && clientsState.form.id === client.id; return `<tr class="${isEditing ? 'catalog-row-selected' : ''}"><td><strong>${escapeHtml(client.full_name)}</strong>${isEditing ? '<small><span class="pill warning">Редактируется</span></small>' : ''}<small>${client.birthday ? `Дата рождения: ${formatDate(client.birthday)}` : 'Дата рождения не указана'}</small></td><td>${client.phone ? escapeHtml(client.phone) : 'Телефон не указан'}<small>${client.email ? escapeHtml(client.email) : 'Email не указан'}</small></td><td>${clientNotesSummary(client)}</td><td><span class="pill ${client.is_active ? 'success' : 'muted'}">${client.is_active ? 'Активен' : 'Архив'}</span></td><td><div class="row-actions"><button class="secondary-action compact" type="button" data-action="start-client-edit" data-id="${client.id}" ${clientSubmitting ? 'disabled' : ''}>Изменить</button>${client.is_active ? `<button class="secondary-action compact danger-action" type="button" data-action="archive-client" data-id="${client.id}">Архивировать</button>` : ''}</div></td></tr>`; }).join('')}</tbody></table></div><p class="next-step">Длинные заметки остаются в карточке редактирования, чтобы список был компактным.</p></section>`;
}

function clientCreateHelper() {
  return `<section class="card empty-card"><h2>Нужно добавить нового клиента?</h2><p>Форма создания скрыта, чтобы рабочий список оставался на первом экране.</p><button class="secondary-action" type="button" data-action="open-client-create">Создать клиента</button></section>`;
}

function ingredientsPage() {
  if (ingredientsStatus === 'idle' || ingredientsStatus === 'loading') return `<section class="card"><p class="card-kicker">Компоненты</p><h2>Загружаем компоненты…</h2><p>Загружаем справочник компонентов.</p></section>`;
  if (ingredientsStatus === 'error') return `<section class="card error-card"><p class="card-kicker">Компоненты</p><h2>Не удалось загрузить компоненты</h2><p>${ingredientsError || 'Данные временно недоступны.'}</p><p class="next-step">Проверьте, что приложение запущено полностью, и попробуйте обновить раздел.</p><button class="primary-action" type="button" data-action="reload-ingredients">Повторить загрузку</button></section>`;
  const filtered = filteredIngredients();
  const isEdit = ingredientsState.formMode === 'edit';
  const isCreateActive = ingredientsState.formMode === 'create' && ingredientsState.showCreateForm;
  const activeWorkspace = isEdit ? `${ingredientForm()}${ingredientCatalogPanel()}` : isCreateActive ? ingredientForm() : '';
  const secondaryWorkspace = isEdit ? '' : isCreateActive ? ingredientCatalogPanel() : `${ingredientForm()}${ingredientCatalogPanel()}`;
  return `<div class="catalog-layout"><section class="card catalog-intro"><div><p class="card-kicker">Каталог компонентов</p><h2>Компоненты</h2><p>Сначала найдите существующий компонент по названию, группе, меткам, системному типу или статусу. Создание и редактирование доступны ниже, чтобы каталог оставался главным рабочим местом.</p><p class="next-step">Системный тип используется программой. Группа и метки — ваш способ организовать компоненты для поиска.</p></div><div class="actions"><button class="secondary-action" type="button" data-action="reload-ingredients">Обновить список</button><button class="primary-action" type="button" data-action="new-ingredient" ${ingredientSubmitting ? 'disabled' : ''}>Создать компонент</button></div></section>${ingredientsMessage ? `<p class="page-message">${ingredientsMessage}</p>` : ''}${ingredientsRefreshWarning ? `<p class="page-message warning-message">${ingredientsRefreshWarning}</p>` : ''}${ingredientsError ? `<p class="page-message error-message">${ingredientsError}</p>` : ''}${ingredientCatalogToolbar(filtered.length)}${activeWorkspace}${ingredientList(filtered)}${secondaryWorkspace}</div>`;
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
  return `<section class="card data-card"><p class="card-kicker">Результаты каталога</p><h2>Найденные компоненты</h2><p class="catalog-results-summary">Показаны компоненты: ${items.length} из ${ingredientsState.items.length}</p><div class="table-wrap"><table class="compact-catalog-table"><thead><tr><th>Название</th><th>Системный тип</th><th>Ед. учета</th><th>Группа</th><th>Метки</th><th>Статус</th><th>Действия</th></tr></thead><tbody>${items.map((item) => `<tr><td><strong>${escapeHtml(item.name)}</strong><small>${item.supplier_hint ? escapeHtml(item.supplier_hint) : 'Поставщик не указан'}</small></td><td>${escapeHtml(categoryLabel(item.category))}</td><td>${unitLabel(item.default_unit)}</td><td>${escapeHtml(ingredientCatalogCategoryLabel(item))}</td><td>${ingredientTagChips(item)}</td><td><span class="pill ${item.is_active ? 'success' : 'muted'}">${item.is_active ? 'Активен' : 'Архив'}</span></td><td><div class="row-actions"><button class="secondary-action compact" type="button" data-action="edit-ingredient" data-id="${item.id}" ${ingredientSubmitting ? 'disabled' : ''}>Изменить</button>${item.is_active ? `<button class="secondary-action compact danger-action" type="button" data-action="deactivate-ingredient" data-id="${item.id}">Деактивировать</button>` : ''}</div></td></tr>`).join('')}</tbody></table></div></section>`;
}



function ingredientForm() {
  const form = ingredientsState.form;
  const isEdit = ingredientsState.formMode === 'edit';
  if (!isEdit && !ingredientsState.showCreateForm) return `<section class="card form-card collapsed-create-card"><div><p class="card-kicker">Создание</p><h2>Создать новый компонент</h2><p>Форма создания скрыта, чтобы каталог оставался первым рабочим экраном.</p></div><button class="primary-action" type="button" data-action="new-ingredient" ${ingredientSubmitting ? 'disabled' : ''}>Создать компонент</button></section>`;
  const secondaryAction = isEdit
    ? `<button class="secondary-action" type="button" data-action="cancel-ingredient-edit" ${ingredientSubmitting ? 'disabled' : ''}>Отменить редактирование</button>`
    : `<button class="secondary-action" type="button" data-action="hide-ingredient-create-form" ${ingredientSubmitting ? 'disabled' : ''}>Вернуться к каталогу</button>`;
  return `<section class="card form-card" data-section="ingredient-form"><p class="card-kicker">${isEdit ? 'Редактирование' : 'Создание'}</p><h2>${isEdit ? 'Изменить компонент' : 'Создать компонент'}</h2><form data-form="ingredient" class="ingredient-form" novalidate>${validationSummary(ingredientValidation, 'Проверьте форму компонента')}<div class="form-grid">${ingredientField(`Название<input name="name" required maxlength="160" value="${escapeHtml(form.name)}" placeholder="Например, масло ши"${ingredientFieldAttrs('name')} />`, 'name')}${ingredientField(`Категория<select name="category"${ingredientFieldAttrs('category')}>${categoryOptions(form.category)}</select>`, 'category')}${ingredientField(`Единица учета<select name="default_unit"${ingredientFieldAttrs('default_unit')}>${unitOptions(form.default_unit)}</select>`, 'default_unit')}${ingredientField(`Плотность<input name="density_g_per_ml" inputmode="decimal" value="${escapeHtml(form.density_g_per_ml ?? '')}" placeholder="Например, 0.950"${ingredientFieldAttrs('density_g_per_ml')} />`, 'density_g_per_ml')}${ingredientField(`Поставщик<input name="supplier_hint" maxlength="160" value="${escapeHtml(form.supplier_hint)}" placeholder="Необязательно"${ingredientFieldAttrs('supplier_hint')} />`, 'supplier_hint')}${ingredientField(`INCI<input name="inci_name" maxlength="240" value="${escapeHtml(form.inci_name)}" placeholder="Необязательно"${ingredientFieldAttrs('inci_name')} />`, 'inci_name')}${ingredientField(`Заметки<textarea name="notes" rows="3" maxlength="1200" placeholder="Короткие рабочие заметки"${ingredientFieldAttrs('notes')}>${escapeHtml(form.notes)}</textarea>`, 'notes', true)}${ingredientField(`Ограничения и аллергены<textarea name="allergen_note" rows="2" maxlength="800" placeholder="Необязательно"${ingredientFieldAttrs('allergen_note')}>${escapeHtml(form.allergen_note)}</textarea>`, 'allergen_note', true)}${ingredientField(`Применение<textarea name="usage_note" rows="2" maxlength="800" placeholder="Необязательно"${ingredientFieldAttrs('usage_note')}>${escapeHtml(form.usage_note)}</textarea>`, 'usage_note', true)}</div><div class="actions"><button class="primary-action" type="submit" ${ingredientSubmitting ? 'disabled' : ''}>${ingredientSubmitting ? 'Сохраняем…' : isEdit ? 'Сохранить изменения' : 'Создать компонент'}</button>${secondaryAction}</div></form></section>`;
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
  return `<div class="catalog-create-grid"><form data-form="ingredient-catalog-category" class="catalog-create-form"><h3>Добавить группу</h3><label>Название группы<input name="name" required maxlength="160" placeholder="Например, Масла" ${categoryDisabled ? 'disabled' : ''} /></label><button class="secondary-action" type="submit" ${categoryDisabled ? 'disabled' : ''}>${ingredientsState.catalogCreating === 'category' ? 'Создаём…' : 'Создать группу'}</button></form><form data-form="ingredient-catalog-tag" class="catalog-create-form"><h3>Добавить метку</h3><label>Название метки<input name="name" required maxlength="160" placeholder="Например, Для лица" ${tagDisabled ? 'disabled' : ''} /></label><button class="secondary-action" type="submit" ${tagDisabled ? 'disabled' : ''}>${ingredientsState.catalogCreating === 'tag' ? 'Создаём…' : 'Создать метку'}</button></form></div>`;
}

function packagingItemsPage() {
  if (packagingItemsStatus === 'idle' || packagingItemsStatus === 'loading') return `<section class="card"><p class="card-kicker">Тара</p><h2>Загружаем тару…</h2><p>Загружаем справочник тары.</p></section>`;
  if (packagingItemsStatus === 'error') return `<section class="card error-card"><p class="card-kicker">Тара</p><h2>Не удалось загрузить тару</h2><p>${packagingItemsError || 'Данные временно недоступны.'}</p><p class="next-step">Проверьте, что приложение запущено полностью, и попробуйте обновить раздел.</p><button class="primary-action" type="button" data-action="reload-packaging-items">Повторить загрузку</button></section>`;
  const filtered = filteredPackagingItems();
  const isEdit = packagingItemsState.formMode === 'edit';
  const isCreateActive = packagingItemsState.formMode === 'create' && packagingItemsState.showCreateForm;
  const activeWorkspace = isEdit ? `${packagingItemForm()}${packagingCatalogPanel()}` : isCreateActive ? packagingItemForm() : '';
  const secondaryWorkspace = isEdit ? '' : isCreateActive ? packagingCatalogPanel() : `${packagingItemForm()}${packagingCatalogPanel()}`;
  return `<div class="catalog-layout"><section class="card catalog-intro"><div><p class="card-kicker">Каталог тары</p><h2>Тара и расходники</h2><p>Сначала найдите тару по названию, группе, меткам, типу или статусу. Создание и редактирование доступны ниже, чтобы каталог оставался главным рабочим местом.</p><p class="next-step">Тип тары используется системой. Группа и метки — ваш способ организовать каталог для поиска.</p></div><div class="actions"><button class="secondary-action" type="button" data-action="reload-packaging-items" ${packagingPageMutationActive() ? 'disabled' : ''}>Обновить список</button><button class="primary-action" type="button" data-action="new-packaging-item" ${packagingPageMutationActive() ? 'disabled' : ''}>Создать тару</button></div></section>${packagingItemsMessage ? `<p class="page-message">${packagingItemsMessage}</p>` : ''}${packagingItemsRefreshWarning ? `<p class="page-message warning-message">${packagingItemsRefreshWarning}</p>` : ''}${packagingItemsError ? `<p class="page-message error-message">${packagingItemsError}</p>` : ''}${packagingCatalogToolbar(filtered.length)}${activeWorkspace}${packagingItemsList(filtered)}${secondaryWorkspace}</div>`;
}

function packagingItemForm() {
  const form = packagingItemsState.form;
  const isEdit = packagingItemsState.formMode === 'edit';
  if (!isEdit && !packagingItemsState.showCreateForm) return `<section class="card form-card collapsed-create-card"><div><p class="card-kicker">Создание</p><h2>Создать новую тару</h2><p>Форма создания скрыта, чтобы каталог тары оставался первым рабочим экраном.</p></div><button class="primary-action" type="button" data-action="new-packaging-item">Создать тару</button></section>`;
  return `<section class="card form-card" data-section="packaging-form"><p class="card-kicker">${isEdit ? 'Редактирование' : 'Создание'}</p><h2>${isEdit ? 'Изменить тару' : 'Добавить тару'}</h2><form data-form="packaging-item" class="ingredient-form" novalidate>${validationSummary(packagingItemValidation, 'Проверьте форму тары')}<div class="form-grid">${packagingItemField(`Название<input name="name" required maxlength="160" value="${escapeHtml(form.name)}" placeholder="Например, баночка 30 мл" ${packagingPageMutationActive() ? 'disabled' : ''}${packagingItemFieldAttrs('name')} />`, 'name')}${packagingItemField(`Тип тары<select name="kind" ${packagingPageMutationActive() ? 'disabled' : ''}${packagingItemFieldAttrs('kind')}>${packagingKindOptions(form.kind)}</select>`, 'kind')}${packagingItemField(`Единица учета<select name="unit" ${packagingPageMutationActive() ? 'disabled' : ''}${packagingItemFieldAttrs('unit')}>${packagingUnitOptions(form.unit)}</select>`, 'unit')}${packagingItemField(`Объем<input name="capacity_value" inputmode="decimal" value="${escapeHtml(form.capacity_value ?? '')}" placeholder="Например, 30" ${packagingPageMutationActive() ? 'disabled' : ''}${packagingItemFieldAttrs('capacity_value')} />`, 'capacity_value')}${packagingItemField(`Единица объема<select name="capacity_unit" ${packagingPageMutationActive() ? 'disabled' : ''}${packagingItemFieldAttrs('capacity_unit')}><option value="" ${form.capacity_unit ? '' : 'selected'}>Не указана</option>${capacityUnitOptions(form.capacity_unit ?? '')}</select>`, 'capacity_unit')}${packagingItemField(`Материал<input name="material" maxlength="120" value="${escapeHtml(form.material)}" placeholder="Стекло, пластик, бумага…" ${packagingPageMutationActive() ? 'disabled' : ''}${packagingItemFieldAttrs('material')} />`, 'material')}${packagingItemField(`Поставщик<input name="supplier_hint" maxlength="160" value="${escapeHtml(form.supplier_hint)}" placeholder="Необязательно" ${packagingPageMutationActive() ? 'disabled' : ''}${packagingItemFieldAttrs('supplier_hint')} />`, 'supplier_hint')}${packagingItemField(`Цена за единицу<input name="unit_cost" inputmode="decimal" value="${escapeHtml(form.unit_cost ?? '')}" placeholder="Например, 12.50" ${packagingPageMutationActive() ? 'disabled' : ''}${packagingItemFieldAttrs('unit_cost')} />`, 'unit_cost')}${packagingItemField(`Заметки<textarea name="notes" rows="3" maxlength="1200" placeholder="Короткие рабочие заметки о таре" ${packagingPageMutationActive() ? 'disabled' : ''}${packagingItemFieldAttrs('notes')}>${escapeHtml(form.notes)}</textarea>`, 'notes', true)}</div><div class="actions"><button class="primary-action" type="submit" ${packagingPageMutationActive() ? 'disabled' : ''}>${packagingItemSubmitting ? 'Сохраняем…' : isEdit ? 'Сохранить изменения' : 'Создать тару'}</button>${isEdit ? `<button class="secondary-action" type="button" data-action="cancel-packaging-edit" ${packagingPageMutationActive() ? 'disabled' : ''}>Закрыть редактирование</button>` : `<button class="secondary-action" type="button" data-action="hide-packaging-create-form" ${packagingPageMutationActive() ? 'disabled' : ''}>Вернуться к каталогу</button>`}</div><p class="next-step">Остатки, приход и списания не меняются в этой форме — для них будут отдельные складские операции.</p></form></section>`;
}

function packagingCatalogPanel() {
  const item = packagingItemsState.formMode === 'edit' && packagingItemsState.form.id ? packagingItemsState.items.find((packagingItem) => packagingItem.id === packagingItemsState.form.id) : null;
  const createControls = packagingCatalogCreateControls();
  const helperCopy = 'Тип тары — системный тип для учета. Группа и метки — ваш способ навести порядок в каталоге.';
  if (!item) return `<section class="card catalog-helper-card"><p class="card-kicker">Организация каталога тары</p><h2>Группа и метки</h2><p>${helperCopy}</p><p>Группа помогает разложить записи по рабочим пространствам. Метки помогают быстро фильтровать и находить записи.</p><p>Чтобы назначить их конкретной таре, нажмите «Изменить» у нужной тары.</p>${createControls}<p class="next-step">Созданные группы и метки появляются здесь сразу. Они не добавляются в выпадающий список «Тип тары».</p></section>`;
  const draft = packagingItemsState.assignmentDraft.itemId === item.id ? packagingItemsState.assignmentDraft : assignmentDraftFromItem(item);
  const isDirty = assignmentDraftIsDirty(item, draft);
  const draftNotice = isDirty ? '<p class="page-message">Есть несохранённые изменения</p>' : '';
  return `<section class="card form-card"><p class="card-kicker">Организация каталога тары</p><h2>Группа и метки</h2><p>${helperCopy}</p><div class="catalog-classification">${catalogCategoryPicker({ itemId: item.id, selectedId: draft.catalogCategoryId, categories: packagingItemsState.catalogCategories, state: packagingCatalogControls, disabled: packagingPageMutationActive() || packagingItemsState.catalogSaving === 'saving', action: 'assign-packaging-category', searchAction: 'search-packaging-category' })}${catalogTagPicker({ itemId: item.id, selectedIds: draft.catalogTagIds, tags: packagingItemsState.catalogTags, state: packagingCatalogControls, disabled: packagingPageMutationActive() || packagingItemsState.catalogSaving === 'saving', toggleAction: 'toggle-packaging-tag', itemDataName: 'packaging-item-id', searchAction: 'search-packaging-tags', showMoreAction: 'toggle-packaging-tags' })}</div>${draftNotice}<div class="actions"><button class="primary-action" type="button" data-action="apply-packaging-assignment" ${packagingPageMutationActive() || !isDirty || packagingItemsState.catalogSaving === 'saving' ? 'disabled' : ''}>${packagingItemsState.catalogSaving === 'saving' ? 'Сохраняем…' : 'Применить изменения'}</button><button class="secondary-action" type="button" data-action="reset-packaging-assignment" ${packagingPageMutationActive() || !isDirty || packagingItemsState.catalogSaving === 'saving' ? 'disabled' : ''}>Сбросить</button></div>${createControls}<p class="next-step">Группа и метки изменяются как черновик. Нажмите «Применить изменения», чтобы сохранить их.</p></section>`;
}

function packagingCatalogCreateControls() {
  const categoryDisabled = packagingPageMutationActive() || packagingItemsState.catalogCreating === 'category' || packagingItemsState.catalogSaving === 'saving';
  const tagDisabled = packagingPageMutationActive() || packagingItemsState.catalogCreating === 'tag' || packagingItemsState.catalogSaving === 'saving';
  return `<div class="catalog-create-grid"><form data-form="packaging-catalog-category" class="catalog-create-form"><h3>Добавить группу</h3><label>Название группы<input name="name" required maxlength="160" placeholder="Например, Баночки" ${categoryDisabled ? 'disabled' : ''} /></label><button class="secondary-action" type="submit" ${categoryDisabled ? 'disabled' : ''}>${packagingItemsState.catalogCreating === 'category' ? 'Создаём…' : 'Создать группу'}</button></form><form data-form="packaging-catalog-tag" class="catalog-create-form"><h3>Добавить метку</h3><label>Название метки<input name="name" required maxlength="160" placeholder="Например, Для кремов" ${tagDisabled ? 'disabled' : ''} /></label><button class="secondary-action" type="submit" ${tagDisabled ? 'disabled' : ''}>${packagingItemsState.catalogCreating === 'tag' ? 'Создаём…' : 'Создать метку'}</button></form></div>`;
}

function packagingCatalogToolbar(resultCount: number) {
  const f = packagingItemsState.filters;
  const categoryOptionsHtml = [`<option value="" ${f.categoryId === '' ? 'selected' : ''}>Все группы</option>`, `<option value="none" ${f.categoryId === 'none' ? 'selected' : ''}>Без группы</option>`, ...packagingItemsState.catalogCategories.map((category) => `<option value="${category.id}" ${f.categoryId === category.id ? 'selected' : ''}>${escapeHtml(category.name)}</option>`)].join('');
  const availableTags = packagingItemsState.catalogTags.filter((tag) => !f.tagIds.includes(tag.id));
  const activeTagChips = f.tagIds.map((id) => packagingItemsState.catalogTags.find((tag) => tag.id === id)).filter((tag): tag is CatalogTag => Boolean(tag)).map((tag) => `<span class="tag-chip selected">${escapeHtml(tag.name)} <button type="button" data-action="remove-packaging-tag-filter" ${packagingPageMutationActive() ? 'disabled' : ''} data-id="${tag.id}" aria-label="Убрать метку ${escapeHtml(tag.name)}">×</button></span>`).join('');
  const activeFilters = packagingActiveFilterChips();
  return `<section class="card data-card catalog-browser"><p class="card-kicker">Каталог тары</p><h2>Найти тару</h2><div class="catalog-toolbar"><label class="full-span">Поиск<input type="search" data-action="filter-packaging-search" ${packagingPageMutationActive() ? 'disabled' : ''} value="${escapeHtml(f.search)}" placeholder="Название, поставщик, заметки, материал или тип тары" /></label><label>Группа<select data-action="filter-packaging-category" ${packagingPageMutationActive() ? 'disabled' : ''}>${categoryOptionsHtml}</select></label><label>Метки<select data-action="add-packaging-tag-filter" ${packagingPageMutationActive() ? 'disabled' : ''}><option value="">Все метки</option>${availableTags.map((tag) => `<option value="${tag.id}">${escapeHtml(tag.name)}</option>`).join('')}</select></label><label>Тип тары<select data-action="filter-packaging-kind" ${packagingPageMutationActive() ? 'disabled' : ''}><option value="" ${f.systemType === '' ? 'selected' : ''}>Все типы</option>${packagingKindValues().map((value) => `<option value="${value}" ${f.systemType === value ? 'selected' : ''}>${packagingKindLabel(value)}</option>`).join('')}</select></label><label>Статус<select data-action="filter-packaging-status" ${packagingPageMutationActive() ? 'disabled' : ''}><option value="active" ${f.status === 'active' ? 'selected' : ''}>Активные</option><option value="archived" ${f.status === 'archived' ? 'selected' : ''}>Архив</option><option value="all" ${f.status === 'all' ? 'selected' : ''}>Все</option></select></label></div>${activeTagChips ? `<div class="active-filter-row"><strong>Метки:</strong>${activeTagChips}</div>` : ''}${activeFilters ? `<div class="active-filter-row"><strong>Активные фильтры:</strong>${activeFilters}</div>` : ''}<div class="catalog-summary"><span>Показана тара: ${resultCount} из ${packagingItemsState.items.length}</span><button class="secondary-action compact" type="button" data-action="reset-packaging-filters" ${packagingPageMutationActive() ? 'disabled' : ''}>Сбросить фильтры</button></div></section>`;
}

function packagingItemsList(items: PackagingItem[]) {
  if (packagingItemsState.items.length === 0) return `<section class="card empty-card"><h2>Тара пока не добавлена</h2><p>Создайте первую баночку, флакон или этикетку.</p><p class="next-step">Следующее действие: нажмите «Создать тару», заполните форму и сохраните карточку.</p></section>`;
  if (items.length === 0) return `<section class="card empty-card"><h2>По этим фильтрам тара не найдена.</h2><p>Попробуйте убрать часть условий поиска или вернуться к полному каталогу.</p><button class="secondary-action" type="button" data-action="reset-packaging-filters" ${packagingPageMutationActive() ? 'disabled' : ''}>Сбросить фильтры</button></section>`;
  return `<section class="card data-card"><p class="card-kicker">Найденная тара</p><h2>Тара и расходники</h2><div class="table-wrap"><table class="compact-catalog-table"><thead><tr><th>Название</th><th>Тип</th><th>Ед. / объем</th><th>Группа</th><th>Метки</th><th>Статус</th><th>Действия</th></tr></thead><tbody>${items.map((item) => { const isEditing = packagingItemsState.formMode === 'edit' && packagingItemsState.form.id === item.id; return `<tr class="${isEditing ? 'catalog-row-selected' : ''}"><td><strong>${escapeHtml(item.name)}</strong>${isEditing ? '<small><span class="pill warning">Редактируется</span></small>' : ''}</td><td>${packagingKindLabel(item.kind)}</td><td>${unitLabel(item.unit)}${item.capacity_value && item.capacity_unit ? `<small>${packagingItemCapacityLabel(item)}</small>` : ''}</td><td>${escapeHtml(packagingCatalogCategoryLabel(item))}</td><td>${packagingTagChips(item)}</td><td><span class="pill ${item.is_active ? 'success' : 'muted'}">${item.is_active ? 'Активна' : 'Архив'}</span></td><td><div class="row-actions"><button class="secondary-action compact" type="button" data-action="edit-packaging-item" data-id="${item.id}" ${packagingPageMutationActive() ? 'disabled' : ''}>Изменить</button>${item.is_active ? `<button class="secondary-action compact danger-action" type="button" data-action="deactivate-packaging-item" data-id="${item.id}" ${packagingPageMutationActive() ? 'disabled' : ''}>Деактивировать</button>` : ''}</div></td></tr>`; }).join('')}</tbody></table></div><p class="next-step">Длинные заметки, поставщик, материал и цена остаются в форме редактирования, чтобы список был компактным.</p></section>`;
}

function ingredientLotsPage() {
  if (ingredientLotsStatus === 'idle' || ingredientLotsStatus === 'loading') return `<section class="card"><p class="card-kicker">Приходы и партии</p><h2>Загружаем приходы и партии…</h2><p>Загружаем партии компонентов.</p></section>`;
  if (ingredientLotsStatus === 'error') return `<section class="card error-card"><p class="card-kicker">Приходы и партии</p><h2>Не удалось загрузить приходы и партии</h2><p>${ingredientLotsError || 'Не удалось получить данные о партиях.'}</p><p class="next-step">Проверьте, что приложение запущено полностью, и попробуйте обновить раздел.</p><button class="primary-action" type="button" data-action="reload-ingredient-lots">Повторить загрузку</button></section>`;
  return `<div class="catalog-layout"><section class="card catalog-intro"><div><p class="card-kicker">Приходы и партии</p><h2>Приходы и партии сырья</h2><p>Здесь хранится паспорт партии: компонент, поставщик, срок годности, цена и единица учета. Остаток не редактируется здесь и считается отдельными движениями сырья.</p></div><button class="secondary-action" type="button" data-action="new-ingredient-lot" ${ingredientLotSubmitting ? 'disabled' : ''}>Очистить форму</button></section>${ingredientLotsMessage ? `<p class="page-message">${ingredientLotsMessage}</p>` : ''}${ingredientLotsRefreshWarning ? `<p class="page-message warning-message">${ingredientLotsRefreshWarning}</p>` : ''}${ingredientLotsError ? `<p class="page-message error-message">${ingredientLotsError}</p>` : ''}${ingredientLotForm()}${ingredientLotList()}</div>`;
}

function ingredientLotForm() {
  const form = ingredientLotsState.form;
  const isEdit = ingredientLotsState.formMode === 'edit';
  const hasIngredients = ingredientLotsState.ingredients.length > 0;
  return `<section class="card form-card"><p class="card-kicker">${isEdit ? 'Редактирование' : 'Создание'}</p><h2>${isEdit ? 'Изменить партию' : 'Создать партию компонента'}</h2><p class="next-step">Количество партии добавляется отдельным движением сырья. Здесь хранится информация о партии: поставщик, срок годности, цена и единица учета.</p><form data-form="ingredient-lot" class="ingredient-form" novalidate>${validationSummary(ingredientLotValidation, 'Проверьте форму партии')}<div class="form-grid">${ingredientLotField(`Компонент<select name="ingredient_id" required ${hasIngredients || ingredientLotSubmitting ? '' : 'disabled'} ${ingredientLotSubmitting ? 'disabled' : ''}${ingredientLotFieldAttrs('ingredient_id')}><option value="">Выберите компонент</option>${ingredientLotsState.ingredients.map((item) => `<option value="${item.id}" ${String(item.id) === form.ingredient_id ? 'selected' : ''}>${escapeHtml(item.name)}</option>`).join('')}</select>`, 'ingredient_id')} ${ingredientLotField(`Номер партии<input name="lot_code" maxlength="120" value="${escapeHtml(form.lot_code)}" placeholder="Например, LOT-2026-01" ${ingredientLotSubmitting ? 'disabled' : ''}${ingredientLotFieldAttrs('lot_code')} />`, 'lot_code')} ${ingredientLotField(`Поставщик<input name="supplier_name" maxlength="160" value="${escapeHtml(form.supplier_name)}" placeholder="Необязательно" ${ingredientLotSubmitting ? 'disabled' : ''}${ingredientLotFieldAttrs('supplier_name')} />`, 'supplier_name')} ${ingredientLotField(`Единица измерения<select name="unit" ${ingredientLotSubmitting ? 'disabled' : ''}${ingredientLotFieldAttrs('unit')}>${lotUnitOptions(form.unit)}</select>`, 'unit')} ${ingredientLotField(`Цена за единицу<input name="unit_cost" inputmode="decimal" value="${escapeHtml(form.unit_cost)}" placeholder="Например, 12.50" ${ingredientLotSubmitting ? 'disabled' : ''}${ingredientLotFieldAttrs('unit_cost')} />`, 'unit_cost')} ${ingredientLotField(`Общая стоимость<input name="total_cost" inputmode="decimal" value="${escapeHtml(form.total_cost)}" placeholder="Необязательно" ${ingredientLotSubmitting ? 'disabled' : ''}${ingredientLotFieldAttrs('total_cost')} />`, 'total_cost')} ${ingredientLotField(`Плотность, г/мл<input name="density_g_per_ml" inputmode="decimal" value="${escapeHtml(form.density_g_per_ml)}" placeholder="Например, 0.950" ${ingredientLotSubmitting ? 'disabled' : ''}${ingredientLotFieldAttrs('density_g_per_ml')} />`, 'density_g_per_ml')} ${ingredientLotField(`Дата покупки<input name="purchased_at" type="date" value="${escapeHtml(form.purchased_at)}" ${ingredientLotSubmitting ? 'disabled' : ''}${ingredientLotFieldAttrs('purchased_at')} />`, 'purchased_at')} ${ingredientLotField(`Срок годности<input name="expires_at" type="date" value="${escapeHtml(form.expires_at)}" ${ingredientLotSubmitting ? 'disabled' : ''}${ingredientLotFieldAttrs('expires_at')} />`, 'expires_at')} ${ingredientLotField(`Заметки<textarea name="notes" rows="3" maxlength="1200" placeholder="Короткие рабочие заметки о партии" ${ingredientLotSubmitting ? 'disabled' : ''}${ingredientLotFieldAttrs('notes')}>${escapeHtml(form.notes)}</textarea>`, 'notes', true)}</div><div class="actions"><button class="primary-action" type="submit" ${hasIngredients && !ingredientLotSubmitting ? '' : 'disabled'}>${ingredientLotSubmitting ? 'Сохраняем…' : isEdit ? 'Сохранить изменения' : 'Создать партию'}</button>${isEdit ? `<button class="secondary-action" type="button" data-action="new-ingredient-lot" ${ingredientLotSubmitting ? 'disabled' : ''}>Отменить редактирование</button>` : ''}</div>${hasIngredients ? '' : '<p class="next-step">Сначала создайте активный компонент в разделе «Компоненты», затем вернитесь к партиям.</p>'}</form></section>`;
}

function ingredientLotList() {
  if (ingredientLotsState.lots.length === 0) return `<section class="card empty-card"><h2>Пока нет партий компонентов</h2><p>Создайте партию, чтобы указать поставщика, срок годности и цену закупки.</p><p class="next-step">Остаток считается по движениям склада. Чтобы добавить количество, используйте движение склада — это будет отдельный шаг.</p></section>`;
  return `<section class="card data-card"><p class="card-kicker">Список</p><h2>Приходы и партии</h2><div class="table-wrap"><table><thead><tr><th>Компонент</th><th>Партия</th><th>Поставщик</th><th>Ед. учета</th><th>Цена за единицу</th><th>Плотность</th><th>Дата покупки</th><th>Срок годности</th><th>Статус</th><th>Действия</th></tr></thead><tbody>${ingredientLotsState.lots.map((lot) => `<tr><td><strong>${escapeHtml(lotIngredientName(lot.ingredient_id))}</strong></td><td>${escapeHtml(lot.lot_code || 'Без номера')}<small>${escapeHtml(lot.notes || '')}</small></td><td>${escapeHtml(lot.supplier_name || 'Не указан')}</td><td>${unitLabel(lot.unit)}</td><td>${lot.unit_cost ? escapeHtml(lot.unit_cost) : 'Не указана'}</td><td>${lot.density_g_per_ml ? `${escapeHtml(lot.density_g_per_ml)} г/мл` : 'Не указана'}</td><td>${formatDate(lot.purchased_at)}</td><td>${formatDate(lot.expires_at)}</td><td><span class="pill ${lotStatusClass(lot)}">${lotStatusLabel(lot)}</span></td><td><div class="row-actions"><button class="secondary-action compact" type="button" data-action="edit-ingredient-lot" data-id="${lot.id}" ${ingredientLotSubmitting ? 'disabled' : ''}>Изменить</button>${lot.is_active ? `<button class="secondary-action compact danger-action" type="button" data-action="deactivate-ingredient-lot" data-id="${lot.id}" ${ingredientLotSubmitting ? 'disabled' : ''}>Деактивировать</button>` : ''}</div></td></tr>`).join('')}</tbody></table></div><p class="next-step">Остаток партии не редактируется в этой таблице: он будет считаться по движениям склада.</p></section>`;
}


function stockMovementsPage() {
  if (stockMovementsStatus === 'idle' || stockMovementsStatus === 'loading') return `<section class="card"><p class="card-kicker">Движения сырья</p><h2>Загружаем движения…</h2><p>Загружаем партии компонентов и историю движений.</p></section>`;
  if (stockMovementsStatus === 'error') return `<section class="card error-card"><p class="card-kicker">Движения сырья</p><h2>Не удалось загрузить движения сырья</h2><p>${stockMovementsError || 'Не удалось получить данные о движениях склада.'}</p><p class="next-step">Проверьте, что приложение запущено полностью, и попробуйте обновить раздел.</p><button class="primary-action" type="button" data-action="reload-stock-movements">Повторить загрузку</button></section>`;
  if (stockMovementsState.lots.length === 0) return `<div class="catalog-layout"><section class="card catalog-intro"><div><p class="card-kicker">Движения сырья</p><h2>История движений компонентов</h2><p>Остаток партии считается по движениям. Старые движения не редактируются, чтобы история склада оставалась честной.</p></div><button class="secondary-action" type="button" data-action="reload-stock-movements" ${stockMovementSubmitting ? 'disabled' : ''}>Обновить</button></section><section class="card empty-card"><h2>Пока нет партий для движений</h2><p>Сначала создайте компонент и партию. После этого можно будет добавить приход или списание.</p><p class="next-step">Текущий остаток нельзя ввести вручную: он появится после первого движения сырья.</p></section></div>`;
  return `<div class="catalog-layout"><section class="card catalog-intro"><div><p class="card-kicker">Движения сырья</p><h2>Движения сырья</h2><p>Остаток партии считается по движениям. Старые движения не редактируются, чтобы история склада оставалась честной.</p></div><button class="secondary-action" type="button" data-action="reload-stock-movements" ${stockMovementSubmitting ? 'disabled' : ''}>Обновить</button></section>${stockMovementsMessage ? `<p class="page-message">${stockMovementsMessage}</p>` : ''}${stockMovementsRefreshWarning ? `<p class="page-message warning-message">${stockMovementsRefreshWarning}</p>` : ''}${stockMovementsError ? `<p class="page-message error-message">${stockMovementsError}</p>` : ''}${stockLotSelector()}${stockMovementForm()}${stockMovementHistory()}</div>`;
}

function stockLotSelector() {
  const selected = stockMovementsState.selectedLotId;
  return `<section class="card form-card"><p class="card-kicker">Партия</p><h2>Выберите партию компонента</h2><div class="form-grid"><label class="full-span">Партия<select data-action="select-stock-lot" ${stockMovementSubmitting ? 'disabled' : ''}><option value="">Выберите партию</option>${stockMovementsState.lots.map((lot) => `<option value="${lot.id}" ${lot.id === selected ? 'selected' : ''}>${escapeHtml(stockLotLabel(lot))}</option>`).join('')}</select></label></div>${stockMovementsState.detailStatus === 'loading' ? '<p class="next-step">Загружаем текущий остаток и историю выбранной партии…</p>' : ''}${stockBalanceCard()}</section>`;
}

function stockBalanceCard() {
  if (!stockMovementsState.selectedLotId) return `<p class="next-step">Выберите партию, чтобы увидеть остаток, рассчитанный по движениям склада, и историю операций.</p>`;
  if (stockMovementsState.detailStatus === 'error') return `<p class="next-step error-message">Не удалось получить остаток или историю партии. Попробуйте обновить раздел.</p>`;
  if (!stockMovementsState.balance) return '';
  const lot = selectedStockLot();
  return `<div class="balance-card" aria-label="Текущий остаток"><span>Текущий остаток</span><strong>${escapeHtml(stockMovementsState.balance.quantity)} ${unitLabel(lot?.unit ?? '')}</strong><small>Остаток считается по истории движений.</small></div>`;
}

function stockMovementForm() {
  const lot = selectedStockLot();
  if (!lot) return '';
  const form = stockMovementsState.form;
  return `<section class="card form-card"><p class="card-kicker">Новое движение</p><h2>Добавить движение по выбранной партии</h2><p class="next-step">Приложение не позволит списать или вернуть больше, чем доступно в выбранной партии. История движений не редактируется и не удаляется.</p><form data-form="stock-movement" class="ingredient-form" novalidate>${validationSummary(stockMovementValidation, 'Проверьте движение склада')}<div class="form-grid">${stockMovementField(`Партия<input name="ingredient_lot_id" value="${escapeHtml(stockLotLabel(lot))}" readonly${stockMovementFieldAttrs('ingredient_lot_id')} />`, 'ingredient_lot_id')}${stockMovementField(`Тип движения<select name="movement_type" ${stockMovementSubmitting ? 'disabled' : ''}${stockMovementFieldAttrs('movement_type')}>${movementTypeOptions(form.movement_type)}</select>`, 'movement_type')}${stockMovementField(`Количество<input name="quantity" required inputmode="decimal" value="${escapeHtml(form.quantity)}" placeholder="Например, 100 или 12.500" ${stockMovementSubmitting ? 'disabled' : ''}${stockMovementFieldAttrs('quantity')} />`, 'quantity')}${stockMovementField(`Единица<input name="unit" value="${unitLabel(lot.unit)}" readonly${stockMovementFieldAttrs('unit')} />`, 'unit')}${stockMovementField(`Дата движения<input name="occurred_at" type="datetime-local" value="${escapeHtml(form.occurred_at)}" ${stockMovementSubmitting ? 'disabled' : ''}${stockMovementFieldAttrs('occurred_at')} />`, 'occurred_at')}${stockMovementField(`Источник<select name="source" ${stockMovementSubmitting ? 'disabled' : ''}${stockMovementFieldAttrs('source')}><option value="manual" ${form.source === 'manual' ? 'selected' : ''}>Вручную</option><option value="import" ${form.source === 'import' ? 'selected' : ''}>Импорт</option><option value="system" ${form.source === 'system' ? 'selected' : ''}>Система</option></select>`, 'source')}${stockMovementField(`Причина<input name="reason" maxlength="240" value="${escapeHtml(form.reason)}" placeholder="Например, закупка, списание просрочки" ${stockMovementSubmitting ? 'disabled' : ''}${stockMovementFieldAttrs('reason')} />`, 'reason', true)}${stockMovementField(`Заметки<textarea name="note" rows="3" maxlength="1200" placeholder="Необязательно" ${stockMovementSubmitting ? 'disabled' : ''}${stockMovementFieldAttrs('note')}>${escapeHtml(form.note)}</textarea>`, 'note', true)}</div><div class="actions"><button class="primary-action" type="submit" ${stockMovementSubmitting ? 'disabled' : ''}>${stockMovementSubmitting ? 'Создаём…' : 'Создать движение'}</button></div></form></section>`;
}

function stockMovementHistory() {
  if (!stockMovementsState.selectedLotId) return '';
  if (stockMovementsState.movements.length === 0) return `<section class="card empty-card"><h2>Движений по партии пока нет</h2><p>Создайте приход, чтобы зафиксировать начальный остаток партии. Текущий остаток останется расчетным.</p></section>`;
  return `<section class="card data-card"><p class="card-kicker">История</p><h2>Движения выбранной партии</h2><div class="table-wrap"><table><thead><tr><th>Дата</th><th>Тип движения</th><th>Количество</th><th>Ед.</th><th>Причина</th><th>Источник</th><th>Заметки</th></tr></thead><tbody>${stockMovementsState.movements.map((movement) => `<tr><td>${formatDateTime(movement.occurred_at)}</td><td>${movementTypeLabel(movement.movement_type)}</td><td>${escapeHtml(movement.quantity)}</td><td>${unitLabel(movement.unit)}</td><td>${escapeHtml(movement.reason || 'Не указана')}</td><td>${sourceLabel(movement.source)}</td><td>${escapeHtml(movement.note || 'Без заметок')}</td></tr>`).join('')}</tbody></table></div><p class="next-step">Это журнал склада: старые движения не редактируются и не удаляются.</p></section>`;
}

function inventoryPage() {
  if (inventoryStatus === 'idle' || inventoryStatus === 'loading') return `<section class="card"><p class="card-kicker">Склад</p><h2>Загружаем остатки…</h2><p>Загружаем сводку по партиям компонентов и таре.</p></section>`;
  if (inventoryStatus === 'error') return `<section class="card error-card"><p class="card-kicker">Склад</p><h2>Не удалось загрузить склад</h2><p>${inventoryError || 'Данные временно недоступны.'}</p><p class="next-step">Проверьте, что приложение запущено полностью, и попробуйте обновить раздел.</p><button class="primary-action" type="button" data-action="reload-inventory">Повторить загрузку</button></section>`;
  const overview = inventoryState.overview;
  return `<div class="inventory-layout"><section class="card inventory-intro"><p class="card-kicker">Склад</p><h2>Обзор запасов</h2><p>Здесь показаны только текущие остатки, которые уже посчитаны приложением. На этой странице нет действий изменения склада.</p></section>${overview ? overviewCards(overview) : emptyCard('Сводка пока пуста', 'Когда появятся партии компонентов или тара, здесь будет краткая сводка.')} ${ingredientLotsTable(inventoryState.ingredientLots)} ${packagingTable(inventoryState.packagingItems)}</div>`;
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
  if (onboardingStatus === 'unavailable') return `<section class="card onboarding-card"><p class="card-kicker">Первый запуск</p><h2>Список первых шагов временно недоступен</h2><p>Список первых шагов временно недоступен. Основные разделы приложения продолжают работать.</p><p class="next-step">Проверьте, что приложение запущено полностью, и обновите главную страницу.</p></section>`;
  const currentStep = onboardingState?.current_step ?? 'welcome';
  const started = onboardingState?.has_started ?? false;
  const steps = onboardingState?.available_steps ?? Object.keys(stepLabels);
  const doneCount = steps.filter((step) => onboardingState?.completed_steps.includes(step)).length;
  if (onboardingState?.is_completed) return `<section class="card onboarding-card"><p class="card-kicker">Первичная настройка</p><h2>Базовая настройка завершена</h2><p>Базовая настройка завершена. Вы можете вернуться к списку первых шагов в любой момент, если хотите проверить путь ещё раз.</p><p class="next-step">Список первых шагов не меняет рецепты, склад, заказы и производство. Он только отмечает ваш прогресс.</p><div class="actions"><button class="secondary-action" type="button" data-action="reset-onboarding">Проверить путь ещё раз</button></div></section>`;
  return `<section class="card onboarding-card"><p class="card-kicker">Первый запуск</p><h2>Настройте мастерскую по шагам</h2><p>Пройдите короткий путь: подготовьте склад, рецепты, клиентов, заказ, производство и защиту данных. Список первых шагов ничего не создаёт сам — он только помогает не пропустить важные разделы.</p><div class="onboarding-note"><strong>Безопасно:</strong> список первых шагов не меняет рецепты, склад, заказы и производство. Он только отмечает ваш прогресс и открывает нужные разделы.</div><p class="onboarding-progress">Выполнено ${doneCount} из ${steps.length}</p>${onboardingMessage ? `<p class="inline-message">${onboardingMessage}</p>` : ''}<ol class="checklist">${steps.map((step) => checklistItem(step, currentStep)).join('')}</ol><div class="actions">${started ? `<button class="primary-action" type="button" data-action="complete-step" data-step="${currentStep}">Отметить текущий шаг</button>` : '<button class="primary-action" type="button" data-action="start-onboarding">Начать настройку</button>'}<button class="secondary-action" type="button" data-action="skip-onboarding">Пропустить пока</button></div></section>`;
}
function checklistItem(step: string, currentStep: string) { const isDone = onboardingState?.completed_steps.includes(step); const isCurrent = step === currentStep && !isDone; const marker = isDone ? '✓' : isCurrent ? '•' : '○'; const sections = onboardingStepUi[step]?.sections ?? []; const links = sections.map((section) => `<button class="secondary-action compact" type="button" data-action="navigate-onboarding-step" data-section="${section}">Открыть ${labelForSection(section).toLowerCase()}</button>`).join(''); return `<li class="${isDone ? 'done' : ''} ${isCurrent ? 'current' : ''}"><span>${marker}</span><div><strong>${stepLabels[step] ?? step}</strong><small>${stepHint(step)}</small>${links ? `<div class="checklist-links">${links}</div>` : ''}</div></li>`; }
function stepHint(step: string) { return onboardingStepUi[step]?.hint ?? 'Шаг будет уточнен позже.'; }


function reportDocumentsPage() {
  const isLoading = reportDocumentsUiState.status === 'loading';
  return `<div class="page-grid backup-page report-documents-page"><section class="card data-card dashboard-hero"><div><p class="card-kicker">Документы отчётов</p><h2>Документы отчётов</h2><p>Отчёты показывают текущую сводку на экране. Здесь можно создать отдельный файл с этой сводкой для хранения, печати или отправки.</p><p class="next-step">Документ создаётся только после явного нажатия. Он основан на текущих данных отчётов и не меняет рецепты, клиентов, заказы, склад или производство.</p></div><div class="actions"><button class="secondary-action" type="button" data-action="reload-report-documents" ${isLoading ? 'disabled' : ''}>${isLoading ? 'Обновляем…' : 'Обновить список'}</button></div></section>${reportDocumentsUiState.error ? feedbackMessage('error', reportDocumentsUiState.error) : ''}${reportDocumentsUiState.message ? feedbackMessage('success', reportDocumentsUiState.message) : ''}${reportDocumentsUiState.status === 'error' && !reportDocumentsUiState.documentStatus ? reportDocumentsLoadErrorCard() : `${reportDocumentsStatusCard()}${reportDocumentsCreateCard()}${reportDocumentsLastCreatedCard()}${reportDocumentsListCard()}${reportDocumentsBoundariesCard()}`}</div>`;
}
function reportDocumentsLoadErrorCard() { return `<section class="card error-card"><h2>Документы недоступны</h2><p>Не удалось загрузить документы отчётов. Проверьте, что приложение запущено, и попробуйте снова.</p><div class="actions"><button class="secondary-action" type="button" data-action="reload-report-documents">Повторить</button></div></section>`; }
function reportDocumentsStatusCard() { const s = reportDocumentsUiState.documentStatus; if (reportDocumentsUiState.status === 'loading' && !s) return '<section class="card"><p>Загружаем сведения о документах отчётов…</p></section>'; if (!s) return ''; return `<section class="overview-grid"><div class="metric-card"><span>Доступные форматы</span><strong>${escapeHtml(s.available_formats.map(reportDocumentFormatLabel).join(', ') || 'Нет')}</strong></div><div class="metric-card"><span>Тип документа</span><strong>${s.available_document_types.includes('workshop_overview') ? 'Сводка мастерской' : escapeHtml(s.available_document_types.join(', ') || 'Нет')}</strong></div><div class="metric-card"><span>Создано документов</span><strong>${s.documents_count}</strong></div><div class="metric-card"><span>Можно создать</span><strong>${s.can_create ? 'Да' : 'Нет'}</strong></div><div class="metric-card wide"><span>Состояние раздела</span><strong>${escapeHtml(s.message || 'Нет сообщения')}</strong><small class="path-text">Папка с документами: ${escapeHtml(s.documents_dir)}</small></div></section>`; }
function reportDocumentsCreateCard() { const disabled = reportDocumentsUiState.actionStatus === 'creating' || reportDocumentsUiState.status === 'loading' || !reportDocumentsUiState.documentStatus?.can_create; const formats = reportDocumentsUiState.documentStatus?.available_formats ?? ['markdown']; const canPdf = formats.includes('pdf'); const pdfUnavailable = !canPdf ? '<p class="next-step">PDF сейчас недоступен на этом устройстве. Можно создать Markdown-документ.</p>' : ''; return `<section class="card data-card"><p class="card-kicker">Явное действие</p><h2>Создать сводку мастерской</h2><p>Файл будет создан из текущей сводки мастерской: склад, заказы, производство, алерты, закупки и базовые финансы.</p>${feedbackMessage('neutral', 'Markdown — текстовый документ, который удобно открыть и отредактировать. PDF — готовый документ для просмотра, печати или отправки.')}<form class="form-grid" data-form="report-document-create" aria-busy="${reportDocumentsUiState.actionStatus === 'creating' ? 'true' : 'false'}"><label>Причина / заметка<input name="reason" maxlength="80" value="${escapeHtml(reportDocumentsUiState.reason)}" data-action="report-document-reason" placeholder="Например: еженедельная проверка" /></label><div class="actions"><button class="secondary-action" type="submit" data-format="markdown" ${disabled ? 'disabled' : ''}>${reportDocumentsUiState.actionStatus === 'creating' ? 'Создаём…' : 'Создать Markdown'}</button>${canPdf ? `<button class="primary-action" type="submit" data-format="pdf" ${disabled ? 'disabled' : ''}>${reportDocumentsUiState.actionStatus === 'creating' ? 'Создаём…' : 'Создать PDF'}</button>` : ''}</div></form>${pdfUnavailable}<p class="next-step">Документ создаётся только после явного нажатия. Создание документа не изменяет данные мастерской.</p></section>`; }
function reportDocumentsLastCreatedCard() { const d = reportDocumentsUiState.lastCreatedDocument; if (!d) return ''; return `<section class="card data-card"><p class="card-kicker">Последний результат</p><h2>Документ создан</h2><p>Файл: <strong>${escapeHtml(d.filename)}</strong></p><p class="next-step">Документ создан. Его можно открыть или скачать из списка ниже.</p></section>`; }
function reportDocumentsListCard() { const docs = reportDocumentsUiState.documents; if (!docs.length) return `<section class="card empty-card"><h2>Созданные документы</h2><p>Документы отчётов пока не создавались. Создайте Markdown или PDF-файл со сводкой мастерской.</p><p>Создайте сводку вручную, когда нужен файл для просмотра или передачи.</p><div class="actions"><button class="secondary-action" type="button" data-action="navigate-report-documents-related" data-section="Отчеты">Открыть отчёты</button></div></section>`; return `<section class="card data-card"><div class="section-heading"><div><p class="card-kicker">Локальные файлы</p><h2>Созданные документы</h2></div><span class="pill info">${docs.length}</span></div><div class="backup-list">${docs.map(reportDocumentItem).join('')}</div><p class="next-step">Файлы можно открыть или скачать с помощью кнопок в списке. Имена файлов не меняются.</p><div class="actions"><button class="secondary-action" type="button" data-action="navigate-report-documents-related" data-section="Отчеты">Открыть отчёты</button></div></section>`; }
function reportDocumentItem(d: ReportDocumentMetadata) { return `<article class="recipe-line backup-item"><div class="section-heading"><div><h3>${escapeHtml(d.title || 'Сводка мастерской')}</h3><p><span class="pill info">${reportDocumentFormatLabel(d.format)}</span> <span class="pill muted">${formatFileSize(d.size_bytes)}</span></p></div><small>${formatDateTime(d.created_at)}</small></div><dl class="metadata-list"><div><dt>Файл</dt><dd>${escapeHtml(d.filename)}</dd></div><div><dt>Формат</dt><dd>${reportDocumentFormatLabel(d.format)}</dd></div><div><dt>Создан</dt><dd>${formatDateTime(d.created_at)}</dd></div><div><dt>Размер</dt><dd>${formatFileSize(d.size_bytes)}</dd></div><div><dt>Предупреждений</dt><dd>${d.warnings_count}</dd></div><div><dt>Основан на сводке</dt><dd>${escapeHtml(d.source)}${d.source_generated_at ? ` · ${formatDateTime(d.source_generated_at)}` : ''}</dd></div></dl>${reportDocumentActions(d)}</article>`; }
function reportDocumentActions(d: ReportDocumentMetadata) { const attachmentUrl = reportDocumentDownloadUrl(d.id, 'attachment'); if (d.format === 'pdf') return `<div class="actions document-actions"><a class="secondary-action compact" href="${reportDocumentDownloadUrl(d.id, 'inline')}" target="_blank" rel="noopener noreferrer">Открыть PDF</a><a class="primary-action compact" href="${attachmentUrl}">Скачать PDF</a></div>`; if (d.format === 'markdown') return `<div class="actions document-actions"><a class="secondary-action compact" href="${attachmentUrl}">Скачать Markdown</a></div>`; return ''; }
function reportDocumentDownloadUrl(documentId: string, disposition: 'attachment' | 'inline') { return `/api/report-documents/${encodeURIComponent(documentId)}/download?disposition=${disposition}`; }
function reportDocumentFormatLabel(format: string) { return format === 'markdown' ? 'Markdown' : format === 'pdf' ? 'PDF' : escapeHtml(format); }
function reportDocumentsBoundariesCard() { return `<section class="card data-card"><p class="card-kicker">Честные границы</p><h2>Что важно знать</h2><ul class="checklist compact-list"><li>Документ создаётся только после явного нажатия.</li><li>Создание документа не изменяет рабочие данные.</li><li>Файл хранится локально на этом MacBook.</li><li>Доступны только форматы, которые показаны на экране.</li><li>Это не бухгалтерский и не налоговый документ.</li><li>Налоговые ставки не придумываются.</li></ul></section>`; }

function reportsPage() {
  const generatedAt = reportsUiState.overview?.generated_at ?? reportsUiState.inventory?.generated_at ?? reportsUiState.orders?.generated_at ?? reportsUiState.production?.generated_at ?? reportsUiState.finance?.generated_at ?? null;
  const body = reportsUiState.status === 'loading' && !reportsUiState.overview ? reportsLoadingCard() : reportsUiState.status === 'error' && !reportsUiState.overview ? reportsErrorCard() : reportsContent();
  return `<div class="reports-layout"><section class="card data-card reports-hero"><div class="section-heading"><div><p class="card-kicker">Отчёты</p><h2>Отчёты</h2><p>Здесь собраны сводные показатели мастерской по складу, заказам, производству и финансам.</p><p class="next-step">Просмотр и обновление отчётов не изменяют рабочие данные.</p><div class="actions"><button class="secondary-action compact" type="button" data-action="navigate-report-related" data-section="Документы отчетов">Открыть документы отчётов</button></div>${generatedAt ? `<p class="muted-text">Сформировано: ${formatDateTime(generatedAt)}</p>` : ''}</div><button class="primary-action" type="button" data-action="reload-reports" ${reportsUiState.status === 'loading' ? 'disabled' : ''}>Обновить отчёты</button></div></section>${reportsUiState.error && reportsUiState.overview ? `<p class="page-message error-message">${escapeHtml(reportsUiState.error)}</p>` : ''}${reportsUiState.message ? `<p class="page-message">${escapeHtml(reportsUiState.message)}</p>` : ''}${body}</div>`;
}
function reportsLoadingCard() { return `<section class="card"><p class="card-kicker">Отчёты</p><h2>Загружаем сводку мастерской…</h2><p>Показываем текущие показатели без изменения рабочих данных.</p></section>`; }
function reportsErrorCard() { return `<section class="card error-card"><p class="card-kicker">Отчёты</p><h2>Не удалось загрузить отчёты</h2><p>${escapeHtml(reportsUiState.error || 'Не удалось загрузить отчёты. Проверьте, что приложение запущено, и попробуйте снова.')}</p><button class="primary-action" type="button" data-action="reload-reports">Повторить</button></section>`; }
function reportsContent() { return `${reportTabs()}${reportEmptyState()}${selectedReportMarkup()}`; }
function reportTabs() { const tabs: Array<[ReportTab,string]> = [['overview','Обзор'],['inventory','Склад'],['orders','Заказы'],['production','Производство'],['finance','Финансы']]; return `<section class="card filter-card"><div class="segmented-control">${tabs.map(([key,label])=>`<button class="secondary-action compact ${reportsUiState.selectedReport===key?'active':''}" type="button" data-action="select-report-tab" data-report="${key}">${label}</button>`).join('')}</div></section>`; }
function reportEmptyState() { const o = reportsUiState.overview; if (!o) return ''; const hasData = o.inventory_summary.total_active_ingredients + o.orders_summary.total_orders + o.production_summary.total_production_batches + o.alerts_summary.open_alerts + o.purchase_summary.open_purchase_suggestions > 0; if (hasData) return ''; return `<section class="card empty-card"><h2>Данных пока мало</h2><p>Данных пока мало. Добавьте компоненты, рецепты, клиентов и заказы или включите демо-данные, чтобы увидеть пример отчётов.</p><div class="actions"><button class="secondary-action compact" type="button" data-action="navigate-report-related" data-section="Демо-данные">Открыть демо-данные</button><button class="secondary-action compact" type="button" data-action="navigate-report-related" data-section="Компоненты">Открыть компоненты</button><button class="secondary-action compact" type="button" data-action="navigate-report-related" data-section="Заказы">Открыть заказы</button></div></section>`; }
function selectedReportMarkup() { if (reportsUiState.selectedReport === 'inventory') return inventoryReportMarkup(); if (reportsUiState.selectedReport === 'orders') return ordersReportMarkup(); if (reportsUiState.selectedReport === 'production') return productionReportMarkup(); if (reportsUiState.selectedReport === 'finance') return financeReportMarkup(); return overviewReportMarkup(); }
function metricCard(label:string, value:string|number|null, hint='') { return `<article class="metric-card"><span>${escapeHtml(label)}</span><strong>${value === null || value === '' ? 'Нет данных' : escapeHtml(String(value))}</strong>${hint ? `<small>${escapeHtml(hint)}</small>` : ''}</article>`; }
function metricGrid(items: Array<[string,string|number|null,string?]>) { return `<div class="overview-grid">${items.map(([label,value,hint])=>metricCard(label,value,hint ?? '')).join('')}</div>`; }
function overviewReportMarkup() { const o=reportsUiState.overview; if(!o) return ''; return `<section class="card data-card"><p class="card-kicker">Обзор</p><h2>Короткая сводка</h2>${metricGrid([['Активные компоненты',o.inventory_summary.total_active_ingredients],['Партии с остатком',o.inventory_summary.ingredient_lots_with_positive_balance],['Открытые заказы',o.orders_summary.active_orders],['Ожидают материалов',o.orders_summary.waiting_for_materials],['Производственных партий',o.production_summary.total_production_batches],['Открытые алерты',o.alerts_summary.open_alerts],['Предложения закупок',o.purchase_summary.open_purchase_suggestions],['Известная выручка',moneyText(o.finance_summary.known_revenue)]])}${reportWarningsMarkup(o.warnings)}</section>`; }
function inventoryReportMarkup() { const r=reportsUiState.inventory; if(!r) return ''; return `<section class="card data-card"><p class="card-kicker">Склад</p><h2>Сводка склада</h2><p class="next-step">Показатели рассчитаны по текущим партиям и движениям. Просмотр сводки не меняет остатки.</p>${metricGrid([['Активные компоненты',r.total_active_ingredients],['Активные партии',r.total_active_ingredient_lots],['Партии с остатком',r.ingredient_lots_with_positive_balance],['Просроченные партии',r.expired_ingredient_lots],['Скоро истекают',r.expiring_soon_ingredient_lots],['Активная тара',r.active_packaging_items],['Тара с остатком',r.packaging_items_with_positive_balance],['Алерты низкого остатка',r.open_low_stock_alerts],['Открытые закупки',r.open_purchase_suggestions]])}${reportWarningsMarkup(r.warnings)}</section>`; }
function ordersReportMarkup() { const r=reportsUiState.orders; if(!r) return ''; return `<section class="card data-card"><p class="card-kicker">Заказы</p><h2>Статусы заказов</h2>${metricGrid([['Всего заказов',r.total_orders],['Активные',r.active_orders],['Новые',r.new_orders],['Ждут материалы',r.waiting_for_materials],['Готовы к производству',r.ready_to_produce],['В работе',r.in_progress],['Произведены',r.produced],['Доставлены',r.delivered],['Отменены',r.cancelled],['В архиве',r.archived],['Без рецепта',r.orders_missing_recipe]])}<div class="actions"><button class="secondary-action compact" type="button" data-action="navigate-report-related" data-section="Заказы">Открыть заказы</button><button class="secondary-action compact" type="button" data-action="navigate-report-related" data-section="Заказы">Проверить готовность</button></div>${reportWarningsMarkup(r.warnings)}</section>`; }
function productionReportMarkup() { const r=reportsUiState.production; if(!r) return ''; return `<section class="card data-card"><p class="card-kicker">Производство</p><h2>Проведенное производство</h2><p class="next-step">Сводка показывает уже проведённое производство. Просмотр не запускает производство и не списывает склад.</p>${metricGrid([['Всего партий',r.total_production_batches],['Партий в периоде',r.batches_in_period],['Последняя дата',r.last_production_date ? formatDate(r.last_production_date) : 'Нет данных'],['Произведенные заказы',r.produced_orders_count],['Известная себестоимость',moneyText(r.total_known_cost)],['Без себестоимости',r.missing_cost_count]])}${r.produced_quantity_totals.length ? `<h3>Итоги по единицам</h3><div class="overview-grid">${r.produced_quantity_totals.map((t)=>metricCard(unitLabel(t.unit), t.quantity)).join('')}</div>` : ''}${reportWarningsMarkup(r.warnings)}</section>`; }
function financeReportMarkup() { const r=reportsUiState.finance; if(!r) return ''; return `<section class="card data-card"><p class="card-kicker">Финансы</p><h2>Базовая финансовая сводка</h2><p class="page-message">Это не бухгалтерский отчёт и не налоговая декларация. Система не придумывает налог и показывает предупреждения, если данных не хватает.</p>${r.known_margin === null ? '<p class="page-message error-message">Маржа недоступна: не хватает цены продажи или себестоимости в одних и тех же производственных записях.</p>' : ''}${metricGrid([['Произведенных заказов',r.produced_order_count],['С ценой продажи',r.produced_orders_with_sale_price],['Известная выручка',moneyText(r.known_revenue)],['Известная себестоимость',moneyText(r.known_production_cost)],['Известная маржа',moneyText(r.known_margin)],['Маржа, %',r.known_margin_percent],['Полных финансовых записей',r.complete_finance_record_count],['Неполных для маржи',r.incomplete_margin_count],['Без цены продажи',r.missing_sale_price_count],['Без себестоимости',r.missing_cost_count]])}${reportWarningsMarkup(r.warnings)}</section>`; }
function reportWarningsMarkup(warnings: ReportWarning[]) { return `<div class="warning-panel"><h3>На что обратить внимание</h3>${warnings.length === 0 ? '<p>Критичных предупреждений нет.</p>' : `<ul>${warnings.map((w)=>`<li><strong>${escapeHtml(w.message)}</strong>${w.field ? `<small>Поле: ${escapeHtml(w.field)}</small>` : ''}</li>`).join('')}</ul>`}</div>`; }
function moneyText(value: string | null) { return value === null || value === '' ? 'Нет данных' : value; }


function loadSettingsStatus(force = false) {
  if (!force && (settingsUiState.status === 'loading' || settingsUiState.status === 'ready')) return;
  settingsUiState.status = 'loading'; settingsUiState.error = ''; render();
  getSettingsStatus().then((data) => { settingsUiState = { status: 'ready', data, error: '' }; render(); }).catch(() => { settingsUiState.status = 'error'; settingsUiState.error = 'Не удалось загрузить статус настроек. Проверьте, что локальное приложение запущено.'; render(); });
}

function loadWorkshopProfile(force = false) {
  if (!force && (workshopProfileUiState.status === 'loading' || workshopProfileUiState.status === 'ready')) return;
  workshopProfileUiState.status = 'loading'; workshopProfileUiState.error = ''; render();
  getWorkshopProfile().then((data) => { workshopProfileUiState = { status: 'ready', actionStatus: 'idle', profile: data.profile, draft: { ...data.profile }, error: '', message: '' }; render(); }).catch(() => { workshopProfileUiState.status = 'error'; workshopProfileUiState.error = 'Не удалось загрузить профиль мастерской. Данные рецептов, склада и заказов не изменялись.'; render(); });
}

function settingsPage() {
  return `<div class="settings-layout"><section class="card data-card settings-hero"><p>Здесь можно сохранить данные мастерской для новых документов и перейти к безопасной работе с локальными файлами.</p></section>${settingsWorkshopProfileCard()}${settingsLocalDataSection()}</div>`;
}

function isWorkshopProfileDirty() {
  const profile = workshopProfileUiState.profile;
  const draft = workshopProfileUiState.draft;
  return profile !== null && (draft.workshop_name !== profile.workshop_name || draft.master_name !== profile.master_name || draft.workshop_contact_text !== profile.workshop_contact_text || draft.workshop_note !== profile.workshop_note);
}
function isWorkshopProfileFormAvailable() { return workshopProfileUiState.status === 'ready' && workshopProfileUiState.profile !== null && workshopProfileUiState.actionStatus !== 'saving'; }

function settingsWorkshopProfileCard() {
  const state = workshopProfileUiState;
  const draft = state.draft;
  const saving = state.actionStatus === 'saving';
  const loading = state.status === 'loading';
  const available = isWorkshopProfileFormAvailable();
  const dirty = available && isWorkshopProfileDirty();
  const disabled = available ? '' : 'disabled';
  const actionDisabled = dirty ? '' : 'disabled';
  const retry = state.status === 'error' && state.profile === null ? '<div class="actions"><button class="secondary-action compact" type="button" data-action="reload-workshop-profile">Повторить загрузку</button></div>' : '';
  const message = state.message && state.status === 'ready' ? `<div data-workshop-profile-result>${feedbackMessage('success', state.message)}</div>` : '';
  const error = state.error ? `<div data-workshop-profile-result>${feedbackMessage('error', state.error)}</div>` : '';
  return `<section class="card data-card settings-card settings-profile-card"><h2>Профиль мастерской</h2><p>Эти данные добавляются в новые Markdown- и PDF-документы «Сводка мастерской», которые создаются в разделе «Документы отчётов».</p><p class="next-step">Ранее созданные документы не меняются автоматически.</p><div class="actions">${settingsAction('Открыть документы отчётов', 'Документы отчетов')}</div>${loading ? '<p class="muted-text">Загружаем профиль мастерской…</p>' : ''}${error}${retry}${message}<div data-workshop-profile-dirty-notice ${dirty ? '' : 'hidden'}>${feedbackMessage('neutral', 'Есть несохранённые изменения.')}</div><form class="ingredient-form" data-form="workshop-profile" aria-busy="${saving ? 'true' : 'false'}"><div class="form-grid settings-profile-form"><label>Название мастерской<input data-workshop-profile-field="workshop_name" value="${escapeHtml(draft.workshop_name)}" maxlength="120" placeholder="Например, Мастерская Анны" ${disabled} /></label><label>Имя мастера / косметолога<input data-workshop-profile-field="master_name" value="${escapeHtml(draft.master_name)}" maxlength="120" placeholder="Например, Анна Иванова" ${disabled} /></label><label class="full-span">Контактная информация<textarea data-workshop-profile-field="workshop_contact_text" maxlength="500" rows="4" placeholder="Телефон, почта или удобный способ связи" ${disabled}>${escapeHtml(draft.workshop_contact_text)}</textarea></label><label class="full-span">Краткое описание / примечание<textarea data-workshop-profile-field="workshop_note" maxlength="500" rows="4" placeholder="Коротко о мастерской для новых сводок" ${disabled}>${escapeHtml(draft.workshop_note)}</textarea></label></div><div class="actions"><button class="primary-action" type="submit" data-workshop-profile-save ${actionDisabled}>${saving ? 'Сохраняем…' : 'Сохранить профиль'}</button><button class="secondary-action" type="button" data-action="cancel-workshop-profile" ${actionDisabled}>Отменить изменения</button></div></form></section>`;
}


function syncWorkshopProfileDraftUi() {
  const available = isWorkshopProfileFormAvailable();
  const dirty = available && isWorkshopProfileDirty();
  const dirtyNotice = document.querySelector<HTMLElement>('[data-workshop-profile-dirty-notice]');
  if (dirtyNotice) dirtyNotice.hidden = !dirty;
  const saveButton = document.querySelector<HTMLButtonElement>('[data-workshop-profile-save]');
  if (saveButton) saveButton.disabled = !dirty;
  const cancelButton = document.querySelector<HTMLButtonElement>('[data-action="cancel-workshop-profile"]');
  if (cancelButton) cancelButton.disabled = !dirty;
  if (workshopProfileUiState.message || workshopProfileUiState.error) {
    workshopProfileUiState.message = '';
    workshopProfileUiState.error = '';
    clearFeedbackAnnouncement();
  }
  document.querySelectorAll<HTMLElement>('[data-workshop-profile-result]').forEach((element) => { element.hidden = true; element.textContent = ''; });
}


function settingsLocalDataSection() {
  if (settingsUiState.status === 'loading' && !settingsUiState.data) {
    return `<section class="card data-card settings-card"><h2>Локальные данные</h2><p>Проверяем, где хранятся данные на этом компьютере…</p>${settingsLocalDataActions()}</section>`;
  }
  if (settingsUiState.status === 'error' && !settingsUiState.data) {
    return `<section class="card data-card settings-card error-card"><h2>Локальные данные</h2><p>Не удалось показать сведения о папке данных. Профиль мастерской можно редактировать отдельно, если он загрузился.</p><div class="actions"><button class="secondary-action" type="button" data-action="reload-settings-status">Обновить сведения</button></div>${settingsLocalDataActions()}</section>`;
  }
  const local = settingsUiState.data?.local_data;
  return `<section class="card data-card settings-card"><h2>Локальные данные</h2><p>Данные мастерской хранятся на этом компьютере. Для переноса или крупных изменений используйте резервные копии и экспорт.</p>${local?.user_data_path_display ? `<div class="settings-data-path"><span>Папка данных</span><strong class="path-text">${escapeHtml(local.user_data_path_display)}</strong></div>` : '<p class="muted-text">Папка данных будет показана, когда локальное приложение вернет эти сведения.</p>'}${settingsLocalDataActions()}</section>`;
}

function settingsLocalDataActions() {
  return `<div class="actions">${settingsAction('Резервные копии', 'Резервные копии', true)}${settingsAction('Экспорт', 'Экспорт')}${settingsAction('Импорт', 'Импорт')}</div>`;
}

function settingsAction(label: string, section: NavigationSection, primary = false) { return `<button class="${primary ? 'primary-action' : 'secondary-action'} compact" type="button" data-action="navigate-settings-target" data-section="${section}">${escapeHtml(label)}</button>`; }

function helpPage() {
  const articles = filteredHelpArticles();
  const selected = helpArticles.find((article) => article.id === helpUiState.selectedArticleId) ?? articles[0] ?? helpArticles[0];
  return `<div class="help-layout"><section class="card data-card help-hero"><p class="card-kicker">Справка</p><h2>Помощь по мастерской</h2><p>Короткие подсказки по основным разделам: склад, рецепты, клиенты, заказы, производство, импорт и безопасность данных.</p><p class="next-step">Раздел помощи ничего не меняет в данных. Он только объясняет, как пользоваться приложением.</p></section>${helpFilters()}<div class="help-content-grid">${helpArticleList(articles)}${helpArticleDetail(selected)}</div></div>`;
}
function filteredHelpArticles() {
  const q = normalizeSearchText(helpUiState.search);
  return helpArticles.filter((article) => (!helpUiState.category || article.category === helpUiState.category) && (!q || normalizeSearchText([article.title, article.category, article.summary, article.body.join(' '), article.warning ?? ''].join(' ')).includes(q)));
}
function helpFilters() {
  return `<section class="card filter-card"><div class="catalog-toolbar"><label>Поиск<input data-action="filter-help-search" type="search" value="${escapeHtml(helpUiState.search)}" placeholder="Найти: рецепт, партия, импорт, резервная копия…" /></label><label>Категория<select data-action="filter-help-category"><option value="">Все категории</option>${helpCategories.map((category) => `<option value="${escapeHtml(category)}" ${helpUiState.category === category ? 'selected' : ''}>${escapeHtml(category)}</option>`).join('')}</select></label></div><div class="actions"><button class="secondary-action compact" type="button" data-action="reset-help-filters">Сбросить фильтр</button></div></section>`;
}
function helpArticleList(articles: HelpArticle[]) {
  if (articles.length === 0) return `<section class="card empty-card"><h2>Подсказки не найдены</h2><p>По этому запросу подсказок нет. Попробуйте другое слово: рецепт, склад, импорт, резервная копия.</p><button class="secondary-action" type="button" data-action="reset-help-filters">Сбросить фильтр</button></section>`;
  return `<section class="card data-card help-article-list"><div class="section-heading"><div><p class="card-kicker">Темы</p><h2>Подсказки</h2></div><span class="pill muted">${articles.length}</span></div>${articles.map((article) => `<article class="help-article-card ${article.id === helpUiState.selectedArticleId ? 'selected' : ''}"><p><span class="pill muted">${escapeHtml(article.category)}</span></p><h3>${escapeHtml(article.title)}</h3><p>${escapeHtml(article.summary)}</p><button class="secondary-action compact" type="button" data-action="open-help-article" data-id="${escapeHtml(article.id)}">${article.id === helpUiState.selectedArticleId ? 'Открыто' : 'Открыть'}</button></article>`).join('')}</section>`;
}
function helpArticleDetail(article: HelpArticle) {
  return `<section class="card data-card help-body"><p class="card-kicker">${escapeHtml(article.category)}</p><h2>${escapeHtml(article.title)}</h2><p class="lead-text">${escapeHtml(article.summary)}</p>${article.warning ? `<p class="page-message error-message">${escapeHtml(article.warning)}</p>` : ''}<ul class="checklist">${article.body.map((line, index) => `<li><span>${index + 1}</span><strong>${escapeHtml(line)}</strong></li>`).join('')}</ul>${article.relatedSections?.length ? `<div class="actions"><strong>Открыть раздел:</strong>${article.relatedSections.map((section) => `<button class="secondary-action compact" type="button" data-action="navigate-help-related" data-section="${section}">${escapeHtml(labelForSection(section))}</button>`).join('')}</div><p class="next-step">Кнопки только открывают разделы и не выполняют действий с данными.</p>` : '<p class="next-step">Эта подсказка только объясняет рабочий процесс и не меняет данные.</p>'}</section>`;
}
function updateHelpSearch(input: HTMLInputElement) {
  const cursor = input.selectionStart ?? input.value.length;
  helpUiState.search = input.value;
  render();
  const nextInput = document.querySelector<HTMLInputElement>('[data-action="filter-help-search"]');
  if (!nextInput) return;
  nextInput.focus();
  const nextCursor = Math.min(cursor, nextInput.value.length);
  nextInput.setSelectionRange(nextCursor, nextCursor);
}

function plannedSectionPlaceholder(section: NavigationSection) {
  return `<section class="card planned-card"><p class="card-kicker">Раздел недоступен</p><h2>${escapeHtml(labelForSection(section))}</h2><p>Не удалось открыть этот раздел из текущего состояния приложения.</p><p class="next-step">Вернитесь в боковое меню и повторите переход.</p></section>`;
}


function recipesPage() {
  if (recipesStatus === 'idle' || recipesStatus === 'loading') return `<section class="card"><p class="card-kicker">Рецепты</p><h2>Загружаем рецепты…</h2><p>Загружаем сохранённые шаблоны рецептов, версии и компоненты.</p></section>`;
  if (recipesStatus === 'error') return `<section class="card error-card"><p class="card-kicker">Рецепты</p><h2>Не удалось загрузить рецепты</h2><p>${recipesError || 'Данные временно недоступны.'}</p><p class="next-step">Проверьте, что приложение запущено полностью, и попробуйте обновить раздел.</p><button class="primary-action" type="button" data-action="reload-recipes">Повторить загрузку</button></section>`;
  const workspace = recipesState.showCreateForm ? recipeTemplateForm() : recipesState.selectedTemplate ? recipeDetailWorkspace() : '';
  const helper = !recipesState.showCreateForm && !recipesState.selectedTemplate ? recipeCreateHelperCard() : '';
  return `<div class="recipes-layout"><section class="card recipes-intro"><div><p class="card-kicker">Рецепты</p><h2>Каталог рецептов</h2><p>Сначала найдите сохраненный рецепт, затем открывайте создание, карточку или версии. Сохраненные версии только просматриваются и рассчитываются — история не редактируется.</p></div><div class="actions"><button class="primary-action" type="button" data-action="open-recipe-create">Создать рецепт</button><button class="secondary-action" type="button" data-action="reload-recipes">Обновить</button></div></section>${recipesMessage ? `<p class="page-message">${recipesMessage}</p>` : ''}${recipesRefreshWarning ? feedbackMessage('warning', recipesRefreshWarning) : ''}${recipesError ? `<p class="page-message error-message">${recipesError}</p>` : ''}${recipeFilterToolbar()}${workspace}${recipeTemplateList()}${helper}</div>`;
}
function recipeFilterToolbar() { const f = recipesState.filters; const categoryOptionsHtml = [`<option value="" ${f.categoryId === '' ? 'selected' : ''}>Все группы</option>`, `<option value="none" ${f.categoryId === 'none' ? 'selected' : ''}>Без группы</option>`, ...recipesState.catalogCategories.map((category) => `<option value="${category.id}" ${f.categoryId === category.id ? 'selected' : ''}>${escapeHtml(category.name)}</option>`)].join(''); const activeFilters = recipeActiveFilterChips(); return `<section class="card data-card catalog-browser"><p class="card-kicker">Каталог рецептов</p><h2>Найти рецепт</h2><div class="catalog-toolbar"><label class="full-span">Поиск<input type="search" data-action="filter-recipes-search" value="${escapeHtml(f.search)}" placeholder="Название, тип продукта, описание, заметки или статус" /></label><label>Моя группа<select data-action="filter-recipes-category">${categoryOptionsHtml}</select></label><label>Статус<select data-action="filter-recipes-status"><option value="active" ${f.status === 'active' ? 'selected' : ''}>Активные</option><option value="archived" ${f.status === 'archived' ? 'selected' : ''}>Неактивные</option><option value="all" ${f.status === 'all' ? 'selected' : ''}>Все</option></select></label></div>${activeFilters ? `<div class="active-filter-row"><strong>Активные фильтры:</strong>${activeFilters}</div>` : ''}<div class="catalog-summary"><span>Показаны рецепты: ${filteredRecipeTemplates().length} из ${recipesState.templates.length}</span><button class="secondary-action compact" type="button" data-action="reset-recipe-filters">Сбросить фильтры</button></div></section>`; }
function recipeTemplateForm() { const f = recipesState.templateForm; const busy = recipeTemplateSubmitting; return `<section class="card form-card"><div class="section-heading"><div><p class="card-kicker">Новый рецепт</p><h2>Создать рецепт</h2></div><button class="secondary-action compact" type="button" data-action="hide-recipe-create" ${busy ? 'disabled' : ''}>Вернуться к каталогу</button></div><form data-form="recipe-template" class="ingredient-form" novalidate ${busy ? 'aria-busy="true"' : ''}>${validationSummary(recipeTemplateValidation, 'Проверьте рецепт')}<div class="form-grid">${recipeTemplateField(`<input name="name" data-field="recipe-template-name" required maxlength="160" value="${escapeHtml(f.name)}" placeholder="Например, базовый дневной крем"${fieldErrorAttrs(recipeTemplateValidation, 'name', 'recipe-template-name-error')} ${busy ? 'readonly' : ''} />`, 'name')}${recipeTemplateField(`<input name="product_type" maxlength="120" value="${escapeHtml(f.product_type)}" placeholder="Крем, гель, тоник…"${fieldErrorAttrs(recipeTemplateValidation, 'product_type', 'recipe-template-product_type-error')} ${busy ? 'readonly' : ''} />`, 'product_type')}${recipeTemplateField(`<textarea name="description" rows="3" maxlength="1200"${fieldErrorAttrs(recipeTemplateValidation, 'description', 'recipe-template-description-error')} ${busy ? 'readonly' : ''}>${escapeHtml(f.description)}</textarea>`, 'description', true)}${recipeTemplateField(`<textarea name="notes" rows="3" maxlength="1200"${fieldErrorAttrs(recipeTemplateValidation, 'notes', 'recipe-template-notes-error')} ${busy ? 'readonly' : ''}>${escapeHtml(f.notes)}</textarea>`, 'notes', true)}</div><div class="actions"><button class="primary-action" type="submit" ${busy ? 'disabled' : ''}>${busy ? 'Создаём…' : 'Создать рецепт'}</button><button class="secondary-action" type="button" data-action="hide-recipe-create" ${busy ? 'disabled' : ''}>Вернуться к каталогу</button></div></form></section>`; }
function recipeCreateHelperCard() { return `<section class="card empty-card"><p class="card-kicker">Создание</p><h2>Нужно добавить новый рецепт?</h2><p>Форма создания скрыта, чтобы каталог оставался первым рабочим экраном.</p><p class="next-step">Нажмите «Создать рецепт», когда не нашли подходящую базовую формулу.</p><button class="primary-action" type="button" data-action="open-recipe-create">Создать рецепт</button></section>`; }
function recipeTemplateList() { const templates = filteredRecipeTemplates(); if (recipesState.templates.length === 0) return `<section class="card empty-card"><h2>Пока нет рецептов</h2><p>Пока нет рецептов. Создайте базовый рецепт, затем добавьте версию с составом.</p><p class="next-step">Следующее действие: нажмите «Создать рецепт».</p><button class="primary-action" type="button" data-action="open-recipe-create">Создать рецепт</button></section>`; if (templates.length === 0) return `<section class="card empty-card"><h2>По фильтрам рецепты не найдены</h2><p>Измените поиск или сбросьте фильтры, чтобы снова увидеть каталог.</p><button class="secondary-action" type="button" data-action="reset-recipe-filters">Сбросить фильтры</button></section>`; return `<section class="card data-card"><p class="card-kicker">Список</p><h2>Рецепты</h2><div class="recipe-list">${templates.map((t)=>`<article class="recipe-list-item ${recipesState.selectedTemplate?.id===t.id?'selected catalog-row-selected':''}"><div><strong>${escapeHtml(t.name)}</strong><small>${escapeHtml(t.product_type || 'Тип продукта не указан')} · <span class="pill ${t.is_active?'success':'muted'}">${t.is_active?'Активен':'Неактивен'}</span>${recipesState.selectedTemplate?.id===t.id?' · <span class="pill warning">Открыто</span>':''}</small><small>Моя группа: ${escapeHtml(recipeCatalogCategoryLabel(t))}</small>${recipeTagChips(t)}</div><button class="secondary-action compact" type="button" data-action="open-recipe" data-id="${t.id}">${recipesState.selectedTemplate?.id===t.id?'Открыто':'Открыть'}</button></article>`).join('')}</div></section>`; }
function recipeDetailWorkspace() { return `<div class="recipe-columns"><div>${recipeCatalogPanel()}</div><div>${recipeDetailPanel()}</div></div>`; }
function recipeCatalogPanel() { const template = recipesState.selectedTemplate; if (!template) return `<section class="card empty-card"><p class="card-kicker">Моя организация каталога</p><h2>Моя группа и метки</h2><p>Выберите рецепт, чтобы назначить ему группу и метки.</p><p class="next-step">Группы и метки помогают навести порядок в рецептах. Они не меняют версии рецепта и состав формулы.</p></section>`; const categoryDisabled = recipesState.catalogCreating === 'category'; const tagDisabled = recipesState.catalogCreating === 'tag'; return `<section class="card form-card"><p class="card-kicker">Моя организация каталога</p><h2>Моя группа и метки</h2><p>Группы и метки помогают навести порядок в рецептах. Они не меняют версии рецепта и состав формулы.</p><div class="catalog-classification"><label>Моя группа<select data-action="assign-recipe-category" data-id="${template.id}" ${recipesState.catalogSaving === 'saving' ? 'disabled' : ''}><option value="">Без моей группы</option>${recipesState.catalogCategories.map((category) => `<option value="${category.id}" ${category.id === template.catalog_category_id ? 'selected' : ''}>${escapeHtml(category.name)}</option>`).join('')}</select></label>${recipesState.catalogCategories.length === 0 ? '<p class="empty-hint">Группы рецептов пока не созданы. Создайте первую группу ниже.</p>' : ''}<div><strong>Метки</strong>${recipesState.catalogTags.length === 0 ? '<p class="empty-hint">Метки рецептов пока не созданы. Создайте первую метку ниже.</p>' : `<div class="tag-picker">${recipesState.catalogTags.map((tag) => `<label class="tag-chip ${template.catalog_tag_ids.includes(tag.id) ? 'selected' : ''}"><input type="checkbox" data-action="toggle-recipe-tag" data-recipe-template-id="${template.id}" value="${tag.id}" ${template.catalog_tag_ids.includes(tag.id) ? 'checked' : ''} ${recipesState.catalogSaving === 'saving' ? 'disabled' : ''} />${escapeHtml(tag.name)}</label>`).join('')}</div>`}</div></div><div class="catalog-create-grid"><form data-form="recipe-catalog-category" class="catalog-create-form"><h3>Добавить группу рецептов</h3><label>Название группы<input name="name" required maxlength="160" placeholder="Например, Кремы" ${categoryDisabled ? 'disabled' : ''} /></label><button class="secondary-action" type="submit" ${categoryDisabled ? 'disabled' : ''}>${recipesState.catalogCreating === 'category' ? 'Создаём…' : 'Создать группу'}</button></form><form data-form="recipe-catalog-tag" class="catalog-create-form"><h3>Добавить метку рецепта</h3><label>Название метки<input name="name" required maxlength="160" placeholder="Например, Для сухой кожи" ${tagDisabled ? 'disabled' : ''} /></label><button class="secondary-action" type="submit" ${tagDisabled ? 'disabled' : ''}>${recipesState.catalogCreating === 'tag' ? 'Создаём…' : 'Создать метку'}</button></form></div><p class="next-step">Группа и метки сохраняются сразу. Они помогают найти рецепт, но не меняют его версии и состав.</p></section>`; }
function recipeDetailPanel() { const template = recipesState.selectedTemplate; if (!template) return `<section class="card empty-card"><h2>Выберите рецепт</h2><p>Откройте рецепт из списка, чтобы увидеть версии, состав и расчет.</p><p class="next-step">Исторические версии не редактируются: для изменений создается новая версия.</p></section>`; return `<div class="recipe-detail-stack"><section class="card"><div class="section-heading"><div><p class="card-kicker">Рецепт</p><h2>${escapeHtml(template.name)}</h2></div><button class="secondary-action compact" type="button" data-action="close-recipe-detail">Закрыть рецепт</button></div><p><strong>Тип:</strong> ${escapeHtml(template.product_type || 'не указан')}</p><p>${escapeHtml(template.description || 'Описание пока не заполнено.')}</p>${template.notes ? `<p class="next-step">${escapeHtml(template.notes)}</p>` : ''}<span class="pill ${template.is_active?'success':'muted'}">${template.is_active?'Активен':'Неактивен'}</span></section>${recipeVersionsList()}${recipeVersionForm()}${recipeVersionDetailPanel()}</div>`; }
function recipeVersionsList() { if (recipesState.versions.length === 0) return `<section class="card empty-card"><h2>Версий пока нет</h2><p>У рецепта пока нет версий. Создайте первую версию и добавьте состав из компонентов.</p></section>`; return `<section class="card data-card"><p class="card-kicker">Версии</p><h2>Версии рецепта</h2><div class="table-wrap"><table><thead><tr><th>Версия</th><th>Статус</th><th>Заголовок</th><th>Партия</th><th>Создана</th><th>Действие</th></tr></thead><tbody>${recipesState.versions.map((v)=>`<tr><td>№${v.version_number}</td><td><span class="pill ${versionStatusClass(v.status)}">${versionStatusLabel(v.status)}</span></td><td>${escapeHtml(v.title || 'Без заголовка')}</td><td>${batchLabel(v.target_batch_size_value, v.target_batch_size_unit)}</td><td>${formatDateTime(v.created_at)}</td><td><button class="secondary-action compact" type="button" data-action="open-version" data-id="${v.id}">Открыть</button></td></tr>`).join('')}</tbody></table></div></section>`; }
function recipeVersionForm() { const f=recipesState.versionForm; const noIngredients = recipesState.ingredients.length === 0; const busy = recipeVersionSubmitting; return `<section class="card form-card"><p class="card-kicker">Новая версия рецепта</p><h2>Новая версия рецепта</h2><p class="next-step">Сохранение создаст новую историческую версию. Уже сохраненная версия не изменится${recipesState.selectedVersionDetail ? `; новая версия будет связана с версией №${recipesState.selectedVersionDetail.version.version_number} как с источником.` : '.'}</p><form data-form="recipe-version" class="ingredient-form" novalidate ${busy ? 'aria-busy="true"' : ''}>${validationSummary(recipeVersionValidation, 'Проверьте версию рецепта')}<div class="form-grid">${recipeVersionField(`<input name="title" maxlength="160" value="${escapeHtml(f.title)}" placeholder="Например, v1 с ниацинамидом"${fieldErrorAttrs(recipeVersionValidation, 'title', 'recipe-version-title-error')} ${busy ? 'readonly' : ''} />`, 'title')}${recipeVersionField(`<select name="status"${fieldErrorAttrs(recipeVersionValidation, 'status', 'recipe-version-status-error')} ${busy ? 'disabled' : ''}>${['draft','active','archived'].map((x)=>`<option value="${x}" ${f.status===x?'selected':''}>${versionStatusLabel(x)}</option>`).join('')}</select>`, 'status')}${recipeVersionField(`<input name="target_batch_size_value" inputmode="decimal" value="${escapeHtml(f.target_batch_size_value)}" placeholder="Например, 100"${fieldErrorAttrs(recipeVersionValidation, 'target_batch_size_value', 'recipe-version-target_batch_size_value-error')} ${busy ? 'readonly' : ''} />`, 'target_batch_size_value')}${recipeVersionField(`<select name="target_batch_size_unit"${fieldErrorAttrs(recipeVersionValidation, 'target_batch_size_unit', 'recipe-version-target_batch_size_unit-error')} ${busy ? 'disabled' : ''}>${['g','ml','pcs'].map((x)=>`<option value="${x}" ${f.target_batch_size_unit===x?'selected':''}>${unitLabel(x)}</option>`).join('')}</select>`, 'target_batch_size_unit')}${recipeVersionField(`<textarea name="change_note" rows="2"${fieldErrorAttrs(recipeVersionValidation, 'change_note', 'recipe-version-change_note-error')} ${busy ? 'readonly' : ''}>${escapeHtml(f.change_note)}</textarea>`, 'change_note', true)}${recipeVersionField(`<textarea name="notes" rows="2"${fieldErrorAttrs(recipeVersionValidation, 'notes', 'recipe-version-notes-error')} ${busy ? 'readonly' : ''}>${escapeHtml(f.notes)}</textarea>`, 'notes', true)}</div><h3>Конструктор состава</h3><p class="next-step">Соберите состав из компонентов справочника. После сохранения будет создана новая версия рецепта. Сохраненные версии не изменяются автоматически.</p><p class="empty-hint">Фазы A, B, C и D помогают читать формулу по шагам приготовления. Позиция задает порядок строк внутри версии.</p>${noIngredients ? '<p class="empty-hint">В рецепте пока нельзя выбрать компонент: активные компоненты не найдены. Создайте компонент в разделе «Компоненты» или обновите список.</p><p class="next-step">Если компонент уже создан, нажмите «Обновить список компонентов» и проверьте, что он не архивирован.</p>' : ''}<div class="recipe-lines">${f.ingredients.map(recipeLineForm).join('')}</div>${draftPercentHint()}<p class="next-step">Сначала добавьте компоненты в состав версии. Когда формула готова, нажмите «Сохранить версию рецепта». Сохранение создаст новую историческую версию и не изменит уже сохранённые версии.</p><div class="actions"><button class="secondary-action" type="button" data-action="add-recipe-line" ${noIngredients || busy ? 'disabled' : ''}>Добавить компонент в состав</button><button class="secondary-action" type="button" data-action="reload-recipe-ingredients" ${busy ? 'disabled' : ''}>Обновить список компонентов</button><button class="primary-action" type="submit" ${noIngredients || busy ? 'disabled' : ''}>${busy ? 'Сохраняем…' : 'Сохранить версию рецепта'}</button></div></form></section>`; }
function recipeLineForm(line: RecipeLineForm, index: number) { const noIngredients = recipesState.ingredients.length === 0; const busy = recipeVersionSubmitting; const name = (field: keyof RecipeLineForm) => `ingredients.${index}.${field}`; return `<fieldset class="recipe-line"><legend>Строка ${index+1} · Фаза ${escapeHtml(line.phase || 'A')}</legend>${recipeVersionField(`<input name="${name('position')}" required inputmode="numeric" value="${escapeHtml(line.position)}" placeholder="${index + 1}"${fieldErrorAttrs(recipeVersionValidation, name('position'), `recipe-version-${name('position')}-error`)} ${busy ? 'readonly' : ''} />`, name('position'))}${recipeVersionField(`<select name="${name('phase')}"${fieldErrorAttrs(recipeVersionValidation, name('phase'), `recipe-version-${name('phase')}-error`)} ${busy ? 'disabled' : ''}>${phaseOptions(line.phase)}</select>`, name('phase'))}${recipeVersionField(`<select name="${name('ingredient_id')}" required ${noIngredients || busy ? 'disabled' : ''}${fieldErrorAttrs(recipeVersionValidation, name('ingredient_id'), `recipe-version-${name('ingredient_id')}-error`)}><option value="">${noIngredients ? 'Нет активных компонентов' : 'Выберите компонент'}</option>${recipesState.ingredients.map((i)=>`<option value="${i.id}" ${line.ingredient_id===String(i.id)?'selected':''}>${escapeHtml(i.name)}</option>`).join('')}</select>`, name('ingredient_id'))}${recipeVersionField(`<input name="${name('amount_value')}" required inputmode="decimal" value="${escapeHtml(line.amount_value)}" placeholder="Например, 5 или 2.5"${fieldErrorAttrs(recipeVersionValidation, name('amount_value'), `recipe-version-${name('amount_value')}-error`)} ${busy ? 'readonly' : ''} />`, name('amount_value'))}${recipeVersionField(`<select name="${name('amount_unit')}"${fieldErrorAttrs(recipeVersionValidation, name('amount_unit'), `recipe-version-${name('amount_unit')}-error`)} ${busy ? 'disabled' : ''}>${['percent','g','ml','pcs'].map((u)=>`<option value="${u}" ${line.amount_unit===u?'selected':''}>${unitLabel(u)}</option>`).join('')}</select>`, name('amount_unit'))}${recipeVersionField(`<input name="${name('notes')}" value="${escapeHtml(line.notes)}" placeholder="Необязательно"${fieldErrorAttrs(recipeVersionValidation, name('notes'), `recipe-version-${name('notes')}-error`)} ${busy ? 'readonly' : ''} />`, name('notes'), true)}${recipesState.versionForm.ingredients.length>1?`<button class="secondary-action compact danger-action" type="button" data-action="remove-recipe-line" data-index="${index}" ${busy ? 'disabled' : ''}>Удалить строку</button>`:''}</fieldset>`; }
function recipeVersionDetailPanel() { if (recipesState.versionDetailStatus === 'loading') return `<section class="card"><h2>Загружаем версию…</h2><p>Загружаем сохранённый состав и расчёт.</p></section>`; if (recipesState.versionDetailStatus === 'error') return `<section class="card error-card"><h2>Не удалось загрузить версию рецепта</h2><p>Попробуйте открыть версию еще раз или обновить раздел.</p></section>`; const d=recipesState.selectedVersionDetail; if (!d) return ''; const v=d.version; const lines = d.ingredients.slice().sort((a,b)=>a.phase.localeCompare(b.phase) || a.position-b.position); return `<section class="card data-card"><p class="card-kicker">Сохраненная версия</p><h2>Версия №${v.version_number}</h2><p><strong>${escapeHtml(v.title || 'Без заголовка')}</strong> · ${versionStatusLabel(v.status)} · ${batchLabel(v.target_batch_size_value, v.target_batch_size_unit)}</p><p><strong>Комментарий к изменениям:</strong> ${escapeHtml(v.change_note || 'Не указан')}</p><p><strong>Заметки:</strong> ${escapeHtml(v.notes || 'Нет заметок')}</p><p class="next-step">Это сохраненная версия рецепта. Чтобы изменить состав, создайте новую версию на ее основе.</p>${d.ingredients.length===0?'<p class="empty-hint">В этой версии пока нет состава. Создайте новую версию с компонентами, чтобы использовать ее в индивидуальных рецептах и производстве.</p>':`<div class="table-wrap"><table><thead><tr><th>Позиция</th><th>Фаза</th><th>Компонент</th><th>Количество</th><th>Заметки</th></tr></thead><tbody>${lines.map((line)=>`<tr><td>${line.position}</td><td>${escapeHtml(line.phase || 'Не указана')}</td><td>${escapeHtml(ingredientName(line.ingredient_id))}</td><td>${escapeHtml(line.amount_value)} ${unitLabel(line.amount_unit)}</td><td>${escapeHtml(line.notes || 'Без заметок')}</td></tr>`).join('')}</tbody></table></div>`}${calculationPanel()}</section>`; }
function calculationPanel() { const c=recipesState.calculation; return `<div class="calculation-panel"><h3>Расчет версии</h3><form data-form="recipe-calculation" class="inline-form"><label>Целевой размер партии<input name="target_batch_size_value" inputmode="decimal" value="${escapeHtml(recipesState.calculationTargetValue)}" placeholder="Оставьте пустым для размера версии" /></label><label>Единица<select name="target_batch_size_unit"><option value="g" ${recipesState.calculationTargetUnit==='g'?'selected':''}>г</option><option value="ml" ${recipesState.calculationTargetUnit==='ml'?'selected':''}>мл</option></select></label><button class="primary-action" type="submit">Пересчитать</button></form>${calculationStatus==='loading'?'<p>Считаем в приложении…</p>':''}${calculationError?`<p class="page-message error-message">${calculationError}</p>`:''}${c?calculationResult(c):'<p class="next-step">Расчёт загрузится автоматически для сохранённой версии. Если нужно, укажите другой размер партии и пересчитайте.</p>'}</div>`; }
function calculationResult(c: RecipeCalculationResult) { return `<div class="calculation-result"><p><strong>Можно рассчитать:</strong> ${c.can_calculate?'да':'нет'} · <strong>Сумма процентов:</strong> ${escapeHtml(c.percent_total)}%</p>${c.issues.length?`<h4>${c.issues.some((i)=>i.severity==='error')?'Нужно исправить':'Предупреждения'}</h4><ul class="issue-list">${c.issues.map((i)=>`<li class="${i.severity==='error'?'danger-text':'warning-text'}">${escapeHtml(i.message)}${i.next_action?` <small>${escapeHtml(i.next_action)}</small>`:''}</li>`).join('')}</ul>`:''}<h4>Состав</h4>${c.lines.length?`<div class="table-wrap"><table><thead><tr><th>Компонент</th><th>Исходно</th><th>Рассчитано</th><th>Фаза</th><th>Комментарий</th></tr></thead><tbody>${c.lines.map((l)=>`<tr><td>${escapeHtml(l.ingredient_name)}</td><td>${escapeHtml(l.source_amount_value)} ${unitLabel(l.source_amount_unit)}</td><td>${l.calculated_amount_value?`${escapeHtml(l.calculated_amount_value)} ${unitLabel(l.calculated_amount_unit || '')}`:'—'}</td><td>${escapeHtml(l.phase || 'Не указана')}</td><td>${escapeHtml(l.calculation_note || '')}</td></tr>`).join('')}</tbody></table></div>`:'<p>Расчётные строки пока не получены.</p>'}<h4>Итого по единицам</h4>${c.totals_by_unit.length?`<ul>${c.totals_by_unit.map((t)=>`<li>${escapeHtml(t.total_value)} ${unitLabel(t.unit)}</li>`).join('')}</ul>`:'<p>Итоги пока не рассчитаны.</p>'}</div>`; }


function emptyPackagingItemForm(): PackagingItemFormState { return { id: null, name: '', kind: 'jar', unit: 'pcs', capacity_value: null, capacity_unit: null, material: '', supplier_hint: '', unit_cost: null, notes: '' }; }
function packagingKindLabel(kind: string) { return ({ jar: 'Баночка', bottle: 'Флакон', tube: 'Туба', pump: 'Помпа', cap: 'Крышка', dropper: 'Пипетка', label: 'Этикетка', box: 'Коробка', bag: 'Пакет', other: 'Другое' } as Record<string, string>)[kind] ?? escapeHtml(kind); }
function packagingKindOptions(current: string) { return packagingKindValues().map((value) => `<option value="${value}" ${value === current ? 'selected' : ''}>${packagingKindLabel(value)}</option>`).join(''); }
function packagingUnitOptions(current: string) { return ['pcs'].map((value) => `<option value="${value}" ${value === current ? 'selected' : ''}>${unitLabel(value)}</option>`).join(''); }
function capacityUnitOptions(current: string) { return ['ml','g'].map((value) => `<option value="${value}" ${value === current ? 'selected' : ''}>${unitLabel(value)}</option>`).join(''); }
function packagingItemCapacityLabel(item: PackagingItem) { return item.capacity_value && item.capacity_unit ? `${escapeHtml(item.capacity_value)} ${unitLabel(item.capacity_unit)}` : 'Не указан'; }
function packagingItemPayloadFromForm(form: HTMLFormElement): PackagingItemPayload { const data = new FormData(form); const nullable = (name: string) => { const value = String(data.get(name) ?? '').trim(); return value || null; }; return { name: String(data.get('name') ?? '').trim(), kind: String(data.get('kind') ?? 'other'), unit: String(data.get('unit') ?? 'pcs'), capacity_value: nullable('capacity_value'), capacity_unit: nullable('capacity_unit'), material: String(data.get('material') ?? '').trim(), supplier_hint: String(data.get('supplier_hint') ?? '').trim(), unit_cost: nullable('unit_cost'), notes: String(data.get('notes') ?? '').trim() }; }
function savePackagingItemFormFromDom() { const form = document.querySelector<HTMLFormElement>('[data-form="packaging-item"]'); if (!form) return; const payload = packagingItemPayloadFromForm(form); packagingItemsState.form = { ...payload, id: packagingItemsState.form.id }; }

function packagingCatalogCategoryLabel(item: PackagingItem) { return packagingItemsState.catalogCategories.find((category) => category.id === item.catalog_category_id)?.name ?? 'Не выбрана'; }
function packagingTagChips(item: PackagingItem) { const tags = item.catalog_tag_ids.map((id) => packagingItemsState.catalogTags.find((tag) => tag.id === id)).filter((tag): tag is CatalogTag => Boolean(tag)); return tags.length ? `<div class="tag-list">${tags.map((tag) => `<span class="tag-chip readonly">${escapeHtml(tag.name)}</span>`).join('')}</div>` : 'Нет меток'; }

function emptyIngredientLotForm(): IngredientLotFormState { return { id: null, ingredient_id: '', lot_code: '', supplier_name: '', purchased_at: '', expires_at: '', unit: 'g', unit_cost: '', total_cost: '', density_g_per_ml: '', notes: '' }; }
function lotUnitOptions(current: string) { return ['g','ml','pcs'].map((value) => `<option value="${value}" ${value === current ? 'selected' : ''}>${unitLabel(value)}</option>`).join(''); }
function lotIngredientName(id: number) { return ingredientLotsState.ingredients.find((ingredient) => ingredient.id === id)?.name ?? 'Компонент'; }
function lotStatusLabel(lot: IngredientLot) { if (!lot.is_active) return 'Неактивна'; const status = expirationStatus(lot.expires_at); return status ?? 'Активна'; }
function lotStatusClass(lot: IngredientLot) { if (!lot.is_active) return 'muted'; const status = expirationStatus(lot.expires_at); if (status === 'Просрочена') return 'danger'; if (status === 'Скоро истекает') return 'warning'; if (status === 'Без срока годности') return 'muted'; return 'success'; }
function expirationStatus(value: string | null) { if (!value) return 'Без срока годности'; const today = new Date(); today.setHours(0, 0, 0, 0); const expires = new Date(`${value}T00:00:00`); const days = Math.ceil((expires.getTime() - today.getTime()) / 86400000); if (days < 0) return 'Просрочена'; if (days <= 30) return 'Скоро истекает'; return null; }
function ingredientLotPayloadFromForm(form: HTMLFormElement): IngredientLotPayload { const data = new FormData(form); const nullable = (name: string) => { const value = String(data.get(name) ?? '').trim(); return value || null; }; return { ingredient_id: Number(data.get('ingredient_id')), lot_code: String(data.get('lot_code') ?? '').trim(), supplier_name: String(data.get('supplier_name') ?? '').trim(), purchased_at: nullable('purchased_at'), expires_at: nullable('expires_at'), unit: String(data.get('unit') ?? 'g'), unit_cost: nullable('unit_cost'), total_cost: nullable('total_cost'), density_g_per_ml: nullable('density_g_per_ml'), notes: String(data.get('notes') ?? '').trim() }; }
function saveIngredientLotFormFromDom() { const form = document.querySelector<HTMLFormElement>('[data-form="ingredient-lot"]'); if (!form) return; const data = new FormData(form); ingredientLotsState.form = { id: ingredientLotsState.form.id, ingredient_id: String(data.get('ingredient_id') ?? ''), lot_code: String(data.get('lot_code') ?? '').trim(), supplier_name: String(data.get('supplier_name') ?? '').trim(), purchased_at: String(data.get('purchased_at') ?? ''), expires_at: String(data.get('expires_at') ?? ''), unit: String(data.get('unit') ?? 'g'), unit_cost: String(data.get('unit_cost') ?? '').trim(), total_cost: String(data.get('total_cost') ?? '').trim(), density_g_per_ml: String(data.get('density_g_per_ml') ?? '').trim(), notes: String(data.get('notes') ?? '').trim() }; }



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


const clientFieldLabels: Record<string, string> = {
  full_name: 'ФИО клиента',
  phone: 'Телефон',
  email: 'Email',
  address: 'Адрес',
  birthday: 'Дата рождения',
  skin_notes: 'Особенности кожи',
  allergy_notes: 'Аллергии',
  preference_notes: 'Предпочтения',
  contraindication_notes: 'Противопоказания',
  notes: 'Заметки',
};
const ingredientFieldLabels: Record<string, string> = {
  name: 'Название',
  category: 'Категория',
  default_unit: 'Единица учета',
  density_g_per_ml: 'Плотность',
  notes: 'Заметки',
  inci_name: 'INCI',
  supplier_hint: 'Поставщик',
  allergen_note: 'Ограничения и аллергены',
  usage_note: 'Применение',
};
const ingredientLotFieldLabels: Record<string, string> = {
  ingredient_id: 'Компонент',
  lot_code: 'Номер партии',
  supplier_name: 'Поставщик',
  purchased_at: 'Дата покупки',
  expires_at: 'Срок годности',
  unit: 'Единица измерения',
  unit_cost: 'Цена за единицу',
  total_cost: 'Общая стоимость',
  density_g_per_ml: 'Плотность, г/мл',
  notes: 'Заметки',
};
const stockMovementFieldLabels: Record<string, string> = {
  ingredient_lot_id: 'Партия',
  movement_type: 'Тип движения',
  quantity: 'Количество',
  unit: 'Единица',
  occurred_at: 'Дата движения',
  reason: 'Причина',
  source: 'Источник',
  note: 'Заметки',
};
const packagingItemFieldLabels: Record<string, string> = {
  name: 'Название',
  kind: 'Тип тары',
  unit: 'Единица учета',
  capacity_value: 'Объем',
  capacity_unit: 'Единица объема',
  material: 'Материал',
  supplier_hint: 'Поставщик',
  unit_cost: 'Цена за единицу',
  notes: 'Заметки',
};
const recipeTemplateFieldLabels: Record<string, string> = {
  name: 'Название рецепта',
  product_type: 'Тип продукта',
  description: 'Описание',
  notes: 'Заметки',
};
const recipeVersionTopFieldLabels: Record<string, string> = {
  status: 'Статус',
  title: 'Заголовок версии',
  target_batch_size_value: 'Размер партии',
  target_batch_size_unit: 'Единица партии',
  notes: 'Заметки',
  change_note: 'Комментарий к изменениям',
};

function validationSummary(state: FormValidationState, title: string) {
  if (state.formErrors.length === 0) return '';
  return `<div class="form-error-summary"><strong>${escapeHtml(title)}</strong><ul>${state.formErrors.map((message) => `<li>${escapeHtml(message)}</li>`).join('')}</ul></div>`;
}
function fieldErrorHtml(state: FormValidationState, field: string, id: string) {
  const messages = state.fieldErrors[field] ?? [];
  if (messages.length === 0) return '';
  return `<div class="field-error" id="${id}">${messages.map((message) => `<p>${escapeHtml(message)}</p>`).join('')}</div>`;
}
function fieldErrorAttrs(state: FormValidationState, field: string, id: string) {
  return (state.fieldErrors[field] ?? []).length ? ` aria-invalid="true" aria-describedby="${id}"` : '';
}
function clientField(control: string, field: keyof ClientPayload, span = false) { return `<div class="form-field${span ? ' full-span' : ''}"><label>${control}</label>${fieldErrorHtml(clientValidation, field, `client-${field}-error`)}</div>`; }
function ingredientField(control: string, field: keyof IngredientPayload, span = false) { return `<div class="form-field${span ? ' full-span' : ''}"><label>${control}</label>${fieldErrorHtml(ingredientValidation, field, `ingredient-${field}-error`)}</div>`; }
function ingredientLotField(control: string, field: keyof IngredientLotFormState, span = false) { return `<div class="form-field${span ? ' full-span' : ''}"><label>${control}</label>${fieldErrorHtml(ingredientLotValidation, field, `ingredient-lot-${field}-error`)}</div>`; }
function stockMovementField(control: string, field: keyof StockMovementFormState, span = false) { return `<div class="form-field${span ? ' full-span' : ''}"><label>${control}</label>${fieldErrorHtml(stockMovementValidation, field, `stock-movement-${field}-error`)}</div>`; }
function recipeTemplateField(control: string, field: keyof RecipeTemplatePayload, span = false) { return `<div class="form-field${span ? ' full-span' : ''}"><label>${control}</label>${fieldErrorHtml(recipeTemplateValidation, field, `recipe-template-${field}-error`)}</div>`; }
function recipeVersionField(control: string, field: string, span = false) { return `<div class="form-field${span ? ' full-span' : ''}"><label>${control}</label>${fieldErrorHtml(recipeVersionValidation, field, `recipe-version-${field}-error`)}</div>`; }
function clientFieldAttrs(field: keyof ClientPayload) { return fieldErrorAttrs(clientValidation, field, `client-${field}-error`); }
function ingredientFieldAttrs(field: keyof IngredientPayload) { return fieldErrorAttrs(ingredientValidation, field, `ingredient-${field}-error`); }
function ingredientLotFieldAttrs(field: keyof IngredientLotFormState) { return fieldErrorAttrs(ingredientLotValidation, field, `ingredient-lot-${field}-error`); }
function clearClientFieldError(field: string, control?: HTMLInputElement | HTMLTextAreaElement) { const next = clearFieldValidation(clientValidation, field); if (next !== clientValidation) { clientValidation = next; clearFieldValidationDom('client', field, control); } }
function clearIngredientFieldError(field: string, control?: HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement) { const next = clearFieldValidation(ingredientValidation, field); if (next !== ingredientValidation) { ingredientValidation = next; clearFieldValidationDom('ingredient', field, control); } }
function clearIngredientLotFieldError(field: string, control?: HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement) { const next = clearFieldValidation(ingredientLotValidation, field); if (next !== ingredientLotValidation) { ingredientLotValidation = next; clearFieldValidationDom('ingredient-lot', field, control); } }
function clearStockMovementFieldError(field: string, control?: HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement) { const next = clearFieldValidation(stockMovementValidation, field); if (next !== stockMovementValidation) { stockMovementValidation = next; clearFieldValidationDom('stock-movement', field, control); } }
function clearPackagingItemFieldError(field: string, control?: HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement) { const next = clearFieldValidation(packagingItemValidation, field); if (next !== packagingItemValidation) { packagingItemValidation = next; clearFieldValidationDom('packaging-item', field, control); } }
function clearRecipeTemplateFieldError(field: string, control?: HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement) { const next = clearFieldValidation(recipeTemplateValidation, field); if (next !== recipeTemplateValidation) { recipeTemplateValidation = next; clearFieldValidationDom('recipe-template', field, control); } }
function clearRecipeVersionFieldError(field: string, control?: HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement) { const next = clearFieldValidation(recipeVersionValidation, field); if (next !== recipeVersionValidation) { recipeVersionValidation = next; clearFieldValidationDom('recipe-version', field, control); } }
function clearFieldValidationDom(prefix: 'client' | 'ingredient' | 'ingredient-lot' | 'stock-movement' | 'packaging-item' | 'recipe-template' | 'recipe-version', field: string, control?: HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement) {
  const active = document.activeElement === control;
  const start = 'selectionStart' in (control ?? {}) ? (control as HTMLInputElement | HTMLTextAreaElement).selectionStart : null;
  const end = 'selectionEnd' in (control ?? {}) ? (control as HTMLInputElement | HTMLTextAreaElement).selectionEnd : null;
  const errorId = `${prefix}-${field}-error`;
  control?.removeAttribute('aria-invalid');
  if (control?.getAttribute('aria-describedby') === errorId) control.removeAttribute('aria-describedby');
  document.getElementById(errorId)?.remove();
  if (active && control) {
    control.focus();
    if (start !== null && end !== null && 'setSelectionRange' in control) {
      try { (control as HTMLInputElement | HTMLTextAreaElement).setSelectionRange(start, end); } catch { /* selection is unavailable for this control type */ }
    }
  }
}
function disableClientFormButtons() {
  const form = document.querySelector<HTMLFormElement>('[data-form="client"]');
  if (form) form.querySelectorAll('button').forEach((b) => b.setAttribute('disabled', ''));
  document.querySelector<HTMLButtonElement>('[data-action="open-client-create"]')?.setAttribute('disabled', '');
}
function disableIngredientFormButtons() {
  const form = document.querySelector<HTMLFormElement>('[data-form="ingredient"]');
  if (form) form.querySelectorAll('button').forEach((b) => b.setAttribute('disabled', ''));
  document.querySelector<HTMLButtonElement>('[data-action="new-ingredient"]')?.setAttribute('disabled', '');
}
function reenableClientSubmitButtons() {
  document.querySelector<HTMLButtonElement>('[data-action="open-client-create"]')?.removeAttribute('disabled');
  const form = document.querySelector<HTMLFormElement>('[data-form="client"]');
  if (form) form.querySelectorAll('button').forEach((b) => b.removeAttribute('disabled'));
}
function reenableIngredientSubmitButtons() {
  document.querySelector<HTMLButtonElement>('[data-action="new-ingredient"]')?.removeAttribute('disabled');
  const form = document.querySelector<HTMLFormElement>('[data-form="ingredient"]');
  if (form) form.querySelectorAll('button').forEach((b) => b.removeAttribute('disabled'));
}
function disableIngredientLotFormButtons() {
  const form = document.querySelector<HTMLFormElement>('[data-form="ingredient-lot"]');
  if (form) form.querySelectorAll('button').forEach((b) => b.setAttribute('disabled', ''));
  document.querySelectorAll<HTMLButtonElement>('[data-action="new-ingredient-lot"], [data-action="edit-ingredient-lot"], [data-action="deactivate-ingredient-lot"]').forEach((b) => b.setAttribute('disabled', ''));
  form?.querySelector<HTMLButtonElement>('button[type="submit"]')?.replaceChildren(document.createTextNode('Сохраняем…'));
}
function reenableIngredientLotSubmitButtons() {
  document.querySelectorAll<HTMLButtonElement>('[data-action="new-ingredient-lot"], [data-action="edit-ingredient-lot"], [data-action="deactivate-ingredient-lot"]').forEach((b) => b.removeAttribute('disabled'));
  const form = document.querySelector<HTMLFormElement>('[data-form="ingredient-lot"]');
  if (form) form.querySelectorAll('button').forEach((b) => b.removeAttribute('disabled'));
  const submit = form?.querySelector<HTMLButtonElement>('button[type="submit"]');
  if (submit) submit.textContent = ingredientLotsState.formMode === 'edit' ? 'Сохранить изменения' : 'Создать партию';
}
function stockMovementFieldAttrs(field: keyof StockMovementFormState) { return fieldErrorAttrs(stockMovementValidation, field, `stock-movement-${field}-error`); }
function packagingItemField(control: string, field: keyof PackagingItemFormState, span = false) { return `<div class="form-field${span ? ' full-span' : ''}"><label>${control}</label>${fieldErrorHtml(packagingItemValidation, field, `packaging-item-${field}-error`)}</div>`; }
function packagingItemFieldAttrs(field: keyof PackagingItemFormState) { return fieldErrorAttrs(packagingItemValidation, field, `packaging-item-${field}-error`); }
function disableStockMovementSubmitControls() {
  const form = document.querySelector<HTMLFormElement>('[data-form="stock-movement"]');
  if (form) {
    form.querySelectorAll<HTMLInputElement | HTMLTextAreaElement>('input:not([readonly]), textarea:not([readonly])').forEach(mutationReadonly);
    form.querySelectorAll<HTMLSelectElement>('select').forEach(mutationDisabled);
    form.querySelectorAll<HTMLButtonElement>('button').forEach(mutationDisabled);
    const submit = form.querySelector<HTMLButtonElement>('button[type="submit"]');
    if (submit) submit.textContent = 'Создаём…';
  }
  mutationDisabled(document.querySelector<HTMLSelectElement>('[data-action="select-stock-lot"]'));
  mutationDisabled(document.querySelector<HTMLButtonElement>('[data-action="reload-stock-movements"]'));
}
function disablePackagingItemSubmitControls() {
  const form = document.querySelector<HTMLFormElement>('[data-form="packaging-item"]');
  if (form) {
    form.querySelectorAll<HTMLInputElement | HTMLTextAreaElement>('input, textarea').forEach(mutationReadonly);
    form.querySelectorAll<HTMLSelectElement>('select').forEach(mutationDisabled);
    form.querySelectorAll<HTMLButtonElement>('button').forEach(mutationDisabled);
    const submit = form.querySelector<HTMLButtonElement>('button[type="submit"]');
    if (submit) submit.textContent = 'Сохраняем…';
  }
  const guarded = '[data-action="new-packaging-item"], [data-action="edit-packaging-item"], [data-action="deactivate-packaging-item"], [data-action="reload-packaging-items"], [data-action="hide-packaging-create-form"], [data-action="cancel-packaging-edit"], [data-action="filter-packaging-search"], [data-action="filter-packaging-category"], [data-action="filter-packaging-kind"], [data-action="filter-packaging-status"], [data-action="add-packaging-tag-filter"], [data-action="remove-packaging-tag-filter"], [data-action="clear-packaging-filter"], [data-action="reset-packaging-filters"], [data-action="assign-packaging-category"], [data-action="toggle-packaging-tag"], [data-action="apply-packaging-assignment"], [data-action="reset-packaging-assignment"], [data-action="search-packaging-category"], [data-action="search-packaging-tags"], [data-action="toggle-packaging-tags"], [data-form="packaging-catalog-category"] input, [data-form="packaging-catalog-category"] button, [data-form="packaging-catalog-tag"] input, [data-form="packaging-catalog-tag"] button';
  document.querySelectorAll(guarded).forEach(mutationDisabled);
}
function reenableStockMovementSubmitButtons() {
  restoreMutationGuards(document);
  const submit = document.querySelector<HTMLButtonElement>('[data-form="stock-movement"] button[type="submit"]');
  if (submit) submit.textContent = 'Создать движение';
}
function reenablePackagingItemSubmitButtons() {
  restoreMutationGuards(document);
  const submit = document.querySelector<HTMLButtonElement>('[data-form="packaging-item"] button[type="submit"]');
  if (submit) submit.textContent = packagingItemsState.formMode === 'edit' ? 'Сохранить изменения' : 'Создать тару';
}
function apiValidationPayload(error: unknown) { return error && typeof error === 'object' && 'payload' in error ? (error as ApiErrorWithDetails).payload : error; }

function emptyClientForm(): ClientFormState { return { id: null, full_name: '', phone: '', email: '', address: '', birthday: null, skin_notes: '', allergy_notes: '', preference_notes: '', contraindication_notes: '', notes: '' }; }
function saveClientFormFromDom() { const form = document.querySelector<HTMLFormElement>('[data-form="client"]'); if (!form) return; const payload = clientPayloadFromForm(form); clientsState.form = { ...payload, id: clientsState.form.id }; }
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
function openClientCreateForm() { if (clientSubmitting) return; clientsState.formMode = 'create'; clientsState.showCreateForm = true; clientsState.form = emptyClientForm(); clientCardState = emptyClientCardState(); clientsMessage = ''; clientsError = ''; clientsRefreshWarning = ''; clientValidation = emptyFormValidationState(); render(); focusClientName(); }
function hideClientCreateForm() { if (clientSubmitting) return; clientSubmitToken += 1; clientsState.showCreateForm = false; clientValidation = emptyFormValidationState(); if (clientsState.formMode === 'create') { clientsState.form = emptyClientForm(); clientCardState = emptyClientCardState(); } render(); }

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
function closeClientEdit() { if (clientSubmitting) return; clientSubmitToken += 1; clientsState.formMode = 'create'; clientsState.showCreateForm = false; clientsState.form = emptyClientForm(); clientCardState = emptyClientCardState(); clientsMessage = ''; clientsError = ''; clientsRefreshWarning = ''; clientValidation = emptyFormValidationState(); render(); }
function focusClientName() { requestAnimationFrame(() => document.querySelector<HTMLInputElement>('[data-field="client-full-name"]')?.focus()); }

function loadClients(force = false) { if (!force && (clientsStatus === 'loading' || clientsStatus === 'ready')) return; clientsStatus = 'loading'; clientsError = ''; render(); getClients(clientsState.includeInactive).then((response) => { clientsState.items = response.clients; clientsStatus = 'ready'; render(); }).catch(() => { clientsStatus = 'error'; clientsError = 'Не удалось загрузить клиентов. Проверьте, что локальное приложение запущено.'; render(); }); }
function startEditClient(id: number) { if (clientSubmitting) return; clientSubmitToken += 1; const client = clientsState.items.find((item) => item.id === id); if (!client) return; clientsState.formMode = 'edit'; clientsState.showCreateForm = false; clientsState.form = { id: client.id, full_name: client.full_name, phone: client.phone, email: client.email, address: client.address, birthday: client.birthday, skin_notes: client.skin_notes, allergy_notes: client.allergy_notes, preference_notes: client.preference_notes, contraindication_notes: client.contraindication_notes, notes: client.notes }; clientsMessage = ''; clientsError = ''; clientsRefreshWarning = ''; clientValidation = emptyFormValidationState(); loadClientCardData(id); render(); focusClientName(); }
function submitClientForm(event: SubmitEvent) {
  event.preventDefault();
  if (clientSubmitting) return;
  const isEdit = Boolean(clientsState.formMode === 'edit' && clientsState.form.id);
  const submittedFormId = clientsState.form.id;
  if (isEdit) syncClientCardDraftFormsFromDom();
  const payload = clientPayloadFromForm(event.currentTarget as HTMLFormElement);
  clientsState.form = { ...payload, id: isEdit ? submittedFormId : null };
  const token = ++clientSubmitToken;
  clientSubmitting = true;
  clientValidation = emptyFormValidationState();
  clientsMessage = '';
  clientsError = '';
  clientsRefreshWarning = '';
  disableClientFormButtons();
  const request = isEdit ? updateClient(submittedFormId!, payload) : createClient(payload);
  request
    .then((client) => {
      if (token !== clientSubmitToken) return;
      clientsMessage = isEdit ? 'Карточка клиента обновлена.' : 'Клиент создан.';
      clientsError = '';
      clientsRefreshWarning = '';
      clientValidation = emptyFormValidationState();
      clientsState.formMode = isEdit ? 'edit' : 'create';
      clientsState.showCreateForm = false;
      clientsState.form = isEdit ? { ...payload, id: client.id } : emptyClientForm();
      clientsStatus = 'ready';
      render();
      getClients(clientsState.includeInactive)
        .then((response) => {
          if (token !== clientSubmitToken) return;
          clientsState.items = response.clients;
          clientsStatus = 'ready';
          clientSubmitting = false;
          render();
        })
        .catch(() => {
          if (token !== clientSubmitToken) return;
          clientSubmitting = false;
          clientsRefreshWarning = 'Клиент сохранён, но список не обновился. Нажмите «Обновить», чтобы получить актуальные данные.';
          clientsStatus = 'ready';
          render();
        });
    })
    .catch((error) => {
      if (token !== clientSubmitToken) return;
      if (isEdit) syncClientCardDraftFormsFromDom();
      clientSubmitting = false;
      clientsMessage = '';
      clientsError = '';
      clientsRefreshWarning = '';
      clientValidation = normalizeBackendValidation(apiValidationPayload(error), clientFieldLabels, 'Не удалось сохранить клиента. Проверьте поля и попробуйте ещё раз.');
      clientsStatus = 'ready';
      applyValidationToClientForm(clientValidation);
      reenableClientSubmitButtons();
      announceAssertive('Проверьте форму клиента. Ошибки показаны рядом с полями.');
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
function addPackagingTagFilter(value: string) { if (packagingPageMutationActive()) return; const id = Number(value); if (!id || packagingItemsState.filters.tagIds.includes(id)) return; packagingItemsState.filters.tagIds = [...packagingItemsState.filters.tagIds, id]; render(); }
function removePackagingTagFilter(id: number) { if (packagingPageMutationActive()) return; packagingItemsState.filters.tagIds = packagingItemsState.filters.tagIds.filter((tagId) => tagId !== id); render(); }
function clearPackagingFilter(filter: string) { if (packagingPageMutationActive()) return; if (filter === 'search') packagingItemsState.filters.search = ''; if (filter === 'category') packagingItemsState.filters.categoryId = ''; if (filter === 'kind') packagingItemsState.filters.systemType = ''; if (filter === 'status') packagingItemsState.filters.status = 'active'; render(); }
function clearablePackagingFilterChip(label: string, filter: 'search' | 'category' | 'kind' | 'status') { return `<span class="tag-chip selected">${label} <button type="button" data-action="clear-packaging-filter" ${packagingPageMutationActive() ? 'disabled' : ''} data-filter="${filter}" aria-label="Убрать фильтр ${label}">×</button></span>`; }
function packagingActiveFilterChips() { const f = packagingItemsState.filters; const chips: string[] = []; if (f.search.trim()) chips.push(clearablePackagingFilterChip(`Поиск: ${escapeHtml(f.search.trim())}`, 'search')); if (f.categoryId === 'none') chips.push(clearablePackagingFilterChip('Группа: Без группы', 'category')); if (typeof f.categoryId === 'number') chips.push(clearablePackagingFilterChip(`Группа: ${escapeHtml(packagingItemsState.catalogCategories.find((category) => category.id === f.categoryId)?.name ?? 'Выбранная группа')}`, 'category')); if (f.systemType) chips.push(clearablePackagingFilterChip(`Тип тары: ${packagingKindLabel(f.systemType)}`, 'kind')); if (f.status !== 'active') chips.push(clearablePackagingFilterChip(`Статус: ${f.status === 'archived' ? 'Архив' : 'Все'}`, 'status')); return chips.join(''); }


function filteredRecipeTemplates() { return filterCatalogItems(recipesState.templates, recipesState.filters, { getSearchText: recipeSearchText, getCatalogCategoryId: (item) => item.catalog_category_id, getCatalogTagIds: (item) => item.catalog_tag_ids, getSystemType: () => '', getIsActive: (item) => item.is_active }); }
function recipeSearchText(item: RecipeTemplate) { return [item.name, item.product_type, item.description, item.notes, item.is_active ? 'активен active' : 'неактивен архив archived', recipeCatalogCategoryLabel(item), item.catalog_tag_ids.map((id) => recipesState.catalogTags.find((tag) => tag.id === id)?.name ?? '').join(' ')].join(' '); }
function updateRecipeFilterSearch(input: HTMLInputElement) { const cursor = input.selectionStart ?? input.value.length; recipesState.filters.search = input.value; render(); const nextInput = document.querySelector<HTMLInputElement>('[data-action="filter-recipes-search"]'); if (!nextInput) return; nextInput.focus(); const nextCursor = Math.min(cursor, nextInput.value.length); nextInput.setSelectionRange(nextCursor, nextCursor); }
function clearRecipeFilter(filter: string) { if (filter === 'search') recipesState.filters.search = ''; if (filter === 'category') recipesState.filters.categoryId = ''; if (filter === 'status') recipesState.filters.status = 'active'; render(); }
function clearableRecipeFilterChip(label: string, filter: 'search' | 'category' | 'status') { return `<span class="tag-chip selected">${label} <button type="button" data-action="clear-recipe-filter" data-filter="${filter}" aria-label="Убрать фильтр ${label}">×</button></span>`; }
function recipeActiveFilterChips() { const f = recipesState.filters; const chips: string[] = []; if (f.search.trim()) chips.push(clearableRecipeFilterChip(`Поиск: ${escapeHtml(f.search.trim())}`, 'search')); if (f.categoryId === 'none') chips.push(clearableRecipeFilterChip('Группа: Без группы', 'category')); if (typeof f.categoryId === 'number') chips.push(clearableRecipeFilterChip(`Группа: ${escapeHtml(recipesState.catalogCategories.find((category) => category.id === f.categoryId)?.name ?? 'Выбранная группа')}`, 'category')); if (f.status !== 'active') chips.push(clearableRecipeFilterChip(`Статус: ${f.status === 'archived' ? 'Неактивные' : 'Все'}`, 'status')); return chips.join(''); }
function openRecipeCreateForm() { if (recipePageMutationActive()) return; recipeTemplateSubmitToken += 1; recipeTemplateMutationLifecycle.invalidate(); recipeTemplateValidation = emptyFormValidationState(); recipesState.showCreateForm = true; recipesState.selectedTemplate = null; recipesState.versions = []; recipesState.selectedVersionDetail = null; recipesState.versionDetailStatus = 'idle'; recipesState.calculation = null; calculationStatus = 'idle'; recipesMessage = ''; recipesError = ''; recipesRefreshWarning = ''; render(); focusRecipeTemplateName(); }
function hideRecipeCreateForm() { if (recipePageMutationActive()) return; recipeTemplateSubmitToken += 1; recipeTemplateMutationLifecycle.invalidate(); saveRecipeTemplateFormFromDom(); recipeTemplateValidation = emptyFormValidationState(); recipesState.showCreateForm = false; recipesMessage = ''; recipesError = ''; recipesRefreshWarning = ''; render(); }
function closeRecipeDetail() { if (recipePageMutationActive()) return; recipeVersionSubmitToken += 1; recipeVersionMutationLifecycle.invalidate(); recipeVersionRefreshToken += 1; recipeVersionValidation = emptyFormValidationState(); recipesState.versionForm = emptyRecipeVersionForm(); recipesState.selectedTemplate = null; recipesState.versions = []; recipesState.selectedVersionDetail = null; recipesState.versionDetailStatus = 'idle'; recipesState.calculation = null; calculationStatus = 'idle'; recipesMessage = ''; recipesError = ''; recipesRefreshWarning = ''; render(); }
function focusRecipeTemplateName() { requestAnimationFrame(() => document.querySelector<HTMLInputElement>('[data-field="recipe-template-name"]')?.focus()); }
function saveRecipeTemplateFormFromDom() { const form = document.querySelector<HTMLFormElement>('[data-form="recipe-template"]'); if (!form) return; recipesState.templateForm = recipeTemplatePayloadFromForm(form); }

function emptyIngredientForm(): IngredientFormState { return { id: null, name: '', category: 'other', default_unit: 'g', density_g_per_ml: null, notes: '', inci_name: '', supplier_hint: '', allergen_note: '', usage_note: '' }; }
function ingredientCatalogCategoryLabel(item: Ingredient) { return ingredientsState.catalogCategories.find((category) => category.id === item.catalog_category_id)?.name ?? 'Не выбрана'; }
function ingredientTagChips(item: Ingredient) { const tags = item.catalog_tag_ids.map((id) => ingredientsState.catalogTags.find((tag) => tag.id === id)).filter((tag): tag is CatalogTag => Boolean(tag)); return tags.length ? `<div class="tag-list">${tags.map((tag) => `<span class="tag-chip readonly">${escapeHtml(tag.name)}</span>`).join('')}</div>` : 'Нет меток'; }
function categoryLabel(category: string) { return ({ oil: 'Масло', butter: 'Баттер', wax: 'Воск', emulsifier: 'Эмульгатор', humectant: 'Увлажнитель', active: 'Актив', preservative: 'Консервант', fragrance: 'Отдушка', essential_oil: 'Эфирное масло', colorant: 'Краситель', water_phase: 'Водная фаза', additive: 'Добавка', other: 'Другое' } as Record<string, string>)[category] ?? category; }
function categoryOptions(current: string) { return ingredientSystemCategories().map((value) => `<option value="${value}" ${value === current ? 'selected' : ''}>${categoryLabel(value)}</option>`).join(''); }
function unitOptions(current: string) { return ['g','ml','percent','pcs'].map((value) => `<option value="${value}" ${value === current ? 'selected' : ''}>${unitLabel(value)}</option>`).join(''); }
function saveIngredientFormFromDom() { const form = document.querySelector<HTMLFormElement>('[data-form="ingredient"]'); if (!form) return; const payload = ingredientPayloadFromForm(form); ingredientsState.form = { ...payload, id: ingredientsState.form.id }; }
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
function addRecipeLine() { if (recipePageMutationActive()) return; saveVersionFormFromDom(); recipesState.versionForm.ingredients.push(emptyRecipeLine(recipesState.versionForm.ingredients.length + 1)); render(); }
function removeRecipeLine(index: number) { if (recipePageMutationActive()) return; saveVersionFormFromDom(); recipesState.versionForm.ingredients.splice(index, 1); recipeVersionValidation = clearRecipeVersionIngredientValidation(recipeVersionValidation); if (recipesState.versionForm.ingredients.length === 0) recipesState.versionForm.ingredients.push(emptyRecipeLine(recipesState.versionForm.ingredients.length + 1)); render(); }
function saveVersionFormFromDom() { const form=document.querySelector<HTMLFormElement>('[data-form="recipe-version"]'); if (!form) return; recipesState.versionForm = recipeVersionFormFromForm(form); }
function draftPercentTotalNumber() { return recipesState.versionForm.ingredients.reduce((sum, line) => line.amount_unit === 'percent' && line.amount_value.trim() && /^-?\d+([.,]\d+)?$/.test(line.amount_value.trim()) ? sum + Number(line.amount_value.trim().replace(',', '.')) : sum, 0); }
function draftPercentTotal() { const total = draftPercentTotalNumber(); return Number.isInteger(total) ? String(total) : String(Number(total.toFixed(4))); }
function draftPercentHint() { const total = draftPercentTotalNumber(); const isExact = Math.abs(total - 100) < 0.000001; return `<p class="next-step ${isExact ? 'success-text' : 'warning-text'}"><strong>Сумма процентов:</strong> ${escapeHtml(draftPercentTotal())}%. ${isExact ? 'Сумма процентов ровно 100%. После сохранения приложение выполнит итоговый расчёт версии.' : 'Проверьте сумму процентов. Итоговый расчёт выполняется приложением после сохранения версии.'}</p>`; }
function phaseOptions(current: string) { const selected = current || 'A'; return ['A','B','C','D'].map((phase) => `<option value="${phase}" ${selected===phase?'selected':''}>Фаза ${phase}</option>`).join(''); }
function clientRecipePhaseOptions(current: string) { const standard = ['A','B','C','D']; const selected = current || 'A'; const options = standard.map((phase) => `<option value="${phase}" ${selected===phase?'selected':''}>Фаза ${phase}</option>`); if (selected && !standard.includes(selected)) options.push(`<option value="${escapeHtml(selected)}" selected>${escapeHtml(selected)} · текущая фаза</option>`); return options.join(''); }
function validateRecipeVersionForm(form: RecipeVersionForm) { if (!recipesState.selectedTemplate) return 'Выберите базовый рецепт, для которого создается версия.'; for (const [index, line] of form.ingredients.entries()) { const row = index + 1; if (!line.ingredient_id) return `В строке ${row} выберите компонент из справочника.`; if (!line.amount_value) return `В строке ${row} укажите количество, например 5 или 2.5.`; if (!line.amount_unit) return `В строке ${row} выберите единицу: %, г, мл или шт.`; if (!/^\d+$/.test(line.position)) return `В строке ${row} позиция должна быть целым числом, например ${row}.`; } return ''; }
function recipeTemplatePayloadFromForm(form: HTMLFormElement): RecipeTemplatePayload { const data = new FormData(form); return { name: String(data.get('name') ?? '').trim(), product_type: String(data.get('product_type') ?? '').trim(), description: String(data.get('description') ?? '').trim(), notes: String(data.get('notes') ?? '').trim() }; }
function recipeVersionFormFromForm(form: HTMLFormElement): RecipeVersionForm { const data = new FormData(form); const ingredients = recipesState.versionForm.ingredients.map((line, index) => ({ ingredient_id: String(data.get(`ingredients.${index}.ingredient_id`) ?? line.ingredient_id ?? ''), position: String(data.get(`ingredients.${index}.position`) ?? line.position ?? index + 1).trim(), phase: String(data.get(`ingredients.${index}.phase`) ?? line.phase ?? '').trim(), amount_value: String(data.get(`ingredients.${index}.amount_value`) ?? line.amount_value ?? '').trim(), amount_unit: String(data.get(`ingredients.${index}.amount_unit`) ?? line.amount_unit ?? 'percent'), notes: String(data.get(`ingredients.${index}.notes`) ?? line.notes ?? '').trim() })); return { title: String(data.get('title') ?? '').trim(), status: String(data.get('status') ?? recipesState.versionForm.status ?? 'draft'), target_batch_size_value: String(data.get('target_batch_size_value') ?? '').trim(), target_batch_size_unit: String(data.get('target_batch_size_unit') ?? recipesState.versionForm.target_batch_size_unit ?? 'g'), notes: String(data.get('notes') ?? '').trim(), change_note: String(data.get('change_note') ?? '').trim(), ingredients }; }
function recipeVersionFieldLabels(form: RecipeVersionForm): Record<string, string> { const labels: Record<string, string> = { ...recipeVersionTopFieldLabels }; form.ingredients.forEach((_, index) => { labels[`ingredients.${index}.ingredient_id`] = `Строка ${index + 1}: компонент`; labels[`ingredients.${index}.position`] = `Строка ${index + 1}: позиция`; labels[`ingredients.${index}.phase`] = `Строка ${index + 1}: фаза`; labels[`ingredients.${index}.amount_value`] = `Строка ${index + 1}: количество`; labels[`ingredients.${index}.amount_unit`] = `Строка ${index + 1}: единица`; labels[`ingredients.${index}.notes`] = `Строка ${index + 1}: заметка`; }); return labels; }
function clearRecipeVersionIngredientValidation(state: FormValidationState): FormValidationState { return clearIndexedCollectionValidation(state, 'ingredients'); }
function recipeVersionPayload(form: RecipeVersionForm) { return { title: form.title, status: form.status, target_batch_size_value: form.target_batch_size_value || null, target_batch_size_unit: form.target_batch_size_value ? form.target_batch_size_unit : null, notes: form.notes, change_note: form.change_note, created_from_version_id: recipesState.selectedVersionDetail?.version.id ?? null, ingredients: form.ingredients.map((line, index)=>({ ingredient_id: Number(line.ingredient_id), position: Number(line.position || index + 1), phase: line.phase, amount_value: line.amount_value, amount_unit: line.amount_unit, notes: line.notes })) }; }

function startEditIngredient(id: number) {
  if (ingredientSubmitting) return;
  ingredientSubmitToken += 1;
  const item = ingredientsState.items.find((ingredient) => ingredient.id === id);
  const current = ingredientsState.formMode === 'edit' && ingredientsState.form.id ? ingredientsState.items.find((ingredient) => ingredient.id === ingredientsState.form.id) ?? null : null;
  if (!item || !confirmDiscardDirtyAssignment(assignmentDraftIsDirty(current, ingredientsState.assignmentDraft))) return;
  ingredientsState.formMode = 'edit'; ingredientsState.showCreateForm = false; ingredientsState.form = { id: item.id, name: item.name, category: item.category, default_unit: item.default_unit, density_g_per_ml: item.density_g_per_ml, notes: item.notes, inci_name: item.inci_name, supplier_hint: item.supplier_hint, allergen_note: item.allergen_note, usage_note: item.usage_note }; ingredientsState.assignmentDraft = assignmentDraftFromItem(item); ingredientsMessage = ''; ingredientsError = ''; ingredientsRefreshWarning = ''; ingredientValidation = emptyFormValidationState(); render();
}
function cancelIngredientEdit() {
  if (ingredientSubmitting) return;
  ingredientSubmitToken += 1;
  const current = ingredientsState.formMode === 'edit' && ingredientsState.form.id ? ingredientsState.items.find((ingredient) => ingredient.id === ingredientsState.form.id) ?? null : null;
  if (!confirmDiscardDirtyAssignment(assignmentDraftIsDirty(current, ingredientsState.assignmentDraft))) return;
  ingredientsState.formMode = 'create'; ingredientsState.form = emptyIngredientForm(); ingredientsState.assignmentDraft = emptyAssignmentDraft(); ingredientsState.showCreateForm = false; ingredientsMessage = ''; ingredientsError = ''; ingredientsRefreshWarning = ''; ingredientValidation = emptyFormValidationState(); render();
}

function apiGet<T>(url: string): Promise<T> { return fetch(url).then(async (response) => { if (!response.ok) { let payload: unknown = null; try { payload = await response.json(); } catch { payload = null; } throw apiErrorFromPayload(payload, response.status); } return response.json() as Promise<T>; }); }
function apiErrorMessage(payload: unknown) { if (typeof payload === 'string') return payload; if (payload && typeof payload === 'object' && 'detail' in payload) { const detail = (payload as { detail?: unknown }).detail; if (typeof detail === 'string') return detail; if (detail && typeof detail === 'object' && 'message' in detail) return String((detail as { message?: unknown }).message ?? 'API request failed'); } return 'API request failed'; }
function apiIssues(payload: unknown): ApiIssue[] { if (!payload || typeof payload !== 'object' || !('detail' in payload)) return []; const detail = (payload as { detail?: unknown }).detail; if (!detail || typeof detail !== 'object' || !('issues' in detail)) return []; const issues = (detail as { issues?: unknown }).issues; return Array.isArray(issues) ? issues as ApiIssue[] : []; }
function apiErrorFromPayload(payload: unknown, status: number): ApiErrorWithDetails { const error = new Error(apiErrorMessage(payload)) as ApiErrorWithDetails; error.status = status; error.issues = apiIssues(payload); error.payload = payload; return error; }
function apiSend<T>(url: string, method: 'POST' | 'PUT' | 'PATCH', body?: unknown): Promise<T> { return fetch(url, { method, headers: body ? { 'Content-Type': 'application/json' } : undefined, body: body ? JSON.stringify(body) : undefined }).then(async (response) => { if (!response.ok) { let payload: unknown = null; try { payload = await response.json(); } catch { payload = null; } throw apiErrorFromPayload(payload, response.status); } return response.json() as Promise<T>; }); }
function apiForm<T>(url: string, method: 'POST', formData: FormData): Promise<T> { return fetch(url, { method, body: formData }).then(async (response) => { if (!response.ok) { let payload: unknown = null; try { payload = await response.json(); } catch { payload = null; } throw apiErrorFromPayload(payload, response.status); } return response.json() as Promise<T>; }); }
function getSettingsStatus(): Promise<SettingsStatusResponse> { return apiGet<SettingsStatusResponse>('/api/settings/status'); }
function getWorkshopProfile(): Promise<WorkshopProfileResponse> { return apiGet<WorkshopProfileResponse>('/api/settings/workshop-profile'); }
function updateWorkshopProfile(payload: WorkshopProfile): Promise<WorkshopProfileResponse> { return apiSend<WorkshopProfileResponse>('/api/settings/workshop-profile', 'PUT', payload); }
function getReportsOverview(): Promise<OverviewReportResponse> { return apiGet<OverviewReportResponse>('/api/reports/overview'); }
function getInventoryReport(): Promise<InventoryReportResponse> { return apiGet<InventoryReportResponse>('/api/reports/inventory'); }
function getOrdersReport(): Promise<OrdersReportResponse> { return apiGet<OrdersReportResponse>('/api/reports/orders'); }
function getProductionReport(): Promise<ProductionReportResponse> { return apiGet<ProductionReportResponse>('/api/reports/production'); }
function getFinanceReport(): Promise<FinanceReportResponse> { return apiGet<FinanceReportResponse>('/api/reports/finance'); }
function getReportDocumentStatus(): Promise<ReportDocumentStatusResponse> { return apiGet<ReportDocumentStatusResponse>('/api/report-documents/status'); }
function getReportDocuments(): Promise<ReportDocumentListResponse> { return apiGet<ReportDocumentListResponse>('/api/report-documents'); }
function createOverviewReportDocument(payload: ReportOverviewDocumentCreateRequest): Promise<ReportDocumentCreateResponse> { return apiSend<ReportDocumentCreateResponse>('/api/report-documents/reports/overview', 'POST', payload); }
function getBackupStatus(): Promise<BackupStatusResponse> { return apiGet<BackupStatusResponse>('/api/backups/status'); }
function getBackups(): Promise<BackupListResponse> { return apiGet<BackupListResponse>('/api/backups'); }
function createBackup(payload: BackupCreateRequest): Promise<BackupCreateResponse> { return apiSend<BackupCreateResponse>('/api/backups', 'POST', payload); }
function getImportTargets(): Promise<ImportTargetsResponse> { return apiGet<ImportTargetsResponse>('/api/imports/targets'); }
function createImportDraft(file: File, targetType: string): Promise<ImportDraftCreateResponse> { const formData = new FormData(); formData.append('file', file); formData.append('target_type', targetType); return apiForm<ImportDraftCreateResponse>('/api/imports/drafts', 'POST', formData); }
function getImportDrafts(params: ImportDraftListParams = {}): Promise<ImportDraftListResponse> { const search = new URLSearchParams(); if (params.status) search.set('status', params.status); if (params.targetType) search.set('target_type', params.targetType); if (params.limit) search.set('limit', String(params.limit)); if (params.offset) search.set('offset', String(params.offset)); const query = search.toString(); return apiGet<ImportDraftListResponse>(`/api/imports/drafts${query ? `?${query}` : ''}`); }
function getImportDraft(id: number, params: { limit?: number; offset?: number } = {}): Promise<ImportDraftDetailResponse> { const search = new URLSearchParams(); if (params.limit) search.set('limit', String(params.limit)); if (params.offset) search.set('offset', String(params.offset)); const query = search.toString(); return apiGet<ImportDraftDetailResponse>(`/api/imports/drafts/${id}${query ? `?${query}` : ''}`); }
function cancelImportDraft(id: number): Promise<ImportDraftCancelResponse> { return apiSend<ImportDraftCancelResponse>(`/api/imports/drafts/${id}/cancel`, 'POST'); }
function applyImportDraft(draftId: number, payload: ImportDraftApplyRequest): Promise<ImportDraftApplyResponse> { return apiSend<ImportDraftApplyResponse>(`/api/imports/drafts/${draftId}/apply`, 'POST', payload); }
function getExportStatus(): Promise<ExportStatusResponse> { return apiGet<ExportStatusResponse>('/api/exports/status'); }
function getExports(): Promise<ExportListResponse> { return apiGet<ExportListResponse>('/api/exports'); }
function createExport(payload: ExportCreateRequest): Promise<ExportCreateResponse> { return apiSend<ExportCreateResponse>('/api/exports', 'POST', payload); }
function getDemoDataStatus(): Promise<DemoDataStatusResponse> { return apiGet<DemoDataStatusResponse>('/api/demo-data/status'); }
function installDemoData(payload: DemoDataInstallRequest): Promise<DemoDataInstallResponse> { return apiSend<DemoDataInstallResponse>('/api/demo-data/install', 'POST', payload); }
function clearDemoData(payload: DemoDataClearRequest): Promise<DemoDataClearResponse> { return apiSend<DemoDataClearResponse>('/api/demo-data/clear', 'POST', payload); }
function getPurchaseSuggestions(filters: PurchaseSuggestionsState['filters']): Promise<PurchaseSuggestionListResponse> { const params = new URLSearchParams({ status: filters.status, limit: '100', offset: '0' }); if (filters.reason) params.set('reason', filters.reason); if (filters.itemType) params.set('item_type', filters.itemType); return apiGet<PurchaseSuggestionListResponse>(`/api/purchase-suggestions?${params.toString()}`); }
function regeneratePurchaseSuggestions(): Promise<PurchaseSuggestionGenerationResponse> { return apiSend<PurchaseSuggestionGenerationResponse>('/api/purchase-suggestions/regenerate', 'POST'); }
function createManualPurchaseSuggestion(payload: ManualPurchaseSuggestionRequest): Promise<PurchaseSuggestionResponse> { return apiSend<PurchaseSuggestionResponse>('/api/purchase-suggestions', 'POST', payload); }
function updatePurchaseSuggestion(id: number, payload: PurchaseSuggestionUpdateRequest): Promise<PurchaseSuggestionResponse> { return apiSend<PurchaseSuggestionResponse>(`/api/purchase-suggestions/${id}`, 'PATCH', payload); }
function markPurchaseSuggestionPurchased(id: number): Promise<PurchaseSuggestionResponse> { return apiSend<PurchaseSuggestionResponse>(`/api/purchase-suggestions/${id}/mark-purchased`, 'POST'); }
function dismissPurchaseSuggestion(id: number): Promise<PurchaseSuggestionResponse> { return apiSend<PurchaseSuggestionResponse>(`/api/purchase-suggestions/${id}/dismiss`, 'POST'); }
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
  }).catch(() => { stockMovementsStatus = 'error'; stockMovementsError = 'Не удалось получить данные о движениях склада.'; render(); });
}
function selectStockMovementLot(lotId: number) { if (stockMovementSubmitting) return; stockMovementSubmitToken += 1; stockMovementLotDetailLifecycle.invalidate(); saveStockMovementFormFromDom(); stockMovementsState.selectedLotId = lotId || null; stockMovementsState.form = { ...emptyStockMovementForm(), ingredient_lot_id: lotId ? String(lotId) : '' }; stockMovementValidation = emptyFormValidationState(); stockMovementsRefreshWarning = ''; stockMovementsMessage = ''; stockMovementsError = ''; render(); if (lotId) loadSelectedStockMovementLot(lotId); }
function fetchStockMovementLotDetail(lotId: number) { return Promise.all([getIngredientLotBalance(lotId), getStockMovementsByLot(lotId)]).then(([balance, movements]) => ({ balance, movements: movements.movements })); }
function stockMovementLotDetailIsCurrent(request: StockMovementLotDetailRequest, submitToken: number | null = request.submitToken) { return stockMovementLotDetailLifecycle.isCurrent(request, stockMovementsState.selectedLotId, submitToken); }
function commitStockMovementLotDetail(request: StockMovementLotDetailRequest, detail: { balance: IngredientLotBalanceResponse; movements: StockMovement[] }, submitToken: number | null = request.submitToken) { if (!stockMovementLotDetailIsCurrent(request, submitToken)) return false; stockMovementsState.balance = detail.balance; stockMovementsState.movements = detail.movements; stockMovementsState.detailStatus = 'ready'; return true; }
function loadSelectedStockMovementLot(lotId: number) { const request = stockMovementLotDetailLifecycle.begin(lotId); stockMovementsState.detailStatus = 'loading'; stockMovementsState.balance = null; stockMovementsState.movements = []; if (!stockMovementSubmitting) render(); fetchStockMovementLotDetail(lotId).then((detail) => { if (!commitStockMovementLotDetail(request, detail)) return; render(); }).catch(() => { if (!stockMovementLotDetailIsCurrent(request)) return; stockMovementsState.detailStatus = 'error'; stockMovementsError = 'Не удалось загрузить остаток или историю выбранной партии.'; render(); }); }
function refreshSelectedStockMovementLot(lotId: number, submitToken: number) { const request = stockMovementLotDetailLifecycle.begin(lotId, submitToken); stockMovementsState.detailStatus = 'loading'; return fetchStockMovementLotDetail(lotId).then((detail) => { if (!commitStockMovementLotDetail(request, detail, submitToken)) return false; return true; }); }
function submitStockMovementForm(event: SubmitEvent) { event.preventDefault(); if (stockMovementSubmitting) return; const payload = stockMovementPayloadFromForm(event.currentTarget as HTMLFormElement); stockMovementsState.form = { ingredient_lot_id: String(payload.ingredient_lot_id || ''), movement_type: payload.movement_type, quantity: payload.quantity, unit: payload.unit, occurred_at: payload.occurred_at ?? '', reason: payload.reason, source: payload.source, note: payload.note }; const token = ++stockMovementSubmitToken; stockMovementLotDetailLifecycle.invalidate(); stockMovementSubmitting = true; stockMovementValidation = emptyFormValidationState(); stockMovementsMessage = ''; stockMovementsError = ''; stockMovementsRefreshWarning = ''; applyValidationToStockMovementForm(stockMovementValidation); disableStockMovementSubmitControls(); if (!payload.ingredient_lot_id) { stockMovementSubmitting = false; stockMovementValidation = { fieldErrors: { ingredient_lot_id: ['Партия: выберите партию для движения.'] }, formErrors: [] }; applyValidationToStockMovementForm(stockMovementValidation); reenableStockMovementSubmitButtons(); return; } createStockMovement(payload).then(() => { if (token !== stockMovementSubmitToken) return; stockMovementsMessage = 'Движение создано. Текущий остаток пересчитан по истории движений.'; stockMovementsError = ''; stockMovementValidation = emptyFormValidationState(); stockMovementsState.form = { ...emptyStockMovementForm(), ingredient_lot_id: String(payload.ingredient_lot_id) }; return refreshSelectedStockMovementLot(payload.ingredient_lot_id, token).then((applied) => { if (token !== stockMovementSubmitToken || !applied) return; stockMovementSubmitting = false; render(); }).catch(() => { if (token !== stockMovementSubmitToken || stockMovementsState.selectedLotId !== payload.ingredient_lot_id) return; stockMovementSubmitting = false; stockMovementsState.detailStatus = 'error'; stockMovementsRefreshWarning = 'Движение создано, но список не обновился. Нажмите «Обновить», чтобы увидеть актуальный остаток.'; render(); }); }).catch((error) => { if (token !== stockMovementSubmitToken) return; stockMovementSubmitting = false; stockMovementsMessage = ''; stockMovementsError = ''; stockMovementsRefreshWarning = ''; stockMovementValidation = normalizeBackendValidation(apiValidationPayload(error), stockMovementFieldLabels, 'Не удалось создать движение. Проверьте количество, единицу и остаток выбранной партии.'); stockMovementsStatus = 'ready'; applyValidationToStockMovementForm(stockMovementValidation); reenableStockMovementSubmitButtons(); announceAssertive('Проверьте движение склада. Ошибки показаны рядом с полями.'); }); }

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
    .catch(() => { recipesStatus = 'error'; recipesError = 'Не получилось загрузить рецепты. Проверьте, что приложение запущено полностью, и попробуйте обновить раздел.'; render(); });
}
function openRecipeTemplate(id: number) {
  if (recipePageMutationActive()) return;
  saveRecipeTemplateFormFromDom();
  recipeTemplateSubmitToken += 1;
  recipeTemplateMutationLifecycle.invalidate();
  recipeVersionSubmitToken += 1;
  recipeVersionMutationLifecycle.invalidate();
  recipeVersionRefreshToken += 1;
  recipeTemplateValidation = emptyFormValidationState();
  recipeVersionValidation = emptyFormValidationState();
  recipesState.showCreateForm = false;
  recipesError = ''; recipesMessage = ''; recipesRefreshWarning = '';
  const token = recipeVersionRefreshToken;
  Promise.all([getRecipeTemplate(id), getRecipeVersions(id)]).then(([template, versions]) => { if (token !== recipeVersionRefreshToken) return; recipesState.selectedTemplate = template; recipesState.versions = versions.recipe_versions; recipesState.selectedVersionDetail = null; recipesState.versionDetailStatus = 'idle'; recipesState.calculation = null; calculationStatus = 'idle'; render(); }).catch(() => { if (token !== recipeVersionRefreshToken) return; recipesError = 'Не удалось открыть рецепт. Попробуйте обновить страницу.'; render(); });
}
function openRecipeVersion(id: number) { if (recipePageMutationActive()) return; const token = ++recipeVersionRefreshToken; recipesError = ''; recipesRefreshWarning = ''; calculationError = ''; recipesState.versionDetailStatus = 'loading'; recipesState.calculation = null; calculationStatus = 'loading'; render(); getRecipeVersionDetail(id).then((detail)=>{ if (token !== recipeVersionRefreshToken) return null; recipesState.selectedVersionDetail = detail; recipesState.versionDetailStatus = 'ready'; recipesState.calculationTargetValue = detail.version.target_batch_size_value ?? ''; recipesState.calculationTargetUnit = detail.version.target_batch_size_unit === 'ml' ? 'ml' : 'g'; render(); return getRecipeCalculation(detail.version.id, recipesState.calculationTargetValue, recipesState.calculationTargetUnit); }).then((result)=>{ if (!result || token !== recipeVersionRefreshToken) return; recipesState.calculation = result; calculationStatus = 'ready'; render(); }).catch(()=>{ if (token !== recipeVersionRefreshToken) return; if (recipesState.versionDetailStatus === 'ready') { calculationStatus = 'error'; calculationError = 'Не удалось выполнить расчет. Состав версии открыт, попробуйте пересчитать позже.'; } else { recipesState.versionDetailStatus = 'error'; calculationStatus = 'idle'; recipesError = 'Не удалось загрузить версию рецепта.'; } render(); }); }
function submitRecipeTemplateForm(event: SubmitEvent) {
  event.preventDefault();
  if (recipeVersionSubmitting) return;
  const lifecycleToken = recipeTemplateMutationLifecycle.begin();
  if (lifecycleToken === null) return;
  const payload = recipeTemplatePayloadFromForm(event.currentTarget as HTMLFormElement);
  recipesState.templateForm = payload;
  const token = ++recipeTemplateSubmitToken;
  recipeTemplateSubmitting = true;
  recipeTemplateValidation = emptyFormValidationState();
  recipesMessage = '';
  recipesError = '';
  recipesRefreshWarning = '';
  applyValidationToRecipeTemplateForm(recipeTemplateValidation);
  disableRecipeTemplateMutationControls(document);
  createRecipeTemplate(payload).then((template)=>{
    if (token !== recipeTemplateSubmitToken) return;
    recipesMessage = 'Рецепт создан.';
    recipesError = '';
    recipeTemplateValidation = emptyFormValidationState();
    recipesState.templateForm = emptyRecipeTemplateForm();
    recipesState.showCreateForm = false;
    return Promise.all([getRecipeTemplates(), getRecipeTemplate(template.id), getRecipeVersions(template.id)]).then(([templates, opened, versions])=>{
      if (token !== recipeTemplateSubmitToken) return;
      recipesState.templates = templates.recipe_templates;
      recipesState.selectedTemplate = opened;
      recipesState.versions = versions.recipe_versions;
      recipesState.selectedVersionDetail = null;
      recipesState.versionDetailStatus = 'idle';
      recipesState.calculation = null;
      calculationStatus = 'idle';
      recipesStatus = 'ready';
      recipeTemplateSubmitting = false;
      recipeTemplateMutationLifecycle.finish(lifecycleToken);
      render();
    }).catch(()=>{
      if (token !== recipeTemplateSubmitToken) return;
      recipeTemplateSubmitting = false;
      recipeTemplateMutationLifecycle.finish(lifecycleToken);
      recipesRefreshWarning = 'Рецепт создан, но список не обновился. Нажмите «Обновить», чтобы увидеть актуальные данные.';
      recipesStatus = 'ready';
      render();
    });
  }).catch((error)=>{
    if (token !== recipeTemplateSubmitToken) return;
    recipeTemplateSubmitting = false;
    recipeTemplateMutationLifecycle.finish(lifecycleToken);
    restoreRecipeMutationControls(document);
    recipesMessage = '';
    recipesError = '';
    recipesRefreshWarning = '';
    recipeTemplateValidation = normalizeBackendValidation(apiValidationPayload(error), recipeTemplateFieldLabels, 'Не удалось создать рецепт. Проверьте поля и попробуйте ещё раз.');
    recipesStatus = 'ready';
    applyValidationToRecipeTemplateForm(recipeTemplateValidation);
    announceAssertive('Проверьте рецепт. Ошибки показаны рядом с полями.');
  });
}
function reloadRecipeCatalogData() { return Promise.all([getRecipeTemplates(), getRecipeCatalogCategories(), getRecipeCatalogTags()]).then(([templates, categories, tags]) => { recipesState.templates = templates.recipe_templates; recipesState.catalogCategories = categories.categories; recipesState.catalogTags = tags.tags; if (recipesState.selectedTemplate) recipesState.selectedTemplate = templates.recipe_templates.find((template) => template.id === recipesState.selectedTemplate?.id) ?? recipesState.selectedTemplate; recipesStatus = 'ready'; }); }
function submitRecipeCatalogCategoryForm(event: SubmitEvent) { event.preventDefault(); const name = String(new FormData(event.currentTarget as HTMLFormElement).get('name') ?? '').trim(); if (!name) { recipesError = 'Укажите название группы, например «Кремы».'; recipesMessage = ''; render(); return; } recipesState.catalogCreating = 'category'; recipesError = ''; render(); createRecipeCatalogCategory(name).then(() => reloadRecipeCatalogData()).then(() => { recipesMessage = 'Группа рецептов создана.'; recipesState.catalogCreating = null; render(); }).catch(() => { recipesState.catalogCreating = null; recipesMessage = ''; recipesError = 'Не удалось создать группу рецептов. Проверьте название и попробуйте еще раз.'; render(); }); }
function submitRecipeCatalogTagForm(event: SubmitEvent) { event.preventDefault(); const name = String(new FormData(event.currentTarget as HTMLFormElement).get('name') ?? '').trim(); if (!name) { recipesError = 'Укажите название метки, например «Для сухой кожи».'; recipesMessage = ''; render(); return; } recipesState.catalogCreating = 'tag'; recipesError = ''; render(); createRecipeCatalogTag(name).then(() => reloadRecipeCatalogData()).then(() => { recipesMessage = 'Метка рецепта создана.'; recipesState.catalogCreating = null; render(); }).catch(() => { recipesState.catalogCreating = null; recipesMessage = ''; recipesError = 'Не удалось создать метку рецепта. Проверьте название и попробуйте еще раз.'; render(); }); }
function assignRecipeCategory(recipeTemplateId: number, value: string) { if (!recipeTemplateId) return; recipesState.catalogSaving = 'saving'; recipesError = ''; render(); updateRecipeCatalogCategory(recipeTemplateId, value ? Number(value) : null).then(() => reloadRecipeCatalogData()).then(() => { recipesMessage = 'Моя группа рецепта сохранена.'; recipesState.catalogSaving = 'idle'; render(); }).catch(() => { recipesState.catalogSaving = 'idle'; recipesMessage = ''; recipesError = 'Не удалось сохранить группу рецепта. Проверьте, что группа активна, и попробуйте еще раз.'; render(); }); }
function assignRecipeTags(recipeTemplateId: number) { if (!recipeTemplateId) return; const tagIds = Array.from(document.querySelectorAll<HTMLInputElement>(`[data-action="toggle-recipe-tag"][data-recipe-template-id="${recipeTemplateId}"]:checked`)).map((input) => Number(input.value)); recipesState.catalogSaving = 'saving'; recipesError = ''; render(); updateRecipeCatalogTags(recipeTemplateId, tagIds).then(() => reloadRecipeCatalogData()).then(() => { recipesMessage = 'Метки рецепта сохранены.'; recipesState.catalogSaving = 'idle'; render(); }).catch(() => { recipesState.catalogSaving = 'idle'; recipesMessage = ''; recipesError = 'Не удалось сохранить метки рецепта. Проверьте, что метки активны, и попробуйте еще раз.'; render(); }); }
function submitRecipeVersionForm(event: SubmitEvent) {
  event.preventDefault();
  if (recipeTemplateSubmitting || !recipesState.selectedTemplate) return;
  const lifecycleToken = recipeVersionMutationLifecycle.begin();
  if (lifecycleToken === null) return;
  const templateId = recipesState.selectedTemplate.id;
  const form = recipeVersionFormFromForm(event.currentTarget as HTMLFormElement);
  recipesState.versionForm = form;
  const token = ++recipeVersionSubmitToken;
  const refreshToken = ++recipeVersionRefreshToken;
  recipeVersionSubmitting = true;
  recipeVersionValidation = emptyFormValidationState();
  recipesMessage = '';
  recipesError = '';
  recipesRefreshWarning = '';
  applyValidationToRecipeVersionForm(recipeVersionValidation);
  disableRecipeVersionMutationControls(document);
  createRecipeVersion(templateId, recipeVersionPayload(form)).then((detail)=>{
    if (token !== recipeVersionSubmitToken || recipesState.selectedTemplate?.id !== templateId) return;
    recipesMessage = 'Новая версия рецепта сохранена. Теперь ее можно использовать для индивидуального рецепта клиента.';
    recipesError = '';
    recipeVersionValidation = emptyFormValidationState();
    recipesState.versionForm = emptyRecipeVersionForm();
    recipesState.selectedVersionDetail = detail;
    recipesState.versionDetailStatus = 'ready';
    return Promise.all([getRecipeVersions(templateId), getRecipeVersionDetail(detail.version.id), getRecipeCalculation(detail.version.id, detail.version.target_batch_size_value ?? '', detail.version.target_batch_size_unit === 'ml' ? 'ml' : 'g')]).then(([versions, opened, calculation])=>{
      if (token !== recipeVersionSubmitToken || refreshToken !== recipeVersionRefreshToken || recipesState.selectedTemplate?.id !== templateId) return;
      recipesState.versions = versions.recipe_versions;
      recipesState.selectedVersionDetail = opened;
      recipesState.versionDetailStatus = 'ready';
      recipesState.calculationTargetValue = opened.version.target_batch_size_value ?? '';
      recipesState.calculationTargetUnit = opened.version.target_batch_size_unit === 'ml' ? 'ml' : 'g';
      recipesState.calculation = calculation;
      calculationStatus = 'ready';
      recipeVersionSubmitting = false;
      recipeVersionMutationLifecycle.finish(lifecycleToken);
      render();
    }).catch(()=>{
      if (token !== recipeVersionSubmitToken || refreshToken !== recipeVersionRefreshToken || recipesState.selectedTemplate?.id !== templateId) return;
      recipeVersionSubmitting = false;
      recipeVersionMutationLifecycle.finish(lifecycleToken);
      recipesRefreshWarning = 'Версия сохранена, но список или расчёт не обновились. Нажмите «Обновить» или откройте версию из списка.';
      render();
    });
  }).catch((error)=>{
    if (token !== recipeVersionSubmitToken || recipesState.selectedTemplate?.id !== templateId) return;
    recipeVersionSubmitting = false;
    recipeVersionMutationLifecycle.finish(lifecycleToken);
    restoreRecipeMutationControls(document);
    recipesMessage = '';
    recipesError = '';
    recipesRefreshWarning = '';
    recipeVersionValidation = normalizeBackendValidation(apiValidationPayload(error), recipeVersionFieldLabels(form), 'Не удалось сохранить версию. Проверьте строки состава и попробуйте ещё раз.');
    applyValidationToRecipeVersionForm(recipeVersionValidation);
    announceAssertive('Проверьте версию рецепта. Ошибки показаны рядом с полями.');
  });
}
function submitCalculationForm(event: SubmitEvent) { event.preventDefault(); const detail = recipesState.selectedVersionDetail; if (!detail) return; const data = new FormData(event.currentTarget as HTMLFormElement); const value = String(data.get('target_batch_size_value') ?? '').trim(); const unit = String(data.get('target_batch_size_unit') ?? 'g'); recipesState.calculationTargetValue = value; recipesState.calculationTargetUnit = unit; calculationStatus = 'loading'; calculationError = ''; render(); getRecipeCalculation(detail.version.id, value, unit).then((result)=>{ recipesState.calculation = result; calculationStatus = 'ready'; render(); }).catch(()=>{ calculationStatus = 'error'; calculationError = 'Не удалось выполнить расчет. Проверьте размер партии и попробуйте еще раз.'; render(); }); }


function loadPackagingItems(force = false) {
  if (!force && (packagingItemsStatus === 'loading' || packagingItemsStatus === 'ready')) return;
  packagingItemsStatus = 'loading'; packagingItemsError = ''; render();
  Promise.all([getPackagingItems(), getPackagingCatalogCategories(), getPackagingCatalogTags()]).then(([response, categories, tags]) => { packagingItemsState.items = response.packaging_items; packagingItemsState.catalogCategories = categories.categories; packagingItemsState.catalogTags = tags.tags; packagingItemsStatus = 'ready'; render(); }).catch(() => { packagingItemsStatus = 'error'; packagingItemsError = 'Не получилось загрузить справочник тары.'; render(); });
}
function startEditPackagingItem(id: number) {
  if (packagingPageMutationActive()) return;
  const item = packagingItemsState.items.find((packagingItem) => packagingItem.id === id);
  const current = packagingItemsState.formMode === 'edit' && packagingItemsState.form.id ? packagingItemsState.items.find((packagingItem) => packagingItem.id === packagingItemsState.form.id) ?? null : null;
  if (!item || !confirmDiscardDirtyAssignment(assignmentDraftIsDirty(current, packagingItemsState.assignmentDraft))) return;
  packagingItemSubmitToken += 1;
  packagingItemValidation = emptyFormValidationState();
  packagingItemsRefreshWarning = '';
  packagingItemsState.formMode = 'edit'; packagingItemsState.showCreateForm = false; packagingItemsState.form = { id: item.id, name: item.name, kind: item.kind, unit: item.unit, capacity_value: item.capacity_value, capacity_unit: item.capacity_unit, material: item.material, supplier_hint: item.supplier_hint, unit_cost: item.unit_cost, notes: item.notes }; packagingItemsState.assignmentDraft = assignmentDraftFromItem(item); packagingItemsMessage = ''; packagingItemsError = ''; render(); focusPackagingFormName();
}
function openPackagingCreateForm() {
  if (packagingPageMutationActive()) return;
  const current = packagingItemsState.formMode === 'edit' && packagingItemsState.form.id ? packagingItemsState.items.find((packagingItem) => packagingItem.id === packagingItemsState.form.id) ?? null : null;
  if (!confirmDiscardDirtyAssignment(assignmentDraftIsDirty(current, packagingItemsState.assignmentDraft))) return;
  packagingItemSubmitToken += 1;
  packagingItemValidation = emptyFormValidationState();
  packagingItemsRefreshWarning = '';
  packagingItemsState.formMode = 'create'; packagingItemsState.showCreateForm = true; packagingItemsState.form = emptyPackagingItemForm(); packagingItemsState.assignmentDraft = emptyAssignmentDraft(); packagingItemsMessage = ''; packagingItemsError = ''; render(); focusPackagingFormName();
}
function hidePackagingCreateForm() {
  if (packagingPageMutationActive()) return;
  packagingItemSubmitToken += 1;
  packagingItemValidation = emptyFormValidationState();
  packagingItemsRefreshWarning = '';
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
  if (packagingPageMutationActive()) return;
  const current = packagingItemsState.formMode === 'edit' && packagingItemsState.form.id ? packagingItemsState.items.find((packagingItem) => packagingItem.id === packagingItemsState.form.id) ?? null : null;
  if (!confirmDiscardDirtyAssignment(assignmentDraftIsDirty(current, packagingItemsState.assignmentDraft))) return;
  packagingItemSubmitToken += 1;
  packagingItemValidation = emptyFormValidationState();
  packagingItemsRefreshWarning = '';
  packagingItemsState.formMode = 'create'; packagingItemsState.showCreateForm = false; packagingItemsState.form = emptyPackagingItemForm(); packagingItemsState.assignmentDraft = emptyAssignmentDraft(); packagingItemsMessage = ''; packagingItemsError = ''; render();
}
function submitPackagingItemForm(event: SubmitEvent) {
  event.preventDefault();
  if (packagingPageMutationActive()) return;
  const isEdit = packagingItemsState.formMode === 'edit' && Boolean(packagingItemsState.form.id);
  const submittedId = packagingItemsState.form.id;
  const payload = packagingItemPayloadFromForm(event.currentTarget as HTMLFormElement);
  packagingItemsState.form = { ...payload, id: isEdit ? submittedId : null };
  const token = ++packagingItemSubmitToken;
  packagingItemSubmitting = true;
  packagingItemValidation = emptyFormValidationState();
  packagingItemsMessage = '';
  packagingItemsError = '';
  packagingItemsRefreshWarning = '';
  applyValidationToPackagingItemForm(packagingItemValidation);
  disablePackagingItemSubmitControls();
  const request = isEdit && submittedId ? updatePackagingItem(submittedId, payload) : createPackagingItem(payload);
  request.then((saved) => {
    if (token !== packagingItemSubmitToken) return;
    packagingItemsMessage = isEdit ? 'Тара сохранена. Остатки не изменялись.' : 'Тара создана. Остатки добавляются отдельными складскими операциями.';
    packagingItemsError = '';
    packagingItemValidation = emptyFormValidationState();
    packagingItemsState.formMode = isEdit ? 'edit' : 'create';
    packagingItemsState.showCreateForm = false;
    packagingItemsState.form = isEdit ? { ...payload, id: saved.id } : emptyPackagingItemForm();
    return getPackagingItems().then((response) => {
      if (token !== packagingItemSubmitToken) return;
      packagingItemsState.items = response.packaging_items;
      packagingItemsStatus = 'ready';
      packagingItemSubmitting = false;
      render();
    }).catch(() => {
      if (token !== packagingItemSubmitToken) return;
      packagingItemsRefreshWarning = 'Тара сохранена, но список не обновился. Нажмите «Обновить список», чтобы увидеть актуальные данные.';
      packagingItemsStatus = 'ready';
      packagingItemSubmitting = false;
      render();
    });
  }).catch((error) => {
    if (token !== packagingItemSubmitToken) return;
    packagingItemSubmitting = false;
    packagingItemsMessage = '';
    packagingItemsError = '';
    packagingItemsRefreshWarning = '';
    packagingItemValidation = normalizeBackendValidation(apiValidationPayload(error), packagingItemFieldLabels, 'Не удалось сохранить тару. Проверьте название, тип, единицы и числовые поля.');
    packagingItemsStatus = 'ready';
    applyValidationToPackagingItemForm(packagingItemValidation);
    reenablePackagingItemSubmitButtons();
    announceAssertive('Проверьте форму тары. Ошибки показаны рядом с полями.');
  });
}
function deactivatePackagingItem(id: number) {
  if (packagingPageMutationActive()) return;
  const item = packagingItemsState.items.find((packagingItem) => packagingItem.id === id);
  if (!item || !window.confirm(`Деактивировать тару «${item.name}»? Она не будет удалена из истории.`)) return;
  packagingItemDeactivatingId = id;
  packagingItemsError = '';
  render();
  deactivatePackagingItemRequest(id).then(() => { packagingItemsMessage = 'Тара деактивирована. История и остатки склада не изменялись.'; packagingItemsError = ''; return getPackagingItems(); }).then((response) => { packagingItemsState.items = response.packaging_items; packagingItemsStatus = 'ready'; packagingItemDeactivatingId = null; render(); }).catch(() => { packagingItemDeactivatingId = null; packagingItemsMessage = ''; packagingItemsError = 'Не удалось деактивировать тару. Попробуйте еще раз.'; packagingItemsStatus = 'ready'; render(); });
}

function reloadPackagingCatalogData() { return Promise.all([getPackagingItems(), getPackagingCatalogCategories(), getPackagingCatalogTags()]).then(([items, categories, tags]) => { packagingItemsState.items = items.packaging_items; packagingItemsState.catalogCategories = categories.categories; packagingItemsState.catalogTags = tags.tags; packagingItemsStatus = 'ready'; }); }
function submitPackagingCatalogCategoryForm(event: SubmitEvent) { event.preventDefault(); if (packagingPageMutationActive()) return; const name = String(new FormData(event.currentTarget as HTMLFormElement).get('name') ?? '').trim(); if (!name) return; packagingItemsState.catalogCreating = 'category'; packagingItemsError = ''; render(); createPackagingCatalogCategory(name).then(() => reloadPackagingCatalogData()).then(() => { packagingItemsMessage = 'Группа тары создана.'; packagingItemsState.catalogCreating = null; render(); }).catch(() => { packagingItemsState.catalogCreating = null; packagingItemsError = 'Не удалось создать группу тары. Проверьте название и попробуйте еще раз.'; render(); }); }
function submitPackagingCatalogTagForm(event: SubmitEvent) { event.preventDefault(); if (packagingPageMutationActive()) return; const name = String(new FormData(event.currentTarget as HTMLFormElement).get('name') ?? '').trim(); if (!name) return; packagingItemsState.catalogCreating = 'tag'; packagingItemsError = ''; render(); createPackagingCatalogTag(name).then(() => reloadPackagingCatalogData()).then(() => { packagingItemsMessage = 'Метка тары создана.'; packagingItemsState.catalogCreating = null; render(); }).catch(() => { packagingItemsState.catalogCreating = null; packagingItemsError = 'Не удалось создать метку тары. Проверьте название и попробуйте еще раз.'; render(); }); }
function updatePackagingDraftCategory(packagingItemId: number, value: string) { if (packagingPageMutationActive()) return; if (packagingItemsState.assignmentDraft.itemId !== packagingItemId) return; updateDraftCategory(packagingItemsState.assignmentDraft, value); packagingItemsMessage = ''; render(); }
function updatePackagingDraftTag(packagingItemId: number, tagId: number, checked: boolean) { if (packagingPageMutationActive()) return; if (packagingItemsState.assignmentDraft.itemId !== packagingItemId || !tagId) return; updateDraftTag(packagingItemsState.assignmentDraft, tagId, checked); packagingItemsMessage = ''; render(); }
function resetPackagingAssignmentDraft() { if (packagingPageMutationActive()) return; const item = packagingItemsState.form.id ? packagingItemsState.items.find((packagingItem) => packagingItem.id === packagingItemsState.form.id) ?? null : null; packagingItemsState.assignmentDraft = resetAssignmentDraft(item); packagingItemsMessage = ''; render(); }
function applyPackagingAssignmentDraft() {
  if (packagingPageMutationActive()) return;
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
    .catch(() => { ingredientLotsStatus = 'error'; ingredientLotsError = 'Не удалось получить данные о партиях.'; render(); });
}
function openIngredientLotCreateForm() { if (ingredientLotSubmitting) return; ingredientLotSubmitToken += 1; ingredientLotsState.formMode = 'create'; ingredientLotsState.form = emptyIngredientLotForm(); ingredientLotsMessage = ''; ingredientLotsError = ''; ingredientLotsRefreshWarning = ''; ingredientLotValidation = emptyFormValidationState(); render(); }
function startEditIngredientLot(id: number) { if (ingredientLotSubmitting) return; ingredientLotSubmitToken += 1; const lot = ingredientLotsState.lots.find((item) => item.id === id); if (!lot) return; ingredientLotsState.formMode = 'edit'; ingredientLotsState.form = { id: lot.id, ingredient_id: String(lot.ingredient_id), lot_code: lot.lot_code, supplier_name: lot.supplier_name, purchased_at: lot.purchased_at ?? '', expires_at: lot.expires_at ?? '', unit: lot.unit, unit_cost: lot.unit_cost ?? '', total_cost: lot.total_cost ?? '', density_g_per_ml: lot.density_g_per_ml ?? '', notes: lot.notes }; ingredientLotsMessage = ''; ingredientLotsError = ''; ingredientLotsRefreshWarning = ''; ingredientLotValidation = emptyFormValidationState(); render(); }
function submitIngredientLotForm(event: SubmitEvent) {
  event.preventDefault();
  if (ingredientLotSubmitting) return;
  const form = event.currentTarget as HTMLFormElement;
  const isEdit = Boolean(ingredientLotsState.formMode === 'edit' && ingredientLotsState.form.id);
  const submittedFormId = ingredientLotsState.form.id;
  const payload = ingredientLotPayloadFromForm(form);
  ingredientLotsState.form = { id: isEdit ? submittedFormId : null, ingredient_id: String(payload.ingredient_id || ''), lot_code: payload.lot_code, supplier_name: payload.supplier_name, purchased_at: payload.purchased_at ?? '', expires_at: payload.expires_at ?? '', unit: payload.unit, unit_cost: payload.unit_cost ?? '', total_cost: payload.total_cost ?? '', density_g_per_ml: payload.density_g_per_ml ?? '', notes: payload.notes };
  const token = ++ingredientLotSubmitToken;
  ingredientLotSubmitting = true;
  ingredientLotValidation = emptyFormValidationState();
  applyValidationToIngredientLotForm(ingredientLotValidation);
  ingredientLotsMessage = '';
  ingredientLotsError = '';
  ingredientLotsRefreshWarning = '';
  disableIngredientLotFormButtons();
  const request = isEdit ? updateIngredientLot(submittedFormId!, payload) : createIngredientLot(payload);
  request.then(() => {
    if (token !== ingredientLotSubmitToken) return;
    ingredientLotsMessage = isEdit ? 'Партия сохранена. Остаток не изменялся.' : 'Партия создана. Количество добавляется отдельным движением сырья.';
    ingredientLotsError = '';
    ingredientLotsRefreshWarning = '';
    ingredientLotValidation = emptyFormValidationState();
    ingredientLotsState.formMode = 'create';
    ingredientLotsState.form = emptyIngredientLotForm();
    ingredientLotsStatus = 'ready';
    render();
    getIngredientLots()
      .then((response) => {
        if (token !== ingredientLotSubmitToken) return;
        ingredientLotsState.lots = response.lots;
        ingredientLotsStatus = 'ready';
        ingredientLotSubmitting = false;
        render();
      })
      .catch(() => {
        if (token !== ingredientLotSubmitToken) return;
        ingredientLotSubmitting = false;
        ingredientLotsRefreshWarning = 'Партия сохранена, но список не обновился. Нажмите «Обновить», чтобы получить актуальные данные.';
        ingredientLotsStatus = 'ready';
        render();
      });
  }).catch((error) => {
    if (token !== ingredientLotSubmitToken) return;
    ingredientLotSubmitting = false;
    ingredientLotsMessage = '';
    ingredientLotsError = '';
    ingredientLotsRefreshWarning = '';
    ingredientLotValidation = normalizeBackendValidation(apiValidationPayload(error), ingredientLotFieldLabels, 'Не удалось сохранить партию. Проверьте поля и попробуйте ещё раз.');
    ingredientLotsStatus = 'ready';
    applyValidationToIngredientLotForm(ingredientLotValidation);
    reenableIngredientLotSubmitButtons();
    announceAssertive('Проверьте форму партии. Ошибки показаны рядом с полями.');
  });
}
function deactivateIngredientLot(id: number) {
  if (ingredientLotSubmitting) return;
  const lot = ingredientLotsState.lots.find((item) => item.id === id);
  if (!lot || !window.confirm(`Деактивировать партию «${lot.lot_code || lotIngredientName(lot.ingredient_id)}»? Она не будет удалена из истории.`)) return;
  deactivateIngredientLotRequest(id).then(() => { ingredientLotsMessage = 'Партия деактивирована. История склада не изменялась.'; ingredientLotsError = ''; return getIngredientLots(); }).then((response) => { ingredientLotsState.lots = response.lots; ingredientLotsStatus = 'ready'; render(); }).catch(() => { ingredientLotsMessage = ''; ingredientLotsError = 'Не удалось деактивировать партию. Попробуйте еще раз.'; ingredientLotsStatus = 'ready'; render(); });
}

function loadIngredients(force = false) {
  if (!force && (ingredientsStatus === 'loading' || ingredientsStatus === 'ready')) return;
  ingredientsStatus = 'loading'; ingredientsError = ''; render();
  Promise.all([getIngredients(), getIngredientCatalogCategories(), getIngredientCatalogTags()]).then(([response, categories, tags]) => { ingredientsState.items = response.ingredients; ingredientsState.catalogCategories = categories.categories; ingredientsState.catalogTags = tags.tags; ingredientsStatus = 'ready'; render(); }).catch(() => { ingredientsStatus = 'error'; ingredientsError = 'Не получилось загрузить справочник компонентов или каталог групп и меток.'; render(); });
}
function submitIngredientForm(event: SubmitEvent) {
  event.preventDefault();
  if (ingredientSubmitting) return;
  const form = event.currentTarget as HTMLFormElement;
  const isEdit = Boolean(ingredientsState.formMode === 'edit' && ingredientsState.form.id);
  const submittedFormId = ingredientsState.form.id;
  const payload = ingredientPayloadFromForm(form);
  ingredientsState.form = { ...payload, id: isEdit ? submittedFormId : null };
  const token = ++ingredientSubmitToken;
  ingredientSubmitting = true;
  ingredientValidation = emptyFormValidationState();
  ingredientsMessage = '';
  ingredientsError = '';
  ingredientsRefreshWarning = '';
  disableIngredientFormButtons();
  const request = isEdit ? updateIngredient(submittedFormId!, payload) : createIngredient(payload);
  request.then(() => {
    if (token !== ingredientSubmitToken) return;
    ingredientsMessage = isEdit ? 'Компонент сохранен.' : 'Компонент создан.';
    ingredientsError = '';
    ingredientsRefreshWarning = '';
    ingredientValidation = emptyFormValidationState();
    ingredientsState.formMode = 'create';
    ingredientsState.form = emptyIngredientForm();
    ingredientsState.showCreateForm = false;
    ingredientsStatus = 'ready';
    render();
    getIngredients()
      .then((response) => {
        if (token !== ingredientSubmitToken) return;
        ingredientsState.items = response.ingredients;
        if (recipesStatus === 'ready') setRecipeIngredientOptions(response.ingredients);
        ingredientsStatus = 'ready';
        ingredientSubmitting = false;
        render();
      })
      .catch(() => {
        if (token !== ingredientSubmitToken) return;
        ingredientSubmitting = false;
        ingredientsRefreshWarning = 'Компонент сохранён, но список не обновился. Нажмите «Обновить список», чтобы получить актуальные данные.';
        ingredientsStatus = 'ready';
        render();
      });
  }).catch((error) => {
    if (token !== ingredientSubmitToken) return;
    ingredientSubmitting = false;
    ingredientsMessage = '';
    ingredientsError = '';
    ingredientsRefreshWarning = '';
    ingredientValidation = normalizeBackendValidation(apiValidationPayload(error), ingredientFieldLabels, 'Не удалось сохранить компонент. Проверьте поля и попробуйте ещё раз.');
    ingredientsStatus = 'ready';
    applyValidationToIngredientForm(ingredientValidation);
    reenableIngredientSubmitButtons();
    announceAssertive('Проверьте форму компонента. Ошибки показаны рядом с полями.');
  });
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


function loadReportDocuments(force = false) {
  if (!force && (reportDocumentsUiState.status === 'loading' || reportDocumentsUiState.status === 'ready')) return;
  reportDocumentsUiState.status = 'loading';
  reportDocumentsUiState.error = '';
  if (force) reportDocumentsUiState.message = '';
  render();
  Promise.all([getReportDocumentStatus(), getReportDocuments()])
    .then(([status, list]) => { reportDocumentsUiState.status = 'ready'; reportDocumentsUiState.documentStatus = status; reportDocumentsUiState.documents = list.items; reportDocumentsUiState.error = ''; render(); })
    .catch(() => { reportDocumentsUiState.status = 'error'; reportDocumentsUiState.error = 'Не удалось загрузить документы отчётов. Проверьте, что приложение запущено, и попробуйте снова.'; render(); });
}

function submitReportDocumentCreateForm(event: SubmitEvent) { event.preventDefault(); const submitter = event.submitter instanceof HTMLButtonElement ? event.submitter : null; createReportDocumentFromUi(submitter?.dataset.format === 'pdf' ? 'pdf' : 'markdown'); }
function createReportDocumentFromUi(format: 'markdown' | 'pdf' = 'markdown') {
  if (reportDocumentsUiState.actionStatus === 'creating') return;
  if (!reportDocumentsUiState.documentStatus?.can_create) { reportDocumentsUiState.error = 'Создание документа сейчас недоступно.'; reportDocumentsUiState.message = ''; render(); return; }
  const reason = reportDocumentsUiState.reason.trim();
  reportDocumentsUiState.actionStatus = 'creating'; reportDocumentsUiState.error = ''; reportDocumentsUiState.message = ''; clearFeedbackAnnouncement(); render();
  createOverviewReportDocument({ format, ...(reason ? { reason } : {}) })
    .then((response) => {
      reportDocumentsUiState.lastCreatedDocument = response.document;
      reportDocumentsUiState.reason = '';
      const successMessage = `${response.message || 'Документ создан.'} Его можно открыть или скачать из списка ниже.`;
      reportDocumentsUiState.message = successMessage;
      announcePolite(successMessage);
      return Promise.all([getReportDocumentStatus(), getReportDocuments()])
        .then(([status, list]) => { reportDocumentsUiState.documentStatus = status; reportDocumentsUiState.documents = list.items; reportDocumentsUiState.status = 'ready'; reportDocumentsUiState.actionStatus = 'idle'; render(); })
        .catch(() => { reportDocumentsUiState.status = 'ready'; reportDocumentsUiState.actionStatus = 'idle'; reportDocumentsUiState.error = ''; reportDocumentsUiState.message = `${successMessage} Не удалось обновить список документов. Нажмите «Обновить список», чтобы перечитать данные.`; render(); });
    })
    .catch((error: unknown) => { const detail = error instanceof Error && error.message && error.message !== 'API request failed' ? ` ${error.message}` : ''; reportDocumentsUiState.actionStatus = 'idle'; reportDocumentsUiState.error = `Не удалось создать документ отчёта. Данные мастерской не изменялись.${detail}`; reportDocumentsUiState.message = ''; announceAssertive(reportDocumentsUiState.error); render(); });
}

function loadReports(force = false) {
  if (!force && (reportsUiState.status === 'loading' || reportsUiState.status === 'ready')) return;
  reportsUiState.status = 'loading'; reportsUiState.error = ''; reportsUiState.message = ''; render();
  Promise.all([getReportsOverview(), getInventoryReport(), getOrdersReport(), getProductionReport(), getFinanceReport()])
    .then(([overview, inventory, orders, production, finance]) => { reportsUiState = { ...reportsUiState, status: 'ready', error: '', message: force ? 'Отчёты обновлены. Показаны актуальные данные мастерской.' : '', overview, inventory, orders, production, finance }; render(); })
    .catch((error: unknown) => { reportsUiState.status = 'error'; const message = error instanceof Error && error.message && error.message !== 'API request failed' ? error.message : 'Не удалось загрузить отчёты. Проверьте, что приложение запущено, и попробуйте снова.'; reportsUiState.error = message; reportsUiState.message = ''; render(); });
}

function loadInventory(force = false) {
  if (!force && (inventoryStatus === 'loading' || inventoryStatus === 'ready')) return;
  inventoryStatus = 'loading'; inventoryError = ''; render();
  Promise.all([getInventoryOverview(), getIngredientLotBalances(), getPackagingBalances()])
    .then(([overview, lots, packaging]) => { inventoryState = { overview, ingredientLots: lots.ingredient_lot_balances, packagingItems: packaging.packaging_balances }; inventoryStatus = 'ready'; render(); })
    .catch(() => { inventoryStatus = 'error'; inventoryError = 'Не получилось загрузить складскую сводку.'; render(); });
}
function loadOnboarding() { fetch('/api/onboarding').then((response) => { if (!response.ok) throw new Error('Onboarding is unavailable'); return response.json() as Promise<OnboardingState>; }).then((state) => { onboardingState = state; onboardingStatus = 'ready'; onboardingMessage = ''; render(); }).catch(() => { onboardingStatus = 'unavailable'; render(); }); }
function updateOnboarding(url: string, body?: Record<string, string>) { fetch(url, { method: 'POST', headers: body ? { 'Content-Type': 'application/json' } : undefined, body: body ? JSON.stringify(body) : undefined }).then((response) => { if (!response.ok) throw new Error('Onboarding update failed'); return response.json() as Promise<OnboardingState>; }).then((state) => { onboardingState = state; onboardingStatus = 'ready'; onboardingMessage = 'Сохранено в локальном рабочем пространстве.'; render(); }).catch(() => { onboardingStatus = 'unavailable'; onboardingMessage = ''; render(); }); }

window.addEventListener('popstate', () => { activeSection = sectionFromLocation(); loadSectionData(activeSection); render(); });
ensureAnnouncementRegions();
render();
fetch('/api/health').then((response) => { healthStatus = response.ok ? 'online' : 'offline'; render(); }).catch(() => { healthStatus = 'offline'; render(); });
loadOnboarding();
loadSectionData(activeSection);

function updateWorkshopProfileDraft(event: Event) {
  if (!isWorkshopProfileFormAvailable()) return;
  const target = event.currentTarget as HTMLInputElement | HTMLTextAreaElement;
  const field = target.dataset.workshopProfileField as keyof WorkshopProfile | undefined;
  if (!field) return;
  workshopProfileUiState.draft = { ...workshopProfileUiState.draft, [field]: target.value };
  if (workshopProfileUiState.error || workshopProfileUiState.message) clearFeedbackAnnouncement();
  workshopProfileUiState.error = ''; workshopProfileUiState.message = '';
  syncWorkshopProfileDraftUi();
}
function cancelWorkshopProfileChanges() { const profile = workshopProfileUiState.profile; if (!isWorkshopProfileFormAvailable() || profile === null || !isWorkshopProfileDirty()) return; clearFeedbackAnnouncement(); workshopProfileUiState.draft = { ...profile }; workshopProfileUiState.error = ''; workshopProfileUiState.message = 'Несохранённые изменения отменены. Восстановлена последняя сохранённая версия.'; announcePolite(workshopProfileUiState.message); render(); }
function submitWorkshopProfileForm(event: Event) { event.preventDefault(); if (!isWorkshopProfileFormAvailable() || !isWorkshopProfileDirty()) return; workshopProfileUiState.actionStatus = 'saving'; workshopProfileUiState.error = ''; workshopProfileUiState.message = ''; clearFeedbackAnnouncement(); render(); updateWorkshopProfile(workshopProfileUiState.draft).then((data) => { workshopProfileUiState = { status: 'ready', actionStatus: 'idle', profile: data.profile, draft: { ...data.profile }, error: '', message: 'Профиль мастерской сохранён. Эти данные будут добавлены только в новые документы «Сводка мастерской». Ранее созданные документы не изменятся.' }; announcePolite(workshopProfileUiState.message); render(); }).catch((error: Error) => { workshopProfileUiState.actionStatus = 'idle'; workshopProfileUiState.error = error.message || 'Не удалось сохранить профиль мастерской. Данные рецептов, склада и заказов не изменялись.'; announceAssertive(workshopProfileUiState.error); render(); }); }
