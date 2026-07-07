# Handoff

PR96 implemented editable workshop profile settings foundation.

Changed behavior:
- `GET /api/settings/workshop-profile` returns safe empty defaults or the saved profile.
- `PUT /api/settings/workshop-profile` saves workshop name, master name, contact text, and note after backend validation.
- Settings profile data is stored backend-side in `app_settings` as grouped JSON key `workshop_profile`; no migration was added.
- `/settings` now shows «Профиль мастерской» with explicit save/cancel controls.
- `GET /api/settings/status` marks only workshop profile definitions as `editable_now=true`; calculation-sensitive settings remain `editable_now=false` and `requires_backend_rules`.

Safety notes:
- Profile changes do not mutate recipes, clients, orders, production, stock, reports, costs, taxes, margins, or historical records.
- Settings page does not create backup/export/import/demo/report document actions or files.
- No tax/currency/margin/unit/threshold/expiry settings were added.

Manual smoke was not run in a browser in this non-interactive environment. Recommended manual smoke:
1. Start backend and frontend.
2. Open `/settings`.
3. Confirm workshop profile loads with empty/default values.
4. Save workshop name/master/contact/note.
5. Refresh `/settings` and confirm saved values persist.
6. Confirm `updated_at` is present after save.
7. Confirm Settings status marks only workshop profile fields as `editable_now=true`.
8. Confirm tax/currency/margin/units/thresholds remain non-editable.
9. Confirm no recipes, clients, orders, stock, production, reports, alerts, purchases, backups, exports, imports, demo data, or report documents are changed by saving the profile.

Next recommended task: PR97 — Workshop profile integration with report documents, or PR97 — Workshop profile settings follow-up fixes if smoke finds issues.

Follow-up fixes: finalized the current `editable_now` Settings DTO contract and preserved persisted workshop profile `updated_at` in GET/PUT responses.
