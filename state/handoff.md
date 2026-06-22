# Handoff

## Last completed work
Implemented PR16 ingredient catalog UI foundation. Added a `Компоненты` frontend route at `/ingredients` that uses the existing `/api/ingredients` endpoints for active-list, create, full update, and soft deactivation. The UI includes loading, empty, error, create, edit, and deactivate states/actions and adds no ingredient lots UI, stock movement UI, packaging write flows, recipes, clients, orders, production, purchase list, alerts, backend migrations, new tables, imports, cloud, mobile, OCR, auth, or roles.

Implemented PR15 inventory overview UI foundation. Added a read-only `Склад` frontend route at `/inventory` that uses the existing `/api/inventory/overview`, `/api/inventory/ingredient-lot-balances`, and `/api/inventory/packaging-balances` endpoints for overview cards and stock tables. The UI includes loading, empty, and error states and adds no write forms, backend migrations, alerts, purchase list, production, recipes, clients, orders, imports, cloud, mobile, OCR, auth, or roles.

Implemented PR13 packaging stock movements foundation. Added `packaging_stock_movements`, pieces-only movement validation, service/repository/API create/read/list endpoints, movement-derived packaging balances, negative-balance prevention, and transactional `packaging_stock_movement.created` audit logging. No packaging lots, purchase list, production behavior, recipes, clients, orders, import/export, frontend UI, launcher behavior, or cloud/mobile/auth scope was added.

Implemented PR12 transactional write services foundation. Added a small SQLite transaction helper and updated ingredient, ingredient lot, stock movement, packaging item, and audited onboarding write services to commit entity/state changes and audit logs atomically. Repository write methods can now use a shared connection, and rollback tests cover simulated audit failures, validation failures, and stock movement derived balance safety. No migrations, tables, public API routes, frontend code, launcher behavior, or schemas were added.

Implemented PR11 hotfix for stock movement table guard cleanup. `backend/app/tests/test_stock_movements.py` now uses the centralized table guard helpers so `packaging_items` is accepted as a current PR11 table while future recipe/client/order/production/import/backup tables remain forbidden.

Implemented PR11 packaging foundation. The backend now has a `packaging_items` migration, packaging item domain validation, repository/service/API operations for create/read/list/update/deactivate, and minimal `packaging_item.created`, `packaging_item.updated`, and `packaging_item.deactivated` audit events. Packaging remains a directory only: no packaging stock movements, balances, lots, `remaining_quantity`, `current_quantity`, production consumption, purchase suggestions, or frontend UI were added.

Previously implemented PR10 stock movements foundation. The backend now has a `stock_movements` migration, immutable movement domain validation, repository/service/API operations for create/read/list/list-by-lot/balance, negative-balance prevention, and a minimal `stock_movement.created` audit event. Current lot quantity is derived from movement history and no `remaining_quantity` or stored balance was added to ingredient lots. PR10 hotfix follow-up keeps those table guards in `backend/app/tests/table_guards.py` so future-table policy remains test-only; `stock_movements` is current and future business tables remain forbidden.

Previously implemented PR9 ingredient lots foundation. The backend now has an `ingredient_lots` migration, lot domain validation, repository/service/API operations for create/read/list/update/deactivate, and minimal audit events for lot creation, update, and deactivation. Lots belong to existing active ingredients and carry batch metadata such as lot code, supplier, purchase/expiration dates, unit, optional Decimal-backed costs, optional density, and notes.

Previously implemented PR8 first-run onboarding skeleton. The backend stores onboarding state as typed JSON in the existing `app_settings` table, exposes thin `/api/onboarding` endpoints, and records minimal audit events for starting, completing a step, and completing onboarding or skipping/closing the checklist. The frontend Dashboard shows a warm Russian welcome/checklist experience and graceful backend-unavailable fallback.

## Current repo state
PR13 adds backend packaging/tare stock accounting through immutable packaging stock movements and derived balances. PR12 adds backend transaction safety for existing write services without schema or API changes. No backend migrations or launcher code changed for PR16. Minimal local-first foundation exists. Backend exposes stable health payloads, technical database/settings endpoints, ingredients endpoints, ingredient lot endpoints, stock movement endpoints, packaging item endpoints, packaging stock movement endpoints, and onboarding endpoints. Frontend remains a branded local-first shell with onboarding, placeholders, the PR15 read-only inventory overview, and the PR16 component directory write UI for basic ingredients only. No ingredient lot, stock movement, packaging write, recipe, client, order, production, import/export, purchase, or alert frontend flows exist yet. No real recipe/client/order/packaging stock/production/import/export/backup UI flows were implemented.

## Important decisions
- Repo: `cosmetic-workshop-os`
- Product: `Мастерская косметолога`
- MVP remains local-first and API-first.
- SQLite is used for the persistence foundation.
- Ingredient lots remain batch metadata; stock accounting is now represented by immutable stock movements connected to lots.
- PR11 does not add packaging stock movements, packaging lots, packaging balances, quantity columns, production consumption, recipes, orders, clients, imports, purchase suggestions, or frontend UI.
- PR10 does not add `remaining_quantity`, materialized balances, FEFO allocation, production write-off, recipes, orders, packaging inventory, packaging movements, or frontend inventory UI.
- Lot creation/update requires an existing active ingredient. Missing ingredients return not found at API level; inactive ingredients return conflict.
- Lot density is optional and never assumed. Costs and density reject floats and are stored as Decimal strings.
- Existing database/startup decisions from PR2-PR4 remain unchanged.
- Existing launcher decisions from PR7 remain unchanged.

## Known issues
- In this Codex environment, full FastAPI/Starlette `TestClient` test runs can be blocked if backend test dependencies are not installed. Attempting `python3 -m pip install -e 'backend[test]'` was blocked by registry/proxy 403 while fetching build dependencies.
- Frontend onboarding fetches `/api/onboarding`; if the frontend is served separately without the backend proxy/runtime, it intentionally falls back to a non-technical unavailable state.

## Next recommended task
PR17 is now implemented: backend recipe model foundation with RecipeTemplate -> RecipeVersion -> RecipeIngredient. Proceed to PR17 review/merge, then the next roadmap-scoped task. Do not add FEFO allocation, automatic production write-off, packaging inventory/movements, recipes, clients, orders, production, imports, exports, backup UI, restore UI, cloud, mobile, OCR, auth or roles until explicitly scoped by the next task.

## Commands to rerun during handoff
- `git status --short`
- `git branch --show-current`
- `python3 -m py_compile $(find backend/app launcher -name '*.py')`
- `python3 -m pytest backend/app/tests/test_domain_primitives.py launcher/tests`
- `cd backend && python3 -m pytest app/tests/test_packaging_items.py`
- `cd backend && python3 -m pytest app/tests/test_stock_movements.py`
- `cd backend && python3 -m pytest app/tests/test_ingredient_lots.py`
- `cd backend && python3 -m pytest`
- `cd frontend && npm run build`
- `make test`
- `make build`
- `git diff --name-only`

## PR9 notes
- Ingredient lot endpoints:
  - `POST /api/ingredient-lots`
  - `GET /api/ingredient-lots`
  - `GET /api/ingredient-lots/{lot_id}`
  - `GET /api/ingredients/{ingredient_id}/lots`
  - `PUT /api/ingredient-lots/{lot_id}`
  - `POST /api/ingredient-lots/{lot_id}/deactivate`
- Smoke should use a temporary database/user data directory and verify migration/table scope, ingredient creation, lot creation/read/list, missing density acceptance, invalid density/cost/date rejection, absence of forbidden future tables, and absence of `remaining_quantity`/stock movement behavior.


## PR10 notes
- Stock movement endpoints:
  - `POST /api/stock-movements`
  - `GET /api/stock-movements`
  - `GET /api/stock-movements/{movement_id}`
  - `GET /api/ingredient-lots/{lot_id}/movements`
  - `GET /api/ingredient-lots/{lot_id}/balance`
- Movement quantities are stored as positive Decimal strings; signed deltas are derived from `direction`.
- Movement type controls direction: receipts/manual in are `in`; manual out/write-off/return to supplier are `out`.
- Outgoing movements are rejected when they would make the derived lot balance negative.
- Full FastAPI TestClient-based checks were blocked in the Codex environment because backend test dependencies were not installed, and dependency installation was blocked by registry/proxy 403. The project uses the normal `httpx>=0.27,<1.0` test dependency; no alternate package is required.


## PR11 notes
- Packaging item endpoints:
  - `POST /api/packaging-items`
  - `GET /api/packaging-items`
  - `GET /api/packaging-items/{packaging_item_id}`
  - `PUT /api/packaging-items/{packaging_item_id}`
  - `POST /api/packaging-items/{packaging_item_id}/deactivate`
- Packaging units are pieces-only (`pcs`). Percent, grams, milliliters, and arbitrary units are rejected for the item stock unit.
- Capacity is optional; when present it must be a positive Decimal string/integer/Decimal with unit `ml` or `g`. Missing capacity is accepted and does not imply ml equals grams.
- Unit cost is optional, Decimal-backed, and non-negative. Floats are rejected for capacity and cost.
- PR11 intentionally excludes packaging stock movement tables, derived balances, lots, purchase planning, production write-off, and frontend UI.


## PR12 notes
- Transaction helper: `backend/app/db/transactions.py`.
- Audited service writes now use one SQLite transaction for main write plus audit event.
- If audit logging fails, ingredient, lot, stock movement, packaging item, and audited onboarding state writes roll back.
- Stock movement rows remain immutable; derived lot balance is still calculated from movement rows and is unchanged after rollback.
- PR12 intentionally adds no migrations, no new tables, no API routes, no frontend changes, no launcher changes, and no schema changes.


## PR13 notes
- Packaging stock movement endpoints:
  - `POST /api/packaging-stock-movements`
  - `GET /api/packaging-stock-movements`
  - `GET /api/packaging-stock-movements/{movement_id}`
  - `GET /api/packaging-items/{packaging_item_id}/stock-movements`
  - `GET /api/packaging-items/{packaging_item_id}/balance`
- Packaging movement quantities are stored as positive integer Decimal strings in pieces (`pcs`) only.
- Movement type controls direction: receipts/manual in are incoming; manual out/write-off/return to supplier are outgoing.
- Outgoing packaging movements are rejected when they would make the movement-derived packaging item balance negative.
- Movement creation and audit logging are transactional; simulated audit failure rolls back the movement and leaves derived balance unchanged.
- PR13 intentionally excludes packaging lots, purchase lists, production write-off/readiness, reservations, frontend UI, recipes, clients, orders, imports, exports, cloud, mobile, OCR, auth, and roles.
- PR13 follow-up: `packaging_item_id` validation is now packaging-specific and no longer reuses ingredient lot validators/messages.

## PR14 notes
- Inventory read endpoints:
  - `GET /api/inventory/overview`
  - `GET /api/inventory/ingredient-lot-balances`
  - `GET /api/inventory/packaging-balances`
- Ingredient lot balances are derived from `stock_movements` and include simple expiration flags with a 30-day default expiring-soon window.
- Packaging balances are derived from `packaging_stock_movements` and remain pieces-only.
- Inventory overview reports counts only; it does not sum incompatible units or create alerts/purchase suggestions.
- PR14 intentionally adds no migrations, tables, stored `current_quantity`/`remaining_quantity`, frontend UI, alerts engine, purchase list, recipes, clients, orders, production, import/export, cloud, mobile, OCR, auth, or roles.


## PR15 notes
- Inventory UI route: `/inventory` (navigation label `Склад`).
- Frontend reads only existing PR14 endpoints: `/api/inventory/overview`, `/api/inventory/ingredient-lot-balances`, and `/api/inventory/packaging-balances`.
- UI shows overview cards, ingredient lot balance table, packaging balance table, and loading/empty/error states.
- PR15 intentionally excludes write actions/forms, backend changes, migrations, new tables, alerts engine, purchase suggestions, production, recipes, clients, orders, imports/exports, cloud, mobile, OCR, auth, and roles.


## PR16 notes
- Ingredient UI route: `/ingredients` (navigation label `Компоненты`).
- Frontend ingredient API usage: `GET /api/ingredients`, `POST /api/ingredients`, `PUT /api/ingredients/{ingredient_id}`, `POST /api/ingredients/{ingredient_id}/deactivate`.
- The backend remains unchanged; no migrations or new tables were added.
- Deactivation is soft: the UI calls the existing deactivate endpoint after a confirmation and refreshes the active ingredient list.
- PR16 intentionally excludes ingredient lots UI, stock movement UI, packaging write UI, recipes, clients, orders, production, purchase list, alerts, imports/exports, cloud, mobile, OCR, auth, and roles.

- PR16 follow-up aligned frontend ingredient category options with backend IngredientCategory codes and labels, and clears stale ingredient form errors after successful saves/deactivation.

- PR16 follow-up aligned frontend ingredient unit options with backend UnitCode values, including percent (`%`).


## PR17 notes
- Recipe endpoints: `POST/GET /api/recipe-templates`, `GET /api/recipe-templates/{template_id}`, `POST /api/recipe-templates/{template_id}/deactivate`, `POST/GET /api/recipe-templates/{template_id}/versions`, `GET /api/recipe-versions/{version_id}`.
- Recipe data model is `RecipeTemplate -> RecipeVersion -> RecipeIngredient`; version numbers are generated per template.
- Recipe version creation with ingredient lines is transactional and audited.
- PR17 intentionally excludes recipe calculations, percent-sum validation, recipe UI, client recipes, clients, orders, production, stock reservation/write-off, imports, cloud, mobile, OCR, auth, and roles.

## PR18 notes
- Calculation endpoint: `GET /api/recipe-versions/{version_id}/calculation`.
- Optional query parameters: `target_batch_size_value` and `target_batch_size_unit` (`g` or `ml`); explicit `pcs` query targets are rejected for PR18 calculation.
- Fixed recipe ingredient lines in `g`, `ml`, and `pcs` remain fixed and are not proportionally scaled in PR18; a stored `pcs` target on a fixed-only recipe is reported as a non-blocking limitation rather than failing the read.
- Percent lines require a target batch size in `g` or `ml` and calculate into the target unit without assuming `1 ml = 1 g`; a stored `pcs` target returns an `unsupported_target_batch_unit` issue.
- `percent_total` is reported; totals below 100% produce a warning issue, totals above 100% produce an error issue, and missing target size for percent lines makes `can_calculate=false`.
- Calculation is read-only: it does not write audit logs, mutate recipe rows, reserve/consume stock, select lots, calculate costs/tax/margin, or create production/client/order/import/export records.
- No migrations or new tables were added for PR18.

## PR19 notes
- Recipe UI route: `/recipes` (navigation label `Рецепты`).
- Frontend recipe API usage:
  - `GET/POST /api/recipe-templates`
  - `GET /api/recipe-templates/{template_id}`
  - `GET/POST /api/recipe-templates/{template_id}/versions`
  - `GET /api/recipe-versions/{version_id}`
  - `GET /api/recipe-versions/{version_id}/calculation`
  - `GET /api/ingredients` for the ingredient dropdown in version lines.
- The calculation panel displays backend-provided lines, percent total, totals by unit, and issues; frontend does not derive recipe amounts.
- Existing versions are view-only. The UI supports creating new templates and new versions only.
- PR19 intentionally excludes historical version editing/deletion, client recipes, clients, orders, production, stock readiness, cost/tax/margin, alerts, purchase suggestions, import/export, migrations, and new tables.

## PR20 notes
- Ingredient lot UI route: `/ingredient-lots` (navigation label `Партии`).
- Frontend ingredient lot API usage:
  - `GET /api/ingredient-lots`
  - `POST /api/ingredient-lots`
  - `PUT /api/ingredient-lots/{lot_id}`
  - `POST /api/ingredient-lots/{lot_id}/deactivate`
  - `GET /api/ingredients` for active component dropdown options.
- The UI intentionally edits only lot metadata and explains that quantity is added through separate stock movements.
- No stock movement UI, manual lot balance fields, frontend balance derivation, backend migrations, new tables, production, purchase list, alerts, client/order UI, cloud, mobile, OCR, auth, or roles were added.

## PR21 notes
- Stock movement UI route: `/stock-movements` (navigation label `Движения склада`).
- Frontend ingredient stock movement API usage:
  - `GET /api/ingredient-lots` and `GET /api/ingredients` for lot selection labels;
  - `GET /api/ingredient-lots/{lot_id}/balance` for backend-derived read-only current balance;
  - `GET /api/ingredient-lots/{lot_id}/movements` for selected lot movement history;
  - `POST /api/stock-movements` for creating an append-only movement.
- Movement types shown in Russian: receipt, manual adjustment in/out, write-off, and return to supplier.
- The UI intentionally has no movement edit/delete actions, no editable current balance/remaining quantity field, no frontend-derived balance calculation, no packaging movement UI, no production, no purchase list, no alerts, no backend changes, no migrations, and no new tables.

## PR22 notes
- Client endpoints:
  - `POST /api/clients`
  - `GET /api/clients` with optional `include_inactive`
  - `GET /api/clients/{client_id}`
  - `PUT /api/clients/{client_id}`
  - `POST /api/clients/{client_id}/deactivate`
- Client records are backend-only for PR22 and store normalized full name/contact/address/birthday/notes plus `is_active` timestamps.
- Client writes and audit events are transactional; simulated audit failures roll back create, update, and deactivate operations.
- PR22 intentionally excludes client UI, client recipes, client wishes/feedback, orders, production, imports/exports, backup changes, cloud, mobile, OCR, auth, and roles.
- Future PR23 can build client-specific recipe foundations on top of the `Client` model without adding client data to recipe notes.

## PR23 notes
- PR23 adds backend client recipe foundation with `client_recipes` and `client_recipe_ingredients` tables.
- Client recipes are first-class entities linked to clients and source recipe versions, not notes on clients and not live views over base recipes.
- Creating a client recipe from a source recipe version snapshots source ingredient lines into `client_recipe_ingredients` rows.
- Client recipe detail reads persisted snapshot rows, not live `recipe_ingredients`, so later source recipe/version changes do not silently mutate existing client formulas.
- `client_recipe.created` and `client_recipe.deactivated` audit events are written transactionally with the business writes.
- PR23 intentionally adds no frontend UI, orders, production behavior, stock reservation/write-off, imports/exports, cloud, mobile, OCR, auth, or roles.

## PR24 — Catalog categories and tags backend foundation
- Added backend-only user-managed catalog categories and tags scoped to ingredients/components, packaging/tare, and recipe templates.
- Existing system classifications remain intact: `IngredientCategory`, `PackagingKind`, and `recipe_templates.product_type` are not removed, replaced, or reinterpreted.
- Catalog categories/tags are additional organization metadata with nullable category assignment and separate scoped tag bindings.
- Writes are service-layer transactional with audit actions for create/update/archive and assignment updates.
- Full frontend catalog UI remains a follow-up; no technical admin panel was added.
- No production, orders, import/export, cloud, mobile, OCR, auth, or roles were added.

## PR24 follow-up notes
- Catalog category/tag `scope` must remain immutable after creation to avoid corrupting existing scoped assignments.
- Missing catalog records and missing ingredient/packaging/recipe assignment targets are handled as controlled API 404 responses.
- No schema changes, migrations, frontend UI, DTO enrichment, production/orders/import/export/cloud/mobile/OCR/auth/roles were added in the follow-up.

## PR25 notes
- «Компоненты» now consumes only ingredient catalog endpoints: `GET /api/catalog/categories?scope=ingredient`, `GET /api/catalog/tags?scope=ingredient`, `PUT /api/ingredients/{ingredient_id}/catalog-category`, and `PUT /api/ingredients/{ingredient_id}/catalog-tags`.
- Ingredient list responses include current `catalog_category_id` and `catalog_tag_ids` for UI state. This is read support only; PR24 schema is unchanged and no migrations were added.
- UI wording keeps the system enum separate as «Системный тип» and presents catalog metadata as «Моя группа» and «Метки». Packaging and recipe catalog UI remain follow-ups.

## PR26 handoff notes
- PR26 adds inline creation of ingredient catalog groups/tags in the existing `Компоненты` UI.
- Frontend calls `POST /api/catalog/categories` and `POST /api/catalog/tags` with ingredient scope internally, then reloads ingredient categories/tags for immediate assignment.
- Scope, slug, color, hierarchy, sorting, and technical catalog administration are not exposed in the UI.
- Catalog categories/tags remain ingredient-scoped organization metadata; the system `IngredientCategory` remains intact.
- Packaging and recipe catalog UI are still future follow-ups.
- No migrations, new tables, production, orders, import/export, cloud, mobile, OCR, auth, or roles were added.
