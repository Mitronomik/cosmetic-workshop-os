# Current Focus

Current task: PR17 - Recipe models backend foundation.

## Allowed scope
Backend-only recipe model foundation: `recipe_templates`, `recipe_versions`, and `recipe_ingredients` migration; domain validation; repository/service/API basics; transactional audit events for recipe template create/deactivate and recipe version create; backend tests; smoke notes; and state documentation updates.

## Do not touch
Frontend recipe UI, recipe calculation service, percent-sum validation, recipe cost calculation, client recipes, clients, orders, production, stock reservation/write-off, purchase suggestions, alerts engine, imports/exports, launcher behavior changes, final app packaging/installers, Docker, cloud/mobile access, OCR, auth, or roles.

## Acceptance
Recipe templates can be created/read/listed/deactivated, recipe versions can be created for active templates, version numbers increment per template, version detail returns ingredient lines, ingredient lines reference existing active ingredients, invalid ingredient lines roll back version creation, audit failures roll back create/deactivate operations, test-only table guards allow only the new recipe tables, and no calculation service, recipe UI, clients, orders, or production are added.
