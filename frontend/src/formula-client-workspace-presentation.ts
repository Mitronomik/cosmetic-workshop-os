import type { FormulaClientWorkspaceFeedbackLifecycle, FormulaClientRoute } from './formula-client-workspace-feedback.js';

export function formulaClientWorkspacePresentation(
  lifecycle: FormulaClientWorkspaceFeedbackLifecycle,
  route: FormulaClientRoute,
) {
  return {
    busy: lifecycle.mutationActive(route),
    hasSnapshot: lifecycle.hasSnapshot(route),
    reconciliationRequired: lifecycle.reconciliationRequired(route),
    feedback: lifecycle.feedback(route),
    canMutate: !lifecycle.mutationActive(route) && !lifecycle.reconciliationRequired(route),
  };
}
