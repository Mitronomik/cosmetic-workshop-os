# Handoff

## Last completed work

PR86 — In-app help center foundation.

## Current repo state after PR86

- `/help` is a real frontend route.
- “Помощь” is marked ready in “Данные и настройки” and opens `/help`.
- Help Center is static frontend content bundled in `frontend/src/main.ts`; it works offline and does not require backend data.
- Help includes Russian, user-facing articles for:
  - first steps;
  - components, lots, stock movements, packaging;
  - recipes and versions;
  - individual client recipes;
  - clients, wishes, feedback;
  - orders, readiness, production/write-off;
  - alerts and purchase suggestions;
  - backup/export;
  - import;
  - demo data.
- Help has frontend-only search, category filtering, article cards, selected article detail, and related-section buttons.
- Related-section buttons only navigate; Help does not install/clear demo data, create imports, apply imports, create backup/export, or mutate business data.
- Dashboard now has a compact Help link card that only opens Help.
- No backend help API, migrations, database tables, CMS, AI/RAG, external docs, internet dependency, import target expansion, reports/settings/audit/package work, or demo data behavior changes were added.

## Automated checks from PR86

- `git status --short` showed only PR86 working-tree changes before commit.
- `git branch --show-current` returned `work`.
- `npm --prefix frontend run build` passed.
- `git diff --check` passed.
- `python3 -m py_compile $(find backend/app launcher -name '*.py')` passed.
- `python3 -m pytest backend/app/tests/test_onboarding.py -q` passed: 10 passed, 1 skipped.
- `python3 -m pytest backend/app/tests/test_demo_data.py -q` passed: 20 passed.
- `python3 -m pytest backend/app/tests/test_import_parsing.py -q` passed: 16 passed.
- `python3 -m pytest backend/app/tests/test_imports_api.py -q` passed: 2 passed, 5 skipped.
- `python3 -m pytest backend/app/tests/test_import_apply.py -q` passed: 11 passed, 1 skipped.
- `python3 -m pytest backend/app/tests/test_exports_api.py -q` passed: 5 passed, 6 skipped.
- `python3 -m pytest backend/app/tests/test_backups_api.py -q` passed: 4 passed, 5 skipped.
- `python3 -m pytest backend/app/tests/test_orders.py -q` passed: 6 passed, 1 skipped.
- `python3 -m pytest backend/app/tests/test_production_readiness.py -q` passed: 8 passed, 1 skipped.
- `python3 -m pytest backend/app/tests/test_production_confirmation.py -q` passed: 10 passed, 1 skipped.
- `python3 -m pytest backend/app/tests/test_purchase_suggestions.py -q` passed: 9 passed, 2 skipped.
- `python3 -m pytest backend/app/tests/test_alerts.py -q` passed: 10 passed, 1 skipped.
- API-test skips are existing optional FastAPI/TestClient dependency skips in this environment.

## Manual smoke

Manual browser smoke was not run yet in this non-interactive session because no long-running backend/frontend browser session was started.

Recommended local smoke:
1. Start backend and frontend.
2. Open `/help`.
3. Confirm Help route loads.
4. Confirm “Помощь” navigation opens `/help`.
5. Confirm categories are visible.
6. Open “Как начать работу”.
7. Search `рецепт`, `backup`, and `импорт` and confirm matching articles.
8. Open “Демо-данные”.
9. Confirm related section buttons navigate only.
10. Confirm no install/clear/import/backup/export action is triggered from Help.
11. Confirm dashboard, onboarding, demo data, and import pages still load.

## Next recommended PR

PR87 — Help center contextual polish / smoke fixes if smoke finds issues; otherwise PR87 — Reports foundation.


## PR87 — Reports backend foundation
- Added read-only backend reports service, schemas, and `/api/reports` endpoints for overview, inventory, orders, production, and finance.
- Reports aggregate existing SQLite data only and do not create audit logs, backups, exports, alerts, purchase suggestions, or report tables.
- Finance values use Decimal-backed string totals and do not invent tax. Missing sale price/cost and mixed production units are surfaced as warnings.
- Added backend report service/API tests and docs.
- Next recommended PR: PR88 — Reports UI foundation, unless report API smoke finds backend follow-up fixes.

## PR87 manual smoke note

Manual long-running backend smoke was not run in this non-interactive session. Automated API coverage used FastAPI TestClient where available and verified all `/api/reports/*` endpoints return `generated_at`/`warnings` and keep table row counts unchanged. Recommended next local smoke for PR88: start backend, call reports on an empty database, install demo data, call reports again, and confirm no backup/export files or alert/purchase regeneration occurred.


## PR87 follow-up — finance margin basis safety
- Fixed finance report margin basis: `known_margin` and `known_margin_percent` now use only production batches where both `sale_price` and `total_cost` are known on the same row.
- `known_revenue` and `known_production_cost` remain independent known totals, but reports no longer combine revenue from one incomplete batch with cost from another unrelated incomplete batch to produce margin.
- Added `complete_finance_record_count`, `incomplete_margin_count`, `margin_unavailable`, and `partial_margin_basis` coverage/docs.
- Manual long-running API smoke was not run in this non-interactive session; automated service/API tests cover the finance mismatch regression and read-only endpoints.
