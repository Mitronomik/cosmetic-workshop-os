# Current Focus

## Status

PR61 — Orders UI foundation is implemented and ready for review.

## Completed in PR61

- Added the frontend `Заказы` navigation entry and `/orders` route.
- Added Orders list, search/status filters, empty/loading/error states, create form, detail view, safe edit flow, cancel action, and archive action.
- Integrated the UI with the existing PR60 Orders backend endpoints only.
- Kept production readiness, production confirmation, stock write-off, production batches, cost/tax/margin calculation, alerts, purchase suggestions, import/export, and backup/restore UI out of scope.

## Next recommended task

Next roadmap step: production readiness foundation for orders, as a separate scoped PR.

The next PR should still avoid production confirmation and automatic stock write-off unless explicitly requested.
