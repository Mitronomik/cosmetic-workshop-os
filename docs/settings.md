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
