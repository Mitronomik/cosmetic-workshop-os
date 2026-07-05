# Handoff

## Last completed work

PR81 — Import confirmation/apply UI.

## Current repo state after PR81

Import now has a safe frontend confirmation flow for the PR80 backend apply endpoint:

- Draft detail shows a `Применение черновика` section below backend readiness.
- Supported UI apply targets match PR80 only: `ingredients`, `clients`, `recipe_templates`, `packaging_items`.
- Unsupported targets such as `ingredient_lots` and `orders` show an unsupported message and no apply button.
- Blocked, cancelled, failed, and already-applied drafts do not show an apply action.
- Ready supported drafts can open an in-panel confirmation step.
- Apply requires explicit confirmation that data will be written and explicit backup acknowledgement.
- `ready_with_warnings` drafts additionally require warning acknowledgement before the button enables.
- The frontend calls only `POST /api/imports/drafts/{draft_id}/apply` after those checkboxes are satisfied.
- Successful apply refreshes the draft list/detail and displays created records returned by backend.
- Backup/export buttons in the confirmation UI only navigate to `/backups` and `/exports`; they do not create backup/export files automatically.

## Safety notes

- No apply call runs on page load or draft open.
- No frontend CSV/XLSX parsing, mapping editor, cell editing, partial import, OCR/PDF/image import, or backend target expansion was added.
- No frontend direct mutation of ingredients, clients, recipes, packaging, orders, stock, production, alerts, purchase suggestions, backups, or exports was added.
- No stock movements, ingredient lots, orders, production records, alerts, purchase suggestions, backups, or exports are created automatically by the UI.

## Manual smoke

Manual browser smoke was not run in this non-interactive session because no long-running backend/frontend browser session was started. Recommended PR82 smoke: create valid and warning ingredients drafts, verify checkbox gating, apply once, verify created records and applied status, retry cannot apply, verify blocked drafts and unsupported `ingredient_lots`/`orders` show no apply button, and verify backup/export buttons only navigate.

## Next recommended PR

PR82 — Import apply hardening and smoke fixes.
