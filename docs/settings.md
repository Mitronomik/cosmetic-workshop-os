# Settings

Settings (`/settings`) is a user-facing, read-only place to understand application and data status.

PR95 intentionally does **not** add editable settings, persistence, migrations, save buttons, or reset/delete actions. Settings must not become a technical admin panel.

## API

`GET /api/settings/status` returns:

- local-first app status;
- local data separation status;
- safe workflow capabilities;
- Settings Decision Matrix;
- `editable_settings_available: false`.

The endpoint is read-only. It must not create files, mutate business data, trigger backup/export/import/demo/report-document actions, regenerate alerts or purchases, or change app configuration.

## Settings Decision Matrix

### Safe MVP candidates

These may become editable later in small scoped PRs if they have backend ownership, validation, defaults, tests, and documentation:

- workshop name;
- master name;
- workshop contact text;
- default report document format;
- backup reminder hint;
- hide demo hints after onboarding.

### Calculation-sensitive candidates

These require backend domain rules before becoming editable:

- currency display;
- default tax rate;
- target margin;
- default low-stock threshold;
- expiry warning days;
- default measurement units.

Calculation-sensitive settings can affect reports, production readiness, alerts, purchases, cost, tax, margin, or historical display. They must never silently mutate historical production batches, orders, stock movements, recipes, or reports.

### V2/V3 only

- document templates;
- labels;
- certificates;
- DOCX export;
- email sending;
- external integrations;
- cloud sync.

### Not planned for MVP

- roles and multi-user access;
- full accounting;
- advanced analytics;
- template marketplace.

## Rule for editable settings

A setting can become editable only when:

- it has a backend owner/service;
- it has validation;
- it has a safe default;
- it defines whether it applies only to future records or also to display;
- it does not silently mutate historical data;
- it has tests;
- it is documented.

Frontend must not own critical setting logic. If a setting affects calculations, stock, production, cost, tax, margin, alerts, purchases, reports, or historical interpretation, backend services must own the rules.

## Allowed future Settings PR examples

- PR96 — Workshop profile settings foundation: read/write display-only profile fields with backend validation and no historical mutation.
- Add default report document format: backend-owned preference used only to preselect a creation option, while document creation remains explicit.
- Add backup reminder hint: UI guidance only, without scheduled jobs or automatic file creation.

Do not jump from PR95 directly to tax, currency, margin, unit, role/auth, cloud sync, integrations, templates, labels, certificates, accounting, scheduled jobs, or AI/RAG settings.

## PR96 — editable workshop profile

PR96 makes only the workshop profile editable. The editable fields are:

- `workshop_name` — workshop display name, max 120 characters;
- `master_name` — master/cosmetologist name, max 120 characters;
- `workshop_contact_text` — human-readable contact text, max 500 characters;
- `workshop_note` — short description/note, max 500 characters.

The profile is stored backend-side in the existing local `app_settings` key-value table under the grouped JSON key `workshop_profile`. No frontend `localStorage`, source-code file, hidden config file, backup/export/import/report document action, or new migration is used for this PR.

Validation is backend-owned: values are trimmed, empty strings are allowed, overlong values are rejected with Russian validation errors, and unsafe control characters are rejected. Phone/email formats are not required.

Profile values are display-only settings for Settings and future documents. They are not calculation inputs and do not mutate recipes, clients, orders, production batches, stock movements, reports, costs, taxes, margins, alerts, purchases, imports, exports, backups, or historical records. Calculation-sensitive settings such as tax, currency, margin, units, stock thresholds, and expiry warning days remain non-editable and require future backend rules.


Settings status uses `editable_now` to indicate fields editable in the current build. In PR96, only `workshop_name`, `master_name`, `workshop_contact_text`, and `workshop_note` have `editable_now=true`; every calculation-sensitive, V2/V3, and not-MVP setting remains `editable_now=false` and requires future backend rules where applicable.

Workshop profile GET/PUT responses include persisted `updated_at` metadata after the profile has been saved.
