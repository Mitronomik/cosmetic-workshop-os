# Handoff

## Last completed work
Implemented PR8 first-run onboarding skeleton. The backend stores onboarding state as typed JSON in the existing `app_settings` table, exposes thin `/api/onboarding` endpoints, and records minimal audit events for starting, completing a step, and completing onboarding or skipping/closing the checklist. The frontend Dashboard now shows a warm Russian welcome/checklist experience, explains that data is local to the computer, and renders a graceful fallback if the backend is unavailable.

Previously implemented PR7 local runtime launcher MVP foundation with localhost-only defaults, explicit user-mode startup initialization, backend process launch support, optional browser opening, and clear startup/port-conflict messages.

## Current repo state
Minimal local-first foundation exists. Backend exposes stable health payloads, technical database/settings endpoints, ingredients endpoints, and onboarding endpoints. Frontend remains a branded static shell with onboarding and placeholder empty states only. No real recipe/client/order/stock/production/import/export/backup UI flows were implemented.

## Important decisions
- Repo: `cosmetic-workshop-os`
- Product: `Мастерская косметолога`
- MVP remains local-first and API-first.
- SQLite is used for the persistence foundation.
- Onboarding state is stored under `app_settings.key = 'onboarding.state'` with `value_type = 'json'` to avoid adding a table for this small infrastructure state.
- PR8 does not add an `onboarding_state` table and does not add forbidden future business tables.
- Onboarding checklist steps are placeholders only and do not create business records. `skip()` closes onboarding without marking uncompleted steps as complete; `complete()` remains the explicit complete-all path.
- Existing database/startup decisions from PR2-PR4 remain unchanged.
- Existing launcher decisions from PR7 remain unchanged.

## Known issues
- If Python dependencies are missing in the environment, backend tests that import FastAPI may fail until dependencies are installed from an available registry/cache.
- Frontend onboarding fetches `/api/onboarding`; if the frontend is served separately without the backend proxy/runtime, it intentionally falls back to a non-technical unavailable state.

## Next recommended task
Proceed to the next roadmap-scoped task after PR8 review/merge. Do not add IngredientLot, StockMovement, packaging, recipes, clients, orders, production, imports, exports, backup UI, restore UI, cloud, mobile, OCR, auth or roles until explicitly scoped by the next task.

## Commands to rerun during handoff
- `git status --short`
- `git branch --show-current`
- `python3 -m py_compile $(find backend/app launcher -name '*.py')`
- `cd backend && python3 -m pytest app/tests/test_onboarding.py`
- `cd backend && python3 -m pytest`
- `cd frontend && npm run build`
- `make test`
- `make build`
- `git diff --name-only`

## PR8 notes
- Onboarding endpoints:
  - `GET /api/onboarding`
  - `POST /api/onboarding/start`
  - `POST /api/onboarding/complete-step`
  - `POST /api/onboarding/complete`
  - `POST /api/onboarding/skip`
  - `POST /api/onboarding/reset`
- Smoke should use a temporary database/user data directory and verify onboarding read/start/step-complete/skip/complete plus absence of forbidden future business tables.
