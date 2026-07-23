# Current focus — B3.4+B3.5 core workspace shared-feedback lifecycle

- PR #136 is merged; B3.3 is complete at merge commit `e7c2d97473070f361052325fd6476208629af1cc`.
- Active combined slice: B3.4+B3.5 — Formula/Client Workspace plus Inventory/Catalog Workspace.
- Branch: `codex/b3.4-b3.5-core-workspace-feedback`.
- Starting `main` SHA: `e7c2d97473070f361052325fd6476208629af1cc`.
- This is a frontend lifecycle migration. Backend production files, schemas, migrations, Orders, and Production remain outside scope.

## Supported operation matrix

- Recipes: template list/detail/create; version list/detail/create with complete composition; backend calculation GET; rendered recipe category/tag create and assignment.
- Clients: list, selected-client related reads, create, update, and deactivate.
- Client Recipes: list/detail, create from a RecipeVersion, composition replacement, deactivate, and restore.
- Client Wishes: list, create, status update, and archive.
- Client Feedback: list and create only.
- Inventory: composed read-only overview, ingredient-lot balances, and packaging balances.
- Ingredients: list, create, update, deactivate, and rendered category/tag create and assignment.
- Ingredient Lots: list/reference reads, create, update, deactivate, and lot balance/movement reads used by Stock Movements.
- Stock Movements: selected-lot movement/balance reads and append-only create with GET-only reconciliation.
- Packaging: list, create, update, deactivate, and rendered category/tag create and assignment.

Explicit exclusions remain: RecipeTemplate update, in-place RecipeVersion update/delete/archive, persisted RecipeIngredient row CRUD, ClientRecipe calculation, Client Feedback update/archive/delete, Packaging StockMovement support, Orders, Production, backend expansion, and migrations.

## Lifecycle decisions

- Two bounded domain lifecycles share only small request-ownership primitives.
- Reads distinguish initial, refresh, detail, related, reference, calculation, mutation-follow-up, and reconciliation ownership.
- Obsolete same-route reference owners are discarded without application, announcement, or focus.
- Mutations apply route-specific side effects only after current ownership and authoritative DTO validation.
- Definite failures preserve drafts; ambiguous transport outcomes lock repeat mutation until authoritative GET reconciliation.
- StockMovement creation sends exactly one POST, never retries automatically, and cannot enter presentation from an invalid response.
- Accepted mutation success remains visible if a follow-up GET fails.
- Route-owned focus uses real rendered controls or focusable workspace/form targets; announcements are request-owned.

## Required verification

- Run both new focused suites twice.
- Run all existing frontend focused regressions and the frontend build.
- Run discovered focused backend domain suites and complete `pytest -q`; branch-only backend failure delta must be zero against the accepted 492-pass/4-known-failure baseline.
- Run repository-integrity checks, commit, publish the branch, and create exactly one PR.

External smoke-authoring contract not stored in the repository; not required for this smoke-deferred runtime slice.

Browser smoke: DEFERRED BY PRODUCT OWNER — FULL BLOCK B INTEGRATION SMOKE.

Next slice: B3.6 — Order-to-production shared-feedback lifecycle.
