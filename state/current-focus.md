# Current focus

## Goal

A4.1 — Shared responsive table containment foundation for `/ingredient-lots`. Keep the Ingredient Lots page usable at desktop, tablet, and narrow viewports without document-level horizontal overflow; wide table content must stay inside a local horizontal scroll area.

## Baseline

Slice A3 is complete. PR #124 / A3.9 Production Confirmation structured errors and mutation safety is the completed A3 implementation baseline based on the product owner's confirmed tests and smoke verification. This is external evidence, not GitHub Actions evidence.

## Allowed scope/files

- Frontend CSS containment contract for shared table wrappers, shrinkable content columns/cards, safe local horizontal scrolling, and visible focus outlines.
- Minimal `/ingredient-lots` markup only if CSS alone cannot preserve accessible table identity/status/actions.
- Focused frontend checks, focused Ingredient Lot backend regression tests, and exact-head browser smoke with isolated SQLite/browser profile.
- Directly affected project-state documentation.

## Non-goals

- No `/orders`, `/clients`, `/inventory`, or `/packaging-items` route implementation changes in A4.1. They remain separate A4 follow-ups.
- No backend API, schema, migration, domain rule, stock calculation, validation lifecycle, dependency, framework, cloud/sync/auth/OCR/analytics, or broad `frontend/src/main.ts` refactor.
- No global `overflow-x: hidden` on `html`, `body`, or the application shell to hide layout defects.

## Required evidence

Record before/after overflow metrics for `/ingredient-lots` at 1440×900, 1024×768, 768×900, and 390×844, including `documentElement`/`body` client and scroll widths plus local table wrapper client/scroll widths. Verify mouse and keyboard reach row actions, focus outlines are visible, create/edit/structured-validation/deactivate behavior remains unchanged, and `/inventory` plus `/packaging-items` have no obvious shared-CSS regressions.
