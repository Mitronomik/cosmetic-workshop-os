export type PurchaseReferenceKind = "ingredient" | "packaging";
export type PurchaseReferenceOwner = {
  requestId: number;
  routeGeneration: number;
};
export type PurchaseReferenceState<
  TIngredient = unknown,
  TPackaging = unknown,
> = {
  routeGeneration: number;
  ingredientRequest: PurchaseReferenceOwner | null;
  packagingRequest: PurchaseReferenceOwner | null;
  ingredientRequestId: number;
  packagingRequestId: number;
  ingredientsLoaded: boolean;
  packagingLoaded: boolean;
  ingredientsError: string;
  packagingError: string;
  ingredients: TIngredient[];
  packaging: TPackaging[];
};
export function createInitialPurchaseReferenceState<
  TIngredient = unknown,
  TPackaging = unknown,
>(): PurchaseReferenceState<TIngredient, TPackaging> {
  return {
    routeGeneration: 0,
    ingredientRequest: null,
    packagingRequest: null,
    ingredientRequestId: 0,
    packagingRequestId: 0,
    ingredientsLoaded: false,
    packagingLoaded: false,
    ingredientsError: "",
    packagingError: "",
    ingredients: [],
    packaging: [],
  };
}
export type PurchaseReferenceDeps<TIngredient, TPackaging> = {
  loadIngredients: () => Promise<TIngredient[]>;
  loadPackaging: () => Promise<TPackaging[]>;
  ownsRoute: () => boolean;
  render: () => void;
  applyIngredients?: (items: TIngredient[]) => void;
  applyPackaging?: (items: TPackaging[]) => void;
};
export function createPurchaseSuggestionsReferenceDataController<
  TIngredient,
  TPackaging,
>(
  state: PurchaseReferenceState<TIngredient, TPackaging>,
  deps: PurchaseReferenceDeps<TIngredient, TPackaging>,
) {
  function startIngredient() {
    if (state.ingredientsLoaded || state.ingredientRequest)
      return { accepted: false };
    const owner = {
      requestId: ++state.ingredientRequestId,
      routeGeneration: state.routeGeneration,
    };
    state.ingredientRequest = owner;
    state.ingredientsError = "";
    if (deps.ownsRoute()) deps.render();
    deps
      .loadIngredients()
      .then((items) => {
        if (
          state.ingredientRequest?.requestId !== owner.requestId ||
          state.ingredientRequest.routeGeneration !== owner.routeGeneration ||
          !deps.ownsRoute()
        )
          return;
        state.ingredientRequest = null;
        state.ingredientsLoaded = true;
        state.ingredients = items;
        state.ingredientsError = "";
        deps.applyIngredients?.(items);
        deps.render();
      })
      .catch(() => {
        if (
          state.ingredientRequest?.requestId !== owner.requestId ||
          state.ingredientRequest.routeGeneration !== owner.routeGeneration ||
          !deps.ownsRoute()
        )
          return;
        state.ingredientRequest = null;
        state.ingredientsLoaded = false;
        state.ingredientsError =
          "Не удалось загрузить компоненты для ручного предложения. Черновик сохранён.";
        deps.render();
      });
    return { accepted: true, owner };
  }
  function startPackaging() {
    if (state.packagingLoaded || state.packagingRequest)
      return { accepted: false };
    const owner = {
      requestId: ++state.packagingRequestId,
      routeGeneration: state.routeGeneration,
    };
    state.packagingRequest = owner;
    state.packagingError = "";
    if (deps.ownsRoute()) deps.render();
    deps
      .loadPackaging()
      .then((items) => {
        if (
          state.packagingRequest?.requestId !== owner.requestId ||
          state.packagingRequest.routeGeneration !== owner.routeGeneration ||
          !deps.ownsRoute()
        )
          return;
        state.packagingRequest = null;
        state.packagingLoaded = true;
        state.packaging = items;
        state.packagingError = "";
        deps.applyPackaging?.(items);
        deps.render();
      })
      .catch(() => {
        if (
          state.packagingRequest?.requestId !== owner.requestId ||
          state.packagingRequest.routeGeneration !== owner.routeGeneration ||
          !deps.ownsRoute()
        )
          return;
        state.packagingRequest = null;
        state.packagingLoaded = false;
        state.packagingError =
          "Не удалось загрузить тару для ручного предложения. Черновик сохранён.";
        deps.render();
      });
    return { accepted: true, owner };
  }
  function ensure(kind?: PurchaseReferenceKind | "all") {
    const results = [];
    if (!kind || kind === "all" || kind === "ingredient")
      results.push(startIngredient());
    if (!kind || kind === "all" || kind === "packaging")
      results.push(startPackaging());
    return results;
  }
  return {
    ensure,
    retry: ensure,
    startIngredient,
    startPackaging,
    leaveRoute() {
      state.routeGeneration += 1;
      state.ingredientRequest = null;
      state.packagingRequest = null;
    },
    selectedCatalogReady(kind: PurchaseReferenceKind) {
      return kind === "ingredient"
        ? state.ingredientsLoaded
        : state.packagingLoaded;
    },
    selectedCatalogEmpty(kind: PurchaseReferenceKind) {
      return kind === "ingredient"
        ? state.ingredientsLoaded && state.ingredients.length === 0
        : state.packagingLoaded && state.packaging.length === 0;
    },
    busy() {
      return Boolean(state.ingredientRequest || state.packagingRequest);
    },
    error() {
      return [state.ingredientsError, state.packagingError]
        .filter(Boolean)
        .join(" ");
    },
  };
}
