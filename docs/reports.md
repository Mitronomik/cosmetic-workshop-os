# Reports backend foundation

PR87 adds read-only backend reports for the local-first workshop app.

## Scope

Reports help the user understand the current operational state of the workshop:

- inventory health;
- order pipeline;
- production history;
- alerts and purchase workload;
- a basic financial snapshot.

This is not advanced analytics and not an accounting module.

## Safety rules

- Reports are read-only.
- Report endpoints do not mutate business records.
- Report endpoints do not create audit logs.
- Report endpoints do not create backup or export files.
- Report endpoints do not regenerate alerts or purchase suggestions.
- Report endpoints do not create report persistence tables.
- Reports work from existing SQLite data and remain offline/local-first.

## Finance report limits

The finance report is an operational snapshot, not accounting or tax filing.

- `known_revenue` is the sum of all known sale prices.
- `known_production_cost` is the sum of all known production costs.
- `known_margin` is calculated only from production batches where both `sale_price` and `total_cost` are known on the same row.
- `known_margin_percent` uses the same complete paired basis as `known_margin`, not the global known revenue total.
- `complete_finance_record_count` is the count of production batches used for margin.
- `incomplete_margin_count` is the count of production batches excluded from margin because sale price or cost is missing.
- Tax is not invented or recalculated by reports.
- Missing sale prices or costs are surfaced as warnings.

## Incomplete data

When data is missing or ambiguous, reports return warnings instead of silently inventing values. Examples:

- `missing_sale_price` — some produced orders do not have sale price.
- `missing_production_cost` — some production batches do not have total cost.
- `mixed_units` — produced quantities are shown by unit because grams, milliliters, and pieces cannot be safely summed together.
- `no_production_data` — no production batches exist yet.
- `margin_unavailable` — no production batch has both sale price and cost, so margin is not returned.
- `partial_margin_basis` — margin is returned, but only for complete finance rows.

## Endpoints

All endpoints are `GET` and are mounted under `/api/reports`:

- `/api/reports/overview`
- `/api/reports/inventory`
- `/api/reports/orders`
- `/api/reports/production`
- `/api/reports/finance`

Each response includes:

- `generated_at`;
- explicit summary fields;
- `warnings`.

## Date filters

PR87 intentionally keeps reports all-time. Date filters are not implemented in this PR to keep the backend foundation small and safe.

## Future UI

The frontend Reports UI is planned for a follow-up PR. The UI should consume these backend endpoints and keep calculations in the backend.


## Report document export foundation

PR89 adds a backend document-export foundation for reports. The first document type is “Сводка мастерской” (`workshop_overview`) generated as Markdown from the existing overview report DTO. This is an explicit POST-only operation under `/api/report-documents`; opening `/reports` does not create files. PDF and DOCX remain future work. See `docs/report-documents.md` for storage, safety, and metadata details.
