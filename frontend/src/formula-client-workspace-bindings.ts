export type FormulaClientBindingCallbacks = {
  reloadRecipes: () => void;
  submitRecipeTemplate: (event: Event) => void;
  submitRecipeVersion: (event: Event) => void;
  submitRecipeCalculation: (event: Event) => void;
  reloadClients: () => void;
  submitClient: (event: Event) => void;
  submitClientWish: (event: Event) => void;
  submitClientFeedback: (event: Event) => void;
  reloadClientRecipes: () => void;
  submitClientRecipe: (event: Event) => void;
  submitClientRecipeComposition: (event: Event) => void;
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

export function bindFormulaClientWorkspaceControls(root: Root, callbacks: FormulaClientBindingCallbacks) {
  return {
    recipeReload: bind(root, '[data-action="reload-recipes"]', 'click', callbacks.reloadRecipes),
    recipeTemplateForm: bind(root, '[data-form="recipe-template"]', 'submit', callbacks.submitRecipeTemplate),
    recipeVersionForm: bind(root, '[data-form="recipe-version"]', 'submit', callbacks.submitRecipeVersion),
    recipeCalculationForm: bind(root, '[data-form="recipe-calculation"]', 'submit', callbacks.submitRecipeCalculation),
    clientReload: bind(root, '[data-action="reload-clients"]', 'click', callbacks.reloadClients),
    clientForm: bind(root, '[data-form="client"]', 'submit', callbacks.submitClient),
    clientWishForm: bind(root, '[data-form="client-wish"]', 'submit', callbacks.submitClientWish),
    clientFeedbackForm: bind(root, '[data-form="client-feedback"]', 'submit', callbacks.submitClientFeedback),
    clientRecipeReload: bind(root, '[data-action="reload-client-recipes"]', 'click', callbacks.reloadClientRecipes),
    clientRecipeForm: bind(root, '[data-form="client-recipe"]', 'submit', callbacks.submitClientRecipe),
    clientRecipeCompositionForm: bind(root, '[data-form="client-recipe-composition"]', 'submit', callbacks.submitClientRecipeComposition),
  };
}
