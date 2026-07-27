# Current focus — C1-I merged and DONE; C2 financial contract being decided in a documentation PR

Active phase: **Roadmap completion window — C1 complete; C2 product contract (`CR-008`) under decision; no C2 runtime implementation exists**

- Diagnostic audit: `DONE` (PATH A / COMPLETE)
- `R3 — Repair purchase-suggestions API smoke seeding`: **DONE**
- `R2 — Align import draft baseline test with date normalization`: **DONE**
- `R4 — Canonical backup/export filename reason normalization`: **DONE**
- `CR-005 — backup/export filename reason contract`: **ACCEPTED AND IMPLEMENTED**
- `CR-007 — C1 workshop tax-rate setting contract`: **ACCEPTED AND IMPLEMENTED**
- `C1-I — Implement backend-owned tax-rate setting`: **DONE — MERGED AND EXACT-HEAD VERIFIED** (PR #149)
- `CR-008 — C2 financial estimates and immutable production snapshots`: **ACCEPTED** (decided in the active documentation PR)
- `C2-I — Backend financial readiness estimate`: **AUTHORIZED AFTER THIS DOCUMENTATION PR MERGES — NOT IMPLEMENTED**
- `C2-II — Transactional production financial snapshots`: **PLANNED — BLOCKED**
- `C2-III — Financial presentation and snapshot-backed reports`: **PLANNED — BLOCKED**
- Backend baseline correction gate: **DONE**
- Merged `main` backend baseline: **GREEN**
- **No runtime implementation slice is active.** The active work is the `CR-008` documentation decision PR on branch `claude/close-c1-decide-c2-financial-contract`, started from merged `origin/main` `ff7afe6b0778ab2b348229a4df34acf3e3fc0001`.

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
- **Warnings stay non-blocking.** The existing `tax_rate_missing`, `sale_price_missing`, and `cost_data_missing` codes and the exact existing `ProductionReadinessIssue` structure are preserved; only the two codes above are added; no aliases are introduced; and `can_produce` stays governed only by recipe/formula readiness, stock, lots, packaging, order lifecycle, and existing physical safety rules.
- **Readiness API mapping.** The existing endpoint is extended additively. `estimated_cost`, `estimated_tax`, and `estimated_margin` are **reused**; only `sale_price`, `tax_rate_percent`, `tax_rate_effective_at`, `estimated_margin_percent`, and `financial_estimate_status` are added. `estimated_total_cost` is not authorized.
- **Snapshots.** `C2-II` adds exactly two nullable `ProductionBatch` columns, `tax_rate_percent_snapshot` and `tax_rate_effective_at_snapshot`, never backfilled, reusing the existing financial fields with no duplicate monetary snapshots, and reads the setting inside the production transaction through a bounded `connection`-aware extension of the C1 service.
- **Confirmation context.** `expected_tax_rate_percent` and `expected_tax_rate_effective_at` are required-but-nullable and declared without defaults; **omission is not the same as explicit `null/null`** (`422 tax_rate_context_required` versus a valid unconfigured pair), a partial-null or malformed context is `422 invalid_tax_rate_context`, and a changed, cleared, or newly configured rate is `409 tax_rate_context_stale` that writes nothing.
- **Reports** read persisted snapshots only, never recalculate history with the current rate, and show old rows as unavailable rather than `0.00`.
- **Frontend** performs no financial arithmetic, and `frontend/src/main.ts` stays at **at most 6399 lines** throughout C2.

## What is authorized next

**No C2 runtime implementation exists.** No migration, no snapshot column, no tax or margin calculation, and no report change is on `main`.

After the `CR-008` documentation PR merges:

- **`C2-I — Backend financial readiness estimate` becomes the only authorized runtime slice.** Scope, non-goals, backend requirements, the frontend `6399`-line invariant, the 34 required test cases, and the exact-head readiness API smoke are in `docs/implementation-plan.md` § 11. Do **not** start it from the unmerged documentation branch.
- **`C2-II` stays `PLANNED — BLOCKED`** on merged and verified `C2-I`.
- **`C2-III` stays `PLANNED — BLOCKED`** on merged and verified `C2-II`, and is a **planning umbrella** that must be subdivided before implementation if it is not one bounded, independently reviewable vertical slice.

No future implementation PR number is assigned to any C2 slice.

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
- C1 is **complete**: `CR-007` is accepted and `C1-I` is merged and `DONE`. C2 has an **accepted product contract** (`CR-008`) and **no implementation**; only `C2-I` becomes authorized after the documentation PR merges, and `C2-II` and `C2-III` remain blocked. C3 and C4 remain **inactive** unless separately authorized.
- Continuing documentation accuracy remains an ongoing obligation.

**Product release readiness is not claimed.**
