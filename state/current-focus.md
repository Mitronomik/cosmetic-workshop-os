# Current focus — `C2-III-B` report aggregation contract clarified; runtime still not implemented

Active phase: **Roadmap completion window — C1 complete; `CR-008` accepted and merged (PR #150); `C2-I` merged (PR #151); `C2-II` merged (PR #152); `C2-III-A` merged (PR #154) and closed; `C2-III-B` authorized as the last remaining C2 runtime slice, its report aggregation contract clarified after a blocking Phase 0 audit, and still not implemented**

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
- `C2-III-A — Order and ProductionBatch financial presentation`: **DONE — MERGED AND EXACT-HEAD VERIFIED** (PR #154)
- `C2-III-B — Snapshot-backed reports and report documents`: **AUTHORIZED AFTER THIS PR MERGES — CONTRACT CLARIFIED — NOT IMPLEMENTED**
- Backend baseline correction gate: **DONE**
- Merged `main` backend baseline: **GREEN**
- **No runtime implementation slice is open.** `C2-III-A` merged as PR #154 at merge commit `d432fcaee52a16a4f8b609ec160cf3fa2b33d013`, which is the `origin/main` this documentation branch started from. `C2-III-B` is the **only** remaining authorized C2 runtime slice, it is **not implemented**, and no PR number is assigned to it.

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

## C2-III-A — merged and exact-head verified (2026-07-28)

`C2-III-A — Order and ProductionBatch financial presentation` is:

```text
C2-III-A — Order and ProductionBatch financial presentation:
DONE — MERGED AND EXACT-HEAD VERIFIED
```

`VERIFIED FROM MERGED PR #154 EVIDENCE — NOT RE-EXECUTED IN THIS DOCUMENTATION PR`

| Item | Verified value |
|---|---|
| PR | #154 — `C2-III-A — Present Order and ProductionBatch financials` |
| State | `MERGED`, base `main` |
| Final reviewed head | `ef1103811a8f062f9129bfb465a98e0cfa388935` |
| Merge commit | `d432fcaee52a16a4f8b609ec160cf3fa2b33d013` |
| Merged at | `2026-07-28T13:05:34Z` |
| Exact smoke-tested head | `ef1103811a8f062f9129bfb465a98e0cfa388935` — identical to the final reviewed head |
| Focused frontend suites | `order-readiness-presentation` `19 pass`; `order-mutation-lifecycle` `33 pass`; `order-production-context` `25 pass`; `order-production-feedback` `21 pass`; new `production-financial-presentation` `22 pass` — all `0 fail / 0 skipped` |
| Complete frontend test-script result | all 16 `test:*` scripts pass, `0 failed`, `0 skipped` |
| Frontend production build | `npm run build` — `PASS` |
| Focused backend result | `test_production_readiness.py`, `test_production_batches_api.py`, `test_production_tax_snapshots.py`, `test_production_confirmation.py` → `160 passed / 0 failed / 0 skipped` |
| Complete backend result | `883 passed / 0 failed / 0 skipped` — byte-identical to the pre-change baseline, all `883` baseline node IDs still collected, zero renames |
| Exact-head API smoke | `PASS — 67 checks / 0 failures` |
| Exact-head browser smoke | `PASS — 28 checks / 0 failures` |
| `frontend/src/main.ts` | `6399` before → `6398` after |
| Commit added after the accepted smoke | none — the head was verified unchanged and the tree clean afterwards |
| Backend formulas, persistence, migrations and reports | unchanged in `C2-III-A` |

`origin/main` equals the PR #154 merge commit, and both the final reviewed head and the merge commit are ancestors of `origin/main`.

Delivered on merged `main`, matching ADR 0012 and `docs/implementation-plan.md` § 11 without reinterpreting them:

- **Two focused frontend modules.** `frontend/src/production-financial-contract.ts` holds the financial DTO types, the three-value `financial_estimate_status` enum, and the readiness financial validation; `frontend/src/production-financial-presentation.ts` holds every financial render function. No catch-all `finance.ts`, `utils.ts`, `helpers.ts`, `manager.ts`, or `common.ts` was created, and the canonical tax-rate pair checks stay in the existing `order-production-context.ts`.
- **Order readiness financial presentation.** One financial block inside the existing readiness result card showing `Цена продажи`, `Ориентировочная себестоимость`, `Ставка налога`, `Налог`, `Маржа`, and `Маржа, %`, with `Ставка действует с: <formatted timestamp>` through the existing application date/time formatter when a rate is configured, and the backend status rendered as `Доступно` / `Частично` / `Недоступно` on an existing pill. The status is never inferred from which fields are null.
- **Immutable actual result.** One shared `Фактическая экономика партии` block renders the persisted `ProductionBatch` snapshot after successful production **and** when an existing batch of a produced or delivered Order is opened, so the two can never drift apart. No estimate-versus-actual variance is calculated or shown, and the current Settings rate is never compared with a historical snapshot.
- **Production history list.** A compact operational summary using only the five existing list fields — sale price, total cost, tax, margin, margin percent. The rate snapshots stay detail-only; no aggregate, total, sort, filter, or second list endpoint was added, and existing search, selection, loading, retained-snapshot and error behavior is unchanged.
- **DTO validation.** A trusted readiness result now requires every additive financial key, a `financial_estimate_status` that is exactly `available`, `partial`, or `unavailable`, and a rate context that is either a canonical pair or explicit `null/null`. `ProductionBatch` detail now requires **both** rate-snapshot keys present; a missing key is an outdated response rather than an implicit null. Malformed or partially populated context reaches the existing untrusted-response path, and nothing is normalized or repaired. The batch list contract is unchanged and still carries no rate snapshots.
- **Value semantics.** Backend `"0.00"` renders as a real zero; `null` renders as `Недоступно` and never as `0`, `0.00`, `0 ₽`, or `0%`; a negative margin and a negative margin percent keep their sign and are marked as negative.
- **No frontend arithmetic.** No money, percentage, or tax-rate value is converted to a JavaScript number, and no tax, margin, margin-percent, status, or variance is derived in the frontend.
- **Backend unchanged.** No formula, readiness status calculation, warning generation, tax-rate setting behavior, production confirmation, persistence, migration, snapshot, report query, report schema, or report document was changed; no endpoint was added; and no backend test was modified. The complete backend suite is unchanged at `883 passed / 0 failed / 0 skipped` with all `883` baseline node IDs still collected.
- **`frontend/src/main.ts` `6399` before → `6398` after.** The file did not grow; the two per-line batch cost-snapshot tables moved into the focused presentation module.
- **Physical readiness untouched.** `can_produce`, the physical readiness status, the stale-result ownership and the production guard behave exactly as before, and backend financial warnings are still shown once through the existing readiness warning section.

## What is authorized next

**Merged `main` contains the `C2-I` readiness estimate, the `C2-II` transactional snapshots and the `C2-III-A` financial presentation**, including migration `0019_production_batch_tax_rate_snapshots`, the required-but-nullable confirmation context, `409 tax_rate_context_stale`, the Order readiness financial block, the shared `Фактическая экономика партии` block, and the compact `ProductionBatch` list financial summary. There is still **no report change**: reports read no snapshots.

`C2-III-B` is the **only** remaining C2 runtime slice, and this documentation PR authorizes it.

```text
C2-III-B — Snapshot-backed reports and report documents:
AUTHORIZED AFTER THIS PR MERGES — CONTRACT CLARIFIED — NOT IMPLEMENTED
```

It must not be started from this unmerged documentation branch, and no PR number is assigned to it.

### Authorized `C2-III-B` boundary

One bounded backend-plus-frontend report vertical:

```text
persisted ProductionBatch financial snapshots
→ backend report aggregation
→ report DTOs
→ /reports presentation
→ overview report consumers
→ generated «Сводка мастерской»
```

**Backend report ownership.** The affected financial reports must read persisted `ProductionBatch` financial snapshots. Report tax comes only from persisted `ProductionBatch.tax`; report margin comes only from persisted `ProductionBatch.margin`; historical rate changes never modify existing report results; the current Settings tax rate is never applied retroactively; report calculations remain backend-owned; report endpoints remain read-only; and report reads create no audit records and no business mutations.

**Missing, zero and negative values.** An explicit stored `"0.00"` stays a real known zero; `null` stays unavailable or incomplete; a negative margin and a negative margin percentage stay valid signed information; and a missing historical snapshot stays different from configured zero tax. A null snapshot must never be included as a fabricated `0`, `0.00`, `0 ₽`, or `0%`. Old batches with incomplete financial snapshots must contribute to explicit incomplete-data counters or warnings rather than silently appearing complete.

**Aggregate basis — conflict found and resolved.** This paragraph previously said no new aggregate margin-percent formula was defined and required the runtime task to **stop and report the exact conflict** if the documented paired basis contradicted snapshot-backed aggregation. That happened. The read-only Phase 0 audit stopped with `C2-III-B — BLOCKED BY REPORT AGGREGATION CONTRACT CONFLICT` and created no branch, edit, commit or PR: the paired sale-price/cost set `P` and the persisted-margin set `M` are the same set only while margin is derived, and diverge as soon as reports read snapshots, because pre-`C2-II` rows carry a known sale price and total cost with `tax` and `margin` both `null`.

The accepted resolution is now recorded in `docs/reports.md` § *Accepted `C2-III-B` snapshot aggregation contract* and in ADR 0012 § *Accepted clarification — snapshot report aggregation contract*: `known_margin` is the sum of persisted `ProductionBatch.margin` over `M`; `known_margin_percent` is `ROUND_PERCENT(Σ margin over M ÷ Σ sale_price over M × 100)`, `null` when `M` is empty or that denominator is zero; `known_tax` is the sum of persisted `ProductionBatch.tax`. The global `known_revenue` is never the denominator, and persisted row `margin_percent` is never summed or averaged. `complete_finance_record_count` and `incomplete_margin_count` keep their paired sale-price/cost meanings and are not snapshot-coverage counters; the additive fields are `known_tax`, `tax_snapshot_record_count`, `missing_tax_snapshot_count`, `margin_snapshot_record_count`, `missing_margin_snapshot_count`; the additive warnings are `tax_unavailable`, `partial_tax_basis`, `margin_percent_unavailable_zero_basis`.

**Report DTO and UI boundary.** Synchronized changes are authorized in the affected finance report backend model, the affected overview finance summary, the corresponding API schemas, frontend `/reports`, backend-provided report warnings, and document generation for `Сводка мастерской` where it consumes the affected report DTO. The frontend displays backend report DTOs and backend warnings; it must not calculate report tax, report margin, report margin percentage, incomplete-data coverage, or historical financial values.

**Report documents.** `Сводка мастерской` stays synchronized with the report DTO it consumes. Newly generated documents may reflect the snapshot-backed report result. Previously generated documents remain immutable and are never rewritten, regenerated, or silently replaced. Document generation remains an explicit user action.

**Explicit exclusions.** `C2-III-B` must not change Orders readiness; Order production confirmation; the Order lifecycle; `ProductionBatch` persistence; `ProductionBatch` list presentation; `ProductionBatch` detail presentation; the `C2-III-A` financial presentation modules; tax-rate Settings behavior; migrations; historical `ProductionBatch` rows; or stock and production transactions.

### C2 completion boundary

```text
C2 is not complete in this documentation PR.
```

C2 becomes complete only after `C2-III-B` is implemented; its focused and complete tests pass; its exact-head API and browser smoke pass; it is reviewed and merged; and the final active C2 documentation and state are closed consistently. C2 is **not** complete merely because `C2-III-B` is now authorized. C3 and C4 remain inactive, and product release readiness is not claimed.

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
- C1 is **complete**: `CR-007` is accepted and `C1-I` is merged and `DONE`. C2 has an **accepted product contract** (`CR-008`) and is **not complete**: `C2-I` is merged (PR #151), `C2-II` is merged (PR #152) and `C2-III-A` is merged (PR #154), while `C2-III-B` is authorized after this documentation PR merges and is **not implemented**. C3 and C4 remain **inactive** unless separately authorized.
- Continuing documentation accuracy remains an ongoing obligation.

**Product release readiness is not claimed.**
