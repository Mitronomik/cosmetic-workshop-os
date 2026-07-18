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


export type ClientCardRenderContextState = {
  readonly capturedClientId: number;
  readonly currentClientId: number | null;
  readonly capturedCardContextToken: number;
  readonly currentCardContextToken: number;
  readonly capturedWishContextToken: number;
  readonly currentWishContextToken: number;
  readonly wishFormDomLocked: boolean;
};

export function clientCardRenderAllowedForCapturedContext(state: ClientCardRenderContextState): boolean {
  return state.currentClientId === state.capturedClientId
    && state.currentCardContextToken === state.capturedCardContextToken
    && state.currentWishContextToken === state.capturedWishContextToken
    && !state.wishFormDomLocked;
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

export function disableClientRecipeArchiveRestoreMutationControls(root: ParentNode = document): void {
  const createForm = root.querySelector<HTMLFormElement>('[data-form="client-recipe"]');
  if (createForm) { createForm.setAttribute('aria-busy', 'true'); createForm.querySelectorAll<HTMLButtonElement>('button[type="submit"]').forEach(mutationDisabled); }
  const compositionForm = root.querySelector<HTMLFormElement>('[data-form="client-recipe-composition"]');
  if (compositionForm) { compositionForm.setAttribute('aria-busy', 'true'); compositionForm.querySelectorAll<HTMLButtonElement>('button[type="submit"]').forEach(mutationDisabled); }
  const guarded = '[data-action="reload-client-recipes"], [data-action="open-client-recipe-create"], [data-action="hide-client-recipe-create"], [data-action="open-client-recipe-detail"], [data-action="close-client-recipe-detail"], [data-action="archive-client-recipe"], [data-action="restore-client-recipe"], [data-action="select-client-recipe-template"], [data-action="open-client-recipe-composition-editor"], [data-action="add-client-recipe-composition-line"], [data-action="remove-client-recipe-composition-line"], [data-action="move-client-recipe-composition-line"], [data-action="reset-client-recipe-composition-editor"], [data-action="close-client-recipe-composition-editor"]';
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

export function createRequestGenerationLifecycle() {
  let currentToken = 0;
  return {
    begin(): number {
      currentToken += 1;
      return currentToken;
    },
    invalidate(): number {
      currentToken += 1;
      return currentToken;
    },
    isCurrent(token: number): boolean {
      return token === currentToken;
    },
    currentToken(): number {
      return currentToken;
    },
  };
}

export function disableClientWishCreateMutationControls(root: ParentNode = document): void {
  const form = root.querySelector<HTMLFormElement>('[data-form="client-wish"]');
  if (form) {
    form.setAttribute('aria-busy', 'true');
    form.querySelectorAll<HTMLInputElement | HTMLTextAreaElement>('input, textarea').forEach(mutationReadonly);
    form.querySelectorAll<HTMLSelectElement>('select').forEach(mutationDisabled);
    form.querySelectorAll<HTMLButtonElement>('button').forEach(mutationDisabled);
    const submit = form.querySelector<HTMLButtonElement>('button[type="submit"]');
    if (submit) submit.textContent = 'Сохраняем…';
  }
  const guarded = '[data-action="toggle-client-wish-form"], [data-action="close-client-wish-form"], [data-action="toggle-archived-client-wishes"], [data-action="start-client-edit"], [data-action="cancel-client-edit"], [data-action="archive-client"], [data-action="change-client-wish-status"], [data-action="archive-client-wish"], [data-action="toggle-client-feedback-form"], [data-action="close-client-feedback-form"], [data-form="client-feedback"] input, [data-form="client-feedback"] textarea, [data-form="client-feedback"] select, [data-form="client-feedback"] button';
  root.querySelectorAll(guarded).forEach(mutationDisabled);
}

export function restoreClientWishMutationControls(root: ParentNode = document): void {
  root.querySelectorAll<HTMLFormElement>('[data-form="client-wish"]').forEach((form) => form.removeAttribute('aria-busy'));
  restoreMutationGuards(root);
  const submit = root.querySelector<HTMLButtonElement>('[data-form="client-wish"] button[type="submit"]');
  if (submit) submit.textContent = 'Сохранить пожелание';
}

export type ClientRecipePageMutationState = { createSubmitting: boolean; compositionSubmitting: boolean; archiveRestoreSubmittingId: number | null };

export function clientRecipePageMutationActiveState(state: ClientRecipePageMutationState): boolean {
  return state.createSubmitting || state.compositionSubmitting || state.archiveRestoreSubmittingId !== null;
}

export type ClientRecipeCreateMutationOptions<TDetail, TList> = { lifecycle: ReturnType<typeof createRecipeMutationLifecycle>; blocked?: () => boolean; create: () => Promise<TDetail>; refresh: () => Promise<TList[]>; onStart: (token: number) => void; onCreateSuccess: (detail: TDetail, token: number) => void; onRefreshSuccess: (items: TList[], token: number) => void; onRefreshFailure: (error: unknown, token: number) => void; onCreateFailure: (error: unknown, token: number) => void; isContextCurrent?: (token: number) => boolean; onFinish: (token: number) => void };

export function runClientRecipeCreateMutation<TDetail, TList>(options: ClientRecipeCreateMutationOptions<TDetail, TList>): boolean {
  if (options.blocked?.()) return false;
  const token = options.lifecycle.begin();
  if (token === null) return false;
  const isCurrent = () => options.lifecycle.isCurrent(token) && (options.isContextCurrent?.(token) ?? true);
  options.onStart(token);
  options.create().then((detail) => {
    if (!isCurrent()) return;
    options.onCreateSuccess(detail, token);
    return options.refresh().then((items) => {
      if (!isCurrent()) return;
      options.onRefreshSuccess(items, token);
      if (options.lifecycle.finish(token)) options.onFinish(token);
    }).catch((error) => {
      if (!isCurrent()) return;
      options.onRefreshFailure(error, token);
      if (options.lifecycle.finish(token)) options.onFinish(token);
    });
  }).catch((error) => {
    if (!isCurrent()) return;
    options.onCreateFailure(error, token);
    if (options.lifecycle.finish(token)) options.onFinish(token);
  });
  return true;
}

export type ClientRecipeCompositionMutationOptions<TDetail> = { lifecycle: ReturnType<typeof createRecipeMutationLifecycle>; blocked?: () => boolean; contextId: number; update: () => Promise<TDetail>; onStart: (token: number) => void; onSuccess: (detail: TDetail, token: number) => void; onFailure: (error: unknown, token: number) => void; isContextCurrent: (contextId: number, token: number) => boolean; onFinish: (token: number) => void };

export function runClientRecipeCompositionMutation<TDetail>(options: ClientRecipeCompositionMutationOptions<TDetail>): boolean {
  if (options.blocked?.()) return false;
  const token = options.lifecycle.begin();
  if (token === null) return false;
  const isCurrent = () => options.lifecycle.isCurrent(token) && options.isContextCurrent(options.contextId, token);
  options.onStart(token);
  options.update().then((detail) => {
    if (!isCurrent()) return;
    options.onSuccess(detail, token);
    if (options.lifecycle.finish(token)) options.onFinish(token);
  }).catch((error) => {
    if (!isCurrent()) return;
    options.onFailure(error, token);
    if (options.lifecycle.finish(token)) options.onFinish(token);
  });
  return true;
}
