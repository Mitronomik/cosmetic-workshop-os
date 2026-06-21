# Progress

## Current phase
PR6 - Ingredients foundation implemented

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
- PR3 tests/smoke coverage for development fallback, env overrides, directory creation, explicit startup initialization, invalid startup modes, no hidden endpoint migrations, and no business tables
- PR4 backend backup service for copying existing SQLite databases into user-data `backups/` without modifying or overwriting the source
- PR4 user-mode startup backup-before-migration guard for existing databases with pending migrations
- PR4 tests for missing-source failures, copy fidelity, non-overwrite filenames, explicit backup directory creation, startup backup behavior, brand-new startup behavior, ordinary read endpoint safety, and no business tables
- PR5 backend-only Decimal parsing and quantization helpers for grams, milliliters, percentages, money, counts, and density
- PR5 MVP unit primitives for grams, milliliters, percent, and pieces with canonical codes and Russian labels
- PR5 lightweight measurement value objects for weight, volume, percentage, money, quantity/count, and density
- PR5 density conversion foundation that converts ml to grams only with an explicit density and returns a missing-density warning otherwise
- PR5 validation issue/error primitives for invalid decimals, float rejection, negative quantities, percentage bounds, and missing/invalid density
- PR5 tests for Decimal utilities, units, measurement validation, density conversion, missing-density warnings, whole-number count validation, fractional-count rejection, and no business tables
- PR6 `ingredients` migration with no stock, lot, recipe, client, order, production, import, packaging, or purchase tables
- PR6 backend ingredient domain category/unit/name/density validation using existing Decimal/Density primitives with missing density allowed
- PR6 repository/service/API foundation for create, read, list active, full PUT update, and deactivate ingredients, plus minimal ingredient audit events
- PR6 tests/smoke coverage for migration scope, infrastructure continuity, valid/invalid ingredient inputs, missing/non-positive/float density, active listing, deactivation, and API behavior where dependencies are available

## In progress
- none

## Blocked
- none

## Next
- Continue with the next roadmap-scoped task after PR6 review/merge. Stock lots, stock movements, recipes, clients, orders, production, imports, and frontend UI remain out of scope until explicitly requested.

## Important notes
- PR4 intentionally keeps backup-before-migration tied to explicit user-mode startup; development mode behavior remains simple/test-friendly.
- PR3 intentionally does not change normal development database behavior: default development SQLite path remains repository-root `.local/cosmetic_workshop.sqlite` and `COSMETIC_WORKSHOP_DB_PATH` still works.
- User-mode data paths are resolved separately and default to `~/Documents/Мастерская косметолога/`, but directories/database are created only by explicit helper/startup calls.
- Startup modes are runtime-validated; only `development` and `user` are accepted.
- Read/status GET endpoints do not apply migrations or create user data directories implicitly.
- Tests and smoke use temporary directories and should not write real user data.
- Dependency installation and backend tests may fail in environments where Python package registry access is blocked; rerun after installing backend dependencies from an available registry/cache.

- PR5 intentionally adds no migrations, routes, frontend code, or business entities. Follow-up fixed count quantities so fractional pieces/items fail validation instead of rounding silently.
- PR6 intentionally adds only the `ingredients` business table and no inventory behavior; ingredient deactivation is used instead of hard delete. Ingredient full update uses `PUT /api/ingredients/{id}`; no partial PATCH contract is exposed.
