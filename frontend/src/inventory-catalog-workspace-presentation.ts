import type { InventoryCatalogRoute, InventoryCatalogWorkspaceFeedbackLifecycle } from './inventory-catalog-workspace-feedback.js';

export function inventoryCatalogWorkspacePresentation(
  lifecycle: InventoryCatalogWorkspaceFeedbackLifecycle,
  route: InventoryCatalogRoute,
) {
  return {
    busy: lifecycle.mutationActive(route),
    hasSnapshot: lifecycle.hasSnapshot(route),
    reconciliationRequired: lifecycle.reconciliationRequired(route),
    feedback: lifecycle.feedback(route),
    canMutate: route !== 'inventory' && !lifecycle.mutationActive(route) && !lifecycle.reconciliationRequired(route),
  };
}
