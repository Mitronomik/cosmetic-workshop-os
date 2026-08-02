# API Contract

Status: evolving implementation contract. Existing implemented areas have backend routes in the application; planned sections remain placeholders until their scoped PRs define them.


## Settings status

`GET /api/settings/status` returns the read-only Settings status foundation. It reports local-first app information, local data separation, safe workflow capabilities, and a Settings Decision Matrix. The endpoint is deterministic and read-only: it does not create files, mutate business data, persist settings, run migrations, trigger backup/export/import/demo/report-document actions, or regenerate alerts/purchases.

**Current editable set on merged `main`.** The Workshop profile fields — `workshop_name`, `master_name`, `workshop_contact_text`, `workshop_note` — are `editable_now`, and so is `default_tax_rate`. `default_tax_rate` is the **only calculation-sensitive setting that is currently editable**; it became editable with the merged `C1-I` slice (PR #149) and it never recalculates historical data. Every other calculation-sensitive setting — currency display, target margin, default low-stock threshold, expiry warning days, default measurement units — remains `requires_backend_rules` and stays closed until it has its own separately accepted backend rules. *(Historical note: `PR96` originally made only the Workshop profile editable; that was the state before `C1-I` merged and is no longer the current contract.)*

Standard error shape includes `code`, `message`, `user_message`, and `details`. Planned sections: health, settings, onboarding, clients, recipes, inventory, orders, production, alerts, purchases, imports, exports, backups, reports, audit logs. The C3-I AuditLog read endpoint is merged and `DONE — MERGED AND EXACT-HEAD VERIFIED`; see § *AuditLog API (`C3-I`)* and `docs/audit-log.md`.

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
- optional `estimated_cost` when existing unit costs support it, plus the financial estimate described under **Financial estimate extension — `C2-I`** below. **The explicit tax-rate setting exists and is editable** (`default_tax_rate`, merged `C1-I` / PR #149), and `estimated_tax` / `estimated_margin` are active since merged `C2-I` (PR #151). Production tax snapshots are added by `C2-II`, merged as PR #152.

Read-only boundary:

- The endpoint does not create `stock_movements`.
- The endpoint does not create `packaging_stock_movements`.
- The endpoint does not create production batch rows.
- The endpoint does not mutate order status, `produced_at`, `delivered_at`, recipe versions, client recipes, ingredient lots, or packaging items.

HTTP boundaries:

- `200` — a valid readiness DTO, including legitimate `blocked` or `warning` results;
- `404` — the order or its linked Recipe Version / Client Recipe was not found;
- `409` — the current order lifecycle does not allow readiness checking;
- `422` — backend-authoritative domain validation rejected the check inputs;
- `500` — an unexpected system failure only.

A blocked readiness DTO is not a request failure. Conversely, a transport or HTTP failure is not a valid blocked-readiness result and must be presented separately by clients.

Current limitations: the Orders frontend presents this read-only check, but the readiness operation itself does not confirm production, reserve stock, write off ingredients or packaging, create a `ProductionBatch`, generate or mutate alerts or purchase suggestions, or change the Order lifecycle status.

**Financial lifecycle, stated precisely.** The default tax-rate setting **exists and is editable** on merged `main` (`GET`/`PUT /api/settings/tax-rate`, key `default_tax_rate`, merged `C1-I` / PR #149), and readiness estimates tax and margin since merged `C2-I` (PR #151). The four lifecycle states are distinct:

| Layer | Status |
|---|---|
| C1 tax-rate setting | **IMPLEMENTED** and merged (PR #149) |
| C2-I readiness tax / margin / margin-percent calculation | **IMPLEMENTED** and merged (PR #151) |
| C2-II `ProductionBatch` rate snapshots and transactional persistence | **IMPLEMENTED** and merged (PR #152) |
| C2-III-A Order and `ProductionBatch` financial presentation | **IMPLEMENTED** and merged (PR #154) |
| C2-III-B snapshot-backed reports and report documents | **IMPLEMENTED** and merged (PR #157) |
| C3-I read-only AuditLog workspace (`GET /api/audit-logs`) | `DONE — MERGED AND EXACT-HEAD VERIFIED` (PR #159); endpoint exists on merged `main` |
| C3-II-A atomic workshop-profile AuditLog coverage | `DONE — MERGED AND EXACT-HEAD VERIFIED` (PR #161); no new endpoint |
| CR-009 file-backed artifact AuditLog semantics | `ACCEPTED — NOT IMPLEMENTED`; only B1 authorized after this documentation PR merges |

### Financial estimate extension — `C2-I`

Status: **IMPLEMENTED** and merged as PR #151. Decided as `CR-008`; durable contract `docs/decisions/0012-c2-financial-calculation-snapshots.md`.

`C2-I` extends this **existing** endpoint additively. No parallel financial-readiness endpoint is created, and no existing field is removed or renamed. The calculation is backend-owned and lives in `backend/app/domain/production_financials.py`; the readiness service supplies backend-owned inputs, reads the current rate through the existing C1 `TaxRateSettingsService.get_tax_rate()` boundary, and maps the returned warning codes onto the existing `ProductionReadinessIssue` structure.

Existing fields, **reused, not duplicated**:

- `estimated_cost` — the existing readiness cost estimate;
- `estimated_tax` — activated;
- `estimated_margin` — activated.

Additive fields:

- `sale_price`;
- `tax_rate_percent`;
- `tax_rate_effective_at`;
- `estimated_margin_percent`;
- `financial_estimate_status`.

Expected response contract:

```text
sale_price
estimated_cost
tax_rate_percent
tax_rate_effective_at
estimated_tax
estimated_margin
estimated_margin_percent
financial_estimate_status
```

All monetary and percentage values are decimal strings or `null`. `tax_rate_effective_at` is an ISO-8601 UTC string or `null`.

`estimated_total_cost` is **not** authorized, and no duplicate alias for `estimated_cost`, `estimated_tax`, or `estimated_margin` may be added. The extension is backward-compatible: the current frontend must keep working unchanged.

`financial_estimate_status` values:

| Value | Meaning |
|---|---|
| `available` | tax, margin, and margin percent are all available |
| `partial` | at least tax or margin is available, but the complete financial set is not |
| `unavailable` | tax is unavailable and every dependent value is therefore unavailable |

| Situation | Status |
|---|---|
| configured rate + sale price `> 0` + total cost | `available` |
| configured rate + sale price `= 0` + total cost | `partial` |
| configured rate + sale price + missing total cost | `partial` |
| missing or invalid rate | `unavailable` |
| missing sale price | `unavailable` |

Formulas, `Decimal` only, rounding only the final amount of each: `tax = ROUND_MONEY(sale_price × tax_rate_percent / 100)`; `margin = ROUND_MONEY(sale_price - total_cost - tax)`; `margin_percent = ROUND_PERCENT(margin / sale_price × 100)`. A configured `0.00` rate yields tax `0.00`; a missing rate yields `null` and never a fabricated zero; a negative margin is returned unclamped.

Readiness warning codes. The existing codes are **preserved and never renamed**, and no aliases such as `tax_rate_unconfigured`, `sale_price_unavailable`, or `total_cost_unavailable` are introduced:

| Code | Status | Meaning |
|---|---|---|
| `tax_rate_missing` | existing | no configured `default_tax_rate` |
| `sale_price_missing` | existing | the authoritative Order sale price is unavailable |
| `cost_data_missing` | existing | the readiness cost calculation cannot produce a complete total cost |
| `margin_percent_unavailable_zero_sale_price` | new in `C2-I` | tax and margin may be available, but the denominator is zero |
| `tax_rate_invalid` | new in `C2-I` | defensive handling of an invalid persisted canonical tax-rate value |

All five are **non-blocking warnings** carried by the existing `ProductionReadinessIssue` structure. They never change `can_produce`, which stays governed by recipe/formula readiness, stock, lots, packaging, order lifecycle, and the existing physical safety rules. An invalid persisted rate must not produce an unhandled `500`.

#### No valid configured tax-rate context

Two distinct backend states share one authoritative financial outcome:

| Backend state | Readiness warning | `tax_rate_percent` | `tax_rate_effective_at` | `financial_estimate_status` | Tax / margin / margin % |
|---|---|---|---|---|---|
| no `default_tax_rate` row | `tax_rate_missing` | `null` | `null` | `unavailable` | `null` |
| row exists but the persisted value is invalid | `tax_rate_invalid` | `null` | `null` | `unavailable` | `null` |

Together these are **`no valid configured tax-rate context`**. The two states stay distinguishable through the warning code, and the invalid case must **not** also emit `tax_rate_missing`. Physical production remains non-blocked in both.

The raw invalid persisted value must never be returned as the authoritative rate, and must never be normalized, coerced, rounded, treated as zero, copied into a readiness DTO, copied into a confirmation request, or copied into a `ProductionBatch` snapshot.

Stated exactly, because the C1 Settings repair surface is deliberately different:

```text
A raw invalid value is never exposed as an authoritative financial value
through C2 readiness or confirmation and is never persisted to a
ProductionBatch snapshot. The existing Settings repair surface may still read
the stored value so the user can replace or clear it.
```

Because `GET /api/settings/tax-rate` may still return the stored text for an externally corrupted row, `is_configured` alone is not proof that a value is financially authoritative. Readiness therefore re-validates the returned percentage through the existing C1 domain parser before using it, and treats anything that does not re-parse — or that carries no effective timestamp — as the no-valid-rate context above. `GET`/`PUT /api/settings/tax-rate` behavior is unchanged by `C2-I`.

`C2-I` performs no persistence write, creates no `AuditLog`, changes no Order, `ProductionBatch`, stock movement, packaging movement, or report, and adds no migration.

## Production confirmation

### `POST /api/orders/{order_id}/produce`

Confirms actual production for an order. This endpoint is intentionally separate from the read-only readiness check and requires an explicit confirmation payload:

```json
{
  "confirm": true,
  "notes": "optional production note",
  "expected_tax_rate_percent": "6.00",
  "expected_tax_rate_effective_at": "2026-07-27T19:44:53Z"
}
```

Both tax-context keys are **required but nullable** since `C2-II`; see the financial snapshot extension below for their exact contract.

Safety rules:

- `confirm` must be exactly `true`; missing or false confirmation returns `422` with a human-readable message.
- The backend re-runs `ProductionReadinessService.check_order(order_id)` before writing anything.
- Blocking readiness issues return `409`; the operation does not create a production batch and does not write off stock.
- Cancelled, archived/inactive, delivered, already produced orders, and orders that already have a production batch return `409`.
- The operation is transactional: production batch snapshot rows, the tax-rate and financial snapshots, ingredient write-off movements, packaging write-off movements, order status update, and audit log are committed together or rolled back together.
- The endpoint uses no hidden default tax rate. Since `C2-II` it reads the current `default_tax_rate` **on the production transaction's own connection**, compares it with the expected context, and only then calculates `tax`, `margin`, and `margin_percent` from the locked Order sale price and the actual production cost.

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
  "tax": "12.00",
  "margin": "78.00",
  "margin_percent": "39.00",
  "tax_rate_percent_snapshot": "6.00",
  "tax_rate_effective_at_snapshot": "2026-07-27T19:44:53Z",
  "produced_at": "2026-06-30T...",
  "notes": "",
  "created_at": "2026-06-30T...",
  "ingredients": [],
  "packaging": []
}
```

Error mapping:

- `404` — order or linked recipe record was not found.
- `409` — order lifecycle conflict, existing production batch, readiness blockers, or a stale tax context (`tax_rate_context_stale`).
- `422` — invalid request body, missing explicit confirmation, or an omitted/off-contract tax context (`tax_rate_context_required`, `invalid_tax_rate_context`).
- `500` — unexpected server error only.

### Financial snapshot extension — `C2-II`

Status: **IMPLEMENTED** and merged as PR #152. Decided as `CR-008`; contract `docs/decisions/0012-c2-financial-calculation-snapshots.md`.

**Required-but-nullable request context.** The request always carries both keys, declared without default values:

```json
{
  "confirm": true,
  "notes": "optional production note",
  "expected_tax_rate_percent": "6.00",
  "expected_tax_rate_effective_at": "2026-07-27T19:44:53Z"
}
```

Only two value pairs are valid:

1. **Valid configured context** — a canonical two-decimal percentage string plus a canonical UTC timestamp:

```json
{
  "expected_tax_rate_percent": "6.00",
  "expected_tax_rate_effective_at": "2026-07-27T19:44:53Z"
}
```

2. **No-valid-rate context** — explicit `null` and explicit `null`:

```json
{
  "expected_tax_rate_percent": null,
  "expected_tax_rate_effective_at": null
}
```

`null/null` means **"the latest readiness result observed no valid configured tax rate"**. That covers **both** a missing setting row **and** an invalid persisted setting. It does **not** mean only that the row is absent.

The frontend passes the pair from the latest accepted readiness response without calculating, normalizing, altering, or inventing any part of it. A readiness DTO that does not carry the pair is not treated as a valid no-rate result: confirmation is blocked until a fresh readiness check supplies one.

**Omitting a key is not equivalent to explicit `null/null`.** Omission means an invalid or outdated client contract.

Validation, rejected with HTTP `422` **before any production transaction writes**. The stable code is returned in the repository's normal structured `detail` shape, never as raw Pydantic internals:

| Condition | Stable code |
|---|---|
| either key is omitted | `tax_rate_context_required` |
| exactly one of the two values is `null` | `invalid_tax_rate_context` |
| the percentage is malformed, non-canonical, out of range, or not a string | `invalid_tax_rate_context` |
| the timestamp is malformed or not the canonical `YYYY-MM-DDTHH:MM:SSZ` form | `invalid_tax_rate_context` |

**Stale conflict.** Inside the existing `BEGIN IMMEDIATE` transaction the backend reads `default_tax_rate` through `TaxRateSettingsService.get_tax_rate(connection=...)` on that same connection — no second connection, no write, no `AuditLog` — and reduces it to one of two comparable canonical contexts — a **valid context** (canonical percentage + canonical API timestamp) or a **no-valid-rate context** (`null` + `null`, covering both missing and invalid) — and compares it with the expected context:

| Expected context | Current backend context | Result |
|---|---|---|
| same valid pair | same valid pair | continue |
| valid pair | different valid pair | `409 tax_rate_context_stale` |
| valid pair | missing | `409 tax_rate_context_stale` |
| valid pair | invalid | `409 tax_rate_context_stale` |
| `null/null` | valid pair | `409 tax_rate_context_stale` |
| `null/null` | missing | continue |
| `null/null` | invalid | continue |

So: valid → changed valid, valid → missing, valid → invalid, and missing-or-invalid → valid are all stale conflicts, while **missing → invalid and invalid → missing are not**. Missing and invalid deliberately share one confirmation context because they produce exactly the same financial result: no rate snapshot, no tax, no margin, no margin percent. No third request field and no generic financial-context token is introduced by this decision.

The `409` carries a safe Russian message equivalent to `Налоговая ставка изменилась. Обновите готовность и подтвердите производство ещё раз.` The client must refresh readiness and confirm again, and must not retry automatically.

A `422` validation rejection and a `409` stale conflict both write **nothing**: no `ProductionBatch`, no financial snapshot, no stock movement, no packaging movement, no Order mutation, and no production audit.

**Accepted no-valid-rate confirmation.** When the current backend state is missing or invalid and the expected context is `null/null`, physical production continues and the batch persists `tax_rate_percent_snapshot = null`, `tax_rate_effective_at_snapshot = null`, `tax = null`, `margin = null`, `margin_percent = null`. The actual authoritative production cost and every other physical snapshot are written normally. An invalid raw setting value stays untouched in `app_settings`: confirmation must not repair, clear, rewrite, or audit a setting mutation, must not persist the invalid value into `ProductionBatch`, and must not treat it as `0.00`. The normal existing production audit still belongs to the transactional production flow.

**An absent or invalid tax-rate setting may make financial values unavailable, but it must not by itself block physical production.**

#### Timestamp contract

**Database persistence** — the existing `AppSetting.updated_at` convention, and the same convention for the `tax_rate_effective_at_snapshot` column:

```text
YYYY-MM-DD HH:MM:SS
```

UTC, second precision, SQLite text, no `T`, no `Z`, no timezone offset.

**API and confirmation-context representation** — `effective_at`, readiness `tax_rate_effective_at`, `expected_tax_rate_effective_at`, and the exposed snapshot:

```text
YYYY-MM-DDTHH:MM:SSZ
```

UTC, second precision, literal `T`, literal `Z`. Not accepted and not documented: local-time values, arbitrary offsets such as `+03:00`, fractional seconds, a space instead of `T`, a missing `Z`, or user-generated timestamps. `expected_tax_rate_effective_at` must be either `null` or the **exact** canonical timestamp previously returned by readiness. A malformed or non-canonical request timestamp is rejected with HTTP `422` and `invalid_tax_rate_context`.

The API must never expose the raw SQLite storage representation: the confirmation response and the `ProductionBatch` detail response normalize `tax_rate_effective_at_snapshot` to the canonical `YYYY-MM-DDTHH:MM:SSZ` form. No backfill is authorized.

**Response exposure boundary.** `C2-II` exposes `tax_rate_percent_snapshot` and `tax_rate_effective_at_snapshot` to the production confirmation response and to the `ProductionBatch` **detail** response, so the persisted snapshot is verifiable in that slice. It does **not** add them to the `ProductionBatch` list response, to report read models, or to report UI — those surfaces remain `C2-III` scope. The existing `sale_price`, `total_cost`, `tax`, `margin`, and `margin_percent` fields are reused; no duplicate alias is created.

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

## Manual Backups API (PR73)

Manual backups are explicit local SQLite safety copies. The API does not restore databases, delete backups, download backup files, export business tables as CSV/XLSX, schedule background backups, or use cloud storage. Status and list endpoints are read-only: they must not create directories, databases, backup files, migrations, exports, imports, stock movements, orders, production batches, alerts, or purchase suggestions.

### `GET /api/backups/status`

Returns the current configured SQLite database path, whether that database exists, the selected backup directory, whether it exists, the number of listed backups, the latest backup if any, and `pending_audit_count`. This endpoint is read-only: it does not create the database or backup directory, and it never reconciles.

`pending_audit_count` (CR-009 B3) is exactly the number of unresolved
`manual_backup` ledger operations — `prepared` plus `pending_audit` — and
excludes `audited`, `abandoned` and every other artifact kind. When the ledger
cannot be read the endpoint returns `500` with the fixed Russian detail
`Не удалось прочитать сведения о резервных копиях. Данные мастерской не
изменялись.` rather than reporting `pending_audit_count: 0`. A `0` is a factual
claim the frontend clears a standing warning on, so it is never fabricated from
a failed read. When no database exists the count is a conclusive `0` and no
connection is opened.

Example response:

```json
{
  "database_path": "/path/to/cosmetic_workshop.sqlite",
  "database_exists": true,
  "database_size_bytes": 245760,
  "backup_dir": "/path/to/backups",
  "backup_dir_exists": true,
  "backup_count": 2,
  "latest_backup": {
    "filename": "20260705T100000000000Z-cosmetic_workshop-manual.sqlite",
    "path": "/path/to/backups/20260705T100000000000Z-cosmetic_workshop-manual.sqlite",
    "created_at": "2026-07-05T10:00:00Z",
    "reason": "manual",
    "size_bytes": 245760
  },
  "pending_audit_count": 0
}
```

### `GET /api/backups`

Lists existing SQLite-like backup files (`.sqlite`, `.sqlite3`, `.db`) in the selected backup directory, newest first. If the backup directory does not exist, returns an empty list and does not create it.

Example response:

```json
{
  "backup_dir": "/path/to/backups",
  "backups": []
}
```

### `POST /api/backups`

Creates an explicit manual backup of the currently configured SQLite database by writing a **transactionally consistent SQLite snapshot** into the selected backup directory through the SQLite Online Backup API (ADR 0015). The API does not accept arbitrary source or destination paths. Existing backup files are never overwritten, and the source database is never modified.

The snapshot contains only committed data and is independently openable without the source WAL or rollback journal. It is **not** byte-identical to the source. If the source database stays locked for the whole bounded wait, the endpoint returns `409` rather than producing an inconsistent file.

The response is built from the backup engine's exact result. The endpoint does **not** re-list the backup directory after a successful create: CR-004 measured that re-scan turning a complete, verified backup into an HTTP `500`.

Request body is optional; missing, null, or blank `reason` becomes `manual`. Reasons are limited to 80 characters and are sanitized for filenames by the backup service. The returned `reason` is the canonical filename-derived segment — see *Backup and export `reason` field semantics* below.

```json
{
  "reason": "before_large_edit"
}
```

Success response:

```json
{
  "backup": {
    "filename": "20260705T100000000000Z-cosmetic_workshop-before_large_edit.sqlite",
    "path": "/path/to/backups/20260705T100000000000Z-cosmetic_workshop-before_large_edit.sqlite",
    "created_at": "2026-07-05T10:00:00Z",
    "reason": "before_large_edit",
    "size_bytes": 245760
  },
  "database_path": "/path/to/cosmetic_workshop.sqlite",
  "backup_dir": "/path/to/backups",
  "message": "Резервная копия создана.",
  "audit_status": "recorded",
  "audit_message": null
}
```

If the database file is missing, the endpoint returns `404` with a human-readable Russian message. If the configured database path exists but is not a file, or the backup cannot be written safely, it returns `409`.

#### Manual-backup AuditLog fields (CR-009 B3)

`audit_status` and `audit_message` are additive and report only the **secondary**
Journal result. `message` remains the artifact result and never changes meaning.
The two are bound: `recorded` always carries `audit_message: null`, and `pending`
always carries exactly the accepted warning.

A verified backup whose Journal entry could not be committed still returns
HTTP `201`:

```json
{
  "message": "Резервная копия создана.",
  "audit_status": "pending",
  "audit_message": "Резервная копия создана, но запись в журнал действий пока не добавлена. Приложение повторит попытку при следующем запуске или перед созданием следующей резервной копии."
}
```

The backup is kept, listed and counted; nothing is deleted and no duplicate
request is sent. The retry happens at exactly two bounded moments: the next
normal startup, and once before the next manual backup.

If audit tracking cannot be durably prepared **before** anything is written, the
create is refused outright and no backup, ledger row or event exists:

```json
{
  "detail": {
    "code": "artifact_audit_tracking_unavailable",
    "message": "Не удалось безопасно подготовить создание резервной копии. Резервная копия не создана.",
    "next_action": "Повторите создание резервной копии. Если ошибка повторяется, перезапустите приложение."
  }
}
```

### Backup and export `reason` field semantics (CR-005, decided 2026-07-27)

This subsection documents the semantics of the **existing** `reason` field on the backup and export create, list, and status responses. `CR-005` adds **no new API field** and changes **no response shape**. The full contract lives in `docs/backup-and-restore.md` and `docs/export.md`.

- The `reason` field returned by `POST /api/backups`, `GET /api/backups`, `GET /api/backups/status`, `POST /api/exports`, `GET /api/exports`, and `GET /api/exports/status` is the **canonical filename-derived reason segment**, not the raw user-supplied text. This API value is the single source of truth for the reason.
- **The frontend consumes this canonical slug and must never reconstruct, sanitize, or normalize it.** Presentation is a separate layer: the Backups and Exports screens map a small set of **known system slugs** to the **existing localized Russian display labels**, and display any **custom or unmapped** canonical slug **verbatim**. The visible label is therefore not always literally the API slug — for example the canonical `before_import` renders as `Перед импортом`, while the canonical `before_update_unsafe` renders verbatim. The exact per-screen mappings are recorded in `docs/backup-and-restore.md` and `docs/export.md`; this decision does not add, remove, or reword any label.
- The canonical segment is path-safe: runs of non-alphanumeric characters collapse to a single underscore, hyphens normalize to underscores, leading and trailing underscores are removed, an empty result becomes `manual`, a numeric-only result is prefixed with `reason_`, and letter case and Unicode alphanumerics are preserved. There is no lowercasing, transliteration, or new truncation.
- The numeric uniqueness suffix used to avoid overwriting an existing artifact is **never** part of the reported `reason`.
- Request-side behavior is unchanged: `reason` remains optional, is trimmed, defaults to `manual` when missing/null/blank, and is limited to 80 characters.
- The **export JSON manifest** `reason` continues to hold the normalized **human** reason, not the canonical filename segment. For the request `before-import`, the API `reason` is `before_import` while the manifest `reason` is `before-import`. The export schema version is unchanged.
- These semantics apply to **newly created** artifacts. Reason parsing for pre-existing legacy artifacts is **best-effort**: legacy files are listed with their filename, path, created-timestamp fallback, and size, but an ambiguous legacy reason may not round-trip exactly and no such guarantee is made.

**Implementation status: `DONE`.** `CR-005` remains **accepted**, and the correcting slice `R4` is **merged and DONE** — PR #146, final reviewed head `c505de2dc213ff75e0eb7cb5ffbcd180069a86fb`, merge commit `127191feb182ccf68a4d7b9f2be28f6aa5b42453` (VERIFIED FROM REPOSITORY / GITHUB / MERGED PR EVIDENCE). **Merged `main` now implements the canonical reason contract documented above**, so the `reason` field returned by the backup and export create/list/status endpoints is the canonical filename-derived slug. Accepted merged backend result: `562 collected / 562 passed / 0 failed / 0 skipped`. The focused exact-head `/backups` and `/exports` browser smoke **passed** against `c505de2dc213ff75e0eb7cb5ffbcd180069a86fb`. `R4` changed **no response shape and no schema file** — `backend/app/api/backups.py`, `backend/app/api/exports.py`, `backend/app/schemas/backups.py`, and `backend/app/schemas/exports.py` are untouched — so this subsection documents the same fields before and after, and there was **no database or filesystem migration**; **existing artifacts remain untouched**. **`CR-004` remains unresolved** and **Restore remains unimplemented**. **Product release readiness is not claimed.**

## Export API (PR75)

Local JSON exports are explicit data snapshots for inspection, transfer preparation, and pre-import safety checks. Export is intentionally separate from backup, import, restore, reporting, and analytics.

### `GET /api/exports/status`

Read-only status endpoint. It reports the current configured SQLite database path, whether that database file exists, the selected local export directory, whether the directory exists, export count, and latest export metadata.

Safety guarantees:

- does not create a database file;
- does not create the `exports/` directory;
- does not create export files, backups, migrations, imports, restores, alerts, purchase suggestions, orders, production batches, or stock movements;
- does not mutate business data.

### `GET /api/exports`

Read-only export listing endpoint. It returns JSON export file metadata from the selected local `exports/` directory, newest first.

If the export directory does not exist, the response is an empty list and the resolved directory path:

```json
{
  "exports": [],
  "export_dir": "/path/to/exports"
}
```

Safety guarantees:

- does not create missing directories;
- lists only local JSON export metadata;
- does not expose export file contents;
- does not download, rename, delete, import, restore, or mutate data.

### `POST /api/exports`

Explicitly creates a local JSON export snapshot for the currently configured SQLite database.

Request body:

```json
{
  "reason": "manual"
}
```

`reason` is optional, trimmed, defaults to `manual` when empty, and is limited to 80 characters. The **normalized human reason** is stored in the export manifest; the **canonical filename-derived segment** is what appears in the filename and in the response `reason` field. See *Backup and export `reason` field semantics* in the Manual Backups API section above.

Successful response shape:

```json
{
  "export": {
    "filename": "20260705T120000000000Z-cosmetic_workshop-export-manual.json",
    "path": "/path/to/exports/20260705T120000000000Z-cosmetic_workshop-export-manual.json",
    "created_at": "2026-07-05T12:00:00Z",
    "reason": "manual",
    "size_bytes": 120000
  },
  "database_path": "/path/to/cosmetic_workshop.sqlite",
  "export_dir": "/path/to/exports",
  "entity_counts": {
    "ingredients": 12,
    "clients": 4
  },
  "message": "Экспорт создан."
}
```

The exported JSON file manifest does not store the absolute local `database_path`. It stores portable source metadata instead: `database_filename` and `database_location_kind` (`user_data` or `development`). API status/create responses may still include local paths for the local UI.

Exported JSON snapshots include whitelisted user-organization catalog tables when they exist: `catalog_categories`, `catalog_tags`, `ingredient_catalog_tags`, `packaging_item_catalog_tags`, and `recipe_template_catalog_tags`.

Safety guarantees:

- creates only the selected local `exports/` directory when needed;
- writes only a new `.json` export snapshot;
- never overwrites an existing export file;
- does not accept arbitrary source or destination paths;
- does not create backups;
- does not run migrations;
- does not implement import, restore, download, delete, CSV/XLSX, PDF, cloud export, scheduled export, or UI behavior;
- does not mutate recipes, clients, orders, stock, lots, packaging, production, alerts, purchase suggestions, settings, or audit records.

### Export create-response confirmation semantics (`CR-006`, decided 2026-08-01)

`CR-006` is **accepted**. Durable decision:
`docs/decisions/0014-json-export-create-confirmation-semantics.md`. Product
summary: `docs/export.md` § *Create-response confirmation contract*.

**Accepted contract for `POST /api/exports`:**

| Response field | Authoritative source |
|---|---|
| `export.filename` | the exact final filename the create operation produced |
| `export.path` | the exact final path the create operation produced |
| `export.created_at` | the create operation's own timestamp |
| `export.size_bytes` | the size the create operation measured on the finished file |
| `export.reason` | the **canonical reason parsed from that exact final filename**, through the same parsing contract `GET /api/exports` and `GET /api/exports/status` use |
| `entity_counts` | the create operation's own counts |

- A successfully completed create operation is **authoritative**. The endpoint
  must not re-scan the export directory to decide whether the operation it just
  performed succeeded.
- The **normalized human reason** preserved in the export JSON manifest must
  **never** be returned as the API `reason`. That would violate the `CR-005`
  contract documented above.
- `HTTP 201 Created` means the application completed creation at the operation
  boundary. It does **not** promise that an external process never removes or
  replaces the file afterwards; `GET /api/exports` and
  `GET /api/exports/status` remain the truthful current-state surface.
- If the create operation does not complete successfully, the endpoint must not
  synthesize success. Its existing `404` and `409` error responses are
  unchanged.
- `GET /api/exports` and `GET /api/exports/status` keep their existing
  best-effort listing contract; `CR-006` does not change it.

**Diagnostic status.** The defensive fallback in the pre-correction
implementation was confirmed reachable in production-equivalent behavior, and
when it ran it returned the human manifest reason. Classification: `PRODUCT
DEFECT — CREATE-RESPONSE CONTRACT MISMATCH`, severity `MEDIUM`; no data loss,
overwrite, incorrect export bytes, or privacy exposure was found. **The
correction is implemented on the `C3-II-B2` PR branch and is not merged.** On
that branch `POST /api/exports` no longer calls `list_export_files` at all: the
response is built from the exact `ExportResult`, and `reason` comes from the
exact final filename through `parse_export_reason`, the same function list and
status use. `CR-006` adds no field and changes no schema.

**`C3-II-B2` additive fields — implemented on the PR branch, not merged.** Under
the `CR-009` contract accepted in ADR 0013, `C3-II-B2` adds `audit_status`
(`recorded` | `pending`) and `audit_message` to `POST /api/exports`, and
`pending_audit_count` to `GET /api/exports/status`, counting exactly the ledger
rows with `artifact_kind = json_export` and
`status IN (prepared, pending_audit)`. A `recorded` result carries
`audit_message: null`; a `pending` result carries the exact accepted Russian
warning and is still HTTP `201`, because the export file exists and is
authoritative. That status GET stays read-only, reconciles nothing, and raises a
safe HTTP `500` rather than reporting a fabricated `0` when the ledger cannot be
read. No other export response field is added, renamed or removed.

## Import drafts API (PR77)

CSV/XLSX import uses safe drafts first: upload → parse → preview → validation → explicit confirmation → apply for supported safe targets. Upload/preview still does not mutate domain tables; applying requires the dedicated apply endpoint and confirmation flags.

Import draft column names are user-facing aliases for uploaded files. They are not guaranteed to match internal domain/API field names; the apply service explicitly maps supported aliases before writing to business tables. Source file hashes remain stored internally and are not exposed in import source responses.

### `GET /api/imports/targets`

Returns supported import target types and basic required/optional columns.

```json
{
  "targets": [
    {
      "type": "ingredients",
      "label": "Компоненты",
      "required_columns": ["name"],
      "optional_columns": ["inci_name", "unit", "density", "notes"]
    }
  ]
}
```

### `POST /api/imports/drafts`

Creates a persistent import draft from a multipart CSV/XLSX upload.

Request: `multipart/form-data`

- `file`: `.csv` or `.xlsx` file;
- `target_type`: one of `ingredients`, `packaging_items`, `clients`, `recipe_templates`, `ingredient_lots`, `orders`.

Successful response includes the draft summary, first preview rows, validation issues, and the required safety message:

```json
{
  "draft": {
    "id": 1,
    "source_id": 1,
    "target_type": "ingredients",
    "status": "draft",
    "row_count": 2,
    "valid_row_count": 2,
    "invalid_row_count": 0,
    "warning_count": 0,
    "error_count": 0,
    "headers": ["name", "unit"],
    "summary": {"message": "Данные ещё не внесены в систему."},
    "apply_readiness": {
      "can_apply": true,
      "status": "ready",
      "blocking_error_count": 0,
      "warning_count": 0,
      "valid_row_count": 2,
      "invalid_row_count": 0,
      "blocking_reasons": [],
      "warnings": [],
      "next_action": "Черновик готов к явному применению после проверки и подтверждения."
    },
    "created_at": "2026-07-05 12:00:00",
    "updated_at": "2026-07-05 12:00:00"
  },
  "preview_rows": [],
  "issues": [],
  "message": "Черновик импорта создан. Данные ещё не внесены в систему."
}
```

Unsupported file types return `415` with `Поддерживаются только CSV и XLSX файлы.`. Oversized files return `413` with `Файл слишком большой для черновика импорта.`. Unreadable or empty files return a safe user-readable `400` error.

### `GET /api/imports/drafts`

Lists draft summaries only. Query parameters:

- `status` — optional draft status filter;
- `target_type` — optional target type filter;
- `limit` — default `50`, maximum `100`;
- `offset` — default `0`.

### `GET /api/imports/drafts/{draft_id}`

Returns draft details with source metadata, headers, paginated preview rows, and validation issues. Query parameters:

- `limit` — default `50`, maximum `100`;
- `offset` — default `0`.

### `POST /api/imports/drafts/{draft_id}/cancel`

Marks a draft and its source as cancelled. This safe mutation changes only import draft records and returns:

```json
{
  "draft": {},
  "message": "Черновик импорта отменён. Рабочие данные не изменены."
}
```

## Imports apply readiness (PR79)

Import draft create, list, detail, and cancel responses include `draft.apply_readiness`:

```json
{
  "can_apply": false,
  "status": "blocked",
  "blocking_error_count": 1,
  "warning_count": 2,
  "valid_row_count": 9,
  "invalid_row_count": 1,
  "blocking_reasons": ["Исправьте ошибки в строках или заголовках перед применением."],
  "warnings": ["Есть неизвестные столбцы, которые не будут применены."],
  "next_action": "Исправьте файл и создайте новый черновик."
}
```

Allowed readiness statuses are `ready`, `ready_with_warnings`, `blocked`, `cancelled`, `failed`, and `applied`. `can_apply` means only “validation-ready for an explicit apply endpoint”; the request can still be rejected for unsupported targets, warnings without acknowledgement, duplicates, or already-applied drafts. Import drafts do not write rows into business tables unless the apply endpoint is called with explicit confirmation and backup acknowledgement.

Draft `summary` may also include `readiness`, `issue_counts_by_code`, and `issue_counts_by_severity`. Refined validation issue codes include `header_alias_used`, `decimal_comma_normalized`, `ambiguous_decimal`, `invalid_positive_decimal`, `invalid_non_negative_decimal`, `unit_alias_normalized`, `date_format_normalized`, `invalid_email`, and `invalid_id` in addition to the PR77 codes.

## PR80 — Import draft apply backend endpoint

`POST /api/imports/drafts/{draft_id}/apply` explicitly applies a validation-ready import draft into supported domain tables.

Request body:

```json
{
  "confirm_apply": true,
  "backup_acknowledged": true,
  "allow_warnings": false
}
```

Rules:

- `confirm_apply=true` is required; otherwise the request is rejected.
- `backup_acknowledged=true` is required. The endpoint does **not** create a backup automatically.
- Drafts in `blocked`, `cancelled`, `failed`, or `applied` states cannot be applied.
- Drafts with readiness `ready_with_warnings` require `allow_warnings=true`.
- PR80 apply-supported targets: `ingredients`, `clients`, `recipe_templates`, `packaging_items`.
- PR80 apply-unsupported targets: `ingredient_lots`, `orders`.
- Apply is transactional and all-or-nothing: if any row conflicts or insert fails, zero domain records are committed and the draft/source remain unapplied.
- Existing domain records are not silently updated. Duplicate records in the database or inside the draft return `409 Conflict`.
- Packaging import is catalog-only. A non-empty `stock` column is rejected because stock must be changed through movements.
- The frontend confirmation UI calls this endpoint only after explicit user confirmation; it does not apply domain data directly.
- No stock movements, ingredient lots, orders, production records, alerts, purchase suggestions, backups, or exports are created automatically.
- Applied drafts cannot be cancelled. Cancelling an applied draft returns `409 Conflict`; the draft/source stay `applied`, and created domain records are not rolled back by cancellation.

Successful response includes the updated draft, an apply result with created record ids/labels, and the message `Черновик импорта применён. Данные внесены в систему.` Conflicts return structured details where possible:

```json
{
  "detail": {
    "message": "Черновик нельзя применить.",
    "issues": [
      {
        "severity": "error",
        "code": "duplicate_domain_record",
        "message": "Компонент с названием «Масло ши» уже существует.",
        "row_number": 2,
        "field": "name"
      }
    ]
  }
}
```

Missing `confirm_apply` or `backup_acknowledged` returns a safe rejection; conflicts, unsupported targets, already-applied drafts, and duplicate records return conflict-style issues. Failed apply is all-or-nothing: the draft/source remain unapplied and zero partial domain rows are committed.

## Demo data API (PR84 backend foundation)

Demo data mode is explicit and safe-by-default. It never runs from migrations, startup, onboarding, import, backup, or export, and PR84 adds no frontend UI.

### `GET /api/demo-data/status`

Read-only status endpoint.

Example response:

```json
{
  "is_installed": false,
  "active_session_id": null,
  "demo_version": "mvp-1",
  "can_install": true,
  "can_clear": false,
  "has_business_data": false,
  "has_non_demo_business_data": false,
  "created_counts": {},
  "blocking_reasons": [],
  "message": "Демо-данные ещё не установлены."
}
```

### `POST /api/demo-data/install`

Installs a compact cosmetic-workshop demo dataset only after explicit confirmation and only when the workspace has no non-demo business rows.

Request:

```json
{
  "confirm_install": true,
  "understand_demo_data": true
}
```

Safety behavior:

- rejects missing confirmation with `400`;
- rejects active demo data with `409`;
- rejects non-empty real workspaces with `409` and the message `Демо-данные можно установить только в пустую рабочую базу. В этой базе уже есть рабочие данные.`;
- writes demo business rows and `demo_data_records` in one transaction;
- does not create production batches, backups, exports, or import apply targets.

### `POST /api/demo-data/clear`

Deletes only rows tracked in `demo_data_records` for the active demo session.

Request:

```json
{
  "confirm_clear": true
}
```

Safety behavior:

- rejects missing confirmation with `400`;
- rejects missing active demo data with `409`;
- preflights untracked dependencies and blocks with `409` if real records reference demo records, including direct table references plus generic `alerts.related_entity_type/id`, `purchase_suggestions.item_type/item_id`, and `purchase_suggestions.source_entity_type/id` references;
- deletes in reverse dependency order in one transaction;
- marks the demo session `cleared` only after successful deletes.

When an active demo session has unsafe working references, `GET /api/demo-data/status` returns `can_clear=false` and includes a Russian blocking reason so the future UI can ask the user to resolve those working records manually before clearing demo data.

## Report documents API

Report document endpoints are available under `/api/report-documents`. They create human-readable report documents explicitly and store them in the safe report-documents directory under the user data/export area. The API supports Markdown and, when the backend finds a parseable local TTF font with Cyrillic glyphs, PDF. DOCX requests are rejected with a clear Russian message.

Document generation reads backend `ReportsService` data and the saved display-only Workshop profile. Configured profile fields are included near the top of newly generated Markdown/PDF overview documents, but profile values are not stored in document metadata and do not affect report calculations. Generation does not mutate business records, existing generated documents, backup/export snapshots, imports, demo data, alerts, or purchase suggestions.

### `GET /api/report-documents/status`

Returns document export availability:

- `documents_dir`;
- `available_formats` (`["markdown", "pdf"]` when a parseable local TTF font with Cyrillic glyphs is available; TTC font collections are not supported, and otherwise PDF is omitted);
- `available_document_types` (`["workshop_overview"]` in the MVP);
- `can_create`;
- `documents_count`;
- `message`;
- `pending_audit_count` (CR-009 B1; documents whose Journal entry is not committed yet).

`pending_audit_count` is exactly the number of unresolved ledger operations
where `artifact_kind = report_document` and `status` is `prepared` or
`pending_audit`; it excludes `audited` and `abandoned`. This endpoint reads the
count and performs no reconciliation, creates no AuditLog row and mutates no
ledger or file state.

If the ledger cannot be read, this endpoint returns HTTP `500` with the safe
Russian detail `Не удалось прочитать сведения о документах отчетов. Данные
мастерской не изменялись.` rather than reporting `pending_audit_count: 0`. A
zero is a factual claim that nothing is awaiting a Journal entry, and the
frontend clears its standing warning on it, so it is never published for a count
that was not actually read. No SQLite message, SQL fragment, stack trace or
internal path is exposed, and the failed read still mutates nothing.

In normal operation the launcher makes this unreachable: `run_local_runtime`
passes the database path that `initialize_startup` backed up, migrated and
reconciled to the API child through `COSMETIC_WORKSHOP_DB_PATH`, so the API
always serves a database whose ledger exists.

### `GET /api/report-documents`

Returns generated document metadata newest first. Supports `limit` and `offset`.

Response fields include:

- `items`;
- `limit`;
- `offset`;
- `total`.

### `GET /api/report-documents/{document_id}/download`

Read-only access to an already generated report document file. The endpoint only serves files known from report document metadata under the safe report-documents directory; it is not a generic file browser and does not accept arbitrary paths or filenames.

Query parameters:

- `disposition=attachment|inline` (default `attachment`). `inline` is used for PDF opening; Markdown is returned as an attachment even if inline is requested.

Content types:

- PDF: `application/pdf`;
- Markdown: `text/markdown; charset=utf-8`;
- fallback: `application/octet-stream`.

Safe errors are returned for unknown document IDs, missing files, unsupported disposition values, and metadata/path mismatches. The endpoint does not create documents, mutate business data, create backup/import/demo data, or regenerate alerts/purchase suggestions.

### `POST /api/report-documents/reports/overview`

Creates a Markdown or PDF “Сводка мастерской” document from `/api/reports/overview` backend data and, when configured, display-only Workshop profile fields from Settings.

Request:

```json
{
  "format": "markdown",
  "reason": "monthly_check"
}
```

`format` defaults to `markdown`; `pdf` creates a PDF when advertised by status; `docx` remains unsupported. `reason` is optional and sanitized; it is not used as a filename.

Response includes created document metadata and the message `Документ отчета создан.`

Since C3-II-B1 the response additively carries the separate result of recording
the document in the Journal:

```json
{
  "document": { "...": "unchanged metadata" },
  "message": "Документ отчета создан.",
  "audit_status": "recorded",
  "audit_message": null
}
```

`audit_status` is `recorded` or `pending`. `recorded` always carries
`audit_message: null`; `pending` always carries the exact accepted Russian
warning below. Both are HTTP `201`: the document exists, is listed and is
downloadable in either case, and `message` keeps its existing meaning as the
artifact result.

If audit tracking cannot be durably prepared, no document, sidecar, AuditLog row
or ledger row is created, and the endpoint returns HTTP `500`:

```json
{
  "detail": {
    "code": "artifact_audit_tracking_unavailable",
    "message": "Не удалось безопасно подготовить создание документа. Документ не создан.",
    "next_action": "Повторите создание документа. Если ошибка повторяется, перезапустите приложение."
  }
}
```

Existing request-validation errors are unchanged and still take precedence: an
unsupported `format` is still rejected with `422` before anything is prepared.

### CR-009 create-result contract — B1 merged; B2 and B3 not authorized

`CR-009` accepts one additive API contract for user-created manual backups,
JSON exports and report documents. C3-II-B1 implements it for report documents
only, as documented above, and is merged into `main` through PR #163. The manual-backup and JSON-export response shapes
remain unchanged until their separately authorized runtime slice implements the
addition.

If bounded ledger preparation fails before file creation, no file and no
AuditLog row are created. The structured code is:

```text
artifact_audit_tracking_unavailable
```

The message means:

```text
Не удалось безопасно подготовить создание файла. Файл не создан.
```

For B1, inability to commit the prepared operation returns HTTP `500` with
this exact safe detail:

```json
{
  "detail": {
    "code": "artifact_audit_tracking_unavailable",
    "message": "Не удалось безопасно подготовить создание документа. Документ не создан.",
    "next_action": "Повторите создание документа. Если ошибка повторяется, перезапустите приложение."
  }
}
```

No document file, metadata file, AuditLog row or prepared ledger row is
committed. No partial success is claimed, and existing request-validation
errors remain unchanged.

After the artifact is fully written and verified, HTTP remains `201 Created`.
Ordinary audited success additively returns:

```json
{
  "message": "<existing artifact success message>",
  "audit_status": "recorded",
  "audit_message": null
}
```

If AuditLog finalization fails after artifact verification, the same artifact
response is returned with HTTP `201`, not `500` or `409`:

```json
{
  "message": "<existing artifact success message>",
  "audit_status": "pending",
  "audit_message": "Документ создан, но запись в журнал действий пока не добавлена. Приложение повторит попытку при следующем запуске или перед созданием следующего документа."
}
```

The exact message above applies to B1. Later B2/B3 must use an
artifact-specific warning that names the actual bounded triggers: the next
normal application startup and before creating the next artifact of that same
scoped kind. It must not imply immediate, periodic or background retry. Every
warning preserves artifact success and separates the pending-Journal warning.
The frontend shows success for the artifact, presents the warning separately,
and sends no duplicate create request.

C3-II-B1 adds `audit_status` and `audit_message` to
`POST /api/report-documents/reports/overview`, and `pending_audit_count` to
`GET /api/report-documents/status`. B1 exposes no path, filename, operation ID
or AuditLog metadata through those new fields.

`pending_audit_count` is exactly the count of unresolved ledger operations
where `artifact_kind = report_document` and `status` is `prepared` or
`pending_audit`. It excludes `audited` and `abandoned`. The status endpoint
reads this count but performs no reconciliation. Normal startup reconciliation
runs before the application serves the ordinary UI. A definitely absent
incomplete pair becomes `abandoned` and is no longer counted; an ambiguous,
unsafe or not-yet-finalized operation remains unresolved and counted. The
frontend presents the count only as a pending-Journal warning, not as failed
document creation.

The same accepted result semantics now cover JSON export. `C3-II-B2` is
`IMPLEMENTED ON PR BRANCH — NOT MERGED`, so `audit_status` / `audit_message` on
`POST /api/exports` and `pending_audit_count` on `GET /api/exports/status` exist
on that branch and are **not yet on merged `main`**. Manual backup keeps the
reserved semantics only: `C3-II-B3` remains blocked by CR-004. Durable contracts:
`docs/decisions/0013-file-backed-artifact-audit-semantics.md` and
`docs/decisions/0014-json-export-create-confirmation-semantics.md`.

## Reports API

Read-only operational reports are available under `/api/reports`. Reports do not mutate business data, do not create audit logs, do not create backup/export files, and do not regenerate alerts or purchase suggestions.

All report responses include `generated_at` and `warnings`.

### `GET /api/reports/overview`

Returns one combined operational snapshot:

- `inventory_summary`
- `orders_summary`
- `production_summary`
- `alerts_summary`
- `purchase_summary`
- `finance_summary`
- `warnings`

### `GET /api/reports/inventory`

Returns stock-health counters:

- active ingredients;
- active ingredient lots;
- lots with positive balance;
- expired and expiring-soon lots;
- active packaging items;
- packaging items with positive balance;
- open low-stock alerts;
- open purchase suggestions.

This endpoint reads existing alerts and purchase suggestions only; it does not regenerate them.

### `GET /api/reports/orders`

Returns order pipeline counters by status:

- total and active orders;
- `new`;
- `waiting_for_materials`;
- `ready_to_produce`;
- `in_progress`;
- `produced`;
- `delivered`;
- `cancelled`;
- `archived`;
- orders missing recipe references if such invalid legacy data exists.

### `GET /api/reports/production`

Returns all-time production summary:

- total production batches;
- batches in period (same as total in PR87 because date filters are not implemented);
- last production date;
- produced orders count;
- produced quantity totals grouped by unit;
- total known production cost;
- missing cost warnings.

Quantities are grouped by unit instead of being silently summed across incompatible units.

### `GET /api/reports/finance`

Returns a basic operational financial snapshot, not accounting:

- produced order count;
- produced orders with sale price;
- known revenue;
- known production cost;
- known tax;
- known margin;
- known margin percent;
- complete finance record count;
- incomplete margin count;
- missing sale price count;
- missing cost count;
- tax snapshot record count and missing tax snapshot count;
- margin snapshot record count and missing margin snapshot count.

The report uses Decimal-safe string values. It does not invent tax or apply a hidden tax rate, and it never reads the current Settings tax rate. `known_revenue` and `known_production_cost` are independent known totals over every non-null persisted value; `known_tax` and `known_margin` are sums of the persisted `ProductionBatch` snapshots and are never reconstructed from sale price and cost.

#### `C2-III-B` snapshot-backed finance contract

Status: **IMPLEMENTED** and merged as PR #157. On merged `main` the response carries the additive fields below and margin comes from persisted snapshots; the pre-`C2-III-B` shape, with margin derived from paired sale price and cost, is historical. The full contract is in `docs/reports.md` § *Accepted `C2-III-B` snapshot aggregation contract*, and the aggregation lives in `backend/app/domain/report_financials.py`.

`known_margin` is the sum of persisted `ProductionBatch.margin` over exactly the rows whose margin snapshot is non-null (`M`), and:

```text
known_margin_percent =
    ROUND_PERCENT(
        Σ margin over M ÷ Σ sale_price over M × 100
    )
```

The denominator uses sale prices from exactly the rows contributing to the numerator — never the global `known_revenue` total, and never an average of persisted row `margin_percent` values. It is `null` when `M` is empty or that denominator is zero.

Authorized additive `FinanceReportResponse` fields:

| Field | Type | Meaning |
|---|---|---|
| `known_tax` | `str \| null` | sum of every non-null persisted `ProductionBatch.tax`; `null` when no row has a tax snapshot |
| `tax_snapshot_record_count` | `int` | rows where persisted `tax` is non-null |
| `missing_tax_snapshot_count` | `int` | rows where persisted `tax` is null |
| `margin_snapshot_record_count` | `int` | rows where persisted `margin` is non-null |
| `missing_margin_snapshot_count` | `int` | rows where persisted `margin` is null |

Each pair sums to `produced_order_count`. The existing `complete_finance_record_count` and `incomplete_margin_count` keep their current paired sale-price/cost meanings for backward compatibility and are **not** snapshot-coverage counters. Additive warning codes: `tax_unavailable`, `partial_tax_basis`, and `margin_percent_unavailable_zero_basis`. `OverviewReportResponse.finance_summary` uses the same `FinanceReportResponse` with no overview-only fields or calculations. Reports never read the current Settings tax rate and never recalculate a historical row.

## AuditLog API (`C3-I`)

Status: `DONE — MERGED AND EXACT-HEAD VERIFIED`. PR #159 merged the endpoint into `main` from final reviewed head `bf7cde060a43190fdf22c612a16b0c137aa5531b` at merge commit `ba3ca7443e3280bc7f700af11e75dc4fa810665f` on `2026-07-30T03:20:23Z`. The durable product, API, privacy and presentation contract is `docs/audit-log.md`; this section is the API-shaped summary of it and defers to that file on any disagreement.

Implementation: `backend/app/api/audit_logs.py` → `backend/app/services/audit_logs.py` → `backend/app/repositories/audit.py`, with the pure `backend/app/domain/audit_log_presentation.py` and `backend/app/domain/audit_log_query.py`. Response schemas live in `backend/app/schemas/audit_logs.py`. **No migration** was added; the only enum addition is `DomainIssueCode.PAGINATION_OUT_OF_RANGE`.

### `GET /api/audit-logs`

The **only** authorized AuditLog endpoint. Read-only, and the only new endpoint in `C3-I`. No create, update, delete, rollback or export endpoint is authorized.

**Superseded.** The `docs/roadmap.md` § PR27 proposal `GET /api/audit-logs/{id}` is **explicitly superseded for the MVP**: the user goal is satisfied by a filtered readable list, raw metadata and technical detail increase privacy and complexity risk, a detail endpoint is not needed to understand the important action, and it may be reconsidered only through a separate future product decision.

#### Query parameters

| Parameter | Rule |
|---|---|
| `created_from` | ISO-8601 UTC, **inclusive** |
| `created_before` | ISO-8601 UTC, **exclusive**; `created_before <= created_from` is rejected |
| `action` | stable action code |
| `entity_type` | stable entity code |
| `actor_type` | stable actor code |
| `limit` | omitted → `50`; valid range integer `1..200` |
| `offset` | omitted → `0`; valid range integer `0..9223372036854775807` |

There is **no `source` filter**. Filters combine with logical **AND**. Empty filters return the latest events. Filtering performs no writes.

#### Response

```text
items
total
limit
offset
filter_options
```

`total` counts the rows matching the filters before `limit`/`offset`; `limit` and `offset` echo the effective applied values, which differ from the request only when a parameter was omitted and its default applied. `filter_options` lists the distinct `action`, `entity_type` and `actor_type` values that **actually exist as rows** in `audit_logs`, each with a safe Russian label.

The exact nested `filter_options` DTO — `docs/audit-log.md` § 7.5.1, the one implementation-level clarification `C3-I` adds:

```json
{
  "filter_options": {
    "actions": [{ "value": "client.created", "label": "Клиент создан" }],
    "entity_types": [{ "value": "client", "label": "Клиент" }],
    "actor_types": [{ "value": "system", "label": "Система" }]
  }
}
```

Each option carries **exactly** `value` and `label`. Values come from rows that actually exist, so a fresh database does not list all 51 known actions. Options are derived from the whole table rather than the current page, so they do not change when the result filters change, and they are ordered deterministically by raw persisted value ascending. An unknown persisted code stays present under its safe fallback label and is never shown as a raw code.

**`null` is omitted from `filter_options.entity_types`.** It is not an authorized query code and could not be offered without inventing a filter sentinel, and no new query parameter or sentinel is authorized. Rows with `entity_type IS NULL` remain fully readable as items carrying `entity_label: "Другая сущность"`.

A blank filter value (`action=`, `entity_type=`, `actor_type=`, `created_from=`, `created_before=`) is the empty-`<option>` "no filter" state and is treated as absent. A blank `limit` or `offset` is instead a malformed pagination value and is rejected, never defaulted.

Each item contains exactly:

```text
id
created_at
action
action_label
entity_type
entity_label
display_summary
actor_type
actor_label
```

- `id` is an internal row identity and is not displayed as a business value;
- `created_at` is ISO-8601 UTC; the SQLite `YYYY-MM-DD HH:MM:SS` storage form is never exposed;
- `action`, `entity_type` and `actor_type` are stable codes; `entity_type` may be `null`;
- `action_label`, `entity_label` and `actor_label` are Russian user-facing labels, with the safe fallbacks `Другое действие`, `Другая сущность` and `Другой инициатор` for unknown codes;
- `display_summary` is a **backend-owned safe Russian presentation value** resolved from `action`, never the raw persisted summary.

#### `actor_type`, not `source`

The API field keeps the persisted column name `actor_type`, and **no `source` field is exposed**. The values `system` and `user` describe the **actor that initiated the action**, not a process origin. Presenting them as a `source` would silently change the field's meaning, so `C3-I` does not.

The historical process vocabulary — `manual`, `import`, `production`, `migration`, `backup`, `onboarding`, `restore` — is **aspirational**: no write call site persists that dimension, so a true `source` field cannot be implemented truthfully. It is **deferred** to a separately authorized product decision and write-side slice. The column is not renamed, no migration or backfill is authorized, and no existing write call site changes.

Labels: `system → Система`, `user → Пользователь`, anything else → `Другой инициатор`.

#### `display_summary`

The raw persisted `audit_logs.summary` is **never returned verbatim and is never used as an unrestricted API or frontend fallback**. It is write-time technical text: mostly English, several values embed internal record IDs (`Ingredient lot created for ingredient #12`, `Order #4 produced as batch #7`), and `client_wish.*` values embed user-authored wish text.

A focused backend presenter — `AuditLogDisplayPresenter`, or an equivalently focused module consistent with the repository structure — resolves `display_summary` from the known `action`. It never includes an internal ID, never includes metadata, performs no business-table join, rewrites no historical row, and never exposes wish text, client notes, allergies, addresses or feedback bodies.

```text
Ingredient lot created for ingredient #12  →  Создана партия компонента
Order #4 produced as batch #7              →  Производство заказа подтверждено
Client wish created: Убрать компонент X    →  Пожелание клиента добавлено
```

**Bounded suffix extraction.** A suffix taken from the persisted summary may contribute to `display_summary` only when **all seven** conditions hold: the action is explicitly allowlisted; the persisted summary starts with the exact prefix assigned to that action; the remaining suffix is non-empty; the action is authorized to retain that category of business name; the suffix is rendered only as plain text; the suffix contains no internal identifier supplied by the presenter; and no database or metadata lookup is performed. Otherwise `display_summary` falls back to the generic action-specific phrase.

The allowlist is the exact 21-row table in `docs/audit-log.md` § 6.4.3 — `client.created` / `.updated` / `.deactivated`, `ingredient.created` / `.updated` / `.deactivated`, `packaging_item.created` / `.updated` / `.deactivated`, `recipe_template.created` / `.deactivated`, `order.created` / `.updated` / `.cancelled` / `.archived`, `catalog_category.created` / `.updated` / `.archived`, and `catalog_tag.created` / `.updated` / `.archived` — each with its exact English prefix, for example `Client created: ` → `Клиент создан: <имя>` with the fallback `Клиент создан`. It is **not** a prefix glob: `client_wish.*`, `client_recipe.*`, every ID-bearing action (`ingredient_lot.*`, `stock_movement.created`, `packaging_stock_movement.created`, `production_confirmed`, `recipe_version.created`) and every catalog-assignment action are excluded. Returning the complete persisted summary, returning its English technical prefix, or using it as an unrestricted fallback all remain prohibited.

### Workshop-profile audit behavior (`C3-II-A`)

Status: `DONE — MERGED AND EXACT-HEAD VERIFIED` (PR #161).

`C3-II-A` adds **no endpoint** and preserves the existing workshop-profile request and response shape:

```text
GET /api/settings/workshop-profile
PUT /api/settings/workshop-profile
```

A real canonical `PUT` change must persist `app_settings.workshop_profile` and exactly one `workshop_profile.updated` AuditLog row in one caller-owned SQLite transaction. An AuditLog failure rolls the profile write back and the API returns failure; a profile persistence failure commits no AuditLog row. A canonically identical request returns the current profile with a normal Russian no-change message, performs no upsert, preserves `updated_at` and creates no AuditLog row. `GET` remains read-only.

The exact no-change message is:

```text
Профиль мастерской уже сохранён без изменений.
```

Missing row plus empty request and existing empty row plus empty request are no-ops. Configured profile plus an all-empty request is a real mutation that persists canonical empty JSON without deleting the row and writes exactly one event.

The existing response fields, profile field names, validation limits, Unicode normalization and control-character rules do not change. No raw summary, metadata, profile value or internal settings payload is added to any response. `GET /api/audit-logs` presents the new action only through backend-owned `action_label`, `entity_label` and `display_summary`; it still returns the exact nine-field item and never returns raw `summary` or `metadata_json`.

Audit metadata contains exactly `setting_key`, `changed_fields`, `changed_field_count`, `previous_configured`, and `new_configured`. `changed_fields` is sorted and limited to the four profile field identifiers. No profile value, raw JSON, timestamp, `source`, request payload or response payload is stored.

Atomic persistence failures return:

```json
{
  "detail": {
    "code": "workshop_profile_not_saved",
    "message": "Не удалось сохранить профиль мастерской. Предыдущие данные сохранены без изменений.",
    "next_action": "Повторите сохранение. Если ошибка повторяется, проверьте, что локальное приложение работает."
  }
}
```

HTTP status is `500`. Existing validation `422`, database-not-initialized `409`, and successful response model remain unchanged.

`CR-009` has since accepted the durable artifact-primary, partial-success,
bounded-ledger and reconciliation contract. Its report-document slice
C3-II-B1 merged as PR #163 (merge commit
`ef0297e41a731f082a2a21a46b361aa9aac36cfa`); export and backup slices remain
blocked by CR-006 and CR-004. Neither the CR-009 documentation PR nor the B1
closure documentation PR changes these runtime endpoints or response schemas.

#### Validation responses

The existing router convention raises `HTTPException(status_code=422, detail=issue.__dict__)`, so the `DomainIssue` object is the **value of `detail`**, not the whole body. The exact wire response is:

```json
{
  "detail": {
    "code": "invalid_date",
    "message": "Russian user-readable message",
    "field": "created_from",
    "value": "the rejected value",
    "next_action": "Russian user-readable next action"
  }
}
```

| Condition | `code` |
|---|---|
| malformed or invalid `created_from` / `created_before` | `invalid_date` |
| `created_before <= created_from` | `invalid_date` |
| non-integer, fractional, boolean or malformed `limit` / `offset` | `non_integer_quantity` |
| negative `limit` / `offset` | `negative_quantity` |
| non-negative `limit` outside `1..200` — that is, `0` or `> 200` | `pagination_out_of_range` |
| `offset` greater than `9223372036854775807` | `pagination_out_of_range` |

`invalid_date`, `non_integer_quantity` and `negative_quantity` already exist in `DomainIssueCode`. `pagination_out_of_range` (`PAGINATION_OUT_OF_RANGE = "pagination_out_of_range"`) is the one new enum member authorized by `C3-I`, because no existing member carries out-of-range pagination semantics; it must not be replaced by `percentage_out_of_range`, `invalid_category`, `invalid_decimal` or `zero_quantity`. It is a bounded enum addition, not a schema change or migration.

**Ordered validation precedence.** The checks run in this exact order and the first match decides the code, so every invalid input maps to exactly one code:

```text
1. Missing value        limit → default 50; offset → default 0
2. Wrong type/repr      non-integer, fractional, boolean, malformed string → non_integer_quantity
3. Negative integer     limit < 0, offset < 0                              → negative_quantity
4. Non-negative value outside range
   limit == 0, limit > 200, offset > 9223372036854775807                   → pagination_out_of_range
5. Accepted             limit: integer 1..200; offset: integer 0..9223372036854775807
```

Because step 3 precedes step 4, a negative `limit` is **only** `negative_quantity`; because step 4 is reached only by a non-negative integer, `limit == 0` and `limit > 200` are **only** `pagination_out_of_range`.

```text
limit=true  → non_integer_quantity      limit=-1  → negative_quantity
limit=1.5   → non_integer_quantity      offset=-1 → negative_quantity
limit=abc   → non_integer_quantity      limit=0   → pagination_out_of_range
limit=200   → accepted                  limit=201 → pagination_out_of_range
limit=-0    → pagination_out_of_range   limit=0001   → accepted as 1
limit=000201 → pagination_out_of_range  offset=-0    → accepted as 0
offset=0000 → accepted as 0
offset=9223372036854775807 → accepted
offset=9223372036854775808 → pagination_out_of_range
```

**An explicitly supplied invalid pagination value is rejected, never silently clamped, coerced, rounded or ignored.**

The upper bound is SQLite's largest bindable signed 64-bit `OFFSET`. Decimal
shape, sign and range are checked on the raw text before integer conversion, so
arbitrary 5000-digit positive values are `pagination_out_of_range`, arbitrary
5000-digit negative values are `negative_quantity`, the rejected value is
echoed only as a bounded excerpt, and no oversized value reaches Python `int()`
or SQLite. These rejections keep the exact structured `422` envelope above and
remain read-only.

**Date-range conflict.** For `created_before <= created_from` the exact structured error is HTTP `422`, `code: invalid_date`, **`field: created_before`**, `value:` the supplied `created_before` value. The Russian `message` explains that the end of the period must be later than its beginning, and the Russian `next_action` tells the user to select an end date later than the start date. Do not use an undefined synthetic field such as `date_range`.

#### Never returned

The raw persisted summary, raw `metadata_json`, `entity_id`, internal entity IDs reached by any route, raw table names, stack traces, SQL, filesystem paths, raw payloads, secrets, and any reconstruction of sensitive client notes, allergies, addresses, wishes or feedback text. The read model is built from `audit_logs` alone and joins no business table.

#### Read-only guarantees

Reading the journal writes no AuditLog record, mutates no business table, creates no file, changes no setting, triggers no regeneration, and performs no cleanup or normalization of historical rows. AuditLog stays append-only — the presenter changes only what is shown, never what is stored.

Ordering is `created_at DESC, id DESC`. Unbounded history is never returned.

## Workshop profile settings API

`GET /api/settings/workshop-profile` returns the local workshop profile from backend settings storage. Empty defaults are safe and mean the profile is not configured.

`PUT /api/settings/workshop-profile` explicitly replaces the complete workshop profile object:

```json
{
  "workshop_name": "Мастерская косметолога",
  "master_name": "Мария Чистякова",
  "workshop_contact_text": "Телефон: +7 ...",
  "workshop_note": "Индивидуальная косметика и уход"
}
```

The endpoint trims strings, allows empty values, rejects overlong values and unsafe control characters, and updates only the grouped `workshop_profile` app setting. It does not mutate business data, create files, run backup/export/import/demo/report-document actions, or recalculate reports, recipes, orders, production, stock, costs, taxes, or margins.

`GET /api/settings/status` marks `workshop_name`, `master_name`, `workshop_contact_text`, `workshop_note`, and `default_tax_rate` as `editable_now`; every other calculation-sensitive setting remains `requires_backend_rules`.

## Tax-rate settings API

Status: **IMPLEMENTED AND MERGED (`C1-I`, PR #149) — VERIFIED FROM MERGED PR EVIDENCE.** These endpoints exist on merged `main` at `ff7afe6b0778ab2b348229a4df34acf3e3fc0001`. They were decided in `CR-007` and delivered by `C1-I — Implement backend-owned tax-rate setting`, whose final reviewed head `1c01c05c861c4008ad6304210dbd65d9fd8dcdf9` passed the exact-head `/settings` smoke (`146 checks / 0 failures`) before merge on `2026-07-27T19:44:53Z`. The durable product contract is `docs/settings.md`; the slice contract is `docs/implementation-plan.md`.

The endpoints live under the existing `/api/settings` surface and use the existing `app_settings` persistence with the key `default_tax_rate`. No new settings table, column, or migration is introduced.

```text
GET /api/settings/tax-rate
PUT /api/settings/tax-rate
```

`PUT` request — configure or change the rate:

```json
{
  "tax_rate_percent": "6.00"
}
```

`PUT` request — explicit clear:

```json
{
  "tax_rate_percent": null
}
```

Response shape for both `GET` and `PUT`:

```json
{
  "is_configured": true,
  "tax_rate_percent": "6.00",
  "effective_at": "2026-07-27T10:28:54Z",
  "message": "Налоговая ставка для расчётов сохранена."
}
```

When the setting is not configured — including after an explicit Clear — `is_configured` is `false`, `tax_rate_percent` is `null`, and `effective_at` is `null`.

Contract rules:

- `tax_rate_percent` is a **percentage** decimal string, not a coefficient — `"6.00"` is `6%` and `"0.06"` is `0.06%`;
- the accepted range is `0.00` to `100.00` inclusive, with at most two fractional digits on input;
- excess precision such as `"6.005"` is **rejected**, never rounded;
- floats, `bool`, `NaN`, `Infinity`, and malformed values are rejected;
- an empty string is not a substitute for `null`;
- `null` means clear/unconfigure, and `0.00` means an explicitly configured zero-percent estimate — the two are never equivalent;
- validation failures return HTTP `422` with the project structured `detail` object — `code`, `message`, `field` (`tax_rate_percent`), `value`, `next_action` — and a human-readable Russian `message`. The stable codes are `invalid_tax_rate_type`, `invalid_tax_rate_format`, `tax_rate_precision_exceeded`, and `tax_rate_out_of_range`;
- a failure to persist the setting atomically with its audit record returns HTTP `500` with a safe structured `detail` and leaves the previous value, timestamp, and row presence unchanged;
- a real mutation writes an `AuditLog` (`tax_rate_setting_changed` / `app_setting` / `default_tax_rate`) **atomically** with the persistence change; if the audit write fails, the change rolls back;
- a no-op — the canonical persisted state would not change — returns the current representation without writing or deleting the setting, without changing `effective_at`, without creating an `AuditLog`, and without claiming the rate changed;
- `GET` is read-only and is never audited.

**Canonical two-decimal representation.** `tax_rate_percent` in a response always carries exactly two fractional digits, and the persisted `default_tax_rate` value uses the same canonical form. Canonical formatting is applied after validation, never to absorb excess precision: `6` → `"6.00"`, `6.0` → `"6.00"`, `6.00` → `"6.00"`, `0` → `"0.00"`, `100` → `"100.00"`, while `6.005` is rejected and must never become `6.01`. The no-op comparison uses that exact canonical string, so `PUT` with `"6"` against a stored `"6.00"` is a no-op.

**`effective_at` semantics.** It is the timestamp of the currently active setting, backend-generated, never client-supplied, and never backdated, scheduled, or edited. Because SQLite `CURRENT_TIMESTAMP` has one-second precision, the service applies a monotonic tie-break for `default_tax_rate` only: successive real changes always receive strictly increasing timestamps, using the previous timestamp plus one second when the current second is not later. First configuration and a real rate change each produce a new value; a no-op keeps the existing one; an explicit Clear returns `effective_at: null`, because there is no active setting to timestamp — the clear event time lives in `AuditLog.created_at`, and the clear audit metadata carries `previous_effective_at` plus `new_effective_at: null`. The stored source is the existing `AppSetting.updated_at` column, which remains persisted in SQLite's `YYYY-MM-DD HH:MM:SS` UTC format; the service normalizes it and only the API exposes ISO-8601 UTC. The database does not store ISO-8601, and `C1-I` changes no column, default, or migration.

**Clear is row deletion.** `PUT` with `tax_rate_percent: null` deletes the `default_tax_rate` `AppSetting` row and nothing else. It never touches the legacy `tax.default_rate` placeholder row, which is a different key and is never read, reinterpreted, migrated, or rewritten. The deletion and its `AuditLog` insert share one transaction, and a failed audit insert rolls the deletion back. Clearing when the row is already absent is a no-op: no delete, no timestamp change, no `AuditLog`, and no message claiming a change. No nullable-column migration, sentinel value, empty-string storage, new settings table, or parallel settings store is authorized — unconfigured is the absence of the row.

The endpoints themselves do not calculate tax, do not calculate margin, do not touch orders, production batches, stock, reports, or documents, and never mutate historical records. `CR-008` decided the C2 contract and divided it into `C2-I` (**merged**, PR #151), `C2-II` (**merged**, PR #152), and `C2-III`, which was subdivided into `C2-III-A` (**merged**, PR #154) and `C2-III-B` (**merged**, PR #157). C2 is **COMPLETED**. The `C2-I` readiness estimate reads the setting through the existing C1 service and writes nothing; `C2-II` reads it again inside the production transaction through the same service and persists immutable snapshots. The `GET`/`PUT` endpoints themselves are unchanged by both. See the `C2-I` financial estimate extension under production readiness and the `C2-II` financial snapshot extension under production confirmation.

## Orders write validation contract

`POST /api/orders` and `PUT /api/orders/{order_id}` use backend-authoritative validation. Domain validation failures from Order draft construction return HTTP `422` with a structured `detail` object containing `code`, `message`, `field`, `value`, and `next_action`. Standard FastAPI/Pydantic request validation, including forbidden lifecycle fields (`status`, `produced_at`, `delivered_at`) and invalid enum/type input, keeps the standard HTTP `422` detail-list shape.

Positive IDs that reference missing linked records remain `404`. Inactive, mismatched, cancelled, archived, or otherwise lifecycle-conflicting linked records remain `409`. Production Readiness and Production Confirmation validation are separate API slices and are not changed by A3.7.


### A3.9 Production Confirmation error boundary

`POST /api/orders/{order_id}/produce` keeps the explicit `{ "confirm": true }` contract. The endpoint returns the project structured error shape in `detail` with safe `code`, `message`, and optional `next_action`. Missing Orders or linked sources are `404`; missing explicit confirmation and structured validation are `422`; lifecycle/readiness/stock/existing-batch conflicts are `409`; unexpected failures are `500` with a safe recovery message and no raw internals.
