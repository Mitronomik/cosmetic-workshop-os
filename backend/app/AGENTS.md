# backend/app/AGENTS.md

Scope: backend application implementation under `backend/app/`.

Implementation-layer rules:

- Keep clear separation between expected layers:
  - `api/` for HTTP routes/controllers;
  - `domain/` for core business objects, value types and domain rules;
  - `services/` for use cases and business workflows;
  - `repositories/` for data access;
  - `models/` for database models;
  - `schemas/` for API request/response contracts;
  - `migrations/` for schema migrations;
  - `tests/` for backend tests.
- Domain services own calculations and business rules, including recipe totals, ml-to-grams conversion, FEFO selection, cost, margin, readiness checks, alerts, purchase suggestions and import validation.
- Repositories and data-access code must not contain hidden business decisions; keep them focused on persistence.
- API schemas must be explicit, stable and reviewable. Do not leak database internals accidentally.
- Error responses must support human-readable frontend messages and should include actionable validation details where appropriate.
- Tests must cover domain services and API behavior for success paths, validation failures and important edge cases.
