# Current focus — `C2-II` merged and verified; `C2-III` subdivided into two bounded runtime slices

Active phase: **Roadmap completion window — C1 complete; `CR-008` accepted and merged (PR #150); `C2-I` merged (PR #151); `C2-II` merged (PR #152); `C2-III` subdivided, with only `C2-III-A` authorized after the subdivision documentation PR merges**

- Diagnostic audit: `DONE` (PATH A / COMPLETE)
- `R3 — Repair purchase-suggestions API smoke seeding`: **DONE**
- `R2 — Align import draft baseline test with date normalization`: **DONE**
- `R4 — Canonical backup/export filename reason normalization`: **DONE**
- `CR-005 — backup/export filename reason contract`: **ACCEPTED AND IMPLEMENTED**
- `CR-007 — C1 workshop tax-rate setting contract`: **ACCEPTED AND IMPLEMENTED**
- `C1-I — Implement backend-owned tax-rate setting`: **DONE — MERGED AND EXACT-HEAD VERIFIED** (PR #149)
- `CR-008 — C2 financial estimates and immutable production snapshots`: **ACCEPTED AND MERGED** (PR #150, merge commit `4c03142ef7acdc31fcb15730484e8e52dde95b69`)
- `C2-I — Backend financial readiness estimate`: **DONE — MERGED AND EXACT-HEAD VERIFIED** (PR #151)
- `C2-II — Transactional production financial snapshots`: **DONE — MERGED AND EXACT-HEAD VERIFIED** (PR #152)
- `C2-III-A — Order and ProductionBatch financial presentation`: **AUTHORIZED AFTER THIS PR MERGES — NOT IMPLEMENTED**
- `C2-III-B — Snapshot-backed reports and report documents`: **PLANNED — BLOCKED** on merged and exact-head-verified `C2-III-A`
- Backend baseline correction gate: **DONE**
- Merged `main` backend baseline: **GREEN**
- **No runtime implementation slice is active.** `C2-II` merged as PR #152 at `c3a3a7b8db06fe85290216113b784123ed9b6b30`, which is the current `origin/main`. The former `C2-III` planning umbrella is now subdivided into exactly two runtime slices, and no PR number is assigned to either.

All four accepted backend baseline gate failures are closed on `main`. The accepted `CR-007` decision (PR #148, merge commit `80b83de3e838cf676669a1b627770300590c99c0`, final reviewed head `577e0fd0b5c3e6fc82e2399fd17f023b6e221b83`) authorized exactly one bounded implementation slice, and that slice is now merged.

## C1-I — merged, verified, DONE

`C1-I` is **`DONE — MERGED AND EXACT-HEAD VERIFIED`** (VERIFIED FROM REPOSITORY / GITHUB / MERGED PR EVIDENCE).

- PR #149 `C1-I — Implement backend-owned tax-rate setting`, state `MERGED`
- Final reviewed head: `1c01c05c861c4008ad6304210dbd65d9fd8dcdf9`
- Merge commit: `ff7afe6b0778ab2b348229a4df34acf3e3fc0001`
- Merged at: `2026-07-27T19:44:53Z`
- `origin/main` equals that merge commit; both the final head and the merge commit were verified as ancestors of `origin/main`.

Accepted merged evidence. None of these results was executed in the documentation task that recorded this closure.

| Check | Accepted result |
|---|---|
| Backend complete suite | `671 collected, 671 passed, 0 failed, 0 skipped` |
| Original merged baseline node IDs still collected | all `562` |
| Focused tax-setting frontend suite | `52 passed, 0 failed, 0 skipped` |
| All 13 focused frontend suites | `568 passed, 0 failed, 0 skipped` |
| Frontend production build | `PASS` |
| Exact-head `/settings` browser smoke | `PASS — 146 checks / 0 failures` |
| Exact smoke-tested head | `1c01c05c861c4008ad6304210dbd65d9fd8dcdf9` |
| `frontend/src/main.ts` | `6406` before → `6399` after |

Delivered on merged `main`: `GET /api/settings/tax-rate` and `PUT /api/settings/tax-rate` in a dedicated router, service, schema, and domain-validation module under the existing `/api/settings` namespace; persistence of the key `default_tax_rate` through the existing `app_settings` table with **no migration**; strict decimal-string validation with structured Russian errors; the canonical exactly-two-decimal representation; a backend-generated monotonic `effective_at`; explicit Clear as row deletion of the `default_tax_rate` row only; exactly one atomic `tax_rate_setting_changed` audit per real mutation with rollback on audit failure; the no-op contract; the `Налоговая ставка для расчётов` section inside `/settings`; and the Settings Decision Matrix marking `default_tax_rate` — and only `default_tax_rate` — as newly editable. The legacy `tax.default_rate = "0.06"` placeholder is unchanged and is never read as a configured rate.

`C1-I` implemented **only the tax-rate setting**, not any C2 calculation. It no longer awaits smoke, review, or merge, and it is not reopened.

## CR-008 — accepted C2 financial decision

`CR-008 — Decide C2 financial estimates and immutable production snapshots` is **accepted** (RECORDED PRODUCT-OWNER DECISION, 2026-07-27) and **not implemented**. The durable contract is `docs/decisions/0012-c2-financial-calculation-snapshots.md`, with the formulas in `AGENTS.md` § 6.6, `docs/architecture.md` § 8.6, and `docs/domain-model.md`, the API mapping in `docs/api.md`, the report boundary in `docs/reports.md`, and the slice contracts in `docs/implementation-plan.md` § 11.

- **Product boundary.** An internal operational estimate for the workshop — never tax filing, a declaration, VAT accounting, automatic regime selection, УСН / ОСНО / НПД / ПСН / АУСН / ЕСХН calculation, insurance contributions, minimum tax, annual or quarterly tax accounting, marketplace tax accounting, invoicing, bookkeeping, or legal or tax advice. Nothing is renamed to a tax reserve. The simplified percentage-of-sale model is the accepted MVP model and may be replaced only by a separately decided future tax-regime model, after which existing snapshots stay immutable.
- **Formulas.** `Decimal` only, never binary float: `tax_amount = ROUND_MONEY(sale_price × tax_rate_percent / 100)`; `margin = ROUND_MONEY(sale_price − total_cost − tax_amount)`; `margin_percent = ROUND_PERCENT(margin / sale_price × 100)`. The percentage is always divided by `100`; money and percentage quanta are both `0.01` with `ROUND_HALF_UP`; only the final amount of each formula is rounded; tax is deducted from gross revenue, never added on top.
- **Availability.** Configured `0.00` yields tax `0.00`. A missing rate or missing sale price yields `null`, never a fabricated zero. Margin is `null` when sale price, total cost, or tax is unavailable. Margin percent needs an available margin **and** a sale price greater than zero; a zero sale price yields `partial` with margin percent `null` and the warning `margin_percent_unavailable_zero_sale_price`. Negative margin and negative margin percent are valid and are never clamped. An invalid persisted rate is handled defensively with `tax_rate_invalid`, without coercion, without a fabricated zero, and without an unhandled HTTP 500.
- **No valid configured tax-rate context.** A missing `default_tax_rate` row and an invalid persisted value stay distinguishable through the warnings `tax_rate_missing` and `tax_rate_invalid` — the invalid case never also emits `tax_rate_missing` — but both return `tax_rate_percent = null` and `tax_rate_effective_at = null`, both leave tax, margin, and margin percent unavailable, and **neither blocks physical production**. The raw invalid value is never returned as an authoritative rate and never reaches a readiness DTO, a confirmation request, or a `ProductionBatch` snapshot.
- **Timestamps.** Storage stays `YYYY-MM-DD HH:MM:SS` UTC SQLite text (no `T`, no `Z`, no offset) for `AppSetting.updated_at` and the future `tax_rate_effective_at_snapshot`; the API and confirmation context use `YYYY-MM-DDTHH:MM:SSZ`. Local time, arbitrary offsets, fractional seconds, a space instead of `T`, and a missing `Z` are rejected with `422 invalid_tax_rate_context`, and the API never exposes the raw stored form.
- **Warnings stay non-blocking.** The existing `tax_rate_missing`, `sale_price_missing`, and `cost_data_missing` codes and the exact existing `ProductionReadinessIssue` structure are preserved; only the two codes above are added; no aliases are introduced; and `can_produce` stays governed only by recipe/formula readiness, stock, lots, packaging, order lifecycle, and existing physical safety rules.
- **Readiness API mapping.** The existing endpoint is extended additively. `estimated_cost`, `estimated_tax`, and `estimated_margin` are **reused**; only `sale_price`, `tax_rate_percent`, `tax_rate_effective_at`, `estimated_margin_percent`, and `financial_estimate_status` are added. `estimated_total_cost` is not authorized.
- **Snapshots.** `C2-II` adds exactly two nullable `ProductionBatch` columns, `tax_rate_percent_snapshot` and `tax_rate_effective_at_snapshot`, never backfilled, reusing the existing financial fields with no duplicate monetary snapshots, and reads the setting inside the production transaction through a bounded `connection`-aware extension of the C1 service.
- **Confirmation context.** `expected_tax_rate_percent` and `expected_tax_rate_effective_at` are required-but-nullable and declared without defaults. `null/null` means readiness observed **no valid configured tax rate** — a missing row **or** an invalid persisted value — not only an absent row. **Omission is not the same as explicit `null/null`** (`422 tax_rate_context_required`), and a partial-null, malformed, non-canonical, or out-of-range context is `422 invalid_tax_rate_context`. Stale conflict `409 tax_rate_context_stale`, writing nothing, fires on valid → changed valid, valid → missing, valid → invalid, missing → valid, and invalid → valid; **missing ↔ invalid is deliberately not a conflict**, because both produce the same financial result. An accepted no-valid-rate confirmation persists null rate snapshots and null tax, margin, and margin percent while completing physical production normally, and never repairs, clears, rewrites, or audits the invalid setting.
- **Reports** read persisted snapshots only, never recalculate history with the current rate, and show old rows as unavailable rather than `0.00`.
- **Frontend** performs no financial arithmetic, and `frontend/src/main.ts` stays at **at most 6399 lines** throughout C2.

## C2-I — merged and exact-head verified (2026-07-28)

`C2-I` is **`DONE — MERGED AND EXACT-HEAD VERIFIED`** (VERIFIED FROM REPOSITORY / GITHUB / MERGED PR EVIDENCE). PR #151, final reviewed head `6f72bffc9a0d17839e3a74c69366fe17df8a318b`, merge commit `7b3dde8278f59658bfa3a81c09e643ea10319551`, merged `2026-07-28T04:22:13Z`, exact-head readiness API smoke `PASS — 113 checks / 0 failures`, complete backend suite `737 passed / 0 failed / 0 skipped`. Both the final head and the merge commit are ancestors of `origin/main`.

Delivered on merged `main`, matching ADR 0012 without reinterpreting it:

- **One pure domain module**, `backend/app/domain/production_financials.py` — `TaxRateContext`, `ProductionFinancialInputs`, the immutable `ProductionFinancialEstimate`, `FinancialEstimateStatus`, and `FinancialWarningCode`. It opens no connection, reads no repository, imports neither FastAPI nor Pydantic, builds no `ProductionReadinessIssue`, and writes nothing.
- **Service integration** through `ProductionReadinessService._estimate_financials`, replacing the previous `_estimate_money`. As merged, the rate was read only through the existing no-argument C1 `TaxRateSettingsService.get_tax_rate()`, and the transaction-aware `connection=` extension was deliberately left to `C2-II`.
- **The five additive response fields** — `sale_price`, `tax_rate_percent`, `tax_rate_effective_at`, `estimated_margin_percent`, `financial_estimate_status` — plus activation of the reused `estimated_tax` and `estimated_margin`. `estimated_total_cost` is absent and no field was renamed, removed, or duplicated.
- **The two new warning codes** only, carried by the existing `ProductionReadinessIssue` structure. All financial warnings stay non-blocking and `can_produce` is untouched.
- **Invalid-rate re-validation.** Because the C1 Settings repair surface may still return the stored text for an externally corrupted row, `is_configured` alone is not trusted: the returned percentage is re-parsed through the existing C1 `parse_tax_rate_percent`, and anything that fails — or a row with no effective timestamp — becomes the no-valid-rate context with `tax_rate_invalid`, never a raw value, never a fabricated `0.00`, and never an unhandled HTTP `500`.
- **Read-only.** No migration, no schema change, no persistence write, no `AuditLog`, no `ProductionBatch` change, no report change. `frontend/src/main.ts` is unchanged at exactly `6399` lines and no frontend production source was touched.

## C2-II — merged and exact-head verified (2026-07-28)

`C2-II` is **`DONE — MERGED AND EXACT-HEAD VERIFIED`**.

`VERIFIED FROM REPOSITORY / GITHUB / MERGED PR EVIDENCE — NOT RE-EXECUTED IN THIS DOCUMENTATION PR`

| Item | Verified value |
|---|---|
| PR | #152 — `C2-II — Persist transactional production financial snapshots` |
| State | `MERGED`, base `main` |
| Final reviewed head | `0cdda1b06b9783975f085207527f7d36a2ef7f22` |
| Merge commit | `c3a3a7b8db06fe85290216113b784123ed9b6b30` |
| Merged at | `2026-07-28T09:00:50Z` |
| Exact smoke-tested head | `0cdda1b06b9783975f085207527f7d36a2ef7f22` |
| Accepted backend result | complete backend suite `883 passed / 0 failed / 0 skipped`; all `737` original merged-baseline node IDs still collected, zero renames |
| Accepted frontend result | all 15 focused frontend suites green, `0 failed` |
| Production build | `npm run build` — `PASS` |
| Exact-head migration smoke | `PASS — 41 checks / 0 failures` |
| Exact-head API smoke | `PASS — 57 checks / 0 failures` |
| Exact-head browser smoke | `PASS — all Orders-route checks / 0 failures` |
| `frontend/src/main.ts` final line count | `6399` |
| Migration `0019` delivered | yes — `0019_production_batch_tax_rate_snapshots` |
| Commit added after the accepted smoke | none — the head was verified unchanged and the tree clean afterwards |

`origin/main` equals the PR #152 merge commit, and both the final reviewed head and the merge commit are ancestors of `origin/main`.

Delivered on merged `main`, matching ADR 0012 without reinterpreting or expanding it:

- **One additive migration**, `0019_production_batch_tax_rate_snapshots`, adding only the two nullable `TEXT` columns `tax_rate_percent_snapshot` and `tax_rate_effective_at_snapshot` to `production_batches` — no default, no backfill, no table rebuild, no new table, and no duplicate monetary column. Existing rows keep every value and read `NULL` for both.
- **The bounded transaction-aware read.** `TaxRateSettingsService.get_tax_rate(connection=None)` — the no-argument behavior is unchanged, and a supplied connection reads `default_tax_rate` through the existing `SettingsRepository` on that exact connection, writing nothing and auditing nothing. No second tax-setting service, no raw `AppSetting` parsing in the confirmation service, and no generic transaction service locator.
- **One shared reducer**, `backend/app/services/tax_rate_context.py`, used by both readiness and confirmation. Missing and invalid both reduce to the comparable `null/null` context; the missing-versus-invalid distinction survives only where readiness warning generation needs it. `TaxRateContext` now rejects impossible state combinations outright.
- **The required-but-nullable request context**, validated in `backend/app/domain/production_tax_context.py` before anything is written. Omission is `422 tax_rate_context_required`; a partial-null, non-string, malformed, non-canonical, or out-of-range value is `422 invalid_tax_rate_context`. Both are returned in the repository's normal structured error contract, never as raw Pydantic internals.
- **The stale-context comparison**, run inside the existing `BEGIN IMMEDIATE` transaction before the first production write, raising `409 tax_rate_context_stale` with safe Russian guidance. Every row of the accepted matrix behaves exactly as decided, including the deliberate non-conflicts missing → invalid and invalid → missing.
- **Immutable financial snapshots** written in the same transaction as the batch, the ingredient and packaging snapshots and write-offs, the Order transition, and the `production_confirmed` audit. The arithmetic reuses the merged `C2-I` pure domain calculation; no formula is duplicated in `ProductionConfirmationService`.
- **One timestamp boundary**, `backend/app/domain/tax_rate_timestamps.py`, converting between the `YYYY-MM-DD HH:MM:SS` storage form and the `YYYY-MM-DDTHH:MM:SSZ` API form. The raw stored text never reaches a response.
- **A narrow API exposure boundary.** The two snapshots appear in the confirmation response and the `ProductionBatch` detail response only. The `ProductionBatch` list response, every report read model, every report API response, and the report UI are unchanged.
- **Minimal frontend integration.** `frontend/src/order-production-context.ts` owns the readiness context and request construction; the readiness DTO guard now requires the context pair and never fabricates `null/null`; a stale `409` is classified as a known no-write conflict that invalidates the cached readiness, closes the confirmation, and demands a fresh check without any automatic retry. No financial arithmetic and no financial presentation were added, and `frontend/src/main.ts` is unchanged at exactly `6399` lines.

## What is authorized next

**Merged `main` contains the `C2-I` readiness estimate and the `C2-II` transactional snapshots**, including migration `0019_production_batch_tax_rate_snapshots`, the required-but-nullable confirmation context, and `409 tax_rate_context_stale`. There is still **no financial presentation in the UI** and **no report change**: reports read no snapshots.

`C2-III` is no longer a single planning umbrella. It is subdivided into exactly two runtime slices — no more, no fewer.

- **`C2-III-A` — Order and `ProductionBatch` financial presentation** is the **only** slice authorized after this documentation PR merges. Status: `AUTHORIZED AFTER THIS PR MERGES — NOT IMPLEMENTED`. It covers one user workflow — check Order readiness → understand the financial estimate → confirm production → see the persisted actual financial result — through Order readiness presentation, `ProductionBatch` detail presentation, and a compact `ProductionBatch` list financial summary. It excludes reports, report DTOs, `/reports` UI, and report documents. Do not start it from this unmerged documentation branch. Full scope, presentation semantics, and constraints — including the frontend display-only rule and the `frontend/src/main.ts <= 6399` invariant — are in `docs/implementation-plan.md` § 11 and ADR 0012.
- **`C2-III-B` — snapshot-backed reports and report documents** stays **`PLANNED — BLOCKED`** until `C2-III-A` is implemented, reviewed, exact-head smoke verified, and merged. It is **not authorized by this PR**. It excludes Orders readiness and `ProductionBatch` UI. No new aggregate margin-percent formula is defined for it; the existing documented `known_margin_percent` paired basis in `docs/reports.md` remains the only accepted aggregate basis, and an arithmetic average, a weighted average, aggregate margin over aggregate revenue, or recalculation from current settings may not be chosen silently.

No implementation PR number is assigned to `C2-III-A` or `C2-III-B`.

```text
C2 is not complete after C2-III-A.
```

C2 becomes complete only after `C2-III-A` is merged and exact-head verified, `C2-III-B` is separately authorized, `C2-III-B` is merged and exact-head verified, and the active documentation and state are closed consistently. C3 and C4 remain inactive.

## R4 merge closure

`R4` is **DONE** (VERIFIED FROM REPOSITORY / GITHUB / MERGED PR EVIDENCE).

- PR #146 `R4 — Canonical backup/export filename reason normalization`, state `MERGED`
- Final reviewed head: `c505de2dc213ff75e0eb7cb5ffbcd180069a86fb`
- Merge commit: `127191feb182ccf68a4d7b9f2be28f6aa5b42453`
- Merged at: `2026-07-27T08:51:06Z`

Both original filename nodes are closed on `main`:

```text
app/tests/test_backups_api.py::test_backup_reason_defaults_empty_and_sanitizes_unsafe_characters
app/tests/test_exports_api.py::test_export_reason_defaults_empty_and_sanitizes_unsafe_characters
```

## CR-005 status

`CR-005` remains **accepted** and **implemented**. The durable contract is unchanged and lives in `docs/backup-and-restore.md`, `docs/export.md`, and `docs/api.md`. The canonical filename reason segment is owned by the shared backend helper `normalize_artifact_reason_segment` in `backend/app/services/local_artifact_filenames.py`; the export JSON manifest continues to carry the normalized human reason.

`R4` is closed and is **not reopened**. `CR-005` is closed and is **not reopened**.

## CR-006 — export create-response fallback — NEEDS EVIDENCE, not active

`CR-006 — Investigate export create-response fallback confirmation semantics` remains a **`needs evidence`** row in `state/change-requests.md`. It is **not an active implementation slice** and is **non-blocking**.

Exact current behavior in `backend/app/api/exports.py::create_export`:

- after `create_json_export` writes an export, the endpoint attempts to find the exact created file through `list_export_files`;
- when the exact file is found, the API response uses parsed filename metadata and therefore returns the canonical filename-derived reason;
- when the exact file is **not** found, the defensive fallback constructs an `ExportFile` using `ExportResult.reason`;
- `ExportResult.reason` is the normalized **human** reason preserved in the export manifest;
- therefore the fallback may return a human reason where the API contract normally expects the canonical filename-derived slug.

Classification: **NEEDS EVIDENCE.** Not a confirmed product defect. No user-visible failure has been reproduced, and no data loss, overwrite, incorrect file content, or unsafe mutation is proven. Fallback reachability is not established, **no severity is assigned**, and **no correction design is authorized**.

`CR-006` is not part of `CR-004`, is not a reason to reopen `CR-005`, and is not a reason to reopen `R4`. It is **not** a fifth backend baseline failure. Full evidence: `docs/backend-baseline-failure-triage.md` §17.

## Remaining release obligations

None of these is activated here.

- `CR-004` — SQLite backup transaction-consistency investigation — remains a separate `needs evidence` row and is **not active**.
- Restore product decision and implementation remains **open**.
- Final macOS packaging and user-ready launch remains **open**.
- Installation verification remains **open**.
- Packaged update flow and update smoke remain **open**.
- Full release-candidate smoke remains **open**.
- C1 is **complete**: `CR-007` is accepted and `C1-I` is merged and `DONE`. C2 has an **accepted product contract** (`CR-008`) and is **not complete**: `C2-I` is merged (PR #151) and `C2-II` is merged (PR #152), `C2-III-A` is authorized after this documentation PR merges, and `C2-III-B` remains blocked. C3 and C4 remain **inactive** unless separately authorized.
- Continuing documentation accuracy remains an ongoing obligation.

**Product release readiness is not claimed.**
