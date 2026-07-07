# API Contract

Status: evolving implementation contract. Existing implemented areas have backend routes in the application; planned sections remain placeholders until their scoped PRs define them.


## Settings status

`GET /api/settings/status` returns the read-only Settings status foundation. It reports local-first app information, local data separation, safe workflow capabilities, and a Settings Decision Matrix. The endpoint is deterministic and read-only: it does not create files, mutate business data, persist settings, run migrations, trigger backup/export/import/demo/report-document actions, or regenerate alerts/purchases. PR96 marks only workshop profile fields as `editable_now`; calculation-sensitive settings remain closed.

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

## Manual Backups API (PR73)

Manual backups are explicit local SQLite safety copies. The API does not restore databases, delete backups, download backup files, export business tables as CSV/XLSX, schedule background backups, or use cloud storage. Status and list endpoints are read-only: they must not create directories, databases, backup files, migrations, exports, imports, stock movements, orders, production batches, alerts, or purchase suggestions.

### `GET /api/backups/status`

Returns the current configured SQLite database path, whether that database exists, the selected backup directory, whether it exists, the number of listed backups, and the latest backup if any. This endpoint is read-only and does not create the database or backup directory.

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
  }
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

Creates an explicit manual backup of the currently configured SQLite database by copying the source database into the selected backup directory. The API does not accept arbitrary source or destination paths. Existing backup files are never overwritten.

Request body is optional; missing, null, or blank `reason` becomes `manual`. Reasons are limited to 80 characters and are sanitized for filenames by the backup service.

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
  "message": "Резервная копия создана."
}
```

If the database file is missing, the endpoint returns `404` with a human-readable Russian message. If the configured database path exists but is not a file, it returns `409`.

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

`reason` is optional, trimmed, defaults to `manual` when empty, and is limited to 80 characters. It is stored in the export manifest and sanitized only for the filename segment.

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

Report document endpoints are available under `/api/report-documents`. They create human-readable report documents explicitly and store them in the safe report-documents directory under the user data/export area. After PR92 the API supports Markdown and, when the backend finds a parseable local TTF font with Cyrillic glyphs, PDF. DOCX requests are rejected with a clear Russian message.

Document generation reads backend `ReportsService` data, does not mutate business records, does not create backup/export snapshots, and does not regenerate alerts or purchase suggestions.

### `GET /api/report-documents/status`

Returns document export availability:

- `documents_dir`;
- `available_formats` (`["markdown", "pdf"]` when a parseable local TTF font with Cyrillic glyphs is available; TTC font collections are not supported in PR92, and otherwise PDF is omitted);
- `available_document_types` (`["workshop_overview"]` in the MVP);
- `can_create`;
- `documents_count`;
- `message`.

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

Creates a Markdown or PDF “Сводка мастерской” document from `/api/reports/overview` backend data.

Request:

```json
{
  "format": "markdown",
  "reason": "monthly_check"
}
```

`format` defaults to `markdown`; `pdf` creates a PDF when advertised by status; `docx` remains unsupported. `reason` is optional and sanitized; it is not used as a filename.

Response includes created document metadata and the message `Документ отчета создан.`

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
- known margin calculated only from rows where sale price and production cost are both known;
- known margin percent calculated from the same paired revenue basis;
- complete finance record count;
- incomplete margin count;
- missing sale price count;
- missing cost count.

The report uses Decimal-safe string values. It does not invent tax or apply a hidden tax rate. `known_revenue` and `known_production_cost` are independent known totals, but `known_margin` never combines revenue from one incomplete batch with cost from another incomplete batch. Warnings include `margin_unavailable` when no paired sale+cost row exists and `partial_margin_basis` when margin is based on a subset of complete rows.

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

`GET /api/settings/status` now marks only `workshop_name`, `master_name`, `workshop_contact_text`, and `workshop_note` as `editable_now`; calculation-sensitive settings remain `requires_backend_rules`.
