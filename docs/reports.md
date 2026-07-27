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

### Tax snapshots — decided, not implemented

`CR-007` decided the workshop tax-rate contract (`docs/settings.md`) and its implementation `C1-I` is **merged and `DONE`** (PR #149, merge commit `ff7afe6b0778ab2b348229a4df34acf3e3fc0001`). `CR-008` then decided the C2 calculation and snapshot contract (`docs/decisions/0012-c2-financial-calculation-snapshots.md`).

Neither changes reports now. On merged `main`, no `ProductionBatch` rate snapshot column exists, no tax or margin is calculated anywhere, and reports still contain **no tax calculation**. Report changes belong to `C2-III`, which is `PLANNED — BLOCKED`.

The durable **report snapshot-only rule**, binding once `C2-II` persists snapshots and `C2-III` reads them:

- reports read the immutable `ProductionBatch` financial snapshots **only**;
- reports never recalculate historical tax or margin using the currently configured rate;
- changing or clearing the tax setting never changes an existing report value;
- a production batch without tax snapshots shows unavailable / `Недоступно` and is **never** shown as a fabricated `0.00`;
- the current rate is never applied retroactively to a historical row;
- an explicitly configured `0%` rate is a real value and is **not** the same as an unconfigured rate — configured zero and missing must remain visually and semantically distinct;
- only existing report read models that already contain cost, revenue, tax, margin, or margin percent are updated;
- no advanced analytics, tax declaration, accounting report, tax-regime reporting, or annual/quarterly filing calculation is added.

### C2-III — blocked, and possibly to be subdivided

Status: **PLANNED — BLOCKED** on merged and verified `C2-II`.

`C2-III` is a **planning umbrella, not authorization for one large implementation PR**. Before it is authorized, repository evidence must determine whether it can remain one bounded, independently reviewable vertical slice. If it cannot, it must be divided before implementation — for example into readiness and `ProductionBatch` financial presentation, and separately snapshot-backed reports. Readiness UI, batch UI, and report backend plus frontend must not be combined into one catch-all PR merely because they share the word "financial". No future implementation PR number is assigned.

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

The frontend Reports UI is available at `/reports` and consumes these backend endpoints. The UI must keep calculations in the backend and display backend-provided warnings instead of recalculating core report values in the frontend.


## Report document export foundation

PR89/PR90 add an explicit document-export path for reports, and PR92 adds PDF generation foundation. The first document type is “Сводка мастерской” (`workshop_overview`) generated as Markdown or PDF from the existing overview report DTO. Creation is an explicit POST-only operation under `/api/report-documents`; opening `/reports` or using its contextual link to `/report-documents` does not create files. DOCX remains future work. See `docs/report-documents.md` for storage, safety, and metadata details.
