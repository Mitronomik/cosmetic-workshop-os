export type InventoryCatalogBindingCallbacks = {
  reloadInventory: () => void;
  reloadIngredients: () => void;
  submitIngredient: (event: Event) => void;
  reloadLots: () => void;
  submitLot: (event: Event) => void;
  reloadStock: () => void;
  reconcileStock: () => void;
  submitStockMovement: (event: Event) => void;
  reloadPackaging: () => void;
  submitPackaging: (event: Event) => void;
};

type Root = { querySelectorAll: <T = Element>(selector: string) => Iterable<T> };
type Target = { addEventListener: (type: string, listener: (event: Event) => void) => void };
const bind = (root: Root, selector: string, type: string, listener: (event: Event) => void): number => {
  let count = 0;
  for (const target of root.querySelectorAll<Target>(selector)) {
    target.addEventListener(type, listener);
    count += 1;
  }
  return count;
};

export function bindInventoryCatalogWorkspaceControls(root: Root, callbacks: InventoryCatalogBindingCallbacks) {
  return {
    inventoryReload: bind(root, '[data-action="reload-inventory"]', 'click', callbacks.reloadInventory),
    ingredientReload: bind(root, '[data-action="reload-ingredients"]', 'click', callbacks.reloadIngredients),
    ingredientForm: bind(root, '[data-form="ingredient"]', 'submit', callbacks.submitIngredient),
    lotReload: bind(root, '[data-action="reload-ingredient-lots"]', 'click', callbacks.reloadLots),
    lotForm: bind(root, '[data-form="ingredient-lot"]', 'submit', callbacks.submitLot),
    stockReload: bind(root, '[data-action="reload-stock-movements"]', 'click', callbacks.reloadStock),
    stockReconcile: bind(root, '[data-action="reconcile-stock-movement"]', 'click', callbacks.reconcileStock),
    stockForm: bind(root, '[data-form="stock-movement"]', 'submit', callbacks.submitStockMovement),
    packagingReload: bind(root, '[data-action="reload-packaging-items"]', 'click', callbacks.reloadPackaging),
    packagingForm: bind(root, '[data-form="packaging-item"]', 'submit', callbacks.submitPackaging),
  };
}
