# Current focus

PR72 hotfix is implemented: Orders form reference refresh and localized quantity display.

## Completed in PR72
- Orders create/edit now refreshes active clients, recipe templates, recipe versions, client recipes, and packaging items before showing usable dropdowns.
- Orders form has explicit reference loading and retryable error states so stale `ordersState` data does not leave client or recipe selects disabled after related records were added elsewhere.
- User-facing quantity labels in Orders/readiness/production/dashboard snippets now display Russian-friendly decimals, e.g. `100.000 г` as `100 г`, `100.500` as `100,5`, and thousands with spaces.
- Order form payloads still normalize comma decimal input back to dot decimal strings for the backend.

## Out of scope / not added
- No backend endpoints, migrations, Decimal storage/API contract changes, production readiness changes, production confirmation changes, stock mutations, recipe mutations, client mutations, alert regeneration, purchase suggestion regeneration, scheduler, polling, import/export, or backup/export changes were added.
- Orders still mutate only through existing explicit create/edit/cancel/archive actions.

## Next recommended PR
- Return to the prior roadmap direction: Backup/export UI foundation or Backup/export backend/frontend foundation, depending on existing backend support and desired next slice.
