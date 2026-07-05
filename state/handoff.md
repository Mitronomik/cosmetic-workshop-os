# Handoff

## Last completed work

PR79 — Import validation refinement and apply readiness contract.

## Current repo state after PR79

Import remains draft-only. The backend now computes `draft.apply_readiness` for create/detail/list/cancel responses and stores readiness/count aggregation in new draft summaries. Older summaries get fallback readiness when returned by the service.

Validation refinements added:

- deterministic target-specific Russian/user-friendly header aliases with visible `header_alias_used` issues;
- comma decimal normalization with visible `decimal_comma_normalized` issues;
- ambiguous decimal blocking via `ambiguous_decimal`;
- positive/non-negative numeric validation;
- visible unit alias normalization to `g`, `ml`, `pcs`;
- ISO plus deterministic `DD.MM.YYYY` date handling;
- client email warnings;
- positive integer validation for optional `ingredient_id` and `client_id`.

Frontend `/imports` displays draft readiness in list/detail panels and repeats that the apply button does not exist yet.

## Safety notes

- No import apply endpoint was added.
- No import confirmation endpoint was added.
- No apply button was added.
- No ingredients, clients, recipes, orders, stock, production, alerts, purchase suggestions, backups, or exports are changed by validation.
- Normalized values are visible in draft rows and raw source values remain preserved.

## Manual smoke

Manual browser smoke was not run in this non-interactive session because no long-running backend/frontend browser session was started. Recommended smoke: open `/imports`, upload valid, alias, comma-decimal, missing-column, invalid-unit, and unknown-column CSV files; verify readiness states and absence of an apply/confirm button; confirm domain tables, backup/export pages, and dashboard remain unchanged.

## Next recommended PR

PR80 — Import apply backend foundation, only after smoke confirms validation/readiness is clear.
