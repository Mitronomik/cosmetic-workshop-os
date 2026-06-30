# Current focus

PR70 frontend Purchase Suggestions workspace is implemented.

## Completed in PR70
- `/purchase-suggestions` route and «Закупки» navigation entry now open the real purchase suggestions workspace.
- Frontend consumes the PR69 purchase suggestion endpoints for list, explicit regenerate, manual create, update, mark purchased, and dismiss.
- Purchase suggestions are shown as Russian human-readable cards with filters by status, reason, item type, and search.
- Manual suggestions use existing component and packaging reference lists instead of requiring raw IDs.
- «Отметить купленным» is explicitly worded as closing the recommendation only; it does not add stock.

## Out of scope / not added
- No backend behavior, migrations, supplier integration, online ordering, invoices, real procurement entities, stock mutation, order mutation, production mutation, dashboard widgets, scheduler, polling, notifications, import/export, or backup UI.

## Next recommended PR
- Dashboard operational overview: surface daily operational summaries without adding procurement automation.
