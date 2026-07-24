import type { InventoryCatalogWorkspaceFeedbackLifecycle, InventoryCatalogRoute } from './inventory-catalog-workspace-feedback.js';

export function inventoryCatalogRouteForSection(section: string | null): InventoryCatalogRoute | null {
  if (section === 'Склад') return 'inventory';
  if (section === 'Компоненты') return 'ingredients';
  if (section === 'Партии') return 'ingredientLots';
  if (section === 'Движения сырья') return 'stockMovements';
  if (section === 'Тара') return 'packaging';
  return null;
}

export function transitionInventoryCatalogRouteOwnership(
  lifecycle: InventoryCatalogWorkspaceFeedbackLifecycle,
  previousSection: string | null,
  nextSection: string | null,
): void {
  lifecycle.transition(inventoryCatalogRouteForSection(previousSection), inventoryCatalogRouteForSection(nextSection));
}
