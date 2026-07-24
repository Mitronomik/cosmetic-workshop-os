import type { FormulaClientWorkspaceFeedbackLifecycle, FormulaClientRoute } from './formula-client-workspace-feedback.js';

export type FormulaClientSection = 'Рецепты' | 'Клиенты' | 'Индивидуальные рецепты';

export function formulaClientRouteForSection(section: string | null): FormulaClientRoute | null {
  if (section === 'Рецепты') return 'recipes';
  if (section === 'Клиенты') return 'clients';
  if (section === 'Индивидуальные рецепты') return 'clientRecipes';
  return null;
}

export function transitionFormulaClientRouteOwnership(
  lifecycle: FormulaClientWorkspaceFeedbackLifecycle,
  previousSection: string | null,
  nextSection: string | null,
): void {
  lifecycle.transition(formulaClientRouteForSection(previousSection), formulaClientRouteForSection(nextSection));
}
