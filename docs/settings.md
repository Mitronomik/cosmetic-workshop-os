# Settings

Settings (`/settings`) is a user-facing place to understand application/data status and edit the safe display-only Workshop profile. Settings must not become a technical admin panel.

## API

`GET /api/settings/status` returns:

- local-first app status;
- local data separation status;
- safe workflow capabilities;
- Settings Decision Matrix;
- `editable_settings_available: true`;
- copy explaining that the Workshop profile is editable while calculation-sensitive settings remain a future backend-rule map.

`GET /api/settings/status` is read-only. It must not create files, mutate business data, trigger backup/export/import/demo/report-document actions, regenerate alerts or purchases, or change app configuration.

## Settings Decision Matrix

### Safe MVP candidates

The Workshop profile fields are editable now through `GET /api/settings/workshop-profile` and `PUT /api/settings/workshop-profile` with backend validation and `app_settings` persistence:

- workshop name;
- master name;
- workshop contact text;
- workshop note.

Other safe candidates remain future work:

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

- PR98 uses saved Workshop profile fields in newly generated Markdown/PDF report overview documents without changing calculations or existing generated files.
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

## PR98 report-document behavior

Saved Workshop profile fields are display metadata for newly generated report documents. They do not affect recipes, clients, orders, production, stock, costs, taxes, margins, alerts, purchases, imports, exports, backups, demo data, or historical records. Existing documents are not mutated. No tax/currency/margin/unit/stock-threshold/expiry settings, template editor, logo upload, DOCX, invoices, labels, or certificates were added.
