# Current focus — C1-I implemented on its PR branch; exact-head `/settings` smoke required before merge

Active phase: **Roadmap completion window C1 — product contract decided; `C1-I` implemented and unmerged**

- Diagnostic audit: `DONE` (PATH A / COMPLETE)
- `R3 — Repair purchase-suggestions API smoke seeding`: **DONE**
- `R2 — Align import draft baseline test with date normalization`: **DONE**
- `R4 — Canonical backup/export filename reason normalization`: **DONE**
- `CR-005 — backup/export filename reason contract`: **ACCEPTED AND IMPLEMENTED**
- `CR-007 — C1 workshop tax-rate setting contract`: **ACCEPTED**
- `C1-I — Backend-owned tax-rate setting`: **IMPLEMENTED — EXACT-HEAD `/settings` SMOKE REQUIRED BEFORE MERGE** (not merged, not `DONE`)
- Backend baseline correction gate: **DONE**
- Merged `main` backend baseline: **GREEN**
- **Active runtime implementation slice: `C1-I`**, on branch `claude/c1-backend-owned-tax-rate-setting`, started from merged `origin/main` `80b83de3e838cf676669a1b627770300590c99c0`.

All four accepted backend baseline gate failures are closed on `main`. The accepted `CR-007` decision (PR #148, merged at `80b83de3e838cf676669a1b627770300590c99c0` from final reviewed head `577e0fd0b5c3e6fc82e2399fd17f023b6e221b83`) authorized exactly one bounded implementation slice, and that slice is now implemented on its PR branch.

## C1-I — implemented, not merged

Delivered on the PR branch, matching the accepted contract:

- `GET /api/settings/tax-rate` and `PUT /api/settings/tax-rate` in a dedicated router, service, schema, and domain-validation module, registered under the existing `/api/settings` namespace;
- persistence of the key `default_tax_rate` through the existing `app_settings` table — **no migration, no new table, no new column, no sentinel**;
- strict decimal-string validation with structured Russian errors (`invalid_tax_rate_type`, `invalid_tax_rate_format`, `tax_rate_precision_exceeded`, `tax_rate_out_of_range`), rejecting JSON numbers, `bool`, `NaN`, `Infinity`, scientific notation, commas at the API boundary, empty strings, negatives, values above `100`, and more than two fractional digits; `6.005` is rejected and never becomes `6.01`;
- the canonical exactly-two-decimal representation, persisted and returned;
- a backend-generated `effective_at` with a monotonic one-second tie-break for `default_tax_rate` only, stored as SQLite `YYYY-MM-DD HH:MM:SS` UTC text and exposed as ISO-8601 UTC;
- explicit Clear as deletion of the `default_tax_rate` row only, returning `is_configured: false`, `tax_rate_percent: null`, `effective_at: null`;
- exactly one atomic `tax_rate_setting_changed` / `app_setting` / `default_tax_rate` `AuditLog` per real mutation, rolling the persistence change back when the audit insert fails — proven for configure, change, and Clear alike;
- the no-op contract: no write, no delete, no timestamp change, no audit, no misleading message;
- the `Налоговая ставка для расчётов` section inside `/settings` with percentage input and `%` unit, Save, Cancel, explicit confirmed Clear, refresh, scoped pending state, field errors, and distinct mutation and refresh failures;
- the Settings Decision Matrix marking `default_tax_rate` — and only `default_tax_rate` — as newly editable;
- the legacy `tax.default_rate = "0.06"` placeholder proven byte-for-byte unchanged after configure, change, and Clear, and never read as a configured rate.

**Not implemented, by design:** readiness tax, confirmation tax, `ProductionBatch` snapshot columns, tax amount, margin, margin percent, report calculation changes, historical backfill or recalculation, tax regimes, and any accounting, invoicing, or filing feature.

Test evidence executed on the PR branch:

| Check | Result |
|---|---|
| Backend complete suite (`backend/`) | `671 collected, 671 passed, 0 failed, 0 skipped` |
| Original merged node IDs still collected | `562 / 562` |
| Targeted backend settings + tax suites | `123 passed, 0 failed, 0 skipped` |
| Frontend `npm run test:settings-tax-feedback` | `34 pass, 0 fail, 0 skipped` |
| All 13 focused frontend suites | `0 fail, 0 skipped` |
| Frontend `npm run build` | `PASS` |
| `frontend/src/main.ts` | `6406` before → `6399` after |

No existing test was deleted, renamed, skipped, `xfail`-ed, or weakened. Four existing Settings assertions were updated to the newly accurate editable set and capability wording; their node IDs and strictness are preserved.

The exact-head `/settings` browser smoke is **still required before merge**. `C1-I` is **not `DONE`** until it is reviewed and merged. **C2 remains blocked.**

## CR-007 — accepted C1 tax-setting decision

`CR-007 — Decide the C1 workshop tax-rate setting contract` is **accepted** (RECORDED PRODUCT-OWNER DECISION, 2026-07-27) and **not implemented**. The durable contract is `docs/settings.md` § “C1 — налоговая ставка для расчётов”, with the API shape in `docs/api.md`, snapshot semantics in `docs/domain-model.md` § 6.14, the report boundary in `docs/reports.md`, the ADR in `docs/decisions/0011-tax-rate-setting.md`, and the slice contract in `docs/implementation-plan.md` § 11.

- **One global setting** `default_tax_rate`, user-facing `Налоговая ставка для расчётов`. An internal planning estimate — never tax filing, a declaration, VAT accounting, legal advice, regime detection, or an accounting subsystem, and never labelled as a specific legal regime.
- **Percentage, not coefficient.** `6` and `6.00` mean `6%`; `0.06` means `0.06%`. `Decimal` only, decimal strings on the wire, never binary float, at most two fractional digits on input, range `0.00`–`100.00` inclusive. `6.005` is **rejected, never rounded**.
- **Canonical form is exactly two fractional digits**, persisted and in the API: `6` → `6.00`, `6.0` → `6.00`, `0` → `0.00`, `100` → `100.00`. Formatting is applied after validation and never absorbs excess precision; the no-op comparison uses that exact canonical string.
- **Taxable base is the order sale price.** `tax_amount = ROUND_MONEY(sale_price_snapshot × tax_rate_percent_snapshot ÷ 100)`, money quantum `0.01`, `ROUND_HALF_UP`, rounding only the final amount. Tax is deducted from gross revenue, never added on top.
- **Immediate effectiveness.** `effective_at` describes the **currently active setting**: backend-generated, with no backdating, scheduling, multiple active periods, or user-configurable effective date. New on first configuration and on a real change; unchanged on a no-op; **`null` after Clear**, since there is no active setting to timestamp — the clear time lives in `AuditLog.created_at`, and the clear metadata carries `previous_effective_at` plus `new_effective_at: null`. The stored source `AppSetting.updated_at` **stays** in SQLite's `YYYY-MM-DD HH:MM:SS` UTC format; the service normalizes it and only the API exposes ISO-8601 UTC.
- **History is immutable.** A rate change never modifies completed `ProductionBatch` rows, report snapshots, prior audit records, generated documents, or persisted tax/margin values. Future C2 snapshot columns are nullable and **never backfilled**.
- **Missing is not zero.** `null` produces a non-blocking warning, leaves tax and dependent margin unavailable, and does not block physical production; old rows show `Недоступно`; a configured `0.00` is a real value. No fabricated zero anywhere.
- **Explicit clear is row deletion.** `tax_rate_percent: null` — confirmed, warned about, audited, never retroactive; an empty string is not a backend substitute for `null`. `C1-I` deletes **only** the `default_tax_rate` `AppSetting` row through a bounded new `delete_setting(key, connection=None)` capability, and never deletes, reads, reinterprets, migrates, or rewrites the legacy `tax.default_rate` key. The delete and its `AuditLog` insert share one transaction; a failed audit insert rolls the deletion back. After a successful Clear the API returns `is_configured: false`, `tax_rate_percent: null`, `effective_at: null`. Clearing an absent row is a no-op — no delete, no timestamp change, no audit, no misleading changed message. **Not authorized:** a nullable-column migration, sentinel value, empty-string storage, new settings table, or parallel settings store; unconfigured is the absence of the row.
- **Atomic audit.** Every real mutation writes `tax_rate_setting_changed` / `app_setting` / `default_tax_rate` in the same transaction as the persistence change — upsert and delete alike — and rolls that change back if the audit write fails. Reads, validation failures, failed persistence, and no-ops are not audited.
- **C1 owns** the setting, validation, the effective timestamp, the GET/update API, explicit clear, the Settings UI, the atomic audit, persistence, and no-op behavior. **C2 owns** readiness estimates, stale-setting detection, `ProductionBatch` tax snapshots and their nullable migration, tax amount, margin and margin percent, reports from snapshots, and backward-compatibility tests. C2 stays blocked until C1 is merged and verified.

## C1-I — recorded repository constraints and how they were met

Recorded when the decision was accepted, verified read-only against `origin/main` at `09d11fc32db6ae57f99d522c4aa71e223e4e01a5`. Every constraint below was respected by the implementation:

- the seeded `app_settings` row `tax.default_rate = "0.06"` from `backend/app/migrations/versions/0001_infrastructure.py` is a **superseded coefficient-shaped placeholder** — use the distinct key `default_tax_rate`, and never read, reinterpret, migrate, rewrite, delete, or treat it as a configured rate; `default_tax_rate` and `tax.default_rate` are never conflated. The `tax_rate default 0.06` line in `docs/roadmap.md` and the coefficient formulas in `AGENTS.md` § 6.6, `docs/domain-model.md`, and `docs/architecture.md` § 8.6 were all corrected in the decision PR, so every active tax formula now reads `tax_rate_percent / 100` and no coefficient default for this setting is left anywhere;
- `SettingsRepository.upsert_setting` opens its own session and accepts no external connection, while `AuditLogRepository.create_log` already accepts one, so atomic setting+audit requires a **bounded optional-`connection` extension** of the existing settings repository — **no schema change, no new settings table, no new settings architecture**; if even that cannot satisfy atomicity, stop, record evidence, and update the contract first;
- `SettingsRepository` has no delete capability, so Clear-by-row-deletion needs one bounded new method equivalent to `delete_setting(key: str, connection=None)` using the same optional-`connection` pattern; it deletes a settings row by key and is **not** authorization for a schema change, nullable column, sentinel value, empty-string storage, new table, or parallel store;
- `app_settings.updated_at` is SQLite `CURRENT_TIMESTAMP` and **stays stored** as `YYYY-MM-DD HH:MM:SS` UTC; the service normalizes it and only the API exposes ISO-8601 UTC `effective_at`. The database does not store ISO-8601, and the column, its default, and migrations are unchanged;
- `upsert_setting` refreshes `updated_at` on every write, so the no-op contract requires a read-compare-then-write in the service;
- `quantize_percentage` must not be reused for validation, because it would silently round `6.005` to `6.01`;
- the Settings UI is inline in `frontend/src/main.ts` and no Settings test module exists, so a focused frontend test requires extracting a tax-setting feedback/presentation module into the existing focused-suite pattern without adding dependencies.

## R4 merge closure

`R4` is **DONE** (VERIFIED FROM REPOSITORY / GITHUB / MERGED PR EVIDENCE).

- PR #146 `R4 — Canonical backup/export filename reason normalization`, state `MERGED`
- Final reviewed head: `c505de2dc213ff75e0eb7cb5ffbcd180069a86fb`
- Merge commit: `127191feb182ccf68a4d7b9f2be28f6aa5b42453`
- Merged at: `2026-07-27T08:51:06Z`
- `origin/main` equals that merge commit; both the final head and the merge commit were verified as ancestors of `origin/main`.

Both original filename nodes are closed on `main`:

```text
app/tests/test_backups_api.py::test_backup_reason_defaults_empty_and_sanitizes_unsafe_characters
app/tests/test_exports_api.py::test_export_reason_defaults_empty_and_sanitizes_unsafe_characters
```

## Accepted merged evidence

All results below are **VERIFIED FROM REPOSITORY / GITHUB / MERGED PR EVIDENCE**. None of them was executed in the documentation task that wrote this section.

| Check | Accepted result |
|---|---|
| Backend complete suite | `562 collected, 562 passed, 0 failed, 0 skipped` |
| Frontend focused suite | `40 passed, 0 failed, 0 skipped` |
| Frontend production build | `PASS` |
| Focused exact-published-head `/backups` and `/exports` browser smoke | `PASS — FULL AUTOMATED SMOKE PASSED` |
| Exact smoke-tested head | `c505de2dc213ff75e0eb7cb5ffbcd180069a86fb` |

The merged slice involved **no frontend production change**, **no database migration**, **no filesystem migration**, and **no existing artifact renamed, rewritten, or deleted**.

## CR-005 status

`CR-005` remains **accepted** and is now **implemented**. The durable contract is unchanged and lives in `docs/backup-and-restore.md`, `docs/export.md`, and `docs/api.md`. The canonical filename reason segment is owned by the shared backend helper `normalize_artifact_reason_segment` in `backend/app/services/local_artifact_filenames.py`; the export JSON manifest continues to carry the normalized human reason.

`R4` is closed and is **not reopened**. `CR-005` is closed and is **not reopened**.

## CR-006 — export create-response fallback — NEEDS EVIDENCE, not active

`CR-006 — Investigate export create-response fallback confirmation semantics` is a new **`needs evidence`** row in `state/change-requests.md`. It is **not an active implementation slice** and is **non-blocking** for `R4` closure.

Exact current behavior in `backend/app/api/exports.py::create_export`:

- after `create_json_export` writes an export, the endpoint attempts to find the exact created file through `list_export_files`;
- when the exact file is found, the API response uses parsed filename metadata and therefore returns the canonical filename-derived reason;
- when the exact file is **not** found, the defensive fallback constructs an `ExportFile` using `ExportResult.reason`;
- `ExportResult.reason` is the normalized **human** reason preserved in the export manifest;
- therefore the fallback may return a human reason where the API contract normally expects the canonical filename-derived slug.

Classification: **NEEDS EVIDENCE.** This is **not** classified as a confirmed product defect. No user-visible failure has been reproduced. No data loss, overwrite, incorrect file content, or unsafe mutation is proven. The normal path is green in the backend suite, in create/list/status integration coverage, and in the exact-head browser smoke. Fallback reachability is not established, **no severity is assigned**, and **no correction design is authorized**.

`CR-006` is not part of `CR-004`, is not a reason to reopen `CR-005`, and is not a reason to reopen `R4`. It is **not** a fifth backend baseline failure. Full evidence: `docs/backend-baseline-failure-triage.md` §17.

## Remaining release obligations

None of these is activated here.

- `CR-004` — SQLite backup transaction-consistency investigation — remains a separate `needs evidence` row and is **not active**.
- Restore product decision and implementation remains **open**.
- Final macOS packaging and user-ready launch remains **open**.
- Installation verification remains **open**.
- Packaged update flow and update smoke remain **open**.
- Full release-candidate smoke remains **open**.
- C1 has an **accepted product contract** (`CR-007`) and its single authorized slice `C1-I` is **implemented on its PR branch and not merged**; the exact-head `/settings` smoke and review remain outstanding. C2, C3, and C4 remain **inactive** unless separately authorized, and C2 stays blocked until the C1 implementation is merged and verified.
- Continuing documentation accuracy remains an ongoing obligation. The durable `CR-005` contract documents `docs/backup-and-restore.md`, `docs/export.md`, and `docs/api.md` record the merged `R4` implementation status and agree with merged `main`.

**Product release readiness is not claimed.**
