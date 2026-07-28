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

Neither changes reports now. On merged `main` the two `ProductionBatch` rate snapshot columns exist and production confirmation persists tax, margin, and margin percent (`C2-I` / PR #151 and `C2-II` / PR #152), but reports still read no snapshots and still contain **no tax calculation**. Report changes belong to `C2-III-B`, which is `PLANNED — BLOCKED`.

The durable **report snapshot-only rule**, binding now that `C2-II` persists snapshots and once `C2-III-B` reads them:

- reports read the immutable `ProductionBatch` financial snapshots **only**;
- reports never recalculate historical tax or margin using the currently configured rate;
- changing or clearing the tax setting never changes an existing report value;
- a production batch without tax snapshots shows unavailable / `Недоступно` and is **never** shown as a fabricated `0.00`;
- the current rate is never applied retroactively to a historical row;
- an explicitly configured `0%` rate is a real value and is **not** the same as an unconfigured rate — configured zero and missing must remain visually and semantically distinct;
- a batch produced while there was **no valid configured tax-rate context** — a missing setting row **or** an invalid persisted value — carries null rate snapshots and null tax, margin, and margin percent, and reports show those as unavailable; a raw invalid setting value is never stored on a batch and therefore never appears in a report;
- only existing report read models that already contain cost, revenue, tax, margin, or margin percent are updated;
- no advanced analytics, tax declaration, accounting report, tax-regime reporting, or annual/quarterly filing calculation is added.

### C2-III-B — snapshot-backed reports and report documents: blocked

Status: **PLANNED — BLOCKED** on merged and verified `C2-III-A`.

`C2-III` was a planning umbrella and has been subdivided into exactly two runtime slices. `C2-III-A — Order and ProductionBatch financial presentation` covers Orders readiness and `ProductionBatch` UI and **excludes reports entirely**. `C2-III-B` is the report slice, it is **not authorized yet**, and no future implementation PR number is assigned to it.

Planned `C2-III-B` boundary: the finance report reads persisted `ProductionBatch` snapshots; report tax comes only from persisted `ProductionBatch.tax` and report margin only from persisted `ProductionBatch.margin`; historical values are never recalculated using the current tax setting; old batches with null snapshots remain incomplete or unavailable; null is never fabricated as `"0.00"`; a configured zero tax remains a real known value; the `/reports` backend DTO and the frontend presentation are updated together; the overview finance summary becomes snapshot-backed where directly affected; the document `Сводка мастерской` stays synchronized with the report DTO it consumes; and Orders readiness and `ProductionBatch` UI are **not** changed in this slice.

**No new aggregate margin-percent formula is defined.** The accepted aggregate basis remains the `known_margin_percent` rule stated above — the same complete paired sale-price/cost basis as `known_margin`, not the global known-revenue total. An arithmetic average of batch percentages, a weighted average of batch percentages, aggregate margin divided by aggregate revenue, and recalculation from current settings must not be chosen silently without an explicit later contract. Before `C2-III-B` is authorized, the implementation-planning task must inspect the current report queries, the paired revenue/cost behavior, the incomplete-data counters and warnings, the finance and overview report schemas, the frontend `/reports`, report-document generation, and the existing tests and smoke boundaries.

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
