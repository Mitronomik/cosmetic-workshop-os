# Progress

## Slice A1 — User-facing technical copy cleanup

Current branch implements Slice A1.

Completed source changes:
- Removed the persistent healthy-state `Локальный API доступен` topbar indicator; only an unavailable state can render a recovery badge.
- Reworded targeted failed-load and recovery copy to Russian product language without API/backend wording.
- Updated Import page copy to describe the implemented draft → validation → confirmation → Apply workflow.
- Preserved Import Apply mutation/refresh separation and structured conflict rendering while changing only copy.
- Added centralized `/demo-data` counter label mapping/fallback so visible counters do not expose raw snake_case keys.
- Corrected targeted stale route/capability copy for exports, report documents, reports, recipes, inventory, demo data, and help text where functionality already exists.

Files changed:
- `frontend/src/main.ts`
- `docs/implementation-plan.md`
- `state/current-focus.md`
- `state/progress.md`
- `state/handoff.md`

Checks completed:
- Targeted source search before edits: completed; runtime findings were in `frontend/src/main.ts`; documentation/state findings were mostly governance/history and not runtime UI.
- Targeted source search after edits: completed; remaining `backend`, `repository_name`, and snake_case matches in `frontend/src` are type fields, API response keys, helper maps, API client usage, or scoped instructions, not raw visible runtime copy. `/demo-data` fallback is `Другие данные`.
- `cd frontend && npm run build`: passed.
- Existing frontend tests: unavailable; `frontend/package.json` has no test script.
- `cd backend && python3 -m pytest`: failed with the same known backend-area pattern recorded before this slice: 5 failed, 463 passed. No backend files changed.
- `git diff --check`: passed.

Browser smoke:
- Environment: `/tmp/cwo-a1-smoke-MxPIsh`, isolated SQLite database `/tmp/cwo-a1-smoke-MxPIsh/smoke.sqlite`, isolated user-data `/tmp/cwo-a1-smoke-MxPIsh/user-data`, local backend on `127.0.0.1:8010`, frontend on `127.0.0.1:5173`, headless Chromium via Playwright.
- Completed partial source-level/browser smoke: healthy desktop and narrow demo/import/route truth checks, unavailable-service recovery check.
- Screenshots captured: `healthy-desktop.png`, `demo-narrow.png`, `imports-desktop.png`, `unavailable.png` under `/tmp/cwo-a1-smoke-MxPIsh/screens/`.
- Results observed: healthy page had no API/backend indicator; demo page showed no raw snake_case keys; Import intro copy described confirmation/apply; checked routes did not show targeted PR/repository/roadmap/backend language; unavailable Import state showed recovery copy with no API/backend/endpoint/localhost/HTTP wording.
- Limitations: full required Import mutation scenarios (normal Apply, refresh failure, structured conflict) were not rerun in browser in this local pass. Browser merge gate remains pending external Hermes or a complete deterministic local smoke.

Known limitations:
- Raw local file-path presentation is intentionally unchanged for Slice A5.
- Responsive table containment is intentionally unchanged for Slice A4.
- Structured validation migration is intentionally unchanged for Slices A2/A3.
