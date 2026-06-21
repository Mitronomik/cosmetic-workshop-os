# Progress

## Current phase
PR9 - Ingredient lots foundation

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

## In progress
- PR9 validation, smoke, commit, and PR creation

## Blocked
- Full pytest-based checks are blocked in this environment until the Starlette `httpx2` test dependency can be installed; registry access returned 403 during dependency installation.

## Next
- Continue with the next roadmap-scoped task after PR9 review/merge. Stock movements, remaining balances, FEFO allocation, packaging, recipes, clients, orders, production, imports, exports, backup UI/restore, final packaging, Electron, Docker, cloud, mobile, OCR, auth and roles remain out of scope until explicitly requested.

## Important notes
- PR9 intentionally does not add `remaining_quantity`, stock movement tables, production write-off logic, FEFO allocation, or frontend inventory UI.
- Ingredient lot `unit` is restricted to grams, milliliters, or pieces; percent is rejected as a lot stock unit.
- Lot creation/update rejects missing and inactive ingredients; inactive lots are hidden from active list endpoints.
- Missing lot density is accepted and no density fallback is assumed.
- Costs and density are Decimal-backed and stored as strings in SQLite.
- Tests and smoke use temporary directories/databases and should not write real user data.
