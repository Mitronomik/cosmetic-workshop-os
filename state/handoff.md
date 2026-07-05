# Handoff

## Last completed work

PR80 — Import apply backend foundation.

## Current repo state after PR80

Import now supports a backend-only explicit apply step:

- `POST /api/imports/drafts/{draft_id}/apply` exists.
- Apply requires `confirm_apply=true` and `backup_acknowledged=true`.
- `ready_with_warnings` drafts require `allow_warnings=true`.
- Supported PR80 apply targets: `ingredients`, `clients`, `recipe_templates`, `packaging_items`.
- Unsupported PR80 apply targets: `ingredient_lots`, `orders`.
- Apply is transactional and all-or-nothing.
- Existing domain conflicts and duplicate rows inside drafts block the whole apply.
- Successful apply marks both import draft and source as `applied` and stores `apply_result` in `summary_json`.
- Audit log entry `import_draft_applied` is created on successful apply.

## Safety notes

- No frontend apply UI or apply button was added.
- No mapping editor, cell editing, partial import, restore, OCR/PDF/image import, cloud import, or scheduled import was added.
- No stock movements, ingredient lots, orders, production records, alerts, purchase suggestions, backups, or exports are created automatically by apply.
- Packaging apply is catalog-only; non-empty `stock` is blocked.
- A migration adds `applied` as an allowed import source/draft status because the existing CHECK constraints did not permit it.

## Manual smoke

Manual browser/API smoke was not run in this non-interactive session because no long-running backend/frontend browser session was started. Recommended smoke for PR81: create an ingredients CSV draft, call apply with missing confirmation and missing backup acknowledgement to confirm rejections, apply with both flags, verify created records and `applied` status, retry apply to confirm conflict, and confirm unsupported `ingredient_lots` creates no stock/lots/movements.

## Next recommended PR

PR81 — Import confirmation/apply UI.
