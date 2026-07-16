# Progress

## Current phase

After PR101.

Runtime product implementation is complete through PR98 — Workshop profile integration with report documents. PR99-PR101 were documentation and governance changes only.

The project is preparing the required manual browser smoke before the next focused implementation slice.

## Current next step

- Run the manual browser smoke for Workshop profile and report document integration.
- Save several Workshop profile fields in `/settings`, leaving at least one field empty.
- Generate and open/download new Markdown and PDF `Сводка мастерской` documents from `/report-documents`.
- Confirm only non-empty profile fields appear and render as plain document text.
- Clear the profile and generate another document.
- Confirm the profile section is omitted without errors and previously generated documents remain unchanged.
- If smoke is clean, prepare a focused Workshop profile display polish / app header integration PR.
- If smoke reveals an issue, prepare a narrowly scoped report document integration fix first.
- Do not assign or reuse a historical PR number before the new PR is created.
- Keep DOCX, arbitrary file browsing, unrelated file access, automatic report generation, scheduled jobs, polling, cloud sync, AI/RAG, template editing, logo upload, document preview, calculation-sensitive settings, roles/auth, motion work, migrations, and unrelated business mutations out of scope.

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
- PR73 manual backup API foundation with `GET /api/backups/status`, `GET /api/backups`, and `POST /api/backups`; status/list are read-only, create copies only the configured SQLite database, no restore/UI/migrations/business mutations were added.
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
- PR58 client wishes and feedback UI plus follow-up fixes preserving client-card drafts are complete.


- PR99 documentation/governance: project UI/UX contract, project-owned Codex UI guidance, repository UI boundaries, and canonical `Склад` navigation wording.
- PR100 documentation/governance: reviewed Impeccable provenance plus safe project-owned non-executable UI guidance; upstream skill not activated.
- PR101 documentation/governance: Taste Skill review recorded as not approved; no upstream content, scripts, dependencies, hooks, or active skill installed.

## In progress

- Manual browser smoke for Workshop profile and report document integration has not yet been recorded as completed.
- No new runtime implementation PR should start until that smoke result determines whether the next slice is polish or an integration fix.

## Blocked
- Full FastAPI TestClient-based checks were blocked in the Codex environment because backend test dependencies were not installed, and dependency installation was blocked by registry/proxy 403. The project uses the normal `httpx>=0.27,<1.0` test dependency; no alternate package is required.

## Next

- First: complete and record the Workshop profile/report document manual browser smoke.
- On a clean result: Workshop profile display polish / app header integration.
- On a failed result: narrowly scoped report document integration follow-up fixes before polish.
- Do not assign the next PR number until the PR is actually created.
- Keep DOCX, arbitrary file browsing, unrelated file access, automatic report generation, scheduled jobs, polling, cloud sync, AI/RAG, template editing, logo upload, document preview, calculation-sensitive settings, roles/auth, motion work, migration changes, and unrelated business behavior out of scope unless explicitly approved.

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

## 2026-06-23 — PR2 update: honest navigation status UX
- Refined PR2 sidebar groups to «Главная», «Рецепты», «Клиенты», «Склад», «Производство», and «Данные и настройки»; removed broad «Создание» grouping.
- Added frontend-only collapsible navigation groups; the active group stays expanded so the current screen remains visible during route and Back/Forward navigation.
- Added explicit module statuses in navigation: ready/empty/planned, with planned modules marked by a visible «скоро» badge and distinct planned-module placeholder pages.
- Added a compact home-page readiness note listing what works now and what is coming soon.
- No backend, domain logic, API, migration, or data model changes were made.

## 2026-06-24 — Frontend stabilization PR3 / GitHub PR #46: shared searchable catalog controls
- Introduced shared frontend helpers for searchable catalog group and tag controls with inline creation support, selected-tag chips, and limited default tag lists to avoid an unlimited chip wall.
- First applied scope: «Компоненты» catalog assignment; the same shared pattern was also safely applied to «Тара» because existing packaging catalog endpoints and UI were already present.
- No backend, domain model, API contract, migration, recipe catalog redesign, or builder-first recipe creation changes were made.
- PR #46 fix before merge: tag assignment now derives the payload from the item's current assigned tag ids plus the explicit toggled tag, so selected tags hidden by search are preserved; catalog search re-renders restore focus/caret for ingredient and packaging controls.

## Frontend stabilization PR4 / GitHub PR #47: component catalog browser and filters
- Components page now has browse-first catalog-level search and filters near the top of `/ingredients`.
- Filtering works over the loaded local frontend state for the local-first MVP; no backend search, pagination, domain, or migration changes were introduced.
- Lightweight generic catalog filter helpers were introduced for future reuse by Packaging, Recipes, Clients, and Client Recipes.
- Group/tag assignment from PR46 remains unchanged and still appears when editing a selected component.
- Packaging, recipes, clients, and client recipes catalog/list UX remain later PRs.
- PR #47 pre-merge fix: `/ingredients` now renders filters first, then the create/edit form and PR46 group/tag assignment area, then compact filtered results so create/edit actions appear near the top even with large catalogs.
- PR #47 final cleanup: default browse mode now renders filters directly followed by compact results, create/edit appears near the top only when active, cancel edit returns to browse mode without opening a blank create form, and search/group/system/status filters have individual clear actions; no backend/domain/API/migration changes.
- PR #47 manual-smoke fix: all `Создать компонент` buttons now use the same create action, opening the form scrolls/focuses the name field, create mode has a separate `Вернуться к каталогу` collapse action, and component results are labeled as `Найденные компоненты`; no backend/domain/API/migration changes.
- PR #47 assignment-picker fix: the shared group assignment picker now uses one searchable list of clickable options with highlighted current selection and `Без группы`; the fake search-plus-select pattern was removed for Ingredients and Packaging assignment panels without backend/domain/API/migration changes.

## PR48 — Staged catalog assignment apply
- Frontend stabilization PR5 / GitHub PR #48: staged apply for catalog assignment.
- Components and Packaging group/tag assignment now uses an explicit local draft and `Применить изменения`; accidental group clicks or tag toggles no longer save immediately.
- Hidden selected tags remain preserved because tag changes update the full draft tag id set, not the visible checkbox DOM.
- Applied only to frontend Components and Packaging assignment UX; no backend/domain/API/migration changes.

## Frontend stabilization PR6 / GitHub PR #49: packaging catalog browser and filters
- Packaging page now has catalog-level search and filters for group, tags, packaging type, and status.
- Packaging filtering works over the loaded local frontend state for the MVP; no backend search, pagination, API, domain, or migration changes were added.
- PR48 staged assignment remains unchanged: group/tag edits stay as a draft until `Применить изменения`, with reset/discard behavior preserved.
- Recipes, clients, and client recipes catalog/list UX remain later PRs.

## Frontend stabilization PR7 / PR50 replacement: recipes browse-first workspace
- Recipes now follow the browse-first workspace pattern used by Components and Packaging: the catalog search/filter area and compact list appear before create/edit/detail workspaces.
- Search/filtering works over loaded frontend recipe state for MVP: name, product type, description, notes, catalog group/tag text, and truthful active/inactive status already returned by the API.
- Create/edit/detail workspaces no longer dominate the first screen; create and opened recipe detail are explicit modes with clear return/close actions.
- No backend/API/domain/migration changes were made.
- Clients and Client Recipes remain separate later PRs.

## Frontend stabilization PR8: clients browse-first workspace

- Clients now follow the browse-first workspace pattern: intro, messages, search/status toolbar, optional create/edit workspace, compact list, and a collapsed create helper.
- Client search/filtering works over the loaded frontend client state and keeps the list visible instead of showing a long always-open form first.
- Status filtering uses the existing `includeInactive` API behavior: `Архив` and `Все` switch to inactive-inclusive loading before local filtering.
- Create/edit workspaces are explicit and closable; edit highlights the active row with the existing selected-row style.
- No backend/API/domain/migration changes were made. Client Recipes remain a separate later PR.

## Frontend stabilization PR9: client recipes browse-first workspace

- Client Recipes now follow the browse-first workspace pattern: intro, messages, search/filter toolbar, optional create/detail workspace, compact list, and collapsed create helper.
- Search and filtering work over loaded frontend client recipe state, including title, status, client name, personalization, allergy, preference, contraindication, and note text.
- Status filtering correctly loads inactive client recipes when `Архив` or `Все` is selected through existing `includeInactive` behavior, then filters locally over the loaded set.
- Base recipe/template filtering was intentionally not added because complete source recipe/template data is not loaded for every client recipe in this workspace.
- Create/detail workspaces no longer dominate the first screen; both are explicitly opened and closable without resetting filters.
- No backend/API/domain/migration changes.

## Frontend stabilization PR53 follow-up: client recipe create UX clarity

- Client Recipe create UX was clarified with non-technical Russian copy for client-specific formulas and saved composition versions.
- Create dependencies now refresh automatically through existing frontend API calls when opening the create form from browse/detail mode, without resetting filters or reloading the client recipe list.
- User-facing Client Recipe copy no longer exposes frontend/backend terminology.
- Version selection now explains that a saved recipe version with composition is required before an individual recipe can be created.
- A full editable ClientRecipe composition builder remains a later PR if backend support is not present.

## PR54: ClientRecipe composition update API

- ClientRecipe already created an independent copied composition from saved RecipeVersion lines.
- Added backend/API support to replace the copied ClientRecipe composition through `PUT /api/client-recipes/{client_recipe_id}/ingredients`.
- Composition updates affect only `client_recipe_ingredients` for the target ClientRecipe; source RecipeVersion / RecipeVersionIngredient rows are not mutated.
- Other ClientRecipes copied from the same source version are not mutated.
- Update validation covers line ids, positive ingredient ids, unique positions, positive precise amounts, allowed units, inactive ingredient replacement, and archived ClientRecipe edits.
- The replace operation is transactional and audited with `client_recipe.composition_updated`.
- No frontend composition editor was implemented; that remains a later PR.

## PR54 follow-up: inactive ClientRecipe line safety

- Tightened ClientRecipe composition updates so inactive existing ingredient lines may only remain if their copied line data is unchanged.
- Inactive existing lines may still be omitted from a full-replace payload to remove them.
- Added duplicate existing line id validation for composition update payloads.
- Source RecipeVersion rows, other ClientRecipes, and frontend UI remain unchanged.

## PR55: ClientRecipe composition editor

- Frontend detail card now has an editor for copied ClientRecipe composition.
- Saving uses the PR54 backend API: `PUT /api/client-recipes/{client_recipe_id}/ingredients`.
- The base recipe and saved RecipeVersion are not changed by composition edits.
- Archived/inactive ClientRecipes remain read-only.
- Inactive/unavailable ingredient lines are protected in the editor: leave unchanged or remove.
- This PR does not add production, stock deduction, cost calculation, or backend changes.

## PR56: Restore archived ClientRecipe
- Archived ClientRecipes can now be restored to the active working list through a backend-controlled restore workflow.
- Restore sets the ClientRecipe back to `draft` with `is_active = true` and keeps copied composition rows unchanged.
- Restore is rejected when the linked client is archived/inactive; source RecipeVersion rows and other ClientRecipes are not mutated.
- Restore writes a transactional `client_recipe.restored` audit event and rolls back if audit logging fails.
- This PR does not add global restore behavior for other entities.

## PR57: Client wishes and feedback backend
- Added backend foundations for client wishes and client feedback.
- Wishes can be created, listed, retrieved, status-updated, resolved, and archived.
- Feedback is append-only in this PR: create/list/get only, with no update or delete endpoint.
- Both wishes and feedback can optionally link to a ClientRecipe belonging to the same client, including archived ClientRecipes for historical context.
- Creating wishes or feedback for inactive clients is rejected.
- Source RecipeVersion, ClientRecipe composition, stock, production, and orders are not mutated.
- Frontend UI will be added in a later PR.

## PR57 follow-up: ClientWish status lifecycle
- Fixed ClientWish status transitions so moving from `resolved` back to `open` or `planned` clears `resolved_at`.
- Generic status updates no longer archive wishes or restore archived wishes; archive remains explicit through `POST /client-wishes/{wish_id}/archive`.
- Feedback remains append-only and no ClientRecipe, RecipeVersion, inventory, production, or frontend behavior was changed.

## PR58: Client wishes and feedback UI
- Added frontend-only client-card sections for `Пожелания клиента` and `Обратная связь` using the existing PR57 backend endpoints.
- Wishes can be created, moved only between `open`, `planned`, and `resolved`, and archived through the explicit archive endpoint; archived wishes are hidden by default, visible through `Показать архивные`, read-only, and not restorable in this PR.
- Feedback can be created and viewed as append-only history; no edit/delete UI was added.
- ClientRecipe linking is implemented in both create forms by loading existing client recipes, including archived recipes when available, and sending only the selected `client_recipe_id` without mutating ClientRecipe composition.
- Backend/domain/migrations were not changed. Orders, production, stock, import/export, backup/restore, cloud, auth, and AI recommendations were not added.

## PR58 follow-up: Preserve client card drafts
- Open ClientWish and ClientFeedback form drafts are now synced from the DOM before background client-card refresh renders, preserving typed text, ClientRecipe selector values, dates, ratings, and follow-up checkbox state.
- Wish title frontend maxlength is aligned with backend validation at 180 characters.
- Backend/domain/migrations were not changed. Feedback edit/delete and wish restore were not added.

## PR58 follow-up: Preserve drafts on client card save
- Client card save now syncs open ClientWish/ClientFeedback drafts before edit-card render paths, so saving the main client details does not lose unsaved wish or feedback form input.
- Backend/domain/migrations were not changed. Feedback edit/delete and wish restore were not added.

## PR60 — Orders backend foundation
- Added the backend Orders foundation: SQLite `orders` table, domain validation, typed repository/model, transactional audited service, schemas, and `/api/orders` routes.
- Orders now connect an active client to exactly one recipe source: either a `RecipeVersion` or a same-client active `ClientRecipe`; optional packaging is validated for active state on new writes.
- Order create/update/cancel/archive writes are audited with rollback on audit failure and do not mutate recipes, client recipes, stock movements, packaging movements, or production data.
- No frontend UI, production readiness, production confirmation, automatic stock write-off, alerts, purchase suggestions, import/export, cloud, mobile, OCR, auth, or roles were added.

## PR61 — Orders UI foundation
- Added `Заказы` navigation and `/orders` route in the frontend shell.
- Added a human-friendly Orders workspace with list, search/status filters, empty/loading/error states, create order form, detail view, safe edit flow, cancel action, and archive action.
- Integrated with existing PR60 Orders endpoints: `POST /api/orders`, `GET /api/orders`, `PUT /api/orders/{order_id}`, `POST /api/orders/{order_id}/cancel`, and `POST /api/orders/{order_id}/archive`.
- Create/update payloads are built from safe order fields only and do not send `status`, `produced_at`, or `delivered_at`.
- The UI displays future production statuses read-only but intentionally adds no production readiness, production confirmation, stock write-off, production batches, cost/tax/margin calculation, alerts, purchase suggestions, import/export, cloud, mobile, OCR, auth, or roles.

## PR62 — Production readiness backend foundation
- Added backend-only Production Readiness foundation for orders.
- Added `POST /api/orders/{order_id}/check-production-readiness` returning structured readiness results with blocking issues, warnings, ingredient requirements, FEFO lot selections, packaging availability, and optional cost/tax/margin estimates.
- Readiness checks current ingredient lot and packaging balances through existing inventory read logic and preserves the production boundary: no stock write-off, no packaging write-off, no production batches, and no order lifecycle mutation.
- Added targeted backend tests for enough stock, missing/insufficient ingredients, FEFO selection, expired/soon-expiring lots, missing density, missing packaging, cancelled/archived rejection, API behavior, and read-only guarantees.
- No frontend UI, production confirmation, alerts, purchase suggestions, import/export, cloud, mobile, OCR, auth, or roles were added.

## PR63 — Production readiness UI
- Added read-only Production Readiness UI inside the Orders workspace.
- Added active-order `Проверить изготовление` action that calls existing `POST /api/orders/{order_id}/check-production-readiness` endpoint.
- Displayed readiness summary, blocking issues, warnings, ingredient requirements, backend-selected FEFO lots, packaging availability, and optional estimates.
- Null tax/margin/cost values are shown as `Не рассчитано`; the frontend does not invent tax settings or calculate margin itself.
- Preserved production boundary: no production confirmation, no stock write-off, no packaging write-off, no lot reservation, no production batches, and no order lifecycle mutation.

## PR64 — Production confirmation backend foundation
- Added transactional backend production confirmation through `POST /api/orders/{order_id}/produce`.
- Added `production_batches`, `production_batch_ingredients`, and `production_batch_packaging` tables for historical production snapshots.
- Production confirmation now requires `confirm=true`, reuses backend Production Readiness, rejects lifecycle/readiness conflicts, writes off ingredient lots and packaging through movement records, marks the order `produced`, sets `produced_at`, and writes a safe audit log in the same transaction.
- Tax, margin, and margin percent remain null; no hidden tax rate or frontend production UI was added.

## PR65 — Production confirmation UI
- Added frontend Production Confirmation UI inside the Orders workspace, using the existing backend readiness result as the gate before showing `Изготовить`.
- Added frontend production batch response types and a `produceOrder` helper that only sends `confirm=true` to `POST /api/orders/{order_id}/produce`.
- Added an inline second-confirmation panel with optional notes before any production request is sent.
- Successful production now displays a human-readable production result panel with batch id, produced date, costs when present, tax/margin as `Не рассчитано`, write-off row counts, and the stock movement safety note.
- After successful production, the frontend refreshes order data from the backend and no longer exposes production actions for produced/cancelled/archived/inactive/delivered orders.
- No frontend readiness, stock write-off, lot selection, production batch, tax, or margin calculations were added; no backend logic or migrations were changed.

## PR66 — Production history read UI and production batch detail page
- Added read-only production batch API endpoints for listing batches, opening one batch detail, and finding a batch by order.
- Production batch repository now supports read-only list/detail access with order, product, and client display context without duplicating production confirmation write logic.
- Added backend tests covering list sorting, detail snapshots, by-order lookup, not-found behavior, and read-only guarantees.
- Added a real frontend `Производство` page with production history search, batch list, and read-only detail panel for cost, ingredient lot, and packaging snapshots.
- Produced/delivered orders can open their production batch without showing production confirmation actions again.
- No migrations, production write actions, reversal/edit/delete flows, frontend stock/cost/tax calculations, alerts, purchases, import/export, cloud, OCR, auth, or analytics were added.

## PR67 — Alert engine backend foundation
- Added the backend `alerts` table with `alert_key` deduplication, alert status/severity/type fields, and safe status timestamps.
- Added backend alert generation for low ingredient stock, low packaging stock, expiring/expired ingredient lots, and order-level ingredient/packaging production readiness blockers.
- Added read-only/list, explicit regenerate, resolve, and dismiss Alert API endpoints.
- Added backend tests for idempotency, deduplication, status transitions, MVP alert types, and read-only guarantees.
- No frontend UI, purchase suggestions, notifications, scheduler, or automatic stock/order/production changes were added.

## PR68 — Alerts UI
- Added a frontend `Алерты` workspace at `/alerts` that consumes the PR67 backend alert endpoints.
- Added status/type/search filters, explicit regeneration, resolve, and dismiss actions with Russian human-readable cards and empty/error states.
- Updated dashboard copy to list Alerts as available.
- No backend behavior, migrations, alert rules, purchase suggestions, notifications, scheduler, polling, or dashboard analytics were added.
- Next recommended PR: purchase suggestions backend foundation.

## PR69 — Purchase suggestions backend foundation
- Added `purchase_suggestions` persistence with generated-key uniqueness and table guard coverage.
- Added backend domain/model/schema/repository/service/API layers for purchase suggestions.
- Added deterministic explicit generation for low ingredient stock, low packaging stock, insufficient order ingredients, and insufficient order packaging.
- Added manual suggestion creation, limited open-suggestion updates, mark purchased, and dismiss endpoints.
- Preserved read-only safety: generation and mark-purchased do not mutate stock movements, packaging movements, ingredient lots, orders, production batches, alerts, clients, recipes, ingredients, or packaging items.
- Updated `docs/api.md`, `state/current-focus.md`, and `state/handoff.md` for PR69.

## PR70 — Purchase Suggestions UI
- Added a frontend `/purchase-suggestions` workspace for purchase suggestions that consumes the PR69 backend endpoints.
- The «Закупки» navigation item now opens the real workspace instead of the old `/#purchases` placeholder.
- Added Russian, card-based purchase suggestion UI with status/reason/item-type/search filters, explicit regeneration, generation summary, manual suggestion creation, safe edit of quantity/unit/notes, mark purchased, and dismiss actions.
- Added visible safety copy that «Куплено» closes the recommendation but does not create IngredientLot records, packaging inbound movements, stock movements, order changes, or production changes.
- Updated dashboard copy to list «Закупки» as working now; no dashboard widgets were added.
- No backend behavior, migrations, supplier integration, online ordering, real procurement, stock mutation, order mutation, production mutation, scheduler, polling, notifications, import/export, or backup UI were added.

## PR71 — Dashboard operational overview frontend
- Replaced the dashboard placeholder with a frontend operational overview on `/`.
- Dashboard uses existing APIs and frontend aggregation for orders, clients, open alerts, open purchase suggestions, and recent production batches.
- Added onboarding, priority cards, “Что сделать сегодня” guidance, active orders, alerts, purchase suggestions, recent production, quick actions, and backup reminder blocks.
- Dashboard reload only repeats existing GET data; it does not regenerate alerts or purchase suggestions and does not run production readiness checks.
- Follow-up hardened dashboard loading so initial load does not show fake empty metrics, manual reload keeps stale data visible, and failed refresh shows a soft stale-data message.
- No backend endpoint, migration, analytics, scheduler, polling, notifications, backup/export, import/export, stock/order/production mutations, or procurement automation were added.
- Next recommended PR: Backup/export UI foundation or Backup/export backend/frontend foundation depending on existing backup/export state.

## PR72 — Orders reference refresh and localized quantity display hotfix
- Added frontend-only Orders reference refresh for create/edit forms so clients, recipe templates, recipe versions, client recipes, and packaging are reloaded before the form shows usable selectors.
- Added explicit Orders form reference loading, retryable error, and post-load empty-state behavior to avoid disabled empty dropdowns caused by stale cached `ordersState` data.
- Added Russian-friendly display formatting for user-facing quantities in Orders, production readiness, production snapshots/history, purchase snippets, and dashboard snippets so raw backend decimals like `100.000 г` render as `100 г`.
- Kept backend Decimal/API payload contracts unchanged by continuing to submit dot-normalized decimal strings and adding no backend endpoints, migrations, or business-logic changes.
- No stock/order/production side effects were added beyond existing explicit order create/edit/cancel/archive actions.

## PR74 Backup UI
- Added a frontend `Резервные копии` workspace at `/backups` that consumes PR73 backup status/list/manual-create endpoints only.
- Added navigation and dashboard reminder link to the backup workspace.
- Added status cards for database path/existence/size, backup directory path/existence, backup count, and latest backup.
- Added explicit manual backup creation with reason presets/custom reason and a refreshed backup history list after success.
- Missing backup directory is shown as a normal empty/local-first state; missing database disables backup creation with a clear next step.
- Restore, download, delete, scheduled backups, cloud backup, export, import, arbitrary paths, polling, notifications, backend changes, migrations, and business mutations were not added.

## PR75 — Export API foundation

- Added backend Export API foundation for explicit local JSON snapshots: `GET /api/exports/status`, `GET /api/exports`, and `POST /api/exports`.
- Added safe export path resolution mirroring backup behavior: user-mode exports use the resolved user `exports/` directory; development/test exports stay next to the configured database.
- Added JSON export creation with `manifest`, whitelisted domain `data`, entity counts, preserved IDs/relationships, catalog/user-organization tables, non-overwriting filenames, and reason normalization/safe filename sanitization.
- Follow-up removed absolute local `database_path` from exported JSON manifests; exports now store `database_filename` and `database_location_kind` while API responses may still show local paths for the local UI.
- Added export listing/status response schemas and tests for read-only GET behavior, missing directories, JSON creation, uniqueness, missing/invalid database handling, reason validation, and malformed filenames.
- Updated API/export documentation.

## PR76 — Export UI
- Added frontend `/exports` workspace and “Экспорт” navigation under “Данные и настройки”.
- Export UI consumes only PR75 endpoints: `GET /api/exports/status`, `GET /api/exports`, and explicit-click `POST /api/exports`.
- Added status cards for database/export directory, manual JSON export creation with reason presets/custom reason, export history list, and entity-count summary from backend response.
- UI explicitly states that import, restore, download/delete, CSV/XLSX, PDF/report, scheduled export, cloud export, and automation are not implemented.
- No backend behavior, migrations, business mutations, dashboard analytics, import/restore/download/delete flows, or arbitrary path inputs were added.

## Next recommended PR

Import CSV/XLSX draft backend foundation.

## PR77 — Import CSV/XLSX draft backend foundation

- Added import source/draft/draft-row persistence for the safe draft-only import flow.
- Added backend parsing and validation for CSV/XLSX import drafts with raw and normalized row storage.
- Added import API endpoints for supported targets, draft creation, draft listing, draft detail, and cancellation.
- Added parser/API tests covering supported formats, validation issues, persistence, cancellation, and safety boundaries.
- Updated API/import docs and state handoff.
- No import apply/confirmation, frontend UI, OCR/PDF/image import, automatic backup/export, or domain-table mutations were added.

### PR77 follow-up fixes

- Fixed CSV/XLSX draft row numbering so preview rows and row-level validation issues keep real source row numbers.
- Fixed XLSX parsing to use cell references and preserve blank/missing cell positions.
- Removed `content_hash` from user-facing import source API responses while keeping it stored internally.
- Documented import columns as user-facing aliases that future confirmation/apply must explicitly map to domain fields.

## PR78 — Import draft UI / preview UI
- Added frontend Import workspace at `/imports` with “Импорт” navigation in “Данные и настройки”.
- The UI consumes only PR77 import draft endpoints: targets, create draft, list drafts, draft detail, and cancel draft.
- The workspace supports CSV/XLSX target selection, explicit multipart draft upload, draft list, detail preview, validation issue display, preview rows, and cancellation.
- The screen repeatedly explains that rows are only draft/preview data and are not applied to real workshop records.
- Import apply/confirmation, column mapping, OCR, PDF/image import, automatic backup/export, polling, and business-domain mutations remain out of scope.
- Next recommended PR: import validation refinement or import apply design/backend, depending on browser smoke feedback.

## PR79 — Import validation refinement and apply readiness contract
- Added explicit import draft apply readiness contract for create/list/detail/cancel responses without adding apply or confirmation.
- Refined import validation with visible header aliases, decimal comma normalization, unit/date normalization, email/ID checks, and target-specific numeric rules.
- Updated Import UI to show readiness while keeping the flow draft-only.
- Updated API/import/state docs for PR79.

## PR80 — Import apply backend foundation
- Added backend-only `POST /api/imports/drafts/{draft_id}/apply` for explicit import application.
- Apply requires confirmation and backup acknowledgement, blocks cancelled/failed/already-applied/blocked drafts, and requires `allow_warnings=true` for ready-with-warnings drafts.
- Implemented transactional all-or-nothing creation for `ingredients`, `clients`, `recipe_templates`, and catalog-only `packaging_items`.
- Kept `ingredient_lots` and `orders` unsupported for apply in PR80.
- Added duplicate/existing-record conflict checks and packaging `stock` apply blocking.
- Successful apply updates draft/source to `applied`, stores `apply_result` in `summary_json`, and writes an audit log entry.
- Added migration support for the new `applied` import status and backend apply tests.
- Next recommended PR: PR81 — Import confirmation/apply UI.

## PR80 follow-up — Applied import cancellation safety
- Blocked cancelling already-applied import drafts; cancel now returns a structured conflict and leaves draft/source status as `applied`.
- Added regression tests for applied-cancel blocking and migration 0017 data preservation/applied status acceptance.
- Updated Import UI defensive labels/readiness pills for `applied` and hides cancel actions unless status is `draft`.
- Updated API/import docs to include `applied` readiness and the no-cancel safety rule for applied drafts.

## PR81 — Import confirmation/apply UI
- Added frontend confirmation/apply UI in the import draft detail panel for PR80-supported targets: ingredients, clients, recipe templates, and packaging items.
- The UI consumes `POST /api/imports/drafts/{draft_id}/apply` only after explicit apply confirmation, backup acknowledgement, and warning acknowledgement for `ready_with_warnings` drafts.
- Blocked, cancelled, failed, already-applied, and unsupported drafts (including ingredient lots and orders) cannot be applied from the UI.
- Successful apply refreshes the draft list/detail and displays created records; backup/export buttons only navigate and do not create files.
- No backend targets, mappings, cell editing, partial import, OCR/PDF/image import, stock/order/lot/production import, automatic backup/export, migrations, or domain direct frontend mutations were added.

## PR81 follow-up — Import apply stale-state and structured errors
- Reset import apply state before upload and after new draft creation so stale success/errors/results from a previous draft cannot appear on the newly selected draft.
- Preserved structured backend `detail.issues` on frontend API errors and surfaced issue messages in import apply conflict/error copy.
- Improved import draft cancel rejection copy to show backend-provided messages while keeping apply gating and supported targets unchanged.

## PR82 — Import apply hardening / smoke fixes
- Hardened import apply after PR80/PR81 without expanding supported targets: `ingredients`, `clients`, `recipe_templates`, and `packaging_items` remain the only apply-supported targets.
- Improved frontend apply failure display so structured backend conflict issues show row, field, code, and user-readable message, plus reassurance that working data was not partially changed.
- Added a double-submit guard while apply is in progress and preserved applied-draft result display after refresh through stored `summary.apply_result`.
- Expanded backend regression coverage for already-applied draft rejection, unsupported orders/lots, duplicate conflicts, warning acknowledgement, unapplied draft/source after failure, no side-effect backup/export/alert/purchase records, and applied detail/list readiness.
- Updated import API/format docs and state handoff. No migrations, new apply targets, automatic backup/export, stock movements, lots, orders, production records, alerts, or purchase suggestions were added.

## PR83 — Refresh existing onboarding checklist after import/apply
- Refreshed the existing single onboarding/checklist flow to match the current MVP workflow after import/apply.
- Added current onboarding steps for component lots, packaging, individual recipes, production readiness/confirmation, alerts/purchases, backup/export, and import drafts.
- Preserved the existing `/api/onboarding` API and `app_settings` state store; no second checklist, table, or API was added.
- Added compatibility handling for old onboarding state, including mapping `first_backup` to `backup_and_export`, ignoring unknown completed steps, and falling back unknown current steps to the first incomplete refreshed step.
- Updated frontend Russian onboarding copy, progress count, safety copy, and navigation hints/buttons.
- Fixed stale import readiness copy that said apply would be added in a separate future PR.
- Import apply targets were not expanded; ingredient lots and orders remain unsupported.

## PR84 — Demo data mode backend foundation
- Added backend-only demo data tracking migration with `demo_data_sessions` and `demo_data_records`.
- Added explicit demo status/install/clear API under `/api/demo-data`.
- Demo install is transactional and blocked for workspaces with non-demo business data.
- Demo clear deletes only tracked rows and blocks when real records reference demo records.
- Demo records are labeled with `Демо ·` and tracked by table name plus record id.
- No frontend UI, startup seeding, migration seeding, backup/export automation, production batches, or import apply target expansion were added.
- Next recommended PR: PR85 — Demo data mode UI.


## PR84 follow-up — Demo data clear safety hardening
- Expanded demo-data clear guards for client wishes, feedback, production batches, production batch rows, alerts, and purchase suggestions.
- Demo status now reports `can_clear=false` with a blocking reason when untracked working records reference tracked demo rows.
- Added regression tests for unsafe alert, purchase suggestion, client wish/feedback, production batch dependencies, and unsafe status behavior.
- No frontend UI, migrations, automatic install/clear, backup/export creation, production confirmation, import target expansion, or user-data deletion behavior was added.


## PR85 — Demo data mode UI
- Added `/demo-data` frontend route and “Демо-данные” navigation item under “Данные и настройки”.
- Added frontend API helpers for PR84 demo-data status/install/clear endpoints.
- Added human-readable demo status cards, backend blocking reason display, demo dataset explanation, explicit install confirmation with two checkboxes, explicit clear confirmation with one checkbox, created/deleted counts, safety boundaries, and post-install navigation links.
- Added compact dashboard card linking to demo data mode; dashboard does not duplicate the full demo UI.
- Demo data is not installed or cleared on page load; frontend does not create/delete business records directly and does not create backup/export automatically.
- No backend demo dataset changes, migrations, import apply target expansion, help center, reports, cloud, OCR/PDF/image behavior, or packaging work was added.

## PR85 follow-up — Demo data UI polish
- Clarified `docs/demo-data.md` so PR84 is described as the backend/API foundation and PR85 as the frontend UI route.
- Failed demo install/clear attempts now refresh demo-data status afterward, preserving the action error while replacing stale `can_install`, `can_clear`, and `blocking_reasons` with backend truth when available.
- No backend endpoints, migrations, demo dataset changes, automatic install/clear, backup/export creation, production behavior, import behavior, or direct frontend business-data mutation were added.

## PR86 — In-app help center foundation
- Added a static frontend Help Center at `/help` and marked “Помощь” ready in the “Данные и настройки” navigation group.
- Help content is bundled in `frontend/src/main.ts`, works offline, and does not call backend APIs or mutate business data.
- Added Russian user-facing articles for first steps, inventory/components/lots/movements/packaging, recipes/client recipes, clients, orders/readiness/production, alerts/purchases, backup/export, import, and demo data.
- Added frontend-only search, category filter, selected article detail view, and related-section navigation buttons that only navigate.
- Added a compact dashboard card linking to Help; no backup/export/import/demo actions are triggered from Help.
- No backend help API, database tables, migrations, CMS, AI/RAG, external docs, reports/settings/audit/package work, or import apply target changes were added.


## PR87 — Reports backend foundation
- Added read-only backend reports service, schemas, and `/api/reports` endpoints for overview, inventory, orders, production, and finance.
- Reports aggregate existing SQLite data only and do not create audit logs, backups, exports, alerts, purchase suggestions, or report tables.
- Finance values use Decimal-backed string totals and do not invent tax. Missing sale price/cost and mixed production units are surfaced as warnings.
- Added backend report service/API tests and docs.
- Next recommended PR: PR88 — Reports UI foundation, unless report API smoke finds backend follow-up fixes.


## PR87 follow-up — finance margin basis safety
- Fixed finance report margin basis: `known_margin` and `known_margin_percent` now use only production batches where both `sale_price` and `total_cost` are known on the same row.
- `known_revenue` and `known_production_cost` remain independent known totals, but reports no longer combine revenue from one incomplete batch with cost from another unrelated incomplete batch to produce margin.
- Added `complete_finance_record_count`, `incomplete_margin_count`, `margin_unavailable`, and `partial_margin_basis` coverage/docs.
- Manual long-running API smoke was not run in this non-interactive session; automated service/API tests cover the finance mismatch regression and read-only endpoints.

## PR88 — Reports UI foundation
- Added `/reports` frontend route and marked “Отчеты” ready in “Данные и настройки”.
- Added typed frontend report DTOs and API helpers for PR87 read-only endpoints: overview, inventory, orders, production, and finance.
- Added Reports page hero, reload button, tabs, metric cards, backend warning panels, friendly empty state, related navigation buttons, and finance safety copy.
- Added compact dashboard card linking to Reports.
- Reports UI displays backend-provided values only and does not calculate core report values, mutate business data, create backup/export files, regenerate alerts/purchase suggestions, or add PDF/export/charts/accounting.


## PR88 follow-up — Reports dashboard card wiring
- Wired the compact Reports dashboard card into the dashboard between demo data and help so users can open `/reports` from the main screen.
- Updated the defensive planned-section fallback for “Отчеты” so it no longer says reports are a future module.
- Reports remain read-only and backend-owned; no mutations, backup/export creation, alert/purchase regeneration, production actions, import apply actions, or frontend finance recalculation were added.

## PR89 — Report document export foundation
- Added backend report document schemas, service, and `/api/report-documents` endpoints for status, metadata listing, and explicit overview document creation.
- Added Markdown “Сводка мастерской” generation from backend `ReportsService.get_overview()` data with required Russian sections, warnings, finance limitation copy, and explicit non-accounting/non-tax notes.
- Generated files are stored under the safe report-documents directory with non-overwriting timestamped filenames and JSON metadata sidecars.
- PDF and DOCX are rejected with a clear Russian unsupported-format message; Markdown is the only PR89 format.
- Document generation writes only the Markdown document and metadata sidecar, does not mutate business data, does not create backup/export snapshots, and does not regenerate alerts or purchase suggestions.
- Added `docs/report-documents.md`, API docs, Reports docs cross-reference, state updates, and backend service/API tests.
- Next recommended PR: PR90 — Report document export UI, unless backend smoke finds follow-up fixes.

## PR89 follow-up — Report document pair-safety and docs polish
- Made report document file creation pair-safe: the service now chooses a unique `.md + .json` pair where both paths are free before writing.
- Added rollback behavior so metadata sidecar write failure best-effort removes the newly created Markdown file and does not leave orphan Markdown.
- Added service regression tests for stale metadata sidecars and metadata-write failure rollback.
- Corrected report document filename examples and documented numeric suffix behavior.
- Updated Reports docs so they no longer describe the `/reports` frontend UI as future-only.
- Manual long-running API smoke was not run in this non-interactive session; automated tests cover the follow-up safety scenarios.

## PR90 — Report document export UI + sidecar cleanup hardening
- Added a focused `/report-documents` frontend route labeled «Документы отчетов» under «Данные и настройки».
- The UI loads PR89 report document status/list endpoints and creates only explicit Markdown «Сводка мастерской» documents via `POST /api/report-documents/reports/overview`.
- Page load and list refresh remain read-only; PDF/DOCX are documented in the UI as future work and no unsupported format actions are shown.
- Added a Reports page contextual navigation link to the document export UI; it does not create documents from `/reports`.
- Hardened `ReportDocumentService` cleanup so the metadata sidecar is unlinked only if this operation actually created it, while preserving original safe errors.

## PR92 — Report PDF generation foundation
- Added explicit PDF generation for workshop overview report documents through the existing `/api/report-documents/reports/overview` pipeline.
- Markdown remains supported; DOCX remains unsupported with a clear Russian error.
- PDF generation uses backend `ReportsService` overview data and the same report document sections as Markdown, without frontend recalculation, tax invention, business-data mutation, backup/export/import/demo creation, or alert/purchase regeneration.
- Generated PDF files and metadata sidecars are stored only in the safe `exports/report-documents` area with non-overwriting filenames and cleanup on current-operation failures.
- Status reports `pdf` only when a local Cyrillic-capable font is available for readable Russian text.
- `/report-documents` can explicitly create Markdown or PDF when available, and `/reports` navigation copy was clarified to «Открыть документы отчетов».
- Next recommended PR: PR93 — Report PDF UI polish / download-open workflow, unless smoke finds follow-up fixes.

## PR92 follow-up — deterministic PDF availability
- Made PDF availability deterministic and independent of host test environment fonts.
- Updated PDF happy-path service/API tests to monkeypatch PDF availability and fake PDF output instead of relying on installed DejaVu, Liberation, or Noto fonts.
- PDF is advertised only when the backend finds a parseable local `.ttf` font with Cyrillic glyphs that the current renderer can use.
- TTC font collections are not supported in PR92.
- Markdown remains always available, and unavailable PDF creation is rejected with a safe Russian message.
- Corrected report-document docs so they no longer describe PDF as future-only after PR92 and use document-file + metadata-sidecar wording.

## PR93 — Report PDF UI polish / download-open workflow
- Added a read-only `/api/report-documents/{document_id}/download` endpoint for known generated Markdown/PDF report documents.
- The endpoint validates metadata, format/filename consistency, safe directory containment, file existence, and disposition before serving files.
- `/report-documents` now shows `Открыть PDF`, `Скачать PDF`, and `Скачать Markdown` actions through the backend endpoint.
- Document creation remains explicit; `/reports` remains navigation-only and DOCX remains unsupported.

## PR93 docs follow-up — frontend concept wording
- Removed stale `docs/frontend-concept.md` wording that described report document export as Markdown-only or PDF future-only.
- Documented the current PR92/PR93 workflow: Markdown always available, PDF shown only when backend support is advertised, DOCX unsupported, and generated files accessed only through the safe backend download endpoint.
- Reconfirmed that `/reports` only navigates to `/report-documents` and does not create files.

## PR94 — Settings UI foundation
- Added a ready `/settings` route and «Настройки» navigation item.
- Added a user-facing, read-only Settings foundation page for local data, backups, import/export, report documents, demo data, Help Center, About app, and future settings boundaries.
- Settings actions only navigate to existing safe workflows and do not run backup/export/import/demo/report document creation actions.
- No backend settings API, persistence, migrations, file creation, or business-data mutations were added.

## PR95 — Settings data/status foundation
- Added read-only `GET /api/settings/status` backend endpoint.
- Added Settings status DTOs/service with local-first app status, user-data separation status, safe workflow capabilities, and Settings Decision Matrix.
- Updated `/settings` to load backend status, render local data status, capability cards, future settings groups, app info, and MVP boundaries.
- Settings actions remain navigation-only; no editable controls, persistence, migrations, file creation, or business-data mutations were added.
- Added `docs/settings.md` and updated API/frontend docs.

## PR95 type-safety polish
- Replaced the raw `str` status parameter in `SettingsService._definition()` with the shared Settings definition status Literal type.
- Removed the `# type: ignore[arg-type]` from settings status construction.
- No runtime Settings behavior, response shape, persistence, migrations, or editability changed.

- PR96 added the first safe editable Settings area: backend-owned workshop profile fields for workshop name, master name, contact text, and note.
- Added `GET /api/settings/workshop-profile` and `PUT /api/settings/workshop-profile`, using the existing `app_settings` storage with grouped JSON key `workshop_profile` and no migration.
- Updated `/settings` with an explicit «Профиль мастерской» form, save/cancel states, validation display, and safety copy.
- Updated Settings status so only workshop profile fields are `editable_now`; calculation-sensitive settings remain non-editable.

## PR98 — Workshop profile integration with report documents
- Report document generation now reads the saved Workshop profile and includes configured fields in new Markdown/PDF workshop overview documents.
- Profile rendering is backend-owned, plain-text/Markdown-safe, and shared by Markdown/PDF content lines.
- Empty/default profiles continue to generate documents without an empty profile section.
- Existing generated documents and metadata are not rewritten.
- Settings and report-document UI copy now reflects that Workshop profile is editable and added to new summaries.
- Docs/state were cleaned up from stale PR94/PR95/PR96/PR97 wording.
- No report calculations, business records, tax/currency/margin/unit/stock-threshold/expiry settings, document templates, logo upload, DOCX, invoices, labels, or certificates were added.

## Settings UI repair

- Manual browser smoke found a blocking Settings UI defect: profile fields flowed horizontally and the page exposed technical planning content.
- The focused Settings repair removes future settings matrices, readiness classifications, repository metadata, and MVP-boundary planning copy from the runtime `/settings` screen.
- The Workshop profile section now renders from its own API state instead of being hidden by the general Settings status request.
- Next step after merge: rerun isolated browser smoke for Workshop profile saving/clearing and report-document generation integration.

## Shared action-state visual contract

- Source and runtime audits identified inconsistent shared action visual states across routes.
- Current branch contains only the shared visual action-state contract in the frontend styles and minimal state notes.
- No application behavior, API behavior, route logic, loading logic, or data behavior changed.
- Browser smoke remains required across representative routes before merge.
- Next planned system-level task: shared feedback presentation and semantics.

## PR105 focus contrast follow-up

- Changed shared action `:focus-visible` outline color from `rgba(211, 154, 122, .75)` to `#9a5f49`; sidebar focus styling remains unchanged.
- Browser smoke used an isolated temporary SQLite database and temporary user-data directory.
- Tested `/settings`, `/exports`, `/report-documents`, `/alerts`, `/purchase-suggestions`, `/demo-data`, sidebar keyboard navigation, and 1440×900 plus 390×844 viewports.
- Passed: shared action keyboard focus, hover/pressed states, disabled settings controls, `/exports` intercepted request-failure presentation, document action links, demo danger action after isolated demo install, no horizontal overflow, screenshots, and no page errors.
- Unavailable in isolated data: alert resolve/dismiss row actions, purchase-suggestion row actions, and a disabled danger action after the safe demo install state.
- Browser console finding: one expected 503 resource error from the intentional `/exports` request-failure interception; no unexpected console errors.
- Frontend build passed.

## Initial shared feedback presentation and semantics slice

- Added one shared frontend feedback helper for neutral/success/warning/error presentation.
- Added shared CSS for readable, non-color-only feedback blocks with structured detail support and narrow-screen wrapping.
- Added persistent hidden announcement regions outside the re-rendered app root: polite `role="status"` and assertive `role="alert"`.
- Migrated feedback and one-time announcement behavior for `/settings`, `/exports`, `/report-documents`, `/imports`, and `/demo-data` only.
- Preserved structured import apply errors with row number, field name where available, safe user-facing message, issue list, and no-partial-change statement.
- Added `aria-busy` coverage for the scoped forms/panels only.
- Source inventory found remaining legacy `.page-message`, `.error-message`, and `.inline-message` uses across dashboard, alerts, purchase suggestions, backup, reports, recipes, clients, production history, stock/catalog, onboarding, and help; these remain outside this migration slice.
- Checks: `git diff --check` passed; `cd frontend && npm run build` passed; `cd backend && python3 -m pytest` ran 468 tests with 463 passed and 5 existing backend-area failures unrelated to this frontend/state-only branch; isolated backend/frontend startup curl passed for `/api/health` and `/settings`.
- Earlier Codex-local Playwright smoke and screenshots were unavailable in that environment because Playwright was not installed and npm registry access failed; this limitation was later superseded by the completed external Hermes audit recorded below.

## PR106 follow-up — feedback semantics fixes

- Fixed Workshop profile stale result feedback after editing begins: state `message`/`error`, visible result markup, and persistent announcers are cleared while the dirty notice remains controlled without full render.
- Changed normal Workshop profile initial load to keep the action-result message empty; save/cancel remain user-action results.
- Pre-created persistent polite/assertive announcers during startup before the first action can update text.
- Split mutation success/failure from follow-up refresh failure for export creation, report document creation, import draft creation, demo-data install, and demo-data clear. A successful mutation with failed refresh now preserves the success result and asks the user to refresh instead of announcing a false action failure.
- Added import draft cancellation success/failure announcements to the scoped action-result contract.
- Backend baseline verification: base commit `2265802f07b3ee3df7a1c5478bc6ae11fed096b7` and PR branch both ran `cd backend && python3 -m pytest` with the identical 5 failing tests and 463 passing tests; no backend test failure exists only on this PR branch.
- Playwright/local browser discovery in Codex found no local browser automation tool, so Codex itself did not run browser smoke at that time; the later external Hermes audit completed the required browser verification recorded below.

## PR106 correction — Import Apply mutation vs refresh

- Corrected the earlier broad Import-flow statement: import draft creation, import draft cancellation, and import draft application are all covered, and Apply now has its own mutation-vs-refresh separation.
- Import Apply mutation failure remains the only path that sets `applyStatus = 'error'`, fills `applyError` / `applyErrorIssues`, announces assertively, and shows the no-partial-change statement.
- Import Apply mutation success now immediately preserves `response.apply_result`, sets success, closes confirmation, resets Apply checkboxes, announces politely once, and replaces the stale selected draft with the backend apply response before refreshing.
- Apply success plus failed list/detail refresh now preserves the successful mutation result and shows a refresh warning instead of `Не удалось применить черновик`.
- Stale pre-apply detail cannot offer Apply again after successful mutation because selected draft state is replaced with the apply response before refresh.
- Structured mutation errors still preserve row, field, code, and message details for actual Apply failures.
- Local pending-smoke wording is superseded by the completed external Hermes audit recorded below.

## PR106 correction — render already-applied refresh warning

- Added explicit `applyRefreshWarning` state for Import Apply read-model refresh failures.
- The previously hidden Apply refresh warning is now rendered in the `status === 'applied'` branch using `feedbackMessage('warning', importUiState.applyRefreshWarning)`.
- Apply success plus refresh failure remains `applyStatus = 'success'`, preserves `response.apply_result`, preserves the authoritative applied draft, and tells the user to press Refresh to reread the draft list/preview.
- Read-model refresh failure does not set `applyError`, does not populate structured mutation issues, does not show the no-partial-change statement, and does not call `announceAssertive()`.
- Stale applied state cannot offer Apply again because selected draft is already replaced with the mutation response before refresh.
- Warning state is cleared on Apply reset, opening another draft, starting Apply, actual Apply mutation failure, and successful post-Apply refresh.
- Local pending-smoke wording is superseded by the completed external Hermes audit recorded below.


## PR106 Hermes browser smoke completed

- Canonical tested GitHub runtime head: `4a2a88d156d1516568b608b113818dfe77e32210`. External GitHub verification confirmed this was the published PR #106 head; the local Codex task checkout may use rewritten SHAs.
- Environment: isolated temporary repository checkout at `/tmp/cwo-pr106-deterministic-20260713-092916/repository`, isolated SQLite database, isolated user-data directory, local frontend/backend plus deterministic local fault proxy, Headless Chrome, 1440×900 desktop viewport, 390×844 narrow viewport, no real user data.
- Verdict: `PR106_DETERMINISTIC_SMOKE_PASS_WITH_NON_BLOCKING_FINDINGS`.
- Normal Import Apply passed: draft creation returned 201, Apply returned 200, exactly one Apply POST occurred, exactly one ingredient was created, Apply result remained visible, repeat Apply became unavailable, polite success was observed, no assertive failure occurred, and `aria-busy` returned to false.
- Apply success plus refresh failure passed: Apply mutation returned 200, the proxy intentionally returned 503 for the immediate draft detail/list refresh requests, mutation success and the applied result were preserved, the imported ingredient existed exactly once, shared warning feedback told the user to press `Обновить`, false mutation-failure text was absent, no assertive Apply failure was emitted, repeat Apply stayed unavailable, manual Refresh recovered the final state, and no second Apply POST or duplicate record occurred.
- Structured mutation conflict passed: duplicate Apply returned 409, structured row-level details were visible, the persistent assertive `role="alert"` region received the blocking failure, no polite Apply success was emitted, no duplicate ingredient was created, no partial domain write occurred, and `applyRefreshWarning` remained empty.
- Settings passed: initial profile load did not show action-success feedback, Cancel restored the saved value and produced polite feedback, Save produced polite feedback, editing after Save cleared stale visible success, focus remained in the field, and `aria-busy` behaved correctly during Save.
- Responsive/keyboard smoke passed: no page-level horizontal overflow at 390×844, tested controls remained reachable, persistent announcement regions were outside `#root`, and 27 keyboard-reachable elements were observed in logical DOM order. No screen-reader certification or formal WCAG conformance claim is made.
- Diagnostics: intentional 503 responses belonged only to the refresh-failure scenario; the expected 409 belonged only to the conflict scenario; final record counts were normal import 1, refresh-failure import 1, duplicate created by rejected conflict 0; seven PNG screenshots and seven matching metrics files were verified; repository remained clean after the audit; audit-started ports were released.
- Non-blocking observations: MutationObserver errors came from the deterministic audit harness observing `#root` before it existed and were not an application defect; a separate narrow screenshot of the conflict draft was unavailable after scenario state transition, while required conflict workflow evidence was present.
- All mandatory PR106 browser scenarios passed, no code blocker remains, and PR #106 is now merged and verified. Browser smoke does not need to be repeated for this documentation-only plan PR because it changes only documentation/state files.

## MVP product-readiness implementation plan

- Added the approved active implementation plan at `docs/implementation-plan.md`.
- The plan is derived from the current strategic roadmap, actual implementation status, and the evidence-based Hermes project audit.
- `docs/roadmap.md` remains authoritative for product scope and strategic sequencing.
- `docs/implementation-plan.md` now controls the current short-horizon sequence, product-readiness slices, unfinished MVP obligations, and MVP release gates.
- PR #106 is merged and verified; its completed Hermes browser smoke remains the latest runtime verification baseline.
- Next active runtime focus is Slice A1 — User-facing technical copy cleanup, which must be implemented in a separate focused PR with no future PR number assigned yet.
- This documentation-only PR changed no runtime behavior, APIs, schemas, migrations, dependencies, lockfiles, CSS, frontend runtime code, or backend runtime code.

## Slice A1a — focused technical copy cleanup

- Implementation summary: removed the normal healthy local-service badge, kept a Russian unavailable recovery message, corrected the `/imports` introduction to match the existing draft/preview/confirm/Apply workflow, and centralized `/demo-data` visible count labels with «Другие данные» fallback for unknown keys.
- Actual changed files: `frontend/src/main.ts`, `docs/implementation-plan.md`, `state/current-focus.md`, `state/progress.md`, and `state/handoff.md`.
- Actual checks: `git diff --check` passed; `git diff --name-only`, `git diff --stat`, and `git status --short` were reviewed; `cd frontend && npm run build` passed; `cd backend && python3 -m pytest` reported the known unchanged 5 backend failures and 463 passing tests.
- Actual browser evidence: Playwright smoke used an isolated temporary SQLite database and user-data directory, local backend on `127.0.0.1:8010`, frontend on `127.0.0.1:5173`, and 1440×900 plus 390×844 viewports. Healthy state loaded without the positive API/backend badge or page-level overflow; `/imports` showed the corrected workflow copy; `/demo-data` showed Russian labels after demo install with no raw snake_case count keys; narrow view had no page-level overflow and keyboard focus remained visible; unavailable-state recovery text appeared with the existing repeat action and no observed polling loop. Screenshots were saved under `/tmp/cwo-a1a-screens`.
- Limitations: backend pytest failures are unchanged baseline failures outside this frontend-copy slice; offline smoke intentionally produced failed network-resource console messages while API requests were aborted to simulate unavailable local service.
- Merge status: branch is ready for focused review after commit/PR creation; no future PR number is assigned here.

## Slice A1b1 — Demo Data and inventory movement copy cleanup

- Scope: static user-facing copy only in `/demo-data`, `/ingredient-lots`, and `/stock-movements`.
- Updated Demo Data blocking, installation, clearing, and boundary wording to avoid backend/internal terminology while keeping dynamic blocking reasons visible and escaped.
- Updated ingredient-lot and stock-movement loading/fallback wording to describe user-visible failures without API terminology.
- Updated stock-movement balance and safety explanations to describe movement-derived balances and outgoing movement limits in product language.
- Preserved demo install/clear behavior, confirmation rules, disabled rules, stock calculations, backend-owned validation, request flow, CSS, dependencies, migrations, and `docs/implementation-plan.md`.

## Slice A1b2 — Backup and Export capability copy
- Scope: static user-facing copy only for `/backups`, `/exports`, and `dashboardBackupReminder()`.
- Updated wording to distinguish резервная копия from export, explain local file storage, and state that restore/import-back-from-export are not performed on these screens.
- Preserved dynamic filenames, raw path values, request flow, disabled states, announcements, escaping, and backend-owned status/count data.
- Deferred Reports, Help Center, route readiness metadata, path presentation redesign, and remaining A1 closure work to later focused slices.
- Verification: repository hygiene and focused source-diff review passed; frontend build passed.
- Backend baseline: 468 collected, 463 passed, and the same 5 known baseline failures; no backend files changed.
- Publication: PR #111 was published from GitHub branch `codex-rzipfx`; the pre-correction head was `b6d44e935d5e320d91b955feec97667f03c93b05`.
- Review status: runtime diff is static-copy only and approved for merge after this metadata correction and final GitHub mergeability check.

## Slice A1b3a — Reports and Report Documents product copy
- Started focused A1b3a runtime-copy cleanup from the local baseline that includes merge commit `06ade9372ff060a7c3ec33aaa01e50e32c5aceee` for PR #111.
- Scope is limited to `/reports`, `/report-documents`, and `dashboardReportsCard()` static user-facing copy, plus this state update.
- Slice A1 remains IN PROGRESS; A1b3b, A1c, A2, backend behavior, CSS, documentation rewrites, report calculations, and report-document generation remain out of scope.
- Publication metadata must be verified by the repository owner; no future PR number is assigned here.

## Slice A1 closure correction — PR #113 pending review

- Navigation readiness and Help Center cleanup are implemented in runtime: implemented modules stay marked ready, the standalone readiness placeholder stays removed, Help uses Russian product language, and onboarding terminology is cleaned.
- Technical contract rewrites from the first PR #113 head were rejected and restored to the main baseline; the runtime Help Center remains the user-facing help surface for this PR.
- Runtime source review is pending final confirmation on the corrected diff.
- Required browser smoke is pending for navigation, Help, and previously cleaned A1 routes.
- A1 is not yet closed; it remains IN PROGRESS until corrected-head review and required smoke pass.
- A2 is not yet ready and remains blocked by A1.

## Slice A1 closure verified — PR #113

- Slice A1 runtime implementation was reviewed on published SHA `040c90fa781edea8484eb84595745c3a3aaf5eaf`.
- Deterministic browser smoke completed with 53 of 53 checks passing.
- Desktop and narrow navigation, Help Center, Orders readiness workflow, cleaned A1 routes, back/forward navigation, and sidebar behavior passed.
- The original offline/recovery test infrastructure gap was not accepted as evidence; R1-R5 were replaced by a targeted retest with genuine backend termination and restart.
- The targeted retest confirmed PID termination, an empty listening port, connection-refused health state, friendly offline UI, restart against the same temporary database, and complete browser recovery.
- JavaScript console errors: 0.
- Real user data and production data were not used.
- Repository integrity and temporary-data isolation passed.
- Slice A1 is DONE.
- Slice A2 is READY and is the next allowed implementation slice.

## Slice A2 structured form validation — PR #114 implementation under review

- Implemented a shared frontend validation parser/normalizer for backend `detail`, `issues`, `field`, `loc`, `message`, `msg`, `code`, and `type` shapes.
- Applied the validation state to `/clients` create/edit and `/ingredients` create/edit only, with explicit allow-listed Russian field labels and inline field errors.
- Added minimal accessible feedback markup/styles: form-level summaries for unassigned errors, `aria-invalid`, `aria-describedby`, and stable error IDs.
- Preserved draft values on rejected submits, cleared validation on retry/success/cancel/record switch/field edits, and kept duplicate-submit protection without retry logic.
- Added dependency-free parser tests through `cd frontend && npm run test:form-validation`.
- Backend code, schemas, migrations, domain rules, recipe calculations, inventory write-offs, production readiness/confirmation, Import Apply, backup/export behavior, navigation routes, dependencies, and lockfiles were not intentionally changed.
- Slice A2 status remains IN PROGRESS — implementation PR under review. Slice A3 remains BLOCKED A2.

## Slice A2 PR #114 correction under review

- Repaired field-error clearing so typing in a corrected Clients or Ingredients field updates only that field's validation DOM and preserves focus/caret instead of re-rendering the app.
- Guarded create/edit close and record-switch actions while the corresponding Clients or Ingredients mutation is in flight, with request tokens invalidated on safe context changes.
- Split mutation validation failures from post-save list-refresh failures so saved records show success and a separate refresh warning instead of save-validation errors.
- Tightened parser field-path mapping: exact known fields and approved `body`/`query`/`path` transport prefixes map inline; unknown nested paths stay in the form summary.
- Slice A2 remains IN PROGRESS — correction under review. Slice A3 remains BLOCKED A2.

## Slice A2 verified closure — PR #114

- Final verified runtime head: `8eb5d0c2c116c83d4162d10895268375e0bc1e1e`.
- Structured validation foundation is complete for Clients create/edit and Ingredients create/edit.
- Final correction preserves the original focused input DOM node, caret and selection without a global render or programmatic refocus.
- Parser tests passed: 11/11.
- Targeted validation DOM tests passed: 4/4.
- Both frontend test scripts passed when executed concurrently.
- Frontend build passed.
- Targeted Clients and Ingredients backend tests passed: 29/29.
- Real Firefox focus-preservation smoke passed for Clients and Ingredients.
- Expected HTTP 422 validation responses were separated from unexpected request failures.
- JavaScript exceptions: 0.
- Console errors: 0.
- Unused `linkedom` and its transitive lockfile entries were removed.
- No backend runtime, schema, migration, domain, inventory, production, import, backup, export or navigation behavior changed.
- Slice A2 is DONE and awaiting PR #114 merge.
- Slice A3 is READY for a separate focused sub-slice after PR #114 is merged.

## Slice A3.1 Ingredient Lots structured validation — implementation under review

- Began the first Slice A3 sub-slice after PR #114 merged.
- Scope is limited to `/ingredient-lots` create/edit structured validation.
- `/stock-movements` and all other A3 candidate forms remain pending.
- Backend runtime behavior, schemas, migrations, dependencies, inventory calculations, and stock movement behavior are not intentionally changed.
- Slice A3.1 remains IN PROGRESS — implementation under review until PR review and accepted smoke evidence.

## Slice A3.1 correction — validation lifecycle under review

- Corrected Ingredient Lot submit start so empty validation is applied through the targeted updater before the request, clearing stale summary, inline errors, and validation-owned ARIA without a global render.
- Completed in-flight action guards for submit, cancel/clear, row edit, and row deactivate actions; deactivation now also has a handler-level guard during create/update.
- Verification: frontend parser tests, targeted validation DOM tests, frontend build, concurrent frontend tests, focused Ingredient Lot backend tests, and isolated local API smoke passed.
- Browser smoke remains pending reviewer execution. Slice A3.1 remains IN PROGRESS — correction under review.

## Slice A3.2 Inventory structured validation closure — PR116 implementation

- Baseline includes merged PR #115 / A3.1 at merge commit `8b3ea5f7ab2b880d901250d111f6f5dca369c4b4`.
- Migrated existing frontend inventory forms only: `/stock-movements` manual ingredient-lot movement create, `/packaging-items` Packaging Item create, and `/packaging-items` Packaging Item edit.
- Reused the shared structured validation parser and targeted validation DOM updater; added Stock Movement and Packaging Item wrappers, explicit field-label allow-lists, inline errors, form summaries, ARIA attributes, draft preservation, duplicate-submit guards, stale-response tokens, and success-versus-refresh-warning separation.
- The initial PR116 implementation was frontend-only. The correction added focused backend domain validation for the documented manual-adjustment reason invariant, without schema, migration, persistent model, direct packaging stock edit, historical Stock Movement edit/delete action, or new inventory architecture changes.
- Current frontend `/stock-movements` supports ingredient-lot movements only. Backend packaging movement APIs exist, but a packaging movement UI is not implemented in PR116 and remains follow-up work.
- Initial verification was superseded by later PR116 correction checks; see the correction entries below for final counts.
- Browser/UI smoke was not run in this environment; reviewer smoke remains required before merge.
- Slice A3 remains IN PROGRESS after A3.2; recipe and recipe-version validation remain a later separate slice.
- A3.2 implementation complete in PR116; merge pending.

## Slice A3.2 PR116 correction — validation lifecycle and manual-adjustment invariant

- Corrected Stock Movement and Packaging Item submit-start lifecycle so stale validation is cleared through the targeted updater and current DOM controls/actions are guarded directly, without calling the global renderer before the mutation request.
- Stock Movement lot selector is disabled during an active movement mutation and re-enabled after recoverable failure.
- Packaging create/edit/cancel context switches now clear validation, refresh warnings, and stale-response tokens only after discard confirmation succeeds; cancelled confirmations preserve the current validation state.
- Backend domain drafts now enforce the existing manual-adjustment invariant for ingredient-lot and packaging movements: `manual_adjustment_in` and `manual_adjustment_out` require non-empty `reason` and return structured `422` with `field = "reason"` through existing APIs.
- Verification after correction: frontend form-validation tests (11/11), targeted validation/update lifecycle tests (superseded; final 15/15 below), frontend build, focused backend inventory tests (82/82), and isolated API smoke with manual-adjustment-without-reason rejection all passed.
- Browser smoke remains pending reviewer execution in an environment with browser tooling.
- A3.2 implementation corrected in PR116; merge pending. A3 remains IN PROGRESS.

## Slice A3.2 PR116 correction — remaining mutation lifecycle races
- Packaging Item mutation now guards adjacent packaging filters, catalog creation, assignment, tag/category search, reload, create/edit/cancel/archive controls at both rendered/direct-DOM and handler levels so they cannot rerender over the active form during submit.
- Stock Movement selected-lot detail loading now uses a detail request token and selected-lot check, and stale detail responses do not render while a Stock Movement mutation is active.
- Control restoration uses mutation markers so pre-existing disabled/readonly states remain intact after recoverable `422` responses.
- A3.2 implementation corrected in PR116; merge pending. A3 remains IN PROGRESS. Browser smoke has not been run in Codex unless a later entry records it.

## Slice A3.2 PR116 final async lifecycle correction
- Stock Movement selected-lot balance/history reads now use a shared request-generation helper: mutation start invalidates old detail requests, post-save refresh is token-aware, and state is written only after selected-lot and submit-token freshness checks pass.
- Packaging page writes are mutually exclusive across item save, item deactivation, catalog category/tag creation, and category/tag assignment save; context changes, filters, catalog searches, reload, and row actions are blocked while any Packaging write is active.
- Mutation marker helpers moved into a focused frontend lifecycle helper module so tests execute the production helper rather than copying it.
- Final verification in Codex: frontend form-validation tests 11/11, targeted validation/update lifecycle tests 20/20, concurrent frontend validation tests 11/11 and 20/20, frontend build passed, focused backend inventory tests 82/82, and isolated temporary-SQLite API smoke passed.
- Browser smoke remains pending reviewer execution. A3.2 implementation corrected in PR116; merge pending. A3 remains IN PROGRESS.

## Slice A3.2 PR116 final correction — post-save refresh lifecycle gaps
- Packaging Item save now keeps the Packaging page mutation lock active until post-save list refresh succeeds or fails; no intermediate unlocked render is emitted before refresh completion.
- Stock Movement post-save detail refresh failure now terminates the detail status with `error` while preserving the movement success message and separate refresh warning.
- Added deferred Promise regression tests for Packaging lock-through-refresh, Packaging refresh failure, stale Packaging refresh, Stock refresh failure terminal state, and stale Stock refresh failure.
- Final verification in Codex: frontend form-validation tests 11/11, targeted validation/update lifecycle tests 20/20, concurrent frontend validation tests 11/11 and 20/20, frontend build passed, focused backend inventory tests 82/82, and isolated temporary-SQLite API smoke passed.
- Browser smoke remains pending reviewer execution. A3.2 implementation corrected in PR116; merge pending. A3 remains IN PROGRESS.
