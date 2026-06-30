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
