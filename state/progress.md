# Progress

## Current phase
PR3 - User data directory and explicit startup initialization implemented

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
- PR3 tests/smoke coverage for development fallback, env overrides, directory creation, explicit startup initialization, no hidden endpoint migrations, and no business tables

## In progress
- none

## Blocked
- none

## Next
- Continue with the next roadmap-scoped foundation task after PR3 review/merge. Do not add business tables or business CRUD until explicitly scoped.

## Important notes
- PR3 intentionally does not change normal development database behavior: default development SQLite path remains repository-root `.local/cosmetic_workshop.sqlite` and `COSMETIC_WORKSHOP_DB_PATH` still works.
- User-mode data paths are resolved separately and default to `~/Documents/Мастерская косметолога/`, but directories/database are created only by explicit helper/startup calls.
- Read/status GET endpoints do not apply migrations or create user data directories implicitly.
- Tests and smoke use temporary directories and should not write real user data.
- Dependency installation and backend tests may fail in environments where Python package registry access is blocked; rerun after installing backend dependencies from an available registry/cache.
