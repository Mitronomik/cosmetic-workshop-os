type Control = HTMLElement & { disabled?: boolean; dataset: DOMStringMap };
export type PurchaseSuggestionBindingHandlers = {
  reload?: () => void;
  resetFilters?: () => void;
  regenerate?: () => void;
  openManual?: () => void;
  reloadReferences?: () => void;
  cancelManual?: () => void;
  cancelEdit?: () => void;
  search?: (input: HTMLInputElement) => void;
  statusFilter?: (value: string) => void;
  reasonFilter?: (value: string) => void;
  itemTypeFilter?: (value: string) => void;
  manualItemType?: (value: string) => void;
  submitManual?: (event: SubmitEvent) => void;
  submitEdit?: (event: SubmitEvent) => void;
  edit?: (id: number) => void;
  markPurchased?: (id: number) => void;
  dismiss?: (id: number) => void;
};
function bindClick(
  root: ParentNode,
  selector: string,
  handler?: (el: Control, event: Event) => void,
) {
  if (!handler) return 0;
  const controls = Array.from(root.querySelectorAll<Control>(selector));
  controls.forEach((control) =>
    control.addEventListener("click", (event) => {
      if (control.disabled) return;
      handler(control, event);
    }),
  );
  return controls.length;
}
function bindChange(
  root: ParentNode,
  selector: string,
  handler?: (el: HTMLSelectElement) => void,
) {
  if (!handler) return 0;
  const controls = Array.from(
    root.querySelectorAll<HTMLSelectElement>(selector),
  );
  controls.forEach((control) =>
    control.addEventListener("change", () => handler(control)),
  );
  return controls.length;
}
function bindSubmit(
  root: ParentNode,
  selector: string,
  handler?: (event: SubmitEvent) => void,
) {
  if (!handler) return 0;
  const controls = Array.from(root.querySelectorAll<HTMLFormElement>(selector));
  controls.forEach((control) => control.addEventListener("submit", handler));
  return controls.length;
}
export function bindPurchaseSuggestionControls(
  root: ParentNode,
  handlers: PurchaseSuggestionBindingHandlers,
) {
  return {
    reload: bindClick(root, '[data-action="reload-purchase-suggestions"]', () =>
      handlers.reload?.(),
    ),
    reset: bindClick(root, '[data-action="reset-purchase-filters"]', () =>
      handlers.resetFilters?.(),
    ),
    regenerate: bindClick(
      root,
      '[data-action="regenerate-purchase-suggestions"]',
      () => handlers.regenerate?.(),
    ),
    openManual: bindClick(
      root,
      '[data-action="open-manual-purchase-form"]',
      () => handlers.openManual?.(),
    ),
    reloadReferences: bindClick(
      root,
      '[data-action="reload-purchase-references"]',
      () => handlers.reloadReferences?.(),
    ),
    cancelManual: bindClick(
      root,
      '[data-action="cancel-manual-purchase-form"]',
      () => handlers.cancelManual?.(),
    ),
    cancelEdit: bindClick(root, '[data-action="cancel-purchase-edit"]', () =>
      handlers.cancelEdit?.(),
    ),
    edit: bindClick(root, '[data-action="edit-purchase-suggestion"]', (el) =>
      handlers.edit?.(Number(el.dataset.id)),
    ),
    mark: bindClick(
      root,
      '[data-action="mark-purchase-suggestion-purchased"]',
      (el) => handlers.markPurchased?.(Number(el.dataset.id)),
    ),
    dismiss: bindClick(
      root,
      '[data-action="dismiss-purchase-suggestion"]',
      (el) => handlers.dismiss?.(Number(el.dataset.id)),
    ),
    status: bindChange(root, '[data-action="filter-purchase-status"]', (el) =>
      handlers.statusFilter?.(el.value),
    ),
    reason: bindChange(root, '[data-action="filter-purchase-reason"]', (el) =>
      handlers.reasonFilter?.(el.value),
    ),
    itemType: bindChange(
      root,
      '[data-action="filter-purchase-item-type"]',
      (el) => handlers.itemTypeFilter?.(el.value),
    ),
    manualType: bindChange(
      root,
      '[data-action="manual-purchase-item-type"]',
      (el) => handlers.manualItemType?.(el.value),
    ),
    search: (() => {
      const controls = Array.from(
        root.querySelectorAll<HTMLInputElement>(
          '[data-action="filter-purchase-search"]',
        ),
      );
      controls.forEach((control) =>
        control.addEventListener("input", () => handlers.search?.(control)),
      );
      return controls.length;
    })(),
    submitManual: bindSubmit(
      root,
      '[data-form="manual-purchase-suggestion"]',
      handlers.submitManual,
    ),
    submitEdit: bindSubmit(
      root,
      '[data-form="purchase-suggestion-edit"]',
      handlers.submitEdit,
    ),
  };
}
