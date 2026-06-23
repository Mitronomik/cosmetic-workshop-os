# Progress

## Current phase
PR16 - Ingredient catalog UI foundation

## Done
- Architecture draft
- Final roadmap draft
- Frontend concept draft
- Codex project structure rules
- Codex prompting rules
- PR testing and smoke rules
- Product specification
- Domain model
- Repository starter structure and documentation placement
- Documentation structure review against project contracts
- Nested `AGENTS.md` contracts expanded for backend, frontend, launcher, docs, ADRs, state, help and scripts
- Minimal backend app shell with `/api/health` and `/health`
- Backend health endpoint tests
- Minimal frontend shell with Russian navigation placeholders and dashboard placeholder
- Minimal project commands for PR1 test/build/dev guidance
- PR1 follow-up: frontend `typescript` devDependency declared and `npm run dev` now builds before serving `dist`
- PR1 follow-up: temporary backend ASGI fallback removed; FastAPI is now the only backend runtime path
- PR1b branding pass: compact sidebar brand area, existing monogram/logo usage, warm cream/deep brown/rose-gold styling, favicon wiring, responsive shell refinements
- PR2 SQLite persistence foundation with test-friendly database configuration
- PR2 stable repository-root default development database path with `COSMETIC_WORKSHOP_DB_PATH` override
- PR2 migration helper and initial infrastructure migration for `app_settings` and `audit_logs` only
- PR2 technical API endpoints for database status and app settings with no hidden migration side effects
- PR2 tests for temporary database initialization, idempotent migrations, stable path behavior, explicit initialization, infrastructure table presence, endpoint behavior, and no business table creation
- PR3 user data directory resolver for `~/Documents/Мастерская косметолога/` with `data`, `backups`, `exports`, `attachments`, and `logs` paths
- PR3 optional `COSMETIC_WORKSHOP_USER_DATA_DIR` override for user-mode data directory resolution
- PR3 explicit startup initialization service that creates user data directories and applies migrations only when called
- PR4 backend backup service for copying existing SQLite databases into user-data `backups/` without modifying or overwriting the source
- PR4 user-mode startup backup-before-migration guard for existing databases with pending migrations
- PR5 backend-only Decimal parsing and quantization helpers for grams, milliliters, percentages, money, counts, and density
- PR5 MVP unit primitives for grams, milliliters, percent, and pieces with canonical codes and Russian labels
- PR5 lightweight measurement value objects for weight, volume, percentage, money, quantity/count, and density
- PR5 density conversion foundation that converts ml to grams only with an explicit density and returns a missing-density warning otherwise
- PR6 `ingredients` migration with no stock, lot, recipe, client, order, production, import, packaging, or purchase tables
- PR6 backend ingredient domain category/unit/name/density validation using existing Decimal/Density primitives with missing density allowed
- PR6 repository/service/API foundation for create, read, list active, full PUT update, and deactivate ingredients, plus minimal ingredient audit events
- PR7 local runtime launcher MVP with localhost-only config, explicit user-mode startup initialization, backend process launch helper, optional browser opening, launcher tests, and docs
- PR8 backend onboarding state stored as typed JSON in `app_settings` without adding a new table
- PR8 thin onboarding API for read/start/complete-step/complete/skip/reset with minimal audit events for started, step completed, and completed
- PR8 frontend first-run welcome/checklist skeleton in Russian with graceful backend-unavailable fallback and small empty-state text for Recipes, Clients, and Stock
- PR8 follow-up separates true completion from skip/close behavior so skipped onboarding does not falsely mark all checklist steps complete
- PR9 `ingredient_lots` migration with ingredient relationship, cost/shelf-life/supplier/density metadata, and no stock movement or remaining balance fields
- PR9 backend ingredient lot domain validation using existing UnitCode, Decimal money quantization, and Density primitives with missing density/costs allowed
- PR9 repository/service/API foundation for create, read, list active, list by ingredient, full PUT update, and deactivate ingredient lots, plus minimal lot audit events
- PR10 `stock_movements` migration for immutable ingredient-lot movements with no stored lot balance or `remaining_quantity` columns
- PR10 backend stock movement domain validation for Decimal quantities, allowed stock units, direction/type consistency, no floats, no percent units, and whole-number pieces
- PR10 repository/service/API foundation for create, read, list, list by lot, derived lot balance, negative-balance prevention, and minimal `stock_movement.created` audit events
- PR10 hotfix: test-only allowed/forbidden table guards now treat `stock_movements` as current and keep future business tables forbidden

- PR11 `packaging_items` migration for cosmetic workshop packaging/tare definitions with no packaging stock movements, packaging balances, lots, or stored quantity columns
- PR11 backend packaging item domain validation for stable MVP kind codes, pieces-only unit, optional positive Decimal capacity in ml/g, optional non-negative Decimal unit cost, no floats, and normalized names/text fields
- PR11 repository/service/API foundation for create, read, list active, full PUT update, and deactivate packaging items, plus minimal packaging audit events
- PR11 table guard update treats `packaging_items` as current while recipe/client/order/production/import/backup future tables remain forbidden
- PR11 hotfix: `test_stock_movements.py` now uses the centralized test-only table guard helpers instead of stale local allowed/forbidden table sets.

- PR12 transactional write service foundation adds a small SQLite transaction helper and moves ingredient, ingredient lot, stock movement, packaging item, and audited onboarding state writes into service-level transactions so business writes and audit logs commit or roll back together.
- PR12 repository write methods can accept a shared SQLite connection while preserving standalone repository behavior for callers that do not pass one.
- PR12 rollback tests cover audit failure for ingredient, ingredient lot, stock movement, packaging item, and onboarding writes; stock movement rollback leaves derived lot balance unchanged.

- PR13 `packaging_stock_movements` migration for immutable packaging/tare stock movements with no stored packaging balance, no `current_quantity`/`remaining_quantity`, and no packaging lots.
- PR13 backend packaging stock movement domain validation for positive integer pieces only, stable MVP movement types, no floats, no fractional pieces, no percent/ml/g/arbitrary movement units, and active packaging item requirements.
- PR13 repository/service/API foundation for create, read, list, list-by-packaging-item, and movement-derived packaging item balance, plus negative-balance prevention.
- PR13 transactional `packaging_stock_movement.created` audit event so audit failure rolls back movement creation and leaves derived balance unchanged.
- PR13 follow-up replaced the packaging stock movement `packaging_item_id` validator with packaging-specific validation messages so invalid tare selection no longer references ingredients/components.

## In progress
- PR16 ingredient/component directory UI foundation validation and PR update

## Blocked
- Full FastAPI TestClient-based checks were blocked in the Codex environment because backend test dependencies were not installed, and dependency installation was blocked by registry/proxy 403. The project uses the normal `httpx>=0.27,<1.0` test dependency; no alternate package is required.

## Next
- Continue with the next roadmap-scoped task after PR16 review/merge. Packaging inventory, recipes, clients, orders, production, FEFO allocation, automatic write-off, imports, exports, backup UI/restore, final packaging, Electron, Docker, cloud, mobile, OCR, auth and roles remain out of scope until explicitly requested.

## Important notes
- PR13 intentionally does not add packaging lots, purchase suggestions, production, recipes, clients, orders, import/export, frontend UI, launcher changes, or cloud/mobile/auth behavior.
- PR12 intentionally does not add migrations, tables, API routes, frontend changes, packaging stock movements, recipes, clients, orders, production, import/export, or cloud/mobile/auth behavior.
- PR11 intentionally does not add packaging stock movements, packaging lots, packaging balances, `remaining_quantity`, `current_quantity`, purchase suggestions, production consumption, or frontend packaging UI.
- PR10 intentionally does not add `remaining_quantity`, materialized balance tables, production write-off logic, FEFO allocation, packaging movements, or frontend inventory UI.
- Stock movement balances are derived by summing immutable movement rows for a lot; corrections should be represented by new movements rather than editing/deleting existing rows.
- PR9 intentionally does not add `remaining_quantity`, stock movement tables, production write-off logic, FEFO allocation, or frontend inventory UI.
- Ingredient lot `unit` is restricted to grams, milliliters, or pieces; percent is rejected as a lot stock unit.
- Lot creation/update rejects missing and inactive ingredients; inactive lots are hidden from active list endpoints.
- Missing lot density is accepted and no density fallback is assumed.
- Costs and density are Decimal-backed and stored as strings in SQLite.
- Tests and smoke use temporary directories/databases and should not write real user data.

- PR14 backend inventory read models: added read-only ingredient lot balance, packaging balance, and inventory overview DTO/service/repository/API layers. Balances are derived from immutable stock movement history; no stored balance fields, migrations, tables, frontend UI, alerts, purchase list, production, recipes, clients, or orders were added.
- PR15 inventory overview UI foundation: added a read-only `/inventory`/`Склад` frontend screen that consumes existing PR14 inventory read endpoints for overview cards, ingredient lot balances, and packaging balances. It includes loading, empty, and error states and intentionally adds no write forms, backend migrations, alerts, purchase list, production, recipes, clients, or orders.

- PR16 ingredient/component directory UI foundation: added a `/ingredients`/`Компоненты` frontend screen that consumes existing ingredient endpoints for active-list, create, full update, and soft deactivation. It includes loading, empty, and error states and intentionally adds no lots, stock movements, packaging write flows, recipes, clients, orders, production, purchase list, alerts, migrations, or new tables.

- PR16 follow-up aligned frontend ingredient category options with backend IngredientCategory codes and labels, and clears stale ingredient form errors after successful saves/deactivation.

- PR16 follow-up aligned frontend ingredient unit options with backend UnitCode values, including percent (`%`).


- PR17 backend recipe model foundation: added `RecipeTemplate -> RecipeVersion -> RecipeIngredient` tables, domain validation, service/repository/API endpoints, and transactional audit events for create/deactivate operations. No calculation service, percent-sum validation, recipe UI, clients, orders, or production were added.

- PR18 backend recipe version calculation service: added a read-only calculation service and API endpoint for recipe versions. Fixed `g`/`ml`/`pcs` recipe lines are returned unchanged, percent lines calculate from an explicit or stored `g`/`ml` target batch size, percent totals are reported with warning/error issues, and calculation reads do not create audit logs or mutate recipe rows. No migrations, new tables, cost calculation, stock readiness, production, client recipes, orders, import/export, or frontend UI were added.

## PR19 — Recipe UI foundation
- Added `Рецепты` navigation and `/recipes` route in the branded frontend shell.
- Added frontend recipe API usage for listing/creating recipe templates, opening templates, listing/creating versions, opening version details, and requesting backend calculation results.
- Added recipe workspace UI with empty/loading/error states, template creation, version creation with ingredient lines populated from active ingredients, version detail, and Russian calculation panels for backend lines/issues/totals.
- Preserved historical-version safety: existing recipe versions are not edited, deleted, or mutated from the UI.
- No backend migrations, tables, client recipes, orders, production, cost calculation, stock readiness, import/export, cloud, mobile, OCR, auth, or roles were added.

## PR20 — Ingredient lots UI foundation
- Added `Партии` navigation and `/ingredient-lots` route in the frontend shell.
- Added frontend API usage for `GET/POST/PUT /api/ingredient-lots` and `POST /api/ingredient-lots/{lot_id}/deactivate`, plus existing `GET /api/ingredients` for active component selection.
- Added ingredient lot loading, empty, error, create, edit, and soft-deactivate UI states with Russian user-facing labels and expiration status labels.
- Preserved stock boundary: no quantity/current balance input, no stock movement form, no frontend balance calculation, no migrations, and no backend changes.

## PR21 — Ingredient stock movement UI foundation
- Added `Движения склада` navigation and `/stock-movements` route in the frontend shell.
- Added frontend API usage for existing ingredient stock movement endpoints: `POST /api/stock-movements`, `GET /api/ingredient-lots/{lot_id}/movements`, and `GET /api/ingredient-lots/{lot_id}/balance`, plus existing ingredient/lot lists for human-readable lot selection.
- Added lot selection, backend-derived read-only current balance, create movement form, movement history table, and loading/empty/error states.
- Preserved append-only stock accounting: no edit/delete movement UI, no manual current balance field, no frontend balance derivation, no backend changes, no migrations, and no new tables.
- PR21 intentionally excludes packaging stock movement UI, production, purchase list, alerts, recipe/client/order changes, import/export, cloud, mobile, OCR, auth, and roles.

## PR22 — Clients backend foundation
- Added `clients` migration with contact, address, birthday, note, active-status, and timestamp fields.
- Added client validation for required normalized full name, normalized optional strings, email shape, optional non-future birthday, and soft deactivation.
- Added backend client create/read/list/full-update/deactivate service and `/api/clients` endpoints with transactional `client.created`, `client.updated`, and `client.deactivated` audit logging.
- Updated test-only table guards so `clients` is current while future client recipe, wishes/feedback, order, production, import, and backup tables remain forbidden.
- Added backend tests for table scope, client behavior, validation, transactional rollback on audit failure, and API endpoint coverage when the local TestClient dependency set is available.
- No frontend application code or client UI was added.

## PR23 — Client recipes backend foundation
- Added `client_recipes` and `client_recipe_ingredients` as backend persistence for first-class individual client formulas.
- Client recipes link to an active client and an existing source recipe version; source recipe ingredient lines are snapshotted into independent client recipe ingredient rows at creation time.
- Client recipe details read snapshot rows from `client_recipe_ingredients`, not live source `recipe_ingredients`, preserving historical individual formulas when base recipes change later.
- Added backend create/read/list/list-by-client/deactivate behavior with transactional `client_recipe.created` and `client_recipe.deactivated` audit events.
- No client recipe UI, orders, production, stock reservation/write-off, imports/exports, cloud, mobile, OCR, auth, or roles were added.

## PR24 — Catalog categories and tags backend foundation
- Added backend-only user-managed catalog categories and tags scoped to ingredients/components, packaging/tare, and recipe templates.
- Existing system classifications remain intact: `IngredientCategory`, `PackagingKind`, and `recipe_templates.product_type` are not removed, replaced, or reinterpreted.
- Catalog categories/tags are additional organization metadata with nullable category assignment and separate scoped tag bindings.
- Writes are service-layer transactional with audit actions for create/update/archive and assignment updates.
- Full frontend catalog UI remains a follow-up; no technical admin panel was added.
- No production, orders, import/export, cloud, mobile, OCR, auth, or roles were added.

## PR24 follow-up — Catalog scope immutability and controlled errors
- Catalog category and tag scopes are now immutable after creation; updates may change names/slugs/sort/color/parent metadata only within the original scope.
- Catalog assignment routes now convert missing catalog records and missing assignment targets into controlled HTTP 404 responses instead of uncaught errors.
- Added regression tests for immutable scopes, assigned record scope-change prevention, and controlled missing-record assignment errors.

## PR25 — Ingredient catalog category selector and tag chips UI
- Added UI support on «Компоненты» for loading ingredient-scoped catalog categories and tags, showing «Системный тип», «Моя группа», and «Метки» in the component list, and assigning a selected component's category/tags through the existing ingredient assignment endpoints.
- Added minimal ingredient response enrichment for `catalog_category_id` and ingredient tag ids so the frontend can show current assignment state without adding migrations or new tables.
- Catalog categories/tags remain user organization metadata; `IngredientCategory` remains the system classification. Packaging/recipe catalog UI, catalog admin screens, deletion, migrations, production, orders, import/export, cloud, mobile, OCR, auth, and roles were not added.

## PR26 — Ingredient catalog inline create UI
- Added simple Russian inline controls on the `Компоненты` screen to create ingredient catalog groups and tags via the existing PR24 catalog endpoints.
- New categories/tags are created automatically as ingredient-scoped organization metadata and reload into the UI after creation.
- The system `IngredientCategory` semantics remain intact; grouping metadata is not used as business logic for stock, recipes, or production.
- Packaging and recipe catalog UI remain follow-ups.
- No migrations, new tables, production, orders, import/export, cloud, mobile, OCR, auth, or roles were added.

## 2026-06-23 — PR1 UX stabilization: recipe builder ingredient selection
- Fixed stale active component options in the recipe version constructor: active components created in «Компоненты» are refreshed for recipe lines without restarting the app.
- The recipe constructor now explains the empty active-component state and offers an explicit component-list refresh; unsaved version form input is preserved while component options refresh.
- Builder-first recipe creation remains a later UX stabilization PR. Catalog/menu/groups/tags redesign remains out of scope.

## 2026-06-23 — PR2 UX stabilization: grouped sidebar navigation
- Regrouped the left sidebar into user-facing sections: «Главная», «Создание», «Склад», «Производство», «Данные», and «Настройки и помощь».
- Existing implemented routes and screens remain intact, including `/inventory`, `/ingredients`, `/ingredient-lots`, `/stock-movements`, `/recipes`, `/clients`, `/client-recipes`, and `/packaging-items`.
- No backend, domain logic, API, migration, or data model changes were made.
- Recipe catalog, groups/tags UX, builder-first recipe creation, and inventory flow cleanup remain later UX stabilization PRs.
