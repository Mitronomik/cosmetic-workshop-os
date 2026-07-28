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

Neither changes reports now. On merged `main` the two `ProductionBatch` rate snapshot columns exist, production confirmation persists tax, margin, and margin percent (`C2-I` / PR #151 and `C2-II` / PR #152), and the Order and `ProductionBatch` financial presentation is merged (`C2-III-A` / PR #154) — but reports still read no snapshots and still contain **no tax calculation**. Report changes belong to `C2-III-B`, which is `AUTHORIZED AFTER THIS PR MERGES — NOT IMPLEMENTED`.

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

### C2-III-B — snapshot-backed reports and report documents: authorized, not implemented

Status: **AUTHORIZED AFTER THIS PR MERGES — NOT IMPLEMENTED.**

`C2-III` was a planning umbrella and has been subdivided into exactly two runtime slices. `C2-III-A — Order and ProductionBatch financial presentation` covered Orders readiness and `ProductionBatch` UI, **excluded reports entirely**, and is **merged and `DONE`** (PR #154, merge commit `d432fcaee52a16a4f8b609ec160cf3fa2b33d013`, merged `2026-07-28T13:05:34Z`). `C2-III-B` is the report slice and the only remaining C2 runtime slice. It is **not implemented**, and no future implementation PR number is assigned to it.

Authorized `C2-III-B` boundary — one bounded backend-plus-frontend report vertical:

```text
persisted ProductionBatch financial snapshots
→ backend report aggregation
→ report DTOs
→ /reports presentation
→ overview report consumers
→ generated «Сводка мастерской»
```

The affected financial reports read persisted `ProductionBatch` financial snapshots; report tax comes only from persisted `ProductionBatch.tax` and report margin only from persisted `ProductionBatch.margin`; historical rate changes never modify existing report results; the current Settings tax rate is never applied retroactively; report calculations remain backend-owned; report endpoints remain read-only; and report reads create no audit records and no business mutations. Old batches with null snapshots remain incomplete or unavailable; `null` is never fabricated as `0`, `"0.00"`, `0 ₽`, or `0%`; a configured zero tax remains a real known value; a negative margin and a negative margin percentage remain valid signed information; and batches with incomplete financial snapshots contribute to explicit incomplete-data counters or warnings rather than silently appearing complete. The `/reports` backend DTO and the frontend presentation are updated together, the frontend stays display-only and calculates no report tax, margin, margin percentage, incomplete-data coverage, or historical value; the overview finance summary becomes snapshot-backed where directly affected; the document `Сводка мастерской` stays synchronized with the report DTO it consumes, newly generated documents may reflect the snapshot-backed result, previously generated documents remain immutable, and document generation remains an explicit user action. Orders readiness, Order production confirmation, the Order lifecycle, `ProductionBatch` persistence, `ProductionBatch` list and detail presentation, the `C2-III-A` presentation modules, tax-rate Settings behavior, migrations, historical `ProductionBatch` rows, and stock or production transactions are **not** changed in this slice.

**No new aggregate margin-percent formula is defined.** The accepted aggregate basis remains the `known_margin_percent` rule stated above — the same complete paired sale-price/cost basis as `known_margin`, not the global known-revenue total. That contract is preserved unchanged by this authorization. An arithmetic average of batch percentages, a weighted average of batch percentages, aggregate margin divided by aggregate revenue, and recalculation from current settings must not be chosen silently without an explicit later contract. The `C2-III-B` implementation task must inspect the current report queries, the paired revenue/cost behavior, the incomplete-data counters and warnings, the finance and overview report schemas, the frontend `/reports`, report-document generation, and the existing tests and smoke boundaries **before** modifying the implementation. If runtime evidence reveals a contradiction between the documented paired basis and the code required for snapshot-backed aggregation, that task must **stop and report the exact conflict** instead of inventing a formula.

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
