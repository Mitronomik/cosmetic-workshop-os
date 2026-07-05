# Handoff

## Last completed work

PR83 — Refresh existing onboarding checklist after import/apply.

## Current repo state after PR83

- The project still has one onboarding/checklist mechanism: the existing `/api/onboarding` API, `OnboardingService`, and `app_settings` JSON state.
- The checklist now reflects the current MVP workflow: local data, components, component lots, packaging, recipes, clients, individual recipes, orders, production readiness, production confirmation, alerts/purchases, backup/export, and import drafts.
- Frontend checklist actions only mark onboarding progress or navigate to existing sections. They do not create recipes, inventory, orders, production records, backups, exports, or imports.
- Legacy onboarding state remains compatible. `first_backup` maps to `backup_and_export`, unknown old step IDs are ignored, and unknown current steps fall back to the first incomplete refreshed step.
- Existing completed/skipped onboarding remains closed unless the user resets it.
- Import apply targets were not expanded. `ingredient_lots` and `orders` remain unsupported for apply.
- Stale import readiness copy that said apply would be added in a future PR was replaced with current supported-target wording.

## Manual smoke

Manual browser smoke was not run in this non-interactive session because no long-running backend/frontend browser session was started and no browser was available. Automated backend onboarding/import regression checks and frontend build were run instead.

Recommended manual smoke:
1. Open dashboard/home and confirm there is only one onboarding/checklist area.
2. Confirm the checklist uses current MVP steps and shows progress.
3. Start onboarding and mark a step complete.
4. Navigate from checklist to Components, Recipes, Clients, Orders, Backups/Exports, and Imports.
5. Confirm checklist actions do not create business data, backups, exports, or imports automatically.
6. Confirm skip closes the checklist and reset reopens it if visible.
7. Confirm import page no longer says apply is entirely future-only.
8. Confirm ingredient lots and orders still do not offer import apply.

## Next recommended PR

O4 — Demo data mode.

If manual onboarding smoke finds issues, do PR84 — Onboarding follow-up fixes first.
