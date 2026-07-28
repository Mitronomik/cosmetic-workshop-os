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

> **CURRENT MERGED BEHAVIOUR — SUPERSEDED BY THE ACCEPTED `C2-III-B` CONTRACT BELOW.** The bullets in this subsection describe `ReportsService.get_finance_report()` exactly as implemented on merged `main` today, where margin is *derived* from paired `sale_price` and `total_cost`. `C2-III-B` replaces that derivation with persisted snapshots — see § *Accepted `C2-III-B` snapshot aggregation contract*. Until `C2-III-B` is implemented and merged, the behaviour below is what the API actually returns.

- `known_revenue` is the sum of all known sale prices.
- `known_production_cost` is the sum of all known production costs.
- `known_margin` is currently **derived** as paired revenue minus paired cost, over production batches where both `sale_price` and `total_cost` are known on the same row. `C2-III-B` replaces this with the sum of persisted `ProductionBatch.margin`.
- `known_margin_percent` currently uses that same paired basis, not the global known revenue total. `C2-III-B` restates the denominator explicitly; see the accepted formula below.
- `complete_finance_record_count` is the count of production batches where sale price and total cost are both known. It is **legacy paired-input coverage**, not persisted-margin-snapshot coverage.
- `incomplete_margin_count` is the count of production batches excluded because sale price or total cost is missing. It is **legacy paired-input coverage**, not persisted-margin-snapshot coverage.
- Tax is not invented or recalculated by reports.
- Missing sale prices or costs are surfaced as warnings.

### Tax snapshots — decided, not implemented

`CR-007` decided the workshop tax-rate contract (`docs/settings.md`) and its implementation `C1-I` is **merged and `DONE`** (PR #149, merge commit `ff7afe6b0778ab2b348229a4df34acf3e3fc0001`). `CR-008` then decided the C2 calculation and snapshot contract (`docs/decisions/0012-c2-financial-calculation-snapshots.md`).

Neither changes reports now. On merged `main` the two `ProductionBatch` rate snapshot columns exist, production confirmation persists tax, margin, and margin percent (`C2-I` / PR #151 and `C2-II` / PR #152), and the Order and `ProductionBatch` financial presentation is merged (`C2-III-A` / PR #154) — but reports still read no snapshots and still contain **no tax calculation**. Report changes belong to `C2-III-B`, which is `AUTHORIZED AFTER THIS PR MERGES — CONTRACT CLARIFIED — NOT IMPLEMENTED`.

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

Status: **AUTHORIZED AFTER THIS PR MERGES — CONTRACT CLARIFIED — NOT IMPLEMENTED.**

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

> **HISTORICAL — RESOLVED BY THE ACCEPTED CONTRACT BELOW.** PR #155 recorded that no new aggregate margin-percent formula was defined, that the accepted basis remained "the same complete paired sale-price/cost basis as `known_margin`", and that the `C2-III-B` implementation task must **stop and report the exact conflict** if runtime evidence revealed a contradiction between the documented paired basis and the code required for snapshot-backed aggregation. That instruction was followed. A read-only Phase 0 audit found exactly such a contradiction and stopped without creating a branch, an edit, a commit or a PR. The section below is the accepted resolution.

## Accepted `C2-III-B` snapshot aggregation contract

### The Phase 0 conflict this resolves

```text
C2-III-B — BLOCKED BY REPORT AGGREGATION CONTRACT CONFLICT
```

The current implementation derives margin from paired `sale_price` and `total_cost`, while the authorized `C2-III-B` contract requires reports to read persisted `ProductionBatch.tax` and `ProductionBatch.margin` snapshots **only**. Under the old implementation the paired sale/cost row set and the persisted-margin row set were the same set, so "the same basis as `known_margin`" was unambiguous. Under snapshot-backed aggregation they are **not** the same set: a batch may carry a known sale price and a known total cost while its `tax` and `margin` snapshots are `null` — which is the normal state of every pre-`C2-II` row, because there was no backfill. The paired phrase and the "same basis as `known_margin`" phrase therefore pointed at two different denominators, and the incomplete-data counters could no longer stay truthful under either reading. This section defines the single accepted answer.

### 1. Authoritative row sets

```text
R = all ProductionBatch rows

P = rows where both sale_price and total_cost are non-null

T = rows where persisted tax is non-null

M = rows where persisted margin is non-null
```

By the existing production financial invariant, `M` is normally a subset of the rows with a known sale price, a known total cost and a known persisted tax. Reports must **not** reconstruct membership in `T` or `M` by calculating tax or margin. Membership is determined solely from the persisted snapshot values.

`P` and `M` are **not** the same set and must never be treated as interchangeable.

### 2. Independent known totals

`known_revenue` and `known_production_cost` keep their current meanings — the sum of every non-null persisted `ProductionBatch.sale_price` and the sum of every non-null persisted `ProductionBatch.total_cost` respectively.

`known_tax` is added as the sum of every non-null persisted `ProductionBatch.tax`. Rules:

- a null tax never contributes zero;
- if no row has a known tax snapshot, `known_tax` is `null`;
- if at least one row has a known tax snapshot and the sum is zero, `known_tax` is `"0.00"`;
- tax may be aggregated for a row that has no margin because its total cost is unavailable;
- reports never calculate row tax;
- reports never read the current Settings tax rate.

### 3. Snapshot-backed known margin

`known_margin` is the sum of persisted `ProductionBatch.margin` over exactly the rows in `M`. Rules:

- a row with `margin = null` never contributes;
- a row with a persisted negative margin contributes its signed value;
- a row with persisted `"0.00"` contributes a real zero;
- reports never calculate `sale_price - total_cost`;
- reports never calculate `sale_price - total_cost - tax`;
- reports never repair or backfill old rows;
- reports never apply the current tax setting to historical rows.

An old row with `sale_price != null`, `total_cost != null`, `tax == null` and `margin == null` remains in `P` but is **not** in `T` or `M`. It contributes to known revenue and known production cost. It does **not** contribute to known tax, to known margin, or to the margin-percent numerator.

### 4. Accepted `known_margin_percent` formula

```text
margin_basis_revenue = Σ ProductionBatch.sale_price
                       over exactly the rows in M

known_margin_percent =
    ROUND_PERCENT(
        Σ ProductionBatch.margin over M
        ÷ margin_basis_revenue
        × 100
    )
```

`known_margin_percent` is `null` when `M` is empty, or when `margin_basis_revenue` is zero.

This is the accepted meaning of **"the same basis as `known_margin`"**: the denominator uses sale prices from exactly the rows whose persisted margin is included in the numerator. It does not use the global `known_revenue` total.

The existing prohibition against *aggregate margin divided by aggregate revenue* means: **do not divide snapshot-backed `known_margin` by the global `known_revenue` total when that total contains rows outside `M`.** It does not prohibit the same-basis denominator accepted above.

Do not use an arithmetic average of persisted row percentages; a weighted average of persisted row percentages; a sum of persisted `margin_percent`; an average of persisted `margin_percent`; the global `known_revenue`; the current Settings rate; or a reconstructed row margin. Persisted row `margin_percent` remains a historical row value and is **never** aggregated into `known_margin_percent`.

### 5. Zero-sale behaviour

A row with `sale_price == "0.00"` and `margin != null` belongs to `M`. It contributes its persisted margin to `known_margin`, contributes zero to `margin_basis_revenue`, increments the margin snapshot record count, and does not on its own make the aggregate percentage available.

When other `M` rows produce a positive `margin_basis_revenue`, the zero-sale row stays part of the aggregate margin numerator. When **every** row in `M` has a zero sale price, `known_margin` remains available, `known_margin_percent` is `null`, and the backend emits `margin_percent_unavailable_zero_basis`.

### 6. Existing counter compatibility

The existing fields are **not** repurposed. They remain for backward API compatibility and describe **legacy paired sale-price/cost input coverage**:

- `complete_finance_record_count` — the count of rows in `P`, that is `sale_price != null and total_cost != null`;
- `incomplete_margin_count` — the count of rows outside `P`, excluded because sale price or total cost is missing.

They are **no longer the authoritative snapshot-margin coverage counters**. Neither field is removed or renamed in `C2-III-B`. The frontend must use truthful Russian labels such as `Партий с ценой и себестоимостью` and `Партий с неполной парой цены и себестоимости`, and must **not** label them as the number of persisted margin snapshots.

### 7. Additive snapshot counters

These exact additive `FinanceReportResponse` fields are authorized:

```text
known_tax: str | null

tax_snapshot_record_count: int
missing_tax_snapshot_count: int

margin_snapshot_record_count: int
missing_margin_snapshot_count: int
```

- `tax_snapshot_record_count` — rows where persisted `tax` is non-null;
- `missing_tax_snapshot_count` — rows where persisted `tax` is null;
- `margin_snapshot_record_count` — rows where persisted `margin` is non-null;
- `missing_margin_snapshot_count` — rows where persisted `margin` is null.

For every response:

```text
tax_snapshot_record_count + missing_tax_snapshot_count
    == produced_order_count

margin_snapshot_record_count + missing_margin_snapshot_count
    == produced_order_count
```

Do not add tax-rate averages, margin-percent averages, taxable-base snapshots, duplicate known-margin fields, generic coverage objects, report status enums, or accounting fields.

`OverviewReportResponse.finance_summary` uses this exact same `FinanceReportResponse`. No overview-only finance fields and no overview-only finance calculation are created.

### 8. Warning contract

The four existing codes are preserved. Their `C2-III-B` meanings:

| Code | Emitted when |
|---|---|
| `missing_sale_price` | at least one row has `sale_price = null` |
| `missing_production_cost` | at least one row has `total_cost = null` |
| `margin_unavailable` | production rows exist but `margin_snapshot_record_count == 0` |
| `partial_margin_basis` | `margin_snapshot_record_count > 0` **and** `missing_margin_snapshot_count > 0` |

The `margin_unavailable` message must explain that no persisted margin snapshots are available. The `partial_margin_basis` message must explain that known margin uses only batches with persisted margin snapshots.

These additive codes are authorized:

| Code | Emitted when |
|---|---|
| `tax_unavailable` | production rows exist but `tax_snapshot_record_count == 0` |
| `partial_tax_basis` | both known and missing tax snapshots exist |
| `margin_percent_unavailable_zero_basis` | `known_margin` is available but the same-basis sale-price denominator is zero |

Rules: warnings use Russian user-readable messages; the warning `field` references the directly affected DTO field; codes are never duplicated; a configured zero is never warned as missing; no warning claims that reports calculated historical tax or margin; and no warning exposes database-column language.

### 9. Report documents

A newly generated `Сводка мастерской` may display `known_revenue`, `known_production_cost`, `known_tax`, `known_margin`, `known_margin_percent`, the additive snapshot counters, and the backend warnings. The document only **displays** backend report DTO values and performs no financial calculation of its own — consistent with the existing rule in `docs/report-documents.md` that the renderer never invents or recalculates tax.

Previously generated documents remain immutable and are never rewritten, regenerated or replaced. Changing or clearing the current tax setting changes none of: a historical `ProductionBatch` value, an existing report document, an existing report-document sidecar, or a report result sourced from persisted historical snapshots. Only a newly generated document reflects the report snapshot at its creation time. Document creation remains an explicit user action; there is no automatic regeneration.

### 10. Lifecycle

`C2-III-B` is `AUTHORIZED AFTER THIS PR MERGES — CONTRACT CLARIFIED — NOT IMPLEMENTED`. No implementation PR number is assigned. C2 remains **incomplete** until `C2-III-B` runtime implementation passes its focused and complete tests, its exact-head API and browser smoke pass, its runtime PR is reviewed and merged, and the active lifecycle documentation is closed. C3 and C4 remain inactive, and product release readiness is not claimed.

## Incomplete data

When data is missing or ambiguous, reports return warnings instead of silently inventing values. Examples:

- `missing_sale_price` — some produced orders do not have sale price.
- `missing_production_cost` — some production batches do not have total cost.
- `mixed_units` — produced quantities are shown by unit because grams, milliliters, and pieces cannot be safely summed together.
- `no_production_data` — no production batches exist yet.
- `margin_unavailable` — currently: no production batch has both sale price and cost, so margin is not returned.
- `partial_margin_basis` — currently: margin is returned, but only for complete finance rows.

The two margin warnings above describe the **current merged** paired-input behaviour. `C2-III-B` restates both against persisted margin snapshots and adds `tax_unavailable`, `partial_tax_basis`, and `margin_percent_unavailable_zero_basis`; see § *Accepted `C2-III-B` snapshot aggregation contract* § 8. The codes themselves are not renamed.

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
