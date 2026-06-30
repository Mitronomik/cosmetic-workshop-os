# API Contract

Status: evolving implementation contract. Existing implemented areas have backend routes in the application; planned sections remain placeholders until their scoped PRs define them.

Standard error shape includes `code`, `message`, `user_message`, and `details`. Planned sections: health, settings, onboarding, clients, recipes, inventory, orders, production, alerts, purchases, imports, exports, backups, reports, audit logs.

## Orders backend foundation (PR60)

Orders are available through the local API under `/api` and connect an active client to exactly one recipe source: either a saved `RecipeVersion` or an individual `ClientRecipe`.

Endpoints:

- `POST /api/orders` — create an order in `new` status. Decimal-backed fields such as `target_batch_size_value`, `packaging_quantity`, and `sale_price` should be sent as strings. Generic create does not accept `status`, `produced_at`, or `delivered_at`.
- `GET /api/orders?include_inactive=true&status=&client_id=` — list orders with optional status/client filters.
- `GET /api/orders/{order_id}` — read one order.
- `PUT /api/orders/{order_id}` — update an active, non-cancelled order. Generic update preserves lifecycle fields and does not accept `status`, `produced_at`, or `delivered_at`.
- `POST /api/orders/{order_id}/cancel` — cancel an active order; repeated cancel is idempotent.
- `POST /api/orders/{order_id}/archive` — archive an order by setting `is_active=false` and `status=archived`.
- `GET /api/clients/{client_id}/orders` — list orders for one client.

Current limitations: this foundation does not calculate production readiness, reserve or write off stock, create production batches, generate alerts, create purchase suggestions, calculate cost/tax/margin, or expose frontend order screens.

## Production readiness backend foundation (PR62)

Production readiness is available through the local API under `/api` as a read-only check for an existing order.

Endpoint:

- `POST /api/orders/{order_id}/check-production-readiness` — calculates whether the selected order can be produced from the order's exact recipe source, current ingredient lot balances, and selected packaging balance.

Response summary:

- `order_id`, `can_produce`, and `status` (`ready`, `blocked`, or `warning`);
- `blocking_issues` and `warnings` with stable `code`, severity, human-readable `message`, optional `field`, `entity_type`, and `entity_id`;
- ingredient requirement lines with required quantity, available quantity, missing quantity, FEFO-selected lots, and line warnings;
- packaging availability lines when the order has selected packaging;
- optional `estimated_cost` when existing unit costs support it; `estimated_tax` and `estimated_margin` stay `null` until explicit tax settings/snapshots exist.

Read-only boundary:

- The endpoint does not create `stock_movements`.
- The endpoint does not create `packaging_stock_movements`.
- The endpoint does not create production batch rows.
- The endpoint does not mutate order status, `produced_at`, `delivered_at`, recipe versions, client recipes, ingredient lots, or packaging items.

Current limitations: this foundation does not confirm production, reserve stock, write off ingredients or packaging, generate alerts, generate purchase suggestions, change order lifecycle status, or add frontend UI.

## Production confirmation

### `POST /api/orders/{order_id}/produce`

Confirms actual production for an order. This endpoint is intentionally separate from the read-only readiness check and requires an explicit confirmation payload:

```json
{
  "confirm": true,
  "notes": "optional production note"
}
```

Safety rules:

- `confirm` must be exactly `true`; missing or false confirmation returns `422` with a human-readable message.
- The backend re-runs `ProductionReadinessService.check_order(order_id)` before writing anything.
- Blocking readiness issues return `409`; the operation does not create a production batch and does not write off stock.
- Cancelled, archived/inactive, delivered, already produced orders, and orders that already have a production batch return `409`.
- The operation is transactional: production batch snapshot rows, ingredient write-off movements, packaging write-off movements, order status update, and audit log are committed together or rolled back together.
- The endpoint does not use a hidden default tax rate. `tax`, `margin`, and `margin_percent` remain `null` until explicit tax snapshot infrastructure exists.

Successful response contains the historical production snapshot:

```json
{
  "id": 1,
  "order_id": 10,
  "recipe_version_id": 5,
  "client_recipe_id": null,
  "final_batch_value": "50.000",
  "final_batch_unit": "g",
  "component_cost": "100.00",
  "packaging_cost": "10.00",
  "other_cost": "0.00",
  "total_cost": "110.00",
  "sale_price": "200.00",
  "tax": null,
  "margin": null,
  "margin_percent": null,
  "produced_at": "2026-06-30T...",
  "notes": "",
  "created_at": "2026-06-30T...",
  "ingredients": [],
  "packaging": []
}
```

Error mapping:

- `404` — order or linked recipe record was not found.
- `409` — order lifecycle conflict, existing production batch, or readiness blockers.
- `422` — invalid request body or missing explicit confirmation.
- `500` — unexpected server error only.

## Production batch history (PR66)

Read-only production batch history is available under `/api` for inspecting immutable production snapshots created by `POST /api/orders/{order_id}/produce`.

Endpoints:

- `GET /api/production-batches?limit=50&offset=0` — list produced batches sorted by `produced_at DESC, id DESC`. The response includes order/product/client context, final batch size, cost/tax/margin snapshot fields, produced date, ingredient snapshot row count, packaging snapshot row count, and notes.
- `GET /api/production-batches/{batch_id}` — open one production batch detail with the batch header, order/product/client context, consumed ingredient lot snapshots, and consumed packaging snapshots.
- `GET /api/orders/{order_id}/production-batch` — open the production batch for one produced order. Returns `404` when the order does not exist or when the order has no production batch.

Read-only boundary:

- These endpoints do not create production batches.
- These endpoints do not create stock movements or packaging stock movements.
- These endpoints do not mutate orders or order statuses.
- Snapshot values are returned as historical data and are not recalculated from current ingredient, lot, packaging, recipe, or order values.

Error mapping:

- `404` — production batch/order was not found, or the order has no production batch.
- `422` — invalid `limit`/`offset` query parameters.

## Alerts API (PR67 backend foundation)

Alert generation is backend-only and explicit. It creates, updates, resolves, or dismisses rows in the `alerts` table only; it does **not** mutate orders, production batches, stock movements, packaging movements, ingredient lots, ingredients, packaging items, recipes, clients, purchase suggestions, or frontend UI state.

### `GET /api/alerts`

Lists alerts for operational review.

Query parameters:

- `status`: `open`, `resolved`, `dismissed`, or `all`; defaults to `open`.
- `type`: optional alert type filter. Supported values are `low_ingredient_stock`, `low_packaging_stock`, `ingredient_expiration_soon`, `ingredient_expired`, `insufficient_materials_for_order`, and `insufficient_packaging_for_order`.
- `limit`: `1..500`, defaults to `100`.
- `offset`: `0+`, defaults to `0`.

Example response:

```json
{
  "alerts": [
    {
      "id": 1,
      "alert_key": "low_ingredient_stock:ingredient:3",
      "type": "low_ingredient_stock",
      "severity": "warning",
      "message": "Компонент «Масло ши» ниже минимального остатка: доступно 20 g, минимум 50 g.",
      "related_entity_type": "ingredient",
      "related_entity_id": 3,
      "recommended_action": "Добавьте компонент в закупку или внесите новую партию после покупки.",
      "status": "open",
      "created_at": "2026-06-30T10:00:00",
      "updated_at": "2026-06-30T10:00:00",
      "resolved_at": null,
      "dismissed_at": null
    }
  ],
  "limit": 100,
  "offset": 0
}
```

### `POST /api/alerts/regenerate`

Regenerates deterministic alert candidates from backend data. Existing open alerts are updated by `alert_key`; new candidates create open alerts; open alerts whose condition disappeared are marked `resolved`; resolved/dismissed alerts are not reopened in PR67.

Example response:

```json
{
  "created_count": 3,
  "updated_count": 1,
  "resolved_count": 2,
  "open_count": 4
}
```

### `POST /api/alerts/{alert_id}/resolve`

Marks an alert as resolved and returns the alert. Re-resolving an already resolved alert is idempotent. A nonexistent alert returns `404`.

### `POST /api/alerts/{alert_id}/dismiss`

Marks an alert as dismissed and returns the alert. Re-dismissing an already dismissed alert is idempotent. A nonexistent alert returns `404`.

## Purchase Suggestions API (PR69)

Purchase suggestions are a backend-only working purchase list. They are generated explicitly by the user/API from current backend domain data and are safe: generation only creates, updates, or archives rows in `purchase_suggestions`. Marking a suggestion as purchased does **not** create `IngredientLot`, packaging inbound movements, stock movements, orders, alerts, production batches, supplier records, invoices, or real purchases.

### `GET /api/purchase-suggestions`

Lists purchase suggestions.

Query parameters:

- `status`: `open`, `purchased`, `dismissed`, `archived`, or `all`; default `open`.
- `reason`: optional `below_minimum_stock`, `insufficient_for_order`, `predicted_shortage`, `expiration_replacement`, or `manual`.
- `item_type`: optional `ingredient` or `packaging`.
- `limit`: integer from 1 to 500; default 100.
- `offset`: integer >= 0; default 0.

Example response:

```json
{
  "purchase_suggestions": [
    {
      "id": 1,
      "suggestion_key": "below_minimum_stock:ingredient:3",
      "item_type": "ingredient",
      "item_id": 3,
      "item_name_snapshot": "Масло ши",
      "recommended_quantity": "30",
      "unit": "g",
      "reason": "below_minimum_stock",
      "source_entity_type": "ingredient",
      "source_entity_id": 3,
      "message": "Купить компонент «Масло ши»: не хватает 30 g до минимального остатка.",
      "status": "open",
      "notes": "Текущий остаток ниже минимума: доступно 20 g, минимум 50 g.",
      "created_at": "2026-06-30 12:00:00",
      "updated_at": "2026-06-30 12:00:00",
      "resolved_at": null
    }
  ],
  "limit": 100,
  "offset": 0
}
```

### `POST /api/purchase-suggestions/regenerate`

Runs deterministic purchase suggestion generation for current PR69 rules:

- low active ingredient stock versus `minimum_stock`;
- low active packaging stock versus `minimum_stock`;
- missing ingredients for active, not terminal orders;
- missing packaging for active, not terminal orders.

Generation uses deterministic `suggestion_key` values to avoid duplicates. Existing open generated suggestions are updated. Existing purchased, dismissed, or archived generated suggestions are not reopened. Stale open generated suggestions for PR69 managed reasons are archived. Manual suggestions are not auto-archived.

Example response:

```json
{
  "created_count": 3,
  "updated_count": 1,
  "archived_count": 2,
  "open_count": 4
}
```

### `POST /api/purchase-suggestions`

Creates a manual open suggestion. This endpoint snapshots the active item name and does not create stock or any supplier/purchase record.

Request:

```json
{
  "item_type": "ingredient",
  "item_id": 1,
  "recommended_quantity": "100",
  "unit": "g",
  "notes": "Нужно для новой идеи рецепта"
}
```

Response: a `PurchaseSuggestion` object with `reason = "manual"` and `status = "open"`.

### `PATCH /api/purchase-suggestions/{suggestion_id}`

Safely updates only editable fields on an open suggestion:

```json
{
  "recommended_quantity": "150",
  "unit": "g",
  "notes": "optional note"
}
```

If the suggestion is already terminal (`purchased`, `dismissed`, or `archived`), the backend preserves the terminal status and returns the current suggestion unchanged.

### `POST /api/purchase-suggestions/{suggestion_id}/mark-purchased`

Marks an open suggestion as `purchased` and sets `resolved_at`. Terminal suggestions stay terminal and are returned unchanged. This endpoint does not create ingredient lots, packaging inbound movements, stock movements, orders, or production changes.

### `POST /api/purchase-suggestions/{suggestion_id}/dismiss`

Marks an open suggestion as `dismissed` and sets `resolved_at`. Terminal suggestions stay terminal and are returned unchanged.
