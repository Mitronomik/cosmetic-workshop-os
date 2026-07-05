# Handoff

## Last completed work

PR82 — Import apply hardening / smoke fixes.

## Current repo state after PR82

Import apply remains a safe, explicit flow for only these targets:

- `ingredients`
- `clients`
- `recipe_templates`
- `packaging_items`

Unsupported targets remain blocked with no apply button:

- `ingredient_lots`
- `orders`

## PR82 changes

- Frontend apply errors now render structured backend `detail.issues` as readable row/field/code conflict details instead of raw JSON.
- Apply failure copy explicitly reassures: working data was not partially changed.
- Apply is guarded while a request is in progress to avoid double-click duplicate calls.
- Applied draft detail/list continues to show `Черновик уже применён` and stored `summary.apply_result` after reload when available.
- Backend tests cover duplicate conflicts, already-applied rejection, unsupported lots/orders, warning acknowledgement, failed apply keeping draft/source unapplied, no side-effect backup/export/alert/purchase records, and applied readiness/result in list/detail.
- Docs were updated for the current apply behavior and PR82 hardening notes.

## Safety notes

- No new import apply targets were added.
- Ingredient lots and orders remain unsupported.
- No stock movements, production records, alerts, purchase suggestions, backups, or exports are created automatically by import apply.
- Existing records are not silently updated.
- Failed apply remains all-or-nothing: zero partial rows are committed and draft/source stay unapplied.
- Frontend still mutates domain data only through `POST /api/imports/drafts/{draft_id}/apply`.

## Manual smoke

Manual browser smoke was not run in this non-interactive session because no long-running backend/frontend browser session was started and no browser was available. Automated backend/API/frontend build checks were run instead. Recommended manual smoke remains:

1. Create a valid ingredients CSV draft, apply it, verify records appear in Components, and verify no second apply button.
2. Upload the same CSV again, verify duplicate conflict details and zero partial inserts.
3. Create a warning draft, verify warning acknowledgement is required before apply.
4. Create a blocked draft, verify no apply button.
5. Create `ingredient_lots` and `orders` drafts, verify unsupported copy and no apply button.
6. Verify `/backups`, `/exports`, and `/dashboard` load and no backup/export files are created automatically.

## Next recommended PR

O3 — Guided setup checklist.

If browser smoke finds remaining import issues, do PR83 — Import apply follow-up fixes before moving on.
