# Handoff

## Last completed work
Implemented PR10 stock movements foundation. The backend now has a `stock_movements` migration, immutable movement domain validation, repository/service/API operations for create/read/list/list-by-lot/balance, negative-balance prevention, and a minimal `stock_movement.created` audit event. Current lot quantity is derived from movement history and no `remaining_quantity` or stored balance was added to ingredient lots.

Previously implemented PR9 ingredient lots foundation. The backend now has an `ingredient_lots` migration, lot domain validation, repository/service/API operations for create/read/list/update/deactivate, and minimal audit events for lot creation, update, and deactivation. Lots belong to existing active ingredients and carry batch metadata such as lot code, supplier, purchase/expiration dates, unit, optional Decimal-backed costs, optional density, and notes.

Previously implemented PR8 first-run onboarding skeleton. The backend stores onboarding state as typed JSON in the existing `app_settings` table, exposes thin `/api/onboarding` endpoints, and records minimal audit events for starting, completing a step, and completing onboarding or skipping/closing the checklist. The frontend Dashboard shows a warm Russian welcome/checklist experience and graceful backend-unavailable fallback.

## Current repo state
Minimal local-first foundation exists. Backend exposes stable health payloads, technical database/settings endpoints, ingredients endpoints, ingredient lot endpoints, stock movement endpoints, and onboarding endpoints. Frontend remains a branded static shell with onboarding and placeholder empty states only. No real recipe/client/order/stock movement/production/import/export/backup UI flows were implemented.

## Important decisions
- Repo: `cosmetic-workshop-os`
- Product: `Мастерская косметолога`
- MVP remains local-first and API-first.
- SQLite is used for the persistence foundation.
- Ingredient lots remain batch metadata; stock accounting is now represented by immutable stock movements connected to lots.
- PR10 does not add `remaining_quantity`, materialized balances, FEFO allocation, production write-off, recipes, orders, packaging inventory, packaging movements, or frontend inventory UI.
- Lot creation/update requires an existing active ingredient. Missing ingredients return not found at API level; inactive ingredients return conflict.
- Lot density is optional and never assumed. Costs and density reject floats and are stored as Decimal strings.
- Existing database/startup decisions from PR2-PR4 remain unchanged.
- Existing launcher decisions from PR7 remain unchanged.

## Known issues
- In this Codex environment, full FastAPI/Starlette `TestClient` test runs can be blocked if backend test dependencies are not installed. Attempting `python3 -m pip install -e 'backend[test]'` was blocked by registry/proxy 403 while fetching build dependencies.
- Frontend onboarding fetches `/api/onboarding`; if the frontend is served separately without the backend proxy/runtime, it intentionally falls back to a non-technical unavailable state.

## Next recommended task
Proceed to the next roadmap-scoped task after PR10 review/merge. Do not add FEFO allocation, automatic production write-off, packaging inventory/movements, recipes, clients, orders, production, imports, exports, backup UI, restore UI, cloud, mobile, OCR, auth or roles until explicitly scoped by the next task.

## Commands to rerun during handoff
- `git status --short`
- `git branch --show-current`
- `python3 -m py_compile $(find backend/app launcher -name '*.py')`
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
- Existing FastAPI TestClient tests may be blocked unless `httpx2` is available in the environment.
