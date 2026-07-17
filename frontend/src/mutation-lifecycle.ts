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


export function disableRecipeTemplateMutationControls(root: ParentNode = document): void {
  const form = root.querySelector<HTMLFormElement>('[data-form="recipe-template"]');
  if (form) {
    form.setAttribute('aria-busy', 'true');
    form.querySelectorAll<HTMLInputElement | HTMLTextAreaElement>('input, textarea').forEach(mutationReadonly);
    form.querySelectorAll<HTMLButtonElement>('button').forEach(mutationDisabled);
    const submit = form.querySelector<HTMLButtonElement>('button[type="submit"]');
    if (submit) submit.textContent = 'Создаём…';
  }
  const guarded = '[data-action="reload-recipes"], [data-action="open-recipe-create"], [data-action="open-recipe"], [data-action="hide-recipe-create"], [data-action="filter-recipes-search"], [data-action="filter-recipes-category"], [data-action="filter-recipes-status"], [data-action="clear-recipe-filter"], [data-action="reset-recipe-filters"], [data-action="assign-recipe-category"], [data-action="toggle-recipe-tag"], [data-form="recipe-catalog-category"] input, [data-form="recipe-catalog-category"] button, [data-form="recipe-catalog-tag"] input, [data-form="recipe-catalog-tag"] button';
  root.querySelectorAll(guarded).forEach(mutationDisabled);
}

export function disableRecipeVersionMutationControls(root: ParentNode = document): void {
  const form = root.querySelector<HTMLFormElement>('[data-form="recipe-version"]');
  if (form) {
    form.setAttribute('aria-busy', 'true');
    form.querySelectorAll<HTMLInputElement | HTMLTextAreaElement>('input, textarea').forEach(mutationReadonly);
    form.querySelectorAll<HTMLSelectElement>('select').forEach(mutationDisabled);
    form.querySelectorAll<HTMLButtonElement>('button').forEach(mutationDisabled);
    const submit = form.querySelector<HTMLButtonElement>('button[type="submit"]');
    if (submit) submit.textContent = 'Сохраняем…';
  }
  const guarded = '[data-action="reload-recipes"], [data-action="open-recipe-create"], [data-action="open-recipe"], [data-action="close-recipe-detail"], [data-action="open-version"], [data-action="reload-recipe-ingredients"], [data-action="add-recipe-line"], [data-action="remove-recipe-line"], [data-action="filter-recipes-search"], [data-action="filter-recipes-category"], [data-action="filter-recipes-status"], [data-action="clear-recipe-filter"], [data-action="reset-recipe-filters"], [data-action="assign-recipe-category"], [data-action="toggle-recipe-tag"], [data-form="recipe-catalog-category"] input, [data-form="recipe-catalog-category"] button, [data-form="recipe-catalog-tag"] input, [data-form="recipe-catalog-tag"] button';
  root.querySelectorAll(guarded).forEach(mutationDisabled);
}

export function restoreRecipeMutationControls(root: ParentNode = document): void {
  root.querySelectorAll<HTMLFormElement>('[data-form="recipe-template"], [data-form="recipe-version"]').forEach((form) => form.removeAttribute('aria-busy'));
  restoreMutationGuards(root);
  const templateSubmit = root.querySelector<HTMLButtonElement>('[data-form="recipe-template"] button[type="submit"]');
  if (templateSubmit) templateSubmit.textContent = 'Создать рецепт';
  const versionSubmit = root.querySelector<HTMLButtonElement>('[data-form="recipe-version"] button[type="submit"]');
  if (versionSubmit) versionSubmit.textContent = 'Сохранить версию рецепта';
}


export function createRecipeMutationLifecycle() {
  let currentToken = 0;
  let active = false;
  return {
    begin(): number | null {
      if (active) return null;
      active = true;
      currentToken += 1;
      return currentToken;
    },
    invalidate(): number {
      active = false;
      currentToken += 1;
      return currentToken;
    },
    isCurrent(token: number): boolean {
      return active && token === currentToken;
    },
    finish(token: number): boolean {
      if (!active || token !== currentToken) return false;
      active = false;
      return true;
    },
    isActive(): boolean {
      return active;
    },
    currentToken(): number {
      return currentToken;
    },
  };
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


export function disableClientRecipeCreateMutationControls(root: ParentNode = document): void {
  const form = root.querySelector<HTMLFormElement>('[data-form="client-recipe"]');
  if (form) {
    form.setAttribute('aria-busy', 'true');
    form.querySelectorAll<HTMLInputElement | HTMLTextAreaElement>('input, textarea').forEach(mutationReadonly);
    form.querySelectorAll<HTMLSelectElement>('select').forEach(mutationDisabled);
    form.querySelectorAll<HTMLButtonElement>('button').forEach(mutationDisabled);
    const submit = form.querySelector<HTMLButtonElement>('button[type="submit"]');
    if (submit) submit.textContent = 'Создаём…';
  }
  const guarded = '[data-action="reload-client-recipes"], [data-action="open-client-recipe-create"], [data-action="hide-client-recipe-create"], [data-action="filter-client-recipes-search"], [data-action="filter-client-recipes-status"], [data-action="filter-client-recipes-client"], [data-action="reset-client-recipe-filters"], [data-action="clear-client-recipe-filter"], [data-action="open-client-recipe-detail"], [data-action="archive-client-recipe"], [data-action="restore-client-recipe"], [data-action="select-client-recipe-template"], [data-action="open-client-recipe-composition-editor"], [data-action="add-client-recipe-composition-line"], [data-action="remove-client-recipe-composition-line"], [data-action="move-client-recipe-composition-line"], [data-action="reset-client-recipe-composition-editor"], [data-action="close-client-recipe-composition-editor"]';
  root.querySelectorAll(guarded).forEach(mutationDisabled);
}

export function disableClientRecipeCompositionMutationControls(root: ParentNode = document): void {
  const form = root.querySelector<HTMLFormElement>('[data-form="client-recipe-composition"]');
  if (form) {
    form.setAttribute('aria-busy', 'true');
    form.querySelectorAll<HTMLInputElement | HTMLTextAreaElement>('input, textarea').forEach(mutationReadonly);
    form.querySelectorAll<HTMLSelectElement>('select').forEach(mutationDisabled);
    form.querySelectorAll<HTMLButtonElement>('button').forEach(mutationDisabled);
    const submit = form.querySelector<HTMLButtonElement>('button[type="submit"]');
    if (submit) submit.textContent = 'Сохраняем…';
  }
  const guarded = '[data-action="reload-client-recipes"], [data-action="open-client-recipe-create"], [data-action="hide-client-recipe-create"], [data-action="filter-client-recipes-search"], [data-action="filter-client-recipes-status"], [data-action="filter-client-recipes-client"], [data-action="reset-client-recipe-filters"], [data-action="clear-client-recipe-filter"], [data-action="open-client-recipe-detail"], [data-action="close-client-recipe-detail"], [data-action="archive-client-recipe"], [data-action="restore-client-recipe"], [data-action="select-client-recipe-template"], [data-action="open-client-recipe-composition-editor"], [data-action="add-client-recipe-composition-line"], [data-action="remove-client-recipe-composition-line"], [data-action="move-client-recipe-composition-line"], [data-action="reset-client-recipe-composition-editor"], [data-action="close-client-recipe-composition-editor"]';
  root.querySelectorAll(guarded).forEach(mutationDisabled);
}

export function restoreClientRecipeMutationControls(root: ParentNode = document): void {
  root.querySelectorAll<HTMLFormElement>('[data-form="client-recipe"], [data-form="client-recipe-composition"]').forEach((form) => form.removeAttribute('aria-busy'));
  restoreMutationGuards(root);
  const createSubmit = root.querySelector<HTMLButtonElement>('[data-form="client-recipe"] button[type="submit"]');
  if (createSubmit) createSubmit.textContent = 'Создать индивидуальный рецепт';
  const compositionSubmit = root.querySelector<HTMLButtonElement>('[data-form="client-recipe-composition"] button[type="submit"]');
  if (compositionSubmit) compositionSubmit.textContent = 'Сохранить состав';
}
