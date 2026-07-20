# Current focus

Slice A4 is active.

## Active task

**A4.4b — Contain responsive Packaging Items workspace**

Goal: contain the complete `/packaging-items` working workspace inside the application content area at `1440×900`, `1024×768`, `768×900`, and `390×844` without document-level horizontal overflow, while keeping the seven-column Packaging Items table usable through local horizontal scrolling.

Allowed files for this focused PR are `frontend/src/main.ts`, `frontend/src/styles.css`, `README.md`, `docs/implementation-plan.md`, `state/current-focus.md`, `state/progress.md`, and `state/handoff.md` unless evidence proves another directly related file is required.

Non-goals: no backend, API, schema, migration, inventory balance, stock movement, order, production, mutation lifecycle, targeted validation, catalog semantics, `/ingredients` behavior, cloud, OCR, roles, analytics, or final cross-route A4 regression changes.

Required checks: frontend form-validation tests, targeted-validation-update tests, frontend build, focused Packaging/Catalog/Inventory backend tests, exact-base full backend suite, exact-head full backend suite, repository hygiene, and exact published-head browser smoke.

Browser smoke must use an isolated SQLite database and browser profile, cover loaded long-content Packaging data, active filters, create and edit forms, classification and create controls, structured validation presentation, first/final table columns, keyboard focus, passive mutation safety, and passive `/ingredients` regression at all required viewports.

Next step after A4.4b merge: run the separate final cross-route A4 responsive regression before marking Slice A4 complete.
