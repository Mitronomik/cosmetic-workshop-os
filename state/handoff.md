# Handoff

## Last completed work

PR84 — Demo data mode backend foundation.

## Current repo state after PR84

- Demo tracking tables `demo_data_sessions` and `demo_data_records` were added by migration `0018_demo_data_tracking`.
- Backend API endpoints were added under `/api/demo-data`:
  - `GET /api/demo-data/status`;
  - `POST /api/demo-data/install`;
  - `POST /api/demo-data/clear`.
- Demo install is explicit, transactional, labels records with `Демо ·`, and is blocked when non-demo business rows exist.
- Demo clear is explicit, transactional, deletes only tracked demo rows, and blocks when untracked working records reference demo rows.
- Demo install does not create production batches, backups, exports, import apply target expansion, frontend UI, startup seed data, migration seed data, or onboarding seed data.

## Manual smoke

Manual browser/API smoke was not run with a long-running local server in this non-interactive session. Automated service tests were run; FastAPI TestClient API tests are skipped when `httpx` is unavailable in the environment.

Recommended manual API smoke for PR85 or local review:
1. Start backend with a temporary empty DB.
2. Call `GET /api/demo-data/status` and confirm `can_install=true`.
3. Call `POST /api/demo-data/install` without confirmation and confirm rejection.
4. Call `POST /api/demo-data/install` with both confirmation flags.
5. Confirm created counts and `Демо ·` labels in ingredient, packaging, recipe, client, and order APIs.
6. Confirm no production batches, backup files, or export files were created automatically.
7. Call `POST /api/demo-data/clear` without confirmation and confirm rejection.
8. Call clear with confirmation and confirm tracked records are removed.
9. Create a real business record in a temp DB and confirm install is blocked.
10. Create a real order referencing demo records and confirm clear is blocked.

## Next recommended PR

PR85 — Demo data mode UI.
