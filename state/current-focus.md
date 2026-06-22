# Current Focus

## PR18 — Recipe version calculation service

PR18 adds a backend-only, read-only recipe version calculation service.

Implemented scope:
- load a recipe version with its template name and ingredient rows in deterministic position/id order;
- calculate fixed `g`, `ml`, and `pcs` lines without proportional scaling;
- calculate percent lines from an explicit `g`/`ml` target batch size or from the version's stored `g`/`ml` target batch size;
- report Decimal-backed `percent_total` and human-readable issues for missing, unsupported `pcs`, or below/above 100% percent totals;
- expose `GET /api/recipe-versions/{version_id}/calculation` with optional `target_batch_size_value` and `target_batch_size_unit` query parameters.

Intentional non-scope:
- no migrations, tables, stored calculation results, cost/tax/margin calculation, stock readiness, production, client recipes, orders, import/export, or frontend UI.

## PR19 current focus
- Added the first recipe UI foundation at `/recipes` with Russian labels for recipe templates, recipe versions, ingredient lines, version detail, and backend-driven calculation display.
- The frontend uses existing recipe template/version endpoints and the PR18 calculation endpoint; recipe amounts are not calculated in the browser.
- Historical recipe versions remain view-only in this PR: no edit/delete/status mutation UI was added.
- No client recipes, clients, orders, production, stock readiness, cost/tax/margin, migrations, or new tables were added.
