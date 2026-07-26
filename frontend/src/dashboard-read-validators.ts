type JsonObject = Record<string, unknown>;

const ALERT_TYPES = new Set([
  'low_ingredient_stock',
  'low_packaging_stock',
  'ingredient_expiration_soon',
  'ingredient_expired',
  'insufficient_materials_for_order',
  'insufficient_packaging_for_order',
]);
const ALERT_SEVERITIES = new Set(['info', 'warning', 'critical', 'blocking']);
const ALERT_STATUSES = new Set(['open', 'resolved', 'dismissed']);
const PURCHASE_ITEM_TYPES = new Set(['ingredient', 'packaging']);
const PURCHASE_REASONS = new Set([
  'below_minimum_stock',
  'insufficient_for_order',
  'predicted_shortage',
  'expiration_replacement',
  'manual',
]);
const PURCHASE_STATUSES = new Set(['open', 'purchased', 'dismissed', 'archived']);

function isObject(value: unknown): value is JsonObject {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function isPositiveInteger(value: unknown): value is number {
  return typeof value === 'number' && Number.isInteger(value) && value > 0;
}

function isNonNegativeInteger(value: unknown): value is number {
  return typeof value === 'number' && Number.isInteger(value) && value >= 0;
}

function isString(value: unknown): value is string {
  return typeof value === 'string';
}

function isNullableString(value: unknown): value is string | null {
  return value === null || isString(value);
}

function isNullablePositiveInteger(value: unknown): value is number | null {
  return value === null || isPositiveInteger(value);
}

function isEnumValue(value: unknown, values: Set<string>): value is string {
  return isString(value) && values.has(value);
}

function listMetadataIsValid(response: JsonObject): boolean {
  return isNonNegativeInteger(response.limit) && isNonNegativeInteger(response.offset);
}

export function clientDtoIsValid(value: unknown): boolean {
  if (!isObject(value)) return false;
  return (
    isPositiveInteger(value.id)
    && isString(value.full_name)
    && isString(value.phone)
    && isString(value.email)
    && isString(value.address)
    && isNullableString(value.birthday)
    && isString(value.skin_notes)
    && isString(value.allergy_notes)
    && isString(value.preference_notes)
    && isString(value.contraindication_notes)
    && isString(value.notes)
    && typeof value.is_active === 'boolean'
    && isString(value.created_at)
    && isString(value.updated_at)
  );
}

export function clientsListDtoIsValid(value: unknown): boolean {
  return isObject(value)
    && Array.isArray(value.clients)
    && value.clients.every(clientDtoIsValid);
}

export function alertResponseDtoIsValid(value: unknown): boolean {
  if (!isObject(value)) return false;
  return (
    isPositiveInteger(value.id)
    && isString(value.alert_key)
    && isEnumValue(value.type, ALERT_TYPES)
    && isEnumValue(value.severity, ALERT_SEVERITIES)
    && isString(value.message)
    && isString(value.related_entity_type)
    && isPositiveInteger(value.related_entity_id)
    && isString(value.recommended_action)
    && isEnumValue(value.status, ALERT_STATUSES)
    && isString(value.created_at)
    && isString(value.updated_at)
    && isNullableString(value.resolved_at)
    && isNullableString(value.dismissed_at)
  );
}

export function alertListResponseDtoIsValid(value: unknown): boolean {
  return isObject(value)
    && Array.isArray(value.alerts)
    && value.alerts.every(alertResponseDtoIsValid)
    && listMetadataIsValid(value);
}

export function purchaseSuggestionResponseDtoIsValid(value: unknown): boolean {
  if (!isObject(value)) return false;
  return (
    isPositiveInteger(value.id)
    && isString(value.suggestion_key)
    && isEnumValue(value.item_type, PURCHASE_ITEM_TYPES)
    && isPositiveInteger(value.item_id)
    && isString(value.item_name_snapshot)
    && isString(value.recommended_quantity)
    && isString(value.unit)
    && isEnumValue(value.reason, PURCHASE_REASONS)
    && isString(value.source_entity_type)
    && isNullablePositiveInteger(value.source_entity_id)
    && isString(value.message)
    && isEnumValue(value.status, PURCHASE_STATUSES)
    && isString(value.notes)
    && isString(value.created_at)
    && isString(value.updated_at)
    && isNullableString(value.resolved_at)
  );
}

export function purchaseSuggestionListResponseDtoIsValid(value: unknown): boolean {
  return isObject(value)
    && Array.isArray(value.purchase_suggestions)
    && value.purchase_suggestions.every(purchaseSuggestionResponseDtoIsValid)
    && listMetadataIsValid(value);
}

export function productionBatchListItemDtoIsValid(value: unknown): boolean {
  if (!isObject(value)) return false;
  return (
    isPositiveInteger(value.id)
    && isPositiveInteger(value.order_id)
    && isString(value.product_name)
    && isPositiveInteger(value.client_id)
    && isNullableString(value.client_name)
    && isNullablePositiveInteger(value.recipe_version_id)
    && isNullablePositiveInteger(value.client_recipe_id)
    && isString(value.final_batch_value)
    && isString(value.final_batch_unit)
    && isNullableString(value.total_cost)
    && isNullableString(value.sale_price)
    && isNullableString(value.tax)
    && isNullableString(value.margin)
    && isNullableString(value.margin_percent)
    && isString(value.produced_at)
    && isNonNegativeInteger(value.ingredient_line_count)
    && isNonNegativeInteger(value.packaging_line_count)
    && isString(value.notes)
  );
}

export function productionBatchListResponseDtoIsValid(value: unknown): boolean {
  return isObject(value)
    && Array.isArray(value.production_batches)
    && value.production_batches.every(productionBatchListItemDtoIsValid)
    && listMetadataIsValid(value);
}
