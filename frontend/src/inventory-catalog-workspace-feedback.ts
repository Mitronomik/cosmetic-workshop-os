import { CoreWorkspaceFeedbackLifecycle, type WorkspaceRouteMessages } from './core-workspace-feedback.js';

export type InventoryCatalogRoute = 'inventory' | 'ingredients' | 'ingredientLots' | 'stockMovements' | 'packaging';
export type InventoryCatalogRead =
  | 'inventory-overview'
  | 'ingredient-list'
  | 'ingredient-references'
  | 'lot-list'
  | 'lot-references'
  | 'stock-references'
  | 'stock-movements'
  | 'stock-balance'
  | 'stock-reconciliation'
  | 'packaging-list'
  | 'packaging-references';
export type InventoryCatalogMutation =
  | 'ingredient-create'
  | 'ingredient-update'
  | 'ingredient-deactivate'
  | 'ingredient-category-create'
  | 'ingredient-tag-create'
  | 'ingredient-assignment'
  | 'lot-create'
  | 'lot-update'
  | 'lot-deactivate'
  | 'stock-movement-create'
  | 'packaging-create'
  | 'packaging-update'
  | 'packaging-deactivate'
  | 'packaging-category-create'
  | 'packaging-tag-create'
  | 'packaging-assignment';

const messages = (subject: string): WorkspaceRouteMessages => ({
  loading: `Загружаем ${subject}…`,
  refreshing: `Обновляем ${subject}…`,
  refreshSuccess: `${subject[0].toUpperCase()}${subject.slice(1)} обновлены.`,
  initialError: `Не удалось загрузить ${subject}. Проверьте, что локальное приложение запущено, и попробуйте снова.`,
  refreshError: `Не удалось обновить ${subject}. Ранее загруженные данные оставлены на экране.`,
  mutationBusy: 'Сохраняем изменения…',
  mutationError: 'Не удалось сохранить изменения. Проверьте поля и попробуйте ещё раз.',
  mutationAmbiguous: 'Не удалось подтвердить результат. Перед повтором обновите данные: операция могла выполниться.',
  invalidResponse: 'Локальное приложение вернуло неполный ответ. Обновите данные перед повторной попыткой.',
  reconciliationFailed: 'Не удалось подтвердить результат. Обновите данные вручную перед повторной операцией.',
});

export class InventoryCatalogWorkspaceFeedbackLifecycle extends CoreWorkspaceFeedbackLifecycle<
  InventoryCatalogRoute,
  InventoryCatalogRead,
  InventoryCatalogMutation
> {
  constructor() {
    const stockMessages = messages('движения сырья');
    stockMessages.mutationAmbiguous = 'Ответ о движении не получен. Не создавайте его повторно: сначала обновите историю и остаток выбранной партии.';
    stockMessages.reconciliationFailed = 'Не удалось проверить историю и остаток партии. Повторное создание заблокировано; нажмите «Проверить результат» ещё раз.';
    super(
      {
        inventory: messages('складскую сводку'),
        ingredients: messages('компоненты'),
        ingredientLots: messages('партии компонентов'),
        stockMovements: stockMessages,
        packaging: messages('тару'),
      },
      {
        inventory: { retry: 'core-inventory-retry', refresh: 'core-inventory-refresh', mutation: 'core-inventory-content', success: 'core-inventory-content' },
        ingredients: { retry: 'core-ingredients-retry', refresh: 'core-ingredients-refresh', mutation: 'core-ingredients-form', success: 'core-ingredients-content' },
        ingredientLots: { retry: 'core-lots-retry', refresh: 'core-lots-refresh', mutation: 'core-lots-form', success: 'core-lots-content' },
        stockMovements: { retry: 'core-stock-retry', refresh: 'core-stock-reconcile', mutation: 'core-stock-form', success: 'core-stock-content' },
        packaging: { retry: 'core-packaging-retry', refresh: 'core-packaging-refresh', mutation: 'core-packaging-form', success: 'core-packaging-content' },
      },
    );
  }
}

export const INVENTORY_CATALOG_UNSUPPORTED_OPERATIONS = Object.freeze([
  'ingredient-stock-overwrite',
  'lot-balance-overwrite',
  'stock-movement-update',
  'stock-movement-delete',
  'packaging-stock-movement',
  'packaging-stock-write-off',
] as const);

export function isInventoryEntityDto(value: unknown): value is { id: number } {
  return Boolean(value && typeof value === 'object' && Number.isInteger(Number((value as { id?: unknown }).id)) && Number((value as { id?: unknown }).id) > 0);
}

export function isStockMovementDto(value: unknown): boolean {
  if (!isInventoryEntityDto(value)) return false;
  const movement = value as { ingredient_lot_id?: unknown; movement_type?: unknown; quantity?: unknown; unit?: unknown };
  return Number.isInteger(Number(movement.ingredient_lot_id))
    && Number(movement.ingredient_lot_id) > 0
    && typeof movement.movement_type === 'string'
    && (typeof movement.quantity === 'string' || typeof movement.quantity === 'number')
    && typeof movement.unit === 'string';
}

export function isStockReconciliationDto(value: unknown): boolean {
  if (!value || typeof value !== 'object') return false;
  const result = value as { movements?: unknown; balance?: unknown };
  return Array.isArray(result.movements)
    && Boolean(result.balance && typeof result.balance === 'object' && 'ingredient_lot_id' in result.balance);
}
