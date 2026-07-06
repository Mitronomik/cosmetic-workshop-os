# Handoff

## Last completed work

PR85 — Demo data mode UI.

## Current repo state after PR85

- Frontend route `/demo-data` is available through “Данные и настройки” → “Демо-данные”.
- The page consumes PR84 backend endpoints:
  - `GET /api/demo-data/status`;
  - `POST /api/demo-data/install`;
  - `POST /api/demo-data/clear`.
- Demo install requires explicit user confirmation with two checkboxes and calls only the backend install endpoint.
- Demo clear requires explicit user confirmation with one checkbox and calls only the backend clear endpoint.
- Backend remains the source of truth for `can_install`, `can_clear`, and blocking reasons.
- The UI does not install demo data automatically, clear demo data automatically, create/delete business records directly, create backup/export automatically, expand import apply targets, create production batches, or alter the demo dataset.
- Dashboard has only a compact link card to `/demo-data`.

## Automated checks from PR85

- `git status --short` showed only PR85 working-tree changes before commit.
- `git branch --show-current` returned `work`.
- `npm --prefix frontend run build` passed.
- `git diff --check` passed.
- `python3 -m py_compile $(find backend/app launcher -name '*.py')` passed.
- `python3 -m pytest backend/app/tests/test_demo_data.py -q` passed.
- `python3 -m pytest backend/app/tests/test_demo_data_api.py -q` skipped because FastAPI TestClient requires `httpx` in this environment.
- Regression pytest commands requested in PR85 passed; several suites include environment-gated skips for TestClient-dependent cases.

## Manual smoke

Manual browser smoke was not run in this non-interactive session because no long-running backend/frontend browser session was started.

Recommended local smoke:
1. Start backend and frontend with an empty temp/dev database.
2. Open `/demo-data` and confirm status loads.
3. Confirm install requires both checkboxes.
4. Install demo data and verify success message plus counts.
5. Navigate to Components, Inventory, Recipes, Clients, Orders, Alerts, and Purchases to verify `Демо ·` records.
6. Return to `/demo-data`, confirm clear requires checkbox, clear demo data, and verify records disappear.
7. In a fresh temp DB with one real record, confirm install is blocked.
8. Confirm no backup/export files are created automatically and dashboard link opens `/demo-data`.

## Next recommended PR

O5 — In-app help center.

If demo smoke finds issues: PR86 — Demo data UI follow-up fixes.
