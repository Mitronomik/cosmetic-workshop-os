# ADR - Workshop tax-rate setting (C1)

## Status
Accepted — 2026-07-27. Recorded as `CR-007`. Not implemented.

## Context

`default_tax_rate` was the first calculation-sensitive Settings candidate to be scheduled for implementation, but it had no product contract. `docs/settings.md` only classified it as `requires_backend_rules`, and the surrounding repository state was ambiguous in ways that would have produced silently wrong money:

- `backend/app/migrations/versions/0001_infrastructure.py` seeds `app_settings` with `tax.default_rate = "0.06"`, a coefficient-shaped placeholder, and `docs/roadmap.md` repeats `tax_rate default 0.06`, while `AGENTS.md` § 6.6 writes `tax = sale_price * tax_rate` — none of which says whether the user enters `6` or `0.06`;
- production readiness already returns `estimated_tax = null` with the warning `Налоговая ставка пока не настроена`, and production confirmation already snapshots `sale_price` while writing `tax`, `margin`, and `margin_percent` as `NULL`, so the missing-value path exists but has no defined completion;
- historical `ProductionBatch` rows must never be silently recalculated, so the effective-time and snapshot semantics had to be decided before any rate could be persisted.

Without a decision, the implementation would have had to guess the representation, the taxable base, the effective-time behavior, and the meaning of a missing value.

## Decision

One global setting, `default_tax_rate`, user-facing `Налоговая ставка для расчётов`: an internal planning estimate, never tax filing, a declaration, VAT accounting, legal advice, regime detection, or an accounting subsystem.

- **Percentage, not coefficient.** `6` and `6.00` mean `6%`; `0.06` means `0.06%`. `Decimal` only, decimal strings on the wire, never binary float, at most two fractional digits, range `0.00`–`100.00`. Excess precision is rejected, never rounded.
- **Taxable base is the order sale price.** `tax_amount = ROUND_MONEY(sale_price × tax_rate_percent ÷ 100)`, money quantum `0.01`, `ROUND_HALF_UP`, rounding only the final amount. Tax is deducted from gross revenue, never added on top.
- **Immediate effectiveness.** A backend-generated ISO-8601 UTC `effective_at`; no backdating, no scheduling, no multiple active periods, no user-configurable effective date. A no-op does not move it.
- **Immutable history.** Changing the rate never modifies completed batches, report snapshots, prior audit records, or generated documents. Future C2 snapshots the rate and its effective timestamp onto `ProductionBatch` in nullable columns that are never backfilled.
- **Missing is not zero.** A missing rate is `null`, produces a non-blocking warning, leaves tax and dependent margin unavailable, and does not block physical production. A configured `0.00` is a real value. No missing financial value is ever displayed as a fabricated zero.
- **Atomic audit.** Every real mutation writes `tax_rate_setting_changed` / `app_setting` / `default_tax_rate` in the same transaction as the setting write; reads, validation failures, and no-ops are not audited.
- **C1/C2 boundary.** C1 owns the setting, its validation, its API, its UI, and its audit. Readiness estimates, confirmation calculation, snapshot fields, margin, and report calculation are C2 and stay blocked until C1 is merged and verified.

The full durable contract is `docs/settings.md` § “C1 — налоговая ставка для расчётов”. The API shape is `docs/api.md`, the snapshot semantics `docs/domain-model.md` § 6.14, the report boundary `docs/reports.md`, and the authorized implementation slice `C1-I` is specified in `docs/implementation-plan.md` § 11.

## Alternatives considered

- **Store a coefficient (`0.06`) to match the existing seed row and `AGENTS.md` § 6.6.** Rejected: non-technical users enter `6`, and a coefficient input makes a hundred-fold error indistinguishable from a valid entry. The seeded `tax.default_rate` row is instead left untouched as a superseded placeholder, and the new setting uses a distinct key.
- **Silently round excess precision to two decimals.** Rejected: `6.005 → 6.01` changes money the user never approved. Rejection is visible and correctable; rounding is not.
- **Treat a missing rate as `0%`.** Rejected: it fabricates a financial result and would make an unconfigured workshop look fully profitable.
- **User-configurable effective dates or multiple rate periods.** Rejected for the MVP: it requires a period model, overlap rules, and retroactive-recalculation policy that the local-first MVP does not need.
- **Recalculate historical batches when the rate changes.** Rejected outright: it violates the project's hard constraint on preserving historical production data.
- **Add a dedicated tax-settings table.** Rejected: the existing `app_settings` key-value mechanism is sufficient; only a bounded optional-`connection` extension of `SettingsRepository` is authorized, so the setting and its audit record can share one transaction.

## Consequences

Positive:
- money semantics are unambiguous before any code is written, including the input unit, the base, the rounding order, and the meaning of missing;
- historical production data stays immutable by contract, not by accident;
- the first audited settings mutation establishes the atomic setting+audit pattern for later calculation-sensitive settings;
- C2 inherits a decided readiness, stale-setting, and snapshot contract instead of inventing one.

Negative:
- the existing seeded `tax.default_rate` row and the roadmap's `0.06` line remain in the repository as superseded placeholders, so future readers must be told which one is authoritative;
- `SettingsRepository` needs a signature extension before the setting can be written atomically with its audit record;
- users cannot backdate or schedule a rate, so a mid-period rate change is only correct for production confirmed after the change;
- until C2 lands, configuring a rate visibly changes nothing in readiness or production, which must be explained in the UI.
