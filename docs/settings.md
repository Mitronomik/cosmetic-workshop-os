# Settings

Settings (`/settings`) is a user-facing place to understand application/data status and edit the safe display-only Workshop profile. Settings must not become a technical admin panel.

## API

`GET /api/settings/status` returns:

- local-first app status;
- local data separation status;
- safe workflow capabilities;
- Settings Decision Matrix;
- `editable_settings_available: true`;
- copy explaining that the Workshop profile and the tax-rate setting are editable while the remaining calculation-sensitive settings remain a future backend-rule map.

`GET /api/settings/status` is read-only. It must not create files, mutate business data, trigger backup/export/import/demo/report-document actions, regenerate alerts or purchases, or change app configuration.

## Settings Decision Matrix

### Safe MVP candidates

The Workshop profile fields are editable now through `GET /api/settings/workshop-profile` and `PUT /api/settings/workshop-profile` with backend validation and `app_settings` persistence:

- workshop name;
- master name;
- workshop contact text;
- workshop note.

The tax-rate setting is editable now through `GET /api/settings/tax-rate` and `PUT /api/settings/tax-rate` with backend-owned Decimal validation, `app_settings` persistence under the key `default_tax_rate`, and an atomic `AuditLog` for every real mutation. It is the only calculation-sensitive setting that is editable, and it changes no historical record.

Other safe candidates remain future work:

- default report document format;
- backup reminder hint;
- hide demo hints after onboarding.

### Calculation-sensitive candidates

The default tax rate is **implemented and editable** (`CR-007` / `C1-I`, see “C1 — налоговая ставка для расчётов” below). It keeps `affects_calculations: true`, `affects_historical_data: true`, and `requires_backend_service: true`, and its safety note states that history is never recalculated.

These still require backend domain rules before becoming editable:

- currency display;
- target margin;
- default low-stock threshold;
- expiry warning days;
- default measurement units.

Calculation-sensitive settings can affect reports, production readiness, alerts, purchases, cost, tax, margin, or historical display. They must never silently mutate historical production batches, orders, stock movements, recipes, or reports.

### V2/V3 only

- document templates;
- labels;
- certificates;
- DOCX export;
- email sending;
- external integrations;
- cloud sync.

### Not planned for MVP

- roles and multi-user access;
- full accounting;
- advanced analytics;
- template marketplace.

## Rule for editable settings

A setting can become editable only when:

- it has a backend owner/service;
- it has validation;
- it has a safe default;
- it defines whether it applies only to future records or also to display;
- it does not silently mutate historical data;
- it has tests;
- it is documented.

Frontend must not own critical setting logic. If a setting affects calculations, stock, production, cost, tax, margin, alerts, purchases, reports, or historical interpretation, backend services must own the rules.

## Allowed future Settings PR examples

- PR98 uses saved Workshop profile fields in newly generated Markdown/PDF report overview documents without changing calculations or existing generated files.
- Add default report document format: backend-owned preference used only to preselect a creation option, while document creation remains explicit.
- Add backup reminder hint: UI guidance only, without scheduled jobs or automatic file creation.

Do not jump from PR95 directly to tax, currency, margin, unit, role/auth, cloud sync, integrations, templates, labels, certificates, accounting, scheduled jobs, or AI/RAG settings.

## PR96 — editable workshop profile

PR96 makes only the workshop profile editable. The editable fields are:

- `workshop_name` — workshop display name, max 120 characters;
- `master_name` — master/cosmetologist name, max 120 characters;
- `workshop_contact_text` — human-readable contact text, max 500 characters;
- `workshop_note` — short description/note, max 500 characters.

The profile is stored backend-side in the existing local `app_settings` key-value table under the grouped JSON key `workshop_profile`. No frontend `localStorage`, source-code file, hidden config file, backup/export/import/report document action, or new migration is used for this PR.

Validation is backend-owned: values are trimmed, empty strings are allowed, overlong values are rejected with Russian validation errors, and unsafe control characters are rejected. Phone/email formats are not required.

Profile values are display-only settings for Settings and future documents. They are not calculation inputs and do not mutate recipes, clients, orders, production batches, stock movements, reports, costs, taxes, margins, alerts, purchases, imports, exports, backups, or historical records. Calculation-sensitive settings such as tax, currency, margin, units, stock thresholds, and expiry warning days remain non-editable and require future backend rules.

## PR98 report-document behavior

Saved Workshop profile fields are display metadata for newly generated report documents. They do not affect recipes, clients, orders, production, stock, costs, taxes, margins, alerts, purchases, imports, exports, backups, demo data, or historical records. Existing documents are not mutated. No tax/currency/margin/unit/stock-threshold/expiry settings, template editor, logo upload, DOCX, invoices, labels, or certificates were added.

---

# C1 — налоговая ставка для расчётов (`default_tax_rate`)

Status: **ACCEPTED PRODUCT CONTRACT — IMPLEMENTED, MERGED, AND EXACT-HEAD VERIFIED (`C1-I`, PR #149).**

This section is the durable contract for the single global workshop tax-rate setting. It was decided as `CR-007` and is the first calculation-sensitive setting to receive a full backend contract.

**`C1-I` is `DONE`** (VERIFIED FROM MERGED PR EVIDENCE): PR #149 `C1-I — Implement backend-owned tax-rate setting` is `MERGED`, final reviewed head `1c01c05c861c4008ad6304210dbd65d9fd8dcdf9`, merge commit `ff7afe6b0778ab2b348229a4df34acf3e3fc0001`, merged at `2026-07-27T19:44:53Z`. Accepted evidence: backend `671 collected / 671 passed / 0 failed / 0 skipped`; focused tax-setting frontend suite `52 passed / 0 failed / 0 skipped`; all 13 focused frontend suites `568 passed / 0 failed / 0 skipped`; frontend production build `PASS`; exact-head `/settings` smoke `PASS — 146 checks / 0 failures` against head `1c01c05c861c4008ad6304210dbd65d9fd8dcdf9`. No migration was added. `frontend/src/main.ts` went from `6406` to `6399` lines. **The setting is implemented; nothing in it still awaits smoke.**

The merged slice implements sections 1–4 and 7–12 of this contract: the `GET`/`PUT` endpoints, Decimal-string validation, the canonical two-decimal representation, the backend-generated `effective_at`, explicit Clear as row deletion, the atomic `AuditLog`, the no-op contract, and the `/settings` UI. `default_tax_rate` is `editable_now` in the Settings Decision Matrix.

Sections 5, 6, and the tax/margin calculations in section 8 are **C2**. Readiness estimates them on merged `main` (`C2-I`, PR #151), and the `ProductionBatch` snapshot columns are on merged `main` too (`C2-II`, PR #152).

**C2 consumes this setting; it never changes it.** `CR-008` (ADR `docs/decisions/0012-c2-financial-calculation-snapshots.md`) decided the C2 calculation and snapshot contract and divided C2 into bounded slices:

- `C2-I` — backend financial readiness estimate: **IMPLEMENTED** and merged (PR #151);
- `C2-II` — transactional production financial snapshots, including `tax_rate_percent_snapshot` and `tax_rate_effective_at_snapshot`: **IMPLEMENTED** and merged (PR #152);
- `C2-III-A` — Order and `ProductionBatch` financial presentation: `DONE — MERGED AND EXACT-HEAD VERIFIED` (PR #154);
- `C2-III-B` — snapshot-backed reports and report documents: `DONE — MERGED AND EXACT-HEAD VERIFIED` (PR #157, merge commit `87410910aad472343c057f0bcbfcc3797f8b8e09`, merged `2026-07-28T22:21:18Z`). **C2 is `COMPLETED`.**
- `C3-I` — read-only AuditLog workspace: `AUTHORIZED AFTER THE CLOSURE DOCUMENTATION PR MERGES — NOT IMPLEMENTED`; contract `docs/audit-log.md`.

The current setting is **only ever an input to calculations**. It never recalculates history: changing or clearing it leaves every completed `ProductionBatch`, report value, prior audit record, and generated document exactly as it was. `C2-II` snapshots the active rate **and** its effective timestamp onto the `ProductionBatch` at confirmation time, in nullable columns that are never backfilled, and reports will read those snapshots only.

**Transaction-aware read boundary (`C2-II`).** The C1 service gained exactly one bounded read-only extension:

```python
TaxRateSettingsService.get_tax_rate(connection: sqlite3.Connection | None = None)
```

The no-argument call is unchanged and still opens its own short-lived session. When a caller supplies a connection, the service reads `default_tax_rate` through the existing `SettingsRepository` **on that exact connection**, so production confirmation observes the setting inside its own `BEGIN IMMEDIATE` transaction without opening a second connection while the write lock is held. The read performs no write, creates no `AuditLog`, and preserves the C1 validation and canonicalization boundaries. Reducing a setting response to the authoritative C2 context lives in one shared reducer, `backend/app/services/tax_rate_context.py`, used by both readiness and confirmation — there is no second tax-setting service, no raw `AppSetting` parsing inside the confirmation service, and no generic transaction service locator.

Full slice contracts: `docs/implementation-plan.md` § 11. C2 contract: `docs/decisions/0012-c2-financial-calculation-snapshots.md`.

## 1. Product meaning

The application supports one global workshop setting:

```text
default_tax_rate
```

User-facing name:

```text
Налоговая ставка для расчётов
```

It is an internal planning setting used to estimate tax from workshop sales.

It is **not**:

- tax filing;
- a tax declaration;
- VAT accounting;
- jurisdiction-specific legal advice;
- automatic identification of a tax regime;
- an invoice or accounting subsystem;
- a replacement for professional accounting.

The UI must explain:

```text
Ставка используется для внутренней оценки налога с цены продажи. Приложение не формирует налоговую отчётность.
```

The setting must never be labelled as a specific legal regime — no УСН, no НДС/VAT, no self-employment tax, no other jurisdiction-specific scheme. The user chooses the percentage.

## 2. Representation

The setting is a **percentage**, not a coefficient.

- `6` means `6%`;
- `6.00` means `6%`;
- `0.06` means `0.06%`, **not** `6%`.

Canonical backend representation:

- `Decimal`;
- persisted and transmitted as a **decimal string**;
- never a binary float;
- at most two fractional decimal places on input.

**Canonical form is exactly two fractional digits.** This is not a display preference; it is the stored and transmitted form.

- the persisted `default_tax_rate` value **always** uses exactly two fractional digits;
- the API `tax_rate_percent` value **always** uses exactly two fractional digits;
- canonical formatting is applied **after** validation, never as a way to absorb excess precision.

| Accepted input | Canonical persisted and API value |
|---|---|
| `6` | `6.00` |
| `6.0` | `6.00` |
| `6.00` | `6.00` |
| `0` | `0.00` |
| `100` | `100.00` |
| `6.005` | rejected — never `6.01` |

The no-op comparison in section 11 compares the **exact canonical two-decimal string**, so a request of `6` against a stored `6.00` is a no-op.

Allowed range:

```text
0.00 <= tax_rate_percent <= 100.00
```

Rules:

- `0.00` is a valid configured value and means an explicitly configured zero-percent tax estimate;
- missing/`null` is **not** the same as zero;
- negative values are invalid;
- values above `100` are invalid;
- `NaN`, `Infinity`, `bool`, `float` payloads, scientific notation where the existing Decimal rules prohibit it, and malformed values are invalid;
- a comma may be accepted in the user-facing input layer;
- the backend API contract stays decimal-string based.

Precision policy:

- at most two fractional digits;
- greater precision is **rejected**, not rounded;
- `6`, `6.0`, and `6.00` are equivalent;
- `6.005` is **invalid**, and must not silently become `6.01`.

Repository consequence: the existing `quantize_percentage` helper in `backend/app/domain/decimal_utils.py` quantizes to `PERCENT_QUANT = 0.01` with `ROUND_HALF_UP`, so it would silently round `6.005` to `6.01`. It must **not** be reused for tax-rate input validation. Use `parse_decimal` plus an explicit precision check that rejects excess fractional digits.

## 3. Taxable base

For the MVP the taxable base is the **order sale price**:

```text
taxable base = sale price paid by the customer
```

- the existing `Order.sale_price` is the editable source before production;
- the existing `ProductionBatch.sale_price` is the historical sale-price snapshot after production.

Tax is an internal expense estimate deducted from gross sale revenue for the future margin calculation. Tax is **not** added on top of `sale_price`.

MVP formula:

```text
tax_amount =
    ROUND_MONEY(
        sale_price_snapshot
        × tax_rate_percent_snapshot
        ÷ 100
    )
```

Do not subtract component cost, packaging cost, other cost, or margin from the taxable base.

Out of scope without a new product decision: expense-based tax regimes; fixed tax amounts; progressive brackets; minimum tax; deductions; VAT-inclusive/VAT-exclusive modes; multiple simultaneous rates; per-product, per-client, per-order, or per-batch tax categories and overrides.

## 4. Effective-time contract

The MVP uses **immediate effectiveness**. A successful setting change becomes effective at the backend-generated save timestamp.

Canonical concept: `effective_at`. It is the timestamp of the **currently active setting**, so it exists only while a rate is configured.

- `effective_at` is generated by the backend;
- the API exposes it as an **ISO-8601 UTC** timestamp;
- the user cannot backdate the rate;
- the user cannot schedule a future rate;
- the user cannot maintain multiple active rate periods;
- the user cannot edit `effective_at`.

Per-event behavior:

| Event | `effective_at` after the event |
|---|---|
| first configuration | new timestamp |
| real change of the configured rate | new timestamp |
| no-op save | unchanged |
| explicit Clear | `null` — there is no active setting to timestamp |
| no-op clear (already unconfigured) | stays `null`, nothing written |

Clear does **not** receive a new active-setting effective timestamp. It removes the active setting, so the API returns `effective_at: null`. The time at which the clear happened is recorded by `AuditLog.created_at`, and the clear audit metadata carries `previous_effective_at` — the former setting timestamp — and `new_effective_at: null`.

**Monotonic tie-break (`C1-I` implementation detail).** SQLite `CURRENT_TIMESTAMP` has one-second precision, so two real changes inside the same second would otherwise share an effective timestamp. The tax-setting service therefore generates the current UTC second itself and, when that second is not strictly later than the previous stored timestamp, persists the previous timestamp plus one second instead. The value is written explicitly for `default_tax_rate` only; no other setting uses this policy, the column, its default, and the migrations are unchanged, and the rate still becomes effective immediately. The timestamp is a logical ordering marker, never a user-scheduled future rate, and tests control the clock through service injection rather than `sleep()`.

**Storage wording.** The source value is the existing `AppSetting.updated_at` column, which stays persisted in SQLite's `YYYY-MM-DD HH:MM:SS` UTC format. The service normalizes that stored value into the ISO-8601 UTC `effective_at` the API exposes. The database does **not** store ISO-8601, and `C1-I` does not change the column, its default, or any migration.

A newly saved rate applies immediately to readiness checks requested after the save, production confirmations performed after the save, and other future C2 calculations.

It does **not** modify completed `ProductionBatch` rows, existing report snapshots, prior audit records, previously generated documents, or previously persisted tax/margin values.

An order created before a rate change but produced after it uses the rate active at production confirmation, unless a separately decided future financial-snapshot contract says otherwise.

No user-configurable effective date is included in MVP C1.

## 5. Readiness estimate semantics

C1 itself does **not** implement readiness tax calculation. The contract for the future C2 slice is nevertheless decided here:

- readiness uses the currently effective tax rate;
- readiness uses the current order `sale_price`;
- readiness tax is an **estimate**, not historical data;
- readiness is recalculated on each request;
- the readiness response must identify the tax rate used, the tax-setting effective timestamp, whether the rate is configured, and whether the tax result is available;
- the frontend displays backend-calculated values and never calculates tax itself.

When the tax setting changes after a readiness result was shown but before production confirmation:

- confirmation must not silently persist a different financial result;
- the backend must re-read the setting during confirmation;
- the backend must detect the stale financial-setting version/effective timestamp;
- confirmation must require a new readiness check through a structured conflict;
- no stock movement, batch, order-status change, or partial write may occur on that conflict.

The exact C2 API shape may be refined by the future C2 decision, but these semantics are mandatory.

**Refined by `CR-008`.** The C2 decision fixed the exact contract these semantics were waiting for, without changing them. The stale-setting conflict is HTTP `409` with the stable code **`tax_rate_context_stale`** — this supersedes the illustrative name `financial_settings_changed` used while `CR-007` was being decided. Readiness identifies the rate context through the additive fields `tax_rate_percent`, `tax_rate_effective_at`, and `financial_estimate_status`, reusing the existing `estimated_cost`, `estimated_tax`, and `estimated_margin` fields. Confirmation carries the required-but-nullable keys `expected_tax_rate_percent` and `expected_tax_rate_effective_at`, and reads the current setting inside the production transaction through a bounded `connection`-aware extension of the `C1` service.

`CR-008` also completed the defensive lifecycle this C1 contract left open. A missing `default_tax_rate` row and a persisted value that is invalid under the C1 validation rules above together form **`no valid configured tax-rate context`**: they stay distinguishable through the readiness warnings `tax_rate_missing` and `tax_rate_invalid`, but both return `tax_rate_percent = null` and `tax_rate_effective_at = null`, both leave tax and margin unavailable, both map to the single `null/null` confirmation context, and **neither blocks physical production**. The raw invalid value is never returned as an authoritative rate, never coerced or treated as `0.00`, and never persisted onto a `ProductionBatch`; production confirmation never repairs, clears, rewrites, or audits it, so the invalid row stays exactly as it is in `app_settings` for the user to fix through `/settings`.

Stated exactly, so the financial boundary and the repair surface are not confused:

```text
A raw invalid value is never exposed as an authoritative financial value
through C2 readiness or confirmation and is never persisted to a
ProductionBatch snapshot. The existing Settings repair surface may still read
the stored value so the user can replace or clear it.
```

That is why the shared reducer re-validates the percentage returned by `TaxRateSettingsService.get_tax_rate()` through the C1 domain parser instead of trusting `is_configured` alone, for both readiness (`C2-I`) and confirmation (`C2-II`). This wording narrows an over-broad reading of "never exposed"; it authorizes no change to `GET`/`PUT /api/settings/tax-rate`, whose behavior is unchanged.

Timestamps keep the C1 storage convention: `app_settings.updated_at` and `tax_rate_effective_at_snapshot` stay `YYYY-MM-DD HH:MM:SS` UTC SQLite text, while `effective_at`, the readiness rate context, the confirmation context, and the exposed snapshot all use `YYYY-MM-DDTHH:MM:SSZ`. `C2-II` routes every conversion between the two through one boundary, `backend/app/domain/tax_rate_timestamps.py`.

Full contract: `docs/decisions/0012-c2-financial-calculation-snapshots.md`.

## 6. Production snapshot semantics

C1 Settings implementation does not calculate or persist production tax. Future C2 must use **immutable** `ProductionBatch` snapshots:

| Field | Meaning |
|---|---|
| `ProductionBatch.sale_price` (exists) | taxable-base snapshot |
| `tax_rate_percent_snapshot` (future, nullable) | exact configured percentage used at confirmation |
| `tax_rate_effective_at_snapshot` (future, nullable) | exact backend effective timestamp/version used |
| `ProductionBatch.tax` (exists) | final rounded tax-amount snapshot |

No separate `taxable_amount_snapshot` is required in the MVP, because the taxable base is exactly the existing `ProductionBatch.sale_price`.

C2 may introduce the two nullable columns. Requirements:

- fields are nullable for backward compatibility;
- **no backfill** with the current rate;
- old rows stay unknown rather than receiving invented values;
- changing the current setting never changes a `ProductionBatch` snapshot;
- reports read production snapshots;
- reports never recalculate old tax using the current setting;
- exports preserve the stored snapshot values once introduced;
- the migration requires the normal backup-before-migration safety flow.

This decision authorizes the **product meaning** of those future fields. It does not authorize their implementation in this decision PR or in the `C1-I` Settings slice; they belong to C2, after C1 is merged and verified.

## 7. Missing-value behavior

**Missing tax rate:**

- represented as `null` / not configured;
- never treated as `0%`;
- UI text `Налоговая ставка не настроена`;
- produces a non-blocking financial warning;
- the tax estimate is unavailable;
- margin and margin percent are unavailable when they depend on tax;
- physical production readiness is **not** blocked solely by a missing tax rate;
- production may proceed, but the financial fields stay unavailable;
- the resulting historical batch keeps unknown tax fields as `null`;
- configuring a rate later does not populate or recalculate that batch.

**Explicit zero rate:**

- `0.00` is configured;
- the tax amount is `0.00` when the sale price is available;
- it must not display as unconfigured;
- margin may be calculated when every other required input is available.

**Missing sale price:**

- tax is unavailable even when a rate is configured;
- margin is unavailable;
- the UI explains that the sale price is required for financial estimates;
- physical production is not blocked solely because the sale price is missing, unless a separately accepted product rule later says otherwise.

**Missing total cost:**

- tax may still be calculated when the sale price and tax rate are available;
- margin and margin percent stay unavailable;
- the application must not invent a zero cost.

**Old `ProductionBatch` rows without tax snapshots:**

- show `Недоступно`;
- do not apply the current setting retroactively;
- do not infer a historical rate from the current configuration;
- do not rewrite historical rows.

No missing financial value may be displayed as a fabricated zero.

## 8. Money rounding

Use `Decimal` only, the project money quantum `0.01`, and `ROUND_HALF_UP` — the existing `MONEY_QUANT` and `ROUNDING_MODE` in `backend/app/domain/decimal_utils.py`.

Calculation order:

1. validate the canonical sale-price `Decimal`;
2. validate the stored tax-rate `Decimal`;
3. multiply using `Decimal`, never binary float;
4. divide by `100` using `Decimal`;
5. round **only the final tax amount** to money quantum `0.01`.

Do not repeatedly round intermediate multiplication values.

Required examples, which must appear in documentation and in future tests:

| Sale price | Rate | Tax |
|---|---|---|
| `1000.00` | `6.00` | `60.00` |
| `999.99` | `6.00` | `60.00` |
| `1.00` | `0.50` | `0.01` |
| `1.00` | `0.00` | `0.00` |
| any | missing | unavailable |
| missing | any | unavailable |

The exact margin and margin-percent rounding contract stays part of C2. This C1 decision defines only the tax contribution: future margin must use the **persisted rounded tax snapshot**, not a freshly recalculated current-rate value.

## 9. Clear / reset semantics

The setting may be explicitly cleared. API meaning: `tax_rate_percent: null`.

- `null` means clear/unconfigure;
- an empty string is **not** a backend substitute for `null`;
- the frontend may translate an explicit Clear action into `null`;
- clearing requires an explicit user action;
- the UI must warn that future financial estimates become unavailable;
- clearing does not alter historical `ProductionBatch` rows;
- clearing is audited;
- clearing an already missing setting is a no-op.

The setting must never be silently cleared because a text input is temporarily empty.

### Clear persistence — row deletion

Clear is **row deletion**, decided explicitly so that “unconfigured” has exactly one representation.

1. `tax_rate_percent: null` means explicit unconfigure.
2. `C1-I` deletes **only** the `default_tax_rate` `AppSetting` row.
3. It must **never** delete, read, reinterpret, migrate, or rewrite the legacy `tax.default_rate` placeholder row. The two keys are never conflated.
4. `C1-I` adds a bounded repository capability equivalent to `delete_setting(key: str, connection=None)`.
5. The delete and the `AuditLog` insert occur in **one transaction**.
6. If the audit insert fails, the deletion **rolls back** and the setting remains configured.
7. After a successful Clear the API returns `is_configured: false`, `tax_rate_percent: null`, and `effective_at: null`.
8. Clearing when no `default_tax_rate` row exists is a **no-op**: no delete, no timestamp change, no `AuditLog`, and no message claiming anything changed.
9. **Not authorized:** a nullable-column migration, a sentinel value, empty-string storage, a new settings table, or a parallel settings store. Unconfigured is the absence of the row and nothing else.

## 10. Audit contract

Every real tax-setting mutation must be audited: first configuration, rate change, and explicit clear.

Do **not** audit: `GET`/read; opening Settings; validation failure; failed persistence; a no-op save; a no-op clear.

The setting write and the `AuditLog` write must be **atomic**. If `AuditLog` creation fails, the tax-setting mutation must roll back and no partial change may remain. This applies to both mutation shapes: a configure/change **upsert**, and a Clear **row deletion** — a failed audit insert must leave the `default_tax_rate` row exactly as it was.

Recommended stable audit contract:

```text
action:      tax_rate_setting_changed
entity_type: app_setting
entity_id:   default_tax_rate
```

Human-readable summary examples:

- `Настроена налоговая ставка для расчётов.`
- `Изменена налоговая ставка для расчётов.`
- `Налоговая ставка для расчётов очищена.`

Safe metadata: `setting_key`; `previous_configured`; `new_configured`; `previous_rate_percent`; `new_rate_percent`; `previous_effective_at`; `new_effective_at`; `source: "settings"`.

For an explicit Clear specifically: `previous_configured: true`, `new_configured: false`, `new_rate_percent: null`, `previous_effective_at` holds the former setting timestamp, and `new_effective_at` is `null`. `AuditLog.created_at` is what records **when** the clear happened, since there is no longer an active setting to timestamp.

The tax rate itself is not treated as sensitive client data. Do not log the raw HTTP payload, the full settings JSON, stack traces, unrelated workshop profile fields, client data, or notes and other sensitive business content.

## 11. No-op contract

When the canonical persisted state would not change:

- return the current representation;
- do not write or delete the `AppSetting`;
- do not update `updated_at` / `effective_at`;
- do not create an `AuditLog`;
- do not show a misleading success message claiming the rate changed.

The comparison is made on the **exact canonical two-decimal string**, so a request of `6` against a stored `6.00` is a no-op.

Examples: saved `6.00` and request `6`; saved `0.00` and request `0`; setting missing and request clear/`null`.

## 12. UI contract

The future C1 implementation stays inside `/settings`. Do not create a separate accounting workspace.

User-facing section: `Налоговая ставка для расчётов`.

Required UI:

- one percentage input;
- a `%` suffix or adjacent unit label;
- help text explaining internal estimation;
- the current configured/unconfigured state;
- the effective timestamp in human-readable form when configured;
- Save, Cancel, and an explicit Clear action;
- confirmation before Clear;
- a structured field error;
- a pending state scoped to the tax-setting form;
- success feedback only after backend confirmation;
- mutation failure and refresh failure kept distinct;
- keyboard-accessible controls;
- no raw JSON, no API terminology, no tax-law or filing promises.

The frontend sends a decimal string or `null`, never stores the authoritative rate independently, never calculates tax, never calculates margin, never invents zero for a missing value, and re-renders from the confirmed backend response.

Suggested input examples: `6`, `6,5`, `0`.

Suggested helper text:

```text
Используется для внутренней оценки налога с цены продажи. Это не налоговая отчётность.
```

Suggested missing state:

```text
Ставка пока не настроена. Налог и маржа будут показаны как недоступные.
```

Do not add multiple tax modes, regimes, deductions, or accounting terminology.

## 13. Boundary between C1 and C2

**C1 — Settings — owns:** the persisted global default tax rate; Decimal validation; the backend-generated effective timestamp; the GET and update API; explicit clear; the Settings UI; the atomic `AuditLog`; persistence and reload behavior; no-op behavior; human-readable help and errors.

**C1 does not own:** tax calculation in readiness; tax calculation in production confirmation; `ProductionBatch` snapshot fields; margin calculation; margin-percent calculation; report calculations; historical migration or backfill.

**C2 — calculations and snapshots.** That gate is now satisfied: the C1 implementation is merged and exact-head verified, so C2 is no longer blocked on C1. C2 owns: the readiness tax estimate; stale-setting detection between readiness and confirmation; `ProductionBatch` tax snapshots; the nullable snapshot migration; the tax amount; margin and margin percent; reports using snapshots; old-record unavailable behavior; backward-compatibility tests.

C2 was not implemented inside the C1 implementation PR. Its product contract is `CR-008` / `docs/decisions/0012-c2-financial-calculation-snapshots.md`, which refines the cost and margin formulas without contradicting this accepted C1 tax decision. C2 ran as its own slice sequence: `C2-I` (PR #151), `C2-II` (PR #152), `C2-III-A` (PR #154) and `C2-III-B` (PR #157) are all merged and exact-head verified. **C2 is `COMPLETED`.**

## 14. Historical pre-C1 implementation baseline — superseded

> **HISTORICAL — NOT CURRENT REPOSITORY CLAIMS.** Every bullet in this section describes the repository baseline **before** `C1-I`, `C2-I`, and `C2-II` were implemented. They were verified read-only against `origin/main` at `09d11fc32db6ae57f99d522c4aa71e223e4e01a5` and are preserved **only for decision traceability** — they record the constraints the `CR-007` contract had to respect at decision time. They are **not** statements about the repository as it stands today. In particular, the transaction-aware settings read, the delete capability, the audited tax-setting mutation, the readiness tax and margin estimate, the `ProductionBatch` tax-rate snapshot columns, and the focused Settings frontend test module **all now exist** on merged `main`.
>
> For the current status, see § 13 *Boundary between C1 and C2* and the active C1/C2 lifecycle list near the top of this document: `C1-I` merged as PR #149, `C2-I` as PR #151, `C2-II` as PR #152, `C2-III-A` as PR #154 and `C2-III-B` as PR #157; **C2 is `COMPLETED`**. The durable C2 contract is `docs/decisions/0012-c2-financial-calculation-snapshots.md`, and the current lifecycle state of record is `state/current-focus.md`.

- **A coefficient-shaped placeholder row already exists.** `backend/app/migrations/versions/0001_infrastructure.py` seeds `app_settings` with key `tax.default_rate`, value `"0.06"`, `value_type` `decimal_string`, description `Default tax rate placeholder.`. Under this contract `0.06` would mean `0.06%`, not `6%`. That row is a **pre-decision placeholder and is not the decided setting**. `C1-I` must use the distinct key `default_tax_rate`, must not read, reinterpret, migrate, or rewrite `tax.default_rate`, and must not treat its presence as a configured rate. The same applies to the historical `tax_rate default 0.06` line in the `AppSettings MVP fields` block of `docs/roadmap.md`: it is superseded by this contract and is not a coefficient authorization.
- **Atomic setting + audit is not currently possible through the existing repository API.** `AuditLogRepository.create_log` in `backend/app/repositories/audit.py` accepts an optional `connection`, but `SettingsRepository.upsert_setting` in `backend/app/repositories/settings.py` opens its own `session(config)` and accepts no external connection, so the two writes cannot share one transaction today. The resolution is a **bounded signature extension** — add an optional `connection` parameter to the existing settings repository methods, matching the pattern `AuditLogRepository` and the production services already use — with **no schema change and no new settings architecture**. A new settings table, a parallel settings store, or a second persistence mechanism is **not** authorized. If implementation evidence shows even this bounded extension cannot satisfy atomicity, stop, record the evidence, and update this contract before writing the slice.
- **There is no delete capability today.** `SettingsRepository` exposes only `list_settings`, `get_setting`, and `upsert_setting`, so the decided Clear-by-row-deletion contract needs one bounded new method equivalent to `delete_setting(key: str, connection=None)`, sharing the same optional-`connection` pattern so the delete and its `AuditLog` insert run in one transaction. It is scoped to deleting a settings row by key; it is **not** authorization for a schema change, a nullable column, a sentinel value, empty-string storage, a new settings table, or a parallel store.
- **`app_settings.updated_at` is not ISO-8601 in storage.** The column defaults to SQLite `CURRENT_TIMESTAMP`, which persists `YYYY-MM-DD HH:MM:SS` in UTC without a `T` separator or offset, and it stays that way. The service normalizes that stored value and the API exposes `effective_at` as ISO-8601 UTC. Do not claim the database stores ISO-8601, and do not change the column type, its default, or any migration for this slice.
- **`upsert_setting` refreshes `updated_at` only in its `ON CONFLICT DO UPDATE` branch**, so any write bumps the timestamp. The no-op contract in section 11 therefore requires a read-compare-then-write in the service: an unchanged canonical value must not reach the repository at all.
- **No settings mutation is audited today.** `WorkshopProfileSettingsService.update_profile` writes no `AuditLog`. The tax setting will be the first audited settings mutation. This decision does **not** authorize retroactively adding audit to the workshop profile; that would be a separate slice.
- **Readiness already behaves as this contract requires.** On merged `main`, `backend/app/services/production_readiness.py::_estimate_money` returns `estimated_tax = None` and `estimated_margin = None`, and emits the `tax_rate_missing` warning `Налоговая ставка пока не настроена, поэтому налог и маржа не рассчитаны.` when a sale price exists. `frontend/src/order-readiness-presentation.ts` renders those through `moneyOrMissing` and states that the interface does not substitute a tax rate itself. C1 does not change this. *(This records the pre-`C2-I` state. `C2-I`, merged as PR #151, replaced `_estimate_money` with `_estimate_financials` plus the pure `backend/app/domain/production_financials.py` and activated the estimate. The `tax_rate_missing` code and message are preserved unchanged, and the frontend presentation stays untouched until `C2-III-A`.)*
- **Production confirmation already snapshots the sale price only.** `backend/app/services/production_confirmation.py` creates the batch with `sale_price=locked_order.sale_price` and explicit `tax=None, margin=None, margin_percent=None`.
- **The snapshot columns are decimal-string friendly.** In `backend/app/migrations/versions/0013_production_batches.py`, `sale_price`, `tax`, `margin`, and `margin_percent` are nullable `TEXT`, so the future C2 snapshot columns can follow the same nullable `TEXT` decimal-string pattern.
- **Reports do not invent tax.** `docs/reports.md` already states that tax is not invented or recalculated by reports, and `backend/app/services/reports.py` contains no tax calculation.
- **There is no Settings frontend test module.** The Settings UI lives inline in `frontend/src/main.ts` (`settingsPage`, `settingsWorkshopProfileCard`), and focused frontend suites follow the `frontend/src/*-feedback.ts` + `frontend/test/*.test.mjs` + `tsconfig.test.*.json` + npm-script pattern. A focused `C1-I` frontend test therefore requires extracting a tax-setting feedback/presentation module into that existing pattern, without adding dependencies.
