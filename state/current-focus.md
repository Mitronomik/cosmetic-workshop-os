# Current Focus

## PR18 — Recipe version calculation service

PR18 adds a backend-only, read-only recipe version calculation service.

Implemented scope:
- load a recipe version with its template name and ingredient rows in deterministic position/id order;
- calculate fixed `g`, `ml`, and `pcs` lines without proportional scaling;
- calculate percent lines from an explicit target batch size or from the version's stored target batch size;
- report Decimal-backed `percent_total` and human-readable issues for missing target size or percent totals below/above 100%;
- expose `GET /api/recipe-versions/{version_id}/calculation` with optional `target_batch_size_value` and `target_batch_size_unit` query parameters.

Intentional non-scope:
- no migrations, tables, stored calculation results, cost/tax/margin calculation, stock readiness, production, client recipes, orders, import/export, or frontend UI.
