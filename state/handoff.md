# Handoff

PR96 implemented editable workshop profile settings foundation.

Changed behavior:
- `GET /api/settings/workshop-profile` returns safe empty defaults or the saved profile.
- `PUT /api/settings/workshop-profile` saves workshop name, master name, contact text, and note after backend validation.
- Settings profile data is stored backend-side in `app_settings` as grouped JSON key `workshop_profile`; no migration was added.
- `/settings` now shows «Профиль мастерской» with explicit save/cancel controls.
- `GET /api/settings/status` marks only workshop profile definitions as `editable_now`; calculation-sensitive settings remain `requires_backend_rules`.

Safety notes:
- Profile changes do not mutate recipes, clients, orders, production, stock, reports, costs, taxes, margins, or historical records.
- Settings page does not create backup/export/import/demo/report document actions or files.
- No tax/currency/margin/unit/threshold/expiry settings were added.

Manual smoke was not run in a browser in this non-interactive environment. Recommended smoke: open `/settings`, save profile fields, reload, cancel draft edits, try an overlong value, and call the two Settings API endpoints manually.

Next recommended task: PR97 — Workshop profile integration with report documents, or PR97 — Workshop profile settings follow-up fixes if smoke finds issues.

Final PR96 polish:
- Updated the Settings capability copy so it no longer says Settings has no editing.
- Confirmed stale PR95 editability flags are absent from Settings schemas/API/frontend types.
- Workshop profile `updated_at` is returned as a persisted `str | None` from `app_settings.updated_at`.
- Attempted `git fetch origin && git rebase origin/main`, but this workspace has no `origin` remote configured, so branch mergeability could not be updated locally.
