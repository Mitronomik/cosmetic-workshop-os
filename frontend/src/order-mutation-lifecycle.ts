import { clearFieldValidation, type FormValidationState } from './form-validation.js';

export type OrderFormMode = 'create' | 'edit';
export type OrderSourceType = 'recipe_version' | 'client_recipe';
export type OrderContextSnapshot = {
  contextToken: number;
  targetedValidationToken: number;
  formMode: OrderFormMode;
  editedOrderId: number | null;
  selectedOrderId: number | null;
  showForm: boolean;
};
export type OrderContextState = OrderContextSnapshot;

export type OrderFormErrorOrigin = 'recipe_source' | 'recipe_version_id' | 'client_recipe_id';
export type OrderValidationProvenance = { formErrors: Array<{ origin: OrderFormErrorOrigin; message: string }> };

export function emptyOrderValidationProvenance(): OrderValidationProvenance {
  return { formErrors: [] };
}

export function orderReadCanRender(snapshot: OrderContextSnapshot, current: OrderContextState): boolean {
  return snapshot.contextToken === current.contextToken
    && snapshot.targetedValidationToken === current.targetedValidationToken
    && snapshot.formMode === current.formMode
    && snapshot.editedOrderId === current.editedOrderId
    && snapshot.selectedOrderId === current.selectedOrderId
    && snapshot.showForm === current.showForm;
}

export function clearOrderSourceValidation(
  validation: FormValidationState,
  provenance: OrderValidationProvenance,
  origins: OrderFormErrorOrigin[],
): { validation: FormValidationState; provenance: OrderValidationProvenance } {
  const originSet = new Set(origins);
  let next = validation;
  for (const origin of origins) next = clearFieldValidation(next, origin === 'recipe_source' ? 'source_type' : origin);
  const removeCounts = new Map<string, number>();
  for (const item of provenance.formErrors) {
    if (originSet.has(item.origin)) removeCounts.set(item.message, (removeCounts.get(item.message) ?? 0) + 1);
  }
  const formErrors: string[] = [];
  for (const message of next.formErrors) {
    const count = removeCounts.get(message) ?? 0;
    if (count > 0) {
      removeCounts.set(message, count - 1);
      continue;
    }
    formErrors.push(message);
  }
  return {
    validation: { ...next, formErrors },
    provenance: { formErrors: provenance.formErrors.filter((item) => !originSet.has(item.origin)) },
  };
}

export type OrderPayloadDraft = {
  client_id: string;
  source_type: OrderSourceType;
  recipe_version_id: string;
  client_recipe_id: string;
  product_name: string;
  target_batch_size_value: string;
  target_batch_size_unit: string;
  packaging_item_id: string;
  packaging_quantity: string;
  sale_price: string;
  ordered_at: string;
  planned_production_at: string;
  notes: string;
};

export type OrderPayload = {
  client_id: number | null;
  recipe_version_id: number | null;
  client_recipe_id: number | null;
  product_name: string;
  target_batch_size_value: string;
  target_batch_size_unit: string;
  packaging_item_id: number | null;
  packaging_quantity: string | null;
  sale_price: string | null;
  ordered_at: string | null;
  planned_production_at: string | null;
  notes: string;
};

export function orderPayloadFromDraft(draft: OrderPayloadDraft): OrderPayload {
  return {
    client_id: Number(draft.client_id) || null,
    recipe_version_id: draft.source_type === 'recipe_version' ? Number(draft.recipe_version_id) || null : null,
    client_recipe_id: draft.source_type === 'client_recipe' ? Number(draft.client_recipe_id) || null : null,
    product_name: draft.product_name.trim(),
    target_batch_size_value: draft.target_batch_size_value,
    target_batch_size_unit: draft.target_batch_size_unit || 'g',
    packaging_item_id: draft.packaging_item_id ? Number(draft.packaging_item_id) : null,
    packaging_quantity: draft.packaging_quantity || null,
    sale_price: draft.sale_price || null,
    ordered_at: draft.ordered_at || null,
    planned_production_at: draft.planned_production_at || null,
    notes: draft.notes,
  };
}
