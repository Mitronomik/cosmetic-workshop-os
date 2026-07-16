export type MutationGuardControl = HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement | HTMLButtonElement;

export function mutationDisabled(element: Element | null): void {
  if (!(element instanceof HTMLButtonElement || element instanceof HTMLSelectElement || element instanceof HTMLInputElement || element instanceof HTMLTextAreaElement)) return;
  if (element.disabled) return;
  element.disabled = true;
  element.dataset.mutationDisabled = 'true';
}

export function mutationReadonly(element: Element | null): void {
  if (!(element instanceof HTMLInputElement || element instanceof HTMLTextAreaElement)) return;
  if (element.readOnly || element.disabled) return;
  element.readOnly = true;
  element.dataset.mutationReadonly = 'true';
}

export function restoreMutationGuards(root: ParentNode = document): void {
  root.querySelectorAll<HTMLInputElement | HTMLTextAreaElement>('[data-mutation-readonly="true"]').forEach((el) => {
    el.readOnly = false;
    delete el.dataset.mutationReadonly;
  });
  root.querySelectorAll<MutationGuardControl>('[data-mutation-disabled="true"]').forEach((el) => {
    el.disabled = false;
    delete el.dataset.mutationDisabled;
  });
}

export type StockMovementLotDetailRequest = {
  readonly token: number;
  readonly lotId: number;
  readonly submitToken: number | null;
};

export function createStockMovementLotDetailLifecycle() {
  let currentToken = 0;
  return {
    invalidate(): number {
      currentToken += 1;
      return currentToken;
    },
    begin(lotId: number, submitToken: number | null = null): StockMovementLotDetailRequest {
      currentToken += 1;
      return { token: currentToken, lotId, submitToken };
    },
    isCurrent(request: StockMovementLotDetailRequest, selectedLotId: number | null, activeSubmitToken: number | null = request.submitToken): boolean {
      return request.token === currentToken
        && selectedLotId === request.lotId
        && (request.submitToken === null || activeSubmitToken === request.submitToken);
    },
    currentToken(): number {
      return currentToken;
    },
  };
}

export type PackagingPageMutationState = {
  packagingItemSubmitting: boolean;
  catalogSaving: string;
  catalogCreating: string | null;
  deactivatingId: number | null;
};

export function packagingPageMutationActiveState(state: PackagingPageMutationState): boolean {
  return state.packagingItemSubmitting || state.catalogSaving === 'saving' || state.catalogCreating !== null || state.deactivatingId !== null;
}
