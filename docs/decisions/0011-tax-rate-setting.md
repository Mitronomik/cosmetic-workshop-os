# ADR - Workshop tax-rate setting (C1)

## Status

Accepted — 2026-07-27. Recorded as `CR-007`. Implemented by `C1-I` and merged as PR #149.

`C1-I` status: **`DONE — MERGED AND EXACT-HEAD VERIFIED`** (VERIFIED FROM REPOSITORY / GITHUB / MERGED PR EVIDENCE).

| Item | Value |
|---|---|
| Implementation PR | #149 — `C1-I — Implement backend-owned tax-rate setting` |
| Final reviewed head | `1c01c05c861c4008ad6304210dbd65d9fd8dcdf9` |
| Merge commit | `ff7afe6b0778ab2b348229a4df34acf3e3fc0001` |
| Merged at | `2026-07-27T19:44:53Z` |
| Exact-head `/settings` smoke | `PASS — 146 checks / 0 failures` |

Nothing in `C1-I` still awaits smoke, review, or merge. The accepted `CR-007` product decision below is unchanged and is not reopened.

The C2 calculation, confirmation-context, and snapshot contract is a separate decision, `CR-008` / `docs/decisions/0012-c2-financial-calculation-snapshots.md`. It does not reopen `CR-007`.

### Implementation note — monotonic effective timestamp

`C1-I` added one implementation detail this decision did not specify. SQLite `CURRENT_TIMESTAMP` has one-second precision, so two real rate changes inside the same second would receive the same `effective_at` and break the “new timestamp on a real change” rule. The tax-setting service generates the current UTC second and, when it is not strictly later than the previous stored timestamp, persists the previous timestamp plus one second. It is written explicitly for `default_tax_rate` only, changes no column, default, or migration, keeps the rate effective immediately, and is a logical ordering marker rather than a scheduled future rate. Tests inject the clock instead of sleeping. This does not become a global settings policy.

## Context

`default_tax_rate` was the first calculation-sensitive Settings candidate to be scheduled for implementation, but it had no product contract. `docs/settings.md` only classified it as `requires_backend_rules`, and the surrounding repository state was ambiguous in ways that would have produced silently wrong money:

- `backend/app/migrations/versions/0001_infrastructure.py` seeds `app_settings` with `tax.default_rate = "0.06"`, a coefficient-shaped placeholder; at decision time `docs/roadmap.md` repeated `tax_rate default 0.06`, and `AGENTS.md` § 6.6, `docs/domain-model.md`, and `docs/architecture.md` § 8.6 all wrote the tax formula without dividing by 100 — none of which said whether the user enters `6` or `0.06`. Every one of those documents was corrected in the decision PR;
- production readiness already returns `estimated_tax = null` with the warning `Налоговая ставка пока не настроена`, and production confirmation already snapshots `sale_price` while writing `tax`, `margin`, and `margin_percent` as `NULL`, so the missing-value path exists but has no defined completion;
- historical `ProductionBatch` rows must never be silently recalculated, so the effective-time and snapshot semantics had to be decided before any rate could be persisted.

Without a decision, the implementation would have had to guess the representation, the taxable base, the effective-time behavior, and the meaning of a missing value.

## Decision

One global setting, `default_tax_rate`, user-facing `Налоговая ставка для расчётов`: an internal planning estimate, never tax filing, a declaration, VAT accounting, legal advice, regime detection, or an accounting subsystem.

- **Percentage, not coefficient.** `6` and `6.00` mean `6%`; `0.06` means `0.06%`. `Decimal` only, decimal strings on the wire, never binary float, at most two fractional digits on input, range `0.00`–`100.00`. Excess precision is rejected, never rounded.
- **Canonical form is exactly two fractional digits**, both persisted and in the API: `6` → `6.00`, `6.0` → `6.00`, `0` → `0.00`, `100` → `100.00`. Formatting happens after validation and never absorbs excess precision, so `6.005` is rejected rather than becoming `6.01`. The no-op comparison uses that exact canonical string.
- **Taxable base is the order sale price.** `tax_amount = ROUND_MONEY(sale_price × tax_rate_percent ÷ 100)`, money quantum `0.01`, `ROUND_HALF_UP`, rounding only the final amount. Tax is deducted from gross revenue, never added on top.
- **Immediate effectiveness.** `effective_at` is the timestamp of the currently active setting: backend-generated, no backdating, no scheduling, no multiple active periods, no user-configurable effective date. New on first configuration and on a real change; unchanged on a no-op; **`null` after Clear**, with the clear time recorded by `AuditLog.created_at` and the clear metadata carrying `previous_effective_at` plus `new_effective_at: null`. The stored source is `AppSetting.updated_at`, which stays in SQLite's `YYYY-MM-DD HH:MM:SS` UTC format — the service normalizes it and only the API exposes ISO-8601.
- **Clear is row deletion.** `tax_rate_percent: null` deletes the `default_tax_rate` `AppSetting` row through a bounded new `delete_setting(key, connection=None)` capability, in the same transaction as its `AuditLog` insert, rolling the deletion back if that insert fails. It never touches the legacy `tax.default_rate` key. Clearing an absent row is a no-op. Unconfigured is the absence of the row — no nullable column, sentinel, empty string, new table, or parallel store.
- **Immutable history.** Changing the rate never modifies completed batches, report snapshots, prior audit records, or generated documents. Future C2 snapshots the rate and its effective timestamp onto `ProductionBatch` in nullable columns that are never backfilled.
- **Missing is not zero.** A missing rate is `null`, produces a non-blocking warning, leaves tax and dependent margin unavailable, and does not block physical production. A configured `0.00` is a real value. No missing financial value is ever displayed as a fabricated zero.
- **Atomic audit.** Every real mutation writes `tax_rate_setting_changed` / `app_setting` / `default_tax_rate` in the same transaction as the setting write; reads, validation failures, and no-ops are not audited.
- **C1/C2 boundary.** C1 owns the setting, its validation, its API, its UI, and its audit. Readiness estimates, confirmation calculation, snapshot fields, margin, and report calculation are C2 and stay blocked until C1 is merged and verified. *(That gate is satisfied: `C1-I` is merged and exact-head verified. C2 is no longer blocked on C1 and is gated by its own slice sequence under `CR-008` — only `C2-I` is authorized after the `CR-008` decision PR merges, with `C2-II` and `C2-III` blocked behind it. The ownership boundary itself is unchanged.)*

The full durable contract is `docs/settings.md` § “C1 — налоговая ставка для расчётов”. The API shape is `docs/api.md`, the snapshot semantics `docs/domain-model.md` § 6.14, the report boundary `docs/reports.md`, and the authorized implementation slice `C1-I` is specified in `docs/implementation-plan.md` § 11.

## Alternatives considered

- **Store a coefficient (`0.06`) to match the existing seed row and `AGENTS.md` § 6.6.** Rejected: non-technical users enter `6`, and a coefficient input makes a hundred-fold error indistinguishable from a valid entry. The seeded `tax.default_rate` row is instead left untouched as a superseded placeholder, and the new setting uses a distinct key.
- **Silently round excess precision to two decimals.** Rejected: `6.005 → 6.01` changes money the user never approved. Rejection is visible and correctable; rounding is not.
- **Treat a missing rate as `0%`.** Rejected: it fabricates a financial result and would make an unconfigured workshop look fully profitable.
- **User-configurable effective dates or multiple rate periods.** Rejected for the MVP: it requires a period model, overlap rules, and retroactive-recalculation policy that the local-first MVP does not need.
- **Recalculate historical batches when the rate changes.** Rejected outright: it violates the project's hard constraint on preserving historical production data.
- **Add a dedicated tax-settings table.** Rejected: the existing `app_settings` key-value mechanism is sufficient; only a bounded optional-`connection` extension of `SettingsRepository`, plus one `delete_setting` method, is authorized, so a mutation and its audit record can share one transaction.
- **Represent “cleared” as a stored sentinel — an empty string, a nullable column, or a magic value — instead of deleting the row.** Rejected: it creates two representations of “unconfigured” that can disagree, invites `"" == 0` bugs in exactly the place where missing must never equal zero, and would need a schema change the slice is not authorized to make. Deleting the row makes absence the single representation.
- **Give Clear its own `effective_at`.** Rejected as incoherent: `effective_at` describes the currently active setting, and after a Clear there is none. The clear event is a historical fact, so it belongs in `AuditLog.created_at`, with `previous_effective_at` preserved in the audit metadata.
- **Treat the two-decimal form as a display convention and store whatever the user typed.** Rejected: the no-op comparison then has to normalize on every read, and `6` versus `6.00` becomes a spurious change with a spurious audit record. Canonicalizing once, after validation, keeps comparison exact.

## Consequences

Positive:
- money semantics are unambiguous before any code is written, including the input unit, the base, the rounding order, and the meaning of missing;
- historical production data stays immutable by contract, not by accident;
- the first audited settings mutation establishes the atomic setting+audit pattern for later calculation-sensitive settings;
- “unconfigured” has exactly one representation — the row is absent — so there is no sentinel that can drift out of agreement with it;
- C2 inherits a decided readiness, stale-setting, and snapshot contract instead of inventing one.

Negative:
- the seeded `tax.default_rate` row remains in the repository as a superseded placeholder, so future readers must be told which key is authoritative; the roadmap's `0.06` line, `AGENTS.md` § 6.6, `docs/domain-model.md`, and `docs/architecture.md` § 8.6 were all corrected in the decision PR, so no coefficient formula for this setting is left anywhere;
- `SettingsRepository` needs a signature extension and one new `delete_setting` method before a mutation can be written atomically with its audit record;
- Clear destroys the previous rate rather than versioning it, so the only record of what the rate used to be is the `AuditLog` metadata;
- users cannot backdate or schedule a rate, so a mid-period rate change is only correct for production confirmed after the change;
- until C2 lands, configuring a rate visibly changes nothing in readiness or production, which must be explained in the UI.
