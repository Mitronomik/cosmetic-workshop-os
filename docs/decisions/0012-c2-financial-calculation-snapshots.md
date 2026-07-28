# ADR - C2 financial calculation and immutable production snapshots

## Status

Status: **Accepted**

Date: **2026-07-27**

Accepted — 2026-07-27. Recorded as `CR-008`.

`C1` is closed: `CR-007` was decided in PR #148 and the single authorized slice `C1-I — Implement backend-owned tax-rate setting` was merged as PR #149. This ADR decides what `C2` means, divides it into bounded slices, and authorizes exactly one of them.

Authorization state of each slice:

| Slice | Status |
|---|---|
| `C2-I` — backend financial readiness estimate | `AUTHORIZED AFTER THIS PR MERGES — NOT IMPLEMENTED` |
| `C2-II` — transactional production financial snapshots | `PLANNED — BLOCKED` on merged and verified `C2-I` |
| `C2-III` — human-readable presentation and snapshot-backed reports | `PLANNED — BLOCKED` on merged and verified `C2-II` |

Nothing in this ADR is implemented on `main`. No migration exists, no snapshot column exists, no tax or margin is calculated, and reports contain no snapshot logic.

**Relationship to ADR 0011.** ADR 0011 remains the authoritative C1 tax-setting decision and now records `C1-I` as merged and verified — PR #149, final reviewed head `1c01c05c861c4008ad6304210dbd65d9fd8dcdf9`, merge commit `ff7afe6b0778ab2b348229a4df34acf3e3fc0001`, merged `2026-07-27T19:44:53Z`, exact-head `/settings` smoke `PASS — 146 checks / 0 failures`. ADR 0012 does not reopen `CR-007`; it defines the C2 calculation, confirmation-context, and snapshot contract.

**Naming refinement over ADR 0011.** While `CR-007` was being decided, the stale-setting conflict was described illustratively as "a structured conflict such as `financial_settings_changed`". `CR-008` fixes the exact stable code as `tax_rate_context_stale` with HTTP `409`. This is a naming decision inside the boundary `CR-007` explicitly assigned to C2; no `CR-007` semantics change.

## Context

`C1` gave the workshop one backend-owned tax-rate setting and nothing else. The merged `C1-I` slice added `GET`/`PUT /api/settings/tax-rate`, the canonical percentage contract, explicit Clear as row deletion, and an atomic audit — but it deliberately calculated nothing. The current state on merged `main`, verified read-only at `ff7afe6b0778ab2b348229a4df34acf3e3fc0001`:

- `backend/app/services/production_readiness.py::_estimate_money` produces `estimated_cost` when both ingredient and packaging costs are known, and always returns `estimated_tax = None` and `estimated_margin = None`. It emits `cost_data_missing`, `sale_price_missing`, or `tax_rate_missing` as **non-blocking warnings** and never reads the tax setting;
- `backend/app/schemas/production_readiness.py::ProductionReadinessResponse` already declares `estimated_cost`, `estimated_tax`, and `estimated_margin`, so the response fields exist but are inert;
- `backend/app/services/production_confirmation.py` creates the `ProductionBatch` with the authoritative locked-order `sale_price`, real `component_cost`, `packaging_cost`, `other_cost`, and `total_cost`, and explicit `tax=None, margin=None, margin_percent=None`;
- `ProductionBatch` has nullable `sale_price`, `total_cost`, `tax`, `margin`, and `margin_percent` (`0013_production_batches.py`, all nullable `TEXT`), and has **no** `tax_rate_percent_snapshot` and **no** `tax_rate_effective_at_snapshot`;
- `backend/app/schemas/production_batches.py::ProductionConfirmRequest` contains exactly `confirm` and `notes`. There is no `backend/app/schemas/production_confirmation.py`;
- `TaxRateSettingsService.get_tax_rate()` takes no connection argument, while `SettingsRepository.get_setting(key, connection=None)` already accepts one;
- reports contain no tax calculation and no snapshot reads;
- no migration implements any part of `C2`;
- `frontend/src/main.ts` is `6399` lines.

Without a decision, `C2` would be one large ambiguous slice touching readiness, confirmation, a migration, reports, and the UI at once, and the calculation semantics — what a missing input means, whether a negative margin is real, what happens when the sale price is zero, and what happens when the rate changes between readiness and confirmation — would be guessed at implementation time, in code that produces money.

## Decision

`C2` implements a backend-owned financial estimate and an immutable per-production financial snapshot, using the simplified percentage-of-sale model already accepted in `CR-007`. It is divided into three bounded slices, and only the first is authorized by this ADR.

### Product boundary

`C2` is an **internal operational estimate for the workshop**. It is not:

- tax filing;
- a tax declaration;
- VAT accounting;
- automatic tax-regime selection;
- УСН, ОСНО, НПД, ПСН, АУСН, or ЕСХН calculation;
- insurance-contribution accounting;
- minimum-tax calculation;
- annual or quarterly tax accounting;
- marketplace tax accounting;
- invoicing;
- bookkeeping;
- legal or tax advice.

The current setting and calculation are **not** renamed to a "tax reserve" by this decision.

```text
The simplified tax model is accepted for the current MVP and may be replaced by
a separately decided future tax-regime model. Existing historical snapshots
must remain immutable after such a replacement.
```

### Authoritative input sources

Every authoritative monetary value is backend-owned:

| Input | Source |
|---|---|
| sale price | the authoritative `Order` sale price |
| readiness total cost | the existing backend readiness cost estimate |
| confirmation total cost | the actual authoritative cost produced by the transactional production-confirmation flow |
| tax rate | the current `default_tax_rate` state from the backend tax-rate service |
| tax-rate effective timestamp | the current backend-owned `effective_at` |

The frontend never supplies an authoritative monetary value and never calculates total cost, tax, margin, or margin percent. Its only financial input responsibility is to pass back, unchanged, the latest backend-returned tax-rate context during production confirmation (`C2-II`).

The legacy `tax.default_rate = "0.06"` row remains a superseded placeholder. `C2` reads `default_tax_rate` and never `tax.default_rate`.

### Formula contract

`Decimal` only. Never binary float, at any intermediate step.

```text
tax_amount =
ROUND_MONEY(
  sale_price × tax_rate_percent / 100
)
```

```text
margin =
ROUND_MONEY(
  sale_price
  - total_cost
  - tax_amount
)
```

```text
margin_percent =
ROUND_PERCENT(
  margin / sale_price × 100
)
```

- `tax_rate_percent` is a **percentage**, not a coefficient — `6.00` means `6%`;
- money quantum `0.01`, `ROUND_HALF_UP`; percentage quantum `0.01`, `ROUND_HALF_UP`;
- round only the final amount of each formula, never intermediate products;
- tax is **deducted from** gross revenue and is never added on top of the sale price;
- a configured `0.00` rate produces tax `0.00`;
- a missing rate produces tax `null`, never a fabricated zero;
- a missing sale price produces tax `null`;
- margin may be positive, zero, or **negative**; a negative margin is valid information and must never be clamped;
- margin is `null` when the sale price, the total cost, or the tax amount is unavailable;
- margin percent is computed only when margin is available **and** the sale price is greater than zero;
- a negative margin may produce a negative margin percent, which is never clamped to `0%`;
- no missing input is ever silently converted to zero.

### Missing-value matrix

| Sale price | Total cost | Tax rate | Tax | Margin | Margin % | `financial_estimate_status` |
|---|---|---|---|---|---|---|
| present, `> 0` | present | configured | available | available | available | `available` |
| present, `= 0` | present | configured | `0.00` | available | **unavailable** | `partial` |
| present | missing | configured | available | unavailable | unavailable | `partial` |
| present | present | missing | unavailable | unavailable | unavailable | `unavailable` |
| missing | any | any | unavailable | unavailable | unavailable | `unavailable` |
| any | any | invalid persisted value | unavailable | unavailable | unavailable | `unavailable` |

A configured `0.00` rate is **configured, not missing**: tax is `0.00`, margin uses zero tax, and margin percent follows the normal sale-price rule.

Physical production is **never blocked** by financial absence in any row of this matrix.

### Invalid persisted tax-rate value

A defensive local-first data-corruption case, not a normal API flow. `C1-I` validates every value it writes, so this can only arise from data edited outside the application.

- do not calculate with the invalid value;
- do not coerce it, and do not treat it as zero;
- do not expose the raw invalid value as an authoritative rate;
- treat the whole financial estimate as unavailable;
- return the safe non-blocking readiness warning `tax_rate_invalid`;
- do not convert the readiness request into an unhandled HTTP `500`;
- do not block physical production because of it.

### No valid configured tax-rate context

**`no valid configured tax-rate context`** is either of two backend states:

1. no `default_tax_rate` row exists; or
2. the persisted `default_tax_rate` value exists but is invalid and cannot be safely interpreted as the canonical C1 percentage.

The two states stay **distinguishable through readiness warnings** but produce **the same authoritative financial context**:

| Backend state | Readiness warning | `tax_rate_percent` | `tax_rate_effective_at` | Status | Tax / margin / margin % | Physical production |
|---|---|---|---|---|---|---|
| row absent | `tax_rate_missing` | `null` | `null` | `unavailable` | `null` | not blocked |
| value invalid | `tax_rate_invalid` | `null` | `null` | `unavailable` | `null` | not blocked |

The invalid case must **not** also emit `tax_rate_missing`, and must not produce an unhandled HTTP `500`.

The raw invalid persisted value must never be returned as the authoritative rate, and must never be normalized, coerced, rounded, treated as zero, copied into a readiness DTO, copied into a confirmation request, or copied into a `ProductionBatch` snapshot.

This is the reason the confirmation context in `C2-II` uses a single `null/null` pair for both states: readiness cannot express an invalid rate as an authoritative value, so requiring a distinct confirmation context for it would make the request impossible to construct and would indirectly block physical production — which the physical-production invariant forbids.

### Exact timestamp contract

| Surface | Canonical format |
|---|---|
| database persistence — `AppSetting.updated_at`, future `tax_rate_effective_at_snapshot` | `YYYY-MM-DD HH:MM:SS` |
| API and confirmation context — `effective_at`, readiness `tax_rate_effective_at`, `expected_tax_rate_effective_at`, exposed snapshot | `YYYY-MM-DDTHH:MM:SSZ` |

Storage is UTC, second precision, SQLite text, with no `T`, no `Z`, and no offset, following the existing C1 storage convention. The API form is UTC, second precision, with a literal `T` and a literal `Z` — for example `2026-07-27T19:44:53Z`.

Not accepted and not documented anywhere in C2: local-time values, arbitrary offsets such as `+03:00`, fractional seconds, a space instead of `T`, a missing `Z`, or user-generated timestamps. `expected_tax_rate_effective_at` must be either `null` or the **exact** canonical timestamp previously returned by readiness; anything else is HTTP `422` with `invalid_tax_rate_context`.

The API must never expose the raw SQLite storage representation. The confirmation response and the `ProductionBatch` detail response normalize `tax_rate_effective_at_snapshot` to the canonical `Z` form. No backfill is authorized.

### Preserved warning-code semantics

Financial warnings are **non-blocking** and use the existing readiness warning mechanism and the existing `ProductionReadinessIssue` response structure. No parallel warning system is created.

Preserved existing codes, unchanged in name and meaning:

| Code | Meaning |
|---|---|
| `tax_rate_missing` | no configured `default_tax_rate` |
| `sale_price_missing` | the authoritative Order sale price is unavailable |
| `cost_data_missing` | the existing readiness cost calculation cannot produce a complete total cost |

New codes, added only because the new contract needs them:

| Code | Meaning |
|---|---|
| `margin_percent_unavailable_zero_sale_price` | tax and margin may be available, but the denominator is zero |
| `tax_rate_invalid` | defensive handling of an invalid persisted canonical tax-rate value |

Existing codes are not renamed. Aliases such as `tax_rate_unconfigured`, `sale_price_unavailable`, or `total_cost_unavailable` are **not** introduced. Two warnings are never emitted for the same semantic condition.

### Readiness financial status semantics

`financial_estimate_status` is one of:

- `available` — tax, margin, and margin percent are all available;
- `partial` — at least tax or margin is available, but the complete financial set is not;
- `unavailable` — tax is unavailable and every dependent value is therefore unavailable.

### Physical-production non-blocking rule

`can_produce` remains governed exclusively by recipe and formula readiness, stock, lots, packaging, order lifecycle, and the existing physical-production safety rules. No financial condition — missing rate, missing sale price, missing cost, zero sale price, invalid persisted rate, or negative margin — may become a physical production blocker.

Stated as an invariant that binds readiness **and** confirmation:

```text
An absent or invalid tax-rate setting may make financial values unavailable,
but it must not by itself block physical production.
```

This invariant is why `C2-II` maps both a missing and an invalid setting to the single `null/null` confirmation context. Requiring a distinct confirmation context for an invalid rate would make the request impossible to construct — readiness never exposes an invalid value as an authoritative rate — and would therefore block physical production indirectly.

### Existing readiness API mapping

The existing endpoint `POST /api/orders/{order_id}/check-production-readiness` is extended additively. No parallel financial-readiness endpoint is created and no existing field is removed or renamed.

Existing fields, **reused**: `estimated_cost`, `estimated_tax`, `estimated_margin`. `estimated_tax` and `estimated_margin` are activated rather than duplicated.

Additive fields: `sale_price`, `tax_rate_percent`, `tax_rate_effective_at`, `estimated_margin_percent`, `financial_estimate_status`.

`estimated_total_cost` is **not** authorized, and no duplicate alias for any existing field is authorized.

All monetary and percentage values are decimal strings or `null`; `tax_rate_effective_at` is an ISO-8601 UTC string or `null`.

### C2-I / C2-II / C2-III split

**`C2-I` — backend financial readiness estimate.** `AUTHORIZED AFTER THIS PR MERGES — NOT IMPLEMENTED`. One focused backend financial calculation domain service, integrated into the existing readiness service; activation of the existing readiness financial fields; the additive readiness fields above; the stable warning codes; focused backend tests; readiness API integration tests; an exact-head readiness API smoke; and minimal directly affected documentation. No migration, no persistence write, no `AuditLog`, no `ProductionBatch` change, no report change, and **no frontend production change** — `frontend/src/main.ts` stays at exactly `6399` lines.

**`C2-II` — transactional production financial snapshots.** `PLANNED — BLOCKED`. One nullable migration adding only `tax_rate_percent_snapshot` and `tax_rate_effective_at_snapshot` to `ProductionBatch`; the transaction-aware tax-setting read; required-but-nullable confirmation context; the stale-context conflict; persistence of all financial snapshots inside the existing production transaction; and exposure of the two rate snapshots in the confirmation response and the `ProductionBatch` detail response only.

**`C2-III` — human-readable financial presentation and snapshot-backed reports.** `PLANNED — BLOCKED`. Readiness and `ProductionBatch` financial presentation, `ProductionBatch` list expansion, and snapshot-backed reports.

### C2-III umbrella and future subdivision rule

`C2-III` is a **planning umbrella, not authorization for one large implementation PR**. Before it is authorized, repository evidence must determine whether it can remain one bounded vertical slice. If it contains more than one independently reviewable user-facing vertical slice, it must be divided before implementation — for example into readiness and `ProductionBatch` financial presentation, and separately snapshot-backed reports. Readiness UI, batch UI, and report backend plus frontend must not be merged into one catch-all PR merely because they share the word "financial".

### Required-but-nullable confirmation context (`C2-II`)

The future production-confirmation request must **always** contain both keys:

- `expected_tax_rate_percent`
- `expected_tax_rate_effective_at`

They are **required but nullable**, and the request schema declares them **without default values**. Exactly two value pairs are allowed:

1. **valid configured context** — a canonical two-decimal percentage string plus the canonical `YYYY-MM-DDTHH:MM:SSZ` timestamp;
2. **no-valid-rate context** — explicit `null` and explicit `null`.

`null/null` means **"the latest readiness result observed no valid configured tax rate"**. That covers **both** a missing setting row **and** an invalid persisted setting; it does not mean only that the row is absent.

The frontend passes the pair from the latest confirmed readiness response. It must not calculate the percentage, normalize it independently, alter it, invent a timestamp, or reuse an older readiness result after it has become stale.

Omitted keys are **not** equivalent to explicit `null/null`. Omission means an invalid or outdated client contract; explicit `null/null` means readiness observed no valid configured tax rate.

### Confirmation validation rules (`C2-II`)

Reject with HTTP `422`, **before any production transaction writes**:

| Condition | Stable error code |
|---|---|
| either key is omitted | `tax_rate_context_required` |
| exactly one of the two values is `null` | `invalid_tax_rate_context` |
| the percentage is malformed, non-canonical, out of range, or not a string | `invalid_tax_rate_context` |
| the timestamp is malformed or not the canonical `YYYY-MM-DDTHH:MM:SSZ` form | `invalid_tax_rate_context` |

A rejected context produces no `ProductionBatch`, no stock movement, no packaging movement, no Order mutation, no financial snapshot, and no production audit.

### Transaction-aware tax-setting read boundary (`C2-II`)

`C2-II` must read the current canonical tax setting **inside the same production transaction**. The current no-argument `C1` read behavior must remain valid. One bounded read-only extension is authorized, equivalent to:

```python
TaxRateSettingsService.get_tax_rate(
    connection: sqlite3.Connection | None = None,
)
```

When a connection is supplied the service reads `default_tax_rate` through the existing `SettingsRepository` on that production-transaction connection, performs no write, creates no `AuditLog`, preserves the public behavior of the current no-argument call, and preserves the `C1` validation and canonicalization boundaries.

Not authorized: reading the setting through a second independent connection while the production transaction is active; parsing raw `AppSetting` values inside the production-confirmation service; bypassing the `C1` service/domain validation; a second tax-setting service; a generic transaction service locator.

If the repository implementation proves this exact extension unsafe or incompatible, `C2-II` must stop and request a contract correction before implementing.

### Stale tax-context rule (`C2-II`)

Inside the transaction, reduce the current backend state to one of exactly two comparable canonical contexts:

- **valid context** — canonical percentage + canonical API timestamp;
- **no-valid-rate context** — `null` + `null`, produced by a missing row **and** by an invalid persisted value alike.

Then compare with the expected context:

| Expected context | Current backend context | Result |
|---|---|---|
| same valid pair | same valid pair | continue |
| valid pair | different valid pair | `409 tax_rate_context_stale` |
| valid pair | missing | `409 tax_rate_context_stale` |
| valid pair | invalid | `409 tax_rate_context_stale` |
| `null/null` | valid pair | `409 tax_rate_context_stale` |
| `null/null` | missing | continue |
| `null/null` | invalid | continue |

Transitions: valid → changed valid, valid → missing, valid → invalid, missing → valid, and invalid → valid are all stale conflicts. **Missing → invalid and invalid → missing are not**, because both states produce exactly the same financial result — no rate snapshot, no tax, no margin, no margin percent — so there is nothing for the user to re-review.

On a stale conflict:

- return HTTP `409` with the stable error code `tax_rate_context_stale`;
- return a safe Russian message equivalent to `Налоговая ставка изменилась. Обновите готовность и подтвердите производство ещё раз.`;
- create no `ProductionBatch`, write no movements, change no Order, write no financial snapshot, write no production audit;
- do not retry automatically.

No third request field and no generic financial-context token is introduced by this decision. A future decision may introduce a richer state token only if product evidence shows it is necessary.

The stale check protects the **editable tax setting only**. `C2-II` still recomputes the current authoritative sale price, the current authoritative physical readiness, and the actual production cost inside the backend transaction. A generic opaque token, a second global versioning system, or a frontend-generated context hash requires a new accepted decision.

### Snapshot and migration rule (`C2-II`)

One nullable migration adds only `tax_rate_percent_snapshot` and `tax_rate_effective_at_snapshot` to `ProductionBatch`, following the decimal-string persistence pattern of the existing nullable financial fields and a timestamp representation consistent with the accepted API and storage boundary. There is **no backfill**; old rows remain `null`. No separate taxable-amount snapshot is added, because the existing `ProductionBatch.sale_price` is the taxable-base snapshot. A backup must be created before applying the migration, migration failure must not destroy user data, and rollback and backup behavior must follow the repository migration contract.

The existing `ProductionBatch` fields `sale_price`, `total_cost`, `tax`, `margin`, and `margin_percent` are **reused**. Duplicate monetary snapshot fields such as `sale_price_snapshot`, `total_cost_snapshot`, `tax_amount_snapshot`, or `margin_amount_snapshot` are **not** authorized.

Missing financial inputs at confirmation time persist honestly:

- **no valid configured tax-rate context** — a missing row **or** an invalid persisted value → both rate snapshots `null`, and `tax`, `margin`, and `margin_percent` all `null`;
- missing sale price → the rate snapshots preserve the actual current context, and `tax`, `margin`, and `margin_percent` are `null`;
- unavailable total cost → the rate snapshots preserve the actual current context, `tax` may be persisted when the sale price and a valid rate exist, and `margin` and `margin_percent` are `null`;
- configured `0.00` → `tax_rate_percent_snapshot = "0.00"`, a non-null effective timestamp, and `tax = "0.00"`;
- an invalid persisted rate must not be used to calculate or persist tax or margin, and must never be silently converted to zero.

When the current backend state is missing or invalid and the expected context is `null/null`, physical production continues: the actual authoritative production cost and every other physical production snapshot are written normally, alongside the five `null` financial values.

An invalid raw setting value stays untouched in `app_settings`. Production confirmation must not repair the setting, clear the setting, rewrite the setting, audit a setting mutation, persist the invalid value into `ProductionBatch`, or treat the invalid value as `0.00`. The normal existing production audit still belongs to the transactional production flow.

### C2-II API exposure boundary

`C2-II` exposes `tax_rate_percent_snapshot` and `tax_rate_effective_at_snapshot` in the production confirmation response and the `ProductionBatch` **detail** response, so the persisted snapshot is verifiable immediately in that slice. It must **not** yet add them to the `ProductionBatch` list presentation, report read models, or user-facing report UI — those read and presentation surfaces are `C2-III` scope. No duplicate API aliases are created; the existing confirmation and detail contracts are used.

### Historical immutability

Changing the current tax setting never changes a persisted `ProductionBatch` financial value, an existing report value, a prior audit record, or a previously generated document. Snapshots are written once, inside the production transaction, and are never recalculated afterwards — including after a future replacement of the simplified tax model.

### Report snapshot-only rule (`C2-III`)

Reports read persisted `ProductionBatch` snapshots **only** and never recalculate historical tax or margin from the current setting. Historical rows without snapshots show unavailable or `null`; they never show a fabricated `0.00` and never receive the current rate retroactively. A configured `0%` is a real value and is distinguished from missing. Only existing report read models that already contain cost, revenue, tax, margin, or margin percent are updated. No advanced analytics, tax declaration, accounting report, tax-regime reporting, or annual/quarterly filing calculation is added.

### Frontend ownership boundary

The frontend renders backend DTO values, renders `Недоступно` for null historical values, distinguishes a configured zero from a missing value, renders a negative margin honestly, renders readiness financial warnings, and renders stale-tax-context recovery guidance. It performs no `Decimal` arithmetic, no tax calculation, no margin calculation, and no historical recalculation.

Preferred focused module responsibilities for `C2-III`: `production-financial-contract.ts`, `production-financial-presentation.ts`, `production-financial-feedback.ts`, `production-financial-runtime.ts` — or the current narrower order, production, or report modules when they are a better home. One catch-all finance module is not authorized.

### God-file and file-size constraints

For **every** future `C2` slice:

- `frontend/src/main.ts` baseline is `6399` lines and its final size is **at most `6399` lines**;
- no calculation logic, no large financial HTML template, no DTO guard, and no lifecycle or stale-context state machine in `main.ts`;
- no minification or artificial line joining to satisfy the ceiling;
- each new production module is normally at most 300 lines, and each new function normally at most 60 lines;
- no generic `utils`, `helpers`, `manager`, or `common` dumping ground.

## Consequences

Positive:

- money semantics are fixed before any calculating code is written, including rounding order, the meaning of every missing input, the zero-denominator case, and the fact that a negative margin is real information;
- the readiness API grows additively, so the existing frontend keeps working unchanged and `C2-I` needs no frontend production change;
- the physical-production and financial concerns stay separated by contract: no financial gap can ever prevent the user from making a product;
- `C2` is three reviewable slices instead of one large one, and each later slice is blocked until the previous one is merged and verified;
- the stale-context rule closes the window in which a rate change between readiness and confirmation would silently persist a financial result the user never saw, without introducing a general-purpose optimistic-concurrency framework;
- historical immutability is guaranteed structurally, because the snapshot is written once inside the production transaction and reports read only snapshots.

Negative:

- the confirmation request contract becomes stricter: both context keys are required, so any client that omits them is rejected with `422` — this is deliberate, because silently defaulting to `null/null` would hide an outdated client;
- a rate change between readiness and confirmation costs the user one extra readiness refresh;
- the two rate snapshots are invisible in the `ProductionBatch` list and in reports until `C2-III`, so `C2-II` is verifiable only through the confirmation and detail responses;
- rows produced before `C2-II` permanently lack rate snapshots and will always display as unavailable, because backfilling would fabricate history;
- `C2-I` visibly changes nothing in the UI, so its value is only provable through the API and tests.

## Non-goals

Tax filing; tax declarations; VAT accounting; УСН, ОСНО, НПД, ПСН, АУСН, and ЕСХН regimes; automatic regime selection; insurance contributions; minimum tax; annual or quarterly tax accounting; marketplace tax accounting; invoicing; bookkeeping; legal or tax advice; advanced analytics; historical backfill or recalculation; per-order, per-product, per-client, or per-batch tax overrides; multiple simultaneous rates; user-configurable effective dates or scheduled rates; `C3`; `C4`; Restore; packaging; the update flow; `CR-004`; `CR-006`; release smoke.

## Future replacement of the simplified tax model

The percentage-of-sale model is the accepted MVP boundary and may be replaced by a separately decided future tax-regime model. Such a replacement is a new product decision with its own ADR. It must not recalculate, migrate, or reinterpret snapshots persisted under this contract:

```text
The simplified tax model is accepted for the current MVP and may be replaced by
a separately decided future tax-regime model. Existing historical snapshots
must remain immutable after such a replacement.
```
