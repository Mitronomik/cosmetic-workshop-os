# Current focus

PR71 frontend Dashboard operational overview is implemented.

## Completed in PR71
- `/` now shows a real operational dashboard instead of the placeholder.
- Dashboard loads existing data from current frontend/API helpers for orders, clients, open alerts, open purchase suggestions, and production batches.
- Dashboard keeps the onboarding checklist visible.
- Dashboard shows priority cards for active orders, waiting-for-materials orders, ready-to-produce orders, open alerts, purchase suggestions, and recent production.
- Dashboard includes “Что сделать сегодня” guidance using existing statuses and records only.
- Dashboard includes card sections for active orders, open alerts, open purchase suggestions, recent production, quick navigation actions, and a backup reminder.

## Out of scope / not added
- No backend endpoints, migrations, dashboard analytics, charts, scheduler, polling, notifications, backup/export implementation, import/export, supplier/procurement automation, stock mutation, order mutation, production mutation, alert mutation, or purchase suggestion mutation were added.
- Dashboard reload only repeats existing GET requests and does not regenerate alerts or purchase suggestions.
- Dashboard does not run production readiness checks and does not infer readiness from stock.

## Next recommended PR
- Backup/export UI foundation or Backup/export backend/frontend foundation, depending on existing backend support and desired next slice.
